# faq_service.py - FAQ lookup and matching
import json
import os
import re
from functools import lru_cache


class FAQService:
    """Loads the university FAQ knowledge base and retrieves relevant entries."""

    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = knowledge_base_path
        self._data = None
        self._all_faqs = []
        self._load_data()

    def _load_data(self):
        """Load FAQ data from the JSON knowledge base file."""
        faq_file = os.path.join(self.knowledge_base_path, "faqs.json")
        try:
            with open(faq_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            # Flatten all FAQs for easier searching
            self._all_faqs = []
            for category in self._data.get("categories", []):
                for faq in category.get("faqs", []):
                    self._all_faqs.append(
                        {
                            "id": faq["id"],
                            "question": faq["question"],
                            "answer": faq["answer"],
                            "keywords": [kw.lower() for kw in faq.get("keywords", [])],
                            "category": category["name"],
                            "category_icon": category.get("icon", ""),
                        }
                    )
        except FileNotFoundError:
            print(f"[FAQService] Warning: FAQ file not found at {faq_file}")
            self._data = {"categories": []}
            self._all_faqs = []
        except json.JSONDecodeError as e:
            print(f"[FAQService] Warning: Invalid JSON in FAQ file: {e}")
            self._data = {"categories": []}
            self._all_faqs = []

    def get_university_info(self) -> dict:
        """Return basic university info from the knowledge base."""
        return self._data.get("university", {})

    def get_categories(self) -> list[dict]:
        """Return all FAQ categories with their names and icons."""
        return [
            {"id": cat["id"], "name": cat["name"], "icon": cat.get("icon", "")}
            for cat in self._data.get("categories", [])
        ]

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search FAQs by matching query words against keywords and question text.
        Returns the top_k most relevant FAQ entries, scored by match quality.
        """
        if not query or not query.strip():
            return []

        query_lower = query.lower().strip()
        query_words = set(re.findall(r"\b\w+\b", query_lower))

        # Remove very common stop words to improve matching
        stop_words = {
            "i", "me", "my", "the", "a", "an", "is", "are", "was", "were",
            "do", "does", "did", "can", "could", "will", "would", "should",
            "what", "how", "where", "when", "who", "which", "that", "this",
            "it", "to", "for", "of", "in", "on", "at", "and", "or", "but",
            "not", "with", "about", "have", "has", "had", "be", "been",
            "am", "please", "tell", "know", "want", "need", "help",
        }
        meaningful_words = query_words - stop_words
        # If all words were stop words, use original query words
        if not meaningful_words:
            meaningful_words = query_words

        scored_results = []
        for faq in self._all_faqs:
            score = 0.0

            # 1. Keyword matches (highest weight, with stem/plural support)
            keyword_matches = sum(
                1
                for word in meaningful_words
                if any(
                    word in kw or (len(word) >= 4 and len(kw) >= 4 and kw in word)
                    for kw in faq["keywords"]
                )
            )
            score += keyword_matches * 3.0

            # 2. Exact or direct plural/singular keyword match bonus
            for word in meaningful_words:
                if (
                    word in faq["keywords"]
                    or (word.endswith("s") and word[:-1] in faq["keywords"])
                    or (f"{word}s" in faq["keywords"])
                ):
                    score += 2.0

            # 3. Question text matches
            question_lower = faq["question"].lower()
            question_words = set(re.findall(r"\b\w+\b", question_lower))
            question_matches = len(meaningful_words & question_words)
            score += question_matches * 1.5

            # 4. Substring match in question
            if query_lower in question_lower:
                score += 5.0

            # 5. Answer text matches (lower weight)
            answer_lower = faq["answer"].lower()
            answer_words = set(re.findall(r"\b\w+\b", answer_lower))
            answer_matches = len(meaningful_words & answer_words)
            score += answer_matches * 0.5

            if score > 0:
                scored_results.append({**faq, "_score": score})

        # Sort by score descending and return top_k
        scored_results.sort(key=lambda x: x["_score"], reverse=True)
        # Remove internal score from results
        results = []
        for item in scored_results[:top_k]:
            result = {k: v for k, v in item.items() if k != "_score"}
            results.append(result)

        return results

    def get_all_faqs(self) -> list[dict]:
        """Return all FAQ entries."""
        return self._all_faqs

    def get_context_for_ai(self, query: str) -> str:
        """
        Build a context string from relevant FAQs for the AI model.
        This is injected into the AI prompt so responses are grounded
        in university information.
        """
        relevant_faqs = self.search(query, top_k=5)
        if not relevant_faqs:
            return "No specific university FAQ entries matched this query."

        context_parts = ["Relevant university information:"]
        for faq in relevant_faqs:
            context_parts.append(
                f"\n[{faq['category']}] Q: {faq['question']}\n"
                f"A: {faq['answer']}"
            )
        return "\n".join(context_parts)
