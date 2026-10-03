import gzip
import json

import pytest

from src.engine.scalping import entry_policy_hypothesis_research as research


def row(index=0, price=100):
    return dict(source_date="2026-09-29",stock_code="005930",effective_venue="KRX",session_bucket="KRX_REGULAR",
        scanner_promotion_id=f"native-{index}", setup_evidence=dict(setup_family="CLEAN_CONTINUATION",structure_phase="continuation",
        strategy_raw_input=dict(current=dict(price=price),features={}),
        mechanistic_context=dict(group=dict(key_parts=dict(liquidity_band="SUPPORTIVE",structure_phase="continuation")))))


def test_stream_retained_array_handles_whitespace_and_gzip(tmp_path):
    path=tmp_path/"cache.json.gz"
    with gzip.open(path,"wt") as stream:
        json.dump(dict(contract={},rows=[dict(x=1),dict(x=2)],authority=False),stream,indent=2)
    assert list(research.stream_array(path))==[dict(x=1),dict(x=2)]


def test_masks_use_training_features_and_sparse_type_falls_back():
    training=[row(i,price=100+i) for i in range(6)]
    masks=research.conditions(training,minimum_opportunities=5)
    assert any(m and m["kind"]=="numeric" for m in masks)
    assert any(m and m["kind"]=="type" for m in masks)
    assert research.conditions(training[:1],minimum_opportunities=5)==[None]
    boundaries=[m["boundary"] for m in masks if m and m["kind"]=="numeric" and m["feature"]=="price"]
    assert boundaries==[102,102,104,104]
    unknown=row();unknown["setup_evidence"]["strategy_raw_input"]["current"]={}
    assert not research.matches(unknown,dict(kind="numeric",feature="price",boundary=102,side="lt"))
    assert research.matches(row(),None)


def horizon_fixture():
    r=dict(evaluation_key="exact",stock_code="005930",decision_ts="2026-09-29T09:05:00+09:00",
        machine_bundle_sha256="a"*64,effective_venue="KRX",session_bucket="KRX_REGULAR",
        ai_stage_path=dict(label_report_sha256="b"*64,conservative_execution_cost_pct=.2))
    label=dict(decision_trace_id="exact",stock_code="005930",decision_ts=r["decision_ts"],machine_bundle_sha256="a"*64,
        source_quality_status="pass",matured_horizons_min=[10],horizon_metrics={"10m":dict(sample_count=10,counterfactual_only=True,
        window_basis="post_decision_same_route",window_start=r["decision_ts"],observed_venue="KRX",
        observed_session_bucket="KRX_REGULAR",end_return_pct=.5)})
    return r,label


def test_fixed_horizon_uses_existing_cost_without_inventing_stop():
    r,label=horizon_fixture()
    assert research.fixed_horizon_net(r,label,10,"b"*64)==.3
    assert "stop" not in json.dumps(r)
    assert research.fixed_horizon_net(r,label,1,"b"*64) is None


@pytest.mark.parametrize("damage",["request","generation","scope","window","cost","invalid"])
def test_fixed_horizon_requires_exact_binding(damage):
    r,label=horizon_fixture()
    if damage=="request":label["decision_trace_id"]="other"
    if damage=="generation":r["ai_stage_path"]["label_report_sha256"]="c"*64
    if damage=="scope":label["horizon_metrics"]["10m"]["observed_venue"]="NXT"
    if damage=="window":label["horizon_metrics"]["10m"]["window_start"]="earlier"
    if damage=="cost":r["ai_stage_path"]["conservative_execution_cost_pct"]=None
    if damage=="invalid":label["source_quality_status"]="fail"
    assert research.fixed_horizon_net(r,label,10,"b"*64) is None


def test_invalid_candidate_cannot_count_as_successful_rejection(monkeypatch):
    monkeypatch.setattr(research.evidence,"evaluate_auxiliary_policy",lambda *a,**k:dict(validation_errors=["invalid"],effective_verdict="INVALID"))
    with pytest.raises(ValueError,match="candidate_validation_failed"):
        research.auxiliary_vector([dict(replay_response={},input=dict(entry_setup_evidence_v1={}),machine_policy={})],{})


def test_auxiliary_metrics_keep_coverage_and_lost_winners():
    rows=[dict(incumbent_verdict="PASS",nets={10:.1}),dict(incumbent_verdict="PASS",nets={10:-.5}),dict(incumbent_verdict="PASS",nets={10:None})]
    metric=research.auxiliary_summary(rows,["CAUTION","CAUTION","PASS"])
    assert metric["comparable"]==2
    assert metric["successful_pass_lost"]==1
    assert metric["paired_mean_cf_delta_pct"]==.2
    assert metric["pass_mean_cf_net_pct"] is None


def test_auxiliary_winrate_selection_can_drop_successes_when_failure_reduction_wins():
    rows = [dict(incumbent_verdict="PASS", nets={10:.1}) for _ in range(6)] + [
        dict(incumbent_verdict="PASS", nets={10:-1.}) for _ in range(4)]
    baseline = research.auxiliary_summary(rows, ["PASS"]*10)
    score = research.auxiliary_summary(rows, ["CAUTION"]+["PASS"]*5+["CAUTION"]*3+["PASS"])
    assert baseline["pass_win_rate_pct"] == 60
    assert score["successful_pass_lost"] == 1
    assert score["pass_win_rate_pct"] == pytest.approx(100*5/6)
    assert research.auxiliary_winrate_qualified(score, baseline)
    # Neither lost winners nor negative net CF secretly replaces the objective.
    score["paired_mean_cf_delta_pct"] = -.1
    assert research.auxiliary_winrate_qualified(score, baseline)
    score["pass_win_rate_pct"] = 60
    assert not research.auxiliary_winrate_qualified(score, baseline)


def test_auxiliary_winrate_rank_ignores_retention_and_net_for_candidate_order():
    score = dict(pass_count=8, pass_win_rate_pct=87.5, successful_pass_lost=2, paired_mean_cf_delta_pct=-.1)
    before = research.auxiliary_winrate_rank(score)
    score.update(successful_pass_lost=0, paired_mean_cf_delta_pct=999)
    assert research.auxiliary_winrate_rank(score) == before


def test_research_outputs_cannot_target_live_policy(tmp_path):
    with pytest.raises(ValueError,match="workspace_tmp"):
        research.run_research(tmp_path,tmp_path/"data/policy")


@pytest.mark.parametrize("damage",[None,"missing_hash","conflict","wrong_stock"])
def test_archived_native_metadata_requires_exact_source_identity(tmp_path,damage):
    r=dict(evaluation_key="exact",stock_code="005930",decision_ts="2026-09-29T09:05:00+09:00",
        payload_sha256="a"*64,machine_bundle_sha256="b"*64,effective_venue="KRX",session_bucket="KRX_REGULAR")
    native={k:v for k,v in r.items() if k!="evaluation_key"}
    native.update(decision_trace_id="exact",watch_origin="MAIN_FIXED_WATCH",watch_admission_id="admission",watch_generation_id="generation")
    if damage=="missing_hash":r["payload_sha256"]=None;native["payload_sha256"]=None
    if damage=="wrong_stock":native["stock_code"]="000660"
    entries=[native]
    if damage=="conflict":entries.append({**native,"watch_generation_id":"other"})
    path=tmp_path/"trace.jsonl.gz"
    with gzip.open(path,"wt") as stream:
        stream.write("".join(json.dumps(value)+"\n" for value in entries))
    result=research.restore_native_metadata([r],path)
    assert result["repaired_rows"]==int(damage is None)
    assert ("watch_admission_id" in r)==(damage is None)


def test_feature_filter_unknown_inherits_and_bounds_are_predecision():
    rows=[dict(opportunity=["day",str(i)],features=dict(confidence=.5+i/10,support_count=4),type_parts=dict(liquidity_band="SUPPORTIVE")) for i in range(6)]
    conditions=research.feature_filter_conditions(rows)
    assert conditions
    assert any(c["kind"]=="numeric" and c["feature"]=="support_count" and c["boundary"]==5 for c in conditions)
    unknown=dict(features={},type_parts={})
    assert not research.feature_filter_matches(unknown,dict(kind="numeric",feature="confidence",boundary=.8,side="lt"))
    assert not research.feature_filter_conditions(rows[:1])
    assert len(research.feature_filter_conditions(rows,maximum=2))<=2
    original=json.dumps(conditions,sort_keys=True)
    for r in rows:r["nets"]={10:999};r["incumbent_verdict"]="VETO"
    assert json.dumps(research.feature_filter_conditions(rows),sort_keys=True)==original


def test_horizon_observation_hash_survives_json_roundtrip():
    r=row()
    setup=r.pop("setup_evidence")
    r.update(input=dict(entry_setup_evidence_v1=setup),replay_response={},machine_policy={},
        incumbent_prompt_version="stored",incumbent_verdict="PASS",nets={1:.1,3:.2,5:.3,10:.4})
    observed=research.auxiliary_observation(r)
    sealed=research.compact.sealed(dict(rows=[observed]))
    assert research.compact.valid(json.loads(json.dumps(sealed)))
