"""Adversarial closure of the Daily threshold final-review findings."""

import copy
import json

import pytest

from src.engine import daily_threshold_cycle_report as daily
from src.engine import threshold_cycle_preopen_apply as preopen
from src.engine import wait6579_ev_cohort_report as wait
from src.engine.scalping import score_recovery_observation as observation


def observation_row():
    fields = observation.observation_fields(
        action="WAIT",
        score=70,
        decision={"ai_parse_ok": True},
        probe={
            "buy_pressure": 75,
            "tick_accel": 1.4,
            "micro_vwap_bp": 20,
            "minute_candle_window_fresh": True,
            "micro_vwap_available": True,
        },
        latency_state="SAFE",
        source_blocked=False,
        scope={"effective_venue": "KRX", "market_session_bucket": "krx_regular"},
        reference_price=10000,
        policy={
            "min_score": 60,
            "max_score": 74,
            "min_buy_pressure": 65,
            "min_tick_accel": 1.2,
            "min_micro_vwap_bp": 0,
        },
    )
    return {
        **fields,
        "candidate_id": "005930:record-1:090001",
        "record_id": "record-1",
        "ai_score": 70,
        "has_score65_74_probe": False,
        "minute_candle_source_quality_gate": "pass",
        "cost_adjusted_expected_ev_pct": 3.0,
        "close_10m_pct": 3.8,
        "mfe_10m_pct": 4.0,
    }


def gate_report():
    return {
        "date": "2026-09-07",
        "calibration_candidates": [
            {
                "family": "entry_split_order_plan",
                "stage": "entry",
                "calibration_state": "adjust_up",
                "allowed_runtime_apply": True,
                "runtime_apply_eligible_now": True,
                "window_policy_resolution": {"primary": "rolling_10d"},
            }
        ],
    }


def failure(date, family):
    return {
        "meta": {
            "pipeline_load": {
                date: {
                    "projection_read_complete": False,
                    "projection_read_failures": [
                        {
                            "path": f"date={date}/family={family}/part-000001.jsonl",
                            "error": "read failed",
                        }
                    ],
                }
            }
        }
    }


def test_unrelated_partition_failure_preserves_independent_candidate():
    report = gate_report()
    daily._enforce_pipeline_projection_source_gate(
        report, failure("2026-06-05", "holding_flow_ofi_smoothing")
    )
    assert report["calibration_candidates"][0]["runtime_apply_eligible_now"] is True
    assert len(report["apply_candidate_list"]) == 1
    assert report["source_flags"]["pipeline_projection_read_complete"] is False


@pytest.mark.parametrize("date,blocked", [("2026-06-05", False), ("2026-09-04", True)])
def test_related_partition_failure_uses_consumed_window(date, blocked):
    report = gate_report()
    cumulative = failure(date, "dynamic_entry_price_resolver")
    cumulative["windows"] = {"rolling_10d": ["2026-09-04", "2026-09-07"]}
    daily._enforce_pipeline_projection_source_gate(report, cumulative)
    assert (
        report["calibration_candidates"][0]["runtime_apply_eligible_now"] is not blocked
    )


def test_unidentified_loss_still_blocks_every_candidate():
    report = gate_report()
    cumulative = failure("2026-09-07", "unknown")
    daily._enforce_pipeline_projection_source_gate(report, cumulative)
    assert not report["calibration_candidates"][0]["runtime_apply_eligible_now"]


def test_malformed_failure_detail_is_not_mistaken_for_complete_read():
    report = gate_report()
    report["meta"] = {
        "pipeline_load": {
            "2026-09-07": {
                "projection_read_complete": False,
                "projection_read_failures": [None],
            }
        }
    }
    daily._enforce_pipeline_projection_source_gate(report)
    assert not report["calibration_candidates"][0]["runtime_apply_eligible_now"]


@pytest.mark.parametrize(
    "family",
    [
        "dynamic_entry_price_resolver",
        "scalping_pyramid_quality_gate",
        "entry_price_execution_quality",
    ],
)
def test_other_active_owners_are_not_blocked_by_holding_partition(family):
    report = gate_report()
    report["calibration_candidates"][0]["family"] = family
    daily._enforce_pipeline_projection_source_gate(
        report, failure("2026-09-07", "holding_flow_ofi_smoothing")
    )
    assert report["calibration_candidates"][0]["runtime_apply_eligible_now"] is True


def test_rolling_window_counts_sessions_not_weekends():
    assert daily._trading_date_range("2026-09-07", 5) == [
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
        "2026-09-04",
        "2026-09-07",
    ]
    assert "2026-05-01" not in daily._trading_date_range("2026-05-04", 2)


def test_unapplied_observation_is_economic_source_without_buy_authority():
    row = observation_row()
    summary = wait._counterfactual_summary([row])
    assert summary["score60_74_cost_adjusted_sample_count"] == 1
    assert summary["score60_74_applied_probe_candidates"] == 0
    assert summary["score60_74_unapplied_observation_candidates"] == 1
    assert row["score_recovery_observation_runtime_effect"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("score_recovery_observation_schema", None),
        ("score_recovery_observation_policy_hash", "f" * 64),
        ("score_recovery_observation_runtime_effect", True),
        ("minute_candle_source_quality_gate", "blocked"),
        ("cost_adjusted_expected_ev_pct", float("nan")),
    ],
)
def test_invalid_observation_does_not_enter_economic_floor(key, value):
    row = {**observation_row(), key: value}
    assert (
        wait._counterfactual_summary([row])["score60_74_cost_adjusted_sample_count"]
        == 0
    )
    row["has_score65_74_probe"] = True
    assert (
        wait._counterfactual_summary([row])["score60_74_cost_adjusted_sample_count"]
        == 0
    )


def test_zero_candidate_day_does_not_poison_valid_cost_window():
    metrics = daily._aggregate_metric_dicts(
        [
            {"score60_74_candidates": 0, "score60_74_cost_contract_complete": False},
            {"score60_74_candidates": 20, "score60_74_cost_contract_complete": True},
        ]
    )
    assert metrics["score60_74_cost_contract_complete"] is True
    assert (
        daily._aggregate_metric_dicts(
            [{"score60_74_candidates": 20, "score60_74_cost_contract_complete": False}]
        )["score60_74_cost_contract_complete"]
        is False
    )


def test_positive_subfloor_ev_is_review_not_no_edge_or_automatic_apply():
    result = observation.condition_feasibility(
        {
            "score60_74_cost_adjusted_sample_count": 30,
            "score60_74_avg_cost_adjusted_expected_ev_pct": 0.5,
            "score60_74_cost_contract_complete": True,
        },
        20,
    )
    assert result["state"] == "positive_edge_below_absolute_floor"
    assert not result["allowed_runtime_apply"]
    assert not result["indefinite_wait_appropriate"]


def test_cost_only_sample_parent_cannot_be_hidden_by_other_candidate_counts():
    metrics = daily._aggregate_metric_dicts(
        [
            None,
            {"score60_74_candidates": 20, "score60_74_cost_contract_complete": True},
            {"score60_74_cost_adjusted_sample_count": 1},
        ]
    )
    assert metrics["score60_74_cost_contract_complete"] is False


def test_observation_survives_event_stringification_without_later_price(monkeypatch):
    fields = observation_row()
    fields.update(action="WAIT", target_buy_price=9900)
    # The real JSONL reader stringifies every field before reconstruction.
    fields = {key: str(value) for key, value in fields.items()}
    events = [
        wait.EntryEvent(
            emitted_at="2026-09-07T09:00:01",
            signal_date="2026-09-07",
            name="Samsung",
            code="005930",
            stage="wait65_79_ev_candidate",
            record_id="record-1",
            fields=fields,
        ),
        wait.EntryEvent(
            emitted_at="2026-09-07T09:00:05",
            signal_date="2026-09-07",
            name="Samsung",
            code="005930",
            stage="entry_armed",
            record_id="record-1",
            fields={"target_buy_price": "12000"},
        ),
    ]
    monkeypatch.setattr(wait, "_load_entry_events", lambda date: events)
    candidates = wait._build_wait6579_candidates("2026-09-07")
    assert len(candidates) == 1
    assert candidates[0]["signal_price"] == 10000
    assert observation.eligible_observation(candidates[0])


def test_unicode_candidate_inventory_is_bounded_without_dropping_families():
    report = {
        "date": "2026-09-07",
        "calibration_candidates": [
            {
                "family": f"family_{i}",
                "stage": "entry",
                "allowed_runtime_apply": True,
                "runtime_apply_eligible_now": True,
                "calibration_state": "adjust_up",
                "calibration_reason": "한" * 600,
                "current_value": 0,
                "recommended_value": 1,
            }
            for i in range(30)
        ],
    }
    context = daily._build_ai_correction_input_context(report)
    assert len(context["required_family_manifest"]) == 30
    assert len(context["calibration_candidates"]) == 30
    assert daily._json_chars(context) <= daily.AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT


@pytest.mark.parametrize("provider", ["openai", "gemini"])
def test_oversized_payload_never_loads_keys_or_calls_provider(monkeypatch, provider):
    def forbidden():
        raise AssertionError("provider access is forbidden")

    monkeypatch.setattr(daily, f"_load_threshold_ai_{provider}_keys", forbidden)
    fn = getattr(daily, f"_call_{provider}_threshold_ai_correction")
    kwargs = {"run_phase": "postclose"} if provider == "openai" else {}
    raw, status = fn({"unbounded": "x" * 120_001}, **kwargs)
    assert raw is None
    assert status["status"] == "blocked_context_budget"
    assert status["new_provider_call"] is False
    assert daily._repair_ai_correction_family_coverage(
        {"required_family_manifest": ["family"]},
        raw,
        status,
        provider=provider,
        run_phase="postclose",
    ) == (raw, status)


def test_observation_policy_cohorts_are_not_pooled_for_preopen():
    metrics = {"score60_74_observation_policy_hashes": ["a" * 64, "b" * 64]}
    assert not observation.observation_cohort_valid(metrics)
    assert not preopen._score65_74_entry_unlock_candidate(
        {
            "family": "score65_74_recovery_probe",
            "source_metrics": metrics,
        }
    )


def test_live_collector_observation_does_not_change_action_or_runtime(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    emitted = []
    monkeypatch.setattr(
        handlers, "_log_entry_pipeline", lambda *a, **kw: emitted.append(kw)
    )
    monkeypatch.setattr(
        handlers, "_buy_recovery_probe_source_quality_hard_block", lambda probe: False
    )
    monkeypatch.setattr(
        handlers, "_ensure_ai_source_quality_fields", lambda *a, **kw: {}
    )
    monkeypatch.setattr(
        handlers, "_build_tick_source_quality_log_fields", lambda probe: {}
    )
    decision = {"ai_parse_ok": True, "action": "WAIT"}
    before = copy.deepcopy(decision)
    handlers._log_wait65_79_ev_candidate(
        stock={"effective_venue": "KRX", "market_session_bucket": "krx_regular"},
        code="005930",
        action="WAIT",
        ai_score=70,
        ai_decision=decision,
        ws_data={"latency_state": "SAFE", "curr": 10000},
        feature_probe={
            "buy_pressure": 95,
            "tick_accel": 3.0,
            "micro_vwap_bp": 40,
            "minute_candle_window_fresh": True,
            "micro_vwap_available": True,
        },
    )
    assert decision == before
    assert emitted[0]["score_recovery_observation_eligible"] is True
    assert handlers._is_wait65_79_candidate("WAIT", 60)
    assert not handlers._is_wait65_79_candidate("BUY", 70)


def test_benchmark_uses_regular_source_loader_without_saves_or_provider(
    monkeypatch, capsys
):
    def forbidden(*args, **kwargs):
        raise AssertionError("benchmark must not publish or call providers")

    calls = []

    def cumulative(*args, **kwargs):
        calls.append(kwargs)
        return {
            "date": "2026-09-07",
            "calibration_source_bundle_by_window": {"rolling_5d": {}},
        }

    monkeypatch.setattr(
        daily,
        "build_daily_threshold_cycle_report",
        lambda *a, **k: {"date": "2026-09-07", "calibration_candidates": []},
    )
    monkeypatch.setattr(daily, "build_cumulative_threshold_cycle_report", cumulative)
    for name in [
        "save_threshold_calibration_report",
        "save_threshold_cycle_report",
        "save_cumulative_threshold_cycle_report",
        "_call_openai_threshold_ai_correction",
    ]:
        monkeypatch.setattr(daily, name, forbidden)
    for name in [
        "merge_scalping_avg_down_recovery_calibration_candidate",
        "merge_scalping_pyramid_quality_calibration_candidate",
    ]:
        monkeypatch.setattr(daily, name, lambda *a, **k: None)
    assert (
        daily.main(
            [
                "--date",
                "2026-09-07",
                "--benchmark-inputs-only",
                "--ai-correction-provider",
                "openai",
            ]
        )
        == 0
    )
    assert (
        calls[0]["report_source_loader"] is daily._summarize_holding_exit_report_sources
    )
    assert calls[0]["skip_completed_rows"] is False
    result = json.loads(capsys.readouterr().out)
    assert result["source_windows"] == ["rolling_5d"]
    assert result["provider_call_count"] == result["report_write_count"] == 0
