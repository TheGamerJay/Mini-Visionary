import base64, io, os, uuid, boto3, requests
from flask import Blueprint, request, jsonify, g
from auth import auth_required
from PIL import Image
import openai
from wallet import spend_credits
from models import get_session, User

bp = Blueprint("poster", __name__, url_prefix="/api/poster")

# ---- Config / Clients ----
openai.api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
_S3 = boto3.client("s3", region_name=os.getenv("S3_REGION")) if os.getenv("S3_BUCKET") else None
_BUCKET = os.getenv("S3_BUCKET")
_CDN = os.getenv("CDN_BASE")  # e.g., CloudFront
CREDITS_PER_POSTER = int(os.getenv("CREDITS_PER_POSTER", "10"))
DEFAULT_IMAGE_MODEL = os.getenv("POSTER_MODEL", "dall-e-3")
DEFAULT_SIZE = os.getenv("POSTER_SIZE", "1024x1024")  # DALL·E 3 supports 1024x1024, 1024x1792, 1792x1024
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8080")

# Local storage fallback
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

def _public_url(key: str) -> str:
    if _BUCKET:
        if _CDN:
            return f"{_CDN.rstrip('/')}/{key}"
        return f"https://{_BUCKET}.s3.amazonaws.com/{key}"
    else:
        # Local storage fallback
        return f"{PUBLIC_BASE_URL.rstrip('/')}/uploads/{key}"

def _upload_bytes(img_bytes: bytes, key: str, ctype="image/png"):
    if _BUCKET and _S3:
        # S3 upload
        _S3.put_object(Bucket=_BUCKET, Key=key, Body=img_bytes, ContentType=ctype, ACL="public-read")
        return _public_url(key)
    else:
        # Local storage fallback
        local_path = os.path.join(UPLOADS_DIR, key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(img_bytes)
        return _public_url(key)

def _refund_credits(user_id: int, amount: int):
    try:
        with get_session() as s:
            user = s.query(User).filter_by(id=user_id).first()
            if user:
                user.credits = (user.credits or 0) + amount
                s.commit()
    except Exception:
        # swallow refund errors; don't mask original
        pass

@bp.post("/generate")
@auth_required
def generate():
    if not openai.api_key:
        return jsonify(ok=False, error="openai_not_configured"), 503

    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    style = (data.get("style") or "indigo cyan on black, cinematic, poster, high detail").strip()
    size = (data.get("size") or DEFAULT_SIZE).strip()

    if not prompt:
        return jsonify(ok=False, error="missing_prompt"), 400

    # Spend first to prevent double-runs
    if not spend_credits(g.user_id, CREDITS_PER_POSTER):
        return jsonify(ok=False, error="insufficient_credits"), 402

    try:
        # 1) Request image
        result = openai.images.generate(
            model=DEFAULT_IMAGE_MODEL,
            prompt=f"Poster: {prompt}. Style: {style}. Aspect should match {size}. Print-quality.",
            size=size,
            quality="standard",
            n=1
        )

        # 2) Get image bytes (URL or base64)
        img_bytes = None
        if getattr(result.data[0], "url", None):
            image_url = result.data[0].url
            r = requests.get(image_url, timeout=30)
            if r.status_code != 200:
                raise RuntimeError(f"download_failed: {r.status_code}")
            img_bytes = r.content
        elif getattr(result.data[0], "b64_json", None):
            img_bytes = base64.b64decode(result.data[0].b64_json)
        else:
            raise RuntimeError("no_image_returned")

        # 3) Normalize to PNG (RGB) and capture dimensions
        im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = im.size
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        png_bytes = buf.getvalue()

        # 4) Upload to S3
        key = f"users/{g.user_id}/posters/{uuid.uuid4()}.png"
        public_url = _upload_bytes(png_bytes, key, ctype="image/png")

        return jsonify(ok=True, url=public_url, key=key, prompt=prompt, width=w, height=h)

    except Exception as e:
        _refund_credits(g.user_id, CREDITS_PER_POSTER)
        return jsonify(ok=False, error=f"generation_failed: {e}"), 500