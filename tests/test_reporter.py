"""Tests for driftcheck.reporter module."""

import pytest

from driftcheck.comparator import DriftResult
from driftcheck.reporter import DriftReport, format_text, format_json


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def no_drift_result():
    return DriftResult(
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        diffs={},
    )


@pytest.fixture()
def drift_result():
    return DriftResult(
        resource_id="aws_s3_bucket.assets",
        resource_type="aws_s3_bucket",
        diffs={"versioning": (True, False), "tags.env": ("prod", "staging")},
    )


@pytest.fixture()
def mixed_report(no_drift_result, drift_result):
    return DriftReport(results=[no_drift_result, drift_result])


# ---------------------------------------------------------------------------
# DriftReport property tests
# ---------------------------------------------------------------------------

def test_report_totals(mixed_report):
    assert mixed_report.total == 2
    assert mixed_report.drift_count == 1
    assert len(mixed_report.clean) == 1


def test_report_empty():
    report = DriftReport(results=[])
    assert report.total == 0
    assert report.drift_count == 0
    assert report.clean == []


# ---------------------------------------------------------------------------
# format_text tests
# ---------------------------------------------------------------------------

def test_format_text_contains_header(mixed_report):
    output = format_text(mixed_report)
    assert "DriftCheck Report" in output
    assert "2 resource(s) evaluated" in output


def test_format_text_shows_drift_status(mixed_report):
    output = format_text(mixed_report)
    assert "[DRIFT]" in output
    assert "[OK]" in output


def test_format_text_shows_diff_fields(mixed_report):
    output = format_text(mixed_report)
    assert "versioning" in output
    assert "tags.env" in output


def test_format_text_empty_report():
    report = DriftReport(results=[])
    output = format_text(report)
    assert "No resources to report." in output


# ---------------------------------------------------------------------------
# format_json tests
# ---------------------------------------------------------------------------

def test_format_json_structure(mixed_report):
    data = format_json(mixed_report)
    assert "summary" in data
    assert "resources" in data
    assert data["summary"]["total"] == 2
    assert data["summary"]["drifted"] == 1


def test_format_json_resource_fields(drift_result):
    report = DriftReport(results=[drift_result])
    data = format_json(report)
    resource = data["resources"][0]
    assert resource["resource_id"] == "aws_s3_bucket.assets"
    assert resource["has_drift"] is True
    assert "versioning" in resource["diffs"]
    assert resource["diffs"]["versioning"] == {"planned": True, "live": False}
