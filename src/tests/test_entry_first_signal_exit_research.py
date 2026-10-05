from copy import deepcopy
import pytest
from src.engine.scalping import entry_first_signal_exit_research as R

POLICY=dict(start_pct=.4,weak_pct=.4,strong_pct=.8,hard_stop_net_pct=-1.4,
    emergency_stop_net_pct=-2.4,runtime_cost_rate=.0023)


def row(trace, *, second=0, parent='RECHECK', candidate='RECHECK', bundle='a'):
    return dict(trace=trace,day='2026-10-02',ts=f'2026-10-02T09:00:{second:02}+09:00',
        group='non_samsung',symbol='000660',outcome_request_code='000660_AL',
        source_bundle_sha256=bundle,parent_action=parent,candidate_action=candidate,
        reference_price=100,features=dict(entry_cost_pct=.3),
        capture_valid=True,reference_type='executable_ask')


def test_first_signal_is_action_only_and_uses_same_union_event():
    rows=[row('a'),row('b',second=1,candidate='ENTER_NOW'),
        row('c',second=2,parent='ENTER_NOW',candidate='ENTER_NOW'),row('d',second=3)]
    events=R.first_signal_events(rows)
    assert len(events)==1 and not events[0]['left_censored']
    assert events[0]['first_by_arm']==dict(candidate_action='b',parent_action='c')
    assert events[0]['closed_by_trace']=='d'
    changed=deepcopy(rows)
    for r in changed:r['future_outcome']='loss';r['path']={'status':'target'}
    assert R.first_signal_events(changed)==events
    assert [r['trace'] for r in R.mask_first_signals(rows,events) if r['candidate_action']=='ENTER_NOW']==['b']


def test_lineage_switch_cannot_merge_two_runs_with_same_restored_bundle():
    events=R.first_signal_events([row('a',candidate='ENTER_NOW'),
        row('b',second=1,candidate='ENTER_NOW',bundle='b'),row('c',second=2,candidate='ENTER_NOW')])
    assert len(events)==3 and all(e['left_censored'] for e in events)


def test_observation_gap_is_reported_not_filled_with_synthetic_events():
    a=row('a',candidate='ENTER_NOW');b=row('b',candidate='ENTER_NOW');b['ts']='2026-10-02T09:20:00+09:00'
    e=R.first_signal_events([a,b])[0]
    assert e['left_censored'] and e['max_internal_observation_gap_sec']==1200


def test_duplicate_or_samsung_rows_are_rejected():
    r=row('a')
    with pytest.raises(ValueError,match='duplicate'):R.first_signal_events([r,r])
    r['symbol']='005930'
    with pytest.raises(ValueError,match='scope'):R.first_signal_events([r])


def bar(anchor, *, seconds=60, o=100, h=100.1, low=99.9, close=100):
    return dict(t=R.epoch(anchor)+seconds,open=o,high=h,low=low,close=close)


def test_shared_kernel_trails_after_arm_and_gap_opens_are_not_backfilled():
    r=row('a');b=bar(r,o=101,h=101,low=100,close=100)
    result=R.bar_exit_scenario(r,[b],policy=POLICY,strong=False)
    assert result['status']=='conditional_bar_exit' and result['rule']=='trailing'
    assert result['exit_price']==pytest.approx(101*.996,abs=1e-6)
    gap=bar(r,o=97,h=97.1,low=96.9,close=97)
    result=R.bar_exit_scenario(r,[gap],policy=POLICY,strong=False)
    assert result['rule']=='emergency_stop' and result['exit_price']==97


def test_first_partial_bar_cannot_arm_from_preentry_high():
    r=row('a',second=30)
    b=bar(r,seconds=30,o=100,h=102,low=100,close=101)
    result=R.bar_exit_scenario(r,[b],policy=POLICY,strong=False)
    assert result['status']=='first_partial_bar_ambiguous' and result['net_pct'] is None


def test_intrabar_unknown_order_is_not_resolved_in_favour_of_profit():
    r=row('a');b=bar(r,o=100,h=101,low=99.9,close=100.9)
    result=R.bar_exit_scenario(r,[b],policy=POLICY,strong=False)
    assert result['status']=='intrabar_exit_order_ambiguous' and result['net_pct'] is None


def test_cost_missing_gap_and_censoring_never_become_zero_profit():
    r=row('a');b=bar(r,seconds=120)
    assert R.bar_exit_scenario(r,[b],policy=POLICY,strong=False)['status']=='price_gap'
    r['features']['entry_cost_pct']=None
    assert R.bar_exit_scenario(r,[b],policy=POLICY,strong=False)['status']=='cost_missing'
    r=row('a');bars=[bar(r,seconds=i*60) for i in range(1,61)]
    result=R.bar_exit_scenario(r,bars,policy=POLICY,strong=False)
    assert result['status']=='horizon_censored' and result['net_pct'] is None
    assert result['mark_to_close_cf_pct']==pytest.approx(-.3)


def test_exit_policy_cannot_silently_default_missing_stop_or_cost():
    broken=dict(POLICY);broken.pop('hard_stop_net_pct')
    with pytest.raises(ValueError,match='policy_invalid'):
        R.bar_exit_scenario(row('a'),[],policy=broken,strong=False)


def point(r, seconds, kind, sequence, *, bid=100, trade=100, age=0, transport=1):
    return dict(t=R.epoch(r)+seconds,item='000660_AL',kind=kind,sequence=sequence,
        epoch=transport,bid=bid,ask=bid+.1,trade_price=trade,quote_age_ms=age,source_valid=True)


def test_archive_peak_uses_postentry_trade_and_exit_uses_observed_bid():
    r=row('a');r['request_code']='000660_AL'
    points=[point(r,-1,'trade',1,trade=105),point(r,-.5,'depth',1,bid=104),
        point(r,.1,'depth',2,bid=103),point(r,.2,'depth',3,bid=100),
        point(r,.3,'trade',2,trade=101,bid=101),point(r,.4,'depth',4,bid=100.5)]
    result=R.archive_exit_scenario(r,points,policy=POLICY,strong=False)
    assert result['status']=='conditional_archive_exit' and result['rule']=='trailing'
    assert result['exit_price']==100.5 and result['peak_trade_price']==101
    assert result['eligible_quote_updates']==4  # quote-only rise did not create a peak


@pytest.mark.parametrize('change,status',[
    ({'sequence':4},'archive_sequence_gap'),({'epoch':2},'archive_epoch_changed'),
    ({'item':'000660_NX'},'archive_item_mismatch'),({'source_valid':False},'archive_source_invalid')])
def test_archive_gap_or_route_failure_cannot_select_later_profitable_exit(change,status):
    r=row('a');r['request_code']='000660_AL'
    points=[point(r,-1,'trade',1),point(r,-.5,'depth',1),
        {**point(r,1,'trade',2,trade=101,bid=101),**change},point(r,2,'depth',2,bid=100.5)]
    p=R.archive_exit_scenario(r,points,policy=POLICY,strong=False)
    assert p['status']==status and p['net_pct'] is None


def test_archive_stale_quote_does_not_exit_and_missing_endpoint_is_not_loss():
    r=row('a');r['request_code']='000660_AL'
    points=[point(r,-1,'trade',1),point(r,-.5,'depth',1),
        point(r,1,'trade',2,trade=98,bid=98,age=701)]
    assert R.archive_exit_scenario(r,points,policy=POLICY,strong=False)['status']=='archive_endpoint_unobserved'


def test_same_millisecond_trade_sequence_proves_order_but_cross_stream_tie_does_not():
    r=row('a');r['request_code']='000660_AL'
    points=[point(r,-1,'trade',1),point(r,-.5,'depth',1),
        point(r,1,'trade',2,trade=101,bid=101),point(r,1,'trade',3,trade=100.5,bid=100.5)]
    assert R.archive_exit_scenario(r,points,policy=POLICY,strong=False)['status']=='conditional_archive_exit'
    points[-1]=point(r,1,'depth',2,bid=100.5)
    assert R.archive_exit_scenario(r,points,policy=POLICY,strong=False)['status']=='archive_clock_or_tie_ambiguous'


def test_cross_stream_tie_cannot_return_first_arbitrarily_ordered_exit():
    r=row('a');r['request_code']='000660_AL'
    points=[point(r,-1,'trade',1),point(r,-.5,'depth',1),
        point(r,1,'trade',2,trade=98,bid=98),point(r,1,'depth',2,bid=100)]
    p=R.archive_exit_scenario(r,points,policy=POLICY,strong=False)
    assert p['status']=='archive_clock_or_tie_ambiguous' and p['net_pct'] is None
