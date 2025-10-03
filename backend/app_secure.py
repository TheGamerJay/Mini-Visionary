import os, base64, traceback
from io import BytesIO
from functools import wraps

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from werkzeug.security import generate_password_hash, check_password_hash

# Use existing Mini-Visionary models and session management
from models import User, ImageJob, get_session

# --- OpenAI new SDK ---
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# Config
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change_me")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change_me_jwt")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://minivisionary.soulbridgeai.com")
CREDIT_START = int(os.getenv("CREDIT_START", "20"))
COST_GEN = int(os.getenv("CREDIT_COST_GENERATE", "10"))
COST_EDIT = int(os.getenv("CREDIT_COST_EDIT", "1"))
COST_VARIATION = int(os.getenv("CREDIT_COST_VARIATION", "5"))
COST_REMIX = int(os.getenv("CREDIT_COST_REMIX", "15"))

# Allowed image sizes
ALLOWED_SIZES = {"1024x1024", "1024x1792", "1792x1024"}

# CORS: restrict to your frontend
CORS(app, resources={r"/api/*": {"origins": [FRONTEND_ORIGIN]}})

# Rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["60/minute", "600/hour"])

# JWT
jwt = JWTManager(app)

# --- Helpers ---
def with_session(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with get_session() as db:
            return fn(db, *args, **kwargs)
    return wrapper

def fail(msg, code=400, e=None):
    if e:
        import sys
        sys.stderr.write(f"ERROR: {msg}\n{traceback.format_exc()}\n")
    return jsonify({"ok": False, "error": msg}), code

# --- Auth ---
@app.post("/api/auth/register")
@limiter.limit("5/minute")
@with_session
def register(db):
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return fail("Email and password required.")
    if db.query(User).filter_by(email=email).first():
        return fail("Email already registered.", 409)
    user = User(email=email, password_hash=generate_password_hash(password), credits=CREDIT_START)
    db.add(user); db.commit()
    token = create_access_token(identity=user.id)
    return jsonify({"ok": True, "token": token, "credits": user.credits})

@app.post("/api/auth/login")
@limiter.limit("10/minute")
@with_session
def login(db):
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = db.query(User).filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
        return fail("Invalid credentials.", 401)
    token = create_access_token(identity=user.id)
    return jsonify({"ok": True, "token": token, "credits": user.credits})

@app.get("/api/me")
@jwt_required()
@with_session
def me(db):
    uid = get_jwt_identity()
    user = db.query(User).get(uid)
    return jsonify({"ok": True, "email": user.email, "credits": user.credits})

# --- Credits ---
def ensure_credits(user, needed):
    if user.credits < needed:
        return False, f"Not enough credits. Need {needed}, have {user.credits}."
    user.credits -= needed
    return True, None

# --- Image Generate (DALL·E 3) ---
@app.post("/api/generate")
@jwt_required()
@limiter.limit("12/minute")
@with_session
def generate(db):
    try:
        uid = get_jwt_identity()
        user = db.query(User).get(uid)
        body = request.get_json() or {}
        prompt = body.get("prompt") or ""
        size = body.get("size") or "1024x1024"

        if not prompt:
            return fail("Prompt required.")

        # Validate size
        if size not in ALLOWED_SIZES:
            return fail(f"Invalid size. Allowed: {', '.join(ALLOWED_SIZES)}")

        ok, err = ensure_credits(user, COST_GEN)
        if not ok:
            return fail(err, 402)

        # OpenAI new SDK call with base64 response
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=1,
            response_format="b64_json"  # ✅ Get base64 directly
        )
        b64 = resp.data[0].b64_json
        png = base64.b64decode(b64)

        job = ImageJob(
            user_id=user.id,
            kind="generate",
            prompt=prompt,
            size=size,
            image_png=png,
            credits_used=COST_GEN
        )
        db.add(job); db.commit()
        return jsonify({
            "ok": True,
            "job_id": job.id,
            "credits": user.credits,
            "image_b64_png": b64
        })
    except Exception as e:
        return fail("Image generation failed.", 500, e)

# --- Legacy endpoint for backward compatibility ---
@app.post("/api/poster/generate")
@jwt_required()
@limiter.limit("12/minute")
@with_session
def poster_generate(db):
    """Legacy endpoint that calls the new generate() logic"""
    try:
        uid = get_jwt_identity()
        user = db.query(User).get(uid)
        body = request.get_json() or {}
        prompt = body.get("prompt") or ""
        size = body.get("size") or "1024x1024"

        # Map common sizes to DALL-E 3 supported sizes
        size_map = {
            "1200x1500": "1024x1792",  # Portrait
            "1500x1200": "1792x1024",  # Landscape
            "512x512": "1024x1024",
            "1024x1024": "1024x1024",
            "1024x1792": "1024x1792",
            "1792x1024": "1792x1024"
        }
        size = size_map.get(size, "1024x1024")

        if not prompt:
            return fail("Prompt required.")

        ok, err = ensure_credits(user, COST_GEN)
        if not ok:
            return fail(err, 402)

        # OpenAI call
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=1,
            response_format="b64_json"
        )
        b64 = resp.data[0].b64_json
        png = base64.b64decode(b64)

        job = ImageJob(
            user_id=user.id,
            kind="generate",
            prompt=prompt,
            size=size,
            image_png=png,
            credits_used=COST_GEN
        )
        db.add(job); db.commit()

        # Return format compatible with old frontend
        return jsonify({
            "ok": True,
            "job_id": job.id,
            "credits": user.credits,
            "image_b64_png": b64
        })
    except Exception as e:
        return fail("Image generation failed.", 500, e)

# --- Image History (paginated) ---
@app.get("/api/history")
@jwt_required()
@with_session
def history(db):
    uid = get_jwt_identity()
    page = int(request.args.get("page", "1"))
    per = min(max(int(request.args.get("per", "12")), 1), 50)
    q = db.query(ImageJob).filter_by(user_id=uid).order_by(ImageJob.id.desc())
    total = q.count()
    rows = q.offset((page-1)*per).limit(per).all()
    items = [{
        "id": r.id, "kind": r.kind, "prompt": r.prompt,
        "size": r.size, "credits_used": r.credits_used,
        "created_at": r.created_at.isoformat()
    } for r in rows]
    return jsonify({"ok": True, "page": page, "per": per, "total": total, "items": items})

# --- Serve PNG by job id (inline preview) ---
@app.get("/api/history/<int:job_id>/png")
@jwt_required()
@with_session
def history_png(db, job_id):
    uid = get_jwt_identity()
    r = db.query(ImageJob).filter_by(id=job_id, user_id=uid).first()
    if not r:
        return fail("Not found.", 404)
    return send_file(BytesIO(r.image_png), mimetype="image/png")

# --- Download PNG (attachment) ---
@app.get("/api/history/<int:job_id>/download")
@jwt_required()
@with_session
def download_image(db, job_id):
    uid = get_jwt_identity()
    r = db.query(ImageJob).filter_by(id=job_id, user_id=uid).first()
    if not r:
        return fail("Not found.", 404)
    filename = f"image_{job_id}.png"
    return send_file(
        BytesIO(r.image_png),
        mimetype="image/png",
        as_attachment=True,
        download_name=filename
    )

# --- Credit Purchase Stub ---
@app.post("/api/credits/purchase")
@jwt_required()
@with_session
def purchase_credits(db):
    # TODO: Stripe Checkout session + webhook to credit the account
    return fail("Credit purchase not yet implemented", 501)

# --- Prompt Refiner (optional) ---
@app.post("/api/refine-prompt")
@jwt_required()
@limiter.limit("30/minute")
@with_session
def refine_prompt(db):
    data = request.get_json() or {}
    rough = data.get("prompt","")
    if not rough:
        return fail("prompt required.")
    try:
        out = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Refine user image prompts: concise, vivid, safe."},
                {"role":"user","content": rough}
            ],
            temperature=0.4
        )
        refined = out.choices[0].message.content.strip()
        return jsonify({"ok": True, "refined": refined})
    except Exception as e:
        return fail("Refine failed.", 500, e)

# --- Health ---
@app.get("/api/health")
def health():
    return {"ok": True, "release": os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
