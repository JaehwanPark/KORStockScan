"""Local latency repairs retain request ownership, durability and native guards."""
import copy
import json
import os
import threading
import time
from collections import OrderedDict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from contextlib import contextmanager
from types import SimpleNamespace
from pathlib import Path

import pytest

from src.engine.monitoring import runtime_performance as R
from src.engine.infrastructure.snapshot_copy import snapshot_without_fields
from src.engine.ai_engine_openai import (
    GPTSniperEngine, OpenAIResponseRequest, OpenAITransportObservation,
    OpenAIHTTPWallClockDeadlineError,
)


def request(**changes):
    return OpenAIResponseRequest(**dict(dict(prompt='fixture', user_input='{}', require_json=True,
        context_name='fixture', model_name='gpt-5.4-nano', temperature=None,
        schema_name='entry_v1', endpoint_name='analyze_target', request_id='request',
        symbol='034020', cache_key='key', submitted_at_perf=time.perf_counter(), timeout_ms=100,
        response_schema_override={'type': 'object', 'properties': {'action': {'type': 'string'}},
                                  'required': ['action'], 'additionalProperties': False}), **changes))


def test_discarded_diagnostic_is_not_copied_but_cycles_and_operating_aliases_are():
    class Discarded:
        def __deepcopy__(self, memo):
            raise AssertionError('discarded diagnostics must not be traversed')
    shared = {'rows': deque([{'price': 1}], maxlen=10)}
    source = {'first': shared, 'second': shared, '_machine_observation_revision': Discarded()}
    source['self'] = source
    owned = snapshot_without_fields(source, ('_machine_observation_revision',))
    assert owned['self'] is owned
    assert owned['first'] is owned['second'] and owned['first'] is not shared
    owned['first']['rows'][0]['price'] = 2
    assert shared['rows'][0]['price'] == 1
    assert owned['first']['rows'].maxlen == 10
    assert '_machine_observation_revision' not in owned


@pytest.mark.parametrize('change', ['prompt', 'user_input', 'model_name', 'metadata', 'schema', 'tokens'])
def test_explicit_wire_cache_preserves_bytes_and_invalidates_all_provider_inputs(change):
    current = request()
    first = current.build_provider_payload(use_schema_registry=True)
    assert first == current._build_provider_payload(use_schema_registry=True)
    first['text']['format']['schema']['properties']['action']['type'] = 'number'
    assert current.build_provider_payload(use_schema_registry=True) == current._build_provider_payload(use_schema_registry=True)
    if change == 'schema':
        current.response_schema_override['properties']['action']['enum'] = ['WAIT']
    elif change == 'tokens':
        current.max_output_tokens = 512
    else:
        setattr(current, change, {'scope': 'changed'} if change == 'metadata' else 'changed')
    assert current.build_provider_payload(use_schema_registry=True) == current._build_provider_payload(use_schema_registry=True)
    successor = replace(current, user_input='{"changed":true}')
    assert successor._entry_payload_cache is None
    assert successor.build_provider_payload(use_schema_registry=True)['input'] != current.build_provider_payload(use_schema_registry=True)['input']


def test_generic_request_schema_has_no_new_process_lifetime_cache():
    current = request(response_schema_override=None)
    current.build_provider_payload(use_schema_registry=False)
    assert current._entry_payload_cache is None


def test_native_hints_preserve_protected_positions_and_full_fairness_population(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('034020', 101.), ('069640', 102.)]))
    targets = [dict(code='held', status='HOLDING'), dict(code='slow', status='WATCHING'),
        dict(code='commit', status='WATCHING', _scanner_scheduler_lane='COMMIT'),
        dict(code='069640', status='WATCHING'), dict(code='sold', status='SELL_ORDERED'),
        dict(code='034020', status='WATCHING'), dict(code='other', status='WATCHING')]
    actual = R.prioritize_native_watches(targets, now=103.)
    assert [t['code'] for t in actual] == ['held', '034020', 'commit', '069640', 'sold', 'slow', 'other']
    assert {id(t) for t in actual} == {id(t) for t in targets}
    assert [t['code'] for t in targets] == ['held', 'slow', 'commit', '069640', 'sold', '034020', 'other']
    assert not R._NATIVE_VISIT_HINTS
    assert R.prioritize_native_watches(targets, now=104.) is targets


def test_expired_or_closed_hint_never_creates_a_new_visit_lease(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('034020', 1.)]))
    targets = [dict(code='slow', status='WATCHING'), dict(code='034020', status='WATCHING')]
    assert R.prioritize_native_watches(targets, now=8.) is targets
    R._NATIVE_VISIT_HINTS['034020'] = 8.
    R.set_native_ready_event(None)
    assert not R._NATIVE_VISIT_HINTS


def test_stage_frame_is_attempt_local_and_exception_does_not_change_reserve(monkeypatch):
    clock = [0.]
    monkeypatch.setattr(R.time, 'perf_counter', lambda: clock[0])
    before = R.response_reserve()
    with R.entry_timing_frame() as outer:
        with R.entry_stage('entry_annotation'):
            clock[0] += .4
            with R.entry_timing_frame() as inner:
                with pytest.raises(ValueError), R.entry_stage('entry_error_processing'):
                    clock[0] += .1
                    raise ValueError('fixture')
        assert set(inner) == {'entry_error_processing'}
        assert set(outer) == {'entry_annotation'}
    assert R.entry_timings() == {}
    assert R.response_reserve() == before


def test_optional_metric_failure_does_not_replace_provider_or_owner_result(monkeypatch):
    monkeypatch.setattr(R, '_ENTRY_TIMING_GAPS', 0)
    monkeypatch.setattr(R, 'observe', lambda *a, **k: (_ for _ in ()).throw(ValueError('metrics unavailable')))
    with R.entry_timing_frame():
        assert R.timed_entry_call('entry_wire', lambda: {'action': 'WAIT'}) == {'action': 'WAIT'}
    assert R._ENTRY_TIMING_GAPS == 1


def test_new_wakeup_namespace_clears_old_hints(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('034020', 1.)]))
    monkeypatch.setattr(R, '_NATIVE_READY_EVENT', threading.Event())
    R.set_native_ready_event(threading.Event())
    assert not R._NATIVE_VISIT_HINTS


def test_health_wait_is_as_of_check_not_fresh_heartbeat_copy(monkeypatch, tmp_path):
    from src.engine.error_detectors import process_health as H
    now = time.time()
    ticks = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
    path = tmp_path/'heartbeat.json'
    receipt = dict(pid=os.getpid(), process_start_ticks=ticks, snapshot_epoch=now, state='enabled',
        entry_transport=dict(state='OPEN', recovery_wait_seconds=30.,
                             recovery_wait_observed_epoch=now-20, recovery_next_eligible_epoch=now+10))
    path.write_text(json.dumps({'ai_circuit': receipt}))
    monkeypatch.setattr(H, 'HEARTBEAT_PATH', path)
    result = H._current_ai_circuit_health(os.getpid(), now)
    assert result['status'] == 'blocked'
    assert result['entry_observation_age_seconds'] == 20
    assert result['recovery_wait_estimate_seconds_as_of_check'] == 10
    assert result['receipt']['entry_transport']['recovery_wait_seconds'] == 30
    assert result['automatic_recovery_forbidden'] is True
    assert result['recovery_wait_estimate_is_admission_authority'] is False


def test_failed_ancestor_recheck_cannot_retain_configuration_receipt(monkeypatch):
    from src.engine.scalping import reversal_evaluation_context as E
    @contextmanager
    def invalid_pass():
        yield
        raise ValueError('ancestor changed')
    monkeypatch.setattr(E.N, 'signature_pass', invalid_pass)
    monkeypatch.setattr(E, '_CONFIGURED', 'invalid')
    monkeypatch.setattr(E, '_CONSUMED', 'invalid')
    monkeypatch.setattr(E, '_prepare_verified', lambda **kw: {'bundle': 'fixture'})
    with pytest.raises(ValueError, match='ancestor changed'):
        E.prepare(data_root='unused', day='2026-10-13')
    assert E._CONFIGURED is None and E._CONSUMED is None


def test_native_predecessor_proof_change_invalidates_the_consumption_dependencies(tmp_path):
    from src.engine.scalping import reversal_evaluation_context as E
    day, commit = '2026-10-13', 'a' * 40
    proof = tmp_path/'runtime/release_transitions'/day/commit/'native-predecessor.json'
    proof.parent.mkdir(parents=True); proof.write_text('{"verified":true}')
    before = proof.parent/'selection-before.json';before.write_text('{"generation":1}')
    paths=E._extra_paths(tmp_path,day,commit)
    identities=E._identities(paths)
    assert str(proof) in identities and str(before) in identities
    proof.write_text('{"verified":false}')
    assert E._identities(paths)!=identities
    proof.unlink()
    assert E._identities(paths)[str(proof)] is None


def test_timeout_does_not_invent_sdk_end_and_late_settlement_is_diagnostic_only(monkeypatch):
    monkeypatch.setattr(R, '_HTTP_SETTLEMENTS', deque(maxlen=128))
    entered, release = threading.Event(), threading.Event()
    def create(**kwargs):
        entered.set()
        assert release.wait(2)
        return 'response'
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    engine._http_deadline_executor = ThreadPoolExecutor(max_workers=1)
    observation = OpenAITransportObservation()
    current = request(timeout_ms=30, transport_observation=observation)
    try:
        with pytest.raises(OpenAIHTTPWallClockDeadlineError) as error:
            engine._create_openai_response_with_deadline(current, provider_payload={})
        assert entered.is_set() and error.value.future_cancelled is False
        phases = observation.fields()['provider_stage_monotonic']
        assert 'sdk_started' in phases and 'sdk_finished' not in phases
        assert 'caller_adapter_finished' in phases
        assert not R._HTTP_SETTLEMENTS
    finally:
        release.set()
        engine._http_deadline_executor.shutdown(wait=True)
    phases = observation.fields()['provider_stage_monotonic']
    assert phases['sdk_finished'] > phases['caller_adapter_finished']
    assert phases['future_settled'] >= phases['sdk_finished']
    row = R._HTTP_SETTLEMENTS[-1]
    assert row['request_id'] == 'request' and row['decision_authority'] == 'none'
    assert row['stage_monotonic']['sdk_finished'] > phases['caller_adapter_finished']


def test_executor_queue_clock_excludes_local_warmup_bookkeeping(monkeypatch):
    monkeypatch.setattr(R, '_HTTP_SETTLEMENTS', deque(maxlen=128))
    clocks = {}
    def activity(client):
        clocks['warmup_finished'] = time.perf_counter()
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: 'response'))
    engine._transport_warmup = SimpleNamespace(note_activity=activity)
    engine._http_deadline_executor = ThreadPoolExecutor(max_workers=1)
    try:
        assert engine._create_openai_response_with_deadline(
            request(transport_observation=OpenAITransportObservation()), provider_payload={}) == 'response'
    finally:
        engine._http_deadline_executor.shutdown(wait=True)
    settled = R._HTTP_SETTLEMENTS[-1]['stage_monotonic']
    assert clocks['warmup_finished'] <= settled['executor_enqueued'] <= settled['executor_started']
