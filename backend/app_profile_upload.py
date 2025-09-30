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

        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        # Save file
        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'profiles')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)

        # Generate public URL
        profile_picture_url = f"/static/uploads/profiles/{unique_filename}"

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
    try:
        with get_session() as session:
            user = session.query(User).filter_by(id=g.user.id).first()
            if not user:
                return jsonify({"ok": False, "error": "User not found"}), 404

            profile_pic = user.profile_picture_url
            is_video = profile_pic and profile_pic.endswith('.mp4')

            return jsonify({
                "ok": True,
                "profile": {
                    "id": user.id,
                    "email": user.email,
                    "display_name": user.display_name,
                    "profile_picture_url": profile_pic,
                    "is_video": is_video,
                    "credits": user.credits,
                    "ad_free": user.ad_free
                }
            }), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500