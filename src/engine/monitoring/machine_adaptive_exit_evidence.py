"""Paired episode-level economic aggregation with fixed chronological windows.

The caller supplies a frozen contract and all source trading dates, including
zero-yield dates. Legs are not samples, unresolved paths are not zero returns,
and base/stress execution models never establish real broker fill quality.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import mean, median
from zoneinfo import ZoneInfo

from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    EVIDENCE_SCHEMA,
    EvaluationContract,
    assess_research_evidence,
    canonical_sha256,
)
from src.trading.order.adaptive_exit.models import finite
from src.trading.order.adaptive_exit.source import validate_source_day
from src.utils.market_day import is_krx_trading_day


def _day(ms):
    if type(ms) is not int or ms <= 0:
        raise ValueError("invalid_episode_timestamp")
    return datetime.fromtimestamp(ms / 1000, ZoneInfo("Asia/Seoul")).date().isoformat()


def _quantile(values, q):
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lo = int(index)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def build_evidence(
    pairs: list[dict],
    contract: EvaluationContract,
    *,
    source_trading_dates: tuple[str, ...],
    model_id: str,
    expected_episode_lots: dict[str, tuple[str, ...]],
) -> dict:
    """Expected lots come from the whole owner census, not resolved rows."""
    if (
        not source_trading_dates
        or tuple(sorted(set(source_trading_dates))) != source_trading_dates
    ):
        raise ValueError("source_calendar_must_include_unique_ordered_zero_yield_days")
    for day in source_trading_dates:
        validate_source_day(day)
    first = date.fromisoformat(source_trading_dates[0])
    last = date.fromisoformat(source_trading_dates[-1])
    expected_dates = []
    day = first
    while day <= last:
        if is_krx_trading_day(day):
            expected_dates.append(day.isoformat())
        day += timedelta(days=1)
    if tuple(expected_dates) != source_trading_dates:
        raise ValueError("source_calendar_has_missing_or_nontrading_days")
    if (
        source_trading_dates[-1] != contract.holdout_end
        or contract.holdout_start not in source_trading_dates
        or contract.train_end not in source_trading_dates
    ):
        raise ValueError("source_calendar_does_not_cover_frozen_split")
    if any(
        not eid
        or not lots
        or len(set(lots)) != len(lots)
        or any(not isinstance(lot, str) or not lot for lot in lots)
        for eid, lots in expected_episode_lots.items()
    ):
        raise ValueError("episode_lot_census_invalid")
    grouped = defaultdict(dict)
    errors, purged, units = [], [], []
    seen = set()
    for pair in pairs:
        if (
            pair.get("policy_hash") != contract.policy_hash
            or pair.get("model_id") != model_id
        ):
            continue
        a, b = pair["baseline"], pair["candidate"]
        identity_fields = (
            "owner_id",
            "scope_key",
            "episode_id",
            "lot_id",
            "position_epoch",
            "entry_policy_hash",
            "cost_contract_hash",
            "source_hash",
            "first_fill_at_ms",
            "horizon_end_ms",
            "entry_notional_krw",
            "model_hash",
        )
        if any(a.get(k) != b.get(k) for k in identity_fields):
            errors.append("paired_identity_or_cost_mismatch")
            continue
        eid, lot = a.get("episode_id"), a.get("lot_id")
        key = (eid, lot)
        if key in seen:
            errors.append("duplicate_episode_lot")
            continue
        seen.add(key)
        if (
            a.get("scope_key") != contract.scope_key
            or a.get("policy_hash") != contract.policy_hash
            or b.get("policy_hash") != contract.policy_hash
            or lot not in expected_episode_lots.get(eid, ())
            or a.get("baseline") is not True
            or b.get("baseline") is not False
            or any(
                x.get("authority") != AUTHORITY
                or any(
                    x.get("authority", {}).get(k) is not v for k, v in AUTHORITY.items()
                )
                or x.get("actual_broker_terminal") is not False
                for x in (a, b)
            )
        ):
            errors.append("scope_census_or_authority_mismatch")
            continue
        grouped[eid][lot] = (a, b)
    for eid, lots in expected_episode_lots.items():
        rows = grouped[eid]
        if set(rows) != set(lots):
            continue
        entry_days = {_day(a["first_fill_at_ms"]) for a, _ in rows.values()}
        end_days = {_day(a["horizon_end_ms"]) for a, _ in rows.values()}
        if len(entry_days) != 1:
            errors.append("mixed_episode_entry_dates")
            continue
        start, end = next(iter(entry_days)), max(end_days)
        if start not in source_trading_dates or end > contract.holdout_end:
            continue
        if start <= contract.train_end and end >= contract.holdout_start:
            purged.append(eid)
            continue
        if contract.train_end < start < contract.holdout_start:
            purged.append(eid)
            continue
        if any(
            x.get("counterfactual_exit_resolved") is not True
            or x.get("remaining_quantity") != 0
            or any(
                not finite(x.get(k))
                for k in ("net_pnl_krw", "net_ev_pct", "entry_notional_krw")
            )
            or x["entry_notional_krw"] <= 0
            for pair in rows.values()
            for x in pair
        ):
            continue
        if (
            len({a["cost_contract_hash"] for a, _ in rows.values()}) != 1
            or len({a["entry_policy_hash"] for a, _ in rows.values()}) != 1
        ):
            errors.append("mixed_episode_cost_or_entry_policy_contracts")
            continue
        if any(
            abs(x["net_ev_pct"] - x["net_pnl_krw"] / x["entry_notional_krw"] * 100)
            > 1e-7
            for pair in rows.values()
            for x in pair
        ):
            errors.append("paired_economic_arithmetic_mismatch")
            continue
        notional = sum(a["entry_notional_krw"] for a, _ in rows.values())
        base = sum(a["net_pnl_krw"] for a, _ in rows.values())
        candidate = sum(b["net_pnl_krw"] for _, b in rows.values())
        occupancy = {}
        for label, index in (("base", 0), ("candidate", 1)):
            durations = []
            for pair in rows.values():
                x = pair[index]
                end_ms, start_ms = x.get("closed_at_ms"), x["first_fill_at_ms"]
                if (
                    type(end_ms) is not int
                    or not start_ms <= end_ms <= x["horizon_end_ms"]
                ):
                    durations = []
                    break
                durations.append((end_ms - start_ms, x["entry_notional_krw"]))
            occupancy[label + "_terminal_duration_ms"] = (
                max(ms for ms, _ in durations) if durations else None
            )
            occupancy[label + "_capital_krw_minutes"] = (
                sum(ms / 60_000 * amount for ms, amount in durations)
                if durations
                else None
            )
        units.append(
            {
                "episode_id": eid,
                "day": start,
                "notional": notional,
                "base": base,
                "candidate": candidate,
                "uplift": (candidate - base) / notional * 100,
                **occupancy,
            }
        )
    count = len(units)
    denominator = len(expected_episode_lots) - len(purged)
    holdout = [u for u in units if u["day"] >= contract.holdout_start]
    summary = {
        "schema": EVIDENCE_SCHEMA,
        "metric_contract": {
            "metric_role": "owned_exit_counterfactual_policy_research",
            "primary_decision_metric": "primary_paired_net_ev_uplift_pct_points",
            "formula": "equal_weight_mean_of_complete_episode_paired_net_pnl_difference_divided_by_same_episode_entry_notional_times_100",
            "denominator": "complete_paired_unique_owner_scope_episode_not_legs_or_ticks",
            "window_policy": "frozen_clean_source_days_with_purged_chronological_holdout",
            "sample_floor_owner": "external_evaluation_contract_hash",
            "source_quality_gate": "whole_owner_lot_census_and_same_scope_cost_policy_path_binding",
            "decision_authority": "research_only_no_broker_or_runtime_apply",
            "forbidden_uses": [
                "actual_broker_fill_quality",
                "realized_pnl",
                "full_population_ev_extrapolation",
                "runtime_activation",
            ],
        },
        "authority": dict(AUTHORITY),
        "evaluation_contract_hash": contract.contract_hash,
        "scope_key": contract.scope_key,
        "policy_hash": contract.policy_hash,
        "holdout_start": contract.holdout_start,
        "holdout_end": contract.holdout_end,
        "model_id": model_id,
        "source_quality_valid": not errors,
        "cost_contract_valid": not errors,
        "purged_split_valid": not errors,
        "unique_episodes": count,
        "holdout_unique_episodes": len(holdout),
        "observed_days": len(source_trading_dates),
        "source_trading_dates": list(source_trading_dates),
        "purged_episode_ids": purged,
        "expected_unique_episodes": len(expected_episode_lots),
        "resolved_coverage_pct": 100 * count / denominator if denominator else 0,
        "right_censored_pct": (
            100 * (denominator - count) / denominator if denominator else 100
        ),
        "contract_errors": sorted(set(errors)),
        "episode_units": units,
        "p10_deterioration_pct_points": None,
        "uncertainty": {
            "unit": "source_day_cluster",
            "daily_mean_uplift_pct_points": {},
            "minimum_daily_uplift_pct_points": None,
        },
        "broker_execution_quality_approved": False,
        "turnover_diagnostics": {
            "denominator": "same_complete_paired_episode_subset_not_all_holdings",
            "frequency_denominator_days": len(source_trading_dates),
            "unresolved_episode_count": denominator - count,
            "not_a_live_gate_or_causal_profit_claim": True,
        },
    }
    for label in ("base", "candidate"):
        profitable = sum(u[label] > 0 for u in units)
        occupancy = [u[label + "_capital_krw_minutes"] for u in units]
        durations = [u[label + "_terminal_duration_ms"] for u in units]
        complete = bool(units) and all(v is not None for v in occupancy + durations)
        capital_minutes = sum(occupancy) if complete else None
        summary["turnover_diagnostics"][label] = {
            "net_profitable_episode_count": profitable,
            "net_profitable_episodes_per_source_trading_day": profitable
            / len(source_trading_dates),
            "median_terminal_duration_ms": median(durations) if complete else None,
            "capital_krw_minutes": capital_minutes,
            "net_profit_per_capital_minute_pct": (
                sum(u[label] for u in units) / capital_minutes * 100
                if capital_minutes is not None and capital_minutes > 0
                else None
            ),
            "timing_complete": complete,
        }
    for label, subset in (("primary", units), ("holdout", holdout)):
        summary[label + "_paired_net_ev_uplift_pct_points"] = (
            mean(u["uplift"] for u in subset) if subset else None
        )
        summary[label + "_paired_net_pnl_uplift_krw"] = (
            sum(u["candidate"] - u["base"] for u in subset) if subset else None
        )
        summary[label + "_candidate_net_ev_pct"] = (
            mean(u["candidate"] / u["notional"] * 100 for u in subset)
            if subset
            else None
        )
    if units:
        summary["p10_deterioration_pct_points"] = _quantile(
            [u["base"] / u["notional"] * 100 for u in units], 0.1
        ) - _quantile([u["candidate"] / u["notional"] * 100 for u in units], 0.1)
        daily = defaultdict(list)
        for u in units:
            daily[u["day"]].append(u["uplift"])
        daily_means = {day: mean(values) for day, values in sorted(daily.items())}
        summary["uncertainty"]["daily_mean_uplift_pct_points"] = daily_means
        summary["uncertainty"]["minimum_daily_uplift_pct_points"] = min(
            daily_means.values()
        )
    summary["canonical_sha256"] = canonical_sha256(summary)
    return summary


def build_candidate(
    *,
    base_evidence: dict,
    stress_evidence: dict,
    contract: EvaluationContract,
    policy_payload: dict,
) -> dict:
    """Native ID is emitted only here, bound to exact policy and both models."""
    base = assess_research_evidence(base_evidence, contract)
    stress = assess_research_evidence(stress_evidence, contract)
    errors = base["errors"] + ["stress:" + e for e in stress["errors"]]
    if base_evidence.get("model_id") == stress_evidence.get("model_id"):
        errors.append("independent_stress_model_required")
    if policy_payload.get("policy_hash") != contract.policy_hash:
        errors.append("policy_hash_mismatch")
    candidate = {
        "schema": "machine_adaptive_exit_candidate_v1",
        "family": "machine_adaptive_exit_v1",
        "authority": dict(AUTHORITY),
        "scope_key": contract.scope_key,
        "source_date": contract.holdout_end,
        "policy": policy_payload,
        "evaluation_contract_hash": contract.contract_hash,
        "evidence_hash": base_evidence["canonical_sha256"],
        "stress_evidence_hash": stress_evidence["canonical_sha256"],
        "decision": "research_ready" if not errors else "hold_evidence",
        "errors": sorted(set(errors)),
        "eligible_for_next_preopen": False,
    }
    candidate["recommendation_id"] = "adaptive-exit:" + canonical_sha256(candidate)[:32]
    candidate["canonical_sha256"] = canonical_sha256(candidate)
    return candidate
