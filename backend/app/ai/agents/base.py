"""AI Agents base utilities."""

from enum import Enum

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
    """Chat message for conversation history."""

    role: MessageRole
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
