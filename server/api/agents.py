from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from server.database.connection import get_db
from server.database.models import User, Agent, AgentToolPermission
from server.api.schemas import AgentCreate, AgentUpdate, AgentResponse
from server.api.auth_utils import get_current_active_user

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=List[AgentResponse])
def list_agents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all agents for the current user's organization.
    """
    agents = db.query(Agent).filter(
        Agent.organization_id == current_user.organization_id
    ).all()

    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific agent by ID.
    """
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return AgentResponse.model_validate(agent)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new agent.
    """
    # Create agent
    new_agent = Agent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=agent_data.name,
        description=agent_data.description,
        system_instructions=agent_data.system_instructions
    )
    db.add(new_agent)
    db.flush()  # Get the agent ID

    # Create tool permissions if provided
    if agent_data.tool_permissions:
        for perm_data in agent_data.tool_permissions:
            permission = AgentToolPermission(
                agent_id=new_agent.id,
                tool_name=perm_data.tool_name,
                permission_level=perm_data.permission_level
            )
            db.add(permission)

    db.commit()
    db.refresh(new_agent)

    return AgentResponse.model_validate(new_agent)


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an agent.
    """
    # Find agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Update fields
    if agent_data.name is not None:
        agent.name = agent_data.name
    if agent_data.description is not None:
        agent.description = agent_data.description
    if agent_data.system_instructions is not None:
        agent.system_instructions = agent_data.system_instructions

    # Update tool permissions if provided
    if agent_data.tool_permissions is not None:
        # Delete existing permissions
        db.query(AgentToolPermission).filter(
            AgentToolPermission.agent_id == agent.id
        ).delete()

        # Create new permissions
        for perm_data in agent_data.tool_permissions:
            permission = AgentToolPermission(
                agent_id=agent.id,
                tool_name=perm_data.tool_name,
                permission_level=perm_data.permission_level
            )
            db.add(permission)

    db.commit()
    db.refresh(agent)

    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an agent.
    """
    # Find agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.organization_id == current_user.organization_id
    ).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Delete agent (cascades to tool_permissions)
    db.delete(agent)
    db.commit()

    return None
