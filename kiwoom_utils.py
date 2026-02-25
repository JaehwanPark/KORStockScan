import requests
import json
import logging
import os
from datetime import datetime

# --- [1. 통합 에러 로깅 및 관제 설정] ---
error_logger = logging.getLogger('KORStockScan_Error')
error_logger.setLevel(logging.ERROR)

if not error_logger.handlers:
    # 파일 기록 설정
    fh = logging.FileHandler('system_errors.log', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    error_logger.addHandler(fh)
    
    # 터미널 출력 설정
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('🚨 [%(asctime)s] %(message)s', '%H:%M:%S'))
    error_logger.addHandler(sh)

def log_error(msg, config=None, send_telegram=False):
    """중앙 집중형 에러 관리 함수"""
    error_logger.error(msg)
    if send_telegram and config:
        try:
            token = config.get('TELEGRAM_TOKEN')
            chat_ids = config.get('CHAT_IDS', [])
            alert_msg = f"⚠️ *[KORStockScan 에러 알림]*\n\n🕒 발생: {datetime.now().strftime('%H:%M:%S')}\n📝 내용: {msg}"
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, data={"chat_id": chat_id, "text": alert_msg, "parse_mode": "Markdown"}, timeout=5)
        except Exception as e:
            error_logger.error(f"텔레그램 전송 실패: {e}")

# --- [2. 키움 API 통신 및 기존 유틸리티 복구] ---

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

def revoke_kiwoom_token(token, config):
    """접근 토큰 폐기"""
    if not token: return
    url = "https://api.kiwoom.com/oauth2/revoke"
    params = {
        'appkey': config.get('KIWOOM_APPKEY'),
        'secretkey': config.get('KIWOOM_SECRETKEY'),
        'token': token
    }
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'api-id': 'au10002'}
    try:
        requests.post(url, headers=headers, json=params, timeout=5)
    except: pass

def get_stock_name_ka10001(code, token):
    """ka10001(주식기본정보요청) - 종목명 조회"""
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    # '_AL'이 붙지 않은 순수 코드로 요청하는 것이 일반적입니다.
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
            stock_name = data.get('stk_nm')
            return stock_name.strip() if stock_name else code
        return code
    except: return code

def get_stock_market_ka10100(code, token):
    """ka10100(종목 거래소 확인)"""
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'ka10100'
    }
    payload = {"stk_cd": str(code)}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            market_name = data.get('nxtEnable')
            return market_name
        return None
    except: return None

def get_fractional_info(code, token):
    """소수점 거래 가능 여부 확인"""
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
    except: return {'is_fractional': False, 'fav_unit': ''}

# --- [3. 보조 계산 및 시각화] ---

def generate_visual_gauge(ratio, label_left="매도", label_right="매수"):
    """수급 비율 바(Bar) 생성"""
    size = 10
    filled = int(round(ratio * size))
    gauge = "▓" * filled + "░" * (size - filled)
    return f"[{label_left} {gauge} {label_right}]"

def analyze_signal_integrated(ws_data, ai_prob, threshold=70):
    """
    [v12.1 정밀 진단 버전] 실시간 데이터와 수치를 결합한 통합 분석 및 상세 사유 반환
    """
    score = ai_prob * 50
    details = [f"AI({ai_prob:.0%})"]
    visuals = ""
    prices = {}
    
    # 🚀 상세 체크리스트 초기 설정 (반환용)
    checklist = {
        "AI 확신도 (75%↑)": {"val": f"{ai_prob:.1%}", "pass": ai_prob >= 0.75},
        "유동성 (5천만↑)": {"val": "데이터 대기", "pass": False},
        "체결강도 (100%↑)": {"val": "데이터 대기", "pass": False},
        "호가잔량비 (1.5~5배)": {"val": "데이터 대기", "pass": False}
    }

    if not ws_data or ws_data.get('curr', 0) == 0:
        return 0, "데이터 부족", "", prices, "결론: 데이터 수신 중", checklist

    try:
        curr_price = ws_data['curr']
        prices = {'curr': curr_price, 'buy': curr_price, 'sell': int(curr_price * 1.03), 'stop': int(curr_price * 0.97)}

        ask_tot = ws_data.get('ask_tot', 1)
        bid_tot = ws_data.get('bid_tot', 1)
        total = ask_tot + bid_tot
      
        # 1️⃣ 유동성 필터 및 체크리스트 업데이트
        liquidity_value = (ask_tot + bid_tot) * curr_price
        MIN_LIQUIDITY = 50_000_000
        checklist["유동성 (5천만↑)"] = {"val": f"{liquidity_value/1e6:.1f}백만", "pass": liquidity_value >= MIN_LIQUIDITY}
        
        ratio_val = (ask_tot / total) * 100 if total > 0 else 0
        gauge_idx = int(ratio_val / 10)
        
        visuals += f"📊 잔량비: [{'▓'*gauge_idx:<10}] {ratio_val:.1f}%\n"
        visuals += f"   (매도: {ask_tot:,} / 매수: {bid_tot:,})\n"
        
        # 2️⃣ 호가잔량비 분석 및 체크리스트 업데이트
        imb_ratio = ask_tot / (bid_tot + 1e-9)
        pass_imb = 1.5 <= imb_ratio <= 5.0
        checklist["호가잔량비 (1.5~5배)"] = {"val": f"{imb_ratio:.2f}배", "pass": pass_imb}
        
        if pass_imb:
            score += 25
            details.append("호가(적격)")

        # 3️⃣ 체결강도 분석 및 체크리스트 업데이트
        v_pw = ws_data.get('v_pw', 0.0)
        visuals += f"⚡ 체결강도: {v_pw:.1f}%\n"
        
        pass_v_pw = v_pw >= 100
        checklist["체결강도 (100%↑)"] = {"val": f"{v_pw:.1f}%", "pass": pass_v_pw}
        
        if v_pw >= 110:
            score += 25
            details.append("수급(강)")
        elif v_pw >= 100:
            score += 15
            details.append("수급(중)")

        # 4️⃣ 최종 결론 로직 (보내주신 로직 그대로 유지)
        if (v_pw < 100 and score < threshold) or (liquidity_value < MIN_LIQUIDITY):
            conclusion = "🚫 *결론: 매수타이밍이 아닙니다*"
        else:
            conclusion = "✅ *결론: 매수를 검토해보십시오*"

    except Exception as e:
        conclusion = "결론: 분석 오류"

    # 🚀 최종적으로 checklist를 6번째 인자로 추가 반환
    return score, " + ".join(details), visuals, prices, conclusion, checklist