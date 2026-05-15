from typing import Optional

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.entities import User
from app.services.rag_service import add_document, search_documents


router = APIRouter()


@router.post("/rag/add")
def add_to_rag(text: str, metadata: Optional[dict] = None, current_user: User = Depends(get_current_user)):
    return add_document(text, metadata)


@router.get("/rag/search")
def search_rag(query: str, top_k: int = 3, current_user: User = Depends(get_current_user)):
    return search_documents(query, top_k)
