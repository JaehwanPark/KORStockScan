"""Report-only panic sell microstructure state detector.

This module is intentionally detached from broker order paths.  It produces
advisory risk flags and evidence that panic_sell_defense can surface in reports.
"""

from __future__ import annotations

import math
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable


REPORT_NORMAL = "NORMAL"
REPORT_PANIC_SELL = "PANIC_SELL"
REPORT_RECOVERY_WATCH = "RECOVERY_WATCH"
REPORT_RECOVERY_CONFIRMED = "RECOVERY_CONFIRMED"


class PanicInternalState(str, Enum):
    NORMAL = "NORMAL"
    PANIC_CANDIDATE = "PANIC_CANDIDATE"
    PANIC_ACTIVE = "PANIC_ACTIVE"
    RECOVERY_CANDIDATE = "RECOVERY_CANDIDATE"
    RECOVERED = "RECOVERED"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class PanicSellDetectorConfig:
    short_window_bars: int = 3
    mid_window_bars: int = 6
    long_window_bars: int = 30
    min_bars_required: int = 3
    min_total_volume: float = 1.0

    panic_entry_score_threshold: float = 0.72
    panic_entry_confirm_bars: int = 2
    panic_entry_confirm_window: int = 3
    min_abs_drop_short_pct: float = 1.2
    min_abs_drop_mid_pct: float = 2.5
    return_z_panic_threshold: float = -2.2
    volume_spike_threshold: float = 2.8
    sell_ratio_threshold: float = 0.64
    ofi_z_panic_threshold: float = -2.0
    bid_depth_drop_threshold: float = 0.35
    spread_widen_threshold: float = 1.8
    close_near_low_threshold: float = 0.25

    recovery_score_threshold: float = 0.66
    recovery_confirm_bars: int = 2
    recovery_confirm_window: int = 4
    sell_ratio_recovery_max: float = 0.56
    ofi_z_recovery_min: float = -0.3
    bid_depth_refill_min: float = 0.65
    spread_recovery_max: float = 1.35
    close_location_recovery_min: float = 0.58
    no_new_low_bars: int = 3
    low_break_tolerance_pct: float = 0.15

    max_panic_active_bars: int = 60
    cooldown_bars: int = 12
    block_long_during_recovery_candidate: bool = True
    degrade_when_orderbook_missing: bool = True


@dataclass(frozen=True)
class PanicCandle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None = None


@dataclass(frozen=True)
class PanicTradeFlow:
    ts: datetime
    buy_volume: float
    sell_volume: float
    unknown_volume: float = 0.0

    @property
    def total_volume(self) -> float:
        return self.buy_volume + self.sell_volume + self.unknown_volume


@dataclass(frozen=True)
class PanicOrderbookMicro:
    ts: datetime
    best_bid: float | None = None
    best_ask: float | None = None
    bid_depth_l5: float | None = None
    ask_depth_l5: float | None = None
    spread_ratio: float | None = None
    bid_depth_drop_ratio: float | None = None
    bid_depth_refill_ratio: float | None = None
    ofi_z: float | None = None
    qi_ewma: float | None = None
    micro_state: str = "missing"
    ready: bool = False
    observer_healthy: bool = False


@dataclass(frozen=True)
class PanicSignal:
    state: str
    internal_state: str
    panic_score: float
    recovery_score: float
    panic_active: bool
    panic_entered: bool
    recovery_candidate: bool
    recovery_confirmed: bool
    risk_off: bool
    risk_off_advisory: bool
    allow_new_long: bool
    allow_new_long_advisory: bool
    confidence: float
    severity: str
    panic_low: float | None = None
    panic_start_ts: str | None = None
    cooldown_remaining: int = 0
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PanicSymbolSignal:
    stock_code: str
    stock_name: str
    signal: PanicSignal
    latest_event_at: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "latest_event_at": self.latest_event_at,
        }
        payload.update(self.signal.to_dict())
        return payload


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        result = float(str(value).replace("%", "").replace("+", "").replace(",", "").strip())
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value if value is not None else "").strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_dt(value: Any) -> datetime | None:
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _clamp01(value: float | None) -> float:
    if value is None or not math.isfinite(float(value)):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _avg(values: Iterable[float]) -> float | None:
    items = [float(value) for value in values if math.isfinite(float(value))]
    return (sum(items) / len(items)) if items else None


def _zscore(latest: float, history: list[float]) -> float:
    if len(history) < 3:
        return 0.0
    mean = sum(history) / len(history)
    variance = sum((value - mean) ** 2 for value in history) / len(history)
    std = math.sqrt(variance)
    if std <= 1e-9:
        return 0.0
    return (latest - mean) / std


def _ofi_cusum(values: list[float], *, direction: str) -> dict[str, Any]:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if len(clean) < 4:
        return {
            "direction": direction,
            "sample_count": len(clean),
            "triggered": False,
            "score": 0.0,
            "sigma": None,
            "k": None,
            "h": None,
            "reason": "insufficient_ofi_samples",
        }
    history = clean[:-1]
    mean = sum(history) / len(history)
    variance = sum((value - mean) ** 2 for value in history) / len(history)
    sigma = math.sqrt(variance)
    if sigma <= 1e-9:
        return {
            "direction": direction,
            "sample_count": len(clean),
            "triggered": False,
            "score": 0.0,
            "sigma": round(sigma, 6),
            "k": 0.0,
            "h": 0.0,
            "reason": "flat_ofi_sigma",
        }
    k = 0.5 * sigma
    h = 4.0 * sigma
    cumulative = 0.0
    if direction == "negative":
        for value in clean:
            cumulative = min(0.0, cumulative + (value - mean) + k)
        score = abs(cumulative)
    else:
        for value in clean:
            cumulative = max(0.0, cumulative + (value - mean) - k)
        score = cumulative
    return {
        "direction": direction,
        "sample_count": len(clean),
        "triggered": score >= h,
        "score": round(score, 6),
        "sigma": round(sigma, 6),
        "k": round(k, 6),
        "h": round(h, 6),
        "reason": "cusum_threshold_breached" if score >= h else "below_cusum_threshold",
    }


def _return_pct(candles: list[PanicCandle], bars: int) -> float:
    if len(candles) < 2:
        return 0.0
    idx = max(0, len(candles) - 1 - max(1, int(bars)))
    base = candles[idx].close
    close = candles[-1].close
    if base <= 0 or close <= 0:
        return 0.0
    return ((close / base) - 1.0) * 100.0


def _close_location(candle: PanicCandle) -> float:
    if candle.high > candle.low:
        return _clamp01((candle.close - candle.low) / (candle.high - candle.low))
    return 0.5


def _lower_wick_ratio(candle: PanicCandle) -> float:
    candle_range = candle.high - candle.low
    if candle_range <= 0:
        return 0.0
    lower_wick = min(candle.open, candle.close) - candle.low
    return _clamp01(lower_wick / candle_range)


def _trade_ratios(trades: list[PanicTradeFlow]) -> tuple[float | None, float | None]:
    if not trades:
        return None, None
    current = trades[-1]
    total = current.total_volume
    if total <= 0:
        return None, None
    return current.sell_volume / total, current.buy_volume / total


def _spread_ratio(orderbooks: list[PanicOrderbookMicro]) -> float | None:
    if not orderbooks:
        return None
    current = orderbooks[-1]
    if current.spread_ratio is not None:
        return current.spread_ratio
    if current.best_bid is None or current.best_ask is None:
        return None
    spread = max(0.0, float(current.best_ask) - float(current.best_bid))
    previous_spreads = [
        max(0.0, float(item.best_ask) - float(item.best_bid))
        for item in orderbooks[:-1]
        if item.best_bid is not None and item.best_ask is not None and float(item.best_ask) > 0
    ]
    baseline = _avg(previous_spreads)
    if baseline is None or baseline <= 0:
        return 1.0 if spread > 0 else 0.0
    return spread / baseline


def _bid_depth_drop(orderbooks: list[PanicOrderbookMicro]) -> float | None:
    if not orderbooks:
        return None
    current = orderbooks[-1]
    if current.bid_depth_drop_ratio is not None:
        return current.bid_depth_drop_ratio
    if current.bid_depth_l5 is None:
        return None
    baseline = _avg(
        float(item.bid_depth_l5)
        for item in orderbooks[:-1]
        if item.bid_depth_l5 is not None and float(item.bid_depth_l5) > 0
    )
    if baseline is None or baseline <= 0:
        return 0.0
    return max(0.0, 1.0 - (float(current.bid_depth_l5) / baseline))


def _bid_depth_refill(orderbooks: list[PanicOrderbookMicro], panic_baseline: float | None = None) -> float | None:
    if not orderbooks:
        return None
    current = orderbooks[-1]
    if current.bid_depth_refill_ratio is not None:
        return current.bid_depth_refill_ratio
    if current.bid_depth_l5 is None:
        return None
    baseline = panic_baseline
    if baseline is None or baseline <= 0:
        baseline = _avg(
            float(item.bid_depth_l5)
            for item in orderbooks[:-1]
            if item.bid_depth_l5 is not None and float(item.bid_depth_l5) > 0
        )
    if baseline is None or baseline <= 0:
        return 0.0
    return max(0.0, float(current.bid_depth_l5) / float(baseline))


def _orderbook_missing(orderbook: PanicOrderbookMicro | None) -> bool:
    if orderbook is None:
        return True
    if str(orderbook.micro_state or "").strip().lower() == "missing":
        return True
    return not any(
        value is not None
        for value in (
            orderbook.best_bid,
            orderbook.best_ask,
            orderbook.bid_depth_l5,
            orderbook.ask_depth_l5,
            orderbook.spread_ratio,
            orderbook.bid_depth_drop_ratio,
            orderbook.bid_depth_refill_ratio,
            orderbook.ofi_z,
            orderbook.qi_ewma,
        )
    )


def compute_panic_features(
    candles: list[PanicCandle],
    trades: list[PanicTradeFlow] | None,
    orderbooks: list[PanicOrderbookMicro] | None,
    *,
    config: PanicSellDetectorConfig,
    panic_low: float | None = None,
    panic_bid_depth_baseline: float | None = None,
) -> dict[str, Any]:
    trades = list(trades or [])
    orderbooks = list(orderbooks or [])
    candle = candles[-1]
    close_returns = []
    for idx in range(1, len(candles)):
        prev = candles[idx - 1].close
        curr = candles[idx].close
        if prev > 0 and curr > 0:
            close_returns.append(((curr / prev) - 1.0) * 100.0)
    current_return = close_returns[-1] if close_returns else 0.0
    recent_returns = close_returns[-max(config.long_window_bars, 3) : -1]
    ranges = [max(0.0, item.high - item.low) for item in candles[:-1]]
    range_baseline = _avg(ranges[-max(1, config.mid_window_bars) :])
    sell_ratio, buy_ratio = _trade_ratios(trades)
    prev_sell_ratio = None
    if len(trades) >= 2 and trades[-2].total_volume > 0:
        prev_sell_ratio = trades[-2].sell_volume / trades[-2].total_volume
    volumes = [max(0.0, item.volume) for item in candles]
    volume_base = _avg(volumes[-max(config.long_window_bars, config.mid_window_bars) : -1])
    volume_ratio = (candle.volume / volume_base) if volume_base and volume_base > 0 else (1.0 if candle.volume > 0 else 0.0)
    volume_z = _zscore(candle.volume, volumes[:-1])
    short_return = _return_pct(candles, config.short_window_bars)
    mid_return = _return_pct(candles, config.mid_window_bars)
    long_return = _return_pct(candles, config.long_window_bars)
    close_location = _close_location(candle)
    lower_wick = _lower_wick_ratio(candle)
    spread_ratio = _spread_ratio(orderbooks)
    bid_depth_drop = _bid_depth_drop(orderbooks)
    bid_depth_refill = _bid_depth_refill(orderbooks, panic_baseline=panic_bid_depth_baseline)
    current_orderbook = orderbooks[-1] if orderbooks else None
    ofi_z = current_orderbook.ofi_z if current_orderbook else None
    ofi_values = [float(item.ofi_z) for item in orderbooks if item.ofi_z is not None]
    ofi_cusum = _ofi_cusum(ofi_values, direction="negative")
    qi_ewma = current_orderbook.qi_ewma if current_orderbook else None
    micro_state = current_orderbook.micro_state if current_orderbook else "missing"
    observer_healthy = current_orderbook.observer_healthy if current_orderbook else False
    orderbook_ready = current_orderbook.ready if current_orderbook else False
    recent_lows = [item.low for item in candles[-max(1, config.no_new_low_bars) :]]
    no_new_low = False
    if panic_low is not None and panic_low > 0 and recent_lows:
        tolerance = float(config.low_break_tolerance_pct) / 100.0
        no_new_low = min(recent_lows) >= panic_low * (1.0 - tolerance)
    bounce_from_low_pct = 0.0
    if panic_low is not None and panic_low > 0 and candle.close > 0:
        bounce_from_low_pct = ((candle.close / panic_low) - 1.0) * 100.0
    micro_consensus_count = sum(
        1
        for passed in (
            ofi_z is not None and float(ofi_z) <= -2.5,
            sell_ratio is not None and float(sell_ratio) >= config.sell_ratio_threshold,
            volume_ratio >= config.volume_spike_threshold,
            bid_depth_drop is not None and float(bid_depth_drop) >= config.bid_depth_drop_threshold,
            spread_ratio is not None and float(spread_ratio) >= config.spread_widen_threshold,
        )
        if passed
    )

    return {
        "short_return_pct": round(short_return, 6),
        "mid_return_pct": round(mid_return, 6),
        "long_return_pct": round(long_return, 6),
        "short_return_z": round(_zscore(current_return, recent_returns), 6),
        "downside_velocity": round(max(0.0, -short_return) / max(1, config.short_window_bars), 6),
        "downside_acceleration": round(max(0.0, -current_return), 6),
        "close_location_value": round(close_location, 6),
        "lower_wick_ratio": round(lower_wick, 6),
        "range_expansion_ratio": round((max(0.0, candle.high - candle.low) / range_baseline), 6)
        if range_baseline and range_baseline > 0
        else 1.0,
        "volume_ratio_short": round(volume_ratio, 6),
        "volume_z": round(volume_z, 6),
        "total_volume": round(candle.volume, 6),
        "sell_ratio": None if sell_ratio is None else round(sell_ratio, 6),
        "buy_ratio": None if buy_ratio is None else round(buy_ratio, 6),
        "sell_pressure_decay": bool(prev_sell_ratio is not None and sell_ratio is not None and sell_ratio < prev_sell_ratio),
        "bid_depth_drop_ratio": None if bid_depth_drop is None else round(bid_depth_drop, 6),
        "bid_depth_refill_ratio": None if bid_depth_refill is None else round(bid_depth_refill, 6),
        "spread_ratio": None if spread_ratio is None else round(spread_ratio, 6),
        "ofi_z": None if ofi_z is None else round(float(ofi_z), 6),
        "ofi_cusum_direction": ofi_cusum["direction"],
        "ofi_cusum_sample_count": ofi_cusum["sample_count"],
        "ofi_cusum_triggered": ofi_cusum["triggered"],
        "ofi_cusum_score": ofi_cusum["score"],
        "ofi_cusum_sigma": ofi_cusum["sigma"],
        "ofi_cusum_k": ofi_cusum["k"],
        "ofi_cusum_h": ofi_cusum["h"],
        "ofi_cusum_reason": ofi_cusum["reason"],
        "micro_consensus_signal_count": micro_consensus_count,
        "micro_consensus_pass": micro_consensus_count >= 2,
        "qi_ewma": None if qi_ewma is None else round(float(qi_ewma), 6),
        "orderbook_micro_state": micro_state,
        "orderbook_ready": bool(orderbook_ready),
        "orderbook_observer_healthy": bool(observer_healthy),
        "orderbook_missing": _orderbook_missing(current_orderbook),
        "no_new_low": bool(no_new_low),
        "bounce_from_low_pct": round(bounce_from_low_pct, 6),
        "panic_low_reference": panic_low,
    }


def compute_panic_score(features: dict[str, Any], config: PanicSellDetectorConfig) -> tuple[float, list[str]]:
    reasons: list[str] = []
    short_return = float(features.get("short_return_pct") or 0.0)
    mid_return = float(features.get("mid_return_pct") or 0.0)
    short_z = float(features.get("short_return_z") or 0.0)
    volume_ratio = float(features.get("volume_ratio_short") or 0.0)
    sell_ratio = features.get("sell_ratio")
    ofi_z = features.get("ofi_z")
    bid_drop = features.get("bid_depth_drop_ratio")
    spread_ratio = features.get("spread_ratio")
    clv = float(features.get("close_location_value") or 0.5)

    price_score = max(
        _clamp01((-short_return) / max(config.min_abs_drop_short_pct, 1e-9)),
        _clamp01((-mid_return) / max(config.min_abs_drop_mid_pct, 1e-9)),
        _clamp01((-short_z) / max(abs(config.return_z_panic_threshold), 1e-9)),
    )
    if short_return <= -config.min_abs_drop_short_pct:
        reasons.append("short_return_breakdown")
    if mid_return <= -config.min_abs_drop_mid_pct:
        reasons.append("mid_return_breakdown")
    if short_z <= config.return_z_panic_threshold:
        reasons.append("return_z_panic")

    volume_score = max(
        _clamp01((volume_ratio - 1.0) / max(config.volume_spike_threshold - 1.0, 1e-9)),
        _clamp01((float(features.get("volume_z") or 0.0)) / 3.0),
    )
    if volume_ratio >= config.volume_spike_threshold:
        reasons.append("volume_spike")

    trade_flow_score = 0.0
    if sell_ratio is not None:
        trade_flow_score = _clamp01((float(sell_ratio) - 0.50) / max(config.sell_ratio_threshold - 0.50, 1e-9))
        if float(sell_ratio) >= config.sell_ratio_threshold:
            reasons.append("sell_ratio_high")

    orderbook_score = 0.0
    if ofi_z is not None:
        orderbook_score = max(orderbook_score, _clamp01((-float(ofi_z)) / max(abs(config.ofi_z_panic_threshold), 1e-9)))
        if float(ofi_z) <= config.ofi_z_panic_threshold:
            reasons.append("ofi_panic")
    if bid_drop is not None:
        orderbook_score = max(orderbook_score, _clamp01(float(bid_drop) / max(config.bid_depth_drop_threshold, 1e-9)))
        if float(bid_drop) >= config.bid_depth_drop_threshold:
            reasons.append("bid_depth_drop")

    spread_score = 0.0
    if spread_ratio is not None:
        spread_score = _clamp01((float(spread_ratio) - 1.0) / max(config.spread_widen_threshold - 1.0, 1e-9))
        if float(spread_ratio) >= config.spread_widen_threshold:
            reasons.append("spread_widen")

    candle_score = _clamp01((config.close_near_low_threshold - clv) / max(config.close_near_low_threshold, 1e-9))
    if clv <= config.close_near_low_threshold:
        reasons.append("close_near_low")

    panic_score = (
        0.30 * price_score
        + 0.15 * volume_score
        + 0.20 * trade_flow_score
        + 0.20 * orderbook_score
        + 0.07 * spread_score
        + 0.08 * candle_score
    )
    if features.get("orderbook_missing"):
        if config.degrade_when_orderbook_missing:
            panic_score = min(panic_score, 0.82)
        reasons.append("orderbook_missing_degraded")
    if float(features.get("total_volume") or 0.0) < config.min_total_volume:
        panic_score = min(panic_score, 0.45)
        reasons.append("low_liquidity_score_capped")
    return round(_clamp01(panic_score), 6), reasons


def compute_recovery_score(features: dict[str, Any], config: PanicSellDetectorConfig) -> tuple[float, list[str]]:
    reasons: list[str] = []
    sell_ratio = features.get("sell_ratio")
    ofi_z = features.get("ofi_z")
    bid_refill = features.get("bid_depth_refill_ratio")
    spread_ratio = features.get("spread_ratio")
    clv = float(features.get("close_location_value") or 0.5)
    lower_wick = float(features.get("lower_wick_ratio") or 0.0)
    short_return = float(features.get("short_return_pct") or 0.0)

    no_new_low_score = 1.0 if bool(features.get("no_new_low")) else 0.0
    if no_new_low_score:
        reasons.append("no_new_low")
    velocity_easing = _clamp01(1.0 - abs(min(short_return, 0.0)) / max(config.min_abs_drop_short_pct, 1e-9))
    bounce_score = _clamp01(float(features.get("bounce_from_low_pct") or 0.0) / 1.0)
    price_stabilization_score = max(no_new_low_score, velocity_easing, bounce_score)

    flow_recovery_score = 0.0
    if sell_ratio is not None:
        flow_recovery_score = _clamp01(
            (config.sell_ratio_threshold - float(sell_ratio))
            / max(config.sell_ratio_threshold - config.sell_ratio_recovery_max, 1e-9)
        )
        if float(sell_ratio) <= config.sell_ratio_recovery_max or bool(features.get("sell_pressure_decay")):
            reasons.append("sell_pressure_easing")

    orderbook_recovery_score = 0.0
    if bid_refill is not None:
        orderbook_recovery_score = max(orderbook_recovery_score, _clamp01(float(bid_refill) / max(config.bid_depth_refill_min, 1e-9)))
        if float(bid_refill) >= config.bid_depth_refill_min:
            reasons.append("bid_depth_refill")
    if ofi_z is not None:
        orderbook_recovery_score = max(
            orderbook_recovery_score,
            _clamp01(
                (float(ofi_z) - config.ofi_z_panic_threshold)
                / max(config.ofi_z_recovery_min - config.ofi_z_panic_threshold, 1e-9)
            ),
        )
        if float(ofi_z) >= config.ofi_z_recovery_min:
            reasons.append("ofi_recovery")

    spread_normalization_score = 0.0
    if spread_ratio is not None:
        spread_normalization_score = _clamp01(
            (config.spread_widen_threshold - float(spread_ratio))
            / max(config.spread_widen_threshold - config.spread_recovery_max, 1e-9)
        )
        if float(spread_ratio) <= config.spread_recovery_max:
            reasons.append("spread_normalized")

    clv_score = _clamp01(clv / max(config.close_location_recovery_min, 1e-9))
    wick_score = _clamp01(lower_wick / 0.45)
    candle_reversal_score = max(clv_score, wick_score)
    if clv >= config.close_location_recovery_min:
        reasons.append("close_location_recovery")

    vwap_reclaim_score = 1.0 if bool(features.get("panic_anchored_vwap_reclaim")) else 0.0
    if vwap_reclaim_score:
        reasons.append("panic_anchored_vwap_reclaim")

    recovery_score = (
        0.25 * price_stabilization_score
        + 0.20 * flow_recovery_score
        + 0.20 * orderbook_recovery_score
        + 0.10 * spread_normalization_score
        + 0.15 * candle_reversal_score
        + 0.10 * vwap_reclaim_score
    )
    if bid_refill is not None and spread_ratio is not None and float(bid_refill) < 0.45 and float(spread_ratio) > 1.5:
        recovery_score *= 0.75
        reasons.append("recovery_blocked_by_unstable_microstructure")
    if bid_refill is not None and sell_ratio is not None:
        if float(bid_refill) >= config.bid_depth_refill_min and float(sell_ratio) >= config.sell_ratio_threshold:
            recovery_score *= 0.85
            reasons.append("bid_refill_but_sell_flow_still_dominant")
    return round(_clamp01(recovery_score), 6), reasons


def _report_state(internal_state: PanicInternalState) -> str:
    if internal_state in {PanicInternalState.PANIC_CANDIDATE, PanicInternalState.PANIC_ACTIVE}:
        return REPORT_PANIC_SELL
    if internal_state == PanicInternalState.RECOVERY_CANDIDATE:
        return REPORT_RECOVERY_WATCH
    if internal_state in {PanicInternalState.RECOVERED, PanicInternalState.COOLDOWN}:
        return REPORT_RECOVERY_CONFIRMED
    return REPORT_NORMAL


class PanicSellStateDetector:
    def __init__(self, config: PanicSellDetectorConfig | None = None) -> None:
        self.config = config or PanicSellDetectorConfig()
        self.state = PanicInternalState.NORMAL
        self.bars_in_state = 0
        self.panic_start_ts: datetime | None = None
        self.panic_low: float | None = None
        self.panic_bid_depth_baseline: float | None = None
        self.max_panic_score = 0.0
        self.recent_panic_scores: deque[float] = deque(maxlen=max(1, self.config.panic_entry_confirm_window))
        self.recent_recovery_scores: deque[float] = deque(maxlen=max(1, self.config.recovery_confirm_window))
        self.cooldown_remaining = 0
        self._candles: list[PanicCandle] = []
        self._trades: list[PanicTradeFlow] = []
        self._orderbooks: list[PanicOrderbookMicro] = []
        self._panic_vwap_value = 0.0
        self._panic_vwap_volume = 0.0

    def update(
        self,
        candle: PanicCandle,
        trade_flow: PanicTradeFlow | None = None,
        orderbook_micro: PanicOrderbookMicro | None = None,
    ) -> PanicSignal:
        self._candles.append(candle)
        self._candles = self._candles[-max(self.config.long_window_bars, self.config.mid_window_bars, 10) :]
        if trade_flow is not None:
            self._trades.append(trade_flow)
            self._trades = self._trades[-max(self.config.long_window_bars, 10) :]
        current_orderbook = orderbook_micro or PanicOrderbookMicro(
            ts=candle.ts,
            micro_state="missing",
            ready=False,
            observer_healthy=False,
        )
        self._orderbooks.append(current_orderbook)
        self._orderbooks = self._orderbooks[-max(self.config.long_window_bars, 10) :]

        if len(self._candles) < max(2, self.config.min_bars_required):
            return self._build_signal(
                panic_score=0.0,
                recovery_score=0.0,
                reasons=["insufficient_data"],
                metrics={"bar_count": len(self._candles)},
                panic_entered=False,
                previous_state=self.state,
            )

        features = compute_panic_features(
            self._candles,
            self._trades,
            self._orderbooks,
            config=self.config,
            panic_low=self.panic_low,
            panic_bid_depth_baseline=self.panic_bid_depth_baseline,
        )
        if self._panic_vwap_volume > 0:
            panic_anchored_vwap = self._panic_vwap_value / self._panic_vwap_volume
            features["panic_anchored_vwap"] = round(panic_anchored_vwap, 6)
            features["panic_anchored_vwap_reclaim"] = candle.close >= panic_anchored_vwap
        else:
            features["panic_anchored_vwap"] = None
            features["panic_anchored_vwap_reclaim"] = False

        panic_score, panic_reasons = compute_panic_score(features, self.config)
        recovery_score, recovery_reasons = compute_recovery_score(features, self.config)
        self.recent_panic_scores.append(panic_score)
        self.recent_recovery_scores.append(recovery_score)

        previous_state = self.state
        panic_entered = False
        price_breakdown = (
            float(features["short_return_pct"]) <= -self.config.min_abs_drop_short_pct
            or float(features["mid_return_pct"]) <= -self.config.min_abs_drop_mid_pct
            or float(features["short_return_z"]) <= self.config.return_z_panic_threshold
        )
        flow_confirmation = (
            float(features.get("volume_ratio_short") or 0.0) >= self.config.volume_spike_threshold
            or (features.get("sell_ratio") is not None and float(features["sell_ratio"]) >= self.config.sell_ratio_threshold)
            or (features.get("ofi_z") is not None and float(features["ofi_z"]) <= self.config.ofi_z_panic_threshold)
        )
        panic_candidate = price_breakdown and flow_confirmation and panic_score >= self.config.panic_entry_score_threshold
        low_break = self._panic_low_broken(candle.low)
        recovery_candidate = self._recovery_candidate(features, recovery_score)
        panic_resumed = low_break or panic_candidate

        if self.state == PanicInternalState.NORMAL:
            if panic_candidate:
                self._transition(PanicInternalState.PANIC_CANDIDATE)
        elif self.state == PanicInternalState.PANIC_CANDIDATE:
            if self._confirm_panic_entry():
                self._transition(PanicInternalState.PANIC_ACTIVE)
                self._initialize_panic_tracking(candle)
                panic_entered = True
            elif not panic_candidate and panic_score < self.config.panic_entry_score_threshold * 0.80:
                self._transition(PanicInternalState.NORMAL)
        elif self.state == PanicInternalState.PANIC_ACTIVE:
            self._update_panic_tracking(candle, orderbook_micro)
            if recovery_candidate:
                self._transition(PanicInternalState.RECOVERY_CANDIDATE)
            elif self.bars_in_state >= self.config.max_panic_active_bars:
                self._transition(PanicInternalState.COOLDOWN)
                self.cooldown_remaining = self.config.cooldown_bars
        elif self.state == PanicInternalState.RECOVERY_CANDIDATE:
            self._update_panic_tracking(candle, orderbook_micro)
            if panic_resumed:
                self._transition(PanicInternalState.PANIC_ACTIVE)
            elif self._confirm_recovery():
                self._transition(PanicInternalState.RECOVERED)
        elif self.state == PanicInternalState.RECOVERED:
            self.cooldown_remaining = self.config.cooldown_bars
            self._transition(PanicInternalState.COOLDOWN)
        elif self.state == PanicInternalState.COOLDOWN:
            self.cooldown_remaining = max(0, self.cooldown_remaining - 1)
            if self.cooldown_remaining <= 0:
                self._reset_panic_tracking()
                self._transition(PanicInternalState.NORMAL)

        self.max_panic_score = max(self.max_panic_score, panic_score)
        reasons = list(dict.fromkeys(panic_reasons + recovery_reasons))
        if self.state == PanicInternalState.COOLDOWN:
            reasons.append("cooldown_active")
        return self._build_signal(
            panic_score=panic_score,
            recovery_score=recovery_score,
            reasons=reasons,
            metrics={**features, "panic_score": panic_score, "recovery_score": recovery_score},
            panic_entered=panic_entered,
            previous_state=previous_state,
        )

    def _transition(self, state: PanicInternalState) -> None:
        if state != self.state:
            self.state = state
            self.bars_in_state = 0
        else:
            self.bars_in_state += 1

    def _confirm_panic_entry(self) -> bool:
        return sum(1 for score in self.recent_panic_scores if score >= self.config.panic_entry_score_threshold) >= self.config.panic_entry_confirm_bars

    def _confirm_recovery(self) -> bool:
        return (
            sum(1 for score in self.recent_recovery_scores if score >= self.config.recovery_score_threshold)
            >= self.config.recovery_confirm_bars
        )

    def _panic_low_broken(self, current_low: float) -> bool:
        if self.panic_low is None or self.panic_low <= 0 or current_low <= 0:
            return False
        tolerance = float(self.config.low_break_tolerance_pct) / 100.0
        return current_low < self.panic_low * (1.0 - tolerance)

    def _recovery_candidate(self, features: dict[str, Any], recovery_score: float) -> bool:
        if recovery_score < self.config.recovery_score_threshold:
            return False
        if not bool(features.get("no_new_low")):
            return False
        sell_ratio = features.get("sell_ratio")
        if sell_ratio is not None and float(sell_ratio) > self.config.sell_ratio_threshold:
            return False
        ofi_ok = features.get("ofi_z") is not None and float(features["ofi_z"]) >= self.config.ofi_z_recovery_min
        depth_ok = (
            features.get("bid_depth_refill_ratio") is not None
            and float(features["bid_depth_refill_ratio"]) >= self.config.bid_depth_refill_min
        )
        if not (ofi_ok or depth_ok):
            return False
        spread_ratio = features.get("spread_ratio")
        if spread_ratio is not None and float(spread_ratio) > self.config.spread_widen_threshold:
            return False
        return True

    def _initialize_panic_tracking(self, candle: PanicCandle) -> None:
        self.panic_start_ts = candle.ts
        self.panic_low = candle.low
        self._panic_vwap_value = 0.0
        self._panic_vwap_volume = 0.0
        self._update_panic_tracking(candle, self._orderbooks[-1] if self._orderbooks else None)

    def _update_panic_tracking(self, candle: PanicCandle, orderbook_micro: PanicOrderbookMicro | None) -> None:
        self.panic_low = candle.low if self.panic_low is None else min(self.panic_low, candle.low)
        price_for_vwap = candle.vwap if candle.vwap and candle.vwap > 0 else candle.close
        if candle.volume > 0 and price_for_vwap > 0:
            self._panic_vwap_value += price_for_vwap * candle.volume
            self._panic_vwap_volume += candle.volume
        if self.panic_bid_depth_baseline is None and orderbook_micro is not None and orderbook_micro.bid_depth_l5:
            self.panic_bid_depth_baseline = float(orderbook_micro.bid_depth_l5)

    def _reset_panic_tracking(self) -> None:
        self.panic_start_ts = None
        self.panic_low = None
        self.panic_bid_depth_baseline = None
        self.max_panic_score = 0.0
        self._panic_vwap_value = 0.0
        self._panic_vwap_volume = 0.0
        self.recent_panic_scores.clear()
        self.recent_recovery_scores.clear()

    def _build_signal(
        self,
        *,
        panic_score: float,
        recovery_score: float,
        reasons: list[str],
        metrics: dict[str, Any],
        panic_entered: bool,
        previous_state: PanicInternalState,
    ) -> PanicSignal:
        report_state = _report_state(self.state)
        risk_off = self.state in {
            PanicInternalState.PANIC_CANDIDATE,
            PanicInternalState.PANIC_ACTIVE,
            PanicInternalState.RECOVERY_CANDIDATE,
            PanicInternalState.COOLDOWN,
        }
        allow_new_long = not risk_off
        if self.state == PanicInternalState.RECOVERY_CANDIDATE and not self.config.block_long_during_recovery_candidate:
            allow_new_long = True
        confidence = 0.5
        if metrics.get("sell_ratio") is not None:
            confidence += 0.2
        if not metrics.get("orderbook_missing"):
            confidence += 0.3
        confidence = round(min(1.0, confidence), 6)
        severity = "LOW"
        if panic_score >= 0.90:
            severity = "EXTREME"
        elif panic_score >= 0.80:
            severity = "HIGH"
        elif panic_score >= self.config.panic_entry_score_threshold:
            severity = "MEDIUM"
        return PanicSignal(
            state=report_state,
            internal_state=self.state.value,
            panic_score=round(float(panic_score), 6),
            recovery_score=round(float(recovery_score), 6),
            panic_active=self.state
            in {PanicInternalState.PANIC_CANDIDATE, PanicInternalState.PANIC_ACTIVE, PanicInternalState.RECOVERY_CANDIDATE},
            panic_entered=bool(panic_entered or (previous_state != PanicInternalState.PANIC_ACTIVE and self.state == PanicInternalState.PANIC_ACTIVE)),
            recovery_candidate=self.state == PanicInternalState.RECOVERY_CANDIDATE,
            recovery_confirmed=self.state == PanicInternalState.RECOVERED,
            risk_off=bool(risk_off),
            risk_off_advisory=bool(risk_off),
            allow_new_long=bool(allow_new_long),
            allow_new_long_advisory=bool(allow_new_long),
            confidence=confidence,
            severity=severity,
            panic_low=None if self.panic_low is None else round(float(self.panic_low), 6),
            panic_start_ts=self.panic_start_ts.isoformat(timespec="seconds") if self.panic_start_ts else None,
            cooldown_remaining=int(self.cooldown_remaining),
            reasons=list(dict.fromkeys(reasons)),
            metrics=metrics,
        )


def _field(fields: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in fields and fields.get(name) not in (None, "", "-"):
            return fields.get(name)
    return None


def candle_from_event(row: dict[str, Any]) -> PanicCandle | None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    ts = _parse_dt(row.get("emitted_at"))
    if ts is None:
        return None
    close = _safe_float(
        _field(
            fields,
            "curr_price",
            "current_price",
            "latest_price",
            "last_price",
            "order_price",
            "sell_price",
            "buy_price",
            "signal_price",
            "price",
        )
    )
    if close is None or close <= 0:
        return None
    open_value = _safe_float(_field(fields, "open", "open_price", "candle_open"), close) or close
    high = _safe_float(_field(fields, "high", "high_price", "candle_high"), max(open_value, close)) or max(open_value, close)
    low = _safe_float(_field(fields, "low", "low_price", "candle_low"), min(open_value, close)) or min(open_value, close)
    volume = _safe_float(_field(fields, "volume", "today_vol", "trade_volume", "total_volume"), None)
    if volume is None:
        buy_volume = _safe_float(_field(fields, "buy_exec_volume", "buy_volume"), 0.0) or 0.0
        sell_volume = _safe_float(_field(fields, "sell_exec_volume", "sell_volume"), 0.0) or 0.0
        volume = buy_volume + sell_volume
    vwap = _safe_float(_field(fields, "vwap", "vwap_price", "panic_anchored_vwap"), None)
    return PanicCandle(ts=ts, open=open_value, high=max(high, low, close), low=min(low, high, close), close=close, volume=max(0.0, volume or 0.0), vwap=vwap)


def trade_flow_from_event(row: dict[str, Any]) -> PanicTradeFlow | None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    ts = _parse_dt(row.get("emitted_at"))
    if ts is None:
        return None
    buy_volume = _safe_float(_field(fields, "buy_exec_volume", "buy_volume"), None)
    sell_volume = _safe_float(_field(fields, "sell_exec_volume", "sell_volume"), None)
    total_volume = _safe_float(_field(fields, "total_volume", "volume", "today_vol"), None)
    if (buy_volume is None or sell_volume is None) and total_volume is not None and total_volume > 0:
        buy_ratio = _safe_float(_field(fields, "exec_buy_ratio", "buy_ratio", "buy_ratio_ws"), None)
        if buy_ratio is not None:
            ratio = buy_ratio / 100.0 if buy_ratio > 1.0 else buy_ratio
            buy_volume = total_volume * _clamp01(ratio)
            sell_volume = total_volume - buy_volume
    if buy_volume is None and sell_volume is None:
        return None
    return PanicTradeFlow(ts=ts, buy_volume=max(0.0, buy_volume or 0.0), sell_volume=max(0.0, sell_volume or 0.0))


def orderbook_micro_from_event(row: dict[str, Any]) -> PanicOrderbookMicro | None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    ts = _parse_dt(row.get("emitted_at"))
    if ts is None:
        return None
    best_bid = _safe_float(_field(fields, "best_bid", "bid_price"), None)
    best_ask = _safe_float(_field(fields, "best_ask", "ask_price"), None)
    ofi_z = _safe_float(_field(fields, "orderbook_micro_ofi_z", "ofi_z"), None)
    qi_ewma = _safe_float(_field(fields, "orderbook_micro_qi_ewma", "qi_ewma"), None)
    spread_ratio = _safe_float(_field(fields, "panic_spread_ratio", "micro_spread_ratio"), None)
    if spread_ratio is None:
        raw_spread_ratio = _safe_float(_field(fields, "spread_ratio"), None)
        if raw_spread_ratio is not None and raw_spread_ratio >= 1.0:
            spread_ratio = raw_spread_ratio
    bid_depth = _safe_float(_field(fields, "bid_depth_l5", "bid_tot", "net_bid_depth"), None)
    ask_depth = _safe_float(_field(fields, "ask_depth_l5", "ask_tot", "net_ask_depth"), None)
    bid_drop = _safe_float(_field(fields, "bid_depth_drop_ratio"), None)
    bid_refill = _safe_float(_field(fields, "bid_depth_refill_ratio"), None)
    micro_state = str(_field(fields, "orderbook_micro_state", "micro_state") or "missing")
    ready = _safe_bool(_field(fields, "orderbook_micro_ready", "orderbook_ready"), default=False)
    healthy = _safe_bool(_field(fields, "orderbook_micro_observer_healthy", "orderbook_observer_healthy"), default=False)
    has_orderbook_signal = any(
        value is not None
        for value in (best_bid, best_ask, ofi_z, qi_ewma, spread_ratio, bid_depth, ask_depth, bid_drop, bid_refill)
    ) or micro_state not in {"", "missing"}
    if not has_orderbook_signal:
        return None
    return PanicOrderbookMicro(
        ts=ts,
        best_bid=best_bid,
        best_ask=best_ask,
        bid_depth_l5=bid_depth,
        ask_depth_l5=ask_depth,
        spread_ratio=spread_ratio,
        bid_depth_drop_ratio=bid_drop,
        bid_depth_refill_ratio=bid_refill,
        ofi_z=ofi_z,
        qi_ewma=qi_ewma,
        micro_state=micro_state,
        ready=ready,
        observer_healthy=healthy,
    )


def summarize_microstructure_detector_from_events(
    events: list[dict[str, Any]],
    *,
    as_of: datetime | None = None,
    config: PanicSellDetectorConfig | None = None,
    max_symbols: int = 20,
) -> dict[str, Any]:
    cfg = config or PanicSellDetectorConfig()
    grouped: dict[str, list[dict[str, Any]]] = {}
    names: dict[str, str] = {}
    for row in events:
        event_ts = _parse_dt(row.get("emitted_at"))
        if as_of is not None and event_ts is not None and event_ts > as_of:
            continue
        code = str(row.get("stock_code") or "").strip()[:6]
        if not code:
            continue
        if candle_from_event(row) is None:
            continue
        grouped.setdefault(code, []).append(row)
        names[code] = str(row.get("stock_name") or code)

    symbol_signals: list[PanicSymbolSignal] = []
    reason_counter: Counter[str] = Counter()
    state_counter: Counter[str] = Counter()
    missing_orderbook = 0
    degraded_orderbook = 0
    for code, rows in grouped.items():
        detector = PanicSellStateDetector(cfg)
        latest_signal: PanicSignal | None = None
        latest_ts: str | None = None
        for row in sorted(rows, key=lambda item: str(item.get("emitted_at") or "")):
            candle = candle_from_event(row)
            if candle is None:
                continue
            latest_ts = candle.ts.isoformat(timespec="seconds")
            latest_signal = detector.update(
                candle,
                trade_flow=trade_flow_from_event(row),
                orderbook_micro=orderbook_micro_from_event(row),
            )
        if latest_signal is None:
            continue
        symbol_signals.append(
            PanicSymbolSignal(
                stock_code=code,
                stock_name=names.get(code, code),
                signal=latest_signal,
                latest_event_at=latest_ts,
            )
        )
        reason_counter.update(latest_signal.reasons)
        state_counter.update([latest_signal.state])
        if latest_signal.metrics.get("orderbook_missing"):
            missing_orderbook += 1
        if "orderbook_missing_degraded" in latest_signal.reasons:
            degraded_orderbook += 1

    ordered = sorted(
        symbol_signals,
        key=lambda item: (
            bool(item.signal.risk_off_advisory),
            float(item.signal.panic_score),
            float(item.signal.recovery_score),
        ),
        reverse=True,
    )
    risk_off_count = sum(1 for item in symbol_signals if item.signal.risk_off_advisory)
    allow_false_count = sum(1 for item in symbol_signals if not item.signal.allow_new_long_advisory)
    panic_scores = [item.signal.panic_score for item in symbol_signals]
    recovery_scores = [item.signal.recovery_score for item in symbol_signals]
    cusum_triggered = [
        item
        for item in symbol_signals
        if bool(item.signal.metrics.get("ofi_cusum_triggered"))
    ]
    cusum_scores = [
        float(item.signal.metrics.get("ofi_cusum_score") or 0.0)
        for item in symbol_signals
    ]
    consensus_passed = [
        item
        for item in symbol_signals
        if bool(item.signal.metrics.get("micro_consensus_pass"))
    ]
    return {
        "schema_version": 1,
        "policy": {
            "report_only": True,
            "runtime_effect": "report_only_no_mutation",
            "live_runtime_effect": False,
            "advisory_only": True,
            "does_not_submit_orders": True,
        },
        "threshold_mode": "static_fallback",
        "threshold_sample_ready": len(symbol_signals) >= 4,
        "threshold_contract": {
            "decision_authority": "source_quality_only",
            "runtime_effect": "report_only_no_mutation",
            "threshold_mode": "static_fallback",
            "threshold_sample_ready": len(symbol_signals) >= 4,
            "threshold_source": "PanicSellDetectorConfig fallback defaults; report-only microstructure evidence",
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "auto_sell",
                "bot_restart",
                "provider_route_change",
            ],
        },
        "evaluated_symbol_count": len(symbol_signals),
        "risk_off_advisory_count": risk_off_count,
        "allow_new_long_false_count": allow_false_count,
        "panic_signal_count": sum(1 for item in symbol_signals if item.signal.state == REPORT_PANIC_SELL),
        "recovery_candidate_count": sum(1 for item in symbol_signals if item.signal.recovery_candidate),
        "recovery_confirmed_count": sum(1 for item in symbol_signals if item.signal.recovery_confirmed),
        "missing_orderbook_count": missing_orderbook,
        "degraded_orderbook_count": degraded_orderbook,
        "state_counts": dict(sorted(state_counter.items())),
        "top_reasons": [{"reason": key, "count": value} for key, value in reason_counter.most_common(12)],
        "micro_cusum_observer": {
            "metric_role": "source_quality_gate",
            "decision_authority": "source_quality_only",
            "window_policy": "intraday_observe_only",
            "sample_floor": 4,
            "primary_decision_metric": None,
            "source_quality_gate": "requires timestamp-ordered orderbook_micro_ofi_z samples per symbol",
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "auto_sell",
                "bot_restart",
                "provider_route_change",
            ],
            "ofi_direction": "negative",
            "triggered_symbol_count": len(cusum_triggered),
            "consensus_pass_symbol_count": len(consensus_passed),
            "max_ofi_cusum_score": round(max(cusum_scores), 6) if cusum_scores else 0.0,
        },
        "metrics": {
            "max_panic_score": round(max(panic_scores), 6) if panic_scores else 0.0,
            "max_recovery_score": round(max(recovery_scores), 6) if recovery_scores else 0.0,
            "avg_panic_score": round(sum(panic_scores) / len(panic_scores), 6) if panic_scores else 0.0,
            "avg_recovery_score": round(sum(recovery_scores) / len(recovery_scores), 6) if recovery_scores else 0.0,
        },
        "latest_signals": [item.to_dict() for item in ordered[:max_symbols]],
    }
