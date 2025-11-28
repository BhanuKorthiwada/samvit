"""Core module exports."""

from app.core.config import settings
from app.core.database import Base, get_async_session
from app.core.deps import CurrentUserId, DbSession, OptionalUserId, TenantDep
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    SamvitException,
    TenantError,
    TenantMismatchError,
    ValidationError,
)
from app.core.tenancy import TenantContext

__all__ = [
    # Config
    "settings",
    # Database
    "Base",
    "get_async_session",
    # Dependencies
    "CurrentUserId",
    "DbSession",
    "OptionalUserId",
    "TenantDep",
    # Tenancy
    "TenantContext",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleViolationError",
    "EntityAlreadyExistsError",
    "EntityNotFoundError",
    "SamvitException",
    "TenantError",
    "TenantMismatchError",
    "ValidationError",
]
