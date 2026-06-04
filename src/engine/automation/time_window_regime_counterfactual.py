"""Build source-only time-window regime counterfactual reports."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_TYPE = "time_window_regime_counterfactual"
SCHEMA_VERSION = 1
POST_SELL_DIR = DATA_DIR / "post_sell"
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
MONITOR_SNAPSHOT_DIR = REPORT_DIR / "monitor_snapshots"
REPORT_BASE_DIR = REPORT_DIR / REPORT_TYPE
SYSTEM_METRIC_SAMPLE_PATH = PROJECT_ROOT / "logs" / "system_metric_samples.jsonl"
FORBIDDEN_USES = [
    "real order enablement",
    "threshold mutation",
    "provider change",
    "bot restart",
    "position cap release",
    "entry decision override",
    "exit decision override",
    "broker order submit",
    "time-window hard gate apply",
]
EXCEPTION_BUCKETS = ("wait6579", "recovery", "high_score_buy", "latency_caution", "defensive_price")
SEGMENTS = (
    ("09:00_09:30", "09:00", "09:30"),
    ("09:30_10:00", "09:30", "10:00"),
    ("10:00_10:50", "10:00", "10:50"),
    ("11:00_11:50", "11:00", "11:50"),
    ("12:00_13:00", "12:00", "13:00"),
    ("13:00_14:30", "13:00", "14:30"),
)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_BASE_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def checkpoint_path(target_date: str) -> Path:
    return REPORT_BASE_DIR / "cache" / f"checkpoint_{target_date}.json"


def _cache_path(target_date: str) -> Path:
    return REPORT_BASE_DIR / "cache" / f"date={target_date}" / "part-000001.jsonl"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    yield from iter_jsonl(path)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str) + "\n")
            count += 1
    return count


def _load_cache_rows(target_date: str) -> list[dict[str, Any]]:
    return list(_iter_jsonl(_cache_path(target_date)))


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return None


def _date_range(start: str, end: str) -> list[str]:
    start_d = _parse_date(start)
    end_d = _parse_date(end)
    if start_d is None or end_d is None or start_d > end_d:
        return []
    days: list[str] = []
    cursor = start_d
    while cursor <= end_d:
        days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


def _available_sim_dates(end_date: str, start_date: str | None = None) -> list[str]:
    dates = []
    start_d = _parse_date(start_date) if start_date else None
    end_d = _parse_date(end_date)
    paths = list(POST_SELL_DIR.glob("sim_post_sell_candidates_*.jsonl"))
    paths.extend(POST_SELL_DIR.glob("sim_post_sell_candidates_*.jsonl.gz"))
    for path in sorted(paths):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
        if not match:
            continue
        current = _parse_date(match.group(1))
        if current is None or end_d is None or current > end_d:
            continue
        if start_d is not None and current < start_d:
            continue
        dates.append(current.isoformat())
    return sorted(set(dates))


def _minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"[T\s](\d{1,2}):(\d{2})(?::\d{2})?", text)
    if match is None:
        match = re.search(r"^(\d{1,2}):?(\d{2})(?::?\d{2})?", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def _hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _cutoff_grid() -> list[str]:
    values = list(range(9 * 60 + 5, 11 * 60 + 51, 5))
    values.extend(range(12 * 60, 14 * 60 + 31, 10))
    return [_hhmm(value) for value in sorted(set(values))]


def _entry_time_from_event(event: dict[str, Any], fields: dict[str, Any]) -> tuple[str, str]:
    emitted = str(event.get("emitted_at") or "").strip()
    if emitted:
        return emitted, "entry_event_emitted_at"
    signal = str(fields.get("signal_time") or fields.get("tick_latest_time") or "").strip()
    if signal:
        return signal, "entry_signal_time"
    return "", "entry_time_missing"


def _index_entry_events(target_date: str) -> dict[str, dict[str, dict[str, Any]]]:
    by_candidate: dict[str, dict[str, Any]] = {}
    by_record: dict[str, dict[str, Any]] = {}
    paths = list((THRESHOLD_CYCLE_DIR / f"date={target_date}" / "family=scalp_entry_action_decision_matrix").glob("part-*.jsonl"))
    legacy = THRESHOLD_CYCLE_DIR / f"threshold_events_{target_date}.jsonl"
    legacy = existing_or_gzip_path(legacy)
    if legacy.exists():
        paths.append(legacy)
    for path in paths:
        for event in _iter_jsonl(path):
            fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
            stage = str(event.get("stage") or fields.get("source_stage") or "")
            if "entry" not in stage and not fields.get("entry_adm_candidate_id") and not fields.get("candidate_id"):
                continue
            entry_time, entry_time_source = _entry_time_from_event(event, fields)
            entry_record_id = str(event.get("record_id") or fields.get("record_id") or "").strip()
            indexed = {
                "entry_event_emitted_at": str(event.get("emitted_at") or ""),
                "entry_signal_time": str(fields.get("signal_time") or fields.get("tick_latest_time") or ""),
                "entry_time": entry_time,
                "entry_time_source": entry_time_source,
                "entry_record_id": entry_record_id,
                "entry_stock_code": str(event.get("stock_code") or fields.get("stock_code") or "").strip()[:6],
            }
            for key in (fields.get("entry_adm_candidate_id"), fields.get("candidate_id")):
                safe_key = str(key or "").strip()
                if safe_key and safe_key not in by_candidate:
                    by_candidate[safe_key] = indexed
            if entry_record_id and entry_record_id not in by_record:
                by_record[entry_record_id] = indexed
    return {"candidate": by_candidate, "record": by_record}


def _join_entry_time(row: dict[str, Any], entry_index: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    for key in (row.get("entry_adm_candidate_id"), row.get("candidate_id")):
        safe_key = str(key or "").strip()
        if safe_key and safe_key in entry_index["candidate"]:
            joined = dict(entry_index["candidate"][safe_key])
            joined.update({"entry_join_status": "joined_by_candidate_id", "entry_join_key": safe_key})
            return joined
    record_key = str(row.get("sim_parent_record_id") or "").strip()
    if record_key and record_key in entry_index["record"]:
        joined = dict(entry_index["record"][record_key])
        joined.update({"entry_join_status": "joined_by_record_id", "entry_join_key": record_key})
        return joined
    existing = str(row.get("entry_event_emitted_at") or row.get("entry_signal_time") or "").strip()
    if existing:
        return {
            "entry_event_emitted_at": str(row.get("entry_event_emitted_at") or ""),
            "entry_signal_time": str(row.get("entry_signal_time") or ""),
            "entry_time": existing,
            "entry_time_source": str(row.get("entry_time_source") or "raw_candidate_entry_time"),
            "entry_record_id": str(row.get("entry_record_id") or ""),
            "entry_join_status": str(row.get("entry_join_status") or "raw_candidate_entry_time"),
            "entry_join_key": str(row.get("entry_join_key") or ""),
        }
    return {
        "entry_event_emitted_at": "",
        "entry_signal_time": "",
        "entry_time": "",
        "entry_time_source": "entry_time_unjoined",
        "entry_record_id": "",
        "entry_join_status": "entry_time_unjoined",
        "entry_join_key": "",
    }


def _profit_krw(row: dict[str, Any]) -> int:
    return int(round((_safe_float(row.get("sell_price")) - _safe_float(row.get("buy_price"))) * _safe_float(row.get("buy_qty"))))


def _completed_rows_for_date(target_date: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    entry_index = _index_entry_events(target_date)
    rows: list[dict[str, Any]] = []
    source_quality = Counter()
    for row in _iter_jsonl(POST_SELL_DIR / f"sim_post_sell_candidates_{target_date}.jsonl"):
        if row.get("profit_rate") in (None, ""):
            continue
        joined = _join_entry_time(row, entry_index)
        entry_minutes = _minutes(joined.get("entry_time"))
        if entry_minutes is None:
            source_quality["entry_time_unjoined"] += 1
        else:
            source_quality["entry_time_joined"] += 1
        derived = {
            "row_type": "completed_sim",
            "date": target_date,
            "stock_code": str(row.get("stock_code") or "").strip()[:6],
            "stock_name": row.get("stock_name") or "",
            "post_sell_id": row.get("post_sell_id"),
            "candidate_id": row.get("candidate_id") or row.get("entry_adm_candidate_id") or "",
            "sim_record_id": row.get("sim_record_id") or "",
            "sim_parent_record_id": row.get("sim_parent_record_id") or "",
            "entry_minutes": entry_minutes,
            "entry_time_key": joined.get("entry_time_source"),
            "entry_join_status": joined.get("entry_join_status"),
            "entry_join_key": joined.get("entry_join_key"),
            "sell_time": row.get("sell_time") or "",
            "profit_rate": _safe_float(row.get("profit_rate")),
            "profit_krw": _profit_krw(row),
            "exit_rule": str(row.get("exit_rule") or ""),
            "is_stop": "stop" in str(row.get("exit_rule") or "").lower(),
        }
        rows.append(derived)
    _write_jsonl(_cache_path(target_date), rows)
    return rows, dict(source_quality)


def _source_quality_from_cached_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    source_quality = Counter()
    for row in rows:
        if row.get("entry_minutes") is None:
            source_quality["entry_time_unjoined"] += 1
        else:
            source_quality["entry_time_joined"] += 1
    return dict(source_quality)


def _load_checkpoint_processed_dates(target_date: str) -> set[str]:
    payload = _load_json(checkpoint_path(target_date))
    values = payload.get("processed_dates") if isinstance(payload.get("processed_dates"), list) else []
    return {str(value) for value in values if _parse_date(str(value))}


def _exception_bucket(row: dict[str, Any]) -> str:
    text = json.dumps(row, ensure_ascii=False, default=str).lower()
    score = _safe_float(row.get("ai_score"), 0.0)
    if row.get("recovery_promoted") or row.get("has_recovery_check") or "recovery" in text:
        return "recovery"
    if score >= 75:
        return "high_score_buy"
    if "latency" in text or str(row.get("latency_state") or "").upper() == "CAUTION":
        return "latency_caution"
    if "defensive_price" in text or "below_window" in text:
        return "defensive_price"
    return "wait6579"


def _counterfactual_rows_for_date(target_date: str) -> list[dict[str, Any]]:
    path = MONITOR_SNAPSHOT_DIR / f"wait6579_ev_cohort_{target_date}.json"
    payload = _load_json(path)
    rows: list[dict[str, Any]] = []
    for row in payload.get("rows") or []:
        if not isinstance(row, dict):
            continue
        minutes = _minutes(row.get("signal_time"))
        if minutes is None:
            continue
        bucket = _exception_bucket(row)
        if bucket not in EXCEPTION_BUCKETS:
            bucket = "wait6579"
        rows.append(
            {
                "row_type": "counterfactual_exception",
                "date": target_date,
                "stock_code": str(row.get("stock_code") or "").strip()[:6],
                "stock_name": row.get("stock_name") or "",
                "entry_minutes": minutes,
                "entry_time_key": "wait6579_signal_time",
                "exception_bucket": bucket,
                "expected_ev_pct": _safe_float(row.get("expected_ev_pct")),
                "expected_ev_krw": _safe_int(row.get("expected_ev_krw")),
            }
        )
    return rows


def _load_system_metric_status() -> tuple[bool, str]:
    max_iowait = _safe_float(os.getenv("THRESHOLD_CYCLE_POSTCLOSE_MAX_IOWAIT_PCT"), 35.0)
    max_cpu = _safe_float(os.getenv("THRESHOLD_CYCLE_MAX_CPU_BUSY_PCT"), 95.0)
    min_mem = _safe_float(os.getenv("THRESHOLD_CYCLE_POSTCLOSE_MIN_MEM_AVAILABLE_MB"), 4096.0)
    max_load1 = _safe_float(os.getenv("THRESHOLD_CYCLE_POSTCLOSE_MAX_LOAD1"), 64.0)
    try:
        with SYSTEM_METRIC_SAMPLE_PATH.open("rb") as handle:
            handle.seek(max(0, SYSTEM_METRIC_SAMPLE_PATH.stat().st_size - 65536))
            lines = handle.read().decode("utf-8", errors="ignore").splitlines()
    except Exception:
        return True, "sampler_unavailable"
    last: dict[str, Any] = {}
    for line in reversed(lines[-200:]):
        try:
            last = json.loads(line)
            break
        except Exception:
            continue
    if not last:
        return True, "sampler_empty"
    memory = last.get("memory") or {}
    cpu = last.get("cpu") or {}
    loadavg = last.get("loadavg") or {}
    issues = []
    if _safe_float(cpu.get("iowait_pct")) > max_iowait:
        issues.append("iowait_pct")
    if _safe_float(cpu.get("cpu_busy_pct")) > max_cpu:
        issues.append("cpu_busy_pct")
    if _safe_float(memory.get("mem_available_mb")) < min_mem:
        issues.append("mem_available_mb")
    if _safe_float(loadavg.get("1m")) > max_load1:
        issues.append("load1")
    return not issues, ",".join(issues) if issues else "ok"


class IoGuard:
    def __init__(self, *, max_rows: int, max_seconds: int) -> None:
        self.max_rows = max(1, int(max_rows))
        self.max_seconds = max(1, int(max_seconds))
        self.started = time.monotonic()
        self.rows = 0
        self.paused_reason = ""

    def tick(self, count: int = 1) -> bool:
        self.rows += count
        if self.rows >= self.max_rows:
            self.paused_reason = f"max_rows_reached:{self.rows}>={self.max_rows}"
            return False
        if time.monotonic() - self.started >= self.max_seconds:
            self.paused_reason = f"max_seconds_reached:{self.max_seconds}"
            return False
        ok, reason = _load_system_metric_status()
        if not ok:
            self.paused_reason = f"resource_guard:{reason}"
            return False
        return True


def _aggregate_completed(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    if not count:
        return {
            "completed_trade_count": 0,
            "completed_avg_profit_pct": 0.0,
            "completed_sum_profit_pct": 0.0,
            "completed_profit_krw_sum": 0,
            "hard_soft_stop_rate": 0.0,
        }
    return {
        "completed_trade_count": count,
        "completed_avg_profit_pct": round(sum(_safe_float(row.get("profit_rate")) for row in rows) / count, 4),
        "completed_sum_profit_pct": round(sum(_safe_float(row.get("profit_rate")) for row in rows), 4),
        "completed_profit_krw_sum": int(sum(_safe_int(row.get("profit_krw")) for row in rows)),
        "hard_soft_stop_rate": round(sum(1 for row in rows if row.get("is_stop")) / count, 4),
    }


def _aggregate_counterfactual(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    if not count:
        return {
            "counterfactual_candidate_count": 0,
            "counterfactual_avg_expected_ev_pct": 0.0,
            "counterfactual_expected_ev_krw_sum": 0,
            "exception_bucket_counts": {},
        }
    return {
        "counterfactual_candidate_count": count,
        "counterfactual_avg_expected_ev_pct": round(sum(_safe_float(row.get("expected_ev_pct")) for row in rows) / count, 4),
        "counterfactual_expected_ev_krw_sum": int(sum(_safe_int(row.get("expected_ev_krw")) for row in rows)),
        "exception_bucket_counts": dict(Counter(str(row.get("exception_bucket") or "unknown") for row in rows)),
    }


def _window_policy(completed: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> dict[str, Any]:
    completed_metrics = _aggregate_completed(completed)
    exception_metrics = _aggregate_counterfactual(exceptions)
    return {
        "allow_all_in_window": {
            **completed_metrics,
            "counterfactual_candidate_count": 0,
            "interpretation": "completed sim rows observed in this window; counterfactual EV is not added",
        },
        "block_all_in_window": {
            "blocked_completed_trade_count": completed_metrics["completed_trade_count"],
            "blocked_completed_sum_profit_pct": completed_metrics["completed_sum_profit_pct"],
            "blocked_completed_profit_krw_sum": completed_metrics["completed_profit_krw_sum"],
            "counterfactual_candidate_count": 0,
            "interpretation": "source-only block-all counterfactual; no runtime hard gate authority",
        },
        "block_general_allow_exception_in_window": {
            "blocked_completed_trade_count": completed_metrics["completed_trade_count"],
            "blocked_completed_sum_profit_pct": completed_metrics["completed_sum_profit_pct"],
            "blocked_completed_profit_krw_sum": completed_metrics["completed_profit_krw_sum"],
            **exception_metrics,
            "combined_ev_netting_allowed": False,
            "interpretation": "general completed PnL and exception counterfactual EV are parallel metrics, not summed",
        },
    }


def _rows_in_window(rows: list[dict[str, Any]], start_min: int, end_min: int) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("entry_minutes") is not None and start_min <= int(row["entry_minutes"]) < end_min]


def _build_window_comparisons(completed: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for label, start, end in SEGMENTS:
        start_min = _minutes(start)
        end_min = _minutes(end)
        if start_min is None or end_min is None:
            continue
        comparisons.append(
            {
                "window_type": "segment",
                "window_id": label,
                "start": start,
                "end": end,
                "operator_seed_cutoff": False,
                "policies": _window_policy(
                    _rows_in_window(completed, start_min, end_min),
                    _rows_in_window(exceptions, start_min, end_min),
                ),
            }
        )
    open_min = _minutes("09:00") or 9 * 60
    for cutoff in _cutoff_grid():
        cutoff_min = _minutes(cutoff)
        if cutoff_min is None:
            continue
        comparisons.append(
            {
                "window_type": "cutoff_before",
                "window_id": f"before_{cutoff.replace(':', '')}",
                "start": "09:00",
                "end": cutoff,
                "operator_seed_cutoff": cutoff == "09:30",
                "policies": _window_policy(
                    _rows_in_window(completed, open_min, cutoff_min),
                    _rows_in_window(exceptions, open_min, cutoff_min),
                ),
            }
        )
    return comparisons


def _window_dates(target_date: str, available_dates: list[str]) -> dict[str, list[str]]:
    ordered = [value for value in available_dates if value <= target_date]
    return {
        "daily": [target_date] if target_date in ordered else [],
        "3d": ordered[-3:],
        "5d": ordered[-5:],
        "10d": ordered[-10:],
        "all_available": ordered,
    }


def _data_driven_candidates(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in comparisons:
        policies = item.get("policies") if isinstance(item.get("policies"), dict) else {}
        allow = policies.get("allow_all_in_window") or {}
        exception = policies.get("block_general_allow_exception_in_window") or {}
        if _safe_float(allow.get("completed_avg_profit_pct")) < 0 and _safe_float(exception.get("counterfactual_avg_expected_ev_pct")) > 0:
            candidates.append(
                {
                    "window_id": item.get("window_id"),
                    "window_type": item.get("window_type"),
                    "reason": "negative_completed_pnl_positive_exception_ev",
                    "operator_seed_cutoff": bool(item.get("operator_seed_cutoff")),
                    "completed_avg_profit_pct": allow.get("completed_avg_profit_pct"),
                    "counterfactual_avg_expected_ev_pct": exception.get("counterfactual_avg_expected_ev_pct"),
                }
            )
    return candidates[:20]


def build_time_window_regime_counterfactual_report(
    target_date: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    rolling_days: int | None = None,
    max_rows: int = 200000,
    max_seconds: int = 240,
    resume: bool = False,
) -> dict[str, Any]:
    safe_target = str(target_date).strip()
    safe_end = str(end_date or safe_target).strip()
    clean_policy = clean_baseline_policy()
    available_dates = _available_sim_dates(safe_end, start_date=start_date)
    baseline_excluded_dates: list[str] = []
    if clean_policy.get("enabled", True):
        available_dates, baseline_excluded_dates = filter_allowed_dates(available_dates, clean_policy)
    if rolling_days:
        available_dates = available_dates[-max(1, int(rolling_days)) :]
    guard = IoGuard(max_rows=max_rows, max_seconds=max_seconds)
    cached_resume_dates = _load_checkpoint_processed_dates(safe_target) if resume else set()
    completed_by_date: dict[str, list[dict[str, Any]]] = {}
    exceptions_by_date: dict[str, list[dict[str, Any]]] = {}
    source_quality_counts = Counter()
    processed_dates: list[str] = []
    resume_cache_hits: list[str] = []
    paused = False
    for current_date in available_dates:
        cache_file = _cache_path(current_date)
        if current_date in cached_resume_dates and cache_file.exists():
            completed = _load_cache_rows(current_date)
            quality = _source_quality_from_cached_rows(completed)
            resume_cache_hits.append(current_date)
        else:
            completed, quality = _completed_rows_for_date(current_date)
        exceptions = _counterfactual_rows_for_date(current_date)
        completed_by_date[current_date] = completed
        exceptions_by_date[current_date] = exceptions
        source_quality_counts.update(quality)
        processed_dates.append(current_date)
        if not guard.tick(len(completed) + len(exceptions)):
            paused = True
            break
    window_reports = []
    for window_label, dates in _window_dates(safe_target, processed_dates).items():
        completed_rows = [row for current in dates for row in completed_by_date.get(current, []) if row.get("entry_minutes") is not None]
        exception_rows = [row for current in dates for row in exceptions_by_date.get(current, [])]
        comparisons = _build_window_comparisons(completed_rows, exception_rows)
        window_reports.append(
            {
                "rolling_window": window_label,
                "dates": dates,
                "completed_rows": len(completed_rows),
                "counterfactual_rows": len(exception_rows),
                "window_comparisons": comparisons,
                "data_driven_candidates": _data_driven_candidates(comparisons),
            }
        )
    joined = source_quality_counts.get("entry_time_joined", 0)
    unjoined = source_quality_counts.get("entry_time_unjoined", 0)
    total = joined + unjoined
    status = "partial" if paused else ("warning" if total and unjoined == total else "pass")
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": safe_target,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "time_window_regime_counterfactual_source_only",
        "metric_role": "source_quality_adjusted_ev_pct",
        "window_policy": "rolling_source_only_time_window_regime_counterfactual",
        "sample_floor": "report_only_no_hard_decision",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry time join rate and separate completed/counterfactual metric scopes",
        "forbidden_uses": FORBIDDEN_USES,
        "clean_tuning_baseline": clean_policy,
        "operator_seed_cutoffs": [{"cutoff": "09:30", "operator_seed_cutoff": True, "hard_gate": False}],
        "summary": {
            "status": status,
            "processed_dates": processed_dates,
            "clean_baseline_excluded_dates": baseline_excluded_dates,
            "resume_mode_requested": bool(resume),
            "resume_cache_hits": resume_cache_hits,
            "resume_required": paused,
            "paused_reason": guard.paused_reason or None,
            "completed_rows": sum(len(rows) for rows in completed_by_date.values()),
            "counterfactual_rows": sum(len(rows) for rows in exceptions_by_date.values()),
            "entry_time_join_rate": round(joined / total, 4) if total else 0.0,
            "unjoined_rate": round(unjoined / total, 4) if total else 0.0,
            "sell_time_fallback_rate": 0.0,
            "time_key_distribution": dict(source_quality_counts),
            "completed_counterfactual_netting_allowed": False,
        },
        "rolling_windows": window_reports,
        "source_paths": {
            "post_sell_dir": str(POST_SELL_DIR),
            "threshold_cycle_dir": str(THRESHOLD_CYCLE_DIR),
            "wait6579_dir": str(MONITOR_SNAPSHOT_DIR),
        },
    }
    json_path, md_path = report_paths(safe_target)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    checkpoint = {
        "date": safe_target,
        "status": status,
        "processed_dates": processed_dates,
        "resume_mode_requested": bool(resume),
        "resume_cache_hits": resume_cache_hits,
        "resume_required": paused,
        "paused_reason": guard.paused_reason or None,
        "updated_at": report["generated_at"],
    }
    checkpoint_file = checkpoint_path(safe_target)
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Time Window Regime Counterfactual - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- actual_order_submitted: `{report.get('actual_order_submitted')}`",
        f"- broker_order_forbidden: `{report.get('broker_order_forbidden')}`",
        f"- resume_required: `{summary.get('resume_required')}`",
        f"- entry_time_join_rate: `{summary.get('entry_time_join_rate')}`",
        f"- unjoined_rate: `{summary.get('unjoined_rate')}`",
        f"- completed_counterfactual_netting_allowed: `{summary.get('completed_counterfactual_netting_allowed')}`",
        "",
        "## Rolling Windows",
        "",
    ]
    for window in report.get("rolling_windows") or []:
        if not isinstance(window, dict):
            continue
        lines.append(
            f"- `{window.get('rolling_window')}` dates=`{window.get('dates')}` "
            f"completed=`{window.get('completed_rows')}` counterfactual=`{window.get('counterfactual_rows')}`"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--rolling-days", type=int)
    parser.add_argument("--max-rows", type=int, default=int(os.getenv("THRESHOLD_CYCLE_TIME_WINDOW_REGIME_MAX_ROWS", "200000")))
    parser.add_argument("--max-seconds", type=int, default=int(os.getenv("THRESHOLD_CYCLE_TIME_WINDOW_REGIME_MAX_SECONDS", "240")))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--provider", default="none")
    args = parser.parse_args(argv)
    report = build_time_window_regime_counterfactual_report(
        args.date,
        start_date=args.start_date,
        end_date=args.end_date,
        rolling_days=args.rolling_days,
        max_rows=args.max_rows,
        max_seconds=args.max_seconds,
        resume=args.resume,
    )
    json_path, md_path = report_paths(args.date)
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
