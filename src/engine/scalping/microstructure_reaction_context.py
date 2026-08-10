from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from src.utils.constants import DATA_DIR

CONTEXT_VERSION = "microstructure_reaction_context_v1"
REPORT_DIR = DATA_DIR / "report" / "microstructure_reaction_context"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
CLEAN_BASELINE_POLICY_PATH = DATA_DIR / "source_quality" / "clean_baseline_policy.json"
SOURCE_QUALITY_AUDIT_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
TRUSTED_TICK_VOLUME_SOURCES = {"15_abs", "13_delta"}

_ENTRY_OPPORTUNITY_STAGES = {
    "ai_confirmed",
    "ai_confirmed_terminal_no_budget",
    "blocked_ai_score",
    "pre_submit_entry_ai_authority_guard_block",
    "pre_submit_entry_ai_authority_retry",
    "rising_missed_tick_speed_entry_block",
    "scalp_entry_action_decision_snapshot",
    "watching_analyze_target",
}
_OPPORTUNITY_CLUSTER_GAP_MS = 120_000
_BLOCKER_LOOKAHEAD_MS = 15_000
_OUTCOME_REFERENCE_TOLERANCE_MS = 5_000
_DEFAULT_CLEAN_BASELINE_DATE = "2026-06-05"

CONTEXT_KEYS = (
    "microstructure_reaction_context_version",
    "microstructure_reaction_context_status",
    "microstructure_reaction_tick_aggressor_pressure_usable",
    "microstructure_reaction_tick_aggressor_trusted_count",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_context_hash",
    "tick_trade_value_source_counts",
    "tick_trade_value_1313_count",
    "tick_trade_value_1313_missing_count",
    "tick_trade_value_1313_missing_rate_pct",
    "trade_volume_source_counts",
    "trade_volume_1030_1031_vs_15_evaluable_count",
    "trade_volume_1030_1031_vs_15_mismatch_count",
    "trade_volume_1030_1031_vs_15_mismatch_rate_pct",
    "trade_volume_1030_1031_vs_15_comparison_contract",
    "trade_volume_1030_1031_vs_15_decision_usable",
    "tick_aggressor_source_counts",
    "kiwoom_0b_aux_observed_count",
    "kiwoom_0b_1313_present_count",
    "kiwoom_0b_1313_missing_count",
    "kiwoom_0b_1313_missing_rate_pct",
    "kiwoom_0b_trade_value_source_counts",
    "kiwoom_0b_trade_volume_source_counts",
    "kiwoom_0b_1030_1031_vs_15_evaluable_count",
    "kiwoom_0b_1030_1031_vs_15_mismatch_count",
    "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct",
    "ka10003_buy_dominance_observation",
    "ka10003_buy_dominance_observation_source_counts",
    "ka10003_buy_dominance_observation_trade_value_source_counts",
    "ka10003_buy_dominance_observation_inside_spread_count",
    "ka10003_buy_dominance_observation_split_vs_15_evaluable_count",
    "ka10003_buy_dominance_observation_split_vs_15_mismatch_count",
    "v_pw_now",
    "v_pw_source",
    "v_pw_runtime_support_usable",
    "v_pw_ws_value",
    "v_pw_rest_value",
    "ka10046_strength_source",
    "ka10046_strength_decision_authority",
    "ka10046_strength_runtime_effect",
    "ka10046_strength_rest_received_ts_ms",
    "market_data_signed_tape_state",
    "market_data_signed_tape_sample_count",
    "market_data_signed_tape_buy_count",
    "market_data_signed_tape_sell_count",
    "market_data_signed_tape_buy_volume",
    "market_data_signed_tape_sell_volume",
    "market_data_signed_tape_buy_ratio_pct",
    "market_data_rest_signed_tape_pressure_usable",
    "rest_signed_trade_ticks",
    "latency_true_ofi_direct_canary_signed_tape_window",
    "latency_true_ofi_direct_canary_signed_tape_min_samples",
    "latency_true_ofi_direct_canary_signed_tape_max_buy_ratio",
    "latency_true_ofi_direct_canary_signed_tape_sample_count",
    "latency_true_ofi_direct_canary_signed_tape_buy_count",
    "latency_true_ofi_direct_canary_signed_tape_sell_count",
    "latency_true_ofi_direct_canary_signed_tape_buy_volume",
    "latency_true_ofi_direct_canary_signed_tape_sell_volume",
    "latency_true_ofi_direct_canary_signed_tape_net_buy_volume",
    "latency_true_ofi_direct_canary_signed_tape_buy_ratio",
    "latency_true_ofi_direct_canary_signed_tape_latest_side",
    "latency_true_ofi_direct_canary_signed_tape_sell_dominated",
    "latency_true_ofi_direct_canary_signed_tape_latest_buy_single",
    "latency_true_ofi_direct_canary_signed_tape_latest_sell_single",
    "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated",
    "latency_true_ofi_direct_canary_tape_block_reason",
    "latency_true_ofi_direct_canary_tape_support_ok",
    "quote_stale",
    "quote_age_ms",
    "quote_age_at_submit_ms",
    "ws_age_ms",
    "market_data_freshness_state",
)

GENERIC_FRESHNESS_CONTEXT_KEYS = {
    "quote_stale",
    "quote_age_ms",
    "quote_age_at_submit_ms",
    "ws_age_ms",
    "market_data_freshness_state",
}

FORBIDDEN_USES = [
    "standalone_buy",
    "broker_guard_bypass",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
]

WORKORDER_FORBIDDEN_USES = [
    "standalone_buy",
    "submit_permission",
    "pressure_math",
    "broker_guard_bypass",
    "stale_quote_guard_bypass",
    "order_guard_relaxation",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
    "real_execution_quality_approval",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _rate_pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 3) if denominator > 0 else 0.0


def _dict_counter(value: Any) -> Counter:
    if isinstance(value, dict):
        return Counter(
            {str(key): int(_safe_float(count, 0.0)) for key, count in value.items()}
        )
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, dict):
                return Counter(
                    {
                        str(key): int(_safe_float(count, 0.0))
                        for key, count in parsed.items()
                    }
                )
    return Counter()


def _list_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, list):
                return parsed
    return []


def _safe_hhmmss_to_seconds(value: Any) -> int | None:
    try:
        text = str(value or "").replace(":", "").strip()
        if not text:
            return None
        if not text.isdigit():
            return None
        text = text.zfill(6)
        hour = int(text[0:2])
        minute = int(text[2:4])
        second = int(text[4:6])
        if hour > 23 or minute > 59 or second > 59:
            return None
        return (hour * 3600) + (minute * 60) + second
    except Exception:
        return None


def _normalize_tick_side(value: Any) -> str:
    raw = str(value or "").strip().upper()
    compact = raw.replace("+", "").replace("-", "").replace(" ", "")
    if raw in {"BUY", "B", "2"} or "매수" in compact:
        return "BUY"
    if raw in {"SELL", "S", "1"} or "매도" in compact:
        return "SELL"
    return raw


def _tick_price(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("price")
        or tick.get("trade_price")
        or tick.get("cur_prc")
        or tick.get("현재가")
        or tick.get("체결가"),
        0.0,
    )


def _tick_best_ask(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("best_ask")
        or tick.get("ask_price")
        or tick.get("ask")
        or tick.get("27"),
        0.0,
    )


def _tick_best_bid(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("best_bid")
        or tick.get("bid_price")
        or tick.get("bid")
        or tick.get("28"),
        0.0,
    )


TRUSTED_AGGRESSOR_SOURCES = {
    "orderbook_touch",
    "cached_orderbook_touch",
    "kiwoom_0b_signed_trade_volume",
    "provider_declared_side",
    "exchange_declared_side",
    "trusted_declared_side",
    "declared_aggressor_side",
}

ORDERBOOK_TOUCH_SOURCES = {
    "orderbook_touch",
    "cached_orderbook_touch",
}

ORDERBOOK_TOUCH_QUOTE_SOURCES = {
    "0B_inline_best_quote",
    "cached_top_of_book_ttl",
}


def infer_tick_aggressor_side(tick: dict[str, Any] | None) -> dict[str, Any]:
    tick = tick if isinstance(tick, dict) else {}
    declared_source = str(
        tick.get("aggressor_source") or tick.get("dir_source") or ""
    ).strip()
    declared_quality = str(tick.get("aggressor_quality") or "").strip()
    quote_source = str(tick.get("aggressor_quote_source") or "").strip()
    touch_source = (
        "cached_orderbook_touch"
        if declared_source == "cached_orderbook_touch"
        or quote_source == "cached_top_of_book_ttl"
        else "orderbook_touch"
    )

    def _touch_quality(default: str) -> str:
        if declared_quality and (
            declared_source in {"orderbook_touch", "cached_orderbook_touch"}
            or quote_source
        ):
            return declared_quality
        return default

    explicit = _normalize_tick_side(
        tick.get("aggressor_side")
        or tick.get("trade_aggressor_side")
        or tick.get("dir")
        or tick.get("side")
    )
    trade_price = _tick_price(tick)
    best_ask = _tick_best_ask(tick)
    best_bid = _tick_best_bid(tick)
    if (
        explicit in {"BUY", "SELL"}
        and declared_source == "kiwoom_0b_signed_trade_volume"
    ):
        return {
            "side": explicit,
            "source": declared_source,
            "quality": declared_quality or "signed_trade_volume",
            "declared_side": explicit,
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
            "touch_side": str(tick.get("aggressor_touch_side") or "UNKNOWN"),
            "touch_source": str(tick.get("aggressor_touch_source") or ""),
            "touch_quality": str(tick.get("aggressor_touch_quality") or ""),
            "touch_confirms_signed": tick.get("aggressor_touch_confirms_signed"),
        }
    if trade_price > 0 and (best_ask > 0 or best_bid > 0):
        raw_inline_quote = (
            not declared_source and not quote_source and ("27" in tick or "28" in tick)
        )
        trusted_touch_source = (
            declared_source in ORDERBOOK_TOUCH_SOURCES
            or quote_source in ORDERBOOK_TOUCH_QUOTE_SOURCES
            or raw_inline_quote
        )
        if not trusted_touch_source:
            return {
                "side": "UNKNOWN",
                "source": declared_source or "untrusted_orderbook_touch_source",
                "quality": "quote_with_untrusted_aggressor_source",
                "declared_side": explicit if explicit in {"BUY", "SELL"} else "UNKNOWN",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_ask <= 0 or best_bid <= 0:
            return {
                "side": "UNKNOWN",
                "source": "missing_best_quote",
                "quality": "partial_orderbook_touch_quote",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_ask > 0 and trade_price >= best_ask:
            return {
                "side": "BUY",
                "source": touch_source,
                "quality": _touch_quality("touch_or_crossed_ask"),
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_bid > 0 and trade_price <= best_bid:
            return {
                "side": "SELL",
                "source": touch_source,
                "quality": _touch_quality("touch_or_crossed_bid"),
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        return {
            "side": "UNKNOWN",
            "source": touch_source,
            "quality": _touch_quality("inside_spread_or_uncertain"),
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"} and declared_source in TRUSTED_AGGRESSOR_SOURCES:
        return {
            "side": explicit,
            "source": declared_source,
            "quality": str(
                tick.get("aggressor_quality") or "side_without_orderbook_touch"
            ),
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"}:
        return {
            "side": "UNKNOWN",
            "source": declared_source or "declared_tick_side_untrusted",
            "quality": "side_without_trusted_source",
            "declared_side": explicit,
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    return {
        "side": "UNKNOWN",
        "source": "missing_aggressor_side",
        "quality": "missing_orderbook_touch_and_side",
        "trade_price": trade_price,
        "best_ask": best_ask,
        "best_bid": best_bid,
    }


def _aggressor_pressure_usable(inferred: dict[str, Any] | None) -> bool:
    inferred = inferred if isinstance(inferred, dict) else {}
    if inferred.get("side") not in {"BUY", "SELL"}:
        return False
    return str(inferred.get("source") or "").strip() in TRUSTED_AGGRESSOR_SOURCES


def _tick_volume_pressure_usable(tick: dict[str, Any] | None) -> bool:
    tick = tick if isinstance(tick, dict) else {}
    source = str(
        tick.get("volume_source") or tick.get("trade_volume_source") or ""
    ).strip()
    # Legacy/test rows without explicit provenance remain usable. Once the WS
    # producer declares a source, cumulative 1030/1031 totals must not acquire
    # per-tick pressure authority.
    return not source or source in TRUSTED_TICK_VOLUME_SOURCES


def _age_ms_from_hhmmss(value: Any, *, now: datetime | None = None) -> int | None:
    tick_sec = _safe_hhmmss_to_seconds(value)
    if tick_sec is None:
        return None
    now_dt = now or datetime.now()
    now_sec = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    age_sec = now_sec - tick_sec
    if age_sec < -43200:
        age_sec += 86400
    elif age_sec > 43200:
        age_sec -= 86400
    return max(0, int(age_sec * 1000))


def _safe_epoch_ms(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        numeric = float(value)
        if numeric <= 0:
            return None
        if numeric > 1_000_000_000_000:
            return int(numeric)
        if numeric > 1_000_000_000:
            return int(numeric * 1000)
    except (TypeError, ValueError):
        pass
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        return int(datetime.fromisoformat(text).timestamp() * 1000)
    except Exception:
        return None


def _quote_age_ms(
    ws_data: dict[str, Any], *, now: datetime | None = None
) -> tuple[int | None, str]:
    quote_ts_keys = (
        "quote_age_ms",
        "ws_age_ms",
        "ws_received_at_ms",
        "quote_received_at_ms",
        "received_at_ms",
        "last_ws_update_ts",
        "last_update_ms",
        "updated_at_ms",
        "captured_at_ms",
        "timestamp_ms",
        "ts_ms",
        "updated_at",
        "timestamp",
    )
    now_ms = int((now or datetime.now()).timestamp() * 1000)
    for key in quote_ts_keys:
        raw = ws_data.get(key)
        if key in {"quote_age_ms", "ws_age_ms"}:
            age_value = _safe_float(raw, -1.0)
            if age_value >= 0:
                return int(age_value), key
            continue
        epoch_ms = _safe_epoch_ms(raw)
        if epoch_ms is None:
            continue
        return max(0, now_ms - epoch_ms), key
    return None, "missing"


def precompute_microstructure_reaction_inputs(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | float | int | None = None,
) -> dict[str, Any]:
    if isinstance(now, (int, float)):
        now = datetime.fromtimestamp(float(now))
    elif now is not None and not isinstance(now, datetime):
        now = None
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    recent_ticks = recent_ticks if isinstance(recent_ticks, list) else []
    recent_candles = recent_candles if isinstance(recent_candles, list) else []
    orderbook = (
        ws_data.get("orderbook") if isinstance(ws_data.get("orderbook"), dict) else {}
    )
    asks = [
        level
        for level in (
            orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        )
        if isinstance(level, dict)
    ]
    bids = [
        level
        for level in (
            orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        )
        if isinstance(level, dict)
    ]
    curr_price = _safe_float(ws_data.get("curr") or ws_data.get("curr_price"), 0.0)
    best_ask = _safe_float(asks[0].get("price") if asks else 0, curr_price)
    best_bid = _safe_float(bids[0].get("price") if bids else 0, curr_price)
    best_ask_vol = _safe_float(asks[0].get("volume") if asks else 0, 0.0)
    best_bid_vol = _safe_float(bids[0].get("volume") if bids else 0, 0.0)
    top3_ask_vol = sum(_safe_float(level.get("volume"), 0.0) for level in asks[:3])
    top3_bid_vol = sum(_safe_float(level.get("volume"), 0.0) for level in bids[:3])
    ticks = [tick for tick in recent_ticks[:10] if isinstance(tick, dict)]
    tick_latest_time = str(ticks[0].get("time") or "") if ticks else ""
    tick_age_ms = (
        _age_ms_from_hhmmss(tick_latest_time, now=now) if tick_latest_time else None
    )
    tick_secs = [_safe_hhmmss_to_seconds(tick.get("time")) for tick in ticks]
    aggressor_rows = [infer_tick_aggressor_side(tick) for tick in ticks]
    tick_trade_value_source_counts = Counter(
        str(tick.get("tick_trade_value_source") or "unknown")
        for tick in ticks
        if "tick_trade_value_source" in tick
    )
    tick_trade_value_observed_count = sum(tick_trade_value_source_counts.values())
    tick_trade_value_1313_count = tick_trade_value_source_counts.get("1313", 0)
    tick_trade_value_1313_missing_count = max(
        0,
        tick_trade_value_observed_count - tick_trade_value_1313_count,
    )
    trade_volume_source_counts = Counter(
        str(tick.get("volume_source") or tick.get("trade_volume_source") or "unknown")
        for tick in ticks
        if "volume_source" in tick or "trade_volume_source" in tick
    )
    trade_volume_mismatch_rows = [
        tick for tick in ticks if "trade_volume_1030_1031_vs_15_mismatch" in tick
    ]
    trade_volume_mismatch_count = sum(
        1
        for tick in trade_volume_mismatch_rows
        if _safe_bool(tick.get("trade_volume_1030_1031_vs_15_mismatch"), False)
    )
    candidate_pressure_rows = [
        (tick, inferred)
        for tick, inferred in zip(ticks, aggressor_rows)
        if _aggressor_pressure_usable(inferred) and _tick_volume_pressure_usable(tick)
    ]
    explicit_untrusted_volume_present = any(
        not _tick_volume_pressure_usable(tick)
        for tick in ticks
        if tick.get("volume_source") or tick.get("trade_volume_source")
    )
    pressure_rows = [] if explicit_untrusted_volume_present else candidate_pressure_rows
    trusted_tick_prices = [
        int(_safe_float(tick.get("price"), 0.0))
        for tick, _inferred in pressure_rows
        if _safe_float(tick.get("price"), 0.0) > 0
    ]
    buy_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "BUY"
    )
    sell_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "SELL"
    )
    total_vol = buy_vol + sell_vol
    buy_pressure_pct = (buy_vol / total_vol * 100.0) if total_vol > 0 else 50.0
    prices: list[float] = []
    volumes: list[float] = []
    pressure_volumes: list[float] = []
    for tick in ticks:
        price_value = _safe_float(tick.get("price"), 0.0)
        if price_value > 0:
            prices.append(price_value)
        volume_value = (
            _safe_float(tick.get("volume"), 0.0)
            if _tick_volume_pressure_usable(tick)
            else 0.0
        )
        if volume_value > 0:
            volumes.append(volume_value)
    for tick, _inferred in pressure_rows:
        volume_value = _safe_float(tick.get("volume"), 0.0)
        if volume_value > 0:
            pressure_volumes.append(volume_value)
    latest_price = prices[0] if prices else curr_price
    oldest_price = prices[-1] if prices else curr_price
    price_change_pct = (
        ((latest_price - oldest_price) / oldest_price * 100.0)
        if oldest_price > 0
        else 0.0
    )
    avg_tick_volume = mean(volumes) if volumes else 0.0
    avg_pressure_tick_volume = mean(pressure_volumes) if pressure_volumes else 0.0
    buy_at_or_above_ask_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "BUY"
        and _safe_float(tick.get("price"), 0.0) >= best_ask
    )
    large_buy_print_detected = (
        any(
            _aggressor_pressure_usable(inferred)
            and inferred.get("side") == "BUY"
            and _safe_float(tick.get("volume"), 0.0) >= avg_pressure_tick_volume * 2.2
            for tick, inferred in zip(ticks[:5], aggressor_rows[:5])
        )
        if avg_pressure_tick_volume > 0
        else False
    )
    large_sell_print_detected = (
        any(
            _aggressor_pressure_usable(inferred)
            and inferred.get("side") == "SELL"
            and _safe_float(tick.get("volume"), 0.0) >= avg_pressure_tick_volume * 2.2
            for tick, inferred in zip(ticks[:5], aggressor_rows[:5])
        )
        if avg_pressure_tick_volume > 0
        else False
    )
    price_buy_count: dict[float, int] = {}
    for tick, inferred in zip(ticks[:6], aggressor_rows[:6]):
        if not _aggressor_pressure_usable(inferred):
            continue
        if inferred.get("side") != "BUY":
            continue
        price_key = _safe_float(tick.get("price"), 0.0)
        price_buy_count[price_key] = price_buy_count.get(price_key, 0) + 1
    same_price_buy_absorption = max(price_buy_count.values()) if price_buy_count else 0
    candle_highs: list[float] = []
    candle_lows: list[float] = []
    for candle in recent_candles:
        if not isinstance(candle, dict):
            continue
        high_value = _safe_float(candle.get("고가"), 0.0)
        if high_value > 0:
            candle_highs.append(high_value)
        low_value = _safe_float(candle.get("저가"), 0.0)
        if low_value > 0:
            candle_lows.append(low_value)
    quote_age_ms, quote_age_source = _quote_age_ms(ws_data, now=now)
    return {
        "ws_data": ws_data,
        "recent_ticks": recent_ticks,
        "recent_candles": recent_candles,
        "asks": asks,
        "bids": bids,
        "curr_price": curr_price,
        "best_ask": best_ask,
        "best_bid": best_bid,
        "best_ask_vol": best_ask_vol,
        "best_bid_vol": best_bid_vol,
        "top3_ask_vol": top3_ask_vol,
        "top3_bid_vol": top3_bid_vol,
        "ticks": ticks,
        "tick_aggressor_rows": aggressor_rows,
        "tick_aggressor_source_counts": dict(
            Counter(str(row.get("source") or "unknown") for row in aggressor_rows)
        ),
        "tick_aggressor_quality_counts": dict(
            Counter(str(row.get("quality") or "unknown") for row in aggressor_rows)
        ),
        "tick_trade_value_source_counts": dict(
            sorted(tick_trade_value_source_counts.items())
        ),
        "tick_trade_value_1313_count": int(tick_trade_value_1313_count),
        "tick_trade_value_1313_missing_count": int(tick_trade_value_1313_missing_count),
        "tick_trade_value_1313_missing_rate_pct": _rate_pct(
            tick_trade_value_1313_missing_count,
            tick_trade_value_observed_count,
        ),
        "trade_volume_source_counts": dict(sorted(trade_volume_source_counts.items())),
        "trade_volume_1030_1031_vs_15_evaluable_count": len(trade_volume_mismatch_rows),
        "trade_volume_1030_1031_vs_15_mismatch_count": int(trade_volume_mismatch_count),
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            trade_volume_mismatch_count,
            len(trade_volume_mismatch_rows),
        ),
        "tick_aggressor_unknown_count": sum(
            1 for row in aggressor_rows if row.get("side") not in {"BUY", "SELL"}
        ),
        "tick_aggressor_orderbook_touch_count": sum(
            1 for row in aggressor_rows if row.get("source") == "orderbook_touch"
        ),
        "tick_aggressor_cached_orderbook_touch_count": sum(
            1 for row in aggressor_rows if row.get("source") == "cached_orderbook_touch"
        ),
        "tick_aggressor_price_heuristic_count": sum(
            1 for row in aggressor_rows if row.get("source") == "price_change_heuristic"
        ),
        # This count is consumed as an authority signal in entry/holding
        # guards.  Keep it aligned with pressure_rows rather than exposing
        # otherwise trusted rows from a mixed window that was failed closed.
        "tick_aggressor_trusted_count": len(pressure_rows),
        "tick_aggressor_pressure_usable": bool(pressure_rows),
        # Newest-first prices from the same rows that own trusted pressure.
        # Consumers must not substitute heuristic/untrusted tick prices.
        "trusted_tick_prices": trusted_tick_prices,
        "tick_sample_count": len(ticks),
        "tick_latest_time": tick_latest_time,
        "tick_age_ms": tick_age_ms,
        "tick_secs": tick_secs,
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "total_vol": total_vol,
        "buy_pressure_pct": buy_pressure_pct,
        "latest_price": latest_price,
        "oldest_price": oldest_price,
        "price_change_pct": price_change_pct,
        "avg_tick_volume": avg_tick_volume,
        "buy_at_or_above_ask_vol": buy_at_or_above_ask_vol,
        "large_buy_print_detected": large_buy_print_detected,
        "large_sell_print_detected": large_sell_print_detected,
        "same_price_buy_absorption": same_price_buy_absorption,
        "quote_age_ms": quote_age_ms,
        "quote_age_source": quote_age_source,
        "candle_highs": candle_highs,
        "candle_lows": candle_lows,
        "session_high": max(candle_highs or [curr_price]),
        "session_low": min(candle_lows or [curr_price]),
    }


def _context_hash(payload: dict[str, Any]) -> str:
    compact = {
        key: payload.get(key)
        for key in CONTEXT_KEYS
        if key != "microstructure_reaction_context_hash"
    }
    raw = json.dumps(compact, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def neutral_microstructure_reaction_context(status: str, reason: str) -> dict[str, Any]:
    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": status,
        "microstructure_reaction_tick_aggressor_pressure_usable": False,
        "microstructure_reaction_tick_aggressor_trusted_count": 0,
        "microstructure_reaction_ask_sweep_score": 50,
        "microstructure_reaction_post_sweep_hold_score": 50,
        "microstructure_reaction_bid_replenishment_score": 50,
        "microstructure_reaction_wall_replenishment_risk_score": 50,
        "microstructure_reaction_vi_proximity_risk": 0,
        "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
        "microstructure_reaction_source_quality": reason,
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    return payload


def build_microstructure_reaction_context(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
    precomputed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = (
        precomputed
        if isinstance(precomputed, dict)
        else precompute_microstructure_reaction_inputs(
            ws_data,
            recent_ticks,
            recent_candles,
            now=now,
        )
    )
    ws_data = (
        snapshot.get("ws_data") if isinstance(snapshot.get("ws_data"), dict) else {}
    )
    recent_candles = (
        snapshot.get("recent_candles")
        if isinstance(snapshot.get("recent_candles"), list)
        else []
    )
    asks = snapshot.get("asks") if isinstance(snapshot.get("asks"), list) else []
    bids = snapshot.get("bids") if isinstance(snapshot.get("bids"), list) else []
    if not asks or not bids:
        return neutral_microstructure_reaction_context(
            "source_quality_missing", "missing_orderbook"
        )
    if int(snapshot.get("tick_sample_count") or 0) < 5:
        return neutral_microstructure_reaction_context(
            "insufficient_window", "tick_sample_lt5"
        )

    tick_age_ms = snapshot.get("tick_age_ms")
    quote_age_ms = snapshot.get("quote_age_ms")
    if (tick_age_ms is not None and tick_age_ms > 5000) or (
        quote_age_ms is not None and quote_age_ms > 1200
    ):
        return neutral_microstructure_reaction_context("stale", "stale_tick_or_quote")
    curr_price = _safe_float(snapshot.get("curr_price"), 0.0)
    best_ask = _safe_float(snapshot.get("best_ask"), curr_price)
    best_bid = _safe_float(snapshot.get("best_bid"), curr_price)
    top3_ask_vol = _safe_float(snapshot.get("top3_ask_vol"), 0.0)
    top3_bid_vol = _safe_float(snapshot.get("top3_bid_vol"), 0.0)
    top3_depth_ratio = top3_ask_vol / top3_bid_vol if top3_bid_vol > 0 else 9.99

    sell_vol = _safe_float(snapshot.get("sell_vol"), 0.0)
    total_vol = _safe_float(snapshot.get("total_vol"), 0.0)
    pressure_usable = (
        _safe_bool(snapshot.get("tick_aggressor_pressure_usable"), False)
        and total_vol > 0
    )
    pressure_trusted_count = _safe_int(snapshot.get("tick_aggressor_trusted_count"), 0)
    if not pressure_usable:
        payload = neutral_microstructure_reaction_context(
            "source_quality_partial",
            "tick_aggressor_pressure_unusable",
        )
        payload["microstructure_reaction_tick_aggressor_trusted_count"] = (
            pressure_trusted_count
        )
        payload["microstructure_reaction_context_hash"] = _context_hash(payload)
        return payload
    buy_pressure = _safe_float(snapshot.get("buy_pressure_pct"), 50.0)
    latest_price = _safe_float(snapshot.get("latest_price"), curr_price)
    price_change_pct = _safe_float(snapshot.get("price_change_pct"), 0.0)
    buy_at_or_above_ask = _safe_float(snapshot.get("buy_at_or_above_ask_vol"), 0.0)
    ask_sweep_share = buy_at_or_above_ask / total_vol if total_vol > 0 else 0.0
    avg_vol = _safe_float(snapshot.get("avg_tick_volume"), 0.0)
    large_buy = bool(snapshot.get("large_buy_print_detected")) if avg_vol > 0 else False
    large_sell = (
        bool(snapshot.get("large_sell_print_detected")) if avg_vol > 0 else False
    )

    ask_sweep_score = _clamp_score(
        35
        + (buy_pressure - 50) * 0.7
        + ask_sweep_share * 35
        + (12 if price_change_pct > 0 else 0)
        + (8 if large_buy else 0)
    )
    post_sweep_hold_score = _clamp_score(
        50
        + min(25, max(-25, price_change_pct * 45))
        + (12 if latest_price >= best_ask else 0)
        - (15 if latest_price < best_bid else 0)
    )
    bid_ratio = top3_bid_vol / top3_ask_vol if top3_ask_vol > 0 else 2.0
    bid_replenishment_score = _clamp_score(
        45
        + min(30, bid_ratio * 14)
        + (10 if sell_vol > 0 and price_change_pct >= -0.05 else 0)
        - (10 if latest_price < best_bid else 0)
    )
    wall_replenishment_risk_score = _clamp_score(
        25
        + max(0, top3_depth_ratio - 1.0) * 28
        + (16 if large_sell else 0)
        + (10 if buy_pressure < 55 else 0)
    )

    fluctuation = _safe_float(ws_data.get("fluctuation"), 0.0)
    high = _safe_float(snapshot.get("session_high"), curr_price)
    low = _safe_float(snapshot.get("session_low"), curr_price)
    distance_from_high = (
        ((curr_price - high) / high * 100.0) if high > 0 and curr_price > 0 else -99.0
    )
    intraday_range = ((high - low) / low * 100.0) if high >= low and low > 0 else 0.0
    vi_proximity_risk = _clamp_score(
        max(0, fluctuation - 20) * 6
        + (20 if distance_from_high >= -0.25 and intraday_range >= 12 else 0)
    )

    if wall_replenishment_risk_score >= 70 or vi_proximity_risk >= 70:
        quality = "risk_context_only"
    elif (
        ask_sweep_score >= 65
        and post_sweep_hold_score >= 60
        and bid_replenishment_score >= 55
    ):
        quality = "favorable_reaction"
    elif ask_sweep_score <= 40 or post_sweep_hold_score <= 40:
        quality = "weak_reaction"
    else:
        quality = "mixed_reaction"

    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": "ok",
        "microstructure_reaction_tick_aggressor_pressure_usable": bool(pressure_usable),
        "microstructure_reaction_tick_aggressor_trusted_count": pressure_trusted_count,
        "microstructure_reaction_ask_sweep_score": ask_sweep_score,
        "microstructure_reaction_post_sweep_hold_score": post_sweep_hold_score,
        "microstructure_reaction_bid_replenishment_score": bid_replenishment_score,
        "microstructure_reaction_wall_replenishment_risk_score": wall_replenishment_risk_score,
        "microstructure_reaction_vi_proximity_risk": vi_proximity_risk,
        "microstructure_reaction_entry_reaction_quality": quality,
        "microstructure_reaction_source_quality": "fresh_short_window",
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    return payload


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"microstructure_reaction_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    if path.exists():
        return path
    gz_path = Path(f"{path}.gz")
    return gz_path


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _has_context(fields: dict[str, Any]) -> bool:
    return any(
        key in fields
        for key in CONTEXT_KEYS
        if key not in GENERIC_FRESHNESS_CONTEXT_KEYS
    )


def _row_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    if not _has_context(fields):
        return None
    row = {
        "stock_code": str(
            event.get("stock_code") or fields.get("stock_code") or ""
        ).lstrip("A"),
        "stock_name": event.get("stock_name"),
        "event_time": event.get("emitted_at")
        or fields.get("event_time")
        or fields.get("event_ts"),
        "event_ts": fields.get("event_ts") or event.get("emitted_at"),
        "record_id": event.get("record_id") or fields.get("record_id"),
        "sim_record_id": fields.get("sim_record_id"),
        "sim_parent_record_id": fields.get("sim_parent_record_id"),
        "source_event_stage": fields.get("source_event_stage") or event.get("stage"),
        "stage": event.get("stage"),
        "actual_order_submitted": _safe_bool(
            fields.get("actual_order_submitted"), False
        ),
        "broker_order_forbidden": (
            _safe_bool(fields.get("broker_order_forbidden"), False)
            if "broker_order_forbidden" in fields
            else None
        ),
    }
    row.update({key: fields.get(key) for key in CONTEXT_KEYS})
    v_pw_expected = any(
        key in fields
        for key in ("v_pw_now", "v_pw_source", "latest_strength", "current_vpw")
    )
    row["v_pw_expected"] = v_pw_expected
    current_v_pw_source = str(row.get("v_pw_source") or "").strip().lower()
    if current_v_pw_source in {"", "missing", "unknown", "not_available"}:
        legacy_v_pw = _safe_float(
            (
                fields.get("latest_strength")
                if fields.get("latest_strength") not in (None, "", "-")
                else fields.get("current_vpw")
            ),
            0.0,
        )
        if legacy_v_pw > 0:
            row["v_pw_now"] = legacy_v_pw
            row["v_pw_ws_value"] = legacy_v_pw
            row["v_pw_source"] = "ws_0b_latest_strength"
            row["v_pw_report_provenance_backfilled"] = True
        elif not v_pw_expected:
            row["v_pw_source"] = "not_applicable"

    comparison_contract = str(
        row.get("trade_volume_1030_1031_vs_15_comparison_contract") or ""
    ).strip()
    comparison_evaluable_count = _safe_int(
        row.get("trade_volume_1030_1031_vs_15_evaluable_count"),
        0,
    )
    if not comparison_contract and comparison_evaluable_count > 0:
        volume_sources = _dict_counter(row.get("trade_volume_source_counts"))
        if volume_sources.get("1030_1031_sum", 0) > 0:
            comparison_contract = "cumulative_split_vs_tick_not_comparable"
        else:
            comparison_contract = "comparison_scope_unknown"
        row["trade_volume_1030_1031_vs_15_comparison_contract"] = comparison_contract
        row["trade_volume_1030_1031_vs_15_contract_inferred_for_report"] = True
    if comparison_contract:
        row["trade_volume_1030_1031_vs_15_decision_usable"] = (
            comparison_contract == "same_tick_comparable"
        )
    observation = fields.get("ka10003_buy_dominance_observation")
    if isinstance(observation, dict):
        row["ka10003_buy_dominance_observation_source_counts"] = (
            row.get("ka10003_buy_dominance_observation_source_counts")
            or observation.get("source_counts")
            or {}
        )
        row["ka10003_buy_dominance_observation_trade_value_source_counts"] = (
            row.get("ka10003_buy_dominance_observation_trade_value_source_counts")
            or observation.get("trade_value_source_counts")
            or {}
        )
        row["ka10003_buy_dominance_observation_inside_spread_count"] = (
            row.get("ka10003_buy_dominance_observation_inside_spread_count")
            if row.get("ka10003_buy_dominance_observation_inside_spread_count")
            not in (None, "")
            else observation.get("inside_spread_count")
        )
        row["ka10003_buy_dominance_observation_split_vs_15_evaluable_count"] = (
            row.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count")
            if row.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count")
            not in (None, "")
            else observation.get("split_vs_15_evaluable_count")
        )
        row["ka10003_buy_dominance_observation_split_vs_15_mismatch_count"] = (
            row.get("ka10003_buy_dominance_observation_split_vs_15_mismatch_count")
            if row.get("ka10003_buy_dominance_observation_split_vs_15_mismatch_count")
            not in (None, "")
            else observation.get("split_vs_15_mismatch_count")
        )
    return row


def _sum_int(rows: list[dict[str, Any]], key: str) -> int:
    return sum(_safe_int(row.get(key), 0) for row in rows)


def _sum_counter_rows(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter = Counter()
    for row in rows:
        counter.update(_dict_counter(row.get(key)))
    return dict(sorted(counter.items()))


def _field_counter(
    rows: list[dict[str, Any]], key: str, *, default: str = "missing"
) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or default) for row in rows).items()))


def _rest_signed_trade_tick_count(rows: list[dict[str, Any]]) -> int:
    return sum(len(_list_value(row.get("rest_signed_trade_ticks"))) for row in rows)


def _rest_signed_trade_tick_source_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter = Counter()
    for row in rows:
        for tick in _list_value(row.get("rest_signed_trade_ticks")):
            if not isinstance(tick, dict):
                counter["unparsed"] += 1
                continue
            source = (
                tick.get("rest_signed_tape_source")
                or tick.get("aggressor_source")
                or tick.get("source")
                or "unknown"
            )
            counter[str(source)] += 1
    return dict(sorted(counter.items()))


def _quote_freshness_state(row: dict[str, Any]) -> str:
    raw_state = str(row.get("market_data_freshness_state") or "").strip().lower()
    if raw_state in {"fresh", "stale", "missing", "unknown"}:
        return raw_state
    if "quote_stale" in row:
        if _safe_bool(row.get("quote_stale"), False):
            return "stale"
        return "fresh"
    age_candidates = (
        row.get("quote_age_ms"),
        row.get("quote_age_at_submit_ms"),
        row.get("ws_age_ms"),
    )
    ages = [_safe_float(value, -1.0) for value in age_candidates]
    ages = [age for age in ages if age >= 0]
    if not ages:
        return "unknown"
    return "stale" if min(ages) > 1200.0 else "fresh"


def _strength_diff_rows(rows: list[dict[str, Any]]) -> list[float]:
    diffs: list[float] = []
    for row in rows:
        ws_value = _safe_float(row.get("v_pw_ws_value"), 0.0)
        rest_value = _safe_float(row.get("v_pw_rest_value"), 0.0)
        if ws_value <= 0 or rest_value <= 0:
            continue
        diffs.append(abs(ws_value - rest_value))
    return diffs


def _microstructure_code_improvement_orders(
    summary: dict[str, Any], report_path: Path
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []

    def base_order(
        order_id: str,
        title: str,
        *,
        route: str,
        improvement_type: str,
        evidence: list[str],
    ) -> dict[str, Any]:
        order = {
            "order_id": order_id,
            "title": title,
            "source_report_type": "microstructure_reaction_context",
            "target_subsystem": "runtime_instrumentation",
            "lifecycle_stage": "entry_source_quality",
            "route": route,
            "threshold_family": "microstructure_reaction_context",
            "improvement_type": improvement_type,
            "priority": 2,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "entry_confidence_modifier_source_only",
            "metric_role": "source_quality_gate",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "microstructure source contract and forbidden-use counters",
            "forbidden_uses": list(WORKORDER_FORBIDDEN_USES),
            "evidence": [
                *evidence,
                "runtime_effect=false",
                "allowed_runtime_apply=false",
                "actual_order_submitted=false",
                "broker_order_forbidden=true",
            ],
            "expected_ev_effect": (
                "Close market-data provenance gaps before any later bounded runtime family can consume "
                "microstructure evidence."
            ),
            "files_likely_touched": [
                "src/engine/scalping/microstructure_reaction_context.py",
                "src/engine/scalping/market_data_enrichment.py",
                "src/utils/pipeline_event_logger.py",
                "src/engine/build_code_improvement_workorder.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_microstructure_reaction_context_report.py src/tests/test_market_data_enrichment.py src/tests/test_pipeline_event_logger.py src/tests/test_build_code_improvement_workorder.py",
                "regenerated microstructure_reaction_context keeps runtime_effect=false and allowed_runtime_apply=false",
                "postclose code_improvement_workorder includes or explicitly closes this source-only order",
            ],
            "source_paths": [str(report_path)],
            "implementation_provenance": {
                "implementation_type": "microstructure_source_quality_workorder_handoff",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "requires_separate_runtime_apply_candidate": True,
            },
        }
        if route == "auto_family_candidate":
            order["candidate_family"] = "microstructure_signed_tape_runtime_candidate"
        else:
            order["mapped_family"] = "microstructure_reaction_context"
        return order

    if (
        _safe_int(
            summary.get("market_data_rest_signed_tape_pressure_usable_true_count"), 0
        )
        > 0
    ):
        orders.append(
            base_order(
                "order_microstructure_rest_signed_tape_pressure_authority_violation",
                "REST signed tape pressure authority violation",
                route="instrumentation_order",
                improvement_type="source_quality_forbidden_use_violation",
                evidence=[
                    "market_data_rest_signed_tape_pressure_usable_true_count="
                    f"{summary.get('market_data_rest_signed_tape_pressure_usable_true_count')}",
                    "REST signed tape must remain negative-veto/source-quality provenance only",
                ],
            )
        )

    if _safe_int(summary.get("ka10046_strength_runtime_effect_true_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_ka10046_runtime_effect_violation",
                "ka10046 REST strength runtime-effect violation",
                route="instrumentation_order",
                improvement_type="source_quality_forbidden_use_violation",
                evidence=[
                    f"ka10046_strength_runtime_effect_true_count={summary.get('ka10046_strength_runtime_effect_true_count')}",
                    "ka10046 REST strength fallback must not create runtime support by itself",
                ],
            )
        )

    if _safe_int(summary.get("ka10046_strength_missing_received_ts_count"), 0) > 0:
        orders.append(
            base_order(
                "order_microstructure_ka10046_received_timestamp_gap",
                "ka10046 REST strength received timestamp gap",
                route="instrumentation_order",
                improvement_type="source_quality_timestamp_provenance_gap",
                evidence=[
                    f"ka10046_strength_missing_received_ts_count={summary.get('ka10046_strength_missing_received_ts_count')}",
                    "REST aggregate row time cannot substitute for client receive timestamp",
                ],
            )
        )

    row_count = _safe_int(summary.get("row_count"), 0)
    v_pw_expected_count = _safe_int(summary.get("v_pw_expected_count"), 0)
    v_pw_missing_count = _safe_int(summary.get("v_pw_missing_count"), 0)
    v_pw_missing_rate_pct = _safe_float(
        summary.get("v_pw_expected_missing_rate_pct"),
        0.0,
    )
    if v_pw_expected_count >= 20 and v_pw_missing_rate_pct >= 95.0:
        orders.append(
            base_order(
                "order_microstructure_v_pw_full_source_gap",
                "microstructure v_pw full source coverage gap",
                route="instrumentation_order",
                improvement_type="source_quality_coverage_gap",
                evidence=[
                    f"row_count={row_count}",
                    f"v_pw_expected_count={v_pw_expected_count}",
                    f"v_pw_missing_count={v_pw_missing_count}",
                    f"v_pw_expected_missing_rate_pct={v_pw_missing_rate_pct}",
                ],
            )
        )

    mismatch_evaluable_count = _safe_int(
        summary.get("trade_volume_1030_1031_vs_15_comparable_evaluable_count"),
        0,
    )
    mismatch_count = _safe_int(
        summary.get("trade_volume_1030_1031_vs_15_contract_violation_count"),
        0,
    )
    mismatch_rate_pct = _safe_float(
        summary.get("trade_volume_1030_1031_vs_15_contract_violation_rate_pct"),
        0.0,
    )
    if mismatch_evaluable_count >= 20 and mismatch_rate_pct >= 95.0:
        orders.append(
            base_order(
                "order_microstructure_trade_volume_split_contract_mismatch",
                "microstructure trade-volume split contract mismatch",
                route="instrumentation_order",
                improvement_type="source_quality_contract_mismatch",
                evidence=[
                    f"trade_volume_1030_1031_vs_15_comparable_evaluable_count={mismatch_evaluable_count}",
                    f"trade_volume_1030_1031_vs_15_contract_violation_count={mismatch_count}",
                    f"trade_volume_1030_1031_vs_15_contract_violation_rate_pct={mismatch_rate_pct}",
                ],
            )
        )

    if (
        _safe_int(summary.get("row_count"), 0) > 0
        and _safe_int(summary.get("rest_signed_trade_ticks_row_count"), 0) > 0
    ):
        orders.append(
            base_order(
                "order_microstructure_signed_tape_runtime_candidate_review",
                "signed tape runtime candidate review from source-quality observation",
                route="auto_family_candidate",
                improvement_type="runtime_candidate_design_review",
                evidence=[
                    f"rest_signed_trade_ticks_row_count={summary.get('rest_signed_trade_ticks_row_count')}",
                    f"market_data_signed_tape_state_counts={summary.get('market_data_signed_tape_state_counts') or {}}",
                    "candidate review only; no runtime apply until separate PREOPEN guard and family contract",
                ],
            )
        )

    if (
        _safe_int(
            summary.get(
                "ka10003_buy_dominance_observation_split_vs_15_evaluable_count"
            ),
            0,
        )
        > 0
    ):
        orders.append(
            base_order(
                "order_microstructure_ka10003_split_vs_15_observation_review",
                "ka10003 split-vs-15 observation review",
                route="instrumentation_order",
                improvement_type="source_quality_observation_review",
                evidence=[
                    "ka10003_buy_dominance_observation_split_vs_15_evaluable_count="
                    f"{summary.get('ka10003_buy_dominance_observation_split_vs_15_evaluable_count')}",
                    "ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct="
                    f"{summary.get('ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct')}",
                    "ka10003 remains observation-only and must not fill trusted pressure fields",
                ],
            )
        )

    return orders


def _latest_rows_by_stock(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        stock_code = str(row.get("stock_code") or "").strip()
        if not stock_code:
            continue
        latest[stock_code] = row
    return list(latest.values())


_DIAGNOSTIC_ROW_KEYS = (
    "stock_code",
    "stock_name",
    "event_time",
    "record_id",
    "sim_record_id",
    "sim_parent_record_id",
    "source_event_stage",
    "stage",
    "actual_order_submitted",
    "broker_order_forbidden",
    "microstructure_reaction_context_status",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
    "microstructure_reaction_tick_aggressor_pressure_usable",
    "microstructure_reaction_tick_aggressor_trusted_count",
    "market_data_freshness_state",
    "quote_age_ms",
    "ws_age_ms",
    "v_pw_source",
    "v_pw_runtime_support_usable",
)


def _compact_diagnostic_rows(
    rows: list[dict[str, Any]], *, limit: int = 200
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    def append_group(group: list[dict[str, Any]], group_limit: int) -> None:
        added = 0
        for row in group:
            key = tuple(
                str(row.get(field) or "")
                for field in ("record_id", "sim_record_id", "event_time", "stage")
            )
            if key in seen:
                continue
            seen.add(key)
            selected.append(
                {
                    field: row.get(field)
                    for field in _DIAGNOSTIC_ROW_KEYS
                    if field in row
                }
            )
            added += 1
            if added >= group_limit or len(selected) >= limit:
                return

    submitted = [row for row in rows if row.get("actual_order_submitted") is True]
    favorable = [
        row
        for row in rows
        if row.get("microstructure_reaction_entry_reaction_quality")
        == "favorable_reaction"
        and row.get("microstructure_reaction_context_status") == "ok"
    ]
    usable = [
        row for row in rows if row.get("microstructure_reaction_context_status") == "ok"
    ]
    source_quality_incidents = [
        row for row in rows if row.get("microstructure_reaction_context_status") != "ok"
    ]
    append_group(submitted, 50)
    append_group(favorable, 50)
    append_group(usable, 75)
    append_group(source_quality_incidents, 25)
    if len(selected) < limit:
        append_group(rows, limit - len(selected))
    return selected


def _is_entry_opportunity_row(row: dict[str, Any]) -> bool:
    stages = {
        str(row.get("stage") or "").strip(),
        str(row.get("source_event_stage") or "").strip(),
    }
    return bool(stages & _ENTRY_OPPORTUNITY_STAGES)


def _opportunity_identity(row: dict[str, Any]) -> tuple[str, str]:
    stock_code = str(row.get("stock_code") or "").lstrip("A")
    record_id = str(
        row.get("record_id")
        or row.get("sim_record_id")
        or row.get("sim_parent_record_id")
        or ""
    )
    return stock_code, record_id


def _unique_entry_opportunities(
    favorable_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered_rows = sorted(
        (row for row in favorable_rows if _is_entry_opportunity_row(row)),
        key=lambda row: (
            *_opportunity_identity(row),
            _safe_epoch_ms(row.get("event_time")) or 0,
        ),
    )
    opportunities: list[dict[str, Any]] = []
    latest_by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    for row in ordered_rows:
        identity = _opportunity_identity(row)
        event_ms = _safe_epoch_ms(row.get("event_time"))
        if not identity[0] or event_ms is None:
            continue
        previous = latest_by_identity.get(identity)
        if (
            previous is None
            or event_ms - int(previous["cluster_end_ms"]) > _OPPORTUNITY_CLUSTER_GAP_MS
        ):
            opportunity = {
                "opportunity_id": (
                    f"{identity[0]}:{identity[1] or 'record_missing'}:{event_ms}"
                ),
                "stock_code": identity[0],
                "stock_name": row.get("stock_name"),
                "record_id": identity[1] or None,
                "opportunity_identity_quality": (
                    "pass" if identity[1] else "record_missing"
                ),
                "observation_time": row.get("event_time"),
                "anchor_ms": event_ms,
                "cluster_end_ms": event_ms,
                "observation_event_count": 0,
                "observation_stages": set(),
                "actual_order_submitted": False,
            }
            opportunities.append(opportunity)
            latest_by_identity[identity] = opportunity
        else:
            opportunity = previous
        opportunity["cluster_end_ms"] = max(
            int(opportunity["cluster_end_ms"]), event_ms
        )
        opportunity["observation_event_count"] += 1
        opportunity["observation_stages"].add(
            str(row.get("source_event_stage") or row.get("stage") or "missing")
        )
        if row.get("actual_order_submitted") is True:
            opportunity["actual_order_submitted"] = True
    for opportunity in opportunities:
        opportunity["observation_stages"] = sorted(opportunity["observation_stages"])
    return opportunities


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields")
    return fields if isinstance(fields, dict) else {}


def _event_identity(event: dict[str, Any]) -> tuple[str, str]:
    fields = _event_fields(event)
    return (
        str(event.get("stock_code") or fields.get("stock_code") or "").lstrip("A"),
        str(event.get("record_id") or fields.get("record_id") or ""),
    )


def _blocking_event(event: dict[str, Any]) -> dict[str, Any] | None:
    fields = _event_fields(event)
    stage = str(event.get("stage") or fields.get("source_event_stage") or "")
    action = str(fields.get("ai_action") or fields.get("action") or "").strip().upper()
    chosen_action = str(fields.get("chosen_action") or "").strip().upper()
    explicitly_blocked = (
        stage.endswith("_block")
        or stage.endswith("_blocked")
        or "_guard_block" in stage
        or stage in {"latency_block", "ai_confirmed_terminal_no_budget"}
    )
    ai_veto = stage == "ai_confirmed" and action == "DROP"
    snapshot_veto = (
        stage == "scalp_entry_action_decision_snapshot"
        and chosen_action.startswith(("NO_BUY", "SKIP"))
        and _safe_bool(fields.get("broker_order_forbidden"), False)
    )
    if not (explicitly_blocked or ai_veto or snapshot_veto):
        return None
    reason = str(
        fields.get("block_reason")
        or fields.get("reason")
        or ("ai_drop" if ai_veto else stage)
    )
    blocker_class = "entry_guard"
    stage_and_reason = f"{stage} {reason}".lower()
    for token, candidate_class in (
        ("ai_", "ai_decision"),
        ("latency", "latency"),
        ("tick_speed", "tick_speed"),
        ("liquidity", "liquidity"),
        ("strength", "strength_momentum"),
        ("momentum", "strength_momentum"),
        ("overbought", "overbought"),
        ("source_quality", "source_quality"),
        ("quantity", "quantity"),
        ("zero_qty", "quantity"),
        ("cooldown", "cooldown"),
    ):
        if token in stage_and_reason:
            blocker_class = candidate_class
            break
    return {
        "first_blocker": stage,
        "first_blocker_reason": reason,
        "first_blocker_class": blocker_class,
        "first_blocker_time": event.get("emitted_at")
        or fields.get("event_time")
        or fields.get("event_ts"),
    }


def _attach_first_blockers(
    opportunities: list[dict[str, Any]], event_path: Path
) -> None:
    pending_by_identity: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for opportunity in opportunities:
        if opportunity.get("actual_order_submitted") is True:
            continue
        identity = (
            str(opportunity.get("stock_code") or ""),
            str(opportunity.get("record_id") or ""),
        )
        pending_by_identity.setdefault(identity, []).append(opportunity)
    if not pending_by_identity:
        return
    for event in _iter_jsonl(event_path) or []:
        identity = _event_identity(event)
        if identity not in pending_by_identity:
            continue
        event_ms = _safe_epoch_ms(
            event.get("emitted_at") or _event_fields(event).get("event_time")
        )
        if event_ms is None:
            continue
        blocker = _blocking_event(event)
        if blocker is None:
            continue
        for opportunity in pending_by_identity[identity]:
            if not (
                int(opportunity["anchor_ms"])
                <= event_ms
                <= int(opportunity["cluster_end_ms"]) + _BLOCKER_LOOKAHEAD_MS
            ):
                continue
            current_blocker_ms = _safe_epoch_ms(opportunity.get("first_blocker_time"))
            if current_blocker_ms is not None and current_blocker_ms <= event_ms:
                continue
            opportunity.update(blocker)


def _missed_entry_counterfactual_path(target_date: str) -> Path:
    base = MONITOR_SNAPSHOT_DIR / f"missed_entry_counterfactual_{target_date}.json"
    return base if base.exists() else Path(f"{base}.gz")


def _load_watch_cycle_outcomes(
    target_date: str,
) -> tuple[list[dict[str, Any]], Path, str]:
    path = _missed_entry_counterfactual_path(target_date)
    if not path.exists():
        return [], path, "missing"
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, TypeError):
        return [], path, "unreadable"
    ledger = payload.get("watch_cycle_participation_ledger")
    if not isinstance(ledger, dict) or not isinstance(ledger.get("rows"), list):
        return [], path, "contract_invalid"
    return (
        [row for row in ledger["rows"] if isinstance(row, dict)],
        path,
        "loaded",
    )


def _attach_time_exact_outcomes(
    opportunities: list[dict[str, Any]], target_date: str
) -> tuple[Path, str]:
    outcomes, path, source_status = _load_watch_cycle_outcomes(target_date)
    by_identity: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for outcome in outcomes:
        identity = (
            str(outcome.get("stock_code") or "").lstrip("A"),
            str(outcome.get("runtime_record_id") or ""),
        )
        if not identity[0] or not identity[1]:
            continue
        by_identity.setdefault(identity, []).append(outcome)
    for opportunity in opportunities:
        if opportunity.get("actual_order_submitted") is True:
            opportunity["outcome_join_status"] = "not_applicable_submitted"
            continue
        identity = (
            str(opportunity.get("stock_code") or ""),
            str(opportunity.get("record_id") or ""),
        )
        candidates: list[tuple[int, dict[str, Any]]] = []
        for outcome in by_identity.get(identity, []):
            reference_ms = _safe_epoch_ms(outcome.get("reference_time"))
            if reference_ms is None:
                continue
            candidates.append(
                (abs(reference_ms - int(opportunity["anchor_ms"])), outcome)
            )
        if not candidates:
            opportunity["outcome_join_status"] = "no_matching_watch_cycle"
            continue
        delta_ms, outcome = min(candidates, key=lambda item: item[0])
        opportunity["outcome_reference_delta_ms"] = delta_ms
        if delta_ms > _OUTCOME_REFERENCE_TOLERANCE_MS:
            opportunity["outcome_join_status"] = "reference_time_mismatch"
            continue
        source_quality = str(outcome.get("primary_source_quality_state") or "missing")
        opportunity.update(
            {
                "outcome_join_status": "time_exact",
                "outcome_source_quality": source_quality,
                "outcome_source_quality_pass": source_quality == "pass",
                "effective_venue": outcome.get("effective_venue"),
                "market_session_bucket": outcome.get("market_session_bucket"),
                "opportunity_label": outcome.get("opportunity_label"),
                "primary_horizon_min": outcome.get("primary_horizon_min"),
                "cost_adjusted_counterfactual_return_pct": outcome.get(
                    "cost_adjusted_counterfactual_return_pct"
                ),
                "forward_horizon_metrics": (
                    outcome.get("forward_horizon_metrics")
                    if isinstance(outcome.get("forward_horizon_metrics"), dict)
                    else {}
                ),
            }
        )
    return path, source_status


def _microstructure_exploration_funnel(
    rows: list[dict[str, Any]], target_date: str, event_path: Path
) -> dict[str, Any]:
    by_quality: dict[str, Counter[str]] = {}
    favorable_rows: list[dict[str, Any]] = []
    for row in rows:
        quality = str(
            row.get("microstructure_reaction_entry_reaction_quality") or "missing"
        )
        status = str(row.get("microstructure_reaction_context_status") or "missing")
        bucket = by_quality.setdefault(quality, Counter())
        bucket["observed"] += 1
        if status == "ok":
            bucket["usable"] += 1
        if row.get("actual_order_submitted") is True:
            bucket["actual_order_submitted"] += 1
        if quality == "favorable_reaction" and status == "ok":
            favorable_rows.append(row)
    favorable_submitted = sum(
        1 for row in favorable_rows if row.get("actual_order_submitted") is True
    )
    favorable_unsubmitted_rows = [
        row for row in favorable_rows if row.get("actual_order_submitted") is not True
    ]
    favorable_unsubmitted_stage_counts = Counter(
        str(row.get("source_event_stage") or "missing")
        for row in favorable_unsubmitted_rows
    )
    entry_favorable_rows = [
        row for row in favorable_rows if _is_entry_opportunity_row(row)
    ]
    opportunities = _unique_entry_opportunities(favorable_rows)
    _attach_first_blockers(opportunities, event_path)
    outcome_source_path, outcome_source_status = _attach_time_exact_outcomes(
        opportunities, target_date
    )
    unsubmitted_opportunities = [
        item for item in opportunities if item.get("actual_order_submitted") is not True
    ]
    attributed_opportunities = [
        item for item in unsubmitted_opportunities if item.get("first_blocker")
    ]
    joined_opportunities = [
        item
        for item in unsubmitted_opportunities
        if item.get("outcome_join_status") == "time_exact"
    ]
    source_quality_pass_opportunities = [
        item
        for item in joined_opportunities
        if item.get("outcome_source_quality_pass") is True
    ]
    blocker_counts = Counter(
        str(item.get("first_blocker") or "missing")
        for item in unsubmitted_opportunities
    )
    outcome_join_counts = Counter(
        str(item.get("outcome_join_status") or "missing")
        for item in unsubmitted_opportunities
    )
    identity_quality_counts = Counter(
        str(item.get("opportunity_identity_quality") or "missing")
        for item in opportunities
    )
    return {
        "metric_role": "opportunity_exploration_funnel",
        "decision_authority": "source_only_no_runtime_mutation",
        "window_policy": (
            "same_day_entry_stage_only_120s_attempt_cluster_with_15s_blocker_lookahead_"
            "and_5s_exact_outcome_reference"
        ),
        "sample_floor": "rolling_source_quality_pass_unique_opportunities_ge_20",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": (
            "entry_stage_only and unique stock-record-time attempt and first blocker "
            "within attempt window and outcome reference delta <=5s and horizon quality pass"
        ),
        "runtime_effect": False,
        "forbidden_uses": [
            "broker_guard_bypass",
            "direct_threshold_relaxation",
            "direct_order_submission",
            "raw_event_count_as_unique_opportunity_count",
            "record_only_cross_attempt_outcome_join",
            "realized_pnl_substitution",
        ],
        "by_quality": {
            quality: dict(counts) for quality, counts in sorted(by_quality.items())
        },
        "favorable_reaction_usable_count": len(favorable_rows),
        "favorable_reaction_submitted_count": favorable_submitted,
        "favorable_reaction_unsubmitted_count": len(favorable_rows)
        - favorable_submitted,
        # Observation-stage counts remain raw diagnostics and are not causal
        # blockers; the attempt-scoped attribution below owns that distinction.
        "favorable_reaction_unsubmitted_observation_stage_counts": dict(
            sorted(favorable_unsubmitted_stage_counts.items())
        ),
        "favorable_reaction_unsubmitted_unique_stock_count": len(
            {
                str(row.get("stock_code") or "")
                for row in favorable_unsubmitted_rows
                if row.get("stock_code")
            }
        ),
        "raw_favorable_event_count": len(favorable_rows),
        "entry_favorable_event_count": len(entry_favorable_rows),
        "holding_or_non_entry_favorable_event_count": len(favorable_rows)
        - len(entry_favorable_rows),
        "unique_entry_opportunity_count": len(opportunities),
        "unique_entry_submitted_opportunity_count": len(opportunities)
        - len(unsubmitted_opportunities),
        "unique_entry_unsubmitted_opportunity_count": len(unsubmitted_opportunities),
        "opportunity_identity_quality_counts": dict(
            sorted(identity_quality_counts.items())
        ),
        "first_blocker_attributed_count": len(attributed_opportunities),
        "first_blocker_counts": dict(sorted(blocker_counts.items())),
        "causal_blocker_attribution_complete": len(attributed_opportunities)
        == len(unsubmitted_opportunities),
        "outcome_time_exact_join_count": len(joined_opportunities),
        "outcome_source_quality_pass_count": len(source_quality_pass_opportunities),
        "outcome_join_status_counts": dict(sorted(outcome_join_counts.items())),
        "post_observation_outcome_join_complete": len(joined_opportunities)
        == len(unsubmitted_opportunities),
        "outcome_source_path": (
            str(outcome_source_path) if outcome_source_path.exists() else None
        ),
        "outcome_source_status": outcome_source_status,
        "required_downstream_join": (
            "generate attempt-time outcome rows for no_matching_watch_cycle or "
            "reference_time_mismatch opportunities"
        ),
        "favorable_reaction_unique_stock_count": len(
            {
                str(row.get("stock_code") or "")
                for row in favorable_rows
                if row.get("stock_code")
            }
        ),
        "opportunities": opportunities,
    }


def _clean_baseline_date() -> str:
    try:
        payload = json.loads(CLEAN_BASELINE_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return _DEFAULT_CLEAN_BASELINE_DATE
    return str(
        payload.get("clean_tuning_baseline_date") or _DEFAULT_CLEAN_BASELINE_DATE
    )


def _available_pipeline_dates(target_date: str) -> list[str]:
    baseline_date = _clean_baseline_date()
    dates: set[str] = set()
    for path in PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl*"):
        date_part = path.name.removeprefix("pipeline_events_")[:10]
        if baseline_date <= date_part <= target_date:
            dates.add(date_part)
    return sorted(dates)


def _daily_opportunity_rollup_path(target_date: str) -> Path:
    return (
        REPORT_DIR
        / "daily_opportunity_rollups"
        / f"microstructure_opportunity_rollup_{target_date}.json"
    )


def _source_signature(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": None, "size_bytes": 0, "mtime_ns": 0}
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _source_quality_audit_path(target_date: str) -> Path:
    return SOURCE_QUALITY_AUDIT_DIR / (
        f"observation_source_quality_audit_{target_date}.json"
    )


def _source_quality_preflight(target_date: str) -> dict[str, Any]:
    path = _source_quality_audit_path(target_date)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {
            "status": "missing_or_unreadable",
            "tuning_input_allowed": False,
            "blocked_reason": "source_quality_preflight_missing_or_unreadable",
            "signature": _source_signature(path),
        }
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    allowed = payload.get("tuning_input_allowed")
    if allowed is None:
        allowed = summary.get("tuning_input_allowed")
    return {
        "status": str(payload.get("status") or summary.get("status") or "missing"),
        "tuning_input_allowed": allowed is True,
        "blocked_reason": payload.get("blocked_reason")
        or summary.get("blocked_reason"),
        "signature": _source_signature(path),
    }


def _lightweight_daily_opportunity_funnel(
    target_date: str,
) -> tuple[dict[str, Any], Path]:
    event_path = _event_path(target_date)
    favorable_rows: list[dict[str, Any]] = []
    for event in _iter_jsonl(event_path) or []:
        fields = _event_fields(event)
        if (
            fields.get("microstructure_reaction_entry_reaction_quality")
            == "favorable_reaction"
            and fields.get("microstructure_reaction_context_status") == "ok"
        ):
            row = _row_from_event(event)
            if row is not None:
                favorable_rows.append(row)

    opportunities = _unique_entry_opportunities(favorable_rows)
    _attach_first_blockers(opportunities, event_path)
    outcome_path, outcome_source_status = _attach_time_exact_outcomes(
        opportunities, target_date
    )
    entry_rows = [row for row in favorable_rows if _is_entry_opportunity_row(row)]
    unsubmitted = [
        item for item in opportunities if item.get("actual_order_submitted") is not True
    ]
    first_blocker_counts = Counter(
        str(item.get("first_blocker") or "missing") for item in unsubmitted
    )
    outcome_join_counts = Counter(
        str(item.get("outcome_join_status") or "missing") for item in unsubmitted
    )
    return (
        {
            "raw_favorable_event_count": len(favorable_rows),
            "entry_favorable_event_count": len(entry_rows),
            "holding_or_non_entry_favorable_event_count": len(favorable_rows)
            - len(entry_rows),
            "unique_entry_opportunity_count": len(opportunities),
            "unique_entry_submitted_opportunity_count": len(opportunities)
            - len(unsubmitted),
            "unique_entry_unsubmitted_opportunity_count": len(unsubmitted),
            "first_blocker_attributed_count": sum(
                1 for item in unsubmitted if item.get("first_blocker")
            ),
            "first_blocker_counts": dict(sorted(first_blocker_counts.items())),
            "outcome_time_exact_join_count": sum(
                1
                for item in unsubmitted
                if item.get("outcome_join_status") == "time_exact"
            ),
            "outcome_source_quality_pass_count": sum(
                1
                for item in unsubmitted
                if item.get("outcome_source_quality_pass") is True
            ),
            "outcome_join_status_counts": dict(sorted(outcome_join_counts.items())),
            "outcome_source_path": str(outcome_path) if outcome_path.exists() else None,
            "outcome_source_status": outcome_source_status,
            "opportunities": opportunities,
        },
        event_path,
    )


def _daily_opportunity_rollup(
    target_date: str,
    funnel: dict[str, Any],
    event_path: Path,
) -> dict[str, Any]:
    opportunities = (
        funnel.get("opportunities")
        if isinstance(funnel.get("opportunities"), list)
        else []
    )
    pass_opportunities = [
        item
        for item in opportunities
        if isinstance(item, dict) and item.get("outcome_source_quality_pass") is True
    ]
    cost_adjusted_returns = [
        _safe_float(item.get("cost_adjusted_counterfactual_return_pct"), float("nan"))
        for item in pass_opportunities
    ]
    cost_adjusted_returns = [value for value in cost_adjusted_returns if value == value]
    primary_metrics: list[dict[str, Any]] = []
    for item in pass_opportunities:
        horizons = item.get("forward_horizon_metrics")
        if not isinstance(horizons, dict):
            continue
        primary = horizons.get(str(item.get("primary_horizon_min") or 20))
        if isinstance(primary, dict):
            primary_metrics.append(primary)
    label_counts = Counter(
        str(item.get("opportunity_label") or "missing") for item in pass_opportunities
    )
    outcome_path = _missed_entry_counterfactual_path(target_date)
    source_quality_preflight = _source_quality_preflight(target_date)
    return {
        "schema_version": 1,
        "date": target_date,
        "metric_role": "counterfactual_opportunity_attribution",
        "decision_authority": "source_only_no_runtime_mutation",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "input_read_mode": "two_pass_streaming_filtered_no_full_event_materialization",
        "source_event_signature": _source_signature(event_path),
        "outcome_source_signature": _source_signature(outcome_path),
        "source_quality_audit_signature": source_quality_preflight["signature"],
        "source_quality_preflight_status": source_quality_preflight["status"],
        "tuning_input_allowed": source_quality_preflight["tuning_input_allowed"],
        "source_quality_blocked_reason": source_quality_preflight["blocked_reason"],
        "raw_favorable_event_count": _safe_int(
            funnel.get("raw_favorable_event_count"), 0
        ),
        "entry_favorable_event_count": _safe_int(
            funnel.get("entry_favorable_event_count"), 0
        ),
        "holding_or_non_entry_favorable_event_count": _safe_int(
            funnel.get("holding_or_non_entry_favorable_event_count"), 0
        ),
        "unique_entry_opportunity_count": _safe_int(
            funnel.get("unique_entry_opportunity_count"), 0
        ),
        "unique_entry_submitted_opportunity_count": _safe_int(
            funnel.get("unique_entry_submitted_opportunity_count"), 0
        ),
        "unique_entry_unsubmitted_opportunity_count": _safe_int(
            funnel.get("unique_entry_unsubmitted_opportunity_count"), 0
        ),
        "first_blocker_attributed_count": _safe_int(
            funnel.get("first_blocker_attributed_count"), 0
        ),
        "first_blocker_counts": funnel.get("first_blocker_counts") or {},
        "outcome_time_exact_join_count": _safe_int(
            funnel.get("outcome_time_exact_join_count"), 0
        ),
        "outcome_source_quality_pass_count": len(pass_opportunities),
        "outcome_join_status_counts": funnel.get("outcome_join_status_counts") or {},
        "outcome_source_status": funnel.get("outcome_source_status") or "missing",
        "source_quality_adjusted_return_sum_pct": round(sum(cost_adjusted_returns), 6),
        "source_quality_adjusted_ev_evaluable_count": len(cost_adjusted_returns),
        "primary_mfe_sum_pct": round(
            sum(_safe_float(item.get("mfe_pct"), 0.0) for item in primary_metrics),
            6,
        ),
        "primary_mae_sum_pct": round(
            sum(_safe_float(item.get("mae_pct"), 0.0) for item in primary_metrics),
            6,
        ),
        "primary_horizon_evaluable_count": len(primary_metrics),
        "opportunity_label_counts": dict(sorted(label_counts.items())),
    }


def _write_daily_opportunity_rollup(rollup: dict[str, Any]) -> Path:
    path = _daily_opportunity_rollup_path(str(rollup.get("date") or ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rollup, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_daily_opportunity_rollup(target_date: str) -> dict[str, Any]:
    path = _daily_opportunity_rollup_path(target_date)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    event_signature = payload.get("source_event_signature")
    outcome_signature = payload.get("outcome_source_signature")
    source_quality_audit_signature = payload.get("source_quality_audit_signature")
    if (
        not isinstance(event_signature, dict)
        or not isinstance(outcome_signature, dict)
        or not isinstance(source_quality_audit_signature, dict)
    ):
        return {}
    current_event_signature = _source_signature(_event_path(target_date))
    current_outcome_signature = _source_signature(
        _missed_entry_counterfactual_path(target_date)
    )
    if event_signature != current_event_signature:
        return {}
    if outcome_signature != current_outcome_signature:
        return {}
    if source_quality_audit_signature != _source_signature(
        _source_quality_audit_path(target_date)
    ):
        return {}
    return payload


def backfill_clean_baseline_opportunity_rollups(target_date: str) -> dict[str, Any]:
    generated_dates: list[str] = []
    reused_dates: list[str] = []
    failed_dates: list[str] = []
    failure_details: list[dict[str, str]] = []
    for source_date in _available_pipeline_dates(target_date):
        if _load_daily_opportunity_rollup(source_date):
            reused_dates.append(source_date)
            continue
        try:
            funnel, event_path = _lightweight_daily_opportunity_funnel(source_date)
            _write_daily_opportunity_rollup(
                _daily_opportunity_rollup(source_date, funnel, event_path)
            )
            generated_dates.append(source_date)
        except Exception as exc:
            failed_dates.append(source_date)
            failure_details.append(
                {
                    "date": source_date,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
    return {
        "generated_dates": generated_dates,
        "reused_dates": reused_dates,
        "failed_dates": failed_dates,
        "failure_details": failure_details,
    }


def _sum_counter_field(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(field)
        if not isinstance(value, dict):
            continue
        counts.update({str(key): _safe_int(count, 0) for key, count in value.items()})
    return dict(sorted(counts.items()))


def _clean_baseline_cumulative_opportunity_exploration(
    target_date: str,
) -> dict[str, Any]:
    available_dates = _available_pipeline_dates(target_date)
    rows: list[dict[str, Any]] = []
    missing_rollup_dates: list[str] = []
    for source_date in available_dates:
        row = _load_daily_opportunity_rollup(source_date)
        if row:
            rows.append(row)
        else:
            missing_rollup_dates.append(source_date)
    decision_rows = [row for row in rows if row.get("tuning_input_allowed") is True]
    source_quality_excluded_dates = [
        {
            "date": str(row.get("date") or ""),
            "status": row.get("source_quality_preflight_status"),
            "blocked_reason": row.get("source_quality_blocked_reason"),
        }
        for row in rows
        if row.get("tuning_input_allowed") is not True
    ]
    pass_count = sum(
        _safe_int(row.get("outcome_source_quality_pass_count"), 0)
        for row in decision_rows
    )
    ev_count = sum(
        _safe_int(row.get("source_quality_adjusted_ev_evaluable_count"), 0)
        for row in decision_rows
    )
    ev_sum = sum(
        _safe_float(row.get("source_quality_adjusted_return_sum_pct"), 0.0)
        for row in decision_rows
    )
    horizon_count = sum(
        _safe_int(row.get("primary_horizon_evaluable_count"), 0)
        for row in decision_rows
    )
    unsubmitted_count = sum(
        _safe_int(row.get("unique_entry_unsubmitted_opportunity_count"), 0)
        for row in decision_rows
    )
    attributed_count = sum(
        _safe_int(row.get("first_blocker_attributed_count"), 0) for row in decision_rows
    )
    exact_join_count = sum(
        _safe_int(row.get("outcome_time_exact_join_count"), 0) for row in decision_rows
    )
    source_quality_adjusted_ev_pct = round(ev_sum / ev_count, 6) if ev_count else None
    sample_floor_met = pass_count >= 20
    source_complete = bool(available_dates) and not missing_rollup_dates
    if not source_complete:
        runtime_reflection_status = "source_quality_incomplete"
    elif not sample_floor_met:
        runtime_reflection_status = "sample_floor_not_met"
    elif source_quality_adjusted_ev_pct is None or source_quality_adjusted_ev_pct <= 0:
        runtime_reflection_status = "non_positive_ev_keep_observe"
    else:
        runtime_reflection_status = "bounded_candidate_review_only"
    runtime_reflection_blockers: list[str] = []
    if missing_rollup_dates:
        runtime_reflection_blockers.append("daily_rollup_missing_or_stale")
    outcome_source_status_counts = Counter(
        str(row.get("outcome_source_status") or "missing") for row in decision_rows
    )
    if outcome_source_status_counts.get("loaded", 0) < len(decision_rows):
        runtime_reflection_blockers.append(
            "historical_outcome_contract_coverage_incomplete"
        )
    if exact_join_count < unsubmitted_count:
        runtime_reflection_blockers.append(
            "exact_attempt_time_outcome_coverage_incomplete"
        )
    if not sample_floor_met:
        runtime_reflection_blockers.append(
            "source_quality_pass_outcome_sample_below_20"
        )
    if sample_floor_met and (
        source_quality_adjusted_ev_pct is None or source_quality_adjusted_ev_pct <= 0
    ):
        runtime_reflection_blockers.append("source_quality_adjusted_ev_not_positive")
    return {
        "metric_role": "counterfactual_opportunity_attribution",
        "decision_authority": "clean_baseline_cumulative_source_only",
        "window_policy": "clean_tuning_baseline_through_target_date_available_pipeline_dates",
        "sample_floor": "source_quality_pass_unique_opportunities_ge_20",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": (
            "all available source dates have fresh rollup and exact attempt-time outcome "
            "join rows contribute to EV"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_apply_required": False,
        "input_read_mode": "compact_daily_rollups_only",
        "runtime_reflection_status": runtime_reflection_status,
        "runtime_reflection_blockers": runtime_reflection_blockers,
        "required_runtime_reflection_actions": [
            "produce attempt-time outcome rows for no_matching_watch_cycle and reference_time_mismatch opportunities",
            "regenerate clean-baseline daily rollups and cumulative attribution after outcome coverage repair",
            "review one bounded PREOPEN candidate only after sample floor, positive EV, conflict, rollback, and post-apply attribution gates pass",
        ],
        "candidate_review_required": runtime_reflection_status
        == "bounded_candidate_review_only",
        "forbidden_uses": [
            "direct_threshold_mutation",
            "direct_runtime_apply",
            "broker_guard_bypass",
            "order_submission",
            "provider_route_change",
            "bot_restart",
            "pre_clean_baseline_tuning_evidence",
        ],
        "clean_tuning_baseline_date": _clean_baseline_date(),
        "window_end_date": target_date,
        "available_source_date_count": len(available_dates),
        "loaded_rollup_date_count": len(rows),
        "included_date_count": len(decision_rows),
        "included_dates": [str(row.get("date") or "") for row in decision_rows],
        "missing_or_stale_rollup_dates": missing_rollup_dates,
        "source_quality_excluded_dates": source_quality_excluded_dates,
        "raw_favorable_event_count": sum(
            _safe_int(row.get("raw_favorable_event_count"), 0) for row in decision_rows
        ),
        "entry_favorable_event_count": sum(
            _safe_int(row.get("entry_favorable_event_count"), 0)
            for row in decision_rows
        ),
        "unique_entry_opportunity_count": sum(
            _safe_int(row.get("unique_entry_opportunity_count"), 0)
            for row in decision_rows
        ),
        "unique_entry_unsubmitted_opportunity_count": unsubmitted_count,
        "first_blocker_attributed_count": attributed_count,
        "first_blocker_attribution_coverage_pct": _rate_pct(
            attributed_count, unsubmitted_count
        ),
        "first_blocker_counts": _sum_counter_field(
            decision_rows, "first_blocker_counts"
        ),
        "outcome_time_exact_join_count": exact_join_count,
        "outcome_time_exact_join_coverage_pct": _rate_pct(
            exact_join_count, unsubmitted_count
        ),
        "outcome_source_quality_pass_count": pass_count,
        "outcome_source_quality_pass_coverage_pct": _rate_pct(
            pass_count, unsubmitted_count
        ),
        "outcome_join_status_counts": _sum_counter_field(
            decision_rows, "outcome_join_status_counts"
        ),
        "outcome_source_status_date_counts": dict(
            sorted(outcome_source_status_counts.items())
        ),
        "opportunity_label_counts": _sum_counter_field(
            decision_rows, "opportunity_label_counts"
        ),
        "source_quality_adjusted_ev_pct": source_quality_adjusted_ev_pct,
        "source_quality_adjusted_ev_evaluable_count": ev_count,
        "primary_horizon_avg_mfe_pct": (
            round(
                sum(
                    _safe_float(row.get("primary_mfe_sum_pct"), 0.0)
                    for row in decision_rows
                )
                / horizon_count,
                6,
            )
            if horizon_count
            else None
        ),
        "primary_horizon_avg_mae_pct": (
            round(
                sum(
                    _safe_float(row.get("primary_mae_sum_pct"), 0.0)
                    for row in decision_rows
                )
                / horizon_count,
                6,
            )
            if horizon_count
            else None
        ),
        "primary_horizon_evaluable_count": horizon_count,
        "sample_floor_met": sample_floor_met,
        "daily_rows": rows,
    }


def _write_clean_baseline_cumulative_artifact(
    target_date: str, cumulative: dict[str, Any]
) -> tuple[Path, Path]:
    base = REPORT_DIR / (
        f"microstructure_reaction_context_{target_date}_clean_baseline_cumulative"
    )
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(cumulative, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(
        "\n".join(
            [
                f"# Microstructure Clean-Baseline Cumulative - {target_date}",
                "",
                f"- window: `{cumulative.get('clean_tuning_baseline_date')}` ~ `{target_date}`",
                "- available/included dates: "
                f"`{cumulative.get('available_source_date_count')}` / "
                f"`{cumulative.get('included_date_count')}`",
                f"- missing_or_stale_rollup_dates: `{cumulative.get('missing_or_stale_rollup_dates') or []}`",
                "- raw/entry/unique opportunities: "
                f"`{cumulative.get('raw_favorable_event_count')}` / "
                f"`{cumulative.get('entry_favorable_event_count')}` / "
                f"`{cumulative.get('unique_entry_opportunity_count')}`",
                "- exact_join/source_quality_pass: "
                f"`{cumulative.get('outcome_time_exact_join_count')}` / "
                f"`{cumulative.get('outcome_source_quality_pass_count')}`",
                "- exact_join/source_quality_pass coverage_pct: "
                f"`{cumulative.get('outcome_time_exact_join_coverage_pct')}` / "
                f"`{cumulative.get('outcome_source_quality_pass_coverage_pct')}`",
                f"- outcome_source_status_date_counts: `{cumulative.get('outcome_source_status_date_counts') or {}}`",
                f"- source_quality_adjusted_ev_pct: `{cumulative.get('source_quality_adjusted_ev_pct')}`",
                f"- primary_horizon_avg_mfe_pct: `{cumulative.get('primary_horizon_avg_mfe_pct')}`",
                f"- primary_horizon_avg_mae_pct: `{cumulative.get('primary_horizon_avg_mae_pct')}`",
                f"- sample_floor_met: `{cumulative.get('sample_floor_met')}`",
                f"- runtime_reflection_status: `{cumulative.get('runtime_reflection_status')}`",
                f"- runtime_reflection_blockers: `{cumulative.get('runtime_reflection_blockers') or []}`",
                "- runtime_effect/allowed_runtime_apply: `False` / `False`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return json_path, md_path


def build_microstructure_reaction_context_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    path = _event_path(target_date)
    rows = [
        row for event in (_iter_jsonl(path) or []) if (row := _row_from_event(event))
    ]
    status_counts = Counter(
        str(row.get("microstructure_reaction_context_status") or "missing")
        for row in rows
    )
    quality_counts = Counter(
        str(row.get("microstructure_reaction_entry_reaction_quality") or "-")
        for row in rows
    )
    source_quality_counts = Counter(
        str(row.get("microstructure_reaction_source_quality") or "-") for row in rows
    )
    stage_counts = Counter(str(row.get("stage") or "-") for row in rows)
    real_rows = [row for row in rows if row.get("actual_order_submitted") is True]
    latest_stock_rows = _latest_rows_by_stock(rows)
    v_pw_source_counts = _field_counter(rows, "v_pw_source")
    v_pw_expected_count = sum(1 for row in rows if row.get("v_pw_expected") is True)
    v_pw_expected_missing_count = sum(
        1
        for row in rows
        if row.get("v_pw_expected") is True
        and str(row.get("v_pw_source") or "missing") == "missing"
    )
    ka10046_fallback_rows = [
        row
        for row in rows
        if str(row.get("v_pw_source") or "") == "ka10046_rest_fallback"
    ]
    ka10046_fallback_quote_freshness_counts = dict(
        sorted(
            Counter(
                _quote_freshness_state(row) for row in ka10046_fallback_rows
            ).items()
        )
    )
    strength_diffs = _strength_diff_rows(rows)
    strength_divergence20_count = sum(1 for value in strength_diffs if value >= 20.0)
    window_trade_value_1313_count = _sum_int(rows, "tick_trade_value_1313_count")
    window_trade_value_1313_missing_count = _sum_int(
        rows, "tick_trade_value_1313_missing_count"
    )
    window_trade_volume_mismatch_evaluable_count = _sum_int(
        rows,
        "trade_volume_1030_1031_vs_15_evaluable_count",
    )
    window_trade_volume_mismatch_count = _sum_int(
        rows,
        "trade_volume_1030_1031_vs_15_mismatch_count",
    )
    comparable_trade_volume_rows = [
        row
        for row in rows
        if str(row.get("trade_volume_1030_1031_vs_15_comparison_contract") or "")
        == "same_tick_comparable"
    ]
    noncomparable_trade_volume_rows = [
        row
        for row in rows
        if str(row.get("trade_volume_1030_1031_vs_15_comparison_contract") or "")
        == "cumulative_split_vs_tick_not_comparable"
    ]
    unknown_contract_trade_volume_rows = [
        row
        for row in rows
        if str(row.get("trade_volume_1030_1031_vs_15_comparison_contract") or "")
        == "comparison_scope_unknown"
    ]
    comparable_trade_volume_evaluable_count = _sum_int(
        comparable_trade_volume_rows,
        "trade_volume_1030_1031_vs_15_evaluable_count",
    )
    comparable_trade_volume_mismatch_count = _sum_int(
        comparable_trade_volume_rows,
        "trade_volume_1030_1031_vs_15_mismatch_count",
    )
    noncomparable_trade_volume_evaluable_count = _sum_int(
        noncomparable_trade_volume_rows,
        "trade_volume_1030_1031_vs_15_evaluable_count",
    )
    unknown_contract_trade_volume_evaluable_count = _sum_int(
        unknown_contract_trade_volume_rows,
        "trade_volume_1030_1031_vs_15_evaluable_count",
    )
    cumulative_0b_count = _sum_int(latest_stock_rows, "kiwoom_0b_aux_observed_count")
    cumulative_1313_missing_count = _sum_int(
        latest_stock_rows, "kiwoom_0b_1313_missing_count"
    )
    cumulative_mismatch_evaluable_count = _sum_int(
        latest_stock_rows,
        "kiwoom_0b_1030_1031_vs_15_evaluable_count",
    )
    cumulative_mismatch_count = _sum_int(
        latest_stock_rows,
        "kiwoom_0b_1030_1031_vs_15_mismatch_count",
    )
    ka10003_split_vs_15_evaluable_count = _sum_int(
        rows,
        "ka10003_buy_dominance_observation_split_vs_15_evaluable_count",
    )
    ka10003_split_vs_15_mismatch_count = _sum_int(
        rows,
        "ka10003_buy_dominance_observation_split_vs_15_mismatch_count",
    )
    opportunity_exploration_funnel = _microstructure_exploration_funnel(
        rows, target_date, path
    )
    daily_opportunity_rollup_path = _write_daily_opportunity_rollup(
        _daily_opportunity_rollup(
            target_date,
            opportunity_exploration_funnel,
            path,
        )
    )
    opportunity_exploration_funnel["opportunities"] = (
        opportunity_exploration_funnel.get("opportunities") or []
    )[:50]
    clean_baseline_cumulative = _clean_baseline_cumulative_opportunity_exploration(
        target_date
    )
    cumulative_base = REPORT_DIR / (
        f"microstructure_reaction_context_{target_date}_clean_baseline_cumulative"
    )
    summary = {
        "available": bool(rows),
        "row_count": len(rows),
        "ok_count": status_counts.get("ok", 0),
        "missing_or_unusable_count": len(rows) - status_counts.get("ok", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "entry_reaction_quality_counts": dict(sorted(quality_counts.items())),
        "source_quality_counts": dict(sorted(source_quality_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "real_submitted_count": len(real_rows),
        "opportunity_exploration_funnel": opportunity_exploration_funnel,
        "clean_baseline_cumulative_opportunity_exploration": clean_baseline_cumulative,
        "v_pw_source_counts": v_pw_source_counts,
        "v_pw_rest_fallback_count": v_pw_source_counts.get("ka10046_rest_fallback", 0),
        "v_pw_ws_0b_count": (
            v_pw_source_counts.get("ws_0b", 0)
            + v_pw_source_counts.get("ws_0b_latest_strength", 0)
        ),
        "v_pw_report_provenance_backfilled_count": sum(
            1 for row in rows if row.get("v_pw_report_provenance_backfilled") is True
        ),
        "v_pw_expected_count": v_pw_expected_count,
        "v_pw_not_applicable_count": len(rows) - v_pw_expected_count,
        "v_pw_missing_count": v_pw_expected_missing_count,
        "v_pw_expected_missing_rate_pct": _rate_pct(
            v_pw_expected_missing_count,
            v_pw_expected_count,
        ),
        "v_pw_rest_fallback_rate_pct": _rate_pct(
            v_pw_source_counts.get("ka10046_rest_fallback", 0),
            len(rows),
        ),
        "v_pw_runtime_support_unusable_count": sum(
            1
            for row in rows
            if "v_pw_runtime_support_usable" in row
            and not _safe_bool(row.get("v_pw_runtime_support_usable"), False)
        ),
        "ka10046_rest_fallback_quote_freshness_counts": ka10046_fallback_quote_freshness_counts,
        "ka10046_rest_fallback_with_fresh_quote_count": ka10046_fallback_quote_freshness_counts.get(
            "fresh", 0
        ),
        "ka10046_rest_fallback_with_stale_quote_count": ka10046_fallback_quote_freshness_counts.get(
            "stale", 0
        ),
        "ka10046_strength_runtime_effect_true_count": sum(
            1
            for row in rows
            if _safe_bool(row.get("ka10046_strength_runtime_effect"), False)
        ),
        "ka10046_strength_missing_received_ts_count": sum(
            1
            for row in rows
            if str(row.get("ka10046_strength_source") or "")
            == "ka10046_rest_strength_trend"
            and _safe_int(row.get("ka10046_strength_rest_received_ts_ms"), 0) <= 0
        ),
        "ka10046_0b_strength_compare_evaluable_count": len(strength_diffs),
        "ka10046_0b_strength_abs_diff_avg": (
            round(sum(strength_diffs) / len(strength_diffs), 3)
            if strength_diffs
            else 0.0
        ),
        "ka10046_0b_strength_abs_diff_max": (
            round(max(strength_diffs), 3) if strength_diffs else 0.0
        ),
        "ka10046_0b_strength_divergence20_count": strength_divergence20_count,
        "ka10046_0b_strength_divergence20_rate_pct": _rate_pct(
            strength_divergence20_count,
            len(strength_diffs),
        ),
        "market_data_signed_tape_state_counts": _field_counter(
            rows, "market_data_signed_tape_state"
        ),
        "market_data_signed_tape_sample_count_total": _sum_int(
            rows, "market_data_signed_tape_sample_count"
        ),
        "market_data_signed_tape_buy_count_total": _sum_int(
            rows, "market_data_signed_tape_buy_count"
        ),
        "market_data_signed_tape_sell_count_total": _sum_int(
            rows, "market_data_signed_tape_sell_count"
        ),
        "market_data_signed_tape_buy_volume_total": _sum_int(
            rows, "market_data_signed_tape_buy_volume"
        ),
        "market_data_signed_tape_sell_volume_total": _sum_int(
            rows, "market_data_signed_tape_sell_volume"
        ),
        "market_data_rest_signed_tape_pressure_usable_true_count": sum(
            1
            for row in rows
            if _safe_bool(
                row.get("market_data_rest_signed_tape_pressure_usable"), False
            )
        ),
        "rest_signed_trade_ticks_row_count": _rest_signed_trade_tick_count(rows),
        "rest_signed_trade_ticks_source_counts": _rest_signed_trade_tick_source_counts(
            rows
        ),
        "latency_true_ofi_direct_canary_signed_tape_sample_count_total": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_sample_count",
        ),
        "latency_true_ofi_direct_canary_signed_tape_buy_count_total": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_buy_count",
        ),
        "latency_true_ofi_direct_canary_signed_tape_sell_count_total": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_sell_count",
        ),
        "latency_true_ofi_direct_canary_signed_tape_net_buy_volume_sum": _sum_int(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume",
        ),
        "latency_true_ofi_direct_canary_signed_tape_latest_side_counts": _field_counter(
            rows,
            "latency_true_ofi_direct_canary_signed_tape_latest_side",
        ),
        "latency_true_ofi_direct_canary_signed_tape_sell_dominated_count": sum(
            1
            for row in rows
            if _safe_bool(
                row.get("latency_true_ofi_direct_canary_signed_tape_sell_dominated"),
                False,
            )
        ),
        "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated_count": sum(
            1
            for row in rows
            if _safe_bool(
                row.get(
                    "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated"
                ),
                False,
            )
        ),
        "latency_true_ofi_direct_canary_tape_block_reason_counts": _field_counter(
            rows,
            "latency_true_ofi_direct_canary_tape_block_reason",
        ),
        "tick_aggressor_source_counts": _sum_counter_rows(
            rows, "tick_aggressor_source_counts"
        ),
        "tick_trade_value_source_counts": _sum_counter_rows(
            rows, "tick_trade_value_source_counts"
        ),
        "tick_trade_value_1313_count": window_trade_value_1313_count,
        "tick_trade_value_1313_missing_count": window_trade_value_1313_missing_count,
        "tick_trade_value_1313_missing_rate_pct": _rate_pct(
            window_trade_value_1313_missing_count,
            window_trade_value_1313_count + window_trade_value_1313_missing_count,
        ),
        "trade_volume_source_counts": _sum_counter_rows(
            rows, "trade_volume_source_counts"
        ),
        "trade_volume_1030_1031_vs_15_evaluable_count": window_trade_volume_mismatch_evaluable_count,
        "trade_volume_1030_1031_vs_15_mismatch_count": window_trade_volume_mismatch_count,
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            window_trade_volume_mismatch_count,
            window_trade_volume_mismatch_evaluable_count,
        ),
        "trade_volume_1030_1031_vs_15_comparison_contract_counts": _field_counter(
            rows,
            "trade_volume_1030_1031_vs_15_comparison_contract",
        ),
        "trade_volume_1030_1031_vs_15_comparable_evaluable_count": (
            comparable_trade_volume_evaluable_count
        ),
        "trade_volume_1030_1031_vs_15_contract_violation_count": (
            comparable_trade_volume_mismatch_count
        ),
        "trade_volume_1030_1031_vs_15_contract_violation_rate_pct": _rate_pct(
            comparable_trade_volume_mismatch_count,
            comparable_trade_volume_evaluable_count,
        ),
        "trade_volume_1030_1031_vs_15_noncomparable_count": (
            noncomparable_trade_volume_evaluable_count
        ),
        "trade_volume_1030_1031_vs_15_unknown_contract_count": (
            unknown_contract_trade_volume_evaluable_count
        ),
        "kiwoom_0b_latest_stock_count": len(latest_stock_rows),
        "kiwoom_0b_aux_observed_count": cumulative_0b_count,
        "kiwoom_0b_1313_present_count": _sum_int(
            latest_stock_rows, "kiwoom_0b_1313_present_count"
        ),
        "kiwoom_0b_1313_missing_count": cumulative_1313_missing_count,
        "kiwoom_0b_1313_missing_rate_pct": _rate_pct(
            cumulative_1313_missing_count, cumulative_0b_count
        ),
        "kiwoom_0b_trade_value_source_counts": _sum_counter_rows(
            latest_stock_rows,
            "kiwoom_0b_trade_value_source_counts",
        ),
        "kiwoom_0b_trade_volume_source_counts": _sum_counter_rows(
            latest_stock_rows,
            "kiwoom_0b_trade_volume_source_counts",
        ),
        "kiwoom_0b_1030_1031_vs_15_evaluable_count": cumulative_mismatch_evaluable_count,
        "kiwoom_0b_1030_1031_vs_15_mismatch_count": cumulative_mismatch_count,
        "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            cumulative_mismatch_count,
            cumulative_mismatch_evaluable_count,
        ),
        "ka10003_buy_dominance_observation_source_counts": _sum_counter_rows(
            rows,
            "ka10003_buy_dominance_observation_source_counts",
        ),
        "ka10003_buy_dominance_observation_trade_value_source_counts": _sum_counter_rows(
            rows,
            "ka10003_buy_dominance_observation_trade_value_source_counts",
        ),
        "ka10003_buy_dominance_observation_inside_spread_count": _sum_int(
            rows,
            "ka10003_buy_dominance_observation_inside_spread_count",
        ),
        "ka10003_buy_dominance_observation_split_vs_15_evaluable_count": ka10003_split_vs_15_evaluable_count,
        "ka10003_buy_dominance_observation_split_vs_15_mismatch_count": ka10003_split_vs_15_mismatch_count,
        "ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct": _rate_pct(
            ka10003_split_vs_15_mismatch_count,
            ka10003_split_vs_15_evaluable_count,
        ),
        "avg_ask_sweep_score": _avg_score(
            rows, "microstructure_reaction_ask_sweep_score"
        ),
        "avg_post_sweep_hold_score": _avg_score(
            rows, "microstructure_reaction_post_sweep_hold_score"
        ),
        "avg_bid_replenishment_score": _avg_score(
            rows, "microstructure_reaction_bid_replenishment_score"
        ),
        "max_vi_proximity_risk": max(
            [
                _safe_int(row.get("microstructure_reaction_vi_proximity_risk"), 0)
                for row in rows
            ]
            or [0]
        ),
    }
    json_path, md_path = report_paths(target_date)
    code_improvement_orders = _microstructure_code_improvement_orders(
        summary, json_path
    )
    summary["code_improvement_order_count"] = len(code_improvement_orders)
    summary["top_code_improvement_orders"] = [
        {
            "order_id": order.get("order_id"),
            "title": order.get("title"),
            "route": order.get("route"),
            "improvement_type": order.get("improvement_type"),
        }
        for order in code_improvement_orders[:5]
    ]
    diagnostic_rows = _compact_diagnostic_rows(rows)
    report = {
        "schema_version": 3,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "microstructure_reaction_context",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "entry_confidence_modifier_source_only",
        "metric_role": "feature_context",
        "window_policy": "same_day_short_window_runtime_events_plus_postclose_source_summary",
        "sample_floor": "none_for_v1_source_only",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "context_status ok and connection keys present",
        "forbidden_uses": FORBIDDEN_USES,
        "sources": {
            "pipeline_events": str(path) if path.exists() else None,
            "missed_entry_counterfactual": opportunity_exploration_funnel.get(
                "outcome_source_path"
            ),
            "daily_opportunity_rollup": str(daily_opportunity_rollup_path),
            "clean_baseline_cumulative_opportunity_exploration": str(
                cumulative_base.with_suffix(".json")
            ),
        },
        "summary": summary,
        "row_storage_policy": "priority_compact_diagnostics_max_200_full_source_retained_in_pipeline_jsonl",
        "source_row_count": len(rows),
        "stored_row_count": len(diagnostic_rows),
        "rows": diagnostic_rows,
        "code_improvement_orders": code_improvement_orders,
        "warnings": [
            message
            for message in [
                "pipeline_events_missing" if not path.exists() else "",
                "microstructure_reaction_context_missing" if not rows else "",
            ]
            if message
        ],
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(
        render_microstructure_reaction_context_markdown(report), encoding="utf-8"
    )
    _write_clean_baseline_cumulative_artifact(target_date, clean_baseline_cumulative)
    return report


def _avg_score(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [_safe_float(row.get(key), -1.0) for row in rows]
    values = [value for value in values if value >= 0]
    return round(sum(values) / len(values), 3) if values else None


def render_microstructure_reaction_context_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    funnel = (
        summary.get("opportunity_exploration_funnel")
        if isinstance(summary.get("opportunity_exploration_funnel"), dict)
        else {}
    )
    cumulative = (
        summary.get("clean_baseline_cumulative_opportunity_exploration")
        if isinstance(
            summary.get("clean_baseline_cumulative_opportunity_exploration"),
            dict,
        )
        else {}
    )
    lines = [
        f"# Microstructure Reaction Context - {report.get('date')}",
        "",
        "- runtime_effect: `False`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- forbidden_uses: `{report.get('forbidden_uses') or []}`",
        "",
        "## Summary",
        f"- available: `{summary.get('available')}`",
        f"- row_count: `{summary.get('row_count')}`",
        f"- ok/missing_or_unusable: `{summary.get('ok_count')}` / `{summary.get('missing_or_unusable_count')}`",
        f"- real_submitted_count: `{summary.get('real_submitted_count')}`",
        f"- status_counts: `{summary.get('status_counts') or {}}`",
        f"- entry_reaction_quality_counts: `{summary.get('entry_reaction_quality_counts') or {}}`",
        f"- source_quality_counts: `{summary.get('source_quality_counts') or {}}`",
        f"- stage_counts: `{summary.get('stage_counts') or {}}`",
        "- opportunity_funnel raw/entry/unique_unsubmitted: "
        f"`{funnel.get('raw_favorable_event_count')}` / "
        f"`{funnel.get('entry_favorable_event_count')}` / "
        f"`{funnel.get('unique_entry_unsubmitted_opportunity_count')}`",
        f"- opportunity_first_blocker_counts: `{funnel.get('first_blocker_counts') or {}}`",
        f"- opportunity_outcome_join_status_counts: `{funnel.get('outcome_join_status_counts') or {}}`",
        f"- opportunity_outcome_source_status: `{funnel.get('outcome_source_status')}`",
        "- opportunity_source_quality_pass/sample_floor: "
        f"`{funnel.get('outcome_source_quality_pass_count')}` / "
        f"`{funnel.get('sample_floor')}`",
        "- cumulative available/included dates: "
        f"`{cumulative.get('available_source_date_count')}` / "
        f"`{cumulative.get('included_date_count')}`",
        "- cumulative unique/pass/EV: "
        f"`{cumulative.get('unique_entry_opportunity_count')}` / "
        f"`{cumulative.get('outcome_source_quality_pass_count')}` / "
        f"`{cumulative.get('source_quality_adjusted_ev_pct')}`",
        f"- cumulative_runtime_reflection_status: `{cumulative.get('runtime_reflection_status')}`",
        f"- v_pw_source_counts: `{summary.get('v_pw_source_counts') or {}}`",
        f"- v_pw_rest_fallback_rate_pct: `{summary.get('v_pw_rest_fallback_rate_pct')}`",
        f"- v_pw_runtime_support_unusable_count: `{summary.get('v_pw_runtime_support_unusable_count')}`",
        f"- ka10046_rest_fallback_quote_freshness_counts: `{summary.get('ka10046_rest_fallback_quote_freshness_counts') or {}}`",
        f"- ka10046_strength_runtime_effect_true_count: `{summary.get('ka10046_strength_runtime_effect_true_count')}`",
        f"- ka10046_strength_missing_received_ts_count: `{summary.get('ka10046_strength_missing_received_ts_count')}`",
        "- ka10046_0b_strength_diff: "
        f"avg=`{summary.get('ka10046_0b_strength_abs_diff_avg')}` "
        f"max=`{summary.get('ka10046_0b_strength_abs_diff_max')}` "
        f"divergence20=`{summary.get('ka10046_0b_strength_divergence20_count')}` / "
        f"`{summary.get('ka10046_0b_strength_compare_evaluable_count')}` "
        f"(`{summary.get('ka10046_0b_strength_divergence20_rate_pct')}`%)",
        f"- market_data_signed_tape_state_counts: `{summary.get('market_data_signed_tape_state_counts') or {}}`",
        f"- market_data_signed_tape_sample_count_total: `{summary.get('market_data_signed_tape_sample_count_total')}`",
        f"- market_data_rest_signed_tape_pressure_usable_true_count: `{summary.get('market_data_rest_signed_tape_pressure_usable_true_count')}`",
        f"- rest_signed_trade_ticks_row_count: `{summary.get('rest_signed_trade_ticks_row_count')}`",
        f"- rest_signed_trade_ticks_source_counts: `{summary.get('rest_signed_trade_ticks_source_counts') or {}}`",
        "- latency_true_ofi_direct_canary_signed_tape: "
        f"sample_total=`{summary.get('latency_true_ofi_direct_canary_signed_tape_sample_count_total')}` "
        f"net_buy_volume_sum=`{summary.get('latency_true_ofi_direct_canary_signed_tape_net_buy_volume_sum')}` "
        f"sell_dominated=`{summary.get('latency_true_ofi_direct_canary_signed_tape_sell_dominated_count')}` "
        f"latest_single_sell_dominated=`{summary.get('latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated_count')}`",
        f"- latency_true_ofi_direct_canary_signed_tape_latest_side_counts: `{summary.get('latency_true_ofi_direct_canary_signed_tape_latest_side_counts') or {}}`",
        f"- latency_true_ofi_direct_canary_tape_block_reason_counts: `{summary.get('latency_true_ofi_direct_canary_tape_block_reason_counts') or {}}`",
        f"- tick_aggressor_source_counts: `{summary.get('tick_aggressor_source_counts') or {}}`",
        f"- tick_trade_value_source_counts: `{summary.get('tick_trade_value_source_counts') or {}}`",
        f"- tick_trade_value_1313_missing_rate_pct: `{summary.get('tick_trade_value_1313_missing_rate_pct')}`",
        f"- trade_volume_source_counts: `{summary.get('trade_volume_source_counts') or {}}`",
        "- trade_volume_1030_1031_vs_15_mismatch: "
        f"`{summary.get('trade_volume_1030_1031_vs_15_mismatch_count')}` / "
        f"`{summary.get('trade_volume_1030_1031_vs_15_evaluable_count')}` "
        f"(`{summary.get('trade_volume_1030_1031_vs_15_mismatch_rate_pct')}`%)",
        f"- kiwoom_0b_latest_stock_count: `{summary.get('kiwoom_0b_latest_stock_count')}`",
        f"- kiwoom_0b_trade_value_source_counts: `{summary.get('kiwoom_0b_trade_value_source_counts') or {}}`",
        f"- kiwoom_0b_1313_missing_rate_pct: `{summary.get('kiwoom_0b_1313_missing_rate_pct')}`",
        f"- kiwoom_0b_trade_volume_source_counts: `{summary.get('kiwoom_0b_trade_volume_source_counts') or {}}`",
        "- kiwoom_0b_1030_1031_vs_15_mismatch: "
        f"`{summary.get('kiwoom_0b_1030_1031_vs_15_mismatch_count')}` / "
        f"`{summary.get('kiwoom_0b_1030_1031_vs_15_evaluable_count')}` "
        f"(`{summary.get('kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct')}`%)",
        f"- ka10003_buy_dominance_observation_source_counts: `{summary.get('ka10003_buy_dominance_observation_source_counts') or {}}`",
        f"- ka10003_buy_dominance_observation_trade_value_source_counts: `{summary.get('ka10003_buy_dominance_observation_trade_value_source_counts') or {}}`",
        f"- ka10003_buy_dominance_observation_inside_spread_count: `{summary.get('ka10003_buy_dominance_observation_inside_spread_count')}`",
        "- ka10003_buy_dominance_observation_split_vs_15_mismatch: "
        f"`{summary.get('ka10003_buy_dominance_observation_split_vs_15_mismatch_count')}` / "
        f"`{summary.get('ka10003_buy_dominance_observation_split_vs_15_evaluable_count')}` "
        f"(`{summary.get('ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct')}`%)",
        f"- avg_ask_sweep_score: `{summary.get('avg_ask_sweep_score')}`",
        f"- avg_post_sweep_hold_score: `{summary.get('avg_post_sweep_hold_score')}`",
        f"- avg_bid_replenishment_score: `{summary.get('avg_bid_replenishment_score')}`",
        f"- max_vi_proximity_risk: `{summary.get('max_vi_proximity_risk')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        f"- code_improvement_order_count: `{summary.get('code_improvement_order_count')}`",
        f"- top_code_improvement_orders: `{summary.get('top_code_improvement_orders') or []}`",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build source-only microstructure reaction context artifact."
    )
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument(
        "--backfill-clean-baseline-rollups",
        action="store_true",
        help=(
            "Stream clean-baseline pipeline sources and create missing/stale compact "
            "daily opportunity rollups before building the target-date report."
        ),
    )
    args = parser.parse_args(argv)
    backfill = (
        backfill_clean_baseline_opportunity_rollups(args.date)
        if args.backfill_clean_baseline_rollups
        else None
    )
    report = build_microstructure_reaction_context_report(args.date)
    print(
        json.dumps(
            {
                "date": report.get("date"),
                "summary": report.get("summary"),
                "warnings": report.get("warnings"),
                "backfill": backfill,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
