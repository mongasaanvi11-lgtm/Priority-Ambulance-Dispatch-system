"""
AmbuPriority â€” PIN code verification against India Post
=======================================================
OpenStreetMap's address tags are community-maintained and occasionally wrong
(e.g. the OSM node "Sadar Bazar, Delhi Cantonment" is tagged 110046, but that
PIN belongs to Nangal Raya/Sagarpur; the real PIN is 110010).

India Post's public API (`api.postalpincode.in`) is the authority. This module
takes the address components that OSM gives us and asks India Post which post
offices / PIN codes actually belong to that locality, then recommends a
correction when it is confident.

Strategies, cheapest first:
    1. Post-office name search for the city / locality / road
    2. Filter to the same state (and district when available)
    3. Score candidates by token overlap with the OSM address
"""

import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_API = "https://api.postalpincode.in/postoffice/{q}"
_HEADERS = {
    "User-Agent": "AmbuPriorityEmergencyDispatch/2.0 (contact: admin@ambupriority.gov.in)"
}
_CACHE: Dict[str, Tuple[float, List[Dict[str, str]]]] = {}
_CACHE_TTL = 86400           # 1 day
_lock = threading.Lock()

# Words that carry no discriminating value when matching place names.
_STOPWORDS = {
    "road", "street", "marg", "nagar", "colony", "area", "sector", "block",
    "the", "and", "near", "opp", "opposite", "india", "delhi", "new",
    "hospital", "house", "floor", "plot", "shop", "building", "lane", "gali",
}

# OSM vs India Post spelling differences.
_REWRITES = [
    (r"\bcantonment\b", "cantt"),
    (r"\bcantt\.?\b", "cantt"),
    (r"\bsadar\b", "sadar"),
]


def _tokens(text: str) -> set:
    text = re.sub(r"\bcantonment\b", "cantt", (text or "").lower())
    return {
        t for t in re.split(r"[^a-z0-9]+", text)
        if len(t) > 2 and t not in _STOPWORDS
    }


def _normalise(query: str) -> List[str]:
    """Return the query plus spelling variants worth trying."""
    base = (query or "").strip()
    if not base:
        return []
    variants = [base]
    alt = base.lower()
    for pattern, repl in _REWRITES:
        alt = re.sub(pattern, repl, alt)
    alt = re.sub(r"\s+", " ", alt).strip()
    if alt and alt.lower() != base.lower():
        variants.append(alt)
    return variants[:2]


def _unique_pin(rows: List[Dict[str, str]], state: str) -> Optional[str]:
    """
    If a place name resolves to exactly one PIN (within the known state), that is
    authoritative â€” e.g. "Delhi Cantt" -> 110010, "Karol Bagh" -> 110005.
    Ambiguous names (e.g. "Sadar Bazar" exists in many states) return None.
    """
    if not rows:
        return None
    # When a state is known, never accept another state's PIN: "Shivaji Nagar"
    # exists across India, and that is how a Gurugram address once ended up with
    # a Uttar Pradesh PIN.
    if state:
        rows = [r for r in rows if r["state"].lower() == state.lower()]
        if not rows:
            return None
    pins = {r["pincode"] for r in rows}
    return pins.pop() if len(pins) == 1 else None


def _post_office_search(query: str) -> List[Dict[str, str]]:
    """India Post post-office search, cached for a day."""
    key = query.strip().lower()
    now = time.time()
    with _lock:
        cached = _CACHE.get(key)
        if cached and (now - cached[0]) < _CACHE_TTL:
            return cached[1]

    rows: List[Dict[str, str]] = []
    try:
        import requests
        resp = requests.get(
            _API.format(q=requests.utils.quote(query)),
            headers=_HEADERS,
            timeout=4,
        )
        for block in (resp.json() or []):
            for p in (block.get("PostOffice") or []):
                pin = (p.get("Pincode") or "").strip()
                if re.match(r"^[1-9][0-9]{5}$", pin):
                    rows.append({
                        "name": (p.get("Name") or "").strip(),
                        "pincode": pin,
                        "district": (p.get("District") or "").strip(),
                        "state": (p.get("State") or "").strip(),
                        "block": (p.get("Block") or "").strip(),
                    })
    except Exception as exc:
        logger.info("India Post search failed for %r: %s", query, exc)
        rows = []

    with _lock:
        _CACHE[key] = (now, rows)
    return rows


def pincode_state(pin: str) -> Optional[str]:
    """
    Which state does a PIN belong to (India Post)? Cached.

    Used to reject provider-supplied PINs that belong to another state — e.g. a
    Gurugram address tagged with 242221 (Uttar Pradesh).
    """
    if not pin:
        return None
    cache_key = f"__pin__{pin}"
    now = time.time()
    with _lock:
        cached = _CACHE.get(cache_key)
        if cached and (now - cached[0]) < _CACHE_TTL:
            rows = cached[1]
            return rows[0]["state"] if rows else None

    rows: List[Dict[str, str]] = []
    try:
        import requests
        resp = requests.get(
            f"https://api.postalpincode.in/pincode/{pin}",
            headers=_HEADERS, timeout=4,
        )
        block = (resp.json() or [{}])[0]
        if block.get("Status") == "Success":
            for p in (block.get("PostOffice") or [])[:1]:
                rows.append({
                    "name": (p.get("Name") or "").strip(),
                    "pincode": pin,
                    "district": (p.get("District") or "").strip(),
                    "state": (p.get("State") or "").strip(),
                    "block": (p.get("Block") or "").strip(),
                })
    except Exception as exc:
        logger.info("PIN state lookup failed for %s: %s", pin, exc)

    with _lock:
        _CACHE[cache_key] = (now, rows)
    return rows[0]["state"] if rows else None


def verify_pincode(components: Dict[str, str], osm_pincode: Optional[str]) -> Dict[str, Any]:
    """
    Recommend the authoritative PIN code for an OSM address.

    Returns:
        {
          "pincode": best PIN (may equal osm_pincode),
          "corrected": bool,
          "confidence": "high" | "medium" | "low",
          "source": "India Post",
          "reason": human readable note,
          "alternatives": [...]
        }
    """
    city = (components.get("city") or "").strip()
    locality = (components.get("locality") or "").strip()
    road = (components.get("road") or "").strip()
    state = (components.get("state") or "").strip()

    # â”€â”€ Step 1: unambiguous place name â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Most specific first: city ("Delhi Cantonment" -> 110010), then locality
    # ("Karol Bagh" -> 110005). If a name maps to exactly one PIN in the state,
    # that is authoritative and we stop â€” this avoids "Sadar Bazar" (110006,
    # North Delhi) hijacking a Delhi-Cantonment address.
    for raw in (city, locality):
        for variant in _normalise(raw):
            rows = _post_office_search(variant)
            pin = _unique_pin(rows, state)
            if pin:
                corrected = bool(osm_pincode and pin != osm_pincode)
                reason = (
                    f"OpenStreetMap tagged this address {osm_pincode}, but India Post maps "
                    f"'{variant}' ({state or 'India'}) to {pin}."
                    if corrected else
                    f"PIN {pin} confirmed against India Post for '{variant}'."
                )
                return {
                    "pincode": pin,
                    "corrected": corrected,
                    "confidence": "high",
                    "unambiguous": True,
                    "source": "India Post",
                    "reason": reason,
                    "matched_on": variant,
                    "alternatives": [],
                }

    # â”€â”€ Step 2: score candidates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    address_tokens = _tokens(" ".join([road, locality, city]))
    queries: List[str] = []
    for raw in (city, locality, road):
        for variant in _normalise(raw):
            if variant and variant.lower() not in [q.lower() for q in queries]:
                queries.append(variant)

    scores: Dict[str, int] = {}
    meta: Dict[str, Dict[str, str]] = {}

    for idx, query in enumerate(queries[:4]):
        rows = _post_office_search(query)
        if not rows:
            continue
        # Prefer rows in the same state when OSM told us one.
        same_state = [r for r in rows if not state or r["state"].lower() == state.lower()]
        pool = same_state or rows

        for row in pool:
            pin = row["pincode"]
            score = 0
            name_tokens = _tokens(row["name"])
            score += 3 * len(address_tokens & name_tokens)
            if address_tokens & _tokens(row["district"]):
                score += 2
            if row["state"].lower() == state.lower():
                score += 1
            if pin == osm_pincode:
                score += 4                      # keep OSM's PIN unless clearly beaten
            score += max(0, 3 - idx)            # earlier queries are more specific
            if query.lower().startswith(row["name"].lower()) or row["name"].lower() in query.lower():
                score += 3                      # the post office name echoes our query
            scores[pin] = max(scores.get(pin, 0), score)
            meta.setdefault(pin, row)

    if not scores:
        return {
            "pincode": osm_pincode,
            "corrected": False,
            "confidence": "low",
            "source": "OpenStreetMap only",
            "reason": "India Post returned no match for this locality.",
            "alternatives": [],
        }

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_pin, best_score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0

    confidence = "high" if best_score >= 6 and (best_score - runner_up) >= 3 else (
        "medium" if best_score >= 4 else "low"
    )

    corrected = bool(osm_pincode and best_pin != osm_pincode and confidence == "high")
    if corrected:
        reason = (f"OpenStreetMap tagged this address {osm_pincode}, but India Post "
                  f"lists {meta[best_pin]['name']} ({meta[best_pin]['district']}) under {best_pin}.")
    elif osm_pincode:
        reason = f"PIN {osm_pincode} confirmed against India Post."
    else:
        reason = f"PIN {best_pin} resolved from India Post."

    return {
        "pincode": best_pin if (corrected or not osm_pincode or confidence == "high") else osm_pincode,
        "corrected": corrected,
        "unambiguous": False,
        "confidence": confidence,
        "source": "India Post",
        "reason": reason,
        "candidate_pincode": best_pin,
        "score": best_score,
        "alternatives": [
            {"pincode": p, "score": s, "post_office": meta.get(p, {}).get("name", "")}
            for p, s in ranked[:3]
        ],
    }
