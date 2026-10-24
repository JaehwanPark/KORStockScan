"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "runtime_apply_bridge"


APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"


GREENFIELD_POLICY_DIR = DATA_DIR / "threshold_cycle" / "greenfield_real_env_policies"


def runtime_apply_bridge_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_bridge_{target_date}.json"


def runtime_apply_bridge_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_bridge_{target_date}.md"


def ldm_scale_in_runtime_bridge_artifact_path(source_date: str) -> Path:
    return APPROVAL_DIR / f"ldm_scale_in_runtime_bridge_{source_date}.json"


def greenfield_real_env_policy_path(source_date: str) -> Path:
    return GREENFIELD_POLICY_DIR / f"greenfield_real_env_policy_{source_date}.json"
