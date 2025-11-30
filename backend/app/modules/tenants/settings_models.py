"""Tenant settings models."""

from enum import Enum
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import BaseModel, TimestampMixin


class SettingCategory(str, Enum):
    """Categories of tenant settings."""

    GENERAL = "general"  # Language, timezone, region
    LOCALIZATION = "localization"  # Date/time formats, number formats
    NOTIFICATIONS = "notifications"  # Email, SMS, push preferences
    SECURITY = "security"  # Password policies, 2FA settings
    INTEGRATIONS = "integrations"  # Third-party service configs
    TELEMETRY = "telemetry"  # Analytics, usage tracking
    BRANDING = "branding"  # UI customization
    FEATURES = "features"  # Feature flags
    COMPLIANCE = "compliance"  # GDPR, data retention


class TenantSettings(BaseModel, TimestampMixin):
    """
    Flexible tenant settings storage.

    Uses JSON column for extensibility - allows adding new settings
    without schema migrations.
    """

    __tablename__ = "tenant_settings"

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Category for grouping settings
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # JSON storage for flexible settings
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant = relationship("Tenant", backref="settings_entries")

    __table_args__ = ({"sqlite_autoincrement": True},)

    def __repr__(self) -> str:
        return f"<TenantSettings {self.tenant_id}:{self.category}>"

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self.settings[key] = value

    def update_settings(self, new_settings: dict[str, Any]) -> None:
        """Update multiple settings at once."""
        self.settings.update(new_settings)
