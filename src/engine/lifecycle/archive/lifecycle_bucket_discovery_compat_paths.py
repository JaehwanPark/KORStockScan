"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "lifecycle_bucket_discovery"


CATALOG_DIR = DATA_DIR / "threshold_cycle" / "lifecycle_bucket_catalog"


SIM_AUTO_APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "sim_auto_approvals"


CONTAMINATION_WINDOW_DIR = DATA_DIR / "threshold_cycle" / "contamination_windows"


def discovery_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"lifecycle_bucket_discovery_{target_date}.json"


def discovery_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"lifecycle_bucket_discovery_{target_date}.md"


def bucket_catalog_path(target_date: str) -> Path:
    return CATALOG_DIR / f"lifecycle_bucket_catalog_{target_date}.json"


def contamination_window_path(target_date: str) -> Path:
    return CONTAMINATION_WINDOW_DIR / f"lifecycle_bucket_quarantine_{target_date}.json"


def sim_auto_approval_path(target_date: str) -> Path:
    return (
        SIM_AUTO_APPROVAL_DIR / f"lifecycle_bucket_sim_auto_approval_{target_date}.json"
    )
