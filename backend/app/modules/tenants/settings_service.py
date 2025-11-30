"""Tenant settings service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.settings_models import SettingCategory, TenantSettings
from app.modules.tenants.settings_schemas import (
    SETTINGS_SCHEMA_MAP,
    AllSettingsResponse,
    BrandingSettings,
    ComplianceSettings,
    FeatureSettings,
    GeneralSettings,
    IntegrationSettings,
    LocalizationSettings,
    NotificationSettings,
    SecuritySettings,
    TelemetrySettings,
)


class TenantSettingsService:
    """Service for managing tenant settings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_settings(
        self,
        tenant_id: str,
        category: SettingCategory,
    ) -> TenantSettings | None:
        """Get settings for a specific category."""
        result = await self.session.execute(
            select(TenantSettings).where(
                TenantSettings.tenant_id == tenant_id,
                TenantSettings.category == category.value,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_settings(self, tenant_id: str) -> AllSettingsResponse:
        """Get all settings for a tenant with defaults filled in."""
        result = await self.session.execute(
            select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        )
        settings_list = result.scalars().all()

        settings_map: dict[str, dict[str, Any]] = {}
        for setting in settings_list:
            settings_map[setting.category] = setting.settings

        return AllSettingsResponse(
            general=GeneralSettings(**(settings_map.get("general", {}))),
            localization=LocalizationSettings(**(settings_map.get("localization", {}))),
            notifications=NotificationSettings(
                **(settings_map.get("notifications", {}))
            ),
            security=SecuritySettings(**(settings_map.get("security", {}))),
            telemetry=TelemetrySettings(**(settings_map.get("telemetry", {}))),
            branding=BrandingSettings(**(settings_map.get("branding", {}))),
            features=FeatureSettings(**(settings_map.get("features", {}))),
            compliance=ComplianceSettings(**(settings_map.get("compliance", {}))),
            integrations=IntegrationSettings(**(settings_map.get("integrations", {}))),
        )

    async def update_settings(
        self,
        tenant_id: str,
        category: SettingCategory,
        updates: dict[str, Any],
    ) -> TenantSettings:
        """
        Update settings for a category.

        Performs a partial update - only updates provided fields.
        Validates against the category schema before saving.
        """
        settings = await self.get_settings(tenant_id, category)

        if settings is None:
            schema_class = SETTINGS_SCHEMA_MAP[category]
            validated = schema_class(**updates)

            settings = TenantSettings(
                tenant_id=tenant_id,
                category=category.value,
                settings=validated.model_dump(),
            )
            self.session.add(settings)
        else:
            merged = {**settings.settings, **updates}
            schema_class = SETTINGS_SCHEMA_MAP[category]
            validated = schema_class(**merged)
            settings.settings = validated.model_dump()

        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def reset_settings(
        self,
        tenant_id: str,
        category: SettingCategory,
    ) -> TenantSettings:
        """Reset settings for a category to defaults."""
        settings = await self.get_settings(tenant_id, category)

        schema_class = SETTINGS_SCHEMA_MAP[category]
        defaults = schema_class()

        if settings is None:
            settings = TenantSettings(
                tenant_id=tenant_id,
                category=category.value,
                settings=defaults.model_dump(),
            )
            self.session.add(settings)
        else:
            settings.settings = defaults.model_dump()

        await self.session.commit()
        await self.session.refresh(settings)
        return settings

    async def reset_all_settings(self, tenant_id: str) -> AllSettingsResponse:
        """Reset all settings to defaults."""
        for category in SettingCategory:
            await self.reset_settings(tenant_id, category)

        return await self.get_all_settings(tenant_id)

    async def get_general_settings(self, tenant_id: str) -> GeneralSettings:
        """Get general settings with defaults."""
        settings = await self.get_settings(tenant_id, SettingCategory.GENERAL)
        if settings is None:
            return GeneralSettings()
        return GeneralSettings(**settings.settings)

    async def get_localization_settings(self, tenant_id: str) -> LocalizationSettings:
        """Get localization settings with defaults."""
        settings = await self.get_settings(tenant_id, SettingCategory.LOCALIZATION)
        if settings is None:
            return LocalizationSettings()
        return LocalizationSettings(**settings.settings)

    async def get_security_settings(self, tenant_id: str) -> SecuritySettings:
        """Get security settings with defaults."""
        settings = await self.get_settings(tenant_id, SettingCategory.SECURITY)
        if settings is None:
            return SecuritySettings()
        return SecuritySettings(**settings.settings)

    async def get_feature_settings(self, tenant_id: str) -> FeatureSettings:
        """Get feature settings with defaults."""
        settings = await self.get_settings(tenant_id, SettingCategory.FEATURES)
        if settings is None:
            return FeatureSettings()
        return FeatureSettings(**settings.settings)

    async def get_branding_settings(self, tenant_id: str) -> BrandingSettings:
        """Get branding settings with defaults."""
        settings = await self.get_settings(tenant_id, SettingCategory.BRANDING)
        if settings is None:
            return BrandingSettings()
        return BrandingSettings(**settings.settings)

    async def get_telemetry_settings(self, tenant_id: str) -> TelemetrySettings:
        """Get telemetry settings with defaults."""
        settings = await self.get_settings(tenant_id, SettingCategory.TELEMETRY)
        if settings is None:
            return TelemetrySettings()
        return TelemetrySettings(**settings.settings)

    async def get_setting_value(
        self,
        tenant_id: str,
        category: SettingCategory,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a single setting value."""
        settings = await self.get_settings(tenant_id, category)
        if settings is None:
            schema_class = SETTINGS_SCHEMA_MAP[category]
            defaults = schema_class()
            return getattr(defaults, key, default)
        return settings.settings.get(key, default)

    async def is_feature_enabled(self, tenant_id: str, feature: str) -> bool:
        """Check if a specific feature is enabled."""
        features = await self.get_feature_settings(tenant_id)
        return getattr(features, feature, False)

    async def get_timezone(self, tenant_id: str) -> str:
        """Get tenant's timezone."""
        general = await self.get_general_settings(tenant_id)
        return general.timezone

    async def get_language(self, tenant_id: str) -> str:
        """Get tenant's language."""
        general = await self.get_general_settings(tenant_id)
        return general.language

    async def get_date_format(self, tenant_id: str) -> str:
        """Get tenant's date format."""
        localization = await self.get_localization_settings(tenant_id)
        return localization.date_format
