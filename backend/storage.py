import os, uuid, boto3
from flask import Blueprint, request, jsonify, g
from auth import auth_required

bp = Blueprint("storage", __name__, url_prefix="/api/storage")
_s3 = boto3.client("s3", region_name=os.getenv("S3_REGION"))
_BUCKET = os.getenv("S3_BUCKET")
_CDN = os.getenv("CDN_BASE")  # if None, fallback to s3 URL

def _public_url(key: str) -> str:
    return f"{_CDN}/{key}" if _CDN else f"https://{_BUCKET}.s3.amazonaws.com/{key}"

@bp.post("/presign")
@auth_required
def presign():
    data = request.get_json() or {}
    ext = (data.get("ext") or "png").lstrip(".").lower()
    ctype = data.get("contentType") or f"image/{'jpeg' if ext=='jpg' else ext}"
    key = data.get("key") or f"users/{g.user_id}/uploads/{uuid.uuid4()}.{ext}"
    url = _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": _BUCKET, "Key": key, "ContentType": ctype, "ACL": "public-read"},
        ExpiresIn=900,
    )
    return jsonify(ok=True, uploadUrl=url, publicUrl=_public_url(key), key=key)