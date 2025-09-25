import os
import io
import base64
import time
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, send_from_directory, render_template, abort, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Database models ---
from models import init_db, get_session, User, PosterJob, Poster, Asset, PosterMode, PosterStatus, PosterStyle
from poster import bp as poster_bp
from app_auth import auth_bp
from app_library import library_bp
from app_legal import legal_bp
from mailer import send_email_post, MailError
from auth import bp as new_auth_bp, bcrypt
from app_payments import payments_bp
from storage import bp as storage_bp
from ads import bp as ads_bp
from ads_portal import bp as ads_portal_bp
from me import bp as me_bp
from me_alias import bp as auth_alias_bp
from webhooks import bp as webhooks_bp
from app_chat import bp as chat_bp

# --- Optional OpenAI (auto-disabled if key missing) ---
OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

load_dotenv()

# ---------------------- ENV / CONFIG ----------------------
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))  # reject > 20MB
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

# Session cookie configuration for SPA
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",  # or "None" if cross-site
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true",  # True in production
)

# CORS configuration - strict for production
cors_origins_env = os.getenv("CORS_ORIGINS", "https://minidreamposter.soulbridgeai.com")
cors_origins = cors_origins_env.split(",") + ["http://localhost:5173"]  # prod + dev
CORS(app, supports_credentials=True, origins=cors_origins)

# Initialize bcrypt
bcrypt.init_app(app)

# Register blueprints
app.register_blueprint(new_auth_bp)  # Use new JWT auth
app.register_blueprint(poster_bp)
app.register_blueprint(library_bp)
app.register_blueprint(legal_bp)
app.register_blueprint(payments_bp)  # Stripe payments
app.register_blueprint(storage_bp)   # S3/R2 storage
app.register_blueprint(ads_bp)       # Ad-free subscriptions
app.register_blueprint(ads_portal_bp) # Customer portal
app.register_blueprint(me_bp)        # User info endpoint
app.register_blueprint(auth_alias_bp) # /api/auth/whoami alias
app.register_blueprint(webhooks_bp)   # Stripe webhooks
app.register_blueprint(chat_bp)       # OpenAI chat

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
    font_title = None
    font_tag = None
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
        # textlength may not give height; estimate with font metrics
        try:
            bbox = draw.textbbox((0, 0), title, font=font_title)
            th = bbox[3] - bbox[1]
            tw = bbox[2] - bbox[0]
        except Exception:
            pass

        x = (W - tw) / 2
        y = H - th - max(20, H // 18)

        # subtle glow
        for r in range(6):
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
        "service": "mini-dream-poster",
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
    subject = data.get("subject", "Hello from Mini Dream Poster")
    html = data.get("html", "<p>Test email.</p>")

    if not to:
        return jsonify({"ok": False, "error": "Missing 'to'"}), 400

    try:
        res = send_email_post(to=to, subject=subject, html=html)
        return jsonify({"ok": True, "id": res.get("id")})
    except MailError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# DEV ONLY: serve local storage dir so returned /storage/... URLs load in browser
@app.get("/storage/<path:key>")
def storage(key: str):
    """Serve files from local storage directory"""
    storage_root = os.path.join(os.getcwd(), "storage")
    return send_from_directory(storage_root, key)

@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)


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


# ---------------------- SPA ROUTES ----------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    """Serve React SPA with proper fallback to index.html"""
    # Don't intercept API routes
    if path.startswith("api/") or path.startswith("uploads/") or path.startswith("storage/"):
        abort(404)

    # If path exists as static file, serve it directly (CSS, JS, assets)
    static_path = os.path.join(app.static_folder or "static", path)
    if path and os.path.exists(static_path) and not path.endswith('.html'):
        resp = make_response(send_from_directory(app.static_folder or "static", path))
        # Add cache-busting headers for CSS/JS files to force reload
        if path.endswith(('.css', '.js')):
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
        return resp

    # Always serve index.html with no-cache headers for SPA routing
    index_path = os.path.join(app.static_folder or "static", "index.html")
    if os.path.exists(index_path):
        resp = make_response(send_from_directory(app.static_folder or "static", "index.html"))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    else:
        return "<h1>React app not found</h1><p>Make sure the frontend is built and copied to static/</p>", 404

# ---------------------- MAIN ----------------------
@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat(), "openai": bool(oai_client)}

if __name__ == "__main__":
    # Initialize database
    init_db()
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)