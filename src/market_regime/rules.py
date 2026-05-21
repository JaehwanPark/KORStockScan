from datetime import datetime

import pandas as pd

from .schemas import MarketRegimeSnapshot
from .indicators import sma, rsi, macd, cross_under


MARKET_REGIME_SCORE_VERSION = "market_regime_continuous_v1"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _linear_between(value: float, x0: float, y0: float, x1: float, y1: float) -> float:
    if x0 == x1:
        return y1
    ratio = _clamp((value - x0) / (x1 - x0), 0.0, 1.0)
    return y0 + ((y1 - y0) * ratio)


def _vix_level_score(vix_close: float) -> float:
    if vix_close <= 0:
        return 0.0
    if vix_close <= 15.0:
        return 25.0
    if vix_close <= 25.0:
        return _linear_between(vix_close, 15.0, 25.0, 25.0, 15.0)
    if vix_close <= 35.0:
        return _linear_between(vix_close, 25.0, 15.0, 35.0, 0.0)
    return 0.0


def _fear_greed_level_score(value: float) -> float:
    if value <= 0:
        return 0.0
    if value <= 25.0:
        return 0.0
    if value <= 50.0:
        return _linear_between(value, 25.0, 0.0, 50.0, 10.0)
    if value <= 70.0:
        return _linear_between(value, 50.0, 10.0, 70.0, 20.0)
    if value <= 90.0:
        return _linear_between(value, 70.0, 20.0, 90.0, 15.0)
    return _linear_between(min(value, 100.0), 90.0, 15.0, 100.0, 10.0)


def _domestic_breadth_score(ma20_ratio: float | None, max_weight: float = 35.0) -> float:
    if ma20_ratio is None:
        return 0.0
    return _clamp((float(ma20_ratio) / 70.0) * max_weight, 0.0, max_weight)


def _oil_pullback_relief_score(snapshot: MarketRegimeSnapshot) -> float:
    drawdown_pct = float(snapshot.wti_from_recent_high_pct or 0.0)
    oil_rsi_turned = bool(snapshot.debug.get("oil_rsi_turned", False))
    score = 0.0

    if drawdown_pct <= -10.0:
        score = 10.0
    elif drawdown_pct <= -5.0:
        score = 7.0 + (_clamp(abs(drawdown_pct) - 5.0, 0.0, 5.0) / 5.0 * 3.0)

    if oil_rsi_turned or snapshot.wti_dead_cross:
        score = max(score, 5.0)

    return _clamp(score, 0.0, 10.0)


def _local_model_score(local_context: dict | None) -> float:
    if not isinstance(local_context, dict):
        return 0.0
    avg_bull = local_context.get("avg_bull")
    if avg_bull is None:
        return 0.0
    try:
        return _clamp(_linear_between(float(avg_bull), 45.0, 0.0, 65.0, 10.0), 0.0, 10.0)
    except (TypeError, ValueError):
        return 0.0


def market_regime_continuous_label(score: float, risk_on_min: float = 65.0, neutral_min: float = 45.0) -> str:
    if score >= risk_on_min:
        return "RISK_ON"
    if score >= neutral_min:
        return "NEUTRAL"
    return "RISK_OFF"


def apply_continuous_market_regime_score(
    snapshot: MarketRegimeSnapshot,
    local_context: dict | None = None,
) -> MarketRegimeSnapshot:
    ma20_ratio = None
    if isinstance(local_context, dict) and local_context.get("ma20_ratio") is not None:
        try:
            ma20_ratio = float(local_context.get("ma20_ratio"))
        except (TypeError, ValueError):
            ma20_ratio = None

    components = {
        "vix_level": _vix_level_score(float(snapshot.vix_close or 0.0)),
        "fear_greed_level": _fear_greed_level_score(float(snapshot.fng_value or 0.0)),
        "domestic_breadth": _domestic_breadth_score(ma20_ratio),
        "oil_relief": _oil_pullback_relief_score(snapshot),
        "local_model": _local_model_score(local_context),
    }
    total = sum(components.values())

    snapshot.swing_entry_recovery_gate_score = int(snapshot.swing_score or 0)
    snapshot.market_regime_component_scores = {
        key: round(float(value), 4)
        for key, value in components.items()
    }
    snapshot.market_regime_continuous_score = round(_clamp(float(total), 0.0, 100.0), 4)
    snapshot.market_regime_continuous_label = market_regime_continuous_label(
        snapshot.market_regime_continuous_score
    )
    snapshot.market_regime_score_version = MARKET_REGIME_SCORE_VERSION
    snapshot.oil_pullback_relief = bool(components["oil_relief"] > 0.0)

    has_market_data = bool(snapshot.vix_close > 0 and snapshot.fng_value > 0)
    has_local_context = ma20_ratio is not None or (
        isinstance(local_context, dict) and local_context.get("avg_bull") is not None
    )
    if has_market_data and has_local_context:
        snapshot.market_regime_source_quality = "valid"
    elif has_market_data:
        snapshot.market_regime_source_quality = "partial_local_context_missing"
    else:
        snapshot.market_regime_source_quality = "partial_market_data_missing"

    snapshot.debug["market_regime_continuous"] = {
        "version": snapshot.market_regime_score_version,
        "label_thresholds": {"risk_on_min_score": 65.0, "neutral_min_score": 45.0},
        "component_scores": snapshot.market_regime_component_scores,
        "source_quality": snapshot.market_regime_source_quality,
        "decision_authority": "risk_context_only",
        "runtime_effect": False,
    }
    return snapshot


def evaluate_market_regime(vix_df: pd.DataFrame, oil_df: pd.DataFrame, fng_data: dict | None = None) -> MarketRegimeSnapshot:
    snapshot = MarketRegimeSnapshot(timestamp=datetime.now())
    fng_data = fng_data if isinstance(fng_data, dict) else {}

    if vix_df is None or vix_df.empty:
        snapshot.reasons.append("VIX 데이터 부족")
        snapshot.risk_state = "NEUTRAL"
        return snapshot

    if oil_df is None or oil_df.empty:
        snapshot.reasons.append("원유 데이터 부족")
        snapshot.risk_state = "NEUTRAL"
        return snapshot

    vix = vix_df.copy()
    oil = oil_df.copy()

    # --- VIX 가공 ---
    vix["ma3"] = sma(vix["close"], 3)
    vix["below_ma3"] = cross_under(vix["close"], vix["ma3"])
    vix["down_day"] = vix["close"] < vix["close"].shift(1)

    # --- WTI 가공 ---
    oil["rsi14"] = rsi(oil["close"], 14)
    oil["macd"], oil["macd_signal"], oil["macd_hist"] = macd(oil["close"])
    oil["dead_cross"] = (
        (oil["macd"].shift(1) >= oil["macd_signal"].shift(1)) &
        (oil["macd"] < oil["macd_signal"])
    )
    oil["recent_high_20"] = oil["close"].rolling(20).max()
    oil["from_recent_high_pct"] = ((oil["close"] / oil["recent_high_20"]) - 1.0) * 100.0

    lv = vix.iloc[-1]
    lo = oil.iloc[-1]

    snapshot.vix_close = float(lv["close"]) if pd.notna(lv["close"]) else 0.0
    snapshot.vix_ma3 = float(lv["ma3"]) if pd.notna(lv["ma3"]) else 0.0
    snapshot.vix_peak_passed = bool(lv["below_ma3"]) if pd.notna(lv["below_ma3"]) else False
    snapshot.vix_two_day_down = bool(vix["down_day"].tail(2).all()) if len(vix) >= 2 else False
    snapshot.vix_extreme = snapshot.vix_close >= 35.0

    snapshot.wti_close = float(lo["close"]) if pd.notna(lo["close"]) else 0.0
    snapshot.wti_rsi = float(lo["rsi14"]) if pd.notna(lo["rsi14"]) else 0.0
    snapshot.wti_macd = float(lo["macd"]) if pd.notna(lo["macd"]) else 0.0
    snapshot.wti_macd_signal = float(lo["macd_signal"]) if pd.notna(lo["macd_signal"]) else 0.0
    snapshot.wti_dead_cross = bool(lo["dead_cross"]) if pd.notna(lo["dead_cross"]) else False
    snapshot.wti_from_recent_high_pct = float(lo["from_recent_high_pct"]) if pd.notna(lo["from_recent_high_pct"]) else 0.0

    oil_rsi_turned = False
    if len(oil) >= 2:
        prev_rsi = oil["rsi14"].iloc[-2]
        curr_rsi = oil["rsi14"].iloc[-1]
        if pd.notna(prev_rsi) and pd.notna(curr_rsi):
            oil_rsi_turned = (prev_rsi >= 70.0) and (curr_rsi < prev_rsi)

    snapshot.oil_reversal = (
        oil_rsi_turned or
        snapshot.wti_dead_cross or
        snapshot.wti_from_recent_high_pct <= -5.0
    )
    snapshot.oil_pullback_relief = snapshot.oil_reversal

    # --- Fear & Greed 가공 ---
    fng_curr = 0.0
    fng_prev = 0.0

    if isinstance(fng_data, dict):
        fng_curr = float(fng_data.get("value", 0.0) or 0.0)
        fng_prev = float(fng_data.get("previous_value", 0.0) or 0.0)

    snapshot.fng_value = fng_curr
    snapshot.fng_prev = fng_prev
    snapshot.fng_extreme_fear = fng_curr > 0 and fng_curr <= 25.0
    snapshot.fng_recovery = (
        (fng_prev <= 25.0 and fng_curr > fng_prev) or
        (fng_curr >= 30.0 and fng_curr > fng_prev)
    )

    # --- Score 기반 스윙 진입 판정 ---
    score = 0
    component_scores = {
        "vix": 0,
        "oil": 0,
        "fng": 0,
    }

    # VIX 비중
    if snapshot.vix_extreme and snapshot.vix_two_day_down:
        score += 40
        component_scores["vix"] = 40
        snapshot.reasons.append("VIX 극점 후 2일 연속 하락")
    elif snapshot.vix_peak_passed:
        score += 25
        component_scores["vix"] = 25
        snapshot.reasons.append("VIX 3일선 하향 이탈")

    # Oil 비중
    if snapshot.oil_reversal:
        score += 35
        component_scores["oil"] = 35
        snapshot.reasons.append("원유 반전 시그널")

    # Fear & Greed 비중
    if snapshot.fng_recovery:
        score += 20
        component_scores["fng"] = 20
        snapshot.reasons.append("공포탐욕지수 회복")
    elif snapshot.fng_extreme_fear:
        score -= 10
        component_scores["fng"] = -10
        snapshot.reasons.append("공포탐욕지수 극단적 공포 유지")

    snapshot.swing_score = score
    snapshot.swing_entry_recovery_gate_score = score
    snapshot.allow_swing_entry = score >= 70

    # 리스크 상태
    if snapshot.allow_swing_entry:
        snapshot.risk_state = "RISK_ON"
    elif score >= 45:
        snapshot.risk_state = "NEUTRAL"
    else:
        snapshot.risk_state = "RISK_OFF"

    # 변동성 모드
    if snapshot.vix_close >= 40.0:
        snapshot.volatility_mode = "EXTREME"
    elif snapshot.vix_close >= 30.0:
        snapshot.volatility_mode = "HIGH"
    else:
        snapshot.volatility_mode = "NORMAL"

    snapshot.debug = {
        "oil_rsi_turned": oil_rsi_turned,
        "fng_curr": fng_curr,
        "fng_prev": fng_prev,
        "score_threshold": 70,
        "component_scores": component_scores,
        "vix_signal": "extreme_two_day_down" if component_scores["vix"] == 40 else ("below_ma3" if component_scores["vix"] == 25 else "none"),
        "oil_signal": "reversal" if snapshot.oil_reversal else "none",
        "fng_signal": "recovery" if component_scores["fng"] == 20 else ("extreme_fear" if component_scores["fng"] == -10 else "none"),
    }

    snapshot.fng_description = str(fng_data.get("description", "") or "")
    apply_continuous_market_regime_score(snapshot)

    return snapshot
