import json

from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents import agent
from app.core.database import get_db
from app.core.security import get_current_user
from app.integrations.tts_client import text_to_speech
from app.models.entities import User
from app.schemas import ChatRequest, ChatResponse, ConversationResponse, UploadResponse
from app.services.chat_service import (
    create_chat_response,
    create_voice_response,
    delete_user_conversation,
    get_user_conversation,
    list_user_conversations,
)
from app.services.file_service import save_upload


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_chat_response(request, db, current_user)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_user_conversations(db, current_user)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_user_conversation(conversation_id, db, current_user)


@router.delete("/conversations/{conversation_id}")
def delete_conv(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_user_conversation(conversation_id, db, current_user)


@router.post("/upload", response_model=UploadResponse)
def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    return save_upload(file, current_user)


@router.post("/voice")
def voice_message(audio: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_voice_response(audio.file.read(), db, current_user)


@router.post("/tts")
def text_to_speech_endpoint(text: str, lang: str = "en"):
    audio_bytes = text_to_speech(text, lang)
    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=speech.mp3"},
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = _extract_message(data)
            if message:
                await websocket.send_json({"response": agent(message)})
    except WebSocketDisconnect:
        print("Client disconnected")


def _extract_message(data: str) -> str:
    try:
        request_data = json.loads(data)
        return request_data.get("message", "")
    except json.JSONDecodeError:
        return data
