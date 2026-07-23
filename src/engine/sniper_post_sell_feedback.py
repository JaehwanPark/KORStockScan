"""Post-sell candidate recording and post-close evaluation."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from src.engine.log_archive_service import load_monitor_snapshot
from src.engine.monitor_snapshot_runtime import guard_stdin_heavy_build
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import read_jsonl
from src.utils.logger import log_error, log_info

_WRITE_LOCK = threading.RLock()
_RECORDED_KEYS: dict[tuple[str, str, str, str], float] = {}
_SIM_RECORDED_KEYS: dict[tuple[str, str, str, str], float] = {}
_WS_RETAIN_UNTIL: dict[str, float] = {}
POST_SELL_REPORT_SCHEMA_VERSION = 4
POST_SELL_FEEDBACK_HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)
POST_SELL_LONG_HORIZONS_MIN = (20, 30, 60)
HIGH_AI_HARD_STOP_SCORE_FLOOR = 70.0
HIGH_AI_HARD_STOP_EXIT_RULES = {
    "scalp_hard_stop_pct",
    "scalp_preset_hard_stop_pct",
}
SIM_POST_SELL_FORBIDDEN_USES = [
    "threshold mutation",
    "order guard mutation",
    "provider change",
    "bot restart",
    "broker order submit",
]
HIGH_AI_HARD_STOP_CONFLICT_FORBIDDEN_USES = [
    *SIM_POST_SELL_FORBIDDEN_USES,
    "hard stop relaxation",
    "automatic exit deferral",
    "runtime approval candidate",
]
HIGH_AI_HARD_STOP_CONFLICT_CONTRACT = {
    "metric_role": "exit_post_sell_dimension",
    "decision_authority": "source_only_exit_attribution_dimension",
    "window_policy": "same_day_post_sell_forward_window",
    "sample_floor": "rolling_window_required_before_any_workorder",
    "primary_decision_metric": "sim_post_decision_mfe_10m_pct",
    "source_quality_gate": "hard_stop exit_rule + numeric current_ai_score + post_sell_forward_metrics",
    "forbidden_uses": list(HIGH_AI_HARD_STOP_CONFLICT_FORBIDDEN_USES),
}


def _post_sell_dir() -> Path:
    path = DATA_DIR / "post_sell"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _candidate_path(target_date: str) -> Path:
    return _post_sell_dir() / f"post_sell_candidates_{target_date}.jsonl"


def _evaluation_path(target_date: str) -> Path:
    return _post_sell_dir() / f"post_sell_evaluations_{target_date}.jsonl"


def _sim_candidate_path(target_date: str) -> Path:
    return _post_sell_dir() / f"sim_post_sell_candidates_{target_date}.jsonl"


def _sim_evaluation_path(target_date: str) -> Path:
    return _post_sell_dir() / f"sim_post_sell_evaluations_{target_date}.jsonl"


def _append_jsonl(path: Path, payload: dict) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> list[dict]:
    return read_jsonl(path)


def _parse_datetime(value, default: datetime | None = None) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, "", "None"):
        return default
    candidate = str(value).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return default


def _minute_bucket(ts: datetime, bucket_min: int = 1) -> str:
    floored_min = (ts.minute // bucket_min) * bucket_min
    return ts.replace(minute=floored_min, second=0, microsecond=0).strftime("%H:%M")


def _safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, "", "None"):
            return int(float(default if default not in (None, "", "None") else 0))
        return int(float(value))
    except Exception:
        try:
            return int(float(default if default not in (None, "", "None") else 0))
        except Exception:
            return 0


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return float(default if default not in (None, "", "None") else 0.0)
        return float(value)
    except Exception:
        try:
            return float(default if default not in (None, "", "None") else 0.0)
        except Exception:
            return 0.0


def _minute_candle_meta(
    candles: list[dict], meta: dict | None = None, *, requested_limit: int | None = None
) -> dict:
    source_meta = dict(meta or {})
    source_meta.setdefault("api_id", "ka10080")
    source_meta.setdefault("requested_limit", requested_limit)
    source_meta.setdefault("received_count", len(candles or []))
    source_meta.setdefault("truncated_window", False)
    source_meta.setdefault("sort_direction_detected", "unknown")
    source_meta.setdefault("cont_yn_seen", False)
    source_meta.setdefault("next_key_seen", False)
    source_meta.setdefault("continuous_next_key_missing", False)
    source_meta.setdefault("continuous_page_limit_reached", False)
    source_meta.setdefault("rest_received_ts_ms", None)
    source_meta.setdefault("latest_source_timestamp", None)
    source_meta.setdefault(
        "source_time_basis", "response_received_epoch_ms_and_chart_bar_timestamp"
    )
    return source_meta


def _fetch_minute_candles_with_meta(
    kiwoom_utils, token: str, code: str, *, limit: int
) -> tuple[list[dict], dict]:
    if hasattr(kiwoom_utils, "get_minute_candles_ka10080_with_meta"):
        candles, meta = kiwoom_utils.get_minute_candles_ka10080_with_meta(
            token, code, limit=limit
        )
        candles = candles or []
        return candles, _minute_candle_meta(candles, meta, requested_limit=limit)
    candles = kiwoom_utils.get_minute_candles_ka10080(token, code, limit=limit) or []
    return candles, _minute_candle_meta(candles, requested_limit=limit)


def _minute_forward_source_quality(
    metrics_by_horizon: dict[int, dict], candle_meta: dict
) -> dict:
    bars_10m = _safe_int((metrics_by_horizon.get(10) or {}).get("bars"), 0)
    if bars_10m <= 0:
        status = "insufficient_window"
        gate = "source_quality_insufficient"
        reason = "no_ka10080_bars_in_forward_10m_window"
    elif bool(candle_meta.get("continuous_next_key_missing")):
        status = "partial_window"
        gate = "source_quality_warning"
        reason = "ka10080_continuation_key_missing"
    elif bool(candle_meta.get("continuous_page_limit_reached")):
        status = "partial_window"
        gate = "source_quality_warning"
        reason = "ka10080_continuation_page_limit_reached"
    elif bool(candle_meta.get("truncated_window")):
        status = "partial_window"
        gate = "source_quality_warning"
        reason = "ka10080_truncated_window"
    else:
        status = "pass"
        gate = "pass"
        reason = "ka10080_forward_window_available"
    return {
        "minute_candle_source_quality": status,
        "minute_candle_source_quality_gate": gate,
        "minute_candle_source_quality_reason": reason,
        "minute_candle_forward_10m_bars": bars_10m,
    }


def _safe_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, "", "None"):
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "none", "null"}:
        return False
    return default


ENTRY_SPLIT_POST_SELL_KEYS = (
    "entry_split_order_policy_applied",
    "entry_split_order_bucket",
    "entry_split_order_policy_version",
    "entry_split_order_policy_mode",
    "entry_split_order_variant_id",
    "entry_split_order_leg_count",
    "entry_split_order_price_offsets_ticks",
    "entry_split_order_qty_weight_min",
    "entry_split_order_qty_weight_max",
    "entry_split_order_runtime_default_policy_applied",
    "entry_split_order_operator_fallback_authorized",
)


def _entry_split_post_sell_fields(stock: dict) -> dict:
    fields: dict = {}
    for key in ENTRY_SPLIT_POST_SELL_KEYS:
        value = stock.get(key)
        if value not in (None, "", "-", "None", "none", "null"):
            fields[key] = value
    if fields.get("entry_split_order_variant_id"):
        fields["entry_split_order_policy_applied"] = _safe_bool(
            fields.get("entry_split_order_policy_applied"), True
        )
        return fields
    pending_orders = (
        stock.get("pending_entry_orders")
        if isinstance(stock.get("pending_entry_orders"), list)
        else []
    )
    for order in pending_orders:
        if not isinstance(order, dict):
            continue
        if not (
            _safe_bool(order.get("entry_split_order_policy_applied"))
            or order.get("entry_split_order_variant_id")
            or order.get("entry_split_order_policy_mode")
        ):
            continue
        for key in ENTRY_SPLIT_POST_SELL_KEYS:
            value = order.get(key)
            if value not in (None, "", "-", "None", "none", "null"):
                fields.setdefault(key, value)
        if fields.get("entry_split_order_variant_id"):
            fields["entry_split_order_policy_applied"] = _safe_bool(
                fields.get("entry_split_order_policy_applied"), True
            )
            break
    return fields


def _realized_result_label(profit_rate) -> str:
    value = _safe_float(profit_rate, 0.0)
    if value > 0.0:
        return "익절"
    if value < 0.0:
        return "손절"
    return "보합"


def _exit_rule_profit_mismatch(exit_rule, profit_rate) -> bool:
    rule = str(exit_rule or "").strip().lower()
    value = _safe_float(profit_rate, 0.0)
    if value <= 0.0:
        return False
    return any(
        marker in rule for marker in ("hard_stop", "soft_stop", "stop_loss", "loss")
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 1)


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(item) for item in values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 3)
    return round((ordered[mid - 1] + ordered[mid]) / 2.0, 3)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(item) for item in values)
    rank = ((len(ordered) - 1) * max(0.0, min(100.0, float(pct)))) / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return round(ordered[lower], 3)
    weight = rank - lower
    return round((ordered[lower] * (1.0 - weight)) + (ordered[upper] * weight), 3)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _ai_score_band(score: float) -> str:
    value = _safe_float(score, 0.0)
    if value <= 0.0:
        return "ai_score_missing"
    if value >= 80.0:
        return "ai_score_80_plus"
    if value >= 75.0:
        return "ai_score_75_79"
    if value >= HIGH_AI_HARD_STOP_SCORE_FLOOR:
        return "ai_score_70_74"
    if value >= 65.0:
        return "ai_score_65_69"
    return "ai_score_below_65"


def _ai_provenance_field(stock: dict, explicit_value, *keys: str) -> str:
    if explicit_value not in (None, "", "None"):
        return str(explicit_value)
    for key in keys:
        value = stock.get(key)
        if value not in (None, "", "None"):
            return str(value)
    return "-"


def _stock_ai_score_fallback(stock: dict) -> float:
    for key in (
        "scalp_sim_ai_last_smoothed_score",
        "scalp_sim_ai_last_score",
        "last_exit_current_ai_score",
    ):
        value = stock.get(key)
        if value not in (None, "", "None"):
            return _safe_float(value, 0.0)
    rt_prob = _safe_float(stock.get("rt_ai_prob"), 0.0)
    if 0.0 < rt_prob <= 1.0:
        return rt_prob * 100.0
    return _safe_float(stock.get("rt_ai_prob"), 0.0)


def _build_high_ai_hard_stop_conflict_fields(
    *,
    exit_rule,
    current_ai_score,
    ai_score_raw=None,
    ai_action=None,
    ai_result_source=None,
    ai_model=None,
    ai_model_tier=None,
    ai_transport_mode=None,
) -> dict:
    resolved_exit_rule = str(exit_rule or "-")
    score = _safe_float(current_ai_score, 0.0)
    is_hard_stop = resolved_exit_rule in HIGH_AI_HARD_STOP_EXIT_RULES
    is_conflict = bool(is_hard_stop and score >= HIGH_AI_HARD_STOP_SCORE_FLOOR)
    if is_conflict:
        dimension_value = "high_ai_hard_stop_conflict"
    elif is_hard_stop and score <= 0.0:
        dimension_value = "hard_stop_ai_score_missing"
    elif is_hard_stop:
        dimension_value = "hard_stop_ai_not_high"
    else:
        dimension_value = "not_hard_stop"
    return {
        "high_ai_hard_stop_conflict": is_conflict,
        "hard_stop_conflict_dimension": dimension_value,
        "hard_stop_conflict_score_floor": HIGH_AI_HARD_STOP_SCORE_FLOOR,
        "hard_stop_conflict_ai_score_band": _ai_score_band(score),
        "hard_stop_conflict_runtime_effect": False,
        "hard_stop_conflict_allowed_runtime_apply": False,
        "hard_stop_conflict_hard_gate": False,
        "hard_stop_conflict_contract": dict(HIGH_AI_HARD_STOP_CONFLICT_CONTRACT),
        "ai_score_at_exit": round(score, 1),
        "ai_score_raw_at_exit": round(_safe_float(ai_score_raw, score), 1),
        "ai_action_at_exit": str(ai_action or "-"),
        "ai_result_source_at_exit": str(ai_result_source or "-"),
        "ai_model_at_exit": str(ai_model or "-"),
        "ai_model_tier_at_exit": str(ai_model_tier or "-"),
        "ai_transport_mode_at_exit": str(ai_transport_mode or "-"),
    }


def should_retain_ws_subscription(code: str, now_ts: float | None = None) -> bool:
    normalized = str(code or "").strip()[:6]
    if not normalized:
        return False

    current_ts = float(now_ts if now_ts is not None else time.time())
    with _WRITE_LOCK:
        until_ts = float(_WS_RETAIN_UNTIL.get(normalized, 0.0) or 0.0)
        if until_ts <= current_ts:
            _WS_RETAIN_UNTIL.pop(normalized, None)
            return False
        return True


def record_post_sell_candidate(
    *,
    recommendation_id=None,
    stock: dict | None = None,
    code: str | None = None,
    sell_time=None,
    buy_price=0,
    sell_price=0,
    profit_rate=0,
    buy_qty=0,
    exit_rule: str | None = None,
    strategy: str | None = None,
    revive: bool = False,
    peak_profit=None,
    held_sec=None,
    current_ai_score=None,
    soft_stop_threshold_pct=None,
    same_symbol_soft_stop_cooldown_would_block=None,
) -> dict | None:
    if not bool(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_ENABLED", True)):
        return None

    stock = stock or {}
    norm_code = str(code or stock.get("code") or "").strip()[:6]
    if not norm_code:
        return None

    safe_sell_price = _safe_int(sell_price, 0)
    if safe_sell_price <= 0:
        return None

    now = datetime.now()
    sell_dt = _parse_datetime(sell_time, default=now) or now
    target_date = sell_dt.strftime("%Y-%m-%d")
    sell_bucket = _minute_bucket(sell_dt, bucket_min=1)
    rec_id_text = str(_safe_int(recommendation_id, 0))
    dedupe_marker = (
        rec_id_text if rec_id_text != "0" else f"{sell_bucket}:{safe_sell_price}"
    )
    dedupe_key = (
        target_date,
        norm_code,
        rec_id_text,
        dedupe_marker,
    )

    with _WRITE_LOCK:
        if dedupe_key in _RECORDED_KEYS:
            return None

        resolved_exit_rule = str(exit_rule or stock.get("last_exit_rule") or "-")
        resolved_ai_score = round(
            _safe_float(current_ai_score, stock.get("last_exit_current_ai_score", 0.0)),
            1,
        )
        resolved_ai_raw = round(
            _safe_float(stock.get("last_exit_ai_score_raw"), resolved_ai_score), 1
        )
        resolved_ai_effective = round(
            _safe_float(stock.get("last_exit_ai_score_effective"), resolved_ai_score), 1
        )
        payload = {
            "post_sell_id": uuid.uuid4().hex[:16],
            "actual_order_submitted": True,
            "recorded_at": now.isoformat(),
            "signal_date": target_date,
            "recommendation_id": _safe_int(recommendation_id, 0),
            "sell_time": sell_dt.strftime("%H:%M:%S"),
            "sell_bucket": sell_bucket,
            "stock_code": norm_code,
            "stock_name": str(stock.get("name", "") or ""),
            "strategy": str(strategy or stock.get("strategy", "") or ""),
            "position_tag": str(stock.get("position_tag", "") or ""),
            "buy_price": _safe_int(buy_price, 0),
            "sell_price": safe_sell_price,
            "profit_rate": round(_safe_float(profit_rate, 0.0), 3),
            "buy_qty": _safe_int(buy_qty, 0),
            "exit_rule": resolved_exit_rule,
            "realized_result_label": _realized_result_label(profit_rate),
            "exit_rule_profit_mismatch": _exit_rule_profit_mismatch(
                resolved_exit_rule, profit_rate
            ),
            "exit_decision_source": str(stock.get("last_exit_decision_source") or "-"),
            "exit_decision_mark_price": (
                _safe_int(stock.get("fast_exit_decision_mark_price"), 0) or "-"
            ),
            "exit_decision_executable_sell_price": (
                _safe_int(
                    stock.get("fast_exit_decision_executable_sell_price"), 0
                )
                or "-"
            ),
            "exit_decision_peak_price": (
                _safe_int(stock.get("fast_exit_decision_peak_price"), 0) or "-"
            ),
            "exit_decision_quote_state": str(
                stock.get("fast_exit_decision_quote_state") or "-"
            ),
            "exit_decision_quote_reason": str(
                stock.get("fast_exit_decision_quote_reason") or "-"
            ),
            "actual_fill_price": safe_sell_price,
            "revive": bool(revive),
            "peak_profit": round(
                _safe_float(peak_profit, stock.get("last_exit_peak_profit", 0.0)), 3
            ),
            "held_sec": _safe_int(held_sec, stock.get("last_exit_held_sec", 0)),
            "current_ai_score": resolved_ai_score,
            "ai_score_raw": resolved_ai_raw,
            "ai_score_effective": resolved_ai_effective,
            "ai_action": str(stock.get("last_exit_ai_action") or "-"),
            "ai_result_source": str(stock.get("last_exit_ai_result_source") or "-"),
            "ai_model": str(stock.get("last_exit_ai_model") or "-"),
            "ai_model_tier": str(stock.get("last_exit_ai_model_tier") or "-"),
            "ai_transport_mode": str(stock.get("last_exit_ai_transport_mode") or "-"),
            "ai_data_quality": str(
                stock.get("last_exit_ai_data_quality")
                or stock.get("holding_score_data_quality")
                or "-"
            ),
            "soft_stop_threshold_pct": round(
                _safe_float(
                    soft_stop_threshold_pct,
                    stock.get("last_exit_soft_stop_threshold_pct", 0.0),
                ),
                3,
            ),
            "same_symbol_soft_stop_cooldown_would_block": bool(
                stock.get("last_exit_same_symbol_soft_stop_cooldown_would_block", False)
                if same_symbol_soft_stop_cooldown_would_block is None
                else same_symbol_soft_stop_cooldown_would_block
            ),
            "evaluation_mode": "post_sell_minute_forward",
            **_entry_split_post_sell_fields(stock),
        }
        for optional_key in (
            "no_scale_in_counterfactual_profit_pct",
            "scale_in_incremental_realized_delta_pct",
            "pre_add_avg_price",
            "post_add_avg_price",
            "pre_add_qty",
            "post_add_qty",
        ):
            if stock.get(optional_key) not in (None, "", "-", "None", "none", "null"):
                payload[optional_key] = stock.get(optional_key)
        payload.update(
            _build_high_ai_hard_stop_conflict_fields(
                exit_rule=resolved_exit_rule,
                current_ai_score=resolved_ai_score,
                ai_score_raw=payload["ai_score_raw"],
                ai_action=payload["ai_action"],
                ai_result_source=payload["ai_result_source"],
                ai_model=payload["ai_model"],
                ai_model_tier=payload["ai_model_tier"],
                ai_transport_mode=payload["ai_transport_mode"],
            )
        )

        _append_jsonl(_candidate_path(target_date), payload)
        _RECORDED_KEYS[dedupe_key] = now.timestamp()
        retain_minutes = int(
            getattr(TRADING_RULES, "POST_SELL_WS_RETAIN_MINUTES", 0) or 0
        )
        if retain_minutes > 0:
            retain_until = sell_dt.timestamp() + (retain_minutes * 60.0)
            current_until = float(_WS_RETAIN_UNTIL.get(norm_code, 0.0) or 0.0)
            if retain_until > current_until:
                _WS_RETAIN_UNTIL[norm_code] = retain_until
        log_info(
            f"[POST_SELL_CANDIDATE] {payload['stock_name']}({payload['stock_code']}) "
            f"sell={payload['sell_price']} ret={payload['profit_rate']:+.2f}% "
            f"exit_rule={payload['exit_rule']} revive={payload['revive']}"
        )
        return payload


def record_sim_post_sell_candidate(
    *,
    candidate_id=None,
    sim_record_id=None,
    sim_parent_record_id=None,
    stock: dict | None = None,
    code: str | None = None,
    sell_time=None,
    buy_price=0,
    sell_price=0,
    profit_rate=0,
    buy_qty=0,
    exit_rule: str | None = None,
    sell_reason_type: str | None = None,
    trigger_profit_rate=None,
    strategy: str | None = "SCALPING",
    source_event_stage: str = "scalp_sim_sell_order_assumed_filled",
    entry_event_emitted_at: str | None = None,
    entry_signal_time: str | None = None,
    entry_time_source: str | None = None,
    entry_record_id: str | None = None,
    entry_join_key: str | None = None,
    entry_join_status: str | None = None,
    current_ai_score=None,
    ai_score_raw=None,
    ai_action=None,
    ai_result_source=None,
    ai_model=None,
    ai_model_tier=None,
    ai_transport_mode=None,
    ai_data_quality=None,
) -> dict | None:
    if not bool(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_ENABLED", True)):
        return None

    stock = stock or {}
    norm_code = str(code or stock.get("code") or "").strip()[:6]
    if not norm_code:
        return None

    safe_sell_price = _safe_int(sell_price, 0)
    if safe_sell_price <= 0:
        return None

    now = datetime.now()
    sell_dt = _parse_datetime(sell_time, default=now) or now
    target_date = sell_dt.strftime("%Y-%m-%d")
    sell_bucket = _minute_bucket(sell_dt, bucket_min=1)
    sim_id = str(sim_record_id or stock.get("sim_record_id") or "").strip()
    sim_parent_id = str(
        sim_parent_record_id or stock.get("sim_parent_record_id") or ""
    ).strip()
    entry_candidate_id = str(
        candidate_id or stock.get("entry_adm_candidate_id") or ""
    ).strip()
    dedupe_marker = sim_id or sim_parent_id or f"{sell_bucket}:{safe_sell_price}"
    dedupe_key = (
        target_date,
        norm_code,
        "scalp_sim",
        dedupe_marker,
    )

    with _WRITE_LOCK:
        if dedupe_key in _SIM_RECORDED_KEYS:
            return None

        resolved_exit_rule = str(exit_rule or stock.get("last_exit_rule") or "-")
        resolved_ai_score = round(
            _safe_float(
                current_ai_score,
                _stock_ai_score_fallback(stock),
            ),
            1,
        )
        payload = {
            "schema_version": POST_SELL_REPORT_SCHEMA_VERSION,
            "report_type": "sim_post_sell_candidate",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "metric_role": "sim_post_sell_mfe_mae_observation",
            "decision_authority": "sim_equal_weight_observation_only",
            "window_policy": "same_day_post_sell_forward_window",
            "sample_floor": "report_only_no_hard_decision",
            "primary_decision_metric": "sim_post_decision_mfe_10m_pct",
            "source_quality_gate": "scalp_sim_sell_order_assumed_filled + numeric profit_rate",
            "forbidden_uses": list(SIM_POST_SELL_FORBIDDEN_USES),
            "post_sell_id": uuid.uuid4().hex[:16],
            "recorded_at": now.isoformat(),
            "signal_date": target_date,
            "sell_time": sell_dt.strftime("%H:%M:%S"),
            "sell_bucket": sell_bucket,
            "stock_code": norm_code,
            "stock_name": str(stock.get("name", "") or ""),
            "strategy": str(strategy or stock.get("strategy", "") or "SCALPING"),
            "position_tag": str(stock.get("position_tag", "") or ""),
            "buy_price": _safe_int(buy_price, stock.get("buy_price", 0)),
            "sell_price": safe_sell_price,
            "profit_rate": round(_safe_float(profit_rate, 0.0), 3),
            "buy_qty": _safe_int(buy_qty, stock.get("buy_qty", 0)),
            "exit_rule": resolved_exit_rule,
            "sell_reason_type": str(sell_reason_type or "-"),
            "trigger_profit_rate": round(
                _safe_float(trigger_profit_rate, _safe_float(profit_rate, 0.0)),
                3,
            ),
            "evaluation_mode": "sim_post_sell_minute_forward",
            "candidate_source": "scalp_simulator",
            "simulation_book": "scalp_ai_buy_all",
            "candidate_id": entry_candidate_id,
            "entry_adm_candidate_id": entry_candidate_id,
            "entry_event_emitted_at": str(
                entry_event_emitted_at
                or stock.get("entry_event_emitted_at")
                or stock.get("entry_adm_event_emitted_at")
                or ""
            ),
            "entry_signal_time": str(
                entry_signal_time
                or stock.get("entry_signal_time")
                or stock.get("signal_time")
                or stock.get("tick_latest_time")
                or ""
            ),
            "entry_time_source": str(
                entry_time_source
                or stock.get("entry_time_source")
                or "not_recorded_at_source"
            ),
            "entry_record_id": str(
                entry_record_id or stock.get("entry_record_id") or sim_parent_id or ""
            ),
            "entry_join_key": str(
                entry_join_key
                or stock.get("entry_join_key")
                or entry_candidate_id
                or sim_parent_id
                or ""
            ),
            "entry_join_status": str(
                entry_join_status
                or stock.get("entry_join_status")
                or "raw_append_only_unjoined"
            ),
            "sim_record_id": sim_id,
            "sim_parent_record_id": sim_parent_id,
            "source_event_stage": str(
                source_event_stage or "scalp_sim_sell_order_assumed_filled"
            ),
            "current_ai_score": resolved_ai_score,
            "ai_score_raw": round(
                _safe_float(
                    ai_score_raw,
                    stock.get(
                        "scalp_sim_ai_last_raw_score",
                        stock.get("scalp_sim_ai_last_score", resolved_ai_score),
                    ),
                ),
                1,
            ),
            "ai_action": _ai_provenance_field(
                stock, ai_action, "scalp_sim_ai_last_action", "last_exit_ai_action"
            ),
            "ai_result_source": _ai_provenance_field(
                stock,
                ai_result_source,
                "scalp_sim_ai_last_result_source",
                "last_exit_ai_result_source",
            ),
            "ai_model": _ai_provenance_field(
                stock, ai_model, "scalp_sim_ai_last_model", "last_exit_ai_model"
            ),
            "ai_model_tier": _ai_provenance_field(
                stock,
                ai_model_tier,
                "scalp_sim_ai_last_model_tier",
                "last_exit_ai_model_tier",
            ),
            "ai_transport_mode": _ai_provenance_field(
                stock,
                ai_transport_mode,
                "scalp_sim_ai_last_transport_mode",
                "last_exit_ai_transport_mode",
            ),
            "ai_data_quality": _ai_provenance_field(
                stock,
                ai_data_quality,
                "scalp_sim_ai_last_data_quality",
                "last_exit_ai_data_quality",
                "holding_score_data_quality",
            ),
        }
        payload.update(
            _build_high_ai_hard_stop_conflict_fields(
                exit_rule=resolved_exit_rule,
                current_ai_score=payload["current_ai_score"],
                ai_score_raw=payload["ai_score_raw"],
                ai_action=payload["ai_action"],
                ai_result_source=payload["ai_result_source"],
                ai_model=payload["ai_model"],
                ai_model_tier=payload["ai_model_tier"],
                ai_transport_mode=payload["ai_transport_mode"],
            )
        )

        _append_jsonl(_sim_candidate_path(target_date), payload)
        _SIM_RECORDED_KEYS[dedupe_key] = now.timestamp()
        log_info(
            f"[SIM_POST_SELL_CANDIDATE] {payload['stock_name']}({payload['stock_code']}) "
            f"sell={payload['sell_price']} ret={payload['profit_rate']:+.2f}% "
            f"sim_record_id={payload['sim_record_id'] or '-'}"
        )
        return payload


def _parse_minute_time(value: str, signal_date: str) -> datetime | None:
    try:
        return datetime.strptime(f"{signal_date} {value}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _compute_window_metrics(
    candidate: dict, candles: list[dict], window_minutes: int
) -> dict:
    signal_dt = datetime.strptime(
        f"{candidate['signal_date']} {candidate['sell_time']}",
        "%Y-%m-%d %H:%M:%S",
    )
    start_dt = signal_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end_dt = start_dt + timedelta(minutes=window_minutes)

    relevant = []
    for candle in candles:
        candle_dt = _parse_minute_time(
            str(candle.get("체결시간", "") or ""), candidate["signal_date"]
        )
        if candle_dt is None:
            continue
        if candle_dt < start_dt or candle_dt >= end_dt:
            continue
        relevant.append((candle_dt, candle))

    sell_price = float(candidate.get("sell_price", 0) or 0)
    buy_price = float(candidate.get("buy_price", 0) or 0)
    if sell_price <= 0 or not relevant:
        return {
            "close_ret_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "mfe_vs_buy_pct": 0.0,
            "close_vs_buy_pct": 0.0,
            "rebound_above_sell": False,
            "rebound_above_buy": False,
            "hit_up_05": False,
            "hit_up_10": False,
            "hit_down_05": False,
            "bars": len(relevant),
        }

    highs = []
    lows = []
    close_ret = 0.0
    highs_vs_buy = []
    close_vs_buy = 0.0

    for _, candle in relevant:
        high_p = float(candle.get("고가", 0) or 0)
        low_p = float(candle.get("저가", 0) or 0)
        close_p = float(candle.get("현재가", 0) or 0)

        if high_p > 0:
            highs.append(((high_p / sell_price) - 1.0) * 100.0)
        if low_p > 0:
            lows.append(((low_p / sell_price) - 1.0) * 100.0)
        if close_p > 0:
            close_ret = ((close_p / sell_price) - 1.0) * 100.0
        if buy_price > 0 and high_p > 0:
            highs_vs_buy.append(((high_p / buy_price) - 1.0) * 100.0)
        if buy_price > 0 and close_p > 0:
            close_vs_buy = ((close_p / buy_price) - 1.0) * 100.0

    mfe_pct = max(highs) if highs else 0.0
    mae_pct = min(lows) if lows else 0.0
    mfe_vs_buy_pct = max(highs_vs_buy) if highs_vs_buy else 0.0
    return {
        "close_ret_pct": round(close_ret, 3),
        "mfe_pct": round(mfe_pct, 3),
        "mae_pct": round(mae_pct, 3),
        "mfe_vs_buy_pct": round(mfe_vs_buy_pct, 3),
        "close_vs_buy_pct": round(close_vs_buy, 3),
        "rebound_above_sell": mfe_pct > 0.0,
        "rebound_above_buy": buy_price > 0 and mfe_vs_buy_pct >= 0.0,
        "hit_up_05": mfe_pct >= 0.5,
        "hit_up_10": mfe_pct >= 1.0,
        "hit_down_05": mae_pct <= -0.5,
        "bars": len(relevant),
    }


def _classify_candidate(metrics_10m: dict) -> str:
    missed_mfe = float(
        getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT", 0.8) or 0.8
    )
    missed_close = float(
        getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT", 0.3) or 0.3
    )
    good_mae = float(
        getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT", -0.6) or -0.6
    )
    good_close = float(
        getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT", -0.2) or -0.2
    )

    mfe = float(metrics_10m.get("mfe_pct", 0.0) or 0.0)
    mae = float(metrics_10m.get("mae_pct", 0.0) or 0.0)
    close_ret = float(metrics_10m.get("close_ret_pct", 0.0) or 0.0)

    if mfe >= missed_mfe and close_ret >= missed_close:
        return "MISSED_UPSIDE"
    if mae <= good_mae and close_ret <= good_close:
        return "GOOD_EXIT"
    return "NEUTRAL"


def _evaluation_has_current_horizons(evaluation: dict) -> bool:
    return all(
        isinstance(evaluation.get(f"metrics_{horizon}m"), dict)
        for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
    )


def _dedupe_latest_evaluations(evaluations: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for item in evaluations or []:
        post_sell_id = str(item.get("post_sell_id", "") or "")
        if not post_sell_id:
            continue
        by_id[post_sell_id] = item
    return list(by_id.values())


@dataclass
class PostSellFeedbackSummary:
    date: str
    total_candidates: int = 0
    evaluated_candidates: int = 0
    outcome_counts: dict[str, int] = field(default_factory=dict)
    minute_candle_source_quality_counts: dict[str, int] = field(default_factory=dict)
    missed_upside_cases: list[dict] = field(default_factory=list)
    good_exit_cases: list[dict] = field(default_factory=list)


def evaluate_post_sell_candidates(
    target_date: str, token: str | None = None
) -> PostSellFeedbackSummary:
    try:
        from src.utils import kiwoom_utils
    except Exception as exc:
        log_error(f"[POST_SELL_EVAL] kiwoom_utils import failed: {exc}")
        kiwoom_utils = None

    candidates = _load_jsonl(_candidate_path(target_date))
    existing_evaluations = _load_jsonl(_evaluation_path(target_date))
    evaluated_ids = {
        str(item.get("post_sell_id", ""))
        for item in existing_evaluations
        if _evaluation_has_current_horizons(item)
    }
    summary = PostSellFeedbackSummary(date=target_date)
    summary.total_candidates = len(candidates)

    if not bool(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_EVAL_ENABLED", True)):
        summary.evaluated_candidates = len(existing_evaluations)
        return summary

    candle_cache: dict[str, tuple[list[dict], dict]] = {}
    new_evaluations: list[dict] = []
    token_fetch_attempted = token is not None

    for candidate in candidates:
        post_sell_id = str(candidate.get("post_sell_id", "") or "")
        code = str(candidate.get("stock_code", "") or "")
        if (
            not post_sell_id
            or not code
            or post_sell_id in evaluated_ids
            or kiwoom_utils is None
        ):
            continue

        if token is None and not token_fetch_attempted:
            token_fetch_attempted = True
            try:
                token = kiwoom_utils.get_kiwoom_token()
            except Exception as exc:
                log_error(f"[POST_SELL_EVAL] token fetch failed: {exc}")
                token = None

        if token is None:
            continue

        if code not in candle_cache:
            try:
                candle_cache[code] = _fetch_minute_candles_with_meta(
                    kiwoom_utils, token, code, limit=700
                )
            except Exception as exc:
                log_error(f"[POST_SELL_EVAL] {code} minute candles fetch failed: {exc}")
                candle_cache[code] = ([], _minute_candle_meta([], requested_limit=700))

        candles, candle_meta = candle_cache.get(
            code, ([], _minute_candle_meta([], requested_limit=700))
        )
        metrics_by_horizon = {
            horizon: _compute_window_metrics(candidate, candles, horizon)
            for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
        }
        metrics_10m = metrics_by_horizon[10]
        outcome = _classify_candidate(metrics_10m)
        source_quality = _minute_forward_source_quality(metrics_by_horizon, candle_meta)

        evaluation = {
            "post_sell_id": post_sell_id,
            "actual_order_submitted": True,
            "evaluated_at": datetime.now().isoformat(),
            "signal_date": target_date,
            "stock_code": code,
            "stock_name": candidate.get("stock_name", ""),
            "recommendation_id": candidate.get("recommendation_id", 0),
            "strategy": candidate.get("strategy", ""),
            "position_tag": candidate.get("position_tag", ""),
            "sell_time": candidate.get("sell_time", ""),
            "sell_bucket": candidate.get("sell_bucket", ""),
            "buy_price": candidate.get("buy_price", 0),
            "sell_price": candidate.get("sell_price", 0),
            "profit_rate": candidate.get("profit_rate", 0.0),
            "buy_qty": candidate.get("buy_qty", 0),
            "exit_rule": candidate.get("exit_rule", "-"),
            "realized_result_label": candidate.get(
                "realized_result_label",
                _realized_result_label(candidate.get("profit_rate", 0.0)),
            ),
            "exit_rule_profit_mismatch": bool(
                candidate.get(
                    "exit_rule_profit_mismatch",
                    _exit_rule_profit_mismatch(
                        candidate.get("exit_rule", "-"),
                        candidate.get("profit_rate", 0.0),
                    ),
                )
            ),
            "revive": bool(candidate.get("revive", False)),
            "peak_profit": candidate.get("peak_profit", 0.0),
            "held_sec": candidate.get("held_sec", 0),
            "current_ai_score": candidate.get("current_ai_score", 0.0),
            "high_ai_hard_stop_conflict": _safe_bool(
                candidate.get("high_ai_hard_stop_conflict", False)
            ),
            "hard_stop_conflict_dimension": candidate.get(
                "hard_stop_conflict_dimension", "not_hard_stop"
            ),
            "hard_stop_conflict_score_floor": candidate.get(
                "hard_stop_conflict_score_floor",
                HIGH_AI_HARD_STOP_SCORE_FLOOR,
            ),
            "hard_stop_conflict_ai_score_band": candidate.get(
                "hard_stop_conflict_ai_score_band",
                "ai_score_missing",
            ),
            "hard_stop_conflict_runtime_effect": False,
            "hard_stop_conflict_allowed_runtime_apply": False,
            "hard_stop_conflict_hard_gate": False,
            "hard_stop_conflict_contract": candidate.get(
                "hard_stop_conflict_contract",
                dict(HIGH_AI_HARD_STOP_CONFLICT_CONTRACT),
            ),
            "ai_score_at_exit": candidate.get(
                "ai_score_at_exit", candidate.get("current_ai_score", 0.0)
            ),
            "ai_score_raw_at_exit": candidate.get(
                "ai_score_raw_at_exit", candidate.get("ai_score_raw", 0.0)
            ),
            "ai_action_at_exit": candidate.get(
                "ai_action_at_exit", candidate.get("ai_action", "-")
            ),
            "ai_result_source_at_exit": candidate.get(
                "ai_result_source_at_exit",
                candidate.get("ai_result_source", "-"),
            ),
            "ai_model_at_exit": candidate.get(
                "ai_model_at_exit", candidate.get("ai_model", "-")
            ),
            "ai_model_tier_at_exit": candidate.get(
                "ai_model_tier_at_exit", candidate.get("ai_model_tier", "-")
            ),
            "ai_transport_mode_at_exit": candidate.get(
                "ai_transport_mode_at_exit",
                candidate.get("ai_transport_mode", "-"),
            ),
            **{
                key: candidate.get(key)
                for key in ENTRY_SPLIT_POST_SELL_KEYS
                if candidate.get(key) is not None
            },
            "soft_stop_threshold_pct": candidate.get("soft_stop_threshold_pct", 0.0),
            "same_symbol_soft_stop_cooldown_would_block": bool(
                candidate.get("same_symbol_soft_stop_cooldown_would_block", False)
            ),
            "outcome": outcome,
            "minute_candle_source_meta": candle_meta,
            **source_quality,
            **{
                f"metrics_{horizon}m": metrics
                for horizon, metrics in metrics_by_horizon.items()
            },
        }
        new_evaluations.append(evaluation)

    if new_evaluations:
        with _WRITE_LOCK:
            path = _evaluation_path(target_date)
            for item in new_evaluations:
                _append_jsonl(path, item)

    all_evaluations = _dedupe_latest_evaluations(existing_evaluations + new_evaluations)
    summary.evaluated_candidates = len(all_evaluations)

    outcome_counts: dict[str, int] = {"MISSED_UPSIDE": 0, "GOOD_EXIT": 0, "NEUTRAL": 0}
    for item in all_evaluations:
        outcome = str(item.get("outcome", "NEUTRAL") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts
    summary.minute_candle_source_quality_counts = dict(
        Counter(
            str(item.get("minute_candle_source_quality") or "unknown")
            for item in all_evaluations
        )
    )

    summary.missed_upside_cases = sorted(
        [
            item
            for item in all_evaluations
            if str(item.get("outcome", "")).upper() == "MISSED_UPSIDE"
        ],
        key=lambda item: float(
            (item.get("metrics_10m", {}) or {}).get("mfe_pct", 0.0) or 0.0
        ),
        reverse=True,
    )[:5]
    summary.good_exit_cases = sorted(
        [
            item
            for item in all_evaluations
            if str(item.get("outcome", "")).upper() == "GOOD_EXIT"
        ],
        key=lambda item: float(
            (item.get("metrics_10m", {}) or {}).get("mae_pct", 0.0) or 0.0
        ),
    )[:5]
    return summary


def evaluate_sim_post_sell_candidates(
    target_date: str, token: str | None = None
) -> PostSellFeedbackSummary:
    try:
        from src.utils import kiwoom_utils
    except Exception as exc:
        log_error(f"[SIM_POST_SELL_EVAL] kiwoom_utils import failed: {exc}")
        kiwoom_utils = None

    candidates = _load_jsonl(_sim_candidate_path(target_date))
    existing_evaluations = _load_jsonl(_sim_evaluation_path(target_date))
    evaluated_ids = {
        str(item.get("post_sell_id", ""))
        for item in existing_evaluations
        if _evaluation_has_current_horizons(item)
    }
    summary = PostSellFeedbackSummary(date=target_date)
    summary.total_candidates = len(candidates)

    if not bool(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_EVAL_ENABLED", True)):
        summary.evaluated_candidates = len(existing_evaluations)
        return summary

    candle_cache: dict[str, tuple[list[dict], dict]] = {}
    new_evaluations: list[dict] = []
    token_fetch_attempted = token is not None

    for candidate in candidates:
        post_sell_id = str(candidate.get("post_sell_id", "") or "")
        code = str(candidate.get("stock_code", "") or "")
        if (
            not post_sell_id
            or not code
            or post_sell_id in evaluated_ids
            or kiwoom_utils is None
        ):
            continue

        if token is None and not token_fetch_attempted:
            token_fetch_attempted = True
            try:
                token = kiwoom_utils.get_kiwoom_token()
            except Exception as exc:
                log_error(f"[SIM_POST_SELL_EVAL] token fetch failed: {exc}")
                token = None

        if token is None:
            continue

        if code not in candle_cache:
            try:
                candle_cache[code] = _fetch_minute_candles_with_meta(
                    kiwoom_utils, token, code, limit=700
                )
            except Exception as exc:
                log_error(
                    f"[SIM_POST_SELL_EVAL] {code} minute candles fetch failed: {exc}"
                )
                candle_cache[code] = ([], _minute_candle_meta([], requested_limit=700))

        candles, candle_meta = candle_cache.get(
            code, ([], _minute_candle_meta([], requested_limit=700))
        )
        metrics_by_horizon = {
            horizon: _compute_window_metrics(candidate, candles, horizon)
            for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
        }
        metrics_10m = metrics_by_horizon[10]
        outcome = _classify_candidate(metrics_10m)
        source_quality = _minute_forward_source_quality(metrics_by_horizon, candle_meta)

        evaluation = {
            "schema_version": POST_SELL_REPORT_SCHEMA_VERSION,
            "report_type": "sim_post_sell_evaluation",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "metric_role": "sim_post_sell_mfe_mae_observation",
            "decision_authority": "sim_equal_weight_observation_only",
            "window_policy": "same_day_post_sell_forward_window",
            "sample_floor": "report_only_no_hard_decision",
            "primary_decision_metric": "sim_post_decision_mfe_10m_pct",
            "source_quality_gate": "scalp_sim_sell_order_assumed_filled + numeric profit_rate",
            "forbidden_uses": list(SIM_POST_SELL_FORBIDDEN_USES),
            "post_sell_id": post_sell_id,
            "evaluated_at": datetime.now().isoformat(),
            "signal_date": target_date,
            "stock_code": code,
            "stock_name": candidate.get("stock_name", ""),
            "strategy": candidate.get("strategy", ""),
            "position_tag": candidate.get("position_tag", ""),
            "sell_time": candidate.get("sell_time", ""),
            "sell_bucket": candidate.get("sell_bucket", ""),
            "buy_price": candidate.get("buy_price", 0),
            "sell_price": candidate.get("sell_price", 0),
            "profit_rate": candidate.get("profit_rate", 0.0),
            "buy_qty": candidate.get("buy_qty", 0),
            "exit_rule": candidate.get("exit_rule", "-"),
            "sell_reason_type": candidate.get("sell_reason_type", "-"),
            "trigger_profit_rate": candidate.get("trigger_profit_rate", 0.0),
            "current_ai_score": candidate.get("current_ai_score", 0.0),
            "ai_score_raw": candidate.get("ai_score_raw", 0.0),
            "ai_action": candidate.get("ai_action", "-"),
            "ai_result_source": candidate.get("ai_result_source", "-"),
            "ai_model": candidate.get("ai_model", "-"),
            "ai_model_tier": candidate.get("ai_model_tier", "-"),
            "ai_transport_mode": candidate.get("ai_transport_mode", "-"),
            "high_ai_hard_stop_conflict": _safe_bool(
                candidate.get("high_ai_hard_stop_conflict", False)
            ),
            "hard_stop_conflict_dimension": candidate.get(
                "hard_stop_conflict_dimension", "not_hard_stop"
            ),
            "hard_stop_conflict_score_floor": candidate.get(
                "hard_stop_conflict_score_floor",
                HIGH_AI_HARD_STOP_SCORE_FLOOR,
            ),
            "hard_stop_conflict_ai_score_band": candidate.get(
                "hard_stop_conflict_ai_score_band",
                "ai_score_missing",
            ),
            "hard_stop_conflict_runtime_effect": False,
            "hard_stop_conflict_allowed_runtime_apply": False,
            "hard_stop_conflict_hard_gate": False,
            "hard_stop_conflict_contract": candidate.get(
                "hard_stop_conflict_contract",
                dict(HIGH_AI_HARD_STOP_CONFLICT_CONTRACT),
            ),
            "ai_score_at_exit": candidate.get(
                "ai_score_at_exit", candidate.get("current_ai_score", 0.0)
            ),
            "ai_score_raw_at_exit": candidate.get(
                "ai_score_raw_at_exit", candidate.get("ai_score_raw", 0.0)
            ),
            "ai_action_at_exit": candidate.get(
                "ai_action_at_exit", candidate.get("ai_action", "-")
            ),
            "ai_result_source_at_exit": candidate.get(
                "ai_result_source_at_exit",
                candidate.get("ai_result_source", "-"),
            ),
            "ai_model_at_exit": candidate.get(
                "ai_model_at_exit", candidate.get("ai_model", "-")
            ),
            "ai_model_tier_at_exit": candidate.get(
                "ai_model_tier_at_exit", candidate.get("ai_model_tier", "-")
            ),
            "ai_transport_mode_at_exit": candidate.get(
                "ai_transport_mode_at_exit",
                candidate.get("ai_transport_mode", "-"),
            ),
            "outcome": outcome,
            "candidate_source": "scalp_simulator",
            "simulation_book": "scalp_ai_buy_all",
            "candidate_id": candidate.get("candidate_id", ""),
            "entry_adm_candidate_id": candidate.get("entry_adm_candidate_id", ""),
            "entry_event_emitted_at": candidate.get("entry_event_emitted_at", ""),
            "entry_signal_time": candidate.get("entry_signal_time", ""),
            "entry_time_source": candidate.get("entry_time_source", ""),
            "entry_record_id": candidate.get("entry_record_id", ""),
            "entry_join_key": candidate.get("entry_join_key", ""),
            "entry_join_status": candidate.get("entry_join_status", ""),
            "sim_record_id": candidate.get("sim_record_id", ""),
            "sim_parent_record_id": candidate.get("sim_parent_record_id", ""),
            "source_event_stage": candidate.get("source_event_stage", ""),
            "minute_candle_source_meta": candle_meta,
            **source_quality,
            **{
                f"metrics_{horizon}m": metrics
                for horizon, metrics in metrics_by_horizon.items()
            },
        }
        new_evaluations.append(evaluation)

    if new_evaluations:
        with _WRITE_LOCK:
            path = _sim_evaluation_path(target_date)
            for item in new_evaluations:
                _append_jsonl(path, item)

    all_evaluations = _dedupe_latest_evaluations(existing_evaluations + new_evaluations)
    summary.evaluated_candidates = len(all_evaluations)

    outcome_counts: dict[str, int] = {"MISSED_UPSIDE": 0, "GOOD_EXIT": 0, "NEUTRAL": 0}
    for item in all_evaluations:
        outcome = str(item.get("outcome", "NEUTRAL") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts
    summary.minute_candle_source_quality_counts = dict(
        Counter(
            str(item.get("minute_candle_source_quality") or "unknown")
            for item in all_evaluations
        )
    )
    summary.missed_upside_cases = sorted(
        [
            item
            for item in all_evaluations
            if str(item.get("outcome", "")).upper() == "MISSED_UPSIDE"
        ],
        key=lambda item: float(
            (item.get("metrics_10m", {}) or {}).get("mfe_pct", 0.0) or 0.0
        ),
        reverse=True,
    )[:5]
    summary.good_exit_cases = sorted(
        [
            item
            for item in all_evaluations
            if str(item.get("outcome", "")).upper() == "GOOD_EXIT"
        ],
        key=lambda item: float(
            (item.get("metrics_10m", {}) or {}).get("mae_pct", 0.0) or 0.0
        ),
    )[:5]
    return summary


def backfill_sim_post_sell_candidates_from_threshold_events(target_date: str) -> dict:
    path = DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"
    rows = _load_jsonl(path)
    existing_candidates = _load_jsonl(_sim_candidate_path(target_date))
    existing_keys = {
        (
            str(item.get("stock_code") or "").strip()[:6],
            str(
                item.get("sim_record_id") or item.get("sim_parent_record_id") or ""
            ).strip()
            or f"{item.get('sell_bucket')}:{item.get('sell_price')}",
        )
        for item in existing_candidates
        if isinstance(item, dict)
    }
    seen = 0
    created = 0
    for event in rows:
        if str(event.get("stage") or "") != "scalp_sim_sell_order_assumed_filled":
            continue
        seen += 1
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        norm_code = str(event.get("stock_code") or "").strip()[:6]
        sim_marker = str(
            fields.get("sim_record_id")
            or event.get("record_id")
            or fields.get("sim_parent_record_id")
            or ""
        ).strip()
        if not sim_marker:
            sell_dt = (
                _parse_datetime(event.get("emitted_at"), default=datetime.now())
                or datetime.now()
            )
            sim_marker = f"{_minute_bucket(sell_dt)}:{fields.get('assumed_fill_price')}"
        existing_key = (norm_code, sim_marker)
        if existing_key in existing_keys:
            continue
        candidate = record_sim_post_sell_candidate(
            candidate_id=fields.get("entry_adm_candidate_id")
            or fields.get("candidate_id"),
            sim_record_id=fields.get("sim_record_id") or event.get("record_id"),
            sim_parent_record_id=fields.get("sim_parent_record_id"),
            stock={
                "name": event.get("stock_name") or "",
                "code": event.get("stock_code") or "",
                "strategy": "SCALPING",
                "position_tag": fields.get("position_tag") or "",
            },
            code=event.get("stock_code"),
            sell_time=event.get("emitted_at"),
            buy_price=fields.get("buy_price"),
            sell_price=fields.get("assumed_fill_price"),
            profit_rate=fields.get("profit_rate"),
            buy_qty=fields.get("qty"),
            exit_rule=fields.get("exit_rule"),
            sell_reason_type=fields.get("sell_reason_type"),
            trigger_profit_rate=fields.get("trigger_profit_rate"),
            current_ai_score=fields.get("current_ai_score")
            or fields.get("ai_score_smoothed"),
            ai_score_raw=fields.get("ai_score_raw"),
            ai_action=fields.get("ai_action"),
            ai_result_source=fields.get("ai_result_source"),
            ai_model=fields.get("ai_model"),
            ai_model_tier=fields.get("ai_model_tier"),
            ai_transport_mode=fields.get("ai_transport_mode")
            or fields.get("openai_transport_mode"),
        )
        if candidate:
            created += 1
            existing_keys.add(existing_key)
    return {
        "date": target_date,
        "source_path": str(path),
        "events_seen": seen,
        "candidates_created": created,
        "candidate_path": str(_sim_candidate_path(target_date)),
        "runtime_effect": False,
    }


def post_sell_feedback_summary_to_dict(summary: PostSellFeedbackSummary) -> dict:
    return {
        "date": summary.date,
        "total_candidates": int(summary.total_candidates),
        "evaluated_candidates": int(summary.evaluated_candidates),
        "outcome_counts": dict(summary.outcome_counts or {}),
        "minute_candle_source_quality_counts": dict(
            summary.minute_candle_source_quality_counts or {}
        ),
        "missed_upside_cases": list(summary.missed_upside_cases or []),
        "good_exit_cases": list(summary.good_exit_cases or []),
    }


def format_post_sell_feedback_summary(summary: PostSellFeedbackSummary) -> str:
    if summary.total_candidates <= 0:
        return f"📉 post-sell 피드백 ({summary.date})\n- 후보 기록 없음"

    lines = [
        f"📉 post-sell 피드백 ({summary.date})",
        f"- 매도 후보 기록: {summary.total_candidates}건",
        f"- 평가 완료: {summary.evaluated_candidates}건",
        f"- 결과 분포: MISSED_UPSIDE {summary.outcome_counts.get('MISSED_UPSIDE', 0)} / "
        f"GOOD_EXIT {summary.outcome_counts.get('GOOD_EXIT', 0)} / "
        f"NEUTRAL {summary.outcome_counts.get('NEUTRAL', 0)}",
    ]

    if summary.missed_upside_cases:
        lines.append("- 상위 missed upside:")
        for item in summary.missed_upside_cases[:3]:
            metrics = item.get("metrics_10m", {}) or {}
            lines.append(
                f"  {item.get('stock_name')}({item.get('stock_code')}) "
                f"MFE10m {float(metrics.get('mfe_pct', 0.0) or 0.0):+.2f}% / "
                f"Close10m {float(metrics.get('close_ret_pct', 0.0) or 0.0):+.2f}% "
                f"(exit_rule={item.get('exit_rule', '-')})"
            )
    return "\n".join(lines)


def _build_summary_from_raw_rows(
    *,
    target_date: str,
    candidates: list[dict],
    evaluations: list[dict],
) -> PostSellFeedbackSummary:
    evaluations = _dedupe_latest_evaluations(evaluations)
    summary = PostSellFeedbackSummary(date=target_date)
    summary.total_candidates = len(candidates)
    summary.evaluated_candidates = len(evaluations)

    outcome_counts: dict[str, int] = {"MISSED_UPSIDE": 0, "GOOD_EXIT": 0, "NEUTRAL": 0}
    for item in evaluations:
        outcome = str(item.get("outcome", "NEUTRAL") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts

    summary.missed_upside_cases = sorted(
        [
            item
            for item in evaluations
            if str(item.get("outcome", "")).upper() == "MISSED_UPSIDE"
        ],
        key=lambda item: float(
            (item.get("metrics_10m", {}) or {}).get("mfe_pct", 0.0) or 0.0
        ),
        reverse=True,
    )[:5]
    summary.good_exit_cases = sorted(
        [
            item
            for item in evaluations
            if str(item.get("outcome", "")).upper() == "GOOD_EXIT"
        ],
        key=lambda item: float(
            (item.get("metrics_10m", {}) or {}).get("mae_pct", 0.0) or 0.0
        ),
    )[:5]
    return summary


def _enrich_post_sell_rows(
    *,
    candidates: list[dict],
    evaluations: list[dict],
) -> list[dict]:
    candidate_by_id = {
        str(item.get("post_sell_id", "") or ""): dict(item)
        for item in (candidates or [])
        if item.get("post_sell_id")
    }
    rows: list[dict] = []
    for item in evaluations:
        post_sell_id = str(item.get("post_sell_id", "") or "")
        candidate = candidate_by_id.get(post_sell_id, {})
        metrics_by_horizon = {
            horizon: dict(item.get(f"metrics_{horizon}m") or {})
            for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
        }
        metrics_10m = metrics_by_horizon[10]
        mfe_10m = _safe_float(metrics_10m.get("mfe_pct"), 0.0)
        mae_10m = _safe_float(metrics_10m.get("mae_pct"), 0.0)
        close_10m = _safe_float(metrics_10m.get("close_ret_pct"), 0.0)
        profit_rate = _safe_float(
            item.get("profit_rate", candidate.get("profit_rate")), 0.0
        )
        exit_rule = str(item.get("exit_rule") or candidate.get("exit_rule") or "-")
        sell_price = _safe_float(
            item.get("sell_price", candidate.get("sell_price")), 0.0
        )
        buy_price = _safe_float(item.get("buy_price", candidate.get("buy_price")), 0.0)
        buy_qty = _safe_int(item.get("buy_qty", candidate.get("buy_qty")), 0)
        peak_profit = _safe_float(
            item.get("peak_profit", candidate.get("peak_profit")), 0.0
        )
        held_sec = _safe_int(item.get("held_sec", candidate.get("held_sec")), 0)
        current_ai_score = _safe_float(
            item.get("current_ai_score", candidate.get("current_ai_score")), 0.0
        )
        conflict_fields = _build_high_ai_hard_stop_conflict_fields(
            exit_rule=item.get("exit_rule", candidate.get("exit_rule", "-")),
            current_ai_score=current_ai_score,
            ai_score_raw=item.get(
                "ai_score_raw_at_exit",
                item.get("ai_score_raw", candidate.get("ai_score_raw")),
            ),
            ai_action=item.get(
                "ai_action_at_exit", item.get("ai_action", candidate.get("ai_action"))
            ),
            ai_result_source=item.get(
                "ai_result_source_at_exit",
                item.get("ai_result_source", candidate.get("ai_result_source")),
            ),
            ai_model=item.get(
                "ai_model_at_exit", item.get("ai_model", candidate.get("ai_model"))
            ),
            ai_model_tier=item.get(
                "ai_model_tier_at_exit",
                item.get("ai_model_tier", candidate.get("ai_model_tier")),
            ),
            ai_transport_mode=item.get(
                "ai_transport_mode_at_exit",
                item.get("ai_transport_mode", candidate.get("ai_transport_mode")),
            ),
        )
        soft_stop_threshold_pct = _safe_float(
            item.get(
                "soft_stop_threshold_pct", candidate.get("soft_stop_threshold_pct")
            ),
            0.0,
        )
        soft_stop_overshoot_pct = (
            round(max(0.0, soft_stop_threshold_pct - profit_rate), 3)
            if soft_stop_threshold_pct < 0.0
            else 0.0
        )
        metrics_1m = metrics_by_horizon[1]
        metrics_3m = metrics_by_horizon[3]
        metrics_5m = metrics_by_horizon[5]
        extra_upside_pct = max(0.0, mfe_10m)
        extra_upside_krw_est = (
            int(round(sell_price * buy_qty * (extra_upside_pct / 100.0)))
            if sell_price > 0 and buy_qty > 0
            else 0
        )
        potential_peak_profit_rate = round(profit_rate + extra_upside_pct, 3)
        capture_efficiency_pct = (
            round(
                _clamp((profit_rate / potential_peak_profit_rate) * 100.0, 0.0, 100.0),
                1,
            )
            if potential_peak_profit_rate > 0
            else 0.0
        )
        row = {
            "post_sell_id": post_sell_id,
            "signal_date": str(
                item.get("signal_date") or candidate.get("signal_date") or ""
            ),
            "stock_code": str(
                item.get("stock_code") or candidate.get("stock_code") or ""
            ),
            "stock_name": str(
                item.get("stock_name") or candidate.get("stock_name") or ""
            ),
            "recommendation_id": _safe_int(
                item.get("recommendation_id", candidate.get("recommendation_id")), 0
            ),
            "strategy": str(item.get("strategy") or candidate.get("strategy") or ""),
            "position_tag": str(
                item.get("position_tag") or candidate.get("position_tag") or ""
            ),
            "sell_time": str(item.get("sell_time") or candidate.get("sell_time") or ""),
            "sell_bucket": str(
                item.get("sell_bucket") or candidate.get("sell_bucket") or ""
            ),
            "buy_price": int(round(buy_price)),
            "sell_price": int(round(sell_price)),
            "buy_qty": int(buy_qty),
            "profit_rate": round(profit_rate, 3),
            "realized_result_label": str(
                item.get("realized_result_label")
                or candidate.get("realized_result_label")
                or _realized_result_label(profit_rate)
            ),
            "exit_rule_profit_mismatch": bool(
                item.get(
                    "exit_rule_profit_mismatch",
                    candidate.get(
                        "exit_rule_profit_mismatch",
                        _exit_rule_profit_mismatch(exit_rule, profit_rate),
                    ),
                )
            ),
            "peak_profit": round(peak_profit, 3),
            "held_sec": int(held_sec),
            "current_ai_score": round(current_ai_score, 1),
            **conflict_fields,
            "exit_rule": exit_rule,
            "revive": bool(item.get("revive", candidate.get("revive", False))),
            "outcome": str(item.get("outcome") or "NEUTRAL").upper(),
            "soft_stop_threshold_pct": round(soft_stop_threshold_pct, 3),
            "soft_stop_overshoot_pct": float(soft_stop_overshoot_pct),
            "same_symbol_soft_stop_cooldown_would_block": bool(
                item.get(
                    "same_symbol_soft_stop_cooldown_would_block",
                    candidate.get("same_symbol_soft_stop_cooldown_would_block", False),
                )
            ),
            "mfe_10m_pct": round(mfe_10m, 3),
            "mae_10m_pct": round(mae_10m, 3),
            "close_10m_pct": round(close_10m, 3),
            "extra_upside_10m_pct": round(extra_upside_pct, 3),
            "extra_upside_10m_krw_est": int(extra_upside_krw_est),
            "potential_peak_profit_rate_10m": float(potential_peak_profit_rate),
            "capture_efficiency_pct": float(capture_efficiency_pct),
            "rebound_above_sell_1m": bool(metrics_1m.get("rebound_above_sell", False)),
            "rebound_above_sell_3m": bool(metrics_3m.get("rebound_above_sell", False)),
            "rebound_above_sell_5m": bool(metrics_5m.get("rebound_above_sell", False)),
            "rebound_above_sell_10m": bool(
                metrics_10m.get("rebound_above_sell", False)
            ),
            "rebound_above_buy_1m": bool(metrics_1m.get("rebound_above_buy", False)),
            "rebound_above_buy_3m": bool(metrics_3m.get("rebound_above_buy", False)),
            "rebound_above_buy_5m": bool(metrics_5m.get("rebound_above_buy", False)),
            "rebound_above_buy_10m": bool(metrics_10m.get("rebound_above_buy", False)),
        }
        for horizon, metrics in metrics_by_horizon.items():
            row[f"metrics_{horizon}m"] = metrics
            if horizon in POST_SELL_LONG_HORIZONS_MIN:
                mfe_pct = _safe_float(metrics.get("mfe_pct"), 0.0)
                mae_pct = _safe_float(metrics.get("mae_pct"), 0.0)
                close_pct = _safe_float(metrics.get("close_ret_pct"), 0.0)
                long_extra = max(0.0, mfe_pct)
                row[f"mfe_{horizon}m_pct"] = round(mfe_pct, 3)
                row[f"mae_{horizon}m_pct"] = round(mae_pct, 3)
                row[f"close_{horizon}m_pct"] = round(close_pct, 3)
                row[f"extra_upside_{horizon}m_pct"] = round(long_extra, 3)
                row[f"extra_upside_{horizon}m_krw_est"] = (
                    int(round(sell_price * buy_qty * (long_extra / 100.0)))
                    if sell_price > 0 and buy_qty > 0
                    else 0
                )
                row[f"potential_peak_profit_rate_{horizon}m"] = round(
                    profit_rate + long_extra, 3
                )
                row[f"rebound_above_sell_{horizon}m"] = bool(
                    metrics.get("rebound_above_sell", False)
                )
                row[f"rebound_above_buy_{horizon}m"] = bool(
                    metrics.get("rebound_above_buy", False)
                )
        rows.append(row)
    return rows


def _bucket_held_sec(held_sec: int) -> str:
    value = max(0, int(held_sec or 0))
    if value < 90:
        return "<90s"
    if value < 180:
        return "90-179s"
    if value < 300:
        return "180-299s"
    return "300s+"


def _bucket_peak_profit(peak_profit: float) -> str:
    value = float(peak_profit or 0.0)
    if value <= 0.2:
        return "<=0.2%"
    if value <= 0.5:
        return "0.21~0.5%"
    if value <= 1.0:
        return "0.51~1.0%"
    return ">1.0%"


def _build_soft_stop_forensics(rows: list[dict]) -> dict:
    soft_stop_rows = [
        row for row in rows if str(row.get("exit_rule") or "") == "scalp_soft_stop_pct"
    ]
    if not soft_stop_rows:
        return {
            "total_soft_stop": 0,
            "rebound_above_sell_rate": {
                f"{horizon}m": 0.0 for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
            },
            "rebound_above_buy_rate": {
                f"{horizon}m": 0.0 for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
            },
            "median_overshoot_pct": 0.0,
            "p95_overshoot_pct": 0.0,
            "cooldown_would_block_rate": 0.0,
            "tag_buckets": [],
            "held_sec_buckets": [],
            "peak_profit_buckets": [],
            "top_rebound_cases": [],
        }

    def _rate(key: str) -> float:
        return _ratio(
            sum(1 for row in soft_stop_rows if bool(row.get(key))), len(soft_stop_rows)
        )

    overshoot_values = [
        _safe_float(row.get("soft_stop_overshoot_pct"), 0.0)
        for row in soft_stop_rows
        if _safe_float(row.get("soft_stop_threshold_pct"), 0.0) < 0.0
    ]

    def _bucket_rows(group_key_fn) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in soft_stop_rows:
            grouped[group_key_fn(row)].append(row)
        result: list[dict] = []
        for bucket, items in grouped.items():
            bucket_row = {
                "bucket": bucket,
                "trades": len(items),
                "avg_profit_rate": _avg(
                    [_safe_float(item.get("profit_rate"), 0.0) for item in items]
                ),
                "avg_peak_profit": _avg(
                    [_safe_float(item.get("peak_profit"), 0.0) for item in items]
                ),
                "median_overshoot_pct": _median(
                    [
                        _safe_float(item.get("soft_stop_overshoot_pct"), 0.0)
                        for item in items
                    ]
                ),
                "cooldown_would_block_rate": _ratio(
                    sum(
                        1
                        for item in items
                        if bool(item.get("same_symbol_soft_stop_cooldown_would_block"))
                    ),
                    len(items),
                ),
            }
            for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN:
                bucket_row[f"rebound_above_sell_{horizon}m_rate"] = _ratio(
                    sum(
                        1
                        for item in items
                        if bool(item.get(f"rebound_above_sell_{horizon}m"))
                    ),
                    len(items),
                )
                bucket_row[f"rebound_above_buy_{horizon}m_rate"] = _ratio(
                    sum(
                        1
                        for item in items
                        if bool(item.get(f"rebound_above_buy_{horizon}m"))
                    ),
                    len(items),
                )
            result.append(bucket_row)
        return sorted(
            result,
            key=lambda item: (
                int(item.get("trades", 0) or 0),
                str(item.get("bucket") or ""),
            ),
            reverse=True,
        )

    top_rebound_cases = sorted(
        soft_stop_rows,
        key=lambda row: (
            bool(row.get("rebound_above_buy_10m")),
            bool(row.get("rebound_above_buy_30m")),
            bool(row.get("rebound_above_buy_60m")),
            _safe_float((row.get("metrics_10m") or {}).get("mfe_vs_buy_pct"), 0.0),
            _safe_float((row.get("metrics_60m") or {}).get("mfe_vs_buy_pct"), 0.0),
            _safe_float(row.get("soft_stop_overshoot_pct"), 0.0),
        ),
        reverse=True,
    )[:5]

    return {
        "total_soft_stop": len(soft_stop_rows),
        "rebound_above_sell_rate": {
            f"{horizon}m": _rate(f"rebound_above_sell_{horizon}m")
            for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
        },
        "rebound_above_buy_rate": {
            f"{horizon}m": _rate(f"rebound_above_buy_{horizon}m")
            for horizon in POST_SELL_FEEDBACK_HORIZONS_MIN
        },
        "median_overshoot_pct": _median(overshoot_values),
        "p95_overshoot_pct": _percentile(overshoot_values, 95.0),
        "cooldown_would_block_rate": _ratio(
            sum(
                1
                for row in soft_stop_rows
                if bool(row.get("same_symbol_soft_stop_cooldown_would_block"))
            ),
            len(soft_stop_rows),
        ),
        "tag_buckets": _bucket_rows(
            lambda row: f"{str(row.get('strategy') or '-')}/{str(row.get('position_tag') or '-')}"
        ),
        "held_sec_buckets": _bucket_rows(
            lambda row: _bucket_held_sec(_safe_int(row.get("held_sec"), 0))
        ),
        "peak_profit_buckets": _bucket_rows(
            lambda row: _bucket_peak_profit(_safe_float(row.get("peak_profit"), 0.0))
        ),
        "top_rebound_cases": [
            {
                **_case_view(row),
                "held_sec": int(_safe_int(row.get("held_sec"), 0)),
                "peak_profit": round(_safe_float(row.get("peak_profit"), 0.0), 3),
                "soft_stop_threshold_pct": round(
                    _safe_float(row.get("soft_stop_threshold_pct"), 0.0), 3
                ),
                "soft_stop_overshoot_pct": round(
                    _safe_float(row.get("soft_stop_overshoot_pct"), 0.0), 3
                ),
                "rebound_above_buy_10m": bool(row.get("rebound_above_buy_10m")),
                "rebound_above_sell_10m": bool(row.get("rebound_above_sell_10m")),
                "mfe_vs_buy_10m_pct": round(
                    _safe_float(
                        (row.get("metrics_10m") or {}).get("mfe_vs_buy_pct"), 0.0
                    ),
                    3,
                ),
                "rebound_above_buy_20m": bool(row.get("rebound_above_buy_20m")),
                "rebound_above_sell_20m": bool(row.get("rebound_above_sell_20m")),
                "mfe_vs_buy_20m_pct": round(
                    _safe_float(
                        (row.get("metrics_20m") or {}).get("mfe_vs_buy_pct"), 0.0
                    ),
                    3,
                ),
                "rebound_above_buy_30m": bool(row.get("rebound_above_buy_30m")),
                "rebound_above_sell_30m": bool(row.get("rebound_above_sell_30m")),
                "mfe_vs_buy_30m_pct": round(
                    _safe_float(
                        (row.get("metrics_30m") or {}).get("mfe_vs_buy_pct"), 0.0
                    ),
                    3,
                ),
                "rebound_above_buy_60m": bool(row.get("rebound_above_buy_60m")),
                "rebound_above_sell_60m": bool(row.get("rebound_above_sell_60m")),
                "mfe_vs_buy_60m_pct": round(
                    _safe_float(
                        (row.get("metrics_60m") or {}).get("mfe_vs_buy_pct"), 0.0
                    ),
                    3,
                ),
                "same_symbol_soft_stop_cooldown_would_block": bool(
                    row.get("same_symbol_soft_stop_cooldown_would_block")
                ),
            }
            for row in top_rebound_cases
        ],
    }


def _build_exit_rule_tuning_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("exit_rule") or "-")].append(row)

    result: list[dict] = []
    for exit_rule, items in grouped.items():
        trades = len(items)
        missed_count = sum(
            1 for item in items if str(item.get("outcome") or "") == "MISSED_UPSIDE"
        )
        good_count = sum(
            1 for item in items if str(item.get("outcome") or "") == "GOOD_EXIT"
        )
        avg_profit = _avg([_safe_float(item.get("profit_rate"), 0.0) for item in items])
        avg_mfe = _avg([_safe_float(item.get("mfe_10m_pct"), 0.0) for item in items])
        avg_mae = _avg([_safe_float(item.get("mae_10m_pct"), 0.0) for item in items])
        avg_close = _avg(
            [_safe_float(item.get("close_10m_pct"), 0.0) for item in items]
        )
        avg_capture = _avg(
            [
                _safe_float(item.get("capture_efficiency_pct"), 0.0)
                for item in items
                if _safe_float(item.get("potential_peak_profit_rate_10m"), 0.0) > 0.0
            ]
        )
        est_extra_krw = int(
            sum(_safe_int(item.get("extra_upside_10m_krw_est"), 0) for item in items)
        )
        missed_rate = _ratio(missed_count, trades)
        good_rate = _ratio(good_count, trades)
        follow_up_rate = _ratio(
            sum(
                1
                for item in items
                if _safe_float(item.get("close_10m_pct"), 0.0) >= 0.2
            ),
            trades,
        )
        tuning_score = _clamp(
            (missed_rate * 0.60)
            + _clamp(max(avg_close, 0.0) * 40.0, 0.0, 25.0)
            + _clamp(max(avg_mfe, 0.0) * 12.0, 0.0, 15.0)
            - _clamp(good_rate * 0.20, 0.0, 15.0),
            0.0,
            100.0,
        )
        if trades < 2:
            tuning_hint = "표본 부족: 2건 이상 누적 후 미세조정 권장"
        elif tuning_score >= 65.0:
            tuning_hint = "우선 점검: 익절 지연/분할청산 shadow 테스트 후보"
        elif good_rate >= 45.0 and avg_mae <= -0.5:
            tuning_hint = "손실 회피 기여가 확인됨: 과도 완화 주의"
        elif avg_mfe >= 1.0 and avg_close < 0.1:
            tuning_hint = "고점 회수보다 트레일링/재진입 규칙 보정이 유리"
        else:
            tuning_hint = "현행 유지 + 표본 추가 관찰"

        result.append(
            {
                "exit_rule": exit_rule,
                "trades": trades,
                "missed_upside_count": missed_count,
                "good_exit_count": good_count,
                "missed_upside_rate": missed_rate,
                "good_exit_rate": good_rate,
                "follow_up_10m_rate": follow_up_rate,
                "avg_profit_rate": avg_profit,
                "avg_mfe_10m_pct": avg_mfe,
                "avg_mae_10m_pct": avg_mae,
                "avg_close_10m_pct": avg_close,
                "avg_capture_efficiency_pct": avg_capture,
                "estimated_extra_upside_10m_krw": est_extra_krw,
                "tuning_pressure_score": round(tuning_score, 1),
                "tuning_hint": tuning_hint,
            }
        )

    return sorted(
        result,
        key=lambda item: (
            float(item.get("tuning_pressure_score", 0.0) or 0.0),
            int(item.get("trades", 0) or 0),
            int(item.get("estimated_extra_upside_10m_krw", 0) or 0),
        ),
        reverse=True,
    )


def _build_tag_tuning_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        strategy = str(row.get("strategy") or "-")
        position_tag = str(row.get("position_tag") or "-")
        grouped[(strategy, position_tag)].append(row)

    result: list[dict] = []
    for (strategy, position_tag), items in grouped.items():
        trades = len(items)
        missed_count = sum(
            1 for item in items if str(item.get("outcome") or "") == "MISSED_UPSIDE"
        )
        good_count = sum(
            1 for item in items if str(item.get("outcome") or "") == "GOOD_EXIT"
        )
        avg_profit = _avg([_safe_float(item.get("profit_rate"), 0.0) for item in items])
        avg_close = _avg(
            [_safe_float(item.get("close_10m_pct"), 0.0) for item in items]
        )
        avg_mfe = _avg([_safe_float(item.get("mfe_10m_pct"), 0.0) for item in items])
        result.append(
            {
                "strategy": strategy,
                "position_tag": position_tag,
                "trades": trades,
                "missed_upside_rate": _ratio(missed_count, trades),
                "good_exit_rate": _ratio(good_count, trades),
                "avg_profit_rate": avg_profit,
                "avg_close_10m_pct": avg_close,
                "avg_mfe_10m_pct": avg_mfe,
                "estimated_extra_upside_10m_krw": int(
                    sum(
                        _safe_int(item.get("extra_upside_10m_krw_est"), 0)
                        for item in items
                    )
                ),
            }
        )
    return sorted(
        result,
        key=lambda item: (
            float(item.get("missed_upside_rate", 0.0) or 0.0),
            float(item.get("avg_close_10m_pct", 0.0) or 0.0),
            int(item.get("trades", 0) or 0),
        ),
        reverse=True,
    )


def _build_high_ai_hard_stop_forensics(rows: list[dict]) -> dict:
    hard_stop_rows = [
        row
        for row in rows
        if str(row.get("exit_rule") or "") in HIGH_AI_HARD_STOP_EXIT_RULES
    ]
    conflict_rows = [
        row
        for row in hard_stop_rows
        if _safe_bool(row.get("high_ai_hard_stop_conflict"))
    ]
    outcome_counter = Counter(
        str(row.get("outcome") or "NEUTRAL").upper() for row in conflict_rows
    )
    source_counter = Counter(
        str(row.get("ai_result_source_at_exit") or "-") for row in conflict_rows
    )
    model_counter = Counter(
        str(row.get("ai_model_at_exit") or "-") for row in conflict_rows
    )
    return {
        "dimension_name": "high_ai_hard_stop_conflict",
        "metric_role": HIGH_AI_HARD_STOP_CONFLICT_CONTRACT["metric_role"],
        "decision_authority": HIGH_AI_HARD_STOP_CONFLICT_CONTRACT["decision_authority"],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "hard_gate": False,
        "score_floor": HIGH_AI_HARD_STOP_SCORE_FLOOR,
        "hard_stop_total": len(hard_stop_rows),
        "conflict_count": len(conflict_rows),
        "conflict_rate_in_hard_stop": _ratio(len(conflict_rows), len(hard_stop_rows)),
        "missed_upside_count": outcome_counter.get("MISSED_UPSIDE", 0),
        "good_exit_count": outcome_counter.get("GOOD_EXIT", 0),
        "neutral_count": outcome_counter.get("NEUTRAL", 0),
        "missed_upside_rate": _ratio(
            outcome_counter.get("MISSED_UPSIDE", 0), len(conflict_rows)
        ),
        "good_exit_rate": _ratio(
            outcome_counter.get("GOOD_EXIT", 0), len(conflict_rows)
        ),
        "avg_mfe_10m_pct": _avg(
            [_safe_float(row.get("mfe_10m_pct"), 0.0) for row in conflict_rows]
        ),
        "avg_close_10m_pct": _avg(
            [_safe_float(row.get("close_10m_pct"), 0.0) for row in conflict_rows]
        ),
        "avg_mae_10m_pct": _avg(
            [_safe_float(row.get("mae_10m_pct"), 0.0) for row in conflict_rows]
        ),
        "source_counts": dict(source_counter),
        "model_counts": dict(model_counter),
        "contract": dict(HIGH_AI_HARD_STOP_CONFLICT_CONTRACT),
    }


def _build_priority_actions(exit_rule_rows: list[dict], limit: int = 3) -> list[dict]:
    actions: list[dict] = []
    for row in exit_rule_rows:
        trades = int(row.get("trades", 0) or 0)
        tuning_score = float(row.get("tuning_pressure_score", 0.0) or 0.0)
        if trades < 2 or tuning_score < 55.0:
            continue
        actions.append(
            {
                "exit_rule": str(row.get("exit_rule") or "-"),
                "tuning_pressure_score": round(tuning_score, 1),
                "reason": (
                    f"missed {float(row.get('missed_upside_rate', 0.0) or 0.0):.1f}% / "
                    f"close10m {float(row.get('avg_close_10m_pct', 0.0) or 0.0):+.2f}% / "
                    f"예상추가수익 {int(row.get('estimated_extra_upside_10m_krw', 0) or 0):,}원"
                ),
                "suggested_test": str(row.get("tuning_hint") or ""),
            }
        )
        if len(actions) >= max(1, int(limit or 3)):
            break

    if actions:
        return actions

    return [
        {
            "exit_rule": "-",
            "tuning_pressure_score": 0.0,
            "reason": "당일 데이터에서 즉시 미세조정이 필요한 강한 신호가 없습니다.",
            "suggested_test": "표본 추가 후 재평가",
        }
    ]


def _case_view(row: dict) -> dict:
    result = {
        "post_sell_id": str(row.get("post_sell_id") or ""),
        "stock_code": str(row.get("stock_code") or ""),
        "stock_name": str(row.get("stock_name") or ""),
        "strategy": str(row.get("strategy") or ""),
        "position_tag": str(row.get("position_tag") or ""),
        "exit_rule": str(row.get("exit_rule") or "-"),
        "realized_result_label": str(
            row.get("realized_result_label")
            or _realized_result_label(row.get("profit_rate"))
        ),
        "exit_rule_profit_mismatch": bool(
            row.get(
                "exit_rule_profit_mismatch",
                _exit_rule_profit_mismatch(
                    row.get("exit_rule"), row.get("profit_rate")
                ),
            )
        ),
        "profit_rate": round(_safe_float(row.get("profit_rate"), 0.0), 3),
        "mfe_10m_pct": round(_safe_float(row.get("mfe_10m_pct"), 0.0), 3),
        "mae_10m_pct": round(_safe_float(row.get("mae_10m_pct"), 0.0), 3),
        "close_10m_pct": round(_safe_float(row.get("close_10m_pct"), 0.0), 3),
        "extra_upside_10m_pct": round(
            _safe_float(row.get("extra_upside_10m_pct"), 0.0), 3
        ),
        "extra_upside_10m_krw_est": int(
            _safe_int(row.get("extra_upside_10m_krw_est"), 0)
        ),
        "capture_efficiency_pct": round(
            _safe_float(row.get("capture_efficiency_pct"), 0.0), 1
        ),
        "high_ai_hard_stop_conflict": _safe_bool(
            row.get("high_ai_hard_stop_conflict", False)
        ),
        "hard_stop_conflict_dimension": str(
            row.get("hard_stop_conflict_dimension") or "not_hard_stop"
        ),
        "hard_stop_conflict_ai_score_band": str(
            row.get("hard_stop_conflict_ai_score_band") or "ai_score_missing"
        ),
        "ai_score_at_exit": round(
            _safe_float(row.get("ai_score_at_exit", row.get("current_ai_score")), 0.0),
            1,
        ),
        "ai_model_at_exit": str(row.get("ai_model_at_exit") or "-"),
        "ai_result_source_at_exit": str(row.get("ai_result_source_at_exit") or "-"),
    }
    for horizon in POST_SELL_LONG_HORIZONS_MIN:
        result[f"mfe_{horizon}m_pct"] = round(
            _safe_float(row.get(f"mfe_{horizon}m_pct"), 0.0), 3
        )
        result[f"mae_{horizon}m_pct"] = round(
            _safe_float(row.get(f"mae_{horizon}m_pct"), 0.0), 3
        )
        result[f"close_{horizon}m_pct"] = round(
            _safe_float(row.get(f"close_{horizon}m_pct"), 0.0), 3
        )
        result[f"extra_upside_{horizon}m_pct"] = round(
            _safe_float(row.get(f"extra_upside_{horizon}m_pct"), 0.0),
            3,
        )
        result[f"extra_upside_{horizon}m_krw_est"] = int(
            _safe_int(row.get(f"extra_upside_{horizon}m_krw_est"), 0)
        )
    return result


def build_post_sell_feedback_report(
    target_date: str,
    *,
    top_n: int = 10,
    evaluate_now: bool = True,
    token: str | None = None,
) -> dict:
    guarded = guard_stdin_heavy_build(
        snapshot_kind="post_sell_feedback",
        target_date=target_date,
        fallback_snapshot=load_monitor_snapshot("post_sell_feedback", target_date),
        request_details={
            "top_n": top_n,
            "evaluate_now": evaluate_now,
        },
    )
    if guarded is not None:
        return guarded

    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    if evaluate_now:
        summary = evaluate_post_sell_candidates(safe_date, token=token)
    else:
        existing_candidates = _load_jsonl(_candidate_path(safe_date))
        existing_evaluations = _load_jsonl(_evaluation_path(safe_date))
        summary = _build_summary_from_raw_rows(
            target_date=safe_date,
            candidates=existing_candidates,
            evaluations=existing_evaluations,
        )

    candidates = _load_jsonl(_candidate_path(safe_date))
    evaluations = _dedupe_latest_evaluations(_load_jsonl(_evaluation_path(safe_date)))
    rows = _enrich_post_sell_rows(candidates=candidates, evaluations=evaluations)
    evaluated_count = len(rows)
    top_limit = max(1, int(top_n or 10))

    if not rows:
        return {
            "date": safe_date,
            "summary": post_sell_feedback_summary_to_dict(summary),
            "metrics": {
                "total_candidates": int(summary.total_candidates),
                "evaluated_candidates": int(summary.evaluated_candidates),
                "missed_upside_rate": 0.0,
                "good_exit_rate": 0.0,
                "avg_realized_profit_rate": 0.0,
                "avg_extra_upside_10m_pct": 0.0,
                "median_extra_upside_10m_pct": 0.0,
                "avg_close_after_sell_10m_pct": 0.0,
                "capture_efficiency_avg_pct": 0.0,
                "estimated_extra_upside_10m_krw_sum": 0,
                "estimated_extra_upside_10m_krw_avg": 0,
                "avg_extra_upside_20m_pct": 0.0,
                "median_extra_upside_20m_pct": 0.0,
                "avg_close_after_sell_20m_pct": 0.0,
                "estimated_extra_upside_20m_krw_sum": 0,
                "estimated_extra_upside_20m_krw_avg": 0,
                "avg_extra_upside_30m_pct": 0.0,
                "median_extra_upside_30m_pct": 0.0,
                "avg_close_after_sell_30m_pct": 0.0,
                "estimated_extra_upside_30m_krw_sum": 0,
                "estimated_extra_upside_30m_krw_avg": 0,
                "avg_extra_upside_60m_pct": 0.0,
                "median_extra_upside_60m_pct": 0.0,
                "avg_close_after_sell_60m_pct": 0.0,
                "estimated_extra_upside_60m_krw_sum": 0,
                "estimated_extra_upside_60m_krw_avg": 0,
                "timing_tuning_pressure_score": 0.0,
            },
            "insight": {
                "headline": "post-sell 평가 데이터가 없습니다.",
                "comment": "후보 기록/장후 평가가 누적되면 수익 극대화 여지와 매도시점 튜닝 후보가 표시됩니다.",
            },
            "exit_rule_tuning": [],
            "tag_tuning": [],
            "priority_actions": _build_priority_actions([], limit=3),
            "soft_stop_forensics": _build_soft_stop_forensics([]),
            "high_ai_hard_stop_forensics": _build_high_ai_hard_stop_forensics([]),
            "top_missed_upside": [],
            "top_good_exit": [],
            "meta": {
                "schema_version": POST_SELL_REPORT_SCHEMA_VERSION,
                "generated_at": datetime.now().isoformat(),
                "evaluation_mode": "post_sell_minute_forward",
                "evaluation_horizons_min": list(POST_SELL_FEEDBACK_HORIZONS_MIN),
                "thresholds": {
                    "missed_upside_mfe_pct": float(
                        getattr(
                            TRADING_RULES,
                            "POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT",
                            0.8,
                        )
                        or 0.8
                    ),
                    "missed_upside_close_pct": float(
                        getattr(
                            TRADING_RULES,
                            "POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT",
                            0.3,
                        )
                        or 0.3
                    ),
                    "good_exit_mae_pct": float(
                        getattr(
                            TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT", -0.6
                        )
                        or -0.6
                    ),
                    "good_exit_close_pct": float(
                        getattr(
                            TRADING_RULES,
                            "POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT",
                            -0.2,
                        )
                        or -0.2
                    ),
                },
            },
        }

    outcome_counter = Counter(
        str(item.get("outcome") or "NEUTRAL").upper() for item in rows
    )
    missed_rate = _ratio(outcome_counter.get("MISSED_UPSIDE", 0), evaluated_count)
    good_rate = _ratio(outcome_counter.get("GOOD_EXIT", 0), evaluated_count)
    avg_profit = _avg([_safe_float(item.get("profit_rate"), 0.0) for item in rows])
    avg_extra_upside = _avg(
        [_safe_float(item.get("extra_upside_10m_pct"), 0.0) for item in rows]
    )
    median_extra_upside = _median(
        [_safe_float(item.get("extra_upside_10m_pct"), 0.0) for item in rows]
    )
    avg_close_10m = _avg([_safe_float(item.get("close_10m_pct"), 0.0) for item in rows])
    capture_avg = _avg(
        [
            _safe_float(item.get("capture_efficiency_pct"), 0.0)
            for item in rows
            if _safe_float(item.get("potential_peak_profit_rate_10m"), 0.0) > 0.0
        ]
    )
    est_extra_krw_sum = int(
        sum(_safe_int(item.get("extra_upside_10m_krw_est"), 0) for item in rows)
    )
    est_extra_krw_avg = (
        int(round(est_extra_krw_sum / evaluated_count)) if evaluated_count > 0 else 0
    )
    long_horizon_metrics: dict[str, float | int] = {}
    for horizon in POST_SELL_LONG_HORIZONS_MIN:
        long_extra_values = [
            _safe_float(item.get(f"extra_upside_{horizon}m_pct"), 0.0) for item in rows
        ]
        long_close_values = [
            _safe_float(item.get(f"close_{horizon}m_pct"), 0.0) for item in rows
        ]
        long_sum = int(
            sum(
                _safe_int(item.get(f"extra_upside_{horizon}m_krw_est"), 0)
                for item in rows
            )
        )
        long_horizon_metrics[f"avg_extra_upside_{horizon}m_pct"] = _avg(
            long_extra_values
        )
        long_horizon_metrics[f"median_extra_upside_{horizon}m_pct"] = _median(
            long_extra_values
        )
        long_horizon_metrics[f"avg_close_after_sell_{horizon}m_pct"] = _avg(
            long_close_values
        )
        long_horizon_metrics[f"estimated_extra_upside_{horizon}m_krw_sum"] = long_sum
        long_horizon_metrics[f"estimated_extra_upside_{horizon}m_krw_avg"] = (
            int(round(long_sum / evaluated_count)) if evaluated_count > 0 else 0
        )
    timing_pressure = _clamp(
        (missed_rate * 0.65)
        + _clamp(max(avg_close_10m, 0.0) * 35.0, 0.0, 25.0)
        + _clamp(max(avg_extra_upside, 0.0) * 8.0, 0.0, 10.0)
        - _clamp(good_rate * 0.15, 0.0, 15.0),
        0.0,
        100.0,
    )

    if missed_rate >= 45.0 and avg_close_10m >= 0.2:
        headline = "매도 후 추가 상승이 잦아 수익 극대화 여지가 큽니다."
    elif good_rate >= 40.0 and avg_close_10m <= 0.0:
        headline = "손실 회피형 매도는 유효했고 과도 완화는 주의가 필요합니다."
    elif timing_pressure >= 55.0:
        headline = "매도시점 미세조정 실험을 시작할 만한 신호가 관측됩니다."
    else:
        headline = "현재 매도 규칙은 크게 무너지지 않았고 표본 축적이 우선입니다."

    exit_rule_rows = _build_exit_rule_tuning_rows(rows)
    tag_rows = _build_tag_tuning_rows(rows)
    priority_actions = _build_priority_actions(exit_rule_rows, limit=3)
    soft_stop_forensics = _build_soft_stop_forensics(rows)
    high_ai_hard_stop_forensics = _build_high_ai_hard_stop_forensics(rows)

    top_missed = [
        _case_view(item)
        for item in sorted(
            [row for row in rows if str(row.get("outcome") or "") == "MISSED_UPSIDE"],
            key=lambda row: (
                _safe_int(row.get("extra_upside_10m_krw_est"), 0),
                _safe_float(row.get("extra_upside_10m_pct"), 0.0),
            ),
            reverse=True,
        )[:top_limit]
    ]
    top_good = [
        _case_view(item)
        for item in sorted(
            [row for row in rows if str(row.get("outcome") or "") == "GOOD_EXIT"],
            key=lambda row: _safe_float(row.get("mae_10m_pct"), 0.0),
        )[:top_limit]
    ]

    return {
        "date": safe_date,
        "summary": post_sell_feedback_summary_to_dict(summary),
        "metrics": {
            "total_candidates": int(summary.total_candidates),
            "evaluated_candidates": int(summary.evaluated_candidates),
            "missed_upside_rate": float(missed_rate),
            "good_exit_rate": float(good_rate),
            "avg_realized_profit_rate": float(avg_profit),
            "avg_extra_upside_10m_pct": float(avg_extra_upside),
            "median_extra_upside_10m_pct": float(median_extra_upside),
            "avg_close_after_sell_10m_pct": float(avg_close_10m),
            "capture_efficiency_avg_pct": float(capture_avg),
            "estimated_extra_upside_10m_krw_sum": int(est_extra_krw_sum),
            "estimated_extra_upside_10m_krw_avg": int(est_extra_krw_avg),
            **long_horizon_metrics,
            "timing_tuning_pressure_score": round(float(timing_pressure), 1),
        },
        "insight": {
            "headline": headline,
            "comment": (
                f"평가 {evaluated_count}건 기준으로 missed_upside {missed_rate:.1f}%, "
                f"good_exit {good_rate:.1f}%, 매도 후 10분 평균 종가 수익률 {avg_close_10m:+.2f}%입니다."
            ),
        },
        "exit_rule_tuning": exit_rule_rows,
        "tag_tuning": tag_rows,
        "priority_actions": priority_actions,
        "soft_stop_forensics": soft_stop_forensics,
        "high_ai_hard_stop_forensics": high_ai_hard_stop_forensics,
        "top_missed_upside": top_missed,
        "top_good_exit": top_good,
        "meta": {
            "schema_version": POST_SELL_REPORT_SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "evaluation_mode": "post_sell_minute_forward",
            "evaluation_horizons_min": list(POST_SELL_FEEDBACK_HORIZONS_MIN),
            "thresholds": {
                "missed_upside_mfe_pct": float(
                    getattr(
                        TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT", 0.8
                    )
                    or 0.8
                ),
                "missed_upside_close_pct": float(
                    getattr(
                        TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT", 0.3
                    )
                    or 0.3
                ),
                "good_exit_mae_pct": float(
                    getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT", -0.6)
                    or -0.6
                ),
                "good_exit_close_pct": float(
                    getattr(
                        TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT", -0.2
                    )
                    or -0.2
                ),
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Post-sell feedback report-only utilities."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--backfill-sim-candidates", action="store_true")
    parser.add_argument("--evaluate-sim", action="store_true")
    args = parser.parse_args(argv)

    result: dict = {"date": args.target_date, "runtime_effect": False}
    if args.backfill_sim_candidates:
        result["sim_backfill"] = (
            backfill_sim_post_sell_candidates_from_threshold_events(args.target_date)
        )
    if args.evaluate_sim:
        summary = evaluate_sim_post_sell_candidates(args.target_date)
        result["sim_evaluation"] = post_sell_feedback_summary_to_dict(summary)
        result["sim_evaluation_path"] = str(_sim_evaluation_path(args.target_date))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
