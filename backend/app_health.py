from __future__ import annotations
from flask import Blueprint, jsonify, current_app, request
import requests

health_bp = Blueprint("health", __name__, url_prefix="/api")

SIGNATURES = {
    "/auth.html":    "Mini Visionary — You Envision it, We Generate It",
    "/terms.html":   "Mini Visionary — Terms of Service",
    "/privacy.html": "Mini Visionary — Privacy Policy",
}

def fetch(url: str) -> tuple[int, str]:
    r = requests.get(url, timeout=5, headers={"Cache-Control": "no-cache"})
    return r.status_code, r.text

def is_spa(html: str) -> bool:
    return 'id="root"' in html.lower()

@health_bp.get("/_health")
def health():
    base = current_app.config.get("PUBLIC_BASE_URL", "").rstrip("/")
    # Fallback to local if not set
    if not base:
        host = current_app.config.get("HOST", "http://localhost:8080").rstrip("/")
        base = host

    checks = {}
    all_ok = True

    for path, needle in SIGNATURES.items():
        url = f"{base}{path}"
        status, body = (0, "")
        ok = False
        spa = False
        try:
            status, body = fetch(url)
            spa = is_spa(body)
            ok = (status == 200) and (needle.lower() in body.lower()) and (not spa)
        except Exception as e:
            checks[path] = {"ok": False, "error": str(e)}
            all_ok = False
            continue

        checks[path] = {
            "ok": ok,
            "status": status,
            "spa_leak": spa,
            "has_signature": needle.lower() in body.lower(),
        }
        if not ok:
            all_ok = False

    return jsonify({
        "ok": all_ok,
        "service": "mini-visionary",
        "version": current_app.config.get("APP_VERSION", "dev"),
        "base": base,
        "checks": checks,
    }), (200 if all_ok else 503)

@health_bp.after_request
def _no_cache_health(resp):
    if request.path == "/api/_health":
        resp.headers["Cache-Control"] = "no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
    return resp