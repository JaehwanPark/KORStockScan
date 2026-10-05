import json
import pytest

from src.engine.scalping.entry_archive_continuity_research import (
    bind_anchor_lease, lease_intervals, parse_lease_log, receipt_bound_exit,
)

DAY = '2026-10-02'

def line(clock, **values):
    p = dict(item='001210_AL', lease_id='one', transport_epoch=1, **values)
    return f'[{DAY} {clock}] [ZERO_BASE_EXACT_WS_LEASE] '+json.dumps(p)

def pair():
    return lease_intervals(parse_lease_log([
        line('12:07:49', created=True, registered=True),
        line('12:08:07', phase='released', actual_order_submitted=False),
    ], day=DAY))

def row(ts='12:08:00.100404', item='001210_AL'):
    return dict(symbol='001210', request_code=item, ts=f'{DAY}T{ts}+09:00')

def target():
    return pair()[0]['release']['at_upper']+100

def test_exact_receipt_preserves_time_interval_and_no_capture_authority():
    b=bind_anchor_lease(row(),pair(),target_at=target())
    assert b['status']=='entry_within_closed_lease'
    assert b['released_definitely_before_target']
    assert b['release_after_entry_lower_sec']==pytest.approx(6.899596)
    assert b['continuous_capture_verified'] is False
    assert b['collector_transport_epoch_binding_verified'] is False

def test_release_same_second_as_entry_is_ambiguous():
    b=bind_anchor_lease(row('12:08:07.7'),pair(),target_at=target())
    assert b['status']=='entry_lease_second_boundary_ambiguous'

def test_different_route_cannot_bind():
    assert bind_anchor_lease(row(item='001210_NX'),pair(),target_at=target())['lease'] is None

def test_after_release_is_not_an_active_lease():
    assert bind_anchor_lease(row('12:08:08'),pair(),target_at=target())['lease'] is None

def test_missing_release_is_explicit_not_continuous():
    data=pair();data[0]['release']=None
    assert bind_anchor_lease(row(),data,target_at=target())['status']=='entry_lease_release_missing'

def test_epoch_mismatch_never_pairs_create_and_release():
    records=parse_lease_log([line('12:07:49',created=True,registered=True),line('12:08:07',phase='released',actual_order_submitted=False)],day=DAY)
    records[1]['transport_epoch']=2
    assert all(x['status']=='incomplete_receipt' for x in lease_intervals(records))

def test_duplicate_phase_and_malformed_record_fail():
    r=parse_lease_log([line('12:07:49',created=True,registered=True)],day=DAY)
    with pytest.raises(ValueError,match='duplicate'):lease_intervals(r+r)
    with pytest.raises(ValueError):parse_lease_log([f'[{DAY} 12:00:00] [ZERO_BASE_EXACT_WS_LEASE] {{bad'],day=DAY)

def test_unconfirmed_registration_is_not_a_lease():
    assert lease_intervals(parse_lease_log([line('12:07:49',created=True,registered=False)],day=DAY))==[]

def test_overlapping_lease_records_are_ambiguous():
    intervals=pair();other={**intervals[0],'lease_id':'other'}
    assert bind_anchor_lease(row(),intervals+[other],target_at=target())['status']=='overlapping_lease_identity_ambiguous'

@pytest.mark.parametrize('delta,status',[(2,'probe_release_precedes_exit'),(.5,'probe_release_exit_order_ambiguous')])
def test_exit_after_release_does_not_remain_evaluable(delta,status):
    b=bind_anchor_lease(row(),pair(),target_at=target())
    old=dict(status='conditional_archive_exit',net_pct=-2,exit_at=pair()[0]['release']['at_lower']+delta,exit_price=100,runtime_net_pct=-1.4,rule='hard_stop')
    out=receipt_bound_exit(old,b)
    assert out['status']==status
    assert all(out[k] is None for k in ('net_pct','exit_at','exit_price','runtime_net_pct','rule'))
    assert out['previous_conditional_path']==old and old['net_pct']==-2

def test_nonterminal_keeps_missing_value_and_reason():
    old=dict(status='archive_epoch_changed',net_pct=None,exit_at=None)
    assert receipt_bound_exit(old,bind_anchor_lease(row(),pair(),target_at=target()))['status']==old['status']

def test_exit_before_release_is_still_only_conditional():
    b=bind_anchor_lease(row(),pair(),target_at=target())
    out=receipt_bound_exit(dict(status='conditional_archive_exit',net_pct=.2,exit_at=pair()[0]['release']['at_lower']-1),b)
    assert out['net_pct']==.2 and out['continuous_capture_verified'] is False

def test_foreign_day_ignored_and_release_authority_validated():
    assert parse_lease_log([line('12:08:07',phase='released',actual_order_submitted=False)],day='2026-10-03')==[]
    with pytest.raises(ValueError,match='authority'):
        parse_lease_log([line('12:08:07',phase='released',actual_order_submitted=True)],day=DAY)

def test_restart_log_context_does_not_carry_unclosed_old_epoch_one_lease():
    logs=[line('10:00:00',created=True,registered=True),
          f'[{DAY} 11:00:00] [WS] 웹소켓 매니저 초기화 완료 (Target: example)',
          line('12:07:49',created=True,registered=True).replace('"one"','"two"'),
          line('12:08:07',phase='released',actual_order_submitted=False).replace('"one"','"two"')]
    intervals=lease_intervals(parse_lease_log(logs,day=DAY))
    b=bind_anchor_lease(row(),intervals,target_at=target())
    assert b['status']=='entry_within_closed_lease'
    assert b['lease']['lease_id']=='two'
    assert intervals[0]['release'] is None
