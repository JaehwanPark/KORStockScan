"""Offline native episode grids; synthetic bars, no API or publication authority."""

import argparse
from copy import deepcopy
from dataclasses import asdict
import gc
import json
from pathlib import Path
import resource
import tempfile
import time

from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring import low_price_two_leg_entry_spot_research as spot
from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as expanded,
)
from src.engine.monitoring.research_scale_benchmark import fixture
from src.engine.monitoring.widget_symbol_signal_policy_research import (
    research_contract_hash,
)
from src.trading.low_price_two_leg.profiles import PROFILES


def run(symbols, days, output, cache, budget=5400):
    semantic = research_contract_hash()
    templates = list(PROFILES.values())
    measurements, cold_hashes, grids = {}, {}, {}
    for mode in ("cold", "warm", "append"):
        candidate_wall = candidate_cpu = reference_cpu = preparation_cpu = 0.0
        hits, transitions, hashes = {}, {}, {}
        for i in range(symbols):
            template = templates[i % len(templates)]
            profile = template
            prepare = time.process_time()
            bars, dates = fixture(days + (mode == "append"), i, populated=True)
            contexts = spot.build_day_contexts(bars)
            calibration_days = len(dates) - spot.HOLDOUT_DAYS
            grids[str(i)] = len(spot.candidate_grid(profile))
            contract = dict(
                fixture="deterministic_synthetic_390_bars_not_native_source",
                producer_sha256=semantic,
                profile=json.loads(
                    json.dumps(asdict(profile), default=lambda v: v.isoformat())
                ),
                source_sha256=expanded._canonical_digest(expanded._bar_rows(bars)),
                observation_dates=[str(d) for d in dates],
                calibration_days=calibration_days,
                holdout_days=spot.HOLDOUT_DAYS,
                grid=[item.public() for item in spot.candidate_grid(profile)],
            )
            preparation_cpu += time.process_time() - prepare
            wall, cpu = time.monotonic(), time.process_time()
            result = expanded._select_profile_checkpoint(
                profile,
                contexts,
                calibration_days=calibration_days,
                cache_dir=cache / str(i),
                contract=contract,
                stats=hits,
                day_stats=transitions,
            )
            candidate_wall += time.monotonic() - wall
            candidate_cpu += time.process_time() - cpu
            digest = loop.digest(result)
            assert result["grid_candidate_count"] == grids[str(i)]
            if mode == "warm":
                assert digest == cold_hashes[str(i)], "warm_native_episode_parity"
            else:
                control = time.process_time()
                reference = spot.select_profile_spot(
                    profile,
                    deepcopy(contexts),
                    calibration_days=calibration_days,
                    holdout_days=spot.HOLDOUT_DAYS,
                )
                reference_cpu += time.process_time() - control
                assert digest == loop.digest(reference), (
                    "original_native_episode_parity"
                )
                del reference
            hashes[str(i)] = digest
            if i + 1 in {19, 50, 100, symbols} or candidate_wall > budget:
                measurements[f"{mode}_N{i + 1}_D{len(dates)}"] = dict(
                    candidate_compute_wall_seconds=candidate_wall,
                    candidate_compute_cpu_seconds=candidate_cpu,
                    separate_reference_cpu_seconds=reference_cpu,
                    separate_preparation_cpu_seconds=preparation_cpu,
                    native_grid_sizes=sorted(set(grids.values())),
                    native_grid_total=sum(grids.values()),
                    checkpoint=hits.copy(),
                    day_transitions=transitions.copy(),
                    canonical_original_parity=True,
                    digest=loop.digest(hashes),
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    remote_requests=0,
                )
                receipt = dict(
                    status="deferred" if candidate_wall > budget else "running",
                    reason="compute_phase_budget_exceeded"
                    if candidate_wall > budget
                    else None,
                    fixture="native_templates_synthetic_390_bars_no_broker_or_policy_acceptance",
                    producer_sha256=semantic,
                    measurements=measurements,
                    requested_scope=dict(
                        symbols=symbols, days=days, modes=["cold", "warm", "append"]
                    ),
                    completed_symbol_count=i + 1,
                    unprocessed_symbol_count=symbols - i - 1,
                    **loop.AUTHORITY,
                )
                loop.atomic_write(output, receipt)
                if candidate_wall > budget:
                    return receipt
            del contexts, bars, result
            gc.collect()
        if mode == "cold":
            cold_hashes = hashes
    receipt.update(status="complete", reason=None)
    loop.atomic_write(output, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", type=int, default=3)
    parser.add_argument("--days", type=int, default=46)
    parser.add_argument("--budget", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.symbols <= 100 or not 46 <= args.days <= 121 or args.budget <= 0:
        raise ValueError("synthetic_episode_fixture_scope_invalid")
    with tempfile.TemporaryDirectory(prefix="episode-native-grid-fixture-") as tmp:
        receipt = run(args.symbols, args.days, args.output, Path(tmp), args.budget)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "complete" else 75


if __name__ == "__main__":
    raise SystemExit(main())
