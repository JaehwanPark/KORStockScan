from dataclasses import replace

import pytest

import src.engine.kiwoom_sniper_v2 as sniper_runtime
import src.engine.sniper_performance_tuning_report as perf_report
import src.engine.sniper_scale_in as scale_in
import src.engine.sniper_state_handlers as state_handlers
from src.engine.daily_threshold_cycle_report import build_daily_threshold_cycle_report
from src.utils.constants import TRADING_RULES as CONFIG
from src.utils.threshold_cycle_registry import threshold_family_for_stage


class FakeEventBus:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload):
        self.published.append((topic, payload))


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SCALP_LIVE_SIMULATOR_ENABLED=True,
        SCALP_LIVE_SIMULATOR_QTY=1,
        SCALP_LIVE_SIMULATOR_FILL_POLICY="signal_inclusive_best_ask_v1",
        SCALP_LIVE_SIMULATOR_ENTRY_TIMEOUT_SEC=90,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "LAST_LOG_TIMES", {})
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", tmp_path / "scalp_live_sim_state.json")
    monkeypatch.setattr(state_handlers, "record_sim_post_sell_candidate", lambda **kwargs: None)
    captured_pipeline_events = []
    monkeypatch.setattr(
        state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, record_id=None, fields=None: captured_pipeline_events.append(
            {
                "pipeline": pipeline,
                "stock_name": name,
                "stock_code": code,
                "stage": stage,
                "record_id": record_id,
                "fields": fields or {},
            }
        ),
    )
    return captured_pipeline_events


def test_scalp_simulator_arms_and_fills_without_real_buy_order(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("real buy order must not be called"),
    )

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
        "latency_state": "DANGER",
    }
    ws_data = {
        "curr": 9_990,
        "orderbook": {
            "asks": [{"price": 9_990}],
            "bids": [{"price": 9_980}],
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        ws_data,
        runtime,
    )

    assert len(state_handlers.ACTIVE_TARGETS) == 1
    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["status"] == "HOLDING"
    assert sim_target["simulation_book"] == "scalp_ai_buy_all"
    assert sim_target["simulation_fill_policy"] == "signal_inclusive_best_ask_v1"
    assert sim_target["actual_order_submitted"] is False
    assert sim_target["msg_audience"] == "ADMIN_ONLY"
    assert sim_target["buy_qty"] == 1
    assert sim_target["buy_price"] == 9_990
    assert [stage for stage, _ in logs] == [
        "scalp_sim_entry_armed",
        "scalp_sim_buy_order_virtual_pending",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_holding_started",
    ]
    assert state_handlers.EVENT_BUS.published == [
        ("COMMAND_WS_REG", {"codes": ["123456"], "source": "scalp_live_simulator"})
    ]
    fill_event = next(fields for stage, fields in logs if stage == "scalp_sim_buy_order_assumed_filled")
    assert fill_event["fill_source"] == "best_ask"
    assert fill_event["would_limit_fill"] is True


def test_scalp_simulator_applies_entry_ai_price_canary_without_real_order(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("real buy order must not be called"),
    )

    class FakeAiEngine:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "IMPROVE_LIMIT",
                "order_price": 10_000,
                "confidence": 90,
                "reason": "sim entry price test",
                "max_wait_sec": 30,
                "ai_parse_ok": True,
                "openai_endpoint_name": "entry_price",
                "openai_transport_mode": "responses_ws",
                "openai_ws_used": True,
                "openai_request_id": "sim-entry-price-1",
            }

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_020,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
        "latency_state": "DANGER",
    }
    ws_data = {
        "curr": 10_020,
        "orderbook": {
            "asks": [{"price": 10_030}],
            "bids": [{"price": 9_990}],
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        ws_data,
        runtime,
        ai_engine=FakeAiEngine(),
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["actual_order_submitted"] is False
    assert sim_target["entry_ai_price_canary_applied"] is True
    assert sim_target["scalp_sim_entry_limit_price"] == 10_000
    assert sim_target["buy_price"] == 10_030
    applied = next(fields for stage, fields in logs if stage == "entry_ai_price_canary_applied")
    assert applied["openai_endpoint_name"] == "entry_price"
    assert applied["openai_transport_mode"] == "responses_ws"
    sim_applied = next(fields for stage, fields in logs if stage == "scalp_sim_entry_ai_price_applied")
    assert sim_applied["runtime_effect"] == "simulated_entry_price_only"
    pending = next(fields for stage, fields in logs if stage == "scalp_sim_buy_order_virtual_pending")
    assert pending["limit_price"] == 10_000


def test_scalp_simulator_blocks_stale_passive_probe_before_virtual_submit(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_history_ka10003", lambda *args, **kwargs: [])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_minute_candles_ka10080", lambda *args, **kwargs: [])
    monkeypatch.setattr(state_handlers.kiwoom_utils, "get_tick_size", lambda price: 10)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("real buy order must not be called"),
    )

    class FakeAiEngine:
        def evaluate_scalping_entry_price(self, *args, **kwargs):
            return {
                "action": "USE_DEFENSIVE",
                "confidence": 90,
                "reason": "passive probe test",
                "max_wait_sec": 60,
                "ai_parse_ok": True,
                "openai_endpoint_name": "entry_price",
                "openai_transport_mode": "responses_ws",
                "openai_ws_used": True,
                "openai_request_id": "sim-entry-price-stale",
            }

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 80,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
        "latency_state": "DANGER",
    }
    ws_data = {
        "curr": 10_020,
        "last_ws_update_ts": 990.0,
        "orderbook": {
            "asks": [{"price": 10_030}],
            "bids": [{"price": 10_010}],
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        ws_data,
        runtime,
        ai_engine=FakeAiEngine(),
    )

    assert state_handlers.ACTIVE_TARGETS == []
    stages = [stage for stage, _ in logs]
    assert "scalp_sim_entry_submit_revalidation_block" in stages
    assert "scalp_sim_buy_order_virtual_pending" not in stages
    block = next(fields for stage, fields in logs if stage == "scalp_sim_entry_submit_revalidation_block")
    assert block["block_reason"] == "stale_context_or_quote"
    assert block["entry_order_lifecycle"] == "passive_probe"
    assert block["actual_order_submitted"] is False


def test_scalp_simulator_entry_uses_virtual_budget_with_live_qty_formula(monkeypatch):
    logs = []
    rules = replace(CONFIG, SCALP_LIVE_SIMULATOR_QTY=0, SCALPING_MAX_BUY_BUDGET_KRW=1_200_000)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_deposit",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("scalp sim must not read real deposit")),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
        "ratio": 0.22,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_000}], "bids": [{"price": 9_990}]}},
        runtime,
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["buy_qty"] == 114
    assert sim_target["scalp_sim_entry_qty_source"] == "sim_virtual_budget_dynamic_formula"
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["qty"] == 114
    assert armed["qty_reason"] == "sim_uses_virtual_budget_with_live_qty_formula"
    assert armed["virtual_budget_override"] is True
    assert armed["virtual_budget_krw"] == 10_000_000
    assert armed["target_budget"] == 1_200_000
    assert armed["safe_budget"] == 1_140_000
    assert armed["virtual_notional_used_krw"] == 1_140_000
    assert armed["budget_authority"] == "sim_virtual_not_real_orderable_amount"


def test_scalp_simulator_entry_ignores_real_orderable_amount_when_unaffordable(monkeypatch):
    logs = []
    rules = replace(CONFIG, SCALP_LIVE_SIMULATOR_QTY=0, SCALPING_MAX_BUY_BUDGET_KRW=0)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 296_988)
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 101,
        "name": "HIGHPRICE",
        "code": "196170",
        "strategy": "SCALPING",
        "target_buy_price": 382_500,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
        "ratio": 1.0,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "196170",
        {"curr": 382_500, "orderbook": {"asks": [{"price": 382_500}], "bids": [{"price": 382_000}]}},
        runtime,
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["buy_qty"] == 24
    assert sim_target["scalp_sim_entry_qty_source"] == "sim_virtual_budget_dynamic_formula"
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["qty"] == 24
    assert armed["virtual_budget_override"] is True
    assert armed["virtual_budget_krw"] == 10_000_000
    assert armed["safe_budget"] == 9_500_000
    assert armed["virtual_notional_used_krw"] == 9_180_000
    assert armed["budget_authority"] == "sim_virtual_not_real_orderable_amount"


def test_scalp_simulator_signal_inclusive_fill_does_not_wait_for_limit_touch(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 80.0,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {
            "curr": 10_020,
            "orderbook": {
                "asks": [{"price": 10_030}],
                "bids": [{"price": 10_010}],
            },
        },
        runtime,
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["status"] == "HOLDING"
    assert sim_target["buy_price"] == 10_030
    fill_event = next(fields for stage, fields in logs if stage == "scalp_sim_buy_order_assumed_filled")
    assert fill_event["fill_source"] == "best_ask"
    assert fill_event["would_limit_fill"] is False
    assert fill_event["limit_price"] == 10_000


def test_swing_dry_run_gatekeeper_report_is_admin_only(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)

    sniper_runtime._publish_gatekeeper_report(
        {"name": "SWING", "strategy": "KOSPI_ML"},
        "654321",
        {"action_label": "BUY", "report": "ok"},
        True,
    )

    assert event_bus.published[0][0] == "TELEGRAM_BROADCAST"
    assert event_bus.published[0][1]["audience"] == "ADMIN_ONLY"


def test_scalp_simulator_duplicate_buy_signal_does_not_create_second_position(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    state_handlers.ACTIVE_TARGETS.append(
        {
            "code": "123456",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "scalp_live_simulator": True,
            "sim_record_id": "SIM-1",
        }
    )

    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 80.0,
    }

    assert not state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990},
        runtime,
    )
    assert len(state_handlers.ACTIVE_TARGETS) == 1
    assert logs[0][0] == "scalp_sim_duplicate_buy_signal"


def test_scalp_simulator_includes_low_score_triggered_buy_signal():
    stock = {
        "id": 101,
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 74.9,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990},
        runtime,
    )
    assert len(state_handlers.ACTIVE_TARGETS) == 1
    assert state_handlers.ACTIVE_TARGETS[0]["status"] == "HOLDING"
    assert state_handlers.ACTIVE_TARGETS[0]["buy_price"] == 9_990


def test_scalp_simulator_preset_tp_sell_does_not_call_real_sell(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: pytest.fail("real sell order must not be called"),
    )

    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "order_time": 1_000.0,
        "holding_started_at": 1_000.0,
        "exit_mode": "SCALP_PRESET_TP",
        "preset_tp_price": 10_150,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    state_handlers.handle_holding_state(
        stock,
        "123456",
        {
            "curr": 10_150,
            "orderbook": {
                "asks": [{"price": 10_160}],
                "bids": [{"price": 10_140}],
            },
        },
        admin_id=None,
        market_regime="NEUTRAL",
        now_ts=1_060.0,
    )

    assert stock["status"] == "COMPLETED"
    assert stock["sell_price"] == 10_150
    assert stock["actual_order_submitted"] is False
    assert any(stage == "exit_signal" for stage, _ in holding_logs)
    assert any(stage == "scalp_sim_sell_order_assumed_filled" for stage, _ in holding_logs)


def test_scalp_simulator_sell_profit_uses_assumed_fill_price(monkeypatch):
    holding_logs = []
    sim_post_sell_candidates = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "record_sim_post_sell_candidate",
        lambda **kwargs: sim_post_sell_candidates.append(kwargs),
    )
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    assert state_handlers._complete_scalp_simulated_sell(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 10_150,
            "orderbook": {
                "asks": [{"price": 10_160}],
                "bids": [{"price": 10_130}],
            },
        },
        curr_price=10_150,
        now_ts=1_060.0,
        sell_reason_type="PROFIT",
        exit_rule="test_exit",
        profit_rate=state_handlers.calculate_net_profit_rate(10_000, 10_150),
    )

    expected_profit = state_handlers.calculate_net_profit_rate(10_000, 10_130)
    assert stock["sell_price"] == 10_130
    assert stock["profit_rate"] == expected_profit
    event = next(fields for stage, fields in holding_logs if stage == "scalp_sim_sell_order_assumed_filled")
    assert event["profit_rate"] == f"{expected_profit:+.2f}"
    assert event["trigger_profit_rate"] == f"{state_handlers.calculate_net_profit_rate(10_000, 10_150):+.2f}"
    assert len(sim_post_sell_candidates) == 1
    assert sim_post_sell_candidates[0]["sim_record_id"] == "SIM-1"
    assert sim_post_sell_candidates[0]["sell_price"] == 10_130
    assert sim_post_sell_candidates[0]["profit_rate"] == expected_profit


def test_scalp_simulator_scale_in_does_not_call_real_buy(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("real add buy order must not be called"),
    )
    monkeypatch.setattr(
        state_handlers,
        "resolve_scale_in_order_price",
        lambda **kwargs: {
            "allowed": True,
            "order_price": 9_990,
            "reason": "test",
            "price_source": "best_bid",
            "best_bid": 9_990,
            "best_ask": 10_000,
            "spread_bps": 10.0,
            "curr_vs_micro_vwap_bp": 0.0,
            "max_spread_bps": 80.0,
            "max_micro_vwap_bps": 60.0,
        },
    )
    monkeypatch.setattr(
        state_handlers,
        "describe_dynamic_scale_in_qty",
        lambda **kwargs: {
            "qty": 1,
            "template_qty": 1,
            "would_qty": 1,
            "effective_qty": 1,
            "cap_qty": 1,
            "floor_applied": False,
            "qty_reason": "test_qty",
        },
    )

    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    res = state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 9_990,
            "orderbook": {
                "asks": [{"price": 9_990}],
                "bids": [{"price": 9_980}],
            },
        },
        action={"add_type": "AVG_DOWN", "reason": "test"},
        admin_id=None,
    )

    assert res["simulated_order"] is True
    assert stock["buy_qty"] == 2
    assert stock["actual_order_submitted"] is False
    assert any(stage == "scalp_sim_scale_in_order_assumed_filled" for stage, _ in holding_logs)


def test_scalp_simulator_scale_in_dynamic_qty_ignores_real_one_share_cap(monkeypatch):
    rules = replace(CONFIG, SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=True, SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP=1)
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 10,
        "hard_stop_price": 9_000,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "actual_order_submitted": False,
    }

    details = scale_in.describe_dynamic_scale_in_qty(
        stock=stock,
        resolved_price=10_000,
        deposit=10_000_000,
        add_type="AVG_DOWN",
        strategy="SCALPING",
        add_reason="reversal_add_ok",
        price_resolution={"allowed": True},
        action={"reason": "reversal_add_ok"},
    )

    assert details["sim_uncapped_qty"] is True
    assert details["effective_qty_cap"] == 0
    assert details["would_qty"] == 3
    assert details["effective_qty"] == 3
    assert details["qty"] == 3


def test_scalp_simulator_scale_in_uses_virtual_budget_not_real_deposit(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_deposit",
        lambda *args, **kwargs: pytest.fail("scalp sim scale-in must not read real deposit"),
    )
    monkeypatch.setattr(
        state_handlers,
        "resolve_scale_in_order_price",
        lambda **kwargs: {
            "allowed": True,
            "order_price": 9_990,
            "reason": "test",
            "price_source": "best_bid",
            "best_bid": 9_990,
            "best_ask": 10_000,
            "spread_bps": 10.0,
            "curr_vs_micro_vwap_bp": 0.0,
            "max_spread_bps": 80.0,
            "max_micro_vwap_bps": 60.0,
        },
    )

    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 10,
        "hard_stop_price": 9_000,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "actual_order_submitted": False,
    }

    res = state_handlers.execute_scale_in_order(
        stock=stock,
        code="123456",
        ws_data={
            "curr": 9_990,
            "orderbook": {
                "asks": [{"price": 9_990}],
                "bids": [{"price": 9_980}],
            },
        },
        action={"add_type": "AVG_DOWN", "reason": "reversal_add_ok"},
        admin_id=None,
    )

    assert res["simulated_order"] is True
    assert stock["actual_order_submitted"] is False
    filled = next(fields for stage, fields in holding_logs if stage == "scalp_sim_scale_in_order_assumed_filled")
    assert filled["virtual_budget_override"] is True
    assert filled["virtual_budget_krw"] == 10_000_000
    assert filled["budget_authority"] == "sim_virtual_not_real_orderable_amount"


def test_swing_probe_scale_in_uses_virtual_budget_not_real_deposit(monkeypatch):
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_deposit",
        lambda *args, **kwargs: pytest.fail("swing probe scale-in must not read real deposit"),
    )
    monkeypatch.setattr(
        state_handlers,
        "resolve_scale_in_order_price",
        lambda **kwargs: {
            "allowed": True,
            "order_price": 0,
            "reason": "market_best",
            "price_source": "market_best",
            "best_bid": 9_990,
            "best_ask": 10_000,
            "spread_bps": 10.0,
            "curr_vs_micro_vwap_bp": 0.0,
            "max_spread_bps": 80.0,
            "max_micro_vwap_bps": 60.0,
        },
    )

    stock = {
        "name": "SWING",
        "code": "654321",
        "strategy": "KOSPI_ML",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 10,
        "simulation_book": "swing_intraday_live_equiv_probe",
        "swing_live_order_dry_run": True,
        "swing_intraday_probe": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "probe_id": "PROBE1",
    }

    res = state_handlers.execute_scale_in_order(
        stock=stock,
        code="654321",
        ws_data={"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        action={"add_type": "AVG_DOWN", "reason": "swing_avg_down_ok"},
        admin_id=None,
    )

    assert res["simulated_order"] is True
    assert stock["actual_order_submitted"] is False
    filled = next(fields for stage, fields in holding_logs if stage == "swing_probe_scale_in_order_assumed_filled")
    assert filled["virtual_budget_override"] is True
    assert filled["virtual_budget_krw"] == 10_000_000
    assert filled["budget_authority"] == "sim_virtual_not_real_orderable_amount"


def test_scalp_simulator_threshold_stages_are_included():
    assert threshold_family_for_stage("pre_submit_liquidity_guard_block") == "liquidity_pre_submit_guard_p1"
    assert (
        threshold_family_for_stage("pre_submit_overbought_pullback_guard_block")
        == "overbought_pullback_guard_p1"
    )
    assert threshold_family_for_stage("scalp_sim_entry_armed") == "entry_mechanical_momentum"
    assert threshold_family_for_stage("scalp_sim_entry_ai_price_applied") == "pre_submit_price_guard"
    assert threshold_family_for_stage("scalp_sim_entry_ai_price_skip_order") == "pre_submit_price_guard"
    assert threshold_family_for_stage("scalp_sim_entry_submit_revalidation_warning") == "pre_submit_price_guard"
    assert threshold_family_for_stage("scalp_sim_entry_submit_revalidation_block") == "pre_submit_price_guard"
    assert threshold_family_for_stage("scalp_sim_buy_order_assumed_filled") == "pre_submit_price_guard"
    assert threshold_family_for_stage("scalp_sim_sell_order_assumed_filled") == "statistical_action_weight"


def test_ws_prune_retains_active_scalp_simulator_consumer(monkeypatch):
    class FakeWS:
        subscribed_codes = {"123456"}

    fake_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "WS_MANAGER", FakeWS())
    monkeypatch.setattr(sniper_runtime, "event_bus", fake_bus)
    monkeypatch.setattr(sniper_runtime, "should_retain_ws_subscription", lambda *args, **kwargs: False)

    sniper_runtime._prune_ws_subscriptions_for_inactive_targets(
        [
            {
                "code": "123456",
                "strategy": "SCALPING",
                "status": "SCALP_SIM_PENDING_BUY",
                "simulation_book": "scalp_ai_buy_all",
                "scalp_live_simulator": True,
            }
        ]
    )

    assert fake_bus.published == []


def test_scalp_simulator_restore_skips_synthetic_state(monkeypatch, tmp_path):
    state_path = tmp_path / "scalp_live_sim_state.json"
    state_path.write_text(
        """
{
  "schema_version": 1,
  "simulation_book": "scalp_ai_buy_all",
  "active_positions": [
    {
      "code": "123456",
      "name": "TEST",
      "strategy": "SCALPING",
      "status": "HOLDING",
      "simulation_book": "scalp_ai_buy_all",
      "scalp_live_simulator": true,
      "sim_record_id": "SIM-TEST"
    },
    {
      "code": "005930",
      "name": "삼성전자",
      "strategy": "SCALPING",
      "status": "HOLDING",
      "simulation_book": "scalp_ai_buy_all",
      "scalp_live_simulator": true,
      "sim_record_id": "SIM-REAL"
    }
  ]
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", state_path)
    targets = []

    restored = state_handlers.restore_scalp_simulator_targets(targets)

    assert restored == 1
    assert [target["code"] for target in targets] == ["005930"]


def test_runtime_heartbeat_classifies_scalp_sim_as_non_real_holding():
    assert sniper_runtime._is_runtime_simulation_target(
        {
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": False,
        }
    )
    assert not sniper_runtime._is_runtime_simulation_target(
        {
            "status": "HOLDING",
            "code": "005930",
            "actual_order_submitted": True,
        }
    )


def test_daily_threshold_cycle_report_keeps_scalp_sim_completed_rows_diagnostic_only():
    target_date = "2026-05-11"

    def pipeline_loader(day):
        if day != target_date:
            return []
        return [
            {
                "event_type": "pipeline_event",
                "pipeline": "HOLDING_PIPELINE",
                "stage": "scalp_sim_sell_order_assumed_filled",
                "stock_name": "SIM",
                "stock_code": "123456",
                "record_id": None,
                "emitted_date": target_date,
                "fields": {
                    "simulation_book": "scalp_ai_buy_all",
                    "sim_record_id": "SIM-1",
                    "profit_rate": "+0.50",
                    "qty": "1",
                    "buy_price": "10000",
                    "assumed_fill_price": "10050",
                    "actual_order_submitted": "False",
                },
            }
        ]

    def completed_rows_loader(start_date, end_date):
        return [
            {
                "rec_date": target_date,
                "stock_code": "000001",
                "stock_name": "REAL",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "profit_rate": 0.2,
                "add_count": 0,
                "avg_down_count": 0,
                "pyramid_count": 0,
            }
        ]

    report = build_daily_threshold_cycle_report(
        target_date,
        pipeline_loader=pipeline_loader,
        report_source_loader=lambda _: {},
        completed_rows_loader=completed_rows_loader,
    )

    assert report["summary"]["real_completed_valid_rolling_7d"] == 1
    assert report["summary"]["sim_completed_valid_rolling_7d"] == 1
    assert report["summary"]["completed_valid_rolling_7d"] == 1
    assert report["completed_by_source"]["combined"]["sample"] == 2
    assert report["completed_by_source"]["sim"]["sample"] == 1
    assert report["completed_by_source"]["combined_authority"] == "diagnostic_only_not_family_candidate_input"
    assert report["scalp_simulator"]["sell_completed"] == 1


def test_performance_tuning_source_split_combines_real_and_scalp_sim():
    split = perf_report._build_completed_source_split(
        [
            {
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "profit_rate": 0.2,
            }
        ],
        [
            perf_report.PerfEvent(
                timestamp="2026-05-11T10:00:00",
                name="SIM",
                code="123456",
                stage="scalp_sim_sell_order_assumed_filled",
                fields={"profit_rate": "+0.50", "simulation_book": "scalp_ai_buy_all"},
                raw_line="",
            )
        ],
    )

    assert split["real"]["completed_rows"] == 1
    assert split["sim"]["completed_rows"] == 1
    assert split["combined"]["completed_rows"] == 2
    assert split["combined"]["avg_profit_rate"] == 0.35
    assert split["calibration_authority"] == "combined_equal_weight_no_sim_downweight"
