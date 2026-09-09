"""Source-only separation of widget confirmation and policy component effects.

Owned by the existing widget evaluation producers; no CLI or runtime selector.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from typing import Any


def confirmation_comparison(rows: list[dict], *, target_date: date) -> dict:
    from src.engine.monitoring.samsung_widget_advisory import AdvisoryPromotionFilter

    inputs: dict[tuple[str, str], dict] = {}
    conflicts: set[tuple[str, str]] = set()
    missing = 0
    for row in rows:
        advisory = row.get("advisory")
        trace = (
            advisory.get("confirmation_input_trace")
            if isinstance(advisory, dict)
            else None
        )
        if (
            not isinstance(trace, dict)
            or trace.get("schema") != "widget_confirmation_input_trace_v1"
            or not isinstance(trace.get("rows"), list)
        ):
            missing += 1
            continue
        for item in trace.get("rows", []):
            if not isinstance(item, dict):
                missing += 1
                continue
            try:
                stamp = datetime.fromisoformat(str(item.get("observed_at")))
            except ValueError:
                missing += 1
                continue
            if (
                stamp.tzinfo is None
                or stamp.date() != target_date
                or not item.get("session")
            ):
                missing += 1
                continue
            key = (str(item["session"]), stamp.isoformat())
            if key in inputs and inputs[key] != item:
                conflicts.add(key)
            inputs[key] = item
    filters: dict[tuple[str, int], Any] = {}
    episodes: list[dict] = []
    active: dict[str, tuple[str, datetime, dict]] = {}
    for key, item in sorted(inputs.items()):
        session, timestamp = key
        stamp = datetime.fromisoformat(timestamp)
        if key in conflicts:
            active.pop(session, None)
            for count in (2, 3):
                filters.pop((session, count), None)
            continue
        raw = str(item.get("raw_state") or item.get("state"))
        prior = active.get(session)
        if (
            not prior
            or raw != prior[0]
            or not 0
            < (stamp - prior[1]).total_seconds()
            <= AdvisoryPromotionFilter.MAX_CONFIRMATION_GAP_SEC
        ):
            episode = {
                "session": session,
                "raw_first_at": timestamp,
                "raw_state": raw,
                "confirmation_2_at": None,
                "confirmation_3_at": None,
                "executable_net_ev_delta_pct": None,
                "economic_status": "requires_exact_quote_fill_and_fixed_exit_replay",
            }
            if raw in AdvisoryPromotionFilter.ACTIONABLE:
                episodes.append(episode)
        else:
            episode = prior[2]
        active[session] = (raw, stamp, episode)
        for count in (2, 3):
            replay = filters.setdefault((session, count), AdvisoryPromotionFilter())
            result = replay.apply(item, required_confirmations=count)
            if raw in AdvisoryPromotionFilter.ACTIONABLE and result["state"] == raw:
                episode[f"confirmation_{count}_at"] = (
                    episode[f"confirmation_{count}_at"] or timestamp
                )
    for episode in episodes:
        two, three = episode["confirmation_2_at"], episode["confirmation_3_at"]
        episode["additional_confirmation_delay_sec"] = (
            (
                datetime.fromisoformat(three) - datetime.fromisoformat(two)
            ).total_seconds()
            if two and three
            else None
        )
        episode["third_confirmation_not_observed"] = bool(two and not three)
    return {
        "schema": "widget_confirmation_comparison_v1",
        "target_date": target_date.isoformat(),
        "status": "observed" if inputs and not conflicts else "source_gap",
        "exact_input_count": len(inputs) - len(conflicts),
        "conflicting_input_count": len(conflicts),
        "legacy_or_invalid_trace_row_count": missing,
        "episodes": episodes,
        "raw_actionable_episode_count": len(episodes),
        "third_confirmation_not_observed_count": sum(
            e["third_confirmation_not_observed"] for e in episodes
        ),
        "metric_role": "paired_raw_confirmation_timing_not_executable_ev",
        "policy_selection_effect": False,
        "allowed_runtime_apply": False,
        "runtime_effect": False,
        "order_authority": False,
    }


def component_arms(
    baseline: dict | None,
    candidate: dict,
    *,
    signal_keys: tuple[str, ...],
    exit_keys: tuple[str, ...],
) -> dict[str, dict]:
    """Use the same applied baseline, never a fresh winner as its own control."""
    if not baseline:
        return {}

    def copy(value):
        return json.loads(json.dumps(value, allow_nan=False))

    arms = {"applied_baseline": copy(baseline), "combined_candidate": copy(candidate)}
    for name, keys in (("signal_only", signal_keys), ("exit_only", exit_keys)):
        arm = copy(baseline)
        arm.update({key: candidate[key] for key in keys if key in candidate})
        arms[name] = arm
    return arms


def objective_comparison(
    arms: dict[str, dict], *, baseline_policy_id: str | None
) -> dict:
    return {
        "schema": "widget_existing_component_comparison_v1",
        "status": "observed_source_only" if arms else "applied_baseline_missing",
        "baseline_policy_id": baseline_policy_id,
        "baseline_provenance_role": "exact_date_verified_policy_not_pid_consumption_receipt",
        "baseline_pid_consumption_verified": False,
        "arms": arms,
        "confirmation_owner": "widget_advisory_calibration.confirmation_comparison",
        "metric_role": "fixed_baseline_component_attribution_not_broker_fill_quality",
        "signal_opportunity_sets_may_differ": True,
        "fixed_input_window": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "economic_acceptance": "not_proven_by_resolved_winners_when_censored_exposure_exists",
        "profit_frequency_guard": "positive_net_close_within_180s_without_profit_upper_cap",
    }


def select_policy_component(comparison: dict) -> dict:
    """Existing signal/exit arms only; freeze a calibration winner before holdout."""
    arms = comparison.get("arms") or {}
    baseline = arms.get("applied_baseline")
    fallback = {"selected_arm": None, "reason": "component_baseline_missing"}
    if not isinstance(baseline, dict):
        return fallback
    base_parameters = baseline.get("parameters") or {}
    for arm_name in ("signal_only", "exit_only"):
        parameters = (arms.get(arm_name) or {}).get("parameters") or {}
        changed_keys = {
            key
            for key in set(base_parameters) | set(parameters)
            if base_parameters.get(key) != parameters.get(key)
        }
        forbidden = {"target_bps", "force_flat_time", "max_completed_entries_per_day"}
        if (
            arm_name == "signal_only"
            and changed_keys & forbidden
            or arm_name == "exit_only"
            and changed_keys - {"target_bps", "force_flat_time"}
        ):
            return {"selected_arm": None, "reason": "component_axis_contract_invalid"}

    def metric(summary, key):
        value = summary.get(key)
        return value if type(value) in (int, float) and math.isfinite(value) else None

    def ready(arm, holdout=False):
        for name, minimum in (
            (("holdout", 4),)
            if holdout
            else (
                ("calibration", 10),
                ("calibration_first_half", 4),
                ("calibration_second_half", 4),
            )
        ):
            summary = arm.get(name) or {}
            ev = metric(summary, "notional_weighted_ev_pct")
            if (
                int(summary.get("episode_count") or 0) < minimum
                or ev is None
                or ev <= 0
                or metric(summary, "worst_episode_return_pct") is None
                or summary["worst_episode_return_pct"] <= -3
            ):
                return False
            for cap in range(
                4,
                int(arm.get("parameters", {}).get("max_completed_entries_per_day") or 1)
                + 1,
            ):
                incremental = (summary.get("entry_cap_comparison") or {}).get(
                    str(cap), {}
                ).get("incremental") or {}
                incremental_ev = metric(incremental, "notional_weighted_ev_pct")
                if (
                    int(incremental.get("episode_count") or 0) < 1
                    or incremental_ev is None
                    or incremental_ev <= 0
                ):
                    return False
        return True

    def improves(candidate, window):
        base, new = baseline.get(window) or {}, candidate.get(window) or {}
        comparisons = (
            ("notional_weighted_ev_pct", True, True),
            ("modeled_net_pnl_per_qualified_day", True, False),
            ("worst_episode_return_pct", True, False),
            ("observed_occupancy_seconds_sum", False, False),
            ("profitable_completed_within_180s_count", True, False),
        )
        for key, higher, strict in comparisons:
            left, right = metric(new, key), metric(base, key)
            if left is None or right is None:
                return False
            if (left <= right if strict else left < right) if higher else left > right:
                return False
        return True

    candidates = [
        name
        for name in ("signal_only", "exit_only")
        if name in arms and ready(arms[name]) and improves(arms[name], "calibration")
    ]
    if candidates:
        winner = max(
            candidates,
            key=lambda name: (
                arms[name]["calibration"]["modeled_net_pnl_per_qualified_day"],
                name,
            ),
        )
        if ready(arms[winner], holdout=True) and improves(arms[winner], "holdout"):
            return {
                "selected_arm": winner,
                "reason": "single_component_incremental_cost_ev",
            }
    if ready(baseline) and ready(baseline, holdout=True):
        return {
            "selected_arm": "applied_baseline",
            "reason": "carry_verified_component_baseline",
        }
    return {"selected_arm": None, "reason": "component_economics_or_holdout_not_ready"}
