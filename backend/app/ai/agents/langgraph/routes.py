"""API routes for Leave Approval Workflow."""

import logging
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.ai.agents.langgraph.leave_workflow import (
    LeaveRequestInput,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    get_leave_workflow_runner,
)
from app.core.database import DbSession
from app.core.security import CurrentUser
from app.core.tenancy import TenantDep
from app.modules.employees.models import Employee

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leave-workflow", tags=["Leave Workflow"])


def _serialize_status(status_value: WorkflowStatus | str) -> str:
    """Serialize WorkflowStatus enum to string."""
    if isinstance(status_value, WorkflowStatus):
        return status_value.value
    return str(status_value)


class StartLeaveRequestBody(BaseModel):
    """Request body for starting a leave request."""

    policy_id: str = Field(..., description="Leave policy ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date")
    reason: str = Field(
        ..., min_length=1, max_length=500, description="Reason for leave"
    )
    start_day_type: str = Field(
        default="full", description="full, first_half, or second_half"
    )
    end_day_type: str = Field(
        default="full", description="full, first_half, or second_half"
    )


class ManagerDecisionBody(BaseModel):
    """Request body for manager's decision."""

    thread_id: str = Field(..., description="Workflow thread ID")
    decision: Literal["approved", "rejected"] = Field(
        ..., description="Approval decision"
    )
    remarks: str = Field(default="", max_length=500, description="Optional remarks")


class HRDecisionBody(BaseModel):
    """Request body for HR's decision."""

    thread_id: str = Field(..., description="Workflow thread ID")
    decision: Literal["approved", "rejected"] = Field(
        ..., description="Approval decision"
    )
    remarks: str = Field(default="", max_length=500, description="Optional remarks")


class WorkflowResponse(BaseModel):
    """Generic workflow response."""

    thread_id: str
    status: str
    message: str
    data: dict | None = None


@router.post(
    "/start",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start leave request workflow",
)
async def start_leave_request(
    body: StartLeaveRequestBody,
    current_user: CurrentUser,
    tenant: TenantDep,
    session: DbSession,
) -> WorkflowResponse:
    """
    Start a new leave request workflow.

    This will:
    1. Validate the request against policy rules
    2. Check leave balance
    3. Create a pending leave request
    4. Wait for manager approval

    Returns a thread_id to track the workflow.
    """
    context = WorkflowContext(
        session=session,
        tenant_id=tenant.tenant_id,
        current_user_id=current_user.id,
        current_user_role="employee",
    )

    request_input = LeaveRequestInput(
        employee_id=current_user.id,
        policy_id=body.policy_id,
        start_date=body.start_date,
        end_date=body.end_date,
        reason=body.reason,
        start_day_type=body.start_day_type,
        end_day_type=body.end_day_type,
    )

    try:
        runner = await get_leave_workflow_runner()
        result: WorkflowResult = await runner.start_leave_request(
            context, request_input
        )

        # Check for validation failures
        if result.status == WorkflowStatus.VALIDATION_FAILED:
            return WorkflowResponse(
                thread_id=result.thread_id,
                status="validation_failed",
                message=result.message,
                data={"errors": result.validation_errors},
            )

        await session.commit()

        return WorkflowResponse(
            thread_id=result.thread_id,
            status=_serialize_status(result.status),
            message=result.message,
            data={
                "request_id": result.request_id,
                "total_days": result.total_days,
                "policy_name": result.policy_name,
                "manager_name": result.manager_name,
            },
        )

    except Exception as e:
        logger.exception("Error starting leave workflow: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start leave request workflow",
        ) from e


async def _get_employee_manager_id(
    session: DbSession,
    tenant_id: str,
    employee_id: str,
) -> str | None:
    """Get the reporting manager ID for an employee."""
    result = await session.execute(
        select(Employee.reporting_manager_id).where(
            Employee.tenant_id == tenant_id,
            Employee.id == employee_id,
        )
    )
    return result.scalar_one_or_none()


@router.post(
    "/manager/decide",
    response_model=WorkflowResponse,
    summary="Submit manager decision",
)
async def submit_manager_decision(
    body: ManagerDecisionBody,
    current_user: CurrentUser,
    tenant: TenantDep,
    session: DbSession,
) -> WorkflowResponse:
    """
    Submit manager's approval or rejection decision.

    Only the reporting manager of the employee can approve/reject.
    """
    context = WorkflowContext(
        session=session,
        tenant_id=tenant.tenant_id,
        current_user_id=current_user.id,
        current_user_role="manager",
    )

    try:
        runner = await get_leave_workflow_runner()

        # Verify workflow exists and is awaiting manager approval
        state_info = await runner.get_workflow_state(body.thread_id)
        if not state_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        # Verify current user is the manager of the employee
        # Get the employee_id from the workflow state (thread_id format: leave_{tenant}_{employee}_{ts})
        thread_parts = body.thread_id.split("_")
        if len(thread_parts) >= 3:
            workflow_employee_id = thread_parts[2]
            manager_id = await _get_employee_manager_id(
                session, tenant.tenant_id, workflow_employee_id
            )
            if manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the reporting manager can approve/reject this request",
                )

        # Verify workflow is awaiting manager approval
        if state_info.status != WorkflowStatus.PENDING_MANAGER_APPROVAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This leave request is not awaiting manager approval. Current status: {_serialize_status(state_info.status)}",
            )

        result: WorkflowResult = await runner.submit_manager_decision(
            thread_id=body.thread_id,
            context=context,
            decision=body.decision,
            remarks=body.remarks,
        )

        await session.commit()

        return WorkflowResponse(
            thread_id=body.thread_id,
            status=_serialize_status(result.status),
            message=result.message,
            data={
                "employee_name": result.employee_name,
                "total_days": result.total_days,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing manager decision: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process manager decision",
        ) from e


@router.post(
    "/hr/decide",
    response_model=WorkflowResponse,
    summary="Submit HR decision",
)
async def submit_hr_decision(
    body: HRDecisionBody,
    current_user: CurrentUser,
    tenant: TenantDep,
    session: DbSession,
) -> WorkflowResponse:
    """
    Submit HR's approval or rejection decision.

    Only HR role can submit this decision.
    This is only needed for leaves > 5 days.
    """
    # TODO: Add HR role verification from user roles
    # if "hr" not in current_user.roles:
    #     raise HTTPException(status_code=403, detail="Only HR can approve this request")

    context = WorkflowContext(
        session=session,
        tenant_id=tenant.tenant_id,
        current_user_id=current_user.id,
        current_user_role="hr",
    )

    try:
        runner = await get_leave_workflow_runner()

        # Verify workflow is awaiting HR review
        state_info = await runner.get_workflow_state(body.thread_id)
        if not state_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        if state_info.status != WorkflowStatus.PENDING_HR_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This leave request is not awaiting HR review. Current status: {_serialize_status(state_info.status)}",
            )

        result: WorkflowResult = await runner.submit_hr_decision(
            thread_id=body.thread_id,
            context=context,
            decision=body.decision,
            remarks=body.remarks,
        )

        await session.commit()

        return WorkflowResponse(
            thread_id=body.thread_id,
            status=_serialize_status(result.status),
            message=result.message,
            data={
                "employee_name": result.employee_name,
                "total_days": result.total_days,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing HR decision: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process HR decision",
        ) from e


@router.get(
    "/status/{thread_id}",
    response_model=WorkflowResponse,
    summary="Get workflow status",
)
async def get_workflow_status(
    thread_id: str,
    current_user: CurrentUser,
    tenant: TenantDep,
    session: DbSession,
) -> WorkflowResponse:
    """Get the current status of a leave workflow."""
    try:
        runner = await get_leave_workflow_runner()
        result = await runner.get_workflow_state(thread_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        # Access control: only allow employee, their manager, or HR to view
        thread_parts = thread_id.split("_")
        if len(thread_parts) >= 3:
            workflow_employee_id = thread_parts[2]
            workflow_tenant_id = thread_parts[1]

            # Verify tenant matches
            if workflow_tenant_id != tenant.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workflow not found",
                )

            # Allow if user is the employee, their manager, or HR
            is_employee = current_user.id == workflow_employee_id
            manager_id = await _get_employee_manager_id(
                session, tenant.tenant_id, workflow_employee_id
            )
            is_manager = manager_id == current_user.id if manager_id else False
            # TODO: Add HR role check when role system is available

            if not (is_employee or is_manager):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this workflow",
                )

        return WorkflowResponse(
            thread_id=thread_id,
            status=_serialize_status(result.status),
            message=result.message,
            data={
                "employee_name": result.employee_name,
                "manager_name": result.manager_name,
                "policy_name": result.policy_name,
                "total_days": result.total_days,
                "start_date": str(result.start_date) if result.start_date else None,
                "end_date": str(result.end_date) if result.end_date else None,
                "request_id": result.request_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting workflow status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow status",
        ) from e
