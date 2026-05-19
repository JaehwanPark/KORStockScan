"""Build the sim-only scalp scale-in window expansion approval artifact."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
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
    target_date = str(target_date).strip()
    matrix_path = REPORT_DIR / f"lifecycle_decision_matrix_{target_date}.json"
    matrix = _read_json(matrix_path)
    summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    source = matrix.get("sources") if isinstance(matrix.get("sources"), dict) else {}
    scale_source = source.get("scalp_sim_scale_in") if isinstance(source.get("scalp_sim_scale_in"), dict) else {}
    policy_entries = matrix.get("policy_entries") if isinstance(matrix.get("policy_entries"), list) else []
    scale_policy = next(
        (item for item in policy_entries if isinstance(item, dict) and item.get("stage") == "scale_in"),
        {},
    )
    artifact = {
        "schema_version": 1,
        "policy_id": POLICY_ID,
        "family": POLICY_ID,
        "stage": "scale_in",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "approved": False,
        "approval_state": "approval_required",
        "decision_authority": "sim_observation_only",
        "runtime_effect": "sim_only_virtual_scale_in_when_approved",
        "source_report": str(matrix_path) if matrix_path.exists() else None,
        "source_summary": {
            "matrix_status": summary.get("status"),
            "scale_in_rows": scale_source.get("rows", 0),
            "scale_in_filled_events": scale_source.get("filled_events", 0),
            "scale_in_unfilled_events": scale_source.get("unfilled_events", 0),
            "scale_in_policy_sample": scale_policy.get("sample"),
            "scale_in_policy_joined_sample": scale_policy.get("joined_sample"),
            "scale_in_policy_gate": scale_policy.get("source_quality_gate"),
        },
        "target_env_keys": [
            "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED",
            "SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS",
            "SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT",
            "SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT",
            "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION",
            "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY",
        ],
        "recommended_values": {
            "enabled": True,
            "allowed_arms": "PYRAMID,AVG_DOWN",
            "min_profit_pct": -2.5,
            "max_profit_pct": 2.5,
            "max_orders_per_position": 1,
            "max_orders_per_day": 30,
        },
        "approval_contract": {
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "real_order_forbidden": True,
            "same_stage_owner": "scalp_sim_scale_in_window_expansion",
            "runtime_apply_path": "next_preopen_only_after_approved_true",
            "operator_action": "set approved=true after reviewing this artifact",
        },
        "forbidden_uses": [
            "real_scale_in_order",
            "position_size_cap_release",
            "hard_safety_override",
            "intraday_threshold_mutation",
            "real_execution_quality_claim",
        ],
    }
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    approval_path(target_date).write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build scalp sim scale-in window approval artifact.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    artifact = build_scalp_sim_scale_in_window_approval(args.target_date)
    print(json.dumps(artifact, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
