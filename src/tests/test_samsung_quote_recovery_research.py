from copy import deepcopy

import pytest

from src.engine.scalping import samsung_quote_recovery_research as Q


def cache(n=2800,step=.25):
    rows=[dict(t=i*step,ex=i*step,ep=1,seq=i+1,continuous=True,
        valid=True,flow_valid=True,p=270000.,q=10.,side='SELL') for i in range(n)]
    depth=[dict(t=i*step-.1,ex=i*step-.1,ep=1,seq=i+1,continuous=True,valid=True,
        bid=270000.,ask=270500.,bq=100.,aq=100.) for i in range(n)]
    event=dict(id='a',day='2026-10-02',start=0.,start_index=0,epoch=1,shock_sequence=1,
        signals={'recovery_only':dict(index=3,t=.75,price=270500.)})
    return dict(rows=rows,depth=depth,events=[event])


def test_unchanged_bbo_trade_price_bounce_is_not_quote_recovery():
    c=cache(100)
    for r in c['rows'][4:]:r['p']=270500.
    event=Q.build_signals(c)[0]
    assert event['signals']=={}
    assert event['baseline_signal']['price']==270500.


def test_first_bid_recovery_is_past_only_and_prefix_invariant():
    c=cache(100)
    for q in c['depth'][12:]:q.update(bid=270500.,ask=271000.)
    event=Q.build_signals(c)[0]
    signal=event['signals']['bid_recovery']
    assert signal['index']==12 and signal['low_bid_asof']==270000.
    prefix=deepcopy(c);prefix['rows']=prefix['rows'][:13];prefix['depth']=prefix['depth'][:13]
    assert Q.build_signals(prefix)[0]['signals']['bid_recovery']==signal


def test_midpoint_rise_from_spread_widening_is_rejected():
    c=cache(100)
    for q in c['depth'][12:]:q['ask']=271500.
    assert 'mid_recovery' not in Q.build_signals(c)[0]['signals']


def test_persistence_requires_two_seconds_and_distinct_depth_receipts():
    c=cache(100)
    for q in c['depth'][12:]:q.update(bid=270500.,ask=271000.)
    s=Q.build_signals(c)[0]['signals']
    assert s['sustained_bid']['t']-s['bid_recovery']['t']>=2
    sparse=deepcopy(c);sparse['depth']=sparse['depth'][:13]
    assert 'sustained_bid' not in Q.build_signals(sparse)[0]['signals']


def test_absorption_hold_precedes_recovery_and_persistence():
    c=cache(150)
    for q in c['depth'][32:]:q.update(bid=270500.,ask=271000.)
    signal=Q.build_signals(c)[0]['signals']['absorption_then_bid']
    assert signal['absorption_receipt']['t']>=5
    assert signal['absorption_receipt']['t']<signal['t']
    assert signal['bid']>=signal['absorption_receipt']['bid']+500
    assert signal['t']>=10


@pytest.mark.parametrize('defect',['invalid','sequence','epoch'])
def test_quote_defect_does_not_connect_old_low_to_recovery(defect):
    c=cache(100)
    if defect=='invalid':c['depth'][11]['valid']=False
    if defect=='sequence':
        for q in c['depth'][12:]:q['seq']+=10
    if defect=='epoch':
        for q in c['depth'][12:]:q['ep']=2
    for q in c['depth'][12:]:q.update(bid=270500.,ask=271000.)
    assert 'bid_recovery' not in Q.build_signals(c)[0]['signals']


def test_trade_flow_break_stops_event_before_later_signal():
    c=cache(100);c['rows'][8]['flow_valid']=False
    for q in c['depth'][12:]:q.update(bid=270500.,ask=271000.)
    event=Q.build_signals(c)[0]
    assert event['signals']=={} and event['window_gap']=='trade_flow_discontinuity'


def test_quote_join_excludes_equal_time_future_and_other_epoch():
    d=cache(10)['depth'];times=[q['t'] for q in d]
    assert Q.quote_at(d,times,times[4],1)==3
    assert Q.quote_at(d,times,times[4],2) is None
    assert Q.quote_at(d,times,100,1) is None
    d[5]['valid']=False
    assert Q.quote_at(d,times,times[5]+.01,1) is None


def test_anchors_do_not_depend_on_signal_availability_or_outcome():
    events=[dict(start=t,shock_sequence=i,signals={}) for i,t in enumerate([0.,1.,841.,842.])]
    assert [e['start'] for e in Q.select_anchors(events)]==[0.,842.]


def test_first_qualifying_signals_reserve_both_windows_and_keep_gap_attempt():
    events=[dict(id=str(i),shock_sequence=i,baseline_signal=dict(t=t-20),
        signals={'bid_recovery':dict(t=t)}) for i,t in enumerate([20.,40.,620.,642.])]
    assert [e['id'] for e in Q.select_signal_events(events,'bid_recovery')]==['0','3']
    events[0]['outcome']='missing'
    assert Q.select_signal_events(events,'bid_recovery')[0]['id']=='0'


def entry(c):
    ctx=Q.context(c)
    e=Q.entry_for(ctx,c['events'][0]['signals']['recovery_only'])
    return ctx,e


def test_ask_entry_bid_exit_neither_is_binary_null():
    ctx,e=entry(cache())
    out=Q.quote_label(ctx,e,e['t']+600)
    assert e['price']==270500 and out['exit_bid']==270000
    assert out['binary'] is None and out['path_complete'] and out['strict_complete']
    assert out['net']==pytest.approx((270000/270500-1)*100-.33)
    assert out['max_net_cf']==out['net']==out['deadline_net_cf']


def test_entry_ask_is_bound_to_exact_past_quote():
    ctx,e=entry(cache());e['price']=270000.
    with pytest.raises(ValueError,match='binding_invalid'):
        Q.quote_label(ctx,e,e['t']+600)


def test_short_identified_invalid_row_excluded_without_interpolation():
    c=cache();c['depth'][100]['valid']=False
    ctx,e=entry(c);out=Q.quote_label(ctx,e,e['t']+600)
    assert out['path_complete'] and not out['strict_complete']
    assert out['excluded_quote_rows']==1
    c['depth'][100]['bid']=9999999.
    ctx,e=entry(c)
    assert Q.quote_label(ctx,e,e['t']+600)['binary'] is None


def test_long_missing_quote_interval_cannot_be_a_loss_or_no_edge():
    c=cache()
    for q in c['depth'][100:110]:q['valid']=False
    ctx,e=entry(c);out=Q.quote_label(ctx,e,e['t']+600)
    assert out['net'] is None and out['status']=='quote_path_gap'


def test_known_target_before_gap_preserved_but_excluded_from_support():
    c=cache()
    for q in c['depth'][100:200]:q.update(bid=272000.,ask=272500.)
    for q in c['depth'][300:310]:q['valid']=False
    ctx,e=entry(c);out=Q.quote_label(ctx,e,e['t']+600)
    assert out['binary']==1 and not out['path_complete']
    assert Q.E.metric([out])['evaluable']==0


def test_raw_epoch_break_after_last_valid_endpoint_is_not_complete():
    c=cache();ctx,e=entry(c);deadline=e['t']+600
    q=next(q for q in c['depth'] if q['t']>deadline-.1)
    q.update(t=deadline-.01,ep=2,valid=False)
    ctx,e=entry(c);out=Q.quote_label(ctx,e,deadline)
    assert not out['path_complete']


def test_common_deadline_and_own_horizon_are_distinct():
    c=cache();ctx,e=entry(c)
    for q in c['depth']:
        if q['t']>610:q.update(bid=272000.,ask=272500.)
    ctx,e=entry(c)
    assert Q.quote_label(ctx,e,600)['binary'] is None
    assert Q.quote_label(ctx,e,650)['binary']==1


def test_endpoint_prices_remain_diagnostic_when_interim_quotes_are_missing():
    c=cache()
    for q in c['depth'][100:110]:q['valid']=False
    ctx,e=entry(c)
    newer=Q.entry_for(ctx,dict(index=20,t=5.,price=270000.))
    assert not Q.quote_label(ctx,e,600)['path_complete']
    point=Q.endpoint_comparison(ctx,e,newer,600)
    assert point['comparable'] and point['delta']==0
    assert 'not_target_first' in point['metric_role']


def test_endpoint_rejects_stale_quote_and_trade_epoch_break():
    c=cache();ctx,e=entry(c)
    newer=Q.entry_for(ctx,dict(index=20,t=5.,price=270000.))
    for q in c['depth'][2390:2410]:q['valid']=False
    ctx=Q.context(c)
    assert Q.endpoint_comparison(ctx,e,newer,600)['status']=='endpoint_quote_missing'
    c['rows'][500]['valid']=False;ctx=Q.context(c)
    assert Q.endpoint_comparison(ctx,e,newer,600)['status']=='trade_path_gap'


def label(binary,net=.1):
    return dict(binary=binary,net=net,status='neither' if binary is None else 'target_first' if binary else 'stop_first',
        path_complete=True,strict_complete=True,deadline_net_cf=net)


def comparison(i,a,b):
    return dict(id=str(i),labels=dict(baseline=label(a),candidate=label(b)),
        entries=dict(baseline=dict(t=1.,price=270500.),candidate=dict(t=2.,price=271000.)),
        signal_status='observed',feature_resets=0)


def test_selection_can_lose_old_winner_and_have_negative_cf():
    rows=[comparison(i,a,b) for i,(a,b) in enumerate([(1,0),(0,1),(0,1),(0,1)])]
    for r in rows:r['labels']['candidate']['net']=-.5
    training={recipe:deepcopy(rows) for recipe in Q.RECIPES}
    before=deepcopy(training);winner,_=Q.choose(training)
    assert winner['recipe']=='bid_recovery'
    assert winner['paired']['lost_targets']==1 and winner['policy']['win_rate_delta']==.5
    assert training==before


def test_admission_filter_effect_is_separate_from_same_entry_pair_effect():
    rows=[comparison(i,1,1) for i in range(3)]
    for i in range(3,6):
        row=comparison(i,0,0);row['labels']['candidate']=Q.missing('entry_missing')
        row.update(signal_status='not_reached',feature_resets=0)
        rows.append(row)
    winner,_=Q.choose({r:deepcopy(rows) for r in Q.RECIPES})
    assert winner['policy']['win_rate_delta']==.5 and winner['paired']['win_rate_delta']==0
    assert winner['policy']['not_admitted']==3
    rows[-1]['feature_resets']=1
    assert Q.policy_comparison(rows)['excluded']==1


def test_insufficient_binary_support_does_not_select_neither_as_losses():
    rows=[comparison(i,None,1) for i in range(10)]
    winner,candidates=Q.choose({r:deepcopy(rows) for r in Q.RECIPES})
    assert winner is None and candidates[0]['policy']['baseline']['win_rate'] is None


def test_cache_and_report_seal_research_only_price_authority(tmp_path):
    p=tmp_path/'cache.gz';Q.write_cache(p,{'runtime_effect':True})
    body=Q.E.read_cache(p)
    assert not body['runtime_effect'] and body['price_basis']==Q.AUTHORITY['price_basis']
    Q.write_cache(p,body)
    assert Q.E.read_cache(p)==body
    report=tmp_path/'report.json';Q.write(report,{'status':'pass'})
    assert not Q.R.read(report)['native_promotion_support']


def test_locked_price_sensitivity_preserves_clock_and_crossed_gaps():
    depth=cache(10)['depth'];depth[2].update(ask=270000.,valid=False)
    depth[3].update(ask=270000.,valid=False,ex=-100.)
    depth[4].update(ask=269500.,valid=False)
    before=deepcopy(depth);restored,count=Q.locked_price_context(depth)
    assert count==1 and restored[2]['valid']
    assert not restored[3]['valid'] and not restored[4]['valid']
    assert depth==before
