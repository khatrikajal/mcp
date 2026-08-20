"""
Agent API endpoints.

Provides CRUD operations for AI agents with organization-scoped access.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
import logging

from backend.src.db.connection import get_db
from backend.src.db.models import User, Agent, AgentToolPermission, Conversation, Message
from backend.src.api.schemas import AgentCreate, AgentUpdate, AgentResponse
from backend.src.api.auth_utils import get_current_active_user
from backend.src.core.database import ResourceFetcher
from backend.src.core.exceptions import NotFoundError, ForbiddenError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


def get_agent_fetcher(db: Session) -> ResourceFetcher[Agent]:
    """Create an Agent resource fetcher."""
    return ResourceFetcher(db, Agent, "Agent")


@router.get("", response_model=List[AgentResponse])
def list_agents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all agents for the current user's organization."""
    fetcher = get_agent_fetcher(db)
    agents = fetcher.list_for_organization(current_user.organization_id)

    logger.info(f"User {current_user.id} listed {len(agents)} agents")
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific agent by ID."""
    fetcher = get_agent_fetcher(db)

    try:
        agent = fetcher.get_for_user_and_org(
            agent_id,
            current_user.id,
            current_user.organization_id
        )
        return AgentResponse.model_validate(agent)
    except (NotFoundError, ForbiddenError) as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    new_agent = Agent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=agent_data.name,
        description=agent_data.description,
        system_instructions=agent_data.system_instructions
    )
    db.add(new_agent)
    db.flush()

    # Create tool permissions if provided
    _create_tool_permissions(db, new_agent.id, agent_data.tool_permissions)

    db.commit()
    db.refresh(new_agent)

    logger.info(f"User {current_user.id} created agent {new_agent.id}")
    return AgentResponse.model_validate(new_agent)


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an agent."""
    fetcher = get_agent_fetcher(db)

    try:
        agent = fetcher.get_for_user_and_org(
            agent_id,
            current_user.id,
            current_user.organization_id
        )
    except (NotFoundError, ForbiddenError) as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Update fields using dict comprehension
    update_fields = {
        'name': agent_data.name,
        'description': agent_data.description,
        'system_instructions': agent_data.system_instructions
    }

    for field, value in update_fields.items():
        if value is not None:
            setattr(agent, field, value)

    # Update tool permissions if provided
    if agent_data.tool_permissions is not None:
        _update_tool_permissions(db, agent.id, agent_data.tool_permissions)

    db.commit()
    db.refresh(agent)

    logger.info(f"User {current_user.id} updated agent {agent_id}")
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an agent and all related records."""
    fetcher = get_agent_fetcher(db)

    try:
        agent = fetcher.get_for_user_and_org(
            agent_id,
            current_user.id,
            current_user.organization_id
        )
    except (NotFoundError, ForbiddenError) as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Delete related records in order (manual cascade for DB compatibility)
    # 1. Delete messages from all agent's conversations
    conversation_ids = [c.id for c in db.query(Conversation).filter(Conversation.agent_id == agent_id).all()]
    if conversation_ids:
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)

    # 2. Delete conversations
    db.query(Conversation).filter(Conversation.agent_id == agent_id).delete(synchronize_session=False)

    # 3. Delete tool permissions
    db.query(AgentToolPermission).filter(AgentToolPermission.agent_id == agent_id).delete(synchronize_session=False)

    # 4. Delete the agent
    db.delete(agent)
    db.commit()

    logger.info(f"User {current_user.id} deleted agent {agent_id}")
    return None


# =============================================================================
# Helper Functions
# =============================================================================

def _create_tool_permissions(
    db: Session,
    agent_id: int,
    permissions: list
) -> None:
    """Create tool permissions for an agent."""
    if not permissions:
        return

    for perm_data in permissions:
        permission = AgentToolPermission(
            agent_id=agent_id,
            tool_name=perm_data.tool_name,
            permission_level=perm_data.permission_level
        )
        db.add(permission)


def _update_tool_permissions(
    db: Session,
    agent_id: int,
    permissions: list
) -> None:
    """Replace all tool permissions for an agent."""
    # Delete existing permissions
    db.query(AgentToolPermission).filter(
        AgentToolPermission.agent_id == agent_id
    ).delete()

    # Create new permissions
    _create_tool_permissions(db, agent_id, permissions)
