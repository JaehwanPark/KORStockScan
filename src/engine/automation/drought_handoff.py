"""Canonical drought receipts owned by postclose automation, never live policy.

EV intentionally retains a diagnostic previous-generation workorder snapshot.
The final runtime summary owns the current ID/disposition receipt instead, avoiding
an EV -> workorder -> EV regeneration cycle.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

EFFECTIVE_DATE = "2026-09-08"
CONTROLLER = "entry_recheck_drought_controller"
REQUIRED_IDS = (
    "order_entry_submit_drought_auto_resolution",
    "order_entry_post_submit_contract_gap_review",
    "order_entry_broker_receipt_contract_gap_review",
    "order_entry_fill_quality_contract_gap_review",
    "order_entry_telegram_post_submit_contract_gap_review",
    "order_entry_source_taxonomy_contract_gap_review",
)


def report_path(root: Path, owner: str, day: str) -> Path:
    return root / owner / f"{owner}_{day}.json"


def read_source(path: Path) -> tuple[dict, str | None]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return {}, None
    digest = hashlib.sha256(raw).hexdigest()
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return {}, digest
    return (value if isinstance(value, dict) else {}), digest


def controller_source_error(
    payload: dict, root: Path, day: str, *, validate_review: bool = False
) -> str:
    """Bind embedded history to canonical bytes and eligible scope meanings."""
    from src.engine.scalping.entry_ai_gate_backtest import _drought_day_summary
    from src.engine.scalping.entry_recheck_policy import trading_dates
    from src.engine.scalping.entry_recheck_review import build_review, review_orders

    if payload.get("target_date") != day:
        return "drought_controller_target_date_mismatch"
    if day < EFFECTIVE_DATE:
        return ""
    if payload.get("source_binding_version") != 1:
        return "drought_controller_source_binding_missing"
    try:
        policy = payload["drought_conditional_policy"]
        history = policy["history"]
        if not isinstance(history, list) or not history:
            return "drought_controller_history_missing"
        dates = [row["source_date"] for row in history]
        if dates != sorted(set(dates)) or dates[-1] != day:
            return "drought_controller_history_dates_invalid"
        # The additional twenty-date maintenance census is diagnostic. Its drift
        # requires a postclose review refresh, never a new PREOPEN promotion gate.
        review_days = []
        if validate_review:
            review = payload["maintenance_review"]
            review_days = review["source_days"]
            if not isinstance(review_days, list):
                return "drought_controller_review_sources_invalid"
            baseline = payload["clean_baseline_policy"]["clean_tuning_baseline_date"]
            if [r["source_date"] for r in review_days] != trading_dates(
                day, baseline, 20
            ):
                return "drought_controller_review_window_incomplete"
        for row in [*history, *review_days]:
            expected = _drought_day_summary(
                report_path(root, "buy_funnel_sentinel", row["source_date"])
            )
            if row.get("source_sha256") != expected["source_sha256"]:
                return "drought_controller_sentinel_source_changed"
            # The same producer normalization includes preflight and scope exclusion.
            # No rehashed stale meaning, invented source-quality pass, or omitted
            # valid scope can qualify merely by carrying the latest file hash.
            if {k: v for k, v in row.items() if k != "source_path"} != {
                k: v for k, v in expected.items() if k != "source_path"
            }:
                return "drought_controller_sentinel_semantic_mismatch"
        if validate_review:
            if review != build_review(policy, review_days, day):
                return "drought_controller_review_mismatch"
            if payload["code_improvement_orders"] != review_orders(review):
                return "drought_controller_review_orders_invalid"
        for candidate in payload["calibration_candidates"]:
            if candidate["source_metrics"]["drought_conditional_policy"] != policy:
                return "drought_controller_candidate_policy_mismatch"
        if len(payload["calibration_candidates"]) != 1:
            return "drought_controller_candidate_missing"
        if (
            payload["summary"]["drought_desired_enabled"]
            is not policy["desired_enabled"]
        ):
            return "drought_controller_summary_decision_mismatch"
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        return "drought_controller_source_binding_invalid"
    return ""


def controller_error(payload: dict, root: Path, day: str) -> str:
    """Use PREOPEN's existing decision validator for final postclose acceptance."""
    from src.engine.threshold_cycle_preopen_apply import (
        _entry_recheck_drought_controller_contract_error,
    )

    if payload.get("schema_version") != 1 or payload.get("report_type") != CONTROLLER:
        return "drought_controller_missing_or_invalid"
    error = controller_source_error(payload, root, day, validate_review=True)
    if error:
        return error
    try:
        candidates = payload["calibration_candidates"]
        if not isinstance(candidates, list) or not all(
            isinstance(c, dict) for c in candidates
        ):
            return "drought_controller_candidates_invalid"
        return _entry_recheck_drought_controller_contract_error(payload, candidates)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        return "drought_controller_decision_invalid"


def canonical_receipt(root: Path, day: str, ev: dict) -> dict:
    work, work_hash = read_source(report_path(root, "code_improvement_workorder", day))
    controller, controller_hash = read_source(report_path(root, CONTROLLER, day))
    issues = []
    if work.get("date") != day or work.get("target_date", day) != day:
        issues.append("drought_workorder_missing_or_wrong_date")
    rows = work.get("orders")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        issues.append("drought_workorder_orders_invalid")
        rows = []
    # Preserve all selected instructions, including additional native follow-ups.
    ids = [row.get("order_id") for row in rows]
    if any(not isinstance(i, str) or not i for i in ids) or len(
        set(str(i) for i in ids)
    ) != len(ids):
        issues.append("drought_workorder_ids_invalid_or_duplicate")
    for row in rows:
        order_id = row.get("order_id")
        if isinstance(order_id, str) and (
            order_id in REQUIRED_IDS or order_id.startswith("order_entry_recheck_")
        ):
            if (
                row.get("runtime_effect") is not False
                or row.get("allowed_runtime_apply") is not False
            ):
                issues.append("drought_workorder_source_only_authority_invalid")
            if not isinstance(row.get("decision"), str) or not row["decision"]:
                issues.append("drought_workorder_disposition_missing")
    projection = sorted(rows, key=lambda row: str(row.get("order_id", "")))
    previous_report = ev.get("code_improvement_workorder")
    previous = (
        previous_report.get("orders", []) if isinstance(previous_report, dict) else []
    )
    previous = previous if isinstance(previous, list) else []
    previous_map = {
        r.get("order_id"): r.get("decision")
        for r in previous
        if isinstance(r, dict) and isinstance(r.get("order_id"), str)
    }
    current_map = {
        r.get("order_id"): r.get("decision")
        for r in rows
        if isinstance(r.get("order_id"), str)
    }
    ev_diff = {
        "missing_in_ev": sorted(current_map.keys() - previous_map.keys()),
        "removed_from_current": sorted(
            previous_map.keys() - current_map.keys(), key=str
        ),
        "decision_changed": sorted(
            k
            for k in current_map.keys() & previous_map.keys()
            if current_map[k] != previous_map[k]
        ),
    }
    return {
        "schema_version": 1,
        "target_date": day,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "canonical_workorder_sha256": work_hash,
        "canonical_orders": projection,
        "controller_sha256": controller_hash,
        "controller_decision": controller.get("summary") or {},
        "ev_snapshot_role": "diagnostic_previous_generation_not_ev_decision_input",
        "ev_snapshot_freshness_authority": False,
        "ev_snapshot_diff": ev_diff,
        "issues": issues,
    }


def verify_drought_handoff(
    root: Path, day: str, *, ev: dict, summary: dict, require_controller: bool = True
) -> dict:
    expected = canonical_receipt(root, day, ev)
    issues = list(expected["issues"])
    if summary.get("drought_handoff") != expected:
        issues.append("drought_runtime_summary_canonical_receipt_mismatch")
    controller, _ = read_source(report_path(root, CONTROLLER, day))
    error = controller_error(controller, root, day) if require_controller else ""
    if error:
        issues.append(error)
    ids = {
        r.get("order_id")
        for r in expected["canonical_orders"]
        if isinstance(r.get("order_id"), str)
    }
    sentinel, _ = read_source(report_path(root, "buy_funnel_sentinel", day))
    contract = sentinel.get("entry_submit_drought_contract")
    if not isinstance(contract, dict):
        issues.append("drought_sentinel_contract_missing_or_invalid")
        contract = {}
    if contract.get("critical") is True:
        if set(REQUIRED_IDS) - ids:
            issues.append("drought_canonical_required_ids_missing")
    if require_controller:
        raw_orders = controller.get("code_improvement_orders")
        required = {
            r.get("order_id")
            for r in (raw_orders if isinstance(raw_orders, list) else [])
            if isinstance(r, dict) and isinstance(r.get("order_id"), str)
        }
        if required - ids:
            issues.append("drought_controller_review_orders_missing")
    return {
        "status": "fail" if issues else "pass",
        "issues": issues,
        "controller_validation_error": error or None,
        "controller_required": require_controller,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "ev_snapshot_diff": expected["ev_snapshot_diff"],
    }
