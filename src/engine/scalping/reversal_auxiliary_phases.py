"""Phase-specific auxiliary request bytes; FIRST delegates unchanged to v1."""
from __future__ import annotations

import copy
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping.continuous_reversal_branches import FIRST, CONFIRMED
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = "continuous_reversal_auxiliary_phases_v2"
CONFIRMED_PROMPT = """Assess a machine-observed price reversal at the current confirmation ask.
The binary event is net +0.4% within 30 minutes before net -3.0%, with the
supplied cost charged once. Do not judge expected PnL or payoff ratio.
The original first uptick and an additional higher trade have BOTH occurred.
Their identities, clocks and prices are separate in observation_phase.
Rolling context ends AT_CONFIRMATION and includes the preceding decline and
the observations since the first uptick. Do not call those observations future,
and do not treat preceding selling or below-VWAP context as failed rebound proof.
Judge the current small-target opportunity with the supplied spread, ask premium,
decline, original uptick and additional observed higher trade. Optional unknown
context is neutral. Do not demand another confirmation or invent depth/news.
There are no observations after as_of. No label, win rate or future outcome is
available. This auxiliary screen has no order authority. Confidence is diagnostic.
Return the six-field JSON. For PASS set risk_codes=["NO_BLOCKING_RISK"] exactly.
Never return an empty risk_codes array. PASS requires citations of
first_price_uptick, additional_higher_trade, and observed_price_decline or
observed_drawdown_state. CAUTION/VETO must cite a supplied binding for every risk
code. Context concerns are context, not invented post-confirmation invalidation.
"""
ARM_SUFFIXES = {
    V1.ARMS[0]: "Read the fact ledger directly, including adverse context.\n",
    V1.ARMS[1]: "Distinguish positive, contextual and current adverse fact roles.\n",
    V1.ARMS[2]: "Read entry_geometry without adding cost or spread twice.\n",
    V1.ARMS[3]: "Ground reservations in exact supplied context/adverse fact IDs.\n",
    V1.ARMS[4]: "All essential inputs were validated. INSUFFICIENT is unavailable.\n",
}


def prompt(phase, arm):
    if phase == FIRST:
        return V1.production_prompt(arm)
    if phase != CONFIRMED or arm not in V1.ARMS:
        raise ValueError("reversal_auxiliary_phase_unsupported")
    return CONFIRMED_PROMPT + ARM_SUFFIXES[arm]


def version(phase, arm):
    if phase == FIRST:
        return V1.PRODUCTION_VERSION + ":" + arm
    return VERSION + ":" + phase + ":" + arm


def binding(phase, arm):
    return dict(phase=phase, arm=arm, prompt_version=version(phase, arm),
                prompt_sha256=digest(prompt(phase, arm)), input_version=VERSION if phase==CONFIRMED else V1.VERSION,
                response_schema_version="entry_setup_risk_adjudication_v1",
                validator_version=VERSION if phase==CONFIRMED else V1.VERSION,
                feature_version='continuous_reversal_v1',
                fact_definition_sha256=digest(CONFIRMED_PROMPT) if phase==CONFIRMED else digest(V1.production_prompt(arm)))


def production_request(source, arm, *, phase=FIRST, event=None):
    if phase == FIRST:
        return V1.production_request(source, arm)
    if phase != CONFIRMED or not isinstance(event, dict) or event.get("decision_phase") != phase:
        raise ValueError("confirmed_reversal_phase_event_missing")
    if not (0 <= event["epoch"]-event["anchor_epoch"] <= 5
            and event["confirmation_price"] > event["anchor_price"]
            and event["anchor_price"] > event["low_price"]):
        raise ValueError("confirmed_reversal_timeline_invalid")
    inp, _, _ = V1.production_request(source, arm)
    inp = copy.deepcopy(inp)
    inp["schema"] = VERSION
    inp["context"] = "Machine-observed additional higher trade; auxiliary only, no order authority."
    inp["observation_phase"] = dict(
        stage=CONFIRMED, rolling_windows_end="AT_CONFIRMATION",
        post_trigger_observations="OBSERVED_THROUGH_CONFIRMATION",
        original_first_uptick=dict(id=event["anchor_event_id"], as_of=event["anchor_epoch"], price=event["anchor_price"]),
        additional_higher_trade=dict(id=event["event_id"], as_of=event["epoch"], price=event["confirmation_price"]))
    inp["entry_setup_evidence_v1"]["positive_facts"].append(dict(
        id="additional_higher_trade", value=100*(event["confirmation_price"]/event["anchor_price"]-1), unit="percent"))
    # The first uptick fact remains its original value. No branch name, study
    # success, labels or arbitrary event metadata enter the model request.
    schema=V1.response_schema(inp, complete_source_only=arm==V1.ARMS[-1])
    schema['properties']['risk_codes']['minItems']=1
    return inp, prompt(phase, arm), schema


def validate_response(response, inp, *, arm, phase):
    errors = V1.validate_response(response, inp, complete_source_only=arm==V1.ARMS[-1])
    if phase == CONFIRMED:
        if (inp or {}).get("observation_phase", {}).get("stage") != CONFIRMED:
            errors.append("reversal_response_phase_mismatch")
        if isinstance(response,dict) and response.get("risk_verdict")=="PASS" and "additional_higher_trade" not in response.get("supporting_fact_ids",[]):
            errors.append("confirmed_pass_support_missing")
    elif phase != FIRST:
        errors.append("reversal_response_phase_unsupported")
    return sorted(set(errors))
