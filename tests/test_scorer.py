"""Tests for driftcheck.scorer."""

import pytest

from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.scorer import (
    ScoredResult,
    _severity_label,
    score_result,
    score_all,
)


@pytest.fixture
def clean_result():
    return DriftResult(resource_id="aws_s3_bucket.logs", resource_type="aws_s3_bucket", drifted=False, diffs=[])


@pytest.fixture
def low_drift_result():
    return DriftResult(
        resource_id="aws_s3_bucket.app",
        resource_type="aws_s3_bucket",
        drifted=True,
        diffs=[FieldDiff(field="tags", planned="{'env': 'prod'}", actual="{'env': 'staging'}")],
    )


@pytest.fixture
def high_drift_result():
    return DriftResult(
        resource_id="aws_s3_bucket.sensitive",
        resource_type="aws_s3_bucket",
        drifted=True,
        diffs=[
            FieldDiff(field="acl", planned="private", actual="public-read"),
            FieldDiff(field="encryption", planned="AES256", actual="none"),
            FieldDiff(field="bucket_policy", planned="{}", actual="{...}"),
        ],
    )


def test_score_clean_result_is_zero(clean_result):
    scored = score_result(clean_result)
    assert scored.score == 0
    assert scored.severity == "none"
    assert scored.reasons == []


def test_score_low_drift(low_drift_result):
    scored = score_result(low_drift_result)
    assert scored.score > 0
    assert scored.severity == "low"
    assert any("tags" in r for r in scored.reasons)


def test_score_high_drift(high_drift_result):
    scored = score_result(high_drift_result)
    assert scored.score >= 40
    assert scored.severity in ("high", "critical")


def test_score_capped_at_100(high_drift_result):
    # Add many diffs to exceed 100
    extra_diffs = [FieldDiff(field=f"field_{i}", planned="a", actual="b") for i in range(20)]
    high_drift_result.diffs.extend(extra_diffs)
    scored = score_result(high_drift_result)
    assert scored.score <= 100


def test_score_all_excludes_clean(clean_result, low_drift_result, high_drift_result):
    results = [clean_result, low_drift_result, high_drift_result]
    scored = score_all(results)
    ids = [s.result.resource_id for s in scored]
    assert clean_result.resource_id not in ids
    assert len(scored) == 2


def test_score_all_sorted_descending(low_drift_result, high_drift_result):
    scored = score_all([low_drift_result, high_drift_result])
    assert scored[0].score >= scored[1].score


def test_severity_label_boundaries():
    assert _severity_label(0) == "low"
    assert _severity_label(19) == "low"
    assert _severity_label(20) == "medium"
    assert _severity_label(39) == "medium"
    assert _severity_label(40) == "high"
    assert _severity_label(69) == "high"
    assert _severity_label(70) == "critical"
    assert _severity_label(100) == "critical"


def test_scored_result_repr(low_drift_result):
    scored = score_result(low_drift_result)
    assert "ScoredResult" in repr(scored)
    assert "aws_s3_bucket.app" in repr(scored)
