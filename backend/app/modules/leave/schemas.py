"""Leave management schemas."""

from datetime import date as date_type
from enum import Enum

from pydantic import Field, model_validator

from app.shared.schemas import BaseSchema, TenantEntitySchema


class LeaveType(str, Enum):
    """Leave types."""

    CASUAL = "casual"
    SICK = "sick"
    EARNED = "earned"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    BEREAVEMENT = "bereavement"
    UNPAID = "unpaid"
    COMPENSATORY = "compensatory"
    WORK_FROM_HOME = "work_from_home"


class LeaveStatus(str, Enum):
    """Leave request status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    WITHDRAWN = "withdrawn"


class DayType(str, Enum):
    """Type of leave day."""

    FULL = "full"
    FIRST_HALF = "first_half"
    SECOND_HALF = "second_half"


# --- Leave Policy Schemas ---


class LeavePolicyCreate(BaseSchema):
    """Create leave policy."""

    name: str = Field(..., min_length=1, max_length=100)
    leave_type: LeaveType
    description: str | None = None
    annual_allocation: float = Field(default=0, ge=0)
    max_accumulation: float = Field(default=0, ge=0)
    carry_forward_limit: float = Field(default=0, ge=0)
    min_days: float = Field(default=0.5, ge=0.5)
    max_days: float | None = None
    advance_notice_days: int = Field(default=0, ge=0)
    requires_attachment: bool = False
    attachment_after_days: int = Field(default=2, ge=0)
    applicable_gender: str | None = None
    min_tenure_months: int = Field(default=0, ge=0)
    is_paid: bool = True


class LeavePolicyUpdate(BaseSchema):
    """Update leave policy."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    annual_allocation: float | None = Field(default=None, ge=0)
    max_accumulation: float | None = Field(default=None, ge=0)
    carry_forward_limit: float | None = Field(default=None, ge=0)
    min_days: float | None = Field(default=None, ge=0.5)
    max_days: float | None = None
    advance_notice_days: int | None = Field(default=None, ge=0)
    requires_attachment: bool | None = None
    is_active: bool | None = None


class LeavePolicyResponse(TenantEntitySchema):
    """Leave policy response."""

    name: str
    leave_type: LeaveType
    description: str | None
    annual_allocation: float
    max_accumulation: float
    carry_forward_limit: float
    min_days: float
    max_days: float | None
    advance_notice_days: int
    requires_attachment: bool
    attachment_after_days: int
    applicable_gender: str | None
    min_tenure_months: int
    is_paid: bool
    is_active: bool


# --- Leave Balance Schemas ---


class LeaveBalanceResponse(TenantEntitySchema):
    """Leave balance response."""

    employee_id: str
    policy_id: str
    year: int
    opening_balance: float
    credited: float
    used: float
    pending: float
    available: float


class LeaveBalanceSummary(BaseSchema):
    """Summary of all leave balances for an employee."""

    employee_id: str
    year: int
    balances: list[LeaveBalanceResponse]


# --- Leave Request Schemas ---


class LeaveRequestCreate(BaseSchema):
    """Create leave request."""

    policy_id: str
    start_date: date_type
    end_date: date_type
    start_day_type: DayType = DayType.FULL
    end_day_type: DayType = DayType.FULL
    reason: str = Field(..., min_length=10, max_length=1000)
    attachment_url: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        """Validate date range."""
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date")
        return self


class LeaveRequestUpdate(BaseSchema):
    """Update leave request (before approval)."""

    start_date: date_type | None = None
    end_date: date_type | None = None
    start_day_type: DayType | None = None
    end_day_type: DayType | None = None
    reason: str | None = Field(default=None, max_length=1000)
    attachment_url: str | None = None


class LeaveApproval(BaseSchema):
    """Approve/reject leave request."""

    action: str = Field(..., pattern="^(approve|reject)$")
    remarks: str | None = Field(default=None, max_length=500)


class LeaveRequestResponse(TenantEntitySchema):
    """Leave request response."""

    employee_id: str
    policy_id: str
    start_date: date_type
    end_date: date_type
    start_day_type: DayType
    end_day_type: DayType
    total_days: float
    reason: str
    status: LeaveStatus
    attachment_url: str | None
    approver_id: str | None
    approved_at: date_type | None
    approver_remarks: str | None


class LeaveRequestSummary(BaseSchema):
    """Brief leave request for lists."""

    id: str
    employee_id: str
    start_date: date_type
    end_date: date_type
    total_days: float
    leave_type: LeaveType
    status: LeaveStatus


# --- Holiday Schemas ---


class HolidayCreate(BaseSchema):
    """Create holiday."""

    name: str = Field(..., min_length=1, max_length=100)
    date: date_type
    description: str | None = None
    is_optional: bool = False


class HolidayUpdate(BaseSchema):
    """Update holiday."""

    name: str | None = Field(default=None, max_length=100)
    date: date_type | None = None
    description: str | None = None
    is_optional: bool | None = None
    is_active: bool | None = None


class HolidayResponse(TenantEntitySchema):
    """Holiday response."""

    name: str
    date: date_type
    description: str | None
    is_optional: bool
    is_active: bool
