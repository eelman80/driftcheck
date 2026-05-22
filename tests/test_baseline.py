"""Tests for driftcheck.baseline."""

import json
import os
import pytest

from driftcheck.baseline import (
    Baseline,
    create_baseline,
    load_baseline,
    save_baseline,
)
from driftcheck.comparator import DriftResult, FieldDiff
from driftcheck.fetcher import LiveResource


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def live_bucket():
    return LiveResource(
        resource_id="aws_s3_bucket.my_bucket",
        resource_type="aws_s3_bucket",
        attributes={"bucket": "my-bucket", "region": "us-east-1"},
    )


@pytest.fixture
def clean_result(live_bucket):
    return DriftResult(
        resource_id="aws_s3_bucket.my_bucket",
        drifted=False,
        diffs=[],
        live=live_bucket,
    )


@pytest.fixture
def drifted_result(live_bucket):
    return DriftResult(
        resource_id="aws_s3_bucket.my_bucket",
        drifted=True,
        diffs=[FieldDiff(field="region", planned="eu-west-1", actual="us-east-1")],
        live=live_bucket,
    )


# ---------------------------------------------------------------------------
# create_baseline
# ---------------------------------------------------------------------------

def test_create_baseline_resource_ids(clean_result):
    baseline = create_baseline([clean_result])
    assert "aws_s3_bucket.my_bucket" in baseline.resource_ids


def test_create_baseline_attributes_captured(clean_result):
    baseline = create_baseline([clean_result])
    attrs = baseline.attributes["aws_s3_bucket.my_bucket"]
    assert attrs["bucket"] == "my-bucket"


def test_create_baseline_description(clean_result):
    baseline = create_baseline([clean_result], description="post-deploy")
    assert baseline.description == "post-deploy"


def test_create_baseline_created_at_set(clean_result):
    baseline = create_baseline([clean_result])
    assert baseline.created_at  # non-empty ISO timestamp


def test_baseline_covers(clean_result):
    baseline = create_baseline([clean_result])
    assert baseline.covers("aws_s3_bucket.my_bucket")
    assert not baseline.covers("aws_instance.web")


# ---------------------------------------------------------------------------
# save_baseline / load_baseline
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path, clean_result):
    path = str(tmp_path / "baseline.json")
    baseline = create_baseline([clean_result], description="roundtrip")
    save_baseline(baseline, path)

    loaded = load_baseline(path)
    assert loaded.resource_ids == baseline.resource_ids
    assert loaded.attributes == baseline.attributes
    assert loaded.description == "roundtrip"


def test_load_baseline_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_baseline(str(tmp_path / "missing.json"))


def test_load_baseline_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not-json")
    with pytest.raises(ValueError, match="Invalid baseline JSON"):
        load_baseline(str(bad))


def test_load_baseline_missing_keys(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"created_at": "2024-01-01"}))
    with pytest.raises(ValueError, match="missing required keys"):
        load_baseline(str(bad))


def test_save_creates_parent_dirs(tmp_path, clean_result):
    path = str(tmp_path / "nested" / "dir" / "baseline.json")
    baseline = create_baseline([clean_result])
    save_baseline(baseline, path)
    assert os.path.exists(path)
