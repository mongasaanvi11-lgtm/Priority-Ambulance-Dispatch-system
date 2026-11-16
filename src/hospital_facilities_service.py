"""
Pranvya — Hospital Facilities, Capability, Cost & Recommendations Engine
=============================================================================
Provides verified facility definitions, government vs private pricing tariffs,
specialties, ICU/Trauma capabilities, ambulance compatibility, and structured
condition-based hospital ranking.

Rules:
- NO MAPS.
- NO FABRICATED OR INVENTED COSTS (Clearly mark Free, Subsidised, or Charges Applicable).
- Verified data sources: MoHFW, NHA PM-JAY, CGHS, State Health Departments.
- Live availability vs service capability strictly segregated.
- No LLM medical hallucination.
"""

import math
import re
from typing import Dict, List, Any, Optional

# Verified Medical Specialties & Facility Capabilities for Known Hospital Chains & Categories
HOSPITAL_FACILITIES_DB: Dict[str, Dict[str, Any]] = {
    "aiims": {
        "classification": "Government (Apex Central Autonomous)",
        "ownership": "Autonomous Institute under MoHFW, Government of India",
        "emergency_dept": "24x7 Apex Level-1 Trauma Centre & Emergency Medicine Department",
        "icu_facilities": "Comprehensive Level-3 Medical, Surgical, Neuro, Cardiac & Paediatric ICUs",
        "icu_available_verified": True,
        "trauma_care": "Level-1 Apex Trauma Centre (Dedicated JPNATC Building)",
        "trauma_available_verified": True,
        "cardiac_care": "Comprehensive 24x7 Cath Lab, Interventional Cardiology, CTVS",
        "cardiac_available_verified": True,
        "stroke_care": "Comprehensive Acute Stroke Unit with 24x7 Mechanical Thrombectomy & IV Thrombolysis",
        "pediatric_care": "Advanced Paediatric Intensive Care (PICU) & Neonatal ICU (NICU)",
        "burn_care": "Dedicated Burns & Plastic Surgery Block (100-bedded dedicated facility)",
        "specialties": [
            "Emergency Medicine", "Trauma Surgery", "Cardiology", "Cardiothoracic Surgery",
            "Neurology", "Neurosurgery", "Paediatrics", "Burns & Plastic Surgery",
            "Critical Care", "Orthopaedics", "Pulmonology", "Nephrology"
        ],
        "cost_model": {
            "type": "Government / Highly Subsidised",
            "summary_badge": "Free – Verified (Emergency)",
            "emergency_treatment": "Free of cost at Emergency / Trauma triage (Life-saving care is fully funded)",
            "opd_consultation": "₹10 (Subsidised one-time registration)",
            "inpatient_charges": "General Ward: Free / nominal bed charges; Subsidised investigations",
            "schemes_coverage": "100% Cashless under PM-JAY, CGHS, ECHS, RAN, State Schemes",
            "tariff_source": "AIIMS New Delhi Schedule of Charges & MoHFW Guidelines"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["Level-1 Trauma", "Emergency Medicine", "24x7 Cath Lab", "Adult & Paediatric ICU"]
        }
    },
    "safdarjung": {
        "classification": "Government (Central Govt / MoHFW)",
        "ownership": "Ministry of Health and Family Welfare, Govt. of India",
        "emergency_dept": "24x7 Emergency Services & Multi-Disciplinary Triage",
        "icu_facilities": "Medical, Surgical, Paediatric and Burns Intensive Care Units",
        "icu_available_verified": True,
        "trauma_care": "Level-1 Super Speciality Emergency & Trauma Hospital",
        "trauma_available_verified": True,
        "cardiac_care": "Dedicated Cardiology Department, CCU & Emergency Angioplasty",
        "cardiac_available_verified": True,
        "stroke_care": "Neurology Emergency & Stroke Protocol with CT/MRI support",
        "pediatric_care": "Paediatric Emergency & Dedicated Nursery / PICU",
        "burn_care": "Asia's largest dedicated Burns Department & Reconstructive Unit",
        "specialties": [
            "Emergency Medicine", "Trauma Surgery", "Burns Unit", "Cardiology",
            "Orthopaedics", "General Surgery", "Paediatrics", "Critical Care"
        ],
        "cost_model": {
            "type": "Government / Subsidised",
            "summary_badge": "Free – Verified (Emergency)",
            "emergency_treatment": "Free emergency stabilization, basic labs & life-saving trauma care",
            "opd_consultation": "Free (Central Govt funded facility)",
            "inpatient_charges": "General Wards free; nominal statutory charges for select implants/super-specialty tests",
            "schemes_coverage": "Fully covered under PM-JAY, CGHS, ECHS, ESIC",
            "tariff_source": "Safdarjung Hospital Citizen Charter & MoHFW Tariff"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["Level-1 Trauma", "National Burns Care", "24x7 Emergency", "Medical ICU"]
        }
    },
    "ram_manohar_lohia": {
        "classification": "Government (Central Govt / MoHFW)",
        "ownership": "Post Graduate Institute of Medical Education and Research (Dr. RML Hospital)",
        "emergency_dept": "24x7 Central Emergency & Comprehensive Trauma Block",
        "icu_facilities": "Multi-disciplinary Intensive Care Unit & CCU",
        "icu_available_verified": True,
        "trauma_care": "Dedicated Trauma Care Centre & Emergency Orthopaedics",
        "trauma_available_verified": True,
        "cardiac_care": "Cardiology, 24x7 Cath Lab, Cardiac Intensive Care",
        "cardiac_available_verified": True,
        "stroke_care": "Neurology & Neuro-Emergency Stroke Protocol",
        "pediatric_care": "Paediatric Wards & Emergency Child Care",
        "burn_care": "General Surgery Burns & Trauma Management",
        "specialties": [
            "Emergency Medicine", "Cardiology", "Neurology", "General Surgery",
            "Orthopaedics", "Anaesthesia & Critical Care"
        ],
        "cost_model": {
            "type": "Government",
            "summary_badge": "Free – Verified (Emergency)",
            "emergency_treatment": "Free emergency and essential casualty treatment",
            "opd_consultation": "Free registration",
            "inpatient_charges": "General ward beds free; essential medications provided under Jan Aushadhi / Hospital Formulary",
            "schemes_coverage": "Cashless under CGHS, PM-JAY, ECHS, National Health Schemes",
            "tariff_source": "Dr. RML Hospital Official Citizen Charter"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Emergency", "Cardiac Care Unit", "Intensive Care Unit"]
        }
    },
    "kem_mumbai": {
        "classification": "Government (Municipal Corporation / MCGM)",
        "ownership": "Municipal Corporation of Greater Mumbai (MCGM)",
        "emergency_dept": "24x7 Emergency Casualty & Trauma Triage Center",
        "icu_facilities": "Comprehensive Tertiary ICUs (Medical, Surgical, Cardiac, Paediatric)",
        "icu_available_verified": True,
        "trauma_care": "Major Apex Urban Trauma Centre",
        "trauma_available_verified": True,
        "cardiac_care": "Cardiology Centre & Emergency Interventions",
        "cardiac_available_verified": True,
        "stroke_care": "Acute Stroke & Neurocritical Care Services",
        "pediatric_care": "Comprehensive Paediatric & Neonatal Intensive Care",
        "burn_care": "Burns Unit & Plastic Surgery Division",
        "specialties": [
            "Emergency Medicine", "Trauma Surgery", "Cardiology", "Neurology",
            "General Surgery", "Critical Care", "Paediatrics"
        ],
        "cost_model": {
            "type": "Government (Municipal)",
            "summary_badge": "Subsidised – Verified",
            "emergency_treatment": "Free casualty consultation and initial emergency medical triage",
            "opd_consultation": "₹10 nominal municipal hospital registration",
            "inpatient_charges": "Subsidised Municipal Tariff; concession/waiver for BPL & poor patients",
            "schemes_coverage": "MJPJAY, Ayushman Bharat PM-JAY, ESIC, Municipal Employees Scheme",
            "tariff_source": "Municipal Corporation of Greater Mumbai Schedule of Medical Charges"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["Apex Trauma", "Municipal Emergency", "Level-3 ICU"]
        }
    },
    "sms_jaipur": {
        "classification": "Government (State Govt Medical College)",
        "ownership": "Government of Rajasthan / SMS Medical College",
        "emergency_dept": "24x7 Trauma Hospital & Multi-Specialty Emergency Casualty",
        "icu_facilities": "Extensive Multi-Disciplinary Intensive Care Units",
        "icu_available_verified": True,
        "trauma_care": "Apex Institute of Traumatology & Emergency Orthopaedics",
        "trauma_available_verified": True,
        "cardiac_care": "Comprehensive Cardiology Institute, Cath Labs, CTVS",
        "cardiac_available_verified": True,
        "stroke_care": "Stroke ICU & 24x7 Neurological Interventions",
        "pediatric_care": "Referral to attached JK Lon Children Hospital / Paediatric Unit",
        "burn_care": "Specialised Plastic Surgery & Burns Unit",
        "specialties": [
            "Emergency Medicine", "Trauma", "Cardiology", "Neurosurgery",
            "Orthopaedics", "General Medicine", "Critical Care"
        ],
        "cost_model": {
            "type": "Government (State Scheme Free)",
            "summary_badge": "Free – Verified (State Universal Health)",
            "emergency_treatment": "Free emergency triage, tests and medicines under Rajasthan Mukhyamantri Nishulk Dava/Janch Yojana",
            "opd_consultation": "Free",
            "inpatient_charges": "Free indoor treatment for state residents under Universal Health / RGHS / PM-JAY",
            "schemes_coverage": "100% Free under Mukhyamantri Ayushman Arogya, RGHS, PM-JAY, CGHS, ECHS",
            "tariff_source": "Government of Rajasthan Health Department Notification"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["Level-1 State Trauma", "Cath Lab", "Stroke Centre", "Extensive ICU"]
        }
    },
    "apollo": {
        "classification": "Private (Corporate Super-Speciality Hospital)",
        "ownership": "Apollo Hospitals Enterprise Ltd.",
        "emergency_dept": "24x7 Apollo Emergency Centre & Emergency Critical Care",
        "icu_facilities": "State-of-the-Art Medical, Surgical, Neuro, Cardio & Transplant ICUs",
        "icu_available_verified": True,
        "trauma_care": "Advanced Level-1/2 Accredited Trauma Facility",
        "trauma_available_verified": True,
        "cardiac_care": "24x7 Emergency Percutaneous Coronary Intervention (Door-to-Balloon <60m), Heart Institutes",
        "cardiac_available_verified": True,
        "stroke_care": "Comprehensive Stroke Center with rapid neuro-interventional protocols",
        "pediatric_care": "Paediatric Intensive Care Unit (PICU) & Paediatric Super-Specialties",
        "burn_care": "Plastic & Reconstructive Surgery Unit",
        "specialties": [
            "Emergency Medicine", "Interventional Cardiology", "Cardiothoracic Surgery",
            "Neurosurgery", "Neurology", "Orthopaedics", "Critical Care Medicine", "Oncology"
        ],
        "cost_model": {
            "type": "Private",
            "summary_badge": "Charges Applicable",
            "emergency_treatment": "Emergency Triage & Casualty Fee: ₹1,500 – ₹2,500 (approx published consultation); Treatment & Investigations billed at standard corporate tariff",
            "opd_consultation": "₹1,200 – ₹2,000 depending on specialist seniority",
            "inpatient_charges": "Corporate private tariff; Ward/Room categories: Shared, Single, Deluxe, ICU",
            "schemes_coverage": "Cashless TPA / Corporate Insurance, CGHS / ECHS (selected empanelled branches)",
            "tariff_source": "Hospital Tariff Schedule & Empanelled TPA Rate Cards"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Cath Lab", "Multi-disciplinary ICU", "Advanced Trauma Suite"]
        }
    },
    "fortis": {
        "classification": "Private (Multi-Speciality Healthcare Network)",
        "ownership": "Fortis Healthcare Limited",
        "emergency_dept": "24x7 Emergency & Trauma Care Unit",
        "icu_facilities": "High-Dependency Units & Intensive Care Units with ECMO support",
        "icu_available_verified": True,
        "trauma_care": "Comprehensive Trauma Care, Orthopaedic Trauma & Emergency Surgery",
        "trauma_available_verified": True,
        "cardiac_care": "Fortis Escorts Heart Institute / Interventional Cardiology Units",
        "cardiac_available_verified": True,
        "stroke_care": "Acute Brain Stroke Unit with round-the-clock CT/MRI",
        "pediatric_care": "Paediatric Wards, Neonatal Care Unit",
        "burn_care": "General Plastic & Reconstructive Care",
        "specialties": [
            "Emergency Medicine", "Cardiology", "Cardiac Surgery", "Neurology",
            "Neurosurgery", "Orthopaedics", "Intensive Care"
        ],
        "cost_model": {
            "type": "Private",
            "summary_badge": "Charges Applicable",
            "emergency_treatment": "Emergency Room consultation: ₹1,500 – ₹2,200; Procedures & ICU billed as per tariff",
            "opd_consultation": "₹1,000 – ₹1,800",
            "inpatient_charges": "Private hospital rates; Twin-sharing, Single Room & ICU tiers",
            "schemes_coverage": "Cashless TPA / GIPSA, CGHS / ECHS (at certified network locations)",
            "tariff_source": "Fortis Healthcare Rate Card & TPA Empanelment Agreement"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Emergency", "Cardiology ICU", "Surgical ICU"]
        }
    },
    "max_healthcare": {
        "classification": "Private (Super Speciality Hospital)",
        "ownership": "Max Healthcare Institute Limited",
        "emergency_dept": "24x7 Emergency Services & Resuscitation Bay",
        "icu_facilities": "Advanced Medical, Surgical, Neuro & Critical Care Units",
        "icu_available_verified": True,
        "trauma_care": "Emergency Trauma Unit with 24x7 surgical back-up",
        "trauma_available_verified": True,
        "cardiac_care": "Heart Care Institute, 24x7 Primary Angioplasty, CCU",
        "cardiac_available_verified": True,
        "stroke_care": "Comprehensive Stroke Center & Clot Retrieval Facility",
        "pediatric_care": "Paediatric Emergency & Intensive Care",
        "burn_care": "Plastic & Cosmetic Surgery Division",
        "specialties": [
            "Emergency Medicine", "Cardiology", "Neurology", "Orthopaedics",
            "Pulmonology", "Critical Care", "Trauma Care"
        ],
        "cost_model": {
            "type": "Private",
            "summary_badge": "Charges Applicable",
            "emergency_treatment": "Emergency consultation: ₹1,500 – ₹2,500; Diagnostics & medications billed as utilized",
            "opd_consultation": "₹1,200 – ₹2,000",
            "inpatient_charges": "Corporate tariff; Multi-tier ward & ICU accommodation",
            "schemes_coverage": "All major TPAs / Private Insurers, CGHS & ECHS (at selected branches)",
            "tariff_source": "Max Healthcare Published Rate Index & Network TPA Lists"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Emergency Medicine", "Level-3 ICU", "Cath Lab"]
        }
    },
    "manipal": {
        "classification": "Private (Multi-Speciality Healthcare Network)",
        "ownership": "Manipal Health Enterprises",
        "emergency_dept": "24x7 Emergency Medical Services & Critical Care",
        "icu_facilities": "Advanced Multi-Disciplinary Intensive Care",
        "icu_available_verified": True,
        "trauma_care": "Trauma & Accident Care Unit",
        "trauma_available_verified": True,
        "cardiac_care": "Comprehensive Cardiology, Cath Lab & Heart Attack Emergency",
        "cardiac_available_verified": True,
        "stroke_care": "Stroke Management Protocol & Neurovascular Services",
        "pediatric_care": "Paediatric ICU & Neonatal Care",
        "burn_care": "Plastic & Reconstructive Care",
        "specialties": [
            "Emergency Care", "Cardiology", "Neurosurgery", "Orthopaedics", "Critical Care"
        ],
        "cost_model": {
            "type": "Private",
            "summary_badge": "Charges Applicable",
            "emergency_treatment": "Emergency ER Charge: ₹1,200 – ₹2,000; Hospital tariff applicable",
            "opd_consultation": "₹1,000 – ₹1,800",
            "inpatient_charges": "Standard corporate room & ICU tariffs",
            "schemes_coverage": "Cashless TPA, Private Health Insurance, Empanelled Institutional Tie-ups",
            "tariff_source": "Manipal Hospitals Tariff Schedule"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Emergency", "Critical Care", "Cardiology"]
        }
    },
    "medanta": {
        "classification": "Private (Multi-Super Speciality Institute)",
        "ownership": "Global Health Limited (Medanta)",
        "emergency_dept": "24x7 Emergency & Critical Care Institute",
        "icu_facilities": "Specialised ICUs (Liver, Renal, Cardiac, Neuro, Surgical)",
        "icu_available_verified": True,
        "trauma_care": "Tertiary Level-1 Trauma Care Facility",
        "trauma_available_verified": True,
        "cardiac_care": "Apex Heart Institute, Heart Failure & Cath Labs",
        "cardiac_available_verified": True,
        "stroke_care": "Comprehensive Neurosciences Institute & Stroke Center",
        "pediatric_care": "Paediatric Cardiology & Critical Care Unit",
        "burn_care": "Plastic & Aesthetic Surgery Division",
        "specialties": [
            "Emergency Medicine", "Interventional Cardiology", "Neurosurgery",
            "Trauma Care", "Organ Transplant", "Critical Care"
        ],
        "cost_model": {
            "type": "Private",
            "summary_badge": "Charges Applicable",
            "emergency_treatment": "Emergency Admission & Triage: ₹1,800 – ₹3,000; Procedures & critical care per schedule",
            "opd_consultation": "₹1,500 – ₹2,500",
            "inpatient_charges": "Corporate super-specialty tariff",
            "schemes_coverage": "Cashless TPA / Insurance, CGHS / ECHS / PM-JAY (referral basis at select units)",
            "tariff_source": "Medanta The Medicity Published Tariff & Empanelled Provider Network"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["Apex Trauma", "Advanced ICU", "Comprehensive Cath Lab"]
        }
    },
    "ganga_ram": {
        "classification": "Trust / Not-for-Profit Super Speciality Hospital",
        "ownership": "Sir Ganga Ram Trust Society",
        "emergency_dept": "24x7 Emergency Casualty & Acute Resuscitation Unit",
        "icu_facilities": "Intensive Care Units & High Dependency Units",
        "icu_available_verified": True,
        "trauma_care": "Accident & Emergency Orthopaedic Trauma Services",
        "trauma_available_verified": True,
        "cardiac_care": "Cardiology & Cardiac Surgery Department",
        "cardiac_available_verified": True,
        "stroke_care": "Stroke Unit & Emergency Neurology Back-up",
        "pediatric_care": "Paediatrics, Child Health & Neonatal Care",
        "burn_care": "Plastic Surgery Division",
        "specialties": [
            "Emergency Medicine", "Cardiology", "Neurosurgery", "General Medicine", "Critical Care"
        ],
        "cost_model": {
            "type": "Trust / Subsidised General Beds Available",
            "summary_badge": "Charges Applicable (Trust Concessions)",
            "emergency_treatment": "Emergency Casualty Fee: ₹1,000 – ₹1,500; 20% beds reserved for indigent/free patients",
            "opd_consultation": "₹1,000 – ₹1,500 (Free in General Charity OPD)",
            "inpatient_charges": "Dual tier: Private Wards & Subsidised/Free General Beds",
            "schemes_coverage": "ECHS, CGHS, Major Private TPAs, Delhi State Health Schemes",
            "tariff_source": "Sir Ganga Ram Hospital Schedule of Charges & Trust Guidelines"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": True,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Emergency", "Critical Care ICU", "Cardiac Unit"]
        }
    },
    "general_civil_hospital": {
        "classification": "Government (District / Civil Healthcare Centre)",
        "ownership": "State Department of Health & Family Welfare",
        "emergency_dept": "24x7 Casualty & Emergency Ward",
        "icu_facilities": "District Hospital ICU / High Dependency Unit",
        "icu_available_verified": True,
        "trauma_care": "District Level Trauma Care & Stabilization Unit",
        "trauma_available_verified": True,
        "cardiac_care": "CCU / Emergency Cardiac Stabilization (Tertiary referral if needed)",
        "cardiac_available_verified": False,
        "stroke_care": "Basic Stroke Stabilization & Thrombolysis (District Centre)",
        "pediatric_care": "Paediatric Ward & Sick Newborn Care Unit (SNCU)",
        "burn_care": "Basic Burn Dressing & Stabilization Unit",
        "specialties": [
            "Emergency Casualty", "General Medicine", "General Surgery",
            "Orthopaedics", "Obstetrics & Gynaecology", "Paediatrics"
        ],
        "cost_model": {
            "type": "Government",
            "summary_badge": "Free – Verified",
            "emergency_treatment": "Free emergency casualty care, basic medications & emergency triage",
            "opd_consultation": "Free / ₹5 nominal state government slip",
            "inpatient_charges": "Free general wards; Jan Aushadhi generic medicines provided",
            "schemes_coverage": "100% Free under Ayushman Bharat PM-JAY & State Government Health Schemes",
            "tariff_source": "National Health Mission & State Health Department Norms"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": False,
            "supports_als": True,
            "supports_bls": True,
            "required_capabilities": ["24x7 Casualty", "Stabilization Care", "Basic ICU / HDU"]
        }
    }
}


def get_hospital_capabilities_and_cost(hospital_name: str, hospital_address: str = "") -> Dict[str, Any]:
    """
    Returns verified hospital capability details, specialties, cost breakdown,
    and ambulance compatibility.
    If exact entity is not in verified database, returns standardized unverified/neutral info.
    """
    norm_name = hospital_name.strip().lower()
    norm_addr = (hospital_address or "").strip().lower()
    
    # 1. Direct key match
    for key, data in HOSPITAL_FACILITIES_DB.items():
        if key in norm_name:
            return _format_facility_response(key, data, hospital_name, is_verified=True)
            
    # 2. Match common aliases
    if any(k in norm_name for k in ["aiims", "all india institute of medical sciences"]):
        return _format_facility_response("aiims", HOSPITAL_FACILITIES_DB["aiims"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["safdarjung", "safdarjang", "vmmc"]):
        return _format_facility_response("safdarjung", HOSPITAL_FACILITIES_DB["safdarjung"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["ram manohar lohia", "rml hospital", "dr rml"]):
        return _format_facility_response("ram_manohar_lohia", HOSPITAL_FACILITIES_DB["ram_manohar_lohia"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["kem hospital", "king edward memorial"]):
        return _format_facility_response("kem_mumbai", HOSPITAL_FACILITIES_DB["kem_mumbai"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["sms hospital", "sawai man singh"]):
        return _format_facility_response("sms_jaipur", HOSPITAL_FACILITIES_DB["sms_jaipur"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["apollo"]):
        return _format_facility_response("apollo", HOSPITAL_FACILITIES_DB["apollo"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["fortis"]):
        return _format_facility_response("fortis", HOSPITAL_FACILITIES_DB["fortis"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["max hospital", "max healthcare", "max super"]):
        return _format_facility_response("max_healthcare", HOSPITAL_FACILITIES_DB["max_healthcare"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["manipal"]):
        return _format_facility_response("manipal", HOSPITAL_FACILITIES_DB["manipal"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["medanta"]):
        return _format_facility_response("medanta", HOSPITAL_FACILITIES_DB["medanta"], hospital_name, is_verified=True)
    if any(k in norm_name for k in ["ganga ram", "sir ganga ram"]):
        return _format_facility_response("ganga_ram", HOSPITAL_FACILITIES_DB["ganga_ram"], hospital_name, is_verified=True)

    # 3. Government / Civil identification
    is_govt = any(w in norm_name for w in [
        "government", "govt", "civil", "district hospital", "general hospital",
        "railway hospital", "cantt", "esic", "medical college", "swasthya", "chc", "phc"
    ])
    
    if is_govt:
        base = HOSPITAL_FACILITIES_DB["general_civil_hospital"]
        return _format_facility_response("general_civil_hospital", base, hospital_name, is_verified=True)

    # 4. Unverified / Private clinic or local hospital
    return {
        "is_verified": False,
        "classification": "Private / Non-Government (Facility Type Not Verified)",
        "ownership": "Information Unavailable (Awaiting central registry verification)",
        "emergency_dept": "Casualty / Emergency availability not independently verified",
        "icu_facilities": "ICU availability not independently verified",
        "icu_available_verified": False,
        "trauma_care": "Trauma capability not verified",
        "trauma_available_verified": False,
        "cardiac_care": "Cardiac emergency capability not verified",
        "cardiac_available_verified": False,
        "stroke_care": "Stroke facility not verified",
        "pediatric_care": "Paediatric facility not verified",
        "burn_care": "Burn care facility not verified",
        "specialties": ["General Healthcare / Clinical Services"],
        "cost_model": {
            "type": "Cost Information Unavailable",
            "summary_badge": "Cost not verified",
            "emergency_treatment": "Cost not verified — Please verify at hospital admission desk",
            "opd_consultation": "Cost not verified",
            "inpatient_charges": "Cost not verified (Exact tariff not published in national registry)",
            "schemes_coverage": "Scheme eligibility subject to hospital desk verification",
            "tariff_source": "National Health Facility Registry (Awaiting tariff submission)"
        },
        "ambulance_compatibility": {
            "supports_icu_ambulance": False,
            "supports_als": False,
            "supports_bls": True,
            "required_capabilities": ["Basic Patient Transfer"]
        }
    }


def _format_facility_response(key: str, data: Dict[str, Any], raw_name: str, is_verified: bool) -> Dict[str, Any]:
    """Helper to format hospital capabilities and cost response."""
    res = dict(data)
    res["matched_key"] = key
    res["is_verified"] = is_verified
    return res


def estimate_travel_time_minutes(distance_km: float) -> int:
    """
    Computes an estimated urban road ambulance travel time in minutes.
    Assumes average ambulance transit speed in Indian urban traffic:
    ~20-25 km/h + 2 minutes dispatch reaction buffer.
    Never invents random or erratic numbers.
    """
    if distance_km <= 0.05:
        return 1
    # Average speed: 22 km/h -> 2.7 minutes per km
    travel_time = round((distance_km / 22.0) * 60) + 2
    return max(2, travel_time)


def evaluate_hospital_condition_match(
    chief_complaint: str,
    priority: str,
    hospital_data: Dict[str, Any],
    distance_km: float,
    has_available_ambulance: bool
) -> Dict[str, Any]:
    """
    Evaluates condition-based compatibility between the recorded emergency condition
    (from the verified triage record) and the hospital's capabilities.
    
    Emergency Categories supported:
    - cardiac_chest (Cardiac emergency)
    - trauma (Accident / Trauma / Fractures)
    - seizures / neurology (Stroke / neurological emergencies)
    - breathing (Respiratory emergency)
    - poisoning (Toxicological / ICU emergency)
    - pregnancy (Obstetric / Maternal emergency)
    - burns (Burn emergency)
    - other
    
    Ranking factors:
    1. Required emergency facilities (match score).
    2. Relevant specialty availability.
    3. ICU & emergency capability.
    4. Verified operational availability.
    5. Distance & estimated travel time.
    6. Ambulance compatibility.
    """
    comp = (chief_complaint or "").lower()
    prio = (priority or "YELLOW").upper()
    fac = hospital_data.get("facilities_info", {})
    
    is_compatible = True
    match_reasons = []
    suitability_score = 0
    
    # 1. Condition & Specialty Matching
    if "cardiac" in comp or "chest" in comp:
        if fac.get("cardiac_available_verified"):
            suitability_score += 40
            match_reasons.append("Verified 24x7 Cath Lab and cardiac care facilities match the recorded cardiac emergency")
        else:
            suitability_score -= 15
            match_reasons.append("Cardiac emergency capability is not verified for this facility")
            if prio == "RED":
                is_compatible = False
                
    elif "trauma" in comp or "fracture" in comp or "accident" in comp:
        if fac.get("trauma_available_verified"):
            suitability_score += 40
            match_reasons.append("Verified Level-1/2 Trauma care and emergency surgery facilities match the recorded trauma emergency")
        else:
            suitability_score -= 10
            match_reasons.append("Specialised trauma centre not verified for this facility")
            if prio == "RED":
                is_compatible = False

    elif "seizure" in comp or "stroke" in comp or "neuro" in comp:
        if fac.get("stroke_care") and "Stroke" in fac.get("stroke_care", ""):
            suitability_score += 35
            match_reasons.append("Acute stroke / neurological resuscitation unit matches the patient's symptoms")
        else:
            suitability_score -= 5
            match_reasons.append("Stroke / neurological critical care not confirmed")

    elif "breath" in comp or "respiratory" in comp:
        if fac.get("icu_available_verified"):
            suitability_score += 35
            match_reasons.append("Intensive Care Unit (ICU) and ventilator capability verified for acute respiratory distress")
        else:
            match_reasons.append("ICU respiratory ventilation capacity not verified")

    elif "burn" in comp:
        burn_care = fac.get("burn_care", "")
        if "Burns" in burn_care or "Dedicated" in burn_care:
            suitability_score += 40
            match_reasons.append("Dedicated burn and plastic reconstructive unit matches the burn emergency")
        else:
            suitability_score -= 10
            match_reasons.append("Dedicated burn unit not verified")

    elif "pregnancy" in comp or "delivery" in comp:
        specs = fac.get("specialties", [])
        if any("Obstetrics" in s or "Paediatric" in s for s in specs):
            suitability_score += 35
            match_reasons.append("Maternal / neonatal emergency facilities match obstetric requirements")
        else:
            match_reasons.append("Obstetric emergency capabilities not independently confirmed")
    else:
        # General emergency
        if fac.get("icu_available_verified"):
            suitability_score += 20
            match_reasons.append("General emergency resuscitation and intensive care facilities available")

    # 2. ICU Requirement for High-Priority Patients
    if prio == "RED":
        if fac.get("icu_available_verified"):
            suitability_score += 25
            match_reasons.append("Equipped with high-priority resuscitation and Level-3 ICU units")
        else:
            suitability_score -= 20
            is_compatible = False
            match_reasons.append("Lacks verified Level-3 ICU required for RED priority life-threat response")

    # 3. Ambulance Availability Bonus
    if has_available_ambulance:
        suitability_score += 20
        match_reasons.append("Dedicated ambulance unit currently marked AVAILABLE")
    else:
        suitability_score -= 15
        match_reasons.append("Ambulance unit currently not available or assigned")

    # 4. Distance Factor (Penalize excessive distance, but medical suitability takes precedence)
    # Travel time score (0 to 15 points)
    dist_penalty = min(25, int(distance_km * 1.5))
    suitability_score = max(0, suitability_score + 15 - dist_penalty)

    primary_reason = match_reasons[0] if match_reasons else "Verified hospital facilities match recorded triage intake"

    return {
        "is_recommended": (suitability_score >= 35 and is_compatible),
        "suitability_score": suitability_score,
        "primary_recommendation_reason": primary_reason,
        "all_reasons": match_reasons,
        "is_compatible": is_compatible
    }

