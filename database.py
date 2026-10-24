"""
SQLite persistence layer for ResQTrack ambulance dispatch system.
Provides idempotent schema creation, parameterized CRUD operations,
atomic dispatch transactions, and fictional fleet seeding.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import DEFAULT_DB_PATH, EVENT_TYPE_AMBULANCE_DISPATCHED, EVENT_TYPE_INCIDENT_CREATED
from .constants import AmbulanceStatus, IncidentStatus, TriageLevel


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class IncidentNotFoundError(DatabaseError):
    """Raised when a requested incident cannot be found."""
    pass


class AmbulanceNotFoundError(DatabaseError):
    """Raised when a requested ambulance cannot be found."""
    pass


class AmbulanceNotAvailableError(DatabaseError):
    """Raised when an ambulance is already assigned or not available for dispatch."""
    pass


def _get_utc_now() -> str:
    """Return current ISO8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Open an SQLite connection with WAL mode, row factory, and foreign key enforcement enabled.
    """
    path_to_use = db_path if db_path is not None else DEFAULT_DB_PATH
    
    # Ensure directory exists if it's a file path
    if path_to_use != ":memory:":
        parent_dir = Path(path_to_use).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path_to_use)
    conn.row_factory = sqlite3.Row
    # Enforce SQLite foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Idempotently initialize all database tables and seed fictional demo fleet if empty.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Incidents Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    contact TEXT,
                    location_text TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    heart_rate INTEGER,
                    systolic_bp INTEGER,
                    diastolic_bp INTEGER,
                    spo2 REAL,
                    temperature_f REAL,
                    symptoms_json TEXT NOT NULL DEFAULT '[]',
                    primary_symptom TEXT,
                    pain_level INTEGER DEFAULT 1,
                    triage_level TEXT NOT NULL DEFAULT 'GREEN',
                    p_red REAL DEFAULT 0.0,
                    p_yellow REAL DEFAULT 0.0,
                    p_green REAL DEFAULT 1.0,
                    demo_priority_score REAL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

            # 2. Ambulances Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ambulances (
                    ambulance_id TEXT PRIMARY KEY,
                    driver_name TEXT NOT NULL,
                    current_lat REAL NOT NULL,
                    current_lng REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'AVAILABLE',
                    assigned_incident_id INTEGER,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (assigned_incident_id) REFERENCES incidents (incident_id) ON DELETE SET NULL
                );
                """
            )

            # 3. Dispatch Events (Append-only audit trail)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dispatch_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER NOT NULL,
                    ambulance_id TEXT,
                    event_type TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    note TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents (incident_id) ON DELETE CASCADE,
                    FOREIGN KEY (ambulance_id) REFERENCES ambulances (ambulance_id) ON DELETE SET NULL
                );
                """
            )

            # Indexes for efficient queue and dispatch queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incidents_status_prio ON incidents (status, demo_priority_score DESC);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ambulances_status ON ambulances (status);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_incident ON dispatch_events (incident_id);"
            )
        
        # Seed fictional demo fleet if ambulances table is empty
        seed_demo_fleet_if_empty(db_path=db_path)
    finally:
        conn.close()


def seed_demo_fleet_if_empty(db_path: Optional[str] = None) -> int:
    """
    Seed an initial fictional fleet of 5 ambulances if no ambulances exist.
    Idempotent: will not create duplicates if ambulances already exist.
    Returns the number of seeded ambulances (0 if already seeded).
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM ambulances;")
        count = cursor.fetchone()[0]
        if count > 0:
            return 0

        now = _get_utc_now()
        fictional_fleet = [
            ("AMB-101", "Paramedic Alex Rivers", 12.9750, 77.5900, AmbulanceStatus.AVAILABLE.value, None, now),
            ("AMB-102", "Paramedic Jordan Lee", 12.9650, 77.6000, AmbulanceStatus.AVAILABLE.value, None, now),
            ("AMB-103", "Paramedic Taylor Morgan", 12.9800, 77.6100, AmbulanceStatus.AVAILABLE.value, None, now),
            ("AMB-104", "Paramedic Casey Chen", 12.9550, 77.5850, AmbulanceStatus.AVAILABLE.value, None, now),
            ("AMB-105", "Paramedic Riley Patel", 12.9900, 77.5800, AmbulanceStatus.AVAILABLE.value, None, now),
        ]

        with conn:
            conn.executemany(
                """
                INSERT INTO ambulances (
                    ambulance_id, driver_name, current_lat, current_lng, status, assigned_incident_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                fictional_fleet,
            )
        return len(fictional_fleet)
    finally:
        conn.close()


def _parse_incident_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Helper to convert sqlite3.Row to dict and parse symptoms_json safely."""
    data = dict(row)
    raw_symptoms = data.get("symptoms_json", "[]")
    try:
        parsed_symptoms = json.loads(raw_symptoms) if raw_symptoms else []
        if not isinstance(parsed_symptoms, list):
            parsed_symptoms = [str(parsed_symptoms)]
    except (json.JSONDecodeError, TypeError):
        parsed_symptoms = []
    data["symptoms"] = parsed_symptoms
    return data


def create_incident(incident_data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """
    Create a new emergency incident record and log its creation event.
    Returns the generated incident_id.
    """
    now = _get_utc_now()
    
    # Validate and encode symptoms
    symptoms = incident_data.get("symptoms", [])
    if isinstance(symptoms, list):
        symptoms_json = json.dumps(symptoms)
    elif isinstance(symptoms, str):
        try:
            # Check if it's already a JSON string
            json.loads(symptoms)
            symptoms_json = symptoms
        except json.JSONDecodeError:
            symptoms_json = json.dumps([symptoms])
    else:
        symptoms_json = json.dumps([])

    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO incidents (
                    patient_name, age, gender, contact, location_text,
                    latitude, longitude, heart_rate, systolic_bp, diastolic_bp,
                    spo2, temperature_f, symptoms_json, primary_symptom, pain_level,
                    triage_level, p_red, p_yellow, p_green, demo_priority_score,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    incident_data.get("patient_name", "Anonymous"),
                    incident_data.get("age"),
                    incident_data.get("gender"),
                    incident_data.get("contact"),
                    incident_data.get("location_text", "Unknown Location"),
                    float(incident_data.get("latitude", 0.0)),
                    float(incident_data.get("longitude", 0.0)),
                    incident_data.get("heart_rate"),
                    incident_data.get("systolic_bp"),
                    incident_data.get("diastolic_bp"),
                    incident_data.get("spo2"),
                    incident_data.get("temperature_f"),
                    symptoms_json,
                    incident_data.get("primary_symptom"),
                    int(incident_data.get("pain_level", 1)),
                    incident_data.get("triage_level", TriageLevel.GREEN.value),
                    float(incident_data.get("p_red", 0.0)),
                    float(incident_data.get("p_yellow", 0.0)),
                    float(incident_data.get("p_green", 1.0)),
                    float(incident_data.get("demo_priority_score", 0.0)),
                    incident_data.get("status", IncidentStatus.PENDING.value),
                    now,
                    now,
                ),
            )
            incident_id = cursor.lastrowid

            # Log audit event
            conn.execute(
                """
                INSERT INTO dispatch_events (
                    incident_id, ambulance_id, event_type, event_time, note
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    incident_id,
                    None,
                    EVENT_TYPE_INCIDENT_CREATED,
                    now,
                    f"Incident created with initial triage level {incident_data.get('triage_level', 'GREEN')}",
                ),
            )
        return incident_id
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to create incident: {e}") from e
    finally:
        conn.close()


def get_incident(incident_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve full incident details by ID. Returns None if not found."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM incidents WHERE incident_id = ?;",
            (incident_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return _parse_incident_row(row)
    finally:
        conn.close()


def list_incidents(
    status: Optional[str] = None,
    triage_level: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List incidents with optional status and triage level filters.
    Sorted by urgency: demo_priority_score DESC, created_at ASC.
    """
    query = "SELECT * FROM incidents WHERE 1=1"
    params: List[Any] = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if triage_level:
        query += " AND triage_level = ?"
        params.append(triage_level)

    query += " ORDER BY demo_priority_score DESC, created_at ASC;"

    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(query, params)
        return [_parse_incident_row(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def list_active_incidents(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all active incidents currently pending, dispatched, en route, or at hospital.
    Ordered by priority rank (RED > YELLOW > GREEN), demo_priority_score DESC, created_at ASC.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT * FROM incidents
            WHERE status IN (?, ?, ?, ?)
            ORDER BY 
                CASE triage_level 
                    WHEN 'RED' THEN 1 
                    WHEN 'YELLOW' THEN 2 
                    WHEN 'GREEN' THEN 3 
                    ELSE 4 
                END ASC,
                demo_priority_score DESC, 
                created_at ASC;
            """,
            (
                IncidentStatus.PENDING.value,
                IncidentStatus.DISPATCHED.value,
                IncidentStatus.EN_ROUTE.value,
                IncidentStatus.AT_HOSPITAL.value,
            ),
        )
        return [_parse_incident_row(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def progress_incident_status(
    incident_id: int,
    new_status: str,
    note: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """
    Progress incident along its lifecycle:
    PENDING -> DISPATCHED -> EN_ROUTE -> AT_HOSPITAL -> COMPLETED / CANCELLED.
    
    If new_status is COMPLETED, RESOLVED, or CANCELLED, any ambulance assigned
    to this incident is automatically released back to AVAILABLE status.
    All operations are committed in a single atomic transaction.
    """
    now = _get_utc_now()
    terminal_statuses = [
        IncidentStatus.COMPLETED.value,
        IncidentStatus.RESOLVED.value,
        IncidentStatus.CANCELLED.value,
    ]

    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Update incident status
            cursor = conn.execute(
                """
                UPDATE incidents
                SET status = ?, updated_at = ?
                WHERE incident_id = ?;
                """,
                (new_status, now, incident_id),
            )
            if cursor.rowcount == 0:
                return False

            # 2. If terminal status, release assigned ambulance
            if new_status in terminal_statuses:
                amb_cursor = conn.execute(
                    """
                    SELECT ambulance_id FROM ambulances
                    WHERE assigned_incident_id = ?;
                    """,
                    (incident_id,),
                )
                assigned_ambs = amb_cursor.fetchall()
                for amb_row in assigned_ambs:
                    amb_id = amb_row["ambulance_id"]
                    conn.execute(
                        """
                        UPDATE ambulances
                        SET status = ?, assigned_incident_id = NULL, updated_at = ?
                        WHERE ambulance_id = ?;
                        """,
                        (AmbulanceStatus.AVAILABLE.value, now, amb_id),
                    )
                    conn.execute(
                        """
                        INSERT INTO dispatch_events (
                            incident_id, ambulance_id, event_type, event_time, note
                        ) VALUES (?, ?, ?, ?, ?);
                        """,
                        (
                            incident_id,
                            amb_id,
                            "AMBULANCE_RELEASED",
                            now,
                            f"Ambulance {amb_id} released back to AVAILABLE after incident reached {new_status}",
                        ),
                    )

            # 3. Log incident status progression event
            conn.execute(
                """
                INSERT INTO dispatch_events (
                    incident_id, ambulance_id, event_type, event_time, note
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    incident_id,
                    None,
                    f"STATUS_PROGRESSION_{new_status}",
                    now,
                    note or f"Incident progressed to {new_status}",
                ),
            )
        return True
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to progress incident status: {e}") from e
    finally:
        conn.close()


def update_incident_status(
    incident_id: int,
    status: str,
    note: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Update status of an incident and log a status change event."""
    now = _get_utc_now()
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                UPDATE incidents
                SET status = ?, updated_at = ?
                WHERE incident_id = ?;
                """,
                (status, now, incident_id),
            )
            if cursor.rowcount == 0:
                return False

            conn.execute(
                """
                INSERT INTO dispatch_events (
                    incident_id, ambulance_id, event_type, event_time, note
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    incident_id,
                    None,
                    f"STATUS_UPDATE_TO_{status}",
                    now,
                    note or f"Incident status changed to {status}",
                ),
            )
        return True
    finally:
        conn.close()


def list_ambulances(
    status: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List all ambulances, optionally filtered by status (AVAILABLE, ASSIGNED, OFF_DUTY)."""
    query = "SELECT * FROM ambulances"
    params: List[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY ambulance_id ASC;"

    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_ambulance(ambulance_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve details of a single ambulance by ID."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM ambulances WHERE ambulance_id = ?;",
            (ambulance_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_ambulance_status(
    ambulance_id: str,
    status: str,
    assigned_incident_id: Optional[int] = None,
    current_lat: Optional[float] = None,
    current_lng: Optional[float] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Update status, location, and assigned incident for an ambulance."""
    now = _get_utc_now()
    conn = get_db_connection(db_path)
    try:
        with conn:
            # Dynamic update query based on provided coordinates
            if current_lat is not None and current_lng is not None:
                cursor = conn.execute(
                    """
                    UPDATE ambulances
                    SET status = ?, assigned_incident_id = ?, current_lat = ?, current_lng = ?, updated_at = ?
                    WHERE ambulance_id = ?;
                    """,
                    (status, assigned_incident_id, current_lat, current_lng, now, ambulance_id),
                )
            else:
                cursor = conn.execute(
                    """
                    UPDATE ambulances
                    SET status = ?, assigned_incident_id = ?, updated_at = ?
                    WHERE ambulance_id = ?;
                    """,
                    (status, assigned_incident_id, now, ambulance_id),
                )
            return cursor.rowcount > 0
    finally:
        conn.close()


def assign_ambulance_to_incident(
    ambulance_id: str,
    incident_id: int,
    note: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """
    Atomic transaction: Assign an available ambulance to a pending incident.
    Guarantees:
      1. Ambulance is currently AVAILABLE.
      2. Incident exists and is currently PENDING.
      3. Ambulance status changes to ASSIGNED with assigned_incident_id set.
      4. Incident status changes to DISPATCHED.
      5. Dispatch event is recorded.
    Fails atomically and raises an error if conditions are violated.
    """
    now = _get_utc_now()
    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Verify Ambulance exists and is AVAILABLE
            amb_cursor = conn.execute(
                "SELECT status, assigned_incident_id FROM ambulances WHERE ambulance_id = ?;",
                (ambulance_id,),
            )
            amb_row = amb_cursor.fetchone()
            if not amb_row:
                raise AmbulanceNotFoundError(f"Ambulance {ambulance_id} not found.")
            if amb_row["status"] != AmbulanceStatus.AVAILABLE.value:
                raise AmbulanceNotAvailableError(
                    f"Ambulance {ambulance_id} is not AVAILABLE (current status: {amb_row['status']})."
                )

            # 2. Verify Incident exists and is PENDING
            inc_cursor = conn.execute(
                "SELECT status FROM incidents WHERE incident_id = ?;",
                (incident_id,),
            )
            inc_row = inc_cursor.fetchone()
            if not inc_row:
                raise IncidentNotFoundError(f"Incident {incident_id} not found.")
            if inc_row["status"] != IncidentStatus.PENDING.value:
                raise DatabaseError(
                    f"Incident {incident_id} is not PENDING (current status: {inc_row['status']})."
                )

            # 3. Update Ambulance
            conn.execute(
                """
                UPDATE ambulances
                SET status = ?, assigned_incident_id = ?, updated_at = ?
                WHERE ambulance_id = ?;
                """,
                (AmbulanceStatus.ASSIGNED.value, incident_id, now, ambulance_id),
            )

            # 4. Update Incident
            conn.execute(
                """
                UPDATE incidents
                SET status = ?, updated_at = ?
                WHERE incident_id = ?;
                """,
                (IncidentStatus.DISPATCHED.value, now, incident_id),
            )

            # 5. Record Dispatch Event
            conn.execute(
                """
                INSERT INTO dispatch_events (
                    incident_id, ambulance_id, event_type, event_time, note
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (
                    incident_id,
                    ambulance_id,
                    EVENT_TYPE_AMBULANCE_DISPATCHED,
                    now,
                    note or f"Ambulance {ambulance_id} dispatched to incident {incident_id}",
                ),
            )
        return True
    except sqlite3.Error as e:
        raise DatabaseError(f"Transaction failed during ambulance assignment: {e}") from e
    finally:
        conn.close()


def record_event(
    incident_id: int,
    event_type: str,
    ambulance_id: Optional[str] = None,
    note: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Record an audit trail event for an incident."""
    now = _get_utc_now()
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO dispatch_events (
                    incident_id, ambulance_id, event_type, event_time, note
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (incident_id, ambulance_id, event_type, now, note),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise DatabaseError(f"Foreign key violation or integrity error: {e}") from e
    finally:
        conn.close()


def list_events_for_incident(
    incident_id: int,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all chronological audit events for a given incident."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT * FROM dispatch_events
            WHERE incident_id = ?
            ORDER BY event_time ASC, event_id ASC;
            """,
            (incident_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
