import os, uuid, boto3
from flask import Blueprint, request, jsonify, g
from auth import auth_required

bp = Blueprint("storage", __name__, url_prefix="/api/storage")

_s3 = boto3.client("s3", region_name=os.getenv("S3_REGION"))
_BUCKET = os.getenv("S3_BUCKET")
_CDN = os.getenv("CDN_BASE")  # optional CloudFront or R2 CDN

def _public_url(key: str) -> str:
    if not _BUCKET:
        raise RuntimeError("S3_BUCKET not configured")
    return f"{_CDN.rstrip('/')}/{key}" if _CDN else f"https://{_BUCKET}.s3.amazonaws.com/{key}"

@bp.post("/presign")
@auth_required
def presign():
    if not _BUCKET:
        return jsonify(ok=False, error="storage_not_configured"), 503

    data = request.get_json() or {}
    ext = (data.get("ext") or "png").lstrip(".").lower()

    # prevent abuse: only allow safe extensions
    if ext not in {"png", "jpg", "jpeg", "webp"}:
        return jsonify(ok=False, error="invalid_extension"), 400

    ctype = data.get("contentType") or f"image/{'jpeg' if ext == 'jpg' else ext}"

    # Always scope keys under the user’s folder
    key = data.get("key") or f"users/{g.user_id}/uploads/{uuid.uuid4()}.{ext}"

    try:
        url = _s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": _BUCKET,
                "Key": key,
                "ContentType": ctype,
                "ACL": "public-read",  # if you want private, drop ACL and use signed GET
            },
            ExpiresIn=900,  # 15 minutes
        )
    except Exception as e:
        return jsonify(ok=False, error=f"presign_failed: {e}"), 500

    return jsonify(ok=True, uploadUrl=url, publicUrl=_public_url(key), key=key)