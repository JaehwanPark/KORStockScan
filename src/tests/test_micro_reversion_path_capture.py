import gzip
from dataclasses import replace
import json
from pathlib import Path

from src.engine.scalping.micro_reversion.contracts import (
    CoverageTier,
    ShockEvent,
)
from src.engine.scalping.micro_reversion.multi_horizon import MultiHorizonShockEvent
from src.engine.scalping.micro_reversion.observation_adapter import (
    RawMarketObservation,
)
from src.engine.scalping.micro_reversion.path_capture import (
    ParentWavePathCoalescer,
    PathPhase,
    PreEventRingBuffer,
    append_path_event_references,
    load_path_event_references,
)

BASE_MS = 1_775_779_200_000


def _envelope(sequence: int, second: int) -> RawMarketObservation:
    return RawMarketObservation(
        symbol="000001",
        venue="KRX",
        session_bucket="KRX_REGULAR",
        exchange_timestamp=f"2026-04-10T09:00:{second:02d}+09:00",
        local_receive_timestamp=f"2026-04-10T09:00:{second:02d}.010+09:00",
        source_sequence=sequence,
        sequence_epoch=1,
        series_sequence=sequence,
        realtime_type="0B",
        manual_control_exclusion_checked=True,
        manual_control_excluded=False,
        manual_control_exclusion_version=1,
        manual_control_exclusion_checked_at="2026-04-10T09:00:00+09:00",
        trade_price=10_000 - sequence,
        trade_qty=10,
    )


def _other_symbol_envelope(sequence: int, second: int) -> RawMarketObservation:
    return replace(_envelope(sequence, second), symbol="000002")


def _event(event_id: str, sequence: int, horizon: int) -> MultiHorizonShockEvent:
    event_ms = BASE_MS + 25_000
    shock = ShockEvent(
        event_id=event_id,
        symbol="000001",
        venue="KRX",
        session_bucket="KRX_REGULAR",
        trade_date="2026-04-10",
        detected_at_ms=event_ms,
        reference_at_ms=event_ms - horizon,
        reference_price=10_000,
        shock_price=9_950,
        shock_return_bps=-50,
        return_robust_z=-4,
        acceleration_robust_z=-3,
        micro_vwap=None,
        coverage_tier=CoverageTier.PRICE_PATH,
        source_quality_status="price_path_only",
    )
    return MultiHorizonShockEvent(
        parent_wave_id="wave-1",
        shock_event_id=event_id,
        shock_horizon_ms=horizon,
        event_sequence_in_wave=sequence,
        rearm_reason="initial_shock" if sequence == 1 else "same_parent_wave",
        event=shock,
    )


def test_ring_tracks_gaps_duplicates_and_out_of_order() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000, max_points_per_series=10)
    assert ring.add(_envelope(1, 1)) is True
    assert ring.add(_envelope(3, 3)) is True
    assert ring.add(_envelope(3, 4)) is False
    assert ring.add(_envelope(2, 5)) is False

    accepted, duplicates, out_of_order, gaps, _evicted = ring.counters()
    assert (accepted, duplicates, out_of_order, gaps) == (2, 1, 1, 1)


def test_parent_wave_creates_one_segment_with_many_event_references() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000, max_points_per_series=100)
    for sequence, second in enumerate((5, 10, 20), start=1):
        assert ring.add(_envelope(sequence, second))
    coalescer = ParentWavePathCoalescer(ring)

    first = coalescer.register_event(
        _event("evt-1", 1, 1_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )
    second = coalescer.register_event(
        _event("evt-2", 2, 3_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )

    assert first.segment_created is True
    assert second.segment_created is False
    assert first.path_segment_id == second.path_segment_id
    assert len(first.pre_event_envelopes) == 3
    assert second.pre_event_envelopes == ()
    assert [ref.shock_event_id for ref in coalescer.references()] == [
        "evt-1",
        "evt-2",
    ]
    points = coalescer.points_from_registration(first, detector_version="mh-v1")
    assert len(points) == 3
    assert all(point.path_phase == PathPhase.PRE_EVENT.value for point in points)
    assert all(point.parent_wave_id == "wave-1" for point in points)

    quality = coalescer.quality_snapshot()
    assert quality.created_segment_count == 1
    assert quality.coalesced_event_reference_count == 1


def test_active_segment_matching_is_symbol_scoped_and_splits_post_phase() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000)
    coalescer = ParentWavePathCoalescer(ring, active_event_ms=20_000)
    registration = coalescer.register_event(
        _event("evt-1", 1, 1_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )

    active_envelope = _envelope(1, 30)
    matches = coalescer.active_segments_for(active_envelope)
    assert len(matches) == 1
    parent_wave_id, state = matches[0]
    active_point = coalescer.point_for_active_envelope(
        active_envelope,
        parent_wave_id=parent_wave_id,
        state=state,
        detector_version="mh-v1",
    )
    assert active_point.path_phase == PathPhase.ACTIVE_EVENT.value
    assert active_point.capture_started_at == registration.capture_started_at

    assert coalescer.active_segments_for(_other_symbol_envelope(2, 31)) == ()
    post_envelope = _envelope(3, 50)
    parent_wave_id, state = coalescer.active_segments_for(post_envelope)[0]
    post_point = coalescer.point_for_active_envelope(
        post_envelope,
        parent_wave_id=parent_wave_id,
        state=state,
        detector_version="mh-v1",
    )
    assert post_point.path_phase == PathPhase.POST_EVENT.value


def test_event_references_append_with_observation_only_authority(
    tmp_path: Path,
) -> None:
    coalescer = ParentWavePathCoalescer(PreEventRingBuffer(max_age_ms=30_000))
    coalescer.register_event(
        _event("evt-1", 1, 1_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )
    coalescer.register_event(
        _event("evt-2", 2, 3_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )

    target = tmp_path / "references.jsonl"
    append_path_event_references(target, coalescer.references())
    rows = [json.loads(line) for line in target.read_text().splitlines()]

    assert [row["shock_event_id"] for row in rows] == ["evt-1", "evt-2"]
    assert all(row["trading_runtime_effect"] is False for row in rows)


def test_manual_exclusion_drop_removes_ring_and_open_segment_state() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000)
    envelope = _envelope(1, 1)
    assert ring.add(envelope) is True
    coalescer = ParentWavePathCoalescer(ring)
    coalescer.register_event(
        _event("evt-drop", 1, 1_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )

    assert ring.drop_symbol("000001") == 1
    assert coalescer.drop_symbol("000001") == 1
    assert coalescer.active_segments_for(_envelope(2, 2)) == ()


def test_reference_loader_supports_post_session_gzip(tmp_path: Path) -> None:
    target = tmp_path / "market_stream_event_references.jsonl"
    compressed = target.with_suffix(".jsonl.gz")
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write('{"schema":"reference-test"}\n')

    assert load_path_event_references(target) == ({"schema": "reference-test"},)
