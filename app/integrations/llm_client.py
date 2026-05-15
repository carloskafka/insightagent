import requests
from typing import Generator

from app.core.config import OPENROUTER_API_KEY


def _build_headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Chatbot",
    }


def stream_llm_response(
    messages: list,
    model: str = "mistralai/mistral-7b-instruct:free",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> Generator[str, None, None]:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    response = requests.post(url, headers=_build_headers(), json=payload, stream=True)
    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            import json

            parsed = json.loads(data)
            delta = parsed.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield content
        except Exception:
            continue


def get_llm_response(
    messages: list,
    model: str = "mistralai/mistral-7b-instruct:free",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(url, headers=_build_headers(), json=payload)
    response.raise_for_status()

    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
