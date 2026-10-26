# config.py - Application configuration
import os


class Config:
    """Base configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # Gemini AI configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Application settings
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
    PORT = int(os.environ.get("FLASK_PORT", 5000))

    # Knowledge base path
    KNOWLEDGE_BASE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "knowledge_base"
    )

    # Chat history settings
    MAX_CHAT_HISTORY = 50  # Max messages to retain per session
