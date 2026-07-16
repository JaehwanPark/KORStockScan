import gzip
import json

import pytest

from src.engine.scalping import entry_hurdle_backtest as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "blocked_reason": None,
            "hard_blocking_contract_gap_count": 0,
            "clean_baseline_enforced": True,
        },
    )


def test_entry_hurdle_micro_context_rejects_not_evaluated_quality():
    assert not mod._event_micro_context_usable(
        {
            "tick_context_quality": "not_evaluated",
            "tick_accel_source": "not_evaluated",
            "quote_age_source": "not_evaluated",
        }
    )
    assert not mod._event_micro_context_usable(
        {
            "tick_context_quality": "not_evaluated_pre_contract",
            "tick_accel_source": "not_evaluated",
            "quote_age_source": "not_evaluated_pre_contract",
        }
    )


def test_entry_hurdle_backtest_classifies_overblocking_from_existing_artifacts(
    tmp_path, monkeypatch
):
    buy_dir = tmp_path / "buy_funnel_sentinel"
    missed_dir = tmp_path / "monitor_snapshots"
    pipeline_dir = tmp_path / "pipeline_events"
    buy_dir.mkdir(parents=True)
    missed_dir.mkdir(parents=True)
    pipeline_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "BUY_FUNNEL_DIR", buy_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)

    (buy_dir / "buy_funnel_sentinel_2026-06-05.json").write_text(
        json.dumps(
            {
                "current": {
                    "session": {
                        "stage_unique": {
                            "ai_confirmed": 10,
                            "budget_pass": 5,
                            "latency_pass": 3,
                            "blocked_ai_score": 2,
                            "order_bundle_submitted": 1,
                            "pre_submit_late_entry_price_drift_guard_block": 1,
                            "pre_submit_overbought_pullback_guard_block": 3,
                        },
                        "ratios": {
                            "submitted_to_ai_unique_pct": 10.0,
                            "submitted_to_budget_unique_pct": 20.0,
                        },
                    },
                },
                "classification": {
                    "primary": "SUBMIT_DROUGHT_CRITICAL",
                    "submit_drought_handoff_state": "handoff_required",
                    "submit_drought_root_cause": {
                        "quote_freshness_attribution": {
                            "runtime_effect": False,
                            "decision_authority": "submit_drought_quote_freshness_attribution_only",
                            "refresh_subreason_counts": {"latest_ws_snapshot_fresh": 2},
                            "refresh_attempted_count": 2,
                            "refresh_applied_count": 2,
                            "still_latency_blocked_after_refresh_count": 0,
                            "latency_pass_recovered_count": 2,
                            "order_bundle_submitted_after_refresh_count": 1,
                            "latency_pass_recovered_downstream_stage_counts": {
                                "pre_submit_liquidity_guard_block": 1,
                                "order_bundle_submitted": 1,
                            },
                        }
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    with gzip.open(
        missed_dir / "missed_entry_counterfactual_2026-06-05.json.gz",
        "wt",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                {
                    "metrics": {
                        "blocker_outcome_metrics": {
                            "pre_submit_liquidity_guard_block": {
                                "evaluated_candidates": 5,
                                "missed_winner_count": 4,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            },
                            "blocked_ai_score": {
                                "evaluated_candidates": 4,
                                "missed_winner_count": 3,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            },
                            "pre_submit_late_entry_price_drift_guard_block": {
                                "evaluated_candidates": 4,
                                "missed_winner_count": 3,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            },
                            "pre_submit_overbought_pullback_guard_block": {
                                "evaluated_candidates": 6,
                                "missed_winner_count": 5,
                                "avoided_loser_count": 0,
                                "neutral_count": 1,
                            },
                        },
                        "cohort_outcome_metrics": {
                            "entry_armed_latency_or_safety_block": {
                                "evaluated_candidates": 5,
                                "missed_winner_rate": 80.0,
                                "avoided_loser_rate": 0.0,
                            }
                        },
                    }
                }
            )
        )
    (pipeline_dir / "pipeline_events_2026-06-05.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "pre_submit_liquidity_guard_block",
                        "stock_code": "123456",
                        "record_id": "1",
                        "emitted_at": "2026-06-05T10:00:00+09:00",
                        "fields": {
                            "ai_score": "82.0",
                            "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                            "curr_vs_micro_vwap_bp": "43.69",
                            "micro_vwap_available": "True",
                            "minute_candle_context_quality": "fresh_bar_window",
                            "minute_candle_window_fresh": "True",
                            "buy_pressure_10t": "93.69",
                            "tick_aggressor_trusted_count": "3",
                            "tick_aggressor_pressure_usable": "True",
                            "quote_stale_at_submit": "False",
                            "price_context_stale_at_submit": "False",
                            "tick_context_quality": "fresh_computed",
                            "tick_accel_source": "computed_10ticks",
                            "quote_age_ms": "120",
                            "quote_age_source": "last_ws_update_ts",
                            "pre_submit_overbought_guard_action": "PASS",
                            "entry_submit_revalidation_warning": "",
                            "liquidity_relief_skip_reason": "tick_accel_below_min",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "blocked_ai_score",
                        "stock_code": "234567",
                        "record_id": "2",
                        "emitted_at": "2026-06-05T10:01:00+09:00",
                        "fields": {
                            "ai_score": "72.0",
                            "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                            "curr_vs_micro_vwap_bp": "7.5",
                            "micro_vwap_available": "True",
                            "minute_candle_context_quality": "fresh_bar_window",
                            "minute_candle_window_fresh": "True",
                            "quote_stale": "False",
                            "tick_context_stale": "False",
                            "tick_context_quality": "fresh_computed",
                            "tick_accel_source": "computed_10ticks",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "first_ai_wait",
                        "stock_code": "456789",
                        "record_id": "4",
                        "emitted_date": "2026-06-05",
                        "emitted_at": "2026-06-05T10:03:00+09:00",
                        "fields": {
                            "ai_score": "62.0",
                            "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP,VOLUME_SURGE_POSITIVE",
                            "curr_vs_micro_vwap_bp": "1.2",
                            "micro_vwap_available": "True",
                            "minute_candle_context_quality": "fresh_bar_window",
                            "minute_candle_window_fresh": "True",
                            "quote_stale": "False",
                            "tick_context_stale": "False",
                            "quote_age_ms": "80",
                            "quote_age_source": "last_ws_update_ts",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "blocked_ai_score",
                        "stock_code": "345678",
                        "record_id": "3",
                        "emitted_at": "2026-06-05T10:02:00+09:00",
                        "fields": {
                            "ai_score": "72.0",
                            "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                            "curr_vs_micro_vwap_bp": "7.5",
                            "micro_vwap_available": "True",
                            "minute_candle_context_quality": "fresh_bar_window",
                            "minute_candle_window_fresh": "True",
                            "quote_stale": "True",
                            "tick_context_stale": "False",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-06-05", start_date="2026-06-05", end_date="2026-06-07"
    )

    assert report["runtime_effect"] is False
    assert report["source_dates"] == ["2026-06-05"]
    assert report["summary"]["submitted_to_ai_unique_pct"] == 10.0
    blocker = report["summary"]["blocker_tradeoff"]["pre_submit_liquidity_guard_block"]
    assert blocker["missed_winner_rate"] == 80.0
    assert blocker["hurdle_decision"] == "overblocking_candidate"
    diagnostics = report["summary"]["next_action_diagnostics"]
    assert diagnostics["metric_role"] == "next_action_diagnostic"
    assert diagnostics["window_policy"] == "2026-06-05_to_2026-06-07"
    assert (
        diagnostics["primary_decision_metric"]
        == "missed_winner_vs_avoided_loser_tradeoff"
    )
    assert diagnostics["runtime_effect"] is False
    assert diagnostics["actual_order_submitted_provenance_preserved"] is True
    assert "entry price reprice" in diagnostics["forbidden_uses"]
    assert "risk expansion" in diagnostics["forbidden_uses"]
    assert "broker guard bypass" in diagnostics["forbidden_uses"]
    assert "stale quote guard bypass" in diagnostics["forbidden_uses"]
    assert diagnostics["quote_freshness_totals"]["latency_pass_recovered_count"] == 2
    assert (
        diagnostics["quote_freshness_totals"][
            "order_bundle_submitted_after_refresh_count"
        ]
        == 1
    )
    action_ids = [item["action_id"] for item in diagnostics["recommended_next_actions"]]
    assert action_ids == [
        "trace_latency_refresh_recovered_downstream_blocker",
        "review_pre_submit_liquidity_relief_scope",
        "review_overbought_gate_miss_ev_recovery_scope",
        "review_ai_wait_score_recheck_scope",
        "audit_late_entry_price_drift_guard_context",
    ]
    assert all(
        item["runtime_effect"] is False
        for item in diagnostics["recommended_next_actions"]
    )
    policy_backtest = report["summary"]["implemented_policy_backtest"]
    assert policy_backtest["runtime_effect"] is False
    assert "entry price reprice" in policy_backtest["forbidden_uses"]
    assert (
        policy_backtest["liquidity_signature_micro_pressure_relief"][
            "eligible_attempts"
        ]
        == 1
    )
    assert (
        policy_backtest["ai_score_60_74_strong_bundle_recheck"][
            "eligible_recheck_attempts"
        ]
        == 2
    )
    assert policy_backtest["ai_score_60_74_strong_bundle_recheck"][
        "excluded_reasons"
    ] == {"stale_quote_or_tick_context": 1}
    assert policy_backtest["total"]["eligible_attempts"] == 3
    assert policy_backtest["total"]["conservative_estimated_order_submit_success"] == 0
    overbought = report["summary"]["overbought_gate_counterfactual"]
    assert overbought["decision"] == "source_only_recovery_design_candidate"
    assert overbought["evaluated_candidates"] == 6
    assert overbought["missed_winner_count"] == 5
    assert overbought["avoided_loser_count"] == 0
    assert overbought["runtime_effect"] is False
    assert overbought["broker_order_forbidden"] is True
    assert report["summary"]["code_improvement_order_count"] == 1
    assert (
        report["code_improvement_orders"][0]["order_id"]
        == "order_overbought_gate_miss_ev_recovery"
    )
    assert report["code_improvement_orders"][0]["implementation_status"] == (
        "implemented_source_quality_contract_available"
    )
    assert report["code_improvement_orders"][0]["runtime_effect"] is False
    assert report["code_improvement_orders"][0]["broker_order_forbidden"] is True
    assert not report["missing_artifacts"]


def test_entry_hurdle_micro_pressure_relief_requires_trusted_tick_pressure():
    base = {
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "curr_vs_micro_vwap_bp": "43.69",
        "buy_pressure_10t": "93.69",
    }
    fresh = {
        **base,
        "tick_context_quality": "fresh_computed",
        "tick_accel_source": "computed_10ticks",
    }
    fresh_micro_vwap = {
        **fresh,
        "micro_vwap_available": "True",
        "minute_candle_context_quality": "fresh_bar_window",
        "minute_candle_window_fresh": "True",
    }
    missing_quality_micro_vwap = {
        **fresh,
        "micro_vwap_available": "True",
        "minute_candle_window_fresh": "True",
    }
    stale_micro_vwap = {
        **fresh_micro_vwap,
        "minute_candle_window_fresh": "False",
    }

    assert mod._signature_micro_pressure_path(base) is False
    assert (
        mod._signature_micro_pressure_path(
            {**base, "tick_aggressor_pressure_usable": "True"}
        )
        is False
    )
    assert (
        mod._signature_micro_pressure_path(
            {**fresh, "tick_aggressor_pressure_usable": "True"}
        )
        is False
    )
    assert (
        mod._signature_micro_pressure_path(
            {**missing_quality_micro_vwap, "tick_aggressor_pressure_usable": "True"}
        )
        is False
    )
    assert (
        mod._signature_micro_pressure_path(
            {**fresh_micro_vwap, "tick_aggressor_pressure_usable": "True"}
        )
        is True
    )
    assert (
        mod._signature_micro_pressure_path(
            {**fresh_micro_vwap, "tick_aggressor_trusted_count": "2"}
        )
        is True
    )
    assert (
        mod._signature_micro_pressure_path(
            {**stale_micro_vwap, "tick_aggressor_trusted_count": "2"}
        )
        is False
    )
    assert (
        mod._signature_micro_pressure_path(
            {
                **fresh_micro_vwap,
                "tick_aggressor_trusted_count": "2",
                "quote_stale": "stale",
            }
        )
        is False
    )


def test_entry_hurdle_backtest_source_quality_preflight_blocks_strategy_workorders(
    tmp_path, monkeypatch
):
    buy_dir = tmp_path / "buy_funnel_sentinel"
    missed_dir = tmp_path / "monitor_snapshots"
    pipeline_dir = tmp_path / "pipeline_events"
    buy_dir.mkdir(parents=True)
    missed_dir.mkdir(parents=True)
    pipeline_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "BUY_FUNNEL_DIR", buy_dir)
    monkeypatch.setattr(mod, "MISSED_ENTRY_DIRS", [missed_dir])
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "required_field_missing",
            "hard_blocking_contract_gap_count": 1,
            "clean_baseline_enforced": True,
        },
    )
    (buy_dir / "buy_funnel_sentinel_2026-06-05.json").write_text(
        json.dumps(
            {
                "current": {
                    "session": {"stage_unique": {"ai_confirmed": 10, "budget_pass": 5}}
                }
            }
        ),
        encoding="utf-8",
    )
    (missed_dir / "missed_entry_counterfactual_2026-06-05.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "blocker_outcome_metrics": {
                        "pre_submit_overbought_pullback_guard_block": {
                            "evaluated_candidates": 6,
                            "missed_winner_count": 5,
                            "avoided_loser_count": 0,
                            "neutral_count": 1,
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-06-05", start_date="2026-06-05", end_date="2026-06-05"
    )

    assert report["status"] == "source_quality_blocked"
    assert report["allowed_runtime_apply"] is False
    assert report["source_quality_gate"] == "blocked_contract_gap"
    assert report["code_improvement_orders"] == []
    assert report["summary"]["code_improvement_order_count"] == 0
    assert report["summary"]["calibration_state"] == "source_quality_blocked"
