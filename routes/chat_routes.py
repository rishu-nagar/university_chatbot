# chat_routes.py - Chat API endpoints
from flask import Blueprint, request, jsonify, current_app, session
from utils.helpers import sanitize_input, validate_message, get_timestamp

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Accepts JSON: { "message": "student's question" }
    Returns JSON: { "success": bool, "response": str, "sources": list, "timestamp": str }
    """
    # Validate request content type
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Request must be JSON.",
        }), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": "Invalid JSON payload.",
        }), 400

    # Extract and validate message
    raw_message = data.get("message", "")
    message = sanitize_input(raw_message)

    is_valid, error = validate_message(message)
    if not is_valid:
        return jsonify({
            "success": False,
            "error": error,
        }), 400

    # Get services from app context
    faq_service = current_app.config["FAQ_SERVICE"]
    ai_service = current_app.config["AI_SERVICE"]

    # Search the knowledge base for relevant context
    relevant_faqs = faq_service.search(message, top_k=5)
    faq_context = faq_service.get_context_for_ai(message)

    # Get chat history from session
    chat_history = session.get("chat_history", [])

    # Generate AI response
    if ai_service.is_available:
        result = ai_service.generate_response(message, faq_context, chat_history)

        if result["success"]:
            response_text = result["response"]
        else:
            # AI failed — fall back to FAQ-only response
            response_text = _build_fallback_response(message, relevant_faqs, result.get("error", ""))
    else:
        # No AI configured — use FAQ-based fallback
        response_text = _build_fallback_response(message, relevant_faqs)

    # Build source references
    sources = [
        {"category": faq["category"], "question": faq["question"]}
        for faq in relevant_faqs[:3]
    ]

    # Update session chat history
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response_text})

    # Trim history to max length
    max_history = current_app.config.get("MAX_CHAT_HISTORY", 50)
    if len(chat_history) > max_history:
        chat_history = chat_history[-max_history:]
    session["chat_history"] = chat_history

    timestamp = get_timestamp()

    return jsonify({
        "success": True,
        "response": response_text,
        "sources": sources,
        "timestamp": timestamp,
    })


@chat_bp.route("/clear", methods=["POST"])
def clear_history():
    """Clear the chat history for the current session."""
    session.pop("chat_history", None)
    return jsonify({"success": True, "message": "Chat history cleared."})


@chat_bp.route("/categories", methods=["GET"])
def get_categories():
    """Return all FAQ categories for the sidebar."""
    faq_service = current_app.config["FAQ_SERVICE"]
    categories = faq_service.get_categories()
    return jsonify({"success": True, "categories": categories})


@chat_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    ai_service = current_app.config["AI_SERVICE"]
    return jsonify({
        "success": True,
        "status": "healthy",
        "ai_available": ai_service.is_available,
    })


def _build_fallback_response(message: str, relevant_faqs: list[dict], error_hint: str = "") -> str:
    """
    Build a helpful response from FAQ data when the AI service is unavailable.
    """
    parts = []

    if error_hint:
        parts.append(f"*Note: {error_hint}*\n")

    if relevant_faqs:
        parts.append("Here's what I found in the university knowledge base:\n")
        for faq in relevant_faqs[:3]:
            parts.append(f"**{faq['question']}**")
            parts.append(f"{faq['answer']}\n")
        parts.append(
            "---\n*For the most current information, please contact the relevant "
            "university office directly.*"
        )
    else:
        parts.append(
            "I couldn't find a specific answer to your question in the university knowledge base. "
            "Here are some suggestions:\n\n"
            "• Try rephrasing your question with more specific terms.\n"
            "• Browse the FAQ categories in the sidebar for common topics.\n"
            "• Contact the university's student services office for personalized assistance."
        )

    ai_service = current_app.config.get("AI_SERVICE")
    ai_available = getattr(ai_service, "is_available", False)
    if not error_hint and not ai_available:
        parts.append(
            "\n\n*💡 AI-powered responses are available when the GEMINI_API_KEY is configured.*"
        )

    return "\n".join(parts)
