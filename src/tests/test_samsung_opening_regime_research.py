from copy import deepcopy

from src.engine.scalping import samsung_opening_regime_research as O


def f(at='2026-10-02T09:03:00+09:00'):
    return dict(index=0,t=O.R.epoch(at),ep=1,hour=9,bid=272000.,ask=272500.,spread=500.,
        hold=5,hold_quotes=10,sell_count=10,sell_dominant=True,buy_share=.6,prior_buy_share=.3,
        sell_decay=.4,volume_acceleration=2.,windows={'180':dict(distance=0.,drawdown=1500.)})


def rule(anchor='none'):
    return dict(family='sell_decay',window=180,level=2,region='all',opening_minutes=15,anchor=anchor)


def test_preopen_high_and_close_use_only_source_valid_observations():
    anchor=O.preopen_anchor(dict(day='2026-10-02',rows=[
        dict(t=1.,p=273000.,valid=True,ep=1,seq=1),
        dict(t=2.,p=9999999.,valid=False,ep=1,seq=2),
        dict(t=3.,p=272500.,valid=True,ep=1,seq=3)]))
    assert anchor['close']==272500 and anchor['high']==273000 and anchor['observations']==2
    assert anchor['source_max_at']==3 and anchor['close_sequence']==3


def test_phase_boundaries_are_fixed_local_clock():
    assert O.phase_pass(f('2026-10-02T09:14:59+09:00'),15)
    assert not O.phase_pass(f('2026-10-02T09:15:00+09:00'),15)
    assert O.phase_pass(f('2026-10-02T09:29:59+09:00'),30)
    assert not O.phase_pass(f('2026-10-02T09:30:00+09:00'),30)


def test_missing_future_or_other_date_anchor_cannot_qualify():
    x=f();r=rule('below_preopen_close')
    a=dict(day='2026-10-02',close=273000.,high=273500.,source_max_at=x['t']-60)
    assert O.qualify(x,r,a)
    assert not O.qualify(x,r,None)
    assert not O.qualify(x,r,{**a,'source_max_at':x['t']})
    assert not O.qualify(x,r,{**a,'day':'2026-09-30'})
    assert O.qualify(x,rule(),None)


def test_registry_has_no_hidden_hypothesis_or_success_veto():
    rs=O.registry(.23)
    assert sum(len(r['horizons']) for r in rs)==3456
    assert len({r['id'] for r in rs})==len(rs)


def test_native_gates_keep_failed_frames_and_preserve_canonical_source():
    day='2026-10-02';a=f();b=f('2026-10-02T09:15:00+09:00')
    fs={day:[a,b]};before=deepcopy(fs)
    raw=dict(native=['real'],day=day,t=b['t']+.1,trace='actual',parent='ENTER_NOW',
        guard=dict(cohort='parent_enter',blockers=[]),recoverable=True,
        label=dict(binary=1,net=.1),cost=.32,features=dict(stream_epoch=1,stream_valid=True))
    result=O.native_bridge(dict(main=[raw]),fs,rule(),{day:None})
    assert result['candidate']['admitted']==0 and result['pattern_hits']==0
    assert fs==before and result['baseline']['admitted']==1
