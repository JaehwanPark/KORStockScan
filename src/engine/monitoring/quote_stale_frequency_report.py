"""Build report-only quote stale frequency diagnostics."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "quote_stale_frequency"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENTS_DIR = DATA_DIR / "threshold_cycle"
BOT_HISTORY_LOG = Path("logs/bot_history.log")
DEFAULT_STALE_THRESHOLD_MS = 3000.0

FORBIDDEN_USES = [
    "EV",
    "rolling_tuning",
    "MTD_tuning",
    "cumulative_tuning",
    "live_auto_promotion",
    "runtime_apply_bridge",
    "intraday_threshold_mutation",
    "provider_route_change",
    "order_price_change",
    "quantity_cap_change",
    "position_cap_release",
    "broker_guard_bypass",
    "stale_quote_bypass",
    "bot_restart",
    "real_execution_quality_approval",
]

KIWOOM_FRESHNESS_OPERATING_ASSUMPTIONS = [
    {
        "topic": "subscription_item_limit",
        "status": "official_number_not_documented",
        "safe_policy": (
            "Treat each websocket item as consuming quota. Count KRX/NXT alternate-route "
            "items separately until Kiwoom confirms otherwise."
        ),
    },
    {
        "topic": "idle_no_event_unsubscribe",
        "status": "exact_idle_timeout_and_cancel_notice_not_documented",
        "safe_policy": (
            "Use client last-receive timestamps to detect no-tick/stale symbols and recover "
            "with bounded REMOVE/REG or reconnect logic."
        ),
    },
    {
        "topic": "reg_refresh_semantics",
        "status": "refresh_1_append_refresh_0_replace",
        "safe_policy": (
            "For NXT-to-KRX route changes, REMOVE the old NXT item before KRX REG; do not "
            "rely on refresh=1 as a full replacement."
        ),
    },
    {
        "topic": "rereg_cooldown",
        "status": "official_cooldown_not_documented",
        "safe_policy": (
            "Start with bounded retry and backoff to avoid request-throttle errors; keep "
            "repair actions observable in logs."
        ),
    },
    {
        "topic": "server_timestamp_sequence",
        "status": "millisecond_server_timestamp_and_global_sequence_not_documented",
        "safe_policy": (
            "Stamp websocket receives on the client, maintain local counters, and compare "
            "against ka10003/ka10004 snapshots for source-quality recovery."
        ),
    },
    {
        "topic": "ka10004_bid_req_base_tm",
        "status": "format_and_authority_ambiguous",
        "safe_policy": (
            "Use bid_req_base_tm as raw snapshot reference-time provenance only; freshness "
            "authority remains the client receive timestamp or measured refresh age."
        ),
    },
]

KIWOOM_SUPPORT_QUESTIONS = [
    (
        "What is the current websocket concurrent subscription limit per session, "
        "and are KRX/NXT alternate-route items counted separately?"
    ),
    (
        "Can the server automatically cancel or stop idle/low-liquidity realtime "
        "subscriptions, and if so what timeout and notice payload should clients expect?"
    ),
    (
        "Is REMOVE plus REG the official required procedure for NXT-to-KRX route "
        "transition, and is refresh=1 append-only for all realtime types?"
    ),
    (
        "What retry cooldown and per-second/per-minute REG or REST snapshot limits "
        "should clients use to avoid 105110-style throttling?"
    ),
    (
        "Is there any realtime millisecond server-send timestamp, sequence number, "
        "or gap-detection API not shown in the public payload docs?"
    ),
    (
        "What exact format and clock basis does ka10004 bid_req_base_tm use in "
        "production, and can it ever be used as freshness authority?"
    ),
]

QUOTE_AGE_FIELDS = (
    ("quote_age_ms", 1.0),
    ("quote_age_at_submit_ms", 1.0),
    ("price_decision_context_age_ms", 1.0),
    ("pre_submit_ws_snapshot_refresh_age_ms", 1.0),
    ("pre_submit_rest_orderbook_refresh_age_ms", 1.0),
    ("quote_consistency_ws_age_ms", 1.0),
    ("quote_consistency_age_ms", 1.0),
    ("holding_ws_age_sec", 1000.0),
    ("ws_age_sec", 1000.0),
)

SCANNER_STAGES = {
    "scalping_scanner_fast_precheck",
    "blocked_vpw",
    "blocked_strength_momentum",
}
HOLDING_SCALE_STAGES = {
    "stat_action_decision_snapshot",
    "reversal_add_blocked_reason",
    "pyramid_blocked_reason",
    "ai_holding_review",
}


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip().replace(",", "").replace("+", "").replace("%", "")
    if text in {"", "-", "None", "none", "null", "nan", "NaN", "unknown"}:
        return default
    if text == "not_available_realtime_type_age_ms":
        return default
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _flatten_event(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(row)
    merged.update(fields)
    return merged


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


def _parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _time_bucket(ts: datetime | None) -> str:
    if ts is None:
        return "unknown"
    hm = ts.hour * 100 + ts.minute
    if hm < 900:
        return "pre_0900"
    if hm < 1200:
        return "regular_0900_1200"
    if hm < 1500:
        return "regular_1200_1500"
    if hm < 1520:
        return "regular_1500_1520"
    if hm < 1530:
        return "closing_1520_1530"
    if hm < 1605:
        return "post_1530_1605"
    if hm < 1950:
        return "nxt_after_1605_1950"
    return "after_1950"


def _quote_age(row: dict[str, Any]) -> tuple[str | None, float | None]:
    for field, multiplier in QUOTE_AGE_FIELDS:
        value = _to_float(row.get(field))
        if value is not None and value >= 0:
            return field, float(value) * multiplier
    return None, None


def _row_class(stage: str, pipeline: str, row: dict[str, Any]) -> str:
    stage_l = stage.lower()
    pipeline_l = pipeline.lower()
    if _boolish(row.get("actual_order_submitted")):
        return "actual_submit"
    if (
        "sell_order" in stage_l
        or stage_l.startswith("sell_")
        or "sell_order" in pipeline_l
    ):
        return "sell_execution_or_exit"
    if stage in SCANNER_STAGES:
        return "scanner_watch"
    if (
        stage in HOLDING_SCALE_STAGES
        or "scale" in stage_l
        or "pyramid" in stage_l
        or "avg" in stage_l
    ):
        return "holding_scale_input"
    if "entry" in stage_l or "latency" in stage_l or "submit" in stage_l:
        return "entry_submit_input"
    if "quote_consistency" in stage_l or row.get("quote_consistency_family"):
        return "quote_consistency"
    return "other"


def _percentiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {
            "avg": None,
            "p50": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
        }
    ordered = sorted(values)

    def pick(percent: float) -> float:
        idx = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percent))))
        return round(float(ordered[idx]), 4)

    return {
        "avg": round(float(mean(ordered)), 4),
        "p50": pick(0.50),
        "p75": pick(0.75),
        "p90": pick(0.90),
        "p95": pick(0.95),
        "p99": pick(0.99),
        "max": round(float(ordered[-1]), 4),
    }


def _rate_pct(count: int, total: int) -> float:
    return round((float(count) / float(total) * 100.0), 4) if total else 0.0


def _group_summary(
    records: list[dict[str, Any]], key: str, *, limit: int | None = None
) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "stale": 0, "ages": []}
    )
    for record in records:
        group_key = str(record.get(key) or "-")
        groups[group_key]["total"] += 1
        groups[group_key]["stale"] += int(bool(record["stale"]))
        groups[group_key]["ages"].append(float(record["quote_age_ms"]))
    rows = []
    for group_key, values in groups.items():
        total = int(values["total"])
        stale = int(values["stale"])
        rows.append(
            {
                key: group_key,
                "total": total,
                "stale_count": stale,
                "stale_rate_pct": _rate_pct(stale, total),
                "quote_age_ms": _percentiles(values["ages"]),
            }
        )
    rows.sort(key=lambda item: (-int(item["total"]), str(item.get(key) or "")))
    return rows[:limit] if limit else rows


def _counter_rows(
    counter: Counter, *, limit: int | None = None
) -> list[dict[str, Any]]:
    rows = [
        {"key": str(key), "count": int(value)}
        for key, value in counter.most_common(limit)
    ]
    return rows


def _top_streaks(
    records: list[dict[str, Any]], *, limit: int = 30
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    for record in records:
        if record["class"] not in {
            "scanner_watch",
            "holding_scale_input",
            "entry_submit_input",
        }:
            continue
        grouped[
            (
                str(record["source"]),
                str(record["class"]),
                str(record["stage"]),
                str(record.get("stock_code") or ""),
                str(record.get("stock_name") or ""),
            )
        ].append(record)

    rows: list[dict[str, Any]] = []
    for (source, row_class, stage, stock_code, stock_name), items in grouped.items():
        if len(items) < 2:
            continue
        items.sort(
            key=lambda item: (
                item.get("emitted_at") or "",
                int(item.get("row_index") or 0),
            )
        )
        run = 0
        max_run = 0
        stale_count = 0
        max_age = 0.0
        for item in items:
            max_age = max(max_age, float(item["quote_age_ms"]))
            if item["stale"]:
                stale_count += 1
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
        if not stale_count:
            continue
        rows.append(
            {
                "source": source,
                "class": row_class,
                "stage": stage,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "total": len(items),
                "stale_count": stale_count,
                "stale_rate_pct": _rate_pct(stale_count, len(items)),
                "max_consecutive_stale": max_run,
                "max_quote_age_ms": round(max_age, 4),
            }
        )
    rows.sort(
        key=lambda item: (
            -int(item["max_consecutive_stale"]),
            -float(item["stale_rate_pct"]),
            -int(item["stale_count"]),
            str(item["stage"]),
            str(item["stock_code"]),
        )
    )
    return rows[:limit]


def _scale_in_refresh_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter = Counter()
    reasons: Counter = Counter()
    quote_reasons: Counter = Counter()
    transitions: Counter = Counter()
    stale_reason_tokens: Counter = Counter()

    for raw in rows:
        if str(raw.get("stage") or "") != "scale_in_feature_context_refresh":
            continue
        row = _flatten_event(raw)
        counts["total"] += 1
        attempted = str(row.get("scale_in_feature_refresh_attempted") or "-")
        applied = str(row.get("scale_in_feature_refresh_applied") or "-")
        reason = str(row.get("scale_in_feature_refresh_reason") or "-")
        existing_quality = str(
            row.get("scale_in_feature_refresh_existing_quality") or "-"
        )
        new_quality = str(row.get("scale_in_feature_refresh_new_quality") or "-")
        counts[f"attempted_{attempted}"] += 1
        counts[f"applied_{applied}"] += 1
        reasons[reason] += 1
        quote_reasons[str(row.get("scale_in_feature_refresh_quote_reason") or "-")] += 1
        transitions[f"{existing_quality}->{new_quality}"] += 1
        for field in (
            "scale_in_feature_refresh_existing_stale_reason",
            "scale_in_feature_refresh_new_stale_reason",
        ):
            value = str(row.get(field) or "")
            for token in value.replace("|", ",").split(","):
                token = token.strip()
                if token and token != "-":
                    stale_reason_tokens[token] += 1

    total = int(counts.get("total", 0))
    applied_true = int(counts.get("applied_True", 0))
    return {
        "counts": dict(counts),
        "applied_true_rate_pct": _rate_pct(applied_true, total),
        "reasons": _counter_rows(reasons),
        "quote_refresh_reasons": _counter_rows(quote_reasons),
        "quality_transitions": _counter_rows(transitions),
        "stale_reason_tokens": _counter_rows(stale_reason_tokens),
    }


def _repair_log_summary(
    target_date: str, *, path: Path | None = None
) -> dict[str, Any]:
    log_path = path or BOT_HISTORY_LOG
    actual_path = log_path if log_path.is_absolute() else Path.cwd() / log_path
    patterns = {
        "first_ws_data": "first realtime data received",
        "recent_reg_skip": "recent REG duplicate skipped",
        "persistent_rebuild": "persistent repair group rebuild",
        "persistent_limit": "persistent repair registration limit",
        "persistent_stuck_cooldown": "persistent repair stuck cooldown",
        "persistent_no_tick_cooldown": "persistent repair no-tick cooldown",
        "scanner_cap": "scanner cap skipped new candidate",
        "reg_item_budget": "REG item budget skipped",
        "alternate_limit": "alternate route registration limit",
    }
    raw_patterns = {
        "first_ws_data": "첫 실시간 데이터 수신 확인",
        "recent_reg_skip": "최근 REG 중복 생략",
        "persistent_rebuild": "persistent repair 전체 REG 그룹 재구성",
        "persistent_limit": "persistent repair 등록 제한",
        "persistent_stuck_cooldown": "persistent repair stuck cooldown",
        "persistent_no_tick_cooldown": "persistent repair no-tick cooldown entered",
        "scanner_cap": "SCALPING 스캐너 cap",
        "reg_item_budget": "REG item budget 초과",
        "alternate_limit": "alternate route 등록 제한",
    }
    counts: Counter = Counter()
    code_counts: dict[str, Counter] = defaultdict(Counter)
    if not actual_path.exists():
        return {
            "path": None,
            "counts": {},
            "labels": patterns,
            "top_codes": {},
        }

    with actual_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if target_date not in line:
                continue
            matched_key = ""
            for key, pattern in raw_patterns.items():
                if pattern in line:
                    matched_key = key
                    counts[key] += 1
                    break
            if not matched_key:
                continue
            if matched_key not in {
                "persistent_limit",
                "persistent_stuck_cooldown",
                "persistent_no_tick_cooldown",
                "persistent_rebuild",
            }:
                continue
            codes: list[str] = []
            code_match = re.search(r"code=([0-9]{6})", line)
            if code_match:
                codes.append(code_match.group(1))
            for group in re.findall(
                r"(?:skipped|allowed|repair_targets)=\[([^\]]+)\]", line
            ):
                codes.extend(re.findall(r"[0-9]{6}", group))
            for code in codes:
                code_counts[matched_key][code] += 1

    return {
        "path": str(actual_path),
        "counts": dict(counts),
        "labels": patterns,
        "top_codes": {
            key: [
                {"stock_code": code, "count": count}
                for code, count in counter.most_common(10)
            ]
            for key, counter in sorted(code_counts.items())
        },
    }


def build_quote_stale_frequency_report(
    target_date: str | None = None,
    *,
    stale_threshold_ms: float = DEFAULT_STALE_THRESHOLD_MS,
    include_repair_log: bool = True,
) -> dict[str, Any]:
    target_date = target_date or date.today().isoformat()
    paths = _source_paths(target_date)
    records: list[dict[str, Any]] = []
    source_missing = [name for name, path in paths.items() if not path.exists()]
    row_count_by_source: Counter = Counter()

    raw_rows_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source_name, path in paths.items():
        for row_index, raw in enumerate(_iter_rows(path), start=1):
            raw_rows_by_source[source_name].append(raw)
            row = _flatten_event(raw)
            age_source, age_ms = _quote_age(row)
            if age_ms is None:
                continue
            stage = str(
                raw.get("stage")
                or row.get("stage")
                or row.get("event_type")
                or "unknown"
            )
            pipeline = str(raw.get("pipeline") or row.get("pipeline") or "")
            emitted_at = str(raw.get("emitted_at") or row.get("emitted_at") or "")
            ts = _parse_ts(emitted_at)
            quote_age_source = str(row.get("quote_age_source") or "").strip()
            row_count_by_source[source_name] += 1
            records.append(
                {
                    "source": source_name,
                    "row_index": row_index,
                    "stage": stage,
                    "pipeline": pipeline,
                    "class": _row_class(stage, pipeline, row),
                    "stock_code": str(
                        raw.get("stock_code") or row.get("stock_code") or ""
                    ),
                    "stock_name": str(
                        raw.get("stock_name") or row.get("stock_name") or ""
                    ),
                    "record_id": str(
                        raw.get("record_id") or row.get("record_id") or ""
                    ),
                    "emitted_at": emitted_at,
                    "time_bucket": _time_bucket(ts),
                    "age_source": age_source,
                    "quote_age_ms": round(float(age_ms), 4),
                    "stale": float(age_ms) >= float(stale_threshold_ms),
                    "quote_age_source": quote_age_source or "missing",
                }
            )

    if any(record["source"] == "pipeline_events" for record in records):
        primary_source = "pipeline_events"
    else:
        primary_source = str(records[0]["source"]) if records else "pipeline_events"
    primary_records = [
        record for record in records if record["source"] == primary_source
    ]
    stale_count = sum(1 for record in primary_records if record["stale"])
    ages = [float(record["quote_age_ms"]) for record in primary_records]
    scale_rows = list(raw_rows_by_source.get(primary_source) or [])
    if not scale_rows:
        for rows in raw_rows_by_source.values():
            scale_rows.extend(rows)

    quote_age_source_missing_by_stage: Counter = Counter()
    for record in primary_records:
        if record["age_source"] == "quote_age_ms" and str(
            record.get("quote_age_source") or ""
        ) in {"", "-", "missing", "None", "none"}:
            quote_age_source_missing_by_stage[str(record["stage"])] += 1

    by_class = _group_summary(primary_records, "class")
    by_stage = _group_summary(primary_records, "stage", limit=40)
    by_time_bucket = _group_summary(primary_records, "time_bucket")
    by_age_source = _group_summary(records, "age_source")
    by_source = _group_summary(records, "source")
    class_by_time: list[dict[str, Any]] = []
    for row_class in sorted({record["class"] for record in primary_records}):
        class_records = [
            record for record in primary_records if record["class"] == row_class
        ]
        for item in _group_summary(class_records, "time_bucket"):
            item["class"] = row_class
            if int(item["total"]) >= 20:
                class_by_time.append(item)
    class_by_time.sort(key=lambda item: (str(item["class"]), str(item["time_bucket"])))

    scale_in_refresh = _scale_in_refresh_summary(scale_rows)
    repair_log_summary = (
        _repair_log_summary(target_date)
        if include_repair_log
        else {
            "path": None,
            "counts": {},
            "labels": {},
            "top_codes": {},
        }
    )

    findings: list[dict[str, Any]] = []
    if source_missing:
        findings.append(
            {
                "severity": "warning",
                "code": "quote_stale_frequency_source_missing",
                "sources": source_missing,
            }
        )
    if not records:
        findings.append(
            {
                "severity": "warning",
                "code": "quote_stale_frequency_observation_missing",
                "message": "No rows with quote age fields were found.",
            }
        )
    class_lookup = {str(item["class"]): item for item in by_class}
    scanner_rate = float(
        (class_lookup.get("scanner_watch") or {}).get("stale_rate_pct") or 0.0
    )
    scale_rate = float(
        (class_lookup.get("holding_scale_input") or {}).get("stale_rate_pct") or 0.0
    )
    if scanner_rate >= 50.0:
        findings.append(
            {
                "severity": "warning",
                "code": "scanner_watch_stale_rate_high",
                "stale_rate_pct": scanner_rate,
            }
        )
    if scale_rate >= 40.0:
        findings.append(
            {
                "severity": "warning",
                "code": "holding_scale_stale_rate_high",
                "stale_rate_pct": scale_rate,
            }
        )
    refresh_counts = scale_in_refresh.get("counts") or {}
    if (
        int(refresh_counts.get("total", 0) or 0)
        and float(scale_in_refresh.get("applied_true_rate_pct") or 0.0) < 25.0
    ):
        findings.append(
            {
                "severity": "warning",
                "code": "scale_in_feature_refresh_recovery_rate_low",
                "applied_true_rate_pct": scale_in_refresh.get("applied_true_rate_pct"),
            }
        )
    repair_counts = repair_log_summary.get("counts") or {}
    if int(repair_counts.get("persistent_no_tick_cooldown", 0) or 0):
        findings.append(
            {
                "severity": "warning",
                "code": "persistent_ws_no_tick_cooldown_observed",
                "count": int(repair_counts.get("persistent_no_tick_cooldown", 0) or 0),
            }
        )

    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "metric_role": "source_quality_gate",
        "decision_authority": "quote_stale_frequency_report_only",
        "window_policy": "same_day_runtime_events",
        "sample_floor": "not_applicable_diagnostic",
        "primary_decision_metric": "quote_stale_rate_pct",
        "source_quality_gate": "diagnostic_only_no_tuning_input",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "stale_threshold_ms": float(stale_threshold_ms),
        "primary_source": primary_source,
        "sources": {
            name: str(path) if path.exists() else None for name, path in paths.items()
        },
        "summary": {
            "rows_with_quote_age": len(primary_records),
            "stale_count": stale_count,
            "stale_rate_pct": _rate_pct(stale_count, len(primary_records)),
            "quote_age_ms": _percentiles(ages),
            "source_quote_age_row_counts": dict(row_count_by_source),
            "quote_age_source_missing_count": sum(
                quote_age_source_missing_by_stage.values()
            ),
        },
        "by_source": by_source,
        "by_class": by_class,
        "by_time_bucket": by_time_bucket,
        "by_stage": by_stage,
        "by_age_source": by_age_source,
        "class_by_time_bucket": class_by_time,
        "top_stale_streaks": _top_streaks(primary_records),
        "quote_age_source_missing_by_stage": _counter_rows(
            quote_age_source_missing_by_stage
        ),
        "scale_in_feature_context_refresh": scale_in_refresh,
        "ws_repair_log_summary": repair_log_summary,
        "kiwoom_freshness_operating_assumptions": KIWOOM_FRESHNESS_OPERATING_ASSUMPTIONS,
        "kiwoom_support_questions": KIWOOM_SUPPORT_QUESTIONS,
        "verifier_findings": findings,
    }


def write_quote_stale_frequency_report(
    report: dict[str, Any],
    *,
    output_dir: Path = REPORT_DIR,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = str(report.get("target_date"))
    json_path = output_dir / f"{REPORT_TYPE}_{target_date}.json"
    md_path = output_dir / f"{REPORT_TYPE}_{target_date}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    summary = report.get("summary") or {}
    lines = [
        f"# Quote Stale Frequency Report {target_date}",
        "",
        "## Contract",
        "",
        f"- metric_role: `{report.get('metric_role')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- broker_order_forbidden: `{report.get('broker_order_forbidden')}`",
        f"- stale_threshold_ms: `{report.get('stale_threshold_ms')}`",
        f"- primary_source: `{report.get('primary_source')}`",
        "",
        "## Summary",
        "",
        f"- rows_with_quote_age: `{summary.get('rows_with_quote_age', 0)}`",
        f"- stale_count: `{summary.get('stale_count', 0)}`",
        f"- stale_rate_pct: `{summary.get('stale_rate_pct', 0.0)}`",
        f"- quote_age_source_missing_count: `{summary.get('quote_age_source_missing_count', 0)}`",
        f"- quote_age_ms: `{summary.get('quote_age_ms')}`",
        "",
        "## Verifier Findings",
        "",
    ]
    findings = report.get("verifier_findings") or []
    if findings:
        lines.extend(
            f"- `{item.get('severity')}` `{item.get('code')}`" for item in findings
        )
    else:
        lines.append("- `ok` `none`")

    lines.extend(["", "## Kiwoom Freshness Operating Assumptions", ""])
    assumptions = report.get("kiwoom_freshness_operating_assumptions") or []
    if not assumptions:
        lines.append("- none")
    for item in assumptions:
        lines.append(
            "- "
            f"`{item.get('topic')}` status={item.get('status')} "
            f"policy={item.get('safe_policy')}"
        )

    lines.extend(["", "## Kiwoom Support Questions", ""])
    questions = report.get("kiwoom_support_questions") or []
    if not questions:
        lines.append("- none")
    for question in questions:
        lines.append(f"- {question}")

    def append_group(
        title: str, rows: list[dict[str, Any]], key: str, *, limit: int = 12
    ) -> None:
        lines.extend(["", f"## {title}", ""])
        if not rows:
            lines.append("- none")
            return
        for item in rows[:limit]:
            lines.append(
                "- "
                f"`{item.get(key)}` total={item.get('total')} "
                f"stale={item.get('stale_count')} "
                f"rate={item.get('stale_rate_pct')}% "
                f"p50={((item.get('quote_age_ms') or {}).get('p50'))} "
                f"p90={((item.get('quote_age_ms') or {}).get('p90'))} "
                f"max={((item.get('quote_age_ms') or {}).get('max'))}"
            )

    append_group("By Class", report.get("by_class") or [], "class")
    append_group("By Time Bucket", report.get("by_time_bucket") or [], "time_bucket")
    append_group("By Stage", report.get("by_stage") or [], "stage", limit=20)
    append_group("By Age Source", report.get("by_age_source") or [], "age_source")

    lines.extend(["", "## Top Stale Streaks", ""])
    streaks = report.get("top_stale_streaks") or []
    if not streaks:
        lines.append("- none")
    for item in streaks[:15]:
        lines.append(
            "- "
            f"`{item.get('stock_name')}` `{item.get('stock_code')}` "
            f"class={item.get('class')} stage={item.get('stage')} "
            f"total={item.get('total')} stale={item.get('stale_count')} "
            f"rate={item.get('stale_rate_pct')}% "
            f"max_run={item.get('max_consecutive_stale')} "
            f"max_age_ms={item.get('max_quote_age_ms')}"
        )

    refresh = report.get("scale_in_feature_context_refresh") or {}
    lines.extend(["", "## Scale-In Feature Refresh", ""])
    lines.append(f"- counts: `{refresh.get('counts') or {}}`")
    lines.append(f"- applied_true_rate_pct: `{refresh.get('applied_true_rate_pct')}`")
    lines.append(f"- reasons: `{refresh.get('reasons') or []}`")
    lines.append(f"- stale_reason_tokens: `{refresh.get('stale_reason_tokens') or []}`")

    repair = report.get("ws_repair_log_summary") or {}
    lines.extend(["", "## WS Repair Log Summary", ""])
    lines.append(f"- path: `{repair.get('path')}`")
    lines.append(f"- counts: `{repair.get('counts') or {}}`")
    lines.append(f"- top_codes: `{repair.get('top_codes') or {}}`")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument(
        "--stale-threshold-ms", type=float, default=DEFAULT_STALE_THRESHOLD_MS
    )
    parser.add_argument("--skip-repair-log", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_quote_stale_frequency_report(
        args.target_date,
        stale_threshold_ms=args.stale_threshold_ms,
        include_repair_log=not args.skip_repair_log,
    )
    if args.write:
        json_path, md_path = write_quote_stale_frequency_report(report)
        print(
            json.dumps({"json": str(json_path), "md": str(md_path)}, ensure_ascii=False)
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
