"""Canonical drought receipts owned by postclose automation, never live policy.

EV intentionally retains a diagnostic previous-generation workorder snapshot.
The final runtime summary owns the current ID/disposition receipt instead, avoiding
an EV -> workorder -> EV regeneration cycle.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.engine.lifecycle.retirement import current_report_view

EFFECTIVE_DATE = "2026-09-08"
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






def canonical_receipt(root: Path, day: str, ev: dict) -> dict:
    work, work_hash = read_source(report_path(root, "code_improvement_workorder", day))
    issues = []
    if work.get("date") != day or work.get("target_date", day) != day:
        issues.append("drought_workorder_missing_or_wrong_date")
    rows = work.get("orders")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        issues.append("drought_workorder_orders_invalid")
        rows = []
    rows = current_report_view(rows)
    # Preserve normal submit-path instructions.
    ids = [row.get("order_id") for row in rows]
    if any(not isinstance(i, str) or not i for i in ids) or len(
        set(str(i) for i in ids)
    ) != len(ids):
        issues.append("drought_workorder_ids_invalid_or_duplicate")
    for row in rows:
        order_id = row.get("order_id")
        if isinstance(order_id, str) and order_id in REQUIRED_IDS:
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
        "ev_snapshot_role": "diagnostic_previous_generation_not_ev_decision_input",
        "ev_snapshot_freshness_authority": False,
        "ev_snapshot_diff": ev_diff,
        "issues": issues,
    }


def verify_drought_handoff(
    root: Path, day: str, *, ev: dict, summary: dict
) -> dict:
    expected = canonical_receipt(root, day, ev)
    issues = list(expected["issues"])
    if summary.get("drought_handoff") != expected:
        issues.append("drought_runtime_summary_canonical_receipt_mismatch")
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
    return {
        "status": "fail" if issues else "pass",
        "issues": issues,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "ev_snapshot_diff": expected["ev_snapshot_diff"],
    }
