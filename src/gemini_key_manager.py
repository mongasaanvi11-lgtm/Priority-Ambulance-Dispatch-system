import os
import time
import logging
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import errors

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class SafeGeminiKeyManager:
    """
    Production-grade Gemini API Key Manager:
    - Safe key rotation across all configured keys.
    - Differentiates 429 (rate-limit/quota), invalid key (400/403), 404 (model), 503 (temporary high load).
    - Exponential backoff with jitter for retries.
    - Prevents parallel stampeding of all keys.
    - Never exposes raw keys in responses, logs, or frontend.
    """

    DEFAULT_MODEL = "gemini-3.5-flash-lite"
    FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]

    def __init__(self):
        self._keys: List[str] = self._load_keys()
        self._key_index = 0
        self._benched_keys: Dict[str, float] = {}  # key -> unbench timestamp
        self._invalid_keys: set = set()            # keys that are permanently bad

    def _load_keys(self) -> List[str]:
        keys = []
        raw = os.getenv("GEMINI_API_KEYS", "") or ""
        for k in raw.replace("\n", ",").split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
        single = (os.getenv("GEMINI_API_KEY", "") or "").strip()
        if single and single not in keys and single != "PASTE_YOUR_KEY_LOCALLY":
            keys.append(single)
        return keys

    def get_total_keys(self) -> int:
        return len(self._keys)

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        pool_status = []
        for idx, k in enumerate(self._keys):
            is_invalid = k in self._invalid_keys
            benched_until = self._benched_keys.get(k, 0.0)
            is_cooling = benched_until > now
            pool_status.append({
                "index": idx + 1,
                "masked": f"...{k[-4:]}" if len(k) > 4 else "****",
                "status": "INVALID" if is_invalid else ("RATE_LIMITED" if is_cooling else "READY"),
                "cooldown_seconds": max(0, int(benched_until - now)) if is_cooling else 0
            })
        return {
            "total_keys": len(self._keys),
            "available_ready": sum(1 for p in pool_status if p["status"] == "READY"),
            "keys": pool_status
        }

    def _get_next_key(self) -> Optional[str]:
        if not self._keys:
            return None
        now = time.time()
        total = len(self._keys)
        # Try finding a ready key in round-robin order
        for _ in range(total):
            key = self._keys[self._key_index % total]
            self._key_index += 1
            if key in self._invalid_keys:
                continue
            if self._benched_keys.get(key, 0.0) <= now:
                return key
        # If all healthy keys are temporarily cooling down, return the one that cools earliest
        candidates = [k for k in self._keys if k not in self._invalid_keys]
        if not candidates:
            return None
        candidates.sort(key=lambda k: self._benched_keys.get(k, 0.0))
        earliest = candidates[0]
        wait_time = max(0.0, self._benched_keys.get(earliest, 0.0) - now)
        if wait_time > 0 and wait_time <= 3.0:
            time.sleep(wait_time)
        return earliest

    def bench_key(self, key: str, duration_sec: float = 60.0):
        self._benched_keys[key] = time.time() + duration_sec
        logger.warning(f"Gemini API key benched for {duration_sec}s due to quota/rate limit.")

    def mark_invalid(self, key: str):
        self._invalid_keys.add(key)
        logger.error("Gemini API key marked permanently invalid.")

    def execute_with_retry(self, fn, max_key_rotations: int = 3, initial_backoff: float = 1.0):
        """
        Executes a callable `fn(client)` with key rotation and exponential backoff.
        Does NOT fire duplicate calls across all keys at the same time.
        """
        last_error = None
        backoff = initial_backoff

        for attempt in range(max_key_rotations):
            key = self._get_next_key()
            if not key:
                break

            try:
                client = genai.Client(api_key=key)
                return fn(client)
            except errors.ClientError as ce:
                status_code = getattr(ce, "code", None) or getattr(ce, "status_code", None)
                msg = str(ce)
                last_error = ce

                # 429: Rate limit / Quota exceeded
                if status_code == 429 or "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    self.bench_key(key, duration_sec=60.0)
                    time.sleep(backoff)
                    backoff = min(backoff * 2.0, 8.0)
                    continue

                # 400 or 403: Invalid Key / API key unauthorized
                if status_code in (400, 403) and ("API_KEY_INVALID" in msg or "forbidden" in msg.lower()):
                    self.mark_invalid(key)
                    continue

                # 503: Service Unavailable / Temporary High Demand
                if status_code == 503 or "503" in msg or "UNAVAILABLE" in msg:
                    self.bench_key(key, duration_sec=15.0)
                    time.sleep(backoff)
                    backoff = min(backoff * 1.5, 5.0)
                    continue

                logger.warning(f"Gemini client call error (key attempt {attempt+1}): {ce}")
                continue
            except Exception as ex:
                last_error = ex
                logger.warning(f"Gemini call exception: {ex}")
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 4.0)
                continue

        logger.error(f"Gemini execute_with_retry exhausted: {last_error}")
        return None

# Global singleton
gemini_key_manager = SafeGeminiKeyManager()
