"""
Agent Executor - Connects database agents with MCP chat service.

This service:
1. Loads agent configuration from database
2. Filters tools based on agent permissions
3. Executes chat via MCP server
4. Returns AI responses
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os

# Add client to path to import chat_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from client.chat_service import chat as mcp_chat
from server.database.models import Agent, Message, AgentToolPermission, PermissionLevel


class AgentExecutor:
    """
    Executes chat messages with agent-specific configuration.
    """

    def __init__(self, agent: Agent, db: Session):
        self.agent = agent
        self.db = db

        # Load tool permissions
        self.tool_permissions = {
            perm.tool_name: perm.permission_level
            for perm in agent.tool_permissions
        }

    def get_enabled_tools(self) -> List[str]:
        """
        Get list of enabled tool names for this agent.
        Maps tool names to category IDs for the MCP chat service.
        """
        # Map tool names to their category IDs
        tool_to_category = {
            "get_current_datetime": "datetime",
            "list_calendar_events": "calendar",
            "create_calendar_event": "calendar",
            "get_weather": "weather",
            "send_email": "email",
            "join_next_meeting": "meeting",
            "join_meeting": "meeting",
            "get_notetaker_status": "notetaker",
            "list_notetakers": "notetaker",
            "get_meeting_transcript": "notetaker",
            "get_meeting_summary": "notetaker",
        }

        # Get enabled categories (tools that are not disabled)
        enabled_categories = set()
        for tool_name, permission in self.tool_permissions.items():
            if permission != PermissionLevel.DISABLED:
                category = tool_to_category.get(tool_name)
                if category:
                    enabled_categories.add(category)

        return list(enabled_categories)

    def get_system_instructions(self) -> str:
        """
        Get system instructions for this agent.
        """
        return self.agent.system_instructions or "You are a helpful AI assistant."

    async def process_message(self, conversation_id: int, user_message: str) -> str:
        """
        Process a user message and return the AI response.

        Args:
            conversation_id: The conversation ID
            user_message: The user's message text

        Returns:
            AI response text
        """
        # Load conversation history from database
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

        # Convert to chat format
        history = []

        # Add system message with agent instructions
        history.append({
            "role": "system",
            "content": self.get_system_instructions()
        })

        # Add conversation history (excluding the just-saved user message)
        for msg in messages:
            if msg.content != user_message:  # Don't duplicate the current message
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add current user message
        history.append({
            "role": "user",
            "content": user_message
        })

        # Get enabled tools for this agent
        enabled_tools = self.get_enabled_tools()

        # Call MCP chat service
        try:
            result = await mcp_chat(history, active_tools=enabled_tools if enabled_tools else None)

            # Extract message from result
            if isinstance(result, dict):
                response_text = result.get("message", "")

                # Check for pending action (requires approval)
                if "pending_action" in result:
                    pending = result["pending_action"]
                    response_text += (
                        f"\n\n⚠️ This action requires approval:\n"
                        f"Tool: {pending['tool']}\n"
                        f"Description: {pending['description']}\n\n"
                        f"Reply 'yes' to confirm or 'no' to cancel."
                    )

                return response_text
            else:
                return str(result)

        except Exception as e:
            return f"Error processing message: {str(e)}"
