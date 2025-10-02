import os
from flask import Blueprint, jsonify

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')

@debug_bp.route('/openai', methods=['GET'])
def openai_config():
    """Check if OpenAI API key is configured"""
    key = os.getenv('OPENAI_API_KEY')
    return jsonify({
        "ok": bool(key),
        "has_key": bool(key),
        "key_prefix": key[:10] + "..." if key else None,
        "org": bool(os.getenv('OPENAI_ORG')),
        "project": bool(os.getenv('OPENAI_PROJECT'))
    }), (200 if key else 500)
