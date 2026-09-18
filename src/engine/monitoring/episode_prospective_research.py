"""Frozen, order-free prospective replay for registered episode discovery lanes."""

from __future__ import annotations

from datetime import date, time
import math

from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    SpotCandidate,
    _evaluate_candidate_windows,
    baseline_candidate,
    paired_economics,
    policy_identity,
    _calibration_ready,
    _manageable_carry,
    _positive_ev,
    _summary,
    COST_PCT,
    ECONOMIC_REPLAY_CONTRACT,
    ECONOMIC_METRIC_CONTRACT,
    clamp_price_to_tick,
    move_price_by_ticks,
)
from src.trading.low_price_two_leg.economics import cost_contract
from src.engine.monitoring.research_source_facts import indexed_day_facts


def spot(parameters):
    start, end = (
        time.fromisoformat(parameters["scan_start"]),
        time.fromisoformat(parameters["scan_end"]),
    )
    return SpotCandidate(
        start.hour * 60 + start.minute,
        end.hour * 60 + end.minute,
        parameters["lookback_bars"],
        parameters["rolling_high_drawdown_pct"],
        parameters["rolling_low_proximity_pct"],
        tuple(parameters["entry_offsets_ticks"]),
        parameters["entry_valid_completed_bars"],
        parameters["target_ticks"],
    )


def _promotion_ready(selected, baseline):
    comparison = paired_economics(baseline["holdout"], selected["holdout"])
    return bool(
        comparison["live_replay_supported"]
        and _calibration_ready(
            selected["calibration"],
            selected["calibration_first_half"],
            selected["calibration_second_half"],
        )
        and all(
            selected[name]["completed_legs"] >= 3
            for name in ("calibration_first_half", "calibration_second_half")
        )
        and selected["holdout"]["signal_episodes"] >= 3
        and selected["holdout"]["completed_legs"] >= 4
        and selected["full"]["completed_legs"] >= 10
        and _manageable_carry(selected["holdout"])
        and _manageable_carry(selected["full"])
        and _positive_ev(selected["holdout"])
        and (comparison["economic_superiority_confirmed"]
             or comparison["participation_net_profit_confirmed"])
    )


def prospective_summary_valid(result, revision):
    """Reconstruct fixed-window economics from native sealed episode snapshots.

    This is a bounded publication/consumer check, not a grid or bar replay.
    Earlier HELD marks remain sealed at their own boundary.
    """
    from src.engine.monitoring.policy_research_economics import aware

    try:
        cal, holdout = revision["calibration_dates"], revision["holdout_dates"]
        windows = dict(
            calibration=cal,
            calibration_first_half=cal[:15],
            calibration_second_half=cal[15:],
            holdout=holdout,
            full=cal + holdout,
        )
        for arm, parameter_key in (
            ("selected", "parameters"),
            ("baseline", "baseline_parameters"),
        ):
            output = result[arm]
            parameters = revision[parameter_key]
            if output["parameters"] != revision[parameter_key]:
                return False
            full = output["full"]["episodes"]
            if not isinstance(full, list) or len(full) > len(windows["full"]):
                return False
            identities = [(row["date"], row["signal_at"]) for row in full]
            if len(identities) != len(set(identities)) or len(
                {day for day, _ in identities}
            ) != len(identities):
                return False
            for name, dates in windows.items():
                summary = output[name]
                episodes = summary["episodes"]
                expected = [row for row in full if row["date"] in dates]
                if not isinstance(episodes, list) or [
                    (row["date"], row["signal_at"]) for row in episodes
                ] != [(row["date"], row["signal_at"]) for row in expected]:
                    return False
                for row, terminal in zip(episodes, expected):
                    clock = aware(row["signal_at"])
                    if (
                        clock is None
                        or str(clock.date()) != row["date"]
                        or row["date"] not in dates
                    ):
                        return False
                    if len(row["legs"]) != 2 or len(terminal["legs"]) != 2:
                        return False
                    if row.get("execution_plan") != {
                        key: parameters[key]
                        for key in (
                            "entry_offsets_ticks",
                            "entry_valid_completed_bars",
                            "target_ticks",
                        )
                    }:
                        return False
                    close = clamp_price_to_tick(row["signal_close"])
                    for offset, leg, later in zip(
                        parameters["entry_offsets_ticks"], row["legs"], terminal["legs"]
                    ):
                        price = move_price_by_ticks(close, offset)
                        if leg["entry_price"] != price:
                            return False
                        if (
                            leg["status"] not in {"COMPLETE", "HELD", "NO_FILL"}
                            or leg["status"] != later["status"]
                        ):
                            return False
                        if leg["status"] != "NO_FILL":
                            target = move_price_by_ticks(
                                price, parameters["target_ticks"]
                            )
                            fill = aware(leg.get("fill_at"))
                            if (
                                leg.get("target_price") != target
                                or fill is None
                                or fill <= clock
                                or fill.date() != clock.date()
                            ):
                                return False
                            if leg["status"] == "COMPLETE":
                                exit_ = aware(leg.get("target_at"))
                                if (
                                    exit_ is None
                                    or exit_ <= fill
                                    or exit_.date() != clock.date()
                                    or leg.get("net_profit_pct")
                                    != round((target / price - 1.0) * 100 - COST_PCT, 6)
                                ):
                                    return False
                        # Native HELD custody never closes through a future bar
                        # touch; only mark/exposure fields may evolve later.
                        if leg["status"] != "HELD" and leg != later:
                            return False
                        if any(
                            leg.get(key) != later.get(key)
                            for key in (
                                "entry_price",
                                "target_price",
                                "fill_at",
                                "target_at",
                                "net_profit_pct",
                            )
                        ):
                            return False
                derived = _summary(episodes)
                derived.update(
                    policy_identity=policy_identity(parameters),
                    observation_dates=dates,
                    source_valid_observation_days=len(dates),
                    cost_pct=COST_PCT,
                    economic_replay_contract=ECONOMIC_REPLAY_CONTRACT,
                    metric_contract=ECONOMIC_METRIC_CONTRACT,
                    cost_adjusted_net_profit_krw_per_source_valid_observation_day=round(
                        derived["realized_net_profit_krw"] / len(dates), 8
                    ),
                    attempted_episodes_per_source_valid_observation_day=round(
                        len(episodes) / len(dates), 8
                    ),
                )
                if loop.digest(derived) != loop.digest(
                    {key: summary.get(key) for key in derived}
                ):
                    return False
        paired = paired_economics(
            result["baseline"]["holdout"], result["selected"]["holdout"]
        )
        return result.get("paired_economics") == paired and _promotion_ready(
            result["selected"], result["baseline"]
        )
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return False


def frozen_research(result, *, profile, contexts, source_date):
    if (
        profile.discovery_lane not in {"new_symbol", "existing_symbol_time_extension", "actual_existing_axis"}
        or profile.fixed_observation
    ):
        return result
    parameters = (
        result.get("calibration_winner")
        or result.get("best_diagnostic_candidate")
        or {}
    ).get("parameters")
    revision = loop.load_candidate(
        profile.symbol, owner="episode", lane_id=profile.profile_id
    )
    previous = revision
    reason = None
    if revision is not None:
        prefix = loop.digest(
            [
                [
                    bar.timestamp.isoformat(),
                    bar.open_price,
                    bar.high_price,
                    bar.low_price,
                    bar.close_price,
                ]
                for day in sorted(contexts)
                if day.isoformat() <= revision["frozen_source_date"]
                for bar in contexts[day].bars
            ]
        )
        if (
            prefix != revision["frozen_source_sha256"]
            or loop.digest(cost_contract()) != revision["cost_sha256"]
        ):
            revision, reason = None, "source_or_cost_correction"
        elif baseline_candidate(profile).public() != revision["baseline_parameters"]:
            revision, reason = None, "incumbent_parent_changed"
    if revision is None:
        if not isinstance(parameters, dict):
            return result
        revision = loop.candidate_revision(
            symbol=profile.symbol,
            owner="episode",
            lane_id=profile.profile_id,
            parameters=parameters,
            source_date=source_date,
            source_sha256=loop.digest(
                [
                    [
                        bar.timestamp.isoformat(),
                        bar.open_price,
                        bar.high_price,
                        bar.low_price,
                        bar.close_price,
                    ]
                    for day in sorted(contexts)
                    for bar in contexts[day].bars
                ]
            ),
            cost_sha256=loop.digest(cost_contract()),
            calibration_days=30,
            holdout_days=16,
            baseline_parameters=baseline_candidate(profile).public(),
            baseline_policy_id=profile.profile_id,
            supersedes_revision_sha256=previous["revision_sha256"] if reason else None,
            supersession_reason=reason,
        )
    result = {
        **result,
        "historical_proxy_diagnostic": {
            key: result.get(key)
            for key in ("decision", "recommended_spot", "date_split")
        },
        "candidate_revision": revision,
        "prospective_window": loop.prospective_window(
            revision, source_date=source_date, qualified_dates=contexts
        ),
        "recommended_spot": revision["parameters"],
        "prospective_qualified_dates": [day.isoformat() for day in sorted(contexts)],
    }
    if result["prospective_window"]["status"] != "ready":
        result["decision"] = (
            "pending_prospective_validation_no_episode_runtime_promotion"
        )
        return result
    cal = [date.fromisoformat(day) for day in revision["calibration_dates"]]
    holdout = [date.fromisoformat(day) for day in revision["holdout_dates"]]
    # A never traded seed starts flat at its registered activation. Earlier CF
    # inventory belongs to the historical proxy, not to the prospective seed.
    prospective = {day: context for day, context in contexts.items() if day >= cal[0]}
    windows = dict(
        calibration=cal,
        calibration_first_half=cal[:15],
        calibration_second_half=cal[15:],
        holdout=holdout,
        full=cal + holdout,
    )
    selected = {"parameters": revision["parameters"]}
    baseline = {"parameters": revision["baseline_parameters"]}
    names = list(windows)
    for output, parameters in (
        (selected, revision["parameters"]),
        (baseline, revision["baseline_parameters"]),
    ):
        evaluated = _evaluate_candidate_windows(
            spot(parameters),
            prospective,
            [windows[name] for name in names],
            include_episodes=True,
        )
        output.update(zip(names, evaluated))
    paired = paired_economics(baseline["holdout"], selected["holdout"])
    ready = _promotion_ready(selected, baseline)
    result.update(
        selected=selected,
        baseline=baseline,
        paired_economics=paired,
        decision="holdout_pass_source_only_early_candidate"
        if ready
        else "prospective_holdout_failed_no_episode_runtime_promotion",
    )
    proof = execution_feasibility(result, source_date=source_date)
    result["execution_feasibility"] = proof
    if ready and proof["status"] != "pass":
        result["decision"] = (
            "execution_feasibility_missing_no_episode_runtime_promotion"
        )
    return result


def execution_feasibility(result, *, source_date, directory=loop.DIRECTORY, arm="selected"):
    """Exact seeded full-depth CF, with TTL NO_FILL and shared-depth accounting."""
    revision = loop.validate_revision(
        result["candidate_revision"], symbol=result["symbol"], owner="episode"
    )
    receipt = dict(
        schema=loop.SCHEMA,
        status="source_gap",
        arm=arm,
        revision_sha256=revision["revision_sha256"],
        source_hashes={},
        source_generations={},
        depth_demands=[],
        matched_completed_legs=0,
        evidence_role="executable_CF_not_actual_broker_fill",
        **loop.AUTHORITY,
    )
    from src.engine.monitoring.policy_research_economics import aware
    from datetime import timedelta

    if arm not in {"selected", "baseline"}:
        raise ValueError("execution_arm_invalid")
    episodes = (result.get(arm) or {}).get("full", {}).get("episodes")
    if not isinstance(episodes, list) or not episodes:
        return {**receipt, "reason": "prospective_episode_lineage_missing"}
    if (
        source_date.isoformat() < revision["holdout_dates"][-1]
        or (result.get(arm) or {}).get("parameters") != revision["baseline_parameters" if arm == "baseline" else "parameters"]
        or loop.digest(cost_contract()) != revision["cost_sha256"]
    ):
        return {**receipt, "reason": "prospective_window_parameters_or_cost_invalid"}
    demand, identities = {}, set()
    for episode in episodes:
        signal = aware(episode.get("signal_at"))
        if (
            signal is None
            or signal.date() > source_date
            or signal.date().isoformat()
            not in revision["calibration_dates"] + revision["holdout_dates"]
        ):
            return {**receipt, "reason": "prospective_signal_calendar_invalid"}
        windows_by_day = {}
        for leg in episode.get("legs") or []:
            if leg.get("status") == "NO_FILL":
                start = signal + timedelta(minutes=1)
                end = start + timedelta(
                    minutes=revision["parameters"]["entry_valid_completed_bars"]
                )
                windows_by_day.setdefault(start.date(), []).append((start, end))
            else:
                for field in ("fill_at", "target_at"):
                    anchor = aware(leg.get(field))
                    if anchor is not None:
                        windows_by_day.setdefault(anchor.date(), []).append(
                            (anchor, anchor + timedelta(seconds=5))
                        )
        books = []
        try:
            for day, windows in sorted(windows_by_day.items()):
                from src.engine.monitoring.research_fact_archive import fact_path

                path = fact_path(directory, result["symbol"], day)
                sha, facts = indexed_day_facts(path, windows=windows)
                receipt["source_hashes"][str(path)] = sha
                from src.engine.monitoring.research_source_facts import generation

                receipt["source_generations"][str(path)] = generation(path.lstat())
                for row in facts:
                    members = row.get("seed_memberships") or ()
                    if (
                        row.get("schema")
                        != "prospective_registered_seed_market_facts_v1"
                        or row.get("source_quality_status") != "PASS"
                        or row.get("market_venue") != "KRX"
                        or any(row.get(k) is not v for k, v in loop.AUTHORITY.items())
                        or not any(
                            member.get("revision_sha256") == revision["revision_sha256"]
                            and member.get("parameters_sha256")
                            == revision["parameters_sha256"]
                            and member.get("frozen_at") == revision["frozen_at"]
                            for member in members
                        )
                    ):
                        continue
                    at, received = (
                        aware(row.get("observed_at_kst")),
                        aware((row.get("bbo") or {}).get("received_at")),
                    )
                    bbo = row.get("bbo") or {}
                    if (
                        at is None
                        or received is None
                        or at <= aware(revision["frozen_at"])
                        or at.date() != day
                        or received.date() != day
                        or not 0 <= (at - received).total_seconds() <= 5
                        or any(
                            type(bbo.get(k)) not in (int, float)
                            or not math.isfinite(bbo[k])
                            or bbo[k] <= 0
                            for k in (
                                "best_bid",
                                "best_ask",
                                "best_bid_qty",
                                "best_ask_qty",
                            )
                        )
                        or bbo["best_bid"] > bbo["best_ask"]
                        or type(bbo.get("source_epoch")) is not int
                        or bbo["source_epoch"] <= 0
                    ):
                        continue
                    books.append((at, bbo))
                books.sort(key=lambda value: value[0])
        except (OSError, ValueError, TypeError):
            return {**receipt, "reason": "prospective_source_missing_or_invalid"}
        if len(episode.get("legs") or []) != 2:
            return {**receipt, "reason": "prospective_two_leg_lineage_incomplete"}
        for leg_index, leg in enumerate(episode["legs"]):
            identity = signal, leg_index
            if identity in identities:
                return {**receipt, "reason": "duplicate_prospective_leg"}
            identities.add(identity)
            if leg.get("status") == "NO_FILL":
                start = signal + timedelta(minutes=1)
                end = start + timedelta(
                    minutes=revision["parameters"]["entry_valid_completed_bars"]
                )
                samples = [(at, book) for at, book in books if start <= at <= end]
                if (
                    not samples
                    or (samples[0][0] - start).total_seconds() > 5
                    or (end - samples[-1][0]).total_seconds() > 5
                    or any(
                        (right[0] - left[0]).total_seconds() > 5
                        or right[1]["source_epoch"] != left[1]["source_epoch"]
                        for left, right in zip(samples, samples[1:])
                    )
                    or any(
                        book["best_ask"] <= leg["entry_price"] for _, book in samples
                    )
                ):
                    return {**receipt, "reason": "no_fill_TTL_path_not_proven"}
                continue
            if leg.get("status") != "COMPLETE":
                return {**receipt, "reason": "partial_held_or_censored_leg"}
            entry, exit_ = aware(leg.get("fill_at")), aware(leg.get("target_at"))
            if (
                entry is None
                or exit_ is None
                or entry < signal + timedelta(minutes=1)
                or exit_ <= entry
                or exit_.date() > source_date
                or type(leg.get("entry_price")) not in (int, float)
                or leg["entry_price"] <= 0
                or type(leg.get("target_price")) not in (int, float)
                or type(leg.get("net_profit_pct")) not in (int, float)
                or not math.isfinite(leg["net_profit_pct"])
                or abs(
                    leg["net_profit_pct"]
                    - (
                        (leg["target_price"] / leg["entry_price"] - 1) * 100
                        - cost_contract()["round_trip_cost_pct"]
                    )
                )
                > 0.0000011
            ):
                return {**receipt, "reason": "prospective_leg_clock_invalid"}
            opening = next(
                (
                    (at, bbo)
                    for at, bbo in books
                    if 0 <= (at - entry).total_seconds() <= 5
                    and bbo["best_ask"] <= leg["entry_price"]
                ),
                None,
            )
            closing = next(
                (
                    (at, bbo)
                    for at, bbo in books
                    if opening
                    and 0 <= (at - exit_).total_seconds() <= 5
                    and bbo["best_bid"] >= leg["target_price"]
                    and (
                        exit_.date() != entry.date()
                        or bbo["source_epoch"] == opening[1]["source_epoch"]
                    )
                ),
                None,
            )
            if opening is None or closing is None:
                return {**receipt, "reason": "exact_seed_depth_or_epoch_missing"}
            for side, quote in (("best_ask_qty", opening), ("best_bid_qty", closing)):
                key = (
                    quote[0],
                    quote[1]["source_epoch"],
                    quote[1].get("source_sequence"),
                    side,
                )
                prior = demand.get(key, 0)
                if prior + 40 > quote[1][side]:
                    return {
                        **receipt,
                        "reason": "shared_depth_insufficient_for_full_stress_quantity",
                    }
                demand[key] = prior + 40
                receipt["depth_demands"].append(
                    dict(
                        quote_id=loop.digest(
                            [
                                result["symbol"],
                                quote[1].get("source_epoch"),
                                quote[1].get("received_at"),
                                quote[1].get("source_sequence"),
                                side,
                            ]
                        ),
                        stress_quantity=40,
                        available_quantity=quote[1][side],
                    )
                )
            receipt["matched_completed_legs"] += 1
    return loop.seal_execution_receipt(
        {
            **receipt,
            "status": "pass",
            "reason": "frozen_seed_full_depth_TTL_and_epoch_CF_validated",
        }
    )
