"""Tests for driftcheck.comparator."""

import pytest

from driftcheck.comparator import DriftResult, compare, compare_all
from driftcheck.fetcher import LiveResource
from driftcheck.parser import PlannedResource


@pytest.fixture
def planned_bucket() -> PlannedResource:
    return PlannedResource(
        resource_type="aws_s3_bucket",
        resource_id="my-bucket",
        module=None,
        attributes={"bucket": "my-bucket", "versioning": "Enabled"},
    )


@pytest.fixture
def live_bucket_ok() -> LiveResource:
    return LiveResource(
        resource_type="aws_s3_bucket",
        resource_id="my-bucket",
        attributes={"bucket": "my-bucket", "versioning": "Enabled", "region": "us-east-1"},
    )


@pytest.fixture
def live_bucket_drifted() -> LiveResource:
    return LiveResource(
        resource_type="aws_s3_bucket",
        resource_id="my-bucket",
        attributes={"bucket": "my-bucket", "versioning": "Disabled"},
    )


def test_compare_no_drift(planned_bucket, live_bucket_ok):
    result = compare(planned_bucket, live_bucket_ok)
    assert isinstance(result, DriftResult)
    assert result.drifted is False
    assert result.differences == []


def test_compare_with_drift(planned_bucket, live_bucket_drifted):
    result = compare(planned_bucket, live_bucket_drifted)
    assert result.drifted is True
    assert len(result.differences) == 1
    diff = result.differences[0]
    assert diff["attribute"] == "versioning"
    assert diff["planned"] == "Enabled"
    assert diff["live"] == "Disabled"


def test_compare_ignores_extra_live_attributes(planned_bucket, live_bucket_ok):
    """Extra attributes present only in live state should not cause drift."""
    result = compare(planned_bucket, live_bucket_ok)
    assert result.drifted is False


def test_compare_all_missing_live_resource(planned_bucket):
    results = compare_all([planned_bucket], [])
    assert len(results) == 1
    assert results[0].drifted is True
    assert results[0].differences[0]["attribute"] == "*"


def test_compare_all_mixed(planned_bucket, live_bucket_ok):
    extra_planned = PlannedResource(
        resource_type="aws_s3_bucket",
        resource_id="missing-bucket",
        module=None,
        attributes={"bucket": "missing-bucket"},
    )
    results = compare_all([planned_bucket, extra_planned], [live_bucket_ok])
    assert len(results) == 2
    ok_result = next(r for r in results if r.resource_id == "my-bucket")
    missing_result = next(r for r in results if r.resource_id == "missing-bucket")
    assert ok_result.drifted is False
    assert missing_result.drifted is True


def test_drift_result_repr(planned_bucket, live_bucket_drifted):
    result = compare(planned_bucket, live_bucket_drifted)
    assert "DRIFTED" in repr(result)
