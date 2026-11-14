import re
from typing import Dict, Any, List, Generator
from src.fast_retriever import FastBM25KeywordIndex
from src.gemini_service import GeminiService
from src.fast_translator import quick_translate_query

class ConversationManager:
    def __init__(self, vector_store=None, gemini_service=None):
        self.fast_retriever = FastBM25KeywordIndex()
        self.gemini_service = gemini_service or GeminiService()

    def detect_exact_language(self, text: str) -> str:
        # Devanagari Unicode -> Hindi
        if re.search(r'[\u0900-\u097F]', text):
            return "Hindi"

        # Hinglish words
        hinglish_markers = {
            "hai", "kya", "kaise", "kare", "karein", "karu", "ho", "raha", "rahi", "dard", "khoon", 
            "chot", "jal", "gaya", "gayi", "madad", "chahiye", "kaha", "lag", "gaya", "karna", 
            "nahi", "ruk", "paani", "patti", "seene", "saans", "aur", "pe", "ko", "mera", "meri", 
            "batao", "bataiye", "ilaj", "sar", "sir", "gale", "pair", "haath", "kuch", "hua", 
            "theek", "kaat", "liya", "daura", "behosh", "chhuri", "chaku", "bhai", "jaldi", "nikal"
        }
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        if words.intersection(hinglish_markers):
            return "Hinglish"

        return "English"

    def detect_language(self, text: str) -> str:
        """Alias for detect_exact_language for backwards compatibility."""
        return self.detect_exact_language(text)

    def stream_chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """
        Instant streaming pipeline (<1 sec time to first token).
        """
        # 1. Instant language detection
        target_lang = self.detect_exact_language(user_message)

        # 2. Instant (0ms) query expansion
        search_query = quick_translate_query(user_message)

        # 3. Instant (<0.005s) book retrieval
        passages = self.fast_retriever.search(search_query, top_k=3)

        # 4. Stream response from Gemini immediately
        for chunk in self.gemini_service.stream_grounded_response(
            user_message=user_message,
            retrieved_passages=passages,
            conversation_history=conversation_history,
            target_language=target_lang
        ):
            yield chunk
