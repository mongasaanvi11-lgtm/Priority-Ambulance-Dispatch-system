import re
from typing import Dict, Any, Optional

# Obvious potentially life-threatening red-flag warning signs that trigger immediate fast-path emergency guidance
EMERGENCY_TRIGGER_KEYWORDS = [
    # Severe breathing issues
    "unconscious", "not breathing", "stopped breathing", "gasping for air", "choking severely", "cannot breathe",
    "saans nahi aa rahi", "saans ruk gayi", "behosh", "unresponsive", "blue lips",
    # Severe chest / heart issues
    "chest pain", "crushing chest", "heart attack", "dil ka daura", "seene me dard",
    # Severe bleeding / trauma
    "severe bleeding", "spurting blood", "heavy bleeding", "khoon beh raha hai", "khoon ruk nahi raha", "amputation", "limb severed",
    # Anaphylaxis / poisoning
    "throat closing", "swollen tongue", "anaphylaxis", "severe allergic reaction", "swallowed poison", "poisoning", "zeher",
    # Stroke / neurological
    "stroke", "facial drooping", "arm weakness", "slurred speech", "paralysis", "lakwa", "seizure lasting", "continuous fit"
]

def check_immediate_emergency(user_text: str) -> Optional[Dict[str, Any]]:
    """
    Independent fast-path check for potentially life-threatening warning signs.
    Does NOT wait for retrieval, gemini, or follow-up questions.
    """
    text_lower = user_text.lower()
    
    for kw in EMERGENCY_TRIGGER_KEYWORDS:
        # Match whole word or exact phrase
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            return {
                "is_immediate_emergency": True,
                "matched_sign": kw,
                "emergency_guidance": (
                    "🚨 **IMMEDIATE EMERGENCY WARNING / CRITICAL ALERT** 🚨\n\n"
                    "Potential life-threatening signs detected (**" + kw.title() + "**).\n\n"
                    "1. **CALL EMERGENCY SERVICES (112 / 911 / 108 / 102) IMMEDIATELY.** Do not wait!\n"
                    "2. If the person is unconscious and not breathing, begin **CPR** immediately if trained (30 chest compressions followed by 2 rescue breaths).\n"
                    "3. If there is severe bleeding, apply firm direct pressure with a clean cloth or bandage.\n"
                    "4. If choking and unable to breathe or speak, perform back blows and abdominal thrusts (Heimlich maneuver).\n"
                    "5. Keep the patient calm, lying down, and warm. Do not give them anything to eat or drink.\n\n"
                    "⚠️ *This is emergency first-aid advice while professional paramedics are en route.*"
                )
            }
            
    return None

