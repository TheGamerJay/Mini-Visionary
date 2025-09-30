# app_library.py
from __future__ import annotations
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

from flask import Blueprint, request, jsonify, g, current_app
from sqlalchemy import func, or_

from models import (
    get_session, Poster, Asset, PosterJob, CreditLedger,
    PosterStyle, User
)
from auth import auth_required

library_bp = Blueprint("library", __name__, url_prefix="/api")

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

def allowed_file(filename, allowed_exts=ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

def save_upload_file(file, subdir="profiles/avatars"):
    """Save uploaded file and return relative URL"""
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        raise ValueError("File type not allowed")

    # Generate unique filename
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', subdir)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)

    # Return URL path
    return f"/static/uploads/{subdir}/{unique_filename}"

@library_bp.get("/library")
@auth_required
def get_library():
    """
    Get user's poster library with filtering and pagination
    Query params: style, page, limit, search
    """
    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 20)), 100)  # Max 100 per page
    style_filter = request.args.get("style")
    search = request.args.get("search", "").strip()

    offset = (page - 1) * limit

    with get_session() as s:
        query = s.query(Poster).filter_by(
            user_id=g.user.id,
            is_deleted=False
        )

        # Apply filters
        if style_filter and style_filter in PosterStyle._value2member_map_:
            query = query.filter_by(style=PosterStyle(style_filter))

        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Poster.title.ilike(like),
                    Poster.tagline.ilike(like)
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        posters = query.order_by(
            Poster.created_at.desc()
        ).offset(offset).limit(limit).all()

        # Format response
        poster_list = []
        for poster in posters:
            asset = s.query(Asset).filter_by(id=poster.output_asset_id).first()
            poster_list.append({
                "id": poster.id,
                "title": poster.title,
                "tagline": poster.tagline,
                "style": poster.style.value if poster.style else None,
                "url": asset.public_url if asset else None,
                "width": poster.width,
                "height": poster.height,
                "is_private": poster.is_private,
                "created_at": poster.created_at.isoformat(),
                "job_id": poster.job_id
            })

        return jsonify({
            "ok": True,
            "posters": poster_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })

@library_bp.get("/posters/<int:poster_id>")
@auth_required
def get_poster(poster_id):
    """Get single poster details"""
    with get_session() as s:
        poster = s.query(Poster).filter_by(
            id=poster_id,
            user_id=g.user.id,
            is_deleted=False
        ).first()

        if not poster:
            return jsonify({"ok": False, "error": "Poster not found"}), 404

        asset = s.query(Asset).filter_by(id=poster.output_asset_id).first()
        job = s.query(PosterJob).filter_by(id=poster.job_id).first()

        job_payload = None
        if job:
            job_payload = {
                "id": job.id,
                "mode": job.mode.value if getattr(job, "mode", None) else None,
                "prompt": job.prompt,
                "status": job.status.value if getattr(job, "status", None) else None
            }

        return jsonify({
            "ok": True,
            "poster": {
                "id": poster.id,
                "title": poster.title,
                "tagline": poster.tagline,
                "style": poster.style.value if poster.style else None,
                "url": asset.public_url if asset else None,
                "width": poster.width,
                "height": poster.height,
                "is_private": poster.is_private,
                "created_at": poster.created_at.isoformat(),
                "job": job_payload
            }
        })

@library_bp.put("/posters/<int:poster_id>")
@auth_required
def update_poster(poster_id):
    """
    Update poster metadata
    Body: {title?, tagline?, is_private?}
    """
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "JSON body required"}), 400

    with get_session() as s:
        poster = s.query(Poster).filter_by(
            id=poster_id,
            user_id=g.user.id,
            is_deleted=False
        ).first()

        if not poster:
            return jsonify({"ok": False, "error": "Poster not found"}), 404

        # Update fields if provided
        if "title" in data:
            title = (data["title"] or "").strip()
            poster.title = title[:160] if title else None

        if "tagline" in data:
            tagline = (data["tagline"] or "").strip()
            poster.tagline = tagline[:220] if tagline else None

        if "is_private" in data:
            poster.is_private = bool(data["is_private"])

        poster.updated_at = datetime.utcnow()
        s.commit()

        return jsonify({
            "ok": True,
            "poster": {
                "id": poster.id,
                "title": poster.title,
                "tagline": poster.tagline,
                "is_private": poster.is_private,
                "updated_at": poster.updated_at.isoformat()
            }
        })

@library_bp.delete("/posters/<int:poster_id>")
@auth_required
def delete_poster(poster_id):
    """Soft delete poster"""
    with get_session() as s:
        poster = s.query(Poster).filter_by(
            id=poster_id,
            user_id=g.user.id,
            is_deleted=False
        ).first()

        if not poster:
            return jsonify({"ok": False, "error": "Poster not found"}), 404

        poster.is_deleted = True
        poster.updated_at = datetime.utcnow()
        s.commit()

        return jsonify({"ok": True, "message": "Poster deleted"})

@library_bp.get("/profile")
@auth_required
def get_profile():
    """Get user profile with stats"""
    with get_session() as s:
        db_user = s.query(User).filter_by(id=g.user.id).first()
        if not db_user:
            return jsonify({"ok": False, "error": "User not found"}), 404

        poster_count = s.query(Poster).filter_by(
            user_id=db_user.id,
            is_deleted=False
        ).count()

        credit_spent = s.query(func.sum(CreditLedger.amount)).filter(
            CreditLedger.user_id == db_user.id,
            CreditLedger.event == 'spend'
        ).scalar() or 0

        credit_purchased = s.query(func.sum(CreditLedger.amount)).filter(
            CreditLedger.user_id == db_user.id,
            CreditLedger.event == 'purchase'
        ).scalar() or 0

        avatar = getattr(db_user, 'avatar_url', None)
        return jsonify({
            "ok": True,
            "profile": {
                "id": db_user.id,
                "email": db_user.email,
                "display_name": db_user.display_name,
                "avatar_image_url": avatar if avatar and not avatar.startswith('data:video/') else None,
                "avatar_video_url": avatar if avatar and avatar.startswith('data:video/') else None,
                "plan": db_user.plan,
                "credits": db_user.credits,
                "created_at": db_user.created_at.isoformat(),
                "stats": {
                    "posters_created": poster_count,
                    "credits_spent": abs(credit_spent),
                    "credits_purchased": credit_purchased
                }
            }
        })

@library_bp.route("/profile", methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"], strict_slashes=False)
@auth_required
def update_profile():
    """
    Update user profile
    Supports both multipart/form-data (file uploads) and application/json
    """
    # Handle OPTIONS for CORS preflight
    if request.method == "OPTIONS":
        return ("", 204)

    # Handle GET for fetching current profile
    if request.method == "GET":
        with get_session() as s:
            db_user = s.query(User).filter_by(id=g.user.id).first()
            if not db_user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            avatar = getattr(db_user, 'avatar_url', None)
            is_video = avatar and (avatar.startswith('data:video/') or avatar.endswith('.mp4'))

            return jsonify({
                "ok": True,
                "profile": {
                    "id": db_user.id,
                    "display_name": db_user.display_name,
                    "avatar_image_url": avatar if avatar and not is_video else None,
                    "avatar_video_url": avatar if avatar and is_video else None,
                    "avatar_url": avatar
                }
            })

    try:
        with get_session() as s:
            db_user = s.query(User).filter_by(id=g.user.id).first()
            if not db_user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            # Check if this is a multipart upload or JSON
            is_multipart = request.content_type and 'multipart/form-data' in request.content_type

            if is_multipart:
                # Handle file uploads
                display_name = request.form.get("display_name", "").strip()
                avatar_file = request.files.get("avatar")

                if display_name:
                    if len(display_name) == 0:
                        return jsonify({"ok": False, "error": "Display name cannot be empty"}), 400
                    db_user.display_name = display_name[:120]

                if avatar_file and avatar_file.filename:
                    # Check file size
                    avatar_file.seek(0, os.SEEK_END)
                    file_size = avatar_file.tell()
                    avatar_file.seek(0)

                    if file_size > MAX_FILE_SIZE:
                        return jsonify({"ok": False, "error": f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB"}), 413

                    # Check file type
                    ext = avatar_file.filename.rsplit('.', 1)[1].lower() if '.' in avatar_file.filename else ''
                    if ext not in ALLOWED_EXTENSIONS:
                        return jsonify({"ok": False, "error": "Only png/jpg/jpeg/gif/webp/mp4 allowed"}), 415

                    # Save file
                    avatar_url = save_upload_file(avatar_file, "profiles/avatars")
                    db_user.avatar_url = avatar_url

            else:
                # Handle JSON (backward compatibility with data URLs)
                data = request.get_json()
                if not data:
                    return jsonify({"ok": False, "error": "Request body required"}), 400

                if "display_name" in data:
                    display_name = (data["display_name"] or "").strip()
                    if not display_name:
                        return jsonify({"ok": False, "error": "Display name cannot be empty"}), 400
                    db_user.display_name = display_name[:120]

                # Handle data URL uploads (fallback)
                if "avatar_image_url" in data:
                    avatar_image_url = (data["avatar_image_url"] or "").strip()
                    db_user.avatar_url = avatar_image_url if avatar_image_url else None

                if "avatar_video_url" in data:
                    avatar_video_url = (data["avatar_video_url"] or "").strip()
                    db_user.avatar_url = avatar_video_url if avatar_video_url else None

            db_user.updated_at = datetime.utcnow()
            s.commit()

            avatar = getattr(db_user, 'avatar_url', None)
            # Determine if it's a video or image
            is_video = avatar and (avatar.startswith('data:video/') or avatar.endswith('.mp4'))

            return jsonify({
                "ok": True,
                "profile": {
                    "id": db_user.id,
                    "display_name": db_user.display_name,
                    "avatar_image_url": avatar if avatar and not is_video else None,
                    "avatar_video_url": avatar if avatar and is_video else None,
                    "avatar_url": avatar,
                    "updated_at": db_user.updated_at.isoformat()
                }
            })

    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.exception("Profile update failed")
        return jsonify({"ok": False, "error": "Server error"}), 500

# Alternative endpoint for production compatibility (POST only)
@library_bp.route("/profile/upload", methods=["POST", "OPTIONS"], strict_slashes=False)
@auth_required
def upload_profile():
    """
    Alternative profile upload endpoint (POST only)
    Workaround for servers that block PUT/PATCH on /profile
    """
    if request.method == "OPTIONS":
        return ("", 204)

    try:
        with get_session() as s:
            db_user = s.query(User).filter_by(id=g.user.id).first()
            if not db_user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            is_multipart = request.content_type and 'multipart/form-data' in request.content_type

            if is_multipart:
                display_name = request.form.get("display_name", "").strip()
                avatar_file = request.files.get("avatar")

                if display_name:
                    db_user.display_name = display_name[:120]

                if avatar_file and avatar_file.filename:
                    avatar_file.seek(0, os.SEEK_END)
                    file_size = avatar_file.tell()
                    avatar_file.seek(0)

                    if file_size > MAX_FILE_SIZE:
                        return jsonify({"ok": False, "error": f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB"}), 413

                    ext = avatar_file.filename.rsplit('.', 1)[1].lower() if '.' in avatar_file.filename else ''
                    if ext not in ALLOWED_EXTENSIONS:
                        return jsonify({"ok": False, "error": "Only png/jpg/jpeg/gif/webp/mp4 allowed"}), 415

                    avatar_url = save_upload_file(avatar_file, "profiles/avatars")
                    db_user.avatar_url = avatar_url
            else:
                data = request.get_json()
                if not data:
                    return jsonify({"ok": False, "error": "Request body required"}), 400

                if "display_name" in data:
                    display_name = (data["display_name"] or "").strip()
                    if display_name:
                        db_user.display_name = display_name[:120]

                if "avatar_image_url" in data:
                    avatar_image_url = (data["avatar_image_url"] or "").strip()
                    db_user.avatar_url = avatar_image_url if avatar_image_url else None

                if "avatar_video_url" in data:
                    avatar_video_url = (data["avatar_video_url"] or "").strip()
                    db_user.avatar_url = avatar_video_url if avatar_video_url else None

            db_user.updated_at = datetime.utcnow()
            s.commit()

            avatar = getattr(db_user, 'avatar_url', None)
            is_video = avatar and (avatar.startswith('data:video/') or avatar.endswith('.mp4'))

            return jsonify({
                "ok": True,
                "profile": {
                    "id": db_user.id,
                    "display_name": db_user.display_name,
                    "avatar_image_url": avatar if avatar and not is_video else None,
                    "avatar_video_url": avatar if avatar and is_video else None,
                    "avatar_url": avatar,
                    "updated_at": db_user.updated_at.isoformat()
                }
            })

    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.exception("Profile upload failed")
        return jsonify({"ok": False, "error": "Server error"}), 500