"""Build intraday websocket freshness diagnostics and postclose workorder directives."""

from __future__ import annotations

import argparse
import ast
import json
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


KST = timezone(timedelta(hours=9))
REPORT_TYPE = "intraday_ws_freshness_monitor"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
WORKORDER_REPORT_DIR = DATA_DIR / "report" / "intraday_ws_freshness_workorder"
WORKORDER_DOC_DIR = Path(__file__).resolve().parents[3] / "docs" / "code-improvement-workorders"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENTS_DIR = DATA_DIR / "threshold_cycle"
DEFAULT_STALE_SEC = 30.0

FORBIDDEN_USES = [
    "EV",
    "rolling_tuning",
    "MTD_tuning",
    "cumulative_tuning",
    "live_auto_promotion",
    "runtime_apply_bridge",
    "intraday_threshold_mutation",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "provider_route_change",
    "order_price_change",
    "quantity_cap_change",
    "position_cap_release",
    "bot_restart",
    "real_execution_quality_approval",
]

METRIC_CONTRACT = {
    "metric_role": "source_quality_gate",
    "decision_authority": "ws_freshness_intraday_monitor_source_only",
    "window_policy": "daily_intraday_operational",
    "sample_floor": "at_least_one_ws_snapshot_or_pipeline_event",
    "primary_decision_metric": "subscription_stale_rate_pct",
    "source_quality_gate": "separate_subscription_stale_from_trade_tick_quiet_before_postclose_workorder",
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "broker_order_forbidden": True,
}

WS_AGE_FIELDS_MS = (
    "ws_last_0b_age_ms",
    "ws_last_0d_age_ms",
    "ws_last_0w_age_ms",
    "ws_last_0f_age_ms",
)

PROVIDER_FIELD_TOKENS = ("provider", "ai_provider", "model_provider")


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip().replace(",", "").replace("+", "")
    if text.lower() in {
        "",
        "-",
        "none",
        "null",
        "nan",
        "unknown",
        "not_available_realtime_type_age_ms",
        "not_available",
    }:
        return default
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _listish(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except Exception:
                try:
                    parsed = ast.literal_eval(text)
                except Exception:
                    parsed = None
            if isinstance(parsed, list):
                return parsed
    return []


def _dictish(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = json.loads(text)
            except Exception:
                try:
                    parsed = ast.literal_eval(text)
                except Exception:
                    parsed = None
            if isinstance(parsed, dict):
                return parsed
    return {}


def _flatten_event(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(row)
    merged.update(fields)
    return merged


def _iter_jsonl_rows(path: Path) -> Iterable[dict[str, Any]]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    yield from iter_jsonl(actual_path)


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _event_time(row: dict[str, Any]) -> datetime | None:
    value = row.get("emitted_at") or row.get("generated_at") or row.get("timestamp")
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _time_bucket(row: dict[str, Any]) -> str:
    ts = _event_time(row)
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
    return "post_1530"


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "pipeline_events": existing_or_gzip_path(
            PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
        ),
        "threshold_events": existing_or_gzip_path(
            THRESHOLD_EVENTS_DIR / f"threshold_events_{target_date}.jsonl"
        ),
    }


def _rate_pct(count: int, total: int) -> float:
    return round((float(count) / float(total) * 100.0), 4) if total else 0.0


def _counter_rows(counter: Counter, *, limit: int = 20, key_name: str = "key") -> list[dict[str, Any]]:
    return [
        {key_name: str(key), "count": int(value)}
        for key, value in counter.most_common(limit)
    ]


def _snapshot_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = snapshot.get("rows")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(snapshot.get("symbols"), list):
        return [row for row in snapshot["symbols"] if isinstance(row, dict)]
    return []


def _row_provider_none(row: dict[str, Any]) -> bool:
    for key, value in row.items():
        key_l = str(key).lower()
        if not any(token in key_l for token in PROVIDER_FIELD_TOKENS):
            continue
        if str(value).strip().lower() == "none":
            return True
    return False


def _pipeline_event_class(row: dict[str, Any], *, stale_ms: float) -> dict[str, Any]:
    stage = str(row.get("stage") or row.get("event_type") or "unknown")
    reason_values = {
        str(row.get("source_quality_block_reason") or "").strip(),
        str(row.get("reason") or "").strip(),
        str(row.get("risk_state") or "").strip(),
        str(row.get("zero_context_blocker") or "").strip(),
    }
    trade_tick_quiet = (
        _boolish(row.get("trade_tick_quiet"))
        or "trade_tick_quiet" in reason_values
        or str(row.get("trade_tick_quiet_reason") or "").strip()
        == "fresh_non_trade_ws_without_fresh_0b"
    )
    repair_recommended = _boolish(row.get("repair_recommended"))
    repair_reason = str(row.get("repair_reason") or "").strip() or "none"
    freshness_state = str(row.get("freshness_state") or "").strip()
    subscription_stale = repair_recommended or repair_reason in {
        "subscription_no_tick",
        "subscription_stale",
    } or freshness_state in {"no_tick", "stale"}

    age_0b = _to_float(row.get("ws_last_0b_age_ms"))
    age_0d = _to_float(row.get("ws_last_0d_age_ms"))
    if age_0b is None:
        age_0b = _to_float(row.get("last_0b_age_sec"))
        age_0b = age_0b * 1000.0 if age_0b is not None else None
    if age_0d is None:
        age_0d = _to_float(row.get("last_0d_age_sec"))
        age_0d = age_0d * 1000.0 if age_0d is not None else None

    stale_0b = age_0b is not None and age_0b >= stale_ms
    stale_0d = age_0d is not None and age_0d >= stale_ms
    fresh_0d = age_0d is not None and age_0d < stale_ms
    both_stale = stale_0b and stale_0d
    quiet_by_age = fresh_0d and stale_0b

    if not trade_tick_quiet and quiet_by_age:
        trade_tick_quiet = True

    submit_related = "submit" in stage.lower() or "order_bundle" in stage.lower()
    scout_related = "scout" in stage.lower() or "rising_missed" in json.dumps(row, ensure_ascii=False)

    return {
        "stage": stage,
        "stock_code": str(row.get("stock_code") or ""),
        "stock_name": str(row.get("stock_name") or ""),
        "time_bucket": _time_bucket(row),
        "trade_tick_quiet": bool(trade_tick_quiet),
        "subscription_stale": bool(subscription_stale),
        "both_ws_stale": bool(both_stale),
        "fresh_0d_stale_0b": bool(quiet_by_age),
        "provider_none": _row_provider_none(row),
        "submit_related": submit_related,
        "scout_related": scout_related,
        "ws_age_observed": any(_to_float(row.get(key)) is not None for key in WS_AGE_FIELDS_MS)
        or age_0b is not None
        or age_0d is not None,
        "age_0b_ms": age_0b,
        "age_0d_ms": age_0d,
        "repair_reason": repair_reason,
        "freshness_state": freshness_state or "-",
    }


def _snapshot_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    states: Counter = Counter()
    repair_reasons: Counter = Counter()
    route_counts: Counter = Counter()
    suffix_counts: Counter = Counter()
    quiet_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    multi_route_rows: list[dict[str, Any]] = []
    quota_units = 0
    for row in rows:
        state = str(row.get("freshness_state") or "unknown")
        states[state] += 1
        reason = str(row.get("repair_reason") or "none")
        repair_reasons[reason] += 1
        quota_units += int(_to_float(row.get("registered_item_quota_units"), 0.0) or 0)
        for route, count in _dictish(row.get("registered_route_counts")).items():
            route_counts[str(route)] += int(_to_float(count, 0.0) or 0)
        for suffix in _listish(row.get("registered_market_suffixes")):
            suffix_counts[str(suffix) or "KRX"] += 1
        if _boolish(row.get("multi_route_registered")):
            multi_route_rows.append(row)
        if _boolish(row.get("trade_tick_quiet")):
            quiet_rows.append(row)
        if _boolish(row.get("repair_recommended")):
            repair_rows.append(row)
    total = len(rows)
    stale_like = int(states.get("stale", 0) + states.get("no_tick", 0))
    return {
        "row_count": total,
        "freshness_state_counts": dict(states),
        "repair_reason_counts": dict(repair_reasons),
        "subscription_stale_like_count": stale_like,
        "subscription_stale_like_rate_pct": _rate_pct(stale_like, total),
        "trade_tick_quiet_count": len(quiet_rows),
        "trade_tick_quiet_rate_pct": _rate_pct(len(quiet_rows), total),
        "repair_recommended_count": len(repair_rows),
        "registered_item_quota_units": quota_units,
        "registered_route_counts": dict(route_counts),
        "registered_market_suffix_counts": dict(suffix_counts),
        "multi_route_registered_count": len(multi_route_rows),
        "multi_route_registered_rate_pct": _rate_pct(len(multi_route_rows), total),
        "route_repair_policy": "remove_then_reg_required_for_route_transition",
        "top_trade_tick_quiet_symbols": [
            {
                "stock_code": str(row.get("stock_code") or ""),
                "last_0b_age_sec": row.get("last_0b_age_sec"),
                "last_0d_age_sec": row.get("last_0d_age_sec"),
                "last_trade_cum_volume": row.get("last_trade_cum_volume"),
            }
            for row in quiet_rows[:20]
        ],
        "top_repair_symbols": [
            {
                "stock_code": str(row.get("stock_code") or ""),
                "freshness_state": row.get("freshness_state"),
                "repair_reason": row.get("repair_reason"),
                "last_receive_age_sec": row.get("last_receive_age_sec"),
            }
            for row in repair_rows[:20]
        ],
        "top_multi_route_symbols": [
            {
                "stock_code": str(row.get("stock_code") or ""),
                "registered_items": row.get("registered_items") or [],
                "registered_market_routes": row.get("registered_market_routes") or [],
                "registered_item_quota_units": row.get("registered_item_quota_units"),
            }
            for row in multi_route_rows[:20]
        ],
    }


def _build_workorders(summary: dict[str, Any], *, target_date: str) -> list[dict[str, Any]]:
    counts = summary["pipeline_counts"]
    snapshot = summary["snapshot_summary"]
    orders: list[dict[str, Any]] = []
    base = {
        "target_date": target_date,
        "source_report_type": REPORT_TYPE,
        "decision": "implement_now",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": METRIC_CONTRACT["decision_authority"],
        "forbidden_uses": FORBIDDEN_USES,
    }
    if counts.get("subscription_stale", 0) or snapshot.get("repair_recommended_count", 0):
        orders.append(
            {
                **base,
                "order_id": "order_ws_subscription_stale_repair_observability",
                "title": "WS subscription stale repair observability",
                "priority": 1,
                "intent": (
                    "Use intraday subscription_stale/no_tick evidence to verify REMOVE->REG recovery "
                    "timing, item budget, duplicate REG suppression, and repair cooldown provenance."
                ),
                "evidence": [
                    f"pipeline_subscription_stale_count={counts.get('subscription_stale', 0)}",
                    f"snapshot_repair_recommended_count={snapshot.get('repair_recommended_count', 0)}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_kiwoom_websocket.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("trade_tick_quiet", 0) or snapshot.get("trade_tick_quiet_count", 0):
        orders.append(
            {
                **base,
                "order_id": "order_ws_trade_tick_quiet_low_liquidity_classification",
                "title": "WS trade tick quiet low-liquidity classification",
                "priority": 2,
                "intent": (
                    "Keep fresh 0D plus stale/missing 0B as trade_tick_quiet source-quality evidence, "
                    "and enrich low-liquidity classification with cumulative-volume provenance before "
                    "requesting subscription repair."
                ),
                "evidence": [
                    f"pipeline_trade_tick_quiet_count={counts.get('trade_tick_quiet', 0)}",
                    f"fresh_0d_stale_0b_count={counts.get('fresh_0d_stale_0b', 0)}",
                    f"snapshot_trade_tick_quiet_count={snapshot.get('trade_tick_quiet_count', 0)}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_state_handler_fast_signatures.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("both_ws_stale", 0):
        orders.append(
            {
                **base,
                "order_id": "order_ws_total_stale_escalation",
                "title": "WS total stale escalation",
                "priority": 1,
                "intent": (
                    "Treat rows where both trade and orderbook websocket freshness are stale as "
                    "subscription/connection quality incidents and verify repair evidence after postclose."
                ),
                "evidence": [f"both_ws_stale_count={counts.get('both_ws_stale', 0)}"],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/monitoring/quote_stale_frequency_report.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("provider_none", 0):
        orders.append(
            {
                **base,
                "order_id": "order_ai_provider_none_intraday_incident",
                "title": "AI provider none intraday incident",
                "priority": 1,
                "intent": (
                    "Investigate and close intraday AI provider provenance rows that resolved to none. "
                    "Provider route must stay explicit and must not be silently treated as healthy."
                ),
                "evidence": [f"provider_none_count={counts.get('provider_none', 0)}"],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/ai",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if not orders:
        return []
    orders.sort(key=lambda item: (int(item.get("priority", 99)), str(item.get("order_id"))))
    return orders


def build_report(
    target_date: str | None = None,
    *,
    pipeline_path: Path | None = None,
    threshold_path: Path | None = None,
    subscription_snapshot_path: Path | None = None,
    stale_sec: float = DEFAULT_STALE_SEC,
    generated_at: str | None = None,
) -> dict[str, Any]:
    target_date = target_date or date.today().isoformat()
    stale_ms = float(stale_sec) * 1000.0
    paths = _source_paths(target_date)
    if pipeline_path is not None:
        paths["pipeline_events"] = pipeline_path
    if threshold_path is not None:
        paths["threshold_events"] = threshold_path

    source_missing = [name for name, path in paths.items() if not path.exists()]
    event_classes: list[dict[str, Any]] = []
    row_count_by_source: Counter = Counter()
    for source_name, path in paths.items():
        for raw in _iter_jsonl_rows(path):
            row_count_by_source[source_name] += 1
            row = _flatten_event(raw)
            event_class = _pipeline_event_class(row, stale_ms=stale_ms)
            event_class["source"] = source_name
            event_classes.append(event_class)

    counts: Counter = Counter()
    stage_counts: dict[str, Counter] = defaultdict(Counter)
    time_bucket_counts: dict[str, Counter] = defaultdict(Counter)
    symbol_counts: dict[str, Counter] = defaultdict(Counter)
    for item in event_classes:
        for key in (
            "trade_tick_quiet",
            "subscription_stale",
            "both_ws_stale",
            "fresh_0d_stale_0b",
            "provider_none",
            "submit_related",
            "scout_related",
            "ws_age_observed",
        ):
            if item.get(key):
                counts[key] += 1
        stage = str(item.get("stage") or "unknown")
        bucket = str(item.get("time_bucket") or "unknown")
        code = str(item.get("stock_code") or "")
        for key in ("trade_tick_quiet", "subscription_stale", "both_ws_stale", "provider_none"):
            if item.get(key):
                stage_counts[key][stage] += 1
                time_bucket_counts[key][bucket] += 1
                if code:
                    symbol_counts[key][code] += 1

    snapshot_payload = _read_json(subscription_snapshot_path)
    snapshot_rows = _snapshot_rows(snapshot_payload)
    snapshot = _snapshot_summary(snapshot_rows)

    total_events = len(event_classes)
    summary = {
        "target_date": target_date,
        "generated_at": generated_at or datetime.now(tz=KST).isoformat(),
        "report_type": REPORT_TYPE,
        "metric_contract": METRIC_CONTRACT,
        "source_paths": {name: str(path) for name, path in paths.items()},
        "source_missing": source_missing,
        "subscription_snapshot_path": str(subscription_snapshot_path) if subscription_snapshot_path else None,
        "row_count_by_source": dict(row_count_by_source),
        "pipeline_counts": dict(counts),
        "pipeline_event_count": total_events,
        "pipeline_rates": {
            "trade_tick_quiet_rate_pct": _rate_pct(int(counts.get("trade_tick_quiet", 0)), total_events),
            "subscription_stale_rate_pct": _rate_pct(int(counts.get("subscription_stale", 0)), total_events),
            "both_ws_stale_rate_pct": _rate_pct(int(counts.get("both_ws_stale", 0)), total_events),
            "provider_none_rate_pct": _rate_pct(int(counts.get("provider_none", 0)), total_events),
        },
        "snapshot_summary": snapshot,
        "by_stage": {
            key: _counter_rows(counter, key_name="stage")
            for key, counter in sorted(stage_counts.items())
        },
        "by_time_bucket": {
            key: _counter_rows(counter, key_name="time_bucket")
            for key, counter in sorted(time_bucket_counts.items())
        },
        "by_symbol": {
            key: _counter_rows(counter, key_name="stock_code")
            for key, counter in sorted(symbol_counts.items())
        },
    }
    workorders = _build_workorders(summary, target_date=target_date)
    summary["workorder_directives"] = workorders
    summary["workorder_summary"] = {
        "selected_order_count": len(workorders),
        "implement_now_runtime_effect_false_count": sum(
            1
            for item in workorders
            if item.get("decision") == "implement_now" and item.get("runtime_effect") is False
        ),
        "provider_none_incident_count": int(counts.get("provider_none", 0)),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    return summary


def _render_monitor_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Intraday WS Freshness Monitor - {report.get('target_date')}",
        "",
        "## Decision",
        "",
    ]
    workorder_count = (report.get("workorder_summary") or {}).get("selected_order_count", 0)
    if workorder_count:
        lines.append(
            f"- postclose_workorder_required: `{workorder_count}` source-only directives"
        )
    else:
        lines.append("- postclose_workorder_required: `0`")
    lines.extend(
        [
            "- runtime_effect: `false`",
            "- allowed_runtime_apply: `false`",
            "",
            "## Evidence",
            "",
            f"- pipeline_event_count: `{report.get('pipeline_event_count')}`",
            f"- pipeline_counts: `{report.get('pipeline_counts')}`",
            f"- pipeline_rates: `{report.get('pipeline_rates')}`",
            f"- snapshot_summary: `{report.get('snapshot_summary')}`",
            f"- source_missing: `{report.get('source_missing')}`",
            "",
            "## Metric Contract",
            "",
            f"- metric_role: `{METRIC_CONTRACT['metric_role']}`",
            f"- decision_authority: `{METRIC_CONTRACT['decision_authority']}`",
            f"- primary_decision_metric: `{METRIC_CONTRACT['primary_decision_metric']}`",
            f"- forbidden_uses: `{','.join(FORBIDDEN_USES)}`",
            "",
            "## Workorder Directives",
            "",
        ]
    )
    orders = report.get("workorder_directives") or []
    if not orders:
        lines.append("- none")
    for order in orders:
        lines.append(
            "- "
            f"`{order.get('order_id')}` priority={order.get('priority')} "
            f"runtime_effect={order.get('runtime_effect')} title={order.get('title')}"
        )
    return "\n".join(lines) + "\n"


def _render_workorder_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Intraday WS Freshness Postclose Workorder - {report.get('target_date')}",
        "",
        "Codex execution scope: implement only source-quality, instrumentation, report, provenance, and tests.",
        "",
        "## 2-Pass Execution",
        "",
        "1. First pass: implement instrumentation/report/provenance fixes, run code review, fix defects, and re-review.",
        "2. Second pass: confirm final review, regenerate the related report, and inspect workorder diff.",
        "",
        "## Guardrails",
        "",
        "- runtime_effect=false",
        "- allowed_runtime_apply=false",
        "- broker_order_forbidden=true",
        f"- forbidden_uses={','.join(FORBIDDEN_USES)}",
        "",
        "## Selected Directives",
        "",
    ]
    orders = report.get("workorder_directives") or []
    if not orders:
        lines.append("- none")
    for order in orders:
        lines.extend(
            [
                f"### {order.get('order_id')}",
                "",
                f"- decision: `{order.get('decision')}`",
                f"- priority: `{order.get('priority')}`",
                f"- title: {order.get('title')}",
                f"- intent: {order.get('intent')}",
                f"- evidence: `{order.get('evidence')}`",
                f"- files_likely_touched: `{order.get('files_likely_touched')}`",
                f"- acceptance_tests: `{order.get('acceptance_tests')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Required Final Report Split",
            "",
            "- Existing implementation",
            "- New implementation",
            "- Deferred or non-implement items",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], *, monitor_only: bool = False) -> tuple[Path, Path, Path | None, Path | None]:
    target_date = str(report.get("target_date") or date.today().isoformat())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    monitor_json = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json"
    monitor_md = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md"

    monitor_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monitor_md.write_text(_render_monitor_markdown(report), encoding="utf-8")
    if monitor_only:
        return monitor_json, monitor_md, None, None

    WORKORDER_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    WORKORDER_DOC_DIR.mkdir(parents=True, exist_ok=True)
    workorder_json = WORKORDER_REPORT_DIR / f"intraday_ws_freshness_workorder_{target_date}.json"
    workorder_md = WORKORDER_DOC_DIR / f"intraday_ws_freshness_workorder_{target_date}.md"
    workorder_payload = {
        "target_date": target_date,
        "source_report_type": REPORT_TYPE,
        "source_report_path": str(monitor_json),
        "metric_contract": METRIC_CONTRACT,
        "orders": report.get("workorder_directives") or [],
        "summary": report.get("workorder_summary") or {},
    }
    workorder_json.write_text(
        json.dumps(workorder_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    workorder_md.write_text(_render_workorder_markdown(report), encoding="utf-8")
    return monitor_json, monitor_md, workorder_json, workorder_md


def _run_once(args: argparse.Namespace) -> dict[str, Any]:
    snapshot_path = Path(args.subscription_snapshot) if args.subscription_snapshot else None
    report = build_report(
        args.target_date,
        pipeline_path=Path(args.pipeline_path) if args.pipeline_path else None,
        threshold_path=Path(args.threshold_path) if args.threshold_path else None,
        subscription_snapshot_path=snapshot_path,
        stale_sec=args.stale_sec,
    )
    if args.write:
        monitor_json, monitor_md, workorder_json, workorder_md = write_report(
            report,
            monitor_only=args.monitor_only,
        )
        print(
            json.dumps(
                {
                    "monitor_json": str(monitor_json),
                    "monitor_md": str(monitor_md),
                    "workorder_json": str(workorder_json) if workorder_json else None,
                    "workorder_md": str(workorder_md) if workorder_md else None,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--pipeline-path")
    parser.add_argument("--threshold-path")
    parser.add_argument("--subscription-snapshot")
    parser.add_argument("--stale-sec", type=float, default=DEFAULT_STALE_SEC)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--monitor-only", action="store_true")
    parser.add_argument("--watch-iterations", type=int, default=1)
    parser.add_argument("--interval-sec", type=float, default=60.0)
    args = parser.parse_args(argv)

    iterations = max(1, int(args.watch_iterations or 1))
    for idx in range(iterations):
        _run_once(args)
        if idx < iterations - 1:
            time.sleep(max(1.0, float(args.interval_sec)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
