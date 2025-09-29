from flask import Blueprint, jsonify, g

bp = Blueprint("auth_alias", __name__, url_prefix="/api/auth")

@bp.get("/whoami")
def whoami():
    """
    Get current user session state for SPA.
    Auth is optional: if no user, return null JSON.
    """
    user = getattr(g, 'user', None)
    if not user:
        return jsonify({"ok": True, "user": None}), 200

    avatar = getattr(user, "avatar_url", None)
    return jsonify({
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": getattr(user, "display_name", None),
            "avatar_image_url": avatar if avatar and not avatar.startswith('data:video/') else None,
            "avatar_video_url": avatar if avatar and avatar.startswith('data:video/') else None,
        }
    }), 200