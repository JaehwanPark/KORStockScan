"""Cross-consumer retirement, custody and Main subscription regressions."""
import asyncio
from copy import deepcopy
from datetime import date
import hashlib
import json
from types import SimpleNamespace

import pytest

from src.engine.scalping import main_fixed_watch as fixed
from src.trading.config import owner_retirement as retired
from src.tests.test_main_fixed_watch import _TestDB, epoch


def test_two_fixed_watches_have_separate_admissions_and_two_reserved_slots(monkeypatch):
    for spec in fixed.SPECS[:2]:
        monkeypatch.setenv(spec.enable_env, 'true')
    monkeypatch.setattr(fixed, 'broker_and_owner_clear', lambda *_: (True, 'verified_flat'))
    db, targets = _TestDB(), []
    for spec in fixed.SPECS[:2]:
        assert fixed.reconcile(db, targets, now_epoch=epoch(10), watch_cap=2, symbol=spec.symbol)[0] == 'armed'
    assert fixed.reserved_slots() == 2
    assert len({t['id'] for t in targets}) == len({t['watch_admission_id'] for t in targets}) == 2
    assert len({t['watch_generation_id'] for t in targets}) == 2
    assert targets[1]['initial_policy_scope'] == 'non_samsung'
    samsung = deepcopy(targets[0])
    assert fixed.reconcile(db, targets, now_epoch=epoch(16), watch_cap=2, symbol='034020')[0] == 'armed'
    assert targets[0] == samsung


@pytest.mark.parametrize('symbol', ['034020', 'A034020', '034020_AL', '034020_NX'])
def test_retired_symbol_cannot_be_renamed_or_resuffixed(symbol):
    assert retired.new_entry_retired(symbol, 'episode')
    assert not retired.new_entry_retired(symbol, 'main_scalping')
    assert not any(p.symbol == '034020' for p in __import__('src.trading.low_price_two_leg.profiles', fromlist=['PROFILES']).PROFILES.values())
    assert retired.main_manual_after_episode_retirement(symbol, ['main_scalping', 'manual_operator'])


def test_dynamic_episode_and_gateway_cannot_restore_retired_buy():
    from src.trading.low_price_two_leg.profiles import PROFILES
    from dataclasses import replace
    from src.trading.low_price_two_leg.gateway import KiwoomLowPriceTwoLegGateway
    policy = next(iter(PROFILES.values()))
    with pytest.raises(ValueError, match='symbol_owner_permanently_retired'):
        replace(policy, symbol='034020', profile_id='renamed_doosan')
    gateway = KiwoomLowPriceTwoLegGateway.__new__(KiwoomLowPriceTwoLegGateway)
    gateway.symbol = '034020'
    gateway._require_write_authority = lambda: pytest.fail('retired BUY reached authority or HTTP')
    assert gateway.submit_limit_buy(price=10000, quantity=10).return_code == 'SYMBOL_OWNER_RETIRED'


def _registry(tmp_path, monkeypatch):
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY', 'test-account')
    monkeypatch.setenv('KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH', str(tmp_path/'registry.jsonl'))
    return OrderOwnerRegistry()


def _activation(registry):
    day = date(2026,10,7)
    migration = registry.migration_receipt(symbol='034020', broker_quantity=0, active_date=day,
        verified_exchanges={'KRX','NXT'}, broker_open_order_nos=set(), broker_snapshot_sha256='d'*64)
    return registry.activate_policy_entry(active_date=day, policy_id='test-main-doosan', symbol='034020',
        mode='COEXIST_ENTRY_ENABLED', allowed_owners=['main_scalping','manual_operator'],
        migration_receipt=migration, entry_authority_hash='a'*64)


def test_native_main_manual_activation_has_no_economic_proof_gate(tmp_path, monkeypatch):
    registry = _registry(tmp_path, monkeypatch)
    receipt = _activation(registry)
    assert receipt['symbol'] == '034020'
    assert receipt['activation_event_hash']
    assert not retired.main_manual_after_episode_retirement('005930', ['main_scalping','manual_operator'])


@pytest.mark.parametrize('action', ['NEW', 'CANCEL'])
def test_retirement_open_exposure_distinguishes_new_order_from_cancel_ack(tmp_path, monkeypatch, action):
    from src.trading.order.owner_custody_registry import OwnerOrderContext, OwnerRegistryConflict
    registry = _registry(tmp_path, monkeypatch)
    original = None
    if action == 'CANCEL':
        original = registry.reserve(context=OwnerOrderContext(owner_type='episode', owner_id='episode:old',
            position_id='episode:old:leg', client_intent_id='episode:old:original'), symbol='034020',
            side='BUY', quantity=10, route='KRX', order_date='2026-09-09')
        registry.transition(original, state='ORDER_BOUND', broker_order_no='0000010')
    intent = registry.reserve(context=OwnerOrderContext(owner_type='episode', owner_id='episode:old',
        position_id='episode:old:leg', client_intent_id='episode:old:intent'), symbol='034020',
        side='BUY', quantity=10, route='KRX', order_date='2026-09-09', action=action,
        original_order_no='0000010' if action == 'CANCEL' else '')
    registry.transition(intent, state='ORDER_BOUND', broker_order_no='0000011')
    if original is not None:
        registry.transition(original, state='ORDER_TERMINAL', broker_order_no='0000010')
    if action == 'NEW':
        with pytest.raises(OwnerRegistryConflict, match='retirement_not_flat'):
            _activation(registry)
    else:
        assert _activation(registry)['activation_event_hash']
        historical = registry.verified_events_snapshot()
        cancel = registry._state(historical)[intent]
        assert cancel['action'] == 'CANCEL' and cancel['state'] == 'ORDER_BOUND'


def test_all_date_intent_blocks_doosan_admission_and_activation(tmp_path, monkeypatch):
    registry = _registry(tmp_path, monkeypatch)
    from src.trading.order.owner_custody_registry import OwnerOrderContext, OwnerRegistryConflict
    registry.reserve(context=OwnerOrderContext(owner_type='episode', owner_id='episode:old', position_id='episode:old:leg',
        client_intent_id='episode:old:intent'), symbol='034020', side='BUY', quantity=10,
        route='KRX', order_date='2026-10-02')
    assert registry.unresolved_intent_summary(symbol='034020', active_date='2026-10-07')['unresolved_intent_count'] == 0
    assert registry.unresolved_intent_summary(symbol='034020', active_date=None)['unresolved_intent_count'] == 1
    with pytest.raises(OwnerRegistryConflict, match='retirement_not_flat'):
        _activation(registry)
    from src.engine.scalping import ai_market_snapshot
    monkeypatch.setattr(ai_market_snapshot, 'broker_symbol_verified_flat', lambda *a, **k: (True,'flat'))
    assert fixed.broker_and_owner_clear(epoch(10), {'symbol':'034020'}) == (False,'owner_registry_unresolved_intent')


def test_al_observation_adoption_waits_for_new_real_packets(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    manager = KiwoomWSManager('test-token')
    monkeypatch.setattr(manager, '_maybe_write_dashboard_snapshot', lambda: None)
    monkeypatch.setattr(manager, '_observe_micro_reversion_forward', lambda *a, **k: None)
    manager.websocket = SimpleNamespace()
    manager._session_ready.set()
    manager._market_data_transport_epoch = 3
    manager.subscribed_codes.add('034020')
    manager._registered_items_by_code['034020'] = ('034020_AL','034020_NX')
    manager._registered_item_epochs['034020_AL'] = 3
    manager._registered_item_types['034020_AL'] = {'0B','0D'}
    manager._micro_reversion_observation_only_items.update({'034020_AL','034020_NX'})
    manager._micro_reversion_observation_only_codes.add('034020')
    old = manager._ensure_target_defaults('034020_AL', store=manager._micro_reversion_observation_route_data)
    old['curr'] = 99999
    now = epoch(10)
    route = fixed.session_route(now,'034020')
    target = dict(code='034020',status='WATCHING',watch_origin=fixed.WATCH_ORIGIN,
        watch_generation_id=fixed.generation_id(now,route),watch_admission_id='native',entry_armed_at_epoch=now)
    assert manager.adopt_main_fixed_watch_target(target, now_ts=now)
    assert manager.get_latest_data('034020').get('curr',0) == 0
    assert '034020_NX' in manager._micro_reversion_observation_only_items
    assert '034020_AL' not in manager._micro_reversion_observation_only_items
    asyncio.run(manager._handle_message(json.dumps(dict(trnm='REAL',data=[dict(type='0B',item='034020_AL',
        values={'10':'10000','15':'+1','228':'101.5'})]))))
    assert manager.get_latest_data('034020')['curr'] == 10000
    manager._registered_item_epochs['034020_AL'] = 2
    assert not manager.adopt_main_fixed_watch_target(target, now_ts=now)


def test_fixed_reg_preserves_other_exact_observation_item(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.tests.test_kiwoom_websocket import _FakeWS
    manager = KiwoomWSManager('test-token')
    monkeypatch.setattr(manager, '_maybe_write_dashboard_snapshot', lambda: None)
    monkeypatch.setattr(manager, '_observe_micro_reversion_forward', lambda *a, **k: None)
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._registered_items_by_code['034020'] = ('034020_NX',)
    manager._micro_reversion_observation_only_items.add('034020_NX')
    asyncio.run(manager._send_reg(['034020_AL'], source='main_fixed_watch_admission', realtime_types=('0B','0D'),
                                replace_existing=False, remove_before_reg=False))
    assert all(json.loads(packet)['trnm'] != 'REMOVE' for packet in manager.websocket.sent)
    assert set(manager._registered_items_by_code['034020']) == {'034020_NX','034020_AL'}
    assert '034020_NX' in manager._micro_reversion_observation_only_items
    assert manager._runtime_primary_items_by_code['034020'] == '034020_AL'


def test_retirement_prepare_is_read_only_and_binds_installed_bytes(tmp_path):
    from src.engine.automation import owner_retirement_transition as transition
    workspace, units = tmp_path/'work', tmp_path/'units'
    guard = workspace/'src/trading/config/owner_retirement.py'
    guard.parent.mkdir(parents=True)
    guard.write_text('reviewed retirement guard')
    units.mkdir()
    unit = units/transition.units()[0]
    unit.write_text('installed timer')
    manifest = transition.prepare(workspace, systemd_dir=units)
    assert unit.read_text() == 'installed timer'
    assert manifest['initial_policy_preproof_required'] is False
    assert manifest['receipt_sha256'] == transition.digest({k:v for k,v in manifest.items() if k!='receipt_sha256'})
    assert manifest['installed_files'] == [dict(path=str(unit),sha256=hashlib.sha256(unit.read_bytes()).hexdigest())]


def test_retirement_flat_check_rejects_older_unresolved_intent(tmp_path, monkeypatch):
    from src.engine.automation.owner_retirement_transition import require_flat
    from datetime import datetime
    snapshot = dict(verified_exchanges=['KRX','NXT'],inventory={'034020':0},open_orders=[],migration_receipts=[])
    snapshot['snapshot_sha256'] = hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    registry = SimpleNamespace(reconcile_symbol_quantity=lambda **k: dict(registered_owner_quantity=0,external_manual_remainder=0),
        unresolved_intent_summary=lambda **k: dict(unresolved_intent_count=int(k['active_date'] is None)))
    with pytest.raises(ValueError, match='unresolved_intent'):
        require_flat(snapshot, registry, observed_at=datetime.fromisoformat('2026-10-07T08:00:00+09:00'))


def test_old_doosan_revision_does_not_stop_other_native_fact_writers(tmp_path, monkeypatch):
    from src.engine.monitoring import research_source_facts as facts, research_closed_loop as loop
    candidates=tmp_path/'candidates'; candidates.mkdir()
    (candidates/'episode_034020.json').write_text(json.dumps(dict(symbol='034020',owner='episode')))
    calls=[]
    monkeypatch.setattr(loop,'admission_symbols',lambda *a,**k: {})
    monkeypatch.setattr(loop,'validate_revision',lambda r: calls.append(r) or pytest.fail('retired revision reached active validation'))
    writer=facts.SharedResearchFactWriter(['034020'],directory=tmp_path,snapshot_path=tmp_path/'absent.json')
    from datetime import datetime
    writer.collect_once(datetime.fromisoformat('2026-10-06T10:00:00+09:00'))
    assert writer.symbols == set() and writer.revisions == {} and calls == []


def test_native_owner_policy_readback_and_manual_veto_after_retirement(tmp_path, monkeypatch):
    from src.trading.config.symbol_owner_policy import (build_symbol_owner_policy_payload,
        symbol_owner_entry_authority_hash, resolve_symbol_owner_policy)
    from src.engine.risk import manual_control_exclusion as manual
    registry=_registry(tmp_path,monkeypatch)
    day=date(2026,10,7); policy_id='doosan-main'
    migration=registry.migration_receipt(symbol='034020',broker_quantity=0,active_date=day,
        verified_exchanges={'KRX','NXT'},broker_open_order_nos=set(),broker_snapshot_sha256='d'*64)
    entry=dict(mode='COEXIST_ENTRY_ENABLED',allowed_owners=['main_scalping','manual_operator'],migration_completed=True,
               rollback_mode='COEXIST_EXIT_ONLY',migration_receipt=migration)
    entry['activation_receipt']=registry.activate_policy_entry(active_date=day,policy_id=policy_id,symbol='034020',
        mode=entry['mode'],allowed_owners=entry['allowed_owners'],migration_receipt=migration,
        entry_authority_hash=symbol_owner_entry_authority_hash(active_date=day,policy_id=policy_id,symbol='034020',entry=entry))
    payload=build_symbol_owner_policy_payload(active_date=day,policy_id=policy_id,generated_at_kst='2026-10-07T07:40:00+09:00',symbol_entries={'034020':entry})
    path=tmp_path/'policy.json'; path.write_text(json.dumps(payload))
    monkeypatch.setenv('KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE',str(path))
    exclusion=tmp_path/'excluded.txt'; exclusion.write_text('034020 # machine_owner_scope doosan_widget_and_episode_independent_owners\n')
    monkeypatch.setenv('KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE',str(exclusion))
    manual._invalidate_file_cache()
    decision=resolve_symbol_owner_policy('034020',target_date=day)
    assert decision.coexistence_enabled and decision.owner_allowed('main_scalping')
    assert not decision.owner_allowed('episode')
    assert not manual.evaluate_main_bot_control_exclusion('034020',target_date=day).excluded
    exclusion.write_text(exclusion.read_text()+'034020 # explicit_user_veto\n')
    manual._invalidate_file_cache()
    assert manual.evaluate_main_bot_control_exclusion('034020',target_date=day).excluded


@pytest.mark.parametrize('grouped', [False, True])
@pytest.mark.parametrize('failure', [None,'active_service','reload_failure'])
def test_retirement_apply_keeps_active_exit_owner_and_prevents_rollback_before_unlink(tmp_path,monkeypatch,failure,grouped):
    from src.engine.automation import owner_retirement_transition as transition
    from src.engine.infrastructure import runtime_release_router as router
    from src.trading.order import symbol_owner_policy_apply as owner_apply
    workspace=tmp_path/'work'; units=tmp_path/'units'; units.mkdir()
    guard=workspace/'src/trading/config/owner_retirement.py'; guard.parent.mkdir(parents=True); guard.write_text('reviewed')
    scope=tuple(sorted(set(retired.RETIRED_EPISODE_PROFILES)-{'034020'})) if grouped else ('034020',)
    unit=units/transition.units(scope)[0]; unit.write_text('timer')
    manifest=transition.prepare(workspace,systemd_dir=units,**({"symbols":scope} if grouped else {}))
    manifest['systemd_dir']='/etc/systemd/system'
    manifest['receipt_sha256']=transition.digest({k:v for k,v in manifest.items() if k!='receipt_sha256'})
    monkeypatch.setattr(transition,'prepare',lambda *a,**k:manifest)
    monkeypatch.setattr(router,'selected_release',lambda *a:(workspace,'a'*40))
    monkeypatch.setattr(owner_apply,'find_running_trading_processes',lambda:[])
    snapshot=dict(verified_exchanges=['KRX','NXT'],inventory={symbol:0 for symbol in scope},open_orders=[],migration_receipts=[])
    snapshot['snapshot_sha256']=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    registry=SimpleNamespace(reconcile_symbol_quantity=lambda **k:dict(registered_owner_quantity=0,external_manual_remainder=0),
                             unresolved_intent_summary=lambda **k:dict(unresolved_intent_count=0))
    calls=[]
    def runner(command,**kwargs):
        calls.append(command)
        if command[1]=='show':
            if '--property=LoadState' in command:
                masked=any(call[1]=='mask' for call in calls) and command[2].endswith('.service')
                return SimpleNamespace(stdout='masked\n' if masked else 'loaded\n')
            return SimpleNamespace(stdout='active\n123\n' if failure=='active_service' else 'inactive\n0\n')
        if command[1]=='daemon-reload' and failure=='reload_failure':raise RuntimeError('reload failed')
        return SimpleNamespace(stdout='')
    if failure:
        with pytest.raises((ValueError,RuntimeError)):
            transition.apply(manifest,registry=registry,snapshot_fetcher=lambda:snapshot,runner=runner)
    else:
        result=transition.apply(manifest,registry=registry,snapshot_fetcher=lambda:snapshot,runner=runner)
        assert result['state']=='terminal'
        assert len(result['masked_instances']) == (54 if grouped else 6)
    receipt=workspace/'data/runtime/retirements'/transition.receipt_file(manifest)
    assert all('--now' not in command for command in calls if any(word.endswith('.service') for word in command))
    if failure=='active_service':
        assert unit.exists() and not receipt.exists()
        assert not any(command[1]=='mask' for command in calls)
    else:
        assert not unit.exists() and receipt.exists()
        assert json.loads(receipt.read_text())['state']==('entry_retired' if failure else 'terminal')
        router._validate_retired_surfaces(workspace,workspace)
        older=tmp_path/'older'; older.mkdir()
        with pytest.raises(ValueError,match='restores_permanently_retired'):
            router._validate_retired_surfaces(workspace,older)


def test_daily_owner_renewal_preserves_main_holding_after_initial_flat(tmp_path,monkeypatch):
    from src.trading.order.owner_custody_registry import OwnerOrderContext
    registry=_registry(tmp_path,monkeypatch)
    _activation(registry)
    context=OwnerOrderContext(owner_type='main_scalping',owner_id='main_scalping:held',
        position_id='main_scalping:held',client_intent_id='main_scalping:held:intent')
    intent=registry.reserve(context=context,symbol='034020',side='BUY',quantity=10,route='KRX',order_date='2026-10-07')
    registry.transition(intent,state='ORDER_BOUND',broker_order_no='1234567')
    registry.record_fill(context=context,symbol='034020',side='BUY',order_quantity=10,order_date='2026-10-07',
        broker_order_no='1234567',cumulative_filled_qty=10,cumulative_fill_amount=100000)
    day=date(2026,10,8)
    migration=registry.migration_receipt(symbol='034020',broker_quantity=10,active_date=day,verified_exchanges={'KRX','NXT'},
        broker_open_order_nos=set(),broker_snapshot_sha256='c'*64)
    receipt=registry.activate_policy_entry(active_date=day,policy_id='renewed-doosan',symbol='034020',mode='COEXIST_ENTRY_ENABLED',
        allowed_owners=['main_scalping','manual_operator'],migration_receipt=migration,entry_authority_hash='b'*64)
    assert receipt['active_date']=='2026-10-08'
    assert registry.owner_position_qty('main_scalping:held',symbol='034020')==10


@pytest.mark.parametrize('argv,blocked', [
    (['/usr/bin/python', 'bot_main.py'], False),
    (['/bin/bash', 'run_bot.sh'], False),
    (['/usr/bin/python', '/tmp/bot_main.py'], True),
    (['/usr/bin/python', '-c', 'bot_main.py'], True),
    (['/usr/bin/python', '-m', 'src.trading.low_price_two_leg.service', '--profile', 'mirae_asset_morning', '--live'], False),
    (['/usr/bin/python', '-m', 'src.trading.low_price_two_leg.service', '--profile', 'doosan_enerbility_afternoon', '--live'], True),
    (['/usr/bin/python', '-m', 'src.trading.low_price_two_leg.service', '--profile', 'dynamic_unknown', '--live'], True),
    (['/usr/bin/python', '-m', 'src.trading.low_price_two_leg.service', '--profile', 'mirae_asset_morning', '--profile', 'doosan_enerbility_afternoon'], True),
    (['/usr/bin/python', '-m', 'src.trading.low_price_two_leg.service', '--profile', 'mirae_asset_morning', '--symbol', '034020'], True),
])
def test_retirement_process_scope_preserves_foreign_owners(tmp_path, argv, blocked):
    from src.engine.automation.owner_retirement_transition import blocking_retirement_processes
    workspace=tmp_path/'work'; (workspace/'src').mkdir(parents=True)
    proc=tmp_path/'proc'; row=proc/'123'; row.mkdir(parents=True)
    (row/'cmdline').write_bytes(b'\0'.join(arg.encode() for arg in argv)+b'\0')
    (row/'cwd').symlink_to(workspace/'src', target_is_directory=True)
    (row/'exe').symlink_to('/usr/bin/python3')
    census=[dict(pid=123, command='untrusted display text')]
    assert bool(blocking_retirement_processes(census,workspace=workspace,proc_root=proc)) == blocked
    (row/'cmdline').unlink()
    assert blocking_retirement_processes(census,workspace=workspace,proc_root=proc) == census


def test_retirement_prepare_preserves_instance_masks(tmp_path):
    from src.engine.automation import owner_retirement_transition as transition
    workspace=tmp_path/'work'; units=tmp_path/'units'; units.mkdir()
    guard=workspace/'src/trading/config/owner_retirement.py'; guard.parent.mkdir(parents=True); guard.write_text('reviewed')
    service=next(name for name in transition.units() if name.endswith('.service'))
    (units/service).symlink_to('/dev/null')
    assert transition.prepare(workspace,systemd_dir=units)['installed_files'] == []
    assert (units/service).is_symlink()


def test_retirement_control_receipt_is_readable_by_runtime_user(tmp_path):
    from src.engine.automation.owner_retirement_transition import atomic_write_json
    path=tmp_path/'retirement.json'
    atomic_write_json(path,dict(state='terminal'))
    assert path.stat().st_mode & 0o777 == 0o644
    assert json.loads(path.read_text()) == dict(state='terminal')
