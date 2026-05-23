"""Tests for driftcheck.snapshot."""

import json
import time
from pathlib import Path

import pytest

from driftcheck.fetcher import LiveResource
from driftcheck.snapshot import (
    ResourceSnapshot,
    SnapshotDelta,
    compare_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture
def base_snapshot():
    return ResourceSnapshot(
        resource_id="bucket-1",
        resource_type="aws_s3_bucket",
        attributes={"region": "us-east-1", "versioning": True, "acl": "private"},
        captured_at=1000.0,
    )


@pytest.fixture
def updated_snapshot():
    return ResourceSnapshot(
        resource_id="bucket-1",
        resource_type="aws_s3_bucket",
        attributes={"region": "us-east-1", "versioning": False, "logging": True},
        captured_at=2000.0,
    )


def test_from_live_resource():
    live = LiveResource(
        resource_id="i-123",
        resource_type="aws_instance",
        attributes={"instance_type": "t3.micro"},
    )
    snap = ResourceSnapshot.from_live(live)
    assert snap.resource_id == "i-123"
    assert snap.resource_type == "aws_instance"
    assert snap.attributes["instance_type"] == "t3.micro"
    assert snap.captured_at > 0


def test_snapshot_round_trip(base_snapshot):
    data = base_snapshot.to_dict()
    restored = ResourceSnapshot.from_dict(data)
    assert restored.resource_id == base_snapshot.resource_id
    assert restored.attributes == base_snapshot.attributes
    assert restored.captured_at == base_snapshot.captured_at


def test_compare_snapshots_detects_changes(base_snapshot, updated_snapshot):
    delta = compare_snapshots(base_snapshot, updated_snapshot)
    assert delta.has_changes
    assert "versioning" in delta.changed
    assert delta.changed["versioning"]["old"] is True
    assert delta.changed["versioning"]["new"] is False


def test_compare_snapshots_detects_added(base_snapshot, updated_snapshot):
    delta = compare_snapshots(base_snapshot, updated_snapshot)
    assert "logging" in delta.added


def test_compare_snapshots_detects_removed(base_snapshot, updated_snapshot):
    delta = compare_snapshots(base_snapshot, updated_snapshot)
    assert "acl" in delta.removed


def test_compare_snapshots_no_changes(base_snapshot):
    delta = compare_snapshots(base_snapshot, base_snapshot)
    assert not delta.has_changes


def test_save_and_load_snapshot(tmp_path, base_snapshot, updated_snapshot):
    out = tmp_path / "snaps" / "state.json"
    save_snapshot([base_snapshot, updated_snapshot], out)
    assert out.exists()
    loaded = load_snapshot(out)
    assert len(loaded) == 2
    assert loaded[0].resource_id == base_snapshot.resource_id
    assert loaded[1].captured_at == updated_snapshot.captured_at


def test_load_snapshot_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "missing.json")
