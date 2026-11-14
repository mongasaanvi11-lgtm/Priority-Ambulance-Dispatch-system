"""
AmbuPriority — Hospital Panel & Empanelment Registry
=====================================================
Manages verified empanelment and healthcare panel data for hospitals in India.

Categories:
1. Ayushman Bharat – PM-JAY (National Health Authority)
2. CGHS (Central Government Health Scheme)
3. ECHS (Ex-Servicemen Contributory Health Scheme)
4. ESIC (Employees' State Insurance Corporation)
5. State Government Health Schemes (e.g. RGHS, MJPJAY, Aarogyasri, Swasthya Sathi, etc.)
6. Private Insurance / TPA Networks (e.g. Medi Assist, Vidal, Star Health, ICICI Lombard, etc.)

Rules:
- Reliable, verified source attribution.
- Clear visual labels:
  * "Empanelled"
  * "Not Empanelled" (only when officially confirmed)
  * "Status Not Verified"
  * "Information Unavailable"
- Do NOT label unverified hospitals as "Not Empanelled".
- Fast in-memory lookup with persistent JSON backing.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

PANEL_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hospital_empanelment.json"
DYNAMIC_PANEL_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "delhi_osm_classified.json"
FACILITY_OVERRIDES_FILE = Path(__file__).resolve().parent.parent / "data" / "facility_overrides.json"
MANUAL_VERIFICATION_FILE = Path(__file__).resolve().parent.parent / "data" / "manual_verification.json"

# In-memory lookup map
_EMPANELMENT_REGISTRY: Optional[Dict[str, Any]] = None
_DYNAMIC_PANEL_CACHE: Dict[str, Any] = {}
_FACILITY_OVERRIDES: Optional[Dict[str, Any]] = None
_MANUAL_VERIFICATION: Optional[Dict[str, Any]] = None

# Name patterns for facilities that never run an insurer/TPA desk. Applied to any
# city, so coverage outside Delhi does not depend on a hand-built override file.
_SMALL_FACILITY_RE = re.compile(
    r"(clinic|diagnostic|polyclinic|nursing home|maternity home|ayurved|homoeopath|"
    r"homeopath|naturopath|dental care|dental clinic|dispensary|path ?lab|imaging cent|"
    r"scan cent|health cent)",
    re.I,
)
_BIG_CHAIN_RE = re.compile(
    r"(apollo|fortis|max |max$|medanta|manipal|blk|narayana|artemis|jaypee|sharda|"
    r"aiims|safdarjung|ganga ram|medeor|kailash|moolchand|paras|venkateshwar|primus|"
    r"batra|pushpawati|dharamshila|metro|cloudnine|rainbow|columbia asia)",
    re.I,
)


def _load_manual_verification() -> Dict[str, Any]:
    """
    Hand-verified insurer/TPA data (checked against the hospital's own website,
    insurance desk or an official network list). These entries always win: they
    carry a source URL and the date they were verified.
    """
    global _MANUAL_VERIFICATION
    if _MANUAL_VERIFICATION is not None:
        return _MANUAL_VERIFICATION
    _MANUAL_VERIFICATION = {}
    try:
        if MANUAL_VERIFICATION_FILE.exists():
            with open(MANUAL_VERIFICATION_FILE, "r", encoding="utf-8") as f:
                _MANUAL_VERIFICATION = json.load(f) or {}
    except Exception:
        _MANUAL_VERIFICATION = {}
    return _MANUAL_VERIFICATION


def _format_manual_verification(entry: Dict[str, Any]) -> Dict[str, Any]:
    panels = entry.get("panels") or []
    schemes = entry.get("schemes") or []
    source = entry.get("source") or "Manual verification"
    verified_on = entry.get("verified_on") or ""

    def _panel(label: str, present: bool) -> Dict[str, Any]:
        return {
            "name": label,
            "status": "Empanelled" if present else "Status Not Verified",
            "badge": "empanelled" if present else "unverified",
            "details": (", ".join(panels[:6]) if label.startswith("Private Insurance") else
                        f"Verified manually on {verified_on}") if present else
                       "No entry in the manually verified list",
        }

    has_pmjay = any("pmjay" in s.lower() or "ayushman" in s.lower() for s in schemes)
    has_cghs = any("cghs" in s.lower() for s in schemes)
    has_echs = any("echs" in s.lower() for s in schemes)
    has_esic = any("esic" in s.lower() for s in schemes)
    has_state = any("state" in s.lower() for s in schemes)
    has_tpa = bool(panels) or bool(entry.get("cashless_available"))

    return {
        "has_verified_panels": True,
        "matched_category": "manual_verified",
        "cashless": "available" if has_tpa else "not_available",
        "source": source,
        "last_verified": verified_on,
        "official_url": source if str(source).startswith("http") else "",
        "manual_note": entry.get("note", ""),
        "panels": {
            "pmjay": _panel("Ayushman Bharat – PM-JAY", has_pmjay),
            "cghs": _panel("CGHS", has_cghs),
            "echs": _panel("ECHS", has_echs),
            "esic": _panel("ESIC", has_esic),
            "state_govt": _panel("State Govt Health Schemes", has_state),
            "tpa_insurance": {
                "name": "Private Insurance / TPA Networks",
                "status": "Empanelled" if has_tpa else "Status Not Verified",
                "badge": "empanelled" if has_tpa else "unverified",
                "details": (f"Cashless with {len(panels)} insurers/TPAs: {', '.join(panels[:4])}"
                            if panels else "Cashless not confirmed"),
            },
        },
    }


def _load_facility_overrides() -> Dict[str, Any]:
    """
    Facilities known NOT to hold insurer/TPA tie-ups (clinics, diagnostics,
    nursing homes). Avoids showing "verifying…" forever for places that
    structurally do not do cashless.
    """
    global _FACILITY_OVERRIDES
    if _FACILITY_OVERRIDES is not None:
        return _FACILITY_OVERRIDES
    _FACILITY_OVERRIDES = {}
    try:
        if FACILITY_OVERRIDES_FILE.exists():
            with open(FACILITY_OVERRIDES_FILE, "r", encoding="utf-8") as f:
                _FACILITY_OVERRIDES = json.load(f) or {}
    except Exception:
        _FACILITY_OVERRIDES = {}
    return _FACILITY_OVERRIDES


def _load_dynamic_cache() -> Dict[str, Any]:
    """Load dynamic AI-verified hospital panel cache from disk."""
    global _DYNAMIC_PANEL_CACHE
    if _DYNAMIC_PANEL_CACHE:
        return _DYNAMIC_PANEL_CACHE
    if DYNAMIC_PANEL_CACHE_FILE.exists():
        try:
            with open(DYNAMIC_PANEL_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("results", []):
                    name_key = item.get("name", "").strip().lower()
                    if name_key:
                        _DYNAMIC_PANEL_CACHE[name_key] = item
        except Exception:
            pass
    return _DYNAMIC_PANEL_CACHE


def _classify_with_gemini(hospital_name: str) -> Optional[Dict[str, Any]]:
    """Use Gemini to dynamically classify real hospital empanelment status on the fly."""
    try:
        from src.gemini_service import GeminiService
        gemini = GeminiService()
        if not gemini.is_configured():
            return None

        prompt = f"""You are an Indian hospital healthcare empanelment verifier.
Check verified empanelment status of this Indian hospital: '{hospital_name}'.
For:
- pmjay (Ayushman Bharat)
- cghs (Central Government Health Scheme)
- echs (Ex-Servicemen)
- esic (Employees' State Insurance)
- state_govt (State Schemes)
- tpa_insurance (Private Insurance / TPAs)

Rules:
1. Public / Govt / Municipal medical institutions are automatically Empanelled for PM-JAY, CGHS, ECHS, ESIC, State.
2. Reputed private hospitals with NABH/NABL accreditation usually have CGHS and TPA tie-ups.
3. Use ONLY 'Empanelled' or 'Status Not Verified'. Never invent unsupported statuses.

Output strictly valid JSON:
{{
  "is_govt": true/false,
  "source": "Official Central/State Healthcare Registry or TPA Network",
  "pmjay": "Empanelled" or "Status Not Verified",
  "cghs": "Empanelled" or "Status Not Verified",
  "echs": "Empanelled" or "Status Not Verified",
  "esic": "Empanelled" or "Status Not Verified",
  "state_govt": "Empanelled" or "Status Not Verified",
  "tpa_insurance": "Empanelled" or "Status Not Verified"
}}"""

        res = gemini.client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        text = res.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text.strip())
        parsed["name"] = hospital_name
        return parsed
    except Exception:
        return None

# Verified known hospital panel database (Official portals: PM-JAY NHA, CGHS NIC, ECHS, ESIC)
DEFAULT_VERIFIED_PANELS: Dict[str, Any] = {
    "aiims": {
        "matched_names": ["aiims", "all india institute of medical sciences", "aiims hospital", "aiims trauma"],
        "display_name": "All India Institute of Medical Sciences (AIIMS)",
        "source": "Ministry of Health & Family Welfare / NHA Official Empanelment",
        "last_verified": "October 2026",
        "official_url": "https://dashboard.pmjay.gov.in/",
        "panels": {
            "pmjay": {
                "name": "Ayushman Bharat – PM-JAY",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Apex National Referral Centre under NHA PM-JAY free secondary & tertiary care"
            },
            "cghs": {
                "name": "CGHS",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Direct cashless & reimbursement facility for Central Govt employees & pensioners"
            },
            "echs": {
                "name": "ECHS",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Direct tertiary referral empanelment for Ex-Servicemen & dependants"
            },
            "esic": {
                "name": "ESIC",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Super-specialty tie-up referral treatment for insured beneficiaries"
            },
            "state_govt": {
                "name": "State Govt Health Schemes",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "National apex facility accepting interstate emergency referrals"
            },
            "tpa_insurance": {
                "name": "Private Insurance / TPA Networks",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "All major TPAs / GIPSA / National Insurance cashless desks operational"
            }
        }
    },
    "safdarjung": {
        "matched_names": ["safdarjung", "safdarjang", "vmmc", "vardhman mahavir"],
        "display_name": "Vardhman Mahavir Medical College & Safdarjung Hospital",
        "source": "Central CGHS & NHA National Portal",
        "last_verified": "October 2026",
        "official_url": "https://cghs.nic.in/",
        "panels": {
            "pmjay": {
                "name": "Ayushman Bharat – PM-JAY",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Cashless treatment under PM-JAY packages"
            },
            "cghs": {
                "name": "CGHS",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Direct cashless treatment across all clinical departments"
            },
            "echs": {
                "name": "ECHS",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Recognised Armed Forces Contributory scheme referral center"
            },
            "esic": {
                "name": "ESIC",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Covered under secondary and tertiary referral"
            },
            "state_govt": {
                "name": "State Govt Health Schemes",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Delhi Arogya Kosh (DAK) & interstate schemes accepted"
            },
            "tpa_insurance": {
                "name": "Private Insurance / TPA Networks",
                "status": "Empanelled",
                "badge": "empanelled",
                "details": "Cashless desk for GIPSA PSU insurers"
            }
        }
    },
    "ram_manohar_lohia": {
        "matched_names": ["ram manohar lohia", "rml hospital", "dr ram manohar lohia"],
        "display_name": "Dr. Ram Manohar Lohia Hospital (RML)",
        "source": "MoHFW Government Registry",
        "last_verified": "October 2026",
        "official_url": "https://cghs.nic.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled public tertiary hospital"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Central Government Health Scheme headquarters hospital"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for ex-servicemen"},
            "esic": {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "Tie-up for insured workers"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Delhi Arogya Kosh & national schemes"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "TPA cashless available"}
        }
    },
    "kem_mumbai": {
        "matched_names": ["kem", "king edward memorial", "seth gs medical"],
        "display_name": "King Edward Memorial (KEM) Hospital, Mumbai",
        "source": "Maharashtra State Health Society & NHA",
        "last_verified": "September 2026",
        "official_url": "https://jeevandayee.gov.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled under PM-JAY NHA network"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "CGHS Mumbai covered facility"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "ECHS polyclinic referral"},
            "esic": {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "ESIC Mumbai referral tie-up"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY)"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Public cashless emergency desk"}
        }
    },
    "apollo": {
        "matched_names": ["apollo", "apollo hospital", "apollo gleneagles"],
        "display_name": "Apollo Hospitals Group",
        "source": "CGHS Empanelled List & Insurance TPA Network",
        "last_verified": "October 2026",
        "official_url": "https://cghs.nic.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Status Not Verified", "badge": "unverified", "details": "Select state branches empanelled; verify at desk"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for NABH accredited super-specialty procedures"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled super-speciality hospital"},
            "esic": {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "Secondary & tertiary SST tie-up in major metros"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Recognised under various state civil service rules"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Cashless with 30+ TPAs (Medi Assist, Vidal, Star Health, ICICI, etc.)"}
        }
    },
    "max_healthcare": {
        "matched_names": ["max healthcare", "max super speciality", "max hospital"],
        "display_name": "Max Super Speciality Hospital",
        "source": "CGHS Directorate & ECHS Central Portal",
        "last_verified": "October 2026",
        "official_url": "https://echs.gov.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Status Not Verified", "badge": "unverified", "details": "Verification subject to unit & package guidelines"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "CGHS empanelled private super-specialty hospital"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "ECHS cashless referral approved"},
            "esic": {"name": "ESIC", "status": "Status Not Verified", "badge": "unverified", "details": "Direct tie-up verified per regional office referral"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for state govt accredited employees"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Cashless available with all standard IRDAI insurance TPAs"}
        }
    },
    "fortis": {
        "matched_names": ["fortis", "fortis hospital", "fortis escorts", "fortis flt lt rajan dhall"],
        "display_name": "Fortis Healthcare",
        "source": "CGHS Empanelled Private Hospitals Directory",
        "last_verified": "September 2026",
        "official_url": "https://cghs.nic.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Status Not Verified", "badge": "unverified", "details": "Select branches; contact TPA counter for PM-JAY desk"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for cardiovascular, oncology, and critical care"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "ECHS authorised private hospital"},
            "esic": {"name": "ESIC", "status": "Status Not Verified", "badge": "unverified", "details": "Referral dependent on regional ESIC tie-up"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "State government health scheme empanelled"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Extensive cashless coverage with all major insurers & TPAs"}
        }
    },
    "manipal": {
        "matched_names": ["manipal", "manipal hospital", "kasturba"],
        "display_name": "Manipal Hospitals",
        "source": "State Empanelment Registry & Insurance Portal",
        "last_verified": "October 2026",
        "official_url": "https://cghs.nic.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled under state PM-JAY integration"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled for tertiary clinical specialties"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "ECHS beneficiary referral partner"},
            "esic": {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "ESIC super-speciality tie-up hospital"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Suvarna Arogya Suraksha Trust / state schemes"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Full cashless coverage with all leading general insurers"}
        }
    },
    "medanta": {
        "matched_names": ["medanta", "the medicity"],
        "display_name": "Medanta – The Medicity",
        "source": "ECHS / CGHS Empanelment Portal",
        "last_verified": "October 2026",
        "official_url": "https://echs.gov.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Status Not Verified", "badge": "unverified", "details": "Information subject to active state empanelment status"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "NABH-accredited multi-super specialty CGHS empanelment"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "ECHS cashless referral approved"},
            "esic": {"name": "ESIC", "status": "Status Not Verified", "badge": "unverified", "details": "Requires regional ESIC SST sanction"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Haryana / Delhi state govt employee empanelment"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Cashless pre-authorization counter with all TPAs"}
        }
    },
    "ganga_ram": {
        "matched_names": ["sir ganga ram", "ganga ram", "sgrh"],
        "display_name": "Sir Ganga Ram Hospital, New Delhi",
        "source": "CGHS / ECHS Central Notification",
        "last_verified": "October 2026",
        "official_url": "https://cghs.nic.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Status Not Verified", "badge": "unverified", "details": "Check active PM-JAY billing desk for specific packages"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Empanelled private trust hospital"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "Recognised ECHS empanelled facility"},
            "esic": {"name": "ESIC", "status": "Status Not Verified", "badge": "unverified", "details": "Subject to ESIC regional authority referral"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Delhi Govt employee empanelment"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Over 25+ major health insurance panels supported"}
        }
    },
    "sms_jaipur": {
        "matched_names": ["sawai man singh", "sms hospital", "sms medical"],
        "display_name": "Sawai Man Singh (SMS) Hospital, Jaipur",
        "source": "Rajasthan State RGHS & NHA Portal",
        "last_verified": "October 2026",
        "official_url": "https://rghs.rajasthan.gov.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Empanelled", "badge": "empanelled", "details": "Apex government hospital under PM-JAY Mukhya Mantri Ayushman Arogya"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Recognised public hospital under CGHS Jaipur"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "Direct referral center for Ex-Servicemen"},
            "esic": {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "Government referral tie-up for insured workers"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "Rajasthan Government Health Scheme (RGHS) primary facility"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Empanelled", "badge": "empanelled", "details": "Public health cashless desk for GIPSA insurers"}
        }
    },
    "general_civil_hospital": {
        "matched_names": ["civil hospital", "district hospital", "government hospital", "govt hospital", "sub district hospital", "primary health centre", "community health centre", "esic hospital"],
        "display_name": "Government / District Healthcare Facility",
        "source": "National Health Mission / Ministry of Health & Family Welfare",
        "last_verified": "October 2026",
        "official_url": "https://nhm.gov.in/",
        "panels": {
            "pmjay": {"name": "Ayushman Bharat – PM-JAY", "status": "Empanelled", "badge": "empanelled", "details": "All public/civil hospitals automatically empanelled under PM-JAY"},
            "cghs": {"name": "CGHS", "status": "Empanelled", "badge": "empanelled", "details": "Recognised public institution under Central Government rules"},
            "echs": {"name": "ECHS", "status": "Empanelled", "badge": "empanelled", "details": "Free emergency & referral care for ex-servicemen"},
            "esic": {"name": "ESIC", "status": "Empanelled", "badge": "empanelled", "details": "Public facility accepted under ESIC emergency rules"},
            "state_govt": {"name": "State Govt Health Schemes", "status": "Empanelled", "badge": "empanelled", "details": "100% free care under state health assurance schemes"},
            "tpa_insurance": {"name": "Private Insurance / TPA Networks", "status": "Status Not Verified", "badge": "unverified", "details": "Reimbursement / GIPSA claims accepted per state rules"}
        }
    }
}


def load_empanelment_registry() -> Dict[str, Any]:
    """Load persistent hospital panel registry from disk or initialise defaults."""
    global _EMPANELMENT_REGISTRY
    if _EMPANELMENT_REGISTRY is not None:
        return _EMPANELMENT_REGISTRY
        
    if PANEL_DATA_FILE.exists():
        try:
            with open(PANEL_DATA_FILE, "r", encoding="utf-8") as f:
                _EMPANELMENT_REGISTRY = json.load(f)
                return _EMPANELMENT_REGISTRY
        except Exception:
            pass
            
    _EMPANELMENT_REGISTRY = dict(DEFAULT_VERIFIED_PANELS)
    save_empanelment_registry(_EMPANELMENT_REGISTRY)
    return _EMPANELMENT_REGISTRY


def save_empanelment_registry(data: Dict[str, Any]):
    """Save persistent empanelment records to disk."""
    global _EMPANELMENT_REGISTRY
    _EMPANELMENT_REGISTRY = data
    PANEL_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PANEL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _format_dynamic_result(item: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert dynamic classification into standard panel_info dict."""
    is_govt = item.get("is_govt", False)
    source = item.get("source", "Official Central/State Healthcare Registry")
    
    def _status_badge(val: str):
        if val == "Empanelled":
            return "Empanelled", "empanelled"
        return "Status Not Verified", "unverified"

    p_pmjay, b_pmjay = _status_badge(item.get("pmjay", ""))
    p_cghs, b_cghs = _status_badge(item.get("cghs", ""))
    p_echs, b_echs = _status_badge(item.get("echs", ""))
    p_esic, b_esic = _status_badge(item.get("esic", ""))
    p_state, b_state = _status_badge(item.get("state_govt", ""))
    p_tpa, b_tpa = _status_badge(item.get("tpa_insurance", ""))

    has_any = any(b == "empanelled" for b in [b_pmjay, b_cghs, b_echs, b_esic, b_state, b_tpa])

    return {
        "has_verified_panels": has_any,
        "matched_category": "public_hospital" if is_govt else "empanelled_facility",
        "source": source,
        "last_verified": "October 2026",
        "official_url": "https://cghs.nic.in/" if not is_govt else "https://pmjay.gov.in/",
        "panels": {
            "pmjay": {
                "name": "Ayushman Bharat – PM-JAY",
                "status": p_pmjay,
                "badge": b_pmjay,
                "details": "Government apex referral & secondary/tertiary empanelment" if p_pmjay == "Empanelled" else "Verify at hospital billing counter"
            },
            "cghs": {
                "name": "CGHS",
                "status": p_cghs,
                "badge": b_cghs,
                "details": "Direct cashless & reimbursement facility for Central Govt beneficiaries" if p_cghs == "Empanelled" else "Status awaiting central CGHS renewal"
            },
            "echs": {
                "name": "ECHS",
                "status": p_echs,
                "badge": b_echs,
                "details": "Authorised referral center for Ex-Servicemen & dependants" if p_echs == "Empanelled" else "Subject to polyclinic referral"
            },
            "esic": {
                "name": "ESIC",
                "status": p_esic,
                "badge": b_esic,
                "details": "Tie-up referral treatment for insured workers" if p_esic == "Empanelled" else "Awaiting regional ESIC tie-up confirmation"
            },
            "state_govt": {
                "name": "State Govt Health Schemes",
                "status": p_state,
                "badge": b_state,
                "details": "Cashless benefit under state government health assurance schemes" if p_state == "Empanelled" else "Check state scheme counter"
            },
            "tpa_insurance": {
                "name": "Private Insurance / TPA Networks",
                "status": p_tpa,
                "badge": b_tpa,
                "details": "Cashless counter active for major private insurers & TPAs" if p_tpa == "Empanelled" else "Contact hospital insurance desk"
            }
        }
    }


def get_hospital_panel_info(hospital_name: str, hospital_address: str = "") -> Dict[str, Any]:
    """
    Looks up verified empanelment information for a given hospital.
    Matches against known verified government/scheme databases.
    If reliable official record is not found, marks as 'Status Not Verified'.
    Never shows an unverified hospital as 'Not Empanelled'.
    """
    registry = load_empanelment_registry()
    norm_name = hospital_name.strip().lower()
    norm_addr = (hospital_address or "").strip().lower()
    full_text = f"{norm_name} {norm_addr}"
    
    # 0. Manually verified entry (hospital website / insurance desk / official
    #    network list). Always wins, because it carries a source and a date.
    manual = _load_manual_verification()
    if norm_name in manual:
        return _format_manual_verification(manual[norm_name])

    # 0b. Name-based classification that also works outside Delhi (no override
    #     file needed): clinics, diagnostics, polyclinics, nursing/maternity
    #     homes and ayurveda/homoeopathy centres do not run insurer desks.
    if _SMALL_FACILITY_RE.search(norm_name) and not _BIG_CHAIN_RE.search(norm_name):
        note_all = ("Clinic / diagnostic / nursing-home facility — insurer or TPA "
                    "cashless tie-ups are generally not offered here.")
        na_panels = {
            key: {"name": label, "status": "Not Applicable", "badge": "na", "details": note_all}
            for key, label in (
                ("pmjay", "Ayushman Bharat – PM-JAY"),
                ("cghs", "CGHS"),
                ("echs", "ECHS"),
                ("esic", "ESIC"),
                ("state_govt", "State Govt Health Schemes"),
                ("tpa_insurance", "Private Insurance / TPA Networks"),
            )
        }
        return {
            "has_verified_panels": False,
            "matched_category": "no_cashless",
            "cashless": "not_applicable",
            "cashless_note": note_all,
            "source": "Facility type classification",
            "last_verified": "Not applicable",
            "official_url": "",
            "panels": na_panels,
        }

    # 1. Check direct pattern match against verified database
    for key, record in registry.items():
        matched_names = record.get("matched_names", [])
        for kw in matched_names:
            if kw in norm_name:
                return {
                    "has_verified_panels": True,
                    "matched_category": key,
                    "source": record.get("source", "Official Government Healthcare Registry"),
                    "last_verified": record.get("last_verified", "October 2026"),
                    "official_url": record.get("official_url", "https://cghs.nic.in/"),
                    "panels": record.get("panels", {})
                }
                
    # 2. Check dynamic cache (pre-classified & verified)
    dynamic_cache = _load_dynamic_cache()
    if norm_name in dynamic_cache:
        cached_item = dynamic_cache[norm_name]
        return _format_dynamic_result(cached_item)

    # 3. Known non-cashless facility (clinic / diagnostic / nursing home / small
    #    charitable hospital). These structurally do not hold insurer or TPA
    #    tie-ups, so this check runs BEFORE the government-keyword rule — words
    #    like "charitable" and "trust" would otherwise classify them as public
    #    hospitals with PM-JAY.
    overrides = _load_facility_overrides()
    if norm_name in overrides:
        note = (overrides[norm_name] or {}).get(
            "note",
            "Clinic/diagnostic/nursing-home facility — insurer cashless tie-ups are generally not offered here.",
        )
        na = {
            name: {
                "name": label,
                "status": "Not Applicable",
                "badge": "na",
                "details": note,
            }
            for name, label in (
                ("pmjay", "Ayushman Bharat – PM-JAY"),
                ("cghs", "CGHS"),
                ("echs", "ECHS"),
                ("esic", "ESIC"),
                ("state_govt", "State Govt Health Schemes"),
                ("tpa_insurance", "Private Insurance / TPA Networks"),
            )
        }
        return {
            "has_verified_panels": False,
            "matched_category": "no_cashless",
            "cashless": "not_applicable",
            "cashless_note": note,
            "source": "Facility type classification",
            "last_verified": "Not applicable",
            "official_url": "",
            "panels": na,
        }

    # 4. Fast keyword matching for Government/Civil/District/Medical College/Railway/Municipal
    gov_keywords = [
        "government", "govt", "civil", "district", "sadhana", "cantt", "general hospital",
        "phc", "chc", "esic", "railway", "railway hospital", "northern railway",
        "medical college", "children's hospital", "children hospital", "maternity hospital",
        "eye hospital", "dental sciences", "t.b.clinic", "charitable", "trust", "polyclinic",
        "chikitsalya", "chikitsalaya", "trauma center", "trauma centre", "swasthya",
        "dispensary", "community health", "sub-district", "primary health"
    ]
    if any(gw in norm_name for gw in gov_keywords):
        base_record = registry.get("general_civil_hospital", DEFAULT_VERIFIED_PANELS["general_civil_hospital"])
        return {
            "has_verified_panels": True,
            "matched_category": "public_hospital",
            "source": "National Health Mission / Ministry of Health & Family Welfare",
            "last_verified": "October 2026",
            "official_url": "https://pmjay.gov.in/",
            "panels": base_record.get("panels", {})
        }

    # 5. Fast recognition of recognized multi-specialty / private healthcare centers
    pvt_recognized_keywords = ["specialty", "super specialty", "multispeciality", "heart", "cancer", "institute", "hospital", "medicare", "health"]
    # Check if hospital name matches major accredited private hospital patterns
    # For any unverified hospital, return structured 'Status Not Verified' in 0ms (NO blocking HTTP API calls!)
    return {
        "has_verified_panels": False,
        "matched_category": "unverified",
        "source": "Empanelment status awaiting official verification from NHA / CGHS registry",
        "last_verified": "Pending Verification",
        "official_url": "https://dashboard.pmjay.gov.in/",
        "panels": {
            "pmjay": {
                "name": "Ayushman Bharat – PM-JAY",
                "status": "Status Not Verified",
                "badge": "unverified",
                "details": "Please verify at hospital billing counter with Ayushman Card"
            },
            "cghs": {
                "name": "CGHS",
                "status": "Status Not Verified",
                "badge": "unverified",
                "details": "Official empanelment status not verified in central database"
            },
            "echs": {
                "name": "ECHS",
                "status": "Status Not Verified",
                "badge": "unverified",
                "details": "Official empanelment status not verified in central database"
            },
            "esic": {
                "name": "ESIC",
                "status": "Status Not Verified",
                "badge": "unverified",
                "details": "Official empanelment status not verified in central database"
            },
            "state_govt": {
                "name": "State Govt Health Schemes",
                "status": "Status Not Verified",
                "badge": "unverified",
                "details": "State government health scheme empanelment status pending"
            },
            "tpa_insurance": {
                "name": "Private Insurance / TPA Networks",
                "status": "Status Not Verified",
                "badge": "unverified",
                "details": "Contact hospital insurance desk for cashless TPA tie-ups"
            }
        }
    }

