"""Build runtime-apply bridge candidates from LDM bucket attribution."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


REPORT_DIR = DATA_DIR / "report" / "runtime_apply_bridge"
LDM_REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "approvals"

ENTRY_BRIDGE_FAMILY = "entry_wait6579_score66_69_recovery_gate_v1"
SCALE_IN_BRIDGE_FAMILY = "scale_in_bucket_runtime_policy_v1"

ENTRY_TARGET_BUCKET_KEY = (
    "score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|"
    "liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown"
)


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
    if confirmations <= 0:
        return "bootstrap_pending", meta
    return "ready_for_approval", meta


def _entry_candidate(payload: dict[str, Any], history: list[dict[str, Any]], target_date: str) -> dict[str, Any]:
    bucket = _find_bucket(payload, "entry_bucket_attribution", "combo_entry_spot", ENTRY_TARGET_BUCKET_KEY)
    state, rolling = _state_for_bucket(
        bucket,
        history,
        section="entry_bucket_attribution",
        bucket_type="combo_entry_spot",
        bucket_key=ENTRY_TARGET_BUCKET_KEY,
        positive_edge=True,
    )
    return {
        "candidate_id": f"{ENTRY_BRIDGE_FAMILY}:{target_date}",
        "family": ENTRY_BRIDGE_FAMILY,
        "stage": "entry",
        "priority": 9,
        "bridge_candidate_state": state,
        "approval_required": True,
        "allowed_runtime_apply": state == "ready_for_approval",
        "runtime_effect": False,
        "runtime_effect_after_approval": "bounded_entry_probe_recovery",
        "target_env_keys": [
            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE",
            "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL",
            "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP",
            "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW",
            "AI_WAIT6579_PROBE_CANARY_MAX_QTY",
            "AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION",
            "AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE",
        ],
        "recommended_values": {
            "enabled": True,
            "min_score": 66,
            "max_score": 69,
            "min_buy_pressure": 65.0,
            "min_tick_accel": 1.2,
            "min_micro_vwap_bp": 0.0,
            "max_budget_krw": 50000,
            "max_qty": 1,
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
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "decision_authority": "ldm_bucket_runtime_bridge_approval_required",
        "forbidden_uses": [
            "artifactless_runtime_apply",
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


def _scale_candidate(payload: dict[str, Any], history: list[dict[str, Any]], target_date: str) -> dict[str, Any]:
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
    ready = pyramid_state == "ready_for_approval" or avg_state == "ready_for_approval"
    blocked_conflict = pyramid_state == "blocked_rolling_conflict" or avg_state == "blocked_rolling_conflict"
    blocked_source = pyramid_state == "blocked_source_quality" and avg_state == "blocked_source_quality"
    if blocked_conflict:
        state = "blocked_rolling_conflict"
    elif ready:
        state = "ready_for_approval"
    elif blocked_source:
        state = "blocked_source_quality"
    else:
        state = "bootstrap_pending"

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
    if pyramid:
        target_env_keys.append("SCALPING_ENABLE_PYRAMID")
        recommended_values["scalping_enable_pyramid"] = False
    if avg_down:
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
        "approval_required": True,
        "allowed_runtime_apply": state == "ready_for_approval",
        "runtime_effect": False,
        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten",
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
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "decision_authority": "ldm_bucket_runtime_bridge_approval_required",
        "forbidden_uses": [
            "artifactless_runtime_apply",
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
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    if not payload:
        warnings.append("lifecycle_decision_matrix_missing")
    else:
        history = _history_reports(target_date)
        candidates.append(_entry_candidate(payload, history, target_date))
        candidates.append(_scale_candidate(payload, history, target_date))
    status = "pass" if candidates else "fail"
    ready_count = sum(1 for item in candidates if item.get("bridge_candidate_state") == "ready_for_approval")
    report = {
        "schema_version": "runtime_apply_bridge_v1",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": {
            "lifecycle_decision_matrix": str(source_path) if source_path.exists() else None,
            "runtime_approval_summary": str(
                DATA_DIR / "report" / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json"
            ),
        },
        "status": status,
        "summary": {
            "candidate_count": len(candidates),
            "ready_for_approval_count": ready_count,
            "approval_required_count": sum(1 for item in candidates if item.get("approval_required")),
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
        f"- ready_for_approval_count: `{report.get('summary', {}).get('ready_for_approval_count')}`",
        "- runtime mutation: `none`",
        "",
        "## 근거",
        "",
    ]
    for item in report.get("candidates") or []:
        lines.extend(
            [
                f"- `{item.get('family')}`: state=`{item.get('bridge_candidate_state')}`, "
                f"allowed_runtime_apply=`{item.get('allowed_runtime_apply')}`, "
                f"approval_required=`{item.get('approval_required')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "",
            "- `ready_for_approval` 후보만 별도 approval artifact가 있으면 다음 PREOPEN env 후보로 소비한다.",
            "- `bootstrap_pending` 후보는 rolling confirmation 후 다시 판정한다.",
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
