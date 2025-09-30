import os
from flask import Blueprint, jsonify, g
from auth import auth_required

bp = Blueprint("me", __name__, url_prefix="/api/me")

@bp.get("")
@auth_required
def me():
    """Get current user info including ad-free status and credits"""
    user = g.user
    if not user:
        return jsonify(ok=False, error="user_not_found"), 404

    avatar = getattr(user, 'avatar_url', None)
    profile_picture = getattr(user, 'profile_picture_url', None)

    payload = {
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": avatar,
            "avatar_image_url": avatar if avatar and not avatar.startswith('data:video/') else None,
            "avatar_video_url": avatar if avatar and avatar.startswith('data:video/') else None,
            "profile_picture_url": profile_picture,
            "ad_free": bool(user.ad_free),
            "credits": user.credits or 0,
            "plan": user.plan,
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        "release": os.getenv("GIT_SHA", "dev-local")
    }

    resp = jsonify(payload)
    resp.headers["X-Release"] = payload["release"]
    return resp