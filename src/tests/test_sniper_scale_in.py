from dataclasses import replace
from datetime import datetime, timedelta

import src.engine.sniper_scale_in as scale_in
import src.engine.sniper_state_handlers as state_handlers
import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_entry_state as entry_state
import src.engine.sniper_sync as sniper_sync
import src.engine.trade_pause_control as trade_pause_control
import src.utils.runtime_flags as runtime_flags
from src.engine import kiwoom_orders


class _DummySession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return 1

    def first(self):
        return None


class _DummyDB:
    def get_session(self):
        return _DummySession()


def test_scalping_avg_down_disabled():
    stock = {"avg_down_count": 0}
    result = scale_in.evaluate_scalping_avg_down(stock, profit_rate=-4.0)
    assert result["should_add"] is False
    assert result["reason"] == "avg_down_disabled"


def test_scalping_pyramid_signal():
    stock = {"pyramid_count": 0}
    result = scale_in.evaluate_scalping_pyramid(
        stock, profit_rate=2.0, peak_profit=2.2, is_new_high=True
    )
    assert result["should_add"] is True
    assert result["add_type"] == "PYRAMID"


def test_swing_avg_down_bear_blocked():
    stock = {"avg_down_count": 0}
    result = scale_in.evaluate_swing_avg_down(stock, profit_rate=-8.0, market_regime="BEAR")
    assert result["should_add"] is False
    assert result["reason"] == "bear_avg_down_blocked"


def test_weighted_avg_price():
    avg = receipts.weighted_avg_price(10000, 10, 9500, 5)
    assert round(avg, 4) == 9833.3333


def test_describe_buy_capacity_relaxes_when_one_share_is_affordable():
    target_budget, safe_budget, qty, used_ratio = kiwoom_orders.describe_buy_capacity(
        current_price=1000,
        total_deposit=10000,
        ratio=0.10,
    )
    assert target_budget == 1000
    assert safe_budget == 1000
    assert qty == 1
    assert used_ratio == 1.0


def test_describe_buy_capacity_respects_absolute_budget_cap():
    target_budget, safe_budget, qty, used_ratio = kiwoom_orders.describe_buy_capacity(
        current_price=100000,
        total_deposit=10000000,
        ratio=0.50,
        max_budget=2000000,
    )
    assert target_budget == 2000000
    assert safe_budget == 1900000
    assert qty == 19
    assert used_ratio == 0.95


def test_add_count_increment_once_on_partial_fills(monkeypatch):
    # Prepare execution receipts environment
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args
        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts, "_update_db_for_add", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)

    target_stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "buy_price": 10000,
        "buy_qty": 10,
        "pending_add_order": True,
        "pending_add_type": "AVG_DOWN",
        "pending_add_qty": 10,
        "pending_add_ord_no": "123",
        "add_count": 0,
        "avg_down_count": 0,
    }
    receipts.ACTIVE_TARGETS.append(target_stock)

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "123", "price": 9500, "qty": 4}
    )
    assert target_stock["add_count"] == 1
    assert target_stock["avg_down_count"] == 1

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "123", "price": 9400, "qty": 3}
    )
    assert target_stock["add_count"] == 1
    assert target_stock["avg_down_count"] == 1


def test_update_db_for_add_does_not_touch_detached_record_after_commit(monkeypatch):
    class DetachedRecord:
        def __init__(self):
            self.buy_price = 10000
            self.buy_qty = 5
            self.add_count = 1
            self.avg_down_count = 1
            self.pyramid_count = 0
            self.last_add_type = None
            self.last_add_at = None
            self.scale_in_locked = False
            self.trailing_stop_price = None
            self.hard_stop_price = None
            self._detached = False

        def __getattribute__(self, name):
            if name not in {"_detached", "__dict__", "__class__", "__getattribute__", "__setattr__"}:
                detached = object.__getattribute__(self, "_detached")
                if detached:
                    raise RuntimeError(f"detached access: {name}")
            return object.__getattribute__(self, name)

    class DummyQuery:
        def __init__(self, record):
            self._record = record

        def filter_by(self, **kwargs):
            return self

        def first(self):
            return self._record

    class DummySession:
        def __init__(self, record):
            self._record = record

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self._record._detached = True
            return False

        def query(self, *args, **kwargs):
            return DummyQuery(self._record)

    class DummyDB:
        def __init__(self, record):
            self._record = record

        def get_session(self):
            return DummySession(self._record)

    class DummyEventBus:
        def __init__(self):
            self.published = []

        def publish(self, topic, payload):
            self.published.append((topic, payload))

    record = DetachedRecord()
    monkeypatch.setattr(receipts, "DB", DummyDB(record))
    monkeypatch.setattr(receipts, "event_bus", DummyEventBus())

    receipts._update_db_for_add(
        target_id=2196,
        exec_price=9500,
        exec_qty=3,
        now=datetime(2026, 4, 15, 9, 31, 54),
        target_stock={
            "name": "TEST",
            "code": "123456",
            "strategy": "SCALPING",
            "buy_price": 9800,
            "buy_qty": 8,
            "add_count": 2,
            "avg_down_count": 2,
            "msg_audience": "ADMIN_ONLY",
        },
        add_type="AVG_DOWN",
        count_increment=True,
    )

    assert record.__dict__["buy_price"] == 9800
    assert record.__dict__["buy_qty"] == 8
    assert len(receipts.event_bus.published) == 1
    assert "add_count=2" in receipts.event_bus.published[0][1]["message"]


def test_execute_scale_in_order_failure_no_pending(monkeypatch):
    state_handlers.KIWOOM_TOKEN = "test"

    monkeypatch.setattr(state_handlers, "calc_scale_in_qty", lambda *args, **kwargs: 1)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 100000)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: None)

    stock = {"name": "TEST", "strategy": "SCALPING", "buy_qty": 10}
    action = {"add_type": "AVG_DOWN"}
    ws_data = {"curr": 10000}

    state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        action=action,
        admin_id=1,
    )

    assert stock.get("pending_add_order") is None
    assert stock.get("pending_add_type") is None


def test_sell_priority_blocks_add(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10000}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}

    class DummyDB:
        def get_session(self):
            raise Exception("db not available")

    state_handlers.DB = DummyDB()

    called = {"gate": False, "eval": False, "add": False}

    def fake_gate(*args, **kwargs):
        called["gate"] = True
        return {"allowed": True, "reason": "ok"}

    def fake_eval(*args, **kwargs):
        called["eval"] = True
        return {"add_type": "PYRAMID", "reason": "forced"}

    def fake_process(*args, **kwargs):
        called["add"] = True

    monkeypatch.setattr(state_handlers, "can_consider_scale_in", fake_gate)
    monkeypatch.setattr(state_handlers, "_evaluate_scale_in_signal", fake_eval)
    monkeypatch.setattr(state_handlers, "_process_scale_in_action", fake_process)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
    }

    ws_data = {"curr": 90}

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert called["gate"] is False
    assert called["eval"] is False
    assert called["add"] is False


def test_timeout_pending_add_attempts_cancel_before_clear(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.KIWOOM_TOKEN = "token"

    cancel_calls = []

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs) or {"return_code": "0"},
    )

    stock = {
        "name": "TEST",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "pending_add_order": True,
        "pending_add_type": "AVG_DOWN",
        "pending_add_ord_no": "A1",
        "pending_add_requested_at": 1.0,
    }

    monkeypatch.setattr(state_handlers.time, "time", lambda: 100.0)
    result = state_handlers.can_consider_scale_in(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        strategy="SCALPING",
        market_regime="BULL",
    )

    assert result["allowed"] is False
    assert result["reason"] == "pending_add_timeout_released"
    assert len(cancel_calls) == 1
    assert stock.get("pending_add_order") is None


def test_missing_pending_ordno_locks_scale_in(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.DB = None

    stock = {
        "name": "TEST",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "pending_add_order": True,
        "pending_add_requested_at": 1.0,
    }

    result = state_handlers.can_consider_scale_in(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        strategy="SCALPING",
        market_regime="BULL",
    )

    assert result["allowed"] is False
    assert result["reason"] == "pending_add_recovered"
    assert stock["scale_in_locked"] is True
    assert stock.get("pending_add_order") is None


def test_scale_in_blocked_when_buy_side_paused(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: True)

    stock = {
        "name": "TEST",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
    }

    result = state_handlers.can_consider_scale_in(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        strategy="SCALPING",
        market_regime="BULL",
    )

    assert result["allowed"] is False
    assert result["reason"] == "buy_side_paused"


def test_watching_state_returns_early_when_buy_side_paused(monkeypatch):
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}

    called = {"deposit": False, "buy": False}

    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: True)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_deposit",
        lambda *args, **kwargs: called.__setitem__("deposit", True),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: called.__setitem__("buy", True),
    )

    stock = {"name": "TEST", "strategy": "SCALPING", "position_tag": "MIDDLE"}
    state_handlers.handle_watching_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        admin_id=1,
        radar=None,
        ai_engine=None,
    )

    assert called["deposit"] is False
    assert called["buy"] is False


def test_send_buy_order_market_blocked_when_paused(tmp_path, monkeypatch):
    pause_flag = tmp_path / "pause.flag"
    monkeypatch.setattr(runtime_flags, "get_pause_flag_path", lambda: pause_flag)
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_paused", lambda: True)

    result = kiwoom_orders.send_buy_order_market("123456", 1, "token")

    assert result["return_code"] == "PAUSED"
    assert result["return_msg"]
    assert result["return_msg"] == trade_pause_control.get_pause_state_label()


def test_send_buy_order_market_allows_order_after_resume(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"rt_cd": "0", "ord_no": "B123"}

    monkeypatch.setattr(kiwoom_orders, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(kiwoom_orders.requests, "post", lambda *args, **kwargs: DummyResponse())
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    result = kiwoom_orders.send_buy_order_market("123456", 1, "token")

    assert result["rt_cd"] == "0"
    assert result["ord_no"] == "B123"


def test_send_buy_order_market_maps_ioc_limit_to_best_ioc(monkeypatch):
    captured = {}

    class DummyResponse:
        status_code = 200

        def json(self):
            return {"rt_cd": "0", "ord_no": "BIOC"}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["payload"] = json
        return DummyResponse()

    monkeypatch.setattr(kiwoom_orders, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(kiwoom_orders.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    result = kiwoom_orders.send_buy_order_market(
        "123456",
        1,
        "token",
        order_type="00",
        price=10000,
        tif="IOC",
    )

    assert result["ord_no"] == "BIOC"
    assert captured["payload"]["trde_tp"] == "16"
    assert captured["payload"]["ord_uv"] == ""


def test_watching_state_submits_fallback_entry_bundle(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 2, 10, 0, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"

    sent_orders = []

    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_capacity",
        lambda *args, **kwargs: (50_000, 47_500, 5, 0.95),
    )
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": True,
            "mode": "fallback",
            "decision": "ALLOW_FALLBACK",
            "reason": "caution_fallback_allowed",
            "latency_state": "CAUTION",
            "orders": [
                {"tag": "fallback_scout", "qty": 1, "price": 10000, "order_type": "LIMIT", "tif": "IOC"},
                {"tag": "fallback_main", "qty": 4, "price": 9990, "order_type": "LIMIT", "tif": "DAY"},
            ],
        },
    )
    def fake_send_buy_order(code, qty, price, order_type_code, *args, **kwargs):
        sent_orders.append((qty, price, order_type_code, kwargs.get("tif")))
        return {"return_code": "0", "ord_no": f"O{len(sent_orders)}"}

    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", fake_send_buy_order)

    stock = {"id": 1, "name": "TEST", "strategy": "SCALPING", "position_tag": "VCP_NEXT"}
    state_handlers.handle_watching_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        admin_id=1,
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "BUY_ORDERED"
    assert len(sent_orders) == 2
    assert sent_orders[0] == (1, 0, "16", "IOC")
    assert sent_orders[1] == (3, 9990, "00", "DAY")
    assert len(stock["pending_entry_orders"]) == 2
    assert stock["entry_requested_qty"] == 4


def test_entry_arm_skips_strength_recheck_after_ai_confirm(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 3, 13, 45, 0)

    class DummyEventBus:
        def publish(self, *args, **kwargs):
            return None

    class DummyRadar:
        def get_smart_target_price(self, curr_price, **kwargs):
            return curr_price, 0.0

    class DummyAI:
        def analyze_target(self, *args, **kwargs):
            return {"action": "BUY", "score": 85, "reason": "confirmed"}

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False, SCALP_ENTRY_ARM_TTL_SEC=20)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"
    state_handlers.EVENT_BUS = DummyEventBus()

    momentum_calls = {"count": 0}
    pipeline_stages = []

    def fake_momentum_gate(ws_data):
        momentum_calls["count"] += 1
        return {
            "enabled": True,
            "allowed": True,
            "reason": "strong_absolute_override",
            "base_vpw": 100.0,
            "current_vpw": 100.0,
            "vpw_delta": 0.0,
            "slope_per_sec": 0.0,
            "window_sec": 8,
            "window_buy_value": 25000,
            "window_sell_value": 5000,
            "window_buy_ratio": 0.83,
            "window_exec_buy_ratio": 0.62,
            "window_net_buy_qty": 120,
            "elapsed_sec": 8.0,
        }

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        pipeline_stages.append(stage)

    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", fake_log_entry_pipeline)
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", fake_momentum_gate)
    monkeypatch.setattr(state_handlers, "arm_big_bite_if_triggered", lambda **kwargs: (False, {}))
    monkeypatch.setattr(state_handlers, "confirm_big_bite_follow_through", lambda **kwargs: (True, {}))
    monkeypatch.setattr(state_handlers, "build_tick_data_from_ws", lambda ws_data: {})
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [1])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [1])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_capacity",
        lambda *args, **kwargs: (100000, 95000, 5, 0.95),
    )
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": False,
            "mode": "reject",
            "decision": "REJECT",
            "reason": "latency_blocked",
            "latency_state": "DANGER",
            "orders": [],
            "signal_price": kwargs.get("signal_price"),
            "latest_price": kwargs.get("signal_price"),
            "computed_allowed_slippage": 0.0,
            "ws_age_ms": 0,
        },
    )

    stock = {"id": 7, "name": "ARMED", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.7}
    ws_data = {
        "curr": 10000,
        "v_pw": 100.0,
        "ask_tot": 30000,
        "bid_tot": 30000,
        "open": 9950,
        "fluctuation": 1.0,
        "orderbook": {"dummy": True},
    }

    state_handlers.handle_watching_state(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=DummyAI(),
    )

    assert stock.get("entry_armed") is True
    assert "entry_armed" in pipeline_stages
    assert "latency_block" in pipeline_stages
    assert momentum_calls["count"] == 1

    pipeline_stages.clear()

    def fail_if_rechecked(_ws_data):
        raise AssertionError("entry_armed 상태에서는 동적 체결강도 재평가를 하면 안 됩니다.")

    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", fail_if_rechecked)

    state_handlers.handle_watching_state(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=DummyAI(),
    )

    assert "entry_armed_resume" in pipeline_stages
    assert "blocked_strength_momentum" not in pipeline_stages
    assert "latency_block" in pipeline_stages


def test_publish_entry_mode_summary_formats_fallback_message(monkeypatch):
    published = []

    class DummyEventBus:
        def publish(self, topic, payload):
            published.append((topic, payload))

    monkeypatch.setattr(state_handlers, "EVENT_BUS", DummyEventBus())

    state_handlers._publish_entry_mode_summary(
        {"name": "씨아이에스"},
        "222080",
        entry_mode="fallback",
        latency_gate={
            "latency_state": "CAUTION",
            "decision": "ALLOW_FALLBACK",
            "signal_price": 12150,
            "latest_price": 12150,
            "orders": [
                {"tag": "fallback_scout", "qty": 1, "price": 12200, "tif": "IOC"},
                {"tag": "fallback_main", "qty": 44, "price": 12130, "tif": "DAY"},
            ],
        },
    )

    assert len(published) == 1
    topic, payload = published[0]
    assert topic == "TELEGRAM_BROADCAST"
    assert payload["audience"] == "ADMIN_ONLY"
    assert payload["parse_mode"] == "Markdown"
    assert "지연 대응 분할진입 활성화" in payload["message"]
    assert "지연 상태: `주의`" in payload["message"]
    assert "판정: `분할 진입 허용`" in payload["message"]
    assert "신호가 `12,150원` / 현재가 `12,150원`" in payload["message"]
    assert "탐색 주문: 1주 / 12,200원 / 즉시체결 우선" in payload["message"]
    assert "본 주문: 44주 / 12,130원 / 장중 유지" in payload["message"]


def test_execution_receipt_accumulates_fallback_bundle_fills(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None
    receipts.DB = _DummyDB()
    entry_state.TERMINAL_ENTRY_ORDERS.clear()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args

        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)
    monkeypatch.setattr(receipts, "_update_db_for_buy", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "send_sell_order_market", lambda *args, **kwargs: {"ord_no": "TP1"})

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "position_tag": "MIDDLE",
        "buy_price": 0,
        "buy_qty": 0,
        "entry_requested_qty": 3,
        "pending_entry_orders": [
            {"tag": "fallback_scout", "qty": 1, "ord_no": "O1", "status": "OPEN", "filled_qty": 0},
            {"tag": "fallback_main", "qty": 2, "ord_no": "O2", "status": "OPEN", "filled_qty": 0},
        ],
    }
    receipts.ACTIVE_TARGETS.append(stock)

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O1", "price": 10000, "qty": 1})
    assert stock["status"] == "HOLDING"
    assert stock["buy_qty"] == 1
    assert stock["pending_entry_orders"][0]["status"] == "FILLED"

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O2", "price": 9990, "qty": 2})
    assert stock["buy_qty"] == 3
    assert round(float(stock["buy_price"]), 4) == 9993.3333
    assert stock.get("pending_entry_orders") is None


def test_late_fill_after_cancel_matches_terminal_entry_order(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None
    receipts.DB = _DummyDB()
    receipts.KIWOOM_TOKEN = "token"
    entry_state.TERMINAL_ENTRY_ORDERS.clear()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args

        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)
    monkeypatch.setattr(receipts, "_update_db_for_buy", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts.kiwoom_utils, "get_target_price_up", lambda price, pct: 10150)
    monkeypatch.setattr(kiwoom_orders, "send_sell_order_market", lambda *args, **kwargs: {"ord_no": "TP1"})
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: {"return_code": "0"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "position_tag": "MIDDLE",
        "buy_price": 0,
        "buy_qty": 0,
        "entry_mode": "fallback",
        "entry_requested_qty": 3,
        "pending_entry_orders": [
            {"tag": "fallback_scout", "qty": 1, "ord_no": "O1", "status": "FILLED", "filled_qty": 1},
            {"tag": "fallback_main", "qty": 2, "ord_no": "O2", "status": "OPEN", "filled_qty": 0},
        ],
    }
    receipts.ACTIVE_TARGETS.append(stock)

    state_handlers._clear_pending_entry_meta(stock)
    assert stock.get("pending_entry_orders") is None
    assert entry_state.get_terminal_entry_order("O2") is not None

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O2", "price": 9990, "qty": 2})

    assert stock["buy_qty"] == 2
    assert stock["status"] == "HOLDING"


def test_order_notice_backfills_missing_entry_order_number(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None
    receipts.DB = _DummyDB()
    receipts.KIWOOM_TOKEN = "token"
    entry_state.TERMINAL_ENTRY_ORDERS.clear()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args

        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)
    monkeypatch.setattr(receipts, "_update_db_for_buy", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts.kiwoom_utils, "get_target_price_up", lambda price, pct: 10150)
    monkeypatch.setattr(kiwoom_orders, "send_sell_order_market", lambda *args, **kwargs: {"ord_no": "TP1"})

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "position_tag": "MIDDLE",
        "buy_price": 0,
        "buy_qty": 0,
        "entry_mode": "fallback",
        "entry_requested_qty": 3,
        "pending_entry_orders": [
            {"tag": "fallback_main", "qty": 3, "ord_no": "", "status": "OPEN", "filled_qty": 0},
        ],
    }
    receipts.ACTIVE_TARGETS.append(stock)

    receipts.handle_order_notice({"code": "123456", "type": "BUY", "order_no": "O1", "status": "접수"})

    assert stock["odno"] == "O1"
    assert stock["pending_entry_orders"][0]["ord_no"] == "O1"
    assert stock["pending_entry_orders"][0]["notice_status"] == "접수"

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O1", "price": 10000, "qty": 3})

    assert stock["buy_qty"] == 3
    assert stock["status"] == "HOLDING"
    assert stock.get("pending_entry_orders") is None


def test_stage_buy_order_submission_preserves_early_fill_state(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None
    receipts.DB = _DummyDB()
    receipts.KIWOOM_TOKEN = "token"
    entry_state.TERMINAL_ENTRY_ORDERS.clear()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args

        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)
    monkeypatch.setattr(receipts, "_update_db_for_buy", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts.kiwoom_utils, "get_target_price_up", lambda price, pct: 10150)
    monkeypatch.setattr(kiwoom_orders, "send_sell_order_market", lambda *args, **kwargs: {"ord_no": "TP1"})

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "MIDDLE",
        "buy_price": 0,
        "buy_qty": 0,
        "entry_mode": "fallback",
    }
    receipts.ACTIVE_TARGETS.append(stock)

    first_leg = [
        {"tag": "fallback_scout", "qty": 1, "ord_no": "O1", "status": "OPEN", "filled_qty": 0},
    ]
    state_handlers._stage_buy_order_submission(
        stock=stock,
        code="123456",
        curr_price=10000,
        requested_qty=3,
        msg="pending",
        entry_orders=first_leg,
    )

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O1", "price": 10000, "qty": 1})

    assert stock["buy_qty"] == 1
    assert stock["entry_filled_qty"] == 1

    all_legs = [
        {"tag": "fallback_scout", "qty": 1, "ord_no": "O1", "status": "OPEN", "filled_qty": 0},
        {"tag": "fallback_main", "qty": 2, "ord_no": "O2", "status": "OPEN", "filled_qty": 0},
    ]
    state_handlers._stage_buy_order_submission(
        stock=stock,
        code="123456",
        curr_price=10000,
        requested_qty=3,
        msg="pending",
        entry_orders=all_legs,
    )

    assert stock["status"] == "BUY_ORDERED"
    assert stock["entry_filled_qty"] == 1
    assert stock["pending_entry_orders"][0]["ord_no"] == "O1"
    assert stock["pending_entry_orders"][0]["filled_qty"] == 1
    assert stock["pending_entry_orders"][0]["status"] == "FILLED"


def test_scalp_preset_tp_refreshes_to_latest_filled_qty(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None
    receipts.DB = _DummyDB()
    entry_state.TERMINAL_ENTRY_ORDERS.clear()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args

        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)
    monkeypatch.setattr(receipts, "_update_db_for_buy", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts.kiwoom_utils, "get_target_price_up", lambda price, pct: 10150)

    cancel_calls = []
    sell_calls = []

    monkeypatch.setattr(
        kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs["orig_ord_no"]) or {"return_code": "0"},
    )
    monkeypatch.setattr(
        kiwoom_orders,
        "send_sell_order_market",
        lambda **kwargs: sell_calls.append(kwargs["qty"]) or {"ord_no": f"TP{len(sell_calls)}", "return_code": "0"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "position_tag": "MIDDLE",
        "buy_price": 0,
        "buy_qty": 0,
        "entry_requested_qty": 3,
        "pending_entry_orders": [
            {"tag": "fallback_scout", "qty": 1, "ord_no": "O1", "status": "OPEN", "filled_qty": 0},
            {"tag": "fallback_main", "qty": 2, "ord_no": "O2", "status": "OPEN", "filled_qty": 0},
        ],
    }
    receipts.ACTIVE_TARGETS.append(stock)

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O1", "price": 10000, "qty": 1})
    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "O2", "price": 9990, "qty": 2})

    assert sell_calls == [1, 3]
    assert cancel_calls == ["TP1"]
    assert stock["preset_tp_ord_no"] == "TP2"


def test_entry_submission_bundle_log_uses_actual_entry_mode(monkeypatch):
    logs = []
    monkeypatch.setattr(state_handlers, "log_info", lambda msg: logs.append(msg))

    stock = {"name": "TEST", "entry_mode": "fallback"}
    state_handlers._finalize_buy_order_submission(
        stock=stock,
        code="123456",
        curr_price=10000,
        requested_qty=5,
        msg="msg",
        entry_orders=[{"ord_no": "O1"}],
    )

    assert any("mode=fallback" in msg for msg in logs)


def test_reconcile_partial_fill_below_min_ratio_sends_exit_order(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True,
        SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT=0.20,
        SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE=0.10,
        SCALP_PARTIAL_FILL_MIN_RATIO_PRESET_TP=0.00,
    )
    state_handlers.KIWOOM_TOKEN = "token"

    monkeypatch.setattr(state_handlers, "_cancel_pending_entry_orders", lambda *args, **kwargs: "cancelled")
    sell_calls = []
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_sell_order_market",
        lambda **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )

    now = datetime.now().timestamp()
    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "status": "BUY_ORDERED",
        "buy_qty": 1,
        "entry_requested_qty": 10,
        "order_price": 10000,
        "order_time": now - 60,
        "pending_entry_orders": [{"ord_no": "B1", "status": "OPEN", "qty": 10, "filled_qty": 1}],
    }

    state_handlers._reconcile_pending_entry_orders(stock, "123456", "SCALPING")

    assert stock["status"] == "SELL_ORDERED"
    assert stock.get("pending_sell_msg", "").startswith("partial_fill_ratio_below_min")
    assert len(sell_calls) == 1
    assert sell_calls[0]["qty"] == 1


def test_reconcile_partial_fill_strong_override_uses_relaxed_ratio(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True,
        SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT=0.20,
        SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE=0.10,
    )

    monkeypatch.setattr(state_handlers, "_cancel_pending_entry_orders", lambda *args, **kwargs: "cancelled")
    sell_calls = []
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_sell_order_market",
        lambda **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )

    now = datetime.now().timestamp()
    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "status": "BUY_ORDERED",
        "buy_qty": 15,
        "entry_requested_qty": 100,
        "entry_dynamic_reason": "strong_absolute_override",
        "order_time": now - 60,
        "pending_entry_orders": [{"ord_no": "B1", "status": "OPEN", "qty": 100, "filled_qty": 15}],
    }

    state_handlers._reconcile_pending_entry_orders(stock, "123456", "SCALPING")

    assert stock["status"] == "HOLDING"
    assert sell_calls == []


def test_ioc_mapping_discards_price():
    tif, price = kiwoom_orders._resolve_buy_order_type("00", price=10000, tif="IOC")
    assert tif == "16"
    assert price == 0


def test_holding_sell_cancels_pending_entry_orders_first(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10000}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"

    calls = []

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: calls.append(("cancel", kwargs["orig_ord_no"])) or {"return_code": "0"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda **kwargs: calls.append(("sell", kwargs["qty"])) or {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 1,
        "pending_entry_orders": [
            {"tag": "fallback_main", "qty": 4, "ord_no": "B2", "status": "OPEN", "filled_qty": 0},
        ],
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 90},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert calls[0] == ("cancel", "B2")
    assert calls[1][0] == "sell"


def test_pause_flag_persists_until_cleared(tmp_path, monkeypatch):
    pause_flag = tmp_path / "pause.flag"
    monkeypatch.setattr(runtime_flags, "get_pause_flag_path", lambda: pause_flag)

    runtime_flags.set_trading_paused()
    assert runtime_flags.is_trading_paused() is True
    assert trade_pause_control.is_buy_side_paused() is True

    runtime_flags.clear_trading_paused()
    assert runtime_flags.is_trading_paused() is False
    assert trade_pause_control.is_buy_side_paused() is False


def test_holding_sell_still_works_when_paused(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = type(
        "DummyDB",
        (),
        {
            "get_session": lambda self: type(
                "Ctx",
                (),
                {
                    "__enter__": lambda s: type(
                        "Sess",
                        (),
                        {
                            "query": lambda *args, **kwargs: type(
                                "Q",
                                (),
                                {
                                    "filter_by": lambda *a, **k: type(
                                        "U", (), {"update": lambda *x, **y: None, "first": lambda *x, **y: None}
                                    )()
                                },
                            )()
                        },
                    )(),
                    "__exit__": lambda *args: None,
                },
            )()
        },
    )()

    called = {"sell": False, "gate": False}
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: True)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: called.__setitem__("sell", True) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: called.__setitem__("gate", True) or {"allowed": False, "reason": "buy_side_paused"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 90},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert called["sell"] is True
    assert called["gate"] is False
    assert stock["status"] == "SELL_ORDERED"


def test_pause_toggle_keeps_file_truth_when_event_publish_fails(tmp_path, monkeypatch):
    import src.notify.telegram_manager as telegram_manager

    pause_flag = tmp_path / "pause.flag"
    monkeypatch.setattr(runtime_flags, "get_pause_flag_path", lambda: pause_flag)
    monkeypatch.setattr(telegram_manager, "set_trading_paused", runtime_flags.set_trading_paused)
    monkeypatch.setattr(telegram_manager, "clear_trading_paused", runtime_flags.clear_trading_paused)
    monkeypatch.setattr(telegram_manager, "_publish_pause_state", lambda status: (_ for _ in ()).throw(RuntimeError("bus fail")))

    replies = []
    monkeypatch.setattr(telegram_manager.bot, "reply_to", lambda *args, **kwargs: replies.append((args, kwargs)))
    monkeypatch.setattr(telegram_manager.event_bus, "publish", lambda *args, **kwargs: None)
    monkeypatch.setattr(telegram_manager, "get_main_keyboard", lambda chat_id=None: None)

    class Chat:
        id = telegram_manager.ADMIN_ID

    class Message:
        chat = Chat()

    telegram_manager._handle_pause_toggle(Message(), paused=True)

    assert runtime_flags.is_trading_paused() is True
    assert replies


def test_non_admin_pause_request_is_rejected(monkeypatch):
    import src.notify.telegram_manager as telegram_manager

    replies = []
    monkeypatch.setattr(telegram_manager.bot, "reply_to", lambda *args, **kwargs: replies.append((args, kwargs)))
    monkeypatch.setattr(telegram_manager, "set_trading_paused", lambda: (_ for _ in ()).throw(AssertionError("should not be called")))

    class Chat:
        id = "not-admin"

    class Message:
        chat = Chat()

    telegram_manager.cmd_pause_buy_side(Message())

    assert replies
    assert "권한이 없습니다." in replies[0][0][1]


def test_s15_fast_track_pause_is_policy_blocked_not_failed(tmp_path, monkeypatch):
    import src.engine.sniper_s15_fast_track as s15

    pause_flag = tmp_path / "pause.flag"
    monkeypatch.setattr(runtime_flags, "get_pause_flag_path", lambda: pause_flag)
    runtime_flags.set_trading_paused()

    updates = []
    monkeypatch.setattr(s15, "update_s15_shadow_record", lambda shadow_id, **kwargs: updates.append(kwargs))
    monkeypatch.setattr(s15, "_unarm_s15_candidate", lambda code: None)
    monkeypatch.setattr(s15, "_pop_fast_state", lambda code: None)

    state = {
        "shadow_id": 99,
        "status": "WATCHING",
        "lock": type("DummyLock", (), {"__enter__": lambda self: None, "__exit__": lambda self, *args: None})(),
    }

    monkeypatch.setattr(s15, "_get_fast_state", lambda code: state)

    s15.execute_fast_track_scalp_v2("123456", "TEST", 10000)

    assert state["status"] == "BLOCKED"
    assert updates
    assert updates[-1]["status"] == "WATCHING"
    assert updates[-1]["position_tag"] == "S15_FAST_PAUSED"


def test_add_receipt_without_order_no_matches_single_pending_target(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._target = target
            self._args = args
        def start(self):
            if self._target:
                self._target(*self._args)

    monkeypatch.setattr(receipts, "_update_db_for_add", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)
    monkeypatch.setattr(receipts, "_refresh_scalp_preset_exit_order", lambda *args, **kwargs: None)

    target_stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 10000,
        "buy_qty": 10,
        "pending_add_order": True,
        "pending_add_type": "AVG_DOWN",
        "pending_add_qty": 5,
        "pending_add_ord_no": "A1",
        "add_count": 0,
        "avg_down_count": 0,
    }
    receipts.ACTIVE_TARGETS.append(target_stock)

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "", "price": 9500, "qty": 5}
    )

    assert target_stock["buy_qty"] == 15
    assert target_stock["add_count"] == 1


def test_add_execution_preserves_request_qty_on_final_fill(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None

    history_calls = []

    monkeypatch.setattr(receipts, "_update_db_for_add", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts, "record_add_history_event", lambda *args, **kwargs: history_calls.append(kwargs) or True)

    target_stock = {
        "id": 7,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 10000,
        "buy_qty": 10,
        "pending_add_order": True,
        "pending_add_type": "AVG_DOWN",
        "pending_add_qty": 5,
        "pending_add_ord_no": "A1",
        "add_count": 0,
        "avg_down_count": 0,
    }
    receipts.ACTIVE_TARGETS.append(target_stock)

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "A1", "price": 9500, "qty": 5}
    )

    assert history_calls
    assert history_calls[-1]["event_type"] == "EXECUTED"
    assert history_calls[-1]["request_qty"] == 5
    assert target_stock.get("pending_add_order") is None


def test_add_execution_keeps_original_buy_time(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None

    original_buy_time = datetime.now() - timedelta(minutes=15)

    monkeypatch.setattr(receipts, "_update_db_for_add", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts, "record_add_history_event", lambda *args, **kwargs: True)

    target_stock = {
        "id": 8,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 10000,
        "buy_qty": 10,
        "buy_time": original_buy_time,
        "pending_add_order": True,
        "pending_add_type": "PYRAMID",
        "pending_add_qty": 3,
        "pending_add_ord_no": "A2",
        "add_count": 0,
        "pyramid_count": 0,
    }
    receipts.ACTIVE_TARGETS.append(target_stock)

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "A2", "price": 10300, "qty": 3}
    )

    assert target_stock["buy_time"] == original_buy_time


def test_reconcile_scale_in_lock_auto_unlocks_when_account_matches():
    calls = []

    sniper_sync.record_add_history_event = lambda *args, **kwargs: calls.append(kwargs) or True
    sniper_sync.find_latest_open_add_order_no = lambda *args, **kwargs: "A1"
    sniper_sync.ACTIVE_TARGETS = [
        {
            "code": "123456",
            "scale_in_locked": True,
        }
    ]

    record = type(
        "Record",
        (),
        {
            "stock_code": "123456",
            "stock_name": "TEST",
            "buy_qty": 10,
            "buy_price": 10000.0,
            "scale_in_locked": True,
        },
    )()

    unlocked = sniper_sync._reconcile_scale_in_lock(record, real_qty=10, real_buy_uv=10000)

    assert unlocked is True
    assert record.scale_in_locked is False
    assert sniper_sync.ACTIVE_TARGETS[0]["scale_in_locked"] is False
    assert calls[-1]["event_type"] == "RECONCILED"
    assert calls[-1]["order_no"] == "A1"


def test_protection_price_triggers_sell_before_add(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10500}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}

    class DummyQuery:
        def filter_by(self, **kwargs):
            return self
        def first(self):
            return type("Record", (), {"buy_qty": 10})()
        def update(self, payload):
            return None

    class DummySession:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def query(self, *args, **kwargs):
            return DummyQuery()

    class DummyDB:
        def get_session(self):
            return DummySession()

    state_handlers.DB = DummyDB()

    called = {"gate": False, "sell": 0}

    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: called.__setitem__("gate", True) or {"allowed": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: called.__setitem__("sell", called["sell"] + 1) or {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 10,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 10000,
        "buy_qty": 10,
        "trailing_stop_price": 9900,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9800},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert called["sell"] == 1
    assert called["gate"] is False


def test_scalping_ai_early_exit_requires_depth_and_hold_guards(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    called = {"sell": False, "gate": False}

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: called.__setitem__("sell", True) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: called.__setitem__("gate", True) or {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 11,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=60),
        "rt_ai_prob": 0.29,
        "ai_low_score_loss_hits": 3,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.4, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert called["sell"] is False
    assert called["gate"] is True
    assert stock["status"] == "HOLDING"


def test_scalping_ai_early_exit_requires_consecutive_low_score_hits(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    monkeypatch.setattr(state_handlers, "datetime", datetime)
    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    sell_calls = []

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_my_inventory",
        lambda *args, **kwargs: ([], None),
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    base_stock = {
        "id": 12,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.29,
    }

    stock = dict(base_stock, ai_low_score_loss_hits=2)
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )
    assert sell_calls == []
    assert stock["status"] == "HOLDING"

    stock = dict(base_stock, ai_low_score_loss_hits=3)
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )
    assert len(sell_calls) == 1
    assert stock["status"] == "SELL_ORDERED"


def test_scalping_ai_exit_avgdown_toggle_off_keeps_original_exit(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    monkeypatch.setattr(state_handlers, "datetime", datetime)
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_AI_EXIT_AVGDOWN_ENABLED=False,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    sell_calls = []
    add_calls = []

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_process_scale_in_action",
        lambda *args, **kwargs: add_calls.append(kwargs) or {"rt_cd": "0"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 121,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.29,
        "ai_low_score_loss_hits": 3,
        "scalp_ai_exit_avgdown_done": False,
    }
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert len(sell_calls) == 1
    assert add_calls == []
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_ai_early_exit"


def test_scalping_ai_exit_avgdown_first_hit_success_resets_hits(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    monkeypatch.setattr(state_handlers, "datetime", datetime)
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_AI_EXIT_AVGDOWN_ENABLED=True,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    sell_calls = []
    add_calls = []

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_process_scale_in_action",
        lambda *args, **kwargs: add_calls.append(kwargs) or {"return_code": "0", "ord_no": "A1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 122,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.29,
        "ai_low_score_loss_hits": 3,
        "scalp_ai_exit_avgdown_done": False,
    }
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert len(add_calls) == 1
    assert sell_calls == []
    assert stock["status"] == "HOLDING"
    assert stock["ai_low_score_loss_hits"] == 0
    assert stock["scalp_ai_exit_avgdown_done"] is True


def test_scalping_ai_exit_avgdown_first_hit_failure_falls_back_to_sell(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    monkeypatch.setattr(state_handlers, "datetime", datetime)
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_AI_EXIT_AVGDOWN_ENABLED=True,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    sell_calls = []
    add_calls = []
    exit_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        if stage == "exit_signal":
            exit_logs.append(fields)

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_process_scale_in_action",
        lambda *args, **kwargs: add_calls.append(kwargs) or None,
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 123,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.29,
        "ai_low_score_loss_hits": 3,
        "scalp_ai_exit_avgdown_done": False,
    }
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert len(add_calls) == 1
    assert len(sell_calls) == 1
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_ai_early_exit"
    assert exit_logs and "fallback" in str(exit_logs[-1].get("reason", ""))


def test_scalping_ai_exit_avgdown_done_stock_sells_without_retry(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    monkeypatch.setattr(state_handlers, "datetime", datetime)
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_AI_EXIT_AVGDOWN_ENABLED=True,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    sell_calls = []
    add_calls = []
    exit_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        if stage == "exit_signal":
            exit_logs.append(fields)

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_process_scale_in_action",
        lambda *args, **kwargs: add_calls.append(kwargs) or {"return_code": "0", "ord_no": "A1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 124,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.29,
        "ai_low_score_loss_hits": 3,
        "scalp_ai_exit_avgdown_done": True,
    }
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert add_calls == []
    assert len(sell_calls) == 1
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_ai_early_exit"
    assert exit_logs and "[물타기 소진]" in str(exit_logs[-1].get("reason", ""))


def test_open_reclaim_ai_early_exit_uses_relaxed_consecutive_hits(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    monkeypatch.setattr(state_handlers, "datetime", datetime)
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS=3,
        SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS_OPEN_RECLAIM=4,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 101}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    sell_calls = []

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_my_inventory",
        lambda *args, **kwargs: ([], None),
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    base_stock = {
        "id": 13,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "OPEN_RECLAIM",
        "buy_price": 100,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.29,
    }

    stock = dict(base_stock, ai_low_score_loss_hits=3)
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )
    assert sell_calls == []
    assert stock["status"] == "HOLDING"

    stock = dict(base_stock, ai_low_score_loss_hits=4)
    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )
    assert len(sell_calls) == 1
    assert stock["status"] == "SELL_ORDERED"


def test_gatekeeper_cooldown_split_by_action():
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN=600,
        ML_GATEKEEPER_REJECT_COOLDOWN=7200,
        ML_GATEKEEPER_NEUTRAL_COOLDOWN=1800,
    )

    assert state_handlers._resolve_gatekeeper_reject_cooldown("눌림 대기") == (600, "pullback_wait")
    assert state_handlers._resolve_gatekeeper_reject_cooldown("전량 회피") == (7200, "hard_reject")
    assert state_handlers._resolve_gatekeeper_reject_cooldown("UNKNOWN") == (1800, "neutral_hold")


def test_holding_exit_signal_logs_exit_rule(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 13,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 98.0, "orderbook": {"bids": [{"price": 98, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    sent_logs = [fields for stage, fields in pipeline_logs if stage == "sell_order_sent"]

    assert stock["last_exit_rule"] == "scalp_soft_stop_pct"
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_soft_stop_pct"
    assert sent_logs and sent_logs[-1]["exit_rule"] == "scalp_soft_stop_pct"


def test_scalp_preset_tp_hard_stop_logs_exit_rule(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(state_handlers, "_confirm_cancel_or_reload_remaining", lambda *args, **kwargs: 10)
    monkeypatch.setattr(
        state_handlers,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "SIOC1"},
    )

    stock = {
        "id": 13,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
        "exit_mode": "SCALP_PRESET_TP",
        "preset_tp_ord_no": "TP1",
        "hard_stop_pct": -0.7,
        "protect_profit_pct": None,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.0, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    sent_logs = [fields for stage, fields in pipeline_logs if stage == "sell_order_sent"]

    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_preset_hard_stop_pct"
    assert stock["sell_ord_no"] == "SIOC1"
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_preset_hard_stop_pct"
    assert exit_logs[-1]["sell_reason_type"] == "LOSS"
    assert sent_logs and sent_logs[-1]["exit_rule"] == "scalp_preset_hard_stop_pct"
    assert sent_logs[-1]["order_type"] == "16"


def test_scalp_preset_tp_hard_stop_grace_delays_exit(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_PRESET_HARD_STOP_GRACE_SEC=0,
        SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC=35,
        SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT=-1.2,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10000}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []
    exit_calls = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(state_handlers, "_confirm_cancel_or_reload_remaining", lambda *args, **kwargs: 10)
    monkeypatch.setattr(
        state_handlers,
        "_send_exit_best_ioc",
        lambda *args, **kwargs: exit_calls.append(args) or {"return_code": "0", "ord_no": "SIOC1"},
    )

    stock = {
        "id": 13,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "entry_mode": "fallback",
        "buy_price": 10000,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
        "exit_mode": "SCALP_PRESET_TP",
        "preset_tp_ord_no": "TP1",
        "hard_stop_pct": -0.7,
        "hard_stop_grace_sec": 35,
        "hard_stop_emergency_pct": -1.2,
        "order_time": state_handlers.time.time() - 10,
        "protect_profit_pct": None,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9925, "orderbook": {"bids": [{"price": 9920, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "HOLDING"
    assert not exit_calls
    grace_logs = [fields for stage, fields in pipeline_logs if stage == "preset_hard_stop_grace"]
    assert grace_logs
    assert grace_logs[-1]["grace_sec"] == 35


def test_open_reclaim_never_green_exit_rule(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC=300,
        SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT=0.20,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100.15}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 13,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "OPEN_RECLAIM",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.30,
        "order_time": state_handlers.time.time() - 420,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_open_reclaim_never_green"
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_open_reclaim_never_green"


def test_scanner_fallback_never_green_exit_rule(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_SCANNER_FALLBACK_NEVER_GREEN_HOLD_SEC=420,
        SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SUSTAIN_SEC=120,
        SCALP_SCANNER_FALLBACK_NEVER_GREEN_PEAK_MAX_PCT=0.20,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100.10}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 13,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_mode": "fallback",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.40,
        "order_time": state_handlers.time.time() - 760,
        "near_ai_exit_started_at": state_handlers.time.time() - 180,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.25, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_scanner_fallback_never_green"
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_scanner_fallback_never_green"


def test_open_reclaim_retrace_exit_rule(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC=300,
        SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT=0.20,
        SCALP_OPEN_RECLAIM_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC=120,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100.60}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S2"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 17,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "OPEN_RECLAIM",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.32,
        "order_time": state_handlers.time.time() - 520,
        "open_reclaim_near_ai_exit_started_at": state_handlers.time.time() - 150,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_open_reclaim_retrace_exit"
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_open_reclaim_retrace_exit"


def test_scanner_fallback_retrace_exit_rule(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_SCANNER_FALLBACK_NEVER_GREEN_HOLD_SEC=420,
        SCALP_SCANNER_FALLBACK_NEVER_GREEN_PEAK_MAX_PCT=0.20,
        SCALP_SCANNER_FALLBACK_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC=150,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100.55}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S3"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 19,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_mode": "fallback",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.36,
        "order_time": state_handlers.time.time() - 780,
        "near_ai_exit_started_at": state_handlers.time.time() - 220,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_scanner_fallback_retrace_exit"
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_scanner_fallback_retrace_exit"


def test_common_hard_time_stop_stays_shadow_only(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=True,
        SCALP_COMMON_HARD_TIME_STOP_SHADOW_MINUTES=(3, 5, 7),
        SCALP_COMMON_HARD_TIME_STOP_SHADOW_MIN_LOSS_PCT=-0.7,
        SCALP_COMMON_HARD_TIME_STOP_SHADOW_MAX_PEAK_PCT=0.20,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100.10}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 21,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "entry_mode": "fallback",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.55,
        "order_time": state_handlers.time.time() - 400,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 99.2, "orderbook": {"bids": [{"price": 99, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "HOLDING"
    shadow_logs = [fields for stage, fields in pipeline_logs if stage == "hard_time_stop_shadow"]
    assert shadow_logs
    assert any(item.get("candidate") == "fallback_3m" for item in shadow_logs)


def test_holding_shadow_band_logs_review_for_near_safe_profit(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10080}
    state_handlers.LAST_AI_CALL_TIMES = {"123456": state_handlers.time.time() - 15}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    class DummyAI:
        def analyze_target(self, *args, **kwargs):
            return {"score": 70, "cache_hit": False}

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: [{"price": 10080, "volume": 1, "dir": "BUY"}],
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda *args, **kwargs: [{"Close": 10080}],
    )

    ws_data = {
        "curr": 10080,
        "fluctuation": 1.2,
        "v_pw": 120.0,
        "buy_ratio": 64.0,
        "ask_tot": 180000,
        "bid_tot": 190000,
        "net_bid_depth": 12000,
        "net_ask_depth": -8000,
        "buy_exec_volume": 9000,
        "sell_exec_volume": 5000,
        "tick_trade_value": 24000,
        "last_ws_update_ts": state_handlers.time.time(),
        "orderbook": {
            "asks": [{"price": 10090, "volume": 1200}],
            "bids": [{"price": 10080, "volume": 1500}],
        },
    }
    snapshot = state_handlers._build_holding_ai_fast_snapshot(ws_data)
    now_ts = state_handlers.time.time()
    current_profit_rate = state_handlers.calculate_net_profit_rate(10000, 10080)

    stock = {
        "id": 21,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "buy_time": datetime.now() - timedelta(seconds=240),
        "rt_ai_prob": 0.70,
        "last_ai_profit": current_profit_rate,
        "last_ai_market_signature": tuple(snapshot.values()),
        "last_ai_market_snapshot": snapshot,
        "last_ai_market_signature_at": now_ts - 5,
        "last_ai_reviewed_at": now_ts - 5,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        admin_id=1,
        market_regime="BULL",
        radar=object(),
        ai_engine=DummyAI(),
    )

    shadow_logs = [fields for stage, fields in pipeline_logs if stage == "ai_holding_shadow_band"]

    assert shadow_logs
    assert shadow_logs[-1]["action"] == "review"
    assert shadow_logs[-1]["near_safe_profit"] is True
    assert shadow_logs[-1]["near_ai_exit"] is False
