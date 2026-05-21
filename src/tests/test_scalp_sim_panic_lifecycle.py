import json
from dataclasses import replace
from datetime import datetime

import pytest

from src.engine import lifecycle_decision_matrix_runtime as runtime
from src.engine import lifecycle_decision_matrix as matrix
from src.engine import sniper_state_handlers as state_handlers
from src.utils.constants import TRADING_RULES as CONFIG


def _rules(**overrides):
    return replace(
        CONFIG,
        SCALP_SIM_PANIC_LIFECYCLE_ENABLED=True,
        SCALP_SIM_PANIC_FORCE_NOOP=False,
        SCALP_SIM_PANIC_PARTIAL_SELL_ENABLED=True,
        SCALP_SIM_PANIC_MIN_REMAINING_QTY=1,
        SCALP_SIM_PANIC_MAX_PARTIAL_COUNT_PER_EPOCH=1,
        **overrides,
    )


@pytest.fixture(autouse=True)
def _state(monkeypatch, tmp_path):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _rules())
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", tmp_path / "scalp_sim_state.json")
    monkeypatch.setattr(state_handlers, "persist_scalp_simulator_state", lambda: None)
    monkeypatch.setattr(state_handlers, "record_sim_post_sell_candidate", lambda **kwargs: None)
    events = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )
    return events


def _panic_files(
    tmp_path,
    target_date="2026-05-20",
    generated_at="2026-05-20T09:10:00",
    *,
    confirmed_risk_off=True,
    confirmed_micro=True,
    micro_risk_off_count=1,
    detector_panic_signal_count=0,
    current_stop_loss_count=0,
):
    panic_dir = tmp_path / "panic_sell_defense"
    breadth_dir = tmp_path / "market_panic_breadth"
    panic_dir.mkdir()
    breadth_dir.mkdir()
    (panic_dir / f"panic_sell_defense_{target_date}.json").write_text(
        json.dumps(
            {
                "report_type": "panic_sell_defense",
                "target_date": target_date,
                "generated_at": generated_at,
                "as_of": generated_at,
                "panic_state": "PANIC_SELL",
                "panic_regime_mode": "PANIC_DETECTED",
                "panic_metrics": {
                    "current_30m_stop_loss_exit_count": current_stop_loss_count,
                },
                "microstructure_detector": {
                    "risk_off_advisory_count": micro_risk_off_count,
                    "panic_signal_count": detector_panic_signal_count,
                },
                "microstructure_market_context": {
                    "market_risk_state": "RISK_OFF",
                    "market_panic_breadth_risk_off_advisory": True,
                    "confirmed_risk_off_advisory": confirmed_risk_off,
                    "confirmed_micro_risk_off_advisory": confirmed_micro,
                    "risk_off_advisory_count": micro_risk_off_count,
                    "liquidity_state": "NORMAL",
                },
            }
        ),
        encoding="utf-8",
    )
    (breadth_dir / f"market_panic_breadth_{target_date}.json").write_text(
        json.dumps(
            {
                "report_type": "market_panic_breadth",
                "target_date": target_date,
                "generated_at": generated_at,
                "as_of": generated_at,
                "risk_off_advisory": True,
                "single_market_risk_off_advisory": False,
            }
        ),
        encoding="utf-8",
    )
    return panic_dir, breadth_dir


def _panic_buying_files(
    tmp_path,
    target_date="2026-05-20",
    generated_at="2026-05-20T09:10:00",
    *,
    mode="PANIC_BUY_CONTINUATION",
    state="PANIC_BUY",
    market_confirmed=True,
    missing_orderbook=0,
    missing_trade=0,
):
    panic_buy_dir = tmp_path / "panic_buying"
    panic_buy_dir.mkdir(parents=True)
    (panic_buy_dir / f"panic_buying_{target_date}.json").write_text(
        json.dumps(
            {
                "report_type": "panic_buying",
                "target_date": target_date,
                "generated_at": generated_at,
                "as_of": generated_at,
                "panic_buy_state": state,
                "panic_buy_regime_mode": mode,
                "microstructure_detector": {
                    "panic_buy_signal_count": 1 if state != "NORMAL" else 0,
                    "missing_orderbook_count": missing_orderbook,
                    "missing_trade_aggressor_count": missing_trade,
                },
                "market_breadth_context": {
                    "market_wide_panic_buy_confirmed": market_confirmed,
                    "market_panic_breadth_risk_on_advisory": market_confirmed,
                },
            }
        ),
        encoding="utf-8",
    )
    return panic_buy_dir


def _sim_position(qty=10):
    return {
        "name": "SIM",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "sim_record_id": "SIM-1",
        "sim_parent_record_id": 101,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "buy_price": 10_000,
        "buy_qty": qty,
    }


def test_panic_context_ok_and_stale(monkeypatch, tmp_path):
    panic_dir, breadth_dir = _panic_files(tmp_path)
    monkeypatch.setattr(runtime, "PANIC_SELL_DEFENSE_DIR", panic_dir)
    monkeypatch.setattr(runtime, "MARKET_PANIC_BREADTH_DIR", breadth_dir)

    ok = runtime.resolve_panic_risk_regime_context(
        now=datetime.fromisoformat("2026-05-20T09:11:00"),
        max_age_sec=600,
    )
    stale = runtime.resolve_panic_risk_regime_context(
        now=datetime.fromisoformat("2026-05-20T09:40:00"),
        max_age_sec=60,
    )

    assert ok["panic_context_status"] == "OK"
    assert ok["panic_level"] == 2
    assert ok["panic_epoch_id"].startswith("2026-05-20|PANIC_SELL|PANIC_DETECTED|L2")
    assert stale["panic_context_status"] == "STALE"
    assert stale["panic_level"] == 0


def test_euphoria_context_maps_modes_and_blocks_bad_source(monkeypatch, tmp_path):
    panic_buy_dir = _panic_buying_files(tmp_path)
    monkeypatch.setattr(runtime, "PANIC_BUYING_DIR", panic_buy_dir)

    ok = runtime.resolve_euphoria_risk_context(
        now=datetime.fromisoformat("2026-05-20T09:11:00"),
        max_age_sec=600,
    )
    assert ok["euphoria_context_status"] == "OK"
    assert ok["euphoria_risk_level"] == 2
    assert ok["risk_direction"] == "risk_on_euphoria"
    assert ok["euphoria_epoch_id"].startswith("2026-05-20|PANIC_BUY|PANIC_BUY_CONTINUATION|E2")

    panic_buy_dir = _panic_buying_files(
        tmp_path / "bad",
        market_confirmed=False,
        missing_orderbook=1,
    )
    monkeypatch.setattr(runtime, "PANIC_BUYING_DIR", panic_buy_dir)
    blocked = runtime.resolve_euphoria_risk_context(
        now=datetime.fromisoformat("2026-05-20T09:11:00"),
        max_age_sec=600,
    )
    assert blocked["euphoria_context_status"] == "SOURCE_QUALITY_BLOCKED"
    assert blocked["euphoria_risk_level"] == 2
    assert "panic_buy_orderbook_collector_coverage_gap" in blocked["source_quality_blockers"]


def test_breadth_only_panic_sell_report_maps_to_level1_watch(monkeypatch, tmp_path):
    panic_dir, breadth_dir = _panic_files(
        tmp_path,
        confirmed_risk_off=True,
        confirmed_micro=False,
        micro_risk_off_count=0,
        detector_panic_signal_count=0,
        current_stop_loss_count=1,
    )
    monkeypatch.setattr(runtime, "PANIC_SELL_DEFENSE_DIR", panic_dir)
    monkeypatch.setattr(runtime, "MARKET_PANIC_BREADTH_DIR", breadth_dir)

    context = runtime.resolve_panic_risk_regime_context(
        now=datetime.fromisoformat("2026-05-20T09:11:00"),
        max_age_sec=600,
    )

    assert context["panic_context_status"] == "OK"
    assert context["panic_level"] == 1
    assert context["panic_level_reason"] == "breadth_risk_off_watch"
    assert context["risk_off_components"]["detector_panic_signal_count"] == 0
    assert context["risk_off_components"]["current_30m_stop_loss_exit_count"] == 1


def test_micro_confirmed_panic_sell_report_maps_to_level2(monkeypatch, tmp_path):
    panic_dir, breadth_dir = _panic_files(
        tmp_path,
        confirmed_risk_off=True,
        confirmed_micro=True,
        micro_risk_off_count=1,
    )
    monkeypatch.setattr(runtime, "PANIC_SELL_DEFENSE_DIR", panic_dir)
    monkeypatch.setattr(runtime, "MARKET_PANIC_BREADTH_DIR", breadth_dir)

    context = runtime.resolve_panic_risk_regime_context(
        now=datetime.fromisoformat("2026-05-20T09:11:00"),
        max_age_sec=600,
    )

    assert context["panic_level"] == 2
    assert context["panic_level_reason"] == "confirmed_panic_sell"


def test_partial_sell_idempotency_blocks_repeated_same_epoch(_state):
    stock = _sim_position(qty=10)
    panic_context = {
        "panic_context_status": "OK",
        "panic_level": 2,
        "panic_level_reason": "confirmed_risk_off",
        "panic_epoch_id": "2026-05-20|PANIC_SELL|PANIC_DETECTED|L2|0910",
        "liquidity_state": "NORMAL",
    }
    ws_data = {"curr": 9900, "orderbook": {"bids": [{"price": 9890}], "asks": [{"price": 9910}]}}

    assert state_handlers.complete_scalp_sim_partial_sell(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        curr_price=9900,
        now_ts=1000.0,
        partial_ratio=0.5,
        panic_context=panic_context,
        panic_action_reason="level2_breakeven_reduce",
        profit_rate=-0.2,
    )
    assert stock["buy_qty"] == 5
    assert stock["panic_partial_exit_count"] == 1

    assert not state_handlers.complete_scalp_sim_partial_sell(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        curr_price=9900,
        now_ts=1010.0,
        partial_ratio=0.5,
        panic_context=panic_context,
        panic_action_reason="level2_breakeven_reduce",
        profit_rate=-0.2,
    )
    assert stock["buy_qty"] == 5
    assert [stage for stage, _ in _state].count("scalp_sim_partial_sell_order_assumed_filled") == 1


def test_level1_partial_does_not_escalate_to_full_exit_for_small_qty(_state):
    stock = _sim_position(qty=1)
    panic_context = {
        "panic_context_status": "OK",
        "panic_level": 1,
        "panic_epoch_id": "epoch-l1",
        "liquidity_state": "NORMAL",
    }

    assert not state_handlers.complete_scalp_sim_partial_sell(
        stock=stock,
        code="123456",
        ws_data={"curr": 9900, "orderbook": {"bids": [{"price": 9890}], "asks": [{"price": 9910}]}},
        curr_price=9900,
        now_ts=1000.0,
        partial_ratio=0.5,
        panic_context=panic_context,
        panic_action_reason="level1_deterioration_partial",
        profit_rate=-0.4,
    )

    assert stock["buy_qty"] == 1
    assert stock["last_panic_action_type"] == "TRAIL_TIGHT"
    stages = [stage for stage, _ in _state]
    assert "scalp_sim_panic_level1_partial_skipped_min_remaining" in stages
    assert "scalp_sim_sell_order_assumed_filled" not in stages


def test_level_rise_allows_additional_reduction(_state):
    stock = _sim_position(qty=10)
    ws_data = {"curr": 9900, "orderbook": {"bids": [{"price": 9890}], "asks": [{"price": 9910}]}}
    level2 = {
        "panic_context_status": "OK",
        "panic_level": 2,
        "panic_epoch_id": "epoch-1",
        "liquidity_state": "NORMAL",
    }
    level3 = {**level2, "panic_level": 3, "liquidity_state": "BROKEN"}

    assert state_handlers.complete_scalp_sim_partial_sell(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        curr_price=9900,
        now_ts=1000.0,
        partial_ratio=0.5,
        panic_context=level2,
        panic_action_reason="level2_reduce",
        profit_rate=0.2,
    )
    assert state_handlers.complete_scalp_sim_partial_sell(
        stock=stock,
        code= "123456",
        ws_data=ws_data,
        curr_price=9900,
        now_ts=1010.0,
        partial_ratio=0.5,
        panic_context=level3,
        panic_action_reason="level3_reduce",
        profit_rate=0.2,
    )
    assert stock["buy_qty"] == 3


def test_partial_sell_price_model_uses_slippage_when_no_bid(_state):
    stock = _sim_position(qty=10)
    panic_context = {
        "panic_context_status": "OK",
        "panic_level": 3,
        "panic_epoch_id": "epoch-2",
        "liquidity_state": "BROKEN",
    }

    assert state_handlers.complete_scalp_sim_partial_sell(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000, "orderbook": {"bids": [], "asks": []}},
        curr_price=10_000,
        now_ts=1000.0,
        partial_ratio=0.5,
        panic_context=panic_context,
        panic_action_reason="level3_reduce",
        profit_rate=0.0,
    )
    event = next(fields for stage, fields in _state if stage == "scalp_sim_partial_sell_order_assumed_filled")
    assert event["assumed_fill_price_source"] == "current_price_slippage"
    assert event["assumed_slippage_bps"] >= 40.0
    assert event["fill_quality"] == "DEGRADED"


def test_real_path_is_not_eligible_and_broker_not_called(monkeypatch):
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_sell_order",
        lambda *args, **kwargs: pytest.fail("real sell order must not be called"),
        raising=False,
    )
    real_stock = _sim_position()
    real_stock["actual_order_submitted"] = True
    assert not state_handlers._scalp_sim_panic_eligible(real_stock, "SCALPING")

    non_forbidden = _sim_position()
    non_forbidden["broker_order_forbidden"] = False
    assert not state_handlers._scalp_sim_panic_eligible(non_forbidden, "SCALPING")

    non_sim = {"strategy": "SCALPING", "actual_order_submitted": False, "broker_order_forbidden": True}
    assert not state_handlers._scalp_sim_panic_eligible(non_sim, "SCALPING")


def test_lifecycle_matrix_ingests_panic_sim_rows_without_real_mix(monkeypatch, tmp_path):
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    monkeypatch.setattr(matrix, "PIPELINE_EVENTS_DIR", events_dir)
    path = events_dir / "pipeline_events_2026-05-20.jsonl"
    path.write_text(
        json.dumps(
            {
                "stage": "scalp_sim_partial_sell_order_assumed_filled",
                "stock_code": "123456",
                "emitted_at": "2026-05-20T09:20:00+09:00",
                "fields": {
                    "simulation_book": "scalp_ai_buy_all",
                    "sim_record_id": "SIM-1",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "profit_rate": "-0.20",
                    "realized_profit_rate": "-0.20",
                    "exit_rule": "scalp_sim_panic_lifecycle_partial_exit",
                    "panic_level": 2,
                    "panic_context_status": "OK",
                    "panic_lifecycle_action_id": "SIM-1|epoch|L2|REDUCE_PARTIAL",
                    "fill_quality": "DEGRADED",
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "stage": "scalp_sim_panic_bottoming_entry_allowed",
                "stock_code": "654321",
                "emitted_at": "2026-05-20T10:20:00+09:00",
                "fields": {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "panic_level": 1,
                    "panic_context_status": "OK",
                    "panic_lifecycle_action_id": "654321|epoch|L1|ALLOW_BOTTOMING_ENTRY",
                    "market_regime": "RISK_OFF",
                    "symbol_regime": "BOTTOMING",
                    "panic_bottoming_entry_allowed": True,
                    "panic_bottoming_arm": "risk_off_bottoming_probe_entry",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows, summary = matrix._load_scalp_sim_panic_rows("2026-05-20")

    assert summary["rows"] == 2
    exit_row = next(row for row in rows if row["stage"] == "exit")
    entry_row = next(row for row in rows if row["stage"] == "entry")
    assert exit_row["runtime_features"]["panic_level"] == 2
    assert exit_row["actual_order_submitted"] is False
    assert exit_row["source"] == "scalp_sim_panic_pipeline_events"
    assert entry_row["runtime_features"]["symbol_regime"] == "BOTTOMING"
    assert entry_row["runtime_features"]["panic_bottoming_arm"] == "risk_off_bottoming_probe_entry"


def test_entry_and_scale_in_are_blocked_for_sim_only_panic(monkeypatch, _state):
    panic_context = {
        "panic_context_status": "OK",
        "panic_level": 2,
        "panic_level_reason": "confirmed_risk_off",
        "panic_epoch_id": "epoch-entry",
        "liquidity_state": "NORMAL",
    }
    monkeypatch.setattr(state_handlers, "_resolve_scalp_sim_panic_context", lambda now_ts=None: panic_context)

    stock = {"id": 101, "name": "SIM", "strategy": "SCALPING", "target_buy_price": 10_000}
    assert not state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_000}], "bids": [{"price": 9_990}]}},
        {"strategy": "SCALPING", "is_trigger": True, "now_ts": 1000.0, "current_ai_score": 80},
    )
    assert any(stage == "scalp_sim_panic_entry_blocked" for stage, _ in _state)

    sim_stock = _sim_position(qty=10)
    result = state_handlers._evaluate_scale_in_signal(
        sim_stock,
        "123456",
        "SCALPING",
        "BULL",
        profit_rate=-0.2,
        peak_profit=0.1,
        curr_price=9_900,
        ws_data={"curr": 9_900},
        current_ai_score=70,
        held_sec=120,
    )
    assert result is None
    assert any(stage == "scalp_sim_panic_scale_in_blocked" for stage, _ in _state)
    event = next(fields for stage, fields in _state if stage == "scalp_sim_panic_entry_blocked")
    assert event["source_family"] == "panic_lifecycle_actuator"
    assert event["family_type"] == "sim_lifecycle_source"
    assert event["live_selectable"] is False
    assert event["risk_context_owner"] == "panic_sell"
    assert event["risk_direction"] == "risk_off"
    assert event["real_order_allowed"] is False


def test_euphoria_l2_blocks_chase_and_allows_retest_starter(monkeypatch, _state):
    monkeypatch.setattr(
        state_handlers,
        "_resolve_scalp_sim_euphoria_context",
        lambda now_ts=None: {
            "euphoria_context_status": "OK",
            "euphoria_risk_level": 2,
            "euphoria_risk_mode": "PANIC_BUY_CONTINUATION",
            "euphoria_level_reason": "confirmed_panic_buying",
            "euphoria_epoch_id": "euphoria-1",
            "euphoria_source_quality": "OK",
            "risk_direction": "risk_on_euphoria",
        },
    )
    stock = {"id": 101, "name": "CHASE", "strategy": "SCALPING", "target_buy_price": 10_000}
    blocked = state_handlers._should_block_scalp_sim_entry_for_euphoria(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000, "orderbook": {"asks": [{"price": 10_200}], "bids": [{"price": 9_900}]}},
        runtime={"strategy": "SCALPING", "now_ts": 1000.0, "current_ai_score": 80},
        current_ai_score=80,
    )
    assert blocked is True
    blocked_event = next(fields for stage, fields in _state if stage == "scalp_sim_euphoria_chase_entry_blocked")
    assert blocked_event["euphoria_action_type"] == "BLOCK_CHASE_ENTRY"
    assert blocked_event["risk_context_owner"] == "euphoria"
    assert blocked_event["family_type"] == "sim_lifecycle_source"
    assert blocked_event["preopen_apply_allowed"] is False

    stock = {
        "id": 102,
        "name": "RETEST",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
        "last_reversal_features": {"curr_vs_micro_vwap_bp": 5.0, "large_sell_print_detected": False},
    }
    allowed_block = state_handlers._should_block_scalp_sim_entry_for_euphoria(
        stock=stock,
        code="654321",
        ws_data={"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 10_000}]}},
        runtime={"strategy": "SCALPING", "now_ts": 1000.0, "current_ai_score": 80},
        current_ai_score=80,
    )
    assert allowed_block is False
    allowed_event = next(fields for stage, fields in _state if stage == "scalp_sim_euphoria_retest_starter_allowed")
    assert allowed_event["euphoria_action_type"] == "ALLOW_RETEST_STARTER_ENTRY"
    assert allowed_event["runtime_effect"] == "sim_arm_allowed"
    assert allowed_event["actual_order_submitted"] is False


def test_euphoria_partial_runner_is_idempotent(monkeypatch, _state):
    stock = _sim_position(qty=10)
    context = {
        "euphoria_context_status": "OK",
        "euphoria_risk_level": 2,
        "euphoria_risk_mode": "PANIC_BUY_CONTINUATION",
        "euphoria_epoch_id": "euphoria-2",
        "euphoria_source_quality": "OK",
        "risk_direction": "risk_on_euphoria",
    }
    ws_data = {"curr": 10_200, "orderbook": {"bids": [{"price": 10_180}], "asks": [{"price": 10_200}]}}
    assert state_handlers.complete_scalp_sim_euphoria_partial_profit(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        curr_price=10_200,
        now_ts=1000.0,
        partial_ratio=0.30,
        euphoria_context=context,
        euphoria_action_type="TAKE_PARTIAL_PROFIT_RUNNER",
        profit_rate=1.0,
    )
    assert stock["buy_qty"] == 7
    assert stock["euphoria_partial_tp_count"] == 1
    assert not state_handlers.complete_scalp_sim_euphoria_partial_profit(
        stock=stock,
        code="123456",
        ws_data=ws_data,
        curr_price=10_200,
        now_ts=1010.0,
        partial_ratio=0.30,
        euphoria_context=context,
        euphoria_action_type="TAKE_PARTIAL_PROFIT_RUNNER",
        profit_rate=1.0,
    )
    assert stock["buy_qty"] == 7
    assert [stage for stage, _ in _state].count("scalp_sim_euphoria_partial_profit_assumed_filled") == 1


def test_euphoria_bad_source_quality_creates_noop_not_mutation(monkeypatch, _state):
    monkeypatch.setattr(
        state_handlers,
        "_resolve_scalp_sim_euphoria_context",
        lambda now_ts=None: {
            "euphoria_context_status": "SOURCE_QUALITY_BLOCKED",
            "euphoria_risk_level": 2,
            "euphoria_risk_mode": "PANIC_BUY_CONTINUATION",
            "euphoria_epoch_id": "euphoria-bad",
            "euphoria_source_quality": "BLOCKED",
            "source_quality_blockers": ["panic_buy_orderbook_collector_coverage_gap"],
            "risk_direction": "risk_on_euphoria",
        },
    )
    stock = {"id": 101, "name": "BAD", "strategy": "SCALPING", "target_buy_price": 10_000}
    assert not state_handlers._should_block_scalp_sim_entry_for_euphoria(
        stock=stock,
        code="123456",
        ws_data={"curr": 10_000},
        runtime={"now_ts": 1000.0},
        current_ai_score=80,
    )
    event = next(fields for stage, fields in _state if stage == "scalp_sim_euphoria_context_noop")
    assert event["runtime_effect"] == "SIM_NOOP_CONTEXT_NOT_OK"
    assert event["exclude_from_ev"] is True
    assert event["real_gate_allowed"] is False
    assert event["pre_submit_gate_allowed"] is False


def test_level1_breadth_risk_off_bottoming_candidate_allows_sim_entry(monkeypatch, _state):
    panic_context = {
        "panic_context_status": "OK",
        "panic_level": 1,
        "panic_level_reason": "breadth_risk_off",
        "panic_epoch_id": "epoch-bottoming",
        "market_risk_state": "RISK_OFF",
        "breadth_risk_off": True,
        "confirmed_risk_off": False,
        "liquidity_state": "NORMAL",
    }
    monkeypatch.setattr(state_handlers, "_resolve_scalp_sim_panic_context", lambda now_ts=None: panic_context)

    stock = {
        "id": 101,
        "name": "BOTTOM",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
        "scalp_sim_candidate_window_expansion": True,
        "scalp_sim_candidate_window_source_stage": "blocked_ai_score",
        "scalp_sim_candidate_window_blocked_reason": "test_level1_risk_off",
        "last_ai_overlap_snapshot": {
            "buy_pressure_10t": 68.0,
            "distance_from_day_high_pct": -7.0,
            "latest_strength": 72.0,
        },
        "last_reversal_features": {
            "curr_vs_micro_vwap_bp": 12.0,
            "curr_vs_ma5_bp": 4.0,
            "tick_acceleration_ratio": 0.8,
            "large_sell_print_detected": False,
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_000}], "bids": [{"price": 9_990}]}},
        {"strategy": "SCALPING", "is_trigger": True, "now_ts": 1000.0, "current_ai_score": 64},
    )
    stages = [stage for stage, _ in _state]
    assert "scalp_sim_panic_bottoming_entry_allowed" in stages
    assert "scalp_sim_panic_entry_blocked" not in stages
    event = next(fields for stage, fields in _state if stage == "scalp_sim_panic_bottoming_entry_allowed")
    assert event["symbol_regime"] == "BOTTOMING"
    assert event["panic_bottoming_arm"] == "risk_off_bottoming_probe_entry"


def test_level1_breadth_risk_off_non_bottoming_is_observed_not_blocked(monkeypatch, _state):
    panic_context = {
        "panic_context_status": "OK",
        "panic_level": 1,
        "panic_level_reason": "breadth_risk_off",
        "panic_epoch_id": "epoch-weak",
        "market_risk_state": "RISK_OFF",
        "breadth_risk_off": True,
        "confirmed_risk_off": True,
        "liquidity_state": "NORMAL",
    }
    monkeypatch.setattr(state_handlers, "_resolve_scalp_sim_panic_context", lambda now_ts=None: panic_context)

    stock = {
        "id": 102,
        "name": "WEAK",
        "strategy": "SCALPING",
        "target_buy_price": 10_000,
        "last_ai_overlap_snapshot": {
            "buy_pressure_10t": 20.0,
            "distance_from_day_high_pct": -7.0,
            "latest_strength": 55.0,
        },
        "last_reversal_features": {
            "curr_vs_micro_vwap_bp": -20.0,
            "curr_vs_ma5_bp": -10.0,
            "large_sell_print_detected": True,
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "654321",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_000}], "bids": [{"price": 9_990}]}},
        {"strategy": "SCALPING", "is_trigger": True, "now_ts": 1000.0, "current_ai_score": 64},
    )
    stages = [stage for stage, _ in _state]
    assert "scalp_sim_panic_level1_entry_observed" in stages
    assert "scalp_sim_panic_entry_blocked" not in stages
    event = next(fields for stage, fields in _state if stage == "scalp_sim_panic_level1_entry_observed")
    assert event["symbol_regime"] == "WEAK"
    assert "bottoming_conditions_failed" in event["panic_bottoming_entry_reason"]
    assert event["runtime_effect"] == "sim_entry_allowed_level1_risk_off_observation"
