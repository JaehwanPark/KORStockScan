"""JSONL vs DuckDB shadow diff 집계 비교 도구.

비교 지표:
- trade_count (COMPLETED/GOOD_EXIT + valid profit_rate)
- funnel(latency/liquidity/ai_threshold/overbought/submitted)
- full_fill / partial_fill
- missed_upside
"""

from __future__ import annotations

import argparse
import gzip
import json
import hashlib
import math
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable

from src.engine.tuning_duckdb_repository import TuningDuckDBRepository
from src.utils.constants import DATA_DIR

PIPELINE_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"


def _iter_dates(start_date: date, end_date: date) -> Iterable[date]:
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    open_func = gzip.open if path.suffix == ".gz" else open
    with open_func(path, "rt", encoding="utf-8") as fp:
        for raw in fp:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise ValueError("shadow_diff_source_non_object")
                yield event
            except json.JSONDecodeError as exc:
                raise ValueError("shadow_diff_source_json_invalid") from exc


def _empty_metrics() -> Dict[str, int]:
    return {
        "trade_count": 0,
        "completed_count": 0,
        "missed_upside": 0,
        "funnel_latency_block": 0,
        "funnel_liquidity_block": 0,
        "funnel_ai_threshold_block": 0,
        "funnel_overbought_block": 0,
        "submitted_events": 0,
        "full_fill_count": 0,
        "partial_fill_count": 0,
    }


def _valid_profit_rate(value: Any) -> bool:
    # JSON booleans are Python ints, but never economic observations. Numeric
    # strings and non-finite values likewise do not prove a completed return.
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _build_event_id(event: Dict[str, Any], *, source_sha256: str | None = None) -> str | None:
    event_id = event.get("event_id")
    if event_id:
        return str(event_id)
    if event.get("event_type") == "pipeline_event":
        return "pipeline-content-sha256:" + (source_sha256 or _source_payload_sha256(event))
    post_sell_id = event.get("post_sell_id")
    if post_sell_id:
        return f"post_sell:{post_sell_id}"
    recommendation_id = event.get("recommendation_id")
    signal_date = event.get("signal_date")
    sell_time = event.get("sell_time")
    if recommendation_id is not None and signal_date and sell_time:
        return f"post_sell:{recommendation_id}:{signal_date}:{sell_time}"
    record_id = event.get("record_id")
    emitted_at = event.get("emitted_at")
    if record_id is not None and emitted_at:
        return f"{record_id}:{emitted_at}"
    return None


def _source_payload_sha256(event: Dict[str, Any]) -> str:
    # This raw-side census is independent of the Parquet extractor/dedupe.
    # Include every source field even when aggregate metrics do not use it.
    return hashlib.sha256(json.dumps(event, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _population_receipt(keys) -> dict:
    ordered = sorted(keys)
    digest = hashlib.sha256()
    for identity, payload_sha256 in ordered:
        digest.update(json.dumps([identity, payload_sha256], separators=(",", ":")).encode() + b"\n")
    return {"count": len(ordered), "identity_payload_sha256": digest.hexdigest()}


def _count_jsonl_metrics(
    start_date: date, end_date: date, *, pipeline_population: dict | None = None
) -> Dict[str, int]:
    metrics = _empty_metrics()
    seen_pipeline_ids: set[str] = set()
    seen_post_sell_ids: set[str] = set()
    source_keys: set[tuple[str, str]] = set()
    native_ids: dict[str, str] = {}
    excluded_dates: dict[str, int] = {}
    for target in _iter_dates(start_date, end_date):
        ds = target.isoformat()
        pipeline_files = [
            PIPELINE_DIR / f"pipeline_events_{ds}.jsonl",
            PIPELINE_DIR / f"pipeline_events_{ds}.jsonl.gz",
        ]
        for path in pipeline_files:
            for event in _iter_jsonl(path):
                source_date = next((str(event[key])[:10] for key in (
                    "emitted_date", "event_date", "signal_date") if event.get(key)), ds)
                if source_date != ds:
                    if target == end_date:
                        excluded_dates[source_date] = excluded_dates.get(source_date, 0) + 1
                    continue
                payload_sha256 = _source_payload_sha256(event)
                event_id = _build_event_id(event, source_sha256=payload_sha256)
                if target == end_date:
                    native = event.get("event_id")
                    if native is not None:
                        if not isinstance(native, str) or not native.strip():
                            raise ValueError("shadow_diff_native_id_invalid")
                        previous = native_ids.get(native)
                        if previous is not None and previous != payload_sha256:
                            raise ValueError("shadow_diff_native_id_conflict:" + native)
                        native_ids[native] = payload_sha256
                    source_keys.add((event_id or "", payload_sha256))
                if event_id and event_id in seen_pipeline_ids:
                    continue
                if event_id:
                    seen_pipeline_ids.add(event_id)
                stage = str(event.get("stage") or "")
                fields = event.get("fields") or {}
                if "latency_block" in stage:
                    metrics["funnel_latency_block"] += 1
                elif "blocked_liquidity" in stage:
                    metrics["funnel_liquidity_block"] += 1
                elif (
                    "blocked_strength" in stage
                    or "blocked_ai_score" in stage
                    or "ai_threshold" in stage
                ):
                    metrics["funnel_ai_threshold_block"] += 1
                if (
                    "blocked_overbought" in stage
                    or str(fields.get("overbought_blocked", "")).lower() == "true"
                ):
                    metrics["funnel_overbought_block"] += 1
                if "submitted" in stage:
                    metrics["submitted_events"] += 1

                if stage == "position_rebased_after_fill":
                    fill_quality = str(fields.get("fill_quality") or "").upper()
                    if fill_quality == "FULL_FILL":
                        metrics["full_fill_count"] += 1
                    elif fill_quality == "PARTIAL_FILL":
                        metrics["partial_fill_count"] += 1

        post_sell_files = [
            POST_SELL_DIR / f"post_sell_evaluations_{ds}.jsonl",
            POST_SELL_DIR / f"post_sell_evaluations_{ds}.jsonl.gz",
        ]
        for path in post_sell_files:
            for event in _iter_jsonl(path):
                event_id = _build_event_id(event)
                if event_id and event_id in seen_post_sell_ids:
                    continue
                if event_id:
                    seen_post_sell_ids.add(event_id)
                outcome = str(event.get("outcome") or "")
                profit_rate = event.get("profit_rate")
                if outcome in {"GOOD_EXIT", "COMPLETED"} and _valid_profit_rate(profit_rate):
                    metrics["trade_count"] += 1
                    metrics["completed_count"] += 1
                if outcome == "MISSED_UPSIDE":
                    metrics["missed_upside"] += 1
    if pipeline_population is not None:
        pipeline_population.update(_population_receipt(source_keys),
            source_date=end_date.isoformat(), excluded_date_counts=excluded_dates,
            contract="all_source_fields_identity_census_v1")
    return metrics


def _count_duckdb_metrics(
    start_date: date, end_date: date, *, pipeline_population: dict | None = None
) -> Dict[str, int]:
    # Shadow comparison needs external files, not a writable operational DB.
    with TuningDuckDBRepository(duckdb_path=Path(":memory:"), read_only=False) as repo:
        try:
            repo.register_parquet_dataset("pipeline_events", start_date=start_date, end_date=end_date)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            if pipeline_population is None:
                raise
            pipeline_population.update(status='source_gap', reason='source_receipt:' + str(exc))
            return _empty_metrics()
        repo.register_parquet_dataset("post_sell", start_date=start_date, end_date=end_date)

        if pipeline_population is not None:
            receipt = repo.pipeline_source_receipts.get(end_date.isoformat())
            if receipt is not None:
                pipeline_population['source_receipt_status'] = receipt['status']
            else:
                pipeline_population.update(status='source_gap', reason='source_receipt_missing')
            columns = set(repo.conn.execute("DESCRIBE v_pipeline_events").fetchdf()["column_name"])
            if "source_event_sha256" not in columns:
                pipeline_population.update(status="source_gap", reason="source_payload_identity_column_missing")
            else:
                cursor = repo.conn.execute("SELECT event_id, source_event_sha256 FROM v_pipeline_events WHERE emitted_date = ?",
                                           [end_date.isoformat()])
                keys = []; invalid = 0
                while batch := cursor.fetchmany(5000):
                    for identity, payload_sha256 in batch:
                        if (not isinstance(payload_sha256, str) or len(payload_sha256) != 64
                                or any(ch not in "0123456789abcdef" for ch in payload_sha256)):
                            invalid += 1
                        else:
                            keys.append((identity or "", payload_sha256))
                pipeline_population.update(_population_receipt(keys), source_date=end_date.isoformat(),
                    invalid_identity_count=invalid, contract="all_source_fields_identity_census_v1")

        pipeline_df = repo.query(
            """
            SELECT
                SUM(CASE WHEN stage LIKE '%latency_block%' THEN 1 ELSE 0 END) AS funnel_latency_block,
                SUM(CASE WHEN stage LIKE '%blocked_liquidity%' THEN 1 ELSE 0 END) AS funnel_liquidity_block,
                SUM(
                    CASE
                        WHEN stage LIKE '%blocked_strength%'
                          OR stage LIKE '%blocked_ai_score%'
                          OR stage LIKE '%ai_threshold%'
                        THEN 1 ELSE 0
                    END
                ) AS funnel_ai_threshold_block,
                SUM(
                    CASE
                        WHEN stage LIKE '%blocked_overbought%'
                          OR lower(coalesce(cast(fields_overbought_blocked as varchar), '')) = 'true'
                        THEN 1 ELSE 0
                    END
                ) AS funnel_overbought_block,
                SUM(CASE WHEN stage LIKE '%submitted%' THEN 1 ELSE 0 END) AS submitted_events,
                SUM(
                    CASE
                        WHEN stage = 'position_rebased_after_fill'
                          AND upper(coalesce(cast(fields_fill_quality as varchar), '')) = 'FULL_FILL'
                        THEN 1 ELSE 0
                    END
                ) AS full_fill_count,
                SUM(
                    CASE
                        WHEN stage = 'position_rebased_after_fill'
                          AND upper(coalesce(cast(fields_fill_quality as varchar), '')) = 'PARTIAL_FILL'
                        THEN 1 ELSE 0
                    END
                ) AS partial_fill_count
            FROM v_pipeline_events
            WHERE emitted_date BETWEEN ? AND ?
            """,
            [start_date.isoformat(), end_date.isoformat()],
        )

        # Judge each original file before union_by_name can coerce BOOLEAN or
        # VARCHAR profits into a numeric type contributed by another day.
        post_sell_row = {key: 0 for key in ("trade_count", "completed_count", "missed_upside")}
        post_sell_files = repo.registered_parquet_files["post_sell"]

        def file_generation(path):
            value = path.stat()
            return (value.st_dev, value.st_ino, value.st_size,
                    value.st_mtime_ns, value.st_ctime_ns)

        source_generations = {path: file_generation(path) for path in post_sell_files}
        for path in post_sell_files:
            post_sell_df = repo.query(
                """
            WITH post_sell_validity AS (
                SELECT *,
                    (
                        typeof(profit_rate) IN (
                            'TINYINT', 'SMALLINT', 'INTEGER', 'BIGINT', 'HUGEINT',
                            'UTINYINT', 'USMALLINT', 'UINTEGER', 'UBIGINT', 'UHUGEINT',
                            'FLOAT', 'DOUBLE'
                        )
                        OR starts_with(typeof(profit_rate), 'DECIMAL(')
                    ) AND isfinite(TRY_CAST(profit_rate AS DOUBLE)) AS valid_profit_rate
                FROM read_parquet(?)
            )
            SELECT
                SUM(
                    CASE
                        WHEN outcome IN ('GOOD_EXIT', 'COMPLETED')
                          AND valid_profit_rate
                        THEN 1 ELSE 0
                    END
                ) AS trade_count,
                SUM(
                    CASE
                        WHEN outcome IN ('GOOD_EXIT', 'COMPLETED')
                          AND valid_profit_rate
                        THEN 1 ELSE 0
                    END
                ) AS completed_count,
                SUM(CASE WHEN outcome = 'MISSED_UPSIDE' THEN 1 ELSE 0 END) AS missed_upside
            FROM post_sell_validity
            WHERE emitted_date BETWEEN ? AND ?
            """,
                [str(path), start_date.isoformat(), end_date.isoformat()],
            )
            counts = post_sell_df.fillna(0).iloc[0].to_dict() if not post_sell_df.empty else {}
            for key in post_sell_row:
                post_sell_row[key] += int(counts.get(key, 0))
        if any(file_generation(path) != source_generations[path] for path in post_sell_files):
            raise ValueError("shadow_diff_post_sell_parquet_changed_during_read")

    metrics = _empty_metrics()
    pipeline_row = (
        pipeline_df.fillna(0).iloc[0].to_dict() if not pipeline_df.empty else {}
    )
    for key in metrics:
        value = pipeline_row.get(key, post_sell_row.get(key, 0))
        if key in post_sell_row:
            value = post_sell_row.get(key, 0)
        if key in pipeline_row and key not in {
            "trade_count",
            "completed_count",
            "missed_upside",
        }:
            value = pipeline_row.get(key, 0)
        metrics[key] = int(value or 0)
    return metrics


def _build_diff(
    jsonl_metrics: Dict[str, int], duckdb_metrics: Dict[str, int]
) -> Dict[str, Any]:
    diff: Dict[str, Any] = {}
    all_equal = True
    for key in jsonl_metrics:
        j = int(jsonl_metrics[key])
        d = int(duckdb_metrics.get(key, 0))
        delta = d - j
        if delta != 0:
            all_equal = False
        diff[key] = {
            "jsonl": j,
            "duckdb": d,
            "delta": delta,
            "match": delta == 0,
        }
    return {"all_match": all_equal, "metrics": diff}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="튜닝 모니터링 shadow diff 비교")
    parser.add_argument("--start", required=True, help="시작일 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="종료일 YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "analytics" / "shadow_diff_summary.json"),
        help="결과 JSON 파일 경로",
    )
    args = parser.parse_args(argv)

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    raw_population, parquet_population = {}, {}
    jsonl_metrics = _count_jsonl_metrics(start_date, end_date, pipeline_population=raw_population)
    duckdb_metrics = _count_duckdb_metrics(start_date, end_date, pipeline_population=parquet_population)
    population_match = bool(parquet_population.get("status") != "source_gap"
        and parquet_population.get("invalid_identity_count") == 0
        and all(raw_population.get(key) == parquet_population.get(key) for key in (
            "count", "identity_payload_sha256", "source_date", "contract")))
    result = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": datetime.now().isoformat(),
        **_build_diff(jsonl_metrics, duckdb_metrics),
        "pipeline_population": {"source_date": end_date.isoformat(),
            "scope": "exact_source_date_all_event_source_identities",
            "transformed_payload_semantics_verified": False,
            "raw": raw_population, "parquet": parquet_population, "match": population_match},
    }
    result["all_match"] = result["all_match"] and population_match

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from src.engine.scalping.micro_reversion.economic_reference import atomic_write_json
    atomic_write_json(out_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"saved: {out_path}")
    return 0 if result["all_match"] else 2


if __name__ == "__main__":
    sys.exit(main())
