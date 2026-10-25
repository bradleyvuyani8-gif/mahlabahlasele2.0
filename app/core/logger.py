import json
import os
import threading
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
_log_lock = threading.Lock()

def log_event(event_type: str, payload: dict):
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "timestamp": timestamp,
        "event_type": str(event_type),
        "payload": payload,
    }
    log_path = LOG_DIR / "mahlabahlasele.log"
    with _log_lock:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

