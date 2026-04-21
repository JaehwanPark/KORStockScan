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
import logging
import shutil
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


def list_jsonl_files(
    dataset: str, target_date: date
) -> List[Path]:
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
        gz_pattern = f"post_sell_evaluations*{target_date.strftime('%Y-%m-%d')}*.jsonl.gz"
        files.extend(src_path.glob(gz_pattern))
        return sorted(files)
    # pipeline_events: 날짜 패턴 매칭
    pattern = f"*{target_date.strftime('%Y-%m-%d')}*.jsonl"
    files = list(src_path.glob(pattern))
    # .gz 확장자도 포함
    gz_pattern = f"*{target_date.strftime('%Y-%m-%d')}*.jsonl.gz"
    files.extend(src_path.glob(gz_pattern))
    return sorted(files)


def read_jsonl_lines(file_path: Path) -> Iterator[Dict[str, Any]]:
    """JSONL 파일을 줄 단위로 읽어 dict 생성."""
    open_func = gzip.open if file_path.suffix == ".gz" else open
    with open_func(file_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("JSON decode error in %s: %s", file_path, e)


def extract_event_id(event: Dict[str, Any]) -> Optional[str]:
    """이벤트 고유 ID 생성. 중복 제거용."""
    # pipeline_event 경우 record_id + emitted_at 조합
    if event.get("event_type") == "pipeline_event":
        record_id = event.get("record_id")
        emitted_at = event.get("emitted_at")
        if record_id is not None and emitted_at:
            return f"{record_id}:{emitted_at}"
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


def convert_to_dataframe(
    events: List[Dict[str, Any]], dataset: str
) -> pd.DataFrame:
    """이벤트 리스트를 Pandas DataFrame으로 변환."""
    if not events:
        return pd.DataFrame()
    if dataset == "pipeline_events":
        rows: List[Dict[str, Any]] = []
        for event in events:
            fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
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
                "fields_json": json.dumps(fields, ensure_ascii=False) if fields else None,
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
        "emitted_at": event.get("emitted_at"),
        "emitted_date": event.get("emitted_date"),
        "text_payload": event.get("text_payload"),
        "event_id": event.get("event_id"),
        "fields_json": json.dumps(fields, ensure_ascii=False) if fields else None,
    }
    for key in PIPELINE_FIELD_KEYS:
        row[f"fields_{key}"] = fields.get(key)
    return row


def _event_matches_target_date(event: Dict[str, Any], dataset: str, target_date: date) -> bool:
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
        out_file = partition_dir / f"{dataset}_{target_date.strftime('%Y%m%d')}_{timestamp}.parquet"
    # PyArrow 테이블로 변환
    table = pa.Table.from_pandas(df, preserve_index=False)
    # Parquet 작성
    pq.write_table(table, out_file, compression="snappy")
    logger.info("Parquet 파일 작성: %s (%d 행)", out_file, len(df))
    return len(df)


def clear_parquet_partition(dataset: str, target_date: date) -> None:
    """대상 날짜 파티션을 제거한다 (stale partition 정리)."""
    partition_dir = ANALYTICS_ROOT / dataset / f"date={target_date.strftime('%Y-%m-%d')}"
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
        logger.info("%s %s: 처리할 파일 없음", dataset, target_date)
        return 0, 0
    logger.info("%s %s: %d개 파일 처리 시작", dataset, target_date, len(files))
    # pipeline_events는 fields 원본 payload가 커서 원본 dict를 모두 보관하면 장후 sync가
    # OOM kill될 수 있다. 읽는 즉시 분석용 축소 row로 변환해 메모리 사용량을 제한한다.
    pipeline_rows: List[Dict[str, Any]] = []
    all_events = []
    total_lines = 0
    for file_path in tqdm(files, desc=str(target_date)):
        for event in read_jsonl_lines(file_path):
            total_lines += 1
            if not _event_matches_target_date(event, dataset, target_date):
                continue
            # event_id 주입
            event_id = extract_event_id(event)
            if event_id:
                event["event_id"] = event_id
            if dataset == "pipeline_events":
                pipeline_rows.append(convert_pipeline_event_to_row(event))
            else:
                all_events.append(event)
    logger.info("읽은 총 행: %d", total_lines)
    if dataset == "pipeline_events":
        if not pipeline_rows:
            clear_parquet_partition(dataset, target_date)
            return total_lines, 0
        df = pd.DataFrame(pipeline_rows)
        df["emitted_date"] = pd.to_datetime(df["emitted_date"], errors="coerce").dt.date
        df = df[df["emitted_date"].notna()]
    elif not all_events:
        clear_parquet_partition(dataset, target_date)
        return total_lines, 0
    else:
        df = convert_to_dataframe(all_events, dataset)
    if dedupe:
        df = deduplicate_by_event_id(df)
    if df.empty:
        clear_parquet_partition(dataset, target_date)
        return total_lines, 0
    written = write_parquet_partition(df, dataset, target_date)
    return total_lines, written


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
    parser = argparse.ArgumentParser(description="튜닝 모니터링 로그 JSONL → Parquet 변환")
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
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="상세 로그 출력"
    )
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
