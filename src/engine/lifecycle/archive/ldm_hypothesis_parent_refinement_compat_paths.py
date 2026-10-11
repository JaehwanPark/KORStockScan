"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.utils.constants import DATA_DIR


REPORT_TYPE = "ldm_hypothesis_parent_refinement"


REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE


LDM_PLAN_DIR = DATA_DIR / "threshold_cycle" / "ldm_hypothesis_observation_plans"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def observation_plan_path(target_date: str) -> Path:
    return LDM_PLAN_DIR / f"ldm_hypothesis_observation_plan_{target_date}.json"


def latest_observation_plan_path(target_date: str) -> Path:
    exact = observation_plan_path(target_date)
    if exact.exists():
        return exact
    candidates: list[tuple[str, Path]] = []
    if LDM_PLAN_DIR.exists():
        for path in LDM_PLAN_DIR.glob("ldm_hypothesis_observation_plan_*.json"):
            plan_date = path.stem.removeprefix("ldm_hypothesis_observation_plan_")
            if plan_date <= target_date:
                candidates.append((plan_date, path))
    if candidates:
        return sorted(candidates)[-1][1]
    return exact
