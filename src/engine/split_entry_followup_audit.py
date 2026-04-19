"""Helpers for noon follow-up audits around latency canary and split-entry soft stops."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


LATENCY_STAGES = {"latency_block", "latency_pass"}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = line.strip()
        if not raw:
            continue
        rows.append(json.loads(raw))
    return rows


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return default


def _is_truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def summarize_latency_canary(pipeline_events_path: Path) -> dict[str, Any]:
    rows = _load_jsonl(pipeline_events_path)
    stage_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    quote_not_stale_blocks = 0

    for row in rows:
        if row.get("pipeline") != "ENTRY_PIPELINE":
            continue
        stage = str(row.get("stage") or "")
        if stage not in LATENCY_STAGES:
            continue
        fields = row.get("fields") or {}
        stage_counts[stage] += 1
        if stage == "latency_block" and str(fields.get("quote_stale") or "").strip().lower() in {"false", "0", "no"}:
            quote_not_stale_blocks += 1
        reason = str(fields.get("latency_canary_reason") or "").strip()
        if reason:
            reason_counts[reason] += 1

    return {
        "stage_counts": dict(stage_counts),
        "latency_block_quote_not_stale": int(quote_not_stale_blocks),
        "latency_canary_reasons": dict(reason_counts),
        "latency_canary_applied": int(reason_counts.get("canary_applied", 0)),
    }


def summarize_split_entry_soft_stop(pipeline_events_path: Path) -> dict[str, Any]:
    rows = _load_jsonl(pipeline_events_path)
    by_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("pipeline") != "HOLDING_PIPELINE":
            continue
        record_id = row.get("record_id")
        if record_id in {None, ""}:
            continue
        by_record[str(record_id)].append(row)

    cases: list[dict[str, Any]] = []
    same_symbol_counts: Counter[str] = Counter()

    for record_id, events in by_record.items():
        sorted_events = sorted(events, key=lambda item: str(item.get("emitted_at") or ""))
        exit_events = [row for row in sorted_events if str(row.get("stage") or "") == "exit_signal"]
        if not exit_events:
            continue

        exit_fields = exit_events[-1].get("fields") or {}
        if str(exit_fields.get("exit_rule") or "") != "scalp_soft_stop_pct":
            continue

        rebase_events = [row for row in sorted_events if str(row.get("stage") or "") == "position_rebased_after_fill"]
        if not rebase_events:
            continue

        partial_rebases = [row for row in rebase_events if str((row.get("fields") or {}).get("fill_quality") or "").upper() == "PARTIAL_FILL"]
        split_entry = len(rebase_events) >= 2 or bool(partial_rebases)
        if not split_entry:
            continue

        first_partial_cum = _to_int((partial_rebases[0].get("fields") or {}).get("cum_filled_qty")) if partial_rebases else 0
        max_rebased_qty = max(_to_int((row.get("fields") or {}).get("cum_filled_qty")) for row in rebase_events)
        expanded_after_partial = bool(partial_rebases) and max_rebased_qty > first_partial_cum
        partial_only = bool(partial_rebases) and not expanded_after_partial

        integrity_flags: set[str] = set()
        same_ts_counts: Counter[str] = Counter()
        for row in rebase_events:
            fields = row.get("fields") or {}
            requested_qty = _to_int(fields.get("requested_qty"))
            cum_filled_qty = _to_int(fields.get("cum_filled_qty"))
            fill_quality = str(fields.get("fill_quality") or "").upper()
            if requested_qty > 0 and cum_filled_qty > requested_qty:
                integrity_flags.add("cum_gt_requested")
            if requested_qty == 0 and fill_quality == "UNKNOWN":
                integrity_flags.add("requested0_unknown")
            same_ts_counts[str(row.get("emitted_at") or "")[:19]] += 1
        if any(count >= 2 and ts for ts, count in same_ts_counts.items()):
            integrity_flags.add("same_ts_multi_rebase")

        buy_qty = 0
        for row in sorted_events:
            if str(row.get("stage") or "") != "holding_started":
                continue
            buy_qty = max(buy_qty, _to_int((row.get("fields") or {}).get("buy_qty")))
        if buy_qty <= 0:
            buy_qty = max_rebased_qty

        name = str(exit_events[-1].get("stock_name") or "")
        same_symbol_counts[name] += 1
        case = {
            "id": _to_int(record_id),
            "name": name,
            "buy_qty": int(buy_qty),
            "rebase_count": int(len(rebase_events)),
            "expanded_after_partial": bool(expanded_after_partial),
            "partial_only": bool(partial_only),
            "held_sec": _to_int(exit_fields.get("held_sec")),
            "profit_rate": _to_float(exit_fields.get("profit_rate")),
            "peak_profit": _to_float(exit_fields.get("peak_profit")),
            "integrity_flags": sorted(integrity_flags),
        }
        cases.append(case)

    cases.sort(key=lambda item: int(item.get("id") or 0))
    expanded_cases = [case for case in cases if case.get("expanded_after_partial")]
    repeats = {name: count for name, count in same_symbol_counts.items() if count >= 2}

    return {
        "case_count": int(len(cases)),
        "expanded_after_partial_count": int(len(expanded_cases)),
        "partial_only_count": int(sum(1 for case in cases if case.get("partial_only"))),
        "held_le_180_count": int(sum(1 for case in cases if int(case.get("held_sec") or 0) <= 180)),
        "integrity_issue_count": int(sum(1 for case in cases if case.get("integrity_flags"))),
        "peak_le_zero_count": int(sum(1 for case in expanded_cases if float(case.get("peak_profit") or 0.0) <= 0.0)),
        "peak_lt_point2_count": int(sum(1 for case in expanded_cases if float(case.get("peak_profit") or 0.0) < 0.2)),
        "same_symbol_repeats": repeats,
        "cases": cases,
    }


def build_followup_summary(
    *,
    local_pipeline_events_path: Path,
    remote_pipeline_events_path: Path | None = None,
) -> dict[str, Any]:
    summary = {
        "local_latency_canary": summarize_latency_canary(local_pipeline_events_path),
        "local_split_entry_soft_stop": summarize_split_entry_soft_stop(local_pipeline_events_path),
    }
    if remote_pipeline_events_path is not None:
        summary["remote_latency_canary"] = summarize_latency_canary(remote_pipeline_events_path)
        summary["remote_split_entry_soft_stop"] = summarize_split_entry_soft_stop(remote_pipeline_events_path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize noon follow-up metrics from pipeline event JSONL files.")
    parser.add_argument("--local-pipeline-events", required=True, help="Path to the local pipeline_events_YYYY-MM-DD.jsonl file.")
    parser.add_argument("--remote-pipeline-events", help="Optional path to the remote fetched pipeline_events_YYYY-MM-DD.jsonl file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    summary = build_followup_summary(
        local_pipeline_events_path=Path(args.local_pipeline_events),
        remote_pipeline_events_path=Path(args.remote_pipeline_events) if args.remote_pipeline_events else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
