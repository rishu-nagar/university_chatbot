# tests/test_ai_service.py
"""Unit tests for the Gemini AI service."""
import pytest
from services.ai_service import AIService


class TestAIServiceInit:
    def test_init_without_key(self):
        service = AIService(api_key="")
        assert service.is_available is False

    def test_init_with_none_key(self):
        service = AIService(api_key=None)
        assert service.is_available is False

    def test_init_with_whitespace_key(self):
        service = AIService(api_key="   ")
        assert service.is_available is False

    def test_init_with_placeholder_keys(self):
        placeholders = [
            "your_gemini_api_key_here",
            "your_actual_api_key_here",
            "your_api_key_here",
            "changeme",
        ]
        for key in placeholders:
            service = AIService(api_key=key)
            assert service.is_available is False, f"Expected {key} to be treated as unavailable"


class TestAIServicePromptAndHistory:
    @pytest.fixture
    def service(self):
        return AIService(api_key="")

    def test_build_prompt(self, service):
        context = "Library hours: 8am - 10pm"
        question = "When does the library close?"
        prompt = service._build_prompt(question, context)
        assert context in prompt
        assert question in prompt
        assert "UNIVERSITY KNOWLEDGE BASE CONTEXT" in prompt

    def test_build_history_empty(self, service):
        assert service._build_history([]) == []
        assert service._build_history(None) == []

    def test_build_history_conversion(self, service):
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
        ]
        history = service._build_history(chat_history)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["parts"] == ["Hello"]
        assert history[1]["role"] == "model"
        assert history[1]["parts"] == ["Hi! How can I help?"]


class TestAIServiceOfflineResponse:
    def test_generate_response_when_offline(self):
        service = AIService(api_key="")
        res = service.generate_response("What is tuition?", "context")
        assert res["success"] is False
        assert "not configured" in res["error"].lower()
