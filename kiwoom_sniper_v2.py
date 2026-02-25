import time
import sqlite3
import pandas as pd
import json
import requests
import threading
from datetime import datetime
import kiwoom_utils
import kiwoom_orders
from kiwoom_websocket import KiwoomWSManager
from google_sheets_utils import GoogleSheetsManager

# ✅ [복구] 실제 주문을 위한 라이브러리 임포트
from kiwoom_orders import send_buy_order_market, calc_buy_qty, get_deposit, send_sell_order_market

# --- [1. 전역 설정 및 변수] ---
def load_config():
    with open('config_prod.json', 'r', encoding='utf-8') as f:
        return json.load(f)

CONF = load_config()
KIWOOM_TOKEN = None
WS_MANAGER = None  # 웹소켓 매니저 전역 객체
SHEET_MANAGER = GoogleSheetsManager('credentials.json', 'KOSPIScanner')

# 👇 여기에 새로고침 함수 추가 👇
def reload_config():
    global CONF
    try:
        CONF = load_config()
        print("✅ JSON 설정 파일이 새로고침 되었습니다!")
        return True
    except Exception as e:
        print(f"❌ 설정 새로고침 실패 (JSON 문법 오류일 수 있음): {e}")
        return False

# 💡 관리자(님) 한 명에게만 주문 결과를 귓속말하는 함수
def send_admin_msg(text):
    admin_id = CONF.get('ADMIN_ID')
    if not admin_id: return
    
    bot_token = CONF.get('TELEGRAM_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': admin_id, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ 관리자 메시지 전송 실패: {e}")

# --- [공통: 상태 업데이트 함수] ---
def update_stock_status(code, status, buy_price=None, buy_qty=None, buy_time=None):
    """DB 상태 업데이트 (가상 트래킹 및 실제 매수 수량 기록)"""
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        today = datetime.now().strftime('%Y-%m-%d')
        nxt = kiwoom_utils.get_stock_market_ka10100(code, KIWOOM_TOKEN)
        
        if buy_price and buy_qty and buy_time:
            conn.execute("UPDATE recommendation_history SET status=?, buy_price=?, buy_qty=?, buy_time=?, nxt=? WHERE code=? AND date=?", 
                        (status, buy_price, buy_qty, buy_time, nxt, code, today))
        else:
            conn.execute("UPDATE recommendation_history SET status=?, nxt=? WHERE date=? AND code=?", 
                        (status, nxt, today, code))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ DB 업데이트 실패: {e}")

def get_active_targets():
    """감시 대상 종목 조회 (매매를 위해 수량과 시간까지 가져옵니다)"""
    targets = []
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        today = datetime.now().strftime('%Y-%m-%d')
        # buy_qty, buy_time을 추가로 SELECT 합니다.
        query = "SELECT code, name, type, status, buy_price, buy_qty, buy_time FROM recommendation_history WHERE date=? OR status='HOLDING'"
        df = pd.read_sql(query, conn, params=(today,))
        conn.close()
        return df.to_dict('records')
    except: pass
    return targets

# --- [2. 외부 요청용 실시간 분석 함수] ---
def analyze_stock_now(code):
    global KIWOOM_TOKEN, WS_MANAGER
    if not WS_MANAGER: return "⏳ 시스템 초기화 중..."
    
    WS_MANAGER.subscribe([code])
    stock_name = kiwoom_utils.get_stock_name_ka10001(code, KIWOOM_TOKEN)
    
    ws_data = {}
    for _ in range(30):
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        if ws_data and ws_data.get('curr', 0) > 0: break
        time.sleep(0.1)
        
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ **{stock_name}**({code}) 데이터 수신 대기 중..."

    score, details, visual, p, conclusion = kiwoom_utils.analyze_signal_integrated(ws_data, 0.5, 70)
    return (f"🔍 *[{stock_name}]({code}) 실시간 분석*\n💰 현재가: `{p['curr']:,}원`\n{visual}\n🎯 목표가: `{p['sell']:,}원` (+3%)\n📝 확신지수: `{score:.1f}점`\n{conclusion}")

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
    
    report += f"━━━━━━━━━━━━━━━━━━\n"
    report += f"🎯 **종합 점수:** `{int(score)}점` (매수기준: 80점)\n"
    report += f"📝 **현재 상태:** {conclusion}\n"
    report += f"\n💡 *TIP: 모든 항목이 ✅이고 점수가 80점 이상일 때 자동으로 매수 주문이 집행됩니다.*"
    
    return report

# --- [3. 메인 스나이퍼 엔진] ---
def run_sniper(broadcast_callback):
    global KIWOOM_TOKEN, WS_MANAGER
    
    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V2 가동 (관리자 ID: {admin_id})")
    
    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        print("❌ 토큰 발급 실패.")
        return

    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)
    WS_MANAGER.start()
    time.sleep(2) 
    
    targets = get_active_targets()
    if not targets:
        print("💤 오늘 감시할 종목이 없습니다.")
        return

    target_codes = [t['code'] for t in targets]
    WS_MANAGER.subscribe(target_codes)
    alerted_stocks = set()
    last_msg_min = -1

    try:
        while True:
            now_t = datetime.now().time()
            # 장 마감 시간 체크 
            if datetime.now().time() >= datetime.strptime("20:00:00", "%H:%M:%S").time():
                print("🌙 장이 마감되었습니다.")
                break
            
            if now_t.minute != last_msg_min:
                # 메모리에 있는 targets 리스트 중 상태가 'WATCHING'인 것만 카운트
                watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
                current_time_str = datetime.now().strftime('%H:%M:%S')
                print(f"💓 [{current_time_str}] 스나이퍼 엔진 정상 가동 중... (감시 대기: {watching_count}개 종목)")
                last_msg_min = now_t.minute
            
            for stock in targets:
                code = stock['code']
                name = stock['name']
                status = stock['status']
                
                ws_data = WS_MANAGER.get_latest_data(code)
                if not ws_data or ws_data.get('curr', 0) == 0: continue

                # ========================================================
                # [Case A] 신규 진입 포착 (알림 + 관리자 실제 매수)
                # ========================================================
                if status == 'WATCHING' and code not in alerted_stocks:
                    
                    # 🚀 [v12.1] AI 확신도가 이미 극도로 높으므로, 실시간 수급 허들을 살짝 낮춰 체결 우선
                    ai_prob = 0.75 
                    threshold = 80 
                    
                    # 🚀 6번째 인자인 checklist를 추가로 받도록 수정 (변수명 뒤에 , checklist 추가)
                    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

                    # Scanner가 넘겨준 최종 확신도 (기본 0.75)
                    final_prob = stock.get('prob', 0.75)
                    
                    # 확신도가 높으면 수급이 조금만 들어와도 바로 낚아챔
                    v_pw_limit = 100 if final_prob >= 0.80 else 120
                    is_shooting = ws_data.get('v_pw', 0) >= v_pw_limit

                    if score >= threshold or is_shooting:
                        msg = (f"🚀 **[{name}]({code}) v12.1 스나이퍼 포착, 진입!**\n"
                               f"현재가: `{p['curr']:,}원` | 확신도: `{final_prob*100:.1f}%`\n"
                               f"수급강도: `{ws_data.get('v_pw', 0):.1f}%` {visual}\n"
                               f"*(🎯 목표: +2.0% / 🛡️ 손절: -2.5%)*")
                        broadcast_callback(msg)
                        alerted_stocks.add(code)
                        
                        real_buy_qty = 0
                        if admin_id:
                            deposit = get_deposit(KIWOOM_TOKEN)
                            # 🚀 [핵심] 계좌 자산의 10% 비중으로만 매수 (MDD 500% -> 50% 이하로 제어)
                            real_buy_qty = calc_buy_qty(p['curr'], deposit, code, KIWOOM_TOKEN, ratio=0.1) 
                            if real_buy_qty > 0:
                                res = send_buy_order_market(code, real_buy_qty, KIWOOM_TOKEN)
                                if res and res.get('return_code') == 0:
                                    send_admin_msg(f"💰 **[매수성공]** {name} {real_buy_qty}주")
                        
                        update_stock_status(code, 'HOLDING', p['curr'], real_buy_qty or 1, datetime.now().timestamp())
                        stock['status'] = 'HOLDING'
                        stock['buy_price'] = p['curr']
                        stock['buy_qty'] = real_buy_qty or 1
                        stock['buy_time'] = datetime.now().timestamp()

                # ========================================================
                # [Case B] 보유 종목 익절/손절 (v12.1 전략 반영)
                # ========================================================
                elif status == 'HOLDING': 
                    curr_p = ws_data['curr']
                    buy_p = stock.get('buy_price', 0)
                    
                    if buy_p > 0 and curr_p > 0:
                        profit_rate = (curr_p - buy_p) / buy_p * 100
                        
                        # 🚀 [v12.1] 엄격한 정답지에 맞춘 익/손절 라인
                        is_take_profit = profit_rate >= 2.0  # 익절 +2.0%
                        is_stop_loss = profit_rate <= -2.5   # 손절 -2.5% (노이즈 견디기)
                        
                        # 타임컷: 장 마감 직전(오후 3시 15분)이 되면 당일 무조건 청산 (오버나잇 금지)
                        now_time = datetime.now().time()
                        market_close_time = datetime.strptime("15:15:00", "%H:%M:%S").time()
                        is_time_cut = now_time >= market_close_time
                        
                        if is_take_profit or is_stop_loss or is_time_cut:
                            reason = "🎯 목표가 달성" if is_take_profit else ("🛑 손절 가이드" if is_stop_loss else "⏳ 장마감 타임컷")
                            
                            sign = "🎊 [익절 완료]" if profit_rate > 0 else "📉 [손절 완료]"
                            msg = (f"{sign} **{name} 트래킹 종료**\n사유: `{reason}`\n"
                                   f"최종 수익률: `{profit_rate:+.2f}%` ({buy_p:,}원 ➡️ {curr_p:,}원)")
                            broadcast_callback(msg)
                            
                            if admin_id and stock.get('buy_qty', 0) > 0:
                                res = send_sell_order_market(code, stock['buy_qty'], KIWOOM_TOKEN)
                                if res and res.get('return_code') == 0:
                                    send_admin_msg(f"🏁 **[매도완료]** {name} ({profit_rate:+.2f}%)")
                            
                            update_stock_status(code, 'COMPLETED')
                            stock['status'] = 'COMPLETED'

            time.sleep(1)
            
    except Exception as e:
        kiwoom_utils.log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}", config=CONF, send_telegram=True)

    except KeyboardInterrupt:
        print("\n🛑 엔진 종료")