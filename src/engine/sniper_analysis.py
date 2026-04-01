"""Analysis/report helpers for the sniper engine."""

import time
from datetime import datetime

from src.engine.sniper_s15_fast_track import bind_s15_dependencies
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info


KIWOOM_TOKEN = None
WS_MANAGER = None
EVENT_BUS = None
ACTIVE_TARGETS = None
CONF = None
DB = None
AI_ENGINE = None
TRADING_RULES = None
CHECK_WATCHING_CONDITIONS = None
CHECK_HOLDING_CONDITIONS = None
AI_ENGINE_SETTER = None


def bind_analysis_dependencies(
    *,
    kiwoom_token=None,
    ws_manager=None,
    event_bus=None,
    active_targets=None,
    conf=None,
    db=None,
    ai_engine=None,
    trading_rules=None,
    check_watching_conditions=None,
    check_holding_conditions=None,
    ai_engine_setter=None,
):
    global KIWOOM_TOKEN, WS_MANAGER, EVENT_BUS, ACTIVE_TARGETS, CONF, DB, AI_ENGINE, TRADING_RULES
    global CHECK_WATCHING_CONDITIONS, CHECK_HOLDING_CONDITIONS
    global AI_ENGINE_SETTER

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if ws_manager is not None:
        WS_MANAGER = ws_manager
    if event_bus is not None:
        EVENT_BUS = event_bus
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if conf is not None:
        CONF = conf
    if db is not None:
        DB = db
    if ai_engine is not None:
        AI_ENGINE = ai_engine
    if trading_rules is not None:
        TRADING_RULES = trading_rules
    if check_watching_conditions is not None:
        CHECK_WATCHING_CONDITIONS = check_watching_conditions
    if check_holding_conditions is not None:
        CHECK_HOLDING_CONDITIONS = check_holding_conditions
    if ai_engine_setter is not None:
        AI_ENGINE_SETTER = ai_engine_setter


def analyze_stock_now(code):
    global KIWOOM_TOKEN, WS_MANAGER, EVENT_BUS, ACTIVE_TARGETS, CONF, DB, AI_ENGINE, TRADING_RULES

    now_time = datetime.now().time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    market_close = datetime.strptime("20:00:00", "%H:%M:%S").time()

    if not (market_open <= now_time <= market_close):
        return "🌙 현재는 정규장 운영 시간(09:00~20:00)이 아닙니다.\n실시간 종목 분석은 장중에만 이용 가능합니다."

    if not WS_MANAGER:
        return "⏳ 시스템 초기화 중..."
    EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [code]})

    try:
        stock_name = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)['Name']
    except Exception:
        stock_name = code

    ws_data = {}
    if WS_MANAGER:
        ws_data = WS_MANAGER.wait_for_data(code, timeout=1.5, require_trade=False)

        if not ws_data or ws_data.get('curr', 0) == 0:
            ws_data = WS_MANAGER.wait_for_data(code, timeout=1.5, require_trade=True)

    if not ws_data or ws_data.get('curr', 0) == 0:
        print(f"⚠️ [{stock_name}] 웹소켓 체결 수신 지연. REST API(ka10003)로 폴백합니다.")
        try:
            recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=1)

            if recent_ticks and len(recent_ticks) > 0:
                last_tick = recent_ticks[0]
                fallback_ws = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
                ws_data = {
                    'curr': last_tick.get('price', 0),
                    'fluctuation': last_tick.get('flu_rate', 0.0),
                    'volume': last_tick.get('acc_vol', 0),
                    'v_pw': last_tick.get('strength', 0.0),
                    'ask_tot': fallback_ws.get('ask_tot', 0),
                    'bid_tot': fallback_ws.get('bid_tot', 0),
                    'orderbook': fallback_ws.get('orderbook', {'asks': [], 'bids': []}),
                    'prog_net_qty': fallback_ws.get('prog_net_qty', 0),
                    'prog_delta_qty': fallback_ws.get('prog_delta_qty', 0),
                    'time': fallback_ws.get('time', ''),
                    'fallback_source': 'ka10003',
                }
        except Exception as exc:
            log_error(f"🚨 REST API 폴백 실패: {exc}")

    if not ws_data or ws_data.get('curr', 0) == 0:
        return (
            f"⏳ **{stock_name}**({code}) 체결 데이터 수신 대기 중...\n"
            "(호가는 먼저 들어올 수 있으며, 거래가 멈춰있거나 일시적인 통신 지연일 수 있습니다.)"
        )

    curr_price = ws_data.get('curr', 0)
    fluctuation = float(ws_data.get('fluctuation', 0.0))
    today_vol = ws_data.get('volume', 0)
    v_pw = float(ws_data.get('v_pw', 0.0))
    ask_tot = int(ws_data.get('ask_tot', 0))
    bid_tot = int(ws_data.get('bid_tot', 0))

    target_info = next((t for t in ACTIVE_TARGETS if t['code'] == code), None)
    strategy = target_info.get('strategy', 'KOSPI_ML') if target_info else 'KOSPI_ML'

    if strategy in ['SCALPING', 'SCALP']:
        trailing_pct = getattr(TRADING_RULES, 'SCALP_TARGET', 1.5)
        stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -1.5)
        strat_label = "⚡ 초단타(SCALP)"
    elif strategy == 'KOSDAQ_ML':
        trailing_pct = getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0)
        stop_pct = getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.5)
        strat_label = "🚀 코스닥 스윙"
    else:
        trailing_pct = getattr(TRADING_RULES, 'TRAILING_START_PCT', 4.0)
        stop_pct = getattr(TRADING_RULES, 'STOP_LOSS_BULL', -3.0)
        strat_label = "🛡️ 우량주 스윙(KOSPI_ML)"

    target_price = int(curr_price * (1 + (trailing_pct / 100)))
    target_reason = f"{strat_label} 기본 익절선 (+{trailing_pct}%)"
    vol_ratio = 0.0

    try:
        df = DB.get_stock_data(code, limit=20)
        if df is not None and len(df) >= 10:
            avg_vol_20 = df['volume'].mean()
            if avg_vol_20 > 0:
                vol_ratio = (today_vol / avg_vol_20) * 100

            if strategy not in ['SCALPING', 'SCALP']:
                high_20d = df['high_price'].max()
                ma20 = df['close_price'].mean()
                std20 = df['close_price'].std()
                upper_bb = ma20 + (2 * std20)

                chart_resistance = max(high_20d, upper_bb)
                if chart_resistance > curr_price:
                    target_price = int(chart_resistance)
                    expected_rtn = ((target_price / curr_price) - 1) * 100
                    target_reason = f"차트 저항대 도달 (예상 +{expected_rtn:.1f}%)"
                else:
                    rally_pct = getattr(TRADING_RULES, 'RALLY_TARGET_PCT', 5.0)
                    target_price = int(curr_price * (1 + (rally_pct / 100)))
                    target_reason = f"신고가 돌파 랠리 (단기 추세 +{rally_pct}%)"
    except Exception as exc:
        log_info(f"⚠️ 목표가/거래량 계산 중 에러: {exc}")

    prog_net_qty = int(ws_data.get('prog_net_qty', 0) or 0)
    prog_delta_qty = int(ws_data.get('prog_delta_qty', 0) or 0)
    foreign_net = 0
    inst_net = 0
    try:
        prog_data = kiwoom_utils.get_program_flow_realtime(KIWOOM_TOKEN, code, ws_data=ws_data)
        prog_net_qty = int(prog_data.get('net_qty', prog_net_qty) or 0)
        prog_delta_qty = int(prog_data.get('delta_qty', prog_delta_qty) or 0)

        inv_df = kiwoom_utils.get_investor_daily_ka10059_df(KIWOOM_TOKEN, code)
        if not inv_df.empty:
            foreign_net = int(inv_df['Foreign_Net'].iloc[-1])
            inst_net = int(inv_df['Inst_Net'].iloc[-1])
    except Exception as exc:
        print(f"⚠️ 수급 데이터 조회 지연: {exc}")

    from src.engine.signal_radar import SniperRadar
    score, prices, conclusion, checklist, metrics = SniperRadar.analyze_signal_integrated(ws_data, 0.5, 70)
    ratio_val = metrics.get('ratio_val', 0)

    quant_data_text = (
        f"- 현재가격: {curr_price:,}원 (전일비 {fluctuation:+.2f}%)\n"
        f"- 감시전략: {strat_label} (익절 {trailing_pct}% / 손절 {stop_pct}%)\n"
        f"- 기계목표가: {target_price:,}원 (사유: {target_reason})\n"
        f"- 누적거래량: {today_vol:,}주 (20일 평균대비 {vol_ratio:.1f}%)\n"
        f"- 실시간 체결강도: {v_pw:.1f}%\n"
        f"- 프로그램 순매수/증감: {prog_net_qty:,}주 / {prog_delta_qty:+,}주\n"
        f"- 당일 가집계(외인/기관): 외인 {foreign_net:,}주 / 기관 {inst_net:,}주\n"
        f"- 호가 불균형: {'매도벽 우위(돌파기대)' if ask_tot > bid_tot else '매수벽 우위(하락방어)'} (매도잔량 {ask_tot:,} / 매수잔량 {bid_tot:,})\n"
        f"- 매수세(Ratio) 비중: {ratio_val:.1f}%\n"
        f"- 퀀트 확신점수: {score:.1f}점\n"
        f"- 퀀트 엔진 결론: {conclusion}"
    )

    ai_report = "⚠️ AI 리포트 생성 실패"
    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]

    if AI_ENGINE is None and api_keys:
        try:
            from src.engine.ai_engine import GeminiSniperEngine
            AI_ENGINE = GeminiSniperEngine(api_keys=api_keys)
            bind_s15_dependencies(ai_engine=AI_ENGINE)
            if AI_ENGINE_SETTER is not None:
                AI_ENGINE_SETTER(AI_ENGINE)
        except Exception as exc:
            ai_report = f"⚠️ AI 엔진 초기화 중 오류: {exc}"

    if AI_ENGINE is not None:
        try:
            ai_report = AI_ENGINE.generate_realtime_report(stock_name, code, quant_data_text)
        except Exception as exc:
            ai_report = f"⚠️ AI 리포트 생성 중 오류: {exc}"
    elif not api_keys:
        ai_report = "⚠️ GEMINI_API_KEY 미설정으로 AI 리포트를 생성할 수 없습니다."

    bars = int(ratio_val / 10) if ratio_val > 0 else 0
    visual = f"📊 매수세: [{'🟥'*bars}{'⬜'*(10-bars)}] ({ratio_val:.1f}%)"
    prog_sign = "🔴" if prog_net_qty > 0 else "🔵"

    return (
        f"🔍 *{stock_name} ({code}) 실시간 분석*\n"
        f"💰 현재가: `{curr_price:,}원` ({fluctuation:+.2f}%)\n"
        f"🏷️ 감시전략: *{strat_label}*\n"
        f"🎯 기계 목표가: `{target_price:,}원`\n"
        f"   └ 📝 사유: *{target_reason}*\n"
        f"🔄 거래량: `평균대비 {vol_ratio:.1f}%`\n"
        f"{prog_sign} 프로그램: `{prog_net_qty:,}주 / {prog_delta_qty:+,}주`\n\n"
        f"🧠 **[Gemini 수석 트레이더 AI 브리핑]**\n"
        f"{ai_report}\n\n"
        f"📊 **[퀀트 소나 데이터]**\n"
        f"{visual}\n"
        f"📝 확신지수: `{score:.1f}점`\n"
        f"📝 퀀트결론: {conclusion}"
    )


def get_detailed_reason(code):
    global ACTIVE_TARGETS, KIWOOM_TOKEN, WS_MANAGER, AI_ENGINE, EVENT_BUS, CONF, TRADING_RULES
    global CHECK_WATCHING_CONDITIONS, CHECK_HOLDING_CONDITIONS

    targets = ACTIVE_TARGETS
    target = next((t for t in targets if t['code'] == code), None)

    if not target:
        return f"🔍 `{code}` 종목은 현재 AI 감시 대상이 아닙니다."

    if WS_MANAGER:
        EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [code]})

    ws_data = None
    if WS_MANAGER:
        for _ in range(30):
            ws_data = WS_MANAGER.get_latest_data(code)
            if ws_data and ws_data.get('curr', 0) > 0:
                break
            time.sleep(0.1)

    if not ws_data or ws_data.get('curr', 0) == 0:
        try:
            recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=1)
            if recent_ticks and len(recent_ticks) > 0:
                last_tick = recent_ticks[0]
                ws_data = {
                    'curr': last_tick.get('price', 0),
                    'fluctuation': last_tick.get('flu_rate', 0.0),
                    'volume': last_tick.get('acc_vol', 0),
                    'v_pw': last_tick.get('strength', 0.0),
                    'ask_tot': 0,
                    'bid_tot': 0,
                    'orderbook': {'asks': [], 'bids': []}
                }
        except Exception as exc:
            log_error(f"REST API 폴백 실패 ({code}): {exc}")

    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ `{code}` 데이터 수신 중..."

    ai_prob = target.get('prob', 0.75)

    from src.engine.signal_radar import SniperRadar
    radar = SniperRadar(KIWOOM_TOKEN)
    score, prices, conclusion, checklist, metrics = radar.analyze_signal_integrated(ws_data, ai_prob)

    ai_reason_str = "AI 심층 분석 대기 중 (또는 호출 불가)"
    if AI_ENGINE:
        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

        if recent_ticks:
            ai_decision = AI_ENGINE.analyze_target(target['name'], ws_data, recent_ticks, recent_candles)
            ai_action = ai_decision.get('action', 'WAIT')
            ai_reason = ai_decision.get('reason', '분석 사유 없음')
            ai_score_val = ai_decision.get('score', 50)
            ai_reason_str = f"[{ai_action}] ({ai_score_val}점) {ai_reason}"

    status = target.get('status')
    admin_id = target.get('admin_id')
    market_regime = CONF.get('MARKET_REGIME', 'BULL')
    failure_reason = None

    if status == 'WATCHING' and CHECK_WATCHING_CONDITIONS:
        failure_reason = CHECK_WATCHING_CONDITIONS(target, code, ws_data, admin_id, radar, AI_ENGINE)
    elif status == 'HOLDING' and CHECK_HOLDING_CONDITIONS:
        failure_reason = CHECK_HOLDING_CONDITIONS(target, code, ws_data, admin_id, market_regime, radar, AI_ENGINE)

    if failure_reason:
        telegram_msg = f"🚨 [상태 진단] {target['name']} ({code}) - {status} 상태 전환 실패: {failure_reason}"
        EVENT_BUS.publish("TELEGRAM_MESSAGE", {"message": telegram_msg})

    report = f"🧐 **[{target['name']}] 미진입 사유 상세 분석**\n━━━━━━━━━━━━━━━━━━\n"
    for label, status in checklist.items():
        icon = "✅" if status['pass'] else "❌"
        report += f"{icon} {label}: `{status['val']}`\n"

    if failure_reason:
        report += f"🚨 **상태 전환 장애:** `{failure_reason}`\n\n"

    buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 80)
    report += "━━━━━━━━━━━━━━━━━━\n"
    report += f"🎯 **기계적 수급 점수:** `{int(score)}점` (매수기준: {buy_threshold}점)\n"
    report += f"🤖 **AI 심층 판단:** `{ai_reason_str}`\n"
    report += f"📝 **최종 시스템 결론:** {conclusion}\n"

    # Big-Bite 디버그 정보 (있을 때만 출력)
    bb_triggered = target.get('big_bite_triggered')
    bb_confirmed = target.get('big_bite_confirmed')
    bb_boost = target.get('big_bite_boost_value', 0)
    bb_hard_required = target.get('big_bite_hard_gate_required')
    bb_hard_blocked = target.get('big_bite_hard_gate_blocked')
    bb_info = target.get('big_bite_info') or {}
    if any(v is not None for v in [bb_triggered, bb_confirmed, bb_boost, bb_hard_required, bb_hard_blocked]):
        report += "━━━━━━━━━━━━━━━━━━\n"
        report += (
            "🧪 **Big-Bite 상태**\n"
            f"- triggered: `{bb_triggered}`\n"
            f"- confirmed: `{bb_confirmed}`\n"
            f"- boost: `+{bb_boost}`\n"
            f"- hard_gate_required: `{bb_hard_required}`\n"
            f"- hard_gate_blocked: `{bb_hard_blocked}`\n"
            f"- agg_value: `{bb_info.get('agg_value')}`\n"
            f"- impact_ratio: `{bb_info.get('impact_ratio')}`\n"
            f"- chase_pct: `{bb_info.get('chase_pct')}`\n"
        )

    return report


def get_realtime_ai_scores(codes):
    """
    [V14.0 신규] 외부(텔레그램) 요청 시 감시 중인 종목들의 실시간 AI 점수를 일괄 분석하여 반환합니다.
    """
    global KIWOOM_TOKEN, WS_MANAGER, AI_ENGINE, ACTIVE_TARGETS
    scores = {}

    if not AI_ENGINE or not WS_MANAGER or not KIWOOM_TOKEN:
        return scores

    ws_data_map = WS_MANAGER.get_all_data(codes)

    for code in codes:
        ws_data = ws_data_map.get(code)
        if not ws_data or ws_data.get('curr', 0) == 0:
            try:
                recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=1)
                if recent_ticks and len(recent_ticks) > 0:
                    last_tick = recent_ticks[0]
                    ws_data = {
                        'curr': last_tick.get('price', 0),
                        'fluctuation': last_tick.get('flu_rate', 0.0),
                        'volume': last_tick.get('acc_vol', 0),
                        'v_pw': last_tick.get('strength', 0.0),
                        'ask_tot': 0,
                        'bid_tot': 0,
                        'orderbook': {'asks': [], 'bids': []}
                    }
            except Exception:
                pass

        if not ws_data or ws_data.get('curr', 0) == 0:
            continue

        target = next((t for t in ACTIVE_TARGETS if t['code'] == code), None)
        name = target['name'] if target else code

        try:
            ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
            candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

            if ticks:
                ai_decision = AI_ENGINE.analyze_target(name, ws_data, ticks, candles)
                scores[code] = ai_decision.get('score', 50)

                if target and scores[code] != 50:
                    target['rt_ai_prob'] = scores[code] / 100.0
        except Exception as exc:
            log_error(f"실시간 일괄 AI 분석 에러 ({code}): {exc}")

        time.sleep(0.3)

    return scores
