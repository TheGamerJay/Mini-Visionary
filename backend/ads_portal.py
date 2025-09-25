import os
import stripe
from flask import Blueprint, jsonify, g
from auth import auth_required
from models import get_session, User

bp = Blueprint("ads_portal", __name__, url_prefix="/api/ads")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

@bp.post("/portal")
@auth_required
def create_portal():
    """Create Stripe Customer Portal session for subscription management"""
    with get_session() as s:
        user = s.query(User).filter_by(id=g.user_id).first()
        if not user or not user.stripe_customer_id:
            return jsonify(ok=False, error="no_customer"), 400

    return_url = f"{FRONTEND_ORIGIN}/settings"
    try:
        sess = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url
        )
        return jsonify(ok=True, url=sess.url)
    except stripe.error.StripeError as e:
        return jsonify(ok=False, error=str(e)), 500