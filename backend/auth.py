import os
import time
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import Unauthorized
from flask_bcrypt import Bcrypt
from models import get_session, User

bcrypt = Bcrypt()
bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SECRET = os.getenv("SECRET_KEY", "dev-secret")
# Default: 30 days in minutes -> seconds
TTL = int(os.getenv("JWT_EXPIRES_MIN", "43200")) * 60

# Brand-aware defaults
PUBLIC_APP_URL = os.getenv("PUBLIC_APP_URL", "https://app.minivisionary.com")

def get_user_by_email(email: str):
    email = (email or "").lower().strip()
    if not email:
        return None
    with get_session() as s:
        return s.query(User).filter_by(email=email).first()

def create_user(display_name: str, email: str, password_hash: str):
    with get_session() as s:
        user = User(
            display_name=display_name,
            email=email.lower().strip(),
            password_hash=password_hash,
            credits=10,  # signup bonus
            accept_terms=True
        )
        s.add(user)
        s.commit()
        s.refresh(user)
        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "credits": user.credits
        }

def verify_password(hashed: str, plain: str) -> bool:
    if not hashed or not plain:
        return False
    try:
        return bcrypt.check_password_hash(hashed, plain)
    except Exception:
        return False

def sign_jwt(user_id, email: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + TTL,
        # Optional: issuer/audience if you want
        # "iss": "mini-visionary",
        # "aud": "mini-visionary-web",
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        hdr = request.headers.get("Authorization", "")
        if not hdr.startswith("Bearer "):
            raise Unauthorized("Missing bearer token")
        token = hdr.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise Unauthorized("Token expired")
        except Exception:
            raise Unauthorized("Invalid token")

        # Load and attach current user
        with get_session() as s:
            user = s.query(User).filter_by(id=payload.get("sub")).first()
            if not user:
                raise Unauthorized("User not found")
            g.user_id = user.id
            g.user = user
            g.email = user.email

        return fn(*args, **kwargs)
    return wrapper

@bp.post("/signup")
def signup():
    data = request.get_json() or {}
    display_name = (data.get("display_name") or "").strip()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    if not (display_name and email and password and len(password) >= 8):
        return jsonify(ok=False, error="invalid_input"), 400

    # Check if user already exists
    if get_user_by_email(email):
        return jsonify(ok=False, error="email_exists"), 400

    hashed = bcrypt.generate_password_hash(password).decode()
    user = create_user(display_name, email, hashed)
    token = sign_jwt(user["id"], email)

    return jsonify(ok=True, token=token, user=user)

@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    user = get_user_by_email(email)
    if not user or not verify_password(user.password_hash, password):
        return jsonify(ok=False, error="invalid_credentials"), 401

    token = sign_jwt(user.id, email)
    return jsonify(ok=True, token=token, user={
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "credits": user.credits
    })

@bp.get("/me")
@auth_required
def me():
    return jsonify(ok=True, user={
        "id": g.user.id,
        "email": g.user.email,
        "display_name": g.user.display_name,
        "credits": g.user.credits,
        "avatar_url": g.user.avatar_url,
        "ad_free": g.user.ad_free
    })

@bp.post("/forgot")
def forgot():
    from mailer import send_reset_email, MailError

    data = request.get_json() or {}
    email = (data.get("email") or "").lower().strip()

    if not email:
        return jsonify(ok=False, error="email_required"), 400

    user = get_user_by_email(email)

    if user:
        try:
            now = int(time.time())
            reset_payload = {
                "sub": user.id,
                "email": user.email,
                "type": "password_reset",
                "iat": now,
                "exp": now + (24 * 60 * 60)  # 24 hours
            }
            reset_token = jwt.encode(reset_payload, SECRET, algorithm="HS256")

            # Build reset URL (brand-aware default)
            reset_url = f"{PUBLIC_APP_URL}/reset-password?token={reset_token}"

            send_reset_email(user.email, reset_url)
        except MailError:
            # Log internally if you like; don't leak to client
            pass

    # Always return success to prevent user enumeration
    return jsonify(ok=True, message="reset_email_sent")

@bp.post("/reset-password")
def reset_password():
    """Reset password using token from email"""
    data = request.get_json() or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("password") or ""

    if not token or len(new_password) < 8:
        return jsonify(ok=False, error="invalid_input"), 400

    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            raise jwt.InvalidTokenError("Invalid token type")

        user_id = payload["sub"]
        email = payload["email"]

        with get_session() as s:
            user = s.query(User).filter_by(id=user_id, email=email).first()
            if not user:
                return jsonify(ok=False, error="user_not_found"), 404

            hashed = bcrypt.generate_password_hash(new_password).decode()
            user.password_hash = hashed
            s.commit()

        return jsonify(ok=True, message="password_reset_success")

    except jwt.ExpiredSignatureError:
        return jsonify(ok=False, error="token_expired"), 400
    except jwt.InvalidTokenError:
        return jsonify(ok=False, error="invalid_token"), 400

@bp.get("/wallet")
@auth_required
def wallet():
    """Get wallet/credits info for authenticated user"""
    from models import CreditLedger, CreditEventType

    with get_session() as s:
        receipts_q = (s.query(CreditLedger)
                        .filter_by(user_id=g.user_id, event=CreditEventType.PURCHASE)
                        .order_by(CreditLedger.created_at.desc())
                        .limit(10))

        receipts = [{
            "id": r.id,
            "amount": r.amount,
            "date": r.created_at.isoformat(),
            "reference": r.ref,
            "notes": r.notes
        } for r in receipts_q]

    return jsonify(
        ok=True,
        credits_remaining=g.user.credits or 0,
        receipts=receipts
    )