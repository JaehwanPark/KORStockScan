import copy

import pytest

from src.engine.scalping.reversal_auxiliary_contract import (
    PROMPT, HURDLE_SUFFIX, build_input, validate_response,
)


@pytest.fixture
def source():
    from src.engine.scalping.reversal_auxiliary_contract import FEATURES
    facts = dict.fromkeys(FEATURES, None)
    facts.update(entry_ask=100.1, confirmation_price=100, low_price=99.9,
                 confirmation_pct=0.1001, buy_pressure_10t=20, vs_vwap_60s_pct=-0.3)
    return dict(market="REGULAR", venue="SOR", source_item="005930_AL",
                symbol_group="samsung", price_band="GE_100000", as_of="2026-10-06T09:05:00+09:00",
                mechanistic_entry_assessment=dict(price_reversal_confirmed=True),
                recent_observed_prices=[dict(age_sec=0, price=100, qty=10, side="BUY")],
                entry_setup_evidence_v1=dict(source_quality="price_and_entry_quote_valid",
                    facts=facts, positive_facts=[dict(id="first_price_uptick", value=0.1001),
                                                dict(id="observed_price_decline", value=0.5)],
                    contradicting_facts=[dict(id="recent_sell_pressure", value=20),
                                         dict(id="below_recent_vwap", value=-0.3)],
                    risk_fact_bindings={"ADVERSE_TAPE": ["recent_sell_pressure", "below_recent_vwap"]}))


def test_roles_preserve_numbers_and_explain_trigger_inclusive_windows(source):
    before = copy.deepcopy(source)
    result = build_input(source, geometry=True)
    setup = result["entry_setup_evidence_v1"]
    assert source == before
    assert setup["facts"] == source["entry_setup_evidence_v1"]["facts"]
    assert len(setup["context_facts"]) == 2
    assert setup["contradicting_facts"] == []
    assert result["observation_phase"]["rolling_windows_end"] == "AT_TRIGGER"
    assert result["entry_geometry"]["target_price"] == pytest.approx(100.1 * 1.004 / .9977)
    assert PROMPT.isascii() and HURDLE_SUFFIX.isascii()


def test_outcomes_and_unknown_metadata_never_reach_provider(source):
    baseline = build_input(source)
    source.update(outcome="WIN", future_price=9999, win_rate_pct=100)
    source["entry_setup_evidence_v1"]["facts"]["outcome"] = "WIN"
    assert build_input(source) == baseline
    source["entry_setup_evidence_v1"]["positive_facts"][0]["outcome"] = "WIN"
    with pytest.raises(ValueError, match="unexpected_fact_metadata"):
        build_input(source)


@pytest.mark.parametrize("change", ["future", "gap", "false_turn"])
def test_invalid_essential_input_cannot_be_promoted(source, change):
    if change == "future":
        source["recent_observed_prices"][0]["age_sec"] = -1
    elif change == "gap":
        source["entry_setup_evidence_v1"]["source_quality"] = "missing"
    else:
        source["mechanistic_entry_assessment"]["price_reversal_confirmed"] = False
    with pytest.raises(ValueError):
        build_input(source)


def test_nonpass_remains_available_without_fabricated_post_trigger_fact(source):
    inp = build_input(source)
    r = dict(schema="entry_setup_risk_adjudication_v1", risk_verdict="CAUTION",
             risk_codes=["EARLY_REVERSAL_FRAGILE"], supporting_fact_ids=["first_price_uptick"],
             contradicting_fact_ids=["recent_sell_pressure"], confidence=60)
    assert validate_response(r, inp) == []
    r["risk_codes"] = ["NO_BLOCKING_RISK"]
    assert validate_response(r, inp) == ["nonpass_risk_unbound"]
    assert r["risk_verdict"] == "CAUTION"
    r["risk_verdict"] = "PASS"
    r["supporting_fact_ids"].append("observed_price_decline")
    assert validate_response(r, inp) == []
    r["confidence"] = True
    assert validate_response(r, inp) == ["response_schema_invalid"]


def test_complete_source_schema_cannot_request_a_fabricated_source_gap(source):
    from src.engine.scalping.reversal_auxiliary_contract import response_schema
    inp = build_input(source)
    schema = response_schema(inp, complete_source_only=True)
    assert "SOURCE_QUALITY_GAP" not in schema["properties"]["risk_codes"]["items"]["enum"]
    assert "INSUFFICIENT" not in schema["properties"]["risk_verdict"]["enum"]
    # Genuine missing input is still rejected before any provider call.
    source["entry_setup_evidence_v1"]["facts"]["entry_ask"] = None
    with pytest.raises(ValueError):
        build_input(source)
