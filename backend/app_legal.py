# app_legal.py
from __future__ import annotations
from flask import Blueprint, jsonify

legal_bp = Blueprint("legal", __name__, url_prefix="/api/legal")

@legal_bp.get("/terms")
def terms():
    """Terms of Service content as JSON for React components"""
    return jsonify({
        "title": "Terms of Service - Mini Dream Poster",
        "lastUpdated": "January 2025",
        "sections": [
            {
                "title": "1. Acceptance of Terms",
                "content": "By using Mini Dream Poster (\"Service\"), you agree to these Terms of Service (\"Terms\"). If you don't agree, don't use our service."
            },
            {
                "title": "2. Service Description",
                "content": "Mini Dream Poster is an AI-powered poster generation service that creates custom posters from text prompts or uploaded images using credits-based pricing."
            },
            {
                "title": "3. User Accounts",
                "content": "You must provide accurate information when creating an account. You're responsible for maintaining account security and all activities under your account."
            },
            {
                "title": "4. Credits and Payments",
                "content": "• Each poster generation costs 10 credits\\n• Credits are non-refundable except for failed generations\\n• Prices are subject to change with notice\\n• Failed generations receive automatic refunds"
            },
            {
                "title": "5. Content Policy",
                "content": "You may not generate content that is:\\n• Illegal, harmful, or threatening\\n• Infringing on others' rights\\n• Spam or misleading\\n• Adult content involving minors"
            },
            {
                "title": "6. Intellectual Property",
                "content": "• You retain rights to your input content\\n• Generated posters are yours to use\\n• Our service and technology remain our property\\n• Don't reverse engineer our systems"
            },
            {
                "title": "7. Limitation of Liability",
                "content": "Our service is provided \"as is.\" We're not liable for indirect damages, and our total liability is limited to amounts you've paid us."
            },
            {
                "title": "8. Termination",
                "content": "We may suspend or terminate accounts for Terms violations. You can delete your account anytime."
            },
            {
                "title": "9. Changes",
                "content": "We may update these Terms. Continued use constitutes acceptance of changes."
            },
            {
                "title": "10. Contact",
                "content": "Questions? Contact us at support@minidreamposter.com"
            }
        ]
    })

@legal_bp.get("/privacy")
def privacy():
    """Privacy Policy content as JSON for React components"""
    return jsonify({
        "title": "Privacy Policy - Mini Dream Poster",
        "lastUpdated": "January 2025",
        "sections": [
            {
                "title": "1. Information We Collect",
                "content": "**Account Information:** Email, display name, password (hashed)\\n**Usage Data:** Prompts, uploaded images, generated posters\\n**Technical Data:** IP address, browser info, usage patterns\\n**Payment Data:** Processed by payment providers (not stored by us)"
            },
            {
                "title": "2. How We Use Information",
                "content": "• Provide and improve our service\\n• Process payments and manage credits\\n• Send service-related communications\\n• Prevent abuse and ensure security\\n• Comply with legal obligations"
            },
            {
                "title": "3. AI Processing",
                "content": "Your prompts and images are processed by AI services (OpenAI) to generate posters. These providers may have their own data practices."
            },
            {
                "title": "4. Data Sharing",
                "content": "We don't sell your data. We may share information:\\n• With service providers (hosting, payment, AI)\\n• When required by law\\n• To protect our rights and safety\\n• With your consent"
            },
            {
                "title": "5. Data Retention",
                "content": "• Account data: Until account deletion\\n• Generated posters: Until you delete them\\n• Usage logs: Up to 2 years\\n• Payment records: As required by law"
            },
            {
                "title": "6. Your Rights",
                "content": "You can:\\n• Access and update your information\\n• Delete your account and data\\n• Export your posters\\n• Request data correction"
            },
            {
                "title": "7. Security",
                "content": "We use industry-standard security measures including encryption, secure hosting, and regular security updates."
            },
            {
                "title": "8. Cookies",
                "content": "We use session cookies for authentication and functionality. No tracking cookies."
            },
            {
                "title": "9. Changes",
                "content": "We'll notify you of significant privacy policy changes."
            },
            {
                "title": "10. Contact",
                "content": "Privacy questions? Contact us at support@minidreamposter.com"
            }
        ]
    })