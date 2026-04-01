from dataclasses import replace
from datetime import datetime, timedelta

import src.engine.sniper_scale_in as scale_in
import src.engine.sniper_state_handlers as state_handlers
import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_sync as sniper_sync


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
    state_handlers.HIGHEST_PRICES = {"123456": 100}
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
        "buy_price": 100,
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
