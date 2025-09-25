import base64, io, os, uuid, boto3
from flask import Blueprint, request, jsonify, g
from auth import auth_required
from PIL import Image
import openai
from wallet import spend_credits
from models import get_session, User

bp = Blueprint("poster", __name__, url_prefix="/api/poster")
openai.api_key = os.getenv("OPENAI_API_KEY")
_S3 = boto3.client("s3", region_name=os.getenv("S3_REGION"))
_BUCKET = os.getenv("S3_BUCKET")
_CDN = os.getenv("CDN_BASE")

def _public_url(key):
    return f"{_CDN}/{key}" if _CDN else f"https://{_BUCKET}.s3.amazonaws.com/{key}"

def _upload_bytes(img_bytes: bytes, key: str, ctype="image/png"):
    _S3.put_object(Bucket=_BUCKET, Key=key, Body=img_bytes, ContentType=ctype, ACL="public-read")
    return _public_url(key)

@bp.post("/generate")
@auth_required
def generate():
    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    style = data.get("style") or "indigo cyan on black, cinematic, poster, high detail"
    if not prompt:
        return jsonify(ok=False, error="missing_prompt"), 400

    # Check if user has enough credits (10 per poster)
    if not spend_credits(g.user_id, 10):
        return jsonify(ok=False, error="insufficient_credits"), 402

    try:
        # 1) create image
        result = openai.images.generate(  # Images API
            model=os.getenv("POSTER_MODEL", "dall-e-3"),
            prompt=f"Poster: {prompt}. Style: {style}. Aspect 4:5, 1200x1500, print-quality.",
            size="1024x1024",  # DALL-E 3 supports 1024x1024, 1024x1792, 1792x1024
            quality="standard",
            n=1
        )

        # Get the image URL from the response
        image_url = result.data[0].url

        # Download the image
        import requests
        img_response = requests.get(image_url)
        if img_response.status_code != 200:
            return jsonify(ok=False, error="failed_to_download_image"), 500

        # 2) optional post-process to ensure PNG + color profile
        im = Image.open(io.BytesIO(img_response.content)).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        img_bytes = buf.getvalue()

        # 3) upload to S3
        key = f"users/{g.user_id}/posters/{uuid.uuid4()}.png"
        public = _upload_bytes(img_bytes, key)

        return jsonify(ok=True, url=public, key=key, prompt=prompt)

    except Exception as e:
        # Refund credits on failure
        with get_session() as s:
            user = s.query(User).filter_by(id=g.user_id).first()
            if user:
                user.credits = (user.credits or 0) + 10
                s.commit()

        return jsonify(ok=False, error=f"generation_failed: {str(e)}"), 500