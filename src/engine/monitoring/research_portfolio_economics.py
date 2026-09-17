"""Fixed-allocator, paired portfolio evidence; no allocation or order authority."""

from datetime import datetime
import math

from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring.policy_research_economics import joint_capital_demand


def reference_inputs(report, family):
    """Keep the registered calendar and original incumbent on each causal lane."""
    lanes, failures = {}, []
    for key, result in report.get(
        "symbols" if family == "widget" else "profiles", {}
    ).items():
        expected = (
            "holdout_pass_widget_signal_policy_candidate"
            if family == "widget"
            else "holdout_pass_source_only_early_candidate"
        )
        if result.get("decision") != expected:
            continue
        revision = result.get("candidate_revision")
        if revision is None:
            baseline_arm = (
                (result.get("component_comparison") or {}).get("arms") or {}
            ).get("applied_baseline")
            parameters = result.get("selected_policy") or {}
            if (
                family != "widget"
                or not isinstance(baseline_arm, dict)
                or baseline_arm.get("parameters") != parameters
            ):
                failures.append(key)
                continue
            split = result.get("date_split") or {}
            qualified = (
                ((report.get("source_meta") or {}).get(key) or {}).get(
                    "daily_source_coverage"
                )
                or {}
            ).get("qualified_dates", [])
            revision = {
                name + "_dates": [
                    day
                    for day in qualified
                    if split.get(name + "_start", "~")
                    <= day
                    <= split.get(name + "_end", "")
                ]
                for name in ("calibration", "holdout")
            }
            revision["baseline_parameters"] = baseline_arm["parameters"]
            if not all(
                revision[name + "_dates"] for name in ("calibration", "holdout")
            ):
                failures.append(key)
                continue
        else:
            loop.validate_revision(revision, owner=family)
        if family == "widget":
            candidate = result
            baseline = (
                (result.get("component_comparison") or {}).get("arms") or {}
            ).get("applied_baseline")
            if revision.get("baseline_parameters") is None:
                baseline = {
                    name: {"episodes": []} for name in ("calibration", "holdout")
                }
        else:
            candidate, baseline = result.get("selected"), result.get("baseline")
        if not isinstance(baseline, dict) or not isinstance(candidate, dict):
            failures.append(key)
            continue

        def rows(summary):
            if family == "widget":
                return summary.get("episodes", [])
            converted = []
            for episode in summary.get("episodes", []):
                legs = episode.get("legs")
                if (
                    not isinstance(legs, list)
                    or len(legs) != 2
                    or any(
                        not isinstance(leg, dict) or leg.get("status") != "COMPLETE"
                        for leg in legs
                    )
                ):
                    raise ValueError("joint_reference_partial_held_or_missing_leg")
                for i, leg in enumerate(legs):
                    converted.append(
                        dict(
                            entry_at=leg.get("fill_at"),
                            exit_at=leg.get("target_at"),
                            entry_price=leg.get("entry_price"),
                            net_return_pct=leg.get("net_profit_pct"),
                            leg_index=i,
                        )
                    )
            return converted

        windows = {}
        for name in ("calibration", "holdout"):
            dates = revision[name + "_dates"]
            for side, source in (("candidate", candidate), ("incumbent", baseline)):
                summary = source.get(name)
                if not isinstance(summary, dict) or "episodes" not in summary:
                    raise ValueError("joint_reference_native_episodes_missing")
                converted = rows(summary)
                if any(
                    str(row.get("entry_at", ""))[:10] not in dates for row in converted
                ):
                    raise ValueError("joint_reference_episode_outside_frozen_calendar")
                windows[side + "_" + name] = converted
            windows[name + "_dates"] = dates
        lanes[family + ":" + key] = windows
    return dict(lanes=lanes, missing_reference_lanes=failures)


def _summary(lanes, side, window, limit, fee):
    dates = sorted(
        {day for value in lanes.values() for day in value[window + "_dates"]}
    )
    groups, daily, costs, minutes = {}, dict.fromkeys(dates, 0.0), 0.0, 0.0
    for lane, value in lanes.items():
        for row in value[side + "_" + window]:
            start, end = (
                datetime.fromisoformat(row["entry_at"]),
                datetime.fromisoformat(row["exit_at"]),
            )
            price, net = row["entry_price"], row["net_return_pct"]
            if (
                start.tzinfo is None
                or end.tzinfo is None
                or end <= start
                or any(
                    type(x) not in (int, float) or not math.isfinite(x)
                    for x in (price, net)
                )
                or price <= 0
                or end.date().isoformat() not in value[window + "_dates"]
            ):
                raise ValueError("joint_reference_economics_invalid")
            group = lane + ":" + str(row.get("leg_index", 0))
            groups.setdefault(group, []).append(row)
            notional = price * 10
            daily[start.date().isoformat()] += notional * net / 100
            costs += notional
            minutes += notional * (end - start).total_seconds() / 60
    demand = joint_capital_demand(groups, capital_limit_krw=limit, buy_fee_bps=fee)
    pnl = demand["independent_modeled_net_profit_krw"]
    return dict(
        demand=demand,
        observation_dates=dates,
        daily_net_profit_krw=daily,
        modeled_net_profit_krw=pnl,
        net_profit_krw_per_day=pnl / len(dates) if dates and pnl is not None else None,
        notional_weighted_ev_pct=pnl / costs * 100
        if costs and pnl is not None
        else None,
        worst_day_net_profit_krw=min(daily.values()) if dates else None,
        capital_krw_minutes=minutes,
        buy_notional_krw=costs,
    )


def paired_joint_economics(inputs, snapshot):
    """Reconstruct fixed composition; never select a holdout subset or new rule."""
    blocked = dict(
        status="allocation_blocked",
        reason="joint_incumbent_reference_missing_or_invalid",
        **loop.AUTHORITY,
    )
    try:
        lanes = {}
        for value in inputs:
            reference = value.get("portfolio_reference") or {}
            if reference.get("missing_reference_lanes"):
                return blocked
            for key, lane in reference.get("lanes", {}).items():
                if key in lanes:
                    raise ValueError("joint_reference_duplicate_lane")
                lanes[key] = lane
        if not lanes:
            return {**blocked, "reason": "no_registered_joint_candidate_reference"}
        constraints = snapshot["constraints"]
        limit = min(
            snapshot["available_cash_krw"] - snapshot["reserved_notional_krw"],
            snapshot["exposure_limit_krw"]
            - snapshot["holding_notional_krw"]
            - snapshot["reserved_notional_krw"],
        )
        fee = constraints["buy_fee_bps"]
        windows, passed = {}, True
        for name in ("calibration", "holdout"):
            current = _summary(lanes, "candidate", name, limit, fee)
            baseline = _summary(lanes, "incumbent", name, limit, fee)
            valid = (
                current["demand"]["capital_feasible"]
                and baseline["demand"]["capital_feasible"]
            )
            valid &= (
                current["net_profit_krw_per_day"] is not None
                and baseline["net_profit_krw_per_day"] is not None
            )
            valid &= (
                current["net_profit_krw_per_day"] >= baseline["net_profit_krw_per_day"]
            )
            # A no-entry control has no estimated return or tail sample. Family
            # guards own its risk, instead of treating absent trades as a lossless strategy.
            if baseline["buy_notional_krw"]:
                valid &= (
                    current["notional_weighted_ev_pct"] is not None
                    and current["notional_weighted_ev_pct"]
                    >= baseline["notional_weighted_ev_pct"]
                )
                valid &= (
                    current["worst_day_net_profit_krw"]
                    >= baseline["worst_day_net_profit_krw"]
                )
            windows[name] = dict(
                candidate=current, incumbent=baseline, nondegradation_passed=bool(valid)
            )
            passed &= valid
        body = dict(
            status="pass" if passed else "allocation_blocked",
            reason="fixed_allocator_paired_joint_non_degradation"
            if passed
            else "joint_incumbent_economics_or_tail_degraded",
            windows=windows,
            allocator_rule="fixed_existing_allocator_no_research_arbitration",
            reference_sha256=loop.digest(
                [v.get("portfolio_reference") for v in inputs]
            ),
            **loop.AUTHORITY,
        )
        return {**body, "economics_sha256": loop.digest(body)}
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError):
        return blocked
