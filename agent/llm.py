import backoff
import os
from typing import Tuple
import requests
import litellm
from dotenv import load_dotenv
import json

load_dotenv()

MAX_TOKENS = 16384

# ============================================================
# Sovereign Core — Local Qwen2.5-32B-AWQ Integration
# All model calls route to localhost:8001 via litellm's
# OpenAI-compatible endpoint support.
#
# Set in .env:
#   OPENAI_API_KEY=not-needed
#   OPENAI_API_BASE=http://localhost:8001/v1
# ============================================================

SOVEREIGN_MODEL = "openai/qwen2.5-32b-awq"
SOVEREIGN_FAST_MODEL = "openai/qwen2.5-32b-awq"

# Backward-compatible aliases — existing code references these
CLAUDE_MODEL = SOVEREIGN_MODEL
CLAUDE_HAIKU_MODEL = SOVEREIGN_FAST_MODEL
CLAUDE_35NEW_MODEL = SOVEREIGN_MODEL
OPENAI_MODEL = SOVEREIGN_MODEL
OPENAI_MINI_MODEL = SOVEREIGN_FAST_MODEL
OPENAI_O3_MODEL = SOVEREIGN_MODEL
OPENAI_O3MINI_MODEL = SOVEREIGN_FAST_MODEL
OPENAI_O4MINI_MODEL = SOVEREIGN_FAST_MODEL
OPENAI_GPT52_MODEL = SOVEREIGN_MODEL
OPENAI_GPT5_MODEL = SOVEREIGN_MODEL
OPENAI_GPT5MINI_MODEL = SOVEREIGN_FAST_MODEL
GEMINI_3_MODEL = SOVEREIGN_MODEL
GEMINI_MODEL = SOVEREIGN_MODEL
GEMINI_FLASH_MODEL = SOVEREIGN_FAST_MODEL

litellm.drop_params=True

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, json.JSONDecodeError, KeyError),
    max_time=600,
    max_value=60,
)
def get_response_from_llm(
    msg: str,
    model: str = SOVEREIGN_MODEL,
    temperature: float = 0.0,
    max_tokens: int = MAX_TOKENS,
    msg_history=None,
) -> Tuple[str, list, dict]:
    if msg_history is None:
        msg_history = []

    # Convert text to content, compatible with LITELLM API
    msg_history = [
        {**msg, "content": msg.pop("text")} if "text" in msg else msg
        for msg in msg_history
    ]

    new_msg_history = msg_history + [{"role": "user", "content": msg}]

    # Build kwargs — simplified for local Qwen2.5 endpoint
    completion_kwargs = {
        "model": model,
        "messages": new_msg_history,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = litellm.completion(**completion_kwargs)
    response_text = response['choices'][0]['message']['content']  # pyright: ignore
    new_msg_history.append({"role": "assistant", "content": response['choices'][0]['message']['content']})

    # Convert content to text, compatible with MetaGen API
    new_msg_history = [
        {**msg, "text": msg.pop("content")} if "content" in msg else msg
        for msg in new_msg_history
    ]

    return response_text, new_msg_history, {}


if __name__ == "__main__":
    msg = 'Hello there!'
    print(f"Testing SOVEREIGN_MODEL: {SOVEREIGN_MODEL}")
    try:
        output_msg, msg_history, info = get_response_from_llm(msg, model=SOVEREIGN_MODEL)
        print(f"OK: {output_msg[:100]}...")
    except Exception as e:
        print(f"FAIL: {str(e)[:200]}")
