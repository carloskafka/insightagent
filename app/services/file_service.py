import os

from app.core.config import UPLOAD_DIR
from app.integrations.rag_pipeline import rag_pipeline
from app.models.entities import User
from app.schemas import UploadResponse


def ensure_upload_dir() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload(file, current_user: User) -> UploadResponse:
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)

    _index_text_file(file.filename, content, current_user.id)
    return UploadResponse(filename=file.filename, path=file_path)


def _index_text_file(filename: str, content: bytes, user_id: int) -> None:
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        return

    chunks = [chunk.strip() for chunk in text_content.split("\n\n") if chunk.strip()]
    if not chunks:
        return

    rag_pipeline.add_documents_batch(
        chunks,
        metadatas=[{"filename": filename, "user_id": user_id}] * len(chunks),
    )
