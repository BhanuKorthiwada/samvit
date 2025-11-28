"""Employee schemas."""

from datetime import date
from enum import Enum

from pydantic import EmailStr, Field

from app.shared.schemas import BaseSchema, TenantEntitySchema


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


# --- Department Schemas ---


class DepartmentCreate(BaseSchema):
    """Create department schema."""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    parent_id: str | None = None
    head_id: str | None = None


class DepartmentUpdate(BaseSchema):
    """Update department schema."""

    name: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = None
    parent_id: str | None = None
    head_id: str | None = None
    is_active: bool | None = None


class DepartmentResponse(TenantEntitySchema):
    """Department response schema."""

    name: str
    code: str
    description: str | None
    parent_id: str | None
    head_id: str | None
    is_active: bool


class DepartmentSummary(BaseSchema):
    """Brief department info."""

    id: str
    name: str
    code: str


# --- Position Schemas ---


class PositionCreate(BaseSchema):
    """Create position schema."""

    title: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    level: int = Field(default=1, ge=1, le=10)
    min_salary: float | None = None
    max_salary: float | None = None
    department_id: str | None = None


class PositionUpdate(BaseSchema):
    """Update position schema."""

    title: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = None
    level: int | None = Field(default=None, ge=1, le=10)
    min_salary: float | None = None
    max_salary: float | None = None
    department_id: str | None = None
    is_active: bool | None = None


class PositionResponse(TenantEntitySchema):
    """Position response schema."""

    title: str
    code: str
    description: str | None
    level: int
    min_salary: float | None
    max_salary: float | None
    department_id: str | None
    is_active: bool


class PositionSummary(BaseSchema):
    """Brief position info."""

    id: str
    title: str
    code: str
    level: int


# --- Employee Schemas ---


class EmployeeCreate(BaseSchema):
    """Create employee schema."""

    employee_code: str = Field(..., min_length=1, max_length=20)

    # Personal Info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    personal_email: EmailStr | None = None

    # Demographics
    date_of_birth: date | None = None
    gender: Gender | None = None
    marital_status: MaritalStatus | None = None
    nationality: str = Field(default="Indian", max_length=50)

    # Address
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str = Field(default="India", max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)

    # Employment
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    date_of_joining: date
    probation_end_date: date | None = None

    # Organization
    department_id: str | None = None
    position_id: str | None = None
    reporting_manager_id: str | None = None

    # Identity (optional at creation)
    pan_number: str | None = Field(default=None, max_length=20)
    aadhaar_number: str | None = Field(default=None, max_length=20)

    # Bank Details (optional at creation)
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account_number: str | None = Field(default=None, max_length=30)
    ifsc_code: str | None = Field(default=None, max_length=15)


class EmployeeUpdate(BaseSchema):
    """Update employee schema."""

    # Personal Info
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    personal_email: EmailStr | None = None

    # Demographics
    date_of_birth: date | None = None
    gender: Gender | None = None
    marital_status: MaritalStatus | None = None
    nationality: str | None = Field(default=None, max_length=50)

    # Address
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)

    # Employment
    employment_type: EmploymentType | None = None
    employment_status: EmploymentStatus | None = None
    date_of_leaving: date | None = None
    probation_end_date: date | None = None

    # Organization
    department_id: str | None = None
    position_id: str | None = None
    reporting_manager_id: str | None = None

    # Identity
    pan_number: str | None = Field(default=None, max_length=20)
    aadhaar_number: str | None = Field(default=None, max_length=20)
    passport_number: str | None = Field(default=None, max_length=20)

    # Bank Details
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account_number: str | None = Field(default=None, max_length=30)
    ifsc_code: str | None = Field(default=None, max_length=15)

    # Profile
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = None


class EmployeeResponse(TenantEntitySchema):
    """Employee response schema."""

    employee_code: str

    # Personal Info
    first_name: str
    last_name: str
    email: str
    phone: str | None
    personal_email: str | None

    # Demographics
    date_of_birth: date | None
    gender: str | None
    marital_status: str | None
    nationality: str

    # Address
    address: str | None
    city: str | None
    state: str | None
    country: str
    postal_code: str | None

    # Employment
    employment_type: EmploymentType
    employment_status: EmploymentStatus
    date_of_joining: date
    date_of_leaving: date | None
    probation_end_date: date | None

    # Organization
    department_id: str | None
    position_id: str | None
    reporting_manager_id: str | None

    # Profile
    avatar_url: str | None
    bio: str | None
    is_active: bool

    # Computed
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class EmployeeSummary(BaseSchema):
    """Brief employee info for lists."""

    id: str
    employee_code: str
    first_name: str
    last_name: str
    email: str
    department_id: str | None
    position_id: str | None
    employment_status: EmploymentStatus
    is_active: bool

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class EmployeeDirectory(BaseSchema):
    """Employee directory entry."""

    id: str
    employee_code: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    avatar_url: str | None
    department: DepartmentSummary | None = None
    position: PositionSummary | None = None
