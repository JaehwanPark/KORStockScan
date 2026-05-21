from dataclasses import replace
from datetime import datetime, timedelta, time as dt_time
import time

import src.engine.sniper_scale_in as scale_in
import src.engine.sniper_state_handlers as state_handlers
import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_entry_state as entry_state
import src.engine.sniper_sync as sniper_sync
import src.engine.trade_pause_control as trade_pause_control
import src.utils.runtime_flags as runtime_flags
from src.engine import kiwoom_orders
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.utils.constants import TRADING_RULES as CONFIG


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


def test_scalping_pyramid_signal():
    stock = {"pyramid_count": 0}
    result = scale_in.evaluate_scalping_pyramid(
        stock, profit_rate=2.0, peak_profit=2.2, is_new_high=True
    )
    assert result["should_add"] is True
    assert result["add_type"] == "PYRAMID"


def test_swing_pyramid_signal():
    result = scale_in.evaluate_swing_pyramid(
        {"strategy": "KOSPI_ML"},
        profit_rate=4.5,
        peak_profit=4.8,
    )

    assert result["should_add"] is True
    assert result["add_type"] == "PYRAMID"
    assert result["reason"] == "swing_pyramid_ok"


def test_swing_avg_down_simulation_signal():
    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(
        CONFIG,
        SWING_ENABLE_AVG_DOWN_SIMULATION=True,
        SWING_AVG_DOWN_MIN_LOSS_PCT=-3.0,
        SWING_AVG_DOWN_MAX_LOSS_PCT=-0.8,
        SWING_AVG_DOWN_MIN_HOLD_SEC=300,
    )
    try:
        result = scale_in.evaluate_swing_avg_down(
            {"strategy": "KOSPI_ML"},
            profit_rate=-1.2,
            peak_profit=0.4,
            current_ai_score=63,
            held_sec=900,
        )
    finally:
        scale_in.TRADING_RULES = original

    assert result["should_add"] is True
    assert result["add_type"] == "AVG_DOWN"
    assert result["reason"] == "swing_avg_down_ok"


def test_swing_dynamic_scale_in_qty_uncapped_for_simulation():
    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(
        CONFIG,
        SWING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        SWING_SCALE_IN_EFFECTIVE_QTY_CAP=0,
        MAX_POSITION_PCT=0.20,
    )
    try:
        details = scale_in.describe_dynamic_scale_in_qty(
            stock={"buy_qty": 10, "swing_live_order_dry_run": True},
            resolved_price=10_000,
            deposit=2_000_000,
            add_type="PYRAMID",
            strategy="KOSPI_ML",
            add_reason="swing_pyramid_ok",
            price_resolution={"allowed": True},
            action={"profit_rate": 4.5, "peak_profit": 4.8},
        )
    finally:
        scale_in.TRADING_RULES = original

    assert details["would_qty"] == 3
    assert details["effective_qty"] == 3
    assert details["qty"] == 3
    assert details["qty_reason"] == "swing_dynamic_allowed"
    assert details["effective_qty_cap"] == 0


def test_scalping_pyramid_count_is_attribution_only():
    from src.utils.constants import TRADING_RULES as CONFIG

    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(CONFIG, SCALPING_MAX_PYRAMID_COUNT=1)
    try:
        result = scale_in.evaluate_scalping_pyramid(
            {"pyramid_count": 5},
            profit_rate=2.0,
            peak_profit=2.1,
            is_new_high=True,
        )
        assert result["should_add"] is True
        assert result["reason"] == "scalping_pyramid_ok"
    finally:
        scale_in.TRADING_RULES = original


def test_avg_down_count_is_attribution_only_for_receipts():
    target_stock = {
        "avg_down_count": 3,
        "reversal_add_state": "STAGNATION",
        "reversal_add_profit_floor": -0.30,
        "reversal_add_ai_bottom": 42,
        "reversal_add_ai_history": [42, 44, 50, 58],
        "last_reversal_features": {
            "buy_pressure_10t": 60.0,
            "tick_acceleration_ratio": 1.05,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -2.0,
        },
    }
    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(
        CONFIG,
        REVERSAL_ADD_ENABLED=True,
        REVERSAL_ADD_PNL_MIN=-0.70,
        REVERSAL_ADD_PNL_MAX=-0.10,
        REVERSAL_ADD_MIN_HOLD_SEC=20,
        REVERSAL_ADD_MAX_HOLD_SEC=180,
        REVERSAL_ADD_MIN_AI_SCORE=60,
        REVERSAL_ADD_MIN_AI_RECOVERY_DELTA=15,
    )
    try:
        result = scale_in.evaluate_scalping_reversal_add(
            target_stock,
            profit_rate=-0.25,
            current_ai_score=65,
            held_sec=50,
        )
        assert result["should_add"] is True
        assert result["reason"] == "reversal_add_ok"
    finally:
        scale_in.TRADING_RULES = original


def test_calc_held_minutes_prefers_order_time_epoch():
    now = datetime.now().timestamp()

    held_min = scale_in._calc_held_minutes({"order_time": now - 180})

    assert 2.9 <= held_min <= 3.1


def test_calc_held_minutes_supports_datetime_buy_time():
    held_min = scale_in._calc_held_minutes({"buy_time": datetime.now() - timedelta(minutes=7)})

    assert 6.9 <= held_min <= 7.1


def test_calc_held_minutes_supports_time_only_buy_time():
    buy_time = (datetime.now() - timedelta(minutes=11)).time().replace(microsecond=0)

    held_min = scale_in._calc_held_minutes({"buy_time": buy_time})

    assert 10.8 <= held_min <= 11.2


def test_calc_held_minutes_returns_zero_for_unsupported_buy_time():
    held_min = scale_in._calc_held_minutes({"buy_time": "not-a-datetime"})

    assert held_min == 0.0


def test_resolve_holding_elapsed_sec_supports_time_only_buy_time():
    buy_time = (datetime.now() - timedelta(minutes=9)).time().replace(microsecond=0)

    held_sec = scale_in.resolve_holding_elapsed_sec({"buy_time": buy_time})

    assert 530 <= held_sec <= 550


def test_state_handler_resolve_holding_elapsed_sec_uses_shared_parser():
    buy_time = (datetime.now() - timedelta(minutes=6)).time().replace(microsecond=0)

    held_sec = state_handlers._resolve_holding_elapsed_sec({"buy_time": buy_time})

    assert 350 <= held_sec <= 370


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


def test_scalping_initial_entry_qty_cap_config_defaults_to_one_share():
    assert CONFIG.SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED is True
    assert CONFIG.SCALPING_INITIAL_ENTRY_MAX_QTY == 1
    assert CONFIG.SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED is True


def test_orderbook_stability_observation_logs_entry_pipeline(monkeypatch):
    logs = []

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        logs.append((stock, code, stage, fields))

    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", fake_log_entry_pipeline)

    state_handlers._log_orderbook_stability_observation(
        {"id": 1, "name": "TEST"},
        "123456",
        {
            "fr_10s": 6,
            "quote_age_p50_ms": 120.0,
            "quote_age_p90_ms": 410.0,
            "print_quote_alignment": 0.85,
            "unstable_quote_observed": True,
            "unstable_reasons": "fr_10s,quote_age_p90",
            "best_bid": 10_000,
            "best_ask": 10_010,
            "sample_trade_count": 3,
            "sample_quote_count": 5,
        },
    )

    assert logs[0][2] == "orderbook_stability_observed"
    assert logs[0][3]["unstable_quote_observed"] is True
    assert logs[0][3]["sample_trade_count"] == 3


def test_stat_action_decision_snapshot_logs_observe_only_with_rate_limit(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    logs = []
    now = {"ts": 1_000.0}

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        STAT_ACTION_DECISION_SNAPSHOT_ENABLED=True,
        STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC=30,
    )
    monkeypatch.setattr(state_handlers.time, "time", lambda: now["ts"])
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 1,
        "name": "TEST",
        "buy_qty": 2,
        "avg_down_count": 1,
        "pyramid_count": 0,
        "last_reversal_features": {
            "buy_pressure_10t": 62,
            "tick_acceleration_ratio": 1.1,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 3.0,
        },
    }
    ws_data = {
        "orderbook": {
            "asks": [{"price": 10010, "volume": 100}, {"price": 10020, "volume": 80}],
            "bids": [{"price": 10000, "volume": 120}, {"price": 9990, "volume": 90}],
        }
    }

    emitted = state_handlers._emit_stat_action_decision_snapshot(
        stock=stock,
        code="123456",
        strategy="SCALPING",
        ws_data=ws_data,
        chosen_action="hold_wait",
        eligible_actions=["hold_wait"],
        rejected_actions=["avg_down_wait:pnl_out_of_range"],
        profit_rate=-0.4,
        peak_profit=0.2,
        current_ai_score=64,
        held_sec=75,
        curr_price=10000,
        buy_price=10050,
        scale_in_gate={"allowed": True, "reason": "ok"},
        reason="unit_test",
    )
    assert emitted is True
    assert logs[0][0] == "stat_action_decision_snapshot"
    assert logs[0][1]["snapshot_observe_only"] is True
    assert logs[0][1]["chosen_action"] == "hold_wait"
    assert logs[0][1]["rejected_actions"] == "avg_down_wait:pnl_out_of_range"
    assert logs[0][1]["scale_in_gate_allowed"] is True
    assert "spread_bps" in logs[0][1]

    now["ts"] = 1_010.0
    emitted_again = state_handlers._emit_stat_action_decision_snapshot(
        stock=stock,
        code="123456",
        strategy="SCALPING",
        ws_data=ws_data,
        chosen_action="hold_wait",
    )
    assert emitted_again is False
    assert len(logs) == 1


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


def test_reversal_add_post_eval_starts_on_execution_receipt(monkeypatch):
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
        "buy_qty": 1,
        "pending_add_order": True,
        "pending_add_type": "AVG_DOWN",
        "pending_add_reason": "reversal_add_ok",
        "pending_add_qty": 1,
        "pending_add_ord_no": "123",
        "add_count": 0,
        "avg_down_count": 0,
        "reversal_add_state": "ADD_ARMED",
    }
    receipts.ACTIVE_TARGETS.append(target_stock)

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "123", "price": 9500, "qty": 1}
    )

    assert target_stock["reversal_add_state"] == "POST_ADD_EVAL"
    assert target_stock["reversal_add_executed_at"] > 0


def test_add_execution_rebases_highest_price_after_pyramid(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {"123456": 18000}
    receipts._get_fast_state = lambda code: None

    monkeypatch.setattr(receipts, "_update_db_for_add", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts, "record_add_history_event", lambda *args, **kwargs: True)
    monkeypatch.setattr(receipts, "_refresh_scalp_preset_exit_order", lambda *args, **kwargs: True)

    target_stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 17150,
        "buy_qty": 2,
        "pending_add_order": True,
        "pending_add_type": "PYRAMID",
        "pending_add_qty": 1,
        "pending_add_ord_no": "A1",
        "add_count": 0,
        "pyramid_count": 0,
    }
    receipts.ACTIVE_TARGETS.append(target_stock)

    receipts.handle_real_execution(
        {"code": "123456", "type": "BUY", "order_no": "A1", "price": 17460, "qty": 1}
    )

    assert round(target_stock["buy_price"], 4) == 17253.3333
    assert receipts.highest_prices["123456"] == 17460


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
        receipt_snapshot={
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
    assert receipts.event_bus.published[0][1]["message"].startswith("➕ 추가매수 체결")
    assert "누적 추가매수: 2회" in receipts.event_bus.published[0][1]["message"]


def test_execute_scale_in_order_failure_no_pending(monkeypatch):
    state_handlers.KIWOOM_TOKEN = "test"

    monkeypatch.setattr(
        state_handlers,
        "describe_scale_in_qty",
        lambda *args, **kwargs: {
            "qty": 1,
            "template_qty": 1,
            "cap_qty": 1,
            "remaining_budget": 10000,
            "floor_applied": False,
        },
    )
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


def test_execute_scalping_pyramid_blocks_wide_spread_price_guard(monkeypatch):
    state_handlers.KIWOOM_TOKEN = "test"
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALPING_PYRAMID_PRICE_GUARD_ENABLED=True,
        SCALPING_PYRAMID_MAX_SPREAD_BPS=80.0,
        SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS=60.0,
    )

    sent_orders = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "A1"},
    )

    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "last_reversal_features": {"curr_vs_micro_vwap_bp": 10.0},
    }
    action = {"add_type": "PYRAMID", "reason": "scalping_pyramid_ok"}
    ws_data = {"curr": 300_500, "best_bid": 299_000, "best_ask": 301_500}

    state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        action=action,
        admin_id=1,
    )

    assert sent_orders == []
    assert stock.get("pending_add_order") is None


def test_execute_scalping_pyramid_sends_resolved_best_bid_with_one_share_cap(monkeypatch):
    rules = replace(CONFIG, MAX_POSITION_PCT=1.0)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    history = []
    logs = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 10_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "P1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "record_add_history_event",
        lambda *args, **kwargs: history.append(kwargs) or True,
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "buy_qty": 10,
        "last_reversal_features": {
            "buy_pressure_10t": 75.0,
            "tick_acceleration_ratio": 0.8,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 10.0,
        },
    }
    action = {
        "add_type": "PYRAMID",
        "reason": "scalping_pyramid_ok",
        "current_ai_score": 75,
        "profit_rate": 2.0,
        "peak_profit": 2.1,
    }
    ws_data = {"curr": 10_000, "best_bid": 9_990, "best_ask": 10_000}

    state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        action=action,
        admin_id=1,
    )

    assert sent_orders == [("123456", 1, 9_990, "00")]
    assert history[0]["request_price"] == 9_990
    assert any(stage == "scale_in_price_resolved" for stage, _ in logs)
    assert any(stage == "scale_in_price_p2_observe" for stage, _ in logs)


def test_execute_swing_sim_scale_in_logs_automation_fields(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        SWING_SCALE_IN_EFFECTIVE_QTY_CAP=0,
        MAX_POSITION_PCT=0.20,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    logs = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 2_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "SHOULD_NOT_SEND"},
    )
    monkeypatch.setattr(state_handlers, "_is_swing_orderbook_micro_context_enabled", lambda strategy: False)
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 11,
        "name": "SWING",
        "strategy": "KOSPI_ML",
        "buy_qty": 10,
        "buy_price": 9_800,
        "swing_live_order_dry_run": True,
        "swing_intraday_probe": True,
        "probe_id": "probe-1",
        "probe_origin_stage": "blocked_gatekeeper_reject",
        "evidence_quality": "blocked_stage_intraday_probe",
    }
    action = {
        "add_type": "PYRAMID",
        "reason": "swing_pyramid_ok",
        "profit_rate": 4.5,
        "peak_profit": 4.8,
    }

    result = state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000},
        action=action,
        admin_id=None,
    )

    assert sent_orders == []
    assert result["actual_order_submitted"] is False
    sim_log = [fields for stage, fields in logs if stage == "swing_sim_scale_in_order_assumed_filled"][0]
    probe_log = [fields for stage, fields in logs if stage == "swing_probe_scale_in_order_assumed_filled"][0]
    for fields in (sim_log, probe_log):
        assert fields["actual_order_submitted"] is False
        assert fields["broker_order_forbidden"] is True
        assert fields["add_type"] == "PYRAMID"
        assert fields["scale_in_type"] == "PYRAMID"
        assert fields["add_trigger"] == "swing_pyramid_ok"
        assert fields["price_policy"] == "market"
        assert fields["post_add_outcome"] == "pending_followup"
        assert fields["scale_in_ratio"] == "0.3000"
        assert fields["would_qty"] == 3
        assert fields["effective_qty"] == 3


def test_execute_swing_real_canary_pyramid_submits_one_share_limit(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_SCALE_IN_REAL_CANARY_ENABLED=True,
        SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS="PYRAMID,AVG_DOWN",
        SWING_SCALE_IN_REAL_CANARY_MAX_QTY=1,
        SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY=1,
        SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION=1,
        SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW=100_000,
        SWING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        MAX_POSITION_PCT=0.20,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    logs = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 2_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "REALADD1"},
    )
    monkeypatch.setattr(state_handlers, "record_add_history_event", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "_build_live_orderbook_micro_context",
        lambda code, curr_price: {
            "ready": True,
            "micro_state": "bullish",
            "observer_healthy": True,
            "sample_quote_count": 10,
            "snapshot_age_ms": 50,
        },
    )

    stock = {
        "id": 12,
        "name": "SWING",
        "strategy": "KOSPI_ML",
        "status": "HOLDING",
        "buy_qty": 10,
        "buy_price": 9_800,
        "actual_order_submitted": True,
        "cohort": "swing_one_share_real_canary",
    }
    action = {"add_type": "PYRAMID", "reason": "swing_pyramid_ok", "profit_rate": 4.5, "peak_profit": 4.8}
    ws_data = {
        "curr": 10_000,
        "last_ws_update_ts": time.time(),
        "orderbook": {"bids": [{"price": 9_990}], "asks": [{"price": 10_010}]},
    }

    result = state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        action=action,
        admin_id=1,
    )

    assert sent_orders == [("123456", 1, 9_990, "00")]
    assert result["ord_no"] == "REALADD1"
    assert stock["pending_add_qty"] == 1
    assert stock["swing_scale_in_real_canary"] is True
    submitted = [fields for stage, fields in logs if stage == "swing_scale_in_real_canary_order_submitted"][0]
    assert submitted["actual_order_submitted"] is True
    assert submitted["would_qty"] == 3
    assert submitted["effective_qty"] == 3
    assert submitted["real_canary_actual_qty"] == 1
    assert submitted["real_canary_qty_cap"] == 1
    assert submitted["qty_cap_reason"] == "swing_scale_in_real_canary_phase0"


def test_execute_swing_real_canary_blocks_bearish_micro(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_SCALE_IN_REAL_CANARY_ENABLED=True,
        SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS="PYRAMID,AVG_DOWN",
        MAX_POSITION_PCT=0.20,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    logs = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 2_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "SHOULD_NOT_SEND"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "_build_live_orderbook_micro_context",
        lambda code, curr_price: {
            "ready": True,
            "micro_state": "bearish",
            "observer_healthy": True,
            "sample_quote_count": 10,
            "snapshot_age_ms": 50,
        },
    )

    stock = {
        "id": 13,
        "name": "SWING",
        "strategy": "KOSPI_ML",
        "status": "HOLDING",
        "buy_qty": 10,
        "buy_price": 9_800,
        "actual_order_submitted": True,
        "cohort": "swing_one_share_real_canary",
    }

    result = state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": time.time(),
            "orderbook": {"bids": [{"price": 9_990}], "asks": [{"price": 10_010}]},
        },
        action={"add_type": "PYRAMID", "reason": "swing_pyramid_ok", "profit_rate": 4.5, "peak_profit": 4.8},
        admin_id=1,
    )

    assert result is None
    assert sent_orders == []
    blocked = [fields for stage, fields in logs if stage == "swing_scale_in_real_canary_blocked"][0]
    assert blocked["block_reason"] == "ofi_qi_risk_bearish"
    assert blocked["actual_order_submitted"] is False


def test_evaluate_swing_one_share_real_canary_caps_initial_qty(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ONE_SHARE_REAL_CANARY_ENABLED=True,
        SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES="123456",
        SWING_ONE_SHARE_REAL_CANARY_MAX_QTY=5,
        SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY=1,
        SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS=3,
        SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW=300_000,
        SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT=True,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])

    result = state_handlers._evaluate_swing_one_share_real_canary(
        {"strategy": "KOSPI_ML", "status": "WATCHING"},
        "123456",
        request_qty=5,
        request_price=10_000,
        ws_data={"curr": 10_000},
        submit_revalidation_fields={},
        swing_entry_micro_fields={"swing_micro_advice": "SUPPORT_ENTRY"},
    )

    assert result["allowed"] is True
    assert result["qty"] == 1
    assert result["reason"] == "swing_one_share_real_canary_allowed"
    assert result["fields"]["actual_order_submitted"] is True
    assert result["fields"]["real_canary_actual_qty"] == 1
    assert result["fields"]["qty_cap_reason"] == "swing_one_share_real_canary_phase0"


def test_evaluate_swing_one_share_real_canary_blocks_unapproved_code(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_ONE_SHARE_REAL_CANARY_ENABLED=True,
        SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES="123456",
        SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT=True,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])

    result = state_handlers._evaluate_swing_one_share_real_canary(
        {"strategy": "KOSPI_ML", "status": "WATCHING"},
        "654321",
        request_qty=1,
        request_price=10_000,
        ws_data={"curr": 10_000},
        submit_revalidation_fields={},
        swing_entry_micro_fields={},
    )

    assert result["allowed"] is False
    assert result["reason"] == "code_not_approved"
    assert result["fields"]["allowed_codes"] == "123456"


def test_execute_scalping_reversal_add_uses_resolved_price_not_curr(monkeypatch):
    rules = replace(CONFIG, MAX_POSITION_PCT=1.0)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 10_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "R1"},
    )

    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "buy_qty": 3,
        "hard_stop_price": 9_000,
        "last_reversal_features": {"curr_vs_micro_vwap_bp": 0.0},
    }
    action = {"add_type": "AVG_DOWN", "reason": "reversal_add_ok"}
    ws_data = {"curr": 10_000, "best_bid": 9_980, "best_ask": 10_000}

    state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        action=action,
        admin_id=1,
    )

    assert sent_orders == [("123456", 1, 9_980, "00")]


def test_dynamic_scale_in_qty_blocks_weak_pyramid_evidence(monkeypatch):
    rules = replace(CONFIG, MAX_POSITION_PCT=1.0)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 10_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "P2"},
    )

    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "buy_qty": 10,
        "last_reversal_features": {
            "buy_pressure_10t": 50.0,
            "tick_acceleration_ratio": 0.0,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 10.0,
        },
    }
    action = {
        "add_type": "PYRAMID",
        "reason": "scalping_pyramid_ok",
        "current_ai_score": 75,
        "profit_rate": 2.0,
        "peak_profit": 2.1,
    }

    state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000, "best_bid": 9_990, "best_ask": 10_000},
        action=action,
        admin_id=1,
    )

    assert sent_orders == []
    assert stock.get("pending_add_order") is None


def test_p2_observe_skip_does_not_change_live_order(monkeypatch):
    rules = replace(CONFIG, MAX_POSITION_PCT=1.0)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    state_handlers.KIWOOM_TOKEN = "test"

    sent_orders = []
    logs = []
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 10_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "P3"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 1,
        "name": "TEST",
        "strategy": "SCALPING",
        "buy_qty": 10,
        "last_reversal_features": {
            "buy_pressure_10t": 70.0,
            "tick_acceleration_ratio": 0.7,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 5.0,
        },
    }
    action = {
        "add_type": "PYRAMID",
        "reason": "scalping_pyramid_ok",
        "current_ai_score": 72,
        "profit_rate": 1.8,
        "peak_profit": 1.8,
        "p2_observe_action": "SKIP",
    }

    state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000, "best_bid": 9_990, "best_ask": 10_000},
        action=action,
        admin_id=1,
    )

    assert sent_orders == [("123456", 1, 9_990, "00")]
    p2_logs = [fields for stage, fields in logs if stage == "scale_in_price_p2_observe"]
    assert p2_logs
    assert p2_logs[0]["live_runtime_effect"] is False
    assert p2_logs[0]["action"] == "SKIP"
    assert "orderbook_micro_ready" in p2_logs[0]
    assert "orderbook_micro_state" in p2_logs[0]
    assert "orderbook_micro_reason" in p2_logs[0]
    assert "orderbook_micro_snapshot_age_ms" in p2_logs[0]
    assert "orderbook_micro_observer_healthy" in p2_logs[0]


def test_calc_scale_in_qty_scalping_reversal_add_uses_configured_ratio():
    from src.utils.constants import TRADING_RULES as CONFIG

    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(CONFIG, MAX_POSITION_PCT=1.0, REVERSAL_ADD_SIZE_RATIO=0.33)
    try:
        qty = scale_in.calc_scale_in_qty(
            stock={"buy_qty": 10},
            curr_price=10000,
            deposit=10_000_000,
            add_type="AVG_DOWN",
            strategy="SCALPING",
            add_reason="reversal_add_ok",
        )
        assert qty == 3
    finally:
        scale_in.TRADING_RULES = original


def test_describe_scale_in_qty_stage1_can_still_be_disabled_by_flag():
    from src.utils.constants import TRADING_RULES as CONFIG

    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(
        CONFIG,
        MAX_POSITION_PCT=1.0,
        SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED=False,
    )
    try:
        details = scale_in.describe_scale_in_qty(
            stock={"buy_qty": 1},
            curr_price=10000,
            deposit=10_000_000,
            add_type="PYRAMID",
            strategy="SCALPING",
        )
        assert details["qty"] == 0
        assert details["template_qty"] == 0
        assert details["cap_qty"] >= 1
        assert details["floor_applied"] is False
    finally:
        scale_in.TRADING_RULES = original


def test_describe_scale_in_qty_stage1_applies_one_share_floor_when_enabled():
    from src.utils.constants import TRADING_RULES as CONFIG

    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(
        CONFIG,
        MAX_POSITION_PCT=1.0,
        SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED=True,
    )
    try:
        details = scale_in.describe_scale_in_qty(
            stock={"buy_qty": 1},
            curr_price=10000,
            deposit=10_000_000,
            add_type="PYRAMID",
            strategy="SCALPING",
        )
        assert details["qty"] == 1
        assert details["template_qty"] == 1
        assert details["cap_qty"] >= 1
        assert details["floor_applied"] is True
    finally:
        scale_in.TRADING_RULES = original


def test_describe_scale_in_qty_stage1_default_prevents_one_share_pyramid_zero_qty():
    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(CONFIG, MAX_POSITION_PCT=1.0)
    try:
        details = scale_in.describe_scale_in_qty(
            stock={"buy_qty": 1},
            curr_price=19_320,
            deposit=9_645_069,
            add_type="PYRAMID",
            strategy="SCALPING",
        )
        assert details["qty"] == 1
        assert details["template_qty"] == 1
        assert details["cap_qty"] >= 1
        assert details["floor_applied"] is True
    finally:
        scale_in.TRADING_RULES = original


def test_describe_scale_in_qty_applies_reversal_add_floor_for_two_share_cap():
    from src.utils.constants import TRADING_RULES as CONFIG
    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(
        CONFIG,
        MAX_POSITION_PCT=1.0,
        REVERSAL_ADD_SIZE_RATIO=0.33,
        REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=True,
    )
    try:
        details = scale_in.describe_scale_in_qty(
            {"buy_qty": 2},
            curr_price=10_000,
            deposit=1_000_000,
            add_type="AVG_DOWN",
            strategy="SCALPING",
            add_reason="reversal_add_ok",
        )
        assert details["qty"] == 1
        assert details["floor_applied"] is True
    finally:
        scale_in.TRADING_RULES = original


def test_describe_scale_in_qty_uses_non_scalping_pyramid_ratio():
    from src.utils.constants import TRADING_RULES as CONFIG

    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(CONFIG, MAX_POSITION_PCT=1.0)
    try:
        details = scale_in.describe_scale_in_qty(
            {"buy_qty": 10},
            curr_price=10_000,
            deposit=1_000_000,
            add_type="PYRAMID",
            strategy="KOSPI_ML",
        )
        assert details["qty"] == 3
        assert details["template_qty"] == 3
        assert details["floor_applied"] is False
    finally:
        scale_in.TRADING_RULES = original


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

    assert called["gate"] is True
    assert called["eval"] is True
    assert called["add"] is False


def test_recent_pyramid_add_suppresses_scalp_trailing(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class _RulesProxy:
        def __getattr__(self, name):
            overrides = {
                "SCALE_IN_REQUIRE_HISTORY_TABLE": False,
                "SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC": 180,
                "SCALP_SAFE_PROFIT": 0.5,
                "SCALP_TRAILING_LIMIT_WEAK": 0.4,
                "SCALP_TRAILING_LIMIT_STRONG": 0.8,
            }
            if name in overrides:
                return overrides[name]
            return getattr(CONFIG, name)

    now_ts = 1_000_000.0
    state_handlers.TRADING_RULES = _RulesProxy()
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 17460}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = None

    calls = {"sell": 0, "stages": []}
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_no_add"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: calls.__setitem__("sell", calls["sell"] + 1) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: calls["stages"].append((stage, fields)),
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 17253.3333,
        "buy_qty": 3,
        "last_add_type": "PYRAMID",
        "last_add_time": now_ts - 90,
        "rt_ai_prob": 0.68,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 17380},
        admin_id=1,
        market_regime="BULL",
        now_ts=now_ts,
        now_dt=datetime(2026, 4, 30, 12, 45, 57),
        radar=None,
        ai_engine=None,
    )

    assert calls["sell"] == 0
    assert any(stage == "pyramid_post_add_trailing_grace" for stage, _ in calls["stages"])


def test_protect_trailing_uses_smoothing_not_single_tick(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class _RulesProxy:
        def __getattr__(self, name):
            overrides = {
                "SCALE_IN_REQUIRE_HISTORY_TABLE": False,
                "SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC": 180,
                "SCALP_PROTECT_TRAILING_SMOOTH_ENABLED": True,
                "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES": 3,
                "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC": 8,
                "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT": 0.80,
                "SCALP_PROTECT_TRAILING_EMERGENCY_PCT": -2.0,
            }
            if name in overrides:
                return overrides[name]
            return getattr(CONFIG, name)

    now_ts = 1_000_000.0
    state_handlers.TRADING_RULES = _RulesProxy()
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 17460}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = None

    calls = {"sell": 0, "stages": []}
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_no_add"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: calls.__setitem__("sell", calls["sell"] + 1) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: calls["stages"].append((stage, fields)),
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 17253.3333,
        "buy_qty": 3,
        "trailing_stop_price": 17305,
        "last_add_type": "PYRAMID",
        "last_add_time": now_ts - 240,
        "rt_ai_prob": 0.68,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 17300},
        admin_id=1,
        market_regime="BULL",
        now_ts=now_ts,
        now_dt=datetime(2026, 4, 30, 12, 45, 57),
        radar=None,
        ai_engine=None,
    )

    assert calls["sell"] == 0
    assert any(stage == "protect_trailing_smooth_hold" for stage, _ in calls["stages"])


def test_pyramid_post_add_grace_prefers_older_db_timestamp_when_runtime_time_is_refreshed():
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC=180,
    )
    now_ts = 1_000_000.0
    stock = {
        "last_add_type": "PYRAMID",
        "last_add_time": now_ts,
        "last_add_at": datetime.fromtimestamp(now_ts - 3600),
    }

    active, elapsed_sec, grace_sec = state_handlers._pyramid_post_add_trailing_grace(stock, now_ts)

    assert active is False
    assert elapsed_sec == 3600
    assert grace_sec == 180


def test_pyramid_post_add_grace_uses_history_when_runtime_timestamps_are_refreshed(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC=180,
    )
    now_ts = 1_000_000.0
    monkeypatch.setattr(
        state_handlers,
        "_lookup_latest_add_executed_timestamp",
        lambda stock: now_ts - 3600,
    )
    stock = {
        "id": 1,
        "last_add_type": "PYRAMID",
        "add_count": 2,
        "pyramid_count": 2,
        "last_add_time": now_ts,
        "last_add_at": datetime.fromtimestamp(now_ts),
    }

    active, elapsed_sec, grace_sec = state_handlers._pyramid_post_add_trailing_grace(stock, now_ts)

    assert active is False
    assert elapsed_sec == 3600
    assert grace_sec == 180


def test_protect_trailing_confirms_sustained_smoothed_break(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_PROTECT_TRAILING_SMOOTH_ENABLED=True,
        SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES=3,
        SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC=8,
        SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO=0.67,
        SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT=0.80,
        SCALP_PROTECT_TRAILING_EMERGENCY_PCT=-2.0,
    )
    now_ts = 1_000_000.0
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = None

    calls = {"sell": 0}
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_no_add"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: calls.__setitem__("sell", calls["sell"] + 1) or {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 3,
        "trailing_stop_price": 10000,
        "rt_ai_prob": 0.68,
        "holding_price_samples": [
            {"ts": now_ts - 12, "price": 9900},
            {"ts": now_ts - 8, "price": 9910},
        ],
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9900},
        admin_id=1,
        market_regime="BULL",
        now_ts=now_ts,
        now_dt=datetime(2026, 4, 30, 12, 45, 57),
        radar=None,
        ai_engine=None,
    )

    assert calls["sell"] == 1


def test_holding_flow_override_candidate_clears_when_exit_candidate_resolves(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    now_ts = 1_000_000.0
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10_050}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = None

    calls = {"sell": 0, "stages": []}
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_no_add"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: calls.__setitem__("sell", calls["sell"] + 1) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: calls["stages"].append((stage, fields)),
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "rt_ai_prob": 0.68,
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": now_ts - 240,
        "holding_flow_override_candidate_profit": -1.80,
        "holding_flow_override_last_review_at": now_ts - 210,
        "holding_flow_override_last_action": "HOLD",
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_050},
        admin_id=1,
        market_regime="BULL",
        now_ts=now_ts,
        now_dt=datetime(2026, 5, 4, 10, 5, 0),
        radar=None,
        ai_engine=None,
    )

    assert calls["sell"] == 0
    assert "holding_flow_override_candidate_key" not in stock
    assert any(stage == "holding_flow_override_candidate_cleared" for stage, _ in calls["stages"])


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
    assert stock["last_add_cancel_at"] == 100.0
    assert stock["last_add_cancel_reason"] == "timeout"

    monkeypatch.setattr(state_handlers.time, "time", lambda: 101.0)
    result = state_handlers.can_consider_scale_in(
        stock=stock,
        code="123456",
        ws_data={"curr": 10000},
        strategy="SCALPING",
        market_regime="BULL",
    )

    assert result["allowed"] is False
    assert result["reason"] == "scale_in_cancel_cooldown"


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


def test_scale_in_guard_ignores_nat_like_last_add_at(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class _FakeNaT:
        def __bool__(self):
            return True

        def __str__(self):
            return "NaT"

        def timestamp(self):
            raise TypeError("NaTType does not support timestamp")

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        ENABLE_SCALE_IN=True,
        REVERSAL_ADD_ENABLED=True,
        SCALPING_MAX_PYRAMID_COUNT=1,
        ADD_JUDGMENT_LOCK_SEC=0,
        SCALE_IN_COOLDOWN_SEC=180,
        MAX_POSITION_PCT=0.30,
    )
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers.time, "time", lambda: 1_000.0)
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 5, 1, 10, 0, 0)

    monkeypatch.setattr(state_handlers, "datetime", FixedDateTime)

    stock = {
        "name": "TEST",
        "code": "489790",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "last_add_at": _FakeNaT(),
    }

    result = state_handlers.can_consider_scale_in(
        stock=stock,
        code="489790",
        ws_data={"curr": 10000},
        strategy="SCALPING",
        market_regime="BULL",
    )

    assert result["allowed"] is True
    assert result["reason"] == "ok"


def test_scale_in_guard_uses_pyramid_enable_flag_not_count_limit(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2026, 4, 30, 10, 0, 0)

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        ENABLE_SCALE_IN=True,
        REVERSAL_ADD_ENABLED=False,
        SCALPING_ENABLE_PYRAMID=True,
        SCALPING_MAX_PYRAMID_COUNT=0,
        ADD_JUDGMENT_LOCK_SEC=0,
        SCALE_IN_COOLDOWN_SEC=0,
        MAX_POSITION_PCT=1.0,
    )
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "datetime", FixedDateTime)

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

    assert result["allowed"] is True
    assert result["reason"] == "ok"


def test_scale_in_guard_allows_reversal_add_without_pyramid(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2026, 4, 30, 10, 0, 0)

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        ENABLE_SCALE_IN=True,
        REVERSAL_ADD_ENABLED=True,
        SCALPING_ENABLE_PYRAMID=False,
        ADD_JUDGMENT_LOCK_SEC=0,
        SCALE_IN_COOLDOWN_SEC=0,
        MAX_POSITION_PCT=1.0,
    )
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "datetime", FixedDateTime)

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

    assert result["allowed"] is True
    assert result["reason"] == "ok"


def test_scale_in_guard_blocks_when_pyramid_and_reversal_add_disabled(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2026, 4, 30, 10, 0, 0)

    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        ENABLE_SCALE_IN=True,
        REVERSAL_ADD_ENABLED=False,
        SCALPING_ENABLE_PYRAMID=False,
        ADD_JUDGMENT_LOCK_SEC=0,
        SCALE_IN_COOLDOWN_SEC=0,
        MAX_POSITION_PCT=1.0,
    )
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "datetime", FixedDateTime)

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
    assert result["reason"] == "scalping_scale_in_disabled"


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


def test_watching_state_rejects_deprecated_fallback_bundle(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 2, 10, 0, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=False,
    )
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
            "allowed": False,
            "mode": "reject",
            "decision": "REJECT_MARKET_CONDITION",
            "reason": "latency_fallback_deprecated",
            "latency_state": "CAUTION",
            "orders": [],
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

    assert stock.get("status") != "BUY_ORDERED"
    assert sent_orders == []
    assert stock.get("pending_entry_orders") is None
    assert stock.get("entry_requested_qty") is None


def test_watching_state_logs_latency_entry_price_guard(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 3, 10, 0, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=False,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {"123456": FixedDateTime.now().timestamp() - 10}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"

    class DummyRadar:
        def get_smart_target_price(self, curr_price, **kwargs):
            return curr_price, 0.0

    class DummyAI:
        def analyze_target(self, *args, **kwargs):
            return {"action": "BUY", "score": 90, "reason": "confirmed"}

    class DummyEventBus:
        def publish(self, *args, **kwargs):
            return None

    state_handlers.EVENT_BUS = DummyEventBus()

    logs = []
    sent_orders = []

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        logs.append((stage, fields))

    def fake_send_buy_order(code, qty, price, order_type_code, *args, **kwargs):
        sent_orders.append((qty, price, order_type_code, kwargs.get("tif")))
        return {"return_code": "0", "ord_no": "O1"}

    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", fake_log_entry_pipeline)
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "_publish_buy_signal_submission_notice", lambda *args, **kwargs: None)
    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", lambda ws_data: {"enabled": True, "allowed": True, "reason": "ok"})
    monkeypatch.setattr(state_handlers, "arm_big_bite_if_triggered", lambda **kwargs: (False, {}))
    monkeypatch.setattr(state_handlers, "confirm_big_bite_follow_through", lambda **kwargs: (True, {}))
    monkeypatch.setattr(state_handlers, "build_tick_data_from_ws", lambda ws_data: {})
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [1])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [1])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_capacity",
        lambda *args, **kwargs: (50_000, 47_500, 5, 0.95),
    )
    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", fake_send_buy_order)
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": True,
            "mode": "normal",
            "decision": "ALLOW_NORMAL",
            "reason": "latency_quote_fresh_composite_normal_override",
            "latency_state": "DANGER",
            "orders": [
                {
                    "tag": "normal",
                    "qty": 2,
                    "price": 9_990,
                    "order_type": "LIMIT",
                    "tif": "DAY",
                }
            ],
            "signal_price": 10_000,
            "latest_price": 10_020,
            "computed_allowed_slippage": 20,
            "ws_age_ms": 820,
            "ws_jitter_ms": 380,
            "spread_ratio": 0.0062,
            "quote_stale": False,
            "latency_danger_reasons": "ws_age_too_high,ws_jitter_too_high",
            "latency_canary_applied": True,
            "latency_canary_reason": "quote_fresh_composite_canary_applied",
            "entry_price_guard": "latency_danger_override_defensive",
            "entry_price_defensive_ticks": 3,
            "normal_defensive_order_price": 10_010,
            "latency_guarded_order_price": 9_990,
            "counterfactual_order_price_1tick": 10_010,
            "order_price": 9_990,
        },
    )

    stock = {"id": 1, "name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.9, "rt_ai_prob": 0.9}
    state_handlers.handle_watching_state(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 10_020,
            "v_pw": 120.0,
            "ask_tot": 20_000,
            "bid_tot": 20_000,
            "open": 10_000,
            "fluctuation": 0.5,
            "orderbook": {
                "asks": [{"price": 10_020, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=DummyAI(),
    )

    assert sent_orders == [(2, 9_990, "00", "DAY")]
    by_stage = {stage: fields for stage, fields in logs}
    assert by_stage["latency_pass"]["entry_price_guard"] == "latency_danger_override_defensive"
    assert by_stage["latency_pass"]["entry_price_defensive_ticks"] == 3
    assert by_stage["latency_pass"]["counterfactual_order_price_1tick"] == 10_010
    assert by_stage["order_leg_request"]["price"] == 9_990
    assert by_stage["order_leg_request"]["entry_price_defensive_ticks"] == 3
    assert by_stage["order_leg_request"]["submitted_order_price"] == 9_990
    assert by_stage["order_leg_request"]["best_bid_at_submit"] == 10_000
    assert by_stage["order_leg_request"]["best_ask_at_submit"] == 10_020
    assert by_stage["order_leg_request"]["price_below_bid_bps"] == 10
    assert by_stage["order_leg_request"]["resolution_reason"] == "defensive_order_price"
    assert by_stage["order_bundle_submitted"]["order_price"] == 9_990
    assert by_stage["order_bundle_submitted"]["submitted_order_price"] == 9_990


def test_watching_state_blocks_deep_below_bid_pre_submit_price(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 29, 10, 0, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=False,
        SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True,
        SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {"001440": FixedDateTime.now().timestamp() - 10}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"

    class DummyRadar:
        def get_smart_target_price(self, curr_price, **kwargs):
            return 48_800, 0.0

    class DummyAI:
        def analyze_target(self, *args, **kwargs):
            return {"action": "BUY", "score": 90, "reason": "confirmed"}

    class DummyEventBus:
        def publish(self, *args, **kwargs):
            return None

    state_handlers.EVENT_BUS = DummyEventBus()

    logs = []
    sent_orders = []

    def fake_log_entry_pipeline(stock, code, stage, **fields):
        logs.append((stage, fields))

    def fake_send_buy_order(code, qty, price, order_type_code, *args, **kwargs):
        sent_orders.append((qty, price, order_type_code, kwargs.get("tif")))
        return {"return_code": "0", "ord_no": "O1"}

    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", fake_log_entry_pipeline)
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "_publish_buy_signal_submission_notice", lambda *args, **kwargs: None)
    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", lambda ws_data: {"enabled": True, "allowed": True, "reason": "ok"})
    monkeypatch.setattr(state_handlers, "arm_big_bite_if_triggered", lambda **kwargs: (False, {}))
    monkeypatch.setattr(state_handlers, "confirm_big_bite_follow_through", lambda **kwargs: (True, {}))
    monkeypatch.setattr(state_handlers, "build_tick_data_from_ws", lambda ws_data: {})
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [1])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [1])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_capacity",
        lambda *args, **kwargs: (250_000, 240_000, 5, 0.96),
    )
    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", fake_send_buy_order)
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": True,
            "mode": "normal",
            "decision": "ALLOW_NORMAL",
            "reason": "ok",
            "latency_state": "SAFE",
            "orders": [
                {
                    "tag": "normal",
                    "qty": 5,
                    "price": 48_800,
                    "order_type": "LIMIT",
                    "tif": "DAY",
                }
            ],
            "target_buy_price": 48_800,
            "signal_price": 50_500,
            "latest_price": 50_500,
            "computed_allowed_slippage": 0,
            "ws_age_ms": 120,
            "ws_jitter_ms": 20,
            "spread_ratio": 0.0079,
            "quote_stale": False,
            "latency_danger_reasons": "",
            "latency_canary_applied": False,
            "latency_canary_reason": "-",
            "entry_price_guard": "normal_defensive",
            "entry_price_defensive_ticks": 1,
            "normal_defensive_order_price": 50_400,
            "latency_guarded_order_price": 50_400,
            "counterfactual_order_price_1tick": 48_800,
            "order_price": 48_800,
        },
    )

    stock = {"id": 4219, "name": "대한전선", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.9, "rt_ai_prob": 0.9}
    state_handlers.handle_watching_state(
        stock=stock,
        code="001440",
        ws_data={
            "curr": 50_500,
            "v_pw": 120.0,
            "ask_tot": 20_000,
            "bid_tot": 20_000,
            "open": 50_000,
            "fluctuation": 0.5,
            "orderbook": {
                "asks": [{"price": 50_900, "volume": 100}],
                "bids": [{"price": 50_500, "volume": 100}],
            },
        },
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=DummyAI(),
    )

    by_stage = {stage: fields for stage, fields in logs}
    assert sent_orders == []
    assert "order_bundle_submitted" not in by_stage
    assert "pre_submit_price_guard_block" in by_stage, logs
    assert by_stage["pre_submit_price_guard_block"]["submitted_order_price"] == 48_800
    assert by_stage["pre_submit_price_guard_block"]["best_bid_at_submit"] == 50_500
    assert by_stage["pre_submit_price_guard_block"]["best_ask_at_submit"] == 50_900
    assert by_stage["pre_submit_price_guard_block"]["price_below_bid_bps"] == 337
    assert by_stage["pre_submit_price_guard_block"]["max_below_bid_bps"] == 80
    assert by_stage["pre_submit_price_guard_block"]["resolution_reason"] == "reference_target_cap"
    assert by_stage["order_bundle_failed"] == {}


def test_scalping_pre_ai_soft_gate_allows_ai_and_blocks_low_liquidity_at_submit(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 5, 18, 13, 55, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(
        CONFIG,
            SCALP_PRE_AI_SOFT_GATE_ENABLED=True,
            SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
            SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED=True,
            SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED=True,
            SCALP_SIM_PANIC_FORCE_NOOP=True,
        )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.ACTIVE_TARGETS = []
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"

    class DummyRadar:
        def get_smart_target_price(self, curr_price, **kwargs):
            return curr_price, 0.0

    class DummyAI:
        def __init__(self):
            self.seen_context = None

        def analyze_target(self, _name, ws_data, *_args, **_kwargs):
            self.seen_context = ws_data.get("scalp_pre_ai_gate_context")
            return {"action": "BUY", "score": 90, "reason": "confirmed"}

    class DummyEventBus:
        def publish(self, *args, **kwargs):
            return None

    state_handlers.EVENT_BUS = DummyEventBus()
    logs = []
    sent_orders = []

    weak_momentum = {
        "enabled": True,
        "allowed": False,
        "reason": "below_buy_ratio",
        "position_tag": "SCANNER",
        "threshold_profile": "default",
        "base_vpw": 100.0,
        "current_vpw": 100.0,
        "vpw_delta": 0.0,
        "slope_per_sec": 0.0,
        "window_sec": 8,
        "elapsed_sec": 8.0,
        "window_total_value": 100_000,
        "window_buy_value": 48_000,
        "window_sell_value": 52_000,
        "window_buy_ratio": 0.48,
        "window_exec_buy_ratio": 0.45,
        "window_net_buy_qty": -2,
    }

    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "_publish_buy_signal_submission_notice", lambda *args, **kwargs: None)
    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", lambda ws_data: weak_momentum)
    monkeypatch.setattr(state_handlers, "arm_big_bite_if_triggered", lambda **kwargs: (False, {}))
    monkeypatch.setattr(state_handlers, "confirm_big_bite_follow_through", lambda **kwargs: (True, {}))
    monkeypatch.setattr(state_handlers, "build_tick_data_from_ws", lambda ws_data: {})
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"dir": "BUY", "volume": 1, "strength": 100}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"고가": 10000, "저가": 9900}])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_capacity",
        lambda *args, **kwargs: (100_000, 95_000, 5, 0.95),
    )
    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "O1"})
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": True,
            "mode": "normal",
            "decision": "ALLOW_NORMAL",
            "reason": "ok",
            "latency_state": "SAFE",
            "orders": [{"tag": "normal", "qty": 1, "price": kwargs.get("signal_price"), "tif": "DAY"}],
            "signal_price": kwargs.get("signal_price"),
            "latest_price": kwargs.get("signal_price"),
            "computed_allowed_slippage": 0,
            "ws_age_ms": 100,
            "ws_jitter_ms": 10,
            "spread_ratio": 0.001,
            "quote_stale": False,
            "latency_danger_reasons": "",
            "order_price": kwargs.get("signal_price"),
        },
    )

    ai = DummyAI()
    stock = {"id": 10, "name": "LOWLIQ", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.9, "rt_ai_prob": 0.9}
    state_handlers.handle_watching_state(
        stock=stock,
        code="123123",
        ws_data={
            "curr": 10_000,
            "v_pw": 100.0,
            "ask_tot": 100,
            "bid_tot": 100,
            "open": 9_950,
            "fluctuation": 1.0,
            "orderbook": {
                "asks": [{"price": 10_010, "volume": 100}],
                "bids": [{"price": 10_000, "volume": 100}],
            },
        },
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=ai,
    )

    by_stage = {stage: fields for stage, fields in logs}
    assert "ai_confirmed" in by_stage
    assert "scalp_sim_entry_armed" in by_stage
    assert by_stage["blocked_strength_momentum"]["gate_action"] == "risk_context_only"
    assert by_stage["blocked_vpw"]["gate_action"] == "risk_context_only"
    assert by_stage["blocked_liquidity"]["gate_action"] == "risk_context_only"
    assert "pre_submit_liquidity_guard_block" in by_stage
    assert by_stage["pre_submit_liquidity_guard_block"]["broker_order_forbidden"] is True
    assert sent_orders == []
    assert ai.seen_context["liquidity"]["threshold_family"] == "liquidity_pre_submit_guard_p1"


def test_scalping_overbought_reaches_ai_but_submit_requires_pullback_or_rebreak(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 5, 18, 14, 0, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(
        CONFIG,
            SCALP_PRE_AI_SOFT_GATE_ENABLED=True,
            SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
            SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED=True,
            SCALP_SIM_PANIC_FORCE_NOOP=True,
        )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.ACTIVE_TARGETS = []
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()
    state_handlers.KIWOOM_TOKEN = "token"

    class DummyRadar:
        def get_smart_target_price(self, curr_price, **kwargs):
            return curr_price, 0.0

    class DummyAI:
        def analyze_target(self, *args, **kwargs):
            return {"action": "BUY", "score": 91, "reason": "confirmed"}

    state_handlers.EVENT_BUS = type("DummyEventBus", (), {"publish": lambda self, *args, **kwargs: None})()
    logs = []
    sent_orders = []

    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "_publish_buy_signal_submission_notice", lambda *args, **kwargs: None)
    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", lambda ws_data: {"enabled": True, "allowed": True, "reason": "ok"})
    monkeypatch.setattr(state_handlers, "arm_big_bite_if_triggered", lambda **kwargs: (False, {}))
    monkeypatch.setattr(state_handlers, "confirm_big_bite_follow_through", lambda **kwargs: (True, {}))
    monkeypatch.setattr(state_handlers, "build_tick_data_from_ws", lambda ws_data: {})
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"dir": "BUY", "volume": 1, "strength": 110}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"고가": 12_000, "저가": 10_000}])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "describe_buy_capacity", lambda *args, **kwargs: (100_000, 95_000, 5, 0.95))
    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", lambda *args, **kwargs: sent_orders.append(args) or {"return_code": "0", "ord_no": "O1"})
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda **kwargs: {
            "allowed": True,
            "mode": "normal",
            "decision": "ALLOW_NORMAL",
            "reason": "ok",
            "latency_state": "SAFE",
            "orders": [{"tag": "normal", "qty": 1, "price": kwargs.get("signal_price"), "tif": "DAY"}],
            "signal_price": kwargs.get("signal_price"),
            "latest_price": kwargs.get("signal_price"),
            "computed_allowed_slippage": 0,
            "ws_age_ms": 100,
            "ws_jitter_ms": 10,
            "spread_ratio": 0.001,
            "quote_stale": False,
            "latency_danger_reasons": "",
            "order_price": kwargs.get("signal_price"),
        },
    )

    stock = {"id": 11, "name": "HOT", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.9, "rt_ai_prob": 0.9}
    state_handlers.handle_watching_state(
        stock=stock,
        code="456456",
        ws_data={
            "curr": 12_000,
            "v_pw": 110.0,
            "buy_ratio": 52.0,
            "ask_tot": 50_000,
            "bid_tot": 50_000,
            "open": 10_000,
            "high": 12_000,
            "low": 10_000,
            "fluctuation": 21.0,
            "orderbook": {
                "asks": [{"price": 12_010, "volume": 100}],
                "bids": [{"price": 12_000, "volume": 100}],
            },
        },
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=DummyAI(),
    )

    by_stage = {stage: fields for stage, fields in logs}
    assert "ai_confirmed" in by_stage
    assert "scalp_sim_entry_armed" in by_stage
    assert by_stage["blocked_overbought"]["gate_action"] == "risk_context_only"
    assert by_stage["blocked_overbought"]["risk_bucket"] == "chase_risk"
    assert "pre_submit_overbought_pullback_guard_block" in by_stage
    assert by_stage["pre_submit_overbought_pullback_guard_block"]["broker_order_forbidden"] is True
    assert sent_orders == []


def test_scalping_pre_ai_source_quality_block_keeps_insufficient_history_closed(monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 5, 18, 14, 5, 0)

    state_handlers.datetime = FixedDateTime
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALP_PRE_AI_SOFT_GATE_ENABLED=True,
        SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.ACTIVE_TARGETS = []
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    class DummyRadar:
        def get_smart_target_price(self, curr_price, **kwargs):
            return curr_price, 0.0

    class FailingAI:
        def analyze_target(self, *args, **kwargs):
            raise AssertionError("source-quality block should stop before AI")

    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))
    monkeypatch.setattr(state_handlers, "evaluate_scalping_strength_momentum", lambda ws_data: {"enabled": True, "allowed": False, "reason": "insufficient_history"})
    monkeypatch.setattr(state_handlers, "arm_big_bite_if_triggered", lambda **kwargs: (False, {}))
    monkeypatch.setattr(state_handlers, "confirm_big_bite_follow_through", lambda **kwargs: (True, {}))
    monkeypatch.setattr(state_handlers, "build_tick_data_from_ws", lambda ws_data: {})

    stock = {"id": 12, "name": "STALE", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.9, "rt_ai_prob": 0.9}
    state_handlers.handle_watching_state(
        stock=stock,
        code="789789",
        ws_data={
            "curr": 10_000,
            "v_pw": 121.0,
            "ask_tot": 50_000,
            "bid_tot": 50_000,
            "open": 9_900,
            "fluctuation": 1.0,
            "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 10_000}]},
        },
        admin_id=1,
        radar=DummyRadar(),
        ai_engine=FailingAI(),
    )

    by_stage = {stage: fields for stage, fields in logs}
    assert by_stage["blocked_strength_momentum"]["gate_action"] == "source_quality_block"
    assert by_stage["blocked_strength_momentum"]["source_quality_block_reason"] == "insufficient_history"
    assert "ai_confirmed" not in by_stage


def test_scalping_entry_timeout_uses_strategy_profile_not_target_price(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_TIMEOUT_SEC=90,
            SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC=120,
            SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC=600,
            SCALPING_RESERVE_ENTRY_TIMEOUT_SEC=1200,
        ),
    )

    assert state_handlers._resolve_buy_order_timeout_sec(
        {"target_buy_price": 48_800, "position_tag": "SCANNER"},
        "SCALPING",
    ) == 90
    assert state_handlers._resolve_buy_order_timeout_sec(
        {"target_buy_price": 48_800, "position_tag": "BREAKOUT"},
        "SCALPING",
    ) == 120
    assert state_handlers._resolve_buy_order_timeout_sec(
        {"target_buy_price": 48_800, "position_tag": "PULLBACK"},
        "SCALPING",
    ) == 600
    assert state_handlers._resolve_buy_order_timeout_sec(
        {"target_buy_price": 48_800, "entry_timeout_profile": "RESERVE"},
        "SCALPING",
    ) == 1200


def test_entry_ai_price_canary_improves_live_order_price(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=60,
            SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE=80,
        ),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"price": 10020}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"close": 10020}])
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    class DummyAI:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "IMPROVE_LIMIT",
                "order_price": 10010,
                "confidence": 72,
                "reason": "호가 흡수 지속",
                "max_wait_sec": 45,
                "ai_parse_ok": True,
                "ai_parse_fail": False,
                "openai_transport_mode": "responses_ws",
                "openai_ws_used": True,
                "openai_ws_http_fallback": False,
                "openai_endpoint_name": "entry_price",
                "openai_ws_roundtrip_ms": 1200,
            }

    latency_gate = {
        "target_buy_price": 9980,
        "latency_guarded_order_price": 9990,
        "normal_defensive_order_price": 9990,
        "order_price": 9990,
        "price_resolution_reason": "defensive_order_price",
        "latency_state": "SAFE",
    }
    planned_orders = [{"tag": "normal", "qty": 1, "price": 9990, "tif": "DAY", "order_type": "LIMIT"}]
    stock = {"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.8}

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock=stock,
        code="123456",
        strategy="SCALPING",
        ws_data={"curr": 10020},
        ai_engine=DummyAI(),
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    assert touched is True
    assert adjusted[0]["price"] == 10010
    assert latency_gate["order_price"] == 10010
    assert latency_gate["price_resolution_reason"] == "ai_tier2_improve_limit"
    assert latency_gate["openai_endpoint_name"] == "entry_price"
    assert latency_gate["openai_transport_mode"] == "responses_ws"
    assert stock["entry_timeout_sec_override"] == 45
    applied = [fields for stage, fields in logs if stage == "entry_ai_price_canary_applied"][0]
    assert applied["openai_endpoint_name"] == "entry_price"
    assert applied["openai_ws_roundtrip_ms"] == 1200


def test_entry_ai_price_canary_falls_back_on_guard_block(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=60,
            SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True,
            SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80,
        ),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"price": 10020}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"close": 10020}])
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    class DummyAI:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "USE_REFERENCE",
                "order_price": 9000,
                "confidence": 90,
                "reason": "너무 깊은 대기",
                "max_wait_sec": 90,
                "ai_parse_ok": True,
                "ai_parse_fail": False,
            }

    latency_gate = {
        "target_buy_price": 9000,
        "latency_guarded_order_price": 9990,
        "normal_defensive_order_price": 9990,
        "order_price": 9990,
        "price_resolution_reason": "defensive_order_price",
        "latency_state": "SAFE",
    }
    planned_orders = [{"tag": "normal", "qty": 1, "price": 9990, "tif": "DAY", "order_type": "LIMIT"}]

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock={"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER"},
        code="123456",
        strategy="SCALPING",
        ws_data={"curr": 10020},
        ai_engine=DummyAI(),
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    assert touched is False
    assert adjusted == planned_orders
    assert latency_gate["order_price"] == 9990
    assert any(fields.get("reason") == "pre_submit_price_guard" for stage, fields in logs if stage == "entry_ai_price_canary_fallback")


def test_entry_ai_price_canary_clamps_wait_danger_passive_probe_to_one_tick(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=60,
        ),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"price": 92000}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"close": 92000}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_size", lambda price: 100)
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    class DummyAI:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "USE_DEFENSIVE",
                "confidence": 85,
                "reason": "latency danger defensive",
                "max_wait_sec": 60,
                "ai_parse_ok": True,
                "ai_parse_fail": False,
            }

    latency_gate = {
        "target_buy_price": 91900,
        "latency_guarded_order_price": 91700,
        "normal_defensive_order_price": 91900,
        "order_price": 91700,
        "price_resolution_reason": "defensive_order_price",
        "latency_state": "DANGER",
    }
    planned_orders = [{"tag": "normal", "qty": 1, "price": 91700, "tif": "DAY", "order_type": "LIMIT"}]
    stock = {
        "name": "파두",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "prob": 0.75,
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 75,
    }

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock=stock,
        code="440110",
        strategy="SCALPING",
        ws_data={"curr": 92000},
        ai_engine=DummyAI(),
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        curr_price=92000,
        best_bid=92000,
        best_ask=92100,
    )

    assert touched is True
    assert adjusted[0]["price"] == 91900
    assert latency_gate["order_price"] == 91900
    assert latency_gate["entry_order_lifecycle"] == "passive_probe"
    assert latency_gate["entry_passive_probe_applied"] is True
    assert stock["entry_timeout_sec_override"] == 30
    applied = [fields for stage, fields in logs if stage == "entry_ai_price_canary_applied"][0]
    assert applied["entry_passive_probe_original_price"] == 91700
    assert applied["entry_passive_probe_adjusted_price"] == 91900


def test_passive_probe_stale_submit_revalidation_blocks(monkeypatch):
    monkeypatch.setattr(state_handlers.time, "time", lambda: 100.0)

    fields = state_handlers._build_entry_submit_revalidation_fields(
        {"last_ws_update_ts": 97.0},
        {
            "entry_order_lifecycle": "passive_probe",
            "entry_passive_probe_applied": True,
            "ai_entry_price_canary_decision_ts": 90.0,
            "ai_entry_price_canary_context_age_ms": 9000,
        },
        now_ts=100.0,
    )

    assert fields["entry_submit_revalidation_warning"] == "stale_context_or_quote"
    assert fields["quote_stale_at_submit"] is True
    assert state_handlers._is_passive_probe_stale_submit_block(fields) is True


def test_pending_entry_cancel_logs_receipt_provenance(monkeypatch):
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: {"return_code": "0", "ord_no": "C1", "return_msg": "정상"},
    )
    stock = {
        "id": 1,
        "name": "TEST",
        "pending_entry_orders": [
            {
                "tag": "normal",
                "qty": 1,
                "filled_qty": 0,
                "price": 91900,
                "ord_no": "O1",
                "status": "OPEN",
                "sent_at": time.time() - 31,
                "entry_order_lifecycle": "passive_probe",
                "entry_passive_probe_applied": True,
                "best_bid_at_submit": 92000,
                "best_ask_at_submit": 92100,
                "price_below_bid_bps": 11,
            }
        ],
    }

    assert state_handlers._cancel_pending_entry_orders(stock, "440110", force=True) == "cancelled"
    stages = {stage: fields for stage, fields in logs}
    assert stages["entry_order_cancel_requested"]["orig_ord_no"] == "O1"
    assert stages["entry_order_cancel_requested"]["entry_order_lifecycle"] == "passive_probe"
    assert stages["entry_order_cancel_confirmed"]["cancel_ord_no"] == "C1"
    assert stages["entry_order_cancel_confirmed"]["submitted_price"] == 91900


def test_entry_ai_price_context_includes_orderbook_micro_when_enabled(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True),
    )
    latency_gate = {
        "target_buy_price": 9980,
        "latency_guarded_order_price": 9990,
        "normal_defensive_order_price": 9990,
        "order_price": 9990,
        "latency_state": "SAFE",
        "orderbook_stability": {
            "orderbook_micro": {
                "ready": True,
                "reason": "ready",
                "qi": 0.42,
                "qi_ewma": 0.44,
                "ofi_norm": -1.5,
                "ofi_z": -1.2,
                "depth_ewma": 1200.0,
                "micro_state": "bearish",
                "sample_quote_count": 24,
                "captured_at_ms": 100_000,
                "observer_healthy": True,
                "observer_missing_reason": "ok",
                "observer_last_quote_age_ms": 120.0,
                "observer_last_trade_age_ms": 220.0,
                "micro_window_sec": 60.0,
                "micro_z_min_samples": 20,
                "micro_lambda": 0.3,
                "ofi_bull_threshold": 1.2,
                "ofi_bear_threshold": -1.0,
                "qi_bull_threshold": 0.55,
                "qi_bear_threshold": 0.48,
                "ofi_threshold_source": "bucket",
                "ofi_threshold_bucket_key": "spread=tight|price=mid|depth=normal|sample=normal",
                "ofi_threshold_manifest_id": "manifest1",
                "ofi_threshold_manifest_version": "v1",
                "ofi_threshold_fallback_reason": "",
                "ofi_bucket_key": "spread=tight|price=mid|depth=normal|sample=normal",
                "ofi_calibration_warning": "",
            }
        },
    }

    ctx = state_handlers._build_entry_ai_price_context(
        {"strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.8},
        latency_gate,
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    assert ctx["orderbook_micro"]["ready"] is True
    assert ctx["orderbook_micro"]["micro_state"] == "bearish"
    assert ctx["orderbook_micro"]["spread_ticks"] == 1
    assert ctx["orderbook_micro"]["ofi_threshold_source"] == "bucket"
    assert ctx["orderbook_micro"]["ofi_threshold_manifest_id"] == "manifest1"
    log_fields = state_handlers._build_orderbook_micro_log_fields(ctx["orderbook_micro"])
    assert log_fields["orderbook_micro_ofi_threshold_source"] == "bucket"
    assert log_fields["orderbook_micro_observer_healthy"] is True


def test_entry_ai_price_context_omits_orderbook_micro_when_disabled(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(CONFIG, SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=False),
    )

    ctx = state_handlers._build_entry_ai_price_context(
        {"strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.8},
        {"order_price": 9990, "orderbook_stability": {"orderbook_micro": {"ready": True}}},
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    assert "orderbook_micro" not in ctx


def test_entry_ai_price_skip_logs_bearish_policy_basis(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=60,
            SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE=80,
            SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True,
        ),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"price": 10020}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"close": 10020}])
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    class DummyAI:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "SKIP",
                "order_price": 0,
                "confidence": 90,
                "reason": "매도 우위",
                "max_wait_sec": 90,
                "ai_parse_ok": True,
                "ai_parse_fail": False,
            }

    stock = {"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.8}
    latency_gate = {
        "target_buy_price": 9980,
        "latency_guarded_order_price": 9990,
        "normal_defensive_order_price": 9990,
        "order_price": 9990,
        "latency_state": "SAFE",
        "orderbook_stability": {
            "orderbook_micro": {
                "ready": True,
                "micro_state": "bearish",
                "ofi_threshold_source": "bucket",
                "ofi_bucket_key": "spread=tight|price=mid|depth=normal|sample=normal",
                "sample_quote_count": 24,
            }
        },
    }

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock=stock,
        code="123456",
        strategy="SCALPING",
        ws_data={"curr": 10020},
        ai_engine=DummyAI(),
        latency_gate=latency_gate,
        planned_orders=[{"tag": "normal", "qty": 1, "price": 9990, "tif": "DAY", "order_type": "LIMIT"}],
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    assert adjusted == []
    assert touched is True
    skip_log = [fields for stage, fields in logs if stage == "entry_ai_price_canary_skip_order"][0]
    assert skip_log["entry_ai_price_skip_policy_warning"] == ""
    assert skip_log["entry_ai_price_skip_policy_basis"] == "ofi_bearish_supported"
    assert stock["entry_ai_price_skip_policy_warning"] == ""
    assert stock["entry_ai_price_skip_threshold_source"] == "bucket"


def test_entry_ai_price_skip_logs_non_bearish_policy_warning(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=60,
            SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE=80,
            SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True,
        ),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"price": 10020}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"close": 10020}])
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    class DummyAI:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "SKIP",
                "order_price": 0,
                "confidence": 90,
                "reason": "불리한 호가",
                "max_wait_sec": 90,
                "ai_parse_ok": True,
                "ai_parse_fail": False,
            }

    state_handlers._apply_entry_ai_price_canary(
        stock={"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.8},
        code="123456",
        strategy="SCALPING",
        ws_data={"curr": 10020},
        ai_engine=DummyAI(),
        latency_gate={
            "target_buy_price": 9980,
            "latency_guarded_order_price": 9990,
            "normal_defensive_order_price": 9990,
            "order_price": 9990,
            "latency_state": "SAFE",
            "orderbook_stability": {
                "orderbook_micro": {
                    "ready": True,
                    "micro_state": "neutral",
                    "sample_quote_count": 24,
                }
            },
        },
        planned_orders=[{"tag": "normal", "qty": 1, "price": 9990, "tif": "DAY", "order_type": "LIMIT"}],
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    skip_log = [fields for stage, fields in logs if stage == "entry_ai_price_canary_skip_order"][0]
    assert skip_log["entry_ai_price_skip_policy_warning"] == "skip_without_bearish_ofi"
    assert skip_log["entry_ai_price_skip_policy_basis"] == "neutral"


def test_entry_ai_price_low_confidence_skip_demotes_to_p1_when_ofi_not_bearish(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            CONFIG,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=60,
            SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE=80,
            SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_ENABLED=True,
            SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE=90,
            SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True,
        ),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [{"price": 10020}])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [{"close": 10020}])
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    class DummyAI:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "SKIP",
                "order_price": 0,
                "confidence": 85,
                "reason": "저신뢰 skip",
                "max_wait_sec": 90,
                "ai_parse_ok": True,
                "ai_parse_fail": False,
            }

    planned_orders = [{"tag": "normal", "qty": 1, "price": 9990, "tif": "DAY", "order_type": "LIMIT"}]
    latency_gate = {
        "target_buy_price": 9980,
        "latency_guarded_order_price": 9990,
        "normal_defensive_order_price": 9990,
        "order_price": 9990,
        "latency_state": "SAFE",
        "orderbook_stability": {
            "orderbook_micro": {
                "ready": True,
                "observer_healthy": True,
                "snapshot_age_ms": 100,
                "micro_state": "neutral",
                "sample_quote_count": 24,
                "ofi_z": 0.1,
                "qi_ewma": 0.51,
            }
        },
    }

    adjusted, touched = state_handlers._apply_entry_ai_price_canary(
        stock={"name": "TEST", "strategy": "SCALPING", "position_tag": "SCANNER", "prob": 0.8},
        code="123456",
        strategy="SCALPING",
        ws_data={"curr": 10020},
        ai_engine=DummyAI(),
        latency_gate=latency_gate,
        planned_orders=planned_orders,
        curr_price=10020,
        best_bid=10020,
        best_ask=10030,
    )

    assert touched is True
    assert adjusted == planned_orders
    assert latency_gate["ai_entry_price_canary_raw_action"] == "SKIP"
    assert latency_gate["ai_entry_price_canary_final_action"] == "USE_DEFENSIVE"
    assert latency_gate["price_resolution_reason"] == "ai_tier2_skip_demoted_to_p1"
    assert any(stage == "entry_ai_price_ofi_skip_demoted" for stage, _ in logs)
    assert not any(stage == "entry_ai_price_canary_skip_order" for stage, _ in logs)


def test_entry_ai_price_skip_followup_logs_mfe_mae(monkeypatch):
    logs = []
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))
    stock = {
        "name": "TEST",
        "entry_ai_price_skip_started_at": 100.0,
        "entry_ai_price_skip_mark_price": 10_000,
        "entry_ai_price_skip_max_price": 10_100,
        "entry_ai_price_skip_min_price": 9_980,
        "entry_ai_price_skip_micro_state": "bearish",
        "entry_ai_price_skip_policy_warning": "ofi_not_ready",
        "entry_ai_price_skip_threshold_source": "fallback",
        "entry_ai_price_skip_bucket_key": "spread=unknown|price=unknown|depth=unknown|sample=insufficient",
        "entry_ai_price_skip_followup_30s": False,
        "entry_ai_price_skip_followup_90s": False,
    }

    state_handlers._maybe_emit_entry_ai_price_skip_followup(stock, "123456", curr_price=10_050, now_ts=130.0)

    assert logs[0][0] == "entry_ai_price_canary_skip_followup"
    assert logs[0][1]["elapsed_sec"] == 30
    assert logs[0][1]["mfe_bps"] == 100
    assert logs[0][1]["mae_bps"] == -20
    assert logs[0][1]["micro_state_at_skip"] == "bearish"
    assert logs[0][1]["ofi_threshold_source_at_skip"] == "fallback"
    assert logs[0][1]["ofi_bucket_key_at_skip"] == "spread=unknown|price=unknown|depth=unknown|sample=insufficient"
    assert logs[0][1]["entry_ai_price_skip_policy_warning"] == "ofi_not_ready"
    assert stock["entry_ai_price_skip_followup_30s"] is True


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


def test_publish_buy_signal_submission_notice_enqueues_once(monkeypatch):
    published = []
    pipeline_stages = []

    class DummyEventBus:
        def publish(self, topic, payload):
            published.append((topic, payload))

    monkeypatch.setattr(state_handlers, "EVENT_BUS", DummyEventBus())
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda _stock, _code, stage, **_fields: pipeline_stages.append(stage),
    )

    stock = {
        "id": 1,
        "name": "덕산하이메탈",
        "entry_bundle_id": "077360-test-bundle",
        "entry_dynamic_reason": "strong_absolute_override",
        "msg_audience": "ADMIN_ONLY",
    }
    latency_gate = {"latency_state": "SAFE", "decision": "ALLOW_NORMAL"}

    state_handlers._publish_buy_signal_submission_notice(
        stock,
        "077360",
        strategy="SCALPING",
        curr_price=16720,
        requested_qty=68,
        entry_mode="normal",
        latency_gate=latency_gate,
    )
    state_handlers._publish_buy_signal_submission_notice(
        stock,
        "077360",
        strategy="SCALPING",
        curr_price=16720,
        requested_qty=68,
        entry_mode="normal",
        latency_gate=latency_gate,
    )

    assert len(published) == 1
    topic, payload = published[0]
    assert topic == "TELEGRAM_BROADCAST"
    assert payload["audience"] == "ADMIN_ONLY"
    assert payload["parse_mode"] == "Markdown"
    assert "BUY 신호 감지" in payload["message"]
    assert "덕산하이메탈 (077360)" in payload["message"]
    assert "후보수량" in payload["message"]
    assert "주문 제출" not in payload["message"]
    assert "strong_absolute_override" in payload["message"]
    assert pipeline_stages == ["buy_signal_telegram_enqueued"]


def test_publish_buy_signal_submission_notice_uses_vip_liquidity_gate(monkeypatch):
    published = []

    class DummyEventBus:
        def publish(self, topic, payload):
            published.append((topic, payload))

    monkeypatch.setattr(state_handlers, "EVENT_BUS", DummyEventBus())
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda _stock, _code, _stage, **_fields: None,
    )

    state_handlers._publish_buy_signal_submission_notice(
        {
            "id": 1,
            "name": "유동성충족",
            "entry_bundle_id": "vip-bundle",
            "entry_dynamic_reason": "strong_absolute_override",
        },
        "111111",
        strategy="SCALPING",
        curr_price=10000,
        requested_qty=10,
        entry_mode="normal",
        latency_gate={"latency_state": "SAFE", "decision": "ALLOW_NORMAL"},
        liquidity_value=1_500_000_000,
        ai_score=95,
    )

    assert published[0][1]["audience"] == "VIP_ALL"


def test_publish_buy_signal_submission_notice_forces_simulation_admin(monkeypatch):
    published = []

    class DummyEventBus:
        def publish(self, topic, payload):
            published.append((topic, payload))

    monkeypatch.setattr(state_handlers, "EVENT_BUS", DummyEventBus())
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda _stock, _code, _stage, **_fields: None,
    )

    state_handlers._publish_buy_signal_submission_notice(
        {
            "id": 1,
            "name": "스윙드라이런",
            "entry_bundle_id": "swing-sim-bundle",
            "entry_dynamic_reason": "dry_run",
        },
        "222222",
        strategy="KOSPI_ML",
        curr_price=10000,
        requested_qty=10,
        entry_mode="swing",
        latency_gate={"latency_state": "SAFE", "decision": "ALLOW_NORMAL"},
        liquidity_value=1_500_000_000,
        ai_score=95,
    )

    assert published[0][1]["audience"] == "ADMIN_ONLY"


def test_receipt_audience_forces_simulation_admin():
    assert (
        receipts._receipt_audience(
            {
                "msg_audience": "VIP_ALL",
                "simulation_book": "scalp_ai_buy_all",
                "actual_order_submitted": False,
            }
        )
        == "ADMIN_ONLY"
    )


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


def test_find_execution_target_prefers_exact_buy_order_match_over_pending_add():
    receipts.ACTIVE_TARGETS = [
        {
            "id": 1,
            "code": "123456",
            "status": "BUY_ORDERED",
            "odno": "O1",
        },
        {
            "id": 2,
            "code": "123456",
            "status": "HOLDING",
            "pending_add_order": True,
            "pending_add_ord_no": "O1",
        },
    ]

    target = receipts._find_execution_target("123456", "BUY", "O1")

    assert target["id"] == 1


def test_find_execution_target_prefers_single_pending_add_candidate_without_order_no():
    receipts.ACTIVE_TARGETS = [
        {
            "id": 1,
            "code": "123456",
            "status": "BUY_ORDERED",
            "odno": "O1",
        },
        {
            "id": 2,
            "code": "123456",
            "status": "HOLDING",
            "pending_add_order": True,
            "pending_add_ord_no": "A1",
        },
    ]

    target = receipts._find_execution_target("123456", "BUY", "")

    assert target["id"] == 2


def test_find_execution_target_prefers_bundle_ord_no_over_buy_ordered_status_match():
    receipts.ACTIVE_TARGETS = [
        {
            "id": 1,
            "code": "123456",
            "status": "BUY_ORDERED",
            "odno": "O1",
        },
        {
            "id": 2,
            "code": "123456",
            "status": "BUY_ORDERED",
            "pending_entry_orders": [
                {"tag": "fallback_main", "ord_no": "O1", "status": "OPEN"},
            ],
        },
    ]

    target = receipts._find_execution_target("123456", "BUY", "O1")

    assert target["id"] == 2


def test_find_execution_target_prefers_exact_sell_order_match():
    receipts.ACTIVE_TARGETS = [
        {
            "id": 1,
            "code": "123456",
            "status": "SELL_ORDERED",
            "sell_odno": "S1",
        },
        {
            "id": 2,
            "code": "123456",
            "status": "SELL_ORDERED",
            "sell_odno": "S2",
        },
    ]

    target = receipts._find_execution_target("123456", "SELL", "S2")

    assert target["id"] == 2


def test_find_execution_target_returns_none_for_ambiguous_buy_order_without_order_no():
    receipts.ACTIVE_TARGETS = [
        {
            "id": 1,
            "code": "123456",
            "status": "BUY_ORDERED",
            "odno": "O1",
        },
        {
            "id": 2,
            "code": "123456",
            "status": "BUY_ORDERED",
            "odno": "O2",
        },
    ]

    target = receipts._find_execution_target("123456", "BUY", "")

    assert target is None


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


def test_cancel_order_notice_does_not_bind_as_buy_order():
    receipts.ACTIVE_TARGETS = []

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "position_tag": "MIDDLE",
        "pending_entry_orders": [
            {"tag": "normal", "qty": 1, "ord_no": "", "status": "OPEN", "filled_qty": 0},
        ],
    }
    receipts.ACTIVE_TARGETS.append(stock)

    receipts.handle_order_notice({"code": "123456", "type": "BUY_CANCEL", "order_no": "C1", "status": "접수"})

    assert stock.get("odno") in (None, "")
    assert stock["pending_entry_orders"][0]["ord_no"] == ""
    assert "notice_status" not in stock["pending_entry_orders"][0]


def test_order_execution_notice_parses_cancel_side_separately():
    manager = KiwoomWSManager.__new__(KiwoomWSManager)

    notice = manager._parse_order_execution_notice({
        "913": "접수",
        "9001": "A123456",
        "9203": "C1",
        "905": "매수취소",
    })

    assert notice["exec_type"] == "BUY_CANCEL"
    assert notice["order_type_str"] == "매수취소"


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


def test_buy_execution_thread_receives_snapshot_and_clears_live_notify_state(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None
    receipts.DB = _DummyDB()

    thread_calls = []

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            thread_calls.append((target, args, daemon))

        def start(self):
            return None

    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)

    stock = {
        "id": 11,
        "code": "123456",
        "name": "TEST",
        "status": "BUY_ORDERED",
        "strategy": "KOSPI_ML",
        "buy_price": 0,
        "buy_qty": 0,
        "pending_buy_msg": "그물망 투척!",
        "msg_audience": "ADMIN_ONLY",
    }
    receipts.ACTIVE_TARGETS.append(stock)

    receipts.handle_real_execution({"code": "123456", "type": "BUY", "order_no": "B1", "price": 10000, "qty": 1})

    assert stock["buy_execution_notified"] is True
    assert "pending_buy_msg" not in stock
    assert thread_calls
    _, args, _ = thread_calls[0]
    snapshot = args[3]
    assert snapshot is not stock
    assert snapshot["pending_buy_msg"] == "그물망 투척!"
    assert snapshot["buy_execution_notified"] is False
    assert snapshot["buy_qty"] == 1

    stock["buy_qty"] = 999
    assert snapshot["buy_qty"] == 1


def test_sell_execution_thread_receives_snapshot_and_clears_live_notify_state(monkeypatch):
    receipts.ACTIVE_TARGETS = []
    receipts.highest_prices = {}
    receipts._get_fast_state = lambda code: None

    thread_calls = []

    class SellRecord:
        buy_price = 10000.0
        strategy = "KOSPI_ML"

    class SellQuery:
        def filter_by(self, **kwargs):
            return self

        def first(self):
            return SellRecord()

    class SellSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query(self, *args, **kwargs):
            return SellQuery()

    class SellDB:
        def get_session(self):
            return SellSession()

    class DummyThread:
        def __init__(self, target=None, args=(), daemon=None):
            thread_calls.append((target, args, daemon))

        def start(self):
            return None

    receipts.DB = SellDB()
    monkeypatch.setattr(receipts.threading, "Thread", DummyThread)

    stock = {
        "id": 12,
        "code": "123456",
        "name": "TEST",
        "status": "SELL_ORDERED",
        "strategy": "KOSPI_ML",
        "sell_odno": "S1",
        "buy_qty": 3,
        "pending_sell_msg": "[익절 주문] 매도 전송",
        "last_exit_rule": "scalp_take_profit",
        "msg_audience": "ADMIN_ONLY",
    }
    receipts.ACTIVE_TARGETS.append(stock)

    receipts.handle_real_execution({"code": "123456", "type": "SELL", "order_no": "S1", "price": 10100, "qty": 3})

    assert stock["status"] == "COMPLETED"
    assert "pending_sell_msg" not in stock
    assert thread_calls
    _, args, _ = thread_calls[0]
    snapshot = args[3]
    assert snapshot is not stock
    assert snapshot["pending_sell_msg"] == "[익절 주문] 매도 전송"
    assert snapshot["last_exit_rule"] == "scalp_take_profit"
    assert snapshot["buy_qty"] == 3

    stock["buy_qty"] = 999
    assert snapshot["buy_qty"] == 3


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
        SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=True,
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
        "order_time": now - 120,
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
        SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=True,
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
        "order_time": now - 120,
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
    assert called["gate"] is True
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
        now_dt=datetime(2026, 5, 4, 15, 0, 0),
        radar=None,
        ai_engine=None,
    )

    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    sent_logs = [fields for stage, fields in pipeline_logs if stage == "sell_order_sent"]

    assert stock["last_exit_rule"] == "scalp_soft_stop_pct"
    assert stock["last_exit_decision_source"] == "SOFT_STOP"
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_soft_stop_pct"
    assert exit_logs[-1]["exit_decision_source"] == "SOFT_STOP"
    assert sent_logs and sent_logs[-1]["exit_rule"] == "scalp_soft_stop_pct"
    assert sent_logs[-1]["exit_decision_source"] == "SOFT_STOP"


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
    assert stock["last_exit_decision_source"] == "PRESET_HARD_STOP"
    assert stock["sell_ord_no"] == "SIOC1"
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_preset_hard_stop_pct"
    assert exit_logs[-1]["exit_decision_source"] == "PRESET_HARD_STOP"
    assert exit_logs[-1]["sell_reason_type"] == "LOSS"
    assert sent_logs and sent_logs[-1]["exit_rule"] == "scalp_preset_hard_stop_pct"
    assert sent_logs[-1]["exit_decision_source"] == "PRESET_HARD_STOP"
    assert sent_logs[-1]["order_type"] == "16"


def test_sell_reject_with_positive_sellable_qty_keeps_holding(monkeypatch):
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
        lambda *args, **kwargs: {
            "return_code": "20",
            "return_msg": "[2000](800033:매도가능수량이 부족합니다. 125주 매도가능)",
        },
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 14,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 145,
        "rt_ai_prob": 0.50,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 98.0, "orderbook": {"bids": [{"price": 98, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        now_dt=datetime(2026, 5, 4, 15, 0, 0),
        radar=None,
        ai_engine=None,
    )

    fail_logs = [fields for stage, fields in pipeline_logs if stage == "sell_order_failed"]
    assert stock["status"] == "HOLDING"
    assert stock["buy_qty"] == 125
    assert fail_logs
    assert fail_logs[-1]["new_status"] == "HOLDING"
    assert fail_logs[-1]["sellable_qty"] == 125


def test_sell_reject_with_zero_sellable_qty_marks_completed(monkeypatch):
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
        lambda *args, **kwargs: {
            "return_code": "20",
            "return_msg": "[2000](800033:매도가능수량이 부족합니다. 0주 매도가능)",
        },
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 15,
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
        now_dt=datetime(2026, 5, 4, 15, 0, 0),
        radar=None,
        ai_engine=None,
    )

    fail_logs = [fields for stage, fields in pipeline_logs if stage == "sell_order_failed"]
    assert stock["status"] == "COMPLETED"
    assert fail_logs
    assert fail_logs[-1]["new_status"] == "COMPLETED"
    assert fail_logs[-1]["sellable_qty"] == 0


def test_scalping_sell_after_market_close_blocks_order_once(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []
    sell_calls = []

    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: pipeline_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append((args, kwargs)) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "near_market_close"},
    )

    stock = {
        "id": 16,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 100,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
    }
    now_dt = datetime(2026, 5, 4, 15, 31, 0)

    for _ in range(2):
        state_handlers.handle_holding_state(
            stock=stock,
            code="123456",
            ws_data={"curr": 98.0, "orderbook": {"bids": [{"price": 98, "volume": 1000}]}},
            admin_id=1,
            market_regime="BULL",
            now_ts=1_777_900_000,
            now_dt=now_dt,
            radar=None,
            ai_engine=None,
        )

    blocked = [fields for stage, fields in pipeline_logs if stage == "sell_order_blocked_market_closed"]
    assert stock["status"] == "HOLDING"
    assert stock["market_closed_sell_pending"] is True
    assert stock["market_closed_sell_exit_rule"] == "scalp_soft_stop_pct"
    assert stock["market_closed_sell_exit_decision_source"] == "SOFT_STOP"
    assert len(blocked) == 1
    assert blocked[-1]["exit_rule"] == "scalp_soft_stop_pct"
    assert blocked[-1]["exit_decision_source"] == "SOFT_STOP"
    assert sell_calls == []
    assert not [stage for stage, _ in pipeline_logs if stage == "sell_order_failed"]


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


def test_scalp_soft_stop_micro_grace_delays_exit(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True,
        SCALP_SOFT_STOP_MICRO_GRACE_SEC=20,
        SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0,
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
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: exit_calls.append(args) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 16,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9840, "orderbook": {"bids": [{"price": 9840, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    grace_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_micro_grace"]
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert stock["status"] == "HOLDING"
    assert stock["soft_stop_micro_grace_started_at"] > 0
    assert grace_logs
    assert grace_logs[-1]["grace_sec"] == 20
    assert not exit_logs
    assert not exit_calls


def test_bad_entry_block_observe_logs_never_green_ai_fade(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED=True,
        SCALP_BAD_ENTRY_BLOCK_MIN_HOLD_SEC=60,
        SCALP_BAD_ENTRY_BLOCK_MIN_LOSS_PCT=-0.70,
        SCALP_BAD_ENTRY_BLOCK_MAX_PEAK_PROFIT_PCT=0.20,
        SCALP_BAD_ENTRY_BLOCK_AI_SCORE_LIMIT=45,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10005}
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
        "id": 1601,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 2,
        "rt_ai_prob": 0.40,
        "order_time": state_handlers.time.time() - 90,
        "last_reversal_features": {
            "buy_pressure_10t": 42.0,
            "tick_acceleration_ratio": 0.80,
            "large_sell_print_detected": True,
            "curr_vs_micro_vwap_bp": -12.0,
        },
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9920, "orderbook": {"bids": [{"price": 9920, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    observed = [fields for stage, fields in pipeline_logs if stage == "bad_entry_block_observed"]
    assert observed
    assert observed[-1]["observe_only"] is True
    assert observed[-1]["classifier"] == "never_green_ai_fade"
    assert stock["status"] == "HOLDING"


def test_bad_entry_refined_canary_exits_before_soft_stop(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_STOP=-1.50,
        SCALP_HARD_STOP=-2.50,
        SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED=True,
        SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=True,
        SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC=180,
        SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT=-1.16,
        SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT=0.05,
        SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT=45,
        SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX=0.30,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10000}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []

    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: pipeline_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1602,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 2,
        "rt_ai_prob": 0.40,
        "order_time": state_handlers.time.time() - 240,
        "last_reversal_features": {
            "buy_pressure_10t": 24.0,
            "tick_acceleration_ratio": 0.50,
            "large_sell_print_detected": True,
            "curr_vs_micro_vwap_bp": -24.0,
            "net_aggressive_delta_10t": -500,
            "same_price_buy_absorption": 0,
            "microprice_edge_bp": -3.0,
            "top3_depth_ratio": 1.8,
        },
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9875, "orderbook": {"bids": [{"price": 9875, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        now_dt=datetime(2026, 5, 4, 15, 0, 0),
        radar=None,
        ai_engine=None,
    )

    candidate = [fields for stage, fields in pipeline_logs if stage == "bad_entry_refined_candidate"]
    refined_exit = [fields for stage, fields in pipeline_logs if stage == "bad_entry_refined_exit"]
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert candidate and candidate[-1]["should_exit"] is True
    assert refined_exit
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_bad_entry_refined_canary"
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_bad_entry_refined_canary"


def test_bad_entry_refined_observe_logs_when_canary_disabled(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_STOP=-1.50,
        SCALP_HARD_STOP=-2.50,
        SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=False,
        SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED=True,
        SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC=180,
        SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT=-1.16,
        SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT=0.05,
        SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT=45,
        SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX=0.30,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10000}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []
    sell_calls = []

    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: pipeline_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append((args, kwargs)) or {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1604,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 2,
        "rt_ai_prob": 0.40,
        "order_time": state_handlers.time.time() - 240,
        "last_reversal_features": {
            "buy_pressure_10t": 24.0,
            "tick_acceleration_ratio": 0.50,
            "large_sell_print_detected": True,
            "curr_vs_micro_vwap_bp": -24.0,
            "net_aggressive_delta_10t": -500,
            "same_price_buy_absorption": 0,
            "microprice_edge_bp": -3.0,
            "top3_depth_ratio": 1.8,
        },
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9875, "orderbook": {"bids": [{"price": 9875, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        now_dt=datetime(2026, 5, 4, 15, 0, 0),
        radar=None,
        ai_engine=None,
    )

    candidate = [fields for stage, fields in pipeline_logs if stage == "bad_entry_refined_candidate"]
    assert candidate
    assert candidate[-1]["canary_enabled"] is False
    assert candidate[-1]["observe_only"] is True
    assert candidate[-1]["should_exit"] is False
    assert candidate[-1]["would_exit"] is True
    assert stock["status"] == "HOLDING"
    assert sell_calls == []


def test_bad_entry_refined_canary_skips_recovered_peak(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_STOP=-1.50,
        SCALP_HARD_STOP=-2.50,
        SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=True,
        SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC=180,
        SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT=-1.16,
        SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT=0.05,
        SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT=45,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10080}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.DB = _DummyDB()

    pipeline_logs = []
    sell_calls = []

    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: pipeline_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
    )

    stock = {
        "id": 1603,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 2,
        "rt_ai_prob": 0.40,
        "order_time": state_handlers.time.time() - 240,
        "last_reversal_features": {
            "buy_pressure_10t": 24.0,
            "tick_acceleration_ratio": 0.50,
            "large_sell_print_detected": True,
            "curr_vs_micro_vwap_bp": -24.0,
            "net_aggressive_delta_10t": -500,
        },
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9875, "orderbook": {"bids": [{"price": 9875, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    candidate = [fields for stage, fields in pipeline_logs if stage == "bad_entry_refined_candidate"]
    refined_exit = [fields for stage, fields in pipeline_logs if stage == "bad_entry_refined_exit"]
    assert candidate and candidate[-1]["exclusion_reason"] == "peak_recovered"
    assert not refined_exit
    assert not sell_calls
    assert stock["status"] == "HOLDING"


def test_scalp_soft_stop_micro_grace_expires_to_soft_stop(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True,
        SCALP_SOFT_STOP_MICRO_GRACE_SEC=20,
        SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0,
    )
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10000}
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
        "id": 17,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
        "soft_stop_micro_grace_started_at": state_handlers.time.time() - 21,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9840, "orderbook": {"bids": [{"price": 9840, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_soft_stop_pct"
    assert exit_logs and exit_logs[-1]["exit_rule"] == "scalp_soft_stop_pct"


def test_scalp_soft_stop_micro_grace_extension_delays_near_threshold_exit(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True,
        SCALP_SOFT_STOP_MICRO_GRACE_SEC=20,
        SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0,
        SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_ENABLED=True,
        SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_SEC=10,
        SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_BUFFER_PCT=0.20,
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
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: exit_calls.append(args) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )

    stock = {
        "id": 171,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "rt_ai_prob": 0.50,
        "soft_stop_micro_grace_started_at": state_handlers.time.time() - 24,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9860, "orderbook": {"bids": [{"price": 9860, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    grace_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_micro_grace"]
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert stock["status"] == "HOLDING"
    assert stock["soft_stop_micro_grace_extension_used"] is True
    assert grace_logs
    assert grace_logs[-1]["extension_used"] is True
    assert grace_logs[-1]["extension_sec"] == 10
    assert not exit_logs
    assert not exit_calls


def _install_soft_stop_expert_test_doubles(monkeypatch):
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
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: exit_calls.append(args) or {"return_code": "0", "ord_no": "S1"},
    )
    monkeypatch.setattr(
        state_handlers,
        "can_consider_scale_in",
        lambda *args, **kwargs: {"allowed": False, "reason": "test_block"},
    )
    return pipeline_logs, exit_calls


def _soft_stop_expert_config(**overrides):
    return replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True,
        SCALP_SOFT_STOP_MICRO_GRACE_SEC=20,
        SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0,
        SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=True,
        SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT="",
        SCALP_SOFT_STOP_ABSORPTION_EXTENSION_SEC=20,
        SCALP_SOFT_STOP_ABSORPTION_MIN_SCORE=3,
        SCALP_SOFT_STOP_ABSORPTION_MAX_EXTENSIONS=1,
        **overrides,
    )


def _soft_stop_expert_stock(**overrides):
    stock = {
        "id": 172,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "buy_qty": 10,
        "rt_ai_prob": 0.60,
        "soft_stop_micro_grace_started_at": state_handlers.time.time() - 21,
        "last_reversal_features": {
            "buy_pressure_10t": 62.0,
            "tick_acceleration_ratio": 1.05,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -2.0,
            "net_aggressive_delta_10t": 300,
            "same_price_buy_absorption": 3,
            "microprice_edge_bp": 1.5,
            "top3_depth_ratio": 1.05,
        },
    }
    stock.update(overrides)
    return stock


def test_soft_stop_expert_absorption_extends_after_micro_grace(monkeypatch):
    state_handlers.TRADING_RULES = _soft_stop_expert_config()
    pipeline_logs, exit_calls = _install_soft_stop_expert_test_doubles(monkeypatch)

    stock = _soft_stop_expert_stock()

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9840, "orderbook": {"bids": [{"price": 9840, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    extend_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_absorption_extend"]
    shadow_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_expert_shadow"]
    adverse_logs = [fields for stage, fields in pipeline_logs if stage == "adverse_fill_observed"]
    exit_logs = [fields for stage, fields in pipeline_logs if stage == "exit_signal"]
    assert stock["status"] == "HOLDING"
    assert stock["soft_stop_absorption_extension_used"] is True
    assert extend_logs and extend_logs[-1]["absorption_score"] >= 3
    assert shadow_logs and shadow_logs[-1]["shadow_only"] is True
    assert adverse_logs and adverse_logs[-1]["observe_only"] is True
    assert not exit_logs
    assert not exit_calls


def test_soft_stop_expert_thesis_veto_blocks_absorption_extension(monkeypatch):
    state_handlers.TRADING_RULES = _soft_stop_expert_config()
    pipeline_logs, exit_calls = _install_soft_stop_expert_test_doubles(monkeypatch)

    stock = _soft_stop_expert_stock(
        last_reversal_features={
            "buy_pressure_10t": 70.0,
            "tick_acceleration_ratio": 1.10,
            "large_sell_print_detected": True,
            "curr_vs_micro_vwap_bp": -1.0,
            "net_aggressive_delta_10t": 400,
            "same_price_buy_absorption": 4,
            "microprice_edge_bp": 2.0,
            "top3_depth_ratio": 1.00,
        }
    )

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9840, "orderbook": {"bids": [{"price": 9840, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    probe_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_absorption_probe"]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_soft_stop_pct"
    assert probe_logs and probe_logs[-1]["thesis_invalidated"] is True
    assert probe_logs[-1]["exclusion_reason"] == "large_sell_print"
    assert exit_calls


def test_soft_stop_expert_excludes_reversal_add_used_position(monkeypatch):
    state_handlers.TRADING_RULES = _soft_stop_expert_config()
    pipeline_logs, exit_calls = _install_soft_stop_expert_test_doubles(monkeypatch)

    stock = _soft_stop_expert_stock(reversal_add_used=True)

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9840, "orderbook": {"bids": [{"price": 9840, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    probe_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_absorption_probe"]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_soft_stop_pct"
    assert probe_logs and probe_logs[-1]["exclusion_reason"] == "reversal_add_used"
    assert exit_calls


def test_soft_stop_expert_emergency_keeps_immediate_exit(monkeypatch):
    state_handlers.TRADING_RULES = _soft_stop_expert_config()
    pipeline_logs, exit_calls = _install_soft_stop_expert_test_doubles(monkeypatch)

    stock = _soft_stop_expert_stock()

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 9790, "orderbook": {"bids": [{"price": 9790, "volume": 1000}]}},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    probe_logs = [fields for stage, fields in pipeline_logs if stage == "soft_stop_absorption_probe"]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["last_exit_rule"] == "scalp_soft_stop_pct"
    assert probe_logs and probe_logs[-1]["exclusion_reason"] == "emergency_pct"
    assert exit_calls


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


def test_hard_time_stop_shadow_skips_completed_position(monkeypatch):
    pipeline_logs = []

    def fake_log_holding_pipeline(stock, code, stage, **fields):
        pipeline_logs.append((stage, fields))

    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", fake_log_holding_pipeline)

    state_handlers._emit_scalp_hard_time_stop_shadow(
        stock={
            "status": "COMPLETED",
            "buy_qty": 0,
            "entry_mode": "normal",
            "position_tag": "SCALP_BASE",
        },
        code="123456",
        held_sec=240,
        profit_rate=-0.9,
        peak_profit=0.1,
        current_ai_score=32.0,
        ai_exit_min_loss_pct=-0.7,
    )

    assert pipeline_logs == []


def test_holding_fast_reuse_band_logs_review_for_near_safe_profit(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    state_handlers.TRADING_RULES = replace(CONFIG, SCALE_IN_REQUIRE_HISTORY_TABLE=False)
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 10080}
    state_handlers.LAST_AI_CALL_TIMES = {"123456": state_handlers.time.time() - 25}
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

    fast_reuse_logs = [fields for stage, fields in pipeline_logs if stage == "ai_holding_fast_reuse_band"]

    assert fast_reuse_logs
    assert fast_reuse_logs[-1]["action"] == "review"
    assert fast_reuse_logs[-1]["near_safe_profit"] is True
    assert fast_reuse_logs[-1]["near_ai_exit"] is False
    assert fast_reuse_logs[-1]["telemetry_only"] is True


# ─────────────────────────────────────────────
#  reversal_add TC-1 ~ TC-10
# ─────────────────────────────────────────────

def _reversal_add_stock(overrides=None):
    """정상 트리거 조건의 기본 stock 픽스처."""
    base = {
        "reversal_add_state": "STAGNATION",
        "reversal_add_used": False,
        "reversal_add_profit_floor": -0.30,
        "reversal_add_ai_bottom": 42,
        "reversal_add_ai_history": [44, 41, 42, 45],
        "reversal_add_executed_at": 0.0,
        "reversal_add_entry_avg_price": 0.0,
        "last_reversal_features": {
            "buy_pressure_10t": 60.0,
            "tick_acceleration_ratio": 1.05,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -2.0,
        },
    }
    if overrides:
        base.update(overrides)
    return base


def _reversal_add_rules(**kwargs):
    """REVERSAL_ADD_ENABLED=True + 기본값을 적용한 TRADING_RULES 반환."""
    from src.utils.constants import TRADING_RULES as CONFIG
    return replace(
        CONFIG,
        REVERSAL_ADD_ENABLED=True,
        REVERSAL_ADD_PNL_MIN=-0.70,
        REVERSAL_ADD_PNL_MAX=-0.10,
        REVERSAL_ADD_MIN_HOLD_SEC=20,
        REVERSAL_ADD_MAX_HOLD_SEC=180,
        REVERSAL_ADD_MIN_AI_SCORE=60,
        REVERSAL_ADD_MIN_AI_RECOVERY_DELTA=15,
        REVERSAL_ADD_MIN_BUY_PRESSURE=55.0,
        REVERSAL_ADD_MIN_TICK_ACCEL=0.95,
        REVERSAL_ADD_VWAP_BP_MIN=-5.0,
        REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN=0.05,
        **kwargs,
    )


# TC-1: 토글 OFF → 미트리거
def test_reversal_add_tc1_toggle_off():
    stock = _reversal_add_stock()
    from src.utils.constants import TRADING_RULES as CONFIG
    original = scale_in.TRADING_RULES
    scale_in.TRADING_RULES = replace(CONFIG, REVERSAL_ADD_ENABLED=False)
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=65, held_sec=50)
        assert result["should_add"] is False
        assert result["reason"] == "reversal_add_disabled"
    finally:
        scale_in.TRADING_RULES = original


# TC-2: PnL 범위 이탈 → 미트리거
def test_reversal_add_tc2_pnl_out_of_range():
    stock = _reversal_add_stock()
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.75, current_ai_score=65, held_sec=50)
        assert result["should_add"] is False
        assert "pnl_out_of_range" in result["reason"]
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-3: AI 고착 저점 (std ≤ 2, avg < 45) → 차단
def test_reversal_add_tc3_ai_stuck_at_bottom():
    stock = _reversal_add_stock({
        "reversal_add_ai_history": [40, 41, 40, 41],
        "reversal_add_ai_bottom": 35,
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        # ai_bottom=35, current=35+15=50 → recovering_delta OK, but avg(40,41,40,41)=40.5 < 45, std≈0.5 ≤ 2 → stuck
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=62, held_sec=50)
        assert result["should_add"] is False
        assert result["reason"] == "ai_stuck_at_bottom"
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-4: AI 회복 없음 (바닥 대비 +14pt, 직전 2틱도 상승 아님) → 차단
def test_reversal_add_tc4_ai_not_recovering():
    stock = _reversal_add_stock({
        "reversal_add_ai_bottom": 50,
        # ai_hist[-1]=53, ai_hist[-2]=55 → 53 > 55 = False → 2연속 상승 아님
        "reversal_add_ai_history": [50, 52, 55, 53],
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        # recovering_delta: 64 >= 50+15=65 → False
        # recovering_consec: ai_hist[-1]=53 > ai_hist[-2]=55 → False
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=64, held_sec=50)
        assert result["should_add"] is False
        assert result["reason"] == "ai_not_recovering"
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-5: 수급 조건 2/4 충족 → 차단
def test_reversal_add_tc5_supply_conditions_not_met():
    stock = _reversal_add_stock({
        "reversal_add_ai_bottom": 42,
        "reversal_add_ai_history": [42, 44, 50, 55],
        "last_reversal_features": {
            "buy_pressure_10t": 40.0,        # 실패
            "tick_acceleration_ratio": 1.10,  # 통과
            "large_sell_print_detected": False,  # 통과
            "curr_vs_micro_vwap_bp": -10.0,  # 실패
        },
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=65, held_sec=50)
        assert result["should_add"] is False
        assert "supply_conditions_not_met" in result["reason"]
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-6: 정상 조건 모두 충족 → 트리거
def test_reversal_add_tc6_all_conditions_met():
    stock = _reversal_add_stock({
        "reversal_add_ai_bottom": 42,
        "reversal_add_ai_history": [42, 44, 50, 58],
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=65, held_sec=50)
        assert result["should_add"] is True
        assert result["add_type"] == "AVG_DOWN"
        assert result["reason"] == "reversal_add_ok"
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-7: 동일 포지션 재평가 허용 → one-shot guard 없음
def test_reversal_add_tc7_used_flag_does_not_block_retrigger():
    stock = _reversal_add_stock({
        "reversal_add_used": True,
        "reversal_add_ai_history": [42, 44, 50, 58],
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=65, held_sec=50)
        assert result["should_add"] is True
        assert result["reason"] == "reversal_add_ok"
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-8: 저점 갱신 → 차단
def test_reversal_add_tc8_low_broken():
    stock = _reversal_add_stock({
        "reversal_add_profit_floor": -0.30,
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        # floor=-0.30, margin=0.05 → -0.30 - 0.05 = -0.35, profit_rate=-0.40 < -0.35 → low_broken
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.40, current_ai_score=65, held_sec=50)
        assert result["should_add"] is False
        assert result["reason"] == "low_broken"
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-9: hold_sec 범위 이탈 → 차단
def test_reversal_add_tc9_hold_sec_out_of_range():
    stock = _reversal_add_stock()
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=65, held_sec=5)
        assert result["should_add"] is False
        assert "hold_sec_out_of_range" in result["reason"]
    finally:
        scale_in.TRADING_RULES = CONFIG


def test_reversal_add_tc11_extended_intraday_window_allows_deeper_loss_and_longer_hold():
    stock = _reversal_add_stock({
        "reversal_add_ai_bottom": 42,
        "reversal_add_ai_history": [42, 44, 50, 58],
        "reversal_add_profit_floor": -0.58,
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.60, current_ai_score=65, held_sec=150)
        assert result["should_add"] is True
        assert result["reason"] == "reversal_add_ok"
    finally:
        scale_in.TRADING_RULES = CONFIG


# TC-10: _extract_scalping_features 없는 엔진 → buy_pressure만으로 판단 (feat={} 시)
def test_reversal_add_tc10_no_features_engine_buy_pressure_only():
    # last_reversal_features가 비어있는 경우 buy_pressure 기본값(50)으로 판단 → 55 미만 → 차단
    stock = _reversal_add_stock({
        "last_reversal_features": {},
        "reversal_add_ai_bottom": 42,
        "reversal_add_ai_history": [42, 44, 50, 58],
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=65, held_sec=50)
        # feat={} 이면 else 분기: buy_pressure_10t=50.0 < 55 → buy_pressure_not_met
        assert result["should_add"] is False
        assert result["reason"] == "buy_pressure_not_met(no_features)"
    finally:
        scale_in.TRADING_RULES = CONFIG


def test_reversal_add_probe_contains_all_predicates_when_blocked():
    stock = _reversal_add_stock({
        "last_reversal_features": {
            "buy_pressure_10t": 52.0,
            "tick_acceleration_ratio": 0.91,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": -7.0,
        },
        "reversal_add_ai_bottom": 40,
        "reversal_add_ai_history": [40, 44, 48],
        "reversal_add_profit_floor": -0.30,
    })
    from src.utils.constants import TRADING_RULES as CONFIG
    scale_in.TRADING_RULES = _reversal_add_rules()
    try:
        result = scale_in.evaluate_scalping_reversal_add(stock, profit_rate=-0.25, current_ai_score=60, held_sec=50)
        probe = result["probe"]
        assert result["should_add"] is False
        assert result["reason"].startswith("supply_conditions_not_met")
        assert probe["pnl_ok"] is True
        assert probe["hold_ok"] is True
        assert probe["low_floor_ok"] is True
        assert probe["ai_score_ok"] is True
        assert probe["ai_recover_ok"] is True
        assert probe["buy_pressure_ok"] is False
        assert probe["tick_accel_ok"] is False
        assert probe["micro_vwap_ok"] is False
        assert probe["supply_ok"] is False
    finally:
        scale_in.TRADING_RULES = CONFIG


def test_resolve_sell_order_sign_trailing_negative_treated_as_loss():
    assert state_handlers._resolve_sell_order_sign("TRAILING", -0.01) == "📉 [손절 주문]"
    assert state_handlers._resolve_sell_order_sign("TRAILING", 0.0) == "📉 [손절 주문]"
    assert state_handlers._resolve_sell_order_sign("TRAILING", 0.15) == "🎊 [익절 주문]"


def test_same_symbol_loss_reentry_cooldown_targets_loss_exits_only():
    from src.utils.constants import TRADING_RULES as CONFIG

    class _RulesProxy:
        def __init__(self, base, **overrides):
            self._base = base
            self._overrides = overrides

        def __getattr__(self, name):
            if name in self._overrides:
                return self._overrides[name]
            return getattr(self._base, name)

    state_handlers.TRADING_RULES = _RulesProxy(
        CONFIG,
        SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_ENABLED=True,
        SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
    )

    assert state_handlers._resolve_same_symbol_loss_reentry_cooldown_sec("scalp_soft_stop_pct", -1.5) == 3600
    assert state_handlers._resolve_same_symbol_loss_reentry_cooldown_sec("protect_trailing_stop", -0.01) == 3600
    assert (
        state_handlers._resolve_same_symbol_loss_reentry_cooldown_sec(
            "scalp_bad_entry_refined_canary",
            -1.2,
        )
        == 3600
    )
    assert state_handlers._resolve_same_symbol_loss_reentry_cooldown_sec("scalp_trailing_take_profit", 1.2) == 0
    assert state_handlers._resolve_same_symbol_loss_reentry_cooldown_sec("protect_trailing_stop", 0.19) == 0


def test_emit_same_symbol_soft_stop_cooldown_shadow_once(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class _RulesProxy:
        def __init__(self, base, **overrides):
            self._base = base
            self._overrides = overrides

        def __getattr__(self, name):
            if name in self._overrides:
                return self._overrides[name]
            return getattr(self._base, name)

    state_handlers.TRADING_RULES = _RulesProxy(
        CONFIG,
        SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED=True,
        SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_SEC=600,
    )
    state_handlers._SAME_SYMBOL_SOFT_STOP_TS = {}
    logs = []

    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {"id": 101, "name": "TEST"}
    now_ts = time.time()
    state_handlers._mark_same_symbol_soft_stop("123456", now_ts=now_ts - 30)

    state_handlers._emit_same_symbol_soft_stop_cooldown_shadow(
        stock=stock,
        code="123456",
        now_ts=now_ts,
        runtime_remaining_sec=200,
    )
    state_handlers._emit_same_symbol_soft_stop_cooldown_shadow(
        stock=stock,
        code="123456",
        now_ts=now_ts + 1,
        runtime_remaining_sec=199,
    )

    assert len(logs) == 1
    assert logs[0][0] == "same_symbol_soft_stop_cooldown_shadow"
    assert logs[0][1]["shadow_only"] is True
    assert logs[0][1]["would_block"] is True


def test_emit_partial_only_timeout_shadow_logs_when_partial_stuck(monkeypatch):
    from src.utils.constants import TRADING_RULES as CONFIG

    class _RulesProxy:
        def __init__(self, base, **overrides):
            self._base = base
            self._overrides = overrides

        def __getattr__(self, name):
            if name in self._overrides:
                return self._overrides[name]
            return getattr(self._base, name)

    state_handlers.TRADING_RULES = _RulesProxy(
        CONFIG,
        SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_ENABLED=True,
        SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_SEC=180,
        SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_MAX_PEAK_PCT=0.20,
    )
    logs = []

    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 102,
        "name": "TEST",
        "entry_requested_qty": 3,
        "buy_qty": 1,
        "entry_mode": "split",
        "_split_entry_rebase_shadow_count": 1,
    }

    state_handlers._emit_partial_only_timeout_shadow(
        stock=stock,
        code="123456",
        held_sec=210,
        profit_rate=-0.32,
        peak_profit=0.08,
        current_ai_score=43.0,
    )

    assert len(logs) == 1
    assert logs[0][0] == "partial_only_timeout_shadow"
    assert logs[0][1]["shadow_only"] is True
    assert logs[0][1]["requested_qty"] == 3
    assert logs[0][1]["buy_qty"] == 1
