"""Offline synthetic C4/C7 statistics scale; no broker or policy acceptance.

Owned by analysis/benchmarks. All cost rows are invented fixture inputs, written
only to a temporary directory. No native source reads, accounts or publication.
"""

from datetime import date
import json, resource, tempfile, time
from pathlib import Path
from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring import research_portfolio_economics as portfolio
from src.engine.monitoring import research_version_outcomes as outcomes
from src.engine.monitoring.widget_symbol_signal_policy_research import (
    research_contract_hash,
)


def run(output):
    measurements = {}
    for d in (72, 120):
        dates = loop.trading_dates_after(date(2026, 6, 4), d)
        for n in (19, 50, 100):
            start, cpu = time.monotonic(), time.process_time()
            lanes = {}
            for i in range(n):
                lane = {}
                for window, days in [
                    ("calibration", dates[:-16]),
                    ("holdout", dates[-16:]),
                ]:
                    lane[window + "_dates"] = days
                    for side, net in [("candidate", 0.3), ("incumbent", 0.2)]:
                        lane[side + "_" + window] = [
                            dict(
                                entry_at=day + "T09:10:00+09:00",
                                exit_at=day + "T09:15:00+09:00",
                                entry_price=10000,
                                net_return_pct=net,
                            )
                            for day in days
                        ]
                lanes["widget:" + str(i)] = lane
            inputs = [
                dict(portfolio_reference=dict(lanes=lanes, missing_reference_lanes=[]))
            ]
            snapshot = dict(
                available_cash_krw=n * 200000,
                reserved_notional_krw=0,
                exposure_limit_krw=n * 200000,
                holding_notional_krw=0,
                constraints=dict(buy_fee_bps=5),
            )
            comparison = portfolio.paired_joint_economics(inputs, snapshot)
            assert comparison["status"] == "pass"
            joint_cpu = time.process_time() - cpu
            joint_digest = loop.digest(comparison)
            with tempfile.TemporaryDirectory(
                prefix="completion-native-feedback-fixture-"
            ) as tmp:
                root = Path(tmp)
                for day in dates:
                    rows = []
                    for i in range(n):
                        revision = loop.digest(["revision", i])
                        version = loop.digest(["version", i])
                        rows.append(
                            dict(
                                profile_id="widget_" + str(i),
                                native_attempt_id=loop.digest([i, day]),
                                target_date=day,
                                attempted=True,
                                execution_policy_content_sha256=version,
                                candidate_revision_sha256=revision,
                                source_quality="pass",
                                eligible_for_tuning=True,
                                outcome_complete_for_ev=True,
                                legs=[dict(completed=True)],
                                broker_realized_economics=dict(
                                    status="matched_exact",
                                    realized_net_profit_krw=-730,
                                    buy_notional_krw=100000,
                                    commission_krw=30,
                                    tax_krw=200,
                                    realized_net_return_pct=-0.73,
                                ),
                            )
                        )
                    body = dict(source_date=day, rows=rows, **loop.AUTHORITY)
                    loop.atomic_write(
                        root / ("widget_outcomes_" + day + ".json"),
                        dict(body, outcomes_sha256=loop.digest(body)),
                    )
                feedback = outcomes.outcome_feedback(
                    date.fromisoformat(dates[-1]), directory=root
                )
                assert len(outcomes.mature_widget_retired_revisions(feedback)) == n
                assert all(
                    v["exact_completed_count"] == d
                    for v in feedback["cumulative"]["strategy_revisions"].values()
                )
                assert all(
                    v["exact_completed_count"] == 16
                    for v in feedback["holdout_last_16"]["strategy_revisions"].values()
                )
                fixture_bytes = sum(p.stat().st_size for p in root.glob("*.json"))
            measurements["N" + str(n) + "D" + str(d)] = dict(
                wall_seconds=time.monotonic() - start,
                cpu_seconds=time.process_time() - cpu,
                joint_compute_cpu_seconds=joint_cpu,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                native_fixture_bytes=fixture_bytes,
                normalized_exact_cost_outcomes=n * d,
                paired_trade_episodes=2 * n * d,
                joint_digest=joint_digest,
                feedback_digest=loop.digest(feedback),
                remote_requests=0,
            )
            loop.atomic_write(
                output,
                dict(
                    status="running",
                    fixture="synthetic_normalized_exact_cost_and_paired_statistics_not_native_broker_or_candidate_publication_acceptance",
                    producer_sha256=research_contract_hash(),
                    measurements=measurements,
                    **loop.AUTHORITY,
                ),
            )
    loop.atomic_write(
        output,
        dict(
            status="complete",
            fixture="synthetic_normalized_exact_cost_and_paired_statistics_not_native_broker_or_candidate_publication_acceptance",
            producer_sha256=research_contract_hash(),
            measurements=measurements,
            **loop.AUTHORITY,
        ),
    )
    return measurements


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), sort_keys=True))


if __name__ == "__main__":
    main()
