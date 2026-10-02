"""Diagnostic scheduling, priority, isolation and persistent key pools."""
from concurrent.futures import Future
from itertools import cycle
from types import SimpleNamespace
import threading
import time

import pytest

from src.engine.ai.transport_warmup import TransportWarmup


def fixture_warmup(*, allowed=True, busy=False, failure=None, clients=1):
    calls, receipts, now = [], [], [100.0]
    def create(**kwargs):
        calls.append(kwargs)
        if failure:
            raise failure
        return SimpleNamespace(status='completed', output_text='OK',
                               usage=SimpleNamespace(input_tokens=31, output_tokens=5))
    group = [SimpleNamespace(responses=SimpleNamespace(create=create)) for _ in range(clients)]
    warmup = TransportWarmup(group, allowed=lambda: allowed, busy=lambda: busy,
                             record=receipts.append, clock=lambda: now[0])
    return warmup, calls, receipts, now


def test_cadence_bounds_token_budget_and_separates_decision_ledgers():
    warmup, calls, receipts, now = fixture_warmup(clients=2)
    try:
        warmup.tick()
        assert len(calls) == len(receipts) == 2
        now[0] += 239
        warmup.tick()
        assert len(calls) == 2
        now[0] += 1
        warmup.tick()
        assert len(calls) == 4
        assert all(c['model']=='gpt-5.4-nano' and c['store'] is False and
                   c['max_output_tokens']==16 and c['timeout']==5 for c in calls)
        assert all(r['decision_authority']=='transport_diagnostic_only' and
                   r['tuning_input_allowed'] is False and
                   r['actual_order_submitted'] is False for r in receipts)
        assert all('output_text' not in r and 'api_key' not in r for r in receipts)
    finally:
        warmup.stop()


@pytest.mark.parametrize('allowed,busy', [(False,False),(True,True),(False,True)])
def test_closed_session_or_live_priority_makes_no_provider_call(allowed,busy):
    warmup, calls, receipts, _ = fixture_warmup(allowed=allowed,busy=busy)
    try:
        warmup.tick()
        assert calls == receipts == []
    finally:
        warmup.stop()


def test_real_model_activity_defers_diagnostic_without_repeated_call():
    warmup, calls, receipts, now = fixture_warmup()
    try:
        warmup.note_activity(warmup.clients[0])
        warmup.tick()
        assert not calls
        now[0] += 240
        warmup.tick()
        assert len(calls)==1
        warmup.note_activity(warmup.clients[0])
        now[0] += 239
        warmup.tick()
        assert len(calls)==1
    finally:
        warmup.stop()


def test_failed_warmup_does_not_retry_within_cadence_or_emit_error_text():
    warmup, calls, receipts, now = fixture_warmup(failure=RuntimeError('sensitive'))
    try:
        warmup.tick()
        warmup.tick()
        assert len(calls)==1
        assert receipts[0]['status']=='error'
        assert receipts[0]['error_type']=='RuntimeError'
        assert 'sensitive' not in str(receipts)
    finally:
        warmup.stop()


def test_running_late_warmup_never_queues_another_provider_request():
    warmup, calls, receipts, now = fixture_warmup()
    pending = Future()
    pending.set_running_or_notify_cancel()
    warmup.pending=pending
    try:
        now[0] += 1000
        warmup.tick()
        assert not calls
    finally:
        pending.set_result(None)
        warmup.stop()


def test_timeout_receipt_keeps_late_worker_bound(monkeypatch):
    warmup, calls, receipts, now = fixture_warmup()
    class LateFuture:
        def result(self, timeout):
            assert timeout==5
            raise TimeoutError()
        def done(self): return False
        def cancel(self): return False
    monkeypatch.setattr(warmup.executor,'submit',lambda *a,**k: LateFuture())
    try:
        warmup.tick()
        assert receipts[0]['status']=='timeout'
        now[0] += 1000
        warmup.tick()
        assert len(receipts)==1
    finally:
        warmup.stop()


def test_stop_prevents_new_provider_calls_and_start_is_idempotent():
    warmup, calls, receipts, now = fixture_warmup(allowed=False)
    warmup.start()
    original=warmup.thread
    warmup.start()
    assert warmup.thread is original
    warmup.stop()
    original.join(timeout=1)
    assert not original.is_alive()
    warmup.tick()
    assert not calls


def test_rotation_reuses_key_pool_without_changing_key_order(monkeypatch):
    from src.engine import ai_engine_openai as module
    made=[]
    monkeypatch.setattr(module,'DefaultHttpxClient',lambda **kwargs: SimpleNamespace(**kwargs))
    def factory(**kwargs):
        made.append(kwargs)
        return SimpleNamespace(**kwargs)
    monkeypatch.setattr(module,'OpenAI',factory)
    engine=module.GPTSniperEngine.__new__(module.GPTSniperEngine)
    engine.api_keys=['a','b']
    engine.key_cycle=cycle(engine.api_keys)
    engine._rotate_client()
    first=engine.client
    engine._rotate_client()
    assert engine.current_api_key_index==1
    engine._rotate_client()
    assert engine.client is first and engine.current_api_key_index==0
    assert len(made)==2
    assert all(m['max_retries']==0 and m['http_client'].limits.keepalive_expiry==300 for m in made)


def test_diagnostic_success_or_error_preserves_live_engine_state(monkeypatch):
    from src.engine import ai_engine_openai as module
    engine=module.GPTSniperEngine.__new__(module.GPTSniperEngine)
    engine.api_keys=['a','b']
    engine.key_cycle=cycle(engine.api_keys)
    from threading import Lock
    engine.lock=Lock()
    engine.api_call_lock=Lock()
    engine.ai_disabled=False
    engine.consecutive_failures=2
    engine.last_call_time=7
    engine._analysis_cache={'live':'unchanged'}
    warmup, calls, receipts, _=fixture_warmup(failure=RuntimeError('failure'),clients=2)
    engine._client_for_key=lambda key: warmup.clients[engine.api_keys.index(key)]
    class CapturedWarmup:
        def __init__(self,clients,**kwargs):
            self.clients=clients
            assert kwargs['allowed']() is True
            assert kwargs['busy']() is False
        def start(self):warmup.tick()
    monkeypatch.setattr('src.engine.ai.transport_warmup.TransportWarmup',CapturedWarmup)
    try:
        engine.start_transport_warmup(allowed=lambda: True)
        engine.start_transport_warmup(allowed=lambda: True)
        assert len(calls)==2
        assert engine.consecutive_failures==2 and engine.ai_disabled is False
        assert engine.last_call_time==7 and engine._analysis_cache=={'live':'unchanged'}
        assert next(engine.key_cycle)=='a'
    finally:
        warmup.stop()


def test_main_start_is_role_test_and_session_gated():
    from pathlib import Path
    source=Path('src/engine/kiwoom_sniper_v2.py').read_text()
    start=source.index('if runtime_role == "main" and openai_api_keys:')
    end=source.index('elif runtime_role == "main" and not openai_api_keys:',start)
    block=source[start:end]
    assert 'if not is_test_mode:' in block
    assert 'datetime.now().date() == warmup_day' in block
    assert 'is_scalping_buy_time_allowed(datetime.now())' in block
    assert 'start_transport_warmup(' not in source[:start]+source[end:]


@pytest.mark.parametrize('change,expected', [
    ('busy', 'deferred_live_priority'), ('allowed', 'deferred_session'),
    ('stop', 'stopped'), ('deadline', 'deadline_expired_before_provider'),
])
def test_lazy_lookup_rechecks_live_session_stop_and_deadline(change, expected):
    calls, receipts, now = [], [], [100.0]
    state = {'busy': False, 'allowed': True}
    class LazyClient:
        @property
        def responses(self):
            if change == 'stop':
                warmup.stop()
            elif change == 'deadline':
                now[0] += 6
            else:
                state[change] = change == 'busy'
            return SimpleNamespace(create=lambda **kwargs: calls.append(kwargs))
    warmup = TransportWarmup([LazyClient()], allowed=lambda: state['allowed'],
        busy=lambda: state['busy'], record=receipts.append, clock=lambda: now[0])
    try:
        warmup.tick()
        assert not calls
        assert receipts[0]['status'] == expected
        assert receipts[0]['provider_call_started_at_receipt'] is False
    finally:
        warmup.stop()


def test_blocked_lazy_lookup_is_inside_deadline_and_cannot_send_late():
    entered, release = threading.Event(), threading.Event()
    calls, receipts = [], []
    class LazyClient:
        @property
        def responses(self):
            entered.set()
            assert release.wait(1)
            return SimpleNamespace(create=lambda **kwargs: calls.append(kwargs))
    warmup = TransportWarmup([LazyClient()], allowed=lambda: True,
        busy=lambda: False, record=receipts.append)
    warmup.deadline_sec = 0.05
    try:
        started = time.monotonic()
        warmup.tick()
        assert entered.is_set() and time.monotonic()-started < 0.5
        assert receipts[0]['status'] == 'timeout'
        assert receipts[0]['provider_call_started_at_receipt'] is False
        warmup.tick()
        assert len(receipts) == 1
        release.set()
        assert warmup.pending.result(timeout=1)['status'] == 'deadline_expired_before_provider'
        assert calls == []
    finally:
        release.set()
        warmup.stop()


def test_sdk_timeout_uses_remaining_budget_after_lookup():
    warmup, calls, receipts, now = fixture_warmup()
    original = warmup.clients[0].responses
    class LazyClient:
        @property
        def responses(self):
            now[0] += 2
            return original
    warmup.clients = (LazyClient(),)
    try:
        warmup.tick()
        assert calls[0]['timeout'] == 3
        assert receipts[0]['provider_call_started_at_receipt'] is True
    finally:
        warmup.stop()


def test_concurrent_ticks_do_not_admit_duplicate_work():
    entered, release = threading.Event(), threading.Event()
    warmup, calls, receipts, _ = fixture_warmup()
    create = warmup.clients[0].responses.create
    def blocked(**kwargs):
        entered.set()
        assert release.wait(1)
        return create(**kwargs)
    warmup.clients[0].responses.create = blocked
    thread = threading.Thread(target=warmup.tick)
    try:
        thread.start()
        assert entered.wait(1)
        warmup.tick()
        release.set()
        thread.join(1)
        assert not thread.is_alive() and len(calls) == len(receipts) == 1
    finally:
        release.set()
        warmup.stop()
        thread.join(1)


def test_stop_before_start_does_not_spawn_scheduler():
    warmup, calls, _, _ = fixture_warmup()
    warmup.stop()
    warmup.start()
    assert warmup.thread is None and not calls


def test_simultaneous_start_keeps_one_scheduler():
    warmup, calls, _, _ = fixture_warmup(allowed=False)
    threads = [threading.Thread(target=warmup.start) for _ in range(8)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(1)
        assert warmup.thread is not None and warmup.thread.is_alive()
        assert len([t for t in threading.enumerate() if t.name == 'main-ai-warmup']) == 1
    finally:
        warmup.stop()
        if warmup.thread is not None:
            warmup.thread.join(1)


def test_start_failure_detaches_even_if_diagnostic_shutdown_fails(monkeypatch, caplog):
    from src.engine import ai_engine_openai as module
    engine = module.GPTSniperEngine.__new__(module.GPTSniperEngine)
    engine.api_keys = ['a']
    engine._client_for_key = lambda key: object()
    class BrokenWarmup:
        def __init__(self, *args, **kwargs): pass
        def start(self): raise RuntimeError('private start message')
        def stop(self): raise ValueError('private stop message')
    monkeypatch.setattr('src.engine.ai.transport_warmup.TransportWarmup', BrokenWarmup)
    with pytest.raises(RuntimeError, match='private start message'):
        engine.start_transport_warmup(allowed=lambda: True)
    assert engine._transport_warmup is None
    assert 'ValueError' in caplog.text and 'private stop message' not in caplog.text
    with pytest.raises(RuntimeError):
        engine.start_transport_warmup(allowed=lambda: True)


def test_shutdown_failure_preserves_main_cleanup_and_live_state(caplog):
    from src.engine import ai_engine_openai as module
    engine = module.GPTSniperEngine.__new__(module.GPTSniperEngine)
    def fail(): raise RuntimeError('private diagnostic failure')
    engine._transport_warmup = SimpleNamespace(stop=fail)
    engine._analysis_cache = {'live': 'unchanged'}
    engine.consecutive_failures = 2
    cleanup = []
    engine.stop_transport_warmup()
    cleanup.append('heartbeat and source cleanup continue')
    assert cleanup and engine._transport_warmup is None
    assert engine._analysis_cache == {'live': 'unchanged'} and engine.consecutive_failures == 2
    assert 'RuntimeError' in caplog.text and 'private diagnostic failure' not in caplog.text


def test_submit_timeout_does_not_cancel_a_stale_future(monkeypatch):
    warmup, _, receipts, _ = fixture_warmup()
    stale = Future()
    stale.set_result(None)
    warmup.pending = stale
    def fail(*args, **kwargs): raise TimeoutError()
    monkeypatch.setattr(warmup.executor, 'submit', fail)
    try:
        warmup.tick()
        assert receipts[0]['status'] == 'timeout' and receipts[0]['cancelled'] is False
        assert warmup.pending is None
    finally:
        warmup.stop()
