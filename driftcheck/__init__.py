"""driftcheck — Compares live infrastructure state against Terraform plans
to surface silent config drift.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("driftcheck")
except PackageNotFoundError:  # package not installed (e.g. during dev)
    __version__ = "0.0.0"

from driftcheck.parser import parse_plan, PlannedResource  # noqa: F401

__all__ = [
    "__version__",
    "parse_plan",
    "PlannedResource",
]
