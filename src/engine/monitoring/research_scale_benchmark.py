"""Offline full-grid scale receipt. No production source, API or order calls."""

from __future__ import annotations
import argparse
from datetime import date, datetime, time, timedelta
import gc
import json
from pathlib import Path
import resource
import tempfile
import time as clock
from zoneinfo import ZoneInfo
from src.engine.monitoring import widget_symbol_signal_policy_research as research
from src.engine.monitoring import research_closed_loop as loop
from src.utils.market_day import is_krx_trading_day


def fixture(days, symbol_number, *, populated=False):
    import math

    day = date(2026, 6, 5)
    rows, dates = [], []
    while len(dates) < days:
        if is_krx_trading_day(day):
            dates.append(day)
            for minute in range(390):
                close = round(10000 + symbol_number * 10 + 150 * math.sin(minute / 12))
                rows.append(
                    research.Bar(
                        datetime.combine(day, time(9), ZoneInfo("Asia/Seoul"))
                        + timedelta(minutes=minute),
                        close - 3 if populated else close + 3,
                        close + 9,
                        close - 9,
                        close,
                        (600 if minute % 7 == 6 else 100)
                        if populated
                        else 100 + (minute % 7) * 10,
                    )
                )
        day += timedelta(days=1)
    return rows, dates


def run(
    symbol_count,
    day_count,
    cache,
    output,
    *,
    populated=False,
    modes=("cold", "warm", "append"),
    compute_budget_sec=5400,
):
    # Freeze the semantic key once, before any concurrent workspace edits.
    semantic = research.research_contract_hash()
    research.research_contract_hash = lambda: semantic
    matrix, digests = {}, {}
    for mode in modes:
        begin = clock.monotonic()
        cpu = clock.process_time()
        hits = misses = skips = 0
        hashes = {}
        for index in range(symbol_count):
            bars, dates = fixture(
                day_count + (mode == "append"), index, populated=populated
            )
            grouped = research._group_bars(bars)
            context = research.ReplayContext(grouped, cache / f"{index:06d}")
            context.symbol = str(index)
            result = research.discover_symbol_policy(
                bars, expected_dates=dates, replay_context=context
            )
            context.flush()
            hits += context.cache_hits
            misses += context.cache_misses
            skips += context.cache_write_skips
            hashes[str(index)] = loop.digest(result)
            if mode == "warm" and digests and hashes[str(index)] != digests[str(index)]:
                raise AssertionError("warm_cold_canonical_discovery_mismatch")
            elapsed = clock.monotonic() - begin
            if index + 1 in {19, 50, 100, symbol_count}:
                matrix[f"{mode}_N{index + 1}_D{len(dates)}"] = dict(
                    wall_seconds=elapsed,
                    cpu_seconds=clock.process_time() - cpu,
                    symbols=index + 1,
                    day_count=len(dates),
                    grid=1536,
                    caps=[1, 2, 3, 4, 5],
                    cache_hits=hits,
                    cache_misses=misses,
                    cache_write_skips=skips,
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    remote_requests=0,
                    candidate_digest=loop.digest(hashes),
                )
                loop.atomic_write(
                    output,
                    dict(
                        schema=loop.SCHEMA,
                        status="running",
                        fixture="deterministic_390_bars_per_symbol_day_sinusoid_v2",
                        populated=populated,
                        producer_sha256=semantic,
                        measurements=matrix,
                        **loop.AUTHORITY,
                    ),
                )
            del bars, grouped, context, result
            gc.collect()
            if elapsed > compute_budget_sec:
                receipt = dict(
                    schema=loop.SCHEMA,
                    status="deferred",
                    reason="compute_phase_budget_exceeded",
                    failed_phase=mode,
                    completed_symbol_count=index + 1,
                    unprocessed_symbol_count=symbol_count - index - 1,
                    requested_scope=dict(
                        symbols=symbol_count,
                        days=day_count,
                        grid=1536,
                        caps=[1, 2, 3, 4, 5],
                    ),
                    populated=populated,
                    producer_sha256=semantic,
                    measurements=matrix,
                    **loop.AUTHORITY,
                )
                loop.atomic_write(output, receipt)
                return receipt
        if mode == "cold":
            digests = hashes
    receipt = dict(
        schema=loop.SCHEMA,
        status="complete",
        fixture="deterministic_390_bars_per_symbol_day_sinusoid_v2",
        populated=populated,
        producer_sha256=semantic,
        measurements=matrix,
        **loop.AUTHORITY,
    )
    loop.atomic_write(output, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", type=int, default=100)
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--populated", action="store_true")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=("cold", "warm", "append"),
        default=["cold", "warm", "append"],
    )
    parser.add_argument("--compute-budget-sec", type=int, default=5400)
    args = parser.parse_args(argv)
    if args.symbols < 1 or args.days < 32:
        raise ValueError("benchmark_fixture_shape_invalid")
    with tempfile.TemporaryDirectory(prefix="research-scale-") as temporary:
        receipt = run(
            args.symbols,
            args.days,
            args.cache or Path(temporary),
            args.output,
            populated=args.populated,
        )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "complete" else 75


if __name__ == "__main__":
    raise SystemExit(main())
