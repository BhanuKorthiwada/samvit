"""AI Agents router."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.base import AgentContext
from app.ai.agents.hr_assistant import HRAssistantAgent
from app.core.database import get_async_session
from app.core.deps import CurrentUser, TenantDep

router = APIRouter(prefix="/ai", tags=["AI Agents"])


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
    session: AsyncSession = Depends(get_async_session),
) -> ChatResponse:
    """
    Chat with the HR Assistant agent.

    The agent can help with:
    - Leave management (balance, applications)
    - Attendance queries
    - Payslip information
    - Holiday calendar
    - Team availability
    """
    # Create agent context
    context = AgentContext(
        tenant_id=tenant.tenant_id,
        user_id=current_user.id,
        employee_id=current_user.id,  # Simplified - would map user to employee
        session=session,
    )

    # Create and use agent
    agent = HRAssistantAgent(context)

    try:
        response = await agent.process_message(request.message)

        return ChatResponse(
            message=response.message,
            follow_up_questions=response.follow_up_questions,
            data=response.data,
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}",
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
