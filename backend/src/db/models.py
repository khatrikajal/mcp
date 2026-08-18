from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class PermissionLevel(str, enum.Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    REQUIRES_APPROVAL = "requires_approval"


class PlanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MeetingImportance(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DelegationStatus(str, enum.Enum):
    PENDING = "pending"           # Awaiting user approval
    APPROVED = "approved"         # User approved delegation
    REJECTED = "rejected"         # User rejected delegation
    JOINING = "joining"           # AI is joining the meeting
    JOINED = "joined"             # AI has joined the meeting
    RECORDING = "recording"       # Meeting is being recorded
    COMPLETED = "completed"       # Meeting completed, report generated
    FAILED = "failed"             # Failed to join or record


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    plan_type = Column(String(50), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization")
    agents = relationship("Agent", back_populates="organization")
    meeting_delegations = relationship("MeetingDelegation", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    agents = relationship("Agent", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    execution_plans = relationship("ExecutionPlan", back_populates="user", foreign_keys="ExecutionPlan.user_id")
    approval_requests = relationship("ApprovalRequest", back_populates="user", foreign_keys="ApprovalRequest.user_id")
    meeting_delegations = relationship("MeetingDelegation", back_populates="user")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    system_instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="agents")
    organization = relationship("Organization", back_populates="agents")
    tool_permissions = relationship("AgentToolPermission", back_populates="agent")
    conversations = relationship("Conversation", back_populates="agent")
    execution_plans = relationship("ExecutionPlan", back_populates="agent")
    approval_requests = relationship("ApprovalRequest", back_populates="agent")


class AgentToolPermission(Base):
    __tablename__ = "agent_tool_permissions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    tool_name = Column(String(255), nullable=False)
    permission_level = Column(SQLEnum(PermissionLevel), default=PermissionLevel.ENABLED)

    # Relationships
    agent = relationship("Agent", back_populates="tool_permissions")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    execution_plans = relationship("ExecutionPlan", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class ExecutionPlan(Base):
    """Planning workflow execution tracking"""
    __tablename__ = "execution_plans"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Plan details
    user_request = Column(Text, nullable=False)  # Original user request
    plan_data = Column(JSON, nullable=False)  # Full plan with steps
    status = Column(SQLEnum(PlanStatus), default=PlanStatus.PENDING)

    # Execution state
    current_step = Column(Integer, default=0)
    state_data = Column(JSON, default={})  # LangGraph state

    # Results
    final_result = Column(Text)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    conversation = relationship("Conversation")
    user = relationship("User")
    agent = relationship("Agent")
    approval_requests = relationship("ApprovalRequest", back_populates="execution_plan")


class ApprovalRequest(Base):
    """Human approval gates for sensitive actions"""
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    execution_plan_id = Column(Integer, ForeignKey("execution_plans.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Action details
    tool_name = Column(String(255), nullable=False)
    tool_arguments = Column(JSON, nullable=False)
    description = Column(Text, nullable=False)
    step_index = Column(Integer)  # Which step in the plan (if applicable)

    # Approval status
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_at = Column(DateTime)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"))
    rejection_reason = Column(Text)

    # Auto-expiration
    expires_at = Column(DateTime, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution_plan = relationship("ExecutionPlan", back_populates="approval_requests")
    user = relationship("User", foreign_keys=[user_id])
    agent = relationship("Agent")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])


class MeetingDelegation(Base):
    """AI meeting delegation tracking"""
    __tablename__ = "meeting_delegations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Meeting details (from Nylas)
    meeting_id = Column(String(255), nullable=False, index=True)  # Nylas event ID
    meeting_title = Column(String(500), nullable=False)
    meeting_description = Column(Text)
    meeting_start_time = Column(DateTime, nullable=False, index=True)
    meeting_end_time = Column(DateTime, nullable=False)
    meeting_location = Column(String(500))  # URL or physical location
    meeting_organizer = Column(String(255))
    meeting_attendees = Column(JSON, default=[])  # List of attendee emails

    # Importance classification
    importance = Column(SQLEnum(MeetingImportance), default=MeetingImportance.MEDIUM)
    importance_score = Column(Integer, default=0)
    importance_reasons = Column(JSON, default=[])  # List of reasons for classification

    # Delegation status
    status = Column(SQLEnum(DelegationStatus), default=DelegationStatus.PENDING)
    auto_approved = Column(Boolean, default=False)  # Was it auto-approved based on importance?
    requires_approval = Column(Boolean, default=True)

    # Notetaker integration
    notetaker_id = Column(String(255))  # Nylas notetaker ID
    notetaker_joined_at = Column(DateTime)
    notetaker_left_at = Column(DateTime)

    # AI-generated content
    introduction_script = Column(Text)  # Script for AI to introduce itself (future use)

    # Post-meeting content
    transcript = Column(Text)  # Full meeting transcript
    transcript_url = Column(String(500))  # URL to transcript if stored externally
    recording_url = Column(String(500))  # URL to recording

    # Report
    report = Column(Text)  # AI-generated meeting report
    report_summary = Column(Text)  # Executive summary
    action_items = Column(JSON, default=[])  # Extracted action items
    decisions = Column(JSON, default=[])  # Key decisions made
    report_sent = Column(Boolean, default=False)
    report_sent_at = Column(DateTime)

    # Error tracking
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="meeting_delegations")
    organization = relationship("Organization", back_populates="meeting_delegations")
