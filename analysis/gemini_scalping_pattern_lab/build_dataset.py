import csv
import gzip
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from . import config
except ImportError:  # pragma: no cover - direct script execution
    import config

try:
    from src.engine.tuning_duckdb_repository import TuningDuckDBRepository

    DUCKDB_AVAILABLE = True
except Exception:
    TuningDuckDBRepository = None
    DUCKDB_AVAILABLE = False

logger = logging.getLogger(__name__)

_DUCKDB_VIEW_READY = False


def _normalize_pipeline_row(row: dict) -> dict:
    """DuckDB parquet row를 pipeline_event 원형 스키마로 보정."""
    normalized = dict(row)
    fields: dict = {}
    for key in list(normalized.keys()):
        if key.startswith("fields_"):
            field_key = key.removeprefix("fields_")
            value = normalized.pop(key)
            if value is not None:
                fields[field_key] = value
    if fields:
        normalized["fields"] = fields
    record_id = normalized.get("record_id")
    if isinstance(record_id, float) and record_id.is_integer():
        normalized["record_id"] = int(record_id)
    return normalized


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    days: list[str] = []
    cur = start
    while cur <= end:
        days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def _load_jsonl_rows(file_path: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        if file_path.suffix == ".gz":
            stream = gzip.open(file_path, "rt", encoding="utf-8")
        else:
            stream = open(file_path, "r", encoding="utf-8")
        with stream as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    return rows


def _process_pipeline_events_rows(
    rows, server_name, funnel_counts, trade_info, seq_info
):
    for data in rows:
        stage = data.get("stage", "")
        record_id = data.get("record_id")
        if not record_id:
            continue

        date_str = (
            data.get("emitted_date")
            or str(data.get("emitted_at", ""))[:10]
            or "unknown"
        )

        if "latency_block" in stage:
            funnel_counts[date_str]["latency_block_events"] += 1
        elif "blocked_liquidity" in stage:
            funnel_counts[date_str]["liquidity_block_events"] += 1
        elif "blocked_strength" in stage or "ai_score" in stage:
            funnel_counts[date_str]["ai_threshold_block_events"] += 1

        fields = data.get("fields", {})
        if str(fields.get("overbought_blocked", "False")).lower() == "true":
            funnel_counts[date_str]["overbought_block_events"] += 1
        if "submitted" in stage:
            funnel_counts[date_str]["submitted_events"] += 1

        seq_info[record_id]["server"] = server_name
        # sequence_fact는 최대 10개 이벤트만 표시하므로 메모리 상한을 둔다.
        if len(seq_info[record_id]["events"]) < 10:
            seq_info[record_id]["events"].append(stage)

        if "entry_mode" in fields:
            trade_info[record_id]["entry_mode"] = fields["entry_mode"]
        if "holding_started" in stage or "entry_time" not in trade_info[record_id]:
            trade_info[record_id]["entry_time"] = data.get("emitted_at")
        if "fill_quality" in fields:
            trade_info[record_id]["fill_quality"] = fields["fill_quality"]
        if "partial_then_expand" in stage:
            seq_info[record_id]["partial_then_expand_flag"] = True
        if "rebase" in stage:
            seq_info[record_id]["multi_rebase_flag"] = True
            seq_info[record_id]["rebase_count"] += 1
        if "rebase_integrity" in stage:
            seq_info[record_id]["rebase_integrity_flag"] = True
        if "same_symbol_repeat" in stage:
            seq_info[record_id]["same_symbol_repeat_flag"] = True


def _derive_cohort(entry_mode: str, fill_quality: str, seq_flags: dict) -> str:
    if seq_flags.get("partial_then_expand_flag") or seq_flags.get("multi_rebase_flag"):
        return "split-entry"
    if fill_quality == "PARTIAL_FILL" or entry_mode == "partial":
        return "partial_fill"
    return "full_fill"


def _process_post_sell_rows(rows, server_name, trade_info, seq_info, trade_facts):
    for data in rows:
        trade_id = data.get("post_sell_id") or str(data.get("recommendation_id"))
        rec_id = data.get("recommendation_id")
        if not trade_id:
            continue

        t_info = trade_info.get(rec_id, {})
        entry_time = t_info.get("entry_time", "")
        exit_time = data.get("sell_time", "")

        held_sec = 0
        if entry_time and exit_time:
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                if "T" in exit_time:
                    exit_dt = datetime.fromisoformat(exit_time)
                else:
                    exit_dt = datetime.strptime(
                        f"{data.get('signal_date', '1970-01-01')}T{exit_time}",
                        "%Y-%m-%dT%H:%M:%S",
                    )
                held_sec = int((exit_dt - entry_dt).total_seconds())
                if held_sec < 0:
                    held_sec = 0
            except Exception:
                pass

        entry_mode = t_info.get("entry_mode", "full")
        if t_info.get("fill_quality") == "PARTIAL_FILL":
            entry_mode = "partial"
        seq_flags = seq_info.get(rec_id, {})
        cohort = _derive_cohort(
            entry_mode=entry_mode,
            fill_quality=t_info.get("fill_quality", ""),
            seq_flags=seq_flags,
        )
        rec_date = (
            data.get("signal_date") or str(entry_time)[:10] or str(exit_time)[:10] or ""
        )

        outcome = data.get("outcome", "COMPLETED")
        profit_rate = data.get("profit_rate")
        profit_valid_flag = outcome == "COMPLETED" and isinstance(
            profit_rate, (int, float)
        )

        trade_facts.append(
            {
                "server": server_name,
                "trade_id": trade_id,
                "symbol": data.get("stock_code", ""),
                "entry_time": entry_time,
                "exit_time": exit_time,
                "rec_date": rec_date,
                "held_sec": held_sec,
                "cohort": cohort,
                "entry_mode": entry_mode,
                "exit_rule": data.get("exit_rule", ""),
                "status": outcome,
                "profit_rate": profit_rate if profit_valid_flag else "",
                "profit_valid_flag": "true" if profit_valid_flag else "false",
            }
        )


def _load_from_duckdb(target_date: str) -> list[dict]:
    """DuckDB에서 pipeline_events 로드 (날짜 필터 적용)."""
    global _DUCKDB_VIEW_READY
    if not DUCKDB_AVAILABLE:
        return []
    try:
        # read_only=False로 열어야 VIEW 생성이 가능하다.
        with TuningDuckDBRepository(read_only=False) as repo:
            if not _DUCKDB_VIEW_READY:
                repo.register_parquet_dataset("pipeline_events")
                _DUCKDB_VIEW_READY = True
            # 날짜 범위 쿼리
            df = repo.query(
                """
                SELECT
                    stage,
                    record_id,
                    emitted_date,
                    emitted_at,
                    fields_overbought_blocked,
                    fields_entry_mode,
                    fields_fill_quality
                FROM v_pipeline_events
                WHERE emitted_date = ?
                """,
                [target_date],
            )
        if df.empty:
            return []
        # DataFrame을 원본 JSON 형식으로 변환
        rows = df.to_dict(orient="records")
        return [_normalize_pipeline_row(r) for r in rows]
    except Exception as e:
        logger.warning("DuckDB 로드 실패 %s: %s", target_date, e)
        return []


def _load_local_pipeline_rows(target_date: str) -> tuple[list[dict], str]:
    # 새 아키텍처: DuckDB 우선 -> 파일 -> DB fallback
    # 1. DuckDB
    if DUCKDB_AVAILABLE:
        rows = _load_from_duckdb(target_date)
        if rows:
            return rows, "duckdb"
    # 2. 파일
    for suffix in (".jsonl", ".jsonl.gz"):
        path = config.LOCAL_PIPELINE_DIR / f"pipeline_events_{target_date}{suffix}"
        if path.exists():
            rows = _load_jsonl_rows(path)
            if rows:
                return rows, "jsonl"
    # legacy DB fallback 제거: 운영 canonical source는 parquet/DuckDB + jsonl이다.
    return [], "none"


def _iter_jsonl_files(base_dir: Path, *, name_contains: str | None = None):
    if not base_dir.exists():
        return
    for root, _, files in os.walk(base_dir):
        for filename in sorted(files):
            if not (filename.endswith(".jsonl") or filename.endswith(".jsonl.gz")):
                continue
            if name_contains and name_contains not in filename:
                continue
            yield Path(root) / filename


def _extract_date_token(name: str) -> str | None:
    # pipeline_events_YYYY-MM-DD(.jsonl/.jsonl.gz), date=YYYY-MM-DD 폴더명 지원
    if "date=" in name:
        token = name.split("date=", 1)[1][:10]
        try:
            date.fromisoformat(token)
            return token
        except ValueError:
            return None
    for idx in range(len(name) - 9):
        token = name[idx : idx + 10]
        try:
            date.fromisoformat(token)
            return token
        except ValueError:
            continue
    return None


def _discover_available_pipeline_dates() -> set[str]:
    dates: set[str] = set()
    for path in _iter_jsonl_files(
        config.LOCAL_PIPELINE_DIR, name_contains="pipeline_events_"
    ):
        token = _extract_date_token(path.name)
        if token:
            dates.add(token)

    parquet_dir = config.ANALYTICS_PARQUET_ROOT / "pipeline_events"
    if parquet_dir.exists():
        for part in parquet_dir.glob("date=*"):
            token = _extract_date_token(part.name)
            if token:
                dates.add(token)
    return dates


def main():
    print("Building datasets...")
    funnel_counts = defaultdict(lambda: defaultdict(int))
    trade_info = defaultdict(dict)
    seq_info = defaultdict(
        lambda: {
            "events": [],
            "partial_then_expand_flag": False,
            "multi_rebase_flag": False,
            "rebase_integrity_flag": False,
            "same_symbol_repeat_flag": False,
            "same_ts_multi_rebase_flag": False,
            "rebase_count": 0,
        }
    )
    trade_facts = []
    all_dates = _date_range(config.START_DATE, config.END_DATE)
    available_dates = _discover_available_pipeline_dates()
    target_date_tokens = set(all_dates)
    local_pipeline_sources = defaultdict(int)
    covered_dates = set()

    # LOCAL pipeline: DuckDB 우선 + 파일/DB fallback
    for date_str in all_dates:
        rows, source = _load_local_pipeline_rows(date_str)
        local_pipeline_sources[source] += 1
        if rows:
            covered_dates.add(date_str)
            _process_pipeline_events_rows(
                rows, "local", funnel_counts, trade_info, seq_info
            )

    # LOCAL post-sell: 파일(jsonl/jsonl.gz)
    for file_path in _iter_jsonl_files(
        config.LOCAL_POST_SELL_EVAL_DIR, name_contains="evaluations"
    ):
        if not any(token in file_path.name for token in target_date_tokens):
            continue
        _process_post_sell_rows(
            _load_jsonl_rows(file_path), "local", trade_info, seq_info, trade_facts
        )

    # REMOTE logs are excluded by default; Plan Rebase decisions are main/local-only.
    if config.INCLUDE_REMOTE:
        for file_path in _iter_jsonl_files(config.REMOTE_BASE_DIR):
            path_str = str(file_path)
            if "remote_" not in path_str:
                continue
            if not any(token in file_path.name for token in target_date_tokens):
                continue
            if "pipeline_events" in file_path.name:
                _process_pipeline_events_rows(
                    _load_jsonl_rows(file_path),
                    "remote",
                    funnel_counts,
                    trade_info,
                    seq_info,
                )
            if "post_sell_evaluations" in file_path.name:
                _process_post_sell_rows(
                    _load_jsonl_rows(file_path),
                    "remote",
                    trade_info,
                    seq_info,
                    trade_facts,
                )

    trade_fact_path = config.OUTPUT_DIR / "trade_fact.csv"
    with open(trade_fact_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "server",
                "trade_id",
                "symbol",
                "entry_time",
                "exit_time",
                "rec_date",
                "held_sec",
                "cohort",
                "entry_mode",
                "exit_rule",
                "status",
                "profit_rate",
                "profit_valid_flag",
            ],
        )
        writer.writeheader()
        writer.writerows(trade_facts)

    funnel_fact_path = config.OUTPUT_DIR / "funnel_fact.csv"
    with open(funnel_fact_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "server",
                "date",
                "latency_block_events",
                "liquidity_block_events",
                "ai_threshold_block_events",
                "overbought_block_events",
                "submitted_events",
            ],
        )
        writer.writeheader()
        for date_key, counts in funnel_counts.items():
            row = {"server": "mixed", "date": date_key}
            row.update(counts)
            writer.writerow(row)

    seq_fact_path = config.OUTPUT_DIR / "sequence_fact.csv"
    with open(seq_fact_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "server",
                "trade_id",
                "event_seq",
                "partial_then_expand_flag",
                "multi_rebase_flag",
                "rebase_integrity_flag",
                "same_symbol_repeat_flag",
                "same_ts_multi_rebase_flag",
                "rebase_count",
            ],
        )
        writer.writeheader()
        for rec_id, info in seq_info.items():
            if not info["events"]:
                continue
            writer.writerow(
                {
                    "server": info.get("server", "unknown"),
                    "trade_id": rec_id,
                    "event_seq": "->".join(info["events"][:10]),
                    "partial_then_expand_flag": str(
                        info["partial_then_expand_flag"]
                    ).lower(),
                    "multi_rebase_flag": str(info["multi_rebase_flag"]).lower(),
                    "rebase_integrity_flag": str(info["rebase_integrity_flag"]).lower(),
                    "same_symbol_repeat_flag": str(
                        info["same_symbol_repeat_flag"]
                    ).lower(),
                    "same_ts_multi_rebase_flag": str(
                        info["same_ts_multi_rebase_flag"]
                    ).lower(),
                    "rebase_count": info["rebase_count"],
                }
            )

    report_path = config.OUTPUT_DIR / "data_quality_report.md"
    total_trades = len(trade_facts)
    valid_trades = [t for t in trade_facts if t["profit_valid_flag"] == "true"]
    local_valid = len([t for t in valid_trades if t["server"] == "local"])
    remote_valid = len([t for t in valid_trades if t["server"] == "remote"])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Data Quality Report\n\n")
        f.write(f"- 총 거래수: {total_trades}\n")
        f.write(
            f"- `COMPLETED` 수: {len([t for t in trade_facts if t['status'] == 'COMPLETED'])}\n"
        )
        f.write(f"- `valid_profit_rate` 수: {len(valid_trades)}\n")
        f.write("- 서버별 `valid_profit_rate` 건수:\n")
        f.write(f"  - 로컬(local): {local_valid}\n")
        f.write(f"  - 원격(remote): {remote_valid}\n\n")

        remote_sample_block = (
            config.INCLUDE_REMOTE and remote_valid < config.MIN_VALID_SAMPLES
        )
        if local_valid < config.MIN_VALID_SAMPLES or remote_sample_block:
            f.write("## ⚠️ 실패 조건 도달\n")
            f.write(
                f"`profit_valid_flag=true` 표본이 기준별 {config.MIN_VALID_SAMPLES}건 미만이므로 **표본 부족**으로 결론을 확정할 수 없음.\n"
            )

    # run_manifest.json 작성
    manifest_path = config.OUTPUT_DIR / "run_manifest.json"
    import json
    from datetime import datetime

    used_sources = {
        k for k, v in local_pipeline_sources.items() if v > 0 and k != "none"
    }
    if used_sources == {"duckdb"}:
        data_source_mode = "duckdb_primary"
    elif used_sources == {"jsonl"}:
        data_source_mode = "jsonl_fallback"
    elif used_sources == {"db"}:
        data_source_mode = "db_fallback"
    elif used_sources:
        data_source_mode = "mixed"
    else:
        data_source_mode = "none"

    expected_dates = sorted(d for d in all_dates if d in available_dates)
    if not expected_dates:
        expected_dates = all_dates
    history_coverage_start = expected_dates[0] if expected_dates else None
    history_coverage_end = expected_dates[-1] if expected_dates else None
    history_coverage_ok = (
        set(expected_dates).issubset(covered_dates) and len(expected_dates) > 0
    )
    manifest = {
        "run_at": datetime.now().isoformat(),
        "data_source_mode": data_source_mode,
        "history_coverage_start": history_coverage_start,
        "history_coverage_end": history_coverage_end,
        "history_coverage_ok": history_coverage_ok,
        "history_expected_dates": expected_dates,
        "local_pipeline_source_stats": dict(local_pipeline_sources),
        "include_remote": bool(config.INCLUDE_REMOTE),
        "total_trades": total_trades,
        "valid_trades": len(valid_trades),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("Dataset built successfully.")


if __name__ == "__main__":
    main()
