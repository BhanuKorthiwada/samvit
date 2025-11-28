"""Leave management models."""

from datetime import date
from enum import Enum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBaseModel


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


class LeavePolicy(TenantBaseModel):
    """Leave policy configuration."""

    __tablename__ = "leave_policies"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Allocation
    annual_allocation: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    max_accumulation: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    carry_forward_limit: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    # Rules
    min_days: Mapped[float] = mapped_column(Numeric(3, 1), default=0.5)
    max_days: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    advance_notice_days: Mapped[int] = mapped_column(Integer, default=0)
    requires_attachment: Mapped[bool] = mapped_column(Boolean, default=False)
    attachment_after_days: Mapped[int] = mapped_column(Integer, default=2)

    # Applicability
    applicable_gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    min_tenure_months: Mapped[int] = mapped_column(Integer, default=0)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<LeavePolicy {self.name}: {self.leave_type}>"


class LeaveBalance(TenantBaseModel):
    """Employee leave balance."""

    __tablename__ = "leave_balances"

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    policy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leave_policies.id"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Balances
    opening_balance: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    credited: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    used: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    pending: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    # Relationships
    policy: Mapped[LeavePolicy] = relationship("LeavePolicy")

    @property
    def available(self) -> float:
        """Calculate available balance."""
        return (
            float(self.opening_balance)
            + float(self.credited)
            - float(self.used)
            - float(self.pending)
        )

    def __repr__(self) -> str:
        return f"<LeaveBalance {self.employee_id} {self.year}: {self.available}>"


class LeaveRequest(TenantBaseModel):
    """Leave request."""

    __tablename__ = "leave_requests"

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    policy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("leave_policies.id"),
        nullable=False,
    )

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_day_type: Mapped[str] = mapped_column(String(20), default=DayType.FULL.value)
    end_day_type: Mapped[str] = mapped_column(String(20), default=DayType.FULL.value)
    total_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    # Details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=LeaveStatus.PENDING.value)
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Approval
    approver_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=True,
    )
    approved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    approver_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    policy: Mapped[LeavePolicy] = relationship("LeavePolicy")

    def __repr__(self) -> str:
        return (
            f"<LeaveRequest {self.employee_id}: {self.start_date} to {self.end_date}>"
        )


class Holiday(TenantBaseModel):
    """Public/company holidays."""

    __tablename__ = "holidays"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Holiday {self.name}: {self.date}>"
