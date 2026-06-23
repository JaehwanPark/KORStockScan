from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENTRY_PIPELINE = "ENTRY_PIPELINE"
PROMOTED_STAGE = "scalping_scanner_candidate_promoted"
REAL_SUBMIT_TRUE = "true"

BLOCKER_STAGES = {
    "ai_confirmed_terminal_no_budget",
    "blocked_ai_score",
    "blocked_gap_from_scan",
    "blocked_liquidity",
    "blocked_overbought",
    "blocked_strength_momentum",
    "blocked_vpw",
    "first_ai_wait",
    "score65_74_recovery_probe_blocked",
    "scalping_scanner_watch_eviction",
    "scalping_scanner_watching_runtime_skip",
}

QUEUE_STAGES = {
    "scalping_scanner_fast_precheck",
    "scalping_scanner_heavy_eval_lag",
    "scalping_scanner_runtime_queue_lag",
}

RELIEF_BLOCKER_REASONS = {
    "scanner_full_eval_loop_budget_deferred",
    "entry_cooldown_active",
    "scalping_new_buy_cutoff",
    "outside_scalping_buy_window",
    "ws_snapshot_missing_or_zero",
    "ws_snapshot_missing_or_zero_recovered",
}

LOW_AI_SCORE_CUTOFF = 65.0
NEGATIVE_BUY_PRESSURE_CUTOFF = 0.0
ENTRY_FRESH_MAX_AGE_MS = 3000.0
ZERO_HISTORY_WORKORDER_MIN_EVENTS = 2

STRENGTH_HISTORY_COUNT_KEYS = (
    "ws_strength_history_count",
    "strength_momentum_history_count",
    "pre_ai_ws_snapshot_refresh_history_count",
    "refresh_history_count",
)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if text.lower() in {"", "none", "nan", "nat", "inf", "+inf", "-inf"}:
            return default
        if text.startswith("not_applicable"):
            return default
        return float(text.replace("%", "").replace("+", ""))
    except Exception:
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, mode="rt", encoding="utf-8") as handle:
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


def _exclude_from_real_entry_analysis(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "")
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    if stage.startswith("scalp_sim_") or stage.startswith("swing_"):
        return True
    if str(fields.get("simulated_order") or "").strip().lower() == "true":
        return True
    authority = str(fields.get("decision_authority") or "").lower()
    return "sim_" in authority or "swing_" in authority


def _entry_events(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("pipeline") != ENTRY_PIPELINE:
            continue
        if _exclude_from_real_entry_analysis(row):
            continue
        code = str(row.get("stock_code") or "").strip()
        if not code or code == "-":
            continue
        grouped[code].append(row)
    return dict(grouped)


def _field(row: dict[str, Any], key: str, default: Any = "") -> Any:
    fields = row.get("fields")
    if not isinstance(fields, dict):
        return default
    return fields.get(key, default)


def _blocker_reason(row: dict[str, Any]) -> str:
    for key in (
        "reason",
        "block_reason",
        "skip_reason",
        "scanner_watch_skip_reason",
        "scanner_block_reason",
        "budget_block_reason",
        "terminal_reason",
        "scalp_sim_candidate_window_blocked_reason",
    ):
        value = _field(row, key)
        if value not in (None, ""):
            return str(value)
    return ""


def _first_float_field(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _safe_float(_field(row, key))
        if value is not None:
            return value
    return None


def _event_max_age_ms(row: dict[str, Any]) -> float | None:
    age_values: list[float] = []
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    for key, value in fields.items():
        key_text = str(key).lower()
        if not (
            "age_ms" in key_text
            or "delay_ms" in key_text
            or "lag_ms" in key_text
            or key_text in {"quote_age_ms", "tick_latest_age_ms"}
        ):
            continue
        parsed = _safe_float(value)
        if parsed is not None:
            age_values.append(parsed)
    return max(age_values) if age_values else None


def _event_has_stale_or_delayed_context(row: dict[str, Any]) -> bool:
    reason = _blocker_reason(row).lower()
    stage = str(row.get("stage") or "").lower()
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    context_text = " ".join(
        str(value).lower()
        for key, value in fields.items()
        if any(token in str(key).lower() for token in ("stale", "fresh", "snapshot", "subscription"))
    )
    if any(
        token in f"{stage} {reason} {context_text}"
        for token in (
            "stale",
            "ws_snapshot_missing_or_zero",
            "subscription_alive_but_entry_stale",
            "insufficient_history",
        )
    ):
        return True
    max_age_ms = _event_max_age_ms(row)
    return max_age_ms is not None and max_age_ms > ENTRY_FRESH_MAX_AGE_MS


def _event_is_fresh_context(row: dict[str, Any]) -> bool:
    max_age_ms = _event_max_age_ms(row)
    return max_age_ms is not None and max_age_ms <= ENTRY_FRESH_MAX_AGE_MS and not _event_has_stale_or_delayed_context(row)


def _low_ai_or_negative_pressure(row: dict[str, Any]) -> bool:
    ai_score = _first_float_field(row, "ai_score", "buy_ai_score", "entry_ai_score")
    buy_pressure = _first_float_field(
        row,
        "buy_pressure",
        "buy_pressure_10t",
        "orderbook_buy_pressure",
        "pressure_buy",
    )
    return (
        (ai_score is not None and ai_score < LOW_AI_SCORE_CUTOFF)
        or (buy_pressure is not None and buy_pressure < NEGATIVE_BUY_PRESSURE_CUTOFF)
    )


def _low_ai_pressure_quality_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "fresh_eval": 0,
        "stale_or_delayed_eval": 0,
        "unknown_eval_quality": 0,
    }
    for row in rows:
        if not _low_ai_or_negative_pressure(row):
            continue
        if _event_has_stale_or_delayed_context(row):
            counts["stale_or_delayed_eval"] += 1
        elif _event_is_fresh_context(row):
            counts["fresh_eval"] += 1
        else:
            counts["unknown_eval_quality"] += 1
    return counts


def _strength_history_count(row: dict[str, Any]) -> int | None:
    for key in STRENGTH_HISTORY_COUNT_KEYS:
        value = _safe_float(_field(row, key))
        if value is not None:
            return int(value)
    return None


def _is_zero_strength_history_source_quality_event(row: dict[str, Any]) -> bool:
    history_count = _strength_history_count(row)
    if history_count is None or history_count > 0:
        return False
    stage = str(row.get("stage") or "").lower()
    reason = _blocker_reason(row).lower()
    context = f"{stage} {reason}"
    return any(
        token in context
        for token in (
            "insufficient_history",
            "stability_pending",
            "strength_momentum",
            "fast_precheck",
            "stale_ws_recovered",
        )
    )


def _zero_strength_history_source_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    zero_rows = [row for row in rows if _is_zero_strength_history_source_quality_event(row)]
    reason_counts = Counter(_blocker_reason(row) or str(row.get("stage") or "") for row in zero_rows)
    latest = zero_rows[-1] if zero_rows else {}
    return {
        "event_count": len(zero_rows),
        "repeated": len(zero_rows) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS,
        "latest_at": _event_time(latest) if latest else "",
        "latest_stage": (latest.get("stage") or "") if latest else "",
        "latest_reason": _blocker_reason(latest) if latest else "",
        "top_reasons": [
            {"reason": reason, "count": count}
            for reason, count in reason_counts.most_common(5)
        ],
        "source_quality_route": (
            "source_quality_workorder_required"
            if len(zero_rows) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS
            else "observe_until_repeated"
        ),
    }


def _dominant_blocker(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_rows = [row for row in rows if row.get("stage") in BLOCKER_STAGES]
    if not blocker_rows:
        return {"stage": "", "reason": "", "count": 0}
    counts = Counter((row.get("stage") or "", _blocker_reason(row)) for row in blocker_rows)
    (stage, reason), count = counts.most_common(1)[0]
    return {"stage": stage, "reason": reason, "count": count}


def _latest_blocker(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in reversed(rows):
        if row.get("stage") in BLOCKER_STAGES:
            return {
                "emitted_at": _event_time(row),
                "stage": row.get("stage") or "",
                "reason": _blocker_reason(row),
                "ai_score": _safe_float(_field(row, "ai_score")),
                "price_delta_since_first_seen_pct": _safe_float(
                    _field(row, "price_delta_since_first_seen_pct")
                ),
            }
    return {"emitted_at": "", "stage": "", "reason": "", "ai_score": None, "price_delta_since_first_seen_pct": None}


def _latest_delta(rows: list[dict[str, Any]]) -> float | None:
    for row in reversed(rows):
        value = _safe_float(_field(row, "price_delta_since_first_seen_pct"))
        if value is not None:
            return value
    return None


def _max_delta(rows: list[dict[str, Any]]) -> float | None:
    values = [
        value
        for row in rows
        if (value := _safe_float(_field(row, "price_delta_since_first_seen_pct"))) is not None
    ]
    return max(values) if values else None


def _event_time(row: dict[str, Any]) -> str:
    return str(row.get("emitted_at") or "")


def _summarize_code(
    code: str,
    rows: list[dict[str, Any]],
    *,
    promotion_source_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    stage_counts = Counter(str(row.get("stage") or "") for row in rows)
    name = next((str(row.get("stock_name") or "") for row in rows if row.get("stock_name")), "")
    promotion_rows = promotion_source_rows if promotion_source_rows is not None else rows
    promoted_rows = [row for row in promotion_rows if row.get("stage") == PROMOTED_STAGE]
    ai_rows = [row for row in rows if row.get("stage") == "ai_confirmed"]
    real_submit_rows = [
        row for row in rows if str(_field(row, "actual_order_submitted")).lower() == REAL_SUBMIT_TRUE
    ]
    blocker_rows = [row for row in rows if row.get("stage") in BLOCKER_STAGES]
    queue_counts = {stage: stage_counts.get(stage, 0) for stage in QUEUE_STAGES if stage_counts.get(stage, 0)}
    latest_ai = ai_rows[-1] if ai_rows else {}
    return {
        "stock_code": code,
        "stock_name": name,
        "promoted_count": len(promoted_rows),
        "first_promoted_at": _event_time(promoted_rows[0]) if promoted_rows else "",
        "promoted_in_event_window": any(row.get("stage") == PROMOTED_STAGE for row in rows),
        "last_event_at": _event_time(rows[-1]) if rows else "",
        "max_price_delta_since_first_seen_pct": _max_delta(rows),
        "latest_price_delta_since_first_seen_pct": _latest_delta(rows),
        "ai_confirmed_count": len(ai_rows),
        "latest_ai_action": _field(latest_ai, "action") if latest_ai else "",
        "latest_ai_score": _safe_float(_field(latest_ai, "ai_score")) if latest_ai else None,
        "latest_entry_score_threshold": _safe_float(_field(latest_ai, "entry_score_threshold"))
        if latest_ai
        else None,
        "real_submit_count": len(real_submit_rows),
        "blocker_count": len(blocker_rows),
        "dominant_blocker": _dominant_blocker(rows),
        "latest_blocker": _latest_blocker(rows),
        "queue_observation_counts": queue_counts,
        "low_ai_or_negative_pressure_eval_quality": _low_ai_pressure_quality_counts(rows),
        "zero_strength_history_source_quality": _zero_strength_history_source_quality(rows),
        "recent_blockers": [
            {
                "emitted_at": _event_time(row),
                "stage": row.get("stage") or "",
                "reason": _blocker_reason(row),
                "ai_score": _safe_float(_field(row, "ai_score")),
                "price_delta_since_first_seen_pct": _safe_float(
                    _field(row, "price_delta_since_first_seen_pct")
                ),
                "rising_entry_relief_eligible": _field(row, "rising_entry_relief_eligible", ""),
                "rising_entry_relief_reason": _field(row, "rising_entry_relief_reason", ""),
                "scanner_positive_delta_pct": _safe_float(_field(row, "scanner_positive_delta_pct")),
                "scanner_full_eval_budget_source": _field(row, "scanner_full_eval_budget_source", ""),
            }
            for row in blocker_rows[-8:]
        ],
    }


def _rollup_blockers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter()
    for item in items:
        for blocker in item["recent_blockers"]:
            stage = blocker.get("stage") or ""
            reason = blocker.get("reason") or ""
            if stage and (reason in RELIEF_BLOCKER_REASONS or stage == "scalping_scanner_watch_eviction"):
                counter[(stage, reason)] += 1
    return [
        {"stage": stage, "reason": reason, "count": count}
        for (stage, reason), count in counter.most_common()
    ]


def _rollup_low_ai_pressure_quality(items: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter()
    for item in items:
        counter.update(item.get("low_ai_or_negative_pressure_eval_quality") or {})
    return {
        "fresh_eval": int(counter.get("fresh_eval", 0)),
        "stale_or_delayed_eval": int(counter.get("stale_or_delayed_eval", 0)),
        "unknown_eval_quality": int(counter.get("unknown_eval_quality", 0)),
    }


def _zero_strength_history_workorders(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    workorders: list[dict[str, Any]] = []
    for item in items:
        quality = item.get("zero_strength_history_source_quality") or {}
        event_count = int(quality.get("event_count") or 0)
        if event_count < ZERO_HISTORY_WORKORDER_MIN_EVENTS:
            continue
        workorders.append(
            {
                "workorder_type": "scanner_strength_momentum_history_missing",
                "stock_code": item.get("stock_code") or "",
                "stock_name": item.get("stock_name") or "",
                "event_count": event_count,
                "latest_at": quality.get("latest_at") or "",
                "latest_stage": quality.get("latest_stage") or "",
                "latest_reason": quality.get("latest_reason") or "",
                "top_reasons": quality.get("top_reasons") or [],
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "strength_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
                "next_action": (
                    "check_ws_strength_momentum_history_producer_and_subscription_tick_flow_before_strategy_tuning"
                ),
            }
        )
    return sorted(workorders, key=lambda item: item["event_count"], reverse=True)


def build_report(
    *,
    target_date: str,
    pipeline_path: Path,
    generated_at: str | None = None,
    since: str | None = None,
    rising_threshold_pct: float = 0.5,
    falling_threshold_pct: float = -0.1,
) -> dict[str, Any]:
    all_rows = _read_jsonl(pipeline_path)
    full_grouped = _entry_events(all_rows)
    rows = all_rows
    if since:
        rows = [row for row in rows if _event_time(row) >= since]
    grouped = _entry_events(rows)
    real_entry_event_count = sum(len(events) for events in grouped.values())
    summaries = [
        _summarize_code(code, events, promotion_source_rows=full_grouped.get(code, events))
        for code, events in grouped.items()
        if any(row.get("stage") == PROMOTED_STAGE for row in full_grouped.get(code, events))
    ]
    rising_missed = [
        item
        for item in summaries
        if (item["max_price_delta_since_first_seen_pct"] or 0.0) >= rising_threshold_pct
        and item["real_submit_count"] == 0
    ]
    falling_submitted = [
        item
        for item in summaries
        if (item["latest_price_delta_since_first_seen_pct"] or 0.0) <= falling_threshold_pct
        and item["real_submit_count"] > 0
    ]
    non_rising_promoted = [
        item
        for item in summaries
        if (item["max_price_delta_since_first_seen_pct"] or 0.0) < rising_threshold_pct
    ]
    falling_promoted = [
        item
        for item in summaries
        if (item["latest_price_delta_since_first_seen_pct"] or 0.0) <= falling_threshold_pct
    ]
    blocker_counter: Counter[tuple[str, str]] = Counter()
    for item in summaries:
        for blocker in item["recent_blockers"]:
            if blocker["stage"]:
                blocker_counter[(blocker["stage"], blocker["reason"])] += 1
    return {
        "schema_version": 1,
        "report_type": "intraday_entry_blocker_diagnostics",
        "target_date": target_date,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "source_pipeline_events": str(pipeline_path),
        "event_window": {
            "since": since or "",
        },
        "thresholds": {
            "rising_missed_pct": rising_threshold_pct,
            "falling_submitted_pct": falling_threshold_pct,
        },
        "metric_contracts": {
            "rising_missed_low_ai_or_negative_pressure_eval_quality": {
                "metric_role": "source_quality_gate",
                "decision_authority": "diagnostic_only",
                "window_policy": "intraday_event_window",
                "sample_floor": "none_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "entry_eval_freshness_context",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
            },
            "repeated_zero_strength_history_source_quality_workorders": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_quality_only",
                "window_policy": "intraday_event_window",
                "sample_floor": f"{ZERO_HISTORY_WORKORDER_MIN_EVENTS}_events_per_symbol",
                "primary_decision_metric": False,
                "source_quality_gate": "strength_momentum_history_available_before_entry_quality_judgment",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "strength_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
            }
        },
        "summary": {
            "entry_event_count": real_entry_event_count,
            "promoted_symbol_count": len(summaries),
            "promoted_before_window_symbol_count": sum(
                1 for item in summaries if not item.get("promoted_in_event_window")
            ),
            "rising_missed_buy_count": len(rising_missed),
            "falling_real_submitted_count": len(falling_submitted),
            "real_submit_symbol_count": sum(1 for item in summaries if item["real_submit_count"] > 0),
            "excluded_analysis_scope": "sim_and_swing_events",
            "rising_missed_low_ai_or_negative_pressure_eval_quality": _rollup_low_ai_pressure_quality(
                rising_missed
            ),
            "repeated_zero_strength_history_workorder_count": len(
                _zero_strength_history_workorders(summaries)
            ),
            "rising_missed_repeated_zero_strength_history_workorder_count": len(
                _zero_strength_history_workorders(rising_missed)
            ),
        },
        "source_quality_workorders": {
            "repeated_zero_strength_history": _zero_strength_history_workorders(summaries),
            "rising_missed_repeated_zero_strength_history": _zero_strength_history_workorders(
                rising_missed
            ),
        },
        "blocker_rollup": [
            {"stage": stage, "reason": reason, "count": count}
            for (stage, reason), count in blocker_counter.most_common()
        ],
        "relief_blocker_split_rollup": {
            "rising_missed_buy": _rollup_blockers(rising_missed),
            "non_rising_promoted": _rollup_blockers(non_rising_promoted),
            "falling_promoted": _rollup_blockers(falling_promoted),
        },
        "rising_missed_buy": sorted(
            rising_missed,
            key=lambda item: item["max_price_delta_since_first_seen_pct"] or -999.0,
            reverse=True,
        ),
        "falling_real_submitted": sorted(
            falling_submitted,
            key=lambda item: item["latest_price_delta_since_first_seen_pct"] or 999.0,
        ),
        "promoted_symbols": sorted(
            summaries,
            key=lambda item: item["max_price_delta_since_first_seen_pct"] or -999.0,
            reverse=True,
        ),
    }


def _default_pipeline_path(target_date: str) -> Path:
    plain_path = PROJECT_ROOT / "data" / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if plain_path.exists():
        return plain_path
    gz_path = plain_path.with_suffix(plain_path.suffix + ".gz")
    return gz_path if gz_path.exists() else plain_path


def _default_output_path(target_date: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "report"
        / "intraday_entry_blocker_diagnostics"
        / f"intraday_entry_blocker_diagnostics_{target_date}.json"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build intraday entry blocker diagnostics from pipeline events.")
    parser.add_argument("--target-date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--pipeline-path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--since", help="Only include events with emitted_at at or after this ISO timestamp.")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)

    pipeline_path = args.pipeline_path or _default_pipeline_path(args.target_date)
    output_path = args.output or _default_output_path(args.target_date)
    report = build_report(target_date=args.target_date, pipeline_path=pipeline_path, since=args.since)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.print_summary:
        print(json.dumps({"output": str(output_path), **report["summary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
