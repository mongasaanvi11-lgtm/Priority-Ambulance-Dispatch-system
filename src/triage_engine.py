"""
AmbuPriority — Clinical Triage Decision Engine
================================================
Pre-hospital telephone triage assessment module.

Sources:
  - WHO Interagency Integrated Triage Tool (IITT), 2020
  - AIIMS Triage Protocol (ATP), PMC7472824
  - GVK EMRI 108 Pre-Hospital Assessment Criteria
  - START Triage (RPM: Respiration, Perfusion, Mental Status)
  - MoHFW Provider Course Manual for Paramedics, Chapter 5

IMPORTANT: This module implements documented, published triage criteria.
It has NOT been clinically validated for operational ambulance dispatch.
All results requiring operational use MUST be reviewed by qualified
clinical professionals before deployment.

Priority Levels:
  RED            — Immediate life threat; highest dispatch priority
  YELLOW         — Urgent; requires timely response
  GREEN          — Non-urgent; can safely wait
  REVIEW_REQUIRED — Insufficient data or no validated rule; needs clinical review
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Rule-set version — increment when clinical rules change
RULESET_VERSION = "1.0.0-draft"
RULESET_SOURCES = [
    "WHO-IITT-2020",
    "AIIMS-ATP-PMC7472824",
    "GVK-EMRI-108-Dispatch",
    "START-Triage-RPM",
    "MoHFW-Paramedic-Manual-Ch5"
]

# ──────────────────────────────────────────────────────
# PRIORITY CONSTANTS
# ──────────────────────────────────────────────────────
RED = "RED"
YELLOW = "YELLOW"
GREEN = "GREEN"
REVIEW = "REVIEW_REQUIRED"


# ──────────────────────────────────────────────────────
# UNIVERSAL RED CRITERIA (WHO IITT + AIIMS ATP)
# These apply regardless of chief complaint.
# ──────────────────────────────────────────────────────
def evaluate_universal_red(assessment: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """
    Check universal emergency signs that indicate RED priority
    regardless of the chief complaint category.
    
    Source: WHO IITT Section 1 (Emergency Signs), AIIMS ATP
    """
    reasons = []
    clinical = assessment.get("clinical_assessment", {})
    
    # 1. Consciousness: Unresponsive or altered → RED
    # Source: WHO IITT Red Criterion; START Triage Mental Status
    consciousness = clinical.get("consciousness")
    if consciousness == "unresponsive":
        reasons.append("RED: Patient unresponsive [WHO-IITT, START]")
    elif consciousness == "responds_to_pain":
        reasons.append("RED: Patient responds only to pain [WHO-IITT, AVPU-P]")
    
    # 2. Active convulsions → RED
    # Source: WHO IITT Red Criterion
    if clinical.get("active_convulsions") == "yes":
        reasons.append("RED: Active convulsions/seizures [WHO-IITT]")
    
    # 3. Airway obstruction or stridor → RED
    # Source: WHO IITT Red Criterion
    airway = clinical.get("airway_status")
    if airway == "obstructed":
        reasons.append("RED: Airway obstruction [WHO-IITT, AIIMS-ATP]")
    elif airway == "stridor":
        reasons.append("RED: Stridor present [WHO-IITT]")
    
    # 4. Severe respiratory distress or cyanosis → RED
    # Source: WHO IITT Red Criterion, AIIMS ATP
    breathing = clinical.get("breathing_status")
    if breathing == "severe_distress":
        reasons.append("RED: Severe respiratory distress [WHO-IITT, AIIMS-ATP]")
    elif breathing == "not_breathing":
        reasons.append("RED: Patient not breathing [WHO-IITT, START]")
    if clinical.get("cyanosis") == "yes":
        reasons.append("RED: Central cyanosis (blue lips/tongue) [WHO-IITT]")
    
    # 5. Heavy/uncontrolled bleeding → RED
    # Source: WHO IITT Red Criterion, GVK EMRI
    bleeding = clinical.get("bleeding_severity")
    if bleeding == "heavy_uncontrolled":
        reasons.append("RED: Heavy uncontrolled bleeding [WHO-IITT, GVK-EMRI]")
    
    # 6. Shock signs: cold extremities + weak rapid pulse → RED
    # Source: WHO IITT Red Criterion
    if clinical.get("cold_extremities") == "yes" and clinical.get("weak_rapid_pulse") == "yes":
        reasons.append("RED: Signs of shock (cold extremities + weak rapid pulse) [WHO-IITT]")
    
    if reasons:
        return RED, reasons
    return None, []


# ──────────────────────────────────────────────────────
# UNIVERSAL YELLOW CRITERIA (WHO IITT)
# ──────────────────────────────────────────────────────
def evaluate_universal_yellow(assessment: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """
    Check universal priority signs that indicate YELLOW priority.
    Source: WHO IITT Section 2 (Priority Signs)
    """
    reasons = []
    clinical = assessment.get("clinical_assessment", {})
    
    # Altered consciousness (responds to voice only) → YELLOW
    consciousness = clinical.get("consciousness")
    if consciousness == "responds_to_voice":
        reasons.append("YELLOW: Altered consciousness — responds to voice only [WHO-IITT, AVPU-V]")
    
    # Severe pain → YELLOW
    # Source: WHO IITT Yellow Criterion
    if clinical.get("severe_pain") == "yes":
        reasons.append("YELLOW: Severe pain reported [WHO-IITT]")
    
    # Unable to eat/drink or vomiting everything → YELLOW
    # Source: WHO IITT Yellow Criterion
    if clinical.get("unable_to_eat_drink") == "yes":
        reasons.append("YELLOW: Unable to eat or drink / vomiting everything [WHO-IITT]")
    
    # Acute visual disturbance → YELLOW
    if clinical.get("acute_visual_disturbance") == "yes":
        reasons.append("YELLOW: Acute visual disturbance [WHO-IITT]")
    
    # Severe pallor → YELLOW
    if clinical.get("severe_pallor") == "yes":
        reasons.append("YELLOW: Severe pallor [WHO-IITT]")
    
    if reasons:
        return YELLOW, reasons
    return None, []


# ──────────────────────────────────────────────────────
# COMPLAINT-SPECIFIC RULES
# ──────────────────────────────────────────────────────

def evaluate_cardiac_chest(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Cardiac / Chest Pain assessment.
    Source: GVK EMRI Dispatch, WHO IITT (acute chest pain >50y → RED)
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    patient_age = assessment.get("patient_age", 0)
    
    # Acute chest pain in adult ≥50 → RED (WHO IITT)
    if patient_age and int(patient_age) >= 50:
        reasons.append("RED: Acute chest pain in adult ≥50 years [WHO-IITT]")
        return RED, reasons
    
    # Crushing/pressure chest pain + radiating to arm/jaw → RED
    # Source: GVK EMRI suspected ACS criteria
    pain_type = complaint.get("chest_pain_type")
    if pain_type in ("crushing", "pressure", "tightness"):
        if complaint.get("pain_radiating") == "yes":
            reasons.append("RED: Crushing/pressure chest pain radiating to arm/jaw [GVK-EMRI ACS criteria]")
            return RED, reasons
        reasons.append("YELLOW: Crushing/pressure chest pain [GVK-EMRI]")
    
    # Associated shortness of breath → upgrades to RED
    if complaint.get("associated_breathlessness") == "yes":
        reasons.append("RED: Chest pain with shortness of breath [GVK-EMRI]")
        return RED, reasons
    
    # Associated sweating/nausea → YELLOW
    if complaint.get("associated_sweating") == "yes" or complaint.get("associated_nausea") == "yes":
        reasons.append("YELLOW: Chest pain with sweating/nausea [GVK-EMRI]")
        return YELLOW, reasons
    
    if reasons:
        return YELLOW, reasons
    return REVIEW, ["REVIEW: Chest pain without validated pre-hospital severity criteria match"]


def evaluate_breathing(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Breathing difficulty assessment.
    Source: WHO IITT, GVK EMRI
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # Choking / airway obstruction → RED
    if complaint.get("choking") == "yes":
        reasons.append("RED: Choking / airway obstruction [GVK-EMRI, WHO-IITT]")
        return RED, reasons
    
    # Wheezing present
    if complaint.get("wheezing") == "yes":
        # With severe distress → already caught by universal RED
        # Without severe distress → YELLOW (WHO IITT)
        reasons.append("YELLOW: Wheezing present [WHO-IITT]")
    
    # Swelling of mouth/throat/neck → YELLOW
    if complaint.get("throat_swelling") == "yes":
        reasons.append("YELLOW: Swelling of mouth/throat/neck [WHO-IITT]")
    
    # Worsening over time
    if complaint.get("worsening") == "yes":
        reasons.append("YELLOW: Breathing difficulty worsening [clinical concern]")
    
    if reasons:
        highest = RED if any("RED:" in r for r in reasons) else YELLOW
        return highest, reasons
    return REVIEW, ["REVIEW: Breathing difficulty without specific severity indicators"]


def evaluate_neurological(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Neurological assessment (stroke, altered consciousness).
    Source: GVK EMRI FAST criteria, WHO IITT, AIIMS ATP
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # FAST stroke criteria: any positive → RED
    # Source: GVK EMRI stroke dispatch
    fast_positive = False
    if complaint.get("facial_drooping") == "yes":
        reasons.append("RED: Facial drooping (FAST-F positive) [GVK-EMRI]")
        fast_positive = True
    if complaint.get("arm_weakness") == "yes":
        reasons.append("RED: Arm weakness (FAST-A positive) [GVK-EMRI]")
        fast_positive = True
    if complaint.get("speech_difficulty") == "yes":
        reasons.append("RED: Speech difficulty (FAST-S positive) [GVK-EMRI]")
        fast_positive = True
    
    if fast_positive:
        reasons.append("RED: Suspected stroke — FAST criteria positive [GVK-EMRI, AIIMS-ATP]")
        return RED, reasons
    
    # Acute onset neurological deficit → RED
    if complaint.get("sudden_onset") == "yes" and complaint.get("neurological_deficit") == "yes":
        reasons.append("RED: Acute-onset neurological deficit [GVK-EMRI]")
        return RED, reasons
    
    # Focal weakness/numbness without other red signs → YELLOW
    if complaint.get("focal_weakness") == "yes":
        reasons.append("YELLOW: Focal neurological complaint [WHO-IITT]")
        return YELLOW, reasons
    
    # Severe headache with stiff neck → YELLOW (meningism concern)
    if complaint.get("severe_headache") == "yes" and complaint.get("stiff_neck") == "yes":
        reasons.append("YELLOW: Severe headache with stiff neck [WHO-IITT meningism]")
        return YELLOW, reasons
    
    # All FAST stroke indicators and acute red flags negative & alert → GREEN (Non-urgent)
    if (complaint.get("facial_drooping") == "no" and 
        complaint.get("arm_weakness") == "no" and 
        complaint.get("speech_difficulty") == "no" and 
        complaint.get("severe_headache") == "no"):
        reasons.append("GREEN: Neurological query without acute stroke or intracranial red flags [WHO-IITT]")
        return GREEN, reasons

    return REVIEW, ["REVIEW: Neurological complaint without validated pre-hospital criteria match"]


def evaluate_trauma(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Road accident / trauma assessment.
    Source: WHO IITT (high-risk trauma), GVK EMRI, START
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # High-risk trauma mechanism → RED
    # Source: WHO IITT, GVK EMRI
    mechanism = complaint.get("trauma_mechanism")
    if mechanism in ("high_speed_rta", "fall_from_height", "penetrating_injury"):
        reasons.append(f"RED: High-risk trauma mechanism ({mechanism}) [WHO-IITT, GVK-EMRI]")
        return RED, reasons
    
    # Multiple injuries → RED
    if complaint.get("multiple_injuries") == "yes":
        reasons.append("RED: Multiple injuries [GVK-EMRI]")
        return RED, reasons
    
    # Suspected spinal injury → RED
    if complaint.get("suspected_spinal") == "yes":
        reasons.append("RED: Suspected spinal injury [GVK-EMRI]")
        return RED, reasons
    
    # Visible acute limb deformity / open fracture → YELLOW
    # Source: WHO IITT Yellow
    if complaint.get("limb_deformity") == "yes" or complaint.get("open_fracture") == "yes":
        reasons.append("YELLOW: Visible limb deformity or open fracture [WHO-IITT]")
        return YELLOW, reasons
    
    # Moderate trauma without specific red flags → YELLOW
    if mechanism in ("low_speed_rta", "fall_standing", "blunt_injury"):
        reasons.append("YELLOW: Moderate trauma mechanism [clinical assessment]")
        return YELLOW, reasons
    
    return REVIEW, ["REVIEW: Trauma without specific severity criteria match"]


def evaluate_bleeding(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Bleeding / injury assessment.
    Source: WHO IITT, GVK EMRI
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # Spurting / arterial bleeding → RED
    if complaint.get("spurting_blood") == "yes":
        reasons.append("RED: Spurting / arterial bleeding [GVK-EMRI]")
        return RED, reasons
    
    # Amputation / limb severed → RED
    if complaint.get("amputation") == "yes":
        reasons.append("RED: Amputation / limb severed [GVK-EMRI]")
        return RED, reasons
    
    # Gastrointestinal bleeding (hematemesis / melena) → RED
    if complaint.get("gi_bleeding") == "yes":
        reasons.append("RED: Gastrointestinal bleeding [GVK-EMRI]")
        return RED, reasons
    
    # Ongoing moderate bleeding → YELLOW
    if complaint.get("ongoing_bleeding") == "yes":
        reasons.append("YELLOW: Ongoing bleeding [WHO-IITT]")
        return YELLOW, reasons
    
    # Bleeding controlled → GREEN
    if complaint.get("bleeding_controlled") == "yes":
        reasons.append("GREEN: Bleeding controlled [clinical assessment]")
        return GREEN, reasons
    
    return REVIEW, ["REVIEW: Bleeding without specific severity assessment"]


def evaluate_burns(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Burns assessment.
    Source: GVK EMRI, WHO IITT
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # Electrical burns → RED
    if complaint.get("burn_type") == "electrical":
        reasons.append("RED: Electrical burn [GVK-EMRI]")
        return RED, reasons
    
    # Chemical burns → RED
    if complaint.get("burn_type") == "chemical":
        reasons.append("RED: Chemical burn [GVK-EMRI]")
        return RED, reasons
    
    # Burns to face/airway → RED
    if complaint.get("burn_face_airway") == "yes":
        reasons.append("RED: Burns involving face/airway [GVK-EMRI]")
        return RED, reasons
    
    # Large area burns (>20% TBSA estimated) → RED
    burn_extent = complaint.get("burn_extent")
    if burn_extent == "large":
        reasons.append("RED: Estimated large area burn (>20% TBSA) [GVK-EMRI]")
        return RED, reasons
    
    # Moderate burns → YELLOW
    if burn_extent == "moderate":
        reasons.append("YELLOW: Moderate burn area [WHO-IITT]")
        return YELLOW, reasons
    
    # Small/minor burns → GREEN
    if burn_extent == "small":
        reasons.append("GREEN: Small/minor burn [clinical assessment]")
        return GREEN, reasons
    
    return REVIEW, ["REVIEW: Burn without extent assessment"]


def evaluate_seizures(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Seizure assessment.
    Source: WHO IITT, GVK EMRI
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # Currently seizing / status epilepticus → RED
    # (Also caught by universal RED active_convulsions)
    if complaint.get("currently_seizing") == "yes":
        reasons.append("RED: Active seizure / status epilepticus [WHO-IITT, GVK-EMRI]")
        return RED, reasons
    
    # Multiple seizures today → RED
    if complaint.get("multiple_seizures") == "yes":
        reasons.append("RED: Multiple seizures [GVK-EMRI]")
        return RED, reasons
    
    # First-time seizure → YELLOW
    if complaint.get("first_seizure") == "yes":
        reasons.append("YELLOW: First-time seizure [clinical assessment]")
        return YELLOW, reasons
    
    # Post-ictal / recovered → YELLOW for observation
    if complaint.get("recovered") == "yes":
        reasons.append("YELLOW: Post-seizure recovery — monitoring needed [clinical assessment]")
        return YELLOW, reasons
    
    return REVIEW, ["REVIEW: Seizure without specific status assessment"]


def evaluate_fever_infection(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Fever / infection assessment.
    Source: WHO IITT
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    clinical = assessment.get("clinical_assessment", {})
    
    # Fever + stiff neck + altered consciousness → RED (meningitis concern)
    # Source: WHO IITT
    if complaint.get("stiff_neck") == "yes":
        consciousness = clinical.get("consciousness", "alert")
        if consciousness != "alert":
            reasons.append("RED: Fever + stiff neck + altered consciousness [WHO-IITT meningitis]")
            return RED, reasons
        reasons.append("YELLOW: Fever with stiff neck [WHO-IITT meningism concern]")
    
    # Severe dehydration signs → YELLOW
    if complaint.get("signs_of_dehydration") == "yes":
        reasons.append("YELLOW: Signs of dehydration [WHO-IITT]")
    
    # High fever in infant <2 months → RED
    # Source: WHO IITT pediatric
    patient_age = assessment.get("patient_age", 0)
    try:
        age_val = float(patient_age)
    except (ValueError, TypeError):
        age_val = 0
    
    if age_val < 1 and complaint.get("infant_under_2months") == "yes":
        reasons.append("RED: Fever in infant under 2 months [WHO-IITT pediatric]")
        return RED, reasons
    
    if reasons:
        highest = RED if any("RED:" in r for r in reasons) else YELLOW
        return highest, reasons
    
    return GREEN, ["GREEN: Fever without emergency signs [clinical assessment]"]


def evaluate_abdominal(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Abdominal complaints assessment.
    Source: WHO IITT, GVK EMRI
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    clinical = assessment.get("clinical_assessment", {})
    patient_age = assessment.get("patient_age", 0)
    worsening = assessment.get("worsening", "").lower()
    
    try:
        age_val = float(patient_age)
    except (ValueError, TypeError):
        age_val = 0
    
    # Severe abdominal pain in elderly (>65) → RED
    # Source: WHO IITT, GVK EMRI
    if age_val >= 65 and (complaint.get("severe_pain") == "yes" or clinical.get("severe_pain") == "yes"):
        reasons.append("RED: Severe abdominal pain in patient ≥65 years [WHO-IITT, GVK-EMRI]")
        return RED, reasons
    
    # Vomiting blood → RED
    if complaint.get("vomiting_blood") == "yes":
        reasons.append("RED: Hematemesis (vomiting blood) [GVK-EMRI]")
        return RED, reasons
    
    # Rigid/board-like abdomen → RED (peritonitis concern)
    if complaint.get("rigid_abdomen") == "yes":
        reasons.append("RED: Rigid abdomen — peritonitis concern [clinical assessment]")
        return RED, reasons
    
    # Severe pain but no other red flags → YELLOW
    if complaint.get("severe_pain") == "yes" or clinical.get("severe_pain") == "yes":
        reasons.append("YELLOW: Severe abdominal pain [WHO-IITT]")
        return YELLOW, reasons
        
    # Mild/moderate abdominal pain, stable, no rigid abdomen → GREEN
    if complaint.get("severe_pain") == "no" or clinical.get("severe_pain") == "no":
        reasons.append("GREEN: Mild/moderate abdominal symptoms without peritonitis or red flags [WHO-IITT]")
        return GREEN, reasons
    
    return REVIEW, ["REVIEW: Abdominal complaint without specific severity assessment"]


def evaluate_pregnancy(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Pregnancy-related & maternal emergency assessment.
    Source: WHO Interagency Integrated Triage Tool (IITT) 2020 & GVK EMRI Obstetric Protocol.
    
    WHO-IITT Emergency Signs (RED):
      - Severe vaginal bleeding / haemorrhage in pregnancy or postpartum
      - Eclampsia (seizures / altered consciousness with severe hypertension)
      - Imminent delivery / crowning / cord prolapse / fetal bradycardia
      - Severe acute trauma or physical assault/injury in pregnancy (Maternal Injury)
      - Severe abdominal pain with signs of shock / rigid abdomen / peritonism
      - High fever with foul-smelling vaginal discharge and altered vitals (Maternal Sepsis)
    
    WHO-IITT Priority Signs (YELLOW):
      - Active labor (regular contractions without crowning)
      - Moderate abdominal/pelvic pain
      - Premature rupture of membranes (water broken without active labor)
      - Mild/moderate vaginal spotting/bleeding
      - History of reduced fetal movements
      - Uncomplicated pregnancy referral or minor non-abdominal trauma
    
    GREEN:
      - Routine pregnancy check, early labor without distress or complications.
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    clinical = assessment.get("clinical_assessment", {})
    symptoms = [s.lower() for s in assessment.get("symptoms", [])]
    worsening = assessment.get("worsening", "").lower()
    
    # ─── RED CRITERIA (WHO-IITT Emergency Signs) ───

    # 1. Maternal Trauma / Injury during pregnancy → RED
    # Any acute physical injury, road accident, fall, blunt trauma to abdomen or assault in pregnancy
    # is a critical threat to both mother and fetus (placental abruption / uterine rupture risk).
    if complaint.get("maternal_injury") == "yes" or complaint.get("trauma_involved") == "yes":
        reasons.append("RED: Acute maternal trauma / injury in pregnancy — high risk of placental abruption/fetal compromise [WHO-IITT, GVK-EMRI]")
        return RED, reasons

    # 2. Imminent delivery / crowning / cord prolapse / abnormal lie → RED
    if complaint.get("crowning") == "yes" or complaint.get("cord_prolapse") == "yes":
        reasons.append("RED: Active labor with crowning / imminent delivery / cord prolapse [WHO-IITT, GVK-EMRI]")
        return RED, reasons

    # 3. Heavy vaginal bleeding / postpartum haemorrhage → RED
    if complaint.get("heavy_vaginal_bleeding") == "yes" or clinical.get("bleeding_severity") in ("heavy_uncontrolled", "moderate"):
        reasons.append("RED: Severe obstetric / vaginal haemorrhage [WHO-IITT Emergency Signs]")
        return RED, reasons

    # 4. Eclamptic seizures / severe hypertensive crisis with headache/visual changes → RED
    if complaint.get("eclamptic_seizures") == "yes" or clinical.get("active_convulsions") == "yes":
        reasons.append("RED: Eclamptic seizures / maternal convulsion [WHO-IITT Emergency Signs]")
        return RED, reasons

    # 5. Severe abdominal / uterine pain with rapid worsening or shock → RED
    if clinical.get("severe_pain") == "yes" and worsening == "yes":
        reasons.append("RED: Severe rapidly worsening abdominal pain in pregnancy [WHO-IITT Emergency Signs]")
        return RED, reasons

    # 6. Sepsis signs in pregnancy: high fever + foul discharge or confusion → RED
    if complaint.get("maternal_sepsis") == "yes" or ("confusion" in symptoms and "fever" in symptoms):
        reasons.append("RED: Suspected maternal sepsis / chorioamnionitis [WHO-IITT]")
        return RED, reasons

    # 7. Shock / distress symptoms in pregnancy → RED
    # Confusion, cyanosis, cold/clammy skin in a pregnant patient = haemodynamic compromise
    shock_symptoms = {"confusion", "cyanosis", "cold_clammy"}
    present_shock = shock_symptoms.intersection(set(symptoms))
    if present_shock:
        reasons.append(f"RED: Maternal haemodynamic compromise — {', '.join(present_shock)} in pregnancy [WHO-IITT, GVK-EMRI]")
        return RED, reasons

    # 8. Multiple distress symptoms (≥3) in pregnancy → RED (multi-system involvement)
    distress_symptoms = {"sweating", "nausea_vomiting", "dizziness", "palpitations", "chest_pain", "breathlessness"}
    present_distress = distress_symptoms.intersection(set(symptoms))
    if len(present_distress) >= 3:
        reasons.append(f"RED: Multiple acute distress signs in pregnancy ({len(present_distress)} symptoms) — possible obstetric emergency [GVK-EMRI 102]")
        return RED, reasons

    # ─── YELLOW CRITERIA (WHO-IITT Priority Signs) ───

    # 1. Active regular labor contractions (without crowning) → YELLOW
    if complaint.get("active_labor") == "yes" or complaint.get("regular_contractions") == "yes":
        reasons.append("YELLOW: Active labor contractions — urgent obstetric admission [WHO-IITT Priority Signs]")
        return YELLOW, reasons

    # 2. Documented or referred pregnancy complications → YELLOW
    if complaint.get("pregnancy_complications") == "yes":
        reasons.append("YELLOW: Pregnancy with identified maternal/fetal complications [WHO-IITT]")
        return YELLOW, reasons

    # 3. Rupture of membranes (water broken) → YELLOW
    if complaint.get("water_broken") == "yes":
        reasons.append("YELLOW: Premature rupture of membranes [WHO-IITT Priority Signs]")
        return YELLOW, reasons

    # 4. Mild or moderate bleeding / spotting without shock → YELLOW
    if complaint.get("mild_bleeding") == "yes" or clinical.get("bleeding_severity") == "minor":
        reasons.append("YELLOW: Vaginal bleeding/spotting in pregnancy [WHO-IITT Priority Signs]")
        return YELLOW, reasons

    # 5. Severe pain or acute distress reported → YELLOW
    if clinical.get("severe_pain") == "yes":
        reasons.append("YELLOW: Severe pain during pregnancy [WHO-IITT Priority Signs]")
        return YELLOW, reasons

    # 6. Any distress symptoms reported in pregnancy → YELLOW (minimum)
    # Per GVK EMRI 102 protocol, ALL pregnancy emergency calls = minimum YELLOW
    if present_distress:
        reasons.append(f"YELLOW: Pregnancy with acute symptoms ({', '.join(present_distress)}) — minimum urgent priority [GVK-EMRI 102]")
        return YELLOW, reasons

    # 7. Worsening condition in pregnancy → YELLOW
    if worsening == "yes":
        reasons.append("YELLOW: Worsening symptoms in pregnancy — requires urgent obstetric evaluation [WHO-IITT]")
        return YELLOW, reasons

    # ─── DEFAULT: All pregnancy calls = minimum YELLOW ───
    # Per GVK EMRI 102 Obstetric Dispatch Protocol, any pregnant woman requesting
    # emergency ambulance is triaged as minimum YELLOW (urgent) — never GREEN.
    # GREEN is only for routine antenatal check-ups that do not involve ambulance dispatch.
    return YELLOW, ["YELLOW: Pregnancy emergency call — minimum urgent obstetric priority [GVK-EMRI 102 Protocol]"]


def evaluate_poisoning(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Poisoning / overdose / envenomation.
    Source: WHO IITT Section 1 (Emergency Signs), GVK EMRI
    """
    reasons = []
    complaint = assessment.get("complaint_specific", {})
    
    # Snake bite → RED
    # Source: WHO IITT Emergency Signs
    if complaint.get("snake_bite") == "yes":
        reasons.append("RED: Snake bite with envenomation risk [WHO-IITT]")
        return RED, reasons
    
    # Poisoning / chemical ingestion → RED
    # Source: WHO IITT Emergency Signs
    if complaint.get("poison_ingested") == "yes":
        reasons.append("RED: Poison / toxic chemical ingestion [WHO-IITT, GVK-EMRI]")
        return RED, reasons
    
    # Drug overdose → RED
    # Source: WHO IITT, GVK-EMRI
    if complaint.get("drug_overdose") == "yes":
        reasons.append("RED: Suspected acute drug overdose [GVK-EMRI, WHO-IITT]")
        return RED, reasons
    
    # Inhalation of smoke/toxic gas or chemical burns → RED
    if complaint.get("toxic_inhalation") == "yes" or complaint.get("chemical_burns") == "yes":
        reasons.append("RED: Toxic gas inhalation or chemical burn exposure [WHO-IITT]")
        return RED, reasons
        
    # Suspected exposure or mild/moderate exposure without emergency signs → YELLOW
    # Source: WHO IITT Section 2 Priority Signs
    if complaint.get("snake_bite") == "no" and complaint.get("poison_ingested") == "no" and complaint.get("drug_overdose") == "no":
        # Patient is stable, alert, no red signs: marked as YELLOW (Priority Observation) under WHO IITT
        reasons.append("YELLOW: Suspected toxic exposure without immediate emergency airway/breathing impairment [WHO-IITT Priority Signs]")
        return YELLOW, reasons
    
    return YELLOW, ["YELLOW: Toxic substance exposure under observation [WHO-IITT]"]


def evaluate_other(assessment: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Fallback for complaints not in specific categories.
    Returns REVIEW_REQUIRED by default — requires clinical review.
    """
    return REVIEW, ["REVIEW: Complaint category 'Other' — requires clinical review for priority assignment"]


# ──────────────────────────────────────────────────────
# OPTIONAL VITAL SIGNS CHECK (WHO IITT)
# ──────────────────────────────────────────────────────
def evaluate_vital_signs(assessment: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """
    Check high-risk vital sign thresholds for up-triaging.
    Only applies if vital signs are actually provided (optional).
    
    Source: WHO IITT Adult Vital Sign Thresholds
    """
    reasons = []
    vitals = assessment.get("vital_signs", {})
    
    if not vitals:
        return None, []
    
    # Heart Rate thresholds (Adult ≥12y): <60 or >130 bpm
    hr = vitals.get("heart_rate")
    if hr is not None:
        try:
            hr_val = int(hr)
            if hr_val < 60:
                reasons.append(f"RED: Bradycardia — HR {hr_val} bpm (<60) [WHO-IITT vital signs]")
            elif hr_val > 130:
                reasons.append(f"RED: Tachycardia — HR {hr_val} bpm (>130) [WHO-IITT vital signs]")
        except (ValueError, TypeError):
            pass
    
    # Respiratory Rate: <10 or >30 breaths/min
    rr = vitals.get("respiratory_rate")
    if rr is not None:
        try:
            rr_val = int(rr)
            if rr_val < 10:
                reasons.append(f"RED: Bradypnea — RR {rr_val}/min (<10) [WHO-IITT vital signs]")
            elif rr_val > 30:
                reasons.append(f"RED: Tachypnea — RR {rr_val}/min (>30) [WHO-IITT vital signs]")
        except (ValueError, TypeError):
            pass
    
    # SpO2: <92%
    spo2 = vitals.get("spo2")
    if spo2 is not None:
        try:
            spo2_val = int(spo2)
            if spo2_val < 92:
                reasons.append(f"RED: Hypoxia — SpO2 {spo2_val}% (<92%) [WHO-IITT vital signs]")
        except (ValueError, TypeError):
            pass
    
    if reasons:
        return RED, reasons
    return None, []


# ──────────────────────────────────────────────────────
# COMPLAINT EVALUATOR DISPATCH
# ──────────────────────────────────────────────────────
COMPLAINT_EVALUATORS = {
    "cardiac_chest": evaluate_cardiac_chest,
    "breathing": evaluate_breathing,
    "neurological": evaluate_neurological,
    "trauma": evaluate_trauma,
    "bleeding_injury": evaluate_bleeding,
    "burns": evaluate_burns,
    "seizures": evaluate_seizures,
    "fever_infection": evaluate_fever_infection,
    "abdominal": evaluate_abdominal,
    "pregnancy": evaluate_pregnancy,
    "poisoning": evaluate_poisoning,
    "other": evaluate_other,
}


# ──────────────────────────────────────────────────────
# MAIN TRIAGE FUNCTION
# ──────────────────────────────────────────────────────
def run_triage(assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete triage evaluation pipeline.
    
    Evaluation order (sequential, highest priority wins):
    1. Universal RED criteria (WHO IITT emergency signs)
    2. Vital signs thresholds (WHO IITT, if available)
    3. Complaint-specific criteria
    4. Universal YELLOW criteria (WHO IITT priority signs)
    5. Default → REVIEW_REQUIRED if no rule matched
    
    Returns a complete triage result with priority, reasons,
    rule sources, and audit metadata.
    """
    all_reasons = []
    final_priority = GREEN  # Default assumption
    
    # Step 1: Universal RED
    priority, reasons = evaluate_universal_red(assessment)
    all_reasons.extend(reasons)
    if priority == RED:
        final_priority = RED
    
    # Step 2: Vital signs (if available) — can up-triage
    vs_priority, vs_reasons = evaluate_vital_signs(assessment)
    all_reasons.extend(vs_reasons)
    if vs_priority == RED:
        final_priority = RED
    
    # Step 3: Complaint-specific evaluation
    chief_complaint = assessment.get("chief_complaint", "other")
    evaluator = COMPLAINT_EVALUATORS.get(chief_complaint, evaluate_other)
    complaint_priority, complaint_reasons = evaluator(assessment)
    all_reasons.extend(complaint_reasons)
    
    # Only upgrade priority, never downgrade from RED
    if final_priority != RED:
        if complaint_priority == RED:
            final_priority = RED
        elif complaint_priority == YELLOW and final_priority != RED:
            final_priority = YELLOW
        elif complaint_priority == REVIEW and final_priority == GREEN:
            final_priority = REVIEW
    
    # Step 4: Universal YELLOW (if not already RED)
    if final_priority not in (RED,):
        yellow_priority, yellow_reasons = evaluate_universal_yellow(assessment)
        all_reasons.extend(yellow_reasons)
        if yellow_priority == YELLOW and final_priority in (GREEN, REVIEW):
            final_priority = YELLOW
    
    # Handle contradictory information
    has_contradictions = _detect_contradictions(assessment)
    if has_contradictions:
        all_reasons.append("NOTE: Potentially contradictory responses detected — clinical review recommended")
        if final_priority == GREEN:
            final_priority = REVIEW
    
    # Handle insufficient data
    missing_count = _count_missing_fields(assessment)
    if missing_count > 5:
        all_reasons.append(f"NOTE: {missing_count} assessment fields not answered — limited data")
        if final_priority == GREEN:
            final_priority = REVIEW
    
    # Build result
    assessment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "assessment_id": assessment_id,
        "request_id": assessment.get("request_id"),
        "suggested_priority": final_priority,
        "assessment_reasons": all_reasons,
        "chief_complaint": chief_complaint,
        "ruleset_version": RULESET_VERSION,
        "ruleset_sources": RULESET_SOURCES,
        "assessed_at": now,
        "clinical_review_status": "PENDING",
        "clinical_review_note": (
            "This priority suggestion is generated by documented triage criteria. "
            "It has NOT been validated for operational use and requires review by "
            "a qualified clinical professional before acting on the recommendation."
        ),
        "data_completeness": {
            "missing_fields": missing_count,
            "has_contradictions": has_contradictions,
            "vital_signs_available": bool(assessment.get("vital_signs"))
        }
    }


def _detect_contradictions(assessment: Dict[str, Any]) -> bool:
    """
    Basic contradiction detection.
    Example: patient reported as 'alert' but also 'unresponsive'.
    """
    clinical = assessment.get("clinical_assessment", {})
    
    # Alert but also unresponsive
    if clinical.get("consciousness") == "alert" and clinical.get("active_convulsions") == "yes":
        # Not necessarily contradictory (patient may have recovered)
        pass
    
    # Not breathing but talking
    if clinical.get("breathing_status") == "not_breathing":
        complaint = assessment.get("complaint_specific", {})
        if complaint.get("speech_difficulty") == "no":
            return True  # Can't have normal speech while not breathing
    
    return False


def _count_missing_fields(assessment: Dict[str, Any]) -> int:
    """Count how many clinical assessment fields are unanswered."""
    clinical = assessment.get("clinical_assessment", {})
    expected = [
        "consciousness", "breathing_status", "airway_status",
        "bleeding_severity", "severe_pain"
    ]
    missing = sum(1 for field in expected if clinical.get(field) in (None, "", "not_assessed"))
    return missing


# ──────────────────────────────────────────────────────
# PERSISTENCE
# ──────────────────────────────────────────────────────
ASSESSMENTS_DIR = Path(__file__).resolve().parent.parent / "data" / "assessments"


def save_assessment(assessment_data: Dict[str, Any], triage_result: Dict[str, Any]) -> str:
    """
    Save the complete assessment and triage result to JSON file.
    Creates an audit trail with timestamps.
    """
    ASSESSMENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    assessment_id = triage_result["assessment_id"]
    record = {
        "assessment_id": assessment_id,
        "request_id": assessment_data.get("request_id"),
        "patient_age": assessment_data.get("patient_age"),
        "chief_complaint": assessment_data.get("chief_complaint"),
        "symptoms": assessment_data.get("symptoms", []),
        "onset_duration": assessment_data.get("onset_duration"),
        "worsening": assessment_data.get("worsening"),
        "complaint_specific": assessment_data.get("complaint_specific", {}),
        "clinical_assessment": assessment_data.get("clinical_assessment", {}),
        "vital_signs": assessment_data.get("vital_signs", {}),
        "triage_result": triage_result,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "audit_trail": [
            {
                "action": "ASSESSMENT_CREATED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": "system",
                "details": f"Triage assessment created — priority: {triage_result['suggested_priority']}"
            }
        ]
    }
    
    filepath = ASSESSMENTS_DIR / f"{assessment_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    
    return assessment_id


def get_stored_patient_assessment(request_id: str) -> Dict[str, Any]:
    """
    Retrieve a stored patient assessment by request_id.
    Searches the assessments directory for a matching record.
    Returns default priority/chief_complaint if not found.
    """
    if not request_id or not ASSESSMENTS_DIR.exists():
        return {"priority": "YELLOW", "chief_complaint": "general"}

    try:
        for filepath in ASSESSMENTS_DIR.glob("*.json"):
            with open(filepath, "r", encoding="utf-8") as f:
                record = json.load(f)
            if record.get("request_id") == request_id:
                triage = record.get("triage_result", {})
                return {
                    "priority": triage.get("suggested_priority", "YELLOW"),
                    "chief_complaint": record.get("chief_complaint", "general"),
                }
    except Exception:
        pass

    return {"priority": "YELLOW", "chief_complaint": "general"}

