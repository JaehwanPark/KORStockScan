from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.scalping.scanner_scheduler_replay import replay_scanner_events

KST = ZoneInfo("Asia/Seoul")


def _event(stage, emitted_at, code="005930", **fields):
    return {
        "stage": stage,
        "stock_code": code,
        "emitted_at": emitted_at,
        "fields": fields,
    }


def test_replay_keeps_exact_generation_and_separates_venues():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:01",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-1",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="KRX",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:03",
            scanner_promotion_id="PROMO-1",
        ),
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:01:01",
            code="000660",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-2",
            scanner_promotion_emitted_epoch=promotion_epoch + 60,
            effective_venue="NXT",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:01:05",
            code="000660",
            scanner_promotion_id="PROMO-2",
        ),
    ]

    replay = replay_scanner_events(events)

    assert replay["valid_generation_count"] == 2
    assert replay["venues"]["KRX"]["attach_to_first_precheck_p95_sec"] == 2.0
    assert replay["venues"]["NXT"]["attach_to_first_precheck_p95_sec"] == 4.0
    assert replay["venues"]["PREMARKET_KRX_LIKE"]["valid_generation_count"] == 0


def test_replay_accepts_canonical_db_poll_recovery_attach():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:01",
            runtime_target_attach_outcome="db_poll_attached",
            runtime_target_attach_reason=(
                "eventbus_attach_missing_recovered_from_database_poll"
            ),
            scanner_promotion_id="PROMO-DB-POLL",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="KRX",
            venue_resolution=(
                "consistent_explicit:payload.effective_venue,"
                "payload.venue,target.effective_venue"
            ),
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:04",
            scanner_promotion_id="PROMO-DB-POLL",
        ),
    ]

    replay = replay_scanner_events(events)

    assert replay["valid_generation_count"] == 1
    assert replay["venues"]["KRX"]["attach_to_first_precheck_p95_sec"] == 3.0
    assert "attach_not_applied" not in replay["exclusions"]


def test_replay_prefers_exact_runtime_handoff_over_event_sink_timestamp():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:09",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-HANDOFF",
            scanner_promotion_emitted_epoch=promotion_epoch,
            scanner_runtime_handoff_epoch=promotion_epoch + 1.0,
            scanner_runtime_handoff_promotion_id="PROMO-HANDOFF",
            scanner_runtime_instance_id="scanner-runtime-test",
            scanner_attach_provenance_version="scanner_runtime_handoff_v1",
            effective_venue="KRX",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:03",
            scanner_promotion_id="PROMO-HANDOFF",
        ),
    ]

    replay = replay_scanner_events(events)

    assert replay["valid_generation_count"] == 1
    assert replay["venues"]["KRX"]["promotion_to_attach_p95_sec"] == 1.0
    assert replay["venues"]["KRX"]["attach_to_first_precheck_p95_sec"] == 2.0
    assert replay["attach_epoch_source_counts"] == {"exact_runtime_handoff": 1}


def test_replay_prefers_scheduler_action_timestamps_over_async_sink_time():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    attach_epoch = promotion_epoch + 1.1
    dispatch_epoch = promotion_epoch + 1.4
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:01",
            runtime_target_attach_outcome="db_poll_attached",
            scanner_promotion_id="PROMO-ACTION-TIME",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="KRX",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_scheduler_work_dispatched",
            "2026-07-24T09:00:30",
            scanner_promotion_id="PROMO-ACTION-TIME",
            scheduler_version="scanner_deadline_scheduler_v1",
            scheduler_action="dispatch",
            scanner_scheduler_lane="fast_precheck",
            scanner_scheduler_precheck_phase="initial",
            scanner_attach_epoch=attach_epoch,
            scanner_scheduler_dispatched_epoch=dispatch_epoch,
            effective_venue="KRX",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:31",
            scanner_promotion_id="PROMO-ACTION-TIME",
            fast_precheck_seen_epoch=dispatch_epoch + 0.1,
        ),
    ]

    replay = replay_scanner_events(events)

    assert replay["valid_generation_count"] == 1
    assert replay["venues"]["KRX"]["promotion_to_attach_p95_sec"] == 1.1
    assert replay["venues"]["KRX"]["attach_to_first_precheck_p95_sec"] == 0.3
    assert "precheck_without_canonical_attach" not in replay["exclusions"]


def test_replay_excludes_missing_venue_and_superseded_generation():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:01",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-UNKNOWN",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="UNKNOWN",
            venue_resolution="missing_tradable_explicit_venue",
        ),
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:02",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-OLD",
            scanner_promotion_emitted_epoch=promotion_epoch + 1,
            effective_venue="KRX",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:03",
            runtime_target_attach_outcome="refreshed",
            scanner_promotion_id="PROMO-NEW",
            scanner_promotion_emitted_epoch=promotion_epoch + 2,
            effective_venue="KRX",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:04",
            scanner_promotion_id="PROMO-OLD",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:05",
            scanner_promotion_id="PROMO-NEW",
        ),
    ]

    replay = replay_scanner_events(events)

    assert replay["valid_generation_count"] == 1
    assert replay["exclusions"]["attach_explicit_venue_missing"] == 1
    assert replay["exclusions"]["superseded_before_precheck"] == 1
    assert replay["exclusions"]["precheck_without_canonical_attach"] == 1


def test_replay_rejects_precheck_venue_conflict():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:01",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-1",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="KRX",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:03",
            scanner_promotion_id="PROMO-1",
            effective_venue="NXT",
        ),
    ]

    replay = replay_scanner_events(events)

    assert replay["valid_generation_count"] == 0
    assert replay["exclusions"]["precheck_venue_conflict"] == 1


def test_replay_separates_attach_source_ready_and_heavy_eval_handoff():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    realtime_epoch = promotion_epoch + 1.2
    heavy_eval_epoch = promotion_epoch + 8.2
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:00.200000",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-SOURCE-READY",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="NXT",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:08",
            scanner_promotion_id="PROMO-SOURCE-READY",
            effective_venue="NXT",
            scanner_entry_realtime_state="received",
            scanner_first_entry_realtime_epoch=realtime_epoch,
            scanner_first_entry_realtime_type="strength_history",
        ),
        _event(
            "scalping_scanner_heavy_eval_lag",
            "2026-07-24T09:00:08.200000",
            scanner_promotion_id="PROMO-SOURCE-READY",
            effective_venue="NXT",
            heavy_eval_started_epoch=heavy_eval_epoch,
        ),
    ]

    replay = replay_scanner_events(events)
    source_ready = replay["source_ready_handoff"]
    nxt = source_ready["venues"]["NXT"]

    assert source_ready["runtime_effect"] is False
    assert source_ready["external_wait_excluded_from_internal_root_cause"] is True
    assert source_ready["internal_latency_anchor"] == (
        "first_post_attach_entry_realtime"
    )
    assert source_ready["external_wait_owner"] == (
        "external_or_subscription_state_first_post_attach_entry_realtime"
    )
    assert (
        source_ready["external_wait_causal_attribution"]
        == "not_assigned_without_server_subscription_ack"
    )
    assert source_ready["valid_generation_count"] == 1
    assert nxt["attach_to_first_entry_realtime_p95_sec"] == 1.0
    assert nxt["first_entry_realtime_to_heavy_eval_p95_sec"] == 7.0
    assert nxt["first_entry_realtime_to_heavy_eval_max_sec"] == 7.0
    assert source_ready["samples"][0]["attach_to_first_entry_realtime_sec"] == 1.0
    assert source_ready["samples"][0]["first_entry_realtime_to_heavy_eval_sec"] == 7.0


def test_source_ready_handoff_excludes_superseded_generation():
    promotion_epoch = datetime(2026, 7, 24, 9, 0, 0, tzinfo=KST).timestamp()
    events = [
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:00.200000",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-OLD",
            scanner_promotion_emitted_epoch=promotion_epoch,
            effective_venue="NXT",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            "2026-07-24T09:00:00.800000",
            scanner_promotion_id="PROMO-OLD",
            effective_venue="NXT",
            scanner_entry_realtime_state="received",
            scanner_first_entry_realtime_epoch=promotion_epoch + 0.7,
            scanner_first_entry_realtime_type="strength_history",
        ),
        _event(
            "scalping_scanner_runtime_target_attach",
            "2026-07-24T09:00:01",
            runtime_target_attach_outcome="attached",
            scanner_promotion_id="PROMO-NEW",
            scanner_promotion_emitted_epoch=promotion_epoch + 0.9,
            effective_venue="NXT",
            venue_resolution="consistent_explicit:payload.effective_venue",
        ),
        _event(
            "scalping_scanner_heavy_eval_lag",
            "2026-07-24T09:00:01.200000",
            scanner_promotion_id="PROMO-OLD",
            effective_venue="NXT",
            heavy_eval_started_epoch=promotion_epoch + 1.2,
        ),
    ]

    source_ready = replay_scanner_events(events)["source_ready_handoff"]

    assert source_ready["valid_generation_count"] == 0
    assert (
        source_ready["exclusions"][
            "scalping_scanner_heavy_eval_lag_superseded_generation"
        ]
        == 1
    )
    assert source_ready["exclusions"]["source_ready_superseded_before_heavy_eval"] == 1
