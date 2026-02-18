import requests
import json

def get_kiwoom_token(config):
    """키움 접근 토큰 발급 (응답 필드 'token' 반영)"""
    url = "https://api.kiwoom.com/oauth2/token"
    params = {
        'grant_type': 'client_credentials',
        'appkey': config.get('KIWOOM_APPKEY'),
        'secretkey': config.get('KIWOOM_SECRETKEY'),
    }
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    try:
        res = requests.post(url, headers=headers, json=params)
        if res.status_code == 200:
            return res.json().get('token')
        return None
    except: return None

def revoke_kiwoom_token(token, config):
    """au10002 API를 통한 접근 토큰 폐기"""
    if not token: return
    url = "https://api.kiwoom.com/oauth2/revoke"
    params = {
        'appkey': config.get('KIWOOM_APPKEY'),
        'secretkey': config.get('KIWOOM_SECRETKEY'),
        'token': token
    }
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'api-id': 'au10002'}
    try:
        requests.post(url, headers=headers, json=params)
    except: pass

def get_stock_name_ka10001(code, token):
    """
    ka10001(주식기본정보요청)을 POST 방식으로 호출하여 종목명을 반환합니다.
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    
    # 샘플 코드와 동일한 헤더 구성
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'ka10001'
    }
    
    # POST 방식이므로 종목 코드를 JSON 바디에 담아 전송
    payload = {
        "stk_cd": str(code)
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            
            # 테스트 결과(test.json)에 맞춰 최상위에서 바로 stk_nm 추출
            stock_name = data.get('stk_nm')
            
            if stock_name:
                return stock_name.strip()
            return code
        else:
            print(f"⚠️ ka10001 호출 실패: {res.status_code}")
            return code
    except Exception as e:
        print(f"⚠️ 종목명 조회 에러: {e}")
        return code

def generate_visual_gauge(ratio, label_left="매도", label_right="매수"):
    """수급 비율을 시각적 바(Bar)로 변환"""
    size = 10
    filled = int(round(ratio * size))
    gauge = "▓" * filled + "░" * (size - filled)
    return f"[{label_left} {gauge} {label_right}]"

def analyze_signal_integrated(ws_data, ai_prob):
    """
    [웹소켓 통합 버전] 실시간 데이터(ws_data)와 AI 확률을 통합 분석
    """
    score = ai_prob * 50
    details = [f"AI({ai_prob:.0%})"]
    visuals = ""
    prices = {}

    # 데이터 미수신 상태 방어
    if not ws_data or ws_data.get('curr', 0) == 0:
        return 0, "데이터 부족", "", prices

    try:
        # 1. 가격 전략 세팅
        curr_price = ws_data['curr']
        prices = {'curr': curr_price, 'buy': curr_price, 'sell': int(curr_price * 1.03), 'stop': int(curr_price * 0.97)}

        # 2. 호가 잔량 분석 (0D 기반)
        ask_tot = ws_data.get('ask_tot', 1)
        bid_tot = ws_data.get('bid_tot', 1)
        total = ask_tot + bid_tot
        
        if total > 0:
            ratio = int((ask_tot / total) * 10)
            visuals += f"📊 잔량비: [{'▓'*ratio:<10}] (매도우위)\n"
        
        imb_ratio = ask_tot / (bid_tot + 1e-9)
        if 1.5 <= imb_ratio <= 5.0:
            score += 25
            details.append("호가(적격)")

        # 3. 체결 강도 분석 (0B 기반)
        v_pw = ws_data.get('v_pw', 0.0)
        visuals += f"⚡ 체결강도: {v_pw:.1f}%\n"
        
        if v_pw >= 110:
            score += 25
            details.append("수급(강)")
        elif v_pw >= 100:
            score += 15
            details.append("수급(중)")

    except Exception as e:
        print(f"⚠️ 통합 분석 중 오류: {e}")

    return score, " + ".join(details), visuals, prices