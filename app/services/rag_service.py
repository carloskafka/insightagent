from app.integrations.rag_pipeline import rag_pipeline


def add_document(text: str, metadata: dict | None = None) -> dict:
    doc_id = rag_pipeline.add_document(text, metadata)
    return {"doc_id": doc_id, "status": "added"}


def search_documents(query: str, top_k: int = 3) -> dict:
    return {"results": rag_pipeline.search(query, top_k)}
