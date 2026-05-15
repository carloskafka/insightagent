from typing import Optional

from app.integrations.api_client import call_api
from app.integrations.search_client import google_search


def execute_api_call(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    data: Optional[dict] = None,
):
    return call_api(url, method, headers, data)


def execute_search(query: str, num_results: int = 3) -> dict:
    return {"results": google_search(query, num_results)}
