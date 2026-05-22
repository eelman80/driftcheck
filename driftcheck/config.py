"""Configuration loader for driftcheck settings."""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


DEFAULT_CONFIG_PATH = ".driftcheck.json"


@dataclass
class DriftCheckConfig:
    """Top-level configuration for a driftcheck run."""
    plan_path: str = "plan.json"
    output_path: Optional[str] = None
    output_format: str = "json"  # 'json' or 'csv'
    notify_channels: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    min_drift_count: int = 1
    exit_on_drift: bool = False
    resource_types: List[str] = field(
        default_factory=lambda: ["aws_s3_bucket", "aws_instance"]
    )


def load_config(path: str = DEFAULT_CONFIG_PATH) -> DriftCheckConfig:
    """Load configuration from a JSON file.

    Falls back to defaults for missing keys. Raises FileNotFoundError if the
    file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    return DriftCheckConfig(
        plan_path=raw.get("plan_path", "plan.json"),
        output_path=raw.get("output_path"),
        output_format=raw.get("output_format", "json"),
        notify_channels=raw.get("notify_channels", []),
        webhook_url=raw.get("webhook_url"),
        min_drift_count=raw.get("min_drift_count", 1),
        exit_on_drift=raw.get("exit_on_drift", False),
        resource_types=raw.get(
            "resource_types", ["aws_s3_bucket", "aws_instance"]
        ),
    )


def save_config(config: DriftCheckConfig, path: str = DEFAULT_CONFIG_PATH) -> None:
    """Persist a DriftCheckConfig to a JSON file."""
    data = {
        "plan_path": config.plan_path,
        "output_path": config.output_path,
        "output_format": config.output_format,
        "notify_channels": config.notify_channels,
        "webhook_url": config.webhook_url,
        "min_drift_count": config.min_drift_count,
        "exit_on_drift": config.exit_on_drift,
        "resource_types": config.resource_types,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
