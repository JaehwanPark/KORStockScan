"""Contract regressions for #89; fixtures are not trading/economic acceptance."""

import json
import gzip

import pytest

from src.engine.monitoring import ws_freshness_acceptance as mod
from src.engine.monitoring import intraday_ws_freshness_monitor as monitor
from src.engine import build_code_improvement_workorder as consumer


def _group(
    resolved=10, *, cohort="general_slot_limit", venue="KRX", session="KRX_REGULAR"
):
    return {
        "cohort": cohort,
        "venue": venue,
        "market_session_bucket": session,
        "eligible_verified_common_stock_candidate_count": resolved,
        "exact_bbo_joined_count": resolved,
        "resolved_outcome_count": resolved,
        "right_censored_count": 0,
        "resolved_return_sum_pct": resolved * 0.02,
    }


def _receipt(target="2026-09-08", groups=None):
    return mod.economic_receipt(
        {
            "target_date": target,
            "evaluation_phase": "postclose_final",
            "diagnostic_acceptance": {"status": "diagnostic_generated"},
            "scanner_unique_funnel": {
                "economic_cohorts": {
                    "executable_bbo_attribution": {
                        "comparison_cost_contract_status": "verified",
                        "comparison_cost_contract": {
                            "contract_sha256": "a" * 64,
                            "policy_id": "cost_v1",
                            "round_trip_cost_pct": 0.23,
                        },
                        "official_symbol_master_binding": {
                            "status": "verified",
                            "artifact_sha256": "b" * 64,
                        },
                        "gross_target_pct": 1.3,
                        "adverse_stop_pct": -0.7,
                        "horizon_sec": 1200,
                        "timeout_max_lag_sec": 5.0,
                        "prune_observer_acceptance": {
                            "groups": [_group()] if groups is None else groups
                        },
                    }
                }
            },
        }
    )


def _write_receipt(path, receipt):
    report = {"daily_prune_economic_receipt": receipt}
    (path / f"intraday_ws_freshness_monitor_{receipt['target_date']}.json").write_text(
        json.dumps(report)
    )


def test_small_positive_rolling_ev_and_independent_sparse_group(tmp_path):
    previous = _receipt("2026-09-07", [_group(), _group(1, venue="NXT", session="NXT")])
    _write_receipt(tmp_path, previous)
    current = _receipt(groups=[_group(), _group(1, venue="NXT", session="NXT")])
    result = mod.rolling_economics(current, tmp_path)
    by_venue = {row["venue"]: row for row in result["groups"]}
    assert by_venue["KRX"]["source_only_comparison_ready"] is True
    assert by_venue["KRX"]["source_quality_adjusted_ev_pct"] == pytest.approx(0.02)
    assert by_venue["NXT"]["source_only_comparison_ready"] is False
    assert by_venue["NXT"]["source_quality_adjusted_ev_pct"] is None
    assert result["all_groups_required"] is False
    assert result["allowed_runtime_apply"] is False


def test_same_date_replacement_future_and_prebaseline_are_not_counted(tmp_path):
    for day in ("2026-06-04", "2026-09-08", "2026-09-09"):
        _write_receipt(tmp_path, _receipt(day, [_group(100)]))
    result = mod.rolling_economics(_receipt(), tmp_path)
    assert result["source_dates"] == ["2026-09-08"]
    assert result["groups"][0]["resolved_outcome_count"] == 10


def test_archived_daily_receipt_is_not_lost_from_rolling_window(tmp_path):
    _write_receipt(tmp_path, _receipt("2026-09-07"))
    path = tmp_path / "intraday_ws_freshness_monitor_2026-09-07.json"
    with gzip.open(str(path) + ".gz", "wb") as handle:
        handle.write(path.read_bytes())
    path.unlink()
    result = mod.rolling_economics(_receipt(), tmp_path)
    assert result["source_dates"] == ["2026-09-07", "2026-09-08"]
    assert result["groups"][0]["resolved_outcome_count"] == 20


def test_prebaseline_current_receipt_is_not_economic_evidence(tmp_path):
    result = mod.rolling_economics(_receipt("2026-06-04"), tmp_path)
    assert result["groups"] == []
    assert result["excluded_sources"][0]["reason"] == "prebaseline_source_forbidden"


@pytest.mark.parametrize("corruption", ["truncated", "invalid_deflate"])
def test_corrupt_archive_excludes_source_without_hiding_current_group(
    tmp_path, corruption
):
    path = tmp_path / "intraday_ws_freshness_monitor_2026-09-07.json.gz"
    encoded = gzip.compress(
        json.dumps({"daily_prune_economic_receipt": _receipt("2026-09-07")}).encode()
    )
    path.write_bytes(
        encoded[:-6]
        if corruption == "truncated"
        else encoded[:10] + b"\xff" + encoded[11:]
    )
    result = mod.rolling_economics(_receipt(), tmp_path)
    assert result["source_dates"] == ["2026-09-08"]
    assert result["window_source_dates"] == ["2026-09-07", "2026-09-08"]
    assert result["groups"][0]["resolved_outcome_count"] == 10
    assert result["excluded_sources"][0]["reason"] == "receipt_missing_or_invalid"


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (
            lambda r: r["groups"][0].update(resolved_outcome_count=90),
            "receipt_hash_invalid",
        ),
        (lambda r: r.update(runtime_effect=True), "authority_invalid"),
        (lambda r: r.update(source_verified=False), "source_quality_blocked"),
        (
            lambda r: r["contract"]["cost"].update(policy_id="different"),
            "different_economic_contract",
        ),
        (
            lambda r: r["groups"][0].update(resolved_return_sum_pct=None),
            "net_outcome_sum_missing",
        ),
    ],
)
def test_rolling_rejects_tampered_or_incompatible_evidence(tmp_path, mutation, reason):
    receipt = _receipt("2026-09-07")
    mutation(receipt)
    if reason != "receipt_hash_invalid":
        receipt["contract_sha256"] = mod._hash(receipt["contract"])
        receipt["sha256"] = mod._hash(
            {k: v for k, v in receipt.items() if k != "sha256"}
        )
    _write_receipt(tmp_path, receipt)
    result = mod.rolling_economics(_receipt(), tmp_path)
    if reason != "net_outcome_sum_missing":
        assert result["source_dates"] == ["2026-09-08"]
    assert result["groups"][0]["resolved_outcome_count"] == 10
    assert any(row["reason"] == reason for row in result["excluded_sources"])


def test_invalid_group_does_not_discard_other_venue(tmp_path):
    invalid = _group(10, venue="NXT", session="NXT")
    invalid["resolved_return_sum_pct"] = None
    _write_receipt(tmp_path, _receipt("2026-09-07", [_group(), invalid]))
    result = mod.rolling_economics(_receipt(), tmp_path)
    assert result["groups"][0]["resolved_outcome_count"] == 20
    assert result["groups"][0]["source_only_comparison_ready"] is True
    assert result["excluded_sources"][0]["scope"] == "group"


def test_empty_finalized_days_expire_old_positive_samples(tmp_path):
    _write_receipt(tmp_path, _receipt("2026-08-27", [_group(30)]))
    for day in (
        "2026-08-28",
        "2026-08-29",
        "2026-08-30",
        "2026-08-31",
        "2026-09-01",
        "2026-09-02",
        "2026-09-03",
        "2026-09-04",
        "2026-09-07",
    ):
        _write_receipt(tmp_path, _receipt(day, []))
    result = mod.rolling_economics(_receipt(groups=[]), tmp_path)
    assert len(result["window_source_dates"]) == 10
    assert "2026-08-27" not in result["source_dates"]
    assert result["groups"] == []


def test_postclose_missing_repair_evidence_reaches_workorder_implementation():
    summary = {
        "evaluation_phase": "postclose_final",
        "pipeline_counts": {"both_ws_stale": 605},
        "snapshot_summary": {},
        "causal_attribution": {
            "both_ws_stale": {"repair_cycle_state_counts": {"not_observed": 589}}
        },
    }
    directives = monitor._build_workorders(summary, target_date="2026-09-08")
    assert directives[0]["decision"] == "implement_now"
    assert directives[0]["gap_reason"] == "repair_receipt_missing"
    orders = consumer._intraday_ws_freshness_followup_orders(
        {"workorder_directives": directives}
    )
    result = consumer._classify_order(
        orders[0],
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert result.decision == "implement_now"
    assert orders[0]["runtime_effect"] is False
    assert orders[0]["allowed_runtime_apply"] is False


def test_normal_safety_attribution_not_automatic_repair_or_buy():
    summary = {
        "evaluation_phase": "postclose_final",
        "pipeline_counts": {"decision_stage_stale_backoff": 2},
        "snapshot_summary": {},
        "causal_attribution": {
            "decision_stage_stale_backoff": {
                "repair_cycle_state_counts": {"ws_reg_reissued_waiting_snapshot": 2}
            }
        },
    }
    order = monitor._build_workorders(summary, target_date="2026-09-08")[0]
    assert order["decision"] == "observe"
    assert order["diagnostic_status"] == "attributed_safety_observation"
    assert order["runtime_effect"] is False


def test_absent_causal_receipt_is_not_attributed_safety():
    summary = {
        "evaluation_phase": "postclose_final",
        "pipeline_counts": {"both_ws_stale": 1},
        "snapshot_summary": {},
    }
    order = monitor._build_workorders(summary, target_date="2026-09-08")[0]
    assert order["decision"] == "implement_now"
    assert order["gap_reason"] == "repair_receipt_missing"


def test_collector_closure_does_not_require_economic_floor():
    summary = {
        "evaluation_phase": "postclose_final",
        "pipeline_counts": {},
        "snapshot_summary": {},
        "scanner_unique_funnel": {
            "economic_cohorts": {"general_slot_limit": 3},
            "prune_observer_summary": {
                "eligible_episode_census_count": 3,
                "scheduled_stable_episode_count": 3,
                "sample_event_count": 3,
                "runtime_configuration_valid_receipt_count": 1,
                "receipt_accounting": {
                    "schema": "ws_prune_receipt_accounting_v1",
                    "episode_count": 3,
                    "unaccounted_episode_count": 0,
                },
                "acceptance": {"acceptance_ready": False},
            },
        },
    }
    order = monitor._build_workorders(summary, target_date="2026-09-08")[0]
    assert order["decision"] == "observe"
    assert order["economic_acceptance"] == "hold_sample"
    assert order["diagnostic_acceptance_requires_economic_floor"] is False


def test_bounded_capacity_rejection_is_not_a_missing_runtime_hook():
    summary = {
        "evaluation_phase": "postclose_final",
        "pipeline_counts": {},
        "snapshot_summary": {},
        "scanner_unique_funnel": {
            "economic_cohorts": {"general_slot_limit": 3},
            "prune_observer_summary": {
                "eligible_episode_census_count": 3,
                "scheduled_stable_episode_count": 0,
                "schedule_status_counts": {"active_episode_capacity_rejected": 3},
                "runtime_configuration_valid_receipt_count": 1,
                "receipt_accounting": {
                    "schema": "ws_prune_receipt_accounting_v1",
                    "episode_count": 3,
                    "unaccounted_episode_count": 0,
                },
            },
        },
    }
    order = monitor._build_workorders(summary, target_date="2026-09-08")[0]
    assert order["decision"] == "observe"
    assert order["diagnostic_status"] == "bounded_collector_admission_observed"


def test_missing_optional_mirror_keeps_incremental_cache_and_appearance_rebuilds(
    tmp_path,
):
    raw, mirror, state = (
        tmp_path / name for name in ("pipeline.jsonl", "mirror.jsonl", "state.json")
    )
    raw.write_text('{"stage":"test","fields":{}}\n')
    kwargs = {
        "pipeline_path": raw,
        "threshold_path": mirror,
        "incremental_state_path": state,
    }
    first = monitor.build_report("2026-09-08", **kwargs)
    second = monitor.build_report("2026-09-08", **kwargs)
    assert first["input_processing"]["incremental_state_persisted"] is True
    assert second["input_processing"]["appended_event_count"] == 0
    assert second["input_processing"]["incremental_state_reason"] == "state_reused"
    mirror.write_text('{"stage":"mirror","fields":{}}\n')
    appeared = monitor.build_report("2026-09-08", **kwargs)
    assert appeared["input_processing"]["mode"] == "full_streaming_rebuild"
    assert appeared["pipeline_event_count"] == 2
    mirror.unlink()
    removed = monitor.build_report("2026-09-08", **kwargs)
    assert removed["pipeline_event_count"] == 1
    assert (
        removed["input_processing"]["incremental_state_reason"]
        == "threshold_events_disappeared"
    )


def test_final_report_exposes_separate_diagnostic_and_rolling_contracts(tmp_path):
    raw = tmp_path / "pipeline.jsonl"
    raw.write_text("")
    report = monitor.build_report(
        "2026-09-08",
        pipeline_path=raw,
        threshold_path=tmp_path / "optional",
        finalize=True,
        history_report_dir=tmp_path,
    )
    assert report["evaluation_phase"] == "postclose_final"
    assert report["diagnostic_acceptance"]["status"] == "diagnostic_generated"
    assert report["rolling_prune_economics"]["allowed_runtime_apply"] is False
    assert report["daily_prune_economic_receipt"]["finalized"] is True
    assert "rolling_prune_economics" in monitor._render_monitor_markdown(report)


@pytest.mark.parametrize(
    "state",
    [
        "not_observed",
        "unknown",
        "repair_required_without_cycle_state",
        "receipt_missing",
    ],
)
def test_missing_cycle_state_never_closes_as_normal_safety(state):
    orders = mod.finalize_followups(
        {
            "evaluation_phase": "postclose_final",
            "causal_attribution": {
                "both_ws_stale": {"repair_cycle_state_counts": {state: 8}}
            },
        },
        [{"order_id": "order_ws_total_stale_escalation", "decision": "defer_evidence"}],
    )
    assert orders[0]["decision"] == "implement_now"


def _finalize_observer(observer):
    return mod.finalize_followups(
        {
            "evaluation_phase": "postclose_final",
            "scanner_unique_funnel": {"prune_observer_summary": observer},
        },
        [
            {
                "order_id": "order_scanner_funnel_executable_bbo_join",
                "decision": "defer_evidence",
            }
        ],
    )[0]


def test_absent_or_partial_observer_receipts_never_close():
    assert _finalize_observer({})["decision"] == "implement_now"
    assert (
        _finalize_observer(
            {
                "runtime_configuration_valid_receipt_count": 1,
                "eligible_episode_census_count": 20,
                "scheduled_stable_episode_count": 20,
                "sample_event_count": 1,
            }
        )["decision"]
        == "implement_now"
    )
    healthy = _finalize_observer(
        {
            "runtime_configuration_valid_receipt_count": 1,
            "eligible_episode_census_count": 0,
            "scheduled_stable_episode_count": 0,
            "receipt_accounting": mod.observer_receipt_accounting([], 10),
        }
    )
    assert healthy["diagnostic_status"] == "healthy_no_natural_sample"


def test_episode_accounting_requires_all_indices_and_valid_terminal():
    complete = {
        "prune_observer_episode_id": "a",
        "prune_observer_schedule_statuses": ["new_episode_scheduled"],
        "prune_observer_receipt_indices": list(range(10)),
        "prune_observer_receipt_terminal_valid": True,
    }
    partial = {
        **complete,
        "prune_observer_episode_id": "b",
        "prune_observer_receipt_indices": [9],
    }
    bounded = {"prune_observer_schedule_statuses": ["active_episode_capacity_rejected"]}
    result = mod.observer_receipt_accounting([complete, partial, bounded, {}], 10)
    assert result["episode_count"] == 4
    assert result["state_counts"] == {
        "scheduled_complete": 1,
        "scheduled_receipt_gap": 1,
        "bounded_not_admitted": 1,
        "admission_receipt_gap": 1,
    }
    assert result["unaccounted_episode_count"] == 2
    assert result["gap_examples"][0]["missing_sample_indices"] == list(range(9))


@pytest.mark.parametrize(
    "age_ms,state,stale_count", [(1000, "fresh", 0), (31000, "stale", 1)]
)
def test_snapshot_age_future_and_historical_scope(
    tmp_path, monkeypatch, age_ms, state, stale_count
):
    from datetime import datetime

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "generated_at": "2026-09-08T09:00:00+09:00",
                "stocks": {
                    "005930": {
                        "last_realtime_type_ages_ms": {"0B": age_ms, "0D": age_ms}
                    }
                },
            }
        )
    )
    monkeypatch.setattr(monitor, "DEFAULT_DASHBOARD_SNAPSHOT_PATH", snapshot)
    for explicit in (None, snapshot):
        _, payload, provenance = monitor._resolve_snapshot(
            explicit,
            target_date="2026-09-08",
            as_of=datetime.fromisoformat("2026-09-08T12:00:00+09:00"),
        )
        assert not payload
        assert provenance["selection_reason"] == "snapshot_stale"
        _, payload, provenance = monitor._resolve_snapshot(
            explicit,
            target_date="2026-09-08",
            as_of=datetime.fromisoformat("2026-09-08T08:59:00+09:00"),
        )
        assert not payload
        assert provenance["selection_reason"] == "snapshot_future_dated"
    raw = tmp_path / "raw.jsonl"
    raw.write_text("")
    report = monitor.build_report(
        "2026-09-08",
        pipeline_path=raw,
        threshold_path=tmp_path / "missing",
        generated_at="2026-09-08T21:00:00+09:00",
        finalize=True,
        history_report_dir=tmp_path,
    )
    assert report["snapshot_summary"]["freshness_state_counts"] == {
        f"{state}_at_snapshot": 1
    }
    assert (
        report["subscription_snapshot_provenance"]["current_freshness_usable"] is False
    )
    assert report["snapshot_summary"]["repair_recommended_count"] == 0
    assert report["snapshot_summary"]["observed_stale_like_count"] == stale_count
    assert report["snapshot_summary"]["current_freshness_usable"] is False


def test_snapshot_elapsed_time_is_added_to_tick_age():
    rows = monitor._snapshot_rows(
        {
            "stocks": {
                "005930": {"last_realtime_type_ages_ms": {"0B": 2000, "0D": 2000}}
            }
        },
        stale_ms=30000,
        elapsed_ms=29000,
    )
    assert rows[0]["freshness_state"] == "stale"
    assert rows[0]["last_0b_age_sec"] == 31


def _hotset_receipt(day, target=0.3, resolved=10, coverage_count=None):
    template = _receipt(day)
    source = {
        "comparison_cost_contract_status": "verified",
        "comparison_cost_contract": {
            **template["contract"]["cost"],
            "contract_sha256": "a" * 64,
        },
        "official_symbol_master_binding": {
            "status": "verified",
            "artifact_sha256": "b" * 64,
        },
        "capacity_values": [2],
        "gross_target_values": [0.3, 1.3],
        "adverse_stop_values": [-0.3],
        "horizon_sec": 1200,
        "timeout_max_lag_sec": 5,
        "scenarios": [
            {
                **_group(resolved),
                "capacity_proxy": 2,
                "gross_target_pct": target,
                "adverse_stop_pct": -0.3,
                "cost_adjusted_resolved_outcome_count": resolved,
                "resolved_holding_sec_sum": resolved * 3,
                "profitable_outcome_count": resolved,
                "eligible_verified_common_stock_candidate_count": coverage_count
                or resolved,
            }
        ],
    }
    return mod.hotset_economic_receipt(
        {
            "target_date": day,
            "evaluation_phase": "postclose_final",
            "diagnostic_acceptance": {"status": "diagnostic_generated"},
            "scanner_unique_funnel": {"hotset_capacity_counterfactual": source},
        }
    )


def test_hotset_small_target_rolling_retains_cost_duration_and_frequency(tmp_path):
    previous = _hotset_receipt("2026-09-07")
    (tmp_path / "intraday_ws_freshness_monitor_2026-09-07.json").write_text(
        json.dumps({"daily_hotset_economic_receipt": previous})
    )
    current = _hotset_receipt("2026-09-08")
    result = mod.rolling_economics(current, tmp_path, hotset=True)
    group = result["groups"][0]
    assert group["source_only_comparison_ready"] is True
    assert group["source_quality_adjusted_ev_pct"] == pytest.approx(0.02)
    assert group["avg_resolved_holding_sec"] == 3
    assert group["resolved_observations_per_source_report_date"] == 10
    assert group["profitable_outcome_count"] == 20
    assert result["allowed_runtime_apply"] is False
    # Larger targets are a separate comparison, not ten extra small-target outcomes.
    result = mod.rolling_economics(
        _hotset_receipt("2026-09-08", target=1.3), tmp_path, hotset=True
    )
    assert len(result["groups"]) == 2
    assert all(g["resolved_outcome_count"] == 10 for g in result["groups"])


def test_below_coverage_subset_is_diagnostic_not_comparison_ready(tmp_path):
    result = mod.rolling_economics(
        _hotset_receipt("2026-09-08", resolved=20, coverage_count=40),
        tmp_path,
        hotset=True,
    )
    group = result["groups"][0]
    assert group["source_only_comparison_ready"] is False
    assert group["source_quality_adjusted_ev_pct"] is None
    assert group[
        "diagnostic_resolved_subset_equal_weight_avg_profit_pct"
    ] == pytest.approx(0.02)
    assert group["comparison_block_reasons"] == ["bbo_coverage_below_floor"]


@pytest.mark.parametrize("serialized", [False, True])
@pytest.mark.parametrize("scheduled_count", [6, 9, 10])
def test_natural_telemetry_indices_survive_coalescing_and_mirror_dedup(
    serialized, scheduled_count
):
    state = monitor._scanner_funnel_state_from_mapping({})
    common = {
        "stock_code": "005930",
        "scanner_scan_generation_id": "scan-1",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 1,
        "effective_venue": "KRX",
        "market_session_bucket": "KRX_REGULAR",
        "scanner_prune_reason": "general_slot_limit",
        "scanner_prune_observer_episode_id": "episode-1",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    for stage in (
        "scalping_scanner_candidate_pruned",
        "scalping_scanner_prune_bbo_schedule",
    ):
        monitor._update_scanner_funnel_state(
            state,
            {
                **common,
                "stage": stage,
                "scanner_prune_observer_schedule_status": "new_episode_scheduled",
                "scanner_prune_observer_scheduled_sample_count": (
                    str(scheduled_count) if serialized else scheduled_count
                ),
            },
            {},
        )
    for index, offset in enumerate(
        monitor.SCANNER_PRUNE_BBO_SAMPLE_OFFSETS_SEC[:scheduled_count]
    ):
        row = {
            **common,
            "stage": "scalping_scanner_prune_bbo_observation",
            "scanner_prune_observer_sample_index": index,
            "scanner_prune_observer_scheduled_offset_sec": offset,
            "scanner_prune_observer_status": "source_quality_gap",
            "scanner_prune_observer_gap_reason": "ka10004_shared_read_budget_deferred",
            "scanner_prune_observer_terminal_sample": index == scheduled_count - 1,
        }
        if serialized:
            row = {
                key: str(value) if type(value) in (bool, int) else value
                for key, value in row.items()
            }
        monitor._update_scanner_funnel_state(state, row, {})
        monitor._update_scanner_funnel_state(state, row, {})
    restored = monitor._scanner_funnel_state_from_mapping(
        json.loads(
            json.dumps({k: v for k, v in state.items() if k != "_fingerprint_set"})
        )
    )
    episodes = monitor._coalesce_prune_observation_episodes(restored["prunes"].values())
    accounted = mod.observer_receipt_accounting(episodes, 10)
    assert accounted["state_counts"]["scheduled_complete"] == 1
    assert accounted["unaccounted_episode_count"] == 0
    assert episodes[0]["prune_observer_sample_event_count"] == scheduled_count
    assert not episodes[0][
        "bbo_observations"
    ]  # gap receipts never become price evidence


@pytest.mark.parametrize("count", [None, 0, 11, True, "6", 6.0])
def test_bad_declared_horizon_never_closes_receipt(count):
    row = {
        "prune_observer_episode_id": "episode",
        "prune_observer_schedule_statuses": ["new_episode_scheduled"],
        "prune_observer_scheduled_sample_count": count,
        "prune_observer_receipt_indices": list(range(6)),
        "prune_observer_terminal_indices": [5],
    }
    assert mod.observer_receipt_accounting([row], 10)["unaccounted_episode_count"] == 1


def test_explicit_null_schedule_is_invalid_not_legacy_missing_metadata():
    state = monitor._scanner_funnel_state_from_mapping({})
    monitor._update_scanner_funnel_state(
        state,
        {
            "stage": "scalping_scanner_prune_bbo_schedule",
            "stock_code": "005930",
            "scanner_scan_generation_id": "scan-null",
            "scanner_prune_reason": "general_slot_limit",
            "scanner_prune_observer_episode_id": "episode-null",
            "scanner_prune_observer_schedule_status": "new_episode_scheduled",
            "scanner_prune_observer_scheduled_sample_count": None,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        {},
    )
    episodes = monitor._coalesce_prune_observation_episodes(state["prunes"].values())
    assert len(episodes) == 1
    assert (
        "scheduled_sample_count_or_authority_invalid"
        in episodes[0]["metadata_conflicts"]
    )
    episodes[0].update(
        prune_observer_receipt_indices=list(range(10)),
        prune_observer_receipt_terminal_valid=True,
    )
    assert (
        mod.observer_receipt_accounting(episodes, 10)["unaccounted_episode_count"] == 1
    )


def test_missing_terminal_and_conflicting_mirror_horizons_remain_gaps():
    row = {
        "prune_observer_episode_id": "episode",
        "prune_observer_schedule_statuses": ["new_episode_scheduled"],
        "prune_observer_scheduled_sample_count": 6,
        "prune_observer_receipt_indices": list(range(6)),
        "prune_observer_terminal_indices": [],
    }
    assert mod.observer_receipt_accounting([row], 10)["unaccounted_episode_count"] == 1
    other = {
        **row,
        "prune_observer_scheduled_sample_count": 9,
        "prune_observer_terminal_indices": [8],
        "prune_observer_receipt_indices": list(range(9)),
    }
    episodes = monitor._coalesce_prune_observation_episodes([row, other])
    assert episodes[0]["metadata_conflicts"]
    assert (
        mod.observer_receipt_accounting(episodes, 10)["unaccounted_episode_count"] == 1
    )


@pytest.mark.parametrize("value", [None, "", "unknown", "false", "0", 0, 1, [], {}])
def test_receipt_bool_never_grants_false_authority_to_unknown(value):
    assert monitor._receipt_bool(value) is None


@pytest.mark.parametrize(
    "value,expected", [(False, False), (True, True), ("False", False), ("True", True)]
)
def test_receipt_bool_matches_pipeline_logger_serialization(value, expected):
    assert monitor._receipt_bool(value) is expected


def test_collector_native_defer_reasons_are_receipts_not_captured_samples():
    episodes = [
        {"prune_observer_schedule_statuses": ["daily_request_budget_rejected"]},
        {
            "prune_observer_schedule_statuses": [
                "anchor_schedule_latency_exceeded",
                "active_episode_capacity_rejected",
            ]
        },
        {
            "prune_observer_schedule_statuses": [
                "anchor_schedule_latency_exceeded",
                "unknown",
            ]
        },
        {
            "prune_observer_schedule_statuses": [
                "new_episode_scheduled",
                "anchor_schedule_latency_exceeded",
            ]
        },
    ]
    result = mod.observer_receipt_accounting(episodes, 10)
    assert result["state_counts"] == {
        "bounded_not_admitted": 1,
        "source_quality_not_admitted": 1,
        "admission_receipt_gap": 1,
        "scheduled_receipt_gap": 1,
    }
    assert result["unaccounted_episode_count"] == 2
    assert "scheduled_complete" not in result["state_counts"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("resolved_holding_sec_sum", None),
        ("profitable_outcome_count", 99),
        ("resolved_return_sum_pct", None),
    ],
)
def test_hotset_rejects_invalid_economic_fields(tmp_path, field, value):
    receipt = _hotset_receipt("2026-09-08")
    receipt["groups"][0][field] = value
    receipt["sha256"] = mod._hash({k: v for k, v in receipt.items() if k != "sha256"})
    result = mod.rolling_economics(receipt, tmp_path, hotset=True)
    assert result["groups"] == []
    assert result["excluded_sources"][0]["scope"] == "group"
