"""
AmbuPriority — Background area scanner for hospital insurance panels
====================================================================
Runs in a worker thread, in strict priority order:

    Phase 1  the ~30 hospitals around the exact searched location
             (these are the rows the page renders, ~3-5 s)
    Phase 2  the rest of the surrounding city, discovered by sweeping a grid
             (background; the user is already served by Phase 1)

Cancellation
------------
Only one scan matters at a time. Starting a new scan flips the cancel flag of
the previous one; the old worker stops at the next checkpoint and never writes
over newer work.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from src.hospital_discovery import discover_nearby_hospitals
from src.gemini_panel_researcher import research_many, get_cached_research_or_none

logger = logging.getLogger(__name__)

_lock = threading.Lock()
# Tracks which job is currently allowed to run.
_current: Dict[str, Any] = {"job_id": None, "cancel": False}
_jobs: Dict[str, Dict[str, Any]] = {}

MAX_JOBS_KEPT = 30


def _grid_points(lat: float, lon: float, span_deg: float = 0.16,
                 step_deg: float = 0.08) -> List[tuple]:
    """Coarse grid around the location, used to enumerate a city's hospitals."""
    n = max(1, int(span_deg / step_deg))
    return [
        (round(lat + i * step_deg, 4), round(lon + j * step_deg, 4))
        for i in range(-n, n + 1)
        for j in range(-n, n + 1)
    ]


def start_scan(job_id: str, lat: float, lon: float, label: str = "",
               radius_km: float = 5.0) -> Dict[str, Any]:
    """Start a scan, cancelling whatever was running before it."""
    with _lock:
        if _current.get("job_id") and _current["job_id"] != job_id:
            _current["cancel"] = True          # ask the previous worker to stop
        _current.update({"job_id": job_id, "cancel": False})
        _jobs[job_id] = {
            "job_id": job_id,
            "label": label,
            "lat": lat,
            "lon": lon,
            "status": "queued",
            "phase": 0,
            "found": 0,
            "researched": 0,
            "started": time.time(),
            "finished": None,
            "error": None,
        }
        # Keep the registry small.
        if len(_jobs) > MAX_JOBS_KEPT:
            for old in sorted(_jobs, key=lambda k: _jobs[k]["started"])[:len(_jobs) - MAX_JOBS_KEPT]:
                _jobs.pop(old, None)

    threading.Thread(target=_run, args=(job_id, lat, lon, radius_km), daemon=True).start()
    return dict(_jobs[job_id])


def cancel_scan(job_id: Optional[str] = None) -> bool:
    """Cancel the given job (or whatever is running)."""
    with _lock:
        if job_id and _current.get("job_id") not in (job_id, None):
            return False
        _current["cancel"] = True
        return True


def scan_status(job_id: str) -> Optional[Dict[str, Any]]:
    job = _jobs.get(job_id)
    return dict(job) if job else None


def active_scan() -> Optional[Dict[str, Any]]:
    with _lock:
        jid = _current.get("job_id")
    return scan_status(jid) if jid else None


def _cancelled(job_id: str) -> bool:
    with _lock:
        return bool(_current.get("cancel")) or _current.get("job_id") != job_id


def _finish(job_id: str, status: str) -> None:
    job = _jobs.get(job_id)
    if job:
        job["status"] = status
        job["finished"] = time.time()
        logger.info("Panel scan %s -> %s (found=%d researched=%d)",
                    job_id, status, job["found"], job["researched"])


def _run(job_id: str, lat: float, lon: float, radius_km: float) -> None:
    job = _jobs[job_id]
    try:
        # ── Phase 1: exactly the hospitals this page will render ──────────────
        job["status"] = "phase1"
        job["phase"] = 1
        nearby = discover_nearby_hospitals(lat, lon, radius_km) or []
        names = [h["name"] for h in nearby if h.get("name")]
        job["found"] = len(names)
        if _cancelled(job_id):
            return _finish(job_id, "cancelled")

        resolved = research_many(names)
        job["researched"] = len(resolved)
        if _cancelled(job_id):
            return _finish(job_id, "cancelled")

        # ── Phase 2: everything else in the surrounding city ─────────────────
        job["status"] = "phase2"
        job["phase"] = 2
        seen = {n.strip().lower() for n in names}

        for glat, glon in _grid_points(lat, lon):
            if _cancelled(job_id):
                return _finish(job_id, "cancelled")
            try:
                found = discover_nearby_hospitals(glat, glon, 6.0) or []
            except Exception:
                continue

            fresh = []
            for h in found:
                name = (h.get("name") or "").strip()
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    fresh.append(name)

            if not fresh:
                continue

            job["found"] = len(seen)
            research_many(fresh)
            job["researched"] = sum(1 for n in seen if get_cached_research_or_none(n))

        _finish(job_id, "done")
    except Exception as exc:                      # never let the thread die loudly
        job["error"] = str(exc)
        logger.warning("Panel scan %s failed: %s", job_id, exc)
        _finish(job_id, "error")
