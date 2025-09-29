import os
import time
import jwt
from functools import wraps
from typing import Optional

from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.exceptions import Unauthorized
from flask_bcrypt import Bcrypt
from werkzeug.security import check_password_hash as wz_check_password_hash

from models import get_session, User

# Public objects expected by app.py and other modules (e.g. /api/generate)
bcrypt = Bcrypt()
bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# JWT/brand config
SECRET = os.getenv("SECRET_KEY", "dev-secret")                 # used to sign/verify JWTs
TTL = int(os.getenv("JWT_EXPIRES_MIN", "43200")) * 60          # default 30 days (min->sec)
PUBLIC_APP_URL = os.getenv("PUBLIC_APP_URL", "https://app.minivisionary.com")


# ----------------------- Helpers -----------------------

def get_user_by_email(email: str) -> Optional[User]:
    email = (email or "").lower().strip()
    if not email:
        return None
    with get_session() as s:
        return s.query(User).filter_by(email=email).first()

def create_user(display_name: str, email: str, password_hash: str) -> dict:
    with get_session() as s:
        user = User(
            display_name=display_name,
            email=email.lower().strip(),
            password_hash=password_hash,
            credits=20  # signup bonus
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
    """
    Backward-compatible password check.
    Supports legacy Werkzeug PBKDF2 hashes ('pbkdf2:...') and current bcrypt ('$2b$', '$2a$', '$2y$').
    """
    if not hashed or not plain:
        return False
    try:
        h = str(hashed)
        if h.startswith("pbkdf2:"):
            # Legacy accounts created with Werkzeug generate_password_hash
            return wz_check_password_hash(h, plain)
        if h.startswith("$2a$") or h.startswith("$2b$") or h.startswith("$2y$"):
            # Bcrypt (current)
            return bcrypt.check_password_hash(h, plain)
        # Unknown format -> fail closed
        return False
    except Exception:
        return False

def maybe_upgrade_hash_to_bcrypt(user: User, plain_password: str) -> None:
    """If user has a legacy PBKDF2 hash, upgrade it to bcrypt after a successful login."""
    try:
        if str(user.password_hash).startswith("pbkdf2:"):
            new_hash = bcrypt.generate_password_hash(plain_password).decode()
            with get_session() as s:
                u = s.query(User).filter_by(id=user.id).first()
                if u:
                    u.password_hash = new_hash
                    s.commit()
            current_app.logger.info("Upgraded password hash to bcrypt for user_id=%s", user.id)
    except Exception as e:
        current_app.logger.warning("Hash upgrade failed for user_id=%s err=%s", user.id, e)

def sign_jwt(user_id, email: str) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + TTL,
        # Optional:
        # "iss": "mini-visionary",
        # "aud": "mini-visionary-web",
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_app.logger.info("[auth_required] Checking auth for %s", request.endpoint)
        hdr = request.headers.get("Authorization", "")
        current_app.logger.info("[auth_required] Auth header: %s", hdr[:20] + "..." if len(hdr) > 20 else hdr)

        if not hdr.startswith("Bearer "):
            current_app.logger.warning("[auth_required] Missing bearer token")
            raise Unauthorized("Missing bearer token")

        token = hdr.split(" ", 1)[1].strip()
        current_app.logger.info("[auth_required] Token extracted: %s", token[:20] + "...")

        try:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            current_app.logger.info("[auth_required] Token decoded successfully, user_id=%s", payload.get("sub"))
        except jwt.ExpiredSignatureError:
            current_app.logger.warning("[auth_required] Token expired")
            raise Unauthorized("Token expired")
        except Exception as e:
            current_app.logger.warning("[auth_required] Invalid token: %s", str(e))
            raise Unauthorized("Invalid token")

        with get_session() as s:
            user_id = int(payload.get("sub"))
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                current_app.logger.warning("[auth_required] User not found: %s", payload.get("sub"))
                raise Unauthorized("User not found")

            current_app.logger.info("[auth_required] User found: %s", user.email)
            g.user_id = user.id
            g.user = user
            g.email = user.email

        return fn(*args, **kwargs)
    return wrapper


# ----------------------- Routes -----------------------

@bp.post("/signup")
def signup():
    try:
        data = request.get_json(silent=True) or {}
        display_name = (data.get("display_name") or "").strip()
        email = (data.get("email") or "").lower().strip()
        password = data.get("password") or ""

        if not (display_name and email and password and len(password) >= 8):
            return jsonify(ok=False, error="invalid_input"), 400

        if get_user_by_email(email):
            return jsonify(ok=False, error="email_exists"), 400

        hashed = bcrypt.generate_password_hash(password).decode()
        user = create_user(display_name, email, hashed)
        token = sign_jwt(user["id"], email)

        # Send welcome email
        try:
            from app_email import send_email
            from app_email_templates import get_welcome_email_template

            email_template = get_welcome_email_template(display_name)
            send_email(
                to=email,
                subject=email_template["subject"],
                html=email_template["html"],
                text=email_template["text"]
            )
            current_app.logger.info("Welcome email sent to %s", email)
        except Exception as email_error:
            current_app.logger.warning("Welcome email failed for %s: %s", email, email_error)
            # Continue with signup even if email fails

        return jsonify(ok=True, token=token, user=user)
    except Exception as e:
        current_app.logger.exception("Signup error: %s", e)
        return jsonify(ok=False, error="server_error"), 500


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    # Loud but safe debug (no plaintext password)
    current_app.logger.info("[auth.login] email=%s json_keys=%s", email, list(data.keys()))

    user = get_user_by_email(email)
    if not user:
        return jsonify(ok=False, error="invalid_credentials"), 401

    if not verify_password(user.password_hash, password):
        return jsonify(ok=False, error="invalid_credentials"), 401

    # Upgrade legacy pbkdf2 -> bcrypt after successful login
    maybe_upgrade_hash_to_bcrypt(user, password)

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
    current_app.logger.info("[auth.me] Success for user_id=%s email=%s", g.user.id, g.user.email)
    avatar = getattr(g.user, 'avatar_url', None)
    return jsonify(ok=True, user={
        "id": g.user.id,
        "email": g.user.email,
        "display_name": g.user.display_name,
        "credits": g.user.credits,
        "avatar_image_url": avatar if avatar and not avatar.startswith('data:video/') else None,
        "avatar_video_url": avatar if avatar and avatar.startswith('data:video/') else None,
        "ad_free": getattr(g.user, 'ad_free', False)
    })


@bp.post("/forgot")
def forgot():
    from mailer import send_reset_email, MailError

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()

    if not email:
        return jsonify(ok=False, error="email_required"), 400

    user = get_user_by_email(email)

    if user:
        try:
            now = int(time.time())
            reset_payload = {
                "sub": str(user.id),
                "email": user.email,
                "type": "password_reset",
                "iat": now,
                "exp": now + (24 * 60 * 60),  # 24 hours
            }
            reset_token = jwt.encode(reset_payload, SECRET, algorithm="HS256")
            reset_url = f"{PUBLIC_APP_URL}/reset-password?token={reset_token}"
            send_reset_email(user.email, reset_url)
            current_app.logger.info("Password reset email sent to %s", user.email)
        except MailError as e:
            current_app.logger.warning("Reset email failed for %s: %s", user.email, e)
            # Return success anyway to avoid enumeration

    return jsonify(ok=True, message="reset_email_sent")


@bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("password") or ""

    if not token or len(new_password) < 8:
        return jsonify(ok=False, error="invalid_input"), 400

    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            raise jwt.InvalidTokenError("Invalid token type")

        user_id = int(payload["sub"])
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
    """Return wallet/credits info for authenticated user."""
    from models import CreditLedger, CreditEventType  # lazy import to avoid circulars

    with get_session() as s:
        receipts_q = (
            s.query(CreditLedger)
            .filter_by(user_id=g.user_id, event=CreditEventType.PURCHASE)
            .order_by(CreditLedger.created_at.desc())
            .limit(10)
        )

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