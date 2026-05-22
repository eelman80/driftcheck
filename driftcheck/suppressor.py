"""Suppression rules: allow known/expected drift to be silenced."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import json
import os

from driftcheck.comparator import DriftResult


@dataclass
class SuppressionRule:
    """A rule that silences drift for a specific resource and/or field."""
    resource_id: str
    field: Optional[str] = None  # None means suppress all drift for the resource
    reason: str = ""

    def matches(self, result: DriftResult, diff_field: Optional[str] = None) -> bool:
        if result.resource_id != self.resource_id:
            return False
        if self.field is None:
            return True
        return self.field == diff_field

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "field": self.field,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SuppressionRule":
        return cls(
            resource_id=data["resource_id"],
            field=data.get("field"),
            reason=data.get("reason", ""),
        )


@dataclass
class SuppressionList:
    rules: List[SuppressionRule] = field(default_factory=list)

    def is_suppressed(self, result: DriftResult, diff_field: Optional[str] = None) -> bool:
        return any(r.matches(result, diff_field) for r in self.rules)

    def apply(self, results: List[DriftResult]) -> List[DriftResult]:
        """Return a new list of DriftResults with suppressed diffs removed."""
        filtered = []
        for result in results:
            if not result.drifted:
                filtered.append(result)
                continue
            remaining_diffs = [
                d for d in result.diffs
                if not self.is_suppressed(result, d.field)
            ]
            if remaining_diffs:
                from driftcheck.comparator import DriftResult as DR
                filtered.append(DR(
                    resource_id=result.resource_id,
                    resource_type=result.resource_type,
                    diffs=remaining_diffs,
                ))
        return filtered


def load_suppressions(path: str) -> SuppressionList:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Suppression file not found: {path}")
    with open(path) as f:
        data = json.load(f)
    rules = [SuppressionRule.from_dict(r) for r in data.get("suppressions", [])]
    return SuppressionList(rules=rules)


def save_suppressions(suppression_list: SuppressionList, path: str) -> None:
    data = {"suppressions": [r.to_dict() for r in suppression_list.rules]}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
