import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests

import final_ensemble_scanner
import kiwoom_orders
import kiwoom_utils
from constants import TRADING_RULES
from google_sheets_utils import GoogleSheetsManager
from kiwoom_websocket import KiwoomWSManager
from db_manager import DBManager

# ==========================================
# 1. 경로 설정 (상대 참조 통일)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
STOCK_DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
CREDENTIALS_PATH = os.path.join(DATA_DIR, 'credentials.json')

# --- [전역 상태 변수] -----------------------------------------------
highest_prices = {}
alerted_stocks = set()
cooldowns = {}  # 💡 [신규] 스캘핑 뇌동매매 방지용 쿨타임 관리
CONF = None
KIWOOM_TOKEN = None
WS_MANAGER = None
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager()  # 💡 전역 객체 생성
# -------------------------------------------------------------------

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# 초기 설정 로드
try:
    CONF = load_config()
except:
    pass


def reload_config():
    global CONF
    try:
        CONF = load_config()
        print("✅ JSON 설정 파일이 새로고침 되었습니다!")
        return True
    except Exception as e:
        print(f"❌ 설정 새로고침 실패: {e}")
        return False


def send_admin_msg(text):
    if not CONF: return
    admin_id = CONF.get('ADMIN_ID')
    if not admin_id: return

    bot_token = CONF.get('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': admin_id, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ 관리자 메시지 전송 실패: {e}")


def update_stock_status(code, status, buy_price=None, buy_qty=None, buy_time=None):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        nxt = kiwoom_utils.get_stock_market_ka10100(code, KIWOOM_TOKEN)

        with DB._get_connection() as conn:
            # 💡 [핵심 수정] 0이나 빈 문자열이 들어와도 정상적으로 업데이트하도록 명시적 확인
            if buy_price is not None and buy_qty is not None and buy_time is not None:
                conn.execute(
                    "UPDATE recommendation_history SET status=?, buy_price=?, buy_qty=?, buy_time=?, nxt=? WHERE code=? AND date=?",
                    (status, buy_price, buy_qty, buy_time, nxt, code, today))
            else:
                conn.execute("UPDATE recommendation_history SET status=?, nxt=? WHERE date=? AND code=?",
                             (status, nxt, today, code))
            conn.commit()
    except Exception as e:
        print(f"⚠️ DB 업데이트 실패: {e}")

def get_active_targets():
    targets = []
    try:
        today = datetime.now().strftime('%Y-%m-%d')

        with DB._get_connection() as conn:
            query = "SELECT * FROM recommendation_history WHERE date=? OR status='HOLDING'"
            df = pd.read_sql(query, conn, params=(today,))

        if df.empty:
            return targets

        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')
        targets = df.to_dict('records')

        for t in targets:
            t['prob'] = t.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8))
            t['buy_qty'] = t.get('buy_qty', 0)
            # 🚀 [추가] DB에 strategy 값이 없으면 기본적으로 KOSPI_ML 로 취급합니다.
            t['strategy'] = t.get('strategy', 'KOSPI_ML')

        return targets
    except Exception as e:
        print(f"🔥 [DB 로드 에러] 감시 대상을 불러오는 중 문제가 발생했습니다: {e}")
        return targets


# --- [외부 요청용 분석 리포트] ---
def analyze_stock_now(code):
    global KIWOOM_TOKEN, WS_MANAGER
    import time
    from datetime import datetime

    # 🚀 1. 장 운영 시간(09:00 ~ 15:30) 체크 로직
    now_time = datetime.now().time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    market_close = datetime.strptime("15:30:00", "%H:%M:%S").time()

    if not (market_open <= now_time <= market_close):
        return f"🌙 현재는 정규장 운영 시간(09:00~15:30)이 아닙니다.\n실시간 종목 분석은 장중에만 이용 가능합니다."

    # 2. 웹소켓 및 구독 상태 체크
    if not WS_MANAGER: return "⏳ 시스템 초기화 중..."
    WS_MANAGER.subscribe([code])

    try:
        stock_name = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)['Name']
    except:
        stock_name = code

    # 3. 실시간 호가 데이터 수신 대기 (최대 3초)
    ws_data = {}
    for _ in range(30):
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        if ws_data and ws_data.get('curr', 0) > 0: break
        time.sleep(0.1)

    # 💡 안내 메시지 개선: 단순히 '대기 중'이 아니라 이유를 함께 설명
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ **{stock_name}**({code}) 호가창 수신 대기 중...\n(거래가 멈춰있거나 일시적인 통신 지연일 수 있습니다.)"

    # 4. 분석 및 목표가 계산
    curr_price = ws_data.get('curr', 0)
    trailing_pct = TRADING_RULES.get('TRAILING_START_PCT', 3.0)
    target_price = int(curr_price * (1 + (trailing_pct / 100)))
    target_reason = f"기본 시스템 익절선 (+{trailing_pct}%)"

    try:
        df = DB.get_stock_data(code, limit=20)
        if df is not None and len(df) >= 10:
            high_20d = df['High'].max()
            ma20 = df['Close'].mean()
            std20 = df['Close'].std()
            upper_bb = ma20 + (2 * std20)

            chart_resistance = max(high_20d, upper_bb)
            if chart_resistance > curr_price:
                target_price = int(chart_resistance)
                expected_rtn = ((target_price / curr_price) - 1) * 100
                target_reason = f"차트 저항대 도달 (예상 +{expected_rtn:.1f}%)"
            else:
                rally_pct = TRADING_RULES.get('RALLY_TARGET_PCT', 5.0)
                target_price = int(curr_price * (1 + (rally_pct / 100)))
                target_reason = f"신고가 돌파 랠리 (단기 추세 +{rally_pct}%)"
    except Exception as e:
        print(f"⚠️ 목표가 계산 중 에러: {e}")

    # 5. 종합 평가
    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, 0.5, 70)

    return (
        f"🔍 *[{stock_name}]({code}) 실시간 분석*\n"
        f"💰 현재가: `{curr_price:,}원`\n"
        f"{visual}\n"
        f"🎯 1차 목표가: `{target_price:,}원`\n"
        f"   └ 📝 사유: *{target_reason}*\n"
        f"🤖 기계 익절선: `+{trailing_pct}%` (도달 시 트레일링 스탑 가동)\n"
        f"📝 확신지수: `{score:.1f}점`\n"
        f"{conclusion}"
    )


def get_detailed_reason(code):
    targets = get_active_targets()
    target = next((t for t in targets if t['code'] == code), None)

    if not target: return f"🔍 `{code}` 종목은 현재 AI 감시 대상이 아닙니다."

    ws_data = WS_MANAGER.get_latest_data(code)
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ `{code}` 데이터 수신 중..."

    ai_prob = target.get('prob', 0.75)
    score, details, visual, prices, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

    report = f"🧐 **[{target['name']}] 미진입 사유 분석**\n━━━━━━━━━━━━━━━━━━\n"
    for label, status in checklist.items():
        icon = "✅" if status['pass'] else "❌"
        report += f"{icon} {label}: `{status['val']}`\n"

    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
    report += f"🎯 **종합 점수:** `{int(score)}점` (매수기준: {buy_threshold}점)\n"
    report += f"📝 **현재 상태:** {conclusion}\n"
    return report


def check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback):
    watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
    max_slots = TRADING_RULES.get('MAX_WATCHING_SLOTS', 5)
    scan_interval = TRADING_RULES.get('SCAN_INTERVAL_SEC', 1800)

    if watching_count < max_slots and (time.time() - last_scan_time > scan_interval):
        print(f"🔄 [시스템] 감시 슬롯 부족({watching_count}개). 신규 종목을 스캔합니다...")
        try:
            new_picks = final_ensemble_scanner.run_intraday_scanner(KIWOOM_TOKEN)
            if new_picks:
                added_count = 0
                msg_body = ""

                for np in new_picks:
                    if not any(t['code'] == np['code'] for t in targets):
                        targets.append(np)
                        WS_MANAGER.subscribe([np['code']])
                        added_count += 1
                        msg_body += f"• **{np['name']}** ({np['code']}) - AI 확신도: {np['prob']:.1%}\n"

                if added_count > 0:
                    alert_msg = f"🔄 **[장중 주도주 재스캔 완료]**\n빈 슬롯을 채우기 위해 다음 {added_count}개 종목의 실시간 감시를 시작합니다.\n\n{msg_body}"
                    broadcast_callback(alert_msg)

            return time.time()
        except Exception as e:
            kiwoom_utils.log_error(f"⚠️ 장중 스캔 중 오류: {e}")
    return last_scan_time


def handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback):
    strategy = stock.get('strategy', 'KOSPI_ML')
    now_t = datetime.now().time()

    # 🚀 1. 쿨타임(휴식기) 검사
    if code in cooldowns and time.time() < cooldowns[code]:
        return  # 아직 쿨타임이 안 지났으면 무시

    # 🚀 2. 초단타 장 후반 진입 금지 (15:15 이후에는 새로 사지 않음)
    if strategy == 'SCALPING' and now_t >= datetime.strptime("15:15:00", "%H:%M:%S").time():
        return

    if code in alerted_stocks: return

    curr_price = ws_data.get('curr', 0)
    current_vpw = ws_data.get('v_pw', 0)

    is_trigger = False
    msg = ""
    ratio = 0.10  # 💡 [안전장치] 만약을 대비한 기본 비중 선언 (10%)

    ai_prob = stock.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70))
    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
    strong_vpw = TRADING_RULES.get('VPW_STRONG_LIMIT', 120)

    # ==========================================
    # 🚀 [멀티 전략] 진입 분기 처리 (SCALP / KOSDAQ / KOSPI)
    # ==========================================
    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':
        ratio = TRADING_RULES.get('INVEST_RATIO_SCALPING', 0.05)

        # 💡 [핵심 방어 3] 실시간 호가창 주문 잔량(유동성) 체크
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        liquidity_value = (ask_tot + bid_tot) * curr_price

        # 하드락: 호가창에 깔린 매수/매도 대기 물량이 최소 1억 원 이상일 때만 진입 (얇은 호가창 휩쏘 방지)
        MIN_SCALP_LIQUIDITY = 100_000_000

        # 체결강도 120 이상 AND 호가잔량대금 1억 이상
        if current_vpw >= TRADING_RULES.get('VPW_SCALP_LIMIT', 120) and liquidity_value >= MIN_SCALP_LIQUIDITY:

            # 💡 [핵심 방어 1] 스캐너 포착 시점의 가격과 현재 호가창 가격의 갭(Gap) 계산
            scanner_price = stock.get('buy_price', 0)
            if scanner_price > 0:
                gap_pct = (curr_price - scanner_price) / scanner_price * 100

                # 갭이 0.5% 이상 벌어졌다면 이미 늦었다고 판단하고 추격매수 포기!
                if gap_pct >= 0.5:
                    if code not in cooldowns:
                        print(f"⚠️ [{stock['name']}] 포착가 대비 너무 오름 (갭 +{gap_pct:.1f}%). 추격매수 포기 및 쿨타임 진입.")
                        cooldowns[code] = time.time() + 1200  # 20분 쿨타임
                    return

            # 💡 [핵심] kiwoom_utils에서 호가 단위 불러와서 2호가 아래 '눌림목 타점' 계산
            target_buy_price = kiwoom_utils.get_price_ticks_down(curr_price, ticks=2)  # 정확한 2호가 아래 가격

            # stock 딕셔너리에 목표 매수가를 잠시 저장 (주문 전송 시 사용)
            stock['target_buy_price'] = target_buy_price

            is_trigger = True
            msg = (f"⚡ **[{stock['name']}]({code}) 초단타(SCALP) 그물망 투척!**\n"
                   f"현재가: `{curr_price:,}원` ➡️ **매수대기: `{target_buy_price:,}원` (2호가 아래)**\n"
                   f"호가잔량대금: `{liquidity_value / 100_000_000:.1f}억` | 수급강도: `{current_vpw:.1f}%`")

    # 2️⃣ 코스닥 우량주 스윙 (KOSDAQ_ML) 전략
    elif strategy == 'KOSDAQ_ML':
        ratio = TRADING_RULES.get('INVEST_RATIO_KOSDAQ', 0.10)   # 💡 진입하자마자 비중부터 확정
        
        score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

        v_pw_limit = TRADING_RULES.get('VPW_KOSDAQ_LIMIT', 105) if ai_prob >= TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70) else strong_vpw
        is_shooting = current_vpw >= v_pw_limit

        # 하드락: 점수가 높아도 코스닥은 체결강도 105(매수 압도 우위) 미만이면 절대 쏘지 않음
        if (score >= buy_threshold or is_shooting) and current_vpw >= TRADING_RULES.get('VPW_KOSDAQ_LIMIT', 105):
            is_trigger = True
            msg = (f"🚀 **[{stock['name']}]({code}) 코스닥(KOSDAQ) 스나이퍼 포착!**\n"
                   f"현재가: `{curr_price:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{current_vpw:.1f}%` {visual}")

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        ratio = TRADING_RULES.get('INVEST_RATIO_KOSPI', 0.20)    # 💡 진입하자마자 비중부터 확정
        
        # [우량주 스윙 모드] 기존의 깐깐한 AI 통합 분석(20일치 차트)을 거칩니다.
        ai_prob = stock.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8))
        score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

        strong_vpw = TRADING_RULES.get('VPW_STRONG_LIMIT', 115)
        buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
        v_pw_limit = 100 if ai_prob >= TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8) else strong_vpw
        is_shooting = current_vpw >= v_pw_limit

        if (score >= buy_threshold or is_shooting) and current_vpw >= 103:
            is_trigger = True
            msg = (f"🚀 **[{stock['name']}]({code}) 스나이퍼 포착! (스윙)**\n"
                   f"현재가: `{curr_price:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{current_vpw:.1f}%` {visual}")

    # ==========================================
    # 🎯 매수 실행 공통 로직
    # ==========================================
    if is_trigger:
        broadcast_callback(msg)
        alerted_stocks.add(code)

        # 🚀 [상호 검증 반영] 전략별 주문 세팅
        if strategy == 'SCALPING':
            order_type_code = "00"  # 지정가
            final_price = stock.get('target_buy_price', curr_price)
        else:
            order_type_code = "6"  # 스윙은 기존대로 최유리지정가
            final_price = 0  # 최유리는 가격을 0으로 전송 (orders에서 빈칸 처리됨)

        if not admin_id:
            print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID가 없습니다.")
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN, config=CONF)
        real_buy_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio)

        if real_buy_qty <= 0:
            print(f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다.")
            return

        # 💡 [핵심] 이제 order_type_code와 final_price가 정상적으로 배달됩니다!
        res = kiwoom_orders.send_buy_order_market(
            code=code, qty=real_buy_qty, token=KIWOOM_TOKEN,
            config=CONF, order_type=order_type_code, price=final_price
        )

        is_success = False
        ord_no = ''

        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                err_msg = res.get('return_msg', '사유 없음')
                print(f"❌ [주문거절] {stock['name']} 서버 거절: {err_msg}")

                # 🚀 [초단타 전용] 키움 서버가 주문을 튕겨냈을 때 20분 쿨타임!
                if strategy == 'SCALPING':
                    alerted_stocks.discard(code)
                    cooldowns[code] = time.time() + 1200

        elif res:  # res가 단순 True일 때 (호환성)
            is_success = True

        if is_success:
            kiwoom_utils.log_error(
                f"💰 [주문접수] {stock['name']} {real_buy_qty}주 (전략: {strategy}, 타입: {order_type_code})", config=CONF)

            stock.update({
                'status': 'PENDING',
                'buy_price': curr_price,  # 기준가는 현재가로 유지
                'buy_qty': real_buy_qty,
                'odno': ord_no,
                'order_time': time.time()
            })
            highest_prices[code] = curr_price

            update_stock_status(
                code=code, status='PENDING', buy_price=curr_price,
                buy_qty=real_buy_qty, buy_time=datetime.now().strftime('%H:%M:%S')
            )


def handle_holding_state(stock, code, ws_data, admin_id, broadcast_callback, market_regime):
    curr_p = ws_data['curr']
    buy_p = stock.get('buy_price', 0)
    if buy_p <= 0: return

    if code not in highest_prices: highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)

    profit_rate = (curr_p - buy_p) / buy_p * 100
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100

    strategy = stock.get('strategy', 'KOSPI_ML')
    is_sell_signal = False
    reason = ""

    # 💡 [수정] now_t를 함수 상단으로 올려서 아래쪽 부활 로직에서도 시간을 확인할 수 있게 합니다.
    now_t = datetime.now().time()

    # ==========================================
    # 🚀 [멀티 전략] 보유 종목 청산 분기 처리
    # ==========================================
    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':

        held_time_min = 0

        if 'order_time' in stock:
            # 메모리에 기록된 주문 시간으로 가장 정확하게 계산
            held_time_min = (time.time() - stock['order_time']) / 60
        elif 'buy_time' in stock and stock['buy_time']:
            # 프로그램 재시작 시 DB에 기록된 시간(HH:MM:SS)을 불러와서 계산
            try:
                b_time = datetime.strptime(stock['buy_time'], '%H:%M:%S').time()
                b_dt = datetime.combine(datetime.now().date(), b_time)
                held_time_min = (datetime.now() - b_dt).total_seconds() / 60
            except:
                pass

        if profit_rate >= TRADING_RULES['SCALP_TARGET']:
            is_sell_signal = True
            reason = f"⚡ 초단타 목표 수익 컷 (+{TRADING_RULES['SCALP_TARGET']}%)"
        elif profit_rate <= TRADING_RULES['SCALP_STOP']:
            is_sell_signal = True
            reason = f"🔪 초단타 무호흡 칼손절 ({TRADING_RULES['SCALP_STOP']}%)"
            
        # 🚀 [신규 추가] 30분이 지났고, 0.3% 이상 수익 중이면 미련 없이 던짐!
        elif held_time_min >= TRADING_RULES['SCALP_TIME_LIMIT_MIN'] and profit_rate >= TRADING_RULES['MIN_FEE_COVER']:
            is_sell_signal = True
            reason = f"⏱️ {TRADING_RULES['SCALP_TIME_LIMIT_MIN']}분 타임아웃 (기회비용 확보용 약익절)"

        # 초단타 오버나잇 금지 (15시 15분 전량 청산)
        elif now_t >= datetime.strptime("15:15:00", "%H:%M:%S").time():
            is_sell_signal = True
            reason = "⏰ 초단타 오버나잇 회피 (장 마감 현금화)"

    # 2️⃣ 코스닥 AI 스윙 (KOSDAQ_ML) 전용 전략 🚀 [신규 추가]
    elif strategy == 'KOSDAQ_ML':

        # 1. 영업일 기준 만료 청산 (안전망 기본값: 2일)
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= TRADING_RULES.get('KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
        except:
            pass

        # 2. 가변 익절 (트레일링 스탑) (안전망 기본값: 4.0%)
        if not is_sell_signal and peak_profit >= TRADING_RULES.get('KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            # 코스닥은 윗꼬리가 길게 달리므로, 고점 대비 조금만 빠져도(1.0%) 바로 수익 실현
            if drawdown >= 1.0:
                is_sell_signal = True
                reason = f"🏆 KOSDAQ 트레일링 익절 (+{TRADING_RULES.get('KOSDAQ_TARGET', 4.0)}% 돌파 후 하락)"

        # 3. 코스닥 전용 타이트한 손절 (안전망 기본값: -2.0%)
        elif not is_sell_signal and profit_rate <= TRADING_RULES.get('KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({TRADING_RULES.get('KOSDAQ_STOP', -2.0)}%)"

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        # [우량주 스윙 청산 룰] 기존의 가변 익절, 트레일링 스탑 적용
        pos_tag = stock.get('position_tag', 'MIDDLE')
        if pos_tag == 'BREAKOUT':
            current_stop_loss = TRADING_RULES['STOP_LOSS_BREAKOUT']
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = TRADING_RULES['STOP_LOSS_BOTTOM']
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = TRADING_RULES['STOP_LOSS_BULL'] if market_regime == 'BULL' else TRADING_RULES[
                'STOP_LOSS_BEAR']
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        # 1. 영업일 기준 만료 청산
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            today_date = datetime.now().date()
            if np.busday_count(buy_date, today_date) >= TRADING_RULES['HOLDING_DAYS']:
                is_sell_signal = True
                reason = f"⏳ {TRADING_RULES['HOLDING_DAYS']}일 스윙 보유 만료"
        except:
            pass

        # 2. 트레일링 스탑 (가변 익절)
        if not is_sell_signal and peak_profit >= TRADING_RULES['TRAILING_START_PCT']:
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= TRADING_RULES['TRAILING_DRAWDOWN_PCT']:
                is_sell_signal = True
                reason = f"🏆 가변익절 (+{TRADING_RULES['TRAILING_START_PCT']}% 도달 후 하락)"
            elif profit_rate <= TRADING_RULES['MIN_PROFIT_PRESERVE']:
                is_sell_signal = True
                reason = f"수익 보존 (최소 {TRADING_RULES['MIN_PROFIT_PRESERVE']}%)"

        # 3. 손절
        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"

    # ==========================================
    # 🎯 매도 실행 공통 로직
    # ==========================================
    if is_sell_signal:
        sign = "🎊 [익절]" if profit_rate > 0 else "📉 [손절]"
        msg = (f"{sign} **{stock['name']} 트래킹 종료 ({strategy})**\n사유: `{reason}`\n"
               f"최종 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)")

        if admin_id and stock.get('buy_qty', 0) > 0:
            kiwoom_orders.send_sell_order_market(code, stock['buy_qty'], KIWOOM_TOKEN, config=CONF)

        highest_prices.pop(code, None)

        # 🚀 [초단타 부활 로직]
        if strategy == 'SCALPING' and now_t < datetime.strptime("15:15:00", "%H:%M:%S").time():
            stock['status'] = 'WATCHING'
            stock['buy_qty'] = 0
            stock['buy_price'] = 0
            alerted_stocks.discard(code)
            cooldowns[code] = time.time() + 1200  # 20분 쿨타임!

            # 💡 [DB 기록] 부활하더라도 방금 완료된 매매 수익률과 가격은 기록!
            DB.update_sell_record(code, curr_p, profit_rate, status='WATCHING')
            update_stock_status(code, 'WATCHING', buy_price=0, buy_qty=0, buy_time='')
            broadcast_callback(msg + f"\n♻️ (20분 쿨타임 후 재감시 돌입)")

        # 일반 종료 (완전 종료)
        else:
            stock['status'] = 'COMPLETED'
            # 💡 [DB 기록] 최종 매매 수익률과 가격을 영구 보존!
            DB.update_sell_record(code, curr_p, profit_rate, status='COMPLETED')
            update_stock_status(code, 'COMPLETED')
            broadcast_callback(msg)


def handle_pending_state(stock, code):
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time
    timeout_sec = TRADING_RULES.get('ORDER_TIMEOUT_SEC', 30)

    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 주문 {timeout_sec}초 경과. 미체결 물량 취소 시도.")
        orig_ord_no = stock.get('odno')

        # 1. 원주문번호가 없는 비정상 펜딩 상태일 때의 탈출 로직
        if not orig_ord_no:
            stock['status'] = 'WATCHING'
            stock.pop('order_time', None)

            if stock.get('strategy') == 'SCALPING':
                alerted_stocks.discard(code)
                cooldowns[code] = time.time() + 1200 # 💡 20분으로 통일
            return

        # 2. 정상적인 미체결 주문 취소 전송
        res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0,
                                              config=CONF)

        # 3. 취소 접수 성공 시 부활 로직
        if res:
            stock['status'] = 'WATCHING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            highest_prices.pop(code, None)
            update_stock_status(code, 'WATCHING', buy_price=0, buy_qty=0, buy_time='')

            # 🚀 [초단타 부활 로직] 미체결 취소(호가가 도망감) 시 추격매수 안하고 20분 대기!
            if stock.get('strategy') == 'SCALPING':
                alerted_stocks.discard(code)
                cooldowns[code] = time.time() + 1200 # 💡 20분으로 통일

        # 4. 취소 실패 시 (이미 체결되었을 확률이 높음) 보유 상태로 전환
        else:
            stock['status'] = 'HOLDING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            update_stock_status(code, 'HOLDING')


# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (교통 정리 전담)
# ==============================================================================
def run_sniper(broadcast_callback):
    global KIWOOM_TOKEN, WS_MANAGER

    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V12.2 멀티 엔진 가동 (관리자: {admin_id})")

    is_open, reason = kiwoom_utils.is_trading_day()
    if not is_open:
        msg = f"🛑 오늘은 {reason} 휴장일이므로 스나이퍼 매매 엔진을 가동하지 않습니다."
        print(msg)
        broadcast_callback(msg)
        return

    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        kiwoom_utils.log_error("❌ 토큰 발급 실패로 엔진을 중단합니다.", config=CONF, send_telegram=True)
        return

    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)
    WS_MANAGER.start()
    time.sleep(2)

    targets = get_active_targets()
    last_scan_time = time.time()

    # 🚀 [핵심] 외부 스캐너가 DB에 밀어넣은 신규 종목을 감지하기 위한 타이머
    last_db_poll_time = time.time()

    current_market_regime = kiwoom_utils.get_market_regime(KIWOOM_TOKEN)
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다.")

    target_codes = [t['code'] for t in targets]
    WS_MANAGER.subscribe([c for c in target_codes])
    last_msg_min = -1

    try:
        while True:
            # 💡 [신규 추가] 'restart.flag' 파일이 생성되었는지 확인
            if os.path.exists("restart.flag"):
                print("🔄 [우아한 종료] 재시작 깃발을 확인했습니다. 시스템을 안전하게 정지합니다.")
                broadcast_callback("🛑 스나이퍼 엔진이 하던 작업을 마치고 우아하게 재시작됩니다.")
                os.remove("restart.flag")  # 깃발 수거
                break  # 무자비한 종료가 아닌, 루프를 스무스하게 빠져나감

            now = datetime.now()
            now_t = now.time()

            if now_t >= datetime.strptime("15:30:00", "%H:%M:%S").time():
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                break

            # 1. 내부 장중 스캐너 가동 (KOSPI)
            last_scan_time = check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback)

            # 🚀 2. [신규 추가] 15초마다 외부(초단타 스캐너 등)에서 DB에 새로 넣은 종목이 있는지 확인
            if time.time() - last_db_poll_time > 15:
                db_targets = get_active_targets()
                for dt in db_targets:
                    if not any(t['code'] == dt['code'] for t in targets):
                        targets.append(dt)
                        WS_MANAGER.subscribe([dt['code']])
                        print(f"🔄 [멀티 스캐너 연동] {dt['name']}({dt['code']}) 감시망 쾌속 합류! (전략: {dt.get('strategy')})")
                last_db_poll_time = time.time()

            # 3. 콘솔 가동 상태 로그 (1분 주기)
            if now_t.minute != last_msg_min:
                watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
                holding_count = len([t for t in targets if t['status'] == 'HOLDING'])
                print(f"💓 [{now.strftime('%H:%M:%S')}] 다중 감시망 가동 중... (감시: {watching_count} / 보유: {holding_count})")
                last_msg_min = now_t.minute

            # 4. 개별 종목 상태 라우팅
            for stock in targets:
                code = str(stock['code'])[:6]
                status = stock['status']

                ws_data = WS_MANAGER.get_latest_data(code)
                if not ws_data or ws_data.get('curr', 0) == 0: continue

                if status == 'WATCHING':
                    handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback)
                elif status == 'HOLDING':
                    handle_holding_state(stock, code, ws_data, admin_id, broadcast_callback, current_market_regime)
                elif status == 'PENDING':
                    handle_pending_state(stock, code)

            time.sleep(1)

    except Exception as e:
        kiwoom_utils.log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}", config=CONF, send_telegram=True)

    except KeyboardInterrupt:
        print("\n🛑 스나이퍼 매매 엔진 종료")