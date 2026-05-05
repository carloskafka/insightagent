from app.tools import safe_eval, google_search, call_api
from app.llm import get_llm_response
from app.rag import rag_pipeline
import requests
from app.config import OPENROUTER_API_KEY

def agent(query: str, use_rag: bool = True, context: str = "") -> str:
    """
    Intelligent agent that decides which tool to use based on the query.
    Supports: math calculations, Google Search, API calls, RAG, and general LLM queries.
    """
    
    # Check for mathematical expressions
    if any(op in query for op in ["+", "-", "*", "/", "**", "//", "%"]):
        result = safe_eval(query)
        if result != "error":
            return f"Result: {result}"
    
    # Check for search intent
    search_keywords = ["search", "find", "look up", "google"]
    if any(keyword in query.lower() for keyword in search_keywords):
        search_query = query
        for keyword in search_keywords:
            search_query = search_query.replace(keyword, "").strip()
        
        results = google_search(search_query)
        if results:
            formatted_results = "\n".join([f"- {r['title']}: {r['link']}" for r in results[:3]])
            return f"Search results:\n{formatted_results}"
    
    # Check for API call intent
    if "call api" in query.lower() or "http" in query:
        # Extract URL and method from query (simplified)
        return "API calling requires structured input. Please use the /api/call endpoint directly."
    
    # Use RAG if enabled and context is available
    if use_rag and context:
        rag_results = rag_pipeline.search(query, top_k=3)
        if rag_results:
            context_text = "\n".join([r["text"] for r in rag_results])
            messages = [
                {"role": "system", "content": f"You are a helpful assistant. Use this context to answer:\n{context_text}"},
                {"role": "user", "content": query}
            ]
            return get_llm_response(messages)
    
    # Default: use LLM directly
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": query}
    ]
    
    return get_llm_response(messages)