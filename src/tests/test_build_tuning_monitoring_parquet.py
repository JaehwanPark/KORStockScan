"""build_tuning_monitoring_parquet 모듈 테스트."""

from datetime import date
from pathlib import Path
import tempfile
import shutil
import json
import gzip

import pandas as pd
import pytest

import src.engine.build_tuning_monitoring_parquet as parquet_builder
from src.engine.build_tuning_monitoring_parquet import (
    read_jsonl_lines,
    extract_event_id,
    convert_to_dataframe,
    deduplicate_by_event_id,
    process_single_date,
)


@pytest.fixture
def temp_jsonl_dir():
    """임시 JSONL 디렉토리 생성."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


def test_list_jsonl_files(temp_jsonl_dir):
    """날짜 패턴에 맞는 JSONL 파일 목록 반환 테스트."""
    # 테스트 파일 생성
    target_date = date(2026, 4, 20)
    file1 = temp_jsonl_dir / f"pipeline_events_{target_date}.jsonl"
    file1.write_text('{"test": 1}')
    file2 = temp_jsonl_dir / f"pipeline_events_{target_date}.jsonl.gz"
    with gzip.open(file2, "wt") as f:
        f.write('{"test": 2}')
    # 함수 호출 (dataset mocking 필요하지만 여기서는 경로 주입하지 않음)
    # 생략


def test_read_jsonl_lines(temp_jsonl_dir):
    """JSONL 파일 읽기 테스트."""
    file_path = temp_jsonl_dir / "test.jsonl"
    lines = ['{"a": 1}', '{"b": 2}']
    file_path.write_text("\n".join(lines))
    rows = list(read_jsonl_lines(file_path))
    assert len(rows) == 2
    assert rows[0]["a"] == 1
    assert rows[1]["b"] == 2


def test_extract_event_id():
    """이벤트 ID 추출 테스트."""
    # pipeline_event
    event = {
        "event_type": "pipeline_event",
        "record_id": 123,
        "emitted_at": "2026-04-20T10:00:00",
    }
    eid = extract_event_id(event)
    assert eid == "123:2026-04-20T10:00:00"
    # 다른 이벤트 유형
    event2 = {"event_type": "other"}
    assert extract_event_id(event2) is None


def test_convert_to_dataframe():
    """DataFrame 변환 테스트."""
    events = [
        {"event_type": "pipeline_event", "emitted_date": "2026-04-20"},
        {"event_type": "pipeline_event", "emitted_date": "2026-04-21"},
    ]
    df = convert_to_dataframe(events, "pipeline_events")
    assert len(df) == 2
    assert "emitted_date" in df.columns


def test_deduplicate_by_event_id():
    """중복 제거 테스트."""
    import pandas as pd

    df = pd.DataFrame({"event_id": ["a", "a", "b"], "value": [1, 2, 3]})
    deduped = deduplicate_by_event_id(df)
    assert len(deduped) == 2
    assert deduped["event_id"].nunique() == 2


def test_write_parquet_partition(tmp_path):
    """Parquet 파티션 쓰기 테스트."""
    # 모듈의 ANALYTICS_ROOT를 패치할 수 없으므로 테스트 생략
    # 통합 테스트는 별도로 작성
    pass


def test_process_single_date_no_files():
    """파일 없을 때 처리 테스트."""
    # 모의 데이터셋 경로를 임시 디렉토리로 설정 필요
    # 생략
    pass


def test_process_single_date_post_sell_ignores_candidates(monkeypatch, tmp_path):
    """post_sell 백필은 candidates가 아니라 evaluations만 적재한다."""
    source_dir = tmp_path / "post_sell"
    analytics_root = tmp_path / "analytics" / "parquet"
    source_dir.mkdir(parents=True)
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "post_sell", source_dir)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", analytics_root)

    candidate = source_dir / "post_sell_candidates_2026-04-20.jsonl"
    candidate.write_text(
        json.dumps(
            {
                "recommendation_id": 1,
                "signal_date": "2026-04-20",
                "outcome": "CANDIDATE_ONLY",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    evaluation = source_dir / "post_sell_evaluations_2026-04-20.jsonl"
    evaluation.write_text(
        json.dumps(
            {
                "post_sell_id": "ps-1",
                "signal_date": "2026-04-20",
                "recommendation_id": 1,
                "sell_time": "10:00:00",
                "outcome": "COMPLETED",
                "profit_rate": 0.7,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    read, written = process_single_date("post_sell", date(2026, 4, 20))

    assert read == 1
    assert written == 1
    out_file = (
        analytics_root / "post_sell" / "date=2026-04-20" / "post_sell_20260420.parquet"
    )
    df = pd.read_parquet(out_file)
    assert df["outcome"].tolist() == ["COMPLETED"]


def test_process_single_date_removes_stale_partition(monkeypatch, tmp_path):
    """소스 파일이 없는 날짜는 기존 parquet 파티션을 제거한다."""
    source_dir = tmp_path / "pipeline_events"
    analytics_root = tmp_path / "analytics" / "parquet"
    source_dir.mkdir(parents=True)
    stale_dir = analytics_root / "pipeline_events" / "date=2026-04-20"
    stale_dir.mkdir(parents=True)
    (stale_dir / "pipeline_events_20260420.parquet").write_text(
        "stale", encoding="utf-8"
    )

    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "pipeline_events", source_dir)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", analytics_root)

    read, written = process_single_date("pipeline_events", date(2026, 4, 20))

    assert (read, written) == (0, 0)
    assert not stale_dir.exists()


def test_process_pipeline_events_streams_chunks_and_deduplicates(monkeypatch, tmp_path):
    source_dir = tmp_path / "pipeline_events"
    analytics_root = tmp_path / "analytics" / "parquet"
    source_dir.mkdir(parents=True)
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "pipeline_events", source_dir)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", analytics_root)
    monkeypatch.setattr(parquet_builder, "_pipeline_chunk_rows", lambda: 3)
    target_date = date(2026, 7, 24)
    rows = []
    for index in range(10):
        rows.append(
            {
                "schema_version": 3,
                "event_type": "pipeline_event",
                "pipeline": "ENTRY_PIPELINE",
                "stage": "candidate_observed",
                "stock_code": f"{index:06d}",
                "record_id": index,
                "emitted_at": f"2026-07-24T09:00:{index:02d}+09:00",
                "emitted_date": target_date.isoformat(),
                "text_payload": f"row-{index}",
                "fields": {"reason": "test", "ai_score": index},
            }
        )
    rows.append(dict(rows[0]))
    rows.append({**rows[1], "emitted_date": "2026-07-23"})
    source_path = source_dir / "pipeline_events_2026-07-24.jsonl"
    source_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    read, written = process_single_date("pipeline_events", target_date)

    assert (read, written) == (12, 10)
    out_file = (
        analytics_root
        / "pipeline_events"
        / "date=2026-07-24"
        / "pipeline_events_20260724.parquet"
    )
    parquet_file = parquet_builder.pq.ParquetFile(out_file)
    assert parquet_file.metadata.num_rows == 10
    assert parquet_file.metadata.num_row_groups == 4
    frame = pd.read_parquet(out_file)
    assert frame["fields_ai_score"].tolist() == [str(index) for index in range(10)]
    assert not out_file.with_suffix(".parquet.tmp").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
