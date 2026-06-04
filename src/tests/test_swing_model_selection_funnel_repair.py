import json
import sys
from dataclasses import replace
from datetime import datetime, time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

import src.engine.sniper_state_handlers as state_handlers
import src.engine.swing_lifecycle_audit as lifecycle_audit_mod
from src.engine.swing_selection_funnel_report import (
    build_swing_selection_funnel_report,
    summarize_pipeline_events,
)
from src.engine.swing_daily_simulation_report import (
    build_swing_daily_simulation_report,
    filter_live_recommendations,
    load_recommendations,
    merge_recommendation_sources,
    simulate_swing_recommendations,
)
from src.engine.swing_lifecycle_audit import (
    build_swing_improvement_automation_report,
    build_swing_lifecycle_audit_report,
    build_swing_runtime_approval_report,
    build_swing_threshold_candidates,
    build_swing_threshold_ai_review_report,
    load_db_lifecycle_rows,
    summarize_db_lifecycle_rows,
    write_swing_lifecycle_outputs,
)
from src.model import common_v2
from src.model.common_v2 import daily_selection_stats, select_daily_candidates
from src.scanners.final_ensemble_scanner import classify_v2_csv_pick
from src.utils.constants import TRADING_RULES as CONFIG


def _has_hangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)


class FakeEventBus:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload):
        self.published.append((topic, payload))


class _NoopDB:
    class _Session:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query(self, *args, **kwargs):
            return self

        def filter_by(self, *args, **kwargs):
            return self

        def update(self, *args, **kwargs):
            return 0

        def first(self):
            return None

    def get_session(self):
        return self._Session()


def _score_rows():
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000001",
                "name": "A",
                "bull_regime": 1,
                "hybrid_mean": 0.36,
                "score": 0.10,
            },
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000002",
                "name": "B",
                "bull_regime": 1,
                "hybrid_mean": 0.34,
                "score": 0.90,
            },
        ]
    )


def test_recommendation_floor_matches_live_repair_policy():
    df = _score_rows()

    default_picks = select_daily_candidates(df, score_col="score", prob_col="hybrid_mean")
    repaired_picks = select_daily_candidates(
        df,
        score_col="score",
        prob_col="hybrid_mean",
        floor_bull=0.35,
        floor_bear=0.40,
        fallback_floor=0.35,
    )
    stats = daily_selection_stats(
        df,
        prob_col="hybrid_mean",
        floor_bull=0.35,
        floor_bear=0.40,
        fallback_floor=0.35,
    )

    assert default_picks.empty
    assert repaired_picks["code"].tolist() == ["000001"]
    assert stats.iloc[0]["safe_pool_count"] == 1
    assert stats.iloc[0]["floor_used"] == 0.35


def test_pickle_compat_registers_legacy_main_calibrator(monkeypatch):
    main_mod = sys.modules["__main__"]
    monkeypatch.delattr(main_mod, "PassThroughCalibrator", raising=False)

    common_v2.ensure_pickle_compat()

    assert getattr(main_mod, "PassThroughCalibrator") is common_v2.PassThroughCalibrator


def test_scanner_classifies_selected_rows_using_hybrid_mean_as_probability():
    row = pd.Series(
        {
            "selection_mode": "SELECTED",
            "hybrid_mean": 0.36,
            "meta_score": -0.03,
            "score": -0.03,
        }
    )

    classified = classify_v2_csv_pick(row)

    assert classified["should_save"] is True
    assert classified["position_tag"] == "META_V2"
    assert classified["pick_type"] == "MAIN"
    assert classified["prob"] == 0.36
    assert classified["meta_score"] == -0.03


def test_scanner_skips_fallback_diagnostic_rows():
    classified = classify_v2_csv_pick(
        pd.Series({"selection_mode": "FALLBACK_DIAGNOSTIC", "hybrid_mean": 0.20, "score": 0.99})
    )

    assert classified["should_save"] is False
    assert classified["position_tag"] == "EMPTY"


def test_swing_funnel_report_separates_raw_and_unique_event_counts():
    events = [
        {
            "stage": "blocked_swing_gap",
            "stock_code": "000001",
            "stock_name": "A",
            "record_id": 1,
            "fields": {"strategy": "KOSPI_ML"},
        },
        {
            "stage": "blocked_swing_gap",
            "stock_code": "000001",
            "stock_name": "A",
            "record_id": 1,
            "fields": {"strategy": "KOSPI_ML"},
        },
        {
            "stage": "blocked_gatekeeper_reject",
            "stock_code": "000002",
            "stock_name": "B",
            "record_id": 2,
            "fields": {"strategy": "KOSPI_ML", "action": "눌림 대기"},
        },
        {
            "stage": "order_bundle_submitted",
            "stock_code": "000003",
            "stock_name": "C",
            "record_id": 3,
            "fields": {"strategy": "KOSPI_ML"},
        },
        {
            "stage": "swing_sim_order_bundle_assumed_filled",
            "stock_code": "000004",
            "stock_name": "D",
            "record_id": 4,
            "fields": {
                "strategy": "KOSPI_ML",
                "actual_order_submitted": False,
                "orderbook_micro_ready": True,
                "orderbook_micro_state": "bullish",
                "orderbook_micro_observer_healthy": True,
                "swing_micro_advice": "SUPPORT_ENTRY",
                "swing_micro_runtime_effect": False,
            },
        },
        {
            "stage": "swing_scale_in_micro_context_observed",
            "stock_code": "000004",
            "stock_name": "D",
            "record_id": 4,
            "fields": {
                "strategy": "KOSPI_ML",
                "orderbook_micro_ready": True,
                "orderbook_micro_state": "bearish",
                "orderbook_micro_observer_healthy": True,
                "swing_micro_advice": "RISK_BEARISH",
                "swing_micro_runtime_effect": False,
            },
        },
        {
            "stage": "holding_flow_ofi_smoothing_applied",
            "stock_code": "000004",
            "stock_name": "D",
            "record_id": 4,
            "fields": {
                "strategy": "KOSPI_ML",
                "smoothing_action": "NO_CHANGE",
                "orderbook_micro_ready": False,
                "orderbook_micro_state": "insufficient",
                "orderbook_micro_observer_healthy": False,
                "swing_micro_advice": "MISSING",
                "swing_micro_runtime_effect": False,
            },
        },
    ]

    summary = summarize_pipeline_events(events)

    assert summary["raw_counts"]["blocked_swing_gap"] == 2
    assert summary["unique_record_counts"]["blocked_swing_gap"] == 1
    assert summary["gatekeeper_actions"]["눌림 대기"] == 1
    assert summary["gatekeeper_action_keys"]["pullback_wait"] == 1
    assert summary["submitted_unique_records"] == 1
    assert summary["simulated_order_unique_records"] == 1
    assert summary["ofi_qi_summary"]["entry_micro_state_counts"]["bullish"] == 1
    assert summary["ofi_qi_summary"]["scale_in_micro_advice_counts"]["RISK_BEARISH"] == 1
    assert summary["ofi_qi_summary"]["exit_smoothing_action_counts"]["NO_CHANGE"] == 1
    assert summary["ofi_qi_summary"]["stale_missing_count"] == 1
    assert summary["ofi_qi_summary"]["stale_missing_reason_counts"]["micro_missing"] == 1
    assert summary["ofi_qi_summary"]["stale_missing_reason_counts"]["micro_not_ready"] == 1
    assert summary["ofi_qi_summary"]["stale_missing_reason_counts"]["observer_unhealthy"] == 1
    assert summary["ofi_qi_summary"]["stale_missing_reason_combination_counts"] == {
        "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
    }
    assert summary["ofi_qi_summary"]["stale_missing_unique_record_count"] == 1
    assert summary["ofi_qi_summary"]["stale_missing_reason_combination_unique_record_counts"] == {
        "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
    }
    assert summary["ofi_qi_summary"]["stale_missing_group_counts"] == {"exit": 1}
    assert summary["ofi_qi_summary"]["stale_missing_group_unique_record_counts"] == {"exit": 1}
    assert summary["ofi_qi_summary"]["observer_unhealthy_overlap"] == {
        "observer_unhealthy_total": 1,
        "observer_unhealthy_with_other_reason": 1,
        "observer_unhealthy_only": 0,
    }
    assert summary["ofi_qi_summary"]["stale_missing_examples"][0]["record_id"] == "4"


def test_swing_lifecycle_audit_separates_intraday_probe_evidence_quality():
    report = build_swing_lifecycle_audit_report(
        "2026-05-11",
        recommendation_rows=[],
        diagnostic_summary={"selected_count": 0},
        db_rows=[],
        event_rows=[
            {
                "stage": "swing_probe_entry_candidate",
                "stock_code": "000001",
                "stock_name": "A",
                "record_id": 1,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "probe_origin_stage": "blocked_gatekeeper_reject",
                    "evidence_quality": "blocked_stage_intraday_probe",
                    "actual_order_submitted": False,
                },
            },
            {
                "stage": "swing_probe_sell_order_assumed_filled",
                "stock_code": "000001",
                "stock_name": "A",
                "record_id": 1,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "evidence_quality": "blocked_stage_intraday_probe",
                    "actual_order_submitted": False,
                    "profit_rate": "+2.10",
                },
            },
            {
                "stage": "swing_daily_simulation_proxy",
                "stock_code": "000002",
                "stock_name": "B",
                "record_id": 2,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "evidence_quality": "daily_next_open_proxy",
                    "actual_order_submitted": False,
                },
            },
        ],
        panic_sell_defense_report={
            "report_type": "panic_sell_defense",
            "panic_state": "RECOVERY_CONFIRMED",
            "panic_state_reasons": ["recovery confirmed by active sim/probe"],
            "policy": {"runtime_effect": "report_only_no_mutation"},
            "panic_metrics": {
                "panic_detected": True,
                "stop_loss_exit_count": 8,
                "max_rolling_30m_stop_loss_exit_count": 7,
            },
            "recovery_metrics": {
                "active_sim_probe": {
                    "active_positions": 2,
                    "profit_sample": 2,
                    "avg_unrealized_profit_rate_pct": 1.5,
                    "win_rate_pct": 50.0,
                    "wins": 1,
                    "losses": 1,
                    "flat": 0,
                    "provenance_check": {"passed": True, "violations": []},
                    "positions": [
                        {
                            "probe_origin_stage": "blocked_gatekeeper_reject",
                            "profit_rate_pct": 2.5,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                        {
                            "probe_origin_stage": "blocked_swing_gap",
                            "profit_rate_pct": 0.5,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        },
                    ],
                }
            },
        },
    )

    events = report["lifecycle_events"]
    assert events["raw_counts"]["swing_probe_entry_candidate"] == 1
    assert events["raw_counts"]["swing_probe_sell_order_assumed_filled"] == 1
    assert events["evidence_quality_counts"]["blocked_stage_intraday_probe"] == 2
    assert events["evidence_quality_counts"]["daily_next_open_proxy"] == 1
    assert events["actual_order_submitted_flags"]["false"] == 3
    assert report["panic_context"]["panic_state"] == "RECOVERY_CONFIRMED"
    assert report["panic_context"]["panic_detected"] is True
    assert report["panic_context"]["active_sim_probe"]["active_positions"] == 2
    assert report["panic_context"]["origin_outcome"]["blocked_gatekeeper_reject"]["avg_profit_rate_pct"] == 2.5
    assert report["panic_context"]["provenance_passed"] is True

    approval = build_swing_runtime_approval_report(report)
    assert approval["rolling_source_bundle"]["panic_context"]["panic_state"] == "RECOVERY_CONFIRMED"


def test_swing_micro_context_advice_is_observe_only(monkeypatch):
    monkeypatch.setattr(state_handlers.time, "time", lambda: 100.0)
    bullish = state_handlers._build_swing_micro_log_fields(
        {
            "ready": True,
            "micro_state": "bullish",
            "observer_healthy": True,
            "snapshot_age_ms": 100,
            "qi": 0.5,
            "ofi_norm": 0.6,
        },
        phase="entry",
    )
    bearish_pyramid = state_handlers._build_swing_micro_log_fields(
        {
            "ready": True,
            "micro_state": "bearish",
            "observer_healthy": True,
            "snapshot_age_ms": 100,
        },
        phase="scale_in",
        add_type="PYRAMID",
    )
    missing = state_handlers._build_swing_micro_log_fields(None, phase="entry")
    missing_with_fresh_ws_quote = state_handlers._build_swing_micro_log_fields(
        None,
        phase="scale_in",
        add_type="PYRAMID",
        ws_data={
            "curr": 10_000,
            "last_ws_update_ts": 99.6,
            "orderbook": {"bids": [{"price": 9_990}], "asks": [{"price": 10_010}]},
        },
    )
    avg_down = state_handlers._build_swing_micro_log_fields(
        {
            "ready": True,
            "micro_state": "bullish",
            "observer_healthy": True,
            "snapshot_age_ms": 100,
        },
        phase="scale_in",
        add_type="AVG_DOWN",
    )

    assert bullish["swing_micro_advice"] == "SUPPORT_ENTRY"
    assert bullish["swing_micro_runtime_effect"] is False
    assert bullish["swing_micro_counterfactual_price_action"] == "ALLOW_EXISTING_PRICE"
    assert bearish_pyramid["swing_micro_advice"] == "RISK_BEARISH"
    assert bearish_pyramid["swing_micro_counterfactual_price_action"] == "WAIT_FOR_PULLBACK"
    assert bearish_pyramid["swing_micro_micro_risk"] is True
    assert missing["swing_micro_advice"] == "MISSING"
    assert missing_with_fresh_ws_quote["swing_micro_advice"] == "MISSING"
    assert missing_with_fresh_ws_quote["swing_micro_source_quality_status"] == "observer_gap_with_fresh_ws_quote"
    assert missing_with_fresh_ws_quote["swing_micro_ws_quote_present"] is True
    assert missing_with_fresh_ws_quote["swing_micro_ws_quote_source"] == "last_ws_update_ts"
    assert avg_down["swing_micro_recovery_support_observed"] is True


def test_swing_intraday_probe_starts_virtual_holding_without_real_order(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_INTRADAY_PROBE_MAX_OPEN=10,
        SWING_INTRADAY_PROBE_MAX_DAILY=30,
        SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1,
    )
    logs = []
    event_bus = FakeEventBus()
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "EVENT_BUS", event_bus)
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "get_deposit",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("swing probe must not read real deposit")),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("real buy order must not be called")),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 501,
        "name": "SWING",
        "code": "000001",
        "strategy": "KOSPI_ML",
        "position_tag": "META_V2",
        "date": "2026-05-08",
    }

    assert state_handlers.maybe_start_swing_intraday_probe(
        stock=stock,
        code="000001",
        ws_data={"curr": 10_000, "v_pw": 95.0, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        origin_stage="blocked_gatekeeper_reject",
        runtime={
            "strategy": "KOSPI_ML",
            "now_ts": 1_768_090_000.0,
            "ratio": 0.10,
            "current_ai_score": 72.0,
            "current_vpw": 95.0,
        },
        extra_fields={"gatekeeper_action": "WAIT", "gatekeeper_allow_entry": False, "score": 72.0},
    )

    assert len(state_handlers.ACTIVE_TARGETS) == 1
    probe = state_handlers.ACTIVE_TARGETS[0]
    assert probe["status"] == "HOLDING"
    assert probe["swing_intraday_probe"] is True
    assert probe["swing_live_order_dry_run"] is True
    assert probe["actual_order_submitted"] is False
    assert probe["broker_order_forbidden"] is True
    assert probe["simulation_book"] == "swing_intraday_live_equiv_probe"
    assert probe["source_record_id"] == 501
    assert probe["buy_price"] == 10_000
    assert probe["buy_qty"] == 95
    assert [stage for stage, _ in logs] == ["swing_probe_entry_candidate", "swing_probe_holding_started"]
    assert logs[0][1]["qty_source"] == "sim_virtual_budget_dynamic_formula"
    assert logs[0][1]["virtual_budget_krw"] == 10_000_000
    assert logs[0][1]["target_budget"] == 1_000_000
    assert logs[0][1]["safe_budget"] == 950_000
    assert logs[0][1]["virtual_notional_used_krw"] == 950_000
    assert logs[0][1]["budget_authority"] == "sim_virtual_not_real_orderable_amount"
    assert event_bus.published == [("COMMAND_WS_REG", {"codes": ["000001"], "source": "swing_intraday_probe"})]
    assert (tmp_path / "swing_probe_state.json").exists()


def test_swing_probe_discard_classifies_symbol_cap_before_global_open_cap(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_INTRADAY_PROBE_MAX_OPEN=1,
        SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1,
        SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC=60,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DISCARD_LOG_TS", {})
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers,
        "ACTIVE_TARGETS",
        [
            {
                "code": "000001",
                "name": "SWING",
                "strategy": "KOSPI_ML",
                "status": "HOLDING",
                "swing_intraday_probe": True,
                "simulation_book": "swing_intraday_live_equiv_probe",
                "probe_origin_stage": "blocked_swing_score_vpw",
            }
        ],
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    assert not state_handlers.maybe_start_swing_intraday_probe(
        stock={"id": 501, "name": "SWING", "code": "000001", "strategy": "KOSPI_ML"},
        code="000001",
        ws_data={"curr": 10_000},
        origin_stage="blocked_swing_score_vpw",
        runtime={"strategy": "KOSPI_ML", "now_ts": 1_768_090_000.0},
    )

    assert logs == [
        (
            "swing_probe_discarded",
            {
                "simulation_book": "swing_intraday_live_equiv_probe",
                "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                "swing_intraday_probe": True,
                "simulated_order": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": "in_memory_probe_only",
                "decision_authority": "swing_sim_exploration_only",
                "probe_id": None,
                "probe_origin_stage": "blocked_swing_score_vpw",
                "probe_arm": None,
                "evidence_quality": "probe_capacity_observation",
                "evidence_quality_weight": None,
                "source_record_id": "501",
                "discard_reason": "max_per_symbol_reached",
                "blocker_authority": "probe_capacity_only",
                "quota_observation_scope": "symbol_probe_quota",
                "hard_gate": False,
                "allowed_runtime_apply": False,
                "strategy": "KOSPI_ML",
                "active_symbol_probes": 1,
            },
        )
    ]


def test_swing_probe_discard_rate_limits_repeated_global_cap_logs(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_INTRADAY_PROBE_MAX_OPEN=1,
        SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1,
        SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC=60,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DISCARD_LOG_TS", {})
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers,
        "ACTIVE_TARGETS",
        [
            {
                "code": "999999",
                "name": "OTHER",
                "strategy": "KOSPI_ML",
                "status": "HOLDING",
                "swing_intraday_probe": True,
                "simulation_book": "swing_intraday_live_equiv_probe",
                "probe_origin_stage": "blocked_swing_gap",
            }
        ],
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {"id": 502, "name": "NEXT", "code": "000002", "strategy": "KOSPI_ML"}
    for now_ts in (1_768_090_000.0, 1_768_090_030.0, 1_768_090_061.0):
        assert not state_handlers.maybe_start_swing_intraday_probe(
            stock=stock,
            code="000002",
            ws_data={"curr": 10_000},
            origin_stage="blocked_swing_gap",
            runtime={"strategy": "KOSPI_ML", "now_ts": now_ts},
        )

    assert [fields["discard_reason"] for _, fields in logs] == ["max_open_reached", "max_open_reached"]
    assert [fields["open_count"] for _, fields in logs] == [1, 1]
    assert {fields["quota_observation_scope"] for _, fields in logs} == {"global_probe_quota"}
    assert {fields["blocker_authority"] for _, fields in logs} == {"probe_capacity_only"}


def test_swing_probe_global_cap_discard_dedupes_across_symbols(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_INTRADAY_PROBE_MAX_OPEN=1,
        SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1,
        SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC=60,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DISCARD_LOG_TS", {})
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers,
        "ACTIVE_TARGETS",
        [
            {
                "code": "999999",
                "name": "OTHER",
                "strategy": "KOSPI_ML",
                "status": "HOLDING",
                "swing_intraday_probe": True,
                "simulation_book": "swing_intraday_live_equiv_probe",
                "probe_origin_stage": "blocked_swing_gap",
            }
        ],
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((code, stage, fields)),
    )

    for stock_code in ("000002", "000003"):
        assert not state_handlers.maybe_start_swing_intraday_probe(
            stock={"id": stock_code, "name": "NEXT", "code": stock_code, "strategy": "KOSPI_ML"},
            code=stock_code,
            ws_data={"curr": 10_000},
            origin_stage="blocked_swing_gap",
            runtime={"strategy": "KOSPI_ML", "now_ts": 1_768_090_000.0},
        )

    assert len(logs) == 1
    assert logs[0][2]["discard_reason"] == "max_open_reached"
    assert logs[0][2]["quota_observation_scope"] == "global_probe_quota"


def test_swing_probe_score_vpw_origin_quota_preserves_other_origin_slots(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_INTRADAY_PROBE_MAX_OPEN=10,
        SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1,
        SWING_INTRADAY_PROBE_SCORE_VPW_MAX_OPEN=1,
        SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC=0,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DISCARD_LOG_TS", {})
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers,
        "ACTIVE_TARGETS",
        [
            {
                "code": "000001",
                "name": "SCORE",
                "strategy": "KOSPI_ML",
                "status": "HOLDING",
                "swing_intraday_probe": True,
                "simulation_book": "swing_intraday_live_equiv_probe",
                "probe_origin_stage": "blocked_swing_score_vpw",
            }
        ],
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    assert not state_handlers.maybe_start_swing_intraday_probe(
        stock={"id": 503, "name": "SCORE2", "code": "000003", "strategy": "KOSPI_ML"},
        code="000003",
        ws_data={"curr": 10_000},
        origin_stage="blocked_swing_score_vpw",
        runtime={"strategy": "KOSPI_ML", "now_ts": 1_768_090_000.0},
    )

    assert logs[-1][1]["discard_reason"] == "origin_quota_reached"
    assert logs[-1][1]["origin_open_count"] == 1
    assert logs[-1][1]["origin_open_cap"] == 1


def test_restore_swing_intraday_probe_targets_skips_synthetic(monkeypatch, tmp_path):
    state_path = tmp_path / "swing_probe_state.json"
    state_path.write_text(
        json.dumps(
            {
                "active_positions": [
                    {
                        "code": "123456",
                        "name": "TEST",
                        "strategy": "KOSPI_ML",
                        "status": "HOLDING",
                        "probe_id": "SKIP",
                    },
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "strategy": "KOSPI_ML",
                        "status": "HOLDING",
                        "probe_id": "KEEP",
                        "buy_price": 10000,
                        "buy_qty": 1,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rules = replace(CONFIG, SWING_LIVE_ORDER_DRY_RUN_ENABLED=True, SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", state_path)
    targets = []

    restored = state_handlers.restore_swing_intraday_probe_targets(targets)

    assert restored == 1
    assert targets[0]["code"] == "005930"
    assert targets[0]["swing_intraday_probe"] is True
    assert targets[0]["actual_order_submitted"] is False
    assert targets[0]["broker_order_forbidden"] is True


def test_swing_probe_state_blocks_accidental_empty_overwrite(monkeypatch, tmp_path):
    state_path = tmp_path / "swing_probe_state.json"
    state_path.write_text(
        json.dumps(
            {
                "active_positions": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "strategy": "KOSPI_ML",
                        "status": "HOLDING",
                        "probe_id": "KEEP",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rules = replace(CONFIG, SWING_LIVE_ORDER_DRY_RUN_ENABLED=True, SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True)
    events = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", state_path)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(
        state_handlers,
        "_log_swing_probe_state_event",
        lambda stage, **fields: events.append((stage, fields)),
    )

    state_handlers.persist_swing_intraday_probe_state(reason="db_refresh_snapshot")

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(payload["active_positions"]) == 1
    assert events[-1][0] == "swing_probe_state_empty_overwrite_blocked"
    assert events[-1][1]["existing_active_count"] == 1


def test_swing_probe_state_allows_empty_overwrite_on_explicit_exit(monkeypatch, tmp_path):
    state_path = tmp_path / "swing_probe_state.json"
    state_path.write_text(
        json.dumps(
            {
                "active_positions": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "strategy": "KOSPI_ML",
                        "status": "HOLDING",
                        "probe_id": "KEEP",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rules = replace(CONFIG, SWING_LIVE_ORDER_DRY_RUN_ENABLED=True, SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True)
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", state_path)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "_log_swing_probe_state_event", lambda *args, **kwargs: None)

    state_handlers.persist_swing_intraday_probe_state(
        allow_empty_overwrite=True,
        reason="probe_exit",
    )

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["active_positions"] == []
    assert payload["persist_reason"] == "probe_exit"


def test_swing_same_symbol_loss_guard_blocks_probe_after_stop_loss(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
        SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT=-2.5,
        SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC=0,
    )
    logs = []
    errors = []
    now_ts = 1_768_090_000.0
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DISCARD_LOG_TS", {})
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(state_handlers, "log_error", lambda msg: errors.append(msg))

    stock = {"id": 701, "name": "HS", "code": "000001", "strategy": "KOSPI_ML"}
    cooldown_row = state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
        source_stage="swing_probe_sell_order_assumed_filled",
    )
    assert cooldown_row["source_probe_id"].startswith("701")
    assert cooldown_row["source_record_id"] == "701"
    assert cooldown_row["source_stage"] == "swing_probe_sell_order_assumed_filled"
    assert cooldown_row["source_id_source"] == "stock_id"
    logs.clear()

    assert not state_handlers.maybe_start_swing_intraday_probe(
        stock=stock,
        code="000001",
        ws_data={"curr": 10_000},
        origin_stage="blocked_gatekeeper_reject",
        runtime={"strategy": "KOSPI_ML", "now_ts": now_ts + 60, "ratio": 0.10},
        extra_fields={"curr_price": 9_999},
    )

    stages = [stage for stage, _ in logs]
    assert stages == ["swing_probe_discarded", "swing_reentry_counterfactual_after_loss"]
    discard = logs[0][1]
    counterfactual = logs[1][1]
    assert discard["discard_reason"] == "same_symbol_loss_reentry_cooldown"
    assert discard["actual_order_submitted"] is False
    assert discard["source_probe_id"] == cooldown_row["source_probe_id"]
    assert discard["source_record_id"] == cooldown_row["source_record_id"]
    assert discard["source_stage"] == cooldown_row["source_stage"]
    assert counterfactual["runtime_effect"] == "counterfactual_only"
    assert counterfactual["source_probe_id"] == cooldown_row["source_probe_id"]
    assert counterfactual["source_record_id"] == cooldown_row["source_record_id"]
    assert counterfactual["source_stage"] == cooldown_row["source_stage"]
    assert counterfactual["curr_price"] == 10_000
    assert counterfactual["event_field_conflict_keys"] == "curr_price"
    assert counterfactual["event_field_conflict_policy"] == "protected_field_preserved"
    assert counterfactual["actual_order_submitted"] is False
    assert counterfactual["broker_order_forbidden"] is True
    assert counterfactual["counterfactual_in_real_like_ev"] is False
    assert any("[SWING_PROBE_EVENT_FIELD_CONFLICT]" in msg for msg in errors)
    assert state_handlers.ACTIVE_TARGETS == []


def test_swing_same_symbol_loss_guard_allows_probe_after_cooldown(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
        SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT=-2.5,
    )
    now_ts = 1_768_090_000.0
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    stock = {"id": 702, "name": "HS", "code": "000001", "strategy": "KOSPI_ML"}
    state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
    )

    assert state_handlers.maybe_start_swing_intraday_probe(
        stock=stock,
        code="000001",
        ws_data={"curr": 10_000},
        origin_stage="blocked_gatekeeper_reject",
        runtime={"strategy": "KOSPI_ML", "now_ts": now_ts + 3601, "ratio": 0.10},
    )
    assert len(state_handlers.ACTIVE_TARGETS) == 1


def test_swing_same_symbol_loss_cooldown_source_id_prefers_probe_id(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
        SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT=-2.5,
    )
    logs = []
    now_ts = 1_768_090_000.0
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 702,
        "name": "HS",
        "code": "000001",
        "strategy": "KOSPI_ML",
        "probe_id": "PROBE-702",
        "source_record_id": "SRC-702",
    }
    row = state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
        source_stage="swing_probe_sell_order_assumed_filled",
    )

    assert row["source_probe_id"] == "PROBE-702"
    assert row["source_record_id"] == "SRC-702"
    assert row["source_id_source"] == "probe_id"
    assert logs[-1][1]["source_probe_id"] == "PROBE-702"
    assert logs[-1][1]["source_record_id"] == "SRC-702"
    assert logs[-1][1]["source_stage"] == "swing_probe_sell_order_assumed_filled"


def test_swing_same_symbol_loss_cooldown_source_id_uses_deterministic_fallback(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
        SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT=-2.5,
    )
    now_ts = 1_768_090_000.0
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    stock = {"name": "HS", "code": "000001", "strategy": "KOSPI_ML"}
    row = state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
        source_stage="exit",
    )

    assert row["source_probe_id"].startswith("swing_dry_run:2026-01-11:KOSPI_ML:000001:exit:")
    assert row["source_probe_id"] == row["source_record_id"]
    assert row["source_id_source"] == "deterministic_fallback"
    assert row["source_probe_id"] not in {"", "-", "None", "none", "null"}


def test_swing_same_symbol_loss_guard_ignores_take_profit_and_triggers_consecutive_losses(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
        SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT=-2.5,
        SWING_SAME_SYMBOL_LOSS_REENTRY_CONSECUTIVE_LOSSES=2,
    )
    logs = []
    now_ts = 1_768_090_000.0
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    stock = {"id": 703, "name": "HS", "code": "000001", "strategy": "KOSPI_ML"}

    assert state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="trailing_take_profit",
        profit_rate=2.7,
        now_ts=now_ts,
        actual_order_submitted=False,
    ) is None
    assert state_handlers.evaluate_swing_same_symbol_loss_reentry_guard(
        "000001", "KOSPI_ML", now_ts + 10
    )["allowed"] is True

    state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="manual_exit",
        profit_rate=-1.0,
        now_ts=now_ts + 20,
        actual_order_submitted=False,
    )
    assert state_handlers.evaluate_swing_same_symbol_loss_reentry_guard(
        "000001", "KOSPI_ML", now_ts + 21
    )["allowed"] is True
    state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="manual_exit",
        profit_rate=-1.2,
        now_ts=now_ts + 30,
        actual_order_submitted=False,
    )
    decision = state_handlers.evaluate_swing_same_symbol_loss_reentry_guard(
        "000001", "KOSPI_ML", now_ts + 31
    )
    assert decision["allowed"] is False
    assert decision["reason"] == "same_symbol_loss_reentry_cooldown"
    assert logs[-1][0] == "swing_same_symbol_loss_reentry_cooldown"
    assert logs[-1][1]["trigger"] == "consecutive_losses"


def test_swing_same_symbol_loss_guard_persists_across_probe_state_restore(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
    )
    now_ts = 1_768_090_000.0
    state_path = tmp_path / "swing_probe_state.json"
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", state_path)
    monkeypatch.setattr(state_handlers.time, "time", lambda: now_ts + 60)
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(state_handlers, "_log_swing_probe_state_event", lambda *args, **kwargs: None)

    stock = {"id": 704, "name": "HS", "code": "000001", "strategy": "KOSPI_ML"}
    state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
    )
    state_handlers.persist_swing_intraday_probe_state(allow_empty_overwrite=True, reason="unit")
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    cooldowns = persisted["same_symbol_loss_reentry_cooldowns"]
    persisted_row = next(iter(cooldowns.values()))
    assert persisted_row["source_probe_id"] not in {"", "-", "None", "none", "null"}
    assert persisted_row["source_record_id"] not in {"", "-", "None", "none", "null"}
    assert persisted_row["source_stage"] == "exit"

    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    state_handlers.restore_swing_intraday_probe_targets([])
    decision = state_handlers.evaluate_swing_same_symbol_loss_reentry_guard(
        "000001", "KOSPI_ML", now_ts + 120
    )
    assert decision["allowed"] is False
    assert decision["cooldown_remaining_sec"] > 0
    assert decision["source_probe_id"] == persisted_row["source_probe_id"]
    assert decision["source_record_id"] == persisted_row["source_record_id"]
    assert decision["source_stage"] == persisted_row["source_stage"]


def test_swing_same_symbol_loss_guard_blocks_dry_run_before_latency_submit(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
    )
    logs = []
    now_ts = 1_768_090_000.0
    cooldowns = {}
    alerted = {"000001"}
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers,
        "evaluate_live_buy_entry",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("latency gate must not run")),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {"id": 705, "name": "HS", "code": "000001", "strategy": "KOSPI_ML"}
    state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
    )
    logs.clear()

    result = state_handlers._submit_watching_triggered_entry(
        stock,
        "000001",
        {"curr": 10_000},
        admin_id=1,
        runtime={
            "strategy": "KOSPI_ML",
            "ratio": 0.10,
            "curr_price": 10_000,
            "liquidity_value": 0,
            "msg": "",
            "now_ts": now_ts + 60,
            "cooldowns": cooldowns,
            "alerted_stocks": alerted,
        },
    )

    assert result is False
    stages = [stage for stage, _ in logs]
    assert stages == ["budget_pass", "swing_same_symbol_loss_reentry_blocked", "swing_reentry_counterfactual_after_loss"]
    blocked = logs[1][1]
    counterfactual = logs[2][1]
    assert blocked["actual_order_submitted"] is False
    assert blocked["broker_order_forbidden"] is True
    assert blocked["runtime_effect"] == "pre_submit_block"
    assert counterfactual["runtime_effect"] == "counterfactual_only"
    assert cooldowns["000001"] > now_ts + 60
    assert "000001" not in alerted


def test_swing_same_symbol_loss_zero_qty_counterfactual_does_not_conflict_curr_price(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=True,
        SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=3600,
    )
    logs = []
    errors = []
    now_ts = 1_768_090_000.0
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DISCARD_LOG_TS", {})
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1)
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(state_handlers, "log_error", lambda msg: errors.append(msg))

    stock = {"id": 706, "name": "HS", "code": "000001", "strategy": "KOSPI_ML"}
    state_handlers._record_swing_same_symbol_loss_reentry_cooldown(
        stock,
        "000001",
        "KOSPI_ML",
        exit_rule="kospi_regime_stop_loss",
        profit_rate=-3.0,
        now_ts=now_ts,
        actual_order_submitted=False,
    )
    logs.clear()

    result = state_handlers._submit_watching_triggered_entry(
        stock,
        "000001",
        {"curr": 10_000},
        admin_id=1,
        runtime={
            "strategy": "KOSPI_ML",
            "ratio": 0.10,
            "curr_price": 10_000,
            "liquidity_value": 0,
            "msg": "",
            "now_ts": now_ts + 60,
            "cooldowns": {},
            "alerted_stocks": set(),
        },
    )

    assert result is False
    stages = [stage for stage, _ in logs]
    assert stages == ["blocked_zero_qty", "swing_probe_discarded", "swing_reentry_counterfactual_after_loss"]
    counterfactual = logs[2][1]
    assert counterfactual["curr_price"] == 10_000
    assert "event_field_conflict_keys" not in counterfactual
    assert "event_field_conflict_policy" not in counterfactual
    assert errors == []


def _allowing_latency_gate(qty=2, price=10_000):
    return {
        "allowed": True,
        "mode": "normal",
        "decision": "ALLOW_NORMAL",
        "latency_state": "SAFE",
        "reason": "unit",
        "signal_price": price,
        "latest_price": price,
        "order_price": price,
        "orders": [{"tag": "normal", "qty": qty, "price": price, "tif": "DAY"}],
        "ws_age_ms": 10,
        "ws_jitter_ms": 0,
        "spread_ratio": 0.0001,
        "quote_stale": False,
        "computed_allowed_slippage": 10,
        "latency_canary_applied": False,
        "latency_danger_reasons": [],
    }


def test_swing_dry_run_submit_path_assumes_fill_after_legacy_prior(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=False,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "describe_buy_capacity", lambda *args, **kwargs: (100_000, 100_000, 2, 1.0))
    monkeypatch.setattr(state_handlers, "evaluate_live_buy_entry", lambda *args, **kwargs: _allowing_latency_gate())
    monkeypatch.setattr(state_handlers, "resolve_lifecycle_decision", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_build_entry_submit_revalidation_fields", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_apply_entry_ai_price_canary", lambda **kwargs: (kwargs["planned_orders"], False))
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("dry-run must not call real buy order")),
    )
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    result = state_handlers._submit_watching_triggered_entry(
        {"id": 706, "name": "DRY", "code": "000001", "strategy": "KOSPI_ML"},
        "000001",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        admin_id=1,
        runtime={
            "strategy": "KOSPI_ML",
            "ratio": 0.10,
            "curr_price": 10_000,
            "liquidity_value": 0,
            "msg": "",
            "now_ts": 1_768_090_000.0,
            "cooldowns": {},
            "alerted_stocks": set(),
            "swing_entry_policy_source_stage": "blocked_swing_score_vpw",
        },
    )

    assert result is False
    stages = [stage for stage, _ in logs]
    assert "swing_sim_buy_order_assumed_filled" in stages
    assert "swing_sim_order_bundle_assumed_filled" in stages
    request = next(fields for stage, fields in logs if stage == "order_leg_request")
    assert request["actual_order_submitted"] is False
    assert request["broker_order_forbidden"] is True
    sim_fill = next(fields for stage, fields in logs if stage == "swing_sim_buy_order_assumed_filled")
    assert sim_fill["actual_order_submitted"] is False
    assert sim_fill["broker_order_forbidden"] is True
    assert sim_fill["would_submit_stage"] == "order_leg_sent"
    bundle = next(fields for stage, fields in logs if stage == "swing_sim_order_bundle_assumed_filled")
    assert bundle["actual_order_submitted"] is False
    assert bundle["broker_order_forbidden"] is True


def test_swing_submit_lifecycle_context_tolerates_missing_liquidity_value(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=False,
    )
    contexts = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_capacity",
        lambda *args, **kwargs: (100_000, 100_000, 2, 1.0),
    )
    monkeypatch.setattr(state_handlers, "evaluate_live_buy_entry", lambda *args, **kwargs: _allowing_latency_gate())
    monkeypatch.setattr(
        state_handlers,
        "resolve_lifecycle_decision",
        lambda *args, **kwargs: contexts.append(kwargs.get("context") or {}) or {},
    )
    monkeypatch.setattr(state_handlers, "_build_entry_submit_revalidation_fields", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_apply_entry_ai_price_canary", lambda **kwargs: (kwargs["planned_orders"], False))
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("dry-run must not call real buy order")),
    )
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    result = state_handlers._submit_watching_triggered_entry(
        {"id": 706, "name": "DRY", "code": "000001", "strategy": "KOSPI_ML"},
        "000001",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        admin_id=1,
        runtime={
            "strategy": "KOSPI_ML",
            "ratio": 0.10,
            "curr_price": 10_000,
            "liquidity_value": None,
            "msg": "",
            "now_ts": 1_768_090_000.0,
            "cooldowns": {},
            "alerted_stocks": set(),
            "swing_entry_policy_source_stage": "blocked_swing_score_vpw",
        },
    )

    assert result is False
    assert contexts
    assert contexts[0]["liquidity_value"] == 0


def test_swing_one_share_real_canary_submits_only_when_allowlisted(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=False,
    )
    logs = []
    orders = []
    stock = {"id": 707, "name": "CANARY", "code": "000001", "strategy": "KOSPI_ML"}
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "DB", _NoopDB())
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "describe_buy_capacity", lambda *args, **kwargs: (100_000, 100_000, 2, 1.0))
    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", lambda code, qty, price, *args, **kwargs: orders.append((code, qty, price)) or {"rt_cd": "0", "ord_no": "123"})
    monkeypatch.setattr(state_handlers, "evaluate_live_buy_entry", lambda *args, **kwargs: _allowing_latency_gate(qty=2))
    monkeypatch.setattr(state_handlers, "resolve_lifecycle_decision", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_build_entry_submit_revalidation_fields", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_apply_entry_ai_price_canary", lambda **kwargs: (kwargs["planned_orders"], False))
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "_publish_buy_signal_submission_notice", lambda *args, **kwargs: None)
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    result = state_handlers._submit_watching_triggered_entry(
        stock,
        "000001",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        admin_id=1,
        runtime={
            "strategy": "KOSPI_ML",
            "ratio": 0.10,
            "curr_price": 10_000,
            "liquidity_value": 0,
            "msg": "",
            "now_ts": 1_768_090_000.0,
            "cooldowns": {},
            "alerted_stocks": set(),
        },
    )

    assert result is False
    assert orders == []
    assert stock["actual_order_submitted"] is False
    assert stock.get("broker_order_forbidden", True) is True
    assert not [stage for stage, _ in logs if "real_canary" in stage]
    request = next(fields for stage, fields in logs if stage == "order_leg_request")
    assert request["actual_order_submitted"] is False
    assert request["broker_order_forbidden"] is True


def test_swing_one_share_real_canary_blocked_code_does_not_submit(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=False,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "DB", _NoopDB())
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers.kiwoom_orders, "get_deposit", lambda *args, **kwargs: 1_000_000)
    monkeypatch.setattr(state_handlers.kiwoom_orders, "describe_buy_capacity", lambda *args, **kwargs: (100_000, 100_000, 2, 1.0))
    monkeypatch.setattr(state_handlers, "evaluate_live_buy_entry", lambda *args, **kwargs: _allowing_latency_gate(qty=2))
    monkeypatch.setattr(state_handlers, "resolve_lifecycle_decision", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_build_entry_submit_revalidation_fields", lambda *args, **kwargs: {})
    monkeypatch.setattr(state_handlers, "_apply_entry_ai_price_canary", lambda **kwargs: (kwargs["planned_orders"], False))
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked canary must not call real buy order")),
    )
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    result = state_handlers._submit_watching_triggered_entry(
        {"id": 708, "name": "BLOCKED", "code": "000001", "strategy": "KOSPI_ML"},
        "000001",
        {"curr": 10_000, "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]}},
        admin_id=1,
        runtime={
            "strategy": "KOSPI_ML",
            "ratio": 0.10,
            "curr_price": 10_000,
            "liquidity_value": 0,
            "msg": "",
            "now_ts": 1_768_090_000.0,
            "cooldowns": {},
            "alerted_stocks": set(),
        },
    )

    assert result is False
    stages = [stage for stage, _ in logs]
    assert "swing_one_share_real_canary_blocked" not in stages
    assert "swing_sim_order_bundle_assumed_filled" in stages


def test_swing_watching_legacy_priors_flow_to_same_submit_policy(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED=False,
    )
    logs = []
    submit_sources = []

    class Radar:
        def __init__(self, score):
            self.score = score

        def analyze_signal_integrated(self, ws_data, ai_prob):
            return self.score, {}, "unit", {}, {}

    class Gatekeeper:
        def __init__(self, allow):
            self.allow = allow

        def evaluate_realtime_gatekeeper(self, **kwargs):
            return {
                "allow_entry": self.allow,
                "action_label": "WAIT" if not self.allow else "BUY",
                "action_key": "pullback_wait" if not self.allow else "buy",
                "report": "unit",
            }

    def fake_submit(stock, code, ws_data, admin_id, runtime):
        submit_sources.append(runtime.get("swing_entry_policy_source_stage"))

    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "LAST_AI_CALL_TIMES", {})
    monkeypatch.setattr(state_handlers, "_resolve_stock_marcap", lambda *args, **kwargs: 100_000_000_000)
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda *args, **kwargs: {"threshold": 3.5, "bucket_label": "unit"},
    )
    monkeypatch.setattr(state_handlers, "_should_block_swing_entry", lambda strategy: (False, None))
    monkeypatch.setattr(state_handlers, "kiwoom_utils", type("KU", (), {"build_realtime_analysis_context": staticmethod(lambda **kwargs: {})}))
    monkeypatch.setattr(state_handlers, "_submit_watching_triggered_entry", fake_submit)
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    cases = [
        ({"fluctuation": 4.2, "v_pw": 130.0}, Radar(85), Gatekeeper(True), "blocked_swing_gap"),
        ({"fluctuation": 1.0, "v_pw": 80.0}, Radar(45), None, "blocked_swing_score_vpw"),
        ({"fluctuation": 1.0, "v_pw": 130.0}, Radar(85), Gatekeeper(False), "blocked_gatekeeper_reject"),
    ]
    for idx, (ws_overrides, radar, ai_engine, expected_source) in enumerate(cases):
        state_handlers.COOLDOWNS = {}
        state_handlers.ALERTED_STOCKS = set()
        stock = {
            "id": 800 + idx,
            "name": f"SWING{idx}",
            "code": f"00000{idx}",
            "strategy": "KOSPI_ML",
            "prob": 0.8,
        }
        state_handlers.handle_watching_state(
            stock,
            stock["code"],
            {"curr": 10_000, "volume": 1000, **ws_overrides},
            admin_id=1,
            now_ts=1_768_090_000.0 + idx,
            now_dt=datetime.combine(datetime(2026, 5, 26), time(10, 0)),
            radar=radar,
            ai_engine=ai_engine,
        )
        assert submit_sources[-1] == expected_source

    policy_sources = [
        fields["feature_snapshot"]["source_stage"]
        for stage, fields in logs
        if stage == "swing_entry_policy_evaluated"
    ]
    assert policy_sources[-3:] == ["blocked_swing_gap", "blocked_swing_score_vpw", "blocked_gatekeeper_reject"]


def test_swing_watching_unconfirmed_market_regime_block_is_prior_observation(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED=False,
    )
    logs = []
    submit_sources = []

    class Radar:
        def analyze_signal_integrated(self, ws_data, ai_prob):
            return 85, {}, "unit", {}, {}

    class Gatekeeper:
        def evaluate_realtime_gatekeeper(self, **kwargs):
            return {
                "allow_entry": True,
                "action_label": "BUY",
                "action_key": "buy",
                "report": "unit",
            }

    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "LAST_AI_CALL_TIMES", {})
    monkeypatch.setattr(state_handlers, "_resolve_stock_marcap", lambda *args, **kwargs: 100_000_000_000)
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda *args, **kwargs: {"threshold": 3.5, "bucket_label": "unit"},
    )
    monkeypatch.setattr(state_handlers, "_should_block_swing_entry", lambda strategy: (True, "unit_regime_prior"))
    monkeypatch.setattr(state_handlers, "kiwoom_utils", type("KU", (), {"build_realtime_analysis_context": staticmethod(lambda **kwargs: {})}))
    monkeypatch.setattr(
        state_handlers,
        "_submit_watching_triggered_entry",
        lambda stock, code, ws_data, admin_id, runtime: submit_sources.append(runtime.get("swing_entry_policy_source_stage")),
    )
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    state_handlers.handle_watching_state(
        {"id": 809, "name": "SWING_REGIME", "code": "000009", "strategy": "KOSPI_ML", "prob": 0.8},
        "000009",
        {"curr": 10_000, "volume": 1000, "fluctuation": 1.0, "v_pw": 130.0},
        admin_id=1,
        now_ts=1_768_090_010.0,
        now_dt=datetime.combine(datetime(2026, 5, 26), time(10, 0)),
        radar=Radar(),
        ai_engine=Gatekeeper(),
    )

    assert submit_sources == ["market_regime_prior_observed"]
    prior = next(fields for stage, fields in logs if stage == "market_regime_prior_observed")
    assert prior["hard_gate"] is False
    assert prior["market_regime_block_downgraded_to_prior"] is True
    policy = next(fields for stage, fields in logs if stage == "swing_entry_policy_evaluated")
    assert policy["submit_allowed_by_policy"] is True
    assert policy["baseline_prior_features"]["market_regime"]["blocked"] is False
    assert policy["baseline_prior_features"]["market_regime"]["prior_observed"] is True


def test_swing_watching_confirmed_market_regime_block_keeps_block_observation(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED=False,
    )
    logs = []
    submit_sources = []

    class Radar:
        def analyze_signal_integrated(self, ws_data, ai_prob):
            return 85, {}, "unit", {}, {}

    class Gatekeeper:
        def evaluate_realtime_gatekeeper(self, **kwargs):
            return {
                "allow_entry": True,
                "action_label": "BUY",
                "action_key": "buy",
                "report": "unit",
            }

    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "LAST_AI_CALL_TIMES", {})
    monkeypatch.setattr(state_handlers, "_resolve_stock_marcap", lambda *args, **kwargs: 100_000_000_000)
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda *args, **kwargs: {"threshold": 3.5, "bucket_label": "unit"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_should_block_swing_entry",
        lambda strategy: (
            True,
            "confirmed_risk_context",
            {
                "confirmed_risk_block": True,
                "market_regime": "PANIC",
                "allow_swing_entry": False,
            },
        ),
    )
    monkeypatch.setattr(state_handlers, "kiwoom_utils", type("KU", (), {"build_realtime_analysis_context": staticmethod(lambda **kwargs: {})}))
    monkeypatch.setattr(
        state_handlers,
        "_submit_watching_triggered_entry",
        lambda stock, code, ws_data, admin_id, runtime: submit_sources.append(runtime.get("swing_entry_policy_source_stage")),
    )
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))

    state_handlers.handle_watching_state(
        {"id": 809, "name": "SWING_CONFIRMED_REGIME", "code": "000009", "strategy": "KOSPI_ML", "prob": 0.8},
        "000009",
        {"curr": 10_000, "volume": 1000, "fluctuation": 1.0, "v_pw": 130.0},
        admin_id=1,
        now_ts=1_768_090_010.0,
        now_dt=datetime.combine(datetime(2026, 5, 26), time(10, 0)),
        radar=Radar(),
        ai_engine=Gatekeeper(),
    )

    assert submit_sources == ["market_regime_block"]
    block = next(fields for stage, fields in logs if stage == "market_regime_block")
    assert block["hard_gate"] is True
    assert block["confirmed_risk_block"] is True
    assert block["market_regime_block_downgraded_to_prior"] is False
    policy = next(fields for stage, fields in logs if stage == "swing_entry_policy_evaluated")
    assert policy["submit_allowed_by_policy"] is True
    assert policy["baseline_prior_features"]["market_regime"]["blocked"] is True


def test_swing_watching_market_regime_prior_observed_flows_to_probe_and_submit_policy(monkeypatch):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=False,
        SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
    )
    logs = []
    submit_sources = []

    class Radar:
        def analyze_signal_integrated(self, ws_data, ai_prob):
            return 85, {}, "unit", {}, {}

    class Gatekeeper:
        def evaluate_realtime_gatekeeper(self, **kwargs):
            return {
                "allow_entry": True,
                "action_label": "BUY",
                "action_key": "buy",
                "report": "unit",
            }

    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "EVENT_BUS", FakeEventBus())
    monkeypatch.setattr(state_handlers, "LAST_AI_CALL_TIMES", {})
    monkeypatch.setattr(state_handlers, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {})
    monkeypatch.setattr(state_handlers, "_SWING_PROBE_DAILY_CREATED", {})
    monkeypatch.setattr(state_handlers, "_resolve_stock_marcap", lambda *args, **kwargs: 100_000_000_000)
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda *args, **kwargs: {"threshold": 3.5, "bucket_label": "unit"},
    )
    monkeypatch.setattr(
        state_handlers,
        "_should_block_swing_entry",
        lambda strategy: (
            False,
            "risk=RISK_OFF",
            {
                "market_regime_prior_observed": True,
                "market_regime_prior_reason": "market_regime_risk_off_prior",
                "market_regime": "RISK_OFF",
                "allow_swing_entry": False,
                "swing_score": 25,
                "risk_off_advisory": False,
                "single_market_risk_off_advisory": True,
                "confirmed_risk_off_advisory": False,
                "confirmed_risk_block": False,
                "panic_state": "NORMAL",
            },
        ),
    )
    monkeypatch.setattr(state_handlers, "kiwoom_utils", type("KU", (), {"build_realtime_analysis_context": staticmethod(lambda **kwargs: {})}))
    monkeypatch.setattr(
        state_handlers,
        "_submit_watching_triggered_entry",
        lambda stock, code, ws_data, admin_id, runtime: submit_sources.append(runtime.get("swing_entry_policy_source_stage")),
    )
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda stock, code, stage, **fields: logs.append((stage, fields)))
    monkeypatch.setattr(state_handlers, "persist_swing_intraday_probe_state", lambda reason="-": None)

    state_handlers.handle_watching_state(
        {"id": 810, "name": "SWING_PRIOR", "code": "000010", "strategy": "KOSPI_ML", "prob": 0.8},
        "000010",
        {"curr": 10_000, "volume": 1000, "fluctuation": 1.0, "v_pw": 130.0},
        admin_id=1,
        now_ts=1_768_090_010.0,
        now_dt=datetime.combine(datetime(2026, 5, 26), time(10, 0)),
        radar=Radar(),
        ai_engine=Gatekeeper(),
    )

    assert submit_sources == ["market_regime_prior_observed"]
    prior = next(fields for stage, fields in logs if stage == "market_regime_prior_observed")
    assert prior["hard_gate"] is False
    assert prior["single_market_risk_off_advisory"] is True
    policy = next(fields for stage, fields in logs if stage == "swing_entry_policy_evaluated")
    assert policy["submit_allowed_by_policy"] is True
    assert policy["baseline_prior_features"]["market_regime"]["prior_observed"] is True
    probe = next(fields for stage, fields in logs if stage == "swing_probe_entry_candidate")
    assert probe["actual_order_submitted"] is False
    assert probe["broker_order_forbidden"] is True
    assert probe["probe_origin_stage"] == "market_regime_prior_observed"


def test_swing_probe_holding_exit_logs_probe_only_sell(monkeypatch, tmp_path):
    rules = replace(
        CONFIG,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=True,
        SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=True,
        TRAILING_START_PCT=2.0,
    )
    logs = []
    monkeypatch.setattr(state_handlers, "TRADING_RULES", rules)
    monkeypatch.setattr(state_handlers, "DB", _NoopDB())
    monkeypatch.setattr(state_handlers, "HIGHEST_PRICES", {"swing_probe:PROBE1": 10_300})
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(state_handlers, "LAST_AI_CALL_TIMES", {})
    monkeypatch.setattr(state_handlers, "LAST_LOG_TIMES", {})
    monkeypatch.setattr(state_handlers, "SWING_INTRADAY_PROBE_STATE_PATH", tmp_path / "swing_probe_state.json")
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("real sell order must not be called")),
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )

    stock = {
        "id": 501,
        "name": "SWING",
        "code": "000001",
        "strategy": "KOSPI_ML",
        "position_tag": "META_V2",
        "status": "HOLDING",
        "date": "2026-05-11",
        "buy_price": 10_000,
        "buy_qty": 1,
        "buy_time": 1_768_090_000.0,
        "holding_started_at": 1_768_090_000.0,
        "swing_live_order_dry_run": True,
        "swing_intraday_probe": True,
        "simulation_book": "swing_intraday_live_equiv_probe",
        "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "probe_id": "PROBE1",
        "probe_origin_stage": "blocked_gatekeeper_reject",
        "probe_arm": "blocked_gatekeeper_reject",
        "evidence_quality": "blocked_stage_intraday_probe",
        "evidence_quality_weight": 0.7,
        "source_record_id": 501,
    }

    state_handlers.handle_holding_state(
        stock,
        "000001",
        {"curr": 10_300, "orderbook": {"asks": [{"price": 10_310}], "bids": [{"price": 10_290}]}},
        admin_id=None,
        market_regime="BULL",
        now_ts=1_768_090_180.0,
    )

    stages = [stage for stage, _ in logs]
    assert "exit_signal" in stages
    assert "swing_probe_exit_signal" in stages
    assert "swing_probe_sell_order_assumed_filled" in stages
    assert stock["status"] == "COMPLETED"
    assert stock["actual_order_submitted"] is False


def test_build_swing_selection_funnel_report_from_injected_sources():
    report = build_swing_selection_funnel_report(
        "2026-05-08",
        recommendation_rows=[
            {
                "selection_mode": "SELECTED",
                "position_tag": "META_V2",
                "hybrid_mean": 0.36,
                "meta_score": 0.01,
            }
        ],
        diagnostic_summary={
            "owner": "SwingModelSelectionFunnelRepair",
            "selection_mode": "SELECTED",
            "selected_count": 1,
            "fallback_written_to_recommendations": False,
        },
        db_rows=[
            {
                "position_tag": "META_V2",
                "status": "WATCHING",
                "buy_qty": 0,
                "buy_time": None,
            }
        ],
        event_rows=[],
    )

    assert report["model_selection"]["selected_count"] == 1
    assert report["recommendation_csv"]["selection_modes"]["SELECTED"] == 1
    assert report["db_recommendations"]["by_position_status"]["META_V2:WATCHING"] == 1
    assert report["recommendation_db_load"]["db_load_skip_reason"] == "loaded"
    json.dumps(report, ensure_ascii=False)


def test_swing_pipeline_summary_splits_probe_discard_raw_and_unique():
    events = [
        {
            "stage": "swing_probe_discarded",
            "stock_code": "000001",
            "stock_name": "A",
            "record_id": 1,
            "fields": {
                "strategy": "KOSPI_ML",
                "discard_reason": "max_open_reached",
                "probe_origin_stage": "blocked_swing_score_vpw",
            },
        },
        {
            "stage": "swing_probe_discarded",
            "stock_code": "000001",
            "stock_name": "A",
            "record_id": 1,
            "fields": {
                "strategy": "KOSPI_ML",
                "discard_reason": "max_open_reached",
                "probe_origin_stage": "blocked_swing_score_vpw",
            },
        },
        {
            "stage": "swing_probe_discarded",
            "stock_code": "000002",
            "stock_name": "B",
            "record_id": 2,
            "fields": {
                "strategy": "KOSPI_ML",
                "discard_reason": "origin_quota_reached",
                "probe_origin_stage": "blocked_swing_score_vpw",
            },
        },
    ]

    summary = summarize_pipeline_events(events)["swing_probe_discard_summary"]

    assert summary["raw_count"] == 3
    assert summary["unique_records"] == 2
    assert summary["reason_counts"] == {"max_open_reached": 2, "origin_quota_reached": 1}
    assert summary["reason_unique_record_counts"] == {"max_open_reached": 1, "origin_quota_reached": 1}
    assert summary["origin_reason_unique_record_counts"] == {
        "blocked_swing_score_vpw:max_open_reached": 1,
        "blocked_swing_score_vpw:origin_quota_reached": 1,
    }


def test_swing_daily_simulation_skips_fallback_diagnostics():
    recs = pd.DataFrame(
        [
            {"date": "2026-05-08", "code": "000001", "selection_mode": "SELECTED"},
            {"date": "2026-05-08", "code": "000002", "selection_mode": "FALLBACK_DIAGNOSTIC"},
        ]
    )

    live, summary = filter_live_recommendations(recs)

    assert live["code"].tolist() == ["000001"]
    assert summary["diagnostic_rows"] == 1


def test_swing_daily_simulation_closes_tp_path():
    recs = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2026-05-08"),
                "code": "000001",
                "name": "A",
                "selection_mode": "SELECTED",
                "bull_regime": 1,
                "hybrid_mean": 0.36,
                "meta_score": 0.1,
                "score_rank": 1,
                "floor_used": 0.35,
                "close": 100.0,
            }
        ]
    )
    quotes = pd.DataFrame(
        [
            {
                "quote_date": pd.Timestamp("2026-05-11"),
                "stock_code": "000001",
                "open_price": 100.0,
                "high_price": 106.0,
                "low_price": 99.0,
                "close_price": 105.0,
            }
        ]
    )

    rows = simulate_swing_recommendations(recs, quotes, target_date="2026-05-11")

    assert rows[0]["status"] == "CLOSED_SIM"
    assert rows[0]["entry_guard"] == "PASS_DRY_RUN"
    assert rows[0]["actual_order_submitted"] is False
    assert rows[0]["order_type_code"] == "6"
    assert rows[0]["qty_source"] == "sim_virtual_budget_dynamic_formula"
    assert rows[0]["virtual_budget_krw"] == 10_000_000
    assert rows[0]["counterfactual_notional_krw"] == rows[0]["buy_qty"] * 100
    assert rows[0]["exit_reason"] == "PRESET_TARGET"
    assert round(rows[0]["net_ret"], 4) == 0.0477


def test_build_swing_daily_simulation_report_from_injected_sources():
    report = build_swing_daily_simulation_report(
        "2026-05-08",
        recommendation_rows=pd.DataFrame(
            [{"date": "2026-05-08", "code": "000001", "selection_mode": "SELECTED"}]
        ),
        quote_rows=pd.DataFrame(),
    )

    assert report["report_type"] == "swing_daily_simulation"
    assert report["recommendation_summary"]["live_rows"] == 1
    assert report["simulation_summary"]["status_counts"]["PENDING_ENTRY"] == 1
    assert report["simulation_arm_summary"]["selection_only"]["status_counts"]["PENDING_ENTRY"] == 1
    assert report["simulation_arm_summary"]["gap_pass"]["status_counts"]["PENDING_ENTRY"] == 1
    assert report["simulation_arm_summary"]["gatekeeper_pass"]["status_counts"]["PENDING_ENTRY"] == 1


def test_swing_daily_recommendations_use_latest_prior_signal_date(tmp_path):
    reco = tmp_path / "daily_recommendations_v2.csv"
    reco.write_text(
        "date,code,name,selection_mode\n"
        "2026-05-08,000001,A,SELECTED\n",
        encoding="utf-8",
    )

    loaded = load_recommendations(reco, target_date="2026-05-11")

    assert loaded["code"].tolist() == ["000001"]
    assert str(loaded.iloc[0]["date"].date()) == "2026-05-08"


def test_swing_daily_recommendations_merge_db_non_csv_sources():
    csv_rows = pd.DataFrame(
        [
            {
                "date": "2026-05-08",
                "code": "000001",
                "name": "CSV",
                "strategy": "KOSPI_ML",
                "selection_mode": "SELECTED",
            }
        ]
    )
    db_rows = pd.DataFrame(
        [
            {
                "date": "2026-05-11",
                "code": "000001",
                "name": "CSV_DUP",
                "strategy": "KOSPI_ML",
                "selection_mode": "DB_FINAL_ENSEMBLE",
                "recommendation_source": "recommendation_history",
            },
            {
                "date": "2026-05-11",
                "code": "000002",
                "name": "DB",
                "strategy": "KOSDAQ_ML",
                "selection_mode": "DB_FINAL_ENSEMBLE",
                "recommendation_source": "recommendation_history",
            },
        ]
    )

    merged = merge_recommendation_sources(csv_rows, db_rows)

    assert merged["code"].tolist() == ["000001", "000002"]
    assert merged.loc[merged["code"] == "000001", "name"].iloc[0] == "CSV"
    assert set(merged["recommendation_source"]) == {"daily_recommendations_v2_csv", "recommendation_history"}


def test_swing_daily_simulation_reports_selection_and_gate_counterfactual_arms():
    report = build_swing_daily_simulation_report(
        "2026-05-11",
        recommendation_rows=pd.DataFrame(
            [
                {
                    "date": "2026-05-08",
                    "code": "000001",
                    "name": "A",
                    "selection_mode": "SELECTED",
                    "close": 100.0,
                    "bull_regime": 1,
                    "hybrid_mean": 0.50,
                    "score_rank": 1,
                }
            ]
        ),
        quote_rows=pd.DataFrame(
            [
                {
                    "quote_date": "2026-05-09",
                    "stock_code": "000001",
                    "stock_name": "A",
                    "open_price": 104.0,
                    "high_price": 110.0,
                    "low_price": 103.0,
                    "close_price": 109.0,
                }
            ]
        ),
    )

    arms = {row["sim_arm"]: row for row in report["simulation_arm_trades"]}
    assert arms["selection_only"]["status"] == "CLOSED_SIM"
    assert arms["selection_only"]["entry_guard"] == "PASS_SELECTION_ONLY"
    assert arms["gap_pass"]["status"] == "BLOCKED_SWING_GAP"
    assert arms["gatekeeper_pass"]["status"] == "BLOCKED_SWING_GAP"
    assert report["simulation_arm_summary"]["selection_only"]["closed_count"] == 1


def test_swing_daily_simulation_runtime_funnel_summary(tmp_path):
    events = tmp_path / "pipeline_events_2026-05-11.jsonl"
    events.write_text(
        json.dumps(
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "blocked_swing_gap",
                "stock_name": "A",
                "stock_code": "000001",
                "record_id": 11,
                "fields": {"strategy": "KOSPI_ML"},
            },
            ensure_ascii=False,
        )
        + "\n"
        + json.dumps(
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "blocked_gatekeeper_reject",
                "stock_name": "B",
                "stock_code": "000002",
                "record_id": 12,
                "fields": {"strategy": "KOSDAQ_ML"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_swing_daily_simulation_report(
        "2026-05-11",
        recommendation_rows=pd.DataFrame(),
        quote_rows=pd.DataFrame(),
        include_runtime_funnel=True,
        pipeline_events_path=events,
    )

    funnel = report["runtime_entry_funnel"]
    assert funnel["available"] is True
    assert funnel["raw_counts"]["blocked_swing_gap"] == 1
    assert funnel["unique_record_counts"]["blocked_gatekeeper_reject"] == 1


def test_swing_lifecycle_audit_tracks_full_funnel_and_observation_axes():
    report = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[
            {
                "selection_mode": "SELECTED",
                "position_tag": "META_V2",
                "hybrid_mean": 0.36,
                "meta_score": 0.01,
            }
        ],
        diagnostic_summary={
            "owner": "SwingModelSelectionFunnelRepair",
            "selection_mode": "SELECTED",
            "selected_count": 1,
            "floor_bull": 0.35,
            "floor_bear": 0.40,
            "safe_pool_count": 1,
            "fallback_written_to_recommendations": False,
        },
        db_rows=[
            {
                "position_tag": "META_V2",
                "status": "COMPLETED",
                "buy_qty": 1,
                "buy_time": "2026-05-08T09:30:00",
                "profit_rate": 1.2,
                "profit": 1200,
            }
        ],
        event_rows=[
            {
                "stage": "blocked_swing_gap",
                "stock_code": "000001",
                "stock_name": "A",
                "record_id": 1,
                "fields": {"strategy": "KOSPI_ML", "gap_pct": 3.2},
            },
            {
                "stage": "blocked_gatekeeper_reject",
                "stock_code": "000002",
                "stock_name": "B",
                "record_id": 2,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "action": "눌림 대기",
                    "cooldown_sec": 1200,
                    "gatekeeper_eval_ms": 1000,
                },
            },
            {
                "stage": "swing_sim_scale_in_order_assumed_filled",
                "stock_code": "000003",
                "stock_name": "C",
                "record_id": 3,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "add_type": "PYRAMID",
                    "add_trigger": "profit_breakout",
                    "price_policy": "best_bid",
                    "add_ratio": 0.25,
                    "post_add_outcome": "pending",
                    "effective_qty": 2,
                    "actual_order_submitted": False,
                    "orderbook_micro_ready": True,
                    "orderbook_micro_state": "bearish",
                    "orderbook_micro_observer_healthy": True,
                    "swing_micro_advice": "RISK_BEARISH",
                    "swing_micro_micro_risk": True,
                    "swing_micro_risk": True,
                    "swing_micro_runtime_effect": False,
                },
            },
            {
                "stage": "swing_sim_sell_order_assumed_filled",
                "stock_code": "000003",
                "stock_name": "C",
                "record_id": 3,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "exit_source": "PRESET_TARGET",
                    "profit_rate": 1.5,
                    "actual_order_submitted": False,
                    "orderbook_micro_ready": True,
                    "orderbook_micro_state": "bullish",
                    "orderbook_micro_observer_healthy": True,
                    "swing_micro_advice": "SUPPORT_ENTRY",
                    "swing_micro_runtime_effect": False,
                },
            },
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "stock_code": "000003",
                "stock_name": "C",
                "record_id": 3,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "smoothing_action": "NO_CHANGE",
                    "orderbook_micro_ready": True,
                    "orderbook_micro_state": "neutral",
                    "orderbook_micro_observer_healthy": True,
                    "swing_micro_advice": "WAIT_FOR_PULLBACK",
                    "swing_micro_runtime_effect": False,
                },
            },
            {
                "stage": "gatekeeper_fast_reuse",
                "stock_code": "000004",
                "stock_name": "D",
                "record_id": 4,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "ai_schema_valid": True,
                    "ai_response_ms": 420,
                    "ai_cost_krw": 1.5,
                    "ai_prompt_type": "swing_gatekeeper",
                    "ai_model": "gpt-5-nano",
                },
            },
        ],
    )

    assert report["report_type"] == "swing_lifecycle_audit"
    assert report["lifecycle_events"]["unique_record_counts"]["blocked_swing_gap"] == 1
    assert report["lifecycle_events"]["gatekeeper_actions"]["눌림 대기"] == 1
    assert report["lifecycle_events"]["gatekeeper_action_keys"]["pullback_wait"] == 1
    assert report["lifecycle_events"]["add_types"]["PYRAMID"] == 1
    assert report["recommendation_db_load"]["db_load_skip_reason"] == "loaded"
    assert report["lifecycle_events"]["scale_in_observation"]["action_groups"]["PYRAMID"] == 1
    assert report["lifecycle_events"]["scale_in_observation"]["price_policies"]["best_bid"] == 1
    assert report["ai_contract_audit"]["metrics"]["schema_valid_rate"] == 1.0
    assert report["ai_contract_audit"]["metrics"]["latency_ms"]["p95"] == 420.0
    assert report["ai_contract_audit"]["metrics"]["prompt_types"]["swing_gatekeeper"] == 1
    assert report["lifecycle_events"]["ofi_qi_summary"]["scale_in_micro_advice_counts"]["RISK_BEARISH"] == 1
    assert report["lifecycle_events"]["ofi_qi_summary"]["exit_smoothing_action_counts"]["NO_CHANGE"] == 1
    assert report["db_lifecycle"]["completed_rows"] == 1
    assert report["observation_axis_coverage"]["runtime_change"] is False
    assert report["observation_axis_coverage"]["instrumentation_gap_count"] == report["observation_axis_summary"]["instrumentation_gap_count"]
    assert report["observation_axis_coverage"]["stage_counts"]
    axis_status = {axis["axis_id"]: axis["status"] for axis in report["observation_axes"]}
    assert axis_status["swing_scale_in_avg_down_pyramid"] == "ready"
    assert axis_status["swing_scale_in_ofi_qi_confirmation"] == "ready"

    families = {family["family"] for family in report["threshold_families"]}
    assert "swing_entry_ofi_qi_execution_quality" in families
    assert "swing_scale_in_ofi_qi_confirmation" in families
    assert "swing_exit_ofi_qi_smoothing" in families
    json.dumps(report, ensure_ascii=False)


def test_swing_lifecycle_audit_reports_db_gap_and_report_only_zero_sample_reason():
    report = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[
            {
                "selection_mode": "SELECTED",
                "position_tag": "META_V2",
                "hybrid_mean": 0.37,
                "meta_score": 0.02,
            }
        ],
        diagnostic_summary={"selected_count": 1},
        db_rows=[],
        event_rows=[
            {
                "stage": "market_regime_pass",
                "stock_code": "000001",
                "stock_name": "A",
                "record_id": 1,
                "fields": {"strategy": "KOSPI_ML", "market_regime": "BULL"},
            }
        ],
    )
    automation = build_swing_improvement_automation_report(report)
    orders = {order["order_id"]: order for order in automation["code_improvement_orders"]}

    assert report["recommendation_db_load"]["db_load_gap"] is True
    assert report["recommendation_db_load"]["db_load_skip_reason"] == "csv_rows_positive_db_rows_zero"
    assert report["recommendation_db_load"]["db_load_missing_rows"] == 1
    assert report["recommendation_db_load"]["db_load_next_action"] == "investigate_recommendation_history_write_path"
    assert "swing_gap_market_budget_price_qty" in report["observation_axis_coverage"]["missing_required_fields_by_axis"]
    assert report["lifecycle_events"]["scale_in_observation"]["zero_sample_reason"] == "no_candidate"
    assert orders["order_swing_recommendation_db_load_gap"]["runtime_effect"] is False
    assert orders["order_swing_recommendation_db_load_gap"]["allowed_runtime_apply"] is False
    assert "db_load_skip_reason=csv_rows_positive_db_rows_zero" in orders["order_swing_recommendation_db_load_gap"]["evidence"]
    assert "zero_sample_reason=no_candidate" in orders["order_swing_scale_in_avg_down_pyramid_observation"]["evidence"]
    assert automation["ev_report_summary"]["db_load_gap"] is True
    assert automation["ev_report_summary"]["scale_in_zero_sample_reason"] == "no_candidate"


def test_swing_lifecycle_db_load_accepts_missing_optional_sell_qty(tmp_path):
    db_path = tmp_path / "recommendation_history.sqlite"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE recommendation_history (
                rec_date TEXT,
                stock_code TEXT,
                stock_name TEXT,
                strategy TEXT,
                trade_type TEXT,
                position_tag TEXT,
                status TEXT,
                prob REAL,
                buy_price REAL,
                buy_qty INTEGER,
                buy_time TEXT,
                sell_price REAL,
                sell_time TEXT,
                profit_rate REAL,
                profit REAL,
                updated_at TEXT
            )
        """))
        conn.execute(
            text("""
                INSERT INTO recommendation_history (
                    rec_date, stock_code, stock_name, strategy, trade_type, position_tag,
                    status, prob, buy_price, buy_qty, buy_time, sell_price, sell_time,
                    profit_rate, profit, updated_at
                )
                VALUES (
                    '2026-05-11', '000001', 'A', 'KOSPI_ML', 'BUY', 'META_V2',
                    'COMPLETED', 0.41, 10000, 1, '2026-05-11 09:00:00',
                    10100, '2026-05-11 10:00:00', 1.0, 100, '2026-05-11 10:00:00'
                )
            """)
        )

    rows = load_db_lifecycle_rows("2026-05-11", db_url=db_url)
    summary = summarize_db_lifecycle_rows(rows)

    assert len(rows) == 1
    assert "sell_qty" not in rows[0]
    assert summary["completed_rows"] == 1
    assert summary["status_counts"]["COMPLETED"] == 1


def test_swing_lifecycle_audit_ingests_daily_simulation_opportunity():
    daily_simulation = {
        "report_type": "swing_daily_simulation",
        "target_date": "2026-05-08",
        "simulation_arm_summary": {
            "selection_only": {"closed_count": 1, "win_rate": 1.0},
            "gap_pass": {"closed_count": 1, "win_rate": 1.0},
            "gatekeeper_pass": {"closed_count": 1, "win_rate": 1.0},
        },
        "runtime_entry_funnel": {
            "available": True,
            "raw_counts": {"blocked_swing_gap": 1, "blocked_gatekeeper_reject": 1},
            "unique_record_counts": {"blocked_swing_gap": 1, "blocked_gatekeeper_reject": 1},
        },
        "simulation_arm_trades": [
            {
                "code": "000001",
                "name": "A",
                "recommendation_source": "recommendation_history",
                "position_tag": "BREAKOUT",
                "selection_mode": "DB_FINAL_ENSEMBLE",
                "runtime_status": "WATCHING",
                "sim_arm": "selection_only",
                "status": "CLOSED_SIM",
                "entry_guard": "PASS_SELECTION_ONLY",
                "net_ret": 0.04,
                "actual_order_submitted": False,
            },
            {
                "code": "000002",
                "name": "B",
                "recommendation_source": "daily_recommendations_v2_csv",
                "position_tag": "PULLBACK",
                "selection_mode": "SELECTED",
                "runtime_status": "WATCHING",
                "sim_arm": "gap_pass",
                "status": "BLOCKED_SWING_GAP",
                "entry_guard": "BLOCKED_SWING_GAP",
                "net_ret": 0.03,
                "actual_order_submitted": False,
            },
            {
                "code": "000003",
                "name": "C",
                "recommendation_source": "daily_recommendations_v2_csv",
                "position_tag": "BREAKOUT",
                "selection_mode": "SELECTED",
                "runtime_status": "WATCHING",
                "sim_arm": "gatekeeper_pass",
                "status": "BLOCKED_GATEKEEPER_REJECT",
                "entry_guard": "BLOCKED_GATEKEEPER_REJECT",
                "net_ret": 0.02,
                "actual_order_submitted": False,
            },
        ],
    }
    audit = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[{"selection_mode": "SELECTED", "position_tag": "META_V2"}],
        diagnostic_summary={"selected_count": 1},
        db_rows=[],
        event_rows=[],
        daily_simulation_report=daily_simulation,
    )
    automation = build_swing_improvement_automation_report(audit)
    orders = {order["order_id"]: order for order in automation["code_improvement_orders"]}

    assert audit["simulation_opportunity"]["available"] is True
    assert audit["simulation_opportunity"]["closed_count"] == 3
    assert audit["simulation_opportunity"]["winner_count"] == 3
    assert audit["simulation_opportunity"]["family_opportunity"]["swing_selection_top_k"]["winner_count"] == 1
    assert audit["simulation_opportunity"]["family_opportunity"]["swing_market_regime_sensitivity"]["winner_count"] == 1
    assert audit["simulation_opportunity"]["family_opportunity"]["swing_gatekeeper_reject_cooldown"]["winner_count"] == 1
    assert orders["order_swing_selection_source_counterfactual_review"]["threshold_family"] == "swing_selection_top_k"
    assert orders["order_swing_gap_regime_counterfactual_review"]["threshold_family"] == "swing_market_regime_sensitivity"
    assert orders["order_swing_gatekeeper_counterfactual_review"]["threshold_family"] == "swing_gatekeeper_reject_cooldown"
    assert automation["ev_report_summary"]["simulation_opportunity_closed_count"] == 3
    assert automation["ev_report_summary"]["simulation_opportunity_winner_count"] == 3


def test_swing_threshold_ai_review_is_proposal_only_and_guarded():
    audit = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[],
        diagnostic_summary={"selected_count": 0},
        db_rows=[],
        event_rows=[],
    )
    raw_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "swing_model_floor",
                "anomaly_type": "entry_drought",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_down",
                    "proposed_value": 0.1,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "rolling_5d",
                },
                "correction_reason": "candidate count is empty",
                "required_evidence": ["safe_pool_count"],
                "risk_flags": ["sample_shortage"],
            }
        ],
    }

    review = build_swing_threshold_ai_review_report(audit, ai_raw_response=raw_response)
    item = next(row for row in review["items"] if row["family"] == "swing_model_floor")

    assert review["runtime_change"] is False
    assert review["policy"]["authority"] == "proposal_only"
    assert item["guard_decision"]["effective_value"] == 0.2
    assert item["guard_decision"]["clamped"] is True
    assert item["guard_decision"]["runtime_change"] is False


def test_swing_threshold_ai_review_drops_real_preapply_primary_ev_claim():
    audit = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[],
        diagnostic_summary={"selected_count": 0},
        db_rows=[],
        event_rows=[],
    )
    raw_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "swing_model_floor",
                "anomaly_type": "entry_drought",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_down",
                    "proposed_value": 0.1,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "rolling_5d",
                    "reason": "preapply_real primary_ev from one-share sample",
                },
                "correction_reason": "merge_real_pnl_with_sim_probe_ev",
                "required_evidence": ["safe_pool_count"],
                "risk_flags": ["sample_shortage"],
            }
        ],
    }

    review = build_swing_threshold_ai_review_report(audit, ai_raw_response=raw_response)

    assert review["ai_status"] == "parsed_empty"
    assert "corrections[0] evidence_authority_violation" in review["parse_warnings"]
    item = next(row for row in review["items"] if row["family"] == "swing_model_floor")
    assert item["ai_tier2_proposal"]["proposal_status"] == "not_provided"


def test_swing_threshold_ai_review_prompt_contract_is_english_ascii():
    instructions = lifecycle_audit_mod._build_openai_review_instructions()

    assert "swing-trading lifecycle threshold reviewer" in instructions
    assert "Domain glossary" in instructions
    assert not _has_hangul(instructions)


def _approval_ready_audit(**overrides):
    audit = {
        "date": "2026-05-08",
        "model_selection": {
            "selected_count": 5,
            "floor_bull": 0.35,
            "floor_bear": 0.40,
            "fallback_written_to_recommendations": False,
        },
        "recommendation_csv": {"csv_rows": 5, "selection_modes": {"SELECTED": 5}},
        "recommendation_db_load": {
            "db_load_gap": False,
            "selection_modes": {"SELECTED": 5},
        },
        "db_lifecycle": {
            "db_rows": 5,
            "completed_rows": 8,
            "valid_profit_rows": 8,
            "avg_profit_rate": 1.1,
        },
        "observation_axis_summary": {
            "instrumentation_gap_count": 0,
            "hold_sample_count": 0,
        },
        "lifecycle_events": {
            "raw_counts": {
                "blocked_gatekeeper_reject": 5,
                "market_regime_block": 0,
                "market_regime_pass": 0,
            },
            "unique_record_counts": {
                "blocked_gatekeeper_reject": 5,
                "market_regime_block": 0,
                "market_regime_pass": 0,
            },
            "group_unique_counts": {"entry": 5, "exit": 3, "holding": 0, "scale_in": 0},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 5,
            "ofi_qi_summary": {},
            "record_timeline_sample": [],
        },
    }
    for key, value in overrides.items():
        audit[key] = value
    return audit


def test_swing_runtime_approval_requires_tradeoff_score_not_perfect_metrics():
    audit = _approval_ready_audit()

    candidates = build_swing_threshold_candidates(audit)
    cooldown = next(item for item in candidates if item["family"] == "swing_gatekeeper_reject_cooldown")

    assert cooldown["calibration_state"] == "approval_required"
    assert cooldown["human_approval_required"] is True
    assert cooldown["tradeoff_score"] >= 0.68
    assert cooldown["tradeoff_components"]["regime_robustness"] < 0.7
    assert cooldown["target_env_keys"] == ["ML_GATEKEEPER_REJECT_COOLDOWN"]
    assert cooldown["actual_order_submission_change"] is False
    assert cooldown["dry_run_required"] is True


def test_swing_runtime_approval_blocks_hard_floor_failures():
    audit = _approval_ready_audit(
        recommendation_db_load={"db_load_gap": True, "selection_modes": {"SELECTED": 5}},
    )

    candidates = build_swing_threshold_candidates(audit)
    cooldown = next(item for item in candidates if item["family"] == "swing_gatekeeper_reject_cooldown")

    assert cooldown["calibration_state"] == "freeze"
    assert cooldown["human_approval_required"] is False
    assert "db_load_gap" in cooldown["hard_floor_block_reasons"]


def test_swing_runtime_approval_report_emits_machine_readable_requests():
    report = build_swing_runtime_approval_report(_approval_ready_audit(), {"ai_status": "parsed"})

    assert report["report_type"] == "swing_runtime_approval"
    assert report["policy"]["perfect_spot_required"] is False
    assert report["policy"]["ev_calibration_source"] == "combined_real_plus_sim"
    assert report["policy"]["sim_authority"] == "equal_for_ev_calibration_when_sim_lifecycle_closed"
    assert report["policy"]["runtime_apply_requires_user_approval_artifact"] is False
    assert report["policy"]["final_full_live_requires_user_approval"] is True
    assert report["approval_requests"]
    request = report["approval_requests"][0]
    assert request["approval_id"].startswith("swing_runtime_approval:2026-05-08:")
    assert request["calibration_state"] == "dry_run_auto_apply_ready"
    assert request["auto_approval_state"] == "ai_tier2_auto_approved"
    assert request["human_approval_required"] is False
    assert request["actual_order_submitted"] is False
    assert request["combined_ev_authority"] is True
    assert report["rolling_source_bundle"]["combined"]["avg_profit_rate"] == 1.1
    assert (
        report["rolling_source_bundle"]["source_authority"]["combined"]
        == "primary_tradeoff_view_for_approval_request_generation"
    )


def test_swing_runtime_approval_report_blocks_pre_final_auto_when_tier2_missing():
    report = build_swing_runtime_approval_report(_approval_ready_audit())

    assert not [
        item
        for item in report["approval_requests"]
        if item.get("calibration_state") == "dry_run_auto_apply_ready"
    ]
    blocked = [
        item
        for item in report["blocked_requests"]
        if item.get("family") == "swing_gatekeeper_reject_cooldown"
    ][0]
    assert "ai_tier2_validation_not_parsed:missing" in blocked["block_reasons"]


def test_swing_runtime_approval_emits_scale_in_real_canary_request_when_arm_ready():
    audit = _approval_ready_audit(
        lifecycle_events={
            "raw_counts": {},
            "unique_record_counts": {},
            "group_unique_counts": {"entry": 5, "exit": 3, "holding": 0, "scale_in": 8},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 5,
            "ofi_qi_summary": {
                "scale_in_micro_state_counts": {"bullish": 5},
                "scale_in_micro_advice_counts": {"SUPPORT_ENTRY": 5},
            },
            "scale_in_observation": {
                "action_groups": {"PYRAMID": 5, "AVG_DOWN": 8},
                "post_add_outcomes": {"closed_win": 8},
                "arm_outcomes": {
                    "PYRAMID": {
                        "sample_count": 5,
                        "final_exit_return_summary": {"count": 5, "avg": 1.2},
                        "post_add_delta_vs_exit_only_summary": {"count": 5, "avg": 0.3},
                        "post_add_mae_summary": {"count": 5, "p50": -1.0},
                        "post_add_mae_p90": -1.5,
                        "loser_extension_rate": 0.1,
                    },
                    "AVG_DOWN": {
                        "sample_count": 8,
                        "final_exit_return_summary": {"count": 8, "avg": 0.8},
                        "post_add_delta_vs_exit_only_summary": {"count": 8, "avg": 0.2},
                        "post_add_mae_summary": {"count": 8, "p50": -1.2},
                        "post_add_mae_p90": -2.5,
                        "loser_extension_rate": 0.2,
                    },
                },
            },
            "record_timeline_sample": [],
        },
    )

    report = build_swing_runtime_approval_report(audit, {"ai_status": "parsed"})
    assert not [
        item
        for item in report["approval_requests"]
        if item.get("policy_id") == "swing_scale_in_real_canary_phase0"
    ]
    assert "scale_in_real_canary_policy" not in report


def test_swing_runtime_approval_blocks_scale_in_real_canary_on_invalid_ofi_qi_source_quality():
    audit = _approval_ready_audit(
        lifecycle_events={
            "raw_counts": {},
            "unique_record_counts": {},
            "group_unique_counts": {"entry": 5, "exit": 3, "holding": 0, "scale_in": 8},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 5,
            "ofi_qi_summary": {
                "scale_in_micro_state_counts": {"bullish": 5, "not_ready": 3},
                "scale_in_micro_advice_counts": {"SUPPORT_ENTRY": 5},
                "stale_missing_group_counts": {"scale_in": 3},
                "stale_missing_group_unique_record_counts": {"scale_in": 1},
                "stale_missing_reason_combination_unique_record_counts": {
                    "micro_missing+micro_not_ready+state_insufficient": 1
                },
            },
            "scale_in_observation": {
                "action_groups": {"PYRAMID": 5, "AVG_DOWN": 8},
                "post_add_outcomes": {"closed_win": 8},
                "arm_outcomes": {
                    "PYRAMID": {
                        "sample_count": 5,
                        "final_exit_return_summary": {"count": 5, "avg": 1.2},
                        "post_add_delta_vs_exit_only_summary": {"count": 5, "avg": 0.3},
                        "post_add_mae_summary": {"count": 5, "p50": -1.0},
                        "post_add_mae_p90": -1.5,
                        "loser_extension_rate": 0.1,
                    },
                    "AVG_DOWN": {
                        "sample_count": 8,
                        "final_exit_return_summary": {"count": 8, "avg": 0.8},
                        "post_add_delta_vs_exit_only_summary": {"count": 8, "avg": 0.2},
                        "post_add_mae_summary": {"count": 8, "p50": -1.2},
                        "post_add_mae_p90": -2.5,
                        "loser_extension_rate": 0.2,
                    },
                },
            },
            "record_timeline_sample": [],
        },
    )

    report = build_swing_runtime_approval_report(audit)
    scale_in_requests = [
        item for item in report["approval_requests"] if item.get("policy_id") == "swing_scale_in_real_canary_phase0"
    ]
    blocked_families = {item["family"]: item for item in report["source_quality_blocked_families"]}

    assert scale_in_requests == []
    assert "swing_scale_in_ofi_qi_confirmation" in blocked_families
    assert "scale_in_ofi_qi_invalid_micro_context" in blocked_families["swing_scale_in_ofi_qi_confirmation"][
        "block_reasons"
    ]
    assert "scale_in_real_canary_policy" not in report


def test_swing_improvement_automation_emits_workorder_ready_orders():
    audit = build_swing_lifecycle_audit_report(
        "2026-05-08",
        recommendation_rows=[{"selection_mode": "SELECTED", "position_tag": "META_V2"}],
        diagnostic_summary={"selected_count": 1},
        db_rows=[],
        event_rows=[
            {
                "stage": "blocked_gatekeeper_reject",
                "stock_code": "000002",
                "stock_name": "B",
                "record_id": 2,
                "fields": {"strategy": "KOSPI_ML", "action": "전량 회피"},
            },
            {
                "stage": "swing_scale_in_micro_context_observed",
                "stock_code": "000003",
                "stock_name": "C",
                "record_id": 3,
                "fields": {
                    "strategy": "KOSPI_ML",
                    "orderbook_micro_ready": True,
                    "orderbook_micro_state": "bearish",
                    "orderbook_micro_observer_healthy": True,
                    "swing_micro_advice": "RISK_BEARISH",
                    "swing_micro_runtime_effect": False,
                },
            }
        ],
    )
    automation = build_swing_improvement_automation_report(audit)
    orders = {order["order_id"]: order for order in automation["code_improvement_orders"]}

    assert automation["report_type"] == "swing_improvement_automation"
    assert orders["order_swing_gatekeeper_reject_threshold_review"]["lifecycle_stage"] == "entry"
    assert orders["order_swing_scale_in_ofi_qi_bearish_risk_review"]["threshold_family"] == "swing_scale_in_ofi_qi_confirmation"
    assert orders["order_swing_ai_contract_structured_output_eval"]["runtime_effect"] is False
    assert automation["auto_family_candidates"]
    assert "approval_requests" in automation


def test_write_swing_lifecycle_outputs_creates_all_artifacts(tmp_path):
    outputs = write_swing_lifecycle_outputs(
        "2026-05-08",
        output_root=tmp_path,
        ai_review_provider="none",
        recommendation_rows=[],
        diagnostic_summary={"selected_count": 0},
        db_rows=[],
        event_rows=[],
    )

    for path in outputs["paths"].values():
        assert tmp_path in Path(path).parents
        assert Path(path).exists()
    assert "runtime_approval" in outputs
