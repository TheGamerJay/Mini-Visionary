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

    return jsonify(
        ok=True,
        user={
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_image_url": getattr(user, 'avatar_image_url', None),
            "avatar_video_url": getattr(user, 'avatar_video_url', None),
            "ad_free": bool(user.ad_free),
            "credits": user.credits or 0,
            "plan": user.plan,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    )