"""
데이터 준비 모듈.

입력:
  - monitor snapshots: DB 우선, 파일(.json/.json.gz) fallback
  - pipeline events: DB 우선, 파일(.jsonl/.jsonl.gz) fallback

출력:
  - outputs/trade_fact.csv
  - outputs/funnel_fact.csv
  - outputs/sequence_fact.csv
  - outputs/data_quality_report.md
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

LAB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = LAB_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(LAB_DIR))
from config import (
    ANALYSIS_END,
    ANALYSIS_START,
    FUNNEL_METRIC_MAP,
    OUTPUT_DIR,
    PIPELINE_EVENT_DIR,
    SEQUENCE_STAGES,
    SERVER_LOCAL,
    SERVER_REMOTE,
    SNAPSHOT_DIR,
    SPLIT_ENTRY_REBASE_THRESHOLD,
)

try:
    from src.engine.dashboard_data_repository import (
        load_monitor_snapshot_prefer_db,
        load_pipeline_events,
    )
except Exception:
    load_monitor_snapshot_prefer_db = None
    load_pipeline_events = None


def _load_json(path: Path) -> dict | None:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as f:
                return json.load(f)
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [WARN] json load failed: {path.name} — {e}")
        return None


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        if path.suffix == ".gz":
            stream = gzip.open(path, "rt", encoding="utf-8")
        else:
            stream = open(path, encoding="utf-8")
        with stream as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    rows.append(json.loads(raw_line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"  [WARN] jsonl load failed: {path.name} — {e}")
    return rows


def _load_snapshot_payload(kind: str, target_date: str) -> tuple[dict | None, str]:
    if load_monitor_snapshot_prefer_db is not None:
        try:
            payload = load_monitor_snapshot_prefer_db(kind, target_date)
            if payload is not None:
                source = payload.get("meta", {}).get("source", "db")
                return payload, str(source)
        except Exception as e:
            print(f"  [WARN] snapshot DB load failed: {kind} {target_date} — {e}")

    for suffix in (".json", ".json.gz"):
        path = SNAPSHOT_DIR / f"{kind}_{target_date}{suffix}"
        if path.exists():
            payload = _load_json(path)
            if payload is not None:
                return payload, f"file:{suffix}"
    return None, "none"


def _load_pipeline_rows(target_date: str) -> tuple[list[dict], str]:
    if load_pipeline_events is not None:
        try:
            rows = load_pipeline_events(target_date, include_file_for_today=True)
            if rows:
                return rows, "db_or_mixed"
        except Exception as e:
            print(f"  [WARN] pipeline DB load failed: {target_date} — {e}")

    for suffix in (".jsonl", ".jsonl.gz"):
        path = PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}{suffix}"
        if path.exists():
            rows = _load_jsonl(path)
            if rows:
                return rows, f"file:{suffix}"
    return [], "none"


# ── 날짜 범위 생성 ────────────────────────────────────────────────────────────

def _date_range(start: date, end: date) -> list[date]:
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


# ── trade_fact 파싱 ───────────────────────────────────────────────────────────

def _parse_trade_review(data: dict[str, Any], server: str) -> list[dict]:
    rows = []
    # completed_trades + open_trades (open은 profit_valid_flag=False)
    all_trades = data.get("sections", {}).get("recent_trades", [])

    for t in all_trades:
        status = t.get("status", "")
        profit_rate = t.get("profit_rate")
        profit_valid = (
            status == "COMPLETED"
            and profit_rate is not None
            and isinstance(profit_rate, (int, float))
        )
        exit_signal = t.get("exit_signal") or {}
        exit_rule = exit_signal.get("exit_rule") or ""

        # timeline에서 holding_started 수 집계 (split-entry 보조 지표)
        timeline = t.get("timeline") or []
        holding_started_count = sum(
            1 for ev in timeline if ev.get("stage") == "holding_started"
        )

        rows.append({
            "server":        server,
            "trade_id":      t.get("id"),
            "symbol":        t.get("code", ""),
            "name":          t.get("name", ""),
            "entry_time":    t.get("buy_time", ""),
            "exit_time":     t.get("sell_time", ""),
            "held_sec":      t.get("holding_seconds"),
            "entry_mode":    t.get("entry_mode", ""),
            "position_tag":  t.get("position_tag", ""),
            "exit_rule":     exit_rule,
            "status":        status,
            "profit_rate":   profit_rate if profit_valid else None,
            "profit_valid_flag": profit_valid,
            "holding_started_count": holding_started_count,
            "rec_date":      t.get("rec_date", ""),
        })
    return rows


def build_trade_fact() -> pd.DataFrame:
    print("[prepare] building trade_fact …")
    rows: list[dict] = []
    parse_errors = 0
    source_count: dict[str, int] = defaultdict(int)

    for d in _date_range(ANALYSIS_START, ANALYSIS_END):
        ds = d.isoformat()
        payload, source = _load_snapshot_payload("trade_review", ds)
        if payload is None:
            continue
        source_count[source] += 1
        result = _parse_trade_review(payload, SERVER_LOCAL)
        if not result:
            parse_errors += 1
        rows.extend(result)

    df = pd.DataFrame(rows)
    if df.empty:
        print("  [WARN] trade_fact is empty")
        return df

    # cohort 컬럼 초기화 (sequence_fact join 후 갱신)
    df["cohort"] = df["entry_mode"].apply(
        lambda m: "full_fill" if m == "normal" else "partial_fill"
    )
    df.to_csv(OUTPUT_DIR / "trade_fact.csv", index=False, encoding="utf-8")
    print(
        f"  → trade_fact: {len(df)} rows, {parse_errors} parse errors, "
        f"source={dict(source_count)}"
    )
    return df


# ── funnel_fact 파싱 ──────────────────────────────────────────────────────────

def _parse_performance_tuning(data: dict[str, Any], target_date: str, server: str) -> dict:
    metrics = data.get("metrics", {})
    date_str = data.get("date", target_date)

    row: dict[str, Any] = {"server": server, "date": date_str}
    for col, src_key in FUNNEL_METRIC_MAP.items():
        row[col] = metrics.get(src_key, 0) or 0

    # liquidity_block_events는 별도 집계 키가 없으면 budget_pass - latency_pass로 추산
    if row.get("liquidity_block_events", 0) == 0:
        budget = metrics.get("budget_pass_events", 0) or 0
        latency_pass = metrics.get("latency_pass_events", 0) or 0
        latency_block = metrics.get("latency_block_events", 0) or 0
        submitted = metrics.get("order_bundle_submitted_events", 0) or 0
        # budget_pass = latency_pass + submitted → liquidity 차단 없음으로 0 처리
        row["liquidity_block_events"] = 0

    return row


def build_funnel_fact() -> pd.DataFrame:
    print("[prepare] building funnel_fact …")
    rows = []
    source_count: dict[str, int] = defaultdict(int)
    for d in _date_range(ANALYSIS_START, ANALYSIS_END):
        ds = d.isoformat()
        payload, source = _load_snapshot_payload("performance_tuning", ds)
        if payload is None:
            continue
        source_count[source] += 1
        rows.append(_parse_performance_tuning(payload, ds, SERVER_LOCAL))

    df = pd.DataFrame(rows)
    if df.empty:
        print("  [WARN] funnel_fact is empty")
        return df
    df.to_csv(OUTPUT_DIR / "funnel_fact.csv", index=False, encoding="utf-8")
    print(f"  → funnel_fact: {len(df)} rows, source={dict(source_count)}")
    return df


# ── sequence_fact 파싱 (JSONL 스트리밍) ──────────────────────────────────────

def _stream_sequence_events(
    rows: list[dict],
    date_str: str,
    server: str,
) -> list[dict]:
    """
    JSONL을 스트리밍해 record_id별 시퀀스 특징을 집계한다.
    메모리 효율을 위해 필요한 stage만 필터링한다.
    """
    # record_id → 집계 버킷
    buckets: dict[int, dict] = defaultdict(lambda: {
        "server":                server,
        "date":                  date_str,
        "trade_id":              None,
        "symbol":                "",
        "holding_started_times": [],
        "rebase_events":         [],   # list of fields dicts
        "exit_rules":            [],
        "exit_times":            [],
    })

    # 동일 종목 repeat soft-stop 추적 (date 단위)
    soft_stop_by_symbol: dict[str, int] = defaultdict(int)  # symbol → count
    symbol_soft_stop_times: dict[str, list[str]] = defaultdict(list)

    try:
        for ev in rows:
            stage = ev.get("stage", "")
            if stage not in SEQUENCE_STAGES:
                continue

            rid = ev.get("record_id")
            if rid is None:
                continue

            b = buckets[rid]
            b["trade_id"] = rid
            if not b["symbol"]:
                b["symbol"] = ev.get("stock_code", "")

            ts = ev.get("emitted_at", "")

            if stage == "holding_started":
                b["holding_started_times"].append(ts)

            elif stage == "position_rebased_after_fill":
                fields = ev.get("fields", {})
                b["rebase_events"].append({
                    "ts":              ts,
                    "fill_qty":        fields.get("fill_qty"),
                    "cum_filled_qty":  fields.get("cum_filled_qty"),
                    "requested_qty":   fields.get("requested_qty"),
                    "remaining_qty":   fields.get("remaining_qty"),
                    "fill_quality":    fields.get("fill_quality", ""),
                    "entry_mode":      fields.get("entry_mode", ""),
                })

            elif stage in ("exit_signal", "sell_completed"):
                fields = ev.get("fields", {})
                rule = fields.get("exit_rule", "")
                if rule:
                    b["exit_rules"].append(rule)
                    b["exit_times"].append(ts)
                    # soft-stop 반복 추적
                    if rule == "scalp_soft_stop_pct" and b["symbol"]:
                        soft_stop_by_symbol[b["symbol"]] += 1
                        symbol_soft_stop_times[b["symbol"]].append(ts)

    except Exception as e:
        print(f"  [WARN] sequence stream error: {date_str} — {e}")
        return []

    # 반복 soft-stop 기호 목록
    repeat_symbols = {sym for sym, cnt in soft_stop_by_symbol.items() if cnt >= 2}

    rows = []
    for rid, b in buckets.items():
        rebase_events = b["rebase_events"]
        rebase_count = len(rebase_events)
        holding_count = len(b["holding_started_times"])
        exit_rules = b["exit_rules"]

        # ── cohort 플래그 ──────────────────────────────────────────────────
        multi_rebase_flag = rebase_count >= SPLIT_ENTRY_REBASE_THRESHOLD

        # partial 이후 확대: PARTIAL_FILL 이후 추가 rebase 발생
        had_partial = any(
            r.get("fill_quality", "").upper() == "PARTIAL_FILL"
            for r in rebase_events
        )
        had_expand = rebase_count >= 2
        partial_then_expand_flag = had_partial and had_expand

        # rebase 정합성 이상
        rebase_integrity_flag = False
        for r in rebase_events:
            try:
                cum = int(r.get("cum_filled_qty") or 0)
                req = int(r.get("requested_qty") or 0)
                fq  = r.get("fill_quality", "").upper()
                if cum > req and req > 0:
                    rebase_integrity_flag = True
                if req == 0 and fq == "UNKNOWN":
                    rebase_integrity_flag = True
            except (TypeError, ValueError):
                pass

        # same_ts 다중 rebase (동일 초에 2건 이상)
        ts_seconds = [r["ts"][:19] for r in rebase_events if r.get("ts")]
        same_ts_multi_rebase = len(ts_seconds) != len(set(ts_seconds)) if ts_seconds else False

        same_symbol_repeat_flag = b["symbol"] in repeat_symbols

        # entry_mode 대표값 (첫 번째 rebase 이벤트 기준)
        entry_mode = rebase_events[0].get("entry_mode", "") if rebase_events else ""

        # 최종 exit_rule
        final_exit_rule = exit_rules[-1] if exit_rules else ""

        # event_seq: holding_count + rebase_count 표현
        event_seq = f"h{holding_count}_r{rebase_count}"

        rows.append({
            "server":                  server,
            "trade_id":                rid,
            "date":                    date_str,
            "symbol":                  b["symbol"],
            "event_seq":               event_seq,
            "holding_started_count":   holding_count,
            "rebase_count":            rebase_count,
            "entry_mode":              entry_mode,
            "final_exit_rule":         final_exit_rule,
            "partial_then_expand_flag": partial_then_expand_flag,
            "multi_rebase_flag":       multi_rebase_flag,
            "rebase_integrity_flag":   rebase_integrity_flag,
            "same_ts_multi_rebase_flag": same_ts_multi_rebase,
            "same_symbol_repeat_flag": same_symbol_repeat_flag,
        })
    return rows


def build_sequence_fact() -> pd.DataFrame:
    print("[prepare] building sequence_fact (streaming JSONL) …")
    all_rows: list[dict] = []
    source_count: dict[str, int] = defaultdict(int)

    for d in _date_range(ANALYSIS_START, ANALYSIS_END):
        ds = d.isoformat()
        rows, source = _load_pipeline_rows(ds)
        if not rows:
            continue
        source_count[source] += 1
        print(f"  streaming pipeline_events_{ds} ({source}) …")
        parsed_rows = _stream_sequence_events(rows, ds, SERVER_LOCAL)
        print(f"    → {len(parsed_rows)} records")
        all_rows.extend(parsed_rows)

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("  [WARN] sequence_fact is empty")
        return df
    df.to_csv(OUTPUT_DIR / "sequence_fact.csv", index=False, encoding="utf-8")
    print(f"  → sequence_fact: {len(df)} rows, source={dict(source_count)}")
    return df


# ── trade_fact 코호트 갱신 (sequence_fact join) ───────────────────────────────

def enrich_trade_cohort(
    trade_df: pd.DataFrame,
    seq_df: pd.DataFrame,
) -> pd.DataFrame:
    if trade_df.empty or seq_df.empty:
        return trade_df

    # sequence_fact에서 split-entry 판정용 컬럼만 추출
    seq_key = seq_df[["trade_id", "multi_rebase_flag",
                       "partial_then_expand_flag", "rebase_integrity_flag",
                       "same_symbol_repeat_flag", "rebase_count"]].copy()
    seq_key = seq_key.rename(columns={"trade_id": "trade_id"})
    # trade_id 기준 중복 제거 (마지막 우선)
    seq_key = seq_key.drop_duplicates(subset="trade_id", keep="last")

    merged = trade_df.merge(seq_key, on="trade_id", how="left")

    # cohort 재분류
    def classify(row: pd.Series) -> str:
        if pd.notna(row.get("multi_rebase_flag")) and row["multi_rebase_flag"]:
            return "split-entry"
        if row.get("entry_mode") == "fallback":
            return "partial_fill"
        return "full_fill"

    merged["cohort"] = merged.apply(classify, axis=1)
    # suffix 컬럼 정리
    for col in ["multi_rebase_flag", "partial_then_expand_flag",
                "rebase_integrity_flag", "same_symbol_repeat_flag", "rebase_count"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(False)

    merged.to_csv(OUTPUT_DIR / "trade_fact.csv", index=False, encoding="utf-8")
    return merged


# ── 품질 보고서 ───────────────────────────────────────────────────────────────

def build_quality_report(
    trade_df: pd.DataFrame,
    funnel_df: pd.DataFrame,
    seq_df: pd.DataFrame,
) -> None:
    print("[prepare] building data_quality_report …")

    lines: list[str] = [
        "# 데이터 품질 보고서",
        "",
        f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"분석 기간: {ANALYSIS_START} ~ {ANALYSIS_END}",
        "",
        "---",
        "",
        "## 1. trade_fact",
        "",
    ]

    if trade_df.empty:
        lines.append("- **데이터 없음**")
    else:
        total = len(trade_df)
        completed = int(trade_df["status"].eq("COMPLETED").sum())
        valid_profit = int(trade_df["profit_valid_flag"].sum())
        excluded = total - valid_profit
        by_server = trade_df.groupby("server").size().to_dict()
        by_cohort = trade_df.groupby("cohort").size().to_dict() if "cohort" in trade_df else {}

        lines += [
            f"| 항목 | 값 |",
            f"|---|---|",
            f"| 총 거래수 | {total} |",
            f"| COMPLETED | {completed} |",
            f"| valid_profit_rate | {valid_profit} |",
            f"| 제외 건수 | {excluded} |",
            "",
            "**서버별:**",
            "",
        ]
        for srv, cnt in by_server.items():
            lines.append(f"- `{srv}`: {cnt}건")

        lines.append("")
        lines.append("**코호트별:**")
        lines.append("")
        for coh, cnt in by_cohort.items():
            lines.append(f"- `{coh}`: {cnt}건")

        # 표본 부족 경고
        lines.append("")
        for srv in trade_df["server"].unique():
            srv_valid = int(
                trade_df[(trade_df["server"] == srv) & trade_df["profit_valid_flag"]].shape[0]
            )
            if srv_valid < 30:
                lines.append(
                    f"> ⚠️ **표본 부족**: `{srv}` 서버 valid_profit_rate={srv_valid}건 < 30. "
                    "이 서버 기준 결론 확정 금지."
                )

    lines += ["", "---", "", "## 2. funnel_fact", ""]
    if funnel_df.empty:
        lines.append("- **데이터 없음**")
    else:
        lines += [
            f"- 날짜 수: {len(funnel_df)}",
            f"- 서버: {list(funnel_df['server'].unique())}",
            f"- 기간 합계 latency_block_events: {int(funnel_df['latency_block_events'].sum())}",
            f"- 기간 합계 submitted_events: {int(funnel_df['submitted_events'].sum())}",
        ]

    lines += ["", "---", "", "## 3. sequence_fact", ""]
    if seq_df.empty:
        lines.append("- **데이터 없음**")
    else:
        total_seq = len(seq_df)
        multi_r = int(seq_df["multi_rebase_flag"].sum()) if "multi_rebase_flag" in seq_df else 0
        partial_exp = int(seq_df["partial_then_expand_flag"].sum()) if "partial_then_expand_flag" in seq_df else 0
        integrity = int(seq_df["rebase_integrity_flag"].sum()) if "rebase_integrity_flag" in seq_df else 0
        same_ts = int(seq_df["same_ts_multi_rebase_flag"].sum()) if "same_ts_multi_rebase_flag" in seq_df else 0
        repeat = int(seq_df["same_symbol_repeat_flag"].sum()) if "same_symbol_repeat_flag" in seq_df else 0

        lines += [
            f"| 플래그 | 건수 |",
            f"|---|---|",
            f"| 총 record 수 | {total_seq} |",
            f"| multi_rebase (split-entry) | {multi_r} |",
            f"| partial_then_expand | {partial_exp} |",
            f"| rebase_integrity 이상 | {integrity} |",
            f"| same_ts_multi_rebase | {same_ts} |",
            f"| same_symbol_repeat_soft_stop | {repeat} |",
        ]

        # 정합성 플래그 분포 (cum_gt_requested / same_ts_multi_rebase / requested0_unknown)
        lines += ["", "**정합성 플래그 분포:**", ""]
        lines.append(f"- `rebase_integrity_flag`: {integrity}건")
        lines.append(f"- `same_ts_multi_rebase_flag`: {same_ts}건")

    lines += ["", "---", "", "## 4. 서버별 파싱 메모", ""]
    lines.append("- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.")
    lines.append("- 원격 비교는 server_comparison_*.md 참조.")

    report_path = OUTPUT_DIR / "data_quality_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → {report_path}")


# ── 진입점 ────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    trade_df  = build_trade_fact()
    funnel_df = build_funnel_fact()
    seq_df    = build_sequence_fact()

    if not trade_df.empty and not seq_df.empty:
        trade_df = enrich_trade_cohort(trade_df, seq_df)

    build_quality_report(trade_df, funnel_df, seq_df)
    print("[prepare] done.")


if __name__ == "__main__":
    main()
