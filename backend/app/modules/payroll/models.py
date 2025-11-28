"""Payroll models."""

from datetime import date
from enum import Enum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import TenantBaseModel


class PayrollStatus(str, Enum):
    """Payroll status."""

    DRAFT = "draft"
    PROCESSING = "processing"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class ComponentType(str, Enum):
    """Salary component type."""

    EARNING = "earning"
    DEDUCTION = "deduction"
    REIMBURSEMENT = "reimbursement"


class SalaryComponent(TenantBaseModel):
    """Salary component definition."""

    __tablename__ = "salary_components"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    component_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Calculation
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=True)
    calculation_formula: Mapped[str | None] = mapped_column(String(255), nullable=True)
    percentage_of: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Tax
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pf_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_esi_applicable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<SalaryComponent {self.code}: {self.name}>"


class SalaryStructure(TenantBaseModel):
    """Salary structure template."""

    __tablename__ = "salary_structures"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    components: Mapped[list["SalaryStructureComponent"]] = relationship(
        "SalaryStructureComponent",
        back_populates="structure",
    )

    def __repr__(self) -> str:
        return f"<SalaryStructure {self.name}>"


class SalaryStructureComponent(TenantBaseModel):
    """Component in a salary structure."""

    __tablename__ = "salary_structure_components"

    structure_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("salary_structures.id"),
        nullable=False,
    )
    component_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("salary_components.id"),
        nullable=False,
    )

    # Value
    default_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    structure: Mapped[SalaryStructure] = relationship(
        "SalaryStructure",
        back_populates="components",
    )
    component: Mapped[SalaryComponent] = relationship("SalaryComponent")


class EmployeeSalary(TenantBaseModel):
    """Employee salary assignment."""

    __tablename__ = "employee_salaries"

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    structure_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("salary_structures.id"),
        nullable=False,
    )

    # CTC breakdown
    annual_ctc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    monthly_gross: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Effective dates
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    structure: Mapped[SalaryStructure] = relationship("SalaryStructure")
    components: Mapped[list["EmployeeSalaryComponent"]] = relationship(
        "EmployeeSalaryComponent",
        back_populates="employee_salary",
    )

    def __repr__(self) -> str:
        return f"<EmployeeSalary {self.employee_id}: {self.annual_ctc}>"


class EmployeeSalaryComponent(TenantBaseModel):
    """Individual salary component for an employee."""

    __tablename__ = "employee_salary_components"

    employee_salary_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employee_salaries.id"),
        nullable=False,
    )
    component_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("salary_components.id"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    employee_salary: Mapped[EmployeeSalary] = relationship(
        "EmployeeSalary",
        back_populates="components",
    )
    component: Mapped[SalaryComponent] = relationship("SalaryComponent")


class PayrollPeriod(TenantBaseModel):
    """Payroll processing period."""

    __tablename__ = "payroll_periods"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=PayrollStatus.DRAFT.value)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    payslips: Mapped[list["Payslip"]] = relationship(
        "Payslip",
        back_populates="period",
    )

    def __repr__(self) -> str:
        return f"<PayrollPeriod {self.month}/{self.year}>"


class Payslip(TenantBaseModel):
    """Employee payslip."""

    __tablename__ = "payslips"

    employee_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payroll_periods.id"),
        nullable=False,
    )

    # Salary details
    gross_earnings: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net_pay: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    # Attendance
    working_days: Mapped[int] = mapped_column(Integer, default=0)
    present_days: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    leave_days: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    lop_days: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=PayrollStatus.DRAFT.value)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    period: Mapped[PayrollPeriod] = relationship(
        "PayrollPeriod", back_populates="payslips"
    )
    items: Mapped[list["PayslipItem"]] = relationship(
        "PayslipItem",
        back_populates="payslip",
    )

    def __repr__(self) -> str:
        return f"<Payslip {self.employee_id}: {self.net_pay}>"


class PayslipItem(TenantBaseModel):
    """Individual item in a payslip."""

    __tablename__ = "payslip_items"

    payslip_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payslips.id"),
        nullable=False,
    )
    component_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("salary_components.id"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    payslip: Mapped[Payslip] = relationship("Payslip", back_populates="items")
    component: Mapped[SalaryComponent] = relationship("SalaryComponent")
