"""Tests for driftcheck.drift_filter."""

import pytest

from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.drift_filter import FilterCriteria, apply_filter, filter_summary


@pytest.fixture
def clean_result():
    return DriftResult(
        resource_id="bucket-clean",
        resource_type="aws_s3_bucket",
        diffs=[],
    )


@pytest.fixture
def drifted_s3():
    return DriftResult(
        resource_id="bucket-drifted",
        resource_type="aws_s3_bucket",
        diffs=[FieldDiff(field="tags", planned="prod", live="staging")],
    )


@pytest.fixture
def drifted_ec2():
    return DriftResult(
        resource_id="instance-1",
        resource_type="aws_instance",
        diffs=[FieldDiff(field="instance_type", planned="t3.micro", live="t3.small")],
    )


def test_empty_criteria_returns_all(clean_result, drifted_s3, drifted_ec2):
    results = [clean_result, drifted_s3, drifted_ec2]
    out = apply_filter(results, FilterCriteria())
    assert out == results


def test_only_drifted_excludes_clean(clean_result, drifted_s3):
    results = [clean_result, drifted_s3]
    out = apply_filter(results, FilterCriteria(only_drifted=True))
    assert clean_result not in out
    assert drifted_s3 in out


def test_filter_by_resource_type(drifted_s3, drifted_ec2):
    results = [drifted_s3, drifted_ec2]
    out = apply_filter(results, FilterCriteria(resource_types=["aws_s3_bucket"]))
    assert out == [drifted_s3]


def test_filter_by_field_name(drifted_s3, drifted_ec2):
    results = [drifted_s3, drifted_ec2]
    out = apply_filter(results, FilterCriteria(field_names=["instance_type"]))
    assert out == [drifted_ec2]


def test_filter_by_field_name_no_match(drifted_s3):
    out = apply_filter([drifted_s3], FilterCriteria(field_names=["nonexistent_field"]))
    assert out == []


def test_filter_by_min_score_excludes_clean(clean_result, drifted_s3):
    results = [clean_result, drifted_s3]
    out = apply_filter(results, FilterCriteria(min_score=1.0))
    assert clean_result not in out


def test_filter_combined_type_and_only_drifted(clean_result, drifted_s3, drifted_ec2):
    results = [clean_result, drifted_s3, drifted_ec2]
    criteria = FilterCriteria(
        resource_types=["aws_s3_bucket"],
        only_drifted=True,
    )
    out = apply_filter(results, criteria)
    assert out == [drifted_s3]


def test_filter_summary_correct_counts(clean_result, drifted_s3):
    original = [clean_result, drifted_s3]
    filtered = [drifted_s3]
    summary = filter_summary(original, filtered)
    assert "1 of 2" in summary
    assert "1 remaining" in summary


def test_filter_summary_no_removal(drifted_s3):
    summary = filter_summary([drifted_s3], [drifted_s3])
    assert "0 of 1" in summary
