# helpers.py - Common helper functions
import re
from datetime import datetime, timezone


def sanitize_input(text: str) -> str:
    """Sanitize user input by stripping excess whitespace and limiting length."""
    if not isinstance(text, str):
        return ""
    # Strip leading/trailing whitespace
    text = text.strip()
    # Collapse multiple whitespace characters into single spaces
    text = re.sub(r"\s+", " ", text)
    # Limit to 2000 characters
    text = text[:2000]
    return text


def get_timestamp() -> str:
    """Return a formatted UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def validate_message(message: str) -> tuple[bool, str]:
    """
    Validate a chat message.
    Returns (is_valid, error_message).
    """
    if not message:
        return False, "Message cannot be empty."
    if len(message) > 2000:
        return False, "Message is too long. Please keep it under 2000 characters."
    if len(message.strip()) == 0:
        return False, "Message cannot be blank."
    return True, ""


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rsplit(" ", 1)[0] + "..."
