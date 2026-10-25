"""
Priority Queue & Ambulance Dispatch Engine.
Manages priority ordering (RED > YELLOW > GREEN), Haversine nearest-neighbor
vehicle selection, atomic assignment, and lifecycle progression.
"""

from typing import Any, Dict, List, Optional, Tuple

from .constants import AmbulanceStatus, IncidentStatus, TriageLevel
from .database import (
    AmbulanceNotAvailableError,
    AmbulanceNotFoundError,
    DatabaseError,
    IncidentNotFoundError,
    assign_ambulance_to_incident,
    get_ambulance,
    get_incident,
    list_ambulances,
    list_incidents,
    progress_incident_status,
)
from .geo import haversine_distance_km, is_valid_coordinate


def sort_incident_queue(incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort incidents deterministically:
    1. Triage priority rank: RED (1) > YELLOW (2) > GREEN (3)
    2. Urgency score (demo_priority_score DESC)
    3. Created timestamp (created_at ASC) as fair waiting-time tie breaker
    """
    def sort_key(item: Dict[str, Any]) -> Tuple[int, float, str]:
        level_str = item.get("triage_level", "GREEN")
        rank = {"RED": 1, "YELLOW": 2, "GREEN": 3}.get(level_str, 4)
        score = float(item.get("demo_priority_score") or 0.0)
        created = str(item.get("created_at") or "")
        # Note: -score for descending order
        return (rank, -score, created)

    return sorted(incidents, key=sort_key)


def find_nearest_available_ambulance(
    incident_lat: float,
    incident_lng: float,
    db_path: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
    """
    Find the closest AVAILABLE ambulance using straight-line Haversine distance.
    Returns (ambulance_dict, distance_km) or (None, None) if no eligible vehicle.
    """
    if not is_valid_coordinate(incident_lat, incident_lng):
        return None, None

    available_fleet = list_ambulances(status=AmbulanceStatus.AVAILABLE.value, db_path=db_path)
    if not available_fleet:
        return None, None

    nearest_ambulance = None
    min_distance = float("inf")

    for amb in available_fleet:
        amb_lat = amb.get("current_lat")
        amb_lng = amb.get("current_lng")
        if not is_valid_coordinate(amb_lat, amb_lng):
            continue

        dist = haversine_distance_km(incident_lat, incident_lng, amb_lat, amb_lng)
        if dist < min_distance:
            min_distance = dist
            nearest_ambulance = amb

    if nearest_ambulance is not None:
        return nearest_ambulance, round(min_distance, 2)
    return None, None


def dispatch_incident(
    incident_id: int,
    ambulance_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Dispatch an ambulance to a specific pending incident.
    If ambulance_id is omitted, automatically finds the nearest available ambulance.
    
    Guarantees:
      - Incident must be in PENDING status.
      - Selected ambulance must be AVAILABLE.
      - Atomic transaction updates both records and logs dispatch event.
    """
    incident = get_incident(incident_id, db_path=db_path)
    if not incident:
        return False, f"Incident #{incident_id} not found."

    if incident["status"] != IncidentStatus.PENDING.value:
        return False, f"Incident #{incident_id} is already in '{incident['status']}' status (cannot dispatch)."

    inc_lat = incident.get("latitude")
    inc_lng = incident.get("longitude")

    chosen_ambulance_id = ambulance_id
    distance_note = ""

    if not chosen_ambulance_id:
        if not is_valid_coordinate(inc_lat, inc_lng):
            return False, f"Incident #{incident_id} has invalid GPS coordinates ({inc_lat}, {inc_lng})."

        nearest_amb, dist = find_nearest_available_ambulance(inc_lat, inc_lng, db_path=db_path)
        if not nearest_amb:
            return False, "No AVAILABLE ambulances with valid coordinates found in fleet."
        chosen_ambulance_id = nearest_amb["ambulance_id"]
        distance_note = f" (approx. {dist:.2f} km straight-line distance)"
    else:
        # Check specific ambulance availability
        amb = get_ambulance(chosen_ambulance_id, db_path=db_path)
        if not amb:
            return False, f"Ambulance {chosen_ambulance_id} not found."
        if amb["status"] != AmbulanceStatus.AVAILABLE.value:
            return False, f"Ambulance {chosen_ambulance_id} is not AVAILABLE (currently {amb['status']})."
        if is_valid_coordinate(inc_lat, inc_lng) and is_valid_coordinate(amb.get("current_lat"), amb.get("current_lng")):
            dist = haversine_distance_km(inc_lat, inc_lng, amb["current_lat"], amb["current_lng"])
            distance_note = f" (approx. {dist:.2f} km straight-line distance)"

    note = f"Dispatched {chosen_ambulance_id} to Incident #{incident_id}{distance_note}"

    try:
        assign_ambulance_to_incident(
            ambulance_id=chosen_ambulance_id,
            incident_id=incident_id,
            note=note,
            db_path=db_path,
        )
        return True, f"Successfully dispatched {chosen_ambulance_id} to Incident #{incident_id}{distance_note}."
    except AmbulanceNotAvailableError as e:
        return False, f"Dispatch failed: Ambulance was already assigned ({e})."
    except DatabaseError as e:
        return False, f"Dispatch failed due to database error: {e}"


def dispatch_next_highest_priority(db_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Select and dispatch the highest-priority waiting incident from the queue.
    """
    pending_incidents = list_incidents(status=IncidentStatus.PENDING.value, db_path=db_path)
    if not pending_incidents:
        return False, "No pending emergency incidents waiting in queue."

    sorted_queue = sort_incident_queue(pending_incidents)
    top_incident = sorted_queue[0]

    return dispatch_incident(top_incident["incident_id"], db_path=db_path)


def advance_incident_status(
    incident_id: int,
    target_status: str,
    note: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Safely advance an incident's lifecycle:
    DISPATCHED -> EN_ROUTE -> AT_HOSPITAL -> COMPLETED / CANCELLED.
    Releases assigned ambulance when reaching terminal state.
    """
    incident = get_incident(incident_id, db_path=db_path)
    if not incident:
        return False, f"Incident #{incident_id} not found."

    current_status = incident["status"]
    try:
        success = progress_incident_status(
            incident_id=incident_id,
            new_status=target_status,
            note=note,
            db_path=db_path,
        )
        if success:
            return True, f"Incident #{incident_id} progressed from {current_status} to {target_status}."
        return False, f"Could not update status for Incident #{incident_id}."
    except DatabaseError as e:
        return False, f"Status progression failed: {e}"
