"""Custom exceptions for the application."""

from typing import Any


class SamvitException(Exception):
    """Base exception for all application exceptions."""

    code: str = "SAMVIT_ERROR"

    def __init__(self, message: str, details: Any = None, code: str | None = None):
        self.message = message
        self.details = details
        if code:
            self.code = code
        super().__init__(self.message)


class EntityNotFoundError(SamvitException):
    """Raised when an entity is not found."""

    code = "ENTITY_NOT_FOUND"

    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} not found",
            details={"entity": entity, "identifier": identifier},
        )


class EntityAlreadyExistsError(SamvitException):
    """Raised when trying to create an entity that already exists."""

    code = "ENTITY_ALREADY_EXISTS"

    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} already exists",
            details={"entity": entity, "identifier": identifier},
        )


class ValidationError(SamvitException):
    """Raised when validation fails."""

    code = "VALIDATION_ERROR"

    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message=message, details={"errors": errors or []})


class AuthenticationError(SamvitException):
    """Raised when authentication fails."""

    code = "AUTHENTICATION_ERROR"

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message)


class AuthorizationError(SamvitException):
    """Raised when user is not authorized to perform an action."""

    code = "AUTHORIZATION_ERROR"

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message=message)


class TenantError(SamvitException):
    """Raised when there's a tenant-related error."""

    code = "TENANT_ERROR"

    def __init__(self, message: str = "Tenant error"):
        super().__init__(message=message)


class TenantMismatchError(TenantError):
    """Raised when trying to access data from another tenant."""

    code = "TENANT_MISMATCH"

    def __init__(self):
        super().__init__(message="Cannot access data from another tenant")


class BusinessRuleViolationError(SamvitException):
    """Raised when a business rule is violated."""

    code = "BUSINESS_RULE_VIOLATION"

    def __init__(self, rule: str, message: str):
        super().__init__(
            message=message,
            details={"rule": rule},
        )
