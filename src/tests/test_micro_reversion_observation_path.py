import json
import threading
import time
from pathlib import Path

import pytest

from src.engine.scalping.micro_reversion.observation_gate import (
    EconomicCandidateStatus,
    ObservationStatus,
    evaluate_economic_gate,
    evaluate_observation_gate,
)
from src.engine.scalping.micro_reversion.path_journal import (
    MarketPathPoint,
    MarketStreamPoint,
    NonBlockingPathJournalWriter,
    PathStoragePolicy,
    append_market_path_points,
    partition_path_files,
    readable_partition_path_files,
)
from src.engine.scalping.micro_reversion.tax import (
    InstrumentType,
    ListingMarket,
    tax_profile_for,
)


def _point(sequence: int = 1, **overrides) -> MarketPathPoint:
    values = {
        "event_id": "evt-1",
        "path_segment_id": "seg-1",
        "symbol": "000001",
        "exchange_timestamp": f"2026-08-08T09:00:0{sequence}+09:00",
        "local_receive_timestamp": f"2026-08-08T09:00:0{sequence}.010+09:00",
        "source_sequence": sequence,
        "sequence_epoch": 1,
        "series_sequence": sequence,
        "venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "detector_version": "detector-v1",
        "capture_started_at": "2026-08-08T09:00:00+09:00",
        "event_detected_at": "2026-08-08T09:00:01+09:00",
        "parent_wave_id": "wave-1",
        "path_phase": "ACTIVE_EVENT",
        "trade_price": 10_000 + sequence,
        "trade_qty": 10,
        "best_bid": 9_995,
        "best_ask": 10_005,
        "bid_depth": 100,
        "ask_depth": 120,
        "quote_age_ms": 10,
    }
    values.update(overrides)
    return MarketPathPoint(**values)


def _stream_point(sequence: int, *, exchange_second: int) -> MarketStreamPoint:
    return MarketStreamPoint(
        symbol="000001",
        exchange_timestamp=f"2026-08-08T09:00:{exchange_second:02d}+09:00",
        local_receive_timestamp=f"2026-08-08T09:01:{sequence:02d}+09:00",
        source_sequence=sequence,
        sequence_epoch=1,
        series_sequence=sequence,
        venue="KRX",
        session_bucket="KRX_REGULAR",
        realtime_type="0B",
        trade_price=10_000,
    )


def test_observation_gate_is_broad_but_economic_gate_is_narrow() -> None:
    observation = evaluate_observation_gate(
        tradeable_session=True,
        detector_condition_met=True,
        source_contract_minimum_passed=True,
    )
    unknown_tax = tax_profile_for(
        trade_date=__import__("datetime").date(2026, 8, 8),
        listing_market=ListingMarket.UNKNOWN,
        instrument_type=InstrumentType.UNKNOWN,
    )
    economic = evaluate_economic_gate(
        tax_profile=unknown_tax,
        instrument_tax_class_verified=False,
        all_in_cost_contract_complete=True,
        oos_net_ev_lcb_bps=1.0,
        tail_risk_passed=True,
        concentration_passed=True,
    )

    assert observation.status is ObservationStatus.OBSERVE_ELIGIBLE
    assert observation.observation_allowed is True
    assert observation.metric_role == "source_quality_and_observation_eligibility_gate"
    assert economic.status is EconomicCandidateStatus.BLOCKED_TAX_CLASS
    assert economic.economic_headline_allowed is False
    assert economic.primary_decision_metric == "coverage_adjusted_lower_bound_bps"


def test_economic_gate_rejects_known_but_unverified_tax_metadata() -> None:
    known_tax = tax_profile_for(
        trade_date=__import__("datetime").date(2026, 8, 8),
        listing_market=ListingMarket.KOSPI,
        instrument_type=InstrumentType.EQUITY,
    )
    result = evaluate_economic_gate(
        tax_profile=known_tax,
        instrument_tax_class_verified=False,
        all_in_cost_contract_complete=True,
        oos_net_ev_lcb_bps=1.0,
        tail_risk_passed=True,
        concentration_passed=True,
    )

    assert result.status is EconomicCandidateStatus.BLOCKED_TAX_CLASS
    assert result.economic_headline_allowed is False


def test_market_path_batch_requires_monotonic_sequence(tmp_path: Path) -> None:
    output = tmp_path / "path.jsonl"
    append_market_path_points(output, [_point(1), _point(2)])
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["source_sequence"] for row in rows] == [1, 2]
    assert all(row["actual_order_submitted"] is False for row in rows)

    with pytest.raises(ValueError, match="increase"):
        append_market_path_points(output, [_point(2), _point(1)])


def test_nonblocking_writer_records_queue_drop(tmp_path: Path, monkeypatch) -> None:
    entered = threading.Event()
    release = threading.Event()

    def blocked_append(path, points):
        entered.set()
        release.wait(timeout=2)

    monkeypatch.setattr(
        "src.engine.scalping.micro_reversion.path_journal.append_market_path_points",
        blocked_append,
    )
    writer = NonBlockingPathJournalWriter(
        tmp_path / "path.jsonl",
        max_queue_size=1,
        max_batch_size=1,
        flush_interval_sec=0.01,
    )
    writer.start()
    assert writer.submit(_point(1)) is True
    assert entered.wait(timeout=1)
    assert writer.submit(_point(2)) is True
    assert writer.submit(_point(3)) is False
    release.set()
    writer.close()

    metrics = writer.metrics()
    assert metrics.journal_dropped_envelopes == 1
    assert metrics.capture_degraded is True
    assert metrics.writer_alive is False


def test_close_does_not_depend_on_queue_shutdown_marker(
    tmp_path: Path, monkeypatch
) -> None:
    entered = threading.Event()
    release = threading.Event()
    close_errors: list[Exception] = []

    def blocked_append(path, points):
        entered.set()
        release.wait(timeout=2)

    monkeypatch.setattr(
        "src.engine.scalping.micro_reversion.path_journal.append_market_path_points",
        blocked_append,
    )
    writer = NonBlockingPathJournalWriter(
        tmp_path / "path.jsonl",
        max_queue_size=1,
        max_batch_size=1,
        flush_interval_sec=0.01,
    )
    writer.start()
    assert writer.submit(_point(1)) is True
    assert entered.wait(timeout=1)
    assert writer.submit(_point(2)) is True

    def close_writer() -> None:
        try:
            writer.close(timeout_sec=2)
        except Exception as exc:  # pragma: no cover - assertion captures it
            close_errors.append(exc)

    closer = threading.Thread(target=close_writer)
    closer.start()
    assert closer.is_alive()
    release.set()
    closer.join(timeout=2)

    assert close_errors == []
    assert closer.is_alive() is False
    assert writer.metrics().writer_alive is False


def test_writer_restart_preserves_sequence_and_drains(tmp_path: Path) -> None:
    writer = NonBlockingPathJournalWriter(
        tmp_path / "path.jsonl",
        max_batch_size=1,
        flush_interval_sec=0.01,
    )
    writer.start()
    assert writer.submit(_point(1)) is True
    writer.close()

    writer.start()
    assert writer.submit(_point(2)) is True
    writer.close()

    rows = [
        json.loads(line) for line in (tmp_path / "path.jsonl").read_text().splitlines()
    ]
    metrics = writer.metrics()
    assert [row["source_sequence"] for row in rows] == [1, 2]
    assert metrics.journal_writer_restart_count == 1
    assert metrics.persisted_envelope_count == 2
    assert (
        metrics.last_persisted_sequence_by_series["000001|KRX|KRX_REGULAR"][
            "series_sequence"
        ]
        == 2
    )
    assert metrics.writer_alive is False


def test_storage_policy_partitions_by_date_venue_and_session(tmp_path: Path) -> None:
    path = PathStoragePolicy().partition_path(
        tmp_path,
        trade_date="2026-08-08",
        venue="KRX",
        session_bucket="KRX_REGULAR",
    )

    assert path.relative_to(tmp_path).as_posix() == (
        "trade_date=2026-08-08/venue=KRX/" "session=KRX_REGULAR/market_path.jsonl"
    )


def test_writer_self_disables_only_capture_at_critical_disk(
    tmp_path: Path, monkeypatch
) -> None:
    writer = NonBlockingPathJournalWriter(tmp_path / "path.jsonl")
    monkeypatch.setattr(writer, "_disk_free_space", lambda: 0)
    writer.start()

    assert writer.submit(_point(1)) is True
    writer.close()

    metrics = writer.metrics()
    assert metrics.storage_self_disabled is True
    assert metrics.capture_degraded is True
    assert metrics.journal_writer_error_count == 1
    assert metrics.last_writer_error_type == "OSError"
    assert metrics.persisted_envelope_count == 0


def test_writer_rotates_full_path_shard_and_publishes_manifest(tmp_path: Path) -> None:
    base = tmp_path / "market_path.jsonl"
    first = _point(1)
    second = _point(2)
    first_size = len(
        (json.dumps(first.as_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    writer = NonBlockingPathJournalWriter(
        base,
        max_batch_size=1,
        flush_interval_sec=0.01,
        storage_policy=PathStoragePolicy(max_partition_bytes=first_size + 8),
    )
    writer.start()
    assert writer.submit(first) is True
    deadline = time.monotonic() + 1
    while writer.metrics().persisted_envelope_count < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert writer.submit(second) is True
    writer.close()

    shards = partition_path_files(base)
    manifest = json.loads(
        (tmp_path / "market_path.manifest.json").read_text(encoding="utf-8")
    )
    metrics = writer.metrics()
    assert [path.name for path in shards] == [
        "market_path.jsonl",
        "market_path.part-000001.jsonl",
    ]
    assert [
        json.loads(path.read_text(encoding="utf-8"))["source_sequence"]
        for path in shards
    ] == [1, 2]
    assert manifest["active_shard_index"] == 1
    assert [row["file"] for row in manifest["shards"]] == [path.name for path in shards]
    assert manifest["actual_order_submitted"] is False
    assert manifest["broker_order_forbidden"] is True
    assert metrics.journal_rotation_count == 1
    assert metrics.journal_shard_count == 2
    assert metrics.journal_manifest_error_count == 0
    assert metrics.journal_dropped_envelopes == 0
    assert metrics.journal_writer_error_count == 0


def test_writer_restart_continues_from_latest_path_shard(tmp_path: Path) -> None:
    base = tmp_path / "market_path.jsonl"
    point_size = len(
        (
            json.dumps(_point(1).as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
    )
    policy = PathStoragePolicy(max_partition_bytes=point_size + 8)
    first_writer = NonBlockingPathJournalWriter(
        base, max_batch_size=1, flush_interval_sec=0.01, storage_policy=policy
    )
    first_writer.start()
    assert first_writer.submit(_point(1)) is True
    deadline = time.monotonic() + 1
    while (
        first_writer.metrics().persisted_envelope_count < 1
        and time.monotonic() < deadline
    ):
        time.sleep(0.005)
    assert first_writer.submit(_point(2)) is True
    first_writer.close()

    restarted = NonBlockingPathJournalWriter(
        base, max_batch_size=1, flush_interval_sec=0.01, storage_policy=policy
    )
    restarted.start()
    assert restarted.submit(_point(3)) is True
    restarted.close()

    shards = partition_path_files(base)
    assert [path.name for path in shards] == [
        "market_path.jsonl",
        "market_path.part-000001.jsonl",
        "market_path.part-000002.jsonl",
    ]
    assert restarted.metrics().journal_active_shard_index == 2
    assert restarted.metrics().journal_shard_count == 3


def test_writer_self_disables_before_overwriting_shard_bound(tmp_path: Path) -> None:
    base = tmp_path / "market_path.jsonl"
    point_size = len(
        (
            json.dumps(_point(1).as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
    )
    writer = NonBlockingPathJournalWriter(
        base,
        max_batch_size=1,
        flush_interval_sec=0.01,
        storage_policy=PathStoragePolicy(
            max_partition_bytes=point_size + 8,
            max_partition_shards=2,
        ),
    )
    writer.start()
    for sequence in (1, 2):
        assert writer.submit(_point(sequence)) is True
        deadline = time.monotonic() + 1
        while (
            writer.metrics().persisted_envelope_count < sequence
            and time.monotonic() < deadline
        ):
            time.sleep(0.005)
    assert writer.submit(_point(3)) is True
    writer.close()

    metrics = writer.metrics()
    assert [path.name for path in partition_path_files(base)] == [
        "market_path.jsonl",
        "market_path.part-000001.jsonl",
    ]
    assert metrics.storage_self_disabled is True
    assert metrics.journal_writer_error_count == 1
    assert metrics.journal_dropped_envelopes == 1
    assert metrics.persisted_envelope_count == 2


def test_writer_projection_guard_stops_unsustainable_daily_rate(
    tmp_path: Path,
) -> None:
    writer = NonBlockingPathJournalWriter(
        tmp_path / "market_path.jsonl",
        max_batch_size=1,
        flush_interval_sec=0.01,
        storage_policy=PathStoragePolicy(
            max_projected_partition_bytes=1,
            projection_horizon_sec=10,
            projection_min_elapsed_sec=1,
        ),
    )
    writer.start()
    assert writer.submit(_point(1)) is True
    deadline = time.monotonic() + 1
    while writer.metrics().persisted_envelope_count < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    writer._first_write_monotonic = time.monotonic() - 2
    assert writer.submit(_point(2)) is True
    writer.close()

    metrics = writer.metrics()
    assert metrics.journal_projection_breach_count == 1
    assert metrics.storage_self_disabled is True
    assert metrics.capture_degraded is True
    assert metrics.journal_projected_partition_bytes is not None
    assert metrics.journal_projected_partition_bytes > 1


def test_canonical_stream_retains_sequence_when_exchange_clock_regresses(
    tmp_path: Path,
) -> None:
    base = tmp_path / "market_stream.jsonl"
    writer = NonBlockingPathJournalWriter(
        base,
        max_batch_size=2,
        flush_interval_sec=0.01,
    )
    writer.start()

    assert writer.submit(_stream_point(1, exchange_second=2)) is True
    assert writer.submit(_stream_point(2, exchange_second=1)) is True
    writer.close()

    rows = [json.loads(line) for line in base.read_text(encoding="utf-8").splitlines()]
    assert [row["series_sequence"] for row in rows] == [1, 2]
    assert writer.metrics().journal_writer_error_count == 0


def test_partition_reader_rejects_malformed_or_gapped_shards(tmp_path: Path) -> None:
    base = tmp_path / "market_path.jsonl"
    base.write_text("{}\n", encoding="utf-8")
    malformed = tmp_path / "market_path.part-bad.jsonl"
    malformed.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="six decimal digits"):
        partition_path_files(base)

    malformed.unlink()
    (tmp_path / "market_path.part-000002.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not contiguous"):
        partition_path_files(base)


def test_readable_partition_discovers_post_session_gzip_shards(tmp_path: Path) -> None:
    base = tmp_path / "market_stream.jsonl"
    base.with_suffix(".jsonl.gz").write_bytes(b"gzip-placeholder")
    (tmp_path / "market_stream.part-000001.jsonl.gz").write_bytes(b"gzip-placeholder")

    assert [path.name for path in readable_partition_path_files(base)] == [
        "market_stream.jsonl.gz",
        "market_stream.part-000001.jsonl.gz",
    ]


def test_writer_rejects_cross_batch_sequence_regression(tmp_path: Path) -> None:
    writer = NonBlockingPathJournalWriter(
        tmp_path / "path.jsonl",
        max_batch_size=1,
        flush_interval_sec=0.01,
    )
    writer.start()
    assert writer.submit(_point(2)) is True
    deadline = time.monotonic() + 1
    while writer.metrics().persisted_envelope_count < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert writer.metrics().persisted_envelope_count == 1

    assert writer.submit(_point(1)) is True
    writer.close()

    metrics = writer.metrics()
    assert metrics.persisted_envelope_count == 1
    assert metrics.journal_writer_error_count == 1
    assert metrics.journal_dropped_envelopes == 1
