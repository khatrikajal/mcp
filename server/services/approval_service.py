"""
Approval Service - Manages human approval gates for sensitive actions.

This service handles:
1. Creating approval requests when agents need permission
2. Approving/rejecting pending requests
3. Auto-expiring old requests
4. Executing approved actions
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from server.database.models import (
    ApprovalRequest,
    ApprovalStatus,
    User,
    Agent,
    ExecutionPlan
)


class ApprovalService:
    """Manages approval requests and executes approved actions."""

    def __init__(self, db: Session):
        self.db = db

    def create_approval_request(
        self,
        user_id: int,
        agent_id: int,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        description: str,
        execution_plan_id: Optional[int] = None,
        step_index: Optional[int] = None,
        expires_in_hours: int = 1
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            user_id: User who will approve/reject
            agent_id: Agent requesting the action
            tool_name: Name of the tool to execute
            tool_arguments: Arguments for the tool
            description: Human-readable description of the action
            execution_plan_id: Plan this approval is part of (optional)
            step_index: Step number in the plan (optional)
            expires_in_hours: Hours until request expires

        Returns:
            Created approval request
        """
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        approval = ApprovalRequest(
            user_id=user_id,
            agent_id=agent_id,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            description=description,
            execution_plan_id=execution_plan_id,
            step_index=step_index,
            status=ApprovalStatus.PENDING,
            expires_at=expires_at
        )

        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)

        return approval

    def get_approval_request(self, approval_id: int) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        return self.db.query(ApprovalRequest).filter(
            ApprovalRequest.id == approval_id
        ).first()

    def get_pending_approvals(
        self,
        user_id: int,
        execution_plan_id: Optional[int] = None
    ) -> List[ApprovalRequest]:
        """
        Get pending approval requests for a user.

        Args:
            user_id: User to get approvals for
            execution_plan_id: Filter by plan (optional)

        Returns:
            List of pending approval requests
        """
        query = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.user_id == user_id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
            ApprovalRequest.expires_at > datetime.utcnow()
        )

        if execution_plan_id:
            query = query.filter(ApprovalRequest.execution_plan_id == execution_plan_id)

        return query.order_by(ApprovalRequest.created_at.desc()).all()

    def approve_request(
        self,
        approval_id: int,
        user_id: int
    ) -> ApprovalRequest:
        """
        Approve an approval request.

        Args:
            approval_id: Approval request ID
            user_id: User approving the request

        Returns:
            Updated approval request

        Raises:
            ValueError: If approval not found or already processed
        """
        approval = self.get_approval_request(approval_id)

        if not approval:
            raise ValueError("Approval request not found")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request already {approval.status.value}")

        if approval.expires_at < datetime.utcnow():
            approval.status = ApprovalStatus.EXPIRED
            self.db.commit()
            raise ValueError("Approval request has expired")

        # Update approval status
        approval.status = ApprovalStatus.APPROVED
        approval.approved_at = datetime.utcnow()
        approval.approved_by_user_id = user_id

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def reject_request(
        self,
        approval_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Reject an approval request.

        Args:
            approval_id: Approval request ID
            user_id: User rejecting the request
            reason: Reason for rejection (optional)

        Returns:
            Updated approval request

        Raises:
            ValueError: If approval not found or already processed
        """
        approval = self.get_approval_request(approval_id)

        if not approval:
            raise ValueError("Approval request not found")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request already {approval.status.value}")

        # Update approval status
        approval.status = ApprovalStatus.REJECTED
        approval.approved_at = datetime.utcnow()
        approval.approved_by_user_id = user_id
        approval.rejection_reason = reason

        self.db.commit()
        self.db.refresh(approval)

        return approval

    def expire_old_requests(self) -> int:
        """
        Expire old pending requests that have passed their expiration time.

        Returns:
            Number of requests expired
        """
        expired_requests = self.db.query(ApprovalRequest).filter(
            ApprovalRequest.status == ApprovalStatus.PENDING,
            ApprovalRequest.expires_at <= datetime.utcnow()
        ).all()

        for approval in expired_requests:
            approval.status = ApprovalStatus.EXPIRED

        self.db.commit()

        return len(expired_requests)

    async def execute_approved_action(
        self,
        approval: ApprovalRequest
    ) -> Dict[str, Any]:
        """
        Execute an approved action.

        Args:
            approval: Approved approval request

        Returns:
            Tool execution result

        Raises:
            ValueError: If approval not approved
        """
        if approval.status != ApprovalStatus.APPROVED:
            raise ValueError("Cannot execute action - approval not granted")

        # Import MCP chat service to execute tool
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

        from client.chat_service import execute_tool

        # Execute the tool with the approved arguments
        try:
            result = await execute_tool(
                tool_name=approval.tool_name,
                arguments=approval.tool_arguments
            )
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_approval_for_step(
        self,
        execution_plan_id: int,
        step_index: int
    ) -> Optional[ApprovalRequest]:
        """
        Get approval request for a specific plan step.

        Args:
            execution_plan_id: Plan ID
            step_index: Step number

        Returns:
            Approval request if exists
        """
        return self.db.query(ApprovalRequest).filter(
            ApprovalRequest.execution_plan_id == execution_plan_id,
            ApprovalRequest.step_index == step_index
        ).first()
