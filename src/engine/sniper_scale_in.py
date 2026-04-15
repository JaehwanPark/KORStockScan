from datetime import datetime

from src.utils.constants import TRADING_RULES


def _base_result():
    return {
        "should_add": False,
        "add_type": None,
        "reason": "",
        "qty": 0,
        "price": 0,
    }


def _calc_held_minutes(stock):
    if stock.get('order_time'):
        return (datetime.now().timestamp() - float(stock['order_time'])) / 60.0
    if stock.get('buy_time'):
        try:
            bt = stock['buy_time']
            if isinstance(bt, datetime):
                b_dt = bt
            else:
                bt_str = str(bt)
                try:
                    b_dt = datetime.fromisoformat(bt_str)
                except Exception:
                    b_time = datetime.strptime(bt_str, '%H:%M:%S').time()
                    b_dt = datetime.combine(datetime.now().date(), b_time)
            return (datetime.now() - b_dt).total_seconds() / 60.0
        except Exception:
            pass
    return 0.0


def evaluate_scalping_avg_down(stock, profit_rate):
    """
    스캘핑 물타기(AVG_DOWN) 평가: 1차는 퍼센트 기반 단순 조건.
    TODO: VWAP/RSI/ATR 기반 필터 추가
    """
    result = _base_result()

    if not getattr(TRADING_RULES, 'SCALPING_ENABLE_AVG_DOWN', False):
        result["reason"] = "avg_down_disabled"
        return result

    max_count = int(getattr(TRADING_RULES, 'SCALPING_MAX_AVG_DOWN_COUNT', 0) or 0)
    avg_down_count = int(stock.get('avg_down_count', 0) or 0)
    if avg_down_count >= max_count:
        result["reason"] = "avg_down_count_limit"
        return result

    min_drop = float(getattr(TRADING_RULES, 'SCALPING_AVG_DOWN_MIN_DROP_PCT', -3.0))
    max_drop = float(getattr(TRADING_RULES, 'SCALPING_AVG_DOWN_MAX_DROP_PCT', -6.0))
    if not (profit_rate <= min_drop and profit_rate >= max_drop):
        result["reason"] = "drop_range_not_met"
        return result

    max_hold_min = float(getattr(TRADING_RULES, 'SCALP_TIME_LIMIT_MIN', 30) or 30)
    held_min = _calc_held_minutes(stock)
    if held_min > max_hold_min:
        result["reason"] = "held_too_long"
        return result

    result["should_add"] = True
    result["add_type"] = "AVG_DOWN"
    result["reason"] = "scalping_avg_down_ok"
    return result


def evaluate_scalping_pyramid(stock, profit_rate, peak_profit, is_new_high):
    """
    스캘핑 불타기(PYRAMID) 평가: 1차는 profit/peak 기반 단순 조건.
    TODO: VWAP/RSI/ATR 기반 필터 추가
    """
    result = _base_result()

    min_profit = float(getattr(TRADING_RULES, 'SCALPING_PYRAMID_MIN_PROFIT_PCT', 1.8))
    if profit_rate < min_profit:
        result["reason"] = "profit_not_enough"
        return result

    max_count = int(getattr(TRADING_RULES, 'SCALPING_MAX_PYRAMID_COUNT', 0) or 0)
    pyramid_count = int(stock.get('pyramid_count', 0) or 0)
    if pyramid_count >= max_count:
        result["reason"] = "pyramid_count_limit"
        return result

    drawdown_from_peak = float(peak_profit - profit_rate)
    if not (is_new_high or drawdown_from_peak <= 0.3):
        result["reason"] = "trend_not_strong"
        return result

    result["should_add"] = True
    result["add_type"] = "PYRAMID"
    result["reason"] = "scalping_pyramid_ok"
    return result


def evaluate_swing_avg_down(stock, profit_rate, market_regime):
    """
    스윙 물타기(AVG_DOWN) 평가: 1차는 퍼센트 기반 단순 조건.
    TODO: VWAP/RSI/ATR 기반 필터 추가
    """
    result = _base_result()

    if market_regime == 'BEAR' and getattr(TRADING_RULES, 'BLOCK_SWING_AVG_DOWN_IN_BEAR', True):
        result["reason"] = "bear_avg_down_blocked"
        return result

    max_count = int(getattr(TRADING_RULES, 'SWING_MAX_AVG_DOWN_COUNT', 0) or 0)
    avg_down_count = int(stock.get('avg_down_count', 0) or 0)
    if avg_down_count >= max_count:
        result["reason"] = "avg_down_count_limit"
        return result

    min_drop = float(getattr(TRADING_RULES, 'SWING_AVG_DOWN_MIN_DROP_PCT', -7.0))
    if profit_rate > min_drop:
        result["reason"] = "drop_not_enough"
        return result

    result["should_add"] = True
    result["add_type"] = "AVG_DOWN"
    result["reason"] = "swing_avg_down_ok"
    return result


def evaluate_swing_pyramid(stock, profit_rate, peak_profit):
    """
    스윙 불타기(PYRAMID) 평가: 1차는 profit/peak 기반 단순 조건.
    TODO: VWAP/RSI/ATR 기반 필터 추가
    """
    result = _base_result()

    min_profit = float(getattr(TRADING_RULES, 'SWING_PYRAMID_MIN_PROFIT_PCT', 5.0))
    if profit_rate < min_profit:
        result["reason"] = "profit_not_enough"
        return result

    max_count = int(getattr(TRADING_RULES, 'SWING_MAX_PYRAMID_COUNT', 0) or 0)
    pyramid_count = int(stock.get('pyramid_count', 0) or 0)
    if pyramid_count >= max_count:
        result["reason"] = "pyramid_count_limit"
        return result

    drawdown_from_peak = float(peak_profit - profit_rate)
    if drawdown_from_peak > 1.0:
        result["reason"] = "trend_not_strong"
        return result

    result["should_add"] = True
    result["add_type"] = "PYRAMID"
    result["reason"] = "swing_pyramid_ok"
    return result


def evaluate_scalping_reversal_add(stock, profit_rate, current_ai_score, held_sec):
    """
    역전 확인 추가매수(reversal_add) 평가.
    저점 미갱신 + AI 회복 + 수급 재개가 동시 확인될 때 1회 실행.
    """
    import statistics as _statistics

    result = _base_result()

    if not getattr(TRADING_RULES, 'REVERSAL_ADD_ENABLED', False):
        result["reason"] = "reversal_add_disabled"
        return result

    if stock.get('reversal_add_used'):
        result["reason"] = "reversal_add_used"
        return result

    pnl_min = float(getattr(TRADING_RULES, 'REVERSAL_ADD_PNL_MIN', -0.45))
    pnl_max = float(getattr(TRADING_RULES, 'REVERSAL_ADD_PNL_MAX', -0.10))
    if not (pnl_min <= profit_rate <= pnl_max):
        result["reason"] = f"pnl_out_of_range({profit_rate:.2f})"
        return result

    min_hold = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_HOLD_SEC', 20))
    max_hold = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MAX_HOLD_SEC', 120))
    if not (min_hold <= held_sec <= max_hold):
        result["reason"] = f"hold_sec_out_of_range({held_sec}s)"
        return result

    # 저점 미갱신 확인
    floor = float(stock.get('reversal_add_profit_floor', 0.0))
    margin = float(getattr(TRADING_RULES, 'REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN', 0.05))
    if profit_rate < floor - margin:
        result["reason"] = "low_broken"
        return result

    # AI 점수 최소 기준
    min_ai = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_AI_SCORE', 60))
    if current_ai_score < min_ai:
        result["reason"] = f"ai_score_too_low({current_ai_score})"
        return result

    # AI 회복 방향성 (바닥 대비 +15pt OR 2연속 상승)
    ai_bottom = int(stock.get('reversal_add_ai_bottom', 100))
    recovery_delta = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_AI_RECOVERY_DELTA', 15))
    ai_hist = list(stock.get('reversal_add_ai_history', []))
    recovering_delta = (current_ai_score >= ai_bottom + recovery_delta)
    recovering_consec = (len(ai_hist) >= 2 and ai_hist[-1] > ai_hist[-2] and current_ai_score > ai_hist[-1])
    if not (recovering_delta or recovering_consec):
        result["reason"] = "ai_not_recovering"
        return result

    # AI 고착 저점 차단
    if len(ai_hist) >= 4:
        try:
            std = _statistics.stdev(ai_hist)
            avg = sum(ai_hist) / len(ai_hist)
            if std <= 2 and avg < 45:
                result["reason"] = "ai_stuck_at_bottom"
                return result
        except Exception:
            pass

    # 수급 재개 조건 (4개 중 3개, 피처 없으면 buy_pressure만 확인)
    feat = stock.get('last_reversal_features', {})
    if feat:
        checks = [
            feat.get('buy_pressure_10t', 0) >= getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_BUY_PRESSURE', 55),
            feat.get('tick_acceleration_ratio', 0) >= getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_TICK_ACCEL', 0.95),
            not feat.get('large_sell_print_detected', True),
            feat.get('curr_vs_micro_vwap_bp', -999) >= getattr(TRADING_RULES, 'REVERSAL_ADD_VWAP_BP_MIN', -5.0),
        ]
        if sum(checks) < 3:
            result["reason"] = f"supply_conditions_not_met({sum(checks)}/4)"
            return result
    else:
        # 피처 미사용 엔진: buy_pressure만 확인
        bp = float(stock.get('last_reversal_features', {}).get('buy_pressure_10t', 50.0))
        if bp < getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_BUY_PRESSURE', 55):
            result["reason"] = "buy_pressure_not_met(no_features)"
            return result

    result["should_add"] = True
    result["add_type"] = "AVG_DOWN"
    result["reason"] = "reversal_add_ok"
    return result


def calc_scale_in_qty(stock, curr_price, deposit, add_type, strategy, add_reason=None):
    """
    추가매수 수량 계산 (1차 보수적 템플릿).
    - 남은 허용 포지션(최대 비중) 기반 cap 우선
    - 템플릿은 기존 보유수량 비율 기반
    """
    if curr_price <= 0 or deposit <= 0:
        return 0

    buy_qty = int(float(stock.get('buy_qty', 0) or 0))
    if buy_qty <= 0:
        return 0

    max_pos_pct = float(getattr(TRADING_RULES, 'MAX_POSITION_PCT', 0.30) or 0.30)
    max_budget = deposit * max_pos_pct
    current_value = buy_qty * curr_price
    remaining_budget = max(max_budget - current_value, 0)
    if remaining_budget <= 0:
        return 0

    raw_strategy = (strategy or "").upper()
    add_type = (add_type or "").upper()

    if raw_strategy == 'SCALPING':
        if add_type == 'AVG_DOWN' and (add_reason or '') == 'reversal_add_ok':
            ratio = float(getattr(TRADING_RULES, 'REVERSAL_ADD_SIZE_RATIO', 0.33) or 0.33)
            if ratio <= 0:
                ratio = 0.33
        else:
            ratio = 0.50
    else:
        ratio = 0.50 if add_type == 'AVG_DOWN' else 0.30

    template_qty = int(buy_qty * ratio)
    if template_qty <= 0:
        return 0

    cap_qty = int((remaining_budget * 0.95) // curr_price)
    qty = min(template_qty, cap_qty)
    return qty if qty >= 1 else 0
