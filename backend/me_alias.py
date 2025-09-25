from flask import Blueprint, jsonify
from app_auth import get_current_user

bp = Blueprint("auth_alias", __name__, url_prefix="/api/auth")

@bp.get("/whoami")
def whoami():
    """Get current user session state for SPA - NO AUTH REQUIRED"""
    # Use the same logic as app_auth.py whoami endpoint
    user = get_current_user()
    if not user:
        return jsonify(None), 200

    # Return only what the UI needs
    return jsonify({
        "id": user.id,
        "email": user.email,
        "display_name": getattr(user, "display_name", None),
        "avatar_url": getattr(user, "avatar_url", None),
    }), 200