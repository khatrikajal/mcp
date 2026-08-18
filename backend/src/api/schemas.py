"""
Pydantic schemas for API request/response validation.

All schemas include:
- Field length limits
- Pattern validation where appropriate
- Clear error messages
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from backend.src.db.models import (
    UserRole,
    PermissionLevel,
    PlanStatus,
    StepStatus,
    ApprovalStatus
)


# =============================================================================
# Validation Constants
# =============================================================================

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_NAME_LENGTH = 100
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_CONTENT_LENGTH = 50000
MAX_INSTRUCTIONS_LENGTH = 10000


# =============================================================================
# Validators
# =============================================================================

def validate_no_html(value: str) -> str:
    """Strip HTML tags from input."""
    if not value:
        return value
    return re.sub(r'<[^>]+>', '', value)


def validate_name(value: str) -> str:
    """Validate name field."""
    if not value or not value.strip():
        raise ValueError("Name cannot be empty")
    cleaned = value.strip()
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be less than {MAX_NAME_LENGTH} characters")
    return cleaned


def validate_password(value: str) -> str:
    """Validate password strength."""
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be less than {MAX_PASSWORD_LENGTH} characters")
    if not re.search(r'[A-Z]', value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r'\d', value):
        raise ValueError("Password must contain at least one digit")
    return value


# =============================================================================
# User Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)

    @field_validator('name')
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        return validate_name(v)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        return validate_password(v)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    role: UserRole
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# Organization Schemas
# =============================================================================

class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    plan_type: str = Field(default="free", max_length=50)

    @field_validator('name')
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        return validate_name(v)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationResponse(OrganizationBase):
    """Schema for organization response data."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Agent Schemas
# =============================================================================

class AgentToolPermissionBase(BaseModel):
    """Base schema for agent tool permissions."""
    tool_name: str = Field(..., min_length=1, max_length=100)
    permission_level: PermissionLevel = PermissionLevel.ENABLED


class AgentToolPermissionCreate(AgentToolPermissionBase):
    """Schema for creating tool permissions."""
    pass


class AgentToolPermissionResponse(AgentToolPermissionBase):
    """Schema for tool permission response."""
    id: int
    agent_id: int

    class Config:
        from_attributes = True


class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    system_instructions: Optional[str] = Field(None, max_length=MAX_INSTRUCTIONS_LENGTH)

    @field_validator('name')
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        return validate_name(v)

    @field_validator('description', 'system_instructions')
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_no_html(v)
        return v


class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    tool_permissions: Optional[List[AgentToolPermissionCreate]] = None


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    system_instructions: Optional[str] = Field(None, max_length=MAX_INSTRUCTIONS_LENGTH)
    tool_permissions: Optional[List[AgentToolPermissionCreate]] = None

    @field_validator('name')
    @classmethod
    def validate_name_field(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_name(v)
        return v

    @field_validator('description', 'system_instructions')
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_no_html(v)
        return v


class AgentResponse(AgentBase):
    """Schema for agent response data."""
    id: int
    user_id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    tool_permissions: List[AgentToolPermissionResponse] = []

    class Config:
        from_attributes = True


# =============================================================================
# Conversation Schemas
# =============================================================================

class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = Field(None, max_length=MAX_TITLE_LENGTH)

    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_no_html(v.strip())
        return v


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    agent_id: int


class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""
    id: int
    user_id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Message Schemas
# =============================================================================

class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, max_length=MAX_CONTENT_LENGTH)


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    pass


class MessageResponse(MessageBase):
    """Schema for message response data."""
    id: int
    conversation_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Execution Plan Schemas
# =============================================================================

class PlanStepSchema(BaseModel):
    """Schema for a single plan step."""
    step_number: int
    description: str = Field(..., max_length=MAX_DESCRIPTION_LENGTH)
    tool: str = Field(..., max_length=100)
    arguments: Dict[str, Any] = {}
    requires_approval: bool = False
    status: StepStatus = StepStatus.PENDING


class ExecutionPlanCreate(BaseModel):
    """Schema for creating an execution plan."""
    conversation_id: int
    agent_id: int
    user_request: str = Field(..., min_length=1, max_length=MAX_CONTENT_LENGTH)


class ExecutionPlanResponse(BaseModel):
    """Schema for execution plan response data."""
    id: int
    conversation_id: int
    user_id: int
    agent_id: int
    user_request: str
    status: PlanStatus
    current_step: int
    plan_data: Dict[str, Any]
    state_data: Optional[Dict[str, Any]] = None
    final_result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_steps(cls, plan) -> "ExecutionPlanResponse":
        """Convert ORM model to response schema with step data."""
        return cls(
            id=plan.id,
            conversation_id=plan.conversation_id,
            user_id=plan.user_id,
            agent_id=plan.agent_id,
            user_request=plan.user_request,
            status=plan.status,
            current_step=plan.current_step,
            plan_data=plan.plan_data or {},
            state_data=plan.state_data,
            final_result=plan.final_result,
            error_message=plan.error_message,
            created_at=plan.created_at,
            started_at=plan.started_at,
            completed_at=plan.completed_at
        )


# =============================================================================
# Approval Request Schemas
# =============================================================================

class ApprovalRequestCreate(BaseModel):
    """Schema for creating an approval request."""
    agent_id: int
    tool_name: str = Field(..., max_length=100)
    tool_arguments: Dict[str, Any] = {}
    description: str = Field(..., max_length=MAX_DESCRIPTION_LENGTH)
    execution_plan_id: Optional[int] = None
    step_index: Optional[int] = None


class ApprovalRejectRequest(BaseModel):
    """Schema for rejecting an approval request."""
    reason: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class ApprovalRequestResponse(BaseModel):
    """Schema for approval request response data."""
    id: int
    user_id: int
    agent_id: int
    tool_name: str
    tool_arguments: Dict[str, Any]
    description: str
    status: ApprovalStatus
    execution_plan_id: Optional[int] = None
    step_index: Optional[int] = None
    approved_at: Optional[datetime] = None
    approved_by_user_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, approval) -> "ApprovalRequestResponse":
        """Convert ORM model to response schema."""
        return cls(
            id=approval.id,
            user_id=approval.user_id,
            agent_id=approval.agent_id,
            tool_name=approval.tool_name,
            tool_arguments=approval.tool_arguments or {},
            description=approval.description,
            status=approval.status,
            execution_plan_id=approval.execution_plan_id,
            step_index=approval.step_index,
            approved_at=approval.approved_at,
            approved_by_user_id=approval.approved_by_user_id,
            rejection_reason=approval.rejection_reason,
            expires_at=approval.expires_at,
            created_at=approval.created_at
        )


# =============================================================================
# Common Response Schemas
# =============================================================================

class SuccessResponse(BaseModel):
    """Schema for simple success responses."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    code: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
