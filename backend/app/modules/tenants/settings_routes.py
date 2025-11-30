"""Tenant settings API routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.database import DbSession
from app.core.rate_limit import rate_limit
from app.core.tenancy import TenantDep
from app.modules.tenants.settings_models import SettingCategory
from app.modules.tenants.settings_schemas import (
    SETTINGS_CATEGORIES_INFO,
    AllSettingsResponse,
    BrandingSettings,
    ComplianceSettings,
    FeatureSettings,
    GeneralSettings,
    IntegrationSettings,
    LocalizationSettings,
    NotificationSettings,
    SecuritySettings,
    SettingsCategoryInfo,
    TelemetrySettings,
    TenantSettingsUpdate,
)
from app.modules.tenants.settings_service import TenantSettingsService

router = APIRouter(prefix="/settings", tags=["Tenant Settings"])


def get_settings_service(session: DbSession) -> TenantSettingsService:
    """Get settings service dependency."""
    return TenantSettingsService(session)


@router.get(
    "/categories",
    response_model=list[SettingsCategoryInfo],
    summary="List setting categories",
)
async def list_categories() -> list[SettingsCategoryInfo]:
    """
    Get list of all available settings categories with metadata.

    Useful for building a settings UI with category navigation.
    """
    return SETTINGS_CATEGORIES_INFO


@router.get(
    "",
    response_model=AllSettingsResponse,
    summary="Get all settings",
)
async def get_all_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> AllSettingsResponse:
    """
    Get all settings for the current tenant.

    Returns settings for all categories with defaults filled in
    for any settings not explicitly configured.
    """
    return await service.get_all_settings(tenant.tenant_id)


@router.post(
    "/reset",
    response_model=AllSettingsResponse,
    summary="Reset all settings to defaults",
)
async def reset_all_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(5, 60))] = None,
) -> AllSettingsResponse:
    """
    Reset all settings to their default values.

    This is a destructive operation - all custom settings will be lost.
    """
    return await service.reset_all_settings(tenant.tenant_id)


@router.get(
    "/general",
    response_model=GeneralSettings,
    summary="Get general settings",
)
async def get_general_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> GeneralSettings:
    """Get general settings (language, timezone, region, etc.)."""
    return await service.get_general_settings(tenant.tenant_id)


@router.patch(
    "/general",
    response_model=GeneralSettings,
    summary="Update general settings",
)
async def update_general_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,
) -> GeneralSettings:
    """Update general settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.GENERAL,
        data.settings,
    )
    return GeneralSettings(**settings.settings)


@router.get(
    "/localization",
    response_model=LocalizationSettings,
    summary="Get localization settings",
)
async def get_localization_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> LocalizationSettings:
    """Get localization settings (date/time formats, number formats, etc.)."""
    return await service.get_localization_settings(tenant.tenant_id)


@router.patch(
    "/localization",
    response_model=LocalizationSettings,
    summary="Update localization settings",
)
async def update_localization_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,
) -> LocalizationSettings:
    """Update localization settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.LOCALIZATION,
        data.settings,
    )
    return LocalizationSettings(**settings.settings)


@router.get(
    "/notifications",
    response_model=NotificationSettings,
    summary="Get notification settings",
)
async def get_notification_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> NotificationSettings:
    """Get notification settings (email, SMS, push preferences)."""
    settings = await service.get_settings(
        tenant.tenant_id, SettingCategory.NOTIFICATIONS
    )
    if settings is None:
        return NotificationSettings()
    return NotificationSettings(**settings.settings)


@router.patch(
    "/notifications",
    response_model=NotificationSettings,
    summary="Update notification settings",
)
async def update_notification_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,
) -> NotificationSettings:
    """Update notification settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.NOTIFICATIONS,
        data.settings,
    )
    return NotificationSettings(**settings.settings)


@router.get(
    "/security",
    response_model=SecuritySettings,
    summary="Get security settings",
)
async def get_security_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> SecuritySettings:
    """Get security settings (password policies, 2FA, etc.)."""
    return await service.get_security_settings(tenant.tenant_id)


@router.patch(
    "/security",
    response_model=SecuritySettings,
    summary="Update security settings",
)
async def update_security_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> SecuritySettings:
    """Update security settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.SECURITY,
        data.settings,
    )
    return SecuritySettings(**settings.settings)


@router.get(
    "/telemetry",
    response_model=TelemetrySettings,
    summary="Get telemetry settings",
)
async def get_telemetry_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> TelemetrySettings:
    """Get telemetry settings (analytics, error tracking, etc.)."""
    return await service.get_telemetry_settings(tenant.tenant_id)


@router.patch(
    "/telemetry",
    response_model=TelemetrySettings,
    summary="Update telemetry settings",
)
async def update_telemetry_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,
) -> TelemetrySettings:
    """Update telemetry settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.TELEMETRY,
        data.settings,
    )
    return TelemetrySettings(**settings.settings)


@router.get(
    "/branding",
    response_model=BrandingSettings,
    summary="Get branding settings",
)
async def get_branding_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> BrandingSettings:
    """Get branding settings (logo, colors, themes, etc.)."""
    return await service.get_branding_settings(tenant.tenant_id)


@router.patch(
    "/branding",
    response_model=BrandingSettings,
    summary="Update branding settings",
)
async def update_branding_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(30, 60))] = None,
) -> BrandingSettings:
    """Update branding settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.BRANDING,
        data.settings,
    )
    return BrandingSettings(**settings.settings)


@router.get(
    "/features",
    response_model=FeatureSettings,
    summary="Get feature settings",
)
async def get_feature_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> FeatureSettings:
    """Get feature settings (enable/disable features)."""
    return await service.get_feature_settings(tenant.tenant_id)


@router.patch(
    "/features",
    response_model=FeatureSettings,
    summary="Update feature settings",
)
async def update_feature_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> FeatureSettings:
    """Update feature settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.FEATURES,
        data.settings,
    )
    return FeatureSettings(**settings.settings)


@router.get(
    "/compliance",
    response_model=ComplianceSettings,
    summary="Get compliance settings",
)
async def get_compliance_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> ComplianceSettings:
    """Get compliance settings (GDPR, data retention, etc.)."""
    settings = await service.get_settings(tenant.tenant_id, SettingCategory.COMPLIANCE)
    if settings is None:
        return ComplianceSettings()
    return ComplianceSettings(**settings.settings)


@router.patch(
    "/compliance",
    response_model=ComplianceSettings,
    summary="Update compliance settings",
)
async def update_compliance_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> ComplianceSettings:
    """Update compliance settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.COMPLIANCE,
        data.settings,
    )
    return ComplianceSettings(**settings.settings)


@router.get(
    "/integrations",
    response_model=IntegrationSettings,
    summary="Get integration settings",
)
async def get_integration_settings(
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
) -> IntegrationSettings:
    """Get integration settings (Slack, Teams, SSO, etc.)."""
    settings = await service.get_settings(
        tenant.tenant_id, SettingCategory.INTEGRATIONS
    )
    if settings is None:
        return IntegrationSettings()
    return IntegrationSettings(**settings.settings)


@router.patch(
    "/integrations",
    response_model=IntegrationSettings,
    summary="Update integration settings",
)
async def update_integration_settings(
    data: TenantSettingsUpdate,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(20, 60))] = None,
) -> IntegrationSettings:
    """Update integration settings (partial update supported)."""
    settings = await service.update_settings(
        tenant.tenant_id,
        SettingCategory.INTEGRATIONS,
        data.settings,
    )
    return IntegrationSettings(**settings.settings)


@router.post(
    "/{category}/reset",
    response_model=dict[str, Any],
    summary="Reset category settings to defaults",
)
async def reset_category_settings(
    category: SettingCategory,
    tenant: TenantDep,
    service: TenantSettingsService = Depends(get_settings_service),
    _: Annotated[None, Depends(rate_limit(10, 60))] = None,
) -> dict[str, Any]:
    """Reset settings for a specific category to defaults."""
    settings = await service.reset_settings(tenant.tenant_id, category)
    return settings.settings
