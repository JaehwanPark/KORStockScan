import json

from src.engine.scalping.adverse_micro_recovery_observer import (
    consume_due_checkpoints,
    create_observation,
    record_next_scanner_loop,
    record_reentry_candidate_decision,
)
from src.engine import sniper_state_handlers as state_handlers
from src.engine.monitoring.rising_missed_intraday_feedback import build_report


def test_adverse_micro_recovery_records_fresh_recheck_and_all_checkpoints():
    state = create_observation(
        observation_id="005930:1",
        stock_code="005930",
        reference_price=10000,
        registered_at=1000.0,
        effective_venue="KRX",
        source_block_reason="rising_missed_tp1_hard_negative_evidence",
    )

    assert record_next_scanner_loop(state, now_ts=1001.0) is True
    record_reentry_candidate_decision(state, allowed=True, now_ts=1002.0)
    samples, completed = consume_due_checkpoints(
        state,
        now_ts=1015.0,
        price=10100,
        price_fresh=True,
        price_source="trusted_ws_0b",
        source_reason="fresh_absolute_ws_0b",
    )

    assert completed is False
    assert [sample["checkpoint_sec"] for sample in samples] == [15]
    assert samples[0]["move_pct"] == 1.0
    assert samples[0]["next_scanner_loop_rechecked"] is True
    assert samples[0]["reentry_candidate_allowed"] is True
    assert samples[0]["recovery_observed"] is True

    samples, completed = consume_due_checkpoints(
        state,
        now_ts=1061.0,
        price=9900,
        price_fresh=True,
        price_source="trusted_ws_0b",
        source_reason="fresh_absolute_ws_0b",
    )

    assert completed is True
    assert [sample["checkpoint_sec"] for sample in samples] == [30, 60]
    assert samples[-1]["max_move_pct"] == 1.0
    assert samples[-1]["min_move_pct"] == -1.0


def test_adverse_micro_recovery_never_treats_stale_price_as_recovery():
    state = create_observation(
        observation_id="005930:2",
        stock_code="005930",
        reference_price=10000,
        registered_at=1000.0,
        effective_venue="KRX",
        source_block_reason="rising_missed_tp1_hard_negative_evidence",
    )

    samples, completed = consume_due_checkpoints(
        state,
        now_ts=1060.0,
        price=10500,
        price_fresh=False,
        price_source="unavailable",
        source_reason="ws_0b_stale",
    )

    assert completed is True
    assert [sample["checkpoint_sec"] for sample in samples] == [15, 30, 60]
    assert all(sample["move_pct"] is None for sample in samples)
    assert all(sample["recovery_observed"] is False for sample in samples)


def test_krx_hard_negative_observer_is_source_only_and_keeps_raw_route_observation(
    monkeypatch,
):
    events = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((code, stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "WS_MANAGER",
        type(
            "WS",
            (),
            {
                "get_latest_data": lambda self, code: {
                    "curr": 10100,
                    "last_realtime_type_ts": {"0B": 1015.0},
                    "last_realtime_type_item": {"0B": "005930"},
                    "last_realtime_type_effective_venue": {"0B": "KRX"},
                    "last_realtime_type_market_route": {"0B": "krx_regular"},
                }
            },
        )(),
    )
    with state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATION_LOCK:
        state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATIONS.clear()

    registered = (
        state_handlers._register_rising_missed_adverse_micro_recovery_observation(
            {"effective_venue": "KRX"},
            "005930",
            {
                "selector_reason": "rising_missed_tp1_hard_negative_evidence",
                "rising_missed_effective_venue": "KRX",
                "rising_missed_tp1_effective_price": 10000,
                "rising_missed_tp1_evaluation_id": "tp1-eval-001",
            },
            now_ts=1000.0,
        )
    )
    stats = state_handlers.observe_rising_missed_adverse_micro_recovery_observations(
        now_ts=1015.0
    )

    assert registered is True
    assert stats["fresh"] == 1
    checkpoint = next(event for event in events if event[1].endswith("checkpoint"))
    assert checkpoint[2]["actual_order_submitted"] is False
    assert checkpoint[2]["broker_order_forbidden"] is True
    assert checkpoint[2]["allowed_runtime_apply"] is False
    assert (
        checkpoint[2]["rising_missed_adverse_micro_recovery_ws_0b_raw_route"]
        == "krx_regular"
    )
    assert (
        checkpoint[2]["rising_missed_adverse_micro_recovery_source_tp1_evaluation_id"]
        == "tp1-eval-001"
    )


def test_krx_hard_negative_observer_deduplicates_active_symbol_horizon(monkeypatch):
    events = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((code, stage, fields)),
    )
    with state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATION_LOCK:
        state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATIONS.clear()
    common = {
        "selector_reason": "rising_missed_tp1_hard_negative_evidence",
        "rising_missed_effective_venue": "KRX",
        "rising_missed_tp1_effective_price": 10000,
    }

    assert state_handlers._register_rising_missed_adverse_micro_recovery_observation(
        {"effective_venue": "KRX"},
        "005930",
        {**common, "rising_missed_tp1_evaluation_id": "one"},
        now_ts=1000.0,
    )
    assert state_handlers._register_rising_missed_adverse_micro_recovery_observation(
        {"effective_venue": "KRX"},
        "005930",
        {**common, "rising_missed_tp1_evaluation_id": "two"},
        now_ts=1005.0,
    )

    with state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATION_LOCK:
        assert (
            len(state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATIONS) == 1
        )
    assert [stage for _, stage, _ in events].count(
        "rising_missed_adverse_micro_recovery_registered"
    ) == 1


def test_adverse_micro_hot_path_updates_are_deferred_without_attribution_loss(
    monkeypatch,
):
    update_queue = state_handlers.queue.Queue(maxsize=4)
    monkeypatch.setattr(
        state_handlers,
        "_RISING_MISSED_ADVERSE_MICRO_RECOVERY_UPDATE_QUEUE",
        update_queue,
    )
    monkeypatch.setattr(
        state_handlers,
        "_RISING_MISSED_ADVERSE_MICRO_RECOVERY_UPDATE_DROPPED",
        0,
    )
    observation = create_observation(
        observation_id="deferred-update",
        stock_code="005930",
        reference_price=10000,
        registered_at=1000.0,
        effective_venue="KRX",
        source_block_reason="rising_missed_tp1_hard_negative_evidence",
    )
    with state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATION_LOCK:
        state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATIONS.clear()
        state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATIONS[
            "deferred-update"
        ] = observation

    state_handlers._record_rising_missed_adverse_micro_next_scanner_loop(
        "005930",
        now_ts=1001.0,
    )
    state_handlers._record_rising_missed_adverse_micro_reentry_candidate(
        "005930",
        allowed=True,
        now_ts=1001.0,
    )
    assert observation["next_scanner_loop_rechecked"] is False
    assert observation["reentry_candidate_allowed"] is False

    stats = state_handlers._drain_rising_missed_adverse_micro_hot_path_updates()

    assert stats == {"queued": 2, "applied": 2, "orphaned": 0, "dropped": 0}
    assert observation["next_scanner_loop_rechecked"] is True
    assert observation["reentry_candidate_allowed"] is True


def test_krx_hard_negative_observer_rejects_integrated_or_unproven_0b(monkeypatch):
    events = []
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((code, stage, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "WS_MANAGER",
        type(
            "WS",
            (),
            {
                "get_latest_data": lambda self, code: {
                    "curr": 10100,
                    "last_realtime_type_ts": {"0B": 1015.0},
                    "last_realtime_type_item": {"0B": "005930_AL"},
                    "last_realtime_type_effective_venue": {"0B": ""},
                    "last_realtime_type_market_route": {"0B": "krx_nxt_integrated"},
                }
            },
        )(),
    )
    with state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATION_LOCK:
        state_handlers._RISING_MISSED_ADVERSE_MICRO_RECOVERY_OBSERVATIONS.clear()
    assert state_handlers._register_rising_missed_adverse_micro_recovery_observation(
        {"effective_venue": "KRX"},
        "005930",
        {
            "selector_reason": "rising_missed_tp1_hard_negative_evidence",
            "rising_missed_effective_venue": "KRX",
            "rising_missed_tp1_effective_price": 10000,
        },
        now_ts=1000.0,
    )

    stats = state_handlers.observe_rising_missed_adverse_micro_recovery_observations(
        now_ts=1015.0
    )

    assert stats["fresh"] == 0
    assert stats["source_gap"] == 1
    checkpoint = next(event for event in events if event[1].endswith("checkpoint"))
    assert checkpoint[2]["rising_missed_adverse_micro_recovery_price_fresh"] is False
    assert (
        checkpoint[2]["rising_missed_adverse_micro_recovery_source_reason"]
        == "canonical_krx_0b_provenance_missing"
    )


def test_stale_backoff_observation_keeps_integrated_raw_route_out_of_venue_blocking():
    fields = state_handlers._scanner_stale_backoff_observation_fields(
        {"effective_venue": "KRX", "venue": "KRX"},
        {
            "last_realtime_type_market_route": {
                "0B": "krx_nxt_integrated",
                "0D": "krx_regular",
            },
        },
        fast_precheck_reason="stale_ws_snapshot",
    )

    assert fields["scanner_stale_backoff_observed"] is True
    assert fields["scanner_stale_backoff_raw_integrated_route_seen"] is True
    assert fields["scanner_stale_backoff_venue_provenance_blocked"] is False
    assert fields["scanner_stale_backoff_signed_tape_state"] == "not_available"


def test_intraday_feedback_reports_krx_adverse_micro_recovery_separately(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-28.jsonl"
    rows = [
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "rising_missed_adverse_micro_recovery_registered",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "emitted_at": "2026-07-28T09:00:00+09:00",
            "fields": {
                "effective_venue": "KRX",
                "rising_missed_adverse_micro_recovery_observation_id": "005930:1",
                "rising_missed_adverse_micro_recovery_source_tp1_evaluation_id": (
                    "tp1-eval-001"
                ),
            },
        },
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "rising_missed_adverse_micro_recovery_checkpoint",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "emitted_at": "2026-07-28T09:00:15+09:00",
            "fields": {
                "effective_venue": "KRX",
                "rising_missed_adverse_micro_recovery_observation_id": "005930:1",
                "rising_missed_adverse_micro_recovery_checkpoint_sec": 15,
                "rising_missed_adverse_micro_recovery_price_fresh": True,
                "rising_missed_adverse_micro_recovery_move_pct": 0.55,
                "rising_missed_adverse_micro_recovery_detected": True,
                "rising_missed_adverse_micro_recovery_source_reason": "fresh_absolute_ws_0b",
                "rising_missed_adverse_micro_recovery_ws_0b_raw_route": "krx_nxt_integrated",
            },
        },
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = build_report(
        "2026-07-28", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert (
        report["summary"]["rising_missed_adverse_micro_recovery_observation_count"] == 1
    )
    assert report["summary"][
        "rising_missed_adverse_micro_recovery_checkpoint_counts"
    ] == [{"checkpoint_sec": "15", "count": 1}]
    assert report["rising_missed_adverse_micro_recovery_rows"][1]["raw_0b_route"] == (
        "krx_nxt_integrated"
    )
    assert (
        report["rising_missed_adverse_micro_recovery_rows"][0][
            "source_tp1_evaluation_id"
        ]
        == "tp1-eval-001"
    )
    assert report["summary"][
        "rising_missed_adverse_micro_recovery_source_quality_counts"
    ] == [{"source_reason": "fresh_absolute_ws_0b", "count": 1}]
