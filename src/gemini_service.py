import os
import re
import logging
from typing import List, Dict, Any, Optional, Generator
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = (model_name or GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")).strip()
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key and self.api_key != "PASTE_YOUR_KEY_LOCALLY":
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize google-genai Client: {e}")
                self.client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "PASTE_YOUR_KEY_LOCALLY" and self.client is not None)

    def stream_grounded_response(
        self,
        user_message: str,
        retrieved_passages: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]],
        target_language: str = "Hinglish"
    ) -> Generator[str, None, None]:
        """
        Real-time streaming response just like ChatGPT.
        Starts delivering tokens in under 1 second.
        """
        if not self.is_configured():
            yield "Kripya apna GEMINI_API_KEY verify karein."
            return

        passages_text = ""
        for idx, p in enumerate(retrieved_passages[:3]):
            passages_text += f"\n[Guide Excerpt {idx+1}]: {p['text']}\n"

        history_context = ""
        for h in conversation_history[-3:]:
            role = "User" if h["role"] == "user" else "Assistant"
            history_context += f"{role}: {h['content']}\n"

        if target_language == "Hindi":
            lang_instruction = "CRITICAL: The user wrote in Hindi. Respond COMPLETELY in pure Hindi (हिंदी देवनागरी लिपि). Do NOT use English."
        elif target_language == "English":
            lang_instruction = "CRITICAL: The user wrote in English. Respond COMPLETELY in English."
        else:
            lang_instruction = "CRITICAL: The user wrote in Hinglish. Respond in friendly, natural conversational Hinglish (Roman Hindi). Do NOT use Devanagari or pure English."

        prompt = f"""You are FirstAid AI, an instant, highly accurate emergency first-aid chatbot (like ChatGPT).

{lang_instruction}

STRICT SAFETY AND MEDICAL RELEVANCE RULES:
1. FOCUS EXCLUSIVELY ON THE CURRENT USER QUERY: '{user_message}'.
2. DO NOT confuse the topic. If the user asks about heart attack, chest pain, or bleeding, address THAT EXACT EMERGENCY. Never talk about unrelated things like child fever, seizures, or pediatric illness unless the user explicitly asked about it.
3. Start directly with immediate, prioritized first-aid action steps.
4. Keep instructions clear, direct, and numbered or bulleted.
5. DO NOT mention book titles or PDF filenames.
6. For life-threatening emergencies (heart attack, severe bleeding, difficulty breathing, unconsciousness), state the emergency emergency action (e.g. call 112 / 911 / emergency services and CPR/sit upright) as Step 1.

MEDICAL REFERENCE CONTEXT:
{passages_text}

USER QUERY:
{user_message}

Direct Answer:"""

        try:
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {e}"
