import json

import pytest

from src.engine.scalping import samsung_session_pattern_research as S


def fixture(tmp_path, session='SOR_PREMARKET'):
    base = tmp_path/f'data/observations/scalp_micro_reversion_forward/trade_date=2026-10-02/venue=SOR/session={session}'
    base.mkdir(parents=True)
    common = dict(symbol='005930',item='005930_AL',venue='SOR',session_bucket=session,
        sequence_epoch=1,series_sequence=1,local_receive_timestamp='2026-10-02T08:01:00.100+09:00',
        exchange_timestamp='2026-10-02T08:01:00+09:00')
    trade = dict(**common,schema='scalp_micro_reversion_market_stream_point_v3',trade_price=270000.,
        trade_qty=10,aggressor_side='SELL',path_consumer_eligible=True,path_order_status='accept')
    depth = dict(**common,schema='scalp_micro_reversion_market_depth_point_v1',best_bid=270000.,best_ask=270500.,
        best_bid_qty=100,best_ask_qty=100,bid_levels=[[1,270000.,100],[2,269500.,100],[3,269000.,100]],
        ask_levels=[[1,270500.,100],[2,271000.,100],[3,271500.,100]])
    for stem,row in [('market_stream',trade),('market_depth_stream',depth)]:
        (base/(stem+'.jsonl')).write_text(json.dumps(row)+'\n')
        (base/(stem+'.manifest.json')).write_text(json.dumps(dict(schema='scalp_micro_reversion_market_path_manifest_v1',
            row_schema=row['schema'],shards=[dict(file=stem+'.jsonl')])))
    return base,trade,depth


def test_local_domain_partition_keeps_exact_clock_route_and_session(tmp_path):
    base,_,_ = fixture(tmp_path)
    records = {};cache,books,stats = S.partition(tmp_path,'2026-10-02','SOR_PREMARKET',records)
    assert len(records)==4 and cache['rows'][0]['flow_valid']
    assert books[(1,1)]==dict(bid_sum=300,ask_sum=300)
    assert stats['trade']['count']==1
    S.Q.verify_hashes(records)


def test_other_route_never_satisfies_al_session(tmp_path):
    base,trade,_ = fixture(tmp_path);trade['item']='005930_NX';trade['source_item']='005930_AL'
    (base/'market_stream.jsonl').write_text(json.dumps(trade)+'\n')
    cache,_,stats = S.partition(tmp_path,'2026-10-02','SOR_PREMARKET',{})
    assert cache['rows']==[] and stats['trade']['rejected']=={'schema_or_exact_route':1}


def test_clock_invalid_row_remains_invalid_no_price_imputation(tmp_path):
    base,trade,_ = fixture(tmp_path);trade['exchange_timestamp']='2026-10-02T08:00:00+09:00'
    (base/'market_stream.jsonl').write_text(json.dumps(trade)+'\n')
    cache,_,_ = S.partition(tmp_path,'2026-10-02','SOR_PREMARKET',{})
    assert not cache['rows'][0]['valid'] and not cache['rows'][0]['flow_valid']


def test_duplicate_sequence_fails_global_identity_preflight(tmp_path):
    base,trade,_ = fixture(tmp_path)
    (base/'market_stream.jsonl').write_text((json.dumps(trade)+'\n')*2)
    with pytest.raises(ValueError,match='duplicate'):
        S.partition(tmp_path,'2026-10-02','SOR_PREMARKET',{})


def test_shard_cannot_escape_its_partition(tmp_path):
    base,_,_ = fixture(tmp_path)
    path=base/'market_stream.manifest.json';body=json.loads(path.read_text());body['shards']=[dict(file='../secret')]
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError,match='outside'):
        S.partition(tmp_path,'2026-10-02','SOR_PREMARKET',{})


def test_all_means_exact_partition_not_an_hour_rewrite():
    assert S.C.region_pass(dict(hour=8),'all')
    assert not S.C.region_pass(dict(hour=8),'open')
    assert S.C.region_pass(dict(hour=18),'all')


def test_missing_nx_partition_has_no_outcome_or_zero_pnl(tmp_path):
    cache,books,stats = S.partition(tmp_path,'2026-09-29','NXT_REGULAR_OVERLAP',{})
    assert cache['rows']==cache['depth']==[] and books=={}
    assert stats['trade']['status']=='source_partition_missing'
    assert S.C.metric([])['mean_net_cf'] is None


def test_bad_manifest_is_not_valid_empty(tmp_path):
    base,_,_ = fixture(tmp_path)
    path=base/'market_stream.manifest.json';body=json.loads(path.read_text());body['row_schema']='unsupported'
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError,match='contract'):
        S.partition(tmp_path,'2026-10-02','SOR_PREMARKET',{})
