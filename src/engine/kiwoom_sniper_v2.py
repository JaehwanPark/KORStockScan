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
import shlex
import socket
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import math
import numpy as np
import json
import traceback
from sqlalchemy import text

# 💡 Level 1 & 2 공통 모듈 (경로 및 패키지 구조에 맞게 통일)
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.constants import RESTART_FLAG_PATH, TRADING_RULES
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.database.db_manager import (
    DBManager,
    SWING_REAL_WATCHING_ENABLED_ENV,
    is_swing_real_watching_enabled,
    is_swing_real_watching_strategy,
)
from src.core.event_bus import EventBus
from src.database.models import RecommendationHistory
from src.engine.trade_profit import calculate_net_profit_rate
from src.engine.risk.manual_control_exclusion import (
    evaluate_manual_control_exclusion,
    normalize_manual_control_exclusion_code,
)
from src.engine.scalping.rising_missed_selection_prior import (
    rising_missed_selection_rank_delta,
)
from src.engine.scalping.watch_budget import (
    GENERAL_SCALPING,
    OPENING_ROTATION,
    RISING_MISSED,
    classify_owner as classify_watch_budget_owner,
    limits as watch_budget_limits,
    normalize_owner as normalize_watch_budget_owner,
    owner_allowances as watch_budget_owner_allowances,
    slot_type as watch_budget_slot_type,
)
from src.engine.scalping.market_data_enrichment import build_market_data_enrichment
from src.engine.scalping.position_sizing_allocator import (
    ScalpingSizingContext,
    infer_scalping_venue,
    max_position_qty_cap_from_budget,
    resolve_scalping_allocation,
)
from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER
from src.engine.scalping.entry_ai_gate import (
    entry_buy_decision_allowed,
    evaluate_ai_score_prior,
    evaluate_entry_score_role_gate,
    get_entry_buy_score_threshold,
)
from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor
from src.engine.sniper_entry_state import ENTRY_LOCK
from src.engine.sniper_config import CONF
from src.engine.sniper_time import (
    _rule_time,
    _in_time_window,
    TIME_07_00,
    TIME_09_00,
    TIME_09_05,
    TIME_09_10,
    TIME_10_30,
    TIME_11_00,
    TIME_SCALPING_OVERNIGHT_DECISION,
    TIME_MARKET_CLOSE,
    TIME_15_30,
    TIME_20_00,
    TIME_23_59,
    describe_scalping_buy_windows,
    is_scalping_buy_time_allowed,
    scalping_session_venue_provenance,
    scalping_buy_time_block_reason,
)
from src.engine.sniper_s15_fast_track import (
    bind_s15_dependencies,
    _now_ts,
    _arm_s15_candidate,
    _unarm_s15_candidate,
    _restore_armed_candidates_from_database,
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
from src.engine.trade_pause_control import (
    bind_event_bus as bind_trade_pause_event_bus,
    is_buy_side_paused,
)
from src.engine.sniper_position_tags import (
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
    target_identity,
)
from src.engine.sniper_post_sell_feedback import should_retain_ws_subscription

# 💡 뇌(AI)와 눈(웹소켓, 레이더) 임포트
from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.engine.signal_radar import SniperRadar
from src.engine.ai_engine_openai import GPTSniperEngine, OpenAIDualPersonaShadowEngine

# 💡 VIX, 유가지표 임포트
from src.market_regime import MarketRegimeService, summarize_market_regime_snapshot

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
        for ch in "*_``~>#+-=|{}":
            text = text.replace(ch, "\\" + ch)
        return text


bind_condition_dependencies(escape_markdown_fn=escape_markdown)

SCANNER_UNDER_10000_PRIORITY_PRICE_CEILING = 10000


def resolve_runtime_role() -> str:
    """Return runtime role: main (default) or remote."""
    host = socket.gethostname().strip().lower()
    remote_host_hints = ("remote", "windy", "songstockscan", "korstock-test-server")
    host_looks_remote = any(token in host for token in remote_host_hints)
    force_main_on_remote = str(
        os.getenv("KORSTOCKSCAN_FORCE_MAIN_ON_REMOTE", "") or ""
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    explicit = str(os.getenv("KORSTOCKSCAN_RUNTIME_ROLE", "") or "").strip().lower()
    if explicit in {"main", "remote"}:
        if explicit == "main" and host_looks_remote and not force_main_on_remote:
            log_info("[AI_RUNTIME] override main->remote on known remote host")
            return "remote"
        return explicit

    latency_profile = (
        str(os.getenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "") or "").strip().lower()
    )
    if "remote" in latency_profile:
        return "remote"
    if host_looks_remote:
        return "remote"
    return "main"


# --- [전역 상태 변수] -----------------------------------------------
highest_prices = {}
alerted_stocks = set()
cooldowns = {}  # 스캘핑 뇌동매매 방지용 쿨타임 관리
DUAL_PERSONA_ENGINE = None

KIWOOM_TOKEN = None
WS_MANAGER = None
AI_ENGINE = None  # 💡 [추가] AI 엔진을 전역으로 끌어올립니다.
DB = DBManager()
event_bus = EventBus()  # 💡 [신규] 전역 이벤트 버스 장착!
bind_trade_pause_event_bus(event_bus)
bind_s15_dependencies(db=DB)

# 💡 [스레드 안전성] 공유 상태 접근용 락
_state_lock = threading.RLock()

global ACTIVE_TARGETS
ACTIVE_TARGETS = []
LAST_AI_CALL_TIMES = {}
LAST_LOG_TIMES = {}

# ── P0/P1 성능 계측 및 캐시 ─────────────────────────────────────
_MARCAP_CACHE: dict[str, tuple[int, float]] = {}  # code -> (marcap, expiry_ts)
_MARCAP_CACHE_TTL: int = 300  # 5분
_STOCK_NAME_CACHE: dict[str, tuple[str, float]] = {}  # code -> (name, expiry_ts)
_STOCK_NAME_CACHE_TTL: int = 3600
_ACCOUNT_SYNC_EXECUTOR: ThreadPoolExecutor | None = None
_ACCOUNT_SYNC_IN_FLIGHT: bool = False
_SCANNER_OBSERVATION_EXECUTOR = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="scanner_observation"
)
_LOOP_METRICS_LAST_LOG_TS: float = 0.0
_GATEKEEPER_REPORT_NOTIFY_TTL_SEC = 600.0
_GATEKEEPER_REPORT_NOTIFY_RECENT: dict[str, float] = {}
_GATEKEEPER_REPORT_NOTIFY_LOCK = threading.Lock()
_SCANNER_REST_QUOTE_FALLBACK_WINDOW_SEC = 30.0
_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS = 4
_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS = 2
_SCANNER_REST_QUOTE_FALLBACK_FAILURE_COOLDOWN_SEC = 30.0
_SCANNER_REST_QUOTE_FALLBACK_STATE = {"call_epochs": [], "cooldown_until": 0.0}
_SCANNER_REST_QUOTE_FALLBACK_LOCK = threading.Lock()
_SCANNER_MARKET_DATA_ENRICHMENT_CACHE: dict[str, dict] = {}
_SCANNER_MARKET_DATA_ENRICHMENT_LOCK = threading.Lock()
_SCANNER_PROMOTION_PENDING_ATTACH_UNTIL: dict[str, float] = {}
_SCANNER_PROMOTION_PENDING_ATTACH_LOCK = threading.Lock()
_SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC = 5.0
_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_PRESSURE_WINDOW_SEC = 30.0
_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_BOOST_TTL_SEC = 45.0
_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS = 2
_SCANNER_HOT_RUNTIME_OVERRIDE_KEYS = frozenset(
    {
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS_PER_WINDOW",
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS",
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP",
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS",
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC",
        "KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_ENABLED",
        "KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_CACHE_TTL_SEC",
        "KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_HOT_DELTA_PCT",
        "KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC",
        "KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_PERSISTENT_SEC",
        "KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC",
        "KORSTOCKSCAN_SCANNER_WS_SUBSCRIPTION_RECHECK_FRESH_SEC",
        "KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MS",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RELIEF_MS",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_COOLDOWN_SEC",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RECOVERY_STREAK",
        "KORSTOCKSCAN_SCANNER_COMMON_WATCH_BUDGET_PRIORITY_ENABLED",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_ENABLED",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_MIN_COUNT",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_MIN_AGE_SEC",
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_MAX_PER_LOOP",
        "KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE",
        "KORSTOCKSCAN_SCANNER_WATCH_BUDGET_REALLOCATION_ENABLED",
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED",
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE",
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS",
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS",
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC",
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK",
        "KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED",
        "KORSTOCKSCAN_SCALPING_WATCHING_TTL_SEC",
        "KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_ENABLED",
        "KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_DELAY_SEC",
        "KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_MAX_ATTEMPTS",
        "KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC",
    }
)
_SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH = (
    PROJECT_ROOT
    / "data"
    / "threshold_cycle"
    / "runtime_env"
    / "operator_runtime_overrides.env"
)
_SCANNER_HOT_RUNTIME_OVERRIDE_REFRESH_SEC = 5.0
_SCANNER_HOT_RUNTIME_OVERRIDES = {
    "mtime_ns": None,
    "values": {},
    "next_check_ts": 0.0,
}
_SCANNER_HOT_RUNTIME_OVERRIDES_LOCK = threading.Lock()
_SCALPING_DYNAMIC_WATCH_CAP_STATE = {
    "effective_cap": None,
    "last_adjust_ts": 0.0,
    "pressure_streak": 0,
    "relief_streak": 0,
}
_SCANNER_FULL_EVAL_PRESSURE_STATE = {
    "reduction": 0,
    "last_adjust_ts": 0.0,
    "pressure_streak": 0,
    "relief_streak": 0,
}
_SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE = {}
SCANNER_WATCH_EVICTION_POLICY_VERSION = "scalping_scanner_watch_eviction_v7"
SCANNER_WATCH_EVICTION_TERMINAL_MIN_COUNT = 2
SCANNER_WATCH_EVICTION_PREFILTER_HARDGATE_STAGES = {
    "blocked_strength_momentum",
    "blocked_liquidity",
}
SCANNER_WATCH_EVICTION_STALE_MIN_COUNT = 3
SCANNER_WATCH_EVICTION_STALE_MIN_AGE_SEC = 90.0
SCANNER_WATCH_EVICTION_COOLDOWN_MIN_COUNT = 2
SCANNER_WATCH_EVICTION_COOLDOWN_MIN_REMAINING_SEC = 60
SCANNER_WATCH_EVICTION_NO_TRADE_GRACE_SEC = 90.0
SCANNER_WATCH_EVICTION_NO_TRADE_MIN_COUNT = 2
SCANNER_WATCH_EVICTION_NO_TRADE_MAX_PER_LOOP = 4
SCANNER_WATCH_EVICTION_QUEUE_LAG_MIN_SEC = 30.0
SCANNER_WATCH_EVICTION_QUEUE_LAG_MIN_COUNT = 2
SCANNER_WATCH_EVICTION_QUEUE_LAG_IMMEDIATE_SEC = 60.0
SCANNER_WATCH_EVICTION_QUEUE_LAG_MAX_PER_LOOP = 4
SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MIN_COUNT = 3
SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MIN_AGE_SEC = 180.0
SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MAX_PER_LOOP = 4
SCANNER_WATCH_EVICTION_AFTER_BUY_WINDOW_MIN_COUNT = 2
SCANNER_WATCH_EVICTION_AFTER_BUY_WINDOW_MIN_AGE_SEC = 60.0
SCANNER_WATCH_EVICTION_RISING_TERMINAL_RECHECK_DELAY_SEC = 5.0
SCANNER_WATCH_EVICTION_RISING_TERMINAL_RECHECK_MAX_ATTEMPTS = 2
SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC = 60.0
KRX_OPEN_WATCHLIST_RESET_POLICY_VERSION = "krx_open_watchlist_reset_v1"
SCANNER_WATCH_EVICTION_SOURCE_QUALITY_REASONS = {
    "insufficient_history",
    "rising_rest_quote_recovery_without_realtime_strength",
}
SCANNER_WATCH_EVICTION_STALE_REASONS = {
    "rest_quote_without_realtime_strength",
    "subscription_recheck_without_realtime_strength",
    "stale_ws_snapshot",
    "ws_snapshot_missing_or_zero",
    "scanner_fast_precheck_stability_pending",
    *SCANNER_WATCH_EVICTION_SOURCE_QUALITY_REASONS,
}


def _run_account_sync_with_cleanup():
    """periodic_account_sync를 감싸서 예외 발생 시에도 in-flight 플래그를 해제합니다."""
    try:
        periodic_account_sync()
    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        global _ACCOUNT_SYNC_IN_FLIGHT
        _ACCOUNT_SYNC_IN_FLIGHT = False


def _clear_account_sync_in_flight():
    """add_done_callback에서 in-flight 플래그를 해제합니다."""
    global _ACCOUNT_SYNC_IN_FLIGHT
    _ACCOUNT_SYNC_IN_FLIGHT = False


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
    fallback = float(getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT", 3.0) or 3.0)
    strategy_upper = str(strategy or "").upper()
    if strategy_upper == "KOSPI_ML":
        return float(
            getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSPI", fallback) or fallback
        )
    return float(
        getattr(TRADING_RULES, "MAX_SWING_GAP_UP_PCT_KOSDAQ", fallback) or fallback
    )


def _resolve_stock_marcap(stock, code) -> int:
    """시가총액 조회 (프로세스 레벨 TTL 캐시 + stock 캐시)."""
    existing = _safe_int(stock.get("marcap"), 0)
    if existing > 0:
        return existing
    now_ts = time.time()
    norm_code = str(code or "").strip()[:6]
    if norm_code:
        cached = _MARCAP_CACHE.get(norm_code)
        if cached is not None:
            val, exp_ts = cached
            if now_ts < exp_ts and val > 0:
                stock["marcap"] = val
                return val
    try:
        marcap = int(DB.get_latest_marcap(code) or 0)
    except Exception:
        marcap = 0
    if marcap > 0 and norm_code:
        _MARCAP_CACHE[norm_code] = (marcap, now_ts + _MARCAP_CACHE_TTL)
        stock["marcap"] = marcap
    return marcap


def _normalize_identity_name(value) -> str:
    return "".join(ch for ch in str(value or "").strip().upper() if ch.isalnum())


def _latest_stock_name_from_db(code: str) -> str:
    norm_code = str(code or "").strip()[:6]
    if not norm_code:
        return ""
    now_ts = time.time()
    cached = _STOCK_NAME_CACHE.get(norm_code)
    if cached is not None:
        name, exp_ts = cached
        if now_ts < exp_ts:
            return name
    try:
        query = text("""
            SELECT stock_name
            FROM daily_stock_quotes
            WHERE stock_code = :code
              AND COALESCE(stock_name, '') <> ''
            ORDER BY quote_date DESC
            LIMIT 1
            """)
        with DB.get_session() as session:
            name = str(
                session.execute(query, {"code": norm_code}).scalar() or ""
            ).strip()
    except Exception as exc:
        log_error(
            f"[SCANNER_IDENTITY_GUARD] latest stock name lookup failed ({norm_code}): {exc}"
        )
        name = ""
    _STOCK_NAME_CACHE[norm_code] = (name, now_ts + _STOCK_NAME_CACHE_TTL)
    return name


def _scanner_identity_guard(payload, code: str, buy_price: int) -> tuple[bool, dict]:
    """Validate scanner source identity before it can enter real WATCHING runtime."""
    norm_code = str(code or "").strip()[:6]
    payload_name = str((payload or {}).get("name") or "").strip()
    db_name = _latest_stock_name_from_db(norm_code)
    payload_name_norm = _normalize_identity_name(payload_name)
    db_name_norm = _normalize_identity_name(db_name)

    fields = {
        "scanner_identity_guard_applied": True,
        "scanner_identity_guard_reason": "scanner_identity_ok",
        "scanner_identity_payload_name": payload_name or "not_available_payload_name",
        "scanner_identity_db_name": db_name or "not_available_db_name",
        "scanner_identity_ws_curr": "not_available_ws_curr",
        "scanner_identity_price_ratio": "not_available_price_ratio",
    }
    # Test fixtures and some legacy callers may use ASCII aliases such as
    # "SAMSUNG"; enforce name mismatch only for real localized scanner names.
    if (
        payload_name
        and not payload_name.isascii()
        and payload_name_norm
        and db_name_norm
        and payload_name_norm != db_name_norm
    ):
        fields["scanner_identity_guard_reason"] = "scanner_identity_name_mismatch"
        return False, fields

    ws_curr = 0
    try:
        ws_snapshot = WS_MANAGER.get_latest_data(norm_code) if WS_MANAGER else {}
        ws_curr = _safe_int((ws_snapshot or {}).get("curr"), 0)
    except Exception as exc:
        log_error(
            f"[SCANNER_IDENTITY_GUARD] ws snapshot lookup failed ({norm_code}): {exc}"
        )
        ws_curr = 0

    if ws_curr > 0:
        fields["scanner_identity_ws_curr"] = ws_curr
    if buy_price > 0 and ws_curr > 0:
        ratio = float(ws_curr) / float(buy_price)
        fields["scanner_identity_price_ratio"] = round(ratio, 6)
        if ratio < 0.5 or ratio > 2.0:
            fields["scanner_identity_guard_reason"] = "scanner_identity_price_mismatch"
            return False, fields

    return True, fields


def _expire_scanner_identity_mismatch_record(payload, code: str, reason: str) -> bool:
    payload = payload or {}
    record_id = payload.get("record_id") or payload.get("id")
    norm_code = str(code or payload.get("code") or "").strip()[:6]
    if not record_id or not norm_code:
        return False
    try:
        with DB.get_session() as session:
            updated = (
                session.query(RecommendationHistory)
                .filter(
                    RecommendationHistory.id == record_id,
                    RecommendationHistory.stock_code == norm_code,
                    RecommendationHistory.status == "WATCHING",
                    RecommendationHistory.strategy == "SCALPING",
                    RecommendationHistory.position_tag == "SCANNER",
                    RecommendationHistory.buy_time.is_(None),
                    RecommendationHistory.buy_qty == 0,
                )
                .update({"status": "EXPIRED"}, synchronize_session=False)
            )
        if updated:
            log_info(
                f"[SCANNER_IDENTITY_GUARD] expired mismatched scanner WATCHING "
                f"record id={record_id} code={norm_code} reason={reason}"
            )
        return bool(updated)
    except Exception as exc:
        log_error(
            f"[SCANNER_IDENTITY_GUARD] failed to expire mismatched scanner WATCHING "
            f"record id={record_id} code={norm_code} reason={reason}: {exc}"
        )
        return False


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
    stock = stock or {}
    gatekeeper = gatekeeper or {}
    code = str(code or "").strip()[:6]
    stock_name = str(stock.get("name") or code or "UNKNOWN")
    action_label = str(gatekeeper.get("action_label") or "UNKNOWN")
    action_key = str(gatekeeper.get("action_key") or "").strip()
    cache_mode = str(gatekeeper.get("cache_mode") or "").strip()
    report = str(gatekeeper.get("report") or "")
    # 리포트가 길면 첫 200자만 사용
    preview = report[:200] + ("..." if len(report) > 200 else "")
    status = "승인" if allowed else "거부"
    if not allowed:
        log_info(
            f"[Gatekeeper 알림 생략] non_approval source_only "
            f"{stock_name}({code}) action={action_label}"
        )
        return
    if (
        action_key == "not_evaluated_score_vpw_prior"
        or action_label == "NOT_EVALUATED_SCORE_VPW_PRIOR"
        or cache_mode == "not_evaluated"
    ):
        return
    strategy = str(stock.get("strategy") or "").strip().upper()
    simulation_context = (
        bool(stock.get("swing_live_order_dry_run"))
        or bool(stock.get("scalp_live_simulator"))
        or bool(stock.get("simulation_owner"))
        or bool(stock.get("simulation_book"))
        or bool(stock.get("simulated_order"))
        or stock.get("actual_order_submitted") is False
        or (
            strategy in {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}
            and bool(getattr(TRADING_RULES, "SWING_LIVE_ORDER_DRY_RUN_ENABLED", True))
        )
    )
    if simulation_context:
        log_info(
            f"[Gatekeeper 알림 생략] simulation_context source_only "
            f"{stock_name}({code}) action={action_label}"
        )
        return
    if allowed:
        now_ts = time.time()
        dedup_key = "|".join(
            [
                code,
                strategy,
                action_label,
                action_key,
                str(preview or ""),
            ]
        )
        with _GATEKEEPER_REPORT_NOTIFY_LOCK:
            last_sent_at = _GATEKEEPER_REPORT_NOTIFY_RECENT.get(dedup_key, 0.0)
            if now_ts - last_sent_at < _GATEKEEPER_REPORT_NOTIFY_TTL_SEC:
                log_info(
                    f"[Gatekeeper 알림 중복 생략] {stock_name}({code}) "
                    f"action={action_label} ttl_sec={int(_GATEKEEPER_REPORT_NOTIFY_TTL_SEC)}"
                )
                return
            _GATEKEEPER_REPORT_NOTIFY_RECENT[dedup_key] = now_ts
            stale_keys = [
                key
                for key, sent_at in list(_GATEKEEPER_REPORT_NOTIFY_RECENT.items())
                if now_ts - sent_at > (_GATEKEEPER_REPORT_NOTIFY_TTL_SEC * 6)
            ]
            for key in stale_keys:
                _GATEKEEPER_REPORT_NOTIFY_RECENT.pop(key, None)
    audience = "VIP_ALL"
    msg = (
        f"🤖 <b>[Gatekeeper {status}]</b>\n"
        f"🎯 종목: {stock_name} ({code})\n"
        f"⚡ 판정: <b>{action_label}</b>\n"
        f"📄 리포트: {preview}"
    )
    event_bus.publish(
        "TELEGRAM_BROADCAST",
        {"message": msg, "audience": audience, "parse_mode": "HTML"},
    )


def _is_runtime_simulation_target(stock):
    stock = stock or {}
    return (
        bool(stock.get("swing_live_order_dry_run"))
        or bool(stock.get("scalp_live_simulator"))
        or bool(stock.get("simulation_owner"))
        or bool(stock.get("simulation_book"))
        or bool(stock.get("simulated_order"))
        or stock.get("actual_order_submitted") is False
    )


def _is_runtime_scalp_sim_target(stock):
    stock = stock or {}
    strategy = str(stock.get("strategy") or "").strip().upper()
    simulation_book = str(stock.get("simulation_book") or "").strip()
    return (
        bool(stock.get("scalp_live_simulator"))
        or simulation_book == "scalp_ai_buy_all"
        or (
            strategy == "SCALPING"
            and bool(stock.get("simulation_owner"))
            and stock.get("actual_order_submitted") is False
        )
    )


def _is_runtime_probe_target(stock):
    stock = stock or {}
    simulation_book = str(stock.get("simulation_book") or "").strip()
    return (
        bool(stock.get("swing_live_order_dry_run"))
        or bool(stock.get("swing_intraday_probe"))
        or simulation_book == "swing_intraday_live_equiv_probe"
    )


def _send_exit_best_ioc(
    code,
    qty,
    token,
    *,
    dmst_stex_tp=None,
    reason_type=None,
    strategy=None,
):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    return sniper_trade_utils.send_exit_best_ioc(
        code,
        qty,
        token,
        dmst_stex_tp=dmst_stex_tp,
        reason_type=reason_type,
        strategy=strategy,
    )


def _confirm_cancel_or_reload_remaining(code, orig_ord_no, token, expected_qty):
    """[공통 유틸] 주문 취소 후 실제 계좌 잔고를 재조회하여 팔아야 할 정확한 잔량(rem_qty) 반환"""
    return sniper_trade_utils.confirm_cancel_or_reload_remaining(
        code, orig_ord_no, token, expected_qty
    )


bind_execution_dependencies(
    kiwoom_token=KIWOOM_TOKEN,
    db=DB,
    event_bus_instance=event_bus,
    active_targets=ACTIVE_TARGETS,
    highest_prices_map=highest_prices,
    get_fast_state=_get_fast_state,
    weighted_avg=_weighted_avg,
    now_ts=_now_ts,
    state_lock=ENTRY_LOCK,
    probe_fill_continuation_callback=(
        sniper_state_handlers.submit_entry_split_probe_residual_after_fill
    ),
)

_STATE_HANDLER_DEPS = {}


def _ensure_state_handler_deps():
    global _STATE_HANDLER_DEPS
    snapshot = {
        "kiwoom_token": KIWOOM_TOKEN,
        "db": DB,
        "event_bus": event_bus,
        "active_targets": ACTIVE_TARGETS,
        "ws_manager": WS_MANAGER,
        "cooldowns": cooldowns,
        "alerted_stocks": alerted_stocks,
        "highest_prices": highest_prices,
        "last_ai_call_times": LAST_AI_CALL_TIMES,
        "last_log_times": LAST_LOG_TIMES,
        "trading_rules": TRADING_RULES,
        "publish_gatekeeper_report": _publish_gatekeeper_report,
        "should_block_swing_entry": should_block_swing_entry_by_market_regime,
        "confirm_cancel_or_reload_remaining": _confirm_cancel_or_reload_remaining,
        "send_exit_best_ioc": _send_exit_best_ioc,
        "dual_persona_engine": DUAL_PERSONA_ENGINE,
    }
    if any(_STATE_HANDLER_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_state_dependencies(**snapshot)
        _STATE_HANDLER_DEPS = snapshot


def handle_watching_state(
    stock, code, ws_data, admin_id, radar=None, ai_engine=None, now_ts=None, now_dt=None
):
    return sniper_state_handlers.handle_watching_state(
        stock,
        code,
        ws_data,
        admin_id,
        radar=radar,
        ai_engine=ai_engine,
        now_ts=now_ts,
        now_dt=now_dt,
    )


def handle_holding_state(
    stock,
    code,
    ws_data,
    admin_id,
    market_regime,
    radar=None,
    ai_engine=None,
    now_ts=None,
    now_dt=None,
):
    return sniper_state_handlers.handle_holding_state(
        stock,
        code,
        ws_data,
        admin_id,
        market_regime,
        radar=radar,
        ai_engine=ai_engine,
        now_ts=now_ts,
        now_dt=now_dt,
    )


def handle_buy_ordered_state(stock, code):
    return sniper_state_handlers.handle_buy_ordered_state(stock, code)


def handle_sell_ordered_state(stock, code):
    return sniper_state_handlers.handle_sell_ordered_state(stock, code)


def process_sell_cancellation(stock, code, orig_ord_no, db):
    return sniper_state_handlers.process_sell_cancellation(stock, code, orig_ord_no, db)


def process_order_cancellation(stock, code, orig_ord_no, db, strategy):
    return sniper_state_handlers.process_order_cancellation(
        stock, code, orig_ord_no, db, strategy
    )


_EXECUTION_DEPS = {}


def _ensure_execution_deps():
    global _EXECUTION_DEPS
    snapshot = {
        "kiwoom_token": KIWOOM_TOKEN,
        "db": DB,
        "event_bus_instance": event_bus,
        "active_targets": ACTIVE_TARGETS,
        "highest_prices_map": highest_prices,
        "get_fast_state": _get_fast_state,
        "weighted_avg": _weighted_avg,
        "now_ts": _now_ts,
        "probe_fill_continuation_callback": (
            sniper_state_handlers.submit_entry_split_probe_residual_after_fill
        ),
    }
    if any(_EXECUTION_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_execution_dependencies(**snapshot)
        _EXECUTION_DEPS = snapshot


def handle_real_execution(exec_data):
    _ensure_execution_deps()
    return sniper_execution_receipts.handle_real_execution(exec_data)


def handle_order_notice(notice_data):
    _ensure_execution_deps()
    return sniper_execution_receipts.handle_order_notice(notice_data)


_OVERNIGHT_DEPS = {}


def _ensure_overnight_deps():
    global _OVERNIGHT_DEPS
    snapshot = {
        "kiwoom_token": KIWOOM_TOKEN,
        "db": DB,
        "ws_manager": WS_MANAGER,
        "event_bus_instance": event_bus,
        "active_targets": ACTIVE_TARGETS,
        "escape_markdown_fn": escape_markdown,
        "confirm_cancel_or_reload_remaining": _confirm_cancel_or_reload_remaining,
        "send_market_exit_now": _send_market_exit_now,
        "is_ok_response": _is_ok_response,
        "extract_ord_no": _extract_ord_no,
        "process_sell_cancellation_fn": process_sell_cancellation,
        "dual_persona_engine": DUAL_PERSONA_ENGINE,
    }
    if any(_OVERNIGHT_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_overnight_dependencies(**snapshot)
        _OVERNIGHT_DEPS = snapshot


def run_scalping_overnight_gatekeeper(ai_engine=None):
    _ensure_overnight_deps()
    return sniper_overnight_gatekeeper.run_scalping_overnight_gatekeeper(
        ai_engine=ai_engine
    )


_MARKET_REGIME_DEPS = {}


def _ensure_market_regime_deps():
    global _MARKET_REGIME_DEPS
    snapshot = {
        "market_regime": MARKET_REGIME,
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


def _current_market_regime_code() -> str:
    """
    보유/청산 로직이 기대하는 시장 국면 코드(BULL/NEUTRAL/BEAR)를 반환합니다.
    시장환경 서비스 오류가 매매 루프 전체 장애로 번지지 않도록 보수적으로 NEUTRAL로 폴백합니다.
    """
    try:
        market_snapshot = MARKET_REGIME.refresh_if_needed()
        regime_summary = summarize_market_regime_snapshot(market_snapshot)
        return str(regime_summary.get("regime_code") or "NEUTRAL").upper()
    except Exception as exc:
        log_error(f"⚠️ 시장 국면 코드 조회 실패, NEUTRAL 폴백 사용: {exc}")
        return "NEUTRAL"


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


def _prune_ws_subscriptions_for_inactive_targets(targets):
    if not WS_MANAGER:
        return
    subscribed_codes = list(getattr(WS_MANAGER, "subscribed_codes", set()) or [])
    if not subscribed_codes:
        return

    active_codes = {
        str(t.get("code", "")).strip()[:6]
        for t in (targets or [])
        if t.get("status") not in {"COMPLETED", "EXPIRED"}
    }
    now_ts = time.time()
    stale_codes = []
    for code in subscribed_codes:
        norm = str(code or "").strip()[:6]
        if not norm or norm in active_codes:
            continue
        if _is_scanner_promotion_pending_attach(norm, now_ts=now_ts):
            continue
        if should_retain_ws_subscription(norm, now_ts=now_ts):
            continue
        if sniper_state_handlers.should_retain_rising_missed_nxt_post_block_subscription(
            norm,
            now_ts=now_ts,
        ):
            continue
        stale_codes.append(norm)

    if stale_codes:
        event_bus.publish("COMMAND_WS_UNREG", {"codes": stale_codes})
        log_info(
            f"[WS_SUBSCRIPTION_PRUNE] inactive={len(stale_codes)} "
            f"codes={','.join(sorted(set(stale_codes)))}"
        )


def _scanner_promotion_pending_attach_ttl_sec() -> float:
    raw = os.getenv("KORSTOCKSCAN_SCANNER_PROMOTION_PENDING_ATTACH_TTL_SEC", "")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 30.0
    except (TypeError, ValueError):
        value = 30.0
    return max(5.0, min(value, 120.0))


def handle_scalping_scanner_promotion_batch_pending(payload):
    """Protect a promoted WS batch until its runtime targets finish attaching."""
    payload = payload if isinstance(payload, dict) else {}
    codes = {
        str(code or "").strip()[:6]
        for code in (payload.get("codes") or [])
        if str(code or "").strip()[:6]
    }
    if not codes:
        return False
    now_ts = _safe_float(payload.get("emitted_epoch"), time.time())
    if now_ts <= 0:
        now_ts = time.time()
    until_ts = now_ts + _scanner_promotion_pending_attach_ttl_sec()
    with _SCANNER_PROMOTION_PENDING_ATTACH_LOCK:
        expired = [
            code
            for code, current_until in _SCANNER_PROMOTION_PENDING_ATTACH_UNTIL.items()
            if float(current_until or 0.0) <= now_ts
        ]
        for code in expired:
            _SCANNER_PROMOTION_PENDING_ATTACH_UNTIL.pop(code, None)
        for code in codes:
            _SCANNER_PROMOTION_PENDING_ATTACH_UNTIL[code] = max(
                until_ts,
                float(_SCANNER_PROMOTION_PENDING_ATTACH_UNTIL.get(code) or 0.0),
            )
    return True


def _is_scanner_promotion_pending_attach(code, *, now_ts=None) -> bool:
    norm = str(code or "").strip()[:6]
    if not norm:
        return False
    now_value = time.time() if now_ts is None else float(now_ts)
    with _SCANNER_PROMOTION_PENDING_ATTACH_LOCK:
        until_ts = float(_SCANNER_PROMOTION_PENDING_ATTACH_UNTIL.get(norm) or 0.0)
        if until_ts <= now_value:
            _SCANNER_PROMOTION_PENDING_ATTACH_UNTIL.pop(norm, None)
            return False
        return True


def _clear_scanner_promotion_pending_attach(code) -> None:
    norm = str(code or "").strip()[:6]
    if not norm:
        return
    with _SCANNER_PROMOTION_PENDING_ATTACH_LOCK:
        _SCANNER_PROMOTION_PENDING_ATTACH_UNTIL.pop(norm, None)


# =====================================================================
# 🧠 상태 머신 (State Machine) 핸들러
# =====================================================================
def _legacy_current_ai_score(stock):
    if isinstance(stock, dict) and stock.get("current_ai_score") not in (None, "", "-"):
        return _safe_float(stock.get("current_ai_score"), 50.0)
    return _safe_float((stock or {}).get("rt_ai_prob"), 0.5) * 100.0


def _legacy_entry_score_role_gate(stock, ws_data, current_ai_score):
    stock = stock if isinstance(stock, dict) else {}
    ai_action = (
        stock.get("last_watching_ai_action")
        or stock.get("ai_action")
        or stock.get("last_ai_action")
        or ""
    )
    source = (
        stock.get("last_watching_ai_result_source")
        or stock.get("ai_result_source")
        or stock.get("current_ai_score_source")
        or stock.get("ai_score_source")
        or ""
    )
    ai_result = {
        "score": current_ai_score,
        "action": ai_action,
        "ai_result_source": source,
        "ai_parse_ok": stock.get("last_watching_ai_parse_ok", stock.get("ai_parse_ok")),
        "ai_parse_fail": stock.get(
            "last_watching_ai_parse_fail", stock.get("ai_parse_fail")
        ),
        "ai_fallback_score_50": stock.get(
            "ai_fallback_score_50",
            stock.get("last_watching_ai_fallback_score_50", False),
        ),
        "tick_context_stale": stock.get(
            "tick_context_stale", (ws_data or {}).get("tick_context_stale")
        ),
        "quote_stale": stock.get("quote_stale", (ws_data or {}).get("quote_stale")),
        "context_stale": stock.get(
            "context_stale", (ws_data or {}).get("context_stale")
        ),
    }
    gate = evaluate_entry_score_role_gate(
        ai_result,
        ws_data=ws_data,
        source_stage="legacy_kiwoom_sniper_v2_watching",
        ai_score=current_ai_score,
        ai_action=ai_action,
    )
    stock["legacy_entry_score_role_gate"] = gate.get("entry_score_role_gate", "unknown")
    stock["legacy_entry_score_excluded_reason"] = gate.get(
        "entry_score_excluded_reason", "-"
    )
    stock["legacy_entry_score_source"] = gate.get("entry_score_source", "unknown")
    stock["legacy_entry_score_action"] = gate.get("entry_score_action", "-")
    stock["entry_score_role_gate"] = gate.get("entry_score_role_gate", "unknown")
    stock["entry_score_excluded_reason"] = gate.get("entry_score_excluded_reason", "-")
    return gate


def _legacy_holding_score_role_context(stock, current_ai_score, *, is_critical_zone):
    now_ts = time.time()
    ctx = sniper_state_handlers._holding_score_runtime_context(
        stock if isinstance(stock, dict) else {},
        current_ai_score=current_ai_score,
        now_ts=now_ts,
        is_critical_zone=is_critical_zone,
    )
    if isinstance(stock, dict):
        stock["legacy_holding_score_role_gate"] = ctx.get(
            "holding_score_role_gate", "unknown"
        )
        stock["legacy_holding_score_negative_exit_usable"] = bool(
            ctx.get("usable_for_negative_exit", False)
        )
        stock["legacy_holding_score_negative_exit_excluded_reason"] = ctx.get(
            "negative_exit_excluded_reason",
            "-",
        )
        stock["legacy_holding_score_role_source"] = ctx.get("source", "-")
        stock["legacy_holding_score_role_data_quality"] = ctx.get("data_quality", "-")
        stock["holding_score_role_gate"] = ctx.get("holding_score_role_gate", "unknown")
        stock["holding_score_negative_exit_usable"] = bool(
            ctx.get("usable_for_negative_exit", False)
        )
        stock["holding_score_negative_exit_excluded_reason"] = ctx.get(
            "negative_exit_excluded_reason",
            "-",
        )
    return ctx


def check_watching_conditions(
    stock, code, ws_data, admin_id, radar=None, ai_engine=None
):
    """
    WATCHING 상태 종목이 BUY_ORDERED로 전환되지 못하는 이유를 분석하여 문자열로 반환합니다.
    모든 조건을 통과하면 None을 반환합니다.
    """
    global LAST_AI_CALL_TIMES, cooldowns, alerted_stocks, highest_prices

    strategy = normalize_strategy(stock.get("strategy"))
    pos_tag = normalize_position_tag(strategy, stock.get("position_tag"))

    now = datetime.now()
    now_t = now.time()

    # 시간 조건
    if strategy == "SCALPING":
        if not is_scalping_buy_time_allowed(now_t):
            return f"SCALPING 매매 시간대 아님 (현재 {now_t}, 허용 {describe_scalping_buy_windows()})"
    else:
        strategy_start = TIME_09_05
        if now_t < strategy_start:
            return f"시간 조건 불충족 (현재 {now_t}, 시작 {strategy_start})"

    MAX_SURGE = getattr(TRADING_RULES, "MAX_SCALP_SURGE_PCT", 20.0)
    MAX_INTRADAY_SURGE = getattr(TRADING_RULES, "MAX_INTRADAY_SURGE", 15.0)
    MIN_LIQUIDITY = getattr(TRADING_RULES, "MIN_SCALP_LIQUIDITY", 500_000_000)

    if code in cooldowns and time.time() < cooldowns[code]:
        return f"쿨다운 중 (만료 시간 {cooldowns[code]})"

    if code in alerted_stocks:
        return "이미 alerted_stocks에 포함됨"

    curr_price = _safe_int(ws_data.get("curr"), 0)
    if curr_price <= 0:
        return "현재가 유효하지 않음"

    current_vpw = float(ws_data.get("v_pw", 0) or 0)
    fluctuation = float(ws_data.get("fluctuation", 0.0) or 0.0)

    # 초단타 SCALPING 전략 검사
    if strategy == "SCALPING":
        if pos_tag == "VCP_CANDID":
            return "VCP_CANDID 태그로 인한 제외"

        ask_tot = _safe_int(ws_data.get("ask_tot"), 0)
        bid_tot = _safe_int(ws_data.get("bid_tot"), 0)
        open_price = float(ws_data.get("open", curr_price) or curr_price)
        marcap = _resolve_stock_marcap(stock, code)
        turnover_hint = estimate_turnover_hint(curr_price, ws_data.get("volume", 0))
        scalp_limits = get_dynamic_scalp_thresholds(marcap, turnover_hint=turnover_hint)
        intraday_surge = (
            ((curr_price - open_price) / open_price) * 100
            if open_price > 0
            else fluctuation
        )
        liquidity_value = (ask_tot + bid_tot) * curr_price
        max_surge = float(scalp_limits.get("max_surge", MAX_SURGE) or MAX_SURGE)
        max_intraday_surge = float(
            scalp_limits.get("max_intraday_surge", MAX_INTRADAY_SURGE)
            or MAX_INTRADAY_SURGE
        )
        min_liquidity = int(
            scalp_limits.get("min_liquidity", MIN_LIQUIDITY) or MIN_LIQUIDITY
        )

        if fluctuation >= max_surge or intraday_surge >= max_intraday_surge:
            return (
                f"과매수 위험 차단 (fluctuation={fluctuation:.2f} >= {max_surge:.2f} "
                f"또는 intraday_surge={intraday_surge:.2f} >= {max_intraday_surge:.2f}, "
                f"cap={scalp_limits.get('bucket_label')})"
            )

        if pos_tag == "VCP_NEXT":
            # VCP_NEXT는 별도 검사 없이 통과
            pass
        else:
            if radar is None:
                return "radar 객체 없음"
            momentum_ws_data = dict(ws_data or {})
            momentum_ws_data["_position_tag"] = pos_tag
            momentum_gate = evaluate_scalping_strength_momentum(momentum_ws_data)
            if current_vpw < getattr(TRADING_RULES, "VPW_SCALP_LIMIT", 120):
                return (
                    f"VPW 불충족 (current_vpw={current_vpw:.1f} < VPW_SCALP_LIMIT, "
                    f"dynamic_allowed={momentum_gate.get('allowed')}, "
                    f"dynamic_reason={momentum_gate.get('reason')}, "
                    f"dynamic_delta={float(momentum_gate.get('vpw_delta', 0.0) or 0.0):.1f}, "
                    f"dynamic_buy_value={int(momentum_gate.get('window_buy_value', 0) or 0)}, "
                    f"dynamic_profile={momentum_gate.get('threshold_profile')})"
                )
            if liquidity_value < min_liquidity:
                return (
                    f"유동성 불충족 (liquidity_value={liquidity_value:,.0f} < "
                    f"MIN_LIQUIDITY={min_liquidity:,.0f}, cap={scalp_limits.get('bucket_label')})"
                )

            scanner_price = stock.get("buy_price") or 0
            if scanner_price > 0:
                gap_pct = (curr_price - scanner_price) / scanner_price * 100
                if gap_pct >= 1.5:
                    return f"포착가 대비 갭 상승 (gap_pct={gap_pct:.1f}% >= 1.5%)"

            # AI score role gate: legacy diagnostic path follows the main entry submit contract.
            current_ai_score = _legacy_current_ai_score(stock)
            entry_score_role_gate = _legacy_entry_score_role_gate(
                stock, ws_data, current_ai_score
            )
            if not entry_score_role_gate.get("entry_score_usable_for_entry_submit"):
                return (
                    "AI score source unusable "
                    f"(reason={entry_score_role_gate.get('entry_score_excluded_reason', '-')}, "
                    f"source={entry_score_role_gate.get('entry_score_source', 'unknown')})"
                )
            current_ai_action = entry_score_role_gate.get("entry_score_action") or "-"
            if not entry_buy_decision_allowed(current_ai_action, current_ai_score):
                score_prior = evaluate_ai_score_prior(
                    current_ai_action,
                    current_ai_score,
                    usable=bool(
                        entry_score_role_gate.get("entry_score_usable_for_entry_submit")
                    ),
                )
                stock["legacy_entry_score_prior_band"] = score_prior.get(
                    "score_prior_band"
                )
                stock["legacy_entry_score_prior_weight"] = score_prior.get(
                    "ai_score_prior_weight"
                )
                stock["legacy_score_gate_converted_to_prior"] = True
                return (
                    f"AI action BUY 아님 "
                    f"(action={current_ai_action}, current_ai_score={current_ai_score})"
                )

    # 스윙 전략 검사 (KOSDAQ_ML / KOSPI_ML)
    elif strategy in ["KOSDAQ_ML", "KOSPI_ML"]:
        if radar is None:
            return "radar 객체 없음 (KOSDAQ_ML/KOSPI_ML)"

        marcap = _resolve_stock_marcap(stock, code)
        turnover_hint = estimate_turnover_hint(curr_price, ws_data.get("volume", 0))
        swing_gap = get_dynamic_swing_gap_threshold(
            strategy, marcap, turnover_hint=turnover_hint
        )
        max_gap = float(
            swing_gap.get("threshold", _get_swing_gap_threshold(strategy))
            or _get_swing_gap_threshold(strategy)
        )
        if fluctuation >= max_gap:
            return (
                f"갭상승 너무 큼 (fluctuation={fluctuation:.2f} >= max_gap={max_gap:.2f}, "
                f"cap={swing_gap.get('bucket_label')})"
            )

        # 추가 검사 생략 (복잡성으로 인해)
        # AI score is retained as a prior feature only; it no longer blocks swing diagnostics by itself.
        current_ai_score = float(stock.get("rt_ai_prob", 0.5) or 0.5) * 100
        ai_score_threshold = (
            getattr(TRADING_RULES, "AI_SCORE_THRESHOLD_KOSDAQ", 60)
            if strategy == "KOSDAQ_ML"
            else getattr(TRADING_RULES, "AI_SCORE_THRESHOLD_KOSPI", 60)
        )
        swing_score_prior = evaluate_ai_score_prior(
            "BUY",
            current_ai_score,
            {"SWING_AI_SCORE_THRESHOLD": ai_score_threshold},
            threshold_key="SWING_AI_SCORE_THRESHOLD",
            default_threshold=ai_score_threshold,
            usable=current_ai_score != 50,
        )
        stock["swing_ai_score_prior_band"] = swing_score_prior.get("score_prior_band")
        stock["swing_ai_score_prior_weight"] = swing_score_prior.get(
            "ai_score_prior_weight"
        )
        stock["swing_score_gate_converted_to_prior"] = True

    # 공통 관리자 ID 체크
    if not admin_id:
        return "관리자 ID 없음"

    # 매수 수량 체크 (자금 부족)
    deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
    budget_cap = 0
    if strategy == "SCALPING":
        budget_cap = int(getattr(TRADING_RULES, "SCALPING_MAX_BUY_BUDGET_KRW", 0) or 0)
        sizing_now = datetime.now()
        sizing_decision = resolve_scalping_allocation(
            ScalpingSizingContext(
                allocation_stage="legacy_precheck",
                reference_time=sizing_now,
                source_signature=stock.get("source_signature")
                or stock.get("scanner_source_signature"),
                effective_venue=infer_scalping_venue(
                    sizing_now,
                    stock.get("rising_missed_effective_venue")
                    or stock.get("effective_venue"),
                ),
                budget_base_krw=deposit,
                price_krw=curr_price,
                absolute_budget_cap_krw=budget_cap,
                max_position_qty_cap=max_position_qty_cap_from_budget(
                    deposit,
                    curr_price,
                    getattr(TRADING_RULES, "MAX_POSITION_PCT", 0.20),
                ),
                min_one_share_floor_enabled=bool(
                    getattr(TRADING_RULES, "SCALPING_MIN_ONE_SHARE_FLOOR_ENABLED", True)
                ),
            )
        )
        target_budget = sizing_decision.target_budget
        safe_budget = sizing_decision.safe_budget
        real_buy_qty = sizing_decision.effective_qty
        used_safety_ratio = sizing_decision.safety_ratio
        ratio = sizing_decision.ratio
    else:
        ratio = stock.get("ratio", 0.1)
        target_budget, safe_budget, real_buy_qty, used_safety_ratio = (
            kiwoom_orders.describe_buy_capacity(
                curr_price,
                deposit,
                ratio,
                max_budget=budget_cap,
                allow_min_one_share_over_budget=False,
            )
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
    hold_time = stock.get("holding_started_at") or stock.get("buy_time")
    if not hold_time:
        return None
    if isinstance(hold_time, datetime):
        return hold_time
    try:
        return datetime.fromisoformat(str(hold_time))
    except Exception:
        return None


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().lower() in {
            "",
            "nan",
            "nat",
            "none",
            "inf",
            "+inf",
            "-inf",
        }:
            return default
        numeric = float(value)
        if not math.isfinite(numeric):
            return default
        return int(numeric)
    except Exception:
        return default


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().lower() in {
            "",
            "nan",
            "nat",
            "none",
            "inf",
            "+inf",
            "-inf",
        }:
            return default
        numeric = float(value)
        if not math.isfinite(numeric):
            return default
        return numeric
    except Exception:
        return default


def _runtime_priority_price(target):
    target = target or {}
    for key in ("current_price", "curr_price", "curr", "buy_price", "price", "Price"):
        price = abs(_safe_int(target.get(key), 0))
        if price > 0:
            return price
    return 0


def _under_10000_runtime_priority_rank(target):
    price = _runtime_priority_price(target)
    return 1 if 0 < price < SCANNER_UNDER_10000_PRIORITY_PRICE_CEILING else 0


def _is_disabled_swing_watching_target(target) -> bool:
    status = str((target or {}).get("status") or "").upper()
    if status != "WATCHING":
        return False
    return (
        is_swing_real_watching_strategy((target or {}).get("strategy"))
        and not is_swing_real_watching_enabled()
    )


def _filter_disabled_swing_watching_targets(targets):
    kept = []
    skipped = 0
    for target in targets or []:
        if _is_disabled_swing_watching_target(target):
            skipped += 1
            continue
        kept.append(target)
    if skipped:
        log_info(
            f"[SWING_REAL_WATCHING_DISABLED] filtered {skipped} boot WATCHING targets "
            f"env={SWING_REAL_WATCHING_ENABLED_ENV}"
        )
    return kept


def _env_bool(name, default=False):
    raw = os.getenv(name, "")
    return _env_bool_from_value(raw, default)


def _env_bool_from_value(raw, default=False):
    text = str(raw).strip().lower()
    if not text:
        return bool(default)
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _parse_scanner_hot_runtime_override_file(path):
    values = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for raw_line in lines:
        line = str(raw_line or "").strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in _SCANNER_HOT_RUNTIME_OVERRIDE_KEYS:
            continue
        value = value.strip()
        try:
            parts = shlex.split(value, comments=False, posix=True)
            parsed_value = parts[0] if parts else ""
        except ValueError:
            parsed_value = value.strip("\"'")
        values[key] = str(parsed_value).strip()
    return values


def _scanner_hot_runtime_override_value(name, now_ts=None):
    key = str(name or "").strip()
    if key not in _SCANNER_HOT_RUNTIME_OVERRIDE_KEYS:
        return None
    now_value = time.time() if now_ts is None else float(now_ts)
    with _SCANNER_HOT_RUNTIME_OVERRIDES_LOCK:
        cache = _SCANNER_HOT_RUNTIME_OVERRIDES
        if now_value < _safe_float(cache.get("next_check_ts"), 0.0):
            return (cache.get("values") or {}).get(key)
        cache["next_check_ts"] = now_value + _SCANNER_HOT_RUNTIME_OVERRIDE_REFRESH_SEC
        path = _SCANNER_OPERATOR_RUNTIME_OVERRIDE_PATH
        try:
            stat = Path(path).stat()
            mtime_ns = int(getattr(stat, "st_mtime_ns", 0) or 0)
        except OSError:
            cache["mtime_ns"] = None
            cache["values"] = {}
            return None
        if cache.get("mtime_ns") != mtime_ns:
            cache["values"] = _parse_scanner_hot_runtime_override_file(path)
            cache["mtime_ns"] = mtime_ns
        return (cache.get("values") or {}).get(key)


def _scanner_hot_or_env_value(name):
    hot_value = _scanner_hot_runtime_override_value(name)
    if hot_value not in (None, ""):
        return hot_value
    return os.getenv(name, "")


def _scanner_no_trade_eviction_enabled():
    return _env_bool("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_ENABLED", True)


def _scanner_rest_quote_stale_eviction_max_watch_age_sec():
    raw = os.getenv(
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_STALE_EVICTION_MAX_WATCH_AGE_SEC", ""
    )
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 300.0
    except Exception:
        value = 300.0
    return max(60.0, min(value, 1800.0))


def _scanner_no_trade_eviction_grace_sec():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_GRACE_SEC", "")
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_NO_TRADE_GRACE_SEC
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_NO_TRADE_GRACE_SEC
    return max(30.0, min(value, 900.0))


def _scanner_no_trade_eviction_min_count():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_MIN_COUNT", "")
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_NO_TRADE_MIN_COUNT
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_NO_TRADE_MIN_COUNT
    return max(1, min(value, 20))


def _scanner_no_trade_eviction_max_per_loop():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_NO_TRADE_EVICTION_MAX_PER_LOOP", "")
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_NO_TRADE_MAX_PER_LOOP
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_NO_TRADE_MAX_PER_LOOP
    return max(0, min(value, 20))


def _scanner_queue_lag_eviction_enabled():
    return _env_bool("KORSTOCKSCAN_SCANNER_QUEUE_LAG_EVICTION_ENABLED", True)


def _scanner_queue_lag_eviction_min_sec():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_QUEUE_LAG_EVICTION_MIN_SEC", "")
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_QUEUE_LAG_MIN_SEC
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_QUEUE_LAG_MIN_SEC
    return max(5.0, min(value, 300.0))


def _scanner_queue_lag_eviction_min_count():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_QUEUE_LAG_EVICTION_MIN_COUNT", "")
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_QUEUE_LAG_MIN_COUNT
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_QUEUE_LAG_MIN_COUNT
    return max(1, min(value, 20))


def _scanner_queue_lag_eviction_immediate_sec():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_QUEUE_LAG_EVICTION_IMMEDIATE_SEC", "")
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_QUEUE_LAG_IMMEDIATE_SEC
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_QUEUE_LAG_IMMEDIATE_SEC
    return max(_scanner_queue_lag_eviction_min_sec(), min(value, 600.0))


def _scanner_queue_lag_eviction_max_per_loop():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_QUEUE_LAG_EVICTION_MAX_PER_LOOP", "")
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_QUEUE_LAG_MAX_PER_LOOP
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_QUEUE_LAG_MAX_PER_LOOP
    return max(0, min(value, 20))


def _scanner_full_eval_deferred_eviction_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_ENABLED"
    )
    return _env_bool_from_value(raw, True)


def _scanner_full_eval_deferred_eviction_min_count():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_MIN_COUNT"
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MIN_COUNT
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MIN_COUNT
    return max(1, min(value, 20))


def _scanner_full_eval_deferred_eviction_min_age_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_MIN_AGE_SEC"
    )
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MIN_AGE_SEC
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MIN_AGE_SEC
    return max(_scanner_fifo_new_promotion_grace_sec(), min(value, 900.0))


def _scanner_full_eval_deferred_eviction_max_per_loop():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_DEFERRED_EVICTION_MAX_PER_LOOP"
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MAX_PER_LOOP
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_FULL_EVAL_DEFERRED_MAX_PER_LOOP
    return max(0, min(value, 20))


def _scanner_after_buy_window_source_quality_eviction_enabled():
    return _env_bool(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_SOURCE_QUALITY_EVICTION_ENABLED", True
    )


def _scanner_after_buy_window_source_quality_eviction_min_count():
    raw = os.getenv(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_SOURCE_QUALITY_EVICTION_MIN_COUNT", ""
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_AFTER_BUY_WINDOW_MIN_COUNT
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_AFTER_BUY_WINDOW_MIN_COUNT
    return max(1, min(value, 20))


def _scanner_after_buy_window_source_quality_eviction_min_age_sec():
    raw = os.getenv(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_SOURCE_QUALITY_EVICTION_MIN_AGE_SEC", ""
    )
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_AFTER_BUY_WINDOW_MIN_AGE_SEC
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_AFTER_BUY_WINDOW_MIN_AGE_SEC
    return max(10.0, min(value, 900.0))


def _scanner_rising_terminal_hardgate_recheck_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_ENABLED"
    )
    text = str(raw).strip().lower()
    if text == "":
        return True
    return text in {"1", "true", "yes", "y", "on"}


def _scanner_rising_terminal_hardgate_recheck_delay_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_DELAY_SEC"
    )
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_RISING_TERMINAL_RECHECK_DELAY_SEC
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_RISING_TERMINAL_RECHECK_DELAY_SEC
    return max(1.0, min(value, 60.0))


def _scanner_rising_terminal_hardgate_recheck_max_attempts():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_RISING_TERMINAL_HARDGATE_RECHECK_MAX_ATTEMPTS"
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else SCANNER_WATCH_EVICTION_RISING_TERMINAL_RECHECK_MAX_ATTEMPTS
        )
    except Exception:
        value = SCANNER_WATCH_EVICTION_RISING_TERMINAL_RECHECK_MAX_ATTEMPTS
    return max(0, min(value, 10))


def _scanner_fifo_new_promotion_grace_sec():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC")
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC
        )
    except Exception:
        value = SCANNER_FIFO_NEW_PROMOTION_GRACE_SEC
    return max(0.0, min(value, 300.0))


def _scanner_scalping_buy_window_closed(now_ts):
    try:
        now_t = datetime.fromtimestamp(float(now_ts)).time()
    except Exception:
        now_t = datetime.now().time()
    override_raw = os.getenv(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_SOURCE_QUALITY_EVICTION_START_TIME", ""
    )
    if str(override_raw).strip():
        try:
            override_start = datetime.strptime(
                str(override_raw).strip(), "%H:%M:%S"
            ).time()
            if now_t >= override_start:
                return True
        except Exception:
            pass
    return scalping_buy_time_block_reason(now_t) == "scalping_new_buy_cutoff"


def _scanner_ws_reg_recovery_throttle_allows(
    last_emit_ts, source, code, now_ts, *, min_interval_sec=10.0
):
    norm_code = str(code or "").strip()[:6]
    if not norm_code:
        return False
    source_key = str(source or "scanner_watching_ws_snapshot_recovery")
    try:
        code_min_interval_sec = float(
            os.getenv("KORSTOCKSCAN_SCANNER_WS_REG_RECOVERY_CODE_TTL_SEC", "20") or 20.0
        )
    except Exception:
        code_min_interval_sec = 20.0
    code_min_interval_sec = max(0.0, min(120.0, code_min_interval_sec))
    code_throttle_key = ("__all_recovery_sources__", norm_code)
    code_last_ts = float((last_emit_ts or {}).get(code_throttle_key) or 0.0)
    if (
        code_min_interval_sec > 0
        and float(now_ts) - code_last_ts < code_min_interval_sec
    ):
        return False
    throttle_key = (source_key, norm_code)
    last_ts = float((last_emit_ts or {}).get(throttle_key) or 0.0)
    if float(now_ts) - last_ts < float(min_interval_sec):
        return False
    last_emit_ts[code_throttle_key] = float(now_ts)
    last_emit_ts[throttle_key] = float(now_ts)
    return True


def _scanner_runtime_target_event_fields(payload, *, outcome, reason, target=None):
    payload = payload or {}
    target = target or {}
    existing = payload.get("existing_target")
    if not isinstance(existing, dict):
        existing = {}
    tp1_context = target.get("tp1_context")
    if not isinstance(tp1_context, dict):
        tp1_context = {}
    venue_candidates = (
        (
            "payload.rising_missed_effective_venue",
            payload.get("rising_missed_effective_venue"),
        ),
        ("payload.effective_venue", payload.get("effective_venue")),
        ("payload.venue", payload.get("venue")),
        (
            "target.rising_missed_effective_venue",
            target.get("rising_missed_effective_venue"),
        ),
        (
            "target.tp1_context.rising_missed_effective_venue",
            tp1_context.get("rising_missed_effective_venue"),
        ),
        ("target.effective_venue", target.get("effective_venue")),
        ("target.venue", target.get("venue")),
    )
    explicit_venues = []
    supported_cohorts = {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
    for venue_source, venue_value in venue_candidates:
        normalized_venue = str(venue_value or "").strip().upper()
        if normalized_venue in supported_cohorts:
            explicit_venues.append((venue_source, normalized_venue))
    unique_venues = {venue for _, venue in explicit_venues}
    if len(unique_venues) == 1:
        canonical_venue = next(iter(unique_venues))
        venue_resolution = "consistent_explicit:" + ",".join(
            source for source, _ in explicit_venues
        )
    elif unique_venues:
        canonical_venue = "UNKNOWN"
        venue_resolution = "conflicting_explicit_venue:" + ",".join(
            f"{source}={venue}" for source, venue in explicit_venues
        )
    else:
        canonical_venue = "UNKNOWN"
        venue_resolution = "missing_tradable_explicit_venue"
    return {
        "metric_role": "runtime_handoff_observation",
        "decision_authority": "real_scalping_scanner_runtime_watchlist_handoff_only",
        "source_quality_gate": "scalping_scanner_runtime_target_attach_contract",
        "window_policy": "intraday_runtime_handoff",
        "sample_floor": "not_applicable_runtime_handoff",
        "primary_decision_metric": "funnel_count",
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
        ),
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "venue": canonical_venue,
        "effective_venue": canonical_venue,
        "venue_resolution": venue_resolution,
        "runtime_target_attach_outcome": outcome,
        "runtime_target_attach_reason": reason,
        "manual_control_exclusion_applied": payload.get(
            "manual_control_exclusion_applied", False
        ),
        "manual_control_exclusion_code": payload.get("manual_control_exclusion_code")
        or "not_applicable_manual_control_exclusion_code",
        "manual_control_exclusion_reason": payload.get(
            "manual_control_exclusion_reason"
        )
        or "not_applicable_manual_control_exclusion_reason",
        "manual_control_exclusion_source": payload.get(
            "manual_control_exclusion_source"
        )
        or "not_applicable_manual_control_exclusion_source",
        "scanner_attach_capacity_cap": payload.get("scanner_attach_capacity_cap")
        or "not_applicable_scanner_attach_capacity_cap",
        "scanner_attach_capacity_watching_count": payload.get(
            "scanner_attach_capacity_watching_count"
        )
        or "not_applicable_scanner_attach_capacity_watching_count",
        "scanner_attach_capacity_candidate_overflow": (
            payload.get("scanner_attach_capacity_candidate_overflow")
            if payload.get("scanner_attach_capacity_candidate_overflow") is not None
            else "not_applicable_scanner_attach_capacity_candidate_overflow"
        ),
        "scanner_watch_budget_owner": payload.get("scanner_watch_budget_owner")
        or target.get("scanner_watch_budget_owner")
        or "not_applicable_scanner_watch_budget_owner",
        "scanner_watch_budget_policy": payload.get("scanner_watch_budget_policy")
        or target.get("scanner_watch_budget_policy")
        or "not_applicable_scanner_watch_budget_policy",
        "scanner_watch_budget_owner_source": payload.get(
            "scanner_watch_budget_owner_source"
        )
        or target.get("scanner_watch_budget_owner_source")
        or "not_applicable_scanner_watch_budget_owner_source",
        "scanner_watch_budget_slot_type": payload.get("scanner_watch_budget_slot_type")
        or target.get("scanner_watch_budget_slot_type")
        or "not_applicable_scanner_watch_budget_slot_type",
        "scanner_watch_budget_candidate_overflow": payload.get(
            "scanner_watch_budget_candidate_overflow",
            "not_applicable_scanner_watch_budget_candidate_overflow",
        ),
        "scanner_watch_budget_replacement_count": payload.get(
            "scanner_watch_budget_replacement_count",
            "not_applicable_scanner_watch_budget_replacement_count",
        ),
        "runtime_record_id": payload.get("record_id")
        or target.get("id")
        or "not_applicable_runtime_record_id",
        "scanner_promotion_id": payload.get("scanner_promotion_id")
        or "not_applicable_scanner_promotion_id",
        "scanner_promotion_reason": payload.get("scanner_promotion_reason")
        or "not_applicable_scanner_promotion_reason",
        "scanner_promotion_emitted_epoch": payload.get(
            "scanner_promotion_emitted_epoch"
        )
        or "not_applicable_scanner_promotion_emitted_epoch",
        "source_signature": payload.get("source_signature")
        or "not_applicable_source_signature",
        "scanner_source_family": payload.get("scanner_source_family") or "",
        "scanner_source_role": payload.get("scanner_source_role") or "",
        "rank_change": payload.get("rank_change", "not_applicable_rank_change"),
        "rank_change_sign": payload.get(
            "rank_change_sign", "not_applicable_rank_change_sign"
        ),
        "rank_change_sign_authority": payload.get(
            "rank_change_sign_authority",
            "raw_unverified_not_decision_input",
        ),
        "rank_change_sign_state": payload.get(
            "rank_change_sign_state",
            "not_applicable_rank_change_sign_state",
        ),
        "rank_change_sign_consistency": payload.get(
            "rank_change_sign_consistency",
            "not_applicable_rank_change_sign_consistency",
        ),
        "rank_change_score_input": payload.get(
            "rank_change_score_input",
            "not_applicable_rank_change_score_input",
        ),
        "rank_change_score_policy": payload.get(
            "rank_change_score_policy",
            "positive_signed_rank_delta_only_raw_rank_sign_unverified",
        ),
        "current_price_observed": payload.get("current_price_observed")
        or payload.get("buy_price")
        or "",
        "price_delta_since_first_seen_pct": payload.get(
            "price_delta_since_first_seen_pct"
        )
        or "",
        "rising_missed_lineage": payload.get("rising_missed_lineage") or "",
        "low_rebound_pct": payload.get("low_rebound_pct") or "",
        "intraday_low_price": payload.get("intraday_low_price") or "",
        "intraday_high_price": payload.get("intraday_high_price") or "",
        "distance_from_intraday_high_pct": payload.get(
            "distance_from_intraday_high_pct"
        )
        or "",
        "negative_display_rebound": (
            payload.get("negative_display_rebound")
            if payload.get("negative_display_rebound") is not None
            else ""
        ),
        "target_status": target.get("status")
        or payload.get("status")
        or "not_applicable_target_status",
        "target_strategy": target.get("strategy")
        or payload.get("strategy")
        or "not_applicable_target_strategy",
        "target_position_tag": target.get("position_tag")
        or payload.get("position_tag")
        or "not_applicable_target_position_tag",
        "existing_status": existing.get("status") or "not_applicable_existing_status",
        "existing_strategy": existing.get("strategy")
        or "not_applicable_existing_strategy",
        "existing_position_tag": existing.get("position_tag")
        or "not_applicable_existing_position_tag",
        "existing_runtime_record_id": existing.get("id")
        or "not_applicable_existing_runtime_record_id",
        "existing_actual_order_submitted": (
            existing.get("actual_order_submitted")
            if existing.get("actual_order_submitted") is not None
            else "not_applicable_existing_actual_order_submitted"
        ),
        "scanner_identity_guard_applied": payload.get(
            "scanner_identity_guard_applied", "not_evaluated"
        ),
        "scanner_identity_guard_reason": payload.get(
            "scanner_identity_guard_reason", "not_evaluated"
        ),
        "scanner_identity_payload_name": payload.get(
            "scanner_identity_payload_name", "not_evaluated"
        ),
        "scanner_identity_db_name": payload.get(
            "scanner_identity_db_name", "not_evaluated"
        ),
        "scanner_identity_ws_curr": payload.get(
            "scanner_identity_ws_curr", "not_evaluated"
        ),
        "scanner_identity_price_ratio": payload.get(
            "scanner_identity_price_ratio", "not_evaluated"
        ),
        "scanner_identity_mismatch_expired": payload.get(
            "scanner_identity_mismatch_expired", False
        ),
        "scanner_positive_delta_context_preserved": bool(
            payload.get("scanner_positive_delta_context_preserved", False)
        ),
        "scanner_positive_delta_context_previous_pct": payload.get(
            "scanner_positive_delta_context_previous_pct",
            "not_applicable_positive_delta_context_previous_pct",
        ),
        "scanner_positive_delta_context_incoming_pct": payload.get(
            "scanner_positive_delta_context_incoming_pct",
            "not_applicable_positive_delta_context_incoming_pct",
        ),
    }


def _log_scanner_runtime_target_attach(payload, *, outcome, reason, target=None):
    payload = payload or {}
    target = target or {}
    code = str(payload.get("code") or target.get("code") or "").strip()[:6]
    try:
        emit_pipeline_event(
            "ENTRY_PIPELINE",
            str(payload.get("name") or target.get("name") or "-"),
            code,
            "scalping_scanner_runtime_target_attach",
            fields=_scanner_runtime_target_event_fields(
                payload, outcome=outcome, reason=reason, target=target
            ),
        )
    finally:
        _clear_scanner_promotion_pending_attach(code)


def _resolve_scanner_runtime_record_id(payload, code, strategy):
    record_id = payload.get("record_id")
    if record_id not in (None, ""):
        return record_id
    if DB is None or not hasattr(DB, "find_reusable_watching_record"):
        return None

    try:
        with DB.get_session() as session:
            record = DB.find_reusable_watching_record(
                session,
                rec_date=datetime.now().date(),
                stock_code=code,
                strategy=strategy,
                position_tag="SCANNER",
            )
            return getattr(record, "id", None) if record is not None else None
    except Exception as exc:
        log_error(
            f"[SCALPING_SCANNER_PROMOTED_TARGET] record id fallback failed ({code}): {exc}"
        )
        return None


def _is_scanner_runtime_target(target):
    strategy = normalize_strategy((target or {}).get("strategy"))
    position_tag = normalize_position_tag(strategy, (target or {}).get("position_tag"))
    return strategy == "SCALPING" and position_tag == "SCANNER"


def _is_scanner_watching_target(target):
    target = target or {}
    return (
        _is_scanner_runtime_target(target)
        and str(target.get("status") or "").upper() == "WATCHING"
    )


def _is_scanner_watch_eviction_candidate(target):
    target = target or {}
    if not _is_scanner_watching_target(target):
        return False
    buy_time_value = target.get("buy_time")
    if buy_time_value not in (None, "", 0) and str(
        buy_time_value
    ).strip().lower() not in {
        "none",
        "nan",
        "nat",
    }:
        return False
    if _safe_int(target.get("buy_qty"), 0) != 0:
        return False
    if not target.get("id"):
        return False
    return True


def _krx_open_epoch_for(now_dt):
    now_dt = now_dt or datetime.now()
    return datetime.combine(now_dt.date(), TIME_09_00).timestamp()


def _is_krx_open_watchlist_reset_candidate(target, *, now_dt=None):
    target = target or {}
    if str(target.get("status") or "").upper() != "WATCHING":
        return False
    if target.get("buy_time") not in (None, "", 0):
        return False
    if _safe_int(target.get("buy_qty"), 0) != 0:
        return False
    if not target.get("id"):
        return False
    now_dt = now_dt or datetime.now()
    open_epoch = _krx_open_epoch_for(now_dt)
    anchor_epoch = _runtime_added_time_for_target(target, now_ts=now_dt.timestamp())
    return anchor_epoch < open_epoch


def _krx_open_watchlist_reset_fields(target, *, now_dt):
    strategy = normalize_strategy((target or {}).get("strategy"))
    return {
        "metric_role": "runtime_watchlist_pool_management",
        "decision_authority": "krx_open_watchlist_reset_pool_management_only",
        "window_policy": "krx_open_once_per_trading_day",
        "sample_floor": "not_applicable_runtime_pool_management",
        "primary_decision_metric": "krx_open_reprice_watchlist_reset",
        "source_quality_gate": "krx_open_watchlist_reset_contract",
        "source_quality_route": "runtime_watchlist_reset_pool_management_only",
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
        ),
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "reset_policy_version": KRX_OPEN_WATCHLIST_RESET_POLICY_VERSION,
        "reset_reason": "krx_open_reprice_watchlist_reset",
        "reset_scope": "watching_without_position_or_order",
        "runtime_record_id": (target or {}).get("id")
        or "not_applicable_runtime_record_id",
        "stock_code": str((target or {}).get("code") or "").strip()[:6]
        or "not_applicable_stock_code",
        "target_status": (target or {}).get("status") or "not_applicable_target_status",
        "target_strategy": strategy,
        "target_position_tag": normalize_position_tag(
            strategy, (target or {}).get("position_tag")
        ),
        "observed_at": (now_dt or datetime.now()).isoformat(),
    }


def _reset_krx_open_watch_targets(targets, *, now_dt=None, emit_event_fn=None):
    now_dt = now_dt or datetime.now()
    if now_dt.time() < TIME_09_00:
        return []
    reset_targets = [
        target
        for target in list(targets or [])
        if _is_krx_open_watchlist_reset_candidate(target, now_dt=now_dt)
    ]
    if not reset_targets:
        return []
    reset_ids = [target.get("id") for target in reset_targets if target.get("id")]
    updated = 0
    try:
        with DB.get_session() as session:
            updated = (
                session.query(RecommendationHistory)
                .filter(
                    RecommendationHistory.id.in_(reset_ids),
                    RecommendationHistory.status == "WATCHING",
                    RecommendationHistory.buy_time.is_(None),
                    RecommendationHistory.buy_qty == 0,
                )
                .update({"status": "EXPIRED"}, synchronize_session=False)
            )
    except Exception as exc:
        log_error(f"🚨 [KRX_OPEN_WATCHLIST_RESET] DB update failed: {exc}")
        return []
    if updated <= 0:
        return []
    updated_ids = set(reset_ids)
    reset_codes = []
    for target in targets or []:
        if target.get("id") not in updated_ids:
            continue
        if not _is_krx_open_watchlist_reset_candidate(target, now_dt=now_dt):
            continue
        fields = _krx_open_watchlist_reset_fields(target, now_dt=now_dt)
        target["status"] = "EXPIRED"
        code = str(target.get("code") or "").strip()[:6]
        if code:
            reset_codes.append(code)
        if emit_event_fn:
            emit_event_fn(target, code, "krx_open_watchlist_reset", fields)
        else:
            sniper_state_handlers._log_entry_pipeline(
                target, code, "krx_open_watchlist_reset", **fields
            )
    return reset_codes


def _scanner_watch_reset_terminal_eviction_state(target):
    if not isinstance(target, dict):
        return
    target.pop("_scanner_watch_eviction_terminal_stage", None)
    target.pop("_scanner_watch_eviction_terminal_reason", None)
    target.pop("_scanner_watch_eviction_terminal_count", None)
    target.pop("_scanner_watch_eviction_last_terminal_observed_epoch", None)


def _scanner_watch_reset_stale_eviction_state(target):
    if not isinstance(target, dict):
        return
    target.pop("_scanner_watch_eviction_stale_first_seen_epoch", None)
    target.pop("_scanner_watch_eviction_stale_count", None)


def _scanner_watch_reset_pool_block_eviction_state(target):
    if not isinstance(target, dict):
        return
    target.pop("_scanner_watch_eviction_pool_block_reason", None)
    target.pop("_scanner_watch_eviction_pool_block_count", None)
    target.pop("_scanner_watch_eviction_last_pool_block_observed_epoch", None)


def _scanner_watch_reset_queue_lag_eviction_state(target):
    if not isinstance(target, dict):
        return
    target.pop("_scanner_watch_queue_lag_count", None)
    target.pop("_scanner_watch_queue_lag_first_observed_epoch", None)
    target.pop("_scanner_watch_queue_lag_last_observed_epoch", None)


def _scanner_watch_reset_full_eval_deferred_eviction_state(target):
    if not isinstance(target, dict):
        return
    target.pop("_scanner_watch_full_eval_deferred_count", None)
    target.pop("_scanner_watch_full_eval_deferred_anchor_epoch", None)
    target.pop("_scanner_watch_full_eval_deferred_first_observed_epoch", None)
    target.pop("_scanner_watch_full_eval_deferred_last_observed_epoch", None)
    cache_key = _scanner_watch_full_eval_deferred_state_key(target)
    if cache_key:
        _SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE.pop(cache_key, None)


def _scanner_watch_full_eval_deferred_state_key(target):
    if not isinstance(target, dict):
        return ""
    record_id = str(target.get("id") or "").strip()
    code = str(target.get("code") or "").strip()[:6]
    if record_id and code:
        return f"{record_id}:{code}"
    if record_id:
        return f"id:{record_id}"
    if code:
        return f"code:{code}"
    return ""


def _scanner_watch_preserve_full_eval_deferred_anchor(target, cache_key, anchor_epoch):
    if not isinstance(target, dict) or anchor_epoch <= 0:
        return
    target.pop("_scanner_watch_full_eval_deferred_count", None)
    target.pop("_scanner_watch_full_eval_deferred_first_observed_epoch", None)
    target.pop("_scanner_watch_full_eval_deferred_last_observed_epoch", None)
    target["_scanner_watch_full_eval_deferred_anchor_epoch"] = anchor_epoch
    if cache_key:
        _SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE[cache_key] = {
            "anchor_epoch": anchor_epoch
        }


def _prune_scanner_watch_full_eval_deferred_state(active_targets):
    if not _SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE:
        return
    active_keys = {
        _scanner_watch_full_eval_deferred_state_key(target)
        for target in active_targets or []
        if _is_scanner_watch_eviction_candidate(target)
    }
    active_keys.discard("")
    for key in list(_SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE.keys()):
        if key not in active_keys:
            _SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE.pop(key, None)


def _scanner_watch_eviction_decision_from_terminal(target, *, now_ts):
    if not _is_scanner_watch_eviction_candidate(target):
        return {"should_evict": False, "eviction_attempt_count": 0}
    block = target.get("_scanner_watch_last_terminal_block")
    if not isinstance(block, dict):
        return {"should_evict": False, "eviction_attempt_count": 0}
    stage = str(block.get("stage") or "")
    if stage not in sniper_state_handlers.SCANNER_WATCH_EVICTION_TERMINAL_STAGES:
        return {"should_evict": False, "eviction_attempt_count": 0}
    reason = str(block.get("reason") or stage)
    fresh_input_confirmed = bool(block.get("fresh_input_confirmed"))
    if not fresh_input_confirmed:
        _scanner_watch_reset_terminal_eviction_state(target)
        return {"should_evict": False, "eviction_attempt_count": 0}
    had_stale_source_quality_state = (
        _safe_float(target.get("_scanner_watch_eviction_stale_first_seen_epoch"), 0.0)
        > 0
        or _safe_int(target.get("_scanner_watch_eviction_stale_count"), 0) > 0
    )
    _scanner_watch_reset_stale_eviction_state(target)
    block_epoch = _safe_float(block.get("observed_epoch"), 0.0)
    last_block_epoch = _safe_float(
        target.get("_scanner_watch_eviction_last_terminal_observed_epoch"), 0.0
    )
    if block_epoch > 0 and block_epoch == last_block_epoch:
        return {
            "should_evict": False,
            "eviction_attempt_count": _safe_int(
                target.get("_scanner_watch_eviction_terminal_count"), 0
            ),
        }
    prev_stage = str(target.get("_scanner_watch_eviction_terminal_stage") or "")
    prev_reason = str(target.get("_scanner_watch_eviction_terminal_reason") or "")
    attempt_count = _safe_int(target.get("_scanner_watch_eviction_terminal_count"), 0)
    if prev_stage == stage and prev_reason == reason:
        attempt_count += 1
    else:
        attempt_count = 1
    target["_scanner_watch_eviction_terminal_stage"] = stage
    target["_scanner_watch_eviction_terminal_reason"] = reason
    target["_scanner_watch_eviction_terminal_count"] = attempt_count
    if block_epoch > 0:
        target["_scanner_watch_eviction_last_terminal_observed_epoch"] = block_epoch
    hardgate_prefilter = stage in SCANNER_WATCH_EVICTION_PREFILTER_HARDGATE_STAGES
    if had_stale_source_quality_state and hardgate_prefilter and attempt_count == 1:
        return {
            "should_evict": False,
            "eviction_reason": "fresh_terminal_after_source_quality_reset",
            "eviction_attempt_count": attempt_count,
            "terminal_stage": stage,
            "terminal_reason": reason,
            "fresh_input_confirmed": True,
            "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
            "stale_age_sec": "not_applicable_stale_age_sec",
            "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
            "observed_epoch": f"{float(now_ts):.3f}",
        }
    rising_terminal_recheck_allowed = (
        hardgate_prefilter
        and _scanner_rising_terminal_hardgate_recheck_enabled()
        and _scanner_is_rising_entry_relief_candidate(target)
        and not _scanner_scalping_buy_window_closed(now_ts)
        and attempt_count <= _scanner_rising_terminal_hardgate_recheck_max_attempts()
    )
    if rising_terminal_recheck_allowed:
        delay_sec = _scanner_rising_terminal_hardgate_recheck_delay_sec()
        _scanner_set_rising_recheck(
            target,
            kind="terminal_hardgate",
            after_epoch=float(now_ts) + delay_sec,
            reason="terminal_hardgate_recheck_pending",
        )
        return {
            "should_evict": False,
            "eviction_reason": "terminal_hardgate_recheck_pending",
            "eviction_attempt_count": attempt_count,
            "terminal_stage": stage,
            "terminal_reason": reason,
            "fresh_input_confirmed": True,
            "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
            "stale_age_sec": "not_applicable_stale_age_sec",
            "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
            "rising_entry_relief_eligible": True,
            "rising_entry_relief_reason": "terminal_hardgate_recheck_pending",
            "scanner_positive_delta_pct": round(
                _scanner_positive_delta_value(target), 4
            ),
            "scanner_full_eval_budget_source": "not_applicable_terminal_hardgate",
            "terminal_hardgate_recheck_delay_sec": delay_sec,
            "terminal_hardgate_recheck_max_attempts": _scanner_rising_terminal_hardgate_recheck_max_attempts(),
            "observed_epoch": f"{float(now_ts):.3f}",
        }
    return {
        "should_evict": hardgate_prefilter
        or attempt_count >= SCANNER_WATCH_EVICTION_TERMINAL_MIN_COUNT,
        "eviction_reason": (
            "scanner_hardgate_prefilter"
            if hardgate_prefilter
            else "terminal_blocker_repeated"
        ),
        "eviction_attempt_count": attempt_count,
        "terminal_stage": stage,
        "terminal_reason": reason,
        "fresh_input_confirmed": True,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "observed_epoch": f"{float(now_ts):.3f}",
    }


def _scanner_watch_eviction_decision_from_stale(
    target, *, now_ts, stale_reason, recovery_fields=None
):
    if not _is_scanner_watch_eviction_candidate(target):
        return {"should_evict": False, "eviction_attempt_count": 0}
    reason = str(stale_reason or "")
    if reason not in SCANNER_WATCH_EVICTION_STALE_REASONS:
        return {"should_evict": False, "eviction_attempt_count": 0}
    recovery_fields = recovery_fields if isinstance(recovery_fields, dict) else {}
    is_source_quality_unresolved = (
        reason in SCANNER_WATCH_EVICTION_SOURCE_QUALITY_REASONS
    )
    rest_quote_price_only_strength_missing = (
        reason == "rising_rest_quote_recovery_without_realtime_strength"
    )
    recovery_outcome = str(
        recovery_fields.get("ws_recovery_outcome")
        or (
            "source_quality_unresolved_no_ws_recovery"
            if is_source_quality_unresolved
            else "not_applicable_ws_recovery_outcome"
        )
    )
    if rest_quote_price_only_strength_missing:
        recovery_outcome = "source_quality_unresolved_price_only_rest_quote"
    subscription_repair_needed = bool(
        recovery_fields.get("ws_subscription_repair_needed")
    )
    subscription_recheck_status = str(
        recovery_fields.get("ws_subscription_recheck_status") or ""
    )
    watch_age_sec = max(
        0.0, float(now_ts) - _runtime_added_time_for_target(target, now_ts=now_ts)
    )
    rest_quote_still_ws_stale = (
        recovery_outcome == "rest_quote_applied"
        and (
            subscription_repair_needed
            or subscription_recheck_status
            in {"subscribed_snapshot_stale_or_missing", "missing_or_not_subscribed"}
        )
        and watch_age_sec >= _scanner_rest_quote_stale_eviction_max_watch_age_sec()
    )
    if recovery_outcome == "rest_quote_applied" and not rest_quote_still_ws_stale:
        _scanner_watch_reset_stale_eviction_state(target)
        return {"should_evict": False, "eviction_attempt_count": 0}
    if rest_quote_still_ws_stale:
        recovery_outcome = "rest_quote_applied_ws_still_stale"
    first_seen = _safe_float(
        target.get("_scanner_watch_eviction_stale_first_seen_epoch"), 0.0
    )
    if first_seen <= 0:
        first_seen = (
            _runtime_added_time_for_target(target, now_ts=now_ts)
            if rest_quote_still_ws_stale
            else float(now_ts)
        )
    attempt_count = _safe_int(target.get("_scanner_watch_eviction_stale_count"), 0) + 1
    stale_age_sec = max(0.0, float(now_ts) - first_seen)
    after_buy_window_source_quality_expired = (
        is_source_quality_unresolved
        and _scanner_after_buy_window_source_quality_eviction_enabled()
        and _scanner_scalping_buy_window_closed(now_ts)
        and attempt_count
        >= _scanner_after_buy_window_source_quality_eviction_min_count()
        and stale_age_sec
        >= _scanner_after_buy_window_source_quality_eviction_min_age_sec()
    )
    if is_source_quality_unresolved:
        target["_scanner_watch_eviction_stale_first_seen_epoch"] = first_seen
        target["_scanner_watch_eviction_stale_count"] = attempt_count
    if after_buy_window_source_quality_expired:
        eviction_reason = "source_quality_unresolved_after_buy_window"
    elif is_source_quality_unresolved:
        eviction_reason = "source_quality_unresolved"
    else:
        eviction_reason = "stale_recovery_failed"
    if (
        not after_buy_window_source_quality_expired
        and _scanner_rising_ws_gap_priority_recovery_enabled()
        and _scanner_is_rising_entry_relief_candidate(target)
        and not rest_quote_price_only_strength_missing
        and (
            is_source_quality_unresolved
            or not (
                attempt_count >= SCANNER_WATCH_EVICTION_STALE_MIN_COUNT
                and stale_age_sec >= SCANNER_WATCH_EVICTION_STALE_MIN_AGE_SEC
            )
        )
    ):
        _scanner_set_rising_recheck(
            target,
            kind="ws_gap_priority",
            after_epoch=float(now_ts) + 5.0,
            reason="ws_gap_recovery_deferred_priority",
        )
        return {
            "should_evict": False,
            "eviction_reason": "ws_gap_recovery_deferred_priority",
            "eviction_attempt_count": _safe_int(
                target.get("_scanner_watch_eviction_stale_count"), 0
            ),
            "terminal_stage": "not_applicable_terminal_stage",
            "terminal_reason": reason,
            "fresh_input_confirmed": False,
            "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
            "stale_age_sec": "not_applicable_stale_age_sec",
            "ws_recovery_outcome": recovery_outcome,
            "ws_gap_recovery_deferred_priority": True,
            "ws_subscription_repair_required": bool(
                recovery_fields.get("ws_subscription_repair_required")
            ),
            "rising_entry_relief_eligible": True,
            "rising_entry_relief_reason": "ws_gap_recovery_deferred_priority",
            "scanner_positive_delta_pct": round(
                _scanner_positive_delta_value(target), 4
            ),
            "scanner_full_eval_budget_source": "not_applicable_ws_gap",
            "observed_epoch": f"{float(now_ts):.3f}",
        }
    target["_scanner_watch_eviction_stale_first_seen_epoch"] = first_seen
    target["_scanner_watch_eviction_stale_count"] = attempt_count
    return {
        "should_evict": (
            after_buy_window_source_quality_expired
            or (
                attempt_count >= SCANNER_WATCH_EVICTION_STALE_MIN_COUNT
                and stale_age_sec >= SCANNER_WATCH_EVICTION_STALE_MIN_AGE_SEC
                and recovery_outcome != "rest_quote_applied"
            )
        ),
        "eviction_reason": (eviction_reason),
        "eviction_attempt_count": attempt_count,
        "terminal_stage": "not_applicable_terminal_stage",
        "terminal_reason": reason,
        "fresh_input_confirmed": False,
        "stale_first_seen_epoch": f"{first_seen:.3f}",
        "stale_age_sec": round(stale_age_sec, 3),
        "ws_recovery_outcome": recovery_outcome,
        "after_buy_window_source_quality_expired": after_buy_window_source_quality_expired,
        "source_quality_detail_route": recovery_fields.get(
            "source_quality_detail_route"
        )
        or (
            "price_only_rest_quote_strength_history_missing"
            if rest_quote_price_only_strength_missing
            else "not_applicable_source_quality_detail_route"
        ),
        "rest_quote_price_recovery_only": bool(
            rest_quote_price_only_strength_missing
            or recovery_fields.get("rest_quote_price_recovery_only")
        ),
        "scanner_source_quality_reallocation_candidate": bool(
            rest_quote_price_only_strength_missing
            or recovery_fields.get("scanner_source_quality_reallocation_candidate")
        ),
        "observed_epoch": f"{float(now_ts):.3f}",
    }


def _scanner_watch_eviction_decision_from_no_trade(target, ws_data, *, now_ts):
    if not _scanner_no_trade_eviction_enabled():
        return {"should_evict": False, "eviction_attempt_count": 0}
    if not _is_scanner_watch_eviction_candidate(target):
        return {"should_evict": False, "eviction_attempt_count": 0}

    received = (ws_data or {}).get("received_types") or []
    try:
        received_types = sorted(str(item) for item in received if str(item).strip())
    except Exception:
        received_types = []
    if not received_types:
        target.pop("_scanner_watch_no_trade_count", None)
        target.pop("_scanner_watch_no_trade_first_observed_epoch", None)
        target.pop("_scanner_watch_no_trade_last_observed_epoch", None)
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_no_trade_waiting_realtime_type",
            "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        }
    if "0B" in received_types:
        target.pop("_scanner_watch_no_trade_count", None)
        target.pop("_scanner_watch_no_trade_first_observed_epoch", None)
        target.pop("_scanner_watch_no_trade_last_observed_epoch", None)
        return {"should_evict": False, "eviction_attempt_count": 0}

    watch_age_sec = max(
        0.0, float(now_ts) - _runtime_added_time_for_target(target, now_ts=now_ts)
    )
    grace_sec = _scanner_no_trade_eviction_grace_sec()
    if watch_age_sec < grace_sec:
        target.pop("_scanner_watch_no_trade_count", None)
        target.pop("_scanner_watch_no_trade_first_observed_epoch", None)
        target.pop("_scanner_watch_no_trade_last_observed_epoch", None)
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_no_trade_grace_active",
            "no_trade_watch_age_sec": round(watch_age_sec, 3),
            "no_trade_grace_sec": round(grace_sec, 3),
            "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        }

    last_observed = _safe_float(
        target.get("_scanner_watch_no_trade_last_observed_epoch"), 0.0
    )
    if last_observed > 0 and float(now_ts) - last_observed < 5.0:
        return {
            "should_evict": False,
            "eviction_attempt_count": _safe_int(
                target.get("_scanner_watch_no_trade_count"), 0
            ),
            "eviction_reason": "scanner_no_trade_confirmation_throttled",
            "no_trade_watch_age_sec": round(watch_age_sec, 3),
            "no_trade_grace_sec": round(grace_sec, 3),
            "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        }

    first_observed = _safe_float(
        target.get("_scanner_watch_no_trade_first_observed_epoch"), 0.0
    )
    if first_observed <= 0:
        first_observed = float(now_ts)
    attempt_count = _safe_int(target.get("_scanner_watch_no_trade_count"), 0) + 1
    target["_scanner_watch_no_trade_first_observed_epoch"] = first_observed
    target["_scanner_watch_no_trade_last_observed_epoch"] = float(now_ts)
    target["_scanner_watch_no_trade_count"] = attempt_count

    last_ws_update_ts = _safe_float((ws_data or {}).get("last_ws_update_ts"), 0.0)
    return {
        "should_evict": attempt_count >= _scanner_no_trade_eviction_min_count(),
        "eviction_reason": "scanner_no_trade_hot_slot_rotation",
        "eviction_attempt_count": attempt_count,
        "terminal_stage": "not_applicable_terminal_stage",
        "terminal_reason": "no_0b_after_grace",
        "fresh_input_confirmed": False,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "no_trade_first_observed_epoch": f"{first_observed:.3f}",
        "no_trade_watch_age_sec": round(watch_age_sec, 3),
        "no_trade_grace_sec": round(grace_sec, 3),
        "no_trade_min_count": _scanner_no_trade_eviction_min_count(),
        "no_trade_received_types": ",".join(received_types) if received_types else "-",
        "no_trade_last_ws_age_sec": (
            round(max(0.0, float(now_ts) - last_ws_update_ts), 3)
            if last_ws_update_ts > 0
            else "not_available"
        ),
        "observed_epoch": f"{float(now_ts):.3f}",
    }


def _scanner_watch_eviction_decision_from_queue_lag(
    target, *, now_ts, queue_lag_fields=None
):
    if not _scanner_queue_lag_eviction_enabled():
        return {"should_evict": False, "eviction_attempt_count": 0}
    if not _is_scanner_watch_eviction_candidate(target):
        return {"should_evict": False, "eviction_attempt_count": 0}

    queue_lag_fields = queue_lag_fields if isinstance(queue_lag_fields, dict) else {}
    fast_precheck_result = str(
        queue_lag_fields.get("fast_precheck_result")
        or (target or {}).get("_scanner_fast_precheck_result")
        or ""
    )
    fast_precheck_reason = str(
        queue_lag_fields.get("fast_precheck_reason")
        or (target or {}).get("_scanner_fast_precheck_reason")
        or ""
    )
    if fast_precheck_result == "eligible_for_heavy_entry_eval":
        _scanner_watch_reset_queue_lag_eviction_state(target)
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_queue_lag_heavy_eval_eligible",
            "fresh_input_confirmed": True,
            "fast_precheck_result": fast_precheck_result,
            "fast_precheck_reason": fast_precheck_reason,
        }

    queue_lag_sec = _safe_float(queue_lag_fields.get("queue_lag_sec"), 0.0)
    min_sec = _scanner_queue_lag_eviction_min_sec()
    if queue_lag_sec < min_sec:
        _scanner_watch_reset_queue_lag_eviction_state(target)
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_queue_lag_below_threshold",
            "queue_lag_sec": round(queue_lag_sec, 3),
            "queue_lag_min_sec": round(min_sec, 3),
            "fresh_input_confirmed": False,
            "fast_precheck_result": fast_precheck_result or "not_available",
            "fast_precheck_reason": fast_precheck_reason or "not_available",
        }

    fast_precheck_fields = dict(
        (target or {}).get("_scanner_fast_precheck_fields") or {}
    )
    retention_fast_precheck_reason = str(
        fast_precheck_fields.get("fast_precheck_reason") or fast_precheck_reason or ""
    )
    retention_reason = str(
        fast_precheck_fields.get("rising_missed_signed_tape_watch_retention_reason")
        or ""
    )
    if (
        _scanner_boolish_true(
            fast_precheck_fields.get(
                "rising_missed_signed_tape_watch_retention_recommended"
            )
        )
        and retention_fast_precheck_reason
        in {"signed_tape_sell_dominated", "signed_tape_sell_dominated_backoff_active"}
        and retention_reason == "bounded_repeat_cooldown_recheck_pending"
    ):
        _scanner_watch_reset_queue_lag_eviction_state(target)
        target["_scanner_queue_lag_retained_at"] = float(now_ts)
        target["_scanner_queue_lag_retained_reason"] = retention_reason
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_queue_lag_signed_tape_retention_pending",
            "queue_lag_sec": round(queue_lag_sec, 3),
            "queue_lag_min_sec": round(min_sec, 3),
            "fresh_input_confirmed": False,
            "fast_precheck_result": fast_precheck_result or "not_available",
            "fast_precheck_reason": fast_precheck_reason or "not_available",
            "fast_precheck_fields": fast_precheck_fields,
            "signed_tape_watch_retention_reason": retention_reason,
        }

    last_observed = _safe_float(
        target.get("_scanner_watch_queue_lag_last_observed_epoch"), 0.0
    )
    if last_observed > 0 and float(now_ts) - last_observed < 5.0:
        return {
            "should_evict": False,
            "eviction_attempt_count": _safe_int(
                target.get("_scanner_watch_queue_lag_count"), 0
            ),
            "eviction_reason": "scanner_queue_lag_confirmation_throttled",
            "queue_lag_sec": round(queue_lag_sec, 3),
            "queue_lag_min_sec": round(min_sec, 3),
            "fresh_input_confirmed": False,
            "fast_precheck_result": fast_precheck_result or "not_available",
            "fast_precheck_reason": fast_precheck_reason or "not_available",
        }

    first_observed = _safe_float(
        target.get("_scanner_watch_queue_lag_first_observed_epoch"), 0.0
    )
    if first_observed <= 0:
        first_observed = float(now_ts)
    attempt_count = _safe_int(target.get("_scanner_watch_queue_lag_count"), 0) + 1
    target["_scanner_watch_queue_lag_first_observed_epoch"] = first_observed
    target["_scanner_watch_queue_lag_last_observed_epoch"] = float(now_ts)
    target["_scanner_watch_queue_lag_count"] = attempt_count

    immediate_sec = _scanner_queue_lag_eviction_immediate_sec()
    min_count = _scanner_queue_lag_eviction_min_count()
    immediate = queue_lag_sec >= immediate_sec
    return {
        "should_evict": immediate or attempt_count >= min_count,
        "eviction_reason": "scanner_queue_lag_budget_reallocated",
        "eviction_attempt_count": attempt_count,
        "terminal_stage": "scalping_scanner_runtime_queue_lag",
        "terminal_reason": "runtime_queue_lag_repeated_or_immediate",
        "fresh_input_confirmed": False,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "source_quality_detail_route": "scanner_queue_lag_budget_reallocation",
        "queue_lag_first_observed_epoch": f"{first_observed:.3f}",
        "queue_lag_sec": round(queue_lag_sec, 3),
        "queue_lag_min_sec": round(min_sec, 3),
        "queue_lag_immediate_sec": round(immediate_sec, 3),
        "queue_lag_min_count": min_count,
        "queue_lag_immediate": immediate,
        "queue_rank": queue_lag_fields.get("queue_rank", "not_available"),
        "scanner_queue_rank": queue_lag_fields.get(
            "scanner_queue_rank", "not_available"
        ),
        "watching_count": queue_lag_fields.get("watching_count", "not_available"),
        "scanner_watching_count": queue_lag_fields.get(
            "scanner_watching_count", "not_available"
        ),
        "queue_lag_anchor_field": queue_lag_fields.get("queue_lag_anchor_field")
        or "entry_armed_at_epoch_or_added_time",
        "fast_precheck_result": fast_precheck_result or "not_available",
        "fast_precheck_reason": fast_precheck_reason or "not_available",
        "fast_precheck_fields": dict(
            (target or {}).get("_scanner_fast_precheck_fields") or {}
        ),
        "observed_epoch": f"{float(now_ts):.3f}",
    }


def _scanner_watch_eviction_decision_from_full_eval_deferred(
    target, *, now_ts, skip_fields=None
):
    if not _scanner_full_eval_deferred_eviction_enabled():
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_full_eval_deferred_disabled",
        }
    if not _is_scanner_watch_eviction_candidate(target):
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_full_eval_deferred_not_candidate",
        }

    skip_fields = skip_fields if isinstance(skip_fields, dict) else {}
    skip_reason = str(skip_fields.get("skip_reason") or "")
    if skip_reason != "scanner_full_eval_loop_budget_deferred":
        _scanner_watch_reset_full_eval_deferred_eviction_state(target)
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_full_eval_deferred_not_applicable",
        }

    now_value = float(now_ts)
    cache_key = _scanner_watch_full_eval_deferred_state_key(target)
    cached_state = (
        _SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE.get(cache_key, {}) if cache_key else {}
    )
    if not isinstance(cached_state, dict):
        cached_state = {}
    target_anchor_epoch = _safe_float(target.get("entry_armed_at_epoch"), 0.0)
    anchor_field = "entry_armed_at_epoch"
    if target_anchor_epoch <= 0:
        target_anchor_epoch = _safe_float(target.get("added_time"), 0.0)
        anchor_field = "added_time"
    cached_anchor_epoch = _safe_float(
        target.get("_scanner_watch_full_eval_deferred_anchor_epoch")
        or cached_state.get("anchor_epoch"),
        0.0,
    )
    if cached_anchor_epoch > 0 and target_anchor_epoch > 0:
        if cached_anchor_epoch < target_anchor_epoch:
            anchor_epoch = cached_anchor_epoch
            anchor_field = "full_eval_deferred_cached_anchor_epoch"
        else:
            anchor_epoch = target_anchor_epoch
    elif cached_anchor_epoch > 0:
        anchor_epoch = cached_anchor_epoch
        anchor_field = "full_eval_deferred_cached_anchor_epoch"
    else:
        anchor_epoch = target_anchor_epoch
    if anchor_epoch <= 0:
        anchor_epoch = _safe_float(
            target.get("_scanner_watch_full_eval_deferred_first_observed_epoch")
            or cached_state.get("first_observed_epoch"),
            0.0,
        )
        anchor_field = "full_eval_deferred_first_observed_epoch"
    if anchor_epoch <= 0:
        anchor_epoch = now_value
        anchor_field = "full_eval_deferred_first_observed_epoch"

    watch_age_sec = max(0.0, now_value - anchor_epoch) if anchor_epoch > 0 else 0.0
    min_age_sec = _scanner_full_eval_deferred_eviction_min_age_sec()
    min_count = _scanner_full_eval_deferred_eviction_min_count()
    if watch_age_sec < min_age_sec:
        _scanner_watch_preserve_full_eval_deferred_anchor(
            target, cache_key, anchor_epoch
        )
        return {
            "should_evict": False,
            "eviction_attempt_count": 0,
            "eviction_reason": "scanner_full_eval_deferred_new_promotion_grace",
            "fresh_input_confirmed": True,
            "full_eval_deferred_watch_age_sec": round(watch_age_sec, 3),
            "full_eval_deferred_min_age_sec": round(min_age_sec, 3),
            "full_eval_deferred_anchor_field": anchor_field,
            "full_eval_deferred_state_source": "module_cache_and_target_dict",
            "terminal_stage": "scalping_scanner_watching_runtime_skip",
            "terminal_reason": skip_reason,
        }

    last_observed = _safe_float(
        target.get("_scanner_watch_full_eval_deferred_last_observed_epoch")
        or cached_state.get("last_observed_epoch"),
        0.0,
    )
    if last_observed > 0 and now_value - last_observed < 5.0:
        return {
            "should_evict": False,
            "eviction_attempt_count": _safe_int(
                target.get("_scanner_watch_full_eval_deferred_count")
                or cached_state.get("count"),
                0,
            ),
            "eviction_reason": "scanner_full_eval_deferred_confirmation_throttled",
            "fresh_input_confirmed": True,
            "full_eval_deferred_watch_age_sec": round(watch_age_sec, 3),
            "full_eval_deferred_min_age_sec": round(min_age_sec, 3),
            "full_eval_deferred_anchor_field": anchor_field,
            "full_eval_deferred_state_source": "module_cache_and_target_dict",
            "terminal_stage": "scalping_scanner_watching_runtime_skip",
            "terminal_reason": skip_reason,
        }

    first_observed = _safe_float(
        target.get("_scanner_watch_full_eval_deferred_first_observed_epoch")
        or cached_state.get("first_observed_epoch"),
        0.0,
    )
    if first_observed <= 0:
        first_observed = now_value
    attempt_count = (
        _safe_int(
            target.get("_scanner_watch_full_eval_deferred_count")
            or cached_state.get("count"),
            0,
        )
        + 1
    )
    target["_scanner_watch_full_eval_deferred_first_observed_epoch"] = first_observed
    target["_scanner_watch_full_eval_deferred_last_observed_epoch"] = now_value
    target["_scanner_watch_full_eval_deferred_count"] = attempt_count
    target["_scanner_watch_full_eval_deferred_anchor_epoch"] = anchor_epoch
    if cache_key:
        _SCANNER_WATCH_FULL_EVAL_DEFERRED_STATE[cache_key] = {
            "anchor_epoch": anchor_epoch,
            "first_observed_epoch": first_observed,
            "last_observed_epoch": now_value,
            "count": attempt_count,
        }

    fast_precheck_fields = dict(
        (target or {}).get("_scanner_fast_precheck_fields") or {}
    )
    return {
        "should_evict": attempt_count >= min_count,
        "eviction_reason": "scanner_full_eval_budget_deferred_repeated",
        "eviction_attempt_count": attempt_count,
        "terminal_stage": "scalping_scanner_watching_runtime_skip",
        "terminal_reason": skip_reason,
        "fresh_input_confirmed": True,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "source_quality_detail_route": "scanner_full_eval_budget_rotation",
        "full_eval_deferred_first_observed_epoch": f"{first_observed:.3f}",
        "full_eval_deferred_watch_age_sec": round(watch_age_sec, 3),
        "full_eval_deferred_min_age_sec": round(min_age_sec, 3),
        "full_eval_deferred_min_count": min_count,
        "full_eval_deferred_anchor_field": anchor_field,
        "full_eval_deferred_state_source": "module_cache_and_target_dict",
        "queue_rank": skip_fields.get("queue_rank", "not_available"),
        "scanner_queue_rank": skip_fields.get("scanner_queue_rank", "not_available"),
        "watching_count": skip_fields.get("watching_count", "not_available"),
        "scanner_watching_count": skip_fields.get(
            "scanner_watching_count", "not_available"
        ),
        "scanner_full_eval_base_limit": skip_fields.get(
            "scanner_full_eval_base_limit", "not_available"
        ),
        "scanner_full_eval_limit": skip_fields.get(
            "scanner_full_eval_limit", "not_available"
        ),
        "scanner_full_eval_count": skip_fields.get(
            "scanner_full_eval_count", "not_available"
        ),
        "scanner_rising_full_eval_extra_limit": skip_fields.get(
            "scanner_rising_full_eval_extra_limit",
            "not_available",
        ),
        "scanner_rising_full_eval_relief_count": skip_fields.get(
            "scanner_rising_full_eval_relief_count",
            "not_available",
        ),
        "fast_precheck_result": str(
            skip_fields.get("fast_precheck_result")
            or (target or {}).get("_scanner_fast_precheck_result")
            or fast_precheck_fields.get("fast_precheck_result")
            or "eligible_for_heavy_entry_eval"
        ),
        "fast_precheck_reason": str(
            skip_fields.get("fast_precheck_reason")
            or (target or {}).get("_scanner_fast_precheck_reason")
            or fast_precheck_fields.get("fast_precheck_reason")
            or "fast_precheck_pass"
        ),
        "fast_precheck_fields": fast_precheck_fields,
        "observed_epoch": f"{now_value:.3f}",
    }


def _scanner_watch_eviction_decision_from_pool_block(target, *, now_ts):
    if not _is_scanner_watch_eviction_candidate(target):
        return {"should_evict": False, "eviction_attempt_count": 0}
    block = target.get("_scanner_watch_last_pool_block")
    if not isinstance(block, dict):
        return {"should_evict": False, "eviction_attempt_count": 0}
    reason = str(block.get("reason") or "")
    if reason != "entry_cooldown_active":
        return {"should_evict": False, "eviction_attempt_count": 0}
    cooldown_remaining_sec = _safe_int(block.get("cooldown_remaining_sec"), 0)
    if cooldown_remaining_sec < SCANNER_WATCH_EVICTION_COOLDOWN_MIN_REMAINING_SEC:
        _scanner_watch_reset_pool_block_eviction_state(target)
        return {"should_evict": False, "eviction_attempt_count": 0}
    if (
        _scanner_rising_cooldown_eviction_relief_enabled()
        and _scanner_is_rising_entry_relief_candidate(target)
    ):
        _scanner_set_rising_recheck(
            target,
            kind="cooldown",
            after_epoch=float(now_ts) + float(cooldown_remaining_sec),
            reason="cooldown_recheck_pending",
        )
        _scanner_watch_reset_pool_block_eviction_state(target)
        return {
            "should_evict": False,
            "eviction_reason": "cooldown_recheck_pending",
            "eviction_attempt_count": 0,
            "terminal_stage": "not_applicable_terminal_stage",
            "terminal_reason": reason,
            "fresh_input_confirmed": False,
            "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
            "stale_age_sec": "not_applicable_stale_age_sec",
            "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
            "cooldown_remaining_sec": cooldown_remaining_sec,
            "rising_entry_relief_eligible": True,
            "rising_entry_relief_reason": "cooldown_recheck_pending",
            "scanner_positive_delta_pct": round(
                _scanner_positive_delta_value(target), 4
            ),
            "scanner_full_eval_budget_source": "not_applicable_cooldown",
            "observed_epoch": f"{float(now_ts):.3f}",
        }
    block_epoch = _safe_float(block.get("observed_epoch"), 0.0)
    last_block_epoch = _safe_float(
        target.get("_scanner_watch_eviction_last_pool_block_observed_epoch"), 0.0
    )
    if block_epoch > 0 and block_epoch == last_block_epoch:
        return {
            "should_evict": False,
            "eviction_attempt_count": _safe_int(
                target.get("_scanner_watch_eviction_pool_block_count"), 0
            ),
        }
    prev_reason = str(target.get("_scanner_watch_eviction_pool_block_reason") or "")
    attempt_count = _safe_int(target.get("_scanner_watch_eviction_pool_block_count"), 0)
    attempt_count = attempt_count + 1 if prev_reason == reason else 1
    target["_scanner_watch_eviction_pool_block_reason"] = reason
    target["_scanner_watch_eviction_pool_block_count"] = attempt_count
    if block_epoch > 0:
        target["_scanner_watch_eviction_last_pool_block_observed_epoch"] = block_epoch
    return {
        "should_evict": attempt_count >= SCANNER_WATCH_EVICTION_COOLDOWN_MIN_COUNT,
        "eviction_reason": "safety_cooldown_pool_blocked",
        "eviction_attempt_count": attempt_count,
        "terminal_stage": "not_applicable_terminal_stage",
        "terminal_reason": reason,
        "fresh_input_confirmed": False,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "cooldown_remaining_sec": cooldown_remaining_sec,
        "observed_epoch": f"{float(now_ts):.3f}",
    }


def _scanner_watch_eviction_event_fields(target, *, decision):
    target = target or {}
    fast_precheck_fields = decision.get("fast_precheck_fields")
    fast_precheck_fields = (
        fast_precheck_fields if isinstance(fast_precheck_fields, dict) else {}
    )
    return {
        "metric_role": "runtime_watchlist_pool_management",
        "decision_authority": "real_scalping_scanner_watch_eviction_pool_management_only",
        "window_policy": "intraday_runtime_watchlist",
        "sample_floor": "not_applicable_runtime_pool_management",
        "primary_decision_metric": "eviction_reason",
        "source_quality_gate": "scalping_scanner_watch_eviction_contract",
        "source_quality_route": "runtime_watchlist_eviction_pool_management_only",
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
        ),
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "eviction_reason": decision.get("eviction_reason")
        or "not_applicable_eviction_reason",
        "eviction_policy_version": SCANNER_WATCH_EVICTION_POLICY_VERSION,
        "eviction_attempt_count": decision.get("eviction_attempt_count", 0),
        "terminal_stage": decision.get("terminal_stage")
        or "not_applicable_terminal_stage",
        "terminal_reason": decision.get("terminal_reason")
        or "not_applicable_terminal_reason",
        "fresh_input_confirmed": bool(decision.get("fresh_input_confirmed")),
        "stale_first_seen_epoch": decision.get("stale_first_seen_epoch")
        or "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": decision.get("stale_age_sec")
        or "not_applicable_stale_age_sec",
        "ws_recovery_outcome": decision.get("ws_recovery_outcome")
        or "not_applicable_ws_recovery_outcome",
        "ws_backoff_retention_active": bool(
            decision.get("ws_backoff_retention_active")
        ),
        "ws_backoff_retention_reason": decision.get("ws_backoff_retention_reason")
        or "not_applicable_ws_backoff_retention_reason",
        "ws_backoff_retention_first_epoch": decision.get(
            "ws_backoff_retention_first_epoch"
        )
        or "not_applicable_ws_backoff_retention_first_epoch",
        "ws_backoff_retention_age_sec": decision.get("ws_backoff_retention_age_sec")
        or "not_applicable_ws_backoff_retention_age_sec",
        "ws_backoff_retention_min_sec": decision.get("ws_backoff_retention_min_sec")
        or "not_applicable_ws_backoff_retention_min_sec",
        "ws_backoff_retention_max_sec": decision.get("ws_backoff_retention_max_sec")
        or "not_applicable_ws_backoff_retention_max_sec",
        "ws_backoff_retention_attempt_count": decision.get(
            "ws_backoff_retention_attempt_count"
        )
        or "not_applicable_ws_backoff_retention_attempt_count",
        "ws_backoff_retention_min_count": decision.get("ws_backoff_retention_min_count")
        or "not_applicable_ws_backoff_retention_min_count",
        "ws_backoff_until": decision.get("ws_backoff_until")
        or "not_applicable_ws_backoff_until",
        "source_quality_detail_route": decision.get("source_quality_detail_route")
        or "not_applicable_source_quality_detail_route",
        "rest_quote_price_recovery_only": bool(
            decision.get("rest_quote_price_recovery_only")
        ),
        "scanner_source_quality_reallocation_candidate": bool(
            decision.get("scanner_source_quality_reallocation_candidate")
        ),
        "no_trade_first_observed_epoch": decision.get("no_trade_first_observed_epoch")
        or "not_applicable_no_trade_first_observed_epoch",
        "no_trade_watch_age_sec": decision.get("no_trade_watch_age_sec")
        or "not_applicable_no_trade_watch_age_sec",
        "no_trade_grace_sec": decision.get("no_trade_grace_sec")
        or "not_applicable_no_trade_grace_sec",
        "no_trade_min_count": decision.get("no_trade_min_count")
        or "not_applicable_no_trade_min_count",
        "no_trade_received_types": decision.get("no_trade_received_types")
        or "not_applicable_no_trade_received_types",
        "no_trade_last_ws_age_sec": decision.get("no_trade_last_ws_age_sec")
        or "not_applicable_no_trade_last_ws_age_sec",
        "queue_lag_first_observed_epoch": decision.get("queue_lag_first_observed_epoch")
        or "not_applicable_queue_lag_first_observed_epoch",
        "queue_lag_sec": decision.get("queue_lag_sec")
        or "not_applicable_queue_lag_sec",
        "queue_lag_min_sec": decision.get("queue_lag_min_sec")
        or "not_applicable_queue_lag_min_sec",
        "queue_lag_immediate_sec": decision.get("queue_lag_immediate_sec")
        or "not_applicable_queue_lag_immediate_sec",
        "queue_lag_min_count": decision.get("queue_lag_min_count")
        or "not_applicable_queue_lag_min_count",
        "queue_lag_immediate": bool(decision.get("queue_lag_immediate")),
        "queue_rank": decision.get("queue_rank", "not_applicable_queue_rank"),
        "scanner_queue_rank": decision.get(
            "scanner_queue_rank", "not_applicable_scanner_queue_rank"
        ),
        "watching_count": decision.get(
            "watching_count", "not_applicable_watching_count"
        ),
        "scanner_watching_count": decision.get(
            "scanner_watching_count",
            "not_applicable_scanner_watching_count",
        ),
        "queue_lag_anchor_field": decision.get("queue_lag_anchor_field")
        or "not_applicable_queue_lag_anchor_field",
        "full_eval_deferred_first_observed_epoch": decision.get(
            "full_eval_deferred_first_observed_epoch"
        )
        or "not_applicable_full_eval_deferred_first_observed_epoch",
        "full_eval_deferred_watch_age_sec": decision.get(
            "full_eval_deferred_watch_age_sec"
        )
        or "not_applicable_full_eval_deferred_watch_age_sec",
        "full_eval_deferred_min_age_sec": decision.get("full_eval_deferred_min_age_sec")
        or "not_applicable_full_eval_deferred_min_age_sec",
        "full_eval_deferred_min_count": decision.get("full_eval_deferred_min_count")
        or "not_applicable_full_eval_deferred_min_count",
        "full_eval_deferred_anchor_field": decision.get(
            "full_eval_deferred_anchor_field"
        )
        or "not_applicable_full_eval_deferred_anchor_field",
        "full_eval_deferred_state_source": decision.get(
            "full_eval_deferred_state_source"
        )
        or "not_applicable_full_eval_deferred_state_source",
        "scanner_full_eval_base_limit": decision.get("scanner_full_eval_base_limit")
        or "not_applicable_scanner_full_eval_base_limit",
        "scanner_full_eval_limit": decision.get("scanner_full_eval_limit")
        or "not_applicable_scanner_full_eval_limit",
        "scanner_full_eval_count": decision.get("scanner_full_eval_count")
        or "not_applicable_scanner_full_eval_count",
        "scanner_rising_full_eval_extra_limit": decision.get(
            "scanner_rising_full_eval_extra_limit"
        )
        or "not_applicable_scanner_rising_full_eval_extra_limit",
        "scanner_rising_full_eval_relief_count": decision.get(
            "scanner_rising_full_eval_relief_count"
        )
        or "not_applicable_scanner_rising_full_eval_relief_count",
        "cooldown_remaining_sec": decision.get(
            "cooldown_remaining_sec", "not_applicable_cooldown_remaining_sec"
        ),
        "fast_precheck_result": decision.get("fast_precheck_result")
        or fast_precheck_fields.get("fast_precheck_result")
        or "not_applicable_fast_precheck_result",
        "fast_precheck_reason": decision.get("fast_precheck_reason")
        or fast_precheck_fields.get("fast_precheck_reason")
        or "not_applicable_fast_precheck_reason",
        "scanner_rising_missed_fast_reject_reason": fast_precheck_fields.get(
            "scanner_rising_missed_fast_reject_reason",
            "not_applicable_scanner_rising_missed_fast_reject_reason",
        ),
        "scanner_rising_missed_recovery_signal_present": bool(
            fast_precheck_fields.get("scanner_rising_missed_recovery_signal_present")
        ),
        "scanner_rising_missed_low_rebound_pct": fast_precheck_fields.get(
            "scanner_rising_missed_low_rebound_pct",
            "not_applicable_scanner_rising_missed_low_rebound_pct",
        ),
        "scanner_rising_missed_positive_delta_pct": fast_precheck_fields.get(
            "scanner_rising_missed_positive_delta_pct",
            "not_applicable_scanner_rising_missed_positive_delta_pct",
        ),
        "scanner_rising_missed_min_delta_pct": fast_precheck_fields.get(
            "scanner_rising_missed_min_delta_pct",
            "not_applicable_scanner_rising_missed_min_delta_pct",
        ),
        "runtime_record_id": target.get("id") or "not_applicable_runtime_record_id",
        "stock_code": str(target.get("code") or "").strip()[:6]
        or "not_applicable_stock_code",
        "target_status": target.get("status") or "not_applicable_target_status",
        "target_strategy": normalize_strategy(target.get("strategy")),
        "target_position_tag": normalize_position_tag(
            normalize_strategy(target.get("strategy")), target.get("position_tag")
        ),
        "observed_epoch": decision.get("observed_epoch") or f"{time.time():.3f}",
    }


def _expire_scanner_watch_target(
    target, code, targets, *, decision, emit_event_fn=None
):
    if not _is_scanner_watch_eviction_candidate(target):
        return False
    record_id = target.get("id")
    norm_code = str(code or target.get("code") or "").strip()[:6]
    fields = _scanner_watch_eviction_event_fields(target, decision=decision)
    updated = 0
    try:
        with DB.get_session() as session:
            updated = (
                session.query(RecommendationHistory)
                .filter(
                    RecommendationHistory.id == record_id,
                    RecommendationHistory.stock_code == norm_code,
                    RecommendationHistory.status == "WATCHING",
                    RecommendationHistory.strategy == "SCALPING",
                    RecommendationHistory.position_tag == "SCANNER",
                    RecommendationHistory.buy_time.is_(None),
                    RecommendationHistory.buy_qty == 0,
                )
                .update({"status": "EXPIRED"}, synchronize_session=False)
            )
    except Exception as exc:
        log_error(
            f"🚨 [SCANNER_WATCH_EVICTION] DB update failed ({norm_code}, id={record_id}): {exc}"
        )
        return False
    if updated <= 0:
        return False
    for item in targets:
        if (
            item.get("id") == record_id
            and str(item.get("code") or "").strip()[:6] == norm_code
        ):
            item["status"] = "EXPIRED"
    if emit_event_fn:
        emit_event_fn(target, norm_code, "scalping_scanner_watch_eviction", fields)
    else:
        sniper_state_handlers._log_entry_pipeline(
            target, norm_code, "scalping_scanner_watch_eviction", **fields
        )
    return True


def _maybe_expire_scanner_watch_for_terminal(
    target, code, targets, *, now_ts, emit_event_fn=None
):
    decision = _scanner_watch_eviction_decision_from_terminal(target, now_ts=now_ts)
    if not decision.get("should_evict"):
        return False
    return _expire_scanner_watch_target(
        target, code, targets, decision=decision, emit_event_fn=emit_event_fn
    )


def _maybe_expire_scanner_watch_for_stale(
    target,
    code,
    targets,
    *,
    now_ts,
    stale_reason,
    recovery_fields=None,
    emit_event_fn=None,
):
    decision = _scanner_watch_eviction_decision_from_stale(
        target,
        now_ts=now_ts,
        stale_reason=stale_reason,
        recovery_fields=recovery_fields,
    )
    if not decision.get("should_evict"):
        return False
    return _expire_scanner_watch_target(
        target, code, targets, decision=decision, emit_event_fn=emit_event_fn
    )


def _maybe_expire_scanner_watch_for_pool_block(
    target, code, targets, *, now_ts, emit_event_fn=None
):
    decision = _scanner_watch_eviction_decision_from_pool_block(target, now_ts=now_ts)
    if not decision.get("should_evict"):
        return False
    return _expire_scanner_watch_target(
        target, code, targets, decision=decision, emit_event_fn=emit_event_fn
    )


def _scanner_ws_backoff_watch_retention_min_sec() -> float:
    raw = os.getenv("KORSTOCKSCAN_SCANNER_WS_BACKOFF_WATCH_RETENTION_MIN_SEC", "")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 15.0
    except (TypeError, ValueError):
        value = 15.0
    return max(1.0, min(value, 120.0))


def _scanner_ws_backoff_watch_retention_max_sec() -> float:
    raw = os.getenv("KORSTOCKSCAN_SCANNER_WS_BACKOFF_WATCH_RETENTION_MAX_SEC", "")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 30.0
    except (TypeError, ValueError):
        value = 30.0
    return max(
        _scanner_ws_backoff_watch_retention_min_sec(),
        min(value, 300.0),
    )


def _scanner_ws_backoff_watch_retention_min_count() -> int:
    raw = os.getenv("KORSTOCKSCAN_SCANNER_WS_BACKOFF_WATCH_RETENTION_MIN_COUNT", "")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 2
    except (TypeError, ValueError):
        value = 2
    return max(1, min(value, 20))


def _reset_scanner_ws_backoff_watch_retention(target) -> None:
    if not isinstance(target, dict):
        return
    for key in (
        "_scanner_ws_backoff_watch_retention_active",
        "_scanner_ws_backoff_watch_retention_first_epoch",
        "_scanner_ws_backoff_watch_retention_last_epoch",
        "_scanner_ws_backoff_watch_retention_count",
        "_scanner_ws_backoff_watch_retention_until",
    ):
        target.pop(key, None)


def _scanner_queue_lag_eviction_allowed_before_recovery(
    fast_precheck_reason,
) -> bool:
    """Keep bounded WS-backoff recovery ahead of generic queue pressure."""

    return str(fast_precheck_reason or "") != "scanner_ws_stale_backoff_active"


def _scanner_watch_eviction_decision_from_fast_precheck_budget(
    target,
    *,
    now_ts,
):
    fast_precheck_fields = dict(
        (target or {}).get("_scanner_fast_precheck_fields") or {}
    )
    fast_precheck_reason = str(
        fast_precheck_fields.get("fast_precheck_reason")
        or "rising_missed_not_rising_without_recovery_signal"
    )
    retention_reason = str(
        fast_precheck_fields.get("rising_missed_signed_tape_watch_retention_reason")
        or ""
    )
    if (
        fast_precheck_fields.get(
            "rising_missed_signed_tape_watch_retention_recommended"
        )
        is True
        and retention_reason == "bounded_repeat_cooldown_recheck_pending"
    ):
        _reset_scanner_ws_backoff_watch_retention(target)
        target["_scanner_fast_precheck_budget_retained_at"] = float(now_ts)
        target["_scanner_fast_precheck_budget_retained_reason"] = retention_reason
        return {
            "should_evict": False,
            "retention_active": True,
            "retention_reason": retention_reason,
            "fast_precheck_result": fast_precheck_fields.get("fast_precheck_result")
            or "budget_reallocated",
            "fast_precheck_reason": fast_precheck_reason,
            "fast_precheck_fields": fast_precheck_fields,
        }

    if fast_precheck_reason == "scanner_ws_stale_backoff_active":
        now_value = float(now_ts)
        backoff_until = _safe_float(
            fast_precheck_fields.get("scanner_ws_stale_backoff_until"), 0.0
        )
        previous_first_epoch = _safe_float(
            (target or {}).get("_scanner_ws_backoff_watch_retention_first_epoch"),
            0.0,
        )
        if previous_first_epoch <= 0:
            first_epoch = now_value
            attempt_count = 1
        else:
            first_epoch = previous_first_epoch
            attempt_count = (
                _safe_int(
                    (target or {}).get("_scanner_ws_backoff_watch_retention_count"),
                    0,
                )
                + 1
            )
        age_sec = max(0.0, now_value - first_epoch)
        min_sec = _scanner_ws_backoff_watch_retention_min_sec()
        max_sec = _scanner_ws_backoff_watch_retention_max_sec()
        min_count = _scanner_ws_backoff_watch_retention_min_count()
        should_evict = age_sec >= max_sec or (
            age_sec >= min_sec and attempt_count >= min_count
        )
        target["_scanner_ws_backoff_watch_retention_active"] = not should_evict
        target["_scanner_ws_backoff_watch_retention_first_epoch"] = first_epoch
        target["_scanner_ws_backoff_watch_retention_last_epoch"] = now_value
        target["_scanner_ws_backoff_watch_retention_count"] = attempt_count
        target["_scanner_ws_backoff_watch_retention_until"] = backoff_until
        decision = {
            "should_evict": should_evict,
            "retention_active": not should_evict,
            "retention_reason": (
                "scanner_ws_stale_backoff_bounded_recovery"
                if not should_evict
                else "scanner_ws_stale_backoff_recovery_exhausted"
            ),
            "eviction_reason": "scanner_ws_stale_backoff_recovery_exhausted",
            "eviction_attempt_count": attempt_count,
            "terminal_stage": "scalping_scanner_fast_precheck",
            "terminal_reason": fast_precheck_reason,
            "fresh_input_confirmed": False,
            "stale_first_seen_epoch": f"{first_epoch:.3f}",
            "stale_age_sec": round(age_sec, 3),
            "ws_recovery_outcome": (
                "bounded_ws_recovery_pending"
                if not should_evict
                else "bounded_ws_recovery_exhausted"
            ),
            "source_quality_detail_route": (
                "scanner_ws_stale_backoff_bounded_watch_retention"
            ),
            "scanner_source_quality_reallocation_candidate": True,
            "fast_precheck_result": fast_precheck_fields.get("fast_precheck_result")
            or "budget_reallocated",
            "fast_precheck_reason": fast_precheck_reason,
            "fast_precheck_fields": fast_precheck_fields,
            "ws_backoff_retention_active": not should_evict,
            "ws_backoff_retention_reason": (
                "scanner_ws_stale_backoff_bounded_recovery"
                if not should_evict
                else "scanner_ws_stale_backoff_recovery_exhausted"
            ),
            "ws_backoff_retention_first_epoch": f"{first_epoch:.3f}",
            "ws_backoff_retention_age_sec": round(age_sec, 3),
            "ws_backoff_retention_min_sec": round(min_sec, 3),
            "ws_backoff_retention_max_sec": round(max_sec, 3),
            "ws_backoff_retention_attempt_count": attempt_count,
            "ws_backoff_retention_min_count": min_count,
            "ws_backoff_until": (
                f"{backoff_until:.3f}"
                if backoff_until > 0
                else "not_available_ws_backoff_until"
            ),
            "observed_epoch": f"{now_value:.3f}",
        }
        if should_evict:
            target["_scanner_ws_backoff_watch_retention_active"] = False
        return decision

    _reset_scanner_ws_backoff_watch_retention(target)
    return {
        "should_evict": True,
        "eviction_reason": "rising_missed_not_rising_budget_reallocated",
        "eviction_attempt_count": 1,
        "terminal_stage": "scalping_scanner_fast_precheck",
        "terminal_reason": fast_precheck_reason,
        "fresh_input_confirmed": False,
        "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
        "stale_age_sec": "not_applicable_stale_age_sec",
        "ws_recovery_outcome": "not_applicable_ws_recovery_outcome",
        "source_quality_detail_route": "scanner_rising_missed_budget_reallocated",
        "scanner_source_quality_reallocation_candidate": False,
        "fast_precheck_result": fast_precheck_fields.get("fast_precheck_result")
        or "budget_reallocated",
        "fast_precheck_reason": fast_precheck_reason,
        "fast_precheck_fields": fast_precheck_fields,
        "observed_epoch": f"{float(now_ts):.3f}",
    }


def _maybe_expire_scanner_watch_for_fast_precheck_budget(
    target,
    code,
    targets,
    *,
    now_ts,
    emit_event_fn=None,
    decision=None,
):
    decision = decision or _scanner_watch_eviction_decision_from_fast_precheck_budget(
        target,
        now_ts=now_ts,
    )
    if not decision.get("should_evict"):
        if (
            emit_event_fn
            and decision.get("ws_backoff_retention_active")
            and _safe_int(decision.get("ws_backoff_retention_attempt_count"), 0) == 1
        ):
            emit_event_fn(
                target,
                str(code or (target or {}).get("code") or "").strip()[:6],
                "scalping_scanner_ws_backoff_watch_retained",
                {
                    "metric_role": "runtime_source_quality_recovery_guard",
                    "decision_authority": (
                        "real_scalping_scanner_ws_backoff_watch_retention_only"
                    ),
                    "window_policy": "same_watch_bounded_ws_recovery",
                    "sample_floor": "not_applicable_runtime_recovery_guard",
                    "primary_decision_metric": "ws_backoff_retention_age_sec",
                    "source_quality_gate": (
                        "scalping_scanner_ws_backoff_watch_retention_contract"
                    ),
                    "source_quality_route": (
                        "runtime_watch_retained_without_entry_evaluation"
                    ),
                    "forbidden_uses": (
                        "stale_submit_bypass,heavy_eval_bypass,score_threshold_change,"
                        "provider_route_change,order_price_change,quantity_or_cap_change,"
                        "broker_guard_change,real_execution_quality_approval"
                    ),
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "retention_reason": decision.get("ws_backoff_retention_reason"),
                    "retention_first_epoch": decision.get(
                        "ws_backoff_retention_first_epoch"
                    ),
                    "retention_age_sec": decision.get("ws_backoff_retention_age_sec"),
                    "retention_min_sec": decision.get("ws_backoff_retention_min_sec"),
                    "retention_max_sec": decision.get("ws_backoff_retention_max_sec"),
                    "retention_attempt_count": decision.get(
                        "ws_backoff_retention_attempt_count"
                    ),
                    "retention_min_count": decision.get(
                        "ws_backoff_retention_min_count"
                    ),
                    "ws_backoff_until": decision.get("ws_backoff_until"),
                    "fast_precheck_result": decision.get("fast_precheck_result"),
                    "fast_precheck_reason": decision.get("fast_precheck_reason"),
                    "runtime_record_id": (target or {}).get("id")
                    or "not_applicable_runtime_record_id",
                    "stock_code": str(code or (target or {}).get("code") or "").strip()[
                        :6
                    ],
                    "target_status": (target or {}).get("status")
                    or "not_applicable_target_status",
                    "target_strategy": normalize_strategy(
                        (target or {}).get("strategy")
                    ),
                    "target_position_tag": normalize_position_tag(
                        normalize_strategy((target or {}).get("strategy")),
                        (target or {}).get("position_tag"),
                    ),
                    "observed_epoch": decision.get("observed_epoch")
                    or f"{float(now_ts):.3f}",
                },
            )
        return False
    return _expire_scanner_watch_target(
        target, code, targets, decision=decision, emit_event_fn=emit_event_fn
    )


def _maybe_expire_scanner_watch_for_no_trade(
    target, code, targets, ws_data, *, now_ts, emit_event_fn=None
):
    decision = _scanner_watch_eviction_decision_from_no_trade(
        target, ws_data, now_ts=now_ts
    )
    if not decision.get("should_evict"):
        return False
    return _expire_scanner_watch_target(
        target, code, targets, decision=decision, emit_event_fn=emit_event_fn
    )


def handle_ws_reg_budget_skipped(payload):
    payload = payload or {}
    skipped_codes = {
        str(code or "").strip()[:6]
        for code in (payload.get("codes") or [])
        if str(code or "").strip()
    }
    if not skipped_codes:
        return False
    now_ts = time.time()
    expired = []
    for target in list(ACTIVE_TARGETS or []):
        code = str((target or {}).get("code") or "").strip()[:6]
        if code not in skipped_codes or not _is_scanner_watching_target(target):
            continue
        decision = {
            "should_evict": True,
            "eviction_reason": "scanner_ws_budget_skipped_hot_slot_rotation",
            "eviction_attempt_count": 1,
            "terminal_stage": "ws_register_budget",
            "terminal_reason": "ws_item_budget_exhausted",
            "fresh_input_confirmed": False,
            "stale_first_seen_epoch": "not_applicable_stale_first_seen_epoch",
            "stale_age_sec": "not_applicable_stale_age_sec",
            "ws_recovery_outcome": "ws_reg_budget_skipped",
            "observed_epoch": f"{now_ts:.3f}",
        }
        if _expire_scanner_watch_target(
            target, code, ACTIVE_TARGETS, decision=decision
        ):
            expired.append(code)
    if expired:
        log_info(
            "[WS_REG_BUDGET_SKIPPED] expired scanner hot-slot targets "
            f"codes={','.join(sorted(set(expired)))} "
            f"max_items={payload.get('max_items', 'unknown')}"
        )
    return bool(expired)


def _scanner_watch_nonfresh_source_quality_reason(target):
    block = (target or {}).get("_scanner_watch_last_terminal_block")
    if not isinstance(block, dict):
        return ""
    stage = str(block.get("stage") or "")
    if stage not in sniper_state_handlers.SCANNER_WATCH_EVICTION_TERMINAL_STAGES:
        return ""
    if bool(block.get("fresh_input_confirmed")):
        return ""
    reason = str(block.get("reason") or "")
    return reason if reason in SCANNER_WATCH_EVICTION_SOURCE_QUALITY_REASONS else ""


def _maybe_expire_scanner_watch_after_full_eval(
    target, code, targets, *, now_ts, emit_event_fn=None
):
    if _maybe_expire_scanner_watch_for_terminal(
        target,
        code,
        targets,
        now_ts=now_ts,
        emit_event_fn=emit_event_fn,
    ):
        return True
    source_quality_reason = _scanner_watch_nonfresh_source_quality_reason(target)
    if not source_quality_reason:
        return _maybe_expire_scanner_watch_for_pool_block(
            target,
            code,
            targets,
            now_ts=now_ts,
            emit_event_fn=emit_event_fn,
        )
    if _maybe_expire_scanner_watch_for_stale(
        target,
        code,
        targets,
        now_ts=now_ts,
        stale_reason=source_quality_reason,
        recovery_fields={
            "ws_recovery_outcome": "source_quality_unresolved_no_ws_recovery"
        },
        emit_event_fn=emit_event_fn,
    ):
        return True
    return _maybe_expire_scanner_watch_for_pool_block(
        target,
        code,
        targets,
        now_ts=now_ts,
        emit_event_fn=emit_event_fn,
    )


def _is_real_holding_target(target):
    target = target or {}
    if str(target.get("status") or "").upper() != "HOLDING":
        return False
    return not _is_runtime_simulation_target(target) and not _is_runtime_probe_target(
        target
    )


def _scanner_queue_added_time(target, now_ts=None):
    now_ts = time.time() if now_ts is None else now_ts
    target = target or {}
    armed_ts = _safe_float(target.get("entry_armed_at_epoch"), 0.0)
    if armed_ts > 0:
        return armed_ts
    return _safe_float(target.get("added_time"), now_ts) or now_ts


def _scanner_last_full_eval_epoch(target):
    return _safe_float((target or {}).get("_scanner_last_full_eval_epoch"), 0.0)


def _scanner_positive_delta_value(target):
    target = target or {}
    delta = max(
        0.0,
        _safe_float(target.get("price_delta_since_first_seen_pct"), 0.0),
        _safe_float(target.get("comparable_flu_delta_since_first_seen"), 0.0),
    )
    if delta >= _scanner_rising_entry_min_delta_pct():
        return delta
    try:
        fallback_context = sniper_state_handlers._find_scanner_rising_strength_context(
            target,
            min_delta=_scanner_rising_entry_min_delta_pct(),
            require_bid_imbalance=False,
        )
    except Exception:
        fallback_context = {}
    if not (fallback_context or {}).get("allowed"):
        return delta
    fallback_delta = _safe_float(
        fallback_context.get("price_delta_since_first_seen_pct"), 0.0
    )
    if fallback_delta > delta and isinstance(target, dict):
        target["price_delta_since_first_seen_pct"] = f"{fallback_delta:.2f}"
        target.setdefault(
            "scanner_promotion_reason",
            fallback_context.get("scanner_promotion_reason") or "",
        )
        target.setdefault(
            "source_signature", fallback_context.get("source_signature") or ""
        )
        target["_scanner_rising_context_source"] = (
            fallback_context.get("scanner_context_source") or "promotion_event_fallback"
        )
        target["_scanner_rising_context_emitted_epoch"] = (
            fallback_context.get("scanner_context_emitted_epoch")
            or "not_applicable_scanner_context_emitted_epoch"
        )
    return max(delta, fallback_delta)


def _scanner_rising_entry_min_delta_pct():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_MIN_DELTA_PCT", "")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 1.0
    except Exception:
        value = 1.0
    return max(0.0, min(value, 20.0))


def _scanner_is_rising_entry_relief_candidate(target):
    if not _is_scanner_watching_target(target):
        return False
    existing_delta = _scanner_positive_delta_value(target)
    sniper_state_handlers._hydrate_scanner_promotion_runtime_context(target)
    hydrated_delta = _scanner_positive_delta_value(target)
    if existing_delta > hydrated_delta and isinstance(target, dict):
        target["price_delta_since_first_seen_pct"] = f"{existing_delta:.2f}"
    return max(existing_delta, hydrated_delta) >= _scanner_rising_entry_min_delta_pct()


def _scanner_rising_full_eval_extra_per_loop():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_RISING_FULL_EVAL_EXTRA_PER_LOOP", "")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 8
    except Exception:
        value = 8
    return max(0, min(value, 40))


def _scanner_common_watch_budget_priority_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_COMMON_WATCH_BUDGET_PRIORITY_ENABLED"
    )
    return _env_bool_from_value(raw, True)


def _scanner_first_present_value(target, *keys):
    target = target or {}
    for key in keys:
        value = target.get(key)
        if value not in (None, ""):
            return value
    return None


def _scanner_common_watch_budget_priority_fields(target):
    target = target or {}
    source_signature = str(target.get("source_signature") or "").upper()
    strong_source_tokens = {
        "BID_IMBALANCE_SURGE",
        "LOW_REBOUND_RISING_MISSED",
        "NEW_HIGH_CONFIRMATION",
        "OPEN_TOP",
        "PRICE_JUMP_START",
        "REALTIME_RANK_START",
        "VALUE_TOP",
        "VI_TRIGGERED",
        "VOLUME_SURGE_POSITIVE",
    }
    source_hits = sorted(
        token for token in strong_source_tokens if token in source_signature
    )
    source_score = min(len(source_hits), 3)

    buy_pressure = _safe_float(
        _scanner_first_present_value(
            target,
            "buy_pressure_10t",
            "last_buy_pressure_10t",
            "late_entry_fresh_buy_pressure_10t",
        ),
        None,
    )
    net_delta = _safe_float(
        _scanner_first_present_value(
            target,
            "net_aggressive_delta_10t",
            "late_entry_fresh_net_aggressive_delta_10t",
        ),
        None,
    )
    supply_pass = (
        (buy_pressure is not None and buy_pressure >= 68.0)
        or (net_delta is not None and net_delta > 0.0)
        or "BID_IMBALANCE_SURGE" in source_hits
    )

    tick_accel = _safe_float(
        _scanner_first_present_value(
            target,
            "tick_acceleration_ratio",
            "tick_accel",
            "late_entry_fresh_tick_acceleration_ratio",
        ),
        None,
    )
    tick_window_span = _safe_float(
        _scanner_first_present_value(
            target, "tick_window_span_sec", "late_entry_tick_window_span_sec"
        ),
        None,
    )
    speed_pass = (tick_accel is not None and tick_accel >= 1.0) and (
        tick_window_span is None or tick_window_span < 60.0
    )

    volume_ratio = _safe_float(target.get("volume_ratio_pct"), None)
    volume_pass = (
        (volume_ratio is not None and volume_ratio >= 150.0)
        or "VALUE_TOP" in source_hits
        or "VOLUME_SURGE_POSITIVE" in source_hits
    )

    quote_age_ms = _safe_float(
        _scanner_first_present_value(target, "quote_age_ms", "last_quote_age_ms"), None
    )
    quote_stale_raw = (
        str(target.get("quote_stale") or target.get("context_stale") or "")
        .strip()
        .lower()
    )
    quote_stale = quote_stale_raw in {"1", "true", "yes", "stale"}
    freshness_pass = (
        quote_age_ms is not None and quote_age_ms <= 3000.0
    ) and not quote_stale

    score = source_score
    score += 2 if supply_pass else 0
    score += 2 if speed_pass else 0
    score += 1 if volume_pass else 0
    score += 1 if freshness_pass else 0
    if quote_stale or (quote_age_ms is not None and quote_age_ms > 3000.0):
        score -= 2
    if tick_accel is not None and tick_accel < 0.8:
        score -= 1
    score = max(0, min(score, 9))

    if not _scanner_common_watch_budget_priority_enabled():
        tier = "disabled"
    elif score >= 6:
        tier = "high_priority_watch"
    elif score >= 3:
        tier = "standard_watch"
    else:
        tier = "low_budget_observe"

    missing_axes = []
    if (
        buy_pressure is None
        and net_delta is None
        and "BID_IMBALANCE_SURGE" not in source_hits
    ):
        missing_axes.append("supply")
    if tick_accel is None and tick_window_span is None:
        missing_axes.append("speed")
    if (
        volume_ratio is None
        and "VALUE_TOP" not in source_hits
        and "VOLUME_SURGE_POSITIVE" not in source_hits
    ):
        missing_axes.append("volume")
    if quote_age_ms is None and not quote_stale_raw:
        missing_axes.append("freshness")

    return {
        "scanner_common_watch_budget_priority_enabled": _scanner_common_watch_budget_priority_enabled(),
        "scanner_common_watch_budget_priority_tier": tier,
        "scanner_common_watch_budget_priority_score": score,
        "scanner_common_watch_budget_source_hits": (
            ",".join(source_hits) if source_hits else "-"
        ),
        "scanner_common_watch_budget_supply_pass": bool(supply_pass),
        "scanner_common_watch_budget_speed_pass": bool(speed_pass),
        "scanner_common_watch_budget_volume_pass": bool(volume_pass),
        "scanner_common_watch_budget_freshness_pass": bool(freshness_pass),
        "scanner_common_watch_budget_missing_axes": (
            ",".join(missing_axes) if missing_axes else "-"
        ),
        "scanner_common_watch_budget_buy_pressure_10t": (
            round(float(buy_pressure), 4) if buy_pressure is not None else "-"
        ),
        "scanner_common_watch_budget_net_aggressive_delta_10t": (
            round(float(net_delta), 4) if net_delta is not None else "-"
        ),
        "scanner_common_watch_budget_tick_acceleration_ratio": (
            round(float(tick_accel), 4) if tick_accel is not None else "-"
        ),
        "scanner_common_watch_budget_tick_window_span_sec": (
            round(float(tick_window_span), 4) if tick_window_span is not None else "-"
        ),
        "scanner_common_watch_budget_volume_ratio_pct": (
            round(float(volume_ratio), 4) if volume_ratio is not None else "-"
        ),
        "scanner_common_watch_budget_quote_age_ms": (
            round(float(quote_age_ms), 4) if quote_age_ms is not None else "-"
        ),
        "scanner_common_watch_budget_quote_stale": bool(quote_stale),
        "scanner_common_watch_budget_authority": "scanner_watch_budget_runtime_priority",
        "scanner_common_watch_budget_forbidden_uses": (
            "broker_submit_bypass,order_guard_relaxation,threshold_mutation,"
            "provider_route_change,bot_restart,real_execution_quality_approval"
        ),
    }


def _scanner_common_watch_budget_priority_score(target):
    if not _scanner_common_watch_budget_priority_enabled():
        return 0
    return _safe_int(
        _scanner_common_watch_budget_priority_fields(target).get(
            "scanner_common_watch_budget_priority_score"
        ),
        0,
    )


def _scanner_rising_cooldown_eviction_relief_enabled():
    return _env_bool(
        "KORSTOCKSCAN_SCANNER_RISING_COOLDOWN_EVICTION_RELIEF_ENABLED", False
    )


def _scanner_rising_cutoff_recheck_enabled():
    return _env_bool("KORSTOCKSCAN_SCANNER_RISING_CUTOFF_RECHECK_ENABLED", False)


def _scanner_rising_ws_gap_priority_recovery_enabled():
    return _env_bool(
        "KORSTOCKSCAN_SCANNER_RISING_WS_GAP_PRIORITY_RECOVERY_ENABLED", False
    )


def _scanner_rising_recheck_pending(target, now_ts=None):
    target = target or {}
    after_epoch = max(
        _safe_float(target.get("_scanner_rising_cooldown_recheck_after_epoch"), 0.0),
        _safe_float(target.get("_scanner_rising_cutoff_recheck_after_epoch"), 0.0),
        _safe_float(
            target.get("_scanner_rising_freshness_envelope_recheck_until_epoch"), 0.0
        ),
        _safe_float(
            target.get("_scanner_rising_latency_direct_recheck_after_epoch"), 0.0
        ),
        _safe_float(
            target.get("_scanner_rising_reversal_up_volatile_recheck_until_epoch"), 0.0
        ),
        _safe_float(
            target.get("_scanner_rising_reversal_up_watch_recheck_until_epoch"), 0.0
        ),
        _safe_float(
            target.get("_scanner_rising_ws_gap_priority_recheck_after_epoch"), 0.0
        ),
        _safe_float(
            target.get("_scanner_rising_terminal_hardgate_recheck_after_epoch"), 0.0
        ),
    )
    if after_epoch <= 0.0:
        return False
    now_ts = time.time() if now_ts is None else now_ts
    return after_epoch <= float(now_ts)


def _scanner_rising_entry_relief_fields(target, *, reason, budget_source="standard"):
    delta = _scanner_positive_delta_value(target)
    eligible = _scanner_is_rising_entry_relief_candidate(target)
    return {
        "rising_entry_relief_eligible": eligible,
        "rising_entry_relief_reason": str(
            reason or "not_applicable_rising_entry_relief"
        ),
        "scanner_positive_delta_pct": round(float(delta), 4),
        "scanner_full_eval_budget_source": str(budget_source or "standard"),
    }


def _scanner_set_rising_recheck(target, *, kind, after_epoch, reason):
    if not isinstance(target, dict):
        return
    key = f"_scanner_rising_{kind}_recheck_after_epoch"
    target[key] = float(after_epoch)
    target["_scanner_rising_recheck_reason"] = str(reason or kind)


def _scanner_strength_recheck_pending(target, now_ts=None):
    target = target or {}
    if not bool(target.get("entry_strength_momentum_recheck_pending")):
        return False
    after_epoch = _safe_float(
        target.get("entry_strength_momentum_recheck_after_epoch"), 0.0
    )
    now_ts = time.time() if now_ts is None else now_ts
    return after_epoch <= 0.0 or after_epoch <= float(now_ts)


def _scanner_strength_recheck_waiting(target, now_ts=None):
    target = target or {}
    if not bool(target.get("entry_strength_momentum_recheck_pending")):
        return False
    after_epoch = _safe_float(
        target.get("entry_strength_momentum_recheck_after_epoch"), 0.0
    )
    now_ts = time.time() if now_ts is None else now_ts
    return after_epoch > float(now_ts)


def _scanner_cooldown_recheck_waiting(target, now_ts=None):
    target = target or {}
    after_epoch = _safe_float(
        target.get("_scanner_rising_cooldown_recheck_after_epoch"), 0.0
    )
    now_ts = time.time() if now_ts is None else now_ts
    return after_epoch > float(now_ts)


def _scanner_full_eval_max_per_loop():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_FULL_EVAL_MAX_PER_LOOP")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 8
    except Exception:
        value = 8
    return max(1, min(value, 40))


def _scanner_full_eval_backlog_extra_per_loop():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_BACKLOG_EXTRA_PER_LOOP"
    )
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 4
    except Exception:
        value = 4
    return max(0, min(value, 40))


def _scanner_full_eval_auto_pressure_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_ENABLED"
    )
    return _env_bool_from_value(raw, True)


def _scanner_full_eval_auto_pressure_min_limit(base_limit):
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MIN_LIMIT"
    )
    value = _safe_int(raw, 6)
    return max(1, min(max(1, _safe_int(base_limit, 8)), value))


def _scanner_full_eval_auto_pressure_ms():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_PRESSURE_MS")
    return max(1000.0, _safe_float(raw, 12000.0))


def _scanner_full_eval_auto_relief_ms():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RELIEF_MS")
    return max(1000.0, _safe_float(raw, 7000.0))


def _scanner_full_eval_auto_cooldown_sec():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_COOLDOWN_SEC")
    return max(0.0, _safe_float(raw, 60.0))


def _scanner_full_eval_auto_recovery_streak():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_FULL_EVAL_AUTO_RECOVERY_STREAK"
    )
    return max(1, _safe_int(raw, 3))


def _scanner_full_eval_pressure_step(loop_elapsed_ms, pressure_ms):
    if loop_elapsed_ms >= pressure_ms * 2.0:
        return 4
    if loop_elapsed_ms >= pressure_ms * 1.5:
        return 2
    return 1


def _reset_scanner_full_eval_pressure_state():
    _SCANNER_FULL_EVAL_PRESSURE_STATE.update(
        {
            "reduction": 0,
            "last_adjust_ts": 0.0,
            "pressure_streak": 0,
            "relief_streak": 0,
        }
    )


def _scanner_full_eval_pressure_reduction(base_limit):
    if not _scanner_full_eval_auto_pressure_enabled():
        return 0
    base_limit = max(1, min(_safe_int(base_limit, 8), 40))
    min_limit = _scanner_full_eval_auto_pressure_min_limit(base_limit)
    max_reduction = max(0, base_limit - min_limit)
    reduction = max(0, _safe_int(_SCANNER_FULL_EVAL_PRESSURE_STATE.get("reduction"), 0))
    return min(reduction, max_reduction)


def _scanner_full_eval_base_effective_limit(queue_context, base_limit=None):
    if base_limit is None:
        base_limit = _scanner_full_eval_max_per_loop()
    else:
        base_limit = max(1, min(_safe_int(base_limit, 8), 40))
    scanner_watching_count = _safe_int(
        (queue_context or {}).get("scanner_watching_count"), 0
    )
    if scanner_watching_count <= base_limit:
        return base_limit
    backlog_extra_cap = _scanner_full_eval_backlog_extra_per_loop()
    backlog_extra = min(backlog_extra_cap, max(0, scanner_watching_count - base_limit))
    return max(1, min(base_limit + backlog_extra, 40))


def _scanner_full_eval_effective_limit(queue_context, base_limit=None):
    effective_base_limit = _scanner_full_eval_base_effective_limit(
        queue_context, base_limit=base_limit
    )
    reduction = _scanner_full_eval_pressure_reduction(effective_base_limit)
    if reduction <= 0:
        return effective_base_limit
    min_limit = _scanner_full_eval_auto_pressure_min_limit(effective_base_limit)
    return max(min_limit, effective_base_limit - reduction)


def _update_scanner_full_eval_pressure(
    loop_elapsed_ms, queue_context=None, *, now_ts=None, buy_time_allowed=True
):
    base_limit = _scanner_full_eval_base_effective_limit(queue_context or {})
    if not _scanner_full_eval_auto_pressure_enabled():
        _reset_scanner_full_eval_pressure_state()
        return base_limit

    if not buy_time_allowed:
        _SCANNER_FULL_EVAL_PRESSURE_STATE["pressure_streak"] = 0
        _SCANNER_FULL_EVAL_PRESSURE_STATE["relief_streak"] = 0
        return _scanner_full_eval_effective_limit(queue_context or {})

    now_ts = time.time() if now_ts is None else now_ts
    pressure_ms = _scanner_full_eval_auto_pressure_ms()
    relief_ms = min(_scanner_full_eval_auto_relief_ms(), pressure_ms)
    cooldown_sec = _scanner_full_eval_auto_cooldown_sec()
    current_limit = _scanner_full_eval_effective_limit(queue_context or {})
    min_limit = _scanner_full_eval_auto_pressure_min_limit(base_limit)
    last_adjust_ts = _safe_float(
        _SCANNER_FULL_EVAL_PRESSURE_STATE.get("last_adjust_ts"), 0.0
    )
    can_adjust = (now_ts - last_adjust_ts) >= cooldown_sec

    if loop_elapsed_ms >= pressure_ms:
        _SCANNER_FULL_EVAL_PRESSURE_STATE["pressure_streak"] = (
            _safe_int(_SCANNER_FULL_EVAL_PRESSURE_STATE.get("pressure_streak"), 0) + 1
        )
        _SCANNER_FULL_EVAL_PRESSURE_STATE["relief_streak"] = 0
        if can_adjust and current_limit > min_limit:
            next_limit = max(
                min_limit,
                current_limit
                - _scanner_full_eval_pressure_step(loop_elapsed_ms, pressure_ms),
            )
            if next_limit != current_limit:
                _SCANNER_FULL_EVAL_PRESSURE_STATE["reduction"] = max(
                    0, base_limit - next_limit
                )
                _SCANNER_FULL_EVAL_PRESSURE_STATE["last_adjust_ts"] = now_ts
                log_info(
                    f"[SCANNER_FULL_EVAL_PRESSURE] action=reduce "
                    f"loop_elapsed_ms={loop_elapsed_ms:.1f} "
                    f"base_limit={base_limit} effective_limit={next_limit} min_limit={min_limit} "
                    f"reduction={_SCANNER_FULL_EVAL_PRESSURE_STATE['reduction']}"
                )
            return _scanner_full_eval_effective_limit(queue_context or {})
        return current_limit

    if loop_elapsed_ms <= relief_ms:
        _SCANNER_FULL_EVAL_PRESSURE_STATE["pressure_streak"] = 0
        _SCANNER_FULL_EVAL_PRESSURE_STATE["relief_streak"] = (
            _safe_int(_SCANNER_FULL_EVAL_PRESSURE_STATE.get("relief_streak"), 0) + 1
        )
        relief_streak = _safe_int(
            _SCANNER_FULL_EVAL_PRESSURE_STATE.get("relief_streak"), 0
        )
        current_reduction = _safe_int(
            _SCANNER_FULL_EVAL_PRESSURE_STATE.get("reduction"), 0
        )
        if (
            can_adjust
            and current_reduction > 0
            and relief_streak >= _scanner_full_eval_auto_recovery_streak()
        ):
            next_reduction = max(0, current_reduction - 1)
            _SCANNER_FULL_EVAL_PRESSURE_STATE["reduction"] = next_reduction
            _SCANNER_FULL_EVAL_PRESSURE_STATE["last_adjust_ts"] = now_ts
            _SCANNER_FULL_EVAL_PRESSURE_STATE["relief_streak"] = 0
            next_limit = _scanner_full_eval_effective_limit(queue_context or {})
            log_info(
                f"[SCANNER_FULL_EVAL_PRESSURE] action=recover "
                f"loop_elapsed_ms={loop_elapsed_ms:.1f} "
                f"base_limit={base_limit} effective_limit={next_limit} reduction={next_reduction}"
            )
            return next_limit
        return current_limit

    _SCANNER_FULL_EVAL_PRESSURE_STATE["pressure_streak"] = 0
    _SCANNER_FULL_EVAL_PRESSURE_STATE["relief_streak"] = 0
    return current_limit


def _reset_scanner_runtime_eval_state(target):
    if not isinstance(target, dict):
        return
    for key in (
        "_scanner_last_full_eval_epoch",
        "_scanner_fast_precheck_logged_at",
        "_scanner_runtime_queue_lag_logged_at",
        "_scanner_heavy_eval_lag_logged_at",
        "_scanner_heavy_queue_enter_epoch",
        "_scanner_fast_precheck_result",
        "_scanner_fast_precheck_reason",
        "_scanner_fast_precheck_fields",
        "_scanner_watch_queue_lag_count",
        "_scanner_watch_queue_lag_first_observed_epoch",
        "_scanner_watch_queue_lag_last_observed_epoch",
        "_scanner_watching_runtime_skip_logged",
        "_scanner_rising_cooldown_recheck_after_epoch",
        "_scanner_rising_cutoff_recheck_after_epoch",
        "_scanner_rising_freshness_envelope_recheck_until_epoch",
        "_scanner_rising_latency_direct_recheck_after_epoch",
        "_scanner_rising_reversal_up_volatile_recheck_until_epoch",
        "_scanner_rising_reversal_up_watch_recheck_until_epoch",
        "_scanner_rising_ws_gap_priority_recheck_after_epoch",
        "_scanner_rising_recheck_reason",
        "_scanner_rising_entry_relief_eligible",
        "_scanner_rising_entry_relief_reason",
        "_scanner_positive_delta_pct",
        "_scanner_full_eval_budget_source",
        "entry_strength_momentum_recheck_pending",
        "entry_strength_momentum_recheck_reason",
        "entry_strength_momentum_recheck_source_quality_block_reason",
        "entry_strength_momentum_recheck_count",
        "entry_strength_momentum_recheck_after_epoch",
        "entry_strength_momentum_recheck_requested_at",
    ):
        target.pop(key, None)


def _scanner_promotion_anchor_time(payload, default_ts):
    payload = payload or {}
    for key in (
        "entry_armed_at_epoch",
        "scanner_promotion_emitted_epoch",
        "added_time",
    ):
        value = _safe_float(payload.get(key), 0.0)
        if value > 0:
            return value
    return default_ts


def _runtime_added_time_for_target(target, now_ts=None):
    """Preserve scanner promotion recency across restarts and DB poll rehydration."""
    now_ts = time.time() if now_ts is None else now_ts
    target = target or {}
    if _is_scanner_runtime_target(target):
        armed_ts = _safe_float(target.get("entry_armed_at_epoch"), 0.0)
        if armed_ts > 0:
            return armed_ts
    return _safe_float(target.get("added_time"), now_ts) or now_ts


def _is_scalping_fifo_target(target):
    target = target or {}
    strategy = normalize_strategy(target.get("strategy"))
    position_tag = normalize_position_tag(strategy, target.get("position_tag"))
    return strategy == "SCALPING" and position_tag not in {
        "VCP_CANDID",
        "VCP_SHOOTING",
        "VCP_NEXT",
    }


def _scalping_fifo_candidates(watching_stocks, now_ts):
    return sorted(
        [t for t in watching_stocks if _is_scalping_fifo_target(t)],
        key=lambda x: _runtime_added_time_for_target(x, now_ts=now_ts),
    )


def _scalping_fifo_base_max_active():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 16
    except Exception:
        value = 16
    return max(1, min(value, 80))


def _scalping_watching_ttl_sec():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCALPING_WATCHING_TTL_SEC")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 1800.0
    except Exception:
        value = 1800.0
    return max(300.0, min(value, 7200.0))


def _scalping_dynamic_watch_cap_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_CAP_ENABLED"
    )
    return _env_bool_from_value(raw, True)


def _scalping_dynamic_watch_cap_min(base_cap):
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_MIN_ACTIVE")
    value = _safe_int(raw, 16)
    return max(1, min(base_cap, value))


def _scalping_dynamic_watch_cap_pressure_ms():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_PRESSURE_MS"
    )
    return max(1000.0, _safe_float(raw, 12000.0))


def _scalping_dynamic_watch_cap_relief_ms():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RELIEF_MS")
    return max(1000.0, _safe_float(raw, 7000.0))


def _scalping_dynamic_watch_cap_cooldown_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_COOLDOWN_SEC"
    )
    return max(0.0, _safe_float(raw, 60.0))


def _scalping_dynamic_watch_cap_recovery_streak():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCALPING_WATCHING_DYNAMIC_RECOVERY_STREAK"
    )
    return max(1, _safe_int(raw, 3))


def _scalping_attach_replace_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCALPING_WATCHING_ATTACH_REPLACE_ENABLED"
    )
    return _env_bool_from_value(raw, True)


def _scalping_dynamic_watch_cap_step(loop_elapsed_ms, pressure_ms):
    if loop_elapsed_ms >= pressure_ms * 2.0:
        return 3
    if loop_elapsed_ms >= pressure_ms * 1.5:
        return 2
    return 1


def _reset_scalping_dynamic_watch_cap_state():
    _SCALPING_DYNAMIC_WATCH_CAP_STATE.update(
        {
            "effective_cap": None,
            "last_adjust_ts": 0.0,
            "pressure_streak": 0,
            "relief_streak": 0,
        }
    )


def _scalping_dynamic_watch_cap_effective(base_cap):
    if not _scalping_dynamic_watch_cap_enabled():
        return base_cap
    effective_cap = _safe_int(_SCALPING_DYNAMIC_WATCH_CAP_STATE.get("effective_cap"), 0)
    if effective_cap <= 0:
        return base_cap
    min_cap = _scalping_dynamic_watch_cap_min(base_cap)
    clamped_cap = max(min_cap, min(base_cap, effective_cap))
    if clamped_cap != effective_cap:
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["effective_cap"] = (
            None if clamped_cap >= base_cap else clamped_cap
        )
    return clamped_cap


def _scalping_fifo_max_active():
    base_cap = _scalping_fifo_base_max_active()
    return _scalping_dynamic_watch_cap_effective(base_cap)


def _scalping_watch_budget_reallocation_enabled():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_WATCH_BUDGET_REALLOCATION_ENABLED"
    )
    return _env_bool_from_value(raw, True)


def _scalping_watch_budget_opening_window_active(now_ts):
    now_time = datetime.fromtimestamp(float(now_ts)).time()
    config = sniper_state_handlers._opening_rotation_entry_config()
    return bool(config.enabled) and config.observe_start <= now_time <= config.entry_end


def _scalping_watch_budget_owner(target, now_ts=None):
    """Resolve observation-budget ownership; never changes trade ownership."""

    target = target or {}
    explicit = target.get("scanner_watch_budget_owner")
    if str(explicit or "").strip().lower() in {
        GENERAL_SCALPING,
        OPENING_ROTATION,
        RISING_MISSED,
    }:
        return normalize_watch_budget_owner(explicit)
    if not _is_scanner_runtime_target(target):
        return GENERAL_SCALPING
    now_ts = time.time() if now_ts is None else now_ts
    return classify_watch_budget_owner(
        source_signature=target.get("source_signature"),
        rising_missed_lineage=target.get("rising_missed_lineage"),
        position_tag=target.get("position_tag") or "SCANNER",
        day_change_pct=_safe_float(
            target.get(
                "current_flu_rate", target.get("price_delta_since_first_seen_pct")
            ),
            0.0,
        ),
        now_dt=datetime.fromtimestamp(float(now_ts)),
        explicit_owner=explicit,
        opening_config=sniper_state_handlers._opening_rotation_entry_config(),
        # DB rows created before this contract have no source metadata.  Keep
        # them in the rising-centered pool instead of inflating general slots.
        missing_default=RISING_MISSED,
    )


def _scalping_watch_budget_policy_fields(targets, now_ts):
    total = _scalping_fifo_max_active()
    opening_active = _scalping_watch_budget_opening_window_active(now_ts)
    policy = watch_budget_limits(total, opening_window_active=opening_active)
    counts = {GENERAL_SCALPING: 0, OPENING_ROTATION: 0, RISING_MISSED: 0}
    for target in targets or []:
        owner = _scalping_watch_budget_owner(target, now_ts=now_ts)
        counts[owner] = counts.get(owner, 0) + 1
    allowances = watch_budget_owner_allowances(
        counts,
        total=total,
        opening_window_active=opening_active,
    )
    return {
        "scanner_watch_budget_policy": "general1_opening3_rising_residual_v1",
        "scanner_watch_budget_total": total,
        "scanner_watch_budget_opening_window_active": opening_active,
        "scanner_watch_budget_general_max": policy.general_max,
        "scanner_watch_budget_opening_protected": policy.opening_protected,
        "scanner_watch_budget_rising_guaranteed": policy.rising_guaranteed,
        "scanner_watch_budget_rising_max_with_borrow": policy.rising_max_with_borrow,
        "scanner_watch_budget_owner_counts": counts,
        "scanner_watch_budget_owner_allowances": allowances,
    }


def _scalping_watch_budget_overflow_candidates(targets, now_ts):
    candidates = [
        target
        for target in targets or []
        if str((target or {}).get("status") or "").upper() == "WATCHING"
        and _is_scalping_fifo_target(target)
    ]
    total = _scalping_fifo_max_active()
    if not _scalping_watch_budget_reallocation_enabled():
        overflow = max(0, len(candidates) - total)
        return _scalping_fifo_overflow_candidates(candidates, now_ts)[:overflow]

    fields = _scalping_watch_budget_policy_fields(candidates, now_ts)
    allowances = fields["scanner_watch_budget_owner_allowances"]
    selected = []
    selected_ids = set()
    for owner in (GENERAL_SCALPING, OPENING_ROTATION, RISING_MISSED):
        owner_targets = [
            target
            for target in candidates
            if _scalping_watch_budget_owner(target, now_ts=now_ts) == owner
        ]
        excess = max(0, len(owner_targets) - allowances[owner])
        for target in _scalping_fifo_overflow_candidates(owner_targets, now_ts)[
            :excess
        ]:
            identity = id(target)
            if identity not in selected_ids:
                selected.append(target)
                selected_ids.add(identity)

    remaining = [target for target in candidates if id(target) not in selected_ids]
    total_excess = max(0, len(remaining) - total)
    for target in _scalping_fifo_overflow_candidates(remaining, now_ts)[:total_excess]:
        identity = id(target)
        if identity not in selected_ids:
            selected.append(target)
            selected_ids.add(identity)
    return selected


def _scalping_attach_capacity_decision(new_target, now_ts, watching_targets=None):
    if not _is_scalping_fifo_target(new_target):
        return True, [], {}
    if watching_targets is None:
        watching_targets = [
            target
            for target in ACTIVE_TARGETS
            if str((target or {}).get("status") or "").upper() == "WATCHING"
            and _is_scalping_fifo_target(target)
        ]
    candidate = dict(new_target or {})
    candidate["_scanner_attach_capacity_candidate"] = True
    combined = [*watching_targets, candidate]
    overflow = _scalping_watch_budget_overflow_candidates(combined, now_ts)
    candidate_overflow = any(
        item.get("_scanner_attach_capacity_candidate") for item in overflow
    )
    replacements = [
        item for item in overflow if not item.get("_scanner_attach_capacity_candidate")
    ]
    fields = _scalping_watch_budget_policy_fields(combined, now_ts)
    owner = _scalping_watch_budget_owner(candidate, now_ts=now_ts)
    owner_count = fields["scanner_watch_budget_owner_counts"].get(owner, 0)
    fields.update(
        {
            "scanner_watch_budget_owner": owner,
            "scanner_watch_budget_slot_type": watch_budget_slot_type(
                owner,
                owner_count,
                total=fields["scanner_watch_budget_total"],
                opening_window_active=fields[
                    "scanner_watch_budget_opening_window_active"
                ],
            ),
            "scanner_watch_budget_candidate_overflow": candidate_overflow,
            "scanner_watch_budget_replacement_count": len(replacements),
        }
    )
    return not candidate_overflow, replacements, fields


def _scalping_attach_capacity_allows(new_target, now_ts):
    allowed, replacements, _fields = _scalping_attach_capacity_decision(
        new_target, now_ts
    )
    if replacements and not _scalping_attach_replace_enabled():
        return False
    return allowed


def _update_scalping_dynamic_watch_cap(
    loop_elapsed_ms, *, now_ts=None, buy_time_allowed=True
):
    if not _scalping_dynamic_watch_cap_enabled():
        return _scalping_fifo_base_max_active()

    base_cap = _scalping_fifo_base_max_active()
    if not buy_time_allowed:
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["pressure_streak"] = 0
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["relief_streak"] = 0
        return _scalping_dynamic_watch_cap_effective(base_cap)

    now_ts = time.time() if now_ts is None else now_ts
    pressure_ms = _scalping_dynamic_watch_cap_pressure_ms()
    relief_ms = min(_scalping_dynamic_watch_cap_relief_ms(), pressure_ms)
    cooldown_sec = _scalping_dynamic_watch_cap_cooldown_sec()
    current_cap = _scalping_dynamic_watch_cap_effective(base_cap)
    min_cap = _scalping_dynamic_watch_cap_min(base_cap)
    last_adjust_ts = _safe_float(
        _SCALPING_DYNAMIC_WATCH_CAP_STATE.get("last_adjust_ts"), 0.0
    )
    can_adjust = (now_ts - last_adjust_ts) >= cooldown_sec

    if loop_elapsed_ms >= pressure_ms:
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["pressure_streak"] = (
            _safe_int(_SCALPING_DYNAMIC_WATCH_CAP_STATE.get("pressure_streak"), 0) + 1
        )
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["relief_streak"] = 0
        if can_adjust and current_cap > min_cap:
            next_cap = max(
                min_cap,
                current_cap
                - _scalping_dynamic_watch_cap_step(loop_elapsed_ms, pressure_ms),
            )
            if next_cap != current_cap:
                _SCALPING_DYNAMIC_WATCH_CAP_STATE["effective_cap"] = next_cap
                _SCALPING_DYNAMIC_WATCH_CAP_STATE["last_adjust_ts"] = now_ts
                log_info(
                    f"[SCALPING_DYNAMIC_WATCH_CAP] action=reduce "
                    f"loop_elapsed_ms={loop_elapsed_ms:.1f} "
                    f"base_cap={base_cap} effective_cap={next_cap} min_cap={min_cap}"
                )
            return _scalping_dynamic_watch_cap_effective(base_cap)
        return current_cap

    if loop_elapsed_ms <= relief_ms:
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["pressure_streak"] = 0
        _SCALPING_DYNAMIC_WATCH_CAP_STATE["relief_streak"] = (
            _safe_int(_SCALPING_DYNAMIC_WATCH_CAP_STATE.get("relief_streak"), 0) + 1
        )
        relief_streak = _safe_int(
            _SCALPING_DYNAMIC_WATCH_CAP_STATE.get("relief_streak"), 0
        )
        if (
            can_adjust
            and current_cap < base_cap
            and relief_streak >= _scalping_dynamic_watch_cap_recovery_streak()
        ):
            next_cap = min(base_cap, current_cap + 1)
            _SCALPING_DYNAMIC_WATCH_CAP_STATE["effective_cap"] = (
                None if next_cap >= base_cap else next_cap
            )
            _SCALPING_DYNAMIC_WATCH_CAP_STATE["last_adjust_ts"] = now_ts
            _SCALPING_DYNAMIC_WATCH_CAP_STATE["relief_streak"] = 0
            log_info(
                f"[SCALPING_DYNAMIC_WATCH_CAP] action=recover "
                f"loop_elapsed_ms={loop_elapsed_ms:.1f} "
                f"base_cap={base_cap} effective_cap={next_cap}"
            )
            return _scalping_dynamic_watch_cap_effective(base_cap)
        return current_cap

    _SCALPING_DYNAMIC_WATCH_CAP_STATE["pressure_streak"] = 0
    _SCALPING_DYNAMIC_WATCH_CAP_STATE["relief_streak"] = 0
    return current_cap


def _scalping_fifo_overflow_candidates(scalp_fifo_targets, now_ts):
    """Prefer expiring non-scanner and non-rising scanner rows before rising scanner promotions."""
    scanner_new_promotion_grace_sec = _scanner_fifo_new_promotion_grace_sec()

    def _overflow_rank(target):
        if not _is_scanner_watching_target(target):
            return (0, _runtime_added_time_for_target(target, now_ts=now_ts))
        armed_epoch = _runtime_added_time_for_target(target, now_ts=now_ts)
        last_full_eval = _scanner_last_full_eval_epoch(target)
        under_10000_priority = _under_10000_runtime_priority_rank(target)
        if under_10000_priority:
            if last_full_eval > 0:
                return (1, last_full_eval, armed_epoch)
            return (2, armed_epoch)
        if (
            scanner_new_promotion_grace_sec > 0.0
            and armed_epoch > 0.0
            and float(now_ts) - armed_epoch < scanner_new_promotion_grace_sec
        ):
            return (9, armed_epoch)
        rising = (
            _scanner_positive_delta_value(target)
            >= _scanner_rising_entry_min_delta_pct()
        )
        if not rising:
            if last_full_eval > 0:
                return (3, last_full_eval, armed_epoch)
            return (4, armed_epoch)
        if last_full_eval > 0:
            return (
                6,
                _scanner_common_watch_budget_priority_score(target),
                last_full_eval,
                armed_epoch,
            )
        return (7, _scanner_common_watch_budget_priority_score(target), armed_epoch)

    return sorted(list(scalp_fifo_targets or []), key=_overflow_rank)


def _expire_scalping_watch_budget_targets(
    expired_targets,
    active_targets,
    *,
    reason,
):
    """Expire displaced observation rows and unregister their WS symbols."""

    expired_targets = list(expired_targets or [])
    if not expired_targets:
        return []
    expired_ids = [target.get("id") for target in expired_targets if target.get("id")]
    if expired_ids:
        try:
            with DB.get_session() as session:
                session.query(RecommendationHistory).filter(
                    RecommendationHistory.id.in_(expired_ids)
                ).update({"status": "EXPIRED"}, synchronize_session=False)
        except Exception as exc:
            log_error(f"[SCANNER_WATCH_BUDGET] DB expiration failed: {exc}")

    expired_codes = []
    for target in expired_targets:
        active_targets[:] = [item for item in active_targets if item is not target]
        code = str(target.get("code") or "").strip()[:6]
        if code:
            expired_codes.append(code)
        emit_pipeline_event(
            "ENTRY_PIPELINE",
            str(target.get("name") or "-"),
            code,
            "scalping_scanner_watch_budget_reallocated",
            record_id=target.get("id"),
            fields={
                "metric_role": "runtime_capacity_provenance",
                "decision_authority": "scanner_observation_budget_only",
                "runtime_effect": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "scanner_watch_budget_owner": _scalping_watch_budget_owner(target),
                "scanner_watch_budget_reallocation_reason": reason,
                "forbidden_uses": (
                    "order_submit,quantity_change,cash_budget_change,provider_change,"
                    "entry_or_exit_threshold_change"
                ),
            },
        )
    active_codes = {
        str(target.get("code") or "").strip()[:6]
        for target in active_targets or []
        if str(target.get("status") or "").upper() not in {"COMPLETED", "EXPIRED"}
    }
    unregister_codes = [
        code
        for code in sorted(set(expired_codes))
        if code not in active_codes
        and not should_retain_ws_subscription(code)
        and not sniper_state_handlers.should_retain_rising_missed_nxt_post_block_subscription(
            code
        )
    ]
    if unregister_codes:
        event_bus.publish(
            "COMMAND_WS_UNREG",
            {
                "codes": unregister_codes,
                "source": "scalping_scanner_watch_budget_reallocation",
                "reason": reason,
            },
        )
    log_info(
        "[SCANNER_WATCH_BUDGET] "
        f"expired={len(expired_targets)} reason={reason} "
        f"codes={','.join(sorted(set(expired_codes)))}"
    )
    return expired_targets


def _initial_ws_registration_groups(targets, now_ts=None):
    now_ts = time.time() if now_ts is None else now_ts
    priority_codes = []
    scanner_targets = []
    seen_priority = set()

    def _target_key(target):
        target = target or {}
        return target.get("id") or str(target.get("code") or "").strip()[:6]

    for target in targets or []:
        status = str((target or {}).get("status") or "").upper()
        if status in {"COMPLETED", "EXPIRED"}:
            continue
        if _is_disabled_swing_watching_target(target):
            continue
        code = str((target or {}).get("code") or "").strip()[:6]
        if not code:
            continue
        if _is_scanner_watching_target(target):
            scanner_targets.append(target)
            continue
        if code not in seen_priority:
            priority_codes.append(code)
            seen_priority.add(code)

    overflow_ids = {
        _target_key(item)
        for item in _scalping_watch_budget_overflow_candidates(scanner_targets, now_ts)
    }
    scanner_codes = []
    seen_scanner = set()
    for target in scanner_targets:
        if _target_key(target) in overflow_ids:
            continue
        code = str(target.get("code") or "").strip()[:6]
        if code and code not in seen_scanner:
            scanner_codes.append(code)
            seen_scanner.add(code)

    return priority_codes, scanner_codes


def _runtime_iteration_targets(targets, now_ts):
    """Prioritize recently scanner-promoted WATCHING rows without mutating ACTIVE_TARGETS."""
    indexed = [
        (idx, target)
        for idx, target in enumerate(targets or [])
        if not _is_disabled_swing_watching_target(target)
    ]

    def _priority(item):
        original_index, target = item
        status = str((target or {}).get("status") or "").upper()
        if status in {"BUY_ORDERED", "SELL_ORDERED"}:
            status_rank = 0
            recency_key = 0.0
        elif (
            status == "HOLDING"
            and _env_bool_from_value(
                (target or {}).get("shallow_source_gap_recheck_armed"),
                default=False,
            )
            and _is_real_holding_target(target)
        ):
            # The recheck's decision window is 10-20 seconds. Keep it behind
            # in-flight orders but ahead of regular holding/scanner work.
            status_rank = 0
            recency_key = 1.0
        elif _is_real_holding_target(target):
            status_rank = 1
            recency_key = 0.0
        elif _is_scanner_watching_target(target):
            status_rank = 2
            last_full_eval = _scanner_last_full_eval_epoch(target)
            pending_recheck = _scanner_strength_recheck_pending(target, now_ts=now_ts)
            rising_recheck = _scanner_rising_recheck_pending(target, now_ts=now_ts)
            cooldown_waiting = _scanner_cooldown_recheck_waiting(target, now_ts=now_ts)
            positive_delta = _scanner_positive_delta_value(target)
            selection_delta = rising_missed_selection_rank_delta(target)
            watch_budget_score = _scanner_common_watch_budget_priority_score(target)
            owner_rank = 0
            if _scalping_watch_budget_reallocation_enabled():
                owner_rank = {
                    OPENING_ROTATION: 0,
                    RISING_MISSED: 1,
                    GENERAL_SCALPING: 2,
                }.get(_scalping_watch_budget_owner(target, now_ts=now_ts), 3)
            under_10000_priority = _under_10000_runtime_priority_rank(target)
            recency_key = (
                (
                    2
                    if cooldown_waiting
                    else (0 if pending_recheck or rising_recheck else 1)
                ),
                owner_rank,
                under_10000_priority,
                -watch_budget_score,
                -selection_delta,
                0 if last_full_eval <= 0 else 1,
                -positive_delta,
                (
                    -_scanner_queue_added_time(target, now_ts=now_ts)
                    if last_full_eval <= 0
                    else last_full_eval
                ),
                -_scanner_queue_added_time(target, now_ts=now_ts),
            )
        elif status == "HOLDING":
            status_rank = 3
            recency_key = 0.0
        elif status == "WATCHING":
            status_rank = 4
            recency_key = _runtime_added_time_for_target(target, now_ts=now_ts)
        else:
            status_rank = 5
            recency_key = 0.0
        return (status_rank, recency_key, original_index)

    return [target for _, target in sorted(indexed, key=_priority)]


def _runtime_queue_context(targets, now_ts):
    iteration_targets = _runtime_iteration_targets(targets, now_ts=now_ts)
    watching = [
        t
        for t in iteration_targets
        if str((t or {}).get("status") or "").upper() == "WATCHING"
    ]
    scanner_watching = [t for t in watching if _is_scanner_watching_target(t)]
    real_holding = [t for t in iteration_targets if _is_real_holding_target(t)]
    non_real_holding = [
        t
        for t in iteration_targets
        if str((t or {}).get("status") or "").upper() == "HOLDING"
        and not _is_real_holding_target(t)
    ]
    queue_rank_by_obj = {
        id(target): idx + 1 for idx, target in enumerate(iteration_targets)
    }
    scanner_rank_by_obj = {
        id(target): idx + 1 for idx, target in enumerate(scanner_watching)
    }
    first_scanner_index = next(
        (
            idx
            for idx, target in enumerate(iteration_targets)
            if _is_scanner_watching_target(target)
        ),
        len(iteration_targets),
    )
    return {
        "iteration_targets": iteration_targets,
        "queue_rank_by_obj": queue_rank_by_obj,
        "scanner_rank_by_obj": scanner_rank_by_obj,
        "watching_count": len(watching),
        "scanner_watching_count": len(scanner_watching),
        "real_holding_count": len(real_holding),
        "non_real_holding_count": len(non_real_holding),
        "pre_scanner_runtime_count": first_scanner_index,
        "loop_started_epoch": now_ts,
    }


def _scanner_latency_anchor_epoch(target, default_ts):
    target = target or {}
    for key in (
        "entry_armed_at_epoch",
        "scanner_promotion_emitted_epoch",
        "added_time",
    ):
        value = _safe_float(target.get(key), 0.0)
        if value > 0:
            return value
    return float(default_ts)


def _scanner_latency_ws_type_epoch(ws_data, type_name):
    type_ts = (ws_data or {}).get("last_realtime_type_ts")
    if not isinstance(type_ts, dict):
        return 0.0
    return _safe_float(type_ts.get(type_name), 0.0)


def _scanner_promotion_latency_trace_fields(
    target,
    ws_data,
    *,
    now_ts,
    trace_phase,
    fast_precheck_fields=None,
    heavy_queue_enter_epoch=None,
):
    target = target or {}
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    fast_precheck_fields = (
        fast_precheck_fields if isinstance(fast_precheck_fields, dict) else {}
    )
    anchor_epoch = _scanner_latency_anchor_epoch(target, now_ts)
    last_0b_epoch = _scanner_latency_ws_type_epoch(ws_data, "0B")
    last_history_epoch = 0.0
    history = ws_data.get("strength_momentum_history")
    if isinstance(history, list):
        for item in reversed(history):
            if isinstance(item, dict):
                last_history_epoch = _safe_float(
                    item.get("ts") or item.get("timestamp"), 0.0
                )
                if last_history_epoch > 0:
                    break
    heavy_enter = _safe_float(
        heavy_queue_enter_epoch,
        _safe_float(target.get("_scanner_heavy_queue_enter_epoch"), 0.0),
    )
    strategy = normalize_strategy(target.get("strategy"))
    return {
        "metric_role": "funnel_count",
        "decision_authority": "real_scalping_scanner_latency_observation_only",
        "window_policy": "same_day_intraday_light",
        "sample_floor": "not_applicable_runtime_observation",
        "primary_decision_metric": "promotion_to_trace_sec",
        "source_quality_gate": "scalping_scanner_promotion_latency_trace_contract",
        "source_quality_route": "runtime_scanner_latency_trace_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,real_execution_quality_approval"
        ),
        "trace_phase": str(trace_phase or "unknown_trace_phase"),
        "scanner_promotion_id": target.get("scanner_promotion_id")
        or "not_applicable_scanner_promotion_id",
        "scanner_promotion_emitted_epoch": target.get("scanner_promotion_emitted_epoch")
        or "not_applicable_scanner_promotion_emitted_epoch",
        "source_signature": target.get("source_signature")
        or "not_applicable_source_signature",
        "runtime_record_id": target.get("id") or "not_applicable_runtime_record_id",
        "stock_code": str(target.get("code") or "").strip()[:6]
        or "not_applicable_stock_code",
        "target_status": target.get("status") or "not_applicable_target_status",
        "target_strategy": strategy,
        "target_position_tag": normalize_position_tag(
            strategy, target.get("position_tag")
        ),
        "promotion_anchor_epoch": f"{float(anchor_epoch):.3f}",
        "trace_observed_epoch": f"{float(now_ts):.3f}",
        "promotion_to_trace_sec": round(
            max(0.0, float(now_ts) - float(anchor_epoch)), 3
        ),
        "promotion_to_last_0b_sec": (
            round(max(0.0, last_0b_epoch - anchor_epoch), 3)
            if last_0b_epoch > 0 and last_0b_epoch >= anchor_epoch
            else "not_available_promotion_to_last_0b_sec"
        ),
        "last_0b_to_trace_sec": (
            round(max(0.0, float(now_ts) - last_0b_epoch), 3)
            if last_0b_epoch > 0
            else "not_available_last_0b_to_trace_sec"
        ),
        "promotion_to_strength_history_sec": (
            round(max(0.0, last_history_epoch - anchor_epoch), 3)
            if last_history_epoch > 0 and last_history_epoch >= anchor_epoch
            else "not_available_promotion_to_strength_history_sec"
        ),
        "strength_history_to_trace_sec": (
            round(max(0.0, float(now_ts) - last_history_epoch), 3)
            if last_history_epoch > 0
            else "not_available_strength_history_to_trace_sec"
        ),
        "heavy_queue_enter_epoch": (
            f"{float(heavy_enter):.3f}"
            if heavy_enter > 0
            else "not_available_heavy_queue_enter_epoch"
        ),
        "fast_precheck_result": fast_precheck_fields.get("fast_precheck_result")
        or target.get("_scanner_fast_precheck_result")
        or "not_available_fast_precheck_result",
        "fast_precheck_reason": fast_precheck_fields.get("fast_precheck_reason")
        or target.get("_scanner_fast_precheck_reason")
        or "not_available_fast_precheck_reason",
        "ws_curr": (
            ws_data.get("curr")
            if ws_data.get("curr") not in (None, "")
            else "not_applicable_ws_curr"
        ),
    }


def _runtime_scanner_ws_snapshot_cache(iteration_targets):
    """Fetch scanner WATCHING snapshots in one WS-manager lock acquisition."""
    manager = WS_MANAGER
    if manager is None or not hasattr(manager, "get_all_data"):
        return {}
    codes = []
    seen = set()
    for target in iteration_targets or []:
        if not _is_scanner_watching_target(target):
            continue
        code = str((target or {}).get("code") or "").strip()[:6]
        if code and code not in seen:
            codes.append(code)
            seen.add(code)
    if not codes:
        return {}
    try:
        lock_wait_ms = float(
            os.getenv("KORSTOCKSCAN_SCANNER_WS_CACHE_LOCK_WAIT_MS", "25") or 25.0
        )
    except Exception:
        lock_wait_ms = 25.0
    lock_wait_sec = max(0.0, min(0.2, lock_wait_ms / 1000.0))
    manager_lock = getattr(manager, "lock", None)
    realtime_data = getattr(manager, "realtime_data", None)
    snapshot_target = getattr(manager, "_snapshot_target", None)
    normalize_code = getattr(manager, "_normalize_code", None)
    if (
        hasattr(manager_lock, "acquire")
        and isinstance(realtime_data, dict)
        and callable(snapshot_target)
        and callable(normalize_code)
    ):
        acquired = False
        try:
            acquired = manager_lock.acquire(timeout=lock_wait_sec)
            if not acquired:
                return {code: {} for code in codes}
            snapshots = {}
            for code in codes:
                norm_code = normalize_code(code)
                target = realtime_data.get(norm_code, {})
                snapshots[norm_code] = snapshot_target(target) if target else {}
            return snapshots
        except Exception as exc:
            log_error(f"[SCANNER_WS_CACHE] nonblocking snapshot lookup failed: {exc}")
            return {code: {} for code in codes}
        finally:
            if acquired:
                try:
                    manager_lock.release()
                except Exception:
                    pass
    try:
        snapshots = manager.get_all_data(codes) or {}
    except Exception as exc:
        log_error(f"[SCANNER_WS_CACHE] bulk snapshot lookup failed: {exc}")
        return {}
    if not isinstance(snapshots, dict):
        return {}
    return snapshots


def _is_non_real_same_symbol_observation(target):
    target = target or {}
    status = str(target.get("status") or "").upper()
    if status in {"BUY_ORDERED", "SELL_ORDERED"}:
        return False
    return _is_runtime_simulation_target(target) or _is_runtime_probe_target(target)


def _same_symbol_active_conflict_reason(target):
    target = target or {}
    status = str(target.get("status") or "").upper()
    if status in {"COMPLETED", "EXPIRED"}:
        return ""
    if _is_non_real_same_symbol_observation(target):
        return ""
    if status in {"BUY_ORDERED", "SELL_ORDERED"}:
        return "same_symbol_active_order_or_holding"
    if status == "HOLDING":
        return "same_symbol_active_order_or_holding"
    return "same_symbol_active_runtime_target"


def _parse_quote_price(value):
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0
    try:
        return abs(int(float(text.replace("+", ""))))
    except Exception:
        return 0


def _scanner_rest_quote_fallback_rate_limit(now_ts, *, priority=False):
    with _SCANNER_REST_QUOTE_FALLBACK_LOCK:
        state = _SCANNER_REST_QUOTE_FALLBACK_STATE
        cooldown_until = _safe_float(state.get("cooldown_until"), 0.0)
        if now_ts < cooldown_until:
            return False, "rest_quote_rate_limited_cooldown"
        window_start = now_ts - _SCANNER_REST_QUOTE_FALLBACK_WINDOW_SEC
        call_epochs = [
            _safe_float(epoch, 0.0)
            for epoch in (state.get("call_epochs") or [])
            if _safe_float(epoch, 0.0) >= window_start
        ]
        limit = _scanner_rest_quote_fallback_max_calls_per_window()
        if priority:
            limit += _scanner_rest_quote_fallback_positive_reserve_calls()
        dynamic_extra = _scanner_rest_quote_dynamic_extra_calls_locked(state, now_ts)
        limit += dynamic_extra
        if len(call_epochs) >= limit:
            _scanner_rest_quote_note_dynamic_pressure_locked(state, now_ts)
            boosted_extra = _scanner_rest_quote_dynamic_extra_calls_locked(
                state,
                now_ts,
                force_recalculate=True,
            )
            boosted_limit = (
                _scanner_rest_quote_fallback_max_calls_per_window()
                + (
                    _scanner_rest_quote_fallback_positive_reserve_calls()
                    if priority
                    else 0
                )
                + boosted_extra
            )
            if boosted_limit > limit and len(call_epochs) < boosted_limit:
                call_epochs.append(now_ts)
                state["call_epochs"] = call_epochs
                return True, "rest_quote_allowed_dynamic_boost"
            state["call_epochs"] = call_epochs
            return False, "rest_quote_rate_limited"
        call_epochs.append(now_ts)
        state["call_epochs"] = call_epochs
        if dynamic_extra > 0:
            return True, "rest_quote_allowed_dynamic_boost"
        return True, "rest_quote_allowed"


def _scanner_rest_quote_note_dynamic_pressure_locked(state, now_ts):
    window_start = now_ts - _SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_PRESSURE_WINDOW_SEC
    pressure_epochs = [
        _safe_float(epoch, 0.0)
        for epoch in (state.get("rate_limited_epochs") or [])
        if _safe_float(epoch, 0.0) >= window_start
    ]
    pressure_epochs.append(float(now_ts))
    state["rate_limited_epochs"] = pressure_epochs


def _scanner_rest_quote_dynamic_extra_calls_locked(
    state, now_ts, *, force_recalculate=False
):
    max_extra = _scanner_rest_quote_fallback_dynamic_max_extra_calls()
    if max_extra <= 0:
        state["dynamic_extra_calls"] = 0
        state["dynamic_boost_until"] = 0.0
        return 0
    boost_until = _safe_float(state.get("dynamic_boost_until"), 0.0)
    current_extra = max(
        0, min(_safe_int(state.get("dynamic_extra_calls"), 0), max_extra)
    )
    if not force_recalculate and current_extra > 0 and float(now_ts) < boost_until:
        return current_extra

    window_start = (
        float(now_ts) - _SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_PRESSURE_WINDOW_SEC
    )
    pressure_epochs = [
        _safe_float(epoch, 0.0)
        for epoch in (state.get("rate_limited_epochs") or [])
        if _safe_float(epoch, 0.0) >= window_start
    ]
    state["rate_limited_epochs"] = pressure_epochs
    pressure_count = len(pressure_epochs)
    if pressure_count >= 2:
        extra = max_extra
    elif pressure_count == 1:
        extra = min(1, max_extra)
    else:
        extra = 0
    state["dynamic_extra_calls"] = extra
    state["dynamic_boost_until"] = (
        float(now_ts) + _SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_BOOST_TTL_SEC
        if extra > 0
        else 0.0
    )
    return extra


def _scanner_rest_quote_fallback_max_calls_per_window():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS_PER_WINDOW"
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else _SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS
        )
    except Exception:
        value = _SCANNER_REST_QUOTE_FALLBACK_MAX_CALLS
    return max(0, min(value, 12))


def _scanner_rest_quote_fallback_positive_reserve_calls():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS"
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else _SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS
        )
    except Exception:
        value = _SCANNER_REST_QUOTE_FALLBACK_POSITIVE_RESERVE_CALLS
    return max(0, min(value, 6))


def _scanner_rest_quote_fallback_max_per_loop():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_MAX_PER_LOOP"
    )
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 6
    except Exception:
        value = 6
    return max(0, min(value, 24))


def _scanner_rest_quote_fallback_dynamic_max_extra_calls():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS"
    )
    try:
        value = (
            int(str(raw).strip())
            if str(raw).strip()
            else _SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS
        )
    except Exception:
        value = _SCANNER_REST_QUOTE_FALLBACK_DYNAMIC_MAX_EXTRA_CALLS
    return max(0, min(value, 8))


def _scanner_rest_quote_fallback_defer_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC"
    )
    try:
        value = (
            float(str(raw).strip())
            if str(raw).strip()
            else _SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC
        )
    except Exception:
        value = _SCANNER_REST_QUOTE_FALLBACK_DEFER_SEC
    return max(1.0, min(value, 30.0))


def _scanner_market_data_enrichment_enabled():
    return _env_bool("KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_ENABLED", True)


def _scanner_market_data_enrichment_cache_ttl_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_CACHE_TTL_SEC"
    )
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 1.5
    except Exception:
        value = 1.5
    return max(0.2, min(value, 5.0))


def _scanner_market_data_enrichment_hot_delta_pct():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_HOT_DELTA_PCT"
    )
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 2.0
    except Exception:
        value = 2.0
    return max(0.0, min(value, 20.0))


def _scanner_market_data_enrichment_rest_timeout_ms():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_MARKET_DATA_ENRICHMENT_REST_TIMEOUT_MS")
    try:
        value = int(float(str(raw).strip())) if str(raw or "").strip() else 400
    except (TypeError, ValueError):
        value = 400
    return max(50, min(value, 1500))


def _scanner_ws_quote_age_ms(ws_data, now_ts):
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    for key in ("quote_age_ms", "ws_age_ms", "pre_submit_effective_quote_age_ms"):
        value = ws_data.get(key)
        if value in (None, "", "-"):
            continue
        parsed = _safe_float(value, -1.0)
        if parsed >= 0:
            return float(parsed)
    for key in ("last_ws_update_ts", "received_at", "received_ts", "timestamp", "ts"):
        parsed = _safe_float(ws_data.get(key), 0.0)
        if parsed > 0:
            if parsed > 10_000_000_000:
                parsed = parsed / 1000.0
            return max(0.0, (float(now_ts) - parsed) * 1000.0)
    return None


def _scanner_snapshot_receive_ts(ws_data) -> float:
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    for key in ("last_ws_update_ts", "received_at", "received_ts", "timestamp", "ts"):
        received_ts = _safe_float(ws_data.get(key), 0.0)
        if received_ts <= 0:
            continue
        if received_ts > 10_000_000_000:
            received_ts = received_ts / 1000.0
        return float(received_ts)
    return 0.0


def _scanner_rest_recovery_receive_ts(ws_data) -> float:
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    for key in ("ws_snapshot_recovery_epoch", "rest_received_ts", "rest_received_at"):
        received_ts = _safe_float(ws_data.get(key), 0.0)
        if received_ts <= 0:
            continue
        if received_ts > 10_000_000_000:
            received_ts = received_ts / 1000.0
        return float(received_ts)
    return 0.0


def _discard_pre_revive_scanner_snapshot(stock, ws_data, *, now_ts: float):
    """Require a quote received after a scalp revive before scanner evaluation."""
    stock = stock if isinstance(stock, dict) else {}
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    min_quote_ts = _safe_float(stock.get("_scalp_revive_min_quote_ts"), 0.0)
    if min_quote_ts <= 0:
        return ws_data, {}

    received_ts = _scanner_snapshot_receive_ts(ws_data)
    if received_ts > min_quote_ts:
        stock.pop("_scalp_revive_min_quote_ts", None)
        return ws_data, {
            "scalp_revive_quote_barrier_applied": True,
            "scalp_revive_quote_barrier_state": "fresh_ws_after_revive",
            "scalp_revive_quote_barrier_min_ts": round(min_quote_ts, 3),
            "scalp_revive_quote_barrier_received_ts": round(received_ts, 3),
        }

    rest_received_ts = _scanner_rest_recovery_receive_ts(ws_data)
    if rest_received_ts > min_quote_ts:
        # A current REST recovery can repair the quote price but must not promote
        # itself to trusted WS micro provenance or clear the WS revival barrier.
        return ws_data, {
            "scalp_revive_quote_barrier_applied": True,
            "scalp_revive_quote_barrier_state": "fresh_rest_after_revive_ws_pending",
            "scalp_revive_quote_barrier_min_ts": round(min_quote_ts, 3),
            "scalp_revive_quote_barrier_received_ts": round(rest_received_ts, 3),
            "scalp_revive_quote_barrier_ws_pending": True,
        }

    return {}, {
        "scalp_revive_quote_barrier_applied": True,
        "scalp_revive_quote_barrier_state": "pre_revive_ws_discarded",
        "scalp_revive_quote_barrier_min_ts": round(min_quote_ts, 3),
        "scalp_revive_quote_barrier_received_ts": (
            round(received_ts, 3) if received_ts > 0 else "missing"
        ),
        "scalp_revive_quote_barrier_wait_sec": round(
            max(0.0, float(now_ts) - min_quote_ts), 3
        ),
    }


def _scanner_boolish_true(value):
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "on", "stale"}


def _scanner_market_data_enrichment_candidate(stock, ws_data, now_ts):
    if not _scanner_market_data_enrichment_enabled():
        return False
    if not _is_scanner_watching_target(stock):
        return False
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    hot_delta = (
        _scanner_positive_delta_value(stock)
        >= _scanner_market_data_enrichment_hot_delta_pct()
    )
    rising_source_marker = sniper_state_handlers._has_rising_missed_watch_source_marker(
        stock
    )
    existing_enrichment_scope = bool(
        _scanner_is_rising_entry_relief_candidate(stock)
        or rising_source_marker
        or hot_delta
    )
    opening_rotation_handoff_allowed = False
    if not existing_enrichment_scope:
        opening_rotation_handoff_allowed = bool(
            sniper_state_handlers._opening_rotation_upstream_handoff_fields(
                stock,
                ws_data,
                now_ts=float(now_ts),
            ).get("opening_rotation_upstream_handoff_allowed")
        )
    if not (existing_enrichment_scope or opening_rotation_handoff_allowed):
        return False
    curr = _safe_int(ws_data.get("curr"), 0)
    quote_age_ms = _scanner_ws_quote_age_ms(ws_data, now_ts)
    stale_or_missing = (
        curr <= 0
        or quote_age_ms is None
        or quote_age_ms > 3000.0
        or str(ws_data.get("quote_state") or "").strip().lower() in {"stale", "missing"}
        or any(
            _scanner_boolish_true(ws_data.get(key))
            for key in ("quote_stale", "stale_quote", "context_stale")
        )
    )
    return bool(stale_or_missing or hot_delta)


def _scanner_market_data_enrichment_cached(code, now_ts):
    norm_code = str(code or "").strip()[:6]
    if not norm_code:
        return None
    with _SCANNER_MARKET_DATA_ENRICHMENT_LOCK:
        cached = _SCANNER_MARKET_DATA_ENRICHMENT_CACHE.get(norm_code)
        if not isinstance(cached, dict):
            return None
        if float(now_ts) > _safe_float(cached.get("expires_at"), 0.0):
            _SCANNER_MARKET_DATA_ENRICHMENT_CACHE.pop(norm_code, None)
            return None
        return dict(cached)


def _scanner_market_data_enrichment_store(
    code, now_ts, rest_orderbook, rest_signed_ticks
):
    norm_code = str(code or "").strip()[:6]
    if not norm_code:
        return
    ttl = _scanner_market_data_enrichment_cache_ttl_sec()
    with _SCANNER_MARKET_DATA_ENRICHMENT_LOCK:
        _SCANNER_MARKET_DATA_ENRICHMENT_CACHE[norm_code] = {
            "expires_at": float(now_ts) + ttl,
            "rest_orderbook": dict(rest_orderbook or {}),
            "rest_signed_ticks": list(rest_signed_ticks or []),
        }


def _fetch_scanner_market_data_enrichment_packet(code, now_ts):
    if not KIWOOM_TOKEN:
        return {}, [], {"market_data_enrichment_fetch_reason": "kiwoom_token_missing"}
    rest_orderbook = {}
    rest_signed_ticks = []
    timeout_ms = _scanner_market_data_enrichment_rest_timeout_ms()
    fields = {
        "market_data_enrichment_fetch_reason": "fetch_attempted",
        "market_data_enrichment_rest_timeout_ms": timeout_ms,
    }
    rest_orderbook, orderbook_state, orderbook_elapsed_ms = (
        sniper_state_handlers._fetch_rest_orderbook_snapshot_bounded(code, timeout_ms)
    )
    fields["market_data_enrichment_orderbook_fetch_state"] = orderbook_state
    fields["market_data_enrichment_orderbook_fetch_elapsed_ms"] = round(
        orderbook_elapsed_ms,
        3,
    )
    if rest_orderbook:
        rest_signed_ticks, signed_tape_state, signed_tape_elapsed_ms = (
            sniper_state_handlers._fetch_rising_missed_signed_tape_bounded(
                code, timeout_ms
            )
        )
    else:
        signed_tape_state = "skipped_orderbook_unavailable"
        signed_tape_elapsed_ms = 0.0
    fields["market_data_enrichment_signed_tape_fetch_state"] = signed_tape_state
    fields["market_data_enrichment_signed_tape_fetch_elapsed_ms"] = round(
        signed_tape_elapsed_ms,
        3,
    )
    if rest_orderbook or rest_signed_ticks:
        _scanner_market_data_enrichment_store(
            code, now_ts, rest_orderbook, rest_signed_ticks
        )
        fields["market_data_enrichment_fetch_reason"] = "rest_packet_fetched"
    elif orderbook_state == "timeout":
        fields["market_data_enrichment_fetch_reason"] = "rest_packet_timeout"
    else:
        fields["market_data_enrichment_fetch_reason"] = "rest_packet_unavailable"
    return rest_orderbook, rest_signed_ticks, fields


def _scanner_ws_repair_cycle_wait_sec():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_WAIT_SEC")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 10.0
    except Exception:
        value = 10.0
    return max(5.0, min(value, 120.0))


def _scanner_ws_repair_cycle_persistent_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_WS_REPAIR_CYCLE_PERSISTENT_SEC"
    )
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 30.0
    except Exception:
        value = 30.0
    return max(10.0, min(value, 300.0))


def _scanner_ws_persistent_repair_min_interval_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_WS_PERSISTENT_REPAIR_MIN_INTERVAL_SEC"
    )
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 20.0
    except Exception:
        value = 20.0
    return max(5.0, min(value, 300.0))


def _scanner_ws_subscription_recheck_fresh_sec():
    raw = _scanner_hot_or_env_value(
        "KORSTOCKSCAN_SCANNER_WS_SUBSCRIPTION_RECHECK_FRESH_SEC"
    )
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 30.0
    except Exception:
        value = 30.0
    return max(3.0, min(value, 120.0))


def _scanner_heavy_eval_recheck_fresh_sec():
    raw = _scanner_hot_or_env_value("KORSTOCKSCAN_SCANNER_HEAVY_EVAL_RECHECK_FRESH_SEC")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 3.0
    except Exception:
        value = 3.0
    return max(1.0, min(value, 20.0))


def _scanner_normalize_ws_snapshot_for_entry_eval(snapshot, *, now_ts):
    normalized = dict(snapshot or {}) if isinstance(snapshot, dict) else {}
    fields = {
        "ws_subscription_recheck_entry_timestamp_normalized": False,
        "ws_subscription_recheck_entry_timestamp_source": "last_ws_update_ts",
        "ws_subscription_recheck_entry_input_age_sec": "not_available_ws_age_sec",
        "ws_subscription_recheck_entry_normalized_age_sec": "not_available_ws_age_sec",
    }
    if not normalized:
        fields["ws_subscription_recheck_entry_timestamp_source"] = "missing_snapshot"
        return normalized, fields
    if _safe_int(normalized.get("curr"), 0) <= 0:
        fields["ws_subscription_recheck_entry_timestamp_source"] = (
            "missing_or_zero_curr"
        )
        return normalized, fields

    base_ts = _safe_float(normalized.get("last_ws_update_ts"), 0.0)
    if base_ts > 0:
        fields["ws_subscription_recheck_entry_input_age_sec"] = round(
            max(0.0, float(now_ts) - base_ts),
            3,
        )
        fields["ws_subscription_recheck_entry_normalized_age_sec"] = round(
            max(0.0, float(now_ts) - base_ts),
            3,
        )
    existing_source = str(
        normalized.get("entry_eval_last_ws_update_ts_normalized_from") or ""
    ).strip()
    if existing_source:
        fields["ws_subscription_recheck_entry_timestamp_normalized"] = True
        fields["ws_subscription_recheck_entry_timestamp_source"] = existing_source
        return normalized, fields
    candidates: list[tuple[str, float]] = []
    type_ts = normalized.get("last_realtime_type_ts")
    if isinstance(type_ts, dict):
        tick_ts = _safe_float(type_ts.get("0B"), 0.0)
        if tick_ts > 0:
            candidates.append(("last_realtime_type_ts_0B", tick_ts))
    last_trade = normalized.get("last_trade_tick")
    if isinstance(last_trade, dict):
        trade_ts = _safe_float(last_trade.get("ts"), 0.0)
        if trade_ts > 0:
            candidates.append(("last_trade_tick", trade_ts))
    history = normalized.get("strength_momentum_history") or []
    try:
        latest_history = history[-1] if history else None
    except Exception:
        latest_history = None
    if isinstance(latest_history, dict):
        history_ts = _safe_float(latest_history.get("ts"), 0.0)
        if history_ts > 0:
            candidates.append(("strength_momentum_history", history_ts))

    if not candidates:
        return normalized, fields
    source, candidate_ts = max(candidates, key=lambda item: item[1])
    if candidate_ts <= 0 or candidate_ts > float(now_ts) + 1.0:
        return normalized, fields
    if base_ts > 0 and candidate_ts <= base_ts:
        return normalized, fields

    normalized["last_ws_update_ts"] = candidate_ts
    normalized["entry_eval_last_ws_update_ts_normalized_from"] = source
    fields["ws_subscription_recheck_entry_timestamp_normalized"] = True
    fields["ws_subscription_recheck_entry_timestamp_source"] = source
    fields["ws_subscription_recheck_entry_normalized_age_sec"] = round(
        max(0.0, float(now_ts) - candidate_ts),
        3,
    )
    return normalized, fields


def _scanner_ws_snapshot_entry_realtime_fresh(snapshot, *, now_ts, fresh_sec):
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    fresh_sec = _safe_float(fresh_sec, 0.0)
    if not snapshot or fresh_sec <= 0 or _safe_int(snapshot.get("curr"), 0) <= 0:
        return False, "missing_entry_snapshot"

    candidates = []
    type_ts = snapshot.get("last_realtime_type_ts")
    if isinstance(type_ts, dict):
        tick_ts = _safe_float(type_ts.get("0B"), 0.0)
        if tick_ts > 0:
            candidates.append(("last_realtime_type_ts_0B", tick_ts))

    last_trade = snapshot.get("last_trade_tick")
    if isinstance(last_trade, dict):
        trade_ts = _safe_float(last_trade.get("ts"), 0.0)
        if trade_ts > 0:
            candidates.append(("last_trade_tick", trade_ts))

    history = snapshot.get("strength_momentum_history") or []
    try:
        latest_history = history[-1] if history else None
    except Exception:
        latest_history = None
    if isinstance(latest_history, dict):
        history_ts = _safe_float(
            latest_history.get("ts") or latest_history.get("timestamp"), 0.0
        )
        if history_ts > 0:
            candidates.append(("strength_momentum_history", history_ts))

    if candidates:
        source, latest_ts = max(candidates, key=lambda item: item[1])
        age_sec = max(0.0, float(now_ts) - latest_ts)
        return age_sec <= fresh_sec, source
    if isinstance(type_ts, dict) and type_ts:
        return False, "missing_fresh_0B_or_strength_history"

    received = snapshot.get("received_types") or []
    try:
        received_types = {str(item) for item in received if str(item).strip()}
    except Exception:
        received_types = set()
    base_ts = _safe_float(snapshot.get("last_ws_update_ts"), 0.0)
    if "0B" in received_types and base_ts > 0:
        age_sec = max(0.0, float(now_ts) - base_ts)
        return age_sec <= fresh_sec, "last_ws_update_ts_with_0B"
    return False, "missing_fresh_0B_or_strength_history"


def _scanner_ws_subscription_recheck_snapshot_and_fields(
    manager, code, ws_data, *, now_ts
):
    norm_code = str(code or "").strip()[:6]
    snapshot = dict(ws_data or {}) if isinstance(ws_data, dict) else {}
    subscribed = False
    manager_available = manager is not None
    if manager is not None:
        try:
            subscribed = norm_code in set(
                getattr(manager, "subscribed_codes", set()) or set()
            )
        except Exception:
            subscribed = False
        if hasattr(manager, "get_latest_data"):
            try:
                latest_snapshot = manager.get_latest_data(norm_code) or {}
            except Exception:
                latest_snapshot = {}
            latest_snapshot = (
                dict(latest_snapshot or {}) if isinstance(latest_snapshot, dict) else {}
            )
            latest_snapshot, _latest_entry_timestamp_fields = (
                _scanner_normalize_ws_snapshot_for_entry_eval(
                    latest_snapshot,
                    now_ts=now_ts,
                )
            )
            latest_ts = _safe_float(latest_snapshot.get("last_ws_update_ts"), 0.0)
            snapshot_ts = _safe_float(snapshot.get("last_ws_update_ts"), 0.0)
            latest_curr = _safe_int(latest_snapshot.get("curr"), 0)
            snapshot_curr = _safe_int(snapshot.get("curr"), 0)
            if latest_snapshot and (
                snapshot_curr <= 0 or latest_curr > 0 and latest_ts >= snapshot_ts
            ):
                snapshot = latest_snapshot
    snapshot, entry_timestamp_fields = _scanner_normalize_ws_snapshot_for_entry_eval(
        snapshot,
        now_ts=now_ts,
    )
    curr = _safe_int(snapshot.get("curr"), 0)
    last_ts = _safe_float(snapshot.get("last_ws_update_ts"), 0.0)
    age_sec = max(0.0, float(now_ts) - last_ts) if last_ts > 0 else None
    received = snapshot.get("received_types") or []
    try:
        received_types = sorted(str(item) for item in received if str(item).strip())
    except Exception:
        received_types = []
    snapshot_present = bool(snapshot)
    fresh_sec = _scanner_ws_subscription_recheck_fresh_sec()
    fresh_curr = curr > 0 and age_sec is not None and age_sec <= fresh_sec
    entry_realtime_fresh, entry_realtime_source = (
        _scanner_ws_snapshot_entry_realtime_fresh(
            snapshot,
            now_ts=now_ts,
            fresh_sec=fresh_sec,
        )
    )
    repair_needed = not (subscribed and fresh_curr and entry_realtime_fresh)
    fields = {
        "ws_subscription_recheck_status": (
            "subscribed_fresh_snapshot"
            if subscribed and fresh_curr and entry_realtime_fresh
            else (
                "subscribed_snapshot_stale_or_missing"
                if subscribed
                else "not_subscribed"
            )
        ),
        "ws_subscription_recheck_manager_available": bool(manager_available),
        "ws_subscription_recheck_subscribed": bool(subscribed),
        "ws_subscription_recheck_snapshot_present": bool(snapshot_present),
        "ws_subscription_recheck_curr": curr if curr > 0 else "not_applicable_ws_curr",
        "ws_subscription_recheck_age_sec": (
            round(age_sec, 3) if age_sec is not None else "not_available_ws_age_sec"
        ),
        "ws_subscription_recheck_fresh_sec": round(fresh_sec, 3),
        "ws_subscription_recheck_received_types": (
            ",".join(received_types) if received_types else "-"
        ),
        "ws_subscription_recheck_entry_realtime_fresh": bool(entry_realtime_fresh),
        "ws_subscription_recheck_entry_realtime_source": entry_realtime_source,
        "ws_subscription_repair_needed": bool(repair_needed),
        **entry_timestamp_fields,
    }
    return snapshot, fields


def _scanner_ws_subscription_recheck_fields(manager, code, ws_data, *, now_ts):
    _snapshot, fields = _scanner_ws_subscription_recheck_snapshot_and_fields(
        manager,
        code,
        ws_data,
        now_ts=now_ts,
    )
    return fields


def _scanner_rest_quote_entry_realtime_outcome_fields(recovery_fields):
    fields = dict(recovery_fields or {})
    if fields.get("ws_recovery_outcome") == "rest_quote_applied" and bool(
        fields.get("ws_subscription_repair_needed")
    ):
        fields["ws_recovery_outcome"] = "rest_quote_applied_entry_realtime_still_stale"
        fields["rest_quote_price_recovery_only"] = True
        fields["entry_evaluable_fresh_after_rest_quote"] = False
    return fields


def _scanner_rest_quote_fallback_due(stock, now_ts, *, allow_early_rest_fallback):
    if not allow_early_rest_fallback:
        return False
    state = (stock or {}).get("_scanner_ws_snapshot_recovery")
    state = state if isinstance(state, dict) else {}
    next_after_ts = _safe_float(state.get("next_fallback_after_ts"), 0.0)
    if next_after_ts > 0 and float(now_ts) < next_after_ts:
        return False
    last_fallback_ts = _safe_float(state.get("last_fallback_ts"), 0.0)
    return float(now_ts) - last_fallback_ts >= 10


def _scanner_rest_quote_mark_deferred(stock, now_ts, *, reason, defer_sec=None):
    state = (
        stock.setdefault("_scanner_ws_snapshot_recovery", {})
        if isinstance(stock, dict)
        else {}
    )
    if not isinstance(state, dict):
        state = {}
        if isinstance(stock, dict):
            stock["_scanner_ws_snapshot_recovery"] = state
    delay = (
        _scanner_rest_quote_fallback_defer_sec()
        if defer_sec is None
        else max(1.0, float(defer_sec))
    )
    next_after_ts = float(now_ts) + delay
    state["last_fallback_outcome"] = str(reason or "rest_quote_deferred")
    state["next_fallback_after_ts"] = next_after_ts
    return {
        "ws_recovery_action": "ws_reg_reissued_rest_quote_fallback",
        "ws_recovery_outcome": str(reason or "rest_quote_deferred"),
        "ws_gap_recovery_deferred_priority": True,
        "rest_quote_fallback_deferred_reason": str(reason or "rest_quote_deferred"),
        "rest_quote_fallback_next_after_epoch": f"{next_after_ts:.3f}",
        "rest_quote_fallback_defer_sec": round(delay, 3),
    }


def _scanner_rest_quote_fallback_note_result(now_ts, *, applied, transport_error=False):
    if applied or not transport_error:
        return
    with _SCANNER_REST_QUOTE_FALLBACK_LOCK:
        state = _SCANNER_REST_QUOTE_FALLBACK_STATE
        state["cooldown_until"] = max(
            _safe_float(state.get("cooldown_until"), 0.0),
            now_ts + _SCANNER_REST_QUOTE_FALLBACK_FAILURE_COOLDOWN_SEC,
        )


def _reset_scanner_rest_quote_fallback_rate_limit_for_tests():
    with _SCANNER_REST_QUOTE_FALLBACK_LOCK:
        _SCANNER_REST_QUOTE_FALLBACK_STATE["call_epochs"] = []
        _SCANNER_REST_QUOTE_FALLBACK_STATE["cooldown_until"] = 0.0
        _SCANNER_REST_QUOTE_FALLBACK_STATE["rate_limited_epochs"] = []
        _SCANNER_REST_QUOTE_FALLBACK_STATE["dynamic_extra_calls"] = 0
        _SCANNER_REST_QUOTE_FALLBACK_STATE["dynamic_boost_until"] = 0.0
    with _SCANNER_MARKET_DATA_ENRICHMENT_LOCK:
        _SCANNER_MARKET_DATA_ENRICHMENT_CACHE.clear()


def _fetch_rest_quote_snapshot_for_ws_gap(code, now_ts):
    if not KIWOOM_TOKEN:
        return {}
    try:
        url = kiwoom_utils.get_api_url("/api/dostk/stkinfo")
        rows = kiwoom_utils.fetch_kiwoom_api_continuous(
            url,
            KIWOOM_TOKEN,
            "ka10001",
            {"stk_cd": code},
            max_retries=1,
            use_continuous=False,
        )
    except Exception as exc:
        log_error(f"[SCANNER_WS_RECOVERY] quote fallback failed ({code}): {exc}")
        _scanner_rest_quote_fallback_note_result(
            now_ts, applied=False, transport_error=True
        )
        return {}
    if not rows:
        return {}
    row = rows[0] if isinstance(rows[0], dict) else {}
    curr = 0
    for key in ("cur_prc", "curr_price", "price", "stck_prpr", "trade_price"):
        curr = _parse_quote_price(row.get(key))
        if curr > 0:
            break
    if curr <= 0:
        return {}
    return {
        "curr": curr,
        "ws_snapshot_recovery_source": "ka10001_rest_quote_fallback",
        "ws_snapshot_recovery_epoch": now_ts,
        "ws_snapshot_recovery_runtime_effect": False,
    }


def _scanner_ws_gap_early_rest_fallback_allowed(stock):
    """Allow quote-only REST recovery earlier for scanner rows already proving upside."""
    return _scanner_rest_quote_fallback_allowed_for_ws_gap(stock)


def _scanner_rest_quote_fallback_allowed_for_ws_gap(stock):
    if not _scanner_rising_ws_gap_priority_recovery_enabled():
        return False
    if not _is_scanner_watching_target(stock):
        return False
    return _scanner_is_rising_entry_relief_candidate(stock)


def _recover_missing_ws_snapshot(
    stock,
    code,
    now_ts,
    ws_data,
    *,
    ws_reg_source="scanner_watching_ws_snapshot_recovery",
    publish_ws_reg=True,
    allow_early_rest_fallback=False,
    rest_quote_deferred_reason="",
    cycle_state_store=None,
):
    norm_code = str(code or "").strip()[:6]
    if isinstance(cycle_state_store, dict) and norm_code:
        state = cycle_state_store.setdefault(norm_code, {})
        if not isinstance(state, dict):
            state = {}
            cycle_state_store[norm_code] = state
        if isinstance(stock, dict):
            stock["_scanner_ws_snapshot_recovery"] = state
    else:
        state = stock.setdefault("_scanner_ws_snapshot_recovery", {})
        if not isinstance(state, dict):
            state = {}
            stock["_scanner_ws_snapshot_recovery"] = state
    cycle_id = str(state.get("repair_cycle_id") or "").strip()
    if not cycle_id:
        cycle_id = f"{str(code or '').strip()[:6]}:{int(float(now_ts) * 1000)}"
        state["repair_cycle_id"] = cycle_id
        state["repair_cycle_started_ts"] = float(now_ts)
    cycle_started_ts = _safe_float(state.get("repair_cycle_started_ts"), float(now_ts))
    cycle_wait_sec = _scanner_ws_repair_cycle_wait_sec()
    persistent_sec = _scanner_ws_repair_cycle_persistent_sec()
    last_ws_reg_ts = _safe_float(state.get("last_ws_reg_ts"), 0.0)
    persistent_gap = float(now_ts) - cycle_started_ts >= persistent_sec
    cycle_reg_allowed = (not persistent_gap) and (
        last_ws_reg_ts <= 0 or float(now_ts) - last_ws_reg_ts >= cycle_wait_sec
    )
    cycle_state = (
        "ws_reg_reissued_waiting_snapshot"
        if cycle_reg_allowed
        else "ws_repair_cycle_waiting_snapshot"
    )
    if persistent_gap:
        cycle_state = "persistent_ws_gap"
    if cycle_reg_allowed:
        state["last_ws_reg_ts"] = float(now_ts)
        state["repair_cycle_attempt_count"] = (
            _safe_int(state.get("repair_cycle_attempt_count"), 0) + 1
        )
        if publish_ws_reg:
            event_bus.publish(
                "COMMAND_WS_REG", {"codes": [code], "source": ws_reg_source}
            )
    miss_count = int(state.get("miss_count") or 0) + 1
    last_fallback_ts = _safe_float(state.get("last_fallback_ts"), 0.0)
    state["miss_count"] = miss_count

    recovery_fields = {
        "ws_recovery_action": (
            "ws_reg_reissued" if cycle_reg_allowed else "ws_repair_cycle_wait"
        ),
        "ws_recovery_miss_count": miss_count,
        "ws_recovery_outcome": cycle_state,
        "ws_subscription_repair_required": cycle_state == "persistent_ws_gap",
        "rest_quote_fallback_eligible": bool(allow_early_rest_fallback),
        "ws_repair_cycle_id": cycle_id,
        "ws_repair_cycle_state": cycle_state,
        "ws_repair_cycle_attempt_count": _safe_int(
            state.get("repair_cycle_attempt_count"), 0
        ),
        "ws_repair_cycle_wait_sec": round(cycle_wait_sec, 3),
        "ws_repair_cycle_age_sec": round(max(0.0, float(now_ts) - cycle_started_ts), 3),
        "ws_repair_cycle_reg_allowed": bool(cycle_reg_allowed),
        "ws_repair_cycle_suppressed_duplicate_reg": not bool(cycle_reg_allowed),
        "ws_repair_batch_required": bool(persistent_gap),
        "ws_repair_cycle_next_reg_after_epoch": (
            f"{float(last_ws_reg_ts + cycle_wait_sec):.3f}"
            if last_ws_reg_ts > 0 and not cycle_reg_allowed
            else "not_applicable_next_reg_after_epoch"
        ),
    }
    fallback_due = _scanner_rest_quote_fallback_due(
        stock,
        now_ts,
        allow_early_rest_fallback=bool(allow_early_rest_fallback),
    )
    if fallback_due and now_ts - last_fallback_ts >= 10:
        if rest_quote_deferred_reason:
            recovery_fields.update(
                _scanner_rest_quote_mark_deferred(
                    stock,
                    now_ts,
                    reason=rest_quote_deferred_reason,
                )
            )
            _scanner_set_rising_recheck(
                stock,
                kind="ws_gap_priority",
                after_epoch=_safe_float(
                    recovery_fields.get("rest_quote_fallback_next_after_epoch"),
                    now_ts + 5,
                ),
                reason="ws_gap_recovery_deferred_priority",
            )
            if miss_count >= 3:
                recovery_fields["ws_subscription_repair_required"] = True
            return ws_data or {}, recovery_fields
        allowed, rate_reason = _scanner_rest_quote_fallback_rate_limit(
            now_ts,
            priority=True,
        )
        recovery_fields["rest_quote_rate_limit_decision"] = rate_reason
        recovery_fields["rest_quote_dynamic_budget_boosted"] = (
            rate_reason == "rest_quote_allowed_dynamic_boost"
        )
        if not allowed:
            recovery_fields.update(
                _scanner_rest_quote_mark_deferred(
                    stock,
                    now_ts,
                    reason=rate_reason,
                    defer_sec=max(10.0, _scanner_rest_quote_fallback_defer_sec()),
                )
            )
            if bool(allow_early_rest_fallback):
                _scanner_set_rising_recheck(
                    stock,
                    kind="ws_gap_priority",
                    after_epoch=_safe_float(
                        recovery_fields.get("rest_quote_fallback_next_after_epoch"),
                        now_ts + 10,
                    ),
                    reason="ws_gap_recovery_deferred_priority",
                )
            if miss_count >= 3:
                recovery_fields["ws_subscription_repair_required"] = True
            return ws_data or {}, recovery_fields
        state["last_fallback_ts"] = now_ts
        fallback = _fetch_rest_quote_snapshot_for_ws_gap(code, now_ts)
        if fallback:
            _scanner_rest_quote_fallback_note_result(
                now_ts, applied=True, transport_error=False
            )
            state["last_fallback_outcome"] = "rest_quote_applied"
            recovery_fields["ws_recovery_action"] = (
                "ws_reg_reissued_rest_quote_fallback"
            )
            recovery_fields["ws_recovery_outcome"] = "rest_quote_applied"
            return fallback, recovery_fields
        state["last_fallback_outcome"] = "rest_quote_unavailable"
        recovery_fields["ws_recovery_action"] = "ws_reg_reissued_rest_quote_fallback"
        recovery_fields["ws_recovery_outcome"] = "rest_quote_unavailable"
    if miss_count >= 3:
        recovery_fields["ws_subscription_repair_required"] = True
    if (
        recovery_fields.get("ws_subscription_repair_required")
        and cycle_state != "persistent_ws_gap"
    ):
        recovery_fields.setdefault("persistent_ws_gap_pending_cycle", True)
    return ws_data or {}, recovery_fields


def _scanner_runtime_context_updates(payload):
    payload = payload or {}
    updates = {}
    for key in (
        "current_price_observed",
        "price_delta_since_first_seen_pct",
        "comparable_flu_delta_since_first_seen",
        "cntr_str_available",
        "cntr_str",
        "rising_missed_lineage",
        "low_rebound_pct",
        "intraday_low_price",
        "intraday_high_price",
        "distance_from_intraday_high_pct",
        "negative_display_rebound",
        "scanner_watch_budget_owner",
        "scanner_watch_budget_owner_source",
    ):
        value = payload.get(key)
        if value not in (None, ""):
            updates[key] = value
    return updates


def _scanner_merge_context_preserving_positive_delta(existing, updates):
    updates = dict(updates or {})
    if not isinstance(existing, dict):
        return updates, {}
    delta_keys = (
        "price_delta_since_first_seen_pct",
        "comparable_flu_delta_since_first_seen",
    )
    if not any(key in updates for key in delta_keys):
        return updates, {}

    existing_delta = max(_safe_float(existing.get(key), 0.0) for key in delta_keys)
    incoming_delta = max(_safe_float(updates.get(key), 0.0) for key in delta_keys)
    if existing_delta <= 0.0 or existing_delta <= incoming_delta:
        return updates, {}

    for key in delta_keys:
        existing_value = existing.get(key)
        if existing_value in (None, ""):
            continue
        if _safe_float(existing_value, 0.0) > _safe_float(updates.get(key), 0.0):
            updates[key] = existing_value
    return updates, {
        "scanner_positive_delta_context_preserved": True,
        "scanner_positive_delta_context_previous_pct": f"{existing_delta:.2f}",
        "scanner_positive_delta_context_incoming_pct": f"{incoming_delta:.2f}",
    }


def _scanner_pipeline_stock_snapshot(stock_value):
    if not isinstance(stock_value, dict):
        return {}
    return {
        key: stock_value.get(key)
        for key in (
            "id",
            "name",
            "strategy",
            "position_tag",
            "scanner_promotion_id",
            "scanner_promotion_reason",
            "scanner_promotion_emitted_epoch",
            "source_signature",
            "entry_armed_at_epoch",
            "added_time",
            "current_price_observed",
            "price_delta_since_first_seen_pct",
            "comparable_flu_delta_since_first_seen",
            "cntr_str_available",
            "cntr_str",
            "rising_missed_lineage",
            "low_rebound_pct",
            "intraday_low_price",
            "intraday_high_price",
            "distance_from_intraday_high_pct",
            "negative_display_rebound",
            "_scanner_rising_entry_relief_eligible",
            "_scanner_rising_entry_relief_reason",
            "_scanner_positive_delta_pct",
            "_scanner_full_eval_budget_source",
            "_scanner_rising_cooldown_recheck_after_epoch",
            "_scanner_rising_cutoff_recheck_after_epoch",
            "_scanner_rising_freshness_envelope_recheck_until_epoch",
            "_scanner_rising_latency_direct_recheck_after_epoch",
            "_scanner_rising_reversal_up_volatile_recheck_until_epoch",
            "_scanner_rising_reversal_up_watch_recheck_until_epoch",
            "_scanner_rising_ws_gap_priority_recheck_after_epoch",
            "_scanner_rising_terminal_hardgate_recheck_after_epoch",
            "_scanner_rising_recheck_reason",
        )
    }


def handle_scalping_scanner_promoted_target(payload):
    """Attach scanner-promoted WATCHING records to the live loop without changing buy thresholds."""
    global ACTIVE_TARGETS

    payload = payload or {}
    code = normalize_manual_control_exclusion_code(payload.get("code"))
    if not code:
        _log_scanner_runtime_target_attach(
            payload, outcome="skipped", reason="missing_code"
        )
        return False

    strategy = normalize_strategy(payload.get("strategy") or "SCALPING")
    if strategy != "SCALPING":
        _log_scanner_runtime_target_attach(
            payload, outcome="skipped", reason="non_scalping_strategy"
        )
        return False

    control_exclusion = evaluate_manual_control_exclusion(code)
    if control_exclusion.excluded:
        _log_scanner_runtime_target_attach(
            {**payload, **control_exclusion.as_log_fields()},
            outcome="skipped",
            reason=control_exclusion.reason,
        )
        log_info(
            f"[MANUAL_CONTROL_EXCLUSION] scanner WATCHING attach skipped "
            f"{payload.get('name') or code}({control_exclusion.code}) source={control_exclusion.source}"
        )
        return False

    now_ts = _safe_float(payload.get("added_time"), time.time())
    promotion_anchor_ts = _scanner_promotion_anchor_time(payload, now_ts)
    buy_price = _safe_int(
        payload.get("buy_price") or payload.get("current_price_observed"), 0
    )
    position_tag = normalize_position_tag(
        strategy, payload.get("position_tag") or "SCANNER"
    )
    record_id = _resolve_scanner_runtime_record_id(payload, code, strategy)
    scanner_context_updates = _scanner_runtime_context_updates(payload)
    identity_ok, identity_fields = _scanner_identity_guard(payload, code, buy_price)
    payload_for_log = {**payload, **identity_fields}
    if not identity_ok:
        identity_reason = (
            identity_fields.get("scanner_identity_guard_reason")
            or "scanner_identity_mismatch"
        )
        expired = _expire_scanner_identity_mismatch_record(
            payload_for_log, code, identity_reason
        )
        _log_scanner_runtime_target_attach(
            {**payload_for_log, "scanner_identity_mismatch_expired": expired},
            outcome="skipped",
            reason=identity_reason,
        )
        return False

    with _state_lock:
        existing = None
        for target in ACTIVE_TARGETS:
            if (
                str(target.get("code") or "").strip()[:6] == code
                and normalize_strategy(target.get("strategy")) == strategy
            ):
                existing = target
                break

        if existing is not None:
            status = str(existing.get("status") or "").upper()
            if status == "WATCHING":
                refresh_context_updates, refresh_context_fields = (
                    _scanner_merge_context_preserving_positive_delta(
                        existing, scanner_context_updates
                    )
                )
                positive_context_preserved = bool(
                    refresh_context_fields.get(
                        "scanner_positive_delta_context_preserved"
                    )
                )
                refresh_added_time = (
                    existing.get("added_time")
                    if positive_context_preserved
                    and existing.get("added_time") not in (None, "")
                    else now_ts
                )
                refresh_anchor_ts = (
                    existing.get("entry_armed_at_epoch")
                    if positive_context_preserved
                    and existing.get("entry_armed_at_epoch") not in (None, "")
                    else promotion_anchor_ts
                )
                refresh_promotion_id = (
                    existing.get("scanner_promotion_id")
                    if positive_context_preserved
                    and existing.get("scanner_promotion_id")
                    else payload.get("scanner_promotion_id")
                    or existing.get("scanner_promotion_id")
                )
                refresh_promotion_reason = (
                    existing.get("scanner_promotion_reason")
                    if positive_context_preserved
                    and existing.get("scanner_promotion_reason")
                    else payload.get("scanner_promotion_reason")
                    or existing.get("scanner_promotion_reason")
                )
                refresh_promotion_epoch = (
                    existing.get("scanner_promotion_emitted_epoch")
                    if positive_context_preserved
                    and existing.get("scanner_promotion_emitted_epoch")
                    else payload.get("scanner_promotion_emitted_epoch")
                    or existing.get("scanner_promotion_emitted_epoch")
                )
                refresh_source_signature = (
                    existing.get("source_signature")
                    if positive_context_preserved and existing.get("source_signature")
                    else payload.get("source_signature")
                    or existing.get("source_signature")
                )
                existing.update(
                    {
                        "id": record_id or existing.get("id"),
                        "name": payload.get("name") or existing.get("name"),
                        "buy_price": buy_price or existing.get("buy_price"),
                        "added_time": refresh_added_time,
                        "entry_armed_at_epoch": refresh_anchor_ts,
                        "position_tag": position_tag,
                        "scanner_promotion_id": refresh_promotion_id,
                        "scanner_promotion_reason": refresh_promotion_reason,
                        "scanner_promotion_emitted_epoch": refresh_promotion_epoch,
                        "source_signature": refresh_source_signature,
                        **refresh_context_updates,
                    }
                )
                refresh_overflow = _scalping_watch_budget_overflow_candidates(
                    ACTIVE_TARGETS, now_ts
                )
                if refresh_overflow:
                    _expire_scalping_watch_budget_targets(
                        refresh_overflow,
                        ACTIVE_TARGETS,
                        reason="owner_quota_refresh_rebalance",
                    )
                    if any(item is existing for item in refresh_overflow):
                        _log_scanner_runtime_target_attach(
                            payload_for_log,
                            outcome="skipped",
                            reason="scanner_watch_budget_owner_quota",
                            target=existing,
                        )
                        return False
                _reset_scanner_runtime_eval_state(existing)
                if buy_price > 0 and not existing.get("marcap"):
                    existing["marcap"] = _resolve_stock_marcap(existing, code)
                _log_scanner_runtime_target_attach(
                    {
                        **payload_for_log,
                        **refresh_context_updates,
                        **refresh_context_fields,
                        "added_time": refresh_added_time,
                        "entry_armed_at_epoch": refresh_anchor_ts,
                        "scanner_promotion_id": refresh_promotion_id,
                        "scanner_promotion_reason": refresh_promotion_reason,
                        "scanner_promotion_emitted_epoch": refresh_promotion_epoch,
                        "source_signature": refresh_source_signature,
                    },
                    outcome="refreshed",
                    reason="existing_watching_refreshed",
                    target=existing,
                )
                event_bus.publish(
                    "COMMAND_WS_REG",
                    {"codes": [code], "source": "scanner_runtime_target_refresh"},
                )
                return True

            conflict_reason = _same_symbol_active_conflict_reason(existing)
            if conflict_reason:
                _log_scanner_runtime_target_attach(
                    {**payload_for_log, "existing_target": dict(existing)},
                    outcome="skipped",
                    reason=conflict_reason,
                    target=existing,
                )
                return False

        new_target = {
            "id": record_id,
            "code": code,
            "name": payload.get("name") or code,
            "strategy": strategy,
            "status": "WATCHING",
            "type": payload.get("trade_type") or "SCALP",
            "buy_price": buy_price,
            "added_time": now_ts,
            "entry_armed_at_epoch": promotion_anchor_ts,
            "position_tag": position_tag,
            "scanner_promotion_id": payload.get("scanner_promotion_id") or "",
            "scanner_promotion_reason": payload.get("scanner_promotion_reason") or "",
            "scanner_promotion_emitted_epoch": payload.get(
                "scanner_promotion_emitted_epoch"
            )
            or "",
            "source_signature": payload.get("source_signature") or "",
            **scanner_context_updates,
        }
        allowed, replacements, budget_fields = _scalping_attach_capacity_decision(
            new_target, now_ts
        )
        new_target.update(
            {
                key: value
                for key, value in budget_fields.items()
                if key
                in {
                    "scanner_watch_budget_owner",
                }
            }
        )
        payload_for_log = {**payload_for_log, **budget_fields}
        if replacements and not _scalping_attach_replace_enabled():
            allowed = False
        if not allowed:
            _log_scanner_runtime_target_attach(
                {
                    **payload_for_log,
                    "scanner_attach_capacity_cap": _scalping_fifo_max_active(),
                    "scanner_attach_capacity_watching_count": len(
                        [
                            target
                            for target in ACTIVE_TARGETS
                            if str((target or {}).get("status") or "").upper()
                            == "WATCHING"
                            and _is_scalping_fifo_target(target)
                        ]
                    ),
                    "scanner_attach_capacity_candidate_overflow": True,
                },
                outcome="skipped",
                reason="scalping_dynamic_watch_cap_capacity",
                target=new_target,
            )
            log_info(
                f"[SCALPING_SCANNER_PROMOTED_TARGET] skipped {code} "
                f"reason=scalping_dynamic_watch_cap_capacity cap={_scalping_fifo_max_active()}"
            )
            return False
        if replacements:
            _expire_scalping_watch_budget_targets(
                replacements,
                ACTIVE_TARGETS,
                reason="higher_priority_owner_slot_reclaimed",
            )
        new_target["marcap"] = _resolve_stock_marcap(new_target, code)
        ACTIVE_TARGETS.append(new_target)

    event_bus.publish(
        "COMMAND_WS_REG",
        {"codes": [code], "source": "scanner_runtime_target_attach"},
    )
    _log_scanner_runtime_target_attach(
        payload_for_log,
        outcome="attached",
        reason="new_watching_target_attached",
        target=new_target,
    )
    log_info(f"[SCALPING_SCANNER_PROMOTED_TARGET] attached {code} to ACTIVE_TARGETS")
    return True


def attach_db_poll_target_if_missing(db_target, targets, now_ts):
    """Merge DB WATCHING/HOLDING polling results, logging scanner event-bus recovery."""
    dt = dict(db_target or {})
    dt["strategy"] = normalize_strategy(dt.get("strategy"))
    dt["position_tag"] = normalize_position_tag(dt["strategy"], dt.get("position_tag"))
    code = normalize_manual_control_exclusion_code(dt.get("code"))
    if not code:
        return False
    control_exclusion = evaluate_manual_control_exclusion(code)
    if control_exclusion.excluded:
        if dt["strategy"] == "SCALPING" and dt["position_tag"] == "SCANNER":
            _log_scanner_runtime_target_attach(
                {**dt, **control_exclusion.as_log_fields()},
                outcome="skipped",
                reason=control_exclusion.reason,
                target=dt,
            )
        log_info(
            f"[MANUAL_CONTROL_EXCLUSION] DB poll attach skipped "
            f"{dt.get('name') or code}({control_exclusion.code}) source={control_exclusion.source}"
        )
        return False
    if _is_disabled_swing_watching_target(dt):
        log_info(
            f"[SWING_REAL_WATCHING_DISABLED] skip DB poll attach "
            f"{code} strategy={dt['strategy']} env={SWING_REAL_WATCHING_ENABLED_ENV}"
        )
        return False

    identity = target_identity(code, dt["strategy"])
    for target in targets:
        if (
            target_identity(target.get("code", ""), target.get("strategy", ""))
            != identity
        ):
            continue
        if _same_symbol_active_conflict_reason(target):
            return False

    dt["added_time"] = _runtime_added_time_for_target(dt, now_ts=now_ts)
    if dt["strategy"] == "SCALPING" and dt["position_tag"] == "SCANNER":
        owner_was_explicit = str(dt.get("scanner_watch_budget_owner") or "").strip()
        dt["scanner_watch_budget_owner"] = _scalping_watch_budget_owner(
            dt, now_ts=now_ts
        )
        dt["scanner_watch_budget_owner_source"] = (
            "database_payload"
            if owner_was_explicit
            else "legacy_db_restore_default_rising"
        )
        identity_payload = {
            "record_id": dt.get("id"),
            "code": code,
            "name": dt.get("name") or code,
            "strategy": dt["strategy"],
            "trade_type": dt.get("type") or "SCALP",
            "status": dt.get("status") or "WATCHING",
            "position_tag": dt["position_tag"],
            "buy_price": dt.get("buy_price"),
            "added_time": dt["added_time"],
            "entry_armed_at_epoch": dt.get("entry_armed_at_epoch") or dt["added_time"],
            "scanner_watch_budget_owner": dt["scanner_watch_budget_owner"],
            "scanner_watch_budget_owner_source": dt[
                "scanner_watch_budget_owner_source"
            ],
            "scanner_watch_budget_policy": "general1_opening3_rising_residual_v1",
            **scalping_session_venue_provenance(float(now_ts)),
        }
        identity_ok, identity_fields = _scanner_identity_guard(
            identity_payload,
            code,
            _safe_int(dt.get("buy_price"), 0),
        )
        identity_payload = {**identity_payload, **identity_fields}
        if not identity_ok:
            identity_reason = (
                identity_fields.get("scanner_identity_guard_reason")
                or "scanner_identity_mismatch"
            )
            expired = _expire_scanner_identity_mismatch_record(
                identity_payload, code, identity_reason
            )
            _log_scanner_runtime_target_attach(
                {**identity_payload, "scanner_identity_mismatch_expired": expired},
                outcome="skipped",
                reason=identity_reason,
                target=dt,
            )
            return False
    else:
        identity_payload = None

    if dt["strategy"] == "SCALPING" and dt["position_tag"] == "SCANNER":
        allowed, replacements, budget_fields = _scalping_attach_capacity_decision(
            dt,
            now_ts,
            watching_targets=[
                target
                for target in targets
                if str((target or {}).get("status") or "").upper() == "WATCHING"
                and _is_scalping_fifo_target(target)
            ],
        )
        identity_payload = {**identity_payload, **budget_fields}
        dt.update(
            {
                key: value
                for key, value in budget_fields.items()
                if key
                in {
                    "scanner_watch_budget_owner",
                }
            }
        )
        if replacements and not _scalping_attach_replace_enabled():
            allowed = False
        if not allowed:
            _expire_scalping_watch_budget_targets(
                [dt],
                targets,
                reason="db_poll_owner_quota_rejected",
            )
            _log_scanner_runtime_target_attach(
                identity_payload,
                outcome="skipped",
                reason="scanner_watch_budget_owner_quota",
                target=dt,
            )
            return False
        if replacements:
            _expire_scalping_watch_budget_targets(
                replacements,
                targets,
                reason="db_poll_higher_priority_owner_slot_reclaimed",
            )

    targets.append(dt)
    reg_payload = {"codes": [code]}
    if dt["strategy"] == "SCALPING" and dt["position_tag"] == "SCANNER":
        reg_payload["source"] = "scanner_db_poll_attach"
    event_bus.publish("COMMAND_WS_REG", reg_payload)

    if dt["strategy"] == "SCALPING" and dt["position_tag"] == "SCANNER":
        _log_scanner_runtime_target_attach(
            identity_payload,
            outcome="db_poll_attached",
            reason="eventbus_attach_missing_recovered_from_database_poll",
            target=dt,
        )
    return True


def _filter_invalid_scanner_identity_targets(targets):
    """Drop source-contaminated scanner WATCHING rows loaded directly from DB at boot."""
    kept = []
    for target in targets or []:
        strategy = normalize_strategy((target or {}).get("strategy"))
        position_tag = normalize_position_tag(
            strategy, (target or {}).get("position_tag")
        )
        status = str((target or {}).get("status") or "").upper()
        if (
            strategy == "SCALPING"
            and position_tag == "SCANNER"
            and status == "WATCHING"
        ):
            code = str((target or {}).get("code") or "").strip()[:6]
            payload = {
                "record_id": (target or {}).get("id"),
                "code": code,
                "name": (target or {}).get("name") or code,
                "strategy": strategy,
                "trade_type": (target or {}).get("type") or "SCALP",
                "status": status,
                "position_tag": position_tag,
                "buy_price": (target or {}).get("buy_price"),
                "added_time": (target or {}).get("added_time"),
                "entry_armed_at_epoch": (target or {}).get("entry_armed_at_epoch"),
                "scanner_promotion_id": (target or {}).get("scanner_promotion_id"),
                "scanner_promotion_reason": (target or {}).get(
                    "scanner_promotion_reason"
                ),
                "scanner_promotion_emitted_epoch": (target or {}).get(
                    "scanner_promotion_emitted_epoch"
                ),
                "source_signature": (target or {}).get("source_signature"),
            }
            identity_ok, identity_fields = _scanner_identity_guard(
                payload,
                code,
                _safe_int((target or {}).get("buy_price"), 0),
            )
            if not identity_ok:
                identity_reason = (
                    identity_fields.get("scanner_identity_guard_reason")
                    or "scanner_identity_mismatch"
                )
                expired = _expire_scanner_identity_mismatch_record(
                    payload, code, identity_reason
                )
                _log_scanner_runtime_target_attach(
                    {
                        **payload,
                        **identity_fields,
                        "scanner_identity_mismatch_expired": expired,
                    },
                    outcome="skipped",
                    reason=identity_reason,
                    target=target,
                )
                continue
        kept.append(target)
    return kept


def _restore_holding_runtime_state(targets):
    """Rehydrate HOLDING runtime fields so restart can resume with minimal drift."""
    restored = 0
    for stock in targets or []:
        if str(stock.get("status") or "").upper() != "HOLDING":
            continue

        code = str(stock.get("code", "")).strip()[:6]
        strategy = normalize_strategy(stock.get("strategy"))
        position_tag = normalize_position_tag(strategy, stock.get("position_tag"))
        buy_price = _safe_float(stock.get("buy_price"))

        stock["strategy"] = strategy
        stock["position_tag"] = position_tag
        stock["buy_qty"] = _safe_int(stock.get("buy_qty"))
        stock["initial_buy_qty"] = _safe_int(stock.get("initial_buy_qty"))
        if (
            stock["initial_buy_qty"] <= 0
            and max(
                _safe_int(stock.get("add_count")),
                _safe_int(stock.get("avg_down_count")),
                _safe_int(stock.get("pyramid_count")),
                int(bool(str(stock.get("last_add_type") or "").strip())),
            )
            <= 0
        ):
            stock["initial_buy_qty"] = _safe_int(stock.get("buy_qty"))
        stock["scale_in_filled_qty"] = _safe_int(stock.get("scale_in_filled_qty"))
        stock["add_count"] = _safe_int(stock.get("add_count"))
        stock["avg_down_count"] = _safe_int(stock.get("avg_down_count"))
        stock["pyramid_count"] = _safe_int(stock.get("pyramid_count"))
        stock["last_add_reason"] = str(stock.get("last_add_reason") or "").strip()
        stock["shallow_volatility_avg_down_count"] = _safe_int(
            stock.get("shallow_volatility_avg_down_count")
        )
        shallow_last_at = stock.get("shallow_volatility_avg_down_last_at")
        try:
            if hasattr(shallow_last_at, "timestamp"):
                stock["shallow_volatility_avg_down_last_at"] = float(
                    shallow_last_at.timestamp()
                )
            else:
                stock["shallow_volatility_avg_down_last_at"] = _safe_float(
                    shallow_last_at
                )
        except Exception:
            stock["shallow_volatility_avg_down_last_at"] = 0.0
        stock["scale_in_locked"] = bool(stock.get("scale_in_locked", False))
        stock["hard_stop_price"] = _safe_float(stock.get("hard_stop_price"))
        stock["trailing_stop_price"] = _safe_float(stock.get("trailing_stop_price"))

        if stock.get("buy_time") and not stock.get("holding_started_at"):
            stock["holding_started_at"] = stock.get("buy_time")

        if code and buy_price > 0:
            restored_peak = 0
            restore_reason = "not_scalping"
            if strategy == "SCALPING":
                try:
                    restored_peak, restore_reason = POSITION_PEAK_LEDGER.restore_peak(
                        stock
                    )
                except Exception as exc:
                    restore_reason = f"ledger_restore_failed:{type(exc).__name__}"
                    log_error(
                        f"[SCALP_PEAK_LEDGER] {stock.get('name', code)}({code}) "
                        f"restore failed: {exc}"
                    )
            highest_prices[code] = max(
                _safe_float(highest_prices.get(code)),
                buy_price,
                float(restored_peak or 0),
            )
            if strategy == "SCALPING":
                stock["position_peak_restore_reason"] = restore_reason
                stock["position_peak_restored_price"] = int(restored_peak or 0)
                stock["position_peak_runtime_price"] = int(highest_prices[code])

        if strategy == "SCALPING":
            stock.setdefault("last_ai_reviewed_at", None)
            stock.setdefault("near_ai_exit_started_at", None)
            if is_default_position_tag(strategy, position_tag):
                stock.setdefault("exit_mode", "SCALP_PRESET_TP")
                stock["preset_tp_price"] = 0

                base_stop = float(
                    getattr(TRADING_RULES, "SCALP_PRESET_HARD_STOP_PCT", -0.7) or -0.7
                )
                base_grace = int(
                    getattr(TRADING_RULES, "SCALP_PRESET_HARD_STOP_GRACE_SEC", 0) or 0
                )
                base_emergency = float(
                    getattr(
                        TRADING_RULES,
                        "SCALP_PRESET_HARD_STOP_EMERGENCY_PCT",
                        min(base_stop - 0.5, -1.2),
                    )
                    or min(base_stop - 0.5, -1.2)
                )

                if str(stock.get("entry_mode", "")).strip().lower() == "fallback":
                    stock.setdefault(
                        "hard_stop_pct",
                        float(
                            getattr(
                                TRADING_RULES,
                                "SCALP_PRESET_HARD_STOP_FALLBACK_BASE_PCT",
                                base_stop,
                            )
                            or base_stop
                        ),
                    )
                    stock.setdefault(
                        "hard_stop_grace_sec",
                        int(
                            getattr(
                                TRADING_RULES,
                                "SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC",
                                base_grace,
                            )
                            or base_grace
                        ),
                    )
                    stock.setdefault(
                        "hard_stop_emergency_pct",
                        float(
                            getattr(
                                TRADING_RULES,
                                "SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT",
                                base_emergency,
                            )
                            or base_emergency
                        ),
                    )
                else:
                    stock.setdefault("hard_stop_pct", base_stop)
                    stock.setdefault("hard_stop_grace_sec", base_grace)
                    stock.setdefault("hard_stop_emergency_pct", base_emergency)

                stock.setdefault("protect_profit_pct", None)
                stock.setdefault("ai_review_done", False)
                stock.setdefault("exit_requested", False)
                stock.setdefault("exit_order_type", None)
                stock.setdefault("exit_order_time", None)

        restored += 1

    if restored:
        log_info(f"[BOOT_RESTORE] HOLDING runtime rehydrated count={restored}")


def evaluate_scalping_exit(
    stock, code, ws_data, curr_p, buy_p, profit_rate, peak_profit
):
    base_stop_pct = getattr(TRADING_RULES, "SCALP_STOP", -1.5)
    hard_stop_pct = getattr(TRADING_RULES, "SCALP_HARD_STOP", -2.5)
    momentum_decay_score_limit = int(
        getattr(TRADING_RULES, "SCALP_AI_MOMENTUM_DECAY_SCORE_LIMIT", 45) or 45
    )
    momentum_decay_min_hold_sec = int(
        getattr(TRADING_RULES, "SCALP_AI_MOMENTUM_DECAY_MIN_HOLD_SEC", 90) or 90
    )
    safe_profit_pct = getattr(TRADING_RULES, "SCALP_SAFE_PROFIT", 0.5)
    trailing_start_pct = getattr(TRADING_RULES, "SCALP_TRAILING_START_PCT", 0.6)
    strong_trailing_ai_score = getattr(
        TRADING_RULES, "SCALP_TRAILING_STRONG_AI_SCORE", 75
    )
    weak_trailing = getattr(TRADING_RULES, "SCALP_TRAILING_LIMIT_WEAK", 0.4)
    strong_trailing = getattr(TRADING_RULES, "SCALP_TRAILING_LIMIT_STRONG", 0.8)
    current_ai_score_raw = _legacy_current_ai_score(stock)
    current_vpw = float(ws_data.get("v_pw", 0) or 0.0)

    # v_pw 히스토리 관리
    recent_vpw = stock.get("recent_vpw_values", [])
    recent_vpw.append(current_vpw)
    if len(recent_vpw) > 6:
        recent_vpw = recent_vpw[-6:]
    stock["recent_vpw_values"] = recent_vpw
    avg_vpw = sum(recent_vpw) / len(recent_vpw) if recent_vpw else current_vpw

    weak_vpw_count = int(stock.get("weak_vpw_count", 0) or 0)
    if current_vpw < 100:
        weak_vpw_count += 1
    else:
        weak_vpw_count = max(0, weak_vpw_count - 1)
    stock["weak_vpw_count"] = weak_vpw_count

    # 시간 가치(Time Decay)
    hold_start = _parse_holding_started_at(stock)
    held_seconds = (datetime.now() - hold_start).total_seconds() if hold_start else 0
    is_critical_zone = (
        abs(profit_rate - safe_profit_pct) <= 0.20
        or profit_rate >= safe_profit_pct
        or profit_rate < 0
    )
    holding_score_ctx = _legacy_holding_score_role_context(
        stock,
        current_ai_score_raw,
        is_critical_zone=is_critical_zone,
    )
    current_ai_score = _safe_float(holding_score_ctx.get("score"), 50.0)
    holding_score_negative_exit_usable = bool(
        holding_score_ctx.get("usable_for_negative_exit", False)
    )
    last_peak_update = stock.get("last_peak_update_at")
    if last_peak_update is None:
        stock["last_peak_update_at"] = datetime.now()
        last_peak_update = stock["last_peak_update_at"]
    elif not isinstance(last_peak_update, datetime):
        try:
            last_peak_update = datetime.fromisoformat(str(last_peak_update))
        except Exception:
            last_peak_update = datetime.now()
        stock["last_peak_update_at"] = last_peak_update

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
        return (
            f"소프트 손절선 도달 (profit_rate={profit_rate:.2f}% <= {soft_stop_pct}%)"
        )

    # Dynamic Trailing (peak 확보 이후만)
    if peak_profit >= trailing_start_pct and profit_rate >= safe_profit_pct:
        drawdown = (
            (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if highest_prices[code] > 0
            else 0
        )
        if (
            holding_score_negative_exit_usable
            and current_ai_score < momentum_decay_score_limit
            and held_seconds >= momentum_decay_min_hold_sec
        ):
            return (
                f"AI 모멘텀 둔화 확인유예 후 익절 "
                f"(score={current_ai_score:.0f}, hold={int(held_seconds)}s)"
            )
        if (
            holding_score_negative_exit_usable
            and current_ai_score >= strong_trailing_ai_score
            and current_vpw >= 110
        ):
            trailing_limit = strong_trailing
        elif (
            holding_score_negative_exit_usable
            and current_ai_score >= 65
            and current_vpw >= 105
        ):
            trailing_limit = (weak_trailing + strong_trailing) / 2
        else:
            trailing_limit = weak_trailing
        if drawdown >= trailing_limit:
            return f"고점 대비 밀림 (drawdown={drawdown:.2f}%)"

    # 장 마감 전 현금화 (기존 보존)
    now_t = datetime.now().time()
    if now_t >= TIME_15_30 and profit_rate >= getattr(
        TRADING_RULES, "MIN_FEE_COVER", 0.1
    ):
        return "장 마감 전 현금화"

    return None


def evaluate_swing_exit(
    stock,
    code,
    ws_data,
    curr_p,
    buy_p,
    profit_rate,
    peak_profit,
    market_regime,
    strategy,
):
    if strategy == "KOSDAQ_ML":
        if peak_profit >= getattr(TRADING_RULES, "KOSDAQ_TARGET", 4.0):
            drawdown = (
                (highest_prices[code] - curr_p) / highest_prices[code] * 100
                if highest_prices[code] > 0
                else 0
            )
            # TODO: KOSDAQ 트레일링 되밀림 폭을 TRAILING_DRAWDOWN_PCT로 통일 검토
            if drawdown >= 1.0:
                return f"KOSDAQ 트레일링 익절 (peak_profit={peak_profit:.1f}%)"
        if profit_rate <= getattr(TRADING_RULES, "KOSDAQ_STOP", -2.0):
            return f"KOSDAQ 손절선 도달 (profit_rate={profit_rate:.2f}%)"
        return None

    pos_tag = normalize_position_tag(strategy, stock.get("position_tag"))
    if pos_tag == "BREAKOUT":
        current_stop_loss = getattr(TRADING_RULES, "STOP_LOSS_BREAKOUT")
    elif pos_tag == "BOTTOM":
        current_stop_loss = getattr(TRADING_RULES, "STOP_LOSS_BOTTOM")
    else:
        current_stop_loss = (
            getattr(TRADING_RULES, "STOP_LOSS_BULL")
            if market_regime == "BULL"
            else getattr(TRADING_RULES, "STOP_LOSS_BEAR")
        )

    if profit_rate <= current_stop_loss:
        return (
            f"스윙 손절선 도달 (profit_rate={profit_rate:.2f}% <= {current_stop_loss}%)"
        )

    if peak_profit >= getattr(TRADING_RULES, "TRAILING_START_PCT"):
        drawdown = (
            (highest_prices[code] - curr_p) / highest_prices[code] * 100
            if highest_prices[code] > 0
            else 0
        )
        if drawdown >= getattr(TRADING_RULES, "TRAILING_DRAWDOWN_PCT"):
            return f"스윙 트레일링 익절 (peak_profit={peak_profit:.1f}%)"
    return None


def check_holding_conditions(
    stock, code, ws_data, admin_id, market_regime, radar=None, ai_engine=None
):
    """
    HOLDING 상태 종목이 SELL_ORDERED로 전환되지 못하는 이유를 분석하여 문자열로 반환합니다.
    모든 조건을 통과하면 None을 반환합니다.
    """
    global highest_prices

    raw_strategy = (stock.get("strategy") or "KOSPI_ML").upper()
    strategy = "SCALPING" if raw_strategy in ["SCALPING", "SCALP"] else raw_strategy

    curr_p = _safe_int(ws_data.get("curr"), 0)
    buy_p = _safe_float(stock.get("buy_price"), 0.0)
    if curr_p <= 0 or buy_p <= 0:
        return "현재가 또는 매수가 유효하지 않음"
    if not stock.get("holding_started_at"):
        if stock.get("buy_time"):
            stock["holding_started_at"] = stock.get("buy_time")

    profit_rate = calculate_net_profit_rate(buy_p, curr_p)
    if code in highest_prices:
        if curr_p > highest_prices[code]:
            highest_prices[code] = curr_p
            stock["last_peak_update_at"] = datetime.now()
    else:
        highest_prices[code] = curr_p
        stock["last_peak_update_at"] = datetime.now()
    peak_profit = calculate_net_profit_rate(buy_p, highest_prices[code])

    if strategy == "SCALPING":
        reason = evaluate_scalping_exit(
            stock, code, ws_data, curr_p, buy_p, profit_rate, peak_profit
        )
        if reason:
            return reason
    else:
        reason = evaluate_swing_exit(
            stock,
            code,
            ws_data,
            curr_p,
            buy_p,
            profit_rate,
            peak_profit,
            market_regime,
            strategy,
        )
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

    admin_id = CONF.get("ADMIN_ID")
    print(f"🔫 스나이퍼 V12.2 멀티 엔진 가동 (관리자: {admin_id})")
    if run_sniper.runtime_pause_state:
        log_info(
            "⏸ 부팅 시 pause.flag 감지: 신규 매수 및 추가매수 중단 상태로 시작합니다."
        )
    if not admin_id:
        log_info(
            "⚠️ ADMIN_ID가 설정되지 않았습니다. 매도 주문이 실행되지 않을 수 있습니다."
        )

    is_open, reason = kiwoom_utils.is_trading_day()
    if not is_test_mode and not is_open:
        msg = f"🛑 오늘은 {reason} 휴장일이므로 스나이퍼 매매 엔진을 가동하지 않습니다."
        print(msg)
        event_bus.publish("TELEGRAM_BROADCAST", {"message": msg})
        return

    KIWOOM_TOKEN = kiwoom_utils.get_kiwoom_token(CONF)
    if not KIWOOM_TOKEN:
        log_error("❌ 토큰 발급 실패로 엔진을 중단합니다.")
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {"message": "🚨 [시스템 에러] 토큰 발급 실패로 엔진을 중단합니다."},
        )
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
    bind_condition_dependencies(
        kiwoom_token=KIWOOM_TOKEN, ws_manager=WS_MANAGER, db=DB, event_bus=event_bus
    )
    bind_state_dependencies(ws_manager=WS_MANAGER)
    bind_analysis_dependencies(
        kiwoom_token=KIWOOM_TOKEN,
        ws_manager=WS_MANAGER,
        event_bus=event_bus,
        conf=CONF,
        db=DB,
        trading_rules=TRADING_RULES,
    )

    # 중복 subscribe 방지
    if not getattr(run_sniper, "_subscriptions_registered", False):
        event_bus.subscribe("ORDER_NOTICE", handle_order_notice)
        event_bus.subscribe("ORDER_EXECUTED", handle_real_execution)
        event_bus.subscribe("CONDITION_MATCHED", handle_condition_matched)
        event_bus.subscribe("CONDITION_UNMATCHED", handle_condition_unmatched)
        event_bus.subscribe(
            "SCALPING_SCANNER_PROMOTION_BATCH_PENDING",
            handle_scalping_scanner_promotion_batch_pending,
        )
        event_bus.subscribe(
            "SCALPING_SCANNER_PROMOTED_TARGET", handle_scalping_scanner_promoted_target
        )
        event_bus.subscribe("WS_REG_BUDGET_SKIPPED", handle_ws_reg_budget_skipped)

        def on_trading_paused(payload):
            payload = payload or {}
            status = str(payload.get("status", "")).upper()
            if status == "PAUSED":
                run_sniper.runtime_pause_state = True
                log_info(
                    "[TRADING_PAUSED] runtime state updated immediately via EventBus: PAUSED"
                )
            elif status == "RESUMED":
                run_sniper.runtime_pause_state = False
                log_info(
                    "[TRADING_RESUMED] runtime state updated immediately via EventBus: RESUMED"
                )
            else:
                run_sniper.runtime_pause_state = is_buy_side_paused()
                tag = (
                    "TRADING_PAUSED"
                    if run_sniper.runtime_pause_state
                    else "TRADING_RESUMED"
                )
                log_info(
                    f"[{tag}] runtime state refreshed from file truth source after unknown EventBus payload; "
                    f"fallback_to_flag={run_sniper.runtime_pause_state}"
                )

        def on_ws_reconnect(payload):
            threading.Thread(target=sync_state_with_broker, daemon=True).start()

        event_bus.subscribe("TRADING_PAUSED", on_trading_paused)
        event_bus.subscribe("WS_RECONNECTED", on_ws_reconnect)
        run_sniper._subscriptions_registered = True

    WS_MANAGER.start()
    time.sleep(2)

    # ==========================================
    # 🤖 OpenAI runtime AI engine
    # ==========================================
    ai_engine = None
    AI_ENGINE = None
    dual_persona_engine = None
    global DUAL_PERSONA_ENGINE
    runtime_role = resolve_runtime_role()

    openai_dual_enabled = bool(
        getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_ENABLED", True)
    )
    openai_shadow_mode = bool(
        getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_SHADOW_MODE", True)
    )
    openai_api_keys = [
        v for k, v in CONF.items() if k.startswith("OPENAI_API_KEY") and v
    ]
    if runtime_role == "main" and openai_api_keys:
        try:
            ai_engine = GPTSniperEngine(
                api_keys=openai_api_keys, announce_startup=False
            )
            fast_model = str(
                getattr(TRADING_RULES, "GPT_FAST_MODEL", "gpt-5-nano") or "gpt-5-nano"
            )
            deep_model = str(
                getattr(TRADING_RULES, "GPT_DEEP_MODEL", fast_model) or fast_model
            )
            report_model = str(
                getattr(TRADING_RULES, "GPT_REPORT_MODEL", fast_model) or fast_model
            )
            ai_engine.set_model_names(
                fast_model=fast_model,
                deep_model=deep_model,
                report_model=report_model,
                announce=True,
            )
            AI_ENGINE = ai_engine
            print(
                "🧠 메인 OpenAI AI 엔진 고정 완료 "
                f"(FAST: {fast_model} / DEEP: {deep_model} / REPORT: {report_model})"
            )
        except Exception as e:
            log_error(f"🚨 OpenAI AI 엔진 초기화 실패: {e}")
            event_bus.publish(
                "TELEGRAM_BROADCAST",
                {"message": f"🚨 [시스템 에러] OpenAI AI 엔진 초기화 실패: {e}"},
            )
            ai_engine = None
            AI_ENGINE = None
    elif runtime_role == "main" and not openai_api_keys:
        log_error("🚨 OPENAI_API_KEY가 없어 AI 엔진을 비활성화합니다.")
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {
                "message": "🚨 [시스템 에러] OPENAI_API_KEY 미설정으로 AI 엔진을 비활성화합니다."
            },
        )
    else:
        log_info(
            f"ℹ️ runtime_role={runtime_role}: main OpenAI AI 엔진 초기화를 건너뜁니다."
        )

    if openai_dual_enabled and openai_shadow_mode and openai_api_keys:
        try:
            dual_persona_engine = OpenAIDualPersonaShadowEngine(
                api_keys=openai_api_keys
            )
            DUAL_PERSONA_ENGINE = dual_persona_engine
            print(
                f"🧠 OpenAI 듀얼 페르소나 shadow 엔진이 {len(openai_api_keys)}개의 API 키로 가동됩니다."
            )
        except Exception as e:
            log_error(f"🚨 OpenAI 듀얼 페르소나 엔진 초기화 실패: {e}")
            dual_persona_engine = None
            DUAL_PERSONA_ENGINE = None
    elif openai_dual_enabled and not openai_api_keys:
        log_info(
            "ℹ️ OPENAI_API_KEY 미설정으로 듀얼 페르소나 shadow 엔진은 비활성화됩니다."
        )

    if AI_ENGINE is not None:
        print(
            f"🧭 AI 라우팅 활성화: role={runtime_role} "
            f"(main_openai={'ON' if runtime_role == 'main' else 'OFF'})"
        )

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
    bind_state_dependencies(active_targets=ACTIVE_TARGETS, ws_manager=WS_MANAGER)
    sniper_state_handlers.sanitize_pending_add_states(ACTIVE_TARGETS)
    bind_execution_dependencies(active_targets=ACTIVE_TARGETS)
    bind_overnight_dependencies(active_targets=ACTIVE_TARGETS)
    _restore_armed_candidates_from_database()
    # ==========================================
    # 💡 [추가 1] 봇 시작 시 불러온 종목들의 진입 시간 기록
    # ==========================================
    boot_ts = time.time()
    for t in ACTIVE_TARGETS:
        t["strategy"] = normalize_strategy(t.get("strategy"))
        t["position_tag"] = normalize_position_tag(t["strategy"], t.get("position_tag"))
        t["added_time"] = _runtime_added_time_for_target(t, now_ts=boot_ts)
    ACTIVE_TARGETS[:] = _filter_disabled_swing_watching_targets(ACTIVE_TARGETS)
    ACTIVE_TARGETS[:] = _filter_invalid_scanner_identity_targets(ACTIVE_TARGETS)
    _restore_holding_runtime_state(ACTIVE_TARGETS)
    sniper_state_handlers.sync_scalp_simulator_targets_from_state(ACTIVE_TARGETS)
    try:
        run_sniper.last_scalp_sim_state_mtime = (
            sniper_state_handlers.SCALP_SIM_STATE_PATH.stat().st_mtime_ns
            if sniper_state_handlers.SCALP_SIM_STATE_PATH.exists()
            else None
        )
    except Exception:
        run_sniper.last_scalp_sim_state_mtime = None
    sniper_state_handlers.restore_swing_intraday_probe_targets(ACTIVE_TARGETS)
    try:
        run_sniper.last_swing_probe_state_mtime = (
            sniper_state_handlers.SWING_INTRADAY_PROBE_STATE_PATH.stat().st_mtime_ns
            if sniper_state_handlers.SWING_INTRADAY_PROBE_STATE_PATH.exists()
            else None
        )
    except Exception:
        run_sniper.last_swing_probe_state_mtime = None

    targets = ACTIVE_TARGETS
    last_db_poll_time = time.time()

    if is_buy_side_paused():
        log_info(
            "[TRADING_PAUSED] engine booted with 신규 매수 및 추가매수 중단 상태 active"
        )

    priority_codes, scanner_boot_codes = _initial_ws_registration_groups(
        targets, now_ts=time.time()
    )
    if priority_codes:
        event_bus.publish(
            "COMMAND_WS_REG",
            {"codes": priority_codes, "source": "sniper_boot_priority_ws_budget"},
        )
    if scanner_boot_codes:
        event_bus.publish(
            "COMMAND_WS_REG",
            {"codes": scanner_boot_codes, "source": "scanner_boot_hot_ws_budget"},
        )

    last_msg_min = -1
    scanner_ws_reg_last_emit_ts: dict[tuple[str, str], float] = {}
    scanner_ws_repair_cycle_state_by_code: dict[str, dict] = {}
    try:
        fast_exit_interval_sec = max(
            0.05,
            float(os.getenv("KORSTOCKSCAN_SCALP_FAST_EXIT_POLL_MS", "250")) / 1000.0,
        )
    except (TypeError, ValueError):
        fast_exit_interval_sec = 0.25
    fast_exit_monitor = ScalpExitSafetyMonitor(
        targets_provider=lambda: targets,
        ws_snapshot_provider=(
            lambda code: (
                WS_MANAGER.get_latest_data(code)
                if WS_MANAGER is not None and hasattr(WS_MANAGER, "get_latest_data")
                else {}
            )
        ),
        evaluator=sniper_state_handlers.evaluate_and_dispatch_fast_scalp_exit,
        state_lock=ENTRY_LOCK,
        interval_sec=fast_exit_interval_sec,
        error_handler=lambda message: log_error(f"[SCALP_FAST_EXIT_MONITOR] {message}"),
    )
    fast_exit_monitor.start()

    try:
        while True:
            now_ts = time.time()
            now = datetime.now()
            now_t = now.time()
            run_sniper.runtime_pause_state = is_buy_side_paused()
            current_market_regime = _current_market_regime_code()
            _ensure_state_handler_deps()

            from src.engine.error_detectors.process_health import (
                write_heartbeat as _sn_whb,
            )

            _sn_whb("sniper_engine")

            if RESTART_FLAG_PATH.exists():
                print(
                    "🔄 [우아한 종료] 재시작 깃발을 확인했습니다. 시스템을 안전하게 정지합니다."
                )
                event_bus.publish(
                    "TELEGRAM_BROADCAST",
                    {
                        "message": "🛑 스나이퍼 엔진이 하던 작업을 마치고 우아하게 재시작됩니다."
                    },
                )
                RESTART_FLAG_PATH.unlink(missing_ok=True)
                _sn_whb("sniper_engine", alive=False)
                break

            today_key = now.date().isoformat()
            if (
                now_t >= TIME_09_00
                and getattr(run_sniper, "krx_open_watchlist_reset_date", None)
                != today_key
            ):
                reset_codes = _reset_krx_open_watch_targets(targets, now_dt=now)
                run_sniper.krx_open_watchlist_reset_date = today_key
                if reset_codes:
                    log_info(
                        "[KRX_OPEN_WATCHLIST_RESET] expired pre-open WATCHING targets "
                        f"count={len(reset_codes)} codes={','.join(sorted(set(reset_codes)))}"
                    )

            scalp_sim_sync = (
                sniper_state_handlers.sync_scalp_simulator_targets_if_state_changed(
                    targets,
                    last_mtime=getattr(run_sniper, "last_scalp_sim_state_mtime", None),
                )
            )
            run_sniper.last_scalp_sim_state_mtime = scalp_sim_sync.get("state_mtime")
            swing_probe_sync = sniper_state_handlers.sync_swing_intraday_probe_targets_if_state_changed(
                targets,
                last_mtime=getattr(run_sniper, "last_swing_probe_state_mtime", None),
            )
            run_sniper.last_swing_probe_state_mtime = swing_probe_sync.get(
                "state_mtime"
            )

            if not is_test_mode and now_t >= TIME_20_00:
                print("🌙 장 마감 시간이 다가와 감시를 종료합니다.")
                highest_prices.clear()
                alerted_stocks.clear()
                cooldowns.clear()
                LAST_AI_CALL_TIMES.clear()
                ACTIVE_TARGETS.clear()
                _sn_whb("sniper_engine", alive=False)
                break

            # =====================================================
            # 신규 DB 타겟 polling (P0 계측 포함)
            # =====================================================
            _t0_db = time.perf_counter()
            if now_ts - last_db_poll_time > 5:
                db_targets = DB.get_active_targets() or []
                for dt in db_targets:
                    attach_db_poll_target_if_missing(dt, targets, now_ts)
                last_db_poll_time = now_ts
            _db_elapsed_ms = (time.perf_counter() - _t0_db) * 1000

            # =====================================================
            # WATCHING TTL / FIFO
            # =====================================================
            if now_ts - getattr(run_sniper, "last_fifo_time", 0) > 10:
                watching_stocks = [t for t in targets if t.get("status") == "WATCHING"]
                expired_ids = []
                expired_names = []

                watching_stocks.sort(
                    key=lambda x: _runtime_added_time_for_target(x, now_ts=now_ts)
                )
                scalp_fifo_targets = _scalping_fifo_candidates(watching_stocks, now_ts)
                scalping_watching_ttl_sec = _scalping_watching_ttl_sec()

                for t in scalp_fifo_targets:
                    if (
                        now_ts - _runtime_added_time_for_target(t, now_ts=now_ts)
                        > scalping_watching_ttl_sec
                    ):
                        expired_ids.append(t["id"])
                        expired_names.append(t["name"])

                scalp_remaining = [
                    t for t in scalp_fifo_targets if t["id"] not in expired_ids
                ]
                for t in _scalping_watch_budget_overflow_candidates(
                    scalp_remaining, now_ts
                ):
                    expired_ids.append(t["id"])
                    expired_names.append(t["name"])

                if expired_ids:
                    try:
                        with DB.get_session() as session:
                            session.query(RecommendationHistory).filter(
                                RecommendationHistory.id.in_(expired_ids)
                            ).update({"status": "EXPIRED"}, synchronize_session=False)
                    except Exception as e:
                        log_error(f"🚨 FIFO 큐 DB 업데이트 에러: {e}")

                    for t in targets:
                        if t.get("id") in expired_ids:
                            t["status"] = "EXPIRED"

                    print(
                        f"🗑️ [스캘핑 큐 정리] {len(expired_ids)}개 단기 종목 감시 만료"
                    )
                    if len(expired_names) <= 10:
                        print(f"   └ 만료 종목: {', '.join(expired_names)}")

                run_sniper.last_fifo_time = now_ts

            # =====================================================
            # 90초 주기 계좌 동기화 (P1: ThreadPoolExecutor)
            # =====================================================
            _t0_acct = time.perf_counter()
            global _ACCOUNT_SYNC_EXECUTOR, _ACCOUNT_SYNC_IN_FLIGHT
            if _ACCOUNT_SYNC_EXECUTOR is None:
                _ACCOUNT_SYNC_EXECUTOR = ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="acct_sync"
                )
            if now_ts - getattr(run_sniper, "last_account_sync_time", 0) > 90:
                if not _ACCOUNT_SYNC_IN_FLIGHT:
                    _ACCOUNT_SYNC_IN_FLIGHT = True
                    future = _ACCOUNT_SYNC_EXECUTOR.submit(
                        _run_account_sync_with_cleanup
                    )
                    future.add_done_callback(lambda _f: _clear_account_sync_in_flight())
                    run_sniper.last_account_sync_time = now_ts
            _acct_elapsed_ms = (time.perf_counter() - _t0_acct) * 1000

            # =====================================================
            # Preclose SCALPING overnight decision (DB 기준, 무조건 1회 작동)
            # =====================================================
            last_eod_done = getattr(run_sniper, "scalping_eod_done_date", None)
            last_eod_try = getattr(run_sniper, "last_scalping_eod_try", 0)
            overnight_gatekeeper_enabled = bool(
                getattr(TRADING_RULES, "SCALPING_OVERNIGHT_GATEKEEPER_ENABLED", False)
            )
            if (
                overnight_gatekeeper_enabled
                and now_t >= TIME_SCALPING_OVERNIGHT_DECISION
                and last_eod_done != today_key
            ):
                if now_ts - last_eod_try >= 60:
                    run_sniper.last_scalping_eod_try = now_ts
                    if run_scalping_overnight_gatekeeper(ai_engine=ai_engine):
                        run_sniper.scalping_eod_done_date = today_key
                        last_eod_done = today_key

            eod_ai_holding_fallback = (
                overnight_gatekeeper_enabled
                and now_t >= TIME_SCALPING_OVERNIGHT_DECISION
                and (last_eod_done == today_key or last_eod_try > 0)
            )

            # =====================================================
            # 상태 로그
            # =====================================================
            if now_t.minute % 5 == 0 and now_t.minute != last_msg_min:
                watching_count = len(
                    [t for t in targets if t.get("status") == "WATCHING"]
                )
                holding_targets = [t for t in targets if t.get("status") == "HOLDING"]
                real_holding_count = len(
                    [t for t in holding_targets if not _is_runtime_simulation_target(t)]
                )
                scalp_sim_holding_count = len(
                    [t for t in holding_targets if _is_runtime_scalp_sim_target(t)]
                )
                probe_holding_count = len(
                    [t for t in holding_targets if _is_runtime_probe_target(t)]
                )
                other_sim_holding_count = max(
                    0,
                    len(holding_targets)
                    - real_holding_count
                    - scalp_sim_holding_count
                    - probe_holding_count,
                )
                print(
                    f"💓 [{now.strftime('%H:%M:%S')}] 다중 감시망 가동 중... "
                    f"(감시: {watching_count} / 보유: {real_holding_count} / "
                    f"scalp_sim: {scalp_sim_holding_count} / probe: {probe_holding_count} / "
                    f"other_sim: {other_sim_holding_count})"
                )
                last_msg_min = now_t.minute

            # =====================================================
            # 상태 라우팅
            # ✅ 주문대기 상태는 ws_data 없이도 먼저 처리
            # =====================================================
            queue_context = _runtime_queue_context(targets, now_ts=now_ts)
            active_scanner_watch_codes = {
                str(t.get("code", "")).strip()[:6]
                for t in targets
                if _is_scanner_watching_target(t)
            }
            _prune_scanner_watch_full_eval_deferred_state(targets)
            for stale_code in list(scanner_ws_repair_cycle_state_by_code.keys()):
                if stale_code not in active_scanner_watch_codes:
                    scanner_ws_repair_cycle_state_by_code.pop(stale_code, None)
            scanner_ws_snapshot_cache = _runtime_scanner_ws_snapshot_cache(
                queue_context["iteration_targets"]
            )
            scanner_full_eval_count = 0
            scanner_rising_full_eval_relief_count = 0
            scanner_full_eval_base_limit = _scanner_full_eval_max_per_loop()
            scanner_full_eval_limit = _scanner_full_eval_effective_limit(
                queue_context,
                base_limit=scanner_full_eval_base_limit,
            )
            scanner_rising_full_eval_extra_limit = min(
                _scanner_rising_full_eval_extra_per_loop(),
                max(0, 40 - scanner_full_eval_limit),
            )
            delayed_scanner_heavy_eval = []
            pending_scanner_ws_reg: dict[str, set[str]] = {}
            pending_scanner_ws_persistent_repair: dict[str, set[str]] = {}
            deferred_scanner_pipeline_events = []
            deferred_scanner_skip_events = []
            scanner_precheck_seen = False
            scanner_heavy_eval_flushed = False
            scanner_rest_quote_fallback_loop_limit = (
                _scanner_rest_quote_fallback_max_per_loop()
            )
            scanner_rest_quote_fallback_loop_count = 0
            scanner_no_trade_eviction_loop_limit = (
                _scanner_no_trade_eviction_max_per_loop()
            )
            scanner_no_trade_eviction_loop_count = 0
            scanner_queue_lag_eviction_loop_limit = (
                _scanner_queue_lag_eviction_max_per_loop()
            )
            scanner_queue_lag_eviction_loop_count = 0
            scanner_full_eval_deferred_eviction_loop_limit = (
                _scanner_full_eval_deferred_eviction_max_per_loop()
            )
            scanner_full_eval_deferred_eviction_loop_count = 0

            def _defer_scanner_entry_pipeline_log(
                stock_value, code_value, stage, fields
            ):
                deferred_scanner_pipeline_events.append(
                    (
                        _scanner_pipeline_stock_snapshot(stock_value),
                        str(code_value or "").strip()[:6],
                        str(stage or ""),
                        dict(fields or {}),
                    )
                )

            def _flush_deferred_scanner_pipeline_events():
                if not deferred_scanner_pipeline_events:
                    return
                events = list(deferred_scanner_pipeline_events)
                deferred_scanner_pipeline_events.clear()

                def _emit_batch(batch):
                    for stock_value, code_value, stage, fields in batch:
                        sniper_state_handlers._log_entry_pipeline(
                            stock_value,
                            code_value,
                            stage,
                            **fields,
                        )

                _SCANNER_OBSERVATION_EXECUTOR.submit(_emit_batch, events)

            def _defer_emit_scanner_fast_precheck(
                stock_value,
                code_value,
                *,
                now_value,
                ws_snapshot,
                queue_rank,
                scanner_queue_rank,
                watching_count,
                scanner_watching_count,
                throttle_sec=5,
            ):
                if not sniper_state_handlers._is_scanner_watching_runtime_observation_target(
                    stock_value
                ):
                    return False
                throttle = max(0, int(throttle_sec or 0))
                last_logged = _safe_float(
                    stock_value.get("_scanner_fast_precheck_logged_at"), 0.0
                )
                if throttle > 0 and float(now_value) - last_logged < throttle:
                    return False
                stock_value["_scanner_fast_precheck_logged_at"] = float(now_value)
                fields = sniper_state_handlers._scanner_fast_precheck_fields(
                    stock_value,
                    now_ts=float(now_value),
                    code=code_value,
                    ws_data=ws_snapshot,
                    queue_rank=queue_rank,
                    scanner_queue_rank=scanner_queue_rank,
                    watching_count=watching_count,
                    scanner_watching_count=scanner_watching_count,
                )
                if (
                    fields.get("fast_precheck_result")
                    == "eligible_for_heavy_entry_eval"
                ):
                    stock_value["_scanner_heavy_queue_enter_epoch"] = float(now_value)
                stock_value["_scanner_fast_precheck_result"] = fields.get(
                    "fast_precheck_result"
                )
                stock_value["_scanner_fast_precheck_reason"] = fields.get(
                    "fast_precheck_reason"
                )
                stock_value["_scanner_fast_precheck_fields"] = dict(fields)
                _defer_scanner_entry_pipeline_log(
                    stock_value,
                    code_value,
                    "scalping_scanner_promotion_latency_trace",
                    _scanner_promotion_latency_trace_fields(
                        stock_value,
                        ws_snapshot,
                        now_ts=float(now_value),
                        trace_phase="fast_precheck",
                        fast_precheck_fields=fields,
                    ),
                )
                _defer_scanner_entry_pipeline_log(
                    stock_value,
                    code_value,
                    "scalping_scanner_fast_precheck",
                    fields,
                )
                return True

            def _defer_emit_scanner_runtime_queue_lag(
                stock_value,
                code_value,
                *,
                now_value,
                queue_rank,
                scanner_queue_rank,
                watching_count,
                scanner_watching_count,
                real_holding_count,
                non_real_holding_count,
                pre_scanner_runtime_count,
                loop_started_epoch,
                throttle_sec=10,
            ):
                if not sniper_state_handlers._is_scanner_watching_runtime_observation_target(
                    stock_value
                ):
                    return None
                throttle = max(0, int(throttle_sec or 0))
                last_logged = _safe_float(
                    stock_value.get("_scanner_runtime_queue_lag_logged_at"), 0.0
                )
                if throttle > 0 and float(now_value) - last_logged < throttle:
                    return None
                stock_value["_scanner_runtime_queue_lag_logged_at"] = float(now_value)
                fields = sniper_state_handlers._scanner_runtime_queue_lag_fields(
                    stock_value,
                    now_ts=float(now_value),
                    queue_rank=queue_rank,
                    scanner_queue_rank=scanner_queue_rank,
                    watching_count=watching_count,
                    scanner_watching_count=scanner_watching_count,
                    real_holding_count=real_holding_count,
                    non_real_holding_count=non_real_holding_count,
                    pre_scanner_runtime_count=pre_scanner_runtime_count,
                    loop_started_epoch=float(loop_started_epoch),
                )
                _defer_scanner_entry_pipeline_log(
                    stock_value,
                    code_value,
                    "scalping_scanner_runtime_queue_lag",
                    fields,
                )
                return fields

            def _defer_emit_scanner_heavy_eval_lag(
                stock_value,
                code_value,
                *,
                now_value,
                queue_enter_epoch,
                throttle_sec=5,
            ):
                if not sniper_state_handlers._is_scanner_watching_runtime_observation_target(
                    stock_value
                ):
                    return False
                throttle = max(0, int(throttle_sec or 0))
                last_logged = _safe_float(
                    stock_value.get("_scanner_heavy_eval_lag_logged_at"), 0.0
                )
                if throttle > 0 and float(now_value) - last_logged < throttle:
                    return False
                stock_value["_scanner_heavy_eval_lag_logged_at"] = float(now_value)
                fields = sniper_state_handlers._scanner_heavy_eval_lag_fields(
                    stock_value,
                    now_ts=float(now_value),
                    queue_enter_epoch=queue_enter_epoch,
                )
                _defer_scanner_entry_pipeline_log(
                    stock_value,
                    code_value,
                    "scalping_scanner_promotion_latency_trace",
                    _scanner_promotion_latency_trace_fields(
                        stock_value,
                        {},
                        now_ts=float(now_value),
                        trace_phase="heavy_eval",
                        heavy_queue_enter_epoch=queue_enter_epoch,
                    ),
                )
                _defer_scanner_entry_pipeline_log(
                    stock_value,
                    code_value,
                    "scalping_scanner_heavy_eval_lag",
                    fields,
                )
                return True

            def _defer_scanner_watching_runtime_skip(stock_value, code_value, **kwargs):
                deferred_scanner_skip_events.append(
                    (stock_value, code_value, dict(kwargs))
                )

            def _flush_deferred_scanner_skip_events():
                if not deferred_scanner_skip_events:
                    return
                events = list(deferred_scanner_skip_events)
                deferred_scanner_skip_events.clear()

                def _emit_batch(batch):
                    for stock_value, code_value, kwargs in batch:
                        sniper_state_handlers.emit_scanner_watching_runtime_skip(
                            stock_value,
                            code_value,
                            **kwargs,
                        )

                _SCANNER_OBSERVATION_EXECUTOR.submit(_emit_batch, events)

            def _queue_scanner_ws_reg(code_value, source):
                norm_code = str(code_value or "").strip()[:6]
                if not norm_code:
                    return
                source_key = str(source or "scanner_watching_ws_snapshot_recovery")
                if not _scanner_ws_reg_recovery_throttle_allows(
                    scanner_ws_reg_last_emit_ts,
                    source_key,
                    norm_code,
                    time.time(),
                ):
                    return
                pending_scanner_ws_reg.setdefault(source_key, set()).add(norm_code)

            def _queue_scanner_ws_persistent_repair(
                stock_value, code_value, ws_snapshot, recovery_fields
            ):
                fields = dict(recovery_fields or {})
                if not fields.get("ws_repair_batch_required"):
                    return {}
                norm_code = str(code_value or "").strip()[:6]
                if not norm_code:
                    return {
                        "ws_repair_batch_queued": False,
                        "ws_repair_batch_reason": "missing_code",
                    }
                now_value = time.time()
                recheck_snapshot, recheck_fields = (
                    _scanner_ws_subscription_recheck_snapshot_and_fields(
                        WS_MANAGER,
                        norm_code,
                        ws_snapshot,
                        now_ts=now_value,
                    )
                )
                repair_state = (
                    stock_value.setdefault("_scanner_ws_persistent_repair", {})
                    if isinstance(stock_value, dict)
                    else {}
                )
                if not isinstance(repair_state, dict):
                    repair_state = {}
                    if isinstance(stock_value, dict):
                        stock_value["_scanner_ws_persistent_repair"] = repair_state
                cycle_id = str(fields.get("ws_repair_cycle_id") or "")
                min_interval_sec = _scanner_ws_persistent_repair_min_interval_sec()
                last_batch_ts = _safe_float(
                    repair_state.get("last_repair_batch_ts"), 0.0
                )
                last_cycle_id = str(repair_state.get("last_repair_cycle_id") or "")
                if not recheck_fields.get("ws_subscription_repair_needed", True):
                    repair_state["last_repair_outcome"] = (
                        "snapshot_arrived_after_subscription_recheck"
                    )
                    return {
                        **recheck_fields,
                        "_ws_subscription_recheck_snapshot": recheck_snapshot,
                        "ws_repair_batch_queued": False,
                        "ws_repair_batch_reason": "snapshot_arrived_after_subscription_recheck",
                        "ws_recovery_outcome": "ws_snapshot_arrived_after_subscription_recheck",
                    }
                if (
                    last_cycle_id == cycle_id
                    and last_batch_ts > 0
                    and now_value - last_batch_ts < min_interval_sec
                ):
                    next_after = last_batch_ts + min_interval_sec
                    repair_state["last_repair_outcome"] = (
                        "persistent_repair_batch_deferred"
                    )
                    return {
                        **recheck_fields,
                        "ws_repair_batch_queued": False,
                        "ws_repair_batch_reason": "persistent_repair_batch_interval_active",
                        "ws_repair_batch_next_after_epoch": f"{next_after:.3f}",
                        "ws_repair_batch_min_interval_sec": round(min_interval_sec, 3),
                    }
                source_key = "scanner_persistent_ws_gap_recovery"
                pending_scanner_ws_persistent_repair.setdefault(source_key, set()).add(
                    norm_code
                )
                repair_state["last_repair_batch_ts"] = now_value
                repair_state["last_repair_cycle_id"] = cycle_id
                repair_state["last_repair_outcome"] = "persistent_repair_batch_queued"
                repair_state["last_subscription_recheck_status"] = recheck_fields.get(
                    "ws_subscription_recheck_status"
                )
                return {
                    **recheck_fields,
                    "ws_repair_batch_queued": True,
                    "ws_repair_batch_reason": "persistent_ws_gap_repair_batch_queued",
                    "ws_repair_batch_source": source_key,
                    "ws_repair_batch_force": True,
                    "ws_repair_batch_min_interval_sec": round(min_interval_sec, 3),
                }

            def _scanner_rest_quote_recovery_options(stock_value, recovery_now_ts):
                nonlocal scanner_rest_quote_fallback_loop_count
                allowed = _scanner_rest_quote_fallback_allowed_for_ws_gap(stock_value)
                deferred_reason = ""
                if _scanner_rest_quote_fallback_due(
                    stock_value,
                    recovery_now_ts,
                    allow_early_rest_fallback=allowed,
                ):
                    if (
                        scanner_rest_quote_fallback_loop_count
                        >= scanner_rest_quote_fallback_loop_limit
                    ):
                        deferred_reason = "rest_quote_loop_budget_deferred"
                    else:
                        scanner_rest_quote_fallback_loop_count += 1
                return allowed, deferred_reason

            def _scanner_market_data_enrichment_for_fast_precheck(
                stock_value,
                code_value,
                ws_snapshot,
                now_value,
            ):
                nonlocal scanner_rest_quote_fallback_loop_count
                ws_snapshot = ws_snapshot if isinstance(ws_snapshot, dict) else {}
                if not _scanner_market_data_enrichment_candidate(
                    stock_value, ws_snapshot, now_value
                ):
                    return ws_snapshot, {}
                cached = _scanner_market_data_enrichment_cached(code_value, now_value)
                packet_fields = {
                    "market_data_enrichment_attempted": True,
                    "market_data_enrichment_packet_source": "scanner_fast_precheck",
                }
                if cached:
                    enriched_ws, envelope_fields = build_market_data_enrichment(
                        ws_data=ws_snapshot,
                        rest_orderbook=cached.get("rest_orderbook"),
                        rest_signed_ticks=cached.get("rest_signed_ticks"),
                        candidate_metadata={
                            "source_signature": (stock_value or {}).get(
                                "source_signature"
                            )
                            or (stock_value or {}).get("scanner_promotion_reason")
                            or "scanner_fast_precheck",
                        },
                        now_ts=now_value,
                        prefer_freshest_source=True,
                    )
                    packet_fields.update(envelope_fields)
                    packet_fields["market_data_enrichment_packet_source"] = (
                        "scanner_cache"
                    )
                    enriched_ws.update(packet_fields)
                    return enriched_ws, packet_fields
                if (
                    scanner_rest_quote_fallback_loop_count
                    >= scanner_rest_quote_fallback_loop_limit
                ):
                    enriched_ws, envelope_fields = build_market_data_enrichment(
                        ws_data=ws_snapshot,
                        candidate_metadata={
                            "source_signature": "scanner_loop_budget_deferred"
                        },
                        now_ts=now_value,
                    )
                    packet_fields.update(envelope_fields)
                    packet_fields["market_data_enrichment_fetch_reason"] = (
                        "rest_quote_loop_budget_deferred"
                    )
                    enriched_ws.update(packet_fields)
                    return enriched_ws, packet_fields
                rate_allowed, rate_reason = _scanner_rest_quote_fallback_rate_limit(
                    now_value,
                    priority=True,
                )
                if not rate_allowed:
                    enriched_ws, envelope_fields = build_market_data_enrichment(
                        ws_data=ws_snapshot,
                        candidate_metadata={"source_signature": "scanner_rate_limited"},
                        now_ts=now_value,
                    )
                    packet_fields.update(envelope_fields)
                    packet_fields["market_data_enrichment_fetch_reason"] = rate_reason
                    enriched_ws.update(packet_fields)
                    return enriched_ws, packet_fields
                scanner_rest_quote_fallback_loop_count += 1
                rest_orderbook, rest_signed_ticks, fetch_fields = (
                    _fetch_scanner_market_data_enrichment_packet(
                        code_value,
                        now_value,
                    )
                )
                enriched_ws, envelope_fields = build_market_data_enrichment(
                    ws_data=ws_snapshot,
                    rest_orderbook=rest_orderbook,
                    rest_signed_ticks=rest_signed_ticks,
                    candidate_metadata={
                        "source_signature": (stock_value or {}).get("source_signature")
                        or (stock_value or {}).get("scanner_promotion_reason")
                        or "scanner_fast_precheck",
                    },
                    now_ts=now_value,
                    prefer_freshest_source=True,
                )
                packet_fields.update(envelope_fields)
                packet_fields.update(fetch_fields)
                packet_fields["market_data_enrichment_rate_limit_reason"] = rate_reason
                enriched_ws.update(packet_fields)
                return enriched_ws, packet_fields

            def _scanner_no_trade_hot_slot_eviction_allowed():
                nonlocal scanner_no_trade_eviction_loop_count
                if scanner_no_trade_eviction_loop_limit <= 0:
                    return False
                if (
                    scanner_no_trade_eviction_loop_count
                    >= scanner_no_trade_eviction_loop_limit
                ):
                    return False
                scanner_no_trade_eviction_loop_count += 1
                return True

            def _scanner_queue_lag_hot_slot_eviction_allowed():
                nonlocal scanner_queue_lag_eviction_loop_count
                if scanner_queue_lag_eviction_loop_limit <= 0:
                    return False
                if (
                    scanner_queue_lag_eviction_loop_count
                    >= scanner_queue_lag_eviction_loop_limit
                ):
                    return False
                scanner_queue_lag_eviction_loop_count += 1
                return True

            def _scanner_full_eval_deferred_hot_slot_eviction_allowed():
                nonlocal scanner_full_eval_deferred_eviction_loop_count
                if scanner_full_eval_deferred_eviction_loop_limit <= 0:
                    return False
                if (
                    scanner_full_eval_deferred_eviction_loop_count
                    >= scanner_full_eval_deferred_eviction_loop_limit
                ):
                    return False
                scanner_full_eval_deferred_eviction_loop_count += 1
                return True

            def _apply_subscription_recheck_snapshot_if_ready(
                ws_snapshot, recovery_fields, *, phase
            ):
                fields = dict(recovery_fields or {})
                recheck_snapshot = fields.pop("_ws_subscription_recheck_snapshot", None)
                if (
                    fields.get("ws_recovery_outcome")
                    != "ws_snapshot_arrived_after_subscription_recheck"
                    or not isinstance(recheck_snapshot, dict)
                    or _safe_int(recheck_snapshot.get("curr"), 0) <= 0
                ):
                    return ws_snapshot, fields, False
                recheck_snapshot = dict(recheck_snapshot)
                recheck_age_sec = _safe_float(
                    fields.get("ws_subscription_recheck_age_sec"), 999999.0
                )
                recheck_fresh_sec = _safe_float(
                    fields.get("ws_subscription_recheck_fresh_sec"), 0.0
                )
                if (
                    str(fields.get("ws_subscription_recheck_status") or "")
                    == "subscribed_fresh_snapshot"
                    and recheck_fresh_sec > 0
                    and recheck_age_sec <= recheck_fresh_sec
                ):
                    recheck_snapshot["scanner_subscription_recheck_entry_relief"] = True
                    recheck_snapshot["scanner_subscription_recheck_age_sec"] = round(
                        recheck_age_sec, 3
                    )
                    recheck_snapshot["scanner_subscription_recheck_fresh_sec"] = round(
                        recheck_fresh_sec, 3
                    )
                fields["ws_subscription_recheck_snapshot_applied"] = True
                fields["ws_subscription_recheck_snapshot_apply_phase"] = str(
                    phase or "unknown"
                )
                return recheck_snapshot, fields, True

            def _flush_pending_scanner_ws_reg():
                if pending_scanner_ws_reg:
                    for source_key, code_set in list(pending_scanner_ws_reg.items()):
                        if code_set:
                            event_bus.publish(
                                "COMMAND_WS_REG",
                                {"codes": sorted(code_set), "source": source_key},
                            )
                    pending_scanner_ws_reg.clear()
                if pending_scanner_ws_persistent_repair:
                    for source_key, code_set in list(
                        pending_scanner_ws_persistent_repair.items()
                    ):
                        if code_set:
                            event_bus.publish(
                                "COMMAND_WS_REG",
                                {
                                    "codes": sorted(code_set),
                                    "source": source_key,
                                    "force": True,
                                    "repair_cycle": "persistent_ws_gap",
                                },
                            )
                    pending_scanner_ws_persistent_repair.clear()

            def _flush_delayed_scanner_heavy_eval():
                nonlocal scanner_heavy_eval_flushed
                if scanner_heavy_eval_flushed:
                    return
                scanner_heavy_eval_flushed = True
                for (
                    delayed_stock,
                    delayed_code,
                    delayed_ws_data,
                    queue_enter_epoch,
                ) in delayed_scanner_heavy_eval:
                    if delayed_stock.get("status") != "WATCHING":
                        continue
                    eval_ws_data = delayed_ws_data
                    opening_rotation_handoff_allowed = False
                    if _is_scanner_watching_target(delayed_stock):
                        recheck_snapshot, recheck_fields = (
                            _scanner_ws_subscription_recheck_snapshot_and_fields(
                                WS_MANAGER,
                                delayed_code,
                                delayed_ws_data,
                                now_ts=time.time(),
                            )
                        )
                        heavy_recheck_age_sec = _safe_float(
                            recheck_fields.get("ws_subscription_recheck_age_sec"),
                            999999.0,
                        )
                        heavy_recheck_fresh_sec = (
                            _scanner_heavy_eval_recheck_fresh_sec()
                        )
                        heavy_recheck_repair_needed = (
                            bool(recheck_fields.get("ws_subscription_repair_needed"))
                            or heavy_recheck_age_sec > heavy_recheck_fresh_sec
                        )
                        opening_rotation_handoff_fields = sniper_state_handlers._opening_rotation_upstream_handoff_fields(
                            delayed_stock,
                            delayed_ws_data,
                            now_ts=time.time(),
                        )
                        opening_rotation_handoff_allowed = bool(
                            opening_rotation_handoff_fields.get(
                                "opening_rotation_upstream_handoff_allowed"
                            )
                        )
                        if (
                            heavy_recheck_repair_needed
                            and opening_rotation_handoff_allowed
                        ):
                            eval_ws_data = delayed_ws_data
                            delayed_stock[
                                "_opening_rotation_upstream_handoff_applied"
                            ] = True
                            delayed_stock[
                                "_opening_rotation_upstream_handoff_reason"
                            ] = opening_rotation_handoff_fields.get(
                                "opening_rotation_upstream_handoff_reason"
                            )
                            delayed_stock[
                                "_scanner_heavy_eval_ws_snapshot_refresh_status"
                            ] = "opening_rotation_quote_envelope_pending"
                            delayed_stock[
                                "_scanner_heavy_eval_ws_snapshot_apply_phase"
                            ] = "opening_rotation_bounded_handoff"
                        elif heavy_recheck_repair_needed:
                            recheck_fields["scanner_heavy_eval_recheck_fresh_sec"] = (
                                round(
                                    heavy_recheck_fresh_sec,
                                    3,
                                )
                            )
                            recheck_fields["scanner_heavy_eval_recheck_age_sec"] = (
                                round(heavy_recheck_age_sec, 3)
                                if heavy_recheck_age_sec < 999999.0
                                else "not_available_ws_age_sec"
                            )
                            recheck_fields[
                                "scanner_heavy_eval_recheck_repair_needed"
                            ] = True
                            rest_quote_allowed, rest_quote_deferred_reason = (
                                _scanner_rest_quote_recovery_options(
                                    delayed_stock,
                                    time.time(),
                                )
                            )
                            _recovered_ws_data, recovery_fields = (
                                _recover_missing_ws_snapshot(
                                    delayed_stock,
                                    delayed_code,
                                    time.time(),
                                    recheck_snapshot or delayed_ws_data,
                                    ws_reg_source="scanner_heavy_eval_stale_ws_recovery",
                                    publish_ws_reg=False,
                                    allow_early_rest_fallback=rest_quote_allowed,
                                    rest_quote_deferred_reason=rest_quote_deferred_reason,
                                    cycle_state_store=scanner_ws_repair_cycle_state_by_code,
                                )
                            )
                            if recovery_fields.get("ws_repair_batch_required"):
                                recovery_fields.update(
                                    _queue_scanner_ws_persistent_repair(
                                        delayed_stock,
                                        delayed_code,
                                        recheck_snapshot or delayed_ws_data,
                                        recovery_fields,
                                    )
                                )
                            elif recovery_fields.get(
                                "ws_repair_cycle_reg_allowed", True
                            ):
                                _queue_scanner_ws_reg(
                                    delayed_code,
                                    "scanner_heavy_eval_stale_ws_recovery",
                                )
                            (
                                recovered_eval_ws_data,
                                recovery_fields,
                                recovery_snapshot_applied,
                            ) = _apply_subscription_recheck_snapshot_if_ready(
                                _recovered_ws_data
                                or recheck_snapshot
                                or delayed_ws_data,
                                recovery_fields,
                                phase="heavy_eval_repair",
                            )
                            if recovery_snapshot_applied:
                                eval_ws_data = recovered_eval_ws_data
                                delayed_stock[
                                    "_scanner_heavy_eval_ws_snapshot_refreshed"
                                ] = True
                                delayed_stock[
                                    "_scanner_heavy_eval_ws_snapshot_refresh_status"
                                ] = (
                                    recovery_fields.get(
                                        "ws_subscription_recheck_status"
                                    )
                                    or "fresh_snapshot_recovered"
                                )
                                delayed_stock[
                                    "_scanner_heavy_eval_ws_snapshot_apply_phase"
                                ] = "heavy_eval_repair"
                            else:
                                heavy_recheck_skip_fields = {
                                    **recheck_fields,
                                    **recovery_fields,
                                }
                                _defer_scanner_watching_runtime_skip(
                                    delayed_stock,
                                    delayed_code,
                                    skip_reason="scanner_heavy_eval_stale_snapshot_recheck",
                                    now_ts=time.time(),
                                    ws_data=recheck_snapshot or delayed_ws_data,
                                    ws_manager_available=bool(WS_MANAGER),
                                    **heavy_recheck_skip_fields,
                                )
                                continue
                        if (
                            not recheck_fields.get(
                                "ws_subscription_repair_needed", True
                            )
                            and _safe_int(recheck_snapshot.get("curr"), 0) > 0
                        ):
                            eval_ws_data = recheck_snapshot
                            delayed_stock[
                                "_scanner_heavy_eval_ws_snapshot_refreshed"
                            ] = True
                            delayed_stock[
                                "_scanner_heavy_eval_ws_snapshot_refresh_status"
                            ] = (
                                recheck_fields.get("ws_subscription_recheck_status")
                                or "fresh_snapshot_rechecked"
                            )
                    if (
                        delayed_stock.get("_scanner_fast_precheck_result")
                        == "eligible_for_heavy_entry_eval"
                    ):
                        _defer_emit_scanner_heavy_eval_lag(
                            delayed_stock,
                            delayed_code,
                            now_value=time.time(),
                            queue_enter_epoch=queue_enter_epoch,
                        )
                    _scanner_watch_reset_full_eval_deferred_eviction_state(
                        delayed_stock
                    )
                    _flush_deferred_scanner_pipeline_events()
                    handler_now_ts = (
                        time.time() if opening_rotation_handoff_allowed else now_ts
                    )
                    handler_now_dt = (
                        datetime.fromtimestamp(handler_now_ts)
                        if opening_rotation_handoff_allowed
                        else now
                    )
                    handle_watching_state(
                        delayed_stock,
                        delayed_code,
                        eval_ws_data,
                        admin_id,
                        now_ts=handler_now_ts,
                        now_dt=handler_now_dt,
                        radar=radar,
                        ai_engine=ai_engine,
                    )
                    if _is_scanner_watching_target(delayed_stock):
                        delayed_stock["_scanner_last_full_eval_epoch"] = time.time()
                        _maybe_expire_scanner_watch_after_full_eval(
                            delayed_stock,
                            delayed_code,
                            targets,
                            now_ts=time.time(),
                            emit_event_fn=_defer_scanner_entry_pipeline_log,
                        )

            for stock in queue_context["iteration_targets"]:
                code = str(stock.get("code", "")).strip()[:6]
                status = stock.get("status")

                if (
                    scanner_precheck_seen
                    and not scanner_heavy_eval_flushed
                    and not _is_scanner_watching_target(stock)
                ):
                    _flush_delayed_scanner_heavy_eval()

                if status == "BUY_ORDERED":
                    handle_buy_ordered_state(stock, code)
                    continue

                if status == "SELL_ORDERED":
                    handle_sell_ordered_state(stock, code)
                    continue

                if (
                    _is_scanner_watching_target(stock)
                    and code in scanner_ws_snapshot_cache
                ):
                    ws_data = scanner_ws_snapshot_cache.get(code) or {}
                else:
                    ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
                revive_quote_barrier_fields = {}
                if _is_scanner_watching_target(stock):
                    ws_data, revive_quote_barrier_fields = (
                        _discard_pre_revive_scanner_snapshot(
                            stock,
                            ws_data,
                            now_ts=now_ts,
                        )
                    )
                if not ws_data or ws_data.get("curr", 0) == 0:
                    if status == "WATCHING":
                        recheck_snapshot_applied = False
                        rest_quote_allowed, rest_quote_deferred_reason = (
                            _scanner_rest_quote_recovery_options(stock, now_ts)
                            if _is_scanner_watching_target(stock)
                            else (False, "")
                        )
                        ws_data, recovery_fields = (
                            _recover_missing_ws_snapshot(
                                stock,
                                code,
                                now_ts,
                                ws_data,
                                publish_ws_reg=False,
                                allow_early_rest_fallback=rest_quote_allowed,
                                rest_quote_deferred_reason=rest_quote_deferred_reason,
                                cycle_state_store=scanner_ws_repair_cycle_state_by_code,
                            )
                            if _is_scanner_watching_target(stock)
                            else (ws_data, {})
                        )
                        if _is_scanner_watching_target(stock):
                            recovery_fields = {
                                **revive_quote_barrier_fields,
                                **recovery_fields,
                            }
                            if recovery_fields.get("ws_repair_batch_required"):
                                recovery_fields.update(
                                    _queue_scanner_ws_persistent_repair(
                                        stock,
                                        code,
                                        ws_data,
                                        recovery_fields,
                                    )
                                )
                            elif recovery_fields.get(
                                "ws_repair_cycle_reg_allowed", True
                            ):
                                _queue_scanner_ws_reg(
                                    code, "scanner_watching_ws_snapshot_recovery"
                                )
                            ws_data, recovery_fields, recheck_snapshot_applied = (
                                _apply_subscription_recheck_snapshot_if_ready(
                                    ws_data,
                                    recovery_fields,
                                    phase="watching_missing_or_zero",
                                )
                            )
                            recovery_fields = (
                                _scanner_rest_quote_entry_realtime_outcome_fields(
                                    recovery_fields
                                )
                            )
                        if (
                            recovery_fields.get("ws_recovery_outcome")
                            == "rest_quote_applied"
                        ):
                            _scanner_watch_reset_stale_eviction_state(stock)
                            _defer_scanner_watching_runtime_skip(
                                stock,
                                code,
                                skip_reason="ws_snapshot_missing_or_zero_recovered",
                                now_ts=now_ts,
                                ws_data=ws_data,
                                ws_manager_available=bool(WS_MANAGER),
                                throttle_sec=0,
                                **recovery_fields,
                            )
                        elif (
                            recovery_fields.get("ws_recovery_outcome")
                            == "ws_snapshot_arrived_after_subscription_recheck"
                            and recheck_snapshot_applied
                        ):
                            _scanner_watch_reset_stale_eviction_state(stock)
                            _defer_scanner_watching_runtime_skip(
                                stock,
                                code,
                                skip_reason="ws_snapshot_missing_or_zero_recovered",
                                now_ts=now_ts,
                                ws_data=ws_data,
                                ws_manager_available=bool(WS_MANAGER),
                                throttle_sec=0,
                                **recovery_fields,
                            )
                        if not ws_data or ws_data.get("curr", 0) == 0:
                            _defer_scanner_watching_runtime_skip(
                                stock,
                                code,
                                skip_reason="ws_snapshot_missing_or_zero",
                                now_ts=now_ts,
                                ws_data=ws_data,
                                ws_manager_available=bool(WS_MANAGER),
                                **recovery_fields,
                            )
                            _maybe_expire_scanner_watch_for_stale(
                                stock,
                                code,
                                targets,
                                now_ts=now_ts,
                                stale_reason="ws_snapshot_missing_or_zero",
                                recovery_fields=recovery_fields,
                                emit_event_fn=_defer_scanner_entry_pipeline_log,
                            )
                            continue
                    else:
                        if status == "HOLDING":
                            handle_holding_state(
                                stock,
                                code,
                                ws_data or {},
                                admin_id,
                                current_market_regime,
                                radar=radar,
                                ai_engine=ai_engine,
                                now_ts=now_ts,
                                now_dt=now,
                            )
                        continue

                if _is_scanner_watching_target(stock):
                    no_trade_decision = _scanner_watch_eviction_decision_from_no_trade(
                        stock,
                        ws_data,
                        now_ts=now_ts,
                    )
                    if (
                        no_trade_decision.get("should_evict")
                        and _scanner_no_trade_hot_slot_eviction_allowed()
                    ):
                        if _expire_scanner_watch_target(
                            stock,
                            code,
                            targets,
                            decision=no_trade_decision,
                            emit_event_fn=_defer_scanner_entry_pipeline_log,
                        ):
                            continue

                if (
                    sniper_state_handlers._is_scalp_simulator_target(stock)
                    and status == sniper_state_handlers.SCALP_SIM_PENDING_STATUS
                ):
                    sniper_state_handlers.handle_scalp_simulator_pending_entry(
                        stock,
                        code,
                        ws_data,
                        now_ts=now_ts,
                    )
                    continue

                if status == "WATCHING":
                    if _is_scanner_watching_target(stock):
                        scanner_precheck_seen = True
                        heavy_queue_enter_epoch = time.time()
                        stock.update(
                            {
                                f"_scanner_{key}": value
                                for key, value in _scanner_rising_entry_relief_fields(
                                    stock,
                                    reason="precheck_observation",
                                    budget_source="standard",
                                ).items()
                            }
                        )
                        ws_data, market_data_enrichment_fields = (
                            _scanner_market_data_enrichment_for_fast_precheck(
                                stock,
                                code,
                                ws_data,
                                heavy_queue_enter_epoch,
                            )
                        )
                        if market_data_enrichment_fields:
                            stock["_scanner_market_data_enrichment_fields"] = dict(
                                market_data_enrichment_fields
                            )
                            stock["_scanner_market_data_enrichment_ws_data"] = dict(
                                ws_data or {}
                            )
                            stock["_scanner_market_data_enrichment_stored_at"] = (
                                heavy_queue_enter_epoch
                            )
                        _defer_emit_scanner_fast_precheck(
                            stock,
                            code,
                            now_value=heavy_queue_enter_epoch,
                            ws_snapshot=ws_data,
                            queue_rank=queue_context["queue_rank_by_obj"].get(
                                id(stock), 0
                            ),
                            scanner_queue_rank=queue_context["scanner_rank_by_obj"].get(
                                id(stock), 0
                            ),
                            watching_count=queue_context["watching_count"],
                            scanner_watching_count=queue_context[
                                "scanner_watching_count"
                            ],
                        )
                        queue_lag_fields = _defer_emit_scanner_runtime_queue_lag(
                            stock,
                            code,
                            now_value=heavy_queue_enter_epoch,
                            queue_rank=queue_context["queue_rank_by_obj"].get(
                                id(stock), 0
                            ),
                            scanner_queue_rank=queue_context["scanner_rank_by_obj"].get(
                                id(stock), 0
                            ),
                            watching_count=queue_context["watching_count"],
                            scanner_watching_count=queue_context[
                                "scanner_watching_count"
                            ],
                            real_holding_count=queue_context["real_holding_count"],
                            non_real_holding_count=queue_context[
                                "non_real_holding_count"
                            ],
                            pre_scanner_runtime_count=queue_context[
                                "pre_scanner_runtime_count"
                            ],
                            loop_started_epoch=queue_context["loop_started_epoch"],
                        )
                        fast_precheck_result = str(
                            stock.get("_scanner_fast_precheck_result") or ""
                        )
                        fast_precheck_reason = str(
                            stock.get("_scanner_fast_precheck_reason") or ""
                        )
                        recovery_fields = {}
                        fast_precheck_stale_like = (
                            fast_precheck_reason in SCANNER_WATCH_EVICTION_STALE_REASONS
                        )
                        if (
                            fast_precheck_result != "eligible_for_heavy_entry_eval"
                            and queue_lag_fields
                            and _scanner_queue_lag_eviction_allowed_before_recovery(
                                fast_precheck_reason
                            )
                        ):
                            queue_lag_decision = (
                                _scanner_watch_eviction_decision_from_queue_lag(
                                    stock,
                                    now_ts=heavy_queue_enter_epoch,
                                    queue_lag_fields=queue_lag_fields,
                                )
                            )
                            if (
                                queue_lag_decision.get("should_evict")
                                and _scanner_queue_lag_hot_slot_eviction_allowed()
                                and _expire_scanner_watch_target(
                                    stock,
                                    code,
                                    targets,
                                    decision=queue_lag_decision,
                                    emit_event_fn=_defer_scanner_entry_pipeline_log,
                                )
                            ):
                                continue
                        if (
                            fast_precheck_result != "eligible_for_heavy_entry_eval"
                            and fast_precheck_stale_like
                        ):
                            rest_quote_allowed, rest_quote_deferred_reason = (
                                _scanner_rest_quote_recovery_options(
                                    stock,
                                    heavy_queue_enter_epoch,
                                )
                            )
                            ws_data, recovery_fields = _recover_missing_ws_snapshot(
                                stock,
                                code,
                                heavy_queue_enter_epoch,
                                ws_data,
                                ws_reg_source="scanner_fast_precheck_stale_ws_recovery",
                                publish_ws_reg=False,
                                allow_early_rest_fallback=rest_quote_allowed,
                                rest_quote_deferred_reason=rest_quote_deferred_reason,
                                cycle_state_store=scanner_ws_repair_cycle_state_by_code,
                            )
                            if recovery_fields.get("ws_repair_batch_required"):
                                recovery_fields.update(
                                    _queue_scanner_ws_persistent_repair(
                                        stock,
                                        code,
                                        ws_data,
                                        recovery_fields,
                                    )
                                )
                            elif recovery_fields.get(
                                "ws_repair_cycle_reg_allowed", True
                            ):
                                _queue_scanner_ws_reg(
                                    code, "scanner_fast_precheck_stale_ws_recovery"
                                )
                            ws_data, recovery_fields, recheck_snapshot_applied = (
                                _apply_subscription_recheck_snapshot_if_ready(
                                    ws_data,
                                    recovery_fields,
                                    phase="fast_precheck",
                                )
                            )
                            recovery_fields = (
                                _scanner_rest_quote_entry_realtime_outcome_fields(
                                    recovery_fields
                                )
                            )
                            if recovery_fields.get("ws_recovery_outcome") in {
                                "rest_quote_applied",
                                "ws_snapshot_arrived_after_subscription_recheck",
                            }:
                                _scanner_watch_reset_stale_eviction_state(stock)
                                _defer_scanner_watching_runtime_skip(
                                    stock,
                                    code,
                                    skip_reason=(
                                        "scanner_fast_precheck_subscription_recheck_snapshot_applied"
                                        if recheck_snapshot_applied
                                        else "scanner_fast_precheck_stale_ws_recovered"
                                    ),
                                    now_ts=heavy_queue_enter_epoch,
                                    ws_data=ws_data,
                                    ws_manager_available=bool(WS_MANAGER),
                                    throttle_sec=0,
                                    queue_rank=queue_context["queue_rank_by_obj"].get(
                                        id(stock), 0
                                    ),
                                    scanner_queue_rank=queue_context[
                                        "scanner_rank_by_obj"
                                    ].get(id(stock), 0),
                                    watching_count=queue_context["watching_count"],
                                    scanner_watching_count=queue_context[
                                        "scanner_watching_count"
                                    ],
                                    fast_precheck_result=fast_precheck_result or "-",
                                    fast_precheck_reason=fast_precheck_reason or "-",
                                    **recovery_fields,
                                )
                                _defer_emit_scanner_fast_precheck(
                                    stock,
                                    code,
                                    now_value=heavy_queue_enter_epoch,
                                    ws_snapshot=ws_data,
                                    queue_rank=queue_context["queue_rank_by_obj"].get(
                                        id(stock), 0
                                    ),
                                    scanner_queue_rank=queue_context[
                                        "scanner_rank_by_obj"
                                    ].get(id(stock), 0),
                                    watching_count=queue_context["watching_count"],
                                    scanner_watching_count=queue_context[
                                        "scanner_watching_count"
                                    ],
                                    throttle_sec=0,
                                )
                                fast_precheck_result = str(
                                    stock.get("_scanner_fast_precheck_result") or ""
                                )
                                fast_precheck_reason = str(
                                    stock.get("_scanner_fast_precheck_reason") or ""
                                )
                        if fast_precheck_reason != "scanner_ws_stale_backoff_active":
                            _reset_scanner_ws_backoff_watch_retention(stock)
                        if (
                            fast_precheck_result == "eligible_for_heavy_entry_eval"
                            and fast_precheck_reason
                            == "rising_rest_quote_recovery_without_realtime_strength"
                        ):
                            price_only_recovery_fields = dict(recovery_fields or {})
                            price_only_recovery_fields.update(
                                {
                                    "ws_recovery_outcome": (
                                        "source_quality_unresolved_price_only_rest_quote"
                                    ),
                                    "source_quality_detail_route": (
                                        "price_only_rest_quote_strength_history_missing"
                                    ),
                                    "rest_quote_price_recovery_only": True,
                                    "entry_evaluable_fresh_after_rest_quote": False,
                                    "scanner_source_quality_reallocation_candidate": True,
                                }
                            )
                            if _maybe_expire_scanner_watch_for_stale(
                                stock,
                                code,
                                targets,
                                now_ts=heavy_queue_enter_epoch,
                                stale_reason=fast_precheck_reason,
                                recovery_fields=price_only_recovery_fields,
                                emit_event_fn=_defer_scanner_entry_pipeline_log,
                            ):
                                continue
                        if fast_precheck_result != "eligible_for_heavy_entry_eval":
                            fast_precheck_budget_decision = None
                            if fast_precheck_result == "budget_reallocated":
                                fast_precheck_budget_decision = _scanner_watch_eviction_decision_from_fast_precheck_budget(
                                    stock,
                                    now_ts=heavy_queue_enter_epoch,
                                )
                            skip_reason = (
                                "scanner_fast_precheck_budget_reallocated"
                                if fast_precheck_result == "budget_reallocated"
                                else (
                                    "scanner_fast_precheck_stability_pending"
                                    if fast_precheck_result == "stability_pending"
                                    else (
                                        "scanner_fast_precheck_source_quality_blocked"
                                        if fast_precheck_result
                                        == "source_quality_blocked"
                                        else "scanner_fast_precheck_not_eligible"
                                    )
                                )
                            )
                            skip_recovery_fields = dict(recovery_fields or {})
                            if fast_precheck_budget_decision:
                                for field_name in (
                                    "retention_active",
                                    "retention_reason",
                                    "ws_backoff_retention_active",
                                    "ws_backoff_retention_reason",
                                    "ws_backoff_retention_first_epoch",
                                    "ws_backoff_retention_age_sec",
                                    "ws_backoff_retention_min_sec",
                                    "ws_backoff_retention_max_sec",
                                    "ws_backoff_retention_attempt_count",
                                    "ws_backoff_retention_min_count",
                                    "ws_backoff_until",
                                ):
                                    if field_name in fast_precheck_budget_decision:
                                        skip_recovery_fields[field_name] = (
                                            fast_precheck_budget_decision[field_name]
                                        )
                            skip_recovery_fields.setdefault(
                                "ws_recovery_action",
                                (
                                    "ws_reg_reissued"
                                    if fast_precheck_stale_like
                                    else "not_applicable_ws_recovery_action"
                                ),
                            )
                            skip_recovery_fields.setdefault(
                                "ws_recovery_outcome",
                                (
                                    "ws_reg_reissued_waiting_snapshot"
                                    if fast_precheck_stale_like
                                    else "not_applicable_ws_recovery_outcome"
                                ),
                            )
                            skip_recovery_fields.setdefault(
                                "ws_recovery_miss_count",
                                "not_applicable_ws_recovery_miss_count",
                            )
                            if (
                                skip_recovery_fields.get(
                                    "ws_subscription_recheck_snapshot_applied"
                                )
                                and fast_precheck_stale_like
                            ):
                                skip_recovery_fields[
                                    "subscription_alive_but_entry_stale"
                                ] = True
                                skip_recovery_fields[
                                    "entry_freshness_after_subscription_recheck"
                                ] = fast_precheck_reason
                                skip_recovery_fields[
                                    "entry_evaluable_fresh_after_subscription_recheck"
                                ] = False
                            _defer_scanner_watching_runtime_skip(
                                stock,
                                code,
                                skip_reason=skip_reason,
                                now_ts=heavy_queue_enter_epoch,
                                ws_data=ws_data,
                                ws_manager_available=bool(WS_MANAGER),
                                queue_rank=queue_context["queue_rank_by_obj"].get(
                                    id(stock), 0
                                ),
                                scanner_queue_rank=queue_context[
                                    "scanner_rank_by_obj"
                                ].get(id(stock), 0),
                                watching_count=queue_context["watching_count"],
                                scanner_watching_count=queue_context[
                                    "scanner_watching_count"
                                ],
                                fast_precheck_result=fast_precheck_result or "-",
                                fast_precheck_reason=fast_precheck_reason or "-",
                                fast_precheck_fields=dict(
                                    stock.get("_scanner_fast_precheck_fields") or {}
                                ),
                                **skip_recovery_fields,
                            )
                            if fast_precheck_stale_like:
                                _maybe_expire_scanner_watch_for_stale(
                                    stock,
                                    code,
                                    targets,
                                    now_ts=heavy_queue_enter_epoch,
                                    stale_reason=fast_precheck_reason,
                                    recovery_fields=recovery_fields,
                                    emit_event_fn=_defer_scanner_entry_pipeline_log,
                                )
                            elif fast_precheck_result == "budget_reallocated":
                                if _maybe_expire_scanner_watch_for_fast_precheck_budget(
                                    stock,
                                    code,
                                    targets,
                                    now_ts=heavy_queue_enter_epoch,
                                    emit_event_fn=_defer_scanner_entry_pipeline_log,
                                    decision=fast_precheck_budget_decision,
                                ):
                                    continue
                                if bool(
                                    (fast_precheck_budget_decision or {}).get(
                                        "retention_active"
                                    )
                                ):
                                    continue
                            if queue_lag_fields:
                                queue_lag_decision = (
                                    _scanner_watch_eviction_decision_from_queue_lag(
                                        stock,
                                        now_ts=heavy_queue_enter_epoch,
                                        queue_lag_fields=queue_lag_fields,
                                    )
                                )
                                if (
                                    queue_lag_decision.get("should_evict")
                                    and _scanner_queue_lag_hot_slot_eviction_allowed()
                                    and _expire_scanner_watch_target(
                                        stock,
                                        code,
                                        targets,
                                        decision=queue_lag_decision,
                                        emit_event_fn=_defer_scanner_entry_pipeline_log,
                                    )
                                ):
                                    continue
                            continue
                        if queue_lag_fields:
                            _scanner_watch_eviction_decision_from_queue_lag(
                                stock,
                                now_ts=heavy_queue_enter_epoch,
                                queue_lag_fields=queue_lag_fields,
                            )
                        if _scanner_strength_recheck_waiting(
                            stock, now_ts=heavy_queue_enter_epoch
                        ):
                            _scanner_watch_reset_terminal_eviction_state(stock)
                            recheck_after_epoch = _safe_float(
                                stock.get(
                                    "entry_strength_momentum_recheck_after_epoch"
                                ),
                                0.0,
                            )
                            _defer_scanner_watching_runtime_skip(
                                stock,
                                code,
                                skip_reason="strength_momentum_stability_recheck_waiting",
                                now_ts=heavy_queue_enter_epoch,
                                ws_data=ws_data,
                                ws_manager_available=bool(WS_MANAGER),
                                queue_rank=queue_context["queue_rank_by_obj"].get(
                                    id(stock), 0
                                ),
                                scanner_queue_rank=queue_context[
                                    "scanner_rank_by_obj"
                                ].get(id(stock), 0),
                                watching_count=queue_context["watching_count"],
                                scanner_watching_count=queue_context[
                                    "scanner_watching_count"
                                ],
                                recheck_after_epoch=f"{recheck_after_epoch:.3f}",
                                recheck_wait_sec=round(
                                    max(
                                        0.0,
                                        recheck_after_epoch - heavy_queue_enter_epoch,
                                    ),
                                    3,
                                ),
                                recheck_attempt_count=_safe_int(
                                    stock.get("entry_strength_momentum_recheck_count"),
                                    0,
                                ),
                                recheck_reason=stock.get(
                                    "entry_strength_momentum_recheck_reason"
                                )
                                or "-",
                            )
                            continue
                        budget_source = "standard"
                        if scanner_full_eval_count >= scanner_full_eval_limit:
                            relief_allowed = (
                                scanner_rising_full_eval_relief_count
                                < scanner_rising_full_eval_extra_limit
                                and _scanner_is_rising_entry_relief_candidate(stock)
                            )
                            if relief_allowed:
                                budget_source = "rising_full_eval_relief"
                                scanner_rising_full_eval_relief_count += 1
                                stock.update(
                                    {
                                        f"_scanner_{key}": value
                                        for key, value in _scanner_rising_entry_relief_fields(
                                            stock,
                                            reason="rising_full_eval_relief_applied",
                                            budget_source=budget_source,
                                        ).items()
                                    }
                                )
                            else:
                                relief_reason = (
                                    "rising_full_eval_relief_budget_exhausted"
                                    if _scanner_is_rising_entry_relief_candidate(stock)
                                    else "not_rising_entry_relief_candidate"
                                )
                                if scanner_rising_full_eval_extra_limit <= 0:
                                    relief_reason = "rising_full_eval_relief_disabled"
                                stock.update(
                                    {
                                        f"_scanner_{key}": value
                                        for key, value in _scanner_rising_entry_relief_fields(
                                            stock,
                                            reason=relief_reason,
                                            budget_source="deferred_no_relief",
                                        ).items()
                                    }
                                )
                        if (
                            scanner_full_eval_count >= scanner_full_eval_limit
                            and budget_source != "rising_full_eval_relief"
                        ):
                            _scanner_watch_reset_terminal_eviction_state(stock)
                            full_eval_deferred_fields = {
                                "skip_reason": "scanner_full_eval_loop_budget_deferred",
                                "now_ts": heavy_queue_enter_epoch,
                                "ws_data": ws_data,
                                "ws_manager_available": bool(WS_MANAGER),
                                "queue_rank": queue_context["queue_rank_by_obj"].get(
                                    id(stock), 0
                                ),
                                "scanner_queue_rank": queue_context[
                                    "scanner_rank_by_obj"
                                ].get(id(stock), 0),
                                "watching_count": queue_context["watching_count"],
                                "scanner_watching_count": queue_context[
                                    "scanner_watching_count"
                                ],
                                "scanner_full_eval_base_limit": scanner_full_eval_base_limit,
                                "scanner_full_eval_limit": scanner_full_eval_limit,
                                "scanner_full_eval_count": scanner_full_eval_count,
                                "scanner_rising_full_eval_extra_limit": scanner_rising_full_eval_extra_limit,
                                "scanner_rising_full_eval_relief_count": scanner_rising_full_eval_relief_count,
                                "fast_precheck_result": fast_precheck_result or "-",
                                "fast_precheck_reason": fast_precheck_reason or "-",
                                **_scanner_common_watch_budget_priority_fields(stock),
                            }
                            full_eval_deferred_decision = _scanner_watch_eviction_decision_from_full_eval_deferred(
                                stock,
                                now_ts=heavy_queue_enter_epoch,
                                skip_fields=full_eval_deferred_fields,
                            )
                            full_eval_deferred_fields.update(
                                {
                                    "full_eval_deferred_eviction_reason": full_eval_deferred_decision.get(
                                        "eviction_reason",
                                        "not_available_full_eval_deferred_eviction_reason",
                                    ),
                                    "full_eval_deferred_should_evict": bool(
                                        full_eval_deferred_decision.get("should_evict")
                                    ),
                                    "full_eval_deferred_attempt_count": full_eval_deferred_decision.get(
                                        "eviction_attempt_count",
                                        0,
                                    ),
                                    "full_eval_deferred_first_observed_epoch": full_eval_deferred_decision.get(
                                        "full_eval_deferred_first_observed_epoch",
                                        "not_available_full_eval_deferred_first_observed_epoch",
                                    ),
                                    "full_eval_deferred_watch_age_sec": full_eval_deferred_decision.get(
                                        "full_eval_deferred_watch_age_sec",
                                        "not_available_full_eval_deferred_watch_age_sec",
                                    ),
                                    "full_eval_deferred_min_age_sec": full_eval_deferred_decision.get(
                                        "full_eval_deferred_min_age_sec",
                                        "not_available_full_eval_deferred_min_age_sec",
                                    ),
                                    "full_eval_deferred_min_count": full_eval_deferred_decision.get(
                                        "full_eval_deferred_min_count",
                                        "not_available_full_eval_deferred_min_count",
                                    ),
                                    "full_eval_deferred_anchor_field": full_eval_deferred_decision.get(
                                        "full_eval_deferred_anchor_field",
                                        "not_available_full_eval_deferred_anchor_field",
                                    ),
                                    "full_eval_deferred_state_source": full_eval_deferred_decision.get(
                                        "full_eval_deferred_state_source",
                                        "not_available_full_eval_deferred_state_source",
                                    ),
                                }
                            )
                            _defer_scanner_watching_runtime_skip(
                                stock,
                                code,
                                **full_eval_deferred_fields,
                            )
                            if (
                                full_eval_deferred_decision.get("should_evict")
                                and _scanner_full_eval_deferred_hot_slot_eviction_allowed()
                                and _expire_scanner_watch_target(
                                    stock,
                                    code,
                                    targets,
                                    decision=full_eval_deferred_decision,
                                    emit_event_fn=_defer_scanner_entry_pipeline_log,
                                )
                            ):
                                continue
                            continue
                        scanner_full_eval_count += 1
                        delayed_scanner_heavy_eval.append(
                            (stock, code, ws_data, heavy_queue_enter_epoch)
                        )
                        if scanner_full_eval_count >= scanner_full_eval_limit:
                            _flush_delayed_scanner_heavy_eval()
                        continue
                    handle_watching_state(
                        stock,
                        code,
                        ws_data,
                        admin_id,
                        now_ts=now_ts,
                        now_dt=now,
                        radar=radar,
                        ai_engine=ai_engine,
                    )
                    if _is_scanner_watching_target(stock):
                        stock["_scanner_last_full_eval_epoch"] = time.time()
                        if (
                            bool(stock.get("entry_strength_momentum_recheck_pending"))
                            and _scanner_is_rising_entry_relief_candidate(stock)
                            and str(
                                stock.get(
                                    "entry_strength_momentum_recheck_source_quality_block_reason"
                                )
                                or ""
                            )
                            .strip()
                            .lower()
                            == "stale_ws_snapshot"
                        ):
                            _queue_scanner_ws_reg(
                                code, "scanner_strength_recheck_stale_ws_recovery"
                            )
                        _maybe_expire_scanner_watch_after_full_eval(
                            stock,
                            code,
                            targets,
                            now_ts=time.time(),
                            emit_event_fn=_defer_scanner_entry_pipeline_log,
                        )
                elif status == "HOLDING":
                    holding_ai_engine = None if eod_ai_holding_fallback else ai_engine
                    handle_holding_state(
                        stock,
                        code,
                        ws_data,
                        admin_id,
                        current_market_regime,
                        now_ts=now_ts,
                        now_dt=now,
                        radar=radar,
                        ai_engine=holding_ai_engine,
                    )

            _flush_delayed_scanner_heavy_eval()
            _flush_pending_scanner_ws_reg()
            _flush_deferred_scanner_pipeline_events()
            _flush_deferred_scanner_skip_events()
            sniper_state_handlers.observe_rising_missed_nxt_post_block_samplers()

            targets[:] = [
                t for t in targets if t.get("status") not in ["COMPLETED", "EXPIRED"]
            ]
            if now_ts - getattr(run_sniper, "last_ws_prune_time", 0) >= 5:
                _prune_ws_subscriptions_for_inactive_targets(targets)
                run_sniper.last_ws_prune_time = now_ts

            # ── P0: 루프 계측 로그 (60초마다) ─────────────────────
            _loop_elapsed_ms = (time.time() - now_ts) * 1000
            _sleep_ms = 1000  # 현재 고정값, 후속 canary에서 변경
            _target_count = len(targets)
            _watching_count = len([t for t in targets if t.get("status") == "WATCHING"])
            _holding_count = len([t for t in targets if t.get("status") == "HOLDING"])
            _update_scalping_dynamic_watch_cap(
                _loop_elapsed_ms,
                now_ts=now_ts,
                buy_time_allowed=is_scalping_buy_time_allowed(now),
            )
            _update_scanner_full_eval_pressure(
                _loop_elapsed_ms,
                queue_context=queue_context,
                now_ts=now_ts,
                buy_time_allowed=is_scalping_buy_time_allowed(now),
            )
            global _LOOP_METRICS_LAST_LOG_TS
            if now_ts - _LOOP_METRICS_LAST_LOG_TS >= 60:
                log_info(
                    f"[LOOP_METRICS] "
                    f"loop_elapsed_ms={_loop_elapsed_ms:.1f} "
                    f"sleep_ms={_sleep_ms} "
                    f"db_active_targets_ms={_db_elapsed_ms:.1f} "
                    f"account_sync_ms={_acct_elapsed_ms:.1f} "
                    f"target_count={_target_count} "
                    f"watching={_watching_count} "
                    f"holding={_holding_count}"
                )
                _LOOP_METRICS_LAST_LOG_TS = now_ts

            time.sleep(1)

    except Exception as e:
        log_error(f"🔥 스나이퍼 루프 치명적 에러: {e}\n{traceback.format_exc()}")
        print(f"🔥 스나이퍼 루프 치명적 에러: {e}")
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {"message": f"🚨 [시스템 에러] 스나이퍼 엔진 치명적 에러: {e}"},
        )

    except KeyboardInterrupt:
        print("\n🛑 스나이퍼 매매 엔진 종료")

    finally:
        fast_exit_monitor.stop()
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
