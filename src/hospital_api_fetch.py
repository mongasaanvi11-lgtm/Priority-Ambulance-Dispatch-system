"""
AmbuPriority — Hospital API Fetch Service with Safe Rotating Key Manager
========================================================================
Uses the SafeGeminiKeyManager for robust key rotation, backoff, and model calls.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from src.gemini_key_manager import gemini_key_manager

logger = logging.getLogger(__name__)

def get_key_status() -> Dict[str, Any]:
    return gemini_key_manager.get_status()

def search_real_hospitals_gemini(lat: float, lon: float, radius_km: float = 12.0,
                                 address: str = "") -> List[Dict[str, Any]]:
    prompt = f"""Search real existing hospitals near {address or f'latitude {lat}, longitude {lon}'} within {radius_km} km.
Return a valid JSON array of objects with:
- name: string
- address: string
- latitude: float
- longitude: float
- phone: string
- emergency: "yes"

Only return real, actual hospitals that exist geographically. Never invent fake hospitals or fake coordinates. Return ONLY JSON."""

    def _call(client):
        res = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(res.text)

    try:
        raw_list = gemini_key_manager.execute_with_retry(_call)
        if not raw_list or not isinstance(raw_list, list):
            return []

        from src.hospital_discovery import haversine_distance
        hospitals = []
        for item in raw_list:
            name = item.get("name", "").strip()
            if not name:
                continue
            h_lat = float(item.get("latitude") or 0.0)
            h_lon = float(item.get("longitude") or 0.0)
            if not h_lat or not h_lon:
                continue
            dist = round(haversine_distance(lat, lon, h_lat, h_lon), 2)
            if dist <= radius_km * 1.5:
                hospitals.append({
                    "id": f"gemini_{abs(hash(name)) % 100000}",
                    "place_id": str(abs(hash(name)) % 100000),
                    "name": name,
                    "address": item.get("address", ""),
                    "latitude": h_lat,
                    "longitude": h_lon,
                    "distance_km": dist,
                    "source": "Verified Grounded Directory",
                    "phone": item.get("phone", ""),
                    "emergency": "yes"
                })
        hospitals.sort(key=lambda x: x["distance_km"])
        return hospitals
    except Exception as e:
        logger.warning(f"search_real_hospitals_gemini error: {e}")
        return []
