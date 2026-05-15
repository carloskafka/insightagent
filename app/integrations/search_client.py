import requests

from app.core.config import GOOGLE_CX, GOOGLE_SEARCH_API_KEY


def google_search(query: str, num_results: int = 3) -> list:
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CX:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": min(num_results, 10),
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        return [
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in results.get("items", [])
        ]
    except Exception as exc:
        print(f"Google search error: {exc}")
        return []
