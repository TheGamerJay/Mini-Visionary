import os
import stripe
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound
from auth import auth_required
from models import get_session, User
from mailer import send_email

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

# ---- PRODUCT CATALOG (final) ----
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
}
CURRENCY = "usd"

@payments_bp.get("/products")
def products():
    """Get available credit packages"""
    items = []
    for sku, p in PRODUCTS.items():
        items.append({
            "sku": sku,
            "name": p["name"],
            "desc": p["desc"],
            "credits": p["credits"],
            "price": p["amount_cents"] / 100.0,
            "currency": CURRENCY,
        })
    return jsonify(ok=True, items=items, publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY"))

@payments_bp.post("/checkout")
@auth_required
def checkout():
    """Create Stripe checkout session"""
    data = request.get_json() or {}
    sku = (data.get("sku") or "").lower().strip()
    success_url = data.get("success_url") or f"{os.getenv('FRONTEND_ORIGIN')}/checkout/success"
    cancel_url = data.get("cancel_url") or f"{os.getenv('FRONTEND_ORIGIN')}/checkout/cancel"

    if sku not in PRODUCTS:
        raise BadRequest("invalid_sku")
    product = PRODUCTS[sku]
    if not product["stripe_price"]:
        raise BadRequest("price_not_configured")

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

# Webhook handling moved to webhooks.py for better organization

@payments_bp.get("/session/<session_id>")
@auth_required
def get_session_status(session_id):
    """Get payment session status"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)

        return jsonify(ok=True,
                      status=session.payment_status,
                      customer_email=session.customer_details.get('email') if session.customer_details else None)
    except stripe.error.StripeError as e:
        return jsonify(ok=False, error=str(e)), 500

@payments_bp.get("/wallet")
@auth_required
def wallet():
    """Get wallet/credits info for authenticated user"""
    with get_session() as s:
        # Get user's current credits
        user = s.query(User).filter_by(id=g.user_id).first()
        credits = user.credits if user else 0

        # Get recent purchase receipts
        receipts_query = s.query(CreditLedger).filter_by(
            user_id=g.user_id,
            event=CreditEventType.PURCHASE
        ).order_by(CreditLedger.created_at.desc()).limit(10)

        receipts = []
        for receipt in receipts_query:
            # Extract SKU from Stripe reference
            sku = "unknown"
            if receipt.ref and "stripe:" in receipt.ref:
                # Try to find the SKU from the notes
                for product_sku, product in PRODUCTS.items():
                    if product["name"] in receipt.notes:
                        sku = product_sku
                        break

            receipts.append({
                "id": receipt.id,
                "sku": sku,
                "amount": PRODUCTS.get(sku, {}).get("amount_cents", 0) / 100.0,
                "currency": CURRENCY,
                "provider_id": receipt.ref.replace("stripe:", "") if receipt.ref else "",
                "created_at": receipt.created_at.isoformat(),
                "notes": receipt.notes
            })

    wallet_data = {"credits": credits, "updated_at": user.updated_at.isoformat() if user and user.updated_at else None}
    return jsonify(ok=True, wallet=wallet_data, receipts=receipts)

@payments_bp.get("/receipt/<int:receipt_id>")
@auth_required
def get_receipt(receipt_id):
    """Get printable receipt HTML for a specific purchase"""
    with get_session() as s:
        # Get the receipt record
        receipt = s.query(CreditLedger).filter_by(
            id=receipt_id,
            user_id=g.user_id,
            event=CreditEventType.PURCHASE
        ).first()

        if not receipt:
            raise NotFound("Receipt not found")

        user = s.query(User).filter_by(id=g.user_id).first()

        # Extract SKU from notes
        sku = "unknown"
        for product_sku, product in PRODUCTS.items():
            if product["name"] in receipt.notes:
                sku = product_sku
                break

        product_info = PRODUCTS.get(sku, {
            "name": "Unknown Pack",
            "desc": "Poster credits",
            "credits": receipt.amount,
            "amount_cents": 0
        })

        # Generate receipt HTML
        receipt_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Receipt #{receipt.id} - Mini Dream Poster</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #000; color: #fff; }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0891b2; padding-bottom: 20px; }}
        .logo {{ color: #06b6d4; font-size: 24px; font-weight: bold; margin-bottom: 8px; }}
        .company {{ color: #a5b4fc; font-size: 14px; }}
        .receipt-info {{ display: flex; justify-content: space-between; margin: 20px 0; }}
        .receipt-info div {{ color: #a5b4fc; }}
        .receipt-info strong {{ color: #fff; display: block; }}
        .items {{ border: 1px solid #374151; border-radius: 8px; margin: 20px 0; }}
        .item-header {{ background: #1e293b; padding: 12px; border-bottom: 1px solid #374151; font-weight: bold; }}
        .item {{ padding: 12px; border-bottom: 1px solid #374151; }}
        .item:last-child {{ border-bottom: none; }}
        .item-name {{ font-weight: 600; color: #06b6d4; }}
        .item-desc {{ color: #a5b4fc; font-size: 14px; margin: 4px 0; }}
        .item-price {{ float: right; font-weight: bold; }}
        .total {{ text-align: right; margin: 20px 0; font-size: 18px; }}
        .total-label {{ color: #a5b4fc; }}
        .total-amount {{ font-weight: bold; color: #06b6d4; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #374151; text-align: center; color: #6b7280; font-size: 12px; }}
        @media print {{ body {{ background: white; color: black; }} .header {{ border-bottom-color: #0891b2; }} .logo {{ color: #0891b2; }} .company, .receipt-info div, .item-desc {{ color: #666; }} .items {{ border-color: #ddd; }} .item-header {{ background: #f8f9fa; border-bottom-color: #ddd; }} .item {{ border-bottom-color: #ddd; }} .item-name, .total-amount {{ color: #0891b2; }} .footer {{ border-top-color: #ddd; color: #666; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Mini Dream Poster</div>
        <div class="company">AI-Powered Poster Generation</div>
    </div>

    <div class="receipt-info">
        <div>
            <strong>Receipt #{receipt.id}</strong>
            Date: {receipt.created_at.strftime('%B %d, %Y at %I:%M %p')}
        </div>
        <div>
            <strong>Customer</strong>
            {user.email if user else 'N/A'}
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
        <p>Transaction ID: {receipt.ref.replace('stripe:', '') if receipt.ref else 'N/A'}</p>
        <p>Questions? Contact us at support@minidreamposter.com</p>
    </div>
</body>
</html>
        """

        return receipt_html, 200, {'Content-Type': 'text/html'}

@payments_bp.post("/email-receipt")
@auth_required
def email_receipt():
    """Email a receipt to the user"""
    data = request.get_json() or {}
    receipt_id = data.get("receipt_id")

    if not receipt_id:
        raise BadRequest("receipt_id is required")

    with get_session() as s:
        # Get the receipt record
        receipt = s.query(CreditLedger).filter_by(
            id=receipt_id,
            user_id=g.user_id,
            event=CreditEventType.PURCHASE
        ).first()

        if not receipt:
            raise NotFound("Receipt not found")

        user = s.query(User).filter_by(id=g.user_id).first()
        if not user:
            raise NotFound("User not found")

        # Extract SKU from notes
        sku = "unknown"
        for product_sku, product in PRODUCTS.items():
            if product["name"] in receipt.notes:
                sku = product_sku
                break

        product_info = PRODUCTS.get(sku, {
            "name": "Unknown Pack",
            "desc": "Poster credits",
            "credits": receipt.amount,
            "amount_cents": 0
        })

        # Create email-friendly receipt HTML
        receipt_html = f"""
<div style="font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0891b2; padding-bottom: 20px;">
        <div style="color: #0891b2; font-size: 24px; font-weight: bold; margin-bottom: 8px;">Mini Dream Poster</div>
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
        <p>Transaction ID: {receipt.ref.replace('stripe:', '') if receipt.ref else 'N/A'}</p>
        <p>Questions? Contact us at support@minidreamposter.com</p>
    </div>
</div>
        """

        try:
            send_email(
                to=user.email,
                subject=f"Receipt #{receipt.id} - Mini Dream Poster",
                html=receipt_html,
                tags={"event": "receipt_email"}
            )
            return jsonify(ok=True, message="Receipt emailed successfully")
        except Exception as e:
            return jsonify(ok=False, error=f"Failed to send email: {str(e)}"), 500