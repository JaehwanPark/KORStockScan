"""Build the lifecycle decision matrix source artifact.

The matrix is a postclose source bundle. Runtime code may consume the latest
policy section, but labels such as MFE/MAE/close are never runtime inputs.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.institutional_flow_context import RUNTIME_FEATURE_KEYS as INSTITUTIONAL_FLOW_FEATURE_KEYS
from src.engine.institutional_flow_context import report_paths as institutional_flow_report_paths
from src.engine.scalp_entry_action_decision_matrix import report_paths as entry_adm_report_paths
from src.utils.jsonl_io import existing_or_gzip_path


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
HOLDING_BUCKET_SAMPLE_FLOOR = 3
EXIT_BUCKET_SAMPLE_FLOOR = 3
LIFECYCLE_FLOW_BUCKET_SAMPLE_FLOOR = 1
LIFECYCLE_FLOW_BUCKET_PROMOTE_SAMPLE_FLOOR = 10
LIFECYCLE_FLOW_BUCKET_NEGATIVE_EV_PCT = -0.30
LIFECYCLE_FLOW_BUCKET_POSITIVE_EV_PCT = 0.30
LIFECYCLE_FLOW_REQUIRED_STAGES = ("entry", "submit", "holding", "exit")
AI_INFERENCE_MODEL = "gpt-5.4-mini"
AI_INFERENCE_REASONING_EFFORT = "medium"
AI_REVIEW_MODEL = "gpt-5.4"
AI_REVIEW_REASONING_EFFORT = "low"

RUNTIME_FEATURE_KEYS = {
    "ai_score",
    "ai_score_raw",
    "ai_action",
    "ai_model",
    "ai_model_tier",
    "ai_result_source",
    "ai_transport_mode",
    "chosen_action",
    "sim_record_id",
    "entry_adm_candidate_id",
    "lifecycle_flow_bridge_key",
    "lifecycle_join_bridge_key",
    "join_bridge_key",
    "lifecycle_flow_bucket_id",
    "score_bucket",
    "risk_context_bucket",
    "stale_bucket",
    "price_resolution_bucket",
    "liquidity_bucket",
    "liquidity_bucket_provenance",
    "liquidity_guard_action",
    "liquidity_guard_reason",
    "overbought_bucket",
    "overbought_bucket_provenance",
    "overbought_guard_action",
    "overbought_guard_reason",
    "latency_state",
    "latency_reason",
    "price_below_bid_bps",
    "time_bucket",
    "time_bucket_provenance",
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
    "scale_in_field_provenance",
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
    "high_ai_hard_stop_conflict",
    "hard_stop_conflict_dimension",
    "hard_stop_conflict_ai_score_band",
    "hard_stop_conflict_runtime_effect",
    "hard_stop_conflict_allowed_runtime_apply",
    "hard_stop_conflict_hard_gate",
    "hard_stop_conflict_contract",
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
    "high_ai_hard_stop_conflict",
    "hard_stop_conflict_dimension",
    "hard_stop_conflict_ai_score_band",
    "ai_score_at_exit",
    "ai_model_at_exit",
    "ai_result_source_at_exit",
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


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "none", "null"}:
        return False
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
    path = existing_or_gzip_path(path)
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


def _time_bucket_from_value(value: Any) -> str:
    raw = str(value or "").strip()
    hour = -1
    try:
        hour = datetime.fromisoformat(raw).hour
    except Exception:
        if len(raw) >= 2 and raw[:2].isdigit() and not raw.startswith("20"):
            try:
                hour = int(raw[:2])
            except Exception:
                hour = -1
    if hour < 0:
        return "time_unknown"
    if hour < 10:
        return "time_0900_1000"
    if hour < 12:
        return "time_1000_1200"
    if hour < 14:
        return "time_1200_1400"
    return "time_1400_close"


def _entry_strength_bucket_from_features(features: dict[str, Any]) -> str:
    explicit = _bucket_value(features.get("risk_context_bucket"), "")
    if explicit:
        return explicit
    buy_pressure = _safe_float(features.get("buy_pressure"), None)
    tick_accel = _safe_float(features.get("tick_accel"), None)
    if buy_pressure is None and tick_accel is None:
        return "strength_proxy_unobserved"
    if (buy_pressure is not None and buy_pressure >= 70.0) or (tick_accel is not None and tick_accel >= 1.25):
        return "strong_strength_momentum"
    if (buy_pressure is not None and buy_pressure < 45.0) or (tick_accel is not None and tick_accel < 0.5):
        return "weak_strength_momentum"
    return "neutral_strength_momentum"


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
        "high_ai_hard_stop_conflict": _safe_bool(item.get("high_ai_hard_stop_conflict", False)),
        "hard_stop_conflict_dimension": item.get("hard_stop_conflict_dimension"),
        "hard_stop_conflict_ai_score_band": item.get("hard_stop_conflict_ai_score_band"),
        "ai_score_at_exit": item.get("ai_score_at_exit") or item.get("current_ai_score"),
        "ai_model_at_exit": item.get("ai_model_at_exit") or item.get("ai_model"),
        "ai_result_source_at_exit": item.get("ai_result_source_at_exit") or item.get("ai_result_source"),
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
            "high_ai_hard_stop_conflict": _safe_bool(item.get("high_ai_hard_stop_conflict", False)),
            "hard_stop_conflict_dimension": item.get("hard_stop_conflict_dimension"),
            "hard_stop_conflict_ai_score_band": item.get("hard_stop_conflict_ai_score_band"),
            "ai_score_at_exit": item.get("ai_score_at_exit") or item.get("current_ai_score"),
            "ai_model_at_exit": item.get("ai_model_at_exit") or item.get("ai_model"),
            "ai_result_source_at_exit": item.get("ai_result_source_at_exit") or item.get("ai_result_source"),
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
                    "sim_record_id": item.get("sim_record_id"),
                    "entry_adm_candidate_id": item.get("entry_adm_candidate_id"),
                    "ai_score": item.get("ai_score") or item.get("current_ai_score") or item.get("ai_score_at_exit"),
                    "ai_score_raw": item.get("ai_score_raw") or item.get("ai_score_raw_at_exit"),
                    "ai_action": item.get("ai_action") or item.get("ai_action_at_exit"),
                    "ai_model": item.get("ai_model") or item.get("ai_model_at_exit"),
                    "ai_model_tier": item.get("ai_model_tier") or item.get("ai_model_tier_at_exit"),
                    "ai_result_source": item.get("ai_result_source") or item.get("ai_result_source_at_exit"),
                    "ai_transport_mode": item.get("ai_transport_mode") or item.get("ai_transport_mode_at_exit"),
                    "high_ai_hard_stop_conflict": _safe_bool(item.get("high_ai_hard_stop_conflict", False)),
                    "hard_stop_conflict_dimension": item.get("hard_stop_conflict_dimension"),
                    "hard_stop_conflict_ai_score_band": item.get("hard_stop_conflict_ai_score_band"),
                    "hard_stop_conflict_runtime_effect": False,
                    "hard_stop_conflict_allowed_runtime_apply": False,
                    "hard_stop_conflict_hard_gate": False,
                    "hard_stop_conflict_contract": item.get("hard_stop_conflict_contract"),
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
                    "chosen_action": "WAIT_REQUOTE" if str(item.get("action") or "").upper() == "WAIT" else item.get("action"),
                    "buy_pressure": item.get("buy_pressure"),
                    "tick_accel": item.get("tick_accel"),
                    "micro_vwap_bp": item.get("micro_vwap_bp"),
                    "liquidity_bucket": item.get("liquidity_bucket"),
                    "liquidity_bucket_provenance": item.get("liquidity_bucket_provenance"),
                    "overbought_bucket": item.get("overbought_bucket"),
                    "overbought_bucket_provenance": item.get("overbought_bucket_provenance"),
                    "time_bucket": item.get("time_bucket") or _time_bucket_from_value(item.get("signal_time") or item.get("event_time")),
                    "time_bucket_provenance": item.get("time_bucket_provenance") or "signal_time_backfill",
                    "risk_context_bucket": _entry_strength_bucket_from_features(item),
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
                    "broker_order_submitted": fields.get("broker_order_submitted") or fields.get("actual_order_submitted"),
                    "broker_order_no": fields.get("broker_order_no") or fields.get("order_no"),
                    "broker_receipt_status": fields.get("broker_receipt_status"),
                    "broker_receipt_reason": fields.get("broker_receipt_reason") or fields.get("reason"),
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
                    "requested_qty": fields.get("requested_qty") or fields.get("qty"),
                    "filled_qty": fields.get("filled_qty"),
                    "remaining_qty": fields.get("remaining_qty"),
                    "fill_quality": fields.get("fill_quality"),
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
                    "post_submit_state": fields.get("post_submit_state"),
                    "cancel_requested": fields.get("cancel_requested"),
                    "cancel_result": fields.get("cancel_result"),
                    "position_rebased_after_fill": fields.get("position_rebased_after_fill"),
                    "telegram_audience": fields.get("telegram_audience"),
                    "telegram_event_type": fields.get("telegram_event_type"),
                    "telegram_sent_after_broker_submit": fields.get("telegram_sent_after_broker_submit"),
                    "strategy_domain": fields.get("strategy_domain") or fields.get("strategy"),
                    "source_namespace": fields.get("source_namespace"),
                    "blocker_namespace": fields.get("blocker_namespace"),
                    "fixed_threshold_contract_role": "bounded_tunable",
                    "sim_record_id": sim_record_id,
                    "entry_adm_candidate_id": fields.get("entry_adm_candidate_id"),
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
                    "entry_adm_candidate_id": fields.get("entry_adm_candidate_id"),
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
            scale_in_arm = _scale_in_arm_from_fields(stage, fields)
            blocker_namespace = _scale_in_blocker_namespace(stage, fields, scale_in_arm)
            ai_score_source = _scale_in_ai_score_source(fields, stage)
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
                        "add_type": scale_in_arm,
                        "scale_in_arm": scale_in_arm,
                        "scale_in_blocker_namespace": blocker_namespace,
                        "scale_in_blocker_reason": fields.get("scale_in_blocker_reason")
                        or fields.get("reason")
                        or fields.get("blocked_reason")
                        or "sim_scale_in_event",
                        "qty": fields.get("qty"),
                        "limit_price": fields.get("limit_price"),
                        "curr_price": fields.get("curr_price"),
                        "best_bid": fields.get("best_bid"),
                        "best_ask": fields.get("best_ask"),
                        "ai_score": fields.get("current_ai_score") or fields.get("ai_score"),
                        "ai_score_source": ai_score_source,
                        "actual_order_submitted": fields.get("actual_order_submitted"),
                        "broker_order_forbidden": fields.get("broker_order_forbidden"),
                        "fixed_threshold_contract_role": "bounded_tunable",
                        "scale_in_fill_observed": is_filled,
                        "sim_record_id": sim_record_id,
                        "scale_in_field_provenance": {
                            "arm": "source_field" if fields.get("scale_in_arm") or fields.get("add_type") else "backfilled_from_stage_or_action",
                            "blocker_namespace": "source_field" if fields.get("scale_in_blocker_namespace") else "backfilled_from_stage_or_action",
                            "ai_score_source": "source_field" if fields.get("ai_score_source") else "backfilled_from_stage_or_action",
                        },
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


def _scale_in_ai_score_source(fields: dict[str, Any], source_stage: str) -> str:
    explicit = _bucket_value(fields.get("ai_score_source"), "")
    if explicit:
        return explicit
    if _bucket_value(fields.get("current_ai_score") or fields.get("ai_score"), ""):
        return "score_field_backfilled"
    if source_stage.startswith("scalp_sim_"):
        return "sim_scale_in_source_not_scored"
    return "stage_rule_backfilled"


def _panic_entry_action_from_stage(source_stage: str, fields: dict[str, Any]) -> str:
    explicit = _bucket_value(
        fields.get("chosen_action")
        or fields.get("panic_lifecycle_action_type")
        or fields.get("euphoria_action_type"),
        "",
    )
    if explicit:
        return explicit
    if source_stage.endswith("_entry_blocked") or "entry_blocked" in source_stage:
        return "BLOCK_ENTRY"
    if "bottoming_entry_allowed" in source_stage:
        return "ALLOW_BOTTOMING_ENTRY"
    if "level1_entry_observed" in source_stage:
        return "ALLOW_LEVEL1_RISK_OFF_ENTRY"
    if "retest_starter_allowed" in source_stage:
        return "ALLOW_RETEST_STARTER"
    if "level1_starter_observed" in source_stage:
        return "ALLOW_LEVEL1_EUPHORIA_STARTER"
    return source_stage


def _panic_entry_liquidity_bucket(fields: dict[str, Any]) -> str:
    explicit = _bucket_value(fields.get("liquidity_bucket"), "")
    if explicit:
        return explicit
    state = _bucket_value(fields.get("liquidity_state"), "")
    return f"liquidity_state_{state.lower()}" if state else "liquidity_context_unobserved"


def _panic_entry_overbought_bucket(fields: dict[str, Any], source_stage: str) -> str:
    explicit = _bucket_value(fields.get("overbought_bucket") or fields.get("overbought_risk_bucket"), "")
    if explicit:
        return explicit
    if _bucket_value(fields.get("chase_risk"), "").lower() in {"true", "1", "yes"}:
        return "overbought_chase_risk"
    level = _bucket_value(fields.get("euphoria_risk_level"), "")
    if level:
        return f"euphoria_risk_level_{level.lower()}"
    if "euphoria" in source_stage:
        return "euphoria_overbought_context_unobserved"
    return "panic_entry_overbought_not_applicable"


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
            "ai_score_source": _scale_in_ai_score_source(fields, source_stage),
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
            "scale_in_field_provenance": {
                "arm": "source_field" if fields.get("scale_in_arm") or fields.get("add_type") or fields.get("scale_in_action_type") else "backfilled_from_stage_or_action",
                "blocker_namespace": "source_field" if fields.get("scale_in_blocker_namespace") else "backfilled_from_stage_or_action",
                "ai_score_source": "source_field" if fields.get("ai_score_source") else "backfilled_from_stage_or_action",
            },
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
                    "sim_record_id": fields.get("sim_record_id"),
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
        scale_in_arm = _scale_in_arm_from_fields(source_stage, fields) if matrix_stage == "scale_in" else ""
        scale_in_blocker_namespace = (
            _scale_in_blocker_namespace(source_stage, fields, scale_in_arm) if matrix_stage == "scale_in" else ""
        )
        ai_score_source = _scale_in_ai_score_source(fields, source_stage) if matrix_stage == "scale_in" else ""
        runtime_features = {
            "ai_score": fields.get("ai_score") or fields.get("current_ai_score"),
            "actual_order_submitted": fields.get("actual_order_submitted"),
            "broker_order_forbidden": fields.get("broker_order_forbidden"),
            "sim_record_id": fields.get("sim_record_id"),
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
        if matrix_stage == "scale_in":
            runtime_features.update(
                {
                    "add_type": scale_in_arm,
                    "scale_in_arm": scale_in_arm,
                    "scale_in_blocker_namespace": scale_in_blocker_namespace,
                    "scale_in_blocker_reason": fields.get("scale_in_blocker_reason")
                    or fields.get("reason")
                    or fields.get("blocked_reason")
                    or source_stage,
                    "ai_score_source": ai_score_source,
                    "scale_in_field_provenance": {
                        "arm": "source_field" if fields.get("scale_in_arm") or fields.get("add_type") else "backfilled_from_stage_or_action",
                        "blocker_namespace": "source_field" if fields.get("scale_in_blocker_namespace") else "backfilled_from_stage_or_action",
                        "ai_score_source": "source_field" if fields.get("ai_score_source") else "backfilled_from_stage_or_action",
                    },
                }
            )
        elif matrix_stage == "entry":
            runtime_features.update(
                {
                    "chosen_action": _panic_entry_action_from_stage(source_stage, fields),
                    "time_bucket": fields.get("time_bucket") or _time_bucket_from_value(item.get("emitted_at")),
                    "liquidity_bucket": _panic_entry_liquidity_bucket(fields),
                    "overbought_bucket": _panic_entry_overbought_bucket(fields, source_stage),
                    "risk_context_bucket": fields.get("risk_context_bucket")
                    or fields.get("symbol_regime")
                    or fields.get("market_regime")
                    or fields.get("risk_direction"),
                }
            )
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
    "actual_order_submitted": "runtime_features.actual_order_submitted|actual_order_submitted|runtime_features.broker_order_submitted",
    "broker_order_forbidden": "runtime_features.broker_order_forbidden",
    "broker_receipt": "runtime_features.broker_order_no|runtime_features.broker_receipt_status|runtime_features.broker_receipt_reason",
    "fill_quality": "runtime_features.fill_quality|runtime_features.filled_qty|runtime_features.remaining_qty|runtime_features.requested_qty",
    "post_submit_state": "runtime_features.post_submit_state|runtime_features.cancel_requested|runtime_features.cancel_result|runtime_features.position_rebased_after_fill",
    "telegram_post_submit": "runtime_features.telegram_sent_after_broker_submit|runtime_features.telegram_event_type|runtime_features.telegram_audience",
    "source_taxonomy": "runtime_features.strategy_domain|runtime_features.source_namespace|runtime_features.blocker_namespace",
    "liquidity_guard_action": "runtime_features.liquidity_guard_action|runtime_features.sim_pre_submit_liquidity_guard_action",
    "liquidity_bucket": "runtime_features.liquidity_guard_reason|runtime_features.sim_pre_submit_liquidity_reason|runtime_features.sim_liquidity_value|runtime_features.sim_min_liquidity|runtime_features.liquidity_bucket",
    "overbought_guard_action": "runtime_features.overbought_guard_action|runtime_features.sim_pre_submit_overbought_guard_action",
    "overbought_bucket": "runtime_features.overbought_guard_reason|runtime_features.sim_pre_submit_overbought_reason|runtime_features.sim_overbought_risk_state|runtime_features.sim_overbought_risk_bucket|runtime_features.overbought_bucket",
    "latency_state": "runtime_features.latency_state",
    "latency_reason": "runtime_features.latency_reason",
    "price_below_bid_bucket": "runtime_features.price_below_bid_bps",
    "combo_submit_quality": "source_stage|runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block|runtime_features.quote_age_ms|runtime_features.would_limit_fill|runtime_features.actual_order_submitted|runtime_features.sim_pre_submit_liquidity_guard_action|runtime_features.sim_pre_submit_liquidity_reason|runtime_features.sim_pre_submit_overbought_guard_action|runtime_features.sim_pre_submit_overbought_reason|runtime_features.latency_state",
}


HOLDING_BUCKET_FIELD_MAP = {
    "holding_source_stage": "source_stage",
    "holding_action": "runtime_features.chosen_action|runtime_features.ai_action",
    "profit_band": "runtime_features.profit_rate_live|labels.profit_rate",
    "held_bucket": "runtime_features.held_sec",
    "combo_holding_flow": "source_stage|runtime_features.chosen_action|runtime_features.ai_action|runtime_features.profit_rate_live|runtime_features.held_sec",
}


EXIT_BUCKET_FIELD_MAP = {
    "exit_source_stage": "source_stage",
    "exit_rule": "labels.exit_rule|runtime_features.chosen_action",
    "exit_outcome": "labels.sim_post_sell_outcome|labels.outcome",
    "profit_band": "labels.profit_rate|runtime_features.profit_rate_live",
    "combo_exit_result": "source_stage|labels.exit_rule|runtime_features.chosen_action|labels.sim_post_sell_outcome|labels.outcome|labels.profit_rate",
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
    if bucket_type == "exit_rule" and all(str(row.get("stage") or "") == "entry" for row in rows):
        return {
            "unknown_dimension_counts": {"exit_rule": 1},
            "unknown_reason_counts": {"entry_label_not_applicable": 1},
            "source_field_coverage": {
                "exit_rule": _field_coverage(rows, field_map.get("exit_rule") or "labels.exit_rule")
            },
            "recommended_resolution": "entry_label_not_applicable",
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
            "runtime_features.post_submit_state|runtime_features.cancel_requested|runtime_features.cancel_result|runtime_features.position_rebased_after_fill|runtime_features.entry_submit_revalidation_warning|runtime_features.entry_submit_revalidation_block|runtime_features.quote_age_ms",
            "price_revalidation_or_submit_state_missing",
        ),
        (
            "broker_receipt_contract_gap",
            "order_entry_broker_receipt_contract_gap_review",
            "runtime_features.broker_order_submitted|runtime_features.broker_order_no|runtime_features.broker_receipt_status|runtime_features.broker_receipt_reason|runtime_features.actual_order_submitted|actual_order_submitted",
            "broker_receipt_or_real_submit_flag_missing",
        ),
        (
            "fill_quality_contract_gap",
            "order_entry_fill_quality_contract_gap_review",
            "runtime_features.requested_qty|runtime_features.filled_qty|runtime_features.remaining_qty|runtime_features.fill_quality|runtime_features.would_limit_fill|runtime_features.resolved_order_price|runtime_features.limit_price",
            "limit_fill_or_price_quality_missing",
        ),
        (
            "telegram_post_submit_contract_gap",
            "order_entry_telegram_post_submit_contract_gap_review",
            "runtime_features.telegram_sent_after_broker_submit|runtime_features.telegram_event_type|runtime_features.telegram_audience|runtime_features.actual_order_submitted|actual_order_submitted",
            "buy_telegram_must_be_bound_to_submitted_only",
        ),
        (
            "source_taxonomy_contract_gap",
            "order_entry_source_taxonomy_contract_gap_review",
            "runtime_features.strategy_domain|runtime_features.source_namespace|runtime_features.blocker_namespace|source_stage",
            "strategy_or_blocker_namespace_missing",
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


def _ai_inference_proposal(
    *,
    decision_point: str,
    deterministic_decision: str,
    bucket_type: str,
    bucket_key: str,
    source_quality_gate: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "decision_point": decision_point,
        "proposal_type": "ai_inference_parallel_review_required",
        "model": AI_INFERENCE_MODEL,
        "reasoning_effort": AI_INFERENCE_REASONING_EFFORT,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "deterministic_decision": deterministic_decision,
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "source_quality_gate": source_quality_gate,
        "reason": reason,
        "review_contract": {
            "model": AI_REVIEW_MODEL,
            "reasoning_effort": AI_REVIEW_REASONING_EFFORT,
            "runtime_effect": False,
            "ai_has_promotion_authority": False,
        },
    }


def _source_missing_value(value: Any) -> bool:
    if value in (None, ""):
        return True
    return str(value).strip().lower() in {"none", "null", "nan", "n/a", "unknown"}


def _holding_action_bucket(row: dict[str, Any]) -> str:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    source_stage = str(row.get("source_stage") or "").strip()
    action = next(
        (
            value
            for value in (
                features.get("chosen_action"),
                features.get("ai_action"),
                features.get("overnight_action"),
            )
            if not _source_missing_value(value)
        ),
        None,
    )
    action_missing = _source_missing_value(action) or str(action) == "holding_action_unknown"
    if action_missing and source_stage == "scalp_sim_holding_started":
        return "holding_action_not_applicable_at_start"
    if action_missing and source_stage == "scalp_sim_overnight_decision":
        return "holding_action_not_applicable_overnight_decision"
    return _bucket_value(action, "holding_action_unknown")


def _holding_held_bucket(row: dict[str, Any]) -> str:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    source_stage = str(row.get("source_stage") or "").strip()
    if features.get("held_sec") in (None, "") and source_stage == "scalp_sim_holding_started":
        return "held_not_applicable_at_start"
    return _numeric_band(
        features.get("held_sec"),
        prefix="held",
        cuts=[(20, "lt020s"), (180, "020_180s"), (600, "180_600s"), (1800, "600_1800s")],
        unknown="held_unknown",
    )


def _holding_profit_bucket(row: dict[str, Any]) -> str:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    source_stage = str(row.get("source_stage") or "").strip()
    value = features.get("profit_rate_live") if features.get("profit_rate_live") is not None else labels.get("profit_rate")
    if value in (None, "") and source_stage == "scalp_sim_holding_started":
        return "profit_not_applicable_at_start"
    return _numeric_band(
        value,
        prefix="profit",
        cuts=[(-0.7, "lt_neg070"), (-0.1, "neg070_neg010"), (0.8, "neg010_pos080"), (1.5, "pos080_pos150"), (3.0, "pos150_pos300")],
        unknown="profit_unknown",
    )


def _holding_bucket_features(row: dict[str, Any]) -> dict[str, str]:
    return {
        "holding_source_stage": _bucket_value(row.get("source_stage"), "holding_source_unknown"),
        "holding_action": _holding_action_bucket(row),
        "profit_band": _holding_profit_bucket(row),
        "held_bucket": _holding_held_bucket(row),
    }


def _exit_outcome_bucket(row: dict[str, Any]) -> str:
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    outcome = labels.get("sim_post_sell_outcome") or labels.get("outcome")
    if not _source_missing_value(outcome):
        return _bucket_value(outcome, "outcome_unknown")
    source_stage = str(row.get("source_stage") or "").strip()
    exit_rule = str(labels.get("exit_rule") or features.get("chosen_action") or "").strip()
    if (
        source_stage == "scalp_sim_partial_sell_order_assumed_filled"
        and exit_rule == "scalp_sim_panic_lifecycle_partial_exit"
    ):
        return "outcome_not_applicable_partial_exit"
    return "outcome_unknown"


def _exit_bucket_features(row: dict[str, Any]) -> dict[str, str]:
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    return {
        "exit_source_stage": _bucket_value(row.get("source_stage"), "exit_source_unknown"),
        "exit_rule": _bucket_value(labels.get("exit_rule") or features.get("chosen_action"), "exit_rule_unknown"),
        "exit_outcome": _exit_outcome_bucket(row),
        "profit_band": _numeric_band(
            labels.get("profit_rate") if labels.get("profit_rate") is not None else features.get("profit_rate_live"),
            prefix="profit",
            cuts=[(-0.7, "lt_neg070"), (-0.1, "neg070_neg010"), (0.8, "neg010_pos080"), (1.5, "pos080_pos150"), (3.0, "pos150_pos300")],
            unknown="profit_unknown",
        ),
    }


def _stage_bucket_row(
    *,
    stage: str,
    bucket_type: str,
    bucket_key: str,
    rows: list[dict[str, Any]],
    field_map: dict[str, str],
    sample_floor: int,
) -> dict[str, Any]:
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
    source_quality = "pass" if len(rows) >= sample_floor and joined_sample >= sample_floor else "hold_sample"
    if "unknown" in str(bucket_key):
        recommended_route = "source_quality_workorder"
    elif avg_ev is None or source_quality != "pass":
        recommended_route = "hold_sample"
    elif avg_ev <= -0.30:
        recommended_route = "candidate_tighten_or_exclude"
    elif avg_ev >= 0.30:
        recommended_route = "candidate_recovery_or_relax"
    else:
        recommended_route = "hold_no_edge"
    unknown_context = _unknown_taxonomy_context(
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        rows=rows,
        joined_sample=joined_sample,
        field_map=field_map,
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
        "recommended_route": recommended_route,
        **unknown_context,
        "ai_inference_proposal": _ai_inference_proposal(
            decision_point=f"{stage}_bucket_classification",
            deterministic_decision=recommended_route,
            bucket_type=bucket_type,
            bucket_key=bucket_key,
            source_quality_gate=source_quality,
            reason="parallel_ai_inference_for_deterministic_bucket_decision",
        ),
        "decision_authority": f"adm_ldm_{stage}_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "stage_only_live_promotion",
            "broker_order_submit",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
            "hard_safety_override",
        ],
    }


def _holding_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    holding_rows = [row for row in rows if str(row.get("stage") or "") == "holding"]
    bucket_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in holding_rows:
        buckets = _holding_bucket_features(row)
        for bucket_type, bucket_key in buckets.items():
            bucket_groups[(bucket_type, bucket_key)].append(row)
        combo_key = "|".join(
            [
                f"source={buckets['holding_source_stage']}",
                f"action={buckets['holding_action']}",
                f"profit={buckets['profit_band']}",
                f"held={buckets['held_bucket']}",
            ]
        )
        bucket_groups[("combo_holding_flow", combo_key)].append(row)
    buckets = [
        _stage_bucket_row(
            stage="holding",
            bucket_type=bucket_type,
            bucket_key=bucket_key,
            rows=subset,
            field_map=HOLDING_BUCKET_FIELD_MAP,
            sample_floor=HOLDING_BUCKET_SAMPLE_FLOOR,
        )
        for (bucket_type, bucket_key), subset in bucket_groups.items()
    ]
    buckets.sort(key=lambda item: (str(item.get("bucket_type") or ""), -int(item.get("joined_sample") or 0), str(item.get("bucket_key") or "")))
    workorder_buckets = [
        item
        for item in buckets
        if item.get("recommended_route") in {"source_quality_workorder", "candidate_tighten_or_exclude", "candidate_recovery_or_relax"}
    ][:10]
    workorders = [
        {
            "workorder_id": f"holding_bucket_source_quality_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "reason": "holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation",
            "recommended_route": item.get("recommended_route"),
            "metric_role": "source_quality_gate",
            "implementation_status": "open" if item.get("recommended_route") == "source_quality_workorder" else "implemented",
            "implementation_provenance": {
                "source_field_coverage": item.get("source_field_coverage") or {},
                "unknown_reason_counts": item.get("unknown_reason_counts") or {},
                "recommended_resolution": item.get("recommended_resolution"),
                "ai_inference_proposal": item.get("ai_inference_proposal"),
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for idx, item in enumerate(workorder_buckets)
    ]
    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "adm_ldm_holding_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "window_policy": "daily_lifecycle_holding_rows_plus_threshold_cycle_rolling_consumer",
        "sample_floor": HOLDING_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "holding rows + joined source labels + parent lifecycle flow required for promotion",
        "forbidden_uses": ["stage_only_live_promotion", "broker_order_submit", "intraday_threshold_mutation", "provider_route_change", "bot_restart_trigger"],
        "summary": {
            "holding_rows": len(holding_rows),
            "source_row_count": len(holding_rows),
            "bucket_count": len(buckets),
            "joined_sample": sum(int(item.get("joined_sample") or 0) for item in buckets),
            "source_quality_adjusted_ev_pct": (
                round(
                    sum(float(item["source_quality_adjusted_ev_pct"]) * int(item.get("joined_sample") or 0) for item in buckets if item.get("source_quality_adjusted_ev_pct") is not None)
                    / sum(int(item.get("joined_sample") or 0) for item in buckets if item.get("source_quality_adjusted_ev_pct") is not None),
                    4,
                )
                if any(item.get("source_quality_adjusted_ev_pct") is not None for item in buckets)
                else None
            ),
            "source_quality_gate": "pass" if any(item.get("source_quality_gate") == "pass" for item in buckets) else "hold_sample",
            "unknown_reason_counts": dict(sum((Counter(item.get("unknown_reason_counts") or {}) for item in buckets), Counter())),
            "workorder_count": len(workorders),
            "runtime_candidate_count": 0,
        },
        "buckets": buckets[:200],
        "runtime_approval_candidates": [],
        "code_improvement_workorders": workorders,
    }


def _exit_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exit_rows = [row for row in rows if str(row.get("stage") or "") == "exit"]
    bucket_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in exit_rows:
        buckets = _exit_bucket_features(row)
        for bucket_type, bucket_key in buckets.items():
            bucket_groups[(bucket_type, bucket_key)].append(row)
        combo_key = "|".join(
            [
                f"source={buckets['exit_source_stage']}",
                f"rule={buckets['exit_rule']}",
                f"outcome={buckets['exit_outcome']}",
                f"profit={buckets['profit_band']}",
            ]
        )
        bucket_groups[("combo_exit_result", combo_key)].append(row)
    buckets = [
        _stage_bucket_row(
            stage="exit",
            bucket_type=bucket_type,
            bucket_key=bucket_key,
            rows=subset,
            field_map=EXIT_BUCKET_FIELD_MAP,
            sample_floor=EXIT_BUCKET_SAMPLE_FLOOR,
        )
        for (bucket_type, bucket_key), subset in bucket_groups.items()
    ]
    buckets.sort(key=lambda item: (str(item.get("bucket_type") or ""), -int(item.get("joined_sample") or 0), str(item.get("bucket_key") or "")))
    workorder_buckets = [
        item
        for item in buckets
        if item.get("recommended_route") in {"source_quality_workorder", "candidate_tighten_or_exclude", "candidate_recovery_or_relax"}
    ][:10]
    workorders = [
        {
            "workorder_id": f"exit_bucket_source_quality_{idx+1}",
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "reason": "exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation",
            "recommended_route": item.get("recommended_route"),
            "metric_role": "source_quality_gate",
            "implementation_status": "open" if item.get("recommended_route") == "source_quality_workorder" else "implemented",
            "implementation_provenance": {
                "source_field_coverage": item.get("source_field_coverage") or {},
                "unknown_reason_counts": item.get("unknown_reason_counts") or {},
                "recommended_resolution": item.get("recommended_resolution"),
                "ai_inference_proposal": item.get("ai_inference_proposal"),
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for idx, item in enumerate(workorder_buckets)
    ]
    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "adm_ldm_exit_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "window_policy": "daily_lifecycle_exit_rows_plus_threshold_cycle_rolling_consumer",
        "sample_floor": EXIT_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "exit rows + joined source labels + parent lifecycle flow required for promotion",
        "forbidden_uses": ["stage_only_live_promotion", "broker_order_submit", "intraday_threshold_mutation", "provider_route_change", "bot_restart_trigger"],
        "summary": {
            "exit_rows": len(exit_rows),
            "source_row_count": len(exit_rows),
            "bucket_count": len(buckets),
            "joined_sample": sum(int(item.get("joined_sample") or 0) for item in buckets),
            "source_quality_adjusted_ev_pct": (
                round(
                    sum(float(item["source_quality_adjusted_ev_pct"]) * int(item.get("joined_sample") or 0) for item in buckets if item.get("source_quality_adjusted_ev_pct") is not None)
                    / sum(int(item.get("joined_sample") or 0) for item in buckets if item.get("source_quality_adjusted_ev_pct") is not None),
                    4,
                )
                if any(item.get("source_quality_adjusted_ev_pct") is not None for item in buckets)
                else None
            ),
            "source_quality_gate": "pass" if any(item.get("source_quality_gate") == "pass" for item in buckets) else "hold_sample",
            "unknown_reason_counts": dict(sum((Counter(item.get("unknown_reason_counts") or {}) for item in buckets), Counter())),
            "workorder_count": len(workorders),
            "runtime_candidate_count": 0,
        },
        "buckets": buckets[:200],
        "runtime_approval_candidates": [],
        "code_improvement_workorders": workorders,
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


def _slug(value: Any, *, max_len: int = 96) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:max_len] or "unknown"


def _stable_flow_bucket_id(bucket_key: str) -> str:
    digest = hashlib.sha1(str(bucket_key or "").encode("utf-8")).hexdigest()[:10]
    return f"lifecycle_flow:combo_lifecycle_flow:{_slug(bucket_key, max_len=56)}:{digest}"


def _entry_adm_bridge_key(stock_code: Any, *candidate_values: Any) -> str:
    code = str(stock_code or "").strip().lstrip("A")
    for value in candidate_values:
        text = str(value or "").strip()
        if not text:
            continue
        match = re.match(r"^ADM-([A-Za-z0-9]+)-([A-Za-z0-9]+)-", text)
        if match:
            return f"entry_adm_source:{match.group(1).lstrip('A')}:{match.group(2)}"
        if code and re.fullmatch(r"[0-9]+", text):
            return f"entry_adm_source:{code}:{text}"
    return ""


def _row_flow_identity(row: dict[str, Any]) -> tuple[str, str]:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    bridge_key = str(
        features.get("lifecycle_flow_bridge_key")
        or features.get("lifecycle_join_bridge_key")
        or features.get("join_bridge_key")
        or ""
    ).strip()
    if bridge_key:
        return f"lifecycle_flow_bridge_key:{bridge_key}", "lifecycle_flow_bridge_key"
    row_candidate_id = str(row.get("candidate_id") or "").strip()
    bridge_candidate_id = (
        row_candidate_id
        if row.get("source") == "scalp_entry_action_decision_matrix" or row_candidate_id.startswith("ADM-")
        else ""
    )
    adm_bridge_key = _entry_adm_bridge_key(
        row.get("stock_code"),
        features.get("entry_adm_candidate_id"),
        bridge_candidate_id,
    )
    if adm_bridge_key:
        return adm_bridge_key, "entry_adm_bridge_key"
    sim_record_id = str(features.get("sim_record_id") or "").strip()
    if sim_record_id:
        return f"sim_record_id:{sim_record_id}", "exact_sim_record_id"
    entry_adm_candidate_id = str(features.get("entry_adm_candidate_id") or "").strip()
    if entry_adm_candidate_id:
        return f"entry_adm_candidate_id:{entry_adm_candidate_id}", "entry_adm_candidate_id"
    candidate_id = str(row.get("candidate_id") or "").strip()
    if candidate_id:
        return f"candidate_id:{candidate_id}", "candidate_id"
    code = str(row.get("stock_code") or "").strip()
    event_time = str(row.get("event_time") or "").strip()
    return f"fallback:{code}:{event_time}", "fallback_incomplete"


def _flow_incomplete_reasons(flow: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if flow.get("identity_quality") == "fallback_incomplete":
        reasons.append("fallback_identity_incomplete")
    presence = flow.get("stage_presence") if isinstance(flow.get("stage_presence"), dict) else {}
    for stage in LIFECYCLE_FLOW_REQUIRED_STAGES:
        if not presence.get(stage):
            reasons.append(f"missing_{stage}")
    present_required = [stage for stage in LIFECYCLE_FLOW_REQUIRED_STAGES if presence.get(stage)]
    quality = str(flow.get("identity_quality") or "")
    if quality == "candidate_id" and len(present_required) < len(LIFECYCLE_FLOW_REQUIRED_STAGES):
        reasons.append("candidate_id_only")
    if quality == "exact_sim_record_id" and len(present_required) < len(LIFECYCLE_FLOW_REQUIRED_STAGES):
        reasons.append("sim_record_id_only")
    if quality == "entry_adm_candidate_id" and len(present_required) < len(LIFECYCLE_FLOW_REQUIRED_STAGES):
        reasons.append("entry_adm_candidate_id_only")
    if presence.get("exit") and not presence.get("entry"):
        reasons.append("postclose_exit_without_entry")
    if presence.get("scale_in") and not any(presence.get(stage) for stage in LIFECYCLE_FLOW_REQUIRED_STAGES):
        reasons.append("scale_in_noise_only")
    return list(dict.fromkeys(reasons))


def _flow_identity_stage_summary(rows: list[dict[str, Any]], flows: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage = {
        stage: [row for row in rows if str(row.get("stage") or "") == stage]
        for stage in ("entry", "submit", "holding", "scale_in", "exit")
    }
    stage_summary: dict[str, Any] = {}
    for stage, stage_rows in by_stage.items():
        quality_counts = Counter(_row_flow_identity(row)[1] for row in stage_rows)
        missing = quality_counts.get("fallback_incomplete", 0)
        present = len(stage_rows) - missing
        stage_summary[stage] = {
            "source_row_count": len(stage_rows),
            "identity_missing_count": missing,
            "identity_quality_counts": dict(quality_counts),
            "identity_join_rate": round(present / len(stage_rows), 4) if stage_rows else 0.0,
        }
    incomplete_reasons: Counter[str] = Counter()
    for flow in flows:
        incomplete_reasons.update(_flow_incomplete_reasons(flow))
    flow_count = len(flows)
    complete_flow_count = sum(1 for item in flows if item.get("stage_completion_state") == "complete")
    total_stage_rows = sum(len(stage_rows) for stage_rows in by_stage.values())
    identity_present_count = sum(
        item["source_row_count"] - item["identity_missing_count"]
        for item in stage_summary.values()
    )
    required_stage_counts = {
        stage: stage_summary.get(stage, {}).get("source_row_count", 0)
        for stage in LIFECYCLE_FLOW_REQUIRED_STAGES
    }
    required_sources_present = all(int(count or 0) > 0 for count in required_stage_counts.values())
    if required_sources_present and complete_flow_count == 0:
        incomplete_reasons["identity_namespace_mismatch"] += 1
        incomplete_reasons["join_contract_blocked"] += 1
        entry_qualities = set(stage_summary.get("entry", {}).get("identity_quality_counts", {}).keys())
        downstream_qualities = set()
        for stage in ("submit", "holding", "exit"):
            downstream_qualities.update(stage_summary.get(stage, {}).get("identity_quality_counts", {}).keys())
        if "candidate_id" in entry_qualities and "exact_sim_record_id" in downstream_qualities:
            incomplete_reasons["entry_candidate_id_to_sim_record_id_bridge_missing"] += 1
        if not {"entry_adm_candidate_id", "entry_adm_bridge_key"} & entry_qualities:
            incomplete_reasons["entry_adm_candidate_id_missing"] += 1
    return {
        "stage": stage_summary,
        "required_stage_source_counts": required_stage_counts,
        "required_sources_present": required_sources_present,
        "identity_missing_count": sum(item["identity_missing_count"] for item in stage_summary.values()),
        "identity_present_count": identity_present_count,
        "identity_join_rate": round(identity_present_count / total_stage_rows, 4) if total_stage_rows else 0.0,
        "complete_flow_count": complete_flow_count,
        "incomplete_flow_count": flow_count - complete_flow_count,
        "complete_flow_rate": round(complete_flow_count / flow_count, 4) if flow_count else 0.0,
        "incomplete_flow_reason_counts": dict(incomplete_reasons),
        "join_contract_blocked": bool(required_sources_present and complete_flow_count == 0),
    }


def _bucket_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    return f"{stage}:{bucket_type}:{_slug(bucket_key)}"


def _entry_combo_bucket_id(row: dict[str, Any]) -> str:
    buckets = _entry_bucket_features(row)
    bucket_key = "|".join(
        [
            f"score={buckets['score_band']}",
            f"source={buckets['source_stage']}",
            f"stale={buckets['stale_bucket']}",
            f"liquidity={buckets['liquidity_bucket']}",
            f"overbought={buckets['overbought_bucket']}",
            f"time={buckets['time_bucket']}",
        ]
    )
    return _bucket_id("entry", "combo_entry_spot", bucket_key)


def _submit_combo_bucket_id(row: dict[str, Any]) -> str:
    buckets = _submit_bucket_features(row)
    bucket_key = "|".join(
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
    return _bucket_id("submit", "combo_submit_quality", bucket_key)


def _holding_combo_bucket_id(row: dict[str, Any]) -> str:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    bucket_key = "|".join(
        [
            f"source={_bucket_value(row.get('source_stage'), 'holding_source_unknown')}",
            f"action={_holding_action_bucket(row)}",
            f"profit={_numeric_band(features.get('profit_rate_live'), prefix='profit', cuts=[(-0.7, 'lt_neg070'), (-0.1, 'neg070_neg010'), (0.8, 'neg010_pos080'), (1.5, 'pos080_pos150'), (3.0, 'pos150_pos300')], unknown='profit_unknown')}",
            f"held={_holding_held_bucket(row)}",
        ]
    )
    return _bucket_id("holding", "combo_holding_flow", bucket_key)


def _scale_in_child_bucket_ids(rows: list[dict[str, Any]]) -> list[str]:
    bucket_ids: list[str] = []
    for row in rows:
        buckets = _scale_in_bucket_features(row)
        arm = buckets.get("arm") or "arm_unknown"
        bucket_ids.append(_bucket_id("scale_in", "arm", arm))
    return list(dict.fromkeys(bucket_ids))


def _exit_combo_bucket_id(row: dict[str, Any]) -> str:
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    bucket_key = "|".join(
        [
            f"source={_bucket_value(row.get('source_stage'), 'exit_source_unknown')}",
            f"rule={_bucket_value(labels.get('exit_rule') or features.get('chosen_action'), 'exit_rule_unknown')}",
            f"outcome={_exit_outcome_bucket(row)}",
            f"profit={_numeric_band(labels.get('profit_rate'), prefix='profit', cuts=[(-0.7, 'lt_neg070'), (-0.1, 'neg070_neg010'), (0.8, 'neg010_pos080'), (1.5, 'pos080_pos150'), (3.0, 'pos150_pos300')], unknown='profit_unknown')}",
        ]
    )
    return _bucket_id("exit", "combo_exit_result", bucket_key)


def _first_stage_row(by_stage: dict[str, list[dict[str, Any]]], stage: str) -> dict[str, Any] | None:
    rows = by_stage.get(stage) or []
    if not rows:
        return None
    return sorted(rows, key=lambda item: str(item.get("event_time") or ""))[0]


def _flow_ev(by_stage: dict[str, list[dict[str, Any]]]) -> float | None:
    exit_row = _first_stage_row(by_stage, "exit")
    if exit_row is not None:
        ev = _safe_float(exit_row.get("stage_ev_composite_pct"), None)
        if ev is not None:
            return round(float(ev), 4)
    values = [
        float(value)
        for rows in by_stage.values()
        for row in rows
        for value in [_safe_float(row.get("stage_ev_composite_pct"), None)]
        if value is not None
    ]
    return round(sum(values) / len(values), 4) if values else None


def _flow_record(attribution_key: str, identity_quality: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[str(row.get("stage") or "unknown")].append(row)
    entry_row = _first_stage_row(by_stage, "entry")
    submit_row = _first_stage_row(by_stage, "submit")
    holding_row = _first_stage_row(by_stage, "holding")
    exit_row = _first_stage_row(by_stage, "exit")
    scale_in_rows = by_stage.get("scale_in") or []
    child_bucket_ids = {
        "entry": _entry_combo_bucket_id(entry_row) if entry_row else None,
        "submit": _submit_combo_bucket_id(submit_row) if submit_row else None,
        "holding": _holding_combo_bucket_id(holding_row) if holding_row else None,
        "scale_in": _scale_in_child_bucket_ids(scale_in_rows),
        "exit": _exit_combo_bucket_id(exit_row) if exit_row else None,
    }
    stage_presence = {stage: bool(by_stage.get(stage)) for stage in LIFECYCLE_FLOW_REQUIRED_STAGES}
    complete = all(stage_presence.values())
    ev = _flow_ev(by_stage)
    if identity_quality == "fallback_incomplete":
        source_quality = "fallback_identity_incomplete"
    elif not complete:
        source_quality = "incomplete_lifecycle_flow"
    elif ev is None:
        source_quality = "outcome_join_missing"
    else:
        source_quality = "pass"
    deterministic_completion = "complete_lifecycle_flow" if complete else "incomplete_lifecycle_flow"
    scale_bucket = child_bucket_ids["scale_in"][0] if child_bucket_ids["scale_in"] else "scale_in:none"
    bucket_key = "|".join(
        [
            f"entry={child_bucket_ids['entry'] or 'entry:missing'}",
            f"submit={child_bucket_ids['submit'] or 'submit:missing'}",
            f"holding={child_bucket_ids['holding'] or 'holding:missing'}",
            f"scale_in={scale_bucket}",
            f"exit={child_bucket_ids['exit'] or 'exit:missing'}",
        ]
    )
    bucket_id = _stable_flow_bucket_id(bucket_key)
    labels = exit_row.get("labels") if exit_row and isinstance(exit_row.get("labels"), dict) else {}
    return {
        "flow_instance_id": attribution_key,
        "identity_quality": identity_quality,
        "lifecycle_flow_bucket_id": bucket_id,
        "bucket_type": "combo_lifecycle_flow",
        "bucket_key": bucket_key,
        "attribution_key": attribution_key,
        "stage_presence": stage_presence,
        "stage_completion_state": "complete" if complete else "incomplete",
        "incomplete_reasons": _flow_incomplete_reasons(
            {
                "identity_quality": identity_quality,
                "stage_presence": stage_presence,
            }
        ),
        "entry_bucket_id": child_bucket_ids["entry"],
        "submit_bucket_id": child_bucket_ids["submit"],
        "holding_bucket_id": child_bucket_ids["holding"],
        "scale_in_bucket_id": scale_bucket if scale_bucket != "scale_in:none" else None,
        "scale_in_bucket_ids": child_bucket_ids["scale_in"],
        "exit_bucket_id": child_bucket_ids["exit"],
        "child_bucket_ids": child_bucket_ids,
        "stage_contract": {
            stage: {
                "stage": stage,
                "row_count": len(by_stage.get(stage) or []),
                "bucket_id": child_bucket_ids.get(stage),
                "contract_state": "present" if by_stage.get(stage) else "missing_policy",
            }
            for stage in LIFECYCLE_FLOW_REQUIRED_STAGES
        },
        "sample": 1,
        "joined_sample": 1 if ev is not None and complete else 0,
        "source_quality_gate": source_quality,
        "ai_inference_proposal": _ai_inference_proposal(
            decision_point="lifecycle_flow_completeness_and_identity_quality",
            deterministic_decision=deterministic_completion,
            bucket_type="combo_lifecycle_flow",
            bucket_key=bucket_key,
            source_quality_gate=source_quality,
            reason="parallel_ai_inference_for_lifecycle_flow_completeness_and_identity_quality",
        ),
        "source_quality_adjusted_ev_pct": ev,
        "equal_weight_avg_profit_pct": _safe_float(labels.get("profit_rate"), None),
        "diagnostic_win_rate": 1.0 if _safe_float(labels.get("profit_rate"), None) and _safe_float(labels.get("profit_rate"), 0.0) > 0 else 0.0 if labels.get("profit_rate") is not None else None,
        "outcome_state": "completed" if exit_row and ev is not None else "open_or_unjoined",
        "actual_order_submitted": any(bool(row.get("actual_order_submitted")) for row in rows),
        "broker_order_forbidden": all(
            bool((row.get("runtime_features") or {}).get("broker_order_forbidden"))
            for row in rows
            if isinstance(row.get("runtime_features"), dict)
        ),
        "metric_scope": "lifecycle_bundle_ev",
        "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
        "decision_authority": "adm_ldm_lifecycle_flow_bucket_attribution_source_only",
        "runtime_effect": False,
    }


def _lifecycle_flow_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("stage") or "") not in {"entry", "submit", "holding", "scale_in", "exit"}:
            continue
        identity, quality = _row_flow_identity(row)
        grouped[(identity, quality)].append(row)
    flows = [
        _flow_record(identity, quality, subset)
        for (identity, quality), subset in grouped.items()
    ]
    bucket_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for flow in flows:
        bucket_groups[str(flow.get("bucket_key") or "")].append(flow)
    buckets: list[dict[str, Any]] = []
    for bucket_key, subset in bucket_groups.items():
        joined = [item for item in subset if item.get("source_quality_adjusted_ev_pct") is not None]
        ev_values = [float(item["source_quality_adjusted_ev_pct"]) for item in joined]
        profit_values = [
            _safe_float(item.get("equal_weight_avg_profit_pct"), None)
            for item in joined
            if item.get("equal_weight_avg_profit_pct") is not None
        ]
        valid_profit = [float(value) for value in profit_values if value is not None]
        avg_ev = round(sum(ev_values) / len(ev_values), 4) if ev_values else None
        fallback_count = sum(1 for item in subset if item.get("identity_quality") == "fallback_incomplete")
        incomplete_count = sum(1 for item in subset if item.get("stage_completion_state") != "complete")
        source_quality = (
            "pass"
            if len(subset) >= LIFECYCLE_FLOW_BUCKET_SAMPLE_FLOOR
            and len(joined) >= LIFECYCLE_FLOW_BUCKET_SAMPLE_FLOOR
            and fallback_count == 0
            and incomplete_count == 0
            else "hold_sample_or_incomplete_flow"
        )
        if incomplete_count:
            source_quality = "join_contract_blocked"
        if avg_ev is None or source_quality != "pass":
            recommended_route = "hold_sample"
        elif avg_ev <= LIFECYCLE_FLOW_BUCKET_NEGATIVE_EV_PCT:
            recommended_route = "candidate_tighten_or_exclude"
        elif avg_ev >= LIFECYCLE_FLOW_BUCKET_POSITIVE_EV_PCT:
            recommended_route = "candidate_recovery_or_relax"
        else:
            recommended_route = "hold_no_edge"
        first = subset[0]
        buckets.append(
            {
                "lifecycle_flow_bucket_id": first.get("lifecycle_flow_bucket_id"),
                "bucket_type": "combo_lifecycle_flow",
                "bucket_key": bucket_key,
                "sample": len(subset),
                "joined_sample": len(joined),
                "join_rate": round(len(joined) / len(subset), 4) if subset else 0.0,
                "complete_flow_count": len(subset) - incomplete_count,
                "incomplete_flow_count": incomplete_count,
                "fallback_identity_count": fallback_count,
                "source_quality_gate": source_quality,
                "source_quality_adjusted_ev_pct": avg_ev,
                "equal_weight_avg_profit_pct": round(sum(valid_profit) / len(valid_profit), 4) if valid_profit else None,
                "diagnostic_win_rate": (
                    round(sum(1 for value in valid_profit if value > 0) / len(valid_profit), 4)
                    if valid_profit
                    else None
                ),
                "recommended_route": recommended_route,
                "ai_inference_proposal": _ai_inference_proposal(
                    decision_point="lifecycle_flow_bucket_classification",
                    deterministic_decision=recommended_route,
                    bucket_type="combo_lifecycle_flow",
                    bucket_key=bucket_key,
                    source_quality_gate=source_quality,
                    reason="parallel_ai_inference_for_lifecycle_parent_bucket_decision",
                ),
                "metric_scope": "lifecycle_bundle_ev",
                "entry_bucket_id": first.get("entry_bucket_id"),
                "submit_bucket_id": first.get("submit_bucket_id"),
                "holding_bucket_id": first.get("holding_bucket_id"),
                "scale_in_bucket_id": first.get("scale_in_bucket_id"),
                "scale_in_bucket_ids": first.get("scale_in_bucket_ids") or [],
                "exit_bucket_id": first.get("exit_bucket_id"),
                "child_bucket_ids": first.get("child_bucket_ids") or {},
                "stage_contract": first.get("stage_contract") or {},
                "attribution_key": first.get("attribution_key"),
                "rollback_guard": first.get("rollback_guard"),
                "decision_authority": "adm_ldm_lifecycle_flow_bucket_attribution_source_only",
                "runtime_effect": False,
                "forbidden_uses": [
                    "entry_only_full_lifecycle_promotion",
                    "hard_safety_bypass",
                    "intraday_threshold_mutation",
                    "broker_order_submit",
                    "provider_route_change",
                    "bot_restart_trigger",
                ],
            }
        )
    buckets.sort(
        key=lambda item: (
            0 if item.get("source_quality_gate") == "pass" else 1,
            -int(item.get("joined_sample") or 0),
            str(item.get("bucket_key") or ""),
        )
    )
    runtime_candidates = [
        {
            "candidate_id": f"lifecycle_flow_bucket_{idx+1}",
            "lifecycle_flow_bucket_id": item.get("lifecycle_flow_bucket_id"),
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "recommended_route": item.get("recommended_route"),
            "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
            "joined_sample": item.get("joined_sample"),
            "approval_required": False,
            "allowed_runtime_apply": False,
            "next_route": "lifecycle_bucket_discovery_greenfield_bundle_contract",
        }
        for idx, item in enumerate(buckets)
        if item.get("source_quality_gate") == "pass"
        and item.get("recommended_route") == "candidate_recovery_or_relax"
        and int(item.get("joined_sample") or 0) >= LIFECYCLE_FLOW_BUCKET_PROMOTE_SAMPLE_FLOOR
    ][:10]
    incomplete_flows = [item for item in flows if item.get("source_quality_gate") != "pass"]
    workorders = [
        {
            "workorder_id": f"lifecycle_flow_bucket_incomplete_{idx+1}",
            "reason": item.get("source_quality_gate"),
            "improvement_type": "join_gap_resolution",
            "join_gap_reasons": item.get("incomplete_reasons") or [],
            "required_producer_consumer_candidates": [
                "entry producer",
                "submit observation",
                "holding flow",
                "exit/post-sell feedback",
                "bridge key normalizer",
            ],
            "metric_role": "source_quality_gate",
            "implementation_status": "implemented",
            "ai_inference_proposal": _ai_inference_proposal(
                decision_point="incomplete_lifecycle_flow_workorder",
                deterministic_decision=str(item.get("source_quality_gate") or "incomplete_lifecycle_flow"),
                bucket_type=str(item.get("bucket_type") or "combo_lifecycle_flow"),
                bucket_key=str(item.get("bucket_key") or ""),
                source_quality_gate=str(item.get("source_quality_gate") or ""),
                reason="parallel_ai_inference_for_incomplete_flow_workorder",
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "lifecycle_flow_bucket_id": item.get("lifecycle_flow_bucket_id"),
        }
        for idx, item in enumerate(incomplete_flows[:20])
    ]
    identity_summary = _flow_identity_stage_summary(rows, flows)
    complete_flow_count = sum(1 for item in flows if item.get("stage_completion_state") == "complete")
    flow_count = len(flows)
    join_contract_blocked = bool(identity_summary.get("join_contract_blocked"))
    incomplete_reason_counts = identity_summary["incomplete_flow_reason_counts"]
    top_incomplete_reason = (
        max(incomplete_reason_counts.items(), key=lambda item: (int(item[1] or 0), str(item[0])))[0]
        if incomplete_reason_counts
        else None
    )
    return {
        "metric_role": "primary_ev",
        "metric_scope": "lifecycle_bundle_ev",
        "decision_authority": "adm_ldm_lifecycle_flow_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "window_policy": "daily_lifecycle_flow_rows_plus_threshold_cycle_rolling_consumer",
        "sample_floor": LIFECYCLE_FLOW_BUCKET_SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry+submit+holding+exit complete flow + stable identity + joined outcome",
        "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
        "forbidden_uses": [
            "entry_only_full_lifecycle_promotion",
            "hard_safety_bypass",
            "intraday_threshold_mutation",
            "broker_order_submit",
            "provider_route_change",
            "bot_restart_trigger",
        ],
        "summary": {
            "flow_count": flow_count,
            "complete_flow_count": complete_flow_count,
            "incomplete_flow_count": flow_count - complete_flow_count,
            "fallback_identity_count": sum(1 for item in flows if item.get("identity_quality") == "fallback_incomplete"),
            "identity_missing_count": identity_summary["identity_missing_count"],
            "identity_present_count": identity_summary["identity_present_count"],
            "identity_join_rate": identity_summary["identity_join_rate"],
            "complete_flow_rate": identity_summary["complete_flow_rate"],
            "join_contract_blocked": join_contract_blocked,
            "bundle_ev_tuning_state": "blocked_join_gap" if join_contract_blocked else "ready_for_bundle_ev_tuning",
            "top_incomplete_reason": top_incomplete_reason,
            "stage_identity": identity_summary["stage"],
            "required_stage_source_counts": identity_summary["required_stage_source_counts"],
            "incomplete_flow_reason_counts": incomplete_reason_counts,
            "bucket_count": len(buckets),
            "runtime_candidate_count": len(runtime_candidates),
            "workorder_count": len(workorders),
        },
        "flows": flows[:200],
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
    holding_bucket_attribution = _holding_bucket_attribution(rows)
    exit_bucket_attribution = _exit_bucket_attribution(rows)
    scale_in_bucket_attribution = _scale_in_bucket_attribution(rows)
    overnight_bucket_attribution = _overnight_bucket_attribution(rows)
    lifecycle_flow_bucket_attribution = _lifecycle_flow_bucket_attribution(rows)
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
            "holding_bucket_count": (
                holding_bucket_attribution.get("summary", {}).get("bucket_count")
                if isinstance(holding_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "holding_bucket_workorder_count": (
                holding_bucket_attribution.get("summary", {}).get("workorder_count")
                if isinstance(holding_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "exit_bucket_count": (
                exit_bucket_attribution.get("summary", {}).get("bucket_count")
                if isinstance(exit_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "exit_bucket_workorder_count": (
                exit_bucket_attribution.get("summary", {}).get("workorder_count")
                if isinstance(exit_bucket_attribution.get("summary"), dict)
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
            "lifecycle_flow_bucket_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("bucket_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "lifecycle_flow_complete_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("complete_flow_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "complete_flow_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("complete_flow_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "incomplete_flow_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("incomplete_flow_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "lifecycle_flow_runtime_candidate_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("runtime_candidate_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "lifecycle_flow_workorder_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("workorder_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "identity_missing_count": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("identity_missing_count")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0
            ),
            "identity_join_rate": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("identity_join_rate")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0.0
            ),
            "complete_flow_rate": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("complete_flow_rate")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else 0.0
            ),
            "join_contract_blocked": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("join_contract_blocked")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else False
            ),
            "bundle_ev_tuning_state": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("bundle_ev_tuning_state")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else "missing_lifecycle_flow_attribution"
            ),
            "top_incomplete_reason": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("top_incomplete_reason")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else None
            ),
            "incomplete_flow_reason_counts": (
                lifecycle_flow_bucket_attribution.get("summary", {}).get("incomplete_flow_reason_counts")
                if isinstance(lifecycle_flow_bucket_attribution.get("summary"), dict)
                else {}
            ),
            "lifecycle_ai_context_feedback": _lifecycle_ai_context_feedback_summary(policy_entries),
            "status": "pass" if not warnings else "warning",
            "warnings": warnings,
        },
        "policy_entries": policy_entries,
        "lifecycle_flow_bucket_attribution": lifecycle_flow_bucket_attribution,
        "entry_bucket_attribution": entry_bucket_attribution,
        "submit_bucket_attribution": submit_bucket_attribution,
        "holding_bucket_attribution": holding_bucket_attribution,
        "exit_bucket_attribution": exit_bucket_attribution,
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
        f"- holding_bucket_count/workorders: `{summary.get('holding_bucket_count')}` / `{summary.get('holding_bucket_workorder_count')}`",
        f"- exit_bucket_count/workorders: `{summary.get('exit_bucket_count')}` / `{summary.get('exit_bucket_workorder_count')}`",
        f"- scale_in_bucket_actionable_count: `{summary.get('scale_in_bucket_actionable_count')}`",
        f"- scale_in_bucket_runtime_candidate_count: `{summary.get('scale_in_bucket_runtime_candidate_count')}`",
        f"- overnight_bucket_actionable_count: `{summary.get('overnight_bucket_actionable_count')}`",
        f"- overnight_bucket_runtime_candidate_count: `{summary.get('overnight_bucket_runtime_candidate_count')}`",
        f"- lifecycle_flow_bucket_count: `{summary.get('lifecycle_flow_bucket_count')}`",
        f"- lifecycle_flow_complete_count: `{summary.get('lifecycle_flow_complete_count')}`",
        f"- lifecycle_flow_runtime_candidate_count: `{summary.get('lifecycle_flow_runtime_candidate_count')}`",
        f"- identity_missing_count/join_rate: `{summary.get('identity_missing_count')}` / `{summary.get('identity_join_rate')}`",
        f"- complete_flow_rate: `{summary.get('complete_flow_rate')}`",
        f"- incomplete_flow_reason_counts: `{summary.get('incomplete_flow_reason_counts') or {}}`",
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
    lifecycle_flow_buckets = (
        report.get("lifecycle_flow_bucket_attribution")
        if isinstance(report.get("lifecycle_flow_bucket_attribution"), dict)
        else {}
    )
    lifecycle_flow_summary = (
        lifecycle_flow_buckets.get("summary")
        if isinstance(lifecycle_flow_buckets.get("summary"), dict)
        else {}
    )
    lines.extend(
        [
            "",
            "## Lifecycle Flow Bucket Attribution",
            "",
            f"- decision_authority: `{lifecycle_flow_buckets.get('decision_authority')}`",
            f"- metric_scope: `{lifecycle_flow_buckets.get('metric_scope')}`",
            f"- primary_decision_metric: `{lifecycle_flow_buckets.get('primary_decision_metric')}`",
            f"- summary: `{lifecycle_flow_summary}`",
            "",
            "| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |",
            "| --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in (lifecycle_flow_buckets.get("buckets") or [])[:20]:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{item.get('lifecycle_flow_bucket_id')}` | {item.get('sample')} | "
            f"{item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | "
            f"`{item.get('recommended_route')}` | `{item.get('source_quality_gate')}` |"
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
    for section_key, title in (
        ("holding_bucket_attribution", "Holding Bucket Attribution"),
        ("exit_bucket_attribution", "Exit Bucket Attribution"),
    ):
        stage_buckets = report.get(section_key) if isinstance(report.get(section_key), dict) else {}
        stage_summary = stage_buckets.get("summary") if isinstance(stage_buckets.get("summary"), dict) else {}
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                f"- decision_authority: `{stage_buckets.get('decision_authority')}`",
                f"- primary_decision_metric: `{stage_buckets.get('primary_decision_metric')}`",
                f"- allowed_runtime_apply: `{stage_buckets.get('allowed_runtime_apply')}`",
                f"- summary: `{stage_summary}`",
                "",
                "| bucket_type | bucket_key | sample | joined | ev | route |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        shown = 0
        for item in stage_buckets.get("buckets") or []:
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
        stage_workorders = stage_buckets.get("code_improvement_workorders") or []
        lines.extend(["", f"### {title} Workorders", ""])
        if stage_workorders:
            for item in stage_workorders:
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
