from typing import Dict, Any, List

# Fast rule-based dictionary for instant Hinglish/Hindi mapping to medical English
TERM_MAP = {
    # Cuts / Bleeding
    "chhuri": "cut bleeding wound knife",
    "chaku": "cut bleeding wound knife",
    "blade": "cut bleeding wound",
    "khoon": "bleeding wound direct pressure",
    "chot": "wound injury dressing",
    "patti": "bandage dressing wound",
    
    # Burns
    "jal": "burn scald heat cold water",
    "jala": "burn scald heat cold water",
    "aag": "burn injury cold water",
    "garam": "scald hot liquid burn",
    "chaale": "blisters burn care",
    
    # Bites / Stings
    "kaat": "sting bite venom insect",
    "kaata": "sting bite venom insect",
    "madhumakkhi": "bee sting insect sting venom",
    "keeda": "insect bite sting",
    "saanp": "snake bite poison",
    "kutta": "dog bite animal bite",
    
    # Choking / Breathing
    "saans": "breathing airway asthma",
    "gala": "choking airway obstruction",
    "atki": "choking back blows thrusts",
    "fas": "choking back blows thrusts",
    "khansi": "coughing choking",
    
    # Fainting / Heart / Pain
    "behosh": "unconscious fainting recovery position",
    "chakkar": "fainting dizziness recovery position",
    "seene": "chest pain heart attack",
    "dil": "heart chest pain",
    "sar": "headache head injury concussion",
    "sir": "headache head injury concussion",
    "haddi": "fracture broken bone splint",
    "moch": "sprain strain RICE rest ice"
}

def quick_translate_query(text: str) -> str:
    """
    Lightning-fast (0ms) keyword translation from Hinglish/Hindi to English medical terms.
    Bypasses slow LLM latency completely.
    """
    text_lower = text.lower()
    expanded = []
    
    for k, v in TERM_MAP.items():
        if k in text_lower:
            expanded.append(v)
            
    if expanded:
        return text + " " + " ".join(expanded)
    return text

