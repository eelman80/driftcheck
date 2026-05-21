"""Terraform plan parser for driftcheck.

Parses a Terraform plan JSON file (produced via `terraform show -json`)
and extracts the planned resource states for comparison.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PlannedResource:
    """Represents a single resource as described in a Terraform plan."""

    address: str
    resource_type: str
    name: str
    provider: str
    values: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"PlannedResource(address={self.address!r}, type={self.resource_type!r})"


def _extract_resources(
    root_module: dict[str, Any],
) -> list[PlannedResource]:
    """Recursively extract resources from a Terraform plan module."""
    resources: list[PlannedResource] = []

    for res in root_module.get("resources", []):
        address = res.get("address", "")
        res_type = res.get("type", "")
        res_name = res.get("name", "")
        provider = res.get("provider_name", "")
        values = res.get("values", {})
        resources.append(
            PlannedResource(
                address=address,
                resource_type=res_type,
                name=res_name,
                provider=provider,
                values=values,
            )
        )

    for child in root_module.get("child_modules", []):
        resources.extend(_extract_resources(child))

    return resources


def parse_plan(plan_path: str | Path) -> list[PlannedResource]:
    """Parse a Terraform plan JSON file and return planned resources.

    Args:
        plan_path: Path to the JSON plan file.

    Returns:
        A list of PlannedResource objects.

    Raises:
        FileNotFoundError: If the plan file does not exist.
        ValueError: If the file is not a valid Terraform plan.
    """
    plan_path = Path(plan_path)
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    with plan_path.open() as fh:
        data = json.load(fh)

    if "planned_values" not in data:
        raise ValueError(
            "Invalid Terraform plan: missing 'planned_values' key. "
            "Ensure the plan was exported with `terraform show -json`."
        )

    root_module = data["planned_values"].get("root_module", {})
    return _extract_resources(root_module)
