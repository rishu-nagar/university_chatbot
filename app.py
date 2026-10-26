# app.py - Flask application entry point
import os
from dotenv import load_dotenv
from flask import Flask, render_template

# Load environment variables from .env file
load_dotenv()

from config import Config
from routes.chat_routes import chat_bp
from services.faq_service import FAQService
from services.ai_service import AIService


def create_app() -> Flask:
    """Application factory for the Flask app."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # Initialize services
    faq_service = FAQService(Config.KNOWLEDGE_BASE_PATH)
    ai_service = AIService(
        api_key=Config.GEMINI_API_KEY,
        model_name=Config.GEMINI_MODEL,
    )

    # Store services in app config for access in routes
    app.config["FAQ_SERVICE"] = faq_service
    app.config["AI_SERVICE"] = ai_service

    # Register blueprints
    app.register_blueprint(chat_bp)

    # Main page route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Log startup status
    _log_startup_status(ai_service, faq_service)

    return app


def _log_startup_status(ai_service: AIService, faq_service: FAQService):
    """Print startup information to the console."""
    try:
        import sys
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("\n" + "=" * 55)
    print("  * Aurora University Chatbot - Starting Up *")
    print("=" * 55)
    university = faq_service.get_university_info()
    print(f"  University : {university.get('name', 'N/A')}")
    print(f"  FAQ entries: {len(faq_service.get_all_faqs())}")
    if ai_service.is_available:
        print(f"  Gemini AI  : [OK] Configured ({ai_service.model_name})")
    else:
        print("  Gemini AI  : [!] Not configured (FAQ-only mode)")
        print("  -> Set GEMINI_API_KEY in .env to enable AI responses")
    print("=" * 55 + "\n")


# Run the application
if __name__ == "__main__":
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )
