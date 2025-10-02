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
    create_engine = text = None
    try:
        # SQLAlchemy is optional but recommended (DB persistence)
        from sqlalchemy import create_engine, text
    except Exception:
        pass
    Image = None
    try:
        from PIL import Image  # Pillow for preprocessing reference images
    except Exception:
        pass
    return requests, create_engine, text, Image

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
    _, create_engine, _, _ = _lazy_imports()
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

    _, _, text, _ = _lazy_imports()

    with engine.begin() as conn:
        # Drop and recreate posters table to ensure correct schema
        # This is safe since poster data is temporary/regeneratable
        drop_ddl = text("DROP TABLE IF EXISTS posters;")
        conn.execute(drop_ddl)

        # Create posters table with correct schema
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

        # Create user_prompt_history table for learning patterns
        history_ddl = text("""
            CREATE TABLE IF NOT EXISTS user_prompt_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id TEXT NOT NULL,
                original_prompt TEXT NOT NULL,
                enhanced_prompt TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        conn.execute(history_ddl)

        # Create index for faster user lookups
        index_ddl = text("""
            CREATE INDEX IF NOT EXISTS idx_prompt_history_user
            ON user_prompt_history(user_id, created_at DESC);
        """)
        conn.execute(index_ddl)

        # Create user_style_preferences table for manual presets
        prefs_ddl = text("""
            CREATE TABLE IF NOT EXISTS user_style_preferences (
                user_id TEXT PRIMARY KEY,
                default_style TEXT,
                auto_apply BOOLEAN DEFAULT TRUE,
                custom_instructions TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        conn.execute(prefs_ddl)

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
        requests, _, _, _ = _lazy_imports()
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


class OpenAIImagesEditClient:
    """DALL-E 2 image editing with reference image support"""
    EDITS_URL = "https://api.openai.com/v1/images/edits"
    MODEL = "dall-e-2"

    @staticmethod
    def edit(
        prompt: str,
        image_blob: bytes,
        size: str = "1024x1024",
        n: int = 1,
        timeout_seconds: int = 60
    ) -> List[Dict]:
        """
        Calls OpenAI images/edits with multipart form (SDK-free).
        image_blob must be PNG bytes with alpha (transparent areas to edit).
        """
        requests, _, _, _ = _lazy_imports()
        headers = get_openai_headers()
        # Remove Content-Type header - requests will set it for multipart/form-data
        if "Content-Type" in headers:
            del headers["Content-Type"]

        data = {
            "prompt": prompt,
            "model": OpenAIImagesEditClient.MODEL,
            "size": size,
            "n": str(max(1, min(int(n or 1), 4))),
            "response_format": "b64_json",
        }
        files = {
            "image": ("reference.png", image_blob, "image/png"),
        }

        try:
            resp = requests.post(
                OpenAIImagesEditClient.EDITS_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=timeout_seconds
            )
        except Exception as e:
            raise RuntimeError(f"Image edit request failed: {e}")

        if resp.status_code >= 400:
            try:
                err = resp.json()
            except Exception:
                err = {"message": resp.text}
            raise RuntimeError(f"OpenAI edit error {resp.status_code}: {err}")

        out = resp.json()
        items = out.get("data", [])
        if not items:
            raise RuntimeError("No edited image returned from OpenAI.")
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
_EDIT_SIZES = {"256x256", "512x512", "1024x1024"}  # DALL-E 2 edits only support square

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

def _preprocess_reference_to_square_png_alpha(file_storage, size: str) -> bytes:
    """
    - Loads uploaded image via Pillow
    - Converts to RGBA
    - Makes it square by transparent padding (centered)
    - Resizes to target (256|512|1024)
    - Saves PNG (optimize), ensures < 4MB (downscales if needed)
    Returns PNG bytes ready for /images/edits.
    """
    *_, Image = _lazy_imports()
    if Image is None:
        raise RuntimeError("Pillow (PIL) not installed. Install with: pip install Pillow")

    # Read into Pillow
    file_storage.stream.seek(0)
    img = Image.open(file_storage.stream).convert("RGBA")

    # Square pad with transparency
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    offset = ((side - w) // 2, (side - h) // 2)
    canvas.paste(img, offset)

    # Resize to requested size (must be square for DALL-E 2 edits)
    if size not in _EDIT_SIZES:
        size = "1024x1024"
    target_w, target_h = _parse_size(size)
    target_size = max(target_w, target_h)  # Ensure square
    canvas = canvas.resize((target_size, target_size), Image.LANCZOS)

    # Save to PNG bytes with optimization; enforce < 4MB
    def encode(pil_image) -> bytes:
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    png_bytes = encode(canvas)
    # If still > 4MB, progressively downscale
    max_bytes = 4 * 1024 * 1024
    current = canvas
    while len(png_bytes) > max_bytes and current.size[0] > 256:
        new_side = int(current.size[0] * 0.85)
        current = current.resize((new_side, new_side), Image.LANCZOS)
        png_bytes = encode(current)

    if len(png_bytes) > max_bytes:
        raise RuntimeError("Reference image exceeds 4MB after processing. Try a smaller size.")

    return png_bytes

def _learn_from_history(user_id: str, engine) -> dict:
    """
    Analyze user's prompt history to learn their patterns.
    Returns learned preferences like common styles, keywords, etc.
    """
    if not engine or not user_id:
        return {}

    _, _, text = _lazy_imports()

    # Get last 50 prompts from this user
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT original_prompt
                FROM user_prompt_history
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"user_id": user_id}
        ).fetchall()

    if not rows or len(rows) < 5:  # Need at least 5 prompts to learn
        return {}

    # Analyze patterns
    prompts = [row[0].lower() for row in rows]
    total = len(prompts)

    # Common style keywords to detect
    style_patterns = {
        "3d": 0, "2d": 0, "cartoon": 0, "anime": 0, "realistic": 0,
        "oil painting": 0, "watercolor": 0, "digital art": 0,
        "sketch": 0, "illustration": 0, "pixel art": 0, "render": 0
    }

    # Count occurrences
    for prompt in prompts:
        for style in style_patterns:
            if style in prompt:
                style_patterns[style] += 1

    # Find dominant styles (appears in >50% of prompts)
    learned = {}
    for style, count in style_patterns.items():
        if count / total >= 0.5:  # 50% threshold
            learned[style] = count / total

    # Sort by frequency
    if learned:
        learned = dict(sorted(learned.items(), key=lambda x: x[1], reverse=True))

    return learned

def _get_user_preferences(user_id: str, engine) -> dict:
    """
    Get user's manual style preferences from database.
    """
    if not engine or not user_id:
        return {}

    _, _, text, _ = _lazy_imports()

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT default_style, auto_apply, custom_instructions
                FROM user_style_preferences
                WHERE user_id = :user_id
            """),
            {"user_id": user_id}
        ).fetchone()

    if not row:
        return {}

    return {
        "default_style": row[0],
        "auto_apply": row[1],
        "custom_instructions": row[2]
    }

def _save_prompt_to_history(user_id: str, original: str, enhanced: str, engine):
    """
    Save prompt to history for learning.
    """
    if not engine or not user_id:
        return

    _, _, text, _ = _lazy_imports()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO user_prompt_history (user_id, original_prompt, enhanced_prompt)
                VALUES (:user_id, :original, :enhanced)
            """),
            {"user_id": user_id, "original": original, "enhanced": enhanced}
        )

def _smart_enhance_prompt(p: str, user_id: str = None, engine = None) -> str:
    """
    Smart prompt enhancement combining:
    1. User's manual preferences (presets)
    2. Auto-learned patterns from history
    3. Basic quality enhancements
    """
    p_lower = p.lower()
    enhancements = []

    # Step 1: Get user's manual preferences
    prefs = _get_user_preferences(user_id, engine) if user_id and engine else {}

    # Step 2: Learn from user's history
    learned = _learn_from_history(user_id, engine) if user_id and engine else {}

    # Step 3: Check if prompt already has style info
    style_keywords = [
        "3d", "2d", "cartoon", "anime", "realistic", "oil painting", "watercolor",
        "digital art", "sketch", "drawing", "illustration", "render", "style",
        "background", "scene", "landscape", "environment", "composition"
    ]
    has_style = any(keyword in p_lower for keyword in style_keywords)

    # Step 4: Apply manual preset if enabled and no style specified
    if prefs.get("auto_apply") and prefs.get("default_style") and not has_style:
        enhancements.append(prefs["default_style"])

    # Step 5: Apply learned patterns if no style specified
    elif learned and not has_style:
        # Use the most common learned style (first in sorted dict)
        top_style = next(iter(learned.keys()), None)
        if top_style:
            # Build natural style string
            if top_style == "3d" and "cartoon" in learned:
                enhancements.append("3D cartoon style")
            elif top_style == "2d" and "anime" in learned:
                enhancements.append("2D anime style")
            else:
                enhancements.append(f"{top_style} style")

    # Step 6: Add custom instructions if set
    if prefs.get("custom_instructions"):
        enhancements.append(prefs["custom_instructions"])

    # Step 7: Basic quality enhancements (only for simple prompts)
    if len(p.split()) < 10 and not has_style:
        framing_keywords = [
            "full body", "full-body", "head to toe", "close-up", "closeup",
            "portrait", "headshot", "bust", "waist up"
        ]
        has_framing = any(keyword in p_lower for keyword in framing_keywords)

        if not has_framing:
            enhancements.append("full body view")

    # Step 8: Always prevent text unless requested
    if "text" not in p_lower and "words" not in p_lower and "title" not in p_lower and "sign" not in p_lower:
        enhancements.append("no text")

    # Build final prompt
    if enhancements:
        return f"{p}, {', '.join(enhancements)}"

    return p

def _enhance_prompt_for_full_body(p: str) -> str:
    """
    Legacy function - kept for backward compatibility.
    Use _smart_enhance_prompt instead for learning capabilities.
    """
    return _smart_enhance_prompt(p, None, None)

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
      "transparent": false,     # if true, ask for transparent background
      "user_id": "user123"      # optional: for learning patterns
    }

    Response JSON:
    {
      "ok": true,
      "items": [
         {"poster_id": "...", "url": "/api/poster/file/<id>", "filename": "poster-....png"}
      ],
      "enhanced_prompt": "...",  # shows what was sent to DALL-E
      "learned_styles": {...}    # shows detected patterns
    }

    On failure: {"ok": false, "error": "..."}
    """
    try:
        data = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400

    original_prompt = _sanitize_prompt(data.get("prompt", ""))
    if not original_prompt:
        return jsonify({"ok": False, "error": "Missing 'prompt'"}), 400

    # Get user ID for learning (optional)
    user_id = data.get("user_id")

    # Get database engine for learning
    engine = get_db_engine()

    # Smart enhancement with learning and presets
    enhanced_prompt = _smart_enhance_prompt(original_prompt, user_id, engine)

    # Get learned patterns for response
    learned_styles = _learn_from_history(user_id, engine) if user_id and engine else {}

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
            prompt=enhanced_prompt,
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
        poster_id = storage.save(b64, filename, "image/png", enhanced_prompt, size)
        out_items.append({
            "poster_id": poster_id,
            "url": f"/api/poster/file/{poster_id}",
            "filename": filename
        })

    if not out_items:
        return jsonify({"ok": False, "error": "No images returned"}), 502

    # Save to history for future learning
    if user_id and engine:
        try:
            _save_prompt_to_history(user_id, original_prompt, enhanced_prompt, engine)
        except Exception:
            current_app.logger.warning("Failed to save prompt history", exc_info=True)

    return jsonify({
        "ok": True,
        "items": out_items,
        "enhanced_prompt": enhanced_prompt,
        "learned_styles": learned_styles
    }), 200


@poster_bp.route("/preferences", methods=["GET", "POST"])
def user_preferences():
    """
    GET: Returns user's style preferences and learned patterns
    POST: Updates user's style preferences

    POST body:
    {
      "user_id": "user123",
      "default_style": "3D cartoon style",
      "auto_apply": true,
      "custom_instructions": "vibrant colors, dynamic pose"
    }
    """
    if request.method == "GET":
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "error": "Missing user_id"}), 400

        engine = get_db_engine()
        prefs = _get_user_preferences(user_id, engine)
        learned = _learn_from_history(user_id, engine)

        return jsonify({
            "ok": True,
            "preferences": prefs,
            "learned_styles": learned
        }), 200

    # POST - update preferences
    try:
        data = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "Missing user_id"}), 400

    default_style = data.get("default_style", "")
    auto_apply = data.get("auto_apply", True)
    custom_instructions = data.get("custom_instructions", "")

    engine = get_db_engine()
    if not engine:
        return jsonify({"ok": False, "error": "Database not configured"}), 500

    _, _, text = _lazy_imports()

    try:
        with engine.begin() as conn:
            # Upsert preferences
            conn.execute(
                text("""
                    INSERT INTO user_style_preferences (user_id, default_style, auto_apply, custom_instructions, updated_at)
                    VALUES (:user_id, :style, :auto, :custom, NOW())
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        default_style = :style,
                        auto_apply = :auto,
                        custom_instructions = :custom,
                        updated_at = NOW()
                """),
                {
                    "user_id": user_id,
                    "style": default_style,
                    "auto": auto_apply,
                    "custom": custom_instructions
                }
            )
    except Exception as e:
        current_app.logger.exception("Failed to save preferences")
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({"ok": True, "message": "Preferences saved"}), 200


@poster_bp.route("/edit", methods=["POST"])
def edit_poster():
    """
    Multipart form endpoint to perform DALL·E 2-style edits with a reference image.

    FORM FIELDS:
      - prompt: text prompt describing changes/style (required)
      - size: 256x256 | 512x512 | 1024x1024 (optional, default 1024x1024)
      - n: number of images (1..4, optional, default 1)
      - image: the reference image file (required) — will be converted to square PNG with alpha
      - user_id: optional user ID for learning

    Returns:
      { "ok": true, "items": [ { "poster_id": "...", "url": "/api/poster/file/<id>", "filename": "..." } ] }
    """
    try:
        prompt = _sanitize_prompt(request.form.get("prompt", ""))
        if not prompt:
            return jsonify({"ok": False, "error": "Missing 'prompt'"}), 400

        size = request.form.get("size", "1024x1024")
        if size not in _EDIT_SIZES:
            size = "1024x1024"

        try:
            n = int(request.form.get("n", "1"))
        except Exception:
            n = 1
        n = max(1, min(n, 4))

        user_id = request.form.get("user_id")

        if "image" not in request.files:
            return jsonify({"ok": False, "error": "Missing reference 'image' file"}), 400

        image_file = request.files["image"]
        try:
            processed_png = _preprocess_reference_to_square_png_alpha(image_file, size)
        except Exception as e:
            current_app.logger.exception("Preprocess failed")
            return jsonify({"ok": False, "error": f"preprocess_failed: {str(e)}"}), 400

        # Get database engine for learning
        engine = get_db_engine()

        # Smart enhancement with learning and presets
        enhanced_prompt = _smart_enhance_prompt(prompt, user_id, engine)

        try:
            items = OpenAIImagesEditClient.edit(
                prompt=enhanced_prompt,
                image_blob=processed_png,
                size=size,
                n=n,
                timeout_seconds=int(os.getenv("POSTER_TIMEOUT_SECONDS", "60")),
            )
        except Exception as e:
            error_msg = str(e)
            current_app.logger.exception(f"Edit generation failed: {error_msg}")
            return jsonify({
                "ok": False,
                "error": error_msg,
                "details": "DALL-E 2 edit failed - check server logs for details"
            }), 502

        storage = PosterStorage()
        out_items = []
        for _i, item in enumerate(items):
            b64 = item.get("b64_json")
            if not b64:
                continue
            filename = f"poster-edit-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}.png"
            poster_id = storage.save(b64, filename, "image/png", enhanced_prompt, size)
            out_items.append({
                "poster_id": poster_id,
                "url": f"/api/poster/file/{poster_id}",
                "filename": filename
            })

        if not out_items:
            return jsonify({"ok": False, "error": "No images returned"}), 502

        # Save to history for future learning
        if user_id and engine:
            try:
                _save_prompt_to_history(user_id, prompt, enhanced_prompt, engine)
            except Exception:
                current_app.logger.warning("Failed to save prompt history", exc_info=True)

        return jsonify({
            "ok": True,
            "items": out_items,
            "enhanced_prompt": enhanced_prompt,
            "model": "dall-e-2"  # Indicate it used DALL-E 2
        }), 200
    except Exception as e:
        # Catch any unexpected errors
        error_msg = f"Unexpected error: {str(e)}"
        current_app.logger.exception(error_msg)
        return jsonify({
            "ok": False,
            "error": error_msg,
            "details": "Internal server error - contact support"
        }), 500


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
