"""AI Agents base utilities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel


class AgentRole(str, Enum):
    """Agent role types."""

    HR_ASSISTANT = "hr_assistant"
    LEAVE_AGENT = "leave_agent"
    PAYROLL_AGENT = "payroll_agent"
    ATTENDANCE_AGENT = "attendance_agent"


class MessageRole(str, Enum):
    """Chat message role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """Chat message."""

    role: MessageRole
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class AgentContext:
    """Context passed to agents."""

    tenant_id: str
    user_id: str
    employee_id: str | None = None
    session: Any = None
    conversation_history: list[ChatMessage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""

    message: str
    tool_results: list[dict] | None = None
    follow_up_questions: list[str] | None = None
    data: dict | None = None


# Tool definitions for agents
COMMON_TOOLS = {
    "get_leave_balance": {
        "name": "get_leave_balance",
        "description": "Get leave balance for an employee",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Employee ID (optional, defaults to current user)",
                },
            },
        },
    },
    "apply_leave": {
        "name": "apply_leave",
        "description": "Apply for leave",
        "parameters": {
            "type": "object",
            "properties": {
                "leave_type": {
                    "type": "string",
                    "description": "Type of leave (casual, sick, earned, etc.)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for leave",
                },
            },
            "required": ["leave_type", "start_date", "end_date"],
        },
    },
    "get_attendance_summary": {
        "name": "get_attendance_summary",
        "description": "Get attendance summary for current month",
        "parameters": {
            "type": "object",
            "properties": {
                "month": {"type": "integer", "description": "Month (1-12)"},
                "year": {"type": "integer", "description": "Year"},
            },
        },
    },
    "get_payslip": {
        "name": "get_payslip",
        "description": "Get payslip for a specific month",
        "parameters": {
            "type": "object",
            "properties": {
                "month": {"type": "integer", "description": "Month (1-12)"},
                "year": {"type": "integer", "description": "Year"},
            },
        },
    },
    "get_upcoming_holidays": {
        "name": "get_upcoming_holidays",
        "description": "Get list of upcoming holidays",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of holidays to return"},
            },
        },
    },
    "get_team_on_leave": {
        "name": "get_team_on_leave",
        "description": "Get team members who are on leave today or upcoming",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            },
        },
    },
}
