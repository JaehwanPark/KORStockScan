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
WORKORDER_DOC_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "code-improvement-workorders"
)
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENTS_DIR = DATA_DIR / "threshold_cycle"
DEFAULT_DASHBOARD_SNAPSHOT_PATH = (
    DATA_DIR / "runtime" / "kiwoom_ws_snapshot" / "latest.json"
)
DEFAULT_STALE_SEC = 30.0
INCREMENTAL_STATE_SCHEMA_VERSION = "intraday_ws_freshness_incremental_v1"

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

DECISION_STAGE_STALE_BACKOFF_METRIC_CONTRACT = {
    "metric_role": "source_quality_diagnostic",
    "decision_authority": "instrumentation_only_no_runtime_mutation",
    "window_policy": "daily_intraday_operational_by_decision_stage",
    "sample_floor": "at_least_one_explicit_stale_backoff_event",
    "primary_decision_metric": "decision_stage_stale_backoff_count",
    "source_quality_gate": "explicit_scanner_stale_or_backoff_reason",
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


def _source_identity(path: Path) -> dict[str, Any]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return {
            "path": str(actual_path),
            "exists": False,
            "cacheable": False,
            "device": None,
            "inode": None,
            "size_bytes": 0,
        }
    stat = actual_path.stat()
    return {
        "path": str(actual_path),
        "exists": True,
        "cacheable": actual_path.suffix != ".gz",
        "device": int(stat.st_dev),
        "inode": int(stat.st_ino),
        "size_bytes": int(stat.st_size),
    }


def _iter_plain_jsonl_from_offset(
    path: Path,
    *,
    offset: int,
) -> tuple[Iterable[dict[str, Any]], dict[str, int]]:
    progress = {"offset": max(0, int(offset)), "invalid_json_line_count": 0}

    def _rows() -> Iterable[dict[str, Any]]:
        if not path.exists():
            return
        with path.open("rb") as handle:
            handle.seek(progress["offset"])
            while True:
                line_offset = handle.tell()
                raw_line = handle.readline()
                if not raw_line:
                    break
                if not raw_line.endswith(b"\n"):
                    handle.seek(line_offset)
                    break
                progress["offset"] = handle.tell()
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    progress["invalid_json_line_count"] += 1
                    continue
                if isinstance(payload, dict):
                    yield payload

    return _rows(), progress


def _counter_from_mapping(value: Any) -> Counter:
    if not isinstance(value, dict):
        return Counter()
    return Counter({str(key): int(count or 0) for key, count in value.items()})


def _nested_counters_from_mapping(value: Any) -> dict[str, Counter]:
    if not isinstance(value, dict):
        return defaultdict(Counter)
    restored: dict[str, Counter] = defaultdict(Counter)
    for key, counts in value.items():
        restored[str(key)] = _counter_from_mapping(counts)
    return restored


def _load_incremental_state(
    state_path: Path | None,
    *,
    target_date: str,
    stale_ms: float,
    source_identities: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    if state_path is None or not state_path.exists():
        return None, "state_missing"
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "state_invalid"
    if not isinstance(payload, dict):
        return None, "state_invalid"
    if payload.get("schema_version") != INCREMENTAL_STATE_SCHEMA_VERSION:
        return None, "schema_changed"
    if str(payload.get("target_date") or "") != target_date:
        return None, "target_date_changed"
    try:
        cached_stale_ms = float(payload.get("stale_ms") or -1.0)
    except (TypeError, ValueError):
        return None, "state_invalid"
    if cached_stale_ms != float(stale_ms):
        return None, "stale_threshold_changed"
    cached_sources = payload.get("sources")
    if not isinstance(cached_sources, dict):
        return None, "source_state_missing"
    for source_name, identity in source_identities.items():
        cached = cached_sources.get(source_name)
        if not isinstance(cached, dict):
            return None, f"{source_name}_state_missing"
        if not identity.get("cacheable"):
            return None, f"{source_name}_not_cacheable"
        try:
            source_identity_matches = (
                str(cached.get("path") or "") == str(identity.get("path") or "")
                and int(cached.get("device") or -1) == int(identity.get("device") or -2)
                and int(cached.get("inode") or -1) == int(identity.get("inode") or -2)
            )
            cached_offset = int(cached.get("offset") or 0)
        except (TypeError, ValueError):
            return None, f"{source_name}_state_invalid"
        if not source_identity_matches:
            return None, f"{source_name}_replaced"
        if int(identity.get("size_bytes") or 0) < cached_offset:
            return None, f"{source_name}_truncated"
    return payload, "state_reused"


def _write_incremental_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


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


def _counter_rows(
    counter: Counter, *, limit: int = 20, key_name: str = "key"
) -> list[dict[str, Any]]:
    return [
        {key_name: str(key), "count": int(value)}
        for key, value in counter.most_common(limit)
    ]


def _snapshot_generated_at(snapshot: dict[str, Any]) -> datetime | None:
    value = snapshot.get("generated_at")
    if value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=KST)
            return parsed.astimezone(KST)
    epoch = _to_float(snapshot.get("generated_at_epoch"))
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=KST)
    except (OverflowError, OSError, ValueError):
        return None


def _resolve_snapshot(
    requested_path: Path | None,
    *,
    target_date: str,
) -> tuple[Path | None, dict[str, Any], dict[str, Any]]:
    explicit = requested_path is not None
    selected_path = requested_path if explicit else DEFAULT_DASHBOARD_SNAPSHOT_PATH
    payload = _read_json(selected_path)
    generated_at = _snapshot_generated_at(payload)
    provenance = {
        "source": "explicit_subscription_snapshot" if explicit else "none",
        "selected": False,
        "selection_reason": "path_missing",
        "schema_version": str(payload.get("schema_version") or "unknown"),
        "generated_at": generated_at.isoformat() if generated_at else None,
        "subscription_state_available": False,
    }
    if selected_path is None or not selected_path.exists():
        return selected_path, {}, provenance
    if not payload:
        provenance["selection_reason"] = "invalid_or_empty_json"
        return selected_path, {}, provenance
    if explicit:
        provenance.update(
            {
                "selected": True,
                "selection_reason": "explicit_path",
                "subscription_state_available": bool(
                    isinstance(payload.get("rows"), list)
                    or isinstance(payload.get("symbols"), list)
                ),
            }
        )
        return selected_path, payload, provenance
    if str(payload.get("schema_version") or "") != "kiwoom_ws_dashboard_snapshot_v1":
        provenance["selection_reason"] = "unsupported_default_snapshot_schema"
        return selected_path, {}, provenance
    if generated_at is None:
        provenance["selection_reason"] = "default_snapshot_generated_at_missing"
        return selected_path, {}, provenance
    if generated_at.date().isoformat() != target_date:
        provenance["selection_reason"] = "default_snapshot_target_date_mismatch"
        return selected_path, {}, provenance
    provenance.update(
        {
            "source": "same_day_live_dashboard_snapshot_fallback",
            "selected": True,
            "selection_reason": "same_day_schema_match",
            "subscription_state_available": False,
        }
    )
    return selected_path, payload, provenance


def _dashboard_snapshot_rows(
    snapshot: dict[str, Any], *, stale_ms: float
) -> list[dict[str, Any]]:
    stocks = snapshot.get("stocks")
    if not isinstance(stocks, dict):
        return []
    rows: list[dict[str, Any]] = []
    for stock_code, raw in stocks.items():
        if not isinstance(raw, dict):
            continue
        ages = _dictish(raw.get("last_realtime_type_ages_ms"))
        numeric_ages = [
            age for value in ages.values() if (age := _to_float(value)) is not None
        ]
        last_receive_age_ms = min(numeric_ages) if numeric_ages else None
        age_0b_ms = _to_float(raw.get("last_0b_age_ms"))
        if age_0b_ms is None:
            age_0b_ms = _to_float(ages.get("0B"))
        age_0d_ms = _to_float(ages.get("0D"))
        non_trade_fresh = any(
            (age := _to_float(ages.get(realtime_type))) is not None and age < stale_ms
            for realtime_type in ("0D", "0w", "0F")
        )
        if last_receive_age_ms is None:
            freshness_state = "no_tick"
        elif last_receive_age_ms >= stale_ms:
            freshness_state = "stale"
        else:
            freshness_state = "fresh"
        trade_tick_quiet = bool(
            freshness_state == "fresh"
            and non_trade_fresh
            and (age_0b_ms is None or age_0b_ms >= stale_ms)
        )
        rows.append(
            {
                "stock_code": str(stock_code),
                "freshness_state": freshness_state,
                "last_receive_age_sec": (
                    round(last_receive_age_ms / 1000.0, 3)
                    if last_receive_age_ms is not None
                    else None
                ),
                "last_0b_age_sec": (
                    round(age_0b_ms / 1000.0, 3) if age_0b_ms is not None else None
                ),
                "last_0d_age_sec": (
                    round(age_0d_ms / 1000.0, 3) if age_0d_ms is not None else None
                ),
                "last_trade_cum_volume": None,
                "trade_tick_quiet": trade_tick_quiet,
                "repair_recommended": False,
                "repair_reason": "dashboard_snapshot_subscription_state_unavailable",
                "observed_market_route": str(
                    raw.get("last_ws_market_route") or "unknown"
                ),
                "observed_market_suffix": str(raw.get("last_ws_market_suffix") or ""),
                "snapshot_row_authority": "live_dashboard_observation_only",
                "subscription_state_available": False,
            }
        )
    return rows


def _snapshot_rows(
    snapshot: dict[str, Any], *, stale_ms: float
) -> list[dict[str, Any]]:
    rows = snapshot.get("rows")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(snapshot.get("symbols"), list):
        return [row for row in snapshot["symbols"] if isinstance(row, dict)]
    return _dashboard_snapshot_rows(snapshot, stale_ms=stale_ms)


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
        str(row.get("skip_reason") or "").strip(),
        str(row.get("fast_precheck_reason") or "").strip(),
        str(row.get("fast_precheck_observed_reason") or "").strip(),
        str(row.get("scanner_ws_stale_backoff_reason") or "").strip(),
        str(row.get("risk_state") or "").strip(),
        str(row.get("zero_context_blocker") or "").strip(),
    }
    decision_stage_stale_backoff_reasons = {
        "persistent_ws_gap",
        "scanner_ws_stale_backoff_active",
        "stale_ws_snapshot",
        "ws_snapshot_missing_or_zero",
    }
    decision_stage_stale_backoff = bool(
        reason_values & decision_stage_stale_backoff_reasons
    )
    trade_tick_quiet = (
        _boolish(row.get("trade_tick_quiet"))
        or "trade_tick_quiet" in reason_values
        or str(row.get("trade_tick_quiet_reason") or "").strip()
        == "fresh_non_trade_ws_without_fresh_0b"
    )
    repair_recommended = _boolish(row.get("repair_recommended"))
    repair_reason = str(row.get("repair_reason") or "").strip() or "none"
    freshness_state = str(row.get("freshness_state") or "").strip()
    subscription_stale = (
        repair_recommended
        or repair_reason
        in {
            "subscription_no_tick",
            "subscription_stale",
        }
        or freshness_state in {"no_tick", "stale"}
    )

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
    scout_related = "scout" in stage.lower() or "rising_missed" in json.dumps(
        row, ensure_ascii=False
    )

    return {
        "stage": stage,
        "stock_code": str(row.get("stock_code") or ""),
        "stock_name": str(row.get("stock_name") or ""),
        "time_bucket": _time_bucket(row),
        "trade_tick_quiet": bool(trade_tick_quiet),
        "subscription_stale": bool(subscription_stale),
        "decision_stage_stale_backoff": decision_stage_stale_backoff,
        "both_ws_stale": bool(both_stale),
        "fresh_0d_stale_0b": bool(quiet_by_age),
        "provider_none": _row_provider_none(row),
        "submit_related": submit_related,
        "scout_related": scout_related,
        "ws_age_observed": any(
            _to_float(row.get(key)) is not None for key in WS_AGE_FIELDS_MS
        )
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
    observed_route_counts: Counter = Counter()
    observed_suffix_counts: Counter = Counter()
    quiet_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    multi_route_rows: list[dict[str, Any]] = []
    subscription_stale_like_rows: list[dict[str, Any]] = []
    observed_stale_like_rows: list[dict[str, Any]] = []
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
        observed_route = str(row.get("observed_market_route") or "").strip()
        if observed_route:
            observed_route_counts[observed_route] += 1
        observed_suffix = str(row.get("observed_market_suffix") or "").strip()
        if row.get("observed_market_suffix") is not None:
            observed_suffix_counts[observed_suffix or "KRX"] += 1
        if _boolish(row.get("multi_route_registered")):
            multi_route_rows.append(row)
        if _boolish(row.get("trade_tick_quiet")):
            quiet_rows.append(row)
        if _boolish(row.get("repair_recommended")):
            repair_rows.append(row)
        if state in {"stale", "no_tick"}:
            observed_stale_like_rows.append(row)
            if row.get("subscription_state_available") is not False:
                subscription_stale_like_rows.append(row)
    total = len(rows)
    stale_like = len(subscription_stale_like_rows)
    return {
        "row_count": total,
        "freshness_state_counts": dict(states),
        "repair_reason_counts": dict(repair_reasons),
        "subscription_stale_like_count": stale_like,
        "subscription_stale_like_rate_pct": _rate_pct(stale_like, total),
        "observed_stale_like_count": len(observed_stale_like_rows),
        "observed_stale_like_rate_pct": _rate_pct(len(observed_stale_like_rows), total),
        "trade_tick_quiet_count": len(quiet_rows),
        "trade_tick_quiet_rate_pct": _rate_pct(len(quiet_rows), total),
        "repair_recommended_count": len(repair_rows),
        "registered_item_quota_units": quota_units,
        "registered_route_counts": dict(route_counts),
        "registered_market_suffix_counts": dict(suffix_counts),
        "observed_market_route_counts": dict(observed_route_counts),
        "observed_market_suffix_counts": dict(observed_suffix_counts),
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


def _build_workorders(
    summary: dict[str, Any], *, target_date: str
) -> list[dict[str, Any]]:
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
    if counts.get("subscription_stale", 0) or snapshot.get(
        "repair_recommended_count", 0
    ):
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
    if counts.get("decision_stage_stale_backoff", 0):
        orders.append(
            {
                **base,
                "order_id": "order_ws_decision_stage_stale_backoff_attribution",
                "title": "WS decision-stage stale backoff attribution",
                "priority": 1,
                "intent": (
                    "Attribute explicit scanner stale/backoff rows to subscription repair, "
                    "decision-stage freshness, and watchlist eviction timing without weakening "
                    "the stale submit boundary."
                ),
                "evidence": [
                    "decision_stage_stale_backoff_count="
                    f"{counts.get('decision_stage_stale_backoff', 0)}"
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/sniper.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q "
                    "src/tests/test_kiwoom_websocket.py "
                    "src/tests/test_intraday_ws_freshness_monitor.py",
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
    orders.sort(
        key=lambda item: (int(item.get("priority", 99)), str(item.get("order_id")))
    )
    return orders


def build_report(
    target_date: str | None = None,
    *,
    pipeline_path: Path | None = None,
    threshold_path: Path | None = None,
    subscription_snapshot_path: Path | None = None,
    stale_sec: float = DEFAULT_STALE_SEC,
    generated_at: str | None = None,
    incremental_state_path: Path | None = None,
) -> dict[str, Any]:
    target_date = target_date or date.today().isoformat()
    stale_ms = float(stale_sec) * 1000.0
    paths = _source_paths(target_date)
    if pipeline_path is not None:
        paths["pipeline_events"] = pipeline_path
    if threshold_path is not None:
        paths["threshold_events"] = threshold_path

    source_missing = [name for name, path in paths.items() if not path.exists()]
    source_identities = {
        source_name: _source_identity(path) for source_name, path in paths.items()
    }
    cached_state, incremental_state_reason = _load_incremental_state(
        incremental_state_path,
        target_date=target_date,
        stale_ms=stale_ms,
        source_identities=source_identities,
    )
    try:
        row_count_by_source = _counter_from_mapping(
            (cached_state or {}).get("row_count_by_source")
        )
        counts = _counter_from_mapping((cached_state or {}).get("counts"))
        stage_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("stage_counts")
        )
        time_bucket_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("time_bucket_counts")
        )
        symbol_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("symbol_counts")
        )
        total_events = int((cached_state or {}).get("total_events") or 0)
    except (TypeError, ValueError):
        cached_state = None
        incremental_state_reason = "aggregate_state_invalid"
        row_count_by_source = Counter()
        counts = Counter()
        stage_counts = defaultdict(Counter)
        time_bucket_counts = defaultdict(Counter)
        symbol_counts = defaultdict(Counter)
        total_events = 0
    appended_event_count = 0
    invalid_json_line_count = 0
    source_offsets: dict[str, dict[str, Any]] = {}
    for source_name, path in paths.items():
        identity = source_identities[source_name]
        cached_source = (
            (cached_state or {}).get("sources", {}).get(source_name, {})
            if cached_state
            else {}
        )
        start_offset = int(cached_source.get("offset") or 0)
        actual_path = Path(str(identity.get("path") or path))
        if identity.get("cacheable"):
            source_rows, progress = _iter_plain_jsonl_from_offset(
                actual_path,
                offset=start_offset,
            )
        else:
            source_rows = _iter_jsonl_rows(path)
            progress = {"offset": 0, "invalid_json_line_count": 0}
        source_appended_count = 0
        for raw in source_rows:
            row_count_by_source[source_name] += 1
            total_events += 1
            appended_event_count += 1
            source_appended_count += 1
            item = _pipeline_event_class(_flatten_event(raw), stale_ms=stale_ms)
            for key in (
                "trade_tick_quiet",
                "subscription_stale",
                "decision_stage_stale_backoff",
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
            for key in (
                "trade_tick_quiet",
                "subscription_stale",
                "decision_stage_stale_backoff",
                "both_ws_stale",
                "provider_none",
            ):
                if item.get(key):
                    stage_counts[key][stage] += 1
                    time_bucket_counts[key][bucket] += 1
                    if code:
                        symbol_counts[key][code] += 1
        invalid_json_line_count += int(progress["invalid_json_line_count"])
        end_identity = _source_identity(actual_path)
        source_identity_stable = bool(
            identity.get("device") == end_identity.get("device")
            and identity.get("inode") == end_identity.get("inode")
        )
        source_offsets[source_name] = {
            **(end_identity if source_identity_stable else identity),
            "offset": int(progress["offset"]),
            "start_offset": start_offset,
            "appended_event_count": source_appended_count,
            "source_identity_stable_during_scan": source_identity_stable,
        }

    incremental_state_persisted = bool(
        incremental_state_path is not None
        and all(identity.get("cacheable") for identity in source_identities.values())
        and all(
            source.get("source_identity_stable_during_scan")
            for source in source_offsets.values()
        )
    )
    if incremental_state_persisted and incremental_state_path is not None:
        _write_incremental_state(
            incremental_state_path,
            {
                "schema_version": INCREMENTAL_STATE_SCHEMA_VERSION,
                "target_date": target_date,
                "stale_ms": stale_ms,
                "sources": {
                    source_name: {
                        "path": source.get("path"),
                        "device": source.get("device"),
                        "inode": source.get("inode"),
                        "offset": source.get("offset"),
                    }
                    for source_name, source in source_offsets.items()
                },
                "row_count_by_source": dict(row_count_by_source),
                "counts": dict(counts),
                "stage_counts": {
                    key: dict(counter) for key, counter in stage_counts.items()
                },
                "time_bucket_counts": {
                    key: dict(counter) for key, counter in time_bucket_counts.items()
                },
                "symbol_counts": {
                    key: dict(counter) for key, counter in symbol_counts.items()
                },
                "total_events": total_events,
            },
        )

    (
        resolved_snapshot_path,
        snapshot_payload,
        snapshot_provenance,
    ) = _resolve_snapshot(subscription_snapshot_path, target_date=target_date)
    snapshot_rows = _snapshot_rows(snapshot_payload, stale_ms=stale_ms)
    snapshot = _snapshot_summary(snapshot_rows)

    summary = {
        "target_date": target_date,
        "generated_at": generated_at or datetime.now(tz=KST).isoformat(),
        "report_type": REPORT_TYPE,
        "metric_contract": METRIC_CONTRACT,
        "decision_stage_stale_backoff_metric_contract": (
            DECISION_STAGE_STALE_BACKOFF_METRIC_CONTRACT
        ),
        "source_paths": {name: str(path) for name, path in paths.items()},
        "source_missing": source_missing,
        "input_processing": {
            "mode": (
                "incremental_streaming_aggregation"
                if cached_state is not None
                else "full_streaming_rebuild"
            ),
            "memory_bounded_streaming": True,
            "full_event_list_materialized": False,
            "aggregated_event_count": total_events,
            "appended_event_count": appended_event_count,
            "invalid_json_line_count": invalid_json_line_count,
            "incremental_state_reason": incremental_state_reason,
            "incremental_state_path": (
                str(incremental_state_path) if incremental_state_path else None
            ),
            "incremental_state_persisted": incremental_state_persisted,
            "source_offsets": source_offsets,
        },
        "subscription_snapshot_path": (
            str(resolved_snapshot_path) if resolved_snapshot_path else None
        ),
        "subscription_snapshot_provenance": snapshot_provenance,
        "row_count_by_source": dict(row_count_by_source),
        "pipeline_counts": dict(counts),
        "pipeline_event_count": total_events,
        "pipeline_rates": {
            "trade_tick_quiet_rate_pct": _rate_pct(
                int(counts.get("trade_tick_quiet", 0)), total_events
            ),
            "subscription_stale_rate_pct": _rate_pct(
                int(counts.get("subscription_stale", 0)), total_events
            ),
            "decision_stage_stale_backoff_rate_pct": _rate_pct(
                int(counts.get("decision_stage_stale_backoff", 0)), total_events
            ),
            "both_ws_stale_rate_pct": _rate_pct(
                int(counts.get("both_ws_stale", 0)), total_events
            ),
            "provider_none_rate_pct": _rate_pct(
                int(counts.get("provider_none", 0)), total_events
            ),
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
            if item.get("decision") == "implement_now"
            and item.get("runtime_effect") is False
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
    workorder_count = (report.get("workorder_summary") or {}).get(
        "selected_order_count", 0
    )
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
            f"- input_processing: `{report.get('input_processing')}`",
            f"- pipeline_counts: `{report.get('pipeline_counts')}`",
            f"- pipeline_rates: `{report.get('pipeline_rates')}`",
            "- subscription_snapshot_path: "
            f"`{report.get('subscription_snapshot_path')}`",
            "- subscription_snapshot_provenance: "
            f"`{report.get('subscription_snapshot_provenance')}`",
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


def write_report(
    report: dict[str, Any], *, monitor_only: bool = False
) -> tuple[Path, Path, Path | None, Path | None]:
    target_date = str(report.get("target_date") or date.today().isoformat())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    monitor_json = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json"
    monitor_md = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md"

    monitor_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monitor_md.write_text(_render_monitor_markdown(report), encoding="utf-8")
    if monitor_only:
        return monitor_json, monitor_md, None, None

    WORKORDER_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    WORKORDER_DOC_DIR.mkdir(parents=True, exist_ok=True)
    workorder_json = (
        WORKORDER_REPORT_DIR / f"intraday_ws_freshness_workorder_{target_date}.json"
    )
    workorder_md = (
        WORKORDER_DOC_DIR / f"intraday_ws_freshness_workorder_{target_date}.md"
    )
    workorder_payload = {
        "target_date": target_date,
        "source_report_type": REPORT_TYPE,
        "source_report_path": str(monitor_json),
        "metric_contract": METRIC_CONTRACT,
        "orders": report.get("workorder_directives") or [],
        "summary": report.get("workorder_summary") or {},
    }
    workorder_json.write_text(
        json.dumps(workorder_payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    workorder_md.write_text(_render_workorder_markdown(report), encoding="utf-8")
    return monitor_json, monitor_md, workorder_json, workorder_md


def _run_once(args: argparse.Namespace) -> dict[str, Any]:
    snapshot_path = (
        Path(args.subscription_snapshot) if args.subscription_snapshot else None
    )
    report = build_report(
        args.target_date,
        pipeline_path=Path(args.pipeline_path) if args.pipeline_path else None,
        threshold_path=Path(args.threshold_path) if args.threshold_path else None,
        subscription_snapshot_path=snapshot_path,
        stale_sec=args.stale_sec,
        incremental_state_path=(
            Path(args.incremental_state_path) if args.incremental_state_path else None
        ),
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
    parser.add_argument("--incremental-state-path")
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
