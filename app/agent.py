from app.tools import safe_eval
import requests
from app.config import OPENROUTER_API_KEY

def agent(query: str):
    if any(op in query for op in ["+","-","*","/"]):
        return safe_eval(query)

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role":"user","content":query}]
        }
    )

    return r.json()["choices"][0]["message"]["content"]