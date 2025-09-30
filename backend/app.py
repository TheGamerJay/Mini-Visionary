import os
import io
import base64
import time
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, send_from_directory, render_template, abort, make_response
from flask_cors import CORS
from flask_compress import Compress
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Database models ---
from models import init_db, get_session, User, PosterJob, Poster, Asset, PosterMode, PosterStatus, PosterStyle
# Temporarily disabled - needs wallet fixes:
# from poster import bp as poster_bp

# Essential blueprints:
from app_library import library_bp
from app_legal import legal_bp
from mailer import send_email_post, MailError
from me import bp as me_bp
from me_alias import bp as auth_alias_bp

# Advanced blueprints that need proper setup:
# from app_auth import auth_bp          # Needs JWT configuration
from auth import bp as new_auth_bp, bcrypt
# from app_payments import payments_bp  # CSS f-string issues - needs manual fix
# from storage import bp as storage_bp  # Needs S3/R2 configuration
# from ads import bp as ads_bp          # Needs subscription logic
from ads_portal import bp as ads_portal_bp
from webhooks import bp as webhooks_bp
from app_chat import bp as chat_bp
from app_health import health_bp

# --- Optional OpenAI (auto-disabled if key missing) ---
OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

load_dotenv()

# ---------------------- BRAND ----------------------
BRAND_NAME = "Mini-Visionary"
BRAND_TAGLINE = "You Envision it, We Generate it"
SUPPORT_EMAIL = "support@minivisionary.com"

# ---------------------- ENV / CONFIG ----------------------
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))  # reject > 10MB
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "30"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "6"))

# local output dir (Railway ephemeral is fine for MVP; move to S3/R2 later)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTS = {"png", "jpg", "jpeg", "webp"}  # posters only

# ---------------------- APP ----------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JSON_SORT_KEYS"] = False
app.config["ASSET_VERSION"] = os.getenv("GIT_SHA", "")
app.config["PUBLIC_BASE_URL"] = os.getenv("PUBLIC_BASE_URL", "https://minivisionary.soulbridgeai.com")
app.config["APP_VERSION"] = os.getenv("GIT_SHA", "dev")

# Session cookie configuration for SPA
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",  # or "None" if cross-site
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true",  # True in production
)

# CORS configuration - strict for production
# You can override with CORS_ORIGINS env (comma-separated)
default_cors = "https://minivisionary.com,https://minivisionary.soulbridgeai.com"
cors_origins_env = os.getenv("CORS_ORIGINS", default_cors)
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] + ["http://localhost:5173"]
CORS(app, supports_credentials=True, origins=cors_origins)

# --- Compression ---
app.config.update(
    COMPRESS_ALGORITHM=["br", "gzip"],  # prefer Brotli, fall back to gzip
    COMPRESS_MIMETYPES=[
        "text/html",
        "text/css",
        "application/javascript",
        "application/json",
        "image/svg+xml",
        "application/xml",
        "text/plain",
        "font/woff2",
    ],
    COMPRESS_LEVEL=6,     # gzip level (0-9)
    COMPRESS_BR_LEVEL=5,  # brotli level (0-11). 5-6 is a good perf/size tradeoff
    COMPRESS_MIN_SIZE=512 # only compress payloads >= 512 bytes
)
Compress(app)

# --- Observability: Sentry + Request IDs + JSON logs ---
import sys, uuid, logging
from flask import g
from pythonjsonlogger import jsonlogger

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
except Exception:
    sentry_sdk = None

def _init_json_logging(app_name: str = "mini-visionary"):
    """Setup JSON logging to stdout (works in Railway/Gunicorn)."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # remove default handlers (avoid double logs)
    for h in list(root.handlers):
        root.removeHandler(h)

    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "levelname": "level",
            "asctime": "ts"
        }
    )
    logHandler.setFormatter(formatter)
    root.addHandler(logHandler)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # quieter dev server logs
    logging.info("json_logging_initialized", extra={"app": app_name})

def _init_sentry(flask_app):
    """Initialize Sentry if DSN is provided."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn or len(dsn) == 0 or not dsn.startswith("https://") or sentry_sdk is None:
        logging.info("sentry_not_configured", extra={"dsn_length": len(dsn), "sentry_sdk_available": sentry_sdk is not None})
        return

    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FlaskIntegration(),                       # captures unhandled errors
                LoggingIntegration(                       # turn ERROR logs into Sentry events
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),   # APM
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),# profiling (optional)
            environment=os.getenv("ENVIRONMENT", "production"),
            release=os.getenv("GIT_SHA", "dev"),
            send_default_pii=False,
        )
        logging.info("sentry_initialized")
    except Exception as e:
        logging.error("sentry_initialization_failed", extra={"error": str(e), "dsn_provided": bool(dsn)})

def _request_id():
    """Get or create a request id for correlation across services."""
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = rid
    return rid

def _log_request_start():
    g._t0 = time.time()
    logging.info(
        "request_start",
        extra={
            "rid": g.request_id,
            "method": request.method,
            "path": request.path,
            "ip": request.headers.get("x-forwarded-for", request.remote_addr),
            "ua": request.headers.get("user-agent"),
        }
    )

def _log_request_end(response):
    dt = None
    try:
        dt = round((time.time() - getattr(g, "_t0", time.time())) * 1000, 2)
    except Exception:
        pass
    response.headers["X-Request-ID"] = g.request_id
    logging.info(
        "request_end",
        extra={
            "rid": g.request_id,
            "status": response.status_code,
            "duration_ms": dt,
            "length": response.calculate_content_length() if hasattr(response, "calculate_content_length") else None,
        }
    )
    return response

# Initialize observability
_init_json_logging(app_name="mini-visionary")
_init_sentry(app)

@app.before_request
def _before():
    _request_id()
    _log_request_start()

@app.after_request
def _after(response):
    return _log_request_end(response)
# --- end observability block ---

# Initialize bcrypt - temporarily disabled
bcrypt.init_app(app)

# Register blueprints - Enable essential core functionality
app.register_blueprint(new_auth_bp)
# app.register_blueprint(poster_bp)       # Disabled - needs OpenAI configuration
app.register_blueprint(library_bp)        # Essential - poster library and gallery
app.register_blueprint(legal_bp)          # Essential - privacy policy, terms of service
# app.register_blueprint(payments_bp)     # CSS f-string issues - needs manual fix
# app.register_blueprint(storage_bp)      # Disabled - needs S3/R2 configuration
# app.register_blueprint(ads_bp)          # Disabled - needs subscription logic
app.register_blueprint(ads_portal_bp)
app.register_blueprint(me_bp)             # Essential - user profile and account management
app.register_blueprint(auth_alias_bp)     # Essential - /api/auth/whoami endpoint
app.register_blueprint(webhooks_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(health_bp)         # Essential - health monitoring endpoint

# JSON error handlers (prevent HTML error pages from breaking JSON APIs)
@app.errorhandler(405)
def handle_405(e):
    """Return JSON for Method Not Allowed instead of HTML"""
    allow = list(e.valid_methods) if e.valid_methods else []
    return jsonify({"ok": False, "error": "METHOD_NOT_ALLOWED", "allow": allow}), 405

@app.errorhandler(404)
def handle_404(e):
    """Return JSON for Not Found on API routes"""
    if request.path.startswith('/api/'):
        return jsonify({"ok": False, "error": "NOT_FOUND"}), 404
    return e  # Let HTML 404 page show for non-API routes

# OpenAI client (only if key + lib present)
oai_client: Optional["OpenAI"] = None
if OPENAI_API_KEY and OPENAI_AVAILABLE:
    try:
        oai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        oai_client = None

# ---------------------- SIMPLE RATE LIMIT ----------------------
# in-memory IP bucket: { ip: [timestamps...] }
_IP_BUCKET = {}

def rate_limited(ip: str) -> bool:
    now = time.time()
    bucket = _IP_BUCKET.get(ip, [])
    # trim old
    bucket = [t for t in bucket if now - t <= RATE_LIMIT_WINDOW_SEC]
    limited = len(bucket) >= RATE_LIMIT_MAX_REQUESTS
    if not limited:
        bucket.append(now)
    _IP_BUCKET[ip] = bucket
    return limited

# ---------------------- HELPERS ----------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS

def reject_large(file_storage) -> bool:
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    return size > MAX_UPLOAD_MB * 1024 * 1024

def b64_to_file(b64_png: str, dest_path: str) -> None:
    with open(dest_path, "wb") as f:
        f.write(base64.b64decode(b64_png))

def overlay_text_cinematic(poster_path: str, title: str = "", tagline: str = "") -> str:
    """
    Adds cinematic title & tagline text. Returns path to the edited poster.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except Exception:
        return poster_path  # Pillow not installed; skip overlay gracefully

    img = Image.open(poster_path).convert("RGBA")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Try to use a nicer font if present, else default
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", size=max(48, W // 16))
    except Exception:
        font_title = ImageFont.load_default()
    try:
        font_tag = ImageFont.truetype("DejaVuSans.ttf", size=max(24, W // 36))
    except Exception:
        font_tag = ImageFont.load_default()

    # Bottom gradient for readability
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        # last 30% fades to black
        val = int(max(0, (y - int(H * 0.7)) / (H * 0.3)) * 220)
        grad.putpixel((0, y), min(220, max(0, val)))
    grad = grad.resize((W, H))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img = Image.alpha_composite(img, Image.merge("RGBA", (black.split()[0], black.split()[1], black.split()[2], grad)))

    # Draw title
    if title:
        tw, th = draw.textlength(title, font=font_title), font_title.size
        try:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            th = bbox[3] - bbox[1]
            tw = bbox[2] - bbox[0]
        except Exception:
            pass

        x = (W - tw) / 2
        y = H - th - max(20, H // 18)

        # subtle glow
        for _ in range(6):
            draw.text((x, y), title, font=font_title, fill=(255, 255, 255, 80))
        draw.text((x, y), title, font=font_title, fill=(255, 255, 255, 230))

    # Draw tagline
    if tagline:
        try:
            bbox2 = draw.textbbox((0, 0), tagline, font=font_tag)
            tw2 = bbox2[2] - bbox2[0]
            th2 = bbox2[3] - bbox2[1]
        except Exception:
            tw2 = draw.textlength(tagline, font=font_tag)
            th2 = font_tag.size

        x2 = (W - tw2) / 2
        y2 = H - th2 - max(10, H // 48)
        draw.text((x2, y2), tagline, font=font_tag, fill=(220, 220, 220, 220))

    out_path = poster_path.replace(".png", "_titled.png").replace(".jpg", "_titled.jpg")
    img.convert("RGB").save(out_path, quality=95)
    return out_path

def save_upload(file_storage, prefix: str = "upload") -> str:
    fname = secure_filename(file_storage.filename)
    base, ext = os.path.splitext(fname)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    final = f"{prefix}_{ts}{ext.lower()}"
    path = os.path.join(UPLOAD_DIR, final)
    file_storage.save(path)
    return path

def make_public_url(local_path: str) -> str:
    return f"/uploads/{os.path.basename(local_path)}"

# ---------------------- ROUTES ----------------------
# ---------- API ENDPOINTS ----------
@app.get("/api/health")
def health():
    return {"ok": True, "service": "mini-visionary", "openai": bool(oai_client)}

@app.post("/api/migrate")
def migrate_database():
    """Manual migration endpoint to add missing display_name column"""
    try:
        from sqlalchemy import text
        from models import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            # Check if display_name column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'display_name'
            """))

            if result.fetchone():
                return {"ok": True, "message": "display_name column already exists"}

            # Add the column
            conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(100)"))
            conn.commit()
            return {"ok": True, "message": "Successfully added display_name column"}

    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

@app.get("/api/version")
def version():
    """Return git SHA and build info with debugging"""
    static_files = []
    try:
        static_dir = app.static_folder or "static"
        if os.path.exists(static_dir):
            static_files = os.listdir(static_dir)[:10]  # Limit to first 10 files
    except Exception as e:
        static_files = [f"Error: {str(e)}"]

    return {
        "ok": True,
        "git": os.getenv("GIT_SHA", "dev"),
        "railway_sha": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
        "github_sha": os.getenv("GITHUB_SHA"),
        "service": "mini-visionary",
        "timestamp": datetime.utcnow().isoformat(),
        "static_files": static_files,
        "openai": bool(oai_client)
    }

# Demo endpoints removed - now handled by auth.py with JWT authentication

@app.post("/api/email/send")
def api_email_send():
    """Send email via Resend API"""
    data = request.get_json(silent=True) or {}
    to = data.get("to")
    subject = data.get("subject", f"Hello from {BRAND_NAME}")
    html = data.get("html", f"<p>Test email from {BRAND_NAME}.</p>")

    if not to:
        return jsonify({"ok": False, "error": "Missing 'to'"}), 400

    try:
        res = send_email_post(to=to, subject=subject, html=html)
        return jsonify({"ok": True, "id": res.get("id")})
    except MailError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/email/config")
def email_config_check():
    """Check email configuration status"""
    from mailer import RESEND_API_KEY, FROM_EMAIL, RESEND_FROM

    config = {
        "resend_api_key_set": bool(RESEND_API_KEY),
        "resend_api_key_length": len(RESEND_API_KEY) if RESEND_API_KEY else 0,
        "from_email": FROM_EMAIL,
        "resend_from": RESEND_FROM,
        "environment_vars": {
            "RESEND_API_KEY": "SET" if os.getenv("RESEND_API_KEY") else "MISSING",
            "FROM_EMAIL": os.getenv("FROM_EMAIL", "NOT_SET"),
            "RESEND_FROM": os.getenv("RESEND_FROM", "NOT_SET")
        }
    }

    return jsonify({"ok": True, "config": config})

# DEV ONLY: serve local storage dir so returned /storage/... URLs load in browser
@app.get("/storage/<path:key>")
def storage(key: str):
    """Serve files from local storage directory"""
    storage_root = os.path.join(os.getcwd(), "storage")
    return send_from_directory(storage_root, key)

@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)

@app.post("/api/generate")
def generate_poster():
    """
    Generate AI poster using OpenAI DALL-E.
    Body: { prompt: str, style?: str }
    Requires JWT authentication.
    """
    from auth import auth_required
    from flask import g

    # Check authentication - verify JWT token is present and valid
    hdr = request.headers.get("Authorization", "")
    if not hdr.startswith("Bearer "):
        return {"ok": False, "error": "authentication_required"}, 401

    token = hdr.split(" ", 1)[1].strip()
    try:
        import jwt
        from auth import SECRET
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            return {"ok": False, "error": "invalid_token"}, 401
    except Exception as e:
        return {"ok": False, "error": "authentication_required"}, 401

    ip = request.headers.get("x-forwarded-for", request.remote_addr or "unknown")
    if rate_limited(ip):
        return {"ok": False, "error": "rate_limited"}, 429

    if not oai_client:
        return {"ok": False, "error": "openai_not_configured"}, 503

    d = request.get_json(force=True, silent=True) or {}
    prompt = (d.get("prompt") or "").strip()
    style = (d.get("style") or "cinematic").strip()

    if not prompt:
        return {"ok": False, "error": "prompt_required"}, 400

    # Style-specific prompt enhancement
    style_prompts = {
        "cinematic": "cinematic movie poster style, dramatic lighting, professional movie poster design",
        "vintage": "vintage retro movie poster style, aged paper texture, classic typography",
        "modern": "modern minimalist poster design, clean typography, contemporary aesthetic",
        "horror": "horror movie poster style, dark atmosphere, scary elements",
        "comedy": "comedy movie poster style, bright colors, playful elements",
        "action": "action movie poster style, explosive effects, dynamic composition"
    }

    style_enhancement = style_prompts.get(style, style_prompts["cinematic"])
    enhanced_prompt = f"{prompt}, {style_enhancement}, high quality, detailed"

    try:
        # Generate image with OpenAI DALL-E
        response = oai_client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url

        # TODO: Save to database and associate with user
        # For now, just return the URL

        return {"ok": True, "image_url": image_url, "prompt": prompt, "style": style}

    except Exception as e:
        return {"ok": False, "error": f"generation_failed: {str(e)}"}, 500

@app.post("/api/poster/add-text")
def add_text_to_poster():
    """
    Add/replace cinematic title+tagline over an existing poster in /uploads.
    Body: { url: "/uploads/xyz.png", title?: str, tagline?: str }
    """
    ip = request.headers.get("x-forwarded-for", request.remote_addr or "unknown")
    if rate_limited(ip):
        return {"ok": False, "error": "rate_limited"}, 429

    d = request.get_json(force=True, silent=True) or {}
    url = (d.get("url") or "").strip()
    title = (d.get("title") or "").strip()
    tagline = (d.get("tagline") or "").strip()

    if not url or not url.startswith("/uploads/"):
        return {"ok": False, "error": "bad_url"}, 400

    local_path = os.path.join(UPLOAD_DIR, os.path.basename(url))
    if not os.path.isfile(local_path):
        return {"ok": False, "error": "not_found"}, 404

    try:
        out_path = overlay_text_cinematic(local_path, title, tagline)
        return {"ok": True, "url": make_public_url(out_path), "title": title, "tagline": tagline}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

# ---------------------- STATIC FILE ROUTE ----------------------
@app.route('/static/<path:filename>')
def static_files(filename):
    """Custom static file handler to ensure proper serving"""
    return send_from_directory(app.static_folder, filename)

# ---------------------- AUTH PAGES ----------------------
@app.route('/auth.html')
def auth_page():
    """Serve auth.html directly"""
    return send_from_directory(app.static_folder, 'auth.html')

@app.route('/register')
def register_redirect():
    """Redirect /register to auth.html#register"""
    return f'<script>window.location.href="/auth.html#register";</script>'

@app.route('/login')
def login_redirect():
    """Redirect /login to auth.html#login"""
    return f'<script>window.location.href="/auth.html#login";</script>'

@app.route('/forgot-password')
def forgot_redirect():
    """Redirect /forgot-password to auth.html#forgot"""
    return f'<script>window.location.href="/auth.html#forgot";</script>'

@app.route('/terms.html')
def terms_page():
    """Serve terms.html directly"""
    return send_from_directory(app.static_folder, 'terms.html')

@app.route('/privacy.html')
def privacy_page():
    """Serve privacy.html directly"""
    return send_from_directory(app.static_folder, 'privacy.html')

# ---------------------- DASHBOARD ROUTES ----------------------

@app.route('/create')
def create_redirect():
    """Redirect /create to poster generation dashboard"""
    return f'<script>window.location.href="/generate";</script>'

@app.route('/generate')
def generate_page():
    """Serve the AI poster generation dashboard"""
    return send_from_directory(app.static_folder, 'generate.html')

# SPA routes are handled by serve_spa.py to avoid duplication

# ---------------------- MAIN ----------------------
@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat(), "openai": bool(oai_client)}

@app.get("/api/test-compression")
def test_compression():
    """Large JSON response to test compression"""
    return {
        "message": "This is a test response to verify Flask-Compress is working with Brotli and gzip compression.",
        "data": ["item_" + str(i) for i in range(100)],
        "compression": "If this is working, you should see Content-Encoding: br or gzip in the response headers",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "mini-visionary",
        "features": [
            "Flask-Compress with Brotli support",
            "Optimal caching headers for hashed assets",
            "Security headers including CSP",
            "Production-ready build system",
            "Direct React build integration"
        ]
    }

@app.get("/api/test-error")
def test_error():
    """Test endpoint to trigger error for Sentry testing"""
    logging.info("test_error_triggered", extra={"rid": getattr(g, "request_id", None)})
    raise Exception("This is a test error for Sentry verification")

@app.get("/api/test-logging")
def test_logging():
    """Test endpoint to verify JSON logging and request correlation"""
    rid = getattr(g, "request_id", None)
    logging.info("test_log_message", extra={"rid": rid, "custom_field": "test_value"})
    logging.warning("test_warning", extra={"rid": rid, "warning_type": "test"})
    return {
        "message": "Check logs for JSON structured entries",
        "request_id": rid,
        "timestamp": datetime.utcnow().isoformat()
    }

# Serve logo from root path for backward compatibility
@app.route('/logo.png')
def serve_logo():
    return send_from_directory(app.static_folder, 'logo.png')

# Import SPA routing to register catch-all routes LAST (after all blueprints)
import serve_spa  # This registers /<path:path> catch-all AFTER all API routes

if __name__ == "__main__":
    # Initialize database
    init_db()
    port = int(os.getenv("PORT", "8080"))  # fallback is 8080 now
    app.run(host="0.0.0.0", port=port, debug=True)