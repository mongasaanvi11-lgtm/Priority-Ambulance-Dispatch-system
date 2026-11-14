"""
AmbuPriority — Resilient geocoding service
==========================================
OpenStreetMap's Nominatim is free but throttles hard (HTTP 429). Once throttled,
every reverse-geocode call fails and the UI degrades to raw coordinates.

This module wraps geocoding with three layers so the app keeps working:

    1. A process-wide rate limiter  (max ~1 request/second to Nominatim)
    2. Retry with backoff on 429
    3. Fallback providers           (BigDataCloud, Photon) when OSM gives up
    4. Long-lived caches            (reverse keyed by ~11 m, forward 10 min)

All functions return the same normalised dictionary shape the UI already
expects: title / subtitle / full_address / lat / lon / locality / city / state /
pincode / accuracy_* / type / source.
"""

import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_UA = "AmbuPriorityEmergencyDispatch/2.0 (contact: admin@ambupriority.gov.in)"

# ── Rate limiting ────────────────────────────────────────────────────────────
_nominatim_lock = threading.Lock()
_last_nominatim_call = 0.0
_NOMINATIM_MIN_INTERVAL = 1.1          # seconds between calls (OSM policy: <=1/s)

# ── Caches ───────────────────────────────────────────────────────────────────
_reverse_cache: Dict[str, tuple] = {}
_forward_cache: Dict[str, tuple] = {}
_REVERSE_TTL = 86400                   # reverse of a point does not change
_FORWARD_TTL = 600


def _throttle() -> None:
    """Space Nominatim calls to at most one per interval (thread-safe)."""
    global _last_nominatim_call
    with _nominatim_lock:
        wait = _NOMINATIM_MIN_INTERVAL - (time.time() - _last_nominatim_call)
        if wait > 0:
            time.sleep(wait)
        _last_nominatim_call = time.time()


def _http_get_json(url: str, timeout: float = 6.0, use_nominatim: bool = False):
    """GET a JSON document, with throttling. 429 fails fast to the next provider."""
    attempts = 2 if use_nominatim else 1
    for attempt in range(attempts):
        if use_nominatim:
            _throttle()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                # Persistent throttle: stop retrying, let the caller fall back.
                logger.info("Nominatim 429 — switching to fallback provider")
                return None
            logger.info("HTTP %s from %s", exc.code, url.split("?")[0])
            return None
        except Exception as exc:
            logger.info("Request failed (%s): %s", type(exc).__name__, str(exc)[:100])
            if attempt + 1 < attempts:
                time.sleep(1.0)
    return None


# ── Normalisation helpers ────────────────────────────────────────────────────
def _clean_pin(value: Any) -> Optional[str]:
    pin = str(value or "").strip()
    return pin if re.match(r"^[1-9][0-9]{5}$", pin) else None


def _normalise(parts: Dict[str, Any]) -> Dict[str, Any]:
    title = (parts.get("title") or "").strip()
    locality = (parts.get("locality") or "").strip()
    city = (parts.get("city") or "").strip()
    state = (parts.get("state") or "").strip()
    pincode = _clean_pin(parts.get("pincode"))

    components = [c for c in [title, locality, city, state, pincode, "India"] if c and c != title]
    full_address = ", ".join([c for c in [title] if c] + components)

    return {
        "title": title or locality or city or "Detected Location",
        "subtitle": ", ".join([c for c in [locality, city, state, pincode] if c]),
        "full_address": full_address,
        "lat": parts.get("lat"),
        "lon": parts.get("lon"),
        "locality": locality,
        "city": city or locality,
        "state": state,
        "pincode": pincode,
        "accuracy_m": parts.get("accuracy_m"),
        "accuracy_status": parts.get("accuracy_status", "RELIABLE"),
        "accuracy_warning": parts.get("accuracy_warning"),
        "type": parts.get("type", "place"),
        "source": parts.get("source", "OpenStreetMap"),
    }


# ── Reverse geocoding ────────────────────────────────────────────────────────
def _reverse_nominatim(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    url = (f"https://nominatim.openstreetmap.org/reverse?"
           f"format=jsonv2&lat={lat}&lon={lon}&addressdetails=1&zoom=18")
    data = _http_get_json(url, use_nominatim=True)
    if not data or not data.get("address"):
        return None
    a = data["address"]
    road = (a.get("road") or a.get("pedestrian") or a.get("street") or "").strip()
    name = (data.get("name") or "").strip()
    return {
        "title": name or road or a.get("suburb") or a.get("neighbourhood") or "",
        "locality": (a.get("suburb") or a.get("neighbourhood") or a.get("residential")
                     or a.get("city_district") or "").strip(),
        "city": (a.get("city") or a.get("town") or a.get("village") or a.get("municipality") or "").strip(),
        "state": (a.get("state") or "").strip(),
        "pincode": a.get("postcode"),
        "lat": float(data.get("lat", lat)),
        "lon": float(data.get("lon", lon)),
        "type": data.get("type", "place"),
        "source": "OpenStreetMap",
    }


def _reverse_bigdatacloud(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    url = (f"https://api.bigdatacloud.net/data/reverse-geocode-client?"
           f"latitude={lat}&longitude={lon}&localityLanguage=en")
    data = _http_get_json(url, timeout=6)
    if not data:
        return None
    locality = (data.get("locality") or data.get("localityInfo", {}).get("administrative", [{}])[0].get("name") or "")
    city = (data.get("city") or data.get("principalSubdivision") or "").strip()
    state = (data.get("principalSubdivision") or "").strip()
    if not (locality or city):
        return None
    return {
        "title": locality or city,
        "locality": locality,
        "city": city,
        "state": state,
        "pincode": data.get("postcode"),
        "lat": lat,
        "lon": lon,
        "type": "place",
        "source": "BigDataCloud",
    }


def _reverse_photon(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    url = f"https://photon.komoot.io/reverse?lat={lat}&lon={lon}"
    data = _http_get_json(url, timeout=6)
    features = (data or {}).get("features") or []
    if not features:
        return None
    p = features[0].get("properties") or {}
    title = (p.get("name") or p.get("street") or "").strip()
    locality = (p.get("district") or p.get("locality") or "").strip()
    city = (p.get("city") or "").strip()
    if not (title or locality or city):
        return None
    return {
        "title": title or locality or city,
        "locality": locality,
        "city": city,
        "state": (p.get("state") or "").strip(),
        "pincode": p.get("postcode"),
        "lat": lat,
        "lon": lon,
        "type": "place",
        "source": "Photon",
    }


def reverse_geocode(lat: float, lon: float, accuracy_m: Optional[float] = None) -> Dict[str, Any]:
    """
    Reverse-geocode with provider fallback. Never raises; always returns a dict.

    Result is cached per ~11 m grid so repeated GPS updates cost nothing.
    """
    key = f"{round(lat, 4)},{round(lon, 4)}"
    cached = _reverse_cache.get(key)
    if cached and (time.time() - cached[0]) < _REVERSE_TTL:
        out = dict(cached[1])
        out["accuracy_m"] = accuracy_m
        return out

    for provider in (_reverse_nominatim, _reverse_bigdatacloud, _reverse_photon):
        try:
            parts = provider(lat, lon)
        except Exception as exc:
            logger.info("Reverse provider %s failed: %s", provider.__name__, exc)
            parts = None
        if parts:
            parts["accuracy_m"] = accuracy_m
            normalised = _normalise(parts)
            _reverse_cache[key] = (time.time(), normalised)
            return dict(normalised)

    # Last resort: coordinates, clearly labelled so the UI does not lie.
    fallback = _normalise({
        "title": f"{lat:.5f}, {lon:.5f}",
        "locality": "", "city": "", "state": "",
        "lat": lat, "lon": lon, "accuracy_m": accuracy_m,
        "accuracy_status": "COORDINATES_ONLY",
        "accuracy_warning": "Address lookup is temporarily unavailable; showing GPS coordinates.",
        "source": "GPS",
    })
    return fallback


# ── Forward geocoding ────────────────────────────────────────────────────────
def _forward_nominatim(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    url = (f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}"
           f"&format=jsonv2&countrycodes=in&addressdetails=1&limit={limit}")
    data = _http_get_json(url, use_nominatim=True)
    out = []
    for item in (data or []):
        a = item.get("address", {}) or {}
        out.append({
            "title": (item.get("name") or a.get("road") or a.get("suburb")
                      or a.get("city") or a.get("town") or query),
            "locality": (a.get("suburb") or a.get("neighbourhood") or a.get("city_district") or ""),
            "city": (a.get("city") or a.get("town") or a.get("village") or ""),
            "state": a.get("state") or "",
            "pincode": a.get("postcode"),
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
            "type": item.get("type", "place"),
            "source": "OpenStreetMap",
        })
    return out


def _forward_photon(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(query)}&limit={limit}"
    data = _http_get_json(url, timeout=6)
    out = []
    for feature in ((data or {}).get("features") or []):
        p = feature.get("properties") or {}
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coords) < 2:
            continue
        if (p.get("countrycode") or "").upper() not in ("IN", ""):
            continue
        out.append({
            "title": (p.get("name") or p.get("street") or p.get("city") or query),
            "locality": (p.get("district") or p.get("locality") or ""),
            "city": (p.get("city") or ""),
            "state": p.get("state") or "",
            "pincode": p.get("postcode"),
            "lat": float(coords[1]),
            "lon": float(coords[0]),
            "type": "place",
            "source": "Photon",
        })
    return out


def forward_geocode(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Forward-geocode with fallback; returns normalised results (may be empty)."""
    key = f"{query.strip().lower()}|{limit}"
    cached = _forward_cache.get(key)
    if cached and (time.time() - cached[0]) < _FORWARD_TTL:
        return list(cached[1])

    results = _forward_nominatim(query, limit)
    source = "OpenStreetMap"
    if not results:
        logger.info("Nominatim forward returned nothing — trying Photon for %r", query)
        results = _forward_photon(query, limit)
        source = "Photon"

    normalised = [_normalise(r) for r in results]
    if normalised:
        _forward_cache[key] = (time.time(), normalised)
    return normalised
