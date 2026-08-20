from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON, Boolean, Float, LargeBinary, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

Base = declarative_base()

# Embedding dimension for sentence-transformers all-MiniLM-L6-v2 model
EMBEDDING_DIMENSION = 384


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


class InterviewType(str, enum.Enum):
    TECHNICAL = "technical"       # Coding, system design, technical knowledge
    BEHAVIORAL = "behavioral"     # STAR method, soft skills
    HR = "hr"                     # Culture fit, salary, availability
    MIXED = "mixed"               # Combination of all types


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"       # Interview scheduled
    PREPARING = "preparing"       # AI preparing questions
    READY = "ready"               # Questions generated, ready to start
    IN_PROGRESS = "in_progress"   # Interview ongoing
    ANALYZING = "analyzing"       # Analyzing transcript
    COMPLETED = "completed"       # Analysis complete
    CANCELLED = "cancelled"       # Interview cancelled
    FAILED = "failed"             # Error occurred


class InterviewRecommendation(str, enum.Enum):
    STRONG_HIRE = "strong_hire"   # Score >= 85
    HIRE = "hire"                 # Score >= 70
    MAYBE = "maybe"               # Score >= 55
    NO_HIRE = "no_hire"           # Score >= 40
    STRONG_NO_HIRE = "strong_no_hire"  # Score < 40


class MemoryType(str, enum.Enum):
    PREFERENCE = "preference"       # User preferences (e.g., preferred meeting time)
    FACT = "fact"                   # Learned facts (e.g., reports to Sarah)
    INTERACTION = "interaction"     # Past interactions summary
    SUMMARY = "summary"             # Conversation summaries
    MEETING = "meeting"             # Meeting-related memories
    EMAIL = "email"                 # Email-related memories
    CONTEXT = "context"             # General context information


class PreferenceCategory(str, enum.Enum):
    SCHEDULING = "scheduling"       # Meeting/calendar preferences
    COMMUNICATION = "communication" # Email/communication style
    WORKFLOW = "workflow"           # Work preferences
    PERSONAL = "personal"           # Personal info (timezone, etc.)
    TOOL = "tool"                   # Tool-specific preferences


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
    tool_permissions = relationship("AgentToolPermission", back_populates="agent", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    execution_plans = relationship("ExecutionPlan", back_populates="agent", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="agent", cascade="all, delete-orphan")


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
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    execution_plans = relationship("ExecutionPlan", back_populates="conversation", cascade="all, delete-orphan")


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


class InterviewSession(Base):
    """AI-conducted interview session tracking"""
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Candidate information
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    candidate_phone = Column(String(50))
    candidate_resume_url = Column(String(500))
    candidate_linkedin = Column(String(500))

    # Position details
    position_title = Column(String(255), nullable=False)
    position_description = Column(Text)
    required_skills = Column(JSON, default=[])  # List of required skills

    # Interview configuration
    interview_type = Column(SQLEnum(InterviewType), default=InterviewType.MIXED)
    duration_minutes = Column(Integer, default=45)
    language = Column(String(50), default="en")  # Interview language

    # Scheduling
    scheduled_time = Column(DateTime, nullable=False)
    meeting_url = Column(String(500))  # Meeting link
    calendar_event_id = Column(String(255))  # Nylas event ID

    # Status tracking
    status = Column(SQLEnum(InterviewStatus), default=InterviewStatus.SCHEDULED)

    # Notetaker integration (for recording)
    notetaker_id = Column(String(255))
    notetaker_joined_at = Column(DateTime)
    notetaker_left_at = Column(DateTime)

    # Interview content
    transcript = Column(Text)  # Full interview transcript
    transcript_url = Column(String(500))
    recording_url = Column(String(500))

    # AI Voice settings
    ai_voice_id = Column(String(100))  # TTS voice ID
    ai_voice_name = Column(String(100), default="Professional Interviewer")
    ai_speaking_rate = Column(Integer, default=100)  # 50-150, 100 is normal

    # Scoring & Analysis
    overall_score = Column(Integer)  # 0-100
    recommendation = Column(SQLEnum(InterviewRecommendation))
    strengths = Column(JSON, default=[])  # List of candidate strengths
    weaknesses = Column(JSON, default=[])  # Areas for improvement
    competency_scores = Column(JSON, default={})  # Detailed competency breakdown

    # Generated report
    report = Column(Text)  # Full AI-generated report
    report_summary = Column(Text)  # Executive summary
    report_sent = Column(Boolean, default=False)
    report_sent_at = Column(DateTime)

    # Error tracking
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", backref="interview_sessions")
    organization = relationship("Organization", backref="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    """Individual interview questions"""
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)

    # Question details
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(SQLEnum(InterviewType), nullable=False)
    competency = Column(String(100))  # e.g., "problem_solving", "communication"
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    weight = Column(Integer, default=10)  # Question importance weight

    # Expected answer hints (for AI scoring)
    expected_keywords = Column(JSON, default=[])  # Keywords to look for
    ideal_answer_points = Column(JSON, default=[])  # Key points expected

    # Candidate's answer (extracted from transcript)
    candidate_answer = Column(Text)
    answer_timestamp_start = Column(Integer)  # Seconds into interview
    answer_timestamp_end = Column(Integer)

    # Scoring
    score = Column(Integer)  # 0-10
    score_reasoning = Column(Text)  # AI explanation for score
    feedback = Column(Text)  # Detailed feedback

    # Follow-up
    follow_up_asked = Column(Boolean, default=False)
    follow_up_question = Column(Text)
    follow_up_answer = Column(Text)

    # Audio TTS tracking
    audio_generated = Column(Boolean, default=False)
    audio_url = Column(String(500))  # TTS audio file URL
    audio_duration_seconds = Column(Integer)

    # Timestamps
    asked_at = Column(DateTime)
    answered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    interview = relationship("InterviewSession", back_populates="questions")


class AgentMemory(Base):
    """
    Vector-based memory storage for agents.
    Stores embeddings for semantic search across conversations, meetings, etc.
    """
    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Memory content
    memory_type = Column(SQLEnum(MemoryType), nullable=False)
    key = Column(String(255), nullable=False, index=True)  # Memory identifier
    content = Column(Text, nullable=False)  # The actual content
    summary = Column(Text)  # Optional summarized version

    # Vector embedding (stored as binary for SQLite, Vector for PostgreSQL)
    embedding = Column(LargeBinary)  # Serialized numpy array for SQLite
    embedding_model = Column(String(100), default="all-MiniLM-L6-v2")

    # Metadata
    source = Column(String(50))  # conversation, meeting, email, manual
    source_id = Column(Integer)  # ID of source record
    importance = Column(Float, default=0.5)  # 0-1 importance score
    access_count = Column(Integer, default=0)  # How often this memory is accessed
    last_accessed = Column(DateTime)

    # TTL support
    expires_at = Column(DateTime)  # Optional expiration

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", backref="memories")
    user = relationship("User", backref="agent_memories")
    organization = relationship("Organization", backref="agent_memories")

    # Index for faster searches
    __table_args__ = (
        Index('idx_agent_memory_type', 'agent_id', 'memory_type'),
        Index('idx_memory_key', 'agent_id', 'key'),
    )


class UserPreference(Base):
    """
    Learned user preferences from interactions.
    Automatically extracted from user corrections and interactions.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Preference details
    category = Column(SQLEnum(PreferenceCategory), nullable=False)
    preference_key = Column(String(255), nullable=False)  # e.g., "preferred_meeting_time"
    preference_value = Column(Text, nullable=False)  # e.g., "2:00 PM"
    confidence = Column(Float, default=0.5)  # How confident we are in this preference

    # Learning metadata
    source_type = Column(String(50))  # correction, explicit, inferred
    source_message_id = Column(Integer)  # Message where this was learned
    times_confirmed = Column(Integer, default=1)  # How many times user confirmed this
    times_contradicted = Column(Integer, default=0)  # How many times user contradicted this

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="preferences")
    organization = relationship("Organization", backref="user_preferences")

    # Unique constraint on user + category + key
    __table_args__ = (
        Index('idx_user_preference_key', 'user_id', 'category', 'preference_key', unique=True),
    )


class ConversationSummary(Base):
    """
    Summarized conversations for long-term memory.
    Old conversations are summarized to save context space.
    """
    __tablename__ = "conversation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Summary content
    summary = Column(Text, nullable=False)  # The summary text
    key_topics = Column(JSON, default=[])  # Main topics discussed
    key_entities = Column(JSON, default=[])  # People, dates, etc. mentioned
    action_items = Column(JSON, default=[])  # Any action items from conversation
    decisions = Column(JSON, default=[])  # Decisions made

    # Embedding for semantic search
    embedding = Column(LargeBinary)  # Serialized numpy array

    # Coverage
    message_count = Column(Integer, default=0)  # Number of messages summarized
    start_message_id = Column(Integer)  # First message covered
    end_message_id = Column(Integer)  # Last message covered
    time_range_start = Column(DateTime)
    time_range_end = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", backref="summaries")
    user = relationship("User", backref="conversation_summaries")
    agent = relationship("Agent", backref="conversation_summaries")


class MemorySearchLog(Base):
    """
    Log of memory searches for analytics and improvement.
    """
    __tablename__ = "memory_search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)

    # Search details
    query = Column(Text, nullable=False)
    query_embedding = Column(LargeBinary)  # Serialized embedding
    result_count = Column(Integer, default=0)
    top_result_ids = Column(JSON, default=[])  # IDs of top results
    result_used = Column(Boolean, default=False)  # Was a result used in response?

    # Performance
    search_time_ms = Column(Integer)  # Search duration

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="memory_searches")
    agent = relationship("Agent", backref="memory_searches")


class SecurityEventType(str, enum.Enum):
    """Types of security events for audit logging."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    AGENT_CREATED = "agent_created"
    AGENT_DELETED = "agent_deleted"
    TOOL_EXECUTED = "tool_executed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    MEETING_JOINED = "meeting_joined"
    INTERVIEW_CONDUCTED = "interview_conducted"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PERMISSION_DENIED = "permission_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"


class ThreatLevel(str, enum.Enum):
    """Threat severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """
    Comprehensive audit logging for security and compliance.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Actor information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous actions
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    session_id = Column(String(100))

    # Event details
    event_type = Column(SQLEnum(SecurityEventType), nullable=False, index=True)
    resource_type = Column(String(100))  # agent, conversation, approval, etc.
    resource_id = Column(Integer)
    action = Column(String(100))  # create, read, update, delete, execute

    # Security classification
    threat_level = Column(SQLEnum(ThreatLevel), default=ThreatLevel.NONE)

    # Event data
    description = Column(Text)
    request_data = Column(JSON, default={})  # Sanitized request data
    response_status = Column(Integer)  # HTTP status code
    error_message = Column(Text)

    # Context
    endpoint = Column(String(255))
    method = Column(String(10))  # GET, POST, etc.
    duration_ms = Column(Integer)  # Request duration

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="audit_logs")
    organization = relationship("Organization", backref="audit_logs")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_event_type', 'event_type', 'created_at'),
        Index('idx_audit_threat', 'threat_level', 'created_at'),
    )


class Permission(Base):
    """
    Fine-grained permissions for RBAC.
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., "agent:create"
    description = Column(Text)
    category = Column(String(50))  # agent, conversation, approval, etc.

    created_at = Column(DateTime, default=datetime.utcnow)


class Role(Base):
    """
    Custom roles with assigned permissions.
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)  # Built-in roles can't be deleted

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", backref="roles")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_role_org_name', 'organization_id', 'name', unique=True),
    )


class RolePermission(Base):
    """
    Many-to-many relationship between roles and permissions.
    """
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", backref="role_permissions")

    __table_args__ = (
        Index('idx_role_permission', 'role_id', 'permission_id', unique=True),
    )


class UserRole(Base):
    """
    User to role assignment.
    """
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="role_assignments")
    role = relationship("Role", backref="user_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])

    __table_args__ = (
        Index('idx_user_role', 'user_id', 'role_id', unique=True),
    )


class AnalyticsEvent(Base):
    """
    Analytics events for dashboard metrics.
    """
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)

    # Event classification
    event_category = Column(String(50), nullable=False, index=True)  # chat, tool, meeting, interview
    event_name = Column(String(100), nullable=False, index=True)  # message_sent, tool_executed, etc.

    # Event data
    properties = Column(JSON, default={})  # Event-specific properties
    value = Column(Float)  # Numeric value (duration, score, etc.)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    organization = relationship("Organization", backref="analytics_events")

    __table_args__ = (
        Index('idx_analytics_org_category', 'organization_id', 'event_category', 'created_at'),
    )
