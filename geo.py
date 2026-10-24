"""
Geospatial calculations for straight-line ambulance distance.
Uses the spherical Haversine formula (pure Python, zero external APIs).
"""

import math
from typing import Optional

# Earth's mean radius in kilometers
EARTH_RADIUS_KM = 6371.0


def is_valid_coordinate(lat: Optional[float], lng: Optional[float]) -> bool:
    """Validate latitude (-90 to 90) and longitude (-180 to 180)."""
    if lat is None or lng is None:
        return False
    try:
        f_lat = float(lat)
        f_lng = float(lng)
        return (-90.0 <= f_lat <= 90.0) and (-180.0 <= f_lng <= 180.0)
    except (ValueError, TypeError):
        return False


def haversine_distance_km(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """
    Calculate the great-circle straight-line distance between two points on Earth in kilometers.
    
    NOTE: This is a straight-line Euclidean-approximated distance and does not reflect
    actual road networks, traffic conditions, or driving routes.
    """
    if not (is_valid_coordinate(lat1, lng1) and is_valid_coordinate(lat2, lng2)):
        raise ValueError(
            f"Invalid coordinates provided: ({lat1}, {lng1}) to ({lat2}, {lng2}). "
            "Latitude must be between -90 and 90; longitude between -180 and 180."
        )

    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    # Haversine formula
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Clip to [0, 1] to avoid math domain errors due to floating-point rounding
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_KM * c
    return round(distance, 2)
