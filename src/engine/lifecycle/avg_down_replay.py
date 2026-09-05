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
    """Freeze fixed policy inputs; the independently versioned tunable is excluded."""
    source = (
        rules
        if isinstance(rules, Mapping)
        else vars(rules) if rules is not None else {}
    )
    values = {
        str(key): value
        for key, value in source.items()
        if str(key).startswith(
            (
                "SCALP",
                "SHALLOW_",
                "DEEP_",
                "REVERSAL_",
                "AGGRESSIVE_",
                "AVG_DOWN",
                "HOLDING_",
                "LIFECYCLE_",
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
        route_replay = observation["route_replay"]
        if not isinstance(route_replay, dict) or not route_replay:
            raise ValueError("route_replay_missing")
        if "NO_ADD" in route_replay:
            raise ValueError("reserved_no_add_arm_in_route_replay")
        current_key = f"{_positive(observation.get('effective_min_buy_pressure')):g}"
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
        for key, arm in {
            **route_replay,
            "NO_ADD": {"should_add": False, "route_evaluation_complete": True},
        }.items():
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
                state["min_buy_pressure"] = None if key == "NO_ADD" else _positive(key)
                state["no_add_control"] = key == "NO_ADD"
                state["source_observation_id"] = observation["source_event_id"]
                trace = []
                completed = False
                for frame in checked_frames:
                    # A fill/cancel model is part of the evidence contract,
                    # never an assumption that an unfilled order stays open forever.
                    pending = state["pending_add"]
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
                        not in {"HOLD", "EXIT", "ADD", "CANCEL_ADD"}
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
                    total_pnl = sum(
                        calculate_net_realized_pnl(
                            leg["price"], bid, leg["qty"], cost_rate=cost_rate
                        )
                        for leg in state["legs"]
                    )
                    result["outcomes"][key] = {
                        "status": "COMPLETED",
                        "exit_price": bid,
                        "exit_qty": state["qty"],
                        "filled_add_qty": state["filled_add_qty"],
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
        control = result["outcomes"]["NO_ADD"]["net_pnl_krw"]
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
