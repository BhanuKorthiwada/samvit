"""Payroll schemas."""

from datetime import date
from enum import Enum

from pydantic import Field

from app.shared.schemas import BaseSchema, TenantEntitySchema


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


# --- Salary Component Schemas ---


class SalaryComponentCreate(BaseSchema):
    """Create salary component."""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    component_type: ComponentType
    description: str | None = None
    is_fixed: bool = True
    calculation_formula: str | None = None
    percentage_of: str | None = None
    is_taxable: bool = True
    is_pf_applicable: bool = False
    is_esi_applicable: bool = False


class SalaryComponentUpdate(BaseSchema):
    """Update salary component."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_fixed: bool | None = None
    calculation_formula: str | None = None
    is_taxable: bool | None = None
    is_pf_applicable: bool | None = None
    is_esi_applicable: bool | None = None
    is_active: bool | None = None


class SalaryComponentResponse(TenantEntitySchema):
    """Salary component response."""

    name: str
    code: str
    component_type: ComponentType
    description: str | None
    is_fixed: bool
    calculation_formula: str | None
    percentage_of: str | None
    is_taxable: bool
    is_pf_applicable: bool
    is_esi_applicable: bool
    is_active: bool
    is_system: bool


# --- Salary Structure Schemas ---


class StructureComponentInput(BaseSchema):
    """Component input for salary structure."""

    component_id: str
    default_amount: float | None = None
    percentage: float | None = None


class SalaryStructureCreate(BaseSchema):
    """Create salary structure."""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    components: list[StructureComponentInput] = []


class SalaryStructureUpdate(BaseSchema):
    """Update salary structure."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class SalaryStructureResponse(TenantEntitySchema):
    """Salary structure response."""

    name: str
    code: str
    description: str | None
    is_active: bool


# --- Employee Salary Schemas ---


class EmployeeSalaryComponentInput(BaseSchema):
    """Component input for employee salary."""

    component_id: str
    amount: float = Field(..., ge=0)


class EmployeeSalaryCreate(BaseSchema):
    """Create employee salary."""

    employee_id: str
    structure_id: str
    annual_ctc: float = Field(..., gt=0)
    effective_from: date
    components: list[EmployeeSalaryComponentInput] = []


class EmployeeSalaryResponse(TenantEntitySchema):
    """Employee salary response."""

    employee_id: str
    structure_id: str
    annual_ctc: float
    monthly_gross: float
    effective_from: date
    effective_to: date | None
    is_current: bool


class EmployeeSalaryDetail(EmployeeSalaryResponse):
    """Detailed employee salary with components."""

    components: list[dict]  # List of {component_name, component_type, amount}


# --- Payroll Period Schemas ---


class PayrollPeriodCreate(BaseSchema):
    """Create payroll period."""

    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)
    start_date: date
    end_date: date
    payment_date: date | None = None


class PayrollPeriodUpdate(BaseSchema):
    """Update payroll period."""

    payment_date: date | None = None
    status: PayrollStatus | None = None


class PayrollPeriodResponse(TenantEntitySchema):
    """Payroll period response."""

    name: str
    month: int
    year: int
    start_date: date
    end_date: date
    payment_date: date | None
    status: PayrollStatus
    is_locked: bool


# --- Payslip Schemas ---


class PayslipItemResponse(BaseSchema):
    """Payslip item response."""

    component_name: str
    component_code: str
    component_type: ComponentType
    amount: float


class PayslipResponse(TenantEntitySchema):
    """Payslip response."""

    employee_id: str
    period_id: str
    gross_earnings: float
    total_deductions: float
    net_pay: float
    working_days: int
    present_days: float
    leave_days: float
    lop_days: float
    status: PayrollStatus
    is_published: bool


class PayslipDetail(PayslipResponse):
    """Detailed payslip with items."""

    items: list[PayslipItemResponse]


class PayrollSummary(BaseSchema):
    """Payroll summary for a period."""

    period_id: str
    month: int
    year: int
    total_employees: int
    total_gross: float
    total_deductions: float
    total_net_pay: float
    status: PayrollStatus
