# tests/test_helpers.py
"""Unit tests for utility helper functions."""
import pytest
from utils.helpers import sanitize_input, validate_message, get_timestamp, truncate_text


class TestSanitizeInput:
    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_collapses_whitespace(self):
        assert sanitize_input("hello   world") == "hello world"

    def test_limits_length(self):
        long_text = "a" * 3000
        result = sanitize_input(long_text)
        assert len(result) == 2000

    def test_handles_empty_string(self):
        assert sanitize_input("") == ""

    def test_handles_non_string(self):
        assert sanitize_input(None) == ""
        assert sanitize_input(123) == ""

    def test_preserves_normal_text(self):
        assert sanitize_input("Hello, how are you?") == "Hello, how are you?"


class TestValidateMessage:
    def test_valid_message(self):
        is_valid, error = validate_message("Hello")
        assert is_valid is True
        assert error == ""

    def test_empty_message(self):
        is_valid, error = validate_message("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_blank_message(self):
        is_valid, error = validate_message("   ")
        assert is_valid is False
        assert "blank" in error.lower()

    def test_too_long_message(self):
        is_valid, error = validate_message("x" * 2001)
        assert is_valid is False
        assert "2000" in error


class TestGetTimestamp:
    def test_returns_string(self):
        ts = get_timestamp()
        assert isinstance(ts, str)
        assert "UTC" in ts

    def test_format(self):
        ts = get_timestamp()
        # Should match: YYYY-MM-DD HH:MM:SS UTC
        parts = ts.split(" ")
        assert len(parts) == 3
        assert len(parts[0].split("-")) == 3


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("hello", 200) == "hello"

    def test_long_text_truncated(self):
        result = truncate_text("a " * 200, 50)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_exact_length(self):
        text = "a" * 200
        assert truncate_text(text, 200) == text
