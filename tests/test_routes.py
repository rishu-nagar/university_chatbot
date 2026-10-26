# tests/test_routes.py
"""Integration tests for API endpoints."""
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "ai_available" in data

    def test_health_status(self, client):
        resp = client.get("/api/health")
        data = resp.get_json()
        assert data["status"] == "healthy"


class TestCategoriesEndpoint:
    def test_categories_returns_list(self, client):
        resp = client.get("/api/categories")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0


class TestChatEndpoint:
    def test_chat_returns_response(self, client):
        resp = client.post("/api/chat", json={"message": "What are the admission requirements?"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["response"]) > 0

    def test_chat_empty_message(self, client):
        resp = client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_chat_missing_message(self, client):
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 400

    def test_chat_not_json(self, client):
        resp = client.post("/api/chat", data="hello")
        assert resp.status_code == 400

    def test_chat_sources_returned(self, client):
        resp = client.post("/api/chat", json={"message": "Tell me about scholarships"})
        data = resp.get_json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_chat_timestamp_returned(self, client):
        resp = client.post("/api/chat", json={"message": "Hello"})
        data = resp.get_json()
        if data["success"]:
            assert "timestamp" in data


class TestClearEndpoint:
    def test_clear_returns_success(self, client):
        resp = client.post("/api/clear")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True


class TestIndexPage:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Aurora" in resp.data
