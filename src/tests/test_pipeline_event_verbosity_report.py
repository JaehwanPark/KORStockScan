import json

from src.engine import pipeline_event_verbosity_report as report_mod
from src.engine.pipeline_event_summary import ProducerSummaryCompactor


def _event(target_date: str, hhmmss: str, stage: str, *, record_id: int, fields: dict | None = None) -> dict:
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
        "text_payload": "-",
    }


def _write_raw(tmp_path, target_date: str, rows: list[dict]) -> None:
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with (raw_dir / f"pipeline_events_{target_date}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_producer_summary(tmp_path, target_date: str, rows: list[dict]) -> None:
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path / "pipeline_event_summaries",
        mode="shadow",
        flush_sec=0,
    )
    for row in rows:
        compactor.submit(row)
    compactor.flush(target_date=target_date)


def test_pipeline_event_verbosity_report_detects_missing_shadow(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_raw(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "blocked_strength_momentum",
                record_id=1,
                fields={"reason": "below_strength_base"},
            )
        ],
    )

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_missing"
    assert report["recommended_workorder_state"] == "open_shadow_order"
    assert report["raw_stream"]["high_volume_line_count"] == 1
    assert report["policy"]["runtime_effect"] is False


def test_pipeline_event_verbosity_report_parity_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:00:01",
            "blocked_overbought",
            record_id=2,
            fields={"reason": "near_day_high"},
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", rows)
    _write_producer_summary(tmp_path, "2026-05-06", rows)

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_parity_pass"
    assert report["parity"]["ok"] is True
    assert report["parity"]["stage_diff"] == {}
    assert report["parity"]["blocker_diff"] == {}
    assert report["producer_summary"]["manifest_mode"] == "shadow"


def test_pipeline_event_verbosity_report_parity_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    raw_rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:00:01",
            "blocked_strength_momentum",
            record_id=2,
            fields={"reason": "below_window_buy_value"},
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", raw_rows)
    _write_producer_summary(tmp_path, "2026-05-06", raw_rows[:1])

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_parity_fail"
    assert report["recommended_workorder_state"] == "block_suppress_and_fix_shadow"
    assert report["parity"]["ok"] is False
    assert "blocked_strength_momentum" in report["parity"]["stage_diff"]


def test_pipeline_event_verbosity_report_marks_pending_flush_when_raw_tail_is_newer(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    raw_rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:05:00",
            "blocked_strength_momentum",
            record_id=2,
            fields={"reason": "below_window_buy_value"},
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", raw_rows)
    _write_producer_summary(tmp_path, "2026-05-06", raw_rows[:1])
    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / "pipeline_event_producer_summary_manifest_2026-05-06.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["updated_at"] = "2026-05-06T10:00:30"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_pending_flush"
    assert report["recommended_workorder_state"] == "observe_pending_next_flush"
    assert report["parity"]["producer_pending_flush"] is True
