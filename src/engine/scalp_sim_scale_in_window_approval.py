"""Build the sim-auto scalp scale-in window expansion artifact."""

from __future__ import annotations

from src.engine.lifecycle.retirement import retired_status

import json
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"
REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
POLICY_ID = "scalp_sim_scale_in_window_expansion"


def approval_path(target_date: str) -> Path:
    return APPROVAL_DIR / f"{POLICY_ID}_{target_date}.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_scalp_sim_scale_in_window_approval(target_date: str) -> dict[str, Any]:
    return retired_status("scalp_sim_scale_in_window_approval")


def main(argv: list[str] | None = None) -> int:
    print(json.dumps(retired_status("scalp_sim_scale_in_window_approval")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
