"""Filter drift results by resource type, field name, or severity threshold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftcheck.comparator import DriftResult
from driftcheck.scorer import ScoredResult, score_result


@dataclass
class FilterCriteria:
    """Criteria used to filter drift results."""
    resource_types: List[str] = field(default_factory=list)
    field_names: List[str] = field(default_factory=list)
    min_score: Optional[float] = None
    only_drifted: bool = False

    def is_empty(self) -> bool:
        return (
            not self.resource_types
            and not self.field_names
            and self.min_score is None
            and not self.only_drifted
        )


def _matches_resource_type(result: DriftResult, types: List[str]) -> bool:
    if not types:
        return True
    return result.resource_type in types


def _matches_field_names(result: DriftResult, names: List[str]) -> bool:
    if not names:
        return True
    drifted_fields = {d.field for d in result.diffs}
    return bool(drifted_fields & set(names))


def _matches_min_score(result: DriftResult, min_score: Optional[float]) -> bool:
    if min_score is None:
        return True
    scored: ScoredResult = score_result(result)
    return scored.score >= min_score


def apply_filter(
    results: List[DriftResult],
    criteria: FilterCriteria,
) -> List[DriftResult]:
    """Return only the results that satisfy all filter criteria."""
    if criteria.is_empty():
        return list(results)

    filtered = []
    for result in results:
        if criteria.only_drifted and not result.drifted:
            continue
        if not _matches_resource_type(result, criteria.resource_types):
            continue
        if not _matches_field_names(result, criteria.field_names):
            continue
        if not _matches_min_score(result, criteria.min_score):
            continue
        filtered.append(result)
    return filtered


def filter_summary(original: List[DriftResult], filtered: List[DriftResult]) -> str:
    """Return a human-readable summary of how many results were filtered out."""
    removed = len(original) - len(filtered)
    return (
        f"Filtered {removed} of {len(original)} result(s); "
        f"{len(filtered)} remaining."
    )
