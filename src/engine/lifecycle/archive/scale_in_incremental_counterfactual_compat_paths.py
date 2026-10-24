"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from pathlib import Path


from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "scale_in_incremental_counterfactual"


PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"


REPORT_TYPE = "scale_in_incremental_counterfactual"


def report_paths(
    target_date: str, artifact_suffix: str | None = None
) -> tuple[Path, Path]:
    suffix = f"_{artifact_suffix}" if artifact_suffix else ""
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}{suffix}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    plain = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    return plain if plain.exists() else plain.with_suffix(plain.suffix + ".gz")
