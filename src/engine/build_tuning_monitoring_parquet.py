"""튜닝 모니터링 로그 JSONL → Parquet 변환 파이프라인.

Raw Layer (JSONL)을 읽어 Analytics Layer (Parquet)로 변환하며,
중복 방지 키(`event_id` 또는 복합키) 기준 dedupe 지원.

사용 예:
    python -m src.engine.build_tuning_monitoring_parquet \\
        --dataset pipeline_events \\
        --start 2026-04-01 \\
        --end 2026-04-20

    python -m src.engine.build_tuning_monitoring_parquet \\
        --dataset post_sell \\
        --single-date 2026-04-20
"""

from __future__ import annotations

import argparse
import gzip
import json
import hashlib
import logging
import os
import shutil
import zlib
import stat
from contextlib import contextmanager, ExitStack
from functools import lru_cache
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from src.utils.constants import DATA_DIR, LOGS_DIR

logger = logging.getLogger(__name__)

# 데이터셋별 소스 경로
DATASET_PATHS = {
    "pipeline_events": DATA_DIR / "pipeline_events",
    "post_sell": DATA_DIR / "post_sell",
    "system_metric_samples": LOGS_DIR / "system_metric_samples.jsonl",
}

# Parquet 출력 루트
ANALYTICS_ROOT = DATA_DIR / "analytics" / "parquet"

# pipeline_events에서 분석에 필요한 필드만 평탄화해 메모리 사용량을 억제한다.
PIPELINE_FIELD_KEYS = [
    # Preserve the execution-context tuple alongside analytics fields.  These
    # originate in the JSONL event's `fields` object and remain strings in the
    # fixed Arrow schema, allowing lossless JSONL -> Parquet round trips.
    "route",
    "session_bucket",
    "effective_venue",
    "overbought_blocked",
    "fill_quality",
    "entry_mode",
    "cum_filled_qty",
    "requested_qty",
    "remaining_qty",
    "fill_qty",
    "exit_rule",
    "ai_score",
    "reason",
]
PIPELINE_PARQUET_CHUNK_ROWS = 5000


def list_jsonl_files(dataset: str, target_date: date) -> List[Path]:
    """지정 날짜에 해당하는 JSONL 파일 목록을 반환."""
    src_path = DATASET_PATHS[dataset]
    if dataset == "system_metric_samples":
        # 단일 파일이므로 날짜에 관계없이 전체 파일 반환
        if src_path.exists():
            return [src_path]
        return []
    if dataset == "post_sell":
        pattern = f"post_sell_evaluations*{target_date.strftime('%Y-%m-%d')}*.jsonl"
        files = list(src_path.glob(pattern))
        gz_pattern = (
            f"post_sell_evaluations*{target_date.strftime('%Y-%m-%d')}*.jsonl.gz"
        )
        files.extend(src_path.glob(gz_pattern))
        return sorted(files)
    # pipeline_events: 날짜 패턴 매칭
    pattern = f"*{target_date.strftime('%Y-%m-%d')}*.jsonl"
    files = list(src_path.glob(pattern))
    # .gz 확장자도 포함
    gz_pattern = f"*{target_date.strftime('%Y-%m-%d')}*.jsonl.gz"
    files.extend(src_path.glob(gz_pattern))
    return sorted(files)


def read_jsonl_lines(
    file_path: Path, *, strict: bool = False, logical_generation: dict | None = None,
) -> Iterator[Dict[str, Any]]:
    """JSONL 파일을 줄 단위로 읽어 dict 생성."""
    logical_sha = hashlib.sha256()
    decoded_size = 0
    with ExitStack() as stack:
        raw_source=stack.enter_context(_open_regular_source(file_path))
        f=(stack.enter_context(gzip.GzipFile(fileobj=raw_source,mode='rb'))
           if file_path.suffix=='.gz' else raw_source)
        for raw in f:
            if logical_generation is not None:
                logical_sha.update(raw)
                decoded_size += len(raw)
            line = raw.decode('utf-8').strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if strict and not isinstance(event, dict):
                    raise ValueError("pipeline_parquet_source_non_object")
                yield event
            except json.JSONDecodeError as e:
                if strict:
                    raise ValueError("pipeline_parquet_source_json_invalid") from e
                logger.warning("JSON decode error in %s: %s", file_path, e)
    if logical_generation is not None:
        logical_generation.update(decoded_size_bytes=decoded_size, sha256=logical_sha.hexdigest())


def extract_event_id(
    event: Dict[str, Any], *, source_payload_sha256: str | None = None
) -> Optional[str]:
    """이벤트 고유 ID 생성. 중복 제거용."""
    # A record can emit several stages or changed observations at one clock.
    # Native IDs retain their identity; absent IDs dedupe complete equal rows.
    if event.get("event_type") == "pipeline_event":
        native = event.get("event_id")
        if native is not None:
            if not isinstance(native, str) or not native.strip():
                raise ValueError("pipeline_event_native_id_invalid")
            return native
        return "pipeline-content-sha256:" + (source_payload_sha256 or pipeline_event_payload_sha256(event))
    # system metric 샘플은 ts 또는 epoch를 사용
    ts = event.get("ts")
    if ts:
        return f"system_metric:{ts}"
    epoch = event.get("epoch")
    if epoch is not None:
        return f"system_metric:{epoch}"
    post_sell_id = event.get("post_sell_id")
    if post_sell_id:
        return f"post_sell:{post_sell_id}"
    recommendation_id = event.get("recommendation_id")
    signal_date = event.get("signal_date")
    sell_time = event.get("sell_time")
    if recommendation_id is not None and signal_date and sell_time:
        return f"post_sell:{recommendation_id}:{signal_date}:{sell_time}"
    # 다른 이벤트 유형은 필요에 따라 확장
    # fallback: 전체 JSON 해시 또는 None (중복 방지 불가)
    return None


def pipeline_event_payload_sha256(event: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        event, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()


def convert_to_dataframe(events: List[Dict[str, Any]], dataset: str) -> pd.DataFrame:
    """이벤트 리스트를 Pandas DataFrame으로 변환."""
    if not events:
        return pd.DataFrame()
    if dataset == "pipeline_events":
        rows: List[Dict[str, Any]] = []
        for event in events:
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            row: Dict[str, Any] = {
                "schema_version": event.get("schema_version"),
                "event_type": event.get("event_type"),
                "pipeline": event.get("pipeline"),
                "stage": event.get("stage"),
                "stock_name": event.get("stock_name"),
                "stock_code": event.get("stock_code"),
                "record_id": event.get("record_id"),
                "emitted_at": event.get("emitted_at"),
                "emitted_date": event.get("emitted_date"),
                "text_payload": event.get("text_payload"),
                "event_id": event.get("event_id"),
                "fields_json": (
                    json.dumps(fields, ensure_ascii=False) if fields else None
                ),
            }
            for key in PIPELINE_FIELD_KEYS:
                row[f"fields_{key}"] = fields.get(key)
            rows.append(row)
        df = pd.DataFrame(rows)
    elif dataset == "post_sell":
        rows = []
        for event in events:
            row = {
                "post_sell_id": event.get("post_sell_id"),
                "evaluated_at": event.get("evaluated_at"),
                "signal_date": event.get("signal_date"),
                "stock_code": event.get("stock_code"),
                "stock_name": event.get("stock_name"),
                "recommendation_id": event.get("recommendation_id"),
                "strategy": event.get("strategy"),
                "position_tag": event.get("position_tag"),
                "sell_time": event.get("sell_time"),
                "sell_bucket": event.get("sell_bucket"),
                "buy_price": event.get("buy_price"),
                "sell_price": event.get("sell_price"),
                "profit_rate": event.get("profit_rate"),
                "buy_qty": event.get("buy_qty"),
                "exit_rule": event.get("exit_rule"),
                "revive": event.get("revive"),
                "outcome": event.get("outcome"),
                "event_id": event.get("event_id"),
            }
            rows.append(row)
        df = pd.DataFrame(rows)
    else:
        # system_metric_samples는 필드 수가 제한적이므로 전체 컬럼 유지
        df = pd.DataFrame(events)
    # 날짜 필드 추가 (타겟 날짜 파티션용)
    # emitted_date 또는 target_date 사용
    if "emitted_date" in df.columns:
        df["emitted_date"] = pd.to_datetime(df["emitted_date"], errors="coerce").dt.date
        df = df[df["emitted_date"].notna()]
    elif "event_date" in df.columns:
        df["emitted_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date
        df = df[df["emitted_date"].notna()]
    elif dataset == "post_sell" and "signal_date" in df.columns:
        df["emitted_date"] = pd.to_datetime(df["signal_date"], errors="coerce").dt.date
        df = df[df["emitted_date"].notna()]
    elif dataset == "system_metric_samples" and "ts" in df.columns:
        # system metric은 ts(ISO8601) 기준으로 날짜 파티션을 만든다.
        df["emitted_date"] = pd.to_datetime(df["ts"], errors="coerce").dt.date
        df = df[df["emitted_date"].notna()]
    else:
        # 파티션을 위해 날짜 열 추가 (데이터셋별 처리 필요)
        pass
    return df


def convert_pipeline_event_to_row(event: Dict[str, Any]) -> Dict[str, Any]:
    """pipeline_event 원본을 분석용 축소 row로 변환한다."""
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    row: Dict[str, Any] = {
        "schema_version": event.get("schema_version"),
        "event_type": event.get("event_type"),
        "pipeline": event.get("pipeline"),
        "stage": event.get("stage"),
        "stock_name": event.get("stock_name"),
        "stock_code": event.get("stock_code"),
        "record_id": event.get("record_id"),
        "source_record_id": None if event.get("record_id") is None else str(event["record_id"]),
        "emitted_at": event.get("emitted_at"),
        "emitted_date": event.get("emitted_date"),
        "text_payload": event.get("text_payload"),
        "event_id": event.get("event_id"),
        "source_event_sha256": event.get("source_event_sha256"),
        "fields_json": json.dumps(fields, ensure_ascii=False) if fields else None,
    }
    for key in PIPELINE_FIELD_KEYS:
        row[f"fields_{key}"] = fields.get(key)
    return row


def _pipeline_arrow_schema() -> pa.Schema:
    fields = [
        pa.field("schema_version", pa.int64()),
        pa.field("event_type", pa.large_string()),
        pa.field("pipeline", pa.large_string()),
        pa.field("stage", pa.large_string()),
        pa.field("stock_name", pa.large_string()),
        pa.field("stock_code", pa.large_string()),
        pa.field("record_id", pa.float64()),
        pa.field("source_record_id", pa.large_string()),
        pa.field("emitted_at", pa.large_string()),
        pa.field("emitted_date", pa.date32()),
        pa.field("text_payload", pa.large_string()),
        pa.field("event_id", pa.large_string()),
        pa.field("source_event_sha256", pa.large_string()),
        pa.field("fields_json", pa.large_string()),
    ]
    fields.extend(
        pa.field(f"fields_{key}", pa.large_string()) for key in PIPELINE_FIELD_KEYS
    )
    return pa.schema(fields)


def _pipeline_row_for_arrow(
    event: Dict[str, Any], *, target_date: date
) -> Dict[str, Any]:
    row = convert_pipeline_event_to_row(event)
    try:
        row["schema_version"] = int(row.get("schema_version"))
    except (TypeError, ValueError):
        row["schema_version"] = None
    try:
        row["record_id"] = float(row.get("record_id"))
    except (TypeError, ValueError):
        row["record_id"] = None
    row["emitted_date"] = target_date
    for key in (
        "event_type",
        "source_record_id",
        "pipeline",
        "stage",
        "stock_name",
        "stock_code",
        "emitted_at",
        "text_payload",
        "event_id",
        "source_event_sha256",
        "fields_json",
        *(f"fields_{item}" for item in PIPELINE_FIELD_KEYS),
    ):
        value = row.get(key)
        row[key] = None if value is None else str(value)
    return row


def _pipeline_chunk_rows() -> int:
    raw = os.getenv(
        "TUNING_MONITORING_PIPELINE_PARQUET_CHUNK_ROWS",
        str(PIPELINE_PARQUET_CHUNK_ROWS),
    )
    try:
        return max(100, int(raw))
    except (TypeError, ValueError):
        return PIPELINE_PARQUET_CHUNK_ROWS


def _source_file_identity(path: Path) -> tuple[int, ...]:
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents) or not path.is_file():
        raise ValueError('pipeline_parquet_source_path_invalid')
    return _source_stat_identity(path.stat())


def _source_stat_identity(metadata) -> tuple[int, ...]:
    return (metadata.st_dev, metadata.st_ino, metadata.st_size,
            metadata.st_mtime_ns, metadata.st_ctime_ns)


@contextmanager
def _open_regular_source(path: Path, *, expected: tuple | None = None):
    before = _source_file_identity(path)
    if expected is not None and before != expected:
        raise ValueError('pipeline_parquet_source_changed_before_open')
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        current=os.fstat(descriptor)
        if not stat.S_ISREG(current.st_mode) or _source_stat_identity(current)!=before:
            raise ValueError('pipeline_parquet_source_changed_before_open')
        with os.fdopen(descriptor,'rb') as stream:
            descriptor=-1
            yield stream
            if _source_stat_identity(os.fstat(stream.fileno()))!=before:
                raise ValueError('pipeline_parquet_source_changed_during_read')
        if _source_file_identity(path)!=before:
            raise ValueError('pipeline_parquet_source_changed_during_read')
    finally:
        if descriptor>=0:os.close(descriptor)


def _parquet_byte_generation(path: Path) -> dict:
    before = _source_file_identity(path)
    digest = hashlib.sha256()
    with _open_regular_source(path,expected=before) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if _source_file_identity(path) != before:
        raise ValueError("pipeline_parquet_output_changed_during_read")
    return {"size_bytes": before[2], "sha256": digest.hexdigest()}


def _read_pipeline_metadata(path: Path) -> dict:
    before = _source_file_identity(path)
    limit = 1024 * 1024
    if before[2] > limit:
        raise ValueError('pipeline_parquet_source_metadata_unbounded')
    with _open_regular_source(path,expected=before) as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or _source_file_identity(path) != before:
        raise ValueError('pipeline_parquet_source_metadata_changed')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('pipeline_parquet_source_metadata_invalid')
    return value


def _pipeline_source_fingerprint(target_date: date) -> dict:
    fingerprint = {}
    for path in list_jsonl_files('pipeline_events',target_date):
        fingerprint[str(path)] = _source_file_identity(path)
        if path.suffix == '.gz':
            receipt = Path(str(path)+'.archive_receipt.json')
            fingerprint[str(receipt)] = _source_file_identity(receipt) if receipt.exists() or receipt.is_symlink() else None
    return fingerprint


@lru_cache(maxsize=32)
def _verify_legacy_pipeline_archive(path_name: str, identity: tuple, sha256: str, size: int, receipt_identity: tuple):
    """Old immutable receipts lack ctime; verify CRC and logical bytes once."""
    path = Path(path_name)
    digest = hashlib.sha256()
    decoded_size = 0
    with _open_regular_source(path,expected=identity) as raw, gzip.GzipFile(fileobj=raw,mode='rb') as stream:
        for block in iter(lambda: stream.read(64 * 1024), b''):
            decoded_size += len(block)
            if decoded_size > size:
                raise ValueError('pipeline_parquet_archive_logical_conflict')
            digest.update(block)
    if (_source_file_identity(path) != identity or decoded_size != size
            or digest.hexdigest() != sha256):
        raise ValueError('pipeline_parquet_archive_logical_conflict')


def _verify_pipeline_archive(path: Path, logical: Path, expected: dict, *, original_verified=False) -> None:
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    before = _source_file_identity(path)
    receipt_path = Path(str(path) + '.archive_receipt.json')
    receipt_before = _source_file_identity(receipt_path)
    archive = _read_pipeline_metadata(receipt_path)
    generation = archive.get('archive_generation')
    physical = dict(device=before[0], inode=before[1], size_bytes=before[2], mtime_ns=before[3])
    if (archive.get('schema') != 'pipeline_raw_archive_identity_v1'
            or archive.get('logical_path') != str(logical)
            or archive.get('logical_content_sha256') != expected.get('sha256')
            or (archive.get('logical_size_bytes') is not None
                and archive['logical_size_bytes'] != expected.get('decoded_size_bytes'))
            or archive.get('runtime_effect') is not False
            or archive.get('allowed_runtime_apply') is not False
            or not isinstance(generation, dict)
            or any(generation.get(key) != value for key, value in physical.items())):
        raise ValueError('pipeline_parquet_archive_receipt_invalid')
    if 'ctime_ns' in generation:
        if (generation['ctime_ns'] != before[4]
                or archive.get('logical_size_bytes') != expected.get('decoded_size_bytes')
                or archive.get('verification_contract') != 'logical_sha256_size_crc_to_eof_v1'
                or archive.get('artifact_content_sha256') != content_sha256({
                    k:v for k,v in archive.items() if k != 'artifact_content_sha256'})):
            raise ValueError('pipeline_parquet_archive_receipt_invalid')
    elif not original_verified:
        _verify_legacy_pipeline_archive(str(path), before, expected['sha256'], expected['decoded_size_bytes'],receipt_before)
    if _source_file_identity(path) != before or _source_file_identity(receipt_path) != receipt_before:
        raise ValueError('pipeline_parquet_archive_changed_during_validation')


def _verify_pipeline_logical_sources(files: List[Path], receipt: dict) -> None:
    original = receipt.get('source_files')
    if not isinstance(original, dict):
        raise ValueError('pipeline_parquet_source_receipt_invalid')
    current = {str(path): list(_source_file_identity(path)) for path in files}
    logical_sources = receipt.get('logical_sources')
    if not isinstance(logical_sources, dict):
        if current != original:
            raise ValueError('pipeline_parquet_source_generation_changed:logical_seal_missing')
        return
    groups = {}
    for path in files:
        logical = path.with_suffix('') if path.suffix == '.gz' else path
        groups.setdefault(str(logical), []).append(path)
    if set(groups) != set(logical_sources):
        raise ValueError('pipeline_parquet_source_generation_changed:logical_inventory')
    try:
        for logical_name, paths in groups.items():
            expected = logical_sources[logical_name]
            if (not isinstance(expected, dict)
                    or type(expected.get('decoded_size_bytes')) is not int or expected['decoded_size_bytes'] < 0
                    or not isinstance(expected.get('sha256'), str) or len(expected['sha256']) != 64):
                raise ValueError('pipeline_parquet_logical_seal_invalid')
            for path in paths:
                if current[str(path)] == original.get(str(path)):
                    # The original producer read this exact representation to
                    # EOF and sealed all decoded bytes in its existing pass.
                    if path.suffix == '.gz' and Path(str(path)+'.archive_receipt.json').exists():
                        _verify_pipeline_archive(path, Path(logical_name), expected,original_verified=True)
                    continue
                if path.suffix != '.gz':
                    raise ValueError('pipeline_parquet_plain_generation_changed')
                _verify_pipeline_archive(path, Path(logical_name), expected)
    except (OSError,ValueError,TypeError,KeyError,EOFError,zlib.error) as exc:
        raise ValueError('pipeline_parquet_source_generation_changed:' + str(exc)) from exc
    if {str(path): list(_source_file_identity(path)) for path in list_jsonl_files('pipeline_events',date.fromisoformat(receipt['target_date']))} != current:
        raise ValueError('pipeline_parquet_source_changed_during_validation')


def verify_pipeline_source_receipt(target_date: date, *, analytics_root: Path | None = None) -> dict:
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    directory = (analytics_root or ANALYTICS_ROOT) / "pipeline_events" / f"date={target_date.isoformat()}"
    receipt_path = directory / 'source_receipt.json'
    receipt_before = _source_file_identity(receipt_path)
    sources_before = _pipeline_source_fingerprint(target_date)
    receipt = _read_pipeline_metadata(receipt_path)
    if (receipt.get("schema") != "tuning_pipeline_parquet_source_v2"
            or receipt.get("status") != "complete"
            or receipt.get("target_date") != target_date.isoformat()
            or receipt.get("conservation_verified") is not True
            or receipt.get("artifact_content_sha256") != content_sha256({
                k:v for k,v in receipt.items() if k != "artifact_content_sha256"})):
        raise ValueError("pipeline_parquet_source_receipt_invalid")
    _verify_pipeline_logical_sources(list_jsonl_files('pipeline_events',target_date),receipt)
    paths = sorted(directory.glob("*.parquet"))
    expected = receipt.get("output_generation")
    if receipt.get("written_count") == 0:
        if paths or expected is not None:
            raise ValueError("pipeline_parquet_empty_generation_conflict")
    elif (len(paths) != 1 or expected != {
            "path": paths[0].name, **_parquet_byte_generation(paths[0])}):
        raise ValueError("pipeline_parquet_output_generation_changed")
    if (_source_file_identity(receipt_path) != receipt_before
            or _pipeline_source_fingerprint(target_date) != sources_before):
        raise ValueError('pipeline_parquet_source_changed_during_validation')
    return receipt


def _write_pipeline_parquet_stream(
    files: List[Path],
    *,
    target_date: date,
    dedupe: bool,
) -> Tuple[int, int]:
    partition_dir = (
        ANALYTICS_ROOT / "pipeline_events" / f"date={target_date.isoformat()}"
    )
    partition_dir.mkdir(parents=True, exist_ok=True)
    out_file = (
        partition_dir / f"pipeline_events_{target_date.strftime('%Y%m%d')}.parquet"
    )
    tmp_file = out_file.with_suffix(out_file.suffix + ".tmp")
    tmp_file.unlink(missing_ok=True)
    schema = _pipeline_arrow_schema()
    chunk_limit = _pipeline_chunk_rows()
    chunk: List[Dict[str, Any]] = []
    seen_event_ids: dict[str, str] = {}
    total_lines = 0
    excluded_dates: dict[str, int] = {}
    exact_duplicates = 0
    selected_source_count = 0
    sources = {str(path): _source_file_identity(path) for path in files}
    logical_sources: dict[str, dict] = {}
    written = 0
    writer: pq.ParquetWriter | None = None

    def verify_sources() -> None:
        if (sorted(map(str,list_jsonl_files('pipeline_events',target_date))) != sorted(sources)
                or any(sources[str(path)] != _source_file_identity(path) for path in files)):
            raise ValueError('pipeline_parquet_source_changed_during_read')

    def flush_chunk() -> None:
        nonlocal chunk, writer, written
        if not chunk:
            return
        table = pa.Table.from_pylist(chunk, schema=schema)
        if writer is None:
            writer = pq.ParquetWriter(tmp_file, schema, compression="snappy")
        writer.write_table(table)
        written += len(chunk)
        chunk = []

    try:
        for file_path in tqdm(files, desc=str(target_date)):
            logical_generation = {}
            for event in read_jsonl_lines(file_path, strict=True,logical_generation=logical_generation):
                total_lines += 1
                if not _event_matches_target_date(
                    event, "pipeline_events", target_date
                ):
                    observed = next((str(event[key])[:10] for key in (
                        "emitted_date", "event_date", "signal_date") if event.get(key)), "unknown")
                    excluded_dates[observed] = excluded_dates.get(observed, 0) + 1
                    continue
                selected_source_count += 1
                source_sha256 = pipeline_event_payload_sha256(event)
                event_id = extract_event_id(event, source_payload_sha256=source_sha256)
                if event_id:
                    previous = seen_event_ids.get(event_id)
                    if previous is not None and previous != source_sha256:
                        raise ValueError("pipeline_event_native_id_conflict:" + event_id)
                    if dedupe and previous is not None:
                        exact_duplicates += 1
                        continue
                    seen_event_ids[event_id] = source_sha256
                    event = {**event, "event_id": event_id}
                event = {**event, "source_event_sha256": source_sha256}
                chunk.append(_pipeline_row_for_arrow(event, target_date=target_date))
                if len(chunk) >= chunk_limit:
                    flush_chunk()
            logical = file_path.with_suffix('') if file_path.suffix == '.gz' else file_path
            previous = logical_sources.setdefault(str(logical),logical_generation)
            if previous != logical_generation:
                raise ValueError('pipeline_parquet_plain_gzip_conflict')
        flush_chunk()
        verify_sources()
        if total_lines != written + exact_duplicates + sum(excluded_dates.values()):
            raise ValueError("pipeline_parquet_population_not_conserved")
    except Exception:
        if writer is not None:
            writer.close()
            writer = None
        tmp_file.unlink(missing_ok=True)
        raise
    finally:
        if writer is not None:
            writer.close()

    from src.engine.scalping.micro_reversion.economic_reference import atomic_write_json, content_sha256
    receipt = {
        "schema": "tuning_pipeline_parquet_source_v2", "target_date": target_date.isoformat(),
        "identity_contract": "native_id_or_complete_payload_sha256_v1",
        "source_files": sources,
        "logical_sources": logical_sources,
        "decoded_input_count": total_lines, "selected_date_count": selected_source_count,
        "excluded_date_count": sum(excluded_dates.values()),
        "excluded_date_counts": excluded_dates, "exact_duplicate_count": exact_duplicates,
        "written_count": written,
        "output_generation": ({"path": out_file.name, **_parquet_byte_generation(tmp_file)}
                              if written else None),
        "population_state": "retained" if written else "valid_empty",
        "conservation_verified": total_lines == written + exact_duplicates + sum(excluded_dates.values()),
        "runtime_effect": False, "allowed_runtime_apply": False,
    }
    def publish_receipt(status):
        body = {**receipt, "status": status}
        atomic_write_json(partition_dir / "source_receipt.json", {
            **body, "artifact_content_sha256": content_sha256(body)})
    try:
        # Invalidate the previous receipt before changing its output. A crash
        # between the two atomic writes stays visibly publishing, never current.
        verify_sources()
        publish_receipt("publishing")
        if written:
            os.replace(tmp_file, out_file)
        else:
            tmp_file.unlink(missing_ok=True)
        for stale_file in partition_dir.glob("*.parquet"):
            if not written or stale_file != out_file:
                stale_file.unlink()
        verify_sources()
        publish_receipt("complete")
    except Exception:
        tmp_file.unlink(missing_ok=True)
        raise
    logger.info("Parquet streaming file written: %s (%d rows, chunk_rows=%d)",
                out_file, written, chunk_limit)
    return total_lines, written


def _event_matches_target_date(
    event: Dict[str, Any], dataset: str, target_date: date
) -> bool:
    target = target_date.isoformat()
    # 우선 공통 날짜 필드를 사용한다.
    for key in ("emitted_date", "event_date", "signal_date"):
        value = str(event.get(key) or "").strip()
        if value:
            return value[:10] == target
    if dataset != "system_metric_samples":
        return True
    ts = str(event.get("ts") or "").strip()
    if ts:
        return ts[:10] == target
    return False


def deduplicate_by_event_id(df: pd.DataFrame) -> pd.DataFrame:
    """event_id 기준으로 중복 제거."""
    if "event_id" not in df.columns:
        return df
    event_id_series = df["event_id"]
    if event_id_series.notna().sum() == 0:
        return df
    with_event_id = df[event_id_series.notna()].drop_duplicates(
        subset=["event_id"], keep="first"
    )
    without_event_id = df[event_id_series.isna()]
    return pd.concat([with_event_id, without_event_id], ignore_index=True)


def write_parquet_partition(
    df: pd.DataFrame, dataset: str, target_date: date, mode: str = "replace"
) -> int:
    """DataFrame을 날짜 파티션 Parquet 파일로 저장."""
    if df.empty:
        logger.warning("빈 DataFrame, 쓰기 건너뜀.")
        return 0
    # 출력 경로: analytics/parquet/<dataset>/date=YYYY-MM-DD/*.parquet
    partition_dir = (
        ANALYTICS_ROOT / dataset / f"date={target_date.strftime('%Y-%m-%d')}"
    )
    partition_dir.mkdir(parents=True, exist_ok=True)
    # idempotent 동작을 위해 기본은 replace 모드로 날짜 파티션을 재생성한다.
    if mode == "replace":
        shutil.rmtree(partition_dir, ignore_errors=True)
        partition_dir.mkdir(parents=True, exist_ok=True)
        out_file = partition_dir / f"{dataset}_{target_date.strftime('%Y%m%d')}.parquet"
    else:
        timestamp = datetime.now().strftime("%H%M%S")
        out_file = (
            partition_dir
            / f"{dataset}_{target_date.strftime('%Y%m%d')}_{timestamp}.parquet"
        )
    # PyArrow 테이블로 변환
    table = pa.Table.from_pandas(df, preserve_index=False)
    # Parquet 작성
    pq.write_table(table, out_file, compression="snappy")
    logger.info("Parquet 파일 작성: %s (%d 행)", out_file, len(df))
    return len(df)


def clear_parquet_partition(dataset: str, target_date: date) -> None:
    """대상 날짜 파티션을 제거한다 (stale partition 정리)."""
    partition_dir = (
        ANALYTICS_ROOT / dataset / f"date={target_date.strftime('%Y-%m-%d')}"
    )
    if partition_dir.exists():
        shutil.rmtree(partition_dir, ignore_errors=True)
        logger.info("기존 파티션 제거: %s", partition_dir)


def process_single_date(
    dataset: str, target_date: date, dedupe: bool = True
) -> Tuple[int, int]:
    """단일 날짜의 모든 JSONL 파일을 읽어 Parquet으로 변환."""
    files = list_jsonl_files(dataset, target_date)
    if not files:
        clear_parquet_partition(dataset, target_date)
        _write_empty_partition_receipt(dataset,target_date,files,0)
        logger.info("%s %s: 처리할 파일 없음", dataset, target_date)
        return 0, 0
    logger.info("%s %s: %d개 파일 처리 시작", dataset, target_date, len(files))
    if dataset == "pipeline_events":
        return _write_pipeline_parquet_stream(
            files,
            target_date=target_date,
            dedupe=dedupe,
        )
    all_events = []
    metric_identities: dict[str, str] = {}
    total_lines = 0
    for file_path in tqdm(files, desc=str(target_date)):
        for event in read_jsonl_lines(file_path, strict=dataset == "system_metric_samples"):
            total_lines += 1
            if not _event_matches_target_date(event, dataset, target_date):
                continue
            # event_id 주입
            event_id = extract_event_id(event)
            if dataset == "system_metric_samples":
                # A sampler clock owns one observation.  Exact repeated bytes
                # may dedupe; changed measurements at that clock must never be
                # silently replaced by whichever row happened to arrive first.
                if event_id is None:
                    raise ValueError("system_metric_sample_identity_missing")
                source_sha256 = pipeline_event_payload_sha256(event)
                previous = metric_identities.setdefault(event_id, source_sha256)
                if previous != source_sha256:
                    raise ValueError("system_metric_sample_identity_conflict:" + event_id)
            if event_id:
                event["event_id"] = event_id
            all_events.append(event)
    logger.info("읽은 총 행: %d", total_lines)
    if not all_events:
        clear_parquet_partition(dataset, target_date)
        _write_empty_partition_receipt(dataset,target_date,files,total_lines)
        return total_lines, 0
    else:
        df = convert_to_dataframe(all_events, dataset)
    if dedupe:
        df = deduplicate_by_event_id(df)
    if df.empty:
        clear_parquet_partition(dataset, target_date)
        _write_empty_partition_receipt(dataset,target_date,files,total_lines)
        return total_lines, 0
    written = write_parquet_partition(df, dataset, target_date)
    return total_lines, written


def _write_empty_partition_receipt(dataset,target_date,files,read_rows):
    """post_sell is emitted on outcomes, unlike mandatory pipeline telemetry."""
    if dataset!='post_sell':return
    from src.engine.scalping.continuous_reversal_postclose import seal,file_hash,write
    path=ANALYTICS_ROOT/dataset/f'date={target_date.isoformat()}'/'source_receipt.json'
    write(path,seal(dict(schema='tuning_parquet_empty_source_v1',dataset=dataset,
                         target_date=target_date.isoformat(),status='valid_empty',written_rows=0,read_rows=read_rows,
                         reason='no_post_sell_emissions' if not files else 'no_target_date_rows',
                         source_files=[dict(path=str(p.resolve()),sha256=file_hash(p)) for p in files])))


def backfill_date_range(
    dataset: str, start_date: date, end_date: date, dedupe: bool = True
) -> Dict[date, Tuple[int, int]]:
    """지정 범위의 모든 날짜를 처리."""
    results = {}
    delta = timedelta(days=1)
    current = start_date
    while current <= end_date:
        read, written = process_single_date(dataset, current, dedupe)
        results[current] = (read, written)
        current += delta
    return results


def main():
    parser = argparse.ArgumentParser(
        description="튜닝 모니터링 로그 JSONL → Parquet 변환"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=["pipeline_events", "post_sell", "system_metric_samples"],
        help="변환할 데이터셋 이름",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--single-date",
        help="단일 날짜 (YYYY-MM-DD)",
    )
    group.add_argument(
        "--start",
        help="시작 날짜 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        help="종료 날짜 (YYYY-MM-DD), --start와 함께 사용",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="중복 제거 수행 안 함",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.single_date:
        target_date = datetime.strptime(args.single_date, "%Y-%m-%d").date()
        read, written = process_single_date(
            args.dataset, target_date, dedupe=not args.no_dedupe
        )
        logger.info("완료: 읽은 행=%d, 작성 행=%d", read, written)
    else:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
        results = backfill_date_range(
            args.dataset, start_date, end_date, dedupe=not args.no_dedupe
        )
        total_read = sum(r[0] for r in results.values())
        total_written = sum(r[1] for r in results.values())
        logger.info("전체 완료: 읽은 행=%d, 작성 행=%d", total_read, total_written)
        for d, (r, w) in results.items():
            logger.info("  %s: 읽은 행=%d, 작성 행=%d", d, r, w)


if __name__ == "__main__":
    main()
