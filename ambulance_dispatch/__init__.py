"""
ambulance_dispatch - Core package for ResQTrack Priority Ambulance Dispatch System.
Educational prototype for emergency triage and priority-based ambulance routing.
"""

__version__ = "0.3.0"
__author__ = "ResQTrack Educational Project Team"

from .config import (
    DEFAULT_DB_PATH,
    DEMO_CENTER_LAT,
    DEMO_CENTER_LNG,
    DEMO_CITY_NAME,
)
from .constants import (
    AVAILABLE_SYMPTOMS,
    DISCLAIMER_TEXT,
    SHORT_DISCLAIMER,
    STAGE_1_RED_FLAG_SYMPTOMS,
    VALID_STATUS_TRANSITIONS,
    AmbulanceStatus,
    IncidentStatus,
    TriageLevel,
)
from .database import (
    AmbulanceNotAvailableError,
    AmbulanceNotFoundError,
    DatabaseError,
    IncidentNotFoundError,
    assign_ambulance_to_incident,
    create_incident,
    get_ambulance,
    get_db_connection,
    get_incident,
    init_db,
    list_active_incidents,
    list_ambulances,
    list_events_for_incident,
    list_incidents,
    progress_incident_status,
    record_event,
    seed_demo_fleet_if_empty,
    update_ambulance_status,
    update_incident_status,
)
from .dispatcher import (
    advance_incident_status,
    dispatch_incident,
    dispatch_next_highest_priority,
    find_nearest_available_ambulance,
    sort_incident_queue,
)
from .geo import (
    haversine_distance_km,
    is_valid_coordinate,
)
from .seed_data import (
    load_demo_incidents,
)
from .triage import (
    calculate_demo_priority_score,
    check_sklearn_availability,
    check_stage1_symptoms,
    evaluate_triage,
)

__all__ = [
    "__version__",
    "DISCLAIMER_TEXT",
    "SHORT_DISCLAIMER",
    "TriageLevel",
    "AmbulanceStatus",
    "IncidentStatus",
    "VALID_STATUS_TRANSITIONS",
    "STAGE_1_RED_FLAG_SYMPTOMS",
    "AVAILABLE_SYMPTOMS",
    "DEFAULT_DB_PATH",
    "DEMO_CENTER_LAT",
    "DEMO_CENTER_LNG",
    "DEMO_CITY_NAME",
    "DatabaseError",
    "IncidentNotFoundError",
    "AmbulanceNotFoundError",
    "AmbulanceNotAvailableError",
    "get_db_connection",
    "init_db",
    "seed_demo_fleet_if_empty",
    "create_incident",
    "get_incident",
    "list_incidents",
    "list_active_incidents",
    "update_incident_status",
    "progress_incident_status",
    "list_ambulances",
    "get_ambulance",
    "update_ambulance_status",
    "assign_ambulance_to_incident",
    "record_event",
    "list_events_for_incident",
    "haversine_distance_km",
    "is_valid_coordinate",
    "evaluate_triage",
    "check_stage1_symptoms",
    "calculate_demo_priority_score",
    "check_sklearn_availability",
    "sort_incident_queue",
    "find_nearest_available_ambulance",
    "dispatch_incident",
    "dispatch_next_highest_priority",
    "advance_incident_status",
    "load_demo_incidents",
]
