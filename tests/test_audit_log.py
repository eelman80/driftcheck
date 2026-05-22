"""Tests for driftcheck.audit_log."""

import json
import os
import pytest

from driftcheck.audit_log import AuditEntry, append_entry, load_entries, summarise_log
from driftcheck.reporter import DriftReport
from driftcheck.comparator import DriftResult, FieldDiff


@pytest.fixture
def log_path(tmp_path):
    return str(tmp_path / "test_audit.log")


@pytest.fixture
def clean_report():
    result = DriftResult(resource_id="i-123", resource_type="aws_instance", diffs=[])
    return DriftReport([result])


@pytest.fixture
def drifted_report():
    diff = FieldDiff(field="instance_type", planned="t3.micro", live="t3.large")
    result = DriftResult(resource_id="i-123", resource_type="aws_instance", diffs=[diff])
    return DriftReport([result])


def test_entry_from_clean_report(clean_report):
    entry = AuditEntry.from_report(clean_report)
    assert not entry.drifted
    assert entry.drift_count == 0
    assert entry.resources_checked == 1
    assert entry.error is None


def test_entry_from_drifted_report(drifted_report):
    entry = AuditEntry.from_report(drifted_report)
    assert entry.drifted
    assert entry.drift_count == 1


def test_entry_with_error(clean_report):
    entry = AuditEntry.from_report(clean_report, error="timeout")
    assert entry.error == "timeout"


def test_append_and_load(log_path, clean_report):
    entry = AuditEntry.from_report(clean_report)
    append_entry(entry, path=log_path)
    loaded = load_entries(path=log_path)
    assert len(loaded) == 1
    assert loaded[0].drift_count == 0


def test_append_multiple(log_path, clean_report, drifted_report):
    append_entry(AuditEntry.from_report(clean_report), path=log_path)
    append_entry(AuditEntry.from_report(drifted_report), path=log_path)
    loaded = load_entries(path=log_path)
    assert len(loaded) == 2


def test_load_missing_file(log_path):
    entries = load_entries(path=log_path + ".missing")
    assert entries == []


def test_summarise_log(log_path, clean_report, drifted_report):
    append_entry(AuditEntry.from_report(clean_report), path=log_path)
    append_entry(AuditEntry.from_report(drifted_report), path=log_path)
    summary = summarise_log(path=log_path)
    assert summary["total_runs"] == 2
    assert summary["total_drifted"] == 1
    assert summary["total_clean"] == 1
    assert summary["total_errors"] == 0


def test_summarise_empty_log(log_path):
    summary = summarise_log(path=log_path)
    assert summary["total_runs"] == 0


def test_entry_round_trip(clean_report):
    entry = AuditEntry.from_report(clean_report)
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.drift_count == entry.drift_count
    assert restored.run_at == entry.run_at
