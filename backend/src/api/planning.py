from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.src.db.connection import get_db
from backend.src.db.models import User, ExecutionPlan, ApprovalRequest
from backend.src.api.auth_utils import get_current_active_user
from backend.src.services.planning_service import PlanningService
from backend.src.services.approval_service import ApprovalService


router = APIRouter(prefix="/planning", tags=["planning"])


# Request/Response models
class CreatePlanRequest(BaseModel):
    conversation_id: int
    agent_id: int
    user_request: str


class PlanStepResponse(BaseModel):
    step_number: int
    description: str
    tool: str
    arguments: dict
    requires_approval: bool
    status: Optional[str] = None
    result: Optional[dict] = None


class ExecutionPlanResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    agent_id: int
    user_request: str
    status: str
    current_step: int
    plan: List[dict]
    step_results: List[dict]
    final_result: Optional[str]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, plan: ExecutionPlan):
        return cls(
            id=plan.id,
            conversation_id=plan.conversation_id,
            user_id=plan.user_id,
            agent_id=plan.agent_id,
            user_request=plan.user_request,
            status=plan.status.value,
            current_step=plan.current_step,
            plan=plan.plan_data.get("plan", []),
            step_results=plan.plan_data.get("step_results", []),
            final_result=plan.final_result,
            error_message=plan.error_message,
            created_at=plan.created_at.isoformat(),
            started_at=plan.started_at.isoformat() if plan.started_at else None,
            completed_at=plan.completed_at.isoformat() if plan.completed_at else None
        )


@router.post("", response_model=ExecutionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_execution_plan(
    plan_request: CreatePlanRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create and execute a planning workflow.

    This will:
    1. Analyze the user request
    2. Create a step-by-step plan
    3. Validate tool permissions
    4. Begin execution (will pause at approval gates)
    """
    try:
        planning_service = PlanningService(db)

        execution_plan = await planning_service.execute_planning_workflow(
            conversation_id=plan_request.conversation_id,
            user_id=current_user.id,
            agent_id=plan_request.agent_id,
            user_request=plan_request.user_request
        )

        return ExecutionPlanResponse.from_orm(execution_plan)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create execution plan: {str(e)}"
        )


@router.get("/{plan_id}", response_model=ExecutionPlanResponse)
def get_execution_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get execution plan by ID."""
    plan = db.query(ExecutionPlan).filter(
        ExecutionPlan.id == plan_id,
        ExecutionPlan.user_id == current_user.id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution plan not found"
        )

    return ExecutionPlanResponse.from_orm(plan)


@router.get("/conversation/{conversation_id}", response_model=List[ExecutionPlanResponse])
def get_plans_for_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all execution plans for a conversation."""
    plans = db.query(ExecutionPlan).filter(
        ExecutionPlan.conversation_id == conversation_id,
        ExecutionPlan.user_id == current_user.id
    ).order_by(ExecutionPlan.created_at.desc()).all()

    return [ExecutionPlanResponse.from_orm(plan) for plan in plans]


@router.post("/{plan_id}/resume")
async def resume_execution_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Resume a paused execution plan.

    This is used after approvals are granted to continue execution.
    """
    # This would continue the LangGraph workflow
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Plan resumption not yet implemented"
    )


@router.post("/{plan_id}/cancel")
def cancel_execution_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a running or paused execution plan."""
    plan = db.query(ExecutionPlan).filter(
        ExecutionPlan.id == plan_id,
        ExecutionPlan.user_id == current_user.id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution plan not found"
        )

    from backend.src.db.models import PlanStatus

    if plan.status in [PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel plan with status: {plan.status.value}"
        )

    plan.status = PlanStatus.CANCELLED
    db.commit()

    return {"message": "Execution plan cancelled successfully"}
