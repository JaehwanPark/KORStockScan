import requests
import json
import logging
import os
from datetime import datetime

# --- [1. 통합 에러 로깅 및 관제 설정] ---
# 로거 생성
error_logger = logging.getLogger('KORStockScan_Error')
error_logger.setLevel(logging.ERROR)

# 핸들러가 없을 경우에만 설정 (중복 로깅 방지)
if not error_logger.handlers:
    # 1) 파일 핸들러: system_errors.log 파일에 기록 (UTF-8)
    fh = logging.FileHandler('system_errors.log', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    error_logger.addHandler(fh)
    
    # 2) 스트림 핸들러: 터미널 창에도 즉시 출력
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('🚨 [%(asctime)s] %(message)s', '%H:%M:%S'))
    error_logger.addHandler(sh)

def log_error(msg, config=None, send_telegram=False):
    """
    시스템 전체에서 발생하는 에러를 중앙 집중적으로 관리합니다.
    :param msg: 에러 메시지 내용
    :param config: 텔레그램 설정을 포함한 객체 (Optional)
    :param send_telegram: True일 경우 텔레그램으로 긴급 알림 전송
    """
    # 1. 파일 및 터미널에 에러 기록
    error_logger.error(msg)

    # 2. 텔레그램 긴급 알림 전송
    if send_telegram and config:
        try:
            token = config.get('TELEGRAM_TOKEN')
            chat_ids = config.get('CHAT_IDS', [])
            
            # 메시지 포맷팅
            alert_msg = f"⚠️ *[KORStockScan v12.1 에러 알림]*\n\n"
            alert_msg += f"🕒 발생시각: {datetime.now().strftime('%H:%M:%S')}\n"
            alert_msg += f"📝 내용: {msg}"
            
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, data={
                    "chat_id": chat_id, 
                    "text": alert_msg, 
                    "parse_mode": "Markdown"
                }, timeout=5)
        except Exception as e:
            # 텔레그램 전송 실패 시 파일에만 기록
            error_logger.error(f"텔레그램 알림 발송 실패: {e}")

# --- [2. 키움 API 통신 유틸리티] ---

def get_kiwoom_token(config):
    """키움 접근 토큰 발급"""
    url = "https://api.kiwoom.com/oauth2/token"
    params = {
        'grant_type': 'client_credentials',
        'appkey': config.get('KIWOOM_APPKEY'),
        'secretkey': config.get('KIWOOM_SECRETKEY'),
    }
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    try:
        res = requests.post(url, headers=headers, json=params, timeout=10)
        if res.status_code == 200:
            return res.json().get('token')
        else:
            log_error(f"토큰 발급 실패 (HTTP {res.status_code})", config=config, send_telegram=True)
            return None
    except Exception as e:
        log_error(f"토큰 발급 중 시스템 예외: {e}", config=config, send_telegram=True)
        return None

def get_fractional_info(code, token):
    """
    ka10001(주식기본정보요청)을 호출하여 소수점 거래 가능 여부 확인
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'ka10001'
    }
    payload = {"stk_cd": str(code)}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            flo_stk = data.get('flo_stk', '')
            fav_unit = data.get('fav_unit', '')
            is_fractional = True if (isinstance(flo_stk, str) and '.' in flo_stk) else False
            return {'is_fractional': is_fractional, 'fav_unit': fav_unit}
        return {'is_fractional': False, 'fav_unit': ''}
    except:
        return {'is_fractional': False, 'fav_unit': ''}

# --- [3. 보조 계산 및 시각화] ---

def generate_visual_gauge(ratio, label_left="매도", label_right="매수"):
    """수급 비율 바(Bar) 생성"""
    size = 10
    filled = int(round(ratio * size))
    gauge = "▓" * filled + "░" * (size - filled)
    return f"[{label_left} {gauge} {label_right}]"

def analyze_signal_integrated(ws_data, ai_prob, threshold=70):
    """실시간 데이터와 AI 확률을 결합한 통합 분석 점수 산출"""
    score = ai_prob * 50
    details = [f"AI({ai_prob:.0%})"]
    
    if not ws_data or ws_data.get('curr', 0) == 0:
        return 0, "데이터 부족", "", {}, "결론: 분석 대기"

    curr_price = ws_data['curr']
    prices = {
        'curr': curr_price, 
        'buy': curr_price, 
        'sell': int(curr_price * 1.02), 
        'stop': int(curr_price * 0.975)
    }

    # 호가 잔량비 계산
    ask_tot = ws_data.get('ask_tot', 1)
    bid_tot = ws_data.get('bid_tot', 1)
    ratio_val = (ask_tot / (ask_tot + bid_tot)) * 100
    
    # 체결강도 계산
    v_pw = ws_data.get('v_pw', 0.0)
    
    if v_pw >= 110:
        score += 25
        details.append("수급강")
    
    if 1.5 <= (ask_tot / (bid_tot + 1e-9)) <= 5.0:
        score += 25
        details.append("호가적격")

    conclusion = "✅ *매수 검토*" if score >= threshold else "🚫 *관망*"
    visuals = f"📊 잔량비: {ratio_val:.1f}% | ⚡ 체결강도: {v_pw:.1f}%"

    return score, " + ".join(details), visuals, prices, conclusion