"""
Delegation Service - AI Meeting Delegation with Importance Classification

This service handles:
1. Scanning upcoming meetings from calendar
2. Classifying meeting importance (CRITICAL, HIGH, MEDIUM, LOW)
3. Auto-approving low/medium importance meetings
4. Joining meetings via Nylas Notetaker
5. Generating post-meeting reports with AI analysis
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from groq import Groq
from sqlalchemy.orm import Session

from backend.src.core.config import GROQ_API_KEY
from backend.src.db.models import (
    MeetingDelegation,
    MeetingImportance,
    DelegationStatus,
    User,
)
from backend.src.services.calendar_service import CalendarService
from backend.src.services.notetaker_service import NotetakerService
from backend.src.services.email_service import EmailService

logger = logging.getLogger(__name__)


# VIP attendee patterns (CEO, CTO, VP, etc.)
VIP_PATTERNS = [
    r'\bceo\b', r'\bcto\b', r'\bcfo\b', r'\bcoo\b', r'\bcio\b',
    r'\bvp\b', r'\bvice\s*president\b', r'\bdirector\b', r'\bexecutive\b',
    r'\bpartner\b', r'\bfounder\b', r'\bowner\b', r'\bchairman\b',
]

# Critical meeting title keywords
CRITICAL_KEYWORDS = [
    'urgent', 'crisis', 'emergency', 'board', 'executive', 'investor',
    'critical', 'asap', 'immediately', 'priority',
]

# High importance keywords
HIGH_KEYWORDS = [
    'decision', 'review', '1:1', 'one-on-one', 'strategy', 'planning',
    'budget', 'quarterly', 'performance', 'interview', 'final',
]

# Model for report generation
REPORT_MODEL = "llama3-70b-8192"


class DelegationService:
    """Service for AI meeting delegation and importance classification."""

    def __init__(self, db: Session):
        self.db = db
        self.calendar_service = CalendarService()
        self.notetaker_service = NotetakerService()
        self.email_service = EmailService()
        self.groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

    def classify_meeting_importance(
        self,
        title: str,
        description: str = "",
        attendees: list[dict] = None,
        organizer: str = "",
    ) -> tuple[MeetingImportance, int, list[str]]:
        """
        Classify meeting importance using scoring algorithm.

        Returns:
            Tuple of (importance level, score, list of reasons)
        """
        score = 0
        reasons = []
        attendees = attendees or []

        # Combine title and description for pattern matching
        text = f"{title} {description} {organizer}".lower()
        attendee_text = " ".join(
            f"{a.get('name', '')} {a.get('email', '')}" for a in attendees
        ).lower()

        # Check for VIP attendees (+3 each)
        for pattern in VIP_PATTERNS:
            if re.search(pattern, attendee_text, re.IGNORECASE):
                score += 3
                reasons.append(f"VIP attendee detected (pattern: {pattern})")
                break  # Only count VIP once

        # Check for critical keywords (+3 each)
        for keyword in CRITICAL_KEYWORDS:
            if keyword.lower() in text:
                score += 3
                reasons.append(f"Critical keyword in title/description: '{keyword}'")
                break  # Only count once

        # Check for high importance keywords (+2 each)
        for keyword in HIGH_KEYWORDS:
            if keyword.lower() in text:
                score += 2
                reasons.append(f"High importance keyword: '{keyword}'")
                break  # Only count once

        # Check attendee count
        attendee_count = len(attendees)
        if attendee_count > 10:
            score += 2
            reasons.append(f"Large meeting (>10 attendees): {attendee_count} people")
        elif attendee_count > 5:
            score += 1
            reasons.append(f"Medium meeting (>5 attendees): {attendee_count} people")

        # Determine importance level
        if score >= 5:
            importance = MeetingImportance.CRITICAL
        elif score >= 3:
            importance = MeetingImportance.HIGH
        elif score >= 1:
            importance = MeetingImportance.MEDIUM
        else:
            importance = MeetingImportance.LOW
            reasons.append("Standard meeting with no special indicators")

        logger.info(
            f"Meeting classified: '{title}' -> {importance.value} (score: {score})"
        )

        return importance, score, reasons

    def should_auto_approve(
        self,
        importance: MeetingImportance,
        user_settings: dict = None,
    ) -> bool:
        """
        Determine if a meeting should be auto-approved based on importance.

        Default behavior:
        - CRITICAL: requires approval
        - HIGH: requires approval
        - MEDIUM: auto-approve (configurable)
        - LOW: auto-approve

        Args:
            importance: Meeting importance level
            user_settings: Optional user preferences (future use)

        Returns:
            True if should auto-approve, False if requires user approval
        """
        user_settings = user_settings or {}

        # Check user preferences (default to standard behavior)
        auto_approve_medium = user_settings.get("auto_approve_medium", True)
        auto_approve_low = user_settings.get("auto_approve_low", True)

        if importance == MeetingImportance.CRITICAL:
            return False
        elif importance == MeetingImportance.HIGH:
            return False
        elif importance == MeetingImportance.MEDIUM:
            return auto_approve_medium
        else:  # LOW
            return auto_approve_low

    def generate_introduction_script(
        self,
        meeting_title: str,
        meeting_description: str = "",
        user_name: str = "the meeting owner",
    ) -> str:
        """
        Generate an introduction script for the AI to use when joining a meeting.

        Note: Nylas Notetaker cannot currently speak in meetings, so this is
        generated but not automatically delivered. Future enhancement would
        add audio SDK for verbal introduction.

        Returns:
            Introduction script text
        """
        if not self.groq_client:
            return self._default_introduction(meeting_title, user_name)

        try:
            prompt = f"""Generate a brief, professional introduction script for an AI meeting assistant.

Meeting Title: {meeting_title}
Meeting Description: {meeting_description or 'No description provided'}
On behalf of: {user_name}

The AI is joining to:
1. Record and transcribe the meeting
2. Take notes and identify action items
3. Generate a summary report for {user_name}

Generate a friendly 2-3 sentence introduction (under 50 words) that the AI would say when joining.
Do not include any greetings like "Hello" or "Hi" at the very start - begin with introducing the purpose.
"""

            response = self.groq_client.chat.completions.create(
                model=REPORT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
            )

            script = response.choices[0].message.content.strip()
            logger.info(f"Generated introduction script for '{meeting_title}'")
            return script

        except Exception as e:
            logger.error(f"Failed to generate introduction: {e}")
            return self._default_introduction(meeting_title, user_name)

    def _default_introduction(self, meeting_title: str, user_name: str) -> str:
        """Default introduction when LLM is unavailable."""
        return (
            f"I'm an AI assistant joining on behalf of {user_name} to record "
            f"this meeting about '{meeting_title}'. I'll be taking notes and "
            f"will provide a summary report after the meeting concludes."
        )

    def generate_delegation_report(
        self,
        transcript: str,
        meeting_title: str,
        meeting_description: str = "",
        attendees: list[dict] = None,
    ) -> dict:
        """
        Generate a comprehensive post-meeting report using AI.

        Returns:
            Dictionary containing:
            - summary: Executive summary
            - report: Full report text
            - action_items: List of action items with assignees
            - decisions: List of key decisions made
        """
        attendees = attendees or []

        if not self.groq_client or not transcript:
            return self._empty_report(meeting_title)

        try:
            attendee_names = ", ".join(
                a.get("name", a.get("email", "Unknown")) for a in attendees
            )

            prompt = f"""Analyze this meeting transcript and generate a comprehensive report.

MEETING: {meeting_title}
DESCRIPTION: {meeting_description or 'None provided'}
ATTENDEES: {attendee_names or 'Unknown'}

TRANSCRIPT:
{transcript[:15000]}  # Limit transcript length for API

Generate a structured report with the following sections:

1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY DISCUSSION POINTS (bullet points)
3. DECISIONS MADE (if any)
4. ACTION ITEMS (format: "- [Assignee] Task description [Deadline if mentioned]")
5. FOLLOW-UP QUESTIONS (questions that need answers)

Be concise and professional. Focus on actionable insights."""

            response = self.groq_client.chat.completions.create(
                model=REPORT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )

            report_text = response.choices[0].message.content.strip()

            # Extract action items using another LLM call
            action_items = self._extract_action_items(report_text)
            decisions = self._extract_decisions(report_text)
            summary = self._extract_summary(report_text)

            logger.info(f"Generated report for '{meeting_title}'")

            return {
                "summary": summary,
                "report": report_text,
                "action_items": action_items,
                "decisions": decisions,
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return self._empty_report(meeting_title)

    def _empty_report(self, meeting_title: str) -> dict:
        """Return empty report structure when generation fails."""
        return {
            "summary": f"Meeting report for '{meeting_title}' - transcript processing failed.",
            "report": "Report generation failed. Please check the transcript manually.",
            "action_items": [],
            "decisions": [],
        }

    def _extract_action_items(self, report_text: str) -> list[dict]:
        """Extract action items from report text."""
        action_items = []

        # Simple regex to find action items
        lines = report_text.split("\n")
        in_action_section = False

        for line in lines:
            if "ACTION ITEM" in line.upper():
                in_action_section = True
                continue
            if in_action_section:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    item_text = line.strip().lstrip("-*").strip()
                    if item_text:
                        # Try to extract assignee if in brackets
                        assignee = "Unassigned"
                        if item_text.startswith("["):
                            end_bracket = item_text.find("]")
                            if end_bracket > 0:
                                assignee = item_text[1:end_bracket]
                                item_text = item_text[end_bracket + 1:].strip()

                        action_items.append({
                            "task": item_text,
                            "assignee": assignee,
                            "status": "pending",
                        })
                elif line.strip() and not line.strip().startswith(("1", "2", "3", "4", "5")):
                    # End of action items section
                    if any(header in line.upper() for header in ["SUMMARY", "DECISION", "FOLLOW", "KEY"]):
                        in_action_section = False

        return action_items

    def _extract_decisions(self, report_text: str) -> list[str]:
        """Extract decisions from report text."""
        decisions = []

        lines = report_text.split("\n")
        in_decision_section = False

        for line in lines:
            if "DECISION" in line.upper():
                in_decision_section = True
                continue
            if in_decision_section:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    decision_text = line.strip().lstrip("-*").strip()
                    if decision_text:
                        decisions.append(decision_text)
                elif line.strip() and not line.strip().startswith(("1", "2", "3", "4", "5")):
                    if any(header in line.upper() for header in ["ACTION", "FOLLOW", "KEY", "SUMMARY"]):
                        in_decision_section = False

        return decisions

    def _extract_summary(self, report_text: str) -> str:
        """Extract executive summary from report text."""
        lines = report_text.split("\n")
        summary_lines = []
        in_summary = False

        for line in lines:
            if "EXECUTIVE SUMMARY" in line.upper() or "SUMMARY" in line.upper():
                in_summary = True
                continue
            if in_summary:
                if line.strip():
                    if any(header in line.upper() for header in ["KEY", "DISCUSSION", "DECISION", "ACTION"]):
                        break
                    summary_lines.append(line.strip())
                elif summary_lines:  # Empty line after content
                    break

        return " ".join(summary_lines) if summary_lines else "Summary not available."

    # ==========================================================================
    # Database Operations
    # ==========================================================================

    def create_delegation(
        self,
        user: User,
        meeting_id: str,
        meeting_title: str,
        meeting_start_time: datetime,
        meeting_end_time: datetime,
        meeting_description: str = "",
        meeting_location: str = "",
        meeting_organizer: str = "",
        meeting_attendees: list[dict] = None,
    ) -> MeetingDelegation:
        """
        Create a new meeting delegation record.

        Classifies importance and determines if auto-approval applies.
        """
        meeting_attendees = meeting_attendees or []

        # Check if delegation already exists for this meeting
        existing = self.db.query(MeetingDelegation).filter(
            MeetingDelegation.meeting_id == meeting_id,
            MeetingDelegation.user_id == user.id,
        ).first()

        if existing:
            logger.info(f"Delegation already exists for meeting {meeting_id}")
            return existing

        # Classify importance
        importance, score, reasons = self.classify_meeting_importance(
            title=meeting_title,
            description=meeting_description,
            attendees=meeting_attendees,
            organizer=meeting_organizer,
        )

        # Determine if auto-approve
        auto_approve = self.should_auto_approve(importance)
        requires_approval = not auto_approve

        # Set initial status
        if auto_approve:
            status = DelegationStatus.APPROVED
        else:
            status = DelegationStatus.PENDING

        # Generate introduction script
        introduction = self.generate_introduction_script(
            meeting_title=meeting_title,
            meeting_description=meeting_description,
            user_name=user.name,
        )

        # Create delegation record
        delegation = MeetingDelegation(
            user_id=user.id,
            organization_id=user.organization_id,
            meeting_id=meeting_id,
            meeting_title=meeting_title,
            meeting_description=meeting_description,
            meeting_start_time=meeting_start_time,
            meeting_end_time=meeting_end_time,
            meeting_location=meeting_location,
            meeting_organizer=meeting_organizer,
            meeting_attendees=meeting_attendees,
            importance=importance,
            importance_score=score,
            importance_reasons=reasons,
            status=status,
            auto_approved=auto_approve,
            requires_approval=requires_approval,
            introduction_script=introduction,
        )

        if auto_approve:
            delegation.approved_at = datetime.utcnow()

        self.db.add(delegation)
        self.db.commit()
        self.db.refresh(delegation)

        logger.info(
            f"Created delegation for '{meeting_title}' - "
            f"importance: {importance.value}, auto_approved: {auto_approve}"
        )

        return delegation

    def get_upcoming_delegations(
        self,
        user_id: int,
        organization_id: int,
        minutes_ahead: int = 60,
    ) -> list[MeetingDelegation]:
        """Get delegations for meetings starting within the specified time window."""
        now = datetime.utcnow()
        cutoff = now + timedelta(minutes=minutes_ahead)

        return self.db.query(MeetingDelegation).filter(
            MeetingDelegation.user_id == user_id,
            MeetingDelegation.organization_id == organization_id,
            MeetingDelegation.meeting_start_time >= now,
            MeetingDelegation.meeting_start_time <= cutoff,
            MeetingDelegation.status.in_([
                DelegationStatus.APPROVED,
                DelegationStatus.PENDING,
            ]),
        ).order_by(MeetingDelegation.meeting_start_time).all()

    def get_pending_delegations(
        self,
        user_id: int,
        organization_id: int,
    ) -> list[MeetingDelegation]:
        """Get all delegations pending user approval."""
        return self.db.query(MeetingDelegation).filter(
            MeetingDelegation.user_id == user_id,
            MeetingDelegation.organization_id == organization_id,
            MeetingDelegation.status == DelegationStatus.PENDING,
        ).order_by(MeetingDelegation.meeting_start_time).all()

    def approve_delegation(self, delegation_id: int, user_id: int) -> MeetingDelegation:
        """Approve a pending delegation."""
        delegation = self.db.query(MeetingDelegation).filter(
            MeetingDelegation.id == delegation_id,
            MeetingDelegation.user_id == user_id,
        ).first()

        if not delegation:
            raise ValueError(f"Delegation {delegation_id} not found")

        if delegation.status != DelegationStatus.PENDING:
            raise ValueError(f"Delegation is not pending (status: {delegation.status})")

        delegation.status = DelegationStatus.APPROVED
        delegation.approved_at = datetime.utcnow()
        delegation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(delegation)

        logger.info(f"Approved delegation {delegation_id}")
        return delegation

    def reject_delegation(
        self,
        delegation_id: int,
        user_id: int,
        reason: str = "",
    ) -> MeetingDelegation:
        """Reject a pending delegation."""
        delegation = self.db.query(MeetingDelegation).filter(
            MeetingDelegation.id == delegation_id,
            MeetingDelegation.user_id == user_id,
        ).first()

        if not delegation:
            raise ValueError(f"Delegation {delegation_id} not found")

        delegation.status = DelegationStatus.REJECTED
        delegation.error_message = reason or "User rejected delegation"
        delegation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(delegation)

        logger.info(f"Rejected delegation {delegation_id}")
        return delegation

    def join_meeting(self, delegation_id: int) -> MeetingDelegation:
        """
        Join a meeting via Nylas Notetaker.

        Should be called close to meeting start time (e.g., 5 minutes before).
        """
        delegation = self.db.query(MeetingDelegation).get(delegation_id)

        if not delegation:
            raise ValueError(f"Delegation {delegation_id} not found")

        if delegation.status != DelegationStatus.APPROVED:
            raise ValueError(f"Delegation must be approved to join (status: {delegation.status})")

        if not delegation.meeting_location:
            raise ValueError("Meeting has no location/URL to join")

        try:
            delegation.status = DelegationStatus.JOINING
            delegation.updated_at = datetime.utcnow()
            self.db.commit()

            # Create notetaker
            result = self.notetaker_service.create_notetaker(
                meeting_url=delegation.meeting_location
            )

            delegation.notetaker_id = result.get("id")
            delegation.notetaker_joined_at = datetime.utcnow()
            delegation.status = DelegationStatus.JOINED
            delegation.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(delegation)

            logger.info(f"Joined meeting for delegation {delegation_id}")
            return delegation

        except Exception as e:
            delegation.status = DelegationStatus.FAILED
            delegation.error_message = str(e)
            delegation.updated_at = datetime.utcnow()
            self.db.commit()

            logger.error(f"Failed to join meeting: {e}")
            raise

    def complete_delegation(self, delegation_id: int) -> MeetingDelegation:
        """
        Complete a delegation by fetching transcript and generating report.

        Should be called after the meeting ends.
        """
        delegation = self.db.query(MeetingDelegation).get(delegation_id)

        if not delegation:
            raise ValueError(f"Delegation {delegation_id} not found")

        if not delegation.notetaker_id:
            raise ValueError("No notetaker ID - meeting was not joined")

        try:
            # Update status to recording (or completed if meeting ended)
            delegation.status = DelegationStatus.RECORDING
            delegation.updated_at = datetime.utcnow()
            self.db.commit()

            # Fetch transcript
            transcript_data = self.notetaker_service.get_transcript(
                delegation.notetaker_id
            )
            delegation.transcript = transcript_data.get("transcript", "")

            # Fetch summary (if available from Nylas)
            try:
                summary_data = self.notetaker_service.get_summary(
                    delegation.notetaker_id
                )
                # Use Nylas summary as base, enhance with our own analysis
            except Exception:
                summary_data = {}

            # Generate comprehensive report
            report_data = self.generate_delegation_report(
                transcript=delegation.transcript,
                meeting_title=delegation.meeting_title,
                meeting_description=delegation.meeting_description or "",
                attendees=delegation.meeting_attendees or [],
            )

            delegation.report = report_data["report"]
            delegation.report_summary = report_data["summary"]
            delegation.action_items = report_data["action_items"]
            delegation.decisions = report_data["decisions"]
            delegation.status = DelegationStatus.COMPLETED
            delegation.notetaker_left_at = datetime.utcnow()
            delegation.completed_at = datetime.utcnow()
            delegation.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(delegation)

            logger.info(f"Completed delegation {delegation_id}")
            return delegation

        except Exception as e:
            delegation.error_message = str(e)
            delegation.updated_at = datetime.utcnow()
            self.db.commit()

            logger.error(f"Failed to complete delegation: {e}")
            raise

    def send_delegation_report(
        self,
        delegation_id: int,
        recipient_email: str = None,
    ) -> bool:
        """
        Send the delegation report via email.

        Args:
            delegation_id: The delegation to send report for
            recipient_email: Override recipient (default: user's email)

        Returns:
            True if sent successfully
        """
        delegation = self.db.query(MeetingDelegation).get(delegation_id)

        if not delegation:
            raise ValueError(f"Delegation {delegation_id} not found")

        if delegation.status != DelegationStatus.COMPLETED:
            raise ValueError("Delegation must be completed to send report")

        if delegation.report_sent:
            logger.info(f"Report already sent for delegation {delegation_id}")
            return True

        # Get user's email if not provided
        if not recipient_email:
            user = self.db.query(User).get(delegation.user_id)
            if user:
                recipient_email = user.email

        if not recipient_email:
            raise ValueError("No recipient email available")

        # Format email body
        email_body = self._format_report_email(delegation)

        try:
            self.email_service.send_email(
                to_email=recipient_email,
                subject=f"Meeting Report: {delegation.meeting_title}",
                body=email_body,
            )

            delegation.report_sent = True
            delegation.report_sent_at = datetime.utcnow()
            delegation.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Sent report for delegation {delegation_id} to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send report email: {e}")
            raise

    def _format_report_email(self, delegation: MeetingDelegation) -> str:
        """Format delegation report as email body."""
        lines = [
            f"Meeting Report: {delegation.meeting_title}",
            f"Date: {delegation.meeting_start_time.strftime('%Y-%m-%d %H:%M')}",
            "",
            "=" * 50,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 20,
            delegation.report_summary or "No summary available.",
            "",
            "=" * 50,
            "",
        ]

        # Add action items
        if delegation.action_items:
            lines.extend([
                "ACTION ITEMS",
                "-" * 20,
            ])
            for item in delegation.action_items:
                assignee = item.get("assignee", "Unassigned")
                task = item.get("task", "")
                lines.append(f"  [{assignee}] {task}")
            lines.append("")

        # Add decisions
        if delegation.decisions:
            lines.extend([
                "DECISIONS MADE",
                "-" * 20,
            ])
            for decision in delegation.decisions:
                lines.append(f"  - {decision}")
            lines.append("")

        # Add full report
        lines.extend([
            "=" * 50,
            "",
            "FULL REPORT",
            "-" * 20,
            delegation.report or "No detailed report available.",
            "",
            "=" * 50,
            "",
            "This report was automatically generated by your AI Meeting Assistant.",
        ])

        return "\n".join(lines)

    # ==========================================================================
    # Cron Job Functions
    # ==========================================================================

    def process_upcoming_meetings(
        self,
        user: User,
        look_ahead_hours: int = 24,
    ) -> list[MeetingDelegation]:
        """
        Process upcoming meetings for a user and create delegations.

        This should be called periodically (e.g., every 5 minutes) via cron job.

        Args:
            user: The user to process meetings for
            look_ahead_hours: How far ahead to look for meetings

        Returns:
            List of created/updated delegations
        """
        delegations = []

        try:
            # Get upcoming calendar events
            events = self.calendar_service.list_events(limit=50)

            now = datetime.utcnow()
            cutoff = now + timedelta(hours=look_ahead_hours)

            for event in events:
                # Parse event time
                when = event.get("when", {})
                start_time = when.get("start_time")
                end_time = when.get("end_time")

                if not start_time or not end_time:
                    continue

                # Convert timestamps to datetime
                if isinstance(start_time, int):
                    start_dt = datetime.utcfromtimestamp(start_time)
                    end_dt = datetime.utcfromtimestamp(end_time)
                else:
                    continue

                # Skip past meetings
                if start_dt < now:
                    continue

                # Skip meetings too far in the future
                if start_dt > cutoff:
                    continue

                # Get meeting URL from conferencing or location
                meeting_url = ""
                conferencing = event.get("conferencing")
                if conferencing:
                    details = conferencing.get("details", {})
                    meeting_url = details.get("url", "")

                if not meeting_url:
                    meeting_url = event.get("location", "")

                # Parse attendees (if available)
                attendees = []
                # Note: Nylas events may have participants field
                participants = event.get("participants", [])
                for p in participants:
                    attendees.append({
                        "email": p.get("email", ""),
                        "name": p.get("name", ""),
                    })

                # Create delegation
                delegation = self.create_delegation(
                    user=user,
                    meeting_id=event.get("id", ""),
                    meeting_title=event.get("title", "Untitled Meeting"),
                    meeting_start_time=start_dt,
                    meeting_end_time=end_dt,
                    meeting_description=event.get("description", ""),
                    meeting_location=meeting_url,
                    meeting_organizer=event.get("organizer", {}).get("email", ""),
                    meeting_attendees=attendees,
                )

                delegations.append(delegation)

            logger.info(
                f"Processed {len(delegations)} meetings for user {user.id}"
            )

        except Exception as e:
            logger.error(f"Error processing meetings: {e}")

        return delegations

    def process_meetings_to_join(
        self,
        user_id: int,
        organization_id: int,
        join_before_minutes: int = 5,
    ) -> list[MeetingDelegation]:
        """
        Find and join meetings that are about to start.

        This should be called frequently (every 1-2 minutes) via cron job.

        Args:
            user_id: User to process for
            organization_id: Organization ID
            join_before_minutes: How many minutes before meeting to join

        Returns:
            List of delegations that were joined
        """
        joined = []
        now = datetime.utcnow()
        join_window = now + timedelta(minutes=join_before_minutes)

        # Find approved delegations for meetings starting soon
        delegations = self.db.query(MeetingDelegation).filter(
            MeetingDelegation.user_id == user_id,
            MeetingDelegation.organization_id == organization_id,
            MeetingDelegation.status == DelegationStatus.APPROVED,
            MeetingDelegation.meeting_start_time <= join_window,
            MeetingDelegation.meeting_start_time >= now - timedelta(minutes=5),
            MeetingDelegation.notetaker_id.is_(None),  # Not already joined
        ).all()

        for delegation in delegations:
            try:
                self.join_meeting(delegation.id)
                joined.append(delegation)
            except Exception as e:
                logger.error(
                    f"Failed to join meeting for delegation {delegation.id}: {e}"
                )

        return joined

    def process_completed_meetings(
        self,
        user_id: int,
        organization_id: int,
    ) -> list[MeetingDelegation]:
        """
        Find and process meetings that have ended.

        This should be called periodically (every 5-10 minutes) via cron job.

        Returns:
            List of delegations that were completed
        """
        completed = []
        now = datetime.utcnow()

        # Find joined delegations where meeting has ended
        delegations = self.db.query(MeetingDelegation).filter(
            MeetingDelegation.user_id == user_id,
            MeetingDelegation.organization_id == organization_id,
            MeetingDelegation.status == DelegationStatus.JOINED,
            MeetingDelegation.meeting_end_time <= now,
            MeetingDelegation.notetaker_id.isnot(None),
        ).all()

        for delegation in delegations:
            try:
                self.complete_delegation(delegation.id)
                completed.append(delegation)

                # Send report
                try:
                    self.send_delegation_report(delegation.id)
                except Exception as e:
                    logger.error(f"Failed to send report: {e}")

            except Exception as e:
                logger.error(
                    f"Failed to complete delegation {delegation.id}: {e}"
                )

        return completed
