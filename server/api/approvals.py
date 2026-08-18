from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from server.database.connection import get_db
from server.database.models import User, ApprovalRequest, ApprovalStatus
from server.api.auth_utils import get_current_active_user
from server.services.approval_service import ApprovalService


router = APIRouter(prefix="/approvals", tags=["approvals"])


# Request/Response models
class ApprovalRequestResponse(BaseModel):
    id: int
    user_id: int
    agent_id: int
    tool_name: str
    tool_arguments: dict
    description: str
    status: str
    execution_plan_id: Optional[int]
    step_index: Optional[int]
    approved_at: Optional[str]
    approved_by_user_id: Optional[int]
    rejection_reason: Optional[str]
    expires_at: str
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, approval: ApprovalRequest):
        return cls(
            id=approval.id,
            user_id=approval.user_id,
            agent_id=approval.agent_id,
            tool_name=approval.tool_name,
            tool_arguments=approval.tool_arguments,
            description=approval.description,
            status=approval.status.value,
            execution_plan_id=approval.execution_plan_id,
            step_index=approval.step_index,
            approved_at=approval.approved_at.isoformat() if approval.approved_at else None,
            approved_by_user_id=approval.approved_by_user_id,
            rejection_reason=approval.rejection_reason,
            expires_at=approval.expires_at.isoformat(),
            created_at=approval.created_at.isoformat()
        )


class ApproveRequest(BaseModel):
    pass  # No additional data needed


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.get("", response_model=List[ApprovalRequestResponse])
def list_pending_approvals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all pending approval requests for the current user.
    """
    approval_service = ApprovalService(db)
    approvals = approval_service.get_pending_approvals(current_user.id)

    return [ApprovalRequestResponse.from_orm(approval) for approval in approvals]


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
def get_approval_request(
    approval_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific approval request by ID."""
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.user_id == current_user.id
    ).first()

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    return ApprovalRequestResponse.from_orm(approval)


@router.post("/{approval_id}/approve", response_model=ApprovalRequestResponse)
def approve_request(
    approval_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Approve an approval request.

    This will:
    1. Mark the request as approved
    2. Execute the approved action
    3. Continue the execution plan (if part of a plan)
    """
    approval_service = ApprovalService(db)

    try:
        approval = approval_service.approve_request(
            approval_id=approval_id,
            user_id=current_user.id
        )

        return ApprovalRequestResponse.from_orm(approval)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{approval_id}/reject", response_model=ApprovalRequestResponse)
def reject_request(
    approval_id: int,
    reject_data: RejectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reject an approval request.

    This will:
    1. Mark the request as rejected
    2. Cancel the execution plan (if part of a plan)
    """
    approval_service = ApprovalService(db)

    try:
        approval = approval_service.reject_request(
            approval_id=approval_id,
            user_id=current_user.id,
            reason=reject_data.reason
        )

        return ApprovalRequestResponse.from_orm(approval)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/plan/{plan_id}", response_model=List[ApprovalRequestResponse])
def get_approvals_for_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all approval requests for a specific execution plan."""
    approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.execution_plan_id == plan_id,
        ApprovalRequest.user_id == current_user.id
    ).order_by(ApprovalRequest.step_index).all()

    return [ApprovalRequestResponse.from_orm(approval) for approval in approvals]


@router.post("/expire-old")
def expire_old_approvals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually expire old approval requests.

    This is typically run as a cron job, but can be triggered manually.
    Only admin users can trigger this.
    """
    from server.database.models import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can expire approvals"
        )

    approval_service = ApprovalService(db)
    expired_count = approval_service.expire_old_requests()

    return {
        "message": f"Expired {expired_count} old approval requests",
        "count": expired_count
    }
