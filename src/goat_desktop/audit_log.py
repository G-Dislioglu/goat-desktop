from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    status: str
    payload: dict[str, Any]
    timestamp: float

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


def get_audit_log_path() -> Path:
    explicit = os.environ.get("GOAT_AUDIT_LOG_PATH")
    if explicit:
        return Path(explicit)
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "GoatDesktop" / "audit.jsonl"
    return Path.home() / "AppData" / "Roaming" / "GoatDesktop" / "audit.jsonl"


def append_audit_event(event_type: str, status: str, payload: dict[str, Any]) -> AuditEvent:
    event = AuditEvent(event_type=event_type, status=status, payload=payload, timestamp=time.time())
    path = get_audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event.to_json_line() + "\n")
    return event


def read_audit_events(path: Path | None = None) -> list[dict[str, Any]]:
    audit_path = path or get_audit_log_path()
    if not audit_path.exists():
        return []
    return [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
