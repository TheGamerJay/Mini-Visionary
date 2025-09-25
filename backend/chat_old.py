import os
import base64
from flask import Blueprint, request, jsonify, g
from auth import auth_required
import openai

bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

@bp.post("/send")
@auth_required
def chat_send():
    """Send message to OpenAI chat with multimodal support"""
    data = request.get_json() or {}
    messages = data.get("messages", [])
    model = data.get("model", DEFAULT_MODEL)

    if not messages:
        return jsonify(ok=False, error="No messages provided"), 400

    try:
        # Process messages to handle images
        processed_messages = []
        for msg in messages:
            if msg.get("role") in ["user", "assistant", "system"]:
                content = msg.get("content", "")

                # Handle multimodal content (text + images)
                if isinstance(content, list):
                    # Already in multimodal format
                    processed_messages.append({
                        "role": msg["role"],
                        "content": content
                    })
                elif isinstance(content, str):
                    # Check if this message has an associated image
                    image_data = msg.get("image")
                    if image_data:
                        # Convert to multimodal format
                        processed_messages.append({
                            "role": msg["role"],
                            "content": [
                                {"type": "text", "text": content},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        })
                    else:
                        # Text-only message
                        processed_messages.append({
                            "role": msg["role"],
                            "content": content
                        })

        # Check for /poster command in the last user message
        last_user_msg = None
        for msg in reversed(processed_messages):
            if msg["role"] == "user":
                last_user_msg = msg
                break

        # Handle /poster command
        if last_user_msg and isinstance(last_user_msg["content"], str) and last_user_msg["content"].strip().startswith("/poster"):
            poster_prompt = last_user_msg["content"].strip().replace("/poster", "").strip()
            if poster_prompt:
                # Generate poster using the poster generation system
                from poster import generate as generate_poster

                # Mock the request for poster generation
                class MockRequest:
                    def get_json(self):
                        return {"prompt": poster_prompt, "style": "cinematic"}

                # Temporarily replace the request object
                original_request = request
                try:
                    import sys
                    poster_module = sys.modules.get('poster')
                    if poster_module:
                        poster_module.request = MockRequest()

                    poster_result = generate_poster()
                    if isinstance(poster_result, tuple):
                        poster_data = poster_result[0].get_json()
                    else:
                        poster_data = poster_result.get_json()

                    if poster_data.get("ok"):
                        poster_url = poster_data.get("url")
                        return jsonify(
                            ok=True,
                            message={
                                "role": "assistant",
                                "content": f"I've created a poster for you: \"{poster_prompt}\"\n\n![Generated Poster]({poster_url})\n\nYour poster has been generated and is ready for download!"
                            },
                            poster_generated=True,
                            poster_url=poster_url
                        )
                    else:
                        return jsonify(
                            ok=True,
                            message={
                                "role": "assistant",
                                "content": f"I'm sorry, I couldn't generate the poster. {poster_data.get('error', 'Unknown error occurred.')}"
                            }
                        )
                finally:
                    if poster_module:
                        poster_module.request = original_request
            else:
                return jsonify(
                    ok=True,
                    message={
                        "role": "assistant",
                        "content": "Please provide a description after `/poster`. For example: `/poster a majestic mountain landscape at sunset`"
                    }
                )

        # Regular chat completion
        response = openai.chat.completions.create(
            model=model,
            messages=processed_messages,
            max_tokens=1500,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

        return jsonify(
            ok=True,
            message={
                "role": "assistant",
                "content": assistant_message
            },
            usage=response.usage.model_dump() if response.usage else None
        )

    except Exception as e:
        return jsonify(ok=False, error=f"Chat error: {str(e)}"), 500

@bp.get("/models")
def get_models():
    """Get available OpenAI models"""
    return jsonify(
        ok=True,
        models=[
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": "128k"},
            {"id": "gpt-4o", "name": "GPT-4o", "context": "128k"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": "128k"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context": "16k"}
        ],
        default=DEFAULT_MODEL
    )