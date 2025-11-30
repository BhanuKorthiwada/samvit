"""Auth API routes."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.audit import AuditAction, log_audit
from app.core.database import DbSession
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import rate_limit
from app.core.security import CurrentUser, CurrentUserId, decode_token
from app.core.tenancy import TenantDep, extract_domain_from_host
from app.core.token_blacklist import token_blacklist
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    CompanyRegisterRequest,
    CompanyRegisterResponse,
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserSummary,
    UserUpdate,
)
from app.modules.auth.service import AuthService
from app.shared.schemas import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(
    tenant: TenantDep,
    session: DbSession,
) -> AuthService:
    """Get auth service dependency with tenant context."""
    return AuthService(session, tenant.tenant_id)


def get_auth_service_no_tenant(
    session: DbSession,
) -> AuthService:
    """Get auth service dependency without tenant context (for company signup)."""
    return AuthService(session)


@router.post(
    "/register/company",
    response_model=CompanyRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new company",
)
async def register_company(
    data: CompanyRegisterRequest,
    _: Annotated[
        None, Depends(rate_limit(3, 3600))
    ] = None,  # 3 per hour - very strict for signups
    service: AuthService = Depends(get_auth_service_no_tenant),
) -> CompanyRegisterResponse:
    """
    Register a new company (tenant) with admin user.

    This is the main signup endpoint for new organizations.
    Creates a new tenant and the first admin user.
    """
    return await service.register_company(data)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user (invitation)",
)
async def register(
    data: RegisterRequest,
    _: Annotated[None, Depends(rate_limit(10, 3600))] = None,  # 10 per hour per IP
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Register a new user in an existing tenant.

    This endpoint is for invited users joining an existing organization.
    Tenant is identified via the Host header (subdomain or custom domain).
    """
    user, tokens = await service.register_with_tokens(data)
    # Build response manually to avoid lazy loading issues
    user_response = UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        status=user.status,
        is_active=user.is_active,
        email_verified=user.email_verified,
        employee_id=user.employee_id,
        roles=[],
    )
    return RegisterResponse(
        user=user_response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
)
async def login(
    request: Request,
    data: LoginRequest,
    session: DbSession,
    _: Annotated[
        None, Depends(rate_limit(5, 60))
    ] = None,  # 5 per minute - prevents brute force
) -> TokenResponse:
    """
    Authenticate and get access tokens.

    Tenant is resolved from the Host header (subdomain or custom domain).
    """
    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    service = AuthService(session)
    result = await service.login_with_tenant_lookup(data, domain)

    # Log successful login
    payload = decode_token(result.access_token)
    if payload:
        await log_audit(
            session,
            tenant_id=payload.get("tenant_id", ""),
            user_id=payload.get("sub", ""),
            action=AuditAction.LOGIN,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    return result


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
)
async def refresh_tokens(
    request: Request,
    data: RefreshTokenRequest,
    session: DbSession,
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> TokenResponse:
    """Refresh access token using refresh token.

    The refresh token is checked against the blacklist to prevent
    revoked tokens from minting new access tokens.
    """
    # Check if refresh token is revoked
    if await token_blacklist.is_revoked(data.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Check user-level revocation
    payload = decode_token(data.refresh_token)
    if payload:
        user_id = payload.get("sub")
        issued_at = payload.get("iat")
        if user_id and issued_at:
            if await token_blacklist.is_user_tokens_revoked(user_id, int(issued_at)):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="All sessions have been revoked. Please log in again.",
                )

    # Extract domain for issuer
    host = request.headers.get("host", "")
    domain = extract_domain_from_host(host)

    service = AuthService(session)
    return await service.refresh_tokens(data.refresh_token, domain)


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout",
)
async def logout(
    request: Request,
    current_user: CurrentUser,
    session: DbSession,
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> SuccessResponse:
    """
    Logout and revoke current access token.

    The token will be blacklisted until its natural expiry.
    """
    # Get token from Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Decode to get expiry
        payload = decode_token(token)
        if payload and payload.get("exp"):
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            await token_blacklist.revoke_token(token, expires_at)

        # Log logout
        if current_user.tenant_id:
            await log_audit(
                session,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                action=AuditAction.LOGOUT,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

    return SuccessResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user",
)
async def get_current_user(
    user_id: CurrentUserId,
    session: DbSession,
    _: Annotated[None, Depends(rate_limit(100, 60))] = None,  # 100 per minute
) -> CurrentUserResponse:
    """Get current authenticated user info."""
    # Don't require tenant context - trust the JWT
    service = AuthService(session)
    user_data = await service.get_current_user(user_id)
    return CurrentUserResponse(**user_data)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update profile",
)
async def update_profile(
    data: UserUpdate,
    user_id: CurrentUserId,
    session: DbSession,
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
) -> UserResponse:
    """Update current user's profile."""
    service = AuthService(session)
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change password",
)
async def change_password(
    data: ChangePasswordRequest,
    user_id: CurrentUserId,
    session: DbSession,
    _: Annotated[
        None, Depends(rate_limit(3, 60, per_user=True))
    ] = None,  # 3 per minute per user
) -> SuccessResponse:
    """Change current user's password.

    After password change, all existing sessions are invalidated.
    User must log in again with the new password.
    """
    service = AuthService(session)
    try:
        await service.change_password(
            user_id,
            data.current_password,
            data.new_password,
        )
        # Revoke all user tokens after password change for security
        await token_blacklist.revoke_all_user_tokens(user_id)
        return SuccessResponse(
            message="Password changed successfully. Please log in again."
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# --- Admin endpoints for user management ---


admin_router = APIRouter(prefix="/users", tags=["Users (Admin)"])


@admin_router.get(
    "",
    response_model=PaginatedResponse[UserSummary],
    summary="List users",
)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    service: AuthService = Depends(get_auth_service),
) -> PaginatedResponse[UserSummary]:
    """List all users in tenant (admin only)."""
    offset = (page - 1) * page_size
    users, total = await service.list_users(offset=offset, limit=page_size)
    items = [UserSummary.model_validate(u) for u in users]
    return PaginatedResponse.create(items, total, page, page_size)


@admin_router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(
    data: UserCreate,
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,  # 10 per minute
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Create a new user (admin only)."""
    user = await service.create_user(data)
    return UserResponse.model_validate(user)


@admin_router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
)
async def get_user(
    user_id: str,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Get a specific user (admin only)."""
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)
