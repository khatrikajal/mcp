from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from server.database.models import UserRole, PermissionLevel


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    role: UserRole
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Organization schemas
class OrganizationBase(BaseModel):
    name: str
    plan_type: str = "free"


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Agent schemas
class AgentToolPermissionBase(BaseModel):
    tool_name: str
    permission_level: PermissionLevel = PermissionLevel.ENABLED


class AgentToolPermissionCreate(AgentToolPermissionBase):
    pass


class AgentToolPermissionResponse(AgentToolPermissionBase):
    id: int
    agent_id: int

    class Config:
        from_attributes = True


class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_instructions: Optional[str] = None


class AgentCreate(AgentBase):
    tool_permissions: Optional[List[AgentToolPermissionCreate]] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_instructions: Optional[str] = None
    tool_permissions: Optional[List[AgentToolPermissionCreate]] = None


class AgentResponse(AgentBase):
    id: int
    user_id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    tool_permissions: List[AgentToolPermissionResponse] = []

    class Config:
        from_attributes = True


# Conversation schemas
class ConversationBase(BaseModel):
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    agent_id: int


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message schemas
class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
