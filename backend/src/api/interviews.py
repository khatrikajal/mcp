"""
Interview API endpoints.

Provides endpoints for AI-conducted interview management:
- Schedule interviews
- Generate questions
- Start/end interview sessions
- Get analysis and reports
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
import logging

from backend.src.db.connection import get_db
from backend.src.db.models import (
    User, InterviewSession, InterviewQuestion,
    InterviewType, InterviewStatus, InterviewRecommendation
)
from backend.src.api.auth_utils import get_current_active_user
from backend.src.services.interview_service import InterviewService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interviews", tags=["interviews"])


# =============================================================================
# Pydantic Schemas
# =============================================================================

class InterviewCreate(BaseModel):
    """Schema for creating a new interview."""
    candidate_name: str = Field(..., min_length=1, max_length=255)
    candidate_email: EmailStr
    candidate_phone: Optional[str] = None
    candidate_resume_url: Optional[str] = None
    candidate_linkedin: Optional[str] = None

    position_title: str = Field(..., min_length=1, max_length=255)
    position_description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)

    interview_type: InterviewType = InterviewType.MIXED
    duration_minutes: int = Field(default=45, ge=15, le=120)
    scheduled_time: datetime
    meeting_url: Optional[str] = None
    language: str = "en"


class InterviewUpdate(BaseModel):
    """Schema for updating an interview."""
    candidate_name: Optional[str] = None
    candidate_email: Optional[EmailStr] = None
    position_title: Optional[str] = None
    position_description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    interview_type: Optional[InterviewType] = None
    duration_minutes: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    meeting_url: Optional[str] = None


class QuestionResponse(BaseModel):
    """Schema for interview question response."""
    id: int
    question_number: int
    question_text: str
    question_type: str
    competency: Optional[str]
    difficulty: str
    weight: int
    candidate_answer: Optional[str]
    score: Optional[int]
    feedback: Optional[str]
    audio_generated: bool
    audio_url: Optional[str]

    class Config:
        from_attributes = True


class InterviewResponse(BaseModel):
    """Schema for interview response."""
    id: int
    user_id: int
    organization_id: int

    # Candidate info
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str]
    candidate_resume_url: Optional[str]
    candidate_linkedin: Optional[str]

    # Position
    position_title: str
    position_description: Optional[str]
    required_skills: List[str]

    # Configuration
    interview_type: str
    duration_minutes: int
    scheduled_time: datetime
    meeting_url: Optional[str]
    language: str

    # Status
    status: str
    notetaker_id: Optional[str]

    # Scoring
    overall_score: Optional[int]
    recommendation: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    competency_scores: dict

    # Report
    report_summary: Optional[str]
    report_sent: bool

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Questions count
    questions_count: int = 0

    class Config:
        from_attributes = True


class InterviewAnalysisResponse(BaseModel):
    """Schema for interview analysis results."""
    overall_score: int
    recommendation: str
    competency_scores: dict
    strengths: List[str]
    weaknesses: List[str]
    report_summary: Optional[str]


class InterviewReportResponse(BaseModel):
    """Schema for full interview report."""
    interview_id: int
    candidate_name: str
    position_title: str
    overall_score: int
    recommendation: str
    report: str
    report_summary: str
    questions: List[QuestionResponse]
    strengths: List[str]
    weaknesses: List[str]
    competency_scores: dict
    completed_at: Optional[datetime]


class GenerateQuestionsRequest(BaseModel):
    """Schema for generating questions."""
    num_questions: int = Field(default=8, ge=3, le=15)


class StartInterviewResponse(BaseModel):
    """Schema for start interview response."""
    status: str
    interview_id: int
    notetaker_id: Optional[str]
    intro_audio_duration: int
    question_audio_files: List[str]
    total_questions: int


# =============================================================================
# Helper Functions
# =============================================================================

def interview_to_response(interview: InterviewSession) -> InterviewResponse:
    """Convert interview model to response schema."""
    return InterviewResponse(
        id=interview.id,
        user_id=interview.user_id,
        organization_id=interview.organization_id,
        candidate_name=interview.candidate_name,
        candidate_email=interview.candidate_email,
        candidate_phone=interview.candidate_phone,
        candidate_resume_url=interview.candidate_resume_url,
        candidate_linkedin=interview.candidate_linkedin,
        position_title=interview.position_title,
        position_description=interview.position_description,
        required_skills=interview.required_skills or [],
        interview_type=interview.interview_type.value,
        duration_minutes=interview.duration_minutes,
        scheduled_time=interview.scheduled_time,
        meeting_url=interview.meeting_url,
        language=interview.language,
        status=interview.status.value,
        notetaker_id=interview.notetaker_id,
        overall_score=interview.overall_score,
        recommendation=interview.recommendation.value if interview.recommendation else None,
        strengths=interview.strengths or [],
        weaknesses=interview.weaknesses or [],
        competency_scores=interview.competency_scores or {},
        report_summary=interview.report_summary,
        report_sent=interview.report_sent,
        created_at=interview.created_at,
        started_at=interview.started_at,
        completed_at=interview.completed_at,
        questions_count=len(interview.questions) if interview.questions else 0
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Schedule a new interview session.

    Creates an interview record and optionally creates a calendar event.
    """
    service = InterviewService(db)

    interview = service.create_interview(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        candidate_name=data.candidate_name,
        candidate_email=data.candidate_email,
        position_title=data.position_title,
        position_description=data.position_description,
        required_skills=data.required_skills,
        interview_type=data.interview_type,
        duration_minutes=data.duration_minutes,
        scheduled_time=data.scheduled_time,
        meeting_url=data.meeting_url
    )

    # Update additional fields
    interview.candidate_phone = data.candidate_phone
    interview.candidate_resume_url = data.candidate_resume_url
    interview.candidate_linkedin = data.candidate_linkedin
    interview.language = data.language
    db.commit()

    logger.info(f"User {current_user.id} created interview {interview.id}")
    return interview_to_response(interview)


@router.get("", response_model=List[InterviewResponse])
def list_interviews(
    status_filter: Optional[InterviewStatus] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all interviews for the current user's organization."""
    service = InterviewService(db)

    interviews = service.list_interviews(
        organization_id=current_user.organization_id,
        status=status_filter,
        limit=limit
    )

    return [interview_to_response(i) for i in interviews]


@router.get("/upcoming", response_model=List[InterviewResponse])
def get_upcoming_interviews(
    hours_ahead: int = 24,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get interviews scheduled in the next X hours."""
    from datetime import timedelta

    now = datetime.utcnow()
    cutoff = now + timedelta(hours=hours_ahead)

    interviews = db.query(InterviewSession).filter(
        InterviewSession.organization_id == current_user.organization_id,
        InterviewSession.scheduled_time >= now,
        InterviewSession.scheduled_time <= cutoff,
        InterviewSession.status.in_([
            InterviewStatus.SCHEDULED,
            InterviewStatus.READY
        ])
    ).order_by(InterviewSession.scheduled_time).all()

    return [interview_to_response(i) for i in interviews]


@router.get("/stats")
def get_interview_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get interview statistics."""
    from sqlalchemy import func

    base_query = db.query(InterviewSession).filter(
        InterviewSession.organization_id == current_user.organization_id
    )

    total = base_query.count()
    scheduled = base_query.filter(InterviewSession.status == InterviewStatus.SCHEDULED).count()
    ready = base_query.filter(InterviewSession.status == InterviewStatus.READY).count()
    in_progress = base_query.filter(InterviewSession.status == InterviewStatus.IN_PROGRESS).count()
    completed = base_query.filter(InterviewSession.status == InterviewStatus.COMPLETED).count()
    cancelled = base_query.filter(InterviewSession.status == InterviewStatus.CANCELLED).count()

    # Average score for completed interviews
    avg_score = db.query(func.avg(InterviewSession.overall_score)).filter(
        InterviewSession.organization_id == current_user.organization_id,
        InterviewSession.status == InterviewStatus.COMPLETED
    ).scalar() or 0

    # Recommendation distribution
    recommendations = {}
    for rec in InterviewRecommendation:
        count = base_query.filter(InterviewSession.recommendation == rec).count()
        recommendations[rec.value] = count

    return {
        "total": total,
        "scheduled": scheduled,
        "ready": ready,
        "in_progress": in_progress,
        "completed": completed,
        "cancelled": cancelled,
        "average_score": round(avg_score, 1),
        "recommendations": recommendations
    }


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific interview by ID."""
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    return interview_to_response(interview)


@router.put("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: int,
    data: InterviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an interview."""
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.status not in [InterviewStatus.SCHEDULED, InterviewStatus.READY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update interview in current status"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(interview, field, value)

    db.commit()
    db.refresh(interview)

    logger.info(f"User {current_user.id} updated interview {interview_id}")
    return interview_to_response(interview)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_interview(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel an interview."""
    service = InterviewService(db)

    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    try:
        service.cancel_interview(interview_id)
        logger.info(f"User {current_user.id} cancelled interview {interview_id}")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return None


# =============================================================================
# Question Generation
# =============================================================================

@router.post("/{interview_id}/generate-questions", response_model=List[QuestionResponse])
def generate_questions(
    interview_id: int,
    data: GenerateQuestionsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate interview questions using AI.

    Questions are tailored based on:
    - Interview type (technical, behavioral, HR)
    - Position requirements
    - Required skills
    """
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.status not in [InterviewStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate questions for interview in status: {interview.status.value}"
        )

    service = InterviewService(db)

    questions = service.generate_questions(
        interview_id=interview_id,
        interview_type=interview.interview_type,
        position_title=interview.position_title,
        required_skills=interview.required_skills or [],
        num_questions=data.num_questions
    )

    logger.info(f"Generated {len(questions)} questions for interview {interview_id}")

    return [
        QuestionResponse(
            id=q.id,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=q.question_type.value,
            competency=q.competency,
            difficulty=q.difficulty,
            weight=q.weight,
            candidate_answer=q.candidate_answer,
            score=q.score,
            feedback=q.feedback,
            audio_generated=q.audio_generated,
            audio_url=q.audio_url
        )
        for q in questions
    ]


@router.get("/{interview_id}/questions", response_model=List[QuestionResponse])
def get_questions(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all questions for an interview."""
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview_id
    ).order_by(InterviewQuestion.question_number).all()

    return [
        QuestionResponse(
            id=q.id,
            question_number=q.question_number,
            question_text=q.question_text,
            question_type=q.question_type.value,
            competency=q.competency,
            difficulty=q.difficulty,
            weight=q.weight,
            candidate_answer=q.candidate_answer,
            score=q.score,
            feedback=q.feedback,
            audio_generated=q.audio_generated,
            audio_url=q.audio_url
        )
        for q in questions
    ]


# =============================================================================
# Interview Execution
# =============================================================================

@router.post("/{interview_id}/start", response_model=StartInterviewResponse)
async def start_interview(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start an interview session.

    This will:
    1. Generate TTS audio for all questions
    2. Join the meeting via Notetaker (if meeting URL provided)
    3. Begin recording
    """
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.status not in [InterviewStatus.SCHEDULED, InterviewStatus.READY]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start interview in status: {interview.status.value}"
        )

    # Ensure questions are generated
    if not interview.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generate questions first before starting the interview"
        )

    service = InterviewService(db)

    try:
        result = await service.start_interview(interview_id)
        logger.info(f"User {current_user.id} started interview {interview_id}")
        return StartInterviewResponse(**result)
    except Exception as e:
        logger.error(f"Failed to start interview {interview_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{interview_id}/end", response_model=InterviewAnalysisResponse)
async def end_interview(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    End an interview and analyze results.

    This will:
    1. Stop recording
    2. Retrieve transcript
    3. Extract and score answers
    4. Generate report
    """
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview is not in progress (current status: {interview.status.value})"
        )

    service = InterviewService(db)

    try:
        result = await service.end_interview(interview_id)
        logger.info(f"User {current_user.id} ended interview {interview_id}")
        return InterviewAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Failed to end interview {interview_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# =============================================================================
# Reports
# =============================================================================

@router.get("/{interview_id}/report", response_model=InterviewReportResponse)
def get_report(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the full interview report."""
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.status != InterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview report is not available yet"
        )

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview_id
    ).order_by(InterviewQuestion.question_number).all()

    return InterviewReportResponse(
        interview_id=interview.id,
        candidate_name=interview.candidate_name,
        position_title=interview.position_title,
        overall_score=interview.overall_score or 0,
        recommendation=interview.recommendation.value if interview.recommendation else "pending",
        report=interview.report or "",
        report_summary=interview.report_summary or "",
        questions=[
            QuestionResponse(
                id=q.id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_type=q.question_type.value,
                competency=q.competency,
                difficulty=q.difficulty,
                weight=q.weight,
                candidate_answer=q.candidate_answer,
                score=q.score,
                feedback=q.feedback,
                audio_generated=q.audio_generated,
                audio_url=q.audio_url
            )
            for q in questions
        ],
        strengths=interview.strengths or [],
        weaknesses=interview.weaknesses or [],
        competency_scores=interview.competency_scores or {},
        completed_at=interview.completed_at
    )


@router.post("/{interview_id}/send-report")
async def send_report(
    interview_id: int,
    recipients: List[EmailStr],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send the interview report via email."""
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if interview.status != InterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview report is not available yet"
        )

    # TODO: Implement email sending via email_service
    # For now, just mark as sent
    interview.report_sent = True
    interview.report_sent_at = datetime.utcnow()
    db.commit()

    logger.info(f"Sent interview {interview_id} report to {len(recipients)} recipients")

    return {
        "status": "sent",
        "recipients": recipients,
        "sent_at": interview.report_sent_at
    }


# =============================================================================
# TTS Audio Generation
# =============================================================================

@router.post("/{interview_id}/generate-audio")
async def generate_question_audio(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate TTS audio for all interview questions.

    This creates audio files that the AI can use to speak
    the questions during the interview.
    """
    interview = db.query(InterviewSession).filter(
        InterviewSession.id == interview_id,
        InterviewSession.organization_id == current_user.organization_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )

    if not interview.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Generate questions first"
        )

    service = InterviewService(db)

    try:
        audio_files = await service.generate_all_question_audio(interview_id)
        return {
            "status": "generated",
            "audio_files": audio_files,
            "count": len(audio_files)
        }
    except Exception as e:
        logger.error(f"Failed to generate audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
