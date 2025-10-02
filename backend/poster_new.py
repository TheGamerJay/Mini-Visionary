# blueprints/poster_new.py
import base64
import io
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict

from flask import Blueprint, request, jsonify, current_app, send_file

# ---- Optional deps kept local to avoid global import conflicts ----
def _lazy_imports():
    import requests  # SDK-free HTTP calls
    try:
        # SQLAlchemy is optional but recommended (DB persistence)
        from sqlalchemy import create_engine, text
        return requests, create_engine, text
    except Exception:
        return requests, None, None

poster_bp = Blueprint("poster", __name__, url_prefix="/api/poster")

# ---------------------------
# Config helpers
# ---------------------------
def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def get_openai_headers() -> Dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Optional: org/project headers if you use them
    if os.getenv("OPENAI_ORG"):
        headers["OpenAI-Organization"] = os.getenv("OPENAI_ORG")
    if os.getenv("OPENAI_PROJECT"):
        headers["OpenAI-Project"] = os.getenv("OPENAI_PROJECT")
    return headers

def get_db_engine():
    # If DATABASE_URL is missing or SQLAlchemy not installed, we'll return None (fallback: base64 response only)
    _, create_engine, _ = _lazy_imports()
    db_url = os.getenv("DATABASE_URL")
    if not db_url or create_engine is None:
        return None
    # Railway often provides a full postgres URL. SQLAlchemy accepts it directly.
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=300)

# Track if table has been initialized in this process
_TABLE_INITIALIZED = False

def ensure_table(engine):
    # Create a small table to store generated images (bytea) if it doesn't exist
    global _TABLE_INITIALIZED

    if engine is None:
        return

    # Only initialize once per process
    if _TABLE_INITIALIZED:
        return

    _, _, text = _lazy_imports()

    with engine.begin() as conn:
        # Drop and recreate table to ensure correct schema
        # This is safe since poster data is temporary/regeneratable
        drop_ddl = text("DROP TABLE IF EXISTS posters;")
        conn.execute(drop_ddl)

        # Create table with correct schema
        create_ddl = text("""
            CREATE TABLE posters (
                id UUID PRIMARY KEY,
                filename TEXT NOT NULL,
                mime TEXT NOT NULL,
                width INT,
                height INT,
                prompt TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                data BYTEA NOT NULL
            );
        """)
        conn.execute(create_ddl)

    _TABLE_INITIALIZED = True

# ---------------------------
# OpenAI Images client (SDK-free)
# ---------------------------
class OpenAIImagesClient:
    GENERATIONS_URL = "https://api.openai.com/v1/images/generations"
    # If you later need edits/variations, add their endpoints similarly

    @staticmethod
    def generate(
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
        quality: str = "standard",   # "hd" if your plan supports it
        background: Optional[str] = None,  # "transparent" or None
        timeout_seconds: int = 60
    ) -> List[Dict]:
        """
        Calls OpenAI Images (DALL·E) via HTTPS and returns list of items with base64 data.
        We request base64 to manage storage ourselves (DB/local/file).
        """
        requests, _, _ = _lazy_imports()
        headers = get_openai_headers()
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": max(1, min(n, 4)),  # cap n to avoid abuse
            "size": size,
            "response_format": "b64_json",
            "quality": "hd" if quality == "hd" else "standard",
        }
        if background == "transparent":
            # API supports background transparency on some models; pass if requested
            payload["background"] = "transparent"

        try:
            resp = requests.post(
                OpenAIImagesClient.GENERATIONS_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=timeout_seconds
            )
        except Exception as e:
            raise RuntimeError(f"Image API request failed: {e}")

        if resp.status_code >= 400:
            # Return the error from OpenAI for visibility
            try:
                err = resp.json()
            except Exception:
                err = {"message": resp.text}
            raise RuntimeError(f"OpenAI error {resp.status_code}: {err}")

        out = resp.json()
        items = out.get("data", [])
        if not items:
            raise RuntimeError("No image returned from OpenAI.")
        return items

# ---------------------------
# Storage
# ---------------------------
class PosterStorage:
    def __init__(self):
        self.engine = get_db_engine()
        if self.engine:
            ensure_table(self.engine)

    def save(self, b64: str, filename: str, mime: str, prompt: str, size: str) -> str:
        """
        Saves the image to Postgres if available; returns poster_id (UUID as str).
        If DB not available, we still return a UUID and keep a short-lived in-memory cache
        so you can immediately GET it once. (Good enough for dev; for prod, keep DB.)
        """
        poster_id = str(uuid.uuid4())
        binary = base64.b64decode(b64)
        width, height = _parse_size(size)

        if self.engine:
            _, _, text = _lazy_imports()
            with self.engine.begin() as conn:
                insert_sql = text("""
                    INSERT INTO posters (id, filename, mime, width, height, prompt, data)
                    VALUES (:id, :filename, :mime, :width, :height, :prompt, :data)
                """)
                conn.execute(
                    insert_sql,
                    {
                        "id": poster_id,
                        "filename": filename,
                        "mime": mime,
                        "width": width,
                        "height": height,
                        "prompt": prompt[:10000],  # safety cap
                        "data": binary
                    }
                )
        else:
            # Dev-only fallback (memory cache)
            _MemoryCache.put(poster_id, filename, mime, binary)

        return poster_id

    def load(self, poster_id: str) -> Optional[Tuple[str, str, bytes]]:
        """
        Returns (filename, mime, bytes) or None.
        """
        if self.engine:
            _, _, text = _lazy_imports()
            with self.engine.begin() as conn:
                row = conn.execute(
                    text("SELECT filename, mime, data FROM posters WHERE id = :id"),
                    {"id": poster_id}
                ).mappings().first()
                if not row:
                    return None
                # Handle PostgreSQL BYTEA - can be bytes, memoryview, or buffer
                data = row["data"]
                if isinstance(data, memoryview):
                    data = data.tobytes()
                elif not isinstance(data, bytes):
                    data = bytes(data)
                return row["filename"], row["mime"], data
        else:
            return _MemoryCache.get(poster_id)

# Dev-only memory cache (process memory). Use DB in production.
class _MemoryCache:
    _CACHE: Dict[str, Tuple[str, str, bytes, float]] = {}
    _TTL_SECONDS = 3600  # 1 hour

    @classmethod
    def put(cls, poster_id: str, filename: str, mime: str, blob: bytes):
        cls._garbage_collect()
        cls._CACHE[poster_id] = (filename, mime, blob, time.time())

    @classmethod
    def get(cls, poster_id: str) -> Optional[Tuple[str, str, bytes]]:
        cls._garbage_collect()
        v = cls._CACHE.get(poster_id)
        if not v:
            return None
        filename, mime, blob, _ = v
        return filename, mime, blob

    @classmethod
    def _garbage_collect(cls):
        now = time.time()
        to_del = []
        for k, (_, _, _, ts) in cls._CACHE.items():
            if now - ts > cls._TTL_SECONDS:
                to_del.append(k)
        for k in to_del:
            cls._CACHE.pop(k, None)

# ---------------------------
# Input validation
# ---------------------------
_ALLOWED_SIZES = {"256x256", "512x512", "1024x1024", "1024x1792", "1792x1024"}
def _parse_size(size: str) -> Tuple[int, int]:
    if size not in _ALLOWED_SIZES:
        size = "1024x1024"
    w, h = size.split("x")
    return int(w), int(h)

def _sanitize_prompt(p: str) -> str:
    p = (p or "").strip()
    # Keep prompts reasonable to avoid extremely long requests/logging
    if len(p) > 2000:
        p = p[:2000]
    return p

def _enhance_prompt_for_full_body(p: str) -> str:
    """
    Automatically enhance prompts to prefer full-body character images.
    Checks if prompt already specifies framing, otherwise adds full-body guidance.
    Also adds instructions to prevent text and multiple subjects.
    """
    p_lower = p.lower()

    # Check if user already specified framing
    framing_keywords = [
        "full body", "full-body", "head to toe", "entire body", "complete body",
        "whole body", "character sheet", "close-up", "closeup", "portrait only",
        "face only", "headshot", "bust", "waist up", "half body"
    ]

    has_framing = any(keyword in p_lower for keyword in framing_keywords)

    # Build enhancement instructions
    enhancements = []

    if not has_framing:
        enhancements.append("full body view showing entire character from head to toe")

    # Always add these unless user explicitly wants text/multiple
    if "text" not in p_lower and "words" not in p_lower and "title" not in p_lower:
        enhancements.append("no text or words in image")

    if "multiple" not in p_lower and "several" not in p_lower and "many" not in p_lower:
        enhancements.append("single character only")

    if enhancements:
        return f"{p}, {', '.join(enhancements)}"

    return p

# ---------------------------
# Routes
# ---------------------------

@poster_bp.route("/generate", methods=["POST"])
def generate_poster():
    """
    Request JSON:
    {
      "prompt": "cinematic cyberpunk poster of ...",
      "size": "1024x1024",      # optional: 256x256|512x512|1024x1024|1024x1792|1792x1024
      "quality": "standard",    # or "hd" (if your plan supports it)
      "n": 1,                   # 1..4 (we cap it to 4)
      "transparent": false      # if true, ask for transparent background
    }

    Response JSON:
    {
      "ok": true,
      "items": [
         {"poster_id": "...", "url": "/api/poster/file/<id>", "filename": "poster-....png"}
      ]
    }

    On failure: {"ok": false, "error": "..."}
    """
    try:
        data = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400

    prompt = _sanitize_prompt(data.get("prompt", ""))
    if not prompt:
        return jsonify({"ok": False, "error": "Missing 'prompt'"}), 400

    # Automatically enhance prompt for full-body images unless user specified otherwise
    prompt = _enhance_prompt_for_full_body(prompt)

    size = data.get("size", "1024x1024")
    if size not in _ALLOWED_SIZES:
        size = "1024x1024"

    quality = "hd" if data.get("quality") == "hd" else "standard"
    n = data.get("n", 1)
    try:
        n = int(n)
    except Exception:
        n = 1
    n = max(1, min(n, 4))

    transparent = bool(data.get("transparent", False))
    background = "transparent" if transparent else None

    try:
        items = OpenAIImagesClient.generate(
            prompt=prompt,
            size=size,
            n=n,
            quality=quality,
            background=background,
            timeout_seconds=int(os.getenv("POSTER_TIMEOUT_SECONDS", "60")),
        )
    except Exception as e:
        current_app.logger.exception("Poster generation failed")
        return jsonify({"ok": False, "error": str(e)}), 502

    storage = PosterStorage()
    out_items = []
    for i, item in enumerate(items):
        b64 = item.get("b64_json")
        if not b64:
            continue
        filename = f"poster-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}.png"
        poster_id = storage.save(b64, filename, "image/png", prompt, size)
        out_items.append({
            "poster_id": poster_id,
            "url": f"/api/poster/file/{poster_id}",
            "filename": filename
        })

    if not out_items:
        return jsonify({"ok": False, "error": "No images returned"}), 502

    return jsonify({"ok": True, "items": out_items}), 200


@poster_bp.route("/file/<poster_id>", methods=["GET"])
def get_poster_file(poster_id: str):
    """
    Streams the stored image (from Postgres if available, otherwise from dev memory cache).
    """
    storage = PosterStorage()
    rec = storage.load(poster_id)
    if not rec:
        return jsonify({"ok": False, "error": "Not found"}), 404

    filename, mime, blob = rec
    return send_file(
        io.BytesIO(blob),
        mimetype=mime,
        as_attachment=False,
        download_name=filename
    )
