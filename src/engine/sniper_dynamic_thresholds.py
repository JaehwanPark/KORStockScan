"""Dynamic entry threshold helpers based on market cap and liquidity hints."""

from __future__ import annotations

from src.utils.constants import TRADING_RULES


LARGE_CAP_THRESHOLD = 2_000_000_000_000
MID_CAP_THRESHOLD = 500_000_000_000


def _coerce_int(value, default=0):
    try:
        return int(float(value or default))
    except Exception:
        return default


def _coerce_float(value, default=0.0):
    try:
        return float(value or default)
    except Exception:
        return default


def classify_market_cap_bucket(marcap) -> str:
    market_cap = _coerce_int(marcap, 0)
    if market_cap >= LARGE_CAP_THRESHOLD:
        return "large"
    if market_cap >= MID_CAP_THRESHOLD:
        return "mid"
    return "small"


def market_cap_bucket_label(bucket: str) -> str:
    mapping = {
        "large": "대형주",
        "mid": "중형주",
        "small": "중소형주",
    }
    return mapping.get(bucket, "중소형주")


def estimate_turnover_hint(curr_price, volume) -> int:
    return max(0, _coerce_int(curr_price, 0) * _coerce_int(volume, 0))


def get_dynamic_scalp_thresholds(marcap, turnover_hint=0) -> dict:
    base_surge = _coerce_float(getattr(TRADING_RULES, "MAX_SCALP_SURGE_PCT", 20.0), 20.0)
    base_intraday = _coerce_float(getattr(TRADING_RULES, "MAX_INTRADAY_SURGE", 16.0), 16.0)
    base_liquidity = _coerce_int(getattr(TRADING_RULES, "MIN_SCALP_LIQUIDITY", 500_000_000), 500_000_000)

    bucket = classify_market_cap_bucket(marcap)
    if bucket == "large":
        surge = base_surge + 2.0
        intraday = base_intraday + 1.5
        liquidity = max(base_liquidity, 800_000_000)
    elif bucket == "mid":
        surge = base_surge + 0.5
        intraday = base_intraday + 0.5
        liquidity = base_liquidity
    else:
        surge = base_surge - 1.0
        intraday = base_intraday - 0.5
        liquidity = min(base_liquidity, 350_000_000)

    turnover = _coerce_int(turnover_hint, 0)
    if turnover >= 150_000_000_000:
        surge += 0.5
        intraday += 0.5
    elif 0 < turnover <= 20_000_000_000:
        surge -= 0.5
        intraday -= 0.3

    return {
        "bucket": bucket,
        "bucket_label": market_cap_bucket_label(bucket),
        "max_surge": max(16.0, min(25.0, surge)),
        "max_intraday_surge": max(13.0, min(20.0, intraday)),
        "min_liquidity": max(250_000_000, liquidity),
        "market_cap": _coerce_int(marcap, 0),
        "turnover_hint": turnover,
    }


def get_dynamic_swing_gap_threshold(strategy: str, marcap, turnover_hint=0) -> dict:
    fallback = _coerce_float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT", 3.0), 3.0)
    strategy_upper = str(strategy or "").upper()
    if strategy_upper == "KOSPI_ML":
        base_gap = _coerce_float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSPI", fallback), fallback)
    else:
        base_gap = _coerce_float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSDAQ", fallback), fallback)

    bucket = classify_market_cap_bucket(marcap)
    if strategy_upper == "KOSPI_ML":
        adjustments = {"large": 0.5, "mid": 0.0, "small": -0.3}
    else:
        adjustments = {"large": 0.3, "mid": 0.0, "small": -0.2}

    gap = base_gap + adjustments.get(bucket, 0.0)
    turnover = _coerce_int(turnover_hint, 0)
    if turnover >= 150_000_000_000:
        gap += 0.2
    elif 0 < turnover <= 20_000_000_000:
        gap -= 0.2

    return {
        "bucket": bucket,
        "bucket_label": market_cap_bucket_label(bucket),
        "threshold": max(2.5, min(5.0, gap)),
        "market_cap": _coerce_int(marcap, 0),
        "turnover_hint": turnover,
    }
