import asyncio
import concurrent.futures
import websockets
import json
import threading
import time
import copy
from collections import deque
from queue import Queue, Empty
from datetime import datetime

# 💡 [Level 1 & 2 적용] 독립 로거 및 싱글톤 이벤트 버스 임포트
from src.utils.logger import log_error
from src.core.event_bus import EventBus
from src.utils.constants import CONFIG_PATH, DEV_PATH, TRADING_RULES


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
        
        # 전역 EventBus 인스턴스 획득 및 외부 명령 수신기 장착
        self.event_bus = EventBus()
        self.event_bus.subscribe("COMMAND_WS_REG", self._handle_reg_event)
        self.event_bus.subscribe("COMMAND_WS_UNREG", self._handle_unreg_event)
        # 💡 [추가] 최초 접속인지, 끊겼다가 다시 붙은(재접속) 것인지 구분하는 플래그
        self.is_reconnected = False
        self.condition_dict = {} # 💡 [추가] 일련번호(seq)와 검색식 이름을 매핑할 사전
        self.market_session_state = ''
        self.market_session_remaining = ''
        
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
        return str(code or '').strip()[:6]

    def _parse_order_execution_notice(self, values):
        status = str(values.get('913', '')).strip()
        code = str(values.get('9001', '')).replace('A', '').strip()
        order_no = str(values.get('9203', '')).strip()
        order_type_str = str(values.get('905', '')).strip()
        exec_price = self._safe_abs_int(values.get('910', '0'), 0)
        exec_qty = self._safe_abs_int(values.get('911', '0'), 0)
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
                'volume': 0, 'time': '', 'fluctuation': 0.0, 'open': 0,
                'orderbook': {'asks': [], 'bids': []},
                'prog_net_qty': 0, 'prog_delta_qty': 0,
                'prog_net_amt': 0, 'prog_delta_amt': 0,
                'prog_buy_qty': 0, 'prog_buy_amt': 0,
                'prog_sell_qty': 0, 'prog_sell_amt': 0,
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
                'last_prog_update_ts': 0.0,
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
            new_token = kiwoom_utils.get_kiwoom_token(self.conf)
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

        print("🔍 [WS] HTS 조건검색식 목록(CNSRLST)을 요청합니다.")
        await self.websocket.send(json.dumps({'trnm': 'CNSRLST'}))

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
                data_list = msg_dict.get('data', [])
                parsed_rows = self._parse_condition_list_rows(data_list)
                self.condition_dict.clear()
                target_seqs = []

                # 💡 HTS에서 만든 시간대별 모든 식을 다 찾습니다! (이름은 HTS 저장명에 맞게 추가하세요)
                target_keywords = [
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
                    "kospi_short_swing_01", # 💡 [신규] 14:30 ~ 15:30 종가/다음날 단기 스윙
                    "kospi_midterm_swing_01", # 💡 [신규] 14:30 ~ 15:30 종가/다음날 중기 스윙
                    "vcp_candid_01",       # 💡 [VCP 1단계] 15:30 ~ VCP 예비 후보 (다음날용)
                    "vcp_shooting_01",     # 💡 [VCP 2단계] 09:00 ~ 15:00 VCP 당일 슈팅
                    "vcp_shooting_next_01", # 💡 [VCP 3단계] 15:30 ~ VCP 다음날 시초가 예약 매수
                    "s15_scan_base_01",     # 💡 [S15 1단계] 09:02 ~ 10:30 S15 예비 후보 
                    "s15_trigger_break_01" # 💡 [S15 2단계] 09:05 ~ 11:00 S15 트리거 브레이크 
                ]
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
                        
                        print(f"📩 [WS 주문상태] {code} | 상태: '{status}' | 구분: '{order_type_str}'")
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
                        continue

                    # ===================================================
                    # [트랙 B] 실시간 주가/호가 데이터 처리
                    # ===================================================
                    item_code = d.get('item', '')
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
                            
                            target['received_types'].add(real_type)
                            target['last_ws_update_ts'] = time.time()
                            target['time'] = datetime.now().strftime('%H:%M:%S')

                            if not target.get('_first_tick_logged') and self._is_ws_ready(target, require_trade=False):
                                received = sorted(list(target.get('received_types') or []))
                                print(f"✅ [WS] 첫 실시간 데이터 수신 확인: {item_code} / types={received}")
                                target['_first_tick_logged'] = True
                            
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

    async def _send_reg(self, codes):
        try:
            normalized_codes = self._normalize_subscribe_codes(codes)
            if not normalized_codes:
                print("⚠️ [WS] 등록 가능한 유효 종목코드가 없어 REG 전송을 생략합니다.")
                return

            for _ in range(100):
                if self._stop_event.is_set():
                    return
                if self.websocket and self._session_ready.is_set():
                    break
                await asyncio.sleep(0.1)

            if self._stop_event.is_set():
                return

            if self.websocket and self._session_ready.is_set():
                batch_size = int(getattr(TRADING_RULES, 'WS_REG_BATCH_SIZE', 20) or 20)
                total_batches = (len(normalized_codes) + batch_size - 1) // batch_size
                print(f"📝 [WS] 종목 등록(REG) 전송 시도: {normalized_codes} (batch_size={batch_size})")
                for batch_index, batch_codes in enumerate(self._chunked(normalized_codes, batch_size), start=1):
                    if self._stop_event.is_set() or not self.websocket:
                        return
                    reg_packet = {
                        'trnm': 'REG',
                        'grp_no': '1',
                        'refresh': '1',
                        'data': [
                            {'item': batch_codes, 'type': ['0B']},
                            {'item': batch_codes, 'type': ['0D']},
                            {'item': batch_codes, 'type': ['0w']}
                        ]
                    }
                    await self.websocket.send(json.dumps(reg_packet))
                    self.subscribed_codes.update(batch_codes)
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

    def execute_subscribe(self, codes):
        if not codes: return
        if isinstance(codes, str): codes = [codes]
        if self._stop_event.is_set() or not self._started:
            return

        normalized_codes = self._normalize_subscribe_codes(codes)
        new_targets = [c for c in normalized_codes if c not in self.subscribed_codes]

        if new_targets and self.loop and self.loop.is_running() and not self._stop_event.is_set():
            future = asyncio.run_coroutine_threadsafe(self._send_reg(new_targets), self.loop)
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
                self.realtime_data.pop(code, None)
    
    def _handle_reg_event(self, payload):
        if self._stop_event.is_set():
            return
        codes = payload.get("codes", [])
        self.execute_subscribe(codes) 

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
