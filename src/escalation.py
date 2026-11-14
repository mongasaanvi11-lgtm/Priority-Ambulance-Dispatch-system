from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class BaseDispatchAdapter(ABC):
    """
    Abstract interface for authorized emergency hospital and ambulance dispatch partners.
    Never claims dispatch succeeded unless confirmed by an authorized real endpoint.
    """
    @abstractmethod
    def request_dispatch(self, patient_details: Dict[str, Any]) -> Dict[str, Any]:
        pass

class MockOrUnconfiguredDispatchAdapter(BaseDispatchAdapter):
    """
    Default unconfigured adapter. Strictly adheres to honesty rules:
    Always reports honestly that NO automated dispatch API is active.
    """
    def request_dispatch(self, patient_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dispatched": False,
            "status": "NOT_DISPATCHED",
            "message": (
                "⚠️ No live ambulance dispatch API is currently integrated or active. "
                "The ambulance has NOT been dispatched automatically. "
                "Please call your local emergency service (e.g. 112 / 108 / 102 / 911) directly immediately."
            ),
            "partner": "None (Direct Call Required)"
        }

def get_escalation_options():
    return [
        {"id": "emergency", "label": "🚨 Call Emergency Services (112 / 911)", "action": "call_112"},
        {"id": "ambulance", "label": "🚑 Request Ambulance / Emergency Helpline", "action": "ambulance"},
        {"id": "hospital", "label": "🏥 Find Verified Hospital Nearby", "action": "hospital"},
        {"id": "doctor", "label": "👨‍⚕️ Connect to On-Call Doctor / Tele-Triage", "action": "doctor"}
    ]

