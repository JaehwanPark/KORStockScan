import statistics
import math
from datetime import datetime, timedelta, time as dt_time

from src.utils.constants import TRADING_RULES
from src.utils import kiwoom_utils

_DEFAULT_SCALE_IN_RATIO = 0.50
_DEFAULT_SWING_PYRAMID_RATIO = 0.30
_STOP_LINE_TOUCH_MANDATORY_AVG_DOWN_REASON = "stop_line_touch_mandatory_avg_down"
_SCALPING_AVG_DOWN_SPECIAL_REASONS = {
    "reversal_add_ok",
    "late_loss_avg_down_retry",
    "aggressive_reversal_add_ok",
    _STOP_LINE_TOUCH_MANDATORY_AVG_DOWN_REASON,
}
_SCALE_IN_RULES = {
    ("SCALPING", "AVG_DOWN", "reversal_add_ok"): {
        "ratio_rule": "REVERSAL_ADD_SIZE_RATIO",
        "default_ratio": 0.33,
        "floor_rule": "REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED",
        "floor_default": True,
    },
    ("SCALPING", "AVG_DOWN", "late_loss_avg_down_retry"): {
        "ratio_rule": "REVERSAL_ADD_SIZE_RATIO",
        "default_ratio": 0.33,
        "floor_rule": "REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED",
        "floor_default": True,
    },
    ("SCALPING", "AVG_DOWN", "aggressive_reversal_add_ok"): {
        "ratio_rule": "AGGRESSIVE_REVERSAL_ADD_SIZE_RATIO",
        "default_ratio": 0.50,
        "floor_rule": "REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED",
        "floor_default": True,
    },
    ("SCALPING", "AVG_DOWN", _STOP_LINE_TOUCH_MANDATORY_AVG_DOWN_REASON): {
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


def _safe_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off", ""}:
            return False
        return default
    return bool(value)


_UNTRUSTED_AI_SCORE_SOURCES = {
    "",
    "-",
    "none",
    "null",
    "missing",
    "not_called",
    "holding_ai_not_called",
    "fallback_score_50",
}


def _ai_score_source(stock, action=None):
    action = action if isinstance(action, dict) else {}
    stock = stock if isinstance(stock, dict) else {}
    for key in (
        "ai_score_source",
        "holding_ai_score_source",
        "current_ai_score_source",
        "ai_result_source",
        "last_ai_result_source",
    ):
        value = action.get(key)
        if value not in (None, ""):
            return str(value).strip()
    for key in (
        "ai_score_source",
        "holding_ai_score_source",
        "current_ai_score_source",
        "ai_result_source",
        "last_ai_result_source",
    ):
        value = stock.get(key)
        if value not in (None, ""):
            return str(value).strip()
    model = str(stock.get("ai_model") or stock.get("last_ai_model") or "").strip()
    if model and model != "-":
        return "model"
    if _safe_bool(stock.get("ai_fallback_score_50"), False) or _safe_bool(action.get("ai_fallback_score_50"), False):
        return "fallback_score_50"
    return "-"


def _ai_score_available_for_scale_in(stock, action=None, *, current_ai_score=None):
    source = _ai_score_source(stock, action)
    normalized = str(source or "").strip().lower()
    score = _safe_float(current_ai_score, None)
    if score is None and isinstance(action, dict):
        score = _safe_float(action.get("current_ai_score"), None)
    if score is None and isinstance(stock, dict):
        score = _safe_float(stock.get("current_ai_score"), None)
    if normalized == "fallback_score_50":
        return False, source or "-"
    if normalized in _UNTRUSTED_AI_SCORE_SOURCES:
        return (False, source or "-") if score is None or abs(float(score) - 50.0) < 1e-9 else (True, source or "-")
    return True, source or "-"


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

    raw_holding_started_at = stock.get("holding_started_at")
    if raw_holding_started_at not in (None, "", 0, "0"):
        try:
            return max(0, int(current_ts - float(raw_holding_started_at)))
        except (TypeError, ValueError):
            holding_dt = resolve_buy_time_as_datetime(raw_holding_started_at, current_dt)
            if holding_dt is not None:
                return max(0, int((current_dt - holding_dt).total_seconds()))

    raw_buy_time = stock.get("buy_time")
    if not raw_buy_time:
        return 0

    buy_dt = resolve_buy_time_as_datetime(raw_buy_time, current_dt)
    if buy_dt is None:
        return 0
    return max(0, int((current_dt - buy_dt).total_seconds()))


def _scalping_pyramid_quality_snapshot(stock, *, current_ai_score=None):
    stock = stock if isinstance(stock, dict) else {}
    feat = stock.get("last_reversal_features") or {}
    if not isinstance(feat, dict):
        feat = {}
    ai_default = _safe_float(stock.get("rt_ai_prob"), 0.0) * 100.0
    ai_score = current_ai_score if current_ai_score is not None else stock.get("current_ai_score")
    raw_micro_vwap = feat.get("curr_vs_micro_vwap_bp")
    ai_score_available, ai_score_source = _ai_score_available_for_scale_in(
        stock,
        current_ai_score=ai_score,
    )
    source_quality = reversal_feature_source_quality(feat)
    source_stale = bool(feat and source_quality["reversal_feature_stale"])
    return {
        "current_ai_score": _safe_float(ai_score, ai_default),
        "ai_score_source": ai_score_source,
        "ai_score_available": ai_score_available,
        "buy_pressure_10t": _safe_float(feat.get("buy_pressure_10t"), 0.0),
        "tick_acceleration_ratio": _safe_float(feat.get("tick_acceleration_ratio"), 0.0),
        "large_sell_print_detected": _safe_bool(feat.get("large_sell_print_detected"), True),
        "curr_vs_micro_vwap_bp": _safe_float(raw_micro_vwap, None),
        "reversal_feature_stale": source_stale,
        **source_quality,
    }


def _scalping_pyramid_strong_continuation_context(
    stock,
    drawdown_from_peak,
    is_new_high,
    *,
    current_ai_score=None,
):
    enabled = bool(getattr(TRADING_RULES, "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED", False))
    base_min_profit = max(
        0.0,
        _safe_float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_PROFIT_PCT", 1.5), 1.5),
    )
    strong_min_profit = _safe_float(
        getattr(TRADING_RULES, "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT", 0.9),
        0.9,
    )
    strong_min_profit = max(0.0, min(base_min_profit, strong_min_profit))
    max_drawdown = max(
        0.0,
        _safe_float(
            getattr(TRADING_RULES, "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT", 0.20),
            0.20,
        ),
    )
    min_ai = _safe_float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_AI_SCORE", 70), 70.0)
    min_buy_pressure = _safe_float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_BUY_PRESSURE", 60.0), 60.0)
    min_tick_accel = _safe_float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_TICK_ACCEL", 0.5), 0.5)
    max_micro_vwap_bp = _safe_float(
        getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS", 60.0),
        60.0,
    )
    quality = _scalping_pyramid_quality_snapshot(stock, current_ai_score=current_ai_score)
    micro_vwap_bp = quality["curr_vs_micro_vwap_bp"]
    ai_score_ok = (not quality["ai_score_available"]) or quality["current_ai_score"] >= min_ai
    ai_score_real_support = quality["ai_score_available"] and quality["current_ai_score"] >= min_ai
    checks = {
        "enabled": enabled,
        "new_high": bool(is_new_high),
        "peak_hold_ok": float(drawdown_from_peak) <= max_drawdown,
        "ai_score_ok": ai_score_ok,
        "buy_pressure_support_ok": quality["buy_pressure_10t"] >= min_buy_pressure,
        "tick_accel_ok": (not quality["reversal_feature_stale"]) and quality["tick_acceleration_ratio"] >= min_tick_accel,
        "large_sell_clear": not quality["large_sell_print_detected"],
        "micro_vwap_available": micro_vwap_bp is not None,
        "micro_vwap_not_overheated": (
            (not quality["reversal_feature_stale"])
            and micro_vwap_bp is not None
            and micro_vwap_bp <= max_micro_vwap_bp
        ),
    }
    strong_checks = {**checks, "ai_score_ok": ai_score_real_support}
    failed = [name for name, ok in checks.items() if not ok]
    strong_failed = [name for name, ok in strong_checks.items() if not ok]
    return {
        "base_min_profit_pct": round(base_min_profit, 4),
        "strong_continuation_min_profit_pct": round(strong_min_profit, 4),
        "strong_continuation_max_drawdown_pct": round(max_drawdown, 4),
        "strong_continuation_failed_checks": ",".join(strong_failed),
        "strong_continuation_allowed": not strong_failed,
        "current_ai_score": round(quality["current_ai_score"], 4),
        "ai_score_source": quality["ai_score_source"],
        "ai_score_available": quality["ai_score_available"],
        "ai_score_real_support": ai_score_real_support,
        "min_ai_score": round(min_ai, 4),
        "buy_pressure_10t": round(quality["buy_pressure_10t"], 4),
        "min_buy_pressure": round(min_buy_pressure, 4),
        "buy_pressure_support_ok": checks["buy_pressure_support_ok"],
        "tick_acceleration_ratio": round(quality["tick_acceleration_ratio"], 4),
        "min_tick_accel": round(min_tick_accel, 4),
        "tick_accel_ok": checks["tick_accel_ok"],
        "large_sell_print_detected": quality["large_sell_print_detected"],
        "large_sell_clear": checks["large_sell_clear"],
        "curr_vs_micro_vwap_bp": "-" if micro_vwap_bp is None else round(micro_vwap_bp, 4),
        "max_micro_vwap_bps": round(max_micro_vwap_bp, 4),
        "micro_vwap_available": checks["micro_vwap_available"],
        "micro_vwap_not_overheated": checks["micro_vwap_not_overheated"],
        "reversal_feature_source_quality": quality["reversal_feature_source_quality"],
        "reversal_feature_stale": quality["reversal_feature_stale"],
        "reversal_feature_stale_reason": quality["reversal_feature_stale_reason"],
        "tick_context_quality": quality["tick_context_quality"],
        "tick_context_stale": quality["tick_context_stale"],
        "tick_latest_age_ms": quality["tick_latest_age_ms"],
        "tick_accel_source": quality["tick_accel_source"],
        "quote_stale": quality["quote_stale"],
        "quote_age_ms": quality["quote_age_ms"],
        "quote_age_source": quality["quote_age_source"],
        "feature_extracted_at": quality["feature_extracted_at"],
        "ai_score_ok": checks["ai_score_ok"],
    }


def _pyramid_runtime_prior_default_fields(runtime_prior_context):
    prior = runtime_prior_context if isinstance(runtime_prior_context, dict) else {}
    return {
        "pyramid_runtime_prior_status": str(prior.get("status") or "missing"),
        "pyramid_runtime_prior_sample_count": int(_safe_float(prior.get("sample_count"), 0)),
        "pyramid_runtime_prior_recovered_or_extended_rate": round(
            _safe_float(prior.get("recovered_or_extended_rate"), 0.0),
            4,
        ),
        "pyramid_runtime_prior_reversal_or_flat_rate": round(
            _safe_float(prior.get("reversal_or_flat_rate"), 0.0),
            4,
        ),
        "pyramid_runtime_prior_blocked_then_recovered_rate": round(
            _safe_float(prior.get("blocked_then_recovered_rate"), 0.0),
            4,
        ),
        "pyramid_runtime_prior_submitted_then_profit_rate": round(
            _safe_float(prior.get("submitted_then_profit_rate"), 0.0),
            4,
        ),
        "pyramid_runtime_prior_signal": str(prior.get("signal") or "neutral"),
        "pyramid_runtime_prior_reason": str(prior.get("reason") or "-"),
    }


def _pyramid_borderline_soft_blockers(result, profit_rate):
    if not isinstance(result, dict):
        return []
    reason = str(result.get("reason") or "")
    failures = []
    if reason.startswith("pyramid_quality_blocked:"):
        failures = [part.strip() for part in reason.split(":", 1)[1].split(",") if part.strip()]
    elif reason:
        failures = [reason]

    soft_blockers = []
    min_profit = _safe_float(result.get("min_profit_pct"), 0.0)
    if "profit_not_enough" in failures and profit_rate >= min_profit - 0.3:
        soft_blockers.append("profit_below_min_borderline")
    ai_score = _safe_float(result.get("current_ai_score"), 0.0)
    min_ai = _safe_float(result.get("min_ai_score"), 70.0)
    if "ai_score_below_min" in failures and ai_score >= min_ai - 5.0:
        soft_blockers.append("ai_score_below_min_borderline")
    tick_accel = _safe_float(result.get("tick_acceleration_ratio"), 0.0)
    min_tick = _safe_float(result.get("min_tick_accel"), 0.5)
    if "tick_accel_below_min" in failures and tick_accel >= min_tick - 0.2:
        soft_blockers.append("tick_accel_below_min_borderline")
    micro_value = result.get("curr_vs_micro_vwap_bp")
    micro_vwap = None if micro_value == "-" else _safe_float(micro_value, None)
    max_micro = _safe_float(result.get("max_micro_vwap_bps"), 60.0)
    if "micro_vwap_overheated" in failures and micro_vwap is not None and micro_vwap <= max_micro + 20.0:
        soft_blockers.append("micro_vwap_overheated_borderline")
    buy_pressure = _safe_float(result.get("buy_pressure_10t"), 0.0)
    min_buy_pressure = _safe_float(result.get("min_buy_pressure"), 60.0)
    if (
        "buy_pressure_below_min" in failures
        and result.get("buy_pressure_support_ok") is False
        and buy_pressure >= min_buy_pressure - 5.0
        and "buy_pressure_below_min_borderline" not in soft_blockers
    ):
        soft_blockers.append("buy_pressure_below_min_borderline")
    return soft_blockers


def _pyramid_support_is_weak(result):
    ai_weak = False
    if result.get("ai_score_available", True):
        ai_score = _safe_float(result.get("current_ai_score"), 0.0)
        min_ai = _safe_float(result.get("min_ai_score"), 70.0)
        ai_weak = ai_score < min_ai + 5.0
    buy_pressure = _safe_float(result.get("buy_pressure_10t"), 0.0)
    min_buy_pressure = _safe_float(result.get("min_buy_pressure"), 60.0)
    tick_accel = _safe_float(result.get("tick_acceleration_ratio"), 0.0)
    min_tick = _safe_float(result.get("min_tick_accel"), 0.5)
    return ai_weak or buy_pressure < min_buy_pressure + 5.0 or tick_accel < min_tick + 0.2


def _apply_pyramid_runtime_prior_context(result, runtime_prior_context, profit_rate):
    if not isinstance(result, dict):
        return result
    prior_fields = _pyramid_runtime_prior_default_fields(runtime_prior_context)
    result.update(prior_fields)
    signal = prior_fields["pyramid_runtime_prior_signal"]
    status = prior_fields["pyramid_runtime_prior_status"]
    if status in {"missing", "stale"} or signal == "neutral":
        return result

    soft_blockers = _pyramid_borderline_soft_blockers(result, profit_rate)
    support_signals = []
    risk_signals = []
    if signal == "support":
        support_signals.append("runtime_prior_support")
    elif signal == "risk":
        risk_signals.append("runtime_prior_risk")
    if soft_blockers:
        result["pyramid_runtime_prior_soft_blockers"] = ",".join(soft_blockers)

    if signal == "support" and not result.get("should_add") and len(soft_blockers) == 1:
        result["should_add"] = True
        result["add_type"] = "PYRAMID"
        result["reason"] = "scalping_pyramid_ok"
        result["pyramid_runtime_prior_support_applied"] = True
        result["pyramid_runtime_prior_relaxed_blocker"] = soft_blockers[0]
    elif signal == "risk":
        if result.get("should_add") and _pyramid_support_is_weak(result):
            result["should_add"] = False
            result["add_type"] = None
            result["reason"] = "runtime_prior_risk"
            result["pyramid_runtime_prior_risk_applied"] = True
        elif not result.get("should_add") and len(soft_blockers) >= 2:
            result["pyramid_runtime_prior_risk_applied"] = True

    if support_signals:
        result["pyramid_runtime_prior_support_signals"] = ",".join(support_signals)
    if risk_signals:
        result["pyramid_runtime_prior_risk_signals"] = ",".join(risk_signals)
    return result


def evaluate_scalping_pyramid(
    stock,
    profit_rate,
    peak_profit,
    is_new_high,
    current_ai_score=None,
    runtime_prior_context=None,
):
    """
    스캘핑 불타기(PYRAMID) 평가: 1차는 profit/peak 기반 단순 조건.
    TODO: VWAP/RSI/ATR 기반 필터 추가
    """
    result = _base_result()

    profit_rate = _safe_float(profit_rate, 0.0)
    peak_profit = _safe_float(peak_profit, profit_rate)
    base_min_profit = max(
        0.0,
        _safe_float(getattr(TRADING_RULES, 'SCALPING_PYRAMID_MIN_PROFIT_PCT', 1.5), 1.5),
    )
    drawdown_from_peak = max(0.0, float(peak_profit - profit_rate))
    continuation_context = _scalping_pyramid_strong_continuation_context(
        stock,
        drawdown_from_peak,
        is_new_high,
        current_ai_score=current_ai_score,
    )
    effective_min_profit = base_min_profit
    profit_gate_mode = "base"
    if profit_rate < base_min_profit:
        strong_min_profit = _safe_float(
            continuation_context.get("strong_continuation_min_profit_pct"),
            base_min_profit,
        )
        if profit_rate >= strong_min_profit and continuation_context.get("strong_continuation_allowed"):
            effective_min_profit = strong_min_profit
            profit_gate_mode = "strong_continuation"
        else:
            result.update(continuation_context)
            result.update(
                {
                    "reason": "profit_not_enough",
                    "profit_gate_mode": "base",
                    "min_profit_pct": round(base_min_profit, 4),
                    "drawdown_from_peak": round(drawdown_from_peak, 4),
                    "is_new_high": bool(is_new_high),
                }
            )
            return _apply_pyramid_runtime_prior_context(result, runtime_prior_context, profit_rate)

    if profit_rate < effective_min_profit:
        result.update(continuation_context)
        result["reason"] = "profit_not_enough"
        result["profit_gate_mode"] = profit_gate_mode
        result["min_profit_pct"] = round(effective_min_profit, 4)
        result["drawdown_from_peak"] = round(drawdown_from_peak, 4)
        result["is_new_high"] = bool(is_new_high)
        return _apply_pyramid_runtime_prior_context(result, runtime_prior_context, profit_rate)

    if not (is_new_high or drawdown_from_peak <= 0.3):
        result.update(continuation_context)
        result["reason"] = "trend_not_strong"
        result["profit_gate_mode"] = profit_gate_mode
        result["min_profit_pct"] = round(effective_min_profit, 4)
        result["drawdown_from_peak"] = round(drawdown_from_peak, 4)
        result["is_new_high"] = bool(is_new_high)
        return _apply_pyramid_runtime_prior_context(result, runtime_prior_context, profit_rate)

    quality_failures = []
    if not continuation_context.get("ai_score_ok"):
        quality_failures.append("ai_score_below_min")
    if not continuation_context.get("buy_pressure_support_ok"):
        quality_failures.append("buy_pressure_below_min")
    if not continuation_context.get("tick_accel_ok"):
        quality_failures.append(
            "tick_accel_stale"
            if continuation_context.get("reversal_feature_stale")
            else "tick_accel_below_min"
        )
    if not continuation_context.get("large_sell_clear"):
        quality_failures.append("large_sell_detected")
    if not continuation_context.get("micro_vwap_available"):
        quality_failures.append("micro_vwap_missing")
    elif not continuation_context.get("micro_vwap_not_overheated"):
        quality_failures.append(
            "micro_context_stale"
            if continuation_context.get("reversal_feature_stale")
            else "micro_vwap_overheated"
        )
    if quality_failures:
        result.update(continuation_context)
        result["reason"] = (
            quality_failures[0]
            if len(quality_failures) == 1
            else "pyramid_quality_blocked:" + ",".join(quality_failures)
        )
        result["profit_gate_mode"] = profit_gate_mode
        result["min_profit_pct"] = round(effective_min_profit, 4)
        result["drawdown_from_peak"] = round(drawdown_from_peak, 4)
        result["is_new_high"] = bool(is_new_high)
        return _apply_pyramid_runtime_prior_context(result, runtime_prior_context, profit_rate)

    result.update(continuation_context)
    result["should_add"] = True
    result["add_type"] = "PYRAMID"
    result["reason"] = "scalping_pyramid_ok"
    result["profit_gate_mode"] = profit_gate_mode
    result["min_profit_pct"] = round(effective_min_profit, 4)
    result["drawdown_from_peak"] = round(drawdown_from_peak, 4)
    result["is_new_high"] = bool(is_new_high)
    return _apply_pyramid_runtime_prior_context(result, runtime_prior_context, profit_rate)


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


def reversal_feature_source_quality(feat):
    feat = feat if isinstance(feat, dict) else {}
    tick_quality = str(feat.get("tick_context_quality") or "").strip().lower()
    tick_stale = _safe_bool(feat.get("tick_context_stale"), False)
    quote_stale = _safe_bool(feat.get("quote_stale"), False)
    tick_age_ms = _safe_float(feat.get("tick_latest_age_ms"), None)
    quote_age_ms = _safe_float(feat.get("quote_age_ms"), None)
    max_tick_age_ms = _safe_float(
        getattr(TRADING_RULES, "REVERSAL_ADD_MAX_TICK_AGE_MS", 5000),
        5000.0,
    )
    max_quote_age_ms = _safe_float(
        getattr(TRADING_RULES, "SCALP_PRE_AI_MAX_WS_AGE_SEC", 3.0),
        3.0,
    ) * 1000.0
    stale_reasons = []
    if tick_stale is True or tick_quality == "stale_tick":
        stale_reasons.append("tick_context_stale")
    elif tick_quality in {"missing_ticks", "missing_tick_time"} or tick_quality.startswith("accel_"):
        stale_reasons.append("tick_context_unusable")
    if quote_stale is True:
        stale_reasons.append("quote_stale")
    if tick_age_ms is not None and tick_age_ms > max_tick_age_ms:
        stale_reasons.append("tick_age_gt_max")
    if quote_age_ms is not None and quote_age_ms > max_quote_age_ms:
        stale_reasons.append("quote_age_gt_max")
    return {
        "reversal_feature_source_quality": "stale" if stale_reasons else "usable",
        "reversal_feature_stale": bool(stale_reasons),
        "reversal_feature_stale_reason": ",".join(stale_reasons) or "-",
        "tick_context_quality": feat.get("tick_context_quality", "-"),
        "tick_context_stale": feat.get("tick_context_stale", "unknown"),
        "tick_latest_age_ms": "-" if tick_age_ms is None else round(tick_age_ms, 3),
        "tick_accel_source": feat.get("tick_accel_source", "-"),
        "quote_stale": feat.get("quote_stale", "unknown"),
        "quote_age_ms": "-" if quote_age_ms is None else round(quote_age_ms, 3),
        "quote_age_source": feat.get("quote_age_source", "missing"),
        "feature_extracted_at": feat.get("feature_extracted_at", "-"),
    }


def _check_reversal_add_supply(stock):
    feat = stock.get('last_reversal_features', {})
    min_buy_pressure = getattr(TRADING_RULES, 'REVERSAL_ADD_MIN_BUY_PRESSURE', 55)
    if feat:
        source_quality = reversal_feature_source_quality(feat)
        if source_quality["reversal_feature_stale"]:
            return "reversal_features_stale:" + source_quality["reversal_feature_stale_reason"]
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


def _check_aggressive_reversal_add(stock, profit_rate, current_ai_score, held_sec):
    if not bool(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_ENABLED', False)):
        return "aggressive_reversal_add_disabled"

    pnl_min = float(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_PNL_MIN', -0.70))
    pnl_max = float(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_PNL_MAX', -0.10))
    if not (pnl_min <= profit_rate <= pnl_max):
        return f"aggressive_pnl_out_of_range({profit_rate:.2f})"

    min_hold = int(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_MIN_HOLD_SEC', 20))
    max_hold = int(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_MAX_HOLD_SEC', 240))
    if not (min_hold <= held_sec <= max_hold):
        return f"aggressive_hold_sec_out_of_range({held_sec}s)"

    min_ai = int(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_MIN_AI_SCORE', 80))
    if current_ai_score < min_ai:
        return f"aggressive_ai_score_too_low({current_ai_score})"

    feat = stock.get('last_reversal_features', {}) or {}
    if not feat:
        return "aggressive_reversal_features_missing"
    source_quality = reversal_feature_source_quality(feat)
    if source_quality["reversal_feature_stale"]:
        return "aggressive_reversal_features_stale:" + source_quality["reversal_feature_stale_reason"]

    buy_pressure = _safe_float(feat.get('buy_pressure_10t'), 0.0)
    micro_vwap_bp = _safe_float(feat.get('curr_vs_micro_vwap_bp'), -999.0)
    large_sell = bool(feat.get('large_sell_print_detected', True))
    min_buy_pressure = float(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_MIN_BUY_PRESSURE', 85.0))
    min_micro_vwap_bp = float(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_VWAP_BP_MIN', -12.0))

    if buy_pressure < min_buy_pressure:
        return f"aggressive_buy_pressure_not_met({buy_pressure:.2f})"
    if large_sell:
        return "aggressive_large_sell_detected"
    if micro_vwap_bp < min_micro_vwap_bp:
        return f"aggressive_micro_vwap_not_met({micro_vwap_bp:.2f})"
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
    source_quality = reversal_feature_source_quality(feat)
    source_quality_stale = bool(feat and source_quality["reversal_feature_stale"])
    supply_checks = {
        "buy_pressure_ok": buy_pressure >= min_buy_pressure,
        "tick_accel_ok": (not source_quality_stale) and tick_accel >= min_tick_accel,
        "large_sell_absent_ok": not large_sell_print,
        "micro_vwap_ok": (not source_quality_stale) and micro_vwap_bp >= min_micro_vwap_bp,
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
        "aggressive_enabled": bool(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_ENABLED', False)),
        "aggressive_min_ai_score": int(getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_MIN_AI_SCORE', 80)),
        "aggressive_min_buy_pressure": _safe_float(
            getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_MIN_BUY_PRESSURE', 85.0),
            85.0,
        ),
        "aggressive_min_micro_vwap_bp": _safe_float(
            getattr(TRADING_RULES, 'AGGRESSIVE_REVERSAL_ADD_VWAP_BP_MIN', -12.0),
            -12.0,
        ),
    }
    probe.update(source_quality)
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

    reasons = (
        _check_reversal_add_pnl_range(profit_rate),
        _check_reversal_add_hold_sec(held_sec),
        _check_reversal_add_low_floor(stock, profit_rate),
        _check_reversal_add_supply(stock),
        _check_reversal_add_ai_recovery(stock, current_ai_score),
    )
    for reason in reasons:
        if reason:
            aggressive_reason = _check_aggressive_reversal_add(stock, profit_rate, current_ai_score, held_sec)
            if aggressive_reason is None:
                result["should_add"] = True
                result["add_type"] = "AVG_DOWN"
                result["reason"] = "aggressive_reversal_add_ok"
                result["blocked_standard_reason"] = reason
                return result
            result["reason"] = reason
            result["aggressive_blocked_reason"] = aggressive_reason
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
    add_reason = str(action.get("reason") or "")
    late_loss_retry = add_reason == "late_loss_avg_down_retry"
    sim_scale_in_observation = action.get("source") == "scalp_sim_scale_in_window_expansion"
    stop_line_touched = bool(
        action.get("stop_line_touched")
        or stock.get("scale_in_stop_line_touched")
    )
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
        "stop_line_touched": stop_line_touched,
        "curr_vs_micro_vwap_bp": _safe_float(
            (stock.get("last_reversal_features") or {}).get("curr_vs_micro_vwap_bp"),
            0.0,
        ),
        "max_micro_vwap_bps": float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS", 60.0) or 60.0),
        "resolver_enabled": bool(getattr(TRADING_RULES, "SCALPING_SCALE_IN_PRICE_RESOLVER_ENABLED", True)),
    }
    feature_quality = reversal_feature_source_quality(stock.get("last_reversal_features") or {})
    result.update(feature_quality)

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
    if (
        add_type == "AVG_DOWN"
        and stop_line_touched
        and not sim_scale_in_observation
        and bool(getattr(TRADING_RULES, "SCALPING_AVG_DOWN_MARKET_ON_STOP_TOUCH_ENABLED", False))
    ):
        result.update({
            "allowed": True,
            "order_price": 0,
            "reason": "stop_line_touch_market",
            "price_source": "stop_line_touch_market",
        })
        return result
    if add_type == "AVG_DOWN":
        min_micro_vwap = float(getattr(TRADING_RULES, "REVERSAL_ADD_VWAP_BP_MIN", -5.0) or -5.0)
        result["min_micro_vwap_bps"] = min_micro_vwap
        micro_supported_avg_down = add_reason in {"reversal_add_ok", "aggressive_reversal_add_ok"}
        if micro_supported_avg_down and feature_quality["reversal_feature_stale"]:
            result["reason"] = "micro_context_stale:" + feature_quality["reversal_feature_stale_reason"]
            return result
        result["late_loss_avg_down_retry_micro_vwap_bypass"] = bool(
            late_loss_retry and not feature_quality["reversal_feature_stale"] and micro_vwap_bp < min_micro_vwap
        )
        if micro_vwap_bp < min_micro_vwap and not late_loss_retry:
            result["reason"] = f"micro_vwap_bp<{min_micro_vwap:.1f}"
            return result

    if (
        add_type == "AVG_DOWN"
        and not sim_scale_in_observation
        and bool(getattr(TRADING_RULES, "SCALPING_AVG_DOWN_MARKET_ON_STOP_TOUCH_ENABLED", False))
    ):
        result["reason"] = "stop_line_not_touched"
        return result

    avg_down_bid_discount_ticks = max(
        0,
        _safe_int(getattr(TRADING_RULES, "SCALPING_AVG_DOWN_BID_DISCOUNT_TICKS", 1), 1),
    )
    result["avg_down_bid_discount_ticks"] = avg_down_bid_discount_ticks
    if add_type == "AVG_DOWN" and best_bid > 0 and best_bid < curr_price and avg_down_bid_discount_ticks > 0:
        order_price = _ticks_down(best_bid, avg_down_bid_discount_ticks)
        source = "best_bid_discount"
    elif best_bid > 0 and best_bid < curr_price:
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
    normalized_reason = (
        add_reason
        if add_reason in _SCALPING_AVG_DOWN_SPECIAL_REASONS
        else "default"
    )
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
    cash_orderable_qty_cap=None,
    budget_source=None,
    account_deposit=None,
    cash_orderable_amount=None,
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
    buy_qty = _safe_int(stock.get("buy_qty"), 0)
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
    cash_qty_cap = None
    if cash_orderable_qty_cap is not None:
        cash_qty_cap = max(0, _safe_int(cash_orderable_qty_cap, 0))
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
        if cash_qty_cap is not None:
            scalp_budget_qty = min(max(0, scalp_budget_qty), cash_qty_cap)
        cap_qty = max(0, scalp_budget_qty)
        effective_cap = configured_effective_cap if configured_effective_cap > 0 else cap_qty
        details.update(
            {
                "scale_in_budget_source": budget_source or "budget_base",
                "scale_in_account_deposit": _safe_int(account_deposit, 0) if account_deposit is not None else deposit,
                "scale_in_cash_orderable_amount": (
                    _safe_int(cash_orderable_amount, 0) if cash_orderable_amount is not None else deposit
                ),
                "scale_in_cash_orderable_qty_cap": cash_qty_cap if cash_qty_cap is not None else "-",
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
    ai_score_available, ai_score_source = _ai_score_available_for_scale_in(
        stock,
        action,
        current_ai_score=current_ai_score,
    )
    buy_pressure = _safe_float(feat.get("buy_pressure_10t"), 0.0)
    tick_accel = _safe_float(feat.get("tick_acceleration_ratio"), 0.0)
    large_sell = _safe_bool(feat.get("large_sell_print_detected"), True)
    micro_vwap_bp = _safe_float(feat.get("curr_vs_micro_vwap_bp"), None)
    feature_quality = reversal_feature_source_quality(feat)
    feature_stale = bool(feat and feature_quality["reversal_feature_stale"])
    profit_rate = _safe_float(action.get("profit_rate"), 0.0)
    peak_profit = _safe_float(action.get("peak_profit"), profit_rate)
    drawdown_from_peak = max(0.0, peak_profit - profit_rate)

    if add_type == "PYRAMID":
        min_ai = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_AI_SCORE", 70) or 70)
        min_buy_pressure = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_BUY_PRESSURE", 60.0) or 60.0)
        min_tick_accel = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_TICK_ACCEL", 0.5) or 0.5)
        max_micro_vwap_bp = float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS", 60.0) or 60.0)
        hard_checks = {
            "ai_score_ok": (not ai_score_available) or current_ai_score >= min_ai,
            "tick_accel_ok": (not feature_stale) and tick_accel >= min_tick_accel,
            "peak_hold_ok": drawdown_from_peak <= 0.3,
            "large_sell_clear": not large_sell,
            "micro_vwap_available": micro_vwap_bp is not None,
            "micro_vwap_not_overheated": (
                (not feature_stale)
                and micro_vwap_bp is not None
                and micro_vwap_bp <= max_micro_vwap_bp
            ),
        }
        support_checks = {
            "buy_pressure_support_ok": buy_pressure >= min_buy_pressure,
        }
        details.update(
            {
                "current_ai_score": round(current_ai_score, 4),
                "ai_score_source": ai_score_source,
                "ai_score_available": ai_score_available,
                "min_ai_score": min_ai,
                "buy_pressure_10t": round(buy_pressure, 4),
                "min_buy_pressure": min_buy_pressure,
                "tick_acceleration_ratio": round(tick_accel, 4),
                "min_tick_accel": min_tick_accel,
                "curr_vs_micro_vwap_bp": "-" if micro_vwap_bp is None else round(micro_vwap_bp, 4),
                "max_micro_vwap_bps": max_micro_vwap_bp,
                "drawdown_from_peak": round(drawdown_from_peak, 4),
                "large_sell_print_detected": large_sell,
                **feature_quality,
                **hard_checks,
                **support_checks,
            }
        )
        if not all(hard_checks.values()):
            failed = [name for name, ok in hard_checks.items() if not ok]
            details.update(
                {
                    "would_qty": 0,
                    "effective_qty": 0,
                    "qty": 0,
                    "qty_reason": "pyramid_evidence_insufficient:" + ",".join(failed),
                }
            )
            return details
        would_qty = max(1, int(scalp_budget_qty or legacy.get("template_qty", 0) or legacy.get("qty", 0) or 0))
        if not details["sim_uncapped_qty"]:
            details.update(
                {
                    "pyramid_sizing_mode": "dynamic_budget",
                    "pyramid_position_ratio_cap_applied": False,
                }
            )
    elif add_type == "AVG_DOWN":
        if add_reason not in _SCALPING_AVG_DOWN_SPECIAL_REASONS:
            details.update({"would_qty": 0, "effective_qty": 0, "qty": 0, "qty_reason": "reversal_probe_missing"})
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
