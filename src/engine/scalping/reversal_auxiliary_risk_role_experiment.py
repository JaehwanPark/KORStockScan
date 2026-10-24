"""Offline spread-role and risk-vocabulary ablations; no runtime publication.

Existing prompt/model/transport and observed values stay fixed. These are
branch-conditional interventions, not a balanced factorial interaction test.
"""

from __future__ import annotations

import copy
import math

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W

VERSION = "auxiliary_risk_role_ablation_v1"
MODES = frozenset({"BASELINE", "ROLE", "VOCAB", "ROLE_VOCAB", "ROLE_VOCAB_PATH"})
SPREAD_NAMES = frozenset({"observed_spread", "observable_wide_spread"})
PATH_UNITS = dict(
    target_gap_from_confirmation_trade_pct="percent",
    ask_premium_to_confirmation_trade_pct="percent",
    observed_recent_return_pct="percent",
    observed_recent_return_minus_target_gap_pct_points="percentage_points",
)


def contract(mode):
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError("risk_role_mode_invalid")
    return dict(
        version=VERSION,
        mode=mode,
        source_sha256=P.file_hash(__file__),
        definition_sha256=P.digest([sorted(SPREAD_NAMES), PATH_UNITS]),
        boundary="ORIGINAL_CONFIRMATION_PREFIX_ONLY",
        **P.AUTH,
    )


def _checked(value):
    if (
        not isinstance(value, dict)
        or value != contract(value.get("mode"))
        or any(value.get(k) is not v for k, v in P.AUTH.items())
    ):
        raise ValueError("risk_role_contract_changed")
    return value["mode"]


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _path(signal, common):
    objective = common.get("objective")
    if objective != dict(
        net_target_pct=0.4,
        net_soft_stop_pct=-3.0,
        horizon_seconds=1800,
        cost_rate=0.0023,
    ):
        raise ValueError("risk_role_path_objective_changed")
    ask, trade = common.get("entry_ask"), common.get("confirmation_price")
    if not all(_finite(v) and v > 0 for v in (ask, trade)):
        raise ValueError("risk_role_path_quote_invalid")
    facts = signal["facts"]
    if facts.get("entry_ask") != ask or facts.get("confirmation_price") != trade:
        raise ValueError("risk_role_path_quote_conflict")
    prices = signal.get("recent_observed_prices")
    if not isinstance(prices, list):
        raise ValueError("risk_role_path_prefix_missing")
    age = math.inf
    for row in prices:
        if (
            not isinstance(row, dict)
            or not _finite(row.get("age_sec"))
            or row["age_sec"] < 0
            or row["age_sec"] > age
            or not _finite(row.get("price"))
            or row["price"] <= 0
        ):
            raise ValueError("risk_role_path_prefix_invalid")
        age = row["age_sec"]
    gap = 100 * (ask * 1.004 / 0.9977 / trade - 1)
    ret = (
        100 * (prices[-1]["price"] / prices[0]["price"] - 1)
        if len(prices) >= 2
        else None
    )
    values = dict(
        target_gap_from_confirmation_trade_pct=gap,
        ask_premium_to_confirmation_trade_pct=100 * (ask / trade - 1),
        observed_recent_return_pct=ret,
        observed_recent_return_minus_target_gap_pct_points=(
            ret - gap if ret is not None else None
        ),
    )
    if any(v is not None and not _finite(v) for v in values.values()):
        raise ValueError("risk_role_path_derived_invalid")
    return values, dict(
        observed_recent_price_count=len(prices),
        observed_recent_span_sec=(
            prices[0]["age_sec"] - prices[-1]["age_sec"] if prices else None
        ),
    )


def project(logical_input, *, expected_contract):
    mode = _checked(expected_contract)
    if (
        not isinstance(logical_input, dict)
        or logical_input.get("schema") != U.VERSION
        or not isinstance(logical_input.get("signals"), list)
        or not logical_input["signals"]
    ):
        raise ValueError("risk_role_input_unsupported")
    W.encode(logical_input)
    result = copy.deepcopy(logical_input)
    if mode == "BASELINE":
        return result
    setup = result["entry_setup_evidence_v1"]
    byref = {s["ref"]: s for s in result["signals"]}
    if len(byref) != len(result["signals"]):
        raise ValueError("risk_role_signal_identity_invalid")
    if any(
        not isinstance(s.get("facts"), dict)
        or not _finite(s["facts"].get("spread_pct"))
        or s["facts"]["spread_pct"] < 0
        for s in byref.values()
    ):
        raise ValueError("risk_role_spread_value_invalid")
    existing = {
        f["id"]
        for field in ("positive_facts", "context_facts", "contradicting_facts")
        for f in setup[field]
    }

    def add(fid, value, unit, risk=None):
        if fid in existing:
            raise ValueError("risk_role_fact_identity_conflict")
        existing.add(fid)
        setup["context_facts"].append(dict(id=fid, value=value, unit=unit))
        if risk:
            setup["risk_fact_bindings"].setdefault(risk, []).append(fid)

    if mode in {"ROLE", "ROLE_VOCAB", "ROLE_VOCAB_PATH"}:
        kept = []
        for fact in setup["contradicting_facts"]:
            ref, _, name = fact["id"].rpartition("/")
            if name in SPREAD_NAMES:
                if (
                    ref not in byref
                    or not _finite(fact.get("value"))
                    or fact["value"] != byref[ref]["facts"].get("spread_pct")
                ):
                    raise ValueError("risk_role_spread_fact_conflict")
                setup["context_facts"].append(fact)
            else:
                kept.append(fact)
        setup["contradicting_facts"] = kept
    if mode in {"VOCAB", "ROLE_VOCAB", "ROLE_VOCAB_PATH"}:
        for ref, signal in byref.items():
            spread = signal["facts"].get("spread_pct")
            if not _finite(spread) or spread < 0:
                raise ValueError("risk_role_spread_value_invalid")
            if not signal["policy_id"].startswith("legacy_") or spread == 0:
                continue
            fid = ref + "/risk_role_observed_spread"
            add(fid, spread, "percent", "ENTRY_SPREAD_CONCERN")
    if mode == "ROLE_VOCAB_PATH":
        common = result.get("common_context") or {}
        for ref, signal in byref.items():
            values, coverage = _path(signal, common)
            for name, value in values.items():
                if value is not None:
                    add(
                        ref + "/observed_target_progress_v1/" + name,
                        value,
                        PATH_UNITS[name],
                        "OBSERVED_TARGET_PROGRESS_CONCERN",
                    )
            # Count/span expose what was actually supplied, including an empty
            # prefix. They are not bound as risk or replaced by invented prices.
            for name, value in coverage.items():
                if value is not None:
                    add(
                        ref + "/observed_target_progress_v1/" + name,
                        value,
                        "count" if name.endswith("count") else "seconds",
                    )
    W.encode(result)
    return result


def transform_request(req, logical_input, *, contract):
    _checked(contract)
    transformed = project(logical_input, expected_contract=contract)
    result = copy.deepcopy(req)
    candidate = result["candidate"]
    present = [
        (field, codec)
        for field, codec in [
            ("compact_runtime_contract", W),
            ("compact_wire_contract", OLD_W),
        ]
        if candidate.get(field)
    ]
    if len(present) > 1:
        raise ValueError("risk_role_multiple_wire_contracts")
    codec = present[0][1] if present else None
    if codec:
        field = present[0][0]
        wire, schema, aliases = codec.encode(logical_input)
        if (
            candidate[field] != codec.contract()
            or req.get("candidate_input") != wire
            or candidate.get("logical_input_sha256") != P.digest(logical_input)
            or candidate.get("response_schema") != schema
            or candidate.get("citation_map_sha256") != P.digest(aliases)
            or not candidate["system_prompt"].endswith(codec.SUFFIX)
        ):
            raise ValueError("risk_role_original_request_changed")
        candidate["system_prompt"] = candidate["system_prompt"][: -len(codec.SUFFIX)]
        for key in (field, "logical_input_sha256", "citation_map_sha256"):
            candidate.pop(key, None)
    elif req.get("candidate_input") != logical_input or candidate.get(
        "response_schema"
    ) != U.response_schema(logical_input):
        raise ValueError("risk_role_original_request_changed")
    if "candidate_input_sha256" in req and req["candidate_input_sha256"] != P.digest(
        req["candidate_input"]
    ):
        raise ValueError("risk_role_original_request_changed")
    for key in ("response_schema_sha256", "response_schema_instance_sha256"):
        if key in req["candidate"] and req["candidate"][key] != P.digest(
            req["candidate"]["response_schema"]
        ):
            raise ValueError("risk_role_original_request_changed")
    # A conditional intervention may be a genuine no-op for this signal
    # family. Never buy another response for the unchanged effective request.
    if transformed == logical_input:
        return copy.deepcopy(req)
    effective_contract = {k: v for k, v in contract.items() if k != "mode"}
    schema = U.response_schema(transformed)
    result.update(
        candidate_input=transformed, candidate_input_sha256=P.digest(transformed)
    )
    candidate.update(
        response_schema=schema,
        response_schema_sha256=P.digest(schema),
        response_schema_instance_sha256=P.digest(schema),
        schema_name=U.VERSION,
        offline_risk_role_contract=effective_contract,
        original_logical_input_sha256=P.digest(logical_input),
    )
    candidate.pop("contract_sha256", None)
    result["paired_replay_id"] = P.digest(
        [
            req["paired_replay_id"],
            VERSION,
            effective_contract,
            {
                k: result[k]
                for k in ("candidate_input", "candidate", "control", "stage")
            },
        ]
    )
    return codec.request(result, transformed, codec.contract()) if codec else result
