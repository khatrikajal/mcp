from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from server.database.connection import get_db
from server.database.models import User, Conversation, Message, Agent
from server.api.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from server.api.auth_utils import get_current_active_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    agent_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all conversations for the current user.
    Optionally filter by agent_id.
    """
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)

    if agent_id:
        query = query.filter(Conversation.agent_id == agent_id)

    conversations = query.order_by(Conversation.updated_at.desc()).all()
    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation by ID.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return ConversationResponse.model_validate(conversation)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    """
    # Verify agent belongs to user's organization
    agent = db.query(Agent).filter(
        Agent.id == conversation_data.agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not accessible"
        )

    # Create conversation
    new_conversation = Conversation(
        user_id=current_user.id,
        agent_id=conversation_data.agent_id,
        title=conversation_data.title or f"Chat with {agent.name}"
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    return ConversationResponse.model_validate(new_conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()
    return None


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a conversation.
    """
    # Verify conversation belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return [MessageResponse.model_validate(msg) for msg in messages]


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in a conversation and get AI response.
    """
    # Verify conversation belongs to user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get agent with permissions
    agent = db.query(Agent).filter(Agent.id == conversation.agent_id).first()

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Process message with agent (import here to avoid circular dependency)
    from server.services.agent_executor import AgentExecutor

    executor = AgentExecutor(agent, db)
    ai_response = await executor.process_message(conversation_id, message_data.content)

    # Save AI response
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response
    )
    db.add(assistant_message)

    # Update conversation timestamp
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assistant_message)

    return MessageResponse.model_validate(assistant_message)
