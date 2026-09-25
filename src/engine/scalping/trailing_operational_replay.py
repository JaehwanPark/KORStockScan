"""Bounded, source-qualified input sensitivity for trailing exit operations.

An input crossing is not a counterfactual fill.  In particular, a different
poll, quote, REST or AI call can change future observations.  Such paths remain
unidentified until their independent source and safety owner can replay them.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any

from src.engine.scalping.trailing_start_replay import _flag, _number
from src.engine.scalping.trailing_threshold_policy import START_MARKETS, market_type_at

SCHEMA = "scalp_trailing_operational_input_replay_v1"
GRID_VERSION = "scalp_trailing_operational_input_grid_v1"

# Diagnostic grids only.  They have no policy selection or runtime authority.
GRID: dict[str, tuple[float, ...]] = {
    "KORSTOCKSCAN_SCALP_FAST_EXIT_POLL_MS": (200, 250, 300, 500),
    "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MAX_0D_AGE_MS": (1000, 1500, 2000),
    "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MIN_0B_STALE_MS": (1000, 1500, 2000),
    "AI_HOLDING_CRITICAL_COOLDOWN": (30, 45, 60),
    "AI_HOLDING_CRITICAL_MIN_COOLDOWN": (10, 20, 30),
    "AI_HOLDING_MIN_COOLDOWN": (30, 45, 60),
    "AI_HOLDING_MAX_COOLDOWN": (120, 180, 240),
    "SCALP_SAFE_PROFIT": (0.8, 1.0, 1.2),
    "AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC": (1.0, 1.5, 2.0),
    "AI_HOLDING_NEAR_SAFE_PROFIT_BAND_PCT": (0.1, 0.2, 0.3),
    "AI_HOLDING_CRITICAL_PRICE_TRIGGER_PCT": (0.1, 0.2, 0.3),
    "AI_HOLDING_NORMAL_PRICE_TRIGGER_PCT": (0.3, 0.4, 0.5),
    "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS": (500, 700, 900),
    "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_REST_AGE_MS": (1000, 1500, 2000),
    "KORSTOCKSCAN_QUOTE_CONSISTENCY_WARN_GAP_BPS": (60, 80, 100),
    "KORSTOCKSCAN_QUOTE_CONSISTENCY_EMERGENCY_REST_TIMEOUT_MS": (300, 400, 500),
    "HOLDING_EXIT_REST_QUOTE_FALLBACK_MIN_INTERVAL_SEC": (5, 10, 15),
}

POLL = "KORSTOCKSCAN_SCALP_FAST_EXIT_POLL_MS"
NXT_0D = "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MAX_0D_AGE_MS"
NXT_0B = "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MIN_0B_STALE_MS"
AI_CRITICAL_TTL = "AI_HOLDING_CRITICAL_COOLDOWN"
AI_REUSE = "AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC"
WS_AGE = "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS"
REST_AGE = "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_REST_AGE_MS"
WARN_GAP = "KORSTOCKSCAN_QUOTE_CONSISTENCY_WARN_GAP_BPS"
REST_TIMEOUT = "KORSTOCKSCAN_QUOTE_CONSISTENCY_EMERGENCY_REST_TIMEOUT_MS"
REST_INTERVAL = "HOLDING_EXIT_REST_QUOTE_FALLBACK_MIN_INTERVAL_SEC"
AI_GATE_KEYS = {
    "AI_HOLDING_CRITICAL_MIN_COOLDOWN", "AI_HOLDING_MIN_COOLDOWN",
    "AI_HOLDING_MAX_COOLDOWN", "SCALP_SAFE_PROFIT",
    "AI_HOLDING_NEAR_SAFE_PROFIT_BAND_PCT",
    "AI_HOLDING_CRITICAL_PRICE_TRIGGER_PCT",
    "AI_HOLDING_NORMAL_PRICE_TRIGGER_PCT",
    AI_CRITICAL_TTL,
}
SHARED_QUOTE_KEYS = {WS_AGE, REST_AGE, WARN_GAP, REST_TIMEOUT, REST_INTERVAL}
OWNER_PATHS = {
    "shared_quote_safety": (
        "src/trading/market/quote_consistency.py:build_quote_consistency_snapshot",
        "src/engine/sniper_state_handlers.py:_build_quote_consistency_fields",
        "src/engine/sniper_state_handlers.py:_fetch_rest_orderbook_snapshot_bounded",
        "src/engine/sniper_state_handlers.py:_recover_scalp_trailing_bid_for_normal",
    ),
    "holding_ai_shared": (
        "src/engine/sniper_state_handlers.py:handle_holding_state",
        "src/engine/sniper_state_handlers.py:_holding_score_runtime_context",
    ),
    "scalp_exit_input_quality": (
        "src/engine/sniper_state_handlers.py:evaluate_and_dispatch_fast_scalp_exit",
        "src/engine/sniper_state_handlers.py:_scalp_nxt_trailing_bid_guard_context",
    ),
}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _owner(key: str) -> str:
    if key in SHARED_QUOTE_KEYS:
        return "shared_quote_safety"
    if key.startswith("AI_HOLDING") or key == "SCALP_SAFE_PROFIT":
        return "holding_ai_shared"
    return "scalp_exit_input_quality"


def _relevant(row: dict, key: str) -> bool:
    evaluator = str(row.get("evaluator") or "")
    if key == POLL:
        return evaluator.startswith("fast")
    if (key in {NXT_0D, NXT_0B, REST_INTERVAL, AI_REUSE}
            or key in AI_GATE_KEYS and key != AI_CRITICAL_TTL):
        return evaluator.startswith("normal")
    return True


def _ai_gate(row: dict, values: dict[str, float]) -> bool | None:
    """Recreate the pre-review cadence gate, not an unobserved provider output."""

    profit = _number(row.get("holding_profit_rate_at_eval"))
    elapsed = _number(row.get("holding_ai_elapsed_since_review_sec"))
    change = _number(row.get("holding_ai_price_change_since_review_pct"))
    available = _flag(row.get("holding_ai_gate_prerequisites_met"))
    sim_budget = _flag(row.get("holding_ai_sim_budget_target"))
    if (profit is None or elapsed is None or change is None or available is None
            or not all(math.isfinite(float(values[key])) for key in AI_GATE_KEYS)):
        return None
    if not available:
        return False
    # Simulation has separate cooldown controls.  The real holding cadence
    # grid cannot be applied to that path without its own recorded policy.
    if sim_budget is not False:
        return None
    near = abs(profit - values["SCALP_SAFE_PROFIT"]) <= (
        values["AI_HOLDING_NEAR_SAFE_PROFIT_BAND_PCT"]
    )
    critical = near or profit >= values["SCALP_SAFE_PROFIT"] or profit < 0
    minimum = values[
        "AI_HOLDING_CRITICAL_MIN_COOLDOWN" if critical
        else "AI_HOLDING_MIN_COOLDOWN"
    ]
    maximum = values[
        AI_CRITICAL_TTL if critical else "AI_HOLDING_MAX_COOLDOWN"
    ]
    trigger = values[
        "AI_HOLDING_CRITICAL_PRICE_TRIGGER_PCT" if critical
        else "AI_HOLDING_NORMAL_PRICE_TRIGGER_PCT"
    ]
    return elapsed > minimum and (near or change >= trigger or elapsed > maximum)


def _gate(row: dict, key: str, value: float, values: dict[str, float]) -> Any:
    if key == REST_INTERVAL and _flag(row.get("holding_rest_first_request_eligible")) is True:
        return True
    if key in {NXT_0D, NXT_0B}:
        item = str(row.get("nxt_trailing_bid_guard_ws_0d_item") or "")
        route = str(row.get("nxt_trailing_bid_guard_ws_0d_route") or "").lower()
        if (not item.endswith(("_NX", "_AL"))
                or route not in {"nxt_only", "krx_nxt_integrated"}):
            return None
    if key in AI_GATE_KEYS:
        candidate = dict(values)
        candidate[key] = value
        due = _ai_gate(row, candidate)
        if key == AI_CRITICAL_TTL:
            age = _number(row.get("ai_score_age_sec"))
            return (due, age <= value) if age is not None else None
        return due
    if key == WARN_GAP and str(row.get("evaluator") or "").startswith("fast"):
        spread = _number(row.get("operational_executable_spread_bps"))
        mark_gap = _number(row.get("operational_mark_to_bid_gap_bps"))
        if spread is None or mark_gap is None or spread < 0 or mark_gap < 0:
            return None
        return max(spread, mark_gap) > value
    if key == WARN_GAP:
        gap = _number(row.get("ws_rest_gap_bps"))
        tick_floor = _number(row.get("operational_quote_warn_tick_floor_bps"))
        if gap is None or tick_floor is None or gap < 0 or tick_floor < 0:
            return None
        return gap > max(value, tick_floor)
    metric_field = {
        NXT_0D: "nxt_trailing_bid_guard_ws_0d_age_ms",
        NXT_0B: "nxt_trailing_bid_guard_ws_0b_age_ms",
        AI_REUSE: "holding_ai_fast_reuse_ws_age_sec",
        WS_AGE: "quote_consistency_ws_age_ms",
        REST_AGE: "quote_consistency_rest_age_ms",
        WARN_GAP: "ws_rest_gap_bps",
        REST_TIMEOUT: "holding_rest_request_elapsed_ms",
        REST_INTERVAL: "holding_rest_since_last_request_sec",
    }.get(key)
    metric = _number(row.get(metric_field)) if metric_field else None
    if key == NXT_0B and metric is None and row.get(metric_field) == "-":
        # The live NXT guard treats an absent 0B receive clock as stale.
        return True
    if metric is None or metric < 0:
        return None
    if key in {NXT_0B, WARN_GAP, REST_INTERVAL}:
        return metric >= value if key != WARN_GAP else metric > value
    return metric <= value


def operational_shadow_state(row: dict, values: dict[str, float]) -> tuple:
    """Compact gate vector evaluated at every live observation, including unlogged ones."""

    return tuple(
        (key, tuple(
            (candidate, _gate(row, key, candidate, values))
            for candidate in sorted(set(grid) | {float(values[key])})
        ))
        for key, grid in GRID.items() if key != POLL
    )


def _prepare(trade: dict, outcome: dict) -> dict:
    trade_id = str(trade.get("id") or "")
    result = {"id": trade_id, "rows": [], "source_gap": None}
    if (trade.get("trailing_event_source_status") != "structured_partition_read"
            or not trade.get("trailing_event_source_sha256")):
        result["source_gap"] = "source_gap_structured_event_provenance"
        return result
    rows = [event.get("fields") or {} for event in trade.get("timeline") or []
            if isinstance(event, dict)
            and event.get("stage") == "scalp_trailing_input_transition"]
    if not rows:
        result["source_gap"] = "source_gap_no_operational_transition"
        return result
    values = outcome.get("trailing_operational_values")
    if not isinstance(values, dict) or not set(GRID).issubset(values):
        result["source_gap"] = "source_gap_operational_value_census"
        return result
    try:
        numeric = {key: float(values[key]) for key in GRID}
        if not all(math.isfinite(value) and value > 0 for value in numeric.values()):
            raise ValueError("invalid_value")
        digest = _digest(values)
    except (TypeError, ValueError):
        result["source_gap"] = "source_gap_operational_value_invalid"
        return result
    if (outcome.get("trailing_operational_value_sha256") != digest
            or any(row.get("operational_threshold_value_sha256") != digest
                   for row in rows)):
        result["source_gap"] = "source_gap_operational_generation_mismatch"
        return result
    previous = float("-inf")
    prepared = []
    for sequence, row in enumerate(rows, 1):
        at = _number(row.get("evaluation_at_epoch"))
        market = market_type_at(at) if at is not None else None
        if (at is None or at < previous or market not in START_MARKETS
                or row.get("tuning_market_type") != market
                or _number(row.get("event_sequence")) != sequence
                or _flag(row.get("observation_coverage_exhausted")) is not False
                or _flag(row.get("observation_telemetry_gap")) is not False
                or _number(row.get("tuning_grid_evaluations_since_event")) is None):
            result["source_gap"] = "source_gap_operational_evaluation_coverage"
            return result
        evaluations = _number(row.get("tuning_grid_evaluations_since_event"))
        max_gap = _number(row.get("tuning_grid_max_evaluation_gap_sec"))
        shadowed = (
            row.get("tuning_operational_shadow_version") == GRID_VERSION
            and row.get("tuning_operational_shadow_sha256")
                == _digest(operational_shadow_state(row, numeric))
        )
        if (evaluations < 1 or not evaluations.is_integer()
                or max_gap is None or max_gap < 0 or max_gap > 2
                or (evaluations > 1 and not shadowed)
                or (row.get("tuning_operational_shadow_version") and not shadowed)):
            result["source_gap"] = "source_gap_operational_shadow_or_clock_coverage"
            return result
        if str(row.get("position_key") or "") != f"record:{trade_id}":
            result["source_gap"] = "source_gap_operational_position_identity"
            return result
        prepared.append({**row, "_at": at, "_market": market})
        previous = at
    result.update(rows=prepared, values=numeric, operational_sha256=digest)
    return result


def summarize_operational_input_replay(
    trades: list[dict], outcomes: list[dict], *, population_complete: bool,
) -> dict:
    """Compare observable input crossings across three markets without promotion."""

    trade_by_id = {str(trade.get("id")): trade for trade in trades}
    outcome_by_id = {str(row.get("record_id")): row for row in outcomes}
    identity_complete = bool(
        len(trade_by_id) == len(trades) and len(outcome_by_id) == len(outcomes)
        and set(trade_by_id) == set(outcome_by_id) and "None" not in trade_by_id
    )
    result = {
        "schema": SCHEMA, "grid_version": GRID_VERSION,
        "grid_sha256": _digest(GRID),
        "decision_authority": "report_only_shared_owner_review_required",
        "metric_role": "input_crossing_sensitivity_not_paired_ev",
        "population_complete": bool(population_complete),
        "strict_completed_position_ids": sorted(trade_by_id),
        "position_identity_census_complete": identity_complete,
        "research_candidate": None, "runtime_selected": None,
        "axes": {key: {"owner": _owner(key), "diagnostic_grid": list(grid)}
                 for key, grid in GRID.items()},
        "source_gap_by_id": {}, "markets": {},
    }
    if not population_complete or not trade_by_id or not identity_complete:
        result["status"] = "hold_population_census_or_empty"
        return result
    prepared = {trade_id: _prepare(trade, outcome_by_id[trade_id])
                for trade_id, trade in trade_by_id.items()}
    result["source_gap_by_id"] = {trade_id: row["source_gap"]
                                  for trade_id, row in prepared.items() if row["source_gap"]}
    for market in START_MARKETS:
        clock_blocked = sorted(
            trade_id for trade_id, row in prepared.items()
            if any(event["_market"] == market
                   and _flag(event.get("tuning_exit_allowed_by_clock")) is not True
                   for event in row["rows"])
        )
        exposed = {trade_id: row for trade_id, row in prepared.items()
                   if any(event["_market"] == market
                          and _flag(event.get("tuning_exit_allowed_by_clock")) is True
                          for event in row["rows"])}
        market_result = {"exposed_ids": sorted(exposed),
                         "exit_clock_blocked_ids": clock_blocked, "axes": {}}
        result["markets"][market] = market_result
        for key, grid in GRID.items():
            axis_exposed = {trade_id: item for trade_id, item in exposed.items()
                            if any(event["_market"] == market
                                   and _flag(event.get("tuning_exit_allowed_by_clock")) is True
                                   and _relevant(event, key)
                                   for event in item["rows"])}
            values = sorted({row["values"][key] for row in axis_exposed.values()})
            axis = {"owner": _owner(key), "exposed_ids": sorted(axis_exposed),
                    "incumbent_values": values,
                    "candidates": {}, "research_candidate": None,
                    "runtime_selected": None}
            market_result["axes"][key] = axis
            if not axis_exposed:
                axis["status"] = "not_exposed"
                continue
            if len(values) != 1:
                axis["status"] = "source_gap_mixed_incumbent_values"
                continue
            incumbent = values[0]
            for candidate in sorted(set(grid) | {incumbent}):
                same_ids, changed_ids, missing_ids, unresolved_ids = [], [], [], []
                first_divergence = {}
                first_transition = {}
                reasons = Counter()
                observed_event_count = 0
                changed_metric_event_count = 0
                for trade_id, item in axis_exposed.items():
                    rows = [row for row in item["rows"] if row["_market"] == market
                            and _flag(row.get("tuning_exit_allowed_by_clock")) is True
                            and _relevant(row, key)]
                    observed_event_count += len(rows)
                    if candidate == incumbent:
                        same_ids.append(trade_id)
                        continue
                    if key == POLL and candidate < incumbent:
                        unresolved_ids.append(trade_id)
                        reasons["faster_than_observed_poll_unidentifiable"] += 1
                        continue
                    if key in {NXT_0D, NXT_0B} and market != "INTEGRATED_AFTERMARKET":
                        same_ids.append(trade_id)
                        continue
                    changed_at = None
                    reason = None
                    for row in rows:
                        if key == POLL:
                            if candidate > incumbent:
                                reason = "unobserved_poll_phase_or_stop_latency"
                                changed_at = row["_at"]
                            continue
                        baseline = _gate(row, key, incumbent, item["values"])
                        alternative = _gate(row, key, candidate, item["values"])
                        if baseline is None or alternative is None:
                            reason = "source_gap_axis_input"
                            break
                        if baseline != alternative:
                            changed_metric_event_count += 1
                            if changed_at is None:
                                changed_at = row["_at"]
                                first_transition[trade_id] = {
                                    "incumbent_gate": baseline,
                                    "candidate_gate": alternative,
                                }
                            reason = (
                                "unobserved_ai_provider_or_reuse_action"
                                if key in AI_GATE_KEYS or key == AI_REUSE else
                                "unobserved_quote_or_rest_substitution"
                            )
                    if reason == "source_gap_axis_input":
                        missing_ids.append(trade_id)
                        reasons[reason] += 1
                    elif key == POLL and changed_at is not None:
                        unresolved_ids.append(trade_id)
                        reasons[reason] += 1
                    elif changed_at is not None:
                        changed_ids.append(trade_id)
                        first_divergence[trade_id] = changed_at
                        reasons[reason or "action_effect_unidentified"] += 1
                    else:
                        same_ids.append(trade_id)
                axis["candidates"][str(candidate)] = {
                    "value": candidate,
                    "status": (
                        "source_gap" if missing_ids else
                        "action_effect_unidentified" if changed_ids else
                        "unobserved_sampling_effect" if unresolved_ids else
                        "incumbent_observed" if candidate == incumbent else
                        "observed_metric_same_action_unproven"
                    ),
                    "observed_input_same_ids": sorted(same_ids),
                    "changed_input_ids": sorted(changed_ids),
                    "source_gap_ids": sorted(missing_ids),
                    "unidentified_sampling_ids": sorted(unresolved_ids),
                    "first_divergence_at_by_id": first_divergence,
                    "first_observed_metric_transition_by_id": first_transition,
                    "observed_event_count": observed_event_count,
                    "changed_metric_event_count": changed_metric_event_count,
                    "reason_counts": dict(reasons),
                    "paired_ev_pct": None,
                    "candidate_value_for_runtime": None,
                }
            axis["status"] = "input_sensitivity_only_no_economic_candidate"
            changed = sorted({trade_id for row in axis["candidates"].values()
                              for trade_id in row["changed_input_ids"]})
            missing = sorted({trade_id for row in axis["candidates"].values()
                              for trade_id in row["source_gap_ids"]})
            unresolved = sorted({trade_id for row in axis["candidates"].values()
                                 for trade_id in row["unidentified_sampling_ids"]})
            axis["owner_review"] = {
                "status": "safety_and_action_evidence_pending",
                "code_owner_paths": list(OWNER_PATHS[_owner(key)]),
                "observed_metric_crossing_ids": changed,
                "source_gap_ids": missing,
                "unidentified_sampling_ids": unresolved,
                "required_consumer_scope": (
                    "entry|scale_in|holding|stop|protect|emergency"
                    if key in SHARED_QUOTE_KEYS else
                    "real_holding|sim_holding|provider_cost|score_ttl"
                    if _owner(key) == "holding_ai_shared" else
                    "take_profit|stop_latency|order_load"
                ),
                "cross_consumer_safety_verified": False,
                "allowed_runtime_apply": False,
            }
    exposed_count = sum(len(row["exposed_ids"]) for row in result["markets"].values())
    result["status"] = (
        "source_gap_input_path" if len(result["source_gap_by_id"]) == len(trades)
        else "no_exit_clock_exposure" if not exposed_count
        else "input_sensitivity_only_no_live_candidate"
    )
    return result
