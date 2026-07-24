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
