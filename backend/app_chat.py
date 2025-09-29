from flask import Blueprint, request, jsonify
import os

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

bp = Blueprint("chat", __name__, url_prefix="/api/chat")

def _normalize_parts(parts):
    """Ensure content array matches OpenAI's expected schema."""
    norm = []
    for p in parts:
        t = (p or {}).get("type")
        if t == "text":
            txt = p.get("text", "")
            if txt:
                norm.append({"type": "text", "text": txt})
        elif t == "image_url":
            # accept either {image_url: "<url>"} or {image_url: {"url": "<url>"}}
            iu = p.get("image_url")
            if isinstance(iu, str):
                norm.append({"type": "image_url", "image_url": {"url": iu}})
            elif isinstance(iu, dict) and iu.get("url"):
                norm.append({"type": "image_url", "image_url": {"url": iu["url"]}})
        # ignore unknown types silently
    return norm

@bp.post("")
def chat():
    if not _HAS_OPENAI:
        return jsonify(ok=False, error="openai-sdk-missing"), 500
    if not os.getenv("OPENAI_API_KEY"):
        return jsonify(ok=False, error="openai_api_key_missing"), 500

    js = request.get_json(silent=True) or {}
    model = js.get("model") or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    try:
        temperature = float(js.get("temperature", 0.7))
    except Exception:
        temperature = 0.7
    temperature = max(0.0, min(1.0, temperature))

    system = js.get("system") or "You are a helpful assistant."
    msgs = js.get("messages") or []          # list[{role, content}]
    parts = js.get("parts") or None          # optional multimodal array for last user

    # Build message list; enforce max history
    built = [{"role": "system", "content": system}]
    for i, m in enumerate(msgs[-29:]):       # keep recent 29 + system = 30
        role = m.get("role")
        content = m.get("content", "")
        is_last_user = (i == len(msgs[-29:]) - 1 and role == "user" and parts)

        if is_last_user:
            content_array = _normalize_parts(parts)
            if not content_array:
                # fall back to plain text if parts invalid/empty
                content_array = [{"type": "text", "text": str(content)}]
            built.append({"role": "user", "content": content_array})
        else:
            built.append({"role": role, "content": content})

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=built,
        )
        text = (resp.choices[0].message.content or "").strip()
        return jsonify(ok=True, message=text), 200
    except Exception as e:
        # You can log e for debugging
        return jsonify(ok=False, error="chat_generation_failed"), 502