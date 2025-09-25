import os, json, stripe
from flask import Blueprint, request, jsonify
from models import get_session, User

bp = Blueprint("webhooks", __name__, url_prefix="/api")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WH_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

PRICE_STARTER  = os.getenv("STORE_PRICE_STARTER")   # 60 credits
PRICE_STANDARD = os.getenv("STORE_PRICE_STANDARD")  # 100 credits
PRICE_STUDIO   = os.getenv("STORE_PRICE_STUDIO")    # 400 credits
PRICE_ADFREE   = os.getenv("STORE_PRICE_ADFREE")    # subscription

CREDIT_MAP = {
    PRICE_STARTER: 60,
    PRICE_STANDARD: 100,
    PRICE_STUDIO: 400,
}

# Simple in-memory set for event idempotency (in production, use database)
_processed_events = set()

def _already_processed(event_id: str) -> bool:
    """Check if event has already been processed (idempotency)"""
    if event_id in _processed_events:
        return True
    _processed_events.add(event_id)
    return False

def _add_credits(user_id: int, amount: int):
    """Add credits to user's balance"""
    with get_session() as s:
        user = s.query(User).filter_by(id=user_id).first()
        if user:
            user.credits = (user.credits or 0) + amount
            s.commit()

def _set_adfree(user_id: int, flag: bool, customer_id: str = None):
    """Set user's ad_free status and optionally save customer_id"""
    with get_session() as s:
        user = s.query(User).filter_by(id=user_id).first()
        if user:
            user.ad_free = flag
            if customer_id:
                user.stripe_customer_id = customer_id
            s.commit()

@bp.post("/stripe-webhook")
def stripe_webhook():
    """Complete Stripe webhook handler for credits and ad-free subscriptions"""
    payload = request.data
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=WH_SECRET)
    except Exception as e:
        return jsonify(ok=False, error=f"signature_error: {e}"), 400

    # Idempotency check
    ev_id = event.get("id")
    if not ev_id or _already_processed(ev_id):
        return ("", 200)

    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    # 1) Checkout completed (one-off OR subscription)
    if event_type == "checkout.session.completed":
        mode = obj.get("mode")
        user_id = obj.get("client_reference_id")
        try:
            user_id = int(user_id)
        except Exception:
            user_id = None

        if mode == "subscription":
            # Ad-Free monthly subscription
            if user_id is not None:
                customer_id = obj.get("customer")
                _set_adfree(user_id, True, customer_id)
                print(f"✅ Activated Ad-Free subscription for user {user_id}")
            return ("", 200)

        # One-off credit purchase
        if mode == "payment" and user_id is not None:
            # Get line items to determine which credit pack was purchased
            line_items = obj.get("line_items")
            if not line_items:
                try:
                    sess = stripe.checkout.Session.retrieve(obj["id"], expand=["line_items.data.price"])
                    line_items = sess.get("line_items", {}).get("data", [])
                except Exception:
                    line_items = []

            total_credits = 0
            for li in line_items or []:
                price_obj = li.get("price")
                if isinstance(price_obj, dict):
                    price_id = price_obj.get("id")
                else:
                    price_id = price_obj

                qty = int(li.get("quantity") or 1)
                if price_id in CREDIT_MAP:
                    total_credits += CREDIT_MAP[price_id] * qty

            if total_credits > 0:
                _add_credits(user_id, total_credits)
                print(f"✅ Added {total_credits} credits to user {user_id}")
        return ("", 200)

    # 2) Subscription canceled/inactive → remove ad_free
    if event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        status = obj.get("status")
        customer = obj.get("customer")

        # Find user by customer ID and update ad_free status
        with get_session() as s:
            user = s.query(User).filter_by(stripe_customer_id=customer).first()
            if user:
                if event_type == "customer.subscription.deleted" or status in ("canceled", "unpaid", "incomplete_expired", "past_due"):
                    user.ad_free = False
                    s.commit()
                    print(f"✅ Deactivated Ad-Free subscription for user {user.id}")
        return ("", 200)

    # 3) Other events - no action needed
    return ("", 200)