import gzip
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.engine.pipeline_event_summary import (
    PRODUCER_SUMMARY_STAGES,
    ProducerSummaryCompactor,
    _rehydrate_summary_for_append,
    update_and_load_pipeline_event_summaries,
)


def _review_event(index=0):
    return {
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": "scalping_scanner_fast_precheck",
        "stock_code": "005930",
        "emitted_at": "2026-09-08T10:00:00.123456",
        "record_id": index,
        "fields": {"source_quality_gate": "pass", "session": "KRX_REGULAR"},
    }


def test_async_submit_never_waits_for_slow_publish(tmp_path, monkeypatch):
    from src.engine.pipeline_event_summary import load_summary_rows

    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=0, auto_flush=True
    )
    entered, release, returned = (threading.Event() for _ in range(3))
    original = compactor._publish

    def slow_publish(*args):
        entered.set()
        assert release.wait(3)
        return original(*args)

    monkeypatch.setattr(compactor, "_publish", slow_publish)
    compactor.submit(_review_event(1))
    writer = threading.Thread(target=compactor.flush)
    writer.start()
    assert entered.wait(2)

    def submit():
        compactor.submit(_review_event(2))
        returned.set()

    caller = threading.Thread(target=submit)
    try:
        caller.start()
        assert returned.wait(0.5), "submit waited for diagnostic disk I/O"
        assert not release.is_set()
    finally:
        release.set()
        writer.join(3)
        caller.join(3)
        compactor.close()
    rows = load_summary_rows(
        tmp_path / "pipeline_event_producer_summary_2026-09-08.jsonl"
    )
    assert sum(row["event_count"] for row in rows) == 2


def test_detached_retry_batch_preserves_new_events_and_dates(tmp_path, monkeypatch):
    from src.engine import pipeline_event_summary as mod

    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600, auto_flush=True
    )
    first, second = _review_event(1), _review_event(2)
    second["emitted_at"] = "2026-09-09T00:00:00"
    compactor.submit(first)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                mod, "_write_json", lambda *args: (_ for _ in ()).throw(OSError("full"))
            )
            with pytest.raises(OSError):
                compactor.flush()
        compactor.submit(first)
        compactor.submit(second)
        compactor.flush()
    finally:
        compactor.close()
    for date, count in [("2026-09-08", 2), ("2026-09-09", 1)]:
        rows = mod.load_summary_rows(
            tmp_path / f"pipeline_event_producer_summary_{date}.jsonl"
        )
        assert sum(row["event_count"] for row in rows) == count


def test_async_buffer_has_bound_and_no_inline_flush_on_overflow(tmp_path, monkeypatch):
    from src.engine import pipeline_event_summary as mod

    monkeypatch.setattr(mod, "PRODUCER_MAX_GROUPS", 1)
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600, auto_flush=True
    )
    other = _review_event(2)
    other["stock_code"] = "000001"
    try:
        with monkeypatch.context() as patch:
            patch.setattr(compactor._wake, "set", lambda: None)
            compactor.submit(_review_event())
            patch.setattr(
                compactor, "flush", lambda **kwargs: pytest.fail("inline disk flush")
            )
            with pytest.raises(BufferError):
                compactor.submit(other)
        assert len(compactor._groups) == 1
        assert compactor._rejected_count == 1
    finally:
        compactor.close()


def test_publish_duration_includes_manifest_and_health_failure_never_reappends(
    tmp_path, monkeypatch
):
    import time
    from src.engine import pipeline_event_summary as mod

    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600
    )
    compactor.submit(_review_event())
    original = mod._write_json

    def slow_manifest_failed_health(path, payload):
        if "producer_health" in path.name:
            raise OSError("health disk full")
        time.sleep(0.05)
        return original(path, payload)

    with monkeypatch.context() as patch:
        patch.setattr(mod, "_write_json", slow_manifest_failed_health)
        receipt = compactor.flush()
    assert receipt["last_flush_duration_ms"] >= 50
    assert compactor.health_write_error_count == 1
    assert compactor.flush()["status"] == "no_pending_rows"
    rows = mod.load_summary_rows(
        tmp_path / "pipeline_event_producer_summary_2026-09-08.jsonl"
    )
    assert sum(row["event_count"] for row in rows) == 1


def test_async_close_without_wait_does_not_block_publisher(tmp_path, monkeypatch):
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600, auto_flush=True
    )
    compactor.submit(_review_event())
    original = compactor._publish
    entered, release = threading.Event(), threading.Event()

    def slow_publish(*args):
        entered.set()
        assert release.wait(3)
        return original(*args)

    monkeypatch.setattr(compactor, "_publish", slow_publish)
    compactor.close(wait=False)
    try:
        assert entered.wait(2)
        with pytest.raises(RuntimeError, match="closed"):
            compactor.submit(_review_event(2))
    finally:
        release.set()
        compactor.close()


def test_high_water_wakes_worker_before_long_period(tmp_path, monkeypatch):
    from src.engine import pipeline_event_summary as mod

    monkeypatch.setattr(mod, "PRODUCER_MAX_GROUPS", 4)
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600, auto_flush=True
    )
    published = threading.Event()
    original = compactor._publish

    def publish(*args):
        result = original(*args)
        published.set()
        return result

    monkeypatch.setattr(compactor, "_publish", publish)
    try:
        for i in range(2):
            event = _review_event(i)
            event["stock_code"] = str(i)
            compactor.submit(event)
        assert published.wait(2)
    finally:
        compactor.close()


def test_overlarge_flush_period_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="3600"):
        ProducerSummaryCompactor(summary_dir=tmp_path, mode="shadow", flush_sec=3601)


def test_producer_periodic_flush_does_not_need_another_event(tmp_path, monkeypatch):
    published = threading.Event()
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=1, auto_flush=True
    )
    original = compactor._publish

    def publish(*args):
        result = original(*args)
        published.set()
        return result

    monkeypatch.setattr(compactor, "_publish", publish)
    try:
        compactor.submit(_review_event())
        assert published.wait(4), "idle tail was not flushed"
        manifest = json.loads(
            (
                tmp_path / "pipeline_event_producer_summary_manifest_2026-09-08.json"
            ).read_text()
        )
        assert manifest["summary_event_count"] == 1
        assert manifest["periodic_flush_enabled"] is True
        assert manifest["coverage_last_event_at"].endswith(".123456")
    finally:
        compactor.close()


def test_producer_manifest_failure_retry_does_not_duplicate_rows(tmp_path, monkeypatch):
    from src.engine import pipeline_event_summary as mod
    import pytest

    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600
    )
    compactor.submit(_review_event())
    original = mod._write_json
    with monkeypatch.context() as patch:

        def fail(*args):
            raise OSError("manifest full")

        patch.setattr(mod, "_write_json", fail)
        with pytest.raises(OSError):
            compactor.flush()
    assert mod._write_json is original
    compactor.flush()
    rows = mod.load_summary_rows(
        tmp_path / "pipeline_event_producer_summary_2026-09-08.jsonl"
    )
    assert sum(row["event_count"] for row in rows) == 1


def test_concurrent_producer_submissions_preserve_exact_counts(tmp_path):
    from src.engine.pipeline_event_summary import load_summary_rows

    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=0
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: compactor.submit(_review_event(i)), range(40)))
    rows = load_summary_rows(
        tmp_path / "pipeline_event_producer_summary_2026-09-08.jsonl"
    )
    manifest = json.loads(
        (
            tmp_path / "pipeline_event_producer_summary_manifest_2026-09-08.json"
        ).read_text()
    )
    assert (
        sum(row["event_count"] for row in rows) == manifest["summary_event_count"] == 40
    )


def test_wrong_date_flush_keeps_pending_evidence(tmp_path):
    import pytest

    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path, mode="shadow", flush_sec=3600
    )
    compactor.submit(_review_event())
    with pytest.raises(ValueError, match="target date"):
        compactor.flush(target_date="2026-09-07")
    assert compactor.flush()["summary_event_count"] == 1


def test_rehydrate_summary_for_append_restores_archive_atomically(tmp_path):
    summary_path = tmp_path / "pipeline_event_summary_2026-08-04.jsonl"
    archived_path = Path(f"{summary_path}.gz")
    with gzip.open(archived_path, "wt", encoding="utf-8") as handle:
        handle.write('{"event_count":1}\n')

    _rehydrate_summary_for_append(summary_path)

    assert summary_path.read_text(encoding="utf-8") == '{"event_count":1}\n'
    assert not archived_path.exists()


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    record_id: int,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
    }


def _labeler(stage: str, fields: dict[str, str]) -> str:
    return f"{stage}:{fields.get('reason') or '-'}"


def test_pipeline_event_summary_handles_partial_line_offsets_and_idempotency(tmp_path):
    target_date = "2026-05-06"
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir()
    raw_path = raw_dir / f"pipeline_events_{target_date}.jsonl"
    rows = [
        _event(
            target_date,
            "10:00:01",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_buy_ratio", "buy_ratio": "0.41", "text": "a"},
        ),
        _event(
            target_date,
            "10:00:02",
            "blocked_strength_momentum",
            record_id=2,
            fields={"reason": "below_buy_ratio", "buy_ratio": "0.45"},
        ),
    ]
    with raw_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(rows[0], ensure_ascii=False) + "\n")
        handle.write(json.dumps(rows[1], ensure_ascii=False))

    summary_rows, meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=tmp_path / "pipeline_event_summaries",
        target_date=target_date,
        reason_labeler=_labeler,
    )

    assert meta["status"] == "ok"
    assert meta["appended_source_events"] == 1
    assert meta["raw_offset"] < raw_path.stat().st_size
    assert len(summary_rows) == 1
    assert summary_rows[0]["event_count"] == 1
    assert summary_rows[0]["numeric_stats"]["buy_ratio"]["avg"] == 0.41
    assert summary_rows[0]["field_presence_counts"]["reason"] == 1

    with raw_path.open("a", encoding="utf-8") as handle:
        handle.write("\n")

    summary_rows, meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=tmp_path / "pipeline_event_summaries",
        target_date=target_date,
        reason_labeler=_labeler,
    )

    assert meta["appended_source_events"] == 1
    assert sum(row["event_count"] for row in summary_rows) == 2
    assert meta["raw_offset"] == raw_path.stat().st_size

    summary_rows, meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=tmp_path / "pipeline_event_summaries",
        target_date=target_date,
        reason_labeler=_labeler,
    )

    assert meta["appended_source_events"] == 0
    assert sum(row["event_count"] for row in summary_rows) == 2


def test_pipeline_event_summary_records_samples_and_actual_order_authority(tmp_path):
    target_date = "2026-05-06"
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir()
    raw_path = raw_dir / f"pipeline_events_{target_date}.jsonl"
    with raw_path.open("w", encoding="utf-8") as handle:
        for idx in range(8):
            handle.write(
                json.dumps(
                    _event(
                        target_date,
                        f"10:00:{idx:02d}",
                        "blocked_overbought",
                        record_id=idx,
                        fields={
                            "reason": "near_day_high",
                            "actual_order_submitted": "false",
                            "distance_pct": str(idx),
                        },
                    ),
                    ensure_ascii=False,
                )
                + "\n"
            )

    summary_rows, meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=tmp_path / "pipeline_event_summaries",
        target_date=target_date,
        reason_labeler=_labeler,
    )

    assert meta["status"] == "ok"
    assert len(summary_rows) == 1
    row = summary_rows[0]
    assert row["actual_order_submitted"] == "false"
    assert row["event_count"] == 8
    assert len(row["sample_events"]) <= 6
    assert row["sample_raw_offsets"] == sorted(row["sample_raw_offsets"])
    assert row["second_counts"]["2026-05-06T10:00:07"] == 1
    assert row["decision_authority"] == "diagnostic_aggregation"
    assert row["runtime_effect"] is False


def test_pipeline_event_summary_profile_isolates_producer_parity_artifacts(tmp_path):
    target_date = "2026-05-06"
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir()
    raw_path = raw_dir / f"pipeline_events_{target_date}.jsonl"
    raw_path.write_text(
        json.dumps(
            _event(
                target_date,
                "10:00:01",
                "scalping_scanner_fast_precheck",
                record_id=1,
                fields={
                    "fast_precheck_result": "defer",
                    "fast_precheck_reason": "waiting_heavy_eval",
                },
            ),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_dir = tmp_path / "pipeline_event_summaries"

    default_rows, default_meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=summary_dir,
        target_date=target_date,
        reason_labeler=_labeler,
    )
    producer_rows, producer_meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=summary_dir,
        target_date=target_date,
        reason_labeler=_labeler,
        summary_stages=PRODUCER_SUMMARY_STAGES,
        summary_profile="producer_parity",
    )

    assert default_rows == []
    assert len(producer_rows) == 1
    assert default_meta["summary_profile"] == "default"
    assert producer_meta["summary_profile"] == "producer_parity"
    assert producer_meta["summary_detail_level"] == "counts_identity_v2"
    assert producer_rows[0]["summary_detail_level"] == "counts_identity_v2"
    assert producer_rows[0]["event_count"] == 1
    for diagnostic_key in (
        "field_presence_counts",
        "numeric_stats",
        "second_counts",
        "first_raw_offset",
        "last_raw_offset",
        "sample_raw_offsets",
        "sample_events",
    ):
        assert diagnostic_key not in producer_rows[0]
    assert default_meta["summary_path"] != producer_meta["summary_path"]
    assert default_meta["manifest_path"] != producer_meta["manifest_path"]


def test_producer_parity_profile_rebuilds_legacy_full_detail_manifest(tmp_path):
    target_date = "2026-05-06"
    raw_path = tmp_path / f"pipeline_events_{target_date}.jsonl"
    raw_path.write_text(
        json.dumps(
            _event(
                target_date,
                "10:00:01",
                "scalping_scanner_fast_precheck",
                record_id=1,
            )
        )
        + "\n",
        encoding="utf-8",
    )
    summary_dir = tmp_path / "pipeline_event_summaries"
    _, first_meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=summary_dir,
        target_date=target_date,
        reason_labeler=_labeler,
        summary_stages=PRODUCER_SUMMARY_STAGES,
        summary_profile="producer_parity",
    )
    manifest_path = Path(first_meta["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("summary_detail_level")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rows, rebuilt_meta = update_and_load_pipeline_event_summaries(
        raw_path=raw_path,
        summary_dir=summary_dir,
        target_date=target_date,
        reason_labeler=_labeler,
        summary_stages=PRODUCER_SUMMARY_STAGES,
        summary_profile="producer_parity",
    )

    assert rebuilt_meta["rebuilt"] is True
    assert rebuilt_meta["summary_detail_level"] == "counts_identity_v2"
    assert len(rows) == 1
    assert "sample_events" not in rows[0]


def test_pipeline_event_summary_rejects_unknown_profile(tmp_path):
    raw_path = tmp_path / "pipeline_events_2026-05-06.jsonl"
    raw_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported pipeline event summary profile"):
        update_and_load_pipeline_event_summaries(
            raw_path=raw_path,
            summary_dir=tmp_path / "pipeline_event_summaries",
            target_date="2026-05-06",
            reason_labeler=_labeler,
            summary_profile="../escape",
        )


def test_producer_summary_flushes_previous_date_before_new_date_event(tmp_path):
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path,
        mode="shadow",
        flush_sec=3600,
        sample_per_bucket=2,
    )
    first = _event(
        "2026-07-31",
        "23:59:59",
        "scalping_scanner_fast_precheck",
        record_id=1,
        fields={
            "fast_precheck_result": "defer",
            "fast_precheck_reason": "waiting_heavy_eval",
        },
    )
    second = _event(
        "2026-08-01",
        "00:00:01",
        "scalping_scanner_fast_precheck",
        record_id=2,
        fields={
            "fast_precheck_result": "pass",
            "fast_precheck_reason": "ready",
        },
    )

    compactor.submit(first)
    compactor.submit(second)
    compactor.flush(target_date="2026-08-01")

    july_rows = [
        json.loads(line)
        for line in (tmp_path / "pipeline_event_producer_summary_2026-07-31.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    august_rows = [
        json.loads(line)
        for line in (tmp_path / "pipeline_event_producer_summary_2026-08-01.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert [row["target_date"] for row in july_rows] == ["2026-07-31"]
    assert [row["target_date"] for row in august_rows] == ["2026-08-01"]
    assert sum(row["event_count"] for row in july_rows) == 1
    assert sum(row["event_count"] for row in august_rows) == 1
