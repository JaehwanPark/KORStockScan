from datetime import date, timedelta
import json

import pytest

from src.engine.monitoring import policy_research_economics as economics
from src.engine.automation.machine_entry_timing_tuning import (
    _candidate_observation,
    _evaluate_dynamic_cohort,
)
from src.engine.monitoring.machine_microstructure_attribution import (
    _unfilled_episode_decision_anchor,
)
from src.tests.test_machine_entry_timing_tuning import _entry_row

DAY = date(2026, 8, 28)


def admission_row(native="opportunity:1", symbol="000001"):
    return {
        "opportunity_episode_id": native,
        "stock_code": symbol,
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "first_census_at": f"{DAY}T09:00:00+09:00",
        "symbol_master_status": "verified",
        "instrument_type": "EQUITY",
        "listing_market": "KOSPI",
        "stage_reached": {"candidate_evaluated": True},
        "first_stage_at": {"candidate_evaluated": f"{DAY}T09:00:01+09:00"},
    }


def test_admission_union_conserves_native_projections_without_outcome_selection():
    enrolled = admission_row()
    missed = admission_row("opportunity:2", "000002")
    census = {
        "target_date": str(DAY),
        "opportunity_details": {
            "liquid_common": {"top_20": {"forward_exact": [enrolled]}},
            "all": {
                "top_50": {
                    "forward_exact": [dict(enrolled, ex_post_profit=999), missed],
                    "same_day_any_venue_retrospective": [admission_row("oracle")],
                }
            },
        },
    }
    ledger = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    assert ledger["input_count"] == 3
    assert ledger["native_id_count"] == 2
    assert ledger["disposition_counts"] == {
        "admitted": 1,
        "deferred_capacity": 1,
        "duplicate_projection": 1,
    }
    assert ledger["unaccounted_count"] == 0
    assert ledger["catalog_mutated"] is False
    assert ledger["allowed_runtime_apply"] is False
    assert all(row.get("native_id") != "oracle" for row in ledger["dispositions"])
    del census["opportunity_details"]["all"]["top_50"]["forward_exact"][0][
        "ex_post_profit"
    ]
    second = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    assert second["disposition_counts"] == ledger["disposition_counts"]


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ({"opportunity_episode_id": None}, "native_identity_missing"),
        ({"symbol_master_status": "missing"}, "official_common_stock_binding_missing"),
        (
            {"stage_reached": {"candidate_evaluated": "true"}},
            "causal_scanner_candidate_join_unproven",
        ),
        (
            {"first_stage_at": {"candidate_evaluated": f"{DAY}T08:59:59+09:00"}},
            "causal_scanner_candidate_join_unproven",
        ),
        (
            {"first_census_at": "2026-08-27T09:00:00+09:00"},
            "causal_scanner_candidate_join_unproven",
        ),
    ],
)
def test_admission_never_invents_causal_candidate_or_common_stock(mutation, reason):
    census = {
        "target_date": str(DAY),
        "opportunity_details": [dict(admission_row(), **mutation)],
    }
    result = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    assert result["dispositions"][0]["reason"] == reason
    assert result["disposition_counts"] == {"source_gap": 1}


def test_admission_conflicting_native_binding_is_not_first_projection_winner():
    rows = [
        admission_row(),
        dict(admission_row(), stage_reached={"candidate_evaluated": False}),
    ]
    for source in (rows, rows[::-1]):
        result = economics.research_admission_ledger(
            {"target_date": str(DAY), "opportunity_details": source},
            source_date=DAY,
            universe={"000001": "fixed"},
            owner="widget",
        )
        assert result["disposition_counts"] == {"source_gap": 2}
        assert {row["reason"] for row in result["dispositions"]} == {
            "conflicting_native_scope"
        }


def test_admission_gap_scope_and_valid_lane_are_isolated():
    census = {
        "target_date": str(DAY),
        "opportunity_details": {
            "all": {"top_20": {"forward_exact": [dict(admission_row(), venue="NXT")]}},
            "liquid_common": {
                "top_20": {"forward_exact": [admission_row("valid")]},
                "top_50": None,
            },
        },
    }
    result = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    assert result["status"] == "source_gap"
    assert result["disposition_counts"] == {"excluded_by_contract": 1, "admitted": 1}
    assert result["unaccounted_count"] == 0
    assert len(result["malformed_scopes"]) == 1


def test_bounded_census_reader_rejects_alias_nonfinite_oversize_and_non_object(
    tmp_path,
):
    path = tmp_path / "census.json"
    path.write_text(json.dumps({"target_date": str(DAY), "opportunity_details": []}))
    assert economics.load_research_census(path)["target_date"] == str(DAY)
    alias = tmp_path / "alias.json"
    alias.symlink_to(path)
    assert economics.load_research_census(alias) is None
    assert economics.load_research_census(path, maximum_bytes=1) is None
    for raw in ('{"bad": NaN}', "[]", "not-json"):
        path.write_text(raw)
        assert economics.load_research_census(path) is None


def test_handoff_malformed_primary_preserves_valid_expanded_scope():
    census = {
        "target_date": str(DAY),
        "opportunity_details": {
            "liquid_common": [],
            "all": {"top_50": {"forward_exact": [admission_row()]}},
        },
    }
    result = economics.research_universe_handoff(
        census, source_date=DAY, universe={"000001": "fixed"}, results={}
    )
    assert result["status"] == "source_gap"
    assert result["admission_ledger"]["disposition_counts"] == {"admitted": 1}


def test_future_ai_progress_does_not_change_native_admission_deduplication():
    row = admission_row()
    projection = dict(
        row,
        stage_reached={"candidate_evaluated": True, "submitted": True},
        first_stage_at={**row["first_stage_at"], "submitted": f"{DAY}T09:10:00+09:00"},
    )
    result = economics.research_admission_ledger(
        {"target_date": str(DAY), "opportunity_details": [row, projection]},
        source_date=DAY,
        universe={"000001": "fixed"},
        owner="widget",
    )
    assert result["disposition_counts"] == {"admitted": 1, "duplicate_projection": 1}


def test_malformed_master_field_is_a_scoped_gap_not_global_crash():
    result = economics.research_admission_ledger(
        {
            "target_date": str(DAY),
            "opportunity_details": [
                dict(admission_row(), listing_market=[]),
                admission_row("valid"),
            ],
        },
        source_date=DAY,
        universe={"000001": "fixed"},
        owner="widget",
    )
    assert result["disposition_counts"] == {"source_gap": 1, "admitted": 1}


def test_admission_registered_scope_is_owner_specific_and_future_clock_is_blocked():
    census = {
        "target_date": str(DAY),
        "generated_at": f"{DAY}T09:00:02+09:00",
        "opportunity_details": [
            dict(admission_row(), venue="NXT", session="NXT_REGULAR_OVERLAP")
        ],
    }
    episode = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="low_price_two_leg"
    )
    widget = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    assert episode["disposition_counts"] == {"admitted": 1}
    assert widget["disposition_counts"] == {"excluded_by_contract": 1}
    census["generated_at"] = f"{DAY}T09:00:00+09:00"
    episode = economics.research_admission_ledger(
        census, source_date=DAY, universe={"000001": "fixed"}, owner="low_price_two_leg"
    )
    assert episode["disposition_counts"] == {"source_gap": 1}


def test_admission_before_baseline_is_never_tuning_ready():
    old = date(2026, 6, 4)
    ledger = economics.research_admission_ledger(
        {"target_date": str(old), "opportunity_details": []},
        source_date=old,
        universe={},
        owner="widget",
    )
    assert ledger["status"] == "source_gap"
    assert ledger["input_count"] is None


def test_bounded_census_reader_rejects_replaced_path_generation(tmp_path, monkeypatch):
    path = tmp_path / "census.json"
    path.write_text('{"opportunity_details": []}')
    original = economics.os.stat

    def replaced_stat(target, **kwargs):
        if target == path:
            replacement = tmp_path / "replacement.json"
            replacement.write_text('{"opportunity_details": []}')
            replacement.replace(path)
        return original(target, **kwargs)

    monkeypatch.setattr(economics.os, "stat", replaced_stat)
    assert economics.load_research_census(path) is None


def test_compact_census_publication_consumes_large_parent_without_rescan(
    tmp_path, monkeypatch
):
    from src.engine.monitoring import market_opportunity_census as producer

    monkeypatch.setattr(producer, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(producer, "render_markdown", lambda report: "source-only")
    report = {
        "target_date": str(DAY),
        "generated_at": f"{DAY}T15:30:00+09:00",
        "opportunity_details": {
            "all": {"top_50": {"forward_exact": [admission_row()]}},
            "liquid_common": {"top_20": {"forward_exact": [admission_row()]}},
        },
        "large_ex_post_diagnostic": "x" * (5 * 1024 * 1024),
    }
    json_path, _ = producer.write_report(report)
    assert json_path.stat().st_size > 4 * 1024 * 1024
    sidecar = json_path.with_suffix(".admission.json")
    assert sidecar.stat().st_size < 4096
    reads = []
    original = economics._load_bounded_research_summary

    def observed_read(path, **kwargs):
        reads.append(path)
        return original(path, **kwargs)

    monkeypatch.setattr(economics, "_load_bounded_research_summary", observed_read)
    compact = economics.load_research_census(json_path)
    assert reads == [sidecar]
    assert (
        compact["canonical_parent"]["sha256"]
        == __import__("hashlib").sha256(json_path.read_bytes()).hexdigest()
    )
    oracle = economics.research_admission_ledger(
        report, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    result = economics.research_admission_ledger(
        compact, source_date=DAY, universe={"000001": "fixed"}, owner="widget"
    )
    assert result["disposition_counts"] == oracle["disposition_counts"]
    assert result["input_count"] == 2
    assert result["unaccounted_count"] == 0
    assert result["dispositions"][0]["canonical_source_row_sha256"] == economics.digest(
        admission_row()
    )
    json_path.write_text(json_path.read_text() + " ")
    assert economics.load_research_census(json_path) is None


def test_compact_corruption_never_falls_back_to_old_full_summary(tmp_path, monkeypatch):
    from src.engine.monitoring import market_opportunity_census as producer

    monkeypatch.setattr(producer, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(producer, "render_markdown", lambda report: "source-only")
    report = {"target_date": str(DAY), "opportunity_details": [admission_row()]}
    parent, _ = producer.write_report(report)
    sidecar = parent.with_suffix(".admission.json")
    payload = json.loads(sidecar.read_text())
    payload["opportunity_details"][0]["stock_code"] = "999999"
    sidecar.write_text(json.dumps(payload))
    assert economics.load_research_census(parent) is None


def test_episode_admission_phase_refresh_preserves_economic_selection():
    from src.engine.monitoring import (
        low_price_two_leg_expanded_candidate_research as producer,
    )

    report = {
        "end_date": str(DAY),
        "research_profile_inventory": {
            "profile": {"symbol": "000001", "name": "fixed"}
        },
        "recommendations": [{"policy": "unchanged"}],
        "source_input_fingerprint": "frozen-economics",
    }
    original = json.loads(json.dumps(report))
    producer._attach_admission_evidence(
        report,
        market_census={
            "target_date": str(DAY),
            "opportunity_details": [admission_row()],
        },
    )
    assert report["research_admission_ledger"]["disposition_counts"] == {"admitted": 1}
    old_phase = report["admission_input_fingerprint"]
    producer._attach_admission_evidence(
        report,
        market_census={
            "target_date": str(DAY),
            "opportunity_details": [admission_row(), admission_row("new", "000002")],
        },
    )
    assert report["admission_input_fingerprint"] != old_phase
    assert report["research_admission_ledger"]["disposition_counts"] == {
        "admitted": 1,
        "deferred_capacity": 1,
    }
    assert report["recommendations"] == original["recommendations"]
    assert report["source_input_fingerprint"] == original["source_input_fingerprint"]


def test_census_publication_busy_preserves_verified_parent(tmp_path, monkeypatch):
    from src.engine.monitoring import market_opportunity_census as producer

    monkeypatch.setattr(producer, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(producer, "render_markdown", lambda report: "source-only")
    report = {"target_date": str(DAY), "opportunity_details": [admission_row()]}
    parent, _ = producer.write_report(report)
    previous = parent.read_bytes()
    with (tmp_path / f"market_opportunity_census_{DAY}.publish.lock").open(
        "r+"
    ) as lock:
        producer.fcntl.flock(
            lock.fileno(), producer.fcntl.LOCK_EX | producer.fcntl.LOCK_NB
        )
        with pytest.raises(BlockingIOError):
            producer.write_report(dict(report, added="not published"))
    assert parent.read_bytes() == previous
    assert economics.load_research_census(parent) is not None


def common_row(*, loss=False, submitted=False):
    row = _entry_row(DAY, 1)
    row.update(
        actual_order_submitted=submitted,
        owner_lifecycle_contract_valid=True,
        source_entry_event_id="native:decision:1",
    )
    deadline = economics.aware(row["anchor_at"]) + timedelta(seconds=300)
    for label in row["dynamic_confirmation_first_hit_outcomes"][
        "checkpoint_outcomes"
    ].values():
        label["common_horizon_terminal"] = {
            "schema": "machine_common_horizon_terminal_v1",
            "deadline_at": deadline.isoformat(),
            "observed_at": deadline.isoformat(),
            "executable_bid": 98.0,
            "available_bid_quantity": 10,
            "quote_age_ms": 0,
            "source_quality_status": "eligible",
            "source_gap_reasons": [],
            "evaluation_only": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        if loss:
            label["target_adverse_first_hit"].update(
                state="unresolved",
                target_at=None,
                target_executable_bid=None,
                target_available_bid_quantity=None,
            )
    return row


def observe(row):
    return economics.source_only_timing_observation(
        source_date=DAY, row=row, replay=row["dynamic_confirmation_source_only_replay"]
    )


@pytest.mark.parametrize("submitted", [False, None, True])
def test_common_counterfactual_includes_original_decision_without_realized_fill(
    submitted,
):
    row = common_row(submitted=submitted)
    row["owner_outcome"] = {"realized": False}
    result = observe(row)
    assert result is not None
    assert result["realized_quantity"] is None
    assert result["modeled_quantity"] == 10
    assert result["reported_cost_aware_net_pct"] is None
    assert result["candidate_modeled_net_profit_krw"] > 0
    assert _candidate_observation(source_date=DAY, row=row, delay_sec=1) is None
    cohort = _evaluate_dynamic_cohort(cohort_rows=[(DAY, row)], target_date=DAY)
    assert cohort["source_only_economic_pair_count"] == 1
    assert (
        cohort["economic_population_basis"]
        == "common_300s_counterfactual_all_decisions"
    )


def test_unresolved_losing_opportunity_is_not_removed_or_imputed_as_zero():
    result = observe(common_row(loss=True))
    assert result["baseline_modeled_net_profit_krw"] < 0
    assert result["candidate_modeled_net_profit_krw"] < 0
    assert result["baseline_capital_krw_minutes"] == 5000


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(anchor_role="prospective_widget_research_entry"),
        lambda row: row.update(source_entry_event_id=""),
        lambda row: row.update(owner_requested_quantity=11),
        lambda row: row["dynamic_confirmation_first_hit_outcomes"][
            "checkpoint_outcomes"
        ]["1"].update(sequence_epoch=8),
        lambda row: row["dynamic_confirmation_first_hit_outcomes"][
            "checkpoint_outcomes"
        ]["0"]["common_horizon_terminal"].update(available_bid_quantity=9),
        lambda row: row["dynamic_confirmation_first_hit_outcomes"][
            "checkpoint_outcomes"
        ]["0"]["common_horizon_terminal"].update(quote_age_ms=999),
    ],
)
def test_common_economics_rejects_missing_signal_quantity_epoch_and_terminal(mutate):
    row = common_row()
    mutate(row)
    assert observe(row) is None


def episode(day="2026-08-28", *, price=100, net=1, minute=0):
    return {
        "entry_at": f"{day}T09:{minute:02}:00+09:00",
        "exit_at": f"{day}T09:{minute+1:02}:00+09:00",
        "entry_price": price,
        "exit_price": price * (1 + net / 100),
        "net_return_pct": net,
        "exit_reason": "target",
    }


def test_valid_zero_day_changes_profit_frequency_without_inventing_missing_outcome():
    rows = [episode()]
    one = economics.modeled_summary(rows, [DAY])
    two = economics.modeled_summary(rows, [DAY, date(2026, 8, 27)])
    assert one["modeled_net_profit_krw"] == two["modeled_net_profit_krw"] == 10
    assert two["modeled_net_pnl_per_qualified_day"] == 5
    rows[0]["net_return_pct"] = None
    assert economics.modeled_summary(rows, [DAY])["modeled_net_profit_krw"] is None


def test_joint_capital_cannot_sum_two_infeasible_simultaneous_winners():
    result = economics.joint_capital_demand(
        {"000001": [episode()], "000002": [episode()]}, capital_limit_krw=1000
    )
    assert result["modeled_peak_concurrent_notional_krw"] == 2000
    assert result["independent_modeled_net_profit_krw"] == 20
    assert result["feasible_combined_net_profit_krw"] is None
    assert result["capital_feasible"] is False
    assert (
        economics.joint_capital_demand({"000001": [episode()]})["status"]
        == "allocation_contract_missing"
    )


def test_joint_capital_releases_before_same_timestamp_entry():
    rows = {"000001": [episode()], "000002": [episode(minute=1)]}
    result = economics.joint_capital_demand(rows, capital_limit_krw=1000)
    assert result["capital_feasible"] is True
    assert result["feasible_combined_net_profit_krw"] == 20


def test_universe_census_does_not_enroll_a_missed_symbol_or_duplicate_panels():
    census = {
        "target_date": DAY.isoformat(),
        "opportunity_details": {
            "liquid_common": {
                "top_20": {
                    "forward_exact": [
                        {"stock_code": "000001", "opportunity_id": "a"},
                        {"stock_code": "000002", "opportunity_id": "b"},
                    ]
                }
            },
            "another_overlapping_panel": {
                "top_20": {"forward_exact": [{"stock_code": "000001"}]}
            },
        },
    }
    result = economics.research_universe_handoff(
        census, source_date=DAY, universe={"000001": "registered"}, results={}
    )
    assert result["input_count"] == 2
    assert result["unaccounted_count"] == 0
    assert result["disposition_counts"]["not_enrolled_research_universe"] == 1
    assert result["runtime_effect"] is False


def write_quotes(tmp_path, *, raw_only=False, depth=40):
    signal = {"segment": "morning"}
    rows = []
    for clock, bid, ask, state in [
        ("09:00:00", 99, 100, "ENTRY_READY"),
        ("09:01:00", 101, 102, "WATCH"),
    ]:
        at = f"{DAY.isoformat()}T{clock}+09:00"
        rows.append(
            {
                "symbol": "000001",
                "observed_at_kst": at,
                "market_venue": "KRX",
                "advisory_generated": not raw_only,
                "observation_seed": {
                    "parameters_sha256": economics.digest(signal),
                    "effective_at_kst": f"{DAY.isoformat()}T08:00:00+09:00",
                },
                "advisory": {
                    "session": "KRX_REGULAR",
                    "source_quality": {"status": "PASS"},
                    "state": state,
                },
                "bbo": {
                    "best_bid": bid,
                    "best_ask": ask,
                    "best_bid_qty": depth,
                    "best_ask_qty": depth,
                    "received_at": at,
                },
            }
        )
    path = tmp_path / f"widget_symbol_advisory_000001_{DAY:%Y%m%d}.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    result = {
        "selected_policy": signal,
        "calibration": {"episodes": [episode()]},
        "holdout": {"episodes": []},
    }
    return result, signal, path


@pytest.mark.parametrize(
    "raw_only,depth,expected",
    [(False, 40, "pass"), (True, 40, "source_gap"), (False, 39, "source_gap")],
)
def test_proxy_needs_exact_seed_full_quantity_entry_and_exit(
    tmp_path, raw_only, depth, expected
):
    result, signal, _ = write_quotes(tmp_path, raw_only=raw_only, depth=depth)
    receipt = economics.signal_execution_feasibility(
        result,
        symbol="000001",
        source_date=DAY,
        signal_policy=signal,
        observation_dir=tmp_path,
    )
    assert receipt["status"] == expected
    assert receipt["allowed_runtime_apply"] is False


def test_proxy_cannot_reuse_other_candidate_seed_or_symlink_source(tmp_path):
    result, signal, path = write_quotes(tmp_path)
    receipt = economics.signal_execution_feasibility(
        result,
        symbol="000001",
        source_date=DAY,
        signal_policy={"segment": "midday"},
        observation_dir=tmp_path,
    )
    assert receipt["status"] == "source_gap"
    original = tmp_path / "original"
    path.rename(original)
    path.symlink_to(original)
    assert (
        economics.signal_execution_feasibility(
            result,
            symbol="000001",
            source_date=DAY,
            signal_policy=signal,
            observation_dir=tmp_path,
        )["status"]
        == "source_gap"
    )


def test_pending_episode_keeps_original_quantity_and_unknown_order_status():
    at = economics.aware(f"{DAY.isoformat()}T09:00:00+09:00")
    result = _unfilled_episode_decision_anchor(
        leg={"entry_price": 100, "quantity": 10, "target_price": 101},
        lifecycle_id="life",
        leg_id="leg1",
        decision_at=at,
        source_event_id="native",
        owner_row_eligible=True,
        symbol="000001",
        session="KRX_REGULAR",
        scope_id="registered",
        expected_venues=["KRX"],
        expected_buckets=["KRX_REGULAR"],
        cost_pct=0.23,
        source_quality={},
    )
    assert result["owner_requested_quantity"] == 10
    assert result["owner_outcome"]["entry_notional_krw"] is None
    assert result["actual_order_submitted"] is None


def test_confirmation_projection_does_not_turn_unknown_order_status_into_no_order():
    from src.engine.monitoring.machine_microstructure_attribution import (
        _entry_confirmation_label,
    )

    pending = {
        "anchor_role": "episode_signal_decision_leg",
        "actual_order_submitted": None,
        "owner": "episode",
        "metrics": {},
    }
    assert _entry_confirmation_label(pending)["actual_order_submitted"] is None


def test_common_replay_never_pools_legacy_actual_terminal_with_new_cf_horizon():
    current = common_row()
    legacy = _entry_row(DAY, 2)
    result = _evaluate_dynamic_cohort(
        cohort_rows=[(DAY, current), (DAY, legacy)], target_date=DAY
    )
    assert result["source_only_economic_pair_count"] == 1
    assert result["right_censored_count"] == 1
    assert result["population_disposition"]["unaccounted_count"] == 0


def test_optional_corrupt_census_is_a_diagnostic_gap_not_a_global_research_crash():
    census = {
        "target_date": DAY.isoformat(),
        "opportunity_details": [],
        "bad": float("nan"),
    }
    result = economics.research_universe_handoff(
        census, source_date=DAY, universe={}, results={}
    )
    assert result["status"] == "source_gap"
    assert result["allowed_runtime_apply"] is False


def test_duplicate_proxy_episode_cannot_reuse_one_quote_pair_twice(tmp_path):
    result, signal, _ = write_quotes(tmp_path)
    result["holdout"]["episodes"] = list(result["calibration"]["episodes"])
    assert (
        economics.signal_execution_feasibility(
            result,
            symbol="000001",
            source_date=DAY,
            signal_policy=signal,
            observation_dir=tmp_path,
        )["status"]
        == "source_gap"
    )


def test_combined_report_reconciles_execution_blocks_and_all_selected_lineage():
    from src.engine.monitoring.widget_symbol_signal_policy_research import (
        _attach_population_evidence,
    )

    report = {
        "end_date": DAY.isoformat(),
        "symbol_universe": {"005930": "Samsung", "000660": "SK"},
        "passed_symbols": ["005930", "000660"],
        "symbols": {
            "005930": {
                "decision": "execution_feasibility_missing_no_widget_runtime_promotion",
                "selected_episodes": {"calibration": [episode()]},
            },
            "000660": {
                "decision": "holdout_pass_widget_signal_policy_candidate",
                "holdout": {"episodes": [episode(minute=1)]},
            },
        },
    }
    result = _attach_population_evidence(report, market_census={})
    assert result["passed_symbols"] == ["000660"]
    assert result["joint_capital_demand"]["independent_modeled_net_profit_krw"] == 20


def test_checkpoint_fingerprint_tracks_raw_generation_without_reading_raw(
    tmp_path,
    monkeypatch,
):
    from src.engine.monitoring import widget_symbol_signal_policy_research as research
    from src.engine.monitoring import widget_symbol_runtime_contract as contract

    monkeypatch.setattr(contract, "DEFAULT_OBSERVATION_DIR", tmp_path)
    monkeypatch.setattr(research, "DATA_DIR", tmp_path)
    kwargs = dict(
        sources={},
        end_date=date(2026, 9, 17),
        applied_baselines={},
        symbol_universe={"005930": "Samsung"},
        symbol_origins={},
    )
    missing = research.research_input_fingerprint(**kwargs)
    raw = tmp_path / "widget_symbol_advisory_005930_20260916.jsonl"
    raw.write_text("not parsed by fingerprint\n")
    present = research.research_input_fingerprint(**kwargs)
    assert present != missing
    assert present == research.research_input_fingerprint(**kwargs)
    raw.write_text("new generation with changed size\n")
    assert research.research_input_fingerprint(**kwargs) != present
