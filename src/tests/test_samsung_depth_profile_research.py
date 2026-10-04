from copy import deepcopy
import json

import pytest

from src.engine.scalping import samsung_depth_profile_research as D
from src.tests.test_samsung_pattern_campaign import cache


def raw():
    return dict(best_bid=270000.,best_ask=270500.,best_bid_qty=100,best_ask_qty=100,
        bid_levels=[[i+1,270000.-i*500,100] for i in range(5)],
        ask_levels=[[i+1,270500.+i*500,100] for i in range(5)],
        bid_depth=2000,ask_depth=1000,route_depth_totals={'combined':{'bid':2000,'ask':1000}})


def test_five_levels_and_full_depth_are_distinct_sources():
    p=D.profile(raw())
    assert p['five_bid']==500 and p['five_ask']==500
    assert p['total_bid']==2000 and p['total_ask']==1000


@pytest.mark.parametrize('change',[{'bid_depth':True},{'bid_depth':2000.5},
    {'bid_depth':400},{'route_depth_totals':None},{'route_depth_totals':{'combined':{'bid':1,'ask':2}}}])
def test_invalid_full_depth_does_not_invent_zero_or_remove_valid_five(change):
    r=raw();r.update(change);p=D.profile(r)
    assert p['total_bid'] is None and p['total_ask'] is None and p['five_bid']==500


def test_missing_five_is_not_filled_from_three():
    r=raw();r['bid_levels']=r['bid_levels'][:3];r['ask_levels']=r['ask_levels'][:3]
    p=D.profile(r)
    assert p['five_bid'] is None and p['bid_prices'] is None and p['total_bid']==2000


def test_bad_deep_level_invalidates_the_snapshot():
    r=raw();r['bid_levels'][4][1]=271000.
    assert D.profile(r) is None


def test_deep_history_is_past_only_and_price_changes_remove_queue_delta():
    c=cache(1200);fs=D.C.feature_rows(c)
    books={(q['ep'],q['seq']):D.profile(raw()) for q in c['depth']}
    full=D.augment(c,fs,books)
    assert full and full[-1]['profile']['five_ratio']==1 and full[-1]['profile']['total_ratio']==2
    assert full[-1]['profile']['deep_bid_replenishment']==1
    stop=full[len(full)//2];prefix=deepcopy(c)
    prefix['rows']=prefix['rows'][:stop['index']+1]
    prefix['depth']=[q for q in prefix['depth'] if q['t']<stop['t']]
    assert D.augment(prefix,[f for f in fs if f['t']<=stop['t']],books)==[f for f in full if f['t']<=stop['t']]
    q=c['depth'][stop['quote_index']-10];books[(q['ep'],q['seq'])]['bid_prices']=(1,2,3,4,5)
    changed=D.augment(c,fs,books)
    x=next(f for f in changed if f['t']==stop['t'])
    assert x['profile']['deep_bid_replenishment'] is None
    assert x['profile']['deep_ask_depletion']==1


def test_profile_registry_counts_and_ids():
    regular=D.registry(.23,True);other=D.registry(.23,False)
    assert sum(len(r['horizons']) for r in regular)==1080
    assert sum(len(r['horizons']) for r in other)==216
    assert len({r['id'] for r in regular})==len(regular)


def source_fixture(tmp_path):
    r=raw();stamp='2026-10-02T09:03:00+09:00'
    r.update(schema='scalp_micro_reversion_market_depth_point_v1',symbol='005930',
        item='005930_AL',source_item='005930_AL',venue='SOR',session_bucket='SOR_REGULAR',
        sequence_epoch=1,series_sequence=1,local_receive_timestamp=stamp)
    p=tmp_path/'trade_date=2026-10-02/venue=SOR/session=SOR_REGULAR/market_depth_stream.jsonl'
    p.parent.mkdir(parents=True);p.write_text(json.dumps(r)+'\n')
    c=dict(depth=[dict(ep=1,seq=1,t=D.R.epoch(stamp),valid=True,bid=270000.,ask=270500.,bq=100,aq=100)])
    return r,p,c


def test_profile_source_exact_cache_binding(tmp_path):
    _,p,c=source_fixture(tmp_path)
    assert D.profiles(c,{str(p):D.R.P.file_sha(p)},'2026-10-02','SOR_REGULAR')[(1,1)]['five_bid']==500
    c['depth'][0]['bq']=101
    with pytest.raises(ValueError,match='cache_binding_conflict'):
        D.profiles(c,{str(p):D.R.P.file_sha(p)},'2026-10-02','SOR_REGULAR')


def test_duplicate_profile_source_fails(tmp_path):
    r,p,c=source_fixture(tmp_path);p.write_text((json.dumps(r)+'\n')*2)
    with pytest.raises(ValueError,match='duplicate_sequence'):
        D.profiles(c,{str(p):D.R.P.file_sha(p)},'2026-10-02','SOR_REGULAR')


def test_missing_profile_source_is_not_an_empty_negative_result(tmp_path):
    _,p,c=source_fixture(tmp_path);p.write_text('')
    with pytest.raises(ValueError,match='source_incomplete'):
        D.profiles(c,{str(p):D.R.P.file_sha(p)},'2026-10-02','SOR_REGULAR')


def test_native_mask_keeps_failed_frame_and_does_not_mutate_canonical(monkeypatch):
    c=cache(1200);fs=D.C.feature_rows(c)
    books={(q['ep'],q['seq']):D.profile(raw()) for q in c['depth']}
    full=D.augment(c,fs,books);snapshot=deepcopy(full)
    rule=D.registry(.23,True)[0]
    def capture(projection,frames,rule):
        assert len(frames['day'])==len(full)
        assert frames['day'][0]['windows']=={}
        assert frames['day'][0]['depth_ratio']==1
        return 'captured'
    monkeypatch.setattr(D.C,'native_bridge',capture)
    assert D.native_bridge({}, {'day':full},rule)=='captured'
    assert full==snapshot
