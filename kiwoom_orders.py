import requests
import json
import kiwoom_utils # 🚀 추가: 소수점 정보 조회 유틸리티 사용

def calc_buy_qty(current_price, total_deposit, code, token, ratio=0.1):
    """
    total_deposit(전체 예수금) 중 ratio(비율)만큼만 사용하여 수량 계산
    🚀 [업데이트] 소수점 거래 가능 종목이면 1주 미만도 예산에 맞춰 소수점 수량으로 계산
    """
    if current_price <= 0 or total_deposit <= 0: 
        return 0
    
    # 1. 사용할 예산 결정 (예: 전체 예수금 1,000만원 * 0.1 = 100만원)
    target_budget = total_deposit * ratio
    
    # 2. 슬리피지 및 수수료 대비 안전 예산 설정 (95% 권장)
    safe_budget = target_budget * 0.95
    
    # 3. 키움 API를 통한 소수점 거래 가능 여부 확인
    fractional_info = kiwoom_utils.get_fractional_info(code, token)
    
    # 4. 수량 계산 로직 분기
    if fractional_info['is_fractional']:
        # [소수점 매수 로직]
        # 예: fav_unit이 "0.01" 처럼 내려온다고 가정하고 최소 단위 파악
        try:
            fav_unit_str = str(fractional_info.get('fav_unit', '0.01'))
            fav_unit_float = float(fav_unit_str) if fav_unit_str else 0.01
            if fav_unit_float <= 0: fav_unit_float = 0.01
        except:
            fav_unit_float = 0.01
            
        # 소수점 단위로 안전 예산 내 수량 내림 계산
        raw_qty = safe_budget / current_price
        qty = (raw_qty // fav_unit_float) * fav_unit_float
        
        # 파이썬 부동소수점 오차 방지를 위해 소수점 자릿수 정리 (예: 0.120000001 -> 0.12)
        decimals = len(str(fav_unit_float).split('.')[1]) if '.' in str(fav_unit_float) else 0
        qty = round(qty, decimals)
        
        print(f"💡 [소수점 거래] {code}: 1주 {current_price:,}원. 예산 {safe_budget:,.0f}원에 맞춰 {qty}주 매수 세팅")
        return qty

    else:
        # [일반 정수 매수 로직] (기존과 동일)
        qty = int(safe_budget // current_price)
        return qty

def send_buy_order_market(code, qty, token):
    """
    [kt10000] 시장가 매수 주문 전송
    """
    code = code[0:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10000'
    }
    
    # payload의 ord_qty는 str(qty)를 통해 0.5 같은 소수점도 정상적으로 문자열 "0.5"로 변환되어 들어갑니다.
    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": str(code),
        "ord_qty": str(qty),
        "ord_uv": "",   # 시장가는 가격 빈값
        "trde_tp": "3", # 3: 시장가
        "cond_uv": ""
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"🚨 [Order] HTTP 에러: {res.status_code}")
            return None
    except Exception as e:
        print(f"🚨 [Order] 시스템 에러: {e}")
        return None

def send_sell_order_market(code, qty, token):
    """
    [kt10001] 주식 매도주문 (시장가 전량 매도)
    """
    code = code[0:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10001' # 💡 매도 전용 API ID
    }
    
    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": str(code),
        "ord_qty": str(qty), # 매수 시 소수점이었다면 그대로 소수점 전량 매도
        "ord_uv": "",        # 시장가는 가격 빈값
        "trde_tp": "3",      # 3: 시장가
        "cond_uv": ""
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"🚨 [Sell] HTTP 에러: {res.status_code}")
            return None
    except Exception as e:
        print(f"🚨 [Sell] 시스템 에러: {e}")
        return None

def get_deposit(token):
    """
    [kt00001] 예수금상세현황요청(kt00001) API를 사용해 예수금 잔액과 주문가능금액을 조회
    """
    url = "https://api.kiwoom.com/api/dostk/acnt"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00001'
    }
    
    payload = {
        "qry_tp": "3"
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            d2_deposit = int(data.get('ord_alow_amt', 0))
            return d2_deposit
        else:
            print(f"🚨 [Deposit] 주문가능금액 조회 실패: {res.status_code}")
            return 0
    except Exception as e:
        print(f"🚨 [Deposit] 시스템 에러: {e}")
        return 0