"""Build a source-only postclose report for limit-down raw-tick observations."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "report" / "limit_down_watch"
CANDIDATE_DIR = DATA_DIR / "report" / "limit_down_watch_candidate_source"
RUNTIME_DIR = DATA_DIR / "runtime"
COUNTERFACTUAL_DIR = DATA_DIR / "report" / "limit_down_watch_counterfactual"
SIM_POLICY_DIR = DATA_DIR / "threshold_cycle" / "scalp_sim_policies"
POST_SIM_DIR = DATA_DIR / "report" / "limit_down_watch_post_sim_attribution"
BOUNDED_CANDIDATE_DIR = DATA_DIR / "threshold_cycle" / "bounded_live_candidates"
APPROVAL_DIR = DATA_DIR / "approval"

ROLLOUT_DATE = date(2026, 7, 28)
CONVERSION_SAMPLE_FLOOR = {
    "observation_days": 5,
    "ordered_paths": 20,
    "ordered_path_capture_rate_pct": 80.0,
}
CONVERSION_SAMPLE_FLOOR_NAME = "5_dates_20_paths_capture80pct_independent_cell_floors"
POST_SIM_SAMPLE_FLOOR_NAME = "20_prior_policy_matches_with_independent_cell_floors"
CONVERSION_FORBIDDEN_USES = (
    "direct_real_order,automatic_runtime_apply,provider_route_change,"
    "bot_restart,hard_safety_bypass"
)
LIVE_AUTO_FORBIDDEN_USES = (
    "direct_broker_order_submission,hard_safety_bypass,stale_quote_bypass,"
    "account_order_quantity_cooldown_bypass,provider_route_change,bot_restart,"
    "scale_in,reentry,overnight,position_sizing_owner_override"
)
COUNTERFACTUAL_METRIC_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "limit_down_counterfactual_sim_only",
    "window_policy": "rolling_clean_baseline_ordered_unlock_entry",
    "sample_floor": CONVERSION_SAMPLE_FLOOR_NAME,
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "valid_ordered_path_and_raw_row_exclusion",
    "forbidden_uses": CONVERSION_FORBIDDEN_USES,
}
POST_SIM_METRIC_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "limit_down_post_sim_attribution_only",
    "window_policy": "rolling_clean_baseline_post_sim_attribution",
    "sample_floor": POST_SIM_SAMPLE_FLOOR_NAME,
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "valid_sim_attribution_and_raw_row_exclusion",
    "forbidden_uses": CONVERSION_FORBIDDEN_USES,
}

CONTRACT = {
    "metric_role": "diagnostic",
    "decision_authority": "limit_down_source_observation_only",
    "window_policy": "same_symbol_same_krx_session_ordered_0b_trade_and_0d_quote",
    "sample_floor": "not_applicable_source_observation",
    "primary_decision_metric": "ordered_intraday_path_capture_rate",
    "source_quality_gate": (
        "official_ka10017_exact_or_completed_daily_near_limit_ka10081_db_match"
    ),
    "forbidden_uses": (
        "real_order,buy_analysis,threshold_change,provider_route_change,"
        "order_price_or_quantity_change,cap_change,broker_guard_change,"
        "bot_restart_authority"
    ),
    "runtime_effect": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "allowed_sim_apply": False,
    "allowed_runtime_apply": False,
}
LIVE_AUTO_COHORTS = {
    "consecutive_limit_down_2plus",
    "single_limit_down",
    "near_limit_rebound",
}


def _safe_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contract_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    return None


def _event_contract_valid(row: dict[str, Any]) -> bool:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return (
        fields.get("decision_authority") == "limit_down_source_observation_only"
        and _contract_bool(fields.get("runtime_effect")) is False
        and _contract_bool(fields.get("actual_order_submitted")) is False
        and _contract_bool(fields.get("broker_order_forbidden")) is True
    )


def _load_events(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    initial_status = {
        "path": str(path),
        "exists": path.exists(),
        "readable": False,
        "read_mode": "streaming_filtered",
        "full_source_materialized": False,
        "line_count": 0,
        "invalid_json_line_count": 0,
        "invalid_schema_line_count": 0,
        "matching_event_count": 0,
        "contract_violation_count": 0,
    }
    status = dict(initial_status)
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                status["line_count"] += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    status["invalid_json_line_count"] += 1
                    continue
                if not isinstance(row, dict):
                    status["invalid_schema_line_count"] += 1
                    continue
                if row.get("pipeline") == "LIMIT_DOWN_WATCH":
                    rows.append(row)
                    if not _event_contract_valid(row):
                        status["contract_violation_count"] += 1
    except (OSError, UnicodeError):
        return [], initial_status
    status["readable"] = True
    status["matching_event_count"] = len(rows)
    status["valid"] = bool(
        status["exists"]
        and status["readable"]
        and status["invalid_json_line_count"] == 0
        and status["invalid_schema_line_count"] == 0
        and status["contract_violation_count"] == 0
    )
    return rows, status


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _candidate_source_summary(
    target_date: str, candidate_source: dict[str, Any]
) -> dict[str, Any]:
    candidates = (
        candidate_source.get("candidates")
        if isinstance(candidate_source.get("candidates"), list)
        else []
    )
    source_pass_count = sum(
        1
        for row in candidates
        if isinstance(row, dict) and row.get("source_quality") == "pass"
    )
    candidate_source_valid = (
        candidate_source.get("schema_version") == 1
        and candidate_source.get("report_type") == "limit_down_watch_candidate_source"
        and candidate_source.get("target_date") == target_date
        and candidate_source.get("status") in {"pass", "partial"}
        and candidate_source.get("candidate_count") == len(candidates)
        and candidate_source.get("decision_authority")
        == "limit_down_source_observation_only"
        and candidate_source.get("runtime_effect") is False
        and candidate_source.get("actual_order_submitted") is False
        and candidate_source.get("broker_order_forbidden") is True
    )
    if not candidate_source:
        source_quality_status = "missing"
    elif not candidate_source_valid:
        source_quality_status = "stale_or_invalid"
    elif source_pass_count != len(candidates):
        source_quality_status = "blocked"
    elif candidate_source.get("status") == "partial":
        source_quality_status = "pass_with_exclusions"
    elif candidates:
        source_quality_status = "pass"
    else:
        source_quality_status = "no_candidate"
    return {
        "candidates": candidates,
        "source_pass_count": source_pass_count,
        "candidate_source_valid": candidate_source_valid,
        "source_quality_status": source_quality_status,
        "event_source_required": bool(
            candidate_source_valid
            and candidates
            and source_quality_status in {"pass", "pass_with_exclusions"}
        ),
    }


def _event_source_not_scanned(path: Path, *, reason: str) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "readable": None,
        "read_mode": "not_scanned_candidate_preflight",
        "full_source_materialized": False,
        "line_count": 0,
        "invalid_json_line_count": 0,
        "invalid_schema_line_count": 0,
        "matching_event_count": 0,
        "contract_violation_count": 0,
        "valid": None,
        "scan_skipped": True,
        "scan_skip_reason": reason,
    }


def _artifact_path_map(target_date: str) -> dict[str, Path]:
    return {
        "runtime_state": RUNTIME_DIR / f"limit_down_watch_state_{target_date}.json",
        "counterfactual": COUNTERFACTUAL_DIR
        / f"limit_down_watch_counterfactual_{target_date}.json",
        "sim_policy_catalog": SIM_POLICY_DIR
        / f"limit_down_watch_sim_policy_catalog_{target_date}.json",
        "post_sim_attribution": POST_SIM_DIR
        / f"limit_down_watch_post_sim_attribution_{target_date}.json",
        "bounded_live_candidate": BOUNDED_CANDIDATE_DIR
        / f"limit_down_watch_bounded_live_candidate_{target_date}.json",
        "live_conversion_approval": APPROVAL_DIR
        / f"limit_down_watch_live_conversion_approval_{target_date}.json",
    }


def _safe_target_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value or "").strip())
    except ValueError:
        return None


def _rolling_observation_evidence(
    target_date: str,
    *,
    current_status: str,
    current_groups: list[dict[str, Any]],
    current_readiness: dict[str, Any],
    history_dir: Path,
) -> dict[str, Any]:
    target = _safe_target_date(target_date)
    daily_rows: list[dict[str, Any]] = []
    if target is not None and history_dir.exists():
        for path in sorted(history_dir.glob("limit_down_watch_*.json")):
            payload = _load_json(path)
            report_date = _safe_target_date(payload.get("target_date"))
            if (
                report_date is None
                or report_date < ROLLOUT_DATE
                or report_date >= target
                or payload.get("schema_version") != 1
                or payload.get("report_type") != "limit_down_watch"
                or payload.get("runtime_effect") is not False
                or payload.get("actual_order_submitted") is not False
                or payload.get("broker_order_forbidden") is not True
                or payload.get("allowed_runtime_apply") is not False
            ):
                continue
            readiness = (
                payload.get("evidence_readiness")
                if isinstance(payload.get("evidence_readiness"), dict)
                else {}
            )
            if (
                payload.get("status") not in {"pass", "no_observation"}
                or readiness.get("candidate_source_valid") is not True
                or readiness.get("event_source_valid") is not True
            ):
                continue
            groups = (
                payload.get("groups") if isinstance(payload.get("groups"), list) else []
            )
            daily_rows.append(
                {
                    "target_date": report_date.isoformat(),
                    "groups": [row for row in groups if isinstance(row, dict)],
                }
            )
    if (
        target is not None
        and target >= ROLLOUT_DATE
        and current_status in {"pass", "no_observation"}
        and current_readiness.get("candidate_source_valid") is True
        and current_readiness.get("event_source_valid") is True
    ):
        daily_rows.append(
            {
                "target_date": target_date,
                "groups": [row for row in current_groups if isinstance(row, dict)],
            }
        )

    registered = 0
    ordered_paths = 0
    cohort_paths: dict[str, int] = defaultdict(int)
    path_dates: set[str] = set()
    included_dates: list[str] = []
    for daily in daily_rows:
        included_dates.append(str(daily["target_date"]))
        daily_paths = 0
        for group in daily["groups"]:
            if str(group.get("cohort") or "") not in LIVE_AUTO_COHORTS:
                continue
            group_registered = _safe_int(group.get("registered_codes"))
            group_paths = _safe_int(group.get("ordered_path_captured_codes"))
            registered += max(0, group_registered)
            ordered_paths += max(0, group_paths)
            daily_paths += max(0, group_paths)
            cohort_paths[str(group.get("cohort") or "unknown")] += max(0, group_paths)
        if daily_paths > 0:
            path_dates.add(str(daily["target_date"]))

    capture_rate = round(ordered_paths / registered * 100.0, 4) if registered else 0.0
    checks = {
        "observation_days": len(path_dates)
        >= CONVERSION_SAMPLE_FLOOR["observation_days"],
        "ordered_paths": ordered_paths >= CONVERSION_SAMPLE_FLOOR["ordered_paths"],
        "ordered_path_capture_rate_pct": (
            capture_rate >= CONVERSION_SAMPLE_FLOOR["ordered_path_capture_rate_pct"]
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "insufficient_sample",
        "window_start": ROLLOUT_DATE.isoformat(),
        "window_end": target_date,
        "included_dates": sorted(set(included_dates)),
        "ordered_path_observation_dates": sorted(path_dates),
        "observation_day_count": len(path_dates),
        "registered_code_count": registered,
        "ordered_path_captured_code_count": ordered_paths,
        "ordered_intraday_path_capture_rate": capture_rate,
        "cohort_ordered_path_counts": dict(sorted(cohort_paths.items())),
        "sample_floor": dict(CONVERSION_SAMPLE_FLOOR),
        "checks": checks,
    }


def _source_only_contract_valid(payload: dict[str, Any], target_date: str) -> bool:
    return bool(
        payload.get("schema_version") == 1
        and payload.get("target_date") == target_date
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
    )


def _contract_mismatches(
    payload: dict[str, Any], expected: dict[str, Any]
) -> list[str]:
    return [
        f"contract_mismatch:{field}"
        for field, expected_value in expected.items()
        if payload.get(field) != expected_value
    ]


def _conversion_artifact_checks(
    target_date: str, paths: dict[str, Path]
) -> dict[str, Any]:
    counterfactual = _load_json(paths["counterfactual"])
    counterfactual_ev = _safe_float(
        counterfactual.get("source_quality_adjusted_ev_pct")
    )
    cumulative_update = (
        counterfactual.get("cumulative_update")
        if isinstance(counterfactual.get("cumulative_update"), dict)
        else {}
    )
    cumulative_rows = (
        counterfactual.get("rows")
        if isinstance(counterfactual.get("rows"), list)
        else []
    )
    counterfactual_checks = {
        "source_only_contract_invalid": _source_only_contract_valid(
            counterfactual, target_date
        ),
        "report_type_invalid": counterfactual.get("report_type")
        == "limit_down_watch_counterfactual",
        "status_not_pass": counterfactual.get("status") == "pass",
        "source_quality_not_pass": counterfactual.get("source_quality_status")
        in {"pass", "pass_with_exclusions"},
        "sample_floor_not_met": _safe_int(counterfactual.get("sample_count"))
        >= CONVERSION_SAMPLE_FLOOR["ordered_paths"],
        "observation_day_floor_not_met": _safe_int(
            counterfactual.get("observation_date_count")
        )
        >= CONVERSION_SAMPLE_FLOOR["observation_days"],
        "eligible_policy_missing": _safe_int(
            counterfactual.get("eligible_policy_count")
        )
        > 0,
        "eligible_policy_ev_not_positive": (
            (_safe_float(counterfactual.get("best_eligible_policy_ev_pct")) or 0.0)
            > 0.0
        ),
        "cumulative_update_mode_invalid": cumulative_update.get("mode")
        == "latest_prior_rolling_rows_plus_current_dedup_by_row_id",
        "cumulative_row_count_mismatch": _safe_int(
            cumulative_update.get("deduplicated_rolling_row_count")
        )
        == len(cumulative_rows),
    }
    counterfactual_issues = (
        ["artifact_missing"]
        if not counterfactual
        else [
            *[name for name, passed in counterfactual_checks.items() if not passed],
            *_contract_mismatches(counterfactual, COUNTERFACTUAL_METRIC_CONTRACT),
        ]
    )
    counterfactual_valid = not counterfactual_issues

    sim_policy = _load_json(paths["sim_policy_catalog"])
    sim_policy_checks = {
        "source_only_contract_invalid": _source_only_contract_valid(
            sim_policy, target_date
        ),
        "report_type_invalid": sim_policy.get("report_type")
        == "limit_down_watch_sim_policy_catalog",
        "status_not_pass": sim_policy.get("status") == "pass",
        "sim_apply_not_allowed": sim_policy.get("allowed_sim_apply") is True,
        "active_policy_missing": _safe_int(sim_policy.get("active_policy_count")) > 0,
        "decision_authority_invalid": sim_policy.get("decision_authority")
        == "limit_down_sim_policy_only",
        "forbidden_uses_invalid": sim_policy.get("forbidden_uses")
        == CONVERSION_FORBIDDEN_USES,
    }
    sim_policy_issues = (
        ["artifact_missing"]
        if not sim_policy
        else [name for name, passed in sim_policy_checks.items() if not passed]
    )
    sim_policy_valid = not sim_policy_issues

    post_sim = _load_json(paths["post_sim_attribution"])
    post_sim_ev = _safe_float(post_sim.get("source_quality_adjusted_ev_pct"))
    post_sim_checks = {
        "source_only_contract_invalid": _source_only_contract_valid(
            post_sim, target_date
        ),
        "report_type_invalid": post_sim.get("report_type")
        == "limit_down_watch_post_sim_attribution",
        "status_not_pass": post_sim.get("status") == "pass",
        "source_quality_not_pass": post_sim.get("source_quality_status")
        in {"pass", "pass_with_exclusions"},
        "sample_floor_not_met": _safe_int(post_sim.get("sample_count"))
        >= CONVERSION_SAMPLE_FLOOR["ordered_paths"],
        "qualified_policy_missing": _safe_int(post_sim.get("qualified_policy_count"))
        > 0,
        "qualified_policy_ev_not_positive": (
            (_safe_float(post_sim.get("best_qualified_policy_ev_pct")) or 0.0) > 0.0
        ),
    }
    post_sim_issues = (
        ["artifact_missing"]
        if not post_sim
        else [
            *[name for name, passed in post_sim_checks.items() if not passed],
            *_contract_mismatches(post_sim, POST_SIM_METRIC_CONTRACT),
        ]
    )
    post_sim_valid = not post_sim_issues

    bounded = _load_json(paths["bounded_live_candidate"])
    bounded_candidates = (
        bounded.get("candidates") if isinstance(bounded.get("candidates"), list) else []
    )
    bounded_candidate_rows_valid = bool(
        bounded_candidates
        and all(
            isinstance(row, dict)
            and str(row.get("policy_key") or "")
            == f"{row.get('cohort')}|{row.get('price_band')}"
            and _safe_int(row.get("sample_count")) >= 1
            and _safe_float(row.get("source_quality_adjusted_ev_pct")) is not None
            and _safe_float(row.get("source_quality_adjusted_ev_pct")) > 0.0
            and _safe_float(row.get("downside_p10_pct")) is not None
            and _safe_float(row.get("downside_p10_pct")) > 0.0
            and _safe_float(row.get("mae_p10_pct")) is not None
            and _safe_float(row.get("mae_p10_pct")) >= -5.0
            and _safe_float(row.get("relock_rate_pct")) is not None
            and _safe_float(row.get("relock_rate_pct")) <= 0.0
            and _safe_float(row.get("entry_bbo_coverage_pct")) is not None
            and _safe_float(row.get("entry_bbo_coverage_pct")) >= 100.0
            for row in bounded_candidates
        )
    )
    bounded_checks = {
        "schema_version_invalid": bounded.get("schema_version") == 1,
        "target_date_invalid": bounded.get("target_date") == target_date,
        "producer_runtime_effect_invalid": bounded.get("runtime_effect") is False,
        "producer_order_state_invalid": bounded.get("actual_order_submitted") is False,
        "producer_broker_state_invalid": bounded.get("broker_order_forbidden") is True,
        "runtime_apply_not_allowed": bounded.get("allowed_runtime_apply") is True,
        "report_type_invalid": bounded.get("report_type")
        == "limit_down_watch_bounded_live_candidate",
        "status_not_ready": bounded.get("status") == "live_auto_apply_ready",
        "ready_candidate_missing": _safe_int(bounded.get("ready_candidate_count"))
        == len(bounded_candidates)
        > 0,
        "candidate_row_contract_invalid": bounded_candidate_rows_valid,
        "decision_authority_invalid": bounded.get("decision_authority")
        == "limit_down_live_auto_eligibility_candidate",
        "operator_approval_must_be_false": bounded.get("operator_approval_required")
        is False,
        "preopen_consumer_missing": bounded.get("preopen_consumer_implemented") is True,
        "forbidden_uses_invalid": bounded.get("forbidden_uses")
        == LIVE_AUTO_FORBIDDEN_USES,
    }
    risk_contract = (
        bounded.get("risk_contract")
        if isinstance(bounded.get("risk_contract"), dict)
        else {}
    )
    bounded_checks.update(
        {
            "risk_max_concurrent_invalid": risk_contract.get("max_concurrent_positions")
            == 1,
            "risk_max_daily_entries_invalid": risk_contract.get("max_daily_entries")
            == 1,
            "risk_quantity_owner_invalid": risk_contract.get("quantity_owner")
            == "position_sizing_dynamic_formula",
            "risk_quantity_override_present": risk_contract.get(
                "requested_quantity_override"
            )
            is None,
            "risk_scale_in_not_blocked": risk_contract.get("scale_in_allowed") is False,
            "risk_overnight_not_blocked": risk_contract.get("overnight_allowed")
            is False,
            "risk_reentry_not_blocked": risk_contract.get("same_day_reentry_allowed")
            is False,
            "risk_spread_cap_invalid": 0.0
            < (_safe_float(risk_contract.get("max_entry_spread_pct")) or 0.0)
            <= 1.5,
            "risk_unlock_confirmation_missing": risk_contract.get(
                "entry_requires_two_ordered_unlocked_ticks"
            )
            is True,
            "risk_trigger_confirmation_missing": risk_contract.get(
                "entry_requires_two_ordered_trigger_ticks"
            )
            is True,
            "risk_near_rebound_open_recovery_missing": risk_contract.get(
                "near_rebound_requires_session_open_recovery"
            )
            is True,
            "risk_near_rebound_threshold_invalid": _safe_float(
                risk_contract.get("near_rebound_min_from_low_pct")
            )
            == 1.0,
            "risk_fresh_bbo_missing": risk_contract.get(
                "entry_requires_fresh_quote_and_bbo"
            )
            is True,
            "risk_relock_cancel_missing": risk_contract.get(
                "relock_or_stale_cancels_unfilled_entry"
            )
            is True,
            "risk_normal_guards_missing": risk_contract.get(
                "normal_scalping_ai_and_submit_guards_required"
            )
            is True,
            "risk_hard_safety_priority_invalid": risk_contract.get(
                "hard_safety_priority"
            )
            == "unchanged_and_unbypassable",
        }
    )
    bounded_issues = (
        ["artifact_missing"]
        if not bounded
        else [name for name, passed in bounded_checks.items() if not passed]
    )
    bounded_valid = not bounded_issues

    return {
        "counterfactual": {
            "status": (
                "pass"
                if counterfactual_valid
                else "missing" if not counterfactual else "invalid"
            ),
            "path": str(paths["counterfactual"]),
            "source_quality_adjusted_ev_pct": counterfactual_ev,
            "sample_count": _safe_int(counterfactual.get("sample_count")),
            "issues": counterfactual_issues,
        },
        "sim_policy_catalog": {
            "status": (
                "pass"
                if sim_policy_valid
                else "missing" if not sim_policy else "invalid"
            ),
            "path": str(paths["sim_policy_catalog"]),
            "active_policy_count": _safe_int(sim_policy.get("active_policy_count")),
            "issues": sim_policy_issues,
        },
        "post_sim_attribution": {
            "status": (
                "pass" if post_sim_valid else "missing" if not post_sim else "invalid"
            ),
            "path": str(paths["post_sim_attribution"]),
            "source_quality_adjusted_ev_pct": post_sim_ev,
            "sample_count": _safe_int(post_sim.get("sample_count")),
            "issues": post_sim_issues,
        },
        "bounded_live_candidate": {
            "status": (
                "pass" if bounded_valid else "missing" if not bounded else "invalid"
            ),
            "path": str(paths["bounded_live_candidate"]),
            "ready_candidate_count": _safe_int(bounded.get("ready_candidate_count")),
            "issues": bounded_issues,
        },
        "live_conversion_approval": {
            "status": "not_required_live_auto",
            "path": str(paths["live_conversion_approval"]),
            "approved": False,
            "issues": [],
        },
    }


def _conversion_readiness(
    target_date: str,
    *,
    candidate_source_valid: bool,
    source_quality_status: str,
    event_source_valid: bool,
    rolling_observation: dict[str, Any],
    artifact_checks: dict[str, Any],
    runtime_state: dict[str, Any],
) -> dict[str, Any]:
    activation_observed = bool(
        candidate_source_valid
        or (
            runtime_state.get("target_date") == target_date
            and runtime_state.get("enabled") is True
        )
    )
    daily_source_ready = bool(
        candidate_source_valid
        and source_quality_status in {"pass", "pass_with_exclusions", "no_candidate"}
        and event_source_valid
    )
    rolling_ready = rolling_observation.get("status") == "pass"
    counterfactual_ready = artifact_checks["counterfactual"]["status"] == "pass"
    sim_policy_ready = artifact_checks["sim_policy_catalog"]["status"] == "pass"
    post_sim_ready = artifact_checks["post_sim_attribution"]["status"] == "pass"
    bounded_candidate_ready = (
        artifact_checks["bounded_live_candidate"]["status"] == "pass"
    )
    live_auto_ready = bool(daily_source_ready and bounded_candidate_ready)
    separate_preopen_apply_ready = live_auto_ready

    blockers: list[str] = []
    if not activation_observed:
        blockers.append("observer_activation_not_observed")
    if not daily_source_ready:
        blockers.append("daily_source_contract_not_ready")
    if not bounded_candidate_ready:
        blockers.append("bounded_live_candidate_contract_missing")

    decision = (
        "auto_live_policy_ready"
        if live_auto_ready
        else "keep_observing_and_build_evidence"
    )
    return {
        "schema_version": 1,
        "decision": decision,
        "observer_activation_expected": True,
        "observer_activation_observed": activation_observed,
        "daily_source_ready": daily_source_ready,
        "rolling_observation_ready": rolling_ready,
        "counterfactual_ev_ready": counterfactual_ready,
        "sim_policy_catalog_ready": sim_policy_ready,
        "post_sim_attribution_ready": post_sim_ready,
        "bounded_live_candidate_ready": bounded_candidate_ready,
        "live_conversion_review_ready": live_auto_ready,
        "operator_approval_required": False,
        "operator_approval_present": False,
        "separate_preopen_apply_ready": separate_preopen_apply_ready,
        "automatic_live_conversion_scheduled": live_auto_ready,
        "automatic_live_conversion_performed": False,
        "real_trading_ready": live_auto_ready,
        "allowed_runtime_apply": live_auto_ready,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "blockers": blockers,
        "rolling_observation": rolling_observation,
        "evidence_artifacts": artifact_checks,
    }


def _evidence_readiness(
    *,
    target_date: str,
    candidate_source: dict[str, Any],
    event_source: dict[str, Any],
    registered_code_count: int,
    snapshot_code_count: int,
    ordered_path_captured_code_count: int,
    conversion_readiness: dict[str, Any],
) -> dict[str, Any]:
    candidate_summary = _candidate_source_summary(target_date, candidate_source)
    candidates = candidate_summary["candidates"]
    source_pass_count = candidate_summary["source_pass_count"]
    candidate_source_valid = candidate_summary["candidate_source_valid"]
    source_quality_status = candidate_summary["source_quality_status"]
    event_source_required = candidate_summary["event_source_required"]
    event_source_valid = (
        bool(event_source.get("valid")) if event_source_required else True
    )
    blockers = []
    if source_quality_status not in {"pass", "pass_with_exclusions", "no_candidate"}:
        blockers.append(f"candidate_source_quality_{source_quality_status}")
    if not event_source_valid:
        blockers.append("ordered_intraday_event_source_invalid")
    if snapshot_code_count <= 0:
        blockers.append("ordered_intraday_path_sample_missing")
    if ordered_path_captured_code_count <= 0:
        blockers.append("ordered_intraday_path_capture_missing")
    elif ordered_path_captured_code_count < registered_code_count:
        blockers.append("ordered_intraday_path_capture_incomplete")
    blockers.extend(conversion_readiness.get("blockers") or [])
    blockers = list(dict.fromkeys(str(item) for item in blockers if str(item)))
    next_evidence_by_blocker = {
        "observer_activation_not_observed": "target_date_candidate_source_or_enabled_runtime_state",
        "daily_source_contract_not_ready": "valid_target_date_candidate_and_event_source_contract",
        "ordered_intraday_event_source_invalid": "valid_ordered_intraday_event_source",
        "ordered_intraday_path_sample_missing": "ordered_unlock_relock_path_capture",
        "ordered_intraday_path_capture_missing": "ordered_unlock_relock_path_capture",
        "ordered_intraday_path_capture_incomplete": "ordered_unlock_relock_path_capture",
        "multi_day_cohort_sample_floor_not_established": "multi_day_cohort_and_price_band_sample_floor",
        "counterfactual_entry_exit_labels_missing": "counterfactual_entry_exit_labels_with_mfe_mae",
        "clean_baseline_rolling_ev_missing": "clean_baseline_rolling_source_quality_adjusted_ev_pct",
        "sim_policy_catalog_handoff_missing": "sim_policy_catalog_and_preopen_handoff",
        "post_sim_attribution_missing": "post_sim_attribution",
        "bounded_live_candidate_contract_missing": "bounded_live_candidate_with_locked_risk_contract",
        "separate_live_conversion_approval_missing": "separate_operator_live_conversion_approval_and_rollback",
    }
    required_next_evidence = list(
        dict.fromkeys(
            next_evidence_by_blocker[item]
            for item in blockers
            if item in next_evidence_by_blocker
        )
    )
    return {
        "stage": "source_observation",
        "decision": "collect_source_and_auto_promote_eligible_type",
        "source_quality_status": source_quality_status,
        "candidate_source_valid": candidate_source_valid,
        "candidate_source_report_status": candidate_source.get("status"),
        "event_source_required": event_source_required,
        "event_source_valid": event_source_valid,
        "event_source": event_source,
        "candidate_count": len(candidates),
        "source_pass_count": source_pass_count,
        "registered_code_count": registered_code_count,
        "snapshot_code_count": snapshot_code_count,
        "ordered_path_captured_code_count": ordered_path_captured_code_count,
        "sim_candidate_ready": False,
        "real_trading_ready": conversion_readiness.get("real_trading_ready", False),
        "blockers": blockers,
        "required_next_evidence": required_next_evidence,
        "conversion_decision": conversion_readiness.get("decision"),
        "live_conversion_review_ready": conversion_readiness.get(
            "live_conversion_review_ready", False
        ),
        "operator_approval_required": conversion_readiness.get(
            "operator_approval_required", False
        ),
        "bounded_live_candidate_ready": conversion_readiness.get(
            "bounded_live_candidate_ready", False
        ),
        "separate_preopen_apply_ready": conversion_readiness.get(
            "separate_preopen_apply_ready", False
        ),
    }


def build_report(
    target_date: str,
    *,
    event_path: Path | None = None,
    candidate_path: Path | None = None,
    history_dir: Path | None = None,
    conversion_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    event_path = event_path or (
        DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    )
    candidate_path = candidate_path or (
        CANDIDATE_DIR / f"limit_down_watch_candidate_source_{target_date}.json"
    )
    candidate_source = _load_json(candidate_path)
    candidate_summary = _candidate_source_summary(target_date, candidate_source)
    if candidate_summary["event_source_required"]:
        events, event_source = _load_events(event_path)
    else:
        events = []
        event_source = _event_source_not_scanned(
            event_path,
            reason=str(candidate_summary["source_quality_status"]),
        )
    snapshots: dict[str, dict[str, Any]] = {}
    quote_snapshots: dict[str, dict[str, Any]] = {}
    transitions: dict[str, list[str]] = defaultdict(list)
    registered_meta: dict[str, dict[str, Any]] = {}
    for event in events:
        code = str(event.get("stock_code") or "").strip()
        stage = str(event.get("stage") or "")
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if stage == "limit_down_watch_registered" and code:
            registered_meta[code] = {
                "cohort": fields.get("cohort"),
                "price_band": fields.get("price_band"),
            }
        elif stage == "limit_down_watch_state_transition" and code:
            transitions[code].append(str(fields.get("phase") or ""))
        elif stage == "limit_down_watch_snapshot" and code:
            snapshots[code] = fields
        elif stage == "limit_down_watch_quote_snapshot" and code:
            quote_snapshots[code] = fields

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    report_codes = sorted(set(registered_meta) | set(snapshots) | set(quote_snapshots))
    ordered_phases = {
        "LIMIT_LOCKED",
        "UNLOCKED",
        "RELOCKED",
        "UNLOCKED_AGAIN",
        "NEAR_REBOUND_OBSERVING",
    }
    for code in report_codes:
        fields = (
            snapshots.get(code)
            or quote_snapshots.get(code)
            or registered_meta.get(code)
            or {}
        )
        key = (
            str(fields.get("cohort") or "unknown"),
            str(fields.get("price_band") or "unknown"),
        )
        row = grouped.setdefault(
            key,
            {
                "cohort": key[0],
                "price_band": key[1],
                "registered_codes": 0,
                "snapshot_codes": 0,
                "quote_snapshot_codes": 0,
                "market_data_observed_codes": 0,
                "observed_codes": 0,
                "unlocked_codes": 0,
                "relocked_codes": 0,
                "ordered_path_captured_codes": 0,
                "_ranges": [],
                "_highs": [],
                "_lows": [],
            },
        )
        if code in registered_meta:
            row["registered_codes"] += 1
        if code in snapshots:
            row["snapshot_codes"] += 1
            row["observed_codes"] += 1
        if code in quote_snapshots:
            row["quote_snapshot_codes"] += 1
        if code in snapshots or code in quote_snapshots:
            row["market_data_observed_codes"] += 1
        phases = transitions.get(code, [])
        unlocked = any(phase in {"UNLOCKED", "UNLOCKED_AGAIN"} for phase in phases)
        relocked = "RELOCKED" in phases
        if unlocked:
            row["unlocked_codes"] += 1
        if relocked:
            row["relocked_codes"] += 1
        if any(phase in ordered_phases for phase in phases):
            row["ordered_path_captured_codes"] += 1
        intraday_range = _safe_float(fields.get("low_to_high_range_pct"))
        high_vs_close = _safe_float(fields.get("high_vs_limit_down_close_pct"))
        low_vs_close = _safe_float(fields.get("low_vs_limit_down_close_pct"))
        if intraday_range is not None:
            row["_ranges"].append(intraday_range)
        if high_vs_close is not None:
            row["_highs"].append(high_vs_close)
        if low_vs_close is not None:
            row["_lows"].append(low_vs_close)

    groups = []
    for row in grouped.values():
        count = max(row["registered_codes"], row["snapshot_codes"])
        ranges = row.pop("_ranges")
        highs = row.pop("_highs")
        lows = row.pop("_lows")
        row.update(
            {
                "unlock_rate_pct": (
                    round(row["unlocked_codes"] / count * 100.0, 4) if count else None
                ),
                "relock_rate_pct": (
                    round(row["relocked_codes"] / count * 100.0, 4) if count else None
                ),
                "ordered_intraday_path_capture_rate": (
                    round(row["ordered_path_captured_codes"] / count * 100.0, 4)
                    if count
                    else None
                ),
                "avg_low_to_high_range_pct": (
                    round(sum(ranges) / len(ranges), 6) if ranges else None
                ),
                "avg_high_vs_limit_down_close_pct": (
                    round(sum(highs) / len(highs), 6) if highs else None
                ),
                "avg_low_vs_limit_down_close_pct": (
                    round(sum(lows) / len(lows), 6) if lows else None
                ),
            }
        )
        groups.append(row)
    groups.sort(key=lambda row: (row["cohort"], row["price_band"]))
    ordered_path_captured_code_count = sum(
        int(row["ordered_path_captured_codes"]) for row in groups
    )
    event_source_valid = (
        bool(event_source.get("valid"))
        if candidate_summary["event_source_required"]
        else True
    )
    current_contract_readiness = {
        "candidate_source_valid": candidate_summary["candidate_source_valid"],
        "event_source_valid": event_source_valid,
    }
    rolling_observation = _rolling_observation_evidence(
        target_date,
        current_status=(
            "source_blocked"
            if (
                not candidate_summary["candidate_source_valid"]
                or not event_source_valid
                or candidate_summary["source_quality_status"]
                not in {"pass", "pass_with_exclusions", "no_candidate"}
            )
            else "pass" if (snapshots or quote_snapshots) else "no_observation"
        ),
        current_groups=groups,
        current_readiness=current_contract_readiness,
        history_dir=history_dir or OUTPUT_DIR,
    )
    resolved_conversion_paths = conversion_paths or _artifact_path_map(target_date)
    required_conversion_paths = set(_artifact_path_map(target_date))
    if set(resolved_conversion_paths) != required_conversion_paths:
        raise ValueError(
            "conversion_paths must provide runtime_state, counterfactual, "
            "sim_policy_catalog, post_sim_attribution, bounded_live_candidate, "
            "and live_conversion_approval"
        )
    runtime_state = _load_json(resolved_conversion_paths["runtime_state"])
    artifact_checks = _conversion_artifact_checks(
        target_date, resolved_conversion_paths
    )
    conversion_readiness = _conversion_readiness(
        target_date,
        candidate_source_valid=candidate_summary["candidate_source_valid"],
        source_quality_status=candidate_summary["source_quality_status"],
        event_source_valid=event_source_valid,
        rolling_observation=rolling_observation,
        artifact_checks=artifact_checks,
        runtime_state=runtime_state,
    )
    evidence_readiness = _evidence_readiness(
        target_date=target_date,
        candidate_source=candidate_source,
        event_source=event_source,
        registered_code_count=len(registered_meta),
        snapshot_code_count=len(snapshots),
        ordered_path_captured_code_count=ordered_path_captured_code_count,
        conversion_readiness=conversion_readiness,
    )
    source_blocked = (
        not evidence_readiness["candidate_source_valid"]
        or not evidence_readiness["event_source_valid"]
        or evidence_readiness["source_quality_status"]
        not in {"pass", "pass_with_exclusions", "no_candidate"}
    )
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": (
            "source_blocked"
            if source_blocked
            else "pass" if (snapshots or quote_snapshots) else "no_observation"
        ),
        "registered_code_count": len(registered_meta),
        "snapshot_code_count": len(snapshots),
        "quote_snapshot_code_count": len(quote_snapshots),
        "market_data_observed_code_count": len(set(snapshots) | set(quote_snapshots)),
        "group_count": len(groups),
        "groups": groups,
        "candidate_source_path": str(candidate_path),
        "event_source_path": str(event_path),
        "evidence_readiness": evidence_readiness,
        "conversion_readiness": conversion_readiness,
        "observer_activation": {
            "policy": "persistent_daily_source_observation",
            "expected_enabled": True,
            "observed_enabled": conversion_readiness["observer_activation_observed"],
            "runtime_state_path": str(resolved_conversion_paths["runtime_state"]),
            "runtime_state_enabled": runtime_state.get("enabled"),
        },
        **CONTRACT,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    readiness = (
        payload.get("evidence_readiness")
        if isinstance(payload.get("evidence_readiness"), dict)
        else {}
    )
    conversion = (
        payload.get("conversion_readiness")
        if isinstance(payload.get("conversion_readiness"), dict)
        else {}
    )
    rolling = (
        conversion.get("rolling_observation")
        if isinstance(conversion.get("rolling_observation"), dict)
        else {}
    )
    evidence_artifacts = (
        conversion.get("evidence_artifacts")
        if isinstance(conversion.get("evidence_artifacts"), dict)
        else {}
    )
    lines = [
        f"# Limit-Down Watch Report — {payload.get('target_date')}",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- status: `{payload.get('status')}`",
        f"- registered_code_count: `{payload.get('registered_code_count')}`",
        f"- snapshot_code_count: `{payload.get('snapshot_code_count')}`",
        f"- quote_snapshot_code_count: `{payload.get('quote_snapshot_code_count')}`",
        (
            "- market_data_observed_code_count: "
            f"`{payload.get('market_data_observed_code_count')}`"
        ),
        f"- event_source_required: `{readiness.get('event_source_required')}`",
        (
            "- event_source_read_mode: "
            f"`{(readiness.get('event_source') or {}).get('read_mode')}`"
        ),
        (
            "- ordered_intraday_path_capture: "
            f"`{readiness.get('ordered_path_captured_code_count', 0)}`"
        ),
        f"- sim_candidate_ready: `{readiness.get('sim_candidate_ready')}`",
        f"- real_trading_ready: `{readiness.get('real_trading_ready')}`",
        f"- decision: `{readiness.get('decision')}`",
        f"- conversion_decision: `{conversion.get('decision')}`",
        (
            "- observer_activation_observed: "
            f"`{conversion.get('observer_activation_observed')}`"
        ),
        (
            "- live_conversion_review_ready: "
            f"`{conversion.get('live_conversion_review_ready')}`"
        ),
        (
            "- operator_approval_required: "
            f"`{conversion.get('operator_approval_required')}`"
        ),
        (
            "- bounded_live_candidate_ready: "
            f"`{conversion.get('bounded_live_candidate_ready')}`"
        ),
        (
            "- separate_preopen_apply_ready: "
            f"`{conversion.get('separate_preopen_apply_ready')}`"
        ),
        "- automatic_live_conversion_performed: `False`",
        "",
        "## Blockers",
        "",
    ]
    blockers = (
        readiness.get("blockers") if isinstance(readiness.get("blockers"), list) else []
    )
    lines.extend(f"- `{item}`" for item in blockers)
    lines.extend(
        [
            "",
            "## Rolling Conversion Evidence",
            "",
            f"- status: `{rolling.get('status')}`",
            f"- observation_day_count: `{rolling.get('observation_day_count', 0)}`",
            (
                "- ordered_path_captured_code_count: "
                f"`{rolling.get('ordered_path_captured_code_count', 0)}`"
            ),
            (
                "- ordered_intraday_path_capture_rate: "
                f"`{rolling.get('ordered_intraday_path_capture_rate')}`"
            ),
            "",
            "## Conversion Artifact Checks",
            "",
            "| artifact | status | issues |",
            "| --- | --- | --- |",
        ]
    )
    for artifact_name, artifact in evidence_artifacts.items():
        artifact = artifact if isinstance(artifact, dict) else {}
        issues = (
            artifact.get("issues") if isinstance(artifact.get("issues"), list) else []
        )
        lines.append(
            f"| {artifact_name} | {artifact.get('status')} | "
            f"{', '.join(str(item) for item in issues) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Cohort / Price Band",
            "",
            "| cohort | price_band | registered | trade_snapshots | quote_snapshots | market_data_observed | unlocked | relocked | ordered_trade_path_capture_rate |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    groups = payload.get("groups") if isinstance(payload.get("groups"), list) else []
    for row in groups:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {cohort} | {price_band} | {registered} | {snapshots} | "
            "{quote_snapshots} | {market_data_observed} | {unlocked} | "
            "{relocked} | {capture} |".format(
                cohort=row.get("cohort") or "unknown",
                price_band=row.get("price_band") or "unknown",
                registered=row.get("registered_codes") or 0,
                snapshots=row.get("snapshot_codes") or 0,
                quote_snapshots=row.get("quote_snapshot_codes") or 0,
                market_data_observed=row.get("market_data_observed_codes") or 0,
                unlocked=row.get("unlocked_codes") or 0,
                relocked=row.get("relocked_codes") or 0,
                capture=row.get("ordered_intraday_path_capture_rate"),
            )
        )
    lines.extend(
        [
            "",
            "## Contract",
            "",
            f"- decision_authority: `{payload.get('decision_authority')}`",
            f"- runtime_effect: `{payload.get('runtime_effect')}`",
            f"- actual_order_submitted: `{payload.get('actual_order_submitted')}`",
            f"- broker_order_forbidden: `{payload.get('broker_order_forbidden')}`",
            f"- allowed_sim_apply: `{payload.get('allowed_sim_apply')}`",
            f"- allowed_runtime_apply: `{payload.get('allowed_runtime_apply')}`",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def write_report(target_date: str) -> tuple[Path, Path]:
    # The research producer validates and streams the same target-date source
    # contract. Run it first, then build the final report once with all research
    # artifacts visible; this avoids a redundant third full JSONL scan.
    from src.engine.monitoring.limit_down_watch_research import (
        produce_research_artifacts,
    )

    produce_research_artifacts(target_date)
    payload = build_report(target_date)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUTPUT_DIR / f"limit_down_watch_{target_date}"
    json_path = base.with_suffix(".json")
    markdown_path = base.with_suffix(".md")
    _atomic_write_text(
        json_path,
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
    )
    _atomic_write_text(markdown_path, _render_markdown(payload))
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        json_path, markdown_path = write_report(args.target_date)
        print(json_path)
        print(markdown_path)
    else:
        payload = build_report(args.target_date)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
