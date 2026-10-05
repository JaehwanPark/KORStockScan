from copy import deepcopy
from datetime import datetime

import pytest
from src.engine.scalping import samsung_absorption_differential_research as D
from src.engine.scalping import entry_flat_buy_flow_research as F
from src.engine.scalping import entry_strategy_policy as S


def raw_receipt():
    raw=dict(stock_code='005930',effective_venue='KRX',session_bucket='KRX_REGULAR',
        entry_machine_input_as_of=100.,entry_candle_context=dict(request_code='005930_AL',ws_route='krx_nxt_integrated'),
        features=dict(buy_pressure_10t=100.,net_aggressive_delta_10t=10,price_change_10t_pct=0.))
    window=[dict(t=99+i*.1,p=100.,q=1,side='BUY',ep=1,seq=i,valid=True,flow_valid=True,continuous=True) for i in range(10)]
    receipt=F.historical_receipt(raw,window,archive_sha256='a'*64,window_cutoff=100.)
    assert receipt['usable']
    return raw,receipt


def test_h1_trusted_quantity_dispersion_and_future_rejected():
    raw,receipt=raw_receipt()
    assert D.h1(raw,receipt)[0] is True
    bad=deepcopy(receipt);bad['archive_window'][-1]['t']=101
    assert D.h1(raw,bad)[0] is None
    window=deepcopy(receipt['archive_window']);window[-1]['q']=100
    raw['features']['net_aggressive_delta_10t']=109
    concentrated=F.historical_receipt(raw,window,archive_sha256='a'*64,window_cutoff=100.)
    assert D.h1(raw,concentrated)[0] is False


def test_h2_same_epoch_ttl_and_strict_prior():
    raw,receipt=raw_receipt()
    old=deepcopy(raw);old['entry_machine_input_as_of']=99.5
    window=deepcopy(receipt['archive_window'])
    for r in window:r['t']-=1
    for r in window[:6]:r['side']='SELL'
    old['features'].update(buy_pressure_10t=40.,net_aggressive_delta_10t=-2)
    prior=F.historical_receipt(old,window,archive_sha256='a'*64,window_cutoff=99.5)
    assert D.h2(raw,receipt,(old,prior))[0] is True
    assert D.h2(raw,receipt,(raw,receipt))[0] is None
    raw['entry_machine_input_as_of']=106
    assert D.h2(raw,receipt,(old,prior))[0] is None


def test_h3_requires_exact_quote_clock_route_epoch_sequence():
    raw,receipt=raw_receipt();raw['quote']=dict(best_bid=100,best_ask=101)
    raw['mechanistic_micro_window']=dict(market_data_health=dict(quote_max_age_ms=1500),feature=dict(window_started_at_ms=99000))
    # The historical receipt must bind the actual raw body including quote.
    receipt=F.historical_receipt(raw,receipt['archive_window'],archive_sha256='a'*64,window_cutoff=100.)
    depth=[dict(t=99.5,ep=1,seq=1,bid=99,ask=101,valid=True,continuous=True),
           dict(t=99.8,ep=1,seq=2,bid=100,ask=101,valid=True,continuous=True)]
    assert D.h3(raw,receipt,depth,[99.5,99.8])[0] is True
    for change in [dict(ep=2),dict(seq=4),dict(bid=101),dict(t=100.1)]:
        bad=deepcopy(depth);bad[-1].update(change)
        assert D.h3(raw,receipt,bad,[r['t'] for r in bad])[0] is None


def candle_raw():
    cutoff=datetime.fromisoformat('2026-10-02T09:10:30+09:00').timestamp()
    body=dict(observed_at='2026-10-02T09:10:10+09:00',bars=[dict(dt=f'2026-10-02T09:{m:02d}:00+09:00',
        h=101.,l=100.,forming=False,partial_volume=False) for m in range(5,10)])
    return dict(entry_machine_input_as_of=cutoff,entry_candle_context=dict(strategy_completed_bars=dict(body=body,sha256=S.digest(body))))


def test_h4_completion_and_actual_availability():
    raw=candle_raw();assert D.h4(raw,.23)[0] is True
    for mutation in ('late','forming','gap','bad_hash'):
        bad=deepcopy(raw);receipt=bad['entry_candle_context']['strategy_completed_bars'];body=receipt['body']
        if mutation=='late':body['observed_at']='2026-10-02T09:10:31+09:00'
        if mutation=='forming':body['bars'][-1]['forming']=True
        if mutation=='gap':body['bars'].pop(2)
        if mutation!='bad_hash':receipt['sha256']=S.digest(body)
        else:receipt['sha256']='f'*64
        assert D.h4(bad,.23)[0] is None


@pytest.mark.parametrize('action',['BLOCK','RECHECK','ENTER_NOW'])
def test_unknown_inherits_and_only_known_fail_filters(action):
    assert D.filtered_action(action,None)==action
    assert D.filtered_action(action,True)==action
    assert D.filtered_action(action,False)==('RECHECK' if action=='ENTER_NOW' else action)


def test_outcomes_do_not_relabel_stop_or_unknown_as_loss():
    assert D.outcome(dict(path=dict(status='stop',net_pct=-.5,post_stop_rebound_pct=2)))=='stop'
    assert D.outcome(dict(path=dict(status='timeout',net_pct=.02)))=='complete_timeout_positive'
    assert D.outcome(dict(path=dict(status='timeout',net_pct=None)))=='source_or_price_gap:timeout'
    assert D.outcome(dict(path=dict(status='session_censored',net_pct=None)))=='source_or_price_gap:session_censored'


def test_new_frozen_waits_without_relabeling_old_dates(tmp_path):
    from src.engine.scalping import samsung_absorption_acceptance_research as A
    from src.tests.test_entry_strategy_policy import policy
    evidence=tmp_path/'evidence.json';evidence.write_text('{}')
    base=A.freeze(policy(),[evidence])
    frozen=D.freeze_candidate(dict(recommended_candidate='H2'),[evidence],base)
    result=D.prepare_forward(tmp_path,'2026-10-06',frozen,base)
    assert result['status']=='waiting_new_source_date' and result['policy_selected'] is False
    with pytest.raises(ValueError):D.prepare_forward(tmp_path,'2026-10-02',frozen,base)
