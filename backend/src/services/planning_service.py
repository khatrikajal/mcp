"""
Planning Service - LangGraph-based multi-step planning workflows.

This service implements:
1. Analyze user request and create execution plan
2. Validate plan for approval requirements
3. Execute plan step-by-step with state management
4. Handle approval gates
5. Synthesize final results
"""
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session
from datetime import datetime
import json

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.src.db.models import (
    ExecutionPlan,
    PlanStatus,
    StepStatus,
    Agent,
    AgentToolPermission,
    PermissionLevel,
    Conversation
)
from backend.src.services.approval_service import ApprovalService
from backend.src.core.config import GROQ_API_KEY


class PlanState(TypedDict):
    """State for planning workflow"""
    user_request: str
    agent_id: int
    conversation_id: int
    user_id: int

    # Planning
    analysis: str
    plan: List[Dict[str, Any]]
    validated: bool

    # Execution
    current_step: int
    step_results: List[Dict[str, Any]]
    waiting_approval: bool
    approval_request_id: Optional[int]

    # Final
    final_result: str
    error: Optional[str]


class PlanningService:
    """Orchestrates multi-step planning workflows using LangGraph."""

    def __init__(self, db: Session):
        self.db = db
        self.approval_service = ApprovalService(db)
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile"
        )
        self.checkpointer = MemorySaver()

    def _get_agent_tools(self, agent_id: int) -> Dict[str, PermissionLevel]:
        """Get agent's tool permissions."""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {}

        return {
            perm.tool_name: perm.permission_level
            for perm in agent.tool_permissions
        }

    async def analyze_request(self, state: PlanState) -> PlanState:
        """Analyze user request and understand intent."""

        # Get agent tools
        tools = self._get_agent_tools(state["agent_id"])
        tool_list = list(tools.keys())

        prompt = f"""Analyze this user request and break it down into actionable components:

User Request: {state["user_request"]}

Available Tools: {", ".join(tool_list)}

Provide a brief analysis of:
1. What the user wants to accomplish
2. Which tools might be needed
3. The general sequence of operations

Keep your analysis concise (2-3 sentences)."""

        messages = [
            SystemMessage(content="You are an AI planning assistant."),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        state["analysis"] = response.content
        return state

    async def create_plan(self, state: PlanState) -> PlanState:
        """Create detailed step-by-step execution plan."""

        tools = self._get_agent_tools(state["agent_id"])
        tool_descriptions = {
            "get_current_datetime": "Get current date and time",
            "list_calendar_events": "List calendar events",
            "create_calendar_event": "Create a new calendar event",
            "get_weather": "Get weather information",
            "send_email": "Send an email",
            "join_next_meeting": "Join the next scheduled meeting",
            "join_meeting": "Join a specific meeting",
            "get_notetaker_status": "Get status of meeting notetaker",
            "list_notetakers": "List all active notetakers",
            "get_meeting_transcript": "Get transcript from a meeting",
            "get_meeting_summary": "Get summary of a meeting"
        }

        available_tools_desc = "\n".join([
            f"- {tool}: {tool_descriptions.get(tool, 'No description')}"
            for tool in tools.keys()
        ])

        prompt = f"""Create a detailed step-by-step execution plan for this request:

User Request: {state["user_request"]}
Analysis: {state["analysis"]}

Available Tools:
{available_tools_desc}

Create a plan as a JSON array of steps. Each step should have:
- step_number: integer
- description: what this step does
- tool: tool name to use
- arguments: estimated arguments (can use placeholders like {{previous_step_result}})
- requires_approval: true if this is a sensitive action

Example format:
[
  {{
    "step_number": 1,
    "description": "Get current date and time",
    "tool": "get_current_datetime",
    "arguments": {{}},
    "requires_approval": false
  }},
  {{
    "step_number": 2,
    "description": "Send summary email",
    "tool": "send_email",
    "arguments": {{"to": "user@example.com", "subject": "Summary", "body": "..."}},
    "requires_approval": true
  }}
]

Return ONLY the JSON array, no explanation."""

        messages = [
            SystemMessage(content="You are an AI planning assistant that creates executable plans."),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse JSON plan
        try:
            plan_text = response.content.strip()
            # Remove markdown code blocks if present
            if plan_text.startswith("```"):
                plan_text = plan_text.split("```")[1]
                if plan_text.startswith("json"):
                    plan_text = plan_text[4:]
                plan_text = plan_text.strip()

            plan = json.loads(plan_text)
            state["plan"] = plan
        except json.JSONDecodeError as e:
            state["error"] = f"Failed to parse plan: {str(e)}"
            state["plan"] = []

        return state

    async def validate_plan(self, state: PlanState) -> PlanState:
        """Validate plan and check for approval requirements."""

        if state.get("error"):
            state["validated"] = False
            return state

        tools = self._get_agent_tools(state["agent_id"])

        # Check each step
        for step in state["plan"]:
            tool_name = step.get("tool")

            # Check if tool exists in agent permissions
            if tool_name not in tools:
                state["error"] = f"Step {step['step_number']}: Tool '{tool_name}' not available for this agent"
                state["validated"] = False
                return state

            # Check if requires approval based on permission level
            permission_level = tools[tool_name]
            if permission_level == PermissionLevel.REQUIRES_APPROVAL:
                step["requires_approval"] = True
            elif permission_level == PermissionLevel.DISABLED:
                state["error"] = f"Step {step['step_number']}: Tool '{tool_name}' is disabled"
                state["validated"] = False
                return state

        state["validated"] = True
        state["current_step"] = 0
        state["step_results"] = []
        state["waiting_approval"] = False

        return state

    async def execute_step(self, state: PlanState) -> PlanState:
        """Execute current step in the plan."""

        if state["current_step"] >= len(state["plan"]):
            # All steps completed
            return state

        current_plan_step = state["plan"][state["current_step"]]

        # Check if step requires approval
        if current_plan_step.get("requires_approval", False):
            # Create approval request
            approval = self.approval_service.create_approval_request(
                user_id=state["user_id"],
                agent_id=state["agent_id"],
                tool_name=current_plan_step["tool"],
                tool_arguments=current_plan_step.get("arguments", {}),
                description=current_plan_step["description"],
                step_index=state["current_step"]
            )

            state["waiting_approval"] = True
            state["approval_request_id"] = approval.id

            return state

        # Execute step (tool execution would happen here)
        # For now, we'll simulate execution
        try:
            # Import MCP chat service for tool execution
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

            from client.chat_service import execute_tool

            result = await execute_tool(
                tool_name=current_plan_step["tool"],
                arguments=current_plan_step.get("arguments", {})
            )

            state["step_results"].append({
                "step_number": state["current_step"],
                "status": "completed",
                "result": result
            })

            state["current_step"] += 1

        except Exception as e:
            state["step_results"].append({
                "step_number": state["current_step"],
                "status": "failed",
                "error": str(e)
            })
            state["error"] = f"Step {state['current_step']} failed: {str(e)}"

        return state

    async def check_approval(self, state: PlanState) -> PlanState:
        """Check if approval has been granted."""

        if not state.get("waiting_approval"):
            return state

        if not state.get("approval_request_id"):
            return state

        approval = self.approval_service.get_approval_request(
            state["approval_request_id"]
        )

        if not approval:
            state["error"] = "Approval request not found"
            return state

        from backend.src.db.models import ApprovalStatus

        if approval.status == ApprovalStatus.APPROVED:
            # Execute the approved action
            result = await self.approval_service.execute_approved_action(approval)

            state["step_results"].append({
                "step_number": state["current_step"],
                "status": "completed",
                "result": result
            })

            state["current_step"] += 1
            state["waiting_approval"] = False
            state["approval_request_id"] = None

        elif approval.status == ApprovalStatus.REJECTED:
            state["step_results"].append({
                "step_number": state["current_step"],
                "status": "rejected",
                "reason": approval.rejection_reason
            })
            state["error"] = f"Step {state['current_step']} rejected by user"
            state["waiting_approval"] = False

        elif approval.status == ApprovalStatus.EXPIRED:
            state["error"] = f"Approval for step {state['current_step']} expired"
            state["waiting_approval"] = False

        return state

    async def synthesize_results(self, state: PlanState) -> PlanState:
        """Synthesize final results from all steps."""

        if state.get("error"):
            state["final_result"] = f"Plan execution failed: {state['error']}"
            return state

        # Create summary of all step results
        results_summary = []
        for result in state["step_results"]:
            step_plan = state["plan"][result["step_number"]]
            results_summary.append(
                f"Step {result['step_number'] + 1}: {step_plan['description']} - "
                f"{result['status']}"
            )

        prompt = f"""Summarize the results of this plan execution:

Original Request: {state["user_request"]}

Steps Executed:
{chr(10).join(results_summary)}

Provide a concise summary (2-3 sentences) of what was accomplished."""

        messages = [
            SystemMessage(content="You are an AI assistant that summarizes task results."),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)
        state["final_result"] = response.content

        return state

    def should_continue(self, state: PlanState) -> str:
        """Determine next node in the graph."""

        if state.get("error"):
            return "synthesize"

        if state.get("waiting_approval"):
            return "check_approval"

        if state["current_step"] >= len(state["plan"]):
            return "synthesize"

        return "execute_step"

    def create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for planning."""

        workflow = StateGraph(PlanState)

        # Add nodes
        workflow.add_node("analyze", self.analyze_request)
        workflow.add_node("plan", self.create_plan)
        workflow.add_node("validate", self.validate_plan)
        workflow.add_node("execute_step", self.execute_step)
        workflow.add_node("check_approval", self.check_approval)
        workflow.add_node("synthesize", self.synthesize_results)

        # Set entry point
        workflow.set_entry_point("analyze")

        # Add edges
        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "validate")
        workflow.add_conditional_edges(
            "validate",
            lambda state: "execute_step" if state.get("validated") else "synthesize"
        )
        workflow.add_conditional_edges("execute_step", self.should_continue)
        workflow.add_conditional_edges("check_approval", self.should_continue)
        workflow.add_edge("synthesize", END)

        return workflow

    async def execute_planning_workflow(
        self,
        conversation_id: int,
        user_id: int,
        agent_id: int,
        user_request: str
    ) -> ExecutionPlan:
        """
        Execute complete planning workflow.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            agent_id: Agent ID
            user_request: User's request

        Returns:
            ExecutionPlan record
        """

        # Create execution plan record
        plan_record = ExecutionPlan(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id,
            user_request=user_request,
            plan_data={},
            status=PlanStatus.PENDING
        )
        self.db.add(plan_record)
        self.db.commit()
        self.db.refresh(plan_record)

        # Create workflow
        workflow = self.create_workflow()
        app = workflow.compile(checkpointer=self.checkpointer)

        # Initialize state
        initial_state: PlanState = {
            "user_request": user_request,
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "analysis": "",
            "plan": [],
            "validated": False,
            "current_step": 0,
            "step_results": [],
            "waiting_approval": False,
            "approval_request_id": None,
            "final_result": "",
            "error": None
        }

        # Execute workflow
        config = {"configurable": {"thread_id": str(plan_record.id)}}

        try:
            plan_record.status = PlanStatus.RUNNING
            plan_record.started_at = datetime.utcnow()
            self.db.commit()

            # Run workflow
            final_state = await app.ainvoke(initial_state, config=config)

            # Update plan record
            plan_record.plan_data = {
                "analysis": final_state.get("analysis"),
                "plan": final_state.get("plan", []),
                "step_results": final_state.get("step_results", [])
            }
            plan_record.current_step = final_state.get("current_step", 0)
            plan_record.state_data = final_state

            if final_state.get("error"):
                plan_record.status = PlanStatus.FAILED
                plan_record.error_message = final_state["error"]
            elif final_state.get("waiting_approval"):
                plan_record.status = PlanStatus.PAUSED
            else:
                plan_record.status = PlanStatus.COMPLETED
                plan_record.completed_at = datetime.utcnow()

            plan_record.final_result = final_state.get("final_result")

            self.db.commit()
            self.db.refresh(plan_record)

        except Exception as e:
            plan_record.status = PlanStatus.FAILED
            plan_record.error_message = str(e)
            self.db.commit()
            raise

        return plan_record
