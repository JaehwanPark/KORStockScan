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
from datetime import datetime
import threading   
import numpy as np
import json

# 💡 Level 1 & 2 공통 모듈 (경로 및 패키지 구조에 맞게 통일)
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.constants import TRADING_RULES, CREDENTIALS_PATH
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.utils.google_sheets_utils import GoogleSheetsManager
from src.database.models import RecommendationHistory
from src.engine.sniper_config import CONF
from src.engine.sniper_time import (
    _rule_time,
    _in_time_window,
    TIME_07_00,
    TIME_09_00,
    TIME_09_03,
    TIME_09_05,
    TIME_09_10,
    TIME_10_30,
    TIME_11_00,
    TIME_SCALPING_NEW_BUY_CUTOFF,
    TIME_SCALPING_OVERNIGHT_DECISION,
    TIME_MARKET_CLOSE,
    TIME_15_30,
    TIME_20_00,
    TIME_23_59,
)
from src.engine.sniper_s15_fast_track import (
    bind_s15_dependencies,
    _now_ts,
    _arm_s15_candidate,
    _unarm_s15_candidate,
    _restore_armed_candidates_from_db,
    _is_s15_armed,
    _is_s15_reentry_blocked,
    _block_s15_reentry,
    _get_fast_state,
    _set_fast_state,
    _pop_fast_state,
    _weighted_avg,
    create_s15_shadow_record,
    update_s15_shadow_record,
    execute_fast_track_scalp_v2,
)
from src.engine.sniper_condition_handlers import (
    bind_condition_dependencies,
    resolve_condition_profile,
    get_condition_target_date,
    handle_condition_matched,
    handle_condition_unmatched,
)
from src.engine.sniper_sync import (
    bind_sync_dependencies,
    sync_balance_with_db,
    sync_state_with_broker,
    periodic_account_sync,
)
from src.engine.sniper_analysis import (
    bind_analysis_dependencies,
    analyze_stock_now,
    get_detailed_reason,
    get_realtime_ai_scores,
)
import src.engine.sniper_state_handlers as sniper_state_handlers
from src.engine.sniper_state_handlers import bind_state_dependencies
import src.engine.sniper_execution_receipts as sniper_execution_receipts
from src.engine.sniper_execution_receipts import bind_execution_dependencies
import src.engine.sniper_overnight_gatekeeper as sniper_overnight_gatekeeper
from src.engine.sniper_overnight_gatekeeper import bind_overnight_dependencies
import src.engine.sniper_market_regime as sniper_market_regime
from src.engine.sniper_market_regime import bind_market_regime_dependencies
import src.engine.sniper_trade_utils as sniper_trade_utils

# 💡 뇌(AI)와 눈(웹소켓, 레이더) 임포트
from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.signal_radar import SniperRadar
from src.engine.ai_engine import GeminiSniperEngine
# from src.engine.ai_engine_openai import OpenAISniperEngine

# 💡 VIX, 유가지표 임포트
from src.market_regime import MarketRegimeService

# 스캐너 모듈 (장중 스캔 호출용)
import src.scanners.final_ensemble_scanner as final_ensemble_scanner
import telebot
try:
    from telebot.formatting import escape_markdown
except ImportError:
    def escape_markdown(text):
        if not isinstance(text, str):
            text = str(text)
        # Escape Markdown special characters (excluding parentheses/brackets/dot/exclamation)
        for ch in '*_``~>#+-=|{}':
            text = text.replace(ch, '\\' + ch)
        return text
bind_condition_dependencies(escape_markdown_fn=escape_markdown)

# --- [전역 상태 변수] -----------------------------------------------
highest_prices = {}
alerted_stocks = set()
cooldowns = {}  # 스캘핑 뇌동매매 방지용 쿨타임 관리

KIWOOM_TOKEN = None
WS_MANAGER = None
AI_ENGINE = None  # 💡 [추가] AI 엔진을 전역으로 끌어올립니다.
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager()  
event_bus = EventBus() # 💡 [신규] 전역 이벤트 버스 장착!
bind_s15_dependencies(db=DB)

# 💡 [스레드 안전성] 공유 상태 접근용 락
_state_lock = threading.RLock()

global ACTIVE_TARGETS
ACTIVE_TARGETS = []
LAST_AI_CALL_TIMES = {}
LAST_LOG_TIMES = {}
MARKET_REGIME = MarketRegimeService(refresh_minutes=15)
bind_market_regime_dependencies(market_regime=MARKET_REGIME)
bind_condition_dependencies(db=DB, event_bus=event_bus, active_targets=ACTIVE_TARGETS)
bind_sync_dependencies(
    db=DB,
    event_bus=event_bus,
    active_targets=ACTIVE_TARGETS,
    highest_prices=highest_prices,
    state_lock=_state_lock,
)
def _set_ai_engine_from_analysis(engine):
    global AI_ENGINE
    AI_ENGINE = engine

bind_analysis_dependencies(
    db=DB,
    event_bus=event_bus,
    active_targets=ACTIVE_TARGETS,
    conf=CONF,
    trading_rules=TRADING_RULES,
    ai_engine_setter=_set_ai_engine_from_analysis,
)

# -------------------------------------------------------------------

def _send_market_exit_now(code, qty, token):
    """정규장 중 즉시 시장가 청산용 공통 래퍼"""
    return sniper_trade_utils.send_market_exit_now(code, qty, token)


def _publish_gatekeeper_report(stock, code, gatekeeper, allowed):
    """
    Gatekeeper 성공일때만 결과를 텔레그램으로 발행합니다.
    """
    action_label = gatekeeper.get('action_label', 'UNKNOWN')
    report = gatekeeper.get('report', '')
    # 리포트가 길면 첫 200자만 사용
    preview = report[:200] + ('...' if len(report) > 200 else '')
    status = '승인' if allowed else '거부'
    audience = 'VIP_ALL'  # 기본적으로 관리자에게만 알림
    # VIP 대상 여부는 stock에 따라 결정 가능 (필요 시 추가)    
    msg = (
        f"🤖 <b>[Gatekeeper {status}]</b>\n"
        f"🎯 종목: {stock['name']} ({code})\n"
        f"⚡ 판정: <b>{action_label}</b>\n"
        f"📄 리포트: {preview}"
    )
    event_bus.publish(
        'TELEGRAM_BROADCAST',
        {'message': msg, 'audience': audience, 'parse_mode': 'HTML'}
    )

def _send_exit_best_ioc(code, qty, token):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    return sniper_trade_utils.send_exit_best_ioc(code, qty, token)
def _confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    """[공통 유틸] 주문 취소 후 실제 계좌 잔고를 재조회하여 팔아야 할 정확한 잔량(rem_qty) 반환"""
    return sniper_trade_utils.confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty)

bind_execution_dependencies(
    kiwoom_token=KIWOOM_TOKEN,
    db=DB,
    event_bus_instance=event_bus,
    active_targets=ACTIVE_TARGETS,
    highest_prices_map=highest_prices,
    get_fast_state=_get_fast_state,
    weighted_avg=_weighted_avg,
    now_ts=_now_ts,
)

_STATE_HANDLER_DEPS = {}

def _ensure_state_handler_deps():
    global _STATE_HANDLER_DEPS
    snapshot = {
        'kiwoom_token': KIWOOM_TOKEN,
        'db': DB,
        'event_bus': event_bus,
        'active_targets': ACTIVE_TARGETS,
        'cooldowns': cooldowns,
        'alerted_stocks': alerted_stocks,
        'highest_prices': highest_prices,
        'last_ai_call_times': LAST_AI_CALL_TIMES,
        'last_log_times': LAST_LOG_TIMES,
        'trading_rules': TRADING_RULES,
        'publish_gatekeeper_report': _publish_gatekeeper_report,
        'should_block_swing_entry': should_block_swing_entry_by_market_regime,
        'confirm_cancel_or_reload_remaining': _confirm_cancel_or_reload_remaining,
        'send_exit_best_ioc': _send_exit_best_ioc,
    }
    if any(_STATE_HANDLER_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_state_dependencies(**snapshot)
        _STATE_HANDLER_DEPS = snapshot


def handle_watching_state(stock, code, ws_data, admin_id, radar=None, ai_engine=None):
    _ensure_state_handler_deps()
    return sniper_state_handlers.handle_watching_state(stock, code, ws_data, admin_id, radar=radar, ai_engine=ai_engine)


def handle_holding_state(stock, code, ws_data, admin_id, market_regime, radar=None, ai_engine=None):
    _ensure_state_handler_deps()
    return sniper_state_handlers.handle_holding_state(
        stock, code, ws_data, admin_id, market_regime, radar=radar, ai_engine=ai_engine
    )


def handle_buy_ordered_state(stock, code):
    _ensure_state_handler_deps()
    return sniper_state_handlers.handle_buy_ordered_state(stock, code)


def handle_sell_ordered_state(stock, code):
    _ensure_state_handler_deps()
    return sniper_state_handlers.handle_sell_ordered_state(stock, code)


def process_sell_cancellation(stock, code, orig_ord_no, db):
    _ensure_state_handler_deps()
    return sniper_state_handlers.process_sell_cancellation(stock, code, orig_ord_no, db)


def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    _ensure_state_handler_deps()
    return sniper_state_handlers.process_order_cancellation(stock, code, orig_ord_no, db, strategy)


_EXECUTION_DEPS = {}

def _ensure_execution_deps():
    global _EXECUTION_DEPS
    snapshot = {
        'kiwoom_token': KIWOOM_TOKEN,
        'db': DB,
        'event_bus_instance': event_bus,
        'active_targets': ACTIVE_TARGETS,
        'highest_prices_map': highest_prices,
        'get_fast_state': _get_fast_state,
        'weighted_avg': _weighted_avg,
        'now_ts': _now_ts,
    }
    if any(_EXECUTION_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_execution_dependencies(**snapshot)
        _EXECUTION_DEPS = snapshot


def handle_real_execution(exec_data):
    _ensure_execution_deps()
    return sniper_execution_receipts.handle_real_execution(exec_data)


_OVERNIGHT_DEPS = {}

def _ensure_overnight_deps():
    global _OVERNIGHT_DEPS
    snapshot = {
        'kiwoom_token': KIWOOM_TOKEN,
        'db': DB,
        'ws_manager': WS_MANAGER,
        'event_bus_instance': event_bus,
        'active_targets': ACTIVE_TARGETS,
        'escape_markdown_fn': escape_markdown,
        'confirm_cancel_or_reload_remaining': _confirm_cancel_or_reload_remaining,
        'send_market_exit_now': _send_market_exit_now,
        'is_ok_response': _is_ok_response,
        'extract_ord_no': _extract_ord_no,
        'process_sell_cancellation_fn': process_sell_cancellation,
    }
    if any(_OVERNIGHT_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_overnight_dependencies(**snapshot)
        _OVERNIGHT_DEPS = snapshot


def run_scalping_overnight_gatekeeper(ai_engine=None):
    _ensure_overnight_deps()
    return sniper_overnight_gatekeeper.run_scalping_overnight_gatekeeper(ai_engine=ai_engine)


_MARKET_REGIME_DEPS = {}

def _ensure_market_regime_deps():
    global _MARKET_REGIME_DEPS
    snapshot = {
        'market_regime': MARKET_REGIME,
    }
    if any(_MARKET_REGIME_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_market_regime_dependencies(**snapshot)
        _MARKET_REGIME_DEPS = snapshot


def init_market_regime_service():
    _ensure_market_regime_deps()
    return sniper_market_regime.init_market_regime_service()


def should_block_swing_entry_by_market_regime(strategy: str):
    _ensure_market_regime_deps()
    return sniper_market_regime.should_block_swing_entry_by_market_regime(strategy)

bind_state_dependencies(
    db=DB,
    event_bus=event_bus,
    active_targets=ACTIVE_TARGETS,
    cooldowns=cooldowns,
    alerted_stocks=alerted_stocks,
    highest_prices=highest_prices,
    last_ai_call_times=LAST_AI_CALL_TIMES,
    last_log_times=LAST_LOG_TIMES,
    trading_rules=TRADING_RULES,
    publish_gatekeeper_report=_publish_gatekeeper_report,
    should_block_swing_entry=should_block_swing_entry_by_market_regime,
    confirm_cancel_or_reload_remaining=_confirm_cancel_or_reload_remaining,
    send_exit_best_ioc=_send_exit_best_ioc,
)
def _extract_ord_no(res):
    return sniper_trade_utils.extract_ord_no(res)

def _is_ok_response(res):
    return sniper_trade_utils.is_ok_response(res)

# =====================================================================
# 🧠 상태 머신 (State Machine) 핸들러 
# =====================================================================
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
            # TODO: KOSDAQ 트레일링 되밀림 폭을 TRAILING_DRAWDOWN_PCT로 통일 검토
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


bind_analysis_dependencies(
    check_watching_conditions=check_watching_conditions,
    check_holding_conditions=check_holding_conditions,
)


# ==============================================================================
# 🎯 메인 스나이퍼 엔진 (Phase 3: Event-Driven & 비동기 아키텍처 완전 적용)
# ==============================================================================
def run_sniper(is_test_mode=False):
    global KIWOOM_TOKEN, WS_MANAGER, ACTIVE_TARGETS, AI_ENGINE

    from src.utils.logger import log_error
    log_error(f"[DEBUG] run_sniper started at {datetime.now()}")
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
    bind_state_dependencies(kiwoom_token=KIWOOM_TOKEN)
    bind_execution_dependencies(kiwoom_token=KIWOOM_TOKEN)
    bind_overnight_dependencies(kiwoom_token=KIWOOM_TOKEN)

    radar = SniperRadar(KIWOOM_TOKEN)
    log_error(f"[DEBUG] radar 객체 생성 완료: {radar}")
    sync_balance_with_db()
    init_market_regime_service()

    if WS_MANAGER:
        try:
            WS_MANAGER.stop()
        except Exception as e:
            log_error(f"Existing WS manager shutdown failed: {e}")

    WS_MANAGER = KiwoomWSManager(KIWOOM_TOKEN)
    bind_overnight_dependencies(ws_manager=WS_MANAGER)
    bind_sync_dependencies(
        kiwoom_token=KIWOOM_TOKEN,
        db=DB,
        event_bus=event_bus,
        highest_prices=highest_prices,
        state_lock=_state_lock,
    )
    bind_condition_dependencies(kiwoom_token=KIWOOM_TOKEN, ws_manager=WS_MANAGER, db=DB, event_bus=event_bus)
    bind_analysis_dependencies(
        kiwoom_token=KIWOOM_TOKEN,
        ws_manager=WS_MANAGER,
        event_bus=event_bus,
        conf=CONF,
        db=DB,
        trading_rules=TRADING_RULES,
    )

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
    bind_analysis_dependencies(ai_engine=AI_ENGINE)

    bind_s15_dependencies(
        kiwoom_token=KIWOOM_TOKEN,
        ws_manager=WS_MANAGER,
        ai_engine=AI_ENGINE,
        db=DB,
    )

    ACTIVE_TARGETS = DB.get_active_targets() or []
    bind_sync_dependencies(active_targets=ACTIVE_TARGETS)
    bind_condition_dependencies(active_targets=ACTIVE_TARGETS)
    bind_analysis_dependencies(active_targets=ACTIVE_TARGETS)
    bind_state_dependencies(active_targets=ACTIVE_TARGETS)
    bind_execution_dependencies(active_targets=ACTIVE_TARGETS)
    bind_overnight_dependencies(active_targets=ACTIVE_TARGETS)
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
            # 15:15 SCALPING 오버나이트 독립 판정 (DB 기준, 무조건 1회 작동)
            # =====================================================
            today_key = now.date().isoformat()
            last_eod_done = getattr(run_sniper, 'scalping_eod_done_date', None)
            last_eod_try = getattr(run_sniper, 'last_scalping_eod_try', 0)
            if now_t >= TIME_SCALPING_OVERNIGHT_DECISION and last_eod_done != today_key:
                if time.time() - last_eod_try >= 60:
                    run_sniper.last_scalping_eod_try = time.time()
                    if run_scalping_overnight_gatekeeper(ai_engine=ai_engine):
                        run_sniper.scalping_eod_done_date = today_key

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
