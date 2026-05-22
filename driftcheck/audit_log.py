"""Audit log for persisting drift check run history."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import List, Optional

DEFAULT_LOG_PATH = "drift_audit.log"


@dataclass
class AuditEntry:
    run_at: str
    drifted: bool
    drift_count: int
    resources_checked: int
    error: Optional[str] = None

    @classmethod
    def from_report(cls, report, error: Optional[str] = None) -> "AuditEntry":
        return cls(
            run_at=datetime.utcnow().isoformat(),
            drifted=report.drifted > 0,
            drift_count=report.drift_count,
            resources_checked=report.total,
            error=error,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(**data)


def append_entry(entry: AuditEntry, path: str = DEFAULT_LOG_PATH) -> None:
    """Append a single audit entry as a JSON line."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")


def load_entries(path: str = DEFAULT_LOG_PATH) -> List[AuditEntry]:
    """Load all audit entries from a log file."""
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries


def summarise_log(path: str = DEFAULT_LOG_PATH) -> dict:
    """Return aggregate statistics from the audit log."""
    entries = load_entries(path)
    if not entries:
        return {"total_runs": 0, "total_drifted": 0, "total_clean": 0, "total_errors": 0}
    total_drifted = sum(1 for e in entries if e.drifted)
    total_errors = sum(1 for e in entries if e.error)
    return {
        "total_runs": len(entries),
        "total_drifted": total_drifted,
        "total_clean": len(entries) - total_drifted - total_errors,
        "total_errors": total_errors,
    }
