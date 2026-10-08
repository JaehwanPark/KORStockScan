"""Regression boundaries for permanent automatic-owner removal."""
from datetime import date
import fcntl
import hashlib
import json
from pathlib import Path

import pytest

from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry, OwnerOrderContext, OwnerRegistryError, OwnerRegistryConflict,
)
from src.trading.config import native_owner_policy as policy


@pytest.fixture
def registry(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(tmp_path / "registry.jsonl"))
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "retirement-test-account")
    monkeypatch.setenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(tmp_path / "excluded.txt"))
    monkeypatch.delenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES", raising=False)
    from src.trading.order import owner_custody_registry as owner
    monkeypatch.setattr(owner, "_DEFAULT_REGISTRY", None, raising=False)
    instance = OrderOwnerRegistry()
    monkeypatch.setattr(owner, "default_order_owner_registry", lambda: instance)
    return instance


def historical(registry, owner="episode", quantity=10, symbol="042660", state="ORDER_BOUND", filled=None):
    context = OwnerOrderContext(owner, owner + ":fixture", owner + ":fixture", owner + ":intent")
    lock = registry._locked()
    try:
        registry._append_locked(registry._read_locked(), {
            "intent_id": owner + ":historical", "event": state, "state": state,
            "account_key": "retirement-test-account", "order_date": "2026-10-08",
            "symbol": symbol, "side": "BUY", "action": "NEW", "quantity": quantity,
            "filled_qty": quantity if filled is None else filled,
            "broker_order_no": "0000001", "route": "SOR",
            "owner_type": owner, "owner_id": context.owner_id,
            "position_id": context.position_id, "client_intent_id": context.client_intent_id,
        })
    finally:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    return context


@pytest.mark.parametrize("owner", ["episode", "widget_auto_trade"])
@pytest.mark.parametrize("side,action", [("BUY", "NEW"), ("SELL", "NEW"), ("BUY", "CANCEL"), ("SELL", "CANCEL"), ("SELL", "AMEND")])
def test_all_retired_automatic_actions_rejected_before_reservation(registry, owner, side, action):
    context = OwnerOrderContext(owner, owner + ":fixture", owner + ":position", "request")
    with pytest.raises(OwnerRegistryError, match="permanently_retired"):
        registry.reserve(context=context, symbol="042660", side=side, action=action,
                         quantity=10, route="SOR", order_date=date(2026, 10, 8))
    assert not registry.path.exists()
    from src.engine import kiwoom_orders
    assert kiwoom_orders._reserve_owner_registry_intent(code="042660", side=side,
        action=action, qty=10, route="SOR", owner_context=context)[2]["broker_order_attempted"] is False


def test_manual_disposition_preserves_ledger_and_is_idempotent_without_flat(registry):
    historical(registry)
    before = registry.path.read_bytes()
    receipt = registry.retire_automatic_owners_to_manual()
    assert receipt["broker_flat_verified"] is False
    assert registry.path.read_bytes().startswith(before)
    after = registry.path.read_bytes()
    assert registry.retire_automatic_owners_to_manual() == receipt
    assert registry.path.read_bytes() == after
    assert registry.verified_events_snapshot()[0] if isinstance(registry.verified_events_snapshot(),tuple) else registry.verified_events_snapshot()


def test_manual_sale_does_not_turn_historical_episode_qty_into_main_deficit(registry):
    historical(registry)
    with pytest.raises(OwnerRegistryConflict, match="broker_quantity_deficit"):
        registry.reconcile_symbol_quantity(symbol="042660", broker_quantity=0)
    registry.retire_automatic_owners_to_manual()
    result = registry.reconcile_symbol_quantity(symbol="042660", broker_quantity=0)
    assert result["registered_owner_quantity"] == 0
    assert result["position_quantities"] == {}
    assert registry.owner_position_qty("episode:fixture", symbol="042660") == 10


def test_main_quantity_deficit_is_still_blocked(registry):
    historical(registry, owner="main_scalping", quantity=3)
    historical(registry, quantity=10)
    registry.retire_automatic_owners_to_manual()
    with pytest.raises(OwnerRegistryConflict, match="broker_quantity_deficit"):
        registry.reconcile_symbol_quantity(symbol="042660", broker_quantity=2)
    assert registry.reconcile_symbol_quantity(symbol="042660", broker_quantity=8)["external_manual_remainder"] == 5


def test_registered_native_contract_needs_disposition_and_ignores_deleted_daily_policy(registry, monkeypatch):
    historical(registry)
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", "/nonexistent/deleted_episode.json")
    with pytest.raises(policy.SymbolOwnerPolicyError, match="disposition_missing"):
        policy.resolve_symbol_owner_policy("042660")
    registry.retire_automatic_owners_to_manual()
    decision = policy.resolve_symbol_owner_policy("A042660_AL")
    assert decision.symbol == "042660" and decision.owner_allowed("main_scalping")
    assert not decision.owner_allowed("episode", new_entry=False)
    assert registry.decision_activation_matches(decision)


def test_late_episode_fill_records_original_owner_without_automatic_execution(registry):
    context = historical(registry, quantity=10, filled=1)
    registry.retire_automatic_owners_to_manual()
    registry.record_fill(context=context, symbol="042660", side="BUY", order_quantity=10,
        order_date="2026-10-08", broker_order_no="0000001", cumulative_filled_qty=2)
    row = registry.order_owner(order_date="2026-10-08", broker_order_no="0000001")
    assert row["owner_type"] == "episode" and row["filled_qty"] == 2
    assert row["state"] == "ORDER_BOUND"
    assert registry.reconcile_symbol_quantity(symbol="042660", broker_quantity=0)["registered_owner_quantity"] == 0


def test_old_episode_ambiguous_intent_cannot_block_a_native_main_intent(registry):
    historical(registry, state="INTENT_AMBIGUOUS", filled=0)
    registry.retire_automatic_owners_to_manual()
    context = OwnerOrderContext("main_scalping", "main_scalping:new", "main_scalping:new", "new-buy")
    assert registry.reserve(context=context, symbol="042660", side="BUY", quantity=1,
                            route="SOR", order_date="2026-10-08")
    with pytest.raises(OwnerRegistryError, match="submit_unresolved"):
        registry.reserve(context=OwnerOrderContext("main_scalping", "main_scalping:other", "main_scalping:other", "other-buy"),
                         symbol="042660", side="BUY", quantity=1, route="SOR", order_date="2026-10-08")


def test_manual_veto_survives_native_management_disposition(registry, monkeypatch):
    historical(registry)
    registry.retire_automatic_owners_to_manual()
    from src.engine.risk import manual_control_exclusion as veto
    p = registry.path.parent / "excluded.txt"
    p.write_text("042660 # manual_operator explicit\n")
    assert veto.evaluate_main_bot_control_exclusion("042660").excluded
    p.write_text("042660 # machine_owner_scope hanwha_widget_and_episode_independent_owners\n")
    assert not veto.evaluate_main_bot_control_exclusion("042660").excluded


def test_current_stage_and_notifier_have_no_retired_producer_requirements():
    from src.engine.automation import postclose_summary_handoff as native
    from src.engine.monitoring.error_detector_coverage import validate_semantic_coverage
    from src.engine.runtime_approval_summary import PRIMARY_DIRECT_OWNERS
    assert not {"episode_policy", "research_capacity", "research_allocation", "machine_attribution", "machine_timing", "legacy_policy_approval", "market_weakness"} & native.STAGE_REGISTRY.keys()
    assert not {"low_price_two_leg", "low_price_expansion", "machine_entry"} & set(PRIMARY_DIRECT_OWNERS)
    assert validate_semantic_coverage("2026-10-08")["status"] == "pass"


def test_native_authority_lookup_never_creates_lock_or_directory(registry, monkeypatch):
    registry.retire_automatic_owners_to_manual()
    historical(registry)
    monkeypatch.setattr(registry, '_locked', lambda: pytest.fail('read-only lookup acquired write lock'))
    assert registry.native_owner_contract('042660')['registered'] is True
    assert policy.resolve_symbol_owner_policy('042660').owner_allowed('main_scalping')


def test_cached_journal_revalidates_changed_bytes(registry):
    registry.retire_automatic_owners_to_manual()
    assert registry.native_owner_contract('042660')['disposition_hash']
    registry.path.write_text(registry.path.read_text().replace('operator_manual_management', 'tampered_manual_management'))
    with pytest.raises(OwnerRegistryError, match='hash_invalid'):
        registry.native_owner_contract('042660')


@pytest.mark.parametrize('defect', [None, 'guard', 'restored', 'seal', 'unsafe_path'])
def test_main_only_release_cannot_restore_removed_executor(tmp_path, defect):
    from src.engine.infrastructure import runtime_release_router as router
    root=tmp_path/'release'; workspace=tmp_path/'workspace'
    guard=root/'src/trading/config/owner_retirement.py'; guard.parent.mkdir(parents=True)
    guard.write_text('permanent guard')
    removed='src/trading/low_price_two_leg/service.py'
    body=dict(schema='main_only_automatic_owner_retirement_v1', management='operator_manual',
              retired_owners=['episode','widget_auto_trade'], guard_file_sha256=hashlib.sha256(guard.read_bytes()).hexdigest(),
              removed_surfaces=[removed])
    if defect=='guard':body['guard_file_sha256']='0'*64
    if defect=='unsafe_path':body['removed_surfaces']=['../untrusted']
    body['receipt_sha256']=router._retirement_digest(body)
    if defect=='seal':body['management']='automatic'
    target=workspace/'data/runtime/retirements/main-only-retirement.json';target.parent.mkdir(parents=True)
    target.write_text(json.dumps(body))
    if defect=='restored':
        executor=root/removed;executor.parent.mkdir(parents=True);executor.write_text('old executor')
    if defect:
        with pytest.raises(ValueError):router._validate_retired_surfaces(workspace,root)
    else:router._validate_retired_surfaces(workspace,root)


def test_retired_unresolved_intents_do_not_hold_main_watch_admission(registry):
    historical(registry, state='INTENT_RESERVED', filled=0)
    assert registry.unresolved_intent_summary(symbol='042660', active_date=None)['unresolved_intent_count']==1
    registry.retire_automatic_owners_to_manual()
    assert registry.unresolved_intent_summary(symbol='042660', active_date=None)['unresolved_intent_count']==0


@pytest.mark.parametrize('defect', [None, 'source', 'terminal', 'strict', 'archive', 'retirement', 'current_date'])
def test_historical_summary_preserves_exact_sources_without_old_executors(tmp_path, defect):
    from src.engine.automation import postclose_summary_handoff as S
    root=tmp_path/'data'; reports=root/'report'; day='2026-10-07'
    source=reports/'source.json'; source.parent.mkdir(parents=True); source.write_text('{}')
    strict=reports/'attempt.json'
    strict.write_text(json.dumps(dict(date=day,status='pass',verification_scope='whole_native_chain',whole_native_chain_done_claimed=True)))
    value=dict(schema=S.STAGE_SCHEMA,stage_id='summary_handoff',source_date=day,
        run_id='sealed',status='succeeded',exit_code=0,sources=S._stage_sources({'source':source}),
        prerequisite_receipts={},input_sources={})
    terminal=S.stage_path(reports,day,'summary_handoff'); terminal.parent.mkdir(parents=True)
    S._stage_write(terminal,value); value=json.loads(terminal.read_text())
    retirement_path=root/'runtime/retirements/main-only-retirement.json';retirement_path.parent.mkdir(parents=True)
    archive=retirement_path.with_name('historical-summary-archive.json')
    archive.write_text(json.dumps(dict(schema='retirement_historical_summary_archive_v1',
        authority='operator_main_only_complete_retirement_20261008',cutover_date='2026-10-08',runtime_effect=False,
        summaries={day:dict(validated_original_contract=True,original_code_commit='a'*40,
            terminal_sha256=hashlib.sha256(terminal.read_bytes()).hexdigest(),strict_attempt_path=str(strict),
            strict_attempt_sha256=hashlib.sha256(strict.read_bytes()).hexdigest())})))
    retirement=dict(schema='main_only_automatic_owner_retirement_v1',management='operator_manual',
        historical_summary_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    retirement['receipt_sha256']=S._stage_digest(retirement); retirement_path.write_text(json.dumps(retirement))
    if defect=='source':source.write_text('changed')
    if defect=='terminal':terminal.write_text('{}')
    if defect=='strict':strict.write_text('{}')
    if defect=='archive':archive.write_text('{}')
    if defect=='retirement':retirement_path.write_text('{}')
    result=S._retired_summary_archive_issues(reports,'2026-10-08' if defect=='current_date' else day,value)
    if defect in {'current_date','retirement'}: assert result is None
    elif defect: assert result
    else: assert result==[]


def test_manual_holdings_do_not_become_main_watch_inventory(registry):
    from src.engine.scalping import ai_market_snapshot as market
    historical(registry, symbol='005930')
    registry.retire_automatic_owners_to_manual()
    old=dict(market._BROKER_ACCOUNT_SNAPSHOT)
    try:
        market.publish_broker_account_snapshot(inventory=[{'code':'005930','qty':10}],
            open_orders=[], successful_exchanges={'KRX','NXT'},
            open_orders_request_succeeded=True, captured_at=1000)
        assert market.broker_symbol_verified_flat('005930',now_ts=1000)[1]=='broker_position_nonzero'
        assert market.broker_symbol_verified_flat('005930',now_ts=1000,allow_manual_remainder=True)==(True,'verified_main_flat_manual_remainder')
        assert market.broker_symbol_verified_flat('005930',now_ts=1100,allow_manual_remainder=True)[1]=='broker_snapshot_missing_or_stale'
    finally:
        market._BROKER_ACCOUNT_SNAPSHOT.clear();market._BROKER_ACCOUNT_SNAPSHOT.update(old)


@pytest.mark.parametrize('side,action',[('BUY','NEW'),('SELL','NEW'),('BUY','CANCEL')])
def test_retirement_monitor_distinguishes_manual_history_from_new_automatic_intents(tmp_path, monkeypatch, side, action):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.error_detectors.process_health import _retirement_expected_set
    from src.engine.infrastructure import runtime_release_router as R
    monkeypatch.setattr(R,'_episode_retirement_receipts',lambda root: [])
    monkeypatch.setattr(R,'_retirement_units',lambda profiles: [])
    path=tmp_path/'data/runtime/retirements/main-only-retirement.json';path.parent.mkdir(parents=True)
    body=dict(schema='main_only_automatic_owner_retirement_v1',management='operator_manual',
              management_observed_at_kst='2026-10-08T12:00:00+09:00')
    body['receipt_sha256']=R._retirement_digest(body);path.write_text(json.dumps(body))
    old=dict(event='INTENT_RESERVED',order_date='2026-10-08',observed_at_kst='2026-10-08T09:00:00+09:00',
             owner_type='episode',symbol='475150',side=side,action=action)
    now=datetime(2026,10,8,13,tzinfo=ZoneInfo('Asia/Seoul'))
    check=lambda rows:_retirement_expected_set(tmp_path,now,states={},processes=[],registry_rows=rows)
    assert check([old])['status']=='retired_not_expected'
    new=dict(old,observed_at_kst='2026-10-08T12:01:00+09:00')
    assert check([old,new])['status']=='retirement_leak'
    bad=dict(new,observed_at_kst='invalid')
    assert check([bad])['status']=='retirement_unverified'


@pytest.mark.parametrize('stderr',['','Access denied'])
def test_deleted_unit_census_accepts_empty_listing_but_not_permission_failure(tmp_path,monkeypatch,stderr):
    from datetime import datetime
    import subprocess
    from src.engine.error_detectors import process_health as H
    from src.engine.infrastructure import runtime_release_router as R
    unit='korstockscan-low-price-two-leg-test.service'
    monkeypatch.setattr(R,'_episode_retirement_receipts',lambda root: [])
    monkeypatch.setattr(R,'_retirement_units',lambda profiles: [unit])
    def run(cmd,**kwargs):
        if 'list-unit-files' in cmd:return subprocess.CompletedProcess(cmd,1,'',stderr)
        if 'list-units' in cmd:return subprocess.CompletedProcess(cmd,0,'','')
        return subprocess.CompletedProcess(cmd,0,f'Id={unit}\nLoadState=not-found\nActiveState=inactive\nMainPID=0\n','')
    monkeypatch.setattr(H.subprocess,'run',run)
    result=H._retirement_expected_set(tmp_path,datetime.fromisoformat('2026-10-08T13:00:00+09:00'),processes=[],registry_rows=[])
    assert result['status']==('retirement_unverified' if stderr else 'retired_not_expected')


@pytest.mark.parametrize('defect',[None,'missing','unknown_key','relative_registry','duplicate_key','shell_expression'])
def test_routed_postclose_and_runtime_share_native_identity_without_shell_execution(tmp_path,defect):
    from src.engine.infrastructure.runtime_release_router import native_custody_environment
    retirement=tmp_path/'data/runtime/retirements/main-only-retirement.json';retirement.parent.mkdir(parents=True);retirement.write_text('{}')
    identity=tmp_path/'data/config/native_owner_custody.env';identity.parent.mkdir(parents=True)
    text="KORSTOCKSCAN_BROKER_ACCOUNT_KEY='approved-account'\nKORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH='/absolute/common-journal.jsonl'\n"
    if defect=='unknown_key':text+='UNAPPROVED_AUTHORITY=true\n'
    if defect=='relative_registry':text=text.replace('/absolute/','relative/')
    if defect=='duplicate_key':text+="KORSTOCKSCAN_BROKER_ACCOUNT_KEY='other-account'\n"
    if defect=='shell_expression':text=text.replace("'approved-account'",'$(touch /tmp/should_never_be_executed)')
    if defect!='missing':identity.write_text(text)
    if defect:
        with pytest.raises((ValueError,OSError)):native_custody_environment(tmp_path)
    else:assert native_custody_environment(tmp_path)==dict(KORSTOCKSCAN_BROKER_ACCOUNT_KEY='approved-account',KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH='/absolute/common-journal.jsonl')


def test_native_custody_projection_reuses_only_verified_generation(registry, monkeypatch):
    historical(registry)
    state=registry._state;calls=[]
    monkeypatch.setattr(registry,'_state',lambda events:calls.append(len(events)) or state(events))
    first=registry.native_owner_contract('042660')
    first['registered']=False
    for _ in range(20): assert registry.native_owner_contract('042660')['registered'] is True
    assert len(calls)==1
    registry.retire_automatic_owners_to_manual()
    value=registry.native_owner_contract('042660')
    assert len(calls)==2 and value['disposition_hash']
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY','other-account')
    with pytest.raises(OwnerRegistryConflict):registry.native_owner_contract('042660')
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY','retirement-test-account')
    text=registry.path.read_text();registry.path.write_text(text.replace('042660','042661'))
    with pytest.raises(OwnerRegistryConflict,match='hash_invalid'):registry.native_owner_contract('042660')
