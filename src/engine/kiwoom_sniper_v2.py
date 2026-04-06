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
from src.engine.sniper_strength_momentum import evaluate_scalping_strength_momentum
from src.engine.sniper_dynamic_thresholds import (
    estimate_turnover_hint,
    get_dynamic_scalp_thresholds,
    get_dynamic_swing_gap_threshold,
)
from src.engine.sniper_state_handlers import bind_state_dependencies
import src.engine.sniper_execution_receipts as sniper_execution_receipts
from src.engine.sniper_execution_receipts import bind_execution_dependencies
import src.engine.sniper_overnight_gatekeeper as sniper_overnight_gatekeeper
from src.engine.sniper_overnight_gatekeeper import bind_overnight_dependencies
import src.engine.sniper_market_regime as sniper_market_regime
from src.engine.sniper_market_regime import bind_market_regime_dependencies
import src.engine.sniper_trade_utils as sniper_trade_utils
from src.engine.trade_pause_control import bind_event_bus as bind_trade_pause_event_bus, is_buy_side_paused
from src.engine.sniper_position_tags import (
    normalize_position_tag,
    normalize_strategy,
    target_identity,
)

# 💡 뇌(AI)와 눈(웹소켓, 레이더) 임포트
from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.signal_radar import SniperRadar
from src.engine.ai_engine import GeminiSniperEngine
from src.engine.ai_engine_openai_v2 import OpenAIDualPersonaShadowEngine
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
DUAL_PERSONA_ENGINE = None

KIWOOM_TOKEN = None
WS_MANAGER = None
AI_ENGINE = None  # 💡 [추가] AI 엔진을 전역으로 끌어올립니다.
SHEET_MANAGER = GoogleSheetsManager(CREDENTIALS_PATH, 'KOSPIScanner')
DB = DBManager()  
event_bus = EventBus() # 💡 [신규] 전역 이벤트 버스 장착!
bind_trade_pause_event_bus(event_bus)
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
    conf=CONF,
)


def _get_swing_gap_threshold(strategy: str) -> float:
    fallback = float(getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT', 3.0) or 3.0)
    strategy_upper = str(strategy or '').upper()
    if strategy_upper == 'KOSPI_ML':
        return float(getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT_KOSPI', fallback) or fallback)
    return float(getattr(TRADING_RULES, 'MAX_SWING_GAP_UP_PCT_KOSDAQ', fallback) or fallback)


def _resolve_stock_marcap(stock, code) -> int:
    try:
        existing = int(float(stock.get('marcap', 0) or 0))
    except Exception:
        existing = 0
    if existing > 0:
        return existing
    try:
        marcap = int(DB.get_latest_marcap(code) or 0)
    except Exception:
        marcap = 0
    if marcap > 0:
        stock['marcap'] = marcap
    return marcap


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
        'dual_persona_engine': DUAL_PERSONA_ENGINE,
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
        'dual_persona_engine': DUAL_PERSONA_ENGINE,
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
    
    strategy = normalize_strategy(stock.get('strategy'))
    pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
    
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
        marcap = _resolve_stock_marcap(stock, code)
        turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
        scalp_limits = get_dynamic_scalp_thresholds(marcap, turnover_hint=turnover_hint)
        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        liquidity_value = (ask_tot + bid_tot) * curr_price
        max_surge = float(scalp_limits.get('max_surge', MAX_SURGE) or MAX_SURGE)
        max_intraday_surge = float(scalp_limits.get('max_intraday_surge', MAX_INTRADAY_SURGE) or MAX_INTRADAY_SURGE)
        min_liquidity = int(scalp_limits.get('min_liquidity', MIN_LIQUIDITY) or MIN_LIQUIDITY)
        
        if fluctuation >= max_surge or intraday_surge >= max_intraday_surge:
            return (
                f"과매수 위험 차단 (fluctuation={fluctuation:.2f} >= {max_surge:.2f} "
                f"또는 intraday_surge={intraday_surge:.2f} >= {max_intraday_surge:.2f}, "
                f"cap={scalp_limits.get('bucket_label')})"
            )
        
        if pos_tag == 'VCP_NEXT':
            # VCP_NEXT는 별도 검사 없이 통과
            pass
        else:
            if radar is None:
                return "radar 객체 없음"
            momentum_gate = evaluate_scalping_strength_momentum(ws_data)
            if current_vpw < getattr(TRADING_RULES, 'VPW_SCALP_LIMIT', 120):
                return (
                    f"VPW 불충족 (current_vpw={current_vpw:.1f} < VPW_SCALP_LIMIT, "
                    f"dynamic_allowed={momentum_gate.get('allowed')}, "
                    f"dynamic_reason={momentum_gate.get('reason')}, "
                    f"dynamic_delta={float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}, "
                    f"dynamic_buy_value={int(momentum_gate.get('window_buy_value', 0) or 0)})"
                )
            if liquidity_value < min_liquidity:
                return (
                    f"유동성 불충족 (liquidity_value={liquidity_value:,.0f} < "
                    f"MIN_LIQUIDITY={min_liquidity:,.0f}, cap={scalp_limits.get('bucket_label')})"
                )
            
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
        
        marcap = _resolve_stock_marcap(stock, code)
        turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
        swing_gap = get_dynamic_swing_gap_threshold(strategy, marcap, turnover_hint=turnover_hint)
        max_gap = float(swing_gap.get('threshold', _get_swing_gap_threshold(strategy)) or _get_swing_gap_threshold(strategy))
        if fluctuation >= max_gap:
            return (
                f"갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap:.2f}, "
                f"cap={swing_gap.get('bucket_label')})"
            )
        
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
    target_budget, safe_budget, real_buy_qty, used_safety_ratio = kiwoom_orders.describe_buy_capacity(
        curr_price,
        deposit,
        ratio,
    )
    if real_buy_qty <= 0:
        return (
            "매수 수량 0주 "
            f"(deposit={deposit}, ratio={ratio:.4f}, target_budget={target_budget}, "
            f"safe_budget={safe_budget}, safety_ratio={used_safety_ratio:.4f}, curr_price={curr_price})"
        )
    
    # 모든 조건 통과
    return None


def _parse_holding_started_at(stock):
    hold_time = stock.get('holding_started_at') or stock.get('buy_time')
    if not hold_time:
        return None
    if isinstance(hold_time, datetime):
        return hold_time
    try:
        return datetime.fromisoformat(str(hold_time))
    except Exception:
        return None


def evaluate_scalping_exit(stock, code, ws_data, curr_p, buy_p, profit_rate, peak_profit):
    base_stop_pct = getattr(TRADING_RULES, 'SCALP_STOP', -1.5)
    hard_stop_pct = getattr(TRADING_RULES, 'SCALP_HARD_STOP', -2.5)
    ai_exit_score_limit = int(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MAX_SCORE', 35))
    ai_exit_min_loss_pct = float(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MIN_LOSS_PCT', -0.7))
    ai_exit_min_hold_sec = int(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_MIN_HOLD_SEC', 180))
    ai_exit_needed_hits = int(getattr(TRADING_RULES, 'SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS', 3))
    safe_profit_pct = getattr(TRADING_RULES, 'SCALP_SAFE_PROFIT', 0.5)
    trailing_start_pct = getattr(TRADING_RULES, 'SCALP_TRAILING_START_PCT', 0.6)
    weak_trailing = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_WEAK', 0.4)
    strong_trailing = getattr(TRADING_RULES, 'SCALP_TRAILING_LIMIT_STRONG', 0.8)

    current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
    current_vpw = float(ws_data.get('v_pw', 0) or 0.0)

    # v_pw 히스토리 관리
    recent_vpw = stock.get('recent_vpw_values', [])
    recent_vpw.append(current_vpw)
    if len(recent_vpw) > 6:
        recent_vpw = recent_vpw[-6:]
    stock['recent_vpw_values'] = recent_vpw
    avg_vpw = sum(recent_vpw) / len(recent_vpw) if recent_vpw else current_vpw

    weak_vpw_count = int(stock.get('weak_vpw_count', 0) or 0)
    if current_vpw < 100:
        weak_vpw_count += 1
    else:
        weak_vpw_count = max(0, weak_vpw_count - 1)
    stock['weak_vpw_count'] = weak_vpw_count

    # 시간 가치(Time Decay)
    hold_start = _parse_holding_started_at(stock)
    held_seconds = (datetime.now() - hold_start).total_seconds() if hold_start else 0
    last_peak_update = stock.get('last_peak_update_at')
    if last_peak_update is None:
        stock['last_peak_update_at'] = datetime.now()
        last_peak_update = stock['last_peak_update_at']
    elif not isinstance(last_peak_update, datetime):
        try:
            last_peak_update = datetime.fromisoformat(str(last_peak_update))
        except Exception:
            last_peak_update = datetime.now()
        stock['last_peak_update_at'] = last_peak_update

    if held_seconds >= 90:
        if profit_rate < 0.2 and peak_profit < 0.4 and avg_vpw < 105:
            return "시간가치 소진(90s+ 미미수익 & v_pw 둔화)"
    if held_seconds >= 180:
        no_peak = (datetime.now() - last_peak_update).total_seconds() >= 60
        if abs(profit_rate) < 0.2 and peak_profit < 0.5 and (avg_vpw < 105 or no_peak):
            return "시간가치 소진(180s+ 정체 & 고점갱신 부재)"

    # Volume Power Crash
    if weak_vpw_count >= 2 and current_vpw < 100:
        avg_drop_ok = len(recent_vpw) >= 3 and (avg_vpw - current_vpw) >= 8
        if profit_rate < 1.0 or avg_drop_ok:
            return f"매수세 급락(v_pw={current_vpw:.0f})"

    # Hard/Soft Stop 정렬: hard는 더 깊은 손실, soft는 완충 손절
    soft_stop_pct = max(base_stop_pct, hard_stop_pct)
    hard_stop_pct = min(base_stop_pct, hard_stop_pct)
    if profit_rate <= hard_stop_pct:
        return f"하드스탑 도달 (profit_rate={profit_rate:.2f}% <= {hard_stop_pct}%)"

    if profit_rate <= soft_stop_pct:
        return f"소프트 손절선 도달 (profit_rate={profit_rate:.2f}% <= {soft_stop_pct}%)"

    # AI 하방 리스크
    ai_low_score_hits = int(stock.get('ai_low_score_loss_hits', 0) or 0)
    if (
        held_seconds >= ai_exit_min_hold_sec
        and profit_rate <= ai_exit_min_loss_pct
        and current_ai_score <= ai_exit_score_limit
        and ai_low_score_hits >= ai_exit_needed_hits
    ):
        return (
            f"AI 하방 리스크 연속 확인 ({ai_low_score_hits}/{ai_exit_needed_hits}, "
            f"AI 점수 {current_ai_score:.0f})"
        )

    # Dynamic Trailing (peak 확보 이후만)
    if peak_profit >= trailing_start_pct and profit_rate >= safe_profit_pct:
        drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100 if highest_prices[code] > 0 else 0
        if current_ai_score >= 75 and current_vpw >= 110:
            trailing_limit = strong_trailing
        elif current_ai_score >= 65 and current_vpw >= 105:
            trailing_limit = (weak_trailing + strong_trailing) / 2
        else:
            trailing_limit = weak_trailing
        if drawdown >= trailing_limit:
            return f"고점 대비 밀림 (drawdown={drawdown:.2f}%)"

    # 장 마감 전 현금화 (기존 보존)
    now_t = datetime.now().time()
    if now_t >= TIME_15_30 and profit_rate >= getattr(TRADING_RULES, 'MIN_FEE_COVER', 0.1):
        return "장 마감 전 현금화"

    return None


def evaluate_swing_exit(stock, code, ws_data, curr_p, buy_p, profit_rate, peak_profit, market_regime, strategy):
    if strategy == 'KOSDAQ_ML':
        if peak_profit >= getattr(TRADING_RULES, 'KOSDAQ_TARGET', 4.0):
            drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100 if highest_prices[code] > 0 else 0
            # TODO: KOSDAQ 트레일링 되밀림 폭을 TRAILING_DRAWDOWN_PCT로 통일 검토
            if drawdown >= 1.0:
                return f"KOSDAQ 트레일링 익절 (peak_profit={peak_profit:.1f}%)"
        if profit_rate <= getattr(TRADING_RULES, 'KOSDAQ_STOP', -2.0):
            return f"KOSDAQ 손절선 도달 (profit_rate={profit_rate:.2f}%)"
        return None

    pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
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
    if not stock.get('holding_started_at'):
        if stock.get('buy_time'):
            stock['holding_started_at'] = stock.get('buy_time')

    profit_rate = (curr_p - buy_p) / buy_p * 100
    if code in highest_prices:
        if curr_p > highest_prices[code]:
            highest_prices[code] = curr_p
            stock['last_peak_update_at'] = datetime.now()
    else:
        highest_prices[code] = curr_p
        stock['last_peak_update_at'] = datetime.now()
    peak_profit = (highest_prices[code] - buy_p) / buy_p * 100

    if strategy == 'SCALPING':
        reason = evaluate_scalping_exit(stock, code, ws_data, curr_p, buy_p, profit_rate, peak_profit)
        if reason:
            return reason
    else:
        reason = evaluate_swing_exit(stock, code, ws_data, curr_p, buy_p, profit_rate, peak_profit, market_regime, strategy)
        if reason:
            return reason

    # 관리자 ID 체크
    if not admin_id:
        return "관리자 ID 없음"

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

    from src.utils.logger import log_error, log_info
    log_info(f"[DEBUG] run_sniper started at {datetime.now()}")
    run_sniper.last_fifo_time = 0
    run_sniper.last_account_sync_time = 0
    # EventBus 즉시성 반영용 런타임 캐시입니다.
    # 최종 BUY 차단 판단은 각 게이트에서 file truth source(is_buy_side_paused)로 다시 확인합니다.
    run_sniper.runtime_pause_state = is_buy_side_paused()

    admin_id = CONF.get('ADMIN_ID')
    print(f"🔫 스나이퍼 V12.2 멀티 엔진 가동 (관리자: {admin_id})")
    if run_sniper.runtime_pause_state:
        log_info("⏸ 부팅 시 pause.flag 감지: 신규 매수 및 추가매수 중단 상태로 시작합니다.")
    if not admin_id:
        log_info("⚠️ ADMIN_ID가 설정되지 않았습니다. 매도 주문이 실행되지 않을 수 있습니다.")
    
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
    # Ensure sync module has the token before any balance calls.
    bind_sync_dependencies(kiwoom_token=KIWOOM_TOKEN, conf=CONF)
    bind_state_dependencies(kiwoom_token=KIWOOM_TOKEN)
    bind_execution_dependencies(kiwoom_token=KIWOOM_TOKEN)
    bind_overnight_dependencies(kiwoom_token=KIWOOM_TOKEN)
    bind_trade_pause_event_bus(event_bus)

    radar = SniperRadar(KIWOOM_TOKEN)
    log_info(f"[DEBUG] radar 객체 생성 완료: {radar}")
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
        conf=CONF,
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

        def on_trading_paused(payload):
            payload = payload or {}
            status = str(payload.get('status', '')).upper()
            if status == 'PAUSED':
                run_sniper.runtime_pause_state = True
                log_info("[TRADING_PAUSED] runtime state updated immediately via EventBus: PAUSED")
            elif status == 'RESUMED':
                run_sniper.runtime_pause_state = False
                log_info("[TRADING_RESUMED] runtime state updated immediately via EventBus: RESUMED")
            else:
                run_sniper.runtime_pause_state = is_buy_side_paused()
                tag = "TRADING_PAUSED" if run_sniper.runtime_pause_state else "TRADING_RESUMED"
                log_info(
                    f"[{tag}] runtime state refreshed from file truth source after unknown EventBus payload; "
                    f"fallback_to_flag={run_sniper.runtime_pause_state}"
                )

        def on_ws_reconnect(payload):
            threading.Thread(target=sync_state_with_broker, daemon=True).start()

        event_bus.subscribe('TRADING_PAUSED', on_trading_paused)
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
    dual_persona_engine = None
    global DUAL_PERSONA_ENGINE

    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY") and v]
    if not api_keys:
        log_error("❌ 제미나이 키 발급 실패로 엔진을 중단합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [시스템 에러] 제미나이 키 발급 실패로 엔진을 중단합니다."})
    else:
        ai_engine = GeminiSniperEngine(api_keys=api_keys)
        AI_ENGINE = ai_engine
        print(f"🤖 제미나이 AI 엔진이 {len(api_keys)}개의 API 키로 가동됩니다.")

    openai_dual_enabled = bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_ENABLED", True))
    openai_shadow_mode = bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_SHADOW_MODE", True))
    openai_api_keys = [v for k, v in CONF.items() if k.startswith("OPENAI_API_KEY") and v]
    if openai_dual_enabled and openai_shadow_mode and openai_api_keys:
        try:
            dual_persona_engine = OpenAIDualPersonaShadowEngine(api_keys=openai_api_keys)
            DUAL_PERSONA_ENGINE = dual_persona_engine
            print(f"🧠 OpenAI 듀얼 페르소나 shadow 엔진이 {len(openai_api_keys)}개의 API 키로 가동됩니다.")
        except Exception as e:
            log_error(f"🚨 OpenAI 듀얼 페르소나 엔진 초기화 실패: {e}")
            dual_persona_engine = None
            DUAL_PERSONA_ENGINE = None
    elif openai_dual_enabled and not openai_api_keys:
        log_info("ℹ️ OPENAI_API_KEY 미설정으로 듀얼 페르소나 shadow 엔진은 비활성화됩니다.")

    bind_analysis_dependencies(ai_engine=AI_ENGINE)
    bind_state_dependencies(dual_persona_engine=DUAL_PERSONA_ENGINE)
    bind_overnight_dependencies(dual_persona_engine=DUAL_PERSONA_ENGINE)

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
        t['strategy'] = normalize_strategy(t.get('strategy'))
        t['position_tag'] = normalize_position_tag(t['strategy'], t.get('position_tag'))

    targets = ACTIVE_TARGETS
    last_db_poll_time = time.time()

    current_market_regime = radar.get_market_regime(KIWOOM_TOKEN)
    regime_kor = "상승장 🐂" if current_market_regime == 'BULL' else "조정장 🐻"
    print(f"📊 [시장 판독] 현재 KOSPI는 '{regime_kor}' 상태입니다.")
    if is_buy_side_paused():
        log_info("[TRADING_PAUSED] engine booted with 신규 매수 및 추가매수 중단 상태 active")

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
            run_sniper.runtime_pause_state = is_buy_side_paused()

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
                    dt['strategy'] = normalize_strategy(dt.get('strategy'))
                    dt['position_tag'] = normalize_position_tag(dt['strategy'], dt.get('position_tag'))
                    code = str(dt.get('code', '')).strip()[:6]
                    identity = target_identity(code, dt['strategy'])
                    if not any(target_identity(t.get('code', ''), t.get('strategy', '')) == identity for t in targets):
                        dt['added_time'] = time.time()
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
                # from src.utils.logger import log_error, log_info
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
