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


def calc_scale_in_qty(stock, curr_price, deposit, add_type, strategy):
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
        ratio = 0.50
    else:
        ratio = 0.50 if add_type == 'AVG_DOWN' else 0.30

    template_qty = int(buy_qty * ratio)
    if template_qty <= 0:
        return 0

    cap_qty = int((remaining_budget * 0.95) // curr_price)
    qty = min(template_qty, cap_qty)
    return qty if qty >= 1 else 0
