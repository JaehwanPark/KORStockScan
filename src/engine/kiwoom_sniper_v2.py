"""
================================================================================
💡 [KORStockScan 아키텍처 노트] Level 2: 하이브리드(Hybrid) 이벤트/데이터 처리 모델
================================================================================
본 스나이퍼 엔진은 시스템 결합도를 낮추면서도 초단타(SCALPING)의 극한 성능을 뽑아내기 위해 
두 가지 아키텍처 패턴을 혼용(Hybrid)하여 설계되었습니다.

1. 제어 흐름 (Control Flow) -> Event-Driven (Push 방식)
   - 텔레그램 발송, 스캐너의 신규 감시 지시, DB 상태 변경 알림 등은 `EventBus`를 통한 
     완벽한 Pub/Sub 모델을 적용하여 모듈 간 강결합을 제거했습니다.

2. 데이터 흐름 (Data Flow) -> Memory Snapshot & Polling (Pull 방식)
   - 초당 수백 번씩 쏟아지는 웹소켓 틱/호가 데이터를 EventBus에 싣게 되면, 
     이벤트 큐(Queue) 병목 현상과 파이썬 GIL 한계로 인해 치명적인 타점 지연(Latency)이 발생합니다.
   - 따라서 실시간 시장 데이터(`ws_data`)는 KiwoomWSManager가 내부 메모리(Dictionary)에 
     항상 '최신 상태만 덮어쓰기'를 하고, 스나이퍼 루프는 자신의 분석 템포에 맞춰 
     가장 신선한 데이터만 당겨오는(Pull) 방식을 고수합니다.
================================================================================
"""
import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
	
import os
import time
from datetime import datetime, time as dt_time
import threading   
import numpy as np
import pandas as pd
import json

# 💡 Level 1 & 2 공통 모듈 (경로 및 패키지 구조에 맞게 통일)
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.constants import TRADING_RULES, CREDENTIALS_PATH, CONFIG_PATH, DEV_PATH
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.utils.google_sheets_utils import GoogleSheetsManager
from src.database.models import RecommendationHistory

# 💡 뇌(AI)와 눈(웹소켓, 레이더) 임포트
from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.signal_radar import SniperRadar
from src.engine.ai_engine import GeminiSniperEngine
# from src.engine.ai_engine_openai import OpenAISniperEngine

# 스캐너 모듈 (장중 스캔 호출용)
import src.scanners.final_ensemble_scanner as final_ensemble_scanner

# --- [전역 상태 변수] -----------------------------------------------
highest_prices = {}
alerted_stocks = set()
cooldowns = {}  # 스캘핑 뇌동매매 방지용 쿨타임 관리

def load_system_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}

CONF = load_system_config()
KIWOOM_TOKEN = None
WS_MANAGER = None
AI_ENGINE = None  # 💡 [추가] AI 엔진을 전역으로 끌어올립니다.
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager()  
event_bus = EventBus() # 💡 [신규] 전역 이벤트 버스 장착!

global ACTIVE_TARGETS
ACTIVE_TARGETS = []
LAST_AI_CALL_TIMES = {}
LAST_LOG_TIMES = {}

# ==========================================
# ⚡ [S15 v2] Fast-Track 상태 관리
# ==========================================
FAST_SCALP_POOL = {}
FAST_TRADE_STATE = {}
FAST_REENTRY_BLOCK = {}
FAST_LOCK = threading.RLock()

# 💡 [스레드 안전성] 공유 상태 접근용 락
_state_lock = threading.RLock()

# 💡 [최적화] 매번 파싱(strptime)하지 않도록 주요 시간 객체를 미리 생성해둡니다.
TIME_07_00 = datetime.strptime("07:00:00", "%H:%M:%S").time()
TIME_09_00 = datetime.strptime("09:00:00", "%H:%M:%S").time()
TIME_09_03 = datetime.strptime("09:03:00", "%H:%M:%S").time()
TIME_09_05 = datetime.strptime("09:05:00", "%H:%M:%S").time()
TIME_09_10 = datetime.strptime("09:10:00", "%H:%M:%S").time()
TIME_10_30 = datetime.strptime("10:30:00", "%H:%M:%S").time()
TIME_11_00 = datetime.strptime("11:00:00", "%H:%M:%S").time()
TIME_15_30 = datetime.strptime("15:30:00", "%H:%M:%S").time()
TIME_20_00 = datetime.strptime("20:00:00", "%H:%M:%S").time()
TIME_23_59 = datetime.strptime("23:59:59", "%H:%M:%S").time()
# -------------------------------------------------------------------

def _in_time_window(now_value, start, end):
    return (start <= now_value <= end) if start <= end else (now_value >= start or now_value <= end)

def _now_ts():
    return time.time()

def _arm_s15_candidate(code, name, cnd_name, ttl_sec=180):
    now = _now_ts()
    with FAST_LOCK:
        FAST_SCALP_POOL[code] = {
            'name': name or code,
            'armed_at': now,
            'last_seen': now,
            'base_condition': cnd_name,
            'expires_at': now + ttl_sec,
        }
    try:
        _save_armed_candidate_to_db(code, name, cnd_name, now, now + ttl_sec)
    except Exception as e:
        log_error(f"🚨 S15 armed candidate DB 저장 실패 ({code}): {e}")

def _unarm_s15_candidate(code):
    with FAST_LOCK:
        FAST_SCALP_POOL.pop(code, None)
    _delete_armed_candidate_from_db(code)

def _save_armed_candidate_to_db(code, name, cnd_name, armed_at, expires_at):
    today = datetime.now().date()
    with DB.get_session() as session:
        record = session.query(RecommendationHistory).filter_by(
            rec_date=today,
            stock_code=code,
            strategy='S15_CANDID'
        ).first()
        if record:
            record.stock_name = name
            record.position_tag = 'S15_CANDID:' + cnd_name
            record.nxt = armed_at
            record.profit_rate = expires_at
        else:
            record = RecommendationHistory(
                rec_date=today,
                stock_code=code,
                stock_name=name,
                trade_type='SCALP',
                strategy='S15_CANDID',
                status='WATCHING',
                position_tag='S15_CANDID:' + cnd_name,
                prob=0.0,
                nxt=armed_at,
                profit_rate=expires_at,
                buy_price=0,
                buy_qty=0
            )
            session.add(record)

def _delete_armed_candidate_from_db(code):
    today = datetime.now().date()
    with DB.get_session() as session:
        session.query(RecommendationHistory).filter_by(
            rec_date=today,
            stock_code=code,
            strategy='S15_CANDID'
        ).delete()

def _restore_armed_candidates_from_db():
    """봇 재시작 시 DB에 저장된 S15_CANDID 후보들을 FAST_SCALP_POOL에 복원합니다."""
    today = datetime.now().date()
    now = _now_ts()
    with DB.get_session() as session:
        records = session.query(RecommendationHistory).filter_by(
            rec_date=today,
            strategy='S15_CANDID',
            status='WATCHING'
        ).all()
        for rec in records:
            code = rec.stock_code
            name = rec.stock_name
            cnd_name = rec.position_tag.replace('S15_CANDID:', '') if rec.position_tag else ''
            armed_at = rec.nxt if rec.nxt else 0.0
            expires_at = rec.profit_rate if rec.profit_rate else 0.0
            if expires_at < now:
                # 이미 만료된 후보는 DB에서 삭제
                session.query(RecommendationHistory).filter_by(
                    rec_date=today,
                    stock_code=code,
                    strategy='S15_CANDID'
                ).delete()
                continue
            with FAST_LOCK:
                FAST_SCALP_POOL[code] = {
                    'name': name or code,
                    'cnd_name': cnd_name,
                    'armed_at': armed_at,
                    'expires_at': expires_at
                }
        session.commit()

def _is_s15_armed(code):
    now = _now_ts()
    need_unarm = False
    with FAST_LOCK:
        item = FAST_SCALP_POOL.get(code)
        if not item:
            return False
        if item.get('expires_at', 0) < now:
            FAST_SCALP_POOL.pop(code, None)
            need_unarm = True
        else:
            return True
    if need_unarm:
        _unarm_s15_candidate(code)
    return False

def _is_s15_reentry_blocked(code):
    return FAST_REENTRY_BLOCK.get(code, 0) > _now_ts()

def _block_s15_reentry(code, seconds=60*60*6):
    FAST_REENTRY_BLOCK[code] = _now_ts() + seconds

def _get_fast_state(code):
    with FAST_LOCK:
        return FAST_TRADE_STATE.get(code)

def _set_fast_state(code, state):
    with FAST_LOCK:
        FAST_TRADE_STATE[code] = state

def _pop_fast_state(code):
    with FAST_LOCK:
        return FAST_TRADE_STATE.pop(code, None)

def _get_tick_size_for_price(price):
    if hasattr(kiwoom_utils, 'get_tick_size'):
        return int(kiwoom_utils.get_tick_size(price))
    if price < 2000:
        return 1
    if price < 5000:
        return 5
    if price < 20000:
        return 10
    if price < 50000:
        return 50
    if price < 200000:
        return 100
    if price < 500000:
        return 500
    return 1000

def _price_ticks_up(curr_price, ticks=2):
    price = int(curr_price)
    for _ in range(ticks):
        price += _get_tick_size_for_price(price)
    return int(price)

def _target_price_pct_up(avg_buy_price, pct=1.8):
    ideal = avg_buy_price * (1 + (pct / 100.0))
    price = int(avg_buy_price)
    while price < ideal:
        price += _get_tick_size_for_price(price)
    return int(price)

def _weighted_avg(amount, qty):
    if qty <= 0:
        return 0
    return int(amount / qty)

def create_s15_shadow_record(code, name):
    global DB
    try:
        with DB.get_session() as session:
            record = RecommendationHistory(
                rec_date=datetime.now().date(),
                stock_code=code,
                stock_name=name,
                buy_price=0,
                trade_type='SCALP',
                strategy='S15_FAST',
                status='WATCHING',
                position_tag='S15_FAST'
            )
            session.add(record)
            session.flush()
            return record.id
    except Exception as e:
        log_error(f"🚨 S15 shadow record 생성 실패 ({code}): {e}")
        return None

def update_s15_shadow_record(shadow_id, **kwargs):
    global DB
    if not shadow_id:
        return
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=shadow_id).first()
            if not record:
                return
            for k, v in kwargs.items():
                if hasattr(record, k):
                    setattr(record, k, v)
    except Exception as e:
        log_error(f"🚨 S15 shadow record 갱신 실패 ({shadow_id}): {e}")

def _send_s15_limit_buy(code, qty, price):
    return kiwoom_orders.send_buy_order_market(
        code=code,
        qty=qty,
        token=KIWOOM_TOKEN,
        order_type="00",
        price=int(price)
    )

def _send_s15_limit_sell(code, qty, price):
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=KIWOOM_TOKEN,
        order_type="00",
        price=int(price)
    )
def _send_s15_market_sell(code, qty):
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=KIWOOM_TOKEN,
        order_type="3"
    )
def _send_exit_best_ioc(code, qty, token):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    from src.engine import kiwoom_orders
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="16"  # 최유리(IOC)
    )
def _confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    """[공통 유틸] 주문 취소 후 실제 계좌 잔고를 재조회하여 팔아야 할 정확한 잔량(rem_qty) 반환"""
    import time
    from src.engine import kiwoom_orders

    # 1) orig_ord_no 가 있을 때만 취소 요청
    if orig_ord_no:
        kiwoom_orders.send_cancel_order(code=code, orig_ord_no=orig_ord_no, token=token, qty=0)
        time.sleep(0.5)  # 키움 서버 반영 대기

    # 2) 계좌 재조회 폴백
    try:
        real_inventory = kiwoom_orders.get_my_inventory(token)
        real_stock = next((item for item in (real_inventory or []) if str(item.get('code', '')).strip()[:6] == code), None)
        if real_stock:
            real_qty = int(float(real_stock.get('qty', 0) or 0))
            if real_qty > 0:
                return real_qty
    except Exception:
        pass

    # 3) 최종 폴백
    try:
        return max(0, int(expected_qty or 0))
    except Exception:
        return 0
def _extract_ord_no(res):
    if isinstance(res, dict):
        return str(res.get('ord_no', '') or res.get('odno', '') or '')
    return ''

def _is_ok_response(res):
    if isinstance(res, dict):
        return str(res.get('return_code', res.get('rt_cd', ''))) == '0'
    return bool(res)

def _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5):
    until = _now_ts() + wait_sec
    while _now_ts() < until:
        with state['lock']:
            rem_qty = max(0, state['cum_buy_qty'] - state['cum_sell_qty'])
        if rem_qty == 0:
            return 0
        time.sleep(0.05)
    try:
        inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
        real_stock = next((item for item in (inventory or []) if str(item.get('code', '')).strip()[:6] == code), None)
        if real_stock:
            return int(float(real_stock.get('qty', 0) or 0))
    except Exception as e:
        log_error(f"⚠️ S15 잔량 재조회 실패 ({code}): {e}")
    with state['lock']:
        return max(0, state['cum_buy_qty'] - state['cum_sell_qty'])

def execute_fast_track_scalp_v2(code, name, trigger_price, ratio=0.10):
    state = _get_fast_state(code)
    if not state:
        return
    try:
        cleanup_allowed = False
        actual_entry_happened = False
        rt_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        curr_price = int(float((rt_data or {}).get('curr', 0) or 0))
        if curr_price <= 0:
            curr_price = int(trigger_price or 0)
        if curr_price <= 0:
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        if AI_ENGINE is None:
            state['status'] = 'FAILED'
            log_error(f"🚨 S15 AI_ENGINE 미초기화 ({code})")
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        ai_res = AI_ENGINE.analyze_target(
            name,
            rt_data or {'curr': curr_price, 'orderbook': {'asks': [], 'bids': []}},
            ticks,
            recent_candles=[],
            strategy="SCALPING"
        )

        if ai_res.get('action') != 'BUY' or ai_res.get('score', 0) < 80:
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        buy_price = _price_ticks_up(curr_price, 2)
        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        req_qty = kiwoom_orders.calc_buy_qty(buy_price, deposit, ratio=ratio)
        if req_qty <= 0:
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        buy_res = _send_s15_limit_buy(code, req_qty, buy_price)
        if not _is_ok_response(buy_res):
            state['status'] = 'FAILED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        with state['lock']:
            state['status'] = 'BUY_SENT'
            state['buy_ord_no'] = _extract_ord_no(buy_res)
            state['req_buy_qty'] = req_qty
            state['updated_at'] = _now_ts()
        update_s15_shadow_record(state.get('shadow_id'), status='BUY_ORDERED')

        expire_at = _now_ts() + 20.0
        while _now_ts() < expire_at:
            with state['lock']:
                if state['cum_buy_qty'] >= req_qty:
                    break
            time.sleep(0.1)

        with state['lock']:
            real_buy_qty = state['cum_buy_qty']
            avg_buy_price = state['avg_buy_price']
            buy_ord_no = state.get('buy_ord_no', '')
        if real_buy_qty > 0:
            actual_entry_happened = True

        if real_buy_qty <= 0:
            cleanup_allowed = True
            if buy_ord_no:
                kiwoom_orders.send_cancel_order(code=code, orig_ord_no=buy_ord_no, token=KIWOOM_TOKEN, qty=0)
            state['status'] = 'CANCELLED'
            update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
            return

        if real_buy_qty < req_qty and buy_ord_no:
            kiwoom_orders.send_cancel_order(code=code, orig_ord_no=buy_ord_no, token=KIWOOM_TOKEN, qty=0)

        if avg_buy_price <= 0:
            avg_buy_price = buy_price

        target_price = _target_price_pct_up(avg_buy_price, 1.8)
        stop_price = int(avg_buy_price * (1 - 0.007))

        with state['lock']:
            state['status'] = 'HOLDING'
            state['target_price'] = target_price
            state['stop_price'] = stop_price
            state['updated_at'] = _now_ts()
        update_s15_shadow_record(
            state.get('shadow_id'),
            status='HOLDING',
            buy_price=avg_buy_price,
            buy_qty=real_buy_qty
        )

        sell_res = _send_s15_limit_sell(code, real_buy_qty, target_price)

        if not _is_ok_response(sell_res):
            print(f"🚨 [S15 Fail-safe] {name} 익절 지정가 매도 세팅 실패. 보호 상태 유지 후 최유리(IOC) 청산 시도.")
            with state['lock']:
                state['status'] = 'HOLDING_NEEDS_EXIT'
                state['updated_at'] = _now_ts()

            update_s15_shadow_record(
                state.get('shadow_id'),
                status='HOLDING'
            )

            rem_qty = _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.3)
            if rem_qty > 0:
                emergency_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                if _is_ok_response(emergency_res):
                    with state['lock']:
                        state['sell_ord_no'] = _extract_ord_no(emergency_res)
                        state['status'] = 'EXIT_RETRY'
                        state['updated_at'] = _now_ts()
                else:
                    print(f"🚨 [S15 Fail-safe] {name} 긴급 청산 주문도 실패. 상태 유지 및 관리자 알림 필요.")
            else:
                print(f"ℹ️ [S15 Fail-safe] {name} 재조회 결과 잔량 없음. 자연 종료 가능.")

            # 여기서 FAILED/EXPIRED/return 로 바로 끝내지 말 것

        with state['lock']:
            state['sell_ord_no'] = _extract_ord_no(sell_res)
            state['status'] = 'EXIT_SENT'
            state['updated_at'] = _now_ts()

        while True:
            time.sleep(0.1)

            with state['lock']:
                if state['cum_sell_qty'] >= state['cum_buy_qty'] > 0:
                    state['status'] = 'DONE'
                    cleanup_allowed = True
                    break

            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
            curr_p = int(float((rt or {}).get('curr', 0) or 0))
            if curr_p <= 0 or avg_buy_price <= 0:
                continue

            profit_rate = ((curr_p - avg_buy_price) / avg_buy_price) * 100
            if profit_rate <= -0.7:
                with state['lock']:
                    sell_ord_no = state.get('sell_ord_no', '')

                if sell_ord_no:
                    cancel_res = kiwoom_orders.send_cancel_order(
                        code=code, orig_ord_no=sell_ord_no, token=KIWOOM_TOKEN, qty=0
                    )
                    if _is_ok_response(cancel_res):
                        with state['lock']:
                            state['pending_cancel_ord_no'] = sell_ord_no

                rem_qty = _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5)
                if rem_qty > 0:
                    market_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                    if _is_ok_response(market_res):
                        with state['lock']:
                            state['sell_ord_no'] = _extract_ord_no(market_res) or state.get('sell_ord_no', '')
                            state['updated_at'] = _now_ts()
                break

        with state['lock']:
            final_buy = state['avg_buy_price']
            final_sell = state['avg_sell_price']
            final_qty = state['cum_buy_qty']

        final_profit_rate = 0.0
        if final_buy > 0 and final_sell > 0:
            final_profit_rate = round(((final_sell - final_buy) / final_buy) * 100, 2)

        update_s15_shadow_record(
            state.get('shadow_id'),
            status='COMPLETED',
            sell_price=final_sell or state.get('target_price', 0),
            sell_time=datetime.now(),
            profit_rate=final_profit_rate,
            buy_price=final_buy,
            buy_qty=final_qty
        )
    except Exception as e:
        log_error(f"🚨 S15 Fast-Track 에러 ({code}): {e}")
        update_s15_shadow_record(state.get('shadow_id'), status='EXPIRED')
    finally:
        if actual_entry_happened:
            _block_s15_reentry(code)
        _unarm_s15_candidate(code)
        if cleanup_allowed:
            _pop_fast_state(code)
def resolve_condition_profile(cnd_name):
    profile = {
        'strategy': 'SCALPING',
        'trade_type': 'SCALP',
        'is_next_day_target': False,
        'position_tag': 'MIDDLE',
        'start': None,
        'end': None,
    }

    if "scalp_candid_aggressive_01" in cnd_name or "scalp_candid_normal_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 0), dt_time(9, 30)
    elif "scalp_strong_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 20), dt_time(11, 0)
    elif "scalp_underpress_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 40), dt_time(13, 0)
    elif "scalp_shooting_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 40), dt_time(13, 30)
    elif "scalp_afternoon_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(13, 0), dt_time(15, 20)
    elif "kospi_short_swing_01" in cnd_name or "kospi_midterm_swing_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(14, 30), dt_time(15, 30)
        profile['strategy'] = 'KOSPI_ML'
        profile['trade_type'] = 'MAIN'
        profile['is_next_day_target'] = True
    elif "vcp_candid_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(15, 30), dt_time(7, 0)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'VCP_CANDID'
    elif "vcp_shooting_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 0), dt_time(15, 0)
        profile['position_tag'] = 'VCP_SHOOTING'
    elif "vcp_shooting_next_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(15, 30), dt_time(23, 59, 59)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'VCP_NEXT'
    elif "s15_scan_base" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 2), dt_time(10, 30)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'S15_CANDID'
    elif "s15_trigger_break" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 5), dt_time(11, 0)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'S15_SHOOTING'
    else:
        return None

    return profile

def get_condition_target_date(is_next_day_target):
    if not is_next_day_target:
        return datetime.now().date()

    import holidays

    kr_hols = holidays.KR(years=[datetime.now().year, datetime.now().year + 1])
    hol_dates = np.array([np.datetime64(d) for d in kr_hols.keys()], dtype='datetime64[D]')
    today_np = np.datetime64(datetime.now().date())
    next_bday_np = np.busday_offset(today_np, 1, holidays=hol_dates)
    return pd.to_datetime(next_bday_np).date()

def handle_condition_matched(payload):
    """실시간 조건검색(Push)으로 날아온 종목을 즉각 감시망(WATCHING)에 올립니다."""
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, event_bus

    code = str(payload.get('code', '')).strip()[:6]
    cnd_name = str(payload.get('condition_name', '') or '')
    if not code:
        return

    now_t = datetime.now().time()

    profile = resolve_condition_profile(cnd_name)
    if not profile:
        return

    if not _in_time_window(now_t, profile['start'], profile['end']):
        return

    target_strategy = profile['strategy']
    target_trade_type = profile['trade_type']
    is_next_day_target = profile['is_next_day_target']
    target_position_tag = profile['position_tag']

    # 당일 감시망에 이미 있으면 일반 케이스는 스킵
    # 단, VCP_SHOOTING은 기존 CANDID -> SHOOTING 승격이 있으므로 통과
    if any(str(t.get('code', '')).strip()[:6] == code for t in ACTIVE_TARGETS):
        if not is_next_day_target and target_position_tag != 'VCP_SHOOTING':
            return

    try:
        basic_info = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)
        name = basic_info.get('Name', code)
        target_date = get_condition_target_date(is_next_day_target)

        # =========================================================
        # ⚡ [S15 v2] Fast-Track 하이패스
        # =========================================================
        if target_position_tag == 'S15_CANDID':
            _arm_s15_candidate(code, name, cnd_name, ttl_sec=180)
            return

        if target_position_tag == 'S15_SHOOTING':
            if not _is_s15_armed(code):
                return
            if _is_s15_reentry_blocked(code):
                return
            if _get_fast_state(code):
                return

            shadow_id = create_s15_shadow_record(code, name)
            state = {
                'lock': threading.RLock(),
                'name': name,
                'status': 'ARMED',
                'buy_ord_no': '',
                'sell_ord_no': '',
                'pending_cancel_ord_no': '',
                'req_buy_qty': 0,
                'cum_buy_qty': 0,
                'cum_buy_amount': 0,
                'avg_buy_price': 0,
                'cum_sell_qty': 0,
                'cum_sell_amount': 0,
                'avg_sell_price': 0,
                'created_at': _now_ts(),
                'updated_at': _now_ts(),
                'target_price': 0,
                'stop_price': 0,
                'shadow_id': shadow_id,
                'trigger_price': 0,
            }
            _set_fast_state(code, state)

            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
            trigger_price = int(float((rt or {}).get('curr', 0) or 0))
            state['trigger_price'] = trigger_price

            threading.Thread(
                target=execute_fast_track_scalp_v2,
                args=(code, name, trigger_price, 0.10),
                daemon=False
            ).start()
            return
        # =========================================================

        print(f"🦅 [V3 헌터] 조건검색 0.1초 포착! {name}({code}) 감시망 편입 준비 (목표일: {target_date})")

        with DB.get_session() as session:
            # =====================================================
            # 1) VCP_SHOOTING: 전일 VCP_CANDID가 있어야 승격
            # =====================================================
            if target_position_tag == 'VCP_SHOOTING':
                candid_record = session.query(RecommendationHistory).filter_by(
                    rec_date=target_date,
                    stock_code=code,
                    position_tag='VCP_CANDID'
                ).first()

                if not candid_record:
                    return

                candid_record.position_tag = 'VCP_SHOOTING'
                candid_record.status = 'WATCHING'
                candid_record.strategy = 'SCALPING'
                candid_record.trade_type = 'SCALP'

                if not any(str(t.get('code', '')).strip()[:6] == code for t in ACTIVE_TARGETS):
                    new_target = {
                        'id': candid_record.id,
                        'code': code,
                        'name': name,
                        'strategy': 'SCALPING',
                        'status': 'WATCHING',
                        'added_time': time.time(),
                        'position_tag': 'VCP_SHOOTING'
                    }
                    ACTIVE_TARGETS.append(new_target)
                    event_bus.publish("COMMAND_WS_REG", {"codes": [code]})

                msg = (
                    f"🎯 **[VCP 돌파 포착]**\n"
                    f"종목: **{name} ({code})**\n"
                    f"전일 CANDID 포착 후 금일 슈팅 조건을 만족하여 스캘핑 감시망에 투입됩니다."
                )
                event_bus.publish(
                    'TELEGRAM_BROADCAST',
                    {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
                )
                return

            # =====================================================
            # 2) VCP_NEXT: 당일 SHOOTING 완료 종목만 다음날 예약
            # =====================================================
            elif target_position_tag == 'VCP_NEXT':
                today = datetime.now().date()
                today_record = session.query(RecommendationHistory).filter_by(
                    rec_date=today,
                    stock_code=code,
                    position_tag='VCP_SHOOTING'
                ).first()

                if not today_record:
                    return

                next_record = session.query(RecommendationHistory).filter_by(
                    rec_date=target_date,
                    stock_code=code
                ).first()

                if not next_record:
                    new_record = RecommendationHistory(
                        rec_date=target_date,
                        stock_code=code,
                        stock_name=name,
                        buy_price=0,
                        trade_type='SCALP',
                        strategy='SCALPING',
                        status='WATCHING',
                        position_tag='VCP_NEXT'
                    )
                    session.add(new_record)

                    msg = (
                        f"🌙 **[내일의 VCP 슈팅 예약]**\n"
                        f"종목: **{name} ({code})**\n"
                        f"금일 슈팅 후 강력한 마감 패턴을 보여 내일 시초가 매수를 예약합니다."
                    )
                    event_bus.publish(
                        'TELEGRAM_BROADCAST',
                        {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
                    )
                return

            # =====================================================
            # 3) 일반 로직 / VCP_CANDID 저장
            # =====================================================
            record = session.query(RecommendationHistory).filter_by(
                rec_date=target_date,
                stock_code=code
            ).first()

            newly_created = False
            if not record:
                record = RecommendationHistory(
                    rec_date=target_date,
                    stock_code=code,
                    stock_name=name,
                    buy_price=0,
                    trade_type=target_trade_type,
                    strategy=target_strategy,
                    status='WATCHING',
                    position_tag=target_position_tag
                )
                session.add(record)
                session.flush()
                newly_created = True
            else:
                # 기존 record가 있는데 position_tag가 비어 있거나 약한 값이면 보강
                if hasattr(record, 'position_tag') and target_position_tag not in [None, '', 'MIDDLE']:
                    record.position_tag = target_position_tag

            if not is_next_day_target:
                if not any(str(t.get('code', '')).strip()[:6] == code for t in ACTIVE_TARGETS):
                    new_target = {
                        'id': record.id,
                        'code': code,
                        'name': name,
                        'strategy': record.strategy or target_strategy,
                        'status': 'WATCHING',
                        'added_time': time.time(),
                        'position_tag': getattr(record, 'position_tag', target_position_tag) or target_position_tag
                    }
                    ACTIVE_TARGETS.append(new_target)

                event_bus.publish("COMMAND_WS_REG", {"codes": [code]})

            else:
                if newly_created:
                    if target_position_tag == 'VCP_CANDID':
                        msg = (
                            f"🌙 **[VCP 예비 후보 포착]**\n"
                            f"조건검색: `{cnd_name}`\n"
                            f"종목: **{name} ({code})**\n"
                            f"내일 오전 VCP 슈팅 조건 만족 시 감시망에 투입됩니다."
                        )

                    elif target_position_tag == 'S15_CANDID':
                        msg = (
                            f"🌙 **[S15 예비 후보 포착]**\n"
                            f"조건검색: `{cnd_name}`\n"
                            f"종목: **{name} ({code})**\n"
                            f"S15 슈팅 조건 만족 시 감시망에 투입됩니다."
                        )

                    else:
                        msg = (
                            f"🌙 **[내일의 스윙 주도주 예약]**\n"
                            f"조건검색 포착: `{cnd_name}`\n"
                            f"종목: **{name} ({code})**\n"
                            f"내일({target_date}) 감시망에 전략({target_strategy})으로 자동 투입됩니다."
                        )

                    event_bus.publish(
                        'TELEGRAM_BROADCAST',
                        {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
                    )
                    print(f"🌙 [{name}] 종가 무렵 포착 완료. 내일({target_date}) 감시 대상({target_strategy})으로 DB 예약 성공!")

    except Exception as e:
        log_error(f"🚨 조건검색 편입 처리 에러: {e}")



def handle_condition_unmatched(payload):
    """실시간 조건검색(D) 이탈 시 WATCHING 상태 대상을 즉시 제거합니다."""
    global DB, ACTIVE_TARGETS, event_bus

    code = str(payload.get('code', '')).strip()[:6]
    cnd_name = str(payload.get('condition_name', '') or '')
    if not code:
        return

    profile = resolve_condition_profile(cnd_name)
    if not profile:
        return

    if profile['position_tag'] == 'S15_CANDID':
        _unarm_s15_candidate(code)
        return

    if profile['position_tag'] == 'S15_SHOOTING':
        return

    target_date = get_condition_target_date(profile['is_next_day_target'])
    target_strategy = profile['strategy']
    target_position_tag = profile['position_tag']
    removed = False

    try:
        with DB.get_session() as session:
            query = session.query(RecommendationHistory).filter_by(
                rec_date=target_date,
                stock_code=code,
                status='WATCHING',
                strategy=target_strategy
            )

            if target_position_tag != 'MIDDLE':
                query = query.filter_by(position_tag=target_position_tag)

            records = query.all()
            for record in records:
                record.status = 'EXPIRED'
                removed = True

        retained_targets = []
        for target in ACTIVE_TARGETS:
            target_code = str(target.get('code', '')).strip()[:6]
            target_status = target.get('status')
            target_strategy_value = (target.get('strategy') or '').upper()
            normalized_strategy = 'SCALPING' if target_strategy_value in ['SCALPING', 'SCALP'] else target_strategy_value
            target_position = target.get('position_tag', 'MIDDLE')

            should_remove = (
                target_code == code and
                target_status == 'WATCHING' and
                normalized_strategy == target_strategy and
                target_position == target_position_tag
            )

            if should_remove:
                removed = True
                continue

            retained_targets.append(target)

        if removed:
            ACTIVE_TARGETS[:] = retained_targets

            still_tracking = any(
                str(t.get('code', '')).strip()[:6] == code and
                t.get('status') not in ['COMPLETED', 'EXPIRED']
                for t in ACTIVE_TARGETS
            )
            if not still_tracking:
                event_bus.publish("COMMAND_WS_UNREG", {"codes": [code]})

    except Exception as e:
        log_error(f"🚨 조건검색 이탈 처리 에러: {e}")


def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다."""
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS

    def to_int(value):
        try:
            return int(float(value or 0))
        except Exception:
            return 0

    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")

    real_inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
    if real_inventory is None:
        print("⚠️ [동기화 보류] 잔고 조회 API 통신에 실패하여 DB 동기화를 건너뜁니다.")
        return

    real_codes = {
        str(item.get('code', '')).strip()[:6]: item
        for item in real_inventory
        if item.get('code')
    }

    try:
        with DB.get_session() as session:
            db_holdings = session.query(RecommendationHistory).filter_by(status='HOLDING').all()

            for record in db_holdings:
                code = str(record.stock_code).strip()[:6]
                name = record.stock_name
                safe_db_qty = to_int(record.buy_qty)

                if code not in real_codes:
                    print(f"⚠️ [동기화] {name}({code}): 실제 잔고 0주. 상태를 COMPLETED로 강제 변경.")
                    record.status = 'COMPLETED'
                    if not record.sell_time:
                        record.sell_time = datetime.now()

                    target = next((t for t in ACTIVE_TARGETS if str(t.get('code', '')).strip()[:6] == code), None)
                    if target:
                        target['status'] = 'COMPLETED'
                else:
                    real_qty = to_int(real_codes[code].get('qty', 0))
                    if safe_db_qty != real_qty:
                        print(f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)")
                        record.buy_qty = real_qty

                    for t in ACTIVE_TARGETS:
                        if str(t.get('code', '')).strip()[:6] == code and real_qty > 0:
                            t['buy_qty'] = real_qty

    except Exception as e:
        log_error(f"🚨 DB 동기화 중 에러 발생: {e}")

    print("✅ [데이터 동기화] 완료. 봇 메모리가 실제 계좌와 완벽히 일치합니다.")


def sync_state_with_broker():
    """
    [Fallback 로직] 웹소켓 재접속 시 증권사 실제 잔고를 불러와
    누락된 체결 건(BUY_ORDERED -> HOLDING)을 강제로 동기화합니다.
    """
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, event_bus

    def to_int(value):
        try:
            return int(float(value or 0))
        except Exception:
            return 0

    print("🔄 [상태 동기화] 웹소켓 재접속 감지! 증권사 잔고와 봇 상태를 대조합니다...")

    real_balances = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
    if real_balances is None:
        print("⚠️ [상태 동기화] 잔고 조회 실패. 다음 턴에 재시도합니다.")
        return

    balance_dict = {
        str(item.get('code', '')).strip()[:6]: item
        for item in real_balances
        if item.get('code')
    }

    synced_count = 0

    try:
        with DB.get_session() as session:
            pending_records = session.query(RecommendationHistory).filter_by(status='BUY_ORDERED').all()

            for record in pending_records:
                code = str(record.stock_code).strip()[:6]

                if code in balance_dict:
                    real_data = balance_dict[code]
                    cur_qty = to_int(real_data.get('qty', 0))

                    if cur_qty > 0:
                        raw_price = (
                            real_data.get('buy_price')
                            or real_data.get('purchase_price')
                            or real_data.get('pchs_avg_pric')
                            or 0
                        )
                        buy_uv = to_int(raw_price)

                        print(f"✅ [동기화 완료] 누락 체결 확인! {record.stock_name}({code}) | 수량: {cur_qty} | 평단가: {buy_uv:,}원")

                        record.status = 'HOLDING'
                        record.buy_price = buy_uv
                        record.buy_qty = cur_qty
                        if not record.buy_time:
                            record.buy_time = datetime.now()

                        for t in ACTIVE_TARGETS:
                            if str(t.get('code', '')).strip()[:6] == code:
                                t['status'] = 'HOLDING'
                                t['buy_price'] = buy_uv
                                t['buy_qty'] = cur_qty

                        synced_count += 1

    except Exception as e:
        log_error(f"🚨 [상태 동기화] DB 처리 중 에러 발생: {e}")

    if synced_count > 0:
        msg = f"🔄 <b>[시스템 복구 알림]</b>\n웹소켓 단절 시간 동안 체결된 <b>{synced_count}건</b>의 종목을 성공적으로 동기화하여 감시망에 편입했습니다."
        event_bus.publish('TELEGRAM_BROADCAST', {'message': msg, 'audience': 'VIP_ALL', 'parse_mode': 'HTML'})
    else:
        print("✅ [상태 동기화] 누락된 체결 건이 없습니다.")



# =====================================================================
# 🔄 3분 주기 강제 계좌 동기화 (웹소켓 영수증 누락 방어)
# =====================================================================
def periodic_account_sync():
    """
    주기적으로 실제 증권사 잔고를 조회하여, 웹소켓 체결 누락으로 인해
    DB와 메모리가 꼬이는 현상을 강제로 바로잡습니다.
    """
    
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, highest_prices, _state_lock

    def to_int(value):
        try:
            return int(float(value or 0))
        except Exception:
            return 0

    real_inventory = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
    if real_inventory is None:
        return

    real_codes = {
        str(item.get('code', '')).strip()[:6]: item
        for item in real_inventory
        if item.get('code')
    }

    synced_count = 0

    try:
        with DB.get_session() as session:
            # 1️⃣ [매도 누락 방어] DB엔 HOLDING/SELL_ORDERED 인데, 실제 계좌엔 없는 경우 -> 팔렸음 (COMPLETED)
            active_records = session.query(RecommendationHistory).filter(
                RecommendationHistory.status.in_(['HOLDING', 'SELL_ORDERED'])
            ).all()

            for record in active_records:
                code = str(record.stock_code).strip()[:6]

                if code not in real_codes:
                    print(f"⚠️ [정기 동기화] {record.stock_name}({code}) 잔고 없음. 매도 영수증 누락으로 판단하여 COMPLETED 강제 전환.")
                    record.status = 'COMPLETED'
                    record.sell_time = datetime.now()

                    with _state_lock:
                        target_stock = next((t for t in ACTIVE_TARGETS if str(t.get('code', '')).strip()[:6] == code), None)
                        estimated_sell_price = target_stock.get('sell_target_price', 0) if target_stock else 0
                        fallback_price = record.buy_price if record.buy_price is not None else 0

                        if not record.sell_price or record.sell_price == 0:
                            record.sell_price = estimated_sell_price if estimated_sell_price > 0 else fallback_price

                        if record.buy_price and record.buy_price > 0 and record.sell_price and record.sell_price > 0:
                            record.profit_rate = round(((record.sell_price - record.buy_price) / record.buy_price) * 100, 2)

                        if target_stock:
                            target_stock['status'] = 'COMPLETED'

                        highest_prices.pop(code, None)
                    synced_count += 1

                else:
                    real_data = real_codes[code]
                    real_qty = to_int(real_data.get('qty', 0))

                    raw_price = (
                        real_data.get('buy_price')
                        or real_data.get('purchase_price')
                        or real_data.get('pchs_avg_pric')
                        or 0
                    )
                    real_buy_uv = to_int(raw_price)

                    if real_qty > 0 and to_int(record.buy_qty) != real_qty:
                        print(f"🔄 [정기 동기화] {record.stock_name} 수량 오차 교정 (기존: {to_int(record.buy_qty)}주 ➡️ 실제: {real_qty}주)")
                        record.buy_qty = real_qty
                        with _state_lock:
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['buy_qty'] = real_qty

                    if real_buy_uv > 0 and record.buy_price != real_buy_uv:
                        print(f"🔄 [정기 동기화] {record.stock_name} 매입단가 오차 교정 (기존: {record.buy_price}원 ➡️ 실제: {real_buy_uv}원)")
                        record.buy_price = real_buy_uv
                        with _state_lock:
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['buy_price'] = real_buy_uv

            # 2️⃣ [매수 누락 방어] DB엔 BUY_ORDERED 인데, 실제 잔고에 들어와 있는 경우 -> 샀음 (HOLDING)
            pending_records = session.query(RecommendationHistory).filter_by(status='BUY_ORDERED').all()

            for record in pending_records:
                code = str(record.stock_code).strip()[:6]

                if code in real_codes:
                    real_data = real_codes[code]
                    cur_qty = to_int(real_data.get('qty', 0))

                    if cur_qty > 0:
                        raw_price = (
                            real_data.get('buy_price')
                            or real_data.get('purchase_price')
                            or real_data.get('pchs_avg_pric')
                            or 0
                        )
                        buy_uv = to_int(raw_price)

                        print(f"⚠️ [정기 동기화] {record.stock_name}({code}) 매수 체결 확인! HOLDING 강제 전환 (평단가 {buy_uv:,}원)")

                        record.status = 'HOLDING'
                        record.buy_price = buy_uv
                        record.buy_qty = cur_qty
                        record.buy_time = datetime.now()

                        with _state_lock:
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['status'] = 'HOLDING'
                                    t['buy_price'] = buy_uv
                                    t['buy_qty'] = cur_qty

                        synced_count += 1

    except Exception as e:
        log_error(f"🚨 정기 계좌 동기화 DB 에러: {e}")

    if synced_count > 0:
        print(f"🔄 [정기 동기화 완료] 총 {synced_count}건의 웹소켓 누락 체결 상태를 바로잡았습니다.")
    else:
        pass  # 조용히 넘어갑니다. (로그 기록 안 함)


# --- [외부 요청용 분석 리포트 (텔레그램 봇 응답용)] ---
def analyze_stock_now(code):
    # 💡 [핵심 교정] 전역 변수 CONF와 DB를 추가로 가져옵니다.
    global KIWOOM_TOKEN, WS_MANAGER, event_bus, ACTIVE_TARGETS, CONF, DB, AI_ENGINE

    now_time = datetime.now().time()
    market_open = datetime.strptime("09:00:00", "%H:%M:%S").time()
    market_close = datetime.strptime("20:00:00", "%H:%M:%S").time()

    if not (market_open <= now_time <= market_close):
        return f"🌙 현재는 정규장 운영 시간(09:00~20:00)이 아닙니다.\n실시간 종목 분석은 장중에만 이용 가능합니다."

    if not WS_MANAGER:
        return "⏳ 시스템 초기화 중..."
    event_bus.publish("COMMAND_WS_REG", {"codes": [code]})

    try:
        from src.utils import kiwoom_utils
        stock_name = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)['Name']
    except:
        stock_name = code

    # ---------------------------------------------------------
    # 기존 대기 로직 (웹소켓 응답 대기 - 6초)
    ws_data = {}
    for _ in range(60):
        ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        if ws_data and ws_data.get('curr', 0) > 0:
            break
        time.sleep(0.1)

    # =========================================================
    # 💡 [핵심 폴백 로직] 웹소켓 데이터가 없으면 REST API로 강제 조회
    # =========================================================
    if not ws_data or ws_data.get('curr', 0) == 0:
        print(f"⚠️ [{stock_name}] 웹소켓 수신 지연. REST API(ka10003)로 폴백합니다.")
        try:
            from src.utils import kiwoom_utils
            # 가장 최근 1틱 데이터를 직접 조회하여 가격과 수급 상태를 강제로 가져옵니다.
            recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=1)

            if recent_ticks and len(recent_ticks) > 0:
                last_tick = recent_ticks[0]
                ws_data = {
                    'curr': last_tick.get('price', 0),
                    'fluctuation': last_tick.get('flu_rate', 0.0),
                    'volume': last_tick.get('acc_vol', 0),
                    'v_pw': last_tick.get('strength', 0.0),
                    'ask_tot': 0,  # REST 조회 시 호가창 잔량은 알 수 없으므로 0 처리
                    'bid_tot': 0,
                    'orderbook': {'asks': [], 'bids': []}
                }
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"🚨 REST API 폴백 실패: {e}")

    # 최종 검사: 그래도 데이터를 못 구했다면 진짜 거래정지거나 통신 장애
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ **{stock_name}**({code}) 호가창 수신 대기 중...\n(거래가 멈춰있거나 일시적인 통신 지연일 수 있습니다.)"
    # ---------------------------------------------------------

    curr_price = ws_data.get('curr', 0)
    fluctuation = float(ws_data.get('fluctuation', 0.0))
    today_vol = ws_data.get('volume', 0)
    v_pw = float(ws_data.get('v_pw', 0.0))
    ask_tot = int(ws_data.get('ask_tot', 0))
    bid_tot = int(ws_data.get('bid_tot', 0))

    # =========================================================
    # 💡 종목별 맞춤형 전략(Strategy) 파라미터 매핑
    # =========================================================
    target_info = next((t for t in ACTIVE_TARGETS if t['code'] == code), None)
    strategy = target_info.get('strategy', 'KOSPI_ML') if target_info else 'KOSPI_ML'

    if strategy in ['SCALPING', 'SCALP']:
        trailing_pct = getattr(TRADING_RULES, 'SCALP_TARGET', 1.5)
        stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -2.5)
        strat_label = "⚡ 초단타(SCALP)"
    elif strategy == 'KOSDAQ_ML':
        trailing_pct = getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0)
        stop_pct = getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.5)
        strat_label = "🚀 코스닥 스윙"
    else:
        trailing_pct = getattr(TRADING_RULES, 'TRAILING_START_PCT', 4.0)
        stop_pct = getattr(TRADING_RULES, 'STOP_LOSS_BULL', -3.0)
        strat_label = "🛡️ 우량주 스윙(KOSPI_ML)"

    target_price = int(curr_price * (1 + (trailing_pct / 100)))
    stop_price = int(curr_price * (1 + (stop_pct / 100)))
    target_reason = f"{strat_label} 기본 익절선 (+{trailing_pct}%)"
    vol_ratio = 0.0

    try:
        # 💡 [DB 1회 조회 최적화] 차트 저항대 분석과 거래량 비율을 동시에 계산
        df = DB.get_stock_data(code, limit=20)
        if df is not None and len(df) >= 10:
            avg_vol_20 = df['volume'].mean()
            if avg_vol_20 > 0:
                vol_ratio = (today_vol / avg_vol_20) * 100

            if strategy not in ['SCALPING', 'SCALP']:
                high_20d = df['high_price'].max()
                ma20 = df['close_price'].mean()
                std20 = df['close_price'].std()
                upper_bb = ma20 + (2 * std20)

                chart_resistance = max(high_20d, upper_bb)
                if chart_resistance > curr_price:
                    target_price = int(chart_resistance)
                    expected_rtn = ((target_price / curr_price) - 1) * 100
                    target_reason = f"차트 저항대 도달 (예상 +{expected_rtn:.1f}%)"
                else:
                    rally_pct = getattr(TRADING_RULES, 'RALLY_TARGET_PCT', 5.0)
                    target_price = int(curr_price * (1 + (rally_pct / 100)))
                    target_reason = f"신고가 돌파 랠리 (단기 추세 +{rally_pct}%)"
    except Exception as e:
        from src.utils.logger import log_error
        log_error(f"⚠️ 목표가/거래량 계산 중 에러: {e}")

    # =========================================================
    # 💡 실시간 프로그램 & 외인/기관 수급 조회
    # =========================================================
    prog_net_qty = 0
    foreign_net = 0
    inst_net = 0
    try:
        from src.utils import kiwoom_utils
        prog_data = kiwoom_utils.check_program_buying_ka90008(KIWOOM_TOKEN, code)
        prog_net_qty = prog_data.get('net_qty', 0)

        inv_df = kiwoom_utils.get_investor_daily_ka10059_df(KIWOOM_TOKEN, code)
        if not inv_df.empty:
            foreign_net = int(inv_df['Foreign_Net'].iloc[-1])
            inst_net = int(inv_df['Inst_Net'].iloc[-1])
    except Exception as e:
        print(f"⚠️ 수급 데이터 조회 지연: {e}")

    # 퀀트 스코어 계산
    from src.engine.signal_radar import SniperRadar
    score, prices, conclusion, checklist, metrics = SniperRadar.analyze_signal_integrated(ws_data, 0.5, 70)
    ratio_val = metrics.get('ratio_val', 0)

    # =========================================================
    # 💡 AI 주입용 데이터 포장 (Mega Quant Packet)
    # =========================================================
    quant_data_text = (
        f"- 현재가격: {curr_price:,}원 (전일비 {fluctuation:+.2f}%)\n"
        f"- 감시전략: {strat_label} (익절 {trailing_pct}% / 손절 {stop_pct}%)\n"
        f"- 기계목표가: {target_price:,}원 (사유: {target_reason})\n"
        f"- 누적거래량: {today_vol:,}주 (20일 평균대비 {vol_ratio:.1f}%)\n"
        f"- 실시간 체결강도: {v_pw:.1f}%\n"
        f"- 프로그램 순매수: {prog_net_qty:,}주\n"
        f"- 당일 가집계(외인/기관): 외인 {foreign_net:,}주 / 기관 {inst_net:,}주\n"
        f"- 호가 불균형: {'매도벽 우위(돌파기대)' if ask_tot > bid_tot else '매수벽 우위(하락방어)'} (매도잔량 {ask_tot:,} / 매수잔량 {bid_tot:,})\n"
        f"- 매수세(Ratio) 비중: {ratio_val:.1f}%\n"
        f"- 퀀트 확신점수: {score:.1f}점\n"
        f"- 퀀트 엔진 결론: {conclusion}"
    )

    # =========================================================
    # 💡 Gemini 3.0 Flash 호출
    # =========================================================
    ai_report = "⚠️ AI 리포트 생성 실패"
    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]

    if AI_ENGINE is None and api_keys:
        try:
            from src.engine.ai_engine import GeminiSniperEngine
            AI_ENGINE = GeminiSniperEngine(api_keys=api_keys)
        except Exception as e:
            ai_report = f"⚠️ AI 엔진 초기화 중 오류: {e}"

    if AI_ENGINE is not None:
        try:
            ai_report = AI_ENGINE.generate_realtime_report(stock_name, code, quant_data_text)
        except Exception as e:
            ai_report = f"⚠️ AI 리포트 생성 중 오류: {e}"
    elif not api_keys:
        ai_report = "⚠️ GEMINI_API_KEY 미설정으로 AI 리포트를 생성할 수 없습니다."

    # =========================================================
    # 💡 최종 리포트 출력 텍스트 조립
    # =========================================================
    bars = int(ratio_val / 10) if ratio_val > 0 else 0
    visual = f"📊 매수세: [{'🟥'*bars}{'⬜'*(10-bars)}] ({ratio_val:.1f}%)"
    prog_sign = "🔴" if prog_net_qty > 0 else "🔵"

    return (
        f"🔍 *{stock_name} ({code}) 실시간 분석*\n"
        f"💰 현재가: `{curr_price:,}원` ({fluctuation:+.2f}%)\n"
        f"🏷️ 감시전략: *{strat_label}*\n"
        f"🎯 기계 목표가: `{target_price:,}원`\n"
        f"   └ 📝 사유: *{target_reason}*\n"
        f"🔄 거래량: `평균대비 {vol_ratio:.1f}%`\n"
        f"{prog_sign} 프로그램: `{prog_net_qty:,}주`\n\n"
        f"🧠 **[Gemini 수석 트레이더 AI 브리핑]**\n"
        f"{ai_report}\n\n"
        f"📊 **[퀀트 소나 데이터]**\n"
        f"{visual}\n"
        f"📝 확신지수: `{score:.1f}점`\n"
        f"📝 퀀트결론: {conclusion}"
    )

def get_detailed_reason(code):
    # 💡 [핵심 교정 1] 전역 AI_ENGINE을 가져옵니다.
    global ACTIVE_TARGETS, KIWOOM_TOKEN, WS_MANAGER, AI_ENGINE, event_bus
    
    targets = ACTIVE_TARGETS
    target = next((t for t in targets if t['code'] == code), None)

    if not target: return f"🔍 `{code}` 종목은 현재 AI 감시 대상이 아닙니다."

    # Ensure websocket subscription
    if WS_MANAGER:
        event_bus.publish("COMMAND_WS_REG", {"codes": [code]})

    # Try to get websocket data with retry
    ws_data = None
    if WS_MANAGER:
        for _ in range(30):
            ws_data = WS_MANAGER.get_latest_data(code)
            if ws_data and ws_data.get('curr', 0) > 0:
                break
            time.sleep(0.1)
    
    # If still no data, fallback to REST API
    if not ws_data or ws_data.get('curr', 0) == 0:
        try:
            from src.utils import kiwoom_utils
            recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=1)
            if recent_ticks and len(recent_ticks) > 0:
                last_tick = recent_ticks[0]
                ws_data = {
                    'curr': last_tick.get('price', 0),
                    'fluctuation': last_tick.get('flu_rate', 0.0),
                    'volume': last_tick.get('acc_vol', 0),
                    'v_pw': last_tick.get('strength', 0.0),
                    'ask_tot': 0,
                    'bid_tot': 0,
                    'orderbook': {'asks': [], 'bids': []}
                }
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"REST API 폴백 실패 ({code}): {e}")
    
    if not ws_data or ws_data.get('curr', 0) == 0:
        return f"⏳ `{code}` 데이터 수신 중..."

    ai_prob = target.get('prob', 0.75)
    
    from src.engine.signal_radar import SniperRadar
    radar = SniperRadar(KIWOOM_TOKEN)
    score, prices, conclusion, checklist, metrics = radar.analyze_signal_integrated(ws_data, ai_prob)

    # 💡 [핵심 교정 2] AI 엔진을 호출하여 정성적 사유를 심층 분석합니다.
    ai_reason_str = "AI 심층 분석 대기 중 (또는 호출 불가)"
    if AI_ENGINE:
        from src.utils import kiwoom_utils
        recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)
        
        if recent_ticks:
            # AI에게 순간 분석을 의뢰합니다 (명령어 호출이므로 락이 걸려도 시도함)
            ai_decision = AI_ENGINE.analyze_target(target['name'], ws_data, recent_ticks, recent_candles)
            ai_action = ai_decision.get('action', 'WAIT')
            ai_reason = ai_decision.get('reason', '분석 사유 없음')
            ai_score_val = ai_decision.get('score', 50)
            ai_reason_str = f"[{ai_action}] ({ai_score_val}점) {ai_reason}"

    # 상태별 전환 실패 이유 분석 및 텔레그램 알림
    status = target.get('status')
    admin_id = target.get('admin_id')
    market_regime = CONF.get('MARKET_REGIME', 'BULL')
    failure_reason = None
    
    if status == 'WATCHING':
        failure_reason = check_watching_conditions(target, code, ws_data, admin_id, radar, AI_ENGINE)
    elif status == 'HOLDING':
        failure_reason = check_holding_conditions(target, code, ws_data, admin_id, market_regime, radar, AI_ENGINE)
    
    if failure_reason:
        telegram_msg = f"🚨 [상태 진단] {target['name']} ({code}) - {status} 상태 전환 실패: {failure_reason}"
        event_bus.publish("TELEGRAM_MESSAGE", {"message": telegram_msg})
    
    report = f"🧐 **[{target['name']}] 미진입 사유 상세 분석**\n━━━━━━━━━━━━━━━━━━\n"
    for label, status in checklist.items():
        icon = "✅" if status['pass'] else "❌"
        report += f"{icon} {label}: `{status['val']}`\n"

    # 상태 전환 실패 이유
    if failure_reason:
        report += f"🚨 **상태 전환 장애:** `{failure_reason}`\n\n"
    
    buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 80)
    report += f"━━━━━━━━━━━━━━━━━━\n"
    report += f"🎯 **기계적 수급 점수:** `{int(score)}점` (매수기준: {buy_threshold}점)\n"
    report += f"🤖 **AI 심층 판단:** `{ai_reason_str}`\n"
    report += f"📝 **최종 시스템 결론:** {conclusion}\n"
    
    return report

def get_realtime_ai_scores(codes):
    """
    [V14.0 신규] 외부(텔레그램) 요청 시 감시 중인 종목들의 실시간 AI 점수를 일괄 분석하여 반환합니다.
    """
    global KIWOOM_TOKEN, WS_MANAGER, AI_ENGINE, ACTIVE_TARGETS
    scores = {}
    
    if not AI_ENGINE or not WS_MANAGER or not KIWOOM_TOKEN:
        return scores
        
    # Bulk fetch websocket data
    ws_data_map = WS_MANAGER.get_all_data(codes)
    
    for code in codes:
        ws_data = ws_data_map.get(code)
        if not ws_data or ws_data.get('curr', 0) == 0:
            # 웹소켓 데이터가 없을 경우 REST API로 가볍게 1틱 폴백
            try:
                from src.utils import kiwoom_utils
                recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=1)
                if recent_ticks and len(recent_ticks) > 0:
                    last_tick = recent_ticks[0]
                    ws_data = {
                        'curr': last_tick.get('price', 0), 'fluctuation': last_tick.get('flu_rate', 0.0),
                        'volume': last_tick.get('acc_vol', 0), 'v_pw': last_tick.get('strength', 0.0),
                        'ask_tot': 0, 'bid_tot': 0, 'orderbook': {'asks': [], 'bids': []}
                    }
            except:
                pass

        if not ws_data or ws_data.get('curr', 0) == 0:
            continue
            
        target = next((t for t in ACTIVE_TARGETS if t['code'] == code), None)
        name = target['name'] if target else code
        
        try:
            from src.utils import kiwoom_utils
            ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
            candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)
            
            if ticks:
                ai_decision = AI_ENGINE.analyze_target(name, ws_data, ticks, candles)
                scores[code] = ai_decision.get('score', 50)
                
                # 스나이퍼 메모리에도 최신 점수로 업데이트 (겸사겸사)
                if target and scores[code] != 50:
                    target['rt_ai_prob'] = scores[code] / 100.0
        except Exception as e:
            from src.utils.logger import log_error, log_info
            log_error(f"실시간 일괄 AI 분석 에러 ({code}): {e}")
            
        time.sleep(0.3) # API 연속 호출 제재 방지
        
    return scores

# =====================================================================
# 🧠 상태 머신 (State Machine) 핸들러 
# =====================================================================
def handle_watching_state(stock, code, ws_data, admin_id, radar=None, ai_engine=None):
    """
    [WATCHING 상태] 진입 타점 감시 및 AI 교차 검증
    """
    global LAST_AI_CALL_TIMES

    # Debug logging
    log_info(f"[DEBUG] handle_watching_state 시작: {stock.get('name')} ({code}), 전략={stock.get('strategy')}, 위치태그={stock.get('position_tag')}, radar={'있음' if radar else '없음'}, ai_engine={'있음' if ai_engine else '없음'}")

    # Cache TRADING_RULES attributes for performance
    MAX_SCALP_SURGE_PCT = getattr(TRADING_RULES, 'MAX_SCALP_SURGE_PCT', 20.0)
    MAX_INTRADAY_SURGE = getattr(TRADING_RULES, 'MAX_INTRADAY_SURGE', 15.0)
    MIN_SCALP_LIQUIDITY = getattr(TRADING_RULES, 'MIN_SCALP_LIQUIDITY', 500_000_000)
    SNIPER_AGGRESSIVE_PROB = getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70)
    BUY_SCORE_THRESHOLD = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 70)
    VPW_STRONG_LIMIT = getattr(TRADING_RULES, 'VPW_STRONG_LIMIT', 120)
    INVEST_RATIO_SCALPING_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_SCALPING_MIN', 0.05)
    INVEST_RATIO_SCALPING_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_SCALPING_MAX', 0.25)
    VPW_SCALP_LIMIT = getattr(TRADING_RULES, 'VPW_SCALP_LIMIT', 120)
    AI_WATCHING_COOLDOWN = getattr(TRADING_RULES, 'AI_WATCHING_COOLDOWN', 60)
    VIP_LIQUIDITY_THRESHOLD = getattr(TRADING_RULES, 'VIP_LIQUIDITY_THRESHOLD', 1_000_000_000)
    AI_WAIT_DROP_COOLDOWN = getattr(TRADING_RULES, 'AI_WAIT_DROP_COOLDOWN', 300)
    MAX_SWING_GAP_UP_PCT = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
    VPW_KOSDAQ_LIMIT = getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105)
    VPW_STRONG_KOSDAQ_LIMIT = getattr(TRADING_RULES, 'VPW_STRONG_KOSDAQ_LIMIT', 120)
    BUY_SCORE_KOSDAQ_THRESHOLD = getattr(TRADING_RULES, 'BUY_SCORE_KOSDAQ_THRESHOLD', 80)
    INVEST_RATIO_KOSDAQ_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MIN', 0.05)
    INVEST_RATIO_KOSDAQ_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MAX', 0.15)
    AI_SCORE_THRESHOLD_KOSDAQ = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60)
    INVEST_RATIO_KOSPI_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MIN', 0.10)
    INVEST_RATIO_KOSPI_MAX = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MAX', 0.30)
    AI_SCORE_THRESHOLD_KOSPI = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSPI', 60)

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    pos_tag = stock.get('position_tag', 'MIDDLE')

    now = datetime.now()
    now_t = now.time()

    # 스캘핑은 9시 3분부터 시작하되, VCP_NEXT 예약 매수는 9시 정각 즉시 시작!
    if strategy == 'SCALPING':
        strategy_start = TIME_09_00 if pos_tag == 'VCP_NEXT' else TIME_09_03
    else:
        strategy_start = TIME_09_05

    if now_t < strategy_start:
        if now.second % 30 == 0:
            print(f"📡 [관찰/블라인드 모드] 차트 데이터(VWAP) 형성 대기 중... (목표: {strategy_start})")
        log_info(f"[DEBUG] {code} 시간 조건 불충족 (현재 {now_t}, 시작 {strategy_start})")
        return

    MAX_SURGE = MAX_SCALP_SURGE_PCT
    MAX_INTRADAY_SURGE = MAX_INTRADAY_SURGE
    MIN_LIQUIDITY = MIN_SCALP_LIQUIDITY

    if code in cooldowns and time.time() < cooldowns[code]:
        log_info(f"[DEBUG] {code} 쿨다운 중 (만료 시간 {cooldowns[code]})")
        return

    if strategy == 'SCALPING' and now_t >= TIME_15_30:
        log_info(f"[DEBUG] {code} SCALPING 15:30 이후 제외")
        return

    if code in alerted_stocks:
        log_info(f"[DEBUG] {code} 이미 alerted_stocks에 포함됨")
        return

    curr_price = int(float(ws_data.get('curr', 0) or 0))
    if curr_price <= 0:
        log_info(f"[DEBUG] {code} 현재가 유효하지 않음: {curr_price}")
        return

    current_vpw = float(ws_data.get('v_pw', 0) or 0)
    fluctuation = float(ws_data.get('fluctuation', 0.0) or 0.0)

    is_trigger = False
    msg = ""
    ratio = 0.10

    ai_prob = stock.get('prob', SNIPER_AGGRESSIVE_PROB)
    buy_threshold = BUY_SCORE_THRESHOLD
    strong_vpw = VPW_STRONG_LIMIT

    # 1️⃣ 초단타 (SCALPING) 전략
    if strategy == 'SCALPING':
        # 🚨 [방어막] VCP_CANDID 상태인 종목은 당일 슈팅 조건이 올 때까지 매수 금지 (대기)
        if pos_tag == 'VCP_CANDID':
            log_info(f"[DEBUG] {code} VCP_CANDID 태그로 인한 제외")
            return

        # AI 점수 기반 동적 투자 비율 계산
        current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        min_ratio = INVEST_RATIO_SCALPING_MIN
        max_ratio = INVEST_RATIO_SCALPING_MAX
        ratio = min_ratio + (current_ai_score / 100.0) * (max_ratio - min_ratio)

        ask_tot = int(float(ws_data.get('ask_tot', 0) or 0))
        bid_tot = int(float(ws_data.get('bid_tot', 0) or 0))
        open_price = float(ws_data.get('open', curr_price) or curr_price)

        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price

        # 🚨 [이중 방어막] 과매수 위험 차단 (로그 출력 없이 조용히 스킵)
        if fluctuation >= MAX_SURGE or intraday_surge >= MAX_INTRADAY_SURGE:
            log_info(f"[DEBUG] {code} 과매수 위험 차단 (fluctuation={fluctuation:.2f} >= {MAX_SURGE} 또는 intraday_surge={intraday_surge:.2f} >= {MAX_INTRADAY_SURGE})")
            return

        # 💡 [VCP_NEXT는 09:00 이후 시초가 예약 진입]
        if pos_tag == 'VCP_NEXT':
            stock['target_buy_price'] = curr_price
            is_trigger = True
            msg = (
                f"🚀 **{stock['name']} ({code}) VCP 시초가 예약 매수!**\n"
                f"현재가: `{curr_price:,}원` (전일 VCP NEXT 달성)"
            )
            stock['msg_audience'] = 'VIP_ALL'

        else:
            if radar is None:
                log_info(f"[DEBUG] {code} radar 객체 없음")
                return

            # 기본 조건
            if current_vpw < VPW_SCALP_LIMIT:
                log_info(f"[DEBUG] {code} VPW 불충족 (current_vpw={current_vpw:.1f} < VPW_SCALP_LIMIT)")
                return
            if liquidity_value < MIN_LIQUIDITY:
                log_info(f"[DEBUG] {code} 유동성 불충족 (liquidity_value={liquidity_value:,.0f} < MIN_LIQUIDITY={MIN_LIQUIDITY:,.0f})")
                return

            scanner_price = stock.get('buy_price') or 0
            if scanner_price > 0:
                gap_pct = (curr_price - scanner_price) / scanner_price * 100
                if gap_pct >= 1.5:
                    if code not in cooldowns:
                        print(f"⚠️ [{stock['name']}] 포착가 대비 너무 오름 (갭 +{gap_pct:.1f}%). 추격매수 포기.")
                        cooldowns[code] = time.time() + 1200
                    log_info(f"[DEBUG] {code} 포착가 대비 갭 상승 (gap_pct={gap_pct:.1f}% >= 1.5%)")
                    return

            # =========================================================
            # 💎 4. [핵심] AI 감시 종목 VIP 필터링 & 타점 계산 (Blocking Wait 적용)
            # =========================================================
            # 1. 이전 AI 점수를 기반으로 1차 타점 계산
            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            target_buy_price, used_drop_pct = radar.get_smart_target_price(
                curr_price,
                v_pw=current_vpw,
                ai_score=current_ai_score,
                ask_tot=ask_tot,
                bid_tot=bid_tot
            )

            last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
            time_elapsed = time.time() - last_ai_time
            is_vip_target = (target_buy_price > 0) and (curr_price <= target_buy_price * 1.015)

            if is_vip_target and last_ai_time == 0:
                print(f"⏳ [{stock['name']}] 첫 AI 분석을 시작합니다... (기계적 매수 일시 보류)")

            if ai_engine and is_vip_target and (time_elapsed > AI_WATCHING_COOLDOWN or last_ai_time == 0):
                ai_call_executed = False
                try:
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

                    if ws_data.get('orderbook') and recent_ticks:
                        ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)
                        ai_call_executed = True

                        action = ai_decision.get('action', 'WAIT')
                        ai_score = ai_decision.get('score', 50)
                        reason = ai_decision.get('reason', '사유 없음')

                        if ai_score != 50:
                            stock['rt_ai_prob'] = ai_score / 100.0
                            current_ai_score = ai_score
                            print(f"💎 [VIP AI 확답 완료: {stock['name']}] {action} | 점수: {ai_score}점 | {reason}")

                            if action == "BUY":
                                ai_msg = (
                                    f"🤖 <b>[VIP 종목 실시간 분석]</b>\n"
                                    f"🎯 종목: {stock['name']}\n"
                                    f"⚡ 행동: <b>{action} ({ai_score}점)</b>\n"
                                    f"🧠 사유: {reason}"
                                )
                                target_audience = 'VIP_ALL' if liquidity_value >= VIP_LIQUIDITY_THRESHOLD else 'ADMIN_ONLY'
                                event_bus.publish(
                                    'TELEGRAM_BROADCAST',
                                    {'message': ai_msg, 'audience': target_audience, 'parse_mode': 'HTML'}
                                )
                        else:
                            print(f"⚠️ [{stock['name']}] AI 판단 보류(Score 50). 기계적 로직으로 폴백합니다.")
                            current_ai_score = 50

                except Exception as e:
                    log_error(f"🚨 [AI 엔진 오류] {stock['name']}({code}): {e} | 기계적 매수 모드로 폴백(Fallback)합니다.")
                    current_ai_score = 50

                if ai_call_executed:
                    LAST_AI_CALL_TIMES[code] = time.time()

                # 첫 분석 턴은 "실제 AI 호출이 수행된 경우에만" 바로 진입하지 않고 다음 루프에서 확인
                if ai_call_executed and last_ai_time == 0:
                    log_info(f"[DEBUG] {code} 첫 AI 분석 턴 대기 (SCALPING)")
                    return

            # =========================================================
            # 🚨 5. AI 거부권 및 최종 매수 대기열(그물망) 투척
            # 💡 [핵심 교정] AI가 명확히 'BUY(75점 이상)'를 외치지 않으면 그물망을 던지지 않습니다!
            # (단, 서버 에러 등으로 인한 기계적 폴백 상태인 '50점'은 예외로 통과시킵니다)
            # =========================================================

            if current_ai_score < 75 and current_ai_score != 50:
                # 1. 로그 출력 (기존 유지)
                if time.time() - last_ai_time < 1.0:
                    action_str = "WAIT(진입 보류)" if current_ai_score > 40 else "DROP(진입 차단)"
                    print(f"🚫 [AI 매수 거부] {stock['name']} {action_str} (AI 점수: {current_ai_score}점)")

                # 💡 [수정] 74점 이하는 점수와 상관없이 모두 설정값(기본 300초) 적용
                cooldown_time = AI_WAIT_DROP_COOLDOWN

                cooldowns[code] = time.time() + cooldown_time
                log_info(f"[DEBUG] {code} AI 점수 불충족 (current_ai_score={current_ai_score} < 75)")
                return

            final_target_buy_price, final_used_drop_pct = radar.get_smart_target_price(
                curr_price,
                v_pw=current_vpw,
                ai_score=current_ai_score,
                ask_tot=ask_tot,
                bid_tot=bid_tot
            )

            stock['target_buy_price'] = final_target_buy_price
            is_trigger = True

            msg = (
                f"⚡ **{stock['name']} ({code}) 초단타(SCALP) 그물망 투척!**\n"
                f"현재가: `{curr_price:,}원` ➡️ **매수대기: `{final_target_buy_price:,}원` (-{final_used_drop_pct:.1f}% 눌림목)**\n"
                f"호가잔량대금: `{liquidity_value / 100_000_000:.1f}억` | 수급강도: `{current_vpw:.1f}%`"
            )
            stock['msg_audience'] = 'VIP_ALL' if liquidity_value >= VIP_LIQUIDITY_THRESHOLD else 'ADMIN_ONLY'

    # 2️⃣ & 3️⃣ 스윙(KOSDAQ_ML / KOSPI_ML) 통합 전략: AI 교차 검증 및 동적 비중 조절
    elif strategy in ['KOSDAQ_ML', 'KOSPI_ML']:
        if radar is None:
            log_info(f"[DEBUG] {code} radar 객체 없음 (KOSDAQ_ML/KOSPI_ML)")
            return

        # --- [1] 전략별 파라미터 세팅 ---
        if strategy == 'KOSDAQ_ML':
            max_gap = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
            if fluctuation >= max_gap:
                log_info(f"[DEBUG] {code} 갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})")
                return  # 갭상승이 너무 크면 패스

            vpw_limit_base = getattr(TRADING_RULES, 'VPW_KOSDAQ_LIMIT', 105)
            strong_vpw = getattr(TRADING_RULES, 'VPW_STRONG_KOSDAQ_LIMIT', 120)
            buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_KOSDAQ_THRESHOLD', 80)
            vpw_condition = current_vpw >= vpw_limit_base
            ratio_min = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MIN', 0.05)
            ratio_max = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MAX', 0.15)
            ai_score_threshold = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60)

            ai_prob = stock.get('prob', getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70))
            v_pw_limit = vpw_limit_base if ai_prob >= 0.70 else strong_vpw

        else:  # KOSPI_ML
            max_gap = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
            if fluctuation >= max_gap:
                log_info(f"[DEBUG] {code} 갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})")
                return  # 갭상승이 너무 크면 패스

            vpw_limit_base = 100
            strong_vpw = getattr(TRADING_RULES, 'VPW_STRONG_LIMIT', 105)
            buy_threshold = getattr(TRADING_RULES, 'BUY_SCORE_THRESHOLD', 70)
            vpw_condition = current_vpw >= 103
            ratio_min = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MIN', 0.10)
            ratio_max = getattr(TRADING_RULES, 'INVEST_RATIO_KOSPI_MAX', 0.30)
            ai_score_threshold = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSPI', 60)

            ai_prob = stock.get('prob', getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70))
            v_pw_limit = vpw_limit_base if ai_prob >= 0.70 else strong_vpw

        # --- [2] 기계적 퀀트 분석 ---
        score, prices, conclusion, checklist, metrics = radar.analyze_signal_integrated(ws_data, ai_prob)
        is_shooting = current_vpw >= v_pw_limit

        # --- [3] 퀀트가 '매수'를 외쳤을 때만 AI 등판 (API 비용/속도 최적화) ---
        if (score >= buy_threshold or is_shooting) and vpw_condition:

            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
            time_elapsed = time.time() - last_ai_time

            # 스윙 매매이므로 쿨타임을 5분(300초)으로 길게 잡습니다.
            if ai_engine and (time_elapsed > 300 or last_ai_time == 0):
                ai_call_executed = False
                try:
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

                    # 데이터 유효성 검사: 최소 20개 분봉 데이터 필요
                    if len(recent_candles) < 20:
                        print(f"⚠️ [{strategy} 데이터 부족] {stock['name']} 분봉 데이터 {len(recent_candles)}개. AI 호출 보류.")
                        # AI 호출 없이 계속 진행 (current_ai_score는 기존 값 유지)
                    else:
                        # 프로그램 수급 데이터 가져오기 (실시간 분석을 위해)
                        prog_data = kiwoom_utils.check_program_buying_ka90008(KIWOOM_TOKEN, code)
                        prog_net_qty = prog_data.get('net_qty', 0)

                        # AI 엔진 호출 시 program_net_qty 주입
                        ai_decision = ai_engine.analyze_target(
                            target_name=stock['name'],
                            ws_data=ws_data,
                            recent_ticks=recent_ticks,
                            recent_candles=recent_candles,
                            strategy=strategy,
                            program_net_qty=prog_net_qty
                        )
                        ai_call_executed = True

                        raw_ai_score = ai_decision.get('score', 50)
                        if raw_ai_score != 50:
                            stock['rt_ai_prob'] = raw_ai_score / 100.0
                            current_ai_score = raw_ai_score
                            print(f"💎 [{strategy} AI 승인 대기: {stock['name']}] 점수: {raw_ai_score}점 | {ai_decision.get('reason', '')}")

                except Exception as e:
                    log_error(f"🚨 [{strategy} AI 연동 오류] {stock['name']}({code}): {e}")

                if ai_call_executed:
                    LAST_AI_CALL_TIMES[code] = time.time()

                # 첫 분석 턴에는 "실제 AI 호출이 수행된 경우에만" 성급하게 사지 않고 다음 루프에서 한 번 더 확인합니다.
                if ai_call_executed and last_ai_time == 0:
                    log_info(f"[DEBUG] {code} 첫 AI 분석 턴 대기 (last_ai_time == 0)")
                    return

            # --- [4] AI 거부권 행사 (60점 미만이면 보류) ---
            if current_ai_score < ai_score_threshold and current_ai_score != 50:
                print(f"🚫 [{strategy} AI 매수 보류] {stock['name']} (AI 점수: {current_ai_score}점)")
                log_info(f"[DEBUG] {code} AI 점수 불충족 (current_ai_score={current_ai_score} < ai_score_threshold={ai_score_threshold})")
                cooldowns[code] = time.time() + 180  # 3분간 쳐다보지 않음
                return

            # --- [5] 동적 투자 비율(Position Sizing) 최종 계산 ---
            if current_ai_score == 50:
                # 에러 등으로 AI가 판단을 못 내린 폴백 상태 -> 중간 비중 적용
                ratio = (ratio_min + ratio_max) / 2
            else:
                # 60점 ~ 100점 사이에서 비중을 선형적으로 증가 (60점=Min비중, 100점=Max비중)
                score_weight = max(0.0, min(1.0, (current_ai_score - ai_score_threshold) / (100 - ai_score_threshold)))
                ratio = ratio_min + (score_weight * (ratio_max - ratio_min))

            is_trigger = True
            stock['target_buy_price'] = curr_price  # 스윙은 보통 최유리지정가/시장가로 긁으므로 현재가 기록

            msg = (
                f"🚀 **{stock['name']} ({code}) {strategy.replace('_', '\\_')} AI 스나이퍼 포착!**\n"
                f"현재가: `{curr_price:,}원` | 수급강도: `{current_vpw:.1f}%`\n"
                f"🧠 AI 확신도: `{current_ai_score}점` ➡️ **투자비중: `{ratio*100:.1f}%` 할당**"
            )

    # ==========================================
    # 🎯 매수 실행 공통 로직
    # ==========================================
    if is_trigger:
        if not admin_id:
            print(f"⚠️ [매수보류] {stock['name']}: 관리자 ID가 없습니다.")
            log_info(f"[DEBUG] {code} 관리자 ID 없음")
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        real_buy_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio)

        if real_buy_qty <= 0:
            print(f"⚠️ [매수보류] {stock['name']}: 매수 수량이 0주입니다. (자금 부족으로 20분 제외)")
            log_info(f"[DEBUG] {code} 매수 수량 0주 (자금 부족)")
            cooldowns[code] = time.time() + 1200
            return

        if strategy == 'SCALPING':
            order_type_code = "00"  # 지정가
            final_price = int(float(stock.get('target_buy_price', curr_price) or curr_price))
        else:
            order_type_code = "6"   # 최유리지정가
            final_price = 0

        res = kiwoom_orders.send_buy_order_market(
            code=code,
            qty=real_buy_qty,
            token=KIWOOM_TOKEN,
            order_type=order_type_code,
            price=final_price
        )

        is_success = False
        ord_no = ''

        if isinstance(res, dict):
            if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            elif strategy == 'SCALPING':
                cooldowns[code] = time.time() + 1200
        elif res:
            is_success = True

        if is_success:
            print(f"🛒 [{stock['name']}] 매수 주문 전송 완료. 체결 영수증 대기 중...")
            stock['pending_buy_msg'] = msg
            alerted_stocks.add(code)

            stock.update({
                'status': 'BUY_ORDERED',
                'order_price': final_price if final_price > 0 else curr_price,
                'buy_qty': real_buy_qty,
                'odno': ord_no,
                'order_time': time.time()
            })
            highest_prices[code] = curr_price

            try:
                with DB.get_session() as session:
                    record = session.query(RecommendationHistory).filter_by(id=stock['id']).first()
                    if record:
                        record.status = 'BUY_ORDERED'
                        record.buy_qty = real_buy_qty
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 상태 업데이트 실패: {e}")



def handle_holding_state(stock, code, ws_data, admin_id, market_regime, radar=None, ai_engine=None):
    """
    [HOLDING 상태] 보유 종목 익절/손절 감시 및 AI 조기 개입
    """
    global LAST_AI_CALL_TIMES

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy

    curr_p = int(float(ws_data.get('curr', 0) or 0))
    buy_p = float(stock.get('buy_price', 0) or 0)
    if curr_p <= 0 or buy_p <= 0:
        return

    if code not in highest_prices:
        highest_prices[code] = curr_p
    highest_prices[code] = max(highest_prices[code], curr_p)

    profit_rate = (curr_p - buy_p) / buy_p * 100
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100

    # 로깅: KOSPI_ML/KOSDAQ_ML 보유 종목 감시 로그 (10분 간격)
    if strategy in ('KOSPI_ML', 'KOSDAQ_ML'):
        last_log = LAST_LOG_TIMES.get(code, 0)
        if time.time() - last_log >= 600:  # 10 minutes
            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            log_info(f"[{strategy}] 보유 종목 감시 중: {stock['name']}({code}) 수익률 {profit_rate:+.2f}%, AI 점수 {current_ai_score:.0f}점")
            LAST_LOG_TIMES[code] = time.time()

    # 💡 [V15.1 신규] 일반 SCALPING(MIDDLE) 선제적 출구 엔진 (기존 로직 우회)
    if stock.get('exit_mode') == 'SCALP_PRESET_TP':
        # 중복 청산 방지
        if stock.get('exit_requested'):
            return

        profit_rate = (curr_p - buy_p) / buy_p * 100 if buy_p > 0 else 0.0
        orig_ord_no = stock.get('preset_tp_ord_no', '')
        expected_qty = stock.get('buy_qty', 0)

        # Case B: -0.7% 손절선 도달
        if profit_rate <= stock.get('hard_stop_pct', -0.7):
            print(f"🔪 [SCALP 출구엔진] {stock['name']} 손절선 터치({profit_rate:.2f}%). 즉각 최유리(IOC) 청산!")
            rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
            if rem_qty > 0:
                sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                stock['exit_requested'] = True
                stock['exit_order_type'] = '16'
                stock['exit_order_time'] = time.time()
                stock['sell_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
            stock['status'] = 'SELL_ORDERED'
            return

        # Case C: +0.8% 도달 시 AI 1회만 호출
        if profit_rate >= 0.8 and not stock.get('ai_review_done', False):
            print(f"🤖 [SCALP 출구엔진] {stock['name']} +0.8% 도달! AI 1회 검문 실시...")
            stock['ai_review_done'] = True

            if ai_engine:
                try:
                    recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                    ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, [], strategy="SCALPING")
                    ai_action = ai_decision.get('action', 'WAIT')
                    ai_score = ai_decision.get('score', 50)

                    stock['ai_review_action'] = ai_action
                    stock['ai_review_score'] = ai_score

                    if ai_action in ['SELL', 'DROP']:
                        print(f"🛑 [SCALP 출구엔진 AI] 모멘텀 둔화 감지. 1.5% 포기 후 즉시 최유리(IOC) 청산!")
                        rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
                        if rem_qty > 0:
                            sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                            stock['exit_requested'] = True
                            stock['exit_order_type'] = '16'
                            stock['exit_order_time'] = time.time()
                            stock['sell_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
                        stock['status'] = 'SELL_ORDERED'
                        return
                    else:
                        print(f"✅ [SCALP 출구엔진 AI] 돌파 모멘텀 유지(WAIT/BUY). 1.5% 유지, +0.3% 보호선 구축.")
                        stock['protect_profit_pct'] = 0.3

                except Exception as e:
                    print(f"⚠️ [SCALP 출구엔진 AI] 분석 실패: {e}. 기존 지정가 유지.")

        # Case D: +0.3% 보호선 이탈
        protect_pct = stock.get('protect_profit_pct')
        if protect_pct is not None and profit_rate <= protect_pct:
            print(f"🛡️ [SCALP 출구엔진] {stock['name']} +0.3% 보호선 이탈. 최유리(IOC) 약익절!")
            rem_qty = _confirm_cancel_or_reload_remaining(code, orig_ord_no, KIWOOM_TOKEN, expected_qty)
            if rem_qty > 0:
                sell_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                stock['exit_requested'] = True
                stock['exit_order_type'] = '16'
                stock['exit_order_time'] = time.time()
                stock['sell_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else stock.get('sell_ord_no')
            stock['status'] = 'SELL_ORDERED'
            return

        # 기존 무거운 AI/트레일링과 절대 충돌 금지
        return

    is_sell_signal = False
    sell_reason_type = "PROFIT"
    reason = ""

    now = datetime.now()
    now_t = now.time()

    # =========================================================
    # 🤖 [AI 보유 종목 실시간 감시] 문지기(Gatekeeper) 스무딩 적용
    # =========================================================
    last_ai_time = LAST_AI_CALL_TIMES.get(code, 0)
    current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100

    last_ai_profit = stock.get('last_ai_profit', profit_rate)
    price_change = abs(profit_rate - last_ai_profit)
    time_elapsed = time.time() - last_ai_time

    if strategy == 'SCALPING' and ai_engine and radar:
        safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
        is_critical_zone = (profit_rate >= safe_profit_pct) or (profit_rate < 0)

        dynamic_min_cd = 3 if is_critical_zone else getattr(TRADING_RULES, 'AI_HOLDING_MIN_COOLDOWN', 15)
        dynamic_max_cd = getattr(TRADING_RULES, 'AI_HOLDING_CRITICAL_COOLDOWN', 20) if is_critical_zone else getattr(TRADING_RULES, 'AI_HOLDING_MAX_COOLDOWN', 60)
        dynamic_price_trigger = 0.20 if is_critical_zone else 0.40
        
        if time_elapsed > dynamic_min_cd and (price_change >= dynamic_price_trigger or time_elapsed > dynamic_max_cd):
            try:
                recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
                recent_candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

                if ws_data.get('orderbook') and recent_ticks:
                    ai_decision = ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)
                    raw_ai_score = ai_decision.get('score', 50)

                    smoothed_score = int((current_ai_score * 0.6) + (raw_ai_score * 0.4))
                    stock['rt_ai_prob'] = smoothed_score / 100.0
                    stock['last_ai_profit'] = profit_rate
                    current_ai_score = smoothed_score

                    print(f"👁️ [AI 보유감시: {stock['name']}] 수익: {profit_rate:+.2f}% | AI: {current_ai_score:.0f}점 | 갱신주기: {dynamic_max_cd}초")

            except Exception as e:
                log_info(f"🚨 [보유 AI 감시 에러] {stock['name']}({code}): {e}")
            finally:
                LAST_AI_CALL_TIMES[code] = time.time()
    # =========================================================



    # 1️⃣ 초단타 (SCALPING) 전략 (V3 동적 트레일링 & AI 개입)
    if strategy == 'SCALPING':
        held_time_min = 0
        # --- [STEP 1] 보유 시간(held_time_min) 계산 ---
        if 'order_time' in stock and stock.get('order_time'):
            held_time_min = (time.time() - stock['order_time']) / 60
        elif stock.get('buy_time'):
            try:
                bt = stock['buy_time']
                if isinstance(bt, datetime):
                    b_dt = bt
                else:
                    bt_str = str(bt)
                    try:
                        b_dt = datetime.fromisoformat(bt_str)
                    except Exception:
                        b_time = datetime.strptime(bt_str, '%H:%M:%S').time()
                        b_dt = datetime.combine(datetime.now().date(), b_time)
                held_time_min = (datetime.now() - b_dt).total_seconds() / 60
            except Exception:
                pass

        # --- [STEP 2] 익절/손절 기준선 및 하락폭(Drawdown) 설정 ---
        base_stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -2.5)
        safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
        if highest_prices.get(code, 0) > 0:
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
        else:
            drawdown = 0

        # AI 점수에 따른 동적 파라미터 분기
        if current_ai_score >= 75:
            dynamic_stop_pct = base_stop_pct - 1.0
            dynamic_trailing_limit = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_STRONG', 0.8)
        else:
            dynamic_stop_pct = base_stop_pct
            dynamic_trailing_limit = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_WEAK', 0.4)

        # --- [STEP 3] 🧠 V3 매도 판단 실행 (우선순위 순서) ---
        
        # 1. 하드 리밋 (최우선: 물리적 손절선 이탈 시 자비 없이 컷)
        if profit_rate <= dynamic_stop_pct:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🔪 무호흡 칼손절 ({dynamic_stop_pct}%) [AI: {current_ai_score:.0f}]"

        # 2. AI 하방 리스크 조기 차단 (수익이 마이너스 구간일 때)
        elif profit_rate < 0 and current_ai_score <= 35:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🚨 AI 하방 리스크 포착 ({current_ai_score:.0f}점). 조기 손절 ({profit_rate:.2f}%)"

        # 3. 🎯 V3 동적 트레일링 익절 (수익이 안전 마진 이상일 때만 발동!)
        elif profit_rate >= safe_profit_pct:
            
            # 3-1. AI 모멘텀 둔화: 고점 대비 눌림을 기다릴 필요도 없이, AI가 가속도 죽었다고 판단하면 즉각 수익 실현
            if current_ai_score < 50:
                is_sell_signal = True
                sell_reason_type = "MOMENTUM_DECAY"
                reason = f"🤖 AI 틱 가속도 둔화 ({current_ai_score:.0f}점). 즉각 익절 (+{profit_rate:.2f}%)"
                
            # 3-2. 기계적 트레일링 방어: AI 점수(수급 강도)에 따라 타이트하게 혹은 여유롭게 익절폭 조절
            elif drawdown >= dynamic_trailing_limit:
                is_sell_signal = True
                sell_reason_type = "TRAILING"
                reason = f"🔥 고점 대비 밀림 (-{drawdown:.2f}%). 트레일링 익절 (+{profit_rate:.2f}%)"


        # 4. 시간 초과 및 장 마감 (가장 하위 우선순위)
        if not is_sell_signal:
            if held_time_min >= getattr(TRADING_RULES, 'SCALP_TIME_LIMIT_MIN', 30) and profit_rate >= getattr(TRADING_RULES, 'MIN_FEE_COVER', 0.1):
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = f"⏱️ {getattr(TRADING_RULES, 'SCALP_TIME_LIMIT_MIN', 30)}분 타임아웃 (순환매 우선)"
            elif now_t >= TIME_15_30 and profit_rate >= getattr(TRADING_RULES, 'MIN_FEE_COVER', 0.1):
                is_sell_signal = True
                sell_reason_type = "CLOSE"
                reason = "⏰ 장 마감 전 현금화"

                
    # 2️⃣ 코스닥 AI 스윙 (KOSDAQ_ML) 전용 전략
    elif strategy == 'KOSDAQ_ML':
        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= getattr(TRADING_RULES, 'KOSDAQ_HOLDING_DAYS', 2):
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = "⏳ 코스닥 스윙 기한 만료 청산"
        except Exception:
            pass

        if not is_sell_signal and peak_profit >= getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if drawdown >= 1.0:
                is_sell_signal = True
                sell_reason_type = "TRAILING"
                reason = f"🏆 KOSDAQ 트레일링 익절 (+{getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0)}% 돌파 후 하락)"

        elif not is_sell_signal and profit_rate <= getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0):
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 KOSDAQ 전용 방어선 이탈 ({getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0)}%)"


    # 3️⃣ 코스피 우량주 스윙 (KOSPI_ML 전용)
    elif strategy == 'KOSPI_ML':
        pos_tag = stock.get('position_tag', 'MIDDLE')
        if pos_tag == 'BREAKOUT':
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BREAKOUT')
            regime_name = "전고점 돌파"
        elif pos_tag == 'BOTTOM':
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BOTTOM')
            regime_name = "바닥 탈출"
        else:
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BULL') if market_regime == 'BULL' else getattr(TRADING_RULES, 'STOP_LOSS_BEAR')
            regime_name = "상승장" if market_regime == 'BULL' else "조정장"

        try:
            buy_date_str = stock.get('date', datetime.now().strftime('%Y-%m-%d'))
            buy_date = datetime.strptime(buy_date_str, '%Y-%m-%d').date()
            if np.busday_count(buy_date, datetime.now().date()) >= getattr(TRADING_RULES, 'HOLDING_DAYS'):
                is_sell_signal = True
                sell_reason_type = "TIMEOUT"
                reason = f"⏳ {getattr(TRADING_RULES, 'HOLDING_DAYS')}일 스윙 보유 만료"
        except Exception:
            pass

        # 익절 목표 도달 시 즉시 매도 (트레일링 없음)
        if not is_sell_signal and profit_rate >= getattr(TRADING_RULES, 'TRAILING_START_PCT'):
            is_sell_signal = True
            sell_reason_type = "PROFIT"
            reason = f"🎯 목표 수익률 도달 (+{getattr(TRADING_RULES, 'TRAILING_START_PCT')}%)"

        # 손절선 도달
        elif not is_sell_signal and profit_rate <= current_stop_loss:
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = f"🛑 손절선 도달 ({regime_name} 기준 {current_stop_loss}%)"

    # ==========================================
    # 🎯 매도 실행 공통 로직 (Smart Sell + ID 정밀 타격 버전)
    # ==========================================
    if is_sell_signal:
        sign = "📉 [손절 주문]" if sell_reason_type == 'LOSS' else "🎊 [익절 주문]"
        msg = (
            f"{sign} **{stock['name']} 매도 전송 ({strategy})**\n"
            f"사유: `{reason}`\n"
            f"현재가 기준 수익: `{profit_rate:+.2f}%` (고점: {peak_profit:.1f}%)"
        )

        is_success = False
        target_id = stock.get('id')

        # 수량 조회
        buy_qty = 0
        try:
            with DB.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                if record and record.buy_qty:
                    buy_qty = int(record.buy_qty)
        except Exception as e:
            print(f"🚨 [DB 조회 에러] ID {target_id} 수량 조회 실패: {e}")

        if buy_qty <= 0:
            buy_qty = int(float(stock.get('buy_qty', 0) or 0))

        if buy_qty <= 0:
            print(f"⚠️ [{stock['name']}] 고유 ID({target_id})의 수량이 0주입니다. 실제 키움 잔고로 폴백합니다...")
            real_inventory = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
            real_stock = next((item for item in (real_inventory or []) if str(item.get('code', '')).strip()[:6] == code), None)

            if real_stock and int(float(real_stock.get('qty', 0) or 0)) > 0:
                buy_qty = int(float(real_stock.get('qty', 0) or 0))
                stock['buy_qty'] = buy_qty
                print(f"🔄 [수량 폴백] 실제 계좌에서 총 잔고 {buy_qty}주를 매도합니다. (다중 매매건 합산 수량일 수 있음)")

        if not admin_id:
            print(f"🚨 [매도실패] {stock['name']}: 관리자 ID가 없습니다.")
            return

        if buy_qty <= 0:
            print(f"🚨 [매도실패] {stock['name']}: 실제 잔고도 0주입니다! 강제 완료(COMPLETED) 처리.")
            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "COMPLETED"})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} COMPLETED 전환 실패: {e}")

            stock['status'] = 'COMPLETED'
            highest_prices.pop(code, None)
            return

        # 장부 잠금
        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "SELL_ORDERED"})
        except Exception as e:
            print(f"🚨 [DB 에러] {stock['name']} SELL_ORDERED 장부 잠금 실패: {e}")

        stock['status'] = 'SELL_ORDERED'
        stock['sell_target_price'] = curr_p

        res = kiwoom_orders.send_smart_sell_order(
            code=code,
            qty=buy_qty,
            token=KIWOOM_TOKEN,
            ws_data=ws_data,
            reason_type=sell_reason_type
        )

        ord_no = ''

        if isinstance(res, dict):
            rt_cd = str(res.get('return_code', res.get('rt_cd', '')))
            if rt_cd == '0':
                is_success = True
                ord_no = str(res.get('ord_no', '') or res.get('odno', ''))
            else:
                print(f"❌ [매도거절] {stock['name']}: {res.get('return_msg')}")
        elif res:
            is_success = True

        if is_success:
            print(f"✅ [{stock['name']}] 매도 주문 전송 완료. 체결 영수증 처리 대기 중...")
            stock['pending_sell_msg'] = msg
            stock['sell_order_time'] = time.time()
            if ord_no:
                stock['sell_odno'] = ord_no

            if strategy == 'SCALPING' and now_t < TIME_15_30:
                cooldowns[code] = time.time() + 1200
                alerted_stocks.discard(code)
                print(f"♻️ [{stock['name']}] 스캘핑 청산 완료 후 20분 쿨타임 진입.")
        else:
            err_msg = res.get('return_msg', '') if isinstance(res, dict) else ''

            if '매도가능수량' in err_msg:
                print(f"🚨 [{stock['name']}] 잔고 0주(이미 매도됨). COMPLETED로 강제 전환.")
                new_status = 'COMPLETED'
            else:
                print(f"🚨 [{stock['name']}] 일시적 매도 실패! HOLDING으로 원상복구.")
                new_status = 'HOLDING'

            stock['status'] = new_status

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": new_status})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")
                log_info(f"🚨 [DB 에러] {stock['name']} 예외 상태({new_status}) 업데이트 실패: {e}")

            if new_status == 'COMPLETED':
                highest_prices.pop(code, None)



def check_watching_conditions(stock, code, ws_data, admin_id, radar=None, ai_engine=None):
    """
    WATCHING 상태 종목이 BUY_ORDERED로 전환되지 못하는 이유를 분석하여 문자열로 반환합니다.
    모든 조건을 통과하면 None을 반환합니다.
    """
    global LAST_AI_CALL_TIMES, cooldowns, alerted_stocks, highest_prices
    
    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    pos_tag = stock.get('position_tag', 'MIDDLE')
    
    now = datetime.now()
    now_t = now.time()
    
    # 시간 조건
    if strategy == 'SCALPING':
        strategy_start = TIME_09_00 if pos_tag == 'VCP_NEXT' else TIME_09_03
    else:
        strategy_start = TIME_09_05
    
    if now_t < strategy_start:
        return f"시간 조건 불충족 (현재 {now_t}, 시작 {strategy_start})"
    
    MAX_SURGE = getattr(TRADING_RULES, 'MAX_SCALP_SURGE_PCT', 20.0)
    MAX_INTRADAY_SURGE = getattr(TRADING_RULES, 'MAX_INTRADAY_SURGE', 15.0)
    MIN_LIQUIDITY = getattr(TRADING_RULES, 'MIN_SCALP_LIQUIDITY', 500_000_000)
    
    if code in cooldowns and time.time() < cooldowns[code]:
        return f"쿨다운 중 (만료 시간 {cooldowns[code]})"
    
    if strategy == 'SCALPING' and now_t >= TIME_15_30:
        return "SCALPING 15:30 이후 제외"
    
    if code in alerted_stocks:
        return "이미 alerted_stocks에 포함됨"
    
    curr_price = int(float(ws_data.get('curr', 0) or 0))
    if curr_price <= 0:
        return "현재가 유효하지 않음"
    
    current_vpw = float(ws_data.get('v_pw', 0) or 0)
    fluctuation = float(ws_data.get('fluctuation', 0.0) or 0.0)
    
    # 초단타 SCALPING 전략 검사
    if strategy == 'SCALPING':
        if pos_tag == 'VCP_CANDID':
            return "VCP_CANDID 태그로 인한 제외"
        
        ask_tot = int(float(ws_data.get('ask_tot', 0) or 0))
        bid_tot = int(float(ws_data.get('bid_tot', 0) or 0))
        open_price = float(ws_data.get('open', curr_price) or curr_price)
        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price
        
        if fluctuation >= MAX_SURGE or intraday_surge >= MAX_INTRADAY_SURGE:
            return f"과매수 위험 차단 (fluctuation={fluctuation:.2f} >= {MAX_SURGE} 또는 intraday_surge={intraday_surge:.2f} >= {MAX_INTRADAY_SURGE})"
        
        if pos_tag == 'VCP_NEXT':
            # VCP_NEXT는 별도 검사 없이 통과
            pass
        else:
            if radar is None:
                return "radar 객체 없음"
            if current_vpw < getattr(TRADING_RULES, 'VPW_SCALP_LIMIT', 120):
                return f"VPW 불충족 (current_vpw={current_vpw:.1f} < VPW_SCALP_LIMIT)"
            if liquidity_value < MIN_LIQUIDITY:
                return f"유동성 불충족 (liquidity_value={liquidity_value:,.0f} < MIN_LIQUIDITY={MIN_LIQUIDITY:,.0f})"
            
            scanner_price = stock.get('buy_price') or 0
            if scanner_price > 0:
                gap_pct = (curr_price - scanner_price) / scanner_price * 100
                if gap_pct >= 1.5:
                    return f"포착가 대비 갭 상승 (gap_pct={gap_pct:.1f}% >= 1.5%)"
            
            # AI 점수 체크
            current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
            if current_ai_score < 75 and current_ai_score != 50:
                return f"AI 점수 불충족 (current_ai_score={current_ai_score} < 75)"
    
    # 스윙 전략 검사 (KOSDAQ_ML / KOSPI_ML)
    elif strategy in ['KOSDAQ_ML', 'KOSPI_ML']:
        if radar is None:
            return "radar 객체 없음 (KOSDAQ_ML/KOSPI_ML)"
        
        max_gap = getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0)
        if fluctuation >= max_gap:
            return f"갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap})"
        
        # 추가 검사 생략 (복잡성으로 인해)
        # AI 점수 체크
        current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        ai_score_threshold = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60) if strategy == 'KOSDAQ_ML' else getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSPI', 60)
        if current_ai_score < ai_score_threshold and current_ai_score != 50:
            return f"AI 점수 불충족 (current_ai_score={current_ai_score} < ai_score_threshold={ai_score_threshold})"
    
    # 공통 관리자 ID 체크
    if not admin_id:
        return "관리자 ID 없음"
    
    # 매수 수량 체크 (자금 부족)
    deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
    ratio = stock.get('ratio', 0.1)  # 기본 비율
    real_buy_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio)
    if real_buy_qty <= 0:
        return "매수 수량 0주 (자금 부족)"
    
    # 모든 조건 통과
    return None


def check_holding_conditions(stock, code, ws_data, admin_id, market_regime, radar=None, ai_engine=None):
    """
    HOLDING 상태 종목이 SELL_ORDERED로 전환되지 못하는 이유를 분석하여 문자열로 반환합니다.
    모든 조건을 통과하면 None을 반환합니다.
    """
    global highest_prices
    
    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    
    curr_p = int(float(ws_data.get('curr', 0) or 0))
    buy_p = float(stock.get('buy_price', 0) or 0)
    if curr_p <= 0 or buy_p <= 0:
        return "현재가 또는 매수가 유효하지 않음"
    
    profit_rate = (curr_p - buy_p) / buy_p * 100
    if code in highest_prices:
        highest_prices[code] = max(highest_prices[code], curr_p)
    else:
        highest_prices[code] = curr_p
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100
    
    now_t = datetime.now().time()
    
    # 초단타 SCALPING 전략 검사
    if strategy == 'SCALPING':
        base_stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -2.5)
        safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
        drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100 if highest_prices[code] > 0 else 0
        
        # AI 점수 (간략화)
        current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        
        # 손절 조건
        if profit_rate <= base_stop_pct:
            return f"손절선 도달 (profit_rate={profit_rate:.2f}% <= {base_stop_pct}%)"
        
        # AI 하방 리스크
        if profit_rate < 0 and current_ai_score <= 35:
            return f"AI 하방 리스크 포착 (AI 점수 {current_ai_score:.0f})"
        
        # 익절 조건
        if profit_rate >= safe_profit_pct:
            if current_ai_score < 50:
                return f"AI 모멘텀 둔화 (AI 점수 {current_ai_score:.0f})"
            if drawdown >= getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_WEAK', 0.4):
                return f"고점 대비 밀림 (drawdown={drawdown:.2f}%)"
        
        # 시간 초과 및 장 마감
        held_time_min = 0  # 계산 생략
        if now_t >= TIME_15_30 and profit_rate >= getattr(TRADING_RULES, 'MIN_FEE_COVER', 0.1):
            return "장 마감 전 현금화"
    
    # 코스닥 스윙 전략 검사 (간략화)
    elif strategy == 'KOSDAQ_ML':
        if peak_profit >= getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100 if highest_prices[code] > 0 else 0
            if drawdown >= 1.0:
                return f"KOSDAQ 트레일링 익절 (peak_profit={peak_profit:.1f}%)"
        if profit_rate <= getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0):
            return f"KOSDAQ 손절선 도달 (profit_rate={profit_rate:.2f}%)"
    
    # 코스피 스윙 전략 검사 (간략화)
    else:
        pos_tag = stock.get('position_tag', 'MIDDLE')
        if pos_tag == 'BREAKOUT':
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BREAKOUT')
        elif pos_tag == 'BOTTOM':
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BOTTOM')
        else:
            current_stop_loss = getattr(TRADING_RULES, 'STOP_LOSS_BULL') if market_regime == 'BULL' else getattr(TRADING_RULES, 'STOP_LOSS_BEAR')
        
        if profit_rate <= current_stop_loss:
            return f"스윙 손절선 도달 (profit_rate={profit_rate:.2f}% <= {current_stop_loss}%)"
        
        if peak_profit >= getattr(TRADING_RULES, 'TRAILING_START_PCT'):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100 if highest_prices[code] > 0 else 0
            if drawdown >= getattr(TRADING_RULES, 'TRAILING_DRAWDOWN_PCT'):
                return f"스윙 트레일링 익절 (peak_profit={peak_profit:.1f}%)"
    
    # 관리자 ID 체크
    if not admin_id:
        return "관리자 ID 없음"
    
    # 모든 조건 통과
    return None


def handle_buy_ordered_state(stock, code):
    """
    주문 전송 후(BUY_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 로직을 호출합니다.
    """
    target_id = stock.get('id')
    order_time = stock.get('order_time', 0)
    time_elapsed = time.time() - order_time

    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy

    if stock.get('target_buy_price', 0) > 0:
        timeout_sec = getattr(TRADING_RULES, 'RESERVE_TIMEOUT_SEC', 1200)
    else:
        timeout_sec = 20 if strategy == 'SCALPING' else getattr(TRADING_RULES, 'ORDER_TIMEOUT_SEC', 30)

    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 매수 대기 {timeout_sec}초 초과. 취소 절차 진입.")
        orig_ord_no = stock.get('odno')

        # 원주문번호가 없는 경우
        if not orig_ord_no:
            stock['status'] = 'WATCHING'
            stock.pop('order_time', None)
            stock.pop('odno', None)
            stock.pop('pending_buy_msg', None)
            stock.pop('target_buy_price', None)
            stock.pop('order_price', None)
            stock.pop('buy_qty', None)
            highest_prices.pop(code, None)
            alerted_stocks.discard(code)

            if strategy == 'SCALPING':
                cooldowns[code] = time.time() + 1200

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({
                        "status": "WATCHING",
                        "buy_price": 0,
                        "buy_qty": 0
                    })
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 매수 타임아웃 복구 실패: {e}")
            return

        process_order_cancellation(stock, code, orig_ord_no, DB, strategy)
    
# =====================================================================
# 💸 매도 미체결(SELL_ORDERED) 타임아웃 감시 및 취소 로직
# =====================================================================
def handle_sell_ordered_state(stock, code):
    """
    주문 전송 후(SELL_ORDERED) 미체결 상태를 감시하고 타임아웃 시 취소 후 HOLDING으로 롤백합니다.
    """
    sell_order_time = stock.get('sell_order_time', 0)

    if sell_order_time == 0:
        stock['sell_order_time'] = time.time()
        return

    time_elapsed = time.time() - sell_order_time
    target_id = stock.get('id')
    timeout_sec = getattr(TRADING_RULES, 'SELL_TIMEOUT_SEC', 40)

    if time_elapsed > timeout_sec:
        print(f"⚠️ [{stock['name']}] 매도 대기 {timeout_sec}초 초과. 호가 꼬임/VI 의심 ➡️ 취소 후 HOLDING 롤백 절차 진입.")
        orig_ord_no = stock.get('sell_odno')

        if not orig_ord_no:
            print(f"🚨 [{stock['name']}] 취소할 원주문번호(odno)가 없습니다. 상태만 HOLDING으로 강제 롤백합니다.")
            stock['status'] = 'HOLDING'
            stock.pop('sell_order_time', None)
            stock.pop('sell_odno', None)
            stock.pop('pending_sell_msg', None)
            stock.pop('sell_target_price', None)

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
            except Exception as e:
                print(f"🚨 [DB 에러] {stock['name']} 매도 타임아웃 복구 실패: {e}")
            return

        process_sell_cancellation(stock, code, orig_ord_no, DB)

def process_sell_cancellation(stock, code, orig_ord_no, db):
    """미체결 매도 주문을 전량 취소하고 상태를 다시 HOLDING으로 되돌립니다."""
    target_id = stock.get('id')

    res = kiwoom_orders.send_cancel_order(
        code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0
    )

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    if is_success:
        print(f"✅ [{stock['name']}] 미체결 매도 주문 취소 성공! HOLDING(보유) 상태로 복귀합니다.")
        stock['status'] = 'HOLDING'
        stock.pop('sell_odno', None)
        stock.pop('sell_order_time', None)
        stock.pop('pending_sell_msg', None)
        stock.pop('sell_target_price', None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "HOLDING"})
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매도 취소 후 HOLDING 복구 실패: {e}")
        return True

    else:
        print(f"🚨 [{stock['name']}] 매도 취소 실패! (사유: {err_msg})")
        if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음', '체결']):
            print(f"💡 [{stock['name']}] 간발의 차이로 이미 매도 체결된 것으로 판단합니다. COMPLETED로 전환.")
            stock['status'] = 'COMPLETED'
            highest_prices.pop(code, None)

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({"status": "COMPLETED"})
            except Exception:
                pass
        return False

def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    """
    미체결 주문의 실제 취소 처리와 DB/메모리 청소를 담당합니다.
    고유 PK(id)를 사용하여 다중 매매 환경에서도 정확한 레코드를 타겟팅합니다.
    """
    target_id = stock.get('id')

    res = kiwoom_orders.send_cancel_order(
        code=code, orig_ord_no=orig_ord_no, token=KIWOOM_TOKEN, qty=0
    )

    is_success = False
    err_msg = str(res)

    if isinstance(res, dict):
        if str(res.get('return_code', res.get('rt_cd', ''))) == '0':
            is_success = True
        err_msg = res.get('return_msg', '사유 알 수 없음')
    elif res:
        is_success = True

    if is_success:
        print(f"✅ [{stock['name']}] 미체결 매수 취소 성공. 감시 상태로 복귀합니다.")
        stock['status'] = 'WATCHING'
        stock.pop('odno', None)
        stock.pop('order_time', None)
        stock.pop('pending_buy_msg', None)
        stock.pop('target_buy_price', None)
        stock.pop('order_price', None)
        stock.pop('buy_qty', None)
        highest_prices.pop(code, None)

        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter_by(id=target_id).update({
                    "status": "WATCHING",
                    "buy_price": 0,
                    "buy_qty": 0
                })
        except Exception as e:
            log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 후 WATCHING 복구 실패: {e}")

        if strategy in ['SCALPING', 'SCALP']:
            alerted_stocks.discard(code)
            cooldowns[code] = time.time() + 1200
            print(f"♻️ [{stock['name']}] 스캘핑 취소 완료. 20분 쿨타임 진입.")
        return True

    else:
        print(f"🚨 [{stock['name']}] 매수 취소 실패! (사유: {err_msg})")
        if any(keyword in err_msg for keyword in ['취소가능수량', '잔고', '주문없음']):
            print(f"💡 [{stock['name']}] 이미 전량 체결된 것으로 판단. HOLDING으로 전환.")
            stock['status'] = 'HOLDING'

            try:
                with DB.get_session() as session:
                    session.query(RecommendationHistory).filter_by(id=target_id).update({
                        "status": "HOLDING"
                    })
            except Exception as e:
                log_error(f"🚨 [DB 에러] {stock['name']} 매수 취소 실패 후 HOLDING 전환 실패: {e}")

        return False

# ==========================================
# 💡 실시간 체결 영수증 처리 (콜백 함수)
# ==========================================
def _find_execution_target(code, exec_type, order_no):
    normalized_order_no = str(order_no or '').strip()

    if exec_type == 'BUY':
        status_key = 'BUY_ORDERED'
        order_key = 'odno'
    else:
        status_key = 'SELL_ORDERED'
        order_key = 'sell_odno'

    status_candidates = [
        stock for stock in ACTIVE_TARGETS
        if str(stock.get('code', '')).strip()[:6] == code and stock.get('status') == status_key
    ]

    if normalized_order_no:
        exact_match = next(
            (
                stock for stock in status_candidates
                if str(stock.get(order_key, '')).strip() == normalized_order_no
            ),
            None
        )
        if exact_match:
            return exact_match

    if len(status_candidates) == 1:
        return status_candidates[0]

    return None


def _update_db_for_buy(target_id, exec_price, now, target_stock):
    """비동기로 실행되는 BUY 체결 DB 업데이트 및 알림"""
    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update({
                "buy_price": exec_price,
                "status": "HOLDING",
                "buy_time": now
            })

        print(f"✅ [영수증: ID {target_id}] {target_stock.get('code')} 실제 매수 체결가 {exec_price:,}원 및 시간 반영 완료!")

        pending_msg = target_stock.get('pending_buy_msg')
        audience = target_stock.get('msg_audience', 'VIP_ALL')
        if pending_msg:
            final_msg = pending_msg.replace("그물망 투척!", "그물망 매수 체결!").replace("스나이퍼 포착!", "스나이퍼 매수 체결!")
            final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원`"
            event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'Markdown'})
        else:
            event_bus.publish(
                'TELEGRAM_BROADCAST',
                {'message': f"🛒 **[{target_stock.get('name')}]** 매수 체결 완료!\n체결가: `{exec_price:,}원`", 'audience': audience, 'parse_mode': 'Markdown'}
            )
        # 메모리에서 pending_buy_msg 제거 (스레드에서 제거)
        target_stock.pop('pending_buy_msg', None)
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} BUY 처리 중 에러: {e}")


def _update_db_for_sell(target_id, exec_price, now, target_stock, strategy, is_scalp_revive):
    """비동기로 실행되는 SELL 체결 DB 업데이트 및 알림 (스캘핑 부활 제외)"""
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return

            safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
            if safe_buy_price > 0:
                profit_rate = round(((exec_price - safe_buy_price) / safe_buy_price) * 100, 2)
            else:
                profit_rate = 0.0
                print(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")

            record.status = 'COMPLETED'
            record.sell_price = exec_price
            record.sell_time = now
            record.profit_rate = profit_rate

            print(f"🎉 [매매 완료: ID {target_id}] {target_stock.get('code')} 실매도가: {exec_price:,}원 / 수익률: {profit_rate}%")

            pending_msg = target_stock.get('pending_sell_msg')
            audience = target_stock.get('msg_audience', 'VIP_ALL')
            if pending_msg:
                final_msg = pending_msg.replace("매도 전송", "매도 체결 완료").replace("[익절 주문]", "[익절 완료]").replace("[손절 주문]", "[손절 완료]")
                final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원` (확정 수익률: `{profit_rate:+.2f}%`)"
                event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'Markdown'})
            else:
                sign = "🎊 [익절 완료]" if profit_rate > 0 else "📉 [손절 완료]"
                event_bus.publish(
                    'TELEGRAM_BROADCAST',
                    {'message': f"{sign} **[{target_stock.get('name')}]** 매도 체결!\n체결가: `{exec_price:,}원`\n수익률: `{profit_rate:+.2f}%`", 'audience': audience, 'parse_mode': 'Markdown'}
                )
            # 메모리에서 pending_sell_msg 제거
            target_stock.pop('pending_sell_msg', None)
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")


def handle_real_execution(exec_data):
    """
    웹소켓에서 주문 체결(00) 통보가 오면 이 함수가 즉시 실행됩니다.
    고유 ID(id)를 추적하여 해당 매매 건의 실제 체결가를 정확히 기록합니다.
    """
    code = str(exec_data.get('code', '')).strip()[:6]
    exec_type = str(exec_data.get('type', '')).upper()
    order_no = str(exec_data.get('order_no', '') or '').strip()

    try:
        exec_price = int(float(exec_data.get('price', 0) or 0))
    except Exception:
        exec_price = 0

    try:
        exec_qty = int(float(exec_data.get('qty', 0) or 0))
    except Exception:
        exec_qty = 0

    if not code or exec_price <= 0:
        return

    state = _get_fast_state(code)
    if state and exec_qty > 0:
        with state['lock']:
            matched = False

            if exec_type == 'BUY':
                if order_no and order_no == str(state.get('buy_ord_no', '')):
                    state['cum_buy_qty'] += exec_qty
                    state['cum_buy_amount'] += exec_price * exec_qty
                    state['avg_buy_price'] = _weighted_avg(state['cum_buy_amount'], state['cum_buy_qty'])
                    state['updated_at'] = _now_ts()
                    matched = True

            elif exec_type == 'SELL':
                valid_sell_ord_nos = {
                    str(state.get('sell_ord_no', '') or ''),
                    str(state.get('pending_cancel_ord_no', '') or ''),
                }
                if order_no and order_no in valid_sell_ord_nos:
                    state['cum_sell_qty'] += exec_qty
                    state['cum_sell_amount'] += exec_price * exec_qty
                    state['avg_sell_price'] = _weighted_avg(state['cum_sell_amount'], state['cum_sell_qty'])
                    state['updated_at'] = _now_ts()
                    matched = True

        if matched:
            return

    now = datetime.now()
    now_t = now.time()

    target_stock = _find_execution_target(code, exec_type, order_no)
    if not target_stock:
        print(f"[EXEC_IGNORED] no matching active order. code={code}, type={exec_type}, order_no={order_no}")
        return

    target_id = target_stock.get('id')
    if not target_id:
        print(f"🚨 [영수증] 종목 {code}의 고유 ID가 메모리에 없습니다. DB 업데이트가 불가능합니다.")
        return

    new_watch_id = None
    is_scalp_revive = False
    
    # ==========================================
    # 1️⃣ DB 상태 업데이트 (ID 기반 정밀 타격)
    # ==========================================
    if exec_type == 'BUY':
        # 먼저 메모리 업데이트
        target_stock['status'] = 'HOLDING'
        target_stock['buy_price'] = exec_price
        target_stock['buy_time'] = now
        highest_prices[code] = exec_price

        raw_strategy = (target_stock.get('strategy') or 'KOSPI_ML').upper()
        pos_tag = target_stock.get('position_tag', 'MIDDLE')

        if raw_strategy in ['SCALPING', 'SCALP'] and pos_tag == 'MIDDLE':
            # 부분체결 다중 이벤트 방지: 1회만 셋업
            if target_stock.get('exit_mode') != 'SCALP_PRESET_TP' and not target_stock.get('preset_tp_ord_no'):
                target_stock['exit_mode'] = 'SCALP_PRESET_TP'

                # 가능한 경우 누적 buy_qty / buy_price 기준 사용, 불가하면 exec_price 폴백
                base_buy_price = int(target_stock.get('buy_price') or exec_price or 0)
                if base_buy_price <= 0:
                    base_buy_price = exec_price

                preset_tp_price = kiwoom_utils.get_target_price_up(base_buy_price, 1.5)
                target_stock['preset_tp_price'] = preset_tp_price
                target_stock['hard_stop_pct'] = -0.7
                target_stock['protect_profit_pct'] = None
                target_stock['ai_review_done'] = False
                target_stock['ai_review_score'] = None
                target_stock['ai_review_action'] = None
                target_stock['exit_requested'] = False
                target_stock['exit_order_type'] = None
                target_stock['exit_order_time'] = None

                from src.engine import kiwoom_orders
                sell_qty = int(target_stock.get('buy_qty') or exec_qty or 0)
                sell_res = kiwoom_orders.send_sell_order_market(
                    code=code, qty=sell_qty, token=KIWOOM_TOKEN, order_type="00", price=preset_tp_price
                )
                target_stock['preset_tp_ord_no'] = sell_res.get('ord_no') if isinstance(sell_res, dict) else ''

                # 지정가 주문 실패 시에도 출구 엔진 자체는 유지
                if not target_stock['preset_tp_ord_no']:
                    print(f"⚠️ [SCALP 출구엔진] {target_stock.get('name')} 지정가 매도 주문번호 미수신. 보유 감시로 보강 필요.")
                else:
                    print(f"🎯 [SCALP 출구엔진 셋업] {target_stock.get('name')} +1.5% 지정가({preset_tp_price:,}원) 1차 매도망 전개 완료.")

        # pending_buy_msg는 백그라운드 스레드에서 제거
        # 백그라운드 DB 업데이트 실행
        threading.Thread(
            target=_update_db_for_buy,
            args=(target_id, exec_price, now, target_stock),
            daemon=True
        ).start()
            
    elif exec_type == 'SELL':
        # record 조회 (동기) - 빠른 조회
        try:
            with DB.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                if not record:
                    return
                safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
                if safe_buy_price > 0:
                    profit_rate = round(((exec_price - safe_buy_price) / safe_buy_price) * 100, 2)
                else:
                    profit_rate = 0.0
                    print(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")
                raw_strategy = (record.strategy or target_stock.get('strategy') or 'KOSPI_ML').upper()
                strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
                # ✅ 일관성 통일: 15:30 이전까지만 스캘핑 부활
                is_scalp_revive = (strategy == 'SCALPING') and (now_t < TIME_15_30)
        except Exception as e:
            log_error(f"🚨 [DB 조회 에러] ID {target_id} SELL 처리 중 에러: {e}")
            return

        if is_scalp_revive:
            # 스캘핑 부활: 동기 DB 업데이트 (새 레코드 삽입 필요)
            try:
                with DB.get_session() as session:
                    record = session.query(RecommendationHistory).filter_by(id=target_id).first()
                    if not record:
                        return
                    record.status = 'COMPLETED'
                    record.sell_price = exec_price
                    record.sell_time = now
                    record.profit_rate = profit_rate
                    print(f"🎉 [매매 완료: ID {target_id}] {code} 실매도가: {exec_price:,}원 / 수익률: {profit_rate}%")
                    # 새 레코드 삽입
                    new_record = RecommendationHistory(
                        rec_date=now.date(),
                        stock_code=code,
                        stock_name=record.stock_name,
                        buy_price=0,
                        status='WATCHING',
                        strategy='SCALPING',
                        trade_type='SCALP',
                        position_tag='MIDDLE',
                        prob=record.prob
                    )
                    session.add(new_record)
                    session.flush()
                    new_watch_id = new_record.id
                    # 알림
                    pending_msg = target_stock.get('pending_sell_msg')
                    audience = target_stock.get('msg_audience', 'VIP_ALL')
                    if pending_msg:
                        final_msg = pending_msg.replace("매도 전송", "매도 체결 완료").replace("[익절 주문]", "[익절 완료]").replace("[손절 주문]", "[손절 완료]")
                        final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원` (확정 수익률: `{profit_rate:+.2f}%`)"
                        event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'Markdown'})
                    else:
                        sign = "🎊 [익절 완료]" if profit_rate > 0 else "📉 [손절 완료]"
                        event_bus.publish(
                            'TELEGRAM_BROADCAST',
                            {'message': f"{sign} **[{target_stock.get('name')}]** 매도 체결!\n체결가: `{exec_price:,}원`\n수익률: `{profit_rate:+.2f}%`", 'audience': audience, 'parse_mode': 'Markdown'}
                        )
            except Exception as e:
                log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")
                return
            # 메모리 업데이트 (부활)
            highest_prices.pop(code, None)
            target_stock['id'] = new_watch_id
            target_stock['status'] = 'WATCHING'
            target_stock['buy_price'] = 0
            target_stock['buy_qty'] = 0
            target_stock['added_time'] = time.time()
            target_stock['position_tag'] = 'MIDDLE'
            for key in [
                'odno', 'order_time', 'order_price', 'buy_time',
                'target_buy_price', 'pending_buy_msg',
                'pending_sell_msg', 'sell_odno', 'sell_order_time',
                'sell_target_price'
            ]:
                target_stock.pop(key, None)
        else:
            # 일반 SELL: 먼저 메모리 업데이트
            highest_prices.pop(code, None)
            target_stock['status'] = 'COMPLETED'
            target_stock['sell_time'] = now.strftime('%H:%M:%S')
            # pending_sell_msg는 백그라운드에서 제거
            # 백그라운드 DB 업데이트 실행
            threading.Thread(
                target=_update_db_for_sell,
                args=(target_id, exec_price, now, target_stock, strategy, is_scalp_revive),
                daemon=True
            ).start()

    # 메모리 업데이트는 각 조건문 내에서 이미 수행됨

# ==========================================
# 💡 09:05 주도주 분석, 리포트 발송
# ==========================================        
def execute_morning_strategy_batch(targets, ws_manager, radar, ai_engine):
    """
    [v13.0] 09:05 주도주 분석, 리포트 발송 일괄 처리합니다.
    고유 PK(id)를 사용하여 정확히 해당 감시 대상의 상태만 변경합니다.
    """
    if not targets or not ws_manager or not radar or not ai_engine:
        return

    print("🤖 [전략 집행] 09:05 주도주 정렬 및 AI Report 시작합니다.")

    codes = [stock['code'] for stock in targets]
    ws_data_map = ws_manager.get_all_data(codes)
    
    for stock in targets:
        try:
            ws_data = ws_data_map.get(stock['code'], {})
            stock['priority_score'] = radar.calculate_market_leader_score(ws_data)
        except Exception:
            stock['priority_score'] = 0

    sorted_targets = sorted(targets, key=lambda x: x.get('priority_score', 0), reverse=True)
    top_3 = sorted_targets[:3]
    if not top_3:
        print("⚠️ [전략 집행] 분석할 감시 종목이 없습니다.")
        return
    
    # 2. 통합 리포트 작성을 위한 변수 초기화
    full_report = "🚀 **[Good Morning AI 주도주 TOP 3 정밀 분석]**\n"
    full_report += f"📅 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    full_report += "━━━━━━━━━━━━━━━━━━\n\n"

    for i, s in enumerate(top_3):
        code = s['code']
        try:
            ws_data = ws_data_map.get(code, {})
            ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
            candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=40)

            ai_json_str = ai_engine.analyze_morning_leader(s['name'], ws_data, ticks, candles)

            if isinstance(ai_json_str, dict):
                res = ai_json_str
            else:
                res = json.loads(ai_json_str)

            full_report += f"📍 **{i+1}위. {s['name']}** ({code})\n"
            full_report += f"💬 `{res.get('one_liner', '분석 중...')}`\n"
            full_report += f"📈 패턴: **{res.get('pattern', '-')}**\n"
            full_report += f"🎯 권장타점: `{res.get('target_price', '-')}원` 부근\n"
            full_report += f"⚠️ 리스크: {res.get('risk_factor', '-')}\n"
            full_report += "━━━━━━━━━━━━━━━━━━\n"

        except Exception as e:
            log_error(f"❌ {s.get('name', code)} 전략 집행 중 에러: {e}")

    event_bus.publish('TELEGRAM_BROADCAST', {'message': full_report, 'parse_mode': 'Markdown'})
    print("✅ 09:05 전략 배치 작업이 완료되었습니다.")

# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (Phase 3: Event-Driven & 비동기 아키텍처 완전 적용)
# ==============================================================================
def run_sniper(is_test_mode=False):
    global KIWOOM_TOKEN, WS_MANAGER, ACTIVE_TARGETS, AI_ENGINE

    from src.utils.logger import log_error
    log_error(f"[DEBUG] run_sniper started at {datetime.now()}")
    run_sniper.morning_report_done = False
    run_sniper.last_fifo_time = 0
    run_sniper.last_account_sync_time = 0

    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V12.2 멀티 엔진 가동 (관리자: {admin_id})")
    if not admin_id:
        log_error("⚠️ ADMIN_ID가 설정되지 않았습니다. 매도 주문이 실행되지 않을 수 있습니다.")

    is_open, reason = kiwoom_utils.is_trading_day()
    if not is_test_mode and not is_open:
        msg = f"🛑 오늘은 {reason} 휴장일이므로 스나이퍼 매매 엔진을 가동하지 않습니다."
        print(msg)
        event_bus.publish('TELEGRAM_BROADCAST', {'message': msg})
        return

    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        log_error("❌ 토큰 발급 실패로 엔진을 중단합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [시스템 에러] 토큰 발급 실패로 엔진을 중단합니다."})
        return

    radar = SniperRadar(KIWOOM_TOKEN)
    log_error(f"[DEBUG] radar 객체 생성 완료: {radar}")
    sync_balance_with_db()

    if WS_MANAGER:
        try:
            WS_MANAGER.stop()
        except Exception as e:
            log_error(f"Existing WS manager shutdown failed: {e}")

    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)

    # 중복 subscribe 방지
    if not getattr(run_sniper, '_subscriptions_registered', False):
        event_bus.subscribe('ORDER_EXECUTED', handle_real_execution)
        event_bus.subscribe('CONDITION_MATCHED', handle_condition_matched)
        event_bus.subscribe('CONDITION_UNMATCHED', handle_condition_unmatched)

        def on_ws_reconnect(payload):
            threading.Thread(target=sync_state_with_broker, daemon=True).start()

        event_bus.subscribe('WS_RECONNECTED', on_ws_reconnect)
        run_sniper._subscriptions_registered = True

    WS_MANAGER.start()
    time.sleep(2)

    # ==========================================
    # 🤖 [신규] 제미나이 엔진 가동
    # ==========================================
    # 1. CONF에서 GEMINI_API_KEY 관련 값들만 추출
    # GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3 등을 모두 가져옵니다.
    ai_engine = None
    AI_ENGINE = None

    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY") and v]
    if not api_keys:
        log_error("❌ 제미나이 키 발급 실패로 엔진을 중단합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [시스템 에러] 제미나이 키 발급 실패로 엔진을 중단합니다."})
    else:
        ai_engine = GeminiSniperEngine(api_keys=api_keys)
        AI_ENGINE = ai_engine
        print(f"🤖 제미나이 AI 엔진이 {len(api_keys)}개의 API 키로 가동됩니다.")

    ACTIVE_TARGETS = DB.get_active_targets() or []
    _restore_armed_candidates_from_db()
    # ==========================================
    # 💡 [추가 1] 봇 시작 시 불러온 종목들의 진입 시간 기록
    # ==========================================
    for t in ACTIVE_TARGETS:
        t['added_time'] = time.time()
        t.setdefault('position_tag', 'MIDDLE')

    targets = ACTIVE_TARGETS
    last_db_poll_time = time.time()

    current_market_regime = radar.get_market_regime(KIWOOM_TOKEN)
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다.")

    target_codes = [t['code'] for t in targets]
    if target_codes:
        event_bus.publish("COMMAND_WS_REG", {"codes": target_codes})

    last_msg_min = -1

    try:
        while True:
            if os.path.exists("restart.flag"):
                print("🔄 [우아한 종료] 재시작 깃발을 확인했습니다. 시스템을 안전하게 정지합니다.")
                event_bus.publish('TELEGRAM_BROADCAST', {'message': "🛑 스나이퍼 엔진이 하던 작업을 마치고 우아하게 재시작됩니다."})
                os.remove("restart.flag")
                break

            now = datetime.now()
            now_t = now.time()

            if not is_test_mode and now_t >= TIME_20_00:
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                highest_prices.clear()
                alerted_stocks.clear()
                cooldowns.clear()
                LAST_AI_CALL_TIMES.clear()
                ACTIVE_TARGETS.clear()
                break

            # =====================================================
            # 신규 DB 타겟 polling
            # =====================================================
            if time.time() - last_db_poll_time > 5:
                db_targets = DB.get_active_targets() or []
                for dt in db_targets:
                    code = str(dt.get('code', '')).strip()[:6]
                    if not any(str(t.get('code', '')).strip()[:6] == code for t in targets):
                        dt['added_time'] = time.time()
                        dt.setdefault('position_tag', 'MIDDLE')
                        targets.append(dt)
                        event_bus.publish("COMMAND_WS_REG", {"codes": [code]})
                last_db_poll_time = time.time()

            # =====================================================
            # WATCHING TTL / FIFO
            # =====================================================
            if time.time() - getattr(run_sniper, 'last_fifo_time', 0) > 10:
                watching_stocks = [t for t in targets if t.get('status') == 'WATCHING']
                expired_ids = []
                expired_names = []

                watching_stocks.sort(key=lambda x: x.get('added_time', 0))

                for t in watching_stocks:
                    if t.get('strategy') in ['SCALPING', 'SCALP']:
                        if t.get('position_tag') in ['VCP_CANDID', 'VCP_SHOOTING', 'VCP_NEXT']:
                            continue
                        if time.time() - t.get('added_time', time.time()) > 7200:
                            expired_ids.append(t['id'])
                            expired_names.append(t['name'])

                scalp_remaining = [
                    t for t in watching_stocks
                    if t.get('strategy') in ['SCALPING', 'SCALP'] and t['id'] not in expired_ids
                    and t.get('position_tag') not in ['VCP_CANDID', 'VCP_SHOOTING', 'VCP_NEXT']
                ]
                if len(scalp_remaining) > 40:
                    overflow = len(scalp_remaining) - 40
                    for t in scalp_remaining[:overflow]:
                        expired_ids.append(t['id'])
                        expired_names.append(t['name'])

                if expired_ids:
                    try:
                        with DB.get_session() as session:
                            session.query(RecommendationHistory).filter(
                                RecommendationHistory.id.in_(expired_ids)
                            ).update({"status": "EXPIRED"}, synchronize_session=False)
                    except Exception as e:
                        log_error(f"🚨 FIFO 큐 DB 업데이트 에러: {e}")

                    for t in targets:
                        if t.get('id') in expired_ids:
                            t['status'] = 'EXPIRED'

                    print(f"🗑️ [스캘핑 큐 정리] {len(expired_ids)}개 단기 종목 감시 만료")
                    if len(expired_names) <= 10:
                        print(f"   └ 만료 종목: {', '.join(expired_names)}")

                run_sniper.last_fifo_time = time.time()

            # =====================================================
            # 90초 주기 계좌 동기화
            # =====================================================
            if time.time() - getattr(run_sniper, 'last_account_sync_time', 0) > 90:
                # from src.utils.logger import log_error
                # log_error(f"[DEBUG] 90초 조건 만족, periodic_account_sync 시작")
                threading.Thread(target=periodic_account_sync, daemon=True).start()
                run_sniper.last_account_sync_time = time.time()

            # =====================================================
            # 09:05 아침 배치
            # =====================================================
            if TIME_09_05 <= now_t <= TIME_09_10 and not getattr(run_sniper, 'morning_report_done', False):
                if ai_engine and targets:
                    print("🤖 Gemini AI가 주도주 TOP 3의 차트와 수급을 정밀 분석합니다...")
                    morning_thread = threading.Thread(
                        target=execute_morning_strategy_batch,
                        args=(targets, WS_MANAGER, radar, ai_engine),
                        daemon=True
                    )
                    morning_thread.start()
                run_sniper.morning_report_done = True
            elif now_t > TIME_09_10:
                run_sniper.morning_report_done = True

            # =====================================================
            # 상태 로그
            # =====================================================
            if now_t.minute % 5 == 0 and now_t.minute != last_msg_min:
                watching_count = len([t for t in targets if t.get('status') == 'WATCHING'])
                holding_count = len([t for t in targets if t.get('status') == 'HOLDING'])
                print(f"💓 [{now.strftime('%H:%M:%S')}] 다중 감시망 가동 중... (감시: {watching_count} / 보유: {holding_count})")
                last_msg_min = now_t.minute

            # =====================================================
            # 상태 라우팅
            # ✅ 주문대기 상태는 ws_data 없이도 먼저 처리
            # =====================================================
            for stock in targets[:]:
                code = str(stock.get('code', '')).strip()[:6]
                status = stock.get('status')

                if status == 'BUY_ORDERED':
                    handle_buy_ordered_state(stock, code)
                    continue

                if status == 'SELL_ORDERED':
                    handle_sell_ordered_state(stock, code)
                    continue

                ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
                if not ws_data or ws_data.get('curr', 0) == 0:
                    continue

                if status == 'WATCHING':
                    handle_watching_state(
                        stock,
                        code,
                        ws_data,
                        admin_id,
                        radar=radar,
                        ai_engine=ai_engine
                    )
                elif status == 'HOLDING':
                    handle_holding_state(
                        stock,
                        code,
                        ws_data,
                        admin_id,
                        current_market_regime,
                        radar=radar,
                        ai_engine=ai_engine
                    )

            targets[:] = [t for t in targets if t.get('status') not in ['COMPLETED', 'EXPIRED']]
            time.sleep(1)

    except Exception as e:
        log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}")
        print(f"🔥 스나이퍼 루프 치명적 에러: {e}")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': f"🚨 [시스템 에러] 스나이퍼 엔진 치명적 에러: {e}"})

    except KeyboardInterrupt:
        print("\n🛑 스나이퍼 매매 엔진 종료")

    finally:
        if WS_MANAGER:
            try:
                WS_MANAGER.stop()
            except Exception as e:
                log_error(f"WS manager stop failed: {e}")

if __name__ == "__main__":
    """
    python src/engine/kiwoom_sniper_v2.py 로 직접 실행할 때만 작동합니다.
    운영 환경(bot_main.py) 배포 시 이 블록은 투명인간 취급되므로 지울 필요가 없습니다!
    """
        
    # 1. 텔레그램 매니저 로드 (이벤트 리스너 가동)
    try:
        import src.notify.telegram_manager
        print("🔔 [Test Mode] 텔레그램 알림 리스너가 가동되었습니다.")
    except ImportError as e:
        print(f"⚠️ 텔레그램 매니저 로드 실패. 알림 없이 진행합니다: {e}")
        
    # 3. 스나이퍼 엔진 단독 실행!
    try:
        run_sniper(is_test_mode=True)
    except KeyboardInterrupt:
        print("\n🛑 테스트를 사용자에 의해 종료합니다.")

