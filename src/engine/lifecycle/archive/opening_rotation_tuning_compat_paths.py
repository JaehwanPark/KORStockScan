"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.engine.scalping.opening_rotation import (
    POLICY_SCHEMA_VERSION,
    RUNTIME_POLICY_DIR,
    OpeningRotationRuntimePolicy,
    is_krx_regular_scope,
    load_runtime_policy,
    runtime_policy_path,
)


from src.utils.constants import DATA_DIR

REPORT_TYPE = "opening_rotation_profile_tuning"


REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE


CANDIDATE_DIR = RUNTIME_POLICY_DIR / "candidates"


def report_path(target_date: str, *, root: Path = REPORT_DIR) -> Path:
    return root / f"{REPORT_TYPE}_{target_date}.json"


def report_markdown_path(target_date: str, *, root: Path = REPORT_DIR) -> Path:
    return root / f"{REPORT_TYPE}_{target_date}.md"


def candidate_path(target_date: str, *, root: Path = CANDIDATE_DIR) -> Path:
    return root / f"opening_rotation_runtime_policy_candidate_{target_date}.json"
