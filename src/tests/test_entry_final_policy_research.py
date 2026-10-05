from collections import defaultdict
from copy import deepcopy
from itertools import product
from statistics import mean

import pytest

from src.engine.scalping import entry_final_policy_research as M
from src.engine.scalping import entry_first_signal_exit_research as F

POLICY = dict(start_pct=.4, weak_pct=.4, strong_pct=.8,
    hard_stop_net_pct=-1.4, emergency_stop_net_pct=-2.4, runtime_cost_rate=.0023)


def row(trace, symbol='000660', status='target'):
    return dict(trace=trace, symbol=symbol, day='2026-10-02', ts='2026-10-02T09:00:00+09:00',
        group='non_samsung', outcome_request_code=symbol+'_AL', source_bundle_sha256='a',
        path=dict(status=status, net_pct=.1 if status == 'target' else -1 if status == 'stop' else None),
        source_lane='machine_observation_counterfactual_no_provider', native_provenance=None,
        reference_price=100, reference_type='executable_ask', capture_valid=True,
        features=dict(entry_cost_pct=.3))


def assigned_rate(rows, assignment):
    groups = defaultdict(list)
    for r in rows:
        status = r['path']['status']
        if status != 'timeout':
            groups[r['symbol']].append(int(status == 'target') if status in {'target','stop'} else assignment[r['trace']])
    return 100 * mean(mean(v) for v in groups.values())


def test_shared_unknown_bounds_match_exhaustive_joint_assignments():
    shared = row('shared', status='first_partial_bar_ambiguous')
    parent = [row('pwin'), shared, row('punknown','000001','cost_missing_or_mismatched')]
    candidate = [row('closs',status='stop'), shared, row('cunknown','000002','insufficient_followup')]
    actual = M.binary_assignment_sensitivity(parent,candidate)
    deltas = []
    for bits in product((0,1), repeat=3):
        labels = dict(zip(('shared','punknown','cunknown'),bits))
        delta = assigned_rate(candidate,labels)-assigned_rate(parent,labels)
        deltas.append(delta)
        formula = actual['delta_formula']
        predicted = formula['intercept_pp'] + sum(formula['target_assignment_coefficients_pp'][k]*v for k,v in labels.items())
        assert delta == pytest.approx(predicted)
    assert actual['lower_delta_pp'] == pytest.approx(min(deltas))
    assert actual['upper_delta_pp'] == pytest.approx(max(deltas))
    assert actual['shared_unknown_count'] == 1
    assert actual['delta_formula']['target_assignment_coefficients_pp']['shared'] == 0


def test_identical_arms_cannot_assign_opposite_results_to_shared_missing_rows():
    rows = [row('a'), row('u',status='same_bar_ambiguous')]
    result = M.binary_assignment_sensitivity(rows,deepcopy(rows))
    assert result['lower_delta_pp'] == result['upper_delta_pp'] == 0


def test_timeouts_are_not_imputed_and_only_missing_binary_denominator_stays_null():
    r = M.binary_assignment_sensitivity([row('p','000001','timeout')],[row('c')])
    assert r['status'] == 'binary_scenario_denominator_unavailable'
    assert r['lower_delta_pp'] is None
    r = M.binary_assignment_sensitivity([row('p'), row('t','000001','timeout')],[row('c')])
    assert r['lower_delta_pp'] == r['upper_delta_pp'] == 0
    assert r['arms']['parent']['known_timeout_excluded'] == 1


def test_unknown_only_cluster_enters_scenario_not_observed_resolved_denominator():
    parent = [row('p'),row('u','000001','insufficient_followup')]
    candidate = [row('c')]
    r = M.binary_assignment_sensitivity(parent,candidate)
    assert r['arms']['parent']['binary_scenario_clusters'] == 2
    assert r['all_unknown_stop_delta_pp'] == 50
    assert r['all_unknown_target_delta_pp'] == 0
    assert r['adverse_targets_to_nonpositive_from_all_stop']['count'] == 1


@pytest.mark.parametrize('damage',['duplicate','shared_identity','unknown_label','samsung'])
def test_invalid_or_conflicting_input_is_not_silently_aggregated(damage):
    parent=[row('p')];candidate=deepcopy(parent)
    if damage=='duplicate': parent+=deepcopy(parent)
    if damage=='shared_identity': candidate[0]['path']['status']='stop'
    if damage=='unknown_label': parent[0]['path']['status']='made_up'
    if damage=='samsung': parent[0]['symbol']='005930'
    with pytest.raises(ValueError): M.binary_assignment_sensitivity(parent,candidate)


def test_same_event_different_entry_is_not_counted_as_same_trace():
    parent=[row('p')];candidate=[row('c',status='stop')]
    events=[dict(event_id='e',first_by_arm=dict(parent_action='p',candidate_action='c'))]
    r=M.compare_selected(parent,candidate,events)
    assert r['shared_trace_count']==0 and r['shared_selected_event_count']==1
    assert r['parent']['event_participation_pct']==100
    assert r['parent_only']['counts']=={'target':1}
    with pytest.raises(ValueError,match='event_binding'):
        M.compare_selected(parent,candidate,[])


def bar(r,seconds=60,high=100.1):
    return dict(t=F.epoch(r)+seconds,open=100,high=high,low=99.9,close=100)


def test_preentry_partial_high_does_not_establish_trailing_reach():
    r=row('a')
    result=M.bar_reach_diagnostic(r,[bar(r,30,102),bar(r,90)],policy=POLICY)
    assert result['status']=='not_observed_in_available_full_bars'
    assert result['partial_bar_excluded'] is True
    assert result['actual_trailing_armed_proven'] is False


def test_reach_beyond_gap_is_observation_not_continuous_replay():
    r=row('a')
    result=M.bar_reach_diagnostic(r,[bar(r,60),bar(r,1200,102)],policy=POLICY)
    assert result['status']=='observed_full_bar_reach'
    assert result['max_interval_sec']>90
    assert not result['actual_trailing_armed_proven']


@pytest.mark.parametrize('damage',['cost','entry','empty','bad_bar'])
def test_invalid_reach_sources_remain_unknown(damage):
    r=row('a');bars=[bar(r)]
    if damage=='cost':r['features']['entry_cost_pct']=None
    if damage=='entry':r['reference_price']=None
    if damage=='empty':bars=[]
    if damage=='bad_bar':bars[0]['high']=float('nan')
    result=M.bar_reach_diagnostic(r,bars,policy=POLICY)
    assert result['status']=='not_evaluable' and result['trailing_start_observed'] is None


def test_reach_ignores_future_session_and_rejects_duplicate_clock():
    r=row('a');b=bar(r)
    assert not M.bar_reach_diagnostic(r,[b,bar(r,3601,102)],policy=POLICY)['trailing_start_observed']
    with pytest.raises(ValueError,match='clock'):
        M.bar_reach_diagnostic(r,[b,b],policy=POLICY)


def test_cross_table_keeps_unknown_exit_as_null_not_loss_and_checks_coverage():
    r=row('a');reach={'a':dict(status='observed_full_bar_reach')}
    paths={w:{'a':dict(status='horizon_censored',net_pct=None,rule=None)} for w in ('weak','strong')}
    result=M.exit_cross_table([r],reach,paths)
    assert len(result['cells'])==2 and all(c['exit_sign']=='unknown' for c in result['cells'])
    assert result['scenarios']['weak']['mean_price_cf_pct'] is None
    paths['weak']['a']['net_pct']=0
    with pytest.raises(ValueError,match='numeric_outcome'):M.exit_cross_table([r],reach,paths)
    paths['weak'].pop('a')
    with pytest.raises(KeyError):M.exit_cross_table([r],reach,paths)
