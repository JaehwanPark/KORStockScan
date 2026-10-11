"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.utils.constants import DATA_DIR


REPORT_DIR = DATA_DIR / "report"


PROJECT_ROOT = Path(__file__).resolve().parents[4]


REPORT_TYPE = "ldm_hypothesis_discovery"


REPORT_OUT_DIR = REPORT_DIR / REPORT_TYPE


PLAN_DIR = (
    PROJECT_ROOT / "data" / "threshold_cycle" / "ldm_hypothesis_observation_plans"
)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_OUT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def observation_plan_path(apply_date: str) -> Path:
    return PLAN_DIR / f"ldm_hypothesis_observation_plan_{apply_date}.json"
