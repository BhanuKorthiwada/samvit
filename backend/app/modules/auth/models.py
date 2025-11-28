"""Auth models - User and Role."""

from enum import Enum

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import BaseModel, TenantBaseModel


class UserRole(str, Enum):
    """User roles."""

    SUPER_ADMIN = "super_admin"  # Platform admin (cross-tenant)
    ADMIN = "admin"  # Tenant admin
    HR_MANAGER = "hr_manager"
    HR_STAFF = "hr_staff"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    LOCKED = "locked"


# Association table for user-role many-to-many
user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id"), primary_key=True),
)


class Role(TenantBaseModel):
    """Role model for RBAC."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permissions: Mapped[str] = mapped_column(String(2000), default="[]")  # JSON array
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(TenantBaseModel):
    """User model for authentication."""

    __tablename__ = "users"

    # Auth credentials - email unique per tenant, not globally
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        {"extend_existing": True},
    )

    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=UserStatus.PENDING.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Link to employee (optional - not all users are employees)
    employee_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("employees.id"),
        nullable=True,
    )

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User {self.email}>"
