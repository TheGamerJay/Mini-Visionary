# app_email_templates.py
import os

# Logo URL - configure this in your environment or hardcode
LOGO_URL = os.getenv("EMAIL_LOGO_URL", "https://minivisionary.soulbridgeai.com/static/logo.png")

def get_welcome_email_template(user_name: str = "New User") -> dict:
    """Welcome email template for new signups"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Mini Visionary</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ max-width: 120px; height: auto; margin-bottom: 20px; }}
            .title {{ color: #663399; font-size: 28px; font-weight: bold; margin: 0; }}
            .subtitle {{ color: #666; font-size: 16px; margin: 10px 0; }}
            .content {{ padding: 20px 0; }}
            .button {{ display: inline-block; background: linear-gradient(90deg, #ec4899, #a855f7, #06b6d4); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{LOGO_URL}" alt="Mini Visionary Logo" class="logo">
                <h1 class="title">Welcome to Mini Visionary!</h1>
                <p class="subtitle">Your creative journey starts here</p>
            </div>

            <div class="content">
                <h2>Hello {user_name}!</h2>
                <p>Welcome to the Mini Visionary community! We're excited to have you on board.</p>

                <p>With Mini Visionary, you can:</p>
                <ul>
                    <li>Create stunning AI-generated posters and artwork</li>
                    <li>Browse our community gallery for inspiration</li>
                    <li>Share your creations with fellow artists</li>
                    <li>Access premium features and tools</li>
                </ul>

                <p>Ready to get started? Click the button below to explore your new creative playground:</p>

                <div style="text-align: center;">
                    <a href="{os.getenv('PUBLIC_APP_URL', 'http://localhost:5000')}" class="button">Start Creating</a>
                </div>
            </div>

            <div class="footer">
                <p>Thank you for joining Mini Visionary!</p>
                <p>If you have any questions, feel free to reach out to us at <a href="mailto:{os.getenv('FROM_EMAIL', 'support@minivisionary.soulbridgeai.com')}">{os.getenv('FROM_EMAIL', 'support@minivisionary.soulbridgeai.com')}</a></p>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    Mini Visionary - Where Creativity Meets AI
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Welcome to Mini Visionary, {user_name}!

    Your creative journey starts here. We're excited to have you on board.

    With Mini Visionary, you can:
    - Create stunning AI-generated posters and artwork
    - Browse our community gallery for inspiration
    - Share your creations with fellow artists
    - Access premium features and tools

    Get started at: {os.getenv('PUBLIC_APP_URL', 'http://localhost:5000')}

    Thank you for joining Mini Visionary!

    If you have any questions, contact us at {os.getenv('FROM_EMAIL', 'support@minivisionary.soulbridgeai.com')}

    Mini Visionary - Where Creativity Meets AI
    """

    return {{
        "subject": "Welcome to Mini Visionary - Let's Create Something Amazing!",
        "html": html_content,
        "text": text_content
    }}


def get_purchase_confirmation_template(user_name: str = "Valued Customer", amount: str = "$0.00", product_name: str = "Premium Access") -> dict:
    """Purchase confirmation email template for Stripe payments"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Purchase Confirmation - Mini Visionary</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ max-width: 120px; height: auto; margin-bottom: 20px; }}
            .title {{ color: #663399; font-size: 28px; font-weight: bold; margin: 0; }}
            .subtitle {{ color: #10b981; font-size: 18px; margin: 10px 0; font-weight: bold; }}
            .content {{ padding: 20px 0; }}
            .purchase-details {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .button {{ display: inline-block; background: linear-gradient(90deg, #ec4899, #a855f7, #06b6d4); color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px; }}
            .success-icon {{ font-size: 48px; color: #10b981; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{LOGO_URL}" alt="Mini Visionary Logo" class="logo">
                <div class="success-icon">✓</div>
                <h1 class="title">Purchase Confirmed!</h1>
                <p class="subtitle">Thank you for your purchase</p>
            </div>

            <div class="content">
                <h2>Hello {user_name}!</h2>
                <p>Your purchase has been successfully processed. Thank you for choosing Mini Visionary!</p>

                <div class="purchase-details">
                    <h3>Purchase Details:</h3>
                    <p><strong>Product:</strong> {product_name}</p>
                    <p><strong>Amount:</strong> {amount}</p>
                    <p><strong>Date:</strong> {{new Date().toLocaleDateString()}}</p>
                </div>

                <p>Your premium features are now active and ready to use. Enjoy creating with enhanced tools and capabilities!</p>

                <div style="text-align: center;">
                    <a href="{os.getenv('PUBLIC_APP_URL', 'http://localhost:5000')}" class="button">Access Your Premium Features</a>
                </div>
            </div>

            <div class="footer">
                <p>Thank you for supporting Mini Visionary!</p>
                <p>If you have any questions about your purchase, please contact us at <a href="mailto:{os.getenv('FROM_EMAIL', 'support@minivisionary.soulbridgeai.com')}">{os.getenv('FROM_EMAIL', 'support@minivisionary.soulbridgeai.com')}</a></p>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    Mini Visionary - Where Creativity Meets AI
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Purchase Confirmed - Mini Visionary

    Hello {user_name}!

    Your purchase has been successfully processed. Thank you for choosing Mini Visionary!

    Purchase Details:
    - Product: {product_name}
    - Amount: {amount}
    - Date: {{new Date().toLocaleDateString()}}

    Your premium features are now active and ready to use.

    Access your premium features at: {os.getenv('PUBLIC_APP_URL', 'http://localhost:5000')}

    Thank you for supporting Mini Visionary!

    If you have any questions, contact us at {os.getenv('FROM_EMAIL', 'support@minivisionary.soulbridgeai.com')}

    Mini Visionary - Where Creativity Meets AI
    """

    return {{
        "subject": f"Purchase Confirmed - {product_name} - Mini Visionary",
        "html": html_content,
        "text": text_content
    }}