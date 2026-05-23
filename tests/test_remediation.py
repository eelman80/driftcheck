"""Tests for driftcheck.remediation."""

import pytest

from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.remediation import (
    RemediationHint,
    batch_hints,
    build_hints,
)


@pytest.fixture
def clean_result():
    return DriftResult(
        resource_id="my-bucket",
        resource_type="aws_s3_bucket",
        drifted=False,
        diffs=[],
    )


@pytest.fixture
def drifted_s3():
    return DriftResult(
        resource_id="my-bucket",
        resource_type="aws_s3_bucket",
        drifted=True,
        diffs=[
            FieldDiff(field="tags", expected={"Env": "prod"}, actual={"Env": "dev"}),
            FieldDiff(field="versioning", expected="Enabled", actual="Suspended"),
        ],
    )


@pytest.fixture
def drifted_ec2():
    return DriftResult(
        resource_id="i-0abc123",
        resource_type="aws_instance",
        drifted=True,
        diffs=[
            FieldDiff(field="instance_type", expected="t3.medium", actual="t3.small"),
        ],
    )


@pytest.fixture
def unknown_type_result():
    return DriftResult(
        resource_id="some-rds",
        resource_type="aws_db_instance",
        drifted=True,
        diffs=[
            FieldDiff(field="engine_version", expected="14.3", actual="13.7"),
        ],
    )


def test_no_hints_for_clean_result(clean_result):
    assert build_hints(clean_result) == []


def test_hints_count_matches_diffs(drifted_s3):
    hints = build_hints(drifted_s3)
    assert len(hints) == 2


def test_hint_fields_populated(drifted_s3):
    hints = build_hints(drifted_s3)
    h = hints[0]
    assert h.resource_id == "my-bucket"
    assert h.resource_type == "aws_s3_bucket"
    assert h.field == "tags"
    assert h.expected == {"Env": "prod"}
    assert h.actual == {"Env": "dev"}


def test_s3_tags_has_terraform_snippet(drifted_s3):
    hints = build_hints(drifted_s3)
    tag_hint = next(h for h in hints if h.field == "tags")
    assert tag_hint.terraform_snippet is not None
    assert "aws_s3_bucket" in tag_hint.terraform_snippet
    assert "my-bucket" in tag_hint.terraform_snippet


def test_s3_tags_has_cli_command(drifted_s3):
    hints = build_hints(drifted_s3)
    tag_hint = next(h for h in hints if h.field == "tags")
    assert tag_hint.aws_cli_command is not None
    assert "put-bucket-tagging" in tag_hint.aws_cli_command


def test_ec2_instance_type_hint(drifted_ec2):
    hints = build_hints(drifted_ec2)
    assert len(hints) == 1
    h = hints[0]
    assert "modify-instance-attribute" in h.aws_cli_command
    assert "t3.medium" in h.aws_cli_command


def test_unknown_type_no_templates(unknown_type_result):
    hints = build_hints(unknown_type_result)
    assert len(hints) == 1
    h = hints[0]
    assert h.terraform_snippet is None
    assert h.aws_cli_command is None


def test_to_dict_keys(drifted_ec2):
    hints = build_hints(drifted_ec2)
    d = hints[0].to_dict()
    assert set(d.keys()) == {
        "resource_id", "resource_type", "field",
        "expected", "actual", "terraform_snippet", "aws_cli_command",
    }


def test_batch_hints_aggregates(drifted_s3, drifted_ec2, clean_result):
    all_hints = batch_hints([drifted_s3, drifted_ec2, clean_result])
    assert len(all_hints) == 3  # 2 from s3, 1 from ec2, 0 from clean
