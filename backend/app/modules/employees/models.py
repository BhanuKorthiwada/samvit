"""Employee models - Department, Position, Employee."""

from datetime import date
from enum import Enum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBaseModel


class EmploymentType(str, Enum):
    """Employment type."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    FREELANCE = "freelance"


class EmploymentStatus(str, Enum):
    """Employment status."""

    ACTIVE = "active"
    ON_NOTICE = "on_notice"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    RESIGNED = "resigned"


class Gender(str, Enum):
    """Gender options."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MaritalStatus(str, Enum):
    """Marital status."""

    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class Department(TenantBaseModel):
    """Department model."""

    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Parent department for hierarchy
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id"),
        nullable=True,
    )

    # Head of department
    head_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=True,
    )

    # Relationships
    parent: Mapped["Department | None"] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children",
    )
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
    )
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        foreign_keys="Employee.department_id",
    )

    def __repr__(self) -> str:
        return f"<Department {self.name}>"


class Position(TenantBaseModel):
    """Job position/title model."""

    __tablename__ = "positions"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)  # 1=Entry, 5=Senior, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Salary range
    min_salary: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_salary: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Department (optional - position can be cross-department)
    department_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id"),
        nullable=True,
    )

    # Relationships
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="position",
    )

    def __repr__(self) -> str:
        return f"<Position {self.title}>"


class Employee(TenantBaseModel):
    """Employee model - core HR entity."""

    __tablename__ = "employees"

    # Employee ID (company-specific)
    employee_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    personal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Demographics
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nationality: Mapped[str] = mapped_column(String(50), default="Indian")

    # Address
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Employment Details
    employment_type: Mapped[str] = mapped_column(
        String(20),
        default=EmploymentType.FULL_TIME.value,
    )
    employment_status: Mapped[str] = mapped_column(
        String(20),
        default=EmploymentStatus.ACTIVE.value,
    )
    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    date_of_leaving: Mapped[date | None] = mapped_column(Date, nullable=True)
    probation_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Organization
    department_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id"),
        nullable=True,
    )
    position_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("positions.id"),
        nullable=True,
    )
    reporting_manager_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=True,
    )

    # Identity Documents (India-specific)
    pan_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    aadhaar_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Bank Details
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ifsc_code: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # Profile
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    department: Mapped[Department | None] = relationship(
        "Department",
        back_populates="employees",
        foreign_keys=[department_id],
    )
    position: Mapped[Position | None] = relationship(
        "Position",
        back_populates="employees",
    )
    reporting_manager: Mapped["Employee | None"] = relationship(
        "Employee",
        remote_side="Employee.id",
        back_populates="direct_reports",
        foreign_keys=[reporting_manager_id],
    )
    direct_reports: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="reporting_manager",
        foreign_keys=[reporting_manager_id],
    )

    @property
    def full_name(self) -> str:
        """Get employee's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Employee {self.employee_code}: {self.full_name}>"
