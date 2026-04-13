"""State machine handlers for the sniper engine."""

import time
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np

from src.database.models import RecommendationHistory
from src.engine import kiwoom_orders
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine.sniper_time import (
    TIME_09_00,
    TIME_09_03,
    TIME_09_05,
    TIME_15_30,
    TIME_SCALPING_NEW_BUY_CUTOFF,
)
from src.engine.sniper_condition_handlers_big_bite import (
    build_tick_data_from_ws,
    arm_big_bite_if_triggered,
    confirm_big_bite_follow_through,
)
from src.engine.sniper_scale_in import (
    evaluate_scalping_avg_down,
    evaluate_scalping_pyramid,
    evaluate_swing_avg_down,
    evaluate_swing_pyramid,
    calc_scale_in_qty,
)
from src.engine.sniper_scale_in_utils import record_add_history_event
from src.engine.trade_pause_control import is_buy_side_paused, get_pause_state_label
from src.engine.sniper_entry_latency import (
    clear_signal_reference,
    evaluate_live_buy_entry,
)
from src.engine.sniper_entry_state import ENTRY_LOCK, move_orders_to_terminal
from src.engine.sniper_strength_momentum import evaluate_scalping_strength_momentum
from src.engine.sniper_strength_shadow_feedback import record_shadow_candidate
from src.engine.sniper_gatekeeper_replay import record_gatekeeper_snapshot
from src.engine.sniper_dynamic_thresholds import (
    estimate_turnover_hint,
    get_dynamic_scalp_thresholds,
    get_dynamic_swing_gap_threshold,
)
from src.engine.trade_profit import calculate_net_profit_rate
from src.engine.sniper_position_tags import (
    normalize_position_tag,
    normalize_strategy,
)


KIWOOM_TOKEN = None
DB = None
EVENT_BUS = None
ACTIVE_TARGETS = None
COOLDOWNS = None
ALERTED_STOCKS = None


def _resolve_zero_qty_cooldown_sec(deposit: int) -> int:
    """주문가능금액 0원은 일시 조회 실패일 수 있어 짧게 재조회합니다."""
    if int(float(deposit or 0)) <= 0:
        return int(getattr(TRADING_RULES, "ZERO_DEPOSIT_RETRY_COOLDOWN_SEC", 20) or 20)
    return 1200
HIGHEST_PRICES = None
LAST_AI_CALL_TIMES = None
LAST_LOG_TIMES = None
TRADING_RULES = None
PUBLISH_GATEKEEPER_REPORT = None
SHOULD_BLOCK_SWING_ENTRY = None
CONFIRM_CANCEL_OR_RELOAD_REMAINING = None
SEND_EXIT_BEST_IOC = None
DUAL_PERSONA_ENGINE = None
BIG_BITE_STATE = {}


def bind_state_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    event_bus=None,
    active_targets=None,
    cooldowns=None,
    alerted_stocks=None,
    highest_prices=None,
    last_ai_call_times=None,
    last_log_times=None,
    trading_rules=None,
    publish_gatekeeper_report=None,
    should_block_swing_entry=None,
    confirm_cancel_or_reload_remaining=None,
    send_exit_best_ioc=None,
    dual_persona_engine=None,
):
    global KIWOOM_TOKEN, DB, EVENT_BUS, ACTIVE_TARGETS, COOLDOWNS, ALERTED_STOCKS, HIGHEST_PRICES
    global LAST_AI_CALL_TIMES, LAST_LOG_TIMES, TRADING_RULES, PUBLISH_GATEKEEPER_REPORT
    global SHOULD_BLOCK_SWING_ENTRY, CONFIRM_CANCEL_OR_RELOAD_REMAINING, SEND_EXIT_BEST_IOC
    global DUAL_PERSONA_ENGINE

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if event_bus is not None:
        EVENT_BUS = event_bus
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
        _sanitize_pending_add_states(ACTIVE_TARGETS)
    if cooldowns is not None:
        COOLDOWNS = cooldowns
    if alerted_stocks is not None:
        ALERTED_STOCKS = alerted_stocks
    if highest_prices is not None:
        HIGHEST_PRICES = highest_prices
    if last_ai_call_times is not None:
        LAST_AI_CALL_TIMES = last_ai_call_times
    if last_log_times is not None:
        LAST_LOG_TIMES = last_log_times
    if trading_rules is not None:
        TRADING_RULES = trading_rules
    if publish_gatekeeper_report is not None:
        PUBLISH_GATEKEEPER_REPORT = publish_gatekeeper_report
    if should_block_swing_entry is not None:
        SHOULD_BLOCK_SWING_ENTRY = should_block_swing_entry
    if confirm_cancel_or_reload_remaining is not None:
        CONFIRM_CANCEL_OR_RELOAD_REMAINING = confirm_cancel_or_reload_remaining
    if send_exit_best_ioc is not None:
        SEND_EXIT_BEST_IOC = send_exit_best_ioc
    if dual_persona_engine is not None:
        DUAL_PERSONA_ENGINE = dual_persona_engine


def _publish_gatekeeper_report_proxy(stock, code, gatekeeper, allowed):
    if PUBLISH_GATEKEEPER_REPORT is None:
        return
    PUBLISH_GATEKEEPER_REPORT(stock, code, gatekeeper, allowed)


def _should_block_swing_entry(strategy):
    if SHOULD_BLOCK_SWING_ENTRY is None:
        return False, None
    return SHOULD_BLOCK_SWING_ENTRY(strategy)


def _confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    if CONFIRM_CANCEL_OR_RELOAD_REMAINING is None:
        return 0
    return CONFIRM_CANCEL_OR_RELOAD_REMAINING(code, orig_ord_no, token, expected_qty)


def _send_exit_best_ioc(code, qty, token):
    if SEND_EXIT_BEST_IOC is None:
        return {}
    return SEND_EXIT_BEST_IOC(code, qty, token)


def _format_entry_price_text(value):
    try:
        price = int(float(value))
    except (TypeError, ValueError):
        return "-"
    return f"{price:,}원"


def _translate_latency_state(value):
    return {
        "SAFE": "양호",
        "CAUTION": "주의",
        "DANGER": "위험",
    }.get(str(value or "").upper(), value or "-")


def _translate_entry_decision(value):
    return {
        "ALLOW_NORMAL": "기본 진입 허용",
        "ALLOW_FALLBACK": "분할 진입 허용",
        "REJECT_DANGER": "진입 보류",
        "REJECT": "진입 보류",
    }.get(str(value or "").upper(), value or "-")


def _translate_order_tag(value):
    return {
        "fallback_scout": "탐색 주문",
        "fallback_main": "본 주문",
    }.get(value, value or "주문")


def _translate_tif(value):
    return {
        "IOC": "즉시체결 우선",
        "DAY": "장중 유지",
    }.get(str(value or "").upper(), value or "-")


def _format_entry_order_line(order):
    return (
        f"- {_translate_order_tag(order.get('tag'))}: "
        f"{int(order.get('qty') or 0)}주 / "
        f"{_format_entry_price_text(order.get('price'))} / "
        f"{_translate_tif(order.get('tif'))}"
    )


def _publish_entry_mode_summary(stock, code, *, entry_mode, latency_gate):
    if EVENT_BUS is None:
        return
    if entry_mode not in {'fallback'}:
        return

    orders = latency_gate.get('orders') or []
    order_lines = [_format_entry_order_line(order) for order in orders]
    order_summary = "\n".join(order_lines) if order_lines else "- 주문 계획 없음"
    msg = (
        f"🧭 **[{stock.get('name')} ({code})] 지연 대응 분할진입 활성화**\n"
        f"- 지연 상태: `{_translate_latency_state(latency_gate.get('latency_state'))}`\n"
        f"- 판정: `{_translate_entry_decision(latency_gate.get('decision'))}`\n"
        f"- 기준 가격: 신호가 `{_format_entry_price_text(latency_gate.get('signal_price'))}` / "
        f"현재가 `{_format_entry_price_text(latency_gate.get('latest_price'))}`\n"
        f"- 주문 계획:\n{order_summary}"
    )
    EVENT_BUS.publish(
        'TELEGRAM_BROADCAST',
        {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'},
        )


def _log_entry_pipeline(stock, code, stage, **fields):
    record_id = stock.get("id") if isinstance(stock, dict) else None
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        stock.get("name"),
        code,
        stage,
        record_id=record_id,
        fields=fields,
    )


def _log_holding_pipeline(stock, code, stage, **fields):
    record_id = stock.get("id")
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        stock.get("name"),
        code,
        stage,
        record_id=record_id,
        fields=fields,
    )


def _update_boolean_sustain_sec(stock, *, key: str, active: bool, now_ts: float) -> int:
    if active:
        started_at = float(stock.get(key, 0) or 0)
        if started_at <= 0:
            started_at = now_ts
            stock[key] = started_at
        return max(0, int(now_ts - started_at))
    stock.pop(key, None)
    return 0


def _apply_fallback_qty_canary(
    planned_orders: list[dict],
    *,
    qty_multiplier: float,
) -> tuple[list[dict], int, int]:
    if not planned_orders:
        return [], 0, 0

    safe_multiplier = max(0.1, min(1.0, float(qty_multiplier or 1.0)))
    updated_orders: list[dict] = []
    original_total = 0
    scaled_total = 0

    for order in planned_orders:
        item = dict(order or {})
        qty = max(0, int(item.get("qty") or 0))
        original_total += qty

        if qty <= 0:
            item["qty"] = 0
            updated_orders.append(item)
            continue

        scaled_qty = int(round(qty * safe_multiplier))
        if str(item.get("tag") or "") == "fallback_scout":
            scaled_qty = max(1, scaled_qty)
        else:
            scaled_qty = max(0, scaled_qty)
        scaled_qty = min(qty, scaled_qty)
        item["qty"] = scaled_qty
        scaled_total += scaled_qty
        updated_orders.append(item)

    if scaled_total <= 0:
        for item in updated_orders:
            if int(item.get("qty") or 0) > 0:
                item["qty"] = 1
                scaled_total = 1
                break
        if scaled_total <= 0 and updated_orders:
            updated_orders[0]["qty"] = 1
            scaled_total = 1

    return updated_orders, original_total, scaled_total


def _emit_scalp_hard_time_stop_shadow(
    *,
    stock: dict,
    code: str,
    held_sec: int,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    ai_exit_min_loss_pct: float,
) -> None:
    if not bool(getattr(TRADING_RULES, "SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY", True)):
        return

    raw_candidates = getattr(TRADING_RULES, "SCALP_COMMON_HARD_TIME_STOP_SHADOW_MINUTES", (3, 5, 7)) or (3, 5, 7)
    try:
        candidates = sorted({max(1, int(value)) for value in raw_candidates})
    except Exception:
        candidates = [3, 5, 7]

    shadow_min_loss_pct = float(
        getattr(TRADING_RULES, "SCALP_COMMON_HARD_TIME_STOP_SHADOW_MIN_LOSS_PCT", ai_exit_min_loss_pct) or ai_exit_min_loss_pct
    )
    shadow_peak_max_pct = float(
        getattr(TRADING_RULES, "SCALP_COMMON_HARD_TIME_STOP_SHADOW_MAX_PEAK_PCT", 0.20) or 0.20
    )
    if profit_rate > shadow_min_loss_pct or peak_profit > shadow_peak_max_pct:
        return

    logged_keys = {
        str(item)
        for item in (stock.get("hard_time_stop_shadow_logged") or [])
        if str(item)
    }
    now_entry_mode = str(stock.get("entry_mode", "")).strip().lower() or "normal"
    pos_tag = normalize_position_tag("SCALPING", stock.get("position_tag"))

    for minute_cut in candidates:
        threshold_sec = minute_cut * 60
        if held_sec < threshold_sec:
            continue
        candidate_key = f"{now_entry_mode}_{minute_cut}m"
        if candidate_key in logged_keys:
            continue
        _log_holding_pipeline(
            stock,
            code,
            "hard_time_stop_shadow",
            candidate=candidate_key,
            threshold_sec=threshold_sec,
            held_sec=held_sec,
            entry_mode=now_entry_mode,
            position_tag=pos_tag,
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            ai_score=f"{current_ai_score:.0f}",
            shadow_only=True,
        )
        logged_keys.add(candidate_key)

    if logged_keys:
        stock["hard_time_stop_shadow_logged"] = sorted(logged_keys)


def _log_dual_persona_shadow_result(stock_name, code, strategy, payload, record_id=None):
    stock_stub = {"name": stock_name, "id": record_id}
    if not isinstance(payload, dict):
        _log_entry_pipeline(
            stock_stub,
            code,
            "dual_persona_shadow_error",
            strategy=strategy,
            decision_type="gatekeeper",
            error="invalid_shadow_payload",
        )
        return

    if payload.get("error"):
        _log_entry_pipeline(
            stock_stub,
            code,
            "dual_persona_shadow_error",
            strategy=strategy,
            decision_type=payload.get("decision_type", "gatekeeper"),
            error=payload.get("error", "unknown"),
            shadow_extra_ms=payload.get("shadow_extra_ms", 0),
        )
        return

    _log_entry_pipeline(
        stock_stub,
        code,
        "dual_persona_shadow",
        strategy=strategy,
        decision_type=payload.get("decision_type", "gatekeeper"),
        dual_mode=payload.get("mode", "shadow"),
        gemini_action=payload.get("gemini_action", ""),
        gemini_score=payload.get("gemini_score", 0),
        aggr_action=payload.get("aggr_action", ""),
        aggr_score=payload.get("aggr_score", 0),
        cons_action=payload.get("cons_action", ""),
        cons_score=payload.get("cons_score", 0),
        cons_veto=str(bool(payload.get("cons_veto", False))).lower(),
        fused_action=payload.get("fused_action", ""),
        fused_score=payload.get("fused_score", 0),
        winner=payload.get("winner", ""),
        agreement_bucket=payload.get("agreement_bucket", ""),
        hard_flags=",".join(payload.get("hard_flags", []) or []) or "-",
        shadow_extra_ms=payload.get("shadow_extra_ms", 0),
    )


def _submit_gatekeeper_dual_persona_shadow(*, stock_name, code, strategy, realtime_ctx, gatekeeper, record_id=None):
    if DUAL_PERSONA_ENGINE is None:
        return
    try:
        DUAL_PERSONA_ENGINE.submit_gatekeeper_shadow(
            stock_name=stock_name,
            stock_code=code,
            strategy=strategy,
            realtime_ctx=realtime_ctx,
            gemini_result=gatekeeper,
            callback=lambda payload: _log_dual_persona_shadow_result(
                stock_name,
                code,
                strategy,
                payload,
                record_id=record_id,
            ),
        )
    except Exception as e:
        log_error(f"🚨 [Gatekeeper 듀얼 페르소나 shadow 제출 실패] {stock_name}({code}): {e}")


def _reason_codes(**checks) -> str:
    failed = [name for name, allowed in checks.items() if not allowed]
    return ",".join(failed) if failed else "eligible"


def _get_swing_gap_threshold(strategy: str) -> float:
    fallback = float(getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0) or 3.0)
    strategy_upper = str(strategy or '').upper()
    if strategy_upper == 'KOSPI_ML':
        return float(getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT_KOSPI', fallback) or fallback)
    return float(getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT_KOSDAQ', fallback) or fallback)


def _resolve_gatekeeper_reject_cooldown(action_label: str) -> tuple[int, str]:
    action = str(action_label or '').strip()
    if action == '눌림 대기':
        return (
            int(getattr(TRADING_RULES, 'ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN', 60 * 20) or 60 * 20),
            'pullback_wait',
        )
    if action in {'전량 회피', '둘 다 아님'}:
        return (
            int(getattr(TRADING_RULES, 'ML_GATEKEEPER_REJECT_COOLDOWN', 60 * 60 * 2) or 60 * 60 * 2),
            'hard_reject',
        )
    return (
        int(getattr(TRADING_RULES, 'ML_GATEKEEPER_NEUTRAL_COOLDOWN', 60 * 30) or 60 * 30),
        'neutral_hold',
    )


def _resolve_stock_marcap(stock, code) -> int:
    try:
        existing = int(float(stock.get('marcap', 0) or 0))
    except Exception:
        existing = 0
    if existing > 0:
        return existing
    if DB is None:
        return 0
    try:
        marcap = int(DB.get_latest_marcap(code) or 0)
    except Exception:
        marcap = 0
    if marcap > 0:
        stock['marcap'] = marcap
    return marcap


def _get_best_levels_from_ws(ws_data):
    orderbook = ws_data.get('orderbook') or {}
    asks = orderbook.get('asks') or []
    bids = orderbook.get('bids') or []
    best_ask = 0
    best_bid = 0
    try:
        if asks:
            best_ask = int(float(asks[-1].get('price', 0) or 0))
    except Exception:
        best_ask = 0
    try:
        if bids:
            best_bid = int(float(bids[0].get('price', 0) or 0))
    except Exception:
        best_bid = 0
    return best_ask, best_bid


def _get_ws_snapshot_age_sec(ws_data):
    raw_ts = (ws_data or {}).get('last_ws_update_ts')
    if raw_ts in (None, '', 0):
        return None
    try:
        age = time.time() - float(raw_ts)
        return max(0.0, float(age))
    except Exception:
        return None


def _resolve_reference_age_sec(primary_ts, *, fallback_ts=None, now_ts=None):
    def _coerce_ts(value):
        if value in (None, "", 0, "0", "None"):
            return None
        try:
            ts = float(value)
        except Exception:
            return None
        return ts if ts > 0 else None

    reference_ts = _coerce_ts(primary_ts)
    if reference_ts is None:
        reference_ts = _coerce_ts(fallback_ts)
    if reference_ts is None:
        return None

    current_ts = time.time() if now_ts is None else float(now_ts)
    return max(0.0, float(current_ts - reference_ts))


def _extract_ai_overlap_snapshot(
    *,
    ws_data,
    recent_ticks=None,
    recent_candles=None,
    ai_engine=None,
):
    snapshot = {
        "latest_strength": float(ws_data.get("v_pw", 0.0) or 0.0),
        "buy_pressure_10t": float(ws_data.get("buy_ratio", 0.0) or 0.0),
        "distance_from_day_high_pct": 0.0,
        "intraday_range_pct": 0.0,
    }

    ticks = list(recent_ticks or [])
    candles = list(recent_candles or [])
    if ticks:
        try:
            snapshot["latest_strength"] = float(ticks[0].get("strength", snapshot["latest_strength"]) or snapshot["latest_strength"])
        except Exception:
            pass
        try:
            buy_vol = sum(int(float(tick.get("volume", 0) or 0)) for tick in ticks if str(tick.get("dir") or "").upper() == "BUY")
            sell_vol = sum(int(float(tick.get("volume", 0) or 0)) for tick in ticks if str(tick.get("dir") or "").upper() == "SELL")
            total_vol = buy_vol + sell_vol
            if total_vol > 0:
                snapshot["buy_pressure_10t"] = (buy_vol / total_vol) * 100.0
        except Exception:
            pass

    curr_price = int(float(ws_data.get("curr", 0) or 0))
    if candles and curr_price > 0:
        highs = []
        lows = []
        for candle in candles:
            try:
                highs.append(float(candle.get("고가", 0) or 0))
                lows.append(float(candle.get("저가", 0) or 0))
            except Exception:
                continue
        high_price = max([value for value in highs if value > 0], default=0.0)
        low_price = min([value for value in lows if value > 0], default=0.0)
        if high_price > 0:
            snapshot["distance_from_day_high_pct"] = ((curr_price - high_price) / high_price) * 100.0
        if low_price > 0 and high_price >= low_price:
            snapshot["intraday_range_pct"] = ((high_price - low_price) / low_price) * 100.0

    if ai_engine and hasattr(ai_engine, "_extract_scalping_features"):
        try:
            feature_map = ai_engine._extract_scalping_features(ws_data, ticks, candles)
            snapshot["latest_strength"] = float(feature_map.get("latest_strength", snapshot["latest_strength"]) or snapshot["latest_strength"])
            snapshot["buy_pressure_10t"] = float(feature_map.get("buy_pressure_10t", snapshot["buy_pressure_10t"]) or snapshot["buy_pressure_10t"])
            snapshot["distance_from_day_high_pct"] = float(
                feature_map.get("distance_from_day_high_pct", snapshot["distance_from_day_high_pct"])
                or snapshot["distance_from_day_high_pct"]
            )
            snapshot["intraday_range_pct"] = float(
                feature_map.get("intraday_range_pct", snapshot["intraday_range_pct"])
                or snapshot["intraday_range_pct"]
            )
        except Exception:
            pass

    return snapshot


def _build_ai_overlap_log_fields(
    *,
    stock,
    ai_score,
    momentum_tag=None,
    threshold_profile=None,
    overbought_blocked=False,
    blocked_stage=None,
    overlap_snapshot=None,
):
    snapshot = overlap_snapshot or (stock.get("last_ai_overlap_snapshot") or {})
    return {
        "ai_score": f"{float(ai_score or 0.0):.1f}",
        "latest_strength": f"{float(snapshot.get('latest_strength', 0.0) or 0.0):.1f}",
        "buy_pressure_10t": f"{float(snapshot.get('buy_pressure_10t', 0.0) or 0.0):.2f}",
        "distance_from_day_high_pct": f"{float(snapshot.get('distance_from_day_high_pct', 0.0) or 0.0):.3f}",
        "intraday_range_pct": f"{float(snapshot.get('intraday_range_pct', 0.0) or 0.0):.3f}",
        "momentum_tag": momentum_tag or stock.get("entry_momentum_tag") or stock.get("position_tag") or "-",
        "threshold_profile": threshold_profile or stock.get("entry_threshold_profile") or "-",
        "overbought_blocked": bool(overbought_blocked),
        "blocked_stage": blocked_stage or "-",
    }


def _build_ai_ops_log_fields(
    ai_decision,
    *,
    ai_score_raw=None,
    ai_score_after_bonus=None,
    entry_score_threshold=None,
    big_bite_bonus_applied=None,
    ai_cooldown_blocked=None,
):
    payload = ai_decision or {}
    out = {
        "ai_parse_ok": bool(payload.get("ai_parse_ok", False)),
        "ai_parse_fail": bool(payload.get("ai_parse_fail", False)),
        "ai_fallback_score_50": bool(payload.get("ai_fallback_score_50", False)),
        "ai_response_ms": int(payload.get("ai_response_ms", 0) or 0),
        "ai_prompt_type": str(payload.get("ai_prompt_type", "-") or "-"),
        "ai_result_source": str(payload.get("ai_result_source", "-") or "-"),
    }
    if ai_score_raw is not None:
        out["ai_score_raw"] = f"{float(ai_score_raw or 0.0):.1f}"
    if ai_score_after_bonus is not None:
        out["ai_score_after_bonus"] = f"{float(ai_score_after_bonus or 0.0):.1f}"
    if entry_score_threshold is not None:
        out["entry_score_threshold"] = f"{float(entry_score_threshold or 0.0):.1f}"
    if big_bite_bonus_applied is not None:
        out["big_bite_bonus_applied"] = bool(big_bite_bonus_applied)
    if ai_cooldown_blocked is not None:
        out["ai_cooldown_blocked"] = bool(ai_cooldown_blocked)
    return out


def _should_run_watching_prompt_75_shadow(ai_decision, ai_score):
    if not bool(getattr(TRADING_RULES, "AI_WATCHING_75_PROMPT_SHADOW_ENABLED", False)):
        return False
    try:
        score = float(ai_score or 0.0)
    except Exception:
        return False
    min_score = float(getattr(TRADING_RULES, "AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE", 75) or 75)
    max_score = float(getattr(TRADING_RULES, "AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE", 79) or 79)
    if score < min_score or score > max_score:
        return False
    if bool((ai_decision or {}).get("ai_fallback_score_50", False)):
        return False
    return str((ai_decision or {}).get("action", "WAIT") or "WAIT").upper() != "BUY"


def _resolve_holding_elapsed_sec(stock):
    now_ts = time.time()
    raw_order_time = stock.get("order_time")
    if raw_order_time not in (None, "", 0, "0"):
        try:
            return max(0, int(now_ts - float(raw_order_time)))
        except Exception:
            pass

    raw_buy_time = stock.get("buy_time")
    if not raw_buy_time:
        return 0
    try:
        if isinstance(raw_buy_time, datetime):
            buy_dt = raw_buy_time
        else:
            buy_str = str(raw_buy_time)
            try:
                buy_dt = datetime.fromisoformat(buy_str)
            except Exception:
                parsed_time = datetime.strptime(buy_str, "%H:%M:%S").time()
                buy_dt = datetime.combine(datetime.now().date(), parsed_time)
        return max(0, int((datetime.now() - buy_dt).total_seconds()))
    except Exception:
        return 0


def _bucket_int(value, bucket):
    try:
        bucket = max(1, int(bucket))
        return int(float(value or 0) // bucket)
    except Exception:
        return 0


def _coerce_int_value(value, default=0):
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _price_bucket_step(price):
    try:
        price = abs(int(float(price or 0)))
    except Exception:
        price = 0
    if price >= 200_000:
        return 500
    if price >= 50_000:
        return 100
    if price >= 10_000:
        return 50
    if price >= 5_000:
        return 10
    return 5


def _bucket_float(value, step):
    try:
        step = float(step)
        if step <= 0:
            return 0
        return round(float(value or 0.0) / step) * step
    except Exception:
        return 0.0


def _floor_bucket_float(value, step):
    try:
        step = float(step)
        if step <= 0:
            return 0.0
        return float(int(float(value or 0.0) // step) * step)
    except Exception:
        return 0.0


def _resolve_holding_ai_fast_reuse_sec(is_critical_zone, dynamic_max_cd):
    configured_sec = (
        float(getattr(TRADING_RULES, 'AI_HOLDING_FAST_REUSE_CRITICAL_SEC', 8.0) or 8.0)
        if is_critical_zone
        else float(getattr(TRADING_RULES, 'AI_HOLDING_FAST_REUSE_NORMAL_SEC', 20.0) or 20.0)
    )
    review_window_floor = max(0.0, float(dynamic_max_cd or 0.0)) + 2.0
    return max(configured_sec, review_window_floor)


def _resolve_gatekeeper_fast_reuse_sec():
    configured_sec = float(getattr(TRADING_RULES, 'AI_GATEKEEPER_FAST_REUSE_SEC', 12.0) or 12.0)
    return max(configured_sec, 20.0)


def _build_gatekeeper_fast_signature(stock, ws_data, strategy, score):
    best_ask, best_bid = _get_best_levels_from_ws(ws_data)
    curr_price = ws_data.get('curr', 0)
    price_bucket = _price_bucket_step(curr_price)
    return (
        str(strategy or ''),
        str(stock.get('position_tag', '') or ''),
        _floor_bucket_float(score, 5.0),
        _bucket_int(curr_price, price_bucket),
        _floor_bucket_float(ws_data.get('fluctuation', 0.0), 0.3),
        _bucket_int(ws_data.get('volume', 0), 50_000),
        _floor_bucket_float(ws_data.get('v_pw', 0.0), 5.0),
        _floor_bucket_float(ws_data.get('buy_ratio', 0.0), 8.0),
        _bucket_int(ws_data.get('prog_net_qty', 0), 10_000),
        _bucket_int(ws_data.get('prog_delta_qty', 0), 2_000),
        _bucket_int(best_ask, price_bucket),
        _bucket_int(best_bid, price_bucket),
        _bucket_int(ws_data.get('ask_tot', 0), 50_000),
        _bucket_int(ws_data.get('bid_tot', 0), 50_000),
        _bucket_int(ws_data.get('net_bid_depth', 0), 5_000),
        _bucket_int(ws_data.get('net_ask_depth', 0), 5_000),
    )


def _build_gatekeeper_fast_snapshot(stock, ws_data, strategy, score):
    """Gatekeeper fast signature 변경 추적용 dict 스냅샷 (sig_delta 비교용)"""
    best_ask, best_bid = _get_best_levels_from_ws(ws_data)
    curr_price = ws_data.get('curr', 0)
    price_bucket = _price_bucket_step(curr_price)
    buy_exec = _coerce_int_value(ws_data.get('buy_exec_volume', 0))
    sell_exec = _coerce_int_value(ws_data.get('sell_exec_volume', 0))
    
    return {
        "curr_price": _bucket_int(curr_price, price_bucket),
        "score": _floor_bucket_float(score, 5.0),
        "v_pw_now": _floor_bucket_float(ws_data.get('v_pw', 0.0), 5.0),
        "buy_ratio_ws": _floor_bucket_float(ws_data.get('buy_ratio', 0.0), 8.0),
        "spread_tick": max(0, _bucket_int(best_ask, price_bucket) - _bucket_int(best_bid, price_bucket)),
        "prog_delta_qty": _bucket_int(ws_data.get('prog_delta_qty', 0), 2_000),
        "net_buy_exec_volume": _bucket_int(buy_exec - sell_exec, 5_000),
    }


def _build_holding_ai_fast_snapshot(ws_data):
    best_ask, best_bid = _get_best_levels_from_ws(ws_data)
    curr_price = ws_data.get('curr', 0)
    price_bucket = _price_bucket_step(curr_price)
    ask_tot = _coerce_int_value(ws_data.get('ask_tot'))
    bid_tot = _coerce_int_value(ws_data.get('bid_tot'))
    buy_exec = _coerce_int_value(ws_data.get('buy_exec_volume'))
    sell_exec = _coerce_int_value(ws_data.get('sell_exec_volume'))
    spread_amount = max(0, _coerce_int_value(best_ask) - _coerce_int_value(best_bid))
    return {
        "curr": _bucket_int(curr_price, price_bucket),
        "fluctuation": _bucket_float(ws_data.get('fluctuation', 0.0), 0.3),
        "v_pw": _bucket_float(ws_data.get('v_pw', 0.0), 10.0),
        "buy_ratio": _bucket_float(ws_data.get('buy_ratio', 0.0), 8.0),
        "spread": _bucket_int(spread_amount, max(1, price_bucket)),
        "ask_bid_balance": _bucket_int(bid_tot - ask_tot, 50_000),
        "depth_balance": _bucket_int(
            _coerce_int_value(ws_data.get('net_bid_depth')) - abs(_coerce_int_value(ws_data.get('net_ask_depth'))),
            20_000,
        ),
        "exec_balance": _bucket_int(buy_exec - sell_exec, 5_000),
        "tick_trade_value": _bucket_int(ws_data.get('tick_trade_value', 0), 20_000),
    }


def _build_holding_ai_fast_signature(ws_data):
    snapshot = _build_holding_ai_fast_snapshot(ws_data)
    return tuple(snapshot.values())


def _describe_snapshot_deltas(previous_snapshot, current_snapshot, *, limit=4):
    if not isinstance(previous_snapshot, dict) or not isinstance(current_snapshot, dict):
        return ""
    deltas = []
    for key in current_snapshot.keys():
        prev = previous_snapshot.get(key)
        curr = current_snapshot.get(key)
        if prev != curr:
            deltas.append(f"{key}:{prev}->{curr}")
        if len(deltas) >= limit:
            break
    return ",".join(deltas)


def _log_strength_momentum_observation(stock, code, result):
    if not isinstance(result, dict):
        return
    stage = "strength_momentum_pass" if result.get("allowed") else "strength_momentum_observed"
    _log_entry_pipeline(
        stock,
        code,
        stage,
        reason=result.get("reason"),
        base_vpw=f"{float(result.get('base_vpw', 0.0) or 0.0):.1f}",
        current_vpw=f"{float(result.get('current_vpw', 0.0) or 0.0):.1f}",
        delta=f"{float(result.get('vpw_delta', 0.0) or 0.0):.1f}",
        slope=f"{float(result.get('slope_per_sec', 0.0) or 0.0):.2f}",
        window_sec=result.get("window_sec"),
        buy_value=int(result.get("window_buy_value", 0) or 0),
        sell_value=int(result.get("window_sell_value", 0) or 0),
        buy_ratio=f"{float(result.get('window_buy_ratio', 0.0) or 0.0):.2f}",
        exec_buy_ratio=f"{float(result.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
        net_buy_qty=int(result.get("window_net_buy_qty", 0) or 0),
        elapsed=f"{float(result.get('elapsed_sec', 0.0) or 0.0):.2f}",
        threshold_profile=result.get("threshold_profile"),
        momentum_tag=result.get("position_tag"),
        canary_applied=bool(result.get("canary_applied")),
        canary_reason=result.get("canary_reason"),
        canary_origin_reason=result.get("canary_origin_reason"),
    )


def _iter_pending_entry_orders(stock):
    orders = stock.get('pending_entry_orders') or []
    if not isinstance(orders, list):
        return []
    return orders


def _clear_pending_entry_meta(stock):
    with ENTRY_LOCK:
        move_orders_to_terminal(stock, reason='pending_entry_meta_cleared')
        for key in [
            'pending_entry_orders',
            'entry_mode',
            'entry_requested_qty',
            'entry_filled_qty',
            'entry_fill_amount',
            'requested_buy_qty',
            'entry_bundle_id',
        ]:
            stock.pop(key, None)
    _clear_entry_arm(stock)


def _merge_pending_entry_orders(existing_orders, entry_orders):
    merged_orders = []
    existing_by_key = {}

    for order in existing_orders or []:
        ord_no = str(order.get('ord_no', '') or '').strip()
        tag = str(order.get('tag', '') or '').strip()
        key = ord_no or f"tag:{tag}"
        if key:
            existing_by_key[key] = order

    for order in entry_orders or []:
        merged = dict(order)
        ord_no = str(order.get('ord_no', '') or '').strip()
        tag = str(order.get('tag', '') or '').strip()
        key = ord_no or f"tag:{tag}"
        previous = existing_by_key.get(key)
        if previous:
            for field in [
                'status',
                'filled_qty',
                'last_fill_price',
                'last_fill_at',
                'cancelled_at',
                'notice_status',
                'notice_at',
            ]:
                if field in previous:
                    merged[field] = previous[field]
        merged_orders.append(merged)

    return merged_orders


def _clear_entry_arm(stock):
    for key in [
        'entry_armed',
        'entry_armed_at',
        'entry_armed_until',
        'entry_armed_reason',
        'entry_armed_ai_score',
        'entry_armed_ratio',
        'entry_armed_target_buy_price',
        'entry_armed_vpw',
        'entry_armed_dynamic_reason',
        'entry_armed_resume_count',
    ]:
        stock.pop(key, None)


def _activate_entry_arm(stock, code, *, ai_score, ratio, target_buy_price, current_vpw, reason, dynamic_reason):
    ttl_sec = int(getattr(TRADING_RULES, 'SCALP_ENTRY_ARM_TTL_SEC', 20) or 20)
    now_ts = time.time()
    stock['entry_armed'] = True
    stock['entry_armed_at'] = now_ts
    stock['entry_armed_until'] = now_ts + ttl_sec
    stock['entry_armed_reason'] = reason
    stock['entry_armed_ai_score'] = float(ai_score)
    stock['entry_armed_ratio'] = float(ratio)
    stock['entry_armed_target_buy_price'] = int(target_buy_price or 0)
    stock['entry_armed_vpw'] = float(current_vpw)
    stock['entry_armed_dynamic_reason'] = dynamic_reason
    stock['entry_armed_resume_count'] = 0
    _log_entry_pipeline(
        stock,
        code,
        'entry_armed',
        ai_score=f"{float(ai_score):.1f}",
        ratio=f"{float(ratio):.4f}",
        target_buy_price=int(target_buy_price or 0),
        current_vpw=f"{float(current_vpw):.1f}",
        reason=reason,
        dynamic_reason=dynamic_reason,
        ttl_sec=ttl_sec,
    )


def _get_live_entry_arm(stock, code):
    if not stock.get('entry_armed'):
        return None
    expires_at = float(stock.get('entry_armed_until', 0) or 0)
    now_ts = time.time()
    if expires_at <= now_ts:
        armed_at = float(stock.get("entry_armed_at", 0) or 0)
        resume_count = int(stock.get("entry_armed_resume_count", 0) or 0)
        waited_sec = max(0.0, now_ts - armed_at) if armed_at > 0 else 0.0
        expired_stage = "entry_armed_expired_after_wait" if resume_count > 0 else "entry_armed_expired"
        _log_entry_pipeline(
            stock,
            code,
            expired_stage,
            waited_sec=f"{waited_sec:.1f}",
            resume_count=resume_count,
            reason=stock.get("entry_armed_reason"),
            dynamic_reason=stock.get("entry_armed_dynamic_reason"),
        )
        _clear_entry_arm(stock)
        return None
    return {
        'armed_at': float(stock.get('entry_armed_at', 0) or 0),
        'expires_at': expires_at,
        'remaining_sec': max(0.0, expires_at - now_ts),
        'ai_score': float(stock.get('entry_armed_ai_score', 50.0) or 50.0),
        'ratio': float(stock.get('entry_armed_ratio', 0.10) or 0.10),
        'target_buy_price': int(stock.get('entry_armed_target_buy_price', 0) or 0),
        'current_vpw': float(stock.get('entry_armed_vpw', 0.0) or 0.0),
        'reason': stock.get('entry_armed_reason'),
        'dynamic_reason': stock.get('entry_armed_dynamic_reason'),
    }


def _has_open_pending_entry_orders(stock):
    return any(
        str(order.get('status', 'OPEN')).upper() in {'OPEN', 'PARTIAL', 'SENT'}
        for order in _iter_pending_entry_orders(stock)
    )


def _cancel_pending_entry_orders(stock, code, *, force=False):
    """
    Cancel unresolved entry BUY orders.

    Returns:
    - 'cancelled': all remaining orders cancelled or already gone
    - 'resolved': nothing left to cancel
    - 'failed': at least one order remains uncertain
    """

    with ENTRY_LOCK:
        open_orders = [
            order for order in _iter_pending_entry_orders(stock)
            if str(order.get('status', 'OPEN')).upper() in {'OPEN', 'PARTIAL', 'SENT'}
            and str(order.get('ord_no', '') or '').strip()
        ]
        if not open_orders:
            _clear_pending_entry_meta(stock)
            return 'resolved'

        had_failure = False
        for order in open_orders:
            ord_no = str(order.get('ord_no', '') or '').strip()
            res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=ord_no, token=KIWOOM_TOKEN, qty=0)
            is_success = False
            err_msg = str(res)
            if isinstance(res, dict):
                if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
                    is_success = True
                err_msg = str(res.get('return_msg', '') or '')
            elif res:
                is_success = True

            if is_success or any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음', '체결']):
                order['status'] = 'CANCELLED'
                order['cancelled_at'] = time.time()
                continue

            had_failure = True
            log_error(
                f"⚠️ [ENTRY_CANCEL] {stock.get('name')}({code}) "
                f"tag={order.get('tag')} ord_no={ord_no} cancel_failed msg={err_msg}"
            )
            if not force:
                break

        if had_failure:
            return 'failed'

        _clear_pending_entry_meta(stock)
        return 'cancelled'


def _stage_buy_order_submission(stock, code, curr_price, requested_qty, msg, entry_orders):
    with ENTRY_LOCK:
        _clear_entry_arm(stock)
        existing_filled_qty = int(stock.get('entry_filled_qty', 0) or 0)
        existing_fill_amount = int(stock.get('entry_fill_amount', 0) or 0)
        stock['status'] = 'HOLDING' if requested_qty > 0 and existing_filled_qty >= requested_qty else 'BUY_ORDERED'
        stock['order_time'] = float(stock.get('order_time', 0) or time.time())
        stock['order_price'] = curr_price
        stock['requested_buy_qty'] = requested_qty
        stock['entry_requested_qty'] = requested_qty
        stock['entry_filled_qty'] = existing_filled_qty
        stock['entry_fill_amount'] = existing_fill_amount
        stock['pending_entry_orders'] = _merge_pending_entry_orders(
            stock.get('pending_entry_orders') or [],
            entry_orders,
        )
        stock.setdefault('entry_bundle_id', f"{code}-{uuid4().hex[:12]}")
        primary_ord_no = ''
        for order in stock.get('pending_entry_orders') or []:
            primary_ord_no = str((order or {}).get('ord_no', '') or '').strip()
            if primary_ord_no:
                break
        if primary_ord_no:
            stock['odno'] = primary_ord_no
        stock['pending_buy_msg'] = msg


def _finalize_buy_order_submission(stock, code, curr_price, requested_qty, msg, entry_orders):
    _stage_buy_order_submission(stock, code, curr_price, requested_qty, msg, entry_orders)
    primary_ord_no = str(stock.get('odno', '') or '').strip()
    log_info(
        f"[ENTRY_SUBMISSION_BUNDLE] {stock.get('name')}({code}) "
        f"mode={stock.get('entry_mode', 'unknown')} requested_qty={requested_qty} "
        f"legs={len(entry_orders)} primary_ord_no={primary_ord_no}"
    )


def _resolve_live_entry_order_request(strategy, entry_mode, planned_order, default_order_type_code, default_price):
    tif = str(planned_order.get('tif', 'DAY') or 'DAY').upper()
    tag = str(planned_order.get('tag', 'normal') or 'normal')
    qty = int(planned_order.get('qty', 0) or 0)
    price = int(planned_order.get('price', default_price) or default_price or 0)

    if tif == 'IOC':
        return {
            'qty': qty,
            'price': 0,
            'order_type_code': '16',
            'tif': tif,
            'tag': tag,
        }

    if strategy == 'SCALPING' or entry_mode == 'fallback':
        return {
            'qty': qty,
            'price': price,
            'order_type_code': '00',
            'tif': tif,
            'tag': tag,
        }

    return {
        'qty': qty,
        'price': int(default_price or 0),
        'order_type_code': default_order_type_code,
        'tif': tif,
        'tag': tag,
    }


def _reconcile_pending_entry_orders(stock, code, strategy):
    if not _has_open_pending_entry_orders(stock):
        return

    order_time = float(stock.get('order_time', 0) or 0)
    if order_time <= 0:
        return

    timeout_sec = 20 if strategy == 'SCALPING' else getattr(TRADING_RULES, 'ORDER_TIMEOUT_SEC', 30)
    if time.time() - order_time <= timeout_sec:
        return

    result = _cancel_pending_entry_orders(stock, code, force=True)
    if result == 'failed':
        return

    if int(stock.get('buy_qty', 0) or 0) > 0:
        stock['status'] = 'HOLDING'
        stock.pop('odno', None)
        log_info(f"[ENTRY_RECONCILED] {stock.get('name')}({code}) partial fill kept, remaining entry orders cancelled")
    else:
        stock['status'] = 'WATCHING'
        stock.pop('odno', None)
        stock.pop('order_time', None)
        stock.pop('pending_buy_msg', None)
        stock.pop('target_buy_price', None)
        stock.pop('order_price', None)
        _clear_entry_arm(stock)
        HIGHEST_PRICES.pop(code, None)
        ALERTED_STOCKS.discard(code)
        if strategy in ['SCALPING', 'SCALP']:
            COOLDOWNS[code] = time.time() + 1200
        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=stock.get('id')).update({
                    "status": "WATCHING",
                    "buy_price": 0,
                    "buy_qty": 0,
                })
        except Exception as exc:
            log_error(f"🚨 [DB 에러] {stock.get('name')} pending entry timeout 복구 실패: {exc}")


# =====================================================================
# 🧠 상태 머신 (State Machine) 핸들러
# =====================================================================

def handle_watching_state(stock, code, ws_data, admin_id, radar=None, ai_engine=None):
    """
    [WATCHING 상태] 진입 타점 감시 및 AI 교차 검증
    """
    global LAST_AI_CALL_TIMES

    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    event_bus = EVENT_BUS

    log_info(
        f"[DEBUG] handle_watching_state 시작: {stock.get('name')} ({code}), 전략={stock.get('strategy')}, "
        f"위치태그={stock.get('position_tag')}, radar={'있음' if radar else '없음'}, "
        f"ai_engine={'있음' if ai_engine else '없음'}"
    )

    if is_buy_side_paused():
        now_ts = time.time()
        last_log = float(stock.get('last_pause_block_log_ts', 0) or 0)
        if (now_ts - last_log) >= 60:
            log_info(
                f"[TRADING_PAUSED_BLOCK] WATCHING buy skipped "
                f"{stock.get('name')}({code}) state={get_pause_state_label()}"
            )
            stock['last_pause_block_log_ts'] = now_ts
        return

    MAX_SCALP_SURGE_PCT = getattr(TRADING_RULES, 'MAX_SCALP_SURGE_PCT', 20.0)
    MAX_INTRADAY_SURGE = getattr(TRADING_RULES, 'MAX_INTRADAY_SURGE', 15.0)
    MIN_SCALP_LIQUIDITY = getattr(TRADING_RULES, 'MIN_SCALP_LIQUIDITY', 500_000_000)
    SNIPER_AGGRESSIVE_PROB = getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70)
    BUY_SCORE_THRESHOLD = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 70)
    VPW_STRONG_LIMIT = getattr(TRADING_RULES, 'VPW_STRONG_LIMIT', 120)
    INVEST_RATIO_SCALPING_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_SCALPING_MIN', 0.05)
    INVEST_RATIO_SCALPING_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_SCALPING_MAX', 0.25)
    VPW_SCALP_LIMIT = getattr(TRADING_RULES, 'VPW_SCALP_LIMIT', 120)
    AI_WATCHING_COOLDOWN = getattr(TRADING_RULES, 'AI_WATCHING_COOLDOWN', 60)
    VIP_LIQUIDITY_THRESHOLD = getattr(TRADING_RULES, 'VIP_LIQUIDITY_THRESHOLD', 1_000_000_000)
    AI_WAIT_DROP_COOLDOWN = getattr(TRADING_RULES, 'AI_WAIT_DROP_COOLDOWN', 300)
    VPW_KOSDAQ_LIMIT = getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105)
    VPW_STRONG_KOSDAQ_LIMIT = getattr(TRADING_RULES, 'VPW_STRONG_KOSDAQ_LIMIT', 120)
    BUY_SCORE_KOSDAQ_THRESHOLD = getattr(TRADING_RULES, 'BUY_SCORE_KOSDAQ_THRESHOLD', 80)
    INVEST_RATIO_KOSDAQ_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MIN', 0.05)
    INVEST_RATIO_KOSDAQ_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MAX', 0.15)
    AI_SCORE_THRESHOLD_KOSDAQ = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60)
    INVEST_RATIO_KOSPI_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MIN', 0.10)
    INVEST_RATIO_KOSPI_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MAX', 0.30)
    AI_SCORE_THRESHOLD_KOSPI = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSPI', 60)
    BIG_BITE_BOOST_SCORE = getattr(TRADING_RULES, 'BIG_BITE_BOOST_SCORE', 5)
    BIG_BITE_ARMED_ENTRY_BONUS = getattr(TRADING_RULES, 'BIG_BITE_ARMED_ENTRY_BONUS', 2)
    BIG_BITE_HARD_GATE_ENABLED = getattr(TRADING_RULES, 'BIG_BITE_HARD_GATE_ENABLED', False)
    BIG_BITE_HARD_GATE_TAGS_SCALPING = getattr(
        TRADING_RULES, 'BIG_BITE_HARD_GATE_TAGS_SCALPING', ("VCP", "BREAK", "BRK", "SHOOT", "NEXT")
    )
    BIG_BITE_HARD_GATE_TAGS_KOSDAQ = getattr(TRADING_RULES, 'BIG_BITE_HARD_GATE_TAGS_KOSDAQ', ())
    BIG_BITE_HARD_GATE_TAGS_KOSPI = getattr(TRADING_RULES, 'BIG_BITE_HARD_GATE_TAGS_KOSPI', ())

    strategy = normalize_strategy(stock.get('strategy'))
    pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))

    now = datetime.now()
    now_t = now.time()

    if strategy == 'SCALPING':
        strategy_start = TIME_09_00 if pos_tag == 'VCP_NEXT' else TIME_09_03
    else:
        strategy_start = TIME_09_05

    if now_t < strategy_start:
        if now.second % 30 == 0:
            print(f"📡 [관찰/블라인드 모드] 차트 데이터(VWAP) 형성 대기 중... (목표: {strategy_start})")
        log_info(f"[DEBUG] {code} 시간 조건 불충족 (현재 {now_t}, 시작 {strategy_start})")
        return

    MAX_SURGE = MAX_SCALP_SURGE_PCT
    MAX_INTRADAY_SURGE = MAX_INTRADAY_SURGE
    MIN_LIQUIDITY = MIN_SCALP_LIQUIDITY

    if code in cooldowns and time.time() < cooldowns[code]:
        log_info(f"[DEBUG] {code} 쿨다운 중 (만료 시간 {cooldowns[code]})")
        return

    if strategy == 'SCALPING' and now_t >= TIME_SCALPING_NEW_BUY_CUTOFF:
        log_info(f"[DEBUG] {code} SCALPING 신규매수 컷오프 이후 제외")
        return

    if code in alerted_stocks:
        log_info(f"[DEBUG] {code} 이미 alerted_stocks에 포함됨")
        return

    curr_price = int(float(ws_data.get('curr', 0) or 0))
    if curr_price <= 0:
        log_info(f"[DEBUG] {code} 현재가 유효하지 않음: {curr_price}")
        return

    current_vpw = float(ws_data.get('v_pw', 0) or 0)
    fluctuation = float(ws_data.get('fluctuation', 0.0) or 0.0)

    is_trigger = False
    msg = ""
    ratio = 0.10

    ai_prob = stock.get('prob', SNIPER_AGGRESSIVE_PROB)
    buy_threshold = BUY_SCORE_THRESHOLD
    strong_vpw = VPW_STRONG_LIMIT

    if strategy == 'SCALPING':
        if pos_tag == 'VCP_CANDID':
            log_info(f"[DEBUG] {code} VCP_CANDID 태그로 인한 제외")
            return

        current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        min_ratio = INVEST_RATIO_SCALPING_MIN
        max_ratio = INVEST_RATIO_SCALPING_MAX
        ratio = min_ratio + (current_ai_score / 100.0) * (max_ratio - min_ratio)

        ask_tot = int(float(ws_data.get('ask_tot', 0) or 0))
        bid_tot = int(float(ws_data.get('bid_tot', 0) or 0))
        open_price = float(ws_data.get('open', curr_price) or curr_price)
        marcap = _resolve_stock_marcap(stock, code)
        turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
        scalp_limits = get_dynamic_scalp_thresholds(marcap, turnover_hint=turnover_hint)

        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price
        max_surge = float(scalp_limits.get('max_surge', MAX_SURGE) or MAX_SURGE)
        max_intraday_surge = float(scalp_limits.get('max_intraday_surge', MAX_INTRADAY_SURGE) or MAX_INTRADAY_SURGE)
        min_liquidity = int(scalp_limits.get('min_liquidity', MIN_LIQUIDITY) or MIN_LIQUIDITY)
        big_bite_hit = False
        big_bite_armed = False
        big_bite_confirmed = False
        big_bite_info = {}
        entry_arm = _get_live_entry_arm(stock, code)

        if entry_arm:
            current_ai_score = float(entry_arm.get('ai_score', current_ai_score) or current_ai_score)
            ratio = float(entry_arm.get('ratio', ratio) or ratio)
            stock['rt_ai_prob'] = current_ai_score / 100.0
            stock['target_buy_price'] = int(entry_arm.get('target_buy_price') or curr_price)
            stock['entry_armed_resume_count'] = int(stock.get('entry_armed_resume_count', 0) or 0) + 1
            _log_entry_pipeline(
                stock,
                code,
                "entry_armed_resume",
                ai_score=f"{current_ai_score:.1f}",
                ratio=f"{ratio:.4f}",
                remaining_sec=f"{float(entry_arm.get('remaining_sec', 0.0) or 0.0):.1f}",
                armed_reason=entry_arm.get('reason'),
                dynamic_reason=entry_arm.get('dynamic_reason'),
            )
            is_trigger = True
        else:
            if fluctuation >= max_surge or intraday_surge >= max_intraday_surge:
                log_info(
                    f"[DEBUG] {code} 과매수 위험 차단 (fluctuation={fluctuation:.2f} >= {max_surge} "
                    f"또는 intraday_surge={intraday_surge:.2f} >= {max_intraday_surge})"
                )
                overlap_snapshot = _extract_ai_overlap_snapshot(ws_data=ws_data)
                stock["last_ai_overlap_snapshot"] = overlap_snapshot
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_overbought",
                    fluctuation=f"{fluctuation:.2f}",
                    intraday_surge=f"{intraday_surge:.2f}",
                    max_surge=f"{max_surge:.2f}",
                    max_intraday_surge=f"{max_intraday_surge:.2f}",
                    marcap=marcap,
                    cap_bucket=scalp_limits.get('bucket_label'),
                    **_build_ai_overlap_log_fields(
                        stock=stock,
                        ai_score=current_ai_score,
                        momentum_tag=stock.get("entry_momentum_tag"),
                        threshold_profile=stock.get("entry_threshold_profile"),
                        overbought_blocked=True,
                        blocked_stage="blocked_overbought",
                        overlap_snapshot=overlap_snapshot,
                    ),
                )
                return

            # --------------------------
            # Big-Bite: arm -> confirm (보조 확증 신호)
            # --------------------------
            try:
                tick_data = build_tick_data_from_ws(ws_data)
                big_bite_armed, big_bite_info = arm_big_bite_if_triggered(
                    stock=stock,
                    code=code,
                    ws_data=ws_data,
                    tick_data=tick_data,
                    runtime_state=BIG_BITE_STATE,
                )
                big_bite_confirmed, confirm_info = confirm_big_bite_follow_through(
                    stock=stock,
                    code=code,
                    ws_data=ws_data,
                    runtime_state=BIG_BITE_STATE,
                )
                big_bite_hit = bool(big_bite_confirmed)
                big_bite_info = {**(big_bite_info or {}), **(confirm_info or {})}
            except Exception as exc:
                log_error(f"⚠️ [Big-Bite] 보조 신호 계산 실패 ({code}): {exc}")

            stock['big_bite_confirmed'] = bool(big_bite_confirmed)
            stock['big_bite_info'] = big_bite_info or {}
            stock['big_bite_triggered'] = bool(big_bite_armed)

            if strategy == 'SCALPING':
                gate_tags = BIG_BITE_HARD_GATE_TAGS_SCALPING
            elif strategy == 'KOSDAQ_ML':
                gate_tags = BIG_BITE_HARD_GATE_TAGS_KOSDAQ
            elif strategy == 'KOSPI_ML':
                gate_tags = BIG_BITE_HARD_GATE_TAGS_KOSPI
            else:
                gate_tags = ()

            hard_gate_required = bool(
                BIG_BITE_HARD_GATE_ENABLED
                and gate_tags
                and any(tag in pos_tag for tag in gate_tags)
            )
            stock['big_bite_hard_gate_required'] = hard_gate_required
            stock['big_bite_hard_gate_blocked'] = bool(hard_gate_required and not big_bite_confirmed)
            stock['big_bite_hard_gate_tags'] = gate_tags

            if hard_gate_required and not big_bite_confirmed:
                log_info(
                    f"[DEBUG] {code} Big-Bite 하드 게이트 차단 "
                    f"(required={hard_gate_required}, triggered={big_bite_armed}, confirmed={big_bite_confirmed})"
                )
                stock['big_bite_block_reason'] = 'hard_gate'
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_big_bite_hard_gate",
                    required=hard_gate_required,
                    triggered=big_bite_armed,
                    confirmed=big_bite_confirmed,
                    position_tag=pos_tag,
                )
                return

            if big_bite_info:
                log_info(
                    f"[DEBUG] {code} Big-Bite 상태 "
                    f"(triggered={big_bite_armed}, confirmed={big_bite_confirmed}, "
                    f"impact={big_bite_info.get('impact_ratio')}, "
                    f"agg_value={big_bite_info.get('agg_value')}, "
                    f"chase_pct={big_bite_info.get('chase_pct')})"
                )

            if pos_tag == 'VCP_NEXT':
                stock['target_buy_price'] = curr_price
                is_trigger = True
                msg = (
                    f"🚀 **{stock['name']} ({code}) VCP 시초가 예약 매수!**\n"
                    f"현재가: `{curr_price:,}원` (전일 VCP NEXT 달성)"
                )
                stock['msg_audience'] = 'ADMIN_ONLY'

            else:
                if radar is None:
                    log_info(f"[DEBUG] {code} radar 객체 없음")
                    _log_entry_pipeline(stock, code, "blocked_missing_radar", strategy=strategy)
                    return

                observe_only = bool(getattr(TRADING_RULES, "SCALP_DYNAMIC_VPW_OBSERVE_ONLY", True))
                momentum_ws_data = dict(ws_data or {})
                momentum_ws_data["_position_tag"] = pos_tag
                momentum_gate = evaluate_scalping_strength_momentum(momentum_ws_data)
                stock["entry_momentum_tag"] = momentum_gate.get("position_tag")
                stock["entry_threshold_profile"] = momentum_gate.get("threshold_profile")
                if momentum_gate.get("enabled"):
                    _log_strength_momentum_observation(stock, code, momentum_gate)
                    if not observe_only and not momentum_gate.get("allowed"):
                        overlap_snapshot = _extract_ai_overlap_snapshot(ws_data=ws_data)
                        stock["last_ai_overlap_snapshot"] = overlap_snapshot
                        _log_entry_pipeline(
                            stock,
                            code,
                            "blocked_strength_momentum",
                            reason=momentum_gate.get("reason"),
                            delta=f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                            buy_value=int(momentum_gate.get("window_buy_value", 0) or 0),
                            buy_ratio=f"{float(momentum_gate.get('window_buy_ratio', 0.0) or 0.0):.2f}",
                            exec_buy_ratio=f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                            net_buy_qty=int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                            **_build_ai_overlap_log_fields(
                                stock=stock,
                                ai_score=current_ai_score,
                                momentum_tag=momentum_gate.get("position_tag"),
                                threshold_profile=momentum_gate.get("threshold_profile"),
                                overbought_blocked=False,
                                blocked_stage="blocked_strength_momentum",
                                overlap_snapshot=overlap_snapshot,
                            ),
                        )
                        return

                if current_vpw < VPW_SCALP_LIMIT:
                    shadow_candidate = None
                    if momentum_gate.get("allowed"):
                        if observe_only:
                            shadow_candidate = record_shadow_candidate(stock, code, ws_data, momentum_gate)
                            if shadow_candidate:
                                _log_entry_pipeline(
                                    stock,
                                    code,
                                    "shadow_candidate_recorded",
                                    shadow_id=shadow_candidate.get("shadow_id"),
                                    signal_price=shadow_candidate.get("signal_price"),
                                    dynamic_delta=f"{float(shadow_candidate.get('dynamic_delta', 0.0) or 0.0):.1f}",
                                    dynamic_buy_value=int(shadow_candidate.get("dynamic_window_buy_value", 0) or 0),
                                    dynamic_buy_ratio=f"{float(shadow_candidate.get('dynamic_window_buy_ratio', 0.0) or 0.0):.2f}",
                                )
                        else:
                            _log_entry_pipeline(
                                stock,
                                code,
                                "dynamic_vpw_override_pass",
                                current_vpw=f"{current_vpw:.1f}",
                                threshold=VPW_SCALP_LIMIT,
                                dynamic_reason=momentum_gate.get("reason"),
                                dynamic_delta=f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                                dynamic_buy_value=int(momentum_gate.get("window_buy_value", 0) or 0),
                                dynamic_buy_ratio=f"{float(momentum_gate.get('window_buy_ratio', 0.0) or 0.0):.2f}",
                                dynamic_exec_buy_ratio=f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                                dynamic_net_buy_qty=int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                                dynamic_profile=momentum_gate.get("threshold_profile"),
                            )
                            shadow_candidate = None
                    if not (momentum_gate.get("allowed") and not observe_only):
                        log_info(f"[DEBUG] {code} VPW 불충족 (current_vpw={current_vpw:.1f} < VPW_SCALP_LIMIT)")
                        overlap_snapshot = _extract_ai_overlap_snapshot(ws_data=ws_data)
                        stock["last_ai_overlap_snapshot"] = overlap_snapshot
                        _log_entry_pipeline(
                            stock,
                            code,
                            "blocked_vpw",
                            current_vpw=f"{current_vpw:.1f}",
                            threshold=VPW_SCALP_LIMIT,
                            dynamic_allowed=momentum_gate.get("allowed"),
                            dynamic_reason=momentum_gate.get("reason"),
                            dynamic_delta=f"{float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}",
                            dynamic_buy_value=int(momentum_gate.get("window_buy_value", 0) or 0),
                            dynamic_exec_buy_ratio=f"{float(momentum_gate.get('window_exec_buy_ratio', 0.0) or 0.0):.2f}",
                            dynamic_net_buy_qty=int(momentum_gate.get("window_net_buy_qty", 0) or 0),
                            shadow_recorded=bool(shadow_candidate),
                            **_build_ai_overlap_log_fields(
                                stock=stock,
                                ai_score=current_ai_score,
                                momentum_tag=momentum_gate.get("position_tag"),
                                threshold_profile=momentum_gate.get("threshold_profile"),
                                overbought_blocked=False,
                                blocked_stage="blocked_vpw",
                                overlap_snapshot=overlap_snapshot,
                            ),
                        )
                        return
                if liquidity_value < min_liquidity:
                    log_info(
                        f"[DEBUG] {code} 유동성 불충족 (liquidity_value={liquidity_value:,.0f} "
                        f"< MIN_LIQUIDITY={min_liquidity:,.0f})"
                    )
                    _log_entry_pipeline(
                        stock,
                        code,
                        "blocked_liquidity",
                        liquidity_value=int(liquidity_value),
                        min_liquidity=min_liquidity,
                        marcap=marcap,
                        cap_bucket=scalp_limits.get('bucket_label'),
                    )
                    return

                scanner_price = stock.get('buy_price') or 0
                if scanner_price > 0:
                    gap_pct = (curr_price - scanner_price) / scanner_price * 100
                    if gap_pct >= 1.5:
                        if code not in cooldowns:
                            print(f"⚠️ [{stock['name']}] 포착가 대비 너무 오름 (갭 +{gap_pct:.1f}%). 추격매수 포기.")
                            cooldowns[code] = time.time() + 1200
                        log_info(f"[DEBUG] {code} 포착가 대비 갭 상승 (gap_pct={gap_pct:.1f}% >= 1.5%)")
                        _log_entry_pipeline(
                            stock,
                            code,
                            "blocked_gap_from_scan",
                            gap_pct=f"{gap_pct:.1f}",
                            scanner_price=int(scanner_price),
                            curr_price=curr_price,
                        )
                        return

                current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
                target_buy_price, used_drop_pct = radar.get_smart_target_price(
                    curr_price,
                    v_pw=current_vpw,
                    ai_score=current_ai_score,
                    ask_tot=ask_tot,
                    bid_tot=bid_tot,
                )

                last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
                time_elapsed = time.time() - last_ai_time
                is_vip_target = (target_buy_price > 0) and (curr_price <= target_buy_price * 1.015)

                if is_vip_target and last_ai_time == 0:
                    print(f"⏳ [{stock['name']}] 첫 AI 분석을 시작합니다... (기계적 매수 일시 보류)")

                if ai_engine and is_vip_target and (time_elapsed > AI_WATCHING_COOLDOWN or last_ai_time == 0):
                    ai_call_executed = False
                    try:
                        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

                        if ws_data.get('orderbook') and recent_ticks:
                            ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)
                            ai_call_executed = True

                            action = ai_decision.get('action', 'WAIT')
                            ai_score = ai_decision.get('score', 50)
                            reason = ai_decision.get('reason', '사유 없음')
                            overlap_snapshot = _extract_ai_overlap_snapshot(
                                ws_data=ws_data,
                                recent_ticks=recent_ticks,
                                recent_candles=recent_candles,
                                ai_engine=ai_engine,
                            )
                            stock["last_ai_overlap_snapshot"] = overlap_snapshot
                            _log_entry_pipeline(
                                stock,
                                code,
                                "ai_confirmed",
                                action=action,
                                vip_target=is_vip_target,
                                **_build_ai_overlap_log_fields(
                                    stock=stock,
                                    ai_score=ai_score,
                                    momentum_tag=stock.get("entry_momentum_tag"),
                                    threshold_profile=stock.get("entry_threshold_profile"),
                                    overbought_blocked=False,
                                    blocked_stage="-",
                                    overlap_snapshot=overlap_snapshot,
                                ),
                                **_build_ai_ops_log_fields(
                                    ai_decision,
                                    ai_score_raw=ai_score,
                                    ai_score_after_bonus=ai_score,
                                    entry_score_threshold=75,
                                    big_bite_bonus_applied=False,
                                    ai_cooldown_blocked=False,
                                ),
                            )

                            if _should_run_watching_prompt_75_shadow(ai_decision, ai_score):
                                shadow_decision = ai_engine.analyze_target_shadow_prompt(
                                    stock['name'],
                                    ws_data,
                                    recent_ticks,
                                    recent_candles,
                                    strategy="SCALPING",
                                    prompt_type="scalping_buy75_shadow",
                                    cache_profile="watching_prompt75_shadow",
                                )
                                shadow_action = str(shadow_decision.get("action", "WAIT") or "WAIT").upper()
                                shadow_score = float(shadow_decision.get("score", 50) or 50)
                                _log_entry_pipeline(
                                    stock,
                                    code,
                                    "watching_prompt_75_shadow",
                                    main_action=str(action or "WAIT").upper(),
                                    main_score=f"{float(ai_score or 0.0):.1f}",
                                    shadow_action=shadow_action,
                                    shadow_score=f"{shadow_score:.1f}",
                                    buy_diverged=str((str(action or "WAIT").upper() == "BUY") != (shadow_action == "BUY")).lower(),
                                    score_band=f"{int(float(ai_score or 0.0))}",
                                    threshold_live=80,
                                    threshold_shadow=75,
                                    **_build_ai_ops_log_fields(
                                        shadow_decision,
                                        ai_score_raw=shadow_score,
                                        ai_score_after_bonus=shadow_score,
                                        entry_score_threshold=75,
                                        big_bite_bonus_applied=False,
                                        ai_cooldown_blocked=False,
                                    ),
                                )

                            if ai_score != 50:
                                stock['rt_ai_prob'] = ai_score / 100.0
                                current_ai_score = ai_score
                                print(
                                    f"💎 [VIP AI 확답 완료: {stock['name']}] {action} | 점수: {ai_score}점 | {reason}"
                                )

                                if action == "BUY":
                                    ai_msg = (
                                        f"🤖 <b>[VIP 종목 실시간 분석]</b>\n"
                                        f"🎯 종목: {stock['name']}\n"
                                        f"⚡ 행동: <b>{action} ({ai_score}점)</b>\n"
                                        f"🧠 사유: {reason}"
                                    )
                                    target_audience = (
                                        'VIP_ALL'
                                        if liquidity_value >= VIP_LIQUIDITY_THRESHOLD and current_ai_score >= 90
                                        else 'ADMIN_ONLY'
                                    )
                                    event_bus.publish(
                                        'TELEGRAM_BROADCAST',
                                        {'message': ai_msg, 'audience': target_audience, 'parse_mode': 'HTML'},
                                    )
                            else:
                                print(
                                    f"⚠️ [{stock['name']}] AI 판단 보류(Score 50). 기계적 로직으로 폴백합니다."
                                )
                                current_ai_score = 50

                    except Exception as e:
                        log_error(
                            f"🚨 [AI 엔진 오류] {stock['name']}({code}): {e} | "
                            "기계적 매수 모드로 폴백(Fallback)합니다."
                        )
                        current_ai_score = 50

                    if ai_call_executed:
                        LAST_AI_CALL_TIMES[code] = time.time()

                    if ai_call_executed and last_ai_time == 0:
                        if not big_bite_confirmed:
                            log_info(f"[DEBUG] {code} 첫 AI 분석 턴 대기 (SCALPING)")
                            _log_entry_pipeline(
                                stock,
                                code,
                                "first_ai_wait",
                                ai_score=f"{current_ai_score:.1f}",
                                big_bite_confirmed=big_bite_confirmed,
                                vip_target=is_vip_target,
                            )
                            return
                        log_info(f"[DEBUG] {code} Big-Bite 확인으로 첫 AI 분석 대기 스킵")

                # Big-Bite 점수 보너스 (보수적)
                boost_applied_value = 0
                if big_bite_confirmed:
                    boost_applied_value = BIG_BITE_BOOST_SCORE
                elif big_bite_armed:
                    boost_applied_value = BIG_BITE_ARMED_ENTRY_BONUS

                if boost_applied_value:
                    current_ai_score = min(100.0, current_ai_score + boost_applied_value)
                    stock['big_bite_boosted'] = bool(big_bite_confirmed)
                    stock['big_bite_boost_value'] = boost_applied_value
                    log_info(
                        f"[DEBUG] {code} Big-Bite boost 적용 (+{boost_applied_value}, "
                        f"score={current_ai_score:.1f})"
                    )
                else:
                    stock['big_bite_boosted'] = False
                    stock['big_bite_boost_value'] = 0

                if ai_engine and is_vip_target and last_ai_time > 0 and time_elapsed <= AI_WATCHING_COOLDOWN:
                    _log_entry_pipeline(
                        stock,
                        code,
                        "ai_cooldown_blocked",
                        cooldown_elapsed_sec=int(time_elapsed),
                        cooldown_threshold_sec=AI_WATCHING_COOLDOWN,
                        **_build_ai_ops_log_fields(
                            {
                                "ai_parse_ok": False,
                                "ai_parse_fail": False,
                                "ai_fallback_score_50": False,
                                "ai_response_ms": 0,
                                "ai_prompt_type": "scalping_shared",
                                "ai_result_source": "watching_cooldown",
                            },
                            ai_score_raw=current_ai_score,
                            ai_score_after_bonus=current_ai_score,
                            entry_score_threshold=75,
                            big_bite_bonus_applied=bool(boost_applied_value),
                            ai_cooldown_blocked=True,
                        ),
                    )

                if current_ai_score < 75 and current_ai_score != 50:
                    if time.time() - last_ai_time < 1.0:
                        action_str = "WAIT(진입 보류)" if current_ai_score > 40 else "DROP(진입 차단)"
                        print(f"🚫 [AI 매수 거부] {stock['name']} {action_str} (AI 점수: {current_ai_score}점)")

                    cooldown_time = AI_WAIT_DROP_COOLDOWN

                    cooldowns[code] = time.time() + cooldown_time
                    log_info(f"[DEBUG] {code} AI 점수 불충족 (current_ai_score={current_ai_score} < 75)")
                    _log_entry_pipeline(
                        stock,
                        code,
                        "blocked_ai_score",
                        threshold=75,
                        cooldown_sec=cooldown_time,
                        **_build_ai_overlap_log_fields(
                            stock=stock,
                            ai_score=current_ai_score,
                            momentum_tag=stock.get("entry_momentum_tag"),
                            threshold_profile=stock.get("entry_threshold_profile"),
                            overbought_blocked=False,
                            blocked_stage="blocked_ai_score",
                        ),
                        **_build_ai_ops_log_fields(
                            ai_decision if "ai_decision" in locals() else {},
                            ai_score_raw=current_ai_score,
                            ai_score_after_bonus=current_ai_score,
                            entry_score_threshold=75,
                            big_bite_bonus_applied=bool(boost_applied_value),
                            ai_cooldown_blocked=False,
                        ),
                    )
                    return

                final_target_buy_price, final_used_drop_pct = radar.get_smart_target_price(
                    curr_price,
                    v_pw=current_vpw,
                    ai_score=current_ai_score,
                    ask_tot=ask_tot,
                    bid_tot=bid_tot,
                )

                stock['target_buy_price'] = final_target_buy_price
                _activate_entry_arm(
                    stock,
                    code,
                    ai_score=current_ai_score,
                    ratio=ratio,
                    target_buy_price=final_target_buy_price,
                    current_vpw=current_vpw,
                    reason='qualification_passed',
                    dynamic_reason=momentum_gate.get('reason'),
                )
                is_trigger = True
                if big_bite_confirmed:
                    stock['big_bite_boosted'] = True
                    log_info(f"[DEBUG] {code} Big-Bite 보조 확증 신호 확인됨 (진입 조건 통과)")

    elif strategy in ['KOSDAQ_ML', 'KOSPI_ML']:
        if radar is None:
            log_info(f"[DEBUG] {code} radar 객체 없음 (KOSDAQ_ML/KOSPI_ML)")
            _log_entry_pipeline(stock, code, "blocked_missing_radar", strategy=strategy)
            return

        if strategy == 'KOSDAQ_ML':
            marcap = _resolve_stock_marcap(stock, code)
            turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
            swing_gap = get_dynamic_swing_gap_threshold(strategy, marcap, turnover_hint=turnover_hint)
            max_gap = float(swing_gap.get('threshold', _get_swing_gap_threshold(strategy)) or _get_swing_gap_threshold(strategy))
            if fluctuation >= max_gap:
                log_info(
                    f"[DEBUG] {code} 갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})"
                )
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_swing_gap",
                    strategy=strategy,
                    fluctuation=f"{fluctuation:.2f}",
                    threshold=f"{max_gap:.2f}",
                    marcap=marcap,
                    cap_bucket=swing_gap.get('bucket_label'),
                )
                return

            vpw_limit_base = getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105)
            strong_vpw = getattr(TRADING_RULES, 'VPW_STRONG_KOSDAQ_LIMIT', 120)
            buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_KOSDAQ_THRESHOLD', 80)
            vpw_condition = current_vpw >= vpw_limit_base
            ratio_min = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MIN', 0.05)
            ratio_max = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MAX', 0.15)
            ai_score_threshold = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60)

            ai_prob = stock.get('prob', getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70))
            v_pw_limit = vpw_limit_base if ai_prob >= 0.70 else strong_vpw

        else:
            marcap = _resolve_stock_marcap(stock, code)
            turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
            swing_gap = get_dynamic_swing_gap_threshold(strategy, marcap, turnover_hint=turnover_hint)
            max_gap = float(swing_gap.get('threshold', _get_swing_gap_threshold(strategy)) or _get_swing_gap_threshold(strategy))
            if fluctuation >= max_gap:
                log_info(
                    f"[DEBUG] {code} 갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})"
                )
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_swing_gap",
                    strategy=strategy,
                    fluctuation=f"{fluctuation:.2f}",
                    threshold=f"{max_gap:.2f}",
                    marcap=marcap,
                    cap_bucket=swing_gap.get('bucket_label'),
                )
                return

            vpw_limit_base = 100
            strong_vpw = getattr(TRADING_RULES, 'VPW_STRONG_LIMIT', 105)
            buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 70)
            vpw_condition = current_vpw >= 103
            ratio_min = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MIN', 0.10)
            ratio_max = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MAX', 0.30)
            ai_score_threshold = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSPI', 60)

            ai_prob = stock.get('prob', getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70))
            v_pw_limit = vpw_limit_base if ai_prob >= 0.70 else strong_vpw

        score, prices, conclusion, checklist, metrics = radar.analyze_signal_integrated(ws_data, ai_prob)
        is_shooting = current_vpw >= v_pw_limit

        if (score >= buy_threshold or is_shooting) and vpw_condition:
            gatekeeper_error_cd = getattr(TRADING_RULES, 'ML_GATEKEEPER_ERROR_COOLDOWN', 60 * 10)
            gatekeeper = None
            gatekeeper_allow = False
            action_label = 'UNKNOWN'
            gatekeeper_eval_ms = 0
            gatekeeper_cd_policy = 'neutral_hold'

            if not ai_engine:
                log_error(f"🚨 [{strategy} Gatekeeper 미초기화] {stock['name']}({code})")
                cooldowns[code] = time.time() + gatekeeper_error_cd
                _log_entry_pipeline(stock, code, "blocked_gatekeeper_missing", strategy=strategy)
                return

            try:
                realtime_ctx = None
                now_ts = time.time()
                gatekeeper_fast_sig = _build_gatekeeper_fast_signature(stock, ws_data, strategy, score)
                gatekeeper_fast_snapshot = _build_gatekeeper_fast_snapshot(stock, ws_data, strategy, score)
                gatekeeper_fast_reuse_sec = _resolve_gatekeeper_fast_reuse_sec()
                gatekeeper_fast_max_ws_age = float(getattr(TRADING_RULES, 'AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC', 2.0) or 2.0)
                gatekeeper_ws_age_sec = _get_ws_snapshot_age_sec(ws_data)
                fast_sig_matches = gatekeeper_fast_sig == stock.get('last_gatekeeper_fast_signature')
                fast_sig_age = _resolve_reference_age_sec(
                    stock.get('last_gatekeeper_fast_at'),
                    fallback_ts=stock.get('last_gatekeeper_action_at'),
                    now_ts=now_ts,
                )
                fast_sig_age_str = "-" if fast_sig_age is None else f"{fast_sig_age:.1f}"
                near_score_boundary = abs(float(score) - float(buy_threshold)) <= 3.0
                fast_sig_fresh = fast_sig_age is not None and fast_sig_age < gatekeeper_fast_reuse_sec
                ws_fresh = gatekeeper_ws_age_sec is None or gatekeeper_ws_age_sec <= gatekeeper_fast_max_ws_age
                has_last_action = bool(str(stock.get('last_gatekeeper_action', '') or '').strip())
                has_last_allow_flag = 'last_gatekeeper_allow_entry' in stock
                can_fast_reuse = (
                    fast_sig_matches
                    and fast_sig_fresh
                    and ws_fresh
                    and not near_score_boundary
                    and has_last_action
                    and has_last_allow_flag
                )

                if can_fast_reuse:
                    gatekeeper = {
                        'allow_entry': bool(stock.get('last_gatekeeper_allow_entry', False)),
                        'action_label': stock.get('last_gatekeeper_action', 'UNKNOWN'),
                        'report': stock.get('last_gatekeeper_report', ''),
                        'eval_ms': 0,
                        'cache_hit': True,
                        'cache_mode': 'fast_reuse',
                    }
                    gatekeeper_eval_ms = 0
                    _log_entry_pipeline(
                        stock,
                        code,
                        "gatekeeper_fast_reuse",
                        strategy=strategy,
                        action=gatekeeper.get('action_label', 'UNKNOWN'),
                        age_sec=fast_sig_age_str,
                        ws_age_sec="-" if gatekeeper_ws_age_sec is None else f"{gatekeeper_ws_age_sec:.2f}",
                    )
                    is_new_evaluation = False
                else:
                    # age 계산: 값이 없으면 "-" sentinel 사용 (p95 오염 방지)
                    action_age_sec = _resolve_reference_age_sec(
                        stock.get('last_gatekeeper_action_at'),
                        now_ts=now_ts,
                    )
                    allow_age_sec = _resolve_reference_age_sec(
                        stock.get('last_gatekeeper_allow_entry_at'),
                        now_ts=now_ts,
                    )
                    action_age_sec_str = "-" if action_age_sec is None else f"{action_age_sec:.2f}"
                    allow_age_sec_str = "-" if allow_age_sec is None else f"{allow_age_sec:.2f}"

                    sig_delta = _describe_snapshot_deltas(
                        stock.get('last_gatekeeper_fast_snapshot', {}),
                        gatekeeper_fast_snapshot,
                        limit=5
                    ) or "-"
                    _log_entry_pipeline(
                        stock,
                        code,
                        "gatekeeper_fast_reuse_bypass",
                        strategy=strategy,
                        score=round(float(score), 2),
                        age_sec=fast_sig_age_str,
                        ws_age_sec="-" if gatekeeper_ws_age_sec is None else f"{gatekeeper_ws_age_sec:.2f}",
                        action_age_sec=action_age_sec_str,
                        allow_entry_age_sec=allow_age_sec_str,
                        sig_delta=sig_delta,
                        reason_codes=_reason_codes(
                            sig_changed=fast_sig_matches,
                            age_expired=fast_sig_fresh,
                            ws_stale=ws_fresh,
                            score_boundary=not near_score_boundary,
                            missing_action=has_last_action,
                            missing_allow_flag=has_last_allow_flag,
                        ),
                    )
                    realtime_ctx = kiwoom_utils.build_realtime_analysis_context(
                        token=KIWOOM_TOKEN,
                        code=code,
                        ws_data=ws_data,
                        market_cap=_resolve_stock_marcap(stock, code),
                        strat_label=strategy,
                        position_status='NONE',
                        avg_price=0,
                        pnl_pct=0.0,
                        trailing_pct=0.0,
                        stop_pct=0.0,
                        target_price=curr_price,
                        target_reason='WATCHING 최종 진입 Gatekeeper 검증',
                        score=float(score),
                        conclusion=conclusion,
                        quant_metrics=metrics,
                    )
                    gatekeeper_started_at = time.perf_counter()
                    gatekeeper = ai_engine.evaluate_realtime_gatekeeper(
                        stock_name=stock['name'],
                        stock_code=code,
                        realtime_ctx=realtime_ctx,
                        analysis_mode='SWING',
                    )
                    gatekeeper_eval_ms = int((time.perf_counter() - gatekeeper_started_at) * 1000)
                    gatekeeper['eval_ms'] = gatekeeper_eval_ms
                    record_gatekeeper_snapshot(
                        stock=stock,
                        code=code,
                        strategy=strategy,
                        realtime_ctx=realtime_ctx,
                        gatekeeper=gatekeeper,
                    )
                    # 신규 평가 결과는 저장하고 timestamp 갱신 (fast_reuse는 갱신 안 함)
                    is_new_evaluation = True
                    current_time = time.time()
                    stock['last_gatekeeper_action_at'] = current_time
                    stock['last_gatekeeper_allow_entry_at'] = current_time
                    stock['last_gatekeeper_fast_snapshot'] = gatekeeper_fast_snapshot
                    stock['last_gatekeeper_fast_at'] = current_time
                    
                LAST_AI_CALL_TIMES[code] = time.time()
                action_label = gatekeeper.get('action_label', 'UNKNOWN')
                gatekeeper_allow = bool(gatekeeper.get('allow_entry', False))
                gatekeeper_cache_mode = str(gatekeeper.get('cache_mode', 'hit' if gatekeeper.get('cache_hit') else 'miss'))
                stock['last_gatekeeper_action'] = action_label
                stock['last_gatekeeper_report'] = gatekeeper.get('report', '')
                stock['last_gatekeeper_eval_ms'] = gatekeeper_eval_ms
                stock['last_gatekeeper_allow_entry'] = gatekeeper_allow
                stock['last_gatekeeper_cache_mode'] = gatekeeper_cache_mode
                stock['last_gatekeeper_fast_signature'] = gatekeeper_fast_sig
                if is_new_evaluation and realtime_ctx is not None:
                    _submit_gatekeeper_dual_persona_shadow(
                        stock_name=stock['name'],
                        code=code,
                        strategy=strategy,
                        realtime_ctx=realtime_ctx,
                        gatekeeper=gatekeeper,
                        record_id=stock.get('id'),
                    )
            except Exception as e:
                log_error(f"🚨 [{strategy} Gatekeeper 오류] {stock['name']}({code}): {e}")
                cooldowns[code] = time.time() + gatekeeper_error_cd
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_gatekeeper_error",
                    strategy=strategy,
                    cooldown_sec=gatekeeper_error_cd,
                    gatekeeper_eval_ms=gatekeeper_eval_ms,
                )
                return

            if not gatekeeper_allow:
                gatekeeper_reject_cd, gatekeeper_cd_policy = _resolve_gatekeeper_reject_cooldown(action_label)
                print(f"🚫 [{strategy} Gatekeeper 거부] {stock['name']} ({action_label})")
                cooldowns[code] = time.time() + gatekeeper_reject_cd
                _log_entry_pipeline(
                    stock,
                    code,
                    "blocked_gatekeeper_reject",
                    strategy=strategy,
                    action=action_label,
                    cooldown_sec=gatekeeper_reject_cd,
                    cooldown_policy=gatekeeper_cd_policy,
                    gatekeeper_eval_ms=gatekeeper_eval_ms,
                    gatekeeper_cache=stock.get('last_gatekeeper_cache_mode', 'miss'),
                )
                return

            blocked, block_reason = _should_block_swing_entry(stock.get('strategy', ''))
            if blocked:
                print(f"⛔ [시장환경필터] {stock['name']}({code}) 스윙 진입 보류 - {block_reason}")
                log_info(f"[DEBUG] {code} 시장환경필터에 의한 스윙 진입 보류 (reason: {block_reason})")
                _log_entry_pipeline(stock, code, "market_regime_block", strategy=strategy)
                return

            _log_entry_pipeline(
                stock,
                code,
                "market_regime_pass",
                strategy=strategy,
                gatekeeper=action_label,
                score=round(float(score), 2),
                gatekeeper_eval_ms=gatekeeper_eval_ms,
                gatekeeper_cache=stock.get('last_gatekeeper_cache_mode', 'miss'),
            )

            score_weight = max(0.0, min(1.0, (float(score) - buy_threshold) / max(1.0, (100 - buy_threshold))))
            ratio = ratio_min + (score_weight * (ratio_max - ratio_min))
            if is_shooting and ratio < ((ratio_min + ratio_max) / 2):
                ratio = (ratio_min + ratio_max) / 2

            is_trigger = True
            stock['target_buy_price'] = curr_price
            stock['msg_audience'] = 'VIP_ALL'
            _publish_gatekeeper_report_proxy(stock, code, gatekeeper, allowed=True)

    if is_trigger:
        if not admin_id:
            print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID가 없습니다.")
            log_info(f"[DEBUG] {code} 관리자 ID 없음")
            _log_entry_pipeline(stock, code, "blocked_no_admin")
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        uncapped_target_budget = int(max(float(deposit) * float(ratio), 0.0))
        budget_cap = 0
        if strategy == 'SCALPING':
            budget_cap = int(getattr(TRADING_RULES, 'SCALPING_MAX_BUY_BUDGET_KRW', 0) or 0)
        target_budget, safe_budget, real_buy_qty, used_safety_ratio = kiwoom_orders.describe_buy_capacity(
            curr_price,
            deposit,
            ratio,
            max_budget=budget_cap,
        )
        budget_cap_applied = budget_cap > 0 and target_budget < uncapped_target_budget
        budget_cap_msg = f", 절대한도 {budget_cap:,}원 적용" if budget_cap_applied else ""

        if real_buy_qty <= 0:
            zero_qty_cooldown_sec = _resolve_zero_qty_cooldown_sec(deposit)
            is_zero_deposit = int(float(deposit or 0)) <= 0
            if is_zero_deposit:
                print(
                    f"⚠️ [매수보류] {stock['name']}: 주문가능금액 조회가 0원으로 반환되어 재조회 대기합니다. "
                    f"(주문가능금액 {deposit:,}원, 전략비중 {ratio:.1%}, 안전계수 {used_safety_ratio:.0%}, "
                    f"실사용예산 {safe_budget:,}원, 현재가 {curr_price:,}원, 재조회대기 {zero_qty_cooldown_sec}초)"
                )
            else:
                print(
                    f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다. "
                    f"(주문가능금액 {deposit:,}원, 전략비중 {ratio:.1%}, 안전계수 {used_safety_ratio:.0%}, "
                    f"실사용예산 {safe_budget:,}원, 현재가 {curr_price:,}원{budget_cap_msg})"
                )
            log_info(
                f"[DEBUG] {code} 매수 수량 0주 "
                f"(deposit={deposit}, ratio={ratio:.4f}, uncapped_target_budget={uncapped_target_budget}, "
                f"target_budget={target_budget}, "
                f"safe_budget={safe_budget}, safety_ratio={used_safety_ratio:.4f}, curr_price={curr_price}, "
                f"retry_cooldown_sec={zero_qty_cooldown_sec})"
            )
            cooldowns[code] = time.time() + zero_qty_cooldown_sec
            _log_entry_pipeline(
                stock,
                code,
                "blocked_zero_qty",
                deposit=deposit,
                ratio=f"{ratio:.4f}",
                target_budget=target_budget,
                safe_budget=safe_budget,
                safety_ratio=f"{used_safety_ratio:.4f}",
                curr_price=curr_price,
                budget_cap=budget_cap if budget_cap_applied else "-",
                cooldown_sec=zero_qty_cooldown_sec,
            )
            return

        _log_entry_pipeline(
            stock,
            code,
            "budget_pass",
            deposit=deposit,
            ratio=f"{ratio:.4f}",
            target_budget=target_budget,
            safe_budget=safe_budget,
            safety_ratio=f"{used_safety_ratio:.4f}",
            budget_cap=budget_cap if budget_cap_applied else "-",
            qty=real_buy_qty,
        )

        if strategy == 'SCALPING':
            order_type_code = "00"
            final_price = int(float(stock.get('target_buy_price', curr_price) or curr_price))
        else:
            order_type_code = "6"
            final_price = 0

        latency_signal_strength = float(stock.get('rt_ai_prob', stock.get('prob', 0.0)) or 0.0)
        latency_signal_score = latency_signal_strength * 100.0
        latency_gate = evaluate_live_buy_entry(
            stock=stock,
            code=code,
            ws_data=ws_data,
            strategy_id=strategy,
            planned_qty=real_buy_qty,
            signal_price=curr_price,
            signal_strength=latency_signal_strength,
            target_buy_price=final_price if strategy == 'SCALPING' else 0,
        )
        stock['latency_entry_state'] = latency_gate.get('latency_state')
        stock['latency_entry_decision'] = latency_gate.get('decision')
        stock['latency_entry_reason'] = latency_gate.get('reason')

        entry_mode = latency_gate.get('mode', 'reject')
        log_info(
            f"[LATENCY_ENTRY_DECISION] {stock.get('name')}({code}) "
            f"mode={entry_mode} decision={latency_gate.get('decision')} "
            f"latency={latency_gate.get('latency_state')} "
            f"signal={latency_gate.get('signal_price')} latest={latency_gate.get('latest_price')} "
            f"allowed_slippage={latency_gate.get('computed_allowed_slippage')} "
            f"orders={len(latency_gate.get('orders') or [])}"
        )
        if not latency_gate.get('allowed') or entry_mode == 'reject':
            log_info(
                f"[LATENCY_ENTRY_BLOCK] {stock.get('name')}({code}) "
                f"decision={latency_gate.get('decision')} "
                f"latency={latency_gate.get('latency_state')} "
                f"reason={latency_gate.get('reason')} "
                f"signal={latency_gate.get('signal_price')} latest={latency_gate.get('latest_price')} "
                f"ws_age_ms={latency_gate.get('ws_age_ms')} "
                f"ws_jitter_ms={latency_gate.get('ws_jitter_ms')} "
                f"spread_ratio={latency_gate.get('spread_ratio')} "
                f"quote_stale={latency_gate.get('quote_stale')}"
            )
            clear_signal_reference(stock)
            _log_entry_pipeline(
                stock,
                code,
                "latency_block",
                decision=latency_gate.get('decision'),
                latency=latency_gate.get('latency_state'),
                reason=latency_gate.get('reason'),
                ws_age_ms=latency_gate.get('ws_age_ms'),
                ws_jitter_ms=latency_gate.get('ws_jitter_ms'),
                spread_ratio=f"{float(latency_gate.get('spread_ratio', 0.0) or 0.0):.6f}",
                quote_stale=bool(latency_gate.get('quote_stale')),
                latency_danger_reasons=latency_gate.get('latency_danger_reasons'),
                signal_price=int(latency_gate.get('signal_price', 0) or 0),
                latest_price=int(latency_gate.get('latest_price', 0) or 0),
                computed_allowed_slippage=int(latency_gate.get('computed_allowed_slippage', 0) or 0),
                latency_canary_applied=bool(latency_gate.get('latency_canary_applied')),
                latency_canary_reason=latency_gate.get('latency_canary_reason'),
                **_build_ai_overlap_log_fields(
                    stock=stock,
                    ai_score=latency_signal_score,
                    momentum_tag=stock.get("entry_momentum_tag"),
                    threshold_profile=stock.get("entry_threshold_profile"),
                    overbought_blocked=False,
                    blocked_stage="latency_block",
                ),
            )
            return

        requested_qty = int(real_buy_qty or 0)
        planned_orders = latency_gate.get('orders') or []
        if entry_mode == "fallback":
            fallback_qty_multiplier = float(getattr(TRADING_RULES, "SCALP_FALLBACK_ENTRY_QTY_MULTIPLIER", 1.0) or 1.0)
            adjusted_orders, original_qty, scaled_qty = _apply_fallback_qty_canary(
                planned_orders,
                qty_multiplier=fallback_qty_multiplier,
            )
            if adjusted_orders:
                planned_orders = adjusted_orders
                latency_gate["orders"] = planned_orders
            if scaled_qty > 0:
                requested_qty = scaled_qty
            if scaled_qty > 0 and scaled_qty < original_qty:
                _log_entry_pipeline(
                    stock,
                    code,
                    "fallback_qty_canary_applied",
                    qty_multiplier=f"{max(0.1, min(1.0, fallback_qty_multiplier)):.2f}",
                    original_qty=original_qty,
                    scaled_qty=scaled_qty,
                    legs=len(planned_orders),
                )
                log_info(
                    f"[FALLBACK_QTY_CANARY] {stock.get('name')}({code}) "
                    f"multiplier={max(0.1, min(1.0, fallback_qty_multiplier)):.2f} "
                    f"qty={original_qty}->{scaled_qty}"
                )

        _log_entry_pipeline(
            stock,
            code,
            "latency_pass",
            mode=entry_mode,
            decision=latency_gate.get('decision'),
            latency=latency_gate.get('latency_state'),
            orders=len(planned_orders),
            reason=latency_gate.get('reason'),
            ws_age_ms=latency_gate.get('ws_age_ms'),
            ws_jitter_ms=latency_gate.get('ws_jitter_ms'),
            spread_ratio=f"{float(latency_gate.get('spread_ratio', 0.0) or 0.0):.6f}",
            quote_stale=bool(latency_gate.get('quote_stale')),
            latency_danger_reasons=latency_gate.get('latency_danger_reasons'),
            signal_price=int(latency_gate.get('signal_price', 0) or 0),
            latest_price=int(latency_gate.get('latest_price', 0) or 0),
            computed_allowed_slippage=int(latency_gate.get('computed_allowed_slippage', 0) or 0),
            latency_canary_applied=bool(latency_gate.get('latency_canary_applied')),
            latency_canary_reason=latency_gate.get('latency_canary_reason'),
            **_build_ai_overlap_log_fields(
                stock=stock,
                ai_score=latency_signal_score,
                momentum_tag=stock.get("entry_momentum_tag"),
                threshold_profile=stock.get("entry_threshold_profile"),
                overbought_blocked=False,
                blocked_stage="-",
            ),
        )

        if is_buy_side_paused():
            log_info(
                f"[TRADING_PAUSED_BLOCK] buy order blocked "
                f"{stock.get('name')}({code}) strategy={strategy} state={get_pause_state_label()}"
            )
            clear_signal_reference(stock)
            _log_entry_pipeline(stock, code, "blocked_pause", strategy=strategy)
            return

        big_bite_summary = ""
        if stock.get('big_bite_triggered') or stock.get('big_bite_confirmed'):
            info = stock.get('big_bite_info') or {}
            big_bite_summary = (
                f"\n🧪 Big-Bite: "
                f"T={stock.get('big_bite_triggered')} / C={stock.get('big_bite_confirmed')} / "
                f"Boost=+{stock.get('big_bite_boost_value', 0)}"
                f"\n└ agg={info.get('agg_value')} impact={info.get('impact_ratio')} chase={info.get('chase_pct')}"
            )
            stock['msg_audience'] = 'ADMIN_ONLY'

        msg = msg or (
            f"✅ **{stock['name']} ({code}) 진입 주문 전송!**\n"
            f"전략: `{strategy}`\n"
            f"현재가: `{curr_price:,}원`\n"
            f"주문 수량: `{requested_qty}주`"
            f"{big_bite_summary}"
        )

        successful_orders = []
        for planned_order in planned_orders:
            request = _resolve_live_entry_order_request(
                strategy=strategy,
                entry_mode=entry_mode,
                planned_order=planned_order,
                default_order_type_code=order_type_code,
                default_price=final_price,
            )
            qty = request['qty']
            price = request['price']
            if qty <= 0:
                _log_entry_pipeline(
                    stock,
                    code,
                    "skip_order_leg_zero_qty",
                    tag=request['tag'],
                )
                continue

            _log_entry_pipeline(
                stock,
                code,
                "order_leg_request",
                tag=request['tag'],
                qty=qty,
                price=price,
                order_type=request['order_type_code'],
                tif=request['tif'],
            )

            res = kiwoom_orders.send_buy_order(
                code,
                qty,
                price,
                request['order_type_code'],
                token=KIWOOM_TOKEN,
                order_type_desc="매수" if strategy == 'SCALPING' else "최유리지정가",
                tif=request['tif'],
            )

            if not isinstance(res, dict):
                _log_entry_pipeline(stock, code, "order_leg_no_response", tag=request['tag'])
                continue
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd != '0':
                log_info(
                    f"[LATENCY_ENTRY_ORDER_FAIL] {stock.get('name')}({code}) "
                    f"tag={planned_order.get('tag')} msg={res.get('return_msg')}"
                )
                _log_entry_pipeline(
                    stock,
                    code,
                    "order_leg_fail",
                    tag=request['tag'],
                    return_code=rt_cd,
                    message=res.get('return_msg') or res.get('err_msg'),
                )
                continue

            ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            successful_orders.append({
                'tag': request['tag'],
                'qty': qty,
                'price': price,
                'ord_no': ord_no,
                'tif': request['tif'],
                'order_type': request['order_type_code'],
                'status': 'OPEN',
                'filled_qty': 0,
                'sent_at': time.time(),
            })
            _stage_buy_order_submission(
                stock=stock,
                code=code,
                curr_price=curr_price,
                requested_qty=requested_qty,
                msg=msg,
                entry_orders=successful_orders,
            )
            log_info(
                f"[LATENCY_ENTRY_ORDER_SENT] {stock.get('name')}({code}) "
                f"tag={request['tag']} qty={qty} price={price} "
                f"type={request['order_type_code']} tif={request['tif']} ord_no={ord_no}"
            )
            _log_entry_pipeline(stock, code, "order_leg_sent", tag=request['tag'], ord_no=ord_no)

        if not successful_orders:
            print(f"❌ [{stock['name']}] 매수 주문 전송 실패 (성공 주문 없음)")
            clear_signal_reference(stock)
            _log_entry_pipeline(stock, code, "order_bundle_failed")
            return

        stock['entry_mode'] = entry_mode
        _finalize_buy_order_submission(
            stock=stock,
            code=code,
            curr_price=curr_price,
            requested_qty=requested_qty,
            msg=msg,
            entry_orders=successful_orders,
        )
        _log_entry_pipeline(
            stock,
            code,
            "order_bundle_submitted",
            entry_mode=entry_mode,
            requested_qty=requested_qty,
            legs=len(successful_orders),
        )

        if strategy in ['SCALPING', 'SCALP']:
            alerted_stocks.add(code)
        else:
            stock['msg_audience'] = 'VIP_ALL'

        _publish_entry_mode_summary(
            stock,
            code,
            entry_mode=entry_mode,
            latency_gate=latency_gate,
        )

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=stock.get('id')).update({
                    "status": "BUY_ORDERED",
                    "buy_price": curr_price,
                    "buy_qty": requested_qty,
                })
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} BUY_ORDERED 장부 업데이트 실패: {e}")

        clear_signal_reference(stock)



def handle_holding_state(stock, code, ws_data, admin_id, market_regime, radar=None, ai_engine=None):
    """
    [HOLDING 상태] 보유 종목 익절/손절 감시 및 AI 조기 개입
    """
    global LAST_AI_CALL_TIMES

    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    highest_prices = HIGHEST_PRICES

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
    stock['position_tag'] = pos_tag

    curr_p = int(float(ws_data.get('curr', 0) or 0))
    buy_p = float(stock.get('buy_price', 0) or 0)
    _reconcile_pending_entry_orders(stock, code, strategy)
    if curr_p <= 0 or buy_p <= 0:
        return

    # --------------------------------------------------------
    # HOLDING 제어 흐름(요약)
    # 1) 현재가/평단/수익률 계산
    # 2) 최고가/보유시간 등 갱신
    # 3) 전략별 청산 조건 평가
    # 4) SELL 신호면 즉시 매도 처리 후 종료
    # 5) stop/trailing 보정(전략별 내장)
    # 6) 추가매수 공통 게이트 확인
    # 7) 전략별 추가매수 시그널 평가
    # 8) 조건 만족 시 추가매수 주문 전송
    # 9) 아니면 HOLD 유지
    # --------------------------------------------------------

    if code not in highest_prices:
        highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)

    profit_rate = calculate_net_profit_rate(buy_p, curr_p)
    peak_profit = calculate_net_profit_rate(buy_p, highest_prices[code])
    trailing_stop_price = float(stock.get('trailing_stop_price') or 0)
    hard_stop_price = float(stock.get('hard_stop_price') or 0)

    if strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        last_log = LAST_LOG_TIMES.get(code, 0)
        if time.time() - last_log >= 600:
            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            log_info(
                f"[{strategy}] 보유 종목 감시 중: {stock['name']}({code}) 수익률 {profit_rate:+.2f}%, "
                f"AI 점수 {current_ai_score:.0f}점"
            )
            LAST_LOG_TIMES[code] = time.time()

    def _dispatch_scalp_preset_exit(*, sell_reason_type, reason, exit_rule):
        target_id = stock.get('id')
        expected_qty = int(stock.get('buy_qty', 0) or 0)
        orig_ord_no = stock.get('preset_tp_ord_no', '')
        preset_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        preset_held_sec = 0
        try:
            if stock.get('order_time'):
                preset_held_sec = max(0, int(time.time() - float(stock.get('order_time') or 0)))
        except Exception:
            preset_held_sec = 0

        stock['last_exit_rule'] = exit_rule or ''
        stock['last_exit_reason'] = reason
        _log_holding_pipeline(
            stock,
            code,
            "exit_signal",
            sell_reason_type=sell_reason_type,
            reason=reason,
            exit_rule=exit_rule or "-",
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            current_ai_score=f"{preset_ai_score:.0f}",
            held_sec=preset_held_sec,
            curr_price=curr_p,
            buy_price=buy_p,
            buy_qty=expected_qty,
        )

        try:
            if target_id:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "SELL_ORDERED"})
        except Exception as e:
            print(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")

        rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
        ord_no = ''
        if rem_qty > 0:
            sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
            stock['exit_requested'] = True
            stock['exit_order_type'] = '16'
            stock['exit_order_time'] = time.time()
            ord_no = str(sell_res.get('ord_no', '') or '') if isinstance(sell_res, dict) else ''
            if ord_no:
                stock['sell_ord_no'] = ord_no
            stock['sell_order_time'] = time.time()
            sign = "📉 [손절 주문]" if sell_reason_type == 'LOSS' else "🎊 [익절 주문]"
            stock['pending_sell_msg'] = (
                f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n"
                f"사유: `{reason}`\n"
                f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)"
            )
            _log_holding_pipeline(
                stock,
                code,
                "sell_order_sent",
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule or "-",
                qty=rem_qty,
                ord_no=ord_no or "-",
                order_type=stock.get("exit_order_type") or "-",
                profit_rate=f"{profit_rate:+.2f}",
            )

        stock['status'] = 'SELL_ORDERED'
        stock['sell_target_price'] = curr_p

    if stock.get('exit_mode') == 'SCALP_PRESET_TP':
        if stock.get('exit_requested'):
            return

        profit_rate = calculate_net_profit_rate(buy_p, curr_p) if buy_p > 0 else 0.0
        preset_hard_stop_pct = float(
            stock.get(
                'hard_stop_pct',
                getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_PCT', -0.7),
            )
            or getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_PCT', -0.7)
        )
        preset_hard_stop_grace_sec = int(
            stock.get(
                'hard_stop_grace_sec',
                getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_GRACE_SEC', 0),
            )
            or 0
        )
        preset_hard_stop_emergency_pct = float(
            stock.get(
                'hard_stop_emergency_pct',
                getattr(
                    TRADING_RULES,
                    'SCALP_PRESET_HARD_STOP_EMERGENCY_PCT',
                    min(preset_hard_stop_pct - 0.5, -1.2),
                ),
            )
            or getattr(
                TRADING_RULES,
                'SCALP_PRESET_HARD_STOP_EMERGENCY_PCT',
                min(preset_hard_stop_pct - 0.5, -1.2),
            )
        )
        preset_held_sec = _resolve_holding_elapsed_sec(stock)
        preset_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        _emit_scalp_hard_time_stop_shadow(
            stock=stock,
            code=code,
            held_sec=preset_held_sec,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=preset_ai_score,
            ai_exit_min_loss_pct=float(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MIN_LOSS_PCT', -0.7) or -0.7),
        )

        if profit_rate <= preset_hard_stop_pct:
            within_grace = preset_hard_stop_grace_sec > 0 and preset_held_sec < preset_hard_stop_grace_sec
            emergency_break = profit_rate <= preset_hard_stop_emergency_pct
            if within_grace and not emergency_break:
                _log_holding_pipeline(
                    stock,
                    code,
                    "preset_hard_stop_grace",
                    profit_rate=f"{profit_rate:+.2f}",
                    held_sec=preset_held_sec,
                    grace_sec=preset_hard_stop_grace_sec,
                    hard_stop_pct=f"{preset_hard_stop_pct:+.2f}",
                    emergency_pct=f"{preset_hard_stop_emergency_pct:+.2f}",
                )
            else:
                print(
                    f"🔪 [SCALP 출구엔진] {stock['name']} 손절선 터치({profit_rate:.2f}%). "
                    "즉각 최유리(IOC) 청산!"
                )
                _dispatch_scalp_preset_exit(
                    sell_reason_type="LOSS",
                    reason=f"🛑 SCALP 출구엔진 손절선 도달 ({preset_hard_stop_pct:+.2f}%)",
                    exit_rule="scalp_preset_hard_stop_pct",
                )
                return

        if profit_rate >= 0.8 and not stock.get('ai_review_done', False):
            print(f"🤖 [SCALP 출구엔진] {stock['name']} +0.8% 도달! AI 1회 검문 실시...")
            stock['ai_review_done'] = True

            if ai_engine:
                try:
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    ai_decision = ai_engine.analyze_target(
                        stock['name'], ws_data, recent_ticks, [], strategy="SCALPING"
                    )
                    ai_action = ai_decision.get('action', 'WAIT')
                    ai_score = ai_decision.get('score', 50)

                    stock['ai_review_action'] = ai_action
                    stock['ai_review_score'] = ai_score

                    # Shared scalping prompt still emits BUY|WAIT|DROP today.
                    # Keep SELL as an explicit placeholder until a dedicated HOLDING/exit action schema lands.
                    if ai_action in ['SELL', 'DROP']:
                        _log_holding_pipeline(
                            stock,
                            code,
                            "scalp_preset_tp_ai_exit_action",
                            ai_action_raw=ai_action,
                            ai_reason_raw=ai_decision.get('reason', '-'),
                            ai_action_used_for_exit=str(ai_action in ['SELL', 'DROP']).lower(),
                            **_build_ai_ops_log_fields(
                                ai_decision,
                                ai_score_raw=ai_score,
                                ai_score_after_bonus=ai_score,
                                ai_cooldown_blocked=False,
                            ),
                        )
                        print(
                            "🛑 [SCALP 출구엔진 AI] 모멘텀 둔화 감지. 1.5% 포기 후 즉시 최유리(IOC) "
                            "청산!"
                        )
                        _dispatch_scalp_preset_exit(
                            sell_reason_type="MOMENTUM_DECAY",
                            reason="🛑 SCALP 출구엔진 AI 모멘텀 둔화 즉시청산",
                            exit_rule="scalp_preset_ai_review_exit",
                        )
                        return
                    else:
                        _log_holding_pipeline(
                            stock,
                            code,
                            "scalp_preset_tp_ai_hold_action",
                            ai_action_raw=ai_action,
                            ai_reason_raw=ai_decision.get('reason', '-'),
                            ai_action_used_for_exit="false",
                            **_build_ai_ops_log_fields(
                                ai_decision,
                                ai_score_raw=ai_score,
                                ai_score_after_bonus=ai_score,
                                ai_cooldown_blocked=False,
                            ),
                        )
                        print(
                            "✅ [SCALP 출구엔진 AI] 돌파 모멘텀 유지(WAIT/BUY). 1.5% 유지, +0.3% 보호선 구축."
                        )
                        stock['protect_profit_pct'] = 0.3

                except Exception as e:
                    print(f"⚠️ [SCALP 출구엔진 AI] 분석 실패: {e}. 기존 지정가 유지.")

        protect_pct = stock.get('protect_profit_pct')
        if protect_pct is not None and profit_rate <= protect_pct:
            print(
                f"🛡️ [SCALP 출구엔진] {stock['name']} +0.3% 보호선 이탈. 최유리(IOC) 약익절!"
            )
            _dispatch_scalp_preset_exit(
                sell_reason_type="TRAILING",
                reason=f"🛡️ SCALP 출구엔진 보호선 이탈 ({protect_pct:+.2f}%)",
                exit_rule="scalp_preset_protect_profit",
            )
            return

        return

    is_sell_signal = False
    sell_reason_type = "PROFIT"
    reason = ""
    exit_rule = ""

    now = datetime.now()
    now_t = now.time()

    last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
    current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
    ai_low_score_hits = int(stock.get('ai_low_score_loss_hits', 0) or 0)
    ai_exit_score_limit = int(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MAX_SCORE', 35))
    ai_exit_min_loss_pct = float(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MIN_LOSS_PCT', -0.7))
    ai_exit_min_hold_sec = int(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MIN_HOLD_SEC', 180))
    ai_exit_needed_hits = int(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS', 3))
    open_reclaim_needed_hits = int(
        getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS_OPEN_RECLAIM', ai_exit_needed_hits)
        or ai_exit_needed_hits
    )
    momentum_decay_score_limit = int(getattr(TRADING_RULES, 'SCALP_AI_MOMENTUM_DECAY_SCORE_LIMIT', 45) or 45)
    momentum_decay_min_hold_sec = int(getattr(TRADING_RULES, 'SCALP_AI_MOMENTUM_DECAY_MIN_HOLD_SEC', 90) or 90)
    if pos_tag == 'OPEN_RECLAIM':
        ai_exit_needed_hits = max(ai_exit_needed_hits, open_reclaim_needed_hits)

    last_ai_profit = stock.get('last_ai_profit', profit_rate)
    price_change = abs(profit_rate - last_ai_profit)
    time_elapsed = time.time() - last_ai_time
    held_sec = _resolve_holding_elapsed_sec(stock)
    held_time_min = held_sec / 60.0
    if strategy == "SCALPING":
        _emit_scalp_hard_time_stop_shadow(
            stock=stock,
            code=code,
            held_sec=held_sec,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            current_ai_score=current_ai_score,
            ai_exit_min_loss_pct=ai_exit_min_loss_pct,
        )

    if strategy == 'SCALPING' and ai_engine and radar:
        safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
        is_critical_zone = (profit_rate >= safe_profit_pct) or (profit_rate < 0)

        dynamic_min_cd = 3 if is_critical_zone else getattr(TRADING_RULES, 'AI_HOLDING_MIN_COOLDOWN', 15)
        dynamic_max_cd = (
            getattr(TRADING_RULES, 'AI_HOLDING_CRITICAL_COOLDOWN', 20)
            if is_critical_zone
            else getattr(TRADING_RULES, 'AI_HOLDING_MAX_COOLDOWN', 60)
        )
        dynamic_price_trigger = 0.20 if is_critical_zone else 0.40

        if time_elapsed > dynamic_min_cd and (price_change >= dynamic_price_trigger or time_elapsed > dynamic_max_cd):
            holding_ai_review_started = time.perf_counter()
            try:
                now_ts = time.time()
                market_snapshot = _build_holding_ai_fast_snapshot(ws_data)
                market_signature = tuple(market_snapshot.values())
                reuse_sec = _resolve_holding_ai_fast_reuse_sec(is_critical_zone, dynamic_max_cd)
                max_ws_age_sec = float(getattr(TRADING_RULES, 'AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC', 1.5) or 1.5)
                ws_age_sec = _get_ws_snapshot_age_sec(ws_data)
                fast_sig_matches = market_signature == stock.get('last_ai_market_signature')
                fast_sig_age = _resolve_reference_age_sec(
                    stock.get('last_ai_market_signature_at'),
                    fallback_ts=stock.get('last_ai_reviewed_at'),
                    now_ts=now_ts,
                )
                fast_sig_age_str = "-" if fast_sig_age is None else f"{fast_sig_age:.1f}"
                sig_delta = _describe_snapshot_deltas(stock.get('last_ai_market_snapshot'), market_snapshot)
                near_ai_exit_band = abs(profit_rate - ai_exit_min_loss_pct) <= 0.20
                near_safe_profit_band = abs(profit_rate - safe_profit_pct) <= 0.20
                near_low_score_band = current_ai_score <= (ai_exit_score_limit + 5)
                fast_sig_fresh = fast_sig_age is not None and fast_sig_age < reuse_sec
                price_change_ok = price_change < (dynamic_price_trigger * 1.25)
                ws_fresh = ws_age_sec is None or ws_age_sec <= max_ws_age_sec
                shadow_action = "review"

                if (
                    fast_sig_matches
                    and fast_sig_fresh
                    and price_change_ok
                    and ws_fresh
                    and not near_ai_exit_band
                    and not near_safe_profit_band
                    and not near_low_score_band
                ):
                    shadow_action = "skip"
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_shadow_band",
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        ai_exit_min_loss_pct=f"{ai_exit_min_loss_pct:+.2f}",
                        safe_profit_pct=f"{safe_profit_pct:+.2f}",
                        near_ai_exit=near_ai_exit_band,
                        near_safe_profit=near_safe_profit_band,
                        distance_to_ai_exit=f"{profit_rate - ai_exit_min_loss_pct:+.2f}",
                        distance_to_safe_profit=f"{profit_rate - safe_profit_pct:+.2f}",
                        action=shadow_action,
                    )
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_skip_unchanged",
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        held_sec=int(held_time_min * 60),
                        price_change=f"{price_change:.2f}",
                        reuse_sec=f"{reuse_sec:.1f}",
                        age_sec=fast_sig_age_str,
                        ws_age_sec="-" if ws_age_sec is None else f"{ws_age_sec:.2f}",
                    )
                else:
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_shadow_band",
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        ai_exit_min_loss_pct=f"{ai_exit_min_loss_pct:+.2f}",
                        safe_profit_pct=f"{safe_profit_pct:+.2f}",
                        near_ai_exit=near_ai_exit_band,
                        near_safe_profit=near_safe_profit_band,
                        distance_to_ai_exit=f"{profit_rate - ai_exit_min_loss_pct:+.2f}",
                        distance_to_safe_profit=f"{profit_rate - safe_profit_pct:+.2f}",
                        action=shadow_action,
                    )
                    _log_holding_pipeline(
                        stock,
                        code,
                        "ai_holding_reuse_bypass",
                        profit_rate=f"{profit_rate:+.2f}",
                        ai_score=f"{current_ai_score:.0f}",
                        held_sec=int(held_time_min * 60),
                        price_change=f"{price_change:.2f}",
                        reuse_sec=f"{reuse_sec:.1f}",
                        age_sec=fast_sig_age_str,
                        ws_age_sec="-" if ws_age_sec is None else f"{ws_age_sec:.2f}",
                        sig_delta=sig_delta or "-",
                        reason_codes=_reason_codes(
                            sig_changed=fast_sig_matches,
                            age_expired=fast_sig_fresh,
                            price_move=price_change_ok,
                            ws_stale=ws_fresh,
                            near_ai_exit=not near_ai_exit_band,
                            near_safe_profit=not near_safe_profit_band,
                            near_low_score=not near_low_score_band,
                        ),
                    )
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

                    if ws_data.get('orderbook') and recent_ticks:
                        ai_decision = ai_engine.analyze_target(
                            stock['name'],
                            ws_data,
                            recent_ticks,
                            recent_candles,
                            cache_profile="holding",
                        )
                        raw_ai_score = ai_decision.get('score', 50)
                        ai_cache_hit = bool(ai_decision.get('cache_hit', False))

                        smoothed_score = int((current_ai_score * 0.6) + (raw_ai_score * 0.4))
                        stock['rt_ai_prob'] = smoothed_score / 100.0
                        stock['last_ai_profit'] = profit_rate
                        current_ai_score = smoothed_score

                        if held_time_min * 60 >= ai_exit_min_hold_sec and profit_rate <= ai_exit_min_loss_pct and current_ai_score <= ai_exit_score_limit:
                            ai_low_score_hits += 1
                        else:
                            ai_low_score_hits = 0

                        stock['ai_low_score_loss_hits'] = ai_low_score_hits
                        review_completed_ts = time.time()
                        stock['last_ai_reviewed_at'] = review_completed_ts
                        stock['last_ai_market_signature'] = market_signature
                        stock['last_ai_market_snapshot'] = market_snapshot
                        stock['last_ai_market_signature_at'] = review_completed_ts

                        print(
                            f"👁️ [AI 보유감시: {stock['name']}] 수익: {profit_rate:+.2f}% | "
                            f"AI: {current_ai_score:.0f}점 | 하방카운트: {ai_low_score_hits}/{ai_exit_needed_hits} | "
                            f"갱신주기: {dynamic_max_cd}초 | AI캐시: {'HIT' if ai_cache_hit else 'MISS'}"
                        )
                        _log_holding_pipeline(
                            stock,
                            code,
                            "ai_holding_review",
                            profit_rate=f"{profit_rate:+.2f}",
                            ai_score=f"{current_ai_score:.0f}",
                            low_score_hits=f"{ai_low_score_hits}/{ai_exit_needed_hits}",
                            held_sec=int(held_time_min * 60),
                            price_change=f"{price_change:.2f}",
                            review_cd_sec=dynamic_max_cd,
                            review_ms=int((time.perf_counter() - holding_ai_review_started) * 1000),
                            ai_cache="hit" if ai_cache_hit else "miss",
                            **_build_ai_ops_log_fields(
                                ai_decision,
                                ai_score_raw=raw_ai_score,
                                ai_score_after_bonus=current_ai_score,
                                ai_cooldown_blocked=False,
                            ),
                        )

            except Exception as e:
                log_info(f"🚨 [보유 AI 감시 에러] {stock['name']}({code}): {e}")
            finally:
                LAST_AI_CALL_TIMES[code] = time.time()

    if hard_stop_price > 0 and curr_p <= hard_stop_price:
        is_sell_signal = True
        sell_reason_type = "LOSS"
        reason = f"🛑 보호 하드스탑 이탈 ({hard_stop_price:,.0f}원)"
        exit_rule = "protect_hard_stop"

    elif trailing_stop_price > 0 and curr_p <= trailing_stop_price:
        is_sell_signal = True
        sell_reason_type = "TRAILING"
        reason = f"🔥 보호 트레일링 이탈 ({trailing_stop_price:,.0f}원)"
        exit_rule = "protect_trailing_stop"

    elif strategy == 'SCALPING':
        base_stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -1.5)
        hard_stop_pct = getattr(TRADING_RULES, 'SCALP_HARD_STOP', -2.5)
        safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
        open_reclaim_peak_max_pct = float(getattr(TRADING_RULES, 'SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT', 0.20) or 0.20)
        open_reclaim_hold_sec = int(getattr(TRADING_RULES, 'SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC', 300) or 300)
        open_reclaim_score_buffer = int(getattr(TRADING_RULES, 'SCALP_OPEN_RECLAIM_NEAR_AI_EXIT_SCORE_BUFFER', 5) or 5)
        open_reclaim_retrace_sustain_sec = int(
            getattr(TRADING_RULES, 'SCALP_OPEN_RECLAIM_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC', 120) or 120
        )
        scanner_fallback_peak_max_pct = float(getattr(TRADING_RULES, 'SCALP_SCANNER_FALLBACK_NEVER_GREEN_PEAK_MAX_PCT', 0.20) or 0.20)
        scanner_fallback_hold_sec = int(getattr(TRADING_RULES, 'SCALP_SCANNER_FALLBACK_NEVER_GREEN_HOLD_SEC', 420) or 420)
        scanner_fallback_score_buffer = int(getattr(TRADING_RULES, 'SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SCORE_BUFFER', 8) or 8)
        scanner_fallback_near_ai_exit_sustain_sec = int(
            getattr(TRADING_RULES, 'SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SUSTAIN_SEC', 120) or 120
        )
        scanner_fallback_retrace_sustain_sec = int(
            getattr(TRADING_RULES, 'SCALP_SCANNER_FALLBACK_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC', 150) or 150
        )
        if highest_prices.get(code, 0) > 0:
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
        else:
            drawdown = 0

        soft_stop_pct = max(base_stop_pct, hard_stop_pct)
        hard_stop_pct = min(base_stop_pct, hard_stop_pct)
        if current_ai_score >= 75:
            dynamic_stop_pct = max(soft_stop_pct - 1.0, hard_stop_pct)
            dynamic_trailing_limit = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_STRONG', 0.8)
        else:
            dynamic_stop_pct = soft_stop_pct
            dynamic_trailing_limit = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_WEAK', 0.4)

        now_ts = time.time()
        open_reclaim_near_ai_exit = (
            profit_rate <= ai_exit_min_loss_pct
            and current_ai_score <= (ai_exit_score_limit + open_reclaim_score_buffer)
        )
        scanner_fallback_near_ai_exit = (
            profit_rate <= ai_exit_min_loss_pct
            and current_ai_score <= (ai_exit_score_limit + scanner_fallback_score_buffer)
        )
        default_near_ai_exit = (
            profit_rate <= ai_exit_min_loss_pct
            and current_ai_score <= ai_exit_score_limit
        )
        open_reclaim_near_ai_exit_sustain_sec = _update_boolean_sustain_sec(
            stock,
            key='open_reclaim_near_ai_exit_started_at',
            active=open_reclaim_near_ai_exit,
            now_ts=now_ts,
        )
        scanner_fallback_near_ai_exit_sustain_runtime_sec = _update_boolean_sustain_sec(
            stock,
            key='near_ai_exit_started_at',
            active=scanner_fallback_near_ai_exit,
            now_ts=now_ts,
        )
        _update_boolean_sustain_sec(
            stock,
            key='generic_near_ai_exit_started_at',
            active=default_near_ai_exit,
            now_ts=now_ts,
        )

        if profit_rate <= hard_stop_pct:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 하드스탑 도달 ({hard_stop_pct}%) [AI: {current_ai_score:.0f}]"
            exit_rule = "scalp_hard_stop_pct"

        elif profit_rate <= dynamic_stop_pct:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🔪 소프트 손절 ({dynamic_stop_pct}%) [AI: {current_ai_score:.0f}]"
            exit_rule = "scalp_soft_stop_pct"

        elif profit_rate >= 0 and ai_low_score_hits:
            stock['ai_low_score_loss_hits'] = 0
            ai_low_score_hits = 0

        elif (
            pos_tag == 'OPEN_RECLAIM'
            and held_sec >= open_reclaim_hold_sec
            and peak_profit <= open_reclaim_peak_max_pct
            and profit_rate <= ai_exit_min_loss_pct
            and current_ai_score <= (ai_exit_score_limit + open_reclaim_score_buffer)
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 OPEN_RECLAIM never-green 조기정리 "
                f"(hold={held_sec}s, peak={peak_profit:.2f}%, ai={current_ai_score:.0f})"
            )
            exit_rule = "scalp_open_reclaim_never_green"

        elif (
            pos_tag == 'OPEN_RECLAIM'
            and held_sec >= open_reclaim_hold_sec
            and peak_profit > open_reclaim_peak_max_pct
            and open_reclaim_near_ai_exit_sustain_sec >= open_reclaim_retrace_sustain_sec
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 OPEN_RECLAIM 양전환 후 재약세 정리 "
                f"(hold={held_sec}s, near_ai_exit={open_reclaim_near_ai_exit_sustain_sec}s, peak={peak_profit:.2f}%)"
            )
            exit_rule = "scalp_open_reclaim_retrace_exit"

        elif (
            pos_tag == 'SCANNER'
            and str(stock.get('entry_mode', '')).strip().lower() == 'fallback'
            and held_sec >= scanner_fallback_hold_sec
            and peak_profit <= scanner_fallback_peak_max_pct
            and scanner_fallback_near_ai_exit_sustain_runtime_sec >= scanner_fallback_near_ai_exit_sustain_sec
            and current_ai_score <= (ai_exit_score_limit + scanner_fallback_score_buffer)
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 SCANNER fallback 지연손절 보정 "
                f"(hold={held_sec}s, near_ai_exit={scanner_fallback_near_ai_exit_sustain_runtime_sec}s, peak={peak_profit:.2f}%)"
            )
            exit_rule = "scalp_scanner_fallback_never_green"

        elif (
            pos_tag == 'SCANNER'
            and str(stock.get('entry_mode', '')).strip().lower() == 'fallback'
            and held_sec >= scanner_fallback_hold_sec
            and peak_profit > scanner_fallback_peak_max_pct
            and scanner_fallback_near_ai_exit_sustain_runtime_sec >= scanner_fallback_retrace_sustain_sec
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🧯 SCANNER fallback 양전환 후 재약세 정리 "
                f"(hold={held_sec}s, near_ai_exit={scanner_fallback_near_ai_exit_sustain_runtime_sec}s, peak={peak_profit:.2f}%)"
            )
            exit_rule = "scalp_scanner_fallback_retrace_exit"

        elif (
            held_sec >= ai_exit_min_hold_sec
            and profit_rate <= ai_exit_min_loss_pct
            and current_ai_score <= ai_exit_score_limit
            and ai_low_score_hits >= ai_exit_needed_hits
        ):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🚨 AI 하방 리스크 연속 확인 {ai_low_score_hits}/{ai_exit_needed_hits}회 "
                f"({current_ai_score:.0f}점). 조기 손절 ({profit_rate:.2f}%)"
            )
            exit_rule = "scalp_ai_early_exit"

        elif profit_rate >= safe_profit_pct:
            if current_ai_score < momentum_decay_score_limit and held_sec >= momentum_decay_min_hold_sec:
                is_sell_signal = True
                sell_reason_type = "MOMENTUM_DECAY"
                reason = (
                    f"🤖 AI 틱 가속도 둔화 ({current_ai_score:.0f}점). "
                    f"확인유예({momentum_decay_min_hold_sec}s) 후 익절 (+{profit_rate:.2f}%)"
                )
                exit_rule = "scalp_ai_momentum_decay"

            elif drawdown >= dynamic_trailing_limit:
                is_sell_signal = True
                sell_reason_type = "TRAILING"
                reason = f"🔥 고점 대비 밀림 (-{drawdown:.2f}%). 트레일링 익절 (+{profit_rate:.2f}%)"
                exit_rule = "scalp_trailing_take_profit"

    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= getattr(TRADING_RULES, 'KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
                exit_rule = "kosdaq_timeout"
        except Exception:
            pass

        if not is_sell_signal and peak_profit >= getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0):
            # TODO: KOSDAQ 트레일링 되밀림 폭을 TRAILING_DRAWDOWN_PCT로 통일 검토
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= 1.0:
                is_sell_signal = True
                sell_reason_type = "TRAILING"
                reason = (
                    "🏆 KOSDAQ 트레일링 익절 (+"
                    f"{getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0)}% 돌파 후 하락)"
                )
                exit_rule = "kosdaq_trailing_take_profit"

        elif not is_sell_signal and profit_rate <= getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0)}%)"
            exit_rule = "kosdaq_stop_loss"

    elif strategy == 'KOSPI_ML':
        pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
        if pos_tag == 'BREAKOUT':
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BREAKOUT')
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BOTTOM')
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = (
                getattr(TRADING_RULES, 'STOP_LOSS_BULL')
                if market_regime == 'BULL'
                else getattr(TRADING_RULES, 'STOP_LOSS_BEAR')
            )
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= getattr(TRADING_RULES, 'HOLDING_DAYS'):
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = f"⏳ {getattr(TRADING_RULES, 'HOLDING_DAYS')}일 스윙 보유 만료"
                exit_rule = "kospi_timeout"
        except Exception:
            pass

        # TODO: TRAILING_START_PCT는 스윙 트레일링 시작 수익률로 통일 필요
        # 현재 로직은 해당 임계 도달 시 즉시 익절로 동작
        if not is_sell_signal and profit_rate >= getattr(TRADING_RULES, 'TRAILING_START_PCT'):
            is_sell_signal = True
            sell_reason_type = "PROFIT"
            reason = (
                f"🎯 트레일링 시작 수익률 도달 (+{getattr(TRADING_RULES, 'TRAILING_START_PCT')}%) "
                "(현 로직: 즉시 익절)"
            )
            exit_rule = "kospi_trailing_start_take_profit"

        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"
            exit_rule = "kospi_regime_stop_loss"

    if is_sell_signal:
        stock['last_exit_rule'] = exit_rule or ''
        stock['last_exit_reason'] = reason
        _log_holding_pipeline(
            stock,
            code,
            "exit_signal",
            sell_reason_type=sell_reason_type,
            reason=reason,
            exit_rule=exit_rule or "-",
            profit_rate=f"{profit_rate:+.2f}",
            peak_profit=f"{peak_profit:+.2f}",
            current_ai_score=f"{current_ai_score:.0f}",
            held_sec=int(held_time_min * 60),
            curr_price=curr_p,
            buy_price=buy_p,
            buy_qty=int(stock.get("buy_qty", 0) or 0),
        )
        if _has_open_pending_entry_orders(stock):
            cancel_state = _cancel_pending_entry_orders(stock, code, force=False)
            if cancel_state == 'failed':
                log_error(
                    f"⚠️ [ENTRY_CANCEL] {stock.get('name')}({code}) "
                    "pending entry orders unresolved; delaying sell until next loop"
                )
                return

        sign = "📉 [손절 주문]" if sell_reason_type == 'LOSS' else "🎊 [익절 주문]"
        msg = (
            f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n"
            f"사유: `{reason}`\n"
            f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)"
        )

        is_success = False
        target_id = stock.get('id')

        mem_buy_qty = int(float(stock.get('buy_qty', 0) or 0))
        buy_qty = mem_buy_qty
        try:
            with DB.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                if record and record.buy_qty:
                    buy_qty = max(buy_qty, int(record.buy_qty))
        except Exception as e:
            print(f"🚨 [DB 조회 에러] ID {target_id} 수량 조회 실패: {e}")

        if buy_qty <= 0:
            print(f"⚠️ [{stock['name']}] 고유 ID({target_id})의 수량이 0주입니다. 실제 키움 잔고로 폴백합니다...")
            real_inventory, _ = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
            real_stock = next(
                (item for item in (real_inventory or []) if str(item.get('code', '')).strip()[:6] == code),
                None,
            )

            if real_stock and int(float(real_stock.get('qty', 0) or 0)) > 0:
                buy_qty = int(float(real_stock.get('qty', 0) or 0))
                stock['buy_qty'] = buy_qty
                print(
                    f"🔄 [수량 폴백] 실제 계좌에서 총 잔고 {buy_qty}주를 매도합니다. "
                    "(다중 매매건 합산 수량일 수 있음)"
                )

        if not admin_id:
            print(f"🚨 [매도실패] {stock['name']}: 관리자 ID가 없습니다.")
            return

        if buy_qty <= 0:
            print(f"🚨 [매도실패] {stock['name']}: 실제 잔고도 0주입니다! 강제 완료(COMPLETED) 처리.")
            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "COMPLETED"})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} COMPLETED 전환 실패: {e}")

            stock['status'] = 'COMPLETED'
            highest_prices.pop(code, None)
            return

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "SELL_ORDERED"})
        except Exception as e:
            print(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")

        stock['status'] = 'SELL_ORDERED'
        stock['sell_target_price'] = curr_p

        res = kiwoom_orders.send_smart_sell_order(
            code=code,
            qty=buy_qty,
            token=KIWOOM_TOKEN,
            ws_data=ws_data,
            reason_type=sell_reason_type,
        )

        ord_no = ''

        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                print(f"❌ [매도거절] {stock['name']}: {res.get('return_msg')}")
        elif res:
            is_success = True

        if is_success:
            print(f"✅ [{stock['name']}] 매도 주문 전송 완료. 체결 영수증 처리 대기 중...")
            stock['pending_sell_msg'] = msg
            stock['sell_order_time'] = time.time()
            if ord_no:
                stock['sell_odno'] = ord_no
            _log_holding_pipeline(
                stock,
                code,
                "sell_order_sent",
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                qty=buy_qty,
                ord_no=ord_no or "-",
                order_type=stock.get("exit_order_type") or "-",
                profit_rate=f"{profit_rate:+.2f}",
            )

            if strategy == 'SCALPING' and now_t < TIME_15_30:
                cooldowns[code] = time.time() + 1200
                alerted_stocks.discard(code)
                print(f"♻️ [{stock['name']}] 스캘핑 청산 완료 후 20분 쿨타임 진입.")
        else:
            err_msg = res.get('return_msg', '') if isinstance(res, dict) else ''

            if '매도가능수량' in err_msg:
                print(f"🚨 [{stock['name']}] 잔고 0주(이미 매도됨). COMPLETED로 강제 전환.")
                new_status = 'COMPLETED'
            else:
                print(f"🚨 [{stock['name']}] 일시적 매도 실패! HOLDING으로 원상복구.")
                new_status = 'HOLDING'

            stock['status'] = new_status
            _log_holding_pipeline(
                stock,
                code,
                "sell_order_failed",
                sell_reason_type=sell_reason_type,
                exit_rule=exit_rule or stock.get("last_exit_rule") or "-",
                new_status=new_status,
                error=err_msg or "unknown",
                profit_rate=f"{profit_rate:+.2f}",
            )

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": new_status})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")
                log_info(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")

            if new_status == 'COMPLETED':
                highest_prices.pop(code, None)
        return

    # --------------------------------------------------------
    # [추가매수 레이어] SELL 신호가 없을 때만 진입
    # --------------------------------------------------------
    gate = can_consider_scale_in(
        stock=stock,
        code=code,
        ws_data=ws_data,
        strategy=strategy,
        market_regime=market_regime,
    )
    if gate.get('allowed'):
        scale_in_action = _evaluate_scale_in_signal(
            stock=stock,
            code=code,
            strategy=strategy,
            market_regime=market_regime,
            profit_rate=profit_rate,
            peak_profit=peak_profit,
            curr_price=curr_p,
            ws_data=ws_data,
        )
        if scale_in_action:
            log_info(
                "[ADD_SIGNAL] "
                f"{stock.get('name')}({code}) "
                f"strategy={strategy} type={scale_in_action.get('add_type')} "
                f"reason={scale_in_action.get('reason')} "
                f"profit={profit_rate:+.2f}% peak={peak_profit:+.2f}%"
            )
            _process_scale_in_action(
                stock=stock,
                code=code,
                ws_data=ws_data,
                action=scale_in_action,
                admin_id=admin_id,
            )
            return
    else:
        last_block = float(stock.get('last_add_block_log_ts', 0) or 0)
        if time.time() - last_block >= 30:
            if gate.get('reason') == 'buy_side_paused':
                log_info(
                    f"[TRADING_PAUSED_BLOCK] HOLDING add skipped "
                    f"{stock.get('name')}({code}) strategy={strategy} "
                    f"state={get_pause_state_label()}"
                )
            else:
                log_info(
                    "[ADD_BLOCKED] "
                    f"{stock.get('name')}({code}) "
                    f"strategy={strategy} reason={gate.get('reason')}"
                )
            stock['last_add_block_log_ts'] = time.time()


def can_consider_scale_in(stock, code, ws_data, strategy, market_regime):
    """추가매수 공통 게이트: 조건을 만족하는 경우에만 True."""
    _ = (code, ws_data)

    if getattr(TRADING_RULES, 'SCALE_IN_REQUIRE_HISTORY_TABLE', False):
        return {"allowed": False, "reason": "history_table_required"}

    if stock.get('pending_add_order') and not stock.get('pending_add_ord_no'):
        _cancel_or_reconcile_pending_add(stock, reason="stale_pending_no_ordno")
        return {"allowed": False, "reason": "pending_add_recovered"}

    # 장시간 미체결된 추가매수 주문은 보수적으로 해제
    pending_ts = float(stock.get('pending_add_requested_at', 0) or 0)
    if pending_ts:
        raw_strategy = (strategy or "").upper()
        base_timeout = 20 if raw_strategy == 'SCALPING' else int(getattr(TRADING_RULES, 'ORDER_TIMEOUT_SEC', 30) or 30)
        add_type = (stock.get('pending_add_type') or '').upper()
        if raw_strategy != 'SCALPING' and add_type == 'PYRAMID':
            base_timeout = int(base_timeout * 2)
        timeout_sec = base_timeout
        pending_filled = int(stock.get('pending_add_filled_qty', 0) or 0)
        if pending_filled > 0:
            timeout_sec = timeout_sec * 3
        if (time.time() - pending_ts) > timeout_sec:
            reconcile = _cancel_or_reconcile_pending_add(stock, reason="timeout")
            if reconcile.get('cleared'):
                return {"allowed": False, "reason": "pending_add_timeout_released"}
            return {"allowed": False, "reason": "pending_add_cancel_failed"}

    if stock.get('status') != 'HOLDING':
        return {"allowed": False, "reason": "not_holding"}

    if not getattr(TRADING_RULES, 'ENABLE_SCALE_IN', False):
        return {"allowed": False, "reason": "scale_in_disabled"}

    if is_buy_side_paused():
        return {"allowed": False, "reason": "buy_side_paused"}

    if stock.get('scale_in_locked'):
        return {"allowed": False, "reason": "scale_in_locked"}

    buy_p = float(stock.get('buy_price', 0) or 0)
    buy_q = int(float(stock.get('buy_qty', 0) or 0))
    if buy_p <= 0 or buy_q <= 0:
        return {"allowed": False, "reason": "invalid_position"}

    if stock.get('status') == 'SELL_ORDERED':
        return {"allowed": False, "reason": "sell_ordered"}

    # 동일 루프/짧은 시간 중복 호출 방지
    lock_sec = int(getattr(TRADING_RULES, 'ADD_JUDGMENT_LOCK_SEC', 20) or 20)
    last_check = float(stock.get('last_scale_in_check_ts', 0) or 0)
    if last_check > 0 and (time.time() - last_check) < lock_sec:
        return {"allowed": False, "reason": "add_judgment_locked"}

    # 최근 추가매수 직후 쿨다운
    cooldown_sec = int(getattr(TRADING_RULES, 'SCALE_IN_COOLDOWN_SEC', 180) or 180)
    last_add = float(stock.get('last_add_time', 0) or 0)
    if not last_add and stock.get('last_add_at'):
        try:
            last_add = stock['last_add_at'].timestamp()
        except Exception:
            pass
    if last_add > 0 and (time.time() - last_add) < cooldown_sec:
        return {"allowed": False, "reason": "scale_in_cooldown"}

    # 매수 주문이 이미 진행 중인 경우
    if (
        stock.get('pending_add_order')
        or stock.get('pending_add_ord_no')
        or stock.get('pending_add_requested_at')
        or stock.get('add_order_time')
        or stock.get('pending_add_msg')
        or stock.get('add_odno')
    ):
        return {"allowed": False, "reason": "pending_add_order"}

    # 계좌 리스크 게이트(옵션): 예수금 정보가 있을 때만 적용
    curr_price = int(float(ws_data.get('curr', 0) or 0))
    deposit_hint = float(stock.get('account_deposit', 0) or stock.get('deposit', 0) or 0)
    if curr_price > 0 and deposit_hint > 0:
        max_pos_pct = float(getattr(TRADING_RULES, 'MAX_POSITION_PCT', 0.30) or 0.30)
        if (buy_q * curr_price) >= (deposit_hint * max_pos_pct * 0.98):
            return {"allowed": False, "reason": "position_at_cap"}

    # 전략별 허용 여부
    raw_strategy = (strategy or "").upper()
    if raw_strategy == 'SCALPING':
        allow_avg = bool(getattr(TRADING_RULES, 'SCALPING_ENABLE_AVG_DOWN', False))
        allow_pyr = int(getattr(TRADING_RULES, 'SCALPING_MAX_PYRAMID_COUNT', 0) or 0) > 0
        if not (allow_avg or allow_pyr):
            return {"allowed": False, "reason": "scalping_scale_in_disabled"}
    elif raw_strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        allow_avg = bool(getattr(TRADING_RULES, 'SWING_ENABLE_AVG_DOWN', False))
        allow_pyr = int(getattr(TRADING_RULES, 'SWING_MAX_PYRAMID_COUNT', 0) or 0) > 0
        if not (allow_avg or allow_pyr):
            return {"allowed": False, "reason": "swing_scale_in_disabled"}

        if (
            allow_avg
            and not allow_pyr
            and market_regime == 'BEAR'
            and getattr(TRADING_RULES, 'BLOCK_SWING_AVG_DOWN_IN_BEAR', True)
        ):
            return {"allowed": False, "reason": "bear_avg_down_blocked"}
    else:
        return {"allowed": False, "reason": "unknown_strategy"}

    # 장 마감 근접 시 추가매수 금지
    now = datetime.now()
    try:
        close_str = getattr(TRADING_RULES, 'MARKET_CLOSE_TIME', "15:30:00")
        close_t = datetime.strptime(close_str, "%H:%M:%S").time()
        close_dt = datetime.combine(now.date(), close_t) - timedelta(minutes=5)
        if now >= close_dt:
            return {"allowed": False, "reason": "near_market_close"}
    except Exception:
        pass

    if raw_strategy == 'SCALPING':
        try:
            cutoff_str = getattr(TRADING_RULES, 'SCALPING_NEW_BUY_CUTOFF', "15:00:00")
            cutoff_t = datetime.strptime(cutoff_str, "%H:%M:%S").time()
            if now.time() >= cutoff_t:
                return {"allowed": False, "reason": "scalping_cutoff"}
        except Exception:
            pass

    stock['last_scale_in_check_ts'] = time.time()
    return {"allowed": True, "reason": "ok"}


def _clear_pending_add_meta(stock, reason=None):
    for key in [
        'pending_add_order',
        'pending_add_type',
        'pending_add_qty',
        'pending_add_ord_no',
        'pending_add_requested_at',
        'pending_add_counted',
        'pending_add_filled_qty',
        'add_order_time',
        'add_odno',
    ]:
        stock.pop(key, None)
    if reason:
        log_info(f"[ADD_CANCELLED] pending add cleared ({reason}) for {stock.get('name')}")


def _persist_scale_in_flags(stock):
    target_id = stock.get('id')
    if not DB or not target_id:
        return
    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update({
                "scale_in_locked": bool(stock.get('scale_in_locked', False)),
            })
    except Exception as e:
        log_error(f"[ADD_BLOCKED] scale_in flag persist failed for id={target_id}: {e}")


def _is_ok_response(res):
    if not isinstance(res, dict):
        return bool(res)
    return str(res.get('return_code', res.get('rt_cd', ''))) == '0'


def _cancel_or_reconcile_pending_add(stock, reason):
    """
    보수적으로 pending add를 정리합니다.
    - 주문번호가 있으면 실제 취소를 먼저 시도
    - 주문이 이미 없거나 체결/취소 완료로 보이면 잠금 후 정리
    - 취소 실패 시 pending을 유지해 중복 add를 막음
    """
    ord_no = str(stock.get('pending_add_ord_no', '') or '').strip()
    code = str(stock.get('code', '')).strip()[:6]

    if not ord_no:
        stock['scale_in_locked'] = True
        _persist_scale_in_flags(stock)
        record_add_history_event(
            DB,
            recommendation_id=stock.get('id'),
            stock_code=code,
            stock_name=stock.get('name'),
            strategy=stock.get('strategy'),
            add_type=stock.get('pending_add_type'),
            event_type='CANCELLED',
            order_no=None,
            request_qty=stock.get('pending_add_qty', 0),
            prev_buy_price=stock.get('buy_price'),
            prev_buy_qty=stock.get('buy_qty', 0),
            add_count_after=stock.get('add_count', 0),
            reason=f"{reason}_missing_ordno",
            note='pending add missing order number; scale_in_locked applied',
        )
        _clear_pending_add_meta(stock, reason=f"{reason}_missing_ordno")
        log_error(
            f"[ADD_CANCELLED] {stock.get('name')}({code}) pending add missing order number. "
            "scale_in_locked=True for manual reconciliation."
        )
        return {"cleared": True, "reason": f"{reason}_missing_ordno"}

    if not code or not KIWOOM_TOKEN:
        stock['scale_in_locked'] = True
        _persist_scale_in_flags(stock)
        log_error(
            f"[ADD_BLOCKED] {stock.get('name')}({code}) cannot reconcile pending add "
            f"(token/code missing). keeping pending blocked."
        )
        return {"cleared": False, "reason": "missing_runtime_context"}

    res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=ord_no, token=KIWOOM_TOKEN, qty=0)
    if _is_ok_response(res):
        record_add_history_event(
            DB,
            recommendation_id=stock.get('id'),
            stock_code=code,
            stock_name=stock.get('name'),
            strategy=stock.get('strategy'),
            add_type=stock.get('pending_add_type'),
            event_type='CANCELLED',
            order_no=ord_no,
            request_qty=stock.get('pending_add_qty', 0),
            prev_buy_price=stock.get('buy_price'),
            prev_buy_qty=stock.get('buy_qty', 0),
            add_count_after=stock.get('add_count', 0),
            reason=reason,
            note='pending add order cancelled before release',
        )
        _clear_pending_add_meta(stock, reason=reason)
        return {"cleared": True, "reason": f"{reason}_cancelled"}

    err_msg = str(res.get('return_msg', '')) if isinstance(res, dict) else str(res)
    uncertain_keywords = ['주문없음', '취소가능수량', '체결', '원주문']
    if any(keyword in err_msg for keyword in uncertain_keywords):
        stock['scale_in_locked'] = True
        _persist_scale_in_flags(stock)
        record_add_history_event(
            DB,
            recommendation_id=stock.get('id'),
            stock_code=code,
            stock_name=stock.get('name'),
            strategy=stock.get('strategy'),
            add_type=stock.get('pending_add_type'),
            event_type='CANCELLED',
            order_no=ord_no,
            request_qty=stock.get('pending_add_qty', 0),
            prev_buy_price=stock.get('buy_price'),
            prev_buy_qty=stock.get('buy_qty', 0),
            add_count_after=stock.get('add_count', 0),
            reason=f"{reason}_uncertain",
            note=f'cancel uncertain: {err_msg}',
        )
        _clear_pending_add_meta(stock, reason=f"{reason}_uncertain")
        log_error(
            f"[ADD_CANCELLED] {stock.get('name')}({code}) pending add uncertain after cancel attempt. "
            "scale_in_locked=True for manual/account reconciliation."
        )
        return {"cleared": True, "reason": f"{reason}_uncertain"}

    log_error(
        f"[ADD_BLOCKED] {stock.get('name')}({code}) pending add cancel failed; keeping pending. "
        f"reason={reason} err={err_msg}"
    )
    return {"cleared": False, "reason": "cancel_failed"}


def _sanitize_pending_add_states(active_targets):
    """재시작/복구 시 보수적으로 pending add 메타를 정리합니다."""
    if not active_targets:
        return
    for stock in active_targets:
        if not isinstance(stock, dict):
            continue
        if stock.get('pending_add_order'):
            # 주문번호가 없으면 복구 불가 → 정리
            if not stock.get('pending_add_ord_no'):
                stock['scale_in_locked'] = True
                _persist_scale_in_flags(stock)
                _clear_pending_add_meta(stock, reason="recovery_no_ordno")
                continue
            # 오래된 pending은 정리
            pending_ts = float(stock.get('pending_add_requested_at', 0) or 0)
            if pending_ts:
                raw_strategy = (stock.get('strategy') or '').upper()
                timeout_sec = 20 if raw_strategy == 'SCALPING' else int(getattr(TRADING_RULES, 'ORDER_TIMEOUT_SEC', 30) or 30)
                if (time.time() - pending_ts) > timeout_sec:
                    _cancel_or_reconcile_pending_add(stock, reason="recovery_timeout")


def _evaluate_scale_in_signal(
    stock,
    code,
    strategy,
    market_regime,
    profit_rate,
    peak_profit,
    curr_price,
    ws_data,
):
    """전략별 추가매수 시그널 평가 (퍼센트 기반 1차 버전)."""
    _ = (ws_data,)

    raw_strategy = (strategy or "").upper()
    if raw_strategy == 'SCALPING':
        is_new_high = False
        try:
            highest_prices = HIGHEST_PRICES or {}
            is_new_high = curr_price >= float(highest_prices.get(code, curr_price))
        except Exception:
            pass

        avg_down = evaluate_scalping_avg_down(stock, profit_rate)
        pyramid = evaluate_scalping_pyramid(stock, profit_rate, peak_profit, is_new_high)
    elif raw_strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        avg_down = evaluate_swing_avg_down(stock, profit_rate, market_regime)
        pyramid = evaluate_swing_pyramid(stock, profit_rate, peak_profit)
    else:
        return None

    if avg_down.get("should_add") and pyramid.get("should_add"):
        return pyramid if profit_rate >= 0 else avg_down
    if pyramid.get("should_add"):
        return pyramid
    if avg_down.get("should_add"):
        return avg_down
    return None


def _process_scale_in_action(stock, code, ws_data, action, admin_id):
    """추가매수 주문 처리 (STEP4 이후 구현 예정)."""
    if not action:
        return None
    return execute_scale_in_order(
        stock=stock,
        code=code,
        ws_data=ws_data,
        action=action,
        admin_id=admin_id,
    )


def execute_scale_in_order(*, stock, code, ws_data, action, admin_id):
    """
    HOLDING 상태 추가매수 주문 실행.
    - 성공 시 HOLDING 유지 + pending add 메타 저장
    - 실패 시 pending 메타 저장하지 않음
    """
    if not admin_id:
        print(f"⚠️ [추가매수보류] {stock.get('name')}: 관리자 ID가 없습니다.")
        log_info(f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=no_admin")
        return None

    add_type = (action.get("add_type") or "").upper()
    if add_type not in ("AVG_DOWN", "PYRAMID"):
        log_info(f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=invalid_add_type")
        return None

    curr_price = int(float(ws_data.get('curr', 0) or 0))
    if curr_price <= 0:
        log_info(f"[ADD_BLOCKED] {stock.get('name')}({code}) reason=invalid_price")
        return None

    deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
    qty = calc_scale_in_qty(
        stock=stock,
        curr_price=curr_price,
        deposit=deposit,
        add_type=add_type,
        strategy=stock.get('strategy', ''),
    )
    if qty <= 0:
        log_info(
            f"[ADD_BLOCKED] {stock.get('name')}({code}) "
            f"reason=zero_qty deposit={deposit} curr_price={curr_price} "
            f"buy_qty={stock.get('buy_qty', 0)} add_type={add_type}"
        )
        print(
            f"⚠️ [추가매수보류] {stock.get('name')}: 추가매수 수량 0주 "
            f"(주문가능금액 {deposit:,}원, 현재가 {curr_price:,}원)"
        )
        return None

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    if strategy == 'SCALPING':
        order_type_code = "00"
        final_price = curr_price
    else:
        order_type_code = "6"
        final_price = 0

    if is_buy_side_paused():
        log_info(
            f"[TRADING_PAUSED_BLOCK] add order blocked "
            f"{stock.get('name')}({code}) strategy={strategy} type={add_type} "
            f"state={get_pause_state_label()}"
        )
        return None

    res = kiwoom_orders.send_buy_order(
        code,
        qty,
        final_price,
        order_type_code,
        token=KIWOOM_TOKEN,
        order_type_desc=f"추가매수({add_type})",
    )

    if res is None:
        print(f"❌ [{stock.get('name')}] 추가매수 주문 전송 실패 (None 반환)")
        log_info(f"[ADD_ORDER_SENT] {stock.get('name')}({code}) failed=None_response")
        return None

    if isinstance(res, dict):
        rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
        if rt_cd == '0':
            ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            stock['pending_add_order'] = True
            stock['pending_add_type'] = add_type
            stock['pending_add_qty'] = qty
            stock['pending_add_ord_no'] = ord_no
            stock['pending_add_requested_at'] = time.time()
            stock['add_order_time'] = time.time()
            if ord_no:
                stock['add_odno'] = ord_no

            print(
                f"✅ [{stock.get('name')}] 추가매수 주문 전송 완료. "
                f"type={add_type}, qty={qty}, ord_no={ord_no}"
            )
            log_info(
                "[ADD_ORDER_SENT] "
                f"{stock.get('name')}({code}) "
                f"type={add_type} qty={qty} ord_no={ord_no}"
            )
            record_add_history_event(
                DB,
                recommendation_id=stock.get('id'),
                stock_code=code,
                stock_name=stock.get('name'),
                strategy=stock.get('strategy'),
                add_type=add_type,
                event_type='ORDER_SENT',
                order_no=ord_no,
                request_qty=qty,
                request_price=curr_price if strategy == 'SCALPING' else None,
                prev_buy_price=stock.get('buy_price'),
                prev_buy_qty=stock.get('buy_qty', 0),
                add_count_after=stock.get('add_count', 0),
                reason=action.get('reason'),
            )
            return res

        print(f"❌ [{stock.get('name')}] 추가매수 주문 거절: {res.get('return_msg')}")
        log_info(
            "[ADD_ORDER_SENT] "
            f"{stock.get('name')}({code}) failed=reject msg={res.get('return_msg')}"
        )
        return None

    print(f"❌ [{stock.get('name')}] 추가매수 주문 전송 실패 (응답 파싱 실패)")
    log_info(f"[ADD_ORDER_SENT] {stock.get('name')}({code}) failed=parse_error")
    return None


def handle_buy_ordered_state(stock, code):
    """
    주문 전송 후(BUY_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 로직을 호출합니다.
    """
    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    highest_prices = HIGHEST_PRICES

    target_id = stock.get('id')
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy

    if stock.get('target_buy_price', 0) > 0:
        timeout_sec = getattr(TRADING_RULES, 'RESERVE_TIMEOUT_SEC', 1200)
    else:
        timeout_sec = 20 if strategy == 'SCALPING' else getattr(TRADING_RULES, 'ORDER_TIMEOUT_SEC', 30)

    if _has_open_pending_entry_orders(stock) and time_elapsed > timeout_sec:
        _reconcile_pending_entry_orders(stock, code, strategy)
        return

    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 매수 대기 {timeout_sec}초 초과. 취소 절차 진입.")
        orig_ord_no = stock.get('odno')

        if not orig_ord_no:
            stock['status'] = 'WATCHING'
            stock.pop('order_time', None)
            stock.pop('odno', None)
            stock.pop('pending_buy_msg', None)
            stock.pop('target_buy_price', None)
            stock.pop('order_price', None)
            stock.pop('buy_qty', None)
            _clear_pending_entry_meta(stock)
            highest_prices.pop(code, None)
            alerted_stocks.discard(code)

            if strategy == 'SCALPING':
                cooldowns[code] = time.time() + 1200

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({
                        "status": "WATCHING",
                        "buy_price": 0,
                        "buy_qty": 0,
                    })
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 매수 타임아웃 복구 실패: {e}")
            return

        process_order_cancellation(stock, code, orig_ord_no, DB, strategy)


def handle_sell_ordered_state(stock, code):
    """
    주문 전송 후(SELL_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 후 HOLDING으로 롤백합니다.
    """
    sell_order_time = stock.get('sell_order_time', 0)

    if sell_order_time == 0:
        stock['sell_order_time'] = time.time()
        return

    time_elapsed = time.time() - sell_order_time
    target_id = stock.get('id')
    timeout_sec = getattr(TRADING_RULES, 'SELL_TIMEOUT_SEC', 40)

    if time_elapsed > timeout_sec:
        print(
            f"⚠️ [{stock['name']}] 매도 대기 {timeout_sec}초 초과. 호가 꼬임/VI 의심 ➡️ "
            "취소 후 HOLDING 롤백 절차 진입."
        )
        orig_ord_no = stock.get('sell_odno')

        if not orig_ord_no:
            print(f"🚨 [{stock['name']}] 취소할 원주문번호(odno)가 없습니다. 상태만 HOLDING으로 강제 롤백합니다.")
            stock['status'] = 'HOLDING'
            stock.pop('sell_order_time', None)
            stock.pop('sell_odno', None)
            stock.pop('pending_sell_msg', None)
            stock.pop('sell_target_price', None)

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 매도 타임아웃 복구 실패: {e}")
            return

        process_sell_cancellation(stock, code, orig_ord_no, DB)


def process_sell_cancellation(stock, code, orig_ord_no, db):
    """미체결 매도 주문을 전량 취소하고 상태를 다시 HOLDING으로 되돌립니다."""
    target_id = stock.get('id')

    res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0)

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    if is_success:
        print(f"✅ [{stock['name']}] 미체결 매도 주문 취소 성공! HOLDING(보유) 상태로 복귀합니다.")
        stock['status'] = 'HOLDING'
        stock.pop('sell_odno', None)
        stock.pop('sell_order_time', None)
        stock.pop('pending_sell_msg', None)
        stock.pop('sell_target_price', None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매도 취소 후 HOLDING 복구 실패: {e}")
        return True

    print(f"🚨 [{stock['name']}] 매도 취소 실패! (사유: {err_msg})")
    if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음', '체결']):
        print(f"💡 [{stock['name']}] 간발의 차이로 이미 매도 체결된 것으로 판단합니다. COMPLETED로 전환.")
        stock['status'] = 'COMPLETED'
        HIGHEST_PRICES.pop(code, None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "COMPLETED"})
        except Exception:
            pass
    return False


def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    """
    미체결 주문의 실제 취소 처리와 DB/메모리 청소를 담당합니다.
    고유 PK(id)를 사용하여 다중 매매 환경에서도 정확한 레코드를 타겟팅합니다.
    """
    cooldowns = COOLDOWNS
    alerted_stocks = ALERTED_STOCKS
    highest_prices = HIGHEST_PRICES

    target_id = stock.get('id')

    if _has_open_pending_entry_orders(stock):
        result = _cancel_pending_entry_orders(stock, code, force=True)
        if result != 'failed':
            stock['status'] = 'WATCHING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            stock.pop('pending_buy_msg', None)
            stock.pop('target_buy_price', None)
            stock.pop('order_price', None)
            stock.pop('buy_qty', None)
            _clear_entry_arm(stock)
            highest_prices.pop(code, None)

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({
                        "status": "WATCHING",
                        "buy_price": 0,
                        "buy_qty": 0,
                    })
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 후 WATCHING 복구 실패: {e}")

            if strategy in ['SCALPING', 'SCALP']:
                alerted_stocks.discard(code)
                cooldowns[code] = time.time() + 1200
            return True

    res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0)

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    if is_success:
        print(f"✅ [{stock['name']}] 미체결 매수 취소 성공. 감시 상태로 복귀합니다.")
        stock['status'] = 'WATCHING'
        stock.pop('odno', None)
        stock.pop('order_time', None)
        stock.pop('pending_buy_msg', None)
        stock.pop('target_buy_price', None)
        stock.pop('order_price', None)
        stock.pop('buy_qty', None)
        _clear_pending_entry_meta(stock)
        highest_prices.pop(code, None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({
                    "status": "WATCHING",
                    "buy_price": 0,
                    "buy_qty": 0,
                })
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 후 WATCHING 복구 실패: {e}")

        if strategy in ['SCALPING', 'SCALP']:
            alerted_stocks.discard(code)
            cooldowns[code] = time.time() + 1200
            print(f"♻️ [{stock['name']}] 스캘핑 취소 완료. 20분 쿨타임 진입.")
        return True

    print(f"🚨 [{stock['name']}] 매수 취소 실패! (사유: {err_msg})")
    if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음']):
        print(f"💡 [{stock['name']}] 이미 전량 체결된 것으로 판단. HOLDING으로 전환.")
        stock['status'] = 'HOLDING'

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 실패 후 HOLDING 전환 실패: {e}")

    return False
