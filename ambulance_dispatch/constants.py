"""
Central constants, enums, and educational disclaimers for the dispatch system.
"""

from enum import Enum
from typing import Dict, List

# Persistent Educational & Non-Clinical Disclaimer
DISCLAIMER_TEXT = (
    "⚠️ EDUCATIONAL PROTOTYPE ONLY: This software is an academic demonstration project "
    "and must NOT be used for real clinical decisions or emergency response. "
    "The triage rules and predictions are simulated and not medically validated. "
    "If you or someone around you is facing an actual medical emergency, please immediately "
    "contact your local emergency services (e.g., 911, 112, 999). "
    "Never use this software for real emergency decisions."
)

SHORT_DISCLAIMER = (
    "🚨 DEMO ONLY: Not for clinical or real-world emergency use. "
    "In a real emergency, call 911 / 112 immediately."
)


class TriageLevel(str, Enum):
    """
    Three-tier triage classification with numerical priority ordering.
    Lower numerical rank = higher dispatch urgency.
    """
    RED = "RED"        # Priority 1: Critical / Life-threatening
    YELLOW = "YELLOW"  # Priority 2: Urgent / Serious
    GREEN = "GREEN"    # Priority 3: Non-urgent / Minor

    @property
    def priority_rank(self) -> int:
        """Return the integer sorting rank where 1 is highest priority."""
        ranks = {
            "RED": 1,
            "YELLOW": 2,
            "GREEN": 3,
        }
        return ranks[self.value]

    @property
    def badge_color(self) -> str:
        colors = {
            "RED": "#FF4B4B",
            "YELLOW": "#FFA500",
            "GREEN": "#28A745",
        }
        return colors[self.value]

    @property
    def emoji(self) -> str:
        emojis = {
            "RED": "🔴",
            "YELLOW": "🟡",
            "GREEN": "🟢",
        }
        return emojis[self.value]


class AmbulanceStatus(str, Enum):
    """Ambulance fleet status states."""
    AVAILABLE = "AVAILABLE"    # Ready for immediate dispatch
    ASSIGNED = "ASSIGNED"      # Assigned to an incident / on mission
    OFF_DUTY = "OFF_DUTY"      # Maintenance, refueling, or offline


class IncidentStatus(str, Enum):
    """Lifecycle status of an emergency request."""
    PENDING = "PENDING"          # Waiting in priority queue for ambulance allocation
    DISPATCHED = "DISPATCHED"    # Ambulance assigned and on the way
    EN_ROUTE = "EN_ROUTE"        # Ambulance en route to scene / patient
    AT_HOSPITAL = "AT_HOSPITAL"  # Ambulance arrived at hospital / ER transfer
    COMPLETED = "COMPLETED"      # Emergency resolved / patient transferred (releases ambulance)
    RESOLVED = "RESOLVED"        # Synonym for COMPLETED
    CANCELLED = "CANCELLED"      # Incident cancelled (releases ambulance)


# Valid progression sequence for incident lifecycle
VALID_STATUS_TRANSITIONS: Dict[IncidentStatus, List[IncidentStatus]] = {
    IncidentStatus.PENDING: [IncidentStatus.DISPATCHED, IncidentStatus.CANCELLED],
    IncidentStatus.DISPATCHED: [IncidentStatus.EN_ROUTE, IncidentStatus.CANCELLED],
    IncidentStatus.EN_ROUTE: [IncidentStatus.AT_HOSPITAL, IncidentStatus.CANCELLED],
    IncidentStatus.AT_HOSPITAL: [IncidentStatus.COMPLETED, IncidentStatus.RESOLVED, IncidentStatus.CANCELLED],
    IncidentStatus.COMPLETED: [],
    IncidentStatus.RESOLVED: [],
    IncidentStatus.CANCELLED: [],
}

# Source example symptoms used for Stage 1 deterministic red-flag overrides
STAGE_1_RED_FLAG_SYMPTOMS = [
    "chest pain",
    "shortness of breath",
    "loss of consciousness",
    "uncontrolled bleeding",
]

# Standard checklist options for user intake
AVAILABLE_SYMPTOMS = [
    "Chest pain",
    "Shortness of breath",
    "Loss of consciousness",
    "Uncontrolled bleeding",
    "Severe burn",
    "High fever",
    "Head injury / Concussion",
    "Severe abdominal pain",
    "Fracture / Suspected broken bone",
    "Dizziness / Lightheadedness",
    "Nausea / Vomiting",
    "Minor cut / abrasion",
    "Minor sprain",
]
