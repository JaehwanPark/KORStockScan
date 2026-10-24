"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]


DATA_DIR = PROJECT_ROOT / "data"


REPORT_DIR = DATA_DIR / "report"


ADM_REPORT_DIR = REPORT_DIR / "scalp_entry_action_decision_matrix"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = ADM_REPORT_DIR / f"scalp_entry_action_decision_matrix_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")
