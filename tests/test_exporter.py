"""Tests for driftcheck.exporter."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile

import pytest

from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.reporter import DriftReport
from driftcheck.exporter import export_json, export_csv, export_to_file


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def clean_result():
    return DriftResult(resource_type="aws_s3_bucket", resource_id="my-bucket", diffs=[])


@pytest.fixture()
def drifted_result():
    return DriftResult(
        resource_type="aws_instance",
        resource_id="i-abc123",
        diffs=[
            FieldDiff(field="instance_type", planned="t3.micro", actual="t3.small"),
            FieldDiff(field="tags.Env", planned="prod", actual="staging"),
        ],
    )


@pytest.fixture()
def mixed_report(clean_result, drifted_result):
    return DriftReport(results=[clean_result, drifted_result])


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def test_export_json_structure(mixed_report):
    raw = export_json(mixed_report)
    data = json.loads(raw)
    assert "summary" in data
    assert data["summary"]["total"] == 2
    assert data["summary"]["drifted"] == 1
    assert len(data["results"]) == 2


def test_export_json_drifted_fields(mixed_report):
    data = json.loads(export_json(mixed_report))
    drifted = next(r for r in data["results"] if r["drifted"])
    assert len(drifted["diffs"]) == 2
    fields = {d["field"] for d in drifted["diffs"]}
    assert "instance_type" in fields


def test_export_json_empty_report():
    report = DriftReport(results=[])
    data = json.loads(export_json(report))
    assert data["summary"]["total"] == 0
    assert data["results"] == []


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def test_export_csv_headers(mixed_report):
    raw = export_csv(mixed_report)
    reader = csv.reader(io.StringIO(raw))
    headers = next(reader)
    assert headers == ["resource_type", "resource_id", "field", "planned", "actual"]


def test_export_csv_only_drifted_rows(mixed_report):
    raw = export_csv(mixed_report)
    reader = csv.reader(io.StringIO(raw))
    next(reader)  # skip headers
    rows = list(reader)
    # Only the drifted result has 2 diff fields
    assert len(rows) == 2
    assert all(row[0] == "aws_instance" for row in rows)


def test_export_csv_no_drift_rows(clean_result):
    report = DriftReport(results=[clean_result])
    raw = export_csv(report)
    reader = csv.reader(io.StringIO(raw))
    next(reader)
    assert list(reader) == []


# ---------------------------------------------------------------------------
# File export
# ---------------------------------------------------------------------------

def test_export_to_file_json(mixed_report):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name
    try:
        export_to_file(mixed_report, path, fmt="json")
        with open(path) as fh:
            data = json.load(fh)
        assert data["summary"]["total"] == 2
    finally:
        os.unlink(path)


def test_export_to_file_csv(mixed_report):
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        path = tmp.name
    try:
        export_to_file(mixed_report, path, fmt="csv")
        with open(path) as fh:
            content = fh.read()
        assert "instance_type" in content
    finally:
        os.unlink(path)


def test_export_to_file_invalid_format(mixed_report):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_to_file(mixed_report, "/tmp/out.txt", fmt="xml")
