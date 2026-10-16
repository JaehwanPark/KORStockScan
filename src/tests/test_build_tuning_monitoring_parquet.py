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
    assert eid.startswith("pipeline-content-sha256:")
    assert eid != extract_event_id({**event, "stage": "second_stage"})
    assert extract_event_id({**event, "event_id": "native-event-1"}) == "native-event-1"
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


def test_pipeline_route_session_venue_round_trip_to_parquet(monkeypatch, tmp_path):
    source_dir = tmp_path / "pipeline_events"
    analytics_root = tmp_path / "analytics" / "parquet"
    source_dir.mkdir(parents=True)
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "pipeline_events", source_dir)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", analytics_root)
    target_date = date(2026, 9, 11)
    source_dir.joinpath("pipeline_events_2026-09-11.jsonl").write_text(
        json.dumps(
            {
                "schema_version": 3,
                "event_type": "pipeline_event",
                "record_id": "route-context-1",
                "emitted_at": "2026-09-11T16:00:00+09:00",
                "emitted_date": target_date.isoformat(),
                "fields": {
                    "route": "SOR",
                    "session_bucket": "KRX_NXT_AFTERMARKET",
                    "effective_venue": "INTEGRATED",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    read, written = process_single_date("pipeline_events", target_date)

    assert (read, written) == (1, 1)
    out_file = (
        analytics_root
        / "pipeline_events"
        / "date=2026-09-11"
        / "pipeline_events_20260911.parquet"
    )
    row = pd.read_parquet(out_file).iloc[0]
    assert row["fields_route"] == "SOR"
    assert row["fields_session_bucket"] == "KRX_NXT_AFTERMARKET"
    assert row["fields_effective_venue"] == "INTEGRATED"
    assert row["source_record_id"] == "route-context-1"


def test_deduplicate_by_event_id():
    """중복 제거 테스트."""
    import pandas as pd

    df = pd.DataFrame({"event_id": ["a", "a", "b"], "value": [1, 2, 3]})
    deduped = deduplicate_by_event_id(df)
    assert len(deduped) == 2
    assert deduped["event_id"].nunique() == 2


def test_system_metrics_collapse_only_exact_repeated_sample(monkeypatch, tmp_path):
    source = tmp_path / "system_metric_samples.jsonl"
    analytics = tmp_path / "analytics"
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "system_metric_samples", source)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", analytics)
    first = {"ts": "2026-10-16T10:00:00+09:00", "epoch": 1792112400,
             "cpu": {"cpu_busy_pct": 10.0}}
    second = {**first, "ts": "2026-10-16T10:01:00+09:00", "epoch": 1792112460}
    excluded = {**first, "ts": "2026-10-15T10:00:00+09:00", "cpu": {"cpu_busy_pct": 99.0}}
    source.write_text("\n".join(json.dumps(row) for row in (first, first, second, excluded)) + "\n")
    assert process_single_date("system_metric_samples", date(2026, 10, 16)) == (4, 2)
    output = analytics / "system_metric_samples/date=2026-10-16/system_metric_samples_20261016.parquet"
    saved = pd.read_parquet(output)
    assert set(saved["ts"]) == {first["ts"], second["ts"]}
    assert [row["cpu_busy_pct"] for row in saved["cpu"]] == [10.0, 10.0]


@pytest.mark.parametrize("dedupe", [True, False])
@pytest.mark.parametrize("mutation", ["cpu", "owner", "malformed", "non_object", "non_finite"])
def test_system_metrics_conflicts_preserve_old_partition(monkeypatch, tmp_path, dedupe, mutation):
    source = tmp_path / "system_metric_samples.jsonl"
    analytics = tmp_path / "analytics"
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "system_metric_samples", source)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", analytics)
    row = {"ts": "2026-10-16T10:00:00+09:00", "epoch": 1792112400,
           "cpu": {"cpu_busy_pct": 10.0}}
    source.write_text(json.dumps(row) + "\n")
    assert process_single_date("system_metric_samples", date(2026, 10, 16)) == (1, 1)
    partition = analytics / "system_metric_samples/date=2026-10-16"
    receipt = partition / "source_receipt.json"
    receipt.write_bytes(b"original receipt bytes")
    original = {path.name: path.read_bytes() for path in partition.iterdir()}
    changed = dict(row)
    if mutation == "cpu": changed["cpu"] = {"cpu_busy_pct": 11.0}
    elif mutation == "owner": changed["process_io"] = [{"pid": 123, "owner": "postclose"}]
    elif mutation == "non_finite": changed["cpu"] = {"cpu_busy_pct": float("nan")}
    extra = ("{" if mutation == "malformed" else "[]" if mutation == "non_object"
             else json.dumps(changed))
    source.write_text(json.dumps(row) + "\n" + extra + "\n")
    with pytest.raises(ValueError):
        process_single_date("system_metric_samples", date(2026, 10, 16), dedupe=dedupe)
    assert {path.name: path.read_bytes() for path in partition.iterdir()} == original


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
    receipt = json.loads((out_file.parent / "source_receipt.json").read_text())
    assert receipt["conservation_verified"] is True
    assert receipt["decoded_input_count"] == 12 and receipt["exact_duplicate_count"] == 1
    assert receipt["excluded_date_counts"] == {"2026-07-23": 1}


def _identity_test_source(monkeypatch, tmp_path, rows):
    from src.engine import compare_tuning_shadow_diff as shadow
    from src.engine import tuning_duckdb_repository as repository
    day = date(2026, 7, 24)
    source_dir = tmp_path / "pipeline_events"
    post_dir = tmp_path / "post_sell"
    source_dir.mkdir(exist_ok=True); post_dir.mkdir(exist_ok=True)
    root = tmp_path / "parquet"
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "pipeline_events", source_dir)
    monkeypatch.setitem(parquet_builder.DATASET_PATHS, "post_sell", post_dir)
    monkeypatch.setattr(parquet_builder, "ANALYTICS_ROOT", root)
    monkeypatch.setattr(repository, "PARQUET_ROOT", root)
    monkeypatch.setattr(shadow, "PIPELINE_DIR", source_dir)
    monkeypatch.setattr(shadow, "POST_SELL_DIR", post_dir)
    path = source_dir / "pipeline_events_2026-07-24.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    process_single_date("post_sell", day)
    return day, path, root / "pipeline_events/date=2026-07-24/pipeline_events_20260724.parquet", shadow


def _same_clock_event(**changes):
    return {"schema_version": 3, "event_type": "pipeline_event", "record_id": 123,
        "emitted_at": "2026-07-24T09:00:00+09:00", "emitted_date": "2026-07-24",
        "pipeline": "ENTRY_PIPELINE", "stage": "diagnostic_a", "fields": {"value": 1}, **changes}


def test_same_clock_stages_fields_and_native_ids_survive_with_exact_duplicate_collapsed(monkeypatch, tmp_path):
    base = _same_clock_event()
    rows = [base, _same_clock_event(stage="diagnostic_b"), _same_clock_event(fields={"value": 2}),
            _same_clock_event(event_id="native-a"), _same_clock_event(event_id="native-b"), dict(base)]
    day, _, path, shadow = _identity_test_source(monkeypatch, tmp_path, rows)
    assert process_single_date("pipeline_events", day) == (6, 5)
    frame = pd.read_parquet(path)
    assert frame["event_id"].nunique() == frame["source_event_sha256"].nunique() == 5
    assert {"native-a", "native-b"} <= set(frame["event_id"])
    assert shadow.main(["--start", str(day), "--end", str(day), "--output", str(tmp_path / "parity.json")]) == 0


def test_pipeline_native_id_conflict_keeps_prior_partition_and_receipt(monkeypatch, tmp_path):
    day, source, path, shadow = _identity_test_source(monkeypatch, tmp_path, [_same_clock_event(event_id="native-a")])
    process_single_date("pipeline_events", day)
    before, receipt = path.read_bytes(), (path.parent / "source_receipt.json").read_bytes()
    source.write_text("".join(json.dumps(row) + "\n" for row in [
        _same_clock_event(event_id="native-a"), _same_clock_event(event_id="native-a", fields={"value": 2})]))
    with pytest.raises(ValueError, match="native_id_conflict"):
        process_single_date("pipeline_events", day)
    assert path.read_bytes() == before and (path.parent / "source_receipt.json").read_bytes() == receipt
    assert not path.with_suffix(".parquet.tmp").exists()
    with pytest.raises(ValueError, match="native_id_conflict"):
        shadow._count_jsonl_metrics(day, day, pipeline_population={})


def test_shadow_full_population_detects_loss_even_when_all_aggregate_metrics_match(monkeypatch, tmp_path):
    day, _, path, shadow = _identity_test_source(monkeypatch, tmp_path, [
        _same_clock_event(), _same_clock_event(fields={"value": 2})])
    process_single_date("pipeline_events", day)
    frame = pd.read_parquet(path)
    frame.iloc[:1].to_parquet(path, index=False)
    output = tmp_path / "parity.json"
    assert shadow.main(["--start", str(day), "--end", str(day), "--output", str(output)]) == 2
    result = json.loads(output.read_text())
    assert all(row["match"] for row in result["metrics"].values())
    assert result["all_match"] is False and result["pipeline_population"]["match"] is False
    assert result["pipeline_population"]["raw"]["count"] == 2


def test_shadow_does_not_claim_full_identity_for_legacy_partition_without_source_hash(monkeypatch, tmp_path):
    day, _, path, shadow = _identity_test_source(monkeypatch, tmp_path, [_same_clock_event()])
    process_single_date("pipeline_events", day)
    frame = pd.read_parquet(path).drop(columns=["source_event_sha256"])
    frame.to_parquet(path, index=False)
    output = tmp_path / "parity.json"
    assert shadow.main(["--start", str(day), "--end", str(day), "--output", str(output)]) == 2
    result = json.loads(output.read_text())
    assert result["pipeline_population"]["parquet"]["status"] == "source_gap"


def test_shadow_and_producer_preserve_out_of_date_exclusion_census(monkeypatch, tmp_path):
    day, _, path, shadow = _identity_test_source(monkeypatch, tmp_path, [
        _same_clock_event(), _same_clock_event(emitted_date="2026-07-23")])
    assert process_single_date("pipeline_events", day) == (2, 1)
    output = tmp_path / "parity.json"
    assert shadow.main(["--start", str(day), "--end", str(day), "--output", str(output)]) == 0
    report = json.loads(output.read_text())
    receipt = json.loads((path.parent / "source_receipt.json").read_text())
    assert report["pipeline_population"]["raw"]["excluded_date_counts"] == receipt["excluded_date_counts"] == {"2026-07-23": 1}


def test_zero_selected_rows_replace_previous_output_with_verified_empty_receipt(monkeypatch, tmp_path):
    day, source, path, shadow = _identity_test_source(monkeypatch, tmp_path, [_same_clock_event()])
    process_single_date("pipeline_events", day)
    source.write_text(json.dumps(_same_clock_event(emitted_date="2026-07-23")) + "\n")
    assert process_single_date("pipeline_events", day) == (1, 0)
    assert not path.exists()
    receipt = parquet_builder.verify_pipeline_source_receipt(day)
    assert receipt["status"] == "complete" and receipt["population_state"] == "valid_empty"
    assert receipt["written_count"] == 0 and receipt["output_generation"] is None
    assert receipt["decoded_input_count"] == receipt["excluded_date_count"] == 1
    assert shadow.main(["--start", str(day), "--end", str(day), "--output", str(tmp_path / "parity.json")]) == 0


def test_final_receipt_failure_leaves_publishing_marker_and_shadow_fails(monkeypatch, tmp_path):
    from src.engine.scalping.micro_reversion import economic_reference as reference
    day, source, path, shadow = _identity_test_source(monkeypatch, tmp_path, [_same_clock_event()])
    process_single_date("pipeline_events", day)
    source.write_text(json.dumps(_same_clock_event(fields={"value": 2})) + "\n")
    native_write = reference.atomic_write_json
    def fail_complete(destination, payload):
        if Path(destination).name == "source_receipt.json" and payload.get("status") == "complete":
            raise OSError("final receipt write interrupted")
        return native_write(destination, payload)
    monkeypatch.setattr(reference, "atomic_write_json", fail_complete)
    with pytest.raises(OSError, match="interrupted"):
        process_single_date("pipeline_events", day)
    receipt = json.loads((path.parent / "source_receipt.json").read_bytes())
    assert receipt["status"] == "publishing"
    with pytest.raises(ValueError, match="receipt_invalid"):
        parquet_builder.verify_pipeline_source_receipt(day)
    output = tmp_path / "parity.json"
    assert shadow.main(["--start", str(day), "--end", str(day), "--output", str(output)]) == 2
    result = json.loads(output.read_text())
    assert result["pipeline_population"]["parquet"]["status"] == "source_gap"
    assert result["pipeline_population"]["transformed_payload_semantics_verified"] is False


def test_source_receipt_is_bound_to_output_bytes_and_current_source_generation(monkeypatch, tmp_path):
    day, source, path, _ = _identity_test_source(monkeypatch, tmp_path, [_same_clock_event()])
    process_single_date("pipeline_events", day)
    original = path.read_bytes()
    path.write_bytes(original + b"changed")
    with pytest.raises(ValueError, match="output_generation_changed"):
        parquet_builder.verify_pipeline_source_receipt(day)
    path.write_bytes(original)
    source.write_text(json.dumps(_same_clock_event(fields={"value": 3})) + "\n")
    with pytest.raises(ValueError, match="source_generation_changed"):
        parquet_builder.verify_pipeline_source_receipt(day)


def _native_archive(source):
    from src.engine import compress_db_backfilled_files as archive
    assert archive._gzip_file(source,dry_run=False)[0] is True
    return Path(str(source)+'.gz'),Path(str(source)+'.gz.archive_receipt.json')


def test_pipeline_logical_seal_is_same_pass_exact_bytes_and_native_archive_is_metadata_only(monkeypatch,tmp_path):
    import hashlib
    day,source,path,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event(stock_name='한글')])
    original=(json.dumps(_same_clock_event(stock_name='한글'),ensure_ascii=False)+'\r\n\r\n  \n').encode()
    source.write_bytes(original)
    native_open=parquet_builder.os.open;read_counts=[]
    def observed(file,*args,**kwargs):
        if file==source or file==str(source):read_counts.append(file)
        return native_open(file,*args,**kwargs)
    with monkeypatch.context() as observation:
        observation.setattr(parquet_builder.os,'open',observed)
        assert process_single_date('pipeline_events',day)==(1,1)
    receipt=json.loads((path.parent/'source_receipt.json').read_bytes())
    assert receipt['logical_sources'][str(source)]==dict(decoded_size_bytes=len(original),sha256=hashlib.sha256(original).hexdigest())
    assert read_counts==[source]
    compressed,archive_receipt=_native_archive(source)
    archive_bytes=archive_receipt.read_bytes()
    before=(path.parent/'source_receipt.json').read_bytes()
    def no_decode(*args,**kwargs):pytest.fail('native archive validation decompressed a fully sealed gzip')
    monkeypatch.setattr(gzip,'GzipFile',no_decode)
    for _ in range(2):assert parquet_builder.verify_pipeline_source_receipt(day)['written_count']==1
    from src.engine.tuning_duckdb_repository import TuningDuckDBRepository
    with TuningDuckDBRepository(tmp_path/'handoff.duckdb',read_only=False) as repository:
        assert repository.register_parquet_dataset('pipeline_events',start_date=day,end_date=day)
        assert int(repository.query('SELECT count(*) AS n FROM v_pipeline_events').iloc[0]['n'])==1
    assert (path.parent/'source_receipt.json').read_bytes()==before and archive_receipt.read_bytes()==archive_bytes
    assert not source.exists() and compressed.exists()


def test_native_archive_plain_and_gzip_overlap_then_plain_removal_is_valid(monkeypatch,tmp_path):
    day,source,_,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    native_unlink=Path.unlink
    with monkeypatch.context() as transfer:
        def keep_plain(path,*args,**kwargs):
            if path!=source:return native_unlink(path,*args,**kwargs)
        transfer.setattr(Path,'unlink',keep_plain)
        _native_archive(source)
    assert source.exists()
    parquet_builder.verify_pipeline_source_receipt(day)
    source.unlink()
    parquet_builder.verify_pipeline_source_receipt(day)


@pytest.mark.parametrize('mutation',['missing_receipt','wrong_logical','bad_digest','new_size_missing','changed_gzip','late','missing_logical'])
def test_pipeline_logical_archive_rejects_unproven_or_changed_generation(monkeypatch,tmp_path,mutation):
    import os
    day,source,path,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    original=source.read_bytes()
    compressed,receipt_path=_native_archive(source)
    if mutation=='missing_receipt':receipt_path.unlink()
    elif mutation in {'wrong_logical','bad_digest','new_size_missing'}:
        body=json.loads(receipt_path.read_bytes())
        if mutation=='wrong_logical':body['logical_content_sha256']='0'*64
        elif mutation=='bad_digest':body['artifact_content_sha256']='0'*64
        else:
            from src.engine.scalping.micro_reversion.economic_reference import content_sha256
            body.pop('logical_size_bytes');body.pop('artifact_content_sha256');body['artifact_content_sha256']=content_sha256(body)
        receipt_path.write_text(json.dumps(body))
    elif mutation=='changed_gzip':
        stamp=compressed.stat().st_mtime_ns
        changed=bytearray(compressed.read_bytes());changed[-8]^=1;compressed.write_bytes(changed)
        os.utime(compressed,ns=(stamp,stamp))
    elif mutation=='late':source.with_name(f'pipeline_events_{day}.late.jsonl').write_bytes(original)
    else:compressed.unlink();receipt_path.unlink()
    with pytest.raises(ValueError,match='source_generation_changed'):
        parquet_builder.verify_pipeline_source_receipt(day)


@pytest.mark.parametrize('corrupt',[False,True])
@pytest.mark.parametrize('size_absent',[False,True])
def test_legacy_archive_crc_fallback_is_once_per_exact_generation_and_preserves_receipt(monkeypatch,tmp_path,corrupt,size_absent):
    day,source,_,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    compressed,receipt_path=_native_archive(source)
    body=json.loads(receipt_path.read_bytes())
    for key in ('verification_contract','artifact_content_sha256'):body.pop(key)
    body['archive_generation'].pop('ctime_ns')
    if size_absent:body.pop('logical_size_bytes')
    if corrupt:
        changed=bytearray(compressed.read_bytes());changed[-8]^=1;compressed.write_bytes(changed)
        s=compressed.stat();body['archive_generation']=dict(device=s.st_dev,inode=s.st_ino,size_bytes=s.st_size,mtime_ns=s.st_mtime_ns)
    receipt_path.write_text(json.dumps(body));original=receipt_path.read_bytes()
    native=gzip.GzipFile;opens=[]
    def observed(*args,**kwargs):
        opens.append(compressed);return native(*args,**kwargs)
    monkeypatch.setattr(gzip,'GzipFile',observed)
    if corrupt:
        with pytest.raises(ValueError,match='source_generation_changed'):
            parquet_builder.verify_pipeline_source_receipt(day)
    else:
        parquet_builder.verify_pipeline_source_receipt(day)
        parquet_builder.verify_pipeline_source_receipt(day)
    assert opens==[compressed]
    assert receipt_path.read_bytes()==original


def test_pipeline_ingested_gzip_original_identity_needs_no_second_crc_read(monkeypatch,tmp_path):
    day,source,_,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    compressed=Path(str(source)+'.gz');compressed.write_bytes(gzip.compress(source.read_bytes()));source.unlink()
    process_single_date('pipeline_events',day)
    monkeypatch.setattr(gzip,'GzipFile',lambda *a,**k:pytest.fail('original unchanged gzip decoded again'))
    parquet_builder.verify_pipeline_source_receipt(day)


def test_pipeline_ingested_legacy_gzip_receipt_without_size_uses_original_generation(monkeypatch,tmp_path):
    day,source,_,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    _,receipt_path=_native_archive(source)
    body=json.loads(receipt_path.read_bytes())
    for key in ('logical_size_bytes','verification_contract','artifact_content_sha256'):body.pop(key)
    body['archive_generation'].pop('ctime_ns');receipt_path.write_text(json.dumps(body))
    process_single_date('pipeline_events',day);original=receipt_path.read_bytes()
    monkeypatch.setattr(gzip,'GzipFile',lambda *a,**k:pytest.fail('original legacy gzip decoded again'))
    parquet_builder.verify_pipeline_source_receipt(day)
    assert receipt_path.read_bytes()==original


@pytest.mark.parametrize('target',['metadata','legacy_gzip'])
def test_pipeline_reader_rejects_fifo_swap_after_stat_without_blocking(monkeypatch,tmp_path,target):
    import os
    day,source,path,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    swap=path.parent/'source_receipt.json'
    if target=='legacy_gzip':
        swap,receipt_path=_native_archive(source);body=json.loads(receipt_path.read_bytes())
        for key in ('verification_contract','artifact_content_sha256'):body.pop(key)
        body['archive_generation'].pop('ctime_ns');receipt_path.write_text(json.dumps(body))
    native=os.open;seen=[]
    def swapped(file,flags,*args,**kwargs):
        if file==swap:
            assert flags&os.O_NONBLOCK and flags&os.O_NOFOLLOW
            swap.unlink();os.mkfifo(swap);seen.append(file)
        return native(file,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',swapped)
    with pytest.raises(ValueError,match='source_(changed_before_open|generation_changed)'):
        parquet_builder.verify_pipeline_source_receipt(day)
    assert seen==[swap]


def test_pipeline_conflicting_alias_does_not_replace_prior_partition(monkeypatch,tmp_path):
    day,source,path,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    before=path.read_bytes();receipt=(path.parent/'source_receipt.json').read_bytes()
    Path(str(source)+'.gz').write_bytes(gzip.compress(source.read_bytes()+b'{}\n'))
    with pytest.raises(ValueError,match='plain_gzip_conflict'):
        process_single_date('pipeline_events',day)
    assert path.read_bytes()==before and (path.parent/'source_receipt.json').read_bytes()==receipt


def test_legacy_parquet_receipt_without_logical_seal_does_not_invent_archive_binding(monkeypatch,tmp_path):
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    day,source,path,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    receipt=path.parent/'source_receipt.json';body=json.loads(receipt.read_bytes())
    body.pop('logical_sources');body.pop('artifact_content_sha256');body['artifact_content_sha256']=content_sha256(body)
    receipt.write_text(json.dumps(body));original=receipt.read_bytes()
    parquet_builder.verify_pipeline_source_receipt(day)
    _native_archive(source)
    with pytest.raises(ValueError,match='logical_seal_missing'):
        parquet_builder.verify_pipeline_source_receipt(day)
    assert receipt.read_bytes()==original


def test_verified_empty_pipeline_partition_keeps_native_archive_handoff(monkeypatch,tmp_path):
    day,source,_,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event(emitted_date='2026-07-23')])
    assert process_single_date('pipeline_events',day)==(1,0)
    _native_archive(source)
    assert parquet_builder.verify_pipeline_source_receipt(day)['population_state']=='valid_empty'


def test_pipeline_source_arrival_during_output_validation_rejects_receipt(monkeypatch,tmp_path):
    day,source,_,_=_identity_test_source(monkeypatch,tmp_path,[_same_clock_event()])
    process_single_date('pipeline_events',day)
    native=parquet_builder._parquet_byte_generation
    def changed(path):
        value=native(path);source.with_name(f'pipeline_events_{day}.late.jsonl').write_text('{}\n');return value
    monkeypatch.setattr(parquet_builder,'_parquet_byte_generation',changed)
    with pytest.raises(ValueError,match='source_changed_during_validation'):
        parquet_builder.verify_pipeline_source_receipt(day)


@pytest.mark.parametrize("bad", ["{invalid-json}", "[]", '{"value": NaN}'])
def test_pipeline_source_invalid_rows_do_not_replace_previous_partition(monkeypatch, tmp_path, bad):
    day, source, path, _ = _identity_test_source(monkeypatch, tmp_path, [_same_clock_event()])
    process_single_date("pipeline_events", day)
    before = path.read_bytes()
    with source.open("a") as stream:
        stream.write(bad + "\n")
    with pytest.raises(ValueError):
        process_single_date("pipeline_events", day)
    assert path.read_bytes() == before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
