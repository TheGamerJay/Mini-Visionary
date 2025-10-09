import os, base64, traceback
from io import BytesIO
from functools import wraps
from datetime import timedelta

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from werkzeug.security import generate_password_hash, check_password_hash

# Use existing Mini-Visionary models and session management
from models import User, ImageJob, Library, GalleryPost, Reaction, get_session

# --- OpenAI new SDK ---
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Stripe ---
import stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)

# Config
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change_me")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change_me_jwt")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)  # 7 days instead of 15 minutes
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://minivisionary.soulbridgeai.com")
CREDIT_START = int(os.getenv("CREDIT_START", "20"))
COST_GEN = int(os.getenv("CREDIT_COST_GENERATE", "10"))
COST_EDIT = int(os.getenv("CREDIT_COST_EDIT", "1"))
COST_VARIATION = int(os.getenv("CREDIT_COST_VARIATION", "5"))
COST_REMIX = int(os.getenv("CREDIT_COST_REMIX", "15"))
COST_GALLERY_POST = int(os.getenv("CREDIT_COST_GALLERY_POST", "3"))

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

    # Check if user exists and has valid password hash
    if not user or not user.password_hash or not user.password_hash.strip():
        return fail("Invalid credentials.", 401)

    # Verify password
    try:
        if not check_password_hash(user.password_hash, password):
            return fail("Invalid credentials.", 401)
    except ValueError:
        # Invalid password hash format
        return fail("Invalid credentials.", 401)

    token = create_access_token(identity=user.id)
    return jsonify({"ok": True, "token": token, "credits": user.credits})

@app.post("/api/auth/forgot")
@with_session
def forgot_password(db):
    """Send password reset email"""
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()

        if not email:
            return fail("Email required.", 400)

        user = db.query(User).filter_by(email=email).first()

        # Always return success to prevent email enumeration
        if not user:
            return jsonify({"ok": True, "message": "If that email exists, a reset link has been sent."})

        # Generate reset token (JWT with 1 hour expiration)
        reset_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))

        # Send email
        from mailer import send_email_post
        reset_url = f"{FRONTEND_ORIGIN}/reset-password.html?token={reset_token}"

        html = f"""
        <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Reset Your Password</h2>
            <p>Hi there,</p>
            <p>You requested to reset your password for Mini-Visionary. Click the button below to reset it:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_url}" style="background: linear-gradient(90deg, #22d3ee, #ec4899); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Reset Password</a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{reset_url}</p>
            <p><strong>This link expires in 1 hour.</strong></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px;">Mini-Visionary - You Envision it, We Generate it</p>
        </div>
        """

        send_email_post(
            to=email,
            subject="Reset Your Password - Mini-Visionary",
            html=html
        )

        return jsonify({"ok": True, "message": "If that email exists, a reset link has been sent."})
    except Exception as e:
        traceback.print_exc()
        return fail("Failed to send reset email. Please try again later.", 500)

@app.post("/api/auth/reset")
@with_session
def reset_password(db):
    """Reset password with token"""
    try:
        data = request.get_json() or {}
        token = data.get("token", "").strip()
        new_password = data.get("password", "")

        if not token or not new_password:
            return fail("Token and password required.", 400)

        if len(new_password) < 8:
            return fail("Password must be at least 8 characters.", 400)

        # Verify token
        from flask_jwt_extended import decode_token
        try:
            payload = decode_token(token)
            user_id = int(payload["sub"])
        except Exception:
            return fail("Invalid or expired reset token.", 401)

        user = db.query(User).get(user_id)
        if not user:
            return fail("User not found.", 404)

        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.commit()

        return jsonify({"ok": True, "message": "Password reset successfully. You can now login."})
    except Exception as e:
        traceback.print_exc()
        return fail("Failed to reset password.", 500)

@app.get("/api/me")
@jwt_required()
@with_session
def me(db):
    uid = get_jwt_identity()
    user = db.query(User).get(uid)
    return jsonify({
        "ok": True,
        "email": user.email,
        "credits": user.credits,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "profile_picture_url": user.profile_picture_url,
            "avatar_url": user.avatar_url,
            "credits": user.credits,
            "ad_free": user.ad_free,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    })

@app.put("/api/profile/update")
@jwt_required()
@with_session
def update_profile(db):
    """Update user profile (display name)"""
    uid = get_jwt_identity()
    user = db.query(User).get(uid)

    if not user:
        return fail("User not found", 404)

    data = request.get_json()
    display_name = data.get("display_name", "").strip()

    if not display_name:
        return fail("Display name is required", 400)

    if len(display_name) > 50:
        return fail("Display name must be 50 characters or less", 400)

    user.display_name = display_name
    db.commit()

    return jsonify({"ok": True, "display_name": display_name})

@app.post("/api/profile/change-password")
@jwt_required()
@with_session
def change_password(db):
    """Change user password"""
    uid = get_jwt_identity()
    user = db.query(User).get(uid)

    if not user:
        return fail("User not found", 404)

    data = request.get_json()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return fail("Current and new password are required", 400)

    # Verify current password
    if not bcrypt.checkpw(current_password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return fail("Current password is incorrect", 401)

    if len(new_password) < 8:
        return fail("New password must be at least 8 characters", 400)

    # Hash and update new password
    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.commit()

    return jsonify({"ok": True, "message": "Password updated successfully"})

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
        db.add(job)
        db.flush()  # Get job.id

        # Auto-add to Mini Library
        lib_item = Library(
            user_id=user.id,
            image_job_id=job.id,
            collection_name="mini_library"
        )
        db.add(lib_item)
        db.commit()

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
        try:
            resp = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                n=1,
                response_format="b64_json"
            )
            b64 = resp.data[0].b64_json
            png = base64.b64decode(b64)
        except Exception as openai_err:
            # Check if it's a content policy violation
            error_str = str(openai_err)
            if 'safety system' in error_str or 'content_policy_violation' in error_str:
                return fail("🚫 Your prompt was blocked by OpenAI's safety system. Please try a different, safer prompt.", 400)
            # Re-raise other errors
            raise

        job = ImageJob(
            user_id=user.id,
            kind="generate",
            prompt=prompt,
            size=size,
            image_png=png,
            credits_used=COST_GEN
        )
        db.add(job)
        db.flush()  # Get job.id

        # Auto-add to Mini Library
        lib_item = Library(
            user_id=user.id,
            image_job_id=job.id,
            collection_name="mini_library"
        )
        db.add(lib_item)
        db.commit()

        # Return format compatible with old frontend
        return jsonify({
            "ok": True,
            "job_id": job.id,
            "credits": user.credits,
            "image_b64_png": b64
        })
    except Exception as e:
        return fail("Image generation failed.", 500, e)

@app.post("/api/poster/remix")
@jwt_required()
@limiter.limit("12/minute")
@with_session
def poster_remix(db):
    """Edit a reference image based on a prompt using DALL-E 3 image edits (gpt-image-1)"""
    try:
        uid = get_jwt_identity()
        user = db.query(User).get(uid)

        if not user:
            return fail("User not found", 404)

        # Get uploaded image file
        if 'image' not in request.files:
            return fail("No image file provided", 400)

        image_file = request.files['image']
        prompt = request.form.get('prompt', '').strip()
        size = request.form.get('size', '1024x1024')

        if not prompt:
            return fail("Prompt required for image edits", 400)

        # DALL-E 3 edits supports 512x512 or 1024x1024
        if size not in ["512x512", "1024x1024"]:
            size = "1024x1024"

        ok, err = ensure_credits(user, COST_GEN)
        if not ok:
            return fail(err, 402)

        # Read image data and convert to PNG
        from PIL import Image
        import io
        image_data = image_file.read()
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")

        # Save as PNG in memory
        png_io = io.BytesIO()
        img.save(png_io, format="PNG")
        png_io.seek(0)
        image_png_bytes = png_io.getvalue()

        # Save to temp file for OpenAI API
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_png_bytes)
            tmp_path = tmp.name

        try:
            # Use DALL-E 3 image edits API (gpt-image-1)
            with open(tmp_path, "rb") as img_file:
                resp = client.images.edit(
                    model="gpt-image-1",
                    image=img_file,
                    prompt=prompt,
                    size=size,
                    n=1,
                    response_format="b64_json"
                )

            # Get base64 image
            b64 = resp.data[0].b64_json
            png = base64.b64decode(b64)

        except Exception as openai_err:
            error_str = str(openai_err)
            if 'safety system' in error_str or 'content_policy_violation' in error_str:
                return fail("🚫 Edit blocked by OpenAI's safety system. Try a different prompt or image.", 400)
            raise
        finally:
            # Clean up temp file
            import os
            os.unlink(tmp_path)

        # Store in database
        job = ImageJob(
            user_id=user.id,
            kind="remix",
            prompt=f"Edit: {prompt}",
            size=size,
            image_png=png,
            credits_used=COST_GEN
        )
        db.add(job)
        db.flush()

        # Auto-add to Mini Library
        lib_item = Library(
            user_id=user.id,
            image_job_id=job.id,
            collection_name="mini_library"
        )
        db.add(lib_item)
        db.commit()

        # Return in items[] format expected by frontend
        return jsonify({
            "ok": True,
            "job_id": job.id,
            "credits": user.credits,
            "mode": "remix",
            "model": "gpt-image-1",
            "items": [{
                "url": f"data:image/png;base64,{b64}"
            }]
        })
    except Exception as e:
        traceback.print_exc()
        return fail("Image edit failed.", 500, e)

# --- Image Edit ---
@app.post("/api/poster/edit")
@jwt_required()
@with_session
def edit_poster(db):
    try:
        uid = get_jwt_identity()
        user = db.query(User).get(uid)
        body = request.get_json() or {}
        prompt = body.get("prompt") or ""
        job_id = body.get("job_id")

        if not prompt:
            return fail("Prompt required.")

        if not job_id:
            return fail("job_id required.")

        # Get original image
        orig_job = db.query(ImageJob).filter_by(id=job_id, user_id=uid).first()
        if not orig_job:
            return fail("Original image not found.", 404)

        ok, err = ensure_credits(user, COST_EDIT)
        if not ok:
            return fail(err, 402)

        # Save original image to temp file for OpenAI API
        import tempfile
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(orig_job.image_png)
            tmp_path = tmp.name

        # Create transparent mask (full edit)
        img = Image.open(tmp_path)
        mask = Image.new("RGBA", img.size, (0, 0, 0, 0))
        mask_path = tmp_path.replace(".png", "_mask.png")
        mask.save(mask_path)

        # OpenAI edit call
        try:
            with open(tmp_path, "rb") as img_file, open(mask_path, "rb") as mask_file:
                resp = client.images.edit(
                    model="dall-e-2",  # Only dall-e-2 supports edit
                    image=img_file,
                    mask=mask_file,
                    prompt=prompt,
                    n=1,
                    size="512x512",  # dall-e-2 only supports 256x256, 512x512, 1024x1024
                    response_format="b64_json"
                )
        except Exception as openai_err:
            # Check if it's a content policy violation
            error_str = str(openai_err)
            if 'safety system' in error_str or 'content_policy_violation' in error_str:
                return fail("🚫 Edit blocked by OpenAI's safety system. DALL-E 2 edit is very strict - try generating a new image instead.", 400)
            # Re-raise other errors
            raise

        b64 = resp.data[0].b64_json
        png = base64.b64decode(b64)

        # Clean up temp files
        import os
        os.unlink(tmp_path)
        os.unlink(mask_path)

        job = ImageJob(
            user_id=user.id,
            kind="edit",
            prompt=prompt,
            size="512x512",
            image_png=png,
            credits_used=COST_EDIT
        )
        db.add(job)
        db.flush()

        # Auto-add to Mini Library
        lib_item = Library(
            user_id=user.id,
            image_job_id=job.id,
            collection_name="mini_library"
        )
        db.add(lib_item)
        db.commit()

        return jsonify({
            "ok": True,
            "job_id": job.id,
            "credits": user.credits,
            "image_b64_png": b64
        })
    except Exception as e:
        return fail("Image edit failed.", 500, e)

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

# --- Library API (PostgreSQL storage) ---
@app.post("/api/library/add")
@jwt_required()
@with_session
def add_to_library(db):
    uid = get_jwt_identity()
    data = request.get_json() or {}
    image_job_id = data.get("image_job_id")
    collection = data.get("collection", "mini_library")  # mini_library or main_library

    if not image_job_id:
        return fail("image_job_id required")

    # Check if image exists and belongs to user
    job = db.query(ImageJob).filter_by(id=image_job_id, user_id=uid).first()
    if not job:
        return fail("Image not found", 404)

    # Check if already in library
    existing = db.query(Library).filter_by(
        user_id=uid,
        image_job_id=image_job_id,
        collection_name=collection
    ).first()

    if existing:
        return jsonify({"ok": True, "message": "Already in library"})

    # Add to library
    lib_item = Library(
        user_id=uid,
        image_job_id=image_job_id,
        collection_name=collection
    )
    db.add(lib_item)
    db.commit()

    return jsonify({"ok": True, "id": lib_item.id})


@app.post("/api/library/save")
@jwt_required()
@with_session
def save_to_library(db):
    """Save an image (from gallery or elsewhere) to library"""
    uid = get_jwt_identity()
    data = request.get_json() or {}

    image_url = data.get("image_url")
    prompt = data.get("prompt", "Saved Image")

    if not image_url:
        return fail("image_url required", 400)

    # For gallery images, we need to create a placeholder ImageJob
    # or find an existing one with the same URL
    job = db.query(ImageJob).filter_by(
        user_id=uid,
        result_image_url=image_url
    ).first()

    if not job:
        # Create a placeholder job for this external image
        job = ImageJob(
            user_id=uid,
            prompt=prompt,
            status="completed",
            result_image_url=image_url
        )
        db.add(job)
        db.flush()  # Get the ID

    # Add to library
    lib_item = Library(
        user_id=uid,
        image_job_id=job.id,
        collection_name="main_library"
    )
    db.add(lib_item)
    db.commit()

    return jsonify({"ok": True, "id": lib_item.id})

@app.get("/api/library")
@jwt_required()
@with_session
def get_library(db):
    uid = get_jwt_identity()
    collection = request.args.get("collection", "mini_library")

    items = db.query(Library).filter_by(
        user_id=uid,
        collection_name=collection
    ).order_by(Library.created_at.desc()).all()

    result = [{
        "id": item.id,
        "image_job_id": item.image_job_id,
        "prompt": item.image_job.prompt,
        "created_at": item.created_at.isoformat()
    } for item in items]

    return jsonify({"ok": True, "items": result, "count": len(result)})


@app.delete("/api/library/clear-all")
@jwt_required()
@with_session
def clear_all_library(db):
    """Delete ALL library items for current user."""
    uid = get_jwt_identity()

    # Delete all library entries for this user
    db.query(Library).filter_by(user_id=uid).delete()
    db.commit()

    return jsonify({"ok": True, "message": "All library items cleared"})


@app.delete("/api/library/<int:lib_id>")
@jwt_required()
@with_session
def delete_from_library(db, lib_id):
    uid = get_jwt_identity()

    item = db.query(Library).filter_by(id=lib_id, user_id=uid).first()
    if not item:
        return fail("Library item not found", 404)

    db.delete(item)
    db.commit()

    return jsonify({"ok": True})


# --- Add Credits (Testing) ---
@app.post("/api/admin/add-credits")
@jwt_required()
@with_session
def add_credits_admin(db):
    """Add 100 credits to current user for testing."""
    uid = get_jwt_identity()
    user = db.query(User).get(uid)

    if not user:
        return fail("User not found", 404)

    user.credits += 100
    db.commit()

    return jsonify({"ok": True, "credits": user.credits, "message": "Added 100 credits"})


# --- Payments ---
@app.post("/api/payments/checkout")
@jwt_required()
@with_session
def create_checkout(db):
    try:
        uid = get_jwt_identity()
        user = db.query(User).get(uid)
        body = request.get_json() or {}

        sku = body.get("sku")
        success_url = body.get("success_url", "https://minivisionary.soulbridgeai.com/static/wallet.html?payment=success")
        cancel_url = body.get("cancel_url", "https://minivisionary.soulbridgeai.com/static/store.html?payment=canceled")

        # Define credit packages with Stripe Price IDs
        packages = {
            "starter": {
                "credits": 60,
                "price_id": os.getenv("STORE_PRICE_STARTER", "price_1SAx3wQhGNo4dMlWbpZ5h2uy"),
                "mode": "payment"
            },
            "standard": {
                "credits": 100,
                "price_id": os.getenv("STORE_PRICE_STANDARD", "price_1SAx4eQhGNo4dMlWWq23PoHo"),
                "mode": "payment"
            },
            "studio": {
                "credits": 400,
                "price_id": os.getenv("STORE_PRICE_STUDIO", "price_1SAx66QhGNo4dMlWRdR1m78Q"),
                "mode": "payment"
            },
            "adfree": {
                "credits": 0,
                "price_id": os.getenv("STORE_PRICE_ADFREE", "price_1SB0j5QhGNo4dMlWyYwGJabi"),
                "mode": "subscription"
            }
        }

        if sku not in packages:
            return fail("Invalid package.", 400)

        package = packages[sku]

        # Create Stripe checkout session using Price ID
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": package["price_id"],
                "quantity": 1,
            }],
            mode=package["mode"],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user.id),
            metadata={
                "user_id": str(user.id),
                "credits": str(package["credits"]),
                "sku": sku
            }
        )

        return jsonify({"ok": True, "url": session.url})
    except Exception as e:
        traceback.print_exc()
        return fail(f"Checkout failed: {str(e)}", 500)

# --- Gallery ---
@app.post("/api/gallery/post")
@jwt_required()
@with_session
def gallery_post(db):
    """Deduct credits for posting to community gallery"""
    try:
        uid = get_jwt_identity()
        user = db.query(User).get(uid)

        # Check and deduct credits
        ok, err = ensure_credits(user, COST_GALLERY_POST)
        if not ok:
            return fail(err, 402)

        user.credits -= COST_GALLERY_POST
        db.commit()

        # Create gallery post with image_url from request
        import json
        data = request.get_json() or {}
        prompt = data.get("prompt", "").strip()
        story = data.get("story", "").strip()
        tags = data.get("tags", [])
        image_url = data.get("image_url", "").strip()

        if not prompt or not image_url:
            return fail("Prompt and image required.", 400)

        post = GalleryPost(
            user_id=uid,
            image_url=image_url,
            prompt=prompt,
            story=story or None,
            tags=json.dumps(tags),
            is_deleted=False
        )
        db.add(post)
        db.commit()

        return jsonify({
            "ok": True,
            "credits": user.credits,
            "post_id": post.id,
            "message": f"Posted to gallery! {COST_GALLERY_POST} credits deducted."
        })
    except Exception as e:
        traceback.print_exc()
        return fail(f"Gallery post failed: {str(e)}", 500)

@app.get("/api/gallery/posts")
@with_session
def get_gallery_posts(db):
    """Get all community gallery posts with optional user reactions"""
    import json
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    try:
        # Try to get current user (optional - endpoint works without auth)
        current_user_id = None
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
        except:
            pass

        posts = db.query(GalleryPost).filter_by(is_deleted=False).order_by(GalleryPost.created_at.desc()).all()

        result = []
        for post in posts:
            reaction_counts = {
                "love": 0, "magic": 0, "peace": 0, "fire": 0,
                "gratitude": 0, "star": 0, "applause": 0, "support": 0
            }
            user_reaction = None

            for reaction in post.reactions:
                if reaction.reaction_type in reaction_counts:
                    reaction_counts[reaction.reaction_type] += 1
                # Check if this is the current user's reaction
                if current_user_id and reaction.user_id == current_user_id:
                    user_reaction = reaction.reaction_type

            result.append({
                "id": post.id,
                "user_id": post.user_id,
                "url": post.image_url,
                "prompt": post.prompt,
                "story": post.story,
                "tags": json.loads(post.tags) if post.tags else [],
                "reactions": reaction_counts,
                "user_reacted": user_reaction,
                "is_demo": post.is_demo,
                "created_at": post.created_at.isoformat()
            })

        return jsonify({"ok": True, "posts": result})
    except Exception as e:
        traceback.print_exc()
        return fail(f"Failed to load gallery: {str(e)}", 500)

@app.post("/api/gallery/<int:post_id>/react")
@jwt_required()
@with_session
def toggle_reaction(db, post_id):
    """Toggle a reaction on a gallery post"""
    try:
        uid = get_jwt_identity()
        data = request.get_json() or {}
        reaction_type = data.get("reaction_type")

        if not reaction_type:
            return fail("Reaction type required.", 400)

        post = db.query(GalleryPost).filter_by(id=post_id, is_deleted=False).first()
        if not post:
            return fail("Post not found.", 404)

        existing = db.query(Reaction).filter_by(post_id=post_id, user_id=uid).first()

        if existing:
            if existing.reaction_type == reaction_type:
                db.delete(existing)
                db.commit()
                return jsonify({"ok": True, "action": "removed", "reaction_type": reaction_type})
            else:
                existing.reaction_type = reaction_type
                db.commit()
                return jsonify({"ok": True, "action": "changed", "reaction_type": reaction_type})
        else:
            reaction = Reaction(post_id=post_id, user_id=uid, reaction_type=reaction_type)
            db.add(reaction)
            db.commit()
            return jsonify({"ok": True, "action": "added", "reaction_type": reaction_type})
    except Exception as e:
        traceback.print_exc()
        return fail(f"Failed to react: {str(e)}", 500)

@app.get("/api/gallery/<int:post_id>/my-reaction")
@jwt_required()
@with_session
def get_my_reaction(db, post_id):
    """Get current user's reaction to a post"""
    try:
        uid = get_jwt_identity()
        reaction = db.query(Reaction).filter_by(post_id=post_id, user_id=uid).first()
        if reaction:
            return jsonify({"ok": True, "reaction_type": reaction.reaction_type})
        else:
            return jsonify({"ok": True, "reaction_type": None})
    except Exception as e:
        traceback.print_exc()
        return fail(f"Failed to get reaction: {str(e)}", 500)

@app.delete("/api/gallery/<int:post_id>/delete")
@jwt_required()
@with_session
def delete_gallery_post(db, post_id):
    """Delete a gallery post (soft delete, only owner or demo posts cannot be deleted)"""
    try:
        uid = get_jwt_identity()
        post = db.query(GalleryPost).filter_by(id=post_id).first()

        if not post:
            return fail("Post not found", 404)

        # Check if user owns the post
        if post.user_id != uid:
            return fail("You can only delete your own posts", 403)

        # Check if it's a demo post
        if post.is_demo:
            return fail("Demo posts cannot be deleted", 403)

        # Soft delete
        post.is_deleted = True
        db.commit()

        return jsonify({"ok": True, "message": "Post deleted successfully"})
    except Exception as e:
        traceback.print_exc()
        return fail(f"Failed to delete post: {str(e)}", 500)

@app.post("/api/payments/webhook")
@with_session
def stripe_webhook(db):
    """Handle Stripe webhook events (payment completion)"""
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return fail("Invalid payload", 400)
    except stripe.error.SignatureVerificationError:
        return fail("Invalid signature", 400)

    # Handle checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        credits = session.get("metadata", {}).get("credits")

        if user_id and credits:
            user = db.query(User).get(int(user_id))
            if user:
                user.credits += int(credits)
                db.commit()

    return jsonify({"ok": True})

# --- Health ---
@app.get("/api/health")
def health():
    return {"ok": True, "release": os.getenv("RAILWAY_GIT_COMMIT_SHA", "local")}

if __name__ == "__main__":
    # Run library table migration on startup
    try:
        from create_library_table import create_library_table
        create_library_table()
    except Exception:
        pass  # Silently fail if migration has issues

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
