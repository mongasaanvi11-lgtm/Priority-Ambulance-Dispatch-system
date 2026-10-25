"""Central configuration for the ResQTrack educational prototype.

These coordinates are only a reference point for the fictional demo city;
they are not live ambulance or patient locations.
"""

import os
from pathlib import Path

# Project root is the parent of the ambulance_dispatch package directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Create the local data directory if it does not exist yet.
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Allow a deployment environment variable to override the default SQLite path.
DEFAULT_DB_PATH = os.environ.get(
    "RESQTRACK_DB_PATH",
    str(DATA_DIR / "dispatch.db"),
)

# Fictional demonstration city settings. Keep consistent with seed_data.py.
DEMO_CITY_NAME = "Metro City"
DEMO_CENTER_LAT = 28.6139
DEMO_CENTER_LNG = 77.2090
