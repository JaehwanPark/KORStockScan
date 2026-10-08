"""Shared retirement and Main fixed-watch producer/consumer contracts."""
from datetime import date, datetime
from types import SimpleNamespace
from dataclasses import replace
import json
import pytest

from src.engine.scalping import main_fixed_watch as fixed
from src.trading.config import owner_retirement as retired
from src.tests.test_main_fixed_watch import _TestDB, epoch

NEW = ("403870", "196170", "036930")
GROUP = tuple(sorted(set(retired.RETIRED_EPISODE_PROFILES) - {"034020"}))




def test_five_symbols_reserve_existing_cap_and_one_custody_wait_does_not_block_others(monkeypatch):
    for spec in fixed.SPECS:
        monkeypatch.setenv(spec.enable_env, "true")
    blocked = {"196170"}
    monkeypatch.setattr(fixed, "broker_and_owner_clear", lambda now, route:
                        (False, "owner_registry_unresolved_intent") if route["symbol"] in blocked else (True, "flat"))
    db, targets = _TestDB(), []
    for spec in fixed.SPECS:
        result, target = fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=5, symbol=spec.symbol)
        assert result == ("owner_registry_unresolved_intent" if spec.symbol in blocked else "armed")
    assert fixed.reserved_slots() == 5
    assert len(targets) == len({t["watch_admission_id"] for t in targets}) == 4
    before = json.loads(json.dumps(targets))
    blocked.clear()
    assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=5, symbol="196170")[0] == "armed"
    assert targets[:4] == before and len(targets) == 5
    for spec in fixed.SPECS:
        assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=5, symbol=spec.symbol)[0] == "already_watching"
    assert len(targets) == 5


@pytest.mark.parametrize("symbol", NEW)
@pytest.mark.parametrize("damage", [None, "date", "false", "missing", "conflict", "provenance", "future"])
def test_new_nxt_admission_requires_native_exact_date_listing(symbol, damage):
    db = _TestDB()
    source = dict(stock_code=symbol, trade_date="2026-09-30", krx_regular_eligible=True,
                  nxt_eligible=True, krx_aftermarket_eligible=False, eligible_venues_json=["NXT"],
                  source_api_id="ka10099", source_revision="official", observed_at_kst="2026-09-30T07:00:00+09:00",
                  payload_sha256="a" * 64, quality_state="VALID")
    if damage == "date": source["trade_date"] = "2026-09-29"
    if damage == "false": source.update(nxt_eligible=False, eligible_venues_json=[])
    if damage == "conflict": source["quality_state"] = "CONFLICT"
    if damage == "provenance": source["payload_sha256"] = ""
    if damage == "future": source["observed_at_kst"] = "2026-09-30T09:00:00+09:00"
    if damage == "missing": source = None
    db.get_security_market_eligibility = lambda *_: source
    ok, _ = fixed._new_symbol_session_eligible(db, fixed.spec_for(symbol), fixed.session_route(epoch(8), symbol), epoch(8))
    assert ok is (damage is None)
    assert fixed._new_symbol_session_eligible(db, fixed.spec_for(symbol), fixed.session_route(epoch(10), symbol), epoch(10))[0]


@pytest.mark.parametrize('symbol',[spec.symbol for spec in fixed.SPECS])
def test_integrated_after_sor_watch_keeps_quote_and_custody_guards(monkeypatch,symbol):
    from src.engine import sniper_state_handlers as handlers
    db,targets=_TestDB(),[]
    monkeypatch.setenv(fixed.spec_for(symbol).enable_env,'true')
    db.get_security_market_eligibility=lambda *_:pytest.fail('SOR observation used NXT-only listing gate')
    now=epoch(16)
    monkeypatch.setattr(fixed,'broker_and_owner_clear',lambda *_:(False,'owner_registry_unresolved_intent'))
    assert fixed.reconcile(db,targets,now_epoch=now,watch_cap=5,symbol=symbol)[0]=='owner_registry_unresolved_intent'
    assert targets==[]
    monkeypatch.setattr(fixed,'broker_and_owner_clear',lambda *_:(True,'verified_flat'))
    status,target=fixed.reconcile(db,targets,now_epoch=now,watch_cap=5,symbol=symbol)
    assert status=='armed' and target['broker_route']=='SOR'
    route=handlers._fixed_watch_entry_source_route(target,now)
    assert route['item']==symbol+'_AL'
    assert route['market_session_bucket']=='KRX_NXT_AFTERMARKET'
    wrong_item=symbol+'_NX'
    snapshot=dict(curr=100,last_ws_item=wrong_item,
        last_realtime_type_item={'0B':wrong_item,'0D':wrong_item},
        last_realtime_type_ts={'0B':now+11,'0D':now+11})
    assert fixed.observation_ready(target,snapshot,now_epoch=now+11)==(False,'exact_route_item_missing')









@pytest.mark.parametrize('symbol',[spec.symbol for spec in fixed.SPECS])
def test_five_symbol_machine_recipe_dispatch_uses_original_symbol_and_preserves_block(symbol):
    from src.tests.test_entry_strategy_policy import raw,setup,policy
    from src.engine.scalping import entry_admission_recipe as recipe,entry_setup_evidence as engine
    from copy import deepcopy
    parent=recipe.candidate_policy(policy())
    payload=raw();payload['stock_code']=symbol
    payload['current']['fluctuation_pct']=1
    payload['features'].update(curr_vs_micro_vwap_bp=-5,curr_vs_ma5_bp=0,micro_vwap_available=True)
    original=setup(payload);before=deepcopy(original)
    decision=engine.mechanistic_entry_policy_decision(original,policy=parent)
    receipt=decision['admission_recipe']
    assert receipt['original_raw_sha256']==original['strategy_raw_sha256'] and original==before
    assert ('outside_scope_parent_inherited' in receipt['unresolved_reasons']) is (symbol=='005930')
    assert decision['strategy_selection']['policy_sha256']==recipe.S.digest(parent)
    damaged=deepcopy(payload);damaged['features']['quote_stale']=True
    blocked=engine.mechanistic_entry_policy_decision(setup(damaged),policy=parent)
    assert blocked['action']!='ENTER_NOW'
