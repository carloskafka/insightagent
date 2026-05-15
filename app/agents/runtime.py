import ast

from app.integrations.llm_client import get_llm_response
from app.integrations.rag_pipeline import rag_pipeline
from app.integrations.search_client import google_search


SEARCH_KEYWORDS = ("search", "find", "look up", "google")
MATH_OPERATORS = ("+", "-", "*", "/", "**", "//", "%")
SYSTEM_PROMPT = "You are a helpful AI assistant."


def agent(query: str, use_rag: bool = True, context: str = "") -> str:
    if _looks_like_api_request(query):
        return "API calling requires structured input. Please use the /api/call endpoint directly."

    math_response = _handle_math_query(query)
    if math_response is not None:
        return math_response

    search_response = _handle_search_query(query)
    if search_response is not None:
        return search_response

    rag_response = _handle_rag_query(query, use_rag=use_rag, context=context)
    if rag_response is not None:
        return rag_response

    return _generate_llm_response(query)


def _looks_like_api_request(query: str) -> bool:
    normalized_query = query.lower()
    return "call api" in normalized_query or "http" in query


def _handle_math_query(query: str) -> str | None:
    if not any(operator in query for operator in MATH_OPERATORS):
        return None

    result = _safe_eval(query)
    if result.startswith("error"):
        return None
    return f"Result: {result}"


def _handle_search_query(query: str) -> str | None:
    normalized_query = query.lower()
    if not any(keyword in normalized_query for keyword in SEARCH_KEYWORDS):
        return None

    search_query = query
    for keyword in SEARCH_KEYWORDS:
        search_query = search_query.replace(keyword, "").strip()

    results = google_search(search_query)
    if not results:
        return None

    formatted_results = "\n".join([f"- {result['title']}: {result['link']}" for result in results[:3]])
    return f"Search results:\n{formatted_results}"


def _handle_rag_query(query: str, use_rag: bool, context: str) -> str | None:
    if not use_rag or not context:
        return None

    rag_results = rag_pipeline.search(query, top_k=3)
    if not rag_results:
        return None

    context_text = "\n".join([result["text"] for result in rag_results])
    messages = [
        {"role": "system", "content": f"You are a helpful assistant. Use this context to answer:\n{context_text}"},
        {"role": "user", "content": query},
    ]
    return get_llm_response(messages)


def _generate_llm_response(query: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    return get_llm_response(messages)


def _safe_eval(expr: str) -> str:
    try:
        ast.parse(expr, mode="eval")
        return str(eval(expr))
    except Exception as exc:
        return f"error: {str(exc)}"
