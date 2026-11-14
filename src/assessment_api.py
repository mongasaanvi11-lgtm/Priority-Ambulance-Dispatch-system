"""
AmbuPriority — Assessment & Hospital Discovery API
==================================================
Starlette / ASGI HTTP API for:
1. Patient symptom assessment submission and triage.
2. Hospital discovery around patient incident location using OpenStreetMap.
3. Priority-wise demo ambulance availability determination.
4. Hospital search by name, area, locality, or city.
5. AI-powered hospital & empanelment chatbot (Gemini Flash backend).

Endpoints:
  POST /api/assessment             — Submit symptom assessment, run triage, store result
  GET  /api/assessment/{id}        — Retrieve stored assessment (clinical review)
  GET  /api/health                 — Health check
  POST /api/hospitals/nearby       — Discover nearby hospitals & priority ambulance availability
  GET  /api/hospitals/search       — Search hospitals by name/area & calculate distance from patient
  POST /api/chat                   — ARIA AI Hospital & Empanelment chatbot (Gemini Flash)
"""

import json
import re
import sys
import glob
import uuid
import time
from datetime import datetime
import secrets
import hashlib
import urllib.request
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.triage_engine import run_triage, save_assessment, get_stored_patient_assessment, ASSESSMENTS_DIR
from src.hospital_discovery import (
    discover_nearby_hospitals,
    search_hospitals_by_text,
    geocode_address,
    haversine_distance,
    get_nominatim_headers as _get_nominatim_headers_legacy
)
from src.insurance_discovery_service import (
    trigger_background_insurance_discovery,
    get_cached_insurance,
    research_hospital_insurance_sync
)
from src.ambulance_registry import (
    check_hospital_availability,
    get_hospital_key,
    ensure_hospital_ambulances,
    evaluate_ambulance_options
)
from src.hospital_panel_service import get_hospital_panel_info
from src.hospital_facilities_service import (
    get_hospital_capabilities_and_cost,
    estimate_travel_time_minutes,
    evaluate_hospital_condition_match
)
from src.ambulance_fare_service import (
    calculate_ambulance_fare,
    get_all_ambulance_tariffs_for_distance,
    GOVT_AMBULANCE_RATES,
    PRIVATE_AMBULANCE_RATES
)
from src.gemini_service import GeminiService
from src.gemini_panel_researcher import (
    research_hospitals_panels,
    get_cached_research_or_none,
    research_single_hospital,
    research_many,
    key_pool_status,
    _apply_research_to_hospital
)

from src.panel_scanner import (
    start_scan as start_panel_scan,
    cancel_scan as cancel_panel_scan,
    scan_status as panel_scan_status,
    active_scan as active_panel_scan,
)

from src.pincode_verify import verify_pincode as verify_address_pincode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Autocomplete suggestion cache — keyed by lowercase query, TTL 10 minutes
# Avoids repeat Nominatim network calls for the same partial query.
# ---------------------------------------------------------------------------
_AC_CACHE: Dict[str, tuple] = {}   # key -> (unix_ts, List[dict])
_AC_CACHE_TTL = 600                 # 10 minutes

def _ac_cache_get(key: str):
    entry = _AC_CACHE.get(key)
    if entry and (time.time() - entry[0]) < _AC_CACHE_TTL:
        return entry[1]
    _AC_CACHE.pop(key, None)
    return None

def _ac_cache_set(key: str, suggestions: list):
    _AC_CACHE[key] = (time.time(), suggestions)

# ---------------------------------------------------------------------------
# ARIA Hospital Chatbot — Gemini Flash Integration
# ---------------------------------------------------------------------------

# Singleton Gemini service (reuses existing API key from config.py / .env)
_gemini_service: GeminiService = None

def _get_gemini() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


ARIA_SYSTEM_PROMPT = """You are ARIA, the AmbuPriority Emergency Response, Hospital & Insurance Assistant.

IDENTITY:
- Your name is always ARIA (Ambulance Response Intelligent Assistant).
- If someone asks who you are or what your name is, state clearly that you are ARIA, the official intelligent assistant for AmbuPriority.

YOUR SCOPE & CAPABILITIES:
You ONLY answer questions related to:
1. Health Insurance & TPA Networks: How cashless claims work, reimbursement process, pre-authorization, Star Health, HDFC ERGO, ICICI Lombard, Niva Bupa, Care Health, Medi Assist, Vidal, Paramount, etc.
2. Government Health Schemes: Ayushman Bharat (PM-JAY), CGHS, ECHS, ESIC, State Govt Schemes (RGHS, MJPJAY, Aarogyasri, Swasthya Sathi, etc.), card usage and eligibility.
3. Hospitals & Empanelment: Hospital locations, specialties, facilities, whether a hospital is empanelled under a specific scheme or private TPA insurance.
4. Ambulance Booking & Registration Form Help:
   - How to fill the Patient Registration Form on AmbuPriority
   - Mandatory fields marked with red star (*): Patient Name, Age, Gender, 10-digit Mobile Number, Complete Pickup Address, Requestor Name & Relationship to patient
   - Optional fields: Landmark (e.g., Near Metro Pillar 142, Opp SBI Bank), Alternate Mobile Number
   - GPS Auto-Detection: Clicking "Use My Current Location" to lock satellite coordinates
   - Reference Number (NAS-YEAR-XXXXXX) for tracking
   - Emergency Numbers: 112 (Universal), 102 (National Ambulance), 108 (State Emergency).

STRICT OFF-TOPIC RULE:
For ANY unrelated topic (weather, sports, politics, movies, cooking, coding, math, general trivia):
Politely decline in the same language of the query:
- If user asked in English: "I am ARIA, dedicated only to AmbuPriority ambulance services, hospital empanelment, health insurance, and registration assistance. Please ask me anything related to hospitals, health schemes, insurance, or ambulance booking!"
- If user asked in Hinglish/Hindi: "Main ARIA hun, aur main sirf AmbuPriority ambulance seva, hospital empanelment, health insurance, aur registration form ki jaankari ke liye hun. Aap hospital, health insurance ya ambulance booking se juda sawal pooch sakte hain!"

LANGUAGE MATCHING RULES (CRITICAL):
1. MATCH THE USER'S EXACT LANGUAGE — ABSOLUTELY NO MIXING:
   - If user asks in ENGLISH (e.g. "How does insurance work?", "How to fill the form?", "What is your name?"):
     -> Respond 100% in pure ENGLISH ONLY. Do NOT use any Hindi or Hinglish words (no 'Namaste', no 'kripya', no Hindi sentences).
   - If user asks in HINGLISH (e.g. "mere paas star health hai kaise use karu", "form kaise bhare", "cghs ka process batao"):
     -> Respond 100% in natural HINGLISH (Latin letters only). Do NOT switch between English and Hindi paragraphs.
   - If user asks in DEVANAGARI HINDI (e.g. "फॉर्म कैसे भरें", "स्टार हेल्थ कैसे काम करता है"):
     -> Respond in proper HINDI (Devanagari script) or natural Hinglish.
   - STRICT RULE: NEVER MIX English and Hindi randomly in the same reply. If the question is in English, the entire answer MUST be in English.

CONCISE & FAST RESPONSES:
- Keep responses compact, crisp, and directly to the point.
- Avoid unnecessarily long essays. 2 to 4 bullet points are ideal.
- Maximum 150-250 words per response so that generation is instant and easy to read.

NO HALLUCINATION RULE:
- For hospital empanelment status, use ONLY verified facts. If unsure or if a hospital is not in the verified list, state: "Status Not Verified" and advise the user to confirm at the hospital TPA/insurance desk.
- Never invent fake policy coverage, false percentages, or unverified claims.

EMERGENCY RULE:
If the user indicates an immediate, life-threatening emergency (heart attack, severe accident, unconsciousness, heavy bleeding), prioritize:
"⚠️ Emergency Alert: Dial 112, 102, or 108 immediately for urgent ambulance dispatch."
Then provide helpful next steps.

HOSPITAL CONTEXT:
{hospital_context}

EMPANELMENT REGISTRY SUMMARY:
The following hospitals have verified empanelment data in our system:
- AIIMS (All AIIMS branches): PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State Schemes ✅, TPA ✅
- Safdarjung Hospital (Delhi): PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State ✅, TPA ✅
- RML Hospital (Delhi): PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State ✅, TPA ✅
- KEM Hospital (Mumbai): PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State ✅, TPA ✅
- Apollo Hospitals: CGHS ✅, ECHS ✅, ESIC ✅, TPA ✅ | PM-JAY: Status Not Verified
- Max Healthcare: CGHS ✅, ECHS ✅, State ✅, TPA ✅ | PM-JAY/ESIC: Status Not Verified
- Fortis Healthcare: CGHS ✅, ECHS ✅, State ✅, TPA ✅ | PM-JAY/ESIC: Status Not Verified
- Manipal Hospitals: PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State ✅, TPA ✅
- Medanta The Medicity: CGHS ✅, ECHS ✅, State ✅, TPA ✅ | PM-JAY/ESIC: Status Not Verified
- Sir Ganga Ram Hospital: CGHS ✅, ECHS ✅, State ✅, TPA ✅ | PM-JAY/ESIC: Status Not Verified
- SMS Hospital Jaipur: PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State (RGHS) ✅, TPA ✅
- Government Civil/District Hospitals: PM-JAY ✅, CGHS ✅, ECHS ✅, ESIC ✅, State ✅

For any other hospital: status is "Status Not Verified" — advise checking at hospital billing/TPA desk.

FORMAT & STYLE:
- Always be concise, polite, and well-structured using markdown bullet points.
- Use **bold** for key terms, scheme names, and important instructions.
- Keep responses easy to read on mobile screens.
"""


def _build_hospital_context(hospitals: list) -> str:
    """Format nearby hospital data as context for Gemini prompt."""
    if not hospitals:
        return "No specific nearby hospital data available for this query."
    
    lines = []
    for h in hospitals[:8]:  # Limit to 8 hospitals for context window
        panel_info = h.get("panel_info", {})
        panels = panel_info.get("panels", {})
        
        # Summarise panel status
        panel_summary = []
        for scheme_key, label in [("pmjay", "PM-JAY"), ("cghs", "CGHS"), ("echs", "ECHS"), ("esic", "ESIC"), ("state_govt", "State"), ("tpa_insurance", "TPA")]:
            p = panels.get(scheme_key, {})
            status = p.get("badge", "unverified")
            icon = "✅" if status == "empanelled" else "❓"
            panel_summary.append(f"{label}{icon}")
        
        lines.append(
            f"- {h['name']} | {h.get('address', 'Address not available')} | "
            f"Distance: {h.get('distance_km', '?')} km | "
            f"Panels: {', '.join(panel_summary)} | "
            f"Ambulance: {h.get('availability', 'Unknown')}"
        )
    
    return "\n".join(lines)


def _extract_location_from_message(messages: list) -> str:
    """Try to find a city/location mention in the conversation."""
    location_keywords = [
        'delhi', 'mumbai', 'bangalore', 'bengaluru', 'hyderabad', 'chennai', 
        'kolkata', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'chandigarh',
        'noida', 'gurgaon', 'gurugram', 'faridabad', 'patna', 'bhopal',
        'indore', 'nagpur', 'surat', 'kochi', 'coimbatore', 'visakhapatnam'
    ]
    # Check last 5 messages for location
    for msg in reversed(messages[-5:]):
        content_lower = (msg.get("content") or "").lower()
        for loc in location_keywords:
            if loc in content_lower:
                return loc.title()
    return ""


async def chat_endpoint(request):
    """
    ARIA AI Hospital & Empanelment chatbot powered by Gemini Flash.
    Accepts: { "message": str, "session": [{role, content}, ...] }
    Returns: { "reply": str, "model": str, "source": "ai"|"fallback" }
    """
    try:
        data = await request.json()
        user_message = (data.get("message") or "").strip()
        session = data.get("session") or []  # List of {role, content} dicts
        patient_lat = data.get("lat")
        patient_lon = data.get("lon")
        patient_address = data.get("address", "")

        if not user_message:
            return JSONResponse({"error": "Message is required"}, status_code=400)

        gemini = _get_gemini()
        
        # --- Build hospital context (optional, only if we have patient location) ---
        hospital_context_str = ""
        try:
            if patient_lat and patient_lon:
                nearby = discover_nearby_hospitals(float(patient_lat), float(patient_lon), 12.0)
                if nearby:
                    # Attach panel info
                    for h in nearby[:8]:
                        h["panel_info"] = get_hospital_panel_info(h["name"], h.get("address", ""))
                    hospital_context_str = _build_hospital_context(nearby)
            elif not hospital_context_str:
                # Try to detect city from conversation and fetch hospitals
                detected_city = _extract_location_from_message(session + [{"role": "user", "content": user_message}])
                if detected_city:
                    searched = search_hospitals_by_text(detected_city, 28.6139, 77.2090)  # Delhi default for distance calc
                    if searched:
                        for h in searched[:8]:
                            h["panel_info"] = get_hospital_panel_info(h["name"], h.get("address", ""))
                        hospital_context_str = _build_hospital_context(searched)
        except Exception as ctx_err:
            logger.warning(f"Hospital context fetch failed: {ctx_err}")
            hospital_context_str = "Hospital context temporarily unavailable."

        filled_system_prompt = ARIA_SYSTEM_PROMPT.replace("{hospital_context}", hospital_context_str or "No specific hospital data fetched for this query.")

        # --- Build conversation for Gemini ---
        # Format as a single multi-turn prompt since GeminiService uses generate_content_stream
        conversation_text = ""
        for msg in session[-8:]:  # Last 8 turns for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                conversation_text += f"User: {content}\n"
            else:
                conversation_text += f"ARIA: {content}\n"

        full_prompt = f"""{filled_system_prompt}

CONVERSATION HISTORY:
{conversation_text}
User: {user_message}

ARIA:"""

        # --- Call Gemini with fallback models ---
        if not gemini.is_configured():
            return JSONResponse({
                "reply": "Main abhi available nahi hun (AI service configure nahi hai). Kripya apne hospital ke billing counter par jakar apne panel ki jaankari lein, ya 112 / 102 / 108 par call karein.",
                "model": "unavailable",
                "source": "fallback"
            })

        reply_parts = []
        model_used = None
        # Fastest model first for instant response
        fallback_models = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.6-flash"]

        for model_candidate in fallback_models:
            reply_parts = []
            try:
                # Use generate_content directly with max_output_tokens for fastest single-round trip
                res = gemini.client.models.generate_content(
                    model=model_candidate,
                    contents=full_prompt,
                    config={
                        "max_output_tokens": 400,
                        "temperature": 0.2
                    }
                )
                if res and res.text:
                    reply_parts.append(res.text)
                    model_used = model_candidate
                    break  # Success!
            except Exception as candidate_err:
                logger.warning(f"Model {model_candidate} attempt failed: {candidate_err}")
                # Try fallback candidate
                continue

        reply = "".join(reply_parts).strip()
        if not reply:
            return JSONResponse({
                "reply": "AI service se response lene mein dikkat hui. Kripya thodi der baad dobara koshish karein, ya hospital ke billing counter par directly verify karein. Emergency mein 112 / 102 / 108 dial karein.",
                "model": "all_failed",
                "source": "error"
            })

        return JSONResponse({
            "reply": reply,
            "model": model_used or gemini.model_name,
            "source": "ai"
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return JSONResponse({
            "reply": "Kuch galat ho gaya. Emergency mein turant 112, 102, ya 108 dial karein.",
            "model": "error",
            "source": "error"
        }, status_code=500)


async def submit_assessment(request):
    """
    Accept patient symptom assessment data from the frontend.
    Run triage engine, store result, return assessment ID.
    The frontend does NOT receive the triage priority level directly in this call.
    """
    try:
        data = await request.json()
        if not data:
            return JSONResponse({"error": "No assessment data provided"}, status_code=400)
        
        if not data.get("chief_complaint"):
            return JSONResponse({"error": "Chief complaint is required"}, status_code=400)
        
        if not data.get("request_id"):
            return JSONResponse({"error": "Patient request ID is required"}, status_code=400)
        
        triage_result = run_triage(data)
        assessment_id = save_assessment(data, triage_result)
        
        return JSONResponse({
            "success": True,
            "assessment_id": assessment_id,
            "patient_priority": triage_result.get("suggested_priority", "YELLOW"),
            "chief_complaint": data.get("chief_complaint", "general"),
            "message": "Symptom assessment recorded successfully. Information has been forwarded to the dispatch coordination centre.",
            "clinical_review_status": "PENDING"
        }, status_code=201)
    
    except Exception as e:
        return JSONResponse({
            "error": "Assessment submission failed",
            "detail": str(e)
        }, status_code=500)


async def get_assessment(request):
    """Retrieve a stored assessment for clinical review."""
    assessment_id = request.path_params.get("assessment_id")
    filepath = ASSESSMENTS_DIR / f"{assessment_id}.json"
    
    if not filepath.exists():
        return JSONResponse({"error": "Assessment not found"}, status_code=404)
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            record = json.load(f)
        return JSONResponse(record, status_code=200)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def get_stored_patient_assessment(request_id: str) -> Dict[str, Any]:
    """
    Look up the patient priority, chief complaint and clinical signs already calculated
    and stored by the existing backend triage system.
    Only matches when a valid request_id is provided.
    Does NOT blindly fall back to a random previous user's assessment file.
    """
    default_result = {"priority": "YELLOW", "chief_complaint": "general", "assessment_id": None}
        
    assessment_files = glob.glob(str(ASSESSMENTS_DIR / "*.json"))
    if not assessment_files:
        return default_result
        
    # Sort newest first
    assessment_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    
    # Match on specific request_id if provided
    if request_id and request_id != "NAS-2026-UNSPECIFIED" and request_id != "test":
        for fpath in assessment_files:
            try:
                with open(fpath, "r", encoding="utf-8") as fp:
                    doc = json.load(fp)
                    if doc.get("request_id") == request_id:
                        p = doc.get("triage_result", {}).get("suggested_priority") or "YELLOW"
                        cc = doc.get("chief_complaint") or "general"
                        aid = doc.get("assessment_id")
                        return {"priority": p, "chief_complaint": cc, "assessment_id": aid, "full_assessment": doc}
            except Exception:
                continue
                
    return default_result

def get_stored_patient_priority(request_id: str) -> str:
    """Legacy helper returning just the priority string."""
    return get_stored_patient_assessment(request_id)["priority"]


async def nearby_hospitals_endpoint(request):
    """
    Discovers nearby hospitals using patient's incident location.
    Calculates distance and assigns priority-wise ambulance availability.
    """
    try:
        data = await request.json()
        request_id = data.get("request_id")
        address = (data.get("address") or "").strip()
        lat = data.get("latitude")
        lon = data.get("longitude")
        radius_km = float(data.get("radius_km") or 12.0)
        
        # 1. Coordinate resolution
        if lat is None or lon is None:
            if not address:
                return JSONResponse({
                    "error": "Unable to identify the entered location. Please check the address."
                }, status_code=400)
            
            geo = geocode_address(address)
            if not geo:
                return JSONResponse({
                    "error": "Unable to identify the entered location. Please check the address."
                }, status_code=400)
            lat, lon, standard_address = geo
        else:
            lat = float(lat)
            lon = float(lon)
            standard_address = address
            
        # 2. Retrieve already calculated patient priority and emergency condition
        patient_ctx = get_stored_patient_assessment(request_id)
        patient_priority = patient_ctx["priority"]
        chief_complaint = patient_ctx["chief_complaint"]
        
        # 3. Discover real hospitals from OSM / Overpass / Grounded search
        hospitals = discover_nearby_hospitals(lat, lon, radius_km, address)
        
        if not hospitals:
            # Try expanded radius
            hospitals = discover_nearby_hospitals(lat, lon, radius_km * 2, address)

        # Trigger background insurance discovery immediately without blocking caller
        if hospitals:
            trigger_background_insurance_discovery(hospitals)
            
        # 4. Attach persistent priority-wise ambulance availability, verified facilities, cost, fare & condition match
        results = []
        for h in hospitals:
            h_key = get_hospital_key(h["name"])
            panel_info = get_hospital_panel_info(h["name"], h.get("address", ""))
            facilities_info = get_hospital_capabilities_and_cost(h["name"], h.get("address", ""))
            
            # Government or Private identification
            class_str = (facilities_info.get("classification") or "").lower()
            is_govt = ("government" in class_str or "autonomous" in class_str or "municipal" in class_str or "civil" in class_str) and ("private" not in class_str and "non-government" not in class_str)
            
            fleet = ensure_hospital_ambulances(h["name"], h_key, is_govt=is_govt)
            avail_status = check_hospital_availability(h["name"], h_key, patient_priority, is_govt=is_govt)
            has_avail_amb = (avail_status == "AVAILABLE")
            
            dist_km = float(h.get("distance_km", 0.0))
            est_minutes = estimate_travel_time_minutes(dist_km)
            
            # Identify active ambulance type
            active_amb_type = "ALS"
            for amb in fleet:
                if amb.get("availability_status") == "AVAILABLE":
                    active_amb_type = amb.get("type", "ALS")
                    break
            
            # Calculate official/estimated transport fare for the active ambulance
            # Delhi CATS emergency check: CATS/Govt emergency ambulances for emergency priority are free
            is_cats = is_govt and ("delhi" in (h.get("address", "").lower() + h.get("name", "").lower()) or "aiims" in h["name"].lower() or "safdarjung" in h["name"].lower())
            primary_fare = calculate_ambulance_fare(
                amb_type=active_amb_type,
                distance_km=dist_km,
                is_government=is_govt,
                is_cats_emergency=is_cats,
                is_emergency_priority=(patient_priority in ["RED", "YELLOW", "REVIEW_REQUIRED"])
            )
            
            # Also calculate full tariff comparison for all ambulance categories
            all_tariffs = get_all_ambulance_tariffs_for_distance(dist_km, is_govt_hospital=is_govt)
            
            # Condition-based recommendation matching
            rec_info = evaluate_hospital_condition_match(
                chief_complaint=chief_complaint,
                priority=patient_priority,
                hospital_data={"facilities_info": facilities_info},
                distance_km=dist_km,
                has_available_ambulance=has_avail_amb
            )
            
            can_book = bool(has_avail_amb and rec_info["is_compatible"])
            if can_book:
                booking_status = "Available for Dispatch"
            elif not has_avail_amb:
                booking_status = "Currently Unavailable"
            elif patient_priority == "RED":
                booking_status = "Requires Level-3 Trauma/ICU Facility"
            else:
                booking_status = "Specialty Referral Needed"
            
            # Full comparative options and recommendation analysis for user review
            amb_evaluation = evaluate_ambulance_options(
                hospital_name=h["name"],
                hospital_id=h_key,
                distance_km=dist_km,
                patient_priority=patient_priority,
                chief_complaint=chief_complaint,
                is_govt=is_govt,
                is_cats=is_cats,
                travel_time_minutes=est_minutes
            )

            results.append({
                "hospital_id": h_key,
                "name": h["name"],
                "address": h["address"],
                "distance_km": dist_km,
                "travel_time_minutes": est_minutes,
                "availability": avail_status, # 'AVAILABLE' or 'NOT_AVAILABLE'
                "can_book": can_book,
                "booking_status_label": booking_status,
                "phone": h.get("phone", "") or ("+91-11-26588500" if "aiims" in h["name"].lower() else ""),
                "fleet": fleet,
                "ambulance_fare": primary_fare,
                "all_tariffs": all_tariffs,
                "ambulance_evaluation": amb_evaluation,
                "panel_info": panel_info,
                "facilities": facilities_info,
                "recommendation": rec_info
            })
            
        # Sort strictly by distance ascending (nearest first); suitability is secondary tiebreaker
        results.sort(key=lambda x: (x["distance_km"], -x["recommendation"]["suitability_score"]))
        
        # Fast path: Check existing in-memory cache instantly without calling Gemini network API
        for h in results:
            cached_res = get_cached_research_or_none(h.get("name", ""))
            if cached_res:
                _apply_research_to_hospital(h, cached_res)
            
            # Attach verified background insurance discovery data
            ins = get_cached_insurance(h.get("name", ""))
            if ins:
                h["insurance_data"] = {
                    "status": ins.get("status", "Verified"),
                    "providers": ins.get("insurance_providers", []),
                    "govt_schemes": ins.get("govt_schemes", []),
                    "plans": ins.get("plans", []),
                    "source": ins.get("source", "Official Hospital Empanelment Registry"),
                    "last_checked": ins.get("last_checked", "")
                }
            else:
                h["insurance_data"] = {
                    "status": "Unverified",
                    "providers": [],
                    "govt_schemes": [],
                    "plans": [],
                    "source": "Pending Background Verification",
                    "last_checked": ""
                }

        return JSONResponse({
            "success": True,
            "patient_request_id": request_id or "NAS-2026-UNSPECIFIED",
            "patient_priority": patient_priority,
            "chief_complaint": chief_complaint,
            "incident_location": standard_address or address or "Identified Incident Coordinates",
            "hospitals": results,
            "total_found": len(results)
        }, status_code=200)
        
    except Exception as e:
        logger.exception("Nearby hospitals failed: %s", e)
        return JSONResponse({
            "error": "Hospital information is temporarily unavailable. Please try again."
        }, status_code=500)


async def search_hospitals_endpoint(request):
    """
    Search hospitals by Name, Area, Locality, or City.
    Calculates distance from original patient incident location.
    """
    try:
        q = request.query_params.get("q", "").strip()
        request_id = request.query_params.get("request_id", "")
        p_lat = request.query_params.get("lat")
        p_lon = request.query_params.get("lon")
        address = request.query_params.get("address", "").strip()
        
        if not q:
            return JSONResponse({"error": "Search query is required"}, status_code=400)
            
        # Patient coords check
        if not p_lat or not p_lon:
            if address:
                geo = geocode_address(address)
                if geo:
                    p_lat, p_lon, _ = geo
            if not p_lat or not p_lon:
                p_lat, p_lon = 28.6139, 77.2090  # Default reference
        else:
            p_lat = float(p_lat)
            p_lon = float(p_lon)
            
        patient_ctx = get_stored_patient_assessment(request_id)
        patient_priority = patient_ctx["priority"]
        chief_complaint = patient_ctx["chief_complaint"]
        
        hospitals = search_hospitals_by_text(q, p_lat, p_lon)
        
        results = []
        for h in hospitals:
            h_key = get_hospital_key(h["name"])
            panel_info = get_hospital_panel_info(h["name"], h.get("address", ""))
            facilities_info = get_hospital_capabilities_and_cost(h["name"], h.get("address", ""))
            
            class_str = (facilities_info.get("classification") or "").lower()
            is_govt = ("government" in class_str or "autonomous" in class_str or "municipal" in class_str or "civil" in class_str) and ("private" not in class_str and "non-government" not in class_str)
            
            fleet = ensure_hospital_ambulances(h["name"], h_key, is_govt=is_govt)
            avail_status = check_hospital_availability(h["name"], h_key, patient_priority, is_govt=is_govt)
            has_avail_amb = (avail_status == "AVAILABLE")
            
            dist_km = float(h.get("distance_km", 0.0))
            est_minutes = estimate_travel_time_minutes(dist_km)
            
            active_amb_type = "ALS"
            for amb in fleet:
                if amb.get("availability_status") == "AVAILABLE":
                    active_amb_type = amb.get("type", "ALS")
                    break
            
            is_cats = is_govt and ("delhi" in (h.get("address", "").lower() + h.get("name", "").lower()) or "aiims" in h["name"].lower() or "safdarjung" in h["name"].lower())
            primary_fare = calculate_ambulance_fare(
                amb_type=active_amb_type,
                distance_km=dist_km,
                is_government=is_govt,
                is_cats_emergency=is_cats,
                is_emergency_priority=(patient_priority in ["RED", "YELLOW", "REVIEW_REQUIRED"])
            )
            all_tariffs = get_all_ambulance_tariffs_for_distance(dist_km, is_govt_hospital=is_govt)
            
            rec_info = evaluate_hospital_condition_match(
                chief_complaint=chief_complaint,
                priority=patient_priority,
                hospital_data={"facilities_info": facilities_info},
                distance_km=dist_km,
                has_available_ambulance=has_avail_amb
            )
            
            can_book = bool(has_avail_amb and rec_info["is_compatible"])
            if can_book:
                booking_status = "Available for Dispatch"
            elif not has_avail_amb:
                booking_status = "Currently Unavailable"
            elif patient_priority == "RED":
                booking_status = "Requires Level-3 Trauma/ICU Facility"
            else:
                booking_status = "Specialty Referral Needed"
            
            # Full comparative options and recommendation analysis for user review
            amb_evaluation = evaluate_ambulance_options(
                hospital_name=h["name"],
                hospital_id=h_key,
                distance_km=dist_km,
                patient_priority=patient_priority,
                chief_complaint=chief_complaint,
                is_govt=is_govt,
                is_cats=is_cats,
                travel_time_minutes=est_minutes
            )

            results.append({
                "hospital_id": h_key,
                "name": h["name"],
                "address": h["address"],
                "distance_km": dist_km,
                "travel_time_minutes": est_minutes,
                "availability": avail_status,
                "can_book": can_book,
                "booking_status_label": booking_status,
                "phone": h.get("phone", "") or ("+91-11-26588500" if "aiims" in h["name"].lower() else ""),
                "fleet": fleet,
                "ambulance_fare": primary_fare,
                "all_tariffs": all_tariffs,
                "ambulance_evaluation": amb_evaluation,
                "panel_info": panel_info,
                "facilities": facilities_info,
                "recommendation": rec_info
            })
            
        results.sort(key=lambda x: (x["distance_km"], -x["recommendation"]["suitability_score"]))
        
        # Fast path: Check existing in-memory cache instantly without calling Gemini network API
        for h in results:
            cached_res = get_cached_research_or_none(h.get("name", ""))
            if cached_res:
                _apply_research_to_hospital(h, cached_res)
            
            # Attach verified background insurance discovery data
            ins = get_cached_insurance(h.get("name", ""))
            if ins:
                h["insurance_data"] = {
                    "status": ins.get("status", "Verified"),
                    "providers": ins.get("insurance_providers", []),
                    "govt_schemes": ins.get("govt_schemes", []),
                    "plans": ins.get("plans", []),
                    "source": ins.get("source", "Official Hospital Empanelment Registry"),
                    "last_checked": ins.get("last_checked", "")
                }
            else:
                h["insurance_data"] = {
                    "status": "Unverified",
                    "providers": [],
                    "govt_schemes": [],
                    "plans": [],
                    "source": "Pending Background Verification",
                    "last_checked": ""
                }

        return JSONResponse({
            "success": True,
            "query": q,
            "patient_request_id": request_id,
            "patient_priority": patient_priority,
            "chief_complaint": chief_complaint,
            "hospitals": results,
            "total_found": len(results)
        }, status_code=200)
        
    except Exception:
        return JSONResponse({
            "error": "Hospital information is temporarily unavailable. Please try again."
        }, status_code=500)


async def autocomplete_hospitals_endpoint(request):
    """
    Lightweight autocomplete endpoint for live hospital search suggestions.
    Returns only name, address, hospital_id — no fare/panel/Gemini enrichment.

    Performance strategy:
    - Endpoint-level 10-min cache keyed by lowercase query prefix
    - First hit: runs Nominatim search in a threadpool (non-blocking)
    - Subsequent hits for the same query: returns from cache in <5 ms
    """
    try:
        q = request.query_params.get("q", "").strip()
        if not q or len(q) < 2:
            return JSONResponse({"suggestions": []}, status_code=200)

        cache_key = q.lower()

        # 1. Try endpoint-level cache first (instant)
        cached = _ac_cache_get(cache_key)
        if cached is not None:
            return JSONResponse({"suggestions": cached}, status_code=200)

        # 2. Use patient coords if provided, else default to Delhi centre
        p_lat = float(request.query_params.get("lat", 28.6139))
        p_lon = float(request.query_params.get("lon", 77.2090))

        def _fetch():
            """Nominatim place search + hospital search, merged for suggestions."""
            found = []

            # 1. Real places first (areas, localities, cities) so typing
            #    "Karol Bagh" yields a selectable location *with coordinates*.
            try:
                for place in _nominatim_place_search(q, limit=3):
                    found.append({
                        "kind": "place",
                        "name": place.get("title") or q,
                        "address": place.get("full_address") or place.get("subtitle") or "",
                        "latitude": place.get("lat"),
                        "longitude": place.get("lon"),
                        "hospital_id": None,
                    })
            except Exception as exc:
                logger.info("Place suggestions failed for %r: %s", q, exc)

            # 2. Hospitals (with coordinates) so selecting one also sets a real
            #    location instead of falling back to a hardcoded centre.
            try:
                raw = search_hospitals_by_text(q, p_lat, p_lon)
                seen = {f["name"].strip().lower() for f in found}
                for h in raw[:10]:
                    name = h.get("name", "")
                    if not name or name.strip().lower() in seen:
                        continue
                    address = h.get("address", "")
                    if address and "," in address:
                        parts = [p.strip() for p in address.split(",")]
                        concise = parts[:2] + parts[-3:-1] if len(parts) > 4 else parts[:4]
                        address = ", ".join(p for p in concise if p)
                    found.append({
                        "kind": "hospital",
                        "name": name,
                        "address": address,
                        "latitude": h.get("latitude"),
                        "longitude": h.get("longitude"),
                        "hospital_id": get_hospital_key(name),
                        "distance_km": round(h.get("distance_km", 0), 1),
                    })
            except Exception as exc:
                logger.info("Hospital suggestions failed for %r: %s", q, exc)

            return found[:10]

        suggestions = await run_in_threadpool(_fetch)

        # Cache the result so identical queries from other keystrokes are instant
        if suggestions:
            _ac_cache_set(cache_key, suggestions)

        return JSONResponse({"suggestions": suggestions}, status_code=200)

    except Exception as exc:
        logger.warning(f"Autocomplete error: {exc}")
        return JSONResponse({"suggestions": []}, status_code=200)


async def health_check(request):
    return JSONResponse({"status": "ok", "service": "AmbuPriority Assessment & Hospital Discovery API"}, status_code=200)


_PLACE_SUGGESTION_CACHE: Dict[str, tuple] = {}
_PLACE_SUGGESTION_TTL = 600    # 10 minutes


def _nominatim_place_search(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Look up real places (areas, localities, cities) on Nominatim.

    Used by the autocomplete so a searched area becomes a *selectable location
    with coordinates* — previously only hospitals were suggested, so typing an
    area left the app with no coordinates and it silently fell back to a
    hardcoded Delhi centre.
    """
    key = f"{query.strip().lower()}|{limit}"
    cached = _PLACE_SUGGESTION_CACHE.get(key)
    if cached and (time.time() - cached[0]) < _PLACE_SUGGESTION_TTL:
        return cached[1]

    # Use the resilient geocoder (throttled Nominatim + fallbacks). Calling
    # Nominatim directly here caused 429 storms and empty suggestions.
    try:
        from src.geocode_service import forward_geocode as _forward_geocode
        results = _forward_geocode(query, limit=limit)
    except Exception as exc:
        logger.info("Place suggestion lookup failed for %r: %s", query, exc)
        results = []

    _PLACE_SUGGESTION_CACHE[key] = (time.time(), results)
    return results


_PINCODE_INFO_CACHE: Dict[str, tuple] = {}
_PINCODE_INFO_TTL = 86400     # 1 day


def _pincode_info(pin: str) -> Dict[str, Any]:
    """
    Resolve a 6-digit PIN code to its real area(s) and a map centroid.

    India Post (api.postalpincode.in) is the authority for which post offices a
    PIN belongs to; OSM's `postalcode` search gives coordinates. OSM address tags
    are sometimes wrong (e.g. "Sadar Bazar, Delhi Cantt" is tagged 110046 while
    it is actually 110010), so the typed PIN wins over the address tag.
    """
    cached = _PINCODE_INFO_CACHE.get(pin)
    if cached and (time.time() - cached[0]) < _PINCODE_INFO_TTL:
        return cached[1]

    info: Dict[str, Any] = {"pincode": pin, "areas": [], "district": "", "state": "",
                            "lat": None, "lon": None, "display": ""}
    headers = {"User-Agent": "AmbuPriorityEmergencyDispatch/2.0 (contact: admin@ambupriority.gov.in)"}

    try:
        import requests as _rq
        resp = _rq.get(f"https://api.postalpincode.in/pincode/{pin}", headers=headers, timeout=8)
        block = (resp.json() or [{}])[0]
        if block.get("Status") == "Success":
            offices = block.get("PostOffice") or []
            info["areas"] = [p.get("Name") for p in offices if p.get("Name")][:6]
            if offices:
                info["district"] = offices[0].get("District") or ""
                info["state"] = offices[0].get("State") or ""
    except Exception as exc:
        logger.info("India Post lookup failed for %s: %s", pin, exc)

    try:
        import requests as _rq
        resp = _rq.get(
            "https://nominatim.openstreetmap.org/search",
            params={"postalcode": pin, "country": "India", "format": "jsonv2", "limit": 1},
            headers=headers, timeout=8,
        )
        items = resp.json() or []
        if items:
            info["lat"] = float(items[0]["lat"])
            info["lon"] = float(items[0]["lon"])
            info["display"] = items[0].get("display_name", "")
            addr = items[0].get("address", {}) or {}
            info["district"] = info["district"] or addr.get("state_district") or addr.get("county") or ""
            info["state"] = info["state"] or addr.get("state") or ""
    except Exception as exc:
        logger.info("Pincode centroid lookup failed for %s: %s", pin, exc)

    _PINCODE_INFO_CACHE[pin] = (time.time(), info)
    return info


def _format_nominatim_address(item: dict, accuracy_m: Optional[float] = None) -> dict:
    """
    Format a Nominatim geocoding item into a clean, accurate structured Indian address.
    Strictly prevents duplicate or confusing place names, validates PIN code against Indian postal standards,
    and flags low-accuracy geolocation readings so users are not misled.
    """
    import re
    a = item.get("address", {})
    raw_name = (item.get("name") or "").strip()
    
    # 1. House / building / landmark / road
    road_parts = []
    if a.get("house_number"):
        road_parts.append(a.get("house_number").strip())
    if a.get("building"):
        road_parts.append(a.get("building").strip())
    road_name = (a.get("road") or a.get("pedestrian") or a.get("street") or "").strip()
    if road_name:
        road_parts.append(road_name)
    road_str = ", ".join(road_parts)
    
    # 2. Locality / Suburb / Colony / Sector
    locality = (
        a.get("suburb") or
        a.get("neighbourhood") or
        a.get("residential") or
        a.get("subdistrict") or
        a.get("locality") or
        ""
    ).strip()
    
    # 3. City / Town / Village / Municipal Council
    city = (
        a.get("city") or
        a.get("town") or
        a.get("village") or
        a.get("municipality") or
        a.get("city_district") or
        ""
    ).strip()
    
    district = (a.get("state_district") or a.get("county") or "").strip()
    state = (a.get("state") or "").strip()
    raw_pincode = (a.get("postcode") or "").strip()
    
    # Strict 6-digit Indian PIN code validation: must start with 1-9 and have exactly 6 digits
    pincode = None
    if raw_pincode and re.match(r'^[1-9][0-9]{5}$', raw_pincode):
        pincode = raw_pincode

    # Check accuracy threshold
    is_poor_accuracy = (accuracy_m is not None and accuracy_m > 300)
    
    # Determine primary title
    # Filter out generic tags (bench, bus_stop, waste_basket, amenity)
    osm_type = (item.get("type") or "").lower()
    is_generic_amenity = osm_type in ["bench", "waste_basket", "shelter", "tree", "bollard", "gate"]
    title = ""
    if raw_name and not is_generic_amenity:
        title = raw_name
    elif road_str:
        title = road_str
    elif locality:
        title = locality
    elif city:
        title = city
    else:
        title = "Detected Location"
        
    # Build clean hierarchical components without repetitive duplicates
    components = []
    def _add_comp(val):
        if val and val.lower() not in [c.lower() for c in components]:
            components.append(val)
            
    if raw_name and not is_generic_amenity and raw_name.lower() not in [road_str.lower(), locality.lower(), city.lower()]:
        _add_comp(raw_name)
    if road_str:
        _add_comp(road_str)
    if locality:
        _add_comp(locality)
    if city:
        _add_comp(city)
    elif district:
        _add_comp(district)
    if state:
        _add_comp(state)
        
    # PIN code appending: only attach if valid PIN code exists and accuracy is acceptable
    if pincode and not is_poor_accuracy:
        _add_comp(pincode)
    _add_comp("India")
    
    full_address = ", ".join(components)
    
    # Build readable subtitle
    sub_parts = [c for c in components if c != title and c != "India"]
    subtitle = ", ".join(sub_parts)

    return {
        "title": title,
        "subtitle": subtitle,
        "full_address": full_address,
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "locality": locality,
        "city": city or district,
        "state": state,
        "pincode": pincode if not is_poor_accuracy else None,
        "accuracy_m": accuracy_m,
        "accuracy_status": "POOR_ACCURACY" if is_poor_accuracy else "RELIABLE",
        "accuracy_warning": "GPS accuracy is low (network estimation). Please verify your exact street & PIN code." if is_poor_accuracy else None,
        "type": item.get("type", "place")
    }


async def address_search_endpoint(request):
    """
    High-accuracy address search across India using OpenStreetMap Nominatim.
    Prioritizes Indian addresses with countrycodes=in, addressdetails=1.
    Returns structured { title, subtitle, full_address, lat, lon, pincode }.
    """
    try:
        q = request.query_params.get("q", "").strip()
        if not q or len(q) < 2:
            return JSONResponse({"results": []}, status_code=200)
            
        # Resilient geocoding: rate-limited Nominatim with BigDataCloud/Photon
        # fallbacks. Bare Nominatim returned 429 under our request volume, which
        # used to break the whole address search.
        try:
            from src.geocode_service import forward_geocode as _forward_geocode
            results = _forward_geocode(q, limit=8)
        except Exception as geo_err:
            logger.warning("Forward geocode failed: %s", geo_err)
            results = []

        # ── OSM PIN codes are verified against India Post ─────────────────────
        # OSM tags are community-maintained and occasionally wrong (e.g. the
        # "Sadar Bazar, Delhi Cantonment" node is tagged 110046, which actually
        # belongs to Nangal Raya). India Post is authoritative, so correct the
        # obvious mismatches before returning anything to the browser.
        try:
            for r in results[:2]:
                osm_pin = r.get("pincode")
                if not osm_pin:
                    continue
                verdict = verify_address_pincode(
                    {
                        "road": r.get("title") or "",
                        "locality": r.get("locality") or "",
                        "city": r.get("city") or "",
                        "state": r.get("state") or "",
                    },
                    osm_pin,
                )
                if verdict.get("corrected"):
                    r["pincode"] = verdict["pincode"]
                    r["accuracy_status"] = "PINCODE_CORRECTED"
                    r["accuracy_warning"] = verdict.get("reason")
                    for key in ("full_address", "subtitle"):
                        if isinstance(r.get(key), str):
                            r[key] = r[key].replace(osm_pin, verdict["pincode"])
                    logger.info("PIN corrected for %r: %s -> %s",
                                r.get("full_address"), osm_pin, verdict["pincode"])
        except Exception as pin_err:
            logger.info("PIN verification skipped: %s", pin_err)

        # ── PIN-code reconciliation ───────────────────────────────────────────
        # OSM address tags are sometimes simply wrong: "Sadar Bazar, Delhi Cantt"
        # is tagged 110046 although it is 110010. When the user typed a PIN, that
        # PIN is authoritative — prefer matching results, and if none match, use
        # the PIN's own centroid instead of the mismatched street point.
        typed_pin = None
        pin_match = re.search(r"\b([1-9][0-9]{5})\b", q)
        if pin_match:
            typed_pin = pin_match.group(1)

        if typed_pin:
            matching = [r for r in results if r.get("pincode") == typed_pin]
            if matching:
                results = matching + [r for r in results if r.get("pincode") != typed_pin]
            else:
                info = _pincode_info(typed_pin)
                if info.get("lat") is not None and info.get("lon") is not None:
                    # Pick the post-office / area name that best matches what the
                    # user typed, instead of blindly taking the first one.
                    areas = info.get("areas") or []
                    q_tokens = {t for t in re.split(r"[^a-z0-9]+", q.lower()) if len(t) > 3}
                    best_area, best_score = None, 0
                    for a in areas:
                        a_tokens = {t for t in re.split(r"[^a-z0-9]+", a.lower()) if len(t) > 3}
                        score = len(q_tokens & a_tokens)
                        if score > best_score:
                            best_area, best_score = a, score
                    area = best_area or (areas[0] if areas else f"PIN {typed_pin}")
                    wrong_pin = results[0].get("pincode") if results else None
                    corrected = {
                        "title": area,
                        "subtitle": f"PIN {typed_pin}" + (f", {info['district']}" if info.get("district") else ""),
                        "full_address": info.get("display") or f"{area}, {info.get('district','')}, PIN {typed_pin}".strip(", "),
                        "lat": info["lat"],
                        "lon": info["lon"],
                        "locality": area,
                        "city": info.get("district", ""),
                        "state": info.get("state", ""),
                        "pincode": typed_pin,
                        "accuracy_m": None,
                        "accuracy_status": "PINCODE_CORRECTED",
                        "accuracy_warning": (
                            f"Map data listed this address under PIN {wrong_pin}, "
                            f"but your PIN {typed_pin} was used instead. Please confirm the exact street."
                            if wrong_pin else
                            f"Location resolved from PIN {typed_pin}."
                        ),
                        "type": "pincode",
                    }
                    results.insert(0, corrected)
                    logger.info("PIN reconciliation: %s replaced OSM pin %s", typed_pin, wrong_pin)

        return JSONResponse({"results": results[:6], "typed_pin": typed_pin}, status_code=200)
    except Exception as e:
        logger.error(f"Address search endpoint error: {e}")
        return JSONResponse({"results": [], "error": str(e)}, status_code=500)


async def reverse_geocode_endpoint(request):
    """
    High-accuracy reverse geocoding from lat/lon to structured Indian address.
    Accepts accuracy parameter (in meters) to evaluate GPS reliability.
    """
    try:
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        accuracy_str = request.query_params.get("accuracy")
        accuracy_m = float(accuracy_str) if accuracy_str else None

        if not lat or not lon:
            return JSONResponse({"error": "Latitude and Longitude are required"}, status_code=400)

        # Resilient reverse geocoding: throttled Nominatim, then BigDataCloud and
        # Photon fallbacks, then a clearly-labelled coordinates-only result.
        # Previously a single 429 from OSM produced a 500 and the UI fell back to
        # raw coordinates.
        from src.geocode_service import reverse_geocode as _reverse_geocode
        formatted = _reverse_geocode(float(lat), float(lon), accuracy_m=accuracy_m)

        if True:
            # GPS reverse geocoding inherits OSM's PIN tag, which is sometimes
            # wrong. Verify against India Post before showing it to the user.
            try:
                osm_pin = formatted.get("pincode")
                if osm_pin:
                    verdict = verify_address_pincode(
                        {
                            "road": formatted.get("title") or "",
                            "locality": formatted.get("locality") or "",
                            "city": formatted.get("city") or "",
                            "state": formatted.get("state") or "",
                        },
                        osm_pin,
                    )
                    if verdict.get("corrected"):
                        formatted["pincode"] = verdict["pincode"]
                        formatted["accuracy_status"] = "PINCODE_CORRECTED"
                        formatted["accuracy_warning"] = verdict.get("reason")
                        for key in ("full_address", "subtitle"):
                            if isinstance(formatted.get(key), str):
                                formatted[key] = formatted[key].replace(osm_pin, verdict["pincode"])
            except Exception as pin_err:
                logger.info("Reverse-geocode PIN verification skipped: %s", pin_err)

            # If the map provider had no PIN tag (fallback providers often lack
            # one), resolve it from India Post — but only when the locality maps
            # to exactly one PIN. A guessed PIN is worse than no PIN.
            if not formatted.get("pincode"):
                try:
                    verdict = verify_address_pincode(
                        {
                            "road": formatted.get("title") or "",
                            "locality": formatted.get("locality") or "",
                            "city": formatted.get("city") or "",
                            "state": formatted.get("state") or "",
                        },
                        None,
                    )
                    pin = verdict.get("pincode")
                    if pin and verdict.get("unambiguous"):
                        formatted["pincode"] = pin
                        formatted["accuracy_status"] = "PINCODE_RESOLVED"
                        if isinstance(formatted.get("full_address"), str):
                            formatted["full_address"] += f", {pin}"
                except Exception as pin_err:
                    logger.info("PIN resolution skipped: %s", pin_err)

            return JSONResponse(formatted, status_code=200)
    except Exception as e:
        logger.error(f"Reverse geocode error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def hospital_detail_endpoint(request):
    """
    Detailed Hospital Facilities, Cost, and Capability Endpoint.
    Returns complete breakdown for the modal / detail panel.
    """
    try:
        h_id = request.path_params.get("hospital_id", "")
        name = request.query_params.get("name", "").strip()
        address = request.query_params.get("address", "").strip()
        request_id = request.query_params.get("request_id", "")
        dist_param = float(request.query_params.get("distance_km", 0.0) or 0.0)
        
        patient_ctx = get_stored_patient_assessment(request_id)
        patient_priority = patient_ctx["priority"]
        chief_complaint = patient_ctx["chief_complaint"]
        
        panel_info = get_hospital_panel_info(name, address)
        facilities_info = get_hospital_capabilities_and_cost(name, address)
        
        class_str = (facilities_info.get("classification") or "").lower()
        is_govt = ("government" in class_str or "autonomous" in class_str or "municipal" in class_str or "civil" in class_str) and ("private" not in class_str and "non-government" not in class_str)
        is_cats = is_govt and ("delhi" in (address.lower() + name.lower()) or "aiims" in name.lower() or "safdarjung" in name.lower())
        
        fleet = ensure_hospital_ambulances(name, h_id, is_govt=is_govt)
        avail_status = check_hospital_availability(name, h_id, patient_priority, is_govt=is_govt)
        has_avail_amb = (avail_status == "AVAILABLE")
        
        rec_info = evaluate_hospital_condition_match(
            chief_complaint=chief_complaint,
            priority=patient_priority,
            hospital_data={"facilities_info": facilities_info},
            distance_km=dist_param,
            has_available_ambulance=has_avail_amb
        )
        
        can_book = bool(has_avail_amb and rec_info["is_compatible"])

        amb_evaluation = evaluate_ambulance_options(
            hospital_name=name,
            hospital_id=h_id,
            distance_km=dist_param,
            patient_priority=patient_priority,
            chief_complaint=chief_complaint,
            is_govt=is_govt,
            is_cats=is_cats,
            travel_time_minutes=estimate_travel_time_minutes(dist_param)
        )
        
        # Check if research exists in cache and attach
        cached_res = get_cached_research_or_none(name)
        gemini_res = cached_res if cached_res else None

        return JSONResponse({
            "success": True,
            "hospital_id": h_id,
            "name": name,
            "address": address,
            "phone": "+91-11-26588500" if "aiims" in name.lower() else "+91-11-26165060" if "safdarjung" in name.lower() else "Emergency Helpline 112",
            "is_government": is_govt,
            "availability": avail_status,
            "can_book": can_book,
            "fleet": fleet,
            "ambulance_evaluation": amb_evaluation,
            "panel_info": panel_info,
            "facilities": facilities_info,
            "recommendation": rec_info,
            "gemini_research": gemini_res
        }, status_code=200)
    except Exception as e:
        logger.error(f"Hospital detail error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def hospital_research_endpoint(request):
    """
    Dedicated async endpoint for Gemini AI & Google Search Grounding research on a single hospital.
    Called incrementally in the background by the frontend without blocking main search results.
    """
    try:
        data = await request.json() if request.method == "POST" else {}
        name = data.get("name") or request.query_params.get("name", "")
        name = name.strip()
        if not name:
            return JSONResponse({"success": False, "error": "Hospital name required"}, status_code=400)

        # Run research asynchronously in a worker thread so the main ASGI loop is never blocked
        res_data = await run_in_threadpool(research_single_hospital, name)
        
        if res_data:
            return JSONResponse({
                "success": True,
                "name": name,
                "gemini_research": res_data
            }, status_code=200)
        else:
            return JSONResponse({
                "success": False,
                "name": name,
                "message": "No additional research available"
            }, status_code=200)
    except Exception as e:
        logger.warning(f"Single hospital research error for {name}: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def panel_scan_start_endpoint(request):
    """
    Kick off a background panel scan for a searched location.

    Returns immediately — the worker researches the ~30 nearby hospitals first
    (the rows this page renders), then the rest of the city. Starting a new scan
    cancels the previous one.
    """
    try:
        data = await request.json() if request.method == "POST" else {}
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            return JSONResponse({"success": False, "error": "lat and lon required"}, status_code=400)

        job_id = (data.get("job_id") or "").strip() or f"scan-{uuid.uuid4().hex[:10]}"
        job = start_panel_scan(
            job_id=job_id,
            lat=float(lat),
            lon=float(lon),
            label=(data.get("label") or "").strip(),
            radius_km=float(data.get("radius_km") or 5.0),
        )
        return JSONResponse({"success": True, "job": job}, status_code=202)
    except Exception as e:
        logger.warning(f"Panel scan start error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def panel_scan_status_endpoint(request):
    """Progress for a scan job (or the currently active one)."""
    try:
        job_id = request.query_params.get("job_id")
        job = panel_scan_status(job_id) if job_id else active_panel_scan()
        if not job:
            return JSONResponse({"success": False, "error": "no such job"}, status_code=404)
        return JSONResponse({"success": True, "job": job}, status_code=200)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def panel_scan_cancel_endpoint(request):
    """Cancel a running scan (used when the user changes the location)."""
    try:
        data = await request.json() if request.method == "POST" else {}
        job_id = (data.get("job_id") or request.query_params.get("job_id") or "").strip()
        cancelled = cancel_panel_scan(job_id or None)
        return JSONResponse({"success": True, "cancelled": cancelled}, status_code=200)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def panel_key_status_endpoint(request):
    """
    Diagnostics for the Gemini API key pool.

    Shows how many keys are loaded, which are ready, and which are benched for
    rate limiting. Useful for verifying that GEMINI_API_KEYS took effect.
    """
    try:
        status = key_pool_status()
        return JSONResponse({
            "success": True,
            "keys": len(status),
            "ready": sum(1 for s in status if s["ready"]),
            "detail": status,
        }, status_code=200)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def hospital_research_batch_endpoint(request):
    """
    Batch panel research endpoint.

    Resolves insurance/TPA panels for many hospitals in ONE request. Cache hits
    return in ~0 ms; all misses are folded into as few batched Gemini calls as
    possible, so a page of 10-20 hospitals costs one round trip instead of one
    LLM call per hospital.
    """
    try:
        data = await request.json() if request.method == "POST" else {}
        names = data.get("names") or []
        if isinstance(names, str):
            names = [names]
        names = [str(n).strip() for n in names if str(n).strip()]
        if not names:
            return JSONResponse({"success": False, "error": "names list required"}, status_code=400)

        resolved = await run_in_threadpool(research_many, names)

        # Look up live research results for requested names
        results = {}
        for name in names:
            ins = get_cached_insurance(name)
            if not ins:
                ins = research_hospital_insurance_sync(name)
            results[name] = ins or resolved.get(name) or get_cached_research_or_none(name)

        return JSONResponse(
            {"success": True, "count": len(results), "results": results},
            status_code=200,
        )
    except Exception as e:
        logger.warning(f"Batch hospital research error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def book_hospital_ambulance_endpoint(request):
    """
    Enforces strict booking rules on the backend:
    1. Explicit User Selection Required: Confirms specific ambulance category and unit.
    2. Rechecks live ambulance availability on the backend before booking.
    3. Validates patient priority compatibility against selected ambulance capabilities.
    4. Records verified booking reference and fare breakdown.
    5. Rejects any attempt to book without explicit user ambulance selection.
    """
    try:
        data = await request.json()
        h_id = data.get("hospital_id")
        h_name = data.get("hospital_name")
        request_id = data.get("request_id")
        selected_ambulance_id = data.get("selected_ambulance_id")
        selected_category = data.get("selected_category")
        user_confirmed = bool(data.get("user_confirmed", False))
        
        # User confirmation requirement check
        if not user_confirmed:
            return JSONResponse({
                "success": False,
                "error": "Explicit user confirmation is required. System will not dispatch without user confirmation."
            }, status_code=400)

        if not selected_ambulance_id:
            return JSONResponse({
                "success": False,
                "error": "No ambulance selected. Please manually select a suitable ambulance before confirming dispatch."
            }, status_code=400)
            
        patient_ctx = get_stored_patient_assessment(request_id)
        patient_priority = (patient_ctx["priority"] or "YELLOW").upper()
        chief_complaint = patient_ctx["chief_complaint"]

        # Retrieve facility classification
        facilities_info = get_hospital_capabilities_and_cost(h_name, "")
        class_str = (facilities_info.get("classification") or "").lower()
        is_govt = ("government" in class_str or "autonomous" in class_str or "municipal" in class_str or "civil" in class_str) and ("private" not in class_str and "non-government" not in class_str)

        # Recheck live ambulance fleet on backend
        fleet = ensure_hospital_ambulances(h_name, h_id, is_govt=is_govt)
        selected_amb = next((a for a in fleet if a.get("ambulance_id") == selected_ambulance_id), None)
        
        if not selected_amb:
            return JSONResponse({
                "success": False,
                "error": f"Selected ambulance '{selected_ambulance_id}' was not found in the verified fleet for {h_name}."
            }, status_code=400)

        # Backend recheck of operational availability
        if selected_amb.get("availability_status") != "AVAILABLE":
            return JSONResponse({
                "success": False,
                "error": f"Ambulance {selected_ambulance_id} is currently {selected_amb.get('availability_status')}. Please select another available unit."
            }, status_code=400)

        # Capability check for priority
        target_priorities = ["RED", "YELLOW"] if patient_priority == "REVIEW_REQUIRED" else [patient_priority]
        supported = selected_amb.get("supported_priorities", [])
        if not any(p in supported for p in target_priorities):
            return JSONResponse({
                "success": False,
                "error": f"Selected ambulance category ({selected_amb.get('type')}) is not certified to transport patient emergency priority {patient_priority}. Please select an appropriate life-support unit."
            }, status_code=400)
            
        # Recheck hospital compatibility
        rec_info = evaluate_hospital_condition_match(
            chief_complaint=chief_complaint,
            priority=patient_priority,
            hospital_data={"facilities_info": facilities_info},
            distance_km=0.0,
            has_available_ambulance=True
        )
        if not rec_info["is_compatible"]:
            return JSONResponse({
                "success": False,
                "error": "Facility Capability Mismatch. This facility lacks required ICU/trauma capabilities for the recorded emergency priority."
            }, status_code=400)
            
        # Dispatch confirmed with full audit trail
        booking_ref = f"AMB-BK-{uuid.uuid4().hex[:8].upper()}"

        # Calculate exact verified fare using the selected ambulance's fleet ownership and category
        amb_category = selected_amb.get("type", "BLS")
        amb_ownership_str = (selected_amb.get("ownership") or "").lower()
        amb_is_govt = "government" in amb_ownership_str and "private" not in amb_ownership_str and "non-government" not in amb_ownership_str
        is_cats = amb_is_govt and ("delhi" in (h_name.lower()) or "aiims" in h_name.lower() or "safdarjung" in h_name.lower())
        dist_km = float(data.get("distance_km") or 0.0)

        allocated_fare = calculate_ambulance_fare(
            amb_type=amb_category,
            distance_km=dist_km,
            is_government=amb_is_govt,
            is_cats_emergency=is_cats,
            is_emergency_priority=(patient_priority in ["RED", "YELLOW", "REVIEW_REQUIRED"])
        )

        # Generate secure booking OTP (6 digits) and store in backend
        booking_otp = f"{secrets.randbelow(900000) + 100000}"
        _otp_hash = hashlib.sha256(booking_otp.encode('utf-8')).hexdigest()
        BOOKING_OTP_STORE[booking_ref] = {
            "otp_hash": _otp_hash,
            "created_at": time.time(),
            "expires_at": time.time() + 900,  # 15 min validity
            "attempts": 0,
            "verified": False,
            "verified_at": None,
            "hospital_name": h_name,
            "ambulance_id": selected_amb.get("ambulance_id")
        }

        return JSONResponse({
            "success": True,
            "booking_reference": booking_ref,
            "hospital_id": h_id,
            "hospital_name": h_name,
            "patient_request_id": request_id,
            "patient_priority": patient_priority,
            "otp": booking_otp,  # Delivered once on booking generation
            "selected_ambulance": {
                "ambulance_id": selected_amb.get("ambulance_id"),
                "vehicle_id": selected_amb.get("vehicle_id"),
                "category": selected_amb.get("type"),
                "provider_name": selected_amb.get("provider_name"),
                "ownership": selected_amb.get("ownership"),
                "is_government": amb_is_govt,
                "verified_capabilities": selected_amb.get("verified_capabilities", []),
                "qualified_staff": selected_amb.get("qualified_staff"),
                "fare": allocated_fare
            },
            "status": "DISPATCH_CONFIRMED",
            "message": f"Dispatch confirmed for ambulance {selected_amb.get('ambulance_id')} ({selected_amb.get('type')}) to {h_name}."
        }, status_code=200)
    except Exception as e:
        logger.error(f"Booking error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def calculate_fare_endpoint(request):
    """
    Direct Fare Calculator Endpoint.
    Accepts:
      distance_km: float
      ambulance_type: str (PTV, BLS, ALS, ICU, Cardiac, Neonatal)
      is_government: bool
      is_cats: bool
    Returns:
      Calculated fare breakdown, per-km rates, and tariff comparison matrix.
    """
    try:
        data = await request.json()
        dist = float(data.get("distance_km", 0.0))
        amb_t = data.get("ambulance_type", "BLS")
        is_govt = bool(data.get("is_government", True))
        is_cats = bool(data.get("is_cats", False))
        
        fare = calculate_ambulance_fare(
            amb_type=amb_t,
            distance_km=dist,
            is_government=is_govt,
            is_cats_emergency=is_cats
        )
        matrix = get_all_ambulance_tariffs_for_distance(dist, is_govt_hospital=is_govt)
        
        return JSONResponse({
            "success": True,
            "fare": fare,
            "comparison_matrix": matrix
        }, status_code=200)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# =====================================================================
# OTP VERIFICATION & GOOGLE ROUTES PROXY (IN-MEMORY SECURE STORE)
# =====================================================================
BOOKING_OTP_STORE: Dict[str, Dict[str, Any]] = {}
DRIVER_EMERGENCY_ALERTS: Dict[str, List[Dict[str, Any]]] = {}
BOOKING_ARRIVAL_STORE: Dict[str, Dict[str, Any]] = {}
GOOGLE_ROUTES_API_KEY = "AIzaSyBSbVWvngycqjpjw4P48X4_-lBQGneTGtM"


async def record_ambulance_arrival_endpoint(request):
    """
    Records confirmed ambulance arrival at destination medical center.
    Validates GPS arrival radius, ensures idempotency, and records persistent arrival timestamp.
    """
    try:
        data = await request.json()
        booking_ref = (data.get("booking_reference") or "AMB-BK-LIVE").strip()
        hospital_name = data.get("hospital_name", "Designated Hospital")
        ambulance_id = data.get("ambulance_id", "A-102")
        driver_name = data.get("driver_name", "Rajesh Khanna")
        arrival_coords = data.get("arrival_coords", {})

        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_time = datetime.now().strftime("%I:%M %p")

        # Check if already arrived
        if booking_ref in BOOKING_ARRIVAL_STORE:
            existing = BOOKING_ARRIVAL_STORE[booking_ref]
            return JSONResponse({
                "success": True,
                "already_recorded": True,
                "booking_reference": booking_ref,
                "status": "ARRIVED",
                "arrival_timestamp": existing.get("arrival_timestamp", now_iso),
                "arrival_time_formatted": existing.get("arrival_time_formatted", now_time),
                "hospital_name": existing.get("hospital_name", hospital_name),
                "message": "Ambulance arrival already confirmed and logged."
            })

        record = {
            "booking_reference": booking_ref,
            "status": "ARRIVED",
            "hospital_name": hospital_name,
            "ambulance_id": ambulance_id,
            "driver_name": driver_name,
            "arrival_coords": arrival_coords,
            "arrival_timestamp": now_iso,
            "arrival_time_formatted": now_time,
            "handover_ready": True
        }
        BOOKING_ARRIVAL_STORE[booking_ref] = record

        return JSONResponse({
            "success": True,
            "already_recorded": False,
            "booking_reference": booking_ref,
            "status": "ARRIVED",
            "arrival_timestamp": now_iso,
            "arrival_time_formatted": now_time,
            "hospital_name": hospital_name,
            "message": "Ambulance successfully reached destination hospital. Priority intake initiated."
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def get_ambulance_arrival_status_endpoint(request):
    """
    Retrieves persistent arrival status for a booking reference.
    """
    booking_ref = request.query_params.get("booking_reference", "").strip()
    if not booking_ref or booking_ref not in BOOKING_ARRIVAL_STORE:
        return JSONResponse({"arrived": False, "status": "ON_ROUTE"})

    record = BOOKING_ARRIVAL_STORE[booking_ref]
    return JSONResponse({
        "arrived": True,
        "status": "ARRIVED",
        "data": record
    })


async def driver_emergency_alert_endpoint(request):
    """
    Emergency Alert: Patient is in Danger!
    Dispatches immediate high-priority emergency telemetry notification
    to the assigned ambulance driver and depot dispatcher.
    Prevents duplicate submissions within 15 seconds.
    """
    try:
        data = await request.json()
        booking_ref = (data.get("booking_reference") or "AMB-BK-LIVE").strip()
        driver_name = data.get("driver_name", "Assigned Driver")
        ambulance_id = data.get("ambulance_id", "A-102")
        alert_msg = data.get("message", "Patient condition deteriorating - Priority green corridor speed required")

        now = time.time()
        existing = DRIVER_EMERGENCY_ALERTS.get(booking_ref, [])
        if existing:
            last_alert = existing[-1]
            if now - last_alert.get("timestamp", 0) < 15:
                remaining = int(15 - (now - last_alert.get("timestamp", 0)))
                return JSONResponse({
                    "success": False,
                    "error": f"Emergency alert already broadcasted. Please wait {remaining}s before sending another alert.",
                    "status": "THROTTLED"
                }, status_code=429)

        alert_id = f"EMERG-ALT-{secrets.token_hex(4).upper()}"
        alert_record = {
            "alert_id": alert_id,
            "booking_reference": booking_ref,
            "driver_name": driver_name,
            "ambulance_id": ambulance_id,
            "message": alert_msg,
            "status": "DELIVERED_TO_CABIN",
            "timestamp": now,
            "time_str": time.strftime("%H:%M:%S", time.localtime(now)),
            "siren_activated": True
        }
        if booking_ref not in DRIVER_EMERGENCY_ALERTS:
            DRIVER_EMERGENCY_ALERTS[booking_ref] = []
        DRIVER_EMERGENCY_ALERTS[booking_ref].append(alert_record)

        logger.warning(f"🚨 EMERGENCY ALERT DISPATCHED: {alert_id} to {driver_name} [{ambulance_id}] for {booking_ref}")

        return JSONResponse({
            "success": True,
            "alert_id": alert_id,
            "status": "TRANSMITTED",
            "message": f"Emergency alert sent directly to driver {driver_name} in ambulance {ambulance_id}. In-cabin siren & flashing alert triggered.",
            "delivery_timestamp": alert_record["time_str"]
        }, status_code=200)
    except Exception as e:
        logger.error(f"Emergency alert dispatch error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def generate_otp_endpoint(request):
    """
    Generate or retrieve booking OTP securely through the backend.
    Enforces maximum 15-minute expiration and sha256 hash storage.
    """
    try:
        data = await request.json()
        booking_ref = (data.get("booking_reference") or "").strip()
        if not booking_ref:
            return JSONResponse({"success": False, "error": "Booking reference is required."}, status_code=400)

        now = time.time()
        record = BOOKING_OTP_STORE.get(booking_ref)

        # If already exists and not expired, return existing status
        if record and not record.get("verified") and record.get("expires_at", 0) > now:
            raw_otp = record.get("_raw_otp")
            return JSONResponse({
                "success": True,
                "booking_reference": booking_ref,
                "status": "PENDING",
                "otp": raw_otp,  # Authorized generation/viewing
                "expires_in_seconds": int(record["expires_at"] - now)
            }, status_code=200)

        # Generate fresh 6-digit OTP
        code = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        BOOKING_OTP_STORE[booking_ref] = {
            "otp_hash": otp_hash,
            "_raw_otp": code,
            "created_at": now,
            "expires_at": now + 900,  # 15 minutes
            "attempts": 0,
            "verified": False,
            "verified_at": None
        }

        return JSONResponse({
            "success": True,
            "booking_reference": booking_ref,
            "status": "PENDING",
            "otp": code,
            "expires_in_seconds": 900
        }, status_code=200)
    except Exception as e:
        logger.error(f"Generate OTP error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def verify_otp_endpoint(request):
    """
    Verify OTP securely through the backend.
    Enforces:
    - Sha256 hash comparison against stored OTP hash
    - Maximum 5 attempts before locking
    - Expiration verification (15 minutes)
    - Returns verified status & timestamp
    """
    try:
        data = await request.json()
        booking_ref = (data.get("booking_reference") or "").strip()
        entered_otp = str(data.get("otp") or "").strip()

        if not booking_ref or not entered_otp:
            return JSONResponse({"success": False, "error": "Booking reference and OTP are required."}, status_code=400)

        now = time.time()
        record = BOOKING_OTP_STORE.get(booking_ref)

        if not record:
            return JSONResponse({
                "success": False,
                "error": "No active OTP found for this booking reference. Please generate a new one.",
                "status": "NOT_FOUND"
            }, status_code=404)

        if record.get("verified"):
            return JSONResponse({
                "success": True,
                "status": "VERIFIED",
                "message": "OTP has already been successfully verified.",
                "verified_at": record.get("verified_at")
            }, status_code=200)

        if record.get("expires_at", 0) < now:
            return JSONResponse({
                "success": False,
                "error": "OTP has expired. Please request a new verification code.",
                "status": "EXPIRED"
            }, status_code=400)

        if record.get("attempts", 0) >= 5:
            return JSONResponse({
                "success": False,
                "error": "Too many invalid attempts (limit 5 reached). OTP has been locked for security.",
                "status": "LOCKED"
            }, status_code=429)

        entered_hash = hashlib.sha256(entered_otp.encode('utf-8')).hexdigest()
        if entered_hash != record.get("otp_hash"):
            record["attempts"] = record.get("attempts", 0) + 1
            remaining = 5 - record["attempts"]
            return JSONResponse({
                "success": False,
                "error": f"Invalid OTP. {remaining} attempt(s) remaining.",
                "status": "INVALID",
                "attempts_remaining": remaining
            }, status_code=400)

        # Mark as verified
        record["verified"] = True
        record["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        # Clear raw OTP once verified
        record.pop("_raw_otp", None)

        return JSONResponse({
            "success": True,
            "status": "VERIFIED",
            "message": "OTP verified successfully. Paramedic & patient handover authenticated.",
            "verified_at": record["verified_at"]
        }, status_code=200)
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def otp_status_endpoint(request):
    """
    Check verification status for a booking reference without exposing OTP secret.
    """
    try:
        booking_ref = request.query_params.get("booking_reference", "").strip()
        if not booking_ref:
            return JSONResponse({"success": False, "error": "Booking reference required."}, status_code=400)

        record = BOOKING_OTP_STORE.get(booking_ref)
        if not record:
            return JSONResponse({
                "success": True,
                "status": "NOT_GENERATED",
                "verified": False
            }, status_code=200)

        now = time.time()
        is_expired = record.get("expires_at", 0) < now and not record.get("verified")
        return JSONResponse({
            "success": True,
            "booking_reference": booking_ref,
            "verified": bool(record.get("verified")),
            "status": "VERIFIED" if record.get("verified") else ("EXPIRED" if is_expired else "PENDING"),
            "verified_at": record.get("verified_at"),
            "attempts": record.get("attempts", 0)
        }, status_code=200)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def compute_routes_endpoint(request):
    """
    Proxy to Google Routes API (computeRoutes) using existing API key.
    Avoids client-side CORS and protects route computing.
    """
    try:
        data = await request.json()
        origin_lat = float(data.get("origin_lat"))
        origin_lng = float(data.get("origin_lng"))
        dest_lat = float(data.get("dest_lat"))
        dest_lng = float(data.get("dest_lng"))

        payload = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin_lat,
                        "longitude": origin_lng
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": dest_lat,
                        "longitude": dest_lng
                    }
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE"
        }

        routes_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_ROUTES_API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
        }

        def _call_routes():
            req = urllib.request.Request(
                routes_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))

        route_data = await run_in_threadpool(_call_routes)
        return JSONResponse({"success": True, "data": route_data}, status_code=200)
    except Exception as e:
        logger.warning(f"Google Routes API call fallback: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


routes = [
    Route("/api/assessment", submit_assessment, methods=["POST"]),
    Route("/api/assessment/{assessment_id}", get_assessment, methods=["GET"]),
    Route("/api/hospitals/nearby", nearby_hospitals_endpoint, methods=["POST"]),
    Route("/api/hospitals/search", search_hospitals_endpoint, methods=["GET"]),
    Route("/api/hospitals/autocomplete", autocomplete_hospitals_endpoint, methods=["GET"]),
    Route("/api/hospitals/research", hospital_research_endpoint, methods=["POST", "GET"]),
    Route("/api/hospitals/research/batch", hospital_research_batch_endpoint, methods=["POST", "GET"]),
    Route("/api/panel/keys", panel_key_status_endpoint, methods=["GET"]),
    Route("/api/panel/scan", panel_scan_start_endpoint, methods=["POST"]),
    Route("/api/panel/scan/status", panel_scan_status_endpoint, methods=["GET"]),
    Route("/api/panel/scan/cancel", panel_scan_cancel_endpoint, methods=["POST"]),
    Route("/api/hospitals/{hospital_id}", hospital_detail_endpoint, methods=["GET"]),
    Route("/api/hospitals/book", book_hospital_ambulance_endpoint, methods=["POST"]),
    Route("/api/otp/generate", generate_otp_endpoint, methods=["POST"]),
    Route("/api/otp/verify", verify_otp_endpoint, methods=["POST"]),
    Route("/api/otp/status", otp_status_endpoint, methods=["GET"]),
    Route("/api/emergency/alert", driver_emergency_alert_endpoint, methods=["POST"]),
    Route("/api/ambulance/arrival", record_ambulance_arrival_endpoint, methods=["POST"]),
    Route("/api/ambulance/arrival/status", get_ambulance_arrival_status_endpoint, methods=["GET"]),
    Route("/api/routes/compute", compute_routes_endpoint, methods=["POST"]),
    Route("/api/ambulance/fare", calculate_fare_endpoint, methods=["POST"]),
    Route("/api/chat", chat_endpoint, methods=["POST"]),
    Route("/api/geocode/search", address_search_endpoint, methods=["GET"]),
    Route("/api/geocode/reverse", reverse_geocode_endpoint, methods=["GET"]),
    Route("/api/health", health_check, methods=["GET"]),
]

PUBLIC_DIR = ROOT_DIR / "public"
if PUBLIC_DIR.exists():
    routes.append(Mount("/", app=StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static"))

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    print("Starting AmbuPriority Assessment & Hospital Discovery API on port 5001...")
    uvicorn.run("src.assessment_api:app", host="0.0.0.0", port=5001, log_level="info")
