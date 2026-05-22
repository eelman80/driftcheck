"""Tests for driftcheck.scheduler."""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from driftcheck.scheduler import DriftScheduler, ScheduleConfig, RunRecord
from driftcheck.reporter import DriftReport
from driftcheck.comparator import DriftResult


@pytest.fixture
def clean_report():
    result = DriftResult(resource_id="bucket-1", resource_type="aws_s3_bucket", diffs=[])
    return DriftReport([result])


@pytest.fixture
def drifted_report():
    from driftcheck.comparator import FieldDiff
    diff = FieldDiff(field="acl", planned="private", live="public-read")
    result = DriftResult(resource_id="bucket-1", resource_type="aws_s3_bucket", diffs=[diff])
    return DriftReport([result])


def test_run_once_clean(clean_report):
    check_fn = MagicMock(return_value=clean_report)
    scheduler = DriftScheduler(check_fn, ScheduleConfig())
    record = scheduler.run_once()
    assert not record.drifted
    assert record.drift_count == 0
    assert record.error is None


def test_run_once_drifted(drifted_report):
    check_fn = MagicMock(return_value=drifted_report)
    scheduler = DriftScheduler(check_fn, ScheduleConfig())
    record = scheduler.run_once()
    assert record.drifted
    assert record.drift_count == 1


def test_run_once_records_history(clean_report):
    check_fn = MagicMock(return_value=clean_report)
    scheduler = DriftScheduler(check_fn, ScheduleConfig())
    scheduler.run_once()
    scheduler.run_once()
    assert len(scheduler.history) == 2


def test_on_drift_callback_called(drifted_report):
    on_drift = MagicMock()
    check_fn = MagicMock(return_value=drifted_report)
    config = ScheduleConfig(on_drift=on_drift)
    scheduler = DriftScheduler(check_fn, config)
    scheduler.run_once()
    on_drift.assert_called_once()


def test_on_clean_callback_called(clean_report):
    on_clean = MagicMock()
    check_fn = MagicMock(return_value=clean_report)
    config = ScheduleConfig(on_clean=on_clean)
    scheduler = DriftScheduler(check_fn, config)
    scheduler.run_once()
    on_clean.assert_called_once()


def test_on_error_callback_called():
    on_error = MagicMock()
    check_fn = MagicMock(side_effect=RuntimeError("boom"))
    config = ScheduleConfig(on_error=on_error)
    scheduler = DriftScheduler(check_fn, config)
    record = scheduler.run_once()
    assert record.error == "boom"
    on_error.assert_called_once()


def test_max_runs_respected(clean_report):
    check_fn = MagicMock(return_value=clean_report)
    config = ScheduleConfig(interval_seconds=0, max_runs=3)
    scheduler = DriftScheduler(check_fn, config)
    scheduler.start()
    assert len(scheduler.history) == 3


def test_next_run_at_no_history():
    scheduler = DriftScheduler(MagicMock(), ScheduleConfig(interval_seconds=60))
    assert scheduler.next_run_at() is not None


def test_next_run_at_after_run(clean_report):
    check_fn = MagicMock(return_value=clean_report)
    config = ScheduleConfig(interval_seconds=300)
    scheduler = DriftScheduler(check_fn, config)
    scheduler.run_once()
    delta = (scheduler.next_run_at() - scheduler.history[-1].run_at).seconds
    assert delta == 300


def test_run_record_repr():
    record = RunRecord(run_at=datetime(2024, 1, 1), drifted=True, drift_count=2)
    assert "DRIFTED" in repr(record)
    assert "2" in repr(record)
