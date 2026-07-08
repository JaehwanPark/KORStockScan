import json
import os
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
        SCALP_SIM_PANIC_FORCE_NOOP=True,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "LAST_LOG_TIMES", {})
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", tmp_path / "scalp_live_sim_state.json")
    monkeypatch.setattr(state_handlers, "_SCALP_SIM_STATE_LAST_SEEN_MTIME_NS", None)
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_STATE_LAST_SEEN_MTIME_NS", None)
    monkeypatch.setattr(state_handlers, "record_sim_post_sell_candidate", lambda **kwargs: None)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.update(
        {
            "path": None,
            "mtime_ns": None,
            "version": None,
            "status": "not_loaded",
            "approved_rows": [],
            "rows_by_source_bucket_id": {},
            "rows_by_bucket_id": {},
            "active_seeds": [],
            "active_seeds_by_prefix": {},
            "hypotheses": [],
            "approved_row_count": 0,
        }
    )
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED.clear()
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_BUCKET_CREATED.clear()
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED.clear()
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_ACTIVE_SEED_CREATED.clear()
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_HYPOTHESIS_CREATED.clear()
    state_handlers._SCALP_SIM_AI_CALL_TIMES.clear()
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
        "liquidity_value": 800_000_000,
        "scalp_min_liquidity": 500_000_000,
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
    sim_stages = [stage for stage, _ in logs if stage.startswith("scalp_sim_")]
    assert sim_stages == [
        "scalp_sim_pre_submit_liquidity_guard_would_pass",
        "scalp_sim_pre_submit_overbought_guard_would_pass",
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
    armed_event = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed_event["runtime_effect"] == "simulated_entry_armed_only"


def test_scalp_live_simulator_respects_max_open_cap(monkeypatch):
    logs = []
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(state_handlers.TRADING_RULES, SCALP_LIVE_SIMULATOR_MAX_OPEN=1),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    state_handlers.ACTIVE_TARGETS.append(
        {
            "code": "111111",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "scalp_live_simulator": True,
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": False,
        }
    )
    stock = {
        "id": 102,
        "name": "TEST2",
        "code": "222222",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
    }

    armed = state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "222222",
        {"curr": 10_000},
        runtime,
    )

    assert armed is False
    assert len(state_handlers.ACTIVE_TARGETS) == 1
    assert state_handlers.EVENT_BUS.published == []
    assert logs[-1][0] == "scalp_live_simulator_discarded"
    assert logs[-1][1]["discard_reason"] == "max_open_reached"
    assert logs[-1][1]["open_count"] == 1
    assert logs[-1][1]["max_open"] == 1


def test_scalp_live_simulator_restore_respects_max_open_cap(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(state_handlers.TRADING_RULES, SCALP_LIVE_SIMULATOR_MAX_OPEN=4),
    )
    payload = {
        "schema_version": 1,
        "active_positions": [
            {
                "code": f"11111{idx}",
                "name": f"SIM{idx}",
                "status": "HOLDING",
                "strategy": "SCALPING",
                "sim_record_id": f"SIM-{idx}",
                "scalp_live_simulator": True,
                "simulation_book": "scalp_ai_buy_all",
                "actual_order_submitted": False,
            }
            for idx in range(7)
        ],
    }
    state_handlers.SCALP_SIM_STATE_PATH.write_text(json.dumps(payload), encoding="utf-8")

    restored = state_handlers.restore_scalp_simulator_targets(state_handlers.ACTIVE_TARGETS)

    assert restored == 4
    assert len(state_handlers._scalp_simulator_active_targets()) == 4
    assert [target["sim_record_id"] for target in state_handlers.ACTIVE_TARGETS] == [
        "SIM-0",
        "SIM-1",
        "SIM-2",
        "SIM-3",
    ]


def test_scalp_live_simulator_sync_removes_state_rows_beyond_max_open(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(state_handlers.TRADING_RULES, SCALP_LIVE_SIMULATOR_MAX_OPEN=4),
    )
    state_handlers.ACTIVE_TARGETS.extend(
        {
            "code": f"11111{idx}",
            "name": f"SIM{idx}",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "sim_record_id": f"SIM-{idx}",
            "scalp_live_simulator": True,
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": False,
        }
        for idx in range(7)
    )
    payload = {"schema_version": 1, "active_positions": [dict(row) for row in state_handlers.ACTIVE_TARGETS]}
    state_handlers.SCALP_SIM_STATE_PATH.write_text(json.dumps(payload), encoding="utf-8")

    result = state_handlers.sync_scalp_simulator_targets_from_state(state_handlers.ACTIVE_TARGETS)

    assert result["removed"] == 3
    assert result["restored"] == 0
    assert len(state_handlers._scalp_simulator_active_targets()) == 4
    assert [target["sim_record_id"] for target in state_handlers.ACTIVE_TARGETS] == [
        "SIM-0",
        "SIM-1",
        "SIM-2",
        "SIM-3",
    ]


def test_scalp_sim_candidate_window_runtime_cap_clamps_policy_width(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=20,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=240,
            SCALP_SIM_CANDIDATE_WINDOW_RUNTIME_MAX_OPEN_CAP=8,
            SCALP_SIM_CANDIDATE_WINDOW_RUNTIME_MAX_DAILY_CAP=80,
        ),
    )

    assert state_handlers._scalp_sim_runtime_capped_limit(
        "SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN",
        20,
        "SCALP_SIM_CANDIDATE_WINDOW_RUNTIME_MAX_OPEN_CAP",
        8,
    ) == (8, 20, 8)
    assert state_handlers._scalp_sim_runtime_capped_limit(
        "SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY",
        240,
        "SCALP_SIM_CANDIDATE_WINDOW_RUNTIME_MAX_DAILY_CAP",
        80,
    ) == (80, 240, 80)


def test_scalp_sim_candidate_window_runtime_cap_zero_preserves_configured_width(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=20,
            SCALP_SIM_CANDIDATE_WINDOW_RUNTIME_MAX_OPEN_CAP=0,
        ),
    )

    assert state_handlers._scalp_sim_runtime_capped_limit(
        "SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN",
        20,
        "SCALP_SIM_CANDIDATE_WINDOW_RUNTIME_MAX_OPEN_CAP",
        8,
    ) == (20, 20, 0)


def test_scalp_simulator_attaches_matched_lifecycle_bucket_provenance(monkeypatch, tmp_path):
    source_bucket_id = "lifecycle_flow:combo_lifecycle_flow:entry_score_70p:abc123"
    bucket_id = "lifecycle_flow:combo_lifecycle_flow:entry_score_70p"
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-05-28.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [
                    {
                        "source_id": "lifecycle_bucket_discovery",
                        "approved_bucket_rows": [
                            {
                                "bucket_id": bucket_id,
                                "source_bucket_id": source_bucket_id,
                                "classification_state": "lifecycle_flow_sim_probe_candidate",
                                "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                                "stage": "lifecycle_flow",
                                "bucket_type": "combo_lifecycle_flow",
                                "sample": 1,
                                "joined_sample": 1,
                                "complete_flow_count": 1,
                                "incomplete_flow_count": 0,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-06-15")
    monkeypatch.delenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_SOURCE_DATE", raising=False)
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_AUTO_POLICY_ENABLED=True,
            SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
            SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-05-28",
        ),
    )
    entry_logs = []
    holding_logs = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: entry_logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: holding_logs.append((stage, fields)),
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
        "lifecycle_bucket_source_bucket_id": source_bucket_id,
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": True,
        "now_ts": 1_000.0,
        "current_ai_score": 82.0,
        "latency_state": "DANGER",
        "liquidity_value": 800_000_000,
        "scalp_min_liquidity": 500_000_000,
    }
    ws_data = {
        "curr": 9_990,
        "orderbook": {
            "asks": [{"price": 9_990}],
            "bids": [{"price": 9_980}],
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(stock, "123456", ws_data, runtime)
    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["lifecycle_bucket_match_status"] == "matched"
    assert sim_target["bucket_directed_sim_probe"] is True

    for stage_name in (
        "scalp_sim_entry_armed",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_holding_started",
    ):
        event = next(fields for stage, fields in entry_logs if stage == stage_name)
        assert event["lifecycle_bucket_match_status"] == "matched"
        assert event["bucket_directed_sim_probe"] is True
        assert event["lifecycle_bucket_source_bucket_id"] == source_bucket_id
        assert event["lifecycle_bucket_bucket_id"] == bucket_id
        assert event["lifecycle_bucket_classification_state"] == "lifecycle_flow_sim_probe_candidate"
        assert event["actual_order_submitted"] is False
        assert event["broker_order_forbidden"] is True

    assert state_handlers._complete_scalp_simulated_sell(
        stock=sim_target,
        code="123456",
        ws_data={"curr": 10_100, "orderbook": {"asks": [{"price": 10_110}], "bids": [{"price": 10_090}]}},
        curr_price=10_100,
        now_ts=1_060.0,
        sell_reason_type="PROFIT",
        exit_rule="scalp_trailing_take_profit",
        profit_rate=state_handlers.calculate_net_profit_rate(9_990, 10_100),
    )
    sell_event = next(fields for stage, fields in holding_logs if stage == "scalp_sim_sell_order_assumed_filled")
    assert sell_event["lifecycle_bucket_match_status"] == "matched"
    assert sell_event["lifecycle_bucket_source_bucket_id"] == source_bucket_id
    assert sell_event["bucket_directed_sim_probe"] is True
    assert sell_event["actual_order_submitted"] is False
    assert sell_event["broker_order_forbidden"] is True


def test_scalp_simulator_consumes_lifecycle_bucket_catalog_handoff_when_direct_policy_off(monkeypatch, tmp_path):
    source_bucket_id = "lifecycle_flow:combo_lifecycle_flow:entry_score_60_62:abc123"
    bucket_id = "lifecycle_flow:combo_lifecycle_flow:entry_score_60_62"
    catalog_path = tmp_path / "lifecycle_bucket_catalog_2026-06-12.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "lifecycle_bucket_catalog_v1",
                "buckets": [
                    {
                        "bucket_id": bucket_id,
                        "source_bucket_id": source_bucket_id,
                        "classification_state": "lifecycle_flow_sim_probe_candidate",
                        "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                        "stage": "lifecycle_flow",
                        "bucket_type": "combo_lifecycle_flow",
                        "sample": 2,
                        "joined_sample": 2,
                        "complete_flow_count": 1,
                        "incomplete_flow_count": 0,
                        "sim_lifecycle_handoff_allowed": True,
                    }
                ],
                "active_sim_priority_seeds": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-06-15")
    monkeypatch.delenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_SOURCE_DATE", raising=False)
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_AUTO_POLICY_ENABLED=False,
            SCALP_SIM_AUTO_POLICY_FILE="",
            SCALP_SIM_AUTO_POLICY_VERSION="",
            LIFECYCLE_BUCKET_DISCOVERY_ENABLED=True,
            LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE=str(catalog_path),
            LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION="lifecycle_bucket_discovery:2026-06-12",
        ),
    )
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

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        {
            "id": 101,
            "name": "TEST",
            "code": "123456",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "target_buy_price": 10_000,
            "lifecycle_bucket_source_bucket_id": source_bucket_id,
        },
        "123456",
        {"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        {
            "strategy": "SCALPING",
            "is_trigger": True,
            "now_ts": 1_000.0,
            "current_ai_score": 82.0,
            "latency_state": "DANGER",
            "liquidity_value": 800_000_000,
            "scalp_min_liquidity": 500_000_000,
        },
    )

    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["lifecycle_bucket_match_status"] == "matched"
    assert armed["scalp_sim_auto_policy_enabled"] is True
    assert armed["scalp_sim_auto_policy_direct_enabled"] is False
    assert armed["lifecycle_bucket_catalog_handoff_enabled"] is True
    assert armed["scalp_sim_policy_source"] == "lifecycle_bucket_discovery_catalog_handoff"
    assert armed["scalp_sim_auto_policy_schema_version"] == "lifecycle_bucket_catalog_v1"
    assert armed["bucket_directed_sim_probe"] is True


def test_lifecycle_bucket_catalog_handoff_does_not_direct_source_only_rows(monkeypatch, tmp_path):
    source_bucket_id = "lifecycle_flow:combo_lifecycle_flow:source_only:abc123"
    catalog_path = tmp_path / "lifecycle_bucket_catalog_2026-06-12.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "lifecycle_bucket_catalog_v1",
                "buckets": [
                    {
                        "bucket_id": "lifecycle_flow:combo_lifecycle_flow:source_only",
                        "source_bucket_id": source_bucket_id,
                        "classification_state": "source_only_keep_collecting",
                        "source_bucket_kind": "source_only_observation",
                        "stage": "lifecycle_flow",
                        "bucket_type": "combo_lifecycle_flow",
                        "sim_lifecycle_handoff_allowed": False,
                    }
                ],
                "active_sim_priority_seeds": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-06-15")
    monkeypatch.delenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_SOURCE_DATE", raising=False)
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_AUTO_POLICY_ENABLED=False,
            SCALP_SIM_AUTO_POLICY_FILE="",
            SCALP_SIM_AUTO_POLICY_VERSION="",
            LIFECYCLE_BUCKET_DISCOVERY_ENABLED=True,
            LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE=str(catalog_path),
            LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION="lifecycle_bucket_discovery:2026-06-12",
        ),
    )
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

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        {
            "id": 101,
            "name": "TEST",
            "code": "123456",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "target_buy_price": 10_000,
            "lifecycle_bucket_source_bucket_id": source_bucket_id,
        },
        "123456",
        {"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        {
            "strategy": "SCALPING",
            "is_trigger": True,
            "now_ts": 1_000.0,
            "current_ai_score": 82.0,
            "latency_state": "DANGER",
            "liquidity_value": 800_000_000,
            "scalp_min_liquidity": 500_000_000,
        },
    )

    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["lifecycle_bucket_match_status"] == "no_match"
    assert armed["bucket_directed_sim_probe"] is False
    assert armed["scalp_sim_policy_source"] == "lifecycle_bucket_discovery_catalog_handoff"
    assert armed["scalp_sim_auto_policy_enabled"] is True


def test_candidate_window_resolves_approved_lifecycle_flow_from_entry_identity(monkeypatch, tmp_path):
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

    entry_bucket_key = (
        "score=score_60_62|source=blocked_ai_score|stale=fresh_or_unflagged|"
        "liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000"
    )
    entry_bucket_id = state_handlers._scalp_sim_ldm_bucket_id("entry", "combo_entry_spot", entry_bucket_key)
    flow_bucket_id = (
        "lifecycle_flow:combo_lifecycle_flow:"
        f"{state_handlers._greenfield_bucket_slug(f'entry={entry_bucket_id}', max_len=96)}"
    )
    source_bucket_id = f"{flow_bucket_id}:source"
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-05-28.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [
                    {
                        "source_id": "lifecycle_bucket_discovery",
                        "approved_bucket_rows": [
                            {
                                "bucket_id": flow_bucket_id,
                                "source_bucket_id": source_bucket_id,
                                "classification_state": "lifecycle_flow_sim_probe_candidate",
                                "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                                "stage": "lifecycle_flow",
                                "bucket_type": "combo_lifecycle_flow",
                                "sample": 3,
                                "joined_sample": 3,
                                "complete_flow_count": 3,
                                "incomplete_flow_count": 0,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_AUTO_POLICY_ENABLED=True,
            SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
            SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-05-28",
            SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=20,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=20,
        ),
    )

    stock = {
        "id": 101,
        "name": "WAIT_TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
        "last_watching_ai_action": "WAIT",
    }

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock,
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime={"strategy": "SCALPING", "is_trigger": False, "now_ts": 1_000.0, "current_ai_score": 61.0},
        ai_decision={"action": "WAIT", "score": 61, "reason": "below entry threshold"},
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["lifecycle_bucket_match_status"] == "matched"
    assert sim_target["bucket_directed_sim_probe"] is True
    assert sim_target["lifecycle_bucket_source_bucket_id"] == source_bucket_id
    assert sim_target["lifecycle_bucket_bucket_id"] == flow_bucket_id
    assert sim_target["lifecycle_bucket_entry_bucket_id"] == entry_bucket_id
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["lifecycle_bucket_match_status"] == "matched"
    assert armed["lifecycle_bucket_source_bucket_id"] == source_bucket_id
    assert armed["bucket_directed_sim_probe"] is True
    assert armed["actual_order_submitted"] is False
    assert armed["broker_order_forbidden"] is True


def test_candidate_window_with_entry_identity_but_no_approved_row_is_background(monkeypatch, tmp_path):
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
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-05-28.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [
                    {
                        "source_id": "lifecycle_bucket_discovery",
                        "approved_bucket_rows": [
                            {
                                "bucket_id": "lifecycle_flow:combo_lifecycle_flow:entry_unrelated",
                                "source_bucket_id": "lifecycle_flow:combo_lifecycle_flow:entry_unrelated:source",
                                "stage": "lifecycle_flow",
                                "bucket_type": "combo_lifecycle_flow",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_AUTO_POLICY_ENABLED=True,
            SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
            SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-05-28",
            SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        ),
    )

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock={"id": 101, "name": "WAIT_TEST", "strategy": "SCALPING", "target_buy_price": 10_000},
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime={"strategy": "SCALPING", "is_trigger": False, "now_ts": 1_000.0, "current_ai_score": 61.0},
        ai_decision={"action": "WAIT", "score": 61},
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["lifecycle_bucket_match_status"] == "no_match"
    assert armed["bucket_directed_sim_probe"] is False
    assert armed["lifecycle_bucket_entry_bucket_id"].startswith("entry:combo_entry_spot:")
    assert armed["actual_order_submitted"] is False
    assert armed["broker_order_forbidden"] is True


def test_scalp_simulator_keeps_background_sim_when_policy_missing(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        replace(
            state_handlers.TRADING_RULES,
            SCALP_SIM_AUTO_POLICY_ENABLED=True,
            SCALP_SIM_AUTO_POLICY_FILE="/tmp/korstockscan-missing-scalp-sim-policy.json",
            SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:missing",
        ),
    )
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
        "liquidity_value": 800_000_000,
        "scalp_min_liquidity": 500_000_000,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime,
    )
    armed_event = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed_event["lifecycle_bucket_match_status"] == "policy_missing"
    assert armed_event["bucket_directed_sim_probe"] is False
    assert armed_event["actual_order_submitted"] is False
    assert armed_event["broker_order_forbidden"] is True
    assert len(state_handlers.ACTIVE_TARGETS) == 1


def test_scalp_simulator_logs_pre_submit_liquidity_would_block_but_keeps_virtual_fill(monkeypatch):
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
        "liquidity_value": 100_000_000,
        "scalp_min_liquidity": 500_000_000,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime,
    )

    stages = [stage for stage, _ in logs]
    assert "scalp_sim_pre_submit_liquidity_guard_would_block" in stages
    assert "scalp_sim_buy_order_virtual_pending" in stages
    assert "scalp_sim_buy_order_assumed_filled" in stages
    guard = next(fields for stage, fields in logs if stage == "scalp_sim_pre_submit_liquidity_guard_would_block")
    assert guard["decision_authority"] == "sim_submit_path_observation_only"
    assert guard["runtime_effect"] is False
    assert guard["actual_order_submitted"] is False
    assert guard["broker_order_forbidden"] is True
    assert guard["sim_pre_submit_liquidity_guard_action"] == "WOULD_BLOCK"
    assert guard["sim_pre_submit_liquidity_reason"] == "below_min_liquidity"
    assert guard["sim_liquidity_value"] == 100_000_000
    pending = next(fields for stage, fields in logs if stage == "scalp_sim_buy_order_virtual_pending")
    assert pending["sim_pre_submit_liquidity_guard_action"] == "WOULD_BLOCK"
    filled = next(fields for stage, fields in logs if stage == "scalp_sim_buy_order_assumed_filled")
    assert filled["sim_pre_submit_liquidity_guard_action"] == "WOULD_BLOCK"
    holding = next(fields for stage, fields in logs if stage == "scalp_sim_holding_started")
    assert holding["sim_pre_submit_liquidity_guard_action"] == "WOULD_BLOCK"
    assert holding["sim_pre_submit_liquidity_reason"] == "below_min_liquidity"


def test_scalp_simulator_logs_liquidity_unknown_when_source_missing(monkeypatch):
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
        "current_ai_score": 82.0,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime,
    )

    stages = [stage for stage, _ in logs]
    assert "scalp_sim_pre_submit_liquidity_guard_unknown" in stages
    assert "scalp_sim_pre_submit_liquidity_guard_would_pass" not in stages
    guard = next(fields for stage, fields in logs if stage == "scalp_sim_pre_submit_liquidity_guard_unknown")
    assert guard["sim_pre_submit_liquidity_guard_action"] == "WOULD_UNKNOWN"
    assert guard["sim_pre_submit_liquidity_reason"] == "liquidity_not_available"


def test_scalp_simulator_derives_liquidity_from_ws_when_runtime_source_unset(monkeypatch):
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
        "current_ai_score": 82.0,
        "liquidity_value": None,
        "scalp_min_liquidity": 500_000_000,
    }
    ws_data = {
        "curr": 10_000,
        "ask_tot": 30_000,
        "bid_tot": 25_000,
        "orderbook": {
            "asks": [{"price": 10_010}],
            "bids": [{"price": 9_990}],
        },
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        ws_data,
        runtime,
    )

    stages = [stage for stage, _ in logs]
    assert "scalp_sim_pre_submit_liquidity_guard_would_pass" in stages
    guard = next(fields for stage, fields in logs if stage == "scalp_sim_pre_submit_liquidity_guard_would_pass")
    assert guard["sim_pre_submit_liquidity_guard_action"] == "WOULD_PASS"
    assert guard["sim_pre_submit_liquidity_reason"] == "liquidity_ok"
    assert guard["sim_liquidity_value"] == 550_000_000


def test_scalp_simulator_marks_liquidity_unknown_when_runtime_zero_is_missing_totals(monkeypatch):
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
        "current_ai_score": 82.0,
        "liquidity_value": 0,
        "scalp_liquidity_value": 0,
        "scalp_liquidity_source_quality": "missing_orderbook_totals",
        "scalp_min_liquidity": 500_000_000,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        runtime,
    )

    stages = [stage for stage, _ in logs]
    assert "scalp_sim_pre_submit_liquidity_guard_unknown" in stages
    guard = next(fields for stage, fields in logs if stage == "scalp_sim_pre_submit_liquidity_guard_unknown")
    assert guard["sim_pre_submit_liquidity_guard_action"] == "WOULD_UNKNOWN"
    assert guard["sim_pre_submit_liquidity_reason"] == "liquidity_not_available"
    assert guard["sim_liquidity_value"] == "not_available"


def test_scalp_simulator_derives_overbought_context_from_intraday_range(monkeypatch):
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
        "current_ai_score": 82.0,
        "liquidity_value": 700_000_000,
        "scalp_min_liquidity": 500_000_000,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {
            "curr": 10_000,
            "intraday_range_pct": 4.0,
            "distance_from_day_high_pct": -2.0,
            "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]},
        },
        runtime,
    )

    guard = next(fields for stage, fields in logs if stage == "scalp_sim_pre_submit_overbought_guard_would_pass")
    assert guard["sim_pre_submit_overbought_guard_action"] == "WOULD_PASS"
    assert guard["sim_pre_submit_overbought_reason"] == "overbought_ok"
    assert guard["sim_overbought_risk_state"] == "not_overbought"
    assert guard["sim_overbought_risk_bucket"] == "overbought_normal"
    assert guard["sim_overbought_context_source"] == "sim_intraday_range_fallback"
    assert guard["sim_overbought_source_quality"] == "derived_from_intraday_range"


def test_scalp_simulator_marks_overbought_not_evaluated_when_context_missing(monkeypatch):
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
        "current_ai_score": 82.0,
        "liquidity_value": 700_000_000,
        "scalp_min_liquidity": 500_000_000,
    }

    assert state_handlers.maybe_arm_scalp_live_simulator_from_buy_signal(
        stock,
        "123456",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        runtime,
    )

    guard = next(fields for stage, fields in logs if stage == "scalp_sim_pre_submit_overbought_guard_would_pass")
    assert guard["sim_pre_submit_overbought_guard_action"] == "WOULD_PASS"
    assert guard["sim_pre_submit_overbought_reason"] == "overbought_not_evaluated"
    assert guard["sim_overbought_risk_state"] == "not_evaluated"
    assert guard["sim_overbought_risk_bucket"] == "overbought_context_missing"
    assert guard["sim_overbought_context_source"] == "missing_overlap_context"
    assert guard["sim_overbought_source_quality"] == "missing_intraday_range"
    filled = next(fields for stage, fields in logs if stage == "scalp_sim_buy_order_assumed_filled")
    assert filled["sim_overbought_context_source"] == "missing_overlap_context"
    assert filled["sim_overbought_source_quality"] == "missing_intraday_range"


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


def test_swing_dry_run_gatekeeper_report_is_source_only_without_telegram(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)

    sniper_runtime._publish_gatekeeper_report(
        {"name": "SWING", "strategy": "KOSPI_ML"},
        "654321",
        {"action_label": "BUY", "report": "ok"},
        True,
    )

    assert event_bus.published == []


def test_actual_order_false_gatekeeper_report_is_source_only_without_telegram(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)

    sniper_runtime._publish_gatekeeper_report(
        {"name": "PROBE", "strategy": "SCALPING", "actual_order_submitted": False},
        "123456",
        {"action_label": "BUY", "action_key": "buy", "report": "probe"},
        True,
    )

    assert event_bus.published == []


def test_not_evaluated_gatekeeper_prior_is_not_telegram_report(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)

    sniper_runtime._publish_gatekeeper_report(
        {"name": "LIVE", "strategy": "SCALPING"},
        "123456",
        {
            "action_label": "NOT_EVALUATED_SCORE_VPW_PRIOR",
            "action_key": "not_evaluated_score_vpw_prior",
            "cache_mode": "not_evaluated",
            "report": "",
        },
        True,
    )

    assert event_bus.published == []


def test_live_gatekeeper_reject_report_is_source_only_without_telegram(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)

    sniper_runtime._publish_gatekeeper_report(
        {"name": "LIVE", "strategy": "SCALPING"},
        "123456",
        {"action_label": "PULLBACK_WAIT", "action_key": "pullback_wait", "report": "wait"},
        False,
    )

    assert event_bus.published == []


def test_live_gatekeeper_report_deduplicates_repeated_approval(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)
    monkeypatch.setattr(sniper_runtime, "_GATEKEEPER_REPORT_NOTIFY_TTL_SEC", 600.0)
    sniper_runtime._GATEKEEPER_REPORT_NOTIFY_RECENT.clear()

    now = {"value": 1_000.0}
    monkeypatch.setattr(sniper_runtime.time, "time", lambda: now["value"])
    stock = {"name": "LIVE", "strategy": "SCALPING"}
    gatekeeper = {"action_label": "BUY", "action_key": "buy", "report": "ok"}

    sniper_runtime._publish_gatekeeper_report(stock, "123456", gatekeeper, True)
    sniper_runtime._publish_gatekeeper_report(stock, "123456", gatekeeper, True)
    now["value"] += 601.0
    sniper_runtime._publish_gatekeeper_report(stock, "123456", gatekeeper, True)

    assert [event for event, _ in event_bus.published] == [
        "TELEGRAM_BROADCAST",
        "TELEGRAM_BROADCAST",
    ]
    assert event_bus.published[0][1]["audience"] == "VIP_ALL"


def test_live_gatekeeper_report_handles_missing_name_and_report(monkeypatch):
    event_bus = FakeEventBus()
    monkeypatch.setattr(sniper_runtime, "event_bus", event_bus)
    sniper_runtime._GATEKEEPER_REPORT_NOTIFY_RECENT.clear()

    sniper_runtime._publish_gatekeeper_report(
        {"strategy": "SCALPING"},
        "123456",
        {"action_label": "BUY", "action_key": "buy", "report": None},
        True,
    )

    assert event_bus.published[0][0] == "TELEGRAM_BROADCAST"
    payload = event_bus.published[0][1]
    assert payload["audience"] == "VIP_ALL"
    assert "123456" in payload["message"]


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
    assert logs[0][1]["actual_order_submitted"] is False
    assert logs[0][1]["broker_order_forbidden"] is True
    assert logs[0][1]["decision_authority"] == "sim_observation_only"
    assert logs[0][1]["runtime_effect"] == "sim_observation_skipped"
    assert logs[0][1]["sim_record_id"] == "SIM-1"


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


def test_scalp_sim_candidate_window_expansion_arms_blocked_wait_candidate(monkeypatch):
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
    rules = replace(
        CONFIG,
        SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=55,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=10,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=10,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)

    stock = {
        "id": 101,
        "name": "WAIT_TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_reason": "below entry threshold",
    }
    runtime = {
        "strategy": "SCALPING",
        "is_trigger": False,
        "now_ts": 1_000.0,
        "current_ai_score": 61.0,
        "latency_state": "DANGER",
    }
    ai_decision = {"action": "WAIT", "score": 61, "reason": "below entry threshold"}

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock,
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime=runtime,
        ai_decision=ai_decision,
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )

    assert len(state_handlers.ACTIVE_TARGETS) == 1
    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["status"] == "HOLDING"
    assert sim_target["actual_order_submitted"] is False
    assert sim_target["broker_order_forbidden"] is True
    assert sim_target["scalp_sim_candidate_window_expansion"] is True
    assert sim_target["scalp_sim_candidate_window_source_stage"] == "blocked_ai_score"
    assert sim_target["scalp_sim_candidate_window_original_action"] == "WAIT"
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["scalp_sim_candidate_window_expansion"] is True
    assert armed["decision_authority"] == "sim_observation_only"
    assert armed["would_real_submit"] is False


def test_scalp_sim_candidate_window_active_seed_uses_reserved_sim_quota(monkeypatch, tmp_path):
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
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [],
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_test",
                        "source_parent_bucket_id": "parent_positive",
                        "status": "active",
                        "priority_tier": "rare_positive_parent_seed",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_blocked_ai_score",
                            "submit_quality_parent": "submit_revalidation_ok",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "targeted_sim_quota": {
                            "quota_policy_version": "active_parent_seed_targeted_quota_v1",
                            "quota_scope": "positive_parent_prefix_revisit",
                            "daily_total_share_pct": 35,
                            "per_seed_daily_limit": 20,
                            "sample_goal_per_bucket": 10,
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                    }
                ],
                "hypothesis_observation_plan": {
                    "schema_version": "ldm_hypothesis_observation_plan_v1",
                    "hypotheses": [
                        {
                            "soft_hypothesis_id": "ldm_hypothesis_also_matches",
                            "rank": 1,
                            "observable_requirements": [
                                {"field": "entry_score_parent", "op": "eq", "value": "score_watch_recovery"},
                                {"field": "entry_source_parent", "op": "eq", "value": "entry_source_blocked_ai_score"},
                            ],
                            "evidence_summary": {
                                "source_quality_adjusted_ev_pct": 1.25,
                                "sample_weight": 12,
                            },
                            "observation_budget_hint": {"policy": "sim_observation_budget_hint_v1"},
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "forbidden_uses": [
                                "buy_sell_hold_live_rule",
                                "threshold_apply",
                                "provider_route_change",
                                "bot_restart",
                                "sizing_formula_runtime_apply_without_guard",
                                "broker_order",
                                "hard_safety_bypass",
                            ],
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
        SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=55,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=10,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=10,
        SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT=60,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.update(
        {
            "path": None,
            "mtime_ns": None,
            "version": None,
            "status": "not_loaded",
            "approved_rows": [],
            "rows_by_source_bucket_id": {},
            "rows_by_bucket_id": {},
            "active_seeds": [],
            "active_seeds_by_prefix": {},
            "hypotheses": [],
            "approved_row_count": 0,
        }
    )
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED["1970-01-01"] = 6
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED[("1970-01-01", "blocked_ai_score")] = 6

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock={
            "id": 101,
            "name": "ACTIVE_SEED",
            "code": "123456",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "target_buy_price": 10_000,
            "last_watching_ai_action": "WAIT",
        },
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime={"strategy": "SCALPING", "is_trigger": False, "now_ts": 1_000.0, "current_ai_score": 61.0},
        ai_decision={"action": "WAIT", "score": 61, "reason": "below entry threshold"},
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["scalp_sim_active_priority_seed_matched"] is True
    assert sim_target["active_seed_id"] == "active_seed_test"
    assert sim_target["ldm_hypothesis_matched"] is True
    assert sim_target["ldm_hypothesis_id"] == "ldm_hypothesis_also_matches"
    assert sim_target["source_parent_bucket_id"] == "parent_positive"
    assert sim_target["scalp_sim_candidate_window_quota_policy"] == "active_parent_seed_v1"
    assert sim_target["active_seed_quota_policy_version"] == "active_parent_seed_targeted_quota_v1"
    assert sim_target["active_seed_daily_total_share_pct"] == 35
    assert sim_target["active_seed_daily_per_seed_limit"] == 20
    assert sim_target["active_seed_sample_goal_per_bucket"] == 10
    assert sim_target["actual_order_submitted"] is False
    assert sim_target["broker_order_forbidden"] is True
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["scalp_sim_active_priority_seed_matched"] is True
    assert armed["active_seed_id"] == "active_seed_test"
    assert armed["ldm_hypothesis_matched"] is True
    assert armed["quota_policy"] == "active_parent_seed_v1"
    assert armed["active_seed_daily_total_share_pct"] == 35
    assert armed["active_seed_daily_per_seed_limit"] == 20
    assert armed["actual_order_submitted"] is False
    assert armed["broker_order_forbidden"] is True

    followup_source = dict(sim_target)
    followup_source.pop("scalp_sim_candidate_window_expansion", None)
    followup_fields = state_handlers._scalp_sim_candidate_window_context_fields(followup_source)
    assert followup_fields["scalp_sim_active_priority_seed_matched"] is True
    assert followup_fields["active_seed_id"] == "active_seed_test"
    assert followup_fields["source_parent_bucket_id"] == "parent_positive"
    assert followup_fields["would_real_submit"] is False


def test_scalp_sim_active_seed_targeted_quota_blocks_after_per_seed_limit(monkeypatch, tmp_path):
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
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [],
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_limited",
                        "source_parent_bucket_id": "parent_positive",
                        "status": "active",
                        "priority_tier": "rare_positive_parent_seed",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_blocked_ai_score",
                            "submit_quality_parent": "submit_revalidation_ok",
                        },
                        "targeted_sim_quota": {
                            "quota_policy_version": "active_parent_seed_targeted_quota_v1",
                            "daily_total_share_pct": 100,
                            "per_seed_daily_limit": 1,
                            "sample_goal_per_bucket": 10,
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
        SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=55,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=10,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=10,
        SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT=60,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.update(
        {
            "path": None,
            "mtime_ns": None,
            "version": None,
            "status": "not_loaded",
            "approved_rows": [],
            "rows_by_source_bucket_id": {},
            "rows_by_bucket_id": {},
            "active_seeds": [],
            "active_seeds_by_prefix": {},
            "hypotheses": [],
            "approved_row_count": 0,
        }
    )
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED["1970-01-01"] = 6
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED[("1970-01-01", "blocked_ai_score")] = 6
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_ACTIVE_SEED_CREATED[
        ("1970-01-01", "active_seed_limited")
    ] = 1

    assert not state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock={
            "id": 101,
            "name": "ACTIVE_SEED_LIMITED",
            "code": "123456",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "target_buy_price": 10_000,
            "last_watching_ai_action": "WAIT",
        },
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime={"strategy": "SCALPING", "is_trigger": False, "now_ts": 1_000.0, "current_ai_score": 61.0},
        ai_decision={"action": "WAIT", "score": 61, "reason": "below entry threshold"},
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )

    discarded = next(fields for stage, fields in logs if stage == "scalp_sim_candidate_window_discarded")
    assert discarded["discard_reason"] == "source_bucket_quota_reached"
    assert discarded["active_seed_daily_per_seed_limit"] == 1
    assert discarded["active_seed_daily_created"] == 1
    assert discarded["actual_order_submitted"] is False
    assert discarded["broker_order_forbidden"] is True


def test_scalp_sim_active_seed_targeted_quota_zero_share_disables_reserve(monkeypatch, tmp_path):
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
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [],
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_zero_share",
                        "source_parent_bucket_id": "parent_positive",
                        "status": "active",
                        "priority_tier": "rare_positive_parent_seed",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_blocked_ai_score",
                            "submit_quality_parent": "submit_revalidation_ok",
                        },
                        "targeted_sim_quota": {
                            "quota_policy_version": "active_parent_seed_targeted_quota_v1",
                            "daily_total_share_pct": 0,
                            "per_seed_daily_limit": 20,
                            "sample_goal_per_bucket": 10,
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
        SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=55,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=10,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=10,
        SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT=60,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.update(
        {
            "path": None,
            "mtime_ns": None,
            "version": None,
            "status": "not_loaded",
            "approved_rows": [],
            "rows_by_source_bucket_id": {},
            "rows_by_bucket_id": {},
            "active_seeds": [],
            "active_seeds_by_prefix": {},
            "hypotheses": [],
            "approved_row_count": 0,
        }
    )
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED["1970-01-01"] = 6
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED[("1970-01-01", "blocked_ai_score")] = 6

    assert not state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock={
            "id": 101,
            "name": "ACTIVE_SEED_ZERO_SHARE",
            "code": "123456",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "target_buy_price": 10_000,
            "last_watching_ai_action": "WAIT",
        },
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime={"strategy": "SCALPING", "is_trigger": False, "now_ts": 1_000.0, "current_ai_score": 61.0},
        ai_decision={"action": "WAIT", "score": 61, "reason": "below entry threshold"},
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )

    discarded = next(fields for stage, fields in logs if stage == "scalp_sim_candidate_window_discarded")
    assert discarded["discard_reason"] == "source_bucket_quota_reached"
    assert discarded["active_seed_daily_total_share_pct"] == 0
    assert discarded["active_seed_daily_total_limit"] == 0
    assert discarded["actual_order_submitted"] is False
    assert discarded["broker_order_forbidden"] is True


def test_scalp_sim_active_seed_matches_first_ai_wait_wait6579_parent(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_wait6579",
                        "source_parent_bucket_id": "parent_wait6579",
                        "status": "active",
                        "priority_tier": "rare_positive_parent_seed",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_active_seed_match_fields(
        score_value=61,
        source_stage="first_ai_wait",
        fields={},
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is True
    assert fields["active_seed_match_eligible"] is True
    assert fields["active_seed_id"] == "active_seed_wait6579"
    assert json.loads(fields["active_seed_candidate_observable_prefix"]) == {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_wait6579",
    }
    assert fields["entry_source_parent_contract_state"] == "canonical_alias"
    assert fields["entry_source_parent_runtime_effect_allowed"] is True


def test_scalp_sim_active_seed_ignores_inactive_catalog_seed(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_inactive",
                        "source_parent_bucket_id": "parent_wait6579",
                        "status": "cooldown",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_active_seed_match_fields(
        score_value=61,
        source_stage="first_ai_wait",
        fields={},
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is False
    assert fields["active_seed_match_eligible"] is True
    assert "active_seed_id" not in fields
    assert fields["active_seed_match_source"] == "no_match"
    cache = state_handlers._load_scalp_sim_auto_policy_cache()
    assert cache["active_seed_count"] == 0
    assert cache["active_seeds_by_prefix"] == {}


def test_scalp_sim_active_seed_blocks_stale_apply_date_policy(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_wait6579",
                        "source_parent_bucket_id": "parent_wait6579",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE", "2026-06-02")
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_active_seed_match_fields(
        score_value=61,
        source_stage="first_ai_wait",
        fields={},
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is False
    assert fields["active_seed_match_eligible"] is False
    assert fields["active_seed_match_exclusion_reason"] == "policy_stale_source_date_mismatch"
    assert "active_seed_id" not in fields
    assert fields["active_seed_match_blocked_reason"] == "policy_stale_source_date_mismatch"
    assert fields["active_seed_match_source"] == "policy_stale_source_date_mismatch"
    cache = state_handlers._load_scalp_sim_auto_policy_cache()
    assert cache["status"] == "policy_stale_source_date_mismatch"
    assert cache["active_seeds_by_prefix"] == {}


def test_scalp_sim_active_seed_blocks_missing_source_date_in_runtime_apply(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_wait6579",
                        "source_parent_bucket_id": "parent_wait6579",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", "2026-06-02")
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE", raising=False)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_active_seed_match_fields(
        score_value=61,
        source_stage="first_ai_wait",
        fields={},
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is False
    assert fields["active_seed_match_eligible"] is False
    assert fields["active_seed_match_exclusion_reason"] == "policy_source_date_missing"
    assert "active_seed_id" not in fields
    assert fields["active_seed_match_blocked_reason"] == "policy_source_date_missing"
    assert fields["active_seed_match_source"] == "policy_source_date_missing"
    cache = state_handlers._load_scalp_sim_auto_policy_cache()
    assert cache["status"] == "policy_source_date_missing"
    assert cache["active_seeds_by_prefix"] == {}


def test_scalp_sim_active_seed_unmatched_new_axis_preserves_taxonomy_contract(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_observed_other",
                        "source_parent_bucket_id": "parent_observed_other",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_observed_other",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_active_seed_match_fields(
        score_value=61,
        source_stage="new_observation_axis_v1",
        fields={},
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is False
    assert fields["active_seed_match_eligible"] is False
    assert fields["active_seed_match_exclusion_reason"] == "entry_source_taxonomy_pending_runtime_effect_blocked"
    assert "active_seed_id" not in fields
    assert json.loads(fields["active_seed_candidate_observable_prefix"]) == {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_observed_other",
    }
    assert fields["active_seed_match_blocked_reason"] == "entry_source_taxonomy_pending_runtime_effect_blocked"
    assert fields["entry_source_parent_contract_state"] == "new_axis_pending_taxonomy"
    assert fields["entry_source_parent_consume_data"] is True
    assert fields["entry_source_parent_runtime_effect_allowed"] is False


def test_scalp_sim_candidate_window_context_recomputes_stale_active_seed_alias(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_wait6579",
                        "source_parent_bucket_id": "parent_wait6579",
                        "status": "active",
                        "priority_tier": "rare_positive_parent_seed",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_sim_candidate_window_context_fields(
        {
            "scalp_sim_candidate_window_expansion": True,
            "scalp_sim_candidate_window_source_stage": "first_ai_wait",
            "scalp_sim_candidate_window_original_score": "61.0",
            "scalp_sim_active_priority_seed_matched": False,
            "active_seed_candidate_observable_prefix": json.dumps(
                {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_observed_other",
                },
                sort_keys=True,
            ),
        }
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is True
    assert fields["active_seed_id"] == "active_seed_wait6579"
    assert json.loads(fields["active_seed_candidate_observable_prefix"]) == {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_wait6579",
    }
    assert fields["entry_source_parent_contract_state"] == "canonical_alias"


def test_scalp_sim_candidate_window_context_refreshes_stale_prefix_even_with_seed_id(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_wait6579",
                        "source_parent_bucket_id": "parent_wait6579",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_sim_candidate_window_context_fields(
        {
            "scalp_sim_candidate_window_expansion": True,
            "scalp_sim_candidate_window_source_stage": "first_ai_wait",
            "scalp_sim_candidate_window_original_score": "61.0",
            "scalp_sim_active_priority_seed_matched": True,
            "active_seed_id": "stale_seed",
            "active_seed_candidate_observable_prefix": json.dumps(
                {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_observed_other",
                },
                sort_keys=True,
            ),
        }
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is True
    assert fields["active_seed_id"] == "active_seed_wait6579"
    assert json.loads(fields["active_seed_candidate_observable_prefix"]) == {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_wait6579",
    }


def test_scalp_sim_candidate_window_context_refreshes_stale_seed_id_with_same_prefix(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_current",
                        "source_parent_bucket_id": "parent_wait6579_current",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                    },
                    {
                        "active_seed_id": "active_seed_stale",
                        "source_parent_bucket_id": "parent_wait6579_old",
                        "status": "cooldown",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_wait6579",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.clear()

    fields = state_handlers._scalp_sim_candidate_window_context_fields(
        {
            "scalp_sim_candidate_window_expansion": True,
            "scalp_sim_candidate_window_source_stage": "first_ai_wait",
            "scalp_sim_candidate_window_original_score": "61.0",
            "scalp_sim_active_priority_seed_matched": True,
            "active_seed_id": "active_seed_stale",
            "active_seed_candidate_observable_prefix": json.dumps(
                {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
                sort_keys=True,
            ),
        }
    )

    assert fields["scalp_sim_active_priority_seed_matched"] is True
    assert fields["active_seed_id"] == "active_seed_current"
    assert fields["active_seed_match_source"] == "current_preopen_active_policy"


def test_scalp_sim_candidate_window_hypothesis_uses_sim_only_reserved_quota(monkeypatch, tmp_path):
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
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [],
                "active_sim_priority_seeds": [],
                "hypothesis_observation_plan": {
                    "schema_version": "ldm_hypothesis_observation_plan_v1",
                    "hypotheses": [
                        {
                            "soft_hypothesis_id": "ldm_hypothesis_test",
                            "rank": 1,
                            "observable_requirements": [
                                {"field": "entry_score_parent", "op": "eq", "value": "score_watch_recovery"},
                                {"field": "entry_source_parent", "op": "eq", "value": "entry_source_blocked_ai_score"},
                            ],
                            "evidence_summary": {
                                "source_quality_adjusted_ev_pct": 1.25,
                                "sample_weight": 12,
                            },
                            "observation_budget_hint": {"policy": "sim_observation_budget_hint_v1"},
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "forbidden_uses": [
                                "buy_sell_hold_live_rule",
                                "threshold_apply",
                                "provider_route_change",
                                "bot_restart",
                                "sizing_formula_runtime_apply_without_guard",
                                "broker_order",
                                "hard_safety_bypass",
                            ],
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
        SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=55,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=10,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=10,
        SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT=60,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_AUTO_POLICY_CACHE.update(
        {
            "path": None,
            "mtime_ns": None,
            "version": None,
            "status": "not_loaded",
            "approved_rows": [],
            "rows_by_source_bucket_id": {},
            "rows_by_bucket_id": {},
            "active_seeds": [],
            "active_seeds_by_prefix": {},
            "hypotheses": [],
            "approved_row_count": 0,
        }
    )
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED["1970-01-01"] = 6
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED[("1970-01-01", "blocked_ai_score")] = 6

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock={
            "id": 101,
            "name": "HYPOTHESIS",
            "code": "123456",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "target_buy_price": 10_000,
            "last_watching_ai_action": "WAIT",
        },
        code="123456",
        ws_data={"curr": 9_990, "orderbook": {"asks": [{"price": 9_990}], "bids": [{"price": 9_980}]}},
        runtime={"strategy": "SCALPING", "is_trigger": False, "now_ts": 1_000.0, "current_ai_score": 61.0},
        ai_decision={"action": "WAIT", "score": 61, "reason": "below entry threshold"},
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )

    sim_target = state_handlers.ACTIVE_TARGETS[0]
    assert sim_target["ldm_hypothesis_matched"] is True
    assert sim_target["ldm_hypothesis_id"] == "ldm_hypothesis_test"
    assert sim_target["scalp_sim_candidate_window_quota_policy"] == "ldm_hypothesis_observation_plan_v1"
    assert sim_target["actual_order_submitted"] is False
    assert sim_target["broker_order_forbidden"] is True
    armed = next(fields for stage, fields in logs if stage == "scalp_sim_entry_armed")
    assert armed["ldm_hypothesis_matched"] is True
    assert armed["ldm_hypothesis_id"] == "ldm_hypothesis_test"
    assert armed["quota_policy"] == "ldm_hypothesis_observation_plan_v1"


def test_scalp_sim_policy_loader_accepts_legacy_ldm_hypothesis_forbidden_use_alias(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [],
                "active_sim_priority_seeds": [],
                "hypothesis_observation_plan": {
                    "schema_version": "ldm_hypothesis_observation_plan_v1",
                    "hypotheses": [
                        {
                            "soft_hypothesis_id": "ldm_hypothesis_legacy_alias",
                            "rank": 1,
                            "observable_requirements": [
                                {"field": "entry_score_parent", "op": "eq", "value": "score_watch_recovery"},
                                {"field": "entry_source_parent", "op": "eq", "value": "entry_source_wait6579"},
                            ],
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "forbidden_uses": [
                                "buy_sell_hold_live_rule",
                                "threshold_apply",
                                "provider_route_change",
                                "bot_restart",
                                "position_cap_release",
                                "broker_order",
                                "hard_safety_bypass",
                            ],
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)

    cache = state_handlers._load_scalp_sim_auto_policy_cache()

    assert cache["hypothesis_count"] == 1
    assert cache["hypotheses"][0]["soft_hypothesis_id"] == "ldm_hypothesis_legacy_alias"


def test_scalp_sim_policy_loader_rejects_invalid_hypothesis_contract(monkeypatch, tmp_path):
    catalog_path = tmp_path / "scalp_sim_policy_catalog_2026-06-01.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "policies": [],
                "active_sim_priority_seeds": [],
                "hypothesis_observation_plan": {
                    "schema_version": "ldm_hypothesis_observation_plan_v1",
                    "hypotheses": [
                        {
                            "soft_hypothesis_id": "invalid_missing_forbidden_uses",
                            "observable_requirements": [
                                {"field": "entry_score_parent", "op": "eq", "value": "score_watch_recovery"}
                            ],
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                        {
                            "soft_hypothesis_id": "invalid_post_arm_requirement",
                            "observable_requirements": [
                                {"field": "submit_quality_parent", "op": "eq", "value": "submit_stale_context_or_quote"}
                            ],
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "forbidden_uses": [
                                "buy_sell_hold_live_rule",
                                "threshold_apply",
                                "provider_route_change",
                                "bot_restart",
                                "broker_order",
                                "hard_safety_bypass",
                            ],
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    rules = replace(
        CONFIG,
        SCALP_SIM_AUTO_POLICY_ENABLED=True,
        SCALP_SIM_AUTO_POLICY_FILE=str(catalog_path),
        SCALP_SIM_AUTO_POLICY_VERSION="scalp_sim_auto_approval:2026-06-01",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)

    cache = state_handlers._load_scalp_sim_auto_policy_cache()

    assert cache["hypotheses"] == []
    assert cache["hypothesis_count"] == 0
    assert cache["status"] == "policy_invalid"


def test_scalp_sim_candidate_window_enforces_ldm_sample_quota_sim_only(monkeypatch):
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
    rules = replace(
        CONFIG,
        SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=55,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=10,
        SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=10,
        SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT=60,
        SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT=30,
        SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY="09:00-10:00=2,10:00-12:00=8",
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED.clear()
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_BUCKET_CREATED.clear()
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED.clear()

    stock = {
        "id": 201,
        "name": "QUOTA_TEST",
        "code": "654321",
        "strategy": "SCALPING",
        "position_tag": "SCALP_BASE",
        "target_buy_price": 10_000,
        "last_watching_ai_action": "WAIT",
    }
    ws_data = {"curr": 10_000, "orderbook": {"asks": [{"price": 10_000}], "bids": [{"price": 9_990}]}}
    ai_decision = {"action": "WAIT", "score": 61, "reason": "sample"}

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock.copy(),
        code="654321",
        ws_data=ws_data,
        runtime={"strategy": "SCALPING", "now_ts": 1_779_235_800.0},
        ai_decision=ai_decision,
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )
    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock.copy(),
        code="654322",
        ws_data=ws_data,
        runtime={"strategy": "SCALPING", "now_ts": 1_779_236_100.0},
        ai_decision=ai_decision,
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )
    assert not state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock.copy(),
        code="654323",
        ws_data=ws_data,
        runtime={"strategy": "SCALPING", "now_ts": 1_779_236_400.0},
        ai_decision=ai_decision,
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )
    assert logs[-1][1]["discard_reason"] == "time_bucket_quota_reached"
    assert logs[-1][1]["runtime_effect"] == "sim_observation_skipped"
    assert logs[-1][1]["decision_authority"] == "sim_observation_only"

    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_CREATED["2026-05-20"] = 7
    state_handlers._SCALP_SIM_CANDIDATE_WINDOW_DAILY_SOURCE_CREATED[("2026-05-20", "blocked_ai_score")] = 6
    assert not state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock.copy(),
        code="654324",
        ws_data=ws_data,
        runtime={"strategy": "SCALPING", "now_ts": 1_779_239_400.0},
        ai_decision=ai_decision,
        ai_score=61,
        source_stage="blocked_ai_score",
        blocked_reason="below_buy_score_threshold",
    )
    assert logs[-1][1]["discard_reason"] == "source_bucket_quota_reached"

    assert state_handlers._maybe_arm_scalp_sim_candidate_window(
        stock=stock.copy(),
        code="654325",
        ws_data=ws_data,
        runtime={"strategy": "SCALPING", "now_ts": 1_779_239_700.0},
        ai_decision=ai_decision,
        ai_score=61,
        source_stage="panic_lifecycle_source",
        blocked_reason="panic_context",
    )


def test_scalp_sim_scale_in_window_expansion_returns_sim_only_action(monkeypatch):
    rules = replace(
        CONFIG,
        SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED=True,
        SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS="PYRAMID,AVG_DOWN",
        SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT=-2.5,
        SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT=2.5,
        SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION=1,
        SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY=30,
    )
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    state_handlers._SCALP_SIM_SCALE_IN_WINDOW_DAILY_CREATED.clear()
    stock = {
        "name": "SIM_SCALE",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "actual_order_submitted": False,
    }

    action = state_handlers._evaluate_scalp_sim_scale_in_window_expansion(
        stock=stock,
        strategy="SCALPING",
        profit_rate=0.4,
        peak_profit=0.6,
        current_ai_score=70,
        held_sec=120,
    )

    assert action["should_add"] is True
    assert action["add_type"] == "PYRAMID"
    assert action["actual_order_submitted"] is False
    assert action["broker_order_forbidden"] is True
    assert action["decision_authority"] == "sim_observation_only"


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
        "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
        "sim_pre_submit_liquidity_reason": "below_min_liquidity",
        "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
        "sim_pre_submit_overbought_reason": "overbought_ok",
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
        "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
        "sim_pre_submit_liquidity_reason": "below_min_liquidity",
        "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
        "sim_pre_submit_overbought_reason": "overbought_ok",
        "scalp_sim_ai_last_smoothed_score": 76,
        "scalp_sim_ai_last_raw_score": 79,
        "scalp_sim_ai_last_action": "HOLD",
        "scalp_sim_ai_last_result_source": "bedrock",
        "scalp_sim_ai_last_model": "bedrock-nova-lite-v2",
        "scalp_sim_ai_last_model_tier": "tier2",
        "scalp_sim_ai_last_transport_mode": "bedrock",
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
        exit_rule="scalp_hard_stop_pct",
        profit_rate=state_handlers.calculate_net_profit_rate(10_000, 10_150),
    )

    expected_profit = state_handlers.calculate_net_profit_rate(10_000, 10_130)
    assert stock["sell_price"] == 10_130
    assert stock["profit_rate"] == expected_profit
    event = next(fields for stage, fields in holding_logs if stage == "scalp_sim_sell_order_assumed_filled")
    assert event["profit_rate"] == f"{expected_profit:+.2f}"
    assert event["trigger_profit_rate"] == f"{state_handlers.calculate_net_profit_rate(10_000, 10_150):+.2f}"
    assert event["decision_authority"] == "sim_observation_only"
    assert event["current_ai_score"] == 76
    assert event["ai_score_raw"] == 79
    assert event["ai_model"] == "bedrock-nova-lite-v2"
    assert event["sim_pre_submit_liquidity_guard_action"] == "WOULD_BLOCK"
    assert event["sim_pre_submit_liquidity_reason"] == "below_min_liquidity"
    assert len(sim_post_sell_candidates) == 1
    assert sim_post_sell_candidates[0]["sim_record_id"] == "SIM-1"
    assert sim_post_sell_candidates[0]["sell_price"] == 10_130
    assert sim_post_sell_candidates[0]["profit_rate"] == expected_profit
    assert sim_post_sell_candidates[0]["exit_rule"] == "scalp_hard_stop_pct"
    assert sim_post_sell_candidates[0]["current_ai_score"] == 76
    assert sim_post_sell_candidates[0]["ai_model"] == "bedrock-nova-lite-v2"


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
    rules = replace(CONFIG, SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=True)
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


def test_real_scalp_scale_in_uses_orderable_percent_budget_without_one_share_cap(monkeypatch):
    rules = replace(
        CONFIG,
        INVEST_RATIO_SCALPING_MIN=0.10,
        INVEST_RATIO_SCALPING_MAX=0.30,
        SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        SCALPING_SCALE_IN_MIN_ONE_SHARE_FLOOR_ENABLED=True,
    )
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 1,
        "hard_stop_price": 9_000,
        "rt_ai_prob": 0.90,
        "actual_order_submitted": True,
    }

    details = scale_in.describe_dynamic_scale_in_qty(
        stock=stock,
        resolved_price=10_000,
        deposit=1_000_000,
        add_type="AVG_DOWN",
        strategy="SCALPING",
        add_reason="reversal_add_ok",
        price_resolution={"allowed": True},
        action={"reason": "reversal_add_ok", "current_ai_score": 100},
    )

    assert details["sim_uncapped_qty"] is False
    assert details["effective_qty_cap"] == 0
    assert details["scale_in_budget_ratio"] == 0.30
    assert details["scale_in_target_budget"] == 300_000
    assert details["scale_in_safe_budget"] == 285_000
    assert details["scale_in_budget_qty"] == 28
    assert details["would_qty"] == 28
    assert details["effective_qty"] == 28
    assert details["qty"] == 28


def test_real_scalp_pyramid_uses_dynamic_budget_for_one_share_position(monkeypatch):
    rules = replace(
        CONFIG,
        INVEST_RATIO_SCALPING_MIN=0.10,
        INVEST_RATIO_SCALPING_MAX=0.30,
        SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        SCALPING_PYRAMID_MAX_ADD_QTY_RATIO=0.50,
    )
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 173_700,
        "buy_qty": 1,
        "rt_ai_prob": 0.72,
        "holding_score_source": "live",
        "holding_score_data_quality": "fresh",
        "holding_score_effective_usable": True,
        "last_reversal_features": {
            "buy_pressure_10t": 79.31,
            "tick_acceleration_ratio": 1.0,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 47.85,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "tick_context_stale": False,
            "quote_stale": False,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
        },
        "actual_order_submitted": True,
    }

    details = scale_in.describe_dynamic_scale_in_qty(
        stock=stock,
        resolved_price=177_000,
        deposit=10_000_000,
        add_type="PYRAMID",
        strategy="SCALPING",
        add_reason="scalping_pyramid_ok",
        price_resolution={"allowed": True},
        action={
            "reason": "scalping_pyramid_ok",
            "current_ai_score": 72,
            "holding_score_source": "live",
            "holding_score_data_quality": "fresh",
            "holding_score_effective_usable": True,
            "profit_rate": 1.55,
            "peak_profit": 1.61,
        },
    )

    assert details["sim_uncapped_qty"] is False
    assert details["scale_in_budget_qty"] == 13
    assert details["would_qty"] == 13
    assert details["effective_qty"] == 13
    assert details["qty"] == 13
    assert details["qty_reason"] == "dynamic_allowed"
    assert details["pyramid_sizing_mode"] == "dynamic_budget"
    assert details["pyramid_position_ratio_cap_applied"] is False


def test_real_scalp_pyramid_uses_dynamic_budget_qty_without_existing_position_ratio_cap(monkeypatch):
    rules = replace(
        CONFIG,
        INVEST_RATIO_SCALPING_MIN=0.10,
        INVEST_RATIO_SCALPING_MAX=0.30,
        SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        SCALPING_PYRAMID_MAX_ADD_QTY_RATIO=0.50,
    )
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 10,
        "rt_ai_prob": 0.90,
        "holding_score_source": "live",
        "holding_score_data_quality": "fresh",
        "holding_score_effective_usable": True,
        "last_reversal_features": {
            "buy_pressure_10t": 80.0,
            "tick_acceleration_ratio": 1.2,
            "large_sell_print_detected": False,
            "curr_vs_micro_vwap_bp": 25.0,
            "micro_vwap_available": True,
            "minute_candle_window_fresh": True,
            "minute_candle_context_quality": "fresh_bar_window",
            "tick_context_stale": False,
            "quote_stale": False,
            "tick_aggressor_trusted_count": 10,
            "tick_aggressor_pressure_usable": True,
        },
        "actual_order_submitted": True,
    }

    details = scale_in.describe_dynamic_scale_in_qty(
        stock=stock,
        resolved_price=10_000,
        deposit=10_000_000,
        add_type="PYRAMID",
        strategy="SCALPING",
        add_reason="scalping_pyramid_ok",
        price_resolution={"allowed": True},
        action={
            "reason": "scalping_pyramid_ok",
            "current_ai_score": 90,
            "holding_score_source": "live",
            "holding_score_data_quality": "fresh",
            "holding_score_effective_usable": True,
            "profit_rate": 2.0,
            "peak_profit": 2.0,
        },
    )

    assert details["scale_in_budget_qty"] == 266
    assert details["would_qty"] == 266
    assert details["effective_qty"] == 266
    assert details["qty"] == 266
    assert details["pyramid_sizing_mode"] == "dynamic_budget"
    assert details["pyramid_position_ratio_cap_applied"] is False


def test_real_scalp_scale_in_min_one_share_floor_when_percent_budget_is_below_price(monkeypatch):
    rules = replace(
        CONFIG,
        INVEST_RATIO_SCALPING_MIN=0.10,
        INVEST_RATIO_SCALPING_MAX=0.30,
        SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=True,
        SCALPING_SCALE_IN_MIN_ONE_SHARE_FLOOR_ENABLED=True,
    )
    monkeypatch.setattr(scale_in, "TRADING_RULES", rules)
    stock = {
        "name": "TEST",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 200_000,
        "buy_qty": 100,
        "hard_stop_price": 100_000,
        "rt_ai_prob": 0.0,
        "actual_order_submitted": True,
    }

    details = scale_in.describe_dynamic_scale_in_qty(
        stock=stock,
        resolved_price=200_000,
        deposit=1_000_000,
        add_type="AVG_DOWN",
        strategy="SCALPING",
        add_reason="reversal_add_ok",
        price_resolution={"allowed": True},
        action={"reason": "reversal_add_ok", "current_ai_score": 0},
    )

    assert details["scale_in_budget_ratio"] == 0.10
    assert details["scale_in_target_budget"] == 100_000
    assert details["scale_in_safe_budget"] == 95_000
    assert details["scale_in_budget_qty"] == 1
    assert details["scale_in_min_one_share_floor_applied"] is True
    assert details["qty"] == 1


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


def test_swing_probe_state_sync_removes_exited_and_restores_active(tmp_path):
    state_handlers.SWING_INTRADAY_PROBE_STATE_PATH.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "simulation_book": "swing_intraday_live_equiv_probe",
                "active_positions": [
                    {
                        "id": 8002,
                        "probe_id": "ACTIVE1",
                        "code": "326030",
                        "name": "SK바이오팜",
                        "strategy": "KOSPI_ML",
                        "status": "HOLDING",
                        "buy_price": 98000,
                        "buy_qty": 1,
                        "swing_intraday_probe": True,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    targets = [
        {
            "probe_id": "EXITED1",
            "code": "000000",
            "name": "OLD",
            "strategy": "KOSPI_ML",
            "status": "HOLDING",
            "simulation_book": "swing_intraday_live_equiv_probe",
            "swing_intraday_probe": True,
        },
        {"code": "005930", "name": "삼성전자", "strategy": "SCALPING", "status": "WATCHING"},
    ]

    result = state_handlers.sync_swing_intraday_probe_targets_from_state(targets)

    assert result["removed"] == 1
    assert result["restored"] == 1
    assert [target.get("code") for target in targets] == ["005930", "326030"]
    restored = targets[-1]
    assert restored["simulation_book"] == "swing_intraday_live_equiv_probe"
    assert restored["actual_order_submitted"] is False
    assert restored["broker_order_forbidden"] is True


def test_scalp_simulator_threshold_stages_are_included():
    assert threshold_family_for_stage("pre_submit_liquidity_guard_block") == "liquidity_pre_submit_guard_p1"
    assert threshold_family_for_stage("caution_weak_liquidity_entry_block") == "caution_weak_liquidity_entry_block"
    assert (
        threshold_family_for_stage("pre_submit_entry_ai_authority_guard_block")
        == "pre_submit_entry_ai_authority_guard"
    )
    assert (
        threshold_family_for_stage("pre_submit_overbought_pullback_guard_block")
        == "overbought_pullback_guard_p1"
    )
    assert threshold_family_for_stage("scalp_sim_entry_armed") == "entry_mechanical_momentum"
    assert threshold_family_for_stage("pre_submit_price_guard_block") == "pre_submit_price_guard"
    assert threshold_family_for_stage("entry_submit_revalidation_block") == "pre_submit_price_guard"
    assert threshold_family_for_stage("entry_order_cancel_confirmed") == "entry_price_execution_quality"
    assert threshold_family_for_stage("scalp_sim_entry_ai_price_applied") == "dynamic_entry_price_resolver"
    assert threshold_family_for_stage("scalp_sim_entry_ai_price_skip_order") == "dynamic_entry_price_resolver"
    assert threshold_family_for_stage("scalp_sim_entry_submit_revalidation_warning") == "dynamic_entry_price_resolver"
    assert threshold_family_for_stage("scalp_sim_entry_submit_revalidation_block") == "dynamic_entry_price_resolver"
    assert (
        threshold_family_for_stage("scalp_sim_pre_submit_liquidity_guard_would_block")
        == "liquidity_pre_submit_guard_p1"
    )
    assert (
        threshold_family_for_stage("scalp_sim_pre_submit_liquidity_guard_would_pass")
        == "liquidity_pre_submit_guard_p1"
    )
    assert (
        threshold_family_for_stage("scalp_sim_pre_submit_liquidity_guard_unknown")
        == "liquidity_pre_submit_guard_p1"
    )
    assert (
        threshold_family_for_stage("scalp_sim_pre_submit_overbought_guard_would_block")
        == "overbought_pullback_guard_p1"
    )
    assert (
        threshold_family_for_stage("scalp_sim_pre_submit_overbought_guard_would_pass")
        == "overbought_pullback_guard_p1"
    )
    assert threshold_family_for_stage("scalp_sim_buy_order_assumed_filled") == "dynamic_entry_price_resolver"
    assert threshold_family_for_stage("scalp_sim_sell_order_assumed_filled") == "statistical_action_weight"
    assert threshold_family_for_stage("scalp_sim_ai_holding_live_call") == "scalp_sim_ai_budget_manager"
    assert threshold_family_for_stage("scalp_sim_ai_holding_reuse") == "scalp_sim_ai_budget_manager"
    assert threshold_family_for_stage("scalp_sim_ai_holding_deferred") == "scalp_sim_ai_budget_manager"
    assert threshold_family_for_stage("sim_ai_budget_exhausted") == "scalp_sim_ai_budget_manager"
    assert threshold_family_for_stage("sim_ai_critical_bypass") == "scalp_sim_ai_budget_manager"


def _sim_budget_rules(**overrides):
    values = {
        "SCALP_SIM_AI_BUDGET_ENABLED": True,
        "SCALP_SIM_AI_MAX_CALLS_PER_MIN": 10,
        "SCALP_SIM_AI_HOLDING_MIN_COOLDOWN_SEC": 90,
        "SCALP_SIM_AI_HOLDING_CRITICAL_COOLDOWN_SEC": 30,
        "SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC": 180,
        "SCALP_SIM_AI_DEFERRED_REVIEW_ENABLED": True,
        "SCALP_SIM_AI_HARD_CRITICAL_MIN_LOSS_PCT": -0.70,
        "SCALP_SIM_AI_SOFT_LOSS_DEFER_ENABLED": True,
        "SCALP_SIM_AI_SAFE_PROFIT_BYPASS_ENABLED": False,
        "SCALP_SIM_AI_CRITICAL_DRAWDOWN_PCT": 0.50,
    }
    values.update(overrides)
    return replace(CONFIG, **values)


def _sim_holding_stock(**overrides):
    stock = {
        "name": "SIM",
        "strategy": "SCALPING",
        "simulation_book": "scalp_ai_buy_all",
        "scalp_live_simulator": True,
        "actual_order_submitted": False,
        "scalp_sim_ai_last_action": "HOLD",
        "scalp_sim_ai_last_score": 62,
        "scalp_sim_ai_last_live_call_at": 1000.0,
    }
    stock.update(overrides)
    return stock


def test_scalp_sim_ai_budget_targets_sim_only_positions(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules())

    assert state_handlers._is_scalp_sim_ai_budget_target(_sim_holding_stock(), "SCALPING")
    assert not state_handlers._is_scalp_sim_ai_budget_target(
        {"strategy": "SCALPING", "actual_order_submitted": True},
        "SCALPING",
    )
    assert not state_handlers._is_scalp_sim_ai_budget_target(
        {"strategy": "SCALPING", "simulation_book": "scalp_ai_buy_all", "actual_order_submitted": True},
        "SCALPING",
    )


def test_scalp_sim_ai_budget_event_fields_preserve_position_provenance():
    fields = state_handlers._scalp_sim_event_fields(
        sim_record_id="SIM-1",
        entry_adm_candidate_id="ADM-1",
        runtime_effect="sim_ai_live_call_only",
    )

    assert fields["sim_record_id"] == "SIM-1"
    assert fields["entry_adm_candidate_id"] == "ADM-1"
    assert fields["simulation_book"] == "scalp_ai_buy_all"
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True
    assert fields["decision_authority"] == "sim_observation_only"


def test_scalp_sim_ai_budget_reuses_unchanged_signature(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules())
    stock = _sim_holding_stock()
    signature = state_handlers._build_scalp_sim_ai_feature_signature(
        stock,
        profit_rate=0.12,
        peak_profit=0.2,
        current_ai_score=62,
        market_signature=("flat",),
        is_critical_zone=False,
        near_ai_exit_band=False,
        near_safe_profit_band=False,
    )
    stock["scalp_sim_ai_last_feature_signature"] = signature

    decision = state_handlers._resolve_scalp_sim_ai_budget_decision(
        stock,
        strategy="SCALPING",
        now_ts=1030.0,
        profit_rate=0.12,
        peak_profit=0.2,
        held_sec=45,
        current_ai_score=62,
        market_signature=("flat",),
        is_critical_zone=False,
        near_ai_exit_band=False,
        near_safe_profit_band=False,
    )

    assert decision["target"] is True
    assert decision["action"] == "reuse"
    assert decision["reuse_reason"] == "unchanged_feature_signature"


def test_scalp_sim_ai_budget_defers_when_cap_exhausted(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules(SCALP_SIM_AI_MAX_CALLS_PER_MIN=1))
    state_handlers._SCALP_SIM_AI_CALL_TIMES[:] = [1020.0]

    decision = state_handlers._resolve_scalp_sim_ai_budget_decision(
        _sim_holding_stock(scalp_sim_ai_last_feature_signature="old"),
        strategy="SCALPING",
        now_ts=1030.0,
        profit_rate=0.15,
        peak_profit=0.2,
        held_sec=45,
        current_ai_score=62,
        market_signature=("changed",),
        is_critical_zone=False,
        near_ai_exit_band=False,
        near_safe_profit_band=False,
    )

    assert decision["action"] == "defer"
    assert decision["defer_reason"] == "sim_ai_budget_exhausted"


def test_scalp_sim_ai_budget_critical_bypasses_cap(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules(SCALP_SIM_AI_MAX_CALLS_PER_MIN=1))
    state_handlers._SCALP_SIM_AI_CALL_TIMES[:] = [1020.0]

    decision = state_handlers._resolve_scalp_sim_ai_budget_decision(
        _sim_holding_stock(scalp_sim_ai_last_feature_signature="old"),
        strategy="SCALPING",
        now_ts=1030.0,
        profit_rate=-0.35,
        peak_profit=0.1,
        held_sec=45,
        current_ai_score=52,
        market_signature=("changed",),
        is_critical_zone=True,
        near_ai_exit_band=True,
        near_safe_profit_band=False,
    )

    assert decision["action"] == "call"
    assert decision["critical_bypass"] is True
    assert decision["call_reason"] == "sim_ai_critical_bypass"
    assert decision["critical_class"] == "hard_critical"
    assert decision["hard_critical_bypass"] is True


def test_scalp_sim_ai_budget_soft_loss_defers_instead_of_bypassing_cap(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules(SCALP_SIM_AI_MAX_CALLS_PER_MIN=1))
    state_handlers._SCALP_SIM_AI_CALL_TIMES[:] = [1020.0]

    decision = state_handlers._resolve_scalp_sim_ai_budget_decision(
        _sim_holding_stock(scalp_sim_ai_last_feature_signature="old"),
        strategy="SCALPING",
        now_ts=1030.0,
        profit_rate=-0.05,
        peak_profit=0.1,
        held_sec=45,
        current_ai_score=62,
        market_signature=("changed",),
        is_critical_zone=True,
        near_ai_exit_band=False,
        near_safe_profit_band=False,
    )

    assert decision["action"] == "defer"
    assert decision["defer_reason"] == "sim_ai_budget_exhausted"
    assert decision["critical_class"] == "soft_critical"
    assert decision["critical_bypass"] is not True
    assert decision["soft_critical_deferred"] is True


def test_scalp_sim_ai_budget_hard_loss_bypasses_cap(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules(SCALP_SIM_AI_MAX_CALLS_PER_MIN=1))
    state_handlers._SCALP_SIM_AI_CALL_TIMES[:] = [1020.0]

    decision = state_handlers._resolve_scalp_sim_ai_budget_decision(
        _sim_holding_stock(scalp_sim_ai_last_feature_signature="old"),
        strategy="SCALPING",
        now_ts=1030.0,
        profit_rate=-0.70,
        peak_profit=0.1,
        held_sec=45,
        current_ai_score=62,
        market_signature=("changed",),
        is_critical_zone=True,
        near_ai_exit_band=False,
        near_safe_profit_band=False,
    )

    assert decision["action"] == "call"
    assert decision["critical_bypass"] is True
    assert decision["critical_class"] == "hard_critical"
    assert decision["hard_critical_bypass"] is True
    assert "hard_loss" in decision["critical_reason"]


def test_scalp_sim_ai_budget_safe_profit_near_band_does_not_bypass_cap(monkeypatch):
    monkeypatch.setattr(state_handlers, "TRADING_RULES", _sim_budget_rules(SCALP_SIM_AI_MAX_CALLS_PER_MIN=1))
    state_handlers._SCALP_SIM_AI_CALL_TIMES[:] = [1020.0]

    decision = state_handlers._resolve_scalp_sim_ai_budget_decision(
        _sim_holding_stock(scalp_sim_ai_last_feature_signature="old"),
        strategy="SCALPING",
        now_ts=1030.0,
        profit_rate=0.45,
        peak_profit=0.45,
        held_sec=45,
        current_ai_score=62,
        market_signature=("changed",),
        is_critical_zone=True,
        near_ai_exit_band=False,
        near_safe_profit_band=True,
    )

    assert decision["action"] == "defer"
    assert decision["critical_class"] == "soft_critical"
    assert decision["critical_bypass"] is not True
    assert decision["soft_critical_deferred"] is True


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


def test_sync_scalp_simulator_targets_prunes_memory_rows_missing_from_state(monkeypatch, tmp_path):
    state_path = tmp_path / "scalp_live_sim_state.json"
    state_path.write_text(
        """
{
  "schema_version": 1,
  "simulation_book": "scalp_ai_buy_all",
  "active_positions": []
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", state_path)
    targets = [
        {
            "code": "005930",
            "name": "삼성전자",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "scalp_live_simulator": True,
            "sim_record_id": "SIM-STALE",
        },
        {
            "code": "000660",
            "name": "SK하이닉스",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "actual_order_submitted": True,
        },
    ]

    result = state_handlers.sync_scalp_simulator_targets_from_state(targets)

    assert result["removed"] == 1
    assert result["restored"] == 0
    assert [target["code"] for target in targets] == ["000660"]


def test_sync_scalp_simulator_targets_restores_state_rows(monkeypatch, tmp_path):
    state_path = tmp_path / "scalp_live_sim_state.json"
    state_path.write_text(
        """
{
  "schema_version": 1,
  "simulation_book": "scalp_ai_buy_all",
  "active_positions": [
    {
      "code": "005930",
      "name": "삼성전자",
      "strategy": "SCALPING",
      "status": "HOLDING",
      "simulation_book": "scalp_ai_buy_all",
      "scalp_live_simulator": true,
      "sim_record_id": "SIM-ACTIVE"
    }
  ]
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", state_path)
    targets = []

    result = state_handlers.sync_scalp_simulator_targets_from_state(targets)

    assert result["removed"] == 0
    assert result["restored"] == 1
    assert [target["sim_record_id"] for target in targets] == ["SIM-ACTIVE"]


def test_sync_scalp_simulator_targets_if_state_changed_prunes_external_preclose_sell(monkeypatch, tmp_path):
    state_path = tmp_path / "scalp_live_sim_state.json"
    state_path.write_text(
        """
{
  "schema_version": 1,
  "simulation_book": "scalp_ai_buy_all",
  "active_positions": [
    {
      "code": "005930",
      "name": "삼성전자",
      "strategy": "SCALPING",
      "status": "HOLDING",
      "simulation_book": "scalp_ai_buy_all",
      "scalp_live_simulator": true,
      "sim_record_id": "SIM-ACTIVE"
    }
  ]
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", state_path)
    targets = [
        {
            "code": "005930",
            "name": "삼성전자",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "scalp_live_simulator": True,
            "sim_record_id": "SIM-ACTIVE",
        }
    ]
    last_mtime = state_path.stat().st_mtime_ns
    state_path.write_text(
        '{"schema_version":1,"simulation_book":"scalp_ai_buy_all","active_positions":[]}',
        encoding="utf-8",
    )
    os.utime(state_path, ns=(last_mtime + 1_000_000_000, last_mtime + 1_000_000_000))

    result = state_handlers.sync_scalp_simulator_targets_if_state_changed(targets, last_mtime=last_mtime)

    assert result["synced"] is True
    assert result["removed"] == 1
    assert targets == []


def test_sync_scalp_simulator_targets_if_state_unchanged_does_not_prune(monkeypatch, tmp_path):
    state_path = tmp_path / "scalp_live_sim_state.json"
    state_path.write_text(
        '{"schema_version":1,"simulation_book":"scalp_ai_buy_all","active_positions":[]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", state_path)
    targets = [
        {
            "code": "005930",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "scalp_live_simulator": True,
            "sim_record_id": "SIM-STALE",
        }
    ]

    result = state_handlers.sync_scalp_simulator_targets_if_state_changed(
        targets,
        last_mtime=state_path.stat().st_mtime_ns,
    )

    assert result["synced"] is False
    assert len(targets) == 1


def test_persist_scalp_simulator_state_reconciles_external_preclose_sell(monkeypatch, tmp_path):
    state_path = tmp_path / "scalp_live_sim_state.json"
    state_path.write_text(
        """
{
  "schema_version": 1,
  "simulation_book": "scalp_ai_buy_all",
  "active_positions": [
    {
      "code": "005930",
      "name": "삼성전자",
      "strategy": "SCALPING",
      "status": "HOLDING",
      "simulation_book": "scalp_ai_buy_all",
      "scalp_live_simulator": true,
      "sim_record_id": "SIM-ACTIVE"
    }
  ]
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(state_handlers, "SCALP_SIM_STATE_PATH", state_path)
    targets = [
        {
            "code": "005930",
            "name": "삼성전자",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "simulation_book": "scalp_ai_buy_all",
            "scalp_live_simulator": True,
            "sim_record_id": "SIM-ACTIVE",
        }
    ]
    last_mtime = state_path.stat().st_mtime_ns
    monkeypatch.setattr(state_handlers, "_SCALP_SIM_STATE_LAST_SEEN_MTIME_NS", last_mtime)
    state_path.write_text(
        '{"schema_version":1,"simulation_book":"scalp_ai_buy_all","active_positions":[]}',
        encoding="utf-8",
    )
    os.utime(state_path, ns=(last_mtime + 1_000_000_000, last_mtime + 1_000_000_000))

    state_handlers.persist_scalp_simulator_state(targets)

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert targets == []
    assert payload["active_positions"] == []


def test_runtime_heartbeat_classifies_scalp_sim_as_non_real_holding():
    scalp_sim = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "simulation_book": "scalp_ai_buy_all",
        "actual_order_submitted": False,
    }
    swing_probe = {
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "simulation_book": "swing_intraday_live_equiv_probe",
        "actual_order_submitted": False,
    }
    assert sniper_runtime._is_runtime_simulation_target(scalp_sim)
    assert sniper_runtime._is_runtime_scalp_sim_target(scalp_sim)
    assert not sniper_runtime._is_runtime_probe_target(scalp_sim)
    assert sniper_runtime._is_runtime_simulation_target(swing_probe)
    assert not sniper_runtime._is_runtime_scalp_sim_target(swing_probe)
    assert sniper_runtime._is_runtime_probe_target(swing_probe)
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
