import requests
import json

def calc_buy_qty(current_price, total_deposit, ratio=0.1):
    """
    total_deposit(전체 예수금) 중 ratio(비율)만큼만 사용하여 수량 계산
    """
    if current_price <= 0 or total_deposit <= 0: 
        return 0
    
    # 1. 사용할 예산 결정 (예: 전체 예수금 1,000만원 * 0.1 = 100만원)
    target_budget = total_deposit * ratio
    
    # 2. 슬리피지 및 수수료 대비 안전 예산 설정 (95% 권장)
    # 90%는 너무 보수적일 수 있으니 95% 정도로 조정해 보았습니다.
    safe_budget = target_budget * 0.95
    
    # 3. 정수 수량 반환
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
    
    # 사용자 제공 request.txt 형식 반영
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
    
# kiwoom_orders.py에 추가

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
    
    # 업로드해주신 request.txt 형식을 100% 반영
    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": str(code),
        "ord_qty": str(qty), # 전량 매도를 위해 매수 시 저장된 수량 사용
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
    
# kiwoom_orders.py (기존 내용 아래에 추가)

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
    
    # 미수금 반영: 추정조회(3) 옵션을 사용하면 미수금이 반영된 정확한 주문가능금액을 조회할 수 있어, 미수금 없이 주문 가능한 잔액 확인에 적합합니다.
    payload = {
        "qry_tp": "3"
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            # ord_alow_amt: 주문가능금액 (실제 매수 가능 금액)
            d2_deposit = int(data.get('ord_alow_amt', 0))
            return d2_deposit
        else:
            print(f"🚨 [Deposit] 주문가능금액 조회 실패: {res.status_code}")
            return 0
    except Exception as e:
        print(f"🚨 [Deposit] 시스템 에러: {e}")
        return 0