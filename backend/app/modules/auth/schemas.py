"""Auth schemas."""

from enum import Enum

from pydantic import EmailStr, Field

from app.shared.schemas import BaseSchema, TenantEntitySchema


class UserRole(str, Enum):
    """User roles."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    HR_STAFF = "hr_staff"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class UserStatus(str, Enum):
    """User status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    LOCKED = "locked"


# --- Auth Requests ---


class LoginRequest(BaseSchema):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseSchema):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)


class ChangePasswordRequest(BaseSchema):
    """Change password request."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseSchema):
    """Reset password request."""

    token: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseSchema):
    """Forgot password request."""

    email: EmailStr


# --- Auth Responses ---


class TokenResponse(BaseSchema):
    """Token response after login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseSchema):
    """Refresh token request."""

    refresh_token: str


class RegisterResponse(BaseSchema):
    """Registration response with user and tokens."""

    user: "UserResponse"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- User Schemas ---


class UserCreate(BaseSchema):
    """Create user schema (admin use)."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    role: UserRole = UserRole.EMPLOYEE
    employee_id: str | None = None


class UserUpdate(BaseSchema):
    """Update user schema."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserResponse(TenantEntitySchema):
    """User response schema."""

    email: str
    first_name: str
    last_name: str
    phone: str | None
    avatar_url: str | None
    status: UserStatus
    is_active: bool
    email_verified: bool
    employee_id: str | None
    roles: list[str] = []  # List of role names

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserSummary(BaseSchema):
    """Brief user info."""

    id: str
    email: str
    first_name: str
    last_name: str
    status: UserStatus
    is_active: bool


class CurrentUserResponse(BaseSchema):
    """Current authenticated user response."""

    id: str
    email: str
    first_name: str
    last_name: str
    tenant_id: str
    roles: list[str]
    permissions: list[str]


# --- Role Schemas ---


class RoleCreate(BaseSchema):
    """Create role schema."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    permissions: list[str] = []


class RoleUpdate(BaseSchema):
    """Update role schema."""

    name: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    permissions: list[str] | None = None


class RoleResponse(TenantEntitySchema):
    """Role response schema."""

    name: str
    description: str | None
    permissions: list[str]
    is_system: bool
