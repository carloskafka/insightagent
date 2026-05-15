from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import json
from datetime import timedelta

from app.config import UPLOAD_DIR, JWT_EXPIRATION_MINUTES
from app.db import init_db, get_db, User, Conversation, Message
from app.schemas import (
    UserCreate, UserLogin, UserResponse, Token, ChatRequest, ChatResponse,
    MessageResponse, ConversationResponse, UploadResponse
)
from app.auth import get_password_hash, authenticate_user, create_access_token, get_current_user
from app.adk_agent import run_agent
from app.memory import (
    get_or_create_conversation, add_message, get_conversation_history,
    get_user_conversations, delete_conversation
)
from app.rag import rag_pipeline
from app.tts import text_to_speech
from app.utils import speech_to_text
from app.rate_limit import RateLimitMiddleware

app = FastAPI(title="InsightAgent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

os.makedirs(UPLOAD_DIR, exist_ok=True)
init_db()


@app.get("/")
def root():
    return {"status": "ok", "message": "InsightAgent API is running", "model": "gemini-2.5-flash"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_data.email, hashed_password=get_password_hash(user_data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=JWT_EXPIRATION_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = get_or_create_conversation(db, current_user.id, request.conversation_id)
    add_message(db, conversation.id, "user", request.message)

    # Fetch history (exclude the message we just added)
    records = get_conversation_history(db, conversation.id, limit=10)
    history = [{"role": m.role, "content": m.content} for m in records[:-1]]

    response_text = await run_agent(
        message=request.message,
        history=history,
        session_id=f"conv_{conversation.id}",
    )

    assistant_message = add_message(db, conversation.id, "assistant", response_text)

    return ChatResponse(
        response=response_text,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
    )


@app.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_user_conversations(db, current_user.id)


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.delete("/conversations/{conversation_id}")
def delete_conv(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not delete_conversation(db, current_user.id, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


@app.post("/upload", response_model=UploadResponse)
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    try:
        text = content.decode("utf-8")
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        rag_pipeline.add_documents_batch(
            chunks,
            metadatas=[{"filename": file.filename, "user_id": current_user.id}] * len(chunks),
        )
    except Exception:
        pass
    return UploadResponse(filename=file.filename, path=file_path)


@app.post("/voice")
async def voice_message(
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    audio_data = audio.file.read()
    text = speech_to_text(audio_data)
    if not text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    conversation = get_or_create_conversation(db, current_user.id)
    add_message(db, conversation.id, "user", text)

    response_text = await run_agent(
        message=text,
        session_id=f"conv_{conversation.id}",
    )
    add_message(db, conversation.id, "assistant", response_text)

    return {"text": text, "response": response_text, "conversation_id": conversation.id}


@app.post("/tts")
def text_to_speech_endpoint(text: str, lang: str = "en"):
    audio_bytes = text_to_speech(text, lang)
    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=speech.mp3"},
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data).get("message", "")
            except json.JSONDecodeError:
                msg = data
            if msg:
                response_text = await run_agent(msg)
                await websocket.send_json({"response": response_text})
    except WebSocketDisconnect:
        pass


@app.post("/api/call")
def api_call(url: str, method: str = "GET", headers: Optional[dict] = None, data: Optional[dict] = None):
    from app.tools import call_api
    return call_api(url, method, headers, data)


@app.get("/search")
def search(query: str, num_results: int = 3):
    from app.tools import google_search
    return {"results": google_search(query, num_results)}


@app.post("/rag/add")
def add_to_rag(text: str, metadata: Optional[dict] = None, current_user: User = Depends(get_current_user)):
    doc_id = rag_pipeline.add_document(text, metadata)
    return {"doc_id": doc_id, "status": "added"}


@app.get("/rag/search")
def search_rag(query: str, top_k: int = 3, current_user: User = Depends(get_current_user)):
    return {"results": rag_pipeline.search(query, top_k)}
