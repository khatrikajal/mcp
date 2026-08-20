"""
Memory Service for Agent Memory Management

Provides vector-based semantic search across agent memories,
conversation history, meeting summaries, and email content.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.src.db.models import (
    AgentMemory,
    UserPreference,
    ConversationSummary,
    MemorySearchLog,
    MemoryType,
    PreferenceCategory,
    Conversation,
    Message,
)
from backend.src.services.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for managing agent memories with vector-based semantic search.
    """

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()

    # ==================== Memory CRUD ====================

    async def store_memory(
        self,
        agent_id: int,
        user_id: int,
        organization_id: int,
        memory_type: MemoryType,
        key: str,
        content: str,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        source_id: Optional[int] = None,
        importance: float = 0.5,
        expires_at: Optional[datetime] = None
    ) -> AgentMemory:
        """
        Store a new memory with embedding.

        Args:
            agent_id: Agent this memory belongs to
            user_id: User who owns this memory
            organization_id: Organization context
            memory_type: Type of memory (preference, fact, etc.)
            key: Unique identifier for this memory
            content: The actual content to remember
            summary: Optional summarized version
            source: Source of memory (conversation, meeting, etc.)
            source_id: ID of source record
            importance: Importance score (0-1)
            expires_at: Optional expiration time

        Returns:
            Created AgentMemory object
        """
        # Generate embedding for the content
        embedding = self.embedding_service.generate_embedding(content)
        serialized_embedding = EmbeddingService.serialize_embedding(embedding)

        memory = AgentMemory(
            agent_id=agent_id,
            user_id=user_id,
            organization_id=organization_id,
            memory_type=memory_type,
            key=key,
            content=content,
            summary=summary,
            embedding=serialized_embedding,
            source=source,
            source_id=source_id,
            importance=importance,
            expires_at=expires_at,
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        logger.info(f"Stored memory {memory.id} for agent {agent_id}: {key}")
        return memory

    async def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        importance: Optional[float] = None
    ) -> Optional[AgentMemory]:
        """
        Update an existing memory.

        Args:
            memory_id: ID of memory to update
            content: New content (regenerates embedding if provided)
            summary: New summary
            importance: New importance score

        Returns:
            Updated AgentMemory or None
        """
        memory = self.db.query(AgentMemory).filter(AgentMemory.id == memory_id).first()
        if not memory:
            return None

        if content:
            memory.content = content
            # Regenerate embedding
            embedding = self.embedding_service.generate_embedding(content)
            memory.embedding = EmbeddingService.serialize_embedding(embedding)

        if summary is not None:
            memory.summary = summary

        if importance is not None:
            memory.importance = max(0.0, min(1.0, importance))

        memory.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(memory)

        return memory

    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        memory = self.db.query(AgentMemory).filter(AgentMemory.id == memory_id).first()
        if not memory:
            return False

        self.db.delete(memory)
        self.db.commit()
        return True

    async def get_memory(self, memory_id: int) -> Optional[AgentMemory]:
        """Get a single memory by ID."""
        return self.db.query(AgentMemory).filter(AgentMemory.id == memory_id).first()

    async def get_memories_by_agent(
        self,
        agent_id: int,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100,
        include_expired: bool = False
    ) -> List[AgentMemory]:
        """
        Get memories for an agent.

        Args:
            agent_id: Agent ID
            memory_type: Optional filter by type
            limit: Maximum number of results
            include_expired: Include expired memories

        Returns:
            List of AgentMemory objects
        """
        query = self.db.query(AgentMemory).filter(AgentMemory.agent_id == agent_id)

        if memory_type:
            query = query.filter(AgentMemory.memory_type == memory_type)

        if not include_expired:
            query = query.filter(
                or_(
                    AgentMemory.expires_at.is_(None),
                    AgentMemory.expires_at > datetime.utcnow()
                )
            )

        return query.order_by(desc(AgentMemory.importance), desc(AgentMemory.created_at)).limit(limit).all()

    # ==================== Semantic Search ====================

    async def search_memories(
        self,
        query: str,
        agent_id: int,
        user_id: int,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 10,
        threshold: float = 0.3,
        include_expired: bool = False
    ) -> List[Tuple[AgentMemory, float]]:
        """
        Semantic search across agent memories.

        Args:
            query: Search query
            agent_id: Agent ID to search within
            user_id: User ID for logging
            memory_types: Optional filter by memory types
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            include_expired: Include expired memories

        Returns:
            List of (AgentMemory, similarity_score) tuples
        """
        import time
        start_time = time.time()

        # Generate query embedding
        query_embedding = self.embedding_service.get_embedding_for_search(query)
        if query_embedding is None:
            logger.warning("Failed to generate query embedding")
            return []

        # Get all candidate memories
        mem_query = self.db.query(AgentMemory).filter(
            AgentMemory.agent_id == agent_id,
            AgentMemory.embedding.isnot(None)
        )

        if memory_types:
            mem_query = mem_query.filter(AgentMemory.memory_type.in_(memory_types))

        if not include_expired:
            mem_query = mem_query.filter(
                or_(
                    AgentMemory.expires_at.is_(None),
                    AgentMemory.expires_at > datetime.utcnow()
                )
            )

        candidates = mem_query.all()

        if not candidates:
            return []

        # Calculate similarities
        results = []
        for memory in candidates:
            candidate_embedding = EmbeddingService.deserialize_embedding(memory.embedding)
            if candidate_embedding is not None:
                similarity = self.embedding_service.cosine_similarity(
                    query_embedding, candidate_embedding
                )
                if similarity >= threshold:
                    results.append((memory, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]

        # Log the search
        search_time_ms = int((time.time() - start_time) * 1000)
        await self._log_search(
            user_id=user_id,
            agent_id=agent_id,
            query=query,
            query_embedding=query_embedding,
            results=results,
            search_time_ms=search_time_ms
        )

        # Update access counts
        for memory, _ in results:
            memory.access_count += 1
            memory.last_accessed = datetime.utcnow()
        self.db.commit()

        return results

    async def _log_search(
        self,
        user_id: int,
        agent_id: int,
        query: str,
        query_embedding,
        results: List[Tuple[AgentMemory, float]],
        search_time_ms: int
    ):
        """Log a memory search for analytics."""
        log = MemorySearchLog(
            user_id=user_id,
            agent_id=agent_id,
            query=query,
            query_embedding=EmbeddingService.serialize_embedding(query_embedding),
            result_count=len(results),
            top_result_ids=[m.id for m, _ in results[:5]],
            search_time_ms=search_time_ms,
        )
        self.db.add(log)
        self.db.commit()

    # ==================== Preference Management ====================

    async def store_preference(
        self,
        user_id: int,
        organization_id: int,
        category: PreferenceCategory,
        preference_key: str,
        preference_value: str,
        source_type: str = "inferred",
        source_message_id: Optional[int] = None,
        confidence: float = 0.5
    ) -> UserPreference:
        """
        Store or update a user preference.

        Args:
            user_id: User ID
            organization_id: Organization ID
            category: Preference category
            preference_key: Preference identifier
            preference_value: Preference value
            source_type: How preference was learned
            source_message_id: Message where learned
            confidence: Confidence score (0-1)

        Returns:
            UserPreference object
        """
        # Check if preference already exists
        existing = self.db.query(UserPreference).filter(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.category == category,
                UserPreference.preference_key == preference_key
            )
        ).first()

        if existing:
            # Update existing preference
            if existing.preference_value == preference_value:
                existing.times_confirmed += 1
                existing.confidence = min(1.0, existing.confidence + 0.1)
            else:
                # Value changed - update with new value
                existing.preference_value = preference_value
                existing.times_contradicted += 1
                existing.confidence = max(0.0, existing.confidence - 0.1)

            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new preference
        preference = UserPreference(
            user_id=user_id,
            organization_id=organization_id,
            category=category,
            preference_key=preference_key,
            preference_value=preference_value,
            source_type=source_type,
            source_message_id=source_message_id,
            confidence=confidence,
        )

        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)

        logger.info(f"Stored preference for user {user_id}: {preference_key} = {preference_value}")
        return preference

    async def get_preferences(
        self,
        user_id: int,
        category: Optional[PreferenceCategory] = None,
        min_confidence: float = 0.0
    ) -> List[UserPreference]:
        """
        Get user preferences.

        Args:
            user_id: User ID
            category: Optional category filter
            min_confidence: Minimum confidence threshold

        Returns:
            List of UserPreference objects
        """
        query = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.is_active == True,
            UserPreference.confidence >= min_confidence
        )

        if category:
            query = query.filter(UserPreference.category == category)

        query = query.filter(
            or_(
                UserPreference.expires_at.is_(None),
                UserPreference.expires_at > datetime.utcnow()
            )
        )

        return query.order_by(desc(UserPreference.confidence)).all()

    async def get_preference_value(
        self,
        user_id: int,
        category: PreferenceCategory,
        preference_key: str
    ) -> Optional[str]:
        """
        Get a specific preference value.

        Args:
            user_id: User ID
            category: Preference category
            preference_key: Preference key

        Returns:
            Preference value or None
        """
        pref = self.db.query(UserPreference).filter(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.category == category,
                UserPreference.preference_key == preference_key,
                UserPreference.is_active == True
            )
        ).first()

        return pref.preference_value if pref else None

    # ==================== Context Retrieval ====================

    async def get_agent_context(
        self,
        agent_id: int,
        user_id: int,
        max_memories: int = 10,
        include_preferences: bool = True
    ) -> Dict[str, Any]:
        """
        Get context for an agent to use in conversation.

        Args:
            agent_id: Agent ID
            user_id: User ID
            max_memories: Max memories to include
            include_preferences: Include user preferences

        Returns:
            Dict with memories and preferences
        """
        context = {
            "memories": [],
            "preferences": [],
            "recent_topics": []
        }

        # Get recent high-importance memories
        memories = await self.get_memories_by_agent(
            agent_id=agent_id,
            limit=max_memories
        )

        for memory in memories:
            context["memories"].append({
                "type": memory.memory_type.value,
                "key": memory.key,
                "content": memory.summary or memory.content[:500],
                "importance": memory.importance
            })

        # Get user preferences
        if include_preferences:
            preferences = await self.get_preferences(
                user_id=user_id,
                min_confidence=0.3
            )

            for pref in preferences[:10]:
                context["preferences"].append({
                    "category": pref.category.value,
                    "key": pref.preference_key,
                    "value": pref.preference_value,
                    "confidence": pref.confidence
                })

        return context

    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format context dict as text for system prompt injection.

        Args:
            context: Context from get_agent_context

        Returns:
            Formatted text string
        """
        lines = []

        if context.get("preferences"):
            lines.append("## User Preferences")
            for pref in context["preferences"]:
                lines.append(f"- {pref['key']}: {pref['value']}")
            lines.append("")

        if context.get("memories"):
            lines.append("## Relevant Memories")
            for memory in context["memories"]:
                lines.append(f"- [{memory['type']}] {memory['key']}: {memory['content'][:200]}")
            lines.append("")

        return "\n".join(lines) if lines else ""

    # ==================== Cleanup ====================

    async def cleanup_expired_memories(self) -> int:
        """
        Delete expired memories.

        Returns:
            Number of memories deleted
        """
        result = self.db.query(AgentMemory).filter(
            AgentMemory.expires_at <= datetime.utcnow()
        ).delete()

        self.db.commit()
        logger.info(f"Cleaned up {result} expired memories")
        return result

    async def get_memory_stats(self, agent_id: int) -> Dict[str, Any]:
        """
        Get memory statistics for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dict with memory stats
        """
        from sqlalchemy import func

        # Count by type
        type_counts = self.db.query(
            AgentMemory.memory_type,
            func.count(AgentMemory.id)
        ).filter(
            AgentMemory.agent_id == agent_id
        ).group_by(AgentMemory.memory_type).all()

        # Total count
        total = self.db.query(func.count(AgentMemory.id)).filter(
            AgentMemory.agent_id == agent_id
        ).scalar()

        # Average importance
        avg_importance = self.db.query(func.avg(AgentMemory.importance)).filter(
            AgentMemory.agent_id == agent_id
        ).scalar()

        return {
            "total_memories": total or 0,
            "by_type": {t.value: c for t, c in type_counts},
            "average_importance": float(avg_importance) if avg_importance else 0.0,
        }
