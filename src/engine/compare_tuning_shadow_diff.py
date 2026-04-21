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
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


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


def _build_event_id(event: Dict[str, Any]) -> str | None:
    event_id = event.get("event_id")
    if event_id:
        return str(event_id)
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


def _count_jsonl_metrics(start_date: date, end_date: date) -> Dict[str, int]:
    metrics = _empty_metrics()
    seen_pipeline_ids: set[str] = set()
    seen_post_sell_ids: set[str] = set()
    for target in _iter_dates(start_date, end_date):
        ds = target.isoformat()
        pipeline_files = [
            PIPELINE_DIR / f"pipeline_events_{ds}.jsonl",
            PIPELINE_DIR / f"pipeline_events_{ds}.jsonl.gz",
        ]
        for path in pipeline_files:
            for event in _iter_jsonl(path):
                event_id = _build_event_id(event)
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
                if "blocked_overbought" in stage or str(fields.get("overbought_blocked", "")).lower() == "true":
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
                if outcome in {"GOOD_EXIT", "COMPLETED"} and isinstance(profit_rate, (int, float)):
                    metrics["trade_count"] += 1
                    metrics["completed_count"] += 1
                if outcome == "MISSED_UPSIDE":
                    metrics["missed_upside"] += 1
    return metrics


def _count_duckdb_metrics(start_date: date, end_date: date) -> Dict[str, int]:
    with TuningDuckDBRepository(read_only=False) as repo:
        repo.register_parquet_dataset("pipeline_events")
        repo.register_parquet_dataset("post_sell")

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

        post_sell_df = repo.query(
            """
            SELECT
                SUM(
                    CASE
                        WHEN outcome IN ('GOOD_EXIT', 'COMPLETED')
                          AND TRY_CAST(profit_rate AS DOUBLE) IS NOT NULL
                        THEN 1 ELSE 0
                    END
                ) AS trade_count,
                SUM(
                    CASE
                        WHEN outcome IN ('GOOD_EXIT', 'COMPLETED')
                          AND TRY_CAST(profit_rate AS DOUBLE) IS NOT NULL
                        THEN 1 ELSE 0
                    END
                ) AS completed_count,
                SUM(CASE WHEN outcome = 'MISSED_UPSIDE' THEN 1 ELSE 0 END) AS missed_upside
            FROM v_post_sell
            WHERE emitted_date BETWEEN ? AND ?
            """,
            [start_date.isoformat(), end_date.isoformat()],
        )

    metrics = _empty_metrics()
    pipeline_row = pipeline_df.fillna(0).iloc[0].to_dict() if not pipeline_df.empty else {}
    post_sell_row = post_sell_df.fillna(0).iloc[0].to_dict() if not post_sell_df.empty else {}
    for key in metrics:
        value = pipeline_row.get(key, post_sell_row.get(key, 0))
        if key in post_sell_row:
            value = post_sell_row.get(key, 0)
        if key in pipeline_row and key not in {"trade_count", "completed_count", "missed_upside"}:
            value = pipeline_row.get(key, 0)
        metrics[key] = int(value or 0)
    return metrics


def _build_diff(jsonl_metrics: Dict[str, int], duckdb_metrics: Dict[str, int]) -> Dict[str, Any]:
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


def main():
    parser = argparse.ArgumentParser(description="튜닝 모니터링 shadow diff 비교")
    parser.add_argument("--start", required=True, help="시작일 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="종료일 YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "analytics" / "shadow_diff_summary.json"),
        help="결과 JSON 파일 경로",
    )
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    jsonl_metrics = _count_jsonl_metrics(start_date, end_date)
    duckdb_metrics = _count_duckdb_metrics(start_date, end_date)
    result = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": datetime.now().isoformat(),
        **_build_diff(jsonl_metrics, duckdb_metrics),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
