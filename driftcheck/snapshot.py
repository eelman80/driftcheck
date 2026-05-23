"""Snapshot module: capture and compare live resource states over time."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from driftcheck.fetcher import LiveResource


@dataclass
class ResourceSnapshot:
    resource_id: str
    resource_type: str
    attributes: Dict
    captured_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ResourceSnapshot":
        return cls(
            resource_id=data["resource_id"],
            resource_type=data["resource_type"],
            attributes=data["attributes"],
            captured_at=data.get("captured_at", 0.0),
        )

    @classmethod
    def from_live(cls, resource: LiveResource) -> "ResourceSnapshot":
        return cls(
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            attributes=dict(resource.attributes),
        )


@dataclass
class SnapshotDelta:
    resource_id: str
    added: Dict = field(default_factory=dict)
    removed: Dict = field(default_factory=dict)
    changed: Dict = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def compare_snapshots(
    old: ResourceSnapshot, new: ResourceSnapshot
) -> SnapshotDelta:
    """Return a SnapshotDelta describing attribute changes between two snapshots."""
    delta = SnapshotDelta(resource_id=old.resource_id)
    old_keys = set(old.attributes)
    new_keys = set(new.attributes)

    for key in new_keys - old_keys:
        delta.added[key] = new.attributes[key]
    for key in old_keys - new_keys:
        delta.removed[key] = old.attributes[key]
    for key in old_keys & new_keys:
        if old.attributes[key] != new.attributes[key]:
            delta.changed[key] = {"old": old.attributes[key], "new": new.attributes[key]}

    return delta


def save_snapshot(snapshots: List[ResourceSnapshot], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump([s.to_dict() for s in snapshots], fh, indent=2)


def load_snapshot(path: Path) -> List[ResourceSnapshot]:
    with open(path) as fh:
        return [ResourceSnapshot.from_dict(d) for d in json.load(fh)]
