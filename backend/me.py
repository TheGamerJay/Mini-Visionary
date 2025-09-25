from flask import Blueprint, jsonify, g
from auth import auth_required
from models import get_session, User

bp = Blueprint("me", __name__, url_prefix="/api/me")

@bp.get("")
@auth_required
def me():
    """Get current user info including ad-free status and credits"""
    with get_session() as s:
        user = s.query(User).filter_by(id=g.user_id).first()
        if not user:
            return jsonify(ok=False, error="user_not_found"), 404

        return jsonify(
            ok=True,
            email=user.email,
            display_name=user.display_name,
            ad_free=bool(user.ad_free),
            credits=user.credits or 0,
            plan=user.plan,
            created_at=user.created_at.isoformat() if user.created_at else None
        )