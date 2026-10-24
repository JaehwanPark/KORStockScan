"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import re


from pathlib import Path


from typing import Any, Iterable


from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report"


MATRIX_DIR = REPORT_DIR / "lifecycle_decision_matrix"


def report_paths(
    target_date: str, *, output_suffix: str | None = None
) -> tuple[Path, Path]:
    suffix = f"_{_safe_slug(output_suffix)}" if output_suffix else ""
    base = MATRIX_DIR / f"lifecycle_decision_matrix_{target_date}{suffix}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9_-]+", "_", text).strip("_")
