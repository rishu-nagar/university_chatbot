# ai_service.py - Gemini API integration
import google.generativeai as genai


class AIService:
    """Handles communication with the Google Gemini API."""

    # System instruction that grounds the AI in its role
    SYSTEM_INSTRUCTION = (
        "You are Aurora, a friendly and knowledgeable AI assistant for university students. "
        "You help students with questions about university life, academics, admissions, "
        "campus services, and general university information.\n\n"
        "IMPORTANT GUIDELINES:\n"
        "1. Use the provided university FAQ context to answer questions accurately.\n"
        "2. If the context contains relevant information, base your answer on it.\n"
        "3. If asked about specific policies, fees, or deadlines that are NOT in the "
        "provided context, clearly state that the student should verify with the "
        "relevant university office for current and accurate details.\n"
        "4. NEVER invent specific fees, dates, deadlines, or policy details.\n"
        "5. Be warm, supportive, and encouraging.\n"
        "6. Keep responses concise but helpful — aim for 2-4 paragraphs max.\n"
        "7. Use simple language and avoid jargon.\n"
        "8. If a question is completely unrelated to university life, politely redirect "
        "the conversation and let them know you specialize in university-related topics.\n"
        "9. Format your responses with markdown when appropriate (bullet points, bold text).\n"
        "10. This is DEMONSTRATION data from a fictional 'Aurora University'. "
        "Always note this if someone asks for real-world specifics."
    )

    # Placeholder strings to ignore
    PLACEHOLDER_KEYS = {
        "your_gemini_api_key_here",
        "your_actual_api_key_here",
        "your_api_key_here",
        "changeme",
    }

    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash-lite"):
        self.api_key = (api_key or "").strip()
        self.model_name = model_name
        self._model = None
        self._configured = False

        if self.api_key and not self._is_placeholder(self.api_key):
            self._configure()

    def _is_placeholder(self, key: str) -> bool:
        """Check if the provided API key is an unconfigured template placeholder."""
        k = key.lower().strip()
        if k in self.PLACEHOLDER_KEYS:
            return True
        if k.startswith("your_") and "api_key" in k:
            return True
        return False

    def _configure(self):
        """Configure the Gemini SDK with the API key."""
        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.SYSTEM_INSTRUCTION,
            )
            self._configured = True
        except Exception as e:
            print(f"[AIService] Failed to configure Gemini: {e}")
            self._configured = False

    @property
    def is_available(self) -> bool:
        """Check if the AI service is properly configured and ready."""
        return self._configured and self._model is not None

    def generate_response(
        self, user_message: str, faq_context: str, chat_history: list[dict] | None = None
    ) -> dict:
        """
        Generate an AI response using Gemini, grounded in FAQ context.

        Args:
            user_message: The student's question.
            faq_context: Relevant FAQ information from the knowledge base.
            chat_history: Previous conversation messages for context.

        Returns:
            dict with 'success', 'response', and optionally 'error'.
        """
        if not self.is_available:
            return {
                "success": False,
                "response": None,
                "error": "AI service is not configured. Please set the GEMINI_API_KEY environment variable.",
            }

        # Build the prompt with FAQ context
        prompt = self._build_prompt(user_message, faq_context)

        # Build conversation history for the model
        history = self._build_history(chat_history)

        try:
            chat = self._model.start_chat(history=history)
            response = chat.send_message(prompt)
            return {
                "success": True,
                "response": response.text,
                "error": None,
            }
        except Exception as e:
            error_msg = str(e)
            print(f"[AIService] Gemini API error: {error_msg}")

            # Provide a user-friendly error message
            if "API_KEY" in error_msg.upper() or "AUTHENTICATION" in error_msg.upper():
                friendly_error = (
                    "There's an issue with the AI service authentication. "
                    "Please check that a valid GEMINI_API_KEY is configured."
                )
            elif "QUOTA" in error_msg.upper() or "RATE" in error_msg.upper():
                friendly_error = (
                    "The AI service is temporarily rate-limited. "
                    "Please wait a moment and try again."
                )
            elif "SAFETY" in error_msg.upper():
                friendly_error = (
                    "The AI could not generate a response for this query. "
                    "Please try rephrasing your question."
                )
            else:
                friendly_error = (
                    "An error occurred while generating a response. "
                    "Please try again in a moment."
                )

            return {
                "success": False,
                "response": None,
                "error": friendly_error,
            }

    def _build_prompt(self, user_message: str, faq_context: str) -> str:
        """Build the full prompt with FAQ context prepended."""
        return (
            f"--- UNIVERSITY KNOWLEDGE BASE CONTEXT ---\n"
            f"{faq_context}\n"
            f"--- END CONTEXT ---\n\n"
            f"Student's question: {user_message}"
        )

    def _build_history(self, chat_history: list[dict] | None) -> list[dict]:
        """
        Convert chat history into the format expected by Gemini.
        Each entry needs 'role' ('user' or 'model') and 'parts'.
        """
        if not chat_history:
            return []

        history = []
        for msg in chat_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
        return history
