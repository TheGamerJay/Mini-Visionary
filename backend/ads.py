import os
import stripe
from flask import Blueprint, jsonify, g
from auth import auth_required

bp = Blueprint("ads", __name__, url_prefix="/api/ads")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ADFREE = os.getenv("STRIPE_ADFREE_PRICE")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

@bp.post("/checkout")
@auth_required
def adfree_checkout():
    """Create Ad-Free subscription checkout session"""
    if not PRICE_ADFREE:
        return jsonify(ok=False, error="price_not_configured"), 400

    try:
        sess = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": PRICE_ADFREE, "quantity": 1}],
            client_reference_id=str(g.user_id),
            success_url=f"{FRONTEND_ORIGIN}/settings?adfree=success",
            cancel_url=f"{FRONTEND_ORIGIN}/settings?adfree=cancel",
        )
        return jsonify(ok=True, url=sess.url)
    except stripe.error.StripeError as e:
        return jsonify(ok=False, error=str(e)), 500