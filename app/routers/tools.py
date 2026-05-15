from typing import Optional

from fastapi import APIRouter

from app.services.tool_service import execute_api_call, execute_search


router = APIRouter()


@router.post("/api/call")
def api_call(url: str, method: str = "GET", headers: Optional[dict] = None, data: Optional[dict] = None):
    return execute_api_call(url, method, headers, data)


@router.get("/search")
def search(query: str, num_results: int = 3):
    return execute_search(query, num_results)
