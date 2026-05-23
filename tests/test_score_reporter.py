"""Tests for driftcheck.score_reporter."""

import pytest

from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.scorer import score_all, score_result
from driftcheck.score_reporter import format_scored, render_score_report


@pytest.fixture
def drifted_result():
    return DriftResult(
        resource_id="aws_s3_bucket.data",
        resource_type="aws_s3_bucket",
        drifted=True,
        diffs=[
            FieldDiff(field="acl", planned="private", actual="public-read"),
            FieldDiff(field="tags", planned="{}", actual="{'owner': 'team'}"),
        ],
    )


@pytest.fixture
def clean_result():
    return DriftResult(
        resource_id="aws_s3_bucket.logs",
        resource_type="aws_s3_bucket",
        drifted=False,
        diffs=[],
    )


def test_render_empty_report_no_colour():
    output = render_score_report([], use_colour=False)
    assert "No drift detected" in output


def test_render_report_contains_resource_id(drifted_result):
    scored = score_all([drifted_result])
    output = render_score_report(scored, use_colour=False)
    assert "aws_s3_bucket.data" in output


def test_render_report_contains_score(drifted_result):
    scored = score_all([drifted_result])
    output = render_score_report(scored, use_colour=False)
    assert "score=" in output


def test_render_report_contains_severity(drifted_result):
    scored = score_all([drifted_result])
    output = render_score_report(scored, use_colour=False)
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if level in output:
            break
    else:
        pytest.fail("No severity label found in report output")


def test_format_scored_no_colour(drifted_result):
    scored = score_result(drifted_result)
    text = format_scored(scored, use_colour=False)
    assert "aws_s3_bucket.data" in text
    assert "acl" in text or "tags" in text


def test_render_report_total_score(drifted_result):
    scored = score_all([drifted_result])
    output = render_score_report(scored, use_colour=False)
    assert "total score=" in output


def test_clean_result_excluded_from_score_all(clean_result):
    scored = score_all([clean_result])
    output = render_score_report(scored, use_colour=False)
    assert "No drift detected" in output
