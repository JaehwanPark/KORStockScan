"""Report-only panic buying microstructure state detector.

This module is intentionally detached from broker order paths. It produces
advisory runner/TP flags and evidence that panic_buying_report can surface in
reports.
"""

from __future__ import annotations

import math
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

REPORT_NORMAL = "NORMAL"
REPORT_PANIC_BUY_WATCH = "PANIC_BUY_WATCH"
REPORT_PANIC_BUY = "PANIC_BUY"
REPORT_EXHAUSTION_WATCH = "EXHAUSTION_WATCH"
REPORT_BUYING_EXHAUSTED = "BUYING_EXHAUSTED"


class PanicBuyingInternalState(str, Enum):
    NORMAL = "NORMAL"
    PANIC_BUY_CANDIDATE = "PANIC_BUY_CANDIDATE"
    PANIC_BUY_ACTIVE = "PANIC_BUY_ACTIVE"
    BUYING_EXHAUSTION_CANDIDATE = "BUYING_EXHAUSTION_CANDIDATE"
    BUYING_EXHAUSTED = "BUYING_EXHAUSTED"
    COOLDOWN = "COOLDOWN"


@dataclass(frozen=True)
class PanicBuyingDetectorConfig:
    short_window_bars: int = 3
    mid_window_bars: int = 6
    long_window_bars: int = 30
    min_bars_required: int = 3
    min_total_volume: float = 1.0

    panic_buy_entry_score_threshold: float = 0.72
    panic_buy_confirm_bars: int = 2
    panic_buy_confirm_window: int = 3
    min_abs_rise_short_pct: float = 1.2
    min_abs_rise_mid_pct: float = 2.5
    return_z_panic_buy_threshold: float = 2.2
    volume_spike_threshold: float = 2.8
    buy_ratio_threshold: float = 0.64
    cvd_slope_buy_threshold: float = 2.0
    ofi_z_panic_buy_threshold: float = 2.0
    ask_depth_drop_threshold: float = 0.35
    bid_depth_support_threshold: float = 1.15
    spread_widen_threshold: float = 1.8
    close_near_high_threshold: float = 0.75
    range_expansion_threshold: float = 1.5

    exhaustion_score_threshold: float = 0.66
    exhaustion_confirm_bars: int = 2
    exhaustion_confirm_window: int = 4
    no_new_high_bars: int = 3
    high_break_tolerance_pct: float = 0.15
    buy_ratio_exhaustion_max: float = 0.58
    cvd_slope_exhaustion_max: float = 0.4
    ofi_z_exhaustion_max: float = 0.3
    ask_depth_refill_min: float = 0.70
    failed_ask_sweep_threshold: int = 2
    upper_wick_exhaustion_min: float = 0.45
    close_location_exhaustion_max: float = 0.45
    price_progress_exhaustion_max: float = 0.35
    vwap_extension_extreme_pct: float = 3.0
    atr_extension_extreme: float = 2.5

    max_panic_buy_active_bars: int = 60
    cooldown_bars: int = 12
    degrade_when_orderbook_missing: bool = True
    degrade_when_trade_aggressor_missing: bool = True


def _detector_threshold_contract(
    config: PanicBuyingDetectorConfig, *, sample_count: int
) -> dict[str, Any]:
    return {
        "threshold_mode": "static_fallback",
        "threshold_sample_ready": sample_count >= max(1, config.min_bars_required),
        "decision_authority": "source_quality_only",
        "runtime_effect": "report_only_no_mutation",
        "static_fallback_values": {
            "panic_buy_entry_score_threshold": config.panic_buy_entry_score_threshold,
            "panic_buy_confirm_bars": config.panic_buy_confirm_bars,
            "panic_buy_confirm_window": config.panic_buy_confirm_window,
            "min_abs_rise_short_pct": config.min_abs_rise_short_pct,
            "min_abs_rise_mid_pct": config.min_abs_rise_mid_pct,
            "return_z_panic_buy_threshold": config.return_z_panic_buy_threshold,
            "volume_spike_threshold": config.volume_spike_threshold,
            "buy_ratio_threshold": config.buy_ratio_threshold,
            "ofi_z_panic_buy_threshold": config.ofi_z_panic_buy_threshold,
            "ask_depth_drop_threshold": config.ask_depth_drop_threshold,
            "spread_widen_threshold": config.spread_widen_threshold,
            "exhaustion_score_threshold": config.exhaustion_score_threshold,
            "buy_ratio_exhaustion_max": config.buy_ratio_exhaustion_max,
            "ofi_z_exhaustion_max": config.ofi_z_exhaustion_max,
        },
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "auto_sell",
            "auto_buy",
            "bot_restart",
            "provider_route_change",
        ],
    }


@dataclass(frozen=True)
class PanicBuyingCandle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None = None


@dataclass(frozen=True)
class PanicBuyingTradeFlow:
    ts: datetime
    buy_volume: float
    sell_volume: float
    unknown_volume: float = 0.0

    @property
    def total_volume(self) -> float:
        return self.buy_volume + self.sell_volume + self.unknown_volume


@dataclass(frozen=True)
class PanicBuyingOrderbookMicro:
    ts: datetime
    best_bid: float | None = None
    best_ask: float | None = None
    bid_depth_l5: float | None = None
    ask_depth_l5: float | None = None
    spread_ratio: float | None = None
    ask_depth_drop_ratio: float | None = None
    ask_depth_refill_ratio: float | None = None
    bid_depth_support_ratio: float | None = None
    ofi_z: float | None = None
    qi_ewma: float | None = None
    micro_state: str = "missing"
    ready: bool = False
    observer_healthy: bool = False


@dataclass(frozen=True)
class PanicBuyingSignal:
    state: str
    internal_state: str
    panic_buy_score: float
    exhaustion_score: float
    panic_buy_active: bool
    panic_buy_entered: bool
    exhaustion_candidate: bool
    exhaustion_confirmed: bool
    allow_tp_override: bool
    allow_runner: bool
    tighten_trailing_stop: bool
    force_exit_runner: bool
    confidence: float
    severity: str
    panic_buy_high: float | None = None
    panic_buy_start_ts: str | None = None
    cooldown_remaining: int = 0
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PanicBuyingSymbolSignal:
    stock_code: str
    stock_name: str
    signal: PanicBuyingSignal
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
        result = float(
            str(value).replace("%", "").replace("+", "").replace(",", "").strip()
        )
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


def _age_seconds(current: datetime, previous: datetime | None) -> float | None:
    if previous is None:
        return None
    return (current - previous).total_seconds()


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


def _return_pct(candles: list[PanicBuyingCandle], bars: int) -> float:
    if len(candles) < 2:
        return 0.0
    idx = max(0, len(candles) - 1 - max(1, int(bars)))
    base = candles[idx].close
    close = candles[-1].close
    if base <= 0 or close <= 0:
        return 0.0
    return ((close / base) - 1.0) * 100.0


def _close_location(candle: PanicBuyingCandle) -> float:
    if candle.high > candle.low:
        return _clamp01((candle.close - candle.low) / (candle.high - candle.low))
    return 0.5


def _upper_wick_ratio(candle: PanicBuyingCandle) -> float:
    candle_range = candle.high - candle.low
    if candle_range <= 0:
        return 0.0
    upper_wick = candle.high - max(candle.open, candle.close)
    return _clamp01(upper_wick / candle_range)


def _trade_ratios(
    trades: list[PanicBuyingTradeFlow],
) -> tuple[float | None, float | None]:
    if not trades:
        return None, None
    current = trades[-1]
    total = current.total_volume
    if total <= 0:
        return None, None
    return current.buy_volume / total, current.sell_volume / total


def _spread_ratio(orderbooks: list[PanicBuyingOrderbookMicro]) -> float | None:
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
        if item.best_bid is not None
        and item.best_ask is not None
        and float(item.best_ask) > 0
    ]
    baseline = _avg(previous_spreads)
    if baseline is None or baseline <= 0:
        return 1.0 if spread > 0 else 0.0
    return spread / baseline


def _ask_depth_drop(orderbooks: list[PanicBuyingOrderbookMicro]) -> float | None:
    if not orderbooks:
        return None
    current = orderbooks[-1]
    if current.ask_depth_drop_ratio is not None:
        return current.ask_depth_drop_ratio
    if current.ask_depth_l5 is None:
        return None
    baseline = _avg(
        float(item.ask_depth_l5)
        for item in orderbooks[:-1]
        if item.ask_depth_l5 is not None and float(item.ask_depth_l5) > 0
    )
    if baseline is None or baseline <= 0:
        return 0.0
    return max(0.0, 1.0 - (float(current.ask_depth_l5) / baseline))


def _ask_depth_refill(
    orderbooks: list[PanicBuyingOrderbookMicro], panic_baseline: float | None = None
) -> float | None:
    if not orderbooks:
        return None
    current = orderbooks[-1]
    if current.ask_depth_refill_ratio is not None:
        return current.ask_depth_refill_ratio
    if current.ask_depth_l5 is None:
        return None
    baseline = panic_baseline
    if baseline is None or baseline <= 0:
        baseline = _avg(
            float(item.ask_depth_l5)
            for item in orderbooks[:-1]
            if item.ask_depth_l5 is not None and float(item.ask_depth_l5) > 0
        )
    if baseline is None or baseline <= 0:
        return 0.0
    return max(0.0, float(current.ask_depth_l5) / float(baseline))


def _bid_depth_support(orderbooks: list[PanicBuyingOrderbookMicro]) -> float | None:
    if not orderbooks:
        return None
    current = orderbooks[-1]
    if current.bid_depth_support_ratio is not None:
        return current.bid_depth_support_ratio
    if current.bid_depth_l5 is None:
        return None
    baseline = _avg(
        float(item.bid_depth_l5)
        for item in orderbooks[:-1]
        if item.bid_depth_l5 is not None and float(item.bid_depth_l5) > 0
    )
    if baseline is None or baseline <= 0:
        return 1.0
    return max(0.0, float(current.bid_depth_l5) / baseline)


def _orderbook_missing(orderbook: PanicBuyingOrderbookMicro | None) -> bool:
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
            orderbook.ask_depth_drop_ratio,
            orderbook.ask_depth_refill_ratio,
            orderbook.bid_depth_support_ratio,
            orderbook.ofi_z,
            orderbook.qi_ewma,
        )
    )


def compute_panic_buying_features(
    candles: list[PanicBuyingCandle],
    trades: list[PanicBuyingTradeFlow] | None,
    orderbooks: list[PanicBuyingOrderbookMicro] | None,
    *,
    config: PanicBuyingDetectorConfig,
    panic_buy_high: float | None = None,
    panic_ask_depth_baseline: float | None = None,
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
    prev_return = close_returns[-2] if len(close_returns) >= 2 else current_return
    recent_returns = close_returns[-max(config.long_window_bars, 3) : -1]
    ranges = [max(0.0, item.high - item.low) for item in candles[:-1]]
    range_baseline = _avg(ranges[-max(1, config.mid_window_bars) :])
    volumes = [max(0.0, item.volume) for item in candles]
    volume_base = _avg(
        volumes[-max(config.long_window_bars, config.mid_window_bars) : -1]
    )
    volume_ratio = (
        (candle.volume / volume_base)
        if volume_base and volume_base > 0
        else (1.0 if candle.volume > 0 else 0.0)
    )
    buy_ratio, sell_ratio = _trade_ratios(trades)
    cvd_values: list[float] = []
    running_cvd = 0.0
    for trade in trades:
        running_cvd += trade.buy_volume - trade.sell_volume
        cvd_values.append(running_cvd)
    cvd_delta = (trades[-1].buy_volume - trades[-1].sell_volume) if trades else None
    cvd_slope = 0.0
    if len(cvd_values) >= 2:
        cvd_slope = (
            cvd_values[-1]
            - cvd_values[max(0, len(cvd_values) - 1 - config.short_window_bars)]
        )
    cvd_step_history = [
        cvd_values[idx] - cvd_values[idx - 1] for idx in range(1, len(cvd_values))
    ]
    cvd_slope_z = (
        _zscore(cvd_slope, cvd_step_history[:-1]) if len(cvd_step_history) >= 4 else 0.0
    )
    prev_buy_ratio = None
    if len(trades) >= 2 and trades[-2].total_volume > 0:
        prev_buy_ratio = trades[-2].buy_volume / trades[-2].total_volume

    close_location = _close_location(candle)
    upper_wick = _upper_wick_ratio(candle)
    spread_ratio = _spread_ratio(orderbooks)
    ask_drop = _ask_depth_drop(orderbooks)
    ask_refill = _ask_depth_refill(orderbooks, panic_baseline=panic_ask_depth_baseline)
    bid_support = _bid_depth_support(orderbooks)
    current_orderbook = orderbooks[-1] if orderbooks else None
    ofi_z = current_orderbook.ofi_z if current_orderbook else None
    ofi_values = [float(item.ofi_z) for item in orderbooks if item.ofi_z is not None]
    ofi_cusum = _ofi_cusum(ofi_values, direction="positive")
    qi_ewma = current_orderbook.qi_ewma if current_orderbook else None
    micro_state = current_orderbook.micro_state if current_orderbook else "missing"
    observer_healthy = (
        current_orderbook.observer_healthy if current_orderbook else False
    )
    orderbook_ready = current_orderbook.ready if current_orderbook else False
    recent_highs = [item.high for item in candles[-max(1, config.no_new_high_bars) :]]
    no_new_high = False
    if panic_buy_high is not None and panic_buy_high > 0 and recent_highs:
        tolerance = float(config.high_break_tolerance_pct) / 100.0
        no_new_high = max(recent_highs) <= panic_buy_high * (1.0 + tolerance)
    breakout_distance_pct = 0.0
    if panic_buy_high is not None and panic_buy_high > 0 and candle.close > 0:
        breakout_distance_pct = ((candle.close / panic_buy_high) - 1.0) * 100.0
    candle_range = max(0.0, candle.high - candle.low)
    price_progress_ratio = (
        abs(candle.close - candles[-2].close) / candle_range
        if len(candles) >= 2 and candle_range > 0
        else 1.0
    )
    vwap_extension_pct = (
        ((candle.close / candle.vwap) - 1.0) * 100.0
        if candle.vwap and candle.vwap > 0
        else 0.0
    )
    atr_base = _avg(ranges[-max(1, config.long_window_bars) :])
    atr_extension = (
        abs(candle.close - (candle.vwap or candle.close)) / atr_base
        if atr_base and atr_base > 0
        else 0.0
    )
    micro_consensus_count = sum(
        1
        for passed in (
            ofi_z is not None and float(ofi_z) >= 2.5,
            buy_ratio is not None and float(buy_ratio) >= config.buy_ratio_threshold,
            volume_ratio >= config.volume_spike_threshold,
            ask_drop is not None and float(ask_drop) >= config.ask_depth_drop_threshold,
            bid_support is not None
            and float(bid_support) >= config.bid_depth_support_threshold,
        )
        if passed
    )

    return {
        "short_return_pct": round(_return_pct(candles, config.short_window_bars), 6),
        "mid_return_pct": round(_return_pct(candles, config.mid_window_bars), 6),
        "long_return_pct": round(_return_pct(candles, config.long_window_bars), 6),
        "short_return_z": round(_zscore(current_return, recent_returns), 6),
        "price_up_velocity": round(
            max(0.0, _return_pct(candles, config.short_window_bars))
            / max(1, config.short_window_bars),
            6,
        ),
        "prev_price_up_velocity": round(max(0.0, prev_return), 6),
        "price_up_acceleration": round(current_return - prev_return, 6),
        "close_location_value": round(close_location, 6),
        "upper_wick_ratio": round(upper_wick, 6),
        "range_expansion_ratio": (
            round((candle_range / range_baseline), 6)
            if range_baseline and range_baseline > 0
            else 1.0
        ),
        "breakout_distance_pct": round(breakout_distance_pct, 6),
        "price_progress_ratio": round(price_progress_ratio, 6),
        "volume_ratio_short": round(volume_ratio, 6),
        "volume_z": round(_zscore(candle.volume, volumes[:-1]), 6),
        "total_volume": round(candle.volume, 6),
        "buy_ratio": None if buy_ratio is None else round(buy_ratio, 6),
        "sell_ratio": None if sell_ratio is None else round(sell_ratio, 6),
        "cvd_delta": None if cvd_delta is None else round(cvd_delta, 6),
        "cvd": round(running_cvd, 6),
        "cvd_slope": round(cvd_slope, 6),
        "cvd_slope_z": round(cvd_slope_z, 6),
        "buy_pressure_decay": bool(
            prev_buy_ratio is not None
            and buy_ratio is not None
            and buy_ratio < prev_buy_ratio
        ),
        "ask_depth_drop_ratio": None if ask_drop is None else round(ask_drop, 6),
        "ask_depth_refill_ratio": None if ask_refill is None else round(ask_refill, 6),
        "bid_depth_support_ratio": (
            None if bid_support is None else round(bid_support, 6)
        ),
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
        "trade_aggressor_missing": buy_ratio is None,
        "no_new_high": bool(no_new_high),
        "vwap_extension_pct": round(vwap_extension_pct, 6),
        "atr_extension": round(atr_extension, 6),
        "panic_buy_high_reference": panic_buy_high,
    }


def compute_panic_buy_score(
    features: dict[str, Any], config: PanicBuyingDetectorConfig
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    short_return = float(features.get("short_return_pct") or 0.0)
    mid_return = float(features.get("mid_return_pct") or 0.0)
    short_z = float(features.get("short_return_z") or 0.0)
    volume_ratio = float(features.get("volume_ratio_short") or 0.0)
    buy_ratio = features.get("buy_ratio")
    cvd_slope_z = float(features.get("cvd_slope_z") or 0.0)
    ofi_z = features.get("ofi_z")
    ask_drop = features.get("ask_depth_drop_ratio")
    bid_support = features.get("bid_depth_support_ratio")
    spread_ratio = features.get("spread_ratio")
    clv = float(features.get("close_location_value") or 0.5)
    range_expansion = float(features.get("range_expansion_ratio") or 1.0)

    price_score = max(
        _clamp01(short_return / max(config.min_abs_rise_short_pct, 1e-9)),
        _clamp01(mid_return / max(config.min_abs_rise_mid_pct, 1e-9)),
        _clamp01(short_z / max(config.return_z_panic_buy_threshold, 1e-9)),
    )
    if short_return >= config.min_abs_rise_short_pct:
        reasons.append("short_return_breakout")
    if mid_return >= config.min_abs_rise_mid_pct:
        reasons.append("mid_return_breakout")
    if short_z >= config.return_z_panic_buy_threshold:
        reasons.append("positive_return_z")

    volume_score = max(
        _clamp01((volume_ratio - 1.0) / max(config.volume_spike_threshold - 1.0, 1e-9)),
        _clamp01((float(features.get("volume_z") or 0.0)) / 3.0),
    )
    if volume_ratio >= config.volume_spike_threshold:
        reasons.append("volume_spike")

    trade_flow_score = 0.0
    if buy_ratio is not None:
        trade_flow_score = max(
            trade_flow_score,
            _clamp01(
                (float(buy_ratio) - 0.50) / max(config.buy_ratio_threshold - 0.50, 1e-9)
            ),
        )
        if float(buy_ratio) >= config.buy_ratio_threshold:
            reasons.append("buy_ratio_high")
    if cvd_slope_z >= config.cvd_slope_buy_threshold:
        trade_flow_score = max(
            trade_flow_score,
            _clamp01(cvd_slope_z / max(config.cvd_slope_buy_threshold, 1e-9)),
        )
        reasons.append("cvd_slope_strong")
    if ofi_z is not None:
        trade_flow_score = max(
            trade_flow_score,
            _clamp01(float(ofi_z) / max(config.ofi_z_panic_buy_threshold, 1e-9)),
        )
        if float(ofi_z) >= config.ofi_z_panic_buy_threshold:
            reasons.append("ofi_buy_pressure")

    orderbook_score = 0.0
    if ask_drop is not None:
        orderbook_score = max(
            orderbook_score,
            _clamp01(float(ask_drop) / max(config.ask_depth_drop_threshold, 1e-9)),
        )
        if float(ask_drop) >= config.ask_depth_drop_threshold:
            reasons.append("ask_depth_sweep")
    if bid_support is not None:
        orderbook_score = max(
            orderbook_score,
            _clamp01(
                float(bid_support) / max(config.bid_depth_support_threshold, 1e-9)
            ),
        )
        if float(bid_support) >= config.bid_depth_support_threshold:
            reasons.append("bid_depth_support")

    spread_score = 0.0
    if spread_ratio is not None:
        spread_score = _clamp01(
            (float(spread_ratio) - 1.0) / max(config.spread_widen_threshold - 1.0, 1e-9)
        )
        if float(spread_ratio) >= config.spread_widen_threshold:
            reasons.append("spread_widen")

    candle_score = max(
        _clamp01(clv / max(config.close_near_high_threshold, 1e-9)),
        _clamp01(range_expansion / max(config.range_expansion_threshold, 1e-9)),
    )
    if clv >= config.close_near_high_threshold:
        reasons.append("close_near_high")
    if range_expansion >= config.range_expansion_threshold:
        reasons.append("range_expansion")

    panic_buy_score = (
        0.28 * price_score
        + 0.17 * volume_score
        + 0.22 * trade_flow_score
        + 0.18 * orderbook_score
        + 0.07 * spread_score
        + 0.08 * candle_score
    )
    if features.get("orderbook_missing"):
        if config.degrade_when_orderbook_missing:
            panic_buy_score = min(panic_buy_score, 0.82)
        reasons.append("orderbook_missing_degraded")
    if features.get("trade_aggressor_missing"):
        if config.degrade_when_trade_aggressor_missing:
            panic_buy_score = min(panic_buy_score, 0.78)
        reasons.append("trade_aggressor_missing_degraded")
    if float(features.get("total_volume") or 0.0) < config.min_total_volume:
        panic_buy_score = min(panic_buy_score, 0.45)
        reasons.append("low_liquidity_score_capped")
    return round(_clamp01(panic_buy_score), 6), reasons


def compute_exhaustion_score(
    features: dict[str, Any], config: PanicBuyingDetectorConfig
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    buy_ratio = features.get("buy_ratio")
    ofi_z = features.get("ofi_z")
    cvd_slope_z = float(features.get("cvd_slope_z") or 0.0)
    ask_refill = features.get("ask_depth_refill_ratio")
    clv = float(features.get("close_location_value") or 0.5)
    upper_wick = float(features.get("upper_wick_ratio") or 0.0)
    volume_ratio = float(features.get("volume_ratio_short") or 0.0)
    price_progress = float(features.get("price_progress_ratio") or 1.0)
    velocity = float(features.get("price_up_velocity") or 0.0)
    prev_velocity = float(features.get("prev_price_up_velocity") or velocity)

    price_stall_score = 1.0 if bool(features.get("no_new_high")) else 0.0
    if price_stall_score:
        reasons.append("no_new_high")
    if prev_velocity > 0 and velocity < prev_velocity:
        price_stall_score = max(
            price_stall_score, _clamp01(1.0 - (velocity / max(prev_velocity, 1e-9)))
        )
        reasons.append("upside_velocity_decay")

    flow_decay_score = 0.0
    if buy_ratio is not None:
        flow_decay_score = max(
            flow_decay_score,
            _clamp01(
                (config.buy_ratio_threshold - float(buy_ratio))
                / max(
                    config.buy_ratio_threshold - config.buy_ratio_exhaustion_max, 1e-9
                )
            ),
        )
        if float(buy_ratio) <= config.buy_ratio_exhaustion_max or bool(
            features.get("buy_pressure_decay")
        ):
            reasons.append("buy_ratio_decay")
    if ofi_z is not None:
        flow_decay_score = max(
            flow_decay_score,
            _clamp01(
                (config.ofi_z_panic_buy_threshold - float(ofi_z))
                / max(
                    config.ofi_z_panic_buy_threshold - config.ofi_z_exhaustion_max, 1e-9
                )
            ),
        )
        if float(ofi_z) <= config.ofi_z_exhaustion_max:
            reasons.append("ofi_decay")
    flow_decay_score = max(
        flow_decay_score,
        _clamp01(
            (config.cvd_slope_buy_threshold - cvd_slope_z)
            / max(
                config.cvd_slope_buy_threshold - config.cvd_slope_exhaustion_max, 1e-9
            )
        ),
    )
    if cvd_slope_z <= config.cvd_slope_exhaustion_max:
        reasons.append("cvd_slope_decay")

    orderbook_absorption_score = 0.0
    if ask_refill is not None:
        orderbook_absorption_score = max(
            orderbook_absorption_score,
            _clamp01(float(ask_refill) / max(config.ask_depth_refill_min, 1e-9)),
        )
        if float(ask_refill) >= config.ask_depth_refill_min:
            reasons.append("ask_depth_refill")
    ask_absorption = (
        ask_refill is not None
        and float(ask_refill) >= config.ask_depth_refill_min
        and buy_ratio is not None
        and float(buy_ratio) >= config.buy_ratio_exhaustion_max
        and price_progress <= config.price_progress_exhaustion_max
    )
    if ask_absorption:
        orderbook_absorption_score = max(orderbook_absorption_score, 1.0)
        reasons.append("ask_absorption")

    candle_exhaustion_score = max(
        _clamp01(upper_wick / max(config.upper_wick_exhaustion_min, 1e-9)),
        _clamp01(
            (config.close_near_high_threshold - clv)
            / max(
                config.close_near_high_threshold - config.close_location_exhaustion_max,
                1e-9,
            )
        ),
    )
    if upper_wick >= config.upper_wick_exhaustion_min:
        reasons.append("upper_wick_exhaustion")
    if clv <= config.close_location_exhaustion_max:
        reasons.append("close_location_failed")

    effort_result_divergence = (
        volume_ratio >= config.volume_spike_threshold
        and price_progress <= config.price_progress_exhaustion_max
    )
    effort_score = 1.0 if effort_result_divergence else 0.0
    if effort_result_divergence:
        reasons.append("effort_result_divergence")

    extension_score = max(
        _clamp01(
            float(features.get("vwap_extension_pct") or 0.0)
            / max(config.vwap_extension_extreme_pct, 1e-9)
        ),
        _clamp01(
            float(features.get("atr_extension") or 0.0)
            / max(config.atr_extension_extreme, 1e-9)
        ),
    )
    if extension_score >= 0.8:
        reasons.append("extension_risk")

    exhaustion_score = (
        0.22 * price_stall_score
        + 0.20 * flow_decay_score
        + 0.18 * orderbook_absorption_score
        + 0.15 * candle_exhaustion_score
        + 0.15 * effort_score
        + 0.10 * extension_score
    )
    if ask_refill is not None and buy_ratio is not None:
        if (
            float(ask_refill) >= config.ask_depth_refill_min
            and float(buy_ratio) >= config.buy_ratio_threshold
            and price_progress > 0.5
        ):
            exhaustion_score *= 0.75
            reasons.append("ask_refill_but_price_progress_continues")
    return round(_clamp01(exhaustion_score), 6), reasons


def _report_state(internal_state: PanicBuyingInternalState) -> str:
    if internal_state == PanicBuyingInternalState.PANIC_BUY_CANDIDATE:
        return REPORT_PANIC_BUY_WATCH
    if internal_state == PanicBuyingInternalState.PANIC_BUY_ACTIVE:
        return REPORT_PANIC_BUY
    if internal_state == PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE:
        return REPORT_EXHAUSTION_WATCH
    if internal_state in {
        PanicBuyingInternalState.BUYING_EXHAUSTED,
        PanicBuyingInternalState.COOLDOWN,
    }:
        return REPORT_BUYING_EXHAUSTED
    return REPORT_NORMAL


class PanicBuyingStateDetector:
    def __init__(self, config: PanicBuyingDetectorConfig | None = None) -> None:
        self.config = config or PanicBuyingDetectorConfig()
        self.state = PanicBuyingInternalState.NORMAL
        self.bars_in_state = 0
        self.panic_buy_start_ts: datetime | None = None
        self.panic_buy_high: float | None = None
        self.panic_ask_depth_baseline: float | None = None
        self.max_panic_buy_score = 0.0
        self.max_exhaustion_score = 0.0
        self.recent_panic_buy_scores: deque[float] = deque(
            maxlen=max(1, self.config.panic_buy_confirm_window)
        )
        self.recent_exhaustion_scores: deque[float] = deque(
            maxlen=max(1, self.config.exhaustion_confirm_window)
        )
        self.cooldown_remaining = 0
        self._candles: list[PanicBuyingCandle] = []
        self._trades: list[PanicBuyingTradeFlow] = []
        self._orderbooks: list[PanicBuyingOrderbookMicro] = []
        self._panic_vwap_value = 0.0
        self._panic_vwap_volume = 0.0

    def update(
        self,
        candle: PanicBuyingCandle,
        trade_flow: PanicBuyingTradeFlow | None = None,
        orderbook_micro: PanicBuyingOrderbookMicro | None = None,
    ) -> PanicBuyingSignal:
        self._candles.append(candle)
        self._candles = self._candles[
            -max(self.config.long_window_bars, self.config.mid_window_bars, 10) :
        ]
        if trade_flow is not None:
            self._trades.append(trade_flow)
            self._trades = self._trades[-max(self.config.long_window_bars, 10) :]
        current_orderbook = orderbook_micro or PanicBuyingOrderbookMicro(
            ts=candle.ts,
            micro_state="missing",
            ready=False,
            observer_healthy=False,
        )
        self._orderbooks.append(current_orderbook)
        self._orderbooks = self._orderbooks[-max(self.config.long_window_bars, 10) :]

        if len(self._candles) < max(2, self.config.min_bars_required):
            return self._build_signal(
                panic_buy_score=0.0,
                exhaustion_score=0.0,
                reasons=["insufficient_data"],
                metrics={"bar_count": len(self._candles)},
                panic_buy_entered=False,
                previous_state=self.state,
            )

        features = compute_panic_buying_features(
            self._candles,
            self._trades,
            self._orderbooks,
            config=self.config,
            panic_buy_high=self.panic_buy_high,
            panic_ask_depth_baseline=self.panic_ask_depth_baseline,
        )
        if self._panic_vwap_volume > 0:
            panic_anchored_vwap = self._panic_vwap_value / self._panic_vwap_volume
            features["panic_buy_anchored_vwap"] = round(panic_anchored_vwap, 6)
            features["panic_buy_anchored_vwap_lost"] = (
                candle.close < panic_anchored_vwap
            )
        else:
            features["panic_buy_anchored_vwap"] = None
            features["panic_buy_anchored_vwap_lost"] = False

        panic_buy_score, panic_reasons = compute_panic_buy_score(features, self.config)
        exhaustion_score, exhaustion_reasons = compute_exhaustion_score(
            features, self.config
        )
        self.recent_panic_buy_scores.append(panic_buy_score)
        self.recent_exhaustion_scores.append(exhaustion_score)

        previous_state = self.state
        panic_buy_entered = False
        price_breakout = (
            float(features["short_return_pct"]) >= self.config.min_abs_rise_short_pct
            or float(features["mid_return_pct"]) >= self.config.min_abs_rise_mid_pct
            or float(features["short_return_z"])
            >= self.config.return_z_panic_buy_threshold
        )
        flow_confirmation = float(
            features.get("volume_ratio_short") or 0.0
        ) >= self.config.volume_spike_threshold and (
            features.get("buy_ratio") is not None
            and float(features["buy_ratio"]) >= self.config.buy_ratio_threshold
            or float(features.get("cvd_slope_z") or 0.0)
            >= self.config.cvd_slope_buy_threshold
            or features.get("ofi_z") is not None
            and float(features["ofi_z"]) >= self.config.ofi_z_panic_buy_threshold
        )
        orderbook_missing = bool(features.get("orderbook_missing"))
        liquidity_confirmation = (
            orderbook_missing
            or (
                features.get("ask_depth_drop_ratio") is not None
                and float(features["ask_depth_drop_ratio"])
                >= self.config.ask_depth_drop_threshold
            )
            or (
                features.get("spread_ratio") is not None
                and float(features["spread_ratio"])
                >= self.config.spread_widen_threshold
            )
            or (
                features.get("bid_depth_support_ratio") is not None
                and float(features["bid_depth_support_ratio"])
                >= self.config.bid_depth_support_threshold
            )
        )
        panic_candidate = (
            price_breakout
            and flow_confirmation
            and liquidity_confirmation
            and panic_buy_score >= self.config.panic_buy_entry_score_threshold
        )
        exhaustion_candidate = self._exhaustion_candidate(features, exhaustion_score)
        high_break = self._panic_high_broken(candle.high)
        panic_resumed = high_break or panic_candidate

        if self.state == PanicBuyingInternalState.NORMAL:
            if panic_candidate:
                self._transition(PanicBuyingInternalState.PANIC_BUY_CANDIDATE)
        elif self.state == PanicBuyingInternalState.PANIC_BUY_CANDIDATE:
            if self._confirm_panic_buy_entry():
                self._transition(PanicBuyingInternalState.PANIC_BUY_ACTIVE)
                self._initialize_panic_buy_tracking(candle)
                panic_buy_entered = True
            elif (
                not panic_candidate
                and panic_buy_score < self.config.panic_buy_entry_score_threshold * 0.80
            ):
                self._transition(PanicBuyingInternalState.NORMAL)
        elif self.state == PanicBuyingInternalState.PANIC_BUY_ACTIVE:
            self._update_panic_buy_tracking(candle, orderbook_micro)
            if exhaustion_candidate:
                self._transition(PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE)
            elif self.bars_in_state >= self.config.max_panic_buy_active_bars:
                self._transition(PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE)
        elif self.state == PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE:
            self._update_panic_buy_tracking(candle, orderbook_micro)
            if panic_resumed:
                self._transition(PanicBuyingInternalState.PANIC_BUY_ACTIVE)
            elif self._confirm_exhaustion():
                self._transition(PanicBuyingInternalState.BUYING_EXHAUSTED)
        elif self.state == PanicBuyingInternalState.BUYING_EXHAUSTED:
            self.cooldown_remaining = self.config.cooldown_bars
            self._transition(PanicBuyingInternalState.COOLDOWN)
        elif self.state == PanicBuyingInternalState.COOLDOWN:
            self.cooldown_remaining = max(0, self.cooldown_remaining - 1)
            if self.cooldown_remaining <= 0:
                self._reset_panic_buy_tracking()
                self._transition(PanicBuyingInternalState.NORMAL)

        self.max_panic_buy_score = max(self.max_panic_buy_score, panic_buy_score)
        self.max_exhaustion_score = max(self.max_exhaustion_score, exhaustion_score)
        reasons = list(dict.fromkeys(panic_reasons + exhaustion_reasons))
        if self.state == PanicBuyingInternalState.COOLDOWN:
            reasons.append("cooldown_active")
        if self.state == PanicBuyingInternalState.BUYING_EXHAUSTED:
            reasons.append("buying_exhaustion_confirmed")
        return self._build_signal(
            panic_buy_score=panic_buy_score,
            exhaustion_score=exhaustion_score,
            reasons=reasons,
            metrics={
                **features,
                "panic_buy_score": panic_buy_score,
                "exhaustion_score": exhaustion_score,
            },
            panic_buy_entered=panic_buy_entered,
            previous_state=previous_state,
        )

    def _transition(self, state: PanicBuyingInternalState) -> None:
        if state != self.state:
            self.state = state
            self.bars_in_state = 0
        else:
            self.bars_in_state += 1

    def _confirm_panic_buy_entry(self) -> bool:
        return (
            sum(
                1
                for score in self.recent_panic_buy_scores
                if score >= self.config.panic_buy_entry_score_threshold
            )
            >= self.config.panic_buy_confirm_bars
        )

    def _confirm_exhaustion(self) -> bool:
        return (
            sum(
                1
                for score in self.recent_exhaustion_scores
                if score >= self.config.exhaustion_score_threshold
            )
            >= self.config.exhaustion_confirm_bars
        )

    def _panic_high_broken(self, current_high: float) -> bool:
        if self.panic_buy_high is None or self.panic_buy_high <= 0 or current_high <= 0:
            return False
        tolerance = float(self.config.high_break_tolerance_pct) / 100.0
        return current_high > self.panic_buy_high * (1.0 + tolerance)

    def _exhaustion_candidate(
        self, features: dict[str, Any], exhaustion_score: float
    ) -> bool:
        if exhaustion_score < self.config.exhaustion_score_threshold:
            return False
        if not bool(features.get("no_new_high")):
            return False
        buy_ratio = features.get("buy_ratio")
        if (
            buy_ratio is not None
            and float(buy_ratio) >= self.config.buy_ratio_threshold
            and not bool(features.get("buy_pressure_decay"))
        ):
            return False
        if (
            buy_ratio is not None
            and float(buy_ratio) >= self.config.buy_ratio_threshold
            and features.get("ofi_z") is not None
            and float(features["ofi_z"]) >= self.config.ofi_z_panic_buy_threshold
            and features.get("ask_depth_drop_ratio") is not None
            and float(features["ask_depth_drop_ratio"])
            >= self.config.ask_depth_drop_threshold
        ):
            return False
        flow_decay = (
            buy_ratio is not None
            and float(buy_ratio) <= self.config.buy_ratio_exhaustion_max
            or features.get("ofi_z") is not None
            and float(features["ofi_z"]) <= self.config.ofi_z_exhaustion_max
            or float(features.get("cvd_slope_z") or 0.0)
            <= self.config.cvd_slope_exhaustion_max
        )
        supply_returning = (
            features.get("ask_depth_refill_ratio") is not None
            and float(features["ask_depth_refill_ratio"])
            >= self.config.ask_depth_refill_min
        )
        candle_exhaustion = (
            float(features.get("upper_wick_ratio") or 0.0)
            >= self.config.upper_wick_exhaustion_min
            or float(features.get("close_location_value") or 0.5)
            <= self.config.close_location_exhaustion_max
        )
        effort_result = (
            float(features.get("volume_ratio_short") or 0.0)
            >= self.config.volume_spike_threshold
            and float(features.get("price_progress_ratio") or 1.0)
            <= self.config.price_progress_exhaustion_max
        )
        return (flow_decay or supply_returning) and (candle_exhaustion or effort_result)

    def _initialize_panic_buy_tracking(self, candle: PanicBuyingCandle) -> None:
        self.panic_buy_start_ts = candle.ts
        self.panic_buy_high = candle.high
        self._panic_vwap_value = 0.0
        self._panic_vwap_volume = 0.0
        self._update_panic_buy_tracking(
            candle, self._orderbooks[-1] if self._orderbooks else None
        )

    def _update_panic_buy_tracking(
        self,
        candle: PanicBuyingCandle,
        orderbook_micro: PanicBuyingOrderbookMicro | None,
    ) -> None:
        self.panic_buy_high = (
            candle.high
            if self.panic_buy_high is None
            else max(self.panic_buy_high, candle.high)
        )
        price_for_vwap = (
            candle.vwap if candle.vwap and candle.vwap > 0 else candle.close
        )
        if candle.volume > 0 and price_for_vwap > 0:
            self._panic_vwap_value += price_for_vwap * candle.volume
            self._panic_vwap_volume += candle.volume
        if (
            self.panic_ask_depth_baseline is None
            and orderbook_micro is not None
            and orderbook_micro.ask_depth_l5
        ):
            self.panic_ask_depth_baseline = float(orderbook_micro.ask_depth_l5)

    def _reset_panic_buy_tracking(self) -> None:
        self.panic_buy_start_ts = None
        self.panic_buy_high = None
        self.panic_ask_depth_baseline = None
        self.max_panic_buy_score = 0.0
        self.max_exhaustion_score = 0.0
        self._panic_vwap_value = 0.0
        self._panic_vwap_volume = 0.0
        self.recent_panic_buy_scores.clear()
        self.recent_exhaustion_scores.clear()

    def _build_signal(
        self,
        *,
        panic_buy_score: float,
        exhaustion_score: float,
        reasons: list[str],
        metrics: dict[str, Any],
        panic_buy_entered: bool,
        previous_state: PanicBuyingInternalState,
    ) -> PanicBuyingSignal:
        panic_active = self.state in {
            PanicBuyingInternalState.PANIC_BUY_CANDIDATE,
            PanicBuyingInternalState.PANIC_BUY_ACTIVE,
            PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE,
        }
        allow_tp_override = self.state in {
            PanicBuyingInternalState.PANIC_BUY_CANDIDATE,
            PanicBuyingInternalState.PANIC_BUY_ACTIVE,
        }
        allow_runner = self.state in {
            PanicBuyingInternalState.PANIC_BUY_CANDIDATE,
            PanicBuyingInternalState.PANIC_BUY_ACTIVE,
            PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE,
        }
        tighten_trailing_stop = self.state in {
            PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE,
            PanicBuyingInternalState.BUYING_EXHAUSTED,
        }
        force_exit_runner = self.state == PanicBuyingInternalState.BUYING_EXHAUSTED
        confidence = 0.4
        if metrics.get("buy_ratio") is not None:
            confidence += 0.25
        if not metrics.get("orderbook_missing"):
            confidence += 0.25
        if float(metrics.get("volume_ratio_short") or 0.0) > 0:
            confidence += 0.10
        confidence = round(min(1.0, confidence), 6)
        severity = "LOW"
        if panic_buy_score >= 0.90:
            severity = "EXTREME"
        elif panic_buy_score >= 0.80:
            severity = "HIGH"
        elif panic_buy_score >= self.config.panic_buy_entry_score_threshold:
            severity = "MEDIUM"
        return PanicBuyingSignal(
            state=_report_state(self.state),
            internal_state=self.state.value,
            panic_buy_score=round(float(panic_buy_score), 6),
            exhaustion_score=round(float(exhaustion_score), 6),
            panic_buy_active=bool(panic_active),
            panic_buy_entered=bool(
                panic_buy_entered
                or (
                    previous_state != PanicBuyingInternalState.PANIC_BUY_ACTIVE
                    and self.state == PanicBuyingInternalState.PANIC_BUY_ACTIVE
                )
            ),
            exhaustion_candidate=self.state
            == PanicBuyingInternalState.BUYING_EXHAUSTION_CANDIDATE,
            exhaustion_confirmed=self.state
            == PanicBuyingInternalState.BUYING_EXHAUSTED,
            allow_tp_override=bool(allow_tp_override),
            allow_runner=bool(allow_runner),
            tighten_trailing_stop=bool(tighten_trailing_stop),
            force_exit_runner=bool(force_exit_runner),
            confidence=confidence,
            severity=severity,
            panic_buy_high=(
                None
                if self.panic_buy_high is None
                else round(float(self.panic_buy_high), 6)
            ),
            panic_buy_start_ts=(
                self.panic_buy_start_ts.isoformat(timespec="seconds")
                if self.panic_buy_start_ts
                else None
            ),
            cooldown_remaining=int(self.cooldown_remaining),
            reasons=list(dict.fromkeys(reasons)),
            metrics=metrics,
        )


def _field(fields: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in fields and fields.get(name) not in (None, "", "-"):
            return fields.get(name)
    return None


def candle_from_event(row: dict[str, Any]) -> PanicBuyingCandle | None:
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
            "price",
            "signal_price",
            "order_price",
        )
    )
    if close is None or close <= 0:
        return None
    open_value = (
        _safe_float(_field(fields, "open", "open_price", "candle_open"), close) or close
    )
    high = _safe_float(
        _field(fields, "high", "high_price", "candle_high"), max(open_value, close)
    ) or max(open_value, close)
    low = _safe_float(
        _field(fields, "low", "low_price", "candle_low"), min(open_value, close)
    ) or min(open_value, close)
    volume = _safe_float(
        _field(fields, "volume", "today_vol", "trade_volume", "total_volume"), None
    )
    if volume is None:
        buy_volume = (
            _safe_float(_field(fields, "buy_exec_volume", "buy_volume"), 0.0) or 0.0
        )
        sell_volume = (
            _safe_float(_field(fields, "sell_exec_volume", "sell_volume"), 0.0) or 0.0
        )
        volume = buy_volume + sell_volume
    vwap = _safe_float(
        _field(fields, "vwap", "vwap_price", "panic_buy_anchored_vwap"), None
    )
    return PanicBuyingCandle(
        ts=ts,
        open=open_value,
        high=max(high, low, close),
        low=min(low, high, close),
        close=close,
        volume=max(0.0, volume or 0.0),
        vwap=vwap,
    )


def trade_flow_from_event(row: dict[str, Any]) -> PanicBuyingTradeFlow | None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    ts = _parse_dt(row.get("emitted_at"))
    if ts is None:
        return None
    buy_volume = _safe_float(_field(fields, "buy_exec_volume", "buy_volume"), None)
    sell_volume = _safe_float(_field(fields, "sell_exec_volume", "sell_volume"), None)
    total_volume = _safe_float(
        _field(fields, "total_volume", "volume", "today_vol"), None
    )
    buy_ratio = _safe_float(
        _field(fields, "exec_buy_ratio", "buy_ratio", "buy_ratio_ws"), None
    )
    if (
        (buy_volume is None or sell_volume is None)
        and total_volume is not None
        and total_volume > 0
    ):
        if buy_ratio is not None:
            ratio = buy_ratio / 100.0 if buy_ratio > 1.0 else buy_ratio
            buy_volume = total_volume * _clamp01(ratio)
            sell_volume = total_volume - buy_volume
    if buy_volume is None and sell_volume is None and buy_ratio is not None:
        ratio = buy_ratio / 100.0 if buy_ratio > 1.0 else buy_ratio
        buy_volume = _clamp01(ratio)
        sell_volume = 1.0 - buy_volume
    if buy_volume is None and sell_volume is None:
        return None
    return PanicBuyingTradeFlow(
        ts=ts,
        buy_volume=max(0.0, buy_volume or 0.0),
        sell_volume=max(0.0, sell_volume or 0.0),
    )


def orderbook_micro_from_event(row: dict[str, Any]) -> PanicBuyingOrderbookMicro | None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    ts = _parse_dt(row.get("emitted_at"))
    if ts is None:
        return None
    best_bid = _safe_float(
        _field(fields, "best_bid", "bid_price", "swing_micro_ws_best_bid"), None
    )
    best_ask = _safe_float(
        _field(fields, "best_ask", "ask_price", "swing_micro_ws_best_ask"), None
    )
    ofi_z = _safe_float(_field(fields, "orderbook_micro_ofi_z", "ofi_z"), None)
    qi_ewma = _safe_float(
        _field(fields, "orderbook_micro_qi_ewma", "orderbook_micro_qi", "qi_ewma"), None
    )
    spread_ratio = _safe_float(
        _field(
            fields, "panic_buy_spread_ratio", "panic_spread_ratio", "micro_spread_ratio"
        ),
        None,
    )
    if spread_ratio is None:
        raw_spread_ratio = _safe_float(_field(fields, "spread_ratio"), None)
        if raw_spread_ratio is not None and raw_spread_ratio >= 1.0:
            spread_ratio = raw_spread_ratio
    bid_depth = _safe_float(
        _field(fields, "bid_depth_l5", "bid_tot", "net_bid_depth"), None
    )
    ask_depth = _safe_float(
        _field(fields, "ask_depth_l5", "ask_tot", "net_ask_depth"), None
    )
    ask_drop = _safe_float(_field(fields, "ask_depth_drop_ratio"), None)
    ask_refill = _safe_float(_field(fields, "ask_depth_refill_ratio"), None)
    bid_support = _safe_float(_field(fields, "bid_depth_support_ratio"), None)
    micro_state = str(
        _field(fields, "orderbook_micro_state", "micro_state") or "missing"
    )
    ready = _safe_bool(
        _field(fields, "orderbook_micro_ready", "orderbook_ready"), default=False
    )
    healthy = _safe_bool(
        _field(
            fields, "orderbook_micro_observer_healthy", "orderbook_observer_healthy"
        ),
        default=False,
    )
    has_orderbook_signal = any(
        value is not None
        for value in (
            best_bid,
            best_ask,
            ofi_z,
            qi_ewma,
            spread_ratio,
            bid_depth,
            ask_depth,
            ask_drop,
            ask_refill,
            bid_support,
        )
    ) or micro_state not in {"", "missing"}
    if not has_orderbook_signal:
        return None
    return PanicBuyingOrderbookMicro(
        ts=ts,
        best_bid=best_bid,
        best_ask=best_ask,
        bid_depth_l5=bid_depth,
        ask_depth_l5=ask_depth,
        spread_ratio=spread_ratio,
        ask_depth_drop_ratio=ask_drop,
        ask_depth_refill_ratio=ask_refill,
        bid_depth_support_ratio=bid_support,
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
    config: PanicBuyingDetectorConfig | None = None,
    max_symbols: int = 20,
    micro_snapshot_max_age_sec: float = 120.0,
    input_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or PanicBuyingDetectorConfig()
    grouped: dict[str, list[dict[str, Any]]] = {}
    names: dict[str, str] = {}
    for row in events:
        event_ts = _parse_dt(row.get("emitted_at"))
        if as_of is not None and event_ts is not None and event_ts > as_of:
            continue
        code = str(row.get("stock_code") or "").strip()[:6]
        if not code:
            continue
        if (
            candle_from_event(row) is None
            and trade_flow_from_event(row) is None
            and orderbook_micro_from_event(row) is None
        ):
            continue
        grouped.setdefault(code, []).append(row)
        names[code] = str(row.get("stock_name") or code)

    symbol_signals: list[PanicBuyingSymbolSignal] = []
    reason_counter: Counter[str] = Counter()
    state_counter: Counter[str] = Counter()
    missing_orderbook = 0
    degraded_orderbook = 0
    missing_trade = 0
    carried_orderbook = 0
    carried_trade = 0
    for code, rows in grouped.items():
        detector = PanicBuyingStateDetector(cfg)
        latest_signal: PanicBuyingSignal | None = None
        latest_ts: str | None = None
        latest_trade_flow: PanicBuyingTradeFlow | None = None
        latest_trade_ts: datetime | None = None
        latest_orderbook_micro: PanicBuyingOrderbookMicro | None = None
        latest_orderbook_ts: datetime | None = None
        for row in sorted(rows, key=lambda item: str(item.get("emitted_at") or "")):
            candle = candle_from_event(row)
            current_trade_flow = trade_flow_from_event(row)
            current_orderbook_micro = orderbook_micro_from_event(row)
            if current_trade_flow is not None:
                latest_trade_flow = current_trade_flow
                latest_trade_ts = current_trade_flow.ts
            if current_orderbook_micro is not None:
                latest_orderbook_micro = current_orderbook_micro
                latest_orderbook_ts = current_orderbook_micro.ts
            if candle is None:
                continue
            trade_flow = current_trade_flow
            trade_flow_carried = False
            trade_flow_age_sec = _age_seconds(candle.ts, latest_trade_ts)
            if (
                trade_flow is None
                and latest_trade_flow is not None
                and trade_flow_age_sec is not None
                and 0 <= trade_flow_age_sec <= micro_snapshot_max_age_sec
            ):
                trade_flow = latest_trade_flow
                trade_flow_carried = True
            orderbook_micro = current_orderbook_micro
            orderbook_carried = False
            orderbook_age_sec = _age_seconds(candle.ts, latest_orderbook_ts)
            if (
                orderbook_micro is None
                and latest_orderbook_micro is not None
                and orderbook_age_sec is not None
                and 0 <= orderbook_age_sec <= micro_snapshot_max_age_sec
            ):
                orderbook_micro = latest_orderbook_micro
                orderbook_carried = True
            latest_ts = candle.ts.isoformat(timespec="seconds")
            latest_signal = detector.update(
                candle,
                trade_flow=trade_flow,
                orderbook_micro=orderbook_micro,
            )
            latest_signal.metrics["trade_flow_carried_forward"] = bool(
                trade_flow_carried
            )
            latest_signal.metrics["trade_flow_age_sec"] = (
                None if trade_flow_age_sec is None else round(trade_flow_age_sec, 6)
            )
            latest_signal.metrics["orderbook_carried_forward"] = bool(orderbook_carried)
            latest_signal.metrics["orderbook_age_sec"] = (
                None if orderbook_age_sec is None else round(orderbook_age_sec, 6)
            )
            if trade_flow_carried:
                carried_trade += 1
            if orderbook_carried:
                carried_orderbook += 1
        if latest_signal is None:
            continue
        symbol_signals.append(
            PanicBuyingSymbolSignal(
                stock_code=code,
                stock_name=names.get(code, code),
                signal=latest_signal,
                latest_event_at=latest_ts,
            )
        )
        state_counter[latest_signal.state] += 1
        reason_counter.update(latest_signal.reasons)
        if latest_signal.metrics.get("orderbook_missing"):
            missing_orderbook += 1
        if "orderbook_missing_degraded" in latest_signal.reasons:
            degraded_orderbook += 1
        if latest_signal.metrics.get("trade_aggressor_missing"):
            missing_trade += 1

    symbol_signals.sort(
        key=lambda item: (
            item.signal.panic_buy_score,
            item.signal.exhaustion_score,
            item.signal.confidence,
        ),
        reverse=True,
    )
    max_panic_buy_score = max(
        (item.signal.panic_buy_score for item in symbol_signals), default=0.0
    )
    max_exhaustion_score = max(
        (item.signal.exhaustion_score for item in symbol_signals), default=0.0
    )
    active_count = sum(
        1 for item in symbol_signals if item.signal.state == REPORT_PANIC_BUY
    )
    watch_count = sum(
        1 for item in symbol_signals if item.signal.state == REPORT_PANIC_BUY_WATCH
    )
    exhaustion_watch_count = sum(
        1 for item in symbol_signals if item.signal.state == REPORT_EXHAUSTION_WATCH
    )
    exhausted_count = sum(
        1 for item in symbol_signals if item.signal.state == REPORT_BUYING_EXHAUSTED
    )
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
        "policy": {
            "report_only": True,
            "runtime_effect": "report_only_no_mutation",
            "does_not_submit_orders": True,
        },
        "threshold_mode": "static_fallback",
        "threshold_contract": _detector_threshold_contract(
            cfg, sample_count=len(symbol_signals)
        ),
        "threshold_sample_ready": len(symbol_signals) >= max(1, cfg.min_bars_required),
        "evaluated_symbol_count": len(symbol_signals),
        "panic_buy_signal_count": active_count + watch_count,
        "panic_buy_active_count": active_count,
        "panic_buy_watch_count": watch_count,
        "exhaustion_candidate_count": exhaustion_watch_count,
        "exhaustion_confirmed_count": exhausted_count,
        "allow_tp_override_count": sum(
            1 for item in symbol_signals if item.signal.allow_tp_override
        ),
        "allow_runner_count": sum(
            1 for item in symbol_signals if item.signal.allow_runner
        ),
        "force_exit_runner_count": sum(
            1 for item in symbol_signals if item.signal.force_exit_runner
        ),
        "missing_orderbook_count": missing_orderbook,
        "degraded_orderbook_count": degraded_orderbook,
        "missing_trade_aggressor_count": missing_trade,
        "carried_orderbook_snapshot_count": carried_orderbook,
        "carried_trade_aggressor_snapshot_count": carried_trade,
        "micro_snapshot_max_age_sec": int(micro_snapshot_max_age_sec),
        "input_provenance": dict(input_provenance or {}),
        "state_counts": dict(state_counter),
        "reason_counts": dict(reason_counter.most_common(20)),
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
                "auto_buy",
                "bot_restart",
                "provider_route_change",
            ],
            "ofi_direction": "positive",
            "triggered_symbol_count": len(cusum_triggered),
            "consensus_pass_symbol_count": len(consensus_passed),
            "max_ofi_cusum_score": round(max(cusum_scores), 6) if cusum_scores else 0.0,
        },
        "metrics": {
            "max_panic_buy_score": round(max_panic_buy_score, 6),
            "max_exhaustion_score": round(max_exhaustion_score, 6),
            "avg_confidence": round(
                _avg([item.signal.confidence for item in symbol_signals]) or 0.0, 6
            ),
        },
        "latest_signals": [item.to_dict() for item in symbol_signals[:max_symbols]],
    }
