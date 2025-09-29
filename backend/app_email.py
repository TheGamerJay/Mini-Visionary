# app_email.py
import os
from resend import Resend

RESEND = Resend(api_key=os.getenv("RESEND_API_KEY"))
FROM = os.getenv("RESEND_FROM") or f'{os.getenv("FROM_NAME","")} <{os.getenv("FROM_EMAIL","")}>'
REPLY_TO = os.getenv("REPLY_TO")  # optional

def send_email(to: str, subject: str, html: str, text: str | None = None):
    payload = {
        "from": FROM,
        "to": to,
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    if REPLY_TO:
        payload["reply_to"] = REPLY_TO

    return RESEND.emails.send(payload)