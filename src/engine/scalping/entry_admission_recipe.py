"""Shared frozen admission recipe; pure facts and no broker or publisher I/O.

Owned by the existing Main entry evaluator and offline replay adapters. The
recipe is enabled only by an explicitly validated machine policy component.
"""

from copy import deepcopy
import math
from src.engine.scalping import entry_strategy_policy as S

RECIPE_ID = "pullback_p60_v0"
POLICY_SCHEMA = "main_entry_admission_recipe_v1"
DECISION_SCHEMA = "main_entry_admission_recipe_decision_v1"
SOFT_CONFIRMATION = frozenset(
    {
        "trigger_confirmation_missing",
        "volume_confirmation_missing",
        "micro_continuation_unconfirmed",
        "no_supported_setup",
    }
)
CONFIRMATION_SCHEMA = "main_entry_machine_confirmation_v1"
CONFIRMATION_FACTS = (
    "registered_machine_recipe_confirmed",
    "trusted_buy_flow_at_or_below_vwap",
)
CONFIRMATION_RULE = (
    "The selected recipe confirms trusted buy flow at or below micro VWAP. "
    "Keep the legacy setup unchanged. The two registered fact IDs supply recipe "
    "setup and trigger support. They resolve only resolved_legacy_fact_ids. "
    "Consider and cite every bound adverse fact. PASS requires NO_BLOCKING_RISK "
    "as its sole risk code and both registered support IDs. Actual recipe "
    "confirmation gaps, other adverse risks, source and hard guards remain binding."
)


def number(value):
    return (
        float(value) if type(value) in (int, float) and math.isfinite(value) else None
    )


def contract(parent):
    return dict(
        schema=POLICY_SCHEMA,
        recipe_id=RECIPE_ID,
        exact_scope=["KRX", "KRX_REGULAR"],
        symbol_predicate="exclude_005930",
        admission_mode="replace",
        parent_policy_sha256=S.digest(parent),
        parameters=dict(
            minimum_buy_pressure_10t=60,
            maximum_buy_pressure_10t=100,
            minimum_trusted_tick_count=10,
            maximum_micro_vwap_bp=0,
            net_aggressive_delta_comparison="strictly_positive",
        ),
        source_quality_contract="parent_guards_and_original_raw_capture",
        counterweight_fact_ids=sorted(SOFT_CONFIRMATION),
    )


def validate(value, parent):
    try:
        valid = isinstance(value, dict) and S.digest(value) == S.digest(
            contract(parent)
        )
    except (ValueError, TypeError, OverflowError):
        valid = False
    return [] if valid else ["entry_admission_recipe_contract_invalid"]


def candidate_policy(parent):
    result = deepcopy(parent)
    result.pop("entry_admission_recipe", None)
    result["entry_admission_recipe"] = contract(result)
    return result


def condition(raw):
    """The previously selected p60/v0 rule; no action or outcome inputs."""
    if not isinstance(raw, dict) or not isinstance(raw.get("features"), dict):
        return False
    f = raw["features"]
    pressure, delta, vwap, trusted = (
        number(f.get(k))
        for k in (
            "buy_pressure_10t",
            "net_aggressive_delta_10t",
            "curr_vs_micro_vwap_bp",
            "tick_aggressor_trusted_count",
        )
    )
    return bool(
        pressure is not None
        and 60 <= pressure <= 100
        and delta is not None
        and delta > 0
        and vwap is not None
        and vwap <= 0
        and trusted is not None
        and trusted >= 10
        and f.get("tick_aggressor_pressure_usable") is True
        and f.get("tick_context_stale") is False
        and f.get("quote_stale") is False
        and f.get("micro_vwap_available") is True
    )


def bind_confirmation(setup, policy):
    """Seal selected confirmation separately from unchanged legacy setup facts."""
    from src.engine.scalping.entry_setup_evidence import (
        mechanistic_entry_policy_decision,
        validate_entry_setup_evidence,
    )

    if not isinstance(policy, dict) or "entry_admission_recipe" not in policy:
        return deepcopy(setup)
    errors = validate_entry_setup_evidence(setup)
    if errors:
        raise ValueError("machine_confirmation_setup_invalid:" + ",".join(errors))
    original = deepcopy(setup)
    previous = original.pop("machine_confirmation", None)
    if previous:
        original["evidence_sha256"] = previous["original_setup_sha256"]
    decision = mechanistic_entry_policy_decision(original, policy=policy)
    receipt = decision.get("admission_recipe") or {}
    if (
        decision.get("action") != "ENTER_NOW"
        or decision.get("admission_recipe_trigger_pass") is not True
        or receipt.get("condition_match") is not True
        or receipt.get("unresolved_reasons")
    ):
        return original
    ledger = dict(
        schema=CONFIRMATION_SCHEMA,
        recipe_id=RECIPE_ID,
        version=1,
        policy_sha256=S.digest(policy),
        source_sha256=original["strategy_raw_sha256"],
        original_setup_sha256=original["evidence_sha256"],
        decision_receipt_sha256=S.digest(receipt),
        action="ENTER_NOW",
        screen_rule=CONFIRMATION_RULE,
        fact_ids=list(CONFIRMATION_FACTS),
        values={
            k: original["strategy_raw_input"]["features"][k]
            for k in (
                "buy_pressure_10t",
                "net_aggressive_delta_10t",
                "curr_vs_micro_vwap_bp",
                "tick_aggressor_trusted_count",
            )
        },
        resolved_legacy_fact_ids=sorted(
            row["original"]["fact_id"]
            for row in receipt["fact_ledger"]
            if row.get("proposed_counterweight")
        ),
    )
    ledger["confirmation_sha256"] = S.digest(ledger)
    result = {**original, "machine_confirmation": ledger}
    result["evidence_sha256"] = S.digest(
        {k: v for k, v in result.items() if k != "evidence_sha256"}
    )
    return result


def confirmation_facts(setup):
    """Wire-schema projection; the full consumer additionally recomputes policy."""
    ledger = setup.get("machine_confirmation") or {}
    if not isinstance(ledger, dict):
        return []
    if (
        ledger.get("schema") == CONFIRMATION_SCHEMA
        and ledger.get("recipe_id") == RECIPE_ID
        and ledger.get("version") == 1
        and ledger.get("action") == "ENTER_NOW"
        and ledger.get("fact_ids") == list(CONFIRMATION_FACTS)
        and ledger.get("confirmation_sha256")
        == S.digest({k: v for k, v in ledger.items() if k != "confirmation_sha256"})
    ):
        return list(CONFIRMATION_FACTS)
    return []


def validate_confirmation(setup):
    if "machine_confirmation" not in setup:
        return []
    ledger = setup["machine_confirmation"]
    if not isinstance(ledger, dict):
        return ["entry_machine_confirmation_invalid"]
    original = {
        k: v
        for k, v in setup.items()
        if k not in {"machine_confirmation", "evidence_sha256"}
    }
    raw = original.get("strategy_raw_input") or {}
    valid = (
        confirmation_facts(setup)
        and isinstance(raw, dict)
        and condition(raw)
        and ledger.get("original_setup_sha256") == S.digest(original)
        and ledger.get("source_sha256") == S.digest(raw)
        and ledger.get("source_sha256") == setup.get("strategy_raw_sha256")
        and ledger.get("values")
        == {
            k: (raw.get("features") or {}).get(k)
            for k in (
                "buy_pressure_10t",
                "net_aggressive_delta_10t",
                "curr_vs_micro_vwap_bp",
                "tick_aggressor_trusted_count",
            )
        }
    )
    return [] if valid else ["entry_machine_confirmation_invalid"]


def evaluate(setup, parent, *, baseline, situation_veto):
    """Replace entry admission in exact non-Samsung KRX regular scope.

    A distinct pullback setup may resolve the enumerated soft confirmations.
    Every other original risk disposition and all parent hard guards survive.
    The original breakout/family/price-response facts are not edited.
    """
    raw = setup.get("strategy_raw_input")
    if not isinstance(raw, dict) or setup.get("strategy_raw_sha256") != S.digest(raw):
        raise ValueError("pullback_raw_capture_invalid")
    rebuilt = baseline.get("effective_setup_evidence") or setup
    scope = (
        str(raw.get("stock_code") or "").isdigit()
        and len(str(raw.get("stock_code") or "")) == 6
        and raw["stock_code"] != "005930"
        and str(raw.get("effective_venue") or "").upper() == "KRX"
        and str(raw.get("session_bucket") or "").upper() == "KRX_REGULAR"
    )
    matched = bool(scope and condition(raw))
    ledger = []
    for risk in baseline["core_comparison"]["risk_assessments"]:
        existing = risk["disposition"] == "COMPENSATED"
        proposed = bool(
            matched
            and risk["disposition"] == "RECHECKABLE"
            and risk["risk_code"] == "CONFIRMATION_MISSING"
            and risk["fact_id"] in SOFT_CONFIRMATION
        )
        ledger.append(
            dict(
                original=deepcopy(risk),
                existing_resolved=existing,
                proposed_counterweight="trusted_buy_flow_at_or_below_vwap"
                if proposed
                else None,
                resolved=existing or proposed,
            )
        )
    reasons = []
    if not scope:
        reasons.append("outside_scope_parent_inherited")
    if not matched:
        reasons.append("frozen_condition_not_met")
    if baseline["action"] == "BLOCK":
        reasons.append("parent_block_preserved")
    if rebuilt.get("invalidation_facts"):
        reasons.append("invalidation_preserved")
    if (rebuilt.get("source_quality") or {}).get("status") != "fresh_consistent":
        reasons.append("parent_source_guard_preserved")
    if (
        baseline.get("liquidity_inputs_complete") is not True
        or baseline.get("liquidity_threshold_pass") is not True
    ):
        reasons.append("parent_liquidity_guard_preserved")
    thresholds = (baseline.get("strategy_selection") or {}).get(
        "effective_thresholds"
    ) or {}
    if thresholds.get("micro_confirmation_recipe", 0) != 0:
        reasons.append("parent_micro_recipe_preserved")
    if any(not row["resolved"] for row in ledger):
        reasons.append("unresolved_risk_facts")
    proposed = baseline["action"]
    if scope and proposed == "ENTER_NOW" and reasons:
        proposed = "RECHECK"
    if scope and baseline["action"] == "RECHECK" and not reasons:
        proposed = situation_veto({**baseline, "action": "ENTER_NOW"}, setup, parent)[
            "action"
        ]
        if proposed != "ENTER_NOW":
            reasons.append("parent_situation_veto_preserved")
    return dict(
        schema=DECISION_SCHEMA,
        parent_sha256=S.digest(parent),
        original_raw_sha256=setup["strategy_raw_sha256"],
        parent_action=baseline["action"],
        parent_reason=baseline["reason"],
        proposed_action=proposed,
        condition_match=matched,
        changed=proposed != baseline["action"],
        unresolved_reasons=reasons,
        fact_ledger=ledger,
        original_setup_family=rebuilt.get("setup_family"),
        original_setup_state=rebuilt.get("setup_state"),
        original_local_breakout=deepcopy(rebuilt.get("local_breakout")),
        proposed_setup_family="PULLBACK_BUY_FLOW" if matched else None,
    )
