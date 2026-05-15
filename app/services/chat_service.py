from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents import agent
from app.integrations.speech_client import speech_to_text
from app.models.entities import Conversation, User
from app.repositories.conversation_repository import (
    add_message,
    delete_conversation,
    get_or_create_conversation,
    get_user_conversations,
)
from app.schemas import ChatRequest, ChatResponse


def create_chat_response(request: ChatRequest, db: Session, current_user: User) -> ChatResponse:
    conversation = get_or_create_conversation(db, current_user.id, request.conversation_id)
    add_message(db, conversation.id, "user", request.message)
    response_text = agent(request.message)
    assistant_message = add_message(db, conversation.id, "assistant", response_text)
    return ChatResponse(
        response=response_text,
        conversation_id=conversation.id,
        message_id=assistant_message.id,
    )


def list_user_conversations(db: Session, current_user: User):
    return get_user_conversations(db, current_user.id)


def get_user_conversation(conversation_id: int, db: Session, current_user: User):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def delete_user_conversation(conversation_id: int, db: Session, current_user: User) -> dict:
    success = delete_conversation(db, current_user.id, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


def create_voice_response(audio_data: bytes, db: Session, current_user: User) -> dict:
    text = speech_to_text(audio_data)
    if not text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")

    conversation = get_or_create_conversation(db, current_user.id)
    add_message(db, conversation.id, "user", text)
    response_text = agent(text)
    add_message(db, conversation.id, "assistant", response_text)
    return {"text": text, "response": response_text, "conversation_id": conversation.id}
