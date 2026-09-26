"""Source-bound historical minute lows following profitable initial BUY fills.

This producer reuses the existing ka10080 client. Its minute lows are
conditional path evidence, never broker fills or exact-second order deadlines.
"""

from __future__ import annotations

import argparse
import json
import math
import resource
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from src.engine.scalping.initial_quantity_policy import (
    _digest, _write_immutable_json, initial_replay_economics_valid,
)
from src.engine.scalping.initial_quantity_type import kst_timestamp

SCHEMA = "initial_quantity_following_minute_bars_v1"
MAX_FOLLOWING_SEC = 1200
_SOURCE_META_FIELDS = (
    "api_id", "request_code", "request_base_dt", "received_count",
    "sort_direction_detected", "cont_yn_seen", "next_key_seen",
    "continuous_next_key_missing", "continuous_page_limit_reached",
    "latest_source_timestamp", "source_time_basis", "truncated_window",
)


def _valid_replay(report: Any) -> bool:
    return (isinstance(report, dict)
            and report.get("report_content_sha256") == _digest({
                key: value for key, value in report.items()
                if key != "report_content_sha256"})
            and initial_replay_economics_valid(report)
            and report.get("census", {}).get("input_manifest_sha256") == _digest(
                report.get("census", {}).get("input_fact_rows")))


def _source_time(raw: Any) -> datetime | None:
    value = str(raw or "").strip()
    if len(value) != 14 or not value.isdigit():
        return None
    try:
        return kst_timestamp(datetime.strptime(value, "%Y%m%d%H%M%S").isoformat())
    except ValueError:
        return None


def _positive_price(raw: Any) -> int | None:
    if isinstance(raw, bool):
        return None
    try:
        price = float(raw)
    except (TypeError, ValueError, OverflowError):
        return None
    return int(price) if math.isfinite(price) and price > 0 and price.is_integer() else None


def _request_route(row: dict[str, Any], stock_code: str) -> tuple[str, str]:
    venue = str(row.get("entry_fill_venue") or "").upper()
    exact_clock = row.get("entry_fill_clock_source") == "broker_execution_observed_at"
    if exact_clock and venue in {"KRX", "NXT"}:
        return ((stock_code if venue == "KRX" else f"{stock_code}_NX"), venue)
    return f"{stock_code}_AL", "INTEGRATED_VENUE_UNVERIFIED"


def build_following_bar_source(
    replay: dict[str, Any], *,
    fetch: Callable[[str, str, int], tuple[list[dict[str, Any]], dict[str, Any]]],
    max_requests: int = 250,
    performance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch each symbol/date/venue once and retain every profitable trade."""
    if not _valid_replay(replay) or type(max_requests) is not int or max_requests < 0:
        raise ValueError("following_bar_input_invalid")
    started = time.perf_counter()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    facts: dict[str, dict[str, Any]] = {}
    conflicting_ids: set[str] = set()
    for fact in replay["census"]["input_fact_rows"]:
        if not isinstance(fact, dict) or fact.get("recommendation_id") is None:
            continue
        rid = str(fact["recommendation_id"])
        if rid in facts and facts[rid] != fact:
            conflicting_ids.add(rid)
        else:
            facts[rid] = fact
    winners = [row for row in replay["trades"]
               if row["actual_net_pnl_krw"] > 0 and row["actual_profit_rate"] > 0]
    queries: dict[tuple[str, str], list[tuple[dict[str, Any], dict[str, Any], str]]] = (
        defaultdict(list))
    results: dict[str, dict[str, Any]] = {}
    for row in winners:
        fact = facts.get(str(row["record_id"]))
        trade_id = row["trade_id"]
        if (row["record_id"] in conflicting_ids or not fact
                or str(fact.get("stock_code") or "") != str(row.get("stock_code") or "")
                or not row.get("stock_code")
                or str(fact.get("status") or "").upper() != "COMPLETED"
                or fact.get("realized_pnl_krw") != row.get("actual_net_pnl_krw")):
            results[trade_id] = {"status": "fact_identity_missing"}
            continue
        if (row.get("shapes") or {}).get("parent", {}).get("status") != "paired":
            results[trade_id] = {"status": "parent_source_quality_blocked"}
            continue
        fill_at = kst_timestamp(row.get("entry_fill_at") or fact.get("buy_time"))
        exit_at = kst_timestamp(fact.get("sell_time"))
        if (fill_at is None or exit_at is None or exit_at <= fill_at
                or fill_at.date() != exit_at.date()
                or fill_at.date().isoformat() != row["entry_date"]):
            results[trade_id] = {"status": "same_day_fill_exit_clock_missing"}
            continue
        request_code, venue_quality = _request_route(row, str(fact["stock_code"]))
        queries[(row["entry_date"], request_code)].append((row, fact, venue_quality))
    sources: dict[str, Any] = {}
    requests = 0
    for (day, request_code), group in sorted(queries.items()):
        key = f"{day}:{request_code}"
        if requests >= max_requests:
            sources[key] = {"status": "request_budget_exhausted"}
            for row, _, _ in group:
                results[row["trade_id"]] = {"status": "request_budget_exhausted"}
            continue
        requests += 1
        try:
            candles, meta = fetch(request_code, day.replace("-", ""), 900)
            if not isinstance(candles, list) or not isinstance(meta, dict):
                raise ValueError("invalid_ka10080_response_shape")
        except Exception as exc:
            sources[key] = {"status": "fetch_failed", "error_class": type(exc).__name__}
            for row, _, _ in group:
                results[row["trade_id"]] = {"status": "fetch_failed"}
            continue
        source_meta = {field: meta.get(field) for field in _SOURCE_META_FIELDS}
        sources[key] = {"status": "received", "api_id": "ka10080",
                        "request_code": request_code,
                        "request_base_dt": day.replace("-", ""),
                        "meta": source_meta, "bar_count": len(candles),
                        "bar_content_sha256": _digest(candles)}
        if (meta.get("api_id") != "ka10080"
                or meta.get("request_code") != request_code
                or meta.get("request_base_dt") != day.replace("-", "")
                or meta.get("continuous_next_key_missing")):
            sources[key]["status"] = "source_contract_gap"
            for row, _, _ in group:
                results[row["trade_id"]] = {"status": "source_contract_gap"}
            continue
        bars = []
        by_clock: dict[datetime, int] = {}
        conflicting_bar_clock = False
        for candle in candles:
            if not isinstance(candle, dict):
                continue
            at = _source_time(candle.get("source_timestamp"))
            low = _positive_price(candle.get("저가"))
            if at and at.date().isoformat() == day and low:
                if at in by_clock and by_clock[at] != low:
                    conflicting_bar_clock = True
                by_clock[at] = low
        if conflicting_bar_clock:
            sources[key]["status"] = "conflicting_minute_bar"
            for row, _, _ in group:
                results[row["trade_id"]] = {"status": "conflicting_minute_bar"}
            continue
        bars = list(by_clock.items())
        bars.sort(key=lambda item: item[0])
        sources[key]["older_pages_unfetched"] = bool(
            meta.get("continuous_page_limit_reached"))
        sources[key]["returned_day_earliest_bar_at"] = (
            bars[0][0].isoformat() if bars else None)
        sources[key]["returned_day_latest_bar_at"] = (
            bars[-1][0].isoformat() if bars else None)
        for row, fact, venue_quality in group:
            fill = kst_timestamp(row.get("entry_fill_at") or fact["buy_time"])
            exit_at = kst_timestamp(fact["sell_time"])
            end = min(exit_at, fill + timedelta(seconds=MAX_FOLLOWING_SEC))
            window_bracketed = bool(
                bars and bars[0][0] <= fill
                and bars[-1][0] + timedelta(seconds=60) >= end)
            if not window_bracketed:
                results[row["trade_id"]] = {
                    "status": "bar_window_source_gap",
                    "quantity_type": row["quantity_type"],
                    "weight_realized_net_pnl_krw": row["actual_net_pnl_krw"],
                    "source_key": key,
                    "window_bracketed": False,
                }
                continue
            # cntr_tm is a bar clock, with no documented within-minute low
            # sequence. Discard the entry minute and the exit/limit boundary.
            observed = [(at, low) for at, low in bars
                        if fill + timedelta(seconds=60) < at
                        and at + timedelta(seconds=60) <= end]
            anchor = _positive_price(fact.get("buy_price"))
            lower = [(at, low) for at, low in observed if anchor and low < anchor]
            first_lower = min(lower, key=lambda item: item[0], default=None)
            lowest = min(lower, key=lambda item: item[1], default=None)
            clock_quality = ("broker_fill_clock" if row.get("entry_fill_clock_source")
                             == "broker_execution_observed_at" else "fact_buy_time_proxy")
            start = kst_timestamp(row.get("entry_order_start_at"))
            results[row["trade_id"]] = {
                "status": ("conditional_lower_observed" if first_lower else
                           "no_lower_in_observed_bars" if observed else "bar_window_missing"),
                "quantity_type": row["quantity_type"],
                "weight_realized_net_pnl_krw": row["actual_net_pnl_krw"],
                "clock_quality": clock_quality,
                "venue_quality": venue_quality,
                "bar_count_in_window": len(observed),
                "window_bracketed": True,
                "first_lower_at": first_lower[0].isoformat() if first_lower else None,
                "first_lower_price": first_lower[1] if first_lower else None,
                "lowest_price": lowest[1] if lowest else None,
                "first_lower_elapsed_from_fill_sec": (
                    round((first_lower[0] - fill).total_seconds(), 3)
                    if first_lower else None),
                "first_lower_elapsed_from_fill_minute": (
                    math.ceil((first_lower[0] - fill).total_seconds() / 60)
                    if first_lower else None),
                "first_lower_elapsed_from_order_start_sec": (
                    round((first_lower[0] - start).total_seconds(), 3)
                    if first_lower and start and start <= first_lower[0] else None),
                "first_lower_elapsed_from_order_start_minute": (
                    math.ceil((first_lower[0] - start).total_seconds() / 60)
                    if first_lower and start and start <= first_lower[0] else None),
                "source_key": key,
                "bar_time_semantics": "complete_minute_conservative_bound",
                "time_resolution_sec": 60,
                "broker_fill_or_cancel_proof": False,
            }
    weighted = {}
    for quantity_type in sorted({row["quantity_type"] for row in winners}):
        linked = [results[row["trade_id"]] for row in winners]
        linked = [row for row in linked if row.get("quantity_type") == quantity_type
                  and row.get("first_lower_elapsed_from_fill_minute") is not None]
        weight = sum(row["weight_realized_net_pnl_krw"] for row in linked)
        start_linked = [row for row in linked
                        if row.get("first_lower_elapsed_from_order_start_minute") is not None]
        start_weight = sum(row["weight_realized_net_pnl_krw"] for row in start_linked)
        weighted[quantity_type] = {
            "observed_minute_lower_count": len(linked),
            "weight_sum_krw": round(weight, 3),
            "weighted_lower_elapsed_from_fill_minute": (
                round(sum(row["first_lower_elapsed_from_fill_minute"] *
                          row["weight_realized_net_pnl_krw"] for row in linked) /
                      weight, 3) if weight else None),
            "order_start_linked_count": len(start_linked),
            "weighted_lower_elapsed_from_order_start_minute": (
                round(sum(row["first_lower_elapsed_from_order_start_minute"] *
                          row["weight_realized_net_pnl_krw"] for row in start_linked) /
                      start_weight, 3) if start_weight else None),
            "weighted_lower_elapsed_from_order_start_sec": (
                round(sum(row["first_lower_elapsed_from_order_start_sec"] *
                          row["weight_realized_net_pnl_krw"] for row in start_linked) /
                      start_weight, 3) if start_weight else None),
        }
    usage_end = resource.getrusage(resource.RUSAGE_SELF)
    if performance is not None:
        performance.update({
            "wall_seconds": round(time.perf_counter() - started, 3),
            "cpu_user_seconds": round(usage_end.ru_utime - usage_start.ru_utime, 3),
            "cpu_system_seconds": round(usage_end.ru_stime - usage_start.ru_stime, 3),
            "peak_rss_kb": usage_end.ru_maxrss,
            "trade_result_count": len(results),
            "source_group_count": len(queries)})
    body = {"schema": SCHEMA, "source_date": replay["source_date"],
            "replay_content_sha256": replay["report_content_sha256"],
            "input_manifest_sha256": replay["census"]["input_manifest_sha256"],
            "winner_weight_kind": "positive_realized_net_pnl_krw",
            "winner_count": len(winners), "request_count": requests,
            "provider_source": "official_kiwoom_ka10080_existing_client",
            "runtime_apply_allowed": False,
            "minute_low_is_conditional_not_broker_fill": True,
            "sources": sources, "trades": dict(sorted(results.items())),
            "weighted_by_type": weighted}
    return {**body, "report_content_sha256": _digest(body)}


def following_bar_source_valid(source: Any, replay: dict[str, Any]) -> bool:
    """Bind every profitable completed trade to a sealed source or gap."""
    if not isinstance(source, dict) or not _valid_replay(replay):
        return False
    try:
        winners = {row["trade_id"]: row for row in replay["trades"]
                   if row["actual_net_pnl_krw"] > 0 and row["actual_profit_rate"] > 0}
        if (source.get("schema") != SCHEMA
                or source.get("report_content_sha256") != _digest({
                    key: value for key, value in source.items()
                    if key != "report_content_sha256"})
                or source.get("replay_content_sha256") != replay["report_content_sha256"]
                or source.get("input_manifest_sha256") !=
                replay["census"]["input_manifest_sha256"]
                or source.get("source_date") != replay["source_date"]
                or source.get("winner_count") != len(winners)
                or source.get("winner_weight_kind") != "positive_realized_net_pnl_krw"
                or source.get("runtime_apply_allowed") is not False
                or source.get("minute_low_is_conditional_not_broker_fill") is not True
                or not isinstance(source.get("trades"), dict)
                or set(source["trades"]) != set(winners)
                or not isinstance(source.get("weighted_by_type"), dict)):
            return False
        for trade_id, trade in winners.items():
            row = source["trades"][trade_id]
            if not isinstance(row, dict) or not str(row.get("status") or ""):
                return False
            if row.get("first_lower_at") is not None:
                if (row.get("quantity_type") != trade["quantity_type"]
                        or row.get("weight_realized_net_pnl_krw") !=
                        trade["actual_net_pnl_krw"]
                        or type(row.get("first_lower_elapsed_from_fill_minute")) is not int
                        or row["first_lower_elapsed_from_fill_minute"] < 1
                        or row.get("time_resolution_sec") != 60
                        or row.get("broker_fill_or_cancel_proof") is not False):
                    return False
        for quantity_type in {row["quantity_type"] for row in winners.values()}:
            linked = [source["trades"][trade_id] for trade_id, trade in winners.items()
                      if trade["quantity_type"] == quantity_type
                      and source["trades"][trade_id].get("first_lower_at") is not None]
            weight = sum(row["weight_realized_net_pnl_krw"] for row in linked)
            expected = (round(sum(row["first_lower_elapsed_from_fill_minute"] *
                                  row["weight_realized_net_pnl_krw"] for row in linked) /
                              weight, 3) if weight else None)
            metric = source["weighted_by_type"][quantity_type]
            if (metric["observed_minute_lower_count"] != len(linked)
                    or abs(metric["weight_sum_krw"] - weight) > 0.001
                    or metric["weighted_lower_elapsed_from_fill_minute"] != expected):
                return False
        return True
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-requests", type=int, default=250)
    parser.add_argument("--print-plan", action="store_true")
    args = parser.parse_args(argv)
    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    if not _valid_replay(replay):
        raise ValueError("following_bar_input_invalid")
    if args.print_plan:
        print(json.dumps({"source_date": replay["source_date"],
                          "winner_count": sum(row["actual_net_pnl_krw"] > 0
                                              and row["actual_profit_rate"] > 0
                                              for row in replay["trades"]),
                          "max_requests": args.max_requests,
                          "runtime_effect": False}))
        return 0
    from src.utils import kiwoom_utils

    token = kiwoom_utils.get_kiwoom_token()

    def fetch(code: str, base_dt: str, limit: int):
        return kiwoom_utils.get_minute_candles_ka10080_with_meta(
            token, code, limit=limit, explicit_request_code=True, base_dt=base_dt)

    performance: dict[str, Any] = {}
    report = build_following_bar_source(replay, fetch=fetch,
                                        max_requests=args.max_requests,
                                        performance=performance)
    if not following_bar_source_valid(report, replay):
        raise ValueError("following_bar_source_self_validation_failed")
    path = args.output_dir / (f"initial_quantity_following_bars_{replay['source_date']}_"
                              f"{report['report_content_sha256'][:12]}.json")
    file_sha = _write_immutable_json(path, report)
    print(json.dumps({"path": str(path.resolve()), "file_sha256": file_sha,
                      "winner_count": report["winner_count"],
                      "request_count": report["request_count"],
                      "performance": performance,
                      "report_content_sha256": report["report_content_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
