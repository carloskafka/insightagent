import ast
from typing import Optional, Dict, Any
import requests
from app.config import GOOGLE_SEARCH_API_KEY, GOOGLE_CX

def safe_eval(expr: str) -> str:
    """Safely evaluate mathematical expressions"""
    try:
        tree = ast.parse(expr, mode="eval")
        return str(eval(expr))
    except Exception as e:
        return f"error: {str(e)}"

def google_search(query: str, num_results: int = 3) -> list:
    """Search Google using Custom Search API"""
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CX:
        return []
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": min(num_results, 10)
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        
        return [
            {"title": item.get("title", ""), "link": item.get("link", ""), "snippet": item.get("snippet", "")}
            for item in results.get("items", [])
        ]
    except Exception as e:
        print(f"Google search error: {e}")
        return []

def call_api(url: str, method: str = "GET", headers: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
    """Generic API caller"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}