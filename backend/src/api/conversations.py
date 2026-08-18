"""
Conversation API endpoints.

Provides CRUD operations for conversations and messages.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from backend.src.db.connection import get_db
from backend.src.db.models import User, Conversation, Message, Agent
from backend.src.api.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from backend.src.api.auth_utils import get_current_active_user
from backend.src.core.database import ResourceFetcher
from backend.src.core.exceptions import NotFoundError, ForbiddenError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_fetcher(db: Session) -> ResourceFetcher[Conversation]:
    """Create a Conversation resource fetcher."""
    return ResourceFetcher(db, Conversation, "Conversation")


def get_agent_fetcher(db: Session) -> ResourceFetcher[Agent]:
    """Create an Agent resource fetcher."""
    return ResourceFetcher(db, Agent, "Agent")


def _verify_conversation_access(
    db: Session,
    conversation_id: int,
    user_id: int
) -> Conversation:
    """
    Verify user has access to conversation.

    Args:
        db: Database session
        conversation_id: Conversation ID
        user_id: User ID

    Returns:
        Conversation if accessible

    Raises:
        HTTPException: If not found or access denied
    """
    fetcher = get_conversation_fetcher(db)

    try:
        return fetcher.get_for_user(conversation_id, user_id)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    agent_id: Optional[int] = None,
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

    logger.info(f"User {current_user.id} listed {len(conversations)} conversations")
    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation by ID."""
    conversation = _verify_conversation_access(db, conversation_id, current_user.id)
    return ConversationResponse.model_validate(conversation)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    # Verify agent belongs to user's organization
    agent_fetcher = get_agent_fetcher(db)

    try:
        agent = agent_fetcher.get_for_organization(
            conversation_data.agent_id,
            current_user.organization_id
        )
    except (NotFoundError, ForbiddenError):
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

    logger.info(f"User {current_user.id} created conversation {new_conversation.id}")
    return ConversationResponse.model_validate(new_conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its messages."""
    conversation = _verify_conversation_access(db, conversation_id, current_user.id)

    db.delete(conversation)
    db.commit()

    logger.info(f"User {current_user.id} deleted conversation {conversation_id}")
    return None


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a conversation."""
    _verify_conversation_access(db, conversation_id, current_user.id)

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
    """Send a message in a conversation and get AI response."""
    conversation = _verify_conversation_access(db, conversation_id, current_user.id)

    # Get agent with permissions
    agent = db.query(Agent).filter(Agent.id == conversation.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Process message with agent
    try:
        from backend.src.services.agent_executor import AgentExecutor

        executor = AgentExecutor(agent, db)
        ai_response = await executor.process_message(conversation_id, message_data.content)
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        ai_response = f"I encountered an error processing your request: {str(e)}"

    # Save AI response
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response
    )
    db.add(assistant_message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assistant_message)

    logger.info(f"User {current_user.id} sent message in conversation {conversation_id}")
    return MessageResponse.model_validate(assistant_message)
