from copy import deepcopy

import pytest

from src.engine.scalping import entry_policy_confirmation_research as research
from src.tests.test_entry_setup_evidence import _hierarchy_case


def case():
    setup, _, scalar = _hierarchy_case()
    rule = scalar.pop("hierarchy")["rules"][0]
    parent = deepcopy(scalar)
    prepared = dict(decision=dict(action="RECHECK", reason="TRIGGER_CONFIRMATION_RECHECK"),
        rebuilt=setup, effective=scalar, receipt=dict(effective_thresholds=dict(micro_confirmation_recipe=0)))
    spec = {key: rule[key] for key in ("id", "match", "flow_family")}
    return dict(setup_evidence=setup), parent, prepared, spec


def reseal(setup):
    setup["evidence_sha256"] = research.S.digest({k: v for k, v in setup.items() if k != "evidence_sha256"})


def test_existing_kernel_confirms_without_mutating_setup_or_parent():
    row, parent, prepared, spec = case()
    before = deepcopy((row, parent, prepared, spec))
    result = research.prototype_decision(row, parent, prepared, spec)
    assert result["action"] == "ENTER_NOW"
    assert result["group_trigger_pass"] is True
    assert (row, parent, prepared, spec) == before


@pytest.mark.parametrize("action,reason", [
    ("BLOCK", "mechanistic_hard_or_source_block"), ("ENTER_NOW", "pass"),
    ("RECHECK", "local_breakout_confirmation_required"), ("RECHECK", "unknown_new_guard"),
])
def test_adapter_preserves_parent_guards(action, reason):
    row, parent, prepared, spec = case()
    prepared["decision"] = dict(action=action, reason=reason)
    assert research.prototype_decision(row, parent, prepared, spec)["action"] == action


@pytest.mark.parametrize("damage", ["price", "delta", "source", "liquidity", "local", "micro_recipe", "unmatched"])
@pytest.mark.parametrize("recipe", ["legacy_group_trigger", "family_setup_confirmation"])
def test_confirmation_cannot_bypass_source_or_confirmation_constraints(damage, recipe):
    row, parent, prepared, spec = case()
    spec["recipe"] = recipe
    setup = prepared["rebuilt"]
    if damage == "price":
        setup["micro_recovery_observation"]["price_change_10t_pct"] = 0
    if damage == "delta":
        setup["micro_recovery_observation"]["net_aggressive_delta_10t"] = 0
    if damage == "source":
        setup["micro_recovery_observation"]["source_usable"] = False
    if damage == "liquidity":
        setup["tail_risk_assessment"]["inputs"]["spread_bp"] = 10000
    if damage == "local":
        setup["local_breakout"] = dict(recheck_required=True)
    if damage == "micro_recipe":
        prepared["receipt"]["effective_thresholds"]["micro_confirmation_recipe"] = 1
    if damage == "unmatched":
        spec["match"]["structure_phase"] = "other"
    reseal(setup)
    assert research.prototype_decision(row, parent, prepared, spec)["action"] == "RECHECK"


@pytest.mark.parametrize("risk_code,fact,disposition,allowed", [
    ("CONFIRMATION_MISSING", "micro_continuation_unconfirmed", "RECHECKABLE", True),
    ("CONFIRMATION_MISSING", "no_supported_setup", "RECHECKABLE", True),
    ("LIQUIDITY_FRAGILE", "liquidity_adverse", "RECHECKABLE", False),
    ("CONFIRMATION_MISSING", "unknown_confirmation", "RECHECKABLE", False),
    ("CONFIRMATION_MISSING", "no_supported_setup", "BLOCKING", False),
])
def test_extended_recipe_has_explicit_soft_fact_boundary(risk_code, fact, disposition, allowed):
    _, _, prepared, _ = case()
    decision = dict(applied_thresholds=prepared["effective"]["thresholds"],
        liquidity_inputs_complete=True, liquidity_threshold_pass=True,
        core_comparison=dict(preferred_action="RECHECK", risk_assessments=[
            dict(risk_code=risk_code, fact_id=fact, disposition=disposition)]))
    before = deepcopy((prepared, decision))
    assert research.family_setup_confirmed(prepared, decision) is allowed
    assert (prepared, decision) == before


def test_parent_vwap_veto_reapplied_after_new_confirmation():
    row, parent, prepared, spec = case()
    parent["entry_situation_veto"] = research.prior.calibration._winrate_veto_payload(68.75)
    row["setup_evidence"] = {**row["setup_evidence"], "strategy_raw_input": dict(
        effective_venue="KRX", session_bucket="KRX_REGULAR", features=dict(
            micro_vwap_available=True, minute_candle_window_fresh=True, curr_vs_micro_vwap_bp=90))}
    row["setup_evidence"]["strategy_raw_sha256"] = research.S.digest(row["setup_evidence"]["strategy_raw_input"])
    assert research.prototype_decision(row, parent, prepared, spec)["action"] == "RECHECK"


def test_unknown_types_and_outcomes_do_not_generate_branches():
    _, _, prepared, _ = case()
    parts = prepared["rebuilt"]["mechanistic_context"]["group"]["key_parts"]
    parts.update(structure_phase="continuation", liquidity_band="UNKNOWN", volatility_band="LOW")
    initial = research.definitions([prepared])
    prepared["future_outcome"] = 10000
    assert research.definitions([prepared]) == initial
    assert len(initial) == 4
    assert all("liquidity_band" not in item["match"] for item in initial)
    assert research.definitions([]) == []


def test_selection_uses_recovery_rank_and_fixed_tie_order(monkeypatch):
    metrics = {"one": dict(recovery_metrics=dict(selected_opportunity_count=1,
        successful_opportunity_weight=1, win_rate_pct=100), selected_opportunity_count=5,
        win_rate_pct=80, selection_score_version=research.S.RECOVERY_SELECTION_VERSION),
        "many": dict(recovery_metrics=dict(selected_opportunity_count=4,
        successful_opportunity_weight=4, win_rate_pct=100), selected_opportunity_count=8,
        win_rate_pct=87.5, selection_score_version=research.S.RECOVERY_SELECTION_VERSION)}
    monkeypatch.setattr(research.prior, "economy", lambda rows, actions: metrics[actions[0]])
    chosen, _ = research.choose([], {"z": ["many"], "a": ["many"], "b": ["one"]})
    assert chosen == "a"
    chosen, _ = research.choose([], {"z": ["many"], "a": ["many"]}, specifications={
        "z": dict(match=dict(venue="KRX")), "a": dict(match=dict(venue="KRX", extra="LOW"))})
    assert chosen == "z"


def test_research_policy_cannot_pass_live_validator():
    _, parent, _, spec = case()
    parent["research_confirmation_overlay"] = spec
    assert research.E.validate_mechanistic_entry_threshold_policy(parent)


def test_output_prohibits_runtime_root_and_replacing_frozen_generation(tmp_path):
    for path in (tmp_path / "data/runtime", tmp_path / "tmp", tmp_path.parent / "elsewhere"):
        with pytest.raises(ValueError, match="workspace_tmp_child"):
            research._checked_output(tmp_path, path)
    output = tmp_path / "tmp/run"
    output.mkdir(parents=True)
    (output / "frozen-candidates.json").write_text("{}")
    with pytest.raises(ValueError, match="already_frozen"):
        research._checked_output(tmp_path, output)
