import os
import stripe
from flask import Blueprint, jsonify, g, current_app
from auth import auth_required
from models import get_session, User  # <- to read/update stripe_customer_id

bp = Blueprint("ads", __name__, url_prefix="/api/ads")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ADFREE = os.getenv("STRIPE_ADFREE_PRICE")  # price_XXX from Stripe
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


@bp.post("/checkout")
@auth_required
def adfree_checkout():
    """Create Ad-Free subscription Checkout session."""
    if not stripe.api_key:
        return jsonify(ok=False, error="stripe_api_key_missing"), 500
    if not PRICE_ADFREE:
        return jsonify(ok=False, error="price_not_configured"), 500

    # Fetch minimal user fields, close session immediately
    with get_session() as s:
        u = s.query(User.id, User.email, User.stripe_customer_id).filter_by(id=g.user_id).first()

    if not u:
        return jsonify(ok=False, error="user_not_found"), 404

    try:
        customer_id = u.stripe_customer_id

        # Create a Stripe customer if we don't have one yet
        if not customer_id:
            cust = stripe.Customer.create(email=u.email, metadata={"user_id": str(u.id)})
            customer_id = cust.id
            # persist on our side
            with get_session() as s:
                s.query(User).filter_by(id=u.id).update({"stripe_customer_id": customer_id})
                s.commit()

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": PRICE_ADFREE, "quantity": 1}],
            client_reference_id=str(u.id),
            metadata={"user_id": str(u.id), "product": "ad_free_subscription"},
            success_url=f"{FRONTEND_ORIGIN}/settings?adfree=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_ORIGIN}/settings?adfree=cancel",
            allow_promotion_codes=False,
            billing_address_collection="auto",
            customer_update={"address": "auto", "name": "auto"},
            automatic_tax={"enabled": True},
        )

        return jsonify(ok=True, url=session.url), 200

    except stripe.error.StripeError as e:
        current_app.logger.exception("Stripe Checkout error")
        return jsonify(ok=False, error="stripe_error"), 502