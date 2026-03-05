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
from src.db_manager import DBManager

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
CONF = None
KIWOOM_TOKEN = None
WS_MANAGER = None
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager() # 💡 전역 객체 생성
# -------------------------------------------------------------------

def load_config():
    # 💡 [수정] 상대 경로가 적용된 CONFIG_PATH 사용
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# 초기 설정 로드
try:
    CONF = load_config()
except:
    pass # 메인 엔진 기동 시 다시 로드됨

def reload_config():
    global CONF
    try:
        CONF = load_config()
        print("✅ JSON 설정 파일이 새로고침 되었습니다!")
        return True
    except Exception as e:
        print(f"❌ 설정 새로고침 실패: {e}")
        return False


# 💡 관리자(님) 한 명에게만 주문 결과를 귓속말하는 함수
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


# --- [공통: 상태 업데이트 함수] ---
def update_stock_status(code, status, buy_price=None, buy_qty=None, buy_time=None):
    """DBManager를 통한 안전한 DB 상태 업데이트"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        nxt = kiwoom_utils.get_stock_market_ka10100(code, KIWOOM_TOKEN)

        with DB._get_connection() as conn:
            if buy_price and buy_qty and buy_time:
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
    """DBManager를 통한 감시 대상 종목 안전 조회"""
    targets = []
    try:
        today = datetime.now().strftime('%Y-%m-%d')

        with DB._get_connection() as conn:
            query = "SELECT * FROM recommendation_history WHERE date=? OR status='HOLDING'"
            df = pd.read_sql(query, conn, params=(today,))

        if df.empty:
            return targets

        # 중복 제거 및 딕셔너리 변환
        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')
        targets = df.to_dict('records')

        # constants.py 의 임계값 적용
        for t in targets:
            t['prob'] = t.get('prob', TRADING_RULES['SNIPER_AGGRESSIVE_PROB'])
            t['buy_qty'] = t.get('buy_qty', 0)

        return targets
    except Exception as e:
        print(f"🔥 [DB 로드 에러] 감시 대상을 불러오는 중 문제가 발생했습니다: {e}")
        return targets


# --- [2. 외부 요청용 실시간 분석 함수] ---
def analyze_stock_now(code):
    global KIWOOM_TOKEN, WS_MANAGER
    import time
    from db_manager import DBManager

    if not WS_MANAGER: return "⏳ 시스템 초기화 중..."

    import kiwoom_utils
    WS_MANAGER.subscribe([code])

    # 1. 종목명 가져오기
    try:
        stock_name = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)['Name']
    except:
        stock_name = code

    # 2. 실시간 웹소켓 데이터 대기
    ws_data = {}
    for _ in range(30):
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        if ws_data and ws_data.get('curr', 0) > 0: break
        time.sleep(0.1)

    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ **{stock_name}**({code}) 데이터 수신 대기 중..."

    curr_price = ws_data.get('curr', 0)

    # ==========================================
    # 💡 [신규] 차트 기반 '진짜 목표가' 계산 로직
    # ==========================================
    from constants import TRADING_RULES
    trailing_pct = TRADING_RULES.get('TRAILING_START_PCT', 3.0)

    # 퍼센트(%)를 소수로 변환하여 곱해줍니다 (예: 3.0 -> 1.03)
    target_price = int(curr_price * (1 + (trailing_pct / 100)))
    target_reason = f"기본 시스템 익절선 (+{trailing_pct}%)"

    try:
        db = DBManager()
        # 최근 20일치 차트 데이터 불러오기
        df = db.get_stock_data(code, limit=20)

        if df is not None and len(df) >= 10:
            # 1. 20일 최고가 저항선
            high_20d = df['High'].max()

            # 2. 볼린저밴드 상단(20, 2) 저항선 계산
            ma20 = df['Close'].mean()
            std20 = df['Close'].std()
            upper_bb = ma20 + (2 * std20)

            # 두 저항선 중 더 높은 곳을 1차 목표가로 설정
            chart_resistance = max(high_20d, upper_bb)

            if chart_resistance > curr_price:
                target_price = int(chart_resistance)
                expected_rtn = ((target_price / curr_price) - 1) * 100
                target_reason = f"차트 저항대 도달 (예상 +{expected_rtn:.1f}%)"
            else:
                # 💡 [개선] 1.05 하드코딩 제거, RALLY_TARGET_PCT 연동
                rally_pct = TRADING_RULES.get('RALLY_TARGET_PCT', 5.0)
                target_price = int(curr_price * (1 + (rally_pct / 100)))
                target_reason = f"신고가 돌파 랠리 (단기 추세 +{rally_pct}%)"

    except Exception as e:
        print(f"⚠️ 목표가 계산 중 에러: {e}")

    # 3. 기존 AI 분석 로직 실행
    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, 0.5, 70)

    from constants import TRADING_RULES
    trailing_pct = TRADING_RULES.get('TRAILING_START_PCT', 3.0)

    # 4. 최종 리포트 생성 (목표가와 익절선 분리)
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
    """
    특정 종목이 왜 안 사고 있는지 상세 사유를 리포트로 반환
    """
    # 1. 감시 리스트에서 해당 종목 찾기
    targets = get_active_targets()
    target = next((t for t in targets if t['code'] == code), None)

    if not target:
        return f"🔍 `{code}` 종목은 현재 AI 감시 대상(WATCHING)이 아닙니다."

    # 2. 실시간 데이터 획득
    ws_data = WS_MANAGER.get_latest_data(code)
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ `{code}` 종목의 실시간 데이터를 수신 중입니다. 잠시 후 다시 시도해 주세요."

    # 3. 통합 분석 실행
    ai_prob = target.get('prob', 0.75)
    score, details, visual, prices, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

    # 4. 리포트 생성
    report = f"🧐 **[{target['name']}] 미진입 사유 분석**\n"
    report += f"━━━━━━━━━━━━━━━━━━\n"
    for label, status in checklist.items():
        icon = "✅" if status['pass'] else "❌"
        report += f"{icon} {label}: `{status['val']}`\n"

    # 💡 [개선] 80점 하드코딩 제거
    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
    report += f"🎯 **종합 점수:** `{int(score)}점` (매수기준: {buy_threshold}점)\n"
    report += f"📝 **현재 상태:** {conclusion}\n"
    report += f"\n💡 *TIP: 모든 항목이 ✅이고 점수가 {buy_threshold}점 이상일 때 자동으로 매수 주문이 집행됩니다.*"

    return report


def check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback):
    """[장중 스캔 부서] 감시 슬롯이 부족하면 신규 주도주를 보충합니다."""
    watching_count = len([t for t in targets if t['status'] == 'WATCHING'])

    # 💡 [개선] 숫자 5와 1800초(30분) 하드코딩 제거
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
                    print(f"✅ [시스템] 신규 종목 {added_count}개 감시 리스트에 추가 완료")
                    # 🚀 [추가] 텔레그램 발송
                    alert_msg = f"🔄 **[장중 주도주 재스캔 완료]**\n빈 슬롯을 채우기 위해 다음 {added_count}개 종목의 실시간 감시를 시작합니다.\n\n{msg_body}"
                    broadcast_callback(alert_msg)

            return time.time()  # 스캔 완료 시점 갱신
        except Exception as e:
            kiwoom_utils.log_error(f"⚠️ 장중 스캔 중 오류: {e}")
    return last_scan_time


def handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback):
    if code in alerted_stocks: return

    ai_prob = stock.get('prob', TRADING_RULES['SNIPER_AGGRESSIVE_PROB'])
    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

    # 💡 [개선] 체결강도 허들(115) 및 매수 확정 점수(80) 연동
    strong_vpw = TRADING_RULES.get('VPW_STRONG_LIMIT', 115)
    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)

    current_vpw = ws_data.get('v_pw', 0)
    v_pw_limit = 100 if ai_prob >= TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8) else strong_vpw
    is_shooting = current_vpw >= v_pw_limit

    # 💡 [핵심 방어선] 점수가 아무리 높아도, 현재 체결강도가 103 미만이면 절대 쏘지 않습니다!
    if (score >= buy_threshold or is_shooting) and current_vpw >= 103:
        msg = (f"🚀 **[{stock['name']}]({code}) 스나이퍼 포착!**\n"
               f"현재가: `{p['curr']:,}원` | 확신도: `{ai_prob:.1%}`\n"
               f"수급강도: `{ws_data.get('v_pw', 0):.1f}%` {visual}")
        broadcast_callback(msg)
        alerted_stocks.add(code)

        if not admin_id:
            print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID(ADMIN_ID)가 없어 주문을 패스합니다.")
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN, config=CONF)
        real_buy_qty = kiwoom_orders.calc_buy_qty(p['curr'], deposit, code, KIWOOM_TOKEN,
                                                  ratio=TRADING_RULES['BUY_RATIO'])
        if real_buy_qty <= 0:
            print(f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다.")
            return

        res = kiwoom_orders.send_buy_order_market(code, real_buy_qty, KIWOOM_TOKEN, config=CONF)

        is_success = False
        ord_no = ''

        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                err_msg = res.get('return_msg', '사유 없음')
                print(f"❌ [주문거절] {stock['name']} 서버 거절: {err_msg} ({res})")
        elif res:
            is_success = True

        if is_success:
            kiwoom_utils.log_error(f"💰 [주문접수] {stock['name']} {real_buy_qty}주 (최유리지정가)", config=CONF)

            stock.update({
                'status': 'PENDING',
                'buy_price': p['curr'],
                'buy_qty': real_buy_qty,
                'odno': ord_no,
                'order_time': time.time()
            })
            highest_prices[code] = p['curr']

            update_stock_status(
                code=code,
                status='PENDING',
                buy_price=p['curr'],
                buy_qty=real_buy_qty,
                buy_time=datetime.now().strftime('%H:%M:%S')
            )
        else:
            print(f"❌ [주문실패] {stock['name']} 응답값 이상: {res}")


def handle_holding_state(stock, code, ws_data, admin_id, broadcast_callback, market_regime):
    pos_tag = stock.get('position_tag', 'MIDDLE')

    if pos_tag == 'BREAKOUT':
        current_stop_loss = TRADING_RULES['STOP_LOSS_BREAKOUT']
        regime_name = "전고점 돌파 시도"
    elif pos_tag == 'BOTTOM':
        current_stop_loss = TRADING_RULES['STOP_LOSS_BOTTOM']
        regime_name = "바닥 탈출 구간"
    else:
        current_stop_loss = TRADING_RULES['STOP_LOSS_BULL'] if market_regime == 'BULL' else TRADING_RULES['STOP_LOSS_BEAR']
        regime_name = "상승장" if market_regime == 'BULL' else "조정장"

    curr_p = ws_data['curr']
    buy_p = stock.get('buy_price', 0)
    if buy_p <= 0: return

    if code not in highest_prices: highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)

    profit_rate = (curr_p - buy_p) / buy_p * 100
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100

    is_sell_signal = False
    reason = ""

    # 1. 영업일 기준 3일 만료 강제 청산
    try:
        buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
        buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
        today_date = datetime.now().date()

        hold_days = np.busday_count(buy_date, today_date)
        if hold_days >= TRADING_RULES['HOLDING_DAYS']:
            is_sell_signal = True
            reason = f"⏳ {TRADING_RULES['HOLDING_DAYS']}일 단기스윙 보유기간 만료 (시간 청산)"
    except Exception as e:
        print(f"⚠️ 날짜 계산 오류: {e}")

    # 2. constants.py 기반 트레일링 스탑 적용
    if not is_sell_signal and peak_profit >= TRADING_RULES['TRAILING_START_PCT']:
        drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
        if drawdown >= TRADING_RULES['TRAILING_DRAWDOWN_PCT']:
            is_sell_signal = True
            reason = f"🏆 가변익절 (+{TRADING_RULES['TRAILING_START_PCT']}% 도달 후 하락)"
        elif profit_rate <= TRADING_RULES['MIN_PROFIT_PRESERVE']:
            is_sell_signal = True
            reason = f"익절 수익 보존 (최소 {TRADING_RULES['MIN_PROFIT_PRESERVE']}%)"

    # 3. constants.py 기반 손절선 적용
    elif not is_sell_signal and profit_rate <= current_stop_loss:
        is_sell_signal = True
        reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"

    if is_sell_signal:
        sign = "🎊 [익절]" if profit_rate > 0 else "📉 [손절]"
        msg = (f"{sign} **{stock['name']} 트래킹 종료**\n사유: `{reason}`\n"
               f"최종 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)")
        broadcast_callback(msg)

        if admin_id and stock.get('buy_qty', 0) > 0:
            kiwoom_orders.send_sell_order_market(code, stock['buy_qty'], KIWOOM_TOKEN, config=CONF)

        stock['status'] = 'COMPLETED'
        highest_prices.pop(code, None)
        update_stock_status(code, 'COMPLETED')

def handle_pending_state(stock, code):
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time

    # 💡 [개선] 30초 하드코딩 제거
    timeout_sec = TRADING_RULES.get('ORDER_TIMEOUT_SEC', 30)

    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 주문 {timeout_sec}초 경과. 미체결 물량(최유리지정가) 취소를 시도합니다.")

        orig_ord_no = stock.get('odno')
        if not orig_ord_no:
            print(f"❌ [{stock['name']}] 원주문번호가 없어 취소를 진행할 수 없습니다. 감시 모드로 복귀합니다.")
            stock['status'] = 'WATCHING'
            return

        res = kiwoom_orders.send_cancel_order(
            code=code,
            orig_ord_no=orig_ord_no,
            token=KIWOOM_TOKEN,
            qty=0,
            config=CONF
        )

        if res:
            kiwoom_utils.log_error(f"🔄 [{stock['name']}] 미체결 잔량 취소 완료. 다시 타점을 감시합니다.", config=CONF)
            stock['status'] = 'WATCHING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            highest_prices.pop(code, None)
            update_stock_status(code, 'WATCHING', buy_price=0, buy_qty=0, buy_time='')
        else:
            kiwoom_utils.log_error(f"ℹ️ [{stock['name']}] 취소 실패 (이미 전량 체결 예상). 매도 감시(HOLDING)를 시작합니다.", config=CONF)
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
    print(f"🔫 스나이퍼 V12.1 가동 (관리자 ID: {admin_id})")

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

    current_market_regime = kiwoom_utils.get_market_regime(KIWOOM_TOKEN)
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다. 맞춤형 손절이 적용됩니다.")

    target_codes = [t['code'] for t in targets]
    WS_MANAGER.subscribe([c for c in target_codes])
    last_msg_min = -1

    try:
        while True:
            now = datetime.now()
            now_t = now.time()

            if now_t >= datetime.strptime("15:30:00", "%H:%M:%S").time():
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                break

            last_scan_time = check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback)

            if now_t.minute != last_msg_min:
                watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
                holding_count = len([t for t in targets if t['status'] == 'HOLDING'])
                current_time_str = now.strftime('%H:%M:%S')
                print(f"💓 [{current_time_str}] 엔진 가동 중... (감시: {watching_count} / 보유: {holding_count})")
                last_msg_min = now_t.minute

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
        print("\n🛑 엔진 종료")