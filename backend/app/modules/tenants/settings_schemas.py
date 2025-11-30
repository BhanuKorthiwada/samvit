"""Tenant settings schemas."""

from enum import Enum
from typing import Any

from pydantic import Field

from app.shared.schemas import BaseEntitySchema, BaseSchema


class SettingCategory(str, Enum):
    """Categories of tenant settings."""

    GENERAL = "general"
    LOCALIZATION = "localization"
    NOTIFICATIONS = "notifications"
    SECURITY = "security"
    INTEGRATIONS = "integrations"
    TELEMETRY = "telemetry"
    BRANDING = "branding"
    FEATURES = "features"
    COMPLIANCE = "compliance"


class GeneralSettings(BaseSchema):
    """General tenant settings."""

    language: str = Field(
        default="en",
        description="Primary language code (ISO 639-1)",
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
    )
    timezone: str = Field(
        default="Asia/Kolkata",
        description="IANA timezone identifier",
    )
    region: str = Field(
        default="IN",
        description="Region/Country code (ISO 3166-1 alpha-2)",
        pattern=r"^[A-Z]{2}$",
    )
    fiscal_year_start_month: int = Field(
        default=4,
        ge=1,
        le=12,
        description="Fiscal year start month (1-12)",
    )
    week_start_day: int = Field(
        default=1,
        ge=0,
        le=6,
        description="Week start day (0=Sunday, 1=Monday, ...)",
    )
    default_currency: str = Field(
        default="INR",
        description="Default currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$",
    )


class LocalizationSettings(BaseSchema):
    """Localization/formatting settings."""

    date_format: str = Field(
        default="DD/MM/YYYY",
        description="Date display format",
    )
    time_format: str = Field(
        default="24h",
        description="Time format: 12h or 24h",
        pattern=r"^(12h|24h)$",
    )
    datetime_format: str = Field(
        default="DD/MM/YYYY HH:mm",
        description="DateTime display format",
    )
    number_format: str = Field(
        default="en-IN",
        description="Number formatting locale",
    )
    decimal_separator: str = Field(
        default=".",
        description="Decimal separator character",
    )
    thousands_separator: str = Field(
        default=",",
        description="Thousands separator character",
    )
    currency_position: str = Field(
        default="before",
        description="Currency symbol position: before or after",
        pattern=r"^(before|after)$",
    )
    currency_decimal_places: int = Field(
        default=2,
        ge=0,
        le=4,
        description="Decimal places for currency",
    )


class NotificationSettings(BaseSchema):
    """Notification preferences."""

    email_notifications: bool = Field(
        default=True,
        description="Enable email notifications",
    )
    sms_notifications: bool = Field(
        default=False,
        description="Enable SMS notifications",
    )
    push_notifications: bool = Field(
        default=True,
        description="Enable push notifications",
    )
    in_app_notifications: bool = Field(
        default=True,
        description="Enable in-app notifications",
    )
    notification_digest: str = Field(
        default="instant",
        description="Notification digest frequency: instant, hourly, daily",
        pattern=r"^(instant|hourly|daily)$",
    )
    quiet_hours_enabled: bool = Field(
        default=False,
        description="Enable quiet hours (no notifications)",
    )
    quiet_hours_start: str = Field(
        default="22:00",
        description="Quiet hours start time (HH:mm)",
        pattern=r"^\d{2}:\d{2}$",
    )
    quiet_hours_end: str = Field(
        default="08:00",
        description="Quiet hours end time (HH:mm)",
        pattern=r"^\d{2}:\d{2}$",
    )


class SecuritySettings(BaseSchema):
    """Security and authentication settings."""

    password_min_length: int = Field(
        default=8,
        ge=6,
        le=128,
        description="Minimum password length",
    )
    password_require_uppercase: bool = Field(
        default=True,
        description="Require uppercase letters in password",
    )
    password_require_lowercase: bool = Field(
        default=True,
        description="Require lowercase letters in password",
    )
    password_require_numbers: bool = Field(
        default=True,
        description="Require numbers in password",
    )
    password_require_special: bool = Field(
        default=True,
        description="Require special characters in password",
    )
    password_expiry_days: int = Field(
        default=0,
        ge=0,
        description="Password expiry in days (0 = never)",
    )
    max_login_attempts: int = Field(
        default=5,
        ge=3,
        le=20,
        description="Max failed login attempts before lockout",
    )
    lockout_duration_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Account lockout duration in minutes",
    )
    session_timeout_minutes: int = Field(
        default=480,
        ge=15,
        le=10080,
        description="Session timeout in minutes",
    )
    require_2fa: bool = Field(
        default=False,
        description="Require two-factor authentication",
    )
    allowed_2fa_methods: list[str] = Field(
        default=["totp", "email"],
        description="Allowed 2FA methods: totp, email, sms",
    )
    ip_whitelist_enabled: bool = Field(
        default=False,
        description="Enable IP whitelist",
    )
    ip_whitelist: list[str] = Field(
        default=[],
        description="List of allowed IP addresses/ranges",
    )


class TelemetrySettings(BaseSchema):
    """Telemetry and analytics settings."""

    analytics_enabled: bool = Field(
        default=True,
        description="Enable usage analytics",
    )
    error_tracking_enabled: bool = Field(
        default=True,
        description="Enable error/exception tracking",
    )
    performance_monitoring: bool = Field(
        default=True,
        description="Enable performance monitoring",
    )
    usage_statistics: bool = Field(
        default=True,
        description="Collect usage statistics",
    )
    share_anonymous_data: bool = Field(
        default=False,
        description="Share anonymous usage data for improvements",
    )
    audit_logging: bool = Field(
        default=True,
        description="Enable detailed audit logging",
    )
    audit_retention_days: int = Field(
        default=90,
        ge=30,
        le=365,
        description="Audit log retention in days",
    )


class BrandingSettings(BaseSchema):
    """UI branding and customization settings."""

    logo_url: str | None = Field(
        default=None,
        description="Logo image URL",
        max_length=500,
    )
    favicon_url: str | None = Field(
        default=None,
        description="Favicon URL",
        max_length=500,
    )
    primary_color: str = Field(
        default="#3B82F6",
        description="Primary brand color (hex)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    secondary_color: str = Field(
        default="#64748B",
        description="Secondary brand color (hex)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    accent_color: str = Field(
        default="#10B981",
        description="Accent color (hex)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    theme_mode: str = Field(
        default="system",
        description="Default theme: light, dark, or system",
        pattern=r"^(light|dark|system)$",
    )
    custom_css: str | None = Field(
        default=None,
        description="Custom CSS for tenant",
        max_length=50000,
    )
    login_background_url: str | None = Field(
        default=None,
        description="Custom login page background URL",
        max_length=500,
    )
    company_tagline: str | None = Field(
        default=None,
        description="Company tagline for login page",
        max_length=200,
    )


class FeatureSettings(BaseSchema):
    """Feature flags and toggles."""

    enable_ai_assistant: bool = Field(
        default=True,
        description="Enable AI assistant features",
    )
    enable_time_tracking: bool = Field(
        default=True,
        description="Enable time tracking module",
    )
    enable_leave_management: bool = Field(
        default=True,
        description="Enable leave management module",
    )
    enable_payroll: bool = Field(
        default=True,
        description="Enable payroll module",
    )
    enable_attendance: bool = Field(
        default=True,
        description="Enable attendance tracking",
    )
    enable_employee_self_service: bool = Field(
        default=True,
        description="Enable employee self-service portal",
    )
    enable_mobile_app: bool = Field(
        default=True,
        description="Enable mobile app access",
    )
    enable_api_access: bool = Field(
        default=False,
        description="Enable API access for integrations",
    )
    enable_bulk_import: bool = Field(
        default=True,
        description="Enable bulk data import",
    )
    enable_reports: bool = Field(
        default=True,
        description="Enable reporting features",
    )
    enable_document_management: bool = Field(
        default=True,
        description="Enable document management",
    )
    beta_features: bool = Field(
        default=False,
        description="Enable beta features",
    )


class ComplianceSettings(BaseSchema):
    """Compliance and data governance settings."""

    gdpr_enabled: bool = Field(
        default=False,
        description="Enable GDPR compliance features",
    )
    data_retention_days: int = Field(
        default=365,
        ge=30,
        le=3650,
        description="Data retention period in days",
    )
    auto_delete_inactive_employees: bool = Field(
        default=False,
        description="Auto-delete data for inactive employees",
    )
    inactive_employee_retention_days: int = Field(
        default=365,
        ge=30,
        description="Days to retain inactive employee data",
    )
    require_consent_for_analytics: bool = Field(
        default=True,
        description="Require user consent for analytics",
    )
    data_export_enabled: bool = Field(
        default=True,
        description="Allow data export (GDPR right to portability)",
    )
    data_deletion_enabled: bool = Field(
        default=True,
        description="Allow data deletion requests",
    )
    cookie_consent_required: bool = Field(
        default=True,
        description="Require cookie consent banner",
    )
    privacy_policy_url: str | None = Field(
        default=None,
        description="Custom privacy policy URL",
        max_length=500,
    )
    terms_of_service_url: str | None = Field(
        default=None,
        description="Custom terms of service URL",
        max_length=500,
    )


class IntegrationSettings(BaseSchema):
    """Third-party integration settings."""

    slack_enabled: bool = Field(
        default=False,
        description="Enable Slack integration",
    )
    slack_webhook_url: str | None = Field(
        default=None,
        description="Slack webhook URL",
        max_length=500,
    )
    teams_enabled: bool = Field(
        default=False,
        description="Enable Microsoft Teams integration",
    )
    teams_webhook_url: str | None = Field(
        default=None,
        description="Teams webhook URL",
        max_length=500,
    )
    google_calendar_enabled: bool = Field(
        default=False,
        description="Enable Google Calendar sync",
    )
    outlook_calendar_enabled: bool = Field(
        default=False,
        description="Enable Outlook Calendar sync",
    )
    sso_enabled: bool = Field(
        default=False,
        description="Enable Single Sign-On",
    )
    sso_provider: str | None = Field(
        default=None,
        description="SSO provider: google, microsoft, okta, custom",
    )
    custom_smtp_enabled: bool = Field(
        default=False,
        description="Use custom SMTP server",
    )
    smtp_host: str | None = Field(
        default=None,
        description="SMTP server host",
        max_length=255,
    )
    smtp_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description="SMTP server port",
    )
    smtp_from_email: str | None = Field(
        default=None,
        description="SMTP from email address",
        max_length=255,
    )


class TenantSettingsUpdate(BaseSchema):
    """Schema for updating settings for a category."""

    settings: dict[str, Any] = Field(
        ...,
        description="Settings to update (partial update supported)",
    )


class TenantSettingsResponse(BaseEntitySchema):
    """Response schema for tenant settings."""

    tenant_id: str
    category: SettingCategory
    settings: dict[str, Any]
    description: str | None = None


class AllSettingsResponse(BaseSchema):
    """All settings for a tenant."""

    general: GeneralSettings = Field(default_factory=GeneralSettings)
    localization: LocalizationSettings = Field(default_factory=LocalizationSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    telemetry: TelemetrySettings = Field(default_factory=TelemetrySettings)
    branding: BrandingSettings = Field(default_factory=BrandingSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    compliance: ComplianceSettings = Field(default_factory=ComplianceSettings)
    integrations: IntegrationSettings = Field(default_factory=IntegrationSettings)


class SettingsCategoryInfo(BaseSchema):
    """Info about a settings category."""

    category: SettingCategory
    name: str
    description: str
    icon: str


SETTINGS_SCHEMA_MAP: dict[SettingCategory, type[BaseSchema]] = {
    SettingCategory.GENERAL: GeneralSettings,
    SettingCategory.LOCALIZATION: LocalizationSettings,
    SettingCategory.NOTIFICATIONS: NotificationSettings,
    SettingCategory.SECURITY: SecuritySettings,
    SettingCategory.TELEMETRY: TelemetrySettings,
    SettingCategory.BRANDING: BrandingSettings,
    SettingCategory.FEATURES: FeatureSettings,
    SettingCategory.COMPLIANCE: ComplianceSettings,
    SettingCategory.INTEGRATIONS: IntegrationSettings,
}


SETTINGS_CATEGORIES_INFO: list[SettingsCategoryInfo] = [
    SettingsCategoryInfo(
        category=SettingCategory.GENERAL,
        name="General",
        description="Language, timezone, region, and basic preferences",
        icon="settings",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.LOCALIZATION,
        name="Localization",
        description="Date, time, number, and currency formatting",
        icon="language",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.NOTIFICATIONS,
        name="Notifications",
        description="Email, SMS, and push notification preferences",
        icon="notifications",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.SECURITY,
        name="Security",
        description="Password policies, 2FA, and access controls",
        icon="security",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.TELEMETRY,
        name="Telemetry",
        description="Analytics, error tracking, and audit logging",
        icon="analytics",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.BRANDING,
        name="Branding",
        description="Logo, colors, themes, and UI customization",
        icon="palette",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.FEATURES,
        name="Features",
        description="Enable or disable application features",
        icon="toggle_on",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.COMPLIANCE,
        name="Compliance",
        description="GDPR, data retention, and privacy settings",
        icon="policy",
    ),
    SettingsCategoryInfo(
        category=SettingCategory.INTEGRATIONS,
        name="Integrations",
        description="Third-party services and SSO configuration",
        icon="extension",
    ),
]
