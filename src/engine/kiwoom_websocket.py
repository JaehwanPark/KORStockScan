import asyncio
import concurrent.futures
import websockets
import json
import threading
import time
import copy
import os
import shlex
from collections import OrderedDict, deque
from queue import Queue, Empty
from datetime import datetime
from pathlib import Path

# 💡 [Level 1 & 2 적용] 독립 로거 및 싱글톤 이벤트 버스 임포트
from src.utils.logger import log_error
from src.core.event_bus import EventBus
from src.utils.constants import CONFIG_PATH, DEV_PATH, TRADING_RULES
from src.database.db_manager import is_swing_real_watching_enabled
from src.engine.bd_fbuy_accum_pre_scanner import write_ws_snapshot
from src.engine.monitoring.market_halt_windows import append_market_session_event
from src.trading.entry.orderbook_stability_observer import ORDERBOOK_STABILITY_OBSERVER


class _LoginAckFailure(RuntimeError):
    def __init__(self, code, message):
        self.code = str(code or '').strip()
        self.message = str(message or '').strip()
        super().__init__(f"LOGIN ACK failed code={self.code or '?'} msg={self.message or '로그인 실패'}")

def _load_system_config():
    """웹소켓 매니저 전용 설정 로더 (의존성 분리)"""
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}


WS_CONDITION_SEARCH_ENABLED_ENV = "KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_WS_HOT_RUNTIME_OVERRIDE_KEYS = frozenset(
    {
        "KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES",
        "KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES",
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC",
    }
)
_WS_OPERATOR_RUNTIME_OVERRIDE_PATH = (
    PROJECT_ROOT / "data" / "threshold_cycle" / "runtime_env" / "operator_runtime_overrides.env"
)
_WS_HOT_RUNTIME_OVERRIDE_REFRESH_SEC = 5.0
_WS_HOT_RUNTIME_OVERRIDES = {
    "mtime_ns": None,
    "values": {},
    "next_check_ts": 0.0,
}
_WS_HOT_RUNTIME_OVERRIDES_LOCK = threading.Lock()


def is_ws_condition_search_enabled() -> bool:
    raw = str(os.getenv(WS_CONDITION_SEARCH_ENABLED_ENV, "") or "").strip().lower()
    return raw in {"1", "true", "t", "yes", "y", "on"}


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


class KiwoomWSManager:
    def __init__(self, token):
        # 💡 [우아한 아키텍처] 하드코딩 파괴! 설정 파일에서 URI를 동적으로 읽어옵니다.
        conf = _load_system_config()
        self.conf = conf
        # config에 URI가 없으면 안전하게 Mock API를 기본값으로 사용합니다.
        self.uri = conf.get('KIWOOM_WS_URI', 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket')
        
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
        self._last_dashboard_snapshot_at = 0.0
        self._dashboard_snapshot_write_inflight = False
        self._recent_reg_request_ts = {}
        self._alternate_route_request_ts = {}
        self._persistent_repair_request_ts = {}
        self._registered_items_by_code = {}
        
        # 전역 EventBus 인스턴스 획득 및 외부 명령 수신기 장착
        self.event_bus = EventBus()
        self.event_bus.subscribe("COMMAND_WS_REG", self._handle_reg_event)
        self.event_bus.subscribe("COMMAND_WS_UNREG", self._handle_unreg_event)
        # 💡 [추가] 최초 접속인지, 끊겼다가 다시 붙은(재접속) 것인지 구분하는 플래그
        self.is_reconnected = False
        self.condition_dict = {} # 💡 [추가] 일련번호(seq)와 검색식 이름을 매핑할 사전
        self.market_session_state = ''
        self.market_session_remaining = ''
        self._last_market_session_event_key = None
        
        print(f"🌐 [WS] 웹소켓 매니저 초기화 완료 (Target: {self.uri})")

    @staticmethod
    def _chunked(items, size):
        chunk_size = max(1, int(size or 1))
        for idx in range(0, len(items), chunk_size):
            yield items[idx:idx + chunk_size]
    
    @staticmethod
    def _safe_abs_int(val, default=0):
        try:
            return abs(int(float(str(val).replace(',', '').strip())))
        except Exception:
            return default

    @staticmethod
    def _safe_signed_int(val, default=0):
        try:
            return int(float(str(val).replace(',', '').replace('+', '').strip()))
        except Exception:
            return default

    @staticmethod
    def _safe_float(val, default=0.0):
        try:
            return float(str(val).replace(',', '').replace('+', '').strip())
        except Exception:
            return default

    @staticmethod
    def _normalize_code(code):
        raw = str(code or '').strip().upper().replace('.0', '')
        for suffix in ('_AL', '_NX'):
            if raw.endswith(suffix):
                raw = raw[:-3]
                break
        if raw.startswith('A') and len(raw) >= 7:
            raw = raw[1:]
        digits = ''.join(ch for ch in raw if ch.isdigit())
        return digits[-6:].zfill(6) if digits else raw[:6]

    @staticmethod
    def _explicit_ws_item(raw_code, canonical_code):
        raw = str(raw_code or '').strip().upper().replace('.0', '')
        if raw.endswith('_AL'):
            return f"{canonical_code}_AL"
        if raw.endswith('_NX'):
            return f"{canonical_code}_NX"
        return None

    def _parse_order_execution_notice(self, values):
        status = str(values.get('913', '')).strip()
        code = str(values.get('9001', '')).replace('A', '').strip()
        order_no = str(values.get('9203', '')).strip()
        order_type_str = str(values.get('905', '')).strip()
        exec_price = self._safe_abs_int(values.get('910', '0'), 0)
        exec_qty = self._safe_abs_int(values.get('911', '0'), 0)
        if '취소' in order_type_str:
            exec_type = 'BUY_CANCEL' if '매수' in order_type_str else 'SELL_CANCEL'
        else:
            exec_type = 'BUY' if '매수' in order_type_str else 'SELL'
        return {
            'status': status,
            'code': code,
            'order_no': order_no,
            'order_type_str': order_type_str,
            'exec_price': exec_price,
            'exec_qty': exec_qty,
            'exec_type': exec_type,
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

    def _resolve_ws_register_items(self, codes, *, include_alternate_route=False, alternate_route_codes=None):
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
        for raw_code in codes or []:
            canonical = self._normalize_code(raw_code)
            if canonical in normalized_codes:
                explicit = self._explicit_ws_item(raw_code, canonical)
                if explicit:
                    explicit_by_code[canonical] = explicit

        register_items = []
        try:
            from src.utils import kiwoom_utils

            for code in normalized_codes:
                explicit = explicit_by_code.get(code)
                if explicit:
                    register_items.append(explicit)
                    continue

                effective = kiwoom_utils.get_effective_kiwoom_code(code)
                items = [effective]
                if (
                    include_alternate_route
                    and code in alternate_route_code_set
                    and not str(effective or '').upper().endswith('_AL')
                ):
                    items.append(f"{code}_AL")
                register_items.extend(OrderedDict.fromkeys(items))
        except Exception as exc:
            log_error(f"🚨 [WS] 거래소별 실시간 등록 코드 변환 실패. 6자리 코드로 폴백합니다: {exc}")
            register_items = []
            for code in normalized_codes:
                explicit = explicit_by_code.get(code)
                if explicit:
                    register_items.append(explicit)
                else:
                    register_items.append(code)
                    if include_alternate_route and code in alternate_route_code_set:
                        register_items.append(f"{code}_AL")

        return normalized_codes, register_items

    @staticmethod
    def _max_registered_item_count():
        raw = os.getenv("KORSTOCKSCAN_WS_MAX_REG_ITEMS", "")
        try:
            value = int(str(raw).strip()) if str(raw).strip() else 24
        except Exception:
            value = 24
        if value <= 0:
            return 0
        return max(1, min(value, 200))

    def _items_by_code(self, normalized_codes, register_items):
        items_by_code = {}
        for code in normalized_codes or []:
            seen = OrderedDict()
            for item in register_items or []:
                if self._normalize_code(item) == code:
                    seen[str(item)] = None
            items_by_code[code] = list(seen.keys())
        return items_by_code

    def _apply_registered_item_budget(self, normalized_codes, register_items, *, enforce=False):
        if not enforce:
            return normalized_codes, register_items, []
        max_items = self._max_registered_item_count()
        if max_items <= 0:
            return normalized_codes, register_items, []

        items_by_code = self._items_by_code(normalized_codes, register_items)
        allowed_codes = []
        allowed_items = []
        skipped_codes = []

        with self.lock:
            planned_item_count = sum(
                len(tuple(items or ()))
                for items in self._registered_items_by_code.values()
            )
            for code in normalized_codes or []:
                candidate_items = tuple(items_by_code.get(code) or ())
                if not candidate_items:
                    continue
                existing_items = tuple(self._registered_items_by_code.get(code) or ())
                delta_items = [item for item in candidate_items if item not in existing_items]
                if code not in self.subscribed_codes:
                    required_delta = len(candidate_items)
                else:
                    required_delta = len(delta_items)
                if required_delta > 0 and planned_item_count + required_delta > max_items:
                    skipped_codes.append(code)
                    continue
                planned_item_count += max(0, required_delta)
                allowed_codes.append(code)
                allowed_items.extend(candidate_items)

        return allowed_codes, list(OrderedDict.fromkeys(allowed_items)), skipped_codes

    @staticmethod
    def _recent_reg_ttl_sec():
        raw = os.getenv("KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC", "")
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
        return max(0, min(value, 20))

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
        return max(0, min(value, 20))

    @staticmethod
    def _persistent_repair_ttl_sec():
        raw = _ws_hot_or_env_value("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC")
        try:
            value = float(str(raw).strip()) if str(raw).strip() else 30.0
        except Exception:
            value = 30.0
        return max(0.0, min(value, 1800.0))

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
        with self.lock:
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
                    continue
                self._persistent_repair_request_ts[code] = now_ts
                allowed.append(code)
        return allowed, skipped

    @staticmethod
    def _parse_condition_list_rows(data_list):
        rows = []
        for entry in data_list or []:
            seq = ""
            name = ""
            if isinstance(entry, dict):
                seq = str(
                    entry.get('seq')
                    or entry.get('cond_seq')
                    or entry.get('search_seq')
                    or entry.get('id')
                    or ''
                ).strip()
                name = str(
                    entry.get('condition_name')
                    or entry.get('cond_nm')
                    or entry.get('name')
                    or entry.get('search_name')
                    or ''
                ).strip()
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                seq = str(entry[0] or '').strip()
                name = str(entry[1] or '').strip()

            if seq or name:
                rows.append((seq, name))
        return rows

    def _append_strength_momentum(self, target, *, current_price, current_vpw, signed_qty, tick_value, buy_ratio, buy_qty, sell_qty):
        history = target.get('strength_momentum_history')
        if not isinstance(history, deque):
            maxlen = int(getattr(TRADING_RULES, 'SCALP_VPW_HISTORY_MAXLEN', 120) or 120)
            history = deque(maxlen=maxlen)
            target['strength_momentum_history'] = history

        buy_tick_value = 0
        sell_tick_value = 0
        if signed_qty > 0:
            buy_tick_value = tick_value
        elif signed_qty < 0:
            sell_tick_value = tick_value
        elif buy_qty > sell_qty:
            buy_tick_value = tick_value
        elif sell_qty > buy_qty:
            sell_tick_value = tick_value
        elif buy_ratio >= 50.0:
            buy_tick_value = tick_value
        else:
            sell_tick_value = tick_value

        now_ts = time.time()
        history.append({
            'ts': now_ts,
            'v_pw': float(current_vpw or 0.0),
            'price': int(current_price or 0),
            'signed_qty': int(signed_qty or 0),
            'buy_qty': int(buy_qty or 0),
            'sell_qty': int(sell_qty or 0),
            'buy_exec_qty_cum': int(buy_qty or 0),
            'sell_exec_qty_cum': int(sell_qty or 0),
            'tick_value': int(tick_value or 0),
            'buy_tick_value': int(buy_tick_value or 0),
            'sell_tick_value': int(sell_tick_value or 0),
            'buy_ratio': float(buy_ratio or 0.0),
        })

        keep_seconds = max(15.0, float(getattr(TRADING_RULES, 'SCALP_VPW_WINDOW_SECONDS', 5) or 5) * 3.0)
        cutoff = now_ts - keep_seconds
        while history and float((history[0] or {}).get('ts', 0.0) or 0.0) < cutoff:
            history.popleft()

    def _ensure_target_defaults(self, item_code):
        if item_code not in self.realtime_data:
            history_maxlen = int(getattr(TRADING_RULES, 'SCALP_VPW_HISTORY_MAXLEN', 120) or 120)
            self.realtime_data[item_code] = {
                'curr': 0, 'v_pw': 0, 'ask_tot': 0, 'bid_tot': 0,
                'volume': 0, 'time': '', 'fluctuation': 0.0, 'open': 0, 'high': 0, 'low': 0,
                'orderbook': {'asks': [], 'bids': []},
                'expected_open': {'price': 0, 'qty': 0, 'source': ''},
                'prog_net_qty': 0, 'prog_delta_qty': 0,
                'prog_net_amt': 0, 'prog_delta_amt': 0,
                'prog_buy_qty': 0, 'prog_buy_amt': 0,
                'prog_sell_qty': 0, 'prog_sell_amt': 0,
                'foreign_broker_sell_est_qty': 0,
                'foreign_broker_sell_est_delta_qty': 0,
                'foreign_broker_buy_est_qty': 0,
                'foreign_broker_buy_est_delta_qty': 0,
                'foreign_broker_net_est_qty': 0,
                'foreign_broker_net_est_delta_qty': 0,
                'tick_trade_value': 0, 'cum_trade_value': 0,
                'buy_exec_volume': 0, 'sell_exec_volume': 0,
                'buy_ratio': 0.0, 'net_buy_exec_volume': 0,
                'sell_exec_single': 0, 'buy_exec_single': 0,
                'net_bid_depth': 0, 'bid_depth_ratio': 0.0,
                'net_ask_depth': 0, 'ask_depth_ratio': 0.0,
                'market_session_state': self.market_session_state,
                'market_session_remaining': self.market_session_remaining,
                'received_types': set(),
                'last_ws_update_ts': 0.0,
                'last_realtime_type_ts': {},
                'last_prog_update_ts': 0.0,
                'last_foreign_broker_update_ts': 0.0,
                'program_history': deque(maxlen=120),
                'strength_momentum_history': deque(maxlen=history_maxlen),
                '_first_tick_logged': False,
                'last_trade_tick': None,
            }
        return self.realtime_data[item_code]

    @staticmethod
    def _has_orderbook(target):
        ob = target.get('orderbook') or {}
        return bool(ob.get('asks')) or bool(ob.get('bids'))

    def _is_ws_ready(self, target, require_trade=False):
        if not target:
            return False

        received_types = target.get('received_types') or set()
        has_trade = target.get('curr', 0) > 0 or ('0B' in received_types)
        has_orderbook = self._has_orderbook(target)
        has_program = '0w' in received_types
        has_timestamp = bool(target.get('time')) or bool(target.get('last_ws_update_ts'))

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
        snapshot['market_session_state'] = self.market_session_state
        snapshot['market_session_remaining'] = self.market_session_remaining
        for key in ("price_history", "v_pw_history", "signed_volume_history", "program_history", "strength_momentum_history"):
            if isinstance(snapshot.get(key), deque):
                snapshot[key] = list(snapshot[key])
        return snapshot

    def _maybe_write_dashboard_snapshot(self):
        now_ts = time.time()
        if self._dashboard_snapshot_write_inflight or now_ts - float(self._last_dashboard_snapshot_at or 0.0) < 10.0:
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

        threading.Thread(target=_write_snapshot_async, name="bd-fbuy-ws-snapshot", daemon=True).start()
    
    def _enqueue_state_event(self, event_type, payload):
        if self._stop_event.is_set():
            return
        self._state_event_queue.put((event_type, payload or {}))

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

    def _queue_tick_event(self, code, data):
        if self._stop_event.is_set():
            return

        with self._tick_lock:
            self._pending_tick_events[code] = {
                'code': code,
                'data': data
            }
        self._tick_dispatch_event.set()

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
                    log_error(f"[WS] tick event dispatch failed ({payload.get('code')}): {e}")

    def stop(self):
        if self._stop_event.is_set():
            return

        self._stop_event.set()
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

        ws = self.websocket
        if ws and self.loop and self.loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(ws.close(), self.loop)
            except Exception as e:
                log_error(f"[WS] stop() websocket close failed: {e}")

        current_thread = threading.current_thread()
        for thread in [self._state_dispatch_thread, self._tick_dispatch_thread, self._ws_thread]:
            if thread and thread is not current_thread and thread.is_alive():
                thread.join(timeout=2)

        self.websocket = None

    @staticmethod
    def _is_login_success_message(msg_dict):
        if not isinstance(msg_dict, dict):
            return False
        if str(msg_dict.get('trnm', '') or '').strip().upper() != 'LOGIN':
            return False
        code = msg_dict.get('return_code', msg_dict.get('rt_cd', ''))
        return str(code).strip() == '0'

    @staticmethod
    def _is_login_failure_message(msg_dict):
        if not isinstance(msg_dict, dict):
            return False
        if str(msg_dict.get('trnm', '') or '').strip().upper() != 'LOGIN':
            return False
        code = str(msg_dict.get('return_code', msg_dict.get('rt_cd', ''))).strip()
        return bool(code) and code != '0'

    @staticmethod
    def _is_auth_token_failure(code, message):
        code_str = str(code or '').strip()
        msg = str(message or '')
        if '8005' in code_str:
            return True
        if '8005' in msg:
            return True
        if 'Token' in msg or '토큰' in msg or '인증' in msg:
            return True
        return False

    def _refresh_ws_token(self):
        now_ts = time.time()
        # 토큰 인증 실패 루프에서 과도한 재발급 스팸을 방지합니다.
        if now_ts - self._last_token_refresh_at < 5:
            return False

        try:
            from src.utils import kiwoom_utils
            new_token = kiwoom_utils.get_kiwoom_token(self.conf, force_refresh=True)
        except Exception as e:
            log_error(f"❌ [WS TOKEN 재발급] 예외: {e}")
            self._last_token_refresh_at = now_ts
            return False

        self._last_token_refresh_at = now_ts
        if not new_token:
            log_error("❌ [WS TOKEN 재발급] 실패")
            return False

        self.token = new_token
        print("✅ [WS TOKEN 재발급] 성공. 새 토큰으로 재접속합니다.")
        return True

    async def _await_login_ack(self, ws, timeout_sec=5.0):
        deadline = time.time() + max(1.0, float(timeout_sec or 0.0))
        while not self._stop_event.is_set() and time.time() < deadline:
            remaining = max(0.1, deadline - time.time())
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=remaining)
            except asyncio.TimeoutError:
                break

            try:
                msg_dict = json.loads(message)
            except Exception:
                continue

            trnm = str(msg_dict.get('trnm', '') or '').strip().upper()
            if trnm == 'PING':
                await ws.send(json.dumps({"trnm": "PONG"}))
                continue

            if self._is_login_success_message(msg_dict):
                print("✅ [WS] 로그인 응답 확인 완료")
                return

            if self._is_login_failure_message(msg_dict):
                code = msg_dict.get('return_code', msg_dict.get('rt_cd', '?'))
                message = msg_dict.get('return_msg', msg_dict.get('msg1', '로그인 실패'))
                raise _LoginAckFailure(code, message)

            await self._handle_message(json.dumps(msg_dict))

        raise TimeoutError("LOGIN ACK timeout")

    async def _send_post_login_bootstrap(self):
        if not self.websocket:
            return

        if is_ws_condition_search_enabled():
            print("🔍 [WS] HTS 조건검색식 목록(CNSRLST)을 요청합니다.")
            await self.websocket.send(json.dumps({'trnm': 'CNSRLST'}))
        else:
            self.condition_dict.clear()
            print(
                "[WS_CONDITION_SEARCH_DISABLED] HTS 조건검색식 목록 요청 생략 "
                f"env={WS_CONDITION_SEARCH_ENABLED_ENV}"
            )

        if self.is_reconnected:
            print("🔄 [WS] 웹소켓 재접속 감지! EventBus에 상태 동기화 이벤트를 발행합니다.")
            self._enqueue_state_event("WS_RECONNECTED", {})

        self.is_reconnected = True

        exec_reg_packet = {
            "trnm": "REG",
            "grp_no": "2",
            "refresh": "1",
            "data": [
                {
                    "item": [""],
                    "type": ["00"]
                }
            ]
        }
        await self.websocket.send(json.dumps(exec_reg_packet))
        print("📝 [WS] 🚨 계좌 주문/체결통보(00) 감시망 등록 완료!")

        session_reg_packet = {
            "trnm": "REG",
            "grp_no": "3",
            "refresh": "1",
            "data": [
                {
                    "item": [""],
                    "type": ["0s"]
                }
            ]
        }
        await self.websocket.send(json.dumps(session_reg_packet))
        print("📝 [WS] 장운영구분(0s) 감시망 등록 완료!")

        if self.subscribed_codes:
            await self._send_reg(list(self.subscribed_codes))

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
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
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

                    login_packet = {'trnm': 'LOGIN', 'token': self.token}
                    await ws.send(json.dumps(login_packet))
                    print("🔑 [WS] 로그인 패킷 전송 완료")
                    await self._await_login_ack(ws)
                    await self._send_post_login_bootstrap()
                    self._session_ready.set()

                    while True:
                        message = await ws.recv()
                        await self._handle_message(message)

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
                    print(f"⚠️ [WS] 로그인 인증 실패 감지(code={e.code}). 토큰 재발급을 시도합니다.")
                    refreshed = self._refresh_ws_token()
                    await asyncio.sleep(1 if refreshed else 3)
                else:
                    log_error(f"🚨 [WS] 로그인 실패: {e}")
                    print(f"🚨 [WS] 로그인 실패: {e}")
                    await asyncio.sleep(3)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                from src.utils.logger import log_error
                log_error(f"🚨 [WS] 예상치 못한 오류: {e}")
                print(f"🚨 [WS] 예상치 못한 오류: {e}")
                self.websocket = None
                self._session_ready.clear()
                await asyncio.sleep(3)
        self.websocket = None
        self._session_ready.clear()

    async def _handle_message(self, message):
        try:
            msg_dict = json.loads(message)
            trnm = msg_dict.get('trnm')
            
            # =========================================================
            # 🏓 [핵심] 생존 신고 (PING/PONG)
            # =========================================================
            if trnm == 'PING':
                if self.websocket:
                    pong_packet = json.dumps({"trnm": "PONG"})
                    await self.websocket.send(pong_packet)
                return
            
            # =========================================================
            # 🚀 [추가 2] 조건검색식 목록 응답 수신 (ka10171)
            # =========================================================
            if trnm == 'CNSRLST':
                if not is_ws_condition_search_enabled():
                    self.condition_dict.clear()
                    print(
                        "[WS_CONDITION_SEARCH_DISABLED] CNSRLST 응답 무시 "
                        f"env={WS_CONDITION_SEARCH_ENABLED_ENV}"
                    )
                    return
                data_list = msg_dict.get('data', [])
                parsed_rows = self._parse_condition_list_rows(data_list)
                self.condition_dict.clear()
                target_seqs = []

                # 💡 HTS에서 만든 시간대별 모든 식을 다 찾습니다! (이름은 HTS 저장명에 맞게 추가하세요)
                scalp_condition_keywords = [
                    "scalp_candid_aggressive_01", # 09:00 ~ 09:30 초단타 후보군 (공격형)
                    "scalp_candid_normal_01", # 09:00 ~ 09:30 초단타 후보군 (일반형)
                    "scalp_open_reclaim_01", # 09:03 ~ 09:20 시초 회복형 스캘핑
                    "scalp_vwap_reclaim_01", # 10:00 ~ 14:00 VWAP 재안착형 스캘핑
                    "scalp_dryup_squeeze_01", # 09:30 ~ 13:30 거래마름 스퀴즈형 스캘핑
                    "scalp_preclose_01", # 14:30 ~ 15:20 장마감 전 스캘핑
                    "scalp_strong_01",  # 09:20 ~ 11:00 스캘핑 강세군 (공격형)
                    "scalp_underpress_01",  # 09:40 ~ 13:00 스캘핑 약세군 (수동)
                    "scalp_shooting_01",   # 09:40 ~ 13:30 스캘핑 슈팅스타 (공격형)
                    "scalp_afternoon_01",  # 13:00 ~ 15:30 장중진입_오후재점화
                    "vcp_candid_01",       # 💡 [VCP 1단계] 15:30 ~ VCP 예비 후보 (다음날용)
                    "vcp_shooting_01",     # 💡 [VCP 2단계] 09:00 ~ 15:00 VCP 당일 슈팅
                    "vcp_shooting_next_01", # 💡 [VCP 3단계] 15:30 ~ VCP 다음날 시초가 예약 매수
                    "s15_scan_base_01",     # 💡 [S15 1단계] 09:02 ~ 10:30 S15 예비 후보
                    "s15_trigger_break_01" # 💡 [S15 2단계] 09:05 ~ 11:00 S15 트리거 브레이크
                ]
                swing_condition_keywords = [
                    "kospi_short_swing_01", # 💡 [신규] 14:30 ~ 15:30 종가/다음날 단기 스윙
                    "kospi_midterm_swing_01", # 💡 [신규] 14:30 ~ 15:30 종가/다음날 중기 스윙
                ]
                target_keywords = list(scalp_condition_keywords)
                if is_swing_real_watching_enabled():
                    target_keywords.extend(swing_condition_keywords)
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
                    print(f"⚠️ [WS] 조건검색식 목록 응답이 비었거나 파싱되지 않았습니다. payload={msg_dict}")

                for seq, name in parsed_rows:
                    if any(k in name for k in target_keywords): 
                        target_seqs.append((seq, name))
                        self.condition_dict[str(seq)] = name # 💡 [핵심] 번호와 이름을 기억해 둡니다.
                
                if target_seqs:
                    for target_seq, target_name in target_seqs:
                        print(f"🎯 [WS] 스캘핑 조건식 발견: [{target_name}] (seq: {target_seq}). 실시간 PUSH 감시 요청.")
                        req_packet = {
                            'trnm': 'CNSRREQ', 'seq': str(target_seq), 'search_type': '1', 'stex_tp': 'K'
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
                            if available_names else " 수신 목록이 비어 있습니다."
                        )
                    )
                return
            
            # =========================================================
            # 🚀 [추가 3] 조건검색 최초 편입 목록 (ka10173)
            # =========================================================
            if trnm == 'CNSRREQ':
                if not is_ws_condition_search_enabled():
                    print(
                        "[WS_CONDITION_SEARCH_DISABLED] CNSRREQ 편입 목록 무시 "
                        f"env={WS_CONDITION_SEARCH_ENABLED_ENV}"
                    )
                    return
                # 💡 [핵심 방어] 키움 서버가 null(None)을 주더라도 안전하게 빈 리스트([])로 바꿔치기합니다!
                c_data = msg_dict.get('data') or []
                seq = str(msg_dict.get('seq', '')).strip()
                cnd_name = self.condition_dict.get(seq) or 'UNKNOWN_CONDITION'
                print(f"[WS] CNSRREQ init load: {len(c_data)} items (seq={seq}, condition={cnd_name})")
                for item in c_data:
                    code = item.get('jmcode', '').replace('A', '')
                    self._enqueue_state_event("CONDITION_MATCHED", {
                        'code': code,
                        'seq': seq,
                        'condition_name': cnd_name
                    })
                return
            
            # =========================================================
            # 📈 [기존 트랙] 실시간 주가 / 호가 / 체결 / 조건검색 데이터 처리
            # =========================================================
            if trnm == 'REAL' and 'data' in msg_dict:
                for d in msg_dict['data']:
                    values = d.get('values', {})
                    if not values: continue

                    real_type = d.get('type')
                    
                    # 🚀 실시간 조건검색 편입/이탈 통보 가로채기 (02)
                    if real_type == '02' or d.get('name') == '조건검색':
                        if not is_ws_condition_search_enabled():
                            continue
                        seq = str(values.get('841', '')).strip() # 💡 일련번호 추출
                        code = str(values.get('9001', '')).replace('A', '').strip()
                        insert_type = str(values.get('843', '')).strip() 
                        
                        # 기억해둔 번호로 검색식 이름을 알아냅니다.
                        cnd_name = self.condition_dict.get(seq) or 'UNKNOWN_CONDITION'

                        if insert_type == 'I':
                            # 💡 스나이퍼에게 출처(이름표)를 함께 보냅니다!
                            self._enqueue_state_event("CONDITION_MATCHED", {
                                'code': code,
                                'type': 'REALTIME',
                                'condition_name': cnd_name
                            })
                        elif insert_type == 'D':
                            self._enqueue_state_event("CONDITION_UNMATCHED", {
                                'code': code,
                                'type': 'REALTIME',
                                'condition_name': cnd_name
                            })
                        continue

                    # ===================================================
                    # [트랙 A] 🚨 주문/체결 통보 가로채기 (ORDER_EXECUTED)
                    # ===================================================
                    if real_type == '00' or d.get('name') == '주문체결':
                        notice = self._parse_order_execution_notice(values)
                        status = notice['status']
                        code = notice['code']
                        order_no = notice['order_no']
                        order_type_str = notice['order_type_str']
                        
                        print(f"📩 [WS 주문상태] {code} | 주문번호: '{order_no}' | 상태: '{status}' | 구분: '{order_type_str}'")
                        self._enqueue_state_event("ORDER_NOTICE", {
                            'code': code,
                            'order_no': order_no,
                            'type': notice['exec_type'],
                            'status': status,
                            'order_type_str': order_type_str,
                            'time': datetime.now().strftime('%H:%M:%S')
                        })

                        if status == '체결':
                            exec_price = notice['exec_price']
                            exec_qty = notice['exec_qty']
                            exec_type = notice['exec_type']
                            
                            print(f"🔔 [WS 실제체결] {code} {exec_type} {exec_qty}주 @ {exec_price}원 (주문번호: {order_no})")
                            
                            if exec_price > 0:
                                self._enqueue_state_event("ORDER_EXECUTED", {
                                    'code': code,
                                    'order_no': order_no,
                                    'type': exec_type,
                                    'price': exec_price,
                                    'qty': exec_qty,
                                    'time': datetime.now().strftime('%H:%M:%S')
                                })
                        continue

                    if real_type == '0s' or d.get('name') == '장시작시간':
                        self.market_session_state = str(values.get('215', '') or '').strip()
                        self.market_session_remaining = str(values.get('214', '') or '').strip()
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
                                log_error(f"🚨 [WS] 장운영구분 source-quality artifact 기록 실패: {exc}")
                        continue

                    # ===================================================
                    # [트랙 B] 실시간 주가/호가 데이터 처리
                    # ===================================================
                    raw_item_code = d.get('item', '')
                    item_code = self._normalize_code(raw_item_code)
                    if item_code and real_type != '00':
                        if item_code not in self.subscribed_codes:
                            continue
                        with self.lock:
                            # 1. 초기 데이터 구조 생성
                            target = self._ensure_target_defaults(item_code)

                            # 💡 안전한 파싱 헬퍼 (ValueError 방어막)
                            def safe_int(val, default=0):
                                val_str = str(val).replace('+', '').replace('-', '').strip()
                                return int(val_str) if val_str.isdigit() else default

                            # 데이터 추출 및 할당
                            if '10' in values: target['curr'] = safe_int(values['10'], target['curr'])
                            if '16' in values: target['open'] = safe_int(values['16'], target.get('open', 0))
                            if '17' in values: target['high'] = safe_int(values['17'], target.get('high', 0))
                            if '18' in values: target['low'] = safe_int(values['18'], target.get('low', 0))
                            if '13' in values: target['volume'] = safe_int(values['13'], target.get('volume', 0))
                                
                            if '12' in values:
                                try: target['fluctuation'] = float(values['12'].replace('+', ''))
                                except ValueError: pass
                            
                            if '228' in values:
                                try: target['v_pw'] = float(values['228'])
                                except ValueError: pass
                            if '14' in values: target['cum_trade_value'] = safe_int(values['14'], target.get('cum_trade_value', 0))
                            if '1313' in values: target['tick_trade_value'] = safe_int(values['1313'], target.get('tick_trade_value', 0))
                            if '1030' in values: target['sell_exec_volume'] = safe_int(values['1030'], target.get('sell_exec_volume', 0))
                            if '1031' in values: target['buy_exec_volume'] = safe_int(values['1031'], target.get('buy_exec_volume', 0))
                            if '1032' in values: target['buy_ratio'] = self._safe_float(values['1032'], target.get('buy_ratio', 0.0))
                            if '1314' in values: target['net_buy_exec_volume'] = self._safe_signed_int(values['1314'], target.get('net_buy_exec_volume', 0))
                            if '1315' in values: target['sell_exec_single'] = safe_int(values['1315'], target.get('sell_exec_single', 0))
                            if '1316' in values: target['buy_exec_single'] = safe_int(values['1316'], target.get('buy_exec_single', 0))
                                
                            if '121' in values: target['ask_tot'] = safe_int(values['121'])
                            if '125' in values: target['bid_tot'] = safe_int(values['125'])
                            if '128' in values: target['net_bid_depth'] = self._safe_signed_int(values['128'], target.get('net_bid_depth', 0))
                            if '129' in values: target['bid_depth_ratio'] = self._safe_float(values['129'], target.get('bid_depth_ratio', 0.0))
                            if '138' in values: target['net_ask_depth'] = self._safe_signed_int(values['138'], target.get('net_ask_depth', 0))
                            if '139' in values: target['ask_depth_ratio'] = self._safe_float(values['139'], target.get('ask_depth_ratio', 0.0))
                            target['market_session_state'] = self.market_session_state
                            target['market_session_remaining'] = self.market_session_remaining

                            # '0B' 체결 데이터는 필드가 문서/계정에 따라 달라질 수 있어
                            if real_type == '0B':
                                signed_qty = self._safe_signed_int(values.get('15'), 0)
                                current_price = target.get('curr', 0)
                                trade_price = safe_int(values.get('10'), current_price)
                                current_vpw = target.get('v_pw', 0.0)
                                tick_value = safe_int(values.get('1313'), 0)
                                if tick_value <= 0 and current_price > 0 and signed_qty != 0:
                                    tick_value = abs(int(current_price * abs(signed_qty)))
                                buy_qty = safe_int(values.get('1031'), 0)
                                sell_qty = safe_int(values.get('1030'), 0)
                                buy_ratio = self._safe_float(values.get('1032'), 0.0)
                                target['last_trade_tick'] = {
                                    'ts': time.time(),
                                    'values': values,
                                }
                                ORDERBOOK_STABILITY_OBSERVER.record_trade(
                                    item_code,
                                    price=trade_price,
                                    ts=target['last_trade_tick']['ts'],
                                )
                                self._append_strength_momentum(
                                    target,
                                    current_price=current_price,
                                    current_vpw=current_vpw,
                                    signed_qty=signed_qty,
                                    tick_value=tick_value,
                                    buy_ratio=buy_ratio,
                                    buy_qty=buy_qty,
                                    sell_qty=sell_qty,
                                )

                            # '0D' 주식호가잔량 데이터 파싱 (1~5호가)
                            if real_type == '0D':
                                asks, bids = [], []
                                for i in range(1, 6):
                                    ask_p = values.get(str(40 + i))
                                    ask_v = values.get(str(60 + i))
                                    bid_p = values.get(str(50 + i))
                                    bid_v = values.get(str(70 + i))

                                    if ask_p and ask_v:
                                        asks.append({'price': safe_int(ask_p), 'volume': safe_int(ask_v)})
                                    if bid_p and bid_v:
                                        bids.append({'price': safe_int(bid_p), 'volume': safe_int(bid_v)})
                                
                                target['orderbook']['asks'] = asks[::-1]
                                target['orderbook']['bids'] = bids
                                best_ask = target['orderbook']['asks'][0].get('price', 0) if target['orderbook']['asks'] else 0
                                best_bid = target['orderbook']['bids'][0].get('price', 0) if target['orderbook']['bids'] else 0
                                best_ask_qty = target['orderbook']['asks'][0].get('volume', 0) if target['orderbook']['asks'] else 0
                                best_bid_qty = target['orderbook']['bids'][0].get('volume', 0) if target['orderbook']['bids'] else 0
                                ask_depth_l = sum(int(level.get('volume', 0) or 0) for level in target['orderbook']['asks'])
                                bid_depth_l = sum(int(level.get('volume', 0) or 0) for level in target['orderbook']['bids'])
                                expected_price = safe_int(values.get('291') or values.get('23'))
                                expected_qty = safe_int(values.get('292') or values.get('24'))
                                if expected_price > 0 or expected_qty > 0:
                                    target['expected_open'] = {
                                        'price': expected_price,
                                        'qty': expected_qty,
                                        'price_vs_prev': safe_int(values.get('294') or values.get('200')),
                                        'price_vs_prev_rate': self._safe_float(values.get('295') or values.get('201'), 0.0),
                                        'sign': values.get('293') or values.get('238') or '',
                                        'volume_vs_prev_rate': self._safe_float(values.get('299'), 0.0),
                                        'source': '0D_expected_open',
                                        'valid_during_expected_session': True,
                                        'raw_field_ids': ['291', '292', '293', '294', '295', '299'],
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
                            
                            # '0w' 프로그램 매매 데이터 파싱
                            if real_type == '0w':
                                if '202' in values: target['prog_sell_qty'] = self._safe_signed_int(values['202'])
                                if '204' in values: target['prog_sell_amt'] = self._safe_signed_int(values['204'])
                                if '206' in values: target['prog_buy_qty'] = self._safe_signed_int(values['206'])
                                if '208' in values: target['prog_buy_amt'] = self._safe_signed_int(values['208'])
                                if '210' in values: target['prog_net_qty'] = self._safe_signed_int(values['210'])
                                if '211' in values: target['prog_delta_qty'] = self._safe_signed_int(values['211'])
                                if '212' in values: target['prog_net_amt'] = self._safe_signed_int(values['212'])
                                if '213' in values: target['prog_delta_amt'] = self._safe_signed_int(values['213'])
                                # 프로그램 히스토리 업데이트
                                target['program_history'].append({
                                    'ts': time.time(),
                                    'net_qty': target['prog_net_qty'],
                                    'delta_qty': target['prog_delta_qty'],
                                    'net_amt': target['prog_net_amt'],
                                    'delta_amt': target['prog_delta_amt'],
                                })
                                target['last_prog_update_ts'] = time.time()

                            # '0F' 주식당일거래원: 외국계 거래원 추정 수급
                            if real_type == '0F':
                                if '261' in values:
                                    target['foreign_broker_sell_est_qty'] = self._safe_signed_int(values['261'])
                                if '262' in values:
                                    target['foreign_broker_sell_est_delta_qty'] = self._safe_signed_int(values['262'])
                                if '263' in values:
                                    target['foreign_broker_buy_est_qty'] = self._safe_signed_int(values['263'])
                                if '264' in values:
                                    target['foreign_broker_buy_est_delta_qty'] = self._safe_signed_int(values['264'])
                                if '267' in values:
                                    target['foreign_broker_net_est_qty'] = self._safe_signed_int(values['267'])
                                if '268' in values:
                                    target['foreign_broker_net_est_delta_qty'] = self._safe_signed_int(values['268'])
                                target['last_foreign_broker_update_ts'] = time.time()
                            
                            target['received_types'].add(real_type)
                            now_update_ts = time.time()
                            target['last_ws_update_ts'] = now_update_ts
                            type_ts = target.setdefault('last_realtime_type_ts', {})
                            if isinstance(type_ts, dict):
                                type_ts[real_type] = now_update_ts
                            target['time'] = datetime.now().strftime('%H:%M:%S')

                            if not target.get('_first_tick_logged') and self._is_ws_ready(target, require_trade=False):
                                received = sorted(list(target.get('received_types') or []))
                                print(f"✅ [WS] 첫 실시간 데이터 수신 확인: {item_code} / types={received}")
                                target['_first_tick_logged'] = True
                            self._maybe_write_dashboard_snapshot()
                            
                            # 💡 파싱 완료 후 구독자들에게 전파
                            self._queue_tick_event(item_code, self._snapshot_target(target))

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"🚨 [WS] 메시지 파싱 에러 발생: {e} | Payload: {message[:150]}")

    def start(self):
        if self._started:
            return
        self._started = True
        self._stop_event.clear()

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

        self._state_dispatch_thread = threading.Thread(target=self._dispatch_state_events, daemon=True)
        self._tick_dispatch_thread = threading.Thread(target=self._dispatch_tick_events, daemon=True)
        self._ws_thread = threading.Thread(target=thread_target, daemon=True)

        self._state_dispatch_thread.start()
        self._tick_dispatch_thread.start()
        self._ws_thread.start()

    async def _send_reg(
        self,
        codes,
        *,
        replace_existing=True,
        enforce_item_budget=False,
        include_alternate_route=False,
        alternate_route_codes=None,
        source="",
    ):
        try:
            normalized_codes, register_items = self._resolve_ws_register_items(
                codes,
                include_alternate_route=include_alternate_route,
                alternate_route_codes=alternate_route_codes,
            )
            if not normalized_codes:
                print("⚠️ [WS] 등록 가능한 유효 종목코드가 없어 REG 전송을 생략합니다.")
                return
            normalized_codes, register_items, budget_skipped_codes = self._apply_registered_item_budget(
                normalized_codes,
                register_items,
                enforce=enforce_item_budget,
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
            register_items_by_code = self._items_by_code(normalized_codes, register_items)

            for _ in range(100):
                if self._stop_event.is_set():
                    return
                if self.websocket and self._session_ready.is_set():
                    break
                await asyncio.sleep(0.1)

            if self._stop_event.is_set():
                return

            if self.websocket and self._session_ready.is_set():
                batch_size = min(int(getattr(TRADING_RULES, 'WS_REG_BATCH_SIZE', 20) or 20), 50)
                total_batches = (len(normalized_codes) + batch_size - 1) // batch_size
                print(
                    f"📝 [WS] 종목 등록(REG) 전송 시도: {normalized_codes} "
                    f"(items={register_items}, batch_size={batch_size}, alternate={include_alternate_route})"
                )
                for batch_index, batch_codes in enumerate(self._chunked(normalized_codes, batch_size), start=1):
                    if self._stop_event.is_set() or not self.websocket:
                        return
                    batch_code_set = set(batch_codes)
                    batch_items = [
                        item
                        for item in register_items
                        if self._normalize_code(item) in batch_code_set
                    ]
                    reg_packet = {
                        'trnm': 'REG',
                        'grp_no': '1',
                        'refresh': '1' if replace_existing and batch_index == 1 else '0',
                        'data': [
                            {'item': batch_items, 'type': ['0B']},
                            {'item': batch_items, 'type': ['0D']},
                            {'item': batch_items, 'type': ['0w']},
                            {'item': batch_items, 'type': ['0F']}
                        ]
                    }
                    await self.websocket.send(json.dumps(reg_packet))
                    with self.lock:
                        self.subscribed_codes.update(batch_codes)
                        for code in batch_codes:
                            self._registered_items_by_code[code] = tuple(
                                register_items_by_code.get(code) or ()
                            )
                    print(
                        "📡 [WS] 종목 등록 패킷 전송 완료(실수신 대기): "
                        f"batch={batch_index}/{total_batches} codes={batch_codes}"
                    )
                    await asyncio.sleep(0.15)
            else:
                print(f"⚠️ [WS] 로그인 준비가 완료되지 않아 REG 전송 실패: {normalized_codes}")
        except asyncio.CancelledError:
            return
        except Exception as e:
            log_error(f"🚨 [WS] _send_reg 에러 발생: {e}")
            print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")

    def execute_subscribe(self, codes, *, force=False, source="", repair_cycle=""):
        if not codes: return
        if isinstance(codes, str): codes = [codes]
        if self._stop_event.is_set() or not self._started:
            return

        normalized_codes = self._normalize_subscribe_codes(codes)
        new_targets = normalized_codes if force else [c for c in normalized_codes if c not in self.subscribed_codes]
        send_ready = bool(self.loop and self.loop.is_running() and not self._stop_event.is_set())
        if send_ready:
            new_targets, skipped_recent = self._filter_recent_reg_targets(new_targets, force=force)
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
                "persistent" in source_key
                or repair_cycle_key == "persistent_ws_gap"
            )
            if persistent_repair:
                new_targets, repair_skipped = self._filter_persistent_repair_targets(new_targets)
                if repair_skipped:
                    print(
                        "🧯 [WS] persistent repair 등록 제한: "
                        f"allowed={new_targets} skipped={repair_skipped} "
                        f"max_codes={self._persistent_repair_max_codes()} "
                        f"ttl_sec={self._persistent_repair_ttl_sec():.1f}"
                    )
                if not new_targets:
                    return
            enforce_item_budget = True
            include_alternate_route = persistent_repair
            alternate_route_codes = None
            if include_alternate_route:
                alternate_route_codes, alternate_skipped = self._filter_alternate_route_targets(new_targets)
                if alternate_skipped:
                    print(
                        "🧯 [WS] alternate route 등록 제한: "
                        f"allowed={alternate_route_codes} skipped={alternate_skipped} "
                        f"max_codes={self._alternate_route_max_codes()} "
                        f"ttl_sec={self._alternate_route_ttl_sec():.1f}"
                    )
            future = asyncio.run_coroutine_threadsafe(
                self._send_reg(
                    new_targets,
                    replace_existing=replace_existing,
                    enforce_item_budget=enforce_item_budget,
                    include_alternate_route=include_alternate_route,
                    alternate_route_codes=alternate_route_codes,
                    source=source,
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

        normalized_codes = {str(code).strip()[:6] for code in codes if code}
        if not normalized_codes:
            return

        self.subscribed_codes.difference_update(normalized_codes)
        with self.lock:
            for code in normalized_codes:
                self._recent_reg_request_ts.pop(code, None)
                self._registered_items_by_code.pop(code, None)
                self.realtime_data.pop(code, None)
    
    def _handle_reg_event(self, payload):
        if self._stop_event.is_set():
            return
        codes = payload.get("codes", [])
        source = str(payload.get("source") or "")
        repair_cycle = str(payload.get("repair_cycle") or "")
        force = bool(payload.get("force")) or "recovery" in source
        self.execute_subscribe(codes, force=force, source=source, repair_cycle=repair_cycle)

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
            return {self._normalize_code(code): (self._snapshot_target(self.realtime_data.get(self._normalize_code(code), {})) if self.realtime_data.get(self._normalize_code(code), {}) else {}) for code in codes}
