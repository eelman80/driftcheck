"""Baseline management for drift detection.

Allows saving and loading a known-good infrastructure state so that
subsequent runs can compare against the baseline rather than the plan.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from driftcheck.comparator import DriftResult


@dataclass
class Baseline:
    """A saved snapshot of a drift-free infrastructure state."""

    created_at: str
    resource_ids: List[str]
    attributes: Dict[str, Dict[str, object]]
    description: Optional[str] = None

    def covers(self, resource_id: str) -> bool:
        """Return True if this baseline includes the given resource."""
        return resource_id in self.resource_ids


def create_baseline(
    results: List[DriftResult],
    description: Optional[str] = None,
) -> Baseline:
    """Build a Baseline from a list of clean DriftResults."""
    attributes: Dict[str, Dict[str, object]] = {}
    resource_ids: List[str] = []

    for result in results:
        rid = result.resource_id
        resource_ids.append(rid)
        if result.live:
            attributes[rid] = dict(result.live.attributes)

    return Baseline(
        created_at=datetime.now(timezone.utc).isoformat(),
        resource_ids=resource_ids,
        attributes=attributes,
        description=description,
    )


def save_baseline(baseline: Baseline, path: str) -> None:
    """Persist a baseline to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(baseline), fh, indent=2)


def load_baseline(path: str) -> Baseline:
    """Load a baseline from a JSON file.

    Raises:
        FileNotFoundError: if *path* does not exist.
        ValueError: if the file is not valid baseline JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline file not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid baseline JSON in {path}: {exc}") from exc

    required = {"created_at", "resource_ids", "attributes"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Baseline missing required keys: {missing}")

    return Baseline(
        created_at=data["created_at"],
        resource_ids=data["resource_ids"],
        attributes=data["attributes"],
        description=data.get("description"),
    )
