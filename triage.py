"""
Two-stage educational triage diagnostic engine.
Combines deterministic Stage 1 safety rules with a cached Scikit-Learn demo classifier
(and a graceful deterministic fallback if Scikit-Learn is missing).

DISCLAIMER: All predictions, probabilities, and scores are synthetic educational demonstrations.
They have NO medical or clinical validity and must NOT be used for real emergency medical decisions.
"""

from typing import Any, Dict, List, Optional, Tuple
from .constants import STAGE_1_RED_FLAG_SYMPTOMS, TriageLevel

# Synthetic default baseline vitals used when optional values are omitted by user
SYNTHETIC_BASELINE_VITALS = {
    "heart_rate": 75.0,
    "systolic_bp": 120.0,
    "diastolic_bp": 80.0,
    "spo2": 98.0,
    "temperature_f": 98.6,
}

# Module-level model cache to prevent retraining on every Streamlit rerun
_CACHED_CLASSIFIER = None
_CACHED_CLASSES = None
_SKLEARN_AVAILABLE = None


def check_sklearn_availability() -> bool:
    """Check if scikit-learn is installed and importable."""
    global _SKLEARN_AVAILABLE
    if _SKLEARN_AVAILABLE is not None:
        return _SKLEARN_AVAILABLE
    try:
        import sklearn  # noqa: F401
        from sklearn.tree import DecisionTreeClassifier  # noqa: F401
        _SKLEARN_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        _SKLEARN_AVAILABLE = False
    return _SKLEARN_AVAILABLE


def get_trained_demo_classifier():
    """
    Build and return a cached, deterministic Scikit-Learn DecisionTreeClassifier
    trained on a tiny synthetic demo dataset.
    """
    global _CACHED_CLASSIFIER, _CACHED_CLASSES
    if _CACHED_CLASSIFIER is not None:
        return _CACHED_CLASSIFIER, _CACHED_CLASSES

    if not check_sklearn_availability():
        return None, None

    from sklearn.tree import DecisionTreeClassifier

    # Features: [heart_rate, systolic_bp, diastolic_bp, spo2, temperature_f, pain_level]
    # Clearly synthetic demo training examples
    X_synthetic = [
        # Normal/Mild -> GREEN
        [72.0, 118.0, 78.0, 99.0, 98.4, 1.0],
        [75.0, 120.0, 80.0, 98.0, 98.6, 2.0],
        [80.0, 122.0, 82.0, 97.0, 99.0, 3.0],
        [68.0, 115.0, 76.0, 98.5, 98.2, 2.0],
        # Moderate/Urgent -> YELLOW
        [105.0, 142.0, 92.0, 93.0, 101.2, 5.0],
        [110.0, 148.0, 95.0, 92.0, 101.8, 6.0],
        [98.0, 138.0, 88.0, 94.0, 100.5, 7.0],
        [102.0, 145.0, 90.0, 93.5, 102.0, 6.0],
        # Severe/Critical -> RED
        [145.0, 185.0, 115.0, 85.0, 103.5, 9.0],
        [150.0, 190.0, 120.0, 82.0, 104.0, 10.0],
        [135.0, 175.0, 110.0, 88.0, 102.8, 8.0],
        [40.0, 80.0, 50.0, 84.0, 95.0, 9.0],  # Severe bradycardia/hypotension
    ]
    y_synthetic = [
        "GREEN", "GREEN", "GREEN", "GREEN",
        "YELLOW", "YELLOW", "YELLOW", "YELLOW",
        "RED", "RED", "RED", "RED"
    ]

    # Explicit class order: RED, YELLOW, GREEN
    classes = ["RED", "YELLOW", "GREEN"]

    clf = DecisionTreeClassifier(max_depth=4, random_state=42)
    clf.fit(X_synthetic, y_synthetic)

    _CACHED_CLASSIFIER = clf
    _CACHED_CLASSES = list(clf.classes_)
    return _CACHED_CLASSIFIER, _CACHED_CLASSES


def check_stage1_symptoms(symptoms: List[str], primary_symptom: Optional[str] = None) -> bool:
    """
    Stage 1: Simple DEMO-ONLY symptom-flag stage.
    Checks if any recognized red-flag symptoms are present.
    """
    search_text = " ".join([str(s).lower() for s in (symptoms or [])])
    if primary_symptom:
        search_text += f" {primary_symptom.lower()}"

    for red_flag in STAGE_1_RED_FLAG_SYMPTOMS:
        if red_flag in search_text:
            return True
    return False


def calculate_demo_priority_score(
    triage_level: str,
    p_red: float,
    p_yellow: float,
    pain_level: int,
) -> float:
    """
    Compute a deterministic demo priority score (DEMO ONLY).
    Higher score indicates higher priority within a triage category.
    """
    # Base weight by triage level
    level_base = {"RED": 100.0, "YELLOW": 50.0, "GREEN": 10.0}.get(triage_level, 0.0)
    score = level_base + (p_red * 50.0) + (p_yellow * 15.0) + (float(pain_level) * 2.0)
    return round(score, 2)


def evaluate_triage(
    symptoms: Optional[List[str]] = None,
    primary_symptom: Optional[str] = None,
    pain_level: int = 1,
    heart_rate: Optional[float] = None,
    systolic_bp: Optional[float] = None,
    diastolic_bp: Optional[float] = None,
    spo2: Optional[float] = None,
    temperature_f: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Execute two-stage triage pipeline:
    1. Stage 1: Deterministic red-flag symptom override.
    2. Stage 2: Scikit-Learn demo classifier (or deterministic fallback if missing).
    
    Returns a dictionary containing triage_level, probabilities, score, and diagnostics.
    """
    symptoms_list = symptoms or []
    safe_pain = max(1, min(10, int(pain_level)))

    # ----------------------------------------------------
    # STAGE 1: DEMO-ONLY Symptom Safety Rule
    # ----------------------------------------------------
    if check_stage1_symptoms(symptoms_list, primary_symptom):
        p_red, p_yellow, p_green = 1.0, 0.0, 0.0
        triage_level = TriageLevel.RED.value
        stage_used = "STAGE_1_RED_FLAG_RULE"
        stage_desc = (
            "DEMO ONLY: Triggered simulated Stage 1 red-flag symptom check "
            "(Chest pain, Shortness of breath, Unconsciousness, or Uncontrolled bleeding)."
        )
        score = calculate_demo_priority_score(triage_level, p_red, p_yellow, safe_pain)
        return {
            "triage_level": triage_level,
            "p_red": p_red,
            "p_yellow": p_yellow,
            "p_green": p_green,
            "demo_priority_score": score,
            "stage_used": stage_used,
            "stage_desc": stage_desc,
            "sklearn_used": False,
        }

    # ----------------------------------------------------
    # STAGE 2: Scikit-Learn Classifier or Deterministic Fallback
    # ----------------------------------------------------
    # Impute missing vitals with synthetic baselines
    hr = float(heart_rate) if heart_rate is not None else SYNTHETIC_BASELINE_VITALS["heart_rate"]
    sbp = float(systolic_bp) if systolic_bp is not None else SYNTHETIC_BASELINE_VITALS["systolic_bp"]
    dbp = float(diastolic_bp) if diastolic_bp is not None else SYNTHETIC_BASELINE_VITALS["diastolic_bp"]
    ox = float(spo2) if spo2 is not None else SYNTHETIC_BASELINE_VITALS["spo2"]
    temp = float(temperature_f) if temperature_f is not None else SYNTHETIC_BASELINE_VITALS["temperature_f"]

    feature_vector = [[hr, sbp, dbp, ox, temp, float(safe_pain)]]

    clf, classes = get_trained_demo_classifier()
    if clf is not None:
        raw_probs = clf.predict_proba(feature_vector)[0]
        prob_dict = {cls_name: float(prob) for cls_name, prob in zip(classes, raw_probs)}
        p_red = round(prob_dict.get("RED", 0.0), 3)
        p_yellow = round(prob_dict.get("YELLOW", 0.0), 3)
        p_green = round(prob_dict.get("GREEN", 0.0), 3)

        # Determine predicted class (highest probability, tie broken by severity)
        predicted_class = clf.predict(feature_vector)[0]
        stage_used = "STAGE_2_SCIKIT_LEARN"
        stage_desc = "DEMO ONLY: Evaluated via synthetic Scikit-Learn DecisionTree classifier."
        sklearn_used = True
    else:
        # Graceful Deterministic Fallback when scikit-learn is not installed
        sklearn_used = False
        stage_used = "STAGE_2_DETERMINISTIC_FALLBACK"
        stage_desc = (
            "DEMO ONLY: Scikit-learn not available. Used deterministic rule fallback. "
            "To enable ML classifier, install scikit-learn via: pip install scikit-learn"
        )
        if safe_pain >= 8 or ox < 90.0:
            p_red, p_yellow, p_green = 0.80, 0.15, 0.05
            predicted_class = "RED"
        elif safe_pain >= 5 or ox < 94.0 or temp > 101.0:
            p_red, p_yellow, p_green = 0.15, 0.70, 0.15
            predicted_class = "YELLOW"
        else:
            p_red, p_yellow, p_green = 0.05, 0.15, 0.80
            predicted_class = "GREEN"

    score = calculate_demo_priority_score(predicted_class, p_red, p_yellow, safe_pain)

    return {
        "triage_level": predicted_class,
        "p_red": p_red,
        "p_yellow": p_yellow,
        "p_green": p_green,
        "demo_priority_score": score,
        "stage_used": stage_used,
        "stage_desc": stage_desc,
        "sklearn_used": sklearn_used,
    }
