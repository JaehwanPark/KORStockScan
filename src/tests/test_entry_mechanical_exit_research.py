from copy import deepcopy
from datetime import datetime
import pytest

from src.engine.scalping import entry_mechanical_exit_research as M
from src.engine.scalping.trailing_mechanical_strength import CONFIG_DEFAULTS

POLICY=dict(start_pct=.4,weak_pct=.4,strong_pct=.8,hard_stop_net_pct=-1.4,
    emergency_stop_net_pct=-2.4,runtime_cost_rate=.0023)


def anchor():
    return dict(ts='2026-10-02T09:00:00+09:00',day='2026-10-02',symbol='000660',
        tags=dict(venue='KRX',session='KRX_REGULAR'),request_code='000660_AL',
        reference_price=10000,reference_type='executable_ask',capture_valid=True,
        features=dict(entry_cost_pct=.3))


def point(kind, seq, delta, *, bid=10000, price=10000, raw='+10', qty=10, bq=10, aq=10):
    p=dict(kind=kind,t=datetime.fromisoformat(anchor()['ts']).timestamp()+delta,
        item='000660_AL',epoch=1,sequence=seq,source_valid=True,
        bid=bid,ask=bid+10,quote_age_ms=0,trade_price=price)
    if kind=='trade':p.update(M.recover_signed_trade(raw,qty));p['trade_volume_raw']=raw
    else:p.update(bid_levels=[dict(price=bid,quantity=bq)],ask_levels=[dict(price=bid+10,quantity=aq)])
    return p


def prefix():return [point('trade',1,-.2),point('depth',1,-.1)]


@pytest.mark.parametrize('raw,qty,side', [('+1,200',1200,'BUY'),(' -35 ',35,'SELL'),('+0004',4,'BUY')])
def test_original_signed_integer_recovers_primary_source(raw,qty,side):
    p=M.recover_signed_trade(raw,qty)
    assert p['aggressor_side']==side and p['volume']==qty
    assert p['aggressor_source']=='kiwoom_0b_signed_trade_volume'


@pytest.mark.parametrize('raw,qty', [('123',123),('+0',0),('-0',0),('+1.5',1.5),('+10',9),('+10',True),(None,5),('+1,,000',1000)])
def test_missing_sign_or_quantity_conflict_cannot_become_trusted_tape(raw,qty):
    p=M.recover_signed_trade(raw,qty)
    assert p['aggressor_side']=='UNKNOWN' and p['aggressor_source'] is None


def test_real_classifier_changes_width_using_postentry_book_and_signed_tape():
    points=prefix()+[point('trade',2,.1,price=10100,bid=10100,raw='+30',qty=30),
        point('depth',2,.2,bid=10100,bq=20,aq=5),
        point('depth',3,.3,bid=10050,bq=30,aq=5),point('depth',4,.4,bid=10010,bq=30,aq=5)]
    before=deepcopy(points)
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    assert points==before
    assert r['paths']['weak']['exit_price']==10050
    assert r['paths']['mechanical']['exit_price']==10010
    assert r['paths']['mechanical']['classifier_state']=='STRONG'
    assert r['paths']['mechanical']['net_pct']==pytest.approx(-.2)
    assert any(j['reason']=='book_and_trade_support' for j in r['journal'])
    assert r['journal'][0]['trade_receipts'][0]['sequence']==2  # pre-entry tape excluded


def test_missing_signed_tape_stays_unknown_and_runtime_weak_width_is_explicit():
    points=prefix()+[point('trade',2,.1,price=10100,bid=10100,raw='30',qty=30),
        point('depth',2,.2,bid=10100,bq=20,aq=5),point('depth',3,.3,bid=10050,bq=30,aq=5)]
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    p=r['paths']['mechanical']
    assert p['exit_price']==10050 and p['classifier_state']=='UNKNOWN'
    assert not p['used_strong_width']
    assert r['classifier']['state_counts'].get('STRONG',0)==0


def test_two_adverse_depth_updates_required_to_leave_strong():
    points=prefix()+[point('trade',2,.10,raw='+20',qty=20),point('depth',2,.15,bq=20,aq=5),
        point('trade',3,.20,raw='-40',qty=40),point('depth',3,.25,bq=5,aq=20),
        point('trade',4,.30,raw='-40',qty=40),point('depth',4,.35,bq=4,aq=22)]
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    assert [j['state'] for j in r['journal']]==['STRONG','STRONG','WEAK']
    assert r['journal'][-1]['reason']=='sustained_adverse_evidence'
    assert r['paths']['mechanical']['net_pct'] is None


@pytest.mark.parametrize('change,status',[({'epoch':2},'archive_epoch_changed'),
    ({'sequence':5},'archive_sequence_gap'),({'item':'000660_NX'},'archive_item_mismatch'),
    ({'source_valid':False},'archive_source_invalid')])
def test_source_failure_before_exit_remains_null(change,status):
    points=prefix()+[{**point('trade',2,.1,price=9800,bid=9800),**change}]
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    assert all(p['status']==status and p['net_pct'] is None for p in r['paths'].values())


def test_cross_stream_tie_rejected_before_first_ordered_stop():
    points=prefix()+[point('trade',2,.1,price=9800,bid=9800),point('depth',2,.1)]
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    assert r['paths']['mechanical']['status']=='archive_clock_or_tie_ambiguous'


def test_cost_and_samsung_scope_cannot_silently_enter_replay():
    a=anchor();a['features']['entry_cost_pct']=None
    assert M.replay_modes(a,[],policy=POLICY,config=CONFIG_DEFAULTS)['paths']['mechanical']['status']=='cost_missing'
    a['symbol']='005930'
    with pytest.raises(ValueError,match='scope'):M.replay_modes(a,[],policy=POLICY,config=CONFIG_DEFAULTS)


def test_canonical_adapter_preserves_raw_side_conflict_without_inventing_provenance():
    p=dict(local_receive_timestamp=anchor()['ts'],source_item='000660_AL',sequence_epoch=7,
        series_sequence=9,trade_price=10000,trade_qty=10,best_bid=10000,best_ask=10010,
        quote_age_ms=4,trade_volume_raw='-10',aggressor_side='BUY')
    n=M.normalize_archive_point(p,kind='trade',source_valid=True)
    assert n['recorded_aggressor_side']=='BUY' and n['aggressor_side']=='SELL'
    assert n['trade_volume_raw']=='-10' and n['epoch']==7 and n['sequence']==9


def test_invalid_preentry_depth_cannot_seed_book_support():
    points=prefix();points[-1]['source_valid']=False
    points += [point('trade',2,.1,raw='+20',qty=20),point('depth',2,.2,bq=20,aq=5)]
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    assert r['paths']['mechanical']['status']=='archive_prefix_invalid'
    assert r['classifier']['state_counts']=={}


def test_classifier_statistics_end_at_mechanical_exit_not_later_fixed_arm():
    points=prefix()+[point('trade',2,.1,price=10100,bid=10100,raw='+30',qty=30),
        point('depth',2,.2,bid=10100,bq=2,aq=20),point('depth',3,.3,bid=10050,bq=2,aq=20),
        point('depth',4,.4,bid=10060,bq=30,aq=1),point('depth',5,.5,bid=10010,bq=30,aq=1)]
    r=M.replay_modes(anchor(),points,policy=POLICY,config=CONFIG_DEFAULTS)
    assert r['paths']['mechanical']['exit_at']<r['paths']['strong']['exit_at']
    assert r['classifier']['state_counts'].get('STRONG',0)==0
    assert all(j['evaluation_at_ms']<=round(r['paths']['mechanical']['exit_at']*1000) for j in r['journal'])
