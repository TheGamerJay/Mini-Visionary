import os
import re
import base64
from typing import Any, Dict, List, Union

from flask import Blueprint, request, jsonify, g
from auth import auth_required

bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# --- OpenAI client: support both new and legacy imports ---
_client = None
_USE_NEW_SDK = False
try:
    # New SDK (preferred)
    from openai import OpenAI  # type: ignore
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip() or None)
    _USE_NEW_SDK = True
except Exception:
    _client = None

if _client is None:
    # Legacy SDK fallback
    try:
        import openai  # type: ignore
        openai.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        _client = openai
        _USE_NEW_SDK = False
    except Exception:
        _client = None

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# ---------- Helpers ----------
_DATAURL_RE = re.compile(r"^data:image/[\w.+-]+;base64,(?P<b64>.+)$", re.IGNORECASE)

def _normalize_image_b64(val: str) -> str:
    """Return a bare base64 string (strip data URL if present)."""
    if not val:
        return ""
    m = _DATAURL_RE.match(val)
    return (m.group("b64") if m else val).strip()

def _to_multimodal_blocks(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize a message into OpenAI's multimodal content list.
    Supports:
      - {"content": "text"}
      - {"content": [{"type":"text",...}, {"type":"image_url", ...}]}
      - {"content": "text", "image_b64": "..."} OR {"content": "text", "image_url": "..."}
      - {"image_b64": "..."} with no text
    """
    blocks: List[Dict[str, Any]] = []
    content = msg.get("content")

    # If already in multimodal form
    if isinstance(content, list):
        # trust caller; ensure minimal shape
        for part in content:
            if isinstance(part, dict) and "type" in part:
                blocks.append(part)
        return blocks

    # Plain text (optional)
    if isinstance(content, str) and content:
        blocks.append({"type": "text", "text": content})

    # Extra helpers: accept either "image_b64" or "image_url" fields directly
    image_b64 = msg.get("image_b64")
    image_url = msg.get("image_url") or msg.get("image")

    if image_b64:
        b64 = _normalize_image_b64(str(image_b64))
        if b64:
            blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })

    elif image_url:
        # If it's a data URL, normalize it to a data: URL (keep as-is if already URL)
        s = str(image_url).strip()
        m = _DATAURL_RE.match(s)
        if m:
            s = f"data:image/jpeg;base64,{m.group('b64')}"
        blocks.append({
            "type": "image_url",
            "image_url": {"url": s}
        })

    # If caller used prior key "image" containing base64 directly (your legacy path)
    if "image" in msg and not image_b64 and not image_url:
        b64 = _normalize_image_b64(str(msg["image"]))
        if b64:
            blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })

    # If nothing was detected, treat as empty text
    if not blocks:
        blocks.append({"type": "text", "text": ""})

    return blocks

def _normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Coerce incoming messages into the OpenAI expected shape."""
    norm: List[Dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        if role not in ("system", "user", "assistant"):
            # skip unknown roles
            continue

        content = msg.get("content")
        if isinstance(content, list):
            # Already mm blocks
            norm.append({"role": role, "content": content})
        elif isinstance(content, str):
            # Possibly has an additional image field
            blocks = _to_multimodal_blocks(msg)
            # If we ended with a single text block and no images, compress to string (saves tokens)
            if len(blocks) == 1 and blocks[0].get("type") == "text":
                norm.append({"role": role, "content": blocks[0]["text"]})
            else:
                norm.append({"role": role, "content": blocks})
        else:
            # No content provided, still add empty text block to preserve role
            norm.append({"role": role, "content": ""})
    return norm

def _extract_usage(resp: Any) -> dict:
    """Safely extract usage info across SDK variants."""
    try:
        usage = getattr(resp, "usage", None)
        if not usage:
            return {}
        # new SDK: object with fields
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }
    except Exception:
        try:
            # legacy: a dict-like
            return dict(resp.usage or {})
        except Exception:
            return {}

# ---------- Routes ----------
@bp.post("/send")
@auth_required
def chat_send():
    """Send message to OpenAI chat with multimodal support and /poster shortcut."""
    if _client is None:
        return jsonify(ok=False, error="OpenAI not configured"), 503

    data = request.get_json() or {}
    messages = data.get("messages", [])
    model = (data.get("model") or DEFAULT_MODEL).strip()

    if not isinstance(messages, list) or not messages:
        return jsonify(ok=False, error="No messages provided"), 400

    # Normalize messages
    processed_messages = _normalize_messages(messages)

    # Find last user message (post-normalization)
    last_user_msg = next((m for m in reversed(processed_messages) if m.get("role") == "user"), None)

    # ---- /poster command (no request monkey-patching) ----
    if last_user_msg:
        last_content = last_user_msg.get("content", "")
        last_text = ""
        if isinstance(last_content, str):
            last_text = last_content.strip()
        elif isinstance(last_content, list):
            # find first text block
            for b in last_content:
                if isinstance(b, dict) and b.get("type") == "text":
                    last_text = (b.get("text") or "").strip()
                    break

        if last_text.startswith("/poster"):
            poster_prompt = last_text.replace("/poster", "", 1).strip()
            if not poster_prompt:
                return jsonify(
                    ok=True,
                    message={"role": "assistant", "content": "Please provide a description after `/poster`. For example: `/poster a majestic mountain landscape at sunset`"}
                )
            # Preferred path: call a dedicated function you expose for API usage
            try:
                # If your poster module exposes a pure function that accepts args, use it:
                from poster import generate_from_api  # you can implement this to accept (prompt, style, user_id)
                poster_data = generate_from_api(prompt=poster_prompt, style="cinematic", user_id=g.user_id)
            except Exception:
                # Fallback to your existing route-like function if needed
                try:
                    from poster import generate as generate_poster
                    # Call the view function directly; ensure it returns a Flask Response
                    rv = generate_poster()
                    poster_data = rv.get_json() if hasattr(rv, "get_json") else (rv[0].get_json() if isinstance(rv, tuple) else {})
                except Exception as e:
                    return jsonify(ok=True, message={"role": "assistant", "content": f"I couldn't generate the poster: {e}."})

            if poster_data and poster_data.get("ok"):
                poster_url = poster_data.get("url") or poster_data.get("poster_url")
                return jsonify(
                    ok=True,
                    message={
                        "role": "assistant",
                        "content": f"I've created a poster for you:\n\n**{poster_prompt}**\n\n![Generated Poster]({poster_url})"
                    },
                    poster_generated=True,
                    poster_url=poster_url
                )
            return jsonify(ok=True, message={"role": "assistant", "content": f"I'm sorry, I couldn't generate the poster. {poster_data.get('error', 'Unknown error occurred.')}"})


    # ---- Regular chat completion ----
    try:
        if _USE_NEW_SDK:
            resp = _client.chat.completions.create(
                model=model,
                messages=processed_messages,
                max_tokens=1500,
                temperature=0.7,
            )
            assistant_msg = resp.choices[0].message.content
        else:
            # legacy
            resp = _client.ChatCompletion.create(
                model=model,
                messages=processed_messages,
                max_tokens=1500,
                temperature=0.7,
            )
            assistant_msg = resp["choices"][0]["message"]["content"]

        usage = _extract_usage(resp)

        return jsonify(
            ok=True,
            message={"role": "assistant", "content": assistant_msg},
            usage=usage or None
        )
    except Exception as e:
        return jsonify(ok=False, error=f"Chat error: {str(e)}"), 500


@bp.get("/models")
def get_models():
    """Get available OpenAI models (front-end helper)."""
    return jsonify(
        ok=True,
        models=[
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": "128k"},
            {"id": "gpt-4o", "name": "GPT-4o", "context": "128k"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": "128k"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": "16k"},
        ],
        default=DEFAULT_MODEL
    )