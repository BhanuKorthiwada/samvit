"""
Leave Approval Workflow using LangGraph.

This implements a multi-step leave approval process:
1. Employee submits leave request
2. System validates the request (balance, policy rules)
3. Manager reviews and approves/rejects (human-in-the-loop)
4. HR reviews for leaves > threshold (human-in-the-loop)
5. Leave balance is updated

Key LangGraph features:
- TypedDict state schema (simpler than Pydantic for LangGraph)
- AsyncPostgresSaver for persistent checkpoints
- interrupt() function for human-in-the-loop (recommended pattern)
- Command(resume=value) for resuming workflows
- Command(goto=node, update={}) for explicit routing
- Closure-based context injection for database access
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal, TypedDict

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.employees.models import Employee
from app.modules.leave.models import (
    Holiday,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveStatus,
)

logger = logging.getLogger(__name__)

HR_REVIEW_THRESHOLD_DAYS = 5


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING_VALIDATION = "pending_validation"
    VALIDATION_FAILED = "validation_failed"
    PENDING_MANAGER_APPROVAL = "pending_manager_approval"
    PENDING_HR_REVIEW = "pending_hr_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ValidationError(BaseModel):
    """Validation error detail."""

    code: str
    message: str


class LeaveRequestInput(BaseModel):
    """Input for creating a leave request."""

    employee_id: str
    policy_id: str
    start_date: date
    end_date: date
    reason: str
    start_day_type: str = "full"
    end_day_type: str = "full"


class DecisionType(str, Enum):
    """Manager/HR decision types."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DayType(str, Enum):
    """Day type for start/end of leave."""

    FULL = "full"
    FIRST_HALF = "first_half"
    SECOND_HALF = "second_half"


class WorkflowState(TypedDict, total=False):
    """
    State maintained throughout the leave approval workflow.

    Using TypedDict (LangGraph's recommended approach) for cleaner
    state management. LangGraph's JsonPlusSerializer preserves Python
    types (date, Enum) through msgpack serialization.
    """

    # Request details
    tenant_id: str
    request_id: str | None
    employee_id: str
    employee_name: str
    manager_id: str | None
    manager_name: str

    # Leave details
    policy_id: str
    policy_name: str
    start_date: date
    end_date: date
    total_days: float
    reason: str
    start_day_type: DayType
    end_day_type: DayType

    # Workflow status
    status: WorkflowStatus
    validation_errors: list[dict[str, str]]

    # Approval details
    requires_hr_review: bool
    manager_decision: DecisionType
    manager_remarks: str
    hr_decision: DecisionType
    hr_remarks: str

    # Metadata
    messages: Annotated[list[dict], add_messages]
    created_at: datetime
    updated_at: datetime


class WorkflowResult(BaseModel):
    """Structured result from workflow operations."""

    thread_id: str
    status: WorkflowStatus
    request_id: str | None = None
    employee_name: str = ""
    manager_name: str = ""
    policy_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    total_days: float = 0.0
    validation_errors: list[str] = []
    message: str = ""

    @classmethod
    def from_state(cls, thread_id: str, state: dict[str, Any]) -> "WorkflowResult":
        """Create result from workflow state."""
        errors = state.get("validation_errors", [])
        error_messages = [e.get("message", str(e)) for e in errors]

        status = state.get("status", WorkflowStatus.PENDING_VALIDATION)
        if isinstance(status, str):
            status = WorkflowStatus(status)

        # Generate appropriate message
        if status == WorkflowStatus.VALIDATION_FAILED:
            message = f"Validation failed: {'; '.join(error_messages)}"
        elif status == WorkflowStatus.PENDING_MANAGER_APPROVAL:
            manager = state.get("manager_name", "your manager")
            message = f"Leave request submitted. Awaiting approval from {manager}."
        elif status == WorkflowStatus.PENDING_HR_REVIEW:
            message = "Manager approved. Awaiting HR review."
        elif status == WorkflowStatus.APPROVED:
            message = f"Leave approved! {state.get('total_days', 0):.1f} days."
        elif status == WorkflowStatus.REJECTED:
            message = "Leave request was rejected."
        else:
            message = f"Status: {status.value}"

        return cls(
            thread_id=thread_id,
            status=status,
            request_id=state.get("request_id"),
            employee_name=state.get("employee_name", ""),
            manager_name=state.get("manager_name", ""),
            policy_name=state.get("policy_name", ""),
            start_date=state.get("start_date"),
            end_date=state.get("end_date"),
            total_days=state.get("total_days", 0.0),
            validation_errors=error_messages,
            message=message,
        )


@dataclass
class WorkflowContext:
    """Context/dependencies for workflow execution."""

    session: AsyncSession
    tenant_id: str
    current_user_id: str
    current_user_role: str = "employee"


# ============================================================================
# Helper Functions
# ============================================================================


def _parse_day_type(value: str | DayType) -> DayType:
    """Parse string to DayType enum, defaulting to FULL for invalid values."""
    if isinstance(value, DayType):
        return value
    try:
        return DayType(value)
    except ValueError:
        return DayType.FULL


def _day_type_to_str(value: str | DayType) -> str:
    """Convert DayType to string value."""
    if isinstance(value, DayType):
        return value.value
    return value if value in [e.value for e in DayType] else DayType.FULL.value


def _calculate_leave_days(
    start_date: date,
    end_date: date,
    start_day_type: str,
    end_day_type: str,
    holidays: set[date],
) -> float:
    """
    Calculate actual leave days excluding holidays and weekends.

    Args:
        start_date: Leave start date
        end_date: Leave end date
        start_day_type: "full", "first_half", or "second_half"
        end_day_type: "full", "first_half", or "second_half"
        holidays: Set of holiday dates to exclude

    Returns:
        Total leave days as float (0.5 for half days)
    """
    # Validate day types
    valid_half_types = {"first_half", "second_half"}
    start_is_half = start_day_type in valid_half_types
    end_is_half = end_day_type in valid_half_types

    total_days = 0.0
    current = start_date

    while current <= end_date:
        # Skip weekends (Saturday=5, Sunday=6) and holidays
        if current.weekday() < 5 and current not in holidays:
            if current == start_date and start_is_half:
                total_days += 0.5
            elif current == end_date and end_is_half:
                total_days += 0.5
            else:
                total_days += 1.0

        current = current + timedelta(days=1)

    return total_days


async def _restore_pending_balance(
    state: WorkflowState,
    session: AsyncSession,
    tenant_id: str,
) -> None:
    """Restore pending balance on rejection."""
    start_date = state["start_date"]

    balance_result = await session.execute(
        select(LeaveBalance).where(
            LeaveBalance.tenant_id == tenant_id,
            LeaveBalance.employee_id == state["employee_id"],
            LeaveBalance.policy_id == state["policy_id"],
            LeaveBalance.year == start_date.year,
        )
    )
    balance = balance_result.scalar_one_or_none()
    if balance:
        balance.pending = max(0, float(balance.pending) - state.get("total_days", 0))


async def _finalize_approval(
    state: WorkflowState,
    session: AsyncSession,
    tenant_id: str,
    approver_id: str,
) -> None:
    """Finalize the leave approval - update request and balance."""
    start_date = state["start_date"]

    if state.get("request_id"):
        result = await session.execute(
            select(LeaveRequest).where(LeaveRequest.id == state["request_id"])
        )
        leave_request = result.scalar_one_or_none()
        if leave_request:
            leave_request.status = LeaveStatus.APPROVED.value
            leave_request.approver_id = approver_id
            leave_request.approved_at = date.today()
            remarks = state.get("manager_remarks", "")
            if state.get("hr_remarks"):
                remarks = f"Manager: {remarks}\nHR: {state['hr_remarks']}"
            leave_request.approver_remarks = remarks

        # Update balance: move from pending to used
        balance_result = await session.execute(
            select(LeaveBalance).where(
                LeaveBalance.tenant_id == tenant_id,
                LeaveBalance.employee_id == state["employee_id"],
                LeaveBalance.policy_id == state["policy_id"],
                LeaveBalance.year == start_date.year,
            )
        )
        balance = balance_result.scalar_one_or_none()
        if balance:
            total_days = state.get("total_days", 0)
            balance.pending = max(0, float(balance.pending) - total_days)
            balance.used = float(balance.used) + total_days


NodeFunc = Callable[[WorkflowState], dict[str, Any]]


def create_workflow_nodes(context: WorkflowContext) -> dict[str, NodeFunc]:
    """
    Factory that creates workflow node functions with context in closure.

    LangGraph nodes only receive state as parameter, but we need database
    access. This factory captures the context in closures for each node.

    Uses the modern interrupt() function for human-in-the-loop, which:
    - Pauses execution and surfaces info to the client
    - Returns the human's response when resumed with Command(resume=value)
    """
    session = context.session

    async def validate_request(state: WorkflowState) -> dict[str, Any]:
        """Validate the leave request against policy rules."""
        errors: list[dict[str, str]] = []

        start_date = state["start_date"]
        end_date = state["end_date"]

        employee_name = ""
        manager_id = None
        manager_name = ""
        policy_name = ""

        # Get employee details
        emp_result = await session.execute(
            select(Employee).where(
                Employee.tenant_id == context.tenant_id,
                Employee.id == state["employee_id"],
                Employee.is_active == True,  # noqa: E712
            )
        )
        employee = emp_result.scalar_one_or_none()

        if not employee:
            errors.append(
                {
                    "code": "EMPLOYEE_NOT_FOUND",
                    "message": "Employee not found or inactive",
                }
            )
            return {
                "validation_errors": errors,
                "status": WorkflowStatus.VALIDATION_FAILED,
                "updated_at": datetime.now(),
            }

        employee_name = f"{employee.first_name} {employee.last_name}"
        manager_id = employee.reporting_manager_id

        if employee.reporting_manager_id:
            mgr_result = await session.execute(
                select(Employee).where(Employee.id == employee.reporting_manager_id)
            )
            manager = mgr_result.scalar_one_or_none()
            if manager:
                manager_name = f"{manager.first_name} {manager.last_name}"

        # Get policy details
        policy_result = await session.execute(
            select(LeavePolicy).where(
                LeavePolicy.tenant_id == context.tenant_id,
                LeavePolicy.id == state["policy_id"],
                LeavePolicy.is_active == True,  # noqa: E712
            )
        )
        policy = policy_result.scalar_one_or_none()

        if not policy:
            errors.append(
                {
                    "code": "POLICY_NOT_FOUND",
                    "message": "Leave policy not found or inactive",
                }
            )
            return {
                "employee_name": employee_name,
                "manager_id": manager_id,
                "manager_name": manager_name,
                "validation_errors": errors,
                "status": WorkflowStatus.VALIDATION_FAILED,
                "updated_at": datetime.now(),
            }

        policy_name = policy.name

        # Get holidays in date range
        holiday_result = await session.execute(
            select(Holiday.date).where(
                Holiday.tenant_id == context.tenant_id,
                Holiday.date >= start_date,
                Holiday.date <= end_date,
                Holiday.is_optional == False,  # noqa: E712
            )
        )
        holidays = {row[0] for row in holiday_result.all()}

        # Calculate total days
        start_day_type = state.get("start_day_type", DayType.FULL)
        end_day_type = state.get("end_day_type", DayType.FULL)

        total_days = _calculate_leave_days(
            start_date=start_date,
            end_date=end_date,
            start_day_type=_day_type_to_str(start_day_type),
            end_day_type=_day_type_to_str(end_day_type),
            holidays=holidays,
        )

        # Check advance notice
        days_in_advance = (start_date - date.today()).days
        if days_in_advance < policy.advance_notice_days:
            errors.append(
                {
                    "code": "INSUFFICIENT_NOTICE",
                    "message": f"Requires {policy.advance_notice_days} days advance notice. You provided {days_in_advance} days.",
                }
            )

        # Check min/max days
        if total_days < float(policy.min_days):
            errors.append(
                {
                    "code": "BELOW_MIN_DAYS",
                    "message": f"Minimum {policy.min_days} days required.",
                }
            )

        if policy.max_days and total_days > float(policy.max_days):
            errors.append(
                {
                    "code": "EXCEEDS_MAX_DAYS",
                    "message": f"Maximum {policy.max_days} days allowed.",
                }
            )

        # Check leave balance
        balance_result = await session.execute(
            select(LeaveBalance).where(
                LeaveBalance.tenant_id == context.tenant_id,
                LeaveBalance.employee_id == state["employee_id"],
                LeaveBalance.policy_id == state["policy_id"],
                LeaveBalance.year == start_date.year,
            )
        )
        balance = balance_result.scalar_one_or_none()

        if not balance:
            errors.append(
                {
                    "code": "NO_BALANCE",
                    "message": "No leave balance found for this leave type.",
                }
            )
        elif balance.available < total_days:
            errors.append(
                {
                    "code": "INSUFFICIENT_BALANCE",
                    "message": f"Insufficient balance. Available: {balance.available:.1f}, Requested: {total_days:.1f}",
                }
            )

        # Check for overlapping leaves
        overlap_result = await session.execute(
            select(LeaveRequest).where(
                LeaveRequest.tenant_id == context.tenant_id,
                LeaveRequest.employee_id == state["employee_id"],
                LeaveRequest.status.in_(
                    [LeaveStatus.PENDING.value, LeaveStatus.APPROVED.value]
                ),
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            )
        )
        if overlap_result.scalars().first():
            errors.append(
                {
                    "code": "OVERLAPPING_LEAVE",
                    "message": "You already have a leave request for overlapping dates.",
                }
            )

        requires_hr_review = total_days > HR_REVIEW_THRESHOLD_DAYS

        now = datetime.now()
        if errors:
            return {
                "employee_name": employee_name,
                "manager_id": manager_id,
                "manager_name": manager_name,
                "policy_name": policy_name,
                "total_days": total_days,
                "requires_hr_review": requires_hr_review,
                "validation_errors": errors,
                "status": WorkflowStatus.VALIDATION_FAILED,
                "updated_at": now,
            }

        return {
            "employee_name": employee_name,
            "manager_id": manager_id,
            "manager_name": manager_name,
            "policy_name": policy_name,
            "total_days": total_days,
            "requires_hr_review": requires_hr_review,
            "validation_errors": [],
            "status": WorkflowStatus.PENDING_MANAGER_APPROVAL,
            "messages": [
                {
                    "role": "system",
                    "content": f"Validated: {total_days:.1f} days of {policy_name}",
                }
            ],
            "updated_at": now,
        }

    async def create_leave_request(state: WorkflowState) -> dict[str, Any]:
        """Create the leave request in database after validation passes."""
        start_date = state["start_date"]
        end_date = state["end_date"]

        start_day_type = state.get("start_day_type", DayType.FULL)
        end_day_type = state.get("end_day_type", DayType.FULL)

        leave_request = LeaveRequest(
            tenant_id=context.tenant_id,
            employee_id=state["employee_id"],
            policy_id=state["policy_id"],
            start_date=start_date,
            end_date=end_date,
            start_day_type=_day_type_to_str(start_day_type),
            end_day_type=_day_type_to_str(end_day_type),
            total_days=state["total_days"],
            reason=state["reason"],
            status=LeaveStatus.PENDING.value,
        )
        session.add(leave_request)
        await session.flush()

        balance_result = await session.execute(
            select(LeaveBalance).where(
                LeaveBalance.tenant_id == context.tenant_id,
                LeaveBalance.employee_id == state["employee_id"],
                LeaveBalance.policy_id == state["policy_id"],
                LeaveBalance.year == start_date.year,
            )
        )
        balance = balance_result.scalar_one_or_none()
        if balance:
            balance.pending = float(balance.pending) + state["total_days"]

        return {
            "request_id": leave_request.id,
            "messages": [
                {
                    "role": "system",
                    "content": f"Leave request created: {leave_request.id}",
                }
            ],
            "updated_at": datetime.now(),
        }

    async def manager_approval(
        state: WorkflowState,
    ) -> Command[Literal["finalize_approval", "await_hr", END]]:
        """
        Manager approval node with human-in-the-loop using interrupt().

        The interrupt() function pauses execution and surfaces the leave
        request details to the manager. When resumed with Command(resume=value),
        the interrupt() returns the manager's decision.
        """
        # Use interrupt() to pause for human input
        # This surfaces the request details and waits for manager decision
        decision_data = interrupt(
            {
                "type": "manager_approval",
                "question": f"Approve leave request for {state.get('employee_name', 'employee')}?",
                "employee_name": state.get("employee_name", ""),
                "policy_name": state.get("policy_name", ""),
                "start_date": str(state.get("start_date", "")),
                "end_date": str(state.get("end_date", "")),
                "total_days": state.get("total_days", 0),
                "reason": state.get("reason", ""),
                "requires_hr_review": state.get("requires_hr_review", False),
            }
        )

        # decision_data is returned by Command(resume={"decision": "...", "remarks": "..."})
        decision = (
            decision_data.get("decision", "pending")
            if isinstance(decision_data, dict)
            else str(decision_data)
        )
        remarks = (
            decision_data.get("remarks", "") if isinstance(decision_data, dict) else ""
        )

        if decision == "rejected":
            # Handle rejection: update leave request and restore balance
            if state.get("request_id"):
                result = await session.execute(
                    select(LeaveRequest).where(LeaveRequest.id == state["request_id"])
                )
                leave_request = result.scalar_one_or_none()
                if leave_request:
                    leave_request.status = LeaveStatus.REJECTED.value
                    leave_request.approver_id = context.current_user_id
                    leave_request.approved_at = date.today()
                    leave_request.approver_remarks = remarks

                await _restore_pending_balance(state, session, context.tenant_id)

            return Command(
                goto=END,
                update={
                    "status": WorkflowStatus.REJECTED,
                    "manager_decision": DecisionType.REJECTED,
                    "manager_remarks": remarks,
                    "messages": [
                        {
                            "role": "manager",
                            "content": f"Rejected: {remarks or 'No reason'}",
                        }
                    ],
                    "updated_at": datetime.now(),
                },
            )

        elif decision == "approved":
            if state.get("requires_hr_review"):
                # Forward to HR for long leaves
                return Command(
                    goto="await_hr",
                    update={
                        "status": WorkflowStatus.PENDING_HR_REVIEW,
                        "manager_decision": DecisionType.APPROVED,
                        "manager_remarks": remarks,
                        "messages": [
                            {
                                "role": "manager",
                                "content": f"Approved. Forwarding to HR (leave > {HR_REVIEW_THRESHOLD_DAYS} days).",
                            }
                        ],
                        "updated_at": datetime.now(),
                    },
                )
            else:
                # Finalize approval directly
                return Command(
                    goto="finalize_approval",
                    update={
                        "manager_decision": DecisionType.APPROVED,
                        "manager_remarks": remarks,
                        "messages": [{"role": "manager", "content": "Approved!"}],
                        "updated_at": datetime.now(),
                    },
                )

        # Pending or unknown - should not happen in normal flow
        return Command(goto=END, update={"updated_at": datetime.now()})

    async def hr_approval(
        state: WorkflowState,
    ) -> Command[Literal["finalize_approval", END]]:
        """
        HR approval node with human-in-the-loop using interrupt().

        Only reached for leaves exceeding the threshold (e.g., > 5 days).
        """
        # Use interrupt() to pause for HR input
        decision_data = interrupt(
            {
                "type": "hr_approval",
                "question": f"HR review for {state.get('employee_name', 'employee')}'s leave request",
                "employee_name": state.get("employee_name", ""),
                "policy_name": state.get("policy_name", ""),
                "start_date": str(state.get("start_date", "")),
                "end_date": str(state.get("end_date", "")),
                "total_days": state.get("total_days", 0),
                "reason": state.get("reason", ""),
                "manager_remarks": state.get("manager_remarks", ""),
            }
        )

        decision = (
            decision_data.get("decision", "pending")
            if isinstance(decision_data, dict)
            else str(decision_data)
        )
        remarks = (
            decision_data.get("remarks", "") if isinstance(decision_data, dict) else ""
        )

        if decision == "rejected":
            # Handle HR rejection
            if state.get("request_id"):
                result = await session.execute(
                    select(LeaveRequest).where(LeaveRequest.id == state["request_id"])
                )
                leave_request = result.scalar_one_or_none()
                if leave_request:
                    leave_request.status = LeaveStatus.REJECTED.value
                    leave_request.approver_remarks = (
                        f"Manager: {state.get('manager_remarks', '')}\nHR: {remarks}"
                    )

                await _restore_pending_balance(state, session, context.tenant_id)

            return Command(
                goto=END,
                update={
                    "status": WorkflowStatus.REJECTED,
                    "hr_decision": DecisionType.REJECTED,
                    "hr_remarks": remarks,
                    "messages": [
                        {
                            "role": "hr",
                            "content": f"Rejected by HR: {remarks or 'No reason'}",
                        }
                    ],
                    "updated_at": datetime.now(),
                },
            )

        elif decision == "approved":
            return Command(
                goto="finalize_approval",
                update={
                    "hr_decision": DecisionType.APPROVED,
                    "hr_remarks": remarks,
                    "messages": [{"role": "hr", "content": "Approved by HR!"}],
                    "updated_at": datetime.now(),
                },
            )

        return Command(goto=END, update={"updated_at": datetime.now()})

    async def finalize_approval(state: WorkflowState) -> dict[str, Any]:
        """Finalize the leave approval - update request and balance."""
        await _finalize_approval(
            state, session, context.tenant_id, context.current_user_id
        )
        return {
            "status": WorkflowStatus.APPROVED,
            "messages": [
                {"role": "system", "content": "Leave request approved and finalized."}
            ],
            "updated_at": datetime.now(),
        }

    return {
        "validate": validate_request,
        "create_request": create_leave_request,
        "manager_approval": manager_approval,
        "await_hr": hr_approval,
        "finalize_approval": finalize_approval,
    }


def route_after_validation(state: WorkflowState) -> str:
    """Route based on validation result."""
    status = state.get("status")
    if status == WorkflowStatus.VALIDATION_FAILED or (
        isinstance(status, str) and status == WorkflowStatus.VALIDATION_FAILED.value
    ):
        return END
    return "create_request"


def build_leave_workflow(nodes: dict[str, NodeFunc]) -> StateGraph:
    """
    Build the leave approval workflow graph with provided nodes.

    Flow:
    1. validate → (fail) → END
                → (pass) → create_request
    2. create_request → manager_approval
    3. manager_approval → [INTERRUPT via interrupt()]
       - On resume: approved (no HR) → finalize_approval → END
       - On resume: approved (HR needed) → await_hr
       - On resume: rejected → END
    4. await_hr → [INTERRUPT via interrupt()]
       - On resume: approved → finalize_approval → END
       - On resume: rejected → END
    5. finalize_approval → END

    Note: The manager_approval and await_hr nodes use interrupt() internally,
    which pauses execution until resumed with Command(resume=value).
    The nodes return Command(goto=...) for explicit routing.
    """
    workflow = StateGraph(WorkflowState)

    workflow.add_node("validate", nodes["validate"])
    workflow.add_node("create_request", nodes["create_request"])
    workflow.add_node("manager_approval", nodes["manager_approval"])
    workflow.add_node("await_hr", nodes["await_hr"])
    workflow.add_node("finalize_approval", nodes["finalize_approval"])

    workflow.set_entry_point("validate")

    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {"create_request": "create_request", END: END},
    )
    workflow.add_edge("create_request", "manager_approval")
    # manager_approval uses Command(goto=...) for routing, no edges needed
    # await_hr uses Command(goto=...) for routing, no edges needed
    workflow.add_edge("finalize_approval", END)

    return workflow


def _get_postgres_connection_string() -> str:
    """Convert SQLAlchemy database URL to psycopg format for LangGraph checkpoint."""
    db_url = settings.database_url
    # SQLAlchemy uses: postgresql+asyncpg://user:pass@host:port/db
    # psycopg expects: postgresql://user:pass@host:port/db
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql://")
    elif db_url.startswith("postgresql://"):
        return db_url
    else:
        raise ValueError(
            f"Unsupported database URL format for LangGraph checkpoint: {db_url}"
        )


class LeaveWorkflowRunner:
    """
    Runner for the leave approval workflow.

    Uses AsyncPostgresSaver for persistent checkpoints that survive
    server restarts. Each operation builds a graph with context-aware
    nodes using the closure pattern.

    Human-in-the-loop is implemented using the interrupt() function
    (LangGraph's recommended pattern), with resume via Command(resume=value).
    """

    def __init__(self, checkpointer: AsyncPostgresSaver):
        self._checkpointer = checkpointer

    def _compile_app_with_context(self, context: WorkflowContext):
        """Compile the workflow graph with context-aware nodes."""
        nodes = create_workflow_nodes(context)
        graph = build_leave_workflow(nodes)
        # No interrupt_before needed - we use interrupt() inside nodes
        return graph.compile(checkpointer=self._checkpointer)

    async def start_leave_request(
        self,
        context: WorkflowContext,
        request: LeaveRequestInput,
    ) -> WorkflowResult:
        """Start a new leave request workflow."""
        thread_id = f"leave_{context.tenant_id}_{request.employee_id}_{int(datetime.now().timestamp())}"

        start_day_type = _parse_day_type(request.start_day_type)
        end_day_type = _parse_day_type(request.end_day_type)

        now = datetime.now()
        initial_state: WorkflowState = {
            "tenant_id": context.tenant_id,
            "employee_id": request.employee_id,
            "policy_id": request.policy_id,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "reason": request.reason,
            "start_day_type": start_day_type,
            "end_day_type": end_day_type,
            "status": WorkflowStatus.PENDING_VALIDATION,
            "validation_errors": [],
            "manager_decision": DecisionType.PENDING,
            "manager_remarks": "",
            "hr_decision": DecisionType.PENDING,
            "hr_remarks": "",
            "requires_hr_review": False,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }

        config = {"configurable": {"thread_id": thread_id}}
        app = self._compile_app_with_context(context)

        final_state: dict[str, Any] = dict(initial_state)
        async for event in app.astream(initial_state, config):
            for node_output in event.values():
                if isinstance(node_output, dict):
                    final_state.update(node_output)

        return WorkflowResult.from_state(thread_id, final_state)

    async def submit_manager_decision(
        self,
        thread_id: str,
        context: WorkflowContext,
        decision: Literal["approved", "rejected"],
        remarks: str = "",
    ) -> WorkflowResult:
        """Submit manager's decision and resume workflow using Command(resume=...)."""
        config = {"configurable": {"thread_id": thread_id}}
        app = self._compile_app_with_context(context)

        current_state = await app.aget_state(config)
        if not current_state or not current_state.values:
            return WorkflowResult(
                thread_id=thread_id,
                status=WorkflowStatus.PENDING_VALIDATION,
                message="Workflow not found",
            )

        # Resume with Command(resume=value) - the official LangGraph pattern
        # The value is returned by the interrupt() call in manager_approval node
        resume_value = {"decision": decision, "remarks": remarks}

        final_state: dict[str, Any] = dict(current_state.values)
        async for event in app.astream(Command(resume=resume_value), config):
            for node_output in event.values():
                if isinstance(node_output, dict):
                    final_state.update(node_output)

        return WorkflowResult.from_state(thread_id, final_state)

    async def submit_hr_decision(
        self,
        thread_id: str,
        context: WorkflowContext,
        decision: Literal["approved", "rejected"],
        remarks: str = "",
    ) -> WorkflowResult:
        """Submit HR's decision and complete workflow using Command(resume=...)."""
        config = {"configurable": {"thread_id": thread_id}}
        app = self._compile_app_with_context(context)

        current_state = await app.aget_state(config)
        if not current_state or not current_state.values:
            return WorkflowResult(
                thread_id=thread_id,
                status=WorkflowStatus.PENDING_VALIDATION,
                message="Workflow not found",
            )

        # Resume with Command(resume=value) - the official LangGraph pattern
        resume_value = {"decision": decision, "remarks": remarks}

        final_state: dict[str, Any] = dict(current_state.values)
        async for event in app.astream(Command(resume=resume_value), config):
            for node_output in event.values():
                if isinstance(node_output, dict):
                    final_state.update(node_output)

        return WorkflowResult.from_state(thread_id, final_state)

    async def get_workflow_state(self, thread_id: str) -> WorkflowResult | None:
        """Get current state of a workflow (stateless, no context needed)."""
        config = {"configurable": {"thread_id": thread_id}}
        # For read-only state access, use dummy nodes that won't be executed
        dummy_nodes: dict[str, NodeFunc] = {
            "validate": lambda s: {},
            "create_request": lambda s: {},
            "manager_approval": lambda s: Command(goto=END),
            "await_hr": lambda s: Command(goto=END),
            "finalize_approval": lambda s: {},
        }
        graph = build_leave_workflow(dummy_nodes)
        app = graph.compile(checkpointer=self._checkpointer)
        state = await app.aget_state(config)
        if state and state.values:
            return WorkflowResult.from_state(thread_id, state.values)
        return None


_runner: LeaveWorkflowRunner | None = None
_checkpointer: AsyncPostgresSaver | None = None
_runner_lock: asyncio.Lock | None = None


def _get_runner_lock() -> asyncio.Lock:
    """Get or create the async lock (must be called in async context)."""
    global _runner_lock
    if _runner_lock is None:
        _runner_lock = asyncio.Lock()
    return _runner_lock


async def get_leave_workflow_runner() -> LeaveWorkflowRunner:
    """
    Get the cached leave workflow runner singleton.

    Uses asyncio.Lock for thread-safe initialization in async context.
    """
    global _runner, _checkpointer

    # Fast path: runner already initialized
    if _runner is not None:
        return _runner

    # Slow path: acquire lock and initialize
    async with _get_runner_lock():
        # Double-check after acquiring lock
        if _runner is not None:
            return _runner

        conn_string = _get_postgres_connection_string()
        _checkpointer = AsyncPostgresSaver.from_conn_string(conn_string)
        await _checkpointer.setup()
        _runner = LeaveWorkflowRunner(_checkpointer)
        logger.info("Leave workflow runner initialized with PostgreSQL checkpointer")
        return _runner


async def create_leave_workflow_runner() -> LeaveWorkflowRunner:
    """Create a new leave workflow runner (for testing or per-request use)."""
    conn_string = _get_postgres_connection_string()
    checkpointer = AsyncPostgresSaver.from_conn_string(conn_string)
    await checkpointer.setup()
    return LeaveWorkflowRunner(checkpointer)
