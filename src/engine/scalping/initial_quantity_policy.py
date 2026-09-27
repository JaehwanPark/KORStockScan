"""Completed-trade census and conditional initial-entry split research.

This producer is source-only. A lower observed price is a counterfactual fill
scenario, never a broker execution receipt or runtime policy approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import tempfile
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from src.trading.order.split_execution_math import pct_price_offset
from src.trading.order.tick_utils import get_tick_size, move_price_by_ticks
from src.engine.trade_profit import (calculate_net_profit_rate,
                                     calculate_net_realized_pnl, get_trade_cost_rate)
from src.engine.scalping.initial_quantity_type import (
    CLASSIFIER_VERSION, QUANTITY_TYPES as _TYPES,
    finite_number as _number,
    kst_timestamp as _timestamp, type_from_decision_receipt as _type_from_decision_receipt,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

BASELINE = date(2026, 6, 5)
REPORT_SCHEMA = "initial_entry_quantity_completed_trade_replay_v1"
POLICY_SCHEMA = "initial_entry_quantity_type_policy_v1"
COST_MODEL = "canonical_sell_notional_only_v1"
MAX_QUOTE_AGE_MS = 1000.0
LEG_TTL_SECONDS = 600
_RECORD_ID = re.compile(r'"record_id"\s*:\s*(?:"([^"\\]*)"|(\d+))')
_SHAPES = {
    "parent": (1.0, (0.0,)),
    "two_leg_0_0p3": (0.5, (0.0, 0.3)),
    "three_leg_0_0p3_0p8": (0.5, (0.0, 0.3, 0.8)),
    "two_leg_0_1tick": (0.5, (0, 1)),
    "three_leg_0_1_2tick": (0.5, (0, 1, 2)),
}
_TICK_SHAPES = {"two_leg_0_1tick", "three_leg_0_1_2tick"}


def _select_initial_winner_shape(
    quantity_type: str, candidates: dict[str, dict[str, Any]],
) -> str:
    """Choose a first seed from observed winner-weighted shapes.

    The first seed has no deployed predecessor to outperform. An unobserved
    split has no shape evidence; ties and unknown types keep the parent.
    """
    best = "parent"
    if quantity_type == "SAFE_UNKNOWN":
        return best
    parent_score = candidates.get("parent", {}).get(
        "winner_weighted_conservative_ev_pct")
    best_score = parent_score if isinstance(parent_score, (int, float)) else None
    for shape in _SHAPES:
        if shape == "parent":
            continue
        metric = candidates.get(shape) or {}
        score = metric.get("winner_weighted_conservative_ev_pct")
        if (metric.get("state") != "paired_with_parent_fallback"
                or not isinstance(metric.get("winner_comparable_count"), int)
                or metric["winner_comparable_count"] < 1
                or not isinstance(score, (int, float))
                or not math.isfinite(score)):
            continue
        if best_score is None or score > best_score + 1e-9:
            best, best_score = shape, score
    return best


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _pctl(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil(len(ordered) * percentile) - 1
    return round(ordered[max(0, min(index, len(ordered) - 1))], 6)


def _block_io_wait_ms() -> float | None:
    try:
        stat = Path("/proc/self/stat").read_text()
        ticks = int(stat[stat.rfind(")") + 2:].split()[39])
        return 1000.0 * ticks / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError):
        return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_quality_state(day: str, data_dir: Path) -> dict[str, Any]:
    path = data_dir / "report" / "observation_source_quality_audit" / f"observation_source_quality_audit_{day}.json"
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, ValueError):
        return {"status": "missing_or_invalid", "tuning_input_allowed": False,
                "artifact": str(path), "sha256": None}
    if not isinstance(payload, dict):
        return {"status": "invalid", "tuning_input_allowed": False,
                "artifact": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or "invalid")
    hard_count = _number(summary.get("hard_blocking_contract_gap_count"))
    allowed = (status in {"pass", "warning"}
               and payload.get("target_date") == day
               and summary.get("tuning_input_allowed") is True
               and hard_count == 0)
    return {"status": status, "tuning_input_allowed": allowed,
            "artifact": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_row_exclusion_applied": bool(payload.get("raw_row_exclusion")
                                              or summary.get("raw_row_exclusion_applied"))}


def _read_trade_facts(as_of: str, *, entry_on_or_after: str | None = None) -> list[dict[str, Any]]:
    """Read the completed-trade fact owner without mutating its database."""
    from sqlalchemy import or_
    from src.database.db_manager import DBManager
    from src.database.models import TradePerformanceFact

    start = max(BASELINE, date.fromisoformat(entry_on_or_after)) if entry_on_or_after else BASELINE
    end = date.fromisoformat(as_of)
    with DBManager().get_session() as session:
        facts = (session.query(TradePerformanceFact)
                 .filter(or_(TradePerformanceFact.rec_date >= start,
                             TradePerformanceFact.buy_time >= datetime.combine(
                                 start, datetime.min.time())),
                         or_(TradePerformanceFact.rec_date <= end,
                             TradePerformanceFact.buy_time < datetime.combine(
                                 end + timedelta(days=1), datetime.min.time())),
                         TradePerformanceFact.strategy.in_(("SCALPING", "SCALP")),
                         TradePerformanceFact.position_tag.in_(("SCANNER", "SCALP_BASE")))
                 .order_by(TradePerformanceFact.recommendation_id).all())
        return [{"recommendation_id": fact.recommendation_id,
                 "rec_date": fact.rec_date.isoformat() if fact.rec_date else None,
                 "stock_code": fact.stock_code, "strategy": fact.strategy,
                 "position_tag": fact.position_tag, "status": fact.status,
                 "buy_price": fact.buy_price, "buy_qty": fact.buy_qty,
                 "buy_time": fact.buy_time.isoformat() if fact.buy_time else None,
                 "sell_price": fact.sell_price,
                 "sell_time": fact.sell_time.isoformat() if fact.sell_time else None,
                 "profit_rate": fact.profit_rate,
                 "realized_pnl_krw": fact.realized_pnl_krw,
                 "add_count": fact.add_count,
                 "avg_down_count": fact.avg_down_count,
                 "pyramid_count": fact.pyramid_count}
                for fact in facts]


def completed_trade_fact_census(as_of: str, *, fact_rows: list[dict[str, Any]] | None = None,
                                data_dir: Path = DATA_DIR,
                                entry_on_or_after: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Seal every eligible completed initial position from the costed fact owner."""
    date.fromisoformat(as_of)
    refresh_start = date.fromisoformat(entry_on_or_after) if entry_on_or_after else None
    source = (_read_trade_facts(as_of, entry_on_or_after=entry_on_or_after)
              if fact_rows is None else list(fact_rows))
    source = sorted(source, key=lambda item: str(item.get("recommendation_id") or "")
                    if isinstance(item, dict) else "")
    exclusions: Counter[str] = Counter()
    rows: dict[str, dict[str, Any]] = {}
    conflicts: set[str] = set()
    cost_rate = get_trade_cost_rate()
    for fact in source:
        if not isinstance(fact, dict):
            exclusions["invalid_fact_row"] += 1
            continue
        if str(fact.get("status") or "").upper() != "COMPLETED":
            exclusions["not_completed"] += 1
            continue
        if str(fact.get("strategy") or "").upper() not in {"SCALPING", "SCALP"}:
            exclusions["other_strategy"] += 1
            continue
        if str(fact.get("position_tag") or "").upper() not in {"SCANNER", "SCALP_BASE"}:
            exclusions["other_custody"] += 1
            continue
        if any(_number(fact.get(key)) not in (None, 0) for key in
               ("add_count", "avg_down_count", "pyramid_count")):
            exclusions["scale_in_position"] += 1
            continue
        rid = str(fact.get("recommendation_id") or "").strip()
        buy_at = _timestamp(fact.get("buy_time"))
        sell_at = _timestamp(fact.get("sell_time"))
        buy_price = _number(fact.get("buy_price"))
        sell_price = _number(fact.get("sell_price"))
        qty = _number(fact.get("buy_qty"))
        profit = _number(fact.get("profit_rate"))
        pnl = _number(fact.get("realized_pnl_krw"))
        if not rid or not str(fact.get("stock_code") or ""):
            exclusions["identity_missing"] += 1
            continue
        if not buy_at or not sell_at or sell_at <= buy_at:
            exclusions["trade_clock_missing_or_invalid"] += 1
            continue
        if not BASELINE <= buy_at.date() <= sell_at.date() <= date.fromisoformat(as_of):
            exclusions["date_outside_baseline_or_as_of"] += 1
            continue
        if refresh_start and buy_at.date() < refresh_start:
            exclusions["before_refresh_start"] += 1
            continue
        if (buy_price is None or buy_price <= 0 or sell_price is None or sell_price <= 0
                or qty is None or qty <= 0 or not qty.is_integer()
                or profit is None or pnl is None):
            exclusions["terminal_cost_or_quantity_missing"] += 1
            continue
        expected_pnl = calculate_net_realized_pnl(buy_price, sell_price, qty,
                                                   cost_rate=cost_rate)
        expected_profit = calculate_net_profit_rate(buy_price, sell_price,
                                                    cost_rate=cost_rate)
        if abs(expected_pnl - pnl) > 1 or abs(expected_profit - profit) > 0.02:
            exclusions["terminal_cost_contract_mismatch"] += 1
            continue
        row = {"trade_id": f"fact:{rid}", "record_id": rid,
               "entry_date": buy_at.date().isoformat(),
               "exit_date": sell_at.date().isoformat(),
               "stock_code": str(fact["stock_code"]),
               "buy_price": buy_price, "sell_price": sell_price,
               "buy_qty": int(qty), "profit_rate": profit,
               "realized_net_pnl_krw": pnl,
               "exit_at": sell_at.isoformat(),
               "entry_at_fact_buy_time": buy_at.isoformat(),
               "entry_date_source": "trade_performance_facts.buy_time",
               "terminal_source": "trade_performance_facts.completed_costed"}
        prior = rows.get(rid)
        if rid in conflicts:
            exclusions["conflicting_duplicate_fact"] += 1
        elif prior is not None and prior != row:
            exclusions["conflicting_duplicate_fact"] += 2
            rows.pop(rid, None)
            conflicts.add(rid)
        elif prior is None:
            rows[rid] = row
        else:
            exclusions["duplicate_fact"] += 1
    result = sorted(rows.values(), key=lambda item: (item["entry_date"], item["record_id"]))
    entry_days = sorted({row["entry_date"] for row in result})
    exit_days = sorted({row["exit_date"] for row in result})
    return result, {"census_source": "trade_performance_facts",
                    **({"entry_on_or_after": entry_on_or_after} if refresh_start else {}),
                    "all_completed_initial_trades": len(result),
                    "actual_completed_net_pnl_krw": round(sum(
                        row["realized_net_pnl_krw"] for row in result), 3),
                    "actual_completed_mean_profit_rate_pct": (
                        round(sum(row["profit_rate"] for row in result) / len(result), 6)
                        if result else None),
                    "fact_rows_read": len(source), "excluded": dict(sorted(exclusions.items())),
                    "cost_rate": cost_rate, "input_fact_rows": source,
                    "input_manifest_sha256": _digest(source),
                    "source_quality_by_entry_date": {
                        day: _source_quality_state(day, data_dir) for day in entry_days},
                    "source_quality_by_exit_date": {
                        day: _source_quality_state(day, data_dir) for day in exit_days}}


def _record_id(raw: str) -> str:
    match = _RECORD_ID.search(raw)
    if match is None:
        return ""
    return match.group(1) or match.group(2)


def _exit_at(trade: dict[str, Any]) -> datetime | None:
    return _timestamp(trade.get("exit_at"))


def _fresh_observed_price(fields: dict[str, Any]) -> tuple[float | None, str]:
    """Never use an unclocked current_price_observed as a post-fill print."""
    if str(fields.get("quote_stale") or "").lower() in {"true", "1"}:
        return None, "stale_quote"
    consistency = str(fields.get("quote_consistency_state") or "").strip().lower()
    if consistency and consistency not in {"ok", "warning", "single_source"}:
        return None, "quote_consistency_invalid"
    age = _number(fields.get("ws_age_ms"))
    price = _number(fields.get("latest_price"))
    if price and price > 0 and age is not None and 0 <= age <= MAX_QUOTE_AGE_MS:
        return price, "fresh_ws_latest_price"
    return None, "price_source_clock_missing_or_stale"


def join_post_fill_paths(trades: list[dict[str, Any]], *, data_dir: Path = DATA_DIR,
                         scan_seconds: dict[str, float] | None = None,
                         source_receipts: dict[str, Any] | None = None,
                         price_horizon_seconds: int = LEG_TTL_SECONDS) -> dict[str, dict[str, Any]]:
    """Stream only matching record IDs from each native pipeline partition."""
    by_date: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for trade in trades:
        by_date[trade["entry_date"]][trade["record_id"]].append(trade)
    result = {}
    for trade in trades:
        entry_clock = _timestamp(trade.get("entry_at_fact_buy_time"))
        exit_clock = _exit_at(trade)
        result[trade["trade_id"]] = {
            "decisions": [], "fills": [], "prices": [], "order_starts": [],
            "order_requests": [], "order_sent": [],
            "source_path": None, "source_gap": [],
            "join_start": entry_clock - timedelta(hours=1) if entry_clock else None,
            "join_end": entry_clock + timedelta(hours=1) if entry_clock else None,
            "price_start": entry_clock - timedelta(minutes=5) if entry_clock else None,
            "price_end": (min(entry_clock + timedelta(seconds=price_horizon_seconds + 300),
                              exit_clock) if entry_clock and exit_clock else None),
        }
    for day, records in sorted(by_date.items()):
        date_started = time.perf_counter()
        path = existing_or_gzip_path(data_dir / "pipeline_events" / f"pipeline_events_{day}.jsonl")
        if not path.exists():
            for group in records.values():
                for trade in group:
                    result[trade["trade_id"]]["source_gap"].append("pipeline_missing")
            continue
        stat = path.stat()
        archive_receipt_path = Path(f"{path}.archive_receipt.json")
        archive_identity_valid: bool | None = None
        if path.suffix == ".gz" and archive_receipt_path.is_file():
            try:
                archive = json.loads(archive_receipt_path.read_text(encoding="utf-8"))
                generation = archive["archive_generation"]
                archive_identity_valid = bool(
                    archive.get("schema") == "pipeline_raw_archive_identity_v1"
                    and generation.get("device") == stat.st_dev
                    and generation.get("inode") == stat.st_ino
                    and generation.get("size_bytes") == stat.st_size
                    and generation.get("mtime_ns") == stat.st_mtime_ns)
            except (OSError, ValueError, KeyError, TypeError):
                archive_identity_valid = False
        if source_receipts is not None:
            source_receipts[day] = {"path": str(path), "size_bytes": stat.st_size,
                                    "sha256": _file_sha256(path),
                                    "archive_identity_valid": archive_identity_valid}
        if archive_identity_valid is False:
            for group in records.values():
                for trade in group:
                    result[trade["trade_id"]]["source_gap"].append("archive_identity_invalid")
            continue
        for group in records.values():
            for trade in group:
                result[trade["trade_id"]]["source_path"] = str(path)
        with open_text_auto(path) as handle:
            for raw in handle:
                rid = _record_id(raw)
                group = records.get(rid)
                if not group:
                    continue
                try:
                    event = json.loads(raw)
                except ValueError:
                    continue
                if str(event.get("stock_code") or "") not in {x["stock_code"] for x in group}:
                    continue
                fields = event.get("fields") or {}
                if not isinstance(fields, dict):
                    continue
                stage = str(event.get("stage") or "")
                emitted = _timestamp(event.get("emitted_at"))
                if emitted is None:
                    continue
                for trade in group:
                    if trade["stock_code"] != str(event.get("stock_code") or ""):
                        continue
                    bucket = result[trade["trade_id"]]
                    within_entry_join = bool(bucket["join_start"] and bucket["join_end"]
                                             and bucket["join_start"] <= emitted <= bucket["join_end"])
                    if ((stage == "entry_execution_sizing_plan"
                         and fields.get("entry_execution_sizing_valid") in (True, "True"))
                            or (stage == "order_bundle_submitted"
                                and fields.get("actual_order_submitted") in (True, "True"))) and within_entry_join:
                        bucket["decisions"].append({"at": emitted, "stage": stage, "fields": {
                                key: fields.get(key) for key in (
                                    "effective_venue", "sizing_venue_at_allocation",
                                    "market_session_bucket", "source_signature",
                                    "reference_time", "current_price", "latest_price", "tier", "ratio",
                                    "requested_qty", "effective_qty", "pre_cap_qty", "binding_caps",
                                    "quantity_type", "quantity_type_classifier_version",
                                    "scalping_sizing_quantity_type",
                                    "scalping_sizing_quantity_type_classifier_version",
                                    "quantity_type_policy_row",
                                    "position_sizing_policy_status",
                                    "position_sizing_policy_sha256",
                                    "initial_quantity_runtime_pid",
                                    "initial_quantity_cap_research_context",
                                    "entry_submit_attempt_id",
                                    "entry_execution_sizing_plan_sha256",
                                    "scalping_sizing_quantity_type_policy_row",
                                    "scalping_sizing_position_sizing_policy_status",
                                    "scalping_sizing_position_sizing_policy_sha256",
                                    "buy_pressure_10t", "tick_aggressor_pressure_usable",
                                    "tick_context_quality", "quote_stale", "quote_consistency_state",
                                    "classifier_route_key", "classifier_transport_epoch",
                                    "ws_route", "market_data_transport_epoch",
                                    "entry_split_order_probe_first_applied",
                                    "entry_split_order_probe_qty",
                                    "entry_split_order_leg_count",
                                )}})
                    if stage == "entry_cancel_wait_submission" and within_entry_join:
                        context_raw = fields.get("entry_cancel_wait_submission_context")
                        try:
                            context = json.loads(context_raw) if isinstance(context_raw, str) else {}
                        except ValueError:
                            context = {}
                        order_start = _timestamp(context.get("frozen_at"))
                        order_no = str(fields.get("broker_order_no") or "")
                        if (fields.get("actual_order_submitted") in (True, "True")
                                and order_no and order_start and order_start <= emitted
                                and context.get("stock_code") == trade["stock_code"]):
                            bucket["order_starts"].append({
                                "at": order_start, "order_no": order_no,
                                "source": "entry_cancel_wait_submission_context_frozen_at",
                                "probe_applied": str(context.get("child_id") or "").startswith(
                                    "entry_split_probe"),
                                "emitted_at": emitted})
                    if stage in {"order_leg_request", "order_leg_sent"} and within_entry_join:
                        attempt_id = str(fields.get("entry_submit_attempt_id") or "")
                        plan_sha = str(fields.get("entry_execution_sizing_plan_sha256") or "")
                        tag = str(fields.get("tag") or "")
                        if attempt_id and plan_sha and tag:
                            event_row = {"at": emitted, "attempt_id": attempt_id,
                                         "plan_sha": plan_sha, "tag": tag,
                                         "probe_applied": tag.startswith("entry_split_probe")}
                            if stage == "order_leg_request":
                                bucket["order_requests"].append(event_row)
                            else:
                                order_no = str(fields.get("broker_order_no")
                                               or fields.get("order_no") or "")
                                if (order_no and fields.get("actual_order_submitted")
                                        in (True, "True")):
                                    bucket["order_sent"].append({**event_row,
                                                                 "order_no": order_no})
                                    initial_start = _timestamp(fields.get(
                                        "initial_quantity_order_start_at"))
                                    schedule_sha = str(fields.get(
                                        "initial_quantity_schedule_sha256") or "")
                                    policy_sha = str(fields.get(
                                        "initial_quantity_policy_file_sha256") or "")
                                    if (initial_start is not None
                                            and initial_start <= emitted
                                            and fields.get("initial_quantity_leg_index")
                                            in (0, "0")
                                            and fields.get("initial_quantity_attempt_id")
                                            == attempt_id
                                            and re.fullmatch(r"[0-9a-f]{64}", schedule_sha)
                                            and re.fullmatch(r"[0-9a-f]{64}", policy_sha)
                                            and any(
                                                decision["fields"].get(
                                                    "entry_submit_attempt_id") ==
                                                attempt_id
                                                and decision["fields"].get(
                                                    "entry_execution_sizing_plan_sha256")
                                                == plan_sha
                                                and decision["fields"].get(
                                                    "scalping_sizing_position_sizing_policy_sha256")
                                                == policy_sha
                                                for decision in bucket["decisions"])):
                                        bucket["order_starts"].append({
                                            "at": initial_start,
                                            "order_no": order_no,
                                            "source":
                                                "initial_quantity_bundle_order_start_at",
                                            "probe_applied": tag ==
                                                "initial_quantity_probe_0",
                                            "emitted_at": emitted,
                                            "attempt_id": attempt_id,
                                            "plan_sha": plan_sha,
                                            "schedule_sha256": schedule_sha,
                                            "policy_sha256": policy_sha,
                                        })
                    elif (stage == "position_rebased_after_fill" and within_entry_join
                          and str(fields.get("entry_mode") or "").lower() == "normal"):
                        price = _number(fields.get("fill_price") or fields.get("avg_buy_price"))
                        qty = _number(fields.get("fill_qty"))
                        broker_fill_raw = fields.get("broker_execution_observed_at")
                        fill_at = _timestamp(broker_fill_raw) or emitted
                        if fill_at and price and qty and qty > 0:
                            bucket["fills"].append({"at": fill_at, "emitted_at": emitted,
                                "clock_precision_sec": (
                                    1 if broker_fill_raw and "." not in
                                    str(broker_fill_raw).split("T")[-1] else 0),
                                "price": price,
                                "qty": int(qty), "venue": str(fields.get("actual_execution_venue") or "UNKNOWN"),
                                "order_no": str(fields.get("order_no") or ""),
                                "execution_no": str(fields.get("execution_no") or ""),
                                "clock_source": ("broker_execution_observed_at"
                                                 if fields.get("broker_execution_observed_at")
                                                 else "position_rebased_emitted_at_proxy")})
                    if trade["buy_qty"] >= 2:
                        price_window = bool(bucket["price_start"] and bucket["price_end"]
                                            and bucket["price_start"] <= emitted <= bucket["price_end"])
                        if price_window:
                            price, source = _fresh_observed_price(fields)
                            if price is not None:
                                bucket["prices"].append({"at": emitted, "price": price,
                                    "source": source,
                                    "venue": str(fields.get("effective_venue") or ""),
                                    "route": str(fields.get("classifier_route_key")
                                                 or fields.get("ws_route") or ""),
                                    "epoch": str(fields.get("classifier_transport_epoch")
                                                 or fields.get("market_data_transport_epoch") or ""),
                                    "stage": stage})
        try:
            stat_after = path.stat()
            source_stable = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) == (
                stat_after.st_dev, stat_after.st_ino, stat_after.st_size,
                stat_after.st_mtime_ns)
        except OSError:
            source_stable = False
        if source_receipts is not None:
            source_receipts[day]["stable_during_scan"] = source_stable
        if not source_stable:
            for group in records.values():
                for trade in group:
                    bucket = result[trade["trade_id"]]
                    bucket["decisions"].clear()
                    bucket["fills"].clear()
                    bucket["prices"].clear()
                    bucket["order_starts"].clear()
                    bucket["order_requests"].clear()
                    bucket["order_sent"].clear()
                    bucket["source_gap"].append("pipeline_changed_during_scan")
        if source_stable:
            for group in records.values():
                for trade in group:
                    bucket = result[trade["trade_id"]]
                    requests = bucket["order_requests"]
                    sent_counts = Counter((row["attempt_id"], row["plan_sha"], row["tag"])
                                          for row in bucket["order_sent"])
                    for sent in bucket["order_sent"]:
                        identity = (sent["attempt_id"], sent["plan_sha"], sent["tag"])
                        if sent_counts[identity] != 1:
                            continue
                        matches = [request for request in requests
                                   if request["attempt_id"] == sent["attempt_id"]
                                   and request["plan_sha"] == sent["plan_sha"]
                                   and request["tag"] == sent["tag"]
                                   and 0 <= (sent["at"] - request["at"]).total_seconds() <= 120]
                        if len(matches) == 1:
                            bucket["order_starts"].append({
                                "at": matches[0]["at"], "latest_at": sent["at"],
                                "order_no": sent["order_no"],
                                "probe_applied": matches[0]["probe_applied"],
                                "source": "order_leg_request_to_sent_bracket"})
        if scan_seconds is not None:
            scan_seconds[day] = round(time.perf_counter() - date_started, 6)
    return result


def _quantity_parts(qty: int, shape: str) -> list[int]:
    if shape == "parent":
        return [qty]
    if shape.startswith("two_leg_"):
        first = max(1, math.ceil(qty / 2))
        return [first, qty - first]
    first = max(1, math.ceil(qty / 2))
    remaining = qty - first
    second = math.ceil(remaining / 2)
    return [first, second, remaining - second]


def _costed_fixed_exit_pnl(
    legs: list[tuple[int, float]], sell_price: float, cost_rate: float,
) -> float:
    """Match trade_profit's sell-notional cost contract before final rounding."""
    if not legs:
        return 0.0
    buy_amount = sum(qty * price for qty, price in legs)
    sell_amount = sell_price * sum(qty for qty, _ in legs)
    return sell_amount - buy_amount - cost_rate * sell_amount


def _paired_candidate(trade: dict[str, Any], path: dict[str, Any], shape: str) -> dict[str, Any]:
    if shape == "parent":
        entry_at = _timestamp(trade.get("entry_at_fact_buy_time"))
        decisions = [item for item in path.get("decisions") or []
                     if entry_at and abs((item["at"] - entry_at).total_seconds()) <= 3600
                     and (item["at"] <= entry_at or item["stage"] == "order_bundle_submitted"
                          and (item["at"] - entry_at).total_seconds() <= 30)]
        # The submitted bundle is often closer to the fill than the sizing
        # decision.  It is an execution event, not proof of which policy
        # calculated the quantity.  Keep that fallback for historical type
        # research, but bind a refresh trade to the actual sizing event.
        sizing_decisions = [item for item in decisions
                            if item["stage"] == "entry_execution_sizing_plan"
                            and item["at"] <= entry_at]
        decision = (max(sizing_decisions, key=lambda item: item["at"])
                    if sizing_decisions else
                    min(decisions, key=lambda item: abs((item["at"] - entry_at).total_seconds()))
                    if decisions else None)
        fields = dict(decision["fields"]) if decision else {}
        fields["effective_venue"] = fields.get("effective_venue") or fields.get("sizing_venue_at_allocation")
        if decision:
            fields["reference_time"] = fields.get("reference_time") or decision["at"].isoformat()
        quantity_type = (_type_from_decision_receipt(
            fields, decision_at=decision["at"], entry_at=entry_at)
            if decision and entry_at else "SAFE_UNKNOWN")
        first_fill = min(path.get("fills") or [], key=lambda item: item["at"],
                         default=None)
        order_no = str(first_fill.get("order_no") or "") if first_fill else ""
        sent = [item for item in path.get("order_sent") or []
                if order_no and item["order_no"] == order_no]
        sent_identity = ((sent[0]["attempt_id"], sent[0]["plan_sha"])
                         if sent and all(
                             (item["attempt_id"], item["plan_sha"]) ==
                             (sent[0]["attempt_id"], sent[0]["plan_sha"])
                             for item in sent) else None)
        bound_decisions = [item for item in sizing_decisions
                           if sent_identity and (
                               item["fields"].get("entry_submit_attempt_id"),
                               item["fields"].get("entry_execution_sizing_plan_sha256"))
                           == sent_identity]
        bound_decision = (max(bound_decisions, key=lambda item: item["at"])
                          if bound_decisions else None)
        bound_fields = bound_decision["fields"] if bound_decision else {}
        raw_cap_context = bound_fields.get("initial_quantity_cap_research_context")
        try:
            cap_context = (json.loads(raw_cap_context)
                           if isinstance(raw_cap_context, str) else raw_cap_context)
        except (ValueError, TypeError):
            cap_context = None
        if (not isinstance(cap_context, dict)
                or cap_context.get("schema_version") !=
                "initial_quantity_cap_context_v1"):
            cap_context = None
        return {"status": "paired", "quantity_type": quantity_type,
                "candidate_net_pct": trade["profit_rate"], "fill_state": "actual_parent",
                "candidate_net_pnl_krw": trade["realized_net_pnl_krw"],
                "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
                "decision_snapshot_status": "joined" if decision else "missing_unknown_type",
                "policy_decision_stage": (bound_decision["stage"]
                                          if bound_decision else None),
                "policy_decision_at": (bound_decision["at"].isoformat()
                                       if bound_decision else None),
                "applied_policy_status": (bound_fields.get("position_sizing_policy_status")
                                          or bound_fields.get("scalping_sizing_position_sizing_policy_status")),
                "applied_policy_file_sha256": (bound_fields.get("position_sizing_policy_sha256")
                                                or bound_fields.get("scalping_sizing_position_sizing_policy_sha256")),
                "applied_policy_runtime_pid": bound_fields.get(
                    "initial_quantity_runtime_pid"),
                **({"applied_cap_research_context": cap_context}
                   if cap_context is not None else {}),
                "fixed_exit_assumption": False}
    if path.get("source_gap"):
        return {"status": "path_source_gap",
                "source_gap": sorted(set(path["source_gap"]))}
    fills = sorted(path["fills"], key=lambda x: x["at"])
    unique = {((x["order_no"], x["execution_no"]) if x["order_no"] and x["execution_no"]
              else (x["at"].isoformat(), x["price"], x["qty"])): x for x in fills}
    fills = sorted(unique.values(), key=lambda x: x["at"])
    if not fills:
        proxy = _timestamp(trade.get("entry_at_fact_buy_time"))
        if proxy is None:
            return {"status": "fill_receipt_missing"}
        fills = [{"at": proxy, "price": trade["buy_price"], "qty": trade["buy_qty"],
                  "venue": "UNKNOWN", "order_no": "", "execution_no": "",
                  "clock_source": "trade_performance_fact_buy_time"}]
    first = fills[0]
    if first["at"].date().isoformat() != trade["entry_date"]:
        return {"status": "fill_entry_date_mismatch"}
    exit_at = _exit_at(trade)
    if exit_at is None or exit_at <= first["at"]:
        return {"status": "exit_clock_unsupported"}
    decisions = [item for item in path.get("decisions") or []
                 if (item["at"] <= first["at"]
                     or item["stage"] == "order_bundle_submitted"
                     and (item["at"] - first["at"]).total_seconds() <= 30)
                 and abs((first["at"] - item["at"]).total_seconds()) <= 3600]
    decision = min(decisions, key=lambda x: abs((first["at"] - x["at"]).total_seconds())) if decisions else None
    if not decision:
        return {"status": "decision_snapshot_missing"}
    fields = dict(decision["fields"])
    fields["effective_venue"] = fields.get("effective_venue") or fields.get("sizing_venue_at_allocation")
    fields["reference_time"] = fields.get("reference_time") or decision["at"].isoformat()
    observed_qty = sum(x["qty"] for x in fills)
    if observed_qty != trade["buy_qty"]:
        return {"status": "fill_quantity_mismatch", "observed_qty": observed_qty}
    quantity_type = _type_from_decision_receipt(fields, decision_at=decision["at"],
                                                entry_at=first["at"])
    if observed_qty < (4 if shape.startswith("three_leg_") else 2):
        return {"status": "paired", "quantity_type": quantity_type,
                "candidate_net_pct": trade["profit_rate"],
                "conservative_net_pct": trade["profit_rate"],
                "upper_net_pct": trade["profit_rate"],
                "parent_net_pct": trade["profit_rate"],
                "candidate_net_pnl_krw": trade["realized_net_pnl_krw"],
                "conservative_net_pnl_krw": trade["realized_net_pnl_krw"],
                "upper_net_pnl_krw": trade["realized_net_pnl_krw"],
                "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
                "fill_state": "quantity_too_small_parent_fallback",
                "fixed_exit_assumption": True}
    candidate_qty = observed_qty
    parts = _quantity_parts(candidate_qty, shape)
    anchor = first["price"]
    if not float(anchor).is_integer() or int(anchor) % get_tick_size(anchor):
        return {"status": "entry_anchor_not_tick_aligned", "quantity_type": quantity_type,
                "fill_clock_source": first["clock_source"]}
    prices = [float(move_price_by_ticks(int(anchor), -int(offset))
                    if shape in _TICK_SHAPES else pct_price_offset(int(anchor), offset))
              for offset in _SHAPES[shape][1]]
    if not prices or any(price <= 0 for price in prices):
        return {"status": "invalid_p1_price", "quantity_type": quantity_type}
    if any(later >= earlier for earlier, later in zip(prices, prices[1:])):
        return {"status": "price_offset_collapsed", "quantity_type": quantity_type}
    deadline = min(first["at"] + timedelta(seconds=LEG_TTL_SECONDS), exit_at)
    decision_venue = str(fields.get("effective_venue") or "")
    decision_route = str(fields.get("classifier_route_key") or fields.get("ws_route") or "")
    decision_epoch = str(fields.get("classifier_transport_epoch")
                         or fields.get("market_data_transport_epoch") or "")
    observations = sorted((x for x in path["prices"] if first["at"] < x["at"] <= deadline
                          and (x["venue"] == decision_venue or not x["venue"] and not decision_venue)),
                          key=lambda x: x["at"])
    if not observations:
        return {"status": "path_source_gap", "quantity_type": quantity_type}
    cost_rate = get_trade_cost_rate()
    first_qty = parts[0]
    conditionally_filled = [(first_qty, anchor)]
    touch_legs: list[tuple[int, float]] = []
    verified_cross_count = 0
    for qty, limit in zip(parts[1:], prices[1:]):
        if qty <= 0:
            continue
        crosses = [x for x in observations if x["price"] < limit]
        if crosses:
            conditionally_filled.append((qty, limit))
            if (first["clock_source"] == "broker_execution_observed_at"
                    and first["order_no"] and first["execution_no"]
                    and decision_venue in {"KRX", "NXT"} and first["venue"] == decision_venue
                    and decision_route and decision_epoch
                    and any(x["route"] == decision_route and x["epoch"] == decision_epoch
                            for x in crosses)):
                verified_cross_count += 1
        elif any(x["price"] == limit for x in observations):
            touch_legs.append((qty, limit))
    def net_pnl(legs: list[tuple[int, float]]) -> float:
        return _costed_fixed_exit_pnl(legs, trade["sell_price"], cost_rate)
    no_extra_pnl = net_pnl([(first_qty, anchor)])
    crossed_pnl = net_pnl(conditionally_filled)
    touched_pnl = net_pnl(conditionally_filled + touch_legs)
    conservative_pnl = min(no_extra_pnl, crossed_pnl, touched_pnl)
    optimistic_pnl = max(no_extra_pnl, crossed_pnl, touched_pnl)
    original_notional = trade["buy_price"] * candidate_qty
    def pct(net_pnl_krw: float) -> float:
        return 100.0 * net_pnl_krw / original_notional
    return {"status": "paired", "quantity_type": quantity_type,
            "candidate_net_pct": round(pct(crossed_pnl), 6),
            "conservative_net_pct": round(pct(conservative_pnl), 6),
            "upper_net_pct": round(pct(optimistic_pnl), 6),
            "parent_net_pct": trade["profit_rate"],
            "candidate_net_pnl_krw": round(crossed_pnl, 3),
            "conservative_net_pnl_krw": round(conservative_pnl, 3),
            "upper_net_pnl_krw": round(optimistic_pnl, 3),
            "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
            "fill_state": "price_cross_conditional" if len(conditionally_filled) > 1 else (
                "price_touch_only" if touch_legs else "no_cross_observed"),
            "conditional_filled_qty": sum(q for q, _ in conditionally_filled),
            "conditional_crossed_leg_count": len(conditionally_filled) - 1,
            "verified_route_epoch_price_cross_count": verified_cross_count,
            "target_qty": candidate_qty, "fixed_exit_assumption": True,
            "counterfactual_anchor_price": anchor,
            "parent_avg_buy_price": trade["buy_price"],
            "candidate_notional_denominator_krw": original_notional,
            "price_source": "fresh_ws_latest_price", "exit_at": exit_at.isoformat(),
            "fill_at": first["at"].isoformat(), "fill_clock_source": first["clock_source"],
            "decision_stage": decision["stage"],
            "decision_emitted_after_fill_proxy": decision["at"] > first["at"],
            "venue_provenance": "verified" if decision_venue in {"KRX", "NXT"}
                and first["venue"] == decision_venue else "unverified_conditional"}


def build_initial_quantity_replay(as_of: str, *, data_dir: Path = DATA_DIR,
                                  fact_rows: list[dict[str, Any]] | None = None,
                                  performance: dict[str, Any] | None = None,
                                  entry_on_or_after: str | None = None,
                                  path_cache: dict[str, Any] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    wait_start = _block_io_wait_ms()
    trades, census = completed_trade_fact_census(as_of, fact_rows=fact_rows,
                                                  data_dir=data_dir,
                                                  entry_on_or_after=entry_on_or_after)
    eligible_trades = [trade for trade in trades
                       if census["source_quality_by_entry_date"][trade["entry_date"]]
                       ["tuning_input_allowed"]
                       and census["source_quality_by_exit_date"][trade["exit_date"]]
                       ["tuning_input_allowed"]]
    date_scan_seconds: dict[str, float] = {}
    source_receipts: dict[str, Any] = {}
    horizon = 1200 if path_cache is not None else LEG_TTL_SECONDS
    paths = join_post_fill_paths(eligible_trades, data_dir=data_dir,
                                 scan_seconds=date_scan_seconds,
                                 source_receipts=source_receipts,
                                 price_horizon_seconds=horizon)
    if path_cache is not None:
        path_cache.update({"census": census, "paths": paths,
                           "pipeline_source_receipts": source_receipts,
                           "date_scan_seconds": date_scan_seconds,
                           "price_horizon_seconds": horizon})
    counts: Counter[str] = Counter()
    paired: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    rows: list[dict[str, Any]] = []
    trade_seconds: list[float] = []
    for trade in trades:
        trade_started = time.perf_counter()
        quality = bool(census["source_quality_by_entry_date"][trade["entry_date"]]
                       ["tuning_input_allowed"]
                       and census["source_quality_by_exit_date"][trade["exit_date"]]
                       ["tuning_input_allowed"])
        shape_rows = ({shape: _paired_candidate(trade, paths[trade["trade_id"]], shape)
                       for shape in _SHAPES} if quality else
                      {shape: {"status": "source_quality_blocked"} for shape in _SHAPES})
        parent = shape_rows["parent"]
        path = paths.get(trade["trade_id"], {})
        first_fill = min(path.get("fills") or [], key=lambda item: item["at"],
                         default=None)
        matched_starts = ([item for item in path.get("order_starts") or []
                           if first_fill and item.get("order_no") == first_fill.get("order_no")]
                          if first_fill else [])
        quantity_type = parent.get("quantity_type") or next(
            (x.get("quantity_type") for x in shape_rows.values() if x.get("quantity_type")), "SAFE_UNKNOWN")
        for shape, value in list(shape_rows.items()):
            if (shape != "parent" and value.get("status") == "paired"
                    and value.get("quantity_type") != quantity_type):
                value = {"status": "decision_type_mismatch",
                         "parent_quantity_type": quantity_type,
                         "candidate_quantity_type": value.get("quantity_type")}
                shape_rows[shape] = value
            counts[f"{shape}:{value['status']}"] += 1
            if value["status"] == "paired":
                paired[quantity_type][shape].append(value)
        rows.append({"trade_id": trade["trade_id"], "record_id": trade["record_id"],
                     "stock_code": trade["stock_code"],
                     "entry_date": trade["entry_date"], "quantity_type": quantity_type,
                     "entry_fill_at": first_fill["at"].isoformat() if first_fill else None,
                     "entry_fill_venue": first_fill.get("venue") if first_fill else None,
                     "entry_fill_clock_source": (first_fill.get("clock_source")
                                                 if first_fill else None),
                     "applied_policy_status": parent.get("applied_policy_status"),
                     "applied_policy_file_sha256": parent.get("applied_policy_file_sha256"),
                     "applied_policy_runtime_pid": parent.get("applied_policy_runtime_pid"),
                     **({"applied_cap_research_context":
                         parent["applied_cap_research_context"]}
                        if "applied_cap_research_context" in parent else {}),
                     "policy_decision_stage": parent.get("policy_decision_stage"),
                     "policy_decision_at": parent.get("policy_decision_at"),
                     "entry_order_start_at": (matched_starts[0]["at"].isoformat()
                                              if len(matched_starts) == 1 else None),
                     "actual_profit_rate": trade["profit_rate"],
                     "actual_net_pnl_krw": trade["realized_net_pnl_krw"],
                     "source_gap": paths.get(trade["trade_id"], {}).get("source_gap", []),
                     "shapes": shape_rows})
        trade_seconds.append(time.perf_counter() - trade_started)
    selections: dict[str, Any] = {}
    type_trade_counts = Counter(row["quantity_type"] for row in rows)
    for quantity_type in _TYPES:
        winners = [row for row in rows if row["quantity_type"] == quantity_type
                   and row["actual_net_pnl_krw"] > 0
                   and row["actual_profit_rate"] > 0]
        winner_weight = sum(row["actual_net_pnl_krw"] for row in winners)
        weighted_parent = (sum(row["actual_profit_rate"] * row["actual_net_pnl_krw"]
                               for row in winners) / winner_weight if winner_weight else None)
        incumbent = paired[quantity_type].get("parent") or []
        incumbent_ev = sum(x["candidate_net_pct"] for x in incumbent) / len(incumbent) if incumbent else None
        incumbent_net = sum(x["parent_net_pnl_krw"] for x in incumbent)
        candidates: dict[str, Any] = {}
        for shape in _SHAPES:
            values = paired[quantity_type].get(shape) or []
            winner_comparable = [row for row in winners
                                 if (row["shapes"].get(shape) or {}).get("status") == "paired"]
            winner_comparable_ids = {row["trade_id"] for row in winner_comparable}
            weighted_candidate = (sum(
                row["actual_net_pnl_krw"] * (
                    (row["shapes"].get(shape) or {}).get("conservative_net_pct",
                     row["actual_profit_rate"])
                    if row["trade_id"] in winner_comparable_ids
                    else row["actual_profit_rate"])
                for row in winners) / winner_weight if winner_weight else None)
            if not values:
                candidates[shape] = {"paired_count": 0, "state": "no_comparable_trade",
                                     "winner_comparable_count": 0,
                                     "winner_weighted_conservative_ev_pct": (
                                         round(weighted_candidate, 6)
                                         if weighted_candidate is not None else None)}
                continue
            estimate = (incumbent_ev + sum(x["candidate_net_pct"] - x.get("parent_net_pct", x["candidate_net_pct"])
                                            for x in values) / len(incumbent)) if incumbent_ev is not None else None
            lower = (incumbent_ev + sum(x.get("conservative_net_pct", x["candidate_net_pct"])
                                         - x.get("parent_net_pct", x["candidate_net_pct"])
                                         for x in values) / len(incumbent)) if incumbent_ev is not None else None
            estimated_net = incumbent_net + sum(
                x["candidate_net_pnl_krw"] - x["parent_net_pnl_krw"]
                for x in values)
            conservative_net = incumbent_net + sum(
                x.get("conservative_net_pnl_krw", x["candidate_net_pnl_krw"])
                - x["parent_net_pnl_krw"] for x in values)
            modeled = sum(x.get("fill_state") in {"price_cross_conditional", "price_touch_only", "no_cross_observed"}
                          for x in values)
            crossed = sum(x.get("fill_state") == "price_cross_conditional" for x in values)
            verified_crossed = sum(x.get("verified_route_epoch_price_cross_count", 0) > 0
                                   and x.get("verified_route_epoch_price_cross_count", 0)
                                   == x.get("conditional_crossed_leg_count", 0)
                                   for x in values)
            candidates[shape] = {"paired_count": len(values), "modeled_count": modeled,
                                 "winner_comparable_count": len(winner_comparable),
                                 "winner_weighted_conservative_ev_pct": (
                                     round(weighted_candidate, 6)
                                     if weighted_candidate is not None else None),
                                 "price_cross_count": crossed,
                                 "verified_route_epoch_price_cross_count": verified_crossed,
                                 "price_touch_only_count": sum(x.get("fill_state") == "price_touch_only" for x in values),
                                 "no_cross_observed_count": sum(x.get("fill_state") == "no_cross_observed" for x in values),
                                 "coverage_of_type": round(len(values) / type_trade_counts[quantity_type], 6)
                                     if type_trade_counts[quantity_type] else 0.0,
                                 "coverage_of_all_completed": round(len(values) / len(trades), 6)
                                     if trades else 0.0,
                                 "estimated_ev_pct": round(estimate, 6) if estimate is not None else None,
                                 "conservative_ev_pct": round(lower, 6) if lower is not None else None,
                                 "actual_parent_net_pnl_krw": round(incumbent_net, 3),
                                 "estimated_net_pnl_krw": round(estimated_net, 3),
                                 "conservative_net_pnl_krw": round(conservative_net, 3),
                                 "missing_paths_carry_parent": max(0, len(incumbent) - len(values)),
                                 "state": "paired_with_parent_fallback"}
        best = _select_initial_winner_shape(quantity_type, candidates)
        selections[quantity_type] = {"selected_shape": best, "parent_ev_pct": incumbent_ev,
                                     "winner_weight_kind": "positive_realized_net_pnl_krw",
                                     "winner_count": len(winners),
                                     "winner_weight_sum_krw": round(winner_weight, 3),
                                     "winner_weighted_parent_ev_pct": (
                                         round(weighted_parent, 6)
                                         if weighted_parent is not None else None),
                                     "candidate_metrics": candidates,
                                     "selection_reason": "initial_winner_weighted_shape" if best != "parent" else "parent_or_source_gap"}
    body = {"schema_version": REPORT_SCHEMA, "source_date": as_of,
            "classifier_version": CLASSIFIER_VERSION,
            "cost_model": COST_MODEL,
            "generation_kind": ("refresh_post_apply_replay" if entry_on_or_after
                                else "initial_completed_trade_seed"),
            "runtime_effect": False, "runtime_apply_allowed": False,
            "actual_order_submitted": False, "broker_order_forbidden": True,
            "census": census, "replay_counts": dict(sorted(counts.items())),
            "pipeline_source_receipts": source_receipts,
            "quantity_type_counts": dict(sorted(Counter(
                row["quantity_type"] for row in rows).items())),
            "selections": selections, "trades": rows,
            "model_limitations": ["fixed_actual_exit", "conditional_price_cross_is_not_broker_fill",
                                   "quantity_expansion_not_estimated", "unclocked_price_excluded",
                                   "decision_and_fill_join_within_one_hour_of_fact_buy_time"]}
    if performance is not None:
        usage_end = resource.getrusage(resource.RUSAGE_SELF)
        wait_end = _block_io_wait_ms()
        performance.update({
            "wall_seconds": round(time.perf_counter() - started, 3),
            "cpu_user_seconds": round(usage_end.ru_utime - usage_start.ru_utime, 3),
            "cpu_system_seconds": round(usage_end.ru_stime - usage_start.ru_stime, 3),
            "peak_rss_kb": usage_end.ru_maxrss,
            "swap_operations": usage_end.ru_nswap - usage_start.ru_nswap,
            "read_blocks": usage_end.ru_inblock - usage_start.ru_inblock,
            "write_blocks": usage_end.ru_oublock - usage_start.ru_oublock,
            "block_io_wait_ms": (round(wait_end - wait_start, 3)
                                 if wait_start is not None and wait_end is not None else None),
            "trade_evaluation_p95_ms": (_pctl(trade_seconds, 0.95) or 0.0) * 1000.0,
            "trade_evaluation_p99_ms": (_pctl(trade_seconds, 0.99) or 0.0) * 1000.0,
            "date_scan_seconds": date_scan_seconds,
            "census_count": census["all_completed_initial_trades"],
        })
    return {**body, "report_content_sha256": _digest(body)}


def build_initial_quantity_policy(
    report: dict[str, Any], *, following_bars: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal a candidate type policy; activation remains a separate handoff."""
    source_date = str(report.get("source_date") or "")
    date.fromisoformat(source_date)
    if (report.get("schema_version") != REPORT_SCHEMA
            or report.get("generation_kind") != "initial_completed_trade_seed"
            or report.get("cost_model") != COST_MODEL
            or report.get("report_content_sha256") != _digest({
                k: v for k, v in report.items() if k != "report_content_sha256"})):
        raise ValueError("initial_replay_integrity_invalid")
    census = report.get("census") or {}
    if census.get("census_source") != "trade_performance_facts":
        raise ValueError("completed_trade_fact_source_required")
    if census.get("input_manifest_sha256") != _digest(census.get("input_fact_rows")):
        raise ValueError("trade_fact_manifest_invalid")
    if not isinstance(census.get("all_completed_initial_trades"), int) or census["all_completed_initial_trades"] <= 0:
        raise ValueError("completed_trade_census_empty")
    if (report.get("replay_counts") or {}).get("parent:paired", 0) <= 0:
        raise ValueError("completed_parent_economics_missing")
    if not initial_replay_economics_valid(report):
        raise ValueError("initial_replay_economics_invalid")
    if following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import (
            following_bar_source_valid,
        )
        if not following_bar_source_valid(following_bars, report):
            raise ValueError("following_bar_source_invalid")
    selections = report.get("selections") or {}
    if set(selections) != set(_TYPES):
        raise ValueError("quantity_type_coverage_invalid")
    types: dict[str, Any] = {}
    for quantity_type in _TYPES:
        row = selections[quantity_type]
        shape = row.get("selected_shape")
        if shape not in _SHAPES:
            raise ValueError("selected_shape_not_allowlisted")
        metric = (row.get("candidate_metrics") or {}).get(shape) or {}
        if quantity_type == "SAFE_UNKNOWN" and shape != "parent":
            raise ValueError("unknown_type_must_keep_parent")
        if shape != "parent" and (metric.get("state") != "paired_with_parent_fallback"
                                  or not isinstance(metric.get("paired_count"), int)
                                  or metric.get("winner_comparable_count", 0) < 1):
            raise ValueError("selected_shape_pairing_missing")
        types[quantity_type] = {"ratio_mode": "parent_5stage",
                                "selected_shape": shape,
                                "selection_reason": row.get("selection_reason"),
                                "paired_count": metric.get("paired_count", 0),
                                "winner_weight_kind": "positive_realized_net_pnl_krw",
                                "winner_count": row.get("winner_count", 0),
                                "winner_weight_sum_krw": row.get("winner_weight_sum_krw", 0),
                                "winner_weighted_parent_ev_pct": row.get(
                                    "winner_weighted_parent_ev_pct"),
                                "winner_weighted_selected_ev_pct": metric.get(
                                    "winner_weighted_conservative_ev_pct"),
                                "timeout_mode": "existing_runtime_profile",
                                "selected_total_wait_sec": None,
                                **({"following_lower_observed_minute_count":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "observed_minute_lower_count", 0),
                                    "following_weighted_lower_from_fill_minute":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "weighted_lower_elapsed_from_fill_minute"),
                                    "following_order_start_linked_count":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "order_start_linked_count", 0),
                                    "following_weighted_lower_from_order_start_minute":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "weighted_lower_elapsed_from_order_start_minute")}
                                   if following_bars is not None else {})}
    core = {"schema_version": POLICY_SCHEMA, "generation_kind": "initial_completed_trade_seed",
            "classifier_version": CLASSIFIER_VERSION,
            "policy_owner": "entry_execution_sizing_owner",
            "source_date": source_date,
            "effective_from": (date.fromisoformat(source_date) + timedelta(days=1)).isoformat(),
            "report_content_sha256": report["report_content_sha256"],
            **({"following_bar_source_content_sha256":
                following_bars["report_content_sha256"]}
               if following_bars is not None else {}),
            "input_manifest_sha256": census.get("input_manifest_sha256"),
            "census_source": "trade_performance_facts",
            "all_completed_initial_trades": census["all_completed_initial_trades"],
            "type_policies": types,
            "action_authority": False, "price_authority": False,
            "scale_in_authority": False, "quantity_cap_relaxation": False,
            "runtime_effect": False, "runtime_apply_allowed": False,
            "actual_order_submitted": False, "broker_order_forbidden": True,
            "activation_state": "candidate_requires_contract_migration_and_preopen_validation"}
    body = {**core, "policy_version": f"initial-type-{source_date}-{_digest(core)[:12]}"}
    policy = {**body, "policy_content_sha256": _digest(body)}
    if not initial_quantity_policy_valid(policy, report=report,
                                         following_bars=following_bars):
        raise ValueError("initial_policy_self_validation_failed")
    return policy


def initial_replay_economics_valid(report: Any) -> bool:
    """Check parent conservation and ordering of conditional EV bounds."""
    def metric(value: Any) -> bool:
        return type(value) in (int, float) and math.isfinite(value)

    if not isinstance(report, dict):
        return False
    if (report.get("generation_kind") == "refresh_post_apply_replay"
            and report.get("cost_model") != COST_MODEL):
        return False
    if report.get("cost_model") not in (None, COST_MODEL):
        return False
    rows = report.get("trades")
    census = report.get("census") or {}
    if (not isinstance(rows, list)
            or len(rows) != census.get("all_completed_initial_trades")):
        return False
    seen: set[str] = set()
    counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    paired_by_type: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list))
    rows_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("shapes"), dict):
            return False
        trade_id = str(row.get("trade_id") or "")
        if not trade_id or trade_id in seen or set(row["shapes"]) != set(_SHAPES):
            return False
        seen.add(trade_id)
        quantity_type = row.get("quantity_type")
        if quantity_type not in _TYPES:
            return False
        type_counts[quantity_type] += 1
        rows_by_type[quantity_type].append(row)
        parent = row["shapes"]["parent"]
        if (not isinstance(parent, dict)
                or not metric(row.get("actual_profit_rate"))
                or not metric(row.get("actual_net_pnl_krw"))):
            return False
        if parent.get("status") == "paired" and (
            not metric(parent.get("candidate_net_pct"))
            or not metric(parent.get("candidate_net_pnl_krw"))
            or abs(parent["candidate_net_pct"] - row["actual_profit_rate"]) > 1e-6
            or abs(parent["candidate_net_pnl_krw"] - row["actual_net_pnl_krw"]) > 1e-3
        ):
            return False
        for shape, result in row["shapes"].items():
            if not isinstance(result, dict):
                return False
            status = result.get("status")
            counts[f"{shape}:{status}"] += 1
            if status == "paired":
                paired_by_type[quantity_type][shape].append(result)
            if status != "paired" or shape == "parent":
                continue
            if result.get("quantity_type") != row.get("quantity_type"):
                return False
            for key in ("conservative_net_pct", "candidate_net_pct", "upper_net_pct",
                        "conservative_net_pnl_krw", "candidate_net_pnl_krw",
                        "upper_net_pnl_krw", "parent_net_pnl_krw"):
                if not metric(result.get(key)):
                    return False
            if (result["conservative_net_pct"] > result["candidate_net_pct"] + 1e-6
                    or result["candidate_net_pct"] > result["upper_net_pct"] + 1e-6
                    or result["conservative_net_pnl_krw"] > result["candidate_net_pnl_krw"] + 0.001
                    or result["candidate_net_pnl_krw"] > result["upper_net_pnl_krw"] + 0.001):
                return False
            if result.get("fill_state") == "quantity_too_small_parent_fallback":
                if abs(result["candidate_net_pnl_krw"] - row["actual_net_pnl_krw"]) > 0.001:
                    return False
            else:
                original_notional = _number(result.get("candidate_notional_denominator_krw"))
                if (not original_notional or original_notional <= 0
                        or abs(result["candidate_net_pct"] -
                               result["candidate_net_pnl_krw"] / original_notional * 100) > 0.001):
                    return False
    if (dict(sorted(counts.items())) != report.get("replay_counts")
            or dict(sorted(type_counts.items())) != report.get("quantity_type_counts")):
        return False
    selections = report.get("selections")
    if not isinstance(selections, dict) or set(selections) != set(_TYPES):
        return False
    for quantity_type in _TYPES:
        selection = selections[quantity_type]
        if not isinstance(selection, dict):
            return False
        metrics = selection.get("candidate_metrics")
        if not isinstance(metrics, dict) or set(metrics) != set(_SHAPES):
            return False
        parent = paired_by_type[quantity_type]["parent"]
        parent_ev = sum(x["candidate_net_pct"] for x in parent) / len(parent) if parent else None
        parent_net = sum(x["parent_net_pnl_krw"] for x in parent)
        if selection.get("winner_weight_kind") is not None:
            winners = [row for row in rows_by_type[quantity_type]
                       if row["actual_net_pnl_krw"] > 0
                       and row["actual_profit_rate"] > 0]
            weight = sum(row["actual_net_pnl_krw"] for row in winners)
            weighted_parent = (sum(row["actual_profit_rate"] * row["actual_net_pnl_krw"]
                                   for row in winners) / weight if weight else None)
            if (selection.get("winner_weight_kind") != "positive_realized_net_pnl_krw"
                    or selection.get("winner_count") != len(winners)
                    or not metric(selection.get("winner_weight_sum_krw"))
                    or abs(selection["winner_weight_sum_krw"] - weight) > 0.002
                    or ((weighted_parent is None) !=
                        (selection.get("winner_weighted_parent_ev_pct") is None))
                    or weighted_parent is not None and abs(
                        selection["winner_weighted_parent_ev_pct"] - weighted_parent) > 1e-6):
                return False
            for shape in _SHAPES:
                comparable = [row for row in winners
                              if row["shapes"][shape].get("status") == "paired"]
                ids = {row["trade_id"] for row in comparable}
                weighted = (sum(row["actual_net_pnl_krw"] * (
                    row["shapes"][shape].get("conservative_net_pct",
                                              row["actual_profit_rate"])
                    if row["trade_id"] in ids else row["actual_profit_rate"])
                    for row in winners) / weight if weight else None)
                metric_row = metrics[shape]
                if (metric_row.get("winner_comparable_count") != len(comparable)
                        or ((weighted is None) !=
                            (metric_row.get("winner_weighted_conservative_ev_pct") is None))
                        or weighted is not None and abs(
                            metric_row["winner_weighted_conservative_ev_pct"] - weighted) > 1e-6):
                    return False
        if ((parent_ev is None) != (selection.get("parent_ev_pct") is None)
                or parent_ev is not None and abs(parent_ev - selection["parent_ev_pct"]) > 1e-6):
            return False
        for shape in _SHAPES:
            values = paired_by_type[quantity_type][shape]
            metric_row = metrics[shape]
            if not isinstance(metric_row, dict) or metric_row.get("paired_count") != len(values):
                return False
            if not values:
                if metric_row.get("state") != "no_comparable_trade":
                    return False
                continue
            expected_modeled = sum(value.get("fill_state") in {
                "price_cross_conditional", "price_touch_only", "no_cross_observed"}
                for value in values)
            expected_crossed = sum(value.get("fill_state") == "price_cross_conditional"
                                   for value in values)
            expected_verified = sum(
                value.get("verified_route_epoch_price_cross_count", 0) > 0
                and value.get("verified_route_epoch_price_cross_count", 0)
                == value.get("conditional_crossed_leg_count", 0)
                for value in values)
            if (metric_row.get("modeled_count") != expected_modeled
                    or metric_row.get("price_cross_count") != expected_crossed
                    or metric_row.get("verified_route_epoch_price_cross_count") != expected_verified
                    or metric_row.get("price_touch_only_count") != sum(
                        value.get("fill_state") == "price_touch_only" for value in values)
                    or metric_row.get("no_cross_observed_count") != sum(
                        value.get("fill_state") == "no_cross_observed" for value in values)):
                return False
            expected_coverage = len(values) / type_counts[quantity_type]
            expected_global_coverage = len(values) / len(rows)
            expected_net = parent_net + sum(
                value["candidate_net_pnl_krw"] - value["parent_net_pnl_krw"]
                for value in values)
            expected_conservative_net = parent_net + sum(
                value.get("conservative_net_pnl_krw", value["candidate_net_pnl_krw"])
                - value["parent_net_pnl_krw"]
                for value in values)
            expected_ev = parent_ev + sum(
                value["candidate_net_pct"] - value.get("parent_net_pct", value["candidate_net_pct"])
                for value in values) / len(parent)
            expected_conservative_ev = parent_ev + sum(
                value.get("conservative_net_pct", value["candidate_net_pct"])
                - value.get("parent_net_pct", value["candidate_net_pct"])
                for value in values) / len(parent)
            if (not metric(metric_row.get("coverage_of_type"))
                    or abs(metric_row["coverage_of_type"] - expected_coverage) > 1e-6
                    or not metric(metric_row.get("coverage_of_all_completed"))
                    or abs(metric_row["coverage_of_all_completed"] - expected_global_coverage) > 1e-6
                    or not metric(metric_row.get("estimated_net_pnl_krw"))
                    or abs(metric_row["estimated_net_pnl_krw"] - expected_net) > 0.002
                    or not metric(metric_row.get("conservative_net_pnl_krw"))
                    or abs(metric_row["conservative_net_pnl_krw"] - expected_conservative_net) > 0.002
                    or not metric(metric_row.get("estimated_ev_pct"))
                    or abs(metric_row["estimated_ev_pct"] - expected_ev) > 1e-6
                    or not metric(metric_row.get("conservative_ev_pct"))
                    or abs(metric_row["conservative_ev_pct"] - expected_conservative_ev) > 1e-6):
                return False
        selected = selection.get("selected_shape")
        if (selected not in _SHAPES
                or selected != _select_initial_winner_shape(
                    quantity_type, metrics)
                or selection.get("selection_reason") != (
                    "initial_winner_weighted_shape" if selected != "parent"
                    else "parent_or_source_gap")):
            return False
    return True


def _eligible_refresh_total_wait(
    report: dict[str, Any], timeout_research: dict[str, Any] | None,
    quantity_type: str, shape: str, minimum_count: int,
) -> int | None:
    """Choose a bounded T only with exact start clocks and dated EV support."""
    if shape == "parent" or not isinstance(timeout_research, dict):
        return None
    selection = (timeout_research.get("selections") or {}).get(quantity_type) or {}
    source_rows = [row for row in report.get("trades") or []
                   if row.get("quantity_type") == quantity_type]
    parent_net = sum(row["actual_net_pnl_krw"] for row in source_rows)
    parent_ev = _number(selection.get("parent_costed_ev_pct"))
    if parent_ev is None or len(source_rows) < minimum_count:
        return None
    ranked = []
    for horizon in timeout_research.get("horizons_sec") or []:
        if (type(horizon) is not int or horizon > 1200
                or horizon < 6 * (3 if shape.startswith("three_leg") else 2)):
            continue
        metric = (selection.get("candidate_metrics") or {}).get(
            f"{shape}:5:{horizon}") or {}
        modeled = metric.get("modeled_count")
        daily = metric.get("daily_conservative_delta_net_pnl_krw") or {}
        ev = _number(metric.get("conservative_ev_pct"))
        net = _number(metric.get("conservative_net_pnl_krw"))
        if (type(modeled) is not int or modeled < minimum_count
                or modeled / len(source_rows) < 0.8
                or (metric.get("order_start_source_counts") or {}) != {
                    "initial_quantity_bundle_order_start_at": modeled}
                or metric.get("verified_cross_count", 0) <
                    max(3, math.ceil(modeled * 0.05))
                or ev is None or ev <= parent_ev + 0.10
                or net is None or net <= parent_net
                or not isinstance(daily, dict) or len(daily) < 3
                or min(daily.values()) < 0
                or daily[max(daily)] <= 0):
            continue
        ranked.append((ev, net, -horizon, horizon))
    return max(ranked)[-1] if ranked else None


def evaluate_refresh_quantity_candidate(
    report: dict[str, Any], *, parent_policy: dict[str, Any],
    pid_receipt: dict[str, Any] | None = None,
    terminal_receipt: dict[str, Any] | None = None,
    following_bars: dict[str, Any] | None = None,
    timeout_research: dict[str, Any] | None = None,
    parent_policy_file_sha256: str | None = None,
    enforce_trade_lineage: bool = True,
) -> dict[str, Any]:
    """Apply stronger post-activation gates without reusing the seed sample."""
    from src.engine.scalping.initial_quantity_activation import (
        RUNTIME_REFRESH_SCHEMA, baseline_policy_valid,
        refresh_parent_policy_valid,
    )

    if not isinstance(parent_policy, dict) or not isinstance(report, dict):
        raise ValueError("refresh_parent_or_replay_contract_invalid")
    parent_body = {key: value for key, value in parent_policy.items()
                   if key != "policy_content_sha256"}
    report_body = {key: value for key, value in report.items()
                   if key != "report_content_sha256"}
    is_initial_baseline = baseline_policy_valid(parent_policy)
    is_v2_parent = (refresh_parent_policy_valid(parent_policy)
                    and not is_initial_baseline)
    is_legacy_parent = (
        parent_policy.get("policy_content_sha256") == _digest(parent_body)
        and parent_policy.get("runtime_apply_allowed") is True
        and parent_policy.get("runtime_effect") is True
        and parent_policy.get("activation_state") == "reviewed_active"
        and isinstance(parent_policy.get("type_policies"), dict)
        and set(parent_policy["type_policies"]) == set(_TYPES)
        and all(type(row) is dict and type(row.get("paired_count")) is int
                and row["paired_count"] >= 0
                for row in parent_policy["type_policies"].values())
    )
    if (not (is_initial_baseline or is_v2_parent or is_legacy_parent)
            or report.get("report_content_sha256") != _digest(report_body)
            or report.get("generation_kind") != "refresh_post_apply_replay"
            or report.get("schema_version") != REPORT_SCHEMA
            or not initial_replay_economics_valid(report)
            or (report.get("census") or {}).get("entry_on_or_after")
            != parent_policy.get("effective_from")
            or len(report.get("trades") or [])
            != (report.get("census") or {}).get("all_completed_initial_trades")
            or any(str(row.get("entry_date") or "") < str(parent_policy.get("effective_from") or "")
                   for row in report.get("trades") or [])
            or (report.get("census") or {}).get("input_manifest_sha256")
            != _digest((report.get("census") or {}).get("input_fact_rows"))):
        raise ValueError("refresh_parent_or_replay_contract_invalid")
    if following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import (
            following_bar_source_valid,
        )
        if not following_bar_source_valid(following_bars, report):
            raise ValueError("refresh_following_source_invalid")
    if timeout_research is not None:
        from src.engine.scalping.initial_quantity_timeout_research import (
            timeout_research_valid,
        )
        if (not timeout_research_valid(timeout_research)
                or timeout_research.get("source_date") != report.get("source_date")
                or timeout_research.get("census") != report.get("census")):
            raise ValueError("refresh_timeout_source_invalid")
    parent_hash = parent_policy["policy_content_sha256"]
    entry_dates = sorted({row["entry_date"] for row in report.get("trades") or []})
    blockers = []
    expected_parent_status = (
        "initial_policy_refresh_loaded"
        if parent_policy.get("schema_version") == RUNTIME_REFRESH_SCHEMA else
        "initial_policy_v2_loaded" if is_v2_parent else
        "initial_policy_loaded")
    daily_pid_rows = (pid_receipt.get("daily_pid_receipts")
                      if isinstance(pid_receipt, dict) else None)
    pid_by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pid_row in daily_pid_rows if isinstance(daily_pid_rows, list) else []:
        if isinstance(pid_row, dict):
            pid_by_day[str(pid_row.get("entry_date") or "")].append(pid_row)
    pid_days_valid = (set(pid_by_day) == set(entry_dates)
                      and all(type(item.get("pid")) is int
                              and item["pid"] > 0
                              and _timestamp(item.get("verified_at")) is not None
                              for rows in pid_by_day.values() for item in rows))
    policy_bound_trades = sum(
        row.get("applied_policy_status") == expected_parent_status
        and row.get("applied_policy_file_sha256") == parent_policy_file_sha256
        and row.get("policy_decision_stage") == "entry_execution_sizing_plan"
        and (decision_at := _timestamp(row.get("policy_decision_at"))) is not None
        and (entry_at := _timestamp(row.get("entry_fill_at"))) is not None
        and decision_at <= entry_at
        and (not pid_receipt or pid_days_valid and any(
            str(row.get("applied_policy_runtime_pid") or "") ==
            str(pid_row["pid"])
            and _timestamp(pid_row["verified_at"]) <= decision_at
            for pid_row in pid_by_day[row["entry_date"]]))
        for row in report.get("trades") or [])
    if (enforce_trade_lineage and report.get("trades")
            and policy_bound_trades != len(report["trades"])):
        blockers.append("parent_trade_policy_binding_missing")
    if following_bars is None and any(
            row["actual_net_pnl_krw"] > 0 and row["actual_profit_rate"] > 0
            for row in report["trades"]):
        blockers.append("winner_following_source_missing")
    if len(entry_dates) < 3:
        blockers.append("independent_post_apply_dates_below_three")
    if not (isinstance(pid_receipt, dict)
            and pid_receipt.get("actual_pid_consumed") is True
            and pid_receipt.get("policy_content_sha256") == parent_hash
            and pid_days_valid
            and str(pid_receipt.get("first_consumed_date") or "") <= (entry_dates[0] if entry_dates else "")):
        blockers.append("parent_pid_consumption_missing")
    if not (isinstance(terminal_receipt, dict)
            and terminal_receipt.get("terminal") is True
            and terminal_receipt.get("costed_completed_trade_count")
            == (report.get("census") or {}).get("all_completed_initial_trades")
            and terminal_receipt.get("report_content_sha256") == report["report_content_sha256"]):
        blockers.append("post_apply_terminal_cost_binding_missing")
    type_decisions = {}
    for quantity_type in _TYPES:
        selection = (report.get("selections") or {}).get(quantity_type) or {}
        incumbent = (selection.get("candidate_metrics") or {}).get("parent") or {}
        parent_count = incumbent.get("paired_count", 0)
        seeded_count = ((parent_policy.get("type_policies") or {}).get(quantity_type) or {}).get(
            "paired_count", 0)
        # The active first baseline intentionally stores no per-type training
        # count. Never turn that absent count into the five-trade refresh floor.
        minimum_count = (30 if is_initial_baseline or is_v2_parent else
                         max(5, min(30, math.ceil(seeded_count * 0.2))))
        incumbent_shape = str((parent_policy.get("type_policies") or {}).get(
            quantity_type, {}).get("selected_shape") or "parent")
        best = incumbent_shape
        best_ev = _number(selection.get("parent_ev_pct"))
        reasons = []
        for shape, metric in (selection.get("candidate_metrics") or {}).items():
            if shape == incumbent_shape or shape not in _SHAPES:
                continue
            if shape == "parent":
                # In the replay, the parent arm is the actual applied trade.
                # It cannot be treated as an independent counterfactual that
                # justifies reverting an already active non-parent shape.
                continue
            if (type(metric.get("paired_count")) is not int
                    or metric["paired_count"] < minimum_count
                    or _number(metric.get("coverage_of_type")) is None
                    or metric["coverage_of_type"] < 0.8
                    or metric.get("verified_route_epoch_price_cross_count", 0) < 1
                    or _number(metric.get("conservative_ev_pct")) is None
                    or _number(selection.get("parent_ev_pct")) is None
                    or metric["conservative_ev_pct"] <= selection["parent_ev_pct"] + 0.10):
                continue
            rows = [row for row in report.get("trades") or []
                    if row.get("quantity_type") == quantity_type]
            daily_delta: dict[str, float] = defaultdict(float)
            for row in rows:
                daily_delta[row["entry_date"]] += 0.0
                result = (row.get("shapes") or {}).get(shape) or {}
                if result.get("status") == "paired":
                    daily_delta[row["entry_date"]] += (
                        result["candidate_net_pnl_krw"] - result["parent_net_pnl_krw"])
            if len(daily_delta) < 3 or min(daily_delta.values()) < 0 or daily_delta[max(daily_delta)] <= 0:
                continue
            if best_ev is None or metric["conservative_ev_pct"] > best_ev:
                best = shape
                best_ev = metric["conservative_ev_pct"]
        if best == incumbent_shape:
            reasons.append("refresh_hurdles_or_evidence_not_met")
        elif following_bars is not None:
            following = (following_bars.get("weighted_by_type") or {}).get(
                quantity_type) or {}
            winner_count = selection.get("winner_count", 0)
            observed = following.get("observed_minute_lower_count", 0)
            if (type(winner_count) is not int or winner_count <= 0
                    or type(observed) is not int
                    or observed / winner_count < 0.8):
                best = incumbent_shape
                reasons.append("winner_following_lower_coverage_below_80pct")
        selected_wait = _eligible_refresh_total_wait(
            report, timeout_research, quantity_type, best, minimum_count)
        parent_row = parent_policy["type_policies"][quantity_type]
        if (selected_wait is not None
                and parent_row.get("timeout_mode") == "selected_total_wait_sec"
                and parent_row.get("selected_total_wait_sec") == selected_wait):
            selected_wait = None
        type_decisions[quantity_type] = {"selected_shape": best,
                                         "selected_total_wait_sec": selected_wait,
                                         "minimum_completed_count": minimum_count,
                                         "observed_completed_count": parent_count,
                                         "reason": reasons[0] if reasons else "post_apply_hurdles_passed"}
    state = ("eligible_source_only" if not blockers and any(
        row["selected_shape"] != (parent_policy["type_policies"][name].get(
            "selected_shape") or "parent")
        or row["selected_total_wait_sec"] is not None
        for name, row in type_decisions.items())
             else "carry_parent")
    return {"schema_version": "initial_entry_quantity_refresh_evaluation_v1",
            "generation_kind": "refresh", "source_date": report["source_date"],
            "parent_policy_content_sha256": parent_hash,
            "report_content_sha256": report["report_content_sha256"],
            "state": state, "global_blockers": blockers,
            **({"parent_policy_bound_trade_count": policy_bound_trades}
               if enforce_trade_lineage else {}),
            "type_decisions": type_decisions,
            "runtime_apply_allowed": False, "runtime_effect": False}


def _natural_refresh_pid_receipt(
    report: dict[str, Any], parent_policy: dict[str, Any],
    parent_policy_path: Path, data_dir: Path,
) -> dict[str, Any] | None:
    """Read each entry day's verified Main PID/environment handoff.

    A selected release or a PREOPEN manifest alone is insufficient. Missing
    daily PID proof leaves the refresh evaluator's existing blocker in place.
    """
    from src.engine.scalping.initial_quantity_activation import ENV_FILE, ENV_SHA

    days = sorted({row["entry_date"] for row in report.get("trades") or []})
    if not days:
        return None
    parent_file_sha = _file_sha256(parent_policy_path)
    bootstrap_dir = data_dir / "runtime" / "policy_bootstrap"
    receipts = []
    for day in days:
        archived = []
        archive_dir = bootstrap_dir / "verified_initial_quantity_pid" / day
        for archive_path in sorted(archive_dir.glob("initial_quantity_pid_*.json")):
            try:
                archive = json.loads(archive_path.read_text(encoding="utf-8"))
                archive_sha = _file_sha256(archive_path)
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(archive, dict):
                continue
            archive_body = {key: value for key, value in archive.items()
                            if key != "receipt_content_sha256"}
            verify = archive.get("verification") or {}
            verified_at = _timestamp(archive.get("verified_at"))
            if (archive.get("schema_version") !=
                    "initial_quantity_pid_verification_v1"
                    or archive.get("receipt_content_sha256") !=
                    _digest(archive_body)
                    or archive_path.name !=
                    f"initial_quantity_pid_{archive.get('pid')}_"
                    f"{archive['receipt_content_sha256'][:12]}.json"
                    or archive.get("target_date") != day
                    or verified_at is None or verified_at.date().isoformat() != day
                    or archive.get("policy_file_sha256") != parent_file_sha
                    or archive.get("policy_content_sha256") !=
                    parent_policy["policy_content_sha256"]
                    or Path(str(archive.get("policy_file") or "")).resolve()
                    != parent_policy_path.resolve()
                    or not isinstance(verify, dict)
                    or verify.get("pid_passed") is not True
                    or verify.get("status") != "pass"
                    or verify.get("passed") is not True
                    or verify.get("pid_env_available") is not True
                    or verify.get("pid") != archive.get("pid")
                    or verify.get("target_date") != day
                    or verify.get("verified_at") != archive.get("verified_at")
                    or verify.get("manifest_sha256") !=
                    archive.get("manifest_sha256")
                    or verify.get("findings") != []
                    or verify.get("pid_mismatches") != []):
                continue
            archived.append({"entry_date": day, "pid": archive["pid"],
                             "verified_at": archive["verified_at"],
                             "archive_path": str(archive_path.resolve()),
                             "archive_file_sha256": archive_sha})
        if archived:
            receipts.extend(archived)
            continue
        manifest_path = bootstrap_dir / f"runtime_policy_bootstrap_{day}.json"
        verify_path = bootstrap_dir / f"runtime_policy_bootstrap_verify_{day}.json"
        env_path = bootstrap_dir / f"runtime_policy_bootstrap_{day}.env"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            verify = json.loads(verify_path.read_text(encoding="utf-8"))
            env_sha = _file_sha256(env_path)
            manifest_file_sha = _file_sha256(manifest_path)
            verify_file_sha = _file_sha256(verify_path)
        except (OSError, ValueError, TypeError):
            return None
        if not isinstance(manifest, dict) or not isinstance(verify, dict):
            return None
        manifest_body = {key: value for key, value in manifest.items()
                         if key != "manifest_sha256"}
        policy_receipt = manifest.get("initial_quantity_policy_receipt") or {}
        env = manifest.get("env_overrides") or {}
        if (manifest.get("target_date") != day
                or manifest.get("manifest_sha256") != _digest(manifest_body)
                or Path(str(manifest.get("env_file") or "")).resolve()
                != env_path.resolve()
                or manifest.get("env_sha256") != env_sha
                or not isinstance(policy_receipt, dict)
                or policy_receipt.get("policy_file_sha256") != parent_file_sha
                or env.get(ENV_FILE) != str(parent_policy_path.resolve())
                or env.get(ENV_SHA) != parent_file_sha
                or verify.get("target_date") != day
                or verify.get("manifest_sha256") != manifest["manifest_sha256"]
                or Path(str(verify.get("manifest_file") or "")).resolve()
                != manifest_path.resolve()
                or Path(str(verify.get("env_file") or "")).resolve()
                != env_path.resolve()
                or (_timestamp(verify.get("verified_at")) is None
                    or _timestamp(verify["verified_at"]).date().isoformat() != day)
                or verify.get("status") != "pass"
                or verify.get("passed") is not True
                or verify.get("pid_passed") is not True
                or verify.get("pid_env_available") is not True
                or type(verify.get("pid")) is not int
                or verify["pid"] <= 0
                or verify.get("findings") != []
                or verify.get("pid_mismatches") != []):
            return None
        receipts.append({"entry_date": day, "pid": verify["pid"],
                         "verified_at": verify["verified_at"],
                         "manifest_file_sha256": manifest_file_sha,
                         "verify_file_sha256": verify_file_sha,
                         "env_file_sha256": env_sha})
    return {"actual_pid_consumed": True,
            "policy_content_sha256": parent_policy["policy_content_sha256"],
            "policy_file_sha256": parent_file_sha,
            "first_consumed_date": days[0], "daily_pid_receipts": receipts,
            "data_root": str(data_dir.resolve()),
            "source": "verified_daily_preopen_main_pid_env"}


def _natural_refresh_terminal_receipt(report: dict[str, Any]) -> dict[str, Any]:
    """Bind the already validated completed costed fact census to replay."""
    census = report["census"]
    return {"terminal": True,
            "costed_completed_trade_count": census["all_completed_initial_trades"],
            "report_content_sha256": report["report_content_sha256"],
            "input_manifest_sha256": census["input_manifest_sha256"],
            "source": "trade_performance_facts_completed_costed"}


def build_refresh_type_policy_candidate(
    report: dict[str, Any], evaluation: dict[str, Any],
    parent_policy: dict[str, Any], timeout_research: dict[str, Any],
) -> dict[str, Any]:
    """Seal eligible type choices without granting runtime or order authority."""
    if not all(isinstance(value, dict) for value in (
            report, evaluation, parent_policy, timeout_research)):
        raise ValueError("refresh_type_candidate_source_invalid")
    from src.engine.scalping.initial_quantity_activation import (
        refresh_parent_policy_valid,
    )
    from src.engine.scalping.initial_quantity_timeout_research import (
        timeout_research_valid,
    )

    decisions = evaluation.get("type_decisions") or {}
    timeout_types = timeout_research.get("selections") or {}
    if (report.get("generation_kind") != "refresh_post_apply_replay"
            or report.get("cost_model") != COST_MODEL
            or report.get("report_content_sha256") != _digest({
                key: value for key, value in report.items()
                if key != "report_content_sha256"})
            or not refresh_parent_policy_valid(parent_policy)
            or not timeout_research_valid(timeout_research)
            or evaluation.get("state") != "eligible_source_only"
            or evaluation.get("global_blockers")
            or evaluation.get("report_content_sha256") !=
            report["report_content_sha256"]
            or evaluation.get("parent_policy_content_sha256") !=
            parent_policy["policy_content_sha256"]
            or set(decisions) != set(_TYPES)
            or set(timeout_types) != set(_TYPES)
            or timeout_research.get("source_date") != report.get("source_date")
            or timeout_research.get("census") != report.get("census")):
        raise ValueError("refresh_type_candidate_source_invalid")
    types = {}
    for name in _TYPES:
        shape = decisions[name].get("selected_shape")
        if (shape not in _SHAPES
                or (name == "SAFE_UNKNOWN" and shape != "parent")):
            raise ValueError("refresh_type_candidate_shape_invalid")
        selected_wait = decisions[name].get("selected_total_wait_sec")
        if (selected_wait is not None and selected_wait !=
                _eligible_refresh_total_wait(
                    report, timeout_research, name, shape,
                    decisions[name]["minimum_completed_count"])):
            raise ValueError("refresh_type_candidate_timeout_unsupported")
        parent_row = parent_policy["type_policies"][name]
        if selected_wait is not None:
            timeout_mode = "selected_total_wait_sec"
        elif shape == parent_row.get("selected_shape", "parent"):
            timeout_mode = parent_row.get(
                "timeout_mode", "existing_runtime_profile")
            selected_wait = parent_row.get("selected_total_wait_sec")
        else:
            timeout_mode = "existing_runtime_profile"
        types[name] = {
            "ratio_mode": parent_row.get("ratio_mode", "parent_5stage"),
            "selected_shape": shape,
            "timeout_mode": timeout_mode,
            "selected_total_wait_sec": selected_wait,
        }
    if all(row == {
            "ratio_mode": parent_policy["type_policies"][name].get(
                "ratio_mode", "parent_5stage"),
            "selected_shape": parent_policy["type_policies"][name].get(
                "selected_shape", "parent"),
            "timeout_mode": parent_policy["type_policies"][name].get(
                "timeout_mode", "existing_runtime_profile"),
            "selected_total_wait_sec": parent_policy["type_policies"][name].get(
                "selected_total_wait_sec"),
        } for name, row in types.items()):
        raise ValueError("refresh_type_candidate_no_selected_change")
    body = {
        "schema_version": "initial_entry_quantity_refresh_candidate_v1",
        "generation_kind": "refresh_post_apply",
        "source_date": report["source_date"],
        "effective_from": (date.fromisoformat(report["source_date"])
                           + timedelta(days=1)).isoformat(),
        "cost_model": COST_MODEL,
        "parent_policy_content_sha256": parent_policy["policy_content_sha256"],
        "report_content_sha256": report["report_content_sha256"],
        "evaluation_content_sha256": _digest(evaluation),
        "timeout_research_content_sha256": timeout_research["report_content_sha256"],
        "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
        "type_policies": types,
        "runtime_apply_allowed": False,
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "price_authority": False,
        "quantity_cap_relaxation": False,
    }
    return {**body, "policy_content_sha256": _digest(body)}


def publish_refresh_quantity_evaluation(
    report: dict[str, Any], *, parent_policy: dict[str, Any],
    parent_policy_path: Path, output_dir: Path,
    pid_receipt: dict[str, Any] | None = None,
    terminal_receipt: dict[str, Any] | None = None,
    following_bars: dict[str, Any] | None = None,
    timeout_research: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal a post-apply replay and carry/eligible research decision.

    This receipt has no current-pointer or broker authority. A later reviewed
    policy publisher must consume it before any runtime change is possible.
    """
    from src.engine.scalping.initial_quantity_activation import (
        refresh_parent_policy_valid,
    )

    if (not parent_policy_path.is_absolute()
            or not refresh_parent_policy_valid(parent_policy)
            or json.loads(parent_policy_path.read_text(encoding="utf-8")) != parent_policy):
        raise ValueError("refresh_parent_file_invalid")
    if timeout_research is None:
        raise ValueError("refresh_timeout_research_required")
    winners = [row for row in report.get("trades") or []
               if row.get("actual_net_pnl_krw", 0) > 0
               and row.get("actual_profit_rate", 0) > 0]
    if winners or following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import (
            following_bar_source_valid,
        )
        if following_bars is None or not following_bar_source_valid(following_bars, report):
            raise ValueError("refresh_winner_following_source_required")
    if timeout_research is not None:
        from src.engine.scalping.initial_quantity_timeout_research import (
            timeout_research_valid,
        )
        if (not timeout_research_valid(timeout_research)
                or timeout_research.get("generation_kind") !=
                "refresh_post_apply_timeout_research"
                or timeout_research.get("source_date") != report.get("source_date")
                or timeout_research.get("entry_on_or_after") !=
                (report.get("census") or {}).get("entry_on_or_after")
                or timeout_research.get("census") != report.get("census")
                or timeout_research.get("quantity_type_counts") !=
                report.get("quantity_type_counts")
                or timeout_research.get("pipeline_source_receipts") !=
                report.get("pipeline_source_receipts")):
            raise ValueError("refresh_timeout_research_source_mismatch")
    evaluation = evaluate_refresh_quantity_candidate(
        report, parent_policy=parent_policy, pid_receipt=pid_receipt,
        terminal_receipt=terminal_receipt,
        following_bars=following_bars,
        timeout_research=timeout_research,
        parent_policy_file_sha256=_file_sha256(parent_policy_path))
    day = report["source_date"]
    report_path = output_dir / (
        f"initial_quantity_refresh_replay_{day}_{report['report_content_sha256'][:12]}.json")
    evaluation_hash = _digest(evaluation)
    evaluation_path = output_dir / (
        f"initial_quantity_refresh_evaluation_{day}_{evaluation_hash[:12]}.json")
    report_file_sha = _write_immutable_json(report_path, report)
    evaluation_file_sha = _write_immutable_json(evaluation_path, evaluation)
    candidate_receipt = {}
    if evaluation["state"] == "eligible_source_only":
        candidate = build_refresh_type_policy_candidate(
            report, evaluation, parent_policy, timeout_research)
        candidate_path = output_dir / (
            f"initial_quantity_refresh_candidate_{day}_"
            f"{candidate['policy_content_sha256'][:12]}.json")
        candidate_receipt = {
            "candidate_status": "source_only",
            "candidate_path": str(candidate_path.resolve()),
            "candidate_file_sha256": _write_immutable_json(
                candidate_path, candidate),
            "candidate_content_sha256": candidate["policy_content_sha256"],
        }
    following_receipt = {"following_bar_source_status": "no_winners"}
    if following_bars is not None:
        following_hash = following_bars["report_content_sha256"]
        following_path = output_dir / (
            f"initial_quantity_refresh_following_bars_{day}_{following_hash[:12]}.json")
        following_receipt = {
            "following_bar_source_status": "source_bound",
            "following_bar_source_path": str(following_path.resolve()),
            "following_bar_source_file_sha256": _write_immutable_json(
                following_path, following_bars),
            "following_bar_source_content_sha256": following_hash,
        }
    timeout_receipt = {"timeout_research_status": "not_provided"}
    if timeout_research is not None:
        timeout_hash = timeout_research["report_content_sha256"]
        timeout_path = output_dir / (
            f"initial_quantity_refresh_timeout_research_{day}_{timeout_hash[:12]}.json")
        timeout_receipt = {
            "timeout_research_status": "source_bound",
            "timeout_research_path": str(timeout_path.resolve()),
            "timeout_research_file_sha256": _write_immutable_json(
                timeout_path, timeout_research),
            "timeout_research_content_sha256": timeout_hash,
        }
    body = {
        "schema_version": "initial_entry_quantity_refresh_stage_v1",
        "stage": "initial_entry_quantity_refresh",
        "source_date": day,
        "generation_kind": "refresh",
        "stage_status": "complete_source_only",
        "applied_policy_lineage_schema": "initial_quantity_trade_policy_binding_v1",
        "terminal": True,
        "parent_policy_path": str(parent_policy_path),
        "parent_policy_file_sha256": _file_sha256(parent_policy_path),
        "parent_policy_content_sha256": parent_policy["policy_content_sha256"],
        "report_path": str(report_path.resolve()),
        "report_file_sha256": report_file_sha,
        "report_content_sha256": report["report_content_sha256"],
        "evaluation_path": str(evaluation_path.resolve()),
        "evaluation_file_sha256": evaluation_file_sha,
        "evaluation_content_sha256": evaluation_hash,
        **candidate_receipt,
        **following_receipt,
        **timeout_receipt,
        "pid_receipt": pid_receipt,
        "terminal_receipt": terminal_receipt,
        "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
        "decision": evaluation["state"],
        "runtime_apply_allowed": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    stage = {**body, "receipt_content_sha256": _digest(body)}
    _write_immutable_json(output_dir / f"initial_quantity_refresh_stage_{day}.json", stage)
    return stage


def refresh_quantity_stage_terminal_valid(receipt: Any) -> bool:
    if not isinstance(receipt, dict):
        return False
    try:
        body = {key: value for key, value in receipt.items()
                if key != "receipt_content_sha256"}
        if (receipt.get("schema_version") != "initial_entry_quantity_refresh_stage_v1"
                or receipt.get("stage") != "initial_entry_quantity_refresh"
                or receipt.get("generation_kind") != "refresh"
                or receipt.get("stage_status") != "complete_source_only"
                or receipt.get("terminal") is not True
                or receipt.get("runtime_apply_allowed") is not False
                or receipt.get("runtime_effect") is not False
                or receipt.get("actual_order_submitted") is not False
                or receipt.get("receipt_content_sha256") != _digest(body)):
            return False
        if receipt.get("applied_policy_lineage_schema") not in (
                None, "initial_quantity_trade_policy_binding_v1"):
            return False
        if (receipt.get("applied_policy_lineage_schema") !=
                "initial_quantity_trade_policy_binding_v1"
                or receipt.get("timeout_research_status") != "source_bound"):
            return False
        paths = {name: Path(receipt[f"{name}_path"])
                 for name in ("parent_policy", "report", "evaluation")}
        if (any(not path.is_absolute() or not path.is_file()
                or _file_sha256(path) != receipt[f"{name}_file_sha256"]
                for name, path in paths.items())
                or paths["report"].parent != paths["evaluation"].parent):
            return False
        parent = json.loads(paths["parent_policy"].read_text(encoding="utf-8"))
        report = json.loads(paths["report"].read_text(encoding="utf-8"))
        evaluation = json.loads(paths["evaluation"].read_text(encoding="utf-8"))
        if (receipt.get("terminal_receipt") is None
                and receipt.get("decision") == "carry_parent"
                and not any(key.startswith("candidate_") for key in receipt)):
            pass  # Historical source-only stages had no derived cost receipt.
        elif receipt.get("terminal_receipt") != _natural_refresh_terminal_receipt(report):
            return False
        pid_receipt = receipt.get("pid_receipt")
        if pid_receipt is not None:
            if (not isinstance(pid_receipt, dict)
                    or pid_receipt.get("source") !=
                    "verified_daily_preopen_main_pid_env"
                    or not Path(str(pid_receipt.get("data_root") or "")).is_absolute()):
                return False
            current_pid_source = _natural_refresh_pid_receipt(
                report, parent, paths["parent_policy"],
                Path(pid_receipt["data_root"]))
            if (current_pid_source is None
                    or any(pid_receipt.get(key) != current_pid_source.get(key)
                           for key in ("actual_pid_consumed",
                                       "policy_content_sha256",
                                       "policy_file_sha256",
                                       "first_consumed_date", "data_root", "source"))
                    or not isinstance(pid_receipt.get("daily_pid_receipts"), list)
                    or not pid_receipt["daily_pid_receipts"]
                    or any(row not in current_pid_source["daily_pid_receipts"]
                           for row in pid_receipt["daily_pid_receipts"])):
                return False
        winners = [row for row in report.get("trades") or []
                   if row.get("actual_net_pnl_krw", 0) > 0
                   and row.get("actual_profit_rate", 0) > 0]
        if receipt.get("following_bar_source_status") == "source_bound":
            from src.engine.scalping.initial_quantity_following_bars import (
                following_bar_source_valid,
            )
            following_path = Path(receipt["following_bar_source_path"])
            if (not following_path.is_absolute()
                    or following_path.parent != paths["report"].parent
                    or _file_sha256(following_path) !=
                    receipt["following_bar_source_file_sha256"]):
                return False
            following = json.loads(following_path.read_text(encoding="utf-8"))
            if (not following_bar_source_valid(following, report)
                    or following["report_content_sha256"] !=
                    receipt["following_bar_source_content_sha256"]):
                return False
        elif (receipt.get("following_bar_source_status") != "no_winners"
              or winners
              or any(key.startswith("following_bar_source_") and key !=
                     "following_bar_source_status" for key in receipt)):
            return False
        timeout_research = None
        if receipt.get("timeout_research_status") == "source_bound":
            from src.engine.scalping.initial_quantity_timeout_research import (
                timeout_research_valid,
            )
            timeout_path = Path(receipt["timeout_research_path"])
            if (not timeout_path.is_absolute()
                    or timeout_path.parent != paths["report"].parent
                    or _file_sha256(timeout_path) !=
                    receipt["timeout_research_file_sha256"]):
                return False
            timeout_research = json.loads(timeout_path.read_text(encoding="utf-8"))
            if (not timeout_research_valid(timeout_research)
                    or timeout_research.get("generation_kind") !=
                    "refresh_post_apply_timeout_research"
                    or timeout_research.get("source_date") != report.get("source_date")
                    or timeout_research.get("entry_on_or_after") !=
                    (report.get("census") or {}).get("entry_on_or_after")
                    or timeout_research.get("census") != report.get("census")
                    or timeout_research.get("quantity_type_counts") !=
                    report.get("quantity_type_counts")
                    or timeout_research.get("pipeline_source_receipts") !=
                    report.get("pipeline_source_receipts")
                    or timeout_research.get("report_content_sha256") !=
                    receipt["timeout_research_content_sha256"]):
                return False
        elif (receipt.get("timeout_research_status") not in (None, "not_provided")
              or any(key.startswith("timeout_research_") and key !=
                     "timeout_research_status" for key in receipt)):
            return False
        expected = evaluate_refresh_quantity_candidate(
            report, parent_policy=parent,
            pid_receipt=receipt["pid_receipt"],
            terminal_receipt=receipt["terminal_receipt"],
            following_bars=(following if receipt["following_bar_source_status"]
                            == "source_bound" else None),
            timeout_research=timeout_research,
            parent_policy_file_sha256=receipt["parent_policy_file_sha256"],
            enforce_trade_lineage=bool(receipt.get("applied_policy_lineage_schema")))
        if receipt.get("decision") == "eligible_source_only":
            if (receipt.get("candidate_status") != "source_only"
                    or not isinstance(timeout_research, dict)):
                return False
            candidate_path = Path(receipt["candidate_path"])
            if (not candidate_path.is_absolute()
                    or candidate_path.parent != paths["report"].parent
                    or _file_sha256(candidate_path) !=
                    receipt["candidate_file_sha256"]):
                return False
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            if (candidate != build_refresh_type_policy_candidate(
                    report, evaluation, parent, timeout_research)
                    or candidate["policy_content_sha256"] !=
                    receipt["candidate_content_sha256"]):
                return False
        elif any(key.startswith("candidate_") for key in receipt):
            return False
        return bool(
            evaluation == expected
            and receipt["parent_policy_content_sha256"] == parent["policy_content_sha256"]
            and receipt["report_content_sha256"] == report["report_content_sha256"]
            and receipt["evaluation_content_sha256"] == _digest(evaluation)
            and receipt["source_date"] == report["source_date"]
            and receipt["all_completed_initial_trades"] == report["census"]["all_completed_initial_trades"]
            and receipt["decision"] == evaluation["state"]
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def initial_quantity_policy_valid(
    policy: Any, *, report: dict[str, Any] | None = None,
    following_bars: dict[str, Any] | None = None,
) -> bool:
    """Reject a tampered or broadened seed even while it is report-only."""
    if not isinstance(policy, dict) or not isinstance(report, dict):
        return False
    try:
        body = {key: value for key, value in policy.items() if key != "policy_content_sha256"}
        source_date = date.fromisoformat(policy["source_date"])
        effective_from = date.fromisoformat(policy["effective_from"])
        types = policy["type_policies"]
        if not (
            policy.get("schema_version") == POLICY_SCHEMA
            and policy.get("generation_kind") == "initial_completed_trade_seed"
            and policy.get("classifier_version") == CLASSIFIER_VERSION
            and policy.get("policy_owner") == "entry_execution_sizing_owner"
            and policy.get("census_source") == "trade_performance_facts"
            and policy.get("policy_content_sha256") == _digest(body)
            and policy.get("policy_version", "").startswith(f"initial-type-{source_date.isoformat()}-")
            and effective_from > source_date
            and type(policy.get("all_completed_initial_trades")) is int
            and policy["all_completed_initial_trades"] > 0
            and isinstance(types, dict) and set(types) == set(_TYPES)
            and all(isinstance(item, dict)
                    and item.get("ratio_mode") == "parent_5stage"
                    and item.get("selected_shape") in _SHAPES
                    and type(item.get("paired_count")) is int
                    and item["paired_count"] >= 0
                    and item.get("timeout_mode") == "existing_runtime_profile"
                    and item.get("selected_total_wait_sec") is None
                    and item.get("winner_weight_kind") == "positive_realized_net_pnl_krw"
                    and type(item.get("winner_count")) is int
                    and item["winner_count"] >= 0
                    and type(item.get("winner_weight_sum_krw")) in (int, float)
                    and math.isfinite(item["winner_weight_sum_krw"])
                    and item["winner_weight_sum_krw"] >= 0 for item in types.values())
            and types["SAFE_UNKNOWN"]["selected_shape"] == "parent"
            and all(policy.get(key) is False for key in (
                "action_authority", "price_authority", "scale_in_authority",
                "quantity_cap_relaxation", "runtime_effect", "runtime_apply_allowed",
                "actual_order_submitted"))
            and policy.get("broker_order_forbidden") is True
            and policy.get("activation_state")
            == "candidate_requires_contract_migration_and_preopen_validation"
        ):
            return False
        if (
            not initial_replay_economics_valid(report)
            or report.get("report_content_sha256") != _digest({
                key: value for key, value in report.items()
                if key != "report_content_sha256"})
            or report.get("schema_version") != REPORT_SCHEMA
            or report.get("report_content_sha256") != policy.get("report_content_sha256")
            or (report.get("census") or {}).get("input_manifest_sha256")
            != policy.get("input_manifest_sha256")
            or (report.get("census") or {}).get("input_manifest_sha256")
            != _digest((report.get("census") or {}).get("input_fact_rows"))
            or (report.get("census") or {}).get("all_completed_initial_trades")
            != policy.get("all_completed_initial_trades")
            or any(types[quantity_type]["selected_shape"] !=
                   (report.get("selections") or {}).get(quantity_type, {}).get("selected_shape")
                   for quantity_type in _TYPES)
            or any(types[quantity_type]["winner_count"] !=
                   report["selections"][quantity_type].get("winner_count", 0)
                   or types[quantity_type]["winner_weight_sum_krw"] !=
                   report["selections"][quantity_type].get("winner_weight_sum_krw", 0)
                   or types[quantity_type]["winner_weighted_parent_ev_pct"] !=
                   report["selections"][quantity_type].get("winner_weighted_parent_ev_pct")
                   or types[quantity_type]["winner_weighted_selected_ev_pct"] !=
                   report["selections"][quantity_type]["candidate_metrics"][
                       types[quantity_type]["selected_shape"]].get(
                           "winner_weighted_conservative_ev_pct")
                   for quantity_type in _TYPES)
        ):
            return False
        if "following_bar_source_content_sha256" in policy:
            from src.engine.scalping.initial_quantity_following_bars import (
                following_bar_source_valid,
            )
            if (not isinstance(following_bars, dict)
                    or not following_bar_source_valid(following_bars, report)
                    or policy["following_bar_source_content_sha256"] !=
                    following_bars["report_content_sha256"]
                    or any(
                        types[quantity_type].get("following_lower_observed_minute_count") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "observed_minute_lower_count", 0)
                        or types[quantity_type].get("following_weighted_lower_from_fill_minute") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "weighted_lower_elapsed_from_fill_minute")
                        or types[quantity_type].get("following_order_start_linked_count") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "order_start_linked_count", 0)
                        or types[quantity_type].get(
                            "following_weighted_lower_from_order_start_minute") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "weighted_lower_elapsed_from_order_start_minute")
                        for quantity_type in _TYPES)):
                return False
        elif following_bars is not None:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _write_immutable_json(path: Path, payload: dict[str, Any]) -> str:
    """Publish a source-only artifact once; retries must reproduce exact bytes."""
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise ValueError(f"immutable_artifact_conflict:{path}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return hashlib.sha256(encoded).hexdigest()


def publish_initial_quantity_candidate(
    report: dict[str, Any], *, output_dir: Path,
    following_bars: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind the full replay and source-only seed to one immutable stage receipt."""
    policy = build_initial_quantity_policy(report, following_bars=following_bars)
    source_date = policy["source_date"]
    report_hash = report["report_content_sha256"]
    policy_hash = policy["policy_content_sha256"]
    report_path = output_dir / f"initial_quantity_replay_{source_date}_{report_hash[:12]}.json"
    policy_path = output_dir / f"initial_quantity_candidate_{source_date}_{policy_hash[:12]}.json"
    report_file_sha = _write_immutable_json(report_path, report)
    policy_file_sha = _write_immutable_json(policy_path, policy)
    following_receipt = {}
    if following_bars is not None:
        following_hash = following_bars["report_content_sha256"]
        following_path = output_dir / (f"initial_quantity_following_bars_{source_date}_"
                                       f"{following_hash[:12]}.json")
        following_receipt = {
            "following_bar_source_path": str(following_path.resolve()),
            "following_bar_source_file_sha256": _write_immutable_json(
                following_path, following_bars),
            "following_bar_source_content_sha256": following_hash,
        }
    body = {
        "schema_version": "initial_entry_quantity_stage_terminal_v1",
        "stage": "initial_entry_quantity_type_policy",
        "source_date": source_date,
        "generation_kind": "initial_completed_trade_seed",
        "stage_status": "complete_source_only",
        "terminal": True,
        "report_path": str(report_path.resolve()),
        "report_file_sha256": report_file_sha,
        "report_content_sha256": report_hash,
        "candidate_policy_path": str(policy_path.resolve()),
        "candidate_policy_file_sha256": policy_file_sha,
        "candidate_policy_content_sha256": policy_hash,
        **following_receipt,
        "input_manifest_sha256": policy["input_manifest_sha256"],
        "all_completed_initial_trades": policy["all_completed_initial_trades"],
        "runtime_apply_allowed": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    receipt = {**body, "receipt_content_sha256": _digest(body)}
    receipt_path = output_dir / f"initial_quantity_stage_{source_date}.json"
    _write_immutable_json(receipt_path, receipt)
    return receipt


def initial_quantity_stage_terminal_valid(receipt: Any) -> bool:
    """Validate stage bytes and both linked inputs before a handoff reads them."""
    if not isinstance(receipt, dict):
        return False
    try:
        body = {key: value for key, value in receipt.items()
                if key != "receipt_content_sha256"}
        if not (
            receipt.get("schema_version") == "initial_entry_quantity_stage_terminal_v1"
            and receipt.get("stage") == "initial_entry_quantity_type_policy"
            and receipt.get("generation_kind") == "initial_completed_trade_seed"
            and receipt.get("stage_status") == "complete_source_only"
            and receipt.get("terminal") is True
            and receipt.get("runtime_apply_allowed") is False
            and receipt.get("runtime_effect") is False
            and receipt.get("actual_order_submitted") is False
            and receipt.get("receipt_content_sha256") == _digest(body)
        ):
            return False
        report_path = Path(receipt["report_path"])
        policy_path = Path(receipt["candidate_policy_path"])
        if (not report_path.is_absolute() or not policy_path.is_absolute()
                or report_path.parent != policy_path.parent
                or not report_path.is_file() or not policy_path.is_file()
                or _file_sha256(report_path) != receipt["report_file_sha256"]
                or _file_sha256(policy_path) != receipt["candidate_policy_file_sha256"]):
            return False
        report = json.loads(report_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        following_bars = None
        if "following_bar_source_path" in receipt:
            following_path = Path(receipt["following_bar_source_path"])
            if (not following_path.is_absolute()
                    or following_path.parent != report_path.parent
                    or _file_sha256(following_path) !=
                    receipt["following_bar_source_file_sha256"]):
                return False
            following_bars = json.loads(following_path.read_text(encoding="utf-8"))
            if (following_bars.get("report_content_sha256") !=
                    receipt["following_bar_source_content_sha256"]):
                return False
        elif any(key.startswith("following_bar_source_") for key in receipt):
            return False
        return bool(
            initial_quantity_policy_valid(policy, report=report,
                                          following_bars=following_bars)
            and report["source_date"] == policy["source_date"] == receipt["source_date"]
            and report["report_content_sha256"] == receipt["report_content_sha256"]
            and policy["policy_content_sha256"] == receipt["candidate_policy_content_sha256"]
            and policy["input_manifest_sha256"] == receipt["input_manifest_sha256"]
            and policy["all_completed_initial_trades"] == receipt["all_completed_initial_trades"]
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of")
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--policy-output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--following-bars", type=Path)
    parser.add_argument("--parent-current", type=Path)
    parser.add_argument("--pid-receipt", type=Path)
    parser.add_argument("--terminal-receipt", type=Path)
    args = parser.parse_args(argv)
    if bool(args.as_of) == bool(args.replay):
        parser.error("exactly one of --as-of or --replay is required")
    if args.output_dir and (args.output or args.policy_output):
        parser.error("--output-dir cannot be combined with explicit output paths")
    if args.parent_current and (not args.output_dir or args.policy_output
                                or args.output):
        parser.error("refresh requires --output-dir and no seed output paths")
    if (args.pid_receipt or args.terminal_receipt) and not args.parent_current:
        parser.error("post-apply receipts require --parent-current")
    parent = None
    parent_path = None
    if args.parent_current:
        from src.engine.scalping.initial_quantity_activation import (
            ENV_FILE, selected_initial_quantity_env,
        )
        target_date = args.as_of
        if args.replay:
            target_date = json.loads(args.replay.read_text(encoding="utf-8"))["source_date"]
        env = selected_initial_quantity_env(args.parent_current, target_date)
        parent_path = Path(env[ENV_FILE])
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
    performance: dict[str, Any] = {}
    path_cache: dict[str, Any] | None = {} if parent is not None and not args.replay else None
    if args.replay:
        report = json.loads(args.replay.read_text(encoding="utf-8"))
        if (not isinstance(report, dict)
                or report.get("report_content_sha256") != _digest({
                    key: value for key, value in report.items()
                    if key != "report_content_sha256"})
                or not initial_replay_economics_valid(report)):
            raise ValueError("existing_replay_invalid")
    else:
        report = build_initial_quantity_replay(
            args.as_of, data_dir=args.data_dir, performance=performance,
            entry_on_or_after=parent["effective_from"] if parent else None,
            path_cache=path_cache)
    following_bars = (json.loads(args.following_bars.read_text(encoding="utf-8"))
                      if args.following_bars else None)
    if parent is not None:
        following_performance: dict[str, Any] = {}
        if following_bars is None and any(
                row["actual_net_pnl_krw"] > 0 and row["actual_profit_rate"] > 0
                for row in report["trades"]):
            from src.engine.scalping.initial_quantity_following_bars import (
                build_following_bar_source,
            )
            from src.utils import kiwoom_utils

            token_state: dict[str, Any] = {"attempted": False, "token": None,
                                           "error": None}

            def fetch(code: str, base_dt: str, limit: int):
                if not token_state["attempted"]:
                    token_state["attempted"] = True
                    try:
                        token_state["token"] = kiwoom_utils.get_kiwoom_token()
                    except Exception as exc:
                        token_state["error"] = exc
                if token_state["error"] is not None:
                    raise token_state["error"]
                return kiwoom_utils.get_minute_candles_ka10080_with_meta(
                    token_state["token"], code, limit=limit, explicit_request_code=True,
                    base_dt=base_dt)

            following_bars = build_following_bar_source(
                report, fetch=fetch, performance=following_performance)
        from src.engine.scalping.initial_quantity_timeout_research import (
            build_timeout_research,
        )
        timeout_performance: dict[str, Any] = {}
        timeout_research = build_timeout_research(
            report["source_date"],
            data_dir=args.data_dir,
            fact_rows=report["census"]["input_fact_rows"],
            entry_on_or_after=parent["effective_from"],
            path_cache=path_cache,
            performance=timeout_performance)
        pid_receipt = _natural_refresh_pid_receipt(
            report, parent, parent_path, args.data_dir)
        terminal_receipt = _natural_refresh_terminal_receipt(report)
        if (args.pid_receipt
                and json.loads(args.pid_receipt.read_text(encoding="utf-8"))
                != pid_receipt):
            raise ValueError("refresh_pid_receipt_source_mismatch")
        if (args.terminal_receipt
                and json.loads(args.terminal_receipt.read_text(encoding="utf-8"))
                != terminal_receipt):
            raise ValueError("refresh_terminal_receipt_source_mismatch")
        stage = publish_refresh_quantity_evaluation(
            report, parent_policy=parent, parent_policy_path=parent_path,
            output_dir=args.output_dir,
            pid_receipt=pid_receipt,
            terminal_receipt=terminal_receipt,
            following_bars=following_bars,
            timeout_research=timeout_research)
        if not refresh_quantity_stage_terminal_valid(stage):
            raise ValueError("refresh_stage_self_validation_failed")
        print(json.dumps({"source_date": report["source_date"],
                          "all_completed_initial_trades": stage["all_completed_initial_trades"],
                          "decision": stage["decision"],
                          "receipt_content_sha256": stage["receipt_content_sha256"],
                          "performance": performance,
                          "following_performance": following_performance,
                          "timeout_performance": timeout_performance}))
        return 0
    if args.output_dir:
        publish_initial_quantity_candidate(
            report, output_dir=args.output_dir, following_bars=following_bars)
    elif args.output:
        _write_immutable_json(args.output, report)
    if args.policy_output:
        policy = build_initial_quantity_policy(report, following_bars=following_bars)
        _write_immutable_json(args.policy_output, policy)
    print(json.dumps({"source_date": report["source_date"],
                      "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
                      "replay_counts": report["replay_counts"],
                      "performance": performance,
                      "report_content_sha256": report["report_content_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
