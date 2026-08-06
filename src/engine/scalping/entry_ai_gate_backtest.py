"""Backtest scalping entry AI score/action gates from existing report artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.engine.automation.source_quality_hard_gate import (
    apply_source_quality_preflight_block,
    filter_source_dates_by_preflight,
    load_source_quality_preflight,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.market_day import is_krx_trading_day

REPORT_TYPE = "entry_ai_gate_backtest"
SCHEMA_VERSION = 3
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
ENTRY_OPPORTUNITY_RECHECK_FAMILY = "entry_opportunity_recheck_runtime"
RUNTIME_UPDATE_MODE = "single_cumulative_quality_update"
ENTRY_RECHECK_TARGET_ENV_KEYS = [
    "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
    "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
    "ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
    "ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT",
    "ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
]
RUNTIME_ENV_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
SCALP_ENTRY_ADM_DIR = DATA_DIR / "report" / "scalp_entry_action_decision_matrix"
MISSED_ENTRY_DIRS = [
    DATA_DIR / "report" / "monitor_snapshots",
    DATA_DIR / "report" / "missed_entry_counterfactual",
]
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"

REALIZED_SAMPLE_FLOOR = 30
COUNTERFACTUAL_SAMPLE_FLOOR = 100
THRESHOLD_RANGE = range(55, 86)
SUPPORTED_WAIT_MIN_SCORE = 60
SUPPORTED_WAIT_MAX_SCORE = 74
SUPPORTED_WAIT_ACTIONS = {"WAIT", "WAIT_REQUOTE"}
NON_DECISION_ACTION_TOKENS = {
    "",
    "-",
    "NONE",
    "NULL",
    "NOT_EVALUATED",
    "NOT_EVALUATED_PRE_CONTRACT",
    "UNKNOWN",
}
ENTRY_CONTEXT_JOIN_FIELDS = (
    "ai_action",
    "action",
    "chosen_action",
    "quote_stale",
    "tick_context_stale",
    "context_stale",
    "entry_submit_revalidation_block",
    "stale_bucket",
    "blocked_reason",
    "no_submit_reason",
    "buy_pressure_10t",
    "net_aggressive_delta_10t",
    "tick_acceleration_ratio",
    "tick_accel",
    "curr_vs_micro_vwap_bp",
    "micro_vwap_bp",
    "large_sell_print_detected",
    "tick_aggressor_pressure_usable",
    "tick_aggressor_trusted_count",
    "tick_context_quality",
    "tick_accel_source",
    "tick_latest_age_ms",
    "quote_age_source",
    "quote_age_ms",
    "micro_vwap_available",
    "minute_candle_window_fresh",
    "minute_candle_context_quality",
    "entry_score_excluded_reason",
    "ai_input_source_quality_reason",
    "decision_quality_contract_status",
    "edge_state",
    "decision_quality_edge_state",
    "entry_probe_intent",
    "entry_probe_intent_status",
    "entry_recheck_recovery_trigger",
    "evidence_trigger",
)
HARD_BLOCK_TOKENS = {
    "broker",
    "cooldown",
    "account",
    "deposit",
    "quantity",
    "zero_qty",
    "manual_control",
    "already_holding",
    "open_pending",
    "loss_reentry",
    "hard_stop",
    "protect_stop",
    "emergency",
}
FORBIDDEN_USES = [
    "score_only_buy",
    "intraday_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "broker_guard_bypass",
    "stale_quote_submit_bypass",
    "quantity_or_cap_change",
    "entry_price_reprice",
]


def _entry_recheck_calibration_candidates(
    best_apply: dict[str, Any],
    *,
    target_date: str,
    cumulative_quality_window: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preserve the bounded entry-recheck handoff without an aggregate report."""

    if not isinstance(best_apply, dict) or not best_apply:
        return []
    policy = str(best_apply.get("policy") or "")
    threshold = int(_safe_float(best_apply.get("threshold"), 0.0) or 0)
    if policy != "supported_wait_recovery" or threshold <= 0:
        return []
    realized = (
        best_apply.get("realized")
        if isinstance(best_apply.get("realized"), dict)
        else {}
    )
    counterfactual = (
        best_apply.get("counterfactual")
        if isinstance(best_apply.get("counterfactual"), dict)
        else {}
    )
    primary_ev_positive = (
        float(realized.get("source_quality_adjusted_ev_pct") or 0.0) > 0.0
    )
    counterfactual_opportunity_positive = bool(
        float(counterfactual.get("source_quality_adjusted_ev_pct") or 0.0) > 0.0
        and float(counterfactual.get("mfe_10m_pct") or 0.0) > 0.0
    )
    current_values, current_values_provenance = _current_recheck_values(target_date)
    current_values_complete = bool(
        current_values_provenance.get("status") == "loaded"
        and all(value is not None for value in current_values.values())
    )
    allowed = bool(
        _safe_bool(best_apply.get("allowed_runtime_apply"))
        and _safe_bool(best_apply.get("sample_floor_passed"))
        and primary_ev_positive
        and counterfactual_opportunity_positive
        and current_values_complete
    )
    quality_update_id = (
        f"{ENTRY_OPPORTUNITY_RECHECK_FAMILY}:cumulative:"
        f"{cumulative_quality_window.get('start_date')}:"
        f"{cumulative_quality_window.get('end_date')}:{threshold}"
    )
    return [
        {
            "family": ENTRY_OPPORTUNITY_RECHECK_FAMILY,
            "stage": "entry",
            "priority": 42,
            "threshold_version": (
                f"entry_opportunity_recheck_runtime:{target_date}:{threshold}"
            ),
            "quality_update_id": quality_update_id,
            "runtime_update_mode": RUNTIME_UPDATE_MODE,
            "max_runtime_apply_count": 1,
            "cumulative_quality_window": cumulative_quality_window,
            "post_apply_attribution_required": True,
            "calibration_state": "adjust_down" if allowed else "hold_sample",
            "calibration_reason": (
                "entry_ai_gate_supported_wait_recovery_positive_ev"
                if allowed
                else "entry_ai_gate_candidate_not_apply_ready"
            ),
            "target_env_keys": ENTRY_RECHECK_TARGET_ENV_KEYS,
            "current_values": current_values,
            "current_values_provenance": current_values_provenance,
            "recommended_values": {
                "enabled": True,
                "min_ai_score": threshold,
                "max_ai_score": 74,
                "require_explicit_buy_action": False,
                "allow_wait_probe_intent": True,
                "require_probe_first_contract": True,
            },
            "source_metrics": {
                "policy": policy,
                "realized": realized,
                "counterfactual": counterfactual,
            },
            "sample_floor_passed": _safe_bool(best_apply.get("sample_floor_passed")),
            "primary_ev_positive": primary_ev_positive,
            "counterfactual_opportunity_positive": (
                counterfactual_opportunity_positive
            ),
            "source_quality_gate": "pass",
            "allowed_runtime_apply": allowed,
            "apply_block_reason": (
                ""
                if allowed
                else (
                    "current_runtime_values_unavailable"
                    if not current_values_complete
                    else str(
                        best_apply.get("apply_block_reason")
                        or "upstream_candidate_blocked"
                    )
                )
            ),
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "entry_ai_gate_backtest_postclose_candidate",
            "forbidden_uses": [
                *FORBIDDEN_USES,
                "broad_buy_score_threshold_relaxation",
            ],
        }
    ]


def _current_recheck_values(target_date: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.json"
    payload, status = _load_json_with_status(path)
    env = (
        payload.get("env_overrides")
        if isinstance(payload.get("env_overrides"), dict)
        else {}
    )
    mapping = {
        "enabled": ("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED", False),
        "min_ai_score": ("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE", 70.0),
        "max_ai_score": ("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE", 74.999),
        "require_explicit_buy_action": (
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
            True,
        ),
        "allow_wait_probe_intent": (
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT",
            False,
        ),
        "require_probe_first_contract": (
            "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
            True,
        ),
    }
    values: dict[str, Any] = {}
    defaulted_env_keys: list[str] = []
    manifest_loaded = status.get("status") == "loaded"
    for value_key, (env_key, default) in mapping.items():
        raw = env.get(env_key)
        if raw is None and manifest_loaded:
            raw = default
            defaulted_env_keys.append(env_key)
        if value_key in {
            "enabled",
            "require_explicit_buy_action",
            "allow_wait_probe_intent",
            "require_probe_first_contract",
        }:
            values[value_key] = _safe_bool(raw) if raw is not None else None
        else:
            values[value_key] = _safe_float(raw, None)
    return values, {
        "status": status.get("status"),
        "path": status.get("path"),
        "source": "target_date_threshold_runtime_env_manifest_plus_code_defaults",
        "defaulted_env_keys": defaulted_env_keys,
    }


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "null", "none", "-"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _stale_flag(value: Any) -> bool:
    if _safe_bool(value):
        return True
    return str(value or "").strip().lower() in {
        "stale",
        "quote_stale",
        "stale_quote",
        "tick_context_stale",
        "context_stale",
    }


def _tick_aggressor_pressure_usable(row: dict[str, Any]) -> bool:
    raw_flag = row.get("tick_aggressor_pressure_usable")
    if isinstance(raw_flag, bool):
        pressure_flag = raw_flag
    else:
        pressure_flag = str(raw_flag or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }
    return bool(
        pressure_flag or _safe_float(row.get("tick_aggressor_trusted_count"), 0.0) > 0
    )


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    dates: list[str] = []
    current = start
    while current <= end:
        if is_krx_trading_day(current):
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _load_json_with_status(path: Path) -> tuple[dict[str, Any], dict[str, str]]:
    actual = existing_or_gzip_path(path)
    if not actual.exists():
        return {}, {"status": "missing", "path": str(actual)}
    try:
        with open_text_auto(actual) as handle:
            payload = json.loads(handle.read())
    except json.JSONDecodeError as exc:
        return {}, {
            "status": "invalid_json",
            "path": str(actual),
            "error": f"JSONDecodeError:{exc.lineno}:{exc.colno}",
        }
    except Exception as exc:
        return {}, {
            "status": "read_error",
            "path": str(actual),
            "error": type(exc).__name__,
        }
    if not isinstance(payload, dict):
        return {}, {
            "status": "invalid_root_type",
            "path": str(actual),
            "error": type(payload).__name__,
        }
    return payload, {"status": "loaded", "path": str(actual)}


def _load_json(path: Path) -> dict[str, Any]:
    payload, _ = _load_json_with_status(path)
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    actual = existing_or_gzip_path(path)
    if not actual.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with open_text_auto(actual) as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except Exception:
        return []
    return rows


def _missed_entry_path(target_date: str) -> Path:
    for base in MISSED_ENTRY_DIRS:
        path = existing_or_gzip_path(
            base / f"missed_entry_counterfactual_{target_date}.json"
        )
        if path.exists():
            return path
    return existing_or_gzip_path(
        MISSED_ENTRY_DIRS[0] / f"missed_entry_counterfactual_{target_date}.json"
    )


def _real_post_sell_outcomes(source_date: str) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for name in ("post_sell_evaluations", "post_sell_candidates"):
        path = POST_SELL_DIR / f"{name}_{source_date}.jsonl"
        for row in _load_jsonl(path):
            if str(row.get("strategy") or "").upper() not in {"", "SCALPING"}:
                continue
            rec_id = str(row.get("recommendation_id") or "").strip()
            profit = _safe_float(row.get("profit_rate"), None)
            if not rec_id or profit is None:
                continue
            prior = outcomes.get(rec_id)
            if prior and prior.get("_outcome_source") == "post_sell_evaluations":
                continue
            item = dict(row)
            item["_outcome_source"] = name
            item["_profit_rate"] = profit
            outcomes[rec_id] = item
    return outcomes


def _source_quality_blocked(row: dict[str, Any]) -> bool:
    text_parts = [
        row.get("source_quality_gate"),
        row.get("source_quality_block_reason"),
        row.get("entry_score_excluded_reason"),
        row.get("ai_input_source_quality_reason"),
        row.get("minute_candle_source_quality_gate"),
        row.get("minute_candle_source_quality_reason"),
    ]
    text = " ".join(str(part or "").lower() for part in text_parts)
    return bool(
        "source_quality_blocked" in text
        or "source_quality_warning" in text
        or "source_quality_insufficient" in text
        or "insufficient_window" in text
        or "truncated_window" in text
        or "continuation_key_missing" in text
        or "continuation_page_limit_reached" in text
        or "hard_block" in text
    )


def _hard_blocked(row: dict[str, Any]) -> bool:
    stage = str(
        row.get("stage") or row.get("terminal_stage") or row.get("source_stage") or ""
    ).lower()
    reason = " ".join(
        str(row.get(key) or "").lower()
        for key in (
            "blocked_reason",
            "no_submit_reason",
            "source_quality_block_reason",
            "entry_submit_revalidation_block",
        )
    )
    return any(token in stage or token in reason for token in HARD_BLOCK_TOKENS)


def _stale(row: dict[str, Any]) -> bool:
    if any(
        _stale_flag(row.get(key))
        for key in ("quote_stale", "tick_context_stale", "context_stale")
    ):
        return True
    submit_block = str(row.get("entry_submit_revalidation_block") or "").strip().lower()
    if submit_block and submit_block not in {"0", "false", "no", "n", "off", "-"}:
        return True
    stale_bucket = str(row.get("stale_bucket") or "").lower()
    return stale_bucket in {"stale", "quote_stale", "stale_quote"}


def _micro_context_usable(row: dict[str, Any]) -> bool:
    if _stale(row):
        return False
    tick_quality = str(row.get("tick_context_quality") or "").strip().lower()
    tick_source = str(row.get("tick_accel_source") or "").strip().lower()
    return bool(
        tick_quality == "fresh_computed"
        and tick_source
        in {
            "computed_10ticks",
            "same_second_burst_10ticks",
        }
    )


def _has_present_value(value: Any) -> bool:
    return str(value or "").strip().lower() not in {"", "-", "none", "null", "nan"}


def _micro_vwap_usable(row: dict[str, Any]) -> bool:
    if not (
        _has_present_value(row.get("curr_vs_micro_vwap_bp"))
        or _has_present_value(row.get("micro_vwap_bp"))
    ):
        return False
    minute_quality = str(row.get("minute_candle_context_quality") or "").strip().lower()
    minute_quality_ok = bool(
        minute_quality
        and minute_quality != "-"
        and not any(
            token in minute_quality
            for token in ("unknown", "missing", "stale", "unavailable")
        )
    )
    return bool(
        _safe_bool(row.get("micro_vwap_available"))
        and _safe_bool(row.get("minute_candle_window_fresh"))
        and minute_quality_ok
    )


def _micro_support(row: dict[str, Any]) -> bool:
    buy_pressure = _safe_float(row.get("buy_pressure_10t"), None)
    tick_accel = _safe_float(
        row.get("tick_acceleration_ratio") or row.get("tick_accel"), None
    )
    micro_vwap = _safe_float(
        row.get("curr_vs_micro_vwap_bp") or row.get("micro_vwap_bp"), None
    )
    large_sell = _safe_bool(row.get("large_sell_print_detected"))
    pressure_usable = _tick_aggressor_pressure_usable(row)
    micro_context_usable = _micro_context_usable(row)
    return bool(
        pressure_usable
        and micro_context_usable
        and _micro_vwap_usable(row)
        and buy_pressure is not None
        and buy_pressure >= 65.0
        and tick_accel is not None
        and tick_accel >= 1.20
        and micro_vwap is not None
        and micro_vwap >= 10.0
        and not large_sell
    )


def _score(row: dict[str, Any]) -> float | None:
    for key in ("ai_score", "score_source_value", "current_ai_score"):
        value = _safe_float(row.get(key), None)
        if value is not None:
            return value
    return None


def _canonical_supported_wait_action(row: dict[str, Any]) -> str:
    """Prefer an actual AI action, but ignore non-decision placeholders."""

    for key in ("ai_action", "action", "chosen_action"):
        action = str(row.get(key) or "").strip().upper()
        if action not in NON_DECISION_ACTION_TOKENS:
            return action
    return ""


def _canonical_wait_probe_contract(row: dict[str, Any]) -> bool:
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    contract_status = (
        str(row.get("decision_quality_contract_status") or "").strip().lower()
    )
    edge_state = (
        str(row.get("edge_state") or row.get("decision_quality_edge_state") or "")
        .strip()
        .upper()
    )
    probe_status = str(row.get("entry_probe_intent_status") or "").strip().lower()
    recovery_trigger = (
        str(
            row.get("entry_recheck_recovery_trigger")
            or row.get("evidence_trigger")
            or evidence.get("trigger")
            or ""
        )
        .strip()
        .lower()
    )
    return bool(
        contract_status == "pass"
        and edge_state == "EDGE"
        and _safe_bool(row.get("entry_probe_intent"))
        and probe_status == "eligible_wait_probe"
        and recovery_trigger == "recovery_required"
    )


def _entry_context_indexes(
    report: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_record: dict[str, list[dict[str, Any]]] = {}
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for raw in report.get("rows") or []:
        if not isinstance(raw, dict):
            continue
        record_id = str(raw.get("record_id") or "").strip()
        candidate_id = str(raw.get("candidate_id") or "").strip()
        if record_id:
            by_record.setdefault(record_id, []).append(raw)
        if candidate_id:
            by_candidate.setdefault(candidate_id, []).append(raw)
    return by_record, by_candidate


def _entry_context_row_rank(
    row: dict[str, Any], *, anchor_stage: str
) -> tuple[int, int, int, int]:
    stage = str(row.get("stage") or "").strip().lower()
    source_stage = str(row.get("source_stage") or "").strip().lower()
    anchor = str(anchor_stage or "").strip().lower()
    stage_match = int(bool(anchor) and anchor in {stage, source_stage})
    decision_snapshot = int(
        "scalp_entry_action_decision_snapshot" in {stage, source_stage}
    )
    action_present = int(
        any(
            _has_present_value(row.get(key))
            for key in ("ai_action", "action", "chosen_action")
        )
    )
    context_field_count = sum(
        1 for key in ENTRY_CONTEXT_JOIN_FIELDS if _has_present_value(row.get(key))
    )
    return stage_match, decision_snapshot, action_present, context_field_count


def _enrich_counterfactual_entry_context(
    raw: dict[str, Any],
    *,
    by_record: dict[str, list[dict[str, Any]]],
    by_candidate: dict[str, list[dict[str, Any]]],
    source_path: Path,
) -> tuple[dict[str, Any], str]:
    row = dict(raw)
    record_id = str(raw.get("record_id") or "").strip()
    candidate_id = str(raw.get("candidate_id") or "").strip()
    matches = by_record.get(record_id) if record_id else None
    join_status = "joined_record_id"
    if not matches:
        matches = by_candidate.get(candidate_id) if candidate_id else None
        join_status = "joined_candidate_id"
    if not matches:
        row["entry_context_join_status"] = "not_joined"
        row["entry_context_join_source"] = str(source_path)
        row["entry_context_joined"] = False
        return row, "not_joined"
    context = max(
        matches,
        key=lambda item: _entry_context_row_rank(
            item, anchor_stage=str(raw.get("anchor_stage") or "")
        ),
    )
    joined_fields: list[str] = []
    for key in ENTRY_CONTEXT_JOIN_FIELDS:
        if _has_present_value(row.get(key)) or not _has_present_value(context.get(key)):
            continue
        row[key] = context.get(key)
        joined_fields.append(key)
    row.update(
        {
            "entry_context_join_status": join_status,
            "entry_context_join_source": str(source_path),
            "entry_context_joined": True,
            "entry_context_joined_fields": joined_fields,
            "entry_context_join_record_id": str(context.get("record_id") or ""),
            "entry_context_join_candidate_id": str(context.get("candidate_id") or ""),
            "entry_context_join_stage": str(
                context.get("stage") or context.get("source_stage") or ""
            ),
        }
    )
    return row, join_status


def _realized_rows(
    source_dates: list[str],
    missing: list[dict[str, str]],
    consumed_dates: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_date in source_dates:
        path = existing_or_gzip_path(
            SCALP_ENTRY_ADM_DIR
            / f"scalp_entry_action_decision_matrix_{source_date}.json"
        )
        report, load_status = _load_json_with_status(path)
        if not report:
            missing.append(
                {
                    "date": source_date,
                    "artifact": "scalp_entry_action_decision_matrix",
                    **load_status,
                }
            )
            continue
        if consumed_dates is not None:
            consumed_dates.append(source_date)
        real_outcomes = _real_post_sell_outcomes(source_date)
        real_joined_by_record: dict[str, tuple[int, dict[str, Any]]] = {}
        for raw in report.get("rows") or []:
            if not isinstance(raw, dict):
                continue
            score = _score(raw)
            if score is None:
                continue
            record_id = str(raw.get("record_id") or "").strip()
            outcome = real_outcomes.get(record_id)
            profit = _safe_float((outcome or {}).get("_profit_rate"), None)
            outcome_source = (outcome or {}).get("_outcome_source")
            if profit is None and _safe_bool(
                raw.get("actual_order_submitted") or raw.get("broker_order_submitted")
            ):
                profit = _safe_float(raw.get("profit_rate"), None)
                outcome_source = "scalp_entry_action_decision_matrix"
            if profit is None:
                continue
            row = dict(raw)
            if outcome:
                row.update(
                    {
                        "actual_order_submitted": True,
                        "broker_order_forbidden": False,
                        "post_sell_id": outcome.get("post_sell_id"),
                        "sell_time": outcome.get("sell_time"),
                        "exit_rule": outcome.get("exit_rule"),
                    }
                )
            row["_date"] = source_date
            row["_score"] = score
            row["_realized_profit_pct"] = profit
            row["_realized_outcome_source"] = outcome_source or "unknown"
            if outcome and record_id:
                stage_text = (
                    f"{row.get('stage') or ''} {row.get('source_stage') or ''}".lower()
                )
                if "ai_confirmed" in stage_text:
                    priority = 0
                elif "blocked_ai_score" in stage_text:
                    priority = 1
                elif str(row.get("ai_action") or "").strip():
                    priority = 2
                else:
                    priority = 3
                prior = real_joined_by_record.get(record_id)
                if prior is None or priority < prior[0]:
                    real_joined_by_record[record_id] = (priority, row)
            else:
                rows.append(row)
        rows.extend(item[1] for item in real_joined_by_record.values())
    return rows


def _counterfactual_rows(
    source_dates: list[str],
    missing: list[dict[str, str]],
    consumed_dates: list[str] | None = None,
    context_join_counts: Counter[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_date in source_dates:
        path = _missed_entry_path(source_date)
        report, load_status = _load_json_with_status(path)
        if not report:
            missing.append(
                {
                    "date": source_date,
                    "artifact": "missed_entry_counterfactual",
                    **load_status,
                }
            )
            continue
        if consumed_dates is not None:
            consumed_dates.append(source_date)
        context_path = existing_or_gzip_path(
            SCALP_ENTRY_ADM_DIR
            / f"scalp_entry_action_decision_matrix_{source_date}.json"
        )
        context_report = _load_json(context_path)
        by_record, by_candidate = _entry_context_indexes(context_report)
        for raw in report.get("full_rows") or []:
            if not isinstance(raw, dict):
                continue
            close_10m = _safe_float(raw.get("close_10m_pct"), None)
            score = _score(raw)
            if close_10m is None or score is None:
                continue
            row, join_status = _enrich_counterfactual_entry_context(
                raw,
                by_record=by_record,
                by_candidate=by_candidate,
                source_path=context_path,
            )
            if context_join_counts is not None:
                context_join_counts["eligible_counterfactual_rows"] += 1
                context_join_counts[join_status] += 1
            row["_date"] = source_date
            row["_score"] = score
            row["_close_10m_pct"] = close_10m
            row["_mfe_10m_pct"] = _safe_float(raw.get("mfe_10m_pct"), 0.0) or 0.0
            row["_mae_10m_pct"] = _safe_float(raw.get("mae_10m_pct"), 0.0) or 0.0
            rows.append(row)
    return rows


def _notional(row: dict[str, Any]) -> float:
    value = _safe_float(
        row.get("counterfactual_notional_krw") or row.get("notional_krw"), None
    )
    return value if value and value > 0 else 1.0


def _metrics(rows: list[dict[str, Any]], value_key: str) -> dict[str, Any]:
    values = [_safe_float(row.get(value_key), None) for row in rows]
    values = [value for value in values if value is not None]
    if not values:
        return {
            "sample": 0,
            "diagnostic_win_rate": 0.0,
            "equal_weight_avg_profit_pct": 0.0,
            "notional_weighted_ev_pct": 0.0,
            "source_quality_adjusted_ev_pct": 0.0,
            "simple_sum_profit_pct": 0.0,
        }
    notionals = [
        _notional(row)
        for row in rows
        if _safe_float(row.get(value_key), None) is not None
    ]
    weighted = sum(
        value * notional for value, notional in zip(values, notionals)
    ) / max(sum(notionals), 1.0)
    source_quality_pass = sum(1 for row in rows if not _source_quality_blocked(row))
    quality_ratio = source_quality_pass / len(rows) if rows else 0.0
    avg = sum(values) / len(values)
    return {
        "sample": len(values),
        "diagnostic_win_rate": round(
            sum(1 for value in values if value > 0) * 100.0 / len(values), 2
        ),
        "equal_weight_avg_profit_pct": round(avg, 6),
        "notional_weighted_ev_pct": round(weighted, 6),
        "source_quality_adjusted_ev_pct": round(avg * quality_ratio, 6),
        "simple_sum_profit_pct": round(sum(values), 6),
    }


def _matches_policy(row: dict[str, Any], policy: str, threshold: int) -> bool:
    score = _safe_float(row.get("_score"), -1.0) or -1.0
    ai_action = str(row.get("ai_action") or row.get("action") or "").strip().upper()
    if policy == "strict_buy":
        return (
            ai_action == "BUY"
            and score >= threshold
            and not _stale(row)
            and not _hard_blocked(row)
            and not _source_quality_blocked(row)
        )
    if policy == "diagnostic_score_only":
        return score >= threshold
    if policy == "supported_wait_recovery":
        action_key = _canonical_supported_wait_action(row)
        return (
            SUPPORTED_WAIT_MIN_SCORE <= score <= SUPPORTED_WAIT_MAX_SCORE
            and score >= threshold
            and action_key in SUPPORTED_WAIT_ACTIONS
            and _canonical_wait_probe_contract(row)
            and not _stale(row)
            and not _hard_blocked(row)
            and not _source_quality_blocked(row)
            and _micro_support(row)
        )
    return False


def _supported_wait_source_contract_evaluable(row: dict[str, Any]) -> bool:
    score = _safe_float(row.get("_score"), -1.0) or -1.0
    action_present = bool(_canonical_supported_wait_action(row))
    wait_probe_contract_fields_present = bool(
        _has_present_value(row.get("decision_quality_contract_status"))
        and _has_present_value(
            row.get("edge_state") or row.get("decision_quality_edge_state")
        )
        and row.get("entry_probe_intent") is not None
        and _has_present_value(row.get("entry_probe_intent_status"))
        and _has_present_value(
            row.get("entry_recheck_recovery_trigger")
            or row.get("evidence_trigger")
            or (
                (row.get("evidence") or {}).get("trigger")
                if isinstance(row.get("evidence"), dict)
                else None
            )
        )
    )
    micro_provenance_present = bool(
        row.get("tick_aggressor_pressure_usable") is not None
        or _has_present_value(row.get("tick_context_quality"))
        or _has_present_value(row.get("tick_accel_source"))
        or row.get("micro_vwap_available") is not None
        or _has_present_value(row.get("minute_candle_context_quality"))
    )
    return bool(
        SUPPORTED_WAIT_MIN_SCORE <= score <= SUPPORTED_WAIT_MAX_SCORE
        and action_present
        and wait_probe_contract_fields_present
        and micro_provenance_present
        and not _source_quality_blocked(row)
    )


def _supported_wait_contract_missing_reasons(row: dict[str, Any]) -> list[str]:
    """Explain source-contract gaps without changing the AI action semantics."""

    reasons: list[str] = []
    score = _safe_float(row.get("_score"), None)
    if score is None:
        reasons.append("score_missing")
    elif not (SUPPORTED_WAIT_MIN_SCORE <= score <= SUPPORTED_WAIT_MAX_SCORE):
        reasons.append("score_outside_supported_wait_band")
    if not _canonical_supported_wait_action(row):
        reasons.append("canonical_action_missing")
    if not _has_present_value(row.get("decision_quality_contract_status")):
        reasons.append("decision_quality_contract_status_missing")
    if not _has_present_value(
        row.get("edge_state") or row.get("decision_quality_edge_state")
    ):
        reasons.append("edge_state_missing")
    if row.get("entry_probe_intent") is None:
        reasons.append("entry_probe_intent_missing")
    if not _has_present_value(row.get("entry_probe_intent_status")):
        reasons.append("entry_probe_intent_status_missing")
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    if not _has_present_value(
        row.get("entry_recheck_recovery_trigger")
        or row.get("evidence_trigger")
        or evidence.get("trigger")
    ):
        reasons.append("recovery_trigger_missing")
    if not (
        row.get("tick_aggressor_pressure_usable") is not None
        or _has_present_value(row.get("tick_context_quality"))
        or _has_present_value(row.get("tick_accel_source"))
    ):
        reasons.append("tick_pressure_provenance_missing")
    if not (
        row.get("micro_vwap_available") is not None
        or _has_present_value(row.get("minute_candle_context_quality"))
    ):
        reasons.append("micro_vwap_provenance_missing")
    if _source_quality_blocked(row):
        reasons.append("source_quality_blocked")
    return reasons


def _policy_result(
    *,
    policy: str,
    threshold: int,
    realized_rows: list[dict[str, Any]],
    counterfactual_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    realized = [row for row in realized_rows if _matches_policy(row, policy, threshold)]
    counterfactual = [
        row for row in counterfactual_rows if _matches_policy(row, policy, threshold)
    ]
    realized_metrics = _metrics(realized, "_realized_profit_pct")
    opportunity_metrics = _metrics(counterfactual, "_close_10m_pct")
    mae_values = [_safe_float(row.get("_mae_10m_pct"), None) for row in counterfactual]
    mae_values = [value for value in mae_values if value is not None]
    mfe_values = [_safe_float(row.get("_mfe_10m_pct"), None) for row in counterfactual]
    mfe_values = [value for value in mfe_values if value is not None]
    primary_ev = float(realized_metrics.get("source_quality_adjusted_ev_pct") or 0.0)
    counterfactual_ev = float(
        opportunity_metrics.get("source_quality_adjusted_ev_pct") or 0.0
    )
    counterfactual_mfe = sum(mfe_values) / len(mfe_values) if mfe_values else 0.0
    sample_floor_passed = (
        realized_metrics["sample"] >= REALIZED_SAMPLE_FLOOR
        and opportunity_metrics["sample"] >= COUNTERFACTUAL_SAMPLE_FLOOR
    )
    primary_ev_positive = primary_ev > 0.0
    counterfactual_opportunity_positive = bool(
        counterfactual_ev > 0.0 and counterfactual_mfe > 0.0
    )
    allowed = bool(
        policy != "diagnostic_score_only"
        and sample_floor_passed
        and primary_ev_positive
        and (policy != "supported_wait_recovery" or counterfactual_opportunity_positive)
    )
    if policy == "diagnostic_score_only":
        apply_block_reason = "diagnostic_score_only"
    elif not sample_floor_passed:
        apply_block_reason = "hold_sample"
    elif not primary_ev_positive:
        apply_block_reason = "non_positive_primary_ev"
    elif (
        policy == "supported_wait_recovery" and not counterfactual_opportunity_positive
    ):
        apply_block_reason = "non_positive_counterfactual_opportunity"
    else:
        apply_block_reason = ""
    return {
        "policy": policy,
        "threshold": threshold,
        "realized": realized_metrics,
        "counterfactual": {
            **opportunity_metrics,
            "missed_upside_close_10m_pct": opportunity_metrics[
                "equal_weight_avg_profit_pct"
            ],
            "mfe_10m_pct": (
                round(sum(mfe_values) / len(mfe_values), 6) if mfe_values else 0.0
            ),
            "mae_10m_pct": (
                round(sum(mae_values) / len(mae_values), 6) if mae_values else 0.0
            ),
        },
        "sample_floor_passed": sample_floor_passed,
        "primary_ev_positive": primary_ev_positive,
        "counterfactual_opportunity_positive": counterfactual_opportunity_positive,
        "calibration_state": "candidate_ready" if allowed else "hold_sample",
        "allowed_runtime_apply": allowed,
        "apply_block_reason": apply_block_reason,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _policy_rank_key(item: dict[str, Any]) -> tuple[Any, ...]:
    realized = item.get("realized") or {}
    counterfactual = item.get("counterfactual") or {}
    passed = bool(item.get("sample_floor_passed"))
    ev = float(realized.get("source_quality_adjusted_ev_pct") or 0.0)
    missed = float(counterfactual.get("missed_upside_close_10m_pct") or 0.0)
    realized_sample = int(realized.get("sample") or 0)
    counterfactual_sample = int(counterfactual.get("sample") or 0)
    threshold = int(item.get("threshold") or 0)
    if passed:
        return (1, ev, missed, realized_sample, counterfactual_sample, -threshold)
    return (0, realized_sample, counterfactual_sample, ev, missed, -threshold)


def _best_candidate(results: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        results,
        key=_policy_rank_key,
        reverse=True,
    )
    return ranked[0] if ranked else {}


def _best_allowed_candidate(results: list[dict[str, Any]]) -> dict[str, Any]:
    return _best_candidate(
        [item for item in results if item.get("allowed_runtime_apply")]
    )


def _best_by_realized_ev(results: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        results,
        key=lambda item: (
            float(
                (item.get("realized") or {}).get("source_quality_adjusted_ev_pct")
                or 0.0
            ),
            int((item.get("realized") or {}).get("sample") or 0),
            int((item.get("counterfactual") or {}).get("sample") or 0),
            -int(item.get("threshold") or 0),
        ),
        reverse=True,
    )
    return ranked[0] if ranked else {}


def build_report(
    target_date: str, *, start_date: str | None = None, end_date: str | None = None
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    baseline_source_dates, excluded_dates = filter_allowed_dates(
        _date_range(start, end), policy
    )
    source_dates, source_quality_excluded_dates = filter_source_dates_by_preflight(
        baseline_source_dates,
        preflight_loader=load_source_quality_preflight,
    )
    clean_baseline_date = str(policy.get("clean_tuning_baseline_date") or "2026-06-05")
    cumulative_start = max(start, clean_baseline_date)
    missing_artifacts: list[dict[str, str]] = []
    realized_consumed_dates: list[str] = []
    counterfactual_consumed_dates: list[str] = []
    context_join_counts: Counter[str] = Counter()
    realized = _realized_rows(
        source_dates,
        missing_artifacts,
        consumed_dates=realized_consumed_dates,
    )
    counterfactual = _counterfactual_rows(
        source_dates,
        missing_artifacts,
        consumed_dates=counterfactual_consumed_dates,
        context_join_counts=context_join_counts,
    )
    effective_source_dates = sorted(
        set(realized_consumed_dates) & set(counterfactual_consumed_dates)
    )
    effective_source_date_set = set(effective_source_dates)
    realized = [
        row
        for row in realized
        if str(row.get("_date") or "") in effective_source_date_set
    ]
    counterfactual = [
        row
        for row in counterfactual
        if str(row.get("_date") or "") in effective_source_date_set
    ]
    artifact_excluded_dates = sorted(set(source_dates) - effective_source_date_set)
    cumulative_quality_window = {
        "window_policy": "clean_baseline_cumulative",
        "start_date": cumulative_start,
        "end_date": end,
        "clean_tuning_baseline_date": clean_baseline_date,
        "source_date_count": len(effective_source_dates),
        "source_dates": effective_source_dates,
        "intended_source_date_count": len(source_dates),
        "intended_source_dates": source_dates,
        "excluded_date_count": len(excluded_dates),
        "source_quality_excluded_date_count": len(source_quality_excluded_dates),
        "source_quality_excluded_dates": source_quality_excluded_dates,
        "artifact_excluded_date_count": len(artifact_excluded_dates),
        "artifact_excluded_dates": artifact_excluded_dates,
    }
    results = [
        _policy_result(
            policy=policy_name,
            threshold=threshold,
            realized_rows=realized,
            counterfactual_rows=counterfactual,
        )
        for policy_name in (
            "strict_buy",
            "supported_wait_recovery",
            "diagnostic_score_only",
        )
        for threshold in THRESHOLD_RANGE
    ]
    best = _best_candidate(
        [item for item in results if item["policy"] != "diagnostic_score_only"]
    )
    best_allowed = _best_allowed_candidate(
        [item for item in results if item["policy"] != "diagnostic_score_only"]
    )
    diagnostic_results = [
        item for item in results if item["policy"] == "diagnostic_score_only"
    ]
    best_diagnostic = _best_candidate(diagnostic_results)
    best_positive_diagnostic = _best_by_realized_ev(
        [
            item
            for item in diagnostic_results
            if float(
                (item.get("realized") or {}).get("source_quality_adjusted_ev_pct")
                or 0.0
            )
            > 0.0
        ]
    )
    supported_wait_contract = {
        "realized_evaluable_rows": sum(
            1 for row in realized if _supported_wait_source_contract_evaluable(row)
        ),
        "counterfactual_evaluable_rows": sum(
            1
            for row in counterfactual
            if _supported_wait_source_contract_evaluable(row)
        ),
        "realized_policy_eligible_rows": sum(
            1
            for row in realized
            if _matches_policy(row, "supported_wait_recovery", SUPPORTED_WAIT_MIN_SCORE)
        ),
        "counterfactual_policy_eligible_rows": sum(
            1
            for row in counterfactual
            if _matches_policy(row, "supported_wait_recovery", SUPPORTED_WAIT_MIN_SCORE)
        ),
    }
    supported_wait_missing_reason_counts: dict[str, dict[str, int]] = {}
    for scope, rows in (("realized", realized), ("counterfactual", counterfactual)):
        counts: Counter[str] = Counter()
        for row in rows:
            if _supported_wait_source_contract_evaluable(row):
                continue
            counts.update(_supported_wait_contract_missing_reasons(row))
        supported_wait_missing_reason_counts[scope] = dict(counts)
    source_contract_status = (
        "evaluable"
        if supported_wait_contract["realized_evaluable_rows"] > 0
        and supported_wait_contract["counterfactual_evaluable_rows"] > 0
        else "source_contract_not_evaluable"
    )
    calibration_candidates = _entry_recheck_calibration_candidates(
        best_allowed,
        target_date=target_date,
        cumulative_quality_window=cumulative_quality_window,
    )
    runtime_apply_ready = any(
        _safe_bool(item.get("allowed_runtime_apply"))
        and str(item.get("calibration_state") or "") == "adjust_down"
        for item in calibration_candidates
    )
    score_band_counts: Counter[str] = Counter()
    for row in counterfactual:
        score = _safe_float(row.get("_score"), -1.0) or -1.0
        if score < 50:
            score_band_counts["score_lt50"] += 1
        elif score < 60:
            score_band_counts["score50_59"] += 1
        elif score < 65:
            score_band_counts["score60_64"] += 1
        elif score < 70:
            score_band_counts["score65_69"] += 1
        elif score < 75:
            score_band_counts["score70_74"] += 1
        else:
            score_band_counts["score75_plus"] += 1
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "excluded_dates": excluded_dates,
        "source_consumption": {
            "baseline_eligible_source_dates": baseline_source_dates,
            "intended_source_dates": source_dates,
            "source_quality_excluded_dates": source_quality_excluded_dates,
            "realized_consumed_dates": sorted(set(realized_consumed_dates)),
            "counterfactual_consumed_dates": sorted(set(counterfactual_consumed_dates)),
            "effective_source_dates": effective_source_dates,
            "artifact_excluded_dates": artifact_excluded_dates,
            "counterfactual_context_join_counts": dict(context_join_counts),
            "supported_wait_recovery_contract": {
                **supported_wait_contract,
                "status": source_contract_status,
                "missing_reason_counts": supported_wait_missing_reason_counts,
            },
        },
        "source_paths": {
            "scalp_entry_action_decision_matrix": str(SCALP_ENTRY_ADM_DIR),
            "missed_entry_counterfactual": [str(path) for path in MISSED_ENTRY_DIRS],
            "pipeline_events": str(PIPELINE_EVENTS_DIR),
            "post_sell": str(POST_SELL_DIR),
        },
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "entry_ai_gate_backtest_postclose_candidate",
            "window_policy": "clean_baseline_cumulative",
            "requested_window": {"start_date": start, "end_date": end},
            "effective_window": cumulative_quality_window,
            "sample_floor": {
                "realized_joined_rows": REALIZED_SAMPLE_FLOOR,
                "counterfactual_rows": COUNTERFACTUAL_SAMPLE_FLOOR,
            },
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": (
                "clean_baseline_allowed_rows_without_hard_source_quality_block_and_"
                "trusted_tick_pressure_for_buy_pressure_support_and_fresh_minute_candle_for_micro_vwap_support"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": runtime_apply_ready,
        "calibration_state": (
            "candidate_ready"
            if runtime_apply_ready
            else (
                "source_contract_not_evaluable"
                if source_contract_status == "source_contract_not_evaluable"
                else "hold_sample"
            )
        ),
        "calibration_candidates": calibration_candidates,
        "summary": {
            "realized_joined_rows": len(realized),
            "counterfactual_rows": len(counterfactual),
            "effective_source_date_count": len(effective_source_dates),
            "artifact_excluded_date_count": len(artifact_excluded_dates),
            "source_quality_excluded_date_count": len(source_quality_excluded_dates),
            "counterfactual_context_joined_count": sum(
                count
                for status, count in context_join_counts.items()
                if status.startswith("joined_")
            ),
            "counterfactual_context_not_joined_count": context_join_counts.get(
                "not_joined", 0
            ),
            "supported_wait_recovery_source_contract_status": source_contract_status,
            "supported_wait_recovery_realized_evaluable_rows": (
                supported_wait_contract["realized_evaluable_rows"]
            ),
            "supported_wait_recovery_counterfactual_evaluable_rows": (
                supported_wait_contract["counterfactual_evaluable_rows"]
            ),
            "supported_wait_recovery_realized_policy_eligible_rows": (
                supported_wait_contract["realized_policy_eligible_rows"]
            ),
            "supported_wait_recovery_counterfactual_policy_eligible_rows": (
                supported_wait_contract["counterfactual_policy_eligible_rows"]
            ),
            "supported_wait_recovery_missing_reason_counts": (
                supported_wait_missing_reason_counts
            ),
            "score_band_counterfactual_counts": dict(score_band_counts),
            "best_policy": best.get("policy"),
            "best_threshold": best.get("threshold"),
            "best_realized_source_quality_adjusted_ev_pct": (
                best.get("realized") or {}
            ).get("source_quality_adjusted_ev_pct"),
            "best_counterfactual_close_10m_pct": (best.get("counterfactual") or {}).get(
                "missed_upside_close_10m_pct"
            ),
            "sample_floor_passed": bool(best.get("sample_floor_passed", False)),
            "best_apply_policy": best_allowed.get("policy"),
            "best_apply_threshold": best_allowed.get("threshold"),
            "best_apply_realized_source_quality_adjusted_ev_pct": (
                best_allowed.get("realized") or {}
            ).get("source_quality_adjusted_ev_pct"),
            "best_apply_counterfactual_close_10m_pct": (
                best_allowed.get("counterfactual") or {}
            ).get("missed_upside_close_10m_pct"),
            "best_diagnostic_score_only_threshold": best_diagnostic.get("threshold"),
            "best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct": (
                best_diagnostic.get("realized") or {}
            ).get("source_quality_adjusted_ev_pct"),
            "best_diagnostic_score_only_counterfactual_close_10m_pct": (
                best_diagnostic.get("counterfactual") or {}
            ).get("missed_upside_close_10m_pct"),
            "best_diagnostic_score_only_realized_sample": (
                best_diagnostic.get("realized") or {}
            ).get("sample"),
            "best_diagnostic_score_only_counterfactual_sample": (
                best_diagnostic.get("counterfactual") or {}
            ).get("sample"),
            "best_positive_realized_diagnostic_threshold": best_positive_diagnostic.get(
                "threshold"
            ),
            "best_positive_realized_diagnostic_ev_pct": (
                best_positive_diagnostic.get("realized") or {}
            ).get("source_quality_adjusted_ev_pct"),
            "best_positive_realized_diagnostic_sample_floor_passed": bool(
                best_positive_diagnostic.get("sample_floor_passed", False)
            ),
            "best_positive_realized_diagnostic_realized_sample": (
                best_positive_diagnostic.get("realized") or {}
            ).get("sample"),
            "best_positive_realized_diagnostic_counterfactual_sample": (
                best_positive_diagnostic.get("counterfactual") or {}
            ).get("sample"),
            "bounded_calibration_candidate_count": len(calibration_candidates),
            "diagnostic_conflict_detected": bool(
                best_positive_diagnostic
                and float(
                    (best_positive_diagnostic.get("realized") or {}).get(
                        "source_quality_adjusted_ev_pct"
                    )
                    or 0.0
                )
                > 0.0
                and float(
                    (best_positive_diagnostic.get("counterfactual") or {}).get(
                        "missed_upside_close_10m_pct"
                    )
                    or 0.0
                )
                <= 0.0
            ),
        },
        "best_candidate": best,
        "best_apply_candidate": best_allowed,
        "best_diagnostic_score_only_candidate": best_diagnostic,
        "best_positive_realized_diagnostic_candidate": best_positive_diagnostic,
        "policy_results": results,
        "missing_artifacts": missing_artifacts,
        "forbidden_uses": FORBIDDEN_USES,
    }
    preflight = load_source_quality_preflight(target_date)
    report = apply_source_quality_preflight_block(report, preflight)
    final_candidates = [
        item
        for item in report.get("calibration_candidates") or []
        if isinstance(item, dict)
    ]
    allowed_candidates = [
        item
        for item in final_candidates
        if _safe_bool(item.get("allowed_runtime_apply"))
    ]
    report["runtime_update_contract"] = {
        "schema_version": 1,
        "update_mode": RUNTIME_UPDATE_MODE,
        "owner_family": ENTRY_OPPORTUNITY_RECHECK_FAMILY,
        "max_runtime_apply_count": 1,
        "runtime_apply_candidate_count": len(final_candidates),
        "allowed_runtime_apply_count": len(allowed_candidates),
        "quality_update_id": (
            str(allowed_candidates[0].get("quality_update_id") or "")
            if allowed_candidates
            else ""
        ),
        "cumulative_quality_window": cumulative_quality_window,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": report.get("source_quality_gate") or "pass",
        "post_apply_attribution_required": True,
        "runtime_effect": False,
        "forbidden_uses": FORBIDDEN_USES,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    runtime_update_contract = (
        report.get("runtime_update_contract")
        if isinstance(report.get("runtime_update_contract"), dict)
        else {}
    )
    best = (
        report.get("best_candidate")
        if isinstance(report.get("best_candidate"), dict)
        else {}
    )
    source_consumption = (
        report.get("source_consumption")
        if isinstance(report.get("source_consumption"), dict)
        else {}
    )
    lines = [
        f"# Entry AI Gate Backtest - {report.get('target_date')}",
        "",
        f"- calibration_state: `{report.get('calibration_state')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- bounded_calibration_candidate_count: "
        f"`{summary.get('bounded_calibration_candidate_count')}`",
        f"- diagnostic_conflict_detected: "
        f"`{summary.get('diagnostic_conflict_detected')}`",
        f"- runtime_update_mode: `{runtime_update_contract.get('update_mode')}`",
        f"- runtime_apply_candidate_count: "
        f"`{runtime_update_contract.get('runtime_apply_candidate_count')}`",
        f"- allowed_runtime_apply_count: "
        f"`{runtime_update_contract.get('allowed_runtime_apply_count')}`",
        f"- effective_source_date_count: "
        f"`{summary.get('effective_source_date_count')}`",
        f"- artifact_excluded_date_count: "
        f"`{summary.get('artifact_excluded_date_count')}`",
        f"- source_quality_excluded_date_count: "
        f"`{summary.get('source_quality_excluded_date_count')}`",
        "- source_quality_excluded_dates: `"
        + json.dumps(
            source_consumption.get("source_quality_excluded_dates") or [],
            ensure_ascii=False,
            sort_keys=True,
        )
        + "`",
        f"- counterfactual_context_joined_count: "
        f"`{summary.get('counterfactual_context_joined_count')}`",
        f"- supported_wait_recovery_source_contract_status: "
        f"`{summary.get('supported_wait_recovery_source_contract_status')}`",
        f"- supported_wait_recovery_policy_eligible_rows(realized/counterfactual): "
        f"`{summary.get('supported_wait_recovery_realized_policy_eligible_rows')}/"
        f"{summary.get('supported_wait_recovery_counterfactual_policy_eligible_rows')}`",
        "- supported_wait_recovery_missing_reason_counts: `"
        + json.dumps(
            summary.get("supported_wait_recovery_missing_reason_counts") or {},
            ensure_ascii=False,
            sort_keys=True,
        )
        + "`",
        f"- realized_joined_rows: `{summary.get('realized_joined_rows')}`",
        f"- counterfactual_rows: `{summary.get('counterfactual_rows')}`",
        f"- best_policy: `{summary.get('best_policy')}`",
        f"- best_threshold: `{summary.get('best_threshold')}`",
        f"- best_realized_source_quality_adjusted_ev_pct: `{summary.get('best_realized_source_quality_adjusted_ev_pct')}`",
        f"- best_counterfactual_close_10m_pct: `{summary.get('best_counterfactual_close_10m_pct')}`",
        f"- best_apply_policy: `{summary.get('best_apply_policy')}`",
        f"- best_apply_threshold: `{summary.get('best_apply_threshold')}`",
        f"- best_diagnostic_score_only_threshold: `{summary.get('best_diagnostic_score_only_threshold')}`",
        f"- best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct: "
        f"`{summary.get('best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct')}`",
        f"- best_diagnostic_score_only_counterfactual_close_10m_pct: "
        f"`{summary.get('best_diagnostic_score_only_counterfactual_close_10m_pct')}`",
        f"- best_positive_realized_diagnostic_threshold: "
        f"`{summary.get('best_positive_realized_diagnostic_threshold')}`",
        f"- best_positive_realized_diagnostic_ev_pct: "
        f"`{summary.get('best_positive_realized_diagnostic_ev_pct')}`",
        f"- best_positive_realized_diagnostic_sample_floor_passed: "
        f"`{summary.get('best_positive_realized_diagnostic_sample_floor_passed')}`",
        "",
        "## Best Candidate",
        "",
        "```json",
        json.dumps(best, ensure_ascii=False, indent=2, default=str),
        "```",
        "",
        "## Bounded Calibration Candidates",
        "",
        "```json",
        json.dumps(
            report.get("calibration_candidates") or [],
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        "```",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("target_date") or "unknown"))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date, start_date=args.start_date, end_date=args.end_date
    )
    if args.write:
        json_path, md_path = write_report(report)
        print(
            json.dumps({"json": str(json_path), "md": str(md_path)}, ensure_ascii=False)
        )
    else:
        print(
            json.dumps(
                report, ensure_ascii=False, indent=2, sort_keys=True, default=str
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
