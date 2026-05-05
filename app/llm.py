import requests
from typing import Generator, Optional
from app.config import OPENROUTER_API_KEY

def stream_llm_response(
    messages: list,
    model: str = "mistralai/mistral-7b-instruct:free",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> Generator[str, None, None]:
    """Stream LLM response via OpenRouter API"""
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Chatbot"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }
    
    response = requests.post(url, headers=headers, json=payload, stream=True)
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    break
                try:
                    import json
                    parsed = json.loads(data)
                    delta = parsed.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        yield content
                except:
                    continue

def get_llm_response(
    messages: list,
    model: str = "mistralai/mistral-7b-instruct:free",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """Get non-streamed LLM response via OpenRouter API"""
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Chatbot"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    return result.get('choices', [{}])[0].get('message', {}).get('content', '')
