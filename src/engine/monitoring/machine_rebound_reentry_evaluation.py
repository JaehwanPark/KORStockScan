"""Paired source-only rebound economics; no broker calls or policy writes.

The caller supplies normalized owner decisions with postclose quote outcomes.
Missing control resumption is not a zero-return control.  Neither target touch
nor a depth-backed immediate entry is described as an actual broker fill.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime
from statistics import mean
from typing import Any

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.trading.config.machine_rebound_reentry_policy import (
    AUTO_ARM,
    MAX_P10_DETERIORATION_PCT,
    MIN_COVERAGE_PCT,
    MIN_DAYS,
    MIN_PAIRS,
    MIN_UPLIFT_PCT,
    REPLAY_VERSION,
    SOURCE_AUTHORITY,
    digest,
    next_session,
    numeric,
    scope_identity,
)
from src.trading.market.machine_rebound_reentry import (
    immediate_plan_feasible,
    rising_confirmation,
)
from src.utils.market_day import is_krx_trading_day
from datetime import timedelta

SOURCE_SCHEMA = "market_weakness_rebound_reentry_source_v1"
SECTION = "market_weakness_rebound_reentry_evaluation"
CONTROL = "current_guard_control"
RECOVERY = "recovery_then_fresh_owner_signal"
AUTHORITY = SOURCE_AUTHORITY
METRIC_CONTRACT = {
    "metric_role": "paired_market_weakness_rebound_reentry_evaluation",
    "decision_authority": AUTHORITY["decision_authority"],
    "window_policy": "clean_baseline_exact_scope_cumulative_rolling_5_10_20_latest_date_holdout",
    "sample_floor": {
        "days": MIN_DAYS,
        "pairs": MIN_PAIRS,
        "coverage_pct": MIN_COVERAGE_PCT,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "causal_owner_receipt_exact_route_depth_cost_full_position_exit_control_parity",
    "forbidden_uses": [
        "missing_as_zero",
        "target_touch_as_actual_fill",
        "partial_full_pooling",
        "expired_signal_revival",
        "quantity_target_cancel_safety_mutation",
    ],
}


def aware(value: Any) -> datetime | None:
    try:
        result = datetime.fromisoformat(str(value))
        return result if result.tzinfo is not None else None
    except ValueError:
        return None


def _outcome(frame: dict[str, Any], basis: float) -> tuple[float | None, str]:
    outcome = frame.get("modeled_owner_exit") or {}
    if frame.get("source_quality_eligible") is not True:
        return None, "source_contract_gap"
    if outcome.get("status") != "completed_full_position":
        return None, str(outcome.get("status") or "owner_exit_replay_gap")
    net = numeric(outcome.get("net_profit_krw"))
    if net is None or outcome.get("actual_order_submitted") is not False:
        return None, "owner_exit_replay_gap"
    return net / basis * 100.0, "eligible"


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = {
        "opportunity_id": case.get("opportunity_id"),
        "trade_date": case.get("trade_date"),
        **scope_identity(case),
        **AUTHORITY,
    }
    frames = case.get("frames") or []
    basis = numeric(case.get("basis_notional_krw"))
    if (
        not basis
        or basis <= 0
        or not frames
        or any(not isinstance(row, dict) for row in frames)
    ):
        return {**result, "status": "source_contract_gap"}
    if any(aware(row.get("observed_at")) is None for row in frames):
        return {**result, "status": "source_contract_gap"}
    frames = sorted(frames, key=lambda row: aware(row["observed_at"]))
    initial_plan = frames[0].get("legs") or []
    if (
        not case.get("opportunity_id")
        or not initial_plan
        or basis
        != sum(
            (numeric(leg.get("entry_price")) or 0) * (numeric(leg.get("quantity")) or 0)
            for leg in initial_plan
        )
    ):
        return {
            **result,
            "status": "source_contract_gap",
            "reason": "initial_fixed_basis_mismatch",
        }
    if len({row["observed_at"] for row in frames}) != len(frames):
        return {
            **result,
            "status": "source_contract_gap",
            "reason": "ambiguous_same_timestamp",
        }
    eligible = []
    for row in frames:
        observed = aware(row["observed_at"])
        valid_until = aware(row.get("signal_valid_until"))
        if (
            scope_identity(row) != scope_identity(case)
            or row.get("owner_signal_valid") is not True
            or valid_until is None
            or observed > valid_until
        ):
            continue
        eligible.append(row)
    control = next(
        (row for row in eligible if row.get("baseline_blocked") is False), None
    )
    # Never assume skip-forever or fabricate a later owner signal from prices.
    terminal = case.get("baseline_no_entry_receipt") or {}
    terminal_at, scan_end = aware(terminal.get("observed_at")), aware(
        terminal.get("scan_end")
    )
    no_entry_control = bool(
        control is None
        and terminal.get("schema") == "machine_rebound_owner_terminal_v1"
        and terminal.get("no_entry_confirmed") is True
        and terminal.get("trace_complete") is True
        and terminal.get("opportunity_id") == case.get("opportunity_id")
        and scope_identity(terminal) == scope_identity(case)
        and terminal.get("trade_date") == case.get("trade_date")
        and terminal_at is not None
        and scan_end is not None
        and terminal_at >= scan_end
        and terminal_at >= aware(frames[-1]["observed_at"])
        and terminal.get("basis_notional_krw") == basis
        and terminal.get("owner_state") in {"NO_TRADE", "COMPLETE"}
    )
    if control is None and not no_entry_control:
        return {
            **result,
            "status": "baseline_replay_gap",
            "reason": "control_resumption_or_terminal_no_entry_receipt_missing",
        }
    if (
        control is not None
        and control.get("baseline_confirmation_mode") != "immediate_owner_guards"
    ):
        return {**result, "status": "baseline_replay_mismatch"}
    early = next(
        (
            row
            for row in eligible
            if row.get("baseline_blocked") is True
            and row.get("market_fresh") is True
            and row.get("market_phase") in {"active", "release_pending"}
            and rising_confirmation(row)
            and immediate_plan_feasible(row)
        ),
        None,
    )
    selected = (
        early
        if early is not None
        and (
            control is None
            or aware(early["observed_at"]) < aware(control["observed_at"])
        )
        else control
    )
    if (
        selected is not None
        and selected.get("baseline_confirmation_mode") != "immediate_owner_guards"
    ):
        return {**result, "status": "baseline_replay_mismatch"}
    if selected is None and not any(
        row.get("source_quality_eligible") is True for row in frames
    ):
        return {**result, "status": "source_contract_gap"}
    control_ev, control_status = (
        (0.0, "observed_terminal_no_entry")
        if no_entry_control
        else _outcome(control, basis)
    )
    candidate_ev, candidate_status = (
        _outcome(selected, basis)
        if selected is not None
        else (0.0, "observed_terminal_no_entry")
    )
    if control_ev is None or candidate_ev is None:
        return {
            **result,
            "status": control_status if control_ev is None else candidate_status,
        }
    recovery_identical = (
        control is not None
        and rising_confirmation(control)
        and control.get("market_fresh") is True
        and control.get("market_phase") not in {"active", "release_pending"}
    )
    return {
        **result,
        "status": "eligible",
        "evidence_class": "modeled_owner_exit",
        "basis_notional_krw": basis,
        "control_ev_pct": control_ev,
        "candidate_ev_pct": candidate_ev,
        "delta_ev_pct": candidate_ev - control_ev,
        "control_at": control["observed_at"] if control else terminal["observed_at"],
        "candidate_at": selected["observed_at"] if selected else None,
        "candidate_source_signal_id": (
            selected.get("source_signal_id") if selected else None
        ),
        "equivalent_to_control": selected is control,
        "recovery_arm_status": (
            "equivalent_to_control"
            if recovery_identical
            else "fresh_followup_owner_signal_not_observed"
        ),
        "runtime_reachability_status": (selected or {}).get(
            "runtime_reachability_status", "unknown_not_evaluated"
        ),
        "owner_contract_sha256": (selected or frames[0]).get("owner_contract_sha256"),
        "control_basis": (
            "observed_terminal_no_entry"
            if no_entry_control
            else "observed_owner_resumption"
        ),
        "case_sha256": digest(case),
    }


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "pairs": 0,
            "source_quality_adjusted_ev_pct": None,
            "candidate_ev_pct": None,
        }

    def p10(key: str) -> float:
        values = sorted(row[key] for row in rows)
        position = (len(values) - 1) * 0.1
        lower = int(position)
        return values[lower] + (
            values[min(lower + 1, len(values) - 1)] - values[lower]
        ) * (position - lower)

    return {
        "pairs": len(rows),
        "source_quality_adjusted_ev_pct": mean(row["delta_ev_pct"] for row in rows),
        "candidate_ev_pct": mean(row["candidate_ev_pct"] for row in rows),
        "p10_deterioration_pct": p10("control_ev_pct") - p10("candidate_ev_pct"),
    }


def build_evaluation(
    *, target_date: date, sources: list[dict[str, Any]], same_stage_clear: bool
) -> dict[str, Any]:
    runtime_cost = comparison_cost_contract(next_session(target_date))
    cases: list[dict[str, Any]] = []
    gaps: Counter[str] = Counter()
    for source in sources:
        section = source.get(SOURCE_SCHEMA)
        if not isinstance(section, dict):
            gaps["source_section_missing"] += 1
            continue
        if section.get("schema") != SOURCE_SCHEMA or any(
            section.get(key) != value for key, value in AUTHORITY.items()
        ):
            gaps["source_authority_or_schema_invalid"] += 1
            continue
        cases.extend(section.get("cases") or [])
        gaps.update(section.get("gap_counts") or {})
    counts = Counter(str(row.get("opportunity_id")) for row in cases)
    rows = []
    for case in cases:
        try:
            day = date.fromisoformat(case["trade_date"])
            if not date(2026, 6, 5) <= day <= target_date:
                gaps["outside_clean_target_window"] += 1
                continue
            if counts[str(case.get("opportunity_id"))] != 1:
                gaps["duplicate_parent_opportunity"] += 1
                continue
            rows.append(evaluate_case(case))
        except (KeyError, TypeError, ValueError):
            gaps["case_contract_invalid"] += 1
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[digest(scope_identity(row))].append(row)
    cohorts = []
    for cohort_rows in grouped.values():
        valid = [row for row in cohort_rows if row["status"] == "eligible"]
        days = sorted({row["trade_date"] for row in valid})
        coverage = len(valid) / len(cohort_rows) * 100.0
        stats = _stats(valid)
        rolling = {
            str(window): (
                _stats([row for row in valid if row["trade_date"] in days[-window:]])
                if len(days) >= window
                else {"status": "unavailable"}
            )
            for window in (5, 10, 20)
        }
        holdout = _stats(
            [row for row in valid if days and row["trade_date"] == days[-1]]
        )
        blockers = []
        if len(days) < MIN_DAYS or len(valid) < MIN_PAIRS:
            blockers.append("hold_sample")
        if coverage < MIN_COVERAGE_PCT:
            blockers.append("paired_coverage_below_floor")
        latest = date.fromisoformat(days[-1]) if days else None
        lag = (
            sum(
                is_krx_trading_day(target_date - timedelta(days=offset))
                for offset in range((target_date - latest).days)
            )
            if latest
            else 999
        )
        maximum_lag = 4 if cohort_rows[0].get("symbol") == "005930" else 1
        if lag > maximum_lag:
            blockers.append("latest_natural_pair_stale")
        if not same_stage_clear:
            blockers.append("same_stage_owner_conflict")
        for name, metrics in (
            ("cumulative", stats),
            ("rolling5", rolling["5"]),
            ("holdout", holdout),
        ):
            uplift = numeric(metrics.get("source_quality_adjusted_ev_pct")) or 0
            if (uplift < MIN_UPLIFT_PCT if name == "cumulative" else uplift <= 0) or (
                numeric(metrics.get("candidate_ev_pct")) or 0
            ) <= 0:
                blockers.append(f"{name}_net_edge_not_positive")
            if (
                numeric(metrics.get("p10_deterioration_pct")) or 0
            ) > MAX_P10_DETERIORATION_PCT:
                blockers.append(f"{name}_p10_deterioration")
        contracts = {row.get("owner_contract_sha256") for row in valid}
        if len(contracts) != 1 or not all(contracts):
            blockers.append("owner_contract_changed_or_missing")
        scope = scope_identity(cohort_rows[0])
        if scope["owner"] != "episode" or scope["entry_state"] != "FLAT_NEW_ENTRY":
            blockers.append("owner_exit_runtime_adapter_not_supported")
        cohorts.append(
            {
                **scope,
                "arm": AUTO_ARM,
                "replay_version": REPLAY_VERSION,
                "status": (
                    "candidate_ready"
                    if not blockers
                    else (
                        "equivalent_to_control"
                        if valid and all(row["equivalent_to_control"] for row in valid)
                        else "blocked"
                    )
                ),
                "blockers": blockers,
                "unique_days": len(days),
                "coverage_pct": coverage,
                "primary_ev": stats,
                "rolling": rolling,
                "holdout": holdout,
                "owner_contract_sha256": (
                    next(iter(contracts)) if len(contracts) == 1 else None
                ),
                "source_through_date": target_date.isoformat(),
                "executable_confirmation": {
                    "mode": "fresh_rebound_checkpoint0",
                    "round_trip_cost_pct": runtime_cost["round_trip_cost_pct"],
                    "cost_trade_date": runtime_cost["trade_date"],
                    "cost_contract_sha256": runtime_cost["contract_sha256"],
                },
            }
        )
    ready = [row for row in cohorts if row["status"] == "candidate_ready"]
    if any(
        gaps[key]
        for key in (
            "journal_contract_invalid",
            "source_authority_or_schema_invalid",
            "case_contract_invalid",
            "duplicate_parent_opportunity",
        )
    ):
        ready = []
    ready.sort(
        key=lambda row: (
            -row["primary_ev"]["source_quality_adjusted_ev_pct"],
            digest(scope_identity(row)),
        )
    )
    for row in rows:
        if row["status"] != "eligible":
            gaps[row["status"]] += 1
    return {
        "schema": REPLAY_VERSION,
        "target_date": target_date.isoformat(),
        "status": (
            "candidate_ready"
            if ready
            else (
                "source_contract_gap"
                if gaps
                else ("evidence_accumulating" if rows else "no_natural_opportunity")
            )
        ),
        "metric_contract": METRIC_CONTRACT,
        "case_count": len(rows),
        "eligible_pair_count": sum(row["status"] == "eligible" for row in rows),
        "gap_counts": dict(gaps),
        "gap_handoff": {
            key: {
                "count": value,
                "owner": "MarketWeaknessReboundReentryRetention0911",
                "next_action": (
                    "do_not_retry_pre_instrumentation_raw_use_new_owner_journals"
                    if key
                    in {
                        "source_section_missing",
                        "pre_instrumentation_owner_journal_unavailable",
                    }
                    else "repair_or_narrow_exact_owner_replay_do_not_wait_for_sample_maturity"
                ),
            }
            for key, value in gaps.items()
            if value
        },
        "evaluation_scope": {
            "automatic_runtime_adapter": "regular_two_leg_episode_flat_new_entry",
            "entry_model": "immediately_marketable_full_plan_existing_cancel_unchanged",
            "outcome_model": "owner_target_touch_before_common_regular_session_end_not_actual_fill",
            "recovery_arm": "baseline_resumption_attribution_no_independent_buy_strategy",
            "unsupported": [
                "widget_sequential_average_target",
                "passive_or_partial_fill",
                "no_entry_without_terminal_receipt",
                "cross_session_no_stop_exit",
            ],
        },
        "cases": rows,
        "cohorts": cohorts,
        "selected_candidate": ready[0] if ready else None,
        "automatic_preopen": {
            "standing_user_authority": True,
            "per_candidate_user_approval_required": False,
            "scope_cap": 1,
            "application_requires_exact_date_receipt": True,
        },
        **AUTHORITY,
    }
