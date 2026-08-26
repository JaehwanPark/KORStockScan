import asyncio
import concurrent.futures
import websockets
import json
import threading
import time
import copy
import os
import re
import shlex
from collections import OrderedDict, deque
from queue import Queue, Empty
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# 💡 [Level 1 & 2 적용] 독립 로거 및 싱글톤 이벤트 버스 임포트
from src.utils.logger import log_error
from src.core.event_bus import EventBus
from src.utils.constants import CONFIG_PATH, DEV_PATH, TRADING_RULES
from src.database.db_manager import is_swing_real_watching_enabled
from src.engine.bd_fbuy_accum_pre_scanner import write_ws_snapshot
from src.engine.monitoring.market_halt_windows import append_market_session_event
from src.engine.sniper_time import (
    describe_scalping_buy_windows,
    is_scalping_prewarm_time_allowed,
    is_scalping_buy_time_allowed,
    scalping_buy_time_block_reason,
)
from src.engine.scalping.micro_estimator_state import (
    DEFAULT_STORE as MICRO_ESTIMATOR_STORE,
)
from src.engine.scalping.limit_down_watch import observe_raw_market_data
from src.trading.entry.orderbook_stability_observer import ORDERBOOK_STABILITY_OBSERVER


class _LoginAckFailure(RuntimeError):
    def __init__(self, code, message):
        self.code = str(code or "").strip()
        self.message = str(message or "").strip()
        super().__init__(
            f"LOGIN ACK failed code={self.code or '?'} msg={self.message or '로그인 실패'}"
        )


def _load_system_config():
    """웹소켓 매니저 전용 설정 로더 (의존성 분리)"""
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}


WS_CONDITION_SEARCH_ENABLED_ENV = "KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED"
# Official Kiwoom reference gate (re-verified 2026-08-20T13:36:00+09:00):
# upstream SHA 69642586f7d84ba9fd8a6faf1f1537c7fda6568b; inspected
# kiwoom_docs/실시간시세.md, kiwoom/realtime/packets.py,
# kiwoom/realtime/{events,decoders,schemas,stream}.py, kiwoom/core/ws_client.py,
# kiwoom/_data/kiwoom_api_spec.json, and the upstream Postman collection.
# REG refresh=1 retains existing registrations; source-only repair requests use
# only the documented 0B trade and 0D depth types. 0B FID 10 owns current price;
# KRX/NXT/SOR items use 005930/005930_NX/005930_AL.
KST = ZoneInfo("Asia/Seoul")
_ORDER_EXECUTION_RAW_ENVELOPE_SCHEMA = "kiwoom_websocket_order_execution_00_values_v1"
_ORDER_EXECUTION_RECEIVE_TIME_SOURCE = "websocket_packet_ingress"
_ORDER_EXECUTION_UNTRUSTED_RECEIVE_TIME_SOURCE = (
    "handler_dispatch_fallback_not_packet_ingress"
)
_ORDER_EXECUTION_RAW_FIDS = (
    "9203",
    "9001",
    "913",
    "900",
    "902",
    "903",
    "905",
    "907",
    "908",
    "909",
    "910",
    "911",
    "914",
    "915",
    "919",
    "2134",
    "2135",
    "2136",
)
COMMAND_MICRO_REVERSION_OBSERVATION_SET = "COMMAND_MICRO_REVERSION_OBSERVATION_SET"
WS_PINNED_OBSERVATION_ITEMS_ENV = "KORSTOCKSCAN_WS_PINNED_OBSERVATION_ITEMS"
WS_DASHBOARD_SNAPSHOT_INTERVAL_SEC_ENV = (
    "KORSTOCKSCAN_WS_DASHBOARD_SNAPSHOT_INTERVAL_SEC"
)
DEFAULT_WS_PINNED_OBSERVATION_ITEMS = ("005930_AL",)
SCALP_CONDITION_PREWARM_MAX_CODES = 16
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCALP_CONDITION_KEYWORDS = (
    "scalp_candid_aggressive_01",
    "scalp_candid_normal_01",
    "scalp_open_reclaim_01",
    "scalp_vwap_reclaim_01",
    "scalp_dryup_squeeze_01",
    "scalp_preclose_01",
    "scalp_strong_01",
    "scalp_underpress_01",
    "scalp_shooting_01",
    "scalp_afternoon_01",
    "vcp_candid_01",
    "vcp_shooting_01",
    "vcp_shooting_next_01",
    "s15_scan_base_01",
    "s15_trigger_break_01",
)
SWING_CONDITION_KEYWORDS = (
    "kospi_short_swing_01",
    "kospi_midterm_swing_01",
)
_WS_HOT_RUNTIME_OVERRIDE_KEYS = frozenset(
    {
        "KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES",
        "KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC",
        "KORSTOCKSCAN_WS_MAX_REG_ITEMS",
        "KORSTOCKSCAN_WS_FRESHNESS_STALE_SEC",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES_PER_WINDOW",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_WINDOW_SEC",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REMOVE_BEFORE_REG_ENABLED",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC",
        "KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC",
    }
)
_WS_OPERATOR_RUNTIME_OVERRIDE_PATH = (
    PROJECT_ROOT
    / "data"
    / "threshold_cycle"
    / "runtime_env"
    / "operator_runtime_overrides.env"
)
_WS_HOT_RUNTIME_OVERRIDE_REFRESH_SEC = 5.0
TOB_CACHE_TTL_MS = int(os.getenv("KORSTOCKSCAN_WS_TOB_CACHE_TTL_MS", "300") or "300")
TICK_SYNC_WINDOW_MS = int(
    os.getenv("KORSTOCKSCAN_WS_TICK_SYNC_WINDOW_MS", "500") or "500"
)
TOB_BACKOFF_BASE_MS = int(
    os.getenv("KORSTOCKSCAN_WS_TOB_BACKOFF_BASE_MS", "200") or "200"
)
TOB_BACKOFF_MAX_MS = int(
    os.getenv("KORSTOCKSCAN_WS_TOB_BACKOFF_MAX_MS", "5000") or "5000"
)
_WS_HOT_RUNTIME_OVERRIDES = {
    "mtime_ns": None,
    "values": {},
    "next_check_ts": 0.0,
}
_WS_HOT_RUNTIME_OVERRIDES_LOCK = threading.Lock()


def pinned_ws_observation_items() -> tuple[str, ...]:
    """Return read-only market-data items that survive target pruning.

    The default Samsung SOR item feeds only the Windows widget comparison.
    It grants no recommendation, order, sizing, or lifecycle authority.
    Setting the environment variable to an empty string disables the pin.
    """

    raw = os.getenv(WS_PINNED_OBSERVATION_ITEMS_ENV)
    values = (
        DEFAULT_WS_PINNED_OBSERVATION_ITEMS
        if raw is None
        else tuple(part.strip().upper() for part in raw.split(",") if part.strip())
    )
    result = []
    seen = set()
    for value in values:
        base = value
        suffix = ""
        if value.endswith(("_AL", "_NX")):
            base, suffix = value[:-3], value[-3:]
        if base != "005930":
            continue
        item = f"{base}{suffix}"
        if item not in seen:
            result.append(item)
            seen.add(item)
    return tuple(result[:1])


def pinned_ws_observation_codes() -> frozenset[str]:
    return frozenset(item[:6] for item in pinned_ws_observation_items())


def is_pinned_ws_observation_registration(
    code: str, items: tuple[str, ...] | list[str]
) -> bool:
    pinned_items = set(pinned_ws_observation_items())
    registered_items = {
        str(item or "").strip().upper() for item in items if str(item or "").strip()
    }
    return bool(
        str(code or "").strip()[:6] in pinned_ws_observation_codes()
        and registered_items
        and registered_items.issubset(pinned_items)
    )


def _ws_dashboard_snapshot_interval_sec() -> float:
    raw = os.getenv(WS_DASHBOARD_SNAPSHOT_INTERVAL_SEC_ENV, "1.0")
    try:
        return max(0.25, min(10.0, float(raw)))
    except (TypeError, ValueError):
        return 1.0


def is_ws_condition_search_enabled() -> bool:
    raw = str(os.getenv(WS_CONDITION_SEARCH_ENABLED_ENV, "") or "").strip().lower()
    return raw in {"1", "true", "t", "yes", "y", "on"}


def _is_scalp_condition_name(condition_name: str) -> bool:
    name = str(condition_name or "")
    return any(keyword in name for keyword in SCALP_CONDITION_KEYWORDS)


def _condition_match_intake_allowed(condition_name: str, *, now=None) -> bool:
    if not _is_scalp_condition_name(condition_name):
        return True
    if is_scalping_buy_time_allowed(now):
        return True
    print(
        "[WS_CONDITION_BUY_WINDOW_BLOCKED] 스캘핑 조건검색 편입 무시 "
        f"condition={condition_name or 'UNKNOWN_CONDITION'} "
        f"reason={scalping_buy_time_block_reason(now)} "
        f"buy_windows={describe_scalping_buy_windows()}"
    )
    return False


def _parse_ws_hot_runtime_override_file(path):
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
        if key not in _WS_HOT_RUNTIME_OVERRIDE_KEYS:
            continue
        value = value.strip()
        try:
            parts = shlex.split(value, comments=False, posix=True)
            parsed_value = parts[0] if parts else ""
        except ValueError:
            parsed_value = value.strip("\"'")
        values[key] = str(parsed_value).strip()
    return values


def _ws_hot_runtime_override_value(name, now_ts=None):
    key = str(name or "").strip()
    if key not in _WS_HOT_RUNTIME_OVERRIDE_KEYS:
        return None
    now_value = time.time() if now_ts is None else float(now_ts)
    with _WS_HOT_RUNTIME_OVERRIDES_LOCK:
        cache = _WS_HOT_RUNTIME_OVERRIDES
        if now_value < float(cache.get("next_check_ts") or 0.0):
            return (cache.get("values") or {}).get(key)
        cache["next_check_ts"] = now_value + _WS_HOT_RUNTIME_OVERRIDE_REFRESH_SEC
        path = _WS_OPERATOR_RUNTIME_OVERRIDE_PATH
        try:
            stat = Path(path).stat()
            mtime_ns = int(getattr(stat, "st_mtime_ns", 0) or 0)
        except OSError:
            cache["mtime_ns"] = None
            cache["values"] = {}
            return None
        if cache.get("mtime_ns") != mtime_ns:
            cache["values"] = _parse_ws_hot_runtime_override_file(path)
            cache["mtime_ns"] = mtime_ns
        return (cache.get("values") or {}).get(key)


def _ws_hot_or_env_value(name):
    hot_value = _ws_hot_runtime_override_value(name)
    if hot_value not in (None, ""):
        return hot_value
    return os.getenv(name, "")


def _env_bool(name, default):
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    text = str(raw).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "f", "no", "n", "off"}:
        return False
    return bool(default)


def _micro_estimator_ws_observation_enabled():
    return _env_bool(
        "KORSTOCKSCAN_MICRO_ESTIMATOR_WS_OBSERVATION_ENABLED",
        _env_bool("KORSTOCKSCAN_MICRO_ESTIMATOR_ENABLED", True),
    )


class KiwoomWSManager:
    def __init__(self, token):
        # 💡 [우아한 아키텍처] 하드코딩 파괴! 설정 파일에서 URI를 동적으로 읽어옵니다.
        conf = _load_system_config()
        self.conf = conf
        # config에 URI가 없으면 안전하게 Mock API를 기본값으로 사용합니다.
        self.uri = conf.get(
            "KIWOOM_WS_URI", "wss://mockapi.kiwoom.com:10000/api/dostk/websocket"
        )

        self.token = token
        self.realtime_data = {}
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None
        self._stop_event = threading.Event()
        self._state_event_queue = Queue()
        self._tick_dispatch_event = threading.Event()
        self._pending_tick_events = {}
        self._tick_lock = threading.Lock()
        self._state_dispatch_thread = None
        self._tick_dispatch_thread = None
        self._ws_thread = None
        self._started = False
        self._pending_loop_futures = set()
        self._pending_future_lock = threading.Lock()
        self._session_ready = threading.Event()
        self._last_token_refresh_at = 0.0
        self._pending_token_handoff = None
        self._last_dashboard_snapshot_at = 0.0
        self._dashboard_snapshot_write_inflight = False
        self._recent_reg_request_ts = {}
        self._alternate_route_request_ts = {}
        self._persistent_repair_request_ts = {}
        self._persistent_repair_window_epochs = deque()
        self._persistent_repair_no_tick_attempts = {}
        self._persistent_repair_stuck_until_ts = {}
        self._persistent_repair_overflow_codes = OrderedDict()
        self._last_persistent_repair_rebuild_ts = 0.0
        self._registered_items_by_code = {}
        self._pinned_unreg_notice_codes = set()
        self._micro_reversion_observation_items_by_code = {}
        self._micro_reversion_observation_only_codes = set()
        self._micro_reversion_observation_notice_codes = set()
        # Most subscriptions can be considered live after any quote packet.
        # Scanner entry is stricter: its short-window tape requires a post-REG
        # 0B receipt, not merely a 0D order-book update.
        self._required_realtime_types_by_code = {}
        self._top_of_book_cache = {}
        self._last_remove_request_ts = {}
        self._deferred_scalp_condition_matches = OrderedDict()
        self._scalp_condition_prewarm_codes = OrderedDict()
        self._micro_reversion_forward_collector = None
        self._micro_reversion_forward_collector_error = ""
        self._micro_reversion_forward_collector_stop_reason = ""
        self._micro_reversion_forward_collector_close_lock = threading.Lock()
        self._micro_reversion_canary_snapshot_lock = threading.Lock()
        self._micro_reversion_canary_monitor_stop_event = threading.Event()
        self._micro_reversion_canary_monitor_thread = None
        self._micro_reversion_canary_latency_breach_count = 0

        # 전역 EventBus 인스턴스 획득 및 외부 명령 수신기 장착
        self.event_bus = EventBus()
        self.event_bus.subscribe("COMMAND_WS_REG", self._handle_reg_event)
        self.event_bus.subscribe("COMMAND_WS_UNREG", self._handle_unreg_event)
        self.event_bus.subscribe(
            COMMAND_MICRO_REVERSION_OBSERVATION_SET,
            self._handle_micro_reversion_observation_set,
        )
        # 💡 [추가] 최초 접속인지, 끊겼다가 다시 붙은(재접속) 것인지 구분하는 플래그
        self.is_reconnected = False
        self.condition_dict = {}  # 💡 [추가] 일련번호(seq)와 검색식 이름을 매핑할 사전
        self.market_session_state = ""
        self.market_session_remaining = ""
        self._last_market_session_event_key = None

        print(f"🌐 [WS] 웹소켓 매니저 초기화 완료 (Target: {self.uri})")

    @staticmethod
    def _chunked(items, size):
        chunk_size = max(1, int(size or 1))
        for idx in range(0, len(items), chunk_size):
            yield items[idx : idx + chunk_size]

    @staticmethod
    def _safe_abs_int(val, default=0):
        try:
            return abs(int(float(str(val).replace(",", "").strip())))
        except Exception:
            return default

    @classmethod
    def _optional_abs_int(cls, values, fid):
        """Return an official numeric FID only when it is actually present."""

        if not isinstance(values, dict) or fid not in values:
            return None
        raw_value = values.get(fid)
        if raw_value is None or not str(raw_value).strip():
            return None
        normalized = str(raw_value).strip()
        if not re.fullmatch(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)", normalized):
            return None
        try:
            return abs(int(normalized.replace(",", "")))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_signed_int(val, default=0):
        try:
            return int(float(str(val).replace(",", "").replace("+", "").strip()))
        except Exception:
            return default

    @staticmethod
    def _safe_float(val, default=0.0):
        try:
            return float(str(val).replace(",", "").replace("+", "").strip())
        except Exception:
            return default

    @staticmethod
    def _flag_enabled(value, *, default=False):
        if value is None:
            return bool(default)
        if isinstance(value, bool):
            return value
        text = str(value or "").strip().lower()
        if text in {"1", "true", "t", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "f", "no", "n", "off"}:
            return False
        return bool(default)

    @staticmethod
    def _infer_trade_aggressor_from_touch(trade_price, best_ask, best_bid):
        price = KiwoomWSManager._safe_abs_int(trade_price, 0)
        ask = KiwoomWSManager._safe_abs_int(best_ask, 0)
        bid = KiwoomWSManager._safe_abs_int(best_bid, 0)
        if price <= 0:
            return "UNKNOWN", "missing_trade_price"
        if ask <= 0 or bid <= 0:
            return "UNKNOWN", "missing_best_quote"
        if ask > 0 and price >= ask:
            return "BUY", "touch_or_crossed_ask"
        if bid > 0 and price <= bid:
            return "SELL", "touch_or_crossed_bid"
        return "UNKNOWN", "inside_spread_or_uncertain"

    @staticmethod
    def _infer_signed_trade_volume_auxiliary(value):
        text = str(value or "").replace(",", "").strip()
        if text.startswith("+"):
            return "BUY", "signed_trade_volume_positive_auxiliary"
        if text.startswith("-"):
            return "SELL", "signed_trade_volume_negative_auxiliary"
        return "UNKNOWN", "signed_trade_volume_missing_or_neutral"

    @staticmethod
    def _primary_signed_trade_volume_quality(auxiliary_quality):
        text = str(auxiliary_quality or "").strip()
        if text.endswith("_auxiliary"):
            return text[: -len("_auxiliary")]
        return text or "signed_trade_volume_missing_or_neutral"

    @staticmethod
    def _parse_0b_auxiliary_fields(values, *, trade_price=0, previous_tick=None):
        values = values if isinstance(values, dict) else {}
        previous_tick = previous_tick if isinstance(previous_tick, dict) else {}
        buy_qty = KiwoomWSManager._safe_abs_int(values.get("1031"), None)
        sell_qty = KiwoomWSManager._safe_abs_int(values.get("1030"), None)
        signed_qty_abs = KiwoomWSManager._safe_abs_int(values.get("15"), None)
        cum_volume = KiwoomWSManager._safe_abs_int(values.get("13"), None)
        prev_cum_volume = KiwoomWSManager._safe_abs_int(
            previous_tick.get("cum_volume"), None
        )
        cum_volume_delta = (
            int(cum_volume - prev_cum_volume)
            if cum_volume is not None
            and prev_cum_volume is not None
            and cum_volume > prev_cum_volume
            else None
        )
        price = KiwoomWSManager._safe_abs_int(trade_price or values.get("10"), 0)
        split_qty_available = buy_qty is not None and sell_qty is not None
        split_qty_sum = (
            int((buy_qty or 0) + (sell_qty or 0)) if split_qty_available else None
        )

        # Kiwoom 1030/1031 are cumulative execution totals in the live 0B
        # stream.  Preserve them for source-quality diagnostics, but never use
        # their sum as a per-tick volume or trade-value multiplier.
        if signed_qty_abs is not None and signed_qty_abs > 0:
            trade_volume = signed_qty_abs
            trade_volume_source = "15_abs"
        elif cum_volume_delta is not None and cum_volume_delta > 0:
            trade_volume = cum_volume_delta
            trade_volume_source = "13_delta"
        else:
            trade_volume = 0
            trade_volume_source = "unknown"

        trade_value = KiwoomWSManager._safe_abs_int(values.get("1313"), None)
        trade_value_source = (
            "1313" if trade_value is not None and trade_value > 0 else "unknown"
        )
        fallback_volume_source = "none"
        if trade_value_source == "unknown":
            if trade_volume > 0:
                fallback_volume_source = trade_volume_source
            if price > 0 and trade_volume > 0:
                trade_value = int(price * trade_volume)
                trade_value_source = f"calc_price_x_{fallback_volume_source}"
            else:
                trade_value = 0

        mismatch = (
            split_qty_sum is not None
            and signed_qty_abs is not None
            and split_qty_sum != signed_qty_abs
        )
        mismatch_delta = (
            int(split_qty_sum - signed_qty_abs)
            if split_qty_sum is not None and signed_qty_abs is not None
            else None
        )
        return {
            "buy_qty": int(buy_qty or 0),
            "sell_qty": int(sell_qty or 0),
            "signed_qty_abs": int(signed_qty_abs or 0),
            "cum_volume": int(cum_volume or 0),
            "prev_cum_volume": int(prev_cum_volume or 0),
            "cum_volume_delta": (
                int(cum_volume_delta) if cum_volume_delta is not None else None
            ),
            "split_qty_sum": int(split_qty_sum or 0),
            "split_qty_available": bool(split_qty_available),
            "split_qty_advisory_only": True,
            "trade_volume": int(trade_volume or 0),
            "trade_volume_source": trade_volume_source,
            "trade_value": int(trade_value or 0),
            "trade_value_source": trade_value_source,
            "trade_value_fallback_volume_source": fallback_volume_source,
            "split_qty_vs_15_evaluable": bool(
                split_qty_sum is not None and signed_qty_abs is not None
            ),
            "split_qty_vs_15_mismatch": bool(mismatch),
            "split_qty_vs_15_delta": mismatch_delta,
        }

    @staticmethod
    def _increment_counter_dict(counter, key):
        if not isinstance(counter, dict):
            counter = {}
        text = str(key or "unknown")
        counter[text] = int(counter.get(text) or 0) + 1
        return counter

    @staticmethod
    def _infer_trade_auxiliary_score(values, *, previous_tick=None):
        values = values if isinstance(values, dict) else {}
        previous_tick = previous_tick if isinstance(previous_tick, dict) else {}
        score = 0.0
        reasons = []
        components = {}

        signed_side, signed_quality = (
            KiwoomWSManager._infer_signed_trade_volume_auxiliary(values.get("15"))
        )
        components["signed_volume_side"] = signed_side
        if signed_side == "BUY":
            score += 3.0
            reasons.append("signed_volume_positive")
        elif signed_side == "SELL":
            score -= 3.0
            reasons.append("signed_volume_negative")

        buy_qty = KiwoomWSManager._safe_abs_int(values.get("1031"), 0)
        sell_qty = KiwoomWSManager._safe_abs_int(values.get("1030"), 0)
        total_qty = buy_qty + sell_qty
        components["buy_exec_qty_1031"] = buy_qty
        components["sell_exec_qty_1030"] = sell_qty
        if total_qty > 0:
            imbalance = (buy_qty - sell_qty) / float(total_qty)
            score += imbalance * 5.0
            components["exec_qty_imbalance"] = round(imbalance, 6)
            reasons.append("exec_qty_imbalance")

        cum_volume = KiwoomWSManager._safe_abs_int(values.get("13"), 0)
        prev_cum_volume = KiwoomWSManager._safe_abs_int(
            previous_tick.get("cum_volume"), 0
        )
        components["cum_volume_13"] = cum_volume
        components["prev_cum_volume_13"] = prev_cum_volume
        if cum_volume > 0 and prev_cum_volume > 0:
            delta = cum_volume - prev_cum_volume
            components["cum_volume_delta"] = delta
            if delta > 0 and signed_side in {"BUY", "SELL"}:
                delta_score = min(2.0, float(delta) * 0.001)
                score += delta_score if signed_side == "BUY" else -delta_score
                reasons.append("cum_volume_delta_with_signed_volume")

        strength = KiwoomWSManager._safe_float(values.get("228"), 0.0)
        components["trade_strength_228"] = strength
        if strength > 0:
            # Kiwoom trade strength is generally interpreted around 100 as neutral.
            strength_bias = max(-2.0, min(2.0, ((strength - 100.0) / 100.0) * 2.0))
            score += strength_bias
            components["trade_strength_bias"] = round(strength_bias, 6)
            reasons.append("trade_strength_bias")

        price = KiwoomWSManager._safe_abs_int(values.get("10"), 0)
        prev_price = KiwoomWSManager._safe_abs_int(previous_tick.get("price"), 0)
        components["prev_trade_price"] = prev_price
        if price > 0 and prev_price > 0:
            if price > prev_price:
                score += 1.0
                reasons.append("price_up_vs_prev")
            elif price < prev_price:
                score -= 1.0
                reasons.append("price_down_vs_prev")

        if score >= 1.5:
            side = "BUY"
        elif score <= -1.5:
            side = "SELL"
        else:
            side = "UNKNOWN"
        if reasons == ["signed_volume_positive"]:
            quality = signed_quality
        elif reasons == ["signed_volume_negative"]:
            quality = signed_quality
        elif reasons:
            quality = "weighted_auxiliary_observation"
        else:
            quality = "auxiliary_observation_missing_or_neutral"
        return {
            "side": side,
            "quality": quality,
            "score": round(score, 6),
            "reason": ";".join(reasons) if reasons else "insufficient_auxiliary_data",
            "components": components,
        }

    @staticmethod
    def _tick_time_to_epoch_ms(tick_time, *, now_ts=None):
        text = str(tick_time or "").strip().replace(":", "")
        if len(text) < 6 or not text[:6].isdigit():
            return 0
        now_value = time.time() if now_ts is None else float(now_ts)
        now_dt = datetime.fromtimestamp(now_value)
        try:
            tick_dt = now_dt.replace(
                hour=int(text[:2]),
                minute=int(text[2:4]),
                second=int(text[4:6]),
                microsecond=0,
            )
        except ValueError:
            return 0
        if len(text) >= 9 and text[6:9].isdigit():
            tick_dt = tick_dt.replace(microsecond=int(text[6:9]) * 1000)
        epoch_ms = int(tick_dt.timestamp() * 1000)
        now_ms = int(now_value * 1000)
        if epoch_ms - now_ms > 12 * 60 * 60 * 1000:
            epoch_ms -= 24 * 60 * 60 * 1000
        elif now_ms - epoch_ms > 12 * 60 * 60 * 1000:
            epoch_ms += 24 * 60 * 60 * 1000
        return epoch_ms

    @staticmethod
    def _empty_tob_cache():
        return {
            "ask": 0,
            "bid": 0,
            "ts_ms": 0,
            "miss_count": 0,
            "next_allowed_retry_ms": 0,
        }

    def _tob_backoff_ms(self, miss_count):
        count = max(0, int(miss_count or 0))
        if count <= 0:
            return 0
        return min(TOB_BACKOFF_BASE_MS * (2 ** max(0, count - 1)), TOB_BACKOFF_MAX_MS)

    def _get_tob_cache(self, item_code):
        cache = self._top_of_book_cache.get(item_code)
        if not isinstance(cache, dict):
            cache = self._empty_tob_cache()
            self._top_of_book_cache[item_code] = cache
        return cache

    def _update_tob_cache(self, item_code, *, best_ask=0, best_bid=0, now_ms=None):
        cache = self._get_tob_cache(item_code)
        now_value = int(now_ms if now_ms is not None else time.time() * 1000)
        ask = self._safe_abs_int(best_ask, 0)
        bid = self._safe_abs_int(best_bid, 0)
        if ask > 0:
            cache["ask"] = ask
        if bid > 0:
            cache["bid"] = bid
        if ask > 0 or bid > 0:
            cache["ts_ms"] = now_value
            cache["miss_count"] = 0
            cache["next_allowed_retry_ms"] = 0
        return cache

    def _resolve_0b_touch_quote(
        self, item_code, *, inline_best_ask, inline_best_bid, tick_time, received_ts
    ):
        now_ms = int(float(received_ts or time.time()) * 1000)
        tick_ms = self._tick_time_to_epoch_ms(tick_time, now_ts=received_ts)
        tick_sync = bool(tick_ms and abs(now_ms - tick_ms) <= TICK_SYNC_WINDOW_MS)
        inline_ask = self._safe_abs_int(inline_best_ask, 0)
        inline_bid = self._safe_abs_int(inline_best_bid, 0)
        cache = self._get_tob_cache(item_code)
        cache_ts_ms = int(cache.get("ts_ms") or 0)
        quote_age_ms = max(0, now_ms - cache_ts_ms) if cache_ts_ms > 0 else None
        cache_fresh = quote_age_ms is not None and quote_age_ms <= TOB_CACHE_TTL_MS
        backoff_active = bool(now_ms < int(cache.get("next_allowed_retry_ms") or 0))

        best_ask = inline_ask
        best_bid = inline_bid
        cache_used = False
        inline_complete = inline_ask > 0 and inline_bid > 0
        inline_partial = (inline_ask > 0) != (inline_bid > 0)
        quote_source = (
            "0B_inline_best_quote"
            if inline_complete
            else "partial_inline_best_quote"
            if inline_partial
            else "missing_best_quote"
        )

        if inline_complete:
            cache = self._update_tob_cache(
                item_code,
                best_ask=inline_ask,
                best_bid=inline_bid,
                now_ms=now_ms,
            )
            quote_age_ms = 0
            cache_fresh = True
            backoff_active = False

        if (
            (inline_ask <= 0 or inline_bid <= 0)
            and cache_fresh
            and tick_sync
            and not backoff_active
        ):
            filled_from_cache = False
            if inline_ask <= 0 and int(cache.get("ask") or 0) > 0:
                best_ask = int(cache.get("ask") or 0)
                filled_from_cache = True
            if inline_bid <= 0 and int(cache.get("bid") or 0) > 0:
                best_bid = int(cache.get("bid") or 0)
                filled_from_cache = True
            if filled_from_cache and best_ask > 0 and best_bid > 0:
                cache_used = True
                quote_source = "cached_top_of_book_ttl"

        if best_ask <= 0 or best_bid <= 0:
            if not cache_used:
                miss_count = int(cache.get("miss_count") or 0) + 1
                cache["miss_count"] = miss_count
                backoff_ms = self._tob_backoff_ms(miss_count)
                cache["next_allowed_retry_ms"] = now_ms + backoff_ms
                backoff_active = bool(backoff_ms > 0)
            else:
                backoff_active = False

        return {
            "best_ask": best_ask,
            "best_bid": best_bid,
            "tick_sync": tick_sync,
            "cache_used": cache_used,
            "quote_age_ms": quote_age_ms,
            "quote_source": quote_source,
            "tob_miss_count": int(cache.get("miss_count") or 0),
            "backoff_active": bool(backoff_active),
        }

    @staticmethod
    def _normalize_code(code):
        raw = str(code or "").strip().upper().replace(".0", "")
        for suffix in ("_AL", "_NX"):
            if raw.endswith(suffix):
                raw = raw[:-3]
                break
        if raw.startswith("A") and len(raw) >= 7:
            raw = raw[1:]
        digits = "".join(ch for ch in raw if ch.isdigit())
        return digits[-6:].zfill(6) if digits else raw[:6]

    @staticmethod
    def _explicit_ws_item(raw_code, canonical_code):
        raw = str(raw_code or "").strip().upper().replace(".0", "")
        if raw.endswith("_AL"):
            return f"{canonical_code}_AL"
        if raw.endswith("_NX"):
            return f"{canonical_code}_NX"
        return None

    @staticmethod
    def _ws_item_market_suffix(item):
        raw = str(item or "").strip().upper()
        if raw.endswith("_AL"):
            return "_AL"
        if raw.endswith("_NX"):
            return "_NX"
        return ""

    @classmethod
    def _ws_item_route(cls, item):
        suffix = cls._ws_item_market_suffix(item)
        if suffix == "_AL":
            return "krx_nxt_integrated"
        if suffix == "_NX":
            return "nxt_only"
        return "krx_regular"

    @classmethod
    def _ws_item_effective_venue(cls, item):
        """Return only venue identity proven by the subscription item itself."""

        suffix = cls._ws_item_market_suffix(item)
        if suffix == "_NX":
            return "NXT"
        if suffix == "_AL":
            return ""
        return "KRX"

    @classmethod
    def _ws_item_route_counts(cls, items):
        counts = {}
        for item in items or ():
            route = cls._ws_item_route(item)
            counts[route] = counts.get(route, 0) + 1
        return dict(sorted(counts.items()))

    def _parse_order_execution_notice(self, values, *, source_type=None):
        raw_provenance = {
            fid: values.get(fid) for fid in _ORDER_EXECUTION_RAW_FIDS if fid in values
        }
        # Only an explicit official realtime type ``00`` may claim the raw
        # envelope markers.  The legacy name-based dispatch fallback remains
        # operational, but cannot manufacture R0-R3 promotion evidence.
        if isinstance(source_type, str) and source_type == "00":
            raw_provenance.update(
                {
                    "main_lifecycle_broker_raw_envelope_schema": (
                        _ORDER_EXECUTION_RAW_ENVELOPE_SCHEMA
                    ),
                    "main_lifecycle_broker_raw_source_type": source_type,
                }
            )
        status = str(values.get("913", "")).strip()
        code = str(values.get("9001", "")).replace("A", "").strip()
        order_no = str(values.get("9203", "")).strip()
        order_type_str = str(values.get("905", "")).strip()
        numeric_fids = ("900", "902", "903", "910", "911", "914", "915")
        parsed_numeric = {
            fid: self._optional_abs_int(values, fid) for fid in numeric_fids
        }
        malformed_numeric_fids = [
            fid
            for fid in numeric_fids
            if fid in values
            and values.get(fid) is not None
            and str(values.get(fid)).strip()
            and parsed_numeric[fid] is None
        ]
        exec_price = parsed_numeric["910"] or 0
        exec_qty = parsed_numeric["911"] or 0
        has_buy = "매수" in order_type_str
        has_sell = "매도" in order_type_str
        side_exact = has_buy != has_sell
        if side_exact:
            side = "BUY" if has_buy else "SELL"
            exec_type = f"{side}_CANCEL" if "취소" in order_type_str else side
            side_gap_reason = ""
        else:
            exec_type = ""
            side_gap_reason = "order_side_ambiguous_or_missing"
        raw_exchange_code = str(values.get("2134", "") or "").strip()
        raw_exchange_name = str(values.get("2135", "") or "").strip().upper()
        exchange_by_code = {"1": "KRX", "2": "NXT"}.get(raw_exchange_code, "")
        exchange_by_name = (
            raw_exchange_name if raw_exchange_name in {"KRX", "NXT"} else ""
        )
        actual_execution_venue = exchange_by_code or exchange_by_name
        if (
            exchange_by_code
            and exchange_by_name
            and exchange_by_code != exchange_by_name
        ):
            actual_execution_venue = ""
        return {
            "status": status,
            "code": code,
            "order_no": order_no,
            "order_type_str": order_type_str,
            "order_qty": parsed_numeric["900"],
            "remaining_qty": parsed_numeric["902"],
            "cumulative_exec_amount": parsed_numeric["903"],
            "execution_no": str(values.get("909", "") or "").strip(),
            "exec_price": exec_price,
            "exec_qty": exec_qty,
            "unit_exec_price": parsed_numeric["914"],
            "unit_exec_qty": parsed_numeric["915"],
            "broker_reject_reason_raw": str(values.get("919", "") or "").strip(),
            "numeric_contract_errors": malformed_numeric_fids,
            "source_gap_reason": side_gap_reason,
            "broker_execution_time_raw": str(values.get("908", "") or "").strip(),
            "actual_exchange_code": raw_exchange_code,
            "actual_exchange_name": raw_exchange_name,
            "actual_execution_venue": actual_execution_venue,
            "sor_flag": str(values.get("2136", "") or "").strip().upper(),
            "exec_type": exec_type,
            "broker_execution_raw_fields": raw_provenance,
        }

    def _normalize_subscribe_codes(self, codes):
        normalized = []
        invalid = []
        seen = set()

        for raw_code in codes or []:
            code = self._normalize_code(raw_code)
            if not code:
                continue
            if len(code) != 6 or not code.isdigit():
                invalid.append(str(raw_code))
                continue
            if code in seen:
                continue
            seen.add(code)
            normalized.append(code)

        if invalid:
            print(f"⚠️ [WS] 실시간 등록 제외 코드: {invalid}")
        return normalized

    def _resolve_ws_register_items(
        self, codes, *, include_alternate_route=False, alternate_route_codes=None
    ):
        """Return canonical subscription codes and Kiwoom exchange-aware REG items."""
        normalized_codes = self._normalize_subscribe_codes(codes)
        if not normalized_codes:
            return [], []
        alternate_route_code_set = (
            set(normalized_codes)
            if alternate_route_codes is None
            else set(alternate_route_codes)
        )

        explicit_by_code = {}
        plain_requested_codes = set()
        for raw_code in codes or []:
            canonical = self._normalize_code(raw_code)
            if canonical in normalized_codes:
                explicit = self._explicit_ws_item(raw_code, canonical)
                if explicit:
                    explicit_items = explicit_by_code.setdefault(canonical, [])
                    if explicit not in explicit_items:
                        explicit_items.append(explicit)
                else:
                    plain_requested_codes.add(canonical)

        register_items = []
        try:
            from src.utils import kiwoom_utils

            for code in normalized_codes:
                explicit_items = explicit_by_code.get(code) or []
                if explicit_items:
                    if code in plain_requested_codes:
                        register_items.append(code)
                    register_items.extend(explicit_items)
                    continue

                effective = kiwoom_utils.get_effective_kiwoom_code(code)
                items = [effective]
                if (
                    include_alternate_route
                    and code in alternate_route_code_set
                    and not str(effective or "").upper().endswith("_AL")
                ):
                    items.append(f"{code}_AL")
                register_items.extend(OrderedDict.fromkeys(items))
        except Exception as exc:
            log_error(
                f"🚨 [WS] 거래소별 실시간 등록 코드 변환 실패. 6자리 코드로 폴백합니다: {exc}"
            )
            register_items = []
            for code in normalized_codes:
                explicit_items = explicit_by_code.get(code) or []
                if explicit_items:
                    if code in plain_requested_codes:
                        register_items.append(code)
                    register_items.extend(explicit_items)
                else:
                    register_items.append(code)
                    if include_alternate_route and code in alternate_route_code_set:
                        register_items.append(f"{code}_AL")

        return normalized_codes, register_items

    @staticmethod
    def _max_registered_item_count():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_MAX_REG_ITEMS")
        try:
            value = int(str(raw).strip()) if str(raw).strip() else 24
        except Exception:
            value = 24
        if value <= 0:
            return 0
        return max(1, min(value, 200))

    @staticmethod
    def _freshness_stale_sec():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_FRESHNESS_STALE_SEC")
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 30.0
        except Exception:
            value = 30.0
        return max(1.0, min(value, 1800.0))

    @staticmethod
    def _persistent_repair_remove_before_reg_enabled():
        raw = _ws_hot_or_env_value(
            "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REMOVE_BEFORE_REG_ENABLED"
        )
        # Kiwoom REG refresh=1 retains existing registrations.  A targeted
        # persistent repair therefore defaults to additive re-registration;
        # REMOVE-before-REG remains an explicit operator recovery option.
        return KiwoomWSManager._flag_enabled(raw, default=False)

    def _registered_item_count_locked(self):
        return sum(
            len(tuple(items or ())) for items in self._registered_items_by_code.values()
        )

    def is_pinned_observation_subscription(self, code):
        normalized = self._normalize_code(code)
        if not normalized:
            return False
        with self.lock:
            registered_items = tuple(
                self._registered_items_by_code.get(normalized) or ()
            )
            micro_observation = bool(
                normalized in self.subscribed_codes
                and normalized in self._micro_reversion_observation_items_by_code
            )
        return micro_observation or is_pinned_ws_observation_registration(
            normalized, registered_items
        )

    def is_micro_reversion_observation_only_subscription(self, code):
        normalized = self._normalize_code(code)
        if not normalized:
            return False
        with self.lock:
            return normalized in self._micro_reversion_observation_only_codes

    def retain_micro_reversion_as_observation_only(self, code):
        """Demote an inactive runtime code back to its exact source-only role."""

        normalized = self._normalize_code(code)
        if not normalized:
            return False
        with self.lock:
            registered_items = tuple(
                self._registered_items_by_code.get(normalized) or ()
            )
            if is_pinned_ws_observation_registration(normalized, registered_items):
                return False
            desired_item = self._micro_reversion_observation_items_by_code.get(
                normalized
            )
            if not desired_item:
                return False
            already_observation_only = (
                normalized in self._micro_reversion_observation_only_codes
            )
            self._micro_reversion_observation_only_codes.add(normalized)
        if not already_observation_only:
            self.execute_subscribe(
                [desired_item],
                force=True,
                source="micro_reversion_collection_feedback_demotion",
                remove_before_reg=True,
                realtime_types=("0B", "0D"),
                observation_only=True,
            )
        return True

    def _items_by_code(self, normalized_codes, register_items):
        items_by_code = {}
        for code in normalized_codes or []:
            seen = OrderedDict()
            for item in register_items or []:
                if self._normalize_code(item) == code:
                    seen[str(item)] = None
            items_by_code[code] = list(seen.keys())
        return items_by_code

    @staticmethod
    def _normalize_required_realtime_types(required_realtime_types):
        if isinstance(required_realtime_types, str):
            required_realtime_types = [required_realtime_types]
        normalized = []
        for value in required_realtime_types or ():
            realtime_type = str(value or "").strip()
            if realtime_type and realtime_type not in normalized:
                normalized.append(realtime_type)
        return tuple(normalized)

    def _required_realtime_types_received_locked(self, code, target=None):
        required = tuple(self._required_realtime_types_by_code.get(code) or ())
        if not required:
            return True
        target = target if isinstance(target, dict) else self.realtime_data.get(code)
        target = target if isinstance(target, dict) else {}
        type_ts = target.get("last_realtime_type_ts")
        type_ts = type_ts if isinstance(type_ts, dict) else {}
        return all(
            self._safe_float(type_ts.get(realtime_type), 0.0) > 0
            for realtime_type in required
        )

    def _has_any_realtime_receipt(self, target):
        type_ts = (target or {}).get("last_realtime_type_ts")
        type_ts = type_ts if isinstance(type_ts, dict) else {}
        return any(self._safe_float(value, 0.0) > 0 for value in type_ts.values())

    def _apply_registered_item_budget(
        self,
        normalized_codes,
        register_items,
        *,
        enforce=False,
        replacement_codes=(),
    ):
        if not enforce:
            return normalized_codes, register_items, []
        max_items = self._max_registered_item_count()
        if max_items <= 0:
            return normalized_codes, register_items, []

        items_by_code = self._items_by_code(normalized_codes, register_items)
        replacement_code_set = set(replacement_codes or ())
        allowed_codes = []
        allowed_items = []
        skipped_codes = []

        with self.lock:
            planned_item_count = sum(
                len(tuple(items or ()))
                for code, items in self._registered_items_by_code.items()
                if not is_pinned_ws_observation_registration(code, tuple(items or ()))
            )
            for code in normalized_codes or []:
                candidate_items = tuple(items_by_code.get(code) or ())
                if not candidate_items:
                    continue
                existing_items = tuple(self._registered_items_by_code.get(code) or ())
                delta_items = [
                    item for item in candidate_items if item not in existing_items
                ]
                if code in replacement_code_set:
                    required_delta = max(0, len(candidate_items) - len(existing_items))
                elif code not in self.subscribed_codes:
                    required_delta = len(candidate_items)
                else:
                    required_delta = len(delta_items)
                pinned_registration = is_pinned_ws_observation_registration(
                    code, candidate_items
                )
                if (
                    not pinned_registration
                    and required_delta > 0
                    and planned_item_count + required_delta > max_items
                ):
                    skipped_codes.append(code)
                    continue
                if not pinned_registration:
                    planned_item_count += max(0, required_delta)
                allowed_codes.append(code)
                allowed_items.extend(candidate_items)

        return allowed_codes, list(OrderedDict.fromkeys(allowed_items)), skipped_codes

    @staticmethod
    def _recent_reg_ttl_sec():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC")
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 20.0
        except Exception:
            value = 20.0
        return max(0.0, min(value, 120.0))

    def _filter_recent_reg_targets(self, codes, *, force=False):
        normalized_codes = self._normalize_subscribe_codes(codes)
        if not normalized_codes:
            return normalized_codes, []
        ttl_sec = self._recent_reg_ttl_sec()
        if ttl_sec <= 0:
            return normalized_codes, []
        now_ts = time.time()
        allowed = []
        skipped = []
        with self.lock:
            stale_codes = [
                code
                for code, last_ts in self._recent_reg_request_ts.items()
                if now_ts - float(last_ts or 0.0) >= ttl_sec
            ]
            for code in stale_codes:
                self._recent_reg_request_ts.pop(code, None)
            for code in normalized_codes:
                last_ts = float(self._recent_reg_request_ts.get(code) or 0.0)
                if last_ts > 0 and now_ts - last_ts < ttl_sec:
                    skipped.append(code)
                    continue
                self._recent_reg_request_ts[code] = now_ts
                allowed.append(code)
        return allowed, skipped

    @staticmethod
    def _alternate_route_max_codes():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES")
        try:
            value = int(str(raw).strip()) if str(raw).strip() else 6
        except Exception:
            value = 6
        return max(0, min(value, 32))

    @staticmethod
    def _alternate_route_ttl_sec():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC")
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 45.0
        except Exception:
            value = 45.0
        return max(0.0, min(value, 1800.0))

    def _filter_alternate_route_targets(self, codes):
        normalized_codes = self._normalize_subscribe_codes(codes)
        if not normalized_codes:
            return [], []
        max_codes = self._alternate_route_max_codes()
        if max_codes <= 0:
            return [], normalized_codes
        ttl_sec = self._alternate_route_ttl_sec()
        now_ts = time.time()
        allowed = []
        skipped = []
        with self.lock:
            if ttl_sec > 0:
                stale_codes = [
                    code
                    for code, last_ts in self._alternate_route_request_ts.items()
                    if now_ts - float(last_ts or 0.0) >= ttl_sec
                ]
                for code in stale_codes:
                    self._alternate_route_request_ts.pop(code, None)
            for code in normalized_codes:
                last_ts = float(self._alternate_route_request_ts.get(code) or 0.0)
                if ttl_sec > 0 and last_ts > 0 and now_ts - last_ts < ttl_sec:
                    skipped.append(code)
                    continue
                if len(allowed) >= max_codes:
                    skipped.append(code)
                    continue
                self._alternate_route_request_ts[code] = now_ts
                allowed.append(code)
        return allowed, skipped

    @staticmethod
    def _persistent_repair_max_codes():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES")
        try:
            value = int(str(raw).strip()) if str(raw).strip() else 8
        except Exception:
            value = 8
        return max(0, min(value, 32))

    @staticmethod
    def _persistent_repair_ttl_sec():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC")
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 30.0
        except Exception:
            value = 30.0
        return max(0.0, min(value, 1800.0))

    @staticmethod
    def _persistent_repair_max_codes_per_window():
        raw = _ws_hot_or_env_value(
            "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES_PER_WINDOW"
        )
        try:
            value = int(str(raw).strip()) if str(raw).strip() else 12
        except Exception:
            value = 12
        return max(1, min(value, 64))

    @staticmethod
    def _persistent_repair_window_sec():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_WINDOW_SEC")
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 60.0
        except Exception:
            value = 60.0
        return max(1.0, min(value, 600.0))

    def _prune_persistent_repair_window_locked(self, now_ts):
        window_start = float(now_ts) - self._persistent_repair_window_sec()
        while (
            self._persistent_repair_window_epochs
            and float(self._persistent_repair_window_epochs[0]) < window_start
        ):
            self._persistent_repair_window_epochs.popleft()

    @staticmethod
    def _persistent_repair_stuck_min_attempts():
        raw = _ws_hot_or_env_value(
            "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS"
        )
        try:
            value = int(str(raw).strip()) if str(raw).strip() else 3
        except Exception:
            value = 3
        return max(0, min(value, 20))

    @staticmethod
    def _persistent_repair_stuck_cooldown_sec():
        raw = _ws_hot_or_env_value(
            "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC"
        )
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 240.0
        except Exception:
            value = 240.0
        return max(0.0, min(value, 1800.0))

    @staticmethod
    def _persistent_repair_rebuild_group_enabled():
        raw = str(
            _ws_hot_or_env_value(
                "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED"
            )
            or ""
        )
        return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}

    @staticmethod
    def _persistent_repair_rebuild_group_min_interval_sec():
        raw = _ws_hot_or_env_value(
            "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC"
        )
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 60.0
        except Exception:
            value = 60.0
        return max(0.0, min(value, 600.0))

    def _persistent_repair_rebuild_targets(self, repair_targets):
        normalized_targets = self._normalize_subscribe_codes(repair_targets)
        if (
            not normalized_targets
            or not self._persistent_repair_rebuild_group_enabled()
        ):
            return False, normalized_targets
        now_ts = time.time()
        min_interval_sec = self._persistent_repair_rebuild_group_min_interval_sec()
        with self.lock:
            last_ts = float(self._last_persistent_repair_rebuild_ts or 0.0)
            if (
                min_interval_sec > 0
                and last_ts > 0
                and now_ts - last_ts < min_interval_sec
            ):
                return False, normalized_targets
            merged_targets = list(
                OrderedDict.fromkeys(
                    list(sorted(self.subscribed_codes)) + list(normalized_targets)
                )
            )
            self._prune_persistent_repair_window_locked(now_ts)
            additional_targets = [
                code for code in merged_targets if code not in normalized_targets
            ]
            remaining = max(
                0,
                self._persistent_repair_max_codes_per_window()
                - len(self._persistent_repair_window_epochs),
            )
            if len(additional_targets) > remaining:
                # A whole-group rebuild is optional recovery.  Fall back to
                # the already-budgeted targeted REG rather than letting it
                # bypass the global repair window.
                return False, normalized_targets
            self._persistent_repair_window_epochs.extend(
                [now_ts] * len(additional_targets)
            )
            self._last_persistent_repair_rebuild_ts = now_ts
            # The rebuild REG packet covers every merged target.  Share that
            # send timestamp with the targeted-repair throttle so a code
            # included in the group cannot be re-registered again immediately
            # by the per-code recovery path.  Only the original gap targets
            # increment no-tick attempts in _filter_persistent_repair_targets.
            for code in merged_targets:
                self._persistent_repair_request_ts[code] = now_ts
        return True, merged_targets

    def get_subscription_freshness_snapshot(self, codes=None, *, now_ts=None):
        """Return client-side freshness state for subscribed websocket symbols."""
        now_value = time.time() if now_ts is None else float(now_ts)
        stale_after_sec = self._freshness_stale_sec()
        requested_codes = self._normalize_subscribe_codes(codes) if codes else None
        rows = []
        with self.lock:
            target_codes = requested_codes or sorted(self.subscribed_codes)
            registered_item_count = self._registered_item_count_locked()
            for code in target_codes:
                target = self.realtime_data.get(code) or {}
                type_ts = target.get("last_realtime_type_ts")
                type_ts = type_ts if isinstance(type_ts, dict) else {}
                numeric_type_ts = [
                    float(value)
                    for value in type_ts.values()
                    if isinstance(value, (int, float)) and float(value) > 0
                ]
                realtime_type_age_sec = {}
                for realtime_type in ("0B", "0D", "0w", "0F"):
                    raw_type_ts = type_ts.get(realtime_type)
                    type_receive_ts = (
                        float(raw_type_ts)
                        if isinstance(raw_type_ts, (int, float))
                        and float(raw_type_ts) > 0
                        else 0.0
                    )
                    realtime_type_age_sec[realtime_type] = (
                        round(max(0.0, now_value - type_receive_ts), 3)
                        if type_receive_ts > 0
                        else None
                    )
                last_ws_update_ts = float(target.get("last_ws_update_ts") or 0.0)
                last_trade_tick = target.get("last_trade_tick")
                last_trade_tick = (
                    last_trade_tick if isinstance(last_trade_tick, dict) else {}
                )
                last_trade_cum_volume = (
                    self._safe_abs_int(last_trade_tick.get("cum_volume"), None)
                    if last_trade_tick.get("cum_volume") not in (None, "")
                    else None
                )
                last_receive_ts = (
                    max([last_ws_update_ts] + numeric_type_ts)
                    if (last_ws_update_ts > 0 or numeric_type_ts)
                    else 0.0
                )
                age_sec = (
                    round(max(0.0, now_value - last_receive_ts), 3)
                    if last_receive_ts > 0
                    else None
                )
                registered_items = tuple(self._registered_items_by_code.get(code) or ())
                required_realtime_types = tuple(
                    self._required_realtime_types_by_code.get(code) or ()
                )
                required_realtime_received = (
                    self._required_realtime_types_received_locked(code, target)
                )
                required_realtime_missing_types = [
                    realtime_type
                    for realtime_type in required_realtime_types
                    if self._safe_float(type_ts.get(realtime_type), 0.0) <= 0
                ]
                registered_route_counts = self._ws_item_route_counts(registered_items)
                registered_market_suffixes = [
                    self._ws_item_market_suffix(item) for item in registered_items
                ]
                registered_market_routes = [
                    self._ws_item_route(item) for item in registered_items
                ]
                subscribed = code in self.subscribed_codes
                if not subscribed:
                    freshness_state = "unsubscribed"
                elif last_receive_ts <= 0:
                    freshness_state = "no_tick"
                elif age_sec is not None and age_sec >= stale_after_sec:
                    freshness_state = "stale"
                else:
                    freshness_state = "fresh"
                non_trade_type_fresh = any(
                    type_age is not None and type_age < stale_after_sec
                    for type_age in (
                        realtime_type_age_sec["0D"],
                        realtime_type_age_sec["0w"],
                        realtime_type_age_sec["0F"],
                    )
                )
                last_0b_age_sec = realtime_type_age_sec["0B"]
                trade_tick_quiet = bool(
                    subscribed
                    and freshness_state == "fresh"
                    and non_trade_type_fresh
                    and (last_0b_age_sec is None or last_0b_age_sec >= stale_after_sec)
                )
                if subscribed and freshness_state == "no_tick":
                    repair_reason = "subscription_no_tick"
                elif subscribed and not required_realtime_received:
                    repair_reason = "subscription_required_realtime_missing"
                elif subscribed and freshness_state == "stale":
                    repair_reason = "subscription_stale"
                else:
                    repair_reason = "none"
                rows.append(
                    {
                        "stock_code": code,
                        "subscribed": subscribed,
                        "freshness_state": freshness_state,
                        "last_receive_ts": last_receive_ts,
                        "last_receive_age_sec": age_sec,
                        "stale_after_sec": stale_after_sec,
                        "received_types": sorted(
                            list(target.get("received_types") or [])
                        ),
                        "required_realtime_types": list(required_realtime_types),
                        "required_realtime_received": required_realtime_received,
                        "required_realtime_missing_types": required_realtime_missing_types,
                        "last_0b_age_sec": last_0b_age_sec,
                        "last_0d_age_sec": realtime_type_age_sec["0D"],
                        "last_0w_age_sec": realtime_type_age_sec["0w"],
                        "last_0f_age_sec": realtime_type_age_sec["0F"],
                        "last_trade_cum_volume": last_trade_cum_volume,
                        "trade_tick_quiet": trade_tick_quiet,
                        "trade_tick_quiet_reason": (
                            "fresh_non_trade_ws_without_fresh_0b"
                            if trade_tick_quiet
                            else "none"
                        ),
                        "registered_items": list(registered_items),
                        "registered_item_count": len(registered_items),
                        "registered_item_quota_units": len(registered_items),
                        "registered_market_suffixes": registered_market_suffixes,
                        "registered_market_routes": registered_market_routes,
                        "registered_route_counts": registered_route_counts,
                        "multi_route_registered": len(set(registered_market_routes))
                        > 1,
                        "route_repair_policy": "remove_then_reg_required_for_route_transition",
                        "total_registered_item_count": registered_item_count,
                        "repair_recommended": subscribed
                        and (
                            freshness_state in {"no_tick", "stale"}
                            or not required_realtime_received
                        ),
                        "repair_reason": repair_reason,
                        "recommended_repair": (
                            "remove_then_reg_backoff"
                            if subscribed
                            and (
                                freshness_state in {"no_tick", "stale"}
                                or not required_realtime_received
                            )
                            else "none"
                        ),
                        "decision_authority": "ws_freshness_source_quality_only",
                        "runtime_effect": False,
                        "broker_order_forbidden": True,
                    }
                )
        return {
            "generated_at_ts": now_value,
            "stale_after_sec": stale_after_sec,
            "registered_item_count": sum(row["registered_item_count"] for row in rows),
            "rows": rows,
        }

    def _filter_persistent_repair_targets(self, codes):
        normalized_codes = self._normalize_subscribe_codes(codes)
        if not normalized_codes:
            return [], []
        max_codes = self._persistent_repair_max_codes()
        if max_codes <= 0:
            return [], normalized_codes
        ttl_sec = self._persistent_repair_ttl_sec()
        now_ts = time.time()
        allowed = []
        skipped = []
        overflow_skipped = []
        stuck_skipped = []
        window_skipped = []
        with self.lock:
            self._prune_persistent_repair_window_locked(now_ts)
            window_limit = self._persistent_repair_max_codes_per_window()
            requested_set = set(normalized_codes)
            for code in list(self._persistent_repair_stuck_until_ts.keys()):
                if now_ts >= float(
                    self._persistent_repair_stuck_until_ts.get(code) or 0.0
                ):
                    self._persistent_repair_stuck_until_ts.pop(code, None)
            for code in list(self._persistent_repair_overflow_codes.keys()):
                if code not in requested_set:
                    self._persistent_repair_overflow_codes.pop(code, None)
            overflow_first = [
                code
                for code in self._persistent_repair_overflow_codes.keys()
                if code in requested_set
            ]
            if overflow_first:
                overflow_set = set(overflow_first)
                normalized_codes = overflow_first + [
                    code for code in normalized_codes if code not in overflow_set
                ]
            active_codes = []
            for code in normalized_codes:
                stuck_until = float(
                    self._persistent_repair_stuck_until_ts.get(code) or 0.0
                )
                if stuck_until > now_ts:
                    skipped.append(code)
                    stuck_skipped.append(code)
                    continue
                active_codes.append(code)
            normalized_codes = active_codes
            if ttl_sec > 0:
                stale_codes = [
                    code
                    for code, last_ts in self._persistent_repair_request_ts.items()
                    if now_ts - float(last_ts or 0.0) >= ttl_sec
                ]
                for code in stale_codes:
                    self._persistent_repair_request_ts.pop(code, None)
            for code in normalized_codes:
                last_ts = float(self._persistent_repair_request_ts.get(code) or 0.0)
                if ttl_sec > 0 and last_ts > 0 and now_ts - last_ts < ttl_sec:
                    skipped.append(code)
                    continue
                if len(allowed) >= max_codes:
                    skipped.append(code)
                    overflow_skipped.append(code)
                    continue
                if len(self._persistent_repair_window_epochs) >= window_limit:
                    skipped.append(code)
                    overflow_skipped.append(code)
                    window_skipped.append(code)
                    continue
                self._persistent_repair_request_ts[code] = now_ts
                self._persistent_repair_window_epochs.append(now_ts)
                self._note_persistent_repair_attempt_locked(code, now_ts)
                self._persistent_repair_overflow_codes.pop(code, None)
                allowed.append(code)
            for code in overflow_skipped:
                self._persistent_repair_overflow_codes[code] = now_ts
            while len(self._persistent_repair_overflow_codes) > 200:
                self._persistent_repair_overflow_codes.popitem(last=False)
        if stuck_skipped:
            print(
                "🧯 [WS] persistent repair stuck cooldown: "
                f"skipped={stuck_skipped} "
                f"cooldown_sec={self._persistent_repair_stuck_cooldown_sec():.1f}"
            )
        if window_skipped:
            print(
                "🧯 [WS] persistent repair global window limit: "
                f"skipped={window_skipped} "
                f"max_codes={self._persistent_repair_max_codes_per_window()} "
                f"window_sec={self._persistent_repair_window_sec():.1f}"
            )
        return allowed, skipped

    def _note_persistent_repair_attempt_locked(self, code, now_ts):
        target = self.realtime_data.get(code) or {}
        required_received = self._required_realtime_types_received_locked(code, target)
        if required_received and (
            target.get("_first_tick_logged")
            or self._is_ws_ready(target, require_trade=False)
        ):
            self._persistent_repair_no_tick_attempts.pop(code, None)
            self._persistent_repair_stuck_until_ts.pop(code, None)
            return
        # A receipt clears the generic no-tick counter only when this
        # subscription has no stricter required-type contract.  Scanner
        # subscriptions require 0B: repeatedly receiving quote-only packets
        # must still converge to the bounded stuck cooldown, otherwise each
        # quote receipt resets the counter and REMOVE/REG repair can run
        # forever.
        required_types = tuple(self._required_realtime_types_by_code.get(code) or ())
        if not required_types and self._has_any_realtime_receipt(target):
            self._persistent_repair_no_tick_attempts.pop(code, None)
            self._persistent_repair_stuck_until_ts.pop(code, None)
            return
        min_attempts = self._persistent_repair_stuck_min_attempts()
        cooldown_sec = self._persistent_repair_stuck_cooldown_sec()
        if min_attempts <= 0 or cooldown_sec <= 0:
            return
        attempts = int(self._persistent_repair_no_tick_attempts.get(code) or 0) + 1
        self._persistent_repair_no_tick_attempts[code] = attempts
        if attempts >= min_attempts:
            self._persistent_repair_stuck_until_ts[code] = now_ts + cooldown_sec
            self._persistent_repair_no_tick_attempts[code] = 0
            print(
                "🧯 [WS] persistent repair no-tick cooldown entered: "
                f"code={code} attempts={attempts} cooldown_sec={cooldown_sec:.1f}"
            )

    @staticmethod
    def _parse_condition_list_rows(data_list):
        rows = []
        for entry in data_list or []:
            seq = ""
            name = ""
            if isinstance(entry, dict):
                seq = str(
                    entry.get("seq")
                    or entry.get("cond_seq")
                    or entry.get("search_seq")
                    or entry.get("id")
                    or ""
                ).strip()
                name = str(
                    entry.get("condition_name")
                    or entry.get("cond_nm")
                    or entry.get("name")
                    or entry.get("search_name")
                    or ""
                ).strip()
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                seq = str(entry[0] or "").strip()
                name = str(entry[1] or "").strip()

            if seq or name:
                rows.append((seq, name))
        return rows

    def _append_strength_momentum(
        self,
        target,
        *,
        current_price,
        current_vpw,
        signed_qty,
        tick_value,
        buy_ratio,
        buy_qty,
        sell_qty,
        aggressor_side="UNKNOWN",
        tick_value_source="unknown",
    ):
        history = target.get("strength_momentum_history")
        if not isinstance(history, deque):
            maxlen = int(getattr(TRADING_RULES, "SCALP_VPW_HISTORY_MAXLEN", 120) or 120)
            history = deque(maxlen=maxlen)
            target["strength_momentum_history"] = history

        buy_tick_value = 0
        sell_tick_value = 0
        tick_direction_source = "unknown"
        if signed_qty > 0:
            buy_tick_value = tick_value
            tick_direction_source = "signed_trade_volume"
        elif signed_qty < 0:
            sell_tick_value = tick_value
            tick_direction_source = "signed_trade_volume"
        elif str(aggressor_side or "").upper() == "BUY":
            buy_tick_value = tick_value
            tick_direction_source = "trusted_aggressor"
        elif str(aggressor_side or "").upper() == "SELL":
            sell_tick_value = tick_value
            tick_direction_source = "trusted_aggressor"

        now_ts = time.time()
        history.append(
            {
                "ts": now_ts,
                "v_pw": float(current_vpw or 0.0),
                "price": int(current_price or 0),
                "signed_qty": int(signed_qty or 0),
                "buy_qty": int(buy_qty or 0),
                "sell_qty": int(sell_qty or 0),
                "buy_exec_qty_cum": int(buy_qty or 0),
                "sell_exec_qty_cum": int(sell_qty or 0),
                "tick_value": int(tick_value or 0),
                "tick_value_source": str(tick_value_source or "unknown"),
                "tick_direction_source": tick_direction_source,
                "buy_tick_value": int(buy_tick_value or 0),
                "sell_tick_value": int(sell_tick_value or 0),
                "buy_ratio": float(buy_ratio or 0.0),
            }
        )

        keep_seconds = max(
            15.0,
            float(getattr(TRADING_RULES, "SCALP_VPW_WINDOW_SECONDS", 5) or 5) * 3.0,
        )
        cutoff = now_ts - keep_seconds
        while history and float((history[0] or {}).get("ts", 0.0) or 0.0) < cutoff:
            history.popleft()

    def _ensure_target_defaults(self, item_code):
        if item_code not in self.realtime_data:
            history_maxlen = int(
                getattr(TRADING_RULES, "SCALP_VPW_HISTORY_MAXLEN", 120) or 120
            )
            self.realtime_data[item_code] = {
                "curr": 0,
                "v_pw": 0,
                "ask_tot": 0,
                "bid_tot": 0,
                "volume": 0,
                "time": "",
                "fluctuation": 0.0,
                "open": 0,
                "high": 0,
                "low": 0,
                "orderbook": {"asks": [], "bids": []},
                "expected_open": {"price": 0, "qty": 0, "source": ""},
                "prog_net_qty": 0,
                "prog_delta_qty": 0,
                "prog_net_amt": 0,
                "prog_delta_amt": 0,
                "prog_buy_qty": 0,
                "prog_buy_amt": 0,
                "prog_sell_qty": 0,
                "prog_sell_amt": 0,
                "foreign_broker_sell_est_qty": 0,
                "foreign_broker_sell_est_delta_qty": 0,
                "foreign_broker_buy_est_qty": 0,
                "foreign_broker_buy_est_delta_qty": 0,
                "foreign_broker_net_est_qty": 0,
                "foreign_broker_net_est_delta_qty": 0,
                "tick_trade_value": 0,
                "tick_trade_value_source": "unknown",
                "tick_trade_value_fallback_volume_source": "none",
                "cum_trade_value": 0,
                "buy_exec_volume": 0,
                "sell_exec_volume": 0,
                "buy_ratio": 0.0,
                "net_buy_exec_volume": 0,
                "trade_volume_source": "unknown",
                "trade_volume_1030_1031_vs_15_mismatch": False,
                "trade_volume_1030_1031_vs_15_delta": None,
                "kiwoom_0b_aux_observed_count": 0,
                "kiwoom_0b_1313_present_count": 0,
                "kiwoom_0b_1313_missing_count": 0,
                "kiwoom_0b_trade_value_source_counts": {},
                "kiwoom_0b_trade_volume_source_counts": {},
                "kiwoom_0b_1030_1031_vs_15_evaluable_count": 0,
                "kiwoom_0b_1030_1031_vs_15_mismatch_count": 0,
                "sell_exec_single": 0,
                "buy_exec_single": 0,
                "net_bid_depth": 0,
                "bid_depth_ratio": 0.0,
                "net_ask_depth": 0,
                "ask_depth_ratio": 0.0,
                "market_session_state": self.market_session_state,
                "market_session_remaining": self.market_session_remaining,
                "last_ws_item": "",
                "last_ws_market_suffix": "",
                "last_ws_market_route": "unknown",
                "last_realtime_type_item": {},
                "last_realtime_type_market_suffix": {},
                "last_realtime_type_market_route": {},
                "last_realtime_type_effective_venue": {},
                "realtime_type_snapshots_by_route": {},
                "received_types": set(),
                "last_ws_update_ts": 0.0,
                "last_realtime_type_ts": {},
                "last_prog_update_ts": 0.0,
                "program_subscription_requested_at": 0.0,
                "program_first_observed_at": 0.0,
                "program_first_observed_latency_ms": None,
                "program_missing_reason": "program_0w_not_registered_or_observed",
                "program_freshness_limit_ms": 60_000.0,
                "last_foreign_broker_update_ts": 0.0,
                "program_history": deque(maxlen=120),
                "strength_momentum_history": deque(maxlen=history_maxlen),
                "recent_trade_ticks": deque(maxlen=120),
                "recent_trade_ticks_by_route": {},
                "_first_tick_logged": False,
                "last_trade_tick": None,
                "top_of_book_cache": self._get_tob_cache(item_code),
            }
        return self.realtime_data[item_code]

    def _update_micro_estimator_from_orderbook(self, item_code, target, *, now_ts):
        if not _micro_estimator_ws_observation_enabled():
            return

        def positive_int(value):
            try:
                parsed = int(float(value or 0))
            except (TypeError, ValueError):
                return 0
            return parsed if parsed > 0 else 0

        orderbook = target.get("orderbook") if isinstance(target, dict) else {}
        asks = orderbook.get("asks") if isinstance(orderbook, dict) else []
        bids = orderbook.get("bids") if isinstance(orderbook, dict) else []
        if not asks or not bids:
            return
        best_ask = positive_int((asks[0] or {}).get("price"))
        best_bid = positive_int((bids[0] or {}).get("price"))
        best_ask_qty = positive_int((asks[0] or {}).get("volume"))
        best_bid_qty = positive_int((bids[0] or {}).get("volume"))
        ask_tot = positive_int(target.get("ask_tot")) or sum(
            positive_int((level or {}).get("volume")) for level in asks
        )
        bid_tot = positive_int(target.get("bid_tot")) or sum(
            positive_int((level or {}).get("volume")) for level in bids
        )
        if best_ask <= 0 or best_bid <= 0 or best_ask_qty <= 0 or best_bid_qty <= 0:
            return
        quote = {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "best_bid_qty": best_bid_qty,
            "best_ask_qty": best_ask_qty,
            "bid_tot": bid_tot,
            "ask_tot": ask_tot,
            "quote_age_ms": 0.0,
            "quote_stale": False,
            "source_quality_state": "fresh_ws_orderbook_observation",
        }
        try:
            state = MICRO_ESTIMATOR_STORE.update_from_ws_quote(
                item_code,
                quote,
                now_ts=float(now_ts),
                tier="warm",
            )
        except Exception as exc:
            log_error(
                f"[MICRO_ESTIMATOR_WS_OBSERVATION] update failed code={item_code}: {exc}"
            )
            return
        target["micro_estimator_ws_observation_ts"] = float(now_ts)
        target["micro_estimator_ws_observation_source"] = "0D_orderbook"
        target["micro_estimator_ws_observation_sample_count"] = int(
            getattr(state, "sample_count", 0) or 0
        )
        target["micro_estimator_ws_observation_true_ofi_sample_count"] = int(
            getattr(state, "true_ofi_sample_count", 0) or 0
        )

    @staticmethod
    def _has_orderbook(target):
        ob = target.get("orderbook") or {}
        return bool(ob.get("asks")) or bool(ob.get("bids"))

    def _is_ws_ready(self, target, require_trade=False):
        if not target:
            return False

        received_types = target.get("received_types") or set()
        has_trade = target.get("curr", 0) > 0 or ("0B" in received_types)
        has_orderbook = self._has_orderbook(target)
        has_program = "0w" in received_types
        has_timestamp = bool(target.get("time")) or bool(
            target.get("last_ws_update_ts")
        )

        if require_trade:
            return has_trade
        return has_trade or has_orderbook or has_program or has_timestamp

    def wait_for_data(self, code, timeout=2.0, require_trade=False, poll_interval=0.05):
        """REG 전송 후 첫 WS 데이터가 실제로 들어올 때까지 대기합니다."""
        code = self._normalize_code(code)
        if not code:
            return {}

        deadline = time.time() + max(0.0, float(timeout or 0.0))
        latest = {}

        while time.time() < deadline and not self._stop_event.is_set():
            latest = self.get_latest_data(code) or {}
            if self._is_ws_ready(latest, require_trade=require_trade):
                return latest
            time.sleep(max(0.01, float(poll_interval or 0.05)))

        return self.get_latest_data(code) or latest or {}

    def _snapshot_target(self, target):
        snapshot = copy.deepcopy(target)
        snapshot["market_session_state"] = self.market_session_state
        snapshot["market_session_remaining"] = self.market_session_remaining
        for key in (
            "price_history",
            "v_pw_history",
            "signed_volume_history",
            "program_history",
            "strength_momentum_history",
            "recent_trade_ticks",
        ):
            if isinstance(snapshot.get(key), deque):
                snapshot[key] = list(snapshot[key])
        route_ticks = snapshot.get("recent_trade_ticks_by_route")
        if isinstance(route_ticks, dict):
            snapshot["recent_trade_ticks_by_route"] = {
                str(route_key): (
                    list(rows) if isinstance(rows, deque) else list(rows or [])
                )
                for route_key, rows in route_ticks.items()
            }
        return snapshot

    def _maybe_write_dashboard_snapshot(self):
        now_ts = time.time()
        if (
            self._dashboard_snapshot_write_inflight
            or now_ts - float(self._last_dashboard_snapshot_at or 0.0)
            < _ws_dashboard_snapshot_interval_sec()
        ):
            return
        self._last_dashboard_snapshot_at = now_ts
        self._dashboard_snapshot_write_inflight = True

        def _write_snapshot_async():
            try:
                write_ws_snapshot(self.realtime_data, now_ts=now_ts)
            except Exception as e:
                log_error(f"[WS] dashboard snapshot write failed: {e}")
            finally:
                self._dashboard_snapshot_write_inflight = False

        threading.Thread(
            target=_write_snapshot_async, name="bd-fbuy-ws-snapshot", daemon=True
        ).start()

    def _enqueue_state_event(self, event_type, payload):
        if self._stop_event.is_set():
            return
        self._state_event_queue.put((event_type, payload or {}))

    def _defer_scalp_condition_match(self, payload):
        code = str((payload or {}).get("code") or "").replace("A", "").strip()[:6]
        condition_name = str(
            (payload or {}).get("condition_name") or "UNKNOWN_CONDITION"
        )
        if not code or not _is_scalp_condition_name(condition_name):
            return
        deferred_payload = {
            **(payload or {}),
            "code": code,
            "type": "DEFERRED_BUY_WINDOW",
        }
        key = (condition_name, code)
        self._deferred_scalp_condition_matches[key] = deferred_payload
        while len(self._deferred_scalp_condition_matches) > 300:
            self._deferred_scalp_condition_matches.popitem(last=False)
        if (
            is_scalping_prewarm_time_allowed()
            and code not in self._scalp_condition_prewarm_codes
            and len(self._scalp_condition_prewarm_codes)
            < SCALP_CONDITION_PREWARM_MAX_CODES
        ):
            self._scalp_condition_prewarm_codes[code] = time.time()
            self.event_bus.publish(
                "COMMAND_WS_REG",
                {
                    "codes": [code],
                    "source": "scanner_condition_buy_window_prewarm",
                    "required_realtime_types": ("0B",),
                    "runtime_effect": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        print(
            "[WS_CONDITION_BUY_WINDOW_DEFERRED] 스캘핑 조건검색 편입 보류 "
            f"condition={condition_name} code={code} "
            f"buy_windows={describe_scalping_buy_windows()}"
        )

    def _drop_deferred_scalp_condition_match(self, code, condition_name):
        normalized_code = str(code or "").replace("A", "").strip()[:6]
        normalized_name = str(condition_name or "UNKNOWN_CONDITION")
        if not normalized_code:
            return
        self._deferred_scalp_condition_matches.pop(
            (normalized_name, normalized_code), None
        )
        self._scalp_condition_prewarm_codes.pop(normalized_code, None)

    def _flush_deferred_scalp_condition_matches_if_allowed(self):
        if not self._deferred_scalp_condition_matches:
            return
        if not is_ws_condition_search_enabled() or not is_scalping_buy_time_allowed():
            return
        payloads = list(self._deferred_scalp_condition_matches.values())
        self._deferred_scalp_condition_matches.clear()
        self._scalp_condition_prewarm_codes.clear()
        for payload in payloads:
            self._enqueue_state_event("CONDITION_MATCHED", payload)
        print(
            "[WS_CONDITION_BUY_WINDOW_FLUSH] 스캘핑 조건검색 보류 편입 등록 "
            f"count={len(payloads)} buy_windows={describe_scalping_buy_windows()}"
        )

    def _dispatch_state_events(self):
        while not self._stop_event.is_set():
            try:
                event_type, payload = self._state_event_queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                self.event_bus.publish(event_type, payload)
            except Exception as e:
                log_error(f"[WS] state event dispatch failed ({event_type}): {e}")

    def _queue_tick_event(self, code, data, *, realtime_type="0B"):
        if self._stop_event.is_set():
            return

        normalized_realtime_type = str(realtime_type or "").strip()
        if normalized_realtime_type in {"0B", "0D"}:
            self._observe_micro_reversion_forward(
                code, data, realtime_type=normalized_realtime_type
            )
        normalized_code = self._normalize_code(code)
        with self.lock:
            observation_only = (
                normalized_code in self._micro_reversion_observation_only_codes
            )
        if observation_only:
            return
        if normalized_realtime_type in {"0B", "0D"}:
            try:
                observe_raw_market_data(
                    code,
                    data,
                    time.time(),
                    realtime_type=normalized_realtime_type,
                )
            except Exception as exc:
                log_error(
                    "[WS] limit-down raw market-data observation failed "
                    f"({code}/{normalized_realtime_type}): {exc}"
                )
        with self._tick_lock:
            self._pending_tick_events[code] = {"code": code, "data": data}
        self._tick_dispatch_event.set()

    def _start_micro_reversion_forward_collector(self):
        """Lazy-load the default-off observer without changing subscriptions."""

        if not _env_bool("SCALP_MICRO_REVERSION_OBSERVER_ENABLED", False):
            self._micro_reversion_forward_collector = None
            self._micro_reversion_forward_collector_error = ""
            self._micro_reversion_forward_collector_stop_reason = ""
            self._micro_reversion_canary_monitor_stop_event.set()
            return
        if self._micro_reversion_forward_collector_stop_reason:
            self._micro_reversion_forward_collector_error = "CanaryAutoStopLatched"
            log_error(
                "[WS] micro-reversion observer restart blocked by latched "
                f"canary stop ({self._micro_reversion_forward_collector_stop_reason})"
            )
            return
        if self._micro_reversion_forward_collector is not None:
            self._close_micro_reversion_forward_collector()
            if self._micro_reversion_forward_collector is not None:
                self._micro_reversion_forward_collector_error = (
                    "PreviousCollectorClosePending"
                )
                log_error(
                    "[WS] micro-reversion observer restart blocked while prior "
                    "collector close is pending"
                )
                return
        try:
            from src.engine.scalping.micro_reversion.forward_collector import (
                build_forward_collector_from_env,
            )

            collector = build_forward_collector_from_env(start=True)
        except Exception as exc:
            self._micro_reversion_forward_collector = None
            self._micro_reversion_forward_collector_error = type(exc).__name__
            log_error(
                f"[WS] micro-reversion forward observer startup isolated failure: {exc}"
            )
            return
        self._micro_reversion_forward_collector = collector
        self._micro_reversion_forward_collector_error = ""
        self._micro_reversion_forward_collector_stop_reason = ""
        try:
            self._start_micro_reversion_canary_monitor()
        except Exception as exc:
            self._micro_reversion_forward_collector_error = type(exc).__name__
            self._micro_reversion_forward_collector_stop_reason = (
                f"canary_monitor_start_failure:{type(exc).__name__}"
            )
            log_error(
                "[WS] micro-reversion canary monitor startup fail-closed "
                f"({type(exc).__name__}): {exc}"
            )
            self._close_micro_reversion_forward_collector()

    def _observe_micro_reversion_forward(self, code, data, *, realtime_type):
        collector = self._micro_reversion_forward_collector
        if collector is None:
            return
        try:
            normalized_type = str(realtime_type or "").strip()
            if normalized_type == "0B":
                collector.observe_kiwoom_0b(code, data, realtime_type="0B")
            elif normalized_type == "0D":
                collector.observe_kiwoom_0d(code, data, realtime_type="0D")
        except Exception as exc:
            self._micro_reversion_forward_collector_error = type(exc).__name__
            log_error(
                "[WS] micro-reversion forward observer callback isolated "
                f"failure ({code}): {exc}"
            )

    def _begin_micro_reversion_transport_epoch(self):
        """Rotate source-only collector state after a successful WS reconnect."""

        collector = self._micro_reversion_forward_collector
        if collector is None:
            return None
        try:
            return collector.begin_transport_epoch()
        except Exception as exc:
            reason = f"transport_epoch_failure:{type(exc).__name__}"
            self._micro_reversion_forward_collector_error = type(exc).__name__
            self._micro_reversion_forward_collector_stop_reason = reason
            log_error(
                f"[WS] micro-reversion reconnect epoch fail-closed ({reason}): {exc}"
            )
            # Collector shutdown can drain writers for up to ten seconds.  Do
            # not hold the websocket bootstrap coroutine (and therefore live
            # execution/session registration) on an observer-only failure.
            threading.Thread(
                target=self._close_micro_reversion_forward_collector,
                name="micro-reversion-epoch-failure-close",
                daemon=True,
            ).start()
            return None

    def _micro_reversion_depth_capture_requested(self):
        collector = self._micro_reversion_forward_collector
        flags = getattr(collector, "flags", None)
        return bool(getattr(flags, "depth_capture_active", False))

    @staticmethod
    def _build_micro_reversion_depth_tick(raw_item_code, values):
        def unsigned_int(value, default=0):
            normalized = str(value).replace("+", "").replace("-", "").strip()
            return int(normalized) if normalized.isdigit() else default

        ask_levels, bid_levels = [], []
        for level in range(1, 6):
            ask_price = unsigned_int(values.get(str(40 + level)))
            ask_qty = unsigned_int(values.get(str(60 + level)), None)
            bid_price = unsigned_int(values.get(str(50 + level)))
            bid_qty = unsigned_int(values.get(str(70 + level)), None)
            if ask_price > 0 and ask_qty is not None:
                ask_levels.append(
                    {"level": level, "price": ask_price, "quantity": ask_qty}
                )
            if bid_price > 0 and bid_qty is not None:
                bid_levels.append(
                    {"level": level, "price": bid_price, "quantity": bid_qty}
                )
        combined_ask = unsigned_int(values.get("121"), None)
        combined_bid = unsigned_int(values.get("125"), None)
        return {
            "item": str(raw_item_code or ""),
            "orderbook_time_raw": str(values.get("21") or "").strip(),
            "received_at_ms": int(time.time() * 1000),
            "ask_levels": ask_levels,
            "bid_levels": bid_levels,
            "ask_depth": combined_ask,
            "bid_depth": combined_bid,
            "route_depth_totals": {
                "combined": {"ask": combined_ask, "bid": combined_bid},
                "KRX": {
                    "ask": unsigned_int(values.get("6064"), None),
                    "bid": unsigned_int(values.get("6065"), None),
                },
                "NXT": {
                    "ask": unsigned_int(values.get("6086"), None),
                    "bid": unsigned_int(values.get("6087"), None),
                },
            },
        }

    def micro_reversion_forward_collector_snapshot(self):
        collector = self._micro_reversion_forward_collector
        if collector is None:
            return {
                "observer_runtime_loaded": False,
                "producer_observation_connected": False,
                "observer_runtime_effect": False,
                "trading_runtime_effect": False,
                "trading_decision_effect": False,
                "sim_position_effect": False,
                "threshold_effect": False,
                "broker_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "isolated_error_type": (
                    self._micro_reversion_forward_collector_error or None
                ),
                "canary_auto_stop_reason": (
                    self._micro_reversion_forward_collector_stop_reason or None
                ),
            }
        try:
            snapshot = collector.runtime_snapshot().as_dict()
            snapshot["canary_auto_stop_reason"] = (
                self._micro_reversion_forward_collector_stop_reason or None
            )
            snapshot["canary_latency_breach_consecutive_count"] = int(
                self._micro_reversion_canary_latency_breach_count
            )
            return snapshot
        except Exception as exc:
            self._micro_reversion_forward_collector_error = type(exc).__name__
            return {
                "observer_runtime_loaded": True,
                "producer_observation_connected": True,
                "observer_runtime_effect": False,
                "observation_capture_active": False,
                "trading_runtime_effect": False,
                "trading_decision_effect": False,
                "sim_position_effect": False,
                "threshold_effect": False,
                "broker_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "isolated_error_type": type(exc).__name__,
                "canary_auto_stop_reason": (
                    self._micro_reversion_forward_collector_stop_reason or None
                ),
            }

    def _persist_micro_reversion_canary_snapshot(self):
        """Persist and evaluate observer health outside the market-data lock."""

        with self._micro_reversion_canary_snapshot_lock:
            collector = self._micro_reversion_forward_collector
            if collector is None and not self._micro_reversion_forward_collector_error:
                return None
            from src.engine.scalping.micro_reversion.canary_monitor import (
                write_canary_runtime_snapshot,
            )

            return write_canary_runtime_snapshot(
                self.micro_reversion_forward_collector_snapshot()
            )

    def _start_micro_reversion_canary_monitor(self):
        """Start observer-only health monitoring outside producer callbacks."""

        if self._micro_reversion_forward_collector is None:
            return
        thread = self._micro_reversion_canary_monitor_thread
        if thread is not None and thread.is_alive():
            return
        self._micro_reversion_canary_monitor_stop_event.clear()
        self._micro_reversion_canary_monitor_thread = threading.Thread(
            target=self._run_micro_reversion_canary_monitor,
            name="micro-reversion-canary-monitor",
            daemon=True,
        )
        self._micro_reversion_canary_monitor_thread.start()

    def _run_micro_reversion_canary_monitor(self):
        while not self._micro_reversion_canary_monitor_stop_event.is_set():
            if self._micro_reversion_forward_collector is None:
                return
            try:
                monitor_payload = self._persist_micro_reversion_canary_snapshot()
            except Exception as exc:
                self._fail_closed_micro_reversion_canary_monitor(exc)
            else:
                self._enforce_micro_reversion_canary_guard(monitor_payload)
            if self._micro_reversion_forward_collector is None:
                return
            self._micro_reversion_canary_monitor_stop_event.wait(timeout=10.0)

    def _fail_closed_micro_reversion_canary_monitor(self, exc):
        if self._micro_reversion_forward_collector is None:
            return
        reason = f"canary_monitor_failure:{type(exc).__name__}"
        self._micro_reversion_forward_collector_error = type(exc).__name__
        self._micro_reversion_forward_collector_stop_reason = reason
        log_error(f"[WS] micro-reversion canary monitor fail-closed ({reason}): {exc}")
        self._close_micro_reversion_forward_collector()

    def _enforce_micro_reversion_canary_guard(self, monitor_payload):
        guard = (monitor_payload or {}).get("canary_guard") or {}
        if not guard.get("stop_required"):
            self._micro_reversion_canary_latency_breach_count = 0
            return
        reasons = tuple(str(row) for row in guard.get("stop_reasons") or ())
        reason = ";".join(reasons) or "unspecified_canary_guard_failure"
        latency_only = bool(reasons) and all(
            row.startswith("producer_callback_latency_p95_exceeded:")
            or row.startswith("producer_callback_latency_p99_exceeded:")
            for row in reasons
        )
        latency_metric_pairs = []
        if any(
            row.startswith("producer_callback_latency_p95_exceeded:") for row in reasons
        ):
            latency_metric_pairs.append(
                (
                    guard.get("observed_latency_p95_ms"),
                    guard.get("latency_p95_max_ms"),
                )
            )
        if any(
            row.startswith("producer_callback_latency_p99_exceeded:") for row in reasons
        ):
            latency_metric_pairs.append(
                (
                    guard.get("observed_latency_p99_ms"),
                    guard.get("latency_p99_max_ms"),
                )
            )
        try:
            latency_confirmation_snapshots = int(
                guard["latency_breach_confirmation_snapshots"]
            )
            latency_immediate_multiplier = float(
                guard["latency_breach_immediate_multiplier"]
            )
            if latency_confirmation_snapshots <= 0:
                raise ValueError("invalid latency confirmation floor")
            if latency_immediate_multiplier <= 1.0:
                raise ValueError("invalid immediate latency multiplier")
            severe_latency = latency_only and any(
                float(observed) >= float(limit) * latency_immediate_multiplier
                for observed, limit in latency_metric_pairs
            )
        except (KeyError, TypeError, ValueError):
            # Missing or malformed enforcement provenance cannot safely earn
            # a delayed observer shutdown.
            severe_latency = latency_only
        if latency_only and not severe_latency:
            self._micro_reversion_canary_latency_breach_count += 1
            if (
                self._micro_reversion_canary_latency_breach_count
                < latency_confirmation_snapshots
            ):
                # The persisted guard remains stop_required from the first
                # breach, so Provider replay and R3 stay fail-closed.  Keep
                # local source capture alive until the rolling 0B latency
                # breach persists across independent monitor snapshots.
                return
        else:
            self._micro_reversion_canary_latency_breach_count = 0
        if not self._micro_reversion_forward_collector_stop_reason:
            self._micro_reversion_forward_collector_stop_reason = reason
            log_error(
                f"[WS] micro-reversion observer canary auto-stop requested ({reason})"
            )
        self._close_micro_reversion_forward_collector()

    def _dispatch_tick_events(self):
        while not self._stop_event.is_set():
            triggered = self._tick_dispatch_event.wait(timeout=0.5)
            if not triggered:
                continue

            with self._tick_lock:
                pending_items = list(self._pending_tick_events.values())
                self._pending_tick_events.clear()
                self._tick_dispatch_event.clear()

            for payload in pending_items:
                try:
                    self.event_bus.publish("REALTIME_TICK_ARRIVED", payload)
                except Exception as e:
                    log_error(
                        f"[WS] tick event dispatch failed ({payload.get('code')}): {e}"
                    )

    def stop(self):
        if self._stop_event.is_set():
            self._micro_reversion_canary_monitor_stop_event.set()
            self._close_micro_reversion_forward_collector()
            return

        self._stop_event.set()
        self._micro_reversion_canary_monitor_stop_event.set()
        self._started = False
        self._session_ready.clear()
        self._tick_dispatch_event.set()
        self._cancel_pending_futures()

        try:
            self.event_bus.unsubscribe("COMMAND_WS_REG", self._handle_reg_event)
        except Exception:
            pass

        try:
            self.event_bus.unsubscribe("COMMAND_WS_UNREG", self._handle_unreg_event)
        except Exception:
            pass

        try:
            self.event_bus.unsubscribe(
                COMMAND_MICRO_REVERSION_OBSERVATION_SET,
                self._handle_micro_reversion_observation_set,
            )
        except Exception:
            pass

        ws = self.websocket
        if ws and self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(ws.close(), self.loop)
            except Exception as e:
                log_error(f"[WS] stop() websocket close failed: {e}")

        current_thread = threading.current_thread()
        for thread in [
            self._state_dispatch_thread,
            self._tick_dispatch_thread,
            self._ws_thread,
            self._micro_reversion_canary_monitor_thread,
        ]:
            if thread and thread is not current_thread and thread.is_alive():
                thread.join(timeout=2)

        self._close_micro_reversion_forward_collector()
        self.websocket = None

    def _close_micro_reversion_forward_collector(self):
        """Close the one-shot observer, retaining it when shutdown needs a retry."""

        with self._micro_reversion_forward_collector_close_lock:
            collector = self._micro_reversion_forward_collector
            if collector is None:
                return
            try:
                collector.close(timeout_sec=10.0)
            except Exception as exc:
                self._micro_reversion_forward_collector_error = type(exc).__name__
                log_error(
                    "[WS] micro-reversion forward observer shutdown isolated "
                    f"failure: {exc}"
                )
            else:
                if self._micro_reversion_forward_collector is collector:
                    final_snapshot_error = None
                    try:
                        self._persist_micro_reversion_canary_snapshot()
                    except Exception as exc:
                        final_snapshot_error = exc
                        log_error(
                            "[WS] micro-reversion final canary snapshot isolated "
                            f"failure: {exc}"
                        )
                    self._micro_reversion_forward_collector = None
                    self._micro_reversion_canary_monitor_stop_event.set()
                    if final_snapshot_error is None:
                        self._micro_reversion_forward_collector_error = ""
                    else:
                        self._micro_reversion_forward_collector_error = type(
                            final_snapshot_error
                        ).__name__

    @staticmethod
    def _is_login_success_message(msg_dict):
        if not isinstance(msg_dict, dict):
            return False
        if str(msg_dict.get("trnm", "") or "").strip().upper() != "LOGIN":
            return False
        code = msg_dict.get("return_code", msg_dict.get("rt_cd", ""))
        return str(code).strip() == "0"

    @staticmethod
    def _is_login_failure_message(msg_dict):
        if not isinstance(msg_dict, dict):
            return False
        if str(msg_dict.get("trnm", "") or "").strip().upper() != "LOGIN":
            return False
        code = str(msg_dict.get("return_code", msg_dict.get("rt_cd", ""))).strip()
        return bool(code) and code != "0"

    @staticmethod
    def _is_auth_token_failure(code, message):
        code_str = str(code or "").strip()
        msg = str(message or "")
        if "8005" in code_str:
            return True
        if "8005" in msg:
            return True
        if "Token" in msg or "토큰" in msg or "인증" in msg:
            return True
        return False

    @staticmethod
    def _ping_echo_payload(raw_message, parsed_message):
        if isinstance(raw_message, (str, bytes)):
            return raw_message
        return json.dumps(parsed_message)

    def _refresh_ws_token(self):
        now_ts = time.time()
        # 토큰 인증 실패 루프에서 과도한 재발급 스팸을 방지합니다.
        if now_ts - self._last_token_refresh_at < 5:
            return False

        try:
            from src.utils import kiwoom_utils

            previous_token = self.token
            new_token = kiwoom_utils.get_kiwoom_token(self.conf, force_refresh=True)
        except Exception as e:
            log_error(f"❌ [WS TOKEN 재발급] 예외: {e}")
            self._last_token_refresh_at = now_ts
            return False

        self._last_token_refresh_at = now_ts
        if not new_token:
            log_error("❌ [WS TOKEN 재발급] 실패")
            return False

        origin_token = (
            self._pending_token_handoff[0]
            if self._pending_token_handoff
            else previous_token
        )
        self._pending_token_handoff = (origin_token, new_token)
        self.token = new_token
        print("✅ [WS TOKEN 재발급] 성공. 새 토큰으로 재접속합니다.")
        return True

    def _commit_ws_token_handoff(self):
        pending = self._pending_token_handoff
        if not pending:
            return False
        from src.utils import kiwoom_utils

        registered = kiwoom_utils.register_kiwoom_token_replacement(
            pending[0],
            pending[1],
            source="websocket_login_ack_success",
        )
        self._pending_token_handoff = None
        return registered

    async def _await_login_ack(self, ws, timeout_sec=5.0):
        deadline = time.time() + max(1.0, float(timeout_sec or 0.0))
        while not self._stop_event.is_set() and time.time() < deadline:
            remaining = max(0.1, deadline - time.time())
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=remaining)
                packet_received_at = datetime.now(KST)
            except asyncio.TimeoutError:
                break

            try:
                msg_dict = json.loads(message)
            except Exception:
                continue
            if not isinstance(msg_dict, dict):
                log_error(
                    f"🚨 [WS] 로그인 대기 중 비정상 메시지 무시: {str(message)[:150]}"
                )
                continue

            trnm = str(msg_dict.get("trnm", "") or "").strip().upper()
            if trnm == "PING":
                await ws.send(self._ping_echo_payload(message, msg_dict))
                continue

            if self._is_login_success_message(msg_dict):
                print("✅ [WS] 로그인 응답 확인 완료")
                return

            if self._is_login_failure_message(msg_dict):
                code = msg_dict.get("return_code", msg_dict.get("rt_cd", "?"))
                message = msg_dict.get(
                    "return_msg", msg_dict.get("msg1", "로그인 실패")
                )
                raise _LoginAckFailure(code, message)

            await self._handle_message(
                json.dumps(msg_dict), received_at=packet_received_at
            )

        raise TimeoutError("LOGIN ACK timeout")

    async def _send_post_login_bootstrap(self):
        if not self.websocket:
            return

        if is_ws_condition_search_enabled():
            print("🔍 [WS] HTS 조건검색식 목록(CNSRLST)을 요청합니다.")
            await self.websocket.send(json.dumps({"trnm": "CNSRLST"}))
        else:
            self.condition_dict.clear()
            print(
                "[WS_CONDITION_SEARCH_DISABLED] HTS 조건검색식 목록 요청 생략 "
                f"env={WS_CONDITION_SEARCH_ENABLED_ENV}"
            )

        if self.is_reconnected:
            self._begin_micro_reversion_transport_epoch()
            print(
                "🔄 [WS] 웹소켓 재접속 감지! EventBus에 상태 동기화 이벤트를 발행합니다."
            )
            self._enqueue_state_event("WS_RECONNECTED", {})

        self.is_reconnected = True

        exec_reg_packet = {
            "trnm": "REG",
            "grp_no": "2",
            "refresh": "1",
            "data": [{"item": [""], "type": ["00"]}],
        }
        await self.websocket.send(json.dumps(exec_reg_packet))
        print("📝 [WS] 🚨 계좌 주문/체결통보(00) 감시망 등록 완료!")

        session_reg_packet = {
            "trnm": "REG",
            "grp_no": "3",
            "refresh": "1",
            "data": [{"item": [""], "type": ["0s"]}],
        }
        await self.websocket.send(json.dumps(session_reg_packet))
        print("📝 [WS] 장운영구분(0s) 감시망 등록 완료!")

        # LOGIN acknowledgement plus the two session-critical registrations are
        # the readiness boundary. Reconnect restoration below intentionally uses
        # _send_reg(), whose normal safety gate waits for this event. Publish
        # readiness before restoring the prior symbol inventory.
        self._session_ready.set()

        if self.subscribed_codes:
            with self.lock:
                observation_only_codes = set(
                    self._micro_reversion_observation_only_codes
                )
                observation_items = [
                    self._micro_reversion_observation_items_by_code[code]
                    for code in sorted(observation_only_codes)
                    if code in self._micro_reversion_observation_items_by_code
                ]
                trading_codes = sorted(
                    set(self.subscribed_codes).difference(observation_only_codes)
                )
            if trading_codes:
                await self._send_reg(trading_codes)
            if observation_items:
                await self._send_reg(
                    observation_items,
                    replace_existing=not bool(trading_codes),
                    realtime_types=("0B", "0D"),
                    source="micro_reversion_collection_feedback_reconnect",
                )

    def _cancel_pending_futures(self):
        with self._pending_future_lock:
            futures = list(self._pending_loop_futures)
            self._pending_loop_futures.clear()
        for future in futures:
            try:
                future.cancel()
            except Exception:
                pass

    def _cancel_pending_loop_tasks(self):
        if not self.loop:
            return
        try:
            pending = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
        except Exception:
            pending = []
        if not pending:
            return
        for task in pending:
            task.cancel()
        try:
            self.loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )
        except Exception:
            pass

    async def _run_ws(self):
        while not self._stop_event.is_set():
            try:
                print(f"🔌 [WS] 키움 서버({self.uri})에 연결을 시도합니다...")
                async with websockets.connect(self.uri, ping_interval=None) as ws:
                    self.websocket = ws
                    self._session_ready.clear()
                    print("✅ [WS] 웹소켓 연결 성공!")

                    login_packet = {"trnm": "LOGIN", "token": self.token}
                    await ws.send(json.dumps(login_packet))
                    print("🔑 [WS] 로그인 패킷 전송 완료")
                    await self._await_login_ack(ws)
                    self._commit_ws_token_handoff()
                    await self._send_post_login_bootstrap()

                    while True:
                        message = await ws.recv()
                        packet_received_at = datetime.now(KST)
                        await self._handle_message(
                            message, received_at=packet_received_at
                        )

            except websockets.ConnectionClosed as e:
                if self._stop_event.is_set():
                    break
                print(
                    "⚠️ [WS] 연결 끊김! "
                    f"(code={getattr(e, 'code', '?')}, reason={getattr(e, 'reason', '') or '-'}) "
                    "3초 후 재접속 시도..."
                )
                self.websocket = None
                self._session_ready.clear()
                await asyncio.sleep(3)
            except _LoginAckFailure as e:
                if self._stop_event.is_set():
                    break

                self.websocket = None
                self._session_ready.clear()

                if self._is_auth_token_failure(e.code, e.message):
                    print(
                        f"⚠️ [WS] 로그인 인증 실패 감지(code={e.code}). 토큰 재발급을 시도합니다."
                    )
                    refreshed = self._refresh_ws_token()
                    await asyncio.sleep(1 if refreshed else 3)
                else:
                    log_error(f"🚨 [WS] 로그인 실패: {e}")
                    print(f"🚨 [WS] 로그인 실패: {e}")
                    await asyncio.sleep(3)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                log_error(f"🚨 [WS] 예상치 못한 오류: {e}")
                print(f"🚨 [WS] 예상치 못한 오류: {e}")
                self.websocket = None
                self._session_ready.clear()
                await asyncio.sleep(3)
        self.websocket = None
        self._session_ready.clear()

    async def _handle_message(self, message, *, received_at=None):
        try:
            received_at_has_utc_offset = bool(
                isinstance(received_at, datetime)
                and received_at.tzinfo is not None
                and received_at.utcoffset() is not None
            )
        except (TypeError, ValueError, OverflowError):
            received_at_has_utc_offset = False
        if received_at_has_utc_offset:
            packet_received_at = received_at.astimezone(KST)
            packet_receive_time_source = _ORDER_EXECUTION_RECEIVE_TIME_SOURCE
        else:
            # Direct/internal dispatch has no trustworthy packet-ingress
            # watermark.  Keep a diagnostic timestamp, but never label it as
            # promotion-grade websocket ingress.  The lifecycle consumer
            # fails closed on this source tag.
            packet_received_at = datetime.now(KST)
            packet_receive_time_source = _ORDER_EXECUTION_UNTRUSTED_RECEIVE_TIME_SOURCE
        try:
            msg_dict = json.loads(message)
            if not isinstance(msg_dict, dict):
                log_error(f"🚨 [WS] 비정상 메시지 무시: {str(message)[:150]}")
                return
            trnm = msg_dict.get("trnm")

            # =========================================================
            # 🏓 [핵심] 생존 신고 (PING/PONG)
            # =========================================================
            if trnm == "PING":
                self._flush_deferred_scalp_condition_matches_if_allowed()
                if self.websocket:
                    await self.websocket.send(
                        self._ping_echo_payload(message, msg_dict)
                    )
                return

            # =========================================================
            # 🚀 [추가 2] 조건검색식 목록 응답 수신 (ka10171)
            # =========================================================
            if trnm == "CNSRLST":
                if not is_ws_condition_search_enabled():
                    self.condition_dict.clear()
                    print(
                        "[WS_CONDITION_SEARCH_DISABLED] CNSRLST 응답 무시 "
                        f"env={WS_CONDITION_SEARCH_ENABLED_ENV}"
                    )
                    return
                data_list = msg_dict.get("data", [])
                parsed_rows = self._parse_condition_list_rows(data_list)
                self.condition_dict.clear()
                target_seqs = []

                target_keywords = list(SCALP_CONDITION_KEYWORDS)
                if is_swing_real_watching_enabled():
                    target_keywords.extend(SWING_CONDITION_KEYWORDS)
                # 🚨 주의: 다중 검색식을 찾을 때는 여기서 break를 쓰면 안 됩니다!

                if parsed_rows:
                    preview = ", ".join(
                        f"{name or 'NO_NAME'}({seq or '?'})"
                        for seq, name in parsed_rows[:20]
                    )
                    print(
                        f"📚 [WS] 조건검색식 목록 수신: {len(parsed_rows)}개"
                        + (f" | {preview}" if preview else "")
                    )
                else:
                    print(
                        f"⚠️ [WS] 조건검색식 목록 응답이 비었거나 파싱되지 않았습니다. payload={msg_dict}"
                    )

                for seq, name in parsed_rows:
                    if any(k in name for k in target_keywords):
                        target_seqs.append((seq, name))
                        self.condition_dict[str(seq)] = (
                            name  # 💡 [핵심] 번호와 이름을 기억해 둡니다.
                        )

                if target_seqs:
                    for target_seq, target_name in target_seqs:
                        print(
                            f"🎯 [WS] 스캘핑 조건식 발견: [{target_name}] (seq: {target_seq}). 실시간 PUSH 감시 요청."
                        )
                        req_packet = {
                            "trnm": "CNSRREQ",
                            "seq": str(target_seq),
                            "search_type": "1",
                            "stex_tp": "K",
                        }
                        if self.websocket:
                            await self.websocket.send(json.dumps(req_packet))
                            await asyncio.sleep(0.2)
                else:
                    available_names = [name for _, name in parsed_rows if name]
                    print(
                        "⚠️ [WS] 타겟 조건검색식을 찾을 수 없습니다."
                        + (
                            f" 수신 목록={available_names[:20]}"
                            if available_names
                            else " 수신 목록이 비어 있습니다."
                        )
                    )
                return

            # =========================================================
            # 🚀 [추가 3] 조건검색 최초 편입 목록 (ka10173)
            # =========================================================
            if trnm == "CNSRREQ":
                if not is_ws_condition_search_enabled():
                    print(
                        "[WS_CONDITION_SEARCH_DISABLED] CNSRREQ 편입 목록 무시 "
                        f"env={WS_CONDITION_SEARCH_ENABLED_ENV}"
                    )
                    return
                # 💡 [핵심 방어] 키움 서버가 null(None)을 주더라도 안전하게 빈 리스트([])로 바꿔치기합니다!
                c_data = msg_dict.get("data") or []
                seq = str(msg_dict.get("seq", "")).strip()
                cnd_name = self.condition_dict.get(seq) or "UNKNOWN_CONDITION"
                print(
                    f"[WS] CNSRREQ init load: {len(c_data)} items (seq={seq}, condition={cnd_name})"
                )
                for item in c_data:
                    code = item.get("jmcode", "").replace("A", "")
                    if not _condition_match_intake_allowed(cnd_name):
                        self._defer_scalp_condition_match(
                            {
                                "code": code,
                                "seq": seq,
                                "condition_name": cnd_name,
                            }
                        )
                        continue
                    self._enqueue_state_event(
                        "CONDITION_MATCHED",
                        {"code": code, "seq": seq, "condition_name": cnd_name},
                    )
                self._flush_deferred_scalp_condition_matches_if_allowed()
                return

            # =========================================================
            # 📈 [기존 트랙] 실시간 주가 / 호가 / 체결 / 조건검색 데이터 처리
            # =========================================================
            if trnm == "REAL" and "data" in msg_dict:
                for d in msg_dict["data"]:
                    values = d.get("values", {})
                    if not values:
                        continue

                    real_type = d.get("type")

                    # 🚀 실시간 조건검색 편입/이탈 통보 가로채기 (02)
                    if real_type == "02" or d.get("name") == "조건검색":
                        if not is_ws_condition_search_enabled():
                            continue
                        seq = str(values.get("841", "")).strip()  # 💡 일련번호 추출
                        code = str(values.get("9001", "")).replace("A", "").strip()
                        insert_type = str(values.get("843", "")).strip()

                        # 기억해둔 번호로 검색식 이름을 알아냅니다.
                        cnd_name = self.condition_dict.get(seq) or "UNKNOWN_CONDITION"

                        if insert_type == "I":
                            if not _condition_match_intake_allowed(cnd_name):
                                self._defer_scalp_condition_match(
                                    {
                                        "code": code,
                                        "type": "REALTIME",
                                        "condition_name": cnd_name,
                                    }
                                )
                                continue
                            # 💡 스나이퍼에게 출처(이름표)를 함께 보냅니다!
                            self._enqueue_state_event(
                                "CONDITION_MATCHED",
                                {
                                    "code": code,
                                    "type": "REALTIME",
                                    "condition_name": cnd_name,
                                },
                            )
                        elif insert_type == "D":
                            self._drop_deferred_scalp_condition_match(code, cnd_name)
                            self._enqueue_state_event(
                                "CONDITION_UNMATCHED",
                                {
                                    "code": code,
                                    "type": "REALTIME",
                                    "condition_name": cnd_name,
                                },
                            )
                        continue

                    # ===================================================
                    # [트랙 A] 🚨 주문/체결 통보 가로채기 (ORDER_EXECUTED)
                    # ===================================================
                    if real_type == "00" or d.get("name") == "주문체결":
                        notice = self._parse_order_execution_notice(
                            values,
                            source_type=real_type,
                        )
                        status = notice["status"]
                        code = notice["code"]
                        order_no = notice["order_no"]
                        order_type_str = notice["order_type_str"]
                        broker_reject_reason_raw = notice["broker_reject_reason_raw"]

                        print(
                            f"📩 [WS 주문상태] {code} | 주문번호: '{order_no}' | "
                            f"상태: '{status}' | 구분: '{order_type_str}' | "
                            f"거부사유: '"
                            f"{broker_reject_reason_raw if status == '거부' else '-'}'"
                        )
                        if not notice["exec_type"]:
                            log_error(
                                "[WS_ORDER_RECEIPT_SOURCE_GAP] "
                                f"code={code or '-'} order_no={order_no or '-'} "
                                f"reason={notice['source_gap_reason']} "
                                f"fid905={order_type_str or '-'}"
                            )
                            self._enqueue_state_event(
                                "ORDER_EXECUTION_SOURCE_GAP",
                                {
                                    "code": code,
                                    "order_no": order_no,
                                    "reason": notice["source_gap_reason"],
                                    "order_type_str": order_type_str,
                                    "broker_snapshot_refresh_required": True,
                                    "runtime_effect": False,
                                },
                            )
                            continue
                        self._enqueue_state_event(
                            "ORDER_NOTICE",
                            {
                                "code": code,
                                "order_no": order_no,
                                "type": notice["exec_type"],
                                "status": status,
                                "order_type_str": order_type_str,
                                "broker_reject_reason_raw": (broker_reject_reason_raw),
                                "broker_execution_raw_fields": notice[
                                    "broker_execution_raw_fields"
                                ],
                                "broker_execution_time_raw": notice[
                                    "broker_execution_time_raw"
                                ],
                                "actual_exchange_code": notice["actual_exchange_code"],
                                "actual_exchange_name": notice["actual_exchange_name"],
                                "actual_execution_venue": notice[
                                    "actual_execution_venue"
                                ],
                                "sor_flag": notice["sor_flag"],
                                "time": datetime.now().strftime("%H:%M:%S"),
                            },
                        )

                        if status == "체결":
                            exec_price = notice["exec_price"]
                            exec_qty = notice["exec_qty"]
                            exec_type = notice["exec_type"]

                            print(
                                f"🔔 [WS 실제체결] {code} {exec_type} {exec_qty}주 @ {exec_price}원 (주문번호: {order_no})"
                            )

                            malformed_fids = set(
                                notice.get("numeric_contract_errors") or []
                            )
                            if malformed_fids:
                                log_error(
                                    "[WS_ORDER_RECEIPT_NUMERIC_SOURCE_GAP] "
                                    f"code={code} order_no={order_no or '-'} "
                                    f"fids={','.join(sorted(malformed_fids))}"
                                )
                                self._enqueue_state_event(
                                    "ORDER_EXECUTION_SOURCE_GAP",
                                    {
                                        "code": code,
                                        "order_no": order_no,
                                        "reason": "official_integer_fid_malformed",
                                        "malformed_fids": sorted(malformed_fids),
                                        "broker_snapshot_refresh_required": True,
                                        "runtime_effect": False,
                                    },
                                )

                            # FID 910 is not custody authority.  When it is
                            # blank/malformed but 903 supplies exact cumulative
                            # notional, the receipt consumer can reconstruct the
                            # leg price while marking unit/source provenance as
                            # incomplete.  FID 911 remains mandatory for any
                            # custody mutation.
                            if exec_qty > 0 and exec_type in {"BUY", "SELL"}:
                                self._enqueue_state_event(
                                    "ORDER_EXECUTED",
                                    {
                                        "code": code,
                                        "order_no": order_no,
                                        "type": exec_type,
                                        "price": exec_price,
                                        "qty": exec_qty,
                                        "order_qty": notice["order_qty"],
                                        "remaining_qty": notice["remaining_qty"],
                                        "cumulative_exec_amount": notice[
                                            "cumulative_exec_amount"
                                        ],
                                        "execution_no": notice["execution_no"],
                                        "unit_exec_price": notice["unit_exec_price"],
                                        "unit_exec_qty": notice["unit_exec_qty"],
                                        "broker_execution_time_raw": notice[
                                            "broker_execution_time_raw"
                                        ],
                                        "broker_execution_received_at": (
                                            packet_received_at.isoformat(
                                                timespec="microseconds"
                                            )
                                        ),
                                        "broker_execution_receive_time_source": (
                                            packet_receive_time_source
                                        ),
                                        "actual_exchange_code": notice[
                                            "actual_exchange_code"
                                        ],
                                        "actual_exchange_name": notice[
                                            "actual_exchange_name"
                                        ],
                                        "actual_execution_venue": notice[
                                            "actual_execution_venue"
                                        ],
                                        "sor_flag": notice["sor_flag"],
                                        **notice["broker_execution_raw_fields"],
                                        "execution_economics_reconstructable": bool(
                                            exec_price > 0
                                            or (
                                                notice["cumulative_exec_amount"]
                                                is not None
                                                and notice["cumulative_exec_amount"] > 0
                                            )
                                        ),
                                        "time": datetime.now().strftime("%H:%M:%S"),
                                    },
                                )
                        continue

                    if real_type == "0s" or d.get("name") == "장시작시간":
                        self.market_session_state = str(
                            values.get("215", "") or ""
                        ).strip()
                        self.market_session_remaining = str(
                            values.get("214", "") or ""
                        ).strip()
                        event_key = (
                            self.market_session_state,
                            self.market_session_remaining,
                            str(real_type or ""),
                        )
                        if event_key != self._last_market_session_event_key:
                            self._last_market_session_event_key = event_key
                            try:
                                append_market_session_event(
                                    target_date=datetime.now().strftime("%Y-%m-%d"),
                                    event={
                                        "source": "kiwoom_websocket_0s",
                                        "real_type": real_type,
                                        "name": d.get("name"),
                                        "market_session_state": self.market_session_state,
                                        "market_session_remaining": self.market_session_remaining,
                                        "raw_values": dict(values),
                                    },
                                )
                            except Exception as exc:
                                log_error(
                                    f"🚨 [WS] 장운영구분 source-quality artifact 기록 실패: {exc}"
                                )
                        continue

                    # ===================================================
                    # [트랙 B] 실시간 주가/호가 데이터 처리
                    # ===================================================
                    raw_item_code = d.get("item", "")
                    item_code = self._normalize_code(raw_item_code)
                    if item_code and real_type != "00":
                        if item_code not in self.subscribed_codes:
                            continue
                        tick_event_snapshot = None
                        with self.lock:
                            # 1. 초기 데이터 구조 생성
                            target = self._ensure_target_defaults(item_code)

                            # 💡 안전한 파싱 헬퍼 (ValueError 방어막)
                            def safe_int(val, default=0):
                                val_str = (
                                    str(val).replace("+", "").replace("-", "").strip()
                                )
                                return int(val_str) if val_str.isdigit() else default

                            # 데이터 추출 및 할당
                            if "10" in values:
                                target["curr"] = safe_int(values["10"], target["curr"])
                            if "16" in values:
                                target["open"] = safe_int(
                                    values["16"], target.get("open", 0)
                                )
                            if "17" in values:
                                target["high"] = safe_int(
                                    values["17"], target.get("high", 0)
                                )
                            if "18" in values:
                                target["low"] = safe_int(
                                    values["18"], target.get("low", 0)
                                )
                            if "13" in values:
                                target["volume"] = safe_int(
                                    values["13"], target.get("volume", 0)
                                )

                            if "12" in values:
                                try:
                                    target["fluctuation"] = float(
                                        values["12"].replace("+", "")
                                    )
                                except ValueError:
                                    pass

                            if "228" in values:
                                try:
                                    target["v_pw"] = float(values["228"])
                                except ValueError:
                                    pass
                            if "14" in values:
                                target["cum_trade_value"] = safe_int(
                                    values["14"], target.get("cum_trade_value", 0)
                                )
                            if "1313" in values:
                                target["tick_trade_value"] = safe_int(
                                    values["1313"], target.get("tick_trade_value", 0)
                                )
                            if "1030" in values:
                                target["sell_exec_volume"] = safe_int(
                                    values["1030"], target.get("sell_exec_volume", 0)
                                )
                            if "1031" in values:
                                target["buy_exec_volume"] = safe_int(
                                    values["1031"], target.get("buy_exec_volume", 0)
                                )
                            if "1032" in values:
                                target["buy_ratio"] = self._safe_float(
                                    values["1032"], target.get("buy_ratio", 0.0)
                                )
                            if "1314" in values:
                                target["net_buy_exec_volume"] = self._safe_signed_int(
                                    values["1314"], target.get("net_buy_exec_volume", 0)
                                )
                            if "1315" in values:
                                target["sell_exec_single"] = safe_int(
                                    values["1315"], target.get("sell_exec_single", 0)
                                )
                            if "1316" in values:
                                target["buy_exec_single"] = safe_int(
                                    values["1316"], target.get("buy_exec_single", 0)
                                )

                            if "121" in values:
                                target["ask_tot"] = safe_int(values["121"])
                            if "125" in values:
                                target["bid_tot"] = safe_int(values["125"])
                            if "128" in values:
                                target["net_bid_depth"] = self._safe_signed_int(
                                    values["128"], target.get("net_bid_depth", 0)
                                )
                            if "129" in values:
                                target["bid_depth_ratio"] = self._safe_float(
                                    values["129"], target.get("bid_depth_ratio", 0.0)
                                )
                            if "138" in values:
                                target["net_ask_depth"] = self._safe_signed_int(
                                    values["138"], target.get("net_ask_depth", 0)
                                )
                            if "139" in values:
                                target["ask_depth_ratio"] = self._safe_float(
                                    values["139"], target.get("ask_depth_ratio", 0.0)
                                )
                            target["market_session_state"] = self.market_session_state
                            target["market_session_remaining"] = (
                                self.market_session_remaining
                            )

                            # '0B' 체결 데이터는 필드가 문서/계정에 따라 달라질 수 있어
                            if real_type == "0B":
                                signed_qty = self._safe_signed_int(values.get("15"), 0)
                                current_price = target.get("curr", 0)
                                trade_price = safe_int(values.get("10"), current_price)
                                current_vpw = target.get("v_pw", 0.0)
                                current_tick_suffix = self._ws_item_market_suffix(
                                    raw_item_code
                                )
                                current_tick_route = self._ws_item_route(raw_item_code)
                                previous_tick = (
                                    target["recent_trade_ticks"][0]
                                    if isinstance(
                                        target.get("recent_trade_ticks"), deque
                                    )
                                    and len(target.get("recent_trade_ticks")) > 0
                                    else None
                                )
                                if previous_tick and (
                                    str(previous_tick.get("market_suffix") or "")
                                    != current_tick_suffix
                                    or str(previous_tick.get("market_route") or "")
                                    != current_tick_route
                                ):
                                    previous_tick = None
                                aux_fields = self._parse_0b_auxiliary_fields(
                                    values,
                                    trade_price=trade_price,
                                    previous_tick=previous_tick,
                                )
                                tick_value = aux_fields["trade_value"]
                                buy_qty = aux_fields["buy_qty"]
                                sell_qty = aux_fields["sell_qty"]
                                trade_volume = aux_fields["trade_volume"]
                                buy_ratio = self._safe_float(values.get("1032"), 0.0)
                                target["tick_trade_value"] = tick_value
                                target["tick_trade_value_source"] = aux_fields[
                                    "trade_value_source"
                                ]
                                target["tick_trade_value_fallback_volume_source"] = (
                                    aux_fields["trade_value_fallback_volume_source"]
                                )
                                target["trade_volume_source"] = aux_fields[
                                    "trade_volume_source"
                                ]
                                target["trade_volume_1030_1031_vs_15_mismatch"] = (
                                    aux_fields["split_qty_vs_15_mismatch"]
                                )
                                target["trade_volume_1030_1031_vs_15_delta"] = (
                                    aux_fields["split_qty_vs_15_delta"]
                                )
                                target["kiwoom_0b_aux_observed_count"] = (
                                    int(target.get("kiwoom_0b_aux_observed_count") or 0)
                                    + 1
                                )
                                if aux_fields["trade_value_source"] == "1313":
                                    target["kiwoom_0b_1313_present_count"] = (
                                        int(
                                            target.get("kiwoom_0b_1313_present_count")
                                            or 0
                                        )
                                        + 1
                                    )
                                else:
                                    target["kiwoom_0b_1313_missing_count"] = (
                                        int(
                                            target.get("kiwoom_0b_1313_missing_count")
                                            or 0
                                        )
                                        + 1
                                    )
                                target["kiwoom_0b_trade_value_source_counts"] = (
                                    self._increment_counter_dict(
                                        target.get(
                                            "kiwoom_0b_trade_value_source_counts"
                                        ),
                                        aux_fields["trade_value_source"],
                                    )
                                )
                                target["kiwoom_0b_trade_volume_source_counts"] = (
                                    self._increment_counter_dict(
                                        target.get(
                                            "kiwoom_0b_trade_volume_source_counts"
                                        ),
                                        aux_fields["trade_volume_source"],
                                    )
                                )
                                if aux_fields["split_qty_vs_15_evaluable"]:
                                    target[
                                        "kiwoom_0b_1030_1031_vs_15_evaluable_count"
                                    ] = (
                                        int(
                                            target.get(
                                                "kiwoom_0b_1030_1031_vs_15_evaluable_count"
                                            )
                                            or 0
                                        )
                                        + 1
                                    )
                                    if aux_fields["split_qty_vs_15_mismatch"]:
                                        target[
                                            "kiwoom_0b_1030_1031_vs_15_mismatch_count"
                                        ] = (
                                            int(
                                                target.get(
                                                    "kiwoom_0b_1030_1031_vs_15_mismatch_count"
                                                )
                                                or 0
                                            )
                                            + 1
                                        )
                                inline_best_ask = safe_int(values.get("27"), 0)
                                inline_best_bid = safe_int(values.get("28"), 0)
                                tick_time = str(
                                    values.get("20")
                                    or datetime.now().strftime("%H%M%S")
                                )
                                received_ts = time.time()
                                quote_resolution = self._resolve_0b_touch_quote(
                                    item_code,
                                    inline_best_ask=inline_best_ask,
                                    inline_best_bid=inline_best_bid,
                                    tick_time=tick_time,
                                    received_ts=received_ts,
                                )
                                best_ask = quote_resolution["best_ask"]
                                best_bid = quote_resolution["best_bid"]
                                quote_complete = (
                                    best_ask > 0
                                    and best_bid > 0
                                    and quote_resolution["quote_source"]
                                    in {
                                        "0B_inline_best_quote",
                                        "cached_top_of_book_ttl",
                                    }
                                )
                                if quote_complete:
                                    touch_side, touch_quality = (
                                        self._infer_trade_aggressor_from_touch(
                                            trade_price,
                                            best_ask,
                                            best_bid,
                                        )
                                    )
                                else:
                                    touch_side = "UNKNOWN"
                                    touch_quality = "missing_best_quote"
                                aux_context = self._infer_trade_auxiliary_score(
                                    values,
                                    previous_tick=previous_tick,
                                )
                                signed_side, signed_quality = (
                                    self._infer_signed_trade_volume_auxiliary(
                                        values.get("15")
                                    )
                                )
                                touch_source = (
                                    "orderbook_touch"
                                    if quote_resolution["quote_source"]
                                    == "0B_inline_best_quote"
                                    else (
                                        "cached_orderbook_touch"
                                        if quote_resolution["cache_used"]
                                        else "missing_best_quote"
                                    )
                                )
                                touch_quality_value = (
                                    touch_quality
                                    if quote_resolution["quote_source"]
                                    == "0B_inline_best_quote"
                                    else (
                                        f"cached_quote_{touch_quality}"
                                        if quote_resolution["cache_used"]
                                        else touch_quality
                                    )
                                )
                                if signed_side in {"BUY", "SELL"}:
                                    aggressor_side = signed_side
                                    aggressor_source = "kiwoom_0b_signed_trade_volume"
                                    aggressor_quality = (
                                        self._primary_signed_trade_volume_quality(
                                            signed_quality
                                        )
                                    )
                                else:
                                    aggressor_side = touch_side
                                    aggressor_source = touch_source
                                    aggressor_quality = touch_quality_value
                                touch_confirms_signed = None
                                if signed_side in {"BUY", "SELL"} and touch_side in {
                                    "BUY",
                                    "SELL",
                                }:
                                    touch_confirms_signed = signed_side == touch_side
                                trusted_buy_volume = (
                                    trade_volume if aggressor_side == "BUY" else 0
                                )
                                trusted_sell_volume = (
                                    trade_volume if aggressor_side == "SELL" else 0
                                )
                                normalized_tick = {
                                    "time": tick_time,
                                    "exchange_time_raw": str(values.get("20") or ""),
                                    "exchange_code_9081": str(values.get("9081") or ""),
                                    "price": trade_price,
                                    "volume": int(trade_volume or 0),
                                    "market_suffix": current_tick_suffix,
                                    "market_route": current_tick_route,
                                    "volume_source": aux_fields["trade_volume_source"],
                                    "dir": aggressor_side,
                                    "aggressor_side": aggressor_side,
                                    "aggressor_source": aggressor_source,
                                    "aggressor_quality": aggressor_quality,
                                    "aggressor_quote_source": quote_resolution[
                                        "quote_source"
                                    ],
                                    "aggressor_tick_sync": quote_resolution[
                                        "tick_sync"
                                    ],
                                    "aggressor_cache_used": quote_resolution[
                                        "cache_used"
                                    ],
                                    "aggressor_quote_age_ms": quote_resolution[
                                        "quote_age_ms"
                                    ],
                                    "aggressor_tob_miss_count": quote_resolution[
                                        "tob_miss_count"
                                    ],
                                    "aggressor_backoff_active": quote_resolution[
                                        "backoff_active"
                                    ],
                                    "aggressor_touch_side": touch_side,
                                    "aggressor_touch_source": touch_source,
                                    "aggressor_touch_quality": touch_quality_value,
                                    "aggressor_touch_confirms_signed": touch_confirms_signed,
                                    "aggressor_aux_side": aux_context["side"],
                                    "aggressor_aux_source": (
                                        "weighted_auxiliary_observation"
                                        if aux_context["reason"]
                                        != "insufficient_auxiliary_data"
                                        else "none"
                                    ),
                                    "aggressor_aux_quality": aux_context["quality"],
                                    "aggressor_aux_score": aux_context["score"],
                                    "aggressor_aux_reason": aux_context["reason"],
                                    "aggressor_aux_components": aux_context[
                                        "components"
                                    ],
                                    "aggressor_aux_pressure_usable": False,
                                    "aggressor_aux_raw_15": str(values.get("15") or ""),
                                    "signed_trade_volume": str(values.get("15") or ""),
                                    "buyer_vol": trusted_buy_volume,
                                    "seller_vol": trusted_sell_volume,
                                    "buy_exec_cum_1031": buy_qty,
                                    "sell_exec_cum_1030": sell_qty,
                                    "buy_ratio_1032": str(values.get("1032") or ""),
                                    "tick_trade_value": tick_value,
                                    "tick_trade_value_source": aux_fields[
                                        "trade_value_source"
                                    ],
                                    "tick_trade_value_fallback_volume_source": aux_fields[
                                        "trade_value_fallback_volume_source"
                                    ],
                                    "trade_volume_1030_1031_sum": aux_fields[
                                        "split_qty_sum"
                                    ],
                                    "trade_volume_1030_1031_available": aux_fields[
                                        "split_qty_available"
                                    ],
                                    "trade_volume_1030_1031_advisory_only": aux_fields[
                                        "split_qty_advisory_only"
                                    ],
                                    "trade_volume_1030_1031_vs_15_mismatch": aux_fields[
                                        "split_qty_vs_15_mismatch"
                                    ],
                                    "trade_volume_1030_1031_vs_15_delta": aux_fields[
                                        "split_qty_vs_15_delta"
                                    ],
                                    "best_ask": best_ask,
                                    "best_bid": best_bid,
                                    "cum_volume": safe_int(values.get("13"), 0),
                                    "prev_cum_volume": aux_fields["prev_cum_volume"],
                                    "cum_volume_delta": aux_fields["cum_volume_delta"],
                                    "quote_age_ms": quote_resolution["quote_age_ms"],
                                    "strength": current_vpw,
                                    "received_at_ms": int(received_ts * 1000),
                                }
                                target["last_trade_tick"] = {
                                    "ts": received_ts,
                                    "values": values,
                                    **normalized_tick,
                                }
                                if isinstance(target.get("recent_trade_ticks"), deque):
                                    target["recent_trade_ticks"].appendleft(
                                        normalized_tick
                                    )
                                route_tick_buffers = target.setdefault(
                                    "recent_trade_ticks_by_route", {}
                                )
                                if isinstance(route_tick_buffers, dict):
                                    route_key = (
                                        f"{normalized_tick['market_suffix'] or 'KRX'}"
                                        f"|{normalized_tick['market_route'] or 'unknown'}"
                                    )
                                    route_buffer = route_tick_buffers.get(route_key)
                                    if not isinstance(route_buffer, deque):
                                        route_buffer = deque(maxlen=120)
                                        route_tick_buffers[route_key] = route_buffer
                                    route_buffer.appendleft(normalized_tick)
                                ORDERBOOK_STABILITY_OBSERVER.record_trade(
                                    item_code,
                                    price=trade_price,
                                    ts=target["last_trade_tick"]["ts"],
                                )
                                self._append_strength_momentum(
                                    target,
                                    current_price=current_price,
                                    current_vpw=current_vpw,
                                    signed_qty=signed_qty,
                                    tick_value=tick_value,
                                    tick_value_source=aux_fields["trade_value_source"],
                                    buy_ratio=buy_ratio,
                                    buy_qty=buy_qty,
                                    sell_qty=sell_qty,
                                    aggressor_side=aggressor_side,
                                )

                            # '0D' 주식호가잔량 데이터 파싱 (1~5호가)
                            if real_type == "0D":
                                if self._micro_reversion_depth_capture_requested():
                                    target["last_depth_tick"] = (
                                        self._build_micro_reversion_depth_tick(
                                            raw_item_code, values
                                        )
                                    )
                                else:
                                    target.pop("last_depth_tick", None)
                                asks, bids = [], []
                                for i in range(1, 6):
                                    ask_p = values.get(str(40 + i))
                                    ask_v = values.get(str(60 + i))
                                    bid_p = values.get(str(50 + i))
                                    bid_v = values.get(str(70 + i))

                                    if ask_p and ask_v:
                                        asks.append(
                                            {
                                                "price": safe_int(ask_p),
                                                "volume": safe_int(ask_v),
                                            }
                                        )
                                    if bid_p and bid_v:
                                        bids.append(
                                            {
                                                "price": safe_int(bid_p),
                                                "volume": safe_int(bid_v),
                                            }
                                        )

                                target["orderbook"]["asks"] = asks[::-1]
                                target["orderbook"]["bids"] = bids
                                best_ask = (
                                    target["orderbook"]["asks"][0].get("price", 0)
                                    if target["orderbook"]["asks"]
                                    else 0
                                )
                                best_bid = (
                                    target["orderbook"]["bids"][0].get("price", 0)
                                    if target["orderbook"]["bids"]
                                    else 0
                                )
                                best_ask_qty = (
                                    target["orderbook"]["asks"][0].get("volume", 0)
                                    if target["orderbook"]["asks"]
                                    else 0
                                )
                                best_bid_qty = (
                                    target["orderbook"]["bids"][0].get("volume", 0)
                                    if target["orderbook"]["bids"]
                                    else 0
                                )
                                ask_depth_l = sum(
                                    int(level.get("volume", 0) or 0)
                                    for level in target["orderbook"]["asks"]
                                )
                                bid_depth_l = sum(
                                    int(level.get("volume", 0) or 0)
                                    for level in target["orderbook"]["bids"]
                                )
                                expected_price = safe_int(
                                    values.get("291") or values.get("23")
                                )
                                expected_qty = safe_int(
                                    values.get("292") or values.get("24")
                                )
                                if expected_price > 0 or expected_qty > 0:
                                    target["expected_open"] = {
                                        "price": expected_price,
                                        "qty": expected_qty,
                                        "price_vs_prev": safe_int(
                                            values.get("294") or values.get("200")
                                        ),
                                        "price_vs_prev_rate": self._safe_float(
                                            values.get("295") or values.get("201"), 0.0
                                        ),
                                        "sign": values.get("293")
                                        or values.get("238")
                                        or "",
                                        "volume_vs_prev_rate": self._safe_float(
                                            values.get("299"), 0.0
                                        ),
                                        "source": "0D_expected_open",
                                        "valid_during_expected_session": True,
                                        "raw_field_ids": [
                                            "291",
                                            "292",
                                            "293",
                                            "294",
                                            "295",
                                            "299",
                                        ],
                                    }
                                ORDERBOOK_STABILITY_OBSERVER.record_quote(
                                    item_code,
                                    best_bid=best_bid,
                                    best_ask=best_ask,
                                    best_bid_qty=best_bid_qty,
                                    best_ask_qty=best_ask_qty,
                                    bid_depth_l=bid_depth_l,
                                    ask_depth_l=ask_depth_l,
                                )
                                self._update_tob_cache(
                                    item_code,
                                    best_ask=best_ask,
                                    best_bid=best_bid,
                                    now_ms=int(time.time() * 1000),
                                )
                                self._update_micro_estimator_from_orderbook(
                                    item_code,
                                    target,
                                    now_ts=time.time(),
                                )

                            # '0w' 프로그램 매매 데이터 파싱
                            if real_type == "0w":
                                program_observed_at = time.time()
                                program_requested_at = self._safe_float(
                                    target.get("program_subscription_requested_at"),
                                    0.0,
                                )
                                if (
                                    self._safe_float(
                                        target.get("program_first_observed_at"),
                                        0.0,
                                    )
                                    <= 0.0
                                ):
                                    target["program_first_observed_at"] = (
                                        program_observed_at
                                    )
                                    target["program_first_observed_latency_ms"] = (
                                        round(
                                            max(
                                                0.0,
                                                program_observed_at
                                                - program_requested_at,
                                            )
                                            * 1000.0,
                                            3,
                                        )
                                        if program_requested_at > 0.0
                                        else None
                                    )
                                target.pop("program_missing_reason", None)
                                if "202" in values:
                                    target["prog_sell_qty"] = self._safe_signed_int(
                                        values["202"]
                                    )
                                if "204" in values:
                                    target["prog_sell_amt"] = self._safe_signed_int(
                                        values["204"]
                                    )
                                if "206" in values:
                                    target["prog_buy_qty"] = self._safe_signed_int(
                                        values["206"]
                                    )
                                if "208" in values:
                                    target["prog_buy_amt"] = self._safe_signed_int(
                                        values["208"]
                                    )
                                if "210" in values:
                                    target["prog_net_qty"] = self._safe_signed_int(
                                        values["210"]
                                    )
                                if "211" in values:
                                    target["prog_delta_qty"] = self._safe_signed_int(
                                        values["211"]
                                    )
                                if "212" in values:
                                    target["prog_net_amt"] = self._safe_signed_int(
                                        values["212"]
                                    )
                                if "213" in values:
                                    target["prog_delta_amt"] = self._safe_signed_int(
                                        values["213"]
                                    )
                                # 프로그램 히스토리 업데이트
                                target["program_history"].append(
                                    {
                                        "ts": time.time(),
                                        "net_qty": target["prog_net_qty"],
                                        "delta_qty": target["prog_delta_qty"],
                                        "net_amt": target["prog_net_amt"],
                                        "delta_amt": target["prog_delta_amt"],
                                    }
                                )
                                target["last_prog_update_ts"] = program_observed_at

                            # '0F' 주식당일거래원: 외국계 거래원 추정 수급
                            if real_type == "0F":
                                if "261" in values:
                                    target["foreign_broker_sell_est_qty"] = (
                                        self._safe_signed_int(values["261"])
                                    )
                                if "262" in values:
                                    target["foreign_broker_sell_est_delta_qty"] = (
                                        self._safe_signed_int(values["262"])
                                    )
                                if "263" in values:
                                    target["foreign_broker_buy_est_qty"] = (
                                        self._safe_signed_int(values["263"])
                                    )
                                if "264" in values:
                                    target["foreign_broker_buy_est_delta_qty"] = (
                                        self._safe_signed_int(values["264"])
                                    )
                                if "267" in values:
                                    target["foreign_broker_net_est_qty"] = (
                                        self._safe_signed_int(values["267"])
                                    )
                                if "268" in values:
                                    target["foreign_broker_net_est_delta_qty"] = (
                                        self._safe_signed_int(values["268"])
                                    )
                                target["last_foreign_broker_update_ts"] = time.time()

                            target["received_types"].add(real_type)
                            now_update_ts = time.time()
                            target["last_ws_update_ts"] = now_update_ts
                            market_suffix = self._ws_item_market_suffix(raw_item_code)
                            market_route = self._ws_item_route(raw_item_code)
                            target["last_ws_item"] = str(raw_item_code or "")
                            target["last_ws_market_suffix"] = market_suffix
                            target["last_ws_market_route"] = market_route
                            type_ts = target.setdefault("last_realtime_type_ts", {})
                            if isinstance(type_ts, dict):
                                type_ts[real_type] = now_update_ts
                            type_items = target.setdefault(
                                "last_realtime_type_item", {}
                            )
                            if isinstance(type_items, dict):
                                type_items[real_type] = str(raw_item_code or "")
                            type_suffixes = target.setdefault(
                                "last_realtime_type_market_suffix", {}
                            )
                            if isinstance(type_suffixes, dict):
                                type_suffixes[real_type] = market_suffix
                            type_routes = target.setdefault(
                                "last_realtime_type_market_route", {}
                            )
                            if isinstance(type_routes, dict):
                                type_routes[real_type] = market_route
                            type_venues = target.setdefault(
                                "last_realtime_type_effective_venue", {}
                            )
                            if isinstance(type_venues, dict):
                                type_venues[real_type] = self._ws_item_effective_venue(
                                    raw_item_code
                                )
                            route_snapshots = target.setdefault(
                                "realtime_type_snapshots_by_route", {}
                            )
                            if isinstance(route_snapshots, dict):
                                route_key = (
                                    f"{market_suffix or 'KRX'}"
                                    f"|{market_route or 'unknown'}"
                                )
                                route_snapshot = route_snapshots.setdefault(
                                    route_key, {}
                                )
                                if isinstance(route_snapshot, dict):
                                    realtime_snapshot = {
                                        "realtime_type": real_type,
                                        "observed_epoch": now_update_ts,
                                        "item": str(raw_item_code or ""),
                                        "market_suffix": market_suffix,
                                        "market_route": market_route,
                                        "effective_venue": (
                                            self._ws_item_effective_venue(raw_item_code)
                                        ),
                                    }
                                    if real_type == "0B":
                                        realtime_snapshot["current_price"] = safe_int(
                                            target.get("curr")
                                        )
                                    elif real_type == "0D":
                                        current_orderbook = target.get("orderbook")
                                        current_orderbook = (
                                            current_orderbook
                                            if isinstance(current_orderbook, dict)
                                            else {}
                                        )
                                        current_asks = current_orderbook.get("asks")
                                        current_bids = current_orderbook.get("bids")
                                        current_asks = (
                                            current_asks
                                            if isinstance(current_asks, list)
                                            else []
                                        )
                                        current_bids = (
                                            current_bids
                                            if isinstance(current_bids, list)
                                            else []
                                        )
                                        realtime_snapshot["orderbook"] = {
                                            "asks": copy.deepcopy(current_asks[:1]),
                                            "bids": copy.deepcopy(current_bids[:1]),
                                        }
                                        current_depth_tick = target.get(
                                            "last_depth_tick"
                                        )
                                        if isinstance(current_depth_tick, dict) and str(
                                            current_depth_tick.get("item") or ""
                                        ) == str(raw_item_code or ""):
                                            route_depth_totals = current_depth_tick.get(
                                                "route_depth_totals"
                                            )
                                            if isinstance(route_depth_totals, dict):
                                                realtime_snapshot[
                                                    "route_depth_totals"
                                                ] = copy.deepcopy(route_depth_totals)
                                            realtime_snapshot["orderbook_time_raw"] = (
                                                str(
                                                    current_depth_tick.get(
                                                        "orderbook_time_raw"
                                                    )
                                                    or ""
                                                )
                                            )
                                    route_snapshot[real_type] = realtime_snapshot
                            target["time"] = datetime.now().strftime("%H:%M:%S")

                            if not target.get(
                                "_first_tick_logged"
                            ) and self._is_ws_ready(target, require_trade=False):
                                received = sorted(
                                    list(target.get("received_types") or [])
                                )
                                print(
                                    f"✅ [WS] 첫 실시간 데이터 수신 확인: {item_code} / types={received}"
                                )
                                target["_first_tick_logged"] = True
                            self._persistent_repair_no_tick_attempts.pop(
                                item_code, None
                            )
                            self._persistent_repair_stuck_until_ts.pop(item_code, None)
                            self._maybe_write_dashboard_snapshot()

                            tick_event_snapshot = self._snapshot_target(target)
                        # Snapshot is completed under the market-data lock; observer
                        # normalization and enqueue stay outside that critical section.
                        self._queue_tick_event(
                            item_code,
                            tick_event_snapshot,
                            realtime_type=real_type,
                        )
                self._flush_deferred_scalp_condition_matches_if_allowed()

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            log_error(f"🚨 [WS] 메시지 파싱 에러 발생: {e} | Payload: {message[:150]}")

    def start(self):
        if self._started:
            return
        self._started = True
        self._stop_event.clear()
        self._start_micro_reversion_forward_collector()

        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self._run_ws())
                self._cancel_pending_loop_tasks()
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            finally:
                self.loop.close()
                self.loop = None

        self._state_dispatch_thread = threading.Thread(
            target=self._dispatch_state_events, daemon=True
        )
        self._tick_dispatch_thread = threading.Thread(
            target=self._dispatch_tick_events, daemon=True
        )
        self._ws_thread = threading.Thread(target=thread_target, daemon=True)

        self._state_dispatch_thread.start()
        self._tick_dispatch_thread.start()
        self._ws_thread.start()

    async def _send_remove(
        self,
        codes,
        *,
        items_by_code_snapshot=None,
        update_local_state=True,
        source="",
        reason="",
    ):
        try:
            normalized_codes = self._normalize_subscribe_codes(codes)
            if not normalized_codes:
                return False

            items_by_code_snapshot = (
                items_by_code_snapshot
                if isinstance(items_by_code_snapshot, dict)
                else None
            )
            if items_by_code_snapshot is None:
                with self.lock:
                    items_by_code_snapshot = {
                        code: tuple(self._registered_items_by_code.get(code) or ())
                        for code in normalized_codes
                    }
            fallback_codes = [
                code
                for code in normalized_codes
                if not items_by_code_snapshot.get(code)
            ]
            fallback_items_by_code = {}
            if fallback_codes:
                _, fallback_items = self._resolve_ws_register_items(fallback_codes)
                fallback_items_by_code = self._items_by_code(
                    fallback_codes, fallback_items
                )

            remove_items = []
            for code in normalized_codes:
                items = tuple(items_by_code_snapshot.get(code) or ())
                if not items:
                    items = tuple(fallback_items_by_code.get(code) or (code,))
                remove_items.extend(
                    str(item) for item in items if str(item or "").strip()
                )
            remove_items = list(OrderedDict.fromkeys(remove_items))
            if not remove_items:
                return False

            for _ in range(100):
                if self._stop_event.is_set():
                    return False
                if self.websocket and self._session_ready.is_set():
                    break
                await asyncio.sleep(0.1)

            if self._stop_event.is_set():
                return False

            if not (self.websocket and self._session_ready.is_set()):
                print(
                    f"⚠️ [WS] 로그인 준비가 완료되지 않아 REMOVE 전송 실패: {normalized_codes}"
                )
                return False

            batch_size = min(
                int(getattr(TRADING_RULES, "WS_REG_BATCH_SIZE", 20) or 20), 50
            )
            total_batches = (len(remove_items) + batch_size - 1) // batch_size
            for batch_index, batch_items in enumerate(
                self._chunked(remove_items, batch_size), start=1
            ):
                if self._stop_event.is_set() or not self.websocket:
                    return False
                remove_packet = {
                    "trnm": "REMOVE",
                    "grp_no": "1",
                    "data": [
                        {"item": batch_items, "type": ["0B"]},
                        {"item": batch_items, "type": ["0D"]},
                        {"item": batch_items, "type": ["0w"]},
                        {"item": batch_items, "type": ["0F"]},
                    ],
                }
                await self.websocket.send(json.dumps(remove_packet))
                now_ts = time.time()
                with self.lock:
                    for code in normalized_codes:
                        self._last_remove_request_ts[code] = now_ts
                    if update_local_state:
                        for code in normalized_codes:
                            self._recent_reg_request_ts.pop(code, None)
                            self._registered_items_by_code.pop(code, None)
                            self._required_realtime_types_by_code.pop(code, None)
                            self._persistent_repair_request_ts.pop(code, None)
                            self._persistent_repair_no_tick_attempts.pop(code, None)
                            self._persistent_repair_stuck_until_ts.pop(code, None)
                            self._persistent_repair_overflow_codes.pop(code, None)
                            self.subscribed_codes.discard(code)
                            self.realtime_data.pop(code, None)
                print(
                    "🧹 [WS] 종목 REMOVE 패킷 전송 완료: "
                    f"grp_no=1 batch={batch_index}/{total_batches} "
                    f"code_count={len(normalized_codes)} item_count={len(batch_items)} "
                    f"source={source or '-'} reason={reason or '-'} "
                    f"items={batch_items}"
                )
                await asyncio.sleep(0.05)
            return True
        except asyncio.CancelledError:
            return False
        except Exception as e:
            log_error(f"🚨 [WS] _send_remove 에러 발생: {e}")
            print(f"🚨 [WS] _send_remove 내부 치명적 에러 발생: {e}")
            return False

    async def _send_reg(
        self,
        codes,
        *,
        replace_existing=True,
        enforce_item_budget=False,
        include_alternate_route=False,
        alternate_route_codes=None,
        remove_before_reg=False,
        source="",
        repair_cycle="",
        realtime_types=None,
        replacement_codes=(),
        trading_promotion_codes=(),
    ):
        try:
            remove_before_reg = self._flag_enabled(remove_before_reg, default=False)
            requested_realtime_types = self._normalize_required_realtime_types(
                realtime_types
            ) or ("0B", "0D", "0w", "0F")
            replacement_code_set = set(
                self._normalize_subscribe_codes(replacement_codes)
            )
            trading_promotion_code_set = set(
                self._normalize_subscribe_codes(trading_promotion_codes)
            )
            normalized_codes, register_items = self._resolve_ws_register_items(
                codes,
                include_alternate_route=include_alternate_route,
                alternate_route_codes=alternate_route_codes,
            )
            if not normalized_codes:
                print("⚠️ [WS] 등록 가능한 유효 종목코드가 없어 REG 전송을 생략합니다.")
                return
            normalized_codes, register_items, budget_skipped_codes = (
                self._apply_registered_item_budget(
                    normalized_codes,
                    register_items,
                    enforce=enforce_item_budget,
                    replacement_codes=replacement_code_set,
                )
            )
            if budget_skipped_codes:
                print(
                    "🧯 [WS] REG item budget 초과로 종목 등록 생략: "
                    f"skipped={budget_skipped_codes} "
                    f"max_items={self._max_registered_item_count()}"
                )
                try:
                    self.event_bus.publish(
                        "WS_REG_BUDGET_SKIPPED",
                        {
                            "codes": budget_skipped_codes,
                            "source": source,
                            "max_items": self._max_registered_item_count(),
                            "registered_item_count": sum(
                                len(tuple(items or ()))
                                for items in self._registered_items_by_code.values()
                            ),
                        },
                    )
                except Exception as exc:
                    log_error(f"[WS] REG budget skip event publish failed: {exc}")
            if not normalized_codes:
                return
            register_items_by_code = self._items_by_code(
                normalized_codes, register_items
            )

            for _ in range(100):
                if self._stop_event.is_set():
                    return
                if self.websocket and self._session_ready.is_set():
                    break
                await asyncio.sleep(0.1)

            if self._stop_event.is_set():
                return

            if self.websocket and self._session_ready.is_set():
                if remove_before_reg:
                    remove_sent = await self._send_remove(
                        normalized_codes,
                        update_local_state=False,
                        source=source,
                        reason="remove_before_reg_recovery",
                    )
                    if not remove_sent:
                        log_error(
                            "[WS] REMOVE-before-REG failed; replacement REG blocked "
                            f"codes={normalized_codes} source={source or '-'}"
                        )
                        return
                    await asyncio.sleep(0.1)
                batch_size = min(
                    int(getattr(TRADING_RULES, "WS_REG_BATCH_SIZE", 20) or 20), 50
                )
                total_batches = (len(normalized_codes) + batch_size - 1) // batch_size
                print(
                    f"📝 [WS] 종목 등록(REG) 전송 시도: {normalized_codes} "
                    f"(grp_no=1, refresh=1, items={register_items}, "
                    f"batch_size={batch_size}, alternate={include_alternate_route}, "
                    f"replace_existing={replace_existing}, source={source or '-'}, "
                    f"repair_cycle={repair_cycle or '-'}, "
                    f"realtime_types={requested_realtime_types}, "
                    f"remove_before_reg={remove_before_reg})"
                )
                for batch_index, batch_codes in enumerate(
                    self._chunked(normalized_codes, batch_size), start=1
                ):
                    if self._stop_event.is_set() or not self.websocket:
                        return
                    batch_code_set = set(batch_codes)
                    batch_items = [
                        item
                        for item in register_items
                        if self._normalize_code(item) in batch_code_set
                    ]
                    reg_packet = {
                        "trnm": "REG",
                        "grp_no": "1",
                        "refresh": "1",
                        "data": [
                            {"item": batch_items, "type": [realtime_type]}
                            for realtime_type in requested_realtime_types
                        ],
                    }
                    await self.websocket.send(json.dumps(reg_packet))
                    reg_sent_at = time.time()
                    with self.lock:
                        self.subscribed_codes.update(batch_codes)
                        self._micro_reversion_observation_only_codes.difference_update(
                            batch_code_set.intersection(trading_promotion_code_set)
                        )
                        for code in batch_codes:
                            self._registered_items_by_code[code] = tuple(
                                register_items_by_code.get(code) or ()
                            )
                            target = self._ensure_target_defaults(code)
                            if "0w" in requested_realtime_types:
                                target["program_subscription_requested_at"] = (
                                    reg_sent_at
                                )
                                if "0w" not in (target.get("received_types") or set()):
                                    target["program_missing_reason"] = (
                                        "program_0w_awaiting_first_observation"
                                    )
                    print(
                        "📡 [WS] 종목 등록 패킷 전송 완료(실수신 대기): "
                        f"grp_no=1 refresh=1 batch={batch_index}/{total_batches} "
                        f"code_count={len(batch_codes)} item_count={len(batch_items)} "
                        f"replace_existing={replace_existing} source={source or '-'} "
                        f"repair_cycle={repair_cycle or '-'} "
                        f"codes={batch_codes}"
                    )
                    await asyncio.sleep(0.15)
            else:
                print(
                    f"⚠️ [WS] 로그인 준비가 완료되지 않아 REG 전송 실패: {normalized_codes}"
                )
        except asyncio.CancelledError:
            return
        except Exception as e:
            log_error(f"🚨 [WS] _send_reg 에러 발생: {e}")
            print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")

    def execute_subscribe(
        self,
        codes,
        *,
        force=False,
        source="",
        repair_cycle="",
        include_alternate_route=False,
        remove_before_reg=None,
        required_realtime_types=None,
        realtime_types=None,
        observation_only=False,
    ):
        if not codes:
            return
        if isinstance(codes, str):
            codes = [codes]
        if self._stop_event.is_set() or not self._started:
            return

        force = self._flag_enabled(force, default=False)
        observation_only = self._flag_enabled(observation_only, default=False)
        explicit_alternate_route = self._flag_enabled(
            include_alternate_route, default=False
        )
        normalized_codes = self._normalize_subscribe_codes(codes)
        requested_items_by_code = {}
        for raw_code in codes:
            normalized = self._normalize_code(raw_code)
            requested_item = self._explicit_ws_item(raw_code, normalized) or normalized
            if normalized and requested_item:
                requested_items = requested_items_by_code.setdefault(normalized, [])
                if requested_item not in requested_items:
                    requested_items.append(requested_item)
        with self.lock:
            existing_source_only = set(normalized_codes).intersection(
                self._micro_reversion_observation_only_codes
            )
            transitioned_source_only = (
                set() if observation_only else existing_source_only
            )
            source_only_replacement = (
                existing_source_only if observation_only and force else set()
            )
            if observation_only:
                self._micro_reversion_observation_only_codes.update(
                    code
                    for code in normalized_codes
                    if code not in self.subscribed_codes
                )
            else:
                self._micro_reversion_observation_only_codes.difference_update(
                    set(normalized_codes).difference(transitioned_source_only)
                )
        required_realtime_types = self._normalize_required_realtime_types(
            required_realtime_types
        )
        if required_realtime_types:
            with self.lock:
                for code in normalized_codes:
                    self._required_realtime_types_by_code[code] = (
                        required_realtime_types
                    )
        new_targets = (
            normalized_codes
            if force
            else [
                code
                for code in normalized_codes
                if code not in self.subscribed_codes or code in transitioned_source_only
            ]
        )
        send_ready = bool(
            self.loop and self.loop.is_running() and not self._stop_event.is_set()
        )
        if send_ready:
            transition_targets = [
                code
                for code in new_targets
                if code in transitioned_source_only or code in source_only_replacement
            ]
            regular_targets = [
                code for code in new_targets if code not in transitioned_source_only
            ]
            allowed_regular, skipped_recent = self._filter_recent_reg_targets(
                regular_targets, force=force
            )
            new_targets = [
                code
                for code in new_targets
                if code in transition_targets or code in allowed_regular
            ]
            if skipped_recent:
                print(
                    "⏳ [WS] 최근 REG 중복 생략: "
                    f"codes={skipped_recent} ttl_sec={self._recent_reg_ttl_sec():.1f}"
                )

        if new_targets and send_ready:
            replace_existing = not bool(self.subscribed_codes)
            source_key = str(source or "").lower()
            repair_cycle_key = str(repair_cycle or "").lower()
            persistent_repair = (
                "persistent" in source_key or repair_cycle_key == "persistent_ws_gap"
            )
            if remove_before_reg is None:
                remove_before_reg = bool(
                    transitioned_source_only or source_only_replacement
                ) or (
                    persistent_repair
                    and self._persistent_repair_remove_before_reg_enabled()
                )
            else:
                remove_before_reg = self._flag_enabled(remove_before_reg, default=False)
            if persistent_repair:
                new_targets, repair_skipped = self._filter_persistent_repair_targets(
                    new_targets
                )
                if repair_skipped:
                    print(
                        "🧯 [WS] persistent repair 등록 제한: "
                        f"allowed={new_targets} skipped={repair_skipped} "
                        f"max_codes={self._persistent_repair_max_codes()} "
                        f"ttl_sec={self._persistent_repair_ttl_sec():.1f}"
                    )
                if not new_targets:
                    return
                rebuild_existing_group, rebuild_targets = (
                    self._persistent_repair_rebuild_targets(new_targets)
                )
                if rebuild_existing_group:
                    print(
                        "🔁 [WS] persistent repair 전체 REG 그룹 재구성: "
                        f"repair_targets={new_targets} rebuild_targets={rebuild_targets} "
                        f"min_interval_sec={self._persistent_repair_rebuild_group_min_interval_sec():.1f}"
                    )
                    new_targets = rebuild_targets
                    replace_existing = True
            enforce_item_budget = True
            include_alternate_route = persistent_repair or explicit_alternate_route
            alternate_route_codes = None
            if include_alternate_route:
                alternate_route_codes, alternate_skipped = (
                    self._filter_alternate_route_targets(new_targets)
                )
                if alternate_skipped:
                    print(
                        "🧯 [WS] alternate route 등록 제한: "
                        f"allowed={alternate_route_codes} skipped={alternate_skipped} "
                        f"max_codes={self._alternate_route_max_codes()} "
                        f"ttl_sec={self._alternate_route_ttl_sec():.1f}"
                    )
            send_targets = []
            for code in new_targets:
                explicit_items = requested_items_by_code.get(code) or []
                send_targets.extend(explicit_items or [code])
            future = asyncio.run_coroutine_threadsafe(
                self._send_reg(
                    send_targets,
                    replace_existing=replace_existing,
                    enforce_item_budget=enforce_item_budget,
                    include_alternate_route=include_alternate_route,
                    alternate_route_codes=alternate_route_codes,
                    remove_before_reg=remove_before_reg,
                    source=source,
                    repair_cycle=repair_cycle,
                    realtime_types=realtime_types,
                    replacement_codes=(
                        transitioned_source_only | source_only_replacement
                    ),
                    trading_promotion_codes=transitioned_source_only,
                ),
                self.loop,
            )
            with self._pending_future_lock:
                self._pending_loop_futures.add(future)

            def on_complete(fut):
                with self._pending_future_lock:
                    self._pending_loop_futures.discard(fut)
                try:
                    fut.result()
                except asyncio.CancelledError:
                    return
                except concurrent.futures.CancelledError:
                    return
                except Exception as e:
                    if self._stop_event.is_set() or "cancelled" in str(e).lower():
                        return
                    log_error(f"🚨 [WS] 스레드 통신 간 에러 발생: {e}")
                    print(f"🚨 [WS] 스레드 통신 간 에러 발생: {e}")

            future.add_done_callback(on_complete)

    def execute_unsubscribe(self, codes):
        if not codes:
            return
        if isinstance(codes, str):
            codes = [codes]

        normalized_codes = set(self._normalize_subscribe_codes(codes))
        with self.lock:
            widget_retained_codes = {
                code
                for code in normalized_codes
                if is_pinned_ws_observation_registration(
                    code, tuple(self._registered_items_by_code.get(code) or ())
                )
            }
            micro_retained_codes = normalized_codes.intersection(
                self._micro_reversion_observation_items_by_code
            )
            micro_retained_codes.difference_update(widget_retained_codes)
            retained_codes = widget_retained_codes | micro_retained_codes
        normalized_codes.difference_update(retained_codes)
        if widget_retained_codes:
            with self.lock:
                first_notice_codes = widget_retained_codes.difference(
                    self._pinned_unreg_notice_codes
                )
                self._pinned_unreg_notice_codes.update(widget_retained_codes)
            if first_notice_codes:
                print(
                    "📌 [WS] 비교전용 관측 구독 REMOVE 생략: "
                    f"codes={sorted(first_notice_codes)} "
                    "authority=widget_ws_price_comparison_only"
                )
        if micro_retained_codes:
            for code in sorted(micro_retained_codes):
                self.retain_micro_reversion_as_observation_only(code)
            with self.lock:
                first_notice_codes = micro_retained_codes.difference(
                    self._micro_reversion_observation_notice_codes
                )
                self._micro_reversion_observation_notice_codes.update(
                    micro_retained_codes
                )
            if first_notice_codes:
                print(
                    "📌 [WS] micro-reversion source-only 관측 구독 REMOVE 생략: "
                    f"codes={sorted(first_notice_codes)} "
                    "authority=next_session_market_data_observation_only"
                )
        if not normalized_codes:
            return

        items_by_code_snapshot = {}
        with self.lock:
            items_by_code_snapshot = {
                code: tuple(self._registered_items_by_code.get(code) or ())
                for code in normalized_codes
            }

        self.subscribed_codes.difference_update(normalized_codes)
        with self.lock:
            for code in normalized_codes:
                self._recent_reg_request_ts.pop(code, None)
                self._registered_items_by_code.pop(code, None)
                self.realtime_data.pop(code, None)
                self._persistent_repair_request_ts.pop(code, None)
                self._persistent_repair_no_tick_attempts.pop(code, None)
                self._persistent_repair_stuck_until_ts.pop(code, None)
                self._persistent_repair_overflow_codes.pop(code, None)
                self._required_realtime_types_by_code.pop(code, None)
                self._micro_reversion_observation_only_codes.discard(code)
                self._micro_reversion_observation_notice_codes.discard(code)
        if self.loop and self.loop.is_running() and not self._stop_event.is_set():
            future = asyncio.run_coroutine_threadsafe(
                self._send_remove(
                    sorted(normalized_codes),
                    items_by_code_snapshot=items_by_code_snapshot,
                    update_local_state=False,
                    source="COMMAND_WS_UNREG",
                    reason="explicit_unsubscribe",
                ),
                self.loop,
            )
            with self._pending_future_lock:
                self._pending_loop_futures.add(future)

            def on_complete(fut):
                with self._pending_future_lock:
                    self._pending_loop_futures.discard(fut)
                try:
                    fut.result()
                except asyncio.CancelledError:
                    return
                except concurrent.futures.CancelledError:
                    return
                except Exception as e:
                    if self._stop_event.is_set() or "cancelled" in str(e).lower():
                        return
                    log_error(f"🚨 [WS] REMOVE 스레드 통신 간 에러 발생: {e}")
                    print(f"🚨 [WS] REMOVE 스레드 통신 간 에러 발생: {e}")

            future.add_done_callback(on_complete)

    def _normalize_micro_reversion_observation_items(self, items):
        normalized = OrderedDict()
        for raw_item in items or ():
            item = str(raw_item or "").strip().upper()
            code = self._normalize_code(item)
            if (
                len(code) != 6
                or not code.isdigit()
                or item not in {code, f"{code}_NX", f"{code}_AL"}
                or code in normalized
            ):
                return None
            normalized[code] = item
        return dict(normalized)

    def _configure_micro_reversion_observation_items(
        self, items, *, source, protected_runtime_codes=()
    ):
        new_items_by_code = self._normalize_micro_reversion_observation_items(items)
        if new_items_by_code is None:
            log_error(
                "[WS] micro-reversion observation set rejected: invalid or "
                "duplicate registration item"
            )
            return False
        protected_codes = set(
            self._normalize_subscribe_codes(protected_runtime_codes or ())
        )

        with self.lock:
            old_items_by_code = dict(self._micro_reversion_observation_items_by_code)
            retired_or_changed = {
                code
                for code, old_item in old_items_by_code.items()
                if new_items_by_code.get(code) != old_item
            }
            removable_codes = retired_or_changed.intersection(
                self._micro_reversion_observation_only_codes
            )
            for code in retired_or_changed:
                self._micro_reversion_observation_items_by_code.pop(code, None)
                self._micro_reversion_observation_only_codes.discard(code)
                self._micro_reversion_observation_notice_codes.discard(code)

        if removable_codes:
            self.execute_unsubscribe(sorted(removable_codes))

        with self.lock:
            self._micro_reversion_observation_items_by_code.update(new_items_by_code)
            subscribe_items = [
                item
                for code, item in new_items_by_code.items()
                if code not in self.subscribed_codes and code not in protected_codes
            ]

        if subscribe_items:
            self.execute_subscribe(
                subscribe_items,
                source=source,
                realtime_types=("0B", "0D"),
                observation_only=True,
            )
        print(
            "📌 [WS] micro-reversion source-only 관측 집합 반영: "
            f"requested={len(new_items_by_code)} subscribed_now={len(subscribe_items)} "
            f"retired={len(retired_or_changed)} "
            f"runtime_protected={len(set(new_items_by_code) & protected_codes)} "
            "trading_runtime_effect=false"
        )
        return True

    def _handle_micro_reversion_observation_set(self, payload):
        if self._stop_event.is_set() or not isinstance(payload, dict):
            return
        effective_date = str(payload.get("effective_date") or "")
        today = datetime.now(KST).date().isoformat()
        valid_authority = bool(
            effective_date == today
            and payload.get("decision_authority")
            == "next_session_market_data_observation_only"
            and payload.get("runtime_effect") is False
            and payload.get("market_data_subscription_effect") is True
            and payload.get("trading_runtime_effect") is False
            and payload.get("trading_decision_effect") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
            and payload.get("manual_control_exclusion_applied") is False
        )
        if not valid_authority:
            log_error(
                "[WS] micro-reversion observation set rejected: "
                f"effective_date={effective_date or '-'} today={today} "
                "reason=stale_or_authority_contract"
            )
            return
        self._configure_micro_reversion_observation_items(
            payload.get("registration_items") or (),
            source=str(payload.get("source") or "micro_reversion_collection_feedback"),
            protected_runtime_codes=payload.get("protected_runtime_codes") or (),
        )

    def _handle_reg_event(self, payload):
        if self._stop_event.is_set():
            return
        codes = payload.get("codes", [])
        source = str(payload.get("source") or "")
        repair_cycle = str(payload.get("repair_cycle") or "")
        force = (
            self._flag_enabled(payload.get("force"), default=False)
            or "recovery" in source
        )
        kwargs = {
            "force": force,
            "source": source,
            "repair_cycle": repair_cycle,
        }
        if "include_alternate_route" in payload:
            kwargs["include_alternate_route"] = payload.get("include_alternate_route")
        required_realtime_types = payload.get("required_realtime_types")
        if required_realtime_types is None and source.startswith("scanner_"):
            required_realtime_types = ("0B",)
        if required_realtime_types is not None:
            kwargs["required_realtime_types"] = required_realtime_types
        if "remove_before_reg" in payload:
            kwargs["remove_before_reg"] = payload.get("remove_before_reg")
        self.execute_subscribe(codes, **kwargs)

    def _handle_unreg_event(self, payload):
        if self._stop_event.is_set():
            return
        codes = payload.get("codes", [])
        self.execute_unsubscribe(codes)

    def get_latest_data(self, code):
        code = self._normalize_code(code)
        with self.lock:
            target = self.realtime_data.get(code, {})
            return self._snapshot_target(target) if target else {}

    def get_all_data(self, codes):
        """Return dict of latest data for multiple codes, acquiring lock once."""
        if isinstance(codes, str):
            codes = [codes]
        with self.lock:
            return {
                self._normalize_code(code): (
                    self._snapshot_target(
                        self.realtime_data.get(self._normalize_code(code), {})
                    )
                    if self.realtime_data.get(self._normalize_code(code), {})
                    else {}
                )
                for code in codes
            }
