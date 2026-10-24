"""
ResQTrack: Priority Ambulance Dispatch System
Main Streamlit application entrypoint.
Educational prototype for priority-based emergency triage and resource routing.
"""

import os
import sys
from datetime import datetime, timezone

import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ambulance_dispatch.config import (
    DEFAULT_DB_PATH,
    DEMO_CENTER_LAT,
    DEMO_CENTER_LNG,
    DEMO_CITY_NAME,
)
from ambulance_dispatch.constants import (
    AVAILABLE_SYMPTOMS,
    DISCLAIMER_TEXT,
    SHORT_DISCLAIMER,
    AmbulanceStatus,
    IncidentStatus,
    TriageLevel,
)
from ambulance_dispatch.database import (
    create_incident,
    get_ambulance,
    get_incident,
    init_db,
    list_active_incidents,
    list_ambulances,
    list_incidents,
)
from ambulance_dispatch.dispatcher import (
    advance_incident_status,
    dispatch_incident,
    dispatch_next_highest_priority,
    find_nearest_available_ambulance,
    sort_incident_queue,
)
from ambulance_dispatch.geo import haversine_distance_km, is_valid_coordinate
from ambulance_dispatch.seed_data import load_demo_incidents
from ambulance_dispatch.triage import (
    check_sklearn_availability,
    evaluate_triage,
)

# Configure Streamlit page layout
st.set_page_config(
    page_title="ResQTrack - Ambulance Dispatch System",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Idempotently initialize SQLite tables and demo fleet on startup
try:
    init_db()
    db_initialized = True
except Exception as e:
    db_initialized = False
    st.error(f"Database Initialization Error: {e}")

# ---------------------------------------------------------
# Persistent Top Banner: Educational & Non-Clinical Disclaimer
# ---------------------------------------------------------
st.error(DISCLAIMER_TEXT, icon="🚨")

# Header Section
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("🚑 ResQTrack: Priority Ambulance Dispatch System")
    st.caption("Educational Demonstration Prototype — Priority Triage & Nearest-Available Dispatch")

with header_col2:
    status_label = "● System Online (Demo Mode)" if db_initialized else "▲ Database Error"
    status_color = "#4ade80" if db_initialized else "#f87171"
    st.markdown(
        f"""
        <div style="background-color: #1e293b; padding: 10px; border-radius: 8px; text-align: center; color: white;">
            <small>Environment Status</small><br>
            <span style="color: {status_color}; font-weight: bold;">{status_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Sidebar Navigation & Fleet Summary
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/ambulance.png", width=64)
    st.header("Control Panel")

    active_tab = st.radio(
        "Select Module",
        [
            "📝 Patient / Bystander Intake",
            "🚨 Dispatcher Dashboard",
            "ℹ️ System Overview & Safety",
        ],
        index=0,
    )

    st.markdown("---")
    st.subheader("📊 Fleet Quick Stats")
    all_ambs = list_ambulances()
    avail_count = sum(1 for a in all_ambs if a["status"] == AmbulanceStatus.AVAILABLE.value)
    assigned_count = sum(1 for a in all_ambs if a["status"] == AmbulanceStatus.ASSIGNED.value)

    c_s1, c_s2 = st.columns(2)
    c_s1.metric("Available", avail_count)
    c_s2.metric("Assigned", assigned_count)

    active_cases = list_active_incidents()
    pending_count = sum(1 for inc in active_cases if inc["status"] == IncidentStatus.PENDING.value)
    st.metric("Pending In Queue", pending_count)

    st.markdown("---")
    st.subheader("🛠️ Demo Actions")
    if st.button("⚡ Load Fictional Demo Cases", use_container_width=True):
        added = load_demo_incidents()
        if added > 0:
            st.success(f"Loaded {added} fictional demo cases!")
            st.rerun()
        else:
            st.info("Demo cases already exist in database (no duplicates added).")

    st.markdown("---")
    st.warning(SHORT_DISCLAIMER)


# =========================================================
# MODULE 1: PATIENT / BYSTANDER INTAKE FORM
# =========================================================
if active_tab == "📝 Patient / Bystander Intake":
    st.subheader("📝 Emergency Patient Intake Form")
    st.markdown(
        "Enter patient details and reported symptoms. Optional vital signs can be left blank. "
        "The system will execute a two-stage triage diagnosis and calculate dispatch priority."
    )

    with st.form("patient_intake_form", clear_on_submit=False):
        st.markdown("#### 1. Patient Demographics")
        col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
        with col_p1:
            patient_name = st.text_input("Patient Full Name *", placeholder="e.g. Jane Doe")
        with col_p2:
            age_input = st.number_input("Age (Years)", min_value=0, max_value=120, value=35, step=1)
        with col_p3:
            gender = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"])

        contact = st.text_input("Emergency Contact Number", placeholder="e.g. 555-0199")

        st.markdown("#### 2. Incident Location (Simulated City)")
        col_l1, col_l2, col_l3 = st.columns([2, 1, 1])
        with col_l1:
            location_text = st.text_input(
                "Address / Landmark Description *",
                value="Central Plaza, Metro City",
            )
        with col_l2:
            latitude_input = st.number_input(
                "Latitude (GPS)",
                value=DEMO_CENTER_LAT,
                format="%.6f",
                help="Defaults to simulated Metro City center coordinates.",
            )
        with col_l3:
            longitude_input = st.number_input(
                "Longitude (GPS)",
                value=DEMO_CENTER_LNG,
                format="%.6f",
                help="Defaults to simulated Metro City center coordinates.",
            )

        st.markdown("#### 3. Reported Symptoms & Pain Level")
        selected_symptoms = st.multiselect(
            "Reported Symptoms Checklist",
            options=AVAILABLE_SYMPTOMS,
            default=["Dizziness / Lightheadedness"],
            help="Select all symptoms described by the patient or caller.",
        )
        primary_symptom = st.text_input(
            "Primary Symptom Summary",
            placeholder="e.g. Sudden onset of sharp pain",
        )
        pain_level = st.slider(
            "Pain Scale (1: Mild to 10: Unbearable)",
            min_value=1,
            max_value=10,
            value=4,
        )

        st.markdown("#### 4. Clinical Vital Signs (Optional — Blank Allowed)")
        st.caption("Leave fields blank if equipment (e.g. blood pressure cuff or pulse oximeter) is not available.")
        col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
        with col_v1:
            hr_text = st.text_input("Heart Rate (BPM)", placeholder="e.g. 78")
        with col_v2:
            sbp_text = st.text_input("Systolic BP (mmHg)", placeholder="e.g. 120")
        with col_v3:
            dbp_text = st.text_input("Diastolic BP (mmHg)", placeholder="e.g. 80")
        with col_v4:
            spo2_text = st.text_input("SpO2 (%)", placeholder="e.g. 98.0")
        with col_v5:
            temp_text = st.text_input("Temp (°F)", placeholder="e.g. 98.6")

        submitted = st.form_submit_button("🚨 Submit Emergency Request", use_container_width=True)

    if submitted:
        # 1. Validation
        errors = []
        if not patient_name.strip():
            errors.append("Patient Full Name is required.")
        if not location_text.strip():
            errors.append("Incident Address / Location Description is required.")
        if not is_valid_coordinate(latitude_input, longitude_input):
            errors.append("Latitude must be between -90 and 90; Longitude between -180 and 180.")

        # Numeric parsing for optional vitals
        def parse_optional_float(val_str, name, min_val, max_val):
            if not val_str or not val_str.strip():
                return None
            try:
                val = float(val_str.strip())
                if val < min_val or val > max_val:
                    errors.append(f"{name} must be between {min_val} and {max_val}.")
                return val
            except ValueError:
                errors.append(f"{name} must be a valid number.")
                return None

        hr = parse_optional_float(hr_text, "Heart Rate", 20, 260)
        sbp = parse_optional_float(sbp_text, "Systolic BP", 40, 300)
        dbp = parse_optional_float(dbp_text, "Diastolic BP", 20, 200)
        spo2 = parse_optional_float(spo2_text, "SpO2", 50.0, 100.0)
        temp_f = parse_optional_float(temp_text, "Temperature", 70.0, 115.0)

        if errors:
            for err in errors:
                st.error(err)
        else:
            # 2. Triage Evaluation
            triage_res = evaluate_triage(
                symptoms=selected_symptoms,
                primary_symptom=primary_symptom,
                pain_level=pain_level,
                heart_rate=hr,
                systolic_bp=sbp,
                diastolic_bp=dbp,
                spo2=spo2,
                temperature_f=temp_f,
            )

            # 3. Save to SQLite
            incident_payload = {
                "patient_name": patient_name.strip(),
                "age": int(age_input),
                "gender": gender,
                "contact": contact.strip() if contact else None,
                "location_text": location_text.strip(),
                "latitude": float(latitude_input),
                "longitude": float(longitude_input),
                "heart_rate": hr,
                "systolic_bp": sbp,
                "diastolic_bp": dbp,
                "spo2": spo2,
                "temperature_f": temp_f,
                "symptoms": selected_symptoms,
                "primary_symptom": primary_symptom.strip() if primary_symptom else None,
                "pain_level": int(pain_level),
                "triage_level": triage_res["triage_level"],
                "p_red": triage_res["p_red"],
                "p_yellow": triage_res["p_yellow"],
                "p_green": triage_res["p_green"],
                "demo_priority_score": triage_res["demo_priority_score"],
                "status": IncidentStatus.PENDING.value,
            }

            try:
                new_id = create_incident(incident_payload)

                # 4. Display Triage Diagnosis Banner
                t_level = triage_res["triage_level"]
                badge_color = {"RED": "#ef4444", "YELLOW": "#f59e0b", "GREEN": "#10b981"}.get(t_level, "#3b82f6")
                emoji = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(t_level, "⚪")

                st.success(f"✅ Emergency Incident #{new_id} Successfully Registered & Queued!")

                st.markdown(
                    f"""
                    <div style="border-left: 6px solid {badge_color}; background-color: #1e293b; padding: 16px; border-radius: 6px; color: white; margin-top: 10px;">
                        <h3 style="margin: 0; color: white;">{emoji} Assigned Triage Level: {t_level}</h3>
                        <p style="margin: 8px 0 4px 0;"><strong>Diagnostic Stage:</strong> {triage_res['stage_desc']}</p>
                        <p style="margin: 0;"><strong>Demo Priority Score:</strong> {triage_res['demo_priority_score']:.2f} (DEMO ONLY)</p>
                        <hr style="border-color: #334155; margin: 10px 0;">
                        <small>
                            <strong>Simulated Probabilities:</strong> 
                            P(Red) = {triage_res['p_red']:.2f} | 
                            P(Yellow) = {triage_res['p_yellow']:.2f} | 
                            P(Green) = {triage_res['p_green']:.2f}
                        </small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Show nearest ambulance estimate
                nearest_amb, nearest_dist = find_nearest_available_ambulance(latitude_input, longitude_input)
                if nearest_amb and nearest_dist is not None:
                    st.info(
                        f"📍 Nearest Available Ambulance: **{nearest_amb['ambulance_id']}** "
                        f"({nearest_amb['driver_name']}) — approx. **{nearest_dist:.2f} km** straight-line distance."
                    )
                else:
                    st.warning("⚠️ No available ambulances currently in fleet. Request queued at priority position.")

            except Exception as e:
                st.error(f"Failed to record incident: {e}")


# =========================================================
# MODULE 2: DISPATCHER DASHBOARD
# =========================================================
elif active_tab == "🚨 Dispatcher Dashboard":
    st.subheader("🚨 Dispatcher Control Dashboard")

    dash_col1, dash_col2 = st.columns([3, 1])
    with dash_col1:
        st.markdown(
            "Manage active emergency calls and ambulance fleet. "
            "Queue is sorted deterministically: **Red (Priority 1) > Yellow (Priority 2) > Green (Priority 3)**."
        )
    with dash_col2:
        if st.button("🚨 Dispatch Next (Highest Priority)", type="primary", use_container_width=True):
            success, msg = dispatch_next_highest_priority()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)

    st.markdown("---")

    # 1. Active Incidents Section
    st.subheader("📋 Active Emergency Incident Queue")
    raw_active_incidents = list_active_incidents()
    active_queue = sort_incident_queue(raw_active_incidents)

    if not active_queue:
        st.info("No active emergency incidents currently in queue. Click '⚡ Load Fictional Demo Cases' in the sidebar to populate demo cases.")
    else:
        for inc in active_queue:
            inc_id = inc["incident_id"]
            t_level = inc.get("triage_level", "GREEN")
            status = inc.get("status", "PENDING")
            badge_color = {"RED": "#ef4444", "YELLOW": "#f59e0b", "GREEN": "#10b981"}.get(t_level, "#3b82f6")
            emoji = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(t_level, "⚪")

            # Calculate nearest ambulance for pending incidents
            nearest_info = "N/A"
            if status == IncidentStatus.PENDING.value and is_valid_coordinate(inc.get("latitude"), inc.get("longitude")):
                n_amb, n_dist = find_nearest_available_ambulance(inc["latitude"], inc["longitude"])
                if n_amb and n_dist is not None:
                    nearest_info = f"{n_amb['ambulance_id']} (~{n_dist:.2f} km)"
                else:
                    nearest_info = "None available"

            # Check if an ambulance is assigned
            assigned_amb_id = None
            if status != IncidentStatus.PENDING.value:
                amb_matches = [a for a in all_ambs if a.get("assigned_incident_id") == inc_id]
                if amb_matches:
                    assigned_amb_id = amb_matches[0]["ambulance_id"]

            with st.container():
                st.markdown(
                    f"""
                    <div style="border-left: 5px solid {badge_color}; background-color: #0f172a; padding: 12px; border-radius: 6px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 16px; color: white;">Incident #{inc_id}: {inc['patient_name']}</strong>
                                &nbsp;&nbsp;
                                <span style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                    {emoji} {t_level} (Score: {inc.get('demo_priority_score', 0):.1f})
                                </span>
                                &nbsp;&nbsp;
                                <span style="background-color: #334155; color: #94a3b8; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                                    Status: {status}
                                </span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_d1, col_d2, col_d3 = st.columns([2, 2, 2])
                with col_d1:
                    st.write(f"📍 **Location:** {inc.get('location_text', 'Unknown')}")
                    st.write(f"⚠️ **Primary Symptom:** {inc.get('primary_symptom') or 'None specified'}")
                with col_d2:
                    symptom_list = inc.get("symptoms", [])
                    symptom_str = ", ".join(symptom_list) if symptom_list else "None checked"
                    st.write(f"🩺 **Symptoms:** {symptom_str}")
                    st.write(f"🩹 **Pain Scale:** {inc.get('pain_level')}/10")
                with col_d3:
                    if status == IncidentStatus.PENDING.value:
                        st.write(f"🚑 **Closest Unit:** {nearest_info}")
                        if st.button(f"Dispatch Unit to #{inc_id}", key=f"disp_btn_{inc_id}", use_container_width=True):
                            ok, msg = dispatch_incident(inc_id)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.write(f"🚑 **Assigned Vehicle:** {assigned_amb_id or 'Assigned'}")
                        # Lifecycle progression buttons
                        p_col1, p_col2 = st.columns(2)
                        with p_col1:
                            if status == IncidentStatus.DISPATCHED.value:
                                if st.button("Mark En Route", key=f"en_route_{inc_id}"):
                                    advance_incident_status(inc_id, IncidentStatus.EN_ROUTE.value)
                                    st.rerun()
                            elif status == IncidentStatus.EN_ROUTE.value:
                                if st.button("At Hospital", key=f"at_hosp_{inc_id}"):
                                    advance_incident_status(inc_id, IncidentStatus.AT_HOSPITAL.value)
                                    st.rerun()
                            elif status == IncidentStatus.AT_HOSPITAL.value:
                                if st.button("Complete & Release", key=f"comp_{inc_id}", type="primary"):
                                    advance_incident_status(inc_id, IncidentStatus.COMPLETED.value)
                                    st.rerun()
                        with p_col2:
                            if st.button("Cancel Call", key=f"canc_{inc_id}"):
                                advance_incident_status(inc_id, IncidentStatus.CANCELLED.value)
                                st.rerun()

                st.markdown("---")

    # 2. Ambulance Fleet Status Table
    st.subheader("🚑 Ambulance Fleet Status")
    fleet_rows = []
    for a in all_ambs:
        amb_id = a["ambulance_id"]
        status_val = a["status"]
        status_str = f"🟢 {status_val}" if status_val == AmbulanceStatus.AVAILABLE.value else (
            f"🟠 {status_val}" if status_val == AmbulanceStatus.ASSIGNED.value else f"⚪ {status_val}"
        )
        assigned_inc = f"Incident #{a['assigned_incident_id']}" if a["assigned_incident_id"] else "None (Free)"
        coords_str = f"({a['current_lat']:.4f}, {a['current_lng']:.4f})" if is_valid_coordinate(a["current_lat"], a["current_lng"]) else "Invalid"

        fleet_rows.append({
            "Ambulance ID": amb_id,
            "Paramedic / Driver": a["driver_name"],
            "Availability Status": status_str,
            "Active Mission": assigned_inc,
            "GPS Base Coordinates": coords_str,
        })

    st.dataframe(fleet_rows, use_container_width=True, hide_index=True)


# =========================================================
# MODULE 3: SYSTEM ARCHITECTURE & EDUCATIONAL INFO
# =========================================================
elif active_tab == "ℹ️ System Overview & Safety":
    st.subheader("ℹ️ System Architecture & Educational Framework")

    st.markdown(
        """
        ### 🎓 Academic Prototype Architecture
        This application demonstrates how basic Python data structures, Scikit-Learn classifiers,
        and SQLite transactions can simulate an automated priority ambulance dispatching workflow:

        ```
        [Patient Intake Form]
                 ↓
        [Stage 1: Deterministic Red-Flag Safety Rule]
                 ↓ (if no immediate red-flag)
        [Stage 2: Scikit-Learn Classifier (Decision Tree)]
                 ↓
        [Deterministic Priority Queue (Red > Yellow > Green)]
                 ↓
        [Haversine Nearest Available Ambulance Dispatch]
                 ↓
        [Lifecycle Tracking & Atomic Resource Release]
        ```

        ### 🚦 Triage Hierarchy
        1. **🔴 Red (Priority 1 — Critical / Life-Threatening)**:
           - Overrides applied for chest pain, shortness of breath, loss of consciousness, or uncontrolled bleeding.
           - Highest queue precedence; dispatched first regardless of arrival time.
        2. **🟡 Yellow (Priority 2 — Urgent / Serious)**:
           - Moderate pain, fractures, non-critical distress.
           - Queued behind Red cases.
        3. **🟢 Green (Priority 3 — Non-Urgent / Minor)**:
           - Superficial abrasions, mild pain. Queued after urgent emergencies.

        ### ⚠️ Important Limitations
        * **Straight-Line Distance**: Distance calculations use the Haversine formula and do NOT account for actual road networks, one-way streets, traffic, or real travel times.
        * **Synthetic Data Only**: The machine learning model is trained on a tiny synthetic dataset for educational demonstration. It has **NO clinical validation**.
        * **Never Use for Real Emergencies**: Anyone in medical distress must immediately contact official emergency services (such as 911, 112, 999).
        """
    )

    sklearn_status = "Available (Active)" if check_sklearn_availability() else "Missing (Using Deterministic Fallback)"
    st.info(f"**Machine Learning Engine Status**: Scikit-Learn is {sklearn_status}.")

# Persistent Footer Disclaimer
st.markdown("---")
st.caption(
    "ResQTrack Educational Prototype • Built for Coursework Demonstrations • "
    "⚠️ Simulated behavior only; not clinically validated."
)
