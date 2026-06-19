import gzip
import json
from datetime import date
from unittest.mock import Mock, patch, MagicMock
import pytest

import src.engine.dashboard_data_repository as dashboard_repo
from src.engine.dashboard_data_repository import (
    ensure_tables,
    upsert_pipeline_event_rows,
    upsert_monitor_snapshot,
    legacy_dashboard_db_enabled,
    load_monitor_snapshot_prefer_db,
    load_pipeline_events,
    _load_monitor_snapshot_from_file,
    _load_monitor_snapshot_from_db,
    _load_pipeline_events_from_file,
    _load_pipeline_events_from_db,
    MONITOR_SNAPSHOT_DIR,
    PIPELINE_EVENTS_DIR,
)


def test_legacy_dashboard_db_disabled_by_default(monkeypatch):
    """parquet 전환 후 legacy raw DB 테이블은 기본 재생성하지 않는다."""
    monkeypatch.delenv("KORSTOCKSCAN_ENABLE_LEGACY_DASHBOARD_DB", raising=False)
    get_conn = Mock()
    monkeypatch.setattr(
        "src.engine.dashboard_data_repository.get_db_connection",
        get_conn,
    )

    assert legacy_dashboard_db_enabled() is False
    ensure_tables()
    assert upsert_pipeline_event_rows("2026-04-20", [{"emitted_at": "2026-04-20T10:00:00"}]) == 0
    upsert_monitor_snapshot("trade_review", "2026-04-20", {"ok": True})

    get_conn.assert_not_called()


def test_load_monitor_snapshot_prefer_db_past_date_db_first(monkeypatch, tmp_path):
    """과거 날짜는 DB를 먼저 조회하고, 없으면 파일을 조회한다."""
    # DB에서 로드 실패 모의
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_monitor_snapshot_from_db',
        lambda *args: None
    )
    
    # 파일에 스냅샷 작성
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR',
        snapshot_dir
    )
    
    payload = {"test": "value"}
    file_path = snapshot_dir / "trade_review_2026-04-01.json"
    file_path.write_text(json.dumps(payload), encoding='utf-8')
    
    # 호출 (날짜는 오늘보다 과거)
    result = load_monitor_snapshot_prefer_db("trade_review", "2026-04-01")
    
    # DB에 없으므로 파일에서 로드되어야 함
    assert result is not None
    assert result["test"] == "value"
    assert result["meta"]["source"] == "file"


def test_load_monitor_snapshot_prefer_db_past_date_db_exists(monkeypatch):
    """과거 날짜 DB에 데이터가 있으면 파일을 조회하지 않는다."""
    # DB에서 로드 성공 모의
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_monitor_snapshot_from_db',
        lambda *args: {"db": "data"}
    )
    # 파일은 존재하지 않도록 모의
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_monitor_snapshot_from_file',
        lambda *args: None
    )
    
    result = load_monitor_snapshot_prefer_db("trade_review", "2026-04-01")
    
    assert result is not None
    assert result["db"] == "data"
    assert result["meta"]["source"] == "db"


def test_load_monitor_snapshot_prefer_db_today_file_first(monkeypatch, tmp_path):
    """당일 날짜는 파일을 먼저 조회하고, 없으면 DB를 조회한다."""
    # 파일에 스냅샷 작성
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR',
        snapshot_dir
    )
    
    payload = {"today": "file"}
    today = date.today().isoformat()
    file_path = snapshot_dir / f"trade_review_{today}.json"
    file_path.write_text(json.dumps(payload), encoding='utf-8')
    
    # DB는 비어있도록 모의
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.get_db_connection',
        lambda: mock_conn
    )
    
    result = load_monitor_snapshot_prefer_db("trade_review", today)
    
    assert result is not None
    assert result["today"] == "file"
    assert result["meta"]["source"] == "file"


def test_load_monitor_snapshot_prefer_db_past_date_file_prefer(monkeypatch, tmp_path):
    """옵션 사용 시 과거 날짜도 파일을 우선 조회한다."""
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR',
        snapshot_dir
    )

    file_payload = {"source": "file"}
    file_path = snapshot_dir / "trade_review_2026-04-01.json"
    file_path.write_text(json.dumps(file_payload), encoding='utf-8')

    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_monitor_snapshot_from_db',
        lambda *args: {"source": "db"}
    )

    result = load_monitor_snapshot_prefer_db(
        "trade_review",
        "2026-04-01",
        prefer_file_for_past=True,
    )

    assert result is not None
    assert result["source"] == "file"
    assert result["meta"]["source"] == "file"


def test_load_monitor_snapshot_from_gzip_file(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.MONITOR_SNAPSHOT_DIR',
        snapshot_dir
    )
    payload = {"source": "gzip_file"}
    with gzip.open(snapshot_dir / "trade_review_2026-04-01.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(payload, handle)

    result = _load_monitor_snapshot_from_file("trade_review", "2026-04-01")

    assert result == payload


def test_load_pipeline_events_past_date_db_fallback(monkeypatch, tmp_path):
    """과거 날짜 DB에 데이터가 없으면 파일에서 로드한다."""
    # DB 빈 결과 모의
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.get_db_connection',
        lambda: mock_conn
    )
    
    # 파일에 이벤트 작성
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR',
        events_dir
    )
    
    payloads = [
        {"event": "1", "emitted_at": "2026-04-01T10:00:00"},
        {"event": "2", "emitted_at": "2026-04-01T10:01:00"},
    ]
    file_path = events_dir / "pipeline_events_2026-04-01.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        for p in payloads:
            f.write(json.dumps(p) + '\n')
    
    result = load_pipeline_events("2026-04-01", include_file_for_today=False)
    
    assert len(result) == 2
    # source 필드는 추가되지 않지만, 파일에서 왔음을 알 수 있음
    # (구현에 source 필드가 없으므로 생략)


def test_load_pipeline_events_past_date_file_prefer(monkeypatch, tmp_path):
    """옵션 사용 시 과거 날짜는 파일을 먼저 사용한다."""
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_pipeline_events_from_db',
        lambda *args: [{"event": "db", "emitted_at": "2026-04-01T09:00:00", "record_id": 1}]
    )

    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR',
        events_dir
    )
    file_path = events_dir / "pipeline_events_2026-04-01.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"event": "file", "emitted_at": "2026-04-01T10:00:00", "record_id": 2}) + '\n')

    result = load_pipeline_events(
        "2026-04-01",
        include_file_for_today=True,
        prefer_file_for_past=True,
    )
    assert len(result) == 1
    assert result[0]["event"] == "file"


def test_load_pipeline_events_from_gzip_file(monkeypatch, tmp_path):
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR',
        events_dir
    )
    with gzip.open(events_dir / "pipeline_events_2026-04-01.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "gzip_file"}) + "\n")

    result = _load_pipeline_events_from_file("2026-04-01")

    assert result == [{"event": "gzip_file"}]


def test_load_pipeline_events_today_merge(monkeypatch, tmp_path):
    """당일 날짜는 파일과 DB를 병합한다."""
    today = date.today().isoformat()
    
    # DB 결과 모의
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_pipeline_events_from_db',
        lambda *args: [{"event": "db", "emitted_at": f"{today}T09:00:00", "record_id": 1}]
    )
    
    # 파일 이벤트 작성
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR',
        events_dir
    )
    
    file_path = events_dir / f"pipeline_events_{today}.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"event": "file", "emitted_at": f"{today}T10:00:00", "record_id": 2}) + '\n')
    
    result = load_pipeline_events(today, include_file_for_today=True)
    
    # 두 이벤트 모두 포함 (중복 없음)
    assert len(result) == 2
    # 중복 제거 로직은 별도 테스트에서 확인


def test_load_pipeline_events_today_file_prefer(monkeypatch, tmp_path):
    """옵션 사용 시 당일은 파일만 우선 사용한다."""
    today = date.today().isoformat()
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository._load_pipeline_events_from_db',
        lambda *args: [{"event": "db", "emitted_at": f"{today}T09:00:00", "record_id": 1}]
    )

    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        'src.engine.dashboard_data_repository.PIPELINE_EVENTS_DIR',
        events_dir
    )
    file_path = events_dir / f"pipeline_events_{today}.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"event": "file", "emitted_at": f"{today}T10:00:00", "record_id": 2}) + '\n')

    result = load_pipeline_events(
        today,
        include_file_for_today=True,
        prefer_file_for_today=True,
    )
    assert len(result) == 1
    assert result[0]["event"] == "file"


def test_upsert_pipeline_event_rows_uses_bulk_execute_values(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ENABLE_LEGACY_DASHBOARD_DB", "1")
    monkeypatch.setattr("src.engine.dashboard_data_repository.ensure_tables", lambda: None)
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr("src.engine.dashboard_data_repository.get_db_connection", lambda: conn)
    execute_mock = MagicMock(return_value=[(1,), (1,)])
    monkeypatch.setattr("src.engine.dashboard_data_repository.execute_values", execute_mock)

    inserted = upsert_pipeline_event_rows(
        "2026-04-20",
        [
            {
                "emitted_date": "2026-04-20",
                "pipeline": "ENTRY_PIPELINE",
                "stock_code": "005930",
                "stage": "order_leg_sent",
                "emitted_at": "2026-04-20T10:00:00+09:00",
                "record_id": 1,
                "fields": {"status": "ok"},
            },
            {
                "emitted_date": "2026-04-20",
                "pipeline": "ENTRY_PIPELINE",
                "stock_code": "000660",
                "stage": "order_leg_sent",
                "emitted_at": "2026-04-20T10:01:00+09:00",
                "record_id": 2,
                "fields": {"status": "ok"},
            },
        ],
    )

    assert inserted == 2
    execute_mock.assert_called_once()
    assert len(execute_mock.call_args.args[2]) == 2
    conn.commit.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
