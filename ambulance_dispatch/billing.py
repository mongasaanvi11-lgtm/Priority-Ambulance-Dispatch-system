from dataclasses import dataclass
from typing import Dict, Any
from .constants import TriageLevel

BASE_CALLOUT_FEE = 50.0  # Base dispatch fee ($)
RATE_PER_KM = 3.50       # Mileage charge per km

TIER_MULTIPLIERS = {
    TriageLevel.GREEN.value: {"name": "Basic Life Support (BLS)", "fee": 75.0, "icon": "🟢"},
    TriageLevel.YELLOW.value: {"name": "Advanced Life Support (ALS)", "fee": 150.0, "icon": "🟡"},
    TriageLevel.RED.value: {"name": "Critical Care Transport (CCT)", "fee": 300.0, "icon": "🔴"},
}

def calculate_ambulance_bill(
    triage_level: str,
    distance_km: float,
    night_shift: bool = False,
    oxygen_administered: bool = False,
    ecg_monitoring: bool = False,
) -> Dict[str, Any]:
    tier = TIER_MULTIPLIERS.get(triage_level, TIER_MULTIPLIERS[TriageLevel.GREEN.value])
    tier_fee = tier["fee"]
    mileage_cost = round(distance_km * RATE_PER_KM, 2)
    
    addons = 0.0
    itemized = [
        {"item": "Base Response / Dispatch Fee", "cost": BASE_CALLOUT_FEE},
        {"item": f"Care Level: {tier['name']}", "cost": tier_fee},
        {"item": f"Mileage ({distance_km:.1f} km @ ${RATE_PER_KM}/km)", "cost": mileage_cost},
    ]

    if oxygen_administered:
        itemized.append({"item": "Medical Oxygen Delivery", "cost": 45.0})
        addons += 45.0
    if ecg_monitoring:
        itemized.append({"item": "12-Lead ECG Telemetry", "cost": 65.0})
        addons += 65.0
    if night_shift:
        surge = round((BASE_CALLOUT_FEE + tier_fee) * 0.15, 2)
        itemized.append({"item": "After-Hours Emergency Surcharge (15%)", "cost": surge})
        addons += surge

    subtotal = BASE_CALLOUT_FEE + tier_fee + mileage_cost + addons
    tax = round(subtotal * 0.05, 2)  # 5% healthcare surcharge/tax
    total = round(subtotal + tax, 2)

    return {
        "tier_name": tier["name"],
        "itemized": itemized,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }