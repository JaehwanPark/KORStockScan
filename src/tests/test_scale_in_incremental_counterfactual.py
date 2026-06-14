from src.engine.lifecycle import scale_in_incremental_counterfactual as mod


def _event(stage, emitted_at, **fields):
    return {"stage": stage, "emitted_at": emitted_at, "fields": fields}


def test_final_price_uses_latest_sell_after_decision():
    events = [
        _event("scalp_sim_sell_order_assumed_filled", "2026-06-12T09:00:00+09:00", assumed_fill_price=900),
        _event("scalp_sim_sell_order_assumed_filled", "2026-06-12T10:10:00+09:00", assumed_fill_price=1050),
        _event("scalp_sim_sell_order_assumed_filled", "2026-06-12T10:20:00+09:00", assumed_fill_price=1100),
    ]
    decision_time = mod._parse_emitted_at(_event("decision", "2026-06-12T10:00:00+09:00"))

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
    assert cohorts["by_quote_touched"]["unfilled"]["horizons"]["final"]["incremental_notional_ev_pct"] == 99.0
    assert cohorts["combined_primary_filled"]["horizons"]["final"]["incremental_notional_ev_pct"] == 2.0


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
        _event("scalp_sim_scale_in_counterfactual_started", "2026-06-12T10:00:00+09:00", actual_order_submitted=False, broker_order_forbidden=True)
    )
    assert not mod._has_sim_counterfactual_authority(
        _event("scalp_sim_scale_in_counterfactual_started", "2026-06-12T10:00:00+09:00", actual_order_submitted=True, broker_order_forbidden=False)
    )
    assert not mod._has_sim_counterfactual_authority(
        _event("scalp_sim_scale_in_counterfactual_started", "2026-06-12T10:00:00+09:00", actual_order_submitted=False)
    )
    assert mod._has_sim_counterfactual_authority(
        _event("scalp_sim_scale_in_order_unfilled", "2026-06-12T10:00:00+09:00", actual_order_submitted=False)
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
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter([canonical, legacy]))

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

    assert report["error"] == "no_counterfactual_events_found"
    assert report["source_quality_gate"] == "pass_with_row_exclusions"
    assert report["summary"]["source_quality_excluded_event_count"] == 1
    assert report["summary"]["source_quality_exclusion_reasons"] == {
        "missing_scale_in_decision_id": 1
    }


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
    monkeypatch.setattr(mod, "_iter_events", lambda target_date: iter([decision_event, terminal]))

    report = mod.build_report("2026-06-12")
    row = report["rows"][0]

    assert row["execution_arm"] == "MARKETABLE_OBSERVATION"
    assert row["runtime_ev_eligible"] is True
    assert row["runtime_authority_ready"] is False
    assert row["runtime_authority_block_reason"] == "paired_add_lifecycle_replay_not_implemented"
    assert row["final_horizon_complete"] is True
