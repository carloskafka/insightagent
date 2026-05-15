import ast
import requests
from typing import Optional, Dict, Any
from app.config import GOOGLE_SEARCH_API_KEY, GOOGLE_CX


# ── ADK tools (used by the Gemini agent) ────────────────────────────────────

def web_search(query: str) -> str:
    """Search the web for current information about a topic or question.

    Args:
        query: The search query string.

    Returns:
        Formatted search results with titles and snippets.
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CX:
        return "Web search is not configured (missing GOOGLE_SEARCH_API_KEY / GOOGLE_CX)."
    try:
        params = {"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_CX, "q": query, "num": 3}
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            return f"No results found for: {query}"
        return "\n".join(f"- {i['title']}: {i.get('snippet', '')}" for i in items)
    except Exception as e:
        return f"Search error: {e}"


def safe_calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: A math expression such as "2 + 2", "15% of 2500", or "2 ** 10".

    Returns:
        The computed result as a string.
    """
    expr = expression.replace("%", "/100").replace(" of ", "*")
    try:
        allowed = (
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
            ast.Mod, ast.FloorDiv, ast.USub, ast.UAdd,
        )
        tree = ast.parse(expr, mode="eval")
        if not all(isinstance(n, allowed) for n in ast.walk(tree)):
            return "Invalid expression."
        return str(eval(compile(tree, "<string>", "eval")))
    except Exception:
        return "Could not evaluate that expression."


def search_documents_rag(query: str) -> str:
    """Search through the user's uploaded documents for relevant information.

    Args:
        query: The topic or question to look up in the uploaded documents.

    Returns:
        Relevant excerpts from uploaded documents.
    """
    try:
        from app.rag import rag_pipeline
        results = rag_pipeline.search(query, top_k=3)
        if not results:
            return "No relevant content found in uploaded documents."
        return "\n\n".join(r.get("text", "") for r in results if r.get("text"))
    except Exception as e:
        return f"Document search error: {e}"


# ── Legacy helpers (kept for /search and /api/call REST endpoints) ───────────

def google_search(query: str, num_results: int = 3) -> list:
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CX:
        return []
    try:
        params = {"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_CX, "q": query, "num": min(num_results, 10)}
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        resp.raise_for_status()
        return [
            {"title": i.get("title", ""), "link": i.get("link", ""), "snippet": i.get("snippet", "")}
            for i in resp.json().get("items", [])
        ]
    except Exception as e:
        print(f"Google search error: {e}")
        return []


def safe_eval(expr: str) -> str:
    return safe_calculate(expr)


def call_api(url: str, method: str = "GET", headers: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
    try:
        m = method.upper()
        if m == "GET":
            resp = requests.get(url, headers=headers, params=data)
        elif m == "POST":
            resp = requests.post(url, headers=headers, json=data)
        elif m == "PUT":
            resp = requests.put(url, headers=headers, json=data)
        elif m == "DELETE":
            resp = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
