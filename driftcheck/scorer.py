"""Drift severity scoring module.

Assigns a numeric severity score to drift results based on
resource type, number of drifted fields, and field sensitivity.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from driftcheck.comparator import DriftResult

# Fields considered high-sensitivity (score multiplier applied)
_SENSITIVE_FIELDS: Dict[str, float] = {
    "bucket_policy": 2.0,
    "acl": 2.0,
    "iam_instance_profile": 2.0,
    "security_groups": 1.8,
    "encryption": 1.8,
    "kms_key_id": 1.8,
    "public_access_block": 1.6,
    "tags": 0.5,
}

_BASE_SCORE_PER_FIELD = 10
_MAX_SCORE = 100


@dataclass
class ScoredResult:
    result: DriftResult
    score: int
    severity: str
    reasons: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"ScoredResult(resource={self.result.resource_id}, score={self.score}, severity={self.severity})"


def _severity_label(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def score_result(result: DriftResult) -> ScoredResult:
    """Score a single DriftResult and return a ScoredResult."""
    if not result.drifted:
        return ScoredResult(result=result, score=0, severity="none", reasons=[])

    reasons: List[str] = []
    raw = 0.0

    for diff in result.diffs:
        multiplier = _SENSITIVE_FIELDS.get(diff.field, 1.0)
        field_score = _BASE_SCORE_PER_FIELD * multiplier
        raw += field_score
        if multiplier > 1.0:
            reasons.append(f"{diff.field} is a sensitive field (x{multiplier})")
        else:
            reasons.append(f"{diff.field} drifted")

    score = min(int(raw), _MAX_SCORE)
    return ScoredResult(
        result=result,
        score=score,
        severity=_severity_label(score),
        reasons=reasons,
    )


def score_all(results: List[DriftResult]) -> List[ScoredResult]:
    """Score a list of DriftResults, returning only drifted ones sorted by score desc."""
    scored = [score_result(r) for r in results if r.drifted]
    return sorted(scored, key=lambda s: s.score, reverse=True)
