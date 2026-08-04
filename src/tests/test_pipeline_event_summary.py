import gzip
import json
from pathlib import Path

import pytest

from src.engine.pipeline_event_summary import (
    PRODUCER_SUMMARY_STAGES,
    ProducerSummaryCompactor,
    _rehydrate_summary_for_append,
    update_and_load_pipeline_event_summaries,
)


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
    assert producer_meta["summary_detail_level"] == "counts_only_v1"
    assert producer_rows[0]["summary_detail_level"] == "counts_only_v1"
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
    assert rebuilt_meta["summary_detail_level"] == "counts_only_v1"
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
