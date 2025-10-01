from flask import Blueprint, request, jsonify, g
from auth import auth_required
from models import get_session, User

bp = Blueprint("gallery", __name__, url_prefix="/api/gallery")

@bp.post("/post")
@auth_required
def post_to_gallery():
    """
    Deduct 3 credits when user posts to gallery.
    """
    user_id = g.user_id

    with get_session() as s:
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"ok": False, "error": "User not found"}), 404

        if user.credits < 3:
            return jsonify({"ok": False, "error": "Insufficient credits"}), 400

        # Deduct 3 credits
        user.credits -= 3
        s.commit()

        return jsonify({
            "ok": True,
            "credits": user.credits
        }), 200
