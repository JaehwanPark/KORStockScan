from src.engine.scalping.smoothing_source_only_path_journal import (
    HORIZONS_SEC,
    SmoothingSourceOnlyPathObserver,
    arm_source_only_path,
    observe_source_only_paths,
)


def _arm(state=None):
    return arm_source_only_path(
        state,
        family="soft_stop_whipsaw_confirmation",
        position_key="record:7",
        trace_id="trace-7",
        snapshot_id="snapshot-7",
        alternative_action="HOLD",
        control_action="EXIT",
        now_ts=1000.0,
        effective_price=10_000,
        effective_profit_rate=-1.5,
        reference_buy_price=10_100,
        effective_price_source="ws",
        effective_price_quality="single_source",
        runtime_family_enabled=False,
        alternative_executed=False,
        source_reason="runtime_disabled",
    )


def test_source_only_journal_emits_exact_horizons_without_runtime_authority():
    state, armed = _arm()

    assert armed["stage"] == "smoothing_source_only_path_armed"
    assert armed["fields"]["runtime_effect"] is False
    assert armed["fields"]["allowed_runtime_apply"] is False
    assert armed["fields"]["broker_order_forbidden"] is True
    assert armed["fields"]["exact_lineage_status"] == "source_exact"
    assert armed["fields"]["reference_buy_price"] == 10_100

    emitted = []
    for horizon in HORIZONS_SEC:
        state, events = observe_source_only_paths(
            state,
            position_key="record:7",
            now_ts=1000.0 + horizon,
            effective_price=10_000 + horizon,
            effective_profit_rate=-1.5 + horizon / 100.0,
            effective_price_source="ws",
            effective_price_quality="single_source",
            hard_breach=False,
            emergency_breach=False,
        )
        emitted.extend(events)

    horizon_events = [
        event
        for event in emitted
        if event["stage"] == "smoothing_source_only_path_horizon"
    ]
    assert [event["fields"]["horizon_sec"] for event in horizon_events] == list(
        HORIZONS_SEC
    )
    assert all(
        event["fields"]["horizon_status"] == "observed" for event in horizon_events
    )
    assert horizon_events[-1]["fields"]["path_mfe_profit_rate"] == -0.6
    assert horizon_events[-1]["fields"]["path_mae_profit_rate"] == -1.5
    assert state["arms"] == {}
    assert emitted[-1]["fields"]["close_reason"] == "horizons_complete"


def test_source_only_journal_deduplicates_arm_and_closes_on_emergency():
    state, armed = _arm()
    duplicate_state, duplicate = _arm(state)

    assert armed is not None
    assert duplicate is None
    assert len(duplicate_state["arms"]) == 1

    closed_state, events = observe_source_only_paths(
        duplicate_state,
        position_key="record:7",
        now_ts=1005.0,
        effective_price=9_800,
        effective_profit_rate=-2.1,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=True,
    )

    assert closed_state["arms"] == {}
    assert [event["stage"] for event in events] == ["smoothing_source_only_path_closed"]
    assert events[0]["fields"]["close_reason"] == "emergency_breach"
    assert events[0]["fields"]["terminal_effective_price"] == 9_800
    assert events[0]["fields"]["terminal_effective_profit_rate"] == -2.1
    assert events[0]["fields"]["terminal_effective_price_quality"] == "single_source"
    assert events[0]["fields"]["path_mae_profit_rate"] == -2.1


def test_source_only_journal_keeps_oldest_arm_across_new_source_snapshots():
    state, armed = _arm()
    state, replacement = arm_source_only_path(
        state,
        family="soft_stop_whipsaw_confirmation",
        position_key="record:7",
        trace_id="trace-new",
        snapshot_id="snapshot-new",
        alternative_action="HOLD",
        control_action="EXIT",
        now_ts=1002.0,
        effective_price=10_020,
        effective_profit_rate=-1.3,
        reference_buy_price=10_100,
        effective_price_source="ws",
        effective_price_quality="single_source",
        runtime_family_enabled=False,
        alternative_executed=False,
        source_reason="new_tick_snapshot",
    )

    assert replacement is None
    assert len(state["arms"]) == 1
    active = next(iter(state["arms"].values()))
    assert active["arm_id"] == armed["fields"]["journal_arm_id"]
    assert active["started_at"] == 1000.0


def test_source_only_journal_marks_missing_source_lineage_and_deduplicates_it():
    kwargs = {
        "family": "holding_flow_ofi_smoothing",
        "position_key": "record:8",
        "trace_id": "-",
        "snapshot_id": None,
        "alternative_action": "EXIT",
        "control_action": "HOLD",
        "now_ts": 1000.0,
        "effective_price": 10_000,
        "effective_profit_rate": -0.5,
        "reference_buy_price": 10_100,
        "effective_price_source": "ws",
        "effective_price_quality": "single_source",
        "runtime_family_enabled": False,
        "alternative_executed": False,
        "source_reason": "runtime_disabled",
    }

    state, armed = arm_source_only_path(None, **kwargs)
    duplicate_state, duplicate = arm_source_only_path(state, **kwargs)

    assert armed["fields"]["exact_lineage_status"] == "journal_native_only"
    assert armed["fields"]["journal_trace_id"].startswith("journal-trace:")
    assert duplicate is None
    assert len(duplicate_state["arms"]) == 1


def test_source_only_journal_rejects_missing_reference_buy_price():
    state, armed = arm_source_only_path(
        None,
        family="holding_flow_ofi_smoothing",
        position_key="record:8",
        trace_id="trace-8",
        snapshot_id="snapshot-8",
        alternative_action="EXIT",
        control_action="HOLD",
        now_ts=1000.0,
        effective_price=10_000,
        effective_profit_rate=-0.5,
        reference_buy_price=0,
        effective_price_source="ws",
        effective_price_quality="single_source",
        runtime_family_enabled=False,
        alternative_executed=False,
        source_reason="runtime_disabled",
    )

    assert armed is None
    assert state["arms"] == {}


def test_source_only_journal_keeps_full_path_excursions_without_tick_list():
    state, _armed = _arm()
    for index in range(150):
        state, events = observe_source_only_paths(
            state,
            position_key="record:7",
            now_ts=1000.0 + (index + 1) * 0.05,
            effective_price=10_100 if index == 0 else 9_950,
            effective_profit_rate=2.0 if index == 0 else -1.0,
            effective_price_source="ws",
            effective_price_quality="single_source",
            hard_breach=False,
            emergency_breach=False,
        )
        assert events == []

    state, events = observe_source_only_paths(
        state,
        position_key="record:7",
        now_ts=1010.0,
        effective_price=10_000,
        effective_profit_rate=0.0,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=False,
    )

    horizon = next(
        event
        for event in events
        if event["stage"] == "smoothing_source_only_path_horizon"
    )
    assert horizon["fields"]["path_mfe_profit_rate"] == 2.0
    assert horizon["fields"]["path_mae_profit_rate"] == -1.5
    active_arm = next(iter(state["arms"].values()))
    assert "samples" not in active_arm


def test_source_only_journal_expires_late_horizon_instead_of_relabeling_it_exact():
    state, _armed = _arm()

    _state, events = observe_source_only_paths(
        state,
        position_key="record:7",
        now_ts=1013.0,
        effective_price=10_000,
        effective_profit_rate=-1.0,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=False,
    )

    horizon = next(
        event
        for event in events
        if event["stage"] == "smoothing_source_only_path_horizon"
    )
    assert horizon["fields"]["horizon_sec"] == 10
    assert horizon["fields"]["observation_lag_sec"] == 3.0
    assert horizon["fields"]["horizon_status"] == "expired_observation_gap"


def test_source_only_journal_marks_missing_horizon_price_without_zero_ev():
    state, _armed = _arm()

    state, events = observe_source_only_paths(
        state,
        position_key="record:7",
        now_ts=1010.0,
        effective_price=0,
        effective_profit_rate=0.0,
        effective_price_source="none",
        effective_price_quality="missing",
        hard_breach=False,
        emergency_breach=False,
        observation_phase="post_sell_non_revive",
    )

    horizon = next(
        event
        for event in events
        if event["stage"] == "smoothing_source_only_path_horizon"
    )
    assert horizon["fields"]["horizon_status"] == "expired_observation_gap"
    assert horizon["fields"]["effective_price"] == "not_available"
    assert horizon["fields"]["effective_profit_rate"] == "not_available"
    assert horizon["fields"]["effective_price_source"] == (
        "not_available:expired_observation_gap"
    )
    assert horizon["fields"]["effective_price_observation_state"] == (
        "not_available:expired_observation_gap"
    )
    assert state["arms"]


def test_source_only_journal_tolerates_transient_invalid_tick_with_fresh_cadence():
    state, _armed = _arm()
    for second in range(1, 11):
        if second == 5:
            state, invalid_events = observe_source_only_paths(
                state,
                position_key="record:7",
                now_ts=1004.5,
                effective_price=9_990,
                effective_profit_rate=-1.1,
                effective_price_source="ws",
                effective_price_quality="stale",
                hard_breach=False,
                emergency_breach=False,
            )
            assert invalid_events == []
        state, events = observe_source_only_paths(
            state,
            position_key="record:7",
            now_ts=1000.0 + second,
            effective_price=10_000 + second,
            effective_profit_rate=-1.5 + second / 100.0,
            effective_price_source="ws",
            effective_price_quality="single_source",
            hard_breach=False,
            emergency_breach=False,
        )

    horizon = next(
        event
        for event in events
        if event["stage"] == "smoothing_source_only_path_horizon"
    )
    assert horizon["fields"]["path_quality_contract_version"] == (
        "fresh_observation_gap_v2"
    )
    assert horizon["fields"]["path_price_quality_invalid_sample_count"] == 1
    assert horizon["fields"]["path_max_valid_observation_gap_sec"] == 1.0
    assert horizon["fields"]["path_max_allowed_observation_gap_sec"] == 2.0


def test_source_only_journal_exposes_true_valid_observation_gap():
    state, _armed = _arm()
    state, _events = observe_source_only_paths(
        state,
        position_key="record:7",
        now_ts=1001.0,
        effective_price=10_001,
        effective_profit_rate=-1.49,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=False,
    )
    _state, events = observe_source_only_paths(
        state,
        position_key="record:7",
        now_ts=1010.0,
        effective_price=10_010,
        effective_profit_rate=-1.4,
        effective_price_source="ws",
        effective_price_quality="single_source",
        hard_breach=False,
        emergency_breach=False,
    )

    horizon = next(
        event
        for event in events
        if event["stage"] == "smoothing_source_only_path_horizon"
    )
    assert horizon["fields"]["path_max_valid_observation_gap_sec"] == 9.0


def test_source_only_cadence_observer_forwards_clock_and_fails_open():
    observed = []
    errors = []
    observer = SmoothingSourceOnlyPathObserver(
        observer=lambda *, now_ts: observed.append(now_ts) or {"observed": 1},
        error_handler=errors.append,
    )

    assert observer.run_once(now_ts=1234.5) == {"observed": 1}
    assert observed == [1234.5]
    assert errors == []

    failing = SmoothingSourceOnlyPathObserver(
        observer=lambda **_kwargs: (_ for _ in ()).throw(ValueError("broken")),
        error_handler=errors.append,
    )
    assert failing.run_once(now_ts=1235.0) is None
    assert errors == ["broken"]
