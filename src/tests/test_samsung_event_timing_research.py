"""Regression of event chronology, paired denominators and conditional exits."""
from copy import deepcopy

import pytest

from src.engine.scalping import samsung_event_timing_research as E


def stream(n=1901):
    return [dict(t=float(i),ex=float(i),ep=1,seq=i+1,continuous=True,
        p=270000.,q=100.,side='BUY' if i%2 else 'SELL',valid=True,flow_valid=True)
        for i in range(n)]


def label(binary=None, net=-.3, complete=True):
    return dict(binary=binary,net=net,path_complete=complete,
        status='neither' if binary is None else 'target_first' if binary else 'stop_first')


def comparison(early,later,idx=0):
    return dict(id=str(idx),labels={'event_now':early,'minute_wait':later},
        entries={'event_now':{'t':0.,'price':270000.},'minute_wait':{'t':30.,'price':270500.}})


def test_shock_threshold_excludes_current_quantity_and_future_low():
    rows=stream(100);rows[25].update(q=1000.,side='SELL')
    rows[26]['p']=269500.;rows[27]['p']=270000.
    rows[80]['p']=260000.
    events=E.build_events(rows,'2026-10-02')
    first=events[0]
    assert first['past_only_threshold']==300
    assert first['signals']['recovery_only']['index']==27
    assert first['signals']['recovery_only']['low_asof']==269500
    assert first['signals']['recovery_only']['price']==270000
    prefix=E.build_events(rows[:28],'2026-10-02')
    assert prefix[0]['signals']['recovery_only']==first['signals']['recovery_only']


@pytest.mark.parametrize('defect',['epoch','sequence','clock_gap','invalid_flow'])
def test_event_does_not_recover_across_input_defect(defect):
    rows=stream(45);rows[25].update(q=1000.,side='SELL');rows[26]['p']=269500.
    if defect=='epoch':
        for r in rows[27:]:r['ep']=2
    if defect=='sequence':rows[27]['seq']=999
    if defect=='clock_gap':
        for r in rows[27:]:r['t']+=15
    if defect=='invalid_flow':rows[27]['flow_valid']=False
    event=E.build_events(rows,'2026-10-02')[0]
    assert 'recovery_only' not in event['signals']


def test_decay_confirmation_is_past_only_and_occurs_after_ten_seconds():
    rows=stream(60);rows[25].update(q=1000.,side='SELL')
    for r in rows[26:35]:r.update(p=269500.,q=100.,side='SELL')
    for r in rows[35:]:r.update(p=270000.,q=10.,side='BUY')
    first=E.build_events(rows,'2026-10-02')[0]
    signal=first['signals']['sell_decay']
    assert signal['t']>=35 and signal['sell_decay']<=.75
    prefix=E.build_events(rows[:signal['index']+1],'2026-10-02')
    assert prefix[0]['signals']['sell_decay']==signal


def test_same_receipt_time_observed_entry_never_goes_back_in_sequence():
    rows=stream(20)
    rows[10]['t']=rows[11]['t']=11.
    times=[r['t'] for r in rows];ends=E.price_segments(rows)
    original=dict(index=11,t=11.,price=rows[11]['p'])
    observed=E.observed_entry(rows,times,ends,original,11.)
    assert observed['index']==11


def test_tick_label_neither_is_null_and_crossing_price_is_observed():
    rows=stream(700);times=[r['t'] for r in rows];entry=dict(index=0,t=0.,price=270000.)
    nohit=E.tick_label(rows,times,E.price_segments(rows),entry)
    assert nohit['binary'] is None and nohit['net']==pytest.approx(-.33)
    rows[10]['p']=271500.
    hit=E.tick_label(rows,times,E.price_segments(rows),entry)
    assert hit['binary']==1 and hit['exit_price']==271500
    assert hit['net']==pytest.approx((271500/270000-1)*100-.33)


def test_known_hit_before_later_gap_is_diagnostic_not_full_path_support():
    rows=stream(700);rows[10]['p']=271500.;rows[100]['valid']=False
    times=[r['t'] for r in rows];entry=dict(index=0,t=0.,price=270000.)
    outcome=E.tick_label(rows,times,E.price_segments(rows),entry)
    assert outcome['binary']==1 and not outcome['path_complete']
    m=E.metric([outcome]);assert m['evaluable']==0 and m['censored_known_terminal']==1


def test_gap_before_crossing_is_missing_instead_of_loss():
    rows=stream(700);rows[10]['valid']=False;rows[100]['p']=271500.
    outcome=E.tick_label(rows,[r['t'] for r in rows],E.price_segments(rows),dict(index=0,t=0.,price=270000.))
    assert outcome['status']=='path_source_gap' and outcome['net'] is None


def test_paired_population_keeps_both_arms_same_event_and_excludes_source_gap():
    data=[comparison(label(1,.1),label(None,-.2),0),
        comparison(label(0,-1.),label(1,.1),1),
        comparison(label(1,.1),label(None,None,False),2)]
    pair=E.paired(data)
    assert pair['event_ids']==['0','1'] and pair['comparable']==2
    assert pair['gained_targets']==pair['lost_targets']==1
    assert pair['mean_net_delta']==pytest.approx(-.4)


def test_missing_first_signal_reserves_future_events_before_any_outcome():
    events=[dict(start=t,shock_sequence=i,signals={'recovery_only':{'t':t+1}})
        for i,t in enumerate([0.,50.,841.,842.])]
    chosen=E.select_events(events,'recovery_only')
    assert [e['start'] for e in chosen]==[0.,842.]


def test_confirmation_receipt_missing_does_not_select_later_good_confirmation():
    rows=stream(200);rows[60]['valid']=False
    grid=[dict(t=60.,features={'past_up':True,'range_location':.2}),
        dict(t=120.,features={'past_up':True,'range_location':.2})]
    result=E.arms(rows,[r['t'] for r in rows],E.price_segments(rows),grid,dict(index=1,t=1.,price=270000.))
    assert result['bar_confirmation'] is None


def test_recipe_fit_does_not_read_held_results_or_preserve_all_winners():
    training={recipe:[comparison(label(1,.1),label(0,-1.),i) for i in range(3)] for recipe in E.RECIPES}
    before=deepcopy(training);winner,candidates=E.choose_recipe(training)
    assert winner['recipe']=='recovery_only' and training==before
    assert len(candidates)==4


def test_conditional_exit_gate_requires_pair_count_net_and_target_effect():
    data=[comparison(label(1,.1),label(None,-.2),i) for i in range(3)]
    assert E.exit_gate(E.paired(data))['allowed']
    assert not E.exit_gate(E.paired(data[:2]))['allowed']
    unchanged=[comparison(label(1,.1),label(1,.1),i) for i in range(3)]
    assert not E.exit_gate(E.paired(unchanged))['allowed']


def test_exit_population_demands_same_source_for_every_horizon_endpoint():
    rows=stream();signal=dict(index=0,t=0.,price=270000.)
    # Continuous 30 minutes, but the ten-minute endpoint's price is stale.
    del rows[598:601]
    for i,r in enumerate(rows):r['seq']=i+1
    cache=dict(rows=rows,events=[dict(id='a',day='2026-10-02',start=0.,shock_sequence=1,
        signals={'recovery_only':signal})])
    population=E.exit_population(cache,'recovery_only')
    assert not population[0]['full_30min_source'] and population[0]['labels']==[None]*18


def test_report_seal_preserves_event_metric_authority(tmp_path):
    p=tmp_path/'report.json';E.write(p,{'status':'pass'})
    report=E.R.read(p)
    assert report['primary_decision_metric']==E.AUTHORITY['primary_decision_metric']
    assert report['native_promotion_support'] is False and report['runtime_effect'] is False
