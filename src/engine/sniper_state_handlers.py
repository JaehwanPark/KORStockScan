"""State machine handlers for the sniper engine."""

import time
from datetime import datetime

import numpy as np

from src.database.models import RecommendationHistory
from src.engine import kiwoom_orders
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.engine.sniper_time import (
    TIME_09_00,
    TIME_09_03,
    TIME_09_05,
    TIME_15_30,
    TIME_SCALPING_NEW_BUY_CUTOFF,
)


KIWOOM_TOKEN = None
DB = None
EVENT_BUS = None
ACTIVE_TARGETS = None
COOLDOWNS = None
ALERTED_STOCKS = None
HIGHEST_PRICES = None
LAST_AI_CALL_TIMES = None
LAST_LOG_TIMES = None
TRADING_RULES = None
PUBLISH_GATEKEEPER_REPORT = None
SHOULD_BLOCK_SWING_ENTRY = None
CONFIRM_CANCEL_OR_RELOAD_REMAINING = None
SEND_EXIT_BEST_IOC = None


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
):
    global KIWOOM_TOKEN, DB, EVENT_BUS, ACTIVE_TARGETS, COOLDOWNS, ALERTED_STOCKS, HIGHEST_PRICES
    global LAST_AI_CALL_TIMES, LAST_LOG_TIMES, TRADING_RULES, PUBLISH_GATEKEEPER_REPORT
    global SHOULD_BLOCK_SWING_ENTRY, CONFIRM_CANCEL_OR_RELOAD_REMAINING, SEND_EXIT_BEST_IOC

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if event_bus is not None:
        EVENT_BUS = event_bus
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
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
    MAX_SWING_GAP_UP_PCT = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
    VPW_KOSDAQ_LIMIT = getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105)
    VPW_STRONG_KOSDAQ_LIMIT = getattr(TRADING_RULES, 'VPW_STRONG_KOSDAQ_LIMIT', 120)
    BUY_SCORE_KOSDAQ_THRESHOLD = getattr(TRADING_RULES, 'BUY_SCORE_KOSDAQ_THRESHOLD', 80)
    INVEST_RATIO_KOSDAQ_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MIN', 0.05)
    INVEST_RATIO_KOSDAQ_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MAX', 0.15)
    AI_SCORE_THRESHOLD_KOSDAQ = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60)
    INVEST_RATIO_KOSPI_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MIN', 0.10)
    INVEST_RATIO_KOSPI_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MAX', 0.30)
    AI_SCORE_THRESHOLD_KOSPI = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSPI', 60)

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    pos_tag = stock.get('position_tag', 'MIDDLE')

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

        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price

        if fluctuation >= MAX_SURGE or intraday_surge >= MAX_INTRADAY_SURGE:
            log_info(
                f"[DEBUG] {code} 과매수 위험 차단 (fluctuation={fluctuation:.2f} >= {MAX_SURGE} "
                f"또는 intraday_surge={intraday_surge:.2f} >= {MAX_INTRADAY_SURGE})"
            )
            return

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
                return

            if current_vpw < VPW_SCALP_LIMIT:
                log_info(f"[DEBUG] {code} VPW 불충족 (current_vpw={current_vpw:.1f} < VPW_SCALP_LIMIT)")
                return
            if liquidity_value < MIN_LIQUIDITY:
                log_info(
                    f"[DEBUG] {code} 유동성 불충족 (liquidity_value={liquidity_value:,.0f} "
                    f"< MIN_LIQUIDITY={MIN_LIQUIDITY:,.0f})"
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
                    log_info(f"[DEBUG] {code} 첫 AI 분석 턴 대기 (SCALPING)")
                    return

            if current_ai_score < 75 and current_ai_score != 50:
                if time.time() - last_ai_time < 1.0:
                    action_str = "WAIT(진입 보류)" if current_ai_score > 40 else "DROP(진입 차단)"
                    print(f"🚫 [AI 매수 거부] {stock['name']} {action_str} (AI 점수: {current_ai_score}점)")

                cooldown_time = AI_WAIT_DROP_COOLDOWN

                cooldowns[code] = time.time() + cooldown_time
                log_info(f"[DEBUG] {code} AI 점수 불충족 (current_ai_score={current_ai_score} < 75)")
                return

            final_target_buy_price, final_used_drop_pct = radar.get_smart_target_price(
                curr_price,
                v_pw=current_vpw,
                ai_score=current_ai_score,
                ask_tot=ask_tot,
                bid_tot=bid_tot,
            )

            stock['target_buy_price'] = final_target_buy_price
            is_trigger = True

    elif strategy in ['KOSDAQ_ML', 'KOSPI_ML']:
        if radar is None:
            log_info(f"[DEBUG] {code} radar 객체 없음 (KOSDAQ_ML/KOSPI_ML)")
            return

        if strategy == 'KOSDAQ_ML':
            max_gap = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
            if fluctuation >= max_gap:
                log_info(
                    f"[DEBUG] {code} 갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})"
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
            max_gap = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
            if fluctuation >= max_gap:
                log_info(
                    f"[DEBUG] {code} 갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})"
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
            gatekeeper_reject_cd = getattr(TRADING_RULES, 'ML_GATEKEEPER_REJECT_COOLDOWN', 60 * 60 * 2)
            gatekeeper_error_cd = getattr(TRADING_RULES, 'ML_GATEKEEPER_ERROR_COOLDOWN', 60 * 10)
            gatekeeper = None
            gatekeeper_allow = False
            action_label = 'UNKNOWN'

            if not ai_engine:
                log_error(f"🚨 [{strategy} Gatekeeper 미초기화] {stock['name']}({code})")
                cooldowns[code] = time.time() + gatekeeper_error_cd
                return

            try:
                realtime_ctx = kiwoom_utils.build_realtime_analysis_context(
                    token=KIWOOM_TOKEN,
                    code=code,
                    ws_data=ws_data,
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
                gatekeeper = ai_engine.evaluate_realtime_gatekeeper(
                    stock_name=stock['name'],
                    stock_code=code,
                    realtime_ctx=realtime_ctx,
                    analysis_mode='SWING',
                )
                LAST_AI_CALL_TIMES[code] = time.time()
                action_label = gatekeeper.get('action_label', 'UNKNOWN')
                gatekeeper_allow = bool(gatekeeper.get('allow_entry', False))
                stock['last_gatekeeper_action'] = action_label
                stock['last_gatekeeper_report'] = gatekeeper.get('report', '')
            except Exception as e:
                log_error(f"🚨 [{strategy} Gatekeeper 오류] {stock['name']}({code}): {e}")
                cooldowns[code] = time.time() + gatekeeper_error_cd
                return

            if not gatekeeper_allow:
                print(f"🚫 [{strategy} Gatekeeper 거부] {stock['name']} ({action_label})")
                cooldowns[code] = time.time() + gatekeeper_reject_cd
                return

            blocked, block_reason = _should_block_swing_entry(stock.get('strategy', ''))
            if blocked:
                print(f"⛔ [시장환경필터] {stock['name']}({code}) 스윙 진입 보류 - {block_reason}")
                log_info(f"[DEBUG] {code} 시장환경필터에 의한 스윙 진입 보류 (reason: {block_reason})")
                return

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
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        real_buy_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio)

        if real_buy_qty <= 0:
            print(f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다. (자금 부족으로 20분 제외)")
            log_info(f"[DEBUG] {code} 매수 수량 0주 (자금 부족)")
            cooldowns[code] = time.time() + 1200
            return

        if strategy == 'SCALPING':
            order_type_code = "00"
            final_price = int(float(stock.get('target_buy_price', curr_price) or curr_price))
        else:
            order_type_code = "6"
            final_price = 0

        res = kiwoom_orders.send_buy_order(
            code,
            real_buy_qty,
            final_price,
            order_type_code,
            token=KIWOOM_TOKEN,
            order_type_desc="매수" if strategy == 'SCALPING' else "최유리지정가",
        )

        msg = msg or (
            f"✅ **{stock['name']} ({code}) 진입 주문 전송!**\n"
            f"전략: `{strategy}`\n"
            f"현재가: `{curr_price:,}원`\n"
            f"주문 수량: `{real_buy_qty}주`"
        )

        if res is None:
            print(f"❌ [{stock['name']}] 매수 주문 전송 실패 (None 반환)")
            return

        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
                log_info(f"[DEBUG] {stock['name']} 매수 주문 성공. ord_no={ord_no}")
                stock['status'] = 'BUY_ORDERED'
                stock['order_time'] = time.time()
                stock['order_price'] = curr_price
                stock['buy_qty'] = real_buy_qty
                if ord_no:
                    stock['odno'] = ord_no
                stock['pending_buy_msg'] = msg

                if strategy in ['SCALPING', 'SCALP']:
                    alerted_stocks.add(code)
                else:
                    stock['msg_audience'] = 'VIP_ALL'

                try:
                    with DB.get_session() as session:
                        session.query(RecommendationHistory).filter_by(id=stock.get('id')).update({
                            "status": "BUY_ORDERED",
                            "buy_price": curr_price,
                            "buy_qty": real_buy_qty,
                        })
                except Exception as e:
                    log_error(f"🚨 [DB 에러] {stock['name']} BUY_ORDERED 장부 업데이트 실패: {e}")

                if event_bus:
                    event_bus.publish(
                        'TELEGRAM_BROADCAST',
                        {'message': msg, 'audience': stock.get('msg_audience', 'ADMIN_ONLY')},
                    )

            else:
                print(f"❌ [{stock['name']}] 매수 주문 거절: {res.get('return_msg')}")

        else:
            print(f"❌ [{stock['name']}] 매수 주문 전송 실패 (응답 파싱 실패)")



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

    curr_p = int(float(ws_data.get('curr', 0) or 0))
    buy_p = float(stock.get('buy_price', 0) or 0)
    if curr_p <= 0 or buy_p <= 0:
        return

    if code not in highest_prices:
        highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)

    profit_rate = (curr_p - buy_p) / buy_p * 100
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100

    if strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        last_log = LAST_LOG_TIMES.get(code, 0)
        if time.time() - last_log >= 600:
            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            log_info(
                f"[{strategy}] 보유 종목 감시 중: {stock['name']}({code}) 수익률 {profit_rate:+.2f}%, "
                f"AI 점수 {current_ai_score:.0f}점"
            )
            LAST_LOG_TIMES[code] = time.time()

    if stock.get('exit_mode') == 'SCALP_PRESET_TP':
        if stock.get('exit_requested'):
            return

        profit_rate = (curr_p - buy_p) / buy_p * 100 if buy_p > 0 else 0.0
        orig_ord_no = stock.get('preset_tp_ord_no', '')
        expected_qty = stock.get('buy_qty', 0)

        if profit_rate <= stock.get('hard_stop_pct', -0.7):
            print(
                f"🔪 [SCALP 출구엔진] {stock['name']} 손절선 터치({profit_rate:.2f}%). "
                "즉각 최유리(IOC) 청산!"
            )
            rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
            if rem_qty > 0:
                sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                stock['exit_requested'] = True
                stock['exit_order_type'] = '16'
                stock['exit_order_time'] = time.time()
                stock['sell_ord_no'] = (
                    sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
                )
            stock['status'] = 'SELL_ORDERED'
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

                    if ai_action in ['SELL', 'DROP']:
                        print(
                            "🛑 [SCALP 출구엔진 AI] 모멘텀 둔화 감지. 1.5% 포기 후 즉시 최유리(IOC) "
                            "청산!"
                        )
                        rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
                        if rem_qty > 0:
                            sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                            stock['exit_requested'] = True
                            stock['exit_order_type'] = '16'
                            stock['exit_order_time'] = time.time()
                            stock['sell_ord_no'] = (
                                sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
                            )
                        stock['status'] = 'SELL_ORDERED'
                        return
                    else:
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
            rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
            if rem_qty > 0:
                sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                stock['exit_requested'] = True
                stock['exit_order_type'] = '16'
                stock['exit_order_time'] = time.time()
                stock['sell_ord_no'] = (
                    sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
                )
            stock['status'] = 'SELL_ORDERED'
            return

        return

    is_sell_signal = False
    sell_reason_type = "PROFIT"
    reason = ""

    now = datetime.now()
    now_t = now.time()

    last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
    current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100

    last_ai_profit = stock.get('last_ai_profit', profit_rate)
    price_change = abs(profit_rate - last_ai_profit)
    time_elapsed = time.time() - last_ai_time

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
            try:
                recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

                if ws_data.get('orderbook') and recent_ticks:
                    ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)
                    raw_ai_score = ai_decision.get('score', 50)

                    smoothed_score = int((current_ai_score * 0.6) + (raw_ai_score * 0.4))
                    stock['rt_ai_prob'] = smoothed_score / 100.0
                    stock['last_ai_profit'] = profit_rate
                    current_ai_score = smoothed_score

                    print(
                        f"👁️ [AI 보유감시: {stock['name']}] 수익: {profit_rate:+.2f}% | "
                        f"AI: {current_ai_score:.0f}점 | 갱신주기: {dynamic_max_cd}초"
                    )

            except Exception as e:
                log_info(f"🚨 [보유 AI 감시 에러] {stock['name']}({code}): {e}")
            finally:
                LAST_AI_CALL_TIMES[code] = time.time()

    if strategy == 'SCALPING':
        held_time_min = 0
        if 'order_time' in stock and stock.get('order_time'):
            held_time_min = (time.time() - stock['order_time']) / 60
        elif stock.get('buy_time'):
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
                held_time_min = (datetime.now() - b_dt).total_seconds() / 60
            except Exception:
                pass

        base_stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -1.5)
        hard_stop_pct = getattr(TRADING_RULES, 'SCALP_HARD_STOP', -2.5)
        safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
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

        if profit_rate <= hard_stop_pct:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 하드스탑 도달 ({hard_stop_pct}%) [AI: {current_ai_score:.0f}]"

        elif profit_rate <= dynamic_stop_pct:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🔪 소프트 손절 ({dynamic_stop_pct}%) [AI: {current_ai_score:.0f}]"

        elif profit_rate < 0 and current_ai_score <= 35:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🚨 AI 하방 리스크 포착 ({current_ai_score:.0f}점). 조기 손절 ({profit_rate:.2f}%)"

        elif profit_rate >= safe_profit_pct:
            if current_ai_score < 50:
                is_sell_signal = True
                sell_reason_type = "MOMENTUM_DECAY"
                reason = (
                    f"🤖 AI 틱 가속도 둔화 ({current_ai_score:.0f}점). 즉각 익절 (+{profit_rate:.2f}%)"
                )

            elif drawdown >= dynamic_trailing_limit:
                is_sell_signal = True
                sell_reason_type = "TRAILING"
                reason = f"🔥 고점 대비 밀림 (-{drawdown:.2f}%). 트레일링 익절 (+{profit_rate:.2f}%)"

    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= getattr(TRADING_RULES, 'KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
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

        elif not is_sell_signal and profit_rate <= getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0)}%)"

    elif strategy == 'KOSPI_ML':
        pos_tag = stock.get('position_tag', 'MIDDLE')
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

        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"

    if is_sell_signal:
        sign = "📉 [손절 주문]" if sell_reason_type == 'LOSS' else "🎊 [익절 주문]"
        msg = (
            f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n"
            f"사유: `{reason}`\n"
            f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)"
        )

        is_success = False
        target_id = stock.get('id')

        buy_qty = 0
        try:
            with DB.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                if record and record.buy_qty:
                    buy_qty = int(record.buy_qty)
        except Exception as e:
            print(f"🚨 [DB 조회 에러] ID {target_id} 수량 조회 실패: {e}")

        if buy_qty <= 0:
            buy_qty = int(float(stock.get('buy_qty', 0) or 0))

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

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": new_status})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")
                log_info(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")

            if new_status == 'COMPLETED':
                highest_prices.pop(code, None)


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
