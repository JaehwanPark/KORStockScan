from copy import deepcopy
import pytest

from src.engine.scalping import entry_policy_deep_research as deep


def row(i=0, **updates):
    value = dict(trace=str(i), day="2026-09-29", symbol="005930", bundle="a"*64,
        ts=f"2026-09-29T09:{i:02}:00+09:00", native_opportunity=None,
        features=dict(flow=float(i)), types=dict(phase="pullback"),
        gross={"1":1., "3":2., "5":3., "10":4.}, cost=.25,
        binary=float(i%2), path_net=.1 if i%2 else -.9)
    value.update(updates)
    return value


def test_first_observation_selection_does_not_choose_future_winner():
    rows=[row(0,binary=None),row(1,binary=1.),row(10,binary=0.)]
    assert [r["trace"] for r in deep.anchors(rows)]==["0","10"]
    for r in rows:r["native_opportunity"]=["same","opportunity"]
    assert deep.anchors(rows,native=True)==[rows[0]]
    assert deep.anchors([row()],native=True)==[]


def test_training_conditions_do_not_consume_outcomes_or_action_labels():
    rows=[row(i) for i in range(20)]
    before=deep.conditions(rows,minimum=5)
    for r in rows:
        r.update(binary=999,path_net=-100,parent_action="BLOCK",gross={"10":999})
    assert deep.conditions(rows,minimum=5)==before
    assert len(deep.conditions(rows,minimum=5,maximum=2))<=2


def test_unknown_and_nonfinite_features_cannot_match():
    c=dict(kind="numeric",feature="flow",boundary=0.,side="ge")
    for value in (None,float("nan"),float("inf")):
        assert not deep.match(row(features=dict(flow=value)),c)


def test_delayed_cf_uses_price_ratio_and_one_round_trip_cost():
    r=row(gross={"1":2.,"10":3.},cost=.3)
    assert deep.net_at(r,10,1)==pytest.approx((1.03/1.02-1)*100-.3)
    assert deep.net_at(r,10)==pytest.approx(2.7)
    assert deep.net_at(r,1,1) is None
    assert deep.net_at(row(cost=None),10) is None


def test_symbol_day_weighting_and_missing_outcome_are_explicit():
    rows=[row(0,binary=1.),row(1,binary=1.),row(2,symbol="000660",binary=0.),row(3,binary=None)]
    metric=deep.metric(rows,[True]*4)
    assert metric["available"]==3
    assert metric["mean"]==pytest.approx(2/3)
    assert metric["symbol_day_weighted_mean"]==.5
    lost=deep.metric(rows,[False,True,True,True])
    assert lost["successful_excluded"]==1


def test_actual_held_outcomes_cannot_change_training_selection():
    training=[row(i) for i in range(20)]
    held=[row(20+i,day="2026-10-02") for i in range(5)]
    first=deep.rule_study(training,held,minimum=5)
    for r in held:r.update(binary=1e9,path_net=1e9,gross={"10":1e9})
    second=deep.rule_study(training,held,minimum=5)
    assert first["selected"]["condition"]==second["selected"]["condition"]
    assert first["selected"]["train"]==second["selected"]["train"]


def test_feature_whitelist_excludes_future_and_source_invalid_micro(monkeypatch):
    monkeypatch.setattr(deep.prior.strategy,"features",lambda *a:dict(volatility_pct=.5,price=100.))
    source=dict(setup_evidence=dict(micro_recovery_observation=dict(source_usable=False,net_aggressive_delta_10t=100),
        strategy_raw_input=dict(current=dict(price=100.),features=dict(price_change_10t_pct=1.,future_return=999))))
    values,_=deep.features(source)
    assert values["price_change_10t_pct"] is None
    assert "future_return" not in values and "price" not in values


def test_projection_horizons_rejects_cost_or_provenance_mismatch(monkeypatch):
    monkeypatch.setattr(deep.prior.calibration,"_full_entry_cost_pct",lambda *a,**kw:.3)
    r=dict(source_date="2026-09-29",effective_venue="KRX",session_bucket="KRX_REGULAR",
        source_provenance_verified=True,machine_observation_hash_verified=True,
        comparison=dict(entry_cost_contract=dict(effective_venue="KRX",session_bucket="KRX_REGULAR"),conservative_execution_cost_pct=.3),
        outcome_horizon_metrics={"1m":dict(status="observed",sample_count=1,end_return_pct=.5)})
    assert deep.projection_horizons(r)==({"1":.5},.3)
    for key in ("source_provenance_verified","machine_observation_hash_verified"):
        broken=deepcopy(r);broken[key]=False
        assert deep.projection_horizons(broken)==({},None)
    r["comparison"]["conservative_execution_cost_pct"]=0.
    assert deep.projection_horizons(r)==({},None)


@pytest.mark.parametrize("damage",[None,"future","attempt","generation","micro"])
def test_pre_ai_feature_join_requires_exact_identity_and_past_time(damage):
    setup=dict(structure_phase_sha256="a"*64,source_quality=dict(status="pass"),micro_recovery_observation=dict(source_usable=True))
    observation=row(ai_trace="ai",attempt="attempt",setup_join_digest=deep.setup_join_digest(setup))
    source=dict(input=dict(entry_setup_evidence_v1=deepcopy(setup)),evaluation_key="ai",evaluation_attempt_id="attempt",
        stock_code="005930",source_date="2026-09-29",machine_bundle_sha256="a"*64,
        effective_venue="KRX",session_bucket="krx_regular",decision_ts="2026-09-29T09:00:05+09:00")
    if damage=="future":observation["ts"]="2026-09-29T09:00:06+09:00"
    if damage=="attempt":source["evaluation_attempt_id"]="other"
    if damage=="generation":source["machine_bundle_sha256"]="b"*64
    if damage=="micro":source["input"]["entry_setup_evidence_v1"]["micro_recovery_observation"]={}
    assert deep.exact_pre_ai_join(observation,source)==(damage is None)


def test_auxiliary_unknown_filter_keeps_parent_pass():
    condition=dict(kind="numeric",feature="unavailable",boundary=1.,side="lt")
    assert deep.rule_mask([row()],condition,"exclude")==[True]


def test_full_population_coverage_keeps_censored_denominator():
    rows=[row(0,binary=1.),row(1,binary=0.),row(2,binary=None)]
    result=deep.coverage_metric(rows,[True]*3)
    assert result["selected_observations"]==3
    assert result["resolved"]==2 and result["unresolved"]==1
    assert result["resolved_target_first_pct"]==50
    assert result["all_selected_known_target_lower_bound_pct"]==pytest.approx(100/3)


@pytest.mark.parametrize("horizon",[1,3,5,10])
def test_vectorized_research_metric_matches_reference_with_gaps(horizon):
    rows=[row(i,symbol=str(i%3),gross={"1":i/10,"3":i/15,"10":i/20} if i%4 else {},cost=.25) for i in range(20)]
    masks=deep.np.array([[True]*20,[i%2==0 for i in range(20)],[False]*20],dtype=bool)
    fast=deep.matrix_metrics(rows,masks,horizon=horizon)
    for mask,actual in zip(masks,fast):
        reference=deep.metric(rows,mask,target="net",horizon=horizon)
        assert actual.keys()==reference.keys()
        for key,value in reference.items():
            if value is None:assert actual[key] is None
            else:assert actual[key]==pytest.approx(value)


@pytest.mark.parametrize("robust",[False,True])
def test_fast_selection_matches_same_frozen_reference_candidates(robust):
    rows=[row(i,symbol=str(i%3),gross={"1":i/10,"3":i/12,"5":i/14,"10":i/15}) for i in range(20)]
    later=[row(i+20,day="2026-10-02",symbol=str(i)) for i in range(5)]
    fast=deep.fast_rule_study(rows,later,minimum=5,robust_horizons=robust)
    slow=deep.rule_study(rows,later,minimum=5,target="net",robust_horizons=robust)
    assert fast["definitions"]==slow["definitions"]
    assert fast["selected"]["condition"]==slow["selected"]["condition"]
    assert fast["selected"]["score"]==pytest.approx(slow["selected"]["score"])


def test_sparse_phase_cannot_become_a_positive_research_rule():
    result=deep.phase_fold([row(i,types=dict(phase="pullback")) for i in range(20)],[row(21)])
    assert not result["positive_training_phase_rules"]
    assert result["results"]["pullback"]["status"]=="sparse_phase_parent_only"
