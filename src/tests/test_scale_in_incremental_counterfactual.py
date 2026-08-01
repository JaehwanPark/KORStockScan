from src.engine.lifecycle import scale_in_incremental_counterfactual as mod


def _event(stage, emitted_at, **fields):
    return {"stage": stage, "emitted_at": emitted_at, "fields": fields}


def test_final_price_uses_latest_sell_after_decision():
    events = [
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "2026-06-12T09:00:00+09:00",
            assumed_fill_price=900,
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "2026-06-12T10:10:00+09:00",
            assumed_fill_price=1050,
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "2026-06-12T10:20:00+09:00",
            assumed_fill_price=1100,
        ),
    ]
    decision_time = mod._parse_emitted_at(
        _event("decision", "2026-06-12T10:00:00+09:00")
    )

    assert mod._find_evaluation_price(events, decision_time, None) == 1100.0


def test_horizon_summary_is_independent_and_unfilled_is_not_primary():
    filled = {
        "scale_in_arm": "PYRAMID",
        "quote_touched": True,
        "runtime_ev_eligible": True,
        "final_horizon_complete": True,
        "all_horizons_complete": False,
        "horizons": {
            "10min": {"incremental_notional_ev_pct": 1.0},
            "30min": {"status": "horizon_incomplete"},
            "60min": {"status": "horizon_incomplete"},
            "final": {"incremental_notional_ev_pct": 2.0},
        },
    }
    unfilled = {
        **filled,
        "quote_touched": False,
        "runtime_ev_eligible": False,
        "treatment_state": "WOULD_ADD_UNFILLED",
        "horizons": {
            **filled["horizons"],
            "final": {"incremental_notional_ev_pct": 99.0},
        },
    }

    summary = mod._build_summary([filled, unfilled], "2026-06-12", 0, {})
    cohorts = mod._build_cohorts([filled, unfilled])

    assert summary["horizon_summary"]["10min"]["sample"] == 1
    assert summary["horizon_summary"]["30min"]["sample"] == 0
    assert summary["horizon_summary"]["final"]["sample"] == 1
    assert summary["horizon_summary"]["final"]["incremental_notional_ev_pct"] == 2.0
    assert (
        cohorts["by_quote_touched"]["unfilled"]["horizons"]["final"][
            "incremental_notional_ev_pct"
        ]
        == 99.0
    )
    assert (
        cohorts["combined_primary_filled"]["horizons"]["final"][
            "incremental_notional_ev_pct"
        ]
        == 2.0
    )


def test_clean_baseline_timestamp_excludes_earlier_same_day_event():
    policy = {"clean_tuning_baseline_ts_kst": "2026-06-04T14:29:09+09:00"}

    assert not mod._event_allowed_by_clean_baseline(
        _event("x", "2026-06-04T14:29:08+09:00"), policy
    )
    assert mod._event_allowed_by_clean_baseline(
        _event("x", "2026-06-04T14:29:09+09:00"), policy
    )


def test_sim_counterfactual_authority_rejects_real_or_incomplete_contract():
    assert mod._has_sim_counterfactual_authority(
        _event(
            "scalp_sim_scale_in_counterfactual_started",
            "2026-06-12T10:00:00+09:00",
            actual_order_submitted=False,
            broker_order_forbidden=True,
        )
    )
    assert not mod._has_sim_counterfactual_authority(
        _event(
            "scalp_sim_scale_in_counterfactual_started",
            "2026-06-12T10:00:00+09:00",
            actual_order_submitted=True,
            broker_order_forbidden=False,
        )
    )
    assert not mod._has_sim_counterfactual_authority(
        _event(
            "scalp_sim_scale_in_counterfactual_started",
            "2026-06-12T10:00:00+09:00",
            actual_order_submitted=False,
        )
    )
    assert mod._has_sim_counterfactual_authority(
        _event(
            "scalp_sim_scale_in_order_unfilled",
            "2026-06-12T10:00:00+09:00",
            actual_order_submitted=False,
        )
    )


def test_incremental_pnl_equals_added_tranche_pnl_without_average_price_rounding():
    result = mod._compute_incremental_pnl(3, 1011, 2, 997, 1053.0)

    expected = mod.calculate_net_realized_pnl(997, 1053, 2)
    assert result["incremental_pnl_krw"] == expected


def test_mixed_canonical_and_legacy_events_are_merged(monkeypatch):
    canonical = _event(
        "scalp_sim_scale_in_counterfactual_started",
        "2026-06-12T10:00:00+09:00",
        sim_record_id="sim-1",
        scale_in_decision_id="canonical-1",
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    legacy = _event(
        "scalp_sim_scale_in_order_unfilled",
        "2026-06-12T10:01:00+09:00",
        sim_record_id="sim-2",
        add_type="PYRAMID",
        ord_no="legacy-1",
        qty=1,
        limit_price=1000,
        actual_order_submitted=False,
    )
    monkeypatch.setattr(
        mod, "_iter_events", lambda target_date: iter([canonical, legacy])
    )

    events = mod._find_counterfactual_events("2026-06-12")

    decision_ids = {item["fields"]["scale_in_decision_id"] for item in events}
    assert "canonical-1" in decision_ids
    assert any(item.startswith("sim-2+PYRAMID+") for item in decision_ids)


def test_canonical_event_without_decision_id_is_excluded_and_diagnosed(monkeypatch):
    missing_id = _event(
        "scalp_sim_scale_in_counterfactual_started",
        "2026-06-12T10:00:00+09:00",
        sim_record_id="sim-1",
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter([missing_id]))
    diagnostics = {}

    events = mod._find_counterfactual_events("2026-06-12", diagnostics)

    assert events == []
    assert diagnostics == {"missing_scale_in_decision_id": 1}


def test_build_report_surfaces_missing_decision_id_exclusion(monkeypatch):
    missing_id = _event(
        "scalp_sim_scale_in_counterfactual_started",
        "2026-06-12T10:00:00+09:00",
        sim_record_id="sim-1",
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter([missing_id]))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "instrumentation_gap"
    assert report["error"] == "counterfactual_event_contract_gap"
    assert report["source_quality_gate"] == "pass_with_row_exclusions"
    assert report["summary"]["source_quality_excluded_event_count"] == 1
    assert report["summary"]["source_quality_exclusion_reasons"] == {
        "missing_scale_in_decision_id": 1
    }
    assert report["summary"]["no_sample_reason"] == (
        "counterfactual_rows_excluded_by_source_quality"
    )


def test_build_report_distinguishes_no_natural_scale_in_sample(monkeypatch):
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter([]))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "no_natural_sample"
    assert report["error"] is None
    assert report["window_policy"] == "daily_only"
    assert report["runtime_authority_ready"] is False
    assert report["primary_decision_metric"] == "incremental_notional_ev_pct"
    assert report["summary"]["candidate_activity_count"] == 0
    assert report["summary"]["no_sample_reason"] == "no_scale_in_candidate_activity"


def test_build_report_flags_candidate_activity_without_counterfactual(monkeypatch):
    candidate = _event(
        "scalp_sim_scale_in_candidate_funnel",
        "2026-06-12T10:00:00+09:00",
        sim_record_id="sim-1",
        scale_in_arm="PYRAMID",
        scale_in_candidate_funnel_state="eligible",
    )
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter([candidate]))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "instrumentation_gap"
    assert report["error"] == "counterfactual_event_contract_gap"
    assert report["summary"]["candidate_activity_count"] == 1
    assert report["summary"]["no_sample_reason"] == (
        "eligible_candidate_without_terminal_execution_event"
    )


def test_guard_blocked_eligible_candidate_is_no_natural_execution_sample(monkeypatch):
    events = [
        _event(
            "scalp_sim_scale_in_candidate_funnel",
            "2026-06-12T10:00:00+09:00",
            sim_record_id="sim-1",
            scale_in_arm="AVG_DOWN",
            scale_in_candidate_funnel_state="eligible",
        ),
        _event(
            "scale_in_qty_block",
            "2026-06-12T10:00:01+09:00",
            sim_record_id="sim-1",
            scale_in_arm="AVG_DOWN",
            decision="qty_guard_blocked",
            reason="reversal_probe_missing",
        ),
    ]
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter(events))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "no_natural_sample"
    assert report["error"] is None
    assert report["summary"]["eligible_candidate_count"] == 1
    assert report["summary"]["guard_blocked_before_execution_count"] == 1
    assert report["summary"]["unresolved_eligible_candidate_count"] == 0
    assert report["summary"]["no_sample_reason"] == (
        "all_eligible_candidates_guard_blocked_before_execution"
    )


def test_legacy_sim_terminal_closes_eligible_lineage(monkeypatch):
    events = [
        _event(
            "scalp_sim_scale_in_candidate_funnel",
            "2026-06-12T10:00:00+09:00",
            sim_record_id="sim-legacy",
            scale_in_arm="PYRAMID",
            scale_in_candidate_funnel_state="eligible",
        ),
        _event(
            "scalp_sim_scale_in_order_unfilled",
            "2026-06-12T10:00:01+09:00",
            sim_record_id="sim-legacy",
            add_type="PYRAMID",
            ord_no="legacy-1",
            qty=1,
            limit_price=1000,
            prev_buy_qty=2,
            prev_buy_price=990,
            actual_order_submitted=False,
        ),
    ]
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter(events))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "evaluated"
    assert report["error"] is None
    assert report["summary"]["eligible_candidate_count"] == 1
    assert report["summary"]["execution_started_from_eligible_count"] == 0
    assert report["summary"]["legacy_execution_terminal_from_eligible_count"] == 1
    assert report["summary"]["terminal_execution_event_from_eligible_count"] == 1
    assert report["summary"]["unresolved_eligible_candidate_count"] == 0


def test_real_legacy_terminal_does_not_close_sim_eligible_lineage(monkeypatch):
    events = [
        _event(
            "scalp_sim_scale_in_candidate_funnel",
            "2026-06-12T10:00:00+09:00",
            sim_record_id="sim-real",
            scale_in_arm="PYRAMID",
            scale_in_candidate_funnel_state="eligible",
        ),
        _event(
            "scalp_sim_scale_in_order_assumed_filled",
            "2026-06-12T10:00:01+09:00",
            sim_record_id="sim-real",
            add_type="PYRAMID",
            qty=1,
            limit_price=1000,
            actual_order_submitted=True,
            broker_order_forbidden=False,
        ),
    ]
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter(events))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "instrumentation_gap"
    assert report["summary"]["legacy_execution_terminal_from_eligible_count"] == 0
    assert report["summary"]["unresolved_eligible_candidate_count"] == 1


def test_immediate_sim_exit_closes_eligible_candidate_lineage(monkeypatch):
    events = [
        _event(
            "scalp_sim_scale_in_candidate_funnel",
            "2026-06-12T10:00:00+09:00",
            sim_record_id="sim-exit",
            scale_in_arm="AVG_DOWN",
            scale_in_candidate_funnel_state="eligible",
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "2026-06-12T10:00:00.100000+09:00",
            sim_record_id="sim-exit",
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
    ]
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter(events))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "no_natural_sample"
    assert report["summary"]["candidate_terminal_from_eligible_count"] == 1
    assert report["summary"]["candidate_terminal_reasons"] == {
        "exit_preempted_scale_in_candidate": 1
    }
    assert report["summary"]["terminal_execution_event_from_eligible_count"] == 0
    assert report["summary"]["terminal_candidate_event_from_eligible_count"] == 1
    assert report["summary"]["unresolved_eligible_candidate_count"] == 0
    assert report["summary"]["no_sample_reason"] == (
        "eligible_candidates_closed_without_counterfactual_execution"
    )


def test_next_quota_funnel_state_closes_prior_eligible_lineage(monkeypatch):
    events = [
        _event(
            "scalp_sim_scale_in_candidate_funnel",
            "2026-06-12T10:00:00+09:00",
            sim_record_id="sim-quota",
            scale_in_arm="AVG_DOWN",
            scale_in_candidate_funnel_state="eligible",
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
        _event(
            "scalp_sim_scale_in_candidate_funnel",
            "2026-06-12T10:00:20+09:00",
            sim_record_id="sim-quota",
            scale_in_arm="AVG_DOWN",
            scale_in_candidate_funnel_state="position_quota_blocked",
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
    ]
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter(events))

    report = mod.build_report("2026-06-12")

    assert report["status"] == "no_natural_sample"
    assert report["summary"]["candidate_terminal_from_eligible_count"] == 1
    assert report["summary"]["candidate_terminal_reasons"] == {
        "next_funnel_state:position_quota_blocked": 1
    }
    assert report["summary"]["terminal_execution_event_from_eligible_count"] == 0
    assert report["summary"]["terminal_candidate_event_from_eligible_count"] == 1
    assert report["summary"]["unresolved_eligible_candidate_count"] == 0


def test_backfill_uses_available_clean_sources_and_preserves_daily_states(
    monkeypatch, tmp_path
):
    available = {"2026-06-10", "2026-06-12", "2026-06-13", "2026-06-14"}
    for source_date in available:
        (tmp_path / f"{source_date}.jsonl").write_text("", encoding="utf-8")

    monkeypatch.setattr(
        mod, "_event_path", lambda source_date: tmp_path / f"{source_date}.jsonl"
    )
    monkeypatch.setattr(mod, "existing_or_gzip_path", lambda path: path)

    def fake_daily(source_date):
        if source_date == "2026-06-10":
            return {
                "status": "no_natural_sample",
                "error": None,
                "rows": [],
                "summary": {
                    "eligible_candidate_count": 2,
                    "guard_blocked_before_execution_count": 2,
                    "execution_started_from_eligible_count": 0,
                    "legacy_execution_terminal_from_eligible_count": 0,
                    "candidate_terminal_from_eligible_count": 0,
                    "terminal_execution_event_from_eligible_count": 0,
                    "terminal_candidate_event_from_eligible_count": 0,
                    "candidate_funnel_by_arm": {"AVG_DOWN": {"eligible": 2}},
                },
            }
        return {
            "status": "instrumentation_gap",
            "error": "counterfactual_event_contract_gap",
            "rows": [],
            "summary": {
                "eligible_candidate_count": 1,
                "execution_started_from_eligible_count": 0,
                "legacy_execution_terminal_from_eligible_count": 0,
                "candidate_terminal_from_eligible_count": 0,
                "terminal_execution_event_from_eligible_count": 0,
                "terminal_candidate_event_from_eligible_count": 0,
                "unresolved_eligible_candidate_count": 1,
                "candidate_funnel_by_arm": {"PYRAMID": {"eligible": 1}},
            },
        }

    monkeypatch.setattr(mod, "build_report", fake_daily)

    report = mod.build_backfill_report(
        "2026-06-14", start_date="2026-06-10", end_date="2026-06-14"
    )

    assert report["source_dates"] == ["2026-06-10", "2026-06-12"]
    assert report["unavailable_source_dates"] == ["2026-06-11"]
    assert report["non_trading_source_dates_excluded"] == [
        "2026-06-13",
        "2026-06-14",
    ]
    assert report["status"] == "instrumentation_gap"
    assert report["summary"]["source_status_counts"] == {
        "no_natural_sample": 1,
        "instrumentation_gap": 1,
    }
    assert report["summary"]["eligible_candidate_count"] == 3
    assert (
        report["source_status_by_date"]["2026-06-10"][
            "legacy_execution_terminal_from_eligible_count"
        ]
        == 0
    )
    assert report["artifact_suffix"] == "2026-06-10_to_2026-06-14"


def test_window_output_path_does_not_overwrite_daily_report(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    report = {
        "date": "2026-06-12",
        "artifact_suffix": "2026-06-10_to_2026-06-12",
        "rows": [],
        "summary": {},
    }

    json_path, md_path = mod.write_outputs(report)

    assert json_path.name.endswith("_2026-06-10_to_2026-06-12.json")
    assert md_path.name.endswith("_2026-06-10_to_2026-06-12.md")


def test_marketable_shadow_with_terminal_control_remains_runtime_blocked(monkeypatch):
    decision_event = _event(
        "scalp_sim_scale_in_counterfactual_started",
        "2026-06-12T10:00:00+09:00",
        sim_record_id="sim-1",
        scale_in_decision_id="decision-1",
        scale_in_arm="PYRAMID",
        execution_arm="MARKETABLE_OBSERVATION",
        decision_time=mod._parse_emitted_at(_event("x", "2026-06-12T10:00:00+09:00")),
        pre_add_buy_price=1000,
        pre_add_buy_qty=10,
        proposed_add_price=1010,
        proposed_add_qty=2,
        proposed_add_notional=2020,
        quote_touched=True,
        runtime_ev_eligible=True,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    terminal = _event(
        "scalp_sim_sell_order_assumed_filled",
        "2026-06-12T10:20:00+09:00",
        sim_record_id="sim-1",
        assumed_fill_price=1050,
    )
    monkeypatch.setattr(
        mod, "_iter_events", lambda target_date: iter([decision_event, terminal])
    )

    report = mod.build_report("2026-06-12")
    row = report["rows"][0]

    assert row["execution_arm"] == "MARKETABLE_OBSERVATION"
    assert row["runtime_ev_eligible"] is True
    assert row["runtime_authority_ready"] is False
    assert (
        row["runtime_authority_block_reason"]
        == "paired_add_lifecycle_replay_not_implemented"
    )
    assert row["final_horizon_complete"] is True


def test_evaluable_rows_do_not_hide_unresolved_eligible_lineage(monkeypatch):
    decision_event = _event(
        "scalp_sim_scale_in_counterfactual_started",
        "2026-06-12T10:00:00+09:00",
        sim_record_id="sim-evaluated",
        scale_in_decision_id="decision-1",
        scale_in_arm="PYRAMID",
        execution_arm="MARKETABLE_OBSERVATION",
        decision_time=mod._parse_emitted_at(_event("x", "2026-06-12T10:00:00+09:00")),
        pre_add_buy_price=1000,
        pre_add_buy_qty=10,
        proposed_add_price=1010,
        proposed_add_qty=2,
        proposed_add_notional=2020,
        quote_touched=True,
        runtime_ev_eligible=True,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )
    orphan_eligible = _event(
        "scalp_sim_scale_in_candidate_funnel",
        "2026-06-12T10:01:00+09:00",
        sim_record_id="sim-orphan",
        scale_in_arm="AVG_DOWN",
        scale_in_candidate_funnel_state="eligible",
    )
    terminal = _event(
        "scalp_sim_sell_order_assumed_filled",
        "2026-06-12T10:20:00+09:00",
        sim_record_id="sim-evaluated",
        assumed_fill_price=1050,
    )
    monkeypatch.setattr(
        mod,
        "_iter_events",
        lambda target_date: iter([decision_event, orphan_eligible, terminal]),
    )

    report = mod.build_report("2026-06-12")

    assert len(report["rows"]) == 1
    assert report["status"] == "instrumentation_gap"
    assert report["error"] == "counterfactual_event_contract_gap"
    assert report["source_quality_gate"] == ("instrumentation_gap_with_evaluable_rows")
    assert report["summary"]["unresolved_eligible_candidate_count"] == 1
