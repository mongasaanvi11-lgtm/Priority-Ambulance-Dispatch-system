"""
Fictional demonstration data loader for ResQTrack.
Provides idempotent insertion of simulated emergency calls.
NEVER overwrites or deletes existing records.
"""

from typing import Optional

from .constants import IncidentStatus, TriageLevel
from .database import create_incident, get_db_connection


def load_demo_incidents(db_path: Optional[str] = None) -> int:
    """
    Idempotently load 3 fictional demo incidents (1 RED, 1 YELLOW, 1 GREEN).
    Will NOT create duplicate demo incidents if demo cases already exist.
    Never wipes existing data.
    Returns the count of newly inserted incidents.
    """
    conn = get_db_connection(db_path)
    try:
        # Check if demo incidents already exist
        cursor = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE patient_name LIKE 'Demo Case:%';"
        )
        count = cursor.fetchone()[0]
        if count > 0:
            return 0
    finally:
        conn.close()

    demo_incidents = [
        # RED: Critical cardiac symptoms
        {
            "patient_name": "Demo Case: Alex Mercer (Simulated Cardiac)",
            "age": 62,
            "gender": "Male",
            "contact": "555-0101",
            "location_text": "City Center Plaza, Metro City",
            "latitude": 12.9735,
            "longitude": 77.5970,
            "heart_rate": 138,
            "systolic_bp": 175,
            "diastolic_bp": 105,
            "spo2": 88.0,
            "temperature_f": 98.6,
            "symptoms": ["Chest pain", "Shortness of breath"],
            "primary_symptom": "Severe crushing chest pain",
            "pain_level": 9,
            "triage_level": TriageLevel.RED.value,
            "p_red": 1.0,
            "p_yellow": 0.0,
            "p_green": 0.0,
            "demo_priority_score": 168.0,
            "status": IncidentStatus.PENDING.value,
        },
        # YELLOW: Moderate urgent case
        {
            "patient_name": "Demo Case: Jamie Lin (Simulated Fracture)",
            "age": 29,
            "gender": "Female",
            "contact": "555-0102",
            "location_text": "North Park Sports Complex, Metro City",
            "latitude": 12.9810,
            "longitude": 77.6050,
            "heart_rate": 104,
            "systolic_bp": 138,
            "diastolic_bp": 88,
            "spo2": 95.0,
            "temperature_f": 99.1,
            "symptoms": ["Fracture / Suspected broken bone", "Severe abdominal pain"],
            "primary_symptom": "Suspected arm fracture after fall",
            "pain_level": 6,
            "triage_level": TriageLevel.YELLOW.value,
            "p_red": 0.15,
            "p_yellow": 0.70,
            "p_green": 0.15,
            "demo_priority_score": 79.5,
            "status": IncidentStatus.PENDING.value,
        },
        # GREEN: Mild non-urgent case
        {
            "patient_name": "Demo Case: Sam Morales (Simulated Minor Cut)",
            "age": 21,
            "gender": "Other",
            "contact": "555-0103",
            "location_text": "East Community College, Metro City",
            "latitude": 12.9680,
            "longitude": 77.5890,
            "heart_rate": 74,
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "spo2": 99.0,
            "temperature_f": 98.4,
            "symptoms": ["Minor cut / abrasion"],
            "primary_symptom": "Superficial finger cut",
            "pain_level": 2,
            "triage_level": TriageLevel.GREEN.value,
            "p_red": 0.05,
            "p_yellow": 0.15,
            "p_green": 0.80,
            "demo_priority_score": 18.75,
            "status": IncidentStatus.PENDING.value,
        },
    ]

    inserted = 0
    for inc in demo_incidents:
        create_incident(inc, db_path=db_path)
        inserted += 1

    return inserted
