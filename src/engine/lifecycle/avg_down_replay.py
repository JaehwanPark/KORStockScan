"""Pure AVG_DOWN evidence identities and independent lifecycle replay.

This module owns offline state reconstruction, never broker execution. Missing
policy/market/AI evidence is a blocked replay, not an assumed HOLD or fill.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

CONFIG_SCHEMA = "avg_down_runtime_config_v1"
REPLAY_SCHEMA = "avg_down_independent_exit_replay_v1"
FRAME_SCHEMA = "avg_down_exit_replay_frame_v1"
METHOD = "paired_add_no_add_lifecycle_replay"


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def policy_fingerprint(rules: Any) -> str:
    """Freeze AVG_DOWN inputs, excluding the independently tuned threshold.

    Entry sizing, prompt, scanner, generic holding, and exit settings are
    owned elsewhere and must not split an otherwise identical AVG_DOWN cohort.
    Keep only AVG_DOWN-specific contracts plus the shared scale-in and shallow
    source-gap contracts. A broad ``SCALP_*`` or ``HOLDING_*`` prefix would
    otherwise turn unrelated changes into a new policy cohort.
    """
    source = (
        rules
        if isinstance(rules, Mapping)
        else vars(rules) if rules is not None else {}
    )
    values = {
        str(key): value
        for key, value in source.items()
        if (
            "AVG_DOWN" in str(key)
            or str(key).startswith(
                (
                    "SCALPING_SCALE_IN_",
                    "KORSTOCKSCAN_SHALLOW_SOURCE_GAP_RECHECK_",
                )
            )
        )
        and key != "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE"
        and isinstance(value, (str, int, float, bool, list, dict, type(None)))
    }
    return "avg_down_policy:" + canonical_digest(values) if values else "unknown"


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def cost_rate_from_version(value: Any) -> float | None:
    prefix = "trade_profit_net_realized_pnl:rate="
    if not isinstance(value, str) or not value.startswith(prefix):
        return None
    rate = finite_number(value[len(prefix) :])
    return rate if rate is not None and 0 <= rate < 1 else None


def runtime_config_valid(value: Mapping[str, Any]) -> bool:
    current = finite_number(value.get("effective_min_buy_pressure"))
    configured = finite_number(value.get("configured_min_buy_pressure"))
    source = value.get("runtime_value_source")
    return bool(
        value.get("runtime_config_schema") == CONFIG_SCHEMA
        and source_only_observation_valid(
            value, "source_only_runtime_config_observation"
        )
        and current is not None
        and current == configured
        and source in {"exact_process_env", "runtime_rules_loaded_value"}
        and (
            source != "exact_process_env"
            or finite_number(value.get("runtime_value_raw")) == current
        )
        and value.get("runtime_pid_value_verified") is True
        and all(
            isinstance(value.get(key), str) and value.get(key) not in {"", "unknown"}
            for key in (
                "avg_down_policy_version",
                "sizing_policy_version",
                "cost_policy_version",
            )
        )
    )


def source_only_observation_valid(value: Mapping[str, Any], authority: str) -> bool:
    def matches(key: str, expected: bool) -> bool:
        raw = value.get(key)
        return raw is expected or (
            isinstance(raw, str)
            and raw.lower() in ({"true", "1"} if expected else {"false", "0"})
        )

    return value.get("decision_authority") == authority and all(
        matches(key, expected)
        for key, expected in (
            ("runtime_effect", False),
            ("allowed_runtime_apply", False),
            ("actual_order_submitted", False),
            ("broker_order_forbidden", True),
        )
    )


def _positive(value: Any, *, integer: bool = False) -> float:
    number = finite_number(value)
    if number is None or number <= 0 or (integer and not number.is_integer()):
        raise ValueError("missing_or_invalid_positive_input")
    return number


def _epoch(value: Any) -> float:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("replay_timestamp_timezone_missing")
    return parsed.timestamp()


def initial_state(
    observation: Mapping[str, Any], arm: Mapping[str, Any]
) -> dict[str, Any]:
    qty = int(_positive(observation["pre_add_buy_qty"], integer=True))
    price = _positive(observation["pre_add_buy_price"])
    policy_state = observation.get("initial_policy_state")
    if not isinstance(policy_state, dict) or not policy_state:
        raise ValueError("initial_full_holding_policy_state_missing")
    pending = None
    if arm.get("should_add") is True:
        pending = {
            "qty": int(_positive(arm.get("proposed_add_qty"), integer=True)),
            "price": _positive(arm.get("proposed_add_price"), integer=True),
            "expires_at": _epoch(arm.get("add_order_expires_at")),
            **(
                {
                    "add_type": arm.get("add_type", "AVG_DOWN"),
                    "reason": arm.get("action_reason", arm.get("selected_route", "")),
                }
                if observation.get("policy_snapshot")
                else {}
            ),
        }
        if pending["expires_at"] <= _epoch(observation["emitted_at"]):
            raise ValueError("add_order_expiry_not_after_decision")
    return {
        "qty": qty,
        "buy_price": price,
        "legs": [{"qty": qty, "price": price}],
        "peak_price": _positive(observation.get("replay_peak_price")),
        "pending_add": pending,
        "policy_state": deepcopy(policy_state),
        "filled_add_qty": 0,
        "realized_pnl_krw": 0,
    }


def policy_input_digest(
    state: Mapping[str, Any], frame: Mapping[str, Any], policy: str
) -> str:
    """An AI/holding decision for A is not reusable on B's different state."""
    return canonical_digest(
        {
            "state": state,
            "frame_id": frame["source_event_id"],
            "market": frame["market"],
            "policy_version": policy,
        }
    )


def _fill_pending(state: dict[str, Any], frame: Mapping[str, Any]) -> None:
    """Quote-touch is an assumption, never a broker fill-quality claim."""
    pending = state["pending_add"]
    if pending is None:
        return
    if _epoch(frame["emitted_at"]) >= pending["expires_at"]:
        # Cancellation acknowledgement cannot be inferred from timeout alone.
        raise ValueError("expired_add_requires_state_bound_cancel_evaluation")
    market = frame["market"]
    ask = _positive(market.get("best_ask"), integer=True)
    if ask > pending["price"]:
        return
    ask_qty = finite_number(market.get("best_ask_qty"))
    if ask_qty is None or ask_qty < 0 or not ask_qty.is_integer():
        raise ValueError("add_quote_quantity_missing_or_invalid")
    if ask_qty == 0:
        return
    # Partial fills are deliberately not promoted as full fills. A future
    # depth/receipt adapter must preserve their independent inventory state.
    if ask_qty < pending["qty"]:
        raise ValueError("partial_add_fill_replay_not_supported")
    price, qty = pending["price"], pending["qty"]
    state["legs"].append({"qty": qty, "price": price})
    state["qty"] += qty
    state["buy_price"] = (
        sum(leg["qty"] * leg["price"] for leg in state["legs"]) / state["qty"]
    )
    state["filled_add_qty"] += qty
    state["last_virtual_fill"] = {**pending, "filled_at": frame["emitted_at"]}
    state["pending_add"] = None


def replay_exit_paths(
    observation: Mapping[str, Any],
    frames: list[dict[str, Any]],
    *,
    full_exit_evaluator=None,
) -> dict[str, Any]:
    """Replay independent inventory/exit paths using the *existing* full policy.

    By default consume hash-bound evaluations recorded for the exact arm state.
    An offline evaluator may supply missing evaluations through the same contract;
    this engine never calls providers, reads runtime env, or dispatches orders.
    Unknown AI/holding decisions create explicit replay requests and stop the arm.
    A quote-only replay remains source-only, including after all arms terminate.
    """
    from src.engine.trade_profit import calculate_net_realized_pnl

    result: dict[str, Any] = {
        "schema": REPLAY_SCHEMA,
        "evaluation_method": METHOD,
        "position_episode_id": observation.get("position_episode_id"),
        "source_observation_id": observation.get("source_event_id"),
        "scale_in_decision_id": observation.get("scale_in_decision_id"),
        "exit_policy_version": observation.get("exit_policy_version"),
        "decision_authority": "source_only_paired_exit_replay",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_authority_ready": False,
        "outcomes": {},
        "replay_requests": [],
        "blockers": {},
        "fill_evidence_class": "quote_touch_counterfactual",
    }
    try:
        decision_epoch = _epoch(observation["emitted_at"])
        if decision_epoch < _epoch("2026-06-05T00:00:00+09:00"):
            raise ValueError("pre_clean_baseline_replay_forbidden")
        policy = observation.get("exit_policy_version")
        if not isinstance(policy, str) or policy in {"", "unknown"}:
            raise ValueError("exit_policy_version_missing")
        cost_rate = finite_number(observation.get("cost_rate"))
        if cost_rate is None or not 0 <= cost_rate < 1:
            raise ValueError("cost_policy_rate_missing")
        component = observation.get("strategy_owner_replay")
        if component:
            from src.engine.scalping.strategy_owner_components import bounded_change

            if not bounded_change(
                component.get("family"),
                component.get("baseline"),
                component.get("profile"),
            ):
                raise ValueError("owner_component_bounded_profile_invalid")
        route_replay = (
            {
                key: {
                    "should_add": False,
                    "route_evaluation_complete": True,
                    "owner_component_profile": component[key],
                }
                for key in ("baseline", "profile")
            }
            if component
            else observation["route_replay"]
        )
        if not isinstance(route_replay, dict) or not route_replay:
            raise ValueError("route_replay_missing")
        if "NO_ADD" in route_replay:
            raise ValueError("reserved_no_add_arm_in_route_replay")
        current_key = (
            "baseline"
            if component
            else f"{_positive(observation.get('effective_min_buy_pressure')):g}"
        )
        if current_key not in route_replay or len(route_replay) < 2:
            raise ValueError("current_and_candidate_route_required")
        if not isinstance(frames, list) or any(
            not isinstance(frame, dict) for frame in frames
        ):
            raise ValueError("replay_frames_invalid")
        if any(
            not observation.get(key)
            for key in (
                "source_event_id",
                "position_episode_id",
                "stock_code",
                "venue",
                "scale_in_decision_id",
            )
        ):
            raise ValueError("replay_observation_identity_missing")
        ordered = sorted(frames, key=lambda value: _epoch(value["emitted_at"]))
        frame_ids: dict[str, str] = {}
        checked_frames = []
        start_sequence = finite_number(observation.get("replay_start_sequence"))
        if (
            start_sequence is None
            or start_sequence < 0
            or not start_sequence.is_integer()
        ):
            raise ValueError("replay_start_sequence_invalid")
        previous_seq = int(start_sequence)
        previous_epoch = decision_epoch
        tail_gap = None
        # A conflicting duplicate invalidates its original event, even when
        # discovered after exit. Ordinary later missing quotes do not.
        all_ids = {}
        for frame in ordered:
            frame_id = str(frame.get("source_event_id") or "")
            fingerprint = canonical_digest(frame)
            if frame_id and frame_id in all_ids and all_ids[frame_id] != fingerprint:
                raise ValueError("conflicting_replay_frame")
            all_ids[frame_id] = fingerprint
        for frame in ordered:
            epoch = _epoch(frame["emitted_at"])
            if epoch <= decision_epoch:
                continue
            max_gap = finite_number(observation.get("replay_max_frame_gap_sec"))
            if frame.get("capture_gap") or (
                max_gap is not None and epoch - previous_epoch > max_gap
            ):
                tail_gap = "replay_capture_continuity_gap"
                break
            fingerprint = canonical_digest(frame)
            frame_id = str(frame.get("source_event_id") or "")
            if frame_id in frame_ids:
                if frame_ids[frame_id] != fingerprint:
                    raise ValueError("conflicting_replay_frame")
                continue
            if (
                not frame_id
                or frame.get("replay_frame_schema") != FRAME_SCHEMA
                or (
                    observation.get("policy_snapshot")
                    and (
                        frame.get("source_observation_id")
                        != observation.get("source_event_id")
                        or frame.get("scale_in_decision_id")
                        != observation.get("scale_in_decision_id")
                    )
                )
                or any(
                    frame.get(key) != observation.get(key)
                    for key in (
                        "position_episode_id",
                        "stock_code",
                        "venue",
                        "exit_policy_version",
                    )
                )
                or finite_number(frame.get("sequence")) != previous_seq + 1
                or epoch <= previous_epoch
            ):
                tail_gap = "replay_frame_identity_policy_or_sequence_gap"
                break
            market = frame.get("market")
            if (
                not isinstance(market, dict)
                or market.get("source_quality") != "fresh_conflict_free"
            ):
                tail_gap = "replay_market_source_quality_gap"
                break
            try:
                bid = _positive(market.get("best_bid"), integer=True)
                ask = _positive(market.get("best_ask"), integer=True)
            except ValueError as exc:
                tail_gap = str(exc)
                break
            if bid > ask:
                tail_gap = "replay_crossed_quote"
                break
            frame_ids[frame_id] = fingerprint
            checked_frames.append(frame)
            previous_seq = int(frame["sequence"])
            previous_epoch = epoch
        if not checked_frames:
            raise ValueError(tail_gap or "replay_market_path_missing")
        if tail_gap:
            result["unconsumed_tail_gap"] = tail_gap
        replay_arms = (
            route_replay
            if component
            else {
                **route_replay,
                "NO_ADD": {"should_add": False, "route_evaluation_complete": True},
            }
        )
        for key, arm in replay_arms.items():
            try:
                if not isinstance(arm, dict):
                    raise ValueError("route_arm_schema_invalid")
                if arm.get("route_evaluation_complete") is not True:
                    raise ValueError("route_arbitration_incomplete")
                if (
                    arm.get("should_add") is True
                    and arm.get("price_allowed") is not True
                ):
                    raise ValueError("route_price_not_allowed")
                if not isinstance(arm.get("should_add"), bool):
                    raise ValueError("route_add_action_missing")
                state = initial_state(observation, arm)
                state["tuning_env_key"] = observation.get("tuning_env_key") or "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE"
                state["min_buy_pressure"] = (
                    None if component or key == "NO_ADD" else _positive(key)
                )
                # Component replay does not suppress another owner's ADD gate.
                # Its unmodelled broker boundary becomes an explicit source gap.
                state["no_add_control"] = key == "NO_ADD"
                if component:
                    state["owner_component_profile"] = arm["owner_component_profile"]
                state["source_observation_id"] = observation["source_event_id"]
                trace = []
                capital_clock, capital_seconds = decision_epoch, 0.0
                peak_reserved = (state["pending_add"]["price"] * state["pending_add"]["qty"] if state["pending_add"] else 0)
                completed = False
                for frame in checked_frames:
                    # A fill/cancel model is part of the evidence contract,
                    # never an assumption that an unfilled order stays open forever.
                    pending = state["pending_add"]
                    frame_epoch = _epoch(frame["emitted_at"])
                    held_add_notional = sum(leg["qty"] * leg["price"] for leg in state["legs"][1:])
                    capital_seconds += held_add_notional * (frame_epoch - capital_clock)
                    if pending:
                        capital_seconds += pending["qty"] * pending["price"] * max(0, min(frame_epoch, pending["expires_at"]) - capital_clock)
                    peak_reserved = max(peak_reserved, held_add_notional + (pending["qty"] * pending["price"] if pending else 0))
                    capital_clock = frame_epoch
                    if (
                        pending is not None
                        and _epoch(frame["emitted_at"]) >= pending["expires_at"]
                    ):
                        state["pending_add_expired"] = True
                    else:
                        _fill_pending(state, frame)
                    state["peak_price"] = max(
                        state["peak_price"], float(frame["market"]["best_bid"])
                    )
                    input_digest = policy_input_digest(state, frame, policy)
                    records = frame.get("full_policy_decisions", {})
                    if not isinstance(records, dict):
                        raise ValueError("full_exit_policy_evaluations_invalid")
                    record = records.get(input_digest)
                    if record is None and full_exit_evaluator is not None:
                        try:
                            record = full_exit_evaluator(
                                deepcopy(state), deepcopy(frame), policy, input_digest
                            )
                        except Exception:
                            raise ValueError(
                                "offline_full_policy_evaluator_failed"
                            ) from None
                    if record is None:
                        result["replay_requests"].append(
                            {
                                "arm": key,
                                "input_digest": input_digest,
                                "position_episode_id": observation[
                                    "position_episode_id"
                                ],
                                "scale_in_decision_id": observation[
                                    "scale_in_decision_id"
                                ],
                                "frame_id": frame["source_event_id"],
                                "policy_version": policy,
                                "state": deepcopy(state),
                                "market": deepcopy(frame["market"]),
                                "reason": "exact_state_full_holding_exit_evaluation_required",
                                "actual_order_submitted": False,
                                "broker_order_forbidden": True,
                            }
                        )
                        raise ValueError("requires_state_bound_holding_ai_replay")
                    if isinstance(record, dict) and record.get("replay_input_gap"):
                        result.setdefault("replay_input_details", {})[key] = record
                        raise ValueError(str(record["replay_input_gap"]))
                    if (
                        not isinstance(record, dict)
                        or record.get("input_digest") != input_digest
                        or record.get("policy_version") != policy
                        or record.get("full_policy_evaluation") is not True
                        or not record.get("source_event_id")
                        or record.get("input_cutoff") != frame["emitted_at"]
                        or not isinstance(record.get("policy_state_after"), dict)
                        or record.get("actual_order_submitted") is not False
                        or record.get("broker_order_forbidden") is not True
                        or record.get("action")
                        not in (
                            {"HOLD", "EXIT", "ADD", "CANCEL_ADD", "NO_ENTRY"}
                            if component
                            else {"HOLD", "EXIT", "ADD", "CANCEL_ADD"}
                        )
                    ):
                        raise ValueError("full_exit_policy_evaluation_contract_gap")
                    trace.append(
                        {
                            "frame": frame["source_event_id"],
                            "input": input_digest,
                            "decision": canonical_digest(record),
                        }
                    )
                    result.setdefault("last_policy_evaluations", {})[key] = {
                        name: record.get(name)
                        for name in (
                            "action",
                            "adapter_version",
                            "evaluated_stages",
                            "exit_rule",
                        )
                    }
                    state["policy_state"] = deepcopy(record["policy_state_after"])
                    if record["action"] == "NO_ENTRY":
                        if (
                            component.get("family")
                            != "weak_pullback_entry_block_runtime"
                            or len(trace) != 1
                        ):
                            raise ValueError("owner_abstention_contract_invalid")
                        result["outcomes"][key] = {
                            "status": "COMPLETED",
                            "net_pnl_krw": 0.0,
                            "exit_time": observation["emitted_at"],
                            "exit_qty": 0,
                            "full_policy_evaluation": True,
                            "filled_add_qty": 0,
                            "known_no_entry": True,
                            "trace_digest": canonical_digest(trace),
                            "evidence_authority": "source_only_paired_exit_replay",
                        }
                        completed = True
                        break
                    if record.get("pending_add_cancelled") is True:
                        if (
                            state["pending_add"] is None
                            or record["action"] == "CANCEL_ADD"
                        ):
                            raise ValueError(
                                "cancel_without_pending_add_or_duplicate_cancel"
                            )
                        state["pending_add"] = None
                        state.pop("pending_add_expired", None)
                    if "peak_price_after" in record:
                        state["peak_price"] = _positive(record["peak_price_after"])
                    if "buy_price_after" in record:
                        price_after = _positive(record["buy_price_after"])
                        if abs(price_after - state["buy_price"]) > 0.0001:
                            raise ValueError(
                                "policy_inventory_average_changed_without_fill"
                            )
                        state["buy_price"] = price_after
                    if record["action"] == "CANCEL_ADD":
                        if state["pending_add"] is None:
                            raise ValueError("cancel_without_pending_add")
                        state["pending_add"] = None
                        state.pop("pending_add_expired", None)
                        continue
                    if state.get("pending_add_expired") and record["action"] != "HOLD":
                        raise ValueError(
                            "expired_add_requires_state_bound_cancel_evaluation"
                        )
                    if record["action"] == "ADD":
                        if state["no_add_control"] or state["pending_add"] is not None:
                            raise ValueError("add_violates_control_or_pending_order")
                        proposal = record.get("add_order") or {}
                        if (
                            proposal.get("existing_sizing_price_and_safety_evaluated")
                            is not True
                        ):
                            raise ValueError("subsequent_add_sizing_price_safety_gap")
                        state["pending_add"] = {
                            "qty": int(_positive(proposal.get("qty"), integer=True)),
                            "price": _positive(proposal.get("price"), integer=True),
                            "expires_at": _epoch(proposal.get("expires_at")),
                            **(
                                {
                                    "add_type": proposal.get("add_type"),
                                    "reason": proposal.get("reason", ""),
                                }
                                if observation.get("policy_snapshot")
                                else {}
                            ),
                        }
                        if state["pending_add"]["expires_at"] <= _epoch(
                            frame["emitted_at"]
                        ):
                            raise ValueError("add_order_expiry_not_after_decision")
                        peak_reserved = max(peak_reserved, held_add_notional + state["pending_add"]["qty"] * state["pending_add"]["price"])
                        continue
                    if record["action"] == "HOLD":
                        continue
                    if state["pending_add"] is not None:
                        raise ValueError("pending_add_cancel_replay_required")
                    bid = int(frame["market"]["best_bid"])
                    if (
                        _positive(frame["market"].get("best_bid_qty"), integer=True)
                        < state["qty"]
                    ):
                        raise ValueError("partial_exit_fill_replay_not_supported")
                    # Match the existing cumulative sell receipt: weighted
                    # position basis, one fee calculation and one KRW rounding.
                    total_pnl = calculate_net_realized_pnl(
                        round(state["buy_price"], 4), bid, state["qty"], cost_rate=cost_rate)
                    result["outcomes"][key] = {
                        "status": "COMPLETED",
                        "exit_price": bid,
                        "exit_qty": state["qty"],
                        "filled_add_qty": state["filled_add_qty"],
                        "add_fill_evidence": deepcopy(state.get("last_virtual_fill")),
                        "peak_add_reserved_notional_krw": peak_reserved,
                        "add_capital_occupancy_krw_seconds": capital_seconds,
                        "net_pnl_krw": total_pnl,
                        "exit_time": frame["emitted_at"],
                        "exit_policy_version": policy,
                        "terminal_source_event_id": "avgdn-replay-"
                        + canonical_digest(
                            {
                                "decision": observation["scale_in_decision_id"],
                                "arm": key,
                                "trace": trace,
                            }
                        ),
                        "evaluation_method": METHOD,
                        "evidence_authority": "source_only_paired_exit_replay",
                        "trace_digest": canonical_digest(trace),
                        "full_policy_evaluation": True,
                        "legs": deepcopy(state["legs"]),
                        "final_policy_state": deepcopy(state["policy_state"]),
                    }
                    completed = True
                    break
                if not completed:
                    result["blockers"][key] = tail_gap or "pending_exit_outcome"
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                result["blockers"][key] = str(exc)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        result["blockers"]["source"] = str(exc)
    result["state"] = (
        "paired_exit_complete_source_only"
        if not result["blockers"] and result["outcomes"]
        else "paired_exit_replay_blocked"
    )
    if result["state"] == "paired_exit_complete_source_only":
        denominator = _positive(observation["pre_add_buy_price"]) * _positive(
            observation["pre_add_buy_qty"]
        )
        control = result["outcomes"]["baseline" if component else "NO_ADD"][
            "net_pnl_krw"
        ]
        baseline = result["outcomes"][current_key]["net_pnl_krw"]
        result["economics"] = {
            key: {
                "incremental_net_pnl_krw": value["net_pnl_krw"] - control,
                "candidate_minus_current_pnl_krw": value["net_pnl_krw"] - baseline,
                "source_quality_adjusted_ev_pct": 100
                * (value["net_pnl_krw"] - control)
                / denominator,
                "reference_notional": denominator,
            }
            for key, value in result["outcomes"].items()
            if key != "NO_ADD"
        }
    result["evidence_digest"] = canonical_digest(result)
    return result


def build_replay_evidence(
    observations: list[dict[str, Any]],
    *,
    policy_ai_enabled: bool = False,
    cached_policy_ai_records: dict | None = None,
) -> dict[str, Any]:
    """The existing postclose producer runs the replay; no second cron/CLI owner.

    The first decision owns each episode even when incomplete. Never select a
    later profitable comparison merely because its earlier path is missing.
    """
    episodes: dict[str, Any] = {}
    remaining_provider_calls = 64
    reused_count = 0
    deadline = time.monotonic() + 600
    for observation in sorted(
        observations, key=lambda value: str(value.get("emitted_at", ""))
    ):
        episode = str(observation.get("position_episode_id") or "")
        if not episode or episode in episodes:
            continue
        observation_digest = canonical_digest(
            {
                key: value
                for key, value in observation.items()
                if key not in {"independent_exit_replay_frames", "cached_replay_result"}
            }
        )
        cached = observation.get("cached_replay_result")
        if (
            isinstance(cached, dict)
            and cached.get("state") == "paired_exit_complete_source_only"
            and cached.get("replay_observation_digest") == observation_digest
            and source_only_observation_valid(cached, "source_only_paired_exit_replay")
            and cached.get("runtime_authority_ready") is False
            and cached.get("position_episode_id") == episode
            and cached.get("source_observation_id")
            == observation.get("source_event_id")
            and cached.get("scale_in_decision_id")
            == observation.get("scale_in_decision_id")
            and cached.get("evidence_digest")
            == canonical_digest(
                {
                    key: value
                    for key, value in cached.items()
                    if key != "evidence_digest"
                }
            )
        ):
            episodes[episode] = deepcopy(cached)
            reused_count += 1
            continue
        frames = observation.get("independent_exit_replay_frames")
        frames = frames if isinstance(frames, list) else []
        if observation.get("policy_snapshot") and frames:
            from src.engine.lifecycle.avg_down_policy_replay import (
                isolated_replay,
                replay_with_current_policy_ai,
            )

            replayed = (
                {"adapter_error": "policy_replay_report_time_budget_exhausted"}
                if time.monotonic() >= deadline
                else (
                    replay_with_current_policy_ai(
                        observation,
                        frames,
                        max_provider_calls=min(16, remaining_provider_calls),
                        cached_records=(cached_policy_ai_records or {}).get(
                            episode, []
                        ),
                        deadline=deadline,
                    )
                    if policy_ai_enabled
                    else isolated_replay(
                        observation,
                        frames,
                        timeout_sec=min(45, max(0.01, deadline - time.monotonic())),
                    )
                )
            )
            remaining_provider_calls -= replayed.get("policy_ai_provider_call_count", 0)
            if replayed.get("adapter_error"):
                adapter_error = str(replayed["adapter_error"])
                budget_fields = {
                    name: value
                    for name, value in replayed.items()
                    if name.startswith(("policy_ai_", "policy_replay_wall_time"))
                }
                replayed = replay_exit_paths(observation, [])
                replayed.update(budget_fields)
                replayed["blockers"] = {"policy_adapter": adapter_error}
                replayed["evidence_digest"] = canonical_digest(
                    {
                        key: value
                        for key, value in replayed.items()
                        if key != "evidence_digest"
                    }
                )
            episodes[episode] = replayed
        else:
            episodes[episode] = replay_exit_paths(observation, frames)
        spreads = [finite_number(frame.get("market", {}).get("best_ask")) - finite_number(frame.get("market", {}).get("best_bid"))
                   for frame in frames
                   if finite_number(frame.get("market", {}).get("best_ask")) is not None
                   and finite_number(frame.get("market", {}).get("best_bid")) is not None]
        episodes[episode]["observed_max_spread_krw"] = max(spreads) if spreads and all(value >= 0 for value in spreads) else None
        episodes[episode]["fill_evidence_class"] = "modeled_executable_quote_full_or_no_fill"
        episodes[episode]["replay_observation_digest"] = observation_digest
        episodes[episode]["replay_source_date"] = str(
            observation.get("emitted_at", "")
        )[:10]
        episodes[episode]["evidence_digest"] = canonical_digest(
            {
                key: value
                for key, value in episodes[episode].items()
                if key != "evidence_digest"
            }
        )
    blockers: dict[str, int] = {}
    for result in episodes.values():
        for reason in set(result["blockers"].values()):
            blockers[reason] = blockers.get(reason, 0) + 1
    return {
        "schema": REPLAY_SCHEMA,
        "decision_authority": "source_only_paired_exit_replay",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "unique_episode_count": len(episodes),
        "policy_ai_enabled": policy_ai_enabled,
        "policy_ai_provider_call_count": 64 - remaining_provider_calls,
        "cached_episode_count": reused_count,
        "complete_episode_count": sum(
            result["state"] == "paired_exit_complete_source_only"
            for result in episodes.values()
        ),
        "blocker_counts": dict(sorted(blockers.items())),
        "episodes": episodes,
        "state": (
            "source_only_replay_complete"
            if episodes and not blockers
            else "source_only_replay_input_gap"
        ),
        "next_action": (
            "exact_state_policy_market_reconstruction"
            if blockers or not episodes
            else "review_source_only_economics_and_execution_evidence"
        ),
        "metric_role": "independent_exit_replay_diagnostic",
        "window_policy": "first_decision_per_clean_same_policy_episode",
        "sample_floor": "all_compared_arms_complete",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "exact_state_policy_frame_and_fill_contract",
        "forbidden_uses": "standalone_live_promotion|real_fill_quality|hard_safety_override",
    }


def replay_evidence_contract_errors(report: Any) -> list[str]:
    """Validate nested authority/identity, not just a source-only root label."""
    if (
        not isinstance(report, dict)
        or report.get("schema") != REPLAY_SCHEMA
        or not source_only_observation_valid(report, "source_only_paired_exit_replay")
    ):
        return ["avg_down_independent_replay_authority_or_schema_invalid"]
    episodes = report.get("episodes")
    if not isinstance(episodes, dict):
        return ["avg_down_independent_replay_episodes_invalid"]
    errors = []
    blockers: dict[str, int] = {}
    complete = 0
    for key, episode in episodes.items():
        if (
            not isinstance(episode, dict)
            or not source_only_observation_valid(
                episode, "source_only_paired_exit_replay"
            )
            or episode.get("runtime_authority_ready") is not False
        ):
            errors.append("avg_down_independent_replay_episode_authority_invalid")
            continue
        if episode.get("evidence_digest") != canonical_digest(
            {
                name: value
                for name, value in episode.items()
                if name != "evidence_digest"
            }
        ):
            errors.append("avg_down_independent_replay_episode_digest_invalid")
        if (
            episode.get("position_episode_id") != key
            or not episode.get("source_observation_id")
            or not episode.get("scale_in_decision_id")
        ):
            errors.append("avg_down_independent_replay_episode_identity_invalid")
        outcomes, gaps = episode.get("outcomes"), episode.get("blockers")
        if not isinstance(outcomes, dict) or not isinstance(gaps, dict):
            errors.append("avg_down_independent_replay_episode_shape_invalid")
            continue
        for reason in set(gaps.values()):
            blockers[reason] = blockers.get(reason, 0) + 1
        if episode.get("state") == "paired_exit_complete_source_only":
            complete += 1
            if gaps or "NO_ADD" not in outcomes or len(outcomes) < 2:
                errors.append("avg_down_independent_replay_completion_invalid")
        for outcome in outcomes.values():
            if (
                not isinstance(outcome, dict)
                or outcome.get("evidence_authority") != "source_only_paired_exit_replay"
                or outcome.get("evaluation_method") != METHOD
                or outcome.get("status") != "COMPLETED"
            ):
                errors.append("avg_down_independent_replay_outcome_authority_invalid")
    if (
        report.get("unique_episode_count") != len(episodes)
        or report.get("complete_episode_count") != complete
        or report.get("blocker_counts") != dict(sorted(blockers.items()))
    ):
        errors.append("avg_down_independent_replay_summary_mismatch")
    return sorted(set(errors))


def _modeled_incumbent_matches_receipt(actual, modeled):
    try:
        return bool(actual.get("actual_order_submitted") in (True, "True", "true")
            and actual.get("sell_execution_receipt_economics_complete") in (True, "True", "true")
            and actual.get("sell_execution_receipt_quantity_contract_complete") in (True, "True", "true")
            and str(actual.get("status") or "COMPLETED").upper() == "COMPLETED"
            and finite_number(actual.get("profit_rate")) is not None
            and finite_number(actual.get("sell_execution_cumulative_net_pnl_krw")) == modeled.get("net_pnl_krw")
            and finite_number(actual.get("position_weighted_sell_price") or actual.get("sell_price")) == modeled.get("exit_price")
            and finite_number(actual.get("sell_execution_cumulative_qty")) == modeled.get("exit_qty"))
    except (TypeError, ValueError, OverflowError):
        return False


def replay_policy_cohort_digest(snapshot):
    """Compare frozen decision rules/code, separately from dated input state.

    Exact snapshot/arm hashes still validate each episode. Custody files and
    publication receipts are inputs to those evaluations, not an exit rule
    revision. No current workspace rule is substituted for a historical one.
    """
    rules = {key: value for key, value in snapshot.get("rules", {}).items()
             if not key.endswith(("_POLICY_FILE", "_EXCLUDED_CODES_FILE"))}
    environment = {key: value for key, value in snapshot.get("environment", {}).items()
                   if not key.startswith(("KORSTOCKSCAN_AVG_DOWN_RUNTIME_", "KORSTOCKSCAN_SCALPING_PYRAMID_RUNTIME_")) and not key.endswith(("_POLICY_FILE", "_EXCLUDED_CODES_FILE"))}
    normalized_blobs = {digest: canonical_digest({key: value for key, value in values.items()
                        if not key.endswith(("_POLICY_FILE", "_EXCLUDED_CODES_FILE"))})
                        for digest, values in snapshot.get("rule_blobs", {}).items()}
    module_rules = {module: normalized_blobs.get(digest, "missing:" + digest)
                    for module, digest in snapshot.get("module_rules", {}).items()}
    return "paired-exit-cohort:" + canonical_digest({"implementation": snapshot.get("implementation"),
        "rules": rules, "module_rules": module_rules, "environment": environment})


def bind_report_paired_terminals(decisions, replay):
    """Bind modeled terminals in memory only; never grant the replay authority."""
    import copy
    from datetime import datetime
    from src.engine.trade_profit import calculate_net_realized_pnl

    from src.engine.lifecycle.avg_down_policy_replay import SNAPSHOT_SCHEMA, implementation_identity, snapshot_version
    current_implementation = implementation_identity()
    errors = replay_evidence_contract_errors(replay)
    result = copy.deepcopy(decisions)
    if errors:
        return result, errors
    for row in result:
        episode = replay["episodes"].get(row["position_episode_id"])
        if not episode or episode.get("state") != "paired_exit_complete_source_only":
            continue
        if (episode.get("source_observation_id") != row["source_event_id"]
                or episode.get("scale_in_decision_id") != row["scale_in_decision_id"]):
            continue
        outcomes = episode["outcomes"]
        source = row["independent_replay_input"]
        snapshot = source.get("policy_snapshot") or {}
        snapshot_valid = (snapshot.get("schema") == SNAPSHOT_SCHEMA
            and snapshot.get("implementation") == current_implementation
            and bool(snapshot.get("loaded_code"))
            and snapshot_version(snapshot) == source.get("exit_policy_version"))
        valid = snapshot_valid and source.get("replay_actual_entry_anchor_valid") in (True, "True", "true") and cost_rate_from_version(row.get("cost_policy_version")) == finite_number(source.get("cost_rate"))
        for arm, outcome in outcomes.items():
            legs = outcome.get("legs")
            if (not isinstance(legs, list) or not legs
                    or outcome.get("full_policy_evaluation") is not True
                    or not outcome.get("trace_digest")
                    or outcome.get("exit_policy_version") != source.get("exit_policy_version")
                    or outcome.get("evaluation_method") != METHOD):
                valid = False
                break
            try:
                qty = sum(int(leg["qty"]) for leg in legs)
                basis = round(sum(leg["price"] * leg["qty"] for leg in legs) / qty, 4)
                net = calculate_net_realized_pnl(basis, outcome["exit_price"], qty, cost_rate=source["cost_rate"])
                filled = int(outcome["filled_add_qty"])
                expected_qty = int(row["pre_add_buy_qty"]) + filled
                if (qty != expected_qty or qty != outcome["exit_qty"]
                        or net != outcome["net_pnl_krw"] or filled < 0
                        or (arm == "NO_ADD" and filled != 0)):
                    valid = False
            except (KeyError, ValueError, TypeError, OverflowError):
                valid = False
        ids = [value.get("terminal_source_event_id") for value in outcomes.values()]
        if not valid or not all(ids) or len(set(ids)) != len(ids):
            continue
        terminal = {
            "stage": "report_paired_lifecycle_terminal", "origin": "modeled_policy_delta",
            "evidence_authority": "source_only_paired_exit_replay",
            "source_observation_id": row["source_event_id"],
            "position_episode_id": row["position_episode_id"],
            "scale_in_decision_id": row["scale_in_decision_id"],
            "paired_exit_replay": copy.deepcopy(outcomes),
            "replay_evidence_digest": episode["evidence_digest"],
            "exit_policy_cohort": replay_policy_cohort_digest(source.get("policy_snapshot") or {}),
            "terminal_time": max(datetime.fromisoformat(value["exit_time"]) for value in outcomes.values()),
            "runtime_effect": False, "allowed_runtime_apply": False,
            "actual_order_submitted": False, "broker_order_forbidden": True,
            **{key: row[key] for key in ("stock_code", "venue", "policy_version",
                                      "sizing_policy_version", "cost_policy_version")},
        }
        row["actual_terminal"] = row.get("terminal")
        actual = (row.get("terminal") or {}).get("actual_receipt") or {}
        current_key = f"{row['effective_min_buy_pressure']:g}"
        modeled_current = outcomes.get(current_key, {})
        row["execution_quality_validated"] = _modeled_incumbent_matches_receipt(actual, modeled_current)
        fills = row.get("actual_add_receipts") or []
        if modeled_current.get("filled_add_qty", 0):
            virtual = modeled_current.get("add_fill_evidence") or {}
            unique = {(fill.get("order_no"), fill.get("execution_no")): fill for fill in fills}
            conflicts = any(canonical_digest(fill) != canonical_digest(unique[(fill.get("order_no"), fill.get("execution_no"))]) for fill in fills)
            row["execution_quality_validated"] = row["execution_quality_validated"] and len(unique) == 1 and not conflicts
            for fill in unique.values():
                try:
                    row["execution_quality_validated"] &= bool(
                        fill.get("order_no") not in (None, "", "-", "unknown") and fill.get("execution_no") not in (None, "", "-", "unknown")
                        and (not virtual.get("add_type") or fill.get("add_type") == virtual["add_type"])
                        and fill.get("position_episode_id") == row["position_episode_id"]
                        and finite_number(fill.get("fill_qty")) == modeled_current["filled_add_qty"]
                        and finite_number(fill.get("fill_price")) == finite_number(virtual.get("price"))
                        and fill.get("receipt_economics_complete") in (True, "True", "true")
                        and fill.get("receipt_quantity_contract_complete") in (True, "True", "true")
                        and finite_number(fill.get("remaining_qty")) == 0
                        and abs(_epoch(fill["emitted_at"]) - _epoch(virtual["filled_at"])) <= float(source.get("replay_max_frame_gap_sec") or 5))
                except (KeyError, ValueError, TypeError):
                    row["execution_quality_validated"] = False
        elif fills:
            row["execution_quality_validated"] = False

        spread = finite_number(episode.get("observed_max_spread_krw"))
        if spread is not None and spread >= 0:
            row["execution_stress_cost_krw"] = spread * max(value.get("filled_add_qty", 0) for value in outcomes.values())

        row["terminal"] = terminal
        row["outcome_state"] = "completed_modeled_paired_exit"
    first = {}
    for row in sorted(result, key=lambda value: value["decision_time"]):
        first.setdefault(row["position_episode_id"], row)
    coverage_ready = bool(first) and all(
        row.get("terminal", {}).get("stage") == "report_paired_lifecycle_terminal"
        and row["independent_replay_input"].get("replay_capture_state") == "armed_source_only"
        for row in first.values())
    for row in result:
        row["capture_coverage_validated"] = coverage_ready
    return result, []


def chronological_economic_selection(economics, *, current, sample_floor, minimum_ev):
    """Fix one calibration winner, then examine the latest source-day once.

    Successor guards fixed before holdout: no worse worst loss or peak capital,
    and positive delta after one observed spread of extra execution cost.
    Missing executable/model-validation facts never imply PASS.
    """
    days = sorted({row["source_date"] for item in economics for row in item.get("episode_economics", [])})
    proof = {"schema": "scale_in_chronological_economics_v1", "holdout_source_date": days[-1] if days else None,
             "calibration_source_dates": days[:-1], "winner_fixed_before_holdout": False,
             "guard_policy": "baseline_tail_capital_nonworsening_observed_spread_stress_v1",
             "passed": False, "blocker": "chronological_source_days_missing"}
    if len(days) < 2:
        return None, proof
    for item in economics:
        identities = [row["position_episode_id"] for row in item.get("episode_economics", [])]
        if len(identities) != len(set(identities)):
            proof["blocker"] = "duplicate_episode_in_comparison_universe"
            return None, proof
    holdout_day = days[-1]
    universes = [set(row["position_episode_id"] for row in item.get("episode_economics", [])) for item in economics]
    if not universes or any(universe != universes[0] for universe in universes):
        proof["blocker"] = "candidate_dependent_comparison_universe"
        return None, proof

    def summary(rows):
        n = len(rows)
        return {"count": n,
                "delta_net_krw": sum(row["candidate_minus_current_pnl_krw"] for row in rows),
                "delta_ev_pct": sum(100 * row["candidate_minus_current_pnl_krw"] / row["reference_notional"] for row in rows) / n if n else None,
                "candidate_ev_pct": sum(100 * row["candidate_incremental_pnl_krw"] / row["reference_notional"] for row in rows) / n if n else None,
                "behavior_change_count": sum(row["behavior_changed"] for row in rows)}

    choices = []
    for item in economics:
        rows = item.get("episode_economics", [])
        calibration = [row for row in rows if row["source_date"] < holdout_day
                       and row.get("terminal_source_date", holdout_day) < holdout_day]
        holdout = [row for row in rows if row["source_date"] == holdout_day]
        # Boundary-crossing labels are embargoed rather than backfilled.
        eligible = calibration + holdout
        c = summary(calibration)
        removal = (item["candidate_value"] > current
                   and any(row.get("current_should_add") is True and row.get("candidate_should_add") is False for row in calibration)
                   and all("current_should_add" in row and "candidate_should_add" in row
                           and not (row["candidate_should_add"] and not row["current_should_add"]) for row in calibration))
        absolute = 0.0 if removal else minimum_ev
        if (len(eligible) >= sample_floor and c["count"] and c["behavior_change_count"]
                and c["delta_net_krw"] > 0 and c["delta_ev_pct"] > 0
                and (c["candidate_ev_pct"] >= absolute if removal else c["candidate_ev_pct"] >= absolute and c["candidate_ev_pct"] > 0)):
            choices.append((item, calibration, holdout, c, removal))
    if not choices:
        proof["blocker"] = "calibration_sample_or_net_edge_missing"
        return None, proof
    winner, calibration, holdout, c, removal = max(choices, key=lambda v: (
        v[3]["delta_ev_pct"], v[3]["delta_net_krw"], -abs(v[0]["candidate_value"] - current), -v[0]["candidate_value"]))
    h = summary(holdout)
    all_rows = calibration + holdout
    proof.update({"candidate_value": winner["candidate_value"], "winner_fixed_before_holdout": True,
                  "calibration": c, "holdout": h, "comparison_universe_hash": canonical_digest(
                      sorted(row["position_episode_id"] for row in all_rows)),
                  "risk_reduction_only": removal})
    guards = {
        "holdout_delta_ev_positive": bool(h["count"] and h["delta_ev_pct"] > 0),
        "holdout_delta_net_positive": h["delta_net_krw"] > 0,
        "holdout_behavior_changed": h["behavior_change_count"] > 0,
        "holdout_absolute_edge": bool(h["count"] and (h["candidate_ev_pct"] >= 0 if removal else h["candidate_ev_pct"] >= minimum_ev and h["candidate_ev_pct"] > 0)),
        "tail_capital_guards_passed": all(
            isinstance(row.get("candidate_peak_exposure_krw"), (int, float))
            and isinstance(row.get("current_peak_exposure_krw"), (int, float))
            and row["candidate_peak_exposure_krw"] <= (finite_number(row.get("capital_limit_krw"))
                                                       or row["current_peak_exposure_krw"])
            for row in all_rows) and all(finite_number(row.get("candidate_total_pnl_krw")) is not None
                                        and finite_number(row.get("current_total_pnl_krw")) is not None for row in all_rows)
            and all(min(row["candidate_total_pnl_krw"] for row in partition) >= min(row["current_total_pnl_krw"] for row in partition)
                    for partition in (calibration, holdout)),
        "cost_stress_passed": all(isinstance(row.get("execution_stress_cost_krw"), (int, float))
                                   for row in all_rows) and all(
            sum(row["candidate_minus_current_pnl_krw"] - row.get("execution_stress_cost_krw", float("inf")) for row in partition) > 0
            for partition in (calibration, holdout)) and all(
                sum((row["candidate_minus_current_pnl_krw"] - row["execution_stress_cost_krw"]) / row["reference_notional"] for row in partition) > 0
                for partition in (calibration, holdout)),
        "venue_scope_holdout_passed": all(
            (scope := [row for row in holdout if row["venue"] == venue])
            and sum(row["candidate_minus_current_pnl_krw"] for row in scope) > 0
            and sum(row["candidate_minus_current_pnl_krw"] / row["reference_notional"] for row in scope) > 0
            for venue in {"KRX", "NXT"}),
        "execution_quality_guard_passed": all(row.get("execution_quality_validated") is True for row in all_rows),
        "capture_coverage_guard_passed": all(row.get("capture_coverage_validated") is True for row in all_rows),
        "frozen_policy_cohort_passed": len({row.get("paired_exit_policy_version") for row in all_rows}) == 1
            and all(row.get("paired_exit_policy_version") for row in all_rows),
    }
    proof["guards"] = guards
    proof["passed"] = all(guards.values())
    proof["blocker"] = next((key for key, value in guards.items() if not value), "")
    return (winner if proof["passed"] else None), proof


def economic_candidate_contract_errors(candidate):
    """Cheap deterministic handoff check, shared by Daily and direct PREOPEN."""
    family = candidate.get("family")
    if family not in {"scalping_pyramid_quality_gate", "scalping_avg_down_recovery_quality_gate"}:
        return []
    if candidate.get("allowed_runtime_apply") is not True:
        return []
    expected_version = "pyramid_paired_economics_v2" if family == "scalping_pyramid_quality_gate" else "avg_down_paired_economics_v3"
    if candidate.get("evidence_contract_version") != expected_version:
        return ["scale_in_economic_evidence_contract_version_invalid"]
    if family == "scalping_pyramid_quality_gate":
        if (candidate.get("target_env_keys") != ["SCALPING_PYRAMID_MIN_PROFIT_PCT"]
                or candidate.get("changed_target_env_keys") != ["SCALPING_PYRAMID_MIN_PROFIT_PCT"]
                or type(candidate.get("current_value")) not in (int, float)
                or type(candidate.get("recommended_value")) not in (int, float)
                or finite_number(candidate.get("current_value")) is None
                or finite_number(candidate.get("recommended_value")) is None
                or not 0.2 <= candidate["recommended_value"] <= 2.5
                or abs(candidate["recommended_value"] - candidate["current_value"]) > 0.100000001
                or candidate.get("current_values", {}).get("min_profit_pct") != candidate["current_value"]
                or candidate.get("recommended_values", {}).get("min_profit_pct") != candidate["recommended_value"]
                or any(value != candidate.get("current_values", {}).get(key) for key, value in candidate.get("recommended_values", {}).items() if key != "min_profit_pct")):
            return ["pyramid_single_profit_axis_or_step_contract_invalid"]
    proof = candidate.get("economic_validation")
    if not isinstance(proof, dict):
        return ["scale_in_chronological_economic_evidence_missing"]
    metrics = candidate.get("source_metrics")
    economics = metrics.get("paired_runtime_candidate_economics") if isinstance(metrics, dict) else None
    if (not isinstance(economics, list) or not economics
            or any(not isinstance(item, dict) or not isinstance(item.get("episode_economics"), list)
                   or any(not isinstance(row, dict) for row in item["episode_economics"])
                   for item in economics)):
        return ["scale_in_paired_episode_economics_missing"]
    try:
        winner, recomputed = chronological_economic_selection(economics,
            current=float(candidate["current_value"]),
            sample_floor=20 if family == "scalping_pyramid_quality_gate" else 10,
            minimum_ev=0.0 if family == "scalping_pyramid_quality_gate" else 0.1)
        if (winner is None or recomputed != proof
                or winner["candidate_value"] != candidate.get("recommended_value")
                or proof["holdout_source_date"] > candidate["source_date"]):
            return ["scale_in_chronological_economic_evidence_invalid"]
    except (ValueError, TypeError, KeyError, ZeroDivisionError):
        return ["scale_in_chronological_economic_evidence_invalid"]
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    try:
        if candidate.get("apply_date") != _next_krx_trading_day(candidate["source_date"]):
            return ["scale_in_next_trading_date_contract_invalid"]
    except (TypeError, KeyError, ValueError):
        return ["scale_in_next_trading_date_contract_invalid"]
    return []


def economic_report_contract_errors(payload):
    """A ready arithmetic proof must also bind its independent arm evidence."""
    ready = []
    for row in payload.get("calibration_candidates", []):
        if (not isinstance(row, dict) or row.get("allowed_runtime_apply") is not True
                or row.get("family") not in {"scalping_pyramid_quality_gate", "scalping_avg_down_recovery_quality_gate"}):
            continue
        proof = row.get("economic_validation")
        if not isinstance(proof, dict):
            return ["scale_in_chronological_economic_evidence_missing"]
        if proof.get("passed") is not True:
            return ["scale_in_chronological_economic_evidence_invalid"]
        ready.append(row)
    if not ready:
        return []
    replay = payload.get("independent_exit_replay")
    errors = replay_evidence_contract_errors(replay)
    if errors:
        return errors
    try:
        for candidate in ready:
            for item in candidate["source_metrics"]["paired_runtime_candidate_economics"]:
                for row in item["episode_economics"]:
                    episode = replay["episodes"][row["position_episode_id"]]
                    outcomes = episode["outcomes"]
                    arms = ("NO_ADD", f"{candidate['current_value']:g}", f"{item['candidate_value']:g}")
                    control, current, challenger = (outcomes[arm] for arm in arms)
                    if any(outcome.get("full_policy_evaluation") is not True
                           or not outcome.get("trace_digest")
                           or outcome.get("exit_policy_version") != episode["exit_policy_version"]
                           for outcome in (control, current, challenger)):
                        return ["scale_in_paired_economic_arm_binding_invalid"]
                    reference = sum(leg["price"] * leg["qty"] for leg in control["legs"])
                    if finite_number(reference) is None or reference <= 0 or control["filled_add_qty"] != 0:
                        return ["scale_in_paired_economic_arm_binding_invalid"]
                    def behavior(outcome):
                        return canonical_digest({key: outcome.get(key) for key in
                            ("filled_add_qty", "exit_qty", "exit_price", "exit_time", "peak_add_reserved_notional_krw")})
                    expected = {
                        "source_date": episode["replay_source_date"],
                        "terminal_source_date": max(str(value["exit_time"])[:10] for value in outcomes.values()),
                        "reference_notional": reference,
                        "no_add_total_pnl_krw": control["net_pnl_krw"],
                        "current_total_pnl_krw": current["net_pnl_krw"],
                        "candidate_total_pnl_krw": challenger["net_pnl_krw"],
                        "current_incremental_pnl_krw": current["net_pnl_krw"] - control["net_pnl_krw"],
                        "candidate_incremental_pnl_krw": challenger["net_pnl_krw"] - control["net_pnl_krw"],
                        "current_peak_exposure_krw": reference + current["peak_add_reserved_notional_krw"],
                        "candidate_peak_exposure_krw": reference + challenger["peak_add_reserved_notional_krw"],
                        "current_capital_occupancy_krw_seconds": current["add_capital_occupancy_krw_seconds"],
                        "candidate_capital_occupancy_krw_seconds": challenger["add_capital_occupancy_krw_seconds"],
                        "current_behavior_signature": behavior(current),
                        "candidate_behavior_signature": behavior(challenger),
                        "behavior_changed": behavior(current) != behavior(challenger),
                        "current_should_add": current["filled_add_qty"] > 0,
                        "candidate_should_add": challenger["filled_add_qty"] > 0,
                        "current_exit_price": current["exit_price"],
                        "candidate_exit_price": challenger["exit_price"],
                        "no_add_exit_price": control["exit_price"],
                        "exact_episode_exit_policy_version": episode["exit_policy_version"],
                    }
                    spread = finite_number(episode.get("observed_max_spread_krw"))
                    if spread is None or spread < 0:
                        return ["scale_in_paired_economic_arm_binding_invalid"]
                    expected["execution_stress_cost_krw"] = spread * max(value["filled_add_qty"] for value in outcomes.values())
                    if (row.get("origin") != "modeled_policy_delta"
                            or episode["scale_in_decision_id"] != row["scale_in_decision_id"]
                            or any(row.get(key) != value for key, value in expected.items())
                            or set(row["paired_terminal_source_event_ids"]) != {outcomes[arm]["terminal_source_event_id"] for arm in arms}
                            or row["candidate_minus_current_pnl_krw"] != outcomes[arms[2]]["net_pnl_krw"] - outcomes[arms[1]]["net_pnl_krw"]):
                        return ["scale_in_paired_economic_arm_binding_invalid"]
    except (KeyError, TypeError, ValueError):
        return ["scale_in_paired_economic_arm_binding_invalid"]
    return []


def actual_policy_outcomes(decisions):
    """Actual receipt ledger, separate from modeled policy deltas and history."""
    outcomes, seen = [], set()
    for row in decisions:
        terminal = row.get("actual_terminal") or row.get("terminal") or {}
        receipt = terminal.get("actual_receipt") or {}
        identity = row["position_episode_id"]
        if identity in seen:
            continue
        if (receipt.get("scale_in_applied_source_observation_id") != row["source_event_id"]
                or receipt.get("scale_in_applied_decision_id") != row["scale_in_decision_id"]
                or receipt.get("scale_in_applied_quality_update_id") != row.get("runtime_candidate_quality_update_id")
                or receipt.get("scale_in_applied_evidence_digest") != row.get("runtime_candidate_evidence_digest")
                or receipt.get("scale_in_applied_lineage_conflict") in (True, "True", "true")
                or row.get("runtime_candidate_selected") is not True
                or row.get("runtime_pid_value_verified") is not True
                or not row.get("runtime_candidate_quality_update_id")
                or len(str(row.get("runtime_candidate_evidence_digest") or "")) != 64
                or receipt.get("actual_order_submitted") not in (True, "True", "true")
                or receipt.get("sell_execution_receipt_economics_complete") not in (True, "True", "true")
                or receipt.get("sell_execution_receipt_quantity_contract_complete") not in (True, "True", "true")
                or row.get("venue") not in {"KRX", "NXT"}
                or row.get("session") in (None, "", "unknown")):
            continue
        pnl = finite_number(receipt.get("sell_execution_cumulative_net_pnl_krw"))
        profit = finite_number(receipt.get("profit_rate"))
        qty = finite_number(receipt.get("sell_execution_cumulative_qty"))
        if (pnl is None or profit is None or qty is None or qty <= 0 or not qty.is_integer()
                or cost_rate_from_version(row.get("cost_policy_version")) is None):
            continue
        seen.add(identity)
        outcomes.append({"origin": "actual_policy_outcome", "status": "COMPLETED",
            "position_episode_id": identity, "scale_in_decision_id": row["scale_in_decision_id"],
            "quality_update_id": row["runtime_candidate_quality_update_id"],
            "evidence_digest": row["runtime_candidate_evidence_digest"],
            "stock_code": row["stock_code"], "venue": row["venue"], "session": row["session"],
            "cost_policy_version": row["cost_policy_version"], "quantity": int(qty),
            "net_pnl_krw": pnl, "profit_rate": profit,
            "new_incremental_profit_claimed": False})
    return outcomes
