from datetime import datetime

import pandas as pd

from .schemas import MarketRegimeSnapshot
from .indicators import sma, rsi, macd, cross_under


def evaluate_market_regime(vix_df: pd.DataFrame, oil_df: pd.DataFrame, fng_data: dict | None = None) -> MarketRegimeSnapshot:
    snapshot = MarketRegimeSnapshot(timestamp=datetime.now())

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

    # VIX 비중
    if snapshot.vix_extreme and snapshot.vix_two_day_down:
        score += 40
        snapshot.reasons.append("VIX 극점 후 2일 연속 하락")
    elif snapshot.vix_peak_passed:
        score += 25
        snapshot.reasons.append("VIX 3일선 하향 이탈")

    # Oil 비중
    if snapshot.oil_reversal:
        score += 35
        snapshot.reasons.append("원유 반전 시그널")

    # Fear & Greed 비중
    if snapshot.fng_recovery:
        score += 20
        snapshot.reasons.append("공포탐욕지수 회복")
    elif snapshot.fng_extreme_fear:
        score -= 10
        snapshot.reasons.append("공포탐욕지수 극단적 공포 유지")

    snapshot.swing_score = score
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
    }

    snapshot.fng_description = str(fng_data.get("description", "") or "")

    return snapshot