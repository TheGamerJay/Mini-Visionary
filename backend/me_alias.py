from flask import Blueprint, jsonify, g
from auth import auth_required

bp = Blueprint("auth_alias", __name__, url_prefix="/api/auth")

@bp.get("/whoami")
@auth_required
def whoami():
    """
    Get current user session state for SPA.
    Requires authentication.
    """
    user = g.user
    avatar = getattr(user, "avatar_url", None)
    return jsonify({
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": getattr(user, "display_name", None),
            "credits": getattr(user, "credits", 0),
            "avatar_image_url": avatar if avatar and not avatar.startswith('data:video/') else None,
            "avatar_video_url": avatar if avatar and avatar.startswith('data:video/') else None,
        }
    }), 200