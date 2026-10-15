"""Restart identity and durable custody; no socket, provider or broker calls."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import subprocess
import sys

import pytest

from src.trading.market import transport_epoch as E


def test_allocations_survive_restart_and_clock_rollback(tmp_path, monkeypatch):
    path = tmp_path / 'epoch.json'
    clock = 1792025242000000000
    monkeypatch.setattr(E.time, 'time_ns', lambda: clock)
    first = E.allocate_transport_epoch(path=path)
    clock -= 3600 * 10**9
    second = E.allocate_transport_epoch(path=path)
    assert second == first + 1
    source = ('from src.trading.market.transport_epoch import allocate_transport_epoch; '
              'import sys; print(allocate_transport_epoch(path=sys.argv[1]))')
    third = int(subprocess.check_output([sys.executable, '-B', '-c', source, str(path)], text=True))
    assert third > second and float(third) == third and third <= E.MAX_EPOCH


def test_concurrent_allocations_cannot_share_a_generation(tmp_path, monkeypatch):
    path = tmp_path / 'epoch.json'
    monkeypatch.setattr(E.time, 'time_ns', lambda: 1792025242000000000)
    with ThreadPoolExecutor(max_workers=8) as workers:
        epochs = list(workers.map(lambda _: E.allocate_transport_epoch(path=path), range(24)))
    assert sorted(epochs) == list(range(min(epochs), min(epochs) + 24))
    assert json.loads(path.read_text())['epoch'] == max(epochs)


def test_concurrent_processes_share_persisted_generation(tmp_path):
    path = tmp_path / 'epoch.json'
    source = ('from src.trading.market import transport_epoch as E; import sys; '
              'E.time.time_ns=lambda:1792025242000000000; '
              'print(E.allocate_transport_epoch(path=sys.argv[1]))')
    children = [subprocess.Popen([sys.executable, '-B', '-c', source, str(path)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for _ in range(4)]
    epochs = []
    for child in children:
        output, error = child.communicate(timeout=15)
        assert child.returncode == 0, error
        epochs.append(int(output))
    assert sorted(epochs) == list(range(min(epochs), min(epochs) + 4))


def test_missing_published_epoch_store_never_reinitializes(tmp_path):
    path = tmp_path / 'epoch.json'
    E.allocate_transport_epoch(path=path)
    path.unlink()
    with pytest.raises(ValueError, match='state_missing'):
        E.allocate_transport_epoch(path=path)
    assert not path.exists()


def test_epoch_exhaustion_never_rounds_or_overwrites_state(tmp_path):
    path = tmp_path / 'epoch.json'
    E.allocate_transport_epoch(path=path)
    assert E.allocate_transport_epoch(path=path, previous=E.MAX_EPOCH-1) == E.MAX_EPOCH
    before = path.read_bytes()
    with pytest.raises(ValueError, match='exhausted'):
        E.allocate_transport_epoch(path=path)
    assert path.read_bytes() == before


@pytest.mark.parametrize('damage', ['json', 'hash', 'type', 'oversize'])
def test_invalid_epoch_store_never_resets_to_legacy_counter(tmp_path, damage):
    path = tmp_path / 'epoch.json'
    E.allocate_transport_epoch(path=path)
    value = json.loads(path.read_text())
    if damage == 'hash':
        value['epoch'] += 1
    elif damage == 'type':
        value['epoch'] = True
        value['sha256'] = E._digest({k:v for k,v in value.items() if k != 'sha256'})
    path.write_text('{' if damage == 'json' else 'x' * 4097 if damage == 'oversize' else json.dumps(value))
    before = path.read_bytes()
    with pytest.raises(ValueError):
        E.allocate_transport_epoch(path=path)
    assert path.read_bytes() == before


@pytest.mark.parametrize('failure_at', ['replace', 'file_fsync', 'directory_fsync'])
def test_failed_commit_never_publishes_epoch_and_later_allocation_advances(tmp_path, monkeypatch, failure_at):
    path = tmp_path / 'epoch.json'
    first = E.allocate_transport_epoch(path=path)
    real_replace = E.os.replace
    real_fsync = E.os.fsync
    sync_count = 0
    def fail(*args):
        raise OSError('controlled storage failure')
    def fail_fsync(fd):
        nonlocal sync_count
        sync_count += 1
        if sync_count == (1 if failure_at == 'file_fsync' else 2):
            raise OSError('controlled fsync failure')
        return real_fsync(fd)
    if failure_at == 'replace':
        monkeypatch.setattr(E.os, 'replace', fail)
    else:
        monkeypatch.setattr(E.os, 'fsync', fail_fsync)
    with pytest.raises(OSError):
        E.allocate_transport_epoch(path=path)
    persisted = json.loads(path.read_text())['epoch']
    assert persisted > first if failure_at == 'directory_fsync' else persisted == first
    monkeypatch.setattr(E.os, 'replace', real_replace)
    monkeypatch.setattr(E.os, 'fsync', real_fsync)
    assert E.allocate_transport_epoch(path=path) > persisted
    assert not list(tmp_path.glob('.transport-epoch-*'))


def _native_turn(epoch, stamp):
    from src.engine.scalping.continuous_reversal_branches import PriceTurnState
    state = PriceTurnState()
    for seq, price in enumerate((214000, 211000, 211500), 2208):
        row = [stamp + (seq-2208) * .1, epoch, seq, price, price, price+250, 10, 1, True, '036930_AL', 0]
        state.observe(row, symbol='036930', venue='SOR', session='SOR_REGULAR')
    event = deepcopy(state.turn)
    event.update(signal_id=event['event_id'], native_epoch=epoch, native_sequence=2210)
    return event


def test_real_bootstrap_generations_separate_native_signals_and_preserve_old_reservations(tmp_path):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.tests.test_kiwoom_websocket import _FakeWS
    from src.engine.scalping import reversal_extended_union as U, reversal_operating_outbox as O
    from src.engine.scalping.initial_quantity_bundle_state import reserve_reversal_signal
    managers = [KiwoomWSManager('fixture') for _ in range(2)]
    events = [_native_turn(1, 1792024355.665473)]
    for manager in managers:
        manager.websocket = _FakeWS([])
        asyncio.run(manager._send_post_login_bootstrap())
        assert manager._session_ready.is_set()
        events.append(_native_turn(manager._market_data_transport_epoch, 1792025242.264881))
    assert len({event['signal_id'] for event in events}) == 3
    assert len({U.opportunity(event) for event in events}) == 3
    for i, event in enumerate(events):
        assessment = dict(opportunity_key=U.opportunity(event), signal_id=event['signal_id'],
                          scope_execution_hash='a'*64, signal_set_hash='b'*64, matched_policy_refs=['fixture'])
        O.reserve(tmp_path, assessment, f'request-{i}')
        # Neither a new policy nor replay under another consumer grants retry.
        replayed = deepcopy(assessment); replayed['scope_execution_hash'] = 'c'*64
        with pytest.raises(O.OperatingOpportunityError, match='already_reserved'):
            O.reserve(tmp_path, replayed, 'replayed-request')
        with pytest.raises(ValueError, match='already_reserved'):
            reserve_reversal_signal(tmp_path/'runtime/initial_quantity/reversal_signals',
                signal_id=event['signal_id'], stage='provider_request', identity='new', binding={})
    old_paths = list((tmp_path/'runtime/initial_quantity').rglob('*.json'))
    before = {str(p): p.read_bytes() for p in old_paths}
    asyncio.run(managers[-1]._send_post_login_bootstrap())  # Reconnect also advances.
    assert managers[-1]._market_data_transport_epoch > events[-1]['native_epoch']
    assert before == {str(p): p.read_bytes() for p in old_paths}


def test_bootstrap_storage_failure_does_not_subscribe_or_publish_ready(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.tests.test_kiwoom_websocket import _FakeWS
    manager = KiwoomWSManager('fixture'); manager.websocket = _FakeWS([])
    manager._session_ready.set()
    def fail(**kwargs):
        raise OSError('controlled storage failure')
    monkeypatch.setattr(E, 'allocate_transport_epoch', fail)
    with pytest.raises(OSError):
        asyncio.run(manager._send_post_login_bootstrap())
    assert not manager._session_ready.is_set() and not manager.websocket.sent
    assert manager._market_data_transport_epoch == 0
