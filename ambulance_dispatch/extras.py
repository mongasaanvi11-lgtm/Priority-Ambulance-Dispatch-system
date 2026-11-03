"""UI extras for ResQTrack (educational prototype).

Adds: themed CSS, hero banner, billing estimator, live Delhi map tracker,
and clickable ambulance-feature flashcards.

All tariffs below are ILLUSTRATIVE placeholders, not an official price list.
"""

import html
import math
from datetime import datetime, timedelta, timezone

import pandas as pd
import pydeck as pdk
import streamlit as st

from ambulance_dispatch.config import DEMO_CENTER_LAT, DEMO_CENTER_LNG
from ambulance_dispatch.database import list_active_incidents, list_ambulances

# ---------------------------------------------------------------------------
# Editable data (change these to match your own assumptions)
# ---------------------------------------------------------------------------
ROAD_FACTOR = 1.35          # straight-line km -> approx road km
BASE_SPEED_KMH = 40         # assumed city ambulance speed for ETA simulation
NIGHT_SURCHARGE = 0.20      # 22:00-06:00
WAITING_PER_15_MIN = 75     # INR

AMBULANCE_TYPES = {
    "Basic Life Support (BLS)": {
        "icon": "🚑", "base": 800, "included_km": 5, "per_km": 18,
        "crew": "Driver + trained EMT",
        "desc": "Patient transfer with oxygen, basic first aid and monitoring. "
                "Suited to stable, non-critical patients.",
    },
    "Advanced Life Support (ALS)": {
        "icon": "🚨", "base": 2000, "included_km": 5, "per_km": 30,
        "crew": "Driver + paramedic",
        "desc": "Adds cardiac monitor, defibrillator, IV access and emergency drugs "
                "for serious cases such as cardiac or trauma emergencies.",
    },
    "ICU / Ventilator": {
        "icon": "🏥", "base": 3500, "included_km": 5, "per_km": 45,
        "crew": "Driver + paramedic + nurse/doctor",
        "desc": "A mobile ICU with ventilator, multi-parameter monitor and infusion "
                "pumps for critically ill patients.",
    },
    "Neonatal Transport": {
        "icon": "👶", "base": 3000, "included_km": 5, "per_km": 40,
        "crew": "Driver + neonatal-trained nurse",
        "desc": "Incubator with temperature control, neonatal ventilation and "
                "monitoring for newborns.",
    },
}

ADDONS = {
    "Oxygen cylinder": 300,
    "Paramedic / doctor on board": 700,
    "Ventilator support": 1200,
    "Cardiac monitor + defibrillator": 600,
    "Stretcher / wheelchair assistance": 150,
}

# Approximate coordinates, for demonstration only
HOSPITALS = {
    "AIIMS, Ansari Nagar": (28.5672, 77.2100),
    "Safdarjung Hospital": (28.5677, 77.2064),
    "Dr. RML Hospital": (28.6258, 77.2007),
    "Lok Nayak Hospital (LNJP)": (28.6389, 77.2400),
    "Sir Ganga Ram Hospital": (28.6381, 77.1898),
    "GTB Hospital, Shahdara": (28.6845, 77.3069),
    "Max Hospital, Saket": (28.5275, 77.2123),
    "Deen Dayal Upadhyay Hospital": (28.6286, 77.1189),
}

DELHI_AREAS = {
    "Connaught Place": (28.6315, 77.2167),
    "India Gate": (28.6129, 77.2295),
    "Karol Bagh": (28.6519, 77.1909),
    "Lajpat Nagar": (28.5677, 77.2433),
    "Dwarka Sector 10": (28.5921, 77.0460),
    "Rohini Sector 7": (28.7041, 77.1025),
    "Saket": (28.5245, 77.2066),
    "Laxmi Nagar": (28.6304, 77.2773),
    "Janakpuri": (28.6219, 77.0878),
    "Old Delhi (Chandni Chowk)": (28.6506, 77.2303),
}

TRIAGE_COLORS = {
    "RED": [239, 68, 68, 230],
    "YELLOW": [245, 158, 11, 230],
    "GREEN": [16, 185, 129, 230],
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _flat(markup: str) -> str:
    """Collapse multi-line HTML so Streamlit's markdown never treats it as code."""
    return " ".join(line.strip() for line in markup.strip().splitlines())


def _hav(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _parse_ts(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _inr(x: float) -> str:
    return f"₹{x:,.0f}"


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
_CSS = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #1b2a4a 0%, #0b1020 55%, #070a14 100%);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111a33 0%, #0b1020 100%);
    border-right: 1px solid #22304f;
}
div.stButton > button {
    border-radius: 10px;
    border: 1px solid #2b3a5e;
    transition: all .15s ease;
}
div.stButton > button:hover {
    border-color: #ef4444;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(239, 68, 68, .35);
}
button[kind="primary"] {
    background: linear-gradient(90deg, #ef4444, #dc2626) !important;
    border: none !important;
}
[data-testid="stMetric"] {
    background: #111a33;
    border: 1px solid #22304f;
    border-radius: 12px;
    padding: 10px 14px;
}
.rq-hero {
    display: flex; justify-content: space-between; align-items: center; gap: 16px;
    background: linear-gradient(120deg, #7f1d1d 0%, #b91c1c 35%, #1e3a8a 100%);
    border-radius: 16px; padding: 18px 24px; margin: 6px 0 14px 0;
    box-shadow: 0 8px 28px rgba(0, 0, 0, .45);
}
.rq-title { font-size: 2rem; font-weight: 800; color: #fff; line-height: 1.1; }
.rq-sub { color: #e2e8f0; opacity: .9; font-size: .95rem; margin-top: 4px; }
.rq-pill {
    background: rgba(15, 23, 42, .75); padding: 8px 16px; border-radius: 999px;
    font-weight: 700; font-size: .85rem; white-space: nowrap; color: #4ade80;
}
.rq-pill.bad { color: #f87171; }
.rq-dot {
    display: inline-block; width: 9px; height: 9px; border-radius: 50%;
    background: currentColor; margin-right: 8px; animation: rqpulse 1.4s infinite;
}
@keyframes rqpulse { 0% {opacity: 1;} 50% {opacity: .25;} 100% {opacity: 1;} }

.rq-invoice {
    background: linear-gradient(145deg, #16223f, #101a33);
    border: 1px solid #2b3a5e; border-radius: 14px; padding: 16px 18px; color: #e2e8f0;
}
.rq-invoice table { width: 100%; border-collapse: collapse; }
.rq-invoice td { padding: 6px 0; border-bottom: 1px dashed #2b3a5e; font-size: .9rem; }
.rq-invoice td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
.rq-total td { font-size: 1.15rem; font-weight: 800; color: #38bdf8; border-bottom: none; padding-top: 12px; }

details.rq-flip {
    background: linear-gradient(145deg, #16223f, #101a33);
    border: 1px solid #2b3a5e; border-radius: 14px; padding: 14px 16px;
    margin-bottom: 12px; transition: all .2s ease;
}
details.rq-flip:hover {
    border-color: #ef4444; box-shadow: 0 6px 18px rgba(239, 68, 68, .25); transform: translateY(-2px);
}
details.rq-flip[open] { border-color: #38bdf8; background: linear-gradient(145deg, #12304a, #0f2038); }
details.rq-flip summary { cursor: pointer; list-style: none; outline: none; }
details.rq-flip summary::-webkit-details-marker { display: none; }
.rq-ico { font-size: 1.9rem; }
.rq-t { font-weight: 700; color: #38bdf8; font-size: 1.02rem; margin: 2px 0; }
.rq-s { color: #94a3b8; font-size: .85rem; }
.rq-hint { color: #f87171; font-size: .72rem; margin-top: 6px; }
.rq-d {
    margin-top: 10px; padding-top: 10px; border-top: 1px dashed #2b3a5e;
    color: #e2e8f0; font-size: .88rem; line-height: 1.45;
}
.rq-legend span { margin-right: 16px; font-size: .85rem; color: #cbd5e1; }
</style>
"""


def apply_theme():
    st.markdown(_CSS, unsafe_allow_html=True)


def render_hero(db_ok: bool = True):
    label = "System Online (Demo Mode)" if db_ok else "Database Error"
    cls = "rq-pill" if db_ok else "rq-pill bad"
    st.markdown(
        _flat(f"""
        <div class="rq-hero">
          <div>
            <div class="rq-title">🚑 ResQTrack</div>
            <div class="rq-sub">Priority Ambulance Dispatch · New Delhi · Educational Prototype</div>
          </div>
          <div class="{cls}"><span class="rq-dot"></span>{label}</div>
        </div>
        """),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------
def estimate_bill(amb_type, pickup_km, trip_km, addons, night, wait_min, discount_pct):
    r = AMBULANCE_TYPES[amb_type]
    total_km = pickup_km + trip_km
    extra_km = max(0.0, total_km - r["included_km"])
    base = r["base"]
    distance = extra_km * r["per_km"]

    lines = [
        (f"Base fare (includes first {r['included_km']} km)", base),
        (f"Distance: {extra_km:.1f} km × {_inr(r['per_km'])}/km", distance),
    ]
    for name in addons:
        lines.append((name, ADDONS[name]))
    waiting = (wait_min / 15) * WAITING_PER_15_MIN
    if waiting:
        lines.append((f"Waiting time ({wait_min} min)", waiting))
    night_amt = (base + distance) * NIGHT_SURCHARGE if night else 0.0
    if night_amt:
        lines.append((f"Night surcharge ({int(NIGHT_SURCHARGE * 100)}%)", night_amt))

    subtotal = sum(a for _, a in lines)
    discount = subtotal * discount_pct / 100
    if discount:
        lines.append((f"Subsidy / insurance cover ({discount_pct}%)", -discount))
    return lines, subtotal, subtotal - discount, total_km


def render_billing():
    st.subheader("💰 Ambulance Billing Estimator")
    st.caption(
        "Illustrative tariff for demonstration only. Edit the rates at the top of "
        "`ambulance_dispatch/extras.py`. Taxes are not included."
    )

    ambs = list_ambulances()
    avail = [
        a for a in ambs
        if a["status"] == "AVAILABLE" and a.get("current_lat") is not None
        and a.get("current_lng") is not None
    ]
    incs = list_active_incidents()

    left, right = st.columns([3, 2], gap="large")

    with left:
        source = st.radio("Trip source", ["Use an active incident", "Enter manually"], horizontal=True)

        patient_name, triage = "Walk-in estimate", "GREEN"
        use_incident = source.startswith("Use") and bool(incs)
        if source.startswith("Use") and not incs:
            st.info("No active incidents yet — load demo cases from the sidebar, or enter a trip manually.")

        if use_incident:
            options = {
                f"#{i['incident_id']} · {i['patient_name']} · {i.get('triage_level', 'GREEN')}": i
                for i in incs
            }
            chosen = options[st.selectbox("Incident", list(options.keys()))]
            plat, plng = chosen["latitude"], chosen["longitude"]
            patient_name = chosen["patient_name"]
            triage = chosen.get("triage_level", "GREEN")
            trip_key = f"inc{chosen['incident_id']}"
        else:
            area = st.selectbox("Pickup area (Delhi)", list(DELHI_AREAS.keys()))
            plat, plng = DELHI_AREAS[area]
            trip_key = f"area{area}"

        hospital = st.selectbox("Destination hospital", list(HOSPITALS.keys()))
        hlat, hlng = HOSPITALS[hospital]

        pickup_default = 0.0
        if avail:
            pickup_default = min(
                _hav(a["current_lat"], a["current_lng"], plat, plng) for a in avail
            ) * ROAD_FACTOR
        trip_default = _hav(plat, plng, hlat, hlng) * ROAD_FACTOR

        c1, c2 = st.columns(2)
        pickup_km = c1.number_input(
            "Ambulance → patient (km)", min_value=0.0, step=0.5,
            value=round(pickup_default, 1), key=f"pk_{trip_key}_{hospital}",
            help="Nearest available unit, straight-line × road factor.",
        )
        trip_km = c2.number_input(
            "Patient → hospital (km)", min_value=0.0, step=0.5,
            value=round(trip_default, 1), key=f"tk_{trip_key}_{hospital}",
        )

        suggested = {"RED": 2, "YELLOW": 1, "GREEN": 0}.get(triage, 0)
        types = list(AMBULANCE_TYPES.keys())
        amb_type = st.selectbox("Ambulance type (suggested from triage level)", types, index=suggested)
        addons = st.multiselect("Add-on services", list(ADDONS.keys()))

        ist_hour = datetime.now(timezone(timedelta(hours=5, minutes=30))).hour
        night = st.toggle("Night trip (10 PM – 6 AM)", value=(ist_hour >= 22 or ist_hour < 6))
        wait_min = st.slider("Waiting time (minutes)", 0, 120, 0, step=15)
        discount_pct = st.slider("Subsidy / insurance cover (%)", 0, 100, 0, step=5)

    lines, subtotal, total, total_km = estimate_bill(
        amb_type, pickup_km, trip_km, addons, night, wait_min, discount_pct
    )

    with right:
        rows = "".join(
            f"<tr><td>{html.escape(label)}</td><td>{'−' if amt < 0 else ''}{_inr(abs(amt))}</td></tr>"
            for label, amt in lines
        )
        st.markdown(
            _flat(f"""
            <div class="rq-invoice">
              <div style="font-weight:800;font-size:1.05rem;margin-bottom:4px;">
                {AMBULANCE_TYPES[amb_type]['icon']} Fare Estimate
              </div>
              <div style="color:#94a3b8;font-size:.82rem;margin-bottom:10px;">
                {html.escape(patient_name)} → {html.escape(hospital)} · {total_km:.1f} km total
              </div>
              <table>{rows}
                <tr class="rq-total"><td>Estimated total</td><td>{_inr(total)}</td></tr>
              </table>
            </div>
            """),
            unsafe_allow_html=True,
        )

        text_lines = [
            "RESQTRACK - AMBULANCE FARE ESTIMATE (DEMO)",
            f"Patient: {patient_name}",
            f"Route: {total_km:.1f} km -> {hospital}",
            f"Ambulance: {amb_type}",
            "-" * 44,
        ]
        text_lines += [f"{label}: {'-' if amt < 0 else ''}{_inr(abs(amt))}" for label, amt in lines]
        text_lines += ["-" * 44, f"TOTAL: {_inr(total)}", "Illustrative estimate only."]
        st.download_button(
            "⬇️ Download estimate (.txt)", "\n".join(text_lines),
            file_name="resqtrack_fare_estimate.txt", use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Live map tracker (Delhi)
# ---------------------------------------------------------------------------
def _build_map_frames(speed_mult: float):
    now = datetime.now(timezone.utc)
    ambs = list_ambulances()
    incs = list_active_incidents()
    inc_by_id = {i["incident_id"]: i for i in incs}

    amb_rows, route_rows = [], []
    for a in ambs:
        lat, lng = a.get("current_lat"), a.get("current_lng")
        if lat is None or lng is None:
            continue
        status = a["status"]
        info = status.title()
        color = [16, 185, 129, 230] if status == "AVAILABLE" else (
            [249, 115, 22, 230] if status == "ASSIGNED" else [148, 163, 184, 200]
        )
        inc = inc_by_id.get(a.get("assigned_incident_id"))
        if inc and inc.get("latitude") is not None and inc.get("longitude") is not None:
            ilat, ilng = inc["latitude"], inc["longitude"]
            dist_km = _hav(lat, lng, ilat, ilng) * ROAD_FACTOR
            eta_s = dist_km / BASE_SPEED_KMH * 3600 / speed_mult if dist_km > 0 else 0
            started = _parse_ts(inc.get("updated_at"))
            elapsed = (now - started).total_seconds() if started else 0
            if inc["status"] == "AT_HOSPITAL":
                progress = 1.0
            elif inc["status"] in ("DISPATCHED", "EN_ROUTE"):
                progress = 1.0 if eta_s <= 0 else min(1.0, max(0.0, elapsed / eta_s))
            else:
                progress = 0.0
            cur_lat = lat + (ilat - lat) * progress
            cur_lng = lng + (ilng - lng) * progress
            remaining_min = max(0.0, (1 - progress) * dist_km / BASE_SPEED_KMH * 60)
            info = f"Incident #{inc['incident_id']} · {inc['status']} · ETA {remaining_min:.0f} min (simulated)"
            route_rows.append({"from": [lng, lat], "to": [ilng, ilat]})
            lat, lng = cur_lat, cur_lng
        amb_rows.append({
            "name": a["ambulance_id"], "info": info,
            "driver": a.get("driver_name", ""), "lat": lat, "lng": lng, "color": color,
        })

    inc_rows = []
    for i in incs:
        if i.get("latitude") is None or i.get("longitude") is None:
            continue
        level = i.get("triage_level", "GREEN")
        inc_rows.append({
            "name": f"Incident #{i['incident_id']} ({level})",
            "info": f"{i.get('patient_name', '')} · {i.get('status', '')}",
            "driver": "", "lat": i["latitude"], "lng": i["longitude"],
            "color": TRIAGE_COLORS.get(level, [59, 130, 246, 230]),
        })

    hosp_rows = [
        {"name": n, "info": "Hospital", "driver": "", "lat": la, "lng": lo,
         "color": [56, 189, 248, 230]}
        for n, (la, lo) in HOSPITALS.items()
    ]
    return (
        pd.DataFrame(amb_rows), pd.DataFrame(inc_rows),
        pd.DataFrame(hosp_rows), pd.DataFrame(route_rows),
    )


def _map_body(speed_mult, layer_choices):
    amb_df, inc_df, hosp_df, route_df = _build_map_frames(speed_mult)

    def scatter(df, radius, min_px):
        return pdk.Layer(
            "ScatterplotLayer", data=df, get_position="[lng, lat]", get_fill_color="color",
            get_radius=radius, radius_min_pixels=min_px, radius_max_pixels=min_px * 3,
            pickable=True, stroked=True, get_line_color=[255, 255, 255, 220],
            line_width_min_pixels=1,
        )

    layers = []
    if "Hospitals" in layer_choices and not hosp_df.empty:
        layers.append(scatter(hosp_df, 350, 7))
    if "Routes" in layer_choices and not route_df.empty:
        layers.append(pdk.Layer(
            "LineLayer", data=route_df, get_source_position="from", get_target_position="to",
            get_color=[255, 255, 255, 140], get_width=3,
        ))
    if "Incidents" in layer_choices and not inc_df.empty:
        layers.append(scatter(inc_df, 400, 9))
    if "Ambulances" in layer_choices and not amb_df.empty:
        layers.append(scatter(amb_df, 300, 8))

    deck = pdk.Deck(
        map_provider="carto", map_style=pdk.map_styles.CARTO_DARK,
        initial_view_state=pdk.ViewState(
            latitude=DEMO_CENTER_LAT, longitude=DEMO_CENTER_LNG, zoom=10.3, pitch=0,
        ),
        layers=layers,
        tooltip={"html": "<b>{name}</b><br/>{info}<br/>{driver}",
                 "style": {"backgroundColor": "#0f172a", "color": "white"}},
    )
    st.pydeck_chart(deck)

    st.markdown(
        _flat("""
        <div class="rq-legend">
          <span>🟢 Ambulance (available)</span><span>🟠 Ambulance (assigned)</span>
          <span>🔴🟡🟢 Incident by triage</span><span>🔵 Hospital</span>
        </div>
        """),
        unsafe_allow_html=True,
    )

    if not amb_df.empty:
        table = amb_df[["name", "driver", "info"]].rename(
            columns={"name": "Unit", "driver": "Driver", "info": "Status / ETA"}
        )
        st.dataframe(table, use_container_width=True, hide_index=True)


_map_body_auto = st.fragment(run_every=5)(_map_body) if hasattr(st, "fragment") else _map_body


def render_live_map():
    st.subheader("🗺️ Live Map Tracker — Delhi")
    st.caption(
        "Ambulance movement is SIMULATED from dispatch time and straight-line distance; "
        "no real GPS hardware is connected."
    )
    c1, c2, c3 = st.columns([1, 1, 2])
    auto = c1.toggle("Auto-refresh (5 s)", value=False)
    speed = c2.select_slider("Simulation speed", options=[1, 5, 10, 30], value=10, format_func=lambda x: f"{x}×")
    layer_choices = c3.multiselect(
        "Map layers", ["Ambulances", "Incidents", "Hospitals", "Routes"],
        default=["Ambulances", "Incidents", "Hospitals", "Routes"],
    )
    if auto:
        _map_body_auto(speed, layer_choices)
    else:
        if st.button("🔄 Refresh positions"):
            st.rerun()
        _map_body(speed, layer_choices)


# ---------------------------------------------------------------------------
# Clickable flashcards
# ---------------------------------------------------------------------------
FEATURES = [
    ("🫀", "Cardiac Monitor & ECG", "Tracks heart rhythm and vitals live.",
     "Continuously displays heart rhythm, heart rate, SpO₂ and blood pressure. Crews can capture an ECG "
     "and share it with the receiving hospital so the cardiac team is ready on arrival."),
    ("⚡", "Defibrillator (AED)", "Restores rhythm in cardiac arrest.",
     "Analyses the heart rhythm and delivers a controlled shock when a shockable rhythm is detected. "
     "Ambulances usually carry an AED or a manual defibrillator."),
    ("🫁", "Oxygen & Airway Kit", "Breathing support from the first minute.",
     "Oxygen cylinders with masks, a bag-valve mask, suction unit and airway adjuncts to keep the airway "
     "open and the patient oxygenated during transport."),
    ("🌬️", "Ventilator", "Machine-assisted breathing (ICU units).",
     "ICU-grade ambulances carry a transport ventilator for patients who cannot breathe adequately on "
     "their own, with adjustable rate, volume and oxygen concentration."),
    ("🛏️", "Stretcher & Spine Board", "Safe lifting and immobilisation.",
     "Wheeled stretcher, scoop stretcher, spine board and cervical collar to move patients with "
     "suspected spinal or limb injuries without making them worse."),
    ("🩹", "Trauma & Bleeding Control", "Stops bleeding and stabilises injuries.",
     "Tourniquets, pressure dressings, splints and IV fluids for road accidents, falls and other "
     "trauma where every minute of blood loss counts."),
    ("💊", "Emergency Drug Box", "Locked kit of life-saving medicines.",
     "Contains emergency medicines (for example for pain, allergic reactions or cardiac events) that "
     "trained crew administer under medical protocols."),
    ("🧑‍⚕️", "Trained Crew", "Driver, EMT, paramedic or doctor.",
     "Crew level depends on the ambulance type: BLS carries an EMT, ALS adds a paramedic, and ICU units "
     "add a nurse or doctor."),
    ("📡", "GPS, Siren & Radio", "Fast routing and constant contact.",
     "GPS lets the control room see the nearest free unit, the siren and lights clear traffic, and the "
     "radio keeps crew, dispatch and the hospital in sync."),
]


def _card(icon, title, summary, detail):
    return _flat(f"""
    <details class="rq-flip">
      <summary>
        <div class="rq-ico">{icon}</div>
        <div class="rq-t">{html.escape(title)}</div>
        <div class="rq-s">{html.escape(summary)}</div>
        <div class="rq-hint">▸ Click to flip</div>
      </summary>
      <div class="rq-d">{html.escape(detail)}</div>
    </details>
    """)


def _grid(cards, per_row=3):
    for start in range(0, len(cards), per_row):
        cols = st.columns(per_row)
        for col, card in zip(cols, cards[start:start + per_row]):
            with col:
                st.markdown(card, unsafe_allow_html=True)


def render_feature_cards():
    st.subheader("🚑 Ambulance Features & Types")
    st.caption("Click any card to see more. General educational information.")

    st.markdown("### Onboard equipment")
    _grid([_card(*f) for f in FEATURES])

    st.markdown("### Ambulance types & illustrative rates")
    type_cards = []
    for name, t in AMBULANCE_TYPES.items():
        detail = (
            f"{t['desc']} Crew: {t['crew']}. Illustrative tariff: {_inr(t['base'])} base "
            f"(first {t['included_km']} km) + {_inr(t['per_km'])}/km."
        )
        type_cards.append(_card(t["icon"], name, f"From {_inr(t['base'])}", detail))
    _grid(type_cards, per_row=2)