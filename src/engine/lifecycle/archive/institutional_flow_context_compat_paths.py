"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.utils.constants import DATA_DIR


REPORT_DIR = DATA_DIR / "report"


REPORT_DIR_PATH = REPORT_DIR / "institutional_flow_context"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR_PATH / f"institutional_flow_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")
