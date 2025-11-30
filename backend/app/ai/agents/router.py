"""AI Agents router."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.agents.langgraph.routes import router as leave_workflow_router
from app.ai.agents.pydantic_ai.hr_agent import HRAgentResponse, process_message
from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.security import CurrentUser
from app.core.tenancy import TenantDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Agents"])
router.include_router(leave_workflow_router)


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response schema."""

    message: str
    follow_up_questions: list[str] | None = None
    data: dict | None = None
    conversation_id: str | None = None


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with HR Assistant",
)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: CurrentUser,
    tenant: TenantDep,
    session: DbSession,
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> ChatResponse:
    """
    Chat with the HR Assistant agent.

    The agent can help with:
    - Leave management (balance inquiries)
    - Attendance queries
    - Payslip information
    - Holiday calendar
    - Team availability
    """
    response: HRAgentResponse = await process_message(
        message=request.message,
        session=session,
        tenant_id=tenant.tenant_id,
        employee_id=current_user.id,
        user_id=current_user.id,
    )

    return ChatResponse(
        message=response.message,
        follow_up_questions=response.follow_up_questions
        if response.follow_up_questions
        else None,
        data=response.data,
        conversation_id=request.conversation_id,
    )


@router.get(
    "/agents",
    summary="List available agents",
)
async def list_agents() -> dict:
    """List all available AI agents."""
    return {
        "agents": [
            {
                "id": "hr_assistant",
                "name": "HR Assistant",
                "description": "General HR queries - leave, attendance, payroll, holidays",
                "capabilities": [
                    "Leave balance inquiry",
                    "Leave application",
                    "Attendance summary",
                    "Payslip information",
                    "Holiday calendar",
                    "Team availability",
                ],
            },
        ],
    }


@router.get(
    "/suggested-prompts",
    summary="Get suggested prompts",
)
async def get_suggested_prompts() -> dict:
    """Get suggested prompts for the chat interface."""
    return {
        "prompts": [
            {
                "category": "Leave",
                "suggestions": [
                    "What's my leave balance?",
                    "I want to apply for sick leave",
                    "How many casual leaves do I have?",
                ],
            },
            {
                "category": "Attendance",
                "suggestions": [
                    "Show my attendance for this month",
                    "How many days was I present this month?",
                ],
            },
            {
                "category": "Payroll",
                "suggestions": [
                    "Get my latest payslip",
                    "What was my salary last month?",
                ],
            },
            {
                "category": "Holidays",
                "suggestions": [
                    "What are the upcoming holidays?",
                    "Who is on leave today?",
                ],
            },
        ],
    }
