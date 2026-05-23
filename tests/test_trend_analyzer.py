"""Tests for driftcheck.trend_analyzer."""

import pytest
from driftcheck.audit_log import AuditEntry
from driftcheck.trend_analyzer import (
    analyze_trends,
    render_trend_report,
    ResourceTrend,
    TrendReport,
)


@pytest.fixture
def clean_entry():
    return AuditEntry(
        timestamp="2024-01-01T10:00:00",
        drifted=False,
        total=2,
        drift_count=0,
        diffs=[],
    )


@pytest.fixture
def drifted_entry_a():
    return AuditEntry(
        timestamp="2024-01-02T10:00:00",
        drifted=True,
        total=2,
        drift_count=1,
        diffs=[
            {"resource_id": "aws_s3_bucket.logs", "field": "versioning"},
        ],
    )


@pytest.fixture
def drifted_entry_b():
    return AuditEntry(
        timestamp="2024-01-03T10:00:00",
        drifted=True,
        total=2,
        drift_count=2,
        diffs=[
            {"resource_id": "aws_s3_bucket.logs", "field": "versioning"},
            {"resource_id": "aws_instance.web", "field": "instance_type"},
        ],
    )


def test_analyze_trends_totals(clean_entry, drifted_entry_a, drifted_entry_b):
    report = analyze_trends([clean_entry, drifted_entry_a, drifted_entry_b])
    assert report.total_runs == 3
    assert report.drifted_runs == 2
    assert report.clean_runs == 1


def test_drift_rate(clean_entry, drifted_entry_a):
    report = analyze_trends([clean_entry, drifted_entry_a])
    assert report.drift_rate == 0.5


def test_drift_rate_all_clean(clean_entry):
    report = analyze_trends([clean_entry, clean_entry])
    assert report.drift_rate == 0.0


def test_most_drifted_ordering(drifted_entry_a, drifted_entry_b):
    report = analyze_trends([drifted_entry_a, drifted_entry_b])
    assert report.most_drifted[0].resource_id == "aws_s3_bucket.logs"
    assert report.most_drifted[0].occurrences == 2


def test_drifted_fields_collected(drifted_entry_a, drifted_entry_b):
    report = analyze_trends([drifted_entry_a, drifted_entry_b])
    s3_trend = next(t for t in report.most_drifted if t.resource_id == "aws_s3_bucket.logs")
    assert "versioning" in s3_trend.drifted_fields


def test_top_n_limits_results(drifted_entry_a, drifted_entry_b):
    report = analyze_trends([drifted_entry_a, drifted_entry_b], top_n=1)
    assert len(report.most_drifted) == 1


def test_empty_entries():
    report = analyze_trends([])
    assert report.total_runs == 0
    assert report.drift_rate == 0.0
    assert report.most_drifted == []


def test_render_trend_report_contains_key_info(clean_entry, drifted_entry_a):
    report = analyze_trends([clean_entry, drifted_entry_a])
    text = render_trend_report(report)
    assert "Total runs" in text
    assert "Drift rate" in text
    assert "aws_s3_bucket.logs" in text


def test_render_trend_report_no_drift(clean_entry):
    report = analyze_trends([clean_entry])
    text = render_trend_report(report)
    assert "(none)" in text
