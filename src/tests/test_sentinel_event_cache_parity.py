import json

from src.engine import buy_funnel_sentinel as buy
from src.engine import holding_exit_sentinel as holding
from src.engine.sentinel_event_cache import update_and_load_cached_event_rows

TARGET_DATE = "2026-05-06"


def _event(
    hhmmss: str,
    stage: str,
    *,
    pipeline: str = "ENTRY_PIPELINE",
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{TARGET_DATE}T{hhmmss}",
        "emitted_date": TARGET_DATE,
    }


def _raw_path(tmp_path):
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    return event_dir / f"pipeline_events_{TARGET_DATE}.jsonl"


def _write_lines(path, rows: list[dict], *, malformed: bool = False) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        if malformed:
            handle.write("{malformed-json}\n")


def _without_event_load(report: dict) -> dict:
    return {key: value for key, value in report.items() if key != "event_load"}


def test_incremental_cache_parity_for_malformed_partial_unchanged_and_appended_jsonl(
    tmp_path,
):
    raw_path = _raw_path(tmp_path)
    first = {
        "id": 1,
        "source_quality_status": "pass",
        "provenance_source": "pipeline_event",
    }
    partial = {
        "id": 2,
        "source_quality_status": "warning",
        "provenance_source": "partial_then_completed",
    }
    appended = {
        "id": 3,
        "source_quality_status": "pass",
        "provenance_source": "appended",
    }
    with raw_path.open("wb") as handle:
        handle.write(json.dumps(first).encode() + b"\n")
        handle.write(b"{malformed-json}\n")
        handle.write(json.dumps(partial).encode())

    kwargs = {
        "raw_path": raw_path,
        "cache_dir": tmp_path / "cache",
        "cache_name": "parity",
        "target_date": TARGET_DATE,
        "schema_version": 1,
        "parse_payload": lambda payload: payload,
    }
    first_rows, first_meta = update_and_load_cached_event_rows(**kwargs)

    assert first_rows == [first]
    assert first_meta["decode_errors"] == 1
    assert first_meta["appended_cache_rows"] == 1
    assert first_meta["rebuilt"] is True

    with raw_path.open("ab") as handle:
        handle.write(b"\n")
        handle.write(json.dumps(appended).encode() + b"\n")

    appended_rows, appended_meta = update_and_load_cached_event_rows(**kwargs)

    assert appended_rows == [first, partial, appended]
    assert appended_meta["appended_raw_lines"] == 2
    assert appended_meta["appended_cache_rows"] == 2
    assert appended_meta["decode_errors"] == 0
    assert appended_meta["rebuilt"] is False

    unchanged_rows, unchanged_meta = update_and_load_cached_event_rows(**kwargs)

    assert unchanged_rows == appended_rows
    assert unchanged_meta["appended_raw_lines"] == 0
    assert unchanged_meta["appended_cache_rows"] == 0
    assert unchanged_meta["decode_errors"] == 0
    assert unchanged_meta["rebuilt"] is False


def test_incremental_cache_empty_and_missing_raw_fallback(tmp_path):
    raw_path = _raw_path(tmp_path)
    raw_path.touch()
    kwargs = {
        "raw_path": raw_path,
        "cache_dir": tmp_path / "cache",
        "cache_name": "empty",
        "target_date": TARGET_DATE,
        "schema_version": 1,
        "parse_payload": lambda payload: payload,
    }

    empty_rows, empty_meta = update_and_load_cached_event_rows(**kwargs)
    assert empty_rows == []
    assert empty_meta["status"] == "ok"
    assert empty_meta["cache_event_count"] == 0

    raw_path.unlink()
    missing_rows, missing_meta = update_and_load_cached_event_rows(**kwargs)
    assert missing_rows == []
    assert missing_meta["status"] == "raw_missing"
    assert missing_meta["cache_event_count"] == 0


def test_buy_sentinel_raw_cache_report_parity(monkeypatch, tmp_path):
    monkeypatch.setattr(buy, "DATA_DIR", tmp_path)
    raw_path = _raw_path(tmp_path)
    _write_lines(
        raw_path,
        [
            _event("10:03:00", "order_bundle_submitted", record_id=3),
            _event("10:00:00", "ai_confirmed", record_id=1),
            _event(
                "10:01:00",
                "blocked_ai_score",
                record_id=2,
                fields={
                    "score": 66,
                    "source_quality_status": "pass",
                    "provenance_source": "entry_adm",
                    "actual_order_submitted": False,
                },
            ),
        ],
        malformed=True,
    )
    as_of = buy._parse_as_of(TARGET_DATE, "10:05:00")

    raw_report = buy.build_buy_funnel_sentinel_report(TARGET_DATE, as_of=as_of)
    cache_report = buy.build_buy_funnel_sentinel_report(
        TARGET_DATE, as_of=as_of, use_cache=True
    )

    assert _without_event_load(cache_report) == _without_event_load(raw_report)


def test_holding_exit_sentinel_raw_cache_report_parity(monkeypatch, tmp_path):
    monkeypatch.setattr(holding, "DATA_DIR", tmp_path)
    raw_path = _raw_path(tmp_path)
    _write_lines(
        raw_path,
        [
            _event(
                "10:03:00",
                "sell_order_sent",
                pipeline="HOLDING_PIPELINE",
                record_id=3,
                fields={"actual_order_submitted": True},
            ),
            _event(
                "10:00:00",
                "holding_started",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
            ),
            _event(
                "10:01:00",
                "ai_holding_review",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
                fields={
                    "ai_cache": "miss",
                    "source_quality_status": "pass",
                    "provenance_source": "holding_flow",
                },
            ),
            _event(
                "10:02:00",
                "exit_signal",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
            ),
        ],
        malformed=True,
    )
    as_of = holding._parse_as_of(TARGET_DATE, "10:05:00")

    raw_report = holding.build_holding_exit_sentinel_report(TARGET_DATE, as_of=as_of)
    cache_report = holding.build_holding_exit_sentinel_report(
        TARGET_DATE, as_of=as_of, use_cache=True
    )

    assert _without_event_load(cache_report) == _without_event_load(raw_report)
