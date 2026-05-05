from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db import Conversation, Message

def get_or_create_conversation(db: Session, user_id: int, conversation_id: Optional[int] = None) -> Conversation:
    """Get existing conversation or create a new one"""
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        if conversation:
            return conversation
    
    # Create new conversation
    conversation = Conversation(user_id=user_id, title=f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def add_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    """Add a message to a conversation"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Update conversation timestamp
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = datetime.utcnow()
        db.commit()
    
    return message

def get_conversation_history(db: Session, conversation_id: int, limit: int = 50) -> List[Message]:
    """Get message history for a conversation"""
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).limit(limit).all()
    return messages

def get_user_conversations(db: Session, user_id: int) -> List[Conversation]:
    """Get all conversations for a user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).all()
    return conversations

def delete_conversation(db: Session, user_id: int, conversation_id: int) -> bool:
    """Delete a conversation and its messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        return False
    
    db.delete(conversation)
    db.commit()
    return True

def update_conversation_title(db: Session, conversation_id: int, title: str) -> Optional[Conversation]:
    """Update conversation title"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.title = title
        db.commit()
        db.refresh(conversation)
    return conversation
