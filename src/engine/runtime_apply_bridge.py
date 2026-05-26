"""Build runtime-apply bridge candidates from LDM bucket attribution.

The bridge now consumes lifecycle bucket discovery policy: entry/scale-in bridge
families are auto-applied when source-quality and safety contracts are closed.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.auto_promotion_contracts import tier2_validation_passed
from src.utils.constants import DATA_DIR
from src.engine.lifecycle_bucket_discovery import (
    ENTRY_LIVE_AUTO_FAMILY,
    ENTRY_LIVE_AUTO_BUCKET_KEY,
    EVIDENCE_GRADE_2_COUNTERFACTUAL,
    WAIT6579_LIVE_EXCEPTION_ARCHIVED_REASON,
    SCALE_IN_LIVE_AUTO_FAMILY,
    discovery_report_path,
)


REPORT_DIR = DATA_DIR / "report" / "runtime_apply_bridge"
LDM_REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"

ENTRY_BRIDGE_FAMILY = ENTRY_LIVE_AUTO_FAMILY
SCALE_IN_BRIDGE_FAMILY = SCALE_IN_LIVE_AUTO_FAMILY

ENTRY_TARGET_BUCKET_KEY = ENTRY_LIVE_AUTO_BUCKET_KEY
ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES = {ENTRY_BRIDGE_FAMILY}


def runtime_apply_bridge_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_bridge_{target_date}.json"


def runtime_apply_bridge_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_bridge_{target_date}.md"


def ldm_entry_runtime_bridge_artifact_path(source_date: str) -> Path:
    return APPROVAL_DIR / f"ldm_entry_runtime_bridge_{source_date}.json"


def ldm_scale_in_runtime_bridge_artifact_path(source_date: str) -> Path:
    return APPROVAL_DIR / f"ldm_scale_in_runtime_bridge_{source_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _ldm_report_path(target_date: str) -> Path:
    return LDM_REPORT_DIR / f"lifecycle_decision_matrix_{target_date}.json"


def _history_reports(target_date: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in sorted(LDM_REPORT_DIR.glob("lifecycle_decision_matrix_*.json")):
        report_date = path.stem.removeprefix("lifecycle_decision_matrix_")
        if report_date >= target_date:
            continue
        payload = _load_json(path)
        if payload:
            reports.append(payload)
    return reports[-5:]


def _find_bucket(payload: dict[str, Any], section: str, bucket_type: str, bucket_key: str) -> dict[str, Any]:
    buckets = (
        payload.get(section, {}).get("buckets", [])
        if isinstance(payload.get(section), dict)
        else []
    )
    for item in buckets:
        if not isinstance(item, dict):
            continue
        if str(item.get("bucket_type") or "") == bucket_type and str(item.get("bucket_key") or "") == bucket_key:
            return item
    return {}


def _state_for_bucket(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    section: str,
    bucket_type: str,
    bucket_key: str,
    positive_edge: bool,
) -> tuple[str, dict[str, Any]]:
    if not current or str(current.get("source_quality_gate") or "") != "pass":
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    route = str(current.get("recommended_route") or "")
    expected_route = "candidate_recovery_or_relax" if positive_edge else "candidate_tighten_or_exclude"
    if route != expected_route:
        return "blocked_source_quality", {
            "confirmation_count": 0,
            "conflict_count": 0,
            "blocked_route": route or "missing",
            "expected_route": expected_route,
        }
    current_ev = _safe_float(current.get("source_quality_adjusted_ev_pct"), 0.0) or 0.0
    if positive_edge and current_ev <= 0:
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    if (not positive_edge) and current_ev >= 0:
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}

    confirmations = 0
    conflicts = 0
    for payload in history:
        bucket = _find_bucket(payload, section, bucket_type, bucket_key)
        if not bucket or str(bucket.get("source_quality_gate") or "") != "pass":
            continue
        ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"), None)
        if ev is None:
            continue
        if (positive_edge and ev > 0) or ((not positive_edge) and ev < 0):
            confirmations += 1
        else:
            conflicts += 1
    meta = {"confirmation_count": confirmations, "conflict_count": conflicts}
    if conflicts:
        return "blocked_rolling_conflict", meta
    meta["daily_only_auto_apply"] = confirmations <= 0
    return "live_auto_apply_ready", meta


def _discovery_live_families(discovery: dict[str, Any]) -> set[str]:
    return {
        str(item.get("live_auto_apply_family"))
        for item in (
            discovery.get("live_auto_apply_candidates")
            if isinstance(discovery.get("live_auto_apply_candidates"), list)
            else []
        )
        if (
            isinstance(item, dict)
            and item.get("live_auto_apply_family")
            and str(item.get("live_auto_apply_family")) not in ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES
            and _discovery_candidate_tier2_passed(item)
        )
    }


def _discovery_candidate_tier2_passed(item: dict[str, Any]) -> bool:
    contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
    status = (
        item.get("ai_review_status")
        or item.get("lifecycle_bucket_discovery_ai_review_status")
        or contract.get("tier2_status")
    )
    return tier2_validation_passed(status)


def _discovery_live_candidate_by_family(discovery: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = (
        discovery.get("live_auto_apply_candidates")
        if isinstance(discovery.get("live_auto_apply_candidates"), list)
        else []
    )
    by_family: dict[str, dict[str, Any]] = {}
    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("live_auto_apply_family") or "")
        if family in ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES:
            continue
        if family and _discovery_candidate_tier2_passed(item) and family not in by_family:
            by_family[family] = item
    return by_family


def _discovery_summary_meta(discovery: dict[str, Any]) -> dict[str, Any]:
    summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    return {
        "lifecycle_bucket_discovery_source_contract_status": summary.get("source_contract_status"),
        "lifecycle_bucket_discovery_ai_review_status": summary.get("ai_two_pass_review_status"),
    }


def _discovery_candidate_meta(
    *,
    family: str,
    discovery: dict[str, Any],
    discovery_live_by_family: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    meta = _discovery_summary_meta(discovery)
    item = discovery_live_by_family.get(family) or {}
    if item:
        meta.update(
            {
                "lifecycle_bucket_discovery_bucket_id": item.get("bucket_id"),
                "lifecycle_bucket_discovery_classification_state": item.get("classification_state"),
                "lifecycle_bucket_discovery_bucket_relation": item.get("bucket_relation"),
                "lifecycle_bucket_discovery_ai_final_decision": item.get("ai_final_decision"),
                "lifecycle_bucket_discovery_ai_final_reason": item.get("ai_final_reason"),
                "lifecycle_bucket_discovery_ai_followup_required": item.get("ai_review_followup_required"),
                "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get("ai_review_block_ignored_reason"),
            }
        )
    return {key: value for key, value in meta.items() if value not in (None, "", [])}


def _align_with_discovery(
    state: str,
    rolling: dict[str, Any],
    *,
    family: str,
    discovery_live_families: set[str],
    discovery_available: bool,
) -> tuple[str, dict[str, Any]]:
    aligned = dict(rolling)
    if state != "live_auto_apply_ready":
        return state, aligned
    if family in discovery_live_families:
        aligned["lifecycle_bucket_discovery_gate"] = "pass"
        return state, aligned
    aligned["lifecycle_bucket_discovery_gate"] = "blocked"
    aligned["lifecycle_bucket_discovery_available"] = bool(discovery_available)
    return "runtime_blocked_contract_gap", aligned


def _entry_candidate(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    target_date: str,
    *,
    discovery_live_families: set[str],
    discovery_live_by_family: dict[str, dict[str, Any]],
    discovery: dict[str, Any],
    discovery_available: bool,
) -> dict[str, Any]:
    bucket = _find_bucket(payload, "entry_bucket_attribution", "combo_entry_spot", ENTRY_TARGET_BUCKET_KEY)
    state, rolling = _state_for_bucket(
        bucket,
        history,
        section="entry_bucket_attribution",
        bucket_type="combo_entry_spot",
        bucket_key=ENTRY_TARGET_BUCKET_KEY,
        positive_edge=True,
    )
    state, rolling = _align_with_discovery(
        state,
        rolling,
        family=ENTRY_BRIDGE_FAMILY,
        discovery_live_families=discovery_live_families,
        discovery_available=discovery_available,
    )
    observed_state = state
    state = "legacy_counterfactual_live_exception_removed"
    rolling = {
        **rolling,
        "observed_bridge_state_before_archive": observed_state,
        "archived_live_exception_reason": WAIT6579_LIVE_EXCEPTION_ARCHIVED_REASON,
    }
    discovery_meta = _discovery_candidate_meta(
        family=ENTRY_BRIDGE_FAMILY,
        discovery=discovery,
        discovery_live_by_family=discovery_live_by_family,
    )
    return {
        "candidate_id": f"{ENTRY_BRIDGE_FAMILY}:{target_date}",
        "family": ENTRY_BRIDGE_FAMILY,
        "stage": "entry",
        "priority": 9,
        "bridge_candidate_state": state,
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": False,
        "allowed_runtime_apply": False,
        "runtime_effect": False,
        "runtime_effect_after_approval": "none_archived_counterfactual_live_exception",
        "target_env_keys": [],
        "recommended_values": {
            "threshold_version": f"{ENTRY_BRIDGE_FAMILY}:{target_date}",
            "calibration_state": f"runtime_apply_bridge:{state}",
        },
        "current_values": {
            "enabled": False,
            "min_score": 65,
            "max_score": 74,
            "max_budget_krw": 50000,
            "max_qty": 1,
            "threshold_version": "runtime_default",
            "calibration_state": "runtime_default",
        },
        "source_bucket_keys": [ENTRY_TARGET_BUCKET_KEY],
        "source_bucket": bucket,
        "rolling_confirmation": rolling,
        **discovery_meta,
        "evidence_grade": EVIDENCE_GRADE_2_COUNTERFACTUAL,
        "transition_target": "sim_lifecycle_handoff",
        "grade_reason": "wait6579_ev_cohort_is_counterfactual_source_not_completed_lifecycle_evidence",
        "full_real_conversion_allowed": False,
        "legacy_family_archived": True,
        "archived_live_exception_reason": WAIT6579_LIVE_EXCEPTION_ARCHIVED_REASON,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "decision_authority": "runtime_apply_bridge_archived_counterfactual_exception",
        "forbidden_uses": [
            "bounded_live_apply",
            "intraday_threshold_mutation",
            "broker_guard_bypass",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }


def _scale_source(bucket: dict[str, Any], *, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "bucket_type": bucket.get("bucket_type"),
        "bucket_key": bucket.get("bucket_key"),
        "joined_sample": bucket.get("joined_sample"),
        "source_quality_adjusted_ev_pct": bucket.get("source_quality_adjusted_ev_pct"),
        "recommended_route": bucket.get("recommended_route"),
        "source_quality_gate": bucket.get("source_quality_gate"),
    }


def _scale_candidate(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    target_date: str,
    *,
    discovery_live_families: set[str],
    discovery_live_by_family: dict[str, dict[str, Any]],
    discovery: dict[str, Any],
    discovery_available: bool,
) -> dict[str, Any]:
    pyramid = _find_bucket(payload, "scale_in_bucket_attribution", "arm", "PYRAMID")
    avg_down = _find_bucket(payload, "scale_in_bucket_attribution", "blocker_namespace", "AVG_DOWN_ONLY")
    pyramid_state, pyramid_roll = _state_for_bucket(
        pyramid,
        history,
        section="scale_in_bucket_attribution",
        bucket_type="arm",
        bucket_key="PYRAMID",
        positive_edge=False,
    )
    avg_state, avg_roll = _state_for_bucket(
        avg_down,
        history,
        section="scale_in_bucket_attribution",
        bucket_type="blocker_namespace",
        bucket_key="AVG_DOWN_ONLY",
        positive_edge=False,
    )
    ready = pyramid_state == "live_auto_apply_ready" or avg_state == "live_auto_apply_ready"
    blocked_conflict = pyramid_state == "blocked_rolling_conflict" or avg_state == "blocked_rolling_conflict"
    blocked_source = pyramid_state == "blocked_source_quality" and avg_state == "blocked_source_quality"
    if blocked_conflict:
        state = "blocked_rolling_conflict"
    elif ready:
        state = "live_auto_apply_ready"
    elif blocked_source:
        state = "blocked_source_quality"
    else:
        state = "bootstrap_pending"
    if state == "live_auto_apply_ready" and SCALE_IN_BRIDGE_FAMILY not in discovery_live_families:
        state = "runtime_blocked_contract_gap"
        pyramid_roll = {**pyramid_roll, "lifecycle_bucket_discovery_gate": "blocked"}
        avg_roll = {**avg_roll, "lifecycle_bucket_discovery_gate": "blocked"}
        pyramid_roll["lifecycle_bucket_discovery_available"] = bool(discovery_available)
        avg_roll["lifecycle_bucket_discovery_available"] = bool(discovery_available)
    discovery_meta = _discovery_candidate_meta(
        family=SCALE_IN_BRIDGE_FAMILY,
        discovery=discovery,
        discovery_live_by_family=discovery_live_by_family,
    )

    target_env_keys = ["SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP"]
    recommended_values: dict[str, Any] = {
        "effective_qty_cap": 1,
        "threshold_version": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "calibration_state": f"runtime_apply_bridge:{state}",
    }
    current_values: dict[str, Any] = {
        "effective_qty_cap": 1,
        "scalping_enable_pyramid": True,
        "reversal_add_min_ai_score": 60,
        "reversal_add_min_buy_pressure": 55.0,
        "reversal_add_min_tick_accel": 0.95,
    }
    if pyramid_state == "live_auto_apply_ready":
        target_env_keys.append("SCALPING_ENABLE_PYRAMID")
        recommended_values["scalping_enable_pyramid"] = False
    if avg_state == "live_auto_apply_ready":
        target_env_keys.extend(
            [
                "REVERSAL_ADD_MIN_AI_SCORE",
                "REVERSAL_ADD_MIN_BUY_PRESSURE",
                "REVERSAL_ADD_MIN_TICK_ACCEL",
            ]
        )
        recommended_values.update(
            {
                "reversal_add_min_ai_score": 65,
                "reversal_add_min_buy_pressure": 60.0,
                "reversal_add_min_tick_accel": 1.05,
            }
        )

    source_buckets = []
    if pyramid:
        source_buckets.append(_scale_source(pyramid, role="pyramid_tighten_or_disable"))
    if avg_down:
        source_buckets.append(_scale_source(avg_down, role="avg_down_reversal_tighten"))
    positive_refs = []
    for item in payload.get("scale_in_bucket_attribution", {}).get("buckets", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("recommended_route") or "") == "candidate_recovery_or_relax":
            positive_refs.append(_scale_source(item, role="observe_only_reference"))

    return {
        "candidate_id": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "family": SCALE_IN_BRIDGE_FAMILY,
        "stage": "scale_in",
        "priority": 39,
        "bridge_candidate_state": state,
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": state == "live_auto_apply_ready",
        "allowed_runtime_apply": state == "live_auto_apply_ready",
        "runtime_effect": False,
        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
        "target_env_keys": list(dict.fromkeys(target_env_keys)),
        "recommended_values": recommended_values,
        "current_values": current_values,
        "source_bucket_keys": [str(item.get("bucket_key") or "") for item in source_buckets],
        "source_buckets": source_buckets,
        "observe_only_reference_buckets": positive_refs[:5],
        "rolling_confirmation": {
            "pyramid": pyramid_roll,
            "avg_down": avg_roll,
            "pyramid_state": pyramid_state,
            "avg_down_state": avg_state,
        },
        **discovery_meta,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "decision_authority": "lifecycle_bucket_discovery_live_auto_apply",
        "forbidden_uses": [
            "position_cap_release",
            "scale_in_safety_guard_bypass",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }


def build_runtime_apply_bridge_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_path = _ldm_report_path(target_date)
    payload = _load_json(source_path)
    discovery_path = discovery_report_path(target_date)
    discovery = _load_json(discovery_path)
    discovery_live_families = _discovery_live_families(discovery)
    discovery_live_by_family = _discovery_live_candidate_by_family(discovery)
    discovery_summary = discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    discovery_warnings = [str(item) for item in (discovery.get("warnings") or []) if str(item)]
    discovery_source_contract_status = str(discovery_summary.get("source_contract_status") or "")
    discovery_ai_review_status = str(discovery_summary.get("ai_two_pass_review_status") or "")
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    if not payload:
        warnings.append("lifecycle_decision_matrix_missing")
    else:
        history = _history_reports(target_date)
        if not discovery:
            warnings.append("lifecycle_bucket_discovery_missing")
        candidates.append(
            _entry_candidate(
                payload,
                history,
                target_date,
                discovery_live_families=discovery_live_families,
                discovery_live_by_family=discovery_live_by_family,
                discovery=discovery,
                discovery_available=bool(discovery),
            )
        )
        candidates.append(
            _scale_candidate(
                payload,
                history,
                target_date,
                discovery_live_families=discovery_live_families,
                discovery_live_by_family=discovery_live_by_family,
                discovery=discovery,
                discovery_available=bool(discovery),
            )
        )
    if discovery and discovery_source_contract_status and discovery_source_contract_status != "pass":
        warnings.append(f"lifecycle_bucket_discovery_source_contract_{discovery_source_contract_status}")
    if discovery and any(item.get("lifecycle_bucket_discovery_ai_followup_required") for item in candidates):
        warnings.append("lifecycle_bucket_discovery_live_auto_post_apply_followup_required")
    warnings.extend(
        item
        for item in discovery_warnings
        if item.startswith("ai_") or item.startswith("source_contract_")
    )
    warnings = list(dict.fromkeys(warnings))
    status = "pass" if candidates else "fail"
    live_ready_count = sum(1 for item in candidates if item.get("bridge_candidate_state") == "live_auto_apply_ready")
    live_followup_count = sum(
        1
        for item in candidates
        if item.get("bridge_candidate_state") == "live_auto_apply_ready"
        and item.get("lifecycle_bucket_discovery_ai_followup_required")
    )
    report = {
        "schema_version": "runtime_apply_bridge_v1",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": {
            "lifecycle_decision_matrix": str(source_path) if source_path.exists() else None,
            "lifecycle_bucket_discovery": str(discovery_path) if discovery_path.exists() else None,
            "runtime_approval_summary": str(
                DATA_DIR / "report" / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json"
            ),
        },
        "status": status,
        "summary": {
            "candidate_count": len(candidates),
            "ready_for_approval_count": 0,
            "live_auto_apply_ready_count": live_ready_count,
            "lifecycle_bucket_discovery_status": "present" if discovery else "missing",
            "lifecycle_bucket_discovery_source_contract_status": discovery_source_contract_status or None,
            "lifecycle_bucket_discovery_ai_review_status": discovery_ai_review_status or None,
            "lifecycle_bucket_discovery_live_followup_count": live_followup_count,
            "approval_required_count": sum(1 for item in candidates if item.get("approval_required")),
            "human_approval_required": False,
            "runtime_mutation_performed": False,
        },
        "candidates": candidates,
        "warnings": warnings,
    }
    return report


def _write_markdown(report: dict[str, Any]) -> None:
    target_date = str(report.get("date") or "")
    lines = [
        f"# Runtime Apply Bridge {target_date}",
        "",
        "## 판정",
        "",
        f"- status: `{report.get('status')}`",
        f"- live_auto_apply_ready_count: `{report.get('summary', {}).get('live_auto_apply_ready_count')}`",
        f"- lifecycle_bucket_discovery_source_contract_status: `{report.get('summary', {}).get('lifecycle_bucket_discovery_source_contract_status') or '-'}`",
        f"- lifecycle_bucket_discovery_ai_review_status: `{report.get('summary', {}).get('lifecycle_bucket_discovery_ai_review_status') or '-'}`",
        f"- lifecycle_bucket_discovery_live_followup_count: `{report.get('summary', {}).get('lifecycle_bucket_discovery_live_followup_count')}`",
        f"- human_approval_required: `{report.get('summary', {}).get('human_approval_required')}`",
        "- runtime mutation: `none`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## 근거",
        "",
    ]
    for item in report.get("candidates") or []:
        lines.extend(
            [
                f"- `{item.get('family')}`: state=`{item.get('bridge_candidate_state')}`, "
                f"allowed_runtime_apply=`{item.get('allowed_runtime_apply')}`, "
                f"approval_required=`{item.get('approval_required')}`, "
                f"live_auto_apply=`{item.get('live_auto_apply')}`, "
                f"ai_followup=`{item.get('lifecycle_bucket_discovery_ai_followup_required') or '-'}`",
            ]
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "",
            "- `live_auto_apply_ready` 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.",
            "- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.",
        ]
    )
    runtime_apply_bridge_markdown_path(target_date).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_runtime_apply_bridge_report(target_date: str) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_runtime_apply_bridge_report(target_date)
    runtime_apply_bridge_report_path(target_date).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_markdown(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build LDM runtime apply bridge report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = write_runtime_apply_bridge_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get("status") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
