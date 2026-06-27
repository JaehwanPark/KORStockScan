"""Backtest quote consistency normalization against historical runtime rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from src.trading.market.quote_consistency import (
    RUNTIME_FAMILY,
    QuoteConsistencyConfig,
    build_quote_consistency_snapshot,
    quote_input_from_rest_orderbook,
    quote_input_from_ws,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


REPORT_DIR = DATA_DIR / "report" / "quote_consistency_backtest"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENTS_DIR = DATA_DIR / "threshold_cycle"

BUY_SIDE_MARKERS = (
    "entry",
    "buy",
    "submit",
    "latency",
    "reprice",
    "scanner_candidate_promoted",
)
SCALE_IN_MARKERS = ("scale_in", "avg_down", "pyramid", "add")
SELL_SIDE_MARKERS = ("sell", "exit", "holding", "stop", "take_profit")
SAFETY_EXIT_MARKERS = (
    "protect",
    "emergency",
    "hard_stop",
    "soft_stop",
    "stop_loss",
    "panic",
    "loss",
)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if text in {"", "-", "None", "none", "null"}:
            return default
        return int(float(text))
    except Exception:
        return default


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if text in {"", "-", "None", "none", "null"}:
            return default
        return float(text)
    except Exception:
        return default


def _to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    dates: list[str] = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "pipeline_events": existing_or_gzip_path(
            PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
        ),
        "threshold_events": existing_or_gzip_path(
            THRESHOLD_EVENTS_DIR / f"threshold_events_{target_date}.jsonl"
        ),
    }


def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    yield from iter_jsonl(path)


def _flatten_event(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(row)
    merged.update(fields)
    return merged


def _first_int(row: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = _to_int(row.get(key))
        if value > 0:
            return value
    return 0


def _first_float(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _has_any(row: dict[str, Any], keys: Iterable[str]) -> bool:
    return any(str(row.get(key) or "").strip() not in {"", "0", "None", "none", "null", "-"} for key in keys)


def _stage_bucket(row: dict[str, Any]) -> str:
    stage = str(row.get("stage") or row.get("event_type") or "unknown").lower()
    blocked_stage = str(row.get("blocked_stage") or "").lower()
    text = f"{stage} {blocked_stage}"
    if any(marker in text for marker in SCALE_IN_MARKERS):
        return "scale_in"
    if any(marker in text for marker in SELL_SIDE_MARKERS):
        return "holding_exit"
    if any(marker in text for marker in BUY_SIDE_MARKERS):
        return "entry_submit"
    if "scanner" in text:
        return "scanner"
    return "other"


def _is_safety_exit(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(row.get(key) or "").lower()
        for key in (
            "stage",
            "event_type",
            "sell_reason",
            "sell_reason_type",
            "exit_rule",
            "holding_action",
            "quote_consistency_runtime_action",
        )
    )
    return any(marker in text for marker in SAFETY_EXIT_MARKERS)


def _row_side(row: dict[str, Any]) -> str:
    bucket = _stage_bucket(row)
    if bucket in {"entry_submit", "scanner", "scale_in"}:
        return "buy"
    if bucket == "holding_exit":
        return "sell"
    return "mark"


def _extract_ws_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "curr": _first_int(
            row,
            "pre_submit_ws_snapshot_refresh_latest_price",
            "mark_price_at_submit",
            "latest_price",
            "current_price",
            "current_price_observed",
            "curr_price",
            "curr",
            "signal_price",
            "promotion_price",
        ),
        "best_bid": _first_int(
            row,
            "pre_submit_ws_snapshot_refresh_best_bid",
            "best_bid_at_submit",
            "best_bid",
            "sim_best_bid_at_submit",
        ),
        "best_ask": _first_int(
            row,
            "pre_submit_ws_snapshot_refresh_best_ask",
            "best_ask_at_submit",
            "best_ask",
        ),
        "pre_submit_ws_snapshot_refresh_age_ms": _first_float(
            row,
            "pre_submit_ws_snapshot_refresh_age_ms",
            "orderbook_micro_observer_last_trade_age_ms",
            "quote_age_at_submit_ms",
            "quote_age_ms",
        ),
    }


def _extract_rest_row(row: dict[str, Any]) -> dict[str, Any]:
    best_bid = _first_int(
        row,
        "pre_submit_rest_orderbook_refresh_best_bid",
        "pre_submit_quote_refresh_best_bid",
    )
    best_ask = _first_int(
        row,
        "pre_submit_rest_orderbook_refresh_best_ask",
        "pre_submit_quote_refresh_best_ask",
    )
    return {
        "best_bid": best_bid,
        "best_ask": best_ask,
        "rest_mid_price": int(round((best_bid + best_ask) / 2.0)) if best_bid > 0 and best_ask > 0 else 0,
        "age_ms": _first_float(
            row,
            "pre_submit_rest_orderbook_refresh_age_ms",
            "pre_submit_quote_refresh_quote_age_ms",
        ),
        "bid_req_base_tm": row.get("pre_submit_rest_orderbook_refresh_bid_req_base_tm"),
    }


def _has_quote_inputs(row: dict[str, Any]) -> bool:
    return _has_any(
        row,
        (
            "pre_submit_ws_snapshot_refresh_latest_price",
            "mark_price_at_submit",
            "latest_price",
            "current_price",
            "current_price_observed",
            "curr_price",
            "curr",
            "signal_price",
            "promotion_price",
            "best_bid_at_submit",
            "best_ask_at_submit",
            "pre_submit_quote_refresh_best_bid",
            "pre_submit_quote_refresh_best_ask",
            "pre_submit_rest_orderbook_refresh_best_bid",
            "pre_submit_rest_orderbook_refresh_best_ask",
        ),
    )


def _percentiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"avg": None, "p50": None, "p95": None, "p99": None, "max": None}
    ordered = sorted(values)

    def pick(percent: float) -> float:
        idx = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percent))))
        return round(float(ordered[idx]), 4)

    return {
        "avg": round(float(mean(ordered)), 4),
        "p50": pick(0.50),
        "p95": pick(0.95),
        "p99": pick(0.99),
        "max": round(float(ordered[-1]), 4),
    }


def build_quote_consistency_backtest(
    *,
    start_date: str,
    end_date: str,
    config: QuoteConsistencyConfig | None = None,
) -> dict[str, Any]:
    config = config or QuoteConsistencyConfig()
    state_counts: Counter = Counter()
    source_counts: Counter = Counter()
    action_counts: Counter = Counter()
    stage_counts: dict[str, Counter] = defaultdict(Counter)
    date_counts: dict[str, Counter] = defaultdict(Counter)
    gap_values: list[float] = []
    price_delta_bps: list[float] = []
    defective_rows: list[dict[str, Any]] = []
    diagnostic_profit_rates_by_state: dict[str, list[float]] = defaultdict(list)
    summary = Counter()
    sources: dict[str, dict[str, str | None]] = {}

    for target_date in _date_range(start_date, end_date):
        paths = _source_paths(target_date)
        sources[target_date] = {
            name: str(path) if path.exists() else None for name, path in paths.items()
        }
        for source_name, path in paths.items():
            for raw in _iter_rows(path):
                row = _flatten_event(raw)
                if not _has_quote_inputs(row):
                    continue
                summary["observed_quote_rows"] += 1
                ws_input = quote_input_from_ws(_extract_ws_row(row), now_ts=0)
                rest_raw = _extract_rest_row(row)
                rest_input = quote_input_from_rest_orderbook(rest_raw, now_ts=0) if _has_any(rest_raw, ("best_bid", "best_ask", "rest_mid_price")) else None
                if ws_input.has_price:
                    summary["ws_input_rows"] += 1
                if rest_input and rest_input.has_price:
                    summary["rest_input_rows"] += 1
                snapshot = build_quote_consistency_snapshot(
                    ws=ws_input if ws_input.has_price else None,
                    rest=rest_input if rest_input and rest_input.has_price else None,
                    side=_row_side(row),
                    safety_exit=_is_safety_exit(row),
                    runtime_enabled=True,
                    config=config,
                )
                state_counts[snapshot.quality_state] += 1
                source_counts[snapshot.source] += 1
                action_counts[snapshot.runtime_action] += 1
                stage_bucket = _stage_bucket(row)
                stage_counts[stage_bucket][snapshot.quality_state] += 1
                date_counts[target_date][snapshot.quality_state] += 1
                if snapshot.ws_rest_gap_bps is not None:
                    gap_values.append(float(snapshot.ws_rest_gap_bps))
                original = _first_int(
                    row,
                    "mark_price_at_submit",
                    "latest_price",
                    "current_price",
                    "current_price_observed",
                    "curr_price",
                    "signal_price",
                )
                if original > 0 and snapshot.canonical_mark_price > 0:
                    price_delta_bps.append(abs(snapshot.canonical_mark_price - original) / original * 10000.0)
                if snapshot.entry_blocked and stage_bucket in {"entry_submit", "scanner", "scale_in"}:
                    summary["would_block_entry_reprice_scale_in"] += 1
                if snapshot.safety_exit_allowed:
                    summary["safety_exit_unblocked"] += 1
                if snapshot.quality_state in {"diverged", "missing", "stale"}:
                    summary["ev_input_excluded_rows"] += 1
                    if len(defective_rows) < 200:
                        defective_rows.append(
                            {
                                "date": target_date,
                                "source": source_name,
                                "stage": row.get("stage"),
                                "stage_bucket": stage_bucket,
                                "stock_code": row.get("stock_code"),
                                "quality_state": snapshot.quality_state,
                                "runtime_action": snapshot.runtime_action,
                                "reason": snapshot.reason,
                                "canonical_mark_price": snapshot.canonical_mark_price,
                                "executable_buy_price": snapshot.executable_buy_price,
                                "executable_sell_price": snapshot.executable_sell_price,
                                "ws_rest_gap_bps": snapshot.ws_rest_gap_bps,
                                "ws_price": snapshot.ws_price,
                                "rest_mark_price": snapshot.rest_mark_price,
                                "ws_age_ms": snapshot.ws_age_ms,
                                "rest_age_ms": snapshot.rest_age_ms,
                            }
                        )
                profit_rate = _to_float(row.get("profit_rate"))
                if profit_rate is not None:
                    diagnostic_profit_rates_by_state[snapshot.quality_state].append(float(profit_rate))

    diagnostic_profit = {
        state: {
            "sample_count": len(values),
            "diagnostic_avg_profit_rate_pct": round(float(mean(values)), 4) if values else None,
        }
        for state, values in sorted(diagnostic_profit_rates_by_state.items())
    }
    findings: list[dict[str, Any]] = []
    if summary["observed_quote_rows"] <= 0:
        findings.append({"severity": "fail", "code": "quote_backtest_no_quote_rows"})
    if summary["rest_input_rows"] <= 0:
        findings.append({"severity": "warning", "code": "quote_backtest_no_rest_rows"})
    return {
        "schema_version": 1,
        "report_type": "quote_consistency_backtest",
        "runtime_family": RUNTIME_FAMILY,
        "start_date": start_date,
        "end_date": end_date,
        "sources": sources,
        "config": {
            "max_ws_age_ms": config.max_ws_age_ms,
            "max_rest_age_ms": config.max_rest_age_ms,
            "ok_gap_bps": config.ok_gap_bps,
            "warn_gap_bps": config.warn_gap_bps,
            "emergency_rest_timeout_ms": config.emergency_rest_timeout_ms,
            "block_entry_on_divergence": config.block_entry_on_divergence,
        },
        "summary": {
            **dict(summary),
            "state_counts": dict(state_counts),
            "source_counts": dict(source_counts),
            "runtime_action_counts": dict(action_counts),
            "gap_bps": _percentiles(gap_values),
            "canonical_vs_original_abs_delta_bps": _percentiles(price_delta_bps),
        },
        "stage_state_counts": {stage: dict(counts) for stage, counts in sorted(stage_counts.items())},
        "date_state_counts": {day: dict(counts) for day, counts in sorted(date_counts.items())},
        "diagnostic_profit_rate_by_state": diagnostic_profit,
        "defective_row_candidates": defective_rows,
        "verifier_findings": findings,
        "forbidden_uses": [
            "real_order_replay",
            "broker_execution_quality_approval",
            "standalone_live_auto_promotion",
            "threshold_mutation_without_postclose_preopen_chain",
        ],
    }


def write_quote_consistency_backtest(report: dict[str, Any], *, output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    start_date = str(report.get("start_date"))
    end_date = str(report.get("end_date"))
    stem = f"quote_consistency_backtest_{start_date}_to_{end_date}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        f"# Quote Consistency Backtest {start_date} to {end_date}",
        "",
        f"- runtime_family: `{report.get('runtime_family')}`",
        f"- observed_quote_rows: `{summary.get('observed_quote_rows', 0)}`",
        f"- ws_input_rows: `{summary.get('ws_input_rows', 0)}`",
        f"- rest_input_rows: `{summary.get('rest_input_rows', 0)}`",
        f"- would_block_entry_reprice_scale_in: `{summary.get('would_block_entry_reprice_scale_in', 0)}`",
        f"- safety_exit_unblocked: `{summary.get('safety_exit_unblocked', 0)}`",
        f"- ev_input_excluded_rows: `{summary.get('ev_input_excluded_rows', 0)}`",
        "",
        "## State Counts",
    ]
    for state, count in sorted((summary.get("state_counts") or {}).items()):
        lines.append(f"- `{state}`: {count}")
    lines.append("")
    lines.append("## Stage State Counts")
    for stage, counts in (report.get("stage_state_counts") or {}).items():
        count_text = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        lines.append(f"- `{stage}`: {count_text}")
    lines.append("")
    lines.append("## Verifier Findings")
    findings = report.get("verifier_findings") or []
    if findings:
        lines.extend(f"- `{item.get('severity')}` `{item.get('code')}`" for item in findings)
    else:
        lines.append("- `ok` `none`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_quote_consistency_backtest(start_date=args.start_date, end_date=args.end_date)
    if args.write:
        json_path, md_path = write_quote_consistency_backtest(report)
        print(json.dumps({"json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
