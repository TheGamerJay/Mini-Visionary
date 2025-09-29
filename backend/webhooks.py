# webhooks.py
import os
import stripe
import logging
from flask import Blueprint, request, jsonify, abort
from models import get_session, User, CreditEventType
from wallet import grant_credits

# Set up logging
log = logging.getLogger("webhooks")

bp = Blueprint("webhooks", __name__, url_prefix="/api")

# --- Stripe config ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
WH_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

# Price IDs from env (Stripe Dashboard) -> map to credits
PRICE_STARTER  = (os.getenv("STORE_PRICE_STARTER")  or "").strip()  # 60 credits
PRICE_STANDARD = (os.getenv("STORE_PRICE_STANDARD") or "").strip()  # 100 credits
PRICE_STUDIO   = (os.getenv("STORE_PRICE_STUDIO")   or "").strip()  # 400 credits
PRICE_ADFREE   = (os.getenv("STORE_PRICE_ADFREE")   or "").strip()  # subscription price

CREDIT_MAP = {
    PRICE_STARTER:  60,
    PRICE_STANDARD: 100,
    PRICE_STUDIO:   400,
}

# --- Resend config ---
RESEND_WEBHOOK_SECRET = os.getenv("RESEND_WEBHOOK_SECRET", "").strip()

# ---- Simple in-memory idempotency (for prod, store in DB) ----
_PROCESSED: set[str] = set()
_MAX_IDS = 2000  # rotate to avoid unbounded growth

def _mark_processed(eid: str) -> bool:
    """True if already processed; otherwise mark and return False."""
    global _PROCESSED
    if not eid:
        return False
    if eid in _PROCESSED:
        return True
    if len(_PROCESSED) >= _MAX_IDS:
        # crude rotation
        _PROCESSED.clear()
    _PROCESSED.add(eid)
    return False

def _set_adfree_by_user_id(user_id: int, active: bool, customer_id: str | None = None):
    with get_session() as s:
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            return
        user.ad_free = bool(active)
        if customer_id:
            user.stripe_customer_id = customer_id
        s.commit()

def _set_adfree_by_customer(customer_id: str, active: bool):
    if not customer_id:
        return
    with get_session() as s:
        user = s.query(User).filter_by(stripe_customer_id=customer_id).first()
        if not user:
            return
        user.ad_free = bool(active)
        s.commit()

def _resolve_user_id_from_session(sess: dict) -> int | None:
    """
    Prefer client_reference_id; fallback to metadata.user_id (both set in your checkout step).
    """
    raw = sess.get("client_reference_id") or (sess.get("metadata") or {}).get("user_id")
    try:
        return int(raw) if raw is not None else None
    except Exception:
        return None

@bp.post("/stripe-webhook")
def stripe_webhook():
    """Stripe webhook handler: credits purchases + ad-free subscriptions."""
    if not WH_SECRET:
        # Fail fast if the webhook secret isn't set
        return jsonify(ok=False, error="webhook_secret_not_configured"), 500

    payload = request.data
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=WH_SECRET)
    except stripe.error.SignatureVerificationError as e:
        return jsonify(ok=False, error=f"signature_error: {e}"), 400
    except Exception as e:
        return jsonify(ok=False, error=f"webhook_parse_error: {e}"), 400

    # Idempotency
    ev_id = event.get("id")
    if _mark_processed(ev_id):
        return ("", 200)

    etype = event.get("type", "")
    obj = event.get("data", {}).get("object", {}) or {}

    # --- 1) Checkout session completed (one-off or subscription) ---
    if etype == "checkout.session.completed":
        mode = obj.get("mode")
        user_id = _resolve_user_id_from_session(obj)

        if mode == "subscription":
            # Activate Ad-Free on start
            if user_id is not None:
                _set_adfree_by_user_id(user_id, True, customer_id=obj.get("customer"))

                # Send subscription confirmation email
                try:
                    with get_session() as s:
                        user = s.query(User).filter_by(id=user_id).first()
                        if user and user.email:
                            from app_email import send_email
                            from app_email_templates import get_purchase_confirmation_template

                            amount_cents = obj.get("amount_total", 0)
                            amount_dollars = f"${amount_cents / 100:.2f}" if amount_cents else "$0.00"
                            product_name = "Ad-Free Premium Access"

                            email_template = get_purchase_confirmation_template(
                                user_name=user.display_name or "Valued Customer",
                                amount=amount_dollars,
                                product_name=product_name
                            )

                            send_email(
                                to=user.email,
                                subject=email_template["subject"],
                                html=email_template["html"],
                                text=email_template["text"]
                            )
                            log.info("Subscription confirmation email sent to %s for ad-free access", user.email)
                except Exception as email_error:
                    log.warning("Subscription confirmation email failed for user_id %s: %s", user_id, email_error)
                    # Continue processing even if email fails

            return ("", 200)

        if mode == "payment" and user_id is not None:
            # Need expanded line items to get price IDs reliably
            try:
                sess = stripe.checkout.Session.retrieve(
                    obj["id"],
                    expand=["line_items.data.price"]
                )
                items = (sess.get("line_items") or {}).get("data", [])
            except Exception:
                items = []

            total_credits = 0
            for li in items:
                price = (li.get("price") or {})
                price_id = price.get("id") or li.get("price")  # fallback
                qty = int(li.get("quantity") or 1)
                if price_id in CREDIT_MAP:
                    total_credits += CREDIT_MAP[price_id] * qty

            if total_credits > 0:
                grant_credits(
                    user_id=user_id,
                    amount=total_credits,
                    event=CreditEventType.PURCHASE,
                    ref=f"stripe:{obj.get('id')}",
                    notes=f"checkout purchase {total_credits} credits"
                )

                # Send purchase confirmation email
                try:
                    with get_session() as s:
                        user = s.query(User).filter_by(id=user_id).first()
                        if user and user.email:
                            from app_email import send_email
                            from app_email_templates import get_purchase_confirmation_template

                            amount_cents = obj.get("amount_total", 0)
                            amount_dollars = f"${amount_cents / 100:.2f}" if amount_cents else "$0.00"
                            product_name = f"{total_credits} Credits"

                            email_template = get_purchase_confirmation_template(
                                user_name=user.display_name or "Valued Customer",
                                amount=amount_dollars,
                                product_name=product_name
                            )

                            send_email(
                                to=user.email,
                                subject=email_template["subject"],
                                html=email_template["html"],
                                text=email_template["text"]
                            )
                            log.info("Purchase confirmation email sent to %s for %s credits", user.email, total_credits)
                except Exception as email_error:
                    log.warning("Purchase confirmation email failed for user_id %s: %s", user_id, email_error)
                    # Continue processing even if email fails

            return ("", 200)

        return ("", 200)

    # --- 2) Invoice paid (subscription renewals) ---
    # This also fires on the first invoice for some subscription flows.
    if etype == "invoice.paid":
        # If you only have one subscription type (Ad-Free), simply mark active
        customer_id = obj.get("customer")
        # Optional: you can check each line to verify it's for PRICE_ADFREE
        _set_adfree_by_customer(customer_id, True)
        return ("", 200)

    # --- 3) Subscription lifecycle updates that disable Ad-Free ---
    if etype in ("customer.subscription.deleted", "customer.subscription.updated"):
        status = obj.get("status")
        customer = obj.get("customer")
        if etype == "customer.subscription.deleted" or status in (
            "canceled", "unpaid", "incomplete_expired", "past_due"
        ):
            _set_adfree_by_customer(customer, False)
        return ("", 200)

    # --- 4) Other events: acknowledge ---
    return ("", 200)

@bp.post("/resend-webhook")
def resend_webhook():
    """Resend webhook handler: email delivery tracking."""
    if not RESEND_WEBHOOK_SECRET:
        # Skip webhook verification if secret not configured (dev mode)
        log.warning("RESEND_WEBHOOK_SECRET not configured - webhook verification disabled")
        payload = request.get_json()
        event_type = payload.get("type") if payload else "unknown"
        data = payload.get("data", {}) if payload else {}
    else:
        # Production: verify webhook signature using svix
        try:
            from svix.webhooks import Webhook, WebhookVerificationError
        except ImportError:
            log.error("svix library not installed - run: pip install svix")
            return jsonify(ok=False, error="svix_not_installed"), 500

        payload = request.data
        headers = {
            "svix-id": request.headers.get("svix-id", ""),
            "svix-timestamp": request.headers.get("svix-timestamp", ""),
            "svix-signature": request.headers.get("svix-signature", ""),
        }

        try:
            wh = Webhook(RESEND_WEBHOOK_SECRET)
            event = wh.verify(payload, headers)  # verified JSON dict
        except WebhookVerificationError as e:
            log.warning("Resend webhook signature invalid: %s", e)
            return abort(400)

        event_type = event.get("type")
        data = event.get("data", {})

    # Handle different email events
    if event_type == "email.sent":
        log.info("📨 Email sent: %s", data)
    elif event_type == "email.delivered":
        log.info("📬 Email delivered: %s", data)
    elif event_type == "email.bounced":
        log.info("❌ Email bounced: %s", data)
        # TODO: Optionally suppress bounced email addresses in your database
    elif event_type == "email.complained":
        log.info("⚠️ Email complaint: %s", data)
        # TODO: Handle spam complaints by suppressing email addresses
    elif event_type == "email.opened":
        log.info("👀 Email opened: %s", data)
        # TODO: Track email open rates in your database
    elif event_type == "email.clicked":
        log.info("🔗 Link clicked: %s", data)
        # TODO: Track email click rates in your database
    else:
        log.info("ℹ️ Unknown Resend event: %s", event_type)

    return "", 200