# app_legal.py
from __future__ import annotations
import os
from flask import Blueprint, jsonify, make_response

legal_bp = Blueprint("legal", __name__, url_prefix="/api/legal")

BRAND = os.getenv("BRAND_NAME", "Mini-Visionary")
SUPPORT = os.getenv("SUPPORT_EMAIL", "support@minivisionary.com")
LAST_UPDATED = os.getenv("LEGAL_LAST_UPDATED", "January 2025")

def _json(payload: dict):
    resp = make_response(jsonify(payload))
    # cache legal docs for a day; bump LAST_UPDATED to refresh
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp

@legal_bp.get("/terms")
def terms():
    return _json({
        "title": f"Terms of Service - {BRAND}",
        "lastUpdated": LAST_UPDATED,
        "sections": [
            {
                "title": "1. Acceptance of Terms",
                "content": f"By using {BRAND} (\"Service\"), you agree to these Terms of Service (\"Terms\"). If you don't agree, do not use the Service."
            },
            {
                "title": "2. Service Description",
                "content": f"{BRAND} is an AI-powered creation platform that can generate posters and other creative content from text prompts and/or uploaded images using a credits-based system."
            },
            {
                "title": "3. User Accounts",
                "content": "You must provide accurate information when creating an account. You are responsible for maintaining account security and all activity under your account."
            },
            {
                "title": "4. Credits and Payments",
                "content": "• Each poster generation costs 10 credits\n• Credits are non-refundable except for failed generations we can verify\n• Prices may change with notice\n• Failed generations are automatically refunded when detected"
            },
            {
                "title": "5. Content Policy",
                "content": "You may not generate content that is illegal, harmful, infringing, or violates others' rights. Adult content involving minors is strictly prohibited."
            },
            {
                "title": "6. Intellectual Property",
                "content": "• You retain rights to your input content\n• Generated outputs are yours to use, subject to applicable law and third-party rights\n• The Service, models, and code remain our property\n• Do not reverse-engineer or abuse the Service"
            },
            {
                "title": "7. Limitation of Liability",
                "content": "The Service is provided \"as is\" without warranties of any kind. To the maximum extent permitted by law, we are not liable for indirect, incidental, or consequential damages. Our aggregate liability is limited to amounts you paid for the Service in the 3 months prior to the claim."
            },
            {
                "title": "8. Termination",
                "content": "We may suspend or terminate accounts for violations. You may delete your account at any time; some records may be retained as required by law."
            },
            {
                "title": "9. Changes",
                "content": "We may update these Terms. Continued use after changes constitutes acceptance."
            },
            {
                "title": "10. Contact",
                "content": f"Questions? Contact us at {SUPPORT}"
            }
        ]
    })

@legal_bp.get("/privacy")
def privacy():
    return _json({
        "title": f"Privacy Policy - {BRAND}",
        "lastUpdated": LAST_UPDATED,
        "sections": [
            {
                "title": "1. Information We Collect",
                "content": "**Account:** email, display name, password (hashed)\n**Usage:** prompts, uploaded images, generated outputs\n**Technical:** IP address, device/browser info, logs\n**Payments:** handled by Stripe; we do not store full card data"
            },
            {
                "title": "2. How We Use Information",
                "content": "• Provide, maintain, and improve the Service\n• Process payments and manage credits\n• Send service-related messages (e.g., receipts, resets)\n• Prevent abuse and ensure security\n• Comply with legal obligations"
            },
            {
                "title": "3. AI Processing",
                "content": "Your prompts and images may be processed by AI providers (e.g., OpenAI) to generate outputs, subject to their processing terms."
            },
            {
                "title": "4. Data Sharing",
                "content": "We do not sell your data. We may share limited data with processors (hosting, payment, email, AI), when required by law, to protect rights and safety, or with your consent."
            },
            {
                "title": "5. Cookies & Ads",
                "content": "We use essential cookies for authentication and functionality. We may also use Google AdSense which can set cookies or similar technologies for ad delivery/measurement. In applicable regions we obtain consent or serve non-personalized ads."
            },
            {
                "title": "6. Data Retention",
                "content": "• Account data: until deletion\n• Generated content: until you delete it or your account\n• Logs: up to 24 months\n• Payment records: per legal requirements"
            },
            {
                "title": "7. Your Rights",
                "content": "You may access, correct, export, or delete your data where applicable. Deleting your account removes stored content except where retention is required by law."
            },
            {
                "title": "8. Security",
                "content": "We use industry-standard measures (encryption in transit, secure hosting, access controls). No method is 100% secure."
            },
            {
                "title": "9. Changes",
                "content": "We will update this policy as needed and reflect the latest date above."
            },
            {
                "title": "10. Contact",
                "content": f"Privacy questions? Contact {SUPPORT}"
            }
        ]
    })

@legal_bp.get("/ads")
def ads():
    """Ad/consent disclosure (handy for AdSense links or CMP)"""
    return _json({
        "title": f"Advertising & Consent - {BRAND}",
        "lastUpdated": LAST_UPDATED,
        "sections": [
            {
                "title": "Ad Services",
                "content": "We use Google AdSense to support free features. AdSense may use cookies or similar technologies to deliver and measure ads."
            },
            {
                "title": "Consent",
                "content": "In regions requiring consent (e.g., EEA/UK), we request consent via a banner. If you decline, we serve non-personalized ads when possible."
            },
            {
                "title": "Managing Choices",
                "content": "You can change preferences via our consent banner and/or your browser settings. See Google’s ad settings for more controls."
            }
        ]
    })