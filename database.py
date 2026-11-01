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

from .config import DEFAULT_DB_PATH
from .constants import (
    AmbulanceStatus,
    IncidentStatus,
    TriageLevel,
    EVENT_TYPE_INCIDENT_CREATED,
)

EVENT_TYPE_AMBULANCE_DISPATCHED = "AMBULANCE_DISPATCHED"


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
