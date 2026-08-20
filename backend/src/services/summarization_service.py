"""
Conversation Summarization and Preference Learning Service

Automatically summarizes old conversations for long-term memory
and extracts user preferences from interactions.
"""
import logging
import re
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from groq import Groq

from backend.src.db.models import (
    Conversation,
    Message,
    ConversationSummary,
    UserPreference,
    AgentMemory,
    MemoryType,
    PreferenceCategory,
)
from backend.src.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


class SummarizationService:
    """
    Service for summarizing conversations and extracting key information.
    """

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()
        self.groq_client = None
        self._init_groq()

    def _init_groq(self):
        """Initialize Groq client for LLM operations."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.groq_client = Groq(api_key=api_key)
        else:
            logger.warning("GROQ_API_KEY not set - summarization will be limited")

    async def summarize_conversation(
        self,
        conversation_id: int,
        force: bool = False
    ) -> Optional[ConversationSummary]:
        """
        Generate a summary for a conversation.

        Args:
            conversation_id: Conversation ID
            force: Force regeneration even if summary exists

        Returns:
            ConversationSummary or None
        """
        # Get conversation and messages
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            return None

        # Check if summary already exists
        if not force:
            existing = self.db.query(ConversationSummary).filter(
                ConversationSummary.conversation_id == conversation_id
            ).first()
            if existing:
                return existing

        # Get messages
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        if not messages or len(messages) < 3:
            logger.info(f"Conversation {conversation_id} too short to summarize")
            return None

        # Generate summary using LLM
        summary_data = await self._generate_summary_with_llm(messages)
        if not summary_data:
            return None

        # Generate embedding for the summary
        embedding = self.embedding_service.generate_embedding(summary_data["summary"])
        serialized_embedding = EmbeddingService.serialize_embedding(embedding)

        # Create or update summary
        summary = ConversationSummary(
            conversation_id=conversation_id,
            user_id=conversation.user_id,
            agent_id=conversation.agent_id,
            summary=summary_data["summary"],
            key_topics=summary_data.get("topics", []),
            key_entities=summary_data.get("entities", []),
            action_items=summary_data.get("action_items", []),
            decisions=summary_data.get("decisions", []),
            embedding=serialized_embedding,
            message_count=len(messages),
            start_message_id=messages[0].id,
            end_message_id=messages[-1].id,
            time_range_start=messages[0].created_at,
            time_range_end=messages[-1].created_at,
        )

        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)

        logger.info(f"Generated summary for conversation {conversation_id}")
        return summary

    async def _generate_summary_with_llm(
        self,
        messages: List[Message]
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to generate conversation summary.

        Args:
            messages: List of Message objects

        Returns:
            Dict with summary, topics, entities, action_items, decisions
        """
        if not self.groq_client:
            # Fallback to simple extraction
            return self._simple_summary(messages)

        # Format messages for LLM
        formatted = []
        for msg in messages:
            formatted.append(f"{msg.role.upper()}: {msg.content}")
        conversation_text = "\n".join(formatted)

        prompt = f"""Analyze this conversation and provide a structured summary.

CONVERSATION:
{conversation_text[:8000]}

Provide your response in this exact format:

SUMMARY:
[2-3 sentence summary of the conversation]

TOPICS:
- [topic 1]
- [topic 2]

ENTITIES:
- [name: description]

ACTION_ITEMS:
- [action item]

DECISIONS:
- [decision made]

Only include sections that have content. Be concise and specific."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content
            return self._parse_summary_response(result_text)

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return self._simple_summary(messages)

    def _parse_summary_response(self, text: str) -> Dict[str, Any]:
        """Parse LLM summary response into structured data."""
        result = {
            "summary": "",
            "topics": [],
            "entities": [],
            "action_items": [],
            "decisions": []
        }

        current_section = None
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if line.startswith("SUMMARY:"):
                current_section = "summary"
                continue
            elif line.startswith("TOPICS:"):
                current_section = "topics"
                continue
            elif line.startswith("ENTITIES:"):
                current_section = "entities"
                continue
            elif line.startswith("ACTION_ITEMS:"):
                current_section = "action_items"
                continue
            elif line.startswith("DECISIONS:"):
                current_section = "decisions"
                continue

            # Add content to current section
            if current_section == "summary":
                result["summary"] += " " + line
            elif current_section in ["topics", "entities", "action_items", "decisions"]:
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    result[current_section].append(line)

        result["summary"] = result["summary"].strip()
        return result

    def _simple_summary(self, messages: List[Message]) -> Dict[str, Any]:
        """Simple summary without LLM - extract key info."""
        # Get first and last messages for context
        user_messages = [m for m in messages if m.role == "user"]

        summary_parts = []
        if user_messages:
            summary_parts.append(f"User discussed: {user_messages[0].content[:100]}")
            if len(user_messages) > 1:
                summary_parts.append(f"Later asked about: {user_messages[-1].content[:100]}")

        return {
            "summary": " ".join(summary_parts) if summary_parts else "Conversation without clear topic",
            "topics": [],
            "entities": [],
            "action_items": [],
            "decisions": []
        }

    async def summarize_old_conversations(
        self,
        age_hours: int = 24,
        limit: int = 50
    ) -> int:
        """
        Summarize conversations older than specified age.

        Args:
            age_hours: Minimum age in hours
            limit: Maximum conversations to process

        Returns:
            Number of conversations summarized
        """
        cutoff = datetime.utcnow() - timedelta(hours=age_hours)

        # Find conversations without summaries
        conversations = self.db.query(Conversation).outerjoin(
            ConversationSummary
        ).filter(
            and_(
                Conversation.updated_at < cutoff,
                ConversationSummary.id.is_(None)
            )
        ).limit(limit).all()

        count = 0
        for conv in conversations:
            try:
                summary = await self.summarize_conversation(conv.id)
                if summary:
                    count += 1
            except Exception as e:
                logger.error(f"Failed to summarize conversation {conv.id}: {e}")

        logger.info(f"Summarized {count} old conversations")
        return count


class PreferenceLearningService:
    """
    Service for learning user preferences from interactions.
    """

    def __init__(self, db: Session):
        self.db = db
        self.groq_client = None
        self._init_groq()

        # Patterns for detecting preferences
        self.preference_patterns = {
            PreferenceCategory.SCHEDULING: [
                r"(?:prefer|like|want)\s+(?:meetings?\s+)?(?:at|around|in the)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
                r"(?:morning|afternoon|evening)\s+(?:works|is)\s+(?:best|better|good)",
                r"(?:don't|do not)\s+schedule\s+(?:anything\s+)?(?:before|after)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            ],
            PreferenceCategory.COMMUNICATION: [
                r"(?:prefer|like)\s+(?:to\s+)?(?:be\s+)?(?:contacted|reached)\s+(?:via|by|through)\s+(\w+)",
                r"(?:email|call|text|message)\s+(?:is|works)\s+(?:best|better)",
            ],
            PreferenceCategory.PERSONAL: [
                r"(?:my|i'm in|located in)\s+timezone\s+(?:is\s+)?([A-Z]{2,4}(?:/[A-Za-z_]+)?)",
                r"(?:i\s+)?work\s+(?:from\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+to\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            ],
        }

        # Correction patterns
        self.correction_patterns = [
            r"(?:no|not|actually|wait),?\s+(?:i\s+)?(?:meant|prefer|want)\s+(.+)",
            r"(?:change|update)\s+(?:that|it)\s+to\s+(.+)",
            r"(?:make\s+it|should\s+be)\s+(.+?)(?:\s+instead)?",
        ]

    def _init_groq(self):
        """Initialize Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.groq_client = Groq(api_key=api_key)

    async def extract_preferences_from_message(
        self,
        user_id: int,
        organization_id: int,
        message_content: str,
        message_id: int,
        previous_message: Optional[str] = None
    ) -> List[UserPreference]:
        """
        Extract preferences from a user message.

        Args:
            user_id: User ID
            organization_id: Organization ID
            message_content: Message content
            message_id: Message ID
            previous_message: Previous assistant message (for context)

        Returns:
            List of extracted preferences
        """
        preferences = []

        # Pattern-based extraction
        for category, patterns in self.preference_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        pref = await self._store_preference_from_match(
                            user_id=user_id,
                            organization_id=organization_id,
                            category=category,
                            match=match,
                            message_id=message_id,
                            source_type="pattern"
                        )
                        if pref:
                            preferences.append(pref)

        # Check for corrections
        if previous_message:
            correction_prefs = await self._detect_corrections(
                user_id=user_id,
                organization_id=organization_id,
                message_content=message_content,
                message_id=message_id,
                previous_message=previous_message
            )
            preferences.extend(correction_prefs)

        # LLM-based extraction for complex preferences
        if self.groq_client and not preferences:
            llm_prefs = await self._extract_with_llm(
                user_id=user_id,
                organization_id=organization_id,
                message_content=message_content,
                message_id=message_id
            )
            preferences.extend(llm_prefs)

        return preferences

    async def _store_preference_from_match(
        self,
        user_id: int,
        organization_id: int,
        category: PreferenceCategory,
        match: str,
        message_id: int,
        source_type: str
    ) -> Optional[UserPreference]:
        """Store a preference extracted from pattern match."""
        from backend.src.services.memory_service import MemoryService
        memory_service = MemoryService(self.db)

        # Generate preference key based on category and match
        if isinstance(match, tuple):
            match = " to ".join(match)

        key = f"{category.value}_preference_{hash(match) % 10000}"

        return await memory_service.store_preference(
            user_id=user_id,
            organization_id=organization_id,
            category=category,
            preference_key=key,
            preference_value=match,
            source_type=source_type,
            source_message_id=message_id,
            confidence=0.6
        )

    async def _detect_corrections(
        self,
        user_id: int,
        organization_id: int,
        message_content: str,
        message_id: int,
        previous_message: str
    ) -> List[UserPreference]:
        """Detect when user is correcting the AI."""
        preferences = []

        for pattern in self.correction_patterns:
            matches = re.findall(pattern, message_content, re.IGNORECASE)
            if matches:
                # User is correcting something - try to identify what
                for match in matches:
                    # This is a correction - store with high confidence
                    # Try to categorize the correction
                    category = self._categorize_correction(match, previous_message)
                    if category:
                        from backend.src.services.memory_service import MemoryService
                        memory_service = MemoryService(self.db)

                        pref = await memory_service.store_preference(
                            user_id=user_id,
                            organization_id=organization_id,
                            category=category,
                            preference_key=f"correction_{message_id}",
                            preference_value=match,
                            source_type="correction",
                            source_message_id=message_id,
                            confidence=0.8  # Higher confidence for corrections
                        )
                        if pref:
                            preferences.append(pref)

        return preferences

    def _categorize_correction(
        self,
        correction: str,
        previous_message: str
    ) -> Optional[PreferenceCategory]:
        """Categorize a correction based on context."""
        lower_correction = correction.lower()
        lower_prev = previous_message.lower() if previous_message else ""

        # Check for time-related corrections
        if any(word in lower_prev or word in lower_correction
               for word in ["meeting", "schedule", "time", "calendar"]):
            return PreferenceCategory.SCHEDULING

        # Check for communication corrections
        if any(word in lower_prev or word in lower_correction
               for word in ["email", "call", "message", "contact"]):
            return PreferenceCategory.COMMUNICATION

        # Default to workflow
        return PreferenceCategory.WORKFLOW

    async def _extract_with_llm(
        self,
        user_id: int,
        organization_id: int,
        message_content: str,
        message_id: int
    ) -> List[UserPreference]:
        """Use LLM to extract complex preferences."""
        if not self.groq_client:
            return []

        # Only use LLM for messages that seem to contain preferences
        if len(message_content) < 20 or not any(
            word in message_content.lower()
            for word in ["prefer", "like", "want", "usually", "always", "never", "don't"]
        ):
            return []

        prompt = f"""Analyze this message for user preferences that should be remembered for future interactions.

MESSAGE: "{message_content}"

If there are preferences, output them in this format (one per line):
CATEGORY: VALUE
Where CATEGORY is one of: scheduling, communication, workflow, personal

If there are no clear preferences, output: NONE

Examples:
- "I prefer meetings in the afternoon" -> scheduling: afternoon meetings
- "Email works best for me" -> communication: prefer email
- "I usually work from 9 to 5" -> personal: work hours 9-5"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )

            result = response.choices[0].message.content.strip()
            if result.upper() == "NONE":
                return []

            return await self._parse_llm_preferences(
                result, user_id, organization_id, message_id
            )

        except Exception as e:
            logger.error(f"LLM preference extraction failed: {e}")
            return []

    async def _parse_llm_preferences(
        self,
        text: str,
        user_id: int,
        organization_id: int,
        message_id: int
    ) -> List[UserPreference]:
        """Parse LLM preference extraction results."""
        preferences = []
        from backend.src.services.memory_service import MemoryService
        memory_service = MemoryService(self.db)

        category_map = {
            "scheduling": PreferenceCategory.SCHEDULING,
            "communication": PreferenceCategory.COMMUNICATION,
            "workflow": PreferenceCategory.WORKFLOW,
            "personal": PreferenceCategory.PERSONAL,
            "tool": PreferenceCategory.TOOL,
        }

        for line in text.strip().split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    cat_str = parts[0].strip().lower()
                    value = parts[1].strip()

                    category = category_map.get(cat_str)
                    if category and value:
                        pref = await memory_service.store_preference(
                            user_id=user_id,
                            organization_id=organization_id,
                            category=category,
                            preference_key=f"llm_extracted_{message_id}_{cat_str}",
                            preference_value=value,
                            source_type="llm_inferred",
                            source_message_id=message_id,
                            confidence=0.5
                        )
                        if pref:
                            preferences.append(pref)

        return preferences

    async def process_conversation_for_learning(
        self,
        conversation_id: int
    ) -> Dict[str, Any]:
        """
        Process an entire conversation to extract preferences.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dict with extraction results
        """
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            return {"error": "Conversation not found"}

        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        results = {
            "conversation_id": conversation_id,
            "messages_processed": len(messages),
            "preferences_extracted": []
        }

        previous_message = None
        for msg in messages:
            if msg.role == "user":
                prefs = await self.extract_preferences_from_message(
                    user_id=conversation.user_id,
                    organization_id=conversation.agent.organization_id,
                    message_content=msg.content,
                    message_id=msg.id,
                    previous_message=previous_message
                )
                results["preferences_extracted"].extend([
                    {"key": p.preference_key, "value": p.preference_value}
                    for p in prefs
                ])
            else:
                previous_message = msg.content

        return results
