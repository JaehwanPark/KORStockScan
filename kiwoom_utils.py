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
    code = code + "_AL"
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

def get_stock_market_ka10100(code, token):
    """
    ka10100(종목 거래소 확인)을 POST 방식으로 호출하여 종목명을 반환합니다.
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    
    # 샘플 코드와 동일한 헤더 구성
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'ka10100'
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
            market_name = data.get('nxtEnable')
            
            if market_name == "Y":
                code = code + "_AL"
            return market_name
        else:
            print(f"⚠️ ka10100 호출 실패: {res.status_code}")
            return code
    except Exception as e:
        print(f"⚠️ 거래소명 조회 에러: {e}")
        return code

def generate_visual_gauge(ratio, label_left="매도", label_right="매수"):
    """수급 비율을 시각적 바(Bar)로 변환"""
    size = 10
    filled = int(round(ratio * size))
    gauge = "▓" * filled + "░" * (size - filled)
    return f"[{label_left} {gauge} {label_right}]"

def analyze_signal_integrated(ws_data, ai_prob, threshold=70):
    """
    [웹소켓 통합 버전] 실시간 데이터와 수치를 결합하여 상세 리포트 생성
    """
    score = ai_prob * 50
    details = [f"AI({ai_prob:.0%})"]
    visuals = ""
    prices = {}

    if not ws_data or ws_data.get('curr', 0) == 0:
        return 0, "데이터 부족", "", prices, "결론: 데이터 수신 중"

    try:
        curr_price = ws_data['curr']
        prices = {'curr': curr_price, 'buy': curr_price, 'sell': int(curr_price * 1.03), 'stop': int(curr_price * 0.97)}

        # 1. 호가 잔량 분석 및 수치화
        ask_tot = ws_data.get('ask_tot', 1)
        bid_tot = ws_data.get('bid_tot', 1)
        total = ask_tot + bid_tot
      
        # 💡 [신규] 유동성 필터: 총 잔량 가치가 5,000만 원 미만이면 스킵
        liquidity_value = (ask_tot + bid_tot) * curr_price
        MIN_LIQUIDITY = 50_000_000
        
        ratio_val = (ask_tot / total) * 100 if total > 0 else 0
        gauge_idx = int(ratio_val / 10)
        
        # 그래프 + 수치 + (매도/매수) 상세 표시
        visuals += f"📊 잔량비: [{'▓'*gauge_idx:<10}] {ratio_val:.1f}%\n"
        visuals += f"   (매도: {ask_tot:,} / 매수: {bid_tot:,})\n"
        
        imb_ratio = ask_tot / (bid_tot + 1e-9)
        if 1.5 <= imb_ratio <= 5.0:
            score += 25
            details.append("호가(적격)")

        # 2. 체결 강도 분석 및 수치화
        v_pw = ws_data.get('v_pw', 0.0)
        visuals += f"⚡ 체결강도: {v_pw:.1f}%\n"
        
        if v_pw >= 110:
            score += 25
            details.append("수급(강)")
        elif v_pw >= 100:
            score += 15
            details.append("수급(중)")
        elif liquidity_value < MIN_LIQUIDITY:
            score += 0
            details.append("유동성 부족")

        # 3. 최종 결론 로직 (사용자 요청 반영)
        # 체결강도 100% 미만 AND 확신지수 threshold 미만인 경우
        if v_pw < 100 and score < threshold:
            conclusion = "🚫 *결론: 매수타이밍이 아닙니다*"
        elif liquidity_value < MIN_LIQUIDITY:
            conclusion = "🚫 *결론: 매수타이밍이 아닙니다*"    
        else:
            conclusion = "✅ *결론: 매수를 검토해보십시오*"

    except Exception as e:
        print(f"⚠️ 분석 중 오류: {e}")
        conclusion = "결론: 분석 오류"

    return score, " + ".join(details), visuals, prices, conclusion