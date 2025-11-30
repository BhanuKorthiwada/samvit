"""Input sanitization utilities to prevent XSS attacks."""

import bleach


def sanitize_html(text: str | None) -> str | None:
    """Sanitize HTML content, removing dangerous tags and attributes."""
    if not text:
        return text

    # Allow only safe tags and attributes
    allowed_tags = ["p", "br", "strong", "em", "u", "a", "ul", "ol", "li"]
    allowed_attributes = {"a": ["href", "title"]}

    return bleach.clean(
        text, tags=allowed_tags, attributes=allowed_attributes, strip=True
    )


def sanitize_text(text: str | None) -> str | None:
    """Sanitize plain text, removing all HTML tags."""
    if not text:
        return text

    return bleach.clean(text, tags=[], strip=True)


def sanitize_dict(data: dict, fields: list[str]) -> dict:
    """Sanitize specific fields in a dictionary."""
    sanitized = data.copy()
    for field in fields:
        if field in sanitized and isinstance(sanitized[field], str):
            sanitized[field] = sanitize_text(sanitized[field])
    return sanitized
