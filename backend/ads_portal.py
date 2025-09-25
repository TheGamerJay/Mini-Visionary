import os
import stripe
from flask import Blueprint, jsonify, g, current_app
from auth import auth_required
from models import get_session, User

bp = Blueprint("ads_portal", __name__, url_prefix="/api/ads")

# Set once at import
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


@bp.post("/portal")
@auth_required
def create_portal():
    """Create a Stripe Billing Portal session for subscription management."""
    if not stripe.api_key:
        return jsonify(ok=False, error="stripe_api_key_missing"), 500

    # fetch only the field we need, then close the session
    with get_session() as s:
        u = s.query(User.id, User.stripe_customer_id).filter_by(id=g.user_id).first()

    if not u:
        return jsonify(ok=False, error="user_not_found"), 404
    if not u.stripe_customer_id:
        return jsonify(ok=False, error="no_customer"), 400

    return_url = f"{FRONTEND_ORIGIN}/settings"

    try:
        sess = stripe.billing_portal.Session.create(
            customer=u.stripe_customer_id,
            return_url=return_url,
        )
        return jsonify(ok=True, url=sess.url), 200
    except stripe.error.StripeError as e:
        current_app.logger.exception("Stripe portal session error")
        # Keep the message generic for clients
        return jsonify(ok=False, error="stripe_error"), 502