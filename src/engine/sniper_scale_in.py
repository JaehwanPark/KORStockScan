import statistics
import math
from datetime import datetime, timedelta, time as dt_time

from src.utils.constants import TRADING_RULES
from src.utils import kiwoom_utils

_DEFAULT_SCALE_IN_RATIO = 0.50
_DEFAULT_SWING_PYRAMID_RATIO = 0.30
_SCALE_IN_RULES = {
    ("SCALPING", "AVG_DOWN", "reversal_add_ok"): {
        "ratio_rule": "REVERSAL_ADD_SIZE_RATIO",
        "default_ratio": 0.33,
        "floor_rule": "REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED",
        "floor_default": True,
    },
    ("SCALPING", "AVG_DOWN", "default"): {
        "ratio": _DEFAULT_SCALE_IN_RATIO,
    },
    ("SCALPING", "PYRAMID", "default"): {
        "ratio": _DEFAULT_SCALE_IN_RATIO,
        "floor_rule": "SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED",
        "floor_default": False,
    },
    ("DEFAULT", "AVG_DOWN", "default"): {
        "ratio": _DEFAULT_SCALE_IN_RATIO,
    },
    ("DEFAULT", "PYRAMID", "default"): {
        "ratio": _DEFAULT_SWING_PYRAMID_RATIO,
    },
}


def _base_result():
    return {
        "should_add": False,
        "add_type": None,
        "reason": "",
        "qty": 0,
        "price": 0,
    }


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().lower() in {"", "nan", "nat", "none", "inf", "+inf", "-inf"}:
            return default
        numeric = float(value)
        if not math.isfinite(numeric):
            return default
        return numeric
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(_safe_float(value, default))
    except Exception:
        return default


def _best_levels_from_ws(ws_data):
    ws_data = ws_data or {}
    best_bid = _safe_int(ws_data.get("best_bid") or ws_data.get("bid") or ws_data.get("bid_price"), 0)
    best_ask = _safe_int(ws_data.get("best_ask") or ws_data.get("ask") or ws_data.get("ask_price"), 0)
    orderbook = ws_data.get("orderbook") or {}
    bids = orderbook.get("bids") or []
    asks = orderbook.get("asks") or []
    if best_bid <= 0 and bids:
        bid_prices = [_safe_int(level.get("price") if isinstance(level, dict) else level, 0) for level in bids]
        best_bid = max([price for price in bid_prices if price > 0], default=0)
    if best_ask <= 0 and asks:
        ask_prices = [_safe_int(level.get("price") if isinstance(level, dict) else level, 0) for level in asks]
        best_ask = min([price for price in ask_prices if price > 0], default=0)
    return best_bid, best_ask


def _spread_bps(best_bid, best_ask):
    if best_bid <= 0 or best_ask <= 0 or best_ask < best_bid:
        return None
    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return None
    return ((best_ask - best_bid) / mid) * 10000.0


def _ticks_down(price, ticks=1):
    if price <= 0:
        return 0
    try:
        return int(kiwoom_utils.get_price_ticks_down(int(price), max(1, int(ticks))))
    except Exception:
        tick = max(1, int(kiwoom_utils.get_tick_size(int(price)) or 1))
        return max(0, int(price) - (tick * max(1, int(ticks))))


def _combine_time_with_current_session_date(raw_time, now_dt):
    combined = datetime.combine(now_dt.date(), raw_time)
    if combined > now_dt:
        combined -= timedelta(days=1)
    return combined


def _resolve_buy_time_as_datetime(raw_buy_time, now_dt):
    if isinstance(raw_buy_time, datetime):
        return raw_buy_time
    if isinstance(raw_buy_time, dt_time):
        return _combine_time_with_current_session_date(raw_buy_time, now_dt)
    if isinstance(raw_buy_time, (int, float)):
        return datetime.fromtimestamp(float(raw_buy_time))
    if isinstance(raw_buy_time, str):
        bt_str = raw_buy_time.strip()
        if not bt_str:
            return None
        try:
            return datetime.fromisoformat(bt_str)
        except ValueError:
            try:
                return _combine_time_with_current_session_date(datetime.strptime(bt_str, '%H:%M:%S').time(), now_dt)
            except ValueError:
                return None
    return None


def resolve_buy_time_as_datetime(raw_buy_time, now_dt):
    """공용 buy_time 파서. state handler와 scale-in이 동일 규칙을 공유한다."""
    return _resolve_buy_time_as_datetime(raw_buy_time, now_dt)


def _calc_held_minutes(stock):
    now_dt = datetime.now()
    raw_order_time = stock.get('order_time')
    if raw_order_time:
        try:
            return max(0.0, (now_dt.timestamp() - float(raw_order_time)) / 60.0)
        except (TypeError, ValueError):
            pass

    raw_buy_time = stock.get('buy_time')
    if raw_buy_time:
        buy_dt = _resolve_buy_time_as_datetime(raw_buy_time, now_dt)
        if buy_dt is not None:
            return max(0.0, (now_dt - buy_dt).total_seconds() / 60.0)
    return 0.0


def resolve_holding_elapsed_sec(stock, *, now_dt=None, now_ts=None):
    """보유 경과초 계산을 공용화해 scale-in/holding handler가 같은 기준을 쓴다."""
    current_dt = now_dt or datetime.now()
    current_ts = float(now_ts if now_ts is not None else current_dt.timestamp())

    raw_order_time = stock.get("order_time")
    if raw_order_time not in (None, "", 0, "0"):
        try:
            return max(0, int(current_ts - float(raw_order_time)))
        except (TypeError, ValueError):
            pass

    raw_buy_time = stock.get("buy_time")
    if not raw_buy_time:
        return 0

    buy_dt = resolve_buy_time_as_datetime(raw_buy_time, current_dt)
    if buy_dt is None:
        return 0
    return max(0, int((current_dt - buy_dt).total_seconds()))


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

    drawdown_from_peak = float(peak_profit - profit_rate)
    if not (is_new_high or drawdown_from_peak <= 0.3):
        result["reason"] = "trend_not_strong"
        return result

    result["should_add"] = True
    result["add_type"] = "PYRAMID"
    result["reason"] = "scalping_pyramid_ok"
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

    drawdown_from_peak = float(peak_profit - profit_rate)
    if drawdown_from_peak > 1.0:
        result["reason"] = "trend_not_strong"
        return result

    result["should_add"] = True
    result["add_type"] = "PYRAMID"
    result["reason"] = "swing_pyramid_ok"
    return result


def evaluate_swing_avg_down(stock, profit_rate, peak_profit, current_ai_score=50, held_sec=0):
    """
    스윙 물타기(AVG_DOWN) 관찰 평가.
    실주문 전환용이 아니라 dry-run/probe가 live-equivalent 후행 데이터를 모으기 위한 후보다.
    """
    result = _base_result()

    if not bool(getattr(TRADING_RULES, 'SWING_ENABLE_AVG_DOWN_SIMULATION', True)):
        result["reason"] = "swing_avg_down_sim_disabled"
        return result

    loss_min = float(getattr(TRADING_RULES, 'SWING_AVG_DOWN_MIN_LOSS_PCT', -3.0))
    loss_max = float(getattr(TRADING_RULES, 'SWING_AVG_DOWN_MAX_LOSS_PCT', -0.8))
    if not (loss_min <= profit_rate <= loss_max):
        result["reason"] = "loss_not_in_avg_down_band"
        return result

    max_peak = float(getattr(TRADING_RULES, 'SWING_AVG_DOWN_MAX_PEAK_PROFIT_PCT', 1.0))
    if peak_profit > max_peak:
        result["reason"] = "prior_green_too_high"
        return result

    min_hold_sec = int(getattr(TRADING_RULES, 'SWING_AVG_DOWN_MIN_HOLD_SEC', 300))
    if int(held_sec or 0) < min_hold_sec:
        result["reason"] = "hold_sec_not_enough"
        return result

    result["should_add"] = True
    result["add_type"] = "AVG_DOWN"
    result["reason"] = "swing_avg_down_ok"
    result["profit_rate"] = profit_rate
    result["peak_profit"] = peak_profit
    result["current_ai_score"] = current_ai_score
    result["held_sec"] = held_sec
    return result


def _check_reversal_add_pnl_range(profit_rate):
    pnl_min = float(getattr(TRADING_RULES, 'REVERSAL_ADD_PNL_MIN', -0.45))
    pnl_max = float(getattr(TRADING_RULES, 'REVERSAL_ADD_PNL_MAX', -0.10))
    if pnl_min <= profit_rate <= pnl_max:
        return None
    return f"pnl_out_of_range({profit_rate:.2f})"


def _check_reversal_add_hold_sec(held_sec):
    min_hold = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_HOLD_SEC', 20))
    max_hold = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MAX_HOLD_SEC', 120))
    if min_hold <= held_sec <= max_hold:
        return None
    return f"hold_sec_out_of_range({held_sec}s)"


def _check_reversal_add_low_floor(stock, profit_rate):
    floor = float(stock.get('reversal_add_profit_floor', 0.0))
    margin = float(getattr(TRADING_RULES, 'REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN', 0.05))
    if profit_rate < floor - margin:
        return "low_broken"
    return None


def _check_reversal_add_ai_recovery(stock, current_ai_score):
    min_ai = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_AI_SCORE', 60))
    if current_ai_score < min_ai:
        return f"ai_score_too_low({current_ai_score})"

    ai_bottom = int(stock.get('reversal_add_ai_bottom', 100))
    recovery_delta = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_AI_RECOVERY_DELTA', 15))
    ai_hist = list(stock.get('reversal_add_ai_history', []))
    recovering_delta = current_ai_score >= ai_bottom + recovery_delta
    recovering_consec = len(ai_hist) >= 2 and ai_hist[-1] > ai_hist[-2] and current_ai_score > ai_hist[-1]
    if not (recovering_delta or recovering_consec):
        return "ai_not_recovering"

    if len(ai_hist) >= 4:
        try:
            std = statistics.stdev(ai_hist)
            avg = sum(ai_hist) / len(ai_hist)
            if std <= 2 and avg < 45:
                return "ai_stuck_at_bottom"
        except statistics.StatisticsError:
            pass
    return None


def _check_reversal_add_supply(stock):
    feat = stock.get('last_reversal_features', {})
    min_buy_pressure = getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_BUY_PRESSURE', 55)
    if feat:
        checks = [
            feat.get('buy_pressure_10t', 0) >= min_buy_pressure,
            feat.get('tick_acceleration_ratio', 0) >= getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_TICK_ACCEL', 0.95),
            not feat.get('large_sell_print_detected', True),
            feat.get('curr_vs_micro_vwap_bp', -999) >= getattr(TRADING_RULES, 'REVERSAL_ADD_VWAP_BP_MIN', -5.0),
        ]
        passed_checks = sum(checks)
        if passed_checks < 3:
            return f"supply_conditions_not_met({passed_checks}/4)"
        return None

    bp = float(stock.get('last_reversal_features', {}).get('buy_pressure_10t', 50.0))
    if bp < min_buy_pressure:
        return "buy_pressure_not_met(no_features)"
    return None


def _build_reversal_add_probe(stock, profit_rate, current_ai_score, held_sec):
    pnl_min = float(getattr(TRADING_RULES, 'REVERSAL_ADD_PNL_MIN', -0.45))
    pnl_max = float(getattr(TRADING_RULES, 'REVERSAL_ADD_PNL_MAX', -0.10))
    min_hold = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_HOLD_SEC', 20))
    max_hold = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MAX_HOLD_SEC', 120))
    floor = float(stock.get('reversal_add_profit_floor', 0.0))
    margin = float(getattr(TRADING_RULES, 'REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN', 0.05))
    min_ai = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_AI_SCORE', 60))
    ai_bottom = int(stock.get('reversal_add_ai_bottom', 100))
    recovery_delta = int(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_AI_RECOVERY_DELTA', 15))
    ai_hist = list(stock.get('reversal_add_ai_history', []))
    recovering_delta = current_ai_score >= ai_bottom + recovery_delta
    recovering_consec = len(ai_hist) >= 2 and ai_hist[-1] > ai_hist[-2] and current_ai_score > ai_hist[-1]
    feat = stock.get('last_reversal_features', {}) or {}
    min_buy_pressure = float(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_BUY_PRESSURE', 55) or 55)
    min_tick_accel = float(getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_TICK_ACCEL', 0.95) or 0.95)
    min_micro_vwap_bp = float(getattr(TRADING_RULES, 'REVERSAL_ADD_VWAP_BP_MIN', -5.0) or -5.0)

    buy_pressure = _safe_float(feat.get('buy_pressure_10t'), 50.0)
    tick_accel = _safe_float(feat.get('tick_acceleration_ratio'), 0.0)
    micro_vwap_bp = _safe_float(feat.get('curr_vs_micro_vwap_bp'), -999.0)
    large_sell_print = bool(feat.get('large_sell_print_detected', False))
    supply_checks = {
        "buy_pressure_ok": buy_pressure >= min_buy_pressure,
        "tick_accel_ok": tick_accel >= min_tick_accel,
        "large_sell_absent_ok": not large_sell_print,
        "micro_vwap_ok": micro_vwap_bp >= min_micro_vwap_bp,
    }
    supply_pass_count = sum(1 for ok in supply_checks.values() if ok)
    supply_ok = supply_pass_count >= 3 if feat else buy_pressure >= min_buy_pressure

    probe = {
        "reversal_add_used": bool(stock.get('reversal_add_used')),
        "profit_rate": round(float(profit_rate), 4),
        "pnl_min": round(pnl_min, 4),
        "pnl_max": round(pnl_max, 4),
        "pnl_ok": pnl_min <= profit_rate <= pnl_max,
        "held_sec": int(held_sec),
        "min_hold_sec": min_hold,
        "max_hold_sec": max_hold,
        "hold_ok": min_hold <= held_sec <= max_hold,
        "profit_floor": round(floor, 4),
        "floor_margin": round(margin, 4),
        "low_floor_ok": profit_rate >= floor - margin,
        "current_ai_score": int(current_ai_score),
        "min_ai_score": min_ai,
        "ai_score_ok": current_ai_score >= min_ai,
        "ai_bottom": ai_bottom,
        "min_ai_recovery_delta": recovery_delta,
        "ai_recovering_delta_ok": recovering_delta,
        "ai_recovering_consec_ok": recovering_consec,
        "ai_recover_ok": recovering_delta or recovering_consec,
        "ai_hist_len": len(ai_hist),
        "buy_pressure_10t": round(float(buy_pressure), 4),
        "min_buy_pressure": round(min_buy_pressure, 4),
        "tick_acceleration_ratio": round(float(tick_accel), 4),
        "min_tick_accel": round(min_tick_accel, 4),
        "curr_vs_micro_vwap_bp": round(float(micro_vwap_bp), 4),
        "min_micro_vwap_bp": round(min_micro_vwap_bp, 4),
        "large_sell_print_detected": large_sell_print,
        "supply_pass_count": supply_pass_count if feat else (1 if supply_ok else 0),
        "supply_ok": supply_ok,
        "has_reversal_features": bool(feat),
    }
    probe.update(supply_checks)
    return probe


def evaluate_scalping_reversal_add(stock, profit_rate, current_ai_score, held_sec):
    """
    역전 확인 추가매수(reversal_add) 평가.
    저점 미갱신 + AI 회복 + 수급 재개가 동시 확인될 때 1회 실행.
    """
    result = _base_result()
    probe = _build_reversal_add_probe(stock, profit_rate, current_ai_score, held_sec)
    result["probe"] = probe

    if not getattr(TRADING_RULES, 'REVERSAL_ADD_ENABLED', False):
        result["reason"] = "reversal_add_disabled"
        return result

    for reason in (
        _check_reversal_add_pnl_range(profit_rate),
        _check_reversal_add_hold_sec(held_sec),
        _check_reversal_add_low_floor(stock, profit_rate),
        _check_reversal_add_ai_recovery(stock, current_ai_score),
        _check_reversal_add_supply(stock),
    ):
        if reason:
            result["reason"] = reason
            return result

    result["should_add"] = True
    result["add_type"] = "AVG_DOWN"
    result["reason"] = "reversal_add_ok"
    return result


def resolve_scale_in_order_price(stock, ws_data, action, *, strategy=None, curr_price=None):
    """
    SCALPING 추가매수 주문 직전 P1 가격 resolver.
    신규 BUY resolver와 분리해 AVG_DOWN/PYRAMID가 현재가 그대로 추격 제출되는 경로를 차단한다.
    """
    ws_data = ws_data or {}
    action = action or {}
    raw_strategy = (strategy or stock.get("strategy") or "").upper()
    normalized_strategy = "SCALPING" if raw_strategy in {"SCALPING", "SCALP"} else raw_strategy
    add_type = (action.get("add_type") or "").upper()
    curr_price = _safe_int(curr_price if curr_price is not None else ws_data.get("curr"), 0)

    result = {
        "allowed": False,
        "order_price": 0,
        "reason": "",
        "price_source": "",
        "curr_price": curr_price,
        "best_bid": 0,
        "best_ask": 0,
        "spread_bps": None,
        "max_spread_bps": float(getattr(TRADING_RULES, "SCALPING_SCALE_IN_MAX_SPREAD_BPS", 80.0) or 80.0),
        "defensive_ticks": 1,
        "defensive_price": 0,
        "curr_vs_micro_vwap_bp": _safe_float(
            (stock.get("last_reversal_features") or {}).get("curr_vs_micro_vwap_bp"),
            0.0,
        ),
        "max_micro_vwap_bps": float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS", 60.0) or 60.0),
        "resolver_enabled": bool(getattr(TRADING_RULES, "SCALPING_SCALE_IN_PRICE_RESOLVER_ENABLED", True)),
    }

    if normalized_strategy != "SCALPING":
        result.update({"allowed": True, "order_price": 0, "reason": "non_scalping_market", "price_source": "market"})
        return result

    if add_type not in {"AVG_DOWN", "PYRAMID"}:
        result["reason"] = "invalid_add_type"
        return result
    if curr_price <= 0:
        result["reason"] = "invalid_curr_price"
        return result

    best_bid, best_ask = _best_levels_from_ws(ws_data)
    spread_bps = _spread_bps(best_bid, best_ask)
    defensive_price = _ticks_down(curr_price, result["defensive_ticks"])
    result.update({
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_bps": spread_bps,
        "defensive_price": defensive_price,
    })

    if not result["resolver_enabled"]:
        result.update({"allowed": True, "order_price": curr_price, "reason": "resolver_disabled_legacy_curr", "price_source": "curr"})
        return result

    if best_bid <= 0 and best_ask <= 0:
        result["reason"] = "invalid_quote"
        return result
    if spread_bps is None:
        result["reason"] = "invalid_spread"
        return result

    max_spread_bps = result["max_spread_bps"]
    if bool(getattr(TRADING_RULES, "SCALPING_PYRAMID_PRICE_GUARD_ENABLED", True)):
        max_spread_bps = min(
            max_spread_bps,
            float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_SPREAD_BPS", max_spread_bps) or max_spread_bps),
        )
        result["max_spread_bps"] = max_spread_bps
    if spread_bps > max_spread_bps:
        result["reason"] = f"spread_bps>{max_spread_bps:.1f}"
        return result

    micro_vwap_bp = result["curr_vs_micro_vwap_bp"]
    if add_type == "PYRAMID" and micro_vwap_bp > result["max_micro_vwap_bps"]:
        result["reason"] = f"micro_vwap_bp>{result['max_micro_vwap_bps']:.1f}"
        return result
    if add_type == "AVG_DOWN":
        min_micro_vwap = float(getattr(TRADING_RULES, "REVERSAL_ADD_VWAP_BP_MIN", -5.0) or -5.0)
        result["min_micro_vwap_bps"] = min_micro_vwap
        if micro_vwap_bp < min_micro_vwap:
            result["reason"] = f"micro_vwap_bp<{min_micro_vwap:.1f}"
            return result

    if best_bid > 0 and best_bid < curr_price:
        order_price = best_bid
        source = "best_bid"
    elif defensive_price > 0 and defensive_price < curr_price:
        order_price = defensive_price
        source = "defensive_ticks"
    elif best_bid > 0:
        order_price = min(best_bid, defensive_price or best_bid)
        source = "best_bid_defensive_clamp"
    else:
        order_price = defensive_price
        source = "defensive_ticks"

    if order_price <= 0 or order_price >= curr_price:
        result["reason"] = "resolved_price_invalid"
        result["order_price"] = int(order_price or 0)
        result["price_source"] = source
        return result

    result.update({"allowed": True, "order_price": int(order_price), "reason": "scale_in_price_resolved", "price_source": source})
    return result


def calc_scale_in_qty(stock, curr_price, deposit, add_type, strategy, add_reason=None):
    """
    추가매수 수량 계산 (1차 보수적 템플릿).
    - 남은 허용 포지션(최대 비중) 기반 cap 우선
    - 템플릿은 기존 보유수량 비율 기반
    """
    details = describe_scale_in_qty(
        stock=stock,
        curr_price=curr_price,
        deposit=deposit,
        add_type=add_type,
        strategy=strategy,
        add_reason=add_reason,
    )
    return int(details["qty"])


def _zero_scale_in_details(*, remaining_budget=0, cap_qty=0, floor_applied=False):
    return {
        "qty": 0,
        "template_qty": 0,
        "cap_qty": cap_qty,
        "remaining_budget": remaining_budget,
        "floor_applied": floor_applied,
    }


def _resolve_scale_in_ratio(raw_strategy, add_type, add_reason):
    rule = _resolve_scale_in_rule(raw_strategy, add_type, add_reason)
    ratio_rule = rule.get("ratio_rule")
    if ratio_rule:
        default_ratio = float(rule.get("default_ratio", _DEFAULT_SCALE_IN_RATIO) or _DEFAULT_SCALE_IN_RATIO)
        ratio = float(getattr(TRADING_RULES, ratio_rule, default_ratio) or default_ratio)
        return ratio if ratio > 0 else default_ratio
    return float(rule.get("ratio", _DEFAULT_SCALE_IN_RATIO))


def _resolve_scale_in_rule(raw_strategy, add_type, add_reason):
    normalized_reason = add_reason if add_reason == "reversal_add_ok" else "default"
    if raw_strategy == "SCALPING":
        key = (raw_strategy, add_type, normalized_reason)
        if key in _SCALE_IN_RULES:
            return _SCALE_IN_RULES[key]
        return _SCALE_IN_RULES[(raw_strategy, add_type, "default")]
    return _SCALE_IN_RULES[("DEFAULT", add_type, "default")]


def _apply_scale_in_template_floor(*, raw_strategy, add_type, add_reason, template_qty, cap_qty):
    floor_applied = False
    adjusted_template_qty = template_qty
    rule = _resolve_scale_in_rule(raw_strategy, add_type, add_reason)

    floor_rule = rule.get("floor_rule")
    if (
        floor_rule
        and bool(
            getattr(
                TRADING_RULES,
                floor_rule,
                rule.get("floor_default", False),
            )
        )
        and adjusted_template_qty <= 0
        and cap_qty >= 1
    ):
        adjusted_template_qty = 1
        floor_applied = True

    return adjusted_template_qty, floor_applied


def describe_scale_in_qty(stock, curr_price, deposit, add_type, strategy, add_reason=None):
    """추가매수 수량과 zero_qty 원인을 함께 반환한다."""
    if curr_price <= 0 or deposit <= 0:
        return _zero_scale_in_details()

    buy_qty = _safe_int(stock.get('buy_qty'), 0)
    if buy_qty <= 0:
        return _zero_scale_in_details()

    max_pos_pct = float(getattr(TRADING_RULES, 'MAX_POSITION_PCT', 0.30) or 0.30)
    max_budget = deposit * max_pos_pct
    current_value = buy_qty * curr_price
    remaining_budget = max(max_budget - current_value, 0)
    if remaining_budget <= 0:
        return _zero_scale_in_details(remaining_budget=remaining_budget)

    raw_strategy = (strategy or "").upper()
    add_type = (add_type or "").upper()
    add_reason = (add_reason or '')

    ratio = _resolve_scale_in_ratio(raw_strategy, add_type, add_reason)

    template_qty = int(buy_qty * ratio)
    cap_qty = int((remaining_budget * 0.95) // curr_price)
    template_qty, floor_applied = _apply_scale_in_template_floor(
        raw_strategy=raw_strategy,
        add_type=add_type,
        add_reason=add_reason,
        template_qty=template_qty,
        cap_qty=cap_qty,
    )
    if template_qty <= 0:
        return _zero_scale_in_details(
            remaining_budget=remaining_budget,
            cap_qty=cap_qty,
            floor_applied=floor_applied,
        )

    qty = min(template_qty, cap_qty)
    return {
        "qty": qty if qty >= 1 else 0,
        "template_qty": template_qty,
        "cap_qty": cap_qty,
        "remaining_budget": remaining_budget,
        "floor_applied": floor_applied,
    }


def describe_dynamic_scale_in_qty(
    stock,
    resolved_price,
    deposit,
    add_type,
    strategy,
    *,
    add_reason=None,
    price_resolution=None,
    action=None,
):
    """추가매수 수량을 safety guard와 position cap 안에서 결정하고 provenance를 남긴다."""
    legacy = describe_scale_in_qty(
        stock=stock,
        curr_price=resolved_price,
        deposit=deposit,
        add_type=add_type,
        strategy=strategy,
        add_reason=add_reason,
    )
    details = dict(legacy)
    details.update(
        {
            "would_qty": int(legacy.get("qty", 0) or 0),
            "effective_qty": int(legacy.get("qty", 0) or 0),
            "qty_reason": "legacy_template",
            "dynamic_enabled": bool(getattr(TRADING_RULES, "SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED", True)),
            "effective_qty_cap": 0,
            "sim_uncapped_qty": bool(
                stock.get("scalp_live_simulator")
                or str(stock.get("simulation_book") or "") == "scalp_ai_buy_all"
            ),
        }
    )

    raw_strategy = (strategy or "").upper()
    normalized_strategy = "SCALPING" if raw_strategy in {"SCALPING", "SCALP"} else raw_strategy
    add_type = (add_type or "").upper()
    if normalized_strategy in {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}:
        details["dynamic_enabled"] = bool(getattr(TRADING_RULES, "SWING_SCALE_IN_DYNAMIC_QTY_ENABLED", True))
        details["effective_qty_cap"] = int(getattr(TRADING_RULES, "SWING_SCALE_IN_EFFECTIVE_QTY_CAP", 0) or 0)
        details["sim_uncapped_qty"] = bool(
            stock.get("swing_live_order_dry_run")
            or stock.get("swing_intraday_probe")
            or str(stock.get("simulation_book") or "").startswith("swing")
        )
    if normalized_strategy not in {"SCALPING", "KOSPI_ML", "KOSDAQ_ML", "MAIN"} or not details["dynamic_enabled"]:
        return details

    cap_qty = int(details.get("cap_qty", 0) or 0)
    configured_effective_cap = int(details.get("effective_qty_cap", 0) or 0)
    if details["sim_uncapped_qty"]:
        configured_effective_cap = 0
        details["effective_qty_cap"] = 0
    effective_cap = configured_effective_cap if configured_effective_cap > 0 else cap_qty
    if resolved_price <= 0 or deposit <= 0:
        details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "invalid_price_or_deposit"})
        return details
    if not (price_resolution or {}).get("allowed", False):
        details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "price_resolution_blocked"})
        return details

    scalp_budget_qty = None
    scalp_min_one_share_floor_applied = False
    if normalized_strategy == "SCALPING" and not details["sim_uncapped_qty"]:
        current_ai_score_for_ratio = _safe_float(
            (action or {}).get("current_ai_score", stock.get("current_ai_score", (stock.get("rt_ai_prob") or 0) * 100)),
            0.0,
        )
        min_ratio = float(getattr(TRADING_RULES, "INVEST_RATIO_SCALPING_MIN", 0.10) or 0.10)
        max_ratio = float(getattr(TRADING_RULES, "INVEST_RATIO_SCALPING_MAX", 0.30) or 0.30)
        if max_ratio < min_ratio:
            min_ratio, max_ratio = max_ratio, min_ratio
        score = max(0.0, min(100.0, current_ai_score_for_ratio))
        scale_in_ratio = min_ratio + (score / 100.0) * (max_ratio - min_ratio)
        target_budget = max(float(deposit) * float(scale_in_ratio), 0.0)
        safe_budget = target_budget * float(getattr(TRADING_RULES, "BUY_BUDGET_SAFETY_RATIO", 0.95) or 0.95)
        scalp_budget_qty = int(safe_budget // resolved_price)
        min_one_share_floor_enabled = bool(
            getattr(TRADING_RULES, "SCALPING_SCALE_IN_MIN_ONE_SHARE_FLOOR_ENABLED", True)
        )
        if scalp_budget_qty <= 0 and min_one_share_floor_enabled and float(deposit) >= float(resolved_price):
            scalp_budget_qty = 1
            scalp_min_one_share_floor_applied = True
        cap_qty = max(0, scalp_budget_qty)
        effective_cap = configured_effective_cap if configured_effective_cap > 0 else cap_qty
        details.update(
            {
                "scale_in_budget_ratio": round(scale_in_ratio, 6),
                "scale_in_target_budget": int(target_budget),
                "scale_in_safe_budget": int(safe_budget),
                "scale_in_budget_qty": int(scalp_budget_qty),
                "scale_in_min_one_share_floor_enabled": min_one_share_floor_enabled,
                "scale_in_min_one_share_floor_applied": scalp_min_one_share_floor_applied,
            }
        )
    if cap_qty <= 0:
        details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "position_cap_or_budget"})
        return details

    if normalized_strategy in {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}:
        if add_type not in {"AVG_DOWN", "PYRAMID"}:
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "invalid_add_type"})
            return details
        if add_type == "AVG_DOWN" and add_reason != "swing_avg_down_ok":
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "swing_avg_down_probe_missing"})
            return details
        if add_type == "PYRAMID" and add_reason != "swing_pyramid_ok":
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "swing_pyramid_probe_missing"})
            return details
        would_qty = max(1, int(scalp_budget_qty or legacy.get("template_qty", 0) or legacy.get("qty", 0) or 0))
        effective_qty = max(0, min(would_qty, cap_qty, effective_cap))
        qty_reason = "swing_dynamic_allowed" if configured_effective_cap <= 0 else "swing_dynamic_capped_allowed"
        details.update(
            {
                "would_qty": would_qty,
                "effective_qty": effective_qty,
                "qty": effective_qty,
                "qty_reason": qty_reason if effective_qty > 0 else "effective_qty_cap_zero",
            }
        )
        return details

    action = action or {}
    feat = stock.get("last_reversal_features") or {}
    current_ai_score = _safe_float(
        action.get("current_ai_score", stock.get("current_ai_score", (stock.get("rt_ai_prob") or 0) * 100)),
        0.0,
    )
    buy_pressure = _safe_float(feat.get("buy_pressure_10t"), 0.0)
    tick_accel = _safe_float(feat.get("tick_acceleration_ratio"), 0.0)
    large_sell = bool(feat.get("large_sell_print_detected", True))
    profit_rate = _safe_float(action.get("profit_rate"), 0.0)
    peak_profit = _safe_float(action.get("peak_profit"), profit_rate)
    drawdown_from_peak = max(0.0, peak_profit - profit_rate)

    if add_type == "PYRAMID":
        min_ai = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_AI_SCORE", 70) or 70)
        min_buy_pressure = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_BUY_PRESSURE", 60.0) or 60.0)
        min_tick_accel = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_TICK_ACCEL", 0.5) or 0.5)
        checks = {
            "ai_score_ok": current_ai_score >= min_ai,
            "buy_pressure_ok": buy_pressure >= min_buy_pressure,
            "tick_accel_ok": tick_accel >= min_tick_accel,
            "peak_hold_ok": drawdown_from_peak <= 0.3,
            "large_sell_clear": not large_sell,
        }
        details.update(
            {
                "current_ai_score": round(current_ai_score, 4),
                "min_ai_score": min_ai,
                "buy_pressure_10t": round(buy_pressure, 4),
                "min_buy_pressure": min_buy_pressure,
                "tick_acceleration_ratio": round(tick_accel, 4),
                "min_tick_accel": min_tick_accel,
                "drawdown_from_peak": round(drawdown_from_peak, 4),
                "large_sell_print_detected": large_sell,
                **checks,
            }
        )
        if not all(checks.values()):
            failed = [name for name, ok in checks.items() if not ok]
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "pyramid_evidence_insufficient:" + ",".join(failed)})
            return details
        would_qty = max(1, int(scalp_budget_qty or legacy.get("template_qty", 0) or legacy.get("qty", 0) or 0))
    elif add_type == "AVG_DOWN":
        if add_reason != "reversal_add_ok":
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "reversal_probe_missing"})
            return details
        hard_stop_price = _safe_float(stock.get("hard_stop_price"), 0.0)
        if hard_stop_price > 0 and resolved_price <= hard_stop_price:
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "protection_distance_invalid"})
            return details
        would_qty = max(1, int(scalp_budget_qty or legacy.get("template_qty", 0) or legacy.get("qty", 0) or 0))
    else:
        details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "invalid_add_type"})
        return details

    effective_qty = max(0, min(would_qty, cap_qty, effective_cap))
    qty_reason = "dynamic_allowed" if configured_effective_cap <= 0 else "dynamic_capped_allowed"
    details.update(
        {
            "would_qty": would_qty,
            "effective_qty": effective_qty,
            "qty": effective_qty,
            "qty_reason": qty_reason if effective_qty > 0 else "effective_qty_cap_zero",
        }
    )
    return details
