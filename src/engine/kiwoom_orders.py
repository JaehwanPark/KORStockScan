import requests
import json
import re

# 💡 Level 1 & 2 공통 모듈
from src.engine import sniper_config
from src.utils.logger import log_error, log_info
from src.utils.constants import TRADING_RULES
from src.core.event_bus import EventBus
from src.utils import kiwoom_utils
from src.engine.trade_pause_control import is_buy_side_paused, get_pause_state_label

# ==========================================
# 1. 계좌 및 자산 조회 API
# ==========================================
_LAST_INVENTORY_ERRORS = []
_LAST_DEPOSIT_OVERRIDE = None

def get_last_inventory_errors():
    """최근 잔고 조회 실패 원인을 반환합니다."""
    return list(_LAST_INVENTORY_ERRORS)

def calc_buy_qty(current_price, total_deposit, ratio=0.1, max_budget=None):
    """
    [v12.1] 예수금 대비 비중을 계산하여 정수 수량 산출
    """
    _, _, qty, _ = describe_buy_capacity(current_price, total_deposit, ratio, max_budget=max_budget)
    return qty


def describe_buy_capacity(current_price, total_deposit, ratio=0.1, safety_ratio=None, max_budget=None):
    """
    주문가능금액과 전략 비중을 바탕으로 실제 주문 가능 예산/수량을 설명합니다.
    """
    if current_price <= 0 or total_deposit <= 0:
        return 0, 0, 0, 0.0

    if safety_ratio is None:
        safety_ratio = getattr(TRADING_RULES, "BUY_BUDGET_SAFETY_RATIO", 0.95)
    safe_ratio = max(0.0, min(float(safety_ratio), 1.0))
    target_budget = max(float(total_deposit) * float(ratio), 0.0)
    if max_budget is not None:
        try:
            budget_cap = max(float(max_budget), 0.0)
        except (TypeError, ValueError):
            budget_cap = 0.0
        if budget_cap > 0:
            target_budget = min(target_budget, budget_cap)
    safe_budget = target_budget * safe_ratio  # 슬리피지 대비 95% 사용

    qty = int(safe_budget // current_price)
    used_ratio = safe_ratio

    if qty <= 0 and target_budget >= float(current_price):
        relaxed_ratio = max(
            safe_ratio,
            min(float(getattr(TRADING_RULES, "BUY_BUDGET_RELAXED_SAFETY_RATIO", 1.0) or 1.0), 1.0),
        )
        relaxed_budget = target_budget * relaxed_ratio
        relaxed_qty = int(relaxed_budget // current_price)
        if relaxed_qty > 0:
            safe_budget = relaxed_budget
            qty = relaxed_qty
            used_ratio = relaxed_ratio

    return int(target_budget), int(safe_budget), qty, float(used_ratio)


def _get_virtual_orderable_amount():
    """설정된 가상 주문가능금액이 있으면 반환합니다."""
    conf = getattr(sniper_config, "CONF", {}) or {}
    for key in ("VIRTUAL_ORDERABLE_AMOUNT", "FIXED_ORDERABLE_AMOUNT"):
        raw_value = conf.get(key, 0)
        try:
            amount = int(float(raw_value or 0))
        except (TypeError, ValueError):
            amount = 0
        if amount > 0:
            return amount, key
    return 0, None


def _log_virtual_orderable_amount_once(amount, key):
    global _LAST_DEPOSIT_OVERRIDE
    marker = (key, int(amount))
    if _LAST_DEPOSIT_OVERRIDE == marker:
        return
    log_info(
        f"💰 [주문가능금액] 가상 주문가능금액 사용 "
        f"({key}={int(amount):,}원)"
    )
    _LAST_DEPOSIT_OVERRIDE = marker


def get_deposit(token):
    """
    [kt00001] 예수금 조회 - return_code 대응 수정
    """
    virtual_amount, config_key = _get_virtual_orderable_amount()
    if virtual_amount > 0:
        _log_virtual_orderable_amount_once(virtual_amount, config_key)
        return virtual_amount

    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
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
            log_error(f"❌ [예수금조회 실패] 사유: {err_msg}")
            return 0
    except:
        return 0

def get_my_inventory(token):
    """
    [kt00018] 계좌평가잔고내역을 조회합니다.
    SOR 주문을 고려하여 KRX(한국거래소) 잔고를 우선 반영하고, 
    NXT(넥스트트레이드) 잔고 중복 종목은 무시하여 리스트를 구성합니다.
    """
    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
    token_preview = f"{str(token)[:6]}...{str(token)[-6:]}" if token else "None"
    log_info(f"🔎 [잔고조회] url={url}, token={token_preview}")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00018',
    }

    # 💡 [핵심] 종목 코드를 키(Key)로 사용하여 중복을 제거할 딕셔너리
    aggregated_inventory = {}
    successful_exchanges = set()
    exchanges = ['KRX', 'NXT']
    _LAST_INVENTORY_ERRORS.clear()
    
    for exchange in exchanges:
        params = {'qry_tp': '2', 'dmst_stex_tp': exchange}

        try:
            response = requests.post(url, headers=headers, json=params, timeout=5)
            data = response.json()
            
            if str(data.get('return_code', data.get('rt_cd', ''))) == '0':
                successful_exchanges.add(exchange)
                stock_list = data.get('acnt_evlt_remn_indv_tot', [])
                
                for item in stock_list:
                    raw_code = item.get('stk_cd', '')
                    code = raw_code[1:] if raw_code.startswith('A') else raw_code
                    qty = int(item.get('rmnd_qty', 0))
                    name = item.get('stk_nm', '')
                    
                    if qty > 0:
                        # 💡 [수정됨] KRX 데이터가 먼저 들어가고, NXT 조회 시 이미 딕셔너리에 있는 종목이면 무시(방어)합니다.
                        if code not in aggregated_inventory:
                            aggregated_inventory[code] = {'code': code, 'name': name, 'qty': qty}
            else:
                err_code = data.get('return_code', data.get('rt_cd', ''))
                err_msg = data.get('return_msg') or data.get('err_msg') or '알 수 없는 오류'
                log_info(f"⚠️ [API 경고] {exchange} 잔고 조회 실패: {err_msg}")
                _LAST_INVENTORY_ERRORS.append({
                    'exchange': exchange,
                    'http_status': response.status_code,
                    'return_code': err_code,
                    'return_msg': err_msg,
                })

        except Exception as e:
            log_error(f"❌ [API 에러] {exchange} 잔고 통신 실패: {e}")
            _LAST_INVENTORY_ERRORS.append({
                'exchange': exchange,
                'http_status': None,
                'return_code': None,
                'return_msg': str(e),
            })

    return list(aggregated_inventory.values()), successful_exchanges

# ==========================================
# 2. 주문 실행 API
# ==========================================
def _resolve_buy_order_type(order_type, price=0, tif=None):
    """
    Normalize legacy buy order request into Kiwoom order code + price.

    Project convention:
    - DAY limit: `00`
    - Best/marketable IOC: `16`
    - Market: `3`
    - Best: `6`

    NOTE:
    - Kiwoom IOC BUY requests are normalized to best-IOC (`16`).
    - The incoming limit price is advisory only and is discarded in payload.
    """
    tif_value = str(tif or "DAY").upper()
    requested_type = str(order_type or "6").upper()
    requested_price = int(price or 0)

    if tif_value == "IOC":
        if requested_type in {"00", "LIMIT", "6", "BEST", "16"}:
            if requested_price > 0:
                log_info(
                    f"[ENTRY_TIF_MAP] IOC buy request promoted to best-IOC(16); "
                    f"requested_limit_price={requested_price} is advisory only"
                )
            return "16", 0
        if requested_type in {"3", "MARKET"}:
            return "3", 0

    if requested_type in {"00", "LIMIT"}:
        return "00", requested_price
    if requested_type in {"3", "MARKET"}:
        return "3", 0
    if requested_type in {"16", "BEST_IOC"}:
        return "16", 0
    return str(order_type), requested_price


def send_buy_order_market(code, qty, token, order_type="6", price=0, tif=None):
    """
    [kt10000] 매수 주문 - return_code 대응 수정 및 지정가(00) 기능 추가
    - order_type: "00" (지정가 - 스캘핑 눌림목 그물망용)
                  "6"  (최유리지정가 - 기본값, 우량주 스윙용)
                  "3"  (시장가 - 강력한 추격 매수용)
    - price: 지정가 주문 시 입력할 1주당 단가 (시장가/최유리 지정가일 경우 0 또는 생략)
    """
    if qty <= 0: return None

    if is_buy_side_paused():
        clean_code = str(code)[:6]
        msg = f"[TRADING_PAUSED_BLOCK] buy order blocked 종목:{clean_code}, 상태:{get_pause_state_label()}"
        log_info(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return {
            "rt_cd": "PAUSED",
            "return_code": "PAUSED",
            "return_msg": get_pause_state_label(),
            "ord_no": "",
        }

    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10000'
    }

    normalized_type, normalized_price = _resolve_buy_order_type(order_type, price=price, tif=tif)
    ord_price_str = str(int(normalized_price)) if str(normalized_type) == "00" and normalized_price > 0 else ""

    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": clean_code,
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,
        "trde_tp": str(normalized_type),
        "cond_uv": ""
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        is_success = str(data.get('rt_cd', '')) == '0' or str(data.get('return_code', '')) == '0'

        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code', data.get('rt_cd', ''))
            
            # 💡 [핵심] 에러 로깅 후 EventBus로 텔레그램 발송 (Decoupling)
            msg = f"❌ [매수거절] 종목:{clean_code}, 사유:{err_msg} (코드:{err_code})"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return data # 에러 데이터를 그대로 반환하여 상위에서 처리하게 함
            
    except Exception as e:
        msg = f"🔥 [매수주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None

# -------------------------------------------------------------------
# Compatibility wrapper (legacy callers)
# -------------------------------------------------------------------
def send_buy_order(code, qty, price, order_type_code, token, order_type_desc=None, tif=None):
    """
    Legacy wrapper for send_buy_order_market.
    - order_type_code: "00" 지정가, "6" 최유리지정가, "3" 시장가
    - price: 지정가일 때만 사용
    """
    return send_buy_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type=str(order_type_code),
        price=price or 0,
        tif=tif,
    )

def send_sell_order_market(code, qty, token, order_type="3", price=0):
    """
    [kt10001] 주식 매도 주문 (시장가/지정가/최유리지정가 통합 지원)
    """
    if qty <= 0: return None

    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10001'
    }

    # 💡 [핵심] 지정가("00") 매도일 경우에만 단가(price)를 세팅합니다.
    ord_price_str = str(int(price)) if str(order_type) == "00" and price > 0 else ""

    payload = {
        "dmst_stex_tp": "SOR",
        "stk_cd": clean_code,
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,
        "trde_tp": str(order_type),
        "cond_uv": ""
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        is_success = str(data.get('rt_cd', '')) == '0' or str(data.get('return_code', '')) == '0'

        if res.status_code == 200 and is_success:
            return data
        else:
            err_msg = data.get('return_msg') or data.get('err_msg') or '상세 사유 없음'
            err_code = data.get('return_code', data.get('rt_cd', ''))
            
            # 📢 EventBus를 통한 에러 브로드캐스트
            msg = f"❌ [매도거절] 종목:{clean_code}, 사유:{err_msg} (코드:{err_code})"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return data
            
    except Exception as e:
        msg = f"🔥 [매도주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None

def send_cancel_order(code, orig_ord_no, token, qty=0):
    """
    [kt10003] 주식 취소 주문 - 미체결 물량 취소
    :param qty: 취소 수량. 기본값 0 (0 입력 시 미체결 잔량 전부 취소)
    """
    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt10003'  # 🚀 취소 전용 TR 명시
    }

    payload = {
        "dmst_stex_tp": "SOR",  # 국내거래소구분
        "orig_ord_no": str(orig_ord_no),  # 원주문번호
        "stk_cd": clean_code,  # 종목코드
        "cncl_qty": str(qty)  # 🚀 '0'이면 남은 물량 싹 다 취소!
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()

        if res.status_code == 200 and str(data.get('return_code', '')) == '0':
            cncl_qty_result = data.get('cncl_qty', '전량')
            new_ord_no = data.get('ord_no', '')
            print(f"✅ [취소접수] {clean_code} {cncl_qty_result}주 취소 성공 (새주문번호:{new_ord_no})")
            return data
        else:
            err_msg = data.get('return_msg', '상세 사유 없음')
            msg = f"❌ [취소거절] {clean_code}: {err_msg}"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return data

    except Exception as e:
        msg = f"🔥 [취소주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None

# ==========================================
# 3. 🚀 스마트 하이브리드 주문 (Sniper 엔진에서 호출)
# ==========================================
def send_smart_sell_order(code, qty, token, ws_data, reason_type):
    """
     [v14.0] 슬리피지 방어를 위한 스마트 매도 로직 (사유 기반 동적 시장가 전환)
    - LOSS, CLOSE: 긴급 탈출 -> 시장가(3)
    - MOMENTUM_DECAY, TRAILING: 빠른 익절 보장 -> 최유리지정가(6)
    - 기타(PROFIT, TIMEOUT): 1호가 잔량 확인 후 지정가(00) 우선 시도
    """
    if qty <= 0: return None

    # 1. 매수 1호가 데이터 추출 (kiwoom_websocket '0D' 구조 반영)
    try:
        orderbook = ws_data.get('orderbook', {})
        bids = orderbook.get('bids', [])
        
        if not bids:
            print(f"⚠️ [{code}] 호가 데이터가 없어 시장가(3)로 전환합니다.")
            return send_sell_order_market(code, qty, token, order_type="3")

        # 매수 1호가 정보 (bids[0] 이 가장 높은 매수 호가)
        bid_1_p = bids[0].get('price', 0)
        bid_1_q = bids[0].get('volume', 0)
        
    except (IndexError, KeyError, TypeError) as e:
        log_error(f"❌ [{code}] 호가 데이터 파싱 실패: {e}")
        return send_sell_order_market(code, qty, token, order_type="3")

    # 2. 매매 성격(reason_type)에 따른 주문 분기
    # 🚨 긴급 탈출(LOSS, CLOSE) : 절대 지정가 쓰지 않음. 시장가(3) 즉시 던짐.
    if reason_type in ['LOSS', 'CLOSE']:
        print(f"🚨 [긴급매도] {code}: 시장가(3) 매도 (사유: {reason_type}, 수량: {qty})")
        return send_sell_order_market(code, qty, token, order_type="3")

    # 💰 익절(PROFIT): 슬리피지 방어 가동
    # ⚠️ 모멘텀 급감, 트레일링 스탑 (MOMENTUM_DECAY, TRAILING) : 최유리지정가(6)로 시장가에 가깝게 즉시 체결 유도
    elif reason_type in ['MOMENTUM_DECAY', 'TRAILING']:
        print(f"⚠️ [시장가성 매도] {code}: 최유리지정가(6) 매도 (사유: {reason_type}, 수량: {qty})")
        return send_sell_order_market(code, qty, token, order_type="6")

    # 💰 일반 익절, 타임아웃 (PROFIT, TIMEOUT) : 지정가(00) 우선 시도, 안 되면 최유리지정가(6) (8:2 비율 중 2의 영역)

    else:
        # 매수 1호가 잔량이 내 물량보다 넉넉한지 확인 (2배 여유)
        if bid_1_p > 0 and bid_1_q >= qty * 2.0:
            print(f"💰 [스마트익절] {code}: 1호가({bid_1_p:,}원) 지정가 매도 (사유: {reason_type}, 호가잔량: {bid_1_q}주)")
            return send_sell_order_market(code, qty, token, order_type="00", price=bid_1_p)
        
        else:
            # 1호가 잔량이 부족하면 '최유리지정가(6)'로 던져서 슬리피지 최소화
            print(f"⚠️ [슬리피지방어] {code}: 1호가 잔량 부족. 최유리지정가(6) 매도")
            return send_sell_order_market(code, qty, token, order_type="6")

def reserve_buy_order_ai(code, ai_target_price, deposit, token, ratio=0.05):
    """
    [v12.9] AI 권장 타점을 바탕으로 지정가 매수 예약 주문을 전송합니다.
    """
    try:
        # 💡 [보완] 입력값이 비어있거나 'None'인 경우 즉시 탈출
        if not ai_target_price or str(ai_target_price).strip() == "":
            print(f"⚠️ [{code}] AI 예약가 데이터가 비어있습니다.")
            return None

        clean_price_str = re.sub(r'[^0-9]', '', str(ai_target_price))
        if not clean_price_str: # 숫자가 하나도 없는 경우 방어
            return None
            
        clean_price = int(clean_price_str)
        
        # 2. 유틸리티를 사용하여 호가 규격에 맞게 내림 정규화
        # AI가 준 가격이 19,950원인데 호가 단위가 100원이면 19,900원으로 맞춥니다.
        final_target_price = kiwoom_utils.get_target_price_by_percent(clean_price, drop_percent=0)
        
        if final_target_price <= 0:
            print(f"⚠️ [{code}] 유효하지 않은 예약가입니다.")
            return None

        # 3. 매수 수량 계산
        buy_qty = calc_buy_qty(final_target_price, deposit, ratio)
        
        if buy_qty <= 0:
            print(f"⚠️ [{code}] 예수금 부족으로 예약 주문을 생성할 수 없습니다.")
            return None

        # 4. 지정가(00) 주문 전송
        print(f"🎯 [AI 예약] {code}: {final_target_price:,}원에 {buy_qty}주 낚싯바늘 투척")
        return send_buy_order_market(
            code=code, 
            qty=buy_qty, 
            token=token, 
            order_type="00", # 지정가
            price=final_target_price
        )
        
    except Exception as e:
        print(f"❌ [예약주문 실패] {code}: {str(e)}")
        return None
