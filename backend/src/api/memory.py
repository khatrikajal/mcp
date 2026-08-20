"""
Memory API Endpoints

Provides REST endpoints for managing agent memories, semantic search,
user preferences, and conversation summaries.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from backend.src.db.connection import get_db
from backend.src.db.models import (
    User,
    AgentMemory,
    UserPreference,
    ConversationSummary,
    MemoryType,
    PreferenceCategory,
    Agent,
)
from backend.src.api.auth_utils import get_current_active_user
from backend.src.services.memory_service import MemoryService
from backend.src.services.summarization_service import (
    SummarizationService,
    PreferenceLearningService,
)

router = APIRouter(prefix="/memory", tags=["memory"])


# ==================== Schemas ====================

class MemoryTypeEnum(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    INTERACTION = "interaction"
    SUMMARY = "summary"
    MEETING = "meeting"
    EMAIL = "email"
    CONTEXT = "context"


class PreferenceCategoryEnum(str, Enum):
    SCHEDULING = "scheduling"
    COMMUNICATION = "communication"
    WORKFLOW = "workflow"
    PERSONAL = "personal"
    TOOL = "tool"


class MemoryCreate(BaseModel):
    agent_id: int
    memory_type: MemoryTypeEnum
    key: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[int] = None
    importance: float = Field(0.5, ge=0.0, le=1.0)
    expires_in_hours: Optional[int] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0.0, le=1.0)


class MemoryResponse(BaseModel):
    id: int
    agent_id: int
    user_id: int
    memory_type: str
    key: str
    content: str
    summary: Optional[str]
    source: Optional[str]
    source_id: Optional[int]
    importance: float
    access_count: int
    last_accessed: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    agent_id: int
    memory_types: Optional[List[MemoryTypeEnum]] = None
    top_k: int = Field(10, ge=1, le=50)
    threshold: float = Field(0.3, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    memory: MemoryResponse
    similarity: float


class PreferenceCreate(BaseModel):
    category: PreferenceCategoryEnum
    preference_key: str = Field(..., min_length=1, max_length=255)
    preference_value: str = Field(..., min_length=1)


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    category: str
    preference_key: str
    preference_value: str
    confidence: float
    source_type: Optional[str]
    times_confirmed: int
    times_contradicted: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationSummaryResponse(BaseModel):
    id: int
    conversation_id: int
    summary: str
    key_topics: List[str]
    key_entities: List[str]
    action_items: List[str]
    decisions: List[str]
    message_count: int
    time_range_start: Optional[datetime]
    time_range_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryStatsResponse(BaseModel):
    total_memories: int
    by_type: dict
    average_importance: float


class AgentContextResponse(BaseModel):
    memories: List[dict]
    preferences: List[dict]
    recent_topics: List[str]


# ==================== Memory Endpoints ====================

@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new memory for an agent.
    """
    # Verify agent belongs to user's organization
    agent = db.query(Agent).filter(
        Agent.id == memory_data.agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    memory_service = MemoryService(db)

    # Calculate expiration
    expires_at = None
    if memory_data.expires_in_hours:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(hours=memory_data.expires_in_hours)

    memory = await memory_service.store_memory(
        agent_id=memory_data.agent_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        memory_type=MemoryType(memory_data.memory_type.value),
        key=memory_data.key,
        content=memory_data.content,
        summary=memory_data.summary,
        source=memory_data.source,
        source_id=memory_data.source_id,
        importance=memory_data.importance,
        expires_at=expires_at,
    )

    return memory


@router.get("/agent/{agent_id}", response_model=List[MemoryResponse])
async def get_agent_memories(
    agent_id: int,
    memory_type: Optional[MemoryTypeEnum] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all memories for an agent.
    """
    # Verify agent belongs to user's organization
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    memory_service = MemoryService(db)
    memory_type_enum = MemoryType(memory_type.value) if memory_type else None

    memories = await memory_service.get_memories_by_agent(
        agent_id=agent_id,
        memory_type=memory_type_enum,
        limit=limit
    )

    return memories


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific memory by ID.
    """
    memory = db.query(AgentMemory).filter(
        AgentMemory.id == memory_id,
        AgentMemory.user_id == current_user.id
    ).first()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    return memory


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    update_data: MemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a memory.
    """
    memory = db.query(AgentMemory).filter(
        AgentMemory.id == memory_id,
        AgentMemory.user_id == current_user.id
    ).first()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    memory_service = MemoryService(db)
    updated = await memory_service.update_memory(
        memory_id=memory_id,
        content=update_data.content,
        summary=update_data.summary,
        importance=update_data.importance
    )

    return updated


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a memory.
    """
    memory = db.query(AgentMemory).filter(
        AgentMemory.id == memory_id,
        AgentMemory.user_id == current_user.id
    ).first()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    memory_service = MemoryService(db)
    await memory_service.delete_memory(memory_id)


# ==================== Search Endpoints ====================

@router.post("/search", response_model=List[MemorySearchResult])
async def search_memories(
    search_request: MemorySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Semantic search across agent memories.
    """
    # Verify agent belongs to user's organization
    agent = db.query(Agent).filter(
        Agent.id == search_request.agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    memory_service = MemoryService(db)

    memory_types = None
    if search_request.memory_types:
        memory_types = [MemoryType(mt.value) for mt in search_request.memory_types]

    results = await memory_service.search_memories(
        query=search_request.query,
        agent_id=search_request.agent_id,
        user_id=current_user.id,
        memory_types=memory_types,
        top_k=search_request.top_k,
        threshold=search_request.threshold
    )

    return [
        MemorySearchResult(
            memory=MemoryResponse.model_validate(memory),
            similarity=similarity
        )
        for memory, similarity in results
    ]


@router.get("/agent/{agent_id}/context", response_model=AgentContextResponse)
async def get_agent_context(
    agent_id: int,
    max_memories: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get context for an agent including memories and preferences.
    """
    # Verify agent belongs to user's organization
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    memory_service = MemoryService(db)
    context = await memory_service.get_agent_context(
        agent_id=agent_id,
        user_id=current_user.id,
        max_memories=max_memories
    )

    return context


@router.get("/agent/{agent_id}/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get memory statistics for an agent.
    """
    # Verify agent belongs to user's organization
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    memory_service = MemoryService(db)
    stats = await memory_service.get_memory_stats(agent_id)

    return stats


# ==================== Preference Endpoints ====================

@router.post("/preferences", response_model=PreferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_preference(
    preference_data: PreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create or update a user preference.
    """
    memory_service = MemoryService(db)

    preference = await memory_service.store_preference(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        category=PreferenceCategory(preference_data.category.value),
        preference_key=preference_data.preference_key,
        preference_value=preference_data.preference_value,
        source_type="explicit",
        confidence=0.9  # High confidence for explicit preferences
    )

    return preference


@router.get("/preferences", response_model=List[PreferenceResponse])
async def get_preferences(
    category: Optional[PreferenceCategoryEnum] = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user preferences.
    """
    memory_service = MemoryService(db)
    category_enum = PreferenceCategory(category.value) if category else None

    preferences = await memory_service.get_preferences(
        user_id=current_user.id,
        category=category_enum,
        min_confidence=min_confidence
    )

    return preferences


@router.delete("/preferences/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(
    preference_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a preference.
    """
    preference = db.query(UserPreference).filter(
        UserPreference.id == preference_id,
        UserPreference.user_id == current_user.id
    ).first()

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )

    db.delete(preference)
    db.commit()


# ==================== Summarization Endpoints ====================

@router.post("/conversations/{conversation_id}/summarize", response_model=ConversationSummaryResponse)
async def summarize_conversation(
    conversation_id: int,
    force: bool = Query(False, description="Force regeneration of existing summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a summary for a conversation.
    """
    from backend.src.db.models import Conversation

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

    summarization_service = SummarizationService(db)
    summary = await summarization_service.summarize_conversation(
        conversation_id=conversation_id,
        force=force
    )

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate summary (conversation may be too short)"
        )

    return summary


@router.get("/conversations/{conversation_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get existing summary for a conversation.
    """
    from backend.src.db.models import Conversation

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

    summary = db.query(ConversationSummary).filter(
        ConversationSummary.conversation_id == conversation_id
    ).first()

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No summary found for this conversation"
        )

    return summary


@router.get("/summaries", response_model=List[ConversationSummaryResponse])
async def get_user_summaries(
    agent_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all conversation summaries for the user.
    """
    query = db.query(ConversationSummary).filter(
        ConversationSummary.user_id == current_user.id
    )

    if agent_id:
        query = query.filter(ConversationSummary.agent_id == agent_id)

    summaries = query.order_by(ConversationSummary.created_at.desc()).limit(limit).all()

    return summaries


# ==================== Preference Learning Endpoints ====================

@router.post("/learn/conversation/{conversation_id}")
async def learn_from_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract and learn preferences from a conversation.
    """
    from backend.src.db.models import Conversation

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

    learning_service = PreferenceLearningService(db)
    results = await learning_service.process_conversation_for_learning(conversation_id)

    return results


# ==================== Cleanup Endpoints ====================

@router.post("/cleanup/expired")
async def cleanup_expired_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clean up expired memories.
    Typically called by a cron job, but can be triggered manually.
    """
    memory_service = MemoryService(db)
    count = await memory_service.cleanup_expired_memories()

    return {"deleted_count": count}
