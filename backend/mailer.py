from __future__ import annotations
import os
import requests
import smtplib
from email.message import EmailMessage
from typing import Optional, Sequence

# ---- BRAND/SENDER (Mini-Visionary) ----
BRAND_NAME = "Mini-Visionary"
BRAND_TAGLINE = "You Envision it, We Generate it"
SUPPORT_EMAIL = "support@minivisionary.com"

RESEND_API_KEY = os.getenv("RESEND_API_KEY")           # set in Railway
FROM_EMAIL = os.getenv("FROM_EMAIL", SUPPORT_EMAIL)

class MailError(Exception):
    pass

def send_email_post(to: str | Sequence[str], subject: str, html: str, cc=None, bcc=None, reply_to=None):
    """
    Sends email via Resend POST /emails
    Docs: https://resend.com/docs/api-reference/emails/send-email
    """
    if not RESEND_API_KEY:
        raise MailError("Missing RESEND_API_KEY")

    payload = {
        "from": f"{BRAND_NAME} <{FROM_EMAIL}>",
        "to": [to] if isinstance(to, str) else list(to),
        "subject": subject,
        "html": html,
    }
    if cc: payload["cc"] = cc
    if bcc: payload["bcc"] = bcc
    if reply_to: payload["reply_to"] = reply_to

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30,
    )
    if r.status_code >= 300:
        raise MailError(f"Resend error {r.status_code}: {r.text}")
    return r.json()   # includes {"id": "..."}

# ---- LEGACY FUNCTIONS (keep for compatibility) ----
# Preferred: use RESEND_FROM (domain sender). Fallback: FROM_EMAIL (Gmail/SMTP).
RESEND_FROM = os.getenv("RESEND_FROM")  # e.g., noreply@minivisionary.com
FROM_NAME = os.getenv("FROM_NAME", BRAND_NAME)

def _fmt_sender() -> str:
    email = RESEND_FROM or FROM_EMAIL
    if not email:
        raise RuntimeError("No sender configured. Set RESEND_FROM or FROM_EMAIL.")
    # Formats "Name <email@domain>"
    return f"{FROM_NAME} <{email}>"

# ---- SMTP (optional fallback) ----
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "1") == "1"

def _send_via_resend(
    to: Sequence[str],
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    reply_to: Optional[str] = None,
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    tags: Optional[dict] = None,
) -> None:
    if not RESEND_API_KEY:
        raise MailError("RESEND_API_KEY not set")

    payload = {
        "from": _fmt_sender(),           # <- includes name + address
        "to": list(to),
        "subject": subject,
        "html": html or "",
    }
    if text:
        payload["text"] = text
    if reply_to:
        payload["reply_to"] = reply_to
    if cc:
        payload["cc"] = list(cc)
    if bcc:
        payload["bcc"] = list(bcc)
    if tags:
        # Resend supports tags via headers; we also include them in payload for logs
        payload["headers"] = {f"X-Tag-{k}": str(v) for k, v in tags.items()}

    headers = {"Authorization": f"Bearer {RESEND_API_KEY}"}
    r = requests.post(
        "https://api.resend.com/emails",
        json=payload,
        headers=headers,
        timeout=20.0
    )
    if r.status_code >= 300:
        raise MailError(f"Resend failed: {r.status_code} {r.text}")

def _send_via_smtp(
    to: Sequence[str],
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    reply_to: Optional[str] = None,
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
) -> None:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        raise MailError("SMTP env not configured")

    msg = EmailMessage()
    msg["From"] = _fmt_sender()         # <- includes name + address
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject

    if html:
        # multipart/alternative: prefer HTML with text fallback
        msg.set_content(text or " ")
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(text or "")

    targets = list(to) + (list(cc) if cc else []) + (list(bcc) if bcc else [])

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        if SMTP_STARTTLS:
            s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg, to_addrs=targets)

def send_email(
    to: Sequence[str] | str,
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    reply_to: Optional[str] = None,
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    tags: Optional[dict] = None,
) -> None:
    """
    Primary: Resend. Fallback: SMTP (if configured).
    """
    to_list = [to] if isinstance(to, str) else list(to)
    try:
        if RESEND_API_KEY:
            _send_via_resend(to_list, subject, html, text, reply_to, cc, bcc, tags)
        else:
            _send_via_smtp(to_list, subject, html, text, reply_to, cc, bcc)
    except Exception as e:
        raise MailError(str(e)) from e

# ---- Convenience templates (Mini-Visionary) ----
def poster_ready_email(user_email: str, poster_url: str, dashboard_url: Optional[str] = None) -> None:
    subject = f"🎨 Your {BRAND_NAME} poster is ready!"
    dash = dashboard_url or poster_url
    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial;">
      <h2>{BRAND_NAME}</h2>
      <p>Your poster has finished rendering.</p>
      <p><a href="{poster_url}" target="_blank" style="display:inline-block;padding:10px 16px;background:#0ea5e9;color:#fff;text-decoration:none;border-radius:8px;">View Poster</a></p>
      <p>Manage all your posters here: <a href="{dash}" target="_blank">{dash}</a></p>
      <hr/>
      <p style="color:#64748b;font-size:12px;">{BRAND_TAGLINE}</p>
    </div>
    """
    text = f"Your poster is ready: {poster_url}\nDashboard: {dash}"
    send_email(user_email, subject, html=html, text=text, tags={"event": "poster_ready"})

def poster_failed_email(user_email: str, error_message: str) -> None:
    subject = f"⚠️ {BRAND_NAME} failed"
    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial;">
      <h2>{BRAND_NAME}</h2>
      <p>We couldn't complete your poster job.</p>
      <pre style="background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;white-space:pre-wrap">{error_message}</pre>
      <p>Please try again. If this keeps happening, reply to this email.</p>
    </div>
    """
    text = f"Your poster job failed:\n\n{error_message}\n\nPlease try again."
    send_email(user_email, subject, html=html, text=text, tags={"event": "poster_failed"})

def welcome_email(user_email: str, display_name: Optional[str] = None) -> None:
    subject = f"Welcome to {BRAND_NAME} 🌟"
    name = display_name or "there"
    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial;">
      <h2>Welcome, {name}!</h2>
      <p>Thanks for joining <strong>{BRAND_NAME}</strong>.</p>
      <ul>
        <li>Text → Poster (describe it)</li>
        <li>Image → Poster (upload and enhance)</li>
        <li>Auto titles, taglines, and borders</li>
      </ul>
      <p style="color:#64748b;font-size:12px;">{BRAND_TAGLINE}</p>
    </div>
    """
    text = f"Welcome {name}! {BRAND_NAME} is ready for you."
    send_email(user_email, subject, html=html, text=text, tags={"event": "welcome"})

def send_reset_email(user_email: str, reset_url: str) -> None:
    subject = f"Reset your {BRAND_NAME} password"
    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial;">
      <h2>Password Reset</h2>
      <p>You requested to reset your password for {BRAND_NAME}.</p>
      <p><a href="{reset_url}" target="_blank" style="display:inline-block;padding:10px 16px;background:#0ea5e9;color:#fff;text-decoration:none;border-radius:8px;">Reset Password</a></p>
      <p>This link will expire in 24 hours.</p>
      <p>If you didn't request this, you can safely ignore this email.</p>
      <hr/>
      <p style="color:#64748b;font-size:12px;">{BRAND_TAGLINE}</p>
    </div>
    """
    text = f"Reset your password: {reset_url}\n\nThis link expires in 24 hours."
    send_email(user_email, subject, html=html, text=text, tags={"event": "password_reset"})