"""Pending-to-native handoff acceptance; no Main startup or provider/order I/O.

Exercise the production ready notifier, visit scheduler, pending gate, native
selector, coordinator completion/consumption and WATCHING cleanup together.
The clock/event and worker completion are deterministic. The trading body is
replaced by a terminal WAIT sink; this is a bounded integration test, not a
full run_sniper replay or a latency benchmark.
"""
from collections import OrderedDict, deque
from concurrent.futures import Future
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.engine import sniper_state_handlers as H
from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
from src.engine.monitoring import runtime_performance as R
from src.engine.scalping import entry_deadline as D
from src.engine.scalping import main_fixed_watch as W
from src.engine.scalping import reversal_current_backend as CURRENT
from src.engine.scalping import reversal_evaluation_context as POLICY
from src.engine.scalping import reversal_extended_runtime as N
from src.engine.scalping import reversal_source_diagnostics as SOURCE
from src.engine.scalping import scanner_async_eval as A


class Clock:
    def __init__(self):
        self.epoch = datetime(2026, 10, 15, 8, 29, tzinfo=N.K.KST).timestamp()
        self.perf = 1000.0

    def time(self):
        return self.epoch

    def perf_counter(self):
        return self.perf

    monotonic = perf_counter

    def advance(self, seconds):
        self.epoch += seconds
        self.perf += seconds


class ControlledEvent:
    """Event semantics with a scheduled notification, without wall-clock sleep."""
    def __init__(self, clock):
        self.clock = clock
        self.flag = False
        self.on_wait = None
        self.blocked_seconds = []

    def set(self):
        self.flag = True

    def clear(self):
        self.flag = False

    def is_set(self):
        return self.flag

    def wait(self, timeout=None):
        if self.on_wait is not None:
            callback, self.on_wait = self.on_wait, None
            callback()
        if self.flag:
            return True
        assert timeout is not None
        self.blocked_seconds.append(timeout)
        self.clock.advance(timeout)
        return False


class DeferredExecutor:
    """Keep preparation pending until the test supplies its worker terminal."""
    def submit(self, *_args, **_kwargs):
        return Future()

    def shutdown(self, **_kwargs):
        pass


@pytest.fixture
def lane(monkeypatch):
    clock = Clock()
    for module in (H, R, D, A, SOURCE):
        monkeypatch.setattr(module, 'time', clock)
    for name in ('_READY', '_SELECTED_READY', '_LIFECYCLE_PENDING', '_NATIVE_VISIT_HINTS', '_SIGNALS'):
        monkeypatch.setattr(R, name, OrderedDict())
    for name in ('_ACTIVE_SELECTED', '_NATIVE_VISIT_TOKENS'):
        monkeypatch.setattr(R, name, {})
    monkeypatch.setattr(R, '_MAIN_PHASE_HISTORY', deque(maxlen=256))
    monkeypatch.setattr(R, '_MAIN_PHASE', dict(name='fixture', code=None, epoch=None, perf=None))
    monkeypatch.setattr(R, '_NATIVE_READY_EVENT', None)
    monkeypatch.setattr(R, '_LIFECYCLE_SINK', None)
    monkeypatch.setattr(H, 'COOLDOWNS', {})
    dispositions = []
    def record(result, disposition, reason, **_fields):
        dispositions.append((result.request_id, disposition, reason))
    monkeypatch.setattr(A, 'record_async_disposition', record)
    monkeypatch.setattr(H, '_log_async_commit', lambda *_a, **_kw: None)
    wait_results = []
    def terminal_wait(*_args, **kwargs):
        resolution = kwargs['_completed_async_resolution']
        assert resolution is not None and resolution['ai_decision']['action'] == 'WAIT'
        wait_results.append(resolution['original_result'].request_id)
    monkeypatch.setattr(H, '_handle_watching_state_impl', terminal_wait)

    code, item, venue, market = '034020', '034020_NX', 'NXT', 'PRE'
    band = N.C.cell_key(code, market, 50000)
    scope = (code, venue, item, market, '2026-10-15', band)
    bid = 'fixture_momentum'
    state = SimpleNamespace(generation='scope', ready=[],
        legacy=SimpleNamespace(turn=None, last=None, rows=[], segment_start=clock.time()))
    family = dict(schema='continuous_reversal_policy_v6', family_sha256='family',
        machine_cells={band: {'routes': {venue: dict(backend='union_v6',
            scope_execution_hash='scope', payload={'branches': [{'branch_id': bid}]})}}})
    monkeypatch.setattr(N, '_STATES', {scope: state})
    monkeypatch.setattr(N, '_CLAIMS', {})
    monkeypatch.setattr(N, '_FAMILY', family)
    monkeypatch.setattr(N, '_GENERATION', 'family')
    monkeypatch.setattr(N.R, '_STATES', {})
    monkeypatch.setattr(CURRENT, 'backend', lambda *_args: N)
    monkeypatch.setattr(POLICY, 'prepare', lambda **_kwargs: {'continuous_reversal': family})

    coordinator = A.ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    coordinator._preparation_executor.shutdown(wait=True)
    coordinator._preparation_executor = DeferredExecutor()
    wake = ControlledEvent(clock)
    coordinator.completion_event = coordinator.ai_dispatcher.completion_event = wake
    R.set_native_ready_event(wake)
    route = W.session_route(clock.time(), code)
    stock = dict(id=1, code=code, name='fixture', status='WATCHING', buy_qty=0,
        watch_origin=W.WATCH_ORIGIN, watch_admission_id='fixture-watch',
        watch_generation_id=W.generation_id(clock.time(), route), broker_route=venue,
        market_session_bucket=route['bucket'])
    ws = dict(curr=50000, quote_stale=False, context_stale=False,
        last_realtime_type_item={'0B': item, '0D': item}, market_session_bucket=route['bucket'],
        market_data_transport_epoch=1, last_realtime_type_ts={'0D': clock.time()},
        realtime_type_snapshots_by_route={'NX|nxt_only': {'0D': {
            'item': item, 'transport_epoch': 1, 'observed_epoch': clock.time()}}})
    requests = []

    def emit(seq):
        event_id = f'2026-10-15:NXT:NXT_PREMARKET:{code}:1:{seq}'
        event = dict(epoch=clock.time(), event_id=event_id, signal_id=event_id,
            native_epoch=1, native_sequence=seq, symbol=code, source_item=item,
            venue=venue, market=market, confirmation_price=50000, entry_ask=50000,
            branch_signals={bid: {'decision_phase': 'MOMENTUM_CROSS', 'event_id': event_id}})
        state.legacy.last = [clock.time(), 1, seq, 50000, 50000, 50000, 10, 1, True, item, 0]
        state.ready.append(dict(event=event, claimed=False, path_inputs={bid: {'fixture': True}}))
        R.record_native_ready(N, code, venue, item, market, clock.time())
        return event

    def visit():
        tokens = {}
        queue = R.prioritize_native_watches([stock], now=clock.time(), visit_tokens=tokens)
        assert queue[0] is stock
        R.record_main_phase('target_visit', code)
        R.acknowledge_native_watch_visit(stock, tokens.get(id(stock)), now=clock.time())

    def claim():
        return SOURCE.claim_snapshot_with_receipt(code, venue, market,
            now=clock.time(), item=item, family_sha256='family', live_clock=True)

    def start_old():
        old_event = emit(1)
        visit()
        old_claim = claim()
        generation = A.FixedWatchGeneration.from_claim(code, old_claim)
        context = A.ScannerAsyncEvalContext.create(generation=generation, cache_key='original',
            submitted_epoch=clock.time(), deadline_epoch=D.claim_deadline_epoch(old_claim),
            stock_snapshot={**stock, '_continuous_reversal_pending_claim': old_claim},
            ws_snapshot=ws, state_version=H._scanner_async_entry_state_version(stock))
        def forbidden(*_a, **_kw):
            pytest.fail('external preparation/provider work must not execute')
        request = A.ScannerAsyncEvalRequest(context=context, prepare=forbidden, evaluate=forbidden)
        assert coordinator.submit(request).accepted
        requests.append(request)
        stock.update(_fixed_watch_async_claim=deepcopy(old_claim),
            _continuous_reversal_pending_claim=deepcopy(old_claim),
            _scanner_async_generation_id=generation.generation_id,
            _scanner_async_cache_key=context.cache_key)
        assert coordinator.wait_for_completion(1.0)  # consume the original native wake
        return old_event, old_claim, request

    def finish(status, payload=None):
        request = requests[0]
        coordinator._finish(request, status=status,
            preparation_started_epoch=request.context.submitted_epoch,
            preparation_completed_epoch=clock.time(), completed_epoch=clock.time(),
            observation_only=status != 'completed', ai_payload=payload or {'action': 'WAIT'})

    def consume():
        notifications = coordinator.drain_completed()
        assert len(notifications) == 1
        visit()
        H.handle_watching_state(stock, code, ws, None, now_ts=clock.time(),
            scanner_async_eval_coordinator=coordinator, scanner_async_commit_phase=True)
        assert not coordinator.has_completed_result()
        assert '_fixed_watch_async_claim' not in stock
        assert '_scanner_async_generation_id' not in stock

    harness = SimpleNamespace(**locals())
    try:
        yield harness
    finally:
        R.set_native_ready_event(None)
        coordinator.shutdown()


@pytest.mark.parametrize('status', ['completed', 'preparation_error'])
@pytest.mark.parametrize('notification', ['before_wait', 'during_wait'])
def test_pending_successor_is_claimed_without_an_extra_idle_wait(lane, status, notification):
    old_event, old_claim, request = lane.start_old()
    lane.clock.advance(.1)
    successor = lane.emit(2)
    lane.visit()
    refresh = H._resolve_watching_state_change_refresh(lane.stock, lane.ws,
        now_ts=lane.clock.time(), last_ai_time=0, cooldown_sec=60)
    assert refresh['reason'] == 'fixed_watch_async_pending'
    assert not lane.state.ready[1]['claimed']
    assert lane.coordinator.is_pending(generation_id=request.context.generation.generation_id,
        cache_key=request.context.cache_key)
    assert lane.coordinator.wait_for_completion(1.0)  # consume successor's first wake while busy
    assert not lane.wake.is_set()
    lane.clock.advance(.2)
    if notification == 'before_wait':
        lane.finish(status)
    else:
        lane.wake.on_wait = lambda: lane.finish(status)
    assert lane.coordinator.wait_for_completion(1.0)
    lane.consume()
    if status == 'completed':
        assert lane.wait_results == [request.context.request_id]
        assert (request.context.request_id, 'accepted_to_entry_path', 'commit_allowed') in lane.dispositions
    else:
        assert lane.wait_results == []
        assert (request.context.request_id, 'rejected', 'result_not_commit_eligible') in lane.dispositions
    ready_at = lane.clock.time()

    # Main has visited this target in its completion pass. No new tick arrives.
    revisit = R.prioritize_native_watches([], now=ready_at,
        completed_requests=lane.coordinator.fixed_watch_ready_requests(), all_targets=[lane.stock],
        processed_target_ids={id(lane.stock)}, revisited_target_ids=set())
    if not revisit:
        lane.coordinator.wait_for_completion(1.0)
    lane.visit()
    refresh = H._resolve_watching_state_change_refresh(lane.stock, lane.ws,
        now_ts=lane.clock.time(), last_ai_time=0, cooldown_sec=60)
    assert refresh['allowed'] and refresh['event_id'] == successor['event_id']
    successor_claim = lane.stock['_continuous_reversal_pending_claim']
    assert successor_claim['token'] != old_claim['token']
    assert D.claim_deadline_epoch(successor_claim) == successor['epoch'] + 5
    assert D.claim_deadline_epoch(old_claim) == old_event['epoch'] + 5
    assert len(lane.requests) == 1 and all(r['claimed'] for r in lane.state.ready)
    assert len(lane.dispositions) >= 2
    delay = lane.clock.time() - ready_at
    assert delay == pytest.approx(0), (
        f'pending successor acquired only after {delay:.3f}s idle; '
        f'completion={status}, notification={notification}, '
        f'blocked_waits={lane.wake.blocked_seconds}')


def test_completion_cleanup_does_not_erase_a_successor_identity(lane):
    _, old_claim, request = lane.start_old()
    lane.clock.advance(.1)
    lane.emit(2)
    successor = lane.claim()
    lane.stock.update(_fixed_watch_async_claim=deepcopy(successor),
        _continuous_reversal_pending_claim=deepcopy(successor),
        _scanner_async_generation_id='fixed-watch:' + successor['token'],
        _scanner_async_cache_key='successor')
    before = deepcopy(lane.stock)
    H._clear_scanner_async_identity(lane.stock,
        generation_id=request.context.generation.generation_id,
        cache_key=request.context.cache_key, claim=old_claim)
    assert lane.stock == before


def test_expired_successor_cannot_receive_a_reset_deadline(lane):
    event = lane.emit(1)
    original = lane.claim()
    lane.clock.advance(5.001)
    with pytest.raises(ValueError, match='expired'):
        A.FixedWatchGeneration.from_claim(lane.code, original)
    assert D.claim_deadline_epoch(original) == event['epoch'] + 5
    assert D.EntryDeadline.create(original).remaining() == 0


def test_native_arrival_does_not_reorder_protected_or_drop_other_targets(lane):
    lane.emit(1)
    held = dict(code='005930', status='HOLDING')
    commit = dict(code='196170', status='WATCHING', _scanner_scheduler_lane='COMMIT')
    ordinary = dict(code='036930', status='WATCHING')
    targets = [held, ordinary, commit, lane.stock]
    ordered = R.prioritize_native_watches(targets, now=lane.clock.time())
    assert ordered == [held, lane.stock, commit, ordinary]
    assert {id(t) for t in ordered} == {id(t) for t in targets}


@pytest.mark.parametrize('blocked', ['absent', 'expired', 'perf_expired', 'terminal', 'claimed',
                                    'selector_claimed', 'generation', 'native_epoch', 'route'])
def test_completion_cannot_rearm_invalid_or_consumed_native_successor(lane, blocked):
    _, old_claim, _ = lane.start_old()
    if blocked != 'absent':
        lane.clock.advance(.1)
        event = lane.emit(2)
        lane.visit()
        row = next(row for row in R._SELECTED_READY.values() if row['signal_id'] == event['signal_id'])
        if blocked == 'expired':
            lane.clock.advance(5)
        elif blocked == 'perf_expired':
            lane.clock.perf += 5  # Backward wall clock cannot renew the budget.
        elif blocked == 'terminal':
            row['terminal'] = 'source_or_guard_blocked_before_claim'
        elif blocked in ('claimed', 'selector_claimed'):
            row[blocked] = True
        elif blocked == 'generation':
            row['scope_execution_hash'] = 'changed'
        elif blocked == 'native_epoch':
            row['native_epoch'] += 1
        elif blocked == 'route':
            old_claim['snapshot'][0]['venue'] = 'KRX'
    lane.wake.clear()
    assert not R.rearm_native_watch_after_completion(old_claim)
    assert not lane.wake.is_set() and not R._NATIVE_VISIT_HINTS


def test_completion_revisit_is_bounded_and_preserves_new_ingress_token(lane):
    _, old_claim, _ = lane.start_old()
    lane.clock.advance(.1)
    lane.emit(2)
    lane.visit()
    lane.wake.clear()
    assert R.rearm_native_watch_after_completion(old_claim)
    original_token = (R._NATIVE_VISIT_HINTS[lane.code], R._NATIVE_VISIT_TOKENS[lane.code])
    revisited = set()
    args = dict(now=lane.clock.time(), all_targets=[lane.stock],
                processed_target_ids={id(lane.stock)}, revisited_target_ids=revisited)
    assert R.prioritize_native_watches([], **args) == [lane.stock]
    assert R.prioritize_native_watches([], **args) == []
    lane.clock.advance(.1)
    lane.emit(3)
    newer_token = (R._NATIVE_VISIT_HINTS[lane.code], R._NATIVE_VISIT_TOKENS[lane.code])
    assert newer_token != original_token
    assert R.rearm_native_watch_after_completion(old_claim)
    R.acknowledge_native_watch_visit(lane.stock, original_token, now=lane.clock.time())
    assert (R._NATIVE_VISIT_HINTS[lane.code], R._NATIVE_VISIT_TOKENS[lane.code]) == newer_token


@pytest.mark.parametrize('successor_owner', ['holding', 'commit', 'successor'])
def test_completion_wrapper_does_not_revisit_holding_or_successor_owner(lane, monkeypatch, successor_owner):
    lane.start_old()
    lane.clock.advance(.1)
    lane.emit(2)
    lane.visit()
    lane.finish('completed')
    lane.coordinator.drain_completed()
    lane.wake.clear()
    def consumed(stock, *args, **kwargs):
        if successor_owner == 'successor':
            stock.update(_fixed_watch_async_claim={'token': 'successor'},
                         _scanner_async_generation_id='new-generation', _scanner_async_cache_key='new-key')
        elif successor_owner == 'commit':
            stock['_scanner_scheduler_lane'] = 'COMMIT'
        else:
            stock['status'] = 'HOLDING'
    monkeypatch.setattr(H, '_handle_watching_state_impl', consumed)
    H.handle_watching_state(lane.stock, lane.code, lane.ws, None, now_ts=lane.clock.time(),
        scanner_async_eval_coordinator=lane.coordinator, scanner_async_commit_phase=True)
    assert not lane.wake.is_set() and not R._NATIVE_VISIT_HINTS
    if successor_owner == 'successor':
        assert lane.stock['_fixed_watch_async_claim']['token'] == 'successor'
        assert lane.stock['_scanner_async_generation_id'] == 'new-generation'


def _complete_unsent_pass(lane, monkeypatch, *, protect=None):
    """Use real Main completion and submit observer; no broker/provider call."""
    from src.engine.monitoring.entry_attempt_identity import observe_submit_attempt
    monkeypatch.setattr(H, '_log_entry_pipeline', lambda *_a, **_kw: None)
    old_event, old_claim, request = lane.start_old()
    lane.clock.advance(.1)
    successor = lane.emit(2)
    lane.visit()  # New native signal first visits while the old request is pending.
    assert lane.coordinator.wait_for_completion(1.0)
    payload = dict(action='BUY', evaluation_attempt_id='original-evaluation',
        ai_decision_trace_id='original-trace', entry_mechanistic_policy_version='continuous_reversal_policy_v6')

    @observe_submit_attempt(on_finish=H._observe_entry_submit_finished)
    def guarded_submit(stock, code):
        H._set_async_terminal(stock, 'real_weak_pullback_entry_block')
        return False

    def accepted_path(stock, code, *_a, **kwargs):
        assert kwargs['_completed_async_resolution']['ai_decision']['action'] == 'BUY'
        stock['last_watching_ai_machine_primary_fields'] = deepcopy(payload)
        stock['last_watching_ai_decision_trace_id'] = payload['ai_decision_trace_id']
        H._activate_entry_arm(stock, code, ai_score=75, ratio=.1, target_buy_price=50000,
            current_vpw=100, reason='fixture', dynamic_reason='fixture')
        guarded_submit(stock, code)
        if protect:
            protect(stock, stock['_async_consumption_guard'])
    monkeypatch.setattr(H, '_handle_watching_state_impl', accepted_path)
    lane.finish('completed', payload)
    lane.consume()
    return old_event, old_claim, request, successor


def test_unsent_native_pass_releases_arm_before_first_successor_revisit(lane, monkeypatch):
    old_event, old_claim, request, successor = _complete_unsent_pass(lane, monkeypatch)
    assert not lane.stock.get('entry_armed')
    assert lane.stock['_async_entry_decision_deadline']['request_id'] == request.context.request_id
    assert lane.stock['last_watching_ai_decision_trace_id'] == 'original-trace'
    ready_at = lane.clock.time()
    revisit = R.prioritize_native_watches([], now=ready_at, all_targets=[lane.stock],
        processed_target_ids={id(lane.stock)}, revisited_target_ids=set())
    assert revisit == [lane.stock]
    lane.visit()
    assert H._get_live_entry_arm(lane.stock, lane.code) is None
    refresh = H._resolve_watching_state_change_refresh(lane.stock, lane.ws,
        now_ts=lane.clock.time(), last_ai_time=0, cooldown_sec=60)
    assert refresh['allowed'] and refresh['event_id'] == successor['event_id']
    assert D.claim_deadline_epoch(lane.stock['_continuous_reversal_pending_claim']) == successor['epoch'] + 5
    assert D.claim_deadline_epoch(old_claim) == old_event['epoch'] + 5
    assert lane.clock.time() == ready_at and not lane.wake.blocked_seconds
    assert len(lane.requests) == 1  # Never restart or resend the old provider request.


@pytest.mark.parametrize('protection', [
    'delay_pending', 'delay_due', 'bundle', 'open_order', 'partial_order', 'sent_order',
    'buy_qty', 'entry_filled_qty', 'holding_qty', 'status', 'broker_attempt',
    'broker_accepted', 'unknown_outcome', 'missing_attempt', 'exception',
    'successor_request', 'successor_evaluation', 'successor_trace', 'missing_owner_id',
])
def test_completion_retains_delayed_or_uncertain_custody_and_successor_arm(lane, monkeypatch, protection):
    def protect(stock, guard):
        if protection.startswith('delay_'):
            stock['_pre_submit_delay_' + protection.split('_')[1]] = {'id': 'retained'}
        elif protection == 'bundle':
            stock['initial_quantity_bundle'] = {'state': 'intent_assigned'}
        elif protection.endswith('_order'):
            stock['pending_entry_orders'] = [{'status': protection.split('_')[0].upper()}]
        elif protection in ('buy_qty', 'entry_filled_qty', 'holding_qty'):
            stock[protection] = 1
        elif protection == 'status':
            stock['status'] = 'HOLDING'
        elif protection == 'broker_attempt':
            guard['async_entry_broker_attempts'] = 1
        elif protection == 'broker_accepted':
            guard['async_entry_broker_accepted'] = True
        elif protection == 'unknown_outcome':
            guard['async_entry_submit_outcome'] = 'raised'
        elif protection == 'missing_attempt':
            guard.pop('async_entry_submit_attempt_id')
        elif protection == 'exception':
            guard['reason'] = 'entry_execution_exception_or_uncertain'
        else:
            key = dict(successor_request='request_id', successor_evaluation='evaluation_attempt_id',
                successor_trace='ai_decision_trace_id', missing_owner_id='request_id')[protection]
            stock['_entry_arm_native_owner'][key] = '' if protection == 'missing_owner_id' else 'successor'
    _complete_unsent_pass(lane, monkeypatch, protect=protect)
    assert lane.stock['entry_armed']


def test_arm_cleanup_failure_does_not_strand_completion_or_native_pending(lane, monkeypatch):
    def broken(*_a):
        raise ValueError('fixture_arm_failure')
    monkeypatch.setattr(H, '_retire_completed_native_entry_arm', broken)
    _complete_unsent_pass(lane, monkeypatch)
    assert lane.stock['entry_armed']
    assert not lane.stock.get('_scanner_async_generation_id')
    assert lane.wake.is_set()


def test_completed_pass_is_not_reused_when_successor_source_is_absent(lane, monkeypatch):
    _complete_unsent_pass(lane, monkeypatch)
    # The next tick/source is absent; old PASS must not fall through to cached BUY.
    lane.state.ready.clear()
    refresh = H._resolve_watching_state_change_refresh(lane.stock, lane.ws,
        now_ts=lane.clock.time(), last_ai_time=0, cooldown_sec=60)
    assert refresh['suppress_normal_refresh']
    assert refresh['reason'] == 'completed_entry_decision_wait_native_signal'
    assert lane.stock['last_watching_ai_machine_primary_fields']['action'] == 'BUY'
    successor = lane.emit(3)
    refresh = H._resolve_watching_state_change_refresh(lane.stock, lane.ws,
        now_ts=lane.clock.time(), last_ai_time=0, cooldown_sec=60)
    assert refresh['allowed'] and refresh['event_id'] == successor['event_id']
    assert D.claim_deadline_epoch(lane.stock['_continuous_reversal_pending_claim']) == successor['epoch'] + 5
