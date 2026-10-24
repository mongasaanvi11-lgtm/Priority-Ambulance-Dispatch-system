# Priority-Ambulance-Dispatch-system
AI/ML-powered Priority Ambulance Dispatch System built with Python and Streamlit. Classifies emergency cases into Red, Yellow, and Green priorities, assigns the nearest available ambulance, and provides a real-time dashboard for emergency monitoring and dispatch management.
# 🚑 ResQTrack: Priority Ambulance Dispatch System
> **Educational Prototype for Intelligent Emergency Triage and Priority-Based Resource Allocation**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework-Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Database-SQLite3](https://img.shields.io/badge/DB-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![ML-Scikit--Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Tests-Unittest](https://img.shields.io/badge/Tests-30%20Passed-brightgreen.svg)](#running-the-automated-tests)
[![License-Educational](https://img.shields.io/badge/License-Educational%20Use%20Only-orange.svg)](#disclaimer)

---

## ⚠️ Important Educational Disclaimer

> **CRITICAL NOTICE**:  
> **ResQTrack is an academic educational prototype developed for computer science coursework and demonstrations. It is NOT a certified clinical decision-support system or an operational emergency dispatch service.**  
> 
> The triage rules, ML classification models, and urgency scores are simulated demonstrations and have **NOT** been clinically validated. **Do NOT use this software for actual medical emergencies.** If you or someone near you is in medical distress, immediately call your local emergency services (e.g., **911**, **112**, **999**). **No real ambulances are dispatched by this application.**

---

## 📌 Project Overview

Traditional ambulance dispatching often operates on a first-come, first-served basis, which can result in life-threatening emergencies waiting behind minor injuries.

**ResQTrack** demonstrates an intelligent dispatch workflow:
1. **Patient Intake Form**: Collects patient name, age, gender, contact, address/location text, GPS coordinates, optional vital signs ($SpO_2$, heart rate, systolic/diastolic BP, temperature in °F), symptoms checklist, and pain scale (1–10). Blank vital signs are fully supported.
2. **Two-Stage Triage Engine**:
   - **Stage 1 (Rule-Based Safety Net — DEMO ONLY)**: Immediately flags critical conditions (*chest pain, shortness of breath, loss of consciousness, uncontrolled bleeding*) as 🔴 **RED (Priority 1)** without waiting for machine learning.
   - **Stage 2 (Scikit-Learn Classifier — DEMO ONLY)**: Tiny, cached Decision Tree classifier trained on synthetic demo examples that outputs probabilities for Red, Yellow, and Green. If scikit-learn is unavailable, a deterministic fallback ensures zero crashes.
3. **Deterministic Priority Queue**: Orders calls strictly by severity:
   $$\text{RED (Priority 1)} > \text{YELLOW (Priority 2)} > \text{GREEN (Priority 3)}$$
   Uses a documented demo urgency score and creation timestamp (waiting time) as a fair tie-breaker.
4. **Haversine Distance Dispatch**: Calculates straight-line Haversine distance in kilometers to locate and assign the nearest **AVAILABLE** ambulance with valid coordinates, enforcing single-vehicle assignment locks.
5. **Dispatcher Dashboard**: Real-time incident queue, Red/Yellow/Green badges, straight-line distance estimates, ambulance fleet status grid, "Dispatch Next" button, and status lifecycle progression (`DISPATCHED` → `EN_ROUTE` → `AT_HOSPITAL` → `COMPLETED`), automatically releasing the ambulance upon completion.

---

## 💾 Database Schema (SQLite)

The persistence layer (`ambulance_dispatch/database.py`) operates with SQLite foreign key enforcement enabled (`PRAGMA foreign_keys = ON;`) and isolates patient demo records into a `data/` directory (git-ignored):

### 1. `incidents` Table
* `incident_id`: Integer primary key (Auto-increment).
* `patient_name`, `age`, `gender`, `contact`: Demographic inputs.
* `location_text`, `latitude`, `longitude`: Geospatial location coordinates.
* `heart_rate`, `systolic_bp`, `diastolic_bp`, `spo2`, `temperature_f`: Optional vital signs.
* `symptoms_json`: JSON-encoded checklist of reported symptoms (validated on read).
* `primary_symptom`, `pain_level` (1–10): Clinical triage attributes.
* `triage_level` (`RED`, `YELLOW`, `GREEN`): Assigned severity tier.
* `p_red`, `p_yellow`, `p_green`: ML-derived probability distribution.
* `demo_priority_score`: Calculated floating-point priority score.
* `status` (`PENDING`, `DISPATCHED`, `EN_ROUTE`, `AT_HOSPITAL`, `COMPLETED`, `CANCELLED`): Lifecycle status.
* `created_at`, `updated_at`: UTC ISO8601 timestamps.

### 2. `ambulances` Table
* `ambulance_id`: String primary key (`AMB-101` through `AMB-105`).
* `driver_name`: Name of assigned paramedic / driver.
* `current_lat`, `current_lng`: Fictional GPS coordinates in Metro City.
* `status` (`AVAILABLE`, `ASSIGNED`, `OFF_DUTY`): Fleet availability status.
* `assigned_incident_id`: Foreign key referencing `incidents(incident_id)` (Null when available).
* `updated_at`: UTC timestamp.

### 3. `dispatch_events` Table (Append-only Audit Log)
* `event_id`: Integer primary key (Auto-increment).
* `incident_id`: Foreign key referencing `incidents(incident_id)`.
* `ambulance_id`: Foreign key referencing `ambulances(ambulance_id)` (Nullable).
* `event_type`: Event category (e.g., `INCIDENT_CREATED`, `AMBULANCE_DISPATCHED`, `AMBULANCE_RELEASED`).
* `event_time`: UTC timestamp.
* `note`: Human-readable non-sensitive event description.

---

## 📂 Project Structure

```text
resqtrack/
├── AGENTS.md                          # Persistent agent & developer directives
├── README.md                          # Project documentation and setup guide
├── requirements.txt                   # Project Python dependencies
├── .gitignore                         # Excludes data/, *.db, and virtualenvs
├── app.py                             # Main Streamlit web application
├── 00_PROJECT_OVERVIEW.md             # Beginner-friendly conceptual overview
├── data/                              # Local SQLite database directory (git-ignored)
│   └── dispatch.db                    # Active SQLite database file
├── ambulance_dispatch/                # Core Python package
│   ├── __init__.py                    # Package exports
│   ├── config.py                      # Centralized paths and demo city coordinates
│   ├── constants.py                   # Triage enums, colors, symptoms, and disclaimers
│   ├── database.py                    # SQLite persistence layer and atomic transactions
│   ├── dispatcher.py                  # Priority queue sorting and dispatch allocation
│   ├── geo.py                         # Haversine straight-line distance calculations
│   ├── seed_data.py                   # Idempotent fictional demo incident loader
│   └── triage.py                      # Two-stage triage engine & Scikit-Learn model
├── docs/                              # Project documentation
│   ├── IMPLEMENTATION_PLAN.md         # Phased roadmap & testing checkpoints
│   └── DECISIONS_AND_OPEN_QUESTIONS.md# Architectural decisions & schema rationale
└── tests/                             # Automated test suite (unittest compatible)
    ├── __init__.py
    ├── test_scaffold.py               # Tests for constants, statuses, and disclaimers
    ├── test_database.py               # Tests for SQLite CRUD, foreign keys, and atomic locks
    └── test_dispatch_and_triage.py     # Tests for Haversine, triage rules, queue sorting, and dispatch
```

---

## 🚀 Getting Started & Execution

### 1. Launch the Application
Run the Streamlit application from your terminal:
```powershell
py -m streamlit run app.py
```
*(On macOS/Linux: `streamlit run app.py`)*

The browser will open automatically at `http://localhost:8501`.

### 2. Running the Automated Tests
Run the complete unittest test suite (30 unit tests):
```powershell
py -m unittest discover -s tests -v
```

### 3. Running Bytecode Compilation Check
Verify all files compile without syntax or bytecode errors:
```powershell
py -m compileall -q ambulance_dispatch app.py
```

---

## ⚠️ Known Limitations & Assumptions

* **Straight-Line Distance**: Distance calculations use the spherical Haversine formula. They represent straight-line Euclidean approximations and do **not** account for real-world road networks, traffic delays, elevation, or travel ETA.
* **Synthetic ML Classifier**: The Scikit-Learn Decision Tree model is trained on a small set of synthetic demo numbers for academic illustration. It is **not clinically validated**.
* **Simulation Bounds**: The demo fleet operates in a simulated city grid (`Metro City`).
* **Educational Scope**: No user authentication, live GPS hardware tracking, payment systems, or external hospital APIs are implemented.
