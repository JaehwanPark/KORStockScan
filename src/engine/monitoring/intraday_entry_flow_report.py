from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENTRY_PIPELINE = "ENTRY_PIPELINE"

BUY_SIGNAL_STAGES = {
    "entry_armed",
    "budget_pass",
    "score_buy_candidate",
    "entry_price_resolved",
    "scalp_entry_action_decision_snapshot",
    "latency_pass",
}
SUBMIT_STAGE_MARKERS = ("submitted", "order_send", "broker_submit", "buy_submit")
STALE_EVAL_QUOTE_AGE_MS = 3000.0


def _parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _field(fields: dict[str, Any], key: str, default: str = "") -> str:
    value = fields.get(key, default)
    return "" if value is None else str(value)


def _reason(fields: dict[str, Any]) -> str:
    for key in ("reason", "skip_reason", "blocked_reason", "terminal_reason", "entry_submit_revalidation_warning"):
        value = _field(fields, key)
        if value:
            return value
    return ""


def _is_real_entry_candidate(row: dict[str, Any], promoted_codes: set[str]) -> bool:
    if row.get("pipeline") != ENTRY_PIPELINE:
        return False
    code = str(row.get("stock_code") or "").strip()
    if not code or code == "-":
        return False
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    if str(fields.get("simulated_order") or "").strip().lower() == "true":
        return False
    stage = str(row.get("stage") or "")
    if stage.startswith("scalp_sim_") or stage.startswith("swing_"):
        return False
    authority = str(fields.get("decision_authority") or "").lower()
    if "sim_" in authority or "swing_" in authority:
        return False
    return bool(
        fields.get("scanner_promotion_id")
        or fields.get("momentum_tag") == "SCANNER"
        or code in promoted_codes
    )


def _default_event_cache_path(target_date: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "runtime"
        / "sentinel_event_cache"
        / f"buy_funnel_sentinel_events_{target_date}.jsonl"
    )


def _default_diagnostic_path(target_date: str) -> Path:
    report_dir = PROJECT_ROOT / "data" / "report" / "intraday_entry_blocker_diagnostics"
    candidates = sorted(report_dir.glob(f"intraday_entry_blocker_diagnostics_{target_date}*.json"))
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else report_dir / f"intraday_entry_blocker_diagnostics_{target_date}.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _flow_summary(events: list[dict[str, Any]], *, limit: int = 8) -> str:
    if not events:
        return "-"
    parts: list[str] = []
    for item in events:
        label = str(item["stage"])
        if item.get("reason"):
            label += f":{item['reason']}"
        if item.get("delta") is not None:
            label += f"({item['delta']:+.2f}%)"
        parts.append(f"{item['ts'].strftime('%H:%M:%S')} {label}")
    if len(parts) <= limit:
        return " -> ".join(parts)
    return " -> ".join(parts[:4] + ["..."] + parts[-3:])


def _main_blocker(record: dict[str, Any], promoted: dict[str, dict[str, Any]]) -> tuple[str, str, int]:
    item = promoted.get(record["code"]) or {}
    dominant = item.get("dominant_blocker") if isinstance(item.get("dominant_blocker"), dict) else {}
    if dominant.get("stage"):
        return str(dominant.get("stage") or ""), str(dominant.get("reason") or ""), int(dominant.get("count") or 0)
    stage_counts: Counter[str] = record["stage_counts"]
    if stage_counts:
        stage, count = max(stage_counts.items(), key=lambda kv: kv[1])
        reason_counts: Counter[str] = record["reason_counts"]
        reason = reason_counts.most_common(1)[0][0] if reason_counts else ""
        return stage, reason, count
    return str(record.get("latest_stage") or ""), str(record.get("latest_reason") or ""), 0


def build_report(
    *,
    target_date: str,
    event_cache_path: Path | None = None,
    diagnostic_path: Path | None = None,
    since: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    event_cache_path = event_cache_path or _default_event_cache_path(target_date)
    diagnostic_path = diagnostic_path or _default_diagnostic_path(target_date)
    diagnostic = _read_json(diagnostic_path)
    raw_promoted = {
        str(item.get("stock_code")): item
        for item in diagnostic.get("promoted_symbols", [])
        if isinstance(item, dict) and item.get("stock_code")
    }
    since_ts = _parse_ts(since) if since else None
    promoted: dict[str, dict[str, Any]] = {}
    for code, item in raw_promoted.items():
        first_promoted_at = _parse_ts(item.get("first_promoted_at"))
        if since_ts is not None and first_promoted_at is not None and first_promoted_at < since_ts:
            continue
        promoted[code] = item
    rising_missed_codes = {
        str(item.get("stock_code"))
        for item in diagnostic.get("rising_missed_buy", [])
        if isinstance(item, dict) and item.get("stock_code")
    }
    promoted_codes = set(promoted)
    raw_promoted_codes = set(raw_promoted)

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "events": [],
            "stage_counts": Counter(),
            "reason_counts": Counter(),
            "first_ts": None,
            "last_ts": None,
            "name": "",
            "code": "",
            "latest_delta": None,
            "max_delta": None,
            "min_delta": None,
            "latest_stage": "",
            "latest_reason": "",
            "latest_ai_score": None,
            "latest_ai_action": "",
            "actual_submit_count": 0,
            "buy_signal_seen": False,
            "first_buy_signal_ts": None,
            "stale_eval_count": 0,
            "max_quote_age_ms": None,
            "stale_eval_stage_counts": Counter(),
        }
    )

    for row in _read_jsonl(event_cache_path):
        ts = _parse_ts(row.get("emitted_at"))
        if ts is None or (since_ts is not None and ts < since_ts):
            continue
        if not _is_real_entry_candidate(row, raw_promoted_codes):
            continue
        code = str(row.get("stock_code") or "").strip()
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        stage = str(row.get("stage") or "")
        reason = _reason(fields)
        record = grouped[code]
        record["code"] = code
        record["name"] = str(row.get("stock_name") or fields.get("stock_name") or record["name"])
        record["first_ts"] = min([value for value in (record["first_ts"], ts) if value], default=ts)
        record["last_ts"] = max([value for value in (record["last_ts"], ts) if value], default=ts)
        delta = _safe_float(fields.get("price_delta_since_first_seen_pct"))
        if delta is not None:
            record["latest_delta"] = delta
            record["max_delta"] = delta if record["max_delta"] is None else max(record["max_delta"], delta)
            record["min_delta"] = delta if record["min_delta"] is None else min(record["min_delta"], delta)
        ai_score = _safe_float(fields.get("ai_score") or fields.get("ai_score_raw") or fields.get("ai_score_projected"))
        if ai_score is not None:
            record["latest_ai_score"] = ai_score
        action = _field(fields, "action") or _field(fields, "ai_action")
        if action:
            record["latest_ai_action"] = action
        quote_age_ms = _safe_float(fields.get("quote_age_ms") or fields.get("quote_age_at_submit_ms"))
        if quote_age_ms is not None:
            record["max_quote_age_ms"] = (
                quote_age_ms
                if record["max_quote_age_ms"] is None
                else max(record["max_quote_age_ms"], quote_age_ms)
            )
        if quote_age_ms is not None and quote_age_ms > STALE_EVAL_QUOTE_AGE_MS:
            record["stale_eval_count"] += 1
            record["stale_eval_stage_counts"][stage] += 1
        record["stage_counts"][stage] += 1
        if reason:
            record["reason_counts"][reason] += 1
        record["latest_stage"] = stage
        record["latest_reason"] = reason
        if str(fields.get("actual_order_submitted") or "").strip().lower() == "true" or any(
            marker in stage for marker in SUBMIT_STAGE_MARKERS
        ):
            record["actual_submit_count"] += 1
        if stage in BUY_SIGNAL_STAGES:
            record["buy_signal_seen"] = True
            if record["first_buy_signal_ts"] is None:
                record["first_buy_signal_ts"] = ts
        event_key = (stage, reason)
        events = record["events"]
        if not events or events[-1]["key"] != event_key or stage in BUY_SIGNAL_STAGES:
            events.append({"ts": ts, "stage": stage, "reason": reason, "delta": delta, "ai_score": ai_score, "key": event_key})

    for code, item in promoted.items():
        record = grouped[code]
        record["code"] = code
        record["name"] = item.get("stock_name") or record["name"]
        record["first_ts"] = _parse_ts(item.get("first_promoted_at")) or record["first_ts"]
        record["last_ts"] = _parse_ts(item.get("last_event_at")) or record["last_ts"]
        latest_delta = _safe_float(item.get("latest_price_delta_since_first_seen_pct"))
        if latest_delta is not None:
            record["latest_delta"] = latest_delta
        max_delta = _safe_float(item.get("max_price_delta_since_first_seen_pct"))
        if max_delta is not None:
            record["max_delta"] = max_delta if record["max_delta"] is None else max(record["max_delta"], max_delta)
        if item.get("latest_ai_score") is not None:
            record["latest_ai_score"] = item.get("latest_ai_score")
        record["latest_ai_action"] = item.get("latest_ai_action") or record["latest_ai_action"]
        latest_blocker = item.get("latest_blocker") if isinstance(item.get("latest_blocker"), dict) else {}
        if latest_blocker:
            record["latest_stage"] = latest_blocker.get("stage") or record["latest_stage"]
            record["latest_reason"] = latest_blocker.get("reason") or record["latest_reason"]
        record["actual_submit_count"] = max(record["actual_submit_count"], int(item.get("real_submit_count") or 0))

    rows: list[dict[str, Any]] = []
    for code, record in grouped.items():
        if record["first_ts"] is None:
            continue
        stage, reason, count = _main_blocker(record, promoted)
        max_delta = record["max_delta"]
        if max_delta is None:
            rise = "unknown"
        elif max_delta > 0:
            rise = "rising"
        else:
            rise = "flat_or_falling"
        rows.append(
            {
                "stock_code": code,
                "stock_name": record["name"],
                "first_observed_at": record["first_ts"].strftime("%H:%M:%S"),
                "last_observed_at": record["last_ts"].strftime("%H:%M:%S") if record["last_ts"] else "",
                "rise_after_watch": rise,
                "max_delta_since_first_seen_pct": max_delta,
                "latest_delta_since_first_seen_pct": record["latest_delta"],
                "buy_signal_seen": bool(record["buy_signal_seen"]),
                "first_buy_signal_at": record["first_buy_signal_ts"].strftime("%H:%M:%S") if record["first_buy_signal_ts"] else "",
                "actual_submit_count": int(record["actual_submit_count"] or 0),
                "main_blocker_stage": stage,
                "main_blocker_reason": reason,
                "main_blocker_count": count,
                "latest_stage": record["latest_stage"],
                "latest_reason": record["latest_reason"],
                "latest_ai_score": record["latest_ai_score"],
                "latest_ai_action": record["latest_ai_action"],
                "stale_eval_count": int(record["stale_eval_count"] or 0),
                "max_quote_age_ms": record["max_quote_age_ms"],
                "dominant_stale_eval_stage": (
                    record["stale_eval_stage_counts"].most_common(1)[0][0]
                    if record["stale_eval_stage_counts"]
                    else ""
                ),
                "rising_missed_in_diagnostic": code in rising_missed_codes,
                "flow": _flow_summary(record["events"]),
            }
        )
    rows.sort(
        key=lambda item: (
            item["max_delta_since_first_seen_pct"] is None,
            -(item["max_delta_since_first_seen_pct"] if item["max_delta_since_first_seen_pct"] is not None else -999.0),
            item["first_observed_at"],
        )
    )
    blocker_rollup = [
        {"stage": stage or "-", "reason": reason or "-", "count": count}
        for (stage, reason), count in Counter((row["main_blocker_stage"], row["main_blocker_reason"]) for row in rows).most_common()
    ]
    rising_blocker_rollup = [
        {"stage": stage or "-", "reason": reason or "-", "count": count}
        for (stage, reason), count in Counter(
            (row["main_blocker_stage"], row["main_blocker_reason"]) for row in rows if row["rise_after_watch"] == "rising"
        ).most_common()
    ]
    summary = {
        "symbol_count": len(rows),
        "rising_symbol_count_by_max_delta": sum(1 for row in rows if row["rise_after_watch"] == "rising"),
        "rising_missed_buy_count_in_latest_diagnostic": len(rising_missed_codes),
        "rising_missed_symbol_count_in_report": sum(1 for row in rows if row["rising_missed_in_diagnostic"]),
        "real_submit_symbol_count_in_latest_diagnostic": diagnostic.get("summary", {}).get("real_submit_symbol_count"),
        "buy_signal_or_pre_submit_pass_seen_symbols": sum(1 for row in rows if row["buy_signal_seen"]),
        "stale_eval_symbol_count": sum(1 for row in rows if row["stale_eval_count"] > 0),
        "rising_stale_eval_symbol_count": sum(
            1 for row in rows if row["rise_after_watch"] == "rising" and row["stale_eval_count"] > 0
        ),
    }
    stale_eval_rollup = [
        {"stage": stage or "-", "count": count}
        for stage, count in Counter(
            row["dominant_stale_eval_stage"] for row in rows if row["dominant_stale_eval_stage"]
        ).most_common()
    ]
    return {
        "report_type": "intraday_entry_flow_report",
        "schema_version": 1,
        "target_date": target_date,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "event_window": {"since": since},
        "source_events": str(event_cache_path),
        "source_diagnostic": str(diagnostic_path),
        "decision_authority": "source_quality_and_blocker_observation_only",
        "runtime_effect": False,
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "provider_route_change",
            "bot_restart",
            "broker_guard_bypass",
        ],
        "summary": summary,
        "blocker_rollup": blocker_rollup,
        "rising_symbol_blocker_rollup": rising_blocker_rollup,
        "stale_eval_rollup": stale_eval_rollup,
        "rows": rows,
    }


def _format_pct(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.2f}%"


def _window_label(report: dict[str, Any]) -> str:
    since_ts = _parse_ts(report.get("event_window", {}).get("since"))
    if since_ts is None:
        return "전체"
    return since_ts.strftime("%H:%M")


def write_outputs(report: dict[str, Any], *, output_md: Path, output_csv: Path, max_rows: int = 100) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = list(report.get("rows", []))
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
    with output_md.open("w", encoding="utf-8") as handle:
        handle.write(f"# {report['target_date']} {_window_label(report)} 이후 감시대상 BUY 전 흐름\n\n")
        handle.write(f"- generated_at: {report['generated_at']}\n")
        handle.write(f"- source_events: {report['source_events']}\n")
        handle.write(f"- source_diagnostic: {report['source_diagnostic']}\n")
        handle.write(f"- event_window_since: {report.get('event_window', {}).get('since')}\n")
        for key, value in report["summary"].items():
            handle.write(f"- {key}: {value}\n")
        handle.write("\n## blocker rollup\n\n")
        for item in report["blocker_rollup"][:12]:
            handle.write(f"- {item['count']}: `{item['stage']}` / `{item['reason']}`\n")
        handle.write("\n## rising-symbol blocker rollup\n\n")
        for item in report["rising_symbol_blocker_rollup"][:12]:
            handle.write(f"- {item['count']}: `{item['stage']}` / `{item['reason']}`\n")
        handle.write("\n## stale-eval rollup\n\n")
        for item in report["stale_eval_rollup"][:12]:
            handle.write(f"- {item['count']}: `{item['stage']}`\n")
        handle.write("\n## top rows by max delta\n\n")
        handle.write("|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|stale평가|max quote age|BUY전 통과신호|AI|실제submit|흐름|\n")
        handle.write("|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---|\n")
        for row in rows[:max_rows]:
            ai = ""
            if row["latest_ai_score"] is not None:
                ai = f"{float(row['latest_ai_score']):.0f}/{row['latest_ai_action']}"
            blocker = f"`{row['main_blocker_stage'] or '-'}`/{row['main_blocker_reason'] or '-'}"
            handle.write(
                "|"
                f"{row['stock_name']}({row['stock_code']})|"
                f"{row['first_observed_at']}|"
                f"{row['last_observed_at']}|"
                f"{row['rise_after_watch']}|"
                f"{_format_pct(row['max_delta_since_first_seen_pct'])}|"
                f"{_format_pct(row['latest_delta_since_first_seen_pct'])}|"
                f"{blocker}|"
                f"{row['stale_eval_count']}|"
                f"{'' if row['max_quote_age_ms'] is None else round(float(row['max_quote_age_ms']), 0)}|"
                f"{row['first_buy_signal_at'] or '-'}|"
                f"{ai}|"
                f"{row['actual_submit_count']}|"
                f"{row['flow']}|\n"
            )


def _default_output_paths(target_date: str, since: str | None, generated_at: str) -> tuple[Path, Path]:
    suffix = "all"
    since_ts = _parse_ts(since)
    if since_ts is not None:
        suffix = since_ts.strftime("%H%M")
    generated_ts = _parse_ts(generated_at) or datetime.now()
    base = PROJECT_ROOT / "data" / "report" / "intraday_entry_flow" / f"intraday_entry_flow_{target_date}_{suffix}_to_{generated_ts.strftime('%H%M')}"
    return base.with_suffix(".md"), base.with_suffix(".csv")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build intraday watched-symbol entry flow report.")
    parser.add_argument("--target-date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--event-cache-path", type=Path)
    parser.add_argument("--diagnostic-path", type=Path)
    parser.add_argument("--since")
    parser.add_argument("--generated-at")
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--max-rows", type=int, default=100)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)

    generated_at = args.generated_at or datetime.now().isoformat(timespec="seconds")
    report = build_report(
        target_date=args.target_date,
        event_cache_path=args.event_cache_path,
        diagnostic_path=args.diagnostic_path,
        since=args.since,
        generated_at=generated_at,
    )
    default_md, default_csv = _default_output_paths(args.target_date, args.since, generated_at)
    output_md = args.output_md or default_md
    output_csv = args.output_csv or default_csv
    write_outputs(report, output_md=output_md, output_csv=output_csv, max_rows=args.max_rows)
    if args.print_summary:
        print(json.dumps({"output_md": str(output_md), "output_csv": str(output_csv), **report["summary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
