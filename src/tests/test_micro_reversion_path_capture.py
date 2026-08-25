import errno
import gzip
from dataclasses import replace
import json
from pathlib import Path
import threading

import pytest

from src.engine.scalping.micro_reversion import path_capture as path_capture_module
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
    PathEnvelopeOrderStatus,
    PathEventReference,
    PathPhase,
    PreEventRingBuffer,
    append_path_event_references,
    load_path_event_references,
)
from src.engine.scalping.micro_reversion.path_journal import (
    partition_maintenance_lock,
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


def _reference(event_id: str, sequence: int = 1) -> PathEventReference:
    coalescer = ParentWavePathCoalescer(PreEventRingBuffer(max_age_ms=30_000))
    registration = coalescer.register_event(
        _event(event_id, sequence, 1_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )
    return registration.event_reference


def test_ring_tracks_gaps_duplicates_and_out_of_order() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000, max_points_per_series=10)
    assert ring.add(_envelope(1, 1)) is True
    assert ring.add(_envelope(3, 3)) is True
    assert ring.add(_envelope(3, 4)) is False
    assert ring.add(_envelope(2, 5)) is False

    (
        accepted,
        duplicates,
        out_of_order,
        timestamp_regressions,
        timestamp_regressions_quarantined,
        timestamp_regressions_exceeded,
        timestamp_regression_max_ms,
        local_receive_timestamp_regressions,
        local_receive_timestamp_regression_max_ms,
        gaps,
        _evicted,
    ) = ring.counters()
    assert (accepted, duplicates, out_of_order, gaps) == (2, 1, 1, 1)
    assert (
        timestamp_regressions,
        timestamp_regressions_quarantined,
        timestamp_regressions_exceeded,
        timestamp_regression_max_ms,
        local_receive_timestamp_regressions,
        local_receive_timestamp_regression_max_ms,
    ) == (0, 0, 0, 0, 0, 0)


def test_ring_quarantines_bounded_exchange_timestamp_regression() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000, max_points_per_series=10)
    first = _envelope(1, 54)
    regressed = replace(
        _envelope(2, 53),
        local_receive_timestamp="2026-04-10T09:00:54.125+09:00",
    )
    recovered = replace(
        _envelope(3, 54),
        local_receive_timestamp="2026-04-10T09:00:54.130+09:00",
    )

    assert ring.add(first) is True
    assert (
        ring.order_status(regressed)
        is PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_QUARANTINED
    )
    assert ring.add(regressed) is False
    assert ring.add(recovered) is True

    quality = ParentWavePathCoalescer(ring).quality_snapshot()
    assert quality.accepted_envelope_count == 2
    assert quality.out_of_order_sequence_count == 0
    assert quality.sequence_gap_count == 0
    assert quality.exchange_timestamp_regression_count == 1
    assert quality.exchange_timestamp_regression_quarantined_count == 1
    assert quality.exchange_timestamp_regression_exceeded_count == 0
    assert quality.exchange_timestamp_regression_max_ms == 1_000


def test_ring_escalates_exchange_timestamp_regression_beyond_one_second() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000, max_points_per_series=10)
    first = _envelope(1, 54)
    regressed = replace(
        _envelope(2, 52),
        local_receive_timestamp="2026-04-10T09:00:54.125+09:00",
    )

    assert ring.add(first) is True
    assert (
        ring.order_status(regressed)
        is PathEnvelopeOrderStatus.EXCHANGE_TIMESTAMP_REGRESSION_EXCEEDED
    )
    assert ring.add(regressed) is False

    quality = ParentWavePathCoalescer(ring).quality_snapshot()
    assert quality.accepted_envelope_count == 1
    assert quality.exchange_timestamp_regression_count == 1
    assert quality.exchange_timestamp_regression_quarantined_count == 0
    assert quality.exchange_timestamp_regression_exceeded_count == 1
    assert quality.exchange_timestamp_regression_max_ms == 2_000


def test_ring_keeps_local_receive_timestamp_regression_as_hard_failure() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000, max_points_per_series=10)
    first = replace(
        _envelope(1, 54),
        local_receive_timestamp="2026-04-10T09:00:54.125+09:00",
    )
    regressed = replace(
        _envelope(2, 53),
        local_receive_timestamp="2026-04-10T09:00:54.120+09:00",
    )

    assert ring.add(first) is True
    assert (
        ring.order_status(regressed)
        is PathEnvelopeOrderStatus.LOCAL_RECEIVE_TIMESTAMP_REGRESSION
    )
    assert ring.add(regressed) is False

    quality = ParentWavePathCoalescer(ring).quality_snapshot()
    assert quality.local_receive_timestamp_regression_count == 1
    assert quality.local_receive_timestamp_regression_max_ms == 5
    assert quality.exchange_timestamp_regression_count == 0


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


def test_transport_epoch_reset_clears_ring_ordering_and_open_paths() -> None:
    ring = PreEventRingBuffer(max_age_ms=30_000)
    first = _envelope(1, 1)
    assert ring.add(first) is True
    coalescer = ParentWavePathCoalescer(ring)
    coalescer.register_event(
        _event("evt-reconnect", 1, 1_000),
        sequence_epoch=1,
        event_exchange_timestamp="2026-04-10T09:00:25+09:00",
    )
    assert len(coalescer.active_segments_for(_envelope(2, 30))) == 1

    assert ring.reset_transport_epoch() == 1
    assert coalescer.reset_transport_epoch() == 1

    assert (
        ring.snapshot_before(
            symbol="000001",
            venue="KRX",
            session_bucket="KRX_REGULAR",
            event_detected_at_ms=BASE_MS + 30_000,
        )
        == ()
    )
    assert coalescer.active_segments_for(_envelope(2, 30)) == ()
    assert ring.add(replace(first, sequence_epoch=2)) is True


def test_reference_loader_supports_post_session_gzip(tmp_path: Path) -> None:
    target = tmp_path / "market_stream_event_references.jsonl"
    compressed = target.with_suffix(".jsonl.gz")
    with gzip.open(compressed, "wt", encoding="utf-8") as handle:
        handle.write('{"schema":"reference-test"}\n')

    assert load_path_event_references(target) == ({"schema": "reference-test"},)


def test_reference_append_holds_shared_partition_lock_through_fsync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (
        tmp_path
        / "trade_date=2026-04-10"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream_event_references.jsonl"
    )
    reached_fsync = threading.Event()
    release_fsync = threading.Event()
    errors: list[BaseException] = []
    real_fsync = path_capture_module.os.fsync

    def blocking_fsync(descriptor: int) -> None:
        reached_fsync.set()
        if not release_fsync.wait(timeout=5):
            raise TimeoutError("reference append test did not release fsync")
        real_fsync(descriptor)

    def append_reference() -> None:
        try:
            append_path_event_references(target, (_reference("evt-lock"),))
        except BaseException as exc:  # pragma: no cover - asserted below
            errors.append(exc)

    monkeypatch.setattr(path_capture_module.os, "fsync", blocking_fsync)
    writer = threading.Thread(target=append_reference)
    writer.start()
    assert reached_fsync.wait(timeout=5)
    try:
        with pytest.raises(BlockingIOError):
            with partition_maintenance_lock(
                target,
                blocking=False,
                exclusive=True,
            ):
                pass
    finally:
        release_fsync.set()
        writer.join(timeout=5)

    assert not writer.is_alive()
    assert errors == []
    assert load_path_event_references(target)[0]["shock_event_id"] == "evt-lock"


def test_reference_append_after_compression_fails_closed_without_mutation(
    tmp_path: Path,
) -> None:
    target = (
        tmp_path
        / "trade_date=2026-04-10"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream_event_references.jsonl"
    )
    append_path_event_references(target, (_reference("evt-before"),))
    compressed = target.with_suffix(".jsonl.gz")
    with target.open("rb") as source, gzip.open(compressed, "wb") as output:
        output.write(source.read())
    target.unlink()

    original = compressed.read_bytes()
    with pytest.raises(OSError, match="partition is closed"):
        append_path_event_references(target, (_reference("evt-after", 2),))

    assert not target.exists()
    assert compressed.read_bytes() == original
    assert not target.with_name(
        "market_stream_event_references.part-000001.jsonl"
    ).exists()
    assert [row["shock_event_id"] for row in load_path_event_references(target)] == [
        "evt-before"
    ]


def test_reference_append_rejects_invalid_existing_gzip_without_mutation(
    tmp_path: Path,
) -> None:
    target = (
        tmp_path
        / "trade_date=2026-04-10"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream_event_references.jsonl"
    )
    target.parent.mkdir(parents=True)
    compressed = target.with_suffix(".jsonl.gz")
    compressed.write_bytes(b"not-a-gzip")
    original = compressed.read_bytes()

    with pytest.raises(OSError, match="partition is closed"):
        append_path_event_references(target, (_reference("evt-invalid"),))

    assert compressed.read_bytes() == original
    assert not target.with_name(
        "market_stream_event_references.part-000001.jsonl"
    ).exists()


def test_reference_plain_append_rolls_back_partial_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (
        tmp_path
        / "trade_date=2026-04-10"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream_event_references.jsonl"
    )
    target.parent.mkdir(parents=True)
    append_path_event_references(target, (_reference("evt-before"),))
    original = target.read_bytes()
    real_write = path_capture_module.os.write
    write_count = 0

    def partial_then_enospc(descriptor: int, payload: memoryview) -> int:
        nonlocal write_count
        write_count += 1
        if write_count == 1:
            return real_write(descriptor, payload[: max(1, len(payload) // 2)])
        raise OSError(errno.ENOSPC, "injected_reference_enospc")

    monkeypatch.setattr(path_capture_module.os, "write", partial_then_enospc)
    with pytest.raises(OSError, match="injected_reference_enospc"):
        append_path_event_references(target, (_reference("evt-failed", 2),))

    assert target.read_bytes() == original
    assert [row["shock_event_id"] for row in load_path_event_references(target)] == [
        "evt-before"
    ]

    monkeypatch.setattr(path_capture_module.os, "write", real_write)
    append_path_event_references(target, (_reference("evt-after", 3),))
    assert [row["shock_event_id"] for row in load_path_event_references(target)] == [
        "evt-before",
        "evt-after",
    ]


@pytest.mark.parametrize("compressed_target", [False, True])
def test_reference_append_rejects_external_symlink_target(
    tmp_path: Path,
    compressed_target: bool,
) -> None:
    target = (
        tmp_path
        / "trade_date=2026-04-10"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream_event_references.jsonl"
    )
    target.parent.mkdir(parents=True)
    selected = target.with_suffix(".jsonl.gz") if compressed_target else target
    external = tmp_path.parent / (
        f"{tmp_path.name}-external.jsonl.gz"
        if compressed_target
        else f"{tmp_path.name}-external.jsonl"
    )
    external.write_bytes(
        gzip.compress(b'{"external":true}\n', mtime=0)
        if compressed_target
        else b'{"external":true}\n'
    )
    original = external.read_bytes()
    selected.symlink_to(external)

    with pytest.raises(OSError, match="symlink"):
        append_path_event_references(target, (_reference("evt-symlink"),))

    assert selected.is_symlink()
    assert external.read_bytes() == original
    peer = target if compressed_target else target.with_suffix(".jsonl.gz")
    assert not peer.exists()
    with pytest.raises(OSError, match="symlink"):
        load_path_event_references(target)


def test_reference_append_and_load_reject_symlinked_session_ancestor(
    tmp_path: Path,
) -> None:
    venue_dir = tmp_path / "trade_date=2026-04-10" / "venue=KRX"
    external = tmp_path.parent / f"{tmp_path.name}-external-session"
    venue_dir.mkdir(parents=True)
    external.mkdir()
    session = venue_dir / "session=KRX_REGULAR"
    session.symlink_to(external, target_is_directory=True)
    target = session / "market_stream_event_references.jsonl"

    with pytest.raises(OSError, match="ancestor symlink"):
        append_path_event_references(target, (_reference("evt-ancestor"),))
    assert not (external / target.name).exists()

    external_source = external / target.name
    external_source.write_text('{"external":true}\n', encoding="utf-8")
    original = external_source.read_bytes()
    with pytest.raises(OSError, match="ancestor symlink"):
        load_path_event_references(target)

    assert external_source.read_bytes() == original
