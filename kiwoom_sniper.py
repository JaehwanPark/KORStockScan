import time
import sqlite3
import pandas as pd
import json
import requests
import threading
from datetime import datetime
import kiwoom_utils
from kiwoom_websocket import KiwoomWSManager

# --- [1. 전역 설정 및 변수] ---
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

CONF = load_config()
TOKEN_LOCK = threading.Lock()
KIWOOM_TOKEN = None
WS_MANAGER = None  # 웹소켓 매니저 전역 객체

# --- [공통: 메시지 전송 및 DB 상태 업데이트 함수] ---
def send_msg(chat_id, text):
    bot_token = CONF.get('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    try: requests.post(url, json=payload)
    except: pass

def update_stock_status(code, status):
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        conn.execute("UPDATE recommendation_history SET status=? WHERE code=? AND date=?", 
                     (status, code, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB 업데이트 실패: {e}")

def get_active_targets():
    """오늘 날짜의 타겟 종목과 이전부터 HOLDING 중인 스윙 종목 조회"""
    targets = []
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        today = datetime.now().strftime('%Y-%m-%d')
        # WATCHING(오늘 감시 대상) + HOLDING(보유 중 추적 대상)
        query = "SELECT code, name, type, status, buy_price FROM recommendation_history WHERE date=? OR status='HOLDING'"
        df = pd.read_sql(query, conn, params=(today,))
        conn.close()
        for _, row in df.iterrows():
            targets.append(row.to_dict())
    except: pass
    return targets

# --- [2. 텔레그램 명령 리스너 쓰레드] ---
def telegram_listener():
    global KIWOOM_TOKEN, WS_MANAGER
    last_update_id = 0
    bot_token = CONF.get('TELEGRAM_TOKEN')
    
    print("🤖 [Bot] 텔레그램 스윙 비서 가동 중...")

    while True:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            params = {'offset': last_update_id + 1, 'timeout': 30}
            response = requests.get(url, params=params, timeout=35).json()

            for update in response.get('result', []):
                last_update_id = update['update_id']
                if 'message' not in update or 'text' not in update['message']: continue

                text = update['message']['text']
                chat_id = update['message']['chat']['id']

                # --- [/분석 명령어: 실시간 즉석 분석] ---
                if text.startswith('/분석'):
                    parts = text.split(' ')
                    code = parts[1] if len(parts) > 1 else None
                    if not code:
                        send_msg(chat_id, "❓ 분석할 종목코드를 입력해주세요. (예: /분석 005930)")
                        continue

                    # 1. 즉시 웹소켓 실시간 데이터 구독 요청
                    if WS_MANAGER:
                        WS_MANAGER.subscribe([code])

                    with TOKEN_LOCK:
                        # 2. [수정됨] POST 방식으로 변경된 ka10001 함수 정상 호출
                        stock_name = kiwoom_utils.get_stock_name_ka10001(code, KIWOOM_TOKEN)
                    
                    # 3. 웹소켓 메모리에서 최신 데이터(0B, 0D 통합) 가져오기
                    ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
                    
                    # 데이터 수신 대기 방어 로직
                    if not ws_data or ws_data.get('curr', 0) == 0:
                        send_msg(chat_id, f"⏳ **{stock_name}**({code}) 실시간 데이터 수신 대기 중입니다. 잠시 후 다시 시도해주세요.")
                        continue

                    # 4. 통합 분석 함수 호출
                    score, details, visual, p = kiwoom_utils.analyze_signal_integrated(ws_data, 0.5)
                    
                    report = (
                        f"🔍 *[{stock_name}] 실시간 분석*\n"
                        f"💰 현재가: `{p['curr']:,}원`\n"
                        f"--------------------------\n"
                        f"{visual}"
                        f"🎯 목표가: `{p['sell']:,}원`\n"
                        f"📝 확신지수: `{score:.1f}점`\n"
                        f"상세: {details}"
                    )
                    send_msg(chat_id, report)
                
        except Exception as e:
            time.sleep(1)

# --- [3. 메인 스나이퍼 (실시간 감시 루프)] ---
def run_sniper():
    global KIWOOM_TOKEN, WS_MANAGER
    print(f"🚀 [Sniper v14.0] 100% 웹소켓 실시간 모드 가동...")

    with TOKEN_LOCK:
        KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN: return

    # 1. 웹소켓 매니저 시작
    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)
    WS_MANAGER.start()

    # 2. 텔레그램 봇 시작
    threading.Thread(target=telegram_listener, daemon=True).start()
    alerted_stocks = set()

    try:
        while True:
            # 장 운영 시간 체크 로직 (예: 09:00 ~ 15:30) 추가 가능
            
            targets = get_active_targets()
            
            # 3. 현재 감시 대상 종목들을 웹소켓 서버에 일괄 구독(REG) 신청
            if WS_MANAGER and targets:
                WS_MANAGER.subscribe([t['code'] for t in targets])

            for stock in targets:
                code, name, status = stock['code'], stock['name'], stock['status']
                
                # 4. HTTP 요청 없이 메모리에서 실시간 통합 데이터 즉시 읽기
                ws_data = WS_MANAGER.get_latest_data(code)
                
                # 데이터 수신 전이면 다음 종목으로 패스
                if not ws_data or ws_data.get('curr', 0) == 0:
                    continue
                
                # --- [Case A: 신규 진입 감시 (WATCHING -> HOLDING)] ---
                if status != 'HOLDING':
                    if code in alerted_stocks: continue
                    
                    prob = 0.7 if stock['type'] == 'MAIN' else 0.6
                    score, details, visual, p = kiwoom_utils.analyze_signal_integrated(ws_data, prob)
                    
                    threshold = 70 if stock['type'] == 'MAIN' else 85
                    
                    # 체결강도 기반 슈팅 감지
                    v_pw = ws_data.get('v_pw', 0.0)
                    is_shooting = v_pw >= 150

                    if score >= threshold or is_shooting:
                        reason = "🚀 수급 슈팅" if is_shooting and score < threshold else "✅ 확신 지수 도달"
                        msg = (f"🎯 *[매수 신호 포착]*\n"
                               f"종목: *{name}* ({code})\n"
                               f"현재가: `{p['curr']:,}원`\n" 
                               f"판정: `{reason}` (지수: {score:.1f}점)\n"
                               f"{visual}\n"
                               f"📢 스윙 모드 추적을 시작합니다.")
                        for cid in CONF.get('CHAT_IDS', []): send_msg(cid, msg)
                        
                        update_stock_status(code, 'HOLDING')
                        alerted_stocks.add(code)

                # --- [Case B: 보유 종목 수익률 감시 (HOLDING -> COMPLETED)] ---
                else:
                    curr_p = ws_data.get('curr', 0)
                    buy_p = stock.get('buy_price', curr_p) # DB에 저장된 매수가
                    
                    if buy_p > 0 and curr_p > 0:
                        profit_rate = (curr_p - buy_p) / buy_p * 100
                        
                        # 예시: +3% 익절 또는 -3% 손절 도달 시 알림 및 감시 종료
                        if profit_rate >= 3.0 or profit_rate <= -3.0:
                            sign = "💰 [익절]" if profit_rate > 0 else "🛡️ [손절]"
                            msg = (f"{sign} **{name}**\n"
                                   f"현재 수익률: `{profit_rate:+.1f}%`\n"
                                   f"현재가: `{curr_p:,}원` (매수가: `{buy_p:,}원`)\n"
                                   f"자동 감시를 종료합니다.")
                            for cid in CONF.get('CHAT_IDS', []): send_msg(cid, msg)
                            
                            update_stock_status(code, 'COMPLETED')

            # HTTP 요청이 없으므로 루프 간격을 매우 짧게(0.1~0.5초) 가져갈 수 있습니다.
            time.sleep(0.5) 
            
    except Exception as e:
        print(f"🚨 스나이퍼 루프 에러 발생: {e}")

if __name__ == "__main__":
    run_sniper()