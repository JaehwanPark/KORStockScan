"""Scalping overnight gatekeeper helpers."""

import time
from datetime import datetime

from src.database.models import RecommendationHistory
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info


KIWOOM_TOKEN = None
DB = None
WS_MANAGER = None
event_bus = None
ACTIVE_TARGETS = None
escape_markdown = None
_confirm_cancel_or_reload_remaining = None
_send_market_exit_now = None
_is_ok_response = None
_extract_ord_no = None
process_sell_cancellation = None


def bind_overnight_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    ws_manager=None,
    event_bus_instance=None,
    active_targets=None,
    escape_markdown_fn=None,
    confirm_cancel_or_reload_remaining=None,
    send_market_exit_now=None,
    is_ok_response=None,
    extract_ord_no=None,
    process_sell_cancellation_fn=None,
):
    global KIWOOM_TOKEN, DB, WS_MANAGER, event_bus, ACTIVE_TARGETS, escape_markdown
    global _confirm_cancel_or_reload_remaining, _send_market_exit_now, _is_ok_response
    global _extract_ord_no, process_sell_cancellation

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if ws_manager is not None:
        WS_MANAGER = ws_manager
    if event_bus_instance is not None:
        event_bus = event_bus_instance
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if escape_markdown_fn is not None:
        escape_markdown = escape_markdown_fn
    if confirm_cancel_or_reload_remaining is not None:
        _confirm_cancel_or_reload_remaining = confirm_cancel_or_reload_remaining
    if send_market_exit_now is not None:
        _send_market_exit_now = send_market_exit_now
    if is_ok_response is not None:
        _is_ok_response = is_ok_response
    if extract_ord_no is not None:
        _extract_ord_no = extract_ord_no
    if process_sell_cancellation_fn is not None:
        process_sell_cancellation = process_sell_cancellation_fn

def _find_active_target_by_code(code):
    code = str(code).strip()[:6]
    for item in ACTIVE_TARGETS:
        if str(item.get('code', '')).strip()[:6] == code:
            return item
    return None


def _calc_held_minutes(stock=None, db_record=None):
    buy_time = None
    if stock and stock.get('buy_time'):
        buy_time = stock.get('buy_time')
    elif db_record is not None:
        buy_time = getattr(db_record, 'buy_time', None)

    if not buy_time:
        return 0.0

    try:
        if isinstance(buy_time, datetime):
            buy_dt = buy_time
        else:
            buy_str = str(buy_time)
            try:
                buy_dt = datetime.fromisoformat(buy_str)
            except Exception:
                buy_dt = datetime.combine(datetime.now().date(), datetime.strptime(buy_str, '%H:%M:%S').time())
        return max(0.0, (datetime.now() - buy_dt).total_seconds() / 60.0)
    except Exception:
        return 0.0


def _build_scalping_overnight_ctx(record, mem_stock=None, ws_data=None):
    ctx = kiwoom_utils.build_realtime_analysis_context(
        KIWOOM_TOKEN,
        record.stock_code,
        position_status=record.status,
        ws_data=ws_data,
        market_cap=(mem_stock or {}).get('marcap', 0),
    )

    avg_price = int(float(getattr(record, 'buy_price', 0) or (mem_stock.get('buy_price', 0) if mem_stock else 0) or 0))
    curr_price = int(float(ctx.get('curr_price', 0) or 0))
    pnl_pct = ((curr_price - avg_price) / avg_price * 100.0) if avg_price > 0 and curr_price > 0 else 0.0

    ctx['stock_name'] = getattr(record, 'stock_name', '') or (mem_stock.get('name') if mem_stock else '')
    ctx['stock_code'] = record.stock_code
    ctx['position_status'] = record.status
    ctx['avg_price'] = avg_price
    ctx['pnl_pct'] = pnl_pct
    ctx['held_minutes'] = _calc_held_minutes(mem_stock, record)
    ctx['strat_label'] = 'SCALPING_EOD_REVIEW'
    if mem_stock and mem_stock.get('rt_ai_prob') is not None:
        try:
            ctx['score'] = float(mem_stock.get('rt_ai_prob', 0.5) or 0.5) * 100.0
        except Exception:
            pass
    ctx['order_status_note'] = (
        f"db_status={record.status}, buy_qty={int(float(getattr(record, 'buy_qty', 0) or 0))}, "
        f"sell_ord_no={(mem_stock or {}).get('sell_odno', '') if mem_stock else ''}"
    )
    return ctx


def _publish_scalping_overnight_decision(stock_name, code, decision, action_taken):
    confidence = int(decision.get('confidence', 0) or 0)
    reason = decision.get('reason', '')
    risk_note = decision.get('risk_note', '')
    chosen = decision.get('action', 'SELL_TODAY')
    esc_stock_name = escape_markdown(stock_name)
    esc_code = escape_markdown(code)
    esc_chosen = escape_markdown(chosen)
    esc_action_taken = escape_markdown(action_taken)
    esc_reason = escape_markdown(reason)
    esc_risk_note = escape_markdown(risk_note)
    msg = (
        f"🌙 **[15:15 SCALPING EOD 판정]**\n"
        f"종목: **{esc_stock_name} ({esc_code})**\n"
        f"AI 결정: `{esc_chosen}` ({confidence}점)\n"
        f"실행: `{esc_action_taken}`\n"
        f"사유: {esc_reason}\n"
        f"리스크: {esc_risk_note}"
    )
    event_bus.publish(
        'TELEGRAM_BROADCAST',
        {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
    )


def _execute_scalping_sell_today(record, mem_stock=None):
    code = str(record.stock_code).strip()[:6]
    stock_name = getattr(record, 'stock_name', code)
    expected_qty = int(float(getattr(record, 'buy_qty', 0) or (mem_stock.get('buy_qty', 0) if mem_stock else 0) or 0))
    orig_ord_no = ''
    if mem_stock:
        orig_ord_no = mem_stock.get('sell_odno', '') or mem_stock.get('sell_ord_no', '') or ''

    rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
    if rem_qty <= 0:
        print(f"⚠️ [15:15 EOD] {stock_name}({code}) 청산 대상이지만 잔량 확인 실패/0주. 시장가 청산 생략")
        return False, '잔량 없음 또는 확인 실패'

    res = _send_market_exit_now(code, rem_qty, KIWOOM_TOKEN)
    if not _is_ok_response(res):
        return False, f"시장가 매도 실패: {res}"

    ord_no = _extract_ord_no(res)
    if mem_stock is not None:
        mem_stock['status'] = 'SELL_ORDERED'
        mem_stock['sell_order_time'] = time.time()
        mem_stock['sell_target_price'] = int((WS_MANAGER.get_latest_data(code) or {}).get('curr', 0) or 0)
        if ord_no:
            mem_stock['sell_odno'] = ord_no

    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=record.id).update({"status": "SELL_ORDERED"})
    except Exception as e:
        log_error(f"🚨 [15:15 EOD] DB SELL_ORDERED 업데이트 실패 ({code}): {e}")

    return True, f"시장가 청산 주문 전송 ({rem_qty}주)"


def _execute_scalping_hold_overnight(record, mem_stock=None):
    code = str(record.stock_code).strip()[:6]
    if record.status != 'SELL_ORDERED':
        return True, '기존 HOLDING 유지'

    if not mem_stock:
        return False, '메모리 대상 없음으로 기존 SELL_ORDERED 취소 불가'

    orig_ord_no = mem_stock.get('sell_odno', '') or mem_stock.get('sell_ord_no', '') or ''
    if not orig_ord_no:
        return False, '취소할 원주문번호 없음'

    cancelled = process_sell_cancellation(mem_stock, code, orig_ord_no, DB)
    if cancelled:
        mem_stock['status'] = 'HOLDING'
        return True, '미체결 매도 취소 후 HOLDING 복귀'
    return False, '미체결 매도 취소 실패'


def run_scalping_overnight_gatekeeper(ai_engine=None):
    """15:15 스캘핑 포지션 오버나이트/당일청산 판정 및 실행."""
    global KIWOOM_TOKEN, DB, WS_MANAGER, event_bus, ACTIVE_TARGETS

    if ai_engine is None:
        log_info("⚠️ [15:15 EOD] AI 엔진이 없어 오버나이트 판정을 건너뜁니다.")
        return False
    if DB is None or ACTIVE_TARGETS is None:
        log_info("⚠️ [15:15 EOD] DB/ACTIVE_TARGETS 의존성 미설정")
        return False

    try:
        with DB.get_session() as session:
            records = (
                session.query(RecommendationHistory)
                .filter(RecommendationHistory.status.in_(('HOLDING', 'SELL_ORDERED')))
                .filter(RecommendationHistory.strategy.in_(('SCALPING', 'SCALP')))
                .all()
            )
    except Exception as e:
        log_error(f"🚨 [15:15 EOD] DB 조회 실패: {e}")
        return False

    if not records:
        print("✅ [15:15 EOD] 스캘핑 보유/주문 대기 종목이 없습니다.")
        return True

    summary_rows = []
    sell_count = 0
    hold_count = 0

    for record in records:
        code = str(record.stock_code).strip()[:6]
        name = getattr(record, 'stock_name', code)
        mem_stock = _find_active_target_by_code(code)
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}

        ctx = _build_scalping_overnight_ctx(record, mem_stock, ws_data)
        decision = ai_engine.evaluate_scalping_overnight_decision(name, code, ctx)
        action = str(decision.get('action', 'SELL_TODAY') or 'SELL_TODAY').upper()

        if action == 'HOLD_OVERNIGHT':
            ok, action_taken = _execute_scalping_hold_overnight(record, mem_stock)
            hold_count += 1
        else:
            ok, action_taken = _execute_scalping_sell_today(record, mem_stock)
            sell_count += 1

        if not ok:
            log_info(f"⚠️ [15:15 EOD] {name}({code}) 처리 실패: {action_taken}")

        summary_rows.append({
            'name': name,
            'code': code,
            'action': action,
            'confidence': int(decision.get('confidence', 0) or 0),
            'pnl_pct': float(ctx.get('pnl_pct', 0.0) or 0.0),
            'note': action_taken,
        })

    if event_bus and escape_markdown and summary_rows:
        lines = [
            "🌙 **[15:15 SCALPING EOD 요약]**",
            f"대상: {len(summary_rows)} | 당일청산: {sell_count} | 오버나이트: {hold_count}",
        ]
        for row in summary_rows:
            esc_name = escape_markdown(row['name'])
            esc_code = escape_markdown(row['code'])
            esc_action = escape_markdown(row['action'])
            esc_note = escape_markdown(row['note'])
            lines.append(
                f"- {esc_name}({esc_code}) | {esc_action} | {row['confidence']}점 | PnL {row['pnl_pct']:+.2f}% | {esc_note}"
            )
        event_bus.publish(
            'TELEGRAM_BROADCAST',
            {'message': "\n".join(lines), 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
        )

    return True
