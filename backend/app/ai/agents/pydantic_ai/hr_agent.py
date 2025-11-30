"""HR Assistant Agent using Pydantic AI."""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from functools import cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.langgraph.leave_workflow import (
    LeaveRequestInput,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    get_leave_workflow_runner,
)
from app.core.config import settings
from app.modules.attendance.models import Attendance, AttendanceStatus
from app.modules.employees.models import Employee
from app.modules.leave.models import (
    Holiday,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveStatus,
)
from app.modules.payroll.models import PayrollPeriod, Payslip

logger = logging.getLogger(__name__)


# ============================================================================
# Schemas for structured responses
# ============================================================================


class LeaveBalanceItem(BaseModel):
    """Single leave balance entry."""

    leave_type: str = Field(description="Type of leave (e.g., Casual, Sick, Earned)")
    total_days: float = Field(description="Total allocated days")
    used_days: float = Field(description="Days already used")
    pending_days: float = Field(description="Days pending approval")
    available_days: float = Field(description="Days available to use")


class LeaveBalanceResponse(BaseModel):
    """Leave balance response."""

    employee_name: str
    balances: list[LeaveBalanceItem]
    message: str


class AttendanceSummaryResponse(BaseModel):
    """Attendance summary response."""

    month: int
    year: int
    present_days: int
    absent_days: int
    leave_days: int
    half_days: int
    message: str


class HolidayItem(BaseModel):
    """Holiday entry."""

    name: str
    date: str
    is_optional: bool


class HolidaysResponse(BaseModel):
    """Holidays response."""

    holidays: list[HolidayItem]
    message: str


class PayslipResponse(BaseModel):
    """Payslip response."""

    month: int
    year: int
    gross_earnings: float
    total_deductions: float
    net_pay: float
    status: str
    message: str


class TeamLeaveResponse(BaseModel):
    """Team on leave response."""

    date: str
    employees: list[str]
    count: int
    message: str


class ApplyLeaveResponse(BaseModel):
    """Response from applying for leave."""

    success: bool
    request_id: str | None = None
    thread_id: str | None = None
    leave_type: str
    start_date: str
    end_date: str
    total_days: float
    status: str
    manager_name: str | None = None
    message: str
    validation_errors: list[str] = []


class HRAgentResponse(BaseModel):
    """Unified response from HR Agent."""

    message: str = Field(description="Natural language response to the user")
    data: dict[str, Any] | None = Field(
        default=None, description="Structured data if applicable"
    )
    follow_up_questions: list[str] = Field(
        default_factory=list, description="Suggested follow-up questions"
    )


# ============================================================================
# Agent Dependencies (Context)
# ============================================================================


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class HRAgentDeps:
    """Dependencies injected into the HR Agent."""

    session: AsyncSession
    tenant_id: str
    employee_id: str
    user_id: str
    message_history: list[ChatMessage] | None = None  # For multi-turn conversations


# ============================================================================
# HR Agent Definition
# ============================================================================

# System prompt for the HR Assistant
HR_SYSTEM_PROMPT = """You are a helpful HR Assistant for SAMVIT HRMS (Human Resource Management System).
You help employees with HR-related queries using the available tools.

Your capabilities:
1. **Leave Management**: Check leave balances, apply for leave, view leave policies
2. **Attendance**: View attendance summary for any month
3. **Payroll**: Get payslip information
4. **Holidays**: View upcoming company holidays
5. **Team**: Check who is on leave

Guidelines:
- Be professional, friendly, and concise
- When displaying monetary values, use Indian Rupee format (₹)
- Always respect data privacy - employees can only access their own information
- If you don't have information, say so clearly
- Suggest relevant follow-up actions when appropriate

When applying for leave:
- First check the user's leave balance to show available options
- Ask for: leave type, start date, end date, and reason
- Confirm the details before submitting
- After submission, inform them about the approval process

When a user asks about something, use the appropriate tool to fetch the information,
then provide a helpful natural language response.
"""


@cache
def get_hr_agent() -> Agent[HRAgentDeps, HRAgentResponse]:
    """
    Get or create the HR Agent instance.

    Uses @cache for thread-safe lazy initialization.
    The agent is created once and reused for all requests.
    """
    agent = Agent(
        model=settings.ai_model,
        system_prompt=HR_SYSTEM_PROMPT,
        deps_type=HRAgentDeps,
        result_type=HRAgentResponse,
        retries=2,
    )
    _register_tools(agent)
    return agent


def _register_tools(agent: Agent[HRAgentDeps, HRAgentResponse]) -> None:
    """Register all tools on the agent."""

    @agent.tool
    async def get_leave_balance(ctx: RunContext[HRAgentDeps]) -> LeaveBalanceResponse:
        """
        Get the current user's leave balance.

        Returns the available, used, and pending leave days for each leave type.
        """
        return await _get_leave_balance_impl(ctx.deps)

    @agent.tool
    async def get_attendance_summary(
        ctx: RunContext[HRAgentDeps],
        month: int | None = None,
        year: int | None = None,
    ) -> AttendanceSummaryResponse:
        """
        Get attendance summary for a specific month.

        Args:
            month: Month number (1-12). Defaults to current month.
            year: Year. Defaults to current year.
        """
        return await _get_attendance_summary_impl(ctx.deps, month, year)

    @agent.tool
    async def get_upcoming_holidays(
        ctx: RunContext[HRAgentDeps],
        count: int = 5,
    ) -> HolidaysResponse:
        """
        Get upcoming company holidays.

        Args:
            count: Number of upcoming holidays to return (default: 5)
        """
        return await _get_upcoming_holidays_impl(ctx.deps, count)

    @agent.tool
    async def get_payslip(
        ctx: RunContext[HRAgentDeps],
        month: int | None = None,
        year: int | None = None,
    ) -> PayslipResponse:
        """
        Get payslip for a specific month.

        Args:
            month: Month number (1-12). Defaults to current month.
            year: Year. Defaults to current year.
        """
        return await _get_payslip_impl(ctx.deps, month, year)

    @agent.tool
    async def get_team_on_leave(
        ctx: RunContext[HRAgentDeps],
        target_date: str | None = None,
    ) -> TeamLeaveResponse:
        """
        Check which team members are on leave for a specific date.

        Args:
            target_date: Date in YYYY-MM-DD format. Defaults to today.
        """
        return await _get_team_on_leave_impl(ctx.deps, target_date)

    @agent.tool
    async def apply_leave(
        ctx: RunContext[HRAgentDeps],
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str,
        start_day_type: str = "full",
        end_day_type: str = "full",
    ) -> ApplyLeaveResponse:
        """
        Apply for leave. This initiates a leave request that goes through approval workflow.

        Args:
            leave_type: Type of leave (e.g., "Casual Leave", "Sick Leave", "Earned Leave")
            start_date: Leave start date in YYYY-MM-DD format
            end_date: Leave end date in YYYY-MM-DD format
            reason: Reason for taking leave
            start_day_type: "full", "first_half", or "second_half" for the start date
            end_day_type: "full", "first_half", or "second_half" for the end date
        """
        return await _apply_leave_impl(
            ctx.deps,
            leave_type,
            start_date,
            end_date,
            reason,
            start_day_type,
            end_day_type,
        )


# ============================================================================
# Tool Implementations
# ============================================================================


async def _get_leave_balance_impl(deps: HRAgentDeps) -> LeaveBalanceResponse:
    """Get the current user's leave balance."""
    session = deps.session

    # Get employee name
    emp_result = await session.execute(
        select(Employee).where(
            Employee.tenant_id == deps.tenant_id,
            Employee.id == deps.employee_id,
        )
    )
    employee = emp_result.scalar_one_or_none()
    employee_name = (
        f"{employee.first_name} {employee.last_name}" if employee else "Employee"
    )

    # Get leave balances with policy names
    result = await session.execute(
        select(LeaveBalance, LeavePolicy)
        .join(LeavePolicy, LeaveBalance.policy_id == LeavePolicy.id)
        .where(
            LeaveBalance.tenant_id == deps.tenant_id,
            LeaveBalance.employee_id == deps.employee_id,
        )
    )
    rows = result.all()

    balances = [
        LeaveBalanceItem(
            leave_type=policy.name,
            total_days=float(balance.total_days),
            used_days=float(balance.used_days),
            pending_days=float(balance.pending_days),
            available_days=float(balance.available_days),
        )
        for balance, policy in rows
    ]

    if not balances:
        return LeaveBalanceResponse(
            employee_name=employee_name,
            balances=[],
            message="No leave balances found. Please contact HR.",
        )

    total_available = sum(b.available_days for b in balances)
    return LeaveBalanceResponse(
        employee_name=employee_name,
        balances=balances,
        message=f"You have {total_available:.1f} total leave days available across all types.",
    )


async def _get_attendance_summary_impl(
    deps: HRAgentDeps,
    month: int | None = None,
    year: int | None = None,
) -> AttendanceSummaryResponse:
    """Get attendance summary for a specific month using optimized SQL aggregation."""
    today = date.today()

    # Validate and default month/year
    target_month = month if month and 1 <= month <= 12 else today.month
    target_year = year if year and 2000 <= year <= 2100 else today.year

    # Optimized: Use SQL aggregation instead of fetching all records
    result = await deps.session.execute(
        select(
            Attendance.status,
            func.count(Attendance.id).label("count"),
        )
        .where(
            Attendance.tenant_id == deps.tenant_id,
            Attendance.employee_id == deps.employee_id,
            extract("month", Attendance.date) == target_month,
            extract("year", Attendance.date) == target_year,
        )
        .group_by(Attendance.status)
    )
    status_counts = {row.status: row.count for row in result.all()}

    present = status_counts.get(AttendanceStatus.PRESENT.value, 0)
    absent = status_counts.get(AttendanceStatus.ABSENT.value, 0)
    leave = status_counts.get(AttendanceStatus.ON_LEAVE.value, 0)
    half_day = status_counts.get(AttendanceStatus.HALF_DAY.value, 0)

    month_name = datetime(target_year, target_month, 1).strftime("%B %Y")
    return AttendanceSummaryResponse(
        month=target_month,
        year=target_year,
        present_days=present,
        absent_days=absent,
        leave_days=leave,
        half_days=half_day,
        message=f"Attendance summary for {month_name}: {present} present, {absent} absent, {leave} on leave.",
    )


async def _get_upcoming_holidays_impl(
    deps: HRAgentDeps,
    count: int = 5,
) -> HolidaysResponse:
    """Get upcoming holidays."""
    today = date.today()

    result = await deps.session.execute(
        select(Holiday)
        .where(
            Holiday.tenant_id == deps.tenant_id,
            Holiday.date >= today,
        )
        .order_by(Holiday.date)
        .limit(count)
    )
    holidays = result.scalars().all()

    holiday_items = [
        HolidayItem(
            name=h.name,
            date=h.date.strftime("%A, %B %d, %Y"),
            is_optional=h.is_optional,
        )
        for h in holidays
    ]

    if not holiday_items:
        return HolidaysResponse(
            holidays=[],
            message="No upcoming holidays found in the calendar.",
        )

    next_holiday = holiday_items[0]
    return HolidaysResponse(
        holidays=holiday_items,
        message=f"Next holiday: {next_holiday.name} on {next_holiday.date}. Found {len(holiday_items)} upcoming holidays.",
    )


async def _get_payslip_impl(
    deps: HRAgentDeps,
    month: int | None = None,
    year: int | None = None,
) -> PayslipResponse:
    """Get payslip for a specific month."""
    today = date.today()

    # Validate and default month/year
    target_month = month if month and 1 <= month <= 12 else today.month
    target_year = year if year and 2000 <= year <= 2100 else today.year

    result = await deps.session.execute(
        select(Payslip)
        .join(PayrollPeriod, Payslip.payroll_period_id == PayrollPeriod.id)
        .where(
            Payslip.tenant_id == deps.tenant_id,
            Payslip.employee_id == deps.employee_id,
            PayrollPeriod.month == target_month,
            PayrollPeriod.year == target_year,
        )
    )
    payslip = result.scalar_one_or_none()

    month_name = datetime(target_year, target_month, 1).strftime("%B %Y")

    if not payslip:
        return PayslipResponse(
            month=target_month,
            year=target_year,
            gross_earnings=0,
            total_deductions=0,
            net_pay=0,
            status="not_found",
            message=f"Payslip for {month_name} is not yet available.",
        )

    return PayslipResponse(
        month=target_month,
        year=target_year,
        gross_earnings=float(payslip.gross_earnings),
        total_deductions=float(payslip.total_deductions),
        net_pay=float(payslip.net_pay),
        status=payslip.status,
        message=f"Your net pay for {month_name} is ₹{float(payslip.net_pay):,.2f}",
    )


async def _get_team_on_leave_impl(
    deps: HRAgentDeps,
    target_date: str | None = None,
) -> TeamLeaveResponse:
    """Check which team members are on leave (same department as current user)."""
    if target_date:
        try:
            check_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            check_date = date.today()
    else:
        check_date = date.today()

    # First, get the current employee's department
    current_emp = await deps.session.execute(
        select(Employee.department_id).where(
            Employee.tenant_id == deps.tenant_id,
            Employee.id == deps.employee_id,
        )
    )
    dept_row = current_emp.scalar_one_or_none()

    # Build query for approved leave requests on the date
    # Limit to 50 to prevent performance issues in large departments
    query = (
        select(LeaveRequest, Employee)
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .where(
            LeaveRequest.tenant_id == deps.tenant_id,
            LeaveRequest.start_date <= check_date,
            LeaveRequest.end_date >= check_date,
            LeaveRequest.status == LeaveStatus.APPROVED.value,
            LeaveRequest.employee_id != deps.employee_id,  # Exclude self
        )
        .order_by(Employee.first_name, Employee.last_name)
        .limit(50)
    )

    # Filter by department if the current user has one
    if dept_row:
        query = query.where(Employee.department_id == dept_row)

    result = await deps.session.execute(query)
    rows = result.all()

    employees_on_leave = [f"{emp.first_name} {emp.last_name}" for _, emp in rows if emp]

    date_str = check_date.strftime("%A, %B %d, %Y")
    if not employees_on_leave:
        return TeamLeaveResponse(
            date=date_str,
            employees=[],
            count=0,
            message=f"No team members are on leave on {date_str}.",
        )

    return TeamLeaveResponse(
        date=date_str,
        employees=employees_on_leave,
        count=len(employees_on_leave),
        message=f"{len(employees_on_leave)} team member(s) on leave on {date_str}: {', '.join(employees_on_leave)}",
    )


async def _apply_leave_impl(
    deps: HRAgentDeps,
    leave_type: str,
    start_date_str: str,
    end_date_str: str,
    reason: str,
    start_day_type: str = "full",
    end_day_type: str = "full",
) -> ApplyLeaveResponse:
    """Apply for leave by triggering the LangGraph workflow."""
    session = deps.session

    # Parse dates
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return ApplyLeaveResponse(
            success=False,
            leave_type=leave_type,
            start_date=start_date_str,
            end_date=end_date_str,
            total_days=0,
            status="validation_failed",
            message="Invalid date format. Please use YYYY-MM-DD format.",
            validation_errors=["Invalid date format"],
        )

    # Validate date range
    if end_date < start_date:
        return ApplyLeaveResponse(
            success=False,
            leave_type=leave_type,
            start_date=start_date_str,
            end_date=end_date_str,
            total_days=0,
            status="validation_failed",
            message="End date cannot be before start date.",
            validation_errors=["End date cannot be before start date"],
        )

    # Find the leave policy by name (case-insensitive)
    policy_result = await session.execute(
        select(LeavePolicy).where(
            LeavePolicy.tenant_id == deps.tenant_id,
            LeavePolicy.is_active == True,  # noqa: E712
            func.lower(LeavePolicy.name).contains(leave_type.lower()),
        )
    )
    policy = policy_result.scalar_one_or_none()

    if not policy:
        # List available policies
        policy_result = await session.execute(
            select(LeavePolicy).where(
                LeavePolicy.tenant_id == deps.tenant_id,
                LeavePolicy.is_active == True,  # noqa: E712
            )
        )
        policies = policy_result.scalars().all()
        policy_names = [p.name for p in policies]

        return ApplyLeaveResponse(
            success=False,
            leave_type=leave_type,
            start_date=start_date_str,
            end_date=end_date_str,
            total_days=0,
            status="validation_failed",
            message=f"Leave type '{leave_type}' not found. Available types: {', '.join(policy_names)}",
            validation_errors=[f"Unknown leave type: {leave_type}"],
        )

    # Create workflow context and request
    workflow_context = WorkflowContext(
        session=session,
        tenant_id=deps.tenant_id,
        current_user_id=deps.user_id,
        current_user_role="employee",
    )

    request_input = LeaveRequestInput(
        employee_id=deps.employee_id,
        policy_id=policy.id,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        start_day_type=start_day_type,
        end_day_type=end_day_type,
    )

    # Start the leave workflow (now async)
    try:
        runner = await get_leave_workflow_runner()
        result: WorkflowResult = await runner.start_leave_request(
            workflow_context, request_input
        )

        # WorkflowResult is now a proper Pydantic model - no fragile dict parsing
        if result.status == WorkflowStatus.VALIDATION_FAILED:
            return ApplyLeaveResponse(
                success=False,
                leave_type=policy.name,
                start_date=start_date_str,
                end_date=end_date_str,
                total_days=result.total_days,
                status="validation_failed",
                message=result.message,
                validation_errors=result.validation_errors,
            )

        # Success - request submitted for approval
        return ApplyLeaveResponse(
            success=True,
            request_id=result.request_id,
            thread_id=result.thread_id,
            leave_type=policy.name,
            start_date=start_date_str,
            end_date=end_date_str,
            total_days=result.total_days,
            status="pending_approval",
            manager_name=result.manager_name,
            message=result.message,
        )

    except Exception as e:
        logger.exception("Error starting leave workflow: %s", e)
        return ApplyLeaveResponse(
            success=False,
            leave_type=policy.name,
            start_date=start_date_str,
            end_date=end_date_str,
            total_days=0,
            status="error",
            message="An error occurred while processing your leave request. Please try again.",
            validation_errors=[str(e)],
        )


# ============================================================================
# Public API
# ============================================================================


async def process_message(
    message: str,
    session: AsyncSession,
    tenant_id: str,
    employee_id: str,
    user_id: str,
    message_history: list[dict[str, str]] | None = None,
) -> HRAgentResponse:
    """
    Process a user message using the HR Agent.

    Args:
        message: User's natural language query
        session: Database session
        tenant_id: Current tenant ID
        employee_id: Current employee ID
        user_id: Current user ID
        message_history: Optional list of previous messages for context.
                        Each message should have 'role' and 'content' keys.

    Returns:
        HRAgentResponse with message, data, and follow-up questions
    """
    # Convert message history to ChatMessage objects
    history = None
    if message_history:
        history = [
            ChatMessage(role=m["role"], content=m["content"]) for m in message_history
        ]

    deps = HRAgentDeps(
        session=session,
        tenant_id=tenant_id,
        employee_id=employee_id,
        user_id=user_id,
        message_history=history,
    )

    try:
        agent = get_hr_agent()

        # Build message history for Pydantic AI
        messages = []
        if history:
            from pydantic_ai.messages import (
                ModelRequest,
                ModelResponse,
                TextPart,
                UserPromptPart,
            )

            for msg in history:
                if msg.role == "user":
                    messages.append(
                        ModelRequest(parts=[UserPromptPart(content=msg.content)])
                    )
                elif msg.role == "assistant":
                    messages.append(
                        ModelResponse(parts=[TextPart(content=msg.content)])
                    )

        # Run with message history
        result = await agent.run(
            message, deps=deps, message_history=messages if messages else None
        )

        return (
            result.data
            if result.data
            else HRAgentResponse(
                message="I processed your request but couldn't generate a proper response.",
                follow_up_questions=[
                    "What's my leave balance?",
                    "Show upcoming holidays",
                ],
            )
        )
    except Exception as e:
        logger.exception("Error processing message with HR Agent: %s", e)
        return HRAgentResponse(
            message="I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
            data=None,
            follow_up_questions=[
                "What's my leave balance?",
                "Show upcoming holidays",
                "Get my attendance summary",
            ],
        )
