from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.ai_response_contracts import (
    is_known_flow_state_label,
    is_known_gatekeeper_action_label,
    normalize_flow_state_label,
    normalize_gatekeeper_action_key,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


REPORT_DIRNAME = "observation_source_quality_audit"


SOURCE_LIKE_TOKENS = (
    "source",
    "metric_role",
    "decision_authority",
    "forbidden_uses",
    "fresh",
    "stale",
    "missing",
    "provenance",
    "authority",
    "forbidden",
    "quality",
    "transport",
    "openai",
    "ws_age",
    "quote",
    "strength",
    "pressure",
    "range",
    "day_high",
    "micro",
    "orderbook",
    "budget_authority",
    "runtime_effect",
    "broker_order",
    "actual_order",
    "submitted",
    "simulated",
)


@dataclass(frozen=True)
class StageContract:
    required_fields: tuple[str, ...]
    zero_sensitive_fields: tuple[str, ...] = ()
    min_sample: int = 1
    max_missing_rate: float = 0.0
    max_zero_rate: float = 1.0
    decision_authority: str = "source_quality_only"
    forbidden_uses: str = "runtime_threshold_apply/order_submit/provider_route_change/bot_restart"


AI_SOURCE_FIELDS = (
    "tick_source_quality_fields_sent",
    "tick_accel_source",
    "tick_context_quality",
    "quote_age_source",
)

AI_OVERLAP_FIELDS = (
    "latest_strength",
    "buy_pressure_10t",
    "distance_from_day_high_pct",
    "intraday_range_pct",
)

SIM_PROVENANCE_FIELDS = (
    "actual_order_submitted",
    "broker_order_forbidden",
    "runtime_effect",
)

SCALP_SIM_PROVENANCE_FIELDS = (
    "simulation_book",
    "simulated_order",
    *SIM_PROVENANCE_FIELDS,
    "decision_authority",
    "sim_record_id",
)

SCALP_SIM_AI_BUDGET_FIELDS = (
    "simulation_book",
    "simulated_order",
    *SIM_PROVENANCE_FIELDS,
    "decision_authority",
    "sim_record_id",
    "entry_adm_candidate_id",
)

SCALP_SIM_RISK_CONTEXT_FIELDS = (
    "simulation_book",
    "simulated_order",
    *SIM_PROVENANCE_FIELDS,
    "decision_authority",
    "threshold_family",
    "source_stage",
)

SWING_PROBE_FIELDS = (
    "simulated_order",
    "evidence_quality",
    "source_record_id",
)

ORDERBOOK_MICRO_FIELDS = (
    "orderbook_micro_ready",
    "orderbook_micro_state",
    "orderbook_micro_reason",
    "orderbook_micro_snapshot_age_ms",
    "orderbook_micro_observer_healthy",
)

PRE_AI_RISK_CONTEXT_FIELDS = (
    "metric_role",
    "decision_authority",
    "runtime_effect",
    "forbidden_uses",
    "threshold_family",
    "gate_action",
    "allowed_runtime_apply",
    "actual_order_submitted",
)

PRE_SUBMIT_GUARD_FIELDS = (
    "metric_role",
    "decision_authority",
    "runtime_effect",
    "forbidden_uses",
    "threshold_family",
    "gate_action",
    "actual_order_submitted",
    "broker_order_forbidden",
)

LATENCY_SUBMIT_FIELDS = (
    "reason",
    "latency_state",
    "policy_decision",
    "effective_decision",
    "ws_age_ms",
    "ws_jitter_ms",
    "spread_ratio",
    "quote_stale",
    "signal_price",
    "latest_price",
    "latency_canary_applied",
    "latency_canary_reason",
    "threshold_family",
    "runtime_effect",
    "actual_order_submitted",
    "broker_order_forbidden",
)

DIAGNOSTIC_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "runtime_effect",
    "forbidden_uses",
)

REAL_EXECUTION_DIAGNOSTIC_FIELDS = (
    *DIAGNOSTIC_CONTRACT_FIELDS,
    "actual_order_submitted",
    "broker_order_forbidden",
)


STAGE_CONTRACTS: dict[str, StageContract] = {
    "ai_confirmed": StageContract(
        required_fields=(*AI_SOURCE_FIELDS, *AI_OVERLAP_FIELDS),
        zero_sensitive_fields=("intraday_range_pct",),
        max_missing_rate=0.25,
        max_zero_rate=0.10,
    ),
    "blocked_ai_score": StageContract(
        required_fields=(*AI_SOURCE_FIELDS, *AI_OVERLAP_FIELDS),
        zero_sensitive_fields=("distance_from_day_high_pct", "intraday_range_pct"),
        max_missing_rate=0.10,
        max_zero_rate=0.10,
    ),
    "wait65_79_ev_candidate": StageContract(
        required_fields=AI_SOURCE_FIELDS,
        max_missing_rate=0.10,
    ),
    "blocked_strength_momentum": StageContract(
        required_fields=(*AI_OVERLAP_FIELDS, *PRE_AI_RISK_CONTEXT_FIELDS),
        zero_sensitive_fields=("intraday_range_pct",),
        max_zero_rate=0.10,
    ),
    "blocked_vpw": StageContract(
        required_fields=(*AI_OVERLAP_FIELDS, *PRE_AI_RISK_CONTEXT_FIELDS),
        zero_sensitive_fields=("distance_from_day_high_pct", "intraday_range_pct"),
        max_zero_rate=0.10,
    ),
    "blocked_overbought": StageContract(
        required_fields=(*AI_OVERLAP_FIELDS, *PRE_AI_RISK_CONTEXT_FIELDS),
        zero_sensitive_fields=("intraday_range_pct",),
        max_zero_rate=0.10,
    ),
    "blocked_liquidity": StageContract(
        required_fields=(*PRE_AI_RISK_CONTEXT_FIELDS, "liquidity_value", "min_liquidity"),
    ),
    "pre_submit_liquidity_guard_block": StageContract(
        required_fields=(*PRE_SUBMIT_GUARD_FIELDS, "liquidity_value", "min_liquidity"),
    ),
    "pre_submit_overbought_pullback_guard_block": StageContract(
        required_fields=(*PRE_SUBMIT_GUARD_FIELDS, "risk_state"),
    ),
    "latency_block": StageContract(
        required_fields=LATENCY_SUBMIT_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "latency_pass": StageContract(
        required_fields=LATENCY_SUBMIT_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "order_bundle_submitted": StageContract(
        required_fields=LATENCY_SUBMIT_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_entry_armed": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_buy_order_virtual_pending": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_buy_order_assumed_filled": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_entry_ai_price_skip_order": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_holding_started": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_sell_order_assumed_filled": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_ai_holding_live_call": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_ai_holding_deferred": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "sim_ai_budget_exhausted": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "sim_ai_critical_bypass": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_panic_bottoming_entry_allowed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_panic_level1_entry_observed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_panic_entry_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_panic_scale_in_blocked": StageContract(required_fields=(*SCALP_SIM_RISK_CONTEXT_FIELDS, "sim_record_id")),
    "scalp_sim_panic_action_deduped": StageContract(required_fields=(*SCALP_SIM_RISK_CONTEXT_FIELDS, "sim_record_id")),
    "scalp_sim_partial_sell_order_assumed_filled": StageContract(
        required_fields=(*SCALP_SIM_RISK_CONTEXT_FIELDS, "sim_record_id", "entry_adm_candidate_id")
    ),
    "scalp_sim_euphoria_context_noop": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_entry_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_chase_entry_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_retest_starter_allowed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_level1_starter_observed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_scale_in_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_partial_profit_assumed_filled": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_partial_profit_unpriced": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_action_deduped": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "ai_holding_fast_reuse_band": StageContract(
        required_fields=(*DIAGNOSTIC_CONTRACT_FIELDS, "source_quality_route", "telemetry_only", "action"),
        decision_authority="source_quality_only",
    ),
    "soft_stop_expert_shadow": StageContract(
        required_fields=(*DIAGNOSTIC_CONTRACT_FIELDS, "source_quality_route", "shadow_only", "hierarchy"),
        decision_authority="source_quality_only",
    ),
    "holding_flow_override_candidate_cleared": StageContract(
        required_fields=(*DIAGNOSTIC_CONTRACT_FIELDS, "source_quality_route", "reason", "previous_key"),
        decision_authority="source_quality_only",
    ),
    "swing_probe_entry_candidate": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, "virtual_budget_override", "budget_authority"),
    ),
    "swing_probe_holding_started": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, "virtual_budget_override", "budget_authority"),
    ),
    "swing_probe_exit_signal": StageContract(required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS)),
    "swing_probe_sell_order_assumed_filled": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.05,
    ),
    "swing_probe_scale_in_order_assumed_filled": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.05,
    ),
    "swing_reentry_counterfactual_after_loss": StageContract(
        required_fields=("simulated_order", "actual_order_submitted", "broker_order_forbidden", "runtime_effect"),
    ),
    "swing_same_symbol_loss_reentry_cooldown": StageContract(
        required_fields=("actual_order_submitted", "broker_order_forbidden", "source_book", "source_probe_id"),
    ),
    "swing_probe_state_persisted": StageContract(
        required_fields=(
            "simulation_book",
            "simulation_owner",
            "metric_role",
            "decision_authority",
            "runtime_effect",
            "forbidden_uses",
        ),
    ),
    "swing_scale_in_micro_context_observed": StageContract(required_fields=ORDERBOOK_MICRO_FIELDS),
    "scale_in_price_resolved": StageContract(
        required_fields=("price_source", "virtual_budget_override", "budget_authority", *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.50,
    ),
    "scale_in_price_p2_observe": StageContract(
        required_fields=("price_source", *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.50,
    ),
    "swing_sim_scale_in_order_assumed_filled": StageContract(
        required_fields=("actual_order_submitted", "broker_order_forbidden", "virtual_budget_override", "budget_authority", *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.05,
    ),
    "loss_fallback_probe": StageContract(
        required_fields=("gate_allowed", "gate_reason", "fallback_candidate", "fallback_reason", "profit_rate", "peak_profit"),
        decision_authority="source_quality_only",
    ),
    "soft_stop_whipsaw_confirmation": StageContract(
        required_fields=("threshold_family", "threshold_version", "threshold_calibration_state", "profit_rate", "flow_state", "exit_rule_candidate"),
        decision_authority="source_quality_only",
    ),
    "blocked_gatekeeper_reject": StageContract(
        required_fields=("action", "cooldown_policy"),
        decision_authority="source_quality_only",
    ),
    "entry_armed": StageContract(
        required_fields=("ai_score", "ratio", "target_buy_price", "current_vpw", "reason", "ttl_sec"),
        decision_authority="source_quality_only",
    ),
    "entry_armed_expired_after_wait": StageContract(
        required_fields=("waited_sec", "resume_count", "reason"),
        decision_authority="source_quality_only",
    ),
    "holding_started": StageContract(
        required_fields=REAL_EXECUTION_DIAGNOSTIC_FIELDS,
        decision_authority="broker_receipt_observation_only",
    ),
    "scale_in_executed": StageContract(
        required_fields=REAL_EXECUTION_DIAGNOSTIC_FIELDS,
        decision_authority="broker_receipt_observation_only",
    ),
    "same_symbol_loss_reentry_cooldown": StageContract(
        required_fields=(
            *DIAGNOSTIC_CONTRACT_FIELDS,
            "actual_order_submitted",
            "broker_order_forbidden",
            "source_stage",
            "guard_family",
        ),
        decision_authority="same_symbol_loss_reentry_guard_observation_only",
    ),
}


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def report_paths(target_date: str) -> tuple[Path, Path]:
    report_dir = DATA_DIR / "report" / REPORT_DIRNAME
    return (
        report_dir / f"observation_source_quality_audit_{target_date}.json",
        report_dir / f"observation_source_quality_audit_{target_date}.md",
    )


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() in {"", "-", "None", "none", "null"}:
        return False
    return True


def _source_like_field(key: str) -> bool:
    lowered = str(key).lower()
    return any(token in lowered for token in SOURCE_LIKE_TOKENS)


def _iter_events(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = existing_or_gzip_path(path)
    if not path.exists():
        return rows
    for payload in iter_jsonl(path):
        if payload.get("event_type") not in (None, "", "pipeline_event"):
            continue
        fields = payload.get("fields")
        payload["fields"] = fields if isinstance(fields, dict) else {}
        rows.append(payload)
    return rows


def _stage_name(row: dict[str, Any]) -> str:
    return str(row.get("stage") or "-")


def _normalized_fields_for_contract(stage: str, fields: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(fields or {})
    if stage == "ai_confirmed":
        for field in AI_SOURCE_FIELDS:
            if not _is_present(normalized.get(field)):
                normalized[field] = "not_evaluated_pre_contract" if field != "tick_source_quality_fields_sent" else False
        normalized.setdefault("ai_input_source_quality_status", "not_evaluated")
        normalized.setdefault("ai_input_source_quality_reason", "pre_contract_or_cooldown_score50_path")
    if stage in {"latency_block", "latency_pass", "order_bundle_submitted"}:
        if not _is_present(normalized.get("policy_decision")):
            normalized["policy_decision"] = normalized.get("decision") or normalized.get("effective_decision") or "unknown_pre_contract"
        if not _is_present(normalized.get("effective_decision")):
            normalized["effective_decision"] = normalized.get("policy_decision") or "unknown_pre_contract"
        for field in ("ws_age_ms", "ws_jitter_ms", "spread_ratio"):
            if not _is_present(normalized.get(field)):
                normalized[field] = "unknown_pre_contract"
        if not _is_present(normalized.get("latency_canary_reason")):
            normalized["latency_canary_reason"] = "not_applicable_or_pre_contract"
    if stage in {"holding_started", "scale_in_executed"}:
        normalized.setdefault("metric_role", "execution_quality_real_only")
        normalized.setdefault("decision_authority", "broker_receipt_observation_only")
        normalized.setdefault("runtime_effect", False)
        normalized.setdefault(
            "forbidden_uses",
            "runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim",
        )
        normalized.setdefault("actual_order_submitted", True)
        normalized.setdefault("broker_order_forbidden", False)
    if stage == "same_symbol_loss_reentry_cooldown":
        normalized.setdefault("metric_role", "safety_veto")
        normalized.setdefault("decision_authority", "same_symbol_loss_reentry_guard_observation_only")
        normalized.setdefault("runtime_effect", False)
        normalized.setdefault(
            "forbidden_uses",
            "runtime_threshold_apply/provider_route_change/bot_restart/position_sizing_cap_release",
        )
        normalized.setdefault("actual_order_submitted", True)
        normalized.setdefault("broker_order_forbidden", False)
        normalized.setdefault("source_stage", "sell_order_sent")
        normalized.setdefault("guard_family", "same_symbol_loss_reentry_guard")
    if stage == "loss_fallback_probe" and not _is_present(normalized.get("fallback_reason")):
        fallback_candidate = str(normalized.get("fallback_candidate") or "").strip().lower() in {"true", "1", "yes"}
        if not fallback_candidate:
            normalized["fallback_reason"] = normalized.get("gate_reason") or "not_candidate"
    if stage == "soft_stop_whipsaw_confirmation" and not _is_present(normalized.get("flow_state")):
        normalized["flow_state"] = "flow_state_unavailable"
        normalized["flow_state_source"] = "audit_normalized_missing_runtime_flow_state"
    elif _is_present(normalized.get("flow_state")):
        raw_flow_state = normalized.get("flow_state")
        if not is_known_flow_state_label(raw_flow_state):
            normalized["invalid_flow_state_label"] = raw_flow_state
            normalized["source_quality_blocker"] = "unknown_flow_state_label"
        normalized["flow_state"] = normalize_flow_state_label(raw_flow_state)
        if normalized["flow_state"] != raw_flow_state:
            normalized["raw_flow_state"] = raw_flow_state
            normalized["flow_state_source"] = "audit_normalized_legacy_runtime_flow_state"
    if "gatekeeper" in stage or any(
        _is_present(normalized.get(field)) for field in ("action_key", "gatekeeper_action_key", "gatekeeper_action")
    ):
        raw_action = normalized.get("action_key") or normalized.get("gatekeeper_action_key") or normalized.get(
            "gatekeeper_action"
        ) or normalized.get("action")
        if _is_present(raw_action):
            if not is_known_gatekeeper_action_label(raw_action):
                normalized["invalid_gatekeeper_action_label"] = raw_action
                normalized["source_quality_blocker"] = "unknown_gatekeeper_action_label"
            normalized["action_key"] = normalize_gatekeeper_action_key(raw_action)
    return normalized


def _stage_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(_stage_name(row) for row in rows)


def _evaluate_contracts(rows: list[dict[str, Any]], stage_counts: Counter[str]) -> dict[str, Any]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[_stage_name(row)].append(row)

    results: dict[str, Any] = {}
    warnings: list[str] = []
    for stage, contract in STAGE_CONTRACTS.items():
        stage_rows = by_stage.get(stage, [])
        total = len(stage_rows)
        if total < contract.min_sample:
            results[stage] = {
                "sample_count": total,
                "status": "sample_below_floor",
                "required_fields": list(contract.required_fields),
                "metric_role": "source_quality_gate",
                "decision_authority": contract.decision_authority,
                "runtime_effect": False,
                "forbidden_uses": contract.forbidden_uses,
            }
            continue

        missing_counts: dict[str, int] = {}
        zero_counts: dict[str, int] = {}
        invalid_label_counts: dict[str, int] = {}
        for field in contract.required_fields:
            missing_counts[field] = sum(
                1
                for row in stage_rows
                if not _is_present(_normalized_fields_for_contract(stage, row["fields"]).get(field))
            )
        if stage == "soft_stop_whipsaw_confirmation":
            invalid_label_counts["flow_state"] = sum(
                1
                for row in stage_rows
                if _is_present(
                    _normalized_fields_for_contract(stage, row["fields"]).get("invalid_flow_state_label")
                )
            )
        if "gatekeeper" in stage:
            invalid_label_counts["action"] = sum(
                1
                for row in stage_rows
                if _is_present(
                    _normalized_fields_for_contract(stage, row["fields"]).get("invalid_gatekeeper_action_label")
                )
            )
        for field in contract.zero_sensitive_fields:
            zero_counts[field] = sum(
                1
                for row in stage_rows
                if (value := _safe_float(_normalized_fields_for_contract(stage, row["fields"]).get(field)))
                is not None
                and abs(value) <= 1e-9
            )

        missing_rates = {field: round(count / total, 4) for field, count in missing_counts.items()}
        zero_rates = {field: round(count / total, 4) for field, count in zero_counts.items()}
        invalid_label_rates = {field: round(count / total, 4) for field, count in invalid_label_counts.items()}
        missing_violations = {
            field: rate for field, rate in missing_rates.items() if rate > contract.max_missing_rate
        }
        zero_violations = {field: rate for field, rate in zero_rates.items() if rate > contract.max_zero_rate}
        invalid_label_violations = {field: rate for field, rate in invalid_label_rates.items() if rate > 0}
        status = (
            "fail"
            if invalid_label_violations
            else ("pass" if not missing_violations and not zero_violations else "warning")
        )
        if status == "warning":
            warnings.append(stage)
        if status == "fail":
            warnings.append(stage)
        results[stage] = {
            "sample_count": total,
            "status": status,
            "required_fields": list(contract.required_fields),
            "missing_counts": missing_counts,
            "missing_rates": missing_rates,
            "zero_sensitive_fields": list(contract.zero_sensitive_fields),
            "zero_counts": zero_counts,
            "zero_rates": zero_rates,
            "invalid_label_counts": invalid_label_counts,
            "invalid_label_rates": invalid_label_rates,
            "missing_violations": missing_violations,
            "zero_violations": zero_violations,
            "invalid_label_violations": invalid_label_violations,
            "metric_role": "source_quality_gate",
            "decision_authority": contract.decision_authority,
            "runtime_effect": False,
            "forbidden_uses": contract.forbidden_uses,
        }

    high_volume_no_source_fields: list[dict[str, Any]] = []
    invalid_label_findings: dict[str, dict[str, Any]] = {}
    field_presence: dict[str, Counter[str]] = defaultdict(Counter)
    example_keys: dict[str, list[str]] = {}
    for row in rows:
        stage = _stage_name(row)
        fields = row["fields"]
        normalized = _normalized_fields_for_contract(stage, fields)
        if _is_present(normalized.get("invalid_flow_state_label")):
            key = f"{stage}:flow_state"
            finding = invalid_label_findings.setdefault(
                key,
                {
                    "stage": stage,
                    "field": "flow_state",
                    "count": 0,
                    "examples": [],
                    "routing": "source_quality_blocker",
                },
            )
            finding["count"] += 1
            if len(finding["examples"]) < 5:
                finding["examples"].append(str(normalized.get("invalid_flow_state_label")))
        if _is_present(normalized.get("invalid_gatekeeper_action_label")):
            key = f"{stage}:gatekeeper_action"
            finding = invalid_label_findings.setdefault(
                key,
                {
                    "stage": stage,
                    "field": "gatekeeper_action",
                    "count": 0,
                    "examples": [],
                    "routing": "source_quality_blocker",
                },
            )
            finding["count"] += 1
            if len(finding["examples"]) < 5:
                finding["examples"].append(str(normalized.get("invalid_gatekeeper_action_label")))
        example_keys.setdefault(stage, list(fields.keys())[:30])
        for key, value in fields.items():
            if _source_like_field(key) and _is_present(value):
                field_presence[stage][key] += 1
    for stage, count in stage_counts.most_common():
        if count < 50 or field_presence.get(stage) or stage in STAGE_CONTRACTS:
            continue
        high_volume_no_source_fields.append(
            {
                "stage": stage,
                "event_count": count,
                "example_fields": example_keys.get(stage, []),
                "routing": "instrumentation_gap_or_diagnostic_contract_needed",
            }
        )
    return {
        "stage_contracts": results,
        "warning_stages": warnings,
        "invalid_label_findings": list(invalid_label_findings.values()),
        "high_volume_no_source_fields": high_volume_no_source_fields,
        "field_presence_top": {
            stage: dict(counter.most_common(20))
            for stage, counter in sorted(field_presence.items(), key=lambda item: (-stage_counts[item[0]], item[0]))
        },
    }


def build_observation_source_quality_audit(target_date: str) -> dict[str, Any]:
    raw_path = existing_or_gzip_path(_pipeline_events_path(target_date))
    rows = _iter_events(raw_path)
    stage_counts = _stage_counts(rows)
    contract_result = _evaluate_contracts(rows, stage_counts)
    status = (
        "fail"
        if any((item.get("status") == "fail") for item in contract_result["stage_contracts"].values())
        or contract_result["invalid_label_findings"]
        else
        "warning"
        if contract_result["warning_stages"] or contract_result["high_volume_no_source_fields"]
        else "pass"
    )
    return {
        "report_type": REPORT_DIRNAME,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "policy": {
            "metric_role": "source_quality_gate",
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
            "window_policy": "daily_intraday_or_postclose_diagnostic",
            "primary_decision_metric": "contract_field_presence_and_zero_rate",
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "provider_route_change",
                "bot_restart",
                "real_execution_quality_approval",
            ],
        },
        "source": {"pipeline_events": str(raw_path), "exists": raw_path.exists()},
        "summary": {
            "event_count": len(rows),
            "stage_count": len(stage_counts),
            "top_stages": dict(stage_counts.most_common(20)),
            "warning_stage_count": len(contract_result["warning_stages"]),
            "high_volume_no_source_field_stage_count": len(contract_result["high_volume_no_source_fields"]),
        },
        **contract_result,
    }


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Observation Source Quality Audit - {report.get('target_date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- event_count: `{report.get('summary', {}).get('event_count')}`",
        f"- decision_authority: `{report.get('policy', {}).get('decision_authority')}`",
        f"- runtime_effect: `{report.get('policy', {}).get('runtime_effect')}`",
        f"- forbidden_uses: `{', '.join(report.get('policy', {}).get('forbidden_uses', []))}`",
        "",
        "## Warning Stages",
    ]
    warnings = report.get("warning_stages") or []
    if warnings:
        for stage in warnings:
            detail = report.get("stage_contracts", {}).get(stage, {})
            lines.append(
                f"- `{stage}` sample=`{detail.get('sample_count')}` missing=`{detail.get('missing_violations')}` zero=`{detail.get('zero_violations')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Invalid Label Findings"])
    invalid_labels = report.get("invalid_label_findings") or []
    if invalid_labels:
        for item in invalid_labels:
            lines.append(
                f"- `{item.get('stage')}` field=`{item.get('field')}` count=`{item.get('count')}` routing=`{item.get('routing')}` examples=`{item.get('examples')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## High Volume Stages Without Source-Like Fields"])
    gaps = report.get("high_volume_no_source_fields") or []
    if gaps:
        for item in gaps:
            lines.append(
                f"- `{item.get('stage')}` count=`{item.get('event_count')}` routing=`{item.get('routing')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Top Stages"])
    for stage, count in (report.get("summary", {}).get("top_stages") or {}).items():
        lines.append(f"- `{stage}`: `{count}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(target_date: str) -> dict[str, Any]:
    report = build_observation_source_quality_audit(target_date)
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(report, md_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit observation source-quality field coverage.")
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = write_report(args.target_date) if args.write else build_observation_source_quality_audit(args.target_date)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
