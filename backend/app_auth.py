# app_auth.py
from __future__ import annotations
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, request, jsonify, session, g
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from models import (
    get_session, User, PasswordReset, CreditLedger,
    CreditEventType
)
from mailer import send_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Configuration
SIGNUP_BONUS_CREDITS = 20
RESET_TOKEN_HOURS = 24

def get_current_user() -> Optional[User]:
    """Get current user from session"""
    user_id = session.get("user_id")
    if not user_id:
        return None

    with get_session() as s:
        return s.query(User).filter_by(id=user_id, is_deleted=False).first()

@auth_bp.post("/register")
def register():
    """
    Register new user
    Body: {email, password, display_name, accept_terms}
    """
    data = request.get_json()
    if not data:
        return {"ok": False, "error": "JSON body required"}, 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    display_name = data.get("display_name", "").strip()
    accept_terms = data.get("accept_terms", False)

    # Validation
    if not email or not password or not display_name:
        return {"ok": False, "error": "email, password, and display_name required"}, 400

    if not accept_terms:
        return {"ok": False, "error": "You must accept Terms and Privacy Policy"}, 400

    if len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters"}, 400

    with get_session() as s:
        # Check if user exists
        existing = s.query(User).filter_by(email=email).first()
        if existing:
            return {"ok": False, "error": "Email already registered"}, 409

        # Create user
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            display_name=display_name,
            credits=SIGNUP_BONUS_CREDITS,
            accept_terms=bool(accept_terms)
        )
        s.add(user)
        s.flush()  # Ensures user.id is available

        # Add signup bonus to ledger
        s.add(CreditLedger(
            user_id=user.id,
            event=CreditEventType.GRANT,
            amount=SIGNUP_BONUS_CREDITS,
            ref="signup_bonus",
            notes="Welcome bonus"
        ))
        s.commit()

        # Auto-login
        session["user_id"] = user.id

        return {
            "ok": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "credits": user.credits,
                "avatar_url": user.avatar_url
            }
        }

@auth_bp.post("/login")
def login():
    """
    Login user
    Body: {email, password}
    """
    data = request.get_json()
    if not data:
        return {"ok": False, "error": "JSON body required"}, 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return {"ok": False, "error": "email and password required"}, 400

    with get_session() as s:
        user = s.query(User).filter_by(email=email, is_deleted=False).first()
        if not user or not check_password_hash(user.password_hash, password):
            return {"ok": False, "error": "Invalid email or password"}, 401

        session["user_id"] = user.id

        return {
            "ok": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "credits": user.credits,
                "avatar_url": user.avatar_url
            }
        }

@auth_bp.post("/logout")
def logout():
    """Logout user"""
    session.clear()
    return {"ok": True}

@auth_bp.post("/forgot")
def forgot_password():
    """
    Send password reset email
    Body: {email}
    """
    data = request.get_json()
    if not data:
        return {"ok": False, "error": "JSON body required"}, 400

    email = data.get("email", "").strip().lower()
    if not email:
        return {"ok": False, "error": "email required"}, 400

    with get_session() as s:
        user = s.query(User).filter_by(email=email, is_deleted=False).first()
        if not user:
            # Don't reveal if email exists or not
            return {"ok": True, "message": "If that email is registered, you'll receive a reset link"}

        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_HOURS)

        reset = PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        s.add(reset)
        s.commit()

        # Send email
        base_url = request.headers.get("Origin") or os.getenv("PUBLIC_APP_URL", "http://localhost:5173")
        reset_url = f"{base_url}/reset?token={token}"

        try:
            send_reset_email(user.email, reset_url)
        except Exception as e:
            print(f"Failed to send reset email: {e}")
            # Still return success to not reveal if email exists

        return {"ok": True, "message": "If that email is registered, you'll receive a reset link"}

@auth_bp.post("/reset")
def reset_password():
    """
    Reset password with token
    Body: {token, password}
    """
    data = request.get_json()
    if not data:
        return {"ok": False, "error": "JSON body required"}, 400

    token = data.get("token", "").strip()
    password = data.get("password", "")

    if not token or not password:
        return {"ok": False, "error": "token and password required"}, 400

    if len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters"}, 400

    with get_session() as s:
        from sqlalchemy import and_
        reset = s.query(PasswordReset).filter(
            and_(
                PasswordReset.token == token,
                PasswordReset.used == False,
                PasswordReset.expires_at > datetime.utcnow()
            )
        ).first()

        if not reset:
            return {"ok": False, "error": "Invalid or expired reset token"}, 400

        # Update user password
        user = s.query(User).filter_by(id=reset.user_id).first()
        if not user:
            return {"ok": False, "error": "User not found"}, 404

        user.password_hash = generate_password_hash(password)
        reset.used = True
        s.commit()

        # Auto-login
        session["user_id"] = user.id

        return {
            "ok": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "credits": user.credits,
                "avatar_url": user.avatar_url
            }
        }

@auth_bp.get("/whoami")
def whoami():
    """Get current user session state for SPA"""
    user = get_current_user()
    if not user:
        return jsonify(None), 200

    # Return only what the UI needs
    return jsonify({
        "id": user.id,
        "email": user.email,
        "display_name": getattr(user, "display_name", None),
        "avatar_url": getattr(user, "avatar_url", None),
    }), 200

@auth_bp.get("/me")
def get_me():
    """Get current user profile"""
    user = get_current_user()
    if not user:
        return {"ok": False, "error": "Not authenticated"}, 401

    return {
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "credits": user.credits,
            "avatar_url": user.avatar_url,
            "plan": user.plan,
            "created_at": user.created_at.isoformat()
        }
    }

# Auth middleware function
def require_auth():
    """Decorator to require authentication and attach g.user"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return {"ok": False, "error": "Authentication required"}, 401
            g.user = user
            return f(*args, **kwargs)
        return wrapper
    return decorator