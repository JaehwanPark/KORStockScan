import json

from src.engine.pipeline_event_summary import update_and_load_pipeline_event_summaries


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
