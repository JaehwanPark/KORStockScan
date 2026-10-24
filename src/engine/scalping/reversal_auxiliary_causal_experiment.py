"""Offline, versioned prefix facts for the auxiliary input ablation.

This module deliberately has no registry, filesystem, provider or publication
writer. The original typed input and original request remain immutable. The
outer union version is the frozen codec surface; the added evidence has its
own version and explicit request identity, and is not a runtime input upgrade.
"""

from __future__ import annotations

import copy
import math
import re

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W

VERSION = "auxiliary_observed_prefix_ablation_v1"
FEATURES = {
    "observed_prefix_return_pct": ("percent", "PREFIX_PATH_CONCERN"),
    "observed_prefix_giveback_pct": ("percent", "PREFIX_PATH_CONCERN"),
    "known_side_buy_qty_share_pct": ("percent", "PREFIX_FLOW_CONCERN"),
    "known_side_qty_coverage_pct": ("percent", "PREFIX_FLOW_CONCERN"),
    "return_60s_minus_spread_pct": ("percentage_points", "EXECUTABLE_PROGRESS_CONCERN"),
    "root_to_confirmation_return_pct": ("percent", "PREFIX_PATH_CONCERN"),
    "root_interval_min_change_pct": ("percent", "PREFIX_PATH_CONCERN"),
    "root_interval_buy_qty_share_pct": ("percent", "PREFIX_FLOW_CONCERN"),
}
SOURCE_PREFIX_SCHEMA = "auxiliary_observed_prefix_v2"
SOURCE_FEATURES = {
    "last10s_last_observed_boundary_return_pct": (
        "percent",
        "RECEIVED_PREFIX_PATH_CONCERN",
    ),
    "previous20s_last_observed_boundary_return_pct": (
        "percent",
        "RECEIVED_PREFIX_PATH_CONCERN",
    ),
    "observed_boundary_return_rate_change_pct_points_per_sec": (
        "percentage_points_per_second",
        "RECEIVED_PREFIX_PATH_CONCERN",
    ),
    "current_from_30s_min_pct": ("percent", "RECEIVED_PREFIX_PATH_CONCERN"),
    "last10s_known_side_buy_qty_pct": ("percent", "RECEIVED_PREFIX_FLOW_CONCERN"),
    "previous20s_known_side_buy_qty_pct": ("percent", "RECEIVED_PREFIX_FLOW_CONCERN"),
    "last10s_known_side_qty_coverage_pct": ("percent", "RECEIVED_PREFIX_FLOW_CONCERN"),
    "previous20s_known_side_qty_coverage_pct": (
        "percent",
        "RECEIVED_PREFIX_FLOW_CONCERN",
    ),
    "known_side_buy_qty_change_pct_points": (
        "percentage_points",
        "RECEIVED_PREFIX_FLOW_CONCERN",
    ),
}


def contract():
    return dict(
        version=VERSION,
        source_sha256=P.file_hash(__file__),
        feature_definition_sha256=P.digest(
            [FEATURES, SOURCE_FEATURES, SOURCE_PREFIX_SCHEMA]
        ),
        observation_boundary="RECEIVED_THROUGH_ORIGINAL_CONFIRMATION",
        source="EXISTING_TYPED_OR_EXACT_FROZEN_RECEIVED_PREFIX_ONLY",
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        broker_order_forbidden=True,
    )


def _check_contract(value):
    if value != contract():
        raise ValueError("causal_prefix_experiment_contract_changed")


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _close(a, b):
    return _finite(a) and _finite(b) and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-8)


def validate_source_prefix(value, logical_input):
    """Check the exact received-prefix producer receipt, without reading raw."""
    identity = {
        "opportunity_key",
        "day",
        "symbol",
        "market",
        "venue",
        "source_item",
        "confirmation_epoch",
        "native_epoch",
        "native_sequence",
    }
    expected_keys = (
        identity
        | set(P.AUTH)
        | {
            "schema",
            "source_receipt",
            "prefix_sha256",
            "observed_prefix_start_epoch",
            "observed_prefix_end_epoch",
            "coverage_seconds",
            "window_complete",
            "windows",
            "price30s",
            "artifact_content_sha256",
        }
    )
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("schema") != SOURCE_PREFIX_SCHEMA
        or any(value.get(k) != v for k, v in P.AUTH.items())
        or value.get("artifact_content_sha256")
        != P.seal(value)["artifact_content_sha256"]
    ):
        raise ValueError("causal_received_prefix_contract_invalid")
    common = logical_input.get("common_context") or {}
    if (
        any(value[k] != common.get(k) for k in identity - {"day", "confirmation_epoch"})
        or value["confirmation_epoch"] != common.get("epoch")
        or value["day"] != str(common.get("as_of", ""))[:10]
        or any(
            type(value[k]) is not int or value[k] < 0
            for k in ("native_epoch", "native_sequence")
        )
    ):
        raise ValueError("causal_received_prefix_identity_changed")
    receipt = value["source_receipt"]
    if (
        not isinstance(receipt, dict)
        or set(receipt) != {"path", "sha256"}
        or not isinstance(receipt["path"], str)
        or not receipt["path"]
        or not re.fullmatch("[a-f0-9]{64}", str(receipt["sha256"]))
        or not re.fullmatch("[a-f0-9]{64}", str(value["prefix_sha256"]))
    ):
        raise ValueError("causal_received_prefix_provenance_invalid")
    t = common.get("epoch")
    start, end = (
        value["observed_prefix_start_epoch"],
        value["observed_prefix_end_epoch"],
    )
    if (
        not _finite(t)
        or not _finite(start)
        or start > t
        or end != t
        or not _close(value["coverage_seconds"], min(30, t - start))
        or type(value["window_complete"]) is not bool
        or value["window_complete"] != (start <= t - 30)
    ):
        raise ValueError("causal_received_prefix_clock_invalid")
    windows = value["windows"]
    if not isinstance(windows, dict) or set(windows) != {"previous20s", "last10s"}:
        raise ValueError("causal_received_prefix_windows_invalid")
    counts = {"observation_count", "positive_qty_observation_count"}
    clocks = {
        "start_epoch",
        "end_epoch",
        "first_observed_epoch",
        "last_observed_epoch",
        "boundary_trade_epoch",
    }
    numeric = {
        "boundary_trade_price",
        "last_trade_price",
        "return_pct",
        "buy_qty",
        "sell_qty",
        "unknown_qty",
        "total_positive_qty",
        "known_side_buy_qty_pct",
        "known_side_qty_coverage_pct",
    }
    for name, bounds in [("previous20s", (t - 30, t - 10)), ("last10s", (t - 10, t))]:
        w = windows[name]
        if (
            not isinstance(w, dict)
            or set(w) != counts | clocks | numeric
            or (w["start_epoch"], w["end_epoch"]) != bounds
            or any(type(w[k]) is not int or w[k] < 0 for k in counts)
            or w["positive_qty_observation_count"] > w["observation_count"]
            or any(w[k] is not None and not _finite(w[k]) for k in numeric)
        ):
            raise ValueError("causal_received_prefix_window_invalid")
        count = w["observation_count"]
        if count:
            if not (
                all(
                    _finite(w[k])
                    for k in ("first_observed_epoch", "last_observed_epoch")
                )
                and bounds[0]
                < w["first_observed_epoch"]
                <= w["last_observed_epoch"]
                <= bounds[1]
            ):
                raise ValueError("causal_received_prefix_window_clock_invalid")
        elif (
            w["first_observed_epoch"] is not None
            or w["last_observed_epoch"] is not None
        ):
            raise ValueError("causal_received_prefix_empty_window_invalid")
        anchor = w["boundary_trade_epoch"]
        if (
            (anchor is None) != (w["boundary_trade_price"] is None)
            or anchor is not None
            and (not _finite(anchor) or not start <= anchor <= bounds[0])
        ):
            raise ValueError("causal_received_prefix_boundary_clock_invalid")
        if not value["window_complete"] or not count:
            if any(w[k] is not None for k in numeric):
                raise ValueError("causal_received_prefix_incomplete_values")
            continue
        if any(
            w[k] is not None and w[k] <= 0
            for k in ("boundary_trade_price", "last_trade_price")
        ):
            raise ValueError("causal_received_prefix_price_invalid")
        boundary, last = w["boundary_trade_price"], w["last_trade_price"]
        expected_ret = (
            100 * (last / boundary - 1)
            if boundary is not None and last is not None
            else None
        )
        if (
            expected_ret is None
            and w["return_pct"] is not None
            or expected_ret is not None
            and not _close(w["return_pct"], expected_ret)
        ):
            raise ValueError("causal_received_prefix_return_invalid")
        qty_keys = ("buy_qty", "sell_qty", "unknown_qty", "total_positive_qty")
        if any(not _finite(w[k]) or w[k] < 0 for k in qty_keys):
            raise ValueError("causal_received_prefix_quantity_invalid")
        buy, sell, unknown, total = (w[k] for k in qty_keys)
        if not _close(total, buy + sell + unknown):
            raise ValueError("causal_received_prefix_quantity_invalid")
        if (w["positive_qty_observation_count"] == 0) != (total == 0):
            raise ValueError("causal_received_prefix_quantity_invalid")
        for key, expected in [
            (
                "known_side_buy_qty_pct",
                100 * buy / (buy + sell) if buy + sell > 0 else None,
            ),
            (
                "known_side_qty_coverage_pct",
                100 * (buy + sell) / total if total > 0 else None,
            ),
        ]:
            if (
                expected is None
                and w[key] is not None
                or expected is not None
                and not _close(w[key], expected)
            ):
                raise ValueError("causal_received_prefix_flow_invalid")
    p = value["price30s"]
    price_fields = {
        "min_trade_price",
        "max_trade_price",
        "last_trade_price",
        "current_from_min_pct",
        "boundary_trade_price",
        "boundary_trade_epoch",
        "return_pct",
    }
    if not isinstance(p, dict) or set(p) != price_fields:
        raise ValueError("causal_received_prefix_price30_invalid")
    if not value["window_complete"]:
        if any(v is not None for v in p.values()):
            raise ValueError("causal_received_prefix_incomplete_values")
    else:
        if (
            any(
                not _finite(p[k]) or p[k] <= 0
                for k in ("min_trade_price", "max_trade_price", "last_trade_price")
            )
            or not p["min_trade_price"] <= p["last_trade_price"] <= p["max_trade_price"]
            or p["last_trade_price"] != common.get("confirmation_price")
            or not _close(
                p["current_from_min_pct"],
                100 * (p["last_trade_price"] / p["min_trade_price"] - 1),
            )
        ):
            raise ValueError("causal_received_prefix_price30_invalid")
        boundary = p["boundary_trade_price"]
        anchor = p["boundary_trade_epoch"]
        if boundary is not None and (not _finite(boundary) or boundary <= 0):
            raise ValueError("causal_received_prefix_price30_invalid")
        if (
            (anchor is None) != (boundary is None)
            or anchor is not None
            and (not _finite(anchor) or not start <= anchor <= t - 30)
        ):
            raise ValueError("causal_received_prefix_boundary_clock_invalid")
        expected_ret = (
            100 * (p["last_trade_price"] / boundary - 1)
            if boundary is not None
            else None
        )
        if (
            expected_ret is None
            and p["return_pct"] is not None
            or expected_ret is not None
            and not _close(p["return_pct"], expected_ret)
        ):
            raise ValueError("causal_received_prefix_price30_invalid")
        last10, previous20 = windows["last10s"], windows["previous20s"]
        if (
            not last10["observation_count"]
            or last10["last_observed_epoch"] != t
            or last10["last_trade_price"] != p["last_trade_price"]
        ):
            raise ValueError("causal_received_prefix_confirmation_price_changed")
        if previous20["observation_count"] and (
            last10["boundary_trade_price"] != previous20["last_trade_price"]
            or last10["boundary_trade_epoch"] != previous20["last_observed_epoch"]
        ):
            raise ValueError("causal_received_prefix_boundary_clock_invalid")
    return value


def _source_features(value):
    last, previous = value["windows"]["last10s"], value["windows"]["previous20s"]
    last_ret, prev_ret = last["return_pct"], previous["return_pct"]
    last_buy, prev_buy = (
        last["known_side_buy_qty_pct"],
        previous["known_side_buy_qty_pct"],
    )
    last_elapsed = (
        last["last_observed_epoch"] - last["boundary_trade_epoch"]
        if last["boundary_trade_epoch"] is not None
        else None
    )
    prev_elapsed = (
        previous["last_observed_epoch"] - previous["boundary_trade_epoch"]
        if previous["boundary_trade_epoch"] is not None
        else None
    )
    return dict(
        last10s_last_observed_boundary_return_pct=last_ret,
        previous20s_last_observed_boundary_return_pct=prev_ret,
        observed_boundary_return_rate_change_pct_points_per_sec=(
            last_ret / last_elapsed - prev_ret / prev_elapsed
            if (
                last_ret is not None
                and prev_ret is not None
                and last_elapsed > 0
                and prev_elapsed > 0
            )
            else None
        ),
        current_from_30s_min_pct=value["price30s"]["current_from_min_pct"],
        last10s_known_side_buy_qty_pct=last_buy,
        previous20s_known_side_buy_qty_pct=prev_buy,
        last10s_known_side_qty_coverage_pct=last["known_side_qty_coverage_pct"],
        previous20s_known_side_qty_coverage_pct=previous["known_side_qty_coverage_pct"],
        known_side_buy_qty_change_pct_points=(
            last_buy - prev_buy
            if last_buy is not None and prev_buy is not None
            else None
        ),
    )


def _features(signal, common):
    """Explain the supplied last-price prefix; never assert later invalidation."""
    prices = signal.get("recent_observed_prices")
    facts = signal.get("facts")
    if not isinstance(prices, list) or not isinstance(facts, dict):
        raise ValueError("causal_prefix_source_missing")
    previous_age = math.inf
    for p in prices:
        if (
            not isinstance(p, dict)
            or not _finite(p.get("age_sec"))
            or p["age_sec"] < 0
            or p["age_sec"] > previous_age
            or not _finite(p.get("price"))
            or p["price"] <= 0
            or p.get("side") not in {"BUY", "SELL", "UNKNOWN"}
            or (p.get("qty") is not None and (not _finite(p["qty"]) or p["qty"] < 0))
        ):
            raise ValueError("causal_prefix_source_invalid")
        previous_age = p["age_sec"]
    ret, spread = facts.get("return_60s_pct"), facts.get("spread_pct")
    if (ret is not None and not _finite(ret)) or not _finite(spread) or spread < 0:
        raise ValueError("causal_prefix_feature_invalid")
    known = sum(
        p["qty"]
        for p in prices
        if p.get("qty") is not None and p["side"] in {"BUY", "SELL"}
    )
    bought = sum(
        p["qty"] for p in prices if p.get("qty") is not None and p["side"] == "BUY"
    )
    complete_qty = bool(prices) and all(p.get("qty") is not None for p in prices)
    total = sum(p["qty"] for p in prices) if complete_qty else None
    proof = signal.get("observed_signal") or {}
    root_epoch, root_price = proof.get("epoch"), proof.get("price")
    confirmation_epoch, confirmation_price = common.get("epoch"), common.get(
        "confirmation_price"
    )
    root_available = all(
        _finite(v)
        for v in (root_epoch, root_price, confirmation_epoch, confirmation_price)
    )
    if root_available and (
        root_price <= 0 or confirmation_price <= 0 or root_epoch > confirmation_epoch
    ):
        raise ValueError("causal_prefix_root_clock_invalid")
    root_age = confirmation_epoch - root_epoch if root_available else None
    root_covered = bool(
        root_available
        and prices
        and prices[0]["age_sec"] >= root_age
        and prices[-1]["age_sec"] == 0
    )
    # Prices carry ages but no native sequences. Multiple root-clock rows cannot
    # establish which same-clock observations precede the signal root.
    root_boundary = [p for p in prices if root_available and p["age_sec"] == root_age]
    root_boundary_unambiguous = bool(
        root_covered
        and len(root_boundary) == 1
        and root_boundary[0]["price"] == root_price
    )
    root_rows = [p for p in prices if root_available and p["age_sec"] <= root_age]
    root_exact = root_covered and root_boundary_unambiguous
    root_flow_complete = bool(
        root_exact
        and root_rows
        and all(
            p.get("qty") is not None and p["side"] in {"BUY", "SELL"} for p in root_rows
        )
    )
    root_qty = sum(p["qty"] for p in root_rows) if root_flow_complete else None
    values = dict(
        observed_prefix_return_pct=(
            100 * (prices[-1]["price"] / prices[0]["price"] - 1)
            if len(prices) >= 2
            else None
        ),
        observed_prefix_giveback_pct=(
            100 * (prices[-1]["price"] / max(p["price"] for p in prices) - 1)
            if len(prices) >= 2
            else None
        ),
        known_side_buy_qty_share_pct=100 * bought / known if known > 0 else None,
        known_side_qty_coverage_pct=(
            100 * known / total if total is not None and total > 0 else None
        ),
        return_60s_minus_spread_pct=ret - spread if ret is not None else None,
        root_to_confirmation_return_pct=(
            100 * (confirmation_price / root_price - 1) if root_available else None
        ),
        root_interval_min_change_pct=(
            100 * (min(p["price"] for p in root_rows) / root_price - 1)
            if root_exact
            else None
        ),
        root_interval_buy_qty_share_pct=(
            100 * sum(p["qty"] for p in root_rows if p["side"] == "BUY") / root_qty
            if root_qty is not None and root_qty > 0
            else None
        ),
    )
    if any(v is not None and not _finite(v) for v in values.values()):
        raise ValueError("causal_prefix_derived_feature_invalid")
    return values, dict(
        observations=len(prices),
        oldest_age_sec=prices[0]["age_sec"] if prices else None,
        newest_age_sec=prices[-1]["age_sec"] if prices else None,
        observed_span_sec=(
            prices[0]["age_sec"] - prices[-1]["age_sec"] if prices else None
        ),
        complete_quantity_observation=complete_qty,
        root_age_sec=root_age,
        root_interval_covered=root_covered,
        root_clock_boundary_unambiguous=root_boundary_unambiguous,
        root_flow_complete=root_flow_complete,
        source_prefix_sha256=P.digest(prices),
    )


def project(logical_input, *, expected_contract=None, source_prefix=None):
    """Add deterministic diagnostic facts, preserving every original field."""
    _check_contract(contract() if expected_contract is None else expected_contract)
    if (
        not isinstance(logical_input, dict)
        or logical_input.get("schema") != U.VERSION
        or not logical_input.get("signals")
        or "causal_prefix_evidence" in logical_input
    ):
        raise ValueError("causal_prefix_input_unsupported")
    result = copy.deepcopy(logical_input)
    setup = result["entry_setup_evidence_v1"]
    existing = {
        f["id"]
        for k in ("positive_facts", "context_facts", "contradicting_facts")
        for f in setup[k]
    }
    rows = []
    for signal in result["signals"]:
        values, coverage = _features(signal, result.get("common_context") or {})
        ref = signal["ref"]
        rows.append(
            dict(
                signal_ref=ref,
                values=values,
                coverage=coverage,
                source_signal_sha256=P.digest(signal),
            )
        )
        for name, (unit, risk) in FEATURES.items():
            value = values[name]
            if value is None:
                continue
            fid = ref + "/" + VERSION + "/" + name
            if fid in existing:
                raise ValueError("causal_prefix_fact_identity_conflict")
            existing.add(fid)
            setup["context_facts"].append(dict(id=fid, value=value, unit=unit))
            setup["risk_fact_bindings"].setdefault(risk, []).append(fid)
    result["causal_prefix_evidence"] = dict(
        schema=VERSION,
        original_logical_input_sha256=P.digest(logical_input),
        per_signal=rows,
        interpretation="Derived descriptions of the supplied prefix, not independent signals or post-confirmation failure.",
        risk_bindings_are_vocabulary_only=True,
        feature_contract=contract(),
    )
    if source_prefix is not None:
        evidence = validate_source_prefix(source_prefix, logical_input)
        values = _source_features(evidence)
        result["causal_prefix_evidence"]["received_prefix"] = dict(
            schema=SOURCE_PREFIX_SCHEMA,
            source_evidence_sha256=evidence["artifact_content_sha256"],
            prefix_sha256=evidence["prefix_sha256"],
            source_sha256=evidence["source_receipt"]["sha256"],
            coverage_seconds=evidence["coverage_seconds"],
            window_complete=evidence["window_complete"],
            values=values,
            interpretation=(
                "Window completeness is observed valid-segment coverage, not complete market reception. "
                "Returns use the last observed trade at or before the boundary, not a print at the exact boundary; "
                "anchor ages and actual elapsed clocks apply. Return-rate change uses actual anchor-to-last elapsed "
                "seconds, not nominal window durations. A single observation is not an observed price sequence. "
                "Quantities and sides describe received observations only, not total market volume. "
                "An empty window leaves market activity unknown; a gap does not prove signal failure or an API defect."
            ),
            windows={
                k: dict(
                    {
                        name: w[name]
                        for name in (
                            "start_epoch",
                            "end_epoch",
                            "observation_count",
                            "positive_qty_observation_count",
                            "first_observed_epoch",
                            "last_observed_epoch",
                            "boundary_trade_epoch",
                        )
                    },
                    boundary_observation_age_sec=(
                        w["start_epoch"] - w["boundary_trade_epoch"]
                        if w["boundary_trade_epoch"] is not None
                        else None
                    ),
                )
                for k, w in evidence["windows"].items()
            },
            price30s_boundary_observation_age_sec=(
                evidence["confirmation_epoch"]
                - 30
                - evidence["price30s"]["boundary_trade_epoch"]
                if evidence["price30s"]["boundary_trade_epoch"] is not None
                else None
            ),
        )
        for name, (unit, risk) in SOURCE_FEATURES.items():
            if values[name] is None:
                continue
            fid = SOURCE_PREFIX_SCHEMA + "/" + name
            if fid in existing:
                raise ValueError("causal_prefix_fact_identity_conflict")
            existing.add(fid)
            setup["context_facts"].append(dict(id=fid, value=values[name], unit=unit))
            setup["risk_fact_bindings"].setdefault(risk, []).append(fid)
    # Codec validation catches duplicate IDs and missing/unknown risk bindings.
    W.encode(result)
    return result


def validate_projected(
    original, projected, *, expected_contract=None, source_prefix=None
):
    wanted = project(
        original, expected_contract=expected_contract, source_prefix=source_prefix
    )
    if wanted != projected:
        raise ValueError("causal_prefix_evidence_changed")
    return projected


def transform_request(req, logical_input, *, contract, source_prefix=None):
    """Rebuild a frozen compact request for this explicit offline input arm.

    Call ``project(original)`` again when decoding/evaluating its raw response;
    the parent registry stays unchanged and cannot identify this experiment as
    a runtime-compatible registered policy.
    """
    _check_contract(contract)
    transformed = project(
        logical_input, expected_contract=contract, source_prefix=source_prefix
    )
    result = copy.deepcopy(req)
    candidate = result["candidate"]
    compact_fields = [("compact_runtime_contract", W), ("compact_wire_contract", OLD_W)]
    present = [
        (field, codec) for field, codec in compact_fields if candidate.get(field)
    ]
    if len(present) > 1:
        raise ValueError("causal_prefix_multiple_wire_contracts")
    codec = present[0][1] if present else None
    if codec:
        field = present[0][0]
        _, original_schema, original_aliases = codec.encode(logical_input)
        if (
            candidate[field] != codec.contract()
            or candidate.get("logical_input_sha256") != P.digest(logical_input)
            or req["candidate_input"] != codec.encode(logical_input)[0]
            or candidate.get("response_schema") != original_schema
            or candidate.get("citation_map_sha256") != P.digest(original_aliases)
            or not candidate["system_prompt"].endswith(codec.SUFFIX)
        ):
            raise ValueError("causal_prefix_original_request_changed")
        candidate["system_prompt"] = candidate["system_prompt"][: -len(codec.SUFFIX)]
        for key in (field, "logical_input_sha256", "citation_map_sha256"):
            candidate.pop(key, None)
    elif req.get("candidate_input") != logical_input:
        raise ValueError("causal_prefix_original_request_changed")
    elif candidate.get("response_schema") != U.response_schema(logical_input):
        raise ValueError("causal_prefix_original_request_changed")
    if "candidate_input_sha256" in req and req["candidate_input_sha256"] != P.digest(
        req["candidate_input"]
    ):
        raise ValueError("causal_prefix_original_request_changed")
    for key in ("response_schema_sha256", "response_schema_instance_sha256"):
        if key in req["candidate"] and req["candidate"][key] != P.digest(
            req["candidate"]["response_schema"]
        ):
            raise ValueError("causal_prefix_original_request_changed")
    schema = U.response_schema(transformed)
    result.update(
        candidate_input=transformed, candidate_input_sha256=P.digest(transformed)
    )
    candidate.update(
        response_schema=schema,
        response_schema_sha256=P.digest(schema),
        response_schema_instance_sha256=P.digest(schema),
        schema_name=U.VERSION,
        offline_causal_prefix_contract=contract,
        original_logical_input_sha256=P.digest(logical_input),
    )
    candidate.pop("contract_sha256", None)
    result["paired_replay_id"] = P.digest(
        [
            req["paired_replay_id"],
            VERSION,
            contract,
            {
                k: result[k]
                for k in ("candidate_input", "candidate", "control", "stage")
            },
        ]
    )
    if codec:
        result = codec.request(result, transformed, codec.contract())
    return result
