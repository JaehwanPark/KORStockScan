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
from bot_main import broadcast_alert # 💡 제미나이 판단결과 텔레그램 수신용
from ai_engine import GeminiSniperEngine # 💡 새로 만든 두뇌 파일 임포트

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
global ACTIVE_TARGETS
ACTIVE_TARGETS = []
LAST_AI_CALL_TIMES = {}
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

def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다."""
    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")
    
    # 💡 [교정 1] 전역 변수와 이미 임포트된 모듈을 직접 사용합니다.
    real_inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN, CONF) 
    
    # 🚨 [방어막 1] API 통신 실패 시 (None 반환 등) DB 강제 초기화 대참사 방지
    if real_inventory is None:
        print("⚠️ [동기화 보류] 잔고 조회 API 통신에 실패하여 DB 동기화를 건너뜁니다.")
        return

    real_codes = {item['code']: item for item in real_inventory}

    # 💡 [교정 2] 전역 인스턴스인 DB.execute_query를 사용합니다.
    db_holdings = DB.execute_query(
        "SELECT code, name, buy_qty FROM recommendation_history WHERE status = 'HOLDING'"
    ) 
    
    if not db_holdings:
        db_holdings = []

    # 3. 대조 및 강제 교정 시작
    for row in db_holdings:
        code, name, db_qty = row[0], row[1], row[2]
        
        # 🚨 [방어막 2] db_qty가 비어있거나 NULL일 경우 다운되는 현상 방지
        try:
            safe_db_qty = int(db_qty) if db_qty else 0
        except ValueError:
            safe_db_qty = 0
            
        if code not in real_codes:
            # 실제 계좌에 없다면? 이미 팔았는데 DB만 쥐고 있는 상태!
            print(f"⚠️ [동기화] {name}({code}): 실제 잔고 0주. 상태를 COMPLETED로 강제 변경.")
            DB.execute_query(
                "UPDATE recommendation_history SET status = 'COMPLETED' WHERE code = ? AND status = 'HOLDING'", 
                (code,)
            )
        else:
            # 계좌에 있는데 수량이 다르다면? (수동 매도, 혹은 이전 에러로 인한 누락)
            real_qty = real_codes[code]['qty']
            if safe_db_qty != real_qty:
                print(f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)")
                DB.execute_query(
                    "UPDATE recommendation_history SET buy_qty = ? WHERE code = ? AND status = 'HOLDING'", 
                    (real_qty, code)
                )

    print("✅ [데이터 동기화] 완료. 봇 메모리가 실제 계좌와 완벽히 일치합니다.")

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

# ==========================================
# 💡 실시간 체결 영수증 처리 (콜백 함수)
# ==========================================
def handle_real_execution(exec_data):
    """
    웹소켓에서 주문 체결(00) 통보가 오면 이 함수가 즉시 실행됩니다.
    실제 체결가를 DB에 덮어쓰고, 스나이퍼의 메모리를 변경합니다.
    """
    code = exec_data['code']
    exec_type = exec_data['type']
    exec_price = exec_data['price']
    
    db = DBManager()
    now_t = datetime.now().time()
    
    # ==========================================
    # 1️⃣ DB 상태 업데이트 (영구 기록)
    # ==========================================
    if exec_type == 'BUY':
        # 🎯 실제 매수 체결: 정확한 단가(buy_price)를 적고 '보유(HOLDING)' 상태로 전환!
        query = """
            UPDATE recommendation_history 
            SET buy_price = ?, status = 'HOLDING' 
            WHERE code = ? AND status IN ('WATCHING', 'BUY_ORDERED')
        """
        db.execute_query(query, (exec_price, code))
        print(f"✅ [영수증 확인] {code} 실제 매수 체결가 {exec_price:,}원 DB 반영 완료!")
        
    elif exec_type == 'SELL':
        # 🏁 실제 매도 체결: 기존 buy_price를 가져와서 정확한 수익률을 계산
        try:
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT buy_price FROM recommendation_history WHERE code = ? AND status IN ('HOLDING', 'SELL_ORDERED')", (code,))
                row = cursor.fetchone()
                
                if row and row[0] > 0:
                    buy_price = row[0]
                    # 실제 수익률 계산 (슬리피지 모두 반영됨)
                    profit_rate = round(((exec_price - buy_price) / buy_price) * 100, 2)

                    cursor.execute("SELECT strategy FROM recommendation_history WHERE code = ?", (code,))
                    strategy_row = cursor.fetchone()
                    
                    # 💡 [핵심 1] 무조건 현재 매매 사이클은 'COMPLETED'로 쾅 닫아서 기록을 영구 보존합니다!
                    db.update_sell_record(code, exec_price, profit_rate, status='COMPLETED')
                    print(f"🎉 [매매 완료] {code} 실매도가 {exec_price:,}원 / 최종 수익률: {profit_rate}% (기록 보존 완료)")

                    # 💡 [핵심 2] 스캘핑 부활 조건이 맞으면, 덮어쓰지 않고 '새로운 줄'을 만들어냅니다.
                    is_scalp_revive = (strategy_row and strategy_row[0] == 'SCALPING') and (now_t < datetime.strptime("15:15:00", "%H:%M:%S").time())
                    if is_scalp_revive:
                        today = datetime.now().strftime('%Y-%m-%d')
                        stock_info = next((s for s in ACTIVE_TARGETS if s['code'] == code), None)
                        
                        if stock_info:
                            name = stock_info.get('name', code)
                            prob = stock_info.get('prob', 0.8)
                            
                            # 완전히 새로운 WATCHING 레코드를 INSERT 합니다.
                            insert_query = """
                                INSERT INTO recommendation_history 
                                (date, code, name, status, strategy, prob)
                                VALUES (?, ?, ?, 'WATCHING', 'SCALPING', ?)
                            """
                            db.execute_query(insert_query, (today, code, name, prob))
                            print(f"♻️ [스캘핑 재진입 준비] {name}({code}) 새로운 매매를 위해 DB에 신규 감시(WATCHING) 등록!")

        except Exception as e:
            print(f"🚨 매도 체결 영수증 처리 중 에러: {e}")

    # ==========================================
    # 2️⃣ 스나이퍼 메모리(ACTIVE_TARGETS) 즉시 동기화
    # ==========================================
    # 💡 [핵심 교정] if exec_type == 'BUY': 밖으로 빼서 무조건 실행되게 함!
    
    for stock in ACTIVE_TARGETS:
        if stock['code'] == code:
            if exec_type == 'BUY':
                stock['status'] = 'HOLDING'
                stock['buy_price'] = exec_price  # 🎯 진짜 체결가로 메모리 업데이트!
            
            elif exec_type == 'SELL':
                strategy = stock.get('strategy', 'KOSPI_ML')
                
                # 스캘핑 부활 조건 검사 (DB 로직과 동일)
                if strategy == 'SCALPING' and now_t < datetime.strptime("15:15:00", "%H:%M:%S").time():
                    stock['status'] = 'WATCHING'
                    stock['buy_price'] = 0
                    stock['buy_qty'] = 0
                else:
                    stock['status'] = 'COMPLETED'
            break
        

def handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback, radar=None, ai_engine=None):
    
    strategy = stock.get('strategy', 'KOSPI_ML')
    now_t = datetime.now().time()
    db = DBManager()
    # 💡 [핵심] TRADING_RULES 딕셔너리에서 MIN_PRICE 값을 안전하게 가져옵니다.
    MIN_PRICE = TRADING_RULES.get('MIN_PRICE', 5000)
    MAX_SURGE = TRADING_RULES.get('MAX_SCALP_SURGE_PCT', 20.0) 
    MAX_INTRADAY_SURGE = TRADING_RULES.get('MAX_INTRADAY_SURGE', 15.0)

    MIN_LIQUIDITY = TRADING_RULES.get('MIN_SCALP_LIQUIDITY', 300_000_000)

    # 🚀 1. 쿨타임(휴식기) 검사
    if code in cooldowns and time.time() < cooldowns[code]:
        return  # 아직 쿨타임이 안 지났으면 무시

    # 🚀 2. 초단타 장 후반 진입 금지 (15:00 이후에는 새로 사지 않음)
    if strategy == 'SCALPING' and now_t >= datetime.strptime("15:00:00", "%H:%M:%S").time():
        return

    if code in alerted_stocks: return

    curr_price = ws_data.get('curr', 0)
    current_vpw = ws_data.get('v_pw', 0)

    # ==========================================
    # 🚨 3. 실시간 동전주/저가주 컷오프 (MIN_PRICE 방어막)
    # ==========================================
    if 0 < curr_price < MIN_PRICE:
        # 💡 [정확한 코드] 60초(1분)에 딱 1번만 터미널에 보고하고 매수 로직을 차단합니다.
        if time.time() % 60 < 1: 
            print(f"🚫 [저가주 방어] {stock['name']} 현재가 {curr_price:,}원. (5,000원 미만 진입 금지)")
        return 
    # ==========================================

    is_trigger = False
    msg = ""
    ratio = 0.10  # 💡 [안전장치] 만약을 대비한 기본 비중 선언 (10%)

    ai_prob = stock.get('prob', TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70))
    buy_threshold = TRADING_RULES.get('BUY_SCORE_THRESHOLD', 80)
    strong_vpw = TRADING_RULES.get('VPW_STRONG_LIMIT', 120)

    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':
        ratio = TRADING_RULES.get('INVEST_RATIO_SCALPING', 0.05)
        
        # 💡 [데이터 확인] 웹소켓 데이터가 정상인지 먼저 체크
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        curr_price = ws_data.get('curr', 0)
        current_vpw = ws_data.get('v_pw', 0)
        fluctuation = float(ws_data.get('fluctuation', 0.0)) # 💡 등락률 가져오기
        open_price = float(ws_data.get('open', curr_price))

        # 당일 시가 대비 등락률
        if open_price > 0:
            intraday_surge = ((curr_price - open_price) / open_price) * 100
        else:
            intraday_surge = fluctuation
        
        liquidity_value = (ask_tot + bid_tot) * curr_price

        # ==========================================
        # 🚨 [완벽해진 이중 방어막 적용]
        # 전일 대비로는 20%까지 넓게 허용해주되, 당일 시가 대비 15% 이상 치솟은 종목은 매수 금지!
        # ==========================================
        if fluctuation >= MAX_SURGE or intraday_surge >= MAX_INTRADAY_SURGE:
            if time.time() % 60 < 1: # 터미널 도배 방지 (1분에 1회 출력)
                print(f"🚫 [SCALP 제외] {stock['name']} | 전일대비: +{fluctuation}%, 시가대비: +{intraday_surge:.1f}% (과매수 위험)")
            return # 즉시 함수를 종료하여 매수 프로세스 차단
        
        if current_vpw >= TRADING_RULES.get('VPW_SCALP_LIMIT', 120) and liquidity_value >= MIN_LIQUIDITY:
            scanner_price = stock.get('buy_price', 0)
            if scanner_price > 0:
                gap_pct = (curr_price - scanner_price) / scanner_price * 100
                if gap_pct >= 1.5: # 1.5% 이상 오르면 추격매수 포기
                    if code not in cooldowns:
                        print(f"⚠️ [{stock['name']}] 포착가 대비 너무 오름 (갭 +{gap_pct:.1f}%). 추격매수 포기 및 쿨타임 진입.")
                        cooldowns[code] = time.time() + 1200
                    return
                
            # =========================================================
            # 🤖 [섀도우 모드] 제미나이 판단 및 텔레그램 콜백 전송
            # =========================================================
            global LAST_AI_CALL_TIMES
            last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
            
            # 엔진과 레이더가 정상적으로 넘어왔고, 종목당 3초 쿨타임이 지났을 때만 실행
            if ai_engine and radar and (time.time() - last_ai_time > 3.0):
                
                # 1. 틱 데이터 수집
                recent_ticks = radar.get_tick_history_ka10003(code, limit=10)
                
                if ws_data.get('orderbook') and recent_ticks:
                    # 2. AI 두뇌 호출 (넘겨받은 ai_engine 인스턴스 사용)
                    ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks)
                    
                    action = ai_decision.get('action', 'WAIT')
                    reason = ai_decision.get('reason', '사유 없음')
                    
                    print(f"🤖 [AI 섀도우 모드: {stock['name']}] {action} | {reason}")
                    
                    if action in ["BUY", "DROP"]:
                        ai_msg = f"🤖 <b>[AI 스나이퍼 모의판단]</b>\n"
                        ai_msg += f"🎯 종목: {stock['name']}\n"
                        ai_msg += f"⚡ 행동: <b>{action}</b>\n"
                        ai_msg += f"🧠 사유: {reason}"
                        
                        # 3. 어드민에게만 발송
                        try:
                            broadcast_callback(ai_msg, audience='ADMIN_ONLY', parse_mode='HTML')
                        except Exception as e:
                            print(f"AI 알림 발송 실패: {e}")
                            
                    # 마지막 호출 시간 기록
                    LAST_AI_CALL_TIMES[code] = time.time()
            # =========================================================

            target_buy_price = kiwoom_utils.get_target_price_by_percent(curr_price, drop_percent=0.5)
            stock['target_buy_price'] = target_buy_price

            is_trigger = True
            msg = (f"⚡ **[{stock['name']}]({code}) 초단타(SCALP) 그물망 투척!**\n"
                   f"현재가: `{curr_price:,}원` ➡️ **매수대기: `{target_buy_price:,}원` (-0.5% 눌림목)**\n"
                   f"호가잔량대금: `{liquidity_value / 100_000_000:.1f}억` | 수급강도: `{current_vpw:.1f}%`")
            
            # 💡 [핵심 추가] 매수 로직과 별개로, 텔레그램 발송용 타겟 오디언스 꼬리표를 붙입니다.
            # 호가잔량이 5억(500,000,000) 이상이면 VIP 포함 전체 발송, 미만이면 ADMIN 전용으로 분류
            stock['msg_audience'] = 'VIP_ALL' if liquidity_value >= TRADING_RULES.get('VIP_LIQUIDITY_THRESHOLD', 500_000_000) else 'ADMIN_ONLY'

    # 2️⃣ 코스닥 우량주 스윙 (KOSDAQ_ML) 전략
    elif strategy == 'KOSDAQ_ML':
        ratio = TRADING_RULES.get('INVEST_RATIO_KOSDAQ', 0.10)
        score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

        v_pw_limit = TRADING_RULES.get('VPW_KOSDAQ_LIMIT', 105) if ai_prob >= TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.70) else strong_vpw
        is_shooting = current_vpw >= v_pw_limit

        if (score >= buy_threshold or is_shooting) and current_vpw >= TRADING_RULES.get('VPW_KOSDAQ_LIMIT', 105):
            is_trigger = True
            msg = (f"🚀 **[{stock['name']}]({code}) 코스닥(KOSDAQ) 스나이퍼 포착!**\n"
                   f"현재가: `{curr_price:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{current_vpw:.1f}%` {visual}")

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        ratio = TRADING_RULES.get('INVEST_RATIO_KOSPI', 0.20)
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
        if not admin_id:
            print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID가 없습니다.")
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN, config=CONF)
        real_buy_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio)

        if real_buy_qty <= 0:
            print(f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다. (자금 부족으로 20분 제외)")
            # 💡 [교정] 0주일 때도 쿨타임을 적용해 무한 루프 차단
            cooldowns[code] = time.time() + 1200 
            return

        # 🚀 [상호 검증 반영] 전략별 주문 세팅
        if strategy == 'SCALPING':
            order_type_code = "00"  # 지정가
            final_price = stock.get('target_buy_price', curr_price)
        else:
            order_type_code = "6"  # 스윙은 최유리지정가
            final_price = 0

        # 주문 발송
        res = kiwoom_orders.send_buy_order_market(
            code=code, qty=real_buy_qty, token=KIWOOM_TOKEN,
            config=CONF, order_type=order_type_code, price=final_price
        )

        is_success = False
        ord_no = ''

        # 💡 [핵심 교정] 응답값을 정확히 분석하여 성공 여부 판단
        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                err_msg = res.get('return_msg', '사유 없음')
                print(f"❌ [주문거절] {stock['name']} 서버 거절: {err_msg}")
                if strategy == 'SCALPING':
                    cooldowns[code] = time.time() + 1200
        elif res:
            is_success = True

        # 💡 [핵심 교정] 주문이 "정상 접수" 되었을 때만 메모리와 DB 상태를 'BUY_ORDERED'로 변경!
        if is_success:
            print(f"🛒 [{stock['name']}] 매수 주문 전송 완료. 체결 영수증 대기 중...")
            # 💡 [신규 추가] 스윙 종목 등 꼬리표가 없는 애들은 기본적으로 모두(VIP_ALL)에게 보냅니다.
            audience = stock.get('msg_audience', 'VIP_ALL')
            # 콜백 함수에 발송 권한 정보를 함께 넘겨줍니다.
            broadcast_callback(msg, audience=audience)
            alerted_stocks.add(code)
            
            kiwoom_utils.log_error(f"💰 [주문접수] {stock['name']} {real_buy_qty}주 (전략: {strategy})", config=CONF)

            # 1. 메모리 업데이트 (BUY_ORDERED 통일)
            stock.update({
                'status': 'BUY_ORDERED',
                'order_price': final_price if final_price > 0 else curr_price,
                'buy_qty': real_buy_qty,
                'odno': ord_no,
                'order_time': time.time()
            })
            highest_prices[code] = curr_price

            # 2. DB 업데이트 (영수증 콜백이 찾을 수 있도록 BUY_ORDERED로 설정) [수정] AND status = 'WATCHING' 추가 하여 이미 매수 주문이 들어간 종목은 중복 업데이트 방지   
            db.execute_query(
                "UPDATE recommendation_history SET status = 'BUY_ORDERED', buy_price = ? WHERE code = ? AND status = 'WATCHING'", 
                (final_price if final_price > 0 else curr_price, code)
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

    now_t = datetime.now().time()
    db = DBManager()  # 💡 DB 매니저 로컬 인스턴스화

    # ==========================================
    # 🚀 [멀티 전략] 보유 종목 청산 분기 처리
    # ==========================================
    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':
        held_time_min = 0
        if 'order_time' in stock:
            held_time_min = (time.time() - stock['order_time']) / 60
        elif 'buy_time' in stock and stock['buy_time']:
            try:
                b_time = datetime.strptime(stock['buy_time'], '%H:%M:%S').time()
                b_dt = datetime.combine(datetime.now().date(), b_time)
                held_time_min = (datetime.now() - b_dt).total_seconds() / 60
            except:
                pass

        target_pct = TRADING_RULES.get('SCALP_TARGET', 2.0)
        stop_pct = TRADING_RULES.get('SCALP_STOP', -2.5)

        if profit_rate >= target_pct:
            is_sell_signal = True
            reason = f"⚡ 초단타 목표 수익 컷 (+{target_pct}%)"
        elif profit_rate <= stop_pct:
            is_sell_signal = True
            reason = f"🔪 초단타 무호흡 칼손절 ({stop_pct}%)"
        elif held_time_min >= TRADING_RULES['SCALP_TIME_LIMIT_MIN'] and profit_rate >= TRADING_RULES['MIN_FEE_COVER']:
            is_sell_signal = True
            reason = f"⏱️ {TRADING_RULES['SCALP_TIME_LIMIT_MIN']}분 타임아웃 (기회비용 확보용 약익절)"
        elif now_t >= datetime.strptime("15:15:00", "%H:%M:%S").time():
            is_sell_signal = True
            reason = "⏰ 초단타 오버나잇 회피 (장 마감 현금화)"

    # 2️⃣ 코스닥 AI 스윙 (KOSDAQ_ML) 전용 전략
    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= TRADING_RULES.get('KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
        except:
            pass

        if not is_sell_signal and peak_profit >= TRADING_RULES.get('KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= 1.0:
                is_sell_signal = True
                reason = f"🏆 KOSDAQ 트레일링 익절 (+{TRADING_RULES.get('KOSDAQ_TARGET', 4.0)}% 돌파 후 하락)"

        elif not is_sell_signal and profit_rate <= TRADING_RULES.get('KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({TRADING_RULES.get('KOSDAQ_STOP', -2.0)}%)"

    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 및 기본값)
    else:
        pos_tag = stock.get('position_tag', 'MIDDLE')
        if pos_tag == 'BREAKOUT':
            current_stop_loss = TRADING_RULES['STOP_LOSS_BREAKOUT']
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = TRADING_RULES['STOP_LOSS_BOTTOM']
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = TRADING_RULES['STOP_LOSS_BULL'] if market_regime == 'BULL' else TRADING_RULES['STOP_LOSS_BEAR']
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= TRADING_RULES['HOLDING_DAYS']:
                is_sell_signal = True
                reason = f"⏳ {TRADING_RULES['HOLDING_DAYS']}일 스윙 보유 만료"
        except:
            pass

        if not is_sell_signal and peak_profit >= TRADING_RULES['TRAILING_START_PCT']:
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= TRADING_RULES['TRAILING_DRAWDOWN_PCT']:
                is_sell_signal = True
                reason = f"🏆 가변익절 (+{TRADING_RULES['TRAILING_START_PCT']}% 도달 후 하락)"
            elif profit_rate <= TRADING_RULES['MIN_PROFIT_PRESERVE']:
                is_sell_signal = True
                reason = f"수익 보존 (최소 {TRADING_RULES['MIN_PROFIT_PRESERVE']}%)"

        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"

    # ==========================================
    # 🎯 매도 실행 공통 로직 (Race Condition 완벽 방지)
    # ==========================================
    if is_sell_signal:
        sign = "🎊 [익절 주문]" if profit_rate > 0 else "📉 [손절 주문]"
        msg = (f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n사유: `{reason}`\n"
               f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)")

        is_success = False
        buy_qty = stock.get('buy_qty', 0)

        # 💡 [수정] 수량이 없으면 왜 못 파는지 터미널에 고래고래 소리치게 만듭니다!
        if not admin_id:
            print(f"🚨 [매도실패] {stock['name']}: 관리자 ID(admin_id)가 설정되지 않았습니다.")
        elif int(buy_qty) <= 0:
            print(f"🚨 [매도실패] {stock['name']}: 수량이 0주입니다! 강제 완료(COMPLETED) 처리합니다.")
            db.execute_query("UPDATE recommendation_history SET status = 'COMPLETED' WHERE code = ?", (code,))
            stock['status'] = 'COMPLETED'
        else:
            # 💡 [핵심 방어 1] 주문 쏘기 전에 미리 장부(DB/메모리)를 SELL_ORDERED로 잠금! (웹소켓 레이스 방지) [수정] AND status = 'HOLDING' 추가하여 감시중 매도완료 종목 업데이트 방지
            db.execute_query("UPDATE recommendation_history SET status = 'SELL_ORDERED' WHERE code = ? AND status = 'HOLDING'", (code,))
            stock['status'] = 'SELL_ORDERED'
            try: highest_prices.pop(code, None)
            except: pass

            # 💡 [핵심 방어 2] 장부 세팅이 끝났으니 안심하고 실제 매도 전송
            res = kiwoom_orders.send_sell_order_market(code, int(buy_qty), KIWOOM_TOKEN, config=CONF)
            
            if isinstance(res, dict):
                rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
                if rt_cd == '0':
                    is_success = True
                else:
                    print(f"❌ [매도거절] {stock['name']}: {res.get('return_msg')}")
            elif res:
                is_success = True

            if is_success:
                print(f"✅ [{stock['name']}] 매도 주문 전송 완료. 체결 영수증 처리 대기 중...")
                broadcast_callback(msg)

                # 스캘핑 쿨타임 (기존 로직 유지)
                if strategy in ['SCALPING', 'SCALP'] and now_t < datetime.strptime("15:15:00", "%H:%M:%S").time():
                    cooldowns[code] = time.time() + 1200
                    try: alerted_stocks.discard(code)
                    except: pass
                    print(f"♻️ [{stock['name']}] 스캘핑 청산 완료 후 20분 쿨타임 진입.")
            else:
                # 💡 [핵심 교정] 에러 메시지를 읽고 영구 탈출(COMPLETED)할지, 복구(HOLDING)할지 결정합니다.
                err_msg = res.get('return_msg', '') if isinstance(res, dict) else ''
                
                if '매도가능수량' in err_msg:
                    print(f"🚨 [{stock['name']}] 잔고 0주(이미 매도됨). 무한루프를 막기 위해 COMPLETED로 강제 전환합니다.")
                    db.execute_query("UPDATE recommendation_history SET status = 'COMPLETED' WHERE code = ?", (code,))
                    stock['status'] = 'COMPLETED'
                else:
                    print(f"🚨 [{stock['name']}] 일시적 매도 전송 실패! 상태를 다시 HOLDING으로 원상복구합니다.")
                    db.execute_query("UPDATE recommendation_history SET status = 'HOLDING' WHERE code = ?", (code,))
                    stock['status'] = 'HOLDING'

def handle_buy_ordered_state(stock, code):
    """
    주문 전송 후(BUY_ORDERED) 일정 시간 동안 체결 영수증이 오지 않으면(미체결) 
    주문을 취소하고 상태를 되돌리거나, 체결 확정 시 HOLDING으로 넘깁니다.
    """
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time
    
    # 💡 [핵심] 스캘핑은 2호가 아래에 깔아두므로 안 사지면 빨리 취소하고 다른 종목을 찾아야 합니다.
    strategy = stock.get('strategy', 'KOSPI_ML')
    timeout_sec = 20 if strategy == 'SCALPING' else TRADING_RULES.get('ORDER_TIMEOUT_SEC', 30)

    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 매수 대기 {timeout_sec}초 초과. 미체결 물량 취소 시도.")
        orig_ord_no = stock.get('odno')
        db = DBManager()

        # 1. 원주문번호가 없는 비정상 펜딩 상태일 때의 탈출 로직
        if not orig_ord_no:
            stock['status'] = 'WATCHING'
            stock.pop('order_time', None)
            
            # DB 상태 동기화 [수정] AND status = 'BUY_ORDERED' 추가하여 이미 체결된 종목의 상태 변경 방지 
            db.execute_query("UPDATE recommendation_history SET status = 'WATCHING', buy_price = 0 WHERE code = ? AND status = 'BUY_ORDERED'", (code,))

            if strategy == 'SCALPING':
                # 여기서 alerted_stocks가 에러를 낼 수 있으므로 안전하게 처리
                try: alerted_stocks.discard(code) 
                except: pass
                cooldowns[code] = time.time() + 1200 # 20분 쿨타임
            return

        # 2. 정상적인 미체결 주문 취소 전송 (kiwoom_orders.send_cancel_order 활용)
        res = kiwoom_orders.send_cancel_order(
            code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0, config=CONF
        )

        is_success = False
        res_str = str(res) # 응답 결과를 문자열로 변환하여 에러 메시지 파악 용이하게 함

        if isinstance(res, dict):
            if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
                is_success = True
        elif res:
            is_success = True

        # 3. 취소 접수 성공 시 부활 로직 (주문이 아직 안 체결되어서 정상 취소됨)
        if is_success:
            print(f"✅ [{stock['name']}] 미체결 매수 취소 성공. 감시 상태로 복귀합니다.")
            stock['status'] = 'WATCHING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            try: highest_prices.pop(code, None)
            except: pass
            
            # DB 상태 동기화 [수정] AND status = 'BUY_ORDERED' 추가하여 이미 체결된 종목의 상태 변경 방지 
            db.execute_query("UPDATE recommendation_history SET status = 'WATCHING', buy_price = 0 WHERE code = ? AND status = 'BUY_ORDERED'", (code,))

            # 🚀 [초단타 부활 로직] 호가가 도망가서 취소한 경우, 추격매수 안하고 20분 대기!
            if strategy == 'SCALPING':
                try: alerted_stocks.discard(code)
                except: pass
                cooldowns[code] = time.time() + 1200
                print(f"♻️ [{stock['name']}] 스캘핑 취소 완료. 20분 쿨타임 진입.")

        # 4. 취소 실패 시 (이미 체결되었거나, 주문 상태가 변경된 경우)
        else:
            print(f"🚨 [{stock['name']}] 매수 취소 실패! (에러응답: {res_str})")
            
            # 💡 [핵심 교정] 이미 샀는데 또 취소하려고 해서 나는 에러면 강제로 HOLDING으로 넘깁니다.
            err_msg = res.get('return_msg', '') if isinstance(res, dict) else res_str
            
            if '취소가능수량' in err_msg:
                print(f"💡 [{stock['name']}] 이미 전량 체결되었을 확률이 99%입니다. 무한루프 방지를 위해 HOLDING으로 강제 전환합니다.")
                
                # 메모리와 DB를 보유 상태로 돌려 다음 루프부터 매도(익절/손절)를 감시하게 만듭니다.
                stock['status'] = 'HOLDING'
                db.execute_query("UPDATE recommendation_history SET status = 'HOLDING' WHERE code = ? AND status = 'BUY_ORDERED'", (code,))
            else:
                print(f"💡 시스템 일시 오류일 수 있으므로 상태를 유지하고 웹소켓 영수증을 대기합니다.")


# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (교통 정리 전담)
# ==============================================================================
def run_sniper(broadcast_callback):
    # 💡 전역 변수 ACTIVE_TARGETS를 선언합니다.
    global KIWOOM_TOKEN, WS_MANAGER, ACTIVE_TARGETS

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

    # 👇 [여기입니다!] 토큰 발급 직후에 동기화를 먼저 싹 돌립니다.
    sync_balance_with_db()
    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN, on_execution_callback=handle_real_execution)
    WS_MANAGER.start()
    time.sleep(2)

    # ==========================================
    # 🤖 [신규] 제미나이 엔진 가동
    # ==========================================
    api_key = CONF.get('GEMINI_API_KEY')
    if api_key:
        ai_engine = GeminiSniperEngine(api_key=api_key)
    else:
        ai_engine = None
        print("⚠️ 설정에 GEMINI_API_KEY가 없어 AI 섀도우 모드가 꺼집니다.")

    # 💡 DB에서 가져온 타겟을 전역 변수에 연결합니다.
    ACTIVE_TARGETS = get_active_targets()
    targets = ACTIVE_TARGETS  # targets는 ACTIVE_TARGETS의 별칭이 되어 동기화됨
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

            # 🚀 2. [신규 추가] 5초마다 외부(초단타 스캐너 등)에서 DB에 새로 넣은 종목이 있는지 확인
            if time.time() - last_db_poll_time > 5:
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
                if not ws_data or ws_data.get('curr', 0) == 0: 
                    # 1분에 한 번 정도만 출력되게 하거나, 특정 종목 하나만 지정해서 확인 (디버깅용)
                    #if time.time() % 60 < 1: 
                    #    print(f"❓ [{stock['name']}] 데이터를 기다리는 중... (현재가: {ws_data.get('curr')})")
                    continue

                if status == 'WATCHING':
                    handle_watching_state(
                        stock, 
                        code, 
                        ws_data, 
                        admin_id, 
                        broadcast_alert, 
                        radar=radar,         # 🚀 추가
                        ai_engine=ai_engine  # 🚀 추가
                    )
                elif status == 'HOLDING':
                    handle_holding_state(
                        stock, 
                        code, 
                        ws_data, 
                        admin_id, 
                        broadcast_callback, 
                        current_market_regime
                    )
                
                # 👇 [수정] PENDING 대신 BUY_ORDERED 로 확인하고, 방금 만든 새 함수를 호출합니다!
                elif status == 'BUY_ORDERED':
                    handle_buy_ordered_state(stock, code)

            time.sleep(1)

    except Exception as e:
        kiwoom_utils.log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}", config=CONF, send_telegram=True)

    except KeyboardInterrupt:
        print("\n🛑 스나이퍼 매매 엔진 종료")