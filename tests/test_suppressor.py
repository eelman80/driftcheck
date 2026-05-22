"""Tests for driftcheck.suppressor."""

import json
import pytest

from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.suppressor import (
    SuppressionRule,
    SuppressionList,
    load_suppressions,
    save_suppressions,
)


@pytest.fixture
def drifted_result():
    return DriftResult(
        resource_id="aws_s3_bucket.my_bucket",
        resource_type="aws_s3_bucket",
        diffs=[
            FieldDiff(field="tags", planned="prod", actual="staging"),
            FieldDiff(field="acl", planned="private", actual="public-read"),
        ],
    )


@pytest.fixture
def clean_result():
    return DriftResult(
        resource_id="aws_s3_bucket.clean",
        resource_type="aws_s3_bucket",
        diffs=[],
    )


def test_rule_matches_resource_and_field(drifted_result):
    rule = SuppressionRule(resource_id="aws_s3_bucket.my_bucket", field="tags")
    assert rule.matches(drifted_result, diff_field="tags") is True


def test_rule_does_not_match_wrong_field(drifted_result):
    rule = SuppressionRule(resource_id="aws_s3_bucket.my_bucket", field="tags")
    assert rule.matches(drifted_result, diff_field="acl") is False


def test_rule_matches_all_fields_when_field_none(drifted_result):
    rule = SuppressionRule(resource_id="aws_s3_bucket.my_bucket")
    assert rule.matches(drifted_result, diff_field="acl") is True
    assert rule.matches(drifted_result, diff_field="tags") is True


def test_rule_does_not_match_wrong_resource(drifted_result):
    rule = SuppressionRule(resource_id="aws_s3_bucket.other")
    assert rule.matches(drifted_result, diff_field="tags") is False


def test_suppression_list_removes_suppressed_field(drifted_result):
    rules = [SuppressionRule(resource_id="aws_s3_bucket.my_bucket", field="tags", reason="known")]
    sl = SuppressionList(rules=rules)
    results = sl.apply([drifted_result])
    assert len(results) == 1
    assert len(results[0].diffs) == 1
    assert results[0].diffs[0].field == "acl"


def test_suppression_list_removes_entire_resource(drifted_result):
    rules = [SuppressionRule(resource_id="aws_s3_bucket.my_bucket")]
    sl = SuppressionList(rules=rules)
    results = sl.apply([drifted_result])
    assert results == []


def test_suppression_list_preserves_clean_result(clean_result):
    rules = [SuppressionRule(resource_id="aws_s3_bucket.clean")]
    sl = SuppressionList(rules=rules)
    results = sl.apply([clean_result])
    assert len(results) == 1


def test_save_and_load_suppressions(tmp_path):
    path = str(tmp_path / "suppressions.json")
    sl = SuppressionList(rules=[
        SuppressionRule(resource_id="aws_s3_bucket.x", field="tags", reason="ignore tags"),
        SuppressionRule(resource_id="aws_ec2_instance.y"),
    ])
    save_suppressions(sl, path)
    loaded = load_suppressions(path)
    assert len(loaded.rules) == 2
    assert loaded.rules[0].resource_id == "aws_s3_bucket.x"
    assert loaded.rules[0].field == "tags"
    assert loaded.rules[1].field is None


def test_load_suppressions_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_suppressions("/nonexistent/path/suppressions.json")
