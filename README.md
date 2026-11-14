# 🚑 AmbuPriority — National Emergency Medical Priority Routing & Triage System

[![Government Standard](https://img.shields.io/badge/MoHFW-Clinical_Triage_Standard-blue?style=for-the-badge&logo=shield)](https://www.mohfw.gov.in/)
[![Vehicle Standard](https://img.shields.io/badge/AIS--125-Road_Ambulance_Compliance-orange?style=for-the-badge)](https://morth.nic.in/)
[![Triage Tool](https://img.shields.io/badge/WHO--IITT-Emergency_Assessment-green?style=for-the-badge)](https://www.who.int/)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)

> **⚠️ ACADEMIC & DEMONSTRATION NOTICE:**  
> This portal and clinical triage algorithms are developed strictly for **academic demonstration, research, and emergency corridor simulation purposes**. For actual real-world medical emergencies in India, dial **112** or **108** immediately.

---

## 📌 Project Overview

**AmbuPriority** is an intelligent emergency ambulance allocation, clinical triage, and hospital suitability recommendation platform aligned with official Indian National Health Authority (NHA), WHO Interagency Integrated Triage Tool (IITT), and Automotive Industry Standard (AIS-125) norms.

The platform provides a complete digital emergency lifecycle:
1. **Patient Intake & Registration** (`register.html`): Rapid geolocation lookup, chief complaint, caller identity verification.
2. **Clinical Triage Survey** (`assessment.html`): ABCDE survey + targeted symptom evaluator assigning **RED**, **YELLOW**, or **GREEN** priority.
3. **Condition-Matched Hospital Discovery** (`hospitals.html`): Recommends nearest verified medical facilities ranked by specialty match (Cardiology, Trauma, OBGYN, Burn) and bed/ICU capability.
4. **Live Smart Ambulance Dispatch & Corridor Animation** (`allocation.html`): Real-time route tracking, live speed/ETA estimation, and turn-by-turn navigation from depot to patient pickup and destination hospital.
5. **System Standards & Bilingual Documentation** (`detail.html`): Complete transparency into AIS-125 fleet types (PTV, BLS, ALS, Mobile ICU, Cardiac, Neonatal) and emergency response reports.
6. **ARIA 3D AI Virtual Assistant** (`assistant.js`): Intelligent procedural 3D avatar & conversational assistant providing real-time guidance, intake assistance, and triage explanations in English and Hindi.

---

## 🤖 ARIA (Ambulance Response Intelligent Assistant)

**ARIA** is an interactive, browser-native 3D AI Virtual Assistant integrated across the AmbuPriority portal:
* **Three.js Powered 3D Avatar:** Procedurally modeled and animated 3D character with real-time responsive states (`idle`, `greeting`, `thinking`, `responding`, `error`).
* **Bilingual Intelligence (English & हिंदी):** Understands queries and form-filling questions in both languages, seamlessly synced with the portal's language toggle.
* **Emergency Domain Knowledge Base:** Provides immediate answers on triage priority meanings, AIS-125 ambulance types, GPS geolocation usage, hospital capability matching, and emergency protocols (102/108/112).
* **Zero External Dependencies:** Built with a self-contained local knowledge engine for instantaneous offline-capable client responses.

---

## 💳 Real Insurance & Government Scheme Empanelment (Live API & Verification)

The system features an automated insurance verification engine (`src/hospital_panel_service.py` & `src/insurance_discovery_service.py`):
* **Real-World Insurance & TPA Matching:** Cross-references patient insurance providers (Star Health, HDFC ERGO, Care, ICICI Lombard, Niva Bupa, Bajaj Allianz, Max Bupa) against hospital Third-Party Administrator (TPA) desks.
* **Government Health Schemes:** Real-time checking for **Ayushman Bharat (PM-JAY)**, **CGHS** (Central Government Health Scheme), **ECHS** (Ex-Servicemen Contributory Health Scheme), and State Government Health Schemes (DGEHS).
* **Live Discovery & AI Research Fallback:** Integrates live panel research APIs and Google Gemini web search grounding to dynamically discover, verify, and cache cashless empanelment status for unverified hospitals.
* **Cashless Admission Badges:** Color-coded badges display whether a hospital supports instant cashless admission, reimbursement, or government scheme coverage.

---

## 🏥 Clinical Triage Framework

Triage priority is determined sequentially through deterministic WHO-IITT protocols:

| Priority | Clinical Status | Target Response | Clinical Triggers | Recommended Fleet |
| :--- | :--- | :--- | :--- | :--- |
| **🔴 RED** | **Immediate Life Threat** | `< 8 mins` | Unresponsive (AVPU), apnea/respiratory distress, severe spurting bleeding, crushing chest pain radiating to arm with shock, stroke FAST positive, active seizures, maternal crowning/trauma/eclampsia. | **Type-D ALS / Mobile ICU** (Ventilator, Defibrillator, ACLS Nurse) |
| **🟡 YELLOW** | **Urgent Emergency** | `< 20 mins` | Moderate dyspnea/wheezing, excruciating abdominal pain without peritonitis, closed fractures, first-time seizure resolved, high persistent fever. *(All pregnancy calls without red flags are minimum YELLOW per GVK EMRI 102).* | **Type-C BLS** (Oxygen cylinder, AED, EMT-Basic) |
| **🟢 GREEN** | **Non-Urgent / Stable** | `< 45 mins` | Normal comfortable breathing, fully alert, clear airway, all stroke FAST signs negative, mild discomfort, minor superficial cuts/sprains. | **Type-A/B PTV** (Stretcher, First Aid Kit, Wheelchair Ramp) |

---

## 🚑 AIS-125 Ambulance Fleet Classification

Under National Health Mission norms, ambulances are categorized based on clinical equipment loadout:

* **Type A / B — PTV (Patient Transport Vehicle):** Non-emergency planned transfers, stretcher, wheelchair access, transport attendant.
* **Type C — BLS (Basic Life Support):** Core 108 emergency vehicle, automated external defibrillator (AED), oxygen cylinders, suction unit, spine board, EMT-Basic.
* **Type D — ALS (Advanced Life Support):** Mechanical transport ventilator, multi-channel cardiac monitor/defibrillator, intubation kit, ACLS paramedic & emergency nurse.
* **Mobile ICU:** Hospital-to-hospital tertiary transfers for multi-organ failure patients, ABG lab, invasive pressure lines, critical care intensivist doctor.
* **Dedicated Cardiac Care Unit:** STEMI/heart attack response with direct catheterization lab telemedicine relay & cardiology fellow.
* **Neonatal / NICU Transport:** Custom incubator with temperature servo-control, micro-airways, and neonatologist.

---

## 📂 Repository Directory Structure

```plaintext
AmbuPriority/
├── app.py                       # Application entrypoint
├── config.py                    # Environment & system configurations
├── requirements.txt             # Python dependencies
├── Procfile                     # Deployment process definition
├── render.yaml                  # Cloud deployment configuration
├── .env.example                 # Sample environment variables
├── .gitignore                   # Ignored files for git
├── README.md                    # Detailed documentation
│
├── src/                         # Backend Python Services
│   ├── assessment_api.py        # Starlette ASGI backend & REST endpoints
│   ├── triage_engine.py         # WHO-IITT / GVK EMRI clinical triage engine
│   ├── hospital_facilities_service.py # Verified hospital directory & capability scoring
│   ├── ambulance_registry.py    # Persistent ambulance fleet & suitability matcher
│   ├── ambulance_fare_service.py # Fare engine & state regulatory caps
│   ├── hospital_panel_service.py# Insurance / Ayushman Bharat empanelment checker
│   └── geocode_service.py       # Reverse geocoding & coordinates service
│
├── public/                      # Frontend Web Portal (GIGW 3.0 / UX4G compliant)
│   ├── index.html               # Main national portal homepage
│   ├── register.html            # Emergency citizen intake & call form
│   ├── assessment.html          # Clinical symptom survey & priority assessment
│   ├── hospitals.html           # Hospital discovery, capability matrix & cost estimation
│   ├── allocation.html          # Full-screen GPS map, ambulance allocation & tracking
│   ├── detail.html              # About System, AIS-125 fleet standards & statistics
│   ├── gov-portal.css           # Government design system stylesheet
│   ├── gov-portal.js            # Bilingual controller (English ⇄ Hindi translation)
│   ├── assistant.js             # ARIA 3D AI assistant module
│   └── assistant.css            # Virtual assistant stylesheet
│
└── data/                        # Static JSON Databases
    ├── hospital_directory.json  # Comprehensive hospitals list with specialties
    ├── ambulances.json          # Pre-registered AIS-125 ambulance fleet records
    ├── hospital_empanelment.json# Insurance empanelment registry
    └── assessments/             # Storage for clinical triage assessments (.gitkeep)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python `3.10` or higher installed
* Modern Web Browser (Chrome, Firefox, Edge, Safari)

### 2. Clone / Setup the Repository
```bash
git clone https://github.com/your-username/AmbuPriority.git
cd AmbuPriority
```

### 3. Create a Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional: add your Google Gemini API key if utilizing generative panels).*

### 5. Launch the Server
```bash
python -m uvicorn src.assessment_api:app --host 0.0.0.0 --port 5001 --reload
```

### 6. Open the Web Application
Open your browser and navigate to:
```
http://127.0.0.1:5001/
```
Or view the pages directly:
* **Citizen Emergency Registration:** `http://127.0.0.1:5001/register.html`
* **Clinical Triage Survey:** `http://127.0.0.1:5001/assessment.html`
* **Hospital Matching & Recommendations:** `http://127.0.0.1:5001/hospitals.html`
* **Live GPS Ambulance Tracking:** `http://127.0.0.1:5001/allocation.html`
* **About System & Fleet Standards:** `http://127.0.0.1:5001/detail.html`

---

## 🌐 Bilingual Support (English / हिंदी)

The entire user interface conforms to the **Guidelines for Indian Government Websites (GIGW 3.0)** and provides instant language switching:
* Click **"हिंदी"** in the top accessibility bar on any page to switch the entire application, clinical criteria, flowchart steps, and reports into clean Devanagari Hindi.
* Click **"English"** to switch back seamlessly without page reloads.

---

## 📄 License & Attribution

Developed under open-source educational guidelines. Clinical protocols referenced from:
* **Ministry of Health & Family Welfare (MoHFW)**
* **WHO Interagency Integrated Triage Tool (WHO-IITT 2020)**
* **Automotive Industry Standard AIS-125 (MoRTH / ARAI)**
* **GVK Emergency Management and Research Institute (EMRI 108/102 Protocols)**
