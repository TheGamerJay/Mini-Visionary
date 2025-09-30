"""
Clean profile picture/video upload endpoint
Handles multipart file uploads for user profiles
"""
import os
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
from auth import auth_required
from models import get_session, User
import uuid

profile_upload_bp = Blueprint('profile_upload', __name__, url_prefix='/api/profile')

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_upload_bp.route('/upload', methods=['POST'])
@auth_required
def upload_profile_picture():
    """
    Upload profile picture or video
    Accepts: multipart/form-data with 'file' field
    Returns: JSON with profile_picture_url
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"ok": False, "error": "No file provided"}), 400

        file = request.files['file']

        if not file or not file.filename:
            return jsonify({"ok": False, "error": "No file selected"}), 400

        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({"ok": False, "error": "Only PNG, JPG, GIF, WebP, MP4 allowed"}), 415

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"ok": False, "error": f"File too large. Max 10MB"}), 413

        # Convert to base64 for database storage (Railway has ephemeral storage)
        import base64
        ext = file.filename.rsplit('.', 1)[1].lower()
        file_data = file.read()
        base64_data = base64.b64encode(file_data).decode('utf-8')

        # Create data URL
        mime_type = 'video/mp4' if ext == 'mp4' else f'image/{ext}'
        profile_picture_url = f"data:{mime_type};base64,{base64_data}"

        # Update database
        with get_session() as session:
            user = session.query(User).filter_by(id=g.user.id).first()
            if not user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            user.profile_picture_url = profile_picture_url
            session.commit()

        return jsonify({
            "ok": True,
            "profile_picture_url": profile_picture_url,
            "is_video": ext == 'mp4'
        }), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@profile_upload_bp.route('/me', methods=['GET'])
@auth_required
def get_profile():
    """Get current user profile"""
    import os
    try:
        with get_session() as session:
            user = session.query(User).filter_by(id=g.user.id).first()
            if not user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            profile_pic = user.profile_picture_url
            is_video = profile_pic and profile_pic.endswith('.mp4')

            payload = {
                "ok": True,
                "profile": {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "profile_picture_url": profile_pic,
                    "is_video": is_video,
                    "credits": user.credits,
                    "ad_free": user.ad_free,
                    "avatar_url": user.avatar_url,
                    "avatar_image_url": user.avatar_url if user.avatar_url and not user.avatar_url.startswith('data:video/') else None,
                    "avatar_video_url": user.avatar_url if user.avatar_url and user.avatar_url.startswith('data:video/') else None,
                    "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None
                },
                "release": os.getenv("GIT_SHA", "dev-local")
            }

            resp = jsonify(payload)
            resp.headers["X-Release"] = payload["release"]
            return resp, 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@profile_upload_bp.route('/update', methods=['PUT', 'PATCH'])
@auth_required
def update_profile_name():
    """Update user profile display name"""
    try:
        data = request.get_json()
        if not data or 'display_name' not in data:
            return jsonify({"ok": False, "error": "display_name required"}), 400

        display_name = data['display_name'].strip()
        if not display_name:
            return jsonify({"ok": False, "error": "display_name cannot be empty"}), 400

        with get_session() as session:
            user = session.query(User).filter_by(id=g.user.id).first()
            if not user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            user.display_name = display_name
            session.commit()

            return jsonify({
                "ok": True,
                "display_name": display_name
            }), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@profile_upload_bp.route('/change-password', methods=['POST'])
@auth_required
def change_password():
    """Change user password"""
    from flask_bcrypt import Bcrypt
    from werkzeug.security import check_password_hash

    bcrypt_instance = Bcrypt()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "error": "Request body required"}), 400

        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()

        if not current_password or not new_password:
            return jsonify({"ok": False, "error": "Both current and new password required"}), 400

        if len(new_password) < 8:
            return jsonify({"ok": False, "error": "Password must be at least 8 characters"}), 400

        with get_session() as session:
            user = session.query(User).filter_by(id=g.user.id).first()
            if not user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            # Verify current password
            password_valid = False
            if user.password_hash:
                # Try bcrypt first
                try:
                    password_valid = bcrypt_instance.check_password_hash(user.password_hash, current_password)
                except:
                    # Fallback to werkzeug
                    password_valid = check_password_hash(user.password_hash, current_password)

            if not password_valid:
                return jsonify({"ok": False, "error": "Current password is incorrect"}), 401

            # Hash and save new password
            user.password_hash = bcrypt_instance.generate_password_hash(new_password).decode('utf-8')
            session.commit()

            return jsonify({"ok": True, "message": "Password changed successfully"}), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500