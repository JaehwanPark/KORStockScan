"""Independent, bounded first-BUY-submit delay evidence and policy.

This owner never changes the entry decision, split shape, cancel wait, or
numeric price. A candidate without paired executable/cost evidence remains
diagnostic and the runtime retains the zero-second incumbent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

KST = timezone(timedelta(hours=9))
REPORT_SCHEMA = "pre_submit_delay_tuning_v1"
POLICY_SCHEMA = "pre_submit_delay_policy_v1"
FAMILY = "pre_submit_delay"
DELAYS_SEC = (0.0, 30.0, 60.0, 120.0, 180.0)
SOURCE_STAGES = frozenset({
    "pre_submit_delay_committed",
    "pre_submit_delay_quote_observed",
    "pre_submit_delay_intent_terminal",
})
REPORT_DIR = DATA_DIR / "report" / "pre_submit_delay_tuning"
POLICY_DIR = DATA_DIR / "threshold_cycle" / "pre_submit_delay_policy"


def _digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, sort_keys=True, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def report_path(target_date: str) -> Path:
    return REPORT_DIR / f"pre_submit_delay_tuning_{target_date}.json"


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"pre_submit_delay_policy_{target_date}.json"


def _source_rows(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    directory = DATA_DIR / "threshold_cycle" / f"date={target_date}" / f"family={FAMILY}"
    paths = sorted(directory.glob("part-execution-*.jsonl"))
    rows: list[dict[str, Any]] = []
    source_hash = hashlib.sha256()
    total_bytes = 0
    seen: set[str] = set()
    for path in paths:
        before = path.stat()
        if path.is_symlink() or before.st_size > 64 * 1024 * 1024:
            raise ValueError("delay_partition_invalid_or_unbounded")
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                total_bytes += len(line.encode())
                if total_bytes > 64 * 1024 * 1024 or not line.endswith("\n"):
                    raise ValueError("delay_partition_decoded_budget_or_partial_line")
                source_hash.update(line.encode())
                row = json.loads(line)
                if row.get("emitted_date") != target_date or row.get("family") != FAMILY:
                    raise ValueError("delay_partition_date_or_family_mismatch")
                if row.get("stage") not in SOURCE_STAGES:
                    continue
                identity = str(row.get("execution_source_event_sha256") or "")
                if len(identity) != 64:
                    raise ValueError("delay_partition_identity_missing")
                if identity not in seen:
                    rows.append(row)
                    seen.add(identity)
        after = path.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino, after.st_size, after.st_mtime_ns
        ):
            raise ValueError("delay_partition_changed_during_read")
    if paths != sorted(directory.glob("part-execution-*.jsonl")):
        raise ValueError("delay_partition_inventory_changed")
    return rows, {
        "status": "ready" if paths else "source_gap",
        "first_blocker": None if paths else "prospective_delay_observations_missing",
        "paths": [str(path) for path in paths],
        "bytes_read": total_bytes,
        "sha256": source_hash.hexdigest() if paths else None,
    }


def _number(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def decision_type_snapshot(*, price: Any, ask: Any, bid: Any,
                           venue: Any, session: Any) -> dict[str, Any]:
    """Freeze only source-known execution features at intent time.

    A spread alone is not the machine's liquidity score. Missing volatility
    and market cap stay unknown rather than being backfilled from later data.
    """
    from src.trading.order.tick_utils import get_tick_size

    observed_price = _number(price)
    observed_ask = _number(ask)
    observed_bid = _number(bid)
    tick_pct = None
    if observed_price is not None and observed_price > 0:
        tick_pct = get_tick_size(observed_price) / observed_price * 100
    tick_band = (
        "UNKNOWN" if tick_pct is None else
        "LT_5BP" if tick_pct < .05 else
        "5_TO_10BP" if tick_pct < .10 else "GE_10BP"
    )
    spread_bp = None
    if (observed_ask is not None and observed_bid is not None
            and observed_ask >= observed_bid > 0):
        spread_bp = (observed_ask - observed_bid) / observed_bid * 10000
    venue_name = str(venue or "UNKNOWN").strip().upper()
    session_name = str(session or "UNKNOWN").strip().upper()
    return {
        "schema": "pre_submit_delay_decision_type_v1",
        "venue": venue_name, "session_bucket": session_name,
        "price_tick_band": tick_band, "tick_pct": tick_pct,
        "spread_bp": spread_bp,
        "liquidity_band": "UNKNOWN", "volatility_band": "UNKNOWN",
        "market_cap_krw": None,
        "type_key": "|".join((venue_name, session_name, tick_band)),
    }


def _validated_candidate(policy: dict[str, Any], report: dict[str, Any],
                         *, scope_key: str | None = None,
                         type_key: str | None = None) -> bool:
    """Require each selected arm to exist on its own paired denominator."""
    if type_key is not None:
        selected_policy = (policy.get("type_policies") or {}).get(type_key)
        source_rows = [row for row in report.get("type_census", [])
                       if isinstance(row, dict) and row.get("type_key") == type_key]
        if (len(source_rows) != 1 or not isinstance(selected_policy, dict)
                or (report.get("selected_type_policies") or {}).get(type_key)
                != selected_policy.get("selected_delay_sec")):
            return False
        grid = source_rows[0].get("candidate_grid") or []
    elif scope_key is not None:
        selected_policy = (policy.get("scope_policies") or {}).get(scope_key)
        source_rows = [row for row in report.get("scope_census", [])
                       if isinstance(row, dict) and row.get("scope_key") == scope_key]
        if (len(source_rows) != 1 or not isinstance(selected_policy, dict)
                or (report.get("selected_scope_policies") or {}).get(scope_key)
                != selected_policy.get("selected_delay_sec")):
            return False
        grid = source_rows[0].get("candidate_grid") or []
    else:
        selected_policy = policy
        grid = report.get("candidate_grid", [])
    selected = _number(selected_policy.get("selected_delay_sec"))
    if selected == 0:
        return True
    if selected not in DELAYS_SEC or report.get("status") != "validated_edge":
        return False
    if report.get("model_status") != "validated" or selected_policy.get("model_status") != "validated":
        return False
    if (report.get("source") or {}).get("status") != "ready":
        return False
    rows = [
        row for row in grid
        if isinstance(row, dict) and _number(row.get("delay_sec")) == selected
    ]
    if len(rows) != 1 or rows[0].get("candidate_passed") is not True:
        return False
    row = rows[0]
    return bool(
        policy.get("runtime_apply_allowed") is True
        and selected_policy.get("runtime_apply_allowed") is True
        and selected_policy.get("selection_status") == "selected"
        and (_number(selected_policy.get("paired_net_ev_delta_pct")) or 0) > 0
        and _number(selected_policy.get("holdout_net_ev_delta_pct")) is not None
        and _number(selected_policy.get("holdout_net_ev_delta_pct")) >= 0
        and _number(row.get("paired_net_ev_delta_pct")) == _number(selected_policy.get("paired_net_ev_delta_pct"))
        and _number(row.get("holdout_net_ev_delta_pct")) == _number(selected_policy.get("holdout_net_ev_delta_pct"))
        and (_number(row.get("source_valid_attempt_count")) or 0) >= 10
        and (_number(row.get("holdout_attempt_count")) or 0) >= 3
        and (_number(report.get("terminal_observation_count")) or 0) >= 10
        and _number(row.get("model_fill_error")) is not None
    )


def _existing_quote_census(target_date: str) -> dict[str, Any]:
    """Count existing post-submit BBO fields once; never infer a fill from them.

    The legacy pipeline has scattered quote events, but no guaranteed sample
    at each delay horizon. This bounded read distinguishes that partial source
    from a complete absence of market data without promoting a counterfactual.
    """
    directory = DATA_DIR / "threshold_cycle" / f"date={target_date}" / "family=dynamic_entry_price_resolver"
    orders: dict[str, list[datetime]] = defaultdict(list)
    partition_bytes = 0
    for path in sorted(directory.glob("part-execution-*.jsonl")):
        size = path.stat().st_size
        partition_bytes += size
        if path.is_symlink() or partition_bytes > 64 * 1024 * 1024:
            return {"status": "partition_unbounded", "submit_count": 0}
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event.get("stage") == "order_leg_sent" and event.get("emitted_date") == target_date:
                    orders[str(event.get("stock_code") or "")].append(
                        datetime.fromisoformat(event["emitted_at"])
                    )
    count = sum(map(len, orders.values()))
    if not count:
        return {"status": "no_submitted_orders", "submit_count": 0}
    raw_path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if not raw_path.is_file() or raw_path.is_symlink():
        return {"status": "raw_pipeline_missing", "submit_count": count}
    before = raw_path.stat()
    # This is a field-presence diagnostic, not the economic source. Read a
    # bounded tail once instead of scanning a multi-GB live pipeline during
    # the postclose critical path. Absence in this window is never absence
    # from the full trading day.
    max_read_bytes = 64 * 1024 * 1024
    read_start = max(0, before.st_size - max_read_bytes)
    cache_path = REPORT_DIR / f"existing_quote_census_{target_date}.json"
    cache_key = _digest({
        "orders": {code: [value.isoformat() for value in times] for code, times in sorted(orders.items())},
        "raw_inode": before.st_ino,
        "raw_size": before.st_size,
        "raw_mtime_ns": before.st_mtime_ns,
        "read_start": read_start,
        "horizons": DELAYS_SEC,
    })
    if cache_path.is_file() and cache_path.stat().st_size <= 1024 * 1024:
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("cache_key") == cache_key and not cached.get("raw_changed_during_read"):
                return {**cached, "cache_hit": True}
        except (OSError, ValueError, AttributeError):
            pass
    markers = tuple(f'"{code}"'.encode() for code in orders if code)
    field_count = Counter()
    horizon_count = Counter()
    field_names = (
        "best_ask_at_submit", "fresh_best_ask", "market_data_effective_best_ask",
        "executable_best_ask", "holding_context_best_ask",
        "entry_split_order_probe_submit_best_ask",
    )
    with raw_path.open("rb") as handle:
        if read_start:
            handle.seek(read_start)
            handle.readline()  # discard the partial first line
        while handle.tell() < before.st_size:
            line = handle.readline()
            if not any(marker in line for marker in markers):
                continue
            try:
                event = json.loads(line)
                code = str(event.get("stock_code") or "")
                if code not in orders:
                    continue
                observed_at = datetime.fromisoformat(event["emitted_at"])
                fields = event.get("fields") or {}
                if not any(_number(fields.get(key)) for key in field_names):
                    continue
            except (ValueError, TypeError, KeyError):
                continue
            for submitted_at in orders[code]:
                elapsed = (observed_at - submitted_at).total_seconds()
                if not -5 <= elapsed <= 183:
                    continue
                field_count[code] += 1
                for horizon in DELAYS_SEC:
                    if abs(elapsed - horizon) <= 3:
                        horizon_count[(code, horizon)] += 1
                break
    after = raw_path.stat()
    changed = (before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_ino, after.st_size, after.st_mtime_ns
    )
    result = {
        "status": "bounded_tail_field_presence_only",
        "submit_count": count,
        "stocks_with_quote_fields": len(field_count),
        "horizon_stock_count": {
            f"{horizon:g}": len({code for code, observed in horizon_count if observed == horizon})
            for horizon in DELAYS_SEC
        },
        "raw_bytes_read": before.st_size - read_start,
        "raw_window_start_offset": read_start,
        "whole_day_absence_not_established": True,
        "raw_inode": before.st_ino,
        "raw_mtime_ns_at_start": before.st_mtime_ns,
        "raw_changed_during_read": changed,
        "not_a_fill_or_route_validity_claim": True,
        "cache_key": cache_key,
        "cache_hit": False,
    }
    if not changed:
        _atomic_json(cache_path, result)
    return result


def build_report(
    target_date: str, *, effective_date: str, write: bool = True
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    if date.fromisoformat(effective_date) <= date.fromisoformat(target_date):
        raise ValueError("delay_effective_date_not_after_source_date")
    started = time.monotonic()
    rows, source = _source_rows(target_date)
    existing_quote_census = _existing_quote_census(target_date)
    commits: dict[str, dict[str, Any]] = {}
    samples: dict[str, dict[float, dict[str, Any]]] = defaultdict(dict)
    terminals: dict[str, dict[str, Any]] = {}
    invalid = Counter()
    for row in rows:
        fields = row.get("fields")
        if not isinstance(fields, dict):
            invalid["fields_missing"] += 1
            continue
        attempt = str(fields.get("delay_intent_id") or "")
        if not attempt:
            invalid["attempt_identity_missing"] += 1
            continue
        stage = row["stage"]
        if stage == "pre_submit_delay_committed":
            if attempt in commits and commits[attempt] != fields:
                invalid["commit_conflict"] += 1
            else:
                commits[attempt] = fields
        elif stage == "pre_submit_delay_quote_observed":
            second = _number(fields.get("target_delay_sec"))
            if second not in DELAYS_SEC or second in samples[attempt]:
                invalid["sample_duplicate_or_horizon_invalid"] += 1
            else:
                samples[attempt][second] = fields
        else:
            if attempt in terminals and terminals[attempt] != fields:
                invalid["terminal_conflict"] += 1
            else:
                terminals[attempt] = fields

    eligible = [
        key for key, commit in commits.items()
        if str(commit.get("entry_action") or "") == "ENTER_NOW"
        and str(commit.get("auxiliary_effective_action") or "") in {"PASS", "CAUTION"}
        and (_number(commit.get("planned_qty")) or 0) > 0
        and str(commit.get("owner") or "") == "main_scalping"
    ]
    type_by_attempt = {}
    for key in eligible:
        observed = commits[key].get("delay_decision_type")
        if isinstance(observed, str) and len(observed) <= 4096:
            try:
                observed = json.loads(observed)
            except ValueError:
                observed = None
        if isinstance(observed, dict) and observed.get("schema") == "pre_submit_delay_decision_type_v1":
            expected = "|".join(str(observed.get(part) or "UNKNOWN") for part in (
                "venue", "session_bucket", "price_tick_band"
            ))
            type_by_attempt[key] = expected if observed.get("type_key") == expected else "UNKNOWN"
        else:
            type_by_attempt[key] = "UNKNOWN"
    missing = Counter()
    diagnostic = []
    valid_asks_by_type: dict[tuple[str, float], list[float]] = defaultdict(list)
    for second in DELAYS_SEC:
        comparable = []
        for key in eligible:
            row = samples.get(key, {}).get(second)
            if not row:
                missing[f"{second:g}s_missing"] += 1
                continue
            ask = _number(row.get("ask_price"))
            depth = _number(row.get("ask_qty"))
            if (
                ask is None or ask <= 0 or depth is None or depth <= 0
                or str(row.get("quote_valid") or "").lower() != "true"
                or row.get("route") != commits[key].get("route")
            ):
                missing[f"{second:g}s_source_invalid"] += 1
                continue
            comparable.append((key, ask, depth))
            valid_asks_by_type[(type_by_attempt[key], second)].append(ask)
        diagnostic.append({
            "delay_sec": second,
            "source_valid_attempt_count": len(comparable),
            "mean_observed_ask": (
                round(sum(item[1] for item in comparable) / len(comparable), 4)
                if comparable else None
            ),
            "paired_net_ev_pct": None,
            "paired_net_ev_delta_pct": None,
            "holdout_net_ev_delta_pct": None,
            "holdout_attempt_count": None,
            "model_fill_error": None,
            "winner_retention": None,
            "candidate_passed": False,
        })
    type_counts = Counter(type_by_attempt.values())
    scope_by_attempt = {key: "|".join(type_by_attempt[key].split("|")[:2])
                        if type_by_attempt[key] != "UNKNOWN" else "UNKNOWN"
                        for key in eligible}
    scope_counts = Counter(scope_by_attempt.values())
    valid_asks_by_scope: dict[tuple[str, float], list[float]] = defaultdict(list)
    for (type_key, second), asks in valid_asks_by_type.items():
        scope = "|".join(type_key.split("|")[:2]) if type_key != "UNKNOWN" else "UNKNOWN"
        valid_asks_by_scope[(scope, second)].extend(asks)
    scope_diagnostic = [
        {
            "scope_key": scope_key, "eligible_attempt_count": scope_counts[scope_key],
            "candidate_grid": [
                {"delay_sec": second,
                 "source_valid_attempt_count": len(valid_asks_by_scope[(scope_key, second)]),
                 "paired_net_ev_delta_pct": None,
                 "holdout_net_ev_delta_pct": None,
                 "candidate_passed": False}
                for second in DELAYS_SEC
            ],
            "selection_status": "root_zero_carry_source_gap",
        } for scope_key in sorted(scope_counts)
    ]
    type_diagnostic = [
        {
            "type_key": type_key, "eligible_attempt_count": type_counts[type_key],
            "candidate_grid": [
                {
                    "delay_sec": second,
                    "source_valid_attempt_count": len(valid_asks_by_type[(type_key, second)]),
                    "mean_observed_ask": (
                        round(sum(valid_asks_by_type[(type_key, second)])
                              / len(valid_asks_by_type[(type_key, second)]), 4)
                        if valid_asks_by_type[(type_key, second)] else None
                    ),
                    "paired_net_ev_delta_pct": None,
                    "holdout_net_ev_delta_pct": None,
                    "candidate_passed": False,
                } for second in DELAYS_SEC
            ],
            "selection_status": "parent_zero_carry_source_gap",
        } for type_key in sorted(type_counts)
    ]
    # Ask improvements alone are not executable fills. Until full/partial/no-fill
    # and completed-cost calibration are joined on this same denominator, every
    # candidate EV remains null and the independent zero-second policy carries.
    if source["status"] == "source_gap":
        blocker = (
            "exact_commit_and_horizon_quote_binding_missing"
            if existing_quote_census.get("submit_count", 0) > 0
            else source["first_blocker"]
        )
    elif not commits:
        blocker = "exact_committed_intent_missing"
    elif not eligible:
        blocker = "eligible_enter_now_auxiliary_pass_intent_missing"
    elif not any(row["source_valid_attempt_count"] for row in diagnostic[1:]):
        blocker = "fresh_route_bound_horizon_quote_missing"
    elif not terminals:
        blocker = "exact_submit_terminal_receipt_missing"
    else:
        blocker = "paired_fill_terminal_cost_model_not_validated"
    report = {
        "schema": REPORT_SCHEMA,
        "source_date": target_date,
        "effective_date": effective_date,
        "generated_at": datetime.now(KST).isoformat(),
        "analysis_axis": FAMILY,
        "fixed_axes": ["machine", "auxiliary_ai", "entry_split"],
        "source": source,
        "existing_quote_census": existing_quote_census,
        "committed_attempt_count": len(commits),
        "eligible_attempt_count": len(eligible),
        "terminal_observation_count": len(terminals),
        "invalid_counts": dict(invalid),
        "missing_counts": dict(missing),
        "candidate_grid": diagnostic,
        "decision_type_schema": "pre_submit_delay_decision_type_v1",
        "type_census": type_diagnostic,
        "scope_census": scope_diagnostic,
        "selected_type_policies": {row["type_key"]: 0.0 for row in type_diagnostic},
        "selected_scope_policies": {row["scope_key"]: 0.0 for row in scope_diagnostic},
        "model_status": "not_validated",
        "metric_role": "primary_ev",
        "decision_authority": "next_preopen_bounded_pre_submit_delay_policy",
        "window_policy": "same_frozen_intent_first_submit_delay_0_30_60_120_180s",
        "sample_floor": {"paired_attempts": 10, "holdout_attempts": 3},
        "primary_decision_metric": "paired_completed_cost_net_ev_delta_pct",
        "source_quality_gate": "exact_intent_route_fresh_depth_fill_terminal_cost_and_holdout",
        "forbidden_uses": ["entry_action", "split_shape", "price_override",
                           "quantity_increase", "safety_guard_bypass"],
        "incumbent_net_ev_pct": None,
        "selected_delay_sec": 0.0,
        "status": "source_gap",
        "first_blocker": blocker,
        "realized_pnl_not_double_counted": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "elapsed_sec": round(time.monotonic() - started, 4),
    }
    policy = {
        "schema": POLICY_SCHEMA,
        "source_date": target_date,
        "effective_from": effective_date,
        "expires_on": effective_date,
        "analysis_axis": FAMILY,
        "selected_delay_sec": 0.0,
        "scope_policies": {
            row["scope_key"]: {
                "selected_delay_sec": 0.0,
                "selection_status": "incumbent_zero_carry_source_gap",
                "runtime_apply_allowed": False,
            } for row in scope_diagnostic
        },
        "type_policies": {
            row["type_key"]: {
                "selected_delay_sec": 0.0,
                "selection_status": "incumbent_zero_carry_source_gap",
                "runtime_apply_allowed": False,
            } for row in type_diagnostic
        },
        "runtime_apply_allowed": False,
        "selection_status": "incumbent_zero_carry_source_gap",
        "first_blocker": blocker,
        "paired_net_ev_delta_pct": None,
        "holdout_net_ev_delta_pct": None,
        "source_sha256": source["sha256"],
        "source_report": str(report_path(target_date)),
        "decision_authority": "next_preopen_bounded_pre_submit_delay_policy",
        "metric_role": "primary_ev",
        "window_policy": "same_frozen_intent_first_submit_delay_0_30_60_120_180s",
        "sample_floor": {"paired_attempts": 10, "holdout_attempts": 3},
        "primary_decision_metric": "paired_completed_cost_net_ev_delta_pct",
        "source_quality_gate": "exact_intent_route_fresh_depth_fill_terminal_cost_and_holdout",
        "forbidden_uses": "entry_action|split_shape|price_override|quantity_increase|safety_guard_bypass",
    }
    policy["report_sha256"] = _digest(report)
    policy["policy_sha256"] = _digest(policy)
    report["policy_sha256"] = policy["policy_sha256"]
    if write:
        _atomic_json(report_path(target_date), report)
        _atomic_json(policy_path(target_date), policy)
    return report


def load_runtime_policy(*, now: datetime | None = None,
                        decision_type: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return zero unless an exact-date, economic-valid independent policy loads."""
    fallback = {"delay_sec": 0.0, "status": "zero_incumbent", "policy_sha256": None}
    if os.getenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED", "").lower() not in {
        "1", "true", "yes", "on"
    }:
        return fallback
    path = Path(os.getenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE") or "")
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        return {**fallback, "status": "policy_missing_or_unbounded"}
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
        now_date = (now or datetime.now(KST)).astimezone(KST).date().isoformat()
        digest = policy.pop("policy_sha256")
        valid = (
            policy.get("schema") == POLICY_SCHEMA
            and digest == _digest(policy)
            and policy.get("effective_from") <= now_date <= policy.get("expires_on")
            and os.getenv("KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE", now_date) == now_date
        )
        if not valid:
            return {**fallback, "status": "policy_identity_or_date_invalid"}
        report_file = report_path(str(policy.get("source_date") or ""))
        if not report_file.is_file() or report_file.stat().st_size > 1024 * 1024:
            return {**fallback, "status": "policy_report_missing_or_unbounded"}
        report = json.loads(report_file.read_text(encoding="utf-8"))
        report_policy_digest = report.pop("policy_sha256", None)
        if (
            report_policy_digest != digest
            or _digest(report) != policy.get("report_sha256")
            or report.get("analysis_axis") != FAMILY
            or report.get("source_date") != policy.get("source_date")
            or report.get("effective_date") != policy.get("effective_from")
            or report.get("selected_delay_sec") != policy.get("selected_delay_sec")
        ):
            return {**fallback, "status": "policy_report_identity_invalid"}
        selected = _number(policy.get("selected_delay_sec"))
        if selected not in DELAYS_SEC:
            return {**fallback, "status": "policy_delay_invalid"}
        if selected > 0 and not _validated_candidate(policy, report):
            return {**fallback, "status": "policy_economics_unvalidated"}
        for family, evidence_key, key_name in (
            ("scope_policies", "scope_census", "scope_key"),
            ("type_policies", "type_census", "type_key"),
        ):
            branches = policy.get(family, {})
            if not isinstance(branches, dict):
                return {**fallback, "status": "policy_selector_invalid"}
            for key, branch in branches.items():
                if not isinstance(branch, dict) or key not in {
                    row.get(key_name) for row in report.get(evidence_key, [])
                    if isinstance(row, dict)
                } or _number(branch.get("selected_delay_sec")) not in DELAYS_SEC:
                    return {**fallback, "status": "policy_selector_invalid"}
                if _number(branch.get("selected_delay_sec")) > 0 and not _validated_candidate(
                    policy, report,
                    scope_key=key if family == "scope_policies" else None,
                    type_key=key if family == "type_policies" else None,
                ):
                    return {**fallback, "status": "policy_economics_unvalidated"}
        if (policy.get("type_policies") or policy.get("scope_policies")) and not isinstance(decision_type, dict):
            return {**fallback, "status": "decision_type_missing"}
        type_key = str((decision_type or {}).get("type_key") or "")
        scope_key = "|".join(type_key.split("|")[:2]) if type_key.count("|") == 2 else ""
        if (decision_type and decision_type.get("schema") != "pre_submit_delay_decision_type_v1"):
            return {**fallback, "status": "decision_type_invalid"}
        type_branch = (policy.get("type_policies") or {}).get(type_key)
        scope_branch = (policy.get("scope_policies") or {}).get(scope_key)
        branch = type_branch or scope_branch
        chosen = _number(branch.get("selected_delay_sec")) if branch else selected
        return {"delay_sec": chosen, "status": "loaded", "policy_sha256": digest,
                "selected_type_key": type_key if type_branch else None,
                "selected_scope_key": scope_key if scope_branch and not type_branch else None}
    except (OSError, ValueError, TypeError, KeyError):
        return {**fallback, "status": "policy_parse_invalid"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--effective-date", required=True)
    args = parser.parse_args(argv)
    result = build_report(args.date, effective_date=args.effective_date)
    print(json.dumps({
        "status": result["status"],
        "first_blocker": result["first_blocker"],
        "eligible_attempt_count": result["eligible_attempt_count"],
        "policy": str(policy_path(args.date)),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
