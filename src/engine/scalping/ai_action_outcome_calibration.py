"""Cumulative exact-trace action/outcome calibration and OFI attribution audit.

This producer replaces the legacy WATCHING numeric-score smoothing diagnostic.
It never changes a live score or action.  It accumulates mature paired replay
outcomes keyed by exact decision trace, then reports action transitions, EV,
error taxonomy, and OFI runtime postprocessor attribution coverage.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

KST = ZoneInfo("Asia/Seoul")
CLEAN_BASELINE_DATE = "2026-06-05"
SCHEMA = "ai_decision_action_outcome_calibration_v1"
POLICY_VERSION = "exact_decision_trace_cumulative_action_outcome_v3"
PROBE_RISK_GATE_VERSION = "bounded_probe_recovery_risk_v1"
MAXIMUM_BOUNDED_PROBE_LOSS_PCT = 2.0
SEVERE_TAIL_ADVERSE_PCT = -2.0
OFI_LEDGER_SCHEMA = "ofi_exact_trace_action_outcome_calibration_v2"
REPORT_SUBDIR = "ai_decision_action_outcome_calibration"
PAIRED_SUBDIR = "ai_prompt_detailed_paired_replay"
OFI_STAGES = {
    "entry_ai_price_ofi_skip_demoted",
    "holding_flow_ofi_smoothing_applied",
}
EXPOSURE_ACTIONS = {
    "BUY",
    "ADD",
    "CONTINUE",
    "HOLD",
    "HOLD_OVERNIGHT",
    "USE_DEFENSIVE",
    "USE_REFERENCE",
    "IMPROVE_LIMIT",
}
NO_EXPOSURE_ACTIONS = {
    "DROP",
    "WAIT",
    "NO_ADD",
    "STOP",
    "EXIT",
    "SELL",
    "SELL_TODAY",
    "EXIT_BEFORE_CLOSE",
    "SKIP",
}
OFFLINE_CONTRACT = {
    "metric_role": "ai_decision_action_outcome_calibration",
    "decision_authority": "offline_prompt_calibration_only_no_runtime_change",
    "window_policy": "clean_baseline_through_target_date_exact_trace_mature_outcome",
    "sample_floor": "one_eligible_exact_trace_updates_cumulative_learning",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_trace_same_venue_session_mature_outcome",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "standalone_live_action_or_score_mutation",
        "prompt_promotion_without_reviewed_paired_replay",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_hard_safety_bypass",
        "counterfactual_realized_pnl_merge",
        "bot_restart",
    ],
}

PROMPT_REVIEW_GATE = {
    "minimum_exact_trace_count": 30,
    "minimum_unique_symbol_count": 10,
    "minimum_independent_source_date_count": 2,
    "minimum_candidate_exposure_count": 5,
    "minimum_candidate_exposure_rate_pct": 2.0,
    "maximum_false_drop_rate_pct": 10.0,
    "maximum_schema_rejection_rate_pct": 1.0,
    "require_positive_candidate_ev": True,
    "require_positive_candidate_exposure_ev": True,
    "require_positive_probe_cost_adjusted_ev": True,
    "require_positive_ev_delta": True,
    "maximum_bounded_probe_loss_pct": MAXIMUM_BOUNDED_PROBE_LOSS_PCT,
    "require_severe_tail_adverse_not_increased": True,
    "require_drawdown_recovery_capture_not_decreased": True,
}
DOWNSTREAM_RUNTIME_GUARDS = [
    "separate_runtime_apply_candidate_required",
    "one_share_probe_first",
    "fresh_quote_and_stale_conflict_guard",
    "broker_account_order_quantity_cooldown_guards",
    "post_probe_direction_and_price_resolver",
    "hard_protect_emergency_exit_guards",
    "post_apply_action_outcome_attribution",
]


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def report_path(target_date: str, report_root: Path = Path("data/report")) -> Path:
    return (
        report_root
        / REPORT_SUBDIR
        / f"ai_decision_action_outcome_calibration_{target_date}.json"
    )


def _report_date(path: Path, report: dict[str, Any]) -> str:
    target_date = str(report.get("target_date") or "")
    if len(target_date) == 10:
        return target_date
    name = path.name
    for index in range(max(0, len(name) - 10)):
        value = name[index : index + 10]
        if value[4:5] == "-" and value[7:8] == "-":
            return value
    return ""


def _candidate_version(report: dict[str, Any], path: Path) -> str:
    cumulative = report.get("cumulative_learning")
    if isinstance(cumulative, dict) and cumulative.get("candidate_prompt_version"):
        return str(cumulative["candidate_prompt_version"])
    for request in report.get("requests") or []:
        if not isinstance(request, dict):
            continue
        candidate = request.get("candidate")
        if isinstance(candidate, dict) and candidate.get("prompt_version"):
            return str(candidate["prompt_version"])
    suffix = path.stem.split("_202", 1)
    return suffix[-1] if len(suffix) > 1 else "unknown"


def _transition_rows(
    paired_dir: Path,
    *,
    target_date: str,
) -> tuple[dict[str, dict[str, dict[str, Any]]], list[dict[str, Any]]]:
    rows_by_version: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    source_reports: list[dict[str, Any]] = []
    for path in sorted(paired_dir.glob("ai_prompt_detailed_paired_replay_*.json")):
        report = _load_json(path)
        source_date = _report_date(path, report)
        if (
            not source_date
            or source_date < CLEAN_BASELINE_DATE
            or source_date > target_date
            or report.get("runtime_effect") is not False
            or (
                isinstance(report.get("model_comparison_contract"), dict)
                and report["model_comparison_contract"].get("enabled") is True
            )
        ):
            continue
        candidate_version = _candidate_version(report, path)
        comparisons = [
            row
            for row in report.get("paired_comparisons") or []
            if isinstance(row, dict) and row.get("decision_trace_id")
        ]
        for row in comparisons:
            trace_id = str(row["decision_trace_id"])
            enriched = dict(row)
            enriched["source_date"] = source_date
            enriched["candidate_prompt_version"] = candidate_version
            rows_by_version[candidate_version][trace_id] = enriched
        source_reports.append(
            {
                "path": str(path),
                "source_date": source_date,
                "candidate_prompt_version": candidate_version,
                "paired_comparable_count": len(comparisons),
                "schema_rejected_count": int(
                    _number(report.get("schema_rejected_count")) or 0
                ),
                "provider_failed_count": int(
                    _number(report.get("provider_failed_count")) or 0
                ),
                "provider_none_count": int(
                    _number(report.get("candidate_provider_none_count")) or 0
                ),
                "generated_at": report.get("generated_at"),
            }
        )
    return rows_by_version, source_reports


def _transition_summary(
    candidate_version: str,
    rows: Iterable[dict[str, Any]],
    source_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    values = list(rows)
    raw_value_pairs: list[tuple[float, float]] = []
    for row in values:
        control_value = _number(row.get("control_decision_value_pct"))
        candidate_raw_value = _number(row.get("candidate_decision_value_pct"))
        if (
            candidate_raw_value is None
            and row.get("candidate_execution_cost_contract_applied") is not True
        ):
            candidate_raw_value = _number(
                row.get("candidate_primary_decision_value_pct")
            )
        if control_value is not None and candidate_raw_value is not None:
            raw_value_pairs.append((control_value, candidate_raw_value))
    control_raw_values = [control for control, _ in raw_value_pairs]
    candidate_raw_values = [candidate for _, candidate in raw_value_pairs]
    candidate_primary_values = [
        value
        for row in values
        if (
            value := _number(
                row.get("candidate_primary_decision_value_pct")
                if row.get("candidate_primary_decision_value_pct") is not None
                else row.get("candidate_decision_value_pct")
            )
        )
        is not None
    ]
    delta_values = [
        value for row in values if (value := _number(row.get("delta_pct"))) is not None
    ]
    exposure_rows = [
        row
        for row in values
        if str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
    ]
    candidate_exposure_values = [
        value
        for row in exposure_rows
        if (
            value := _number(
                row.get("candidate_primary_decision_value_pct")
                if row.get("candidate_primary_decision_value_pct") is not None
                else row.get("candidate_decision_value_pct")
            )
        )
        is not None
    ]
    candidate_probe_losses = []
    candidate_probe_risk_missing_count = 0
    for row in exposure_rows:
        probe_loss = _number(row.get("candidate_probe_worst_loss_pct"))
        if probe_loss is None:
            probe_loss = _number(row.get("probe_worst_loss_pct"))
        if probe_loss is None:
            outcome_mae = _number(row.get("outcome_mae_pct"))
            if outcome_mae is not None:
                probe_loss = min(0.0, outcome_mae)
        if probe_loss is None:
            candidate_probe_risk_missing_count += 1
            continue
        candidate_probe_losses.append(probe_loss)
    control_severe_tail = sum(
        row.get("control_probe_severe_tail_exposure") is True
        or (
            str(row.get("control_action") or "").upper() in EXPOSURE_ACTIONS
            and (_number(row.get("probe_worst_loss_pct")) or 0.0)
            < SEVERE_TAIL_ADVERSE_PCT
        )
        for row in values
    )
    candidate_severe_tail = sum(
        row.get("candidate_probe_severe_tail_exposure") is True
        or (
            str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
            and (_number(row.get("probe_worst_loss_pct")) or 0.0)
            < SEVERE_TAIL_ADVERSE_PCT
        )
        for row in values
    )
    control_recovery_capture = sum(
        row.get("control_drawdown_recovery_captured") is True
        or (
            str(row.get("control_action") or "").upper() in EXPOSURE_ACTIONS
            and row.get("profit_opportunity_sequence")
            == "drawdown_then_profit_recovery"
        )
        for row in values
    )
    candidate_recovery_capture = sum(
        row.get("candidate_drawdown_recovery_captured") is True
        or (
            str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
            and row.get("profit_opportunity_sequence")
            == "drawdown_then_profit_recovery"
        )
        for row in values
    )
    control_adverse = sum(
        str(row.get("first_hit") or "") == "adverse"
        and str(row.get("control_action") or "").upper() in EXPOSURE_ACTIONS
        for row in values
    )
    candidate_adverse = sum(
        str(row.get("first_hit") or "") == "adverse"
        and str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
        for row in values
    )
    transitions = Counter(
        f"{str(row.get('control_action') or 'UNKNOWN').upper()}->"
        f"{str(row.get('candidate_action') or 'UNKNOWN').upper()}"
        for row in values
    )
    reports = [
        row
        for row in source_reports
        if row["candidate_prompt_version"] == candidate_version
    ]
    schema_rejected_count = sum(row["schema_rejected_count"] for row in reports)
    schema_evaluated_count = len(values) + schema_rejected_count
    schema_rejection_rate_pct = (
        (schema_rejected_count / schema_evaluated_count) * 100.0
        if schema_evaluated_count
        else 0.0
    )
    provider_failed_count = sum(row["provider_failed_count"] for row in reports)
    provider_none_count = sum(row["provider_none_count"] for row in reports)
    primary_ev_delta = fmean(delta_values) if delta_values else None
    source_quality_ev_delta = (
        fmean(candidate - control for control, candidate in raw_value_pairs)
        if raw_value_pairs
        else None
    )
    adverse_not_increased = candidate_adverse <= control_adverse
    probe_loss_budget_pass = (
        bool(exposure_rows)
        and candidate_probe_risk_missing_count == 0
        and len(candidate_probe_losses) == len(exposure_rows)
        and all(
            loss >= -MAXIMUM_BOUNDED_PROBE_LOSS_PCT for loss in candidate_probe_losses
        )
    )
    severe_tail_not_increased = candidate_severe_tail <= control_severe_tail
    recovery_capture_not_decreased = (
        candidate_recovery_capture >= control_recovery_capture
    )
    unique_symbol_count = len(
        {str(row.get("stock_code") or "") for row in values if row.get("stock_code")}
    )
    source_dates = sorted(
        {str(row.get("source_date")) for row in values if row.get("source_date")}
    )
    candidate_ev = fmean(candidate_primary_values) if candidate_primary_values else None
    candidate_exposure_ev = (
        fmean(candidate_exposure_values) if candidate_exposure_values else None
    )
    probe_cost_contract_complete = bool(exposure_rows) and all(
        row.get("candidate_execution_cost_contract_applied") is True
        for row in exposure_rows
    )
    candidate_probe_cost_adjusted_ev = (
        candidate_exposure_ev if probe_cost_contract_complete else None
    )
    candidate_exposure_rate_pct = (
        (len(exposure_rows) / len(values)) * 100.0 if values else 0.0
    )
    false_drop_count = sum(
        "false_drop"
        in {str(error) for error in row.get("candidate_error_taxonomy") or []}
        for row in values
    )
    false_drop_rate_pct = (false_drop_count / len(values)) * 100.0 if values else 0.0
    review_gate_checks = {
        "exact_trace_floor": len(values)
        >= PROMPT_REVIEW_GATE["minimum_exact_trace_count"],
        "unique_symbol_floor": unique_symbol_count
        >= PROMPT_REVIEW_GATE["minimum_unique_symbol_count"],
        "independent_source_date_floor": len(source_dates)
        >= PROMPT_REVIEW_GATE["minimum_independent_source_date_count"],
        "candidate_exposure_floor": len(exposure_rows)
        >= PROMPT_REVIEW_GATE["minimum_candidate_exposure_count"],
        "candidate_exposure_rate_floor": candidate_exposure_rate_pct
        >= PROMPT_REVIEW_GATE["minimum_candidate_exposure_rate_pct"],
        "false_drop_rate_ceiling": false_drop_rate_pct
        <= PROMPT_REVIEW_GATE["maximum_false_drop_rate_pct"],
        "positive_candidate_ev": candidate_ev is not None and candidate_ev > 0,
        "positive_candidate_exposure_ev": candidate_exposure_ev is not None
        and candidate_exposure_ev > 0,
        "positive_probe_cost_adjusted_ev": (
            candidate_probe_cost_adjusted_ev is not None
            and candidate_probe_cost_adjusted_ev > 0
        ),
        "positive_ev_delta": primary_ev_delta is not None and primary_ev_delta > 0,
        "probe_loss_budget_within_cap": probe_loss_budget_pass,
        "severe_tail_adverse_not_increased": severe_tail_not_increased,
        "drawdown_recovery_capture_not_decreased": (recovery_capture_not_decreased),
        "schema_rejection_rate_ceiling": schema_rejection_rate_pct
        <= PROMPT_REVIEW_GATE["maximum_schema_rejection_rate_pct"],
        "provider_transport_clean": provider_failed_count == 0
        and provider_none_count == 0,
    }
    review_ready = bool(values and all(review_gate_checks.values()))
    review_gate_blockers = [
        name for name, passed in review_gate_checks.items() if not passed
    ]
    return {
        "candidate_prompt_version": candidate_version,
        "exact_trace_count": len(values),
        "unique_symbol_count": unique_symbol_count,
        "source_date_count": len(source_dates),
        "source_dates": source_dates,
        "candidate_exposure_count": len(exposure_rows),
        "candidate_exposure_rate_pct": candidate_exposure_rate_pct,
        "candidate_exposure_ev_pct": candidate_exposure_ev,
        "false_drop_count": false_drop_count,
        "false_drop_rate_pct": false_drop_rate_pct,
        "control_source_quality_adjusted_ev_pct": (
            fmean(control_raw_values) if control_raw_values else None
        ),
        "candidate_source_quality_adjusted_ev_pct": (
            fmean(candidate_raw_values) if candidate_raw_values else None
        ),
        "candidate_primary_decision_ev_pct": (
            fmean(candidate_primary_values) if candidate_primary_values else None
        ),
        "source_quality_adjusted_ev_delta_pct": source_quality_ev_delta,
        "candidate_primary_decision_ev_delta_pct": primary_ev_delta,
        "candidate_primary_decision_metric": (
            "candidate_execution_cost_adjusted_ev_pct"
            if any(
                row.get("candidate_execution_cost_contract_applied") is True
                for row in values
            )
            else "source_quality_adjusted_ev_pct"
        ),
        "control_adverse_first_exposure_count": control_adverse,
        "candidate_adverse_first_exposure_count": candidate_adverse,
        "probe_risk_gate_version": PROBE_RISK_GATE_VERSION,
        "candidate_probe_cost_adjusted_ev_pct": candidate_probe_cost_adjusted_ev,
        "probe_cost_contract_complete": probe_cost_contract_complete,
        "candidate_probe_loss_budget_breach_count": sum(
            loss < -MAXIMUM_BOUNDED_PROBE_LOSS_PCT for loss in candidate_probe_losses
        ),
        "candidate_probe_risk_missing_count": candidate_probe_risk_missing_count,
        "control_probe_severe_tail_exposure_count": control_severe_tail,
        "candidate_probe_severe_tail_exposure_count": candidate_severe_tail,
        "control_drawdown_recovery_capture_count": control_recovery_capture,
        "candidate_drawdown_recovery_capture_count": candidate_recovery_capture,
        "candidate_error_taxonomy_counts": dict(
            Counter(
                error
                for row in values
                for error in row.get("candidate_error_taxonomy") or []
            )
        ),
        "control_action_counts": dict(
            Counter(str(row.get("control_action") or "UNKNOWN") for row in values)
        ),
        "candidate_action_counts": dict(
            Counter(str(row.get("candidate_action") or "UNKNOWN") for row in values)
        ),
        "action_transition_counts": dict(transitions),
        "schema_rejected_count": schema_rejected_count,
        "schema_evaluated_count": schema_evaluated_count,
        "schema_rejection_rate_pct": schema_rejection_rate_pct,
        "provider_failed_count": provider_failed_count,
        "provider_none_count": provider_none_count,
        "adverse_first_exposure_not_increased": adverse_not_increased,
        "adverse_first_role": "diagnostic_not_absolute_quality_veto",
        "review_ready_for_prompt_candidate": review_ready,
        "prompt_review_gate": {
            "policy": PROMPT_REVIEW_GATE,
            "checks": review_gate_checks,
            "blockers": review_gate_blockers,
            "alignment": ("bounded_opportunity_exploration_with_downstream_safety"),
            "required_runtime_conversion_guards": DOWNSTREAM_RUNTIME_GUARDS,
        },
        "learning_update_floor": {
            "required_exact_trace_rows": 1,
            "observed_exact_trace_rows": len(values),
            "pass": bool(values),
            "role": "cumulative_learning_update_only",
        },
        "runtime_apply_authority": False,
    }


def _fields(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("fields")
    return value if isinstance(value, dict) else {}


def build_ofi_smoothing_audit(
    pipeline_path: Path,
) -> dict[str, Any]:
    if not pipeline_path.exists():
        return {
            "status": "source_unavailable",
            "source_path": str(pipeline_path),
            "event_count": 0,
            "runtime_action_change_count": 0,
            "exact_trace_linked_count": 0,
        }
    events: list[dict[str, Any]] = []
    for event in iter_jsonl(pipeline_path):
        stage = str(event.get("stage") or "")
        if stage in OFI_STAGES:
            events.append(event)
    action_counter: Counter[str] = Counter()
    trace_linked = 0
    snapshot_linked = 0
    explicit_contract = 0
    runtime_action_changes = 0
    usable_count = 0
    regime_counter: Counter[str] = Counter()
    for event in events:
        stage = str(event.get("stage") or "")
        fields = _fields(event)
        smoothing_action = str(
            fields.get("smoothing_action")
            or ("DEMOTE_SKIP" if stage == "entry_ai_price_ofi_skip_demoted" else "")
            or "UNKNOWN"
        )
        action_counter[f"{stage}:{smoothing_action}"] += 1
        raw_action = str(
            fields.get("raw_flow_action") or fields.get("raw_action") or ""
        )
        final_action = str(
            fields.get("final_flow_action") or fields.get("final_action") or ""
        )
        if raw_action and final_action and raw_action != final_action:
            runtime_action_changes += 1
        if fields.get("ai_decision_trace_id") not in (None, "", "-"):
            trace_linked += 1
        if fields.get("ai_input_snapshot_id") not in (None, "", "-"):
            snapshot_linked += 1
        if fields.get("metric_role") and fields.get("decision_authority"):
            explicit_contract += 1
        usable = fields.get("holding_flow_ofi_usable")
        if usable is None:
            usable = fields.get("entry_ai_price_ofi_usable")
        if usable is True or str(usable).lower() == "true":
            usable_count += 1
        regime = str(
            fields.get("holding_flow_ofi_regime")
            or fields.get("entry_ai_price_ofi_regime")
            or ""
        )
        if regime:
            regime_counter[regime] += 1
    defects: list[str] = []
    if events and trace_linked < len(events):
        defects.append("exact_decision_trace_attribution_incomplete")
    if events and snapshot_linked < len(events):
        defects.append("exact_snapshot_attribution_incomplete")
    if events and explicit_contract < len(events):
        defects.append("runtime_authority_contract_incomplete")
    if events and usable_count == 0:
        defects.append("ofi_usability_provenance_missing")
    return {
        "status": "pass" if not defects else "warning",
        "source_path": str(pipeline_path),
        "event_count": len(events),
        "action_counts": dict(action_counter),
        "runtime_action_change_count": runtime_action_changes,
        "exact_trace_linked_count": trace_linked,
        "exact_snapshot_linked_count": snapshot_linked,
        "explicit_contract_count": explicit_contract,
        "usable_provenance_count": usable_count,
        "regime_counts": dict(regime_counter),
        "defects": defects,
        "finding": (
            "OFI is an action postprocessor, not a replacement for exact-trace "
            "outcome calibration."
        ),
    }


def _outcome_index(
    rows_by_version: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for rows in rows_by_version.values():
        for trace_id, row in rows.items():
            outcomes[trace_id] = {
                "outcome_return_pct": _number(row.get("outcome_return_pct")),
                "outcome_mfe_pct": _number(row.get("outcome_mfe_pct")),
                "outcome_mae_pct": _number(row.get("outcome_mae_pct")),
                "first_hit": str(row.get("first_hit") or ""),
            }
    return outcomes


def _decision_value(action: str, outcome_return_pct: float) -> float | None:
    normalized = str(action or "").upper()
    if normalized in EXPOSURE_ACTIONS:
        return outcome_return_pct
    if normalized in NO_EXPOSURE_ACTIONS:
        return 0.0
    return None


def _attach_ofi_outcome(
    row: dict[str, Any],
    outcome: dict[str, Any] | None,
) -> None:
    if not outcome or outcome.get("outcome_return_pct") is None:
        row["outcome_status"] = "pending"
        return
    outcome_return = float(outcome["outcome_return_pct"])
    raw_value = _decision_value(str(row.get("raw_action") or ""), outcome_return)
    final_value = _decision_value(str(row.get("final_action") or ""), outcome_return)
    row.update(outcome)
    row["raw_action_decision_value_pct"] = raw_value
    row["final_action_decision_value_pct"] = final_value
    if raw_value is None or final_value is None:
        row["outcome_status"] = "mature_not_comparable"
        row["outcome_not_comparable_reason"] = (
            "action_value_requires_exact_quantity_or_cashflow_contract"
        )
        row["ofi_action_adjustment_delta_pct"] = None
        return
    row["outcome_status"] = "mature"
    row["outcome_not_comparable_reason"] = None
    row["ofi_action_adjustment_delta_pct"] = final_value - raw_value


def _is_effective_ofi_transition(row: dict[str, Any]) -> bool:
    raw_action = str(row.get("raw_action") or "").strip().upper()
    final_action = str(row.get("final_action") or "").strip().upper()
    return bool(raw_action and final_action and raw_action != final_action)


def _current_ofi_outcome_rows(
    pipeline_path: Path,
    *,
    outcome_by_trace: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: dict[str, dict[str, Any]] = {}
    exclusions: Counter[str] = Counter()
    if not pipeline_path.exists():
        return [], exclusions
    for event in iter_jsonl(pipeline_path):
        stage = str(event.get("stage") or "")
        if stage not in OFI_STAGES:
            continue
        fields = _fields(event)
        trace_id = str(fields.get("ai_decision_trace_id") or "").strip()
        snapshot_id = str(fields.get("ai_input_snapshot_id") or "").strip()
        if trace_id in {"", "-"}:
            exclusions["exact_decision_trace_missing"] += 1
            continue
        if snapshot_id in {"", "-"}:
            exclusions["exact_snapshot_missing"] += 1
            continue
        raw_action = str(
            fields.get("raw_flow_action") or fields.get("raw_action") or ""
        ).upper()
        final_action = str(
            fields.get("final_flow_action") or fields.get("final_action") or ""
        ).upper()
        if not raw_action or not final_action:
            exclusions["action_transition_missing"] += 1
            continue
        outcome = outcome_by_trace.get(trace_id)
        row = {
            "ledger_key": f"{stage}:{trace_id}",
            "decision_trace_id": trace_id,
            "ai_input_snapshot_id": snapshot_id,
            "stage": stage,
            "stock_code": str(event.get("stock_code") or ""),
            "emitted_at": event.get("emitted_at"),
            "raw_action": raw_action,
            "final_action": final_action,
            "smoothing_action": str(fields.get("smoothing_action") or ""),
            "ofi_regime": str(
                fields.get("holding_flow_ofi_regime")
                or fields.get("entry_ai_price_ofi_regime")
                or ""
            ),
            "ofi_reason": str(
                fields.get("holding_flow_ofi_reason")
                or fields.get("entry_ai_price_ofi_reason")
                or ""
            ),
            "ofi_snapshot_age_ms": _number(
                fields.get("holding_flow_ofi_snapshot_age_ms")
                if fields.get("holding_flow_ofi_snapshot_age_ms") is not None
                else fields.get("entry_ai_price_ofi_snapshot_age_ms")
            ),
            "outcome_status": "mature" if outcome else "pending",
            **(outcome or {}),
        }
        _attach_ofi_outcome(row, outcome)
        rows[row["ledger_key"]] = row
    return list(rows.values()), exclusions


def _prior_ofi_outcome_rows(
    report_root: Path,
    *,
    target_date: str,
) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    directory = report_root / REPORT_SUBDIR
    for path in sorted(directory.glob("ai_decision_action_outcome_calibration_*.json")):
        report = _load_json(path)
        source_date = _report_date(path, report)
        if not source_date or source_date >= target_date:
            continue
        ledger = report.get("ofi_action_outcome_calibration")
        if not isinstance(ledger, dict):
            continue
        for row in ledger.get("rows") or []:
            if not isinstance(row, dict) or not row.get("ledger_key"):
                continue
            rows[str(row["ledger_key"])] = dict(row)
    return list(rows.values())


def build_ofi_action_outcome_calibration(
    *,
    report_root: Path,
    target_date: str,
    pipeline_path: Path,
    outcome_by_trace: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    prior_rows = {
        str(row.get("ledger_key")): row
        for row in _prior_ofi_outcome_rows(report_root, target_date=target_date)
    }
    current_rows, exclusions = _current_ofi_outcome_rows(
        pipeline_path,
        outcome_by_trace=outcome_by_trace,
    )
    for row in current_rows:
        prior_rows[str(row["ledger_key"])] = row
    rows = list(prior_rows.values())
    for row in rows:
        trace_id = str(row.get("decision_trace_id") or "")
        _attach_ofi_outcome(row, outcome_by_trace.get(trace_id))
    comparable_mature_rows = [
        row
        for row in rows
        if row.get("outcome_status") == "mature"
        and _number(row.get("ofi_action_adjustment_delta_pct")) is not None
    ]
    pending_rows = [row for row in rows if row.get("outcome_status") == "pending"]
    not_comparable_rows = [
        row for row in rows if row.get("outcome_status") == "mature_not_comparable"
    ]
    effective_transition_rows = [
        row for row in rows if _is_effective_ofi_transition(row)
    ]
    no_change_control_rows = [
        row for row in rows if not _is_effective_ofi_transition(row)
    ]
    mature_effective_rows = [
        row for row in comparable_mature_rows if _is_effective_ofi_transition(row)
    ]
    pending_effective_rows = [
        row for row in pending_rows if _is_effective_ofi_transition(row)
    ]
    not_comparable_effective_rows = [
        row for row in not_comparable_rows if _is_effective_ofi_transition(row)
    ]
    deltas = [
        float(row["ofi_action_adjustment_delta_pct"]) for row in mature_effective_rows
    ]
    return {
        "schema": OFI_LEDGER_SCHEMA,
        "status": (
            "cumulative_learning_updated"
            if mature_effective_rows
            else (
                "exact_trace_rows_waiting_for_mature_outcome"
                if pending_effective_rows
                else (
                    "mature_outcome_not_comparable_keep_collecting"
                    if not_comparable_effective_rows
                    else "sample_floor_keep_collecting"
                )
            )
        ),
        "exact_trace_row_count": len(rows),
        "effective_transition_row_count": len(effective_transition_rows),
        "no_change_control_row_count": len(no_change_control_rows),
        "mature_outcome_row_count": len(comparable_mature_rows),
        "mature_effective_transition_outcome_row_count": len(mature_effective_rows),
        "pending_outcome_row_count": len(pending_rows),
        "pending_effective_transition_outcome_row_count": len(pending_effective_rows),
        "mature_not_comparable_outcome_row_count": len(not_comparable_rows),
        "mature_not_comparable_effective_transition_outcome_row_count": len(
            not_comparable_effective_rows
        ),
        "mature_not_comparable_reason_counts": dict(
            Counter(
                str(row.get("outcome_not_comparable_reason") or "unknown")
                for row in not_comparable_rows
            )
        ),
        "raw_to_final_transition_counts": dict(
            Counter(
                f"{row.get('raw_action')}->{row.get('final_action')}"
                for row in mature_effective_rows
            )
        ),
        "effective_transition_lane_counts": dict(
            Counter(
                f"{row.get('stage')}:{row.get('raw_action')}->{row.get('final_action')}"
                for row in effective_transition_rows
            )
        ),
        "no_change_control_outcome_status_counts": dict(
            Counter(
                str(row.get("outcome_status") or "unknown")
                for row in no_change_control_rows
            )
        ),
        "smoothing_action_counts": dict(
            Counter(str(row.get("smoothing_action") or "UNKNOWN") for row in rows)
        ),
        "source_quality_adjusted_ev_delta_pct": (fmean(deltas) if deltas else None),
        "positive_adjustment_count": sum(value > 0 for value in deltas),
        "negative_adjustment_count": sum(value < 0 for value in deltas),
        "zero_adjustment_count": sum(value == 0 for value in deltas),
        "current_date_exclusion_counts": dict(exclusions),
        "learning_update_floor": {
            "required_mature_exact_trace_rows": 1,
            "observed_mature_exact_trace_rows": len(mature_effective_rows),
            "required_mature_effective_transition_rows": 1,
            "observed_mature_effective_transition_rows": len(mature_effective_rows),
            "pass": bool(mature_effective_rows),
            "role": "effective_transition_cumulative_learning_update_only",
        },
        "runtime_authority_expansion_allowed": False,
        "rows": rows,
    }


def build_report(
    *,
    target_date: str,
    data_root: Path = Path("data"),
) -> dict[str, Any]:
    report_root = data_root / "report"
    rows_by_version, source_reports = _transition_rows(
        report_root / PAIRED_SUBDIR,
        target_date=target_date,
    )
    candidates = [
        _transition_summary(version, rows.values(), source_reports)
        for version, rows in sorted(rows_by_version.items())
    ]
    review_ready = [
        row for row in candidates if row["review_ready_for_prompt_candidate"]
    ]
    selected = (
        max(
            review_ready,
            key=lambda row: (
                _number(row.get("candidate_primary_decision_ev_delta_pct"))
                or float("-inf")
            ),
        )
        if review_ready
        else None
    )
    pipeline_path = existing_or_gzip_path(
        data_root / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    )
    ofi_action_outcome_calibration = build_ofi_action_outcome_calibration(
        report_root=report_root,
        target_date=target_date,
        pipeline_path=pipeline_path,
        outcome_by_trace=_outcome_index(rows_by_version),
    )
    return {
        "schema": SCHEMA,
        "policy_version": POLICY_VERSION,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "cumulative_action_outcome_calibration_updated"
            if candidates
            else "sample_floor_keep_collecting"
        ),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "candidate_count": len(candidates),
        "prompt_review_gate_policy": PROMPT_REVIEW_GATE,
        "required_runtime_conversion_guards": DOWNSTREAM_RUNTIME_GUARDS,
        "candidate_summaries": candidates,
        "selected_review_candidate": (
            selected["candidate_prompt_version"] if selected else None
        ),
        "selection_status": (
            "review_candidate_available_no_runtime_authority"
            if selected
            else "no_candidate_passes_bounded_exploration_and_ev_gate"
        ),
        "source_reports": source_reports,
        "dedupe_key": "candidate_prompt_version+decision_trace_id",
        "update_policy": (
            "append_exact_trace_daily_results_then_recompute_cumulative_action_outcome"
        ),
        "ofi_smoothing_audit": build_ofi_smoothing_audit(pipeline_path),
        "ofi_action_outcome_calibration": ofi_action_outcome_calibration,
        **OFFLINE_CONTRACT,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build cumulative exact-trace action/outcome calibration."
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(target_date=args.target_date, data_root=args.data_root)
    path = report_path(args.target_date, args.data_root / "report")
    if args.write:
        _atomic_write_json(path, report)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "candidate_count": report["candidate_count"],
                    "selected_review_candidate": report["selected_review_candidate"],
                    "ofi_smoothing_audit": report["ofi_smoothing_audit"],
                    "path": str(path),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
