"""Opt-in, as-of-only auxiliary contract for a confirmed first price uptick.

Pure input/prompt/schema functions. No provider, policy publication or orders.
The continuous-reversal producer must bind this contract before live use.
"""

from __future__ import annotations

import copy
import math

VERSION = "continuous_reversal_auxiliary_v4"
CONTEXT_IDS = frozenset({
    "recent_sell_pressure", "negative_short_momentum", "below_recent_vwap",
    "volume_not_expanding",
})
FEATURES = (
    "buy_pressure_10t", "buy_pressure_30s", "return_10t_pct",
    "vs_vwap_60s_pct", "spread_pct", "confirmation_pct", "volume_ratio_60s",
    "drop_pct", "drawdown_5m_pct", "decline_seconds", "confirmation_price",
    "low_price", "entry_ask", "down_steps",
)
FACT_IDS = CONTEXT_IDS | {
    "observed_price_decline", "first_price_uptick", "observed_drawdown_state",
    "recent_buy_pressure", "observable_wide_spread", "rebound_already_consumed",
}

PROMPT = """Assess a machine-confirmed first price uptick after a decline.
The event of interest is net +0.4% within 30 minutes from the current entry ask,
before net -3.0%. Use the supplied cost exactly once. Judge event likelihood,
not expected profit, reward/risk, a larger target or a desired PASS frequency.
The machine owns price-turn detection. Do not require another uptick, positive
momentum, a buy-pressure threshold, VWAP reclaim, or increased volume as a
second compulsory setup. One uptick also does not guarantee eventual success.

Read the timeline correctly. Rolling tape and VWAP measures END AT the first
uptick and may include it. They mix the preceding decline with the trigger;
they are NOT measurements of a failed rebound after the trigger. There are no
later observations. Negative rolling context is retained, not erased or made
positive. Several overlapping weak measures are not independent confirmations
that the current price turn failed. Context can inform your assessment in
combination with the current entry facts; it is not an automatic veto.

Compare the measured decline and actual first uptick with the current ask,
observed spread and rebound already consumed. PASS when supplied facts support
this small-target opportunity without a material current blocking issue.
CAUTION means a concrete unresolved issue at THIS entry, not a generic request
for all lagging indicators to improve. VETO requires a material fact-based
reason. Never invent post-trigger selling, renewed low breaks, insufficient
depth, news, or future prices. Optional unknowns are neutral, not source gaps.
INSUFFICIENT is only for an explicitly supplied essential input gap.

Return only the six-field JSON. For PASS use risk_codes=["NO_BLOCKING_RISK"]
and cite first_price_uptick plus observed_price_decline or observed_drawdown_state.
For CAUTION or VETO use a supplied risk code (never NO_BLOCKING_RISK), with a
matching contradicting_fact_ids citation. Context-only concerns use
EARLY_REVERSAL_FRAGILE and their exact context IDs; do not label them confirmed
post-trigger invalidation. Do not emit CAUTION with NO_BLOCKING_RISK.
All citations must exist. Confidence is diagnostic, not an entry gate.
This is offline counterfactual research, not historical entry or order authority.
"""

HURDLE_SUFFIX = """
The entry_geometry fields make the present price reference explicit. The target
gap from the observed trade includes any ask premium and the stated cost.
Do not add spread or cost again. A large rebound already consumed or a wide
spread may weaken the opportunity; neither has a new fixed threshold here.
"""

CITATION_SUFFIX = """
Field meaning: contradicting_fact_ids contains ANY supplied fact behind your
reservation, including context_facts. It does not assert post-trigger failure.
If CAUTION or VETO cites EARLY_REVERSAL_FRAGILE, copy at least one context fact
ID from that code's risk_fact_bindings into contradicting_fact_ids. Leaving
that list empty while naming a risk is inconsistent. When no present concern
can be grounded in any supplied fact, do not invent one to avoid PASS.
Format example only, not an instruction to choose this verdict:
{"schema":"entry_setup_risk_adjudication_v1","risk_verdict":"CAUTION",
"risk_codes":["EARLY_REVERSAL_FRAGILE"],"supporting_fact_ids":
["first_price_uptick"],"contradicting_fact_ids":["recent_sell_pressure"],
"confidence":50}
Only use the example's fact ID if it exists in this input.
"""


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def build_input(source: dict, *, geometry: bool = False, production: bool = False) -> dict:
    """Project only known as-of fields; never forward arbitrary source metadata."""
    setup = source["entry_setup_evidence_v1"]
    facts = {key: copy.deepcopy(setup["facts"][key]) for key in FEATURES}
    if any(value is not None and not _finite(value) for value in facts.values()):
        raise ValueError('non_numeric_reversal_feature')
    for key in ("entry_ask", "confirmation_price", "low_price", "confirmation_pct"):
        if not _finite(facts[key]) or facts[key] <= 0:
            raise ValueError("essential_reversal_value_invalid:" + key)
    if facts["confirmation_price"] <= facts["low_price"]:
        raise ValueError("first_uptick_not_present")
    if source["mechanistic_entry_assessment"].get("price_reversal_confirmed") is not True:
        raise ValueError("machine_price_reversal_not_confirmed")
    if setup.get("source_quality") != "price_and_entry_quote_valid":
        raise ValueError("essential_source_quality_invalid")
    # Values are immutable. IDs determine roles, not wins or previous AI answers.
    positives = copy.deepcopy(setup["positive_facts"])
    original = copy.deepcopy(setup["contradicting_facts"] + setup.get("context_facts", []))
    for fact in positives + original:
        if fact.get("id") not in FACT_IDS:
            raise ValueError("unsupported_fact_id")
        # Do not accidentally transmit newly attached labels through fact objects.
        if set(fact) - {"id", "value", "unit", "source_feature", "disposition"}:
            raise ValueError("unexpected_fact_metadata")
        if fact.get('value') is not None and not _finite(fact['value']):
            raise ValueError('non_numeric_fact_value')
        if fact.get('source_feature') is not None and fact['source_feature'] not in FEATURES:
            raise ValueError('unsupported_fact_source_feature')
    contexts = [f for f in original if f["id"] in CONTEXT_IDS]
    active = [f for f in original if f["id"] not in CONTEXT_IDS]
    active_ids = {f["id"] for f in active}
    bindings = {code: [fid for fid in ids if fid in active_ids]
                for code, ids in setup["risk_fact_bindings"].items()
                if any(fid in active_ids for fid in ids)}
    if contexts:
        bindings["EARLY_REVERSAL_FRAGILE"] = [f["id"] for f in contexts]
    prices = [{key: p[key] for key in ("age_sec", "price", "qty", "side")}
              for p in source["recent_observed_prices"]]
    if any(not _finite(p["age_sec"]) or p["age_sec"] < 0 for p in prices):
        raise ValueError("future_observation_forbidden")
    if any(not _finite(p['price']) or p['price'] <= 0 or p['side'] not in {'BUY','SELL','UNKNOWN'}
           or (p['qty'] is not None and (not _finite(p['qty']) or p['qty'] < 0)) for p in prices):
        raise ValueError('invalid_recent_price_observation')
    result = {key: copy.deepcopy(source[key]) for key in
              ("market", "venue", "source_item", "symbol_group", "price_band", "as_of")}
    result.update(
        schema=VERSION,
        context="Offline first-uptick counterfactual; not a historical machine decision.",
        objective=dict(net_target_pct=0.4, net_soft_stop_pct=-3.0,
                       horizon_seconds=1800, cost_rate=0.0023),
        observation_phase=dict(stage="FIRST_UPTICK", rolling_windows_end="AT_TRIGGER",
                               post_trigger_observations="NOT_YET_OBSERVABLE"),
        mechanistic_entry_assessment=dict(action="ENTER_NOW", price_reversal_confirmed=True,
                                         basis="counterfactual_price_reversal_research_only"),
        entry_setup_evidence_v1=dict(
            setup_state="READY", source_quality="price_and_entry_quote_valid",
            facts=facts, positive_facts=positives, context_facts=contexts,
            contradicting_facts=active, risk_fact_bindings=bindings,
            optional_missing=[key for key, value in facts.items() if value is None],
        ),
        recent_observed_prices=prices, runtime_effect=False,
        allowed_runtime_apply=False, actual_order_submitted=False,
    )
    if geometry:
        ask, trade = facts["entry_ask"], facts["confirmation_price"]
        result["entry_geometry"] = dict(
            target_price=ask * 1.004 / 0.9977,
            soft_stop_price=ask * 0.97 / 0.9977,
            ask_premium_to_trade_pct=100 * (ask / trade - 1),
            target_gap_from_trade_pct=100 * (ask * 1.004 / 0.9977 / trade - 1),
        )
    if production:
        result['context'] = 'Machine-confirmed observed first uptick; auxiliary assessment only, no order authority.'
        result['mechanistic_entry_assessment']['basis'] = 'observed_price_reversal'
    return result


def response_schema(inp: dict, *, complete_source_only: bool = False) -> dict:
    setup = inp["entry_setup_evidence_v1"]
    positive = [f["id"] for f in setup["positive_facts"]]
    adverse = [f["id"] for f in setup["contradicting_facts"] + setup["context_facts"]]
    def array(values):
        return dict(type="array", items=dict(type="string", enum=values))
    return dict(type="object", additionalProperties=False,
                required=["schema", "risk_verdict", "risk_codes", "supporting_fact_ids",
                          "contradicting_fact_ids", "confidence"], properties={
        "schema": dict(type="string", enum=["entry_setup_risk_adjudication_v1"]),
        "risk_verdict": dict(type="string", enum=["PASS", "CAUTION", "VETO"] + ([] if complete_source_only else ["INSUFFICIENT"])),
        "risk_codes": array(["NO_BLOCKING_RISK"] + ([] if complete_source_only else ["SOURCE_QUALITY_GAP"]) + list(setup["risk_fact_bindings"])),
        "supporting_fact_ids": array(positive),
        "contradicting_fact_ids": array(adverse) if adverse else dict(type="array", items=dict(type="string"), maxItems=0),
        "confidence": dict(type="integer", minimum=0, maximum=100),
    })


def validate_response(response: dict, inp: dict, *, complete_source_only: bool = False) -> list[str]:
    """Validate response meaning without turning any verdict into PASS."""
    errors = []
    schema = response_schema(inp, complete_source_only=complete_source_only)
    if not isinstance(response, dict) or set(response) != set(schema["required"]):
        return ["response_schema_invalid"]
    for key, rule in schema["properties"].items():
        value = response[key]
        if rule["type"] == "string" and (not isinstance(value, str) or value not in rule["enum"]):
            errors.append("response_schema_invalid")
        elif rule["type"] == "integer" and (type(value) is not int or not 0 <= value <= 100):
            errors.append("response_schema_invalid")
        elif rule["type"] == "array":
            if not isinstance(value, list) or any(not isinstance(v, str) or v not in rule["items"].get("enum", []) for v in value):
                errors.append("response_schema_invalid")
    if errors:
        return sorted(set(errors))
    verdict, codes = response["risk_verdict"], response["risk_codes"]
    support, contrary = set(response["supporting_fact_ids"]), set(response["contradicting_fact_ids"])
    if verdict == "PASS":
        if codes != ["NO_BLOCKING_RISK"]:
            errors.append("pass_code")
        if "first_price_uptick" not in support or not support & {"observed_price_decline", "observed_drawdown_state"}:
            errors.append("pass_support")
    elif verdict == "INSUFFICIENT":
        errors.append("essential_source_gap_not_supplied")
    else:
        bindings = inp["entry_setup_evidence_v1"]["risk_fact_bindings"]
        if not codes or any(code not in bindings or not contrary & set(bindings[code]) for code in codes):
            errors.append("nonpass_risk_unbound")
    return sorted(set(errors))


ARMS = ('existing_wording', 'reversal_fact_roles_v2', 'reversal_entry_geometry_v5',
        'reversal_citation_v6', 'reversal_complete_source_v7')
TIE_ORDER = tuple(reversed(ARMS))
PRODUCTION_VERSION = 'continuous_reversal_auxiliary_production_v1'
PRODUCTION_COMMON = '''
The supplied input is a machine-confirmed observed first uptick after a decline.
Assess net +0.4% within 1800 seconds from its entry ask before net -3%, with
cost 0.23% exactly once. Do not rank expected profit or reward/risk.
Rolling features end at the first uptick and can include that tick. They mix
the decline and trigger; no post-trigger failure has been observed. Optional
unknowns are neutral. Only supplied facts exist; do not invent future prices,
depth, news or a source gap. The machine owns the trigger and the runtime owns
all account, quote and order guards. This screen has no order authority.
Return the six-field JSON with supplied fact IDs. PASS uses NO_BLOCKING_RISK
and cites first_price_uptick plus observed_price_decline or observed_drawdown_state.
CAUTION/VETO must name a supplied code and a matching contradictory fact.
Confidence is diagnostic. Do not optimize a desired PASS quota.
'''


def production_prompt(arm):
    """Issued prompt bytes shared by registry, replay and runtime."""
    if arm not in ARMS:
        raise ValueError('unsupported_reversal_auxiliary_arm')
    if arm == ARMS[0]:
        from src.engine.ai_prompt_contracts import machine_auxiliary_compact_entry_system_prompt
        prompt = machine_auxiliary_compact_entry_system_prompt('entry') + PRODUCTION_COMMON
    elif arm == ARMS[1]:
        # Retain the role hypothesis, correct the historical temporal wording.
        prompt = LEGACY_ROLE_PROMPT.replace(
            'Read context_facts as the measured state preceding the reversal, not proof that',
            'Read context_facts as rolling measurements ending AT the first uptick, not proof that',
        ).replace(
            'All decisions are offline observations, without order or live-policy authority.',
            'This auxiliary assessment has no independent order authority.',
        ) + PRODUCTION_COMMON
    else:
        prompt = PROMPT.replace('This is offline counterfactual research, not historical entry or order authority.',
                                'This is an auxiliary assessment, with no independent order authority.') + HURDLE_SUFFIX
        if arm in ARMS[3:]:
            prompt += CITATION_SUFFIX
    if not prompt.isascii():
        raise ValueError('runtime_prompt_must_be_ascii')
    return prompt


def production_request(source, arm):
    """Exactly the same prompt, input projection and schema in replay and live."""
    prompt=production_prompt(arm)
    inp=build_input(source,geometry=arm in ARMS[2:],production=True)
    if arm==ARMS[0]:
        inp['entry_setup_evidence_v1']['contradicting_facts']+=inp['entry_setup_evidence_v1'].pop('context_facts')
        inp['entry_setup_evidence_v1']['context_facts']=[]
        inp['entry_setup_evidence_v1']['risk_fact_bindings']=copy.deepcopy(source['entry_setup_evidence_v1']['risk_fact_bindings'])
    return inp,prompt,response_schema(inp,complete_source_only=arm==ARMS[-1])

LEGACY_ROLE_PROMPT = 'Price-reversal auxiliary adjudication, with an explicit fact-role ledger.\nAssess the current price turn for net +0.4% within 30 minutes before net -3.0%.\nUse binary event likelihood, never expected PnL, payoff ratio or a larger target.\nThe machine hypothesis is already a decline followed by its first uptick.\nThat uptick is the requested confirmation, not a promise of a future win.\nAn additional positive trend, VWAP reclaim, buy-pressure floor or rising volume\nis not a mandatory second confirmation for this early reversal hypothesis.\nRead context_facts as the measured state preceding the reversal, not proof that\nthe reversal is invalid. Their numeric values are fully preserved in facts.\nDo not automatically reclassify a preceding sell wave, negative short momentum,\nbelow-VWAP price, or non-expanding volume as a present blocking risk. Consider\nthem together with the observed decline, current uptick, spread and rebound\nalready consumed. A large prior decline is the reversal context, not a veto.\nPASS when the price-reversal trigger is present and supplied current adverse\nevidence does not defeat the small-target opportunity. Cite its setup and trigger.\nCAUTION must name a concrete issue at the current entry, not desire to wait for\nall lagging context to agree. VETO needs a material current fact combination;\na contextual warning alone is insufficient. Account for an already large rebound\nor wide observed spread rather than rechecking the entire preceding trend.\nThe essential current price and entry quote were validated in constructing this\nresearch input. Optional missing context is neutral. Do not invent a source gap,\nfuture price, loss estimate, news, depth or investor/program flow.\nAll decisions are offline observations, without order or live-policy authority.\nUse the six-field risk JSON. PASS uses only NO_BLOCKING_RISK; acknowledge active\nadverse bindings. Other verdicts must cite matching active or context fact IDs.\nConfidence is not a gate. Optimize no PASS quota and give no guaranteed outcome.\n'
