import csv
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

try:
    from src.engine.dashboard_data_repository import load_pipeline_events
except Exception:
    load_pipeline_events = None


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


def _process_pipeline_events_rows(rows, server_name, funnel_counts, trade_info, seq_info):
    for data in rows:
        stage = data.get("stage", "")
        record_id = data.get("record_id")
        if not record_id:
            continue

        date_str = data.get("emitted_date") or str(data.get("emitted_at", ""))[:10] or "unknown"

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

        outcome = data.get("outcome", "COMPLETED")
        profit_rate = data.get("profit_rate")
        profit_valid_flag = (
            outcome in {"GOOD_EXIT", "COMPLETED"} and isinstance(profit_rate, (int, float))
        )

        trade_facts.append(
            {
                "server": server_name,
                "trade_id": trade_id,
                "symbol": data.get("stock_code", ""),
                "entry_time": entry_time,
                "exit_time": exit_time,
                "held_sec": held_sec,
                "entry_mode": entry_mode,
                "exit_rule": data.get("exit_rule", ""),
                "status": outcome,
                "profit_rate": profit_rate if profit_valid_flag else "",
                "profit_valid_flag": "true" if profit_valid_flag else "false",
            }
        )


def _load_local_pipeline_rows(target_date: str) -> list[dict]:
    if load_pipeline_events is not None:
        try:
            rows = load_pipeline_events(target_date, include_file_for_today=True)
            if rows:
                return rows
        except Exception:
            pass

    for suffix in (".jsonl", ".jsonl.gz"):
        path = config.LOCAL_PIPELINE_DIR / f"pipeline_events_{target_date}{suffix}"
        if path.exists():
            return _load_jsonl_rows(path)
    return []


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


def main():
    print("Building datasets...")
    funnel_counts = defaultdict(lambda: defaultdict(int))
    trade_info = defaultdict(dict)
    seq_info = defaultdict(
        lambda: {"events": [], "partial_then_expand_flag": False, "multi_rebase_flag": False}
    )
    trade_facts = []

    # LOCAL pipeline: DB 우선 + 파일 fallback
    for date_str in _date_range(config.START_DATE, config.END_DATE):
        rows = _load_local_pipeline_rows(date_str)
        if rows:
            _process_pipeline_events_rows(rows, "local", funnel_counts, trade_info, seq_info)

    # LOCAL post-sell: 파일(jsonl/jsonl.gz)
    for file_path in _iter_jsonl_files(config.LOCAL_POST_SELL_EVAL_DIR, name_contains="evaluations"):
        _process_post_sell_rows(
            _load_jsonl_rows(file_path), "local", trade_info, seq_info, trade_facts
        )

    # REMOTE logs: 파일(jsonl/jsonl.gz)
    for file_path in _iter_jsonl_files(config.REMOTE_BASE_DIR):
        path_str = str(file_path)
        if "remote_" not in path_str:
            continue
        if "pipeline_events" in file_path.name:
            _process_pipeline_events_rows(
                _load_jsonl_rows(file_path), "remote", funnel_counts, trade_info, seq_info
            )
        if "post_sell_evaluations" in file_path.name:
            _process_post_sell_rows(
                _load_jsonl_rows(file_path), "remote", trade_info, seq_info, trade_facts
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
                "held_sec",
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
                    "partial_then_expand_flag": str(info["partial_then_expand_flag"]).lower(),
                    "multi_rebase_flag": str(info["multi_rebase_flag"]).lower(),
                    "rebase_integrity_flag": "true",
                    "same_symbol_repeat_flag": "false",
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
            f"- `COMPLETED` 수: {len([t for t in trade_facts if t['status'] == 'GOOD_EXIT' or t['status'] == 'COMPLETED'])}\n"
        )
        f.write(f"- `valid_profit_rate` 수: {len(valid_trades)}\n")
        f.write("- 서버별 `valid_profit_rate` 건수:\n")
        f.write(f"  - 로컬(local): {local_valid}\n")
        f.write(f"  - 원격(remote): {remote_valid}\n\n")

        if local_valid < config.MIN_VALID_SAMPLES or remote_valid < config.MIN_VALID_SAMPLES:
            f.write("## ⚠️ 실패 조건 도달\n")
            f.write(
                f"`profit_valid_flag=true` 표본이 서버별 {config.MIN_VALID_SAMPLES}건 미만이므로 **표본 부족**으로 결론을 확정할 수 없음.\n"
            )

    print("Dataset built successfully.")


if __name__ == "__main__":
    main()
