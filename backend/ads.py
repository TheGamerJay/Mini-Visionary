import os
import stripe
from flask import Blueprint, jsonify, g, current_app
from auth import auth_required
from models import get_session, User

bp = Blueprint("ads", __name__, url_prefix="/api/ads")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ADFREE = os.getenv("STRIPE_ADFREE_PRICE")         # e.g. price_123
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


@bp.post("/checkout")
@auth_required
def adfree_checkout():
    """Create an Ad-Free monthly subscription Checkout session."""
    if not stripe.api_key:
        return jsonify(ok=False, error="stripe_api_key_missing"), 500
    if not PRICE_ADFREE:
        return jsonify(ok=False, error="price_not_configured"), 400

    # get minimal user fields (email + stripe_customer_id) then close DB session
    with get_session() as s:
        u = s.query(User.id, User.email, User.stripe_customer_id).filter_by(id=g.user_id).first()

    if not u:
        return jsonify(ok=False, error="user_not_found"), 404

    success_url = f"{FRONTEND_ORIGIN}/settings?adfree=success&cs={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{FRONTEND_ORIGIN}/settings?adfree=cancel"

    kwargs = dict(
        mode="subscription",
        line_items=[{"price": PRICE_ADFREE, "quantity": 1}],
        client_reference_id=str(u.id),     # helps reconcile if webhook arrives first
        metadata={"app_user_id": str(u.id), "product": "ad_free"},
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=False,       # you said no promos
        # Automatic tax if you enabled it in Stripe Tax:
        # automatic_tax={"enabled": True},
    )

    # Reuse customer if we have one; otherwise let Checkout create it
    if u.stripe_customer_id:
        kwargs["customer"] = u.stripe_customer_id
    else:
        kwargs["customer_creation"] = {"enabled": True}
        if u.email:
            kwargs["customer_email"] = u.email  # helps link the new customer

    try:
        session = stripe.checkout.Session.create(**kwargs)
        return jsonify(ok=True, url=session.url), 200
    except stripe.error.StripeError as e:
        current_app.logger.exception("Stripe Checkout error")
        return jsonify(ok=False, error="stripe_error"), 502