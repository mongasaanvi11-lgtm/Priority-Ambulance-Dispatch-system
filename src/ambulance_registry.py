"""
AmbuPriority — Persistent Demo Ambulance Fleet Registry & Recommendation Engine
==============================================================================
Stores persistent ambulance units associated with hospital IDs/names.
Each ambulance record contains:
- ambulance_id: Stable identifier / vehicle tag
- vehicle_id: Formatted vehicle registration / fleet plate
- hospital_id: (or normalized hospital identifier/hash)
- provider_name: Real or structured operating organization (e.g. Delhi CATS / Hospital Fleet)
- ownership: "Government" or "Private"
- type: "PTV", "BLS", "ALS", "ICU", "Cardiac", "Neonatal"
- availability_status: "AVAILABLE", "ASSIGNED", "OUT_OF_SERVICE"
- supported_priorities: list of ["RED", "YELLOW", "GREEN"]
- verified_capabilities: List of equipment and clinical capabilities
- qualified_staff: Staffing designation (Paramedic, EMT, Specialist)

Rules:
- Persistent across page reloads (deterministic/saved to disk).
- NOT randomly generated on every reload.
- Government ambulances: STRICTLY PTV, BLS, ALS.
- Private ambulances: PTV, BLS, ALS, ICU, Cardiac, Neonatal.
- Automated recommendation provides guidance ONLY. System NEVER automatically selects or books.
- Final ambulance selection belongs strictly to the user.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

AMBULANCES_FILE = Path(__file__).resolve().parent.parent / "data" / "ambulances.json"

# Standard equipment & capabilities catalog per ambulance category
AMBULANCE_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    "PTV": {
        "equipment": ["Patient Stretcher", "Basic First Aid Kit", "Manual Wheelchair Access"],
        "qualified_staff": "Trained Transport Driver & Attendant",
        "priority_support": ["GREEN"],
        "description": "Patient Transport Vehicle for non-emergency transfer"
    },
    "BLS": {
        "equipment": ["Automated External Defibrillator (AED)", "Portable Oxygen Cylinder & Masks", "Suction Unit", "Immobilization Spine Board", "Cervical Collars", "Vital Signs Monitor"],
        "qualified_staff": "Certified Emergency Medical Technician (EMT-Basic)",
        "priority_support": ["YELLOW", "GREEN"],
        "description": "Basic Life Support for urgent, non-critical medical support"
    },
    "ALS": {
        "equipment": ["Multipara Cardiac Monitor / Defibrillator", "Transport Mechanical Ventilator", "Advanced Airway & Endotracheal Intubation Kit", "Syringe Infusion Pump", "Emergency Resuscitation Drugs", "IV Fluids"],
        "qualified_staff": "Advanced Paramedic & Emergency Nurse",
        "priority_support": ["RED", "YELLOW", "GREEN"],
        "description": "Advanced Life Support with invasive airway and cardiac monitoring"
    },
    "ICU": {
        "equipment": ["ICU Multi-channel Ventilator", "Invasive Arterial / CVP Pressure Monitoring", "Dual Syringe Infusion Pumps", "Portable Blood Gas & Point-of-Care Lab", "Defibrillator / External Pacer", "Suction Unit"],
        "qualified_staff": "Critical Care Physician / Intensivist & ICU Nurse",
        "priority_support": ["RED", "YELLOW", "GREEN"],
        "description": "Mobile Intensive Care Unit for critical multi-organ failure and ventilator support"
    },
    "Cardiac": {
        "equipment": ["12-Lead Diagnostic ECG Machine", "Bi-phasic Defibrillator with External Transcutaneous Pacer", "Oxygen & Nitric Delivery", "Cardiac Emergency Meds (Thrombolytics / Antiarrhythmics)", "Syringe Infusion Pumps"],
        "qualified_staff": "Cardiology Fellow / Specialist Nurse & ACLS Paramedic",
        "priority_support": ["RED", "YELLOW", "GREEN"],
        "description": "Dedicated Cardiac Care Ambulance for STEMI, arrhythmia and cardiac arrest"
    },
    "Neonatal": {
        "equipment": ["Transport Infant Incubator", "Neonatal Specialized Resuscitator", "Pulse Oximeter with Neonatal Sensors", "Infant IV Infusion Pump", "Temperature Servo-Control", "Micro-airway Equipment"],
        "qualified_staff": "Neonatal Intensivist / NICU Specialized Nurse",
        "priority_support": ["RED", "YELLOW", "GREEN"],
        "description": "Specialized Neonatal / Pediatric Intensive Care transport unit"
    }
}

def get_hospital_key(name: str) -> str:
    """Derive a stable clean hospital ID from name."""
    clean = "".join(ch.lower() for ch in name if ch.isalnum() or ch == ' ')
    clean = "_".join(clean.split())
    if not clean:
        return "hosp_gen"
    slug = clean[:24]
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:6]
    return f"{slug}_{h}"

_IN_MEMORY_AMBULANCES = None

def load_or_init_ambulances() -> Dict[str, List[Dict[str, Any]]]:
    """Load persistent ambulance records from disk, caching in memory."""
    global _IN_MEMORY_AMBULANCES
    if _IN_MEMORY_AMBULANCES is not None:
        return _IN_MEMORY_AMBULANCES
    if AMBULANCES_FILE.exists():
        try:
            with open(AMBULANCES_FILE, "r", encoding="utf-8") as f:
                _IN_MEMORY_AMBULANCES = json.load(f)
                return _IN_MEMORY_AMBULANCES
        except Exception:
            pass
    _IN_MEMORY_AMBULANCES = {}
    return _IN_MEMORY_AMBULANCES

def save_ambulances(data: Dict[str, List[Dict[str, Any]]]):
    """Save persistent ambulance records to disk and memory."""
    global _IN_MEMORY_AMBULANCES
    _IN_MEMORY_AMBULANCES = data
    AMBULANCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AMBULANCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def enrich_ambulance_record(amb: Dict[str, Any], hospital_name: str, is_govt: bool) -> Dict[str, Any]:
    """Ensures each ambulance record contains complete verified capabilities, provider, and vehicle ID."""
    amb_type = amb.get("type", "BLS")
    spec = AMBULANCE_SPECIFICATIONS.get(amb_type, AMBULANCE_SPECIFICATIONS["BLS"])
    
    # Ownership
    amb["ownership"] = "Government" if is_govt else "Private"
    
    # Provider name
    if "provider_name" not in amb or not amb["provider_name"]:
        if is_govt:
            h_lower = hospital_name.lower()
            if "delhi" in h_lower or "aiims" in h_lower or "safdarjung" in h_lower:
                amb["provider_name"] = "Delhi CATS (Centralised Accident & Trauma Services)"
            else:
                amb["provider_name"] = f"Govt Emergency Medical Services ({hospital_name})"
        else:
            amb["provider_name"] = f"{hospital_name} Emergency Fleet"

    # Vehicle ID
    if "vehicle_id" not in amb or not amb["vehicle_id"]:
        amb_id = amb.get("ambulance_id", "AMB-100")
        num_part = "".join(ch for ch in amb_id if ch.isdigit()) or "101"
        state_code = "DL-01" if is_govt else "DL-04"
        amb["vehicle_id"] = f"{state_code}-EA-{int(num_part):04d}"

    # Verified equipment & capabilities
    if "verified_capabilities" not in amb or not amb["verified_capabilities"]:
        amb["verified_capabilities"] = spec["equipment"]

    # Qualified staff
    if "qualified_staff" not in amb or not amb["qualified_staff"]:
        amb["qualified_staff"] = spec["qualified_staff"]

    # Supported priorities
    if "supported_priorities" not in amb or not amb["supported_priorities"]:
        amb["supported_priorities"] = spec["priority_support"]

    return amb

def ensure_hospital_ambulances(hospital_name: str, hospital_id: str, is_govt: bool = False) -> List[Dict[str, Any]]:
    """
    Ensure deterministic persistent ambulance records exist for a hospital.
    Respects Government vs Private ambulance categories:
    - Government hospitals: only PTV, BLS, ALS (ICU, Cardiac, Neonatal strictly excluded).
    - Private hospitals: PTV, BLS, ALS, ICU, Cardiac, Neonatal.
    """
    records = load_or_init_ambulances()
    key = hospital_id or get_hospital_key(hospital_name)
    
    # If already cached, check validity, ownership alignment, and enrichment
    if key in records and records[key]:
        existing = records[key]
        has_generic_id = any(amb.get("ambulance_id", "").startswith("AMB-") for amb in existing)
        if not has_generic_id:
            if is_govt:
                filtered = [
                    amb for amb in existing
                    if amb.get("type") in ["PTV", "BLS", "ALS", "Patient Transport"]
                ]
                if filtered:
                    enriched = [enrich_ambulance_record(a, hospital_name, is_govt=True) for a in filtered]
                    records[key] = enriched
                    return enriched
            else:
                enriched = [enrich_ambulance_record(a, hospital_name, is_govt=False) for a in existing]
                records[key] = enriched
                return enriched
    
    # Deterministically generate fleet for this hospital using hash
    h_val = int(hashlib.md5(hospital_name.encode("utf-8")).hexdigest(), 16)
    pattern = h_val % 6
    
    fleet = []
    if is_govt:
        # Government ambulance categories: STRICTLY PTV, BLS, ALS
        if pattern in [0, 4]:
            fleet = [
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 100}-ALS",
                    "hospital_id": key,
                    "type": "ALS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 101}-BLS",
                    "hospital_id": key,
                    "type": "BLS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["YELLOW", "GREEN"]
                }
            ]
        elif pattern in [1, 5]:
            fleet = [
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 200}-ALS",
                    "hospital_id": key,
                    "type": "ALS",
                    "availability_status": "ASSIGNED",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 201}-BLS",
                    "hospital_id": key,
                    "type": "BLS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["YELLOW", "GREEN"]
                }
            ]
        elif pattern == 2:
            fleet = [
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 300}-PTV",
                    "hospital_id": key,
                    "type": "PTV",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["GREEN"]
                }
            ]
        else:
            fleet = [
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 400}-ALS",
                    "hospital_id": key,
                    "type": "ALS",
                    "availability_status": "OUT_OF_SERVICE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"GOV-AMB-{h_val%900 + 401}-BLS",
                    "hospital_id": key,
                    "type": "BLS",
                    "availability_status": "ASSIGNED",
                    "supported_priorities": ["YELLOW", "GREEN"]
                }
            ]
    else:
        # Private ambulance categories: PTV, BLS, ALS, ICU, Cardiac, Neonatal
        if pattern == 0:
            fleet = [
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 100}-ICU",
                    "hospital_id": key,
                    "type": "ICU",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 101}-BLS",
                    "hospital_id": key,
                    "type": "BLS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["YELLOW", "GREEN"]
                }
            ]
        elif pattern == 1:
            fleet = [
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 200}-Cardiac",
                    "hospital_id": key,
                    "type": "Cardiac",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 201}-ALS",
                    "hospital_id": key,
                    "type": "ALS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                }
            ]
        elif pattern == 2:
            fleet = [
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 300}-Neonatal",
                    "hospital_id": key,
                    "type": "Neonatal",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 301}-PTV",
                    "hospital_id": key,
                    "type": "PTV",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["GREEN"]
                }
            ]
        elif pattern == 3:
            fleet = [
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 400}-ALS",
                    "hospital_id": key,
                    "type": "ALS",
                    "availability_status": "ASSIGNED",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 401}-BLS",
                    "hospital_id": key,
                    "type": "BLS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["YELLOW", "GREEN"]
                }
            ]
        else:
            fleet = [
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 500}-ICU",
                    "hospital_id": key,
                    "type": "ICU",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                },
                {
                    "ambulance_id": f"PVT-AMB-{h_val%900 + 501}-ALS",
                    "hospital_id": key,
                    "type": "ALS",
                    "availability_status": "AVAILABLE",
                    "supported_priorities": ["RED", "YELLOW", "GREEN"]
                }
            ]
    
    enriched_fleet = [enrich_ambulance_record(amb, hospital_name, is_govt) for amb in fleet]
    records[key] = enriched_fleet
    save_ambulances(records)
    return enriched_fleet

def check_hospital_availability(hospital_name: str, hospital_id: str, patient_priority: str, is_govt: bool = False) -> str:
    """
    Determines if at least one ambulance at the hospital is AVAILABLE
    and supports the patient's priority.
    Returns: 'AVAILABLE' or 'NOT_AVAILABLE'
    """
    fleet = ensure_hospital_ambulances(hospital_name, hospital_id, is_govt=is_govt)
    norm_p = (patient_priority or "YELLOW").upper()
    
    if norm_p == "REVIEW_REQUIRED":
        target_priorities = ["RED", "YELLOW"]
    else:
        target_priorities = [norm_p]
    
    for amb in fleet:
        if amb.get("availability_status") == "AVAILABLE":
            supported = amb.get("supported_priorities", [])
            if any(p in supported for p in target_priorities):
                return "AVAILABLE"
                
    return "NOT_AVAILABLE"


# ─────────────────────────────────────────────────────────────────────────────
# INTELLIGENT AMBULANCE RECOMMENDATION ENGINE (GUIDANCE ONLY - USER DECIDES)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_ambulance_options(
    hospital_name: str,
    hospital_id: str,
    distance_km: float,
    patient_priority: str,
    chief_complaint: str = "",
    is_govt: bool = False,
    is_cats: bool = False,
    travel_time_minutes: int = 15
) -> Dict[str, Any]:
    """
    Evaluates all ambulance options for a selected hospital based on:
    - Patient emergency priority & structured complaint
    - Medical suitability (MUST COME BEFORE price or distance)
    - Verified availability
    - Capabilities & qualified staff
    - Distance, ETA, and verified/estimated fare
    
    Highlights the single most suitable available unit as 'RECOMMENDED FOR YOUR PRIORITY'
    with a concise clinical reason.
    DOES NOT automatically select any ambulance.
    """
    from src.ambulance_fare_service import calculate_ambulance_fare

    fleet = ensure_hospital_ambulances(hospital_name, hospital_id, is_govt=is_govt)
    norm_p = (patient_priority or "YELLOW").upper()
    if norm_p == "REVIEW_REQUIRED":
        target_priorities = ["RED", "YELLOW"]
    else:
        target_priorities = [norm_p]

    complaint_lower = (chief_complaint or "").lower()

    options = []
    for amb in fleet:
        amb_t = amb.get("type", "BLS")
        is_avail = (amb.get("availability_status") == "AVAILABLE")
        supported = amb.get("supported_priorities", [])
        
        # 1. Medical Suitability Assessment
        is_priority_supported = any(p in supported for p in target_priorities)
        medical_score = 0
        suitability_label = "Suitable"
        suitability_reason = ""

        # Category suitability hierarchy
        # RED: ALS, ICU, Cardiac (if cardiac issue), Neonatal (if pediatric/infant)
        # YELLOW: BLS, ALS, ICU, Cardiac
        # GREEN: PTV, BLS, ALS
        if norm_p == "RED" or "RED" in target_priorities:
            if amb_t in ["Cardiac"]:
                if any(term in complaint_lower for term in ["cardiac", "chest", "heart", "angina", "attack"]):
                    medical_score = 100
                    suitability_label = "Optimal Medical Match"
                    suitability_reason = "Dedicated 12-lead ECG, transcutaneous pacer and cardiology specialist for severe cardiac emergency."
                else:
                    medical_score = 88
                    suitability_label = "Advanced Cardiac & Resuscitation Support"
                    suitability_reason = "Defibrillator, cardiac monitoring and emergency resuscitation life-support capabilities."
            elif amb_t in ["Neonatal"]:
                if any(term in complaint_lower for term in ["neonatal", "infant", "baby", "pediatric", "child", "nicu"]):
                    medical_score = 100
                    suitability_label = "Optimal Medical Match"
                    suitability_reason = "Transport infant incubator and neonatal intensivist team for critical pediatric care."
                else:
                    medical_score = 70
                    suitability_label = "Neonatal/Pediatric Specialized Unit"
                    suitability_reason = "Specialized neonatal life-support unit; equipped for critical pediatric transport."
            elif amb_t in ["ICU"]:
                medical_score = 95
                suitability_label = "High Critical Care Capability"
                suitability_reason = "Mobile ICU ventilator, arterial monitoring and critical care intensivist for immediate life threat."
            elif amb_t in ["ALS"]:
                medical_score = 90
                suitability_label = "Recommended ALS Level"
                suitability_reason = "Advanced airway intubation, mechanical ventilation and ACLS paramedic crew for RED emergency priority."
            elif amb_t in ["BLS"]:
                medical_score = 40
                suitability_label = "Basic Care Only (Capability Caution)"
                suitability_reason = "Basic Life Support lacks invasive airway/ventilator support for RED priority, but available as emergency standby."
            else: # PTV
                medical_score = 10
                suitability_label = "Unsuitable for Emergency"
                suitability_reason = "PTV does not possess emergency life support resuscitation equipment."

        elif norm_p == "YELLOW":
            if amb_t in ["BLS"]:
                medical_score = 90
                suitability_label = "Clinically Appropriate (Standard BLS)"
                suitability_reason = "Automated external defibrillator, oxygen therapy, EMT team and immobilization for urgent YELLOW priority."
            elif amb_t in ["ALS"]:
                medical_score = 85
                suitability_label = "Enhanced Clinical Support"
                suitability_reason = "Provides advanced cardiac monitoring and paramedic oversight for escalating urgent symptoms."
            elif amb_t in ["Cardiac"] and any(term in complaint_lower for term in ["cardiac", "chest", "heart"]):
                medical_score = 95
                suitability_label = "Targeted Cardiac Support"
                suitability_reason = "Specialized cardiac monitoring suited for urgent chest discomfort."
            elif amb_t in ["ICU"]:
                medical_score = 75
                suitability_label = "Advanced Support Available"
                suitability_reason = "Higher tier intensive care unit with full physician support."
            elif amb_t in ["PTV"]:
                medical_score = 30
                suitability_label = "Sub-optimal for Urgent Intake"
                suitability_reason = "Limited monitoring equipment for acute medical symptoms."
            else:
                medical_score = 70
                suitability_label = "Clinically Suitable"
                suitability_reason = "Appropriate medical monitoring available."

        else: # GREEN
            if amb_t in ["PTV"]:
                medical_score = 95
                suitability_label = "Optimal Non-Urgent Transfer"
                suitability_reason = "Patient transport stretcher and attendant suited for non-urgent GREEN condition."
            elif amb_t in ["BLS"]:
                medical_score = 85
                suitability_label = "Suitable with Extra Support"
                suitability_reason = "Basic medical observation and oxygen support during transfer."
            else:
                medical_score = 60
                suitability_label = "Advanced Unit (Over-specified for non-urgent)"
                suitability_reason = "Fully equipped advanced ambulance capable of patient transport."

        # Compute accurate fare using formula
        fare_details = calculate_ambulance_fare(
            amb_type=amb_t,
            distance_km=distance_km,
            is_government=is_govt,
            is_cats_emergency=is_cats,
            is_emergency_priority=(norm_p in ["RED", "YELLOW", "REVIEW_REQUIRED"])
        )

        option_entry = {
            "ambulance_id": amb.get("ambulance_id"),
            "vehicle_id": amb.get("vehicle_id", "DL-01-EA-0101"),
            "category": amb_t,
            "provider_name": amb.get("provider_name", "Ambulance Provider"),
            "ownership": amb.get("ownership", "Government" if is_govt else "Private"),
            "is_government": is_govt,
            "availability_status": amb.get("availability_status", "AVAILABLE"),
            "supported_priorities": supported,
            "is_available": is_avail,
            "verified_capabilities": amb.get("verified_capabilities", []),
            "qualified_staff": amb.get("qualified_staff", "Paramedic Crew"),
            "distance_km": round(float(distance_km or 0.0), 2),
            "estimated_eta_minutes": travel_time_minutes,
            "rate_per_km": fare_details.get("rate_per_km", 0.0),
            "base_fare": fare_details.get("base_fare", 0.0),
            "total_fare": fare_details.get("total_fare", 0.0),
            "formatted_total": fare_details.get("formatted_total", "₹0.00"),
            "fare_status": fare_details.get("fare_status", "Project Estimate"),
            "fare_badge": fare_details.get("fare_badge", ""),
            "is_free": fare_details.get("is_free", False),
            "rate_breakdown": fare_details.get("rate_breakdown", ""),
            "medical_suitability_score": medical_score,
            "suitability_label": suitability_label,
            "suitability_reason": suitability_reason,
            "is_recommended": False,
            "recommendation_reason": ""
        }
        options.append(option_entry)

    # 2. Pick the Best Recommendation (Guidance only)
    # Strictly require ambulance to support the patient's priority
    # (e.g. RED priority strictly requires verified RED support - ALS/ICU/Cardiac)
    available_suitable = [
        o for o in options
        if o["is_available"] and any(p in o.get("supported_priorities", []) for p in target_priorities) and o["medical_suitability_score"] >= 60
    ]

    # Sort candidates strictly by:
    # 1. medical_suitability_score DESC (Medical suitability comes first)
    # 2. total_fare ASC (cost efficiency among medically sound choices)
    recommended_option = None
    if available_suitable:
        available_suitable.sort(key=lambda x: (-x["medical_suitability_score"], x["total_fare"]))
        recommended_option = available_suitable[0]
        recommended_option["is_recommended"] = True
        recommended_option["recommendation_reason"] = (
            f"Highest medical suitability for patient's {norm_p} priority intake: "
            f"{recommended_option['suitability_reason']}"
        )

    # All options sorted: Recommended first, then available candidates by suitability, then unavailable
    def sort_key(item):
        is_rec = 1 if item.get("is_recommended") else 0
        is_av = 1 if item.get("is_available") else 0
        score = item.get("medical_suitability_score", 0)
        return (-is_rec, -is_av, -score)

    options.sort(key=sort_key)

    has_available = any(o["is_available"] for o in options)
    has_suitable_available = (recommended_option is not None)

    alert_message = ""
    if not has_available:
        alert_message = "No ambulance from this hospital is currently verified as available. All active units are assigned or out of service."
    elif not has_suitable_available:
        alert_message = f"Ambulances are present on fleet, but none currently match the verified life-support capabilities required for {norm_p} emergency priority."

    return {
        "hospital_id": hospital_id,
        "hospital_name": hospital_name,
        "patient_priority": norm_p,
        "chief_complaint": chief_complaint,
        "distance_km": round(float(distance_km or 0.0), 2),
        "travel_time_minutes": travel_time_minutes,
        "has_available_options": has_available,
        "has_suitable_available_options": has_suitable_available,
        "recommended_ambulance_id": recommended_option["ambulance_id"] if recommended_option else None,
        "recommended_category": recommended_option["category"] if recommended_option else None,
        "alert_message": alert_message,
        "options": options,
        "guidance_notice": "Recommendation is guidance only based on clinical criteria. The system never automatically selects or books an ambulance. Final selection belongs to the user."
    }
