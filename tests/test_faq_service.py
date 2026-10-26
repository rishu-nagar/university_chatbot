# tests/test_faq_service.py
"""Unit tests for the FAQ knowledge base service."""
import os
import pytest
from services.faq_service import FAQService

# Use the actual knowledge base for integration-style tests
KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")


@pytest.fixture
def faq_service():
    return FAQService(KB_PATH)


class TestFAQServiceLoad:
    def test_loads_data(self, faq_service):
        all_faqs = faq_service.get_all_faqs()
        assert len(all_faqs) > 0

    def test_university_info(self, faq_service):
        info = faq_service.get_university_info()
        assert "name" in info
        assert "Demo" in info["name"]

    def test_categories(self, faq_service):
        categories = faq_service.get_categories()
        assert len(categories) >= 5
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "icon" in cat


class TestFAQServiceSearch:
    def test_search_admission(self, faq_service):
        results = faq_service.search("admission requirements")
        assert len(results) > 0
        # Should find admission-related FAQ
        found = any("admission" in r["question"].lower() for r in results)
        assert found

    def test_search_wifi(self, faq_service):
        results = faq_service.search("how to connect to wifi")
        assert len(results) > 0
        found = any("wi-fi" in r["question"].lower() or "wifi" in str(r["keywords"]) for r in results)
        assert found

    def test_search_empty_query(self, faq_service):
        results = faq_service.search("")
        assert results == []

    def test_search_returns_limited_results(self, faq_service):
        results = faq_service.search("university", top_k=3)
        assert len(results) <= 3

    def test_search_results_have_required_fields(self, faq_service):
        results = faq_service.search("scholarship")
        for r in results:
            assert "id" in r
            assert "question" in r
            assert "answer" in r
            assert "category" in r


class TestFAQServiceContext:
    def test_context_for_ai_with_match(self, faq_service):
        context = faq_service.get_context_for_ai("housing")
        assert "Relevant university information" in context
        assert len(context) > 50

    def test_context_for_ai_no_match(self, faq_service):
        context = faq_service.get_context_for_ai("xyznonexistent")
        assert "No specific" in context


class TestFAQServiceMissingFile:
    def test_missing_knowledge_base(self):
        service = FAQService("/nonexistent/path")
        assert service.get_all_faqs() == []
        assert service.search("test") == []
