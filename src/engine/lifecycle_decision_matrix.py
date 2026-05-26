"""Build the lifecycle decision matrix source artifact.

The matrix is a postclose source bundle. Runtime code may consume the latest
policy section, but labels such as MFE/MAE/close are never runtime inputs.
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.institutional_flow_context import RUNTIME_FEATURE_KEYS as INSTITUTIONAL_FLOW_FEATURE_KEYS
from src.engine.institutional_flow_context import report_paths as institutional_flow_report_paths
from src.engine.scalp_entry_action_decision_matrix import report_paths as entry_adm_report_paths


MATRIX_DIR = REPORT_DIR / "lifecycle_decision_matrix"
POST_SELL_DIR = Path(__file__).resolve().parents[2] / "data" / "post_sell"
MONITOR_SNAPSHOT_DIR = REPORT_DIR / "monitor_snapshots"
PIPELINE_EVENTS_DIR = Path(__file__).resolve().parents[2] / "data" / "pipeline_events"

REPORT_SCHEMA_VERSION = 1
MATRIX_VERSION_PREFIX = "lifecycle_decision_matrix_v1"
SAMPLE_FLOOR = 20
JOINED_SAMPLE_FLOOR = 10
PROMOTE_JOINED_SAMPLE_FLOOR = 20
PROMOTE_MIN_EV_PCT = 0.30
ENTRY_BUCKET_SAMPLE_FLOOR = 10
ENTRY_BUCKET_PROMOTE_SAMPLE_FLOOR = 20
ENTRY_BUCKET_NEGATIVE_EV_PCT = -0.30
ENTRY_BUCKET_POSITIVE_EV_PCT = 0.30
SCALE_IN_BUCKET_SAMPLE_FLOOR = 5
SCALE_IN_BUCKET_PROMOTE_SAMPLE_FLOOR = 10
SCALE_IN_BUCKET_NEGATIVE_EV_PCT = -0.30
SCALE_IN_BUCKET_POSITIVE_EV_PCT = 0.30
OVERNIGHT_BUCKET_SAMPLE_FLOOR = 5
OVERNIGHT_BUCKET_PROMOTE_SAMPLE_FLOOR = 10
OVERNIGHT_BUCKET_NEGATIVE_EV_PCT = -0.30
OVERNIGHT_BUCKET_POSITIVE_EV_PCT = 0.30
SUBMIT_BUCKET_SAMPLE_FLOOR = 3

RUNTIME_FEATURE_KEYS = {
    "ai_score",
    "ai_action",
    "chosen_action",
    "score_bucket",
    "risk_context_bucket",
    "stale_bucket",
    "price_resolution_bucket",
    "liquidity_bucket",
    "liquidity_guard_action",
    "liquidity_guard_reason",
    "overbought_bucket",
    "overbought_guard_action",
    "overbought_guard_reason",
    "latency_state",
    "latency_reason",
    "price_below_bid_bps",
    "time_bucket",
    "actual_order_submitted",
    "broker_order_forbidden",
    "context_age_ms",
    "quote_age_ms",
    "entry_submit_revalidation_warning",
    "entry_submit_revalidation_block",
    "best_bid",
    "best_ask",
    "resolved_order_price",
    "add_type",
    "scale_in_arm",
    "scale_in_blocker_namespace",
    "scale_in_blocker_reason",
    "qty",
    "limit_price",
    "curr_price",
    "price_guard_reason",
    "qty_reason",
    "ai_score_source",
    "supply_pass_count",
    "would_limit_fill",
    "source_quality_block_reason",
    "gate_action",
    "profit_rate_live",
    "peak_profit",
    "held_sec",
    "ofi",
    "qi",
    "overnight_action",
    "overnight_confidence",
    "overnight_price_source",
    "overnight_status",
    "panic_context_status",
    "panic_level",
    "panic_level_reason",
    "panic_epoch_id",
    "panic_lifecycle_action_id",
    "source_family",
    "decision_family",
    "family_type",
    "live_selectable",
    "preopen_apply_allowed",
    "env_apply_allowed",
    "threshold_env_mutation_allowed",
    "real_order_allowed",
    "risk_context_owner",
    "risk_direction",
    "action_namespace",
    "risk_regime_context_status",
    "risk_regime_level",
    "risk_regime_reason",
    "risk_regime_epoch_id",
    "risk_regime_source_files",
    "runtime_effect",
    "decision_authority",
    "euphoria_risk_level",
    "euphoria_risk_mode",
    "euphoria_level_reason",
    "euphoria_epoch_id",
    "euphoria_context_status",
    "euphoria_source_quality",
    "euphoria_action_id",
    "euphoria_action_type",
    "chase_risk",
    "retest_confirmed",
    "profit_locked",
    "runner_mode",
    "exhaustion_risk",
    "reversal_signal",
    "exclude_from_ev",
    "source_quality_gate_scope",
    "real_gate_allowed",
    "pre_submit_gate_allowed",
    "exclude_from_live_approval",
    "risk_regime_context_owner",
    "market_regime",
    "market_regime_continuous_score",
    "market_regime_continuous_label",
    "market_regime_component_scores",
    "swing_entry_recovery_gate_score",
    "market_regime_score_version",
    "market_regime_source_quality",
    "symbol_regime",
    "panic_bottoming_entry_allowed",
    "panic_bottoming_entry_reason",
    "panic_bottoming_arm",
    "liquidity_state",
    "fill_quality",
    "quote_quality_state",
    "assumed_slippage_bps",
    "lifecycle_ai_context_enabled",
    "lifecycle_ai_context_applied",
    "lifecycle_ai_context_status",
    "lifecycle_ai_context_version",
    "lifecycle_ai_context_source_date",
    "lifecycle_ai_context_stage",
    "lifecycle_ai_context_policy_key",
    "lifecycle_ai_context_hash",
    "lifecycle_ai_context_alignment_hint",
    "lifecycle_ai_context_decision_authority",
    "context_eligible_count",
    "context_applied_count",
    "context_skipped_count",
    "ai_action_alignment_rate",
    "no_context_replay_sample",
    "ai_action_delta_rate",
    "ai_score_delta_avg",
    "context_contribution_score",
    "bounded_auxiliary_weight",
    "attribution_quality_status",
    *INSTITUTIONAL_FLOW_FEATURE_KEYS,
}

LABEL_KEYS = {
    "profit_rate",
    "exit_rule",
    "sim_post_sell_outcome",
    "mfe_10m_pct",
    "mae_10m_pct",
    "close_10m_pct",
    "mfe_30m_pct",
    "mae_30m_pct",
    "close_30m_pct",
    "mfe_60m_pct",
    "mae_60m_pct",
    "close_60m_pct",
    "missed_winner",
    "avoided_loser",
    "sell_today_realized_profit_pct",
    "next_day_open_gap_pct",
    "next_day_mfe_pct",
    "next_day_mae_pct",
    "next_day_close_pct",
    "final_realized_exit_pct",
}

HARD_SAFETY_THRESHOLDS = [
    "broker_submit_guard",
    "stale_quote_submit_block",
    "price_freshness_guard",
    "hard_stop",
    "protect_stop",
    "emergency_stop",
    "account_order_cooldown_qty_guard",
]

BASELINE_PRIOR_THRESHOLDS = [
    "BUY_SCORE_THRESHOLD",
    "VPW_MIN_SCORE",
    "strength_momentum_cutoff",
    "entry_score_cutoff",
]

BOUNDED_TUNABLE_THRESHOLDS = [
    "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION",
    "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION",
    "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION",
    "score65_74_recovery_probe",
    "soft_stop_whipsaw_confirmation",
    "holding_flow_override",
    "scale_in_price_guard",
]

LEGACY_ARCHIVE_THRESHOLDS = [
    "fallback_scout_main",
    "fallback_single",
    "latency_fallback_split_entry",
    "legacy_latency_composite",
    "closed_shadow_axes",
]

SCALP_SIM_SUBMIT_STAGES = {
    "scalp_sim_buy_order_virtual_pending",
    "scalp_sim_buy_order_assumed_filled",
    "scalp_sim_entry_submit_revalidation_warning",
    "scalp_sim_entry_submit_revalidation_block",
    "scalp_sim_pre_submit_liquidity_guard_would_block",
    "scalp_sim_pre_submit_liquidity_guard_would_pass",
    "scalp_sim_pre_submit_liquidity_guard_unknown",
    "scalp_sim_pre_submit_overbought_guard_would_block",
    "scalp_sim_pre_submit_overbought_guard_would_pass",
}

SCALP_SIM_HOLDING_STAGE = "scalp_sim_holding_started"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = MATRIX_DIR / f"lifecycle_decision_matrix_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _read_json_dict(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    try:
        with _open_text(path) as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    yield payload
    except OSError:
        return


def fixed_threshold_contract() -> dict[str, Any]:
    return {
        "priority": [
            "hard_safety_veto",
            "account_order_broker_guard",
            "lifecycle_matrix_runtime_policy",
            "existing_adm_adapter",
            "baseline_fixed_threshold_fallback",
        ],
        "roles": {
            "hard_safety": HARD_SAFETY_THRESHOLDS,
            "baseline_prior": BASELINE_PRIOR_THRESHOLDS,
            "bounded_tunable": BOUNDED_TUNABLE_THRESHOLDS,
            "legacy_archive": LEGACY_ARCHIVE_THRESHOLDS,
        },
        "forbidden_uses": [
            "hard_safety_override",
            "intraday_threshold_mutation",
            "legacy_archive_as_runtime_feature",
            "score_monotonic_ev_assumption",
        ],
    }


def _stage_for_row(row: dict[str, Any]) -> str:
    stage = str(row.get("stage") or "")
    action = str(row.get("chosen_action") or "").upper()
    if stage in {
        "entry_submit_revalidation_warning",
        "entry_submit_revalidation_block",
        *SCALP_SIM_SUBMIT_STAGES,
    }:
        return "submit"
    if stage.startswith("pre_submit_") or stage in {"latency_pass", "latency_block", "order_bundle_submitted"}:
        return "submit"
    if action in {"BUY_NOW", "BUY_DEFENSIVE", "NO_BUY_AI", "WAIT_REQUOTE", "SKIP_STALE", "SKIP_SOURCE_QUALITY"}:
        return "entry"
    return "entry"


def _runtime_features(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in sorted(RUNTIME_FEATURE_KEYS) if key in row}


def _labels(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in sorted(LABEL_KEYS) if key in row}


def _load_institutional_flow_feature_map(target_date: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    json_path, _ = institutional_flow_report_paths(target_date)
    payload = _load_json(json_path)
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    feature_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = str(row.get("stock_code") or "").strip().lstrip("A")
        if not code:
            continue
        feature_map[code] = {
            key: row.get(key)
            for key in INSTITUTIONAL_FLOW_FEATURE_KEYS
            if key in row
        }
    return feature_map, {
        "artifact": str(json_path) if json_path.exists() else None,
        "rows": len(rows),
        "joined_feature_codes": len(feature_map),
        "status": (payload.get("summary") or {}).get("status") if isinstance(payload.get("summary"), dict) else None,
    }


def _apply_institutional_flow_features(rows: list[dict[str, Any]], feature_map: dict[str, dict[str, Any]]) -> int:
    joined = 0
    for row in rows:
        code = str(row.get("stock_code") or "").strip().lstrip("A")
        features = feature_map.get(code)
        if not features:
            continue
        runtime_features = row.setdefault("runtime_features", {})
        if isinstance(runtime_features, dict):
            runtime_features.update(features)
            joined += 1
    return joined


def _stage_ev(stage: str, labels: dict[str, Any]) -> float | None:
    realized = _safe_float(labels.get("profit_rate"), None)
    mfe = _safe_float(labels.get("mfe_10m_pct"), None)
    mae = _safe_float(labels.get("mae_10m_pct"), None)
    close = _safe_float(labels.get("close_10m_pct"), None)
    if all(value is None for value in (realized, mfe, mae, close)):
        return None
    mfe_capped = min(float(mfe or 0.0), 3.0)
    mae_value = float(mae or 0.0)
    close_value = float(close if close is not None else realized or 0.0)
    realized_value = float(realized if realized is not None else close_value)
    if stage in {"entry", "submit"}:
        return round(0.45 * close_value + 0.35 * mfe_capped + 0.20 * mae_value, 4)
    if stage == "scale_in":
        return round(0.40 * realized_value + 0.30 * close_value + 0.20 * mfe_capped + 0.10 * mae_value, 4)
    return round(0.50 * realized_value + 0.25 * close_value + 0.15 * mfe_capped + 0.10 * mae_value, 4)


def _adm_source_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    if rows:
        return [row for row in rows if isinstance(row, dict)]
    examples = payload.get("examples") if isinstance(payload.get("examples"), list) else []
    return [row for row in examples if isinstance(row, dict)]


def _load_entry_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    json_path, _ = entry_adm_report_paths(target_date)
    payload = _load_json(json_path)
    source_rows = _adm_source_rows(payload)
    rows: list[dict[str, Any]] = []
    skipped_sim_lifecycle_rows = 0
    for item in source_rows:
        if not isinstance(item, dict):
            continue
        source_stage = str(item.get("stage") or "")
        if source_stage in SCALP_SIM_SUBMIT_STAGES or source_stage == "scalp_sim_sell_order_assumed_filled":
            skipped_sim_lifecycle_rows += 1
            continue
        stage = _stage_for_row(item)
        labels = _labels(item)
        rows.append(
            {
                "candidate_id": item.get("candidate_id"),
                "stock_code": item.get("stock_code"),
                "event_time": item.get("event_time"),
                "stage": stage,
                "source_stage": item.get("stage"),
                "runtime_features": _runtime_features(item),
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev(stage, labels),
                "outcome_joined": bool(item.get("outcome_joined")),
                "actual_order_submitted": bool(item.get("actual_order_submitted")),
                "source": "scalp_entry_action_decision_matrix",
            }
        )
    return rows, {
        "artifact": str(json_path) if json_path.exists() else None,
        "rows": len(rows),
        "source_rows": len(source_rows),
        "skipped_sim_lifecycle_rows": skipped_sim_lifecycle_rows,
        "source_field": "rows" if isinstance(payload.get("rows"), list) else "examples",
    }


def _sim_label_from_evaluation(item: dict[str, Any]) -> dict[str, Any]:
    metrics = item.get("metrics_10m") if isinstance(item.get("metrics_10m"), dict) else {}
    return {
        "profit_rate": item.get("profit_rate"),
        "exit_rule": item.get("exit_rule"),
        "sim_post_sell_outcome": item.get("outcome"),
        "mfe_10m_pct": metrics.get("mfe_pct"),
        "mae_10m_pct": metrics.get("mae_pct"),
        "close_10m_pct": metrics.get("close_ret_pct"),
    }


def _sim_labels_from_completed_event(item: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
    profit = _safe_float(fields.get("profit_rate") or fields.get("trigger_profit_rate"), None)
    if profit is None:
        return {}
    return {
        "profit_rate": profit,
        "exit_rule": fields.get("exit_rule"),
        "mfe_10m_pct": profit,
        "mae_10m_pct": profit,
        "close_10m_pct": profit,
    }


def _load_sim_post_sell_label_map(target_date: str) -> dict[str, dict[str, Any]]:
    path = POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl"
    labels_by_key: dict[str, dict[str, Any]] = {}
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        labels = _sim_label_from_evaluation(item)
        for key in (item.get("sim_record_id"), item.get("candidate_id"), item.get("entry_adm_candidate_id")):
            raw = str(key or "").strip()
            if raw:
                labels_by_key[raw] = labels
    return labels_by_key


def _scalp_sim_fields(item: dict[str, Any]) -> dict[str, Any]:
    return item.get("fields") if isinstance(item.get("fields"), dict) else {}


def _is_scalp_sim_event(stage: str, fields: dict[str, Any]) -> bool:
    return stage.startswith("scalp_sim_") or fields.get("simulation_book") == "scalp_ai_buy_all"


def _load_sim_post_sell_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl"
    rows: list[dict[str, Any]] = []
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        metrics = item.get("metrics_10m") if isinstance(item.get("metrics_10m"), dict) else {}
        labels = {
            "profit_rate": item.get("profit_rate"),
            "exit_rule": item.get("exit_rule"),
            "sim_post_sell_outcome": item.get("outcome"),
            "mfe_10m_pct": metrics.get("mfe_pct"),
            "mae_10m_pct": metrics.get("mae_pct"),
            "close_10m_pct": metrics.get("close_ret_pct"),
        }
        stage = "exit"
        rows.append(
            {
                "candidate_id": item.get("candidate_id") or item.get("entry_adm_candidate_id") or item.get("sim_record_id"),
                "stock_code": item.get("stock_code"),
                "event_time": item.get("evaluated_at") or item.get("exit_time"),
                "stage": stage,
                "source_stage": "sim_post_sell_evaluation",
                "runtime_features": {
                    "ai_score": item.get("ai_score"),
                    "chosen_action": item.get("exit_rule"),
                    "fixed_threshold_contract_role": "bounded_tunable",
                },
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev(stage, labels),
                "outcome_joined": True,
                "actual_order_submitted": False,
                "source": "sim_post_sell_evaluations",
            }
        )
    return rows, {"artifact": str(path) if path.exists() else None, "rows": len(rows)}


def _load_wait6579_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = MONITOR_SNAPSHOT_DIR / f"wait6579_ev_cohort_{target_date}.json"
    payload = _load_json(path)
    candidates = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    if not candidates:
        candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    rows: list[dict[str, Any]] = []
    for item in candidates[:500]:
        if not isinstance(item, dict):
            continue
        labels = {
            "mfe_10m_pct": item.get("mfe_10m_pct"),
            "mae_10m_pct": item.get("mae_10m_pct"),
            "close_10m_pct": item.get("close_10m_pct"),
            "profit_rate": item.get("expected_ev_pct"),
        }
        rows.append(
            {
                "candidate_id": item.get("candidate_id") or item.get("record_id") or item.get("stock_code"),
                "stock_code": item.get("stock_code"),
                "event_time": item.get("event_time") or item.get("observed_at"),
                "stage": "entry",
                "source_stage": "wait6579_ev_cohort",
                "runtime_features": {
                    "ai_score": item.get("ai_score"),
                    "buy_pressure": item.get("buy_pressure"),
                    "tick_accel": item.get("tick_accel"),
                    "micro_vwap_bp": item.get("micro_vwap_bp"),
                    "latency_state": item.get("latency_state"),
                    "fixed_threshold_contract_role": "baseline_prior",
                },
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev("entry", labels),
                "outcome_joined": True,
                "actual_order_submitted": False,
                "source": "wait6579_ev_cohort",
            }
        )
    return rows, {"artifact": str(path) if path.exists() else None, "rows": len(rows)}


def _boolish_false(value: Any) -> bool:
    return str(value).strip().lower() in {"", "0", "false", "none", "no"}


def _load_scalp_sim_submit_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    labels_by_key = _load_sim_post_sell_label_map(target_date)
    submit_priority = {
        "scalp_sim_entry_submit_revalidation_block": 0,
        "scalp_sim_pre_submit_liquidity_guard_would_block": 1,
        "scalp_sim_pre_submit_overbought_guard_would_block": 2,
        "scalp_sim_pre_submit_liquidity_guard_unknown": 3,
        "scalp_sim_entry_submit_revalidation_warning": 4,
        "scalp_sim_buy_order_assumed_filled": 5,
        "scalp_sim_buy_order_virtual_pending": 6,
        "scalp_sim_pre_submit_liquidity_guard_would_pass": 7,
        "scalp_sim_pre_submit_overbought_guard_would_pass": 8,
    }
    submit_events: dict[str, dict[str, Any]] = {}
    completed_events: dict[str, dict[str, Any]] = {}
    stage_counts: Counter[str] = Counter()
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage") or "")
        fields = _scalp_sim_fields(item)
        if not _is_scalp_sim_event(stage, fields):
            continue
        sim_record_id = str(fields.get("sim_record_id") or "").strip()
        if not sim_record_id:
            continue
        if stage == "scalp_sim_sell_order_assumed_filled":
            completed_events[sim_record_id] = item
        if stage not in SCALP_SIM_SUBMIT_STAGES:
            continue
        stage_counts[stage] += 1
        current = submit_events.get(sim_record_id)
        if current is None or submit_priority.get(stage, 99) < submit_priority.get(str(current.get("stage") or ""), 99):
            submit_events[sim_record_id] = item

    rows: list[dict[str, Any]] = []
    joined_count = 0
    for sim_record_id, event in sorted(submit_events.items(), key=lambda item: str(item[1].get("emitted_at") or "")):
        fields = _scalp_sim_fields(event)
        labels = labels_by_key.get(sim_record_id) or labels_by_key.get(str(fields.get("entry_adm_candidate_id") or ""))
        if not labels:
            labels = _sim_labels_from_completed_event(completed_events.get(sim_record_id))
        outcome_joined = bool(labels)
        joined_count += int(outcome_joined)
        rows.append(
            {
                "candidate_id": fields.get("entry_adm_candidate_id") or sim_record_id,
                "stock_code": event.get("stock_code"),
                "event_time": event.get("emitted_at"),
                "stage": "submit",
                "source_stage": event.get("stage"),
                "runtime_features": {
                    "actual_order_submitted": fields.get("actual_order_submitted"),
                    "broker_order_forbidden": fields.get("broker_order_forbidden"),
                    "decision_authority": fields.get("decision_authority"),
                    "runtime_effect": fields.get("runtime_effect"),
                    "ai_score": fields.get("scalp_sim_candidate_window_original_score") or fields.get("ai_score"),
                    "chosen_action": fields.get("scalp_sim_candidate_window_original_action") or fields.get("ai_action"),
                    "entry_submit_revalidation_warning": fields.get("entry_submit_revalidation_warning"),
                    "entry_submit_revalidation_block": fields.get("entry_submit_revalidation_block"),
                    "quote_age_ms": fields.get("quote_age_at_submit_ms"),
                    "best_bid": fields.get("best_bid") or fields.get("best_bid_at_submit"),
                    "best_ask": fields.get("best_ask") or fields.get("best_ask_at_submit"),
                    "resolved_order_price": fields.get("resolved_order_price") or fields.get("submitted_order_price"),
                    "would_limit_fill": fields.get("would_limit_fill"),
                    "qty": fields.get("qty"),
                    "limit_price": fields.get("limit_price"),
                    "curr_price": fields.get("curr_price") or fields.get("mark_price_at_submit"),
                    "price_resolution_bucket": fields.get("resolution_reason"),
                    "liquidity_guard_action": fields.get("sim_pre_submit_liquidity_guard_action"),
                    "liquidity_guard_reason": fields.get("sim_pre_submit_liquidity_reason"),
                    "sim_pre_submit_liquidity_guard_action": fields.get("sim_pre_submit_liquidity_guard_action"),
                    "sim_pre_submit_liquidity_reason": fields.get("sim_pre_submit_liquidity_reason"),
                    "sim_liquidity_value": fields.get("sim_liquidity_value"),
                    "sim_min_liquidity": fields.get("sim_min_liquidity"),
                    "liquidity_bucket": fields.get("liquidity_bucket"),
                    "liquidity_risk_state": fields.get("liquidity_risk_state"),
                    "liquidity_reason": fields.get("liquidity_reason"),
                    "liquidity_gate_action": fields.get("liquidity_gate_action"),
                    "overbought_guard_action": fields.get("sim_pre_submit_overbought_guard_action"),
                    "overbought_guard_reason": fields.get("sim_pre_submit_overbought_reason"),
                    "sim_pre_submit_overbought_guard_action": fields.get("sim_pre_submit_overbought_guard_action"),
                    "sim_pre_submit_overbought_reason": fields.get("sim_pre_submit_overbought_reason"),
                    "sim_overbought_risk_state": fields.get("sim_overbought_risk_state"),
                    "sim_overbought_risk_bucket": fields.get("sim_overbought_risk_bucket"),
                    "overbought_bucket": fields.get("overbought_bucket"),
                    "overbought_risk_state": fields.get("overbought_risk_state"),
                    "overbought_risk_bucket": fields.get("overbought_risk_bucket"),
                    "overbought_gate_action": fields.get("overbought_gate_action"),
                    "latency_state": fields.get("sim_latency_state") or fields.get("latency_state"),
                    "latency_reason": fields.get("sim_latency_danger_reasons") or fields.get("reason"),
                    "price_below_bid_bps": fields.get("sim_price_below_bid_bps") or fields.get("price_below_bid_bps"),
                    "fixed_threshold_contract_role": "bounded_tunable",
                    "sim_record_id": sim_record_id,
                },
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev("submit", labels),
                "outcome_joined": outcome_joined,
                "actual_order_submitted": not _boolish_false(fields.get("actual_order_submitted")),
                "source": "scalp_sim_entry_submit_pipeline_events",
            }
        )
    return rows, {
        "artifact": str(path) if path.exists() else None,
        "rows": len(rows),
        "joined_rows": joined_count,
        "stage_counts": dict(sorted(stage_counts.items())),
    }


def _load_scalp_sim_holding_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    labels_by_key = _load_sim_post_sell_label_map(target_date)
    holding_events: dict[str, dict[str, Any]] = {}
    completed_events: dict[str, dict[str, Any]] = {}
    stage_counts: Counter[str] = Counter()
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage") or "")
        fields = _scalp_sim_fields(item)
        if not _is_scalp_sim_event(stage, fields):
            continue
        sim_record_id = str(fields.get("sim_record_id") or "").strip()
        if not sim_record_id:
            continue
        if stage == "scalp_sim_sell_order_assumed_filled":
            completed_events[sim_record_id] = item
        if stage != SCALP_SIM_HOLDING_STAGE:
            continue
        stage_counts[stage] += 1
        holding_events.setdefault(sim_record_id, item)

    rows: list[dict[str, Any]] = []
    joined_count = 0
    for sim_record_id, event in sorted(holding_events.items(), key=lambda item: str(item[1].get("emitted_at") or "")):
        fields = _scalp_sim_fields(event)
        labels = labels_by_key.get(sim_record_id) or labels_by_key.get(str(fields.get("entry_adm_candidate_id") or ""))
        if not labels:
            labels = _sim_labels_from_completed_event(completed_events.get(sim_record_id))
        outcome_joined = bool(labels)
        joined_count += int(outcome_joined)
        rows.append(
            {
                "candidate_id": fields.get("entry_adm_candidate_id") or sim_record_id,
                "stock_code": event.get("stock_code"),
                "event_time": event.get("emitted_at"),
                "stage": "holding",
                "source_stage": event.get("stage"),
                "runtime_features": {
                    "actual_order_submitted": fields.get("actual_order_submitted"),
                    "broker_order_forbidden": fields.get("broker_order_forbidden"),
                    "decision_authority": fields.get("decision_authority"),
                    "runtime_effect": fields.get("runtime_effect"),
                    "ai_score": fields.get("scalp_sim_candidate_window_original_score") or fields.get("ai_score"),
                    "chosen_action": fields.get("scalp_sim_candidate_window_original_action"),
                    "qty": fields.get("requested_qty") or fields.get("qty"),
                    "limit_price": fields.get("assumed_fill_price"),
                    "curr_price": fields.get("assumed_fill_price"),
                    "would_limit_fill": fields.get("would_limit_fill"),
                    "source_quality_block_reason": fields.get("scalp_sim_candidate_window_blocked_reason"),
                    "fixed_threshold_contract_role": "bounded_tunable",
                    "sim_record_id": sim_record_id,
                },
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev("holding", labels),
                "outcome_joined": outcome_joined,
                "actual_order_submitted": not _boolish_false(fields.get("actual_order_submitted")),
                "source": "scalp_sim_holding_pipeline_events",
            }
        )
    return rows, {
        "artifact": str(path) if path.exists() else None,
        "rows": len(rows),
        "joined_rows": joined_count,
        "stage_counts": dict(sorted(stage_counts.items())),
    }


def _load_scalp_sim_scale_in_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    positions: dict[str, dict[str, Any]] = defaultdict(lambda: {"events": [], "scale_events": [], "completed": None})
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage") or "")
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        sim_record_id = fields.get("sim_record_id")
        if not sim_record_id:
            continue
        is_scalp_sim = stage.startswith("scalp_sim_") or fields.get("simulation_book") == "scalp_ai_buy_all"
        if not is_scalp_sim:
            continue
        position = positions[str(sim_record_id)]
        position["events"].append(item)
        if stage in {"scalp_sim_scale_in_order_assumed_filled", "scalp_sim_scale_in_order_unfilled"}:
            position["scale_events"].append(item)
        if stage == "scalp_sim_sell_order_assumed_filled":
            position["completed"] = item

    rows: list[dict[str, Any]] = []
    filled_count = 0
    unfilled_count = 0
    for sim_record_id, position in positions.items():
        completed = position.get("completed") if isinstance(position.get("completed"), dict) else None
        completed_fields = completed.get("fields") if completed and isinstance(completed.get("fields"), dict) else {}
        final_profit = _safe_float(completed_fields.get("profit_rate"), None)
        for scale_event in position.get("scale_events") or []:
            stage = str(scale_event.get("stage") or "")
            fields = scale_event.get("fields") if isinstance(scale_event.get("fields"), dict) else {}
            is_filled = stage == "scalp_sim_scale_in_order_assumed_filled"
            filled_count += int(is_filled)
            unfilled_count += int(not is_filled)
            first_add_at = str(scale_event.get("emitted_at") or "")
            post_add_values: list[float] = []
            for event in position.get("events") or []:
                if str(event.get("emitted_at") or "") < first_add_at:
                    continue
                event_fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
                for key in ("profit_rate", "trigger_profit_rate"):
                    value = _safe_float(event_fields.get(key), None)
                    if value is not None:
                        post_add_values.append(value)
            labels = {
                "profit_rate": final_profit,
                "exit_rule": completed_fields.get("exit_rule"),
                "mfe_10m_pct": max(post_add_values) if post_add_values else None,
                "mae_10m_pct": min(post_add_values) if post_add_values else None,
                "close_10m_pct": final_profit,
            }
            rows.append(
                {
                    "candidate_id": fields.get("ord_no") or f"{sim_record_id}:{scale_event.get('emitted_at')}",
                    "stock_code": scale_event.get("stock_code"),
                    "event_time": scale_event.get("emitted_at"),
                    "stage": "scale_in",
                    "source_stage": stage,
                    "runtime_features": {
                        "add_type": fields.get("add_type"),
                        "qty": fields.get("qty"),
                        "limit_price": fields.get("limit_price"),
                        "curr_price": fields.get("curr_price"),
                        "best_bid": fields.get("best_bid"),
                        "best_ask": fields.get("best_ask"),
                        "actual_order_submitted": fields.get("actual_order_submitted"),
                        "broker_order_forbidden": fields.get("broker_order_forbidden"),
                        "fixed_threshold_contract_role": "bounded_tunable",
                        "scale_in_fill_observed": is_filled,
                    },
                    "labels": labels,
                    "stage_ev_composite_pct": _stage_ev("scale_in", labels),
                    "outcome_joined": completed is not None,
                    "actual_order_submitted": not _boolish_false(fields.get("actual_order_submitted")),
                    "source": "scalp_sim_scale_in_pipeline_events",
                }
            )
    return rows, {
        "artifact": str(path) if path.exists() else None,
        "rows": len(rows),
        "filled_events": filled_count,
        "unfilled_events": unfilled_count,
    }


def _scale_in_arm_from_fields(stage: str, fields: dict[str, Any]) -> str:
    arm = str(fields.get("scale_in_arm") or fields.get("add_type") or fields.get("scale_in_action_type") or "").upper()
    if arm in {"AVG_DOWN", "PYRAMID"}:
        return arm
    chosen = str(fields.get("chosen_action") or "").lower()
    rejected = str(fields.get("rejected_actions") or "").lower()
    reason = str(fields.get("blocked_reason") or fields.get("reason") or "").lower()
    if "pyramid" in "|".join([stage.lower(), chosen, rejected, reason]):
        return "PYRAMID"
    if "avg_down" in rejected or "reversal" in stage.lower() or "reversal" in reason:
        return "AVG_DOWN"
    profit = _safe_float(fields.get("profit_rate"), None)
    if profit is not None and profit >= 0:
        return "PYRAMID"
    return "AVG_DOWN"


def _scale_in_blocker_namespace(stage: str, fields: dict[str, Any], arm: str) -> str:
    namespace = str(fields.get("scale_in_blocker_namespace") or "").strip().upper()
    if namespace:
        return namespace
    if stage == "scale_in_price_guard_block":
        return "PRICE_GUARD"
    if stage == "scale_in_qty_block":
        return "QTY_GUARD"
    if "hold_sec_out_of_range" in str(fields.get("blocked_reason") or fields.get("reason") or ""):
        return "AVG_DOWN_ONLY"
    return arm or "NONE"


def _load_scale_in_attribution_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    source_stages = {
        "stat_action_decision_snapshot",
        "pyramid_blocked_reason",
        "scale_in_arm_blocked",
        "reversal_add_blocked_reason",
        "reversal_add_gate_blocked",
        "scale_in_price_guard_block",
        "scale_in_qty_block",
    }
    rows: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    arm_counts: Counter[str] = Counter()
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        source_stage = str(item.get("stage") or "")
        if source_stage not in source_stages:
            continue
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        chosen = str(fields.get("chosen_action") or "")
        action_type = str(fields.get("scale_in_action_type") or fields.get("add_type") or "")
        rejected = str(fields.get("rejected_actions") or "")
        if source_stage == "stat_action_decision_snapshot" and not (
            chosen in {"avg_down_wait", "pyramid_wait"}
            or action_type in {"AVG_DOWN", "PYRAMID"}
            or "avg_down_wait" in rejected
            or "pyramid_wait" in rejected
        ):
            continue
        arm = _scale_in_arm_from_fields(source_stage, fields)
        namespace = _scale_in_blocker_namespace(source_stage, fields, arm)
        reason = (
            fields.get("scale_in_blocker_reason")
            or fields.get("blocked_reason")
            or fields.get("gate_reason")
            or fields.get("reason")
            or fields.get("scale_in_action_reason")
            or "-"
        )
        profit = _safe_float(fields.get("profit_rate"), None)
        peak = _safe_float(fields.get("peak_profit"), None)
        labels = {
            "profit_rate": profit,
            "mfe_10m_pct": peak if peak is not None else profit,
            "mae_10m_pct": profit,
            "close_10m_pct": profit,
        }
        runtime_features = {
            "add_type": arm,
            "scale_in_arm": arm,
            "scale_in_blocker_namespace": namespace,
            "scale_in_blocker_reason": reason,
            "chosen_action": chosen,
            "profit_rate_live": profit,
            "peak_profit": peak,
            "held_sec": fields.get("held_sec"),
            "ai_score": fields.get("current_ai_score") or fields.get("ai_score"),
            "ai_score_source": fields.get("ai_score_source") or "-",
            "supply_pass_count": fields.get("supply_pass_count"),
            "price_guard_reason": fields.get("reason") if source_stage == "scale_in_price_guard_block" else None,
            "qty_reason": fields.get("reason") if source_stage == "scale_in_qty_block" else None,
            "source_quality_block_reason": reason,
            "actual_order_submitted": fields.get("actual_order_submitted", False),
            "broker_order_forbidden": fields.get("broker_order_forbidden", True),
            "fixed_threshold_contract_role": "bounded_tunable",
            "time_bucket": fields.get("time_bucket"),
            "runtime_effect": False,
            "decision_authority": fields.get("decision_authority") or "scale_in_attribution_source_only",
        }
        candidate_id = (
            fields.get("candidate_id")
            or fields.get("sim_record_id")
            or item.get("record_id")
            or f"{item.get('stock_code')}:{source_stage}:{item.get('emitted_at')}"
        )
        rows.append(
            {
                "candidate_id": candidate_id,
                "stock_code": item.get("stock_code"),
                "event_time": item.get("emitted_at"),
                "stage": "scale_in",
                "source_stage": source_stage,
                "runtime_features": runtime_features,
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev("scale_in", labels),
                "outcome_joined": profit is not None,
                "actual_order_submitted": (
                    False
                    if fields.get("actual_order_submitted") is None
                    else not _boolish_false(fields.get("actual_order_submitted"))
                ),
                "source": "scale_in_attribution_pipeline_events",
            }
        )
        stage_counts[source_stage] += 1
        arm_counts[arm] += 1
    return rows, {
        "artifact": str(path) if path.exists() else None,
        "rows": len(rows),
        "stage_counts": dict(sorted(stage_counts.items())),
        "arm_counts": dict(sorted(arm_counts.items())),
        "decision_authority": "scale_in_attribution_source_only",
    }


def _load_scalp_sim_overnight_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    rows: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        source_stage = str(item.get("stage") or "")
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        if source_stage not in {
            "scalp_sim_overnight_decision",
            "scalp_sim_overnight_hold",
            "scalp_sim_overnight_sell_today",
            "scalp_sim_sell_order_assumed_filled",
        }:
            continue
        if source_stage == "scalp_sim_sell_order_assumed_filled" and fields.get("exit_rule") != "scalp_sim_overnight_sell_today":
            continue
        if fields.get("simulation_book") != "scalp_ai_buy_all":
            continue
        stage_counts[source_stage] += 1
        matrix_stage = "exit" if source_stage in {"scalp_sim_overnight_sell_today", "scalp_sim_sell_order_assumed_filled"} else "holding"
        profit = _safe_float(fields.get("profit_rate"), None)
        labels = {
            "profit_rate": profit,
            "exit_rule": fields.get("exit_rule"),
            "sell_today_realized_profit_pct": profit if matrix_stage == "exit" else None,
            "next_day_open_gap_pct": fields.get("next_day_open_gap_pct"),
            "next_day_mfe_pct": fields.get("next_day_mfe_pct"),
            "next_day_mae_pct": fields.get("next_day_mae_pct"),
            "next_day_close_pct": fields.get("next_day_close_pct"),
            "mfe_10m_pct": fields.get("next_day_mfe_pct"),
            "mae_10m_pct": fields.get("next_day_mae_pct"),
            "close_10m_pct": fields.get("next_day_close_pct"),
            "final_realized_exit_pct": fields.get("final_realized_exit_pct"),
        }
        rows.append(
            {
                "candidate_id": fields.get("sim_record_id") or item.get("stock_code"),
                "stock_code": item.get("stock_code"),
                "event_time": item.get("emitted_at"),
                "stage": matrix_stage,
                "source_stage": source_stage,
                "runtime_features": {
                    "ai_score": fields.get("last_holding_ai_score"),
                    "ai_action": fields.get("last_holding_ai_action"),
                    "profit_rate_live": fields.get("profit_rate_live"),
                    "peak_profit": fields.get("peak_profit"),
                    "held_sec": fields.get("held_sec"),
                    "curr_price": fields.get("current_price"),
                    "best_bid": fields.get("best_bid"),
                    "best_ask": fields.get("best_ask"),
                    "overnight_action": fields.get("ai_action"),
                    "overnight_confidence": fields.get("ai_confidence"),
                    "overnight_price_source": fields.get("current_price_source"),
                    "overnight_status": "SELL_TODAY" if matrix_stage == "exit" else "HOLD_OVERNIGHT",
                    "source_quality_gate": fields.get("source_quality_gate"),
                    "metric_role": fields.get("metric_role"),
                    "openai_model": fields.get("openai_model"),
                    "openai_transport_mode": fields.get("openai_transport_mode"),
                    "bedrock_shadow_route_mode": fields.get("bedrock_shadow_route_mode"),
                    "actual_order_submitted": fields.get("actual_order_submitted"),
                    "broker_order_forbidden": fields.get("broker_order_forbidden"),
                    "fixed_threshold_contract_role": "bounded_tunable",
                },
                "labels": labels,
                "stage_ev_composite_pct": _stage_ev(matrix_stage, labels),
                "outcome_joined": matrix_stage == "exit" and profit is not None,
                "actual_order_submitted": not _boolish_false(fields.get("actual_order_submitted")),
                "source": "scalp_sim_overnight_pipeline_events",
            }
        )
    return rows, {
        "artifact": str(path) if path.exists() else None,
        "rows": len(rows),
        "stage_counts": dict(sorted(stage_counts.items())),
    }


def _load_scalp_sim_panic_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    source_stages = {
        "scalp_sim_panic_bottoming_entry_allowed",
        "scalp_sim_panic_level1_entry_observed",
        "scalp_sim_panic_entry_blocked",
        "scalp_sim_panic_scale_in_blocked",
        "scalp_sim_partial_sell_order_assumed_filled",
        "scalp_sim_panic_context_warning",
        "scalp_sim_euphoria_context_noop",
        "scalp_sim_euphoria_entry_blocked",
        "scalp_sim_euphoria_chase_entry_blocked",
        "scalp_sim_euphoria_retest_starter_allowed",
        "scalp_sim_euphoria_level1_starter_observed",
        "scalp_sim_euphoria_scale_in_blocked",
        "scalp_sim_euphoria_partial_profit_assumed_filled",
        "scalp_sim_euphoria_action_deduped",
        "scalp_sim_sell_order_assumed_filled",
    }
    rows: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    for item in _iter_jsonl(path) or []:
        if not isinstance(item, dict):
            continue
        source_stage = str(item.get("stage") or "")
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        if source_stage not in source_stages:
            continue
        if source_stage == "scalp_sim_sell_order_assumed_filled" and fields.get("exit_rule") not in {
            "scalp_sim_panic_lifecycle_full_exit",
            "scalp_sim_euphoria_exit_on_reversal",
        }:
            continue
        if fields.get("simulation_book") != "scalp_ai_buy_all":
            continue
        stage_counts[source_stage] += 1
        if source_stage in {
            "scalp_sim_panic_entry_blocked",
            "scalp_sim_panic_bottoming_entry_allowed",
            "scalp_sim_panic_level1_entry_observed",
            "scalp_sim_euphoria_entry_blocked",
            "scalp_sim_euphoria_chase_entry_blocked",
            "scalp_sim_euphoria_retest_starter_allowed",
            "scalp_sim_euphoria_level1_starter_observed",
        }:
            matrix_stage = "entry"
        elif source_stage in {"scalp_sim_panic_scale_in_blocked", "scalp_sim_euphoria_scale_in_blocked"}:
            matrix_stage = "scale_in"
        else:
            matrix_stage = "exit"
        profit = _safe_float(fields.get("profit_rate") or fields.get("realized_profit_rate"), None)
        exclude_from_ev = bool(fields.get("exclude_from_ev"))
        labels = {
            "profit_rate": profit,
            "exit_rule": fields.get("exit_rule"),
            "mfe_10m_pct": profit,
            "mae_10m_pct": profit,
            "close_10m_pct": profit,
        } if not exclude_from_ev else {"exit_rule": fields.get("exit_rule")}
        runtime_features = {
            "ai_score": fields.get("ai_score") or fields.get("current_ai_score"),
            "actual_order_submitted": fields.get("actual_order_submitted"),
            "broker_order_forbidden": fields.get("broker_order_forbidden"),
            "source_family": fields.get("source_family"),
            "decision_family": fields.get("decision_family"),
            "family_type": fields.get("family_type"),
            "live_selectable": fields.get("live_selectable"),
            "preopen_apply_allowed": fields.get("preopen_apply_allowed"),
            "env_apply_allowed": fields.get("env_apply_allowed"),
            "threshold_env_mutation_allowed": fields.get("threshold_env_mutation_allowed"),
            "real_order_allowed": fields.get("real_order_allowed"),
            "risk_context_owner": fields.get("risk_context_owner"),
            "risk_direction": fields.get("risk_direction"),
            "action_namespace": fields.get("action_namespace"),
            "risk_regime_context_status": fields.get("risk_regime_context_status"),
            "risk_regime_level": fields.get("risk_regime_level"),
            "risk_regime_reason": fields.get("risk_regime_reason"),
            "risk_regime_epoch_id": fields.get("risk_regime_epoch_id"),
            "risk_regime_source_files": fields.get("risk_regime_source_files"),
            "runtime_effect": fields.get("runtime_effect"),
            "decision_authority": fields.get("decision_authority"),
            "profit_rate_live": fields.get("trigger_profit_rate") or fields.get("profit_rate"),
            "peak_profit": fields.get("peak_profit"),
            "held_sec": fields.get("held_sec"),
            "curr_price": fields.get("curr_price"),
            "best_bid": fields.get("best_bid"),
            "best_ask": fields.get("best_ask"),
            "panic_context_status": fields.get("panic_context_status"),
            "panic_level": fields.get("panic_level"),
            "panic_level_reason": fields.get("panic_level_reason"),
            "panic_epoch_id": fields.get("panic_epoch_id"),
            "panic_lifecycle_action_id": fields.get("panic_lifecycle_action_id"),
            "risk_regime_context_owner": fields.get("risk_regime_context_owner"),
            "market_regime": fields.get("market_regime"),
            "market_regime_continuous_score": fields.get("market_regime_continuous_score"),
            "market_regime_continuous_label": fields.get("market_regime_continuous_label"),
            "market_regime_component_scores": fields.get("market_regime_component_scores"),
            "swing_entry_recovery_gate_score": fields.get("swing_entry_recovery_gate_score"),
            "market_regime_score_version": fields.get("market_regime_score_version"),
            "market_regime_source_quality": fields.get("market_regime_source_quality"),
            "symbol_regime": fields.get("symbol_regime"),
            "panic_bottoming_entry_allowed": fields.get("panic_bottoming_entry_allowed"),
            "panic_bottoming_entry_reason": fields.get("panic_bottoming_entry_reason"),
            "panic_bottoming_arm": fields.get("panic_bottoming_arm"),
            "liquidity_state": fields.get("liquidity_state"),
            "fill_quality": fields.get("fill_quality"),
            "quote_quality_state": fields.get("quote_quality_state"),
            "assumed_slippage_bps": fields.get("assumed_slippage_bps"),
            "euphoria_context_status": fields.get("euphoria_context_status"),
            "euphoria_risk_level": fields.get("euphoria_risk_level"),
            "euphoria_risk_mode": fields.get("euphoria_risk_mode"),
            "euphoria_level_reason": fields.get("euphoria_level_reason"),
            "euphoria_epoch_id": fields.get("euphoria_epoch_id"),
            "euphoria_source_quality": fields.get("euphoria_source_quality"),
            "euphoria_action_id": fields.get("euphoria_action_id"),
            "euphoria_action_type": fields.get("euphoria_action_type"),
            "chase_risk": fields.get("chase_risk"),
            "retest_confirmed": fields.get("retest_confirmed"),
            "profit_locked": fields.get("profit_locked"),
            "runner_mode": fields.get("runner_mode"),
            "exhaustion_risk": fields.get("exhaustion_risk"),
            "reversal_signal": fields.get("reversal_signal"),
            "exclude_from_ev": fields.get("exclude_from_ev"),
            "source_quality_gate_scope": fields.get("source_quality_gate_scope"),
            "real_gate_allowed": fields.get("real_gate_allowed"),
            "pre_submit_gate_allowed": fields.get("pre_submit_gate_allowed"),
            "exclude_from_live_approval": fields.get("exclude_from_live_approval"),
            "fixed_threshold_contract_role": "bounded_tunable",
        }
        runtime_features = {key: value for key, value in runtime_features.items() if value is not None}
        rows.append(
            {
                "candidate_id": fields.get("panic_lifecycle_action_id")
                or fields.get("sim_record_id")
                or f"{item.get('stock_code')}:{item.get('emitted_at')}",
                "stock_code": item.get("stock_code"),
                "event_time": item.get("emitted_at"),
                "stage": matrix_stage,
                "source_stage": source_stage,
                "runtime_features": runtime_features,
                "labels": labels,
                "stage_ev_composite_pct": None if exclude_from_ev else _stage_ev(matrix_stage, labels),
                "outcome_joined": (profit is not None) and not exclude_from_ev,
                "actual_order_submitted": not _boolish_false(fields.get("actual_order_submitted")),
                "source": "scalp_sim_panic_pipeline_events",
            }
        )
    return rows, {
        "artifact": str(path) if path.exists() else None,
        "rows": len(rows),
        "stage_counts": dict(sorted(stage_counts.items())),
    }


def _policy_action_for(stage: str, rows: list[dict[str, Any]]) -> str:
    joined = [row for row in rows if row.get("stage_ev_composite_pct") is not None]
    if not joined:
        return "NO_CHANGE"
    avg_ev = sum(float(row["stage_ev_composite_pct"]) for row in joined) / len(joined)
    if stage in {"entry", "submit"}:
        if avg_ev >= PROMOTE_MIN_EV_PCT:
            return "BUY_DEFENSIVE" if stage == "entry" else "ALLOW_SUBMIT"
        if avg_ev < 0:
            return "WAIT_REQUOTE" if stage == "entry" else "NO_CHANGE"
    if stage in {"holding", "scale_in", "exit"}:
        if avg_ev >= PROMOTE_MIN_EV_PCT:
            return "HOLD" if stage != "scale_in" else "PYRAMID_BIAS"
        if avg_ev < 0:
            return "EXIT" if stage != "scale_in" else "NO_CHANGE"
    return "NO_CHANGE"


def _bucket_value(value: Any, fallback: str = "unknown") -> str:
    text = str(value if value is not None else "").strip()
    if not text or text in {"-", "None", "none", "null"}:
        return fallback
    return text


def _entry_score_band(value: Any) -> str:
    score = _safe_float(value, None)
    if score is None:
        return "score_unknown"
    if score < 60:
        return "score_lt60"
    if score < 63:
        return "score_60_62"
    if score < 66:
        return "score_63_65"
    if score < 70:
        return "score_66_69"
    return "score_70p"


def _stale_bucket(features: dict[str, Any]) -> str:
    warning = str(features.get("entry_submit_revalidation_warning") or "").strip()
    block = str(features.get("entry_submit_revalidation_block") or "").strip()
    if warning == "stale_context_or_quote" or block == "stale_context_or_quote":
        return "stale_context_or_quote"
    stale = str(features.get("stale_bucket") or "").strip()
    if stale and stale not in {"-", "None", "none", "null"}:
        return stale
    return "fresh_or_unflagged"


def _entry_bucket_features(row: dict[str, Any]) -> dict[str, str]:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    return {
        "score_band": _entry_score_band(features.get("ai_score")),
        "source_stage": _bucket_value(row.get("source_stage"), "source_unknown"),
        "chosen_action": _bucket_value(features.get("chosen_action"), "action_unknown"),
        "stale_bucket": _stale_bucket(features),
        "liquidity_bucket": _bucket_value(features.get("liquidity_bucket"), "liquidity_unknown"),
        "strength_bucket": _bucket_value(features.get("risk_context_bucket"), "strength_unknown"),
        "overbought_bucket": _bucket_value(features.get("overbought_bucket"), "overbought_unknown"),
        "time_bucket": _bucket_value(features.get("time_bucket"), "time_unknown"),
        "exit_rule": _bucket_value(labels.get("exit_rule"), "exit_unknown"),
    }


ENTRY_BUCKET_FIELD_MAP = {
    "score": "runtime_features.ai_score",
    "source": "source_stage",
    "liquidity": "runtime_features.liquidity_bucket",
    "overbought": "runtime_features.overbought_bucket",
    "time": "runtime_features.time_bucket",
    "stale": "runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block|runtime_features.stale_bucket",
    "score_band": "runtime_features.ai_score",
    "source_stage": "source_stage",
    "chosen_action": "runtime_features.chosen_action",
    "stale_bucket": "runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block|runtime_features.stale_bucket",
    "liquidity_bucket": "runtime_features.liquidity_bucket",
    "strength_bucket": "runtime_features.risk_context_bucket",
    "overbought_bucket": "runtime_features.overbought_bucket",
    "time_bucket": "runtime_features.time_bucket",
    "exit_rule": "labels.exit_rule",
    "combo_entry_spot": "runtime_features.ai_score|source_stage|runtime_features.stale_bucket|runtime_features.liquidity_bucket|runtime_features.overbought_bucket|runtime_features.time_bucket",
}


SCALE_IN_BUCKET_FIELD_MAP = {
    "arm": "runtime_features.scale_in_arm|runtime_features.add_type",
    "blocker_namespace": "runtime_features.scale_in_blocker_namespace",
    "blocker_reason": "runtime_features.scale_in_blocker_reason|runtime_features.source_quality_block_reason",
    "profit_band": "runtime_features.profit_rate_live|labels.profit_rate",
    "peak_profit_band": "runtime_features.peak_profit",
    "held_bucket": "runtime_features.held_sec",
    "ai_score_band": "runtime_features.ai_score",
    "ai_score_source": "runtime_features.ai_score_source",
    "supply_pass_bucket": "runtime_features.supply_pass_count",
    "price_guard_reason": "runtime_features.price_guard_reason",
    "qty_reason": "runtime_features.qty_reason",
    "time_bucket": "runtime_features.time_bucket",
}


SUBMIT_BUCKET_FIELD_MAP = {
    "submit_source_stage": "source_stage",
    "revalidation_state": "runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block",
    "quote_age_bucket": "runtime_features.quote_age_ms",
    "price_resolution_bucket": "runtime_features.price_resolution_bucket|runtime_features.resolved_order_price|runtime_features.limit_price",
    "would_limit_fill": "runtime_features.would_limit_fill",
    "actual_order_submitted": "runtime_features.actual_order_submitted|actual_order_submitted",
    "broker_order_forbidden": "runtime_features.broker_order_forbidden",
    "liquidity_guard_action": "runtime_features.liquidity_guard_action|runtime_features.sim_pre_submit_liquidity_guard_action",
    "liquidity_bucket": "runtime_features.liquidity_guard_reason|runtime_features.sim_pre_submit_liquidity_reason|runtime_features.sim_liquidity_value|runtime_features.sim_min_liquidity|runtime_features.liquidity_bucket",
    "overbought_guard_action": "runtime_features.overbought_guard_action|runtime_features.sim_pre_submit_overbought_guard_action",
    "overbought_bucket": "runtime_features.overbought_guard_reason|runtime_features.sim_pre_submit_overbought_reason|runtime_features.sim_overbought_risk_state|runtime_features.sim_overbought_risk_bucket|runtime_features.overbought_bucket",
    "latency_state": "runtime_features.latency_state",
    "latency_reason": "runtime_features.latency_reason",
    "price_below_bid_bucket": "runtime_features.price_below_bid_bps",
    "combo_submit_quality": "source_stage|runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block|runtime_features.quote_age_ms|runtime_features.would_limit_fill|runtime_features.actual_order_submitted|runtime_features.sim_pre_submit_liquidity_guard_action|runtime_features.sim_pre_submit_liquidity_reason|runtime_features.sim_pre_submit_overbought_guard_action|runtime_features.sim_pre_submit_overbought_reason|runtime_features.latency_state",
}


def _nested_present(row: dict[str, Any], path: str) -> bool:
    current: Any = row
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current.get(part)
    return current not in (None, "", "-", "None", "none", "null")


def _field_coverage(rows: list[dict[str, Any]], paths: str) -> dict[str, Any]:
    field_paths = [part for part in paths.split("|") if part]
    present = 0
    for row in rows:
        if any(_nested_present(row, path) for path in field_paths):
            present += 1
    total = len(rows)
    return {
        "source_fields": field_paths,
        "present_count": present,
        "sample_count": total,
        "coverage_rate": round(present / total, 4) if total else 0.0,
    }


def _unknown_taxonomy_context(
    *,
    bucket_type: str,
    bucket_key: str,
    rows: list[dict[str, Any]],
    joined_sample: int,
    field_map: dict[str, str],
) -> dict[str, Any]:
    if "unknown" not in str(bucket_key):
        return {
            "unknown_dimension_counts": {},
            "unknown_reason_counts": {},
            "source_field_coverage": {},
            "recommended_resolution": "none",
        }
    source_dimensions: list[str] = []
    if bucket_type.startswith("combo_") and "=" in bucket_key:
        for part in str(bucket_key).split("|"):
            if "=" not in part:
                continue
            dimension, value = part.split("=", 1)
            if "unknown" in value:
                source_dimensions.append(dimension)
    else:
        source_dimensions.append(bucket_type)
    source_field_coverage: dict[str, Any] = {}
    reason_counts: Counter[str] = Counter()
    for dimension in source_dimensions:
        source_path = field_map.get(dimension) or field_map.get(bucket_type) or dimension
        coverage = _field_coverage(rows, source_path)
        source_field_coverage[dimension] = coverage
        if joined_sample <= 0:
            reason = "join_gap"
        elif coverage["present_count"] <= 0:
            reason = "missing_source_field"
        elif coverage["coverage_rate"] < 1.0:
            reason = "pre_instrumentation"
        else:
            reason = "not_applicable"
        reason_counts[reason] += 1
    if reason_counts.get("join_gap"):
        recommended = "join_labels_before_bucket_decision"
    elif reason_counts.get("missing_source_field"):
        recommended = "emit_or_backfill_source_field"
    elif reason_counts.get("pre_instrumentation"):
        recommended = "keep_collecting_post_instrumentation"
    else:
        recommended = "mark_not_applicable_explicitly"
    return {
        "unknown_dimension_counts": dict(Counter(source_dimensions)),
        "unknown_reason_counts": dict(reason_counts),
        "source_field_coverage": source_field_coverage,
        "recommended_resolution": recommended,
    }


def _avg_label(rows: list[dict[str, Any]], key: str) -> float | None:
    values: list[float] = []
    for row in rows:
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        value = _safe_float(labels.get(key), None)
        if value is not None:
            values.append(float(value))
    return round(sum(values) / len(values), 4) if values else None


def _entry_bucket_row(bucket_type: str, bucket_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined = [row for row in rows if row.get("stage_ev_composite_pct") is not None]
    joined_sample = len(joined)
    ev_values = [float(row["stage_ev_composite_pct"]) for row in joined]
    profit_values = [
        _safe_float((row.get("labels") or {}).get("profit_rate"), None)
        for row in joined
        if isinstance(row.get("labels"), dict)
    ]
    valid_profit = [float(value) for value in profit_values if value is not None]
    avg_ev = round(sum(ev_values) / len(ev_values), 4) if ev_values else None
    avg_profit = round(sum(valid_profit) / len(valid_profit), 4) if valid_profit else None
    source_quality = (
        "pass"
        if len(rows) >= ENTRY_BUCKET_SAMPLE_FLOOR and joined_sample >= ENTRY_BUCKET_SAMPLE_FLOOR
        else "hold_sample"
    )
    if avg_ev is None:
        recommended_route = "hold_sample"
    elif source_quality != "pass":
        recommended_route = "hold_sample"
    elif avg_ev <= ENTRY_BUCKET_NEGATIVE_EV_PCT:
        recommended_route = "candidate_tighten_or_exclude"
    elif avg_ev >= ENTRY_BUCKET_POSITIVE_EV_PCT:
        recommended_route = "candidate_recovery_or_relax"
    else:
        recommended_route = "hold_no_edge"
    unknown_context = _unknown_taxonomy_context(
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        rows=rows,
        joined_sample=joined_sample,
        field_map=ENTRY_BUCKET_FIELD_MAP,
    )
    return {
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "sample": len(rows),
        "joined_sample": joined_sample,
        "join_rate": round(joined_sample / len(rows), 4) if rows else 0.0,
        "source_quality_gate": source_quality,
        "source_quality_adjusted_ev_pct": avg_ev,
        "equal_weight_avg_profit_pct": avg_profit,
        "diagnostic_win_rate": (
            round(sum(1 for value in valid_profit if value > 0) / len(valid_profit), 4)
            if valid_profit
            else None
        ),
        "mfe_10m_pct": _avg_label(joined, "mfe_10m_pct"),
        "mae_10m_pct": _avg_label(joined, "mae_10m_pct"),
        "close_10m_pct": _avg_label(joined, "close_10m_pct"),
        "mfe_30m_pct": _avg_label(joined, "mfe_30m_pct"),
        "mae_30m_pct": _avg_label(joined, "mae_30m_pct"),
        "close_30m_pct": _avg_label(joined, "close_30m_pct"),
        "mfe_60m_pct": _avg_label(joined, "mfe_60m_pct"),
        "mae_60m_pct": _avg_label(joined, "mae_60m_pct"),
        "close_60m_pct": _avg_label(joined, "close_60m_pct"),
        "recommended_route": recommended_route,
        **unknown_context,
        "decision_authority": "adm_weight_candidate_source_only",
        "runtime_effect": False,
        "forbidden_uses": [
            "single_bucket_buy_decision",
            "intraday_threshold_mutation",
            "broker_order_submit",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }


def _entry_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_rows = [row for row in rows if str(row.get("stage") or "") == "entry"]
    bucket_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in entry_rows:
        buckets = _entry_bucket_features(row)
        for bucket_type in (
            "score_band",
            "source_stage",
            "chosen_action",
            "stale_bucket",
            "liquidity_bucket",
            "strength_bucket",
            "overbought_bucket",
            "time_bucket",
            "exit_rule",
        ):
            bucket_groups[(bucket_type, buckets[bucket_type])].append(row)
        combo_key = "|".join(
            [
                f"score={buckets['score_band']}",
                f"source={buckets['source_stage']}",
                f"stale={buckets['stale_bucket']}",
                f"liquidity={buckets['liquidity_bucket']}",
                f"overbought={buckets['overbought_bucket']}",
                f"time={buckets['time_bucket']}",
            ]
        )
        bucket_groups[("combo_entry_spot", combo_key)].append(row)

    buckets = [
        _entry_bucket_row(bucket_type, bucket_key, subset)
        for (bucket_type, bucket_key), subset in bucket_groups.items()
    ]
    buckets.sort(
        key=lambda item: (
            str(item.get("bucket_type") or ""),
            -int(item.get("joined_sample") or 0),
            str(item.get("bucket_key") or ""),
        )
    )
    actionable = [
        item
        for item in buckets
        if item.get("source_quality_gate") == "pass"
        and item.get("recommended_route") in {"candidate_tighten_or_exclude", "candidate_recovery_or_relax"}
    ]
    approval_bucket_types = {
        "score_band",
        "source_stage",
        "stale_bucket",
        "liquidity_bucket",
        "strength_bucket",
        "overbought_bucket",
        "time_bucket",
        "combo_entry_spot",
    }

    def approval_eligible(item: dict[str, Any]) -> bool:
        bucket_type = str(item.get("bucket_type") or "")
        bucket_key = str(item.get("bucket_key") or "")
        if bucket_type not in approval_bucket_types:
            return False
        if "unknown" in bucket_key or "exit_unknown" in bucket_key or "action_unknown" in bucket_key:
            return False
        return int(item.get("joined_sample") or 0) >= ENTRY_BUCKET_PROMOTE_SAMPLE_FLOOR

    runtime_candidates = [
        {
            "candidate_id": f"entry_bucket_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "recommended_route": item.get("recommended_route"),
            "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
            "joined_sample": item.get("joined_sample"),
            "approval_required": True,
            "allowed_runtime_apply": False,
            "next_route": "threshold_cycle_runtime_approval_request_after_rolling_confirmation",
        }
        for idx, item in enumerate(actionable)
        if approval_eligible(item)
    ][:10]
    workorders = [
        {
            "workorder_id": f"entry_bucket_source_quality_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "reason": "bucket_has_edge_but_needs_rolling_or_feature_confirmation",
            "recommended_route": item.get("recommended_route"),
            "metric_role": "source_quality_gate",
            "implementation_status": "implemented",
            "implementation_provenance": {
                "source_field_coverage": item.get("source_field_coverage") or {},
                "unknown_reason_counts": item.get("unknown_reason_counts") or {},
                "recommended_resolution": item.get("recommended_resolution"),
            },
            "runtime_effect": False,
        }
        for idx, item in enumerate(actionable[:10])
    ]
    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "adm_ldm_entry_bucket_attribution_source_only",
        "runtime_effect": False,
        "window_policy": "daily_lifecycle_rows_plus_threshold_cycle_rolling_consumer",
        "sample_floor": ENTRY_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry row sample + joined outcome labels + no future label runtime input",
        "forbidden_uses": [
            "single_bucket_buy_decision",
            "intraday_threshold_mutation",
            "broker_order_submit",
            "provider_route_change",
            "bot_restart_trigger",
        ],
        "summary": {
            "entry_rows": len(entry_rows),
            "bucket_count": len(buckets),
            "actionable_bucket_count": len(actionable),
            "runtime_candidate_count": len(runtime_candidates),
            "workorder_count": len(workorders),
        },
        "buckets": buckets[:200],
        "runtime_approval_candidates": runtime_candidates,
        "code_improvement_workorders": workorders,
    }


def _quote_age_bucket(value: Any) -> str:
    age = _safe_float(value, None)
    if age is None:
        return "quote_age_unknown"
    if age < 1000:
        return "quote_age_lt1s"
    if age < 3000:
        return "quote_age_1_3s"
    if age < 10000:
        return "quote_age_3_10s"
    return "quote_age_10s_plus"


def _bool_bucket(value: Any, *, unknown: str) -> str:
    if value in (None, "", "-", "None", "none", "null"):
        return unknown
    return "true" if not _boolish_false(value) else "false"


def _submit_revalidation_state(features: dict[str, Any]) -> str:
    block = _bucket_value(features.get("entry_submit_revalidation_block"), "")
    if block:
        return f"block_{block}"
    warning = _bucket_value(features.get("entry_submit_revalidation_warning"), "")
    if warning:
        return f"warning_{warning}"
    return "ok_or_unflagged"


def _submit_liquidity_guard_action(features: dict[str, Any]) -> str:
    action = _bucket_value(
        features.get("liquidity_guard_action") or features.get("sim_pre_submit_liquidity_guard_action"),
        "",
    ).lower()
    if action in {"block", "blocked"}:
        return "would_block"
    if action in {"pass", "passed"}:
        return "would_pass"
    if action in {"unknown", "source_unknown"}:
        return "would_unknown"
    if action in {"would_block", "would_pass", "would_unknown"}:
        return action
    return "liquidity_guard_unknown"


def _submit_liquidity_bucket(features: dict[str, Any]) -> str:
    action = _submit_liquidity_guard_action(features)
    reason = _bucket_value(
        features.get("liquidity_guard_reason") or features.get("sim_pre_submit_liquidity_reason"),
        "",
    )
    if action == "would_block":
        return reason or "below_min_liquidity"
    if action == "would_pass" and reason == "liquidity_ok":
        return "liquidity_ok"
    if action == "would_pass" and reason == "liquidity_unknown":
        return "liquidity_unknown"
    if action == "would_unknown":
        return reason or "liquidity_unknown"
    explicit = _bucket_value(features.get("liquidity_bucket"), "")
    if explicit:
        return explicit
    value = _safe_float(features.get("sim_liquidity_value") or features.get("liquidity_value"), None)
    min_liquidity = _safe_float(features.get("sim_min_liquidity") or features.get("min_liquidity"), None)
    if value is None:
        return "liquidity_unknown"
    if min_liquidity is not None and value < min_liquidity:
        return "below_min_liquidity"
    return "liquidity_ok"


def _submit_overbought_guard_action(features: dict[str, Any]) -> str:
    action = _bucket_value(
        features.get("overbought_guard_action") or features.get("sim_pre_submit_overbought_guard_action"),
        "",
    ).lower()
    if action in {"block", "blocked"}:
        return "would_block"
    if action in {"pass", "passed"}:
        return "would_pass"
    if action in {"would_block", "would_pass"}:
        return action
    return "overbought_guard_unknown"


def _submit_overbought_bucket(features: dict[str, Any]) -> str:
    action = _submit_overbought_guard_action(features)
    reason = _bucket_value(
        features.get("overbought_guard_reason") or features.get("sim_pre_submit_overbought_reason"),
        "",
    )
    if action == "would_block":
        return reason or "pullback_or_rebreak_not_confirmed"
    if action == "would_pass" and reason == "overbought_ok":
        return "overbought_ok"
    if action == "would_pass" and reason == "overbought_unknown":
        return "overbought_unknown"
    explicit = _bucket_value(features.get("overbought_bucket") or features.get("sim_overbought_risk_bucket"), "")
    if explicit:
        return explicit
    state = _bucket_value(features.get("overbought_risk_state") or features.get("sim_overbought_risk_state"), "")
    if state in {"pullback_observed", "rebreak_candidate"}:
        return "overbought_ok"
    if state:
        return state
    return "overbought_unknown"


def _submit_latency_state(features: dict[str, Any]) -> str:
    return _bucket_value(features.get("latency_state"), "latency_unknown").lower()


def _submit_latency_reason(features: dict[str, Any]) -> str:
    return _bucket_value(features.get("latency_reason"), "latency_reason_unknown")


def _submit_price_below_bid_bucket(value: Any) -> str:
    bps = _safe_float(value, None)
    if bps is None:
        return "price_below_bid_unknown"
    if bps <= 0:
        return "not_below_bid"
    if bps <= 5:
        return "below_bid_0_5bps"
    if bps <= 20:
        return "below_bid_5_20bps"
    return "below_bid_20bps_plus"


def _submit_bucket_features(row: dict[str, Any]) -> dict[str, str]:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    return {
        "submit_source_stage": _bucket_value(row.get("source_stage"), "source_unknown"),
        "revalidation_state": _submit_revalidation_state(features),
        "quote_age_bucket": _quote_age_bucket(features.get("quote_age_ms")),
        "price_resolution_bucket": _bucket_value(
            features.get("price_resolution_bucket"),
            "price_resolution_unknown",
        ),
        "would_limit_fill": _bool_bucket(features.get("would_limit_fill"), unknown="would_limit_fill_unknown"),
        "actual_order_submitted": _bool_bucket(
            features.get("actual_order_submitted", row.get("actual_order_submitted")),
            unknown="actual_order_submitted_unknown",
        ),
        "broker_order_forbidden": _bool_bucket(
            features.get("broker_order_forbidden"),
            unknown="broker_order_forbidden_unknown",
        ),
        "liquidity_guard_action": _submit_liquidity_guard_action(features),
        "liquidity_bucket": _submit_liquidity_bucket(features),
        "overbought_guard_action": _submit_overbought_guard_action(features),
        "overbought_bucket": _submit_overbought_bucket(features),
        "latency_state": _submit_latency_state(features),
        "latency_reason": _submit_latency_reason(features),
        "price_below_bid_bucket": _submit_price_below_bid_bucket(features.get("price_below_bid_bps")),
    }


def _submit_bucket_row(bucket_type: str, bucket_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined = [row for row in rows if row.get("stage_ev_composite_pct") is not None]
    joined_sample = len(joined)
    ev_values = [float(row["stage_ev_composite_pct"]) for row in joined]
    avg_ev = round(sum(ev_values) / len(ev_values), 4) if ev_values else None
    source_quality = "pass" if len(rows) >= SUBMIT_BUCKET_SAMPLE_FLOOR else "hold_sample"
    unknown_context = _unknown_taxonomy_context(
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        rows=rows,
        joined_sample=joined_sample,
        field_map=SUBMIT_BUCKET_FIELD_MAP,
    )
    return {
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "sample": len(rows),
        "joined_sample": joined_sample,
        "join_rate": round(joined_sample / len(rows), 4) if rows else 0.0,
        "source_quality_gate": source_quality,
        "source_quality_adjusted_ev_pct": avg_ev,
        "recommended_route": "source_quality_workorder" if "unknown" in bucket_key else "keep_collecting",
        **unknown_context,
        "decision_authority": "adm_ldm_submit_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "broker_order_submit",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
            "hard_safety_override",
        ],
    }


def _submit_contract_gaps(submit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not submit_rows:
        return []
    gap_specs = [
        (
            "post_submit_contract_gap",
            "order_entry_post_submit_contract_gap_review",
            "runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block|runtime_features.quote_age_ms",
            "price_revalidation_or_submit_state_missing",
        ),
        (
            "broker_receipt_contract_gap",
            "order_entry_broker_receipt_contract_gap_review",
            "runtime_features.actual_order_submitted|actual_order_submitted",
            "broker_receipt_or_real_submit_flag_missing",
        ),
        (
            "fill_quality_contract_gap",
            "order_entry_fill_quality_contract_gap_review",
            "runtime_features.would_limit_fill|runtime_features.resolved_order_price|runtime_features.limit_price",
            "limit_fill_or_price_quality_missing",
        ),
        (
            "telegram_post_submit_contract_gap",
            "order_entry_telegram_post_submit_contract_gap_review",
            "runtime_features.actual_order_submitted|actual_order_submitted",
            "buy_telegram_must_be_bound_to_submitted_only",
        ),
    ]
    gaps: list[dict[str, Any]] = []
    for gap_type, workorder_id, paths, reason in gap_specs:
        coverage = _field_coverage(submit_rows, paths)
        if coverage["present_count"] <= 0:
            gaps.append(
                {
                    "gap_type": gap_type,
                    "workorder_id": workorder_id,
                    "bucket_type": gap_type,
                    "bucket_key": reason,
                    "reason": reason,
                    "source_field_coverage": coverage,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
    sim_submit_rows = []
    for row in submit_rows:
        runtime_features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
        if str(row.get("source_stage") or "") in SCALP_SIM_SUBMIT_STAGES or _bucket_value(
            runtime_features.get("sim_record_id"),
            "",
        ):
            sim_submit_rows.append(row)
    if sim_submit_rows:
        coverage = _field_coverage(
            sim_submit_rows,
            "runtime_features.sim_pre_submit_liquidity_guard_action|runtime_features.sim_pre_submit_liquidity_reason|runtime_features.sim_liquidity_value|runtime_features.sim_min_liquidity",
        )
        if coverage["present_count"] <= 0:
            gaps.append(
                {
                    "gap_type": "sim_pre_submit_guard_contract_gap",
                    "workorder_id": "order_entry_sim_submit_path_bucket_instrumentation",
                    "bucket_type": "sim_pre_submit_guard_contract_gap",
                    "bucket_key": "sim_pre_submit_guard_bucket_fields_missing",
                    "reason": "sim_pre_submit_guard_bucket_fields_missing",
                    "source_field_coverage": coverage,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
    return gaps


def _submit_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    submit_rows = [row for row in rows if str(row.get("stage") or "") == "submit"]
    bucket_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in submit_rows:
        buckets = _submit_bucket_features(row)
        for bucket_type in (
            "submit_source_stage",
            "revalidation_state",
            "quote_age_bucket",
            "price_resolution_bucket",
            "would_limit_fill",
            "actual_order_submitted",
            "broker_order_forbidden",
            "liquidity_guard_action",
            "liquidity_bucket",
            "overbought_guard_action",
            "overbought_bucket",
            "latency_state",
            "latency_reason",
            "price_below_bid_bucket",
        ):
            bucket_groups[(bucket_type, buckets[bucket_type])].append(row)
        combo_key = "|".join(
            [
                f"source={buckets['submit_source_stage']}",
                f"revalidation={buckets['revalidation_state']}",
                f"quote_age={buckets['quote_age_bucket']}",
                f"liquidity={buckets['liquidity_bucket']}",
                f"liquidity_guard={buckets['liquidity_guard_action']}",
                f"overbought={buckets['overbought_bucket']}",
                f"latency={buckets['latency_state']}",
                f"fill={buckets['would_limit_fill']}",
                f"submitted={buckets['actual_order_submitted']}",
            ]
        )
        bucket_groups[("combo_submit_quality", combo_key)].append(row)
    buckets = [
        _submit_bucket_row(bucket_type, bucket_key, subset)
        for (bucket_type, bucket_key), subset in bucket_groups.items()
    ]
    buckets.sort(
        key=lambda item: (
            str(item.get("bucket_type") or ""),
            -int(item.get("sample") or 0),
            str(item.get("bucket_key") or ""),
        )
    )
    contract_gaps = _submit_contract_gaps(submit_rows)
    workorders = [
        {
            "workorder_id": item["workorder_id"],
            "bucket_type": item["bucket_type"],
            "bucket_key": item["bucket_key"],
            "reason": item["reason"],
            "metric_role": "source_quality_gate",
            "implementation_status": "open",
            "implementation_provenance": {
                "source_field_coverage": item.get("source_field_coverage") or {},
                "recommended_resolution": "emit_or_backfill_submit_contract_field",
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for item in contract_gaps
    ]
    return {
        "metric_role": "submit_funnel_source_quality_gate",
        "decision_authority": "adm_ldm_submit_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "window_policy": "daily_lifecycle_submit_rows_plus_threshold_cycle_rolling_consumer",
        "sample_floor": SUBMIT_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "submit row sample + revalidation/broker/fill provenance + no runtime mutation",
        "forbidden_uses": [
            "broker_order_submit",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
            "hard_safety_override",
        ],
        "summary": {
            "submit_rows": len(submit_rows),
            "bucket_count": len(buckets),
            "contract_gap_count": len(contract_gaps),
            "workorder_count": len(workorders),
            "runtime_candidate_count": 0,
        },
        "buckets": buckets[:200],
        "runtime_approval_candidates": [],
        "code_improvement_workorders": workorders,
        "post_submit_contract_gaps": contract_gaps,
    }


def _numeric_band(value: Any, *, prefix: str, cuts: list[tuple[float, str]], unknown: str) -> str:
    number = _safe_float(value, None)
    if number is None:
        return unknown
    for upper, label in cuts:
        if number < upper:
            return f"{prefix}_{label}"
    return f"{prefix}_{cuts[-1][1]}_plus"


def _scale_in_bucket_features(row: dict[str, Any]) -> dict[str, str]:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    return {
        "arm": _bucket_value(features.get("scale_in_arm") or features.get("add_type"), "arm_unknown"),
        "blocker_namespace": _bucket_value(features.get("scale_in_blocker_namespace"), "blocker_namespace_unknown"),
        "blocker_reason": _bucket_value(features.get("scale_in_blocker_reason") or features.get("source_quality_block_reason"), "blocker_reason_unknown"),
        "profit_band": _numeric_band(
            features.get("profit_rate_live") if features.get("profit_rate_live") is not None else labels.get("profit_rate"),
            prefix="profit",
            cuts=[(-0.7, "lt_neg070"), (-0.1, "neg070_neg010"), (0.8, "neg010_pos080"), (1.5, "pos080_pos150"), (3.0, "pos150_pos300")],
            unknown="profit_unknown",
        ),
        "peak_profit_band": _numeric_band(
            features.get("peak_profit"),
            prefix="peak",
            cuts=[(0.0, "lt_zero"), (0.8, "zero_pos080"), (1.5, "pos080_pos150"), (3.0, "pos150_pos300")],
            unknown="peak_unknown",
        ),
        "held_bucket": _numeric_band(
            features.get("held_sec"),
            prefix="held",
            cuts=[(20, "lt020s"), (180, "020_180s"), (600, "180_600s"), (1800, "600_1800s")],
            unknown="held_unknown",
        ),
        "ai_score_band": _entry_score_band(features.get("ai_score")),
        "ai_score_source": _bucket_value(features.get("ai_score_source"), "ai_source_unknown"),
        "supply_pass_bucket": _numeric_band(
            features.get("supply_pass_count"),
            prefix="supply_pass",
            cuts=[(1, "0"), (2, "1"), (3, "2"), (4, "3")],
            unknown="supply_pass_unknown",
        ),
        "price_guard_reason": _bucket_value(features.get("price_guard_reason"), "price_guard_none"),
        "qty_reason": _bucket_value(features.get("qty_reason"), "qty_none"),
        "time_bucket": _bucket_value(features.get("time_bucket"), "time_unknown"),
    }


def _scale_in_bucket_row(bucket_type: str, bucket_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined = [row for row in rows if row.get("stage_ev_composite_pct") is not None]
    joined_sample = len(joined)
    ev_values = [float(row["stage_ev_composite_pct"]) for row in joined]
    profit_values = [
        _safe_float((row.get("labels") or {}).get("profit_rate"), None)
        for row in joined
        if isinstance(row.get("labels"), dict)
    ]
    valid_profit = [float(value) for value in profit_values if value is not None]
    avg_ev = round(sum(ev_values) / len(ev_values), 4) if ev_values else None
    avg_profit = round(sum(valid_profit) / len(valid_profit), 4) if valid_profit else None
    source_quality = (
        "pass"
        if len(rows) >= SCALE_IN_BUCKET_SAMPLE_FLOOR and joined_sample >= SCALE_IN_BUCKET_SAMPLE_FLOOR
        else "hold_sample"
    )
    if avg_ev is None or source_quality != "pass":
        recommended_route = "hold_sample"
    elif avg_ev <= SCALE_IN_BUCKET_NEGATIVE_EV_PCT:
        recommended_route = "candidate_tighten_or_exclude"
    elif avg_ev >= SCALE_IN_BUCKET_POSITIVE_EV_PCT:
        recommended_route = "candidate_recovery_or_relax"
    else:
        recommended_route = "hold_no_edge"
    unknown_context = _unknown_taxonomy_context(
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        rows=rows,
        joined_sample=joined_sample,
        field_map=SCALE_IN_BUCKET_FIELD_MAP,
    )
    return {
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "sample": len(rows),
        "joined_sample": joined_sample,
        "join_rate": round(joined_sample / len(rows), 4) if rows else 0.0,
        "source_quality_gate": source_quality,
        "source_quality_adjusted_ev_pct": avg_ev,
        "equal_weight_avg_profit_pct": avg_profit,
        "diagnostic_win_rate": (
            round(sum(1 for value in valid_profit if value > 0) / len(valid_profit), 4)
            if valid_profit
            else None
        ),
        "mfe_10m_pct": _avg_label(joined, "mfe_10m_pct"),
        "mae_10m_pct": _avg_label(joined, "mae_10m_pct"),
        "close_10m_pct": _avg_label(joined, "close_10m_pct"),
        "recommended_route": recommended_route,
        **unknown_context,
        "decision_authority": "adm_ldm_scale_in_bucket_attribution_source_only",
        "runtime_effect": False,
        "fixed_threshold_contract_role": "bounded_tunable",
    }


def _scale_in_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scale_rows = [row for row in rows if str(row.get("stage") or "") == "scale_in"]
    bucket_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scale_rows:
        buckets = _scale_in_bucket_features(row)
        for bucket_type, bucket_key in buckets.items():
            bucket_groups[(bucket_type, bucket_key)].append(row)

    buckets = [
        _scale_in_bucket_row(bucket_type, bucket_key, subset)
        for (bucket_type, bucket_key), subset in bucket_groups.items()
    ]
    buckets.sort(
        key=lambda item: (
            str(item.get("bucket_type") or ""),
            -int(item.get("joined_sample") or 0),
            str(item.get("bucket_key") or ""),
        )
    )
    actionable = [
        item
        for item in buckets
        if item.get("source_quality_gate") == "pass"
        and item.get("recommended_route") in {"candidate_tighten_or_exclude", "candidate_recovery_or_relax"}
    ]

    def approval_eligible(item: dict[str, Any]) -> bool:
        key = str(item.get("bucket_key") or "")
        if "unknown" in key:
            return False
        return int(item.get("joined_sample") or 0) >= SCALE_IN_BUCKET_PROMOTE_SAMPLE_FLOOR

    runtime_candidates = [
        {
            "candidate_id": f"scale_in_bucket_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "recommended_route": item.get("recommended_route"),
            "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
            "joined_sample": item.get("joined_sample"),
            "approval_required": True,
            "allowed_runtime_apply": False,
            "decision_authority": "adm_ldm_scale_in_bucket_attribution_source_only",
            "next_route": "threshold_cycle_runtime_approval_request_after_rolling_confirmation",
        }
        for idx, item in enumerate(actionable)
        if approval_eligible(item)
    ][:10]
    workorders = [
        {
            "workorder_id": f"scale_in_bucket_source_quality_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "reason": "scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation",
            "recommended_route": item.get("recommended_route"),
            "metric_role": "source_quality_gate",
            "implementation_status": "implemented",
            "implementation_provenance": {
                "source_field_coverage": item.get("source_field_coverage") or {},
                "unknown_reason_counts": item.get("unknown_reason_counts") or {},
                "recommended_resolution": item.get("recommended_resolution"),
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for idx, item in enumerate(actionable[:10])
    ]
    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "adm_ldm_scale_in_bucket_attribution_source_only",
        "runtime_effect": False,
        "window_policy": "daily_lifecycle_rows_plus_threshold_cycle_rolling_consumer",
        "sample_floor": SCALE_IN_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "scale_in arm + blocker namespace + joined source labels",
        "forbidden_uses": [
            "real_scale_in_submit",
            "position_cap_release",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
        ],
        "summary": {
            "scale_in_rows": len(scale_rows),
            "bucket_count": len(buckets),
            "actionable_bucket_count": len(actionable),
            "runtime_candidate_count": len(runtime_candidates),
            "workorder_count": len(workorders),
            "arm_counts": dict(Counter(_scale_in_bucket_features(row)["arm"] for row in scale_rows)),
        },
        "buckets": buckets[:200],
        "runtime_approval_candidates": runtime_candidates,
        "code_improvement_workorders": workorders,
    }


def _confidence_band(value: Any) -> str:
    confidence = _safe_float(value, None)
    if confidence is None:
        return "confidence_unknown"
    if confidence < 0.4:
        return "confidence_lt040"
    if confidence < 0.7:
        return "confidence_040_069"
    return "confidence_070p"


def _overnight_bucket_features(row: dict[str, Any]) -> dict[str, str]:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    return {
        "stage": _bucket_value(row.get("stage"), "stage_unknown"),
        "source_stage": _bucket_value(row.get("source_stage"), "source_unknown"),
        "overnight_action": _bucket_value(features.get("overnight_action"), "action_unknown"),
        "overnight_status": _bucket_value(features.get("overnight_status"), "status_unknown"),
        "confidence_band": _confidence_band(features.get("overnight_confidence")),
        "profit_band": _numeric_band(
            features.get("profit_rate_live") if features.get("profit_rate_live") is not None else labels.get("profit_rate"),
            prefix="profit",
            cuts=[(-0.7, "lt_neg070"), (-0.1, "neg070_neg010"), (0.8, "neg010_pos080"), (1.5, "pos080_pos150"), (3.0, "pos150_pos300")],
            unknown="profit_unknown",
        ),
        "peak_profit_band": _numeric_band(
            features.get("peak_profit"),
            prefix="peak",
            cuts=[(0.0, "lt_zero"), (0.8, "zero_pos080"), (1.5, "pos080_pos150"), (3.0, "pos150_pos300")],
            unknown="peak_unknown",
        ),
        "held_bucket": _numeric_band(
            features.get("held_sec"),
            prefix="held",
            cuts=[(20, "lt020s"), (180, "020_180s"), (600, "180_600s"), (1800, "600_1800s")],
            unknown="held_unknown",
        ),
        "price_source": _bucket_value(features.get("overnight_price_source"), "price_source_unknown"),
        "source_quality_gate": _bucket_value(features.get("source_quality_gate"), "source_quality_unknown"),
    }


def _overnight_bucket_row(bucket_type: str, bucket_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined = [row for row in rows if row.get("stage_ev_composite_pct") is not None]
    joined_sample = len(joined)
    ev_values = [float(row["stage_ev_composite_pct"]) for row in joined]
    profit_values = [
        _safe_float((row.get("labels") or {}).get("profit_rate"), None)
        for row in joined
        if isinstance(row.get("labels"), dict)
    ]
    valid_profit = [float(value) for value in profit_values if value is not None]
    avg_ev = round(sum(ev_values) / len(ev_values), 4) if ev_values else None
    avg_profit = round(sum(valid_profit) / len(valid_profit), 4) if valid_profit else None
    source_quality = (
        "pass"
        if len(rows) >= OVERNIGHT_BUCKET_SAMPLE_FLOOR and joined_sample >= OVERNIGHT_BUCKET_SAMPLE_FLOOR
        else "hold_sample"
    )
    if avg_ev is None or source_quality != "pass":
        recommended_route = "hold_sample"
    elif avg_ev <= OVERNIGHT_BUCKET_NEGATIVE_EV_PCT:
        recommended_route = "candidate_tighten_or_exclude"
    elif avg_ev >= OVERNIGHT_BUCKET_POSITIVE_EV_PCT:
        recommended_route = "candidate_recovery_or_relax"
    else:
        recommended_route = "hold_no_edge"
    return {
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "sample": len(rows),
        "joined_sample": joined_sample,
        "join_rate": round(joined_sample / len(rows), 4) if rows else 0.0,
        "source_quality_gate": source_quality,
        "source_quality_adjusted_ev_pct": avg_ev,
        "equal_weight_avg_profit_pct": avg_profit,
        "diagnostic_win_rate": (
            round(sum(1 for value in valid_profit if value > 0) / len(valid_profit), 4)
            if valid_profit
            else None
        ),
        "next_day_mfe_pct": _avg_label(joined, "next_day_mfe_pct"),
        "next_day_mae_pct": _avg_label(joined, "next_day_mae_pct"),
        "next_day_close_pct": _avg_label(joined, "next_day_close_pct"),
        "recommended_route": recommended_route,
        "decision_authority": "adm_ldm_overnight_bucket_attribution_source_only",
        "runtime_effect": False,
        "fixed_threshold_contract_role": "bounded_tunable",
    }


def _overnight_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overnight_rows = [
        row
        for row in rows
        if str(row.get("source") or "") == "scalp_sim_overnight_pipeline_events"
    ]
    bucket_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in overnight_rows:
        buckets = _overnight_bucket_features(row)
        for bucket_type, bucket_key in buckets.items():
            bucket_groups[(bucket_type, bucket_key)].append(row)
        combo_key = "|".join(
            [
                f"action={buckets['overnight_action']}",
                f"status={buckets['overnight_status']}",
                f"confidence={buckets['confidence_band']}",
                f"profit={buckets['profit_band']}",
            ]
        )
        bucket_groups[("combo_overnight_decision", combo_key)].append(row)

    buckets = [
        _overnight_bucket_row(bucket_type, bucket_key, subset)
        for (bucket_type, bucket_key), subset in bucket_groups.items()
    ]
    buckets.sort(
        key=lambda item: (
            str(item.get("bucket_type") or ""),
            -int(item.get("joined_sample") or 0),
            str(item.get("bucket_key") or ""),
        )
    )
    actionable = [
        item
        for item in buckets
        if item.get("source_quality_gate") == "pass"
        and item.get("recommended_route") in {"candidate_tighten_or_exclude", "candidate_recovery_or_relax"}
    ]

    def approval_eligible(item: dict[str, Any]) -> bool:
        bucket_key = str(item.get("bucket_key") or "")
        if "unknown" in bucket_key:
            return False
        return int(item.get("joined_sample") or 0) >= OVERNIGHT_BUCKET_PROMOTE_SAMPLE_FLOOR

    runtime_candidates = [
        {
            "candidate_id": f"overnight_bucket_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "recommended_route": item.get("recommended_route"),
            "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
            "joined_sample": item.get("joined_sample"),
            "approval_required": True,
            "allowed_runtime_apply": False,
            "decision_authority": "adm_ldm_overnight_bucket_attribution_source_only",
            "next_route": "threshold_cycle_runtime_approval_request_after_rolling_confirmation",
        }
        for idx, item in enumerate(actionable)
        if approval_eligible(item)
    ][:10]
    workorders = [
        {
            "workorder_id": f"overnight_bucket_source_quality_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "reason": "overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation",
            "recommended_route": item.get("recommended_route"),
            "metric_role": "source_quality_gate",
            "implementation_status": "implemented",
            "implementation_provenance": {
                "source_field_coverage": item.get("source_field_coverage") or {},
                "unknown_reason_counts": item.get("unknown_reason_counts") or {},
                "recommended_resolution": item.get("recommended_resolution"),
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for idx, item in enumerate(actionable[:10])
    ]
    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "adm_ldm_overnight_bucket_attribution_source_only",
        "runtime_effect": False,
        "implementation_status": "implemented",
        "implementation_provenance": {
            "runtime_effect": False,
            "decision_authority": "adm_ldm_overnight_bucket_attribution_source_only",
            "source_quality_gate": "overnight decision coverage + joined same/next-day source labels",
            "forbidden_uses": [
                "hard_overnight_gate",
                "real_sell_order_submit",
                "intraday_threshold_mutation",
                "provider_route_change",
                "bot_restart_trigger",
            ],
        },
        "window_policy": "daily_overnight_rows_plus_next_day_carry_label_join_consumer",
        "sample_floor": OVERNIGHT_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "overnight decision coverage + joined same/next-day source labels",
        "forbidden_uses": [
            "hard_overnight_gate",
            "real_sell_order_submit",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
        ],
        "summary": {
            "overnight_rows": len(overnight_rows),
            "bucket_count": len(buckets),
            "actionable_bucket_count": len(actionable),
            "runtime_candidate_count": len(runtime_candidates),
            "workorder_count": len(workorders),
            "status_counts": dict(Counter(_overnight_bucket_features(row)["overnight_status"] for row in overnight_rows)),
        },
        "buckets": buckets[:200],
        "runtime_approval_candidates": runtime_candidates,
        "code_improvement_workorders": workorders,
    }


def _policy_entries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("stage") or "unknown")].append(row)
    entries: list[dict[str, Any]] = []
    for stage in ("entry", "submit", "holding", "scale_in", "exit"):
        subset = grouped.get(stage, [])
        joined = [row for row in subset if row.get("stage_ev_composite_pct") is not None]
        sample = len(subset)
        joined_sample = len(joined)
        join_rate = (joined_sample / sample) if sample else 0.0
        avg_ev = (
            round(sum(float(row["stage_ev_composite_pct"]) for row in joined) / joined_sample, 4)
            if joined_sample
            else None
        )
        confidence = round(min(1.0, (joined_sample / JOINED_SAMPLE_FLOOR) * join_rate), 4) if sample else 0.0
        source_quality = "pass" if sample >= SAMPLE_FLOOR and joined_sample >= JOINED_SAMPLE_FLOOR else "hold_sample"
        selected_action = _policy_action_for(stage, subset)
        promote_ready = (
            stage == "entry"
            and selected_action == "BUY_DEFENSIVE"
            and joined_sample >= PROMOTE_JOINED_SAMPLE_FLOOR
            and (avg_ev or 0.0) >= PROMOTE_MIN_EV_PCT
            and source_quality == "pass"
        )
        entries.append(
            {
                "policy_key": f"{stage}:weighted_adm_v1",
                "stage": stage,
                "sample": sample,
                "joined_sample": joined_sample,
                "join_rate": round(join_rate, 4),
                "stage_ev_composite_pct": avg_ev,
                "confidence": confidence,
                "source_quality_gate": source_quality,
                "selected_action": selected_action,
                "promote_ready": promote_ready,
                "allowed_actions": _allowed_actions(stage),
            }
        )
    return entries


def _load_lifecycle_ai_context_attribution(target_date: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = REPORT_DIR / "lifecycle_ai_context_attribution" / f"lifecycle_ai_context_attribution_{target_date}.json"
    payload = _read_json_dict(path)
    if not payload:
        return {}, {"artifact": str(path) if path.exists() else None, "status": "missing"}
    by_stage = payload.get("stage_attribution") if isinstance(payload.get("stage_attribution"), dict) else {}
    return (
        {str(stage): dict(item) for stage, item in by_stage.items() if isinstance(item, dict)},
        {
            "artifact": str(path),
            "status": "available",
            "summary": payload.get("summary") if isinstance(payload.get("summary"), dict) else {},
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
        },
    )


def _apply_lifecycle_ai_context_feedback(
    policy_entries: list[dict[str, Any]],
    attribution_by_stage: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in policy_entries:
        stage = str(entry.get("stage") or "")
        attribution = attribution_by_stage.get(stage, {})
        contribution = _safe_float(attribution.get("context_contribution_score"), 0.0) or 0.0
        bounded_weight = _safe_float(attribution.get("bounded_auxiliary_weight"), 0.0) or 0.0
        result.append(
            {
                **entry,
                "context_contribution_score": round(float(contribution), 4),
                "bounded_auxiliary_weight": round(float(bounded_weight), 4),
                "context_feedback_route": (
                    attribution.get("feedback_route")
                    or ("hold_sample" if not attribution else "bounded_auxiliary_weight")
                ),
                "context_attribution_quality_status": attribution.get("attribution_quality_status")
                or "hold_sample",
            }
        )
    return result


def _lifecycle_ai_context_feedback_summary(policy_entries: list[dict[str, Any]]) -> dict[str, Any]:
    route_counts: Counter[str] = Counter()
    quality_counts: Counter[str] = Counter()
    weighted_count = 0
    for entry in policy_entries:
        route_counts[str(entry.get("context_feedback_route") or "hold_sample")] += 1
        quality_counts[str(entry.get("context_attribution_quality_status") or "hold_sample")] += 1
        if abs(_safe_float(entry.get("bounded_auxiliary_weight"), 0.0) or 0.0) > 0:
            weighted_count += 1
    return {
        "implementation_status": "implemented",
        "runtime_effect": False,
        "decision_authority": "lifecycle_ai_context_feedback_source_only",
        "policy_entry_count": len(policy_entries),
        "bounded_auxiliary_weight_nonzero_count": weighted_count,
        "route_counts": dict(route_counts),
        "quality_counts": dict(quality_counts),
    }


def _allowed_actions(stage: str) -> list[str]:
    return {
        "entry": ["BUY_DEFENSIVE", "WAIT_REQUOTE", "DROP", "NO_CHANGE"],
        "submit": ["ALLOW_SUBMIT", "NO_CHANGE"],
        "holding": ["HOLD", "EXIT", "NO_CHANGE"],
        "scale_in": ["AVG_DOWN_BIAS", "PYRAMID_BIAS", "NO_CHANGE"],
        "exit": ["HOLD", "EXIT", "NO_CHANGE"],
    }.get(stage, ["NO_CHANGE"])


def build_lifecycle_decision_matrix_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_loaders = [
        _load_entry_rows,
        _load_sim_post_sell_rows,
        _load_wait6579_rows,
        _load_scalp_sim_submit_rows,
        _load_scalp_sim_holding_rows,
        _load_scalp_sim_scale_in_rows,
        _load_scale_in_attribution_rows,
        _load_scalp_sim_overnight_rows,
        _load_scalp_sim_panic_rows,
    ]
    rows: list[dict[str, Any]] = []
    sources: dict[str, Any] = {}
    for loader in source_loaders:
        loaded_rows, summary = loader(target_date)
        rows.extend(loaded_rows)
        sources[loader.__name__.removeprefix("_load_").removesuffix("_rows")] = summary
    source_rows_total = len(rows)
    retained_rows = len(rows)
    dropped_rows_by_source: dict[str, int] = {}
    institutional_feature_map, institutional_summary = _load_institutional_flow_feature_map(target_date)
    institutional_joined_rows = _apply_institutional_flow_features(rows, institutional_feature_map)
    sources["institutional_flow_context"] = {
        **institutional_summary,
        "joined_rows": institutional_joined_rows,
        "runtime_effect": False,
        "decision_authority": "source_only_lifecycle_feature",
    }
    attribution_by_stage, attribution_summary = _load_lifecycle_ai_context_attribution(target_date)
    policy_entries = _apply_lifecycle_ai_context_feedback(_policy_entries(rows), attribution_by_stage)
    warnings: list[str] = []
    if not rows:
        warnings.append("lifecycle_rows_missing")
    if all(entry.get("source_quality_gate") != "pass" for entry in policy_entries):
        warnings.append("all_stage_policy_entries_below_sample_floor")
    entry_bucket_attribution = _entry_bucket_attribution(rows)
    submit_bucket_attribution = _submit_bucket_attribution(rows)
    scale_in_bucket_attribution = _scale_in_bucket_attribution(rows)
    overnight_bucket_attribution = _overnight_bucket_attribution(rows)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "lifecycle_decision_matrix",
        "matrix_version": f"{MATRIX_VERSION_PREFIX}_{target_date}",
        "runtime_effect": False,
        "decision_authority": "weighted_adm_source_bundle_for_auto_bounded_apply",
        "metric_role": "primary_ev",
        "window_policy": "same_day_source_bundle_plus_rolling_threshold_cycle_consumer",
        "sample_floor": SAMPLE_FLOOR,
        "joined_sample_floor": JOINED_SAMPLE_FLOOR,
        "primary_decision_metric": "stage_ev_composite_pct",
        "source_quality_gate": "stage sample, joined outcome, fixed threshold contract, no future-label runtime inputs",
        "forbidden_uses": [
            "hard_safety_override",
            "real_execution_quality_from_sim_only",
            "intraday_threshold_mutation",
            "runtime_feature_future_label_leakage",
        ],
        "fixed_threshold_contract": fixed_threshold_contract(),
        "runtime_feature_keys": sorted(RUNTIME_FEATURE_KEYS),
        "label_keys": sorted(LABEL_KEYS),
        "summary": {
            "total_rows": len(rows),
            "source_rows_total": source_rows_total,
            "retained_rows": retained_rows,
            "dropped_rows_by_source": dropped_rows_by_source,
            "joined_rows": sum(1 for row in rows if row.get("stage_ev_composite_pct") is not None),
            "stage_counts": dict(Counter(str(row.get("stage") or "unknown") for row in rows)),
            "policy_pass_count": sum(1 for entry in policy_entries if entry.get("source_quality_gate") == "pass"),
            "promote_ready_count": sum(1 for entry in policy_entries if entry.get("promote_ready")),
            "entry_bucket_actionable_count": (
                entry_bucket_attribution.get("summary", {}).get("actionable_bucket_count")
                if isinstance(entry_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "entry_bucket_runtime_candidate_count": (
                entry_bucket_attribution.get("summary", {}).get("runtime_candidate_count")
                if isinstance(entry_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "submit_bucket_contract_gap_count": (
                submit_bucket_attribution.get("summary", {}).get("contract_gap_count")
                if isinstance(submit_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "submit_bucket_workorder_count": (
                submit_bucket_attribution.get("summary", {}).get("workorder_count")
                if isinstance(submit_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "scale_in_bucket_actionable_count": (
                scale_in_bucket_attribution.get("summary", {}).get("actionable_bucket_count")
                if isinstance(scale_in_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "scale_in_bucket_runtime_candidate_count": (
                scale_in_bucket_attribution.get("summary", {}).get("runtime_candidate_count")
                if isinstance(scale_in_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "scale_in_bucket_workorder_count": (
                scale_in_bucket_attribution.get("summary", {}).get("workorder_count")
                if isinstance(scale_in_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "overnight_bucket_actionable_count": (
                overnight_bucket_attribution.get("summary", {}).get("actionable_bucket_count")
                if isinstance(overnight_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "overnight_bucket_runtime_candidate_count": (
                overnight_bucket_attribution.get("summary", {}).get("runtime_candidate_count")
                if isinstance(overnight_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "overnight_bucket_workorder_count": (
                overnight_bucket_attribution.get("summary", {}).get("workorder_count")
                if isinstance(overnight_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "lifecycle_ai_context_feedback": _lifecycle_ai_context_feedback_summary(policy_entries),
            "status": "pass" if not warnings else "warning",
            "warnings": warnings,
        },
        "policy_entries": policy_entries,
        "entry_bucket_attribution": entry_bucket_attribution,
        "submit_bucket_attribution": submit_bucket_attribution,
        "scale_in_bucket_attribution": scale_in_bucket_attribution,
        "overnight_bucket_attribution": overnight_bucket_attribution,
        "examples": rows[:50],
        "sources": {**sources, "lifecycle_ai_context_attribution": attribution_summary},
        "warnings": warnings,
    }
    MATRIX_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_lifecycle_decision_matrix_markdown(report), encoding="utf-8")
    return report


def render_lifecycle_decision_matrix_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Lifecycle Decision Matrix - {report.get('date')}",
        "",
        "## Contract",
        f"- matrix_version: `{report.get('matrix_version')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- primary_decision_metric: `{report.get('primary_decision_metric')}`",
        "",
        "## Summary",
        f"- total_rows: `{summary.get('total_rows')}`",
        f"- source_rows_total: `{summary.get('source_rows_total')}`",
        f"- retained_rows: `{summary.get('retained_rows')}`",
        f"- dropped_rows_by_source: `{summary.get('dropped_rows_by_source') or {}}`",
        f"- joined_rows: `{summary.get('joined_rows')}`",
        f"- policy_pass_count: `{summary.get('policy_pass_count')}`",
        f"- promote_ready_count: `{summary.get('promote_ready_count')}`",
        f"- entry_bucket_actionable_count: `{summary.get('entry_bucket_actionable_count')}`",
        f"- entry_bucket_runtime_candidate_count: `{summary.get('entry_bucket_runtime_candidate_count')}`",
        f"- scale_in_bucket_actionable_count: `{summary.get('scale_in_bucket_actionable_count')}`",
        f"- scale_in_bucket_runtime_candidate_count: `{summary.get('scale_in_bucket_runtime_candidate_count')}`",
        f"- overnight_bucket_actionable_count: `{summary.get('overnight_bucket_actionable_count')}`",
        f"- overnight_bucket_runtime_candidate_count: `{summary.get('overnight_bucket_runtime_candidate_count')}`",
        f"- lifecycle_ai_context_feedback: `{summary.get('lifecycle_ai_context_feedback') or {}}`",
        f"- warnings: `{summary.get('warnings')}`",
        "",
        "## Policy Entries",
        "| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in report.get("policy_entries") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{item.get('stage')}` | {item.get('sample')} | {item.get('joined_sample')} | "
            f"{item.get('stage_ev_composite_pct')} | {item.get('confidence')} | "
            f"`{item.get('source_quality_gate')}` | `{item.get('selected_action')}` | {item.get('promote_ready')} |"
        )
    entry_buckets = (
        report.get("entry_bucket_attribution")
        if isinstance(report.get("entry_bucket_attribution"), dict)
        else {}
    )
    bucket_summary = entry_buckets.get("summary") if isinstance(entry_buckets.get("summary"), dict) else {}
    lines.extend(
        [
            "",
            "## Entry Bucket Attribution",
            "",
            f"- decision_authority: `{entry_buckets.get('decision_authority')}`",
            f"- primary_decision_metric: `{entry_buckets.get('primary_decision_metric')}`",
            f"- summary: `{bucket_summary}`",
            "",
            "| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    shown = 0
    for item in entry_buckets.get("buckets") or []:
        if not isinstance(item, dict):
            continue
        if item.get("source_quality_gate") != "pass" and shown >= 20:
            continue
        lines.append(
            f"| `{item.get('bucket_type')}` | `{item.get('bucket_key')}` | {item.get('sample')} | "
            f"{item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | "
            f"{item.get('equal_weight_avg_profit_pct')} | {item.get('diagnostic_win_rate')} | "
            f"`{item.get('recommended_route')}` |"
        )
        shown += 1
        if shown >= 40:
            break
    candidates = entry_buckets.get("runtime_approval_candidates") or []
    lines.extend(["", "### Entry Bucket Runtime Approval Candidates", ""])
    if candidates:
        for item in candidates:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('candidate_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('recommended_route')}`")
    else:
        lines.append("- none")
    workorders = entry_buckets.get("code_improvement_workorders") or []
    lines.extend(["", "### Entry Bucket Workorders", ""])
    if workorders:
        for item in workorders:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('workorder_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('reason')}`")
    else:
        lines.append("- none")
    submit_buckets = (
        report.get("submit_bucket_attribution")
        if isinstance(report.get("submit_bucket_attribution"), dict)
        else {}
    )
    submit_summary = submit_buckets.get("summary") if isinstance(submit_buckets.get("summary"), dict) else {}
    lines.extend(
        [
            "",
            "## Submit Bucket Attribution",
            "",
            f"- decision_authority: `{submit_buckets.get('decision_authority')}`",
            f"- primary_decision_metric: `{submit_buckets.get('primary_decision_metric')}`",
            f"- summary: `{submit_summary}`",
            "",
            "| bucket_type | bucket_key | sample | joined | ev | route |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    shown = 0
    for item in submit_buckets.get("buckets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{item.get('bucket_type')}` | `{item.get('bucket_key')}` | {item.get('sample')} | "
            f"{item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | "
            f"`{item.get('recommended_route')}` |"
        )
        shown += 1
        if shown >= 40:
            break
    submit_workorders = submit_buckets.get("code_improvement_workorders") or []
    lines.extend(["", "### Submit Bucket Workorders", ""])
    if submit_workorders:
        for item in submit_workorders:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('workorder_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('reason')}`")
    else:
        lines.append("- none")
    scale_buckets = (
        report.get("scale_in_bucket_attribution")
        if isinstance(report.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    scale_summary = scale_buckets.get("summary") if isinstance(scale_buckets.get("summary"), dict) else {}
    lines.extend(
        [
            "",
            "## Scale-In Bucket Attribution",
            "",
            f"- decision_authority: `{scale_buckets.get('decision_authority')}`",
            f"- primary_decision_metric: `{scale_buckets.get('primary_decision_metric')}`",
            f"- summary: `{scale_summary}`",
            "",
            "| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    shown = 0
    for item in scale_buckets.get("buckets") or []:
        if not isinstance(item, dict):
            continue
        if item.get("source_quality_gate") != "pass" and shown >= 20:
            continue
        lines.append(
            f"| `{item.get('bucket_type')}` | `{item.get('bucket_key')}` | {item.get('sample')} | "
            f"{item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | "
            f"{item.get('equal_weight_avg_profit_pct')} | {item.get('diagnostic_win_rate')} | "
            f"`{item.get('recommended_route')}` |"
        )
        shown += 1
        if shown >= 40:
            break
    scale_candidates = scale_buckets.get("runtime_approval_candidates") or []
    lines.extend(["", "### Scale-In Bucket Runtime Approval Candidates", ""])
    if scale_candidates:
        for item in scale_candidates:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('candidate_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('recommended_route')}`")
    else:
        lines.append("- none")
    scale_workorders = scale_buckets.get("code_improvement_workorders") or []
    lines.extend(["", "### Scale-In Bucket Workorders", ""])
    if scale_workorders:
        for item in scale_workorders:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('workorder_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('reason')}`")
    else:
        lines.append("- none")
    overnight_buckets = (
        report.get("overnight_bucket_attribution")
        if isinstance(report.get("overnight_bucket_attribution"), dict)
        else {}
    )
    overnight_summary = overnight_buckets.get("summary") if isinstance(overnight_buckets.get("summary"), dict) else {}
    lines.extend(
        [
            "",
            "## Overnight Bucket Attribution",
            "",
            f"- decision_authority: `{overnight_buckets.get('decision_authority')}`",
            f"- primary_decision_metric: `{overnight_buckets.get('primary_decision_metric')}`",
            f"- summary: `{overnight_summary}`",
            "",
            "| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    shown = 0
    for item in overnight_buckets.get("buckets") or []:
        if not isinstance(item, dict):
            continue
        if item.get("source_quality_gate") != "pass" and shown >= 20:
            continue
        lines.append(
            f"| `{item.get('bucket_type')}` | `{item.get('bucket_key')}` | {item.get('sample')} | "
            f"{item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | "
            f"{item.get('equal_weight_avg_profit_pct')} | {item.get('diagnostic_win_rate')} | "
            f"`{item.get('recommended_route')}` |"
        )
        shown += 1
        if shown >= 40:
            break
    overnight_candidates = overnight_buckets.get("runtime_approval_candidates") or []
    lines.extend(["", "### Overnight Bucket Runtime Approval Candidates", ""])
    if overnight_candidates:
        for item in overnight_candidates:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('candidate_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('recommended_route')}`")
    else:
        lines.append("- none")
    overnight_workorders = overnight_buckets.get("code_improvement_workorders") or []
    lines.extend(["", "### Overnight Bucket Workorders", ""])
    if overnight_workorders:
        for item in overnight_workorders:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('workorder_id')}`: `{item.get('bucket_type')}` / `{item.get('bucket_key')}` -> `{item.get('reason')}`")
    else:
        lines.append("- none")
    contract = report.get("fixed_threshold_contract") if isinstance(report.get("fixed_threshold_contract"), dict) else {}
    roles = contract.get("roles") if isinstance(contract.get("roles"), dict) else {}
    lines.extend(["", "## Fixed Threshold Roles", ""])
    for role, values in roles.items():
        lines.append(f"- `{role}`: {', '.join(str(value) for value in values)}")
    lines.extend(["", "## Forbidden Uses", ""])
    for item in report.get("forbidden_uses") or []:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build lifecycle decision matrix report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    build_lifecycle_decision_matrix_report(args.target_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
