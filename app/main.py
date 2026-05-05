
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
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
from app.auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user
)
from app.agent import agent
from app.memory import (
    get_or_create_conversation, add_message, get_conversation_history,
    get_user_conversations, delete_conversation
)
from app.rag import rag_pipeline
from app.tts import text_to_speech
from app.utils import speech_to_text
from app.rate_limit import RateLimitMiddleware

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Create upload directory
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize database
init_db()

# Health check
@app.get("/")
def root():
    return {"status": "ok", "message": "Chatbot API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Auth endpoints
@app.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=JWT_EXPIRATION_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = get_or_create_conversation(db, current_user.id, request.conversation_id)
    
    # Add user message
    user_message = add_message(db, conversation.id, "user", request.message)
    
    # Get conversation history for context
    history = get_conversation_history(db, conversation.id, limit=10)
    messages = [{"role": m.role, "content": m.content} for m in history]
    
    # Get agent response
    response_text = agent(request.message)
    
    # Add assistant message
    assistant_message = add_message(db, conversation.id, "assistant", response_text)
    
    return ChatResponse(
        response=response_text,
        conversation_id=conversation.id,
        message_id=assistant_message.id
    )

@app.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversations = get_user_conversations(db, current_user.id)
    return conversations

@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation

@app.delete("/conversations/{conversation_id}")
def delete_conv(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = delete_conversation(db, current_user.id, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

# Upload endpoint
@app.post("/upload", response_model=UploadResponse)
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Process file for RAG
    try:
        text_content = content.decode('utf-8')
        # Simple chunking by paragraphs
        chunks = [chunk.strip() for chunk in text_content.split('\n\n') if chunk.strip()]
        rag_pipeline.add_documents_batch(chunks, metadatas=[{"filename": file.filename, "user_id": current_user.id}] * len(chunks))
    except:
        pass  # Binary files or non-text files
    
    return UploadResponse(filename=file.filename, path=file_path)

# Voice endpoints
@app.post("/voice")
def voice_message(audio: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    audio_data = audio.file.read()
    text = speech_to_text(audio_data)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
    
    conversation = get_or_create_conversation(db, current_user.id)
    add_message(db, conversation.id, "user", text)
    
    response_text = agent(text)
    add_message(db, conversation.id, "assistant", response_text)
    
    return {"text": text, "response": response_text, "conversation_id": conversation.id}

@app.post("/tts")
def text_to_speech_endpoint(text: str, lang: str = "en"):
    audio_bytes = text_to_speech(text, lang)
    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=speech.mp3"}
    )

# WebSocket for real-time chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                request_data = json.loads(data)
                message = request_data.get("message", "")
                
                if message:
                    response_text = agent(message)
                    await websocket.send_json({"response": response_text})
            except json.JSONDecodeError:
                response_text = agent(data)
                await websocket.send_json({"response": response_text})
    
    except WebSocketDisconnect:
        print("Client disconnected")

# API call endpoint
@app.post("/api/call")
def api_call(url: str, method: str = "GET", headers: Optional[dict] = None, data: Optional[dict] = None):
    from app.tools import call_api
    result = call_api(url, method, headers, data)
    return result

# Search endpoint
@app.get("/search")
def search(query: str, num_results: int = 3):
    from app.tools import google_search
    results = google_search(query, num_results)
    return {"results": results}

# RAG endpoints
@app.post("/rag/add")
def add_to_rag(text: str, metadata: Optional[dict] = None, current_user: User = Depends(get_current_user)):
    doc_id = rag_pipeline.add_document(text, metadata)
    return {"doc_id": doc_id, "status": "added"}

@app.get("/rag/search")
def search_rag(query: str, top_k: int = 3, current_user: User = Depends(get_current_user)):
    results = rag_pipeline.search(query, top_k)
    return {"results": results}
