import requests
import json
import kiwoom_utils

def calc_buy_qty(current_price, total_deposit, code, token, ratio=0.1):
    """
    예수금 대비 비중을 계산하여 매수 수량 산출
    (소수점 매매 미지원으로 인해 정수 수량만 계산)
    """
    if current_price <= 0 or total_deposit <= 0: 
        return 0
    
    target_budget = total_deposit * ratio
    safe_budget = target_budget * 0.95 # 수수료 및 슬리피지 대비 95% 사용
    
    qty = int(safe_budget // current_price)
    return qty

def send_buy_order_market(code, qty, token, config=None):
    """
    [kt10000] 시장가 매수 주문 및 에러 감시
    """
    if qty <= 0:
        return None

    code = code[0:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10000'
    }
    
    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": str(code),
        "ord_qty": str(qty),
        "ord_uv": "",
        "trde_tp": "3", # 시장가
        "cond_uv": ""
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        
        # 1. HTTP 통신 에러 체크
        if res.status_code != 200:
            kiwoom_utils.log_error(f"🚨 [매수주문] 통신 실패 (HTTP {res.status_code}) - {code}", config=config, send_telegram=True)
            return None
            
        data = res.json()
        
        # 2. 키움 API 내부 처리 결과 체크 (rt_cd '0'이 아니면 실패)
        rt_cd = data.get('rt_cd')
        if rt_cd != '0':
            err_msg = data.get('err_msg', '상세 사유 없음')
            kiwoom_utils.log_error(f"❌ [매수거절] 종목:{code}, 사유:{err_msg} (코드:{rt_cd})", config=config, send_telegram=True)
            return None
            
        return data

    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [매수주문] 시스템 예외 발생: {str(e)}", config=config, send_telegram=True)
        return None

def send_sell_order_market(code, qty, token, config=None):
    """
    [kt10001] 시장가 매도 주문 및 에러 감시
    """
    if qty <= 0:
        return None

    code = code[0:6]
    url = "https://api.kiwoom.com/api/dostk/ordr"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10001'
    }
    
    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": str(code),
        "ord_qty": str(qty),
        "ord_uv": "",
        "trde_tp": "3",
        "cond_uv": ""
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code != 200:
            kiwoom_utils.log_error(f"🚨 [매도주문] 통신 실패 (HTTP {res.status_code}) - {code}", config=config, send_telegram=True)
            return None
            
        data = res.json()
        
        rt_cd = data.get('rt_cd')
        if rt_cd != '0':
            err_msg = data.get('err_msg', '상세 사유 없음')
            kiwoom_utils.log_error(f"❌ [매도거절] 종목:{code}, 사유:{err_msg} (코드:{rt_cd})", config=config, send_telegram=True)
            return None
            
        return data

    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [매도주문] 시스템 예외 발생: {str(e)}", config=config, send_telegram=True)
        return None

def get_deposit(token, config=None):
    """
    [kt00001] 예수금 조회 및 에러 감시
    """
    url = "https://api.kiwoom.com/api/dostk/acnt"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00001'
    }
    
    payload = {"qry_tp": "3"} # 주문가능금액 포함 조회
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code != 200:
            kiwoom_utils.log_error(f"🚨 [예수금조회] 통신 실패 (HTTP {res.status_code})", config=config, send_telegram=False)
            return 0
            
        data = res.json()
        
        if data.get('rt_cd') != '0':
            err_msg = data.get('err_msg', '상세 사유 없음')
            kiwoom_utils.log_error(f"⚠️ [예수금조회] 실패 사유: {err_msg}", config=config, send_telegram=False)
            return 0
            
        # 정상 조회 시 주문가능금액 반환
        return int(data.get('ord_alow_amt', 0))

    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [예수금조회] 시스템 예외 발생: {str(e)}", config=config, send_telegram=False)
        return 0