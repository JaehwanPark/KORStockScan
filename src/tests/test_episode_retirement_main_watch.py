"""Shared retirement and Main fixed-watch producer/consumer contracts."""
from datetime import date, datetime
from types import SimpleNamespace
from dataclasses import replace
import json
import pytest

from src.engine.scalping import main_fixed_watch as fixed
from src.trading.config import owner_retirement as retired
from src.engine.automation import owner_retirement_transition as transition
from src.tests.test_main_fixed_watch import _TestDB, epoch

NEW = ("403870", "196170", "036930")
GROUP = tuple(sorted(set(retired.RETIRED_EPISODE_PROFILES) - {"034020"}))


@pytest.mark.parametrize("symbol", GROUP + NEW)
def test_retirement_blocks_static_dynamic_and_gateway_buy_but_preserves_main(symbol):
    from src.trading.low_price_two_leg.profiles import PROFILES
    from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway
    for code in (symbol, "A" + symbol, symbol + "_AL", symbol + "_NX"):
        assert retired.new_entry_retired(code, "episode")
        assert not retired.new_entry_retired(code, "main_scalping")
    with pytest.raises(ValueError, match="symbol_owner_permanently_retired"):
        replace(next(iter(PROFILES.values())), symbol=symbol, profile_id="renamed_time_window")
    gateway = KiwoomLowPriceTwoLegGateway.__new__(KiwoomLowPriceTwoLegGateway)
    gateway.symbol = symbol
    gateway._require_write_authority = lambda: pytest.fail("retired BUY reached order transport")
    assert gateway.submit_limit_buy(price=10000, quantity=10).return_code == "SYMBOL_OWNER_RETIRED"
    assert retired.main_manual_after_episode_retirement(symbol, ["main_scalping", "manual_operator"])


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
    if damage == "future": source["observed_at_kst"] = "2026-09-30T17:00:00+09:00"
    if damage == "missing": source = None
    db.get_security_market_eligibility = lambda *_: source
    ok, _ = fixed._new_symbol_session_eligible(db, fixed.spec_for(symbol), fixed.session_route(epoch(16), symbol), epoch(16))
    assert ok is (damage is None)
    assert fixed._new_symbol_session_eligible(db, fixed.spec_for(symbol), fixed.session_route(epoch(10), symbol), epoch(10))[0]


def test_group_manifest_has_exact_27_profiles_54_timers_and_54_instances(tmp_path):
    root = tmp_path / "work"
    guard = root / "src/trading/config/owner_retirement.py"
    guard.parent.mkdir(parents=True)
    guard.write_text("reviewed guard")
    result = transition.prepare(root, systemd_dir=tmp_path / "units", symbols=GROUP)
    assert transition.retirement_symbols(result) == GROUP
    assert len(result["profile_ids"]) == 27
    assert sum(unit.endswith(".timer") for unit in result["units"]) == 54
    assert sum(unit.endswith(".service") for unit in result["units"]) == 54
    assert result["receipt_sha256"] == transition.digest({k:v for k,v in result.items() if k != "receipt_sha256"})
    assert len(transition.units()) == 12  # immutable prior Doosan transition
    with pytest.raises(ValueError, match="scope"):
        transition.prepare(root, symbols=["005930"])


@pytest.mark.parametrize("symbol", GROUP)
@pytest.mark.parametrize("gap", ["broker", "order", "registry", "intent"])
def test_every_retired_symbol_requires_its_own_flat_proof(symbol, gap):
    snapshot = dict(verified_exchanges=["KRX", "NXT"], inventory={s:0 for s in GROUP}, open_orders=[], migration_receipts=[])
    if gap == "broker": snapshot["inventory"][symbol] = 1
    if gap == "order": snapshot["open_orders"] = [dict(symbol=symbol,order_no="0000001",side="BUY",route="KRX",quantity=1,filled_quantity=0,remaining_quantity=1)]
    snapshot["snapshot_sha256"] = transition.digest(snapshot)
    registry = SimpleNamespace(
        reconcile_symbol_quantity=lambda **kw: dict(registered_owner_quantity=int(gap == "registry" and kw["symbol"] == symbol), external_manual_remainder=0),
        unresolved_intent_summary=lambda **kw: dict(unresolved_intent_count=int(gap == "intent" and kw["symbol"] == symbol)))
    with pytest.raises(ValueError):
        transition.require_flat(snapshot, registry, observed_at=datetime.fromisoformat("2026-10-06T17:30:00+09:00"), symbol=symbol, symbols=GROUP)


def test_historical_bundle_preserves_original_hash_and_only_31_runtime_profiles():
    from src.trading.low_price_two_leg import policy_runtime as policies
    from src.trading.low_price_two_leg.profiles import PROFILES
    binding = policies.runtime_policy_binding(target_date=date(2026,10,6))
    assert binding["status"] == "ready"
    assert set(binding["policies"]) == set(PROFILES) and len(PROFILES) == 31
    assert policies.runtime_profile_exclusions(date(2026,10,6)) == []
    for profile_id in retired.RETIRED_EPISODE_PROFILE_IDS:
        assert policies.load_applied_profile_policy(profile_id,target_date=date(2026,10,6))[2] == "symbol_owner_permanently_retired"


@pytest.mark.parametrize("symbol", NEW)
def test_three_research_populations_and_frozen_candidate_budget_are_separate(tmp_path, symbol):
    from src.engine.monitoring import main_fixed_watch_policy_research as research
    from src.tests.test_entry_strategy_policy import policy
    source = tmp_path / "retained.json"
    source.write_text(json.dumps(dict(rows=[dict(stock_code="005930"),dict(stock_code="034020")]+[dict(stock_code=s) for s in NEW])))
    frozen = research.freeze(policy(), [source], source_date="2026-10-06", publication_date="2026-10-06", target_date="2026-10-07", symbol=symbol)
    result = research.evaluate(frozen)
    assert result["symbol"] == symbol and result["census"]["symbol_rows"] == 1
    assert len(result["candidates"]) == 10
    assert result["initial_policy_preproof_required"] is False
    assert result["selection_status"] == "source_gap"
    assert result["actual_completed_net_profit_krw"] is None

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
