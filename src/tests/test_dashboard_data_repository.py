import gzip
import json
from datetime import date, timedelta

import pytest

from src.engine.dashboard_data_repository import (
    _list_snapshot_kinds,
    _load_monitor_snapshot_from_file,
    _load_pipeline_events_from_file,
    load_monitor_snapshot_file_first,
    load_pipeline_events,
)


def test_load_monitor_snapshot_from_plain_file(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR", snapshot_dir)
    payload = {"source": "plain_file"}
    (snapshot_dir / "trade_review_2026-04-01.json").write_text(json.dumps(payload), encoding="utf-8")

    assert _load_monitor_snapshot_from_file("trade_review", "2026-04-01") == payload
    assert load_monitor_snapshot_file_first("trade_review", "2026-04-01") == payload


def test_load_monitor_snapshot_from_gzip_file(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR", snapshot_dir)
    payload = {"source": "gzip_file"}
    with gzip.open(snapshot_dir / "trade_review_2026-04-01.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(payload, handle)

    assert _load_monitor_snapshot_from_file("trade_review", "2026-04-01") == payload


def test_load_monitor_snapshot_future_date_returns_none(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR", snapshot_dir)
    future = (date.today() + timedelta(days=1)).isoformat()
    (snapshot_dir / f"trade_review_{future}.json").write_text("{}", encoding="utf-8")

    assert load_monitor_snapshot_file_first("trade_review", future) is None


def test_list_snapshot_kinds_from_plain_and_gzip(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR", snapshot_dir)
    (snapshot_dir / "trade_review_2026-04-01.json").write_text("{}", encoding="utf-8")
    with gzip.open(snapshot_dir / "performance_tuning_2026-04-01.json.gz", "wt", encoding="utf-8") as handle:
        handle.write("{}")

    assert _list_snapshot_kinds("2026-04-01") == ["performance_tuning", "trade_review"]


def test_load_pipeline_events_from_plain_file(monkeypatch, tmp_path):
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR", events_dir)
    payloads = [{"event": "1"}, {"event": "2"}]
    with (events_dir / "pipeline_events_2026-04-01.jsonl").open("w", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload) + "\n")

    assert _load_pipeline_events_from_file("2026-04-01") == payloads
    assert load_pipeline_events("2026-04-01") == payloads


def test_load_pipeline_events_from_gzip_file(monkeypatch, tmp_path):
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR", events_dir)
    with gzip.open(events_dir / "pipeline_events_2026-04-01.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "gzip_file"}) + "\n")

    assert _load_pipeline_events_from_file("2026-04-01") == [{"event": "gzip_file"}]


def test_load_pipeline_events_today_respects_include_file_flag(monkeypatch, tmp_path):
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR", events_dir)
    today = date.today().isoformat()
    (events_dir / f"pipeline_events_{today}.jsonl").write_text(
        json.dumps({"event": "file"}) + "\n",
        encoding="utf-8",
    )

    assert load_pipeline_events(today, include_file_for_today=True) == [{"event": "file"}]
    assert load_pipeline_events(today, include_file_for_today=False) == []


def test_load_pipeline_events_future_date_returns_empty(monkeypatch, tmp_path):
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    monkeypatch.setattr("src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR", events_dir)
    future = (date.today() + timedelta(days=1)).isoformat()
    (events_dir / f"pipeline_events_{future}.jsonl").write_text(
        json.dumps({"event": "future"}) + "\n",
        encoding="utf-8",
    )

    assert load_pipeline_events(future) == []


def test_invalid_dates_are_empty():
    assert load_monitor_snapshot_file_first("trade_review", "bad-date") is None
    assert load_pipeline_events("bad-date") == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
