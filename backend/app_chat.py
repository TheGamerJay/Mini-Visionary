from flask import Blueprint, request, jsonify
import os

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False

bp = Blueprint("chat", __name__, url_prefix="/api/chat")

@bp.post("")
def chat():
    if not _HAS_OPENAI:
        return jsonify(ok=False, error="openai-sdk-missing"), 500

    js = request.get_json() or {}
    model = js.get("model") or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    temperature = float(js.get("temperature", 0.7))
    system = js.get("system") or "You are a helpful assistant."
    msgs = js.get("messages") or []      # [{role, content}]
    parts = js.get("parts") or None      # optional multimodal array for last user

    built = [{"role": "system", "content": system}]
    for i, m in enumerate(msgs):
        if i == len(msgs) - 1 and m.get("role") == "user" and parts:
            built.append({"role": "user", "content": parts})
        else:
            built.append({"role": m.get("role"), "content": m.get("content", "")})
    built = built[-30:]

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Chat completions supports arrays for images on recent models
        resp = client.chat.completions.create(model=model, temperature=temperature, messages=built)
        text = resp.choices[0].message.content or ""
        return jsonify(ok=True, message=text)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500