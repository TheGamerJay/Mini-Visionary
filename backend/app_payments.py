# payments.py
import os
import stripe
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound
from auth import auth_required
from models import get_session, User, CreditLedger, CreditEventType
from mailer import send_email

# Stripe init (use STRIPE_SECRET_KEY or fall back to SECRET_KEY for backward compatibility)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("SECRET_KEY")
FRONTEND_ORIGIN = (os.getenv("FRONTEND_ORIGIN") or "").rstrip("/")
CURRENCY = "usd"

# Debug: Log Stripe configuration status (remove in production)
import logging
logging.info(f"Stripe API Key configured: {bool(stripe.api_key)}")
logging.info(f"Price IDs configured - Starter: {bool(os.getenv('STORE_PRICE_STARTER'))}, Standard: {bool(os.getenv('STORE_PRICE_STANDARD'))}, Studio: {bool(os.getenv('STORE_PRICE_STUDIO'))}")

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

# ---- PRODUCT CATALOG (server authority) ----
PRODUCTS = {
    "starter": {
        "name": "Starter Pack",
        "desc": "60 poster credits (6 posters)",
        "credits": 60,
        "amount_cents": 900,  # $9
        "stripe_price": os.getenv("STORE_PRICE_STARTER"),
    },
    "standard": {
        "name": "Standard Pack",
        "desc": "100 poster credits (10 posters)",
        "credits": 100,
        "amount_cents": 1500,  # $15
        "stripe_price": os.getenv("STORE_PRICE_STANDARD"),
    },
    "studio": {
        "name": "Studio Pack",
        "desc": "400 poster credits (40 posters)",
        "credits": 400,
        "amount_cents": 4900,  # $49
        "stripe_price": os.getenv("STORE_PRICE_STUDIO"),
    },
    "adfree": {
        "name": "Ad-Free Subscription",
        "desc": "Monthly subscription - No ads or promos",
        "credits": 0,  # Subscriptions don't grant credits
        "amount_cents": 499,  # $4.99/month
        "stripe_price": os.getenv("STORE_PRICE_ADFREE"),
    },
}

@payments_bp.get("/products")
def products():
    """List purchasable credit packs (no price IDs leaked)."""
    items = [{
        "sku": sku,
        "name": p["name"],
        "desc": p["desc"],
        "credits": p["credits"],
        "price": p["amount_cents"] / 100.0,
        "currency": CURRENCY,
    } for sku, p in PRODUCTS.items()]
    return jsonify(ok=True, items=items, publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"))

@payments_bp.get("/debug/config")
def debug_config():
    """Debug endpoint to check Stripe configuration (REMOVE IN PRODUCTION)"""
    return jsonify({
        "stripe_api_key_set": bool(stripe.api_key),
        "stripe_api_key_length": len(stripe.api_key) if stripe.api_key else 0,
        "price_starter_set": bool(os.getenv("STORE_PRICE_STARTER")),
        "price_standard_set": bool(os.getenv("STORE_PRICE_STANDARD")),
        "price_studio_set": bool(os.getenv("STORE_PRICE_STUDIO")),
        "price_adfree_set": bool(os.getenv("STORE_PRICE_ADFREE")),
        "products": {k: {"name": v["name"], "price_set": bool(v.get("stripe_price"))} for k, v in PRODUCTS.items()}
    })

@payments_bp.post("/checkout")
@auth_required
def checkout():
    """Create a Stripe Checkout Session for a single SKU."""
    data = request.get_json() or {}
    sku = (data.get("sku") or "").lower().strip()

    if sku not in PRODUCTS:
        return jsonify(ok=False, error="invalid_sku"), 400

    product = PRODUCTS[sku]

    # Check if Stripe is configured
    if not stripe.api_key or not product.get("stripe_price"):
        return jsonify(
            ok=False,
            error="Stripe not configured. Please set STRIPE_SECRET_KEY and price IDs in environment variables."
        ), 503

    # success/cancel fallbacks (must be absolute URLs)
    success_url = data.get("success_url") or f"{FRONTEND_ORIGIN}/checkout/success"
    cancel_url  = data.get("cancel_url")  or f"{FRONTEND_ORIGIN}/checkout/cancel"

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": product["stripe_price"], "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(g.user_id),
            metadata={"sku": sku, "user_id": str(g.user_id)},
        )
        return jsonify(ok=True, url=session.url)
    except stripe.error.StripeError as e:
        return jsonify(ok=False, error=str(e)), 500
    except Exception as e:
        return jsonify(ok=False, error=f"Checkout failed: {str(e)}"), 500

@payments_bp.get("/session/<session_id>")
@auth_required
def get_session_status(session_id: str):
    """Verify a Checkout Session belongs to this user, then return status."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if (session.client_reference_id or "") != str(g.user_id):
            # Don’t leak existence; just 404
            raise NotFound("Session not found")
        customer_email = None
        if getattr(session, "customer_details", None):
            customer_email = session.customer_details.get("email")
        return jsonify(ok=True, status=session.payment_status, customer_email=customer_email)
    except NotFound:
        raise
    except stripe.error.StripeError as e:
        return jsonify(ok=False, error=str(e)), 500

@payments_bp.get("/wallet")
@auth_required
def wallet():
    """Return current credits and last 10 purchase receipts."""
    with get_session() as s:
        user = s.query(User).filter_by(id=g.user_id).first()
        credits = user.credits if user else 0

        receipts_q = (s.query(CreditLedger)
                        .filter_by(user_id=g.user_id, event=CreditEventType.PURCHASE)
                        .order_by(CreditLedger.created_at.desc())
                        .limit(10))

        receipts = []
        for r in receipts_q:
            notes = r.notes or ""
            # Try to infer SKU from notes (fallback to 'unknown')
            sku = next((psku for psku, prod in PRODUCTS.items() if prod["name"] in notes), "unknown")
            receipts.append({
                "id": r.id,
                "sku": sku,
                "amount": PRODUCTS.get(sku, {}).get("amount_cents", 0) / 100.0,
                "currency": CURRENCY,
                "provider_id": (r.ref or "").replace("stripe:", ""),
                "created_at": r.created_at.isoformat(),
                "notes": notes,
            })

        wallet_data = {
        "credits": credits,
            "updated_at": user.updated_at.isoformat() if user and user.updated_at else None
        }
        return jsonify(ok=True, wallet=wallet_data, receipts=receipts)

@payments_bp.get("/receipt/<int:receipt_id>")
@auth_required
def get_receipt(receipt_id: int):
    """Return a printable HTML receipt for a purchase."""
    with get_session() as s:
        receipt = (s.query(CreditLedger)
                     .filter_by(id=receipt_id, user_id=g.user_id, event=CreditEventType.PURCHASE)
                     .first())
        if not receipt:
            raise NotFound("Receipt not found")

        user = s.query(User).filter_by(id=g.user_id).first()
        notes = receipt.notes or ""

        sku = next((psku for psku, prod in PRODUCTS.items() if prod["name"] in notes), "unknown")
        product_info = PRODUCTS.get(sku, {
        "name": "Unknown Pack",
            "desc": "Poster credits",
            "credits": receipt.amount,
            "amount_cents": 0
        })

        receipt_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Receipt #{receipt.id} - Mini-Visionary</title>
<style>
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
    background: black;
    color: white;
  }}

  .header {{
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 2px solid #0891b2;
    padding-bottom: 20px;
  }}

  .logo {{
    color: #06b6d4;
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 8px;
  }}

  .company {{
color: #a5b4fc;
    font-size: 14px;
  }}

  .receipt-info {{
display: flex;
    justify-content: space-between;
    margin: 20px 0;
  }}

  .receipt-info div {{
color: #a5b4fc;
  }}

  .receipt-info strong {{
color: #fff;
    display: block;
  }}

  .items {{
border: 1px solid #374151;
    border-radius: 8px;
    margin: 20px 0;
  }}

  .item-header {{
background: #1e293b;
    padding: 12px;
    border-bottom: 1px solid #374151;
    font-weight: bold;
  }}

  .item {{
padding: 12px;
    border-bottom: 1px solid #374151;
  }}

  .item:last-child {{
border-bottom: none;
  }}

  .item-name {{
font-weight: 600;
    color: #06b6d4;
  }}

  .item-desc {{
color: #a5b4fc;
    font-size: 14px;
    margin: 4px 0;
  }}

  .item-price {{
float: right;
    font-weight: bold;
  }}

  .total {{
text-align: right;
    margin: 20px 0;
    font-size: 18px;
  }}

  .total-label {{
color: #a5b4fc;
  }}

  .total-amount {{
font-weight: bold;
    color: #06b6d4;
  }}

  .footer {{
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #374151;
    text-align: center;
    color: #6b7280;
    font-size: 12px;
  }}

  @media print {{
    body {{ background: white; color: black; }}
    .header {{ border-bottom-color: #0891b2; }}
    .logo {{ color: #0891b2; }}
    .company, .receipt-info div, .item-desc {{ color: #666; }}
    .items {{ border-color: #ddd; }}
    .item-header {{ background: #f8f9fa; border-bottom-color: #ddd; }}
    .item {{ border-bottom-color: #ddd; }}
    .item-name, .total-amount {{ color: #0891b2; }}
    .footer {{ border-top-color: #ddd; color: #666; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="logo">Mini-Visionary</div>
    <div class="company">AI-Powered Poster Generation</div>
  </div>

  <div class="receipt-info">
    <div>
      <strong>Receipt #{receipt.id}</strong>
      Date: {receipt.created_at.strftime('%B %d, %Y at %I:%M %p')}
    </div>
    <div>
      <strong>Customer</strong>
      {(user.email if user else 'N/A')}
    </div>
  </div>

  <div class="items">
    <div class="item-header">Purchase Details</div>
    <div class="item">
      <div class="item-name">{product_info['name']}</div>
      <div class="item-desc">{product_info['desc']}</div>
      <div class="item-price">${product_info['amount_cents'] / 100:.2f}</div>
    </div>
  </div>

  <div class="total">
    <span class="total-label">Total Paid: </span>
    <span class="total-amount">${product_info['amount_cents'] / 100:.2f} USD</span>
  </div>

  <div class="total">
    <span class="total-label">Credits Added: </span>
    <span class="total-amount">{receipt.amount} poster credits</span>
  </div>

  <div class="footer">
    <p>Thank you for your purchase!</p>
    <p>Transaction ID: {(receipt.ref or '').replace('stripe:', '') or 'N/A'}</p>
    <p>Questions? Contact us at support@minivisionary.com</p>
  </div>
</body>
</html>"""
        return receipt_html, 200, {'Content-Type': 'text/html'}

@payments_bp.post("/email-receipt")
@auth_required
def email_receipt():
    """Email a receipt to the user."""
    data = request.get_json() or {}
    receipt_id = data.get("receipt_id")
    if not receipt_id:
        raise BadRequest("receipt_id is required")

    with get_session() as s:
        receipt = (s.query(CreditLedger)
                     .filter_by(id=receipt_id, user_id=g.user_id, event=CreditEventType.PURCHASE)
                     .first())
        if not receipt:
            raise NotFound("Receipt not found")

        user = s.query(User).filter_by(id=g.user_id).first()
        if not user:
            raise NotFound("User not found")

        notes = receipt.notes or ""
        sku = next((psku for psku, prod in PRODUCTS.items() if prod["name"] in notes), "unknown")
        product_info = PRODUCTS.get(sku, {
        "name": "Unknown Pack",
            "desc": "Poster credits",
            "credits": receipt.amount,
            "amount_cents": 0
        })

        # Email-friendly receipt HTML (light background)
        receipt_html = f"""
<div style="font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
  <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0891b2; padding-bottom: 20px;">
    <div style="color: #0891b2; font-size: 24px; font-weight: bold; margin-bottom: 8px;">Mini-Visionary</div>
    <div style="color: #666; font-size: 14px;">AI-Powered Poster Generation</div>
  </div>

  <div style="display: flex; justify-content: space-between; margin: 20px 0; flex-wrap: wrap;">
    <div style="color: #666; margin-bottom: 10px;">
      <strong style="color: #333; display: block;">Receipt #{receipt.id}</strong>
      Date: {receipt.created_at.strftime('%B %d, %Y at %I:%M %p')}
    </div>
    <div style="color: #666; margin-bottom: 10px;">
      <strong style="color: #333; display: block;">Customer</strong>
      {user.email}
    </div>
  </div>

  <div style="border: 1px solid #ddd; border-radius: 8px; margin: 20px 0; background: white;">
    <div style="background: #f8f9fa; padding: 12px; border-bottom: 1px solid #ddd; font-weight: bold;">Purchase Details</div>
    <div style="padding: 12px;">
      <div style="font-weight: 600; color: #0891b2;">{product_info['name']}</div>
      <div style="color: #666; font-size: 14px; margin: 4px 0;">{product_info['desc']}</div>
      <div style="float: right; font-weight: bold;">${product_info['amount_cents'] / 100:.2f}</div>
      <div style="clear: both;"></div>
    </div>
  </div>

  <div style="text-align: right; margin: 20px 0; font-size: 18px;">
    <span style="color: #666;">Total Paid: </span>
    <span style="font-weight: bold; color: #0891b2;">${product_info['amount_cents'] / 100:.2f} USD</span>
  </div>

  <div style="text-align: right; margin: 20px 0; font-size: 18px;">
    <span style="color: #666;">Credits Added: </span>
    <span style="font-weight: bold; color: #0891b2;">{receipt.amount} poster credits</span>
  </div>

  <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
    <p>Thank you for your purchase!</p>
    <p>Transaction ID: {(receipt.ref or '').replace('stripe:', '') or 'N/A'}</p>
    <p>Questions? Contact us at support@minivisionary.com</p>
  </div>
</div>
        """

        try:
            send_email(
                to=user.email,
                subject=f"Receipt #{receipt.id} - Mini-Visionary",
                html=receipt_html,
                tags={"event": "receipt_email"}
            )
            return jsonify(ok=True, message="Receipt emailed successfully")
        except Exception as e:
            return jsonify(ok=False, error=f"Failed to send email: {str(e)}"), 500