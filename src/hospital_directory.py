import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import DIRECTORY_DATA_FILE

# Default verified emergency directory entries
DEFAULT_DIRECTORY: List[Dict[str, Any]] = [
    {
        "id": "em-1",
        "name": "National Emergency Services Helpline",
        "type": "Emergency",
        "phone": "112",
        "city": "All India / Unified Emergency",
        "address": "Toll-Free Emergency Dispatch",
        "verified": True
    },
    {
        "id": "em-2",
        "name": "National Ambulance Service",
        "type": "Ambulance",
        "phone": "108 / 102",
        "city": "All India",
        "address": "Government Emergency Medical Ambulance Services",
        "verified": True
    },
    {
        "id": "hosp-1",
        "name": "AIIMS Emergency & Trauma Centre",
        "type": "Hospital",
        "phone": "+91-11-26588500",
        "city": "New Delhi",
        "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi, Delhi 110029",
        "verified": True
    },
    {
        "id": "hosp-2",
        "name": "KEM Hospital Emergency Ward",
        "type": "Hospital",
        "phone": "+91-22-24107000",
        "city": "Mumbai",
        "address": "Acharya Donde Marg, Parel, Mumbai, Maharashtra 400012",
        "verified": True
    },
    {
        "id": "doc-1",
        "name": "On-Call Emergency Tele-Triage Helpline",
        "type": "Doctor / Telehealth",
        "phone": "1075 (National Health Toll-Free)",
        "city": "National",
        "address": "Ministry of Health & Family Welfare Helpline",
        "verified": True
    }
]

class HospitalDirectory:
    def __init__(self, file_path: Path = DIRECTORY_DATA_FILE):
        self.file_path = file_path
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except Exception:
                self.entries = list(DEFAULT_DIRECTORY)
                self.save()
        else:
            self.entries = list(DEFAULT_DIRECTORY)
            self.save()

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)

    def get_all(self) -> List[Dict[str, Any]]:
        return self.entries

    def add_entry(self, name: str, entry_type: str, phone: str, city: str, address: str) -> Dict[str, Any]:
        new_entry = {
            "id": f"dir-{len(self.entries) + 1}",
            "name": name.strip(),
            "type": entry_type.strip(),
            "phone": phone.strip(),
            "city": city.strip(),
            "address": address.strip(),
            "verified": True
        }
        self.entries.append(new_entry)
        self.save()
        return new_entry

    def delete_entry(self, entry_id: str) -> bool:
        initial_len = len(self.entries)
        self.entries = [e for e in self.entries if e.get("id") != entry_id]
        if len(self.entries) < initial_len:
            self.save()
            return True
        return False

    def search(self, query: str = "", filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        q = query.lower()
        results = []
        for e in self.entries:
            if filter_type and filter_type.lower() != "all" and e.get("type", "").lower() != filter_type.lower():
                continue
            if not q or (q in e.get("name", "").lower() or q in e.get("city", "").lower() or q in e.get("address", "").lower() or q in e.get("phone", "").lower()):
                results.append(e)
        return results

