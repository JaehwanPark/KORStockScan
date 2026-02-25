import requests
import json
import kiwoom_utils

def calc_buy_qty(current_price, total_deposit, code, token, ratio=0.1):
    """
    [v12.1] 예수금 대비 비중을 계산하여 정수 수량 산출
    """
    if current_price <= 0 or total_deposit <= 0: 
        return 0
    
    target_budget = total_deposit * ratio
    safe_budget = target_budget * 0.95 # 슬리피지 대비 95% 사용
    
    qty = int(safe_budget // current_price)
    return qty

def send_buy_order_market(code, qty, token, config=None):
    """
    [kt10000] 시장가 매수 주문 - return_code 대응 수정
    """
    if qty <= 0: return None

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
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()
        
        # 🚀 [핵심 수정] rt_cd 또는 return_code 둘 중 하나라도 0이면 성공으로 간주
        is_success = data.get('rt_cd') == '0' or data.get('return_code') == 0
        
        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code') if data.get('return_code') is not None else data.get('rt_cd')
            kiwoom_utils.log_error(f"❌ [매수거절] 종목:{code}, 사유:{err_msg} (코드:{err_code})", config=config, send_telegram=True)
            return None
    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [매수주문] 시스템 예외: {str(e)}", config=config, send_telegram=True)
        return None

def send_sell_order_market(code, qty, token, config=None):
    """
    [kt10001] 시장가 매도 주문 - return_code 대응 수정
    """
    if qty <= 0: return None

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
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()
        
        # 🚀 [핵심 수정] 성공 판단 로직 통일
        is_success = data.get('rt_cd') == '0' or data.get('return_code') == 0
        
        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code') if data.get('return_code') is not None else data.get('rt_cd')
            kiwoom_utils.log_error(f"❌ [매도거절] 종목:{code}, 사유:{err_msg} (코드:{err_code})", config=config, send_telegram=True)
            return None
    except Exception as e:
        kiwoom_utils.log_error(f"🔥 [매도주문] 시스템 예외: {str(e)}", config=config, send_telegram=True)
        return None

def get_deposit(token, config=None):
    """
    [kt00001] 예수금 조회 - return_code 대응 수정
    """
    url = "https://api.kiwoom.com/api/dostk/acnt"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00001'
    }
    payload = {"qry_tp": "3"} 
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()
        is_success = data.get('rt_cd') == '0' or data.get('return_code') == 0
        if res.status_code == 200 and is_success:
            return int(data.get('ord_alow_amt', 0))
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            kiwoom_utils.log_error(f"❌ [예수금조회 실패] 사유: {err_msg}", config=config)
            return 0
    except: return 0