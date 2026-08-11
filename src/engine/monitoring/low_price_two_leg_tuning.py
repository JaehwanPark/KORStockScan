"""Postclose actual-outcome tuning for each lower-price two-leg profile.

This producer reads only durable profile states and its own prior reports.  It
never queries market history and can only propose one bounded tightening axis
for the next PREOPEN across the shared regular-entry stage.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.trading.low_price_two_leg.machine import DEFAULT_STATE_DIR
from src.trading.low_price_two_leg.policy_runtime import (
    BASELINE_POLICIES,
    POLICY_BOUNDS,
    CANDIDATE_DIR,
    CANDIDATE_SCHEMA,
    atomic_write_json,
    policy_hash,
    policy_mutations_between,
    validate_candidate,
)
from src.trading.low_price_two_leg.profiles import PROFILES
from src.trading.order.regular_two_leg_machine import KST
from src.trading.order.samsung_entry_policy import (
    CANDIDATE_DIR as SAMSUNG_CANDIDATE_DIR,
)
from src.trading.order.samsung_entry_policy import (
    validate_candidate as validate_samsung_candidate,
)
from src.utils.constants import DATA_DIR

REPORT_TYPE = "low_price_two_leg_tuning"
REPORT_SCHEMA = "low_price_two_leg_tuning_report_v1"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
SAMPLE_FLOOR_COMPLETED_LEGS = 20
RECENT_FLOOR_COMPLETED_LEGS = 3
SOURCE_QUALITY_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
OUTPUT_DIR = DATA_DIR / "report" / REPORT_TYPE
TERMINAL_LEG_STATUSES = {"COMPLETE", "NO_FILL"}
KNOWN_LEG_STATUSES = {
    "PLANNED",
    "BUY_SUBMITTING",
    "BUY_OPEN",
    "BUY_CANCEL_SUBMITTING",
    "BUY_CANCEL_PENDING",
    "POSITION_OPEN",
    "TARGET_SUBMITTING",
    "TARGET_OPEN",
    "NO_FILL",
    "COMPLETE",
    "HELD",
}
METRIC_CONTRACT = {
    "metric_role": "low_price_two_leg_profile_entry_tuning_observation",
    "decision_authority": "postclose_bounded_candidate_only",
    "window_policy": "profile_separated_daily_rolling10_rolling20_and_clean_cumulative",
    "sample_floor": {
        "cumulative_completed_legs": SAMPLE_FLOOR_COMPLETED_LEGS,
        "rolling10_completed_legs": RECENT_FLOOR_COMPLETED_LEGS,
        "rolling20_completed_legs": RECENT_FLOOR_COMPLETED_LEGS,
    },
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "target_date_profile_state_match",
        "actual_broker_receipt_terminal_leg_contract",
        "profile_specific_no_cross_symbol_pooling",
        "existing_samsung_regular_entry_same_stage_owner_guard",
        "held_or_unresolved_inventory_blocks_tightening",
        "observation_source_quality_audit_tuning_input_allowed",
    ],
    "forbidden_uses": [
        "historical_market_data_requery",
        "price_touch_as_fill",
        "cross_profile_outcome_pooling",
        "same_day_or_intraday_runtime_mutation",
        "more_than_one_profile_or_axis_mutation_per_day",
        "threshold_relaxation",
        "quantity_target_entry_validity_stop_or_forced_exit_change",
        "provider_bot_cap_or_broker_guard_change",
    ],
}


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _source_quality_preflight(target_date: str, source_quality_dir: Path) -> dict:
    path = source_quality_dir / f"observation_source_quality_audit_{target_date}.json"
    payload = _read_json(path)
    if payload is None:
        return {
            "status": "blocked",
            "tuning_input_allowed": False,
            "reason": "observation_source_quality_audit_missing_or_invalid",
            "source_path": str(path),
        }
    status = str(payload.get("status") or "").lower()
    allowed = (payload.get("summary") or {}).get("tuning_input_allowed") is True
    passed = allowed and status in {"pass", "warning"}
    return {
        "status": "pass" if passed else "blocked",
        "tuning_input_allowed": passed,
        "reason": "ready" if passed else "observation_source_quality_audit_blocked",
        "source_path": str(path),
        "audit_status": status,
    }


def _empty_row(profile_id: str, target_date: str, reason: str) -> dict:
    return {
        "profile_id": profile_id,
        "symbol": PROFILES[profile_id].symbol,
        "session": PROFILES[profile_id].session,
        "target_date": target_date,
        "source_quality": "gap",
        "source_quality_reasons": [reason],
        "eligible_for_tuning": False,
        "attempted": False,
        "no_signal": False,
        "state_status": "UNKNOWN",
        "signal_features": {},
        "legs": [],
    }


def _sanitize_leg(raw: dict[str, Any], cost_pct: float) -> dict[str, Any]:
    status = str(raw.get("status") or "UNKNOWN")
    quantity = _as_int(raw.get("quantity"))
    entry_price = _as_int(raw.get("entry_price"))
    fill_price = _as_int(raw.get("fill_price"))
    target_price = _as_int(raw.get("target_price"))
    position_qty = _as_int(raw.get("position_qty"))
    target_filled_qty = _as_int(raw.get("target_filled_qty"))
    completed = (
        status == "COMPLETE"
        and target_filled_qty == 1
        and position_qty == 0
        and fill_price > 0
        and target_price > fill_price
    )
    position_statuses = {"POSITION_OPEN", "TARGET_SUBMITTING", "TARGET_OPEN", "HELD"}
    held = status == "HELD" or position_qty == 1
    contract_valid = bool(
        quantity == 1
        and entry_price > 0
        and position_qty in {0, 1}
        and target_filled_qty in {0, 1}
        and ((status in position_statuses) == (position_qty == 1))
        and (status == "COMPLETE" or target_filled_qty == 0)
        and (status != "COMPLETE" or completed)
        and (
            status != "NO_FILL"
            or (fill_price == 0 and position_qty == 0 and target_filled_qty == 0)
        )
    )
    net_profit_pct = (
        (target_price / fill_price - 1.0) * 100.0 - cost_pct if completed else None
    )
    return {
        "leg_id": str(raw.get("leg_id") or ""),
        "quantity": quantity,
        "status": status,
        "entry_price": entry_price,
        "fill_price": fill_price,
        "target_price": target_price,
        "position_qty": position_qty,
        "target_filled_qty": target_filled_qty,
        "completed": completed,
        "held": held,
        "terminal": status in TERMINAL_LEG_STATUSES,
        "contract_valid": contract_valid,
        "net_profit_pct": (
            round(net_profit_pct, 6) if net_profit_pct is not None else None
        ),
    }


def extract_profile_row(
    *, profile_id: str, state_path: Path, target_date: str, cost_pct: float
) -> dict:
    profile = PROFILES[profile_id]
    state = _read_json(state_path)
    if state is None:
        return _empty_row(profile_id, target_date, "state_missing_or_invalid")
    reasons: list[str] = []
    if state.get("schema") != f"low_price_two_leg_{profile_id}_state_v1":
        reasons.append("state_schema_mismatch")
    if state.get("trade_date") != target_date:
        reasons.append("state_target_date_mismatch")
    attempted = bool(state.get("attempt_consumed"))
    state_status = str(state.get("status") or "UNKNOWN")
    features = state.get("signal_features")
    if not isinstance(features, dict):
        features = {}
        reasons.append("signal_features_invalid")
    if attempted:
        if (
            features.get("schema") != "regular_two_leg_entry_signal_features_v1"
            or features.get("strategy") != profile_id
            or features.get("symbol") != profile.symbol
        ):
            reasons.append("signal_feature_profile_contract_mismatch")
    elif state_status != "NO_TRADE":
        reasons.append("nonterminal_no_attempt_state")
    raw_legs = state.get("legs")
    if not isinstance(raw_legs, list):
        raw_legs = []
        reasons.append("legs_invalid")
    legs = [_sanitize_leg(leg, cost_pct) for leg in raw_legs if isinstance(leg, dict)]
    if attempted:
        if len(legs) != 2 or {leg["leg_id"] for leg in legs} != {
            "signal_close",
            "signal_close_minus_1tick",
        }:
            reasons.append("two_leg_identity_contract_invalid")
        if any(
            leg["quantity"] != 1 or leg["status"] not in KNOWN_LEG_STATUSES
            for leg in legs
        ):
            reasons.append("leg_quantity_or_status_invalid")
        if any(not leg["contract_valid"] for leg in legs):
            reasons.append("leg_execution_contract_invalid")
        if any(not leg["terminal"] for leg in legs):
            reasons.append("held_or_unresolved_inventory")
        if any(leg["status"] == "COMPLETE" and not leg["completed"] for leg in legs):
            reasons.append("complete_leg_receipt_contract_invalid")
        if all(leg["terminal"] for leg in legs):
            expected_terminal_status = (
                "NO_TRADE"
                if all(leg["status"] == "NO_FILL" for leg in legs)
                else "COMPLETE"
            )
            if state_status != expected_terminal_status:
                reasons.append("aggregate_terminal_status_mismatch")
        elif state_status in {"COMPLETE", "NO_TRADE"}:
            reasons.append("aggregate_nonterminal_status_mismatch")
    return {
        "profile_id": profile_id,
        "symbol": profile.symbol,
        "session": profile.session,
        "target_date": target_date,
        "source_quality": "pass" if not reasons else "gap",
        "source_quality_reasons": reasons,
        "eligible_for_tuning": not reasons,
        "attempted": attempted,
        "no_signal": not attempted and state_status == "NO_TRADE",
        "state_status": state_status,
        "signal_features": features,
        "legs": legs,
    }


def _aggregate(rows: list[dict]) -> dict:
    all_attempted_rows = [row for row in rows if row.get("attempted")]
    attempted_rows = [
        row for row in rows if row.get("eligible_for_tuning") and row.get("attempted")
    ]
    legs = [leg for row in attempted_rows for leg in row.get("legs", [])]
    all_legs = [leg for row in all_attempted_rows for leg in row.get("legs", [])]
    completed = [leg for leg in legs if leg.get("completed")]
    attempted_notional = sum(_as_int(leg.get("entry_price")) for leg in legs)
    realized_profit = sum(
        _as_int(leg.get("fill_price")) * float(leg["net_profit_pct"]) / 100.0
        for leg in completed
    )
    ev = realized_profit / attempted_notional * 100.0 if attempted_notional else None
    return {
        "eligible_days": sum(row.get("eligible_for_tuning") for row in rows),
        "source_gap_days": sum(row.get("source_quality") != "pass" for row in rows),
        "attempted_episodes": len(attempted_rows),
        "completed_legs": len(completed),
        "no_fill_legs": sum(leg.get("status") == "NO_FILL" for leg in legs),
        "held_or_unresolved_legs": sum(
            leg.get("held") or not leg.get("terminal") for leg in all_legs
        ),
        "notional_weighted_ev_pct": round(ev, 6) if ev is not None else None,
    }


def _axis_outcome(
    rows: list[dict], *, min_drawdown: float, max_near_low: float
) -> dict:
    selected: list[dict] = []
    for row in rows:
        if not row.get("attempted"):
            continue
        features = row.get("signal_features") or {}
        drawdown = _as_float(features.get("observed_drawdown_pct"))
        near_low = _as_float(features.get("observed_near_low_pct"))
        if (
            drawdown is not None
            and near_low is not None
            and drawdown + 1e-12 >= min_drawdown
            and near_low - 1e-12 <= max_near_low
        ):
            selected.append(row)
    return _aggregate(selected)


def _load_history(output_dir: Path, target_date: date) -> dict[str, dict[str, dict]]:
    history: dict[str, dict[str, dict]] = {}
    for path in sorted(output_dir.glob(f"{REPORT_TYPE}_*.json")):
        raw_date = path.stem.removeprefix(f"{REPORT_TYPE}_")
        try:
            report_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if not CLEAN_BASELINE_DATE <= report_date < target_date:
            continue
        payload = _read_json(path)
        profiles = (payload or {}).get("daily", {}).get("profiles", {})
        if (
            not payload
            or payload.get("schema") != REPORT_SCHEMA
            or payload.get("target_date") != raw_date
            or not isinstance(profiles, dict)
        ):
            history[raw_date] = {
                profile_id: _empty_row(
                    profile_id, raw_date, "prior_report_contract_invalid"
                )
                for profile_id in PROFILES
            }
            continue
        history[raw_date] = {
            profile_id: (
                profiles[profile_id]
                if isinstance(profiles.get(profile_id), dict)
                else _empty_row(profile_id, raw_date, "prior_profile_row_missing")
            )
            for profile_id in PROFILES
        }
    return history


def _latest_prior_policies(candidate_dir: Path, target_date: str) -> dict[str, dict]:
    paths = sorted(
        candidate_dir.glob("low_price_two_leg_policy_candidate_*.json"), reverse=True
    )
    for path in paths:
        payload = _read_json(path)
        if not payload or str(payload.get("source_date") or "") >= target_date:
            continue
        valid, reason = validate_candidate(payload)
        if not valid:
            raise ValueError(f"latest_prior_candidate_{reason}")
        return {
            profile_id: dict(payload["profiles"][profile_id]["policy"])
            for profile_id in PROFILES
        }
    return {
        profile_id: dict(policy) for profile_id, policy in BASELINE_POLICIES.items()
    }


def _samsung_same_stage_owner(
    target_date: str, samsung_candidate_dir: Path
) -> dict[str, Any]:
    path = samsung_candidate_dir / (
        f"samsung_machine_entry_policy_candidate_{target_date}.json"
    )
    if not path.exists():
        return {
            "status": "no_samsung_candidate_for_target_date",
            "mutation_present": False,
            "source_path": str(path),
        }
    payload = _read_json(path)
    if payload is None:
        return {
            "status": "samsung_candidate_invalid_fail_closed",
            "mutation_present": True,
            "source_path": str(path),
        }
    valid, reason = validate_samsung_candidate(payload)
    if not valid:
        return {
            "status": f"samsung_candidate_{reason}_fail_closed",
            "mutation_present": True,
            "source_path": str(path),
        }
    mutations = list(payload.get("policy_mutations") or [])
    return {
        "status": (
            "samsung_regular_entry_mutation_owns_stage"
            if mutations
            else "samsung_candidate_has_no_stage_mutation"
        ),
        "mutation_present": bool(mutations),
        "source_path": str(path),
        "policy_mutations": mutations,
    }


def build_report(
    *,
    target_date: str,
    state_dir: Path = DEFAULT_STATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    source_quality_dir: Path = SOURCE_QUALITY_DIR,
    cost_pct: float = 0.20,
) -> dict:
    parsed_date = date.fromisoformat(target_date)
    if parsed_date < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_precedes_clean_baseline")
    if not math.isfinite(cost_pct) or not 0 <= cost_pct < 100:
        raise ValueError("cost_pct_must_be_finite_percentage")
    daily: dict[str, dict] = {}
    prior_state_reconciliations: dict[str, dict] = {}
    for profile_id in PROFILES:
        state_path = state_dir / f"{profile_id}_state.json"
        state = _read_json(state_path)
        raw_state_date = str((state or {}).get("trade_date") or "")
        try:
            state_date = date.fromisoformat(raw_state_date)
        except ValueError:
            state_date = None
        if state_date is not None and CLEAN_BASELINE_DATE <= state_date < parsed_date:
            resolved_row = extract_profile_row(
                profile_id=profile_id,
                state_path=state_path,
                target_date=state_date.isoformat(),
                cost_pct=cost_pct,
            )
            original_preflight = _source_quality_preflight(
                state_date.isoformat(), source_quality_dir
            )
            if not original_preflight["tuning_input_allowed"]:
                resolved_row["eligible_for_tuning"] = False
                resolved_row["source_quality"] = "gap"
                if (
                    "original_date_source_quality_audit_blocked"
                    not in resolved_row["source_quality_reasons"]
                ):
                    resolved_row["source_quality_reasons"].append(
                        "original_date_source_quality_audit_blocked"
                    )
            prior_state_reconciliations[profile_id] = {
                "source_date": state_date.isoformat(),
                "state_status": resolved_row["state_status"],
                "row": resolved_row,
                "source_quality_preflight": original_preflight,
            }
            daily[profile_id] = _empty_row(
                profile_id,
                target_date,
                "prior_episode_custody_no_current_date_episode",
            )
            continue
        daily[profile_id] = extract_profile_row(
            profile_id=profile_id,
            state_path=state_path,
            target_date=target_date,
            cost_pct=cost_pct,
        )
    source_preflight = _source_quality_preflight(target_date, source_quality_dir)
    if not source_preflight["tuning_input_allowed"]:
        for row in daily.values():
            row["eligible_for_tuning"] = False
            if (
                "observation_source_quality_audit_blocked"
                not in row["source_quality_reasons"]
            ):
                row["source_quality_reasons"].append(
                    "observation_source_quality_audit_blocked"
                )
            row["source_quality"] = "gap"
    history = _load_history(output_dir, parsed_date)
    for profile_id, reconciliation in prior_state_reconciliations.items():
        source_date = reconciliation["source_date"]
        history.setdefault(
            source_date,
            {
                item: _empty_row(
                    item,
                    source_date,
                    "prior_report_missing_during_state_reconciliation",
                )
                for item in PROFILES
            },
        )
        history[source_date][profile_id] = reconciliation["row"]
    history[target_date] = daily
    dates = sorted(history)
    windows: dict[str, dict[str, Any]] = {}
    for name, selected_dates in {
        "rolling10": dates[-10:],
        "rolling20": dates[-20:],
        "cumulative": dates,
    }.items():
        windows[name] = {}
        for profile_id in PROFILES:
            rows = [history[day][profile_id] for day in selected_dates]
            windows[name][profile_id] = {
                "summary": _aggregate(rows),
                "rows": rows,
            }
    return {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "cost_pct": cost_pct,
        "metric_contract": METRIC_CONTRACT,
        "source_quality_preflight": source_preflight,
        "daily": {"profiles": daily},
        "prior_state_reconciliations": prior_state_reconciliations,
        "windows": windows,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "decision": "profile_separated_actual_outcome_observation_only",
    }


def build_candidate(
    report: dict,
    *,
    candidate_dir: Path = CANDIDATE_DIR,
    samsung_candidate_dir: Path = SAMSUNG_CANDIDATE_DIR,
) -> dict:
    prior = _latest_prior_policies(candidate_dir, report["target_date"])
    selected_policies = {
        profile_id: dict(policy) for profile_id, policy in prior.items()
    }
    evaluations: dict[str, dict[str, Any]] = {}
    eligible: list[tuple[float, str, str, float]] = []
    for profile_id in PROFILES:
        current = prior[profile_id]
        current_windows = {
            window: report["windows"][window][profile_id]
            for window in ("rolling10", "rolling20", "cumulative")
        }
        current_outcomes = {
            window: _axis_outcome(
                item["rows"],
                min_drawdown=float(current["rolling_high_drawdown_pct"]),
                max_near_low=float(current["rolling_low_proximity_pct"]),
            )
            for window, item in current_windows.items()
        }
        profile_inventory_clear = all(
            item["summary"]["held_or_unresolved_legs"] == 0
            for item in current_windows.values()
        )
        alternatives: list[tuple[str, float, float]] = []
        bounds = POLICY_BOUNDS[profile_id]
        if float(current["rolling_high_drawdown_pct"]) < bounds["drawdown_max"]:
            alternatives.append(
                (
                    "rolling_high_drawdown_pct",
                    bounds["drawdown_max"],
                    float(current["rolling_low_proximity_pct"]),
                )
            )
        if float(current["rolling_low_proximity_pct"]) > bounds["near_low_min"]:
            alternatives.append(
                (
                    "rolling_low_proximity_pct",
                    float(current["rolling_high_drawdown_pct"]),
                    bounds["near_low_min"],
                )
            )
        evaluated_alternatives = []
        for axis, drawdown, near_low in alternatives:
            outcomes = {
                window: _axis_outcome(
                    item["rows"], min_drawdown=drawdown, max_near_low=near_low
                )
                for window, item in current_windows.items()
            }
            cumulative = outcomes["cumulative"]
            recent = [outcomes["rolling10"], outcomes["rolling20"]]
            current_ev = current_outcomes["cumulative"]["notional_weighted_ev_pct"]
            candidate_ev = cumulative["notional_weighted_ev_pct"]
            ready = bool(
                report["source_quality_preflight"]["tuning_input_allowed"]
                and profile_inventory_clear
                and cumulative["completed_legs"] >= SAMPLE_FLOOR_COMPLETED_LEGS
                and cumulative["held_or_unresolved_legs"] == 0
                and candidate_ev is not None
                and current_ev is not None
                and float(candidate_ev) > max(0.0, float(current_ev))
                and all(
                    item["completed_legs"] >= RECENT_FLOOR_COMPLETED_LEGS
                    and item["held_or_unresolved_legs"] == 0
                    and item["notional_weighted_ev_pct"] is not None
                    and float(item["notional_weighted_ev_pct"]) > 0.0
                    for item in recent
                )
            )
            evaluated_alternatives.append(
                {
                    "axis": axis,
                    "resulting_drawdown_pct": drawdown,
                    "resulting_near_low_pct": near_low,
                    "outcomes": outcomes,
                    "ready": ready,
                }
            )
            if ready:
                after = drawdown if axis == "rolling_high_drawdown_pct" else near_low
                eligible.append(
                    (float(candidate_ev) - float(current_ev), profile_id, axis, after)
                )
        evaluations[profile_id] = {
            "current_policy": current,
            "current_outcomes": current_outcomes,
            "profile_inventory_clear": profile_inventory_clear,
            "alternatives": evaluated_alternatives,
        }
    same_stage_owner = _samsung_same_stage_owner(
        report["target_date"], samsung_candidate_dir
    )
    winner = (
        None if same_stage_owner["mutation_present"] else max(eligible, default=None)
    )
    selected_profile = selected_axis = None
    if winner is not None:
        _, selected_profile, selected_axis, after = winner
        selected_policies[selected_profile][selected_axis] = after
    mutations = policy_mutations_between(prior, selected_policies)
    if len(mutations) > 1:
        raise ValueError("same_stage_multiple_axis_candidate_forbidden")
    profiles = {}
    for profile_id in PROFILES:
        profiles[profile_id] = {
            "selection_status": (
                "selected_next_preopen_bounded_tightening"
                if profile_id == selected_profile
                else "carry_forward_profile_policy"
            ),
            "selected_axis": selected_axis if profile_id == selected_profile else None,
            "policy": selected_policies[profile_id],
            "evaluation": evaluations[profile_id],
            "allowed_runtime_apply": True,
        }
    return {
        "schema": CANDIDATE_SCHEMA,
        "source_date": report["target_date"],
        "generated_at_kst": report["generated_at_kst"],
        "source_report": REPORT_TYPE,
        "source_report_schema": REPORT_SCHEMA,
        "clean_tuning_baseline_date": report["clean_tuning_baseline_date"],
        "source_quality_preflight": report["source_quality_preflight"],
        "policy_hash": policy_hash(selected_policies),
        "policy_mutations": mutations,
        "same_stage_owner_guard": same_stage_owner,
        "profiles": profiles,
        "decision_authority": "postclose_bounded_candidate_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "rollback": "next_preopen_exact_date_artifact_or_verified_baseline",
        "forbidden_uses": METRIC_CONTRACT["forbidden_uses"],
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def render_markdown(report: dict, candidate: dict) -> str:
    lines = [
        f"# Low-price two-leg tuning — {report['target_date']}",
        "",
        "- Decision: profile-separated actual broker outcomes; next-PREOPEN bounded tightening only.",
        "- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.",
        "",
        "| Profile | Symbol | Session | Daily status | Cumulative attempts | Complete legs | Held/unresolved | EV |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for profile_id, row in report["daily"]["profiles"].items():
        summary = report["windows"]["cumulative"][profile_id]["summary"]
        lines.append(
            f"| {profile_id} | {row['symbol']} | {row['session']} | "
            f"{row['source_quality']} | {summary['attempted_episodes']} | "
            f"{summary['completed_legs']} | {summary['held_or_unresolved_legs']} | "
            f"{summary['notional_weighted_ev_pct']} |"
        )
    lines.extend(["", "## Next PREOPEN candidate", ""])
    if candidate["policy_mutations"]:
        item = candidate["policy_mutations"][0]
        lines.append(
            f"- Selected `{item['profile_id']}` `{item['axis']}`: "
            f"{item['before']} -> {item['after']}."
        )
    else:
        lines.append("- No profile/axis mutation; carry forward current policies.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    report: dict, candidate: dict, *, output_dir: Path, candidate_dir: Path
) -> tuple[Path, Path, Path]:
    stem = f"{REPORT_TYPE}_{report['target_date']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    candidate_path = candidate_dir / (
        f"low_price_two_leg_policy_candidate_{report['target_date']}.json"
    )
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(md_path, render_markdown(report, candidate))
    atomic_write_json(candidate_path, candidate)
    return json_path, md_path, candidate_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=CANDIDATE_DIR)
    parser.add_argument("--source-quality-dir", type=Path, default=SOURCE_QUALITY_DIR)
    parser.add_argument("--cost-pct", type=float, default=0.20)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        target_date=args.target_date,
        state_dir=args.state_dir,
        output_dir=args.output_dir,
        source_quality_dir=args.source_quality_dir,
        cost_pct=args.cost_pct,
    )
    candidate = build_candidate(report, candidate_dir=args.candidate_dir)
    valid, reason = validate_candidate(candidate)
    if not valid:
        raise ValueError(reason)
    paths = write_outputs(
        report,
        candidate,
        output_dir=args.output_dir,
        candidate_dir=args.candidate_dir,
    )
    if args.print_summary:
        print(
            json.dumps(
                {
                    "target_date": args.target_date,
                    "report_path": str(paths[0]),
                    "markdown_path": str(paths[1]),
                    "candidate_path": str(paths[2]),
                    "policy_mutations": candidate["policy_mutations"],
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
