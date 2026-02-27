import time
import sqlite3
import pandas as pd
import json
import requests
import threading
import final_ensemble_scanner # 🚀 장중 재스캔을 위해 임포트
import FinanceDataReader as fdr
import kiwoom_utils
import kiwoom_orders
import db_manager # 🚀 신규 DB 매니저 임포트
from kiwoom_websocket import KiwoomWSManager
from google_sheets_utils import GoogleSheetsManager
from datetime import timedelta # 상단에 없다면 추가
from datetime import datetime

# ✅ [복구] 실제 주문을 위한 라이브러리 임포트
from kiwoom_orders import send_buy_order_market, calc_buy_qty, get_deposit, send_sell_order_market

# 종목별 장중 최고가 저장소 (가변 익절용)
highest_prices = {}

# --- [전역 상태 변수] -----------------------------------------------
# 함수들이 쪼개지더라도 기존 상태를 기억하도록 모듈 레벨에서 관리합니다.
highest_prices = {} 
alerted_stocks = set() 
# -------------------------------------------------------------------

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

    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, 0.5, 70)
    return (f"🔍 *[{stock_name}]({code}) 실시간 분석*\n💰 현재가: `{p['curr']:,}원`\n{visual}\n🎯 목표가: `{p['sell']:,}원` (+3%)\n📝 확신지수: `{score:.1f}점`\n{conclusion}")

def get_detailed_reason(code):
    """
    특정 종목이 왜 안 사고 있는지 상세 사유를 리포트로 반환
    """
    # 1. 감시 리스트에서 해당 종목 찾기
    targets = db_manager.get_active_targets()
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

def get_market_regime():
    """코스피 5일 이동평균을 기준으로 상승장(BULL)/조정장(BEAR)을 판별합니다."""
    try:
        # 최근 10일치 데이터를 가져와서 5일 전과 비교
        kospi = fdr.DataReader('KS11', start=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'))
        kospi_5d_return = (kospi['Close'].iloc[-1] / kospi['Close'].iloc[-5]) - 1
        
        # 0보다 크면 상승 추세, 아니면 조정/하락 추세
        return 'BULL' if kospi_5d_return > 0 else 'BEAR'
    except Exception as e:
        print(f"⚠️ 시장 상태 조회 실패 (기본값 BULL 적용): {e}")
        return 'BULL'

def check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback): # 🚀 콜백 인자 추가
    """[장중 스캔 부서] 감시 슬롯이 부족하면 신규 주도주를 보충합니다."""
    watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
    if watching_count < 5 and (time.time() - last_scan_time > 1800):
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
                    
            return time.time() # 스캔 완료 시점 갱신
        except Exception as e:
            kiwoom_utils.log_error(f"⚠️ 장중 스캔 중 오류: {e}")
    return last_scan_time

def handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback):
    """[감시/매수 부서] 신규 진입 포착 및 매수 주문을 담당합니다."""
    if code in alerted_stocks: return
    
    ai_prob = stock.get('prob', 0.75)
    score, details, visual, p, conclusion, checklist = kiwoom_utils.analyze_signal_integrated(ws_data, ai_prob)

    # 확신도에 따른 유연한 수급 필터
    v_pw_limit = 100 if ai_prob >= 0.80 else 115
    is_shooting = ws_data.get('v_pw', 0) >= v_pw_limit

    if score >= 80 or is_shooting:
            msg = (f"🚀 **[{stock['name']}]({code}) 스나이퍼 포착!**\n"
                   f"현재가: `{p['curr']:,}원` | 확신도: `{ai_prob:.1%}`\n"
                   f"수급강도: `{ws_data.get('v_pw', 0):.1f}%` {visual}")
            broadcast_callback(msg)
            alerted_stocks.add(code)
            
            # -----------------------------------------------------
            # 🚀 [수정됨] 매수 주문 및 에러 추적 로직 강화
            # -----------------------------------------------------
            if not admin_id:
                print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID(ADMIN_ID)가 없어 주문을 패스합니다.")
                return

            deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN, config=CONF)
            real_buy_qty = kiwoom_orders.calc_buy_qty(p['curr'], deposit, code, KIWOOM_TOKEN, ratio=0.1) 
            
            if real_buy_qty <= 0:
                print(f"⚠️ [매수보류] {stock['name']}: 계산된 매수 수량이 0주입니다. (현재가:{p['curr']}원 / 예수금:{deposit}원)")
                return

            # 실제 주문 전송
            res = kiwoom_orders.send_buy_order_market(code, real_buy_qty, KIWOOM_TOKEN, config=CONF)
            
            is_success = False
            ord_no = ''
            
            # 🚀 API 응답 타입이 dict이든 bool이든 모두 유연하게 처리합니다.
            if isinstance(res, dict):
                # 숫자 0과 문자열 '0'을 모두 커버하기 위해 문자로 변환 후 비교
                rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
                if rt_cd == '0':
                    is_success = True
                    ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
                else:
                    err_msg = res.get('return_msg', '사유 없음')
                    print(f"❌ [주문거절] {stock['name']} 서버 거절: {err_msg} ({res})")
            elif res: 
                # 만약 send_buy_order_market이 단순히 True만 리턴하는 구조일 경우
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
                
                # DB에 PENDING 상태 업데이트
                db_manager.update_stock_status(
                    code=code, 
                    status='PENDING', 
                    buy_price=p['curr'], 
                    buy_qty=real_buy_qty, 
                    buy_time=datetime.now().strftime('%H:%M:%S')
                )
            else:
                print(f"❌ [주문실패] {stock['name']} 응답값 이상 또는 통신실패: {res}")

def handle_holding_state(stock, code, ws_data, admin_id, broadcast_callback, market_regime):
    """
    [보유/매도 부서] 차트 위치(태그) 및 시장 상태별 2중 가변 손절 적용
    """
    pos_tag = stock.get('position_tag', 'MIDDLE')

    # ⚙️ [대표님 설정 영역] 시장 상태별 손절 라인 설정 (언제든 여기서 수정하세요!)
    STOP_LOSS_BULL = -3.5  # 상승장일 때의 손절선 (%)
    STOP_LOSS_BEAR = -1.5  # 조정장/하락장일 때의 타이트한 손절선 (%)
    STOP_LOSS_BREAKOUT = -1.5   # 🚀 [돌파형] 휩쏘/가짜돌파 방어용 칼손절
    STOP_LOSS_BOTTOM = -3.0     # 🚀 [바닥형] 매물대 소화 흔들기 버티기용

    # 시장 판독 결과에 따라 현재 사용할 손절선을 결정합니다.
    current_stop_loss = STOP_LOSS_BULL if market_regime == 'BULL' else STOP_LOSS_BEAR

    curr_p = ws_data['curr']
    buy_p = stock.get('buy_price', 0)
    if buy_p <= 0: return

    # 1순위: 차트 위치에 따른 특수 손절선 적용
    if pos_tag == 'BREAKOUT':
        current_stop_loss = STOP_LOSS_BREAKOUT
        regime_name = "전고점 돌파 시도"
    elif pos_tag == 'BOTTOM':
        current_stop_loss = STOP_LOSS_BOTTOM
        regime_name = "바닥 탈출 구간"
    # 2순위: 특이점이 없으면(MIDDLE) 시장 상태 적용
    else:
        current_stop_loss = STOP_LOSS_BULL if market_regime == 'BULL' else STOP_LOSS_BEAR
        regime_name = "상승장" if market_regime == 'BULL' else "조정장"

    curr_p = ws_data['curr']
    buy_p = stock.get('buy_price', 0)
    if buy_p <= 0: return

    # 1) 최고가 갱신 및 수익률 계산
    if code not in highest_prices: highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)
    
    profit_rate = (curr_p - buy_p) / buy_p * 100
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100
    
    is_sell_signal = False
    reason = ""

    # A. 가변 익절 (Trailing Stop)
    if peak_profit >= 2.0:
        drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
        if drawdown >= 0.5:
            is_sell_signal = True
            reason = f"가변익절(고점:{peak_profit:.1f}% 대비 하락)"
        elif profit_rate <= 1.5:
            is_sell_signal = True
            reason = "익절 수익 보존(최소 1.5%)"
    
    # B. 🚀 가변 손절 라인 적용 (위치 + 시장상태 융합)
    elif profit_rate <= current_stop_loss:
        is_sell_signal = True
        # ✅ regime_name은 함수 위쪽에서 이미 결정되었으므로 그대로 가져다 씁니다.
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

        # 🚀 [추가] DB 상태를 매매 완료(COMPLETED)로 변경
        db_manager.update_stock_status(code, 'COMPLETED')

def handle_pending_state(stock, code):
    """
    [미체결 부서] 주문 후 30초가 경과하면 남은 물량을 전량 취소합니다.
    """
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time
    
    # ⏱️ 1. 30초 대기 타이머
    if time_elapsed > 30:
        print(f"⚠️ [{stock['name']}] 주문 30초 경과. 미체결 물량(최유리지정가) 취소를 시도합니다.")
        
        orig_ord_no = stock.get('odno')
        if not orig_ord_no:
            print(f"❌ [{stock['name']}] 원주문번호가 없어 취소를 진행할 수 없습니다. 감시 모드로 복귀합니다.")
            stock['status'] = 'WATCHING'
            return

        # 🚀 2. 취소 주문 전송 (0개 = 미체결 잔량 싹 다 취소)
        res = kiwoom_orders.send_cancel_order(
            code=code, 
            orig_ord_no=orig_ord_no, 
            token=KIWOOM_TOKEN, 
            qty=0, 
            config=CONF
        )
        
        # 🚀 3. 취소 결과에 따른 다음 상태 결정
        if res:
            # 정상적으로 취소가 접수된 경우 -> 다시 매수 기회를 노리기 위해 WATCHING으로 복귀
            kiwoom_utils.log_error(f"🔄 [{stock['name']}] 미체결 잔량 취소 완료. 다시 타점을 감시합니다.", config=CONF)
            stock['status'] = 'WATCHING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            highest_prices.pop(code, None) # 고점 기록도 초기화
            
            # 🚀 [추가] DB 상태를 다시 감시 모드로 복구 (수량, 가격 초기화)
            db_manager.update_stock_status(code, 'WATCHING', buy_price=0, buy_qty=0, buy_time='')
        else:
            # 취소가 실패(거절)된 경우 -> '이미 30초 안에 전량 체결되었다'고 간주하고 익절 모드로 진입
            kiwoom_utils.log_error(f"ℹ️ [{stock['name']}] 취소 실패 (이미 전량 체결 예상). 매도 감시(HOLDING)를 시작합니다.", config=CONF)
            stock['status'] = 'HOLDING'
            stock.pop('odno', None)
            stock.pop('order_time', None)
            
            # 🚀 [추가] DB 상태를 HOLDING으로 확정 (수량, 가격은 이미 PENDING때 들어감)
            # 여기서는 status만 업데이트하면 되므로 간단하게 호출
            db_manager.update_stock_status(code, 'HOLDING')

# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (교통 정리 전담)
# ==============================================================================
def run_sniper(broadcast_callback):
    global KIWOOM_TOKEN, WS_MANAGER
    
    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V12.1 가동 (관리자 ID: {admin_id})")
    
    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        kiwoom_utils.log_error("❌ 토큰 발급 실패로 엔진을 중단합니다.", config=CONF, send_telegram=True)
        return

    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)
    WS_MANAGER.start()
    time.sleep(2) 
    
    targets = db_manager.get_active_targets()
    last_scan_time = time.time() 

    # 🚀 수정 1: 엔진 가동 시 오늘의 시장 상태를 계산하여 기억합니다.
    current_market_regime = get_market_regime()
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다. 맞춤형 손절이 적용됩니다.")

    target_codes = [t['code'] for t in targets]
    WS_MANAGER.subscribe([c for c in target_codes]) 
    last_msg_min = -1

    try:
        while True:
            now = datetime.now()
            now_t = now.time()

            # 1. 장 마감 및 자동 종료 체크
            if now_t >= datetime.strptime("15:20:00", "%H:%M:%S").time():
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                break
            
            # 2. 장중 감시 종목 자동 채우기
            # 🚀 수정: broadcast_callback 인자 추가
            last_scan_time = check_and_run_intraday_scanner(targets, last_scan_time, broadcast_callback)

            # 3. 생존 신고 (하트비트)
            if now_t.minute != last_msg_min:
                watching_count = len([t for t in targets if t['status'] == 'WATCHING'])
                holding_count = len([t for t in targets if t['status'] == 'HOLDING'])
                current_time_str = now.strftime('%H:%M:%S')
                print(f"💓 [{current_time_str}] 엔진 가동 중... (감시: {watching_count} / 보유: {holding_count})")
                last_msg_min = now_t.minute
            
            # 4. 개별 종목 상태 머신 라우팅
            for stock in targets:
                code = str(stock['code'])[:6] 
                status = stock['status']
                
                ws_data = WS_MANAGER.get_latest_data(code)
                if not ws_data or ws_data.get('curr', 0) == 0: continue

                # 🚀 상태(Status)에 따라 각 전담 함수로 업무 위임
                if status == 'WATCHING':
                    handle_watching_state(stock, code, ws_data, admin_id, broadcast_callback)
                
                elif status == 'HOLDING':
                    # 🚀 수정 2: 시장 상태(current_market_regime)를 인자로 같이 넘겨줍니다.
                    handle_holding_state(stock, code, ws_data, admin_id, broadcast_callback, current_market_regime)
                
                elif status == 'PENDING':
                    handle_pending_state(stock, code)

            time.sleep(1) # CPU 부하 감소
            
    except Exception as e:
        kiwoom_utils.log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}", config=CONF, send_telegram=True)

    except KeyboardInterrupt:
        print("\n🛑 엔진 종료")