from flask import Blueprint
from me import me as me_handler   # reuse existing handler
from auth import auth_required

bp = Blueprint("auth_alias", __name__, url_prefix="/api/auth")

@bp.get("/whoami")
@auth_required
def whoami():
    """Alias for /api/me to maintain compatibility with existing frontend calls"""
    # call the same function used by /api/me
    return me_handler()