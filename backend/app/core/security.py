"""Security utilities for authentication and authorization."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthorizationError

# Type alias for token types
TokenType = Literal["access", "refresh"]

# Security scheme for JWT Bearer authentication
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password with configurable work factor."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=settings.bcrypt_rounds),
    ).decode("utf-8")


def validate_password_strength(password: str) -> list[str]:
    """Validate password meets security requirements.

    Returns a list of validation error messages, empty if password is valid.
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain an uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain a lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain a digit")
    return errors


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    issuer: str | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Token payload (should include sub, tenant_id)
        expires_delta: Optional custom expiration time
        issuer: Domain that issued the token (for multi-tenant validation)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update(
        {
            "exp": expire,
            "type": "access",
            "iat": datetime.now(timezone.utc),
        }
    )
    if issuer:
        to_encode["iss"] = issuer
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
    issuer: str | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        data: Token payload (should include sub, tenant_id)
        expires_delta: Optional custom expiration time
        issuer: Domain that issued the token (for multi-tenant validation)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
        }
    )
    if issuer:
        to_encode["iss"] = issuer
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def decode_token(token: str, expected_type: TokenType | None = None) -> dict | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode
        expected_type: If provided, validates the token type matches

    Returns:
        The decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={
                "require_exp": True,
                "require_sub": True,
            },
        )
        # Validate token type if specified
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None


# --- User Context and Dependencies ---


@dataclass
class UserContext:
    """Current user context extracted from JWT."""

    id: str
    email: str | None = None
    tenant_id: str | None = None


def _get_validated_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict:
    """Validate credentials and return JWT payload. Raises 401 on failure."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def _check_token_revoked(token: str, payload: dict) -> None:
    """Check if token is revoked (individual or user-level). Raises 401 if revoked."""
    from app.core.token_blacklist import token_blacklist

    # Check individual token revocation
    if await token_blacklist.is_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user-level token revocation (e.g., password change, account compromise)
    user_id = payload.get("sub")
    issued_at = payload.get("iat")
    if user_id and issued_at:
        if await token_blacklist.is_user_tokens_revoked(user_id, int(issued_at)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="All sessions have been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def get_current_user_id(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    """Get current user ID from JWT token. Raises 401 if not authenticated."""
    payload = _get_validated_payload(credentials)
    await _check_token_revoked(credentials.credentials, payload)

    # Set user_id on request.state for per_user rate limiting
    request.state.user_id = payload["sub"]

    return payload["sub"]


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserContext:
    """Get current user context from JWT token. Raises 401 if not authenticated."""
    payload = _get_validated_payload(credentials)
    await _check_token_revoked(credentials.credentials, payload)

    # Set user_id on request.state for per_user rate limiting
    request.state.user_id = payload["sub"]

    return UserContext(
        id=payload["sub"],
        email=payload.get("email"),
        tenant_id=payload.get("tenant_id"),
    )


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str | None:
    """Get current user ID if authenticated, None otherwise."""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload:
        return None

    return payload.get("sub")


# Type aliases for dependency injection
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
OptionalUserId = Annotated[str | None, Depends(get_current_user_optional)]


# --- Role-Based Access Control ---


def require_roles(allowed_roles: list[str]):
    """
    Dependency factory that requires user to have one of the allowed roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: CurrentUser,
            _: Annotated[None, Depends(require_roles(["super_admin", "admin"]))],
        ):
            ...
    """

    async def role_checker(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Depends(security)
        ],
    ) -> None:
        from sqlalchemy import select

        from app.core.database import async_session_maker
        from app.modules.auth.models import Role, User, user_roles

        payload = _get_validated_payload(credentials)
        await _check_token_revoked(credentials.credentials, payload)

        user_id = payload["sub"]

        async with async_session_maker() as session:
            result = await session.execute(
                select(Role.name)
                .join(user_roles, user_roles.c.role_id == Role.id)
                .where(user_roles.c.user_id == user_id)
            )
            user_role_names = [row[0] for row in result.fetchall()]

        if not any(role in allowed_roles for role in user_role_names):
            raise AuthorizationError(
                f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )

    return role_checker


def require_super_admin():
    """Dependency that requires super_admin role (platform admin)."""
    return require_roles(["super_admin"])


def require_tenant_admin():
    """Dependency that requires admin or super_admin role."""
    return require_roles(["super_admin", "admin"])


def require_hr():
    """Dependency that requires HR role (hr_manager, hr_staff, admin, or super_admin)."""
    return require_roles(["super_admin", "admin", "hr_manager", "hr_staff"])


def require_manager():
    """Dependency that requires manager or higher role."""
    return require_roles(["super_admin", "admin", "hr_manager", "manager"])


# Convenience type aliases for common role checks
RequireSuperAdmin = Annotated[None, Depends(require_super_admin())]
RequireTenantAdmin = Annotated[None, Depends(require_tenant_admin())]
RequireHR = Annotated[None, Depends(require_hr())]
RequireManager = Annotated[None, Depends(require_manager())]
