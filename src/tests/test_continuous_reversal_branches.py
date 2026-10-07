import copy
import pytest
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping import reversal_auxiliary_phases as A


def rows():
    start = 1791331200.
    return [[start+t, 1, i+1, p, p-.01, p+.01, 10, 1, 1, "005930_AL", 0]
            for i,(t,p) in enumerate([(0,100.),(10,103.),(30,103.1),(31,103.2),
                                     (60,103.8),(60.2,103.6),(60.5,103.7),
                                     (61,103.6),(62,103.3),(63,103.4),(64,103.5)])]


def state(values):
    s=B.BranchState(session_anchor=values[0])
    for r in values:
        s.observe(r,symbol="005930",venue="SOR",session="SOR_REGULAR")
    return s


def test_confirmation_uses_frozen_anchor_and_actual_quote():
    r=rows();s=state(r)
    assert s.counts["confirmed"]==1
    e,source=s.snapshot(s.ready[0])
    assert e["epoch"]==r[-1][0] and e["anchor_epoch"]==r[-2][0]
    assert e["entry_ask"]==r[-1][5] and e["anchor_price"]==r[-2][3]
    for arm in V1.ARMS:
        inp,prompt,schema=A.production_request(source,arm,phase=B.CONFIRMED,event=e)
        assert inp["observation_phase"]["post_trigger_observations"]=="OBSERVED_THROUGH_CONFIRMATION"
        assert "additional_higher_trade" in schema["properties"]["supporting_fact_ids"]["items"]["enum"]
        assert prompt.isascii()
        assert "outcome" not in str(inp) and B.BRANCH not in str(inp)


@pytest.mark.parametrize("mutation,reason",[("retest","original_low_retested"),
                                          ("timeout","confirmation_timeout"),
                                          ("gap","confirmation_path_censored")])
def test_pending_invalidated_before_confirmation(mutation,reason):
    r=rows()
    if mutation=="retest":r[-1][3]=103.3
    if mutation=="timeout":r[-1][0]+=5
    if mutation=="gap":r[-1][2]+=1
    s=state(r)
    assert not s.ready and s.counts[reason]>=1


def test_confirmation_missing_quote_is_not_repaired_by_later_tick():
    r=rows();r[-1][5]=None;s=state(r)
    assert s.ready[0]["event"]["entry_ask"] is None
    new=r[-1][:];new[0]+=1;new[2]+=1;new[5]=104.
    s.observe(new,symbol="005930",venue="SOR",session="SOR_REGULAR")
    assert s.ready[0]["event"]["entry_ask"] is None


def test_missing_session_anchor_does_not_substitute_restart_price():
    s=B.BranchState()
    for r in rows():s.observe(r,symbol="005930",venue="SOR",session="SOR_REGULAR")
    assert not s.ready and s.counts["required_feature_missing"]


def test_payload_definition_scope_and_phase_are_strict():
    p=B.payload([B.legacy_branch("DD5_GE_1_2"),B.pattern_branch()])
    B.validate_payload(p,"samsung|REGULAR|ALL")
    for key in ("samsung|PRE|ALL","other|REGULAR|GE_100000"):
        with pytest.raises(ValueError):B.validate_payload(p,key)
    p["branches"][1]["definition_sha256"]="0"*64
    with pytest.raises(ValueError):B.validate_payload(p,"samsung|REGULAR|ALL")


def test_first_production_bytes_are_identical():
    s=state(rows());e,source=s.snapshot(s.ready[0])
    for arm in V1.ARMS:
        assert A.production_request(source,arm,phase=B.FIRST)==V1.production_request(source,arm)


def test_same_claim_snapshot_survives_later_tick_and_rejects_generation():
    r=rows();s=state(r);B._STATES.clear();B._CLAIMS.clear();B._GENERATION="g"
    key=("005930","SOR","005930_AL","REGULAR","2026-10-07")
    B._STATES[key]=s
    claim=B.claim_snapshot("005930","SOR","SOR_REGULAR",now=r[-1][0],item="005930_AL",family_sha256="g")
    assert claim
    new=r[-1][:];new[0]+=.1;new[2]+=1;new[3]-=.05
    s.observe(new,symbol="005930",venue="SOR",session="SOR_REGULAR")
    assert B.validate_claim(claim,"g",now=new[0])[0]["confirmation_price"]==103.5
    with pytest.raises(ValueError):B.validate_claim(claim,"other",now=new[0])
    with pytest.raises(ValueError):B.validate_claim(claim,"g",now=new[0]+6)
    altered=copy.deepcopy(claim);altered["snapshot"][0]["entry_ask"]=1
    with pytest.raises(ValueError):B.validate_claim(altered,"g",now=new[0])


@pytest.fixture(autouse=True)
def restore_global_state():
 old=(B._GENERATION,B._V2,dict(B._STATES),dict(B._CLAIMS),dict(B._ANCHORS),set(B._RESTORED_DAYS),set(B._EMPTY_PREFIX_DAYS))
 yield
 B._GENERATION,B._V2=old[:2]
 for dest,src in zip((B._STATES,B._CLAIMS,B._ANCHORS),old[2:5]):dest.clear();dest.update(src)
 B._RESTORED_DAYS.clear();B._RESTORED_DAYS.update(old[5]);B._EMPTY_PREFIX_DAYS.clear();B._EMPTY_PREFIX_DAYS.update(old[6])


def test_legacy_adapter_full_snapshot_parity_after_rolling_and_invalid_rows():
 import random
 from src.engine.scalping import continuous_reversal as K
 random.seed(7);a=K.ReversalState();b=B.PriceTurnState();p=100.
 for i in range(900):
  p+=random.choice((-.2,0,.1))
  r=[1791331200.+i,1,i+1,p,p-.01,p+.01,10,1,int(i not in (144,301,505)),"005930_AL",0]
  for s in (a,b):s.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
  assert a.turn==b.turn
  if a.turn and a.turn['epoch']==r[0]:assert a.snapshot()==b.snapshot()


def test_ready_feature_build_is_outside_ingestion_lock(monkeypatch):
 from src.engine.scalping import continuous_reversal as K
 r=rows();s=state(r);B._STATES.clear();B._CLAIMS.clear();B._GENERATION='g'
 B._STATES[('005930','SOR','005930_AL','REGULAR','2026-10-07')]=s
 original=K.build_features
 def guarded(*args,**kwargs):
  assert not B._LOCK._is_owned()
  return original(*args,**kwargs)
 monkeypatch.setattr(K,'build_features',guarded)
 assert B.claim_snapshot('005930','SOR','SOR_REGULAR',now=r[-1][0],item='005930_AL',family_sha256='g')


def test_empty_prefix_allows_true_first_observation_but_existing_gap_does_not(tmp_path):
 import json
 B._STATES.clear();B._ANCHORS.clear();B._RESTORED_DAYS.clear();B._EMPTY_PREFIX_DAYS.clear()
 B.configure('g',v2=True);B.restore_session_anchors(tmp_path,'2026-10-07')
 r=rows()[0]
 env=dict(observed_epoch=r[0],provider_trade_epoch=r[0],trade_price=r[3],transport_epoch=r[1],route_sequence=r[2],item=r[9],
          market_route='krx_nxt_integrated',inline_best_bid=r[4],inline_best_ask=r[5],trade_qty=r[6])
 B.observe_normalized('005930','SOR_REGULAR',env)
 assert next(iter(B._STATES.values())).session_anchor[3]==r[3]
 B._STATES.clear();B._ANCHORS.clear();B._RESTORED_DAYS.clear();B._EMPTY_PREFIX_DAYS.clear()
 path=tmp_path/'observations/scalp_micro_reversion_forward/trade_date=2026-10-07/venue=SOR/session=SOR_REGULAR/market_stream.jsonl'
 path.parent.mkdir(parents=True);path.write_text(json.dumps(dict(symbol='005930',source_item=None))+'\n')
 B.restore_session_anchors(tmp_path,'2026-10-07');B.observe_normalized('005930','SOR_REGULAR',env)
 assert next(iter(B._STATES.values())).session_anchor is None
