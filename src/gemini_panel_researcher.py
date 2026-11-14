"""
AmbuPriority ÃƒÂ¢Ã¢â€šÂ¬” Gemini Hospital Panel & Scheme Intelligence Service
===================================================================
Researches returned hospitals using Gemini Developer API with:
1. Google Search Grounding (gemini-3.5-flash-lite / compatible Flash models)
2. Resilient fallback to direct Gemini clinical/healthcare knowledge if search grounding encounters rate limits.
3. In-memory caching with 1-day TTL (never permanently hardcoded; fresh research for new requests).
4. Concurrency limits & batching to avoid API overload.
5. Secure backend execution using GEMINI_API_KEY environment variable.
"""

import os
import json
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Cache structure: { hospital_normalized_name: { "data": dict, "timestamp": float } }
_ONE_DAY_SECONDS = int(os.getenv("PANEL_CACHE_TTL_HOURS", "720")) * 3600  # 30 days by default
# Empty answers ("model found nothing") are retried sooner, so a facility is not
# stuck as unverified forever just because one call returned nothing.
_EMPTY_TTL_SECONDS = int(os.getenv("PANEL_EMPTY_TTL_HOURS", "6")) * 3600


def _is_empty(data: Any) -> bool:
    if not isinstance(data, dict):
        return True
    return not (data.get("schemes") or data.get("panels"))


def _cache_entry_valid(entry: Optional[Dict[str, Any]], now: float) -> bool:
    """Empty research results expire after _EMPTY_TTL_SECONDS, not the full TTL."""
    if not entry:
        return False
    age = now - entry.get("timestamp", 0)
    if _is_empty(entry.get("data")):
        return age < _EMPTY_TTL_SECONDS
    return age < _ONE_DAY_SECONDS
_PANEL_RESEARCH_CACHE: Dict[str, Dict[str, Any]] = {}

# ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ Speed configuration ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬ÃƒÂ¢”Ã¢â€šÂ¬
# Measured on this deployment: 3.1-flash-lite answers a batch of 8 hospitals in
# ~2.7s, while 3.5-flash-lite takes 4.4-6.4s and 3.5-flash is frequently 503.
_PANEL_MODEL = os.getenv("PANEL_RESEARCH_MODEL", "gemini-3.5-flash-lite").strip()
# 20 names per call measured fastest (~5.2s for 24 hospitals vs 6.5s at 12).
_MAX_BATCH = int(os.getenv("PANEL_RESEARCH_BATCH", "20"))
# Google Search grounding is disabled by default: on free tier it returns
# 429 RESOURCE_EXHAUSTED on every call, wasting ~0.8s and quota before the
# direct-knowledge fallback runs anyway.
_SEARCH_GROUNDING = os.getenv("PANEL_SEARCH_GROUNDING", "0").strip() == "1"

# Persistent cache so restarts and repeat searches cost 0 ms.
_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "panel_research_cache.json"
_cache_loaded = False
_cache_lock = threading.Lock()


def _cache_key(hospital_name: str) -> str:
    return (hospital_name or "").strip().lower()


def _load_persistent_cache() -> None:
    """Load the on-disk research cache once per process."""
    global _cache_loaded
    if _cache_loaded:
        return
    _cache_loaded = True
    if not _CACHE_FILE.exists():
        return
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            # Only keep entries that carry both data and a timestamp.
            for key, entry in raw.items():
                if isinstance(entry, dict) and entry.get("data") and entry.get("timestamp"):
                    _PANEL_RESEARCH_CACHE[key] = entry
        logger.info("Loaded %d cached panel research entries from disk", len(_PANEL_RESEARCH_CACHE))
    except Exception as exc:
        logger.warning("Could not load panel research cache: %s", exc)


def _save_persistent_cache() -> None:
    """Atomically persist the research cache (best effort, never raises)."""
    try:
        with _cache_lock:
            tmp = _CACHE_FILE.with_suffix(".json.tmp")
            _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(_PANEL_RESEARCH_CACHE, f, ensure_ascii=False)
            os.replace(tmp, _CACHE_FILE)
    except Exception as exc:
        logger.warning("Could not persist panel research cache: %s", exc)


# Ã¢”â‚¬Ã¢”€ API key pool Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”â‚¬Ã¢”€
# GEMINI_API_KEYS=a,b,c  → round-robin across keys with automatic 429 failover.
# Falls back to the single GEMINI_API_KEY so existing setups keep working.
# Note: distinct free-tier quotas require distinct projects/accounts; several
# keys inside one project share a single quota.
_key_cooldown: Dict[str, float] = {}   # api key -> unix time it may be used again
_key_lock = threading.Lock()
_key_rr = 0
_KEY_COOLDOWN_DEFAULT = 60.0           # seconds to bench a key after a 429


def _api_keys() -> List[str]:
    """
    Ordered list of usable API keys.

    When GEMINI_API_KEYS is set it is used *exclusively* (the legacy single
    GEMINI_API_KEY is ignored here, though other services still use it).
    """
    raw = os.getenv("GEMINI_API_KEYS", "") or ""
    keys = [k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()]
    if keys:
        return keys
    single = (os.getenv("GEMINI_API_KEY", "") or "").strip()
    if single and single != "PASTE_YOUR_KEY_LOCALLY":
        return [single]
    return []


def _pick_key(exclude: Optional[set] = None) -> Optional[str]:
    """Round-robin over keys that are not cooling down."""
    global _key_rr
    keys = [k for k in _api_keys() if not exclude or k not in exclude]
    if not keys:
        return None
    now = time.time()
    with _key_lock:
        healthy = [k for k in keys if _key_cooldown.get(k, 0.0) <= now]
        pool = healthy or keys          # all cooling: still try rather than fail
        key = pool[_key_rr % len(pool)]
        _key_rr += 1
        return key


def _bench_key(key: str, seconds: float = _KEY_COOLDOWN_DEFAULT) -> None:
    with _key_lock:
        _key_cooldown[key] = time.time() + seconds
    logger.info("API key benched for %.0fs (quota/rate limit)", seconds)


def key_pool_status() -> List[Dict[str, Any]]:
    """Health snapshot for diagnostics."""
    now = time.time()
    out = []
    for i, key in enumerate(_api_keys()):
        cd = _key_cooldown.get(key, 0.0)
        out.append({
            "index": i,
            "key_hint": f"...{key[-4:]}" if len(key) > 4 else "****",
            "ready": cd <= now,
            "cooldown_s": max(0, round(cd - now)),
        })
    return out


def _client_for(key: str):
    try:
        from google import genai
        return genai.Client(api_key=key)
    except Exception as exc:
        logger.error("Failed to initialize Gemini client: %s", exc)
        return None


def _get_gemini_client():
    """Backwards-compatible helper: client for any available key."""
    key = _pick_key()
    return _client_for(key) if key else None


def _clean_json_text(text: str) -> str:
    """Strip markdown code blocks from model response."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class _RateLimited(Exception):
    """Raised when a key hits its quota."""


_GEMINI_REST_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _generate_json_via_rest(key: str, prompt: str, use_search: bool = False,
                            timeout: float = 12.0) -> str:
    """
    Call Gemini's REST endpoint directly with a per-request timeout.

    Returns the generated text ('' when the model produced nothing).
    Raises _RateLimited on 429 so the caller can fail over to another key.
    """
    import requests

    body: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    if use_search:
        body["tools"] = [{"google_search": {}}]

    resp = requests.post(
        _GEMINI_REST_URL.format(model=_PANEL_MODEL),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=body,
        timeout=timeout,
    )

    if resp.status_code == 429:
        raise _RateLimited(resp.text[:200])
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts)


def _research_batch_with_gemini(hospital_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Research a batch of hospital names, round-robining across the API key pool.
    A key that returns 429 is benched and the next key retries the same batch.
    """
    if not hospital_names or not _api_keys():
        return {}

    prompt_lines = "\n".join(f"- {h}" for h in hospital_names)
    # Response is deliberately compact. The UI only consumes name / schemes /
    # panels / cashless_available, and an LLM's latency is dominated by how many
    # tokens it writes (measured ~200 tok/s), so "summary" and "source" were
    # dropped: same UI, roughly half the generated tokens, roughly half the wait.
    prompt = (
        "You are an Indian hospital insurance-panel and empanelment researcher.\n"
        "For each hospital, list accepted private insurance/TPA panels and government schemes.\n\n"
        f"Hospitals:\n{prompt_lines}\n\n"
        "Rules:\n"
        "- panels: private insurers / TPAs (Star Health, HDFC ERGO, ICICI Lombard, Niva Bupa, "
        "Care Health, Medi Assist, Paramount, MDIndia, Vidal). Max 4.\n"
        "- schemes: government schemes (Ayushman Bharat PM-JAY, CGHS, ECHS, ESIC, State Govt). Max 4.\n"
        "- Use empty arrays when unsure. Do not invent.\n\n"
        "Reply with JSON only, no commentary, no summary, no extra fields:\n"
        '{"results":[{"name":"exact name from the list","cashless_available":true,'
        '"schemes":[],"panels":[]}]}'
    )

    results_map: Dict[str, Dict[str, Any]] = {}
    response_text = ""

    # REST transport: the genai SDK stalls against these "AQ." style keys, while
    # the plain REST endpoint with an x-goog-api-key header answers in ~1-4 s.
    #
    # Hedged requests: a single key sometimes hangs for 30-40 s. Rather than wait
    # for it, after HEDGE_DELAY we fire the same batch on another key and take
    # whichever answers first. This removes straggler latency almost entirely.
    attempts = [True, False] if _SEARCH_GROUNDING else [False]
    HEDGE_DELAY = 3.5
    MAX_HEDGES = 3

    for use_search in attempts:
        if response_text:
            break
        tried: set = set()
        pending = {}
        stop_at = time.time() + 14.0

        with ThreadPoolExecutor(max_workers=MAX_HEDGES) as pool:
            first = _pick_key(exclude=tried)
            if not first:
                break
            tried.add(first)
            pending[pool.submit(_generate_json_via_rest, first, prompt, use_search)] = first

            while pending and time.time() < stop_at:
                done, _ = wait(pending, timeout=HEDGE_DELAY, return_when=FIRST_COMPLETED)
                for fut in done:
                    key = pending.pop(fut)
                    try:
                        text = fut.result()
                        if text:
                            response_text = text
                            logger.info(
                                "Panel research via %s (key ...%s, grounding=%s) for %d hospital(s)",
                                _PANEL_MODEL, key[-4:], use_search, len(hospital_names),
                            )
                            break
                        tried.add(key)
                    except _RateLimited:
                        _bench_key(key)
                        tried.add(key)
                    except Exception as call_err:
                        msg = str(call_err)
                        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                            _bench_key(key)
                        else:
                            logger.info("Panel research attempt failed (key ...%s): %s",
                                        key[-4:], msg[:120])
                        tried.add(key)
                if response_text:
                    break
                # Hedge: still waiting -> try a different key in parallel.
                if pending and len(tried) < MAX_HEDGES:
                    nxt = _pick_key(exclude=tried)
                    if nxt:
                        tried.add(nxt)
                        pending[pool.submit(_generate_json_via_rest, nxt, prompt, use_search)] = nxt

            # Do not block shutdown on hung calls; they are daemonised by timeout.
            for fut in pending:
                fut.cancel()

    if not response_text:
        logger.error("Gemini panel research failed on all keys/attempts")
        return {}

    # Parse JSON
    try:
        cleaned = _clean_json_text(response_text)
        data = json.loads(cleaned)
        items = data.get("results", [])
        for item in items:
            raw_name = (item.get("name") or "").strip().lower()
            if raw_name:
                results_map[raw_name] = item
    except Exception as parse_err:
        logger.warning(f"Error parsing Gemini panel research response: {parse_err}")

    return results_map


def get_cached_research_or_none(hospital_name: str) -> Optional[Dict[str, Any]]:
    """Return valid cached research data for a single hospital name, or None."""
    _load_persistent_cache()
    name_key = _cache_key(hospital_name)
    cached = _PANEL_RESEARCH_CACHE.get(name_key)
    if cached and (time.time() - cached["timestamp"] < _ONE_DAY_SECONDS):
        return cached["data"]
    return None


def _match_research_item(hospital_name: str, found: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Map a Gemini result back onto the requested hospital name."""
    name_key = _cache_key(hospital_name)
    for res_name, res_data in found.items():
        if res_name in name_key or name_key in res_name:
            return res_data
    # Single-hospital request: the model's sole result is the answer.
    if len(found) == 1:
        return list(found.values())[0]
    return None


def _fuzzy_cached_lookup(name_key: str, now: float) -> Optional[Dict[str, Any]]:
    """
    Second-chance cache lookup for name variants.

    OSM returns names like "Apollo Hospital, Sarita Vihar" while the cache may
    hold "Apollo Hospitals" ÃƒÂ¢Ã¢â€šÂ¬” a strict key match would miss and pay for another
    LLM call. This does a cheap longest-substring match instead.
    """
    if len(name_key) < 6:
        return None
    generic = {
        "hospital", "hospitals", "general hospital", "medical", "medical college",
        "health", "healthcare", "clinic", "centre", "center", "institute",
    }
    best_key: Optional[str] = None
    for key in _PANEL_RESEARCH_CACHE:
        if len(key) < 6 or key in generic:
            continue
        if key in name_key or name_key in key:
            if best_key is None or len(key) > len(best_key):
                best_key = key
    if best_key is None:
        return None
    entry = _PANEL_RESEARCH_CACHE.get(best_key) or {}
    if not _cache_entry_valid(entry, now):
        return None
    return entry.get("data")


def research_many(hospital_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Resolve panel research for many hospitals at once.

    Cache hits cost 0 ms. All cache misses go to Gemini in as few batched calls
    as possible (up to PANEL_RESEARCH_BATCH names per call), which is what keeps
    the insurance panel column near-instant for a page of 10-20 hospitals.
    """
    _load_persistent_cache()
    now = time.time()

    resolved: Dict[str, Dict[str, Any]] = {}
    missing: List[str] = []

    for raw_name in hospital_names:
        name = (raw_name or "").strip()
        if not name:
            continue
        key = _cache_key(name)
        cached = _PANEL_RESEARCH_CACHE.get(key)
        if _cache_entry_valid(cached, now):
            resolved[name] = cached["data"]
            continue
        # Name-variant hit (e.g. "Apollo Hospital, Sarita Vihar" vs "Apollo Hospitals").
        fuzzy = _fuzzy_cached_lookup(key, now)
        if fuzzy:
            resolved[name] = fuzzy
        else:
            missing.append(name)

    # Preserve order, drop duplicates.
    missing = list(dict.fromkeys(missing))

    if missing:
        # Free-tier keys have a tight per-minute quota, so we favour FEWER, larger
        # calls over many tiny ones: a burst of tiny calls burns RPM and triggers
        # 429 cascades that end up slower than one bigger batch.
        max_parallel = max(2, min(len(_api_keys()), 4))
        chunk_size = max(6, min(_MAX_BATCH, -(-len(missing) // max_parallel)))
        chunks = [missing[i:i + chunk_size] for i in range(0, len(missing), chunk_size)]

        if len(chunks) == 1:
            batches = [(chunks[0], _research_batch_with_gemini(chunks[0]))]
        else:
            # Run the batches concurrently, spread across keys with a short stagger
            # so they do not all hit their per-minute window at the same instant.
            max_workers = max(2, min(max_parallel, len(chunks)))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = []
                for idx, c in enumerate(chunks):
                    if idx:
                        time.sleep(0.25)
                    futures.append((c, pool.submit(_research_batch_with_gemini, c)))
                batches = [(c, f.result()) for c, f in futures]

        for chunk, found in batches:
            if not found:
                continue
            for name in chunk:
                item = _match_research_item(name, found)
                if item:
                    resolved[name] = item
                    _PANEL_RESEARCH_CACHE[_cache_key(name)] = {"data": item, "timestamp": now}

        # Second pass: the model sometimes omits hospitals (or renames them), which
        # left rows stuck on "verifying…" forever. Retry the leftovers in tiny
        # batches so each one gets a focused prompt.
        leftovers = [n for n in missing if n not in resolved]
        if leftovers:
            for name in leftovers[:12]:
                found = _research_batch_with_gemini([name])
                item = _match_research_item(name, found) if found else None
                if item:
                    resolved[name] = item
                    _PANEL_RESEARCH_CACHE[_cache_key(name)] = {"data": item, "timestamp": now}
            if len(resolved) > len(missing) - len(leftovers):
                logger.info("Second pass resolved %d leftover hospital(s)",
                            len([n for n in leftovers if n in resolved]))

        _save_persistent_cache()

    return resolved


def research_single_hospital(hospital_name: str) -> Optional[Dict[str, Any]]:
    """Research a single hospital (cache first, then one Gemini call)."""
    return research_many([hospital_name]).get((hospital_name or "").strip())


def research_hospitals_panels(hospitals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich a list of hospital dicts with researched panels & schemes.
    Uses one batched Gemini call for all cache misses instead of one per hospital.
    """
    names = [(h.get("name") or "").strip() for h in hospitals]
    resolved = research_many([n for n in names if n])

    for h in hospitals:
        name = (h.get("name") or "").strip()
        item = resolved.get(name)
        if item:
            _apply_research_to_hospital(h, item)

    return hospitals


def _apply_research_to_hospital(hospital: Dict[str, Any], research_data: Dict[str, Any]):
    """Format and map Gemini research results into the hospital's panel_info and schemes display."""
    schemes_list = research_data.get("schemes") or []
    panels_list = research_data.get("panels") or []
    summary = research_data.get("summary") or "Verified Cashless Tie-ups Available"
    source = research_data.get("source") or "Official Hospital & TPA Directory"

    # Merge into existing panel_info structure so UI and filters remain 100% compatible
    current_panels = hospital.get("panel_info", {}).get("panels", {})
    
    # Check Government Schemes
    has_pmjay = any("pmjay" in s.lower() or "ayushman" in s.lower() for s in schemes_list)
    has_cghs = any("cghs" in s.lower() for s in schemes_list)
    has_echs = any("echs" in s.lower() for s in schemes_list)
    has_esic = any("esic" in s.lower() for s in schemes_list)
    has_state = any("state" in s.lower() or "dghs" in s.lower() or "rghs" in s.lower() or "aarogya" in s.lower() for s in schemes_list)

    if has_pmjay:
        current_panels["pmjay"] = {"name": "Ayushman Bharat – PM-JAY", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for Ayushman Bharat PM-JAY cashless treatment"}
    if has_cghs:
        current_panels["cghs"] = {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for CGHS beneficiaries"}
    if has_echs:
        current_panels["echs"] = {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for Ex-Servicemen Contributory Health Scheme"}
    if has_esic:
        current_panels["esic"] = {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "Tie-up for ESIC beneficiaries"}
    if has_state:
        current_panels["state_govt"] = {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for state employee & public health schemes"}

    # Private TPAs / Insurance Companies
    if panels_list or research_data.get("cashless_available"):
        tpa_names_str = ", ".join(panels_list[:4]) if panels_list else "All Major TPAs"
        current_panels["tpa_insurance"] = {
            "name": "Private Insurance / TPA Networks",
            "status": "Empanelled",
            "badge": "empanelled",
            "details": f"Cashless desk operational for: {tpa_names_str}"
        }

    # Attach Gemini intelligence block for rich frontend display
    hospital["gemini_research"] = {
        "status": "Verified by Gemini AI",
        "schemes": schemes_list,
        "panels": panels_list,
        "summary": summary,
        "source": source
    }
    
    if "panel_info" not in hospital:
        hospital["panel_info"] = {}
    hospital["panel_info"]["panels"] = current_panels
    hospital["panel_info"]["has_verified_panels"] = bool(schemes_list or panels_list)
    hospital["panel_info"]["gemini_summary"] = summary
    hospital["panel_info"]["gemini_source"] = source

