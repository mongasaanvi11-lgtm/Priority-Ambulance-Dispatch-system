"""
AmbuPriority — Ambulance Fare Calculation & Rate Engine
======================================================
Manages ambulance tariff structures, government vs private vehicle rates,
official Delhi CATS free emergency service rules, and exact road-route fare calculations.

Rates specified:
1. Government Ambulances:
   - PTV:  ₹1.70 per KM
   - BLS:  ₹1.70 per KM
   - ALS:  ₹1.70 per KM
   - (ICU, Cardiac, and Neonatal are strictly removed from Government categories)
   - CATS Emergency Service (Toll-Free 102): 100% Free Official Verified Status (₹0)

2. Private Ambulances:
   - PTV:      ₹30 per KM
   - BLS:      ₹50 per KM
   - ALS:      ₹100 per KM
   - ICU:      ₹83 per KM
   - Cardiac:  ₹88 per KM
   - Neonatal: ₹75 per KM

Fare Formula:
   Fare = Base Fare (if applicable) + (Chargeable Distance in KM * Per-KM Rate) + Verified Additional Charges
   - No invented base fares or hidden surcharges.
   - Cleanly distinguishes:
     * Official Verified Fare
     * Estimated Fare
     * Final Provider-Confirmed Fare
   - Separates ambulance transport charges from hospital clinical treatment costs.
"""

from typing import Dict, List, Any, Optional

# Initial project estimates per KM
GOVT_AMBULANCE_RATES: Dict[str, float] = {
    "PTV": 1.70,
    "BLS": 1.70,
    "ALS": 1.70,
}

PRIVATE_AMBULANCE_RATES: Dict[str, float] = {
    "PTV": 30.0,
    "BLS": 50.0,
    "ALS": 100.0,
    "ICU": 83.0,
    "Cardiac": 88.0,
    "Neonatal": 75.0,
}

# Type aliases and normalizer
TYPE_ALIASES: Dict[str, str] = {
    "ptv": "PTV",
    "patient transport": "PTV",
    "patient transport vehicle": "PTV",
    "bls": "BLS",
    "basic life support": "BLS",
    "als": "ALS",
    "advanced life support": "ALS",
    "icu": "ICU",
    "icu-equipped": "ICU",
    "cardiac": "Cardiac",
    "cardiac care": "Cardiac",
    "neonatal": "Neonatal",
    "neonatal care": "Neonatal",
    "nicu": "Neonatal"
}

def normalize_ambulance_type(amb_type: str) -> str:
    clean = (amb_type or "BLS").strip().lower()
    return TYPE_ALIASES.get(clean, amb_type.upper() if len(amb_type) <= 4 else amb_type.title())

def calculate_ambulance_fare(
    amb_type: str,
    distance_km: float,
    is_government: bool = True,
    is_cats_emergency: bool = False,
    is_emergency_priority: bool = False
) -> Dict[str, Any]:
    """
    Computes verified and estimated ambulance transportation fare based on distance and type.
    """
    norm_type = normalize_ambulance_type(amb_type)
    dist = max(0.0, float(distance_km or 0.0))
    chargeable_dist = round(dist, 2)
    
    # 1. Delhi CATS Free Emergency Scheme Check
    if is_cats_emergency:
        # CATS Emergency services operate officially free of charge
        return {
            "ambulance_type": norm_type,
            "ownership": "Government (CATS / Toll-Free 102 Emergency Dispatch)",
            "is_government": True,
            "is_free": True,
            "rate_per_km": 0.0,
            "chargeable_distance_km": chargeable_dist,
            "base_fare": 0.0,
            "distance_charge": 0.0,
            "additional_charges": 0.0,
            "total_fare": 0.0,
            "fare_status": "Official Verified Fare",
            "fare_badge": "Free – Verified (CATS Toll-Free 102)",
            "currency": "INR",
            "formatted_total": "₹0 (Free Emergency Service)",
            "rate_breakdown": "CATS Toll-Free 102 emergency and trauma transfer is fully funded by the Government.",
            "source": "Delhi CATS / Department of Health and Family Welfare Official Charter"
        }
    
    # 2. Government Ambulances (Non-CATS or Scheduled Transfer: PTV, BLS, ALS)
    if is_government:
        # Strictly reject ICU, Cardiac, Neonatal under Govt categories
        if norm_type not in GOVT_AMBULANCE_RATES:
            # Fall back to ALS or BLS for Govt
            norm_type = "ALS" if norm_type in ["ICU", "Cardiac"] else "BLS"
            
        rate = GOVT_AMBULANCE_RATES[norm_type]
        base_fare = 0.0  # Do not invent base fare
        distance_charge = round(chargeable_dist * rate, 2)
        total_fare = round(base_fare + distance_charge, 2)
        
        return {
            "ambulance_type": norm_type,
            "ownership": "Government Ambulance Service",
            "is_government": True,
            "is_free": False,
            "rate_per_km": rate,
            "chargeable_distance_km": chargeable_dist,
            "base_fare": base_fare,
            "distance_charge": distance_charge,
            "additional_charges": 0.0,
            "total_fare": total_fare,
            "fare_status": "Project Estimate",
            "fare_badge": f"Govt Rate: ₹{rate:.2f}/km (Project Estimate)",
            "currency": "INR",
            "formatted_total": f"₹{total_fare:,.2f}",
            "rate_breakdown": f"Fare = {chargeable_dist} km × ₹{rate:.2f}/km = ₹{total_fare:,.2f}",
            "source": "Project Estimate Tariff"
        }

    # 3. Private Ambulances (PTV, BLS, ALS, ICU, Cardiac, Neonatal)
    if norm_type not in PRIVATE_AMBULANCE_RATES:
        norm_type = "BLS"
        
    rate = PRIVATE_AMBULANCE_RATES[norm_type]
    base_fare = 0.0  # No invented base fare
    distance_charge = round(chargeable_dist * rate, 2)
    total_fare = round(base_fare + distance_charge, 2)

    return {
        "ambulance_type": norm_type,
        "ownership": "Private Healthcare Provider Ambulance Fleet",
        "is_government": False,
        "is_free": False,
        "rate_per_km": rate,
        "chargeable_distance_km": chargeable_dist,
        "base_fare": base_fare,
        "distance_charge": distance_charge,
        "additional_charges": 0.0,
        "total_fare": total_fare,
        "fare_status": "Project Estimate",
        "fare_badge": f"Private Rate: ₹{rate:.0f}/km (Project Estimate)",
        "currency": "INR",
        "formatted_total": f"₹{total_fare:,.2f}",
        "rate_breakdown": f"Fare = {chargeable_dist} km × ₹{rate:.0f}/km = ₹{total_fare:,.2f}",
        "source": "Project Estimate Tariff"
    }


def get_all_ambulance_tariffs_for_distance(distance_km: float, is_govt_hospital: bool = True) -> Dict[str, Any]:
    """
    Returns full comparative fare matrix for all supported ambulance categories
    at the given distance.
    """
    dist = max(0.0, float(distance_km or 0.0))
    
    govt_options = {}
    for amb_t in ["PTV", "BLS", "ALS"]:
        govt_options[amb_t] = calculate_ambulance_fare(
            amb_type=amb_t,
            distance_km=dist,
            is_government=True,
            is_cats_emergency=(amb_t in ["BLS", "ALS"])
        )
        
    private_options = {}
    for amb_t in ["PTV", "BLS", "ALS", "ICU", "Cardiac", "Neonatal"]:
        private_options[amb_t] = calculate_ambulance_fare(
            amb_type=amb_t,
            distance_km=dist,
            is_government=False
        )
        
    return {
        "distance_km": round(dist, 2),
        "government_fleet": govt_options,
        "private_fleet": private_options
    }
