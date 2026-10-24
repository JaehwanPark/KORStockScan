"""Causal stop-confirmation comparison. No synthetic AI, fills or broker calls."""

from dataclasses import asdict, replace
from collections import Counter, OrderedDict
from contextlib import contextmanager
import math
from .main_stop_policy import (
    StopValues,
    soft_decision,
    safety_decision,
    protect_confirmed,
    append_sample,
    digest,
    finite,
    TUNABLE,
)
from .holding_vote_exit_models import cost_known_epoch

SCHEMA = "main_stop_research_v1"
EVALUATION_SCHEMA = "main_stop_evaluation_source_v1"
_LANE_SCOPE_FIELDS = (
    "evaluation_lane_scope",
    "source_lifecycle_epoch",
    "source_runtime_pid",
    "source_runtime_incarnation",
)


def _evaluation_lane_scope(value):
    # Epoch alone existed before evaluator lanes. Preserve that legacy branch;
    # any new lane/runtime marker requires the complete new typed contract.
    markers = (
        "evaluation_lane_scope",
        "evaluation_lane_generation",
        "evaluation_lane_generations",
        "source_runtime_pid",
        "source_runtime_incarnation",
    )
    if not any(key in value for key in markers):
        return None
    if (
        value.get("evaluation_lane_scope") != "native_evaluator_lifecycle_v1"
        or any(
            type(value.get(k)) is not int or value[k] <= 0
            for k in ("source_lifecycle_epoch", "source_runtime_pid")
        )
        or not isinstance(value.get("source_runtime_incarnation"), str)
        or len(value["source_runtime_incarnation"]) != 32
        or any(c not in "0123456789abcdef" for c in value["source_runtime_incarnation"])
    ):
        raise ValueError("native_evaluation_lane_scope_invalid")
    return tuple(value[key] for key in _LANE_SCOPE_FIELDS)


class _RetainedSource(dict):
    """Keep the shared admission alive for detached immutable endpoint data."""

    def __init__(self, value):
        from src.engine.lifecycle.research_input_budget import Claim
        import json

        self._claim = Claim(len(json.dumps(value, allow_nan=False).encode()) * 8)
        super().__init__(value)

    def __copy__(self):
        return type(self)(self)

    def __deepcopy__(self, memo):
        from copy import deepcopy

        result = type(self)(deepcopy(dict(self), memo))
        memo[id(self)] = result
        return result


def evaluation_binding(value, quote, *, preset_predecessor=None, preset_quote=None):
    """Bind an actual native evaluator to its unchanged shared quote receipt."""
    if (
        not _sealed(value)
        or value.get("schema") != EVALUATION_SCHEMA
        or not _sealed(quote)
        or quote.get("schema") != "main_stop_source_v1"
        or quote.get("owner") != "main"
        or value.get("decision_owner") != "main_scalping"
        or value.get("stage") not in {"preset_safety", "common_soft"}
        or value.get("rule_scope") != [value.get("stage")]
        or value.get("priority_status") not in {"reached", "blocked_legacy"}
        or value.get("quote_source_sha256") != quote.get("source_sha256")
        or value.get("evaluator") not in {"normal", "fast"}
        or type(value.get("evaluation_generation")) is not int
        or value["evaluation_generation"] <= 0
        or type(value.get("source_observation_generation")) is not int
        or value["source_observation_generation"]
        <= quote.get("source_observation_generation", 0)
        or value.get("decision_price_observation") != "native_gate_argument"
        or value.get("independently_verified_mark_clock") is not False
        or any(
            value.get(k) is not False
            for k in (
                "runtime_effect",
                "allowed_runtime_apply",
                "actual_order_submitted",
            )
        )
        or type(value.get("legacy_broker_recovered")) is not bool
        or any(
            type(value.get(k)) is not int or value[k] < 0
            for k in ("capture_rejected_count", "evaluation_rejected_count")
        )
        or not all(
            finite(value.get(k))
            for k in (
                "at",
                "quote_observation_at",
                "quote_max_age_sec",
                "decision_price",
                "decision_profit_pct",
            )
        )
        or value["decision_price"] <= 0
        or value["at"] <= 0
        or value["quote_max_age_sec"] <= 0
        or value.get("quote_binding_status") not in {"supported", "source_gap"}
        or value.get("quote_validated_at") != value["at"]
        or value["quote_observation_at"] != quote.get("at")
        or value["at"] < quote["at"]
        or value.get("decision_price_basis") not in {"mark_price", "executable_bid"}
        or (
            value["decision_price_basis"] == "executable_bid"
            and value["decision_price"] != quote.get("bid")
        )
        or value.get("source_stop_values") != quote.get("source_stop_values")
        or value.get("parent_values_sha256") != quote.get("parent_values_sha256")
    ):
        raise ValueError("native_evaluation_receipt_unbound")
    if value["quote_binding_status"] == "supported" and (
        not quote_supported(quote)
        or not finite(value.get("quote_at"))
        or not 0 <= value["at"] - value["quote_at"] <= value["quote_max_age_sec"]
    ):
        raise ValueError("native_evaluation_quote_support_invalid")
    for key in (
        "position_key",
        "record_id",
        "pin_sha256",
        "role",
        "market",
        "quote_at",
        "item",
        "route",
        "transport_epoch",
        "quantity",
        "buy_basis_krw",
    ):
        if type(value.get(key)) is not type(quote.get(key)) or value.get(
            key
        ) != quote.get(key):
            raise ValueError("native_evaluation_identity_or_clock_changed")
    anchor = dict(
        position_key=value["position_key"],
        pin_sha256=value["pin_sha256"],
        evaluator=value["evaluator"],
        stage=value["stage"],
        at=value["at"],
        generation=value["evaluation_generation"],
    )
    if value.get("evaluation_id") != digest(anchor):
        raise ValueError("native_evaluation_generation_unbound")
    lane_scope = _evaluation_lane_scope(value)
    if lane_scope != _evaluation_lane_scope(quote):
        raise ValueError("native_evaluation_quote_scope_unbound")
    if lane_scope is not None:
        lanes = value.get("evaluation_lane_generations")
        if (
            type(lanes) is not dict
            or set(lanes) != {"normal", "fast"}
            or any(type(v) is not int or v < 0 for v in lanes.values())
            or type(value.get("evaluation_lane_generation")) is not int
            or value["evaluation_lane_generation"] <= 0
            or lanes[value["evaluator"]] != value["evaluation_lane_generation"]
            or sum(lanes.values()) != value["evaluation_generation"]
        ):
            raise ValueError("native_evaluation_lane_generation_unbound")
    if value["stage"] == "preset_safety" and (
        not isinstance(value.get("decision_inputs"), dict)
        or type(value["decision_inputs"].get("handoff_enabled")) is not bool
    ):
        raise ValueError("native_preset_decision_inputs_missing")
    if value["stage"] == "common_soft":
        if value["evaluator"] != "normal" or value["priority_status"] != "reached":
            raise ValueError("common_soft_native_owner_unproven")
        inputs = value.get("decision_inputs")
        if (
            not isinstance(inputs, dict)
            or any(
                type(inputs.get(k)) is not bool
                for k in (
                    "grace_enabled",
                    "after_add",
                    "handoff_enabled",
                    "holding_ai_required",
                    "protect_enabled",
                )
            )
            or not finite(inputs.get("vote_max_worsen_pct"))
        ):
            raise ValueError("native_soft_decision_inputs_missing")
        vote_source = inputs.get("holding_vote_source")
        if inputs["holding_ai_required"] and isinstance(vote_source, dict):
            quantity = value.get("quantity_source") or {}
            # Metadata mismatch may reject early; metadata equality grants no
            # quantity authority. Replay and the source census still validate
            # the full proof once before admitting a supported decision.
            if isinstance(quantity, dict) and quantity.get("status") in {
                "full_fill",
                "settled_partial",
            }:
                reason = vote_quantity_identity_error(
                    vote_source,
                    record_id=quote.get("record_id"),
                    buy_fill_identity=quantity.get("buy_fill_identity"),
                )
                if reason:
                    raise ValueError(reason)
        if (
            value["role"] == "SCALP_PRESET_TP"
            or lane_scope is not None
            and value.get("preset_predecessor") is not None
        ) and not value["legacy_broker_recovered"]:
            reference = value.get("preset_predecessor")
            predecessor = preset_predecessor
            if (
                not isinstance(reference, dict)
                or reference.get("schema") != "main_stop_evaluation_reference_v1"
                or not isinstance(predecessor, dict)
                or predecessor.get("stage") != "preset_safety"
                or any(
                    reference.get(k) != predecessor.get(k)
                    for k in (
                        "evaluation_id",
                        "source_sha256",
                        "at",
                        "evaluator",
                        "stage",
                        "position_key",
                        "pin_sha256",
                    )
                )
            ):
                raise ValueError("normal_preset_predecessor_unbound")
            if lane_scope is not None and (
                _evaluation_lane_scope(predecessor) != lane_scope
                or predecessor.get("evaluation_lane_generation", 0) + 1
                != value["evaluation_lane_generation"]
            ):
                raise ValueError("normal_preset_lane_predecessor_unbound")
            evaluation_binding(predecessor, preset_quote)
            if (
                predecessor["stage"] != "preset_safety"
                or predecessor["evaluator"] != "normal"
                or predecessor["priority_status"] != "reached"
                or predecessor["legacy_broker_recovered"]
                or predecessor["at"] != value["at"]
                or any(
                    predecessor[k] != value[k]
                    for k in (
                        "position_key",
                        "pin_sha256",
                        "role",
                        "market",
                        "quantity",
                        "buy_basis_krw",
                    )
                )
                or predecessor["evaluation_generation"]
                >= value["evaluation_generation"]
            ):
                raise ValueError("normal_preset_predecessor_unbound")
    return value


def vote_quantity_identity_error(vote_source, *, record_id, buy_fill_identity):
    """Bind native record-key AI evidence to the independently proven BUY set.

    Stop position cycles and AI record keys intentionally use different key
    schemes. Legacy holdings without an explicit record cannot be translated.
    """
    from src.engine.ai.holding_vote_replay_source import SCHEMA as VOTE_SCHEMA

    if (
        vote_source.get("schema") != VOTE_SCHEMA
        or vote_source.get("path_id") != "EXIT_SOFT_STOP"
    ):
        return "holding_vote_native_path_mismatch"
    if (
        type(record_id) not in (int, str)
        or not str(record_id).strip()
        or str(record_id).strip() in {"-", "0"}
    ):
        return "holding_vote_record_binding_unproven"
    if vote_source.get("position_key") != "record:" + str(record_id).strip():
        return "holding_vote_record_generation_mismatch"
    if (
        not buy_fill_identity
        or vote_source.get("buy_fill_identity") != buy_fill_identity
    ):
        return "holding_vote_buy_generation_mismatch"
    return None


def quantity_support(receipt, quote, *, at=None):
    from .main_stop_quantity_source import validate_quantity_source
    from .main_stop_runtime_source import resolve_quantity_source

    at = quote["at"] if at is None else at
    if not isinstance(receipt, dict):
        return "unknown", "quantity_terminal_source_missing"
    try:
        receipt = resolve_quantity_source(receipt, quote, at=at)
    except (ValueError, KeyError, TypeError):
        return "unknown", "quantity_source_reference_unbound"
    if not validate_quantity_source(
        receipt,
        position_key=quote["position_key"],
        at=at,
        quantity=quote["quantity"],
        buy_basis_krw=quote["buy_basis_krw"],
    ):
        return "unknown", str(
            receipt.get("reason") or "quantity_terminal_source_unverified"
        )
    return receipt["status"], None


def initial_quantity_prefix_no_exit(quote, evaluation, threshold):
    """An unknown quantity may be excluded only with an actual common no-exit gate."""
    receipt = evaluation.get("quantity_source")
    inputs = evaluation["decision_inputs"]
    return bool(
        _sealed(receipt)
        and receipt.get("schema") == "main_stop_quantity_source_v1"
        and receipt.get("status") == "unknown"
        and all(
            receipt.get(k) == quote.get(k)
            for k in ("position_key", "quantity", "buy_basis_krw")
        )
        and all(finite(receipt.get(k)) for k in ("known_at", "captured_at"))
        and 0 < receipt["known_at"] <= receipt["captured_at"] <= evaluation["at"]
        and receipt.get("allowed_runtime_apply") is False
        and receipt.get("actual_order_submitted") is False
        and common_no_exit_prefix(quote, evaluation, threshold)
    )


def common_no_exit_prefix(quote, evaluation, threshold):
    inputs = evaluation["decision_inputs"]
    return bool(
        evaluation["decision_profit_pct"] > threshold
        and not quote.get("add_count")
        and not (finite(quote.get("protect_line")) and quote["protect_line"] > 0)
        and "soft_stop_micro_grace_started_at" in inputs
        and inputs["soft_stop_micro_grace_started_at"] is None
        and inputs["after_add"] is False
        and quote.get("automatic_management_allowed") is True
        and quote.get("manual") is False
        and quote.get("pending_exit") is False
        and quote.get("pending_add") is False
    )


def quote_supported(value):
    return bool(
        value.get("coverage_complete") is True
        and value.get("owner") == "main"
        and value.get("item")
        and value.get("route")
        and value.get("transport_epoch")
        and all(finite(value.get(k)) for k in ("at", "quote_at", "bid", "bid_qty"))
        and value["bid"] > 0
        and value["bid_qty"] >= 0
        and 0 <= value["at"] - value["quote_at"] <= 3
    )


@contextmanager
def bound_evaluations(rows):
    """Join tiny native decisions to bounded recent quotes, never infer a call."""
    from src.engine.lifecycle.research_input_budget import Claim

    quotes = OrderedDict()
    claims = {}
    first_claim = None
    preset_claim = None
    supported_claim = None
    unsupported_pending = set()
    global_pending = {}
    state = dict(
        first_quote=None,
        last_quote=None,
        quote_count=0,
        evaluation_count=0,
        common_soft_count=0,
        unsupported=Counter(),
        coverage_generation=0,
        previous_quote_at=None,
        previous_quote_identity=None,
        bridge_unsupported=False,
        preset_predecessor=None,
        preset_quote=None,
        coverage_discontinuity=False,
        previous_evaluation_generation=0,
        evaluation_order_mode=None,
        evaluation_lane_scope=None,
        evaluation_scope_broken=False,
        evaluation_lane_previous={"normal": 0, "fast": 0},
        evaluation_global_prefix=0,
        evaluation_global_counts={"normal": 0, "fast": 0},
        evaluation_global_required=0,
    )

    def admit_lane(value):
        if state["evaluation_scope_broken"]:
            return "native_evaluation_scope_mixed"
        scope = _evaluation_lane_scope(value)
        mode = "lane" if scope is not None else "legacy"
        if state["evaluation_order_mode"] not in (None, mode):
            state["evaluation_scope_broken"] = True
            return "native_evaluation_scope_mixed"
        state["evaluation_order_mode"] = mode
        if scope is None:
            return None
        if state["evaluation_lane_scope"] not in (None, scope):
            state["evaluation_scope_broken"] = True
            return "native_evaluation_runtime_scope_changed"
        state["evaluation_lane_scope"] = scope
        evaluator = value["evaluator"]
        generation = value["evaluation_generation"]
        if (
            generation <= state["evaluation_global_prefix"]
            or generation in global_pending
        ):
            return "native_evaluation_global_generation_duplicate"
        if (
            value["evaluation_lane_generation"]
            <= state["evaluation_lane_previous"][evaluator]
        ):
            return "native_evaluation_lane_generation_duplicate"
        if (
            value["evaluation_lane_generation"]
            != state["evaluation_lane_previous"][evaluator] + 1
        ):
            return "native_evaluation_lane_generation_missing"
        # Only displaced observations remain resident. Normal in-order rows
        # release their admission immediately; overflow requests a partition.
        claim = Claim(1024)
        global_pending[generation] = (
            evaluator,
            dict(value["evaluation_lane_generations"]),
            claim,
        )
        state["evaluation_lane_previous"][evaluator] = value[
            "evaluation_lane_generation"
        ]
        state["evaluation_global_required"] = max(
            state["evaluation_global_required"], generation
        )
        while state["evaluation_global_prefix"] + 1 in global_pending:
            next_generation = state["evaluation_global_prefix"] + 1
            owner, counts, held = global_pending.pop(next_generation)
            held.close()
            expected = dict(state["evaluation_global_counts"])
            expected[owner] += 1
            if counts != expected:
                return "native_evaluation_lane_vector_conflict"
            state["evaluation_global_counts"] = counts
            state["evaluation_global_prefix"] = next_generation
        return None

    def pin_supported(quote):
        nonlocal supported_claim
        if supported_claim is None:
            supported_claim = Claim(
                len(__import__("json").dumps(quote, allow_nan=False).encode()) * 8
            )
            state["first_supported_quote"] = quote

    state["pin_supported_quote"] = pin_supported

    def stream():
        nonlocal first_claim, preset_claim
        for value in rows:
            if not isinstance(value, dict):
                yield dict(
                    schema="main_stop_contract_gap", reason="stop_source_row_invalid"
                ), None
                continue
            schema = value.get("schema")
            if schema == "main_stop_source_v1":
                if unsupported_pending:
                    yield dict(
                        schema="main_stop_contract_gap",
                        reason="unsupported_quote_without_actual_decision",
                    ), None
                    unsupported_pending.clear()
                state["quote_count"] += 1
                at = value.get("at")
                previous = state["previous_quote_at"]
                if (
                    finite(at)
                    and finite(previous)
                    and (at < previous or at - previous > 1.5)
                ):
                    state["coverage_generation"] += 1
                    state["coverage_discontinuity"] = True
                state["previous_quote_at"] = at
                identity = tuple(
                    value.get(k)
                    for k in (
                        "position_key",
                        "pin_sha256",
                        "quantity",
                        "buy_basis_krw",
                        "item",
                        "route",
                        "transport_epoch",
                        "capture_rejected_count",
                    )
                )
                if state["previous_quote_identity"] not in (None, identity):
                    state["coverage_generation"] += 1
                state["previous_quote_identity"] = identity
                if (
                    value.get("manual")
                    or value.get("pending_add")
                    or value.get("pending_exit")
                    or value.get("add_count")
                    or value.get("other_exit")
                    or (finite(value.get("protect_line")) and value["protect_line"] > 0)
                    or value.get("automatic_management_allowed") is not True
                ):
                    state["bridge_unsupported"] = True
                sha = value.get("source_sha256")
                if not _sealed(value) or not finite(at):
                    state["unsupported"]["quote_source_invalid"] += 1
                    yield dict(
                        schema="main_stop_contract_gap", reason="quote_source_invalid"
                    ), None
                    continue
                if value.get("native_decision_required") is True:
                    generation = value.get("quote_generation")
                    observation = value.get("source_observation_generation")
                    if (
                        type(generation) is not int
                        or generation <= 0
                        or type(observation) is not int
                        or observation <= 0
                        or value.get("quote_id")
                        != digest(
                            dict(
                                position_key=value.get("position_key"),
                                pin_sha256=value.get("pin_sha256"),
                                at=at,
                                generation=generation,
                            )
                        )
                    ):
                        yield dict(
                            schema="main_stop_contract_gap",
                            reason="native_quote_generation_unbound",
                        ), None
                        continue
                raw = __import__("json").dumps(value, allow_nan=False).encode()
                if len(raw) > 65536:
                    raise ValueError("stop_quote_join_partition_required")
                if state["first_quote"] is None:
                    first_claim = Claim(len(raw) * 8)
                    state["first_quote"] = value
                state["last_quote"] = value
                if sha not in quotes:
                    if len(quotes) >= 4:
                        old, _ = quotes.popitem(last=False)
                        claims.pop(old).close()
                    claims[sha] = Claim(len(raw) * 8)
                    quotes[sha] = value
                if not quote_supported(value):
                    unsupported_pending.add(sha)
                continue
            if schema == EVALUATION_SCHEMA:
                state["evaluation_count"] += 1
                quote = quotes.get(value.get("quote_source_sha256"))
                try:
                    evaluation_binding(
                        value,
                        quote,
                        preset_predecessor=state["preset_predecessor"],
                        preset_quote=state["preset_quote"],
                    )
                except (ValueError, TypeError, KeyError) as exc:
                    state["unsupported"][str(exc)] += 1
                    yield dict(schema="main_stop_contract_gap", reason=str(exc)), None
                    continue
                lane_reason = admit_lane(value)
                if lane_reason:
                    yield dict(
                        schema="main_stop_contract_gap", reason=lane_reason
                    ), None
                    continue
                if state["evaluation_order_mode"] == "legacy":
                    if (
                        value["evaluation_generation"]
                        != state["previous_evaluation_generation"] + 1
                    ):
                        yield dict(
                            schema="main_stop_contract_gap",
                            reason="native_evaluation_generation_missing",
                        ), None
                        state["previous_evaluation_generation"] = value[
                            "evaluation_generation"
                        ]
                        continue
                    state["previous_evaluation_generation"] = value[
                        "evaluation_generation"
                    ]
                if value["stage"] == "common_soft":
                    state["common_soft_count"] += 1
                unsupported_pending.discard(value.get("quote_source_sha256"))
                if value["stage"] == "preset_safety" and value["evaluator"] == "normal":
                    if preset_claim is not None:
                        preset_claim.close()
                    preset_claim = Claim(
                        len(
                            __import__("json")
                            .dumps([value, quote], allow_nan=False)
                            .encode()
                        )
                        * 8
                    )
                    state["preset_predecessor"] = value
                    state["preset_quote"] = quote
                yield quote, value
                continue
            if schema not in {
                "main_stop_handoff_source_v1",
                "main_stop_release_source_v1",
            }:
                yield dict(
                    schema="main_stop_contract_gap",
                    reason="native_source_schema_invalid",
                ), None
            else:
                yield value, None
        if unsupported_pending:
            yield dict(
                schema="main_stop_contract_gap",
                reason="unsupported_quote_without_actual_decision",
            ), None
        if global_pending:
            yield dict(
                schema="main_stop_contract_gap",
                reason="native_evaluation_global_generation_missing",
            ), None

    try:
        yield stream(), state
    finally:
        for claim in claims.values():
            claim.close()
        if first_claim is not None:
            first_claim.close()
        if preset_claim is not None:
            preset_claim.close()
        if supported_claim is not None:
            supported_claim.close()
        for _, _, claim in global_pending.values():
            claim.close()
        global_pending.clear()
        state.pop("pin_supported_quote", None)
        quotes.clear()
        claims.clear()


def _sealed(row):
    try:
        return isinstance(row, dict) and row.get("source_sha256") == digest(
            {k: v for k, v in row.items() if k != "source_sha256"}
        )
    except (ValueError, TypeError):
        return False


def preset_decision(row):
    """Evaluate only the observed preset contract, ahead of common soft stop."""
    receipt = row.get("preset_stop")
    if not isinstance(receipt, dict):
        raise ValueError("preset_effective_stop_unobserved")
    if (
        receipt.get("schema") != "main_preset_stop_receipt_v1"
        or receipt.get("sha256")
        != digest({k: v for k, v in receipt.items() if k != "sha256"})
        or any(
            receipt.get(k) != row.get(k) for k in ("position_key", "pin_sha256", "at")
        )
        or not isinstance(receipt.get("evaluator"), str)
        or not receipt["evaluator"]
        or not all(
            finite(receipt.get(k)) for k in ("hard_stop_pct", "grace_sec", "held_sec")
        )
        or receipt["hard_stop_pct"] >= 0
        or min(receipt["grace_sec"], receipt["held_sec"]) < 0
        or type(receipt.get("enabled")) is not bool
        or (
            receipt.get("emergency_pct") is not None
            and (
                not finite(receipt["emergency_pct"])
                or receipt["emergency_pct"] > receipt["hard_stop_pct"]
            )
        )
        or (
            receipt.get("protect_pct") is not None
            and not finite(receipt["protect_pct"])
        )
        or not finite(row.get("decision_profit_pct"))
        or type(row.get("handoff_enabled")) is not bool
    ):
        raise ValueError("preset_effective_stop_invalid")
    return (
        safety_decision(
            profit_pct=row["decision_profit_pct"],
            hard_pct=receipt["hard_stop_pct"],
            emergency_pct=receipt.get("emergency_pct"),
            protect_pct=receipt.get("protect_pct"),
            preset_grace_sec=receipt["grace_sec"],
            held_sec=receipt["held_sec"],
            handoff_enabled=row["handoff_enabled"],
            manual=bool(row.get("manual")),
            pending=bool(row.get("pending_exit")),
        )
        if (
            receipt["enabled"] and row.get("automatic_management_allowed", True) is True
        )
        else None
    )


def native_preset_decision(quote, evaluation):
    """Use the actual preset caller's clock and mark, never the fast snapshot."""
    row = dict(
        quote,
        at=evaluation["at"],
        decision_profit_pct=evaluation["decision_profit_pct"],
        preset_stop=evaluation.get("preset_stop"),
        handoff_enabled=evaluation["decision_inputs"]["handoff_enabled"],
    )
    return preset_decision(row)


def valid_handoff(row):
    return (
        _sealed(row)
        and row.get("schema") == "main_stop_handoff_source_v1"
        and row.get("owner") == "main"
        and type(row.get("registered")) is bool
        and finite(row.get("at"))
        and row["at"] > 0
        and bool(
            row.get("position_key")
            and row.get("pin_sha256")
            and row.get("source_stage")
        )
        and row.get("exit_rule")
        in {"scalp_hard_stop_pct", "scalp_preset_hard_stop_pct"}
        and finite(row.get("decision_profit_pct"))
        and row.get("actual_order_submitted") is False
        and row.get("handoff_enabled") is True
        and row.get("actual_realized_net_krw") is None
        and row.get("allowed_runtime_apply") is False
    )


def valid_release(row):
    return (
        _sealed(row)
        and row.get("schema") == "main_stop_release_source_v1"
        and row.get("owner") == "main"
        and row.get("released") is True
        and row.get("remaining_excluded") is False
        and row.get("actual_order_submitted") is False
        and row.get("allowed_runtime_apply") is False
        and row.get("actual_realized_net_krw") is None
        and row.get("source_stage") == "manual_control_auto_released_at_average_price"
        and bool(row.get("position_key") and row.get("pin_sha256"))
        and row.get("auto_source")
        in {"auto_hard_stop_handoff", "auto_open_loss", "auto_scale_in_qty_guard_block"}
        and all(
            finite(row.get(k))
            for k in (
                "at",
                "quote_at",
                "quote_max_age_sec",
                "current_price",
                "average_price",
            )
        )
        and row["at"] > 0
        and row["average_price"] > 0
        and row["current_price"] >= row["average_price"]
        and row["quote_max_age_sec"] > 0
        and 0 <= row["at"] - row["quote_at"] <= row["quote_max_age_sec"]
    )


def holding_contracts(rows):
    """Keep actual evaluator scopes separate from conditional quote diagnostics."""
    result = dict(
        schema="main_holding_contract_comparison_v1",
        status="observed",
        common_stop_values=None,
        effective_preset=None,
        preset_crossing=None,
        last_per_evaluator={},
        evaluation_census={},
        conditional_certificate=None,
        manual_handoff=dict(status="not_observed", attempts=0),
        actual_realized_net_krw=None,
    )
    census = Counter()
    identity = None
    previous = None

    def observed():
        for row in rows:
            if row.get("schema") == "main_stop_source_v1" and _sealed(row):
                try:
                    common = asdict(StopValues.parse(row.get("source_stop_values")))
                except (ValueError, TypeError):
                    result.update(
                        status="source_gap", reason="original_stop_values_unverified"
                    )
                else:
                    if result["common_stop_values"] not in (None, common):
                        result.update(
                            status="source_gap", reason="original_stop_values_changed"
                        )
                    result["common_stop_values"] = common
                if (
                    row.get("role") == "SCALP_PRESET_TP"
                    and result["conditional_certificate"] is None
                ):
                    try:
                        candidate = preset_decision(row)
                        receipt = row["preset_stop"]
                        result["conditional_certificate"] = dict(
                            status="conditional_certificate",
                            source_sha256=row["source_sha256"],
                            preset=receipt,
                            conditional_rule=candidate.rule if candidate else None,
                            actual_common_soft_reachability_proven=False,
                            missing_assumptions=[
                                "actual_normal_evaluation",
                                "nonlegacy_active_scope",
                                "same_decision_price_and_clock",
                            ],
                        )
                    except (ValueError, KeyError, TypeError):
                        pass
            yield row

    with bound_evaluations(observed()) as (bound, state):
        for row, evaluation in bound:
            if result["status"] == "source_gap":
                if evaluation:
                    census[evaluation["evaluator"] + ":" + evaluation["stage"]] += 1
                elif valid_handoff(row) and (
                    identity is None
                    or tuple(
                        row.get(k)
                        for k in (
                            "position_key",
                            "pin_sha256",
                            "role",
                            "market",
                            "record_id",
                        )
                    )
                    == identity
                ):
                    old = result["manual_handoff"]
                    if row["registered"] or old["status"] != "registered":
                        result["manual_handoff"] = dict(
                            status="registered" if row["registered"] else "pending",
                            at=row["at"],
                            source_sha256=row["source_sha256"],
                            attempts=old["attempts"] + 1,
                            exit_rule=row["exit_rule"],
                            observed_profit_pct=row["decision_profit_pct"],
                        )
                    if (
                        row.get("role") == "SCALP_PRESET_TP"
                        and result["preset_crossing"] is None
                    ):
                        try:
                            decision = preset_decision(row)
                        except (ValueError, KeyError, TypeError):
                            decision = None
                        if decision and decision.disposition in {
                            "exit_candidate",
                            "manual_handoff",
                        }:
                            result["preset_crossing"] = dict(
                                at=row["at"],
                                rule=decision.rule,
                                disposition=decision.disposition,
                                evidence_kind="native_manual_handoff_receipt_not_sell",
                                first_crossing_proven=False,
                                source_sha256=row["source_sha256"],
                            )
                elif valid_release(row):
                    result["manual_release"] = dict(
                        at=row["at"],
                        source_sha256=row["source_sha256"],
                        auto_source=row["auto_source"],
                    )
                    result["manual_handoff"] = {
                        **result["manual_handoff"],
                        "status": "released",
                    }
                continue
            if row.get("schema") == "main_stop_contract_gap":
                result.update(status="source_gap", reason=row["reason"])
                continue
            current = tuple(
                row.get(k)
                for k in ("position_key", "pin_sha256", "role", "market", "record_id")
            )
            at = evaluation["at"] if evaluation else row.get("at")
            if not all(current[:4]) or (identity is not None and current != identity):
                result.update(
                    status="source_gap", reason="holding_contract_identity_changed"
                )
                continue
            if not finite(at) or (previous is not None and at < previous):
                result.update(
                    status="source_gap", reason="holding_contract_clock_invalid"
                )
                continue
            identity, previous = current, at
            if evaluation:
                key = evaluation["evaluator"] + ":" + evaluation["stage"]
                census[key] += 1
                if (
                    result["manual_handoff"]["status"] == "registered"
                    and row.get("automatic_management_allowed") is True
                    and not row.get("manual")
                ):
                    result.update(
                        status="source_gap",
                        reason="automatic_source_after_manual_handoff",
                    )
                    continue
                if evaluation["stage"] != "preset_safety":
                    continue
                result["last_per_evaluator"][key] = evaluation
                if (
                    evaluation["evaluator"] != "normal"
                    or evaluation["legacy_broker_recovered"]
                ):
                    continue
                try:
                    decision = native_preset_decision(row, evaluation)
                except (ValueError, KeyError, TypeError) as exc:
                    result.update(status="source_gap", reason=str(exc))
                    continue
                result["effective_preset"] = evaluation["preset_stop"]
                if (
                    decision is not None
                    and decision.disposition in {"exit_candidate", "manual_handoff"}
                    and result["preset_crossing"] is None
                ):
                    result["preset_crossing"] = dict(
                        at=at,
                        rule=decision.rule,
                        disposition=decision.disposition,
                        evidence_kind="actual_native_preset_evaluation_not_sell",
                        first_crossing_proven=False,
                        source_sha256=evaluation["source_sha256"],
                    )
            elif row.get("schema") == "main_stop_release_source_v1":
                if not valid_release(row):
                    result.update(
                        status="source_gap", reason="manual_release_receipt_invalid"
                    )
                    continue
                result["manual_release"] = dict(
                    at=at,
                    source_sha256=row["source_sha256"],
                    auto_source=row["auto_source"],
                )
                result["manual_handoff"] = {
                    **result["manual_handoff"],
                    "status": "released",
                }
            elif row.get("schema") == "main_stop_handoff_source_v1":
                if not valid_handoff(row):
                    result.update(
                        status="source_gap", reason="manual_handoff_receipt_invalid"
                    )
                    continue
                old = result["manual_handoff"]
                if old["status"] == "registered" and not row["registered"]:
                    result.update(
                        status="source_gap", reason="manual_custody_regressed"
                    )
                    continue
                result["manual_handoff"] = dict(
                    status="registered" if row["registered"] else "pending",
                    at=at,
                    source_sha256=row["source_sha256"],
                    attempts=old["attempts"] + 1,
                    exit_rule=row["exit_rule"],
                    observed_profit_pct=row["decision_profit_pct"],
                )
                if row.get("role") == "SCALP_PRESET_TP":
                    try:
                        decision = preset_decision(row)
                    except (ValueError, KeyError, TypeError) as exc:
                        result.update(status="source_gap", reason=str(exc))
                        continue
                    if (
                        decision is not None
                        and decision.disposition in {"exit_candidate", "manual_handoff"}
                        and result["preset_crossing"] is None
                    ):
                        result["preset_crossing"] = dict(
                            at=at,
                            rule=decision.rule,
                            disposition=decision.disposition,
                            evidence_kind="native_manual_handoff_receipt_not_sell",
                            first_crossing_proven=False,
                            source_sha256=row["source_sha256"],
                        )
            else:
                result.update(
                    status="source_gap", reason="holding_contract_source_invalid"
                )
    result["evaluation_census"] = dict(census)
    return result


def candidates(parent):
    """One axis per candidate; safety references are immutable."""
    grid = {
        "soft_stop_pct": [parent.soft_stop_pct + d for d in (-0.5, -0.25, 0.25, 0.5)],
        "grace_sec": [0, 15, 30, 45, 60],
        "window_sec": [10, 20, 30],
        "min_span_sec": [0, 4, 8],
        "min_samples": [2, 3, 5],
        "below_ratio": [0.5, 0.67, 0.8],
        "buffer_pct": [0.0, 0.1, 0.2],
    }
    result = {"parent": parent}
    for field, values in grid.items():
        for value in values:
            if value == getattr(parent, field):
                continue
            try:
                parsed = StopValues.parse(asdict(replace(parent, **{field: value})))
            except ValueError:
                continue
            result[f"{field}:{value}"] = parsed
    return result


def vote_assembly_source(rows):
    """Locate the actual common caller's store; per-call snapshots stay exact."""
    for row in rows:
        if (
            row.get("schema") != EVALUATION_SCHEMA
            or row.get("stage") != "common_soft"
            or not _sealed(row)
        ):
            continue
        inputs = row.get("decision_inputs") or {}
        source = inputs.get("holding_vote_source")
        if inputs.get("holding_ai_required") is True and isinstance(source, dict):
            return source
    return None


def replay(
    rows,
    values,
    *,
    vote_reader=None,
    post_add_generation=False,
    terminal_outcome=None,
    support_soft_threshold=None,
):
    """Only actual native decision calls can advance a counterfactual stop."""
    with bound_evaluations(rows) as (bound, source):
        result = _replay_decisions(
            bound,
            values,
            vote_reader=vote_reader,
            post_add_generation=post_add_generation,
            terminal_outcome=terminal_outcome,
            source=source,
            support_soft_threshold=support_soft_threshold,
        )
        # A caller's earlier clock can sort before an already observed fast
        # lane. Complete the new scope's global presence check before returning
        # economics. Tail rows establish integrity only; they never rewrite an
        # earlier decision/clock. Legacy sources retain their original reads.
        if source["evaluation_order_mode"] == "lane":
            for row, evaluation in bound:
                if row.get("schema") == "main_stop_contract_gap":
                    if result["status"] != "source_gap":
                        result = dict(
                            result,
                            status="source_gap",
                            reason=row["reason"],
                            modeled_net_krw=None,
                        )
            if (
                source["evaluation_global_prefix"]
                < source["evaluation_global_required"]
                and result["status"] != "source_gap"
            ):
                result = dict(
                    result,
                    status="source_gap",
                    reason="native_evaluation_global_generation_missing",
                    modeled_net_krw=None,
                )
        result["source_support"] = dict(
            shared_quotes_seen=source["quote_count"],
            native_evaluations_seen=source["evaluation_count"],
            common_soft_decisions_seen=source["common_soft_count"],
            unsupported=dict(source["unsupported"]),
        )
        return result


def _replay_decisions(
    rows,
    values,
    *,
    vote_reader=None,
    post_add_generation=False,
    terminal_outcome=None,
    source,
    support_soft_threshold=None,
):
    """First crossing on actual supplied receipts, bounded memory per position.

    A changed exit is a modeled full-depth alternative, never an actual fill.
    Original votes must already permit that exact crossing. Different/missing
    vote inputs, ADD, partial fills, manual custody and other exits censor it.
    """
    touch = None
    samples = []
    previous = None
    birth = None
    identity = None
    worst = 0.0
    count = 0
    vote_hold = None
    first_row = last_row = None
    result = dict(
        status="censored",
        reason="crossing_not_observed",
        modeled_net_krw=None,
        actual_order_submitted=False,
        allowed_runtime_apply=False,
    )
    previous_coverage = None
    for row, evaluation in rows:
        if row.get("schema") == "main_stop_contract_gap":
            return dict(result, status="source_gap", reason=row["reason"])
        if row.get("schema") == "main_stop_handoff_source_v1":
            if not valid_handoff(row) or (
                identity is not None
                and (row["position_key"], row["pin_sha256"]) != identity[:2]
            ):
                return dict(
                    result, status="source_gap", reason="manual_handoff_receipt_invalid"
                )
            return dict(
                result,
                reason=(
                    "manual_handoff_not_sell"
                    if row["registered"]
                    else "manual_handoff_pending"
                ),
            )
        if row.get("schema") == "main_stop_release_source_v1":
            return dict(
                result,
                status="censored" if valid_release(row) else "source_gap",
                reason=(
                    "manual_release_alternative_lifecycle_unmodeled"
                    if valid_release(row)
                    else "manual_release_receipt_invalid"
                ),
            )
        if evaluation is None:
            return dict(
                result,
                status="source_unsupported",
                reason="native_decision_schema_missing",
            )
        if evaluation["legacy_broker_recovered"]:
            return dict(
                result,
                status="source_unsupported",
                reason="legacy_recovered_decision_scope_unsupported",
            )
        if any(
            evaluation[k] > 0
            for k in ("capture_rejected_count", "evaluation_rejected_count")
        ):
            return dict(
                result, status="source_gap", reason="native_source_capture_loss"
            )
        if evaluation["stage"] == "preset_safety":
            if evaluation.get("evaluator") != "normal":
                source["unsupported"]["non_normal_preset_scope"] += 1
                continue
            if evaluation["priority_status"] == "blocked_legacy":
                return dict(
                    result,
                    status="source_unsupported",
                    reason="legacy_recovered_decision_scope_unsupported",
                )
            try:
                safety = native_preset_decision(row, evaluation)
            except ValueError as exc:
                return dict(result, status="source_gap", reason=str(exc))
            if safety is not None and safety.disposition in {
                "exit_candidate",
                "manual_handoff",
            }:
                return dict(
                    result,
                    status="unreachable",
                    reason="native_preset_safety_precedes_common_soft",
                    operating_rule=safety.rule,
                    operating_disposition=safety.disposition,
                    crossing_at=evaluation["at"],
                )
            continue
        quote = row
        at, bid = evaluation["at"], row.get("bid")
        if evaluation["quote_binding_status"] == "source_gap":
            try:
                original = StopValues.parse(row["source_stop_values"])
                threshold = (
                    max(v.soft_stop_pct for v in candidates(original).values())
                    if support_soft_threshold is None
                    else support_soft_threshold
                )
            except (KeyError, ValueError, TypeError):
                return dict(
                    result,
                    status="source_gap",
                    reason="original_stop_values_unverified",
                )
            if (
                not count
                and not source["coverage_discontinuity"]
                and not source["bridge_unsupported"]
                and common_no_exit_prefix(quote, evaluation, threshold)
            ):
                result["excluded_initial_quote_decisions"] = (
                    result.get("excluded_initial_quote_decisions", 0) + 1
                )
                continue
            return dict(
                result,
                status="source_unsupported",
                reason="actual_decision_quote_source_gap",
            )
        if (
            row.get("schema") != "main_stop_source_v1"
            or not finite(at)
            or not finite(bid)
            or bid <= 0
            or row.get("coverage_complete") is not True
            or row.get("owner") != "main"
            or not row.get("route")
            or not row.get("transport_epoch")
            or not row.get("position_key")
            or not row.get("pin_sha256")
            or row.get("source_sha256")
            != digest({k: v for k, v in row.items() if k != "source_sha256"})
        ):
            return dict(
                result, status="source_gap", reason="quote_or_position_source_invalid"
            )
        # The original quote stays sealed. Actual stage inputs own the decision
        # clock, flags, vote reference and contemporaneous cost model.
        row = dict(
            row,
            at=at,
            **{
                k: evaluation["decision_inputs"].get(k)
                for k in (
                    "grace_enabled",
                    "after_add",
                    "protect_enabled",
                    "handoff_enabled",
                    "vote_max_worsen_pct",
                    "holding_vote_source",
                    "holding_ai_required",
                    "cost_model",
                )
            },
        )
        row["capture_rejected_count"] = evaluation.get("capture_rejected_count")
        row["evaluation_rejected_count"] = evaluation.get("evaluation_rejected_count")
        row["decision_profit_pct"] = evaluation["decision_profit_pct"]
        current_identity = tuple(
            row.get(k)
            for k in (
                "position_key",
                "pin_sha256",
                "role",
                "market",
                "item",
                "route",
                "transport_epoch",
                "quantity",
                "buy_basis_krw",
                "capture_rejected_count",
            )
        )
        current_identity += (
            evaluation.get("evaluation_rejected_count"),
            (evaluation.get("quantity_source") or {}).get("generation_sha256"),
        )
        if post_add_generation:
            current_identity += ((row.get("post_add_generation") or {}).get("sha256"),)
        try:
            original = StopValues.parse(row["source_stop_values"])
            if digest(asdict(original)) != row.get("parent_values_sha256"):
                raise ValueError("original_values_hash")
        except (ValueError, TypeError, KeyError):
            return dict(
                result, status="source_gap", reason="original_stop_values_unverified"
            )
        threshold = (
            max(v.soft_stop_pct for v in candidates(original).values())
            if support_soft_threshold is None
            else support_soft_threshold
        )
        if not finite(threshold) or threshold < values.soft_stop_pct:
            return dict(
                result,
                status="source_gap",
                reason="common_candidate_window_threshold_invalid",
            )
        if previous is not None and (
            at < previous
            or current_identity != identity
            or previous_coverage != source["coverage_generation"]
        ):
            return dict(result, reason="coverage_or_position_generation_changed")
        if (
            not row.get("automatic_management_allowed")
            or row.get("manual")
            or row.get("pending_exit")
        ):
            return dict(result, reason="custody_or_existing_exit")
        if any(
            type(row.get(k)) is not bool
            for k in ("grace_enabled", "protect_enabled", "handoff_enabled")
        ) or not finite(row.get("vote_max_worsen_pct")):
            return dict(result, status="source_gap", reason="runtime_flags_unobserved")
        qty, basis = row.get("quantity"), row.get("buy_basis_krw")
        quantity_kind, quantity_reason = quantity_support(
            evaluation.get("quantity_source"), quote, at=at
        )
        if quantity_reason:
            if (
                not count
                and not source["coverage_discontinuity"]
                and not source["bridge_unsupported"]
                and initial_quantity_prefix_no_exit(quote, evaluation, threshold)
            ):
                result["excluded_initial_quantity_decisions"] = (
                    result.get("excluded_initial_quantity_decisions", 0) + 1
                )
                continue
            return dict(
                result,
                status="source_unsupported",
                reason=quantity_reason,
                quantity_status=quantity_kind,
            )
        count += 1
        if count == 1:
            if source["coverage_discontinuity"]:
                return dict(
                    result, status="source_gap", reason="initial_source_clock_gap"
                )
            if evaluation["decision_profit_pct"] <= threshold:
                return dict(result, reason="pre_crossing_source_missing")
            if (
                "soft_stop_micro_grace_started_at" not in evaluation["decision_inputs"]
                or evaluation["decision_inputs"]["soft_stop_micro_grace_started_at"]
                is not None
            ):
                return dict(
                    result,
                    status="source_unsupported",
                    reason="initial_soft_touch_not_reset",
                )
            result["comparison_start"] = dict(
                at=at,
                evaluation_id=evaluation["evaluation_id"],
                source_sha256=quote["source_sha256"],
                shared_soft_threshold=threshold,
                scope="whole_lifecycle_with_proven_common_no_exit_prefix",
            )
            source["pin_supported_quote"](quote)
        result["quantity_status"] = quantity_kind
        result["quantity_generation_sha256"] = evaluation["quantity_source"][
            "generation_sha256"
        ]
        model = row.get("cost_model")
        if not isinstance(model, dict):
            return dict(result, status="source_gap", reason="cost_model_source_missing")
        buy_cost, sell_rate = model.get("buy_cost_krw"), model.get("sell_cost_rate")
        known_at = cost_known_epoch(model.get("known_at"))
        if (
            not all(finite(x) for x in (qty, basis, buy_cost, sell_rate, known_at))
            or qty <= 0
            or int(qty) != qty
            or basis <= 0
            or buy_cost < 0
            or not 0 <= sell_rate < 0.05
            or known_at > at
            or not model.get("source_sha256")
        ):
            return dict(result, status="source_gap", reason="cost_model_source_missing")
        if post_add_generation:
            aggregate = row.get("post_add_generation") or {}
            if (
                aggregate.get("schema") != "verified_post_add_generation_v1"
                or aggregate.get("sha256")
                != digest({k: v for k, v in aggregate.items() if k != "sha256"})
                or aggregate.get("position_key") != row["position_key"]
                or aggregate.get("quantity") != qty
                or aggregate.get("buy_basis_krw") != basis
                or aggregate.get("cost_source_sha256") != model["source_sha256"]
                or not finite(aggregate.get("completed_at"))
                or aggregate["completed_at"] > at
                or not aggregate.get("add_receipt_sha256")
                or aggregate.get("pending_add") is not False
                or aggregate.get("partial_fill") is not False
                or row.get("pending_add")
            ):
                return dict(
                    result,
                    status="source_gap",
                    reason="post_add_aggregate_generation_unverified",
                )
        if (
            bool(row.get("after_add")) != bool(post_add_generation)
            or (row.get("add_count", 0) and not post_add_generation)
            or row.get("pending_add")
            or row.get("other_exit")
        ):
            return dict(result, reason="alternative_lifecycle_unidentified")
        quote_at = row.get("quote_at")
        if (
            not finite(quote_at)
            or not 0 <= at - quote_at <= evaluation["quote_max_age_sec"]
        ):
            return dict(result, status="source_gap", reason="quote_clock_unverified")
        if not finite(row.get("decision_profit_pct")):
            return dict(
                result, status="source_gap", reason="runtime_decision_profit_unobserved"
            )
        previous, identity, previous_coverage = (
            at,
            current_identity,
            source["coverage_generation"],
        )
        if birth is None:
            birth = at
        if first_row is None:
            first_row = row
        last_row = row
        pnl = bid * qty * (1 - sell_rate) - basis - buy_cost
        # Runtime crossing uses the actually observed decision basis. Exact
        # costs evaluate the alternative economics without rewriting that rule.
        profit = evaluation["decision_profit_pct"]
        if row.get("role") == "SCALP_PRESET_TP":
            try:
                safety = native_preset_decision(
                    source["preset_quote"], source["preset_predecessor"]
                )
            except ValueError as exc:
                return dict(result, status="source_gap", reason=str(exc))
            if safety is not None and safety.disposition in {
                "exit_candidate",
                "manual_handoff",
            }:
                return dict(
                    result,
                    status="source_gap",
                    reason="common_soft_after_terminating_preset",
                )
        line = row.get("protect_line")
        if finite(line) and line > 0:
            # Current Main has no active source-bound line generator. A legacy
            # database number alone cannot prove custody/arm/monotonicity for
            # this experiment. Runtime safety still honors the existing line.
            return dict(
                result,
                status="source_unsupported",
                reason="protect_line_producer_unidentified",
            )
        if (
            count == 1
            and not post_add_generation
            and (
                profit <= values.soft_stop_pct
                or (finite(line) and line > 0 and bid <= line)
            )
        ):
            return dict(result, reason="pre_crossing_source_missing")
        worst = min(worst, profit)
        samples, quality = append_sample(samples, at=at, price=bid)
        if quality == "capacity_censored":
            return dict(result, reason="sample_capacity_censored")
        decision = soft_decision(
            values,
            profit_pct=profit,
            now=at,
            touch_at=touch,
            enabled=row.get("grace_enabled", True),
            after_add=post_add_generation,
        )
        touch = decision.touch_at
        if decision.rule == "soft_recovered" and not post_add_generation:
            vote_hold = None
        rule = decision.rule if decision.disposition == "exit_candidate" else None
        if post_add_generation and rule != "scalp_hard_stop_pct":
            from .holding_vote_exit_models import post_add_failure

            inputs = row.get("post_add_failure_inputs") or {}
            if (
                any(
                    not finite(inputs.get(k))
                    for k in ("executed_at", "floor", "eval_sec", "tick_acceleration")
                )
                or any(
                    type(inputs.get(k)) is not bool
                    for k in ("active", "feature_usable", "large_sell_print")
                )
                or inputs["executed_at"] > at
                or inputs["eval_sec"] <= 0
            ):
                return dict(
                    result,
                    status="source_gap",
                    reason="post_add_failure_inputs_missing",
                )
            rule = (
                "reversal_add_post_eval_fail"
                if inputs["active"]
                and post_add_failure(
                    profit=profit,
                    floor=inputs["floor"],
                    elapsed=at - inputs["executed_at"],
                    eval_sec=inputs["eval_sec"],
                    feature_usable=inputs["feature_usable"],
                    large_sell_print=inputs["large_sell_print"],
                    tick_acceleration=inputs["tick_acceleration"],
                )
                else None
            )
        if finite(line) and line > 0 and bid <= line:
            confirmed, _ = protect_confirmed(
                values,
                samples,
                now=at,
                price_line=line,
                profit_pct=profit,
                enabled=row.get("protect_enabled", True),
            )
            if confirmed:
                rule = "protect_trailing_stop"
        if not rule:
            continue
        # Never infer an earlier crossing from a series starting below threshold.
        if count == 1:
            return dict(result, reason="pre_crossing_source_missing")
        # Runtime EXIT_SOFT_STOP also releases VETO at the existing protective
        # emergency threshold. Keep that effective priority; do not extend it.
        safety = (
            profit <= values.hard_stop_pct or profit <= values.protect_emergency_pct
        )
        if profit <= values.hard_stop_pct and row.get("handoff_enabled"):
            return dict(result, reason="manual_handoff_not_sell")
        if (
            row.get("holding_ai_required") is not False
            and not safety
            and rule != "protect_trailing_stop"
        ):
            if not isinstance(row.get("holding_vote_source"), dict):
                return dict(
                    result, status="source_gap", reason="holding_vote_reference_unbound"
                )
            if vote_hold is None:
                vote = (
                    vote_reader(row, at)
                    if vote_reader is not None
                    else (row.get("original_vote") or {})
                )
                if not (
                    vote.get("decision") in {"PASS", "VETO", "INSUFFICIENT"}
                    and vote.get("source_verified") is True
                ):
                    return dict(result, reason="original_crossing_vote_unidentified")
                vote_hold = dict(vote=vote, at=at, profit=profit, started=touch or at)
            from .trailing_exit_decision import evaluate_exit_deferral

            vote = vote_hold["vote"]
            outcome = evaluate_exit_deferral(
                decision=vote["decision"],
                now=at,
                signal_at=vote_hold["at"],
                started_at=vote_hold["started"],
                anchor_profit=vote_hold["profit"],
                profit=profit,
                max_defer_sec=vote["max_defer_sec"],
                max_worsen_pct=row.get("vote_max_worsen_pct", 0.8),
                policy_valid=True,
                quote_fresh=True,
                safety=safety,
                same_generation=True,
                same_market=True,
            )
            if not outcome.proceeds:
                continue
        if not finite(row.get("bid_qty")) or row["bid_qty"] < qty:
            return dict(result, reason="full_executable_depth_unobserved")
        return dict(
            result,
            status="modeled",
            reason=rule,
            modeled_net_krw=pnl,
            crossing_at=at,
            exposure_sec=at - birth,
            mae_pct=worst,
            evidence_kind="actual_entry_alternative_exit",
            cost_source_sha256=model["source_sha256"],
        )
    if not count:
        return dict(
            result,
            status="source_unsupported",
            reason="actual_common_soft_decision_unobserved",
        )
    if terminal_outcome is not None:
        if (
            previous_coverage != source["coverage_generation"]
            or source["bridge_unsupported"]
        ):
            return dict(result, reason="terminal_bridge_source_unsupported")
        terminal_quote = source["last_quote"]
        if terminal_quote.get("native_decision_required") is True:
            kind, gap = quantity_support(
                terminal_quote.get("quantity_source"), terminal_quote
            )
            if (
                gap
                or kind != result["quantity_status"]
                or terminal_quote["quantity_source"].get("generation_sha256")
                != result["quantity_generation_sha256"]
            ):
                return dict(
                    result,
                    status="source_unsupported",
                    reason="terminal_quantity_generation_unverified",
                )
        if post_add_generation:
            return dict(result, reason="terminal_add_lifecycle_unsupported")
        try:
            terminal = validate_terminal_outcome(
                terminal_outcome,
                first_row=source["first_supported_quote"],
                last_row=source["last_quote"],
            )
        except (ValueError, TypeError, KeyError):
            return dict(result, status="source_gap", reason="terminal_outcome_unbound")
        if terminal["kind"] == "horizon_mark":
            return dict(
                result,
                reason="horizon_mark_not_terminal",
                evidence_kind="unrealized_horizon_diagnostic",
                horizon_price=terminal["price"],
                horizon_at=terminal["at"],
            )
        last_row = source["last_quote"]
        model = last_row["cost_model"]
        return dict(
            result,
            status="modeled",
            reason="observed_normal_exit_endpoint",
            modeled_net_krw=terminal["price"]
            * last_row["quantity"]
            * (1 - model["sell_cost_rate"])
            - last_row["buy_basis_krw"]
            - model["buy_cost_krw"],
            crossing_at=terminal["at"],
            exposure_sec=terminal["at"] - birth,
            mae_pct=worst,
            evidence_kind="actual_entry_modeled_normal_exit_endpoint",
            cost_source_sha256=model["source_sha256"],
            terminal_source_sha256=terminal["source_reference"]["sha256"],
            terminal_outcome_sha256=terminal["source_sha256"],
            actual_realized_net_krw=None,
        )
    return result


def source_diagnostics(
    rows, parent, normal_decision=None, *, support_soft_threshold=None
):
    """Whole-input source census; never truncate at a counterfactual crossing."""
    counts = Counter()
    evaluators = Counter()
    quantities = Counter()
    gaps = Counter()
    minimum = None
    first_soft = None
    first_preset = None
    first_at = last_at = None
    first_source = last_source = normal_source = None
    economic_binding_source = None
    first_supported = None
    threshold = (
        max(v.soft_stop_pct for v in candidates(parent).values())
        if support_soft_threshold is None
        else support_soft_threshold
    )
    prefix_supported = True
    excluded_quantity = 0
    first_quantity_seen = False
    tail = dict(observations=0, first_at=None, last_at=None)
    support = dict(
        windows=0,
        decisions=0,
        pre_crossing_decisions=0,
        first_at=None,
        last_at=None,
        quantity_cohorts={},
        scope="actual_normal_common_soft_gate_checked",
    )
    cohort_counts = Counter()
    previous_support = None
    invalid = 0

    def observed():
        nonlocal minimum, first_soft, first_at, last_at, first_source, last_source, normal_source
        for row in rows:
            counts["observations"] += 1
            if normal_source is not None:
                tail["observations"] += 1
                if finite(row.get("at")):
                    tail["first_at"] = (
                        row["at"]
                        if tail["first_at"] is None
                        else min(tail["first_at"], row["at"])
                    )
                    tail["last_at"] = (
                        row["at"]
                        if tail["last_at"] is None
                        else max(tail["last_at"], row["at"])
                    )
            if row.get("schema") == EVALUATION_SCHEMA:
                counts["evaluation_receipts"] += 1
                evaluators[str(row.get("evaluator")) + ":" + str(row.get("stage"))] += 1
            elif row.get("schema") != "main_stop_source_v1":
                counts["lifecycle_receipts"] += 1
            else:
                counts["shared_quotes"] += 1
                retained = _RetainedSource(row)
                if first_source is None:
                    first_source = retained
                last_source = retained
                at, profit = row.get("at"), row.get("decision_profit_pct")
                if finite(at):
                    first_at = at if first_at is None else min(first_at, at)
                    last_at = at if last_at is None else max(last_at, at)
                if not _sealed(row):
                    counts["invalid_source_seal"] += 1
                else:
                    if (
                        normal_decision is not None
                        and at == normal_decision["decision_at"]
                        and row.get("bid") == normal_decision["executable_bid"]
                    ):
                        if normal_source is not None:
                            raise ValueError(
                                "stop_research_normal_exit_source_ambiguous"
                            )
                        normal_source = retained
                    for name in (
                        "partial_fill",
                        "pending_add",
                        "pending_exit",
                        "manual",
                    ):
                        if row.get(name):
                            counts[name] += 1
                    for name in ("coverage_complete", "automatic_management_allowed"):
                        if row.get(name) is not True:
                            counts[name + ":false_or_missing"] += 1
                    if finite(profit):
                        minimum = profit if minimum is None else min(minimum, profit)
                        if profit <= parent.soft_stop_pct and first_soft is None:
                            first_soft = at
                    if finite(row.get("protect_line")) and row["protect_line"] > 0:
                        counts["protect_line_without_supported_generator"] += 1
                    if row.get("role") == "SCALP_PRESET_TP":
                        try:
                            decision = preset_decision(row)
                            if decision and decision.disposition in {
                                "exit_candidate",
                                "manual_handoff",
                            }:
                                counts[
                                    "conditional_preset:" + decision.disposition
                                ] += 1
                        except (ValueError, KeyError, TypeError):
                            counts["preset_receipt_invalid_or_missing"] += 1
            yield row

    with bound_evaluations(observed()) as (bound, state):
        for quote, evaluation in bound:
            if quote.get("schema") == "main_stop_contract_gap":
                invalid += 1
                gaps[quote["reason"]] += 1
                previous_support = None
                continue
            if evaluation is None:
                previous_support = None
                continue
            if evaluation["legacy_broker_recovered"]:
                gaps["legacy_recovered_decision_scope_unsupported"] += 1
                previous_support = None
                continue
            if any(
                evaluation[k] > 0
                for k in ("capture_rejected_count", "evaluation_rejected_count")
            ):
                invalid += 1
                gaps["native_source_capture_loss"] += 1
                previous_support = None
                continue
            if evaluation["stage"] == "preset_safety":
                if evaluation["evaluator"] == "normal":
                    try:
                        decision = native_preset_decision(quote, evaluation)
                    except (ValueError, KeyError, TypeError):
                        invalid += 1
                        gaps["preset_effective_stop_invalid"] += 1
                        previous_support = None
                        continue
                    if decision and decision.disposition in {
                        "exit_candidate",
                        "manual_handoff",
                    }:
                        counts["actual_normal_preset_preempts_common_soft"] += 1
                        if first_preset is None:
                            first_preset = evaluation["at"]
                        previous_support = None
                continue
            if evaluation["quote_binding_status"] == "source_gap":
                if (
                    not first_quantity_seen
                    and prefix_supported
                    and not state["coverage_discontinuity"]
                    and not state["bridge_unsupported"]
                    and common_no_exit_prefix(quote, evaluation, threshold)
                ):
                    counts["excluded_initial_quote_decisions"] += 1
                else:
                    prefix_supported = False
                gaps["actual_decision_quote_source_gap"] += 1
                previous_support = None
                continue
            kind, reason = quantity_support(
                evaluation.get("quantity_source"), quote, at=evaluation["at"]
            )
            quantities[kind] += 1
            if reason:
                if (
                    not first_quantity_seen
                    and prefix_supported
                    and not state["coverage_discontinuity"]
                    and not state["bridge_unsupported"]
                    and initial_quantity_prefix_no_exit(quote, evaluation, threshold)
                ):
                    excluded_quantity += 1
                else:
                    prefix_supported = False
                gaps[reason] += 1
                previous_support = None
                continue
            if not first_quantity_seen:
                first_quantity_seen = True
                if (
                    state["coverage_discontinuity"]
                    or evaluation["decision_profit_pct"] <= threshold
                    or "soft_stop_micro_grace_started_at"
                    not in evaluation["decision_inputs"]
                    or evaluation["decision_inputs"]["soft_stop_micro_grace_started_at"]
                    is not None
                ):
                    prefix_supported = False
            if (
                quote.get("coverage_complete") is not True
                or quote.get("owner") != "main"
                or quote.get("automatic_management_allowed") is not True
                or quote.get("manual")
                or quote.get("pending_exit")
                or quote.get("pending_add")
                or quote.get("add_count")
                or evaluation["decision_inputs"]["after_add"]
            ):
                gaps["decision_lifecycle_scope_unsupported"] += 1
                previous_support = None
                continue
            if finite(quote.get("protect_line")) and quote["protect_line"] > 0:
                gaps["protect_line_producer_unidentified"] += 1
                previous_support = None
                continue
            identity = (
                kind,
                evaluation["quantity_source"]["generation_sha256"],
                evaluation["pin_sha256"],
                evaluation["route"],
                evaluation["item"],
                evaluation["transport_epoch"],
                evaluation.get("capture_rejected_count"),
                evaluation.get("evaluation_rejected_count"),
                state["coverage_generation"],
            )
            if previous_support != identity:
                support["windows"] += 1
            previous_support = identity
            support["decisions"] += 1
            cohort_counts[kind] += 1
            if economic_binding_source is None and prefix_supported:
                first_supported = _RetainedSource(quote)
                from .main_stop_runtime_source import resolve_quantity_source

                economic_binding_source = {
                    k: quote[k]
                    for k in (
                        "position_key",
                        "record_id",
                        "pin_sha256",
                        "role",
                        "market",
                        "item",
                        "route",
                        "transport_epoch",
                        "quantity",
                        "buy_basis_krw",
                    )
                }
                economic_binding_source.update(
                    at=evaluation["at"],
                    quantity_source=resolve_quantity_source(
                        evaluation["quantity_source"], quote, at=evaluation["at"]
                    ),
                    evaluation_source_sha256=evaluation["source_sha256"],
                    quote_source_sha256=quote["source_sha256"],
                )
                economic_binding_source = _RetainedSource(economic_binding_source)
            if evaluation["decision_profit_pct"] > parent.soft_stop_pct:
                support["pre_crossing_decisions"] += 1
            at = evaluation["at"]
            support["first_at"] = (
                at if support["first_at"] is None else min(support["first_at"], at)
            )
            support["last_at"] = (
                at if support["last_at"] is None else max(support["last_at"], at)
            )
    support["quantity_cohorts"] = dict(cohort_counts)
    if not prefix_supported:
        gaps["initial_comparison_prefix_unproven"] += 1
    status = (
        "source_gap"
        if invalid
        else (
            "source_unsupported"
            if not prefix_supported
            else (
                "supported_decision_windows"
                if support["decisions"] >= 2
                else (
                    "insufficient_sample"
                    if support["decisions"]
                    else (
                        "unreachable_observed"
                        if counts["actual_normal_preset_preempts_common_soft"]
                        else "source_unsupported"
                    )
                )
            )
        )
    )
    return dict(
        counts=dict(counts),
        minimum_observed_decision_profit_pct=minimum,
        first_observed_soft_at=first_soft,
        first_observed_preset_at=first_preset,
        first_at=first_at,
        last_at=last_at,
        native_support=dict(
            status=status,
            evaluator_census=dict(evaluators),
            quantity_census=dict(quantities),
            supported_windows=support,
            gaps=dict(gaps),
            whole_population_scanned=True,
            shared_quote_only_never_implies_normal_decision=True,
            protection_scope="source_unsupported_no_active_source_bound_generator",
        ),
        economic_binding_source=economic_binding_source,
        comparison_prefix=dict(
            whole_lifecycle_no_exit_prefix_proven=prefix_supported
            and first_supported is not None,
            excluded_initial_quantity_decisions=excluded_quantity,
            shared_soft_threshold=threshold,
            original_first_source_sha256=(
                first_source.get("source_sha256") if first_source else None
            ),
            supported_first_source_sha256=(
                first_supported.get("source_sha256") if first_supported else None
            ),
        ),
        source_endpoints=dict(
            first=first_supported or first_source,
            last=last_source,
            normal_exit=normal_source,
            normal_decision_expected=normal_decision is not None,
            excluded_tail=tail,
        ),
        observation_kind="source_diagnostics_not_actual_stop_or_profit",
    )


def terminal_from_endpoints(endpoints, economic):
    try:
        if (
            endpoints.get("normal_decision_expected")
            and endpoints.get("normal_exit") is None
        ):
            raise ValueError("stop_terminal_exact_original_decision_row_missing")
        result = normal_exit_terminal_outcome(
            first_row=endpoints.get("first"),
            last_row=endpoints.get("normal_exit") or endpoints.get("last"),
            economic=economic,
        )
        return result, None
    except ValueError as exc:
        return None, str(exc)


def terminal_prefix(rows, terminal):
    for row in rows:
        yield row
        if (
            terminal is not None
            and row.get("source_sha256") == terminal["last_source_sha256"]
        ):
            return
    if terminal is not None:
        raise ValueError("stop_research_terminal_source_not_replayed")


def prepare_terminal_prefix(
    rows_factory, economic, *, parent=None, support_soft_threshold=None
):
    """Share native terminal binding without reconstructing missing decisions."""
    if parent is None:
        first = next(rows_factory(), {})
        parent = StopValues.parse(first.get("source_stop_values"))
    try:
        decision = normal_exit_decision_from_economic(economic)
    except ValueError:
        decision = None
    diagnostics = source_diagnostics(
        rows_factory(), parent, decision, support_soft_threshold=support_soft_threshold
    )
    endpoints = diagnostics.pop("source_endpoints")
    terminal, reason = terminal_from_endpoints(endpoints, economic)
    diagnostics["terminal_reason"] = reason
    diagnostics["excluded_tail"] = endpoints["excluded_tail"] if terminal else None
    return lambda: terminal_prefix(rows_factory(), terminal), terminal, diagnostics


def validate_terminal_outcome(value, *, first_row, last_row):
    """Validate a native caller's verified endpoint; never infer missing prices.

    The caller verifies the original receipt and its source generation. This
    pure boundary checks its sealed projection against both observed endpoints;
    a boolean assertion of verification cannot supply the missing binding.
    """

    def sha(text):
        return (
            isinstance(text, str)
            and len(text) == 64
            and all(c in "0123456789abcdef" for c in text)
        )

    if (
        not _sealed(first_row)
        or not _sealed(last_row)
        or first_row.get("schema") != "main_stop_source_v1"
        or last_row.get("schema") != "main_stop_source_v1"
        or not _sealed(value)
        or value.get("schema") != "main_stop_terminal_outcome_v1"
        or value.get("kind") not in {"observed_normal_exit", "horizon_mark"}
    ):
        raise ValueError("stop_terminal_contract_invalid")
    model = last_row.get("cost_model")
    if (
        not quote_supported(last_row)
        or not isinstance(model, dict)
        or not all(finite(model.get(k)) for k in ("buy_cost_krw", "sell_cost_rate"))
        or model["buy_cost_krw"] < 0
        or not 0 <= model["sell_cost_rate"] < 0.05
        or cost_known_epoch(model.get("known_at")) is None
        or cost_known_epoch(model["known_at"]) > last_row["at"]
        or last_row.get("automatic_management_allowed") is not True
        or any(
            last_row.get(k) is not False
            for k in ("manual", "pending_add", "pending_exit")
        )
        or last_row.get("add_count") != 0
    ):
        raise ValueError("stop_terminal_quote_or_cost_unverified")
    for key in (
        "position_key",
        "record_id",
        "pin_sha256",
        "role",
        "market",
        "item",
        "route",
        "transport_epoch",
        "quantity",
        "buy_basis_krw",
    ):
        if (
            value.get(key) is None
            or type(value.get(key)) is not type(last_row.get(key))
            or value.get(key) != first_row.get(key)
            or value.get(key) != last_row.get(key)
        ):
            raise ValueError("stop_terminal_identity_invalid")
    if (
        value.get("first_source_sha256") != first_row["source_sha256"]
        or value.get("last_source_sha256") != last_row["source_sha256"]
        or value.get("at") != last_row["at"]
        or value.get("price") != last_row["bid"]
        or not finite(value.get("at"))
        or not finite(value.get("price"))
        or value["price"] <= 0
        or not finite(last_row.get("bid_qty"))
        or last_row["bid_qty"] < last_row["quantity"]
        or value.get("cost_source_sha256") != last_row["cost_model"]["source_sha256"]
        or value.get("owner") != "main"
        or value.get("automatic_management_allowed") is not True
        or any(
            value.get(k) is not False for k in ("manual", "pending_add", "partial_fill")
        )
        or type(value.get("add_count")) is not int
        or value["add_count"] != 0
    ):
        raise ValueError("stop_terminal_source_invalid")
    reference = value.get("source_reference")
    if (
        not isinstance(reference, dict)
        or not isinstance(reference.get("path"), str)
        or not reference["path"].strip()
        or not sha(reference.get("sha256"))
    ):
        raise ValueError("stop_terminal_reference_missing")
    if value["kind"] == "horizon_mark":
        return value
    receipt = value.get("receipt_binding")
    if (
        not isinstance(receipt, dict)
        or receipt.get("sha256")
        != digest({k: v for k, v in receipt.items() if k != "sha256"})
        or receipt.get("status") != "COMPLETED"
        or type(receipt.get("main_automatic_management_allowed")) is not bool
        or receipt.get("decision_automatic_management_allowed") is not True
        or receipt.get("seller_attribution_basis")
        != "native_main_decision_same_order_generation"
        or receipt.get("partial_fill") is not False
        or type(receipt.get("add_count")) is not int
        or receipt["add_count"] != 0
        or value.get("exit_rule")
        not in {"scalp_trailing_take_profit", "daily_limit_up_immediate_exit"}
        or receipt.get("exit_rule") != value["exit_rule"]
        or any(
            receipt.get(k) != value[k]
            for k in ("position_key", "record_id", "quantity")
        )
        or receipt.get("decision_at") != value["at"]
        or receipt.get("executable_bid") != value["price"]
        or receipt.get("decision_price_basis")
        != (
            "executable_bid"
            if value["exit_rule"] == "scalp_trailing_take_profit"
            else "mark_price"
        )
        or not finite(receipt.get("decision_price"))
        or receipt["decision_price"] <= 0
        or (
            value["exit_rule"] == "scalp_trailing_take_profit"
            and receipt["decision_price"] != value["price"]
        )
        or receipt.get("source_sha256") != reference["sha256"]
    ):
        raise ValueError("stop_terminal_receipt_invalid")
    return value


def normal_exit_decision_from_economic(economic):
    """Read the sealed native decision from the verified immutable cost source."""
    import json
    from .main_stop_policy import NORMAL_EXIT_RULES

    try:
        if (
            economic.get("schema") != "main_stop_research_cost_v1"
            or economic.get("artifact_sha256")
            != digest({k: v for k, v in economic.items() if k != "artifact_sha256"})
            or economic.get("status") != "eligible"
            or economic.get("economics_scope") != "main_stop_research_only"
            or economic.get("manual_exit") is not False
            or economic.get("custody_status") != "verified_registry_fill_census"
            or economic.get("fill_state")
            not in {"fully_closed", "fully_closed_multi_fill"}
            or economic.get("main_exit_source", {}).get("seller_attribution_basis")
            != "native_main_decision_same_order_generation"
        ):
            raise ValueError("stop_terminal_completion_unverified")
        native = economic["terminal_observation"]
        signal = native["exit_signal"]
        fields = signal.get("fields") or {}
        raw = fields.get("main_stop_normal_exit_decision")
        if isinstance(raw, str):
            if len(raw.encode()) > 8192:
                raise ValueError("stop_terminal_decision_unbounded")
            raw = json.loads(raw)
        if (
            not _sealed(raw)
            or raw.get("schema") != "main_stop_normal_exit_decision_v1"
            or raw.get("status") != "decision_observed"
            or raw.get("source_stage") != "exit_signal"
            or raw.get("exit_rule") not in NORMAL_EXIT_RULES
            or signal.get("exit_rule", fields.get("exit_rule")) != raw["exit_rule"]
            or raw.get("actual_order_submitted") is not False
            or raw.get("allowed_runtime_apply") is not False
            or raw.get("actual_realized_net_krw") is not None
            or raw.get("owner") != "main"
            or raw.get("automatic_management_allowed") is not True
            or economic.get("main_exit_source", {}).get("status")
            != "verified_native_decision_submit_chain"
            or economic.get("main_exit_source", {}).get("exit_rule") != raw["exit_rule"]
            or any(raw.get(k) is not False for k in ("manual", "pending_add"))
            or raw.get("quantity_source_status") != "runtime_observed_not_terminal"
            or not all(
                finite(raw.get(k)) and raw[k] > 0
                for k in (
                    "decision_at",
                    "decision_price",
                    "executable_bid",
                    "mark_price",
                    "quantity",
                    "buy_basis_krw",
                )
            )
            or raw.get("decision_price_basis")
            != (
                "executable_bid"
                if raw["exit_rule"] == "scalp_trailing_take_profit"
                else "mark_price"
            )
            or raw["decision_price"] != raw[raw["decision_price_basis"]]
            or str(raw.get("record_id")) != str(economic.get("record_id"))
            or type(raw.get("add_count")) is not int
            or raw["add_count"] != 0
        ):
            raise ValueError("stop_terminal_normal_decision_missing")
        return raw
    except (KeyError, TypeError, AttributeError, ArithmeticError) as exc:
        raise ValueError("stop_terminal_native_decision_missing") from exc


def normal_exit_terminal_outcome(*, first_row, last_row, economic):
    """Bind the exact original quote to native decision and full custody closure.

    Flat native snapshots retain their original management flag. Seller authority
    comes from the native decision/submit generation, never that flat-state flag.
    """
    from src.engine.lifecycle.broker_cost_allocation import _legs

    try:
        raw = normal_exit_decision_from_economic(economic)
        native = economic["terminal_observation"]
        for name in (
            "position_key",
            "record_id",
            "pin_sha256",
            "role",
            "market",
            "quantity",
            "buy_basis_krw",
        ):
            if (
                type(raw.get(name)) is not type(last_row.get(name))
                or raw.get(name) != last_row.get(name)
                or raw.get(name) != first_row.get(name)
            ):
                raise ValueError("stop_terminal_normal_decision_identity")
        quantity = economic["quantity_basis"]
        completed_at = cost_known_epoch(native.get("terminal_fill_time"))
        buys, sells = _legs(native["buy_fill_legs"]), _legs(native["sell_fill_legs"])

        # Native log clocks can be truncated to whole seconds. Preserve that
        # representation interval; a supplied subsecond clock gets no slack.
        def precedes_decision(stamp):
            bound = 1.0 if float(stamp).is_integer() else 0.0
            return stamp < raw["decision_at"] and raw["decision_at"] >= stamp + bound

        if (
            native.get("status") != "COMPLETED"
            or type(native.get("main_automatic_management_allowed")) is not bool
            or native.get("strategy") != "SCALPING"
            or str(native.get("id")) != str(raw["record_id"])
            or native.get("terminal_decision_authority")
            != "broker_sell_fill_observation_only"
            or native.get("terminal_population_scope") != "real_record_bound"
            or quantity.get("buy_qty") != raw["quantity"]
            or quantity.get("sell_qty") != raw["quantity"]
            or quantity.get("residual_qty") != 0
            or not buys
            or not sells
            or float(sum(leg[1] for leg in buys)) != raw["quantity"]
            or float(sum(leg[1] for leg in sells)) != raw["quantity"]
            or float(sum(leg[2] for leg in buys)) != raw["buy_basis_krw"]
            or raw["decision_at"] != last_row["at"]
            or raw["executable_bid"] != last_row["bid"]
            or max(leg[0].timestamp() for leg in buys) > first_row["at"]
            or completed_at is None
            or precedes_decision(completed_at)
            or any(precedes_decision(leg[0].timestamp()) for leg in sells)
        ):
            raise ValueError("stop_terminal_native_completion_mismatch")
        projection = economic["completion_source"]["projection"]
        reference = dict(path=projection["path"], sha256=projection["sha256"])
        receipt = dict(
            status="COMPLETED",
            main_automatic_management_allowed=native[
                "main_automatic_management_allowed"
            ],
            decision_automatic_management_allowed=True,
            seller_attribution_basis=economic["main_exit_source"][
                "seller_attribution_basis"
            ],
            native_terminal_at=completed_at,
            terminal_clock_precision_bound_sec=(
                1.0 if float(completed_at).is_integer() else 0.0
            ),
            sell_fill_clock_precision_bound_sec=max(
                1.0 if leg[0].microsecond == 0 else 0.0 for leg in sells
            ),
            executable_bid=raw["executable_bid"],
            decision_price_basis=raw["decision_price_basis"],
            partial_fill=False,
            add_count=0,
            position_key=raw["position_key"],
            record_id=raw["record_id"],
            quantity=raw["quantity"],
            decision_at=raw["decision_at"],
            decision_price=raw["decision_price"],
            exit_rule=raw["exit_rule"],
            source_sha256=reference["sha256"],
            normal_decision_sha256=raw["source_sha256"],
        )
        receipt["sha256"] = digest(receipt)
        value = {
            key: last_row[key]
            for key in (
                "position_key",
                "record_id",
                "pin_sha256",
                "role",
                "market",
                "item",
                "route",
                "transport_epoch",
                "quantity",
                "buy_basis_krw",
            )
        }
        value.update(
            schema="main_stop_terminal_outcome_v1",
            kind="observed_normal_exit",
            first_source_sha256=first_row["source_sha256"],
            last_source_sha256=last_row["source_sha256"],
            at=raw["decision_at"],
            price=raw["executable_bid"],
            exit_rule=raw["exit_rule"],
            cost_source_sha256=last_row["cost_model"]["source_sha256"],
            owner="main",
            automatic_management_allowed=True,
            manual=False,
            pending_add=False,
            partial_fill=False,
            add_count=0,
            source_reference=reference,
            receipt_binding=receipt,
        )
        value["source_sha256"] = digest(value)
        return validate_terminal_outcome(value, first_row=first_row, last_row=last_row)
    except (KeyError, TypeError, AttributeError, ArithmeticError) as exc:
        raise ValueError("stop_terminal_native_completion_missing") from exc


def validate_experiment(contract, *, parent_sha, source_sha, code_sha):
    """A numerical acceptance contract is frozen before source/holdout evaluation."""
    if not isinstance(contract, dict):
        raise ValueError("stop_experiment_missing")
    if contract.get("schema") == "main_stop_experiment_v2":
        from .main_stop_experiment import validate_experiment_v2

        return validate_experiment_v2(
            contract,
            parent_sha=parent_sha,
            source_sha=source_sha,
            code_sha=code_sha,
            require_promotion=True,
        )
    body = {k: v for k, v in contract.items() if k != "experiment_sha256"}
    if (
        contract.get("schema") != "main_stop_experiment_v1"
        or contract.get("experiment_sha256") != digest(body)
        or contract.get("parent_sha256") != parent_sha
        or contract.get("source_sha256") != source_sha
        or contract.get("code_sha256") != code_sha
        or not contract.get("operator_lock_sha256")
        or not finite(contract.get("frozen_at"))
        or not finite(contract.get("split_at"))
        or type(contract.get("min_train")) is not int
        or contract["min_train"] < 2
        or type(contract.get("min_holdout")) is not int
        or contract["min_holdout"] < 2
        or not finite(contract.get("minimum_paired_ev_krw"))
        or contract["minimum_paired_ev_krw"] < 0
        or not isinstance(contract.get("allowed_keys"), list)
        or not contract["allowed_keys"]
        or not set(contract["allowed_keys"]) <= TUNABLE
        or not finite(contract.get("embargo_sec"))
        or contract["embargo_sec"] < 60
    ):
        raise ValueError("stop_experiment_binding_invalid")
    if (
        not finite(contract.get("max_censoring_ratio"))
        or not 0 <= contract["max_censoring_ratio"] < 1
        or not finite(contract.get("max_standard_error_krw"))
        or contract["max_standard_error_krw"] < 0
        or not isinstance(contract.get("max_daily_change"), dict)
        or set(contract["max_daily_change"]) != set(contract["allowed_keys"])
        or any(not finite(x) or x <= 0 for x in contract["max_daily_change"].values())
        or not isinstance(contract.get("performance_receipt"), dict)
    ):
        raise ValueError("stop_acceptance_limits_not_frozen")
    from .main_stop_policy import bounded_object

    performance, sha = bounded_object(contract["performance_receipt"].get("path", ""))
    if (
        sha != contract["performance_receipt"].get("sha256")
        or performance.get("schema") != "main_stop_performance_v1"
        or performance.get("status") != "pass"
        or performance.get("code_sha256") != code_sha
        or performance.get("scope") != "runtime_and_postclose"
        or performance.get("unresolved_findings") != []
    ):
        raise ValueError("stop_performance_gate_unverified")
    if contract["frozen_at"] >= contract["split_at"] - contract["embargo_sec"]:
        raise ValueError("stop_experiment_not_frozen_before_holdout")
    return contract


def split_acceptable(row, split, contract):
    n, total = row[split + "_n"], row[split + "_total"]
    if n < contract["min_" + split] or total < n or not total:
        return False
    variance = max(
        0.0, (row[split + "_delta_sq"] - row[split + "_delta"] ** 2 / n) / (n - 1)
    )
    return (
        1 - n / total <= contract["max_censoring_ratio"]
        and math.sqrt(variance / n) <= contract["max_standard_error_krw"]
    )


def choose(aggregates, contract):
    """Use global identical eligible denominators, one train winner then holdout."""
    if not contract:
        return None, "baseline_carry"
    for row in aggregates.values():
        if (
            not isinstance(row, dict)
            or any(
                type(row.get(k)) is not int or row[k] < 0
                for k in (
                    "train_n",
                    "holdout_n",
                    "train_total",
                    "holdout_total",
                    "train_safety_regressions",
                    "holdout_safety_regressions",
                )
            )
            or any(
                not finite(row.get(k))
                for k in (
                    "train_delta",
                    "holdout_delta",
                    "train_delta_sq",
                    "holdout_delta_sq",
                )
            )
            or row["train_delta_sq"] < 0
            or row["holdout_delta_sq"] < 0
        ):
            raise ValueError("stop_selection_aggregate_invalid")
        for split in ("train", "holdout"):
            n = row[split + "_n"]
            if row[split + "_total"] < n or (
                n and row[split + "_delta_sq"] + 1e-6 < row[split + "_delta"] ** 2 / n
            ):
                raise ValueError("stop_selection_aggregate_invalid")
    rows = [
        (name, row)
        for name, row in aggregates.items()
        if name != "parent" and name.split(":")[0] in contract["allowed_keys"]
    ]
    eligible = [
        (name, row)
        for name, row in rows
        if split_acceptable(row, "train", contract)
        and row["train_delta"] / row["train_n"] > contract["minimum_paired_ev_krw"]
        and row["train_safety_regressions"] == 0
    ]
    if not eligible:
        return None, (
            "hold_sample"
            if not rows
            or any(not split_acceptable(row, "train", contract) for _, row in rows)
            else "hold_no_edge"
        )
    name, row = max(
        eligible,
        key=lambda pair: (pair[1]["train_delta"] / pair[1]["train_n"], pair[0]),
    )
    if not split_acceptable(row, "holdout", contract):
        return None, "hold_sample"
    if row["holdout_safety_regressions"]:
        return None, "hold_no_edge"
    if row["holdout_delta"] / row["holdout_n"] <= contract["minimum_paired_ev_krw"]:
        return None, "hold_no_edge"
    return name, "selected"
