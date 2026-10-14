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


@pytest.mark.parametrize('version', ['v5', 'v6'])
@pytest.mark.parametrize('failure', [None, 'model', 'claim', 'changed_refs', 'auxiliary', 'exit'])
def test_final_native_boundary_keeps_all_guards_and_closes_before_provider(monkeypatch, version, failure):
    from src.engine.scalping import reversal_evaluation_context as E
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_intraday as I
    V = __import__('src.engine.scalping.continuous_reversal_policy_' + version, fromlist=['unused'])
    calls = []
    active = E.N._freeze({'bundle_sha256': 'a' * 64, 'nested': {'policy': ['original']}})
    policy = {'continuous_reversal_assessment': {
        'policy_version': 'continuous_reversal_policy_' + version,
        'auxiliary_registry_sha256': 'b' * 64, 'matched_policy_refs': ['original']}}
    @contextmanager
    def view(**kwargs):
        assert E.N._SIGNATURE_PASS.get() is not None
        calls.append('load')
        try:
            yield active
        finally:
            calls.append('exit')
            if failure == 'exit':
                raise ValueError('pointer changed')
    def registry(*args):
        calls.append('model')
        return {'model': 'changed' if failure == 'model' else 'gpt-5.4-nano'}
    def claim(actual_policy, actual_bundle, *, now):
        assert actual_policy is policy and actual_bundle is active
        with pytest.raises(TypeError):
            actual_bundle['nested']['policy'].append('mutated')
        calls.append('claim')
        if failure == 'claim':
            raise ValueError('reversal_signal_expired_or_changed')
        return ['changed'] if failure == 'changed_refs' else ['original']
    def auxiliary(root, actual_policy, actual_bundle, *, now):
        assert actual_policy is policy and actual_bundle is active
        calls.append('auxiliary')
        if failure == 'auxiliary':
            raise ValueError('auxiliary_decision_generation_revoked')
    monkeypatch.setattr(E.N, 'verified_evaluation', view)
    monkeypatch.setattr(G, 'load', registry)
    monkeypatch.setattr(V, 'validate_active_claim', claim)
    monkeypatch.setattr(I, 'validate_decision', auxiliary)
    with R.entry_timing_frame() as frame:
        if failure:
            with pytest.raises(ValueError):
                E.validate_before_provider(policy, data_root='fixture', model='gpt-5.4-nano')
        else:
            assert E.validate_before_provider(policy, data_root='fixture', model='gpt-5.4-nano') == ['original']
        assert 'entry_native_load' in frame
    assert calls[0:2] == ['load', 'model'] and calls[-1] == 'exit'
    assert ('claim' in calls) == (failure != 'model')
    assert ('auxiliary' in calls) == (failure not in {'model', 'claim', 'changed_refs'})
    assert E.N._SIGNATURE_PASS.get() is None and E.N._VERIFIED_EVALUATION.get() is None



def request(**changes):
    return OpenAIResponseRequest(**dict(dict(prompt='fixture', user_input='{}', require_json=True,
        context_name='fixture', model_name='gpt-5.4-nano', temperature=None,
        schema_name='entry_v1', endpoint_name='analyze_target', request_id='request',
        symbol='034020', cache_key='key', submitted_at_perf=time.perf_counter(), timeout_ms=100,
        response_schema_override={'type': 'object', 'properties': {'action': {'type': 'string'}},
                                  'required': ['action'], 'additionalProperties': False}), **changes))


@pytest.mark.parametrize('damage', [None, 'scope', 'backend', 'expired', 'path', 'unrequested'])
def test_prepared_native_claim_matches_original_dynamic_validator(monkeypatch, tmp_path, damage):
    from src.engine.scalping import reversal_evaluation_context as E
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_current_backend as D
    bid = 'legacy_dd5_ge_0_4_v1'
    family = {'schema': V.SCHEMA, 'family_sha256': 'a' * 64, 'machine_cells': {
        'scope': {'routes': {'SOR': {'scope_execution_hash': 'b' * 64, 'backend': 'union_v6'}}}}}
    if damage == 'backend': family['machine_cells']['scope']['routes']['SOR']['backend'] = 'registered_v4'
    active = E.N._freeze({'bundle_sha256': 'c' * 64, 'continuous_reversal': family})
    policy = {'continuous_reversal_claim': {'token': 'native'}, 'continuous_reversal_assessment': {
        'policy_version': V.SCHEMA, 'cell_key': 'scope', 'route': 'SOR',
        'scope_execution_hash': ('0' if damage == 'scope' else 'b') * 64,
        'matched_policy_refs': [] if damage == 'unrequested' else [bid + ':' + V.A.definition_hash(bid)]}}
    calls = []
    def native(claim, sha, *, now):
        calls.append('native')
        assert claim is policy['continuous_reversal_claim'] and sha == family['family_sha256']
        if damage in {'expired', 'path'}:
            raise ValueError('reversal_signal_expired_or_changed' if damage == 'expired' else 'reversal_signal_path_changed')
        return ({'branch_signals': {bid: {}}}, {})
    monkeypatch.setattr(V, 'validate_family', lambda f: calls.append('static'))
    monkeypatch.setattr(D, 'configure_bundle', lambda *a, **kw: calls.append('configure'))
    monkeypatch.setattr(D, 'validate_any_claim', native)
    monkeypatch.setattr(D, 'backend', lambda: SimpleNamespace(_GENERATION=family['family_sha256']))
    monkeypatch.setattr(E, '_CONFIGURED', ('verified', active))
    monkeypatch.setattr(E, '_CONSUMED', ('verified', active, {}, {}))
    monkeypatch.setattr(E, 'prepare', lambda **kw: calls.append('fresh_sources_and_pid') or active)
    def result(fn):
        try: return ('pass', fn())
        except ValueError as exc: return ('fail', str(exc))
    expected = result(lambda: V.validate_active_claim(policy, active, now=1000.))
    assert 'static' in calls
    calls.clear()
    token = E.N._VERIFIED_EVALUATION.set((str(tmp_path.absolute()), '2026-10-13', active, 'pointer'))
    try:
        actual = result(lambda: E._prepared_v6_claim(policy, active, data_root=tmp_path, day='2026-10-13'))
    finally: E.N._VERIFIED_EVALUATION.reset(token)
    assert actual == expected and 'fresh_sources_and_pid' in calls
    assert 'static' not in calls and 'configure' not in calls


@pytest.mark.parametrize('damage', ['mutable', 'no_view', 'different_view', 'no_configuration', 'no_consumption'])
def test_unverified_native_configuration_never_uses_the_fast_path(monkeypatch, tmp_path, damage):
    from src.engine.scalping import reversal_evaluation_context as E
    active = E.N._freeze({'bundle_sha256': 'a' * 64})
    if damage == 'mutable': active = dict(active)
    monkeypatch.setattr(E, '_CONFIGURED', None if damage == 'no_configuration' else ('key', active))
    monkeypatch.setattr(E, '_CONSUMED', None if damage == 'no_consumption' else ('key', active, {}, {}))
    monkeypatch.setattr(E, 'prepare', lambda **kw: pytest.fail('No unchecked preparation'))
    view = None if damage == 'no_view' else (str(tmp_path.absolute()), '2026-10-13', {} if damage == 'different_view' else active, 'pointer')
    token = E.N._VERIFIED_EVALUATION.set(view)
    try: assert E._prepared_v6_claim({}, active, data_root=tmp_path, day='2026-10-13') is None
    finally: E.N._VERIFIED_EVALUATION.reset(token)


@pytest.mark.parametrize('appended', [True, False])
def test_action_snapshot_references_only_successful_canonical_economic_append(monkeypatch, appended):
    from src.engine import sniper_state_handlers as H
    emitted = []
    monkeypatch.setattr(H, '_log_entry_pipeline', lambda *a, **kw: emitted.append((a[2], kw)))
    body = {'loaded_code': 'same frozen code' * 10000}
    decision = {'action': 'WAIT', 'score': 50, 'evaluation_attempt_id': 'exact',
        'machine_observation_sha256': 'm', 'ai_decision_trace_id': 'trace',
        'entry_economic_conditional_seed': body, 'entry_economic_operating_context': body,
        'entry_pre_ai_source_append_receipt': {'structured_append_succeeded': appended, 'capsule_sha256': 'a' * 64}}
    H._emit_scalp_entry_adm_snapshot({'id': 1, 'name': 'TEST', 'strategy': 'SCALPING'}, '005930',
                                   'ai_confirmed', ai_decision=decision)
    fields = emitted[-1][1]
    assert ('entry_economic_conditional_seed' in fields) is not appended
    assert ('entry_economic_operating_context' in fields) is not appended
    assert decision['entry_economic_operating_context'] is body  # Canonical input never mutated.
    if appended:
        assert fields['entry_economic_payload_reference']['evaluation_attempt_id'] == 'exact'
        assert fields['entry_economic_payload_reference']['capsule_sha256'] == 'a' * 64


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
    tokens = {}
    actual = R.prioritize_native_watches(targets, now=103., visit_tokens=tokens)
    assert [t['code'] for t in actual] == ['held', '034020', 'commit', '069640', 'sold', 'slow', 'other']
    assert {id(t) for t in actual} == {id(t) for t in targets}
    assert [t['code'] for t in targets] == ['held', 'slow', 'commit', '069640', 'sold', '034020', 'other']
    assert len(R._NATIVE_VISIT_HINTS) == 2
    R.acknowledge_native_watch_visit(actual[1], tokens[id(actual[1])], now=103.)
    assert set(R._NATIVE_VISIT_HINTS) == {'069640'}
    # Sorting one target cannot lose another target's pending notification.
    assert R.prioritize_native_watches(targets[2:], now=103.)[1]['code'] == '069640'
    R.acknowledge_native_watch_visit(actual[3], tokens[id(actual[3])], now=103.)
    assert R.prioritize_native_watches(targets, now=104.) is targets


def test_new_hint_between_selection_and_actual_visit_is_retained(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('005930', 100.)]))
    monkeypatch.setattr(R, '_NATIVE_VISIT_TOKENS', {'005930': 7})
    target = dict(code='005930', status='WATCHING')
    tokens = {}
    R.prioritize_native_watches([target], now=101., visit_tokens=tokens)
    # Even equal wall timestamps in a successor generation have a new token.
    R._NATIVE_VISIT_TOKENS['005930'] = 8
    R.acknowledge_native_watch_visit(target, tokens[id(target)], now=101.)
    assert R._NATIVE_VISIT_HINTS['005930'] == 100.
    R.prioritize_native_watches([target], now=101., visit_tokens=tokens)
    R.acknowledge_native_watch_visit(target, tokens[id(target)], now=101.)
    assert not R._NATIVE_VISIT_HINTS and not R._NATIVE_VISIT_TOKENS


def test_native_signal_after_ordinary_visit_reenters_once_without_displacing_protected_work(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('005930', 100.)]))
    monkeypatch.setattr(R, '_NATIVE_VISIT_TOKENS', {'005930': 1})
    ready = dict(code='005930', status='WATCHING')
    held = dict(code='held', status='HOLDING')
    commit = dict(code='commit', status='WATCHING', _scanner_scheduler_lane='COMMIT')
    ordinary = dict(code='other', status='WATCHING')
    all_targets = [ready, held, commit, ordinary]
    visited, revisited = {id(ready)}, set()
    queue = [held, commit, ordinary]
    tokens = {}
    actual = R.prioritize_native_watches(queue, now=100.1, all_targets=all_targets,
        processed_target_ids=visited, revisited_target_ids=revisited, visit_tokens=tokens)
    assert actual == [held, commit, ready, ordinary]
    assert len(actual) == 4 and revisited == {id(ready)}
    R.acknowledge_native_watch_visit(ready, tokens[id(ready)], now=100.1)
    R._NATIVE_VISIT_HINTS['005930'] = 100.2
    R._NATIVE_VISIT_TOKENS['005930'] = 2
    # A continuing ingress stream cannot starve the ordinary target forever.
    assert R.prioritize_native_watches([ordinary], now=100.3, all_targets=all_targets,
        processed_target_ids=visited, revisited_target_ids=revisited) == [ordinary]
    # A fresh outer pass can consume this still-original eligible hint.
    assert R.prioritize_native_watches([], now=100.3, all_targets=all_targets,
        processed_target_ids=visited, revisited_target_ids=set()) == [ready]


def test_transport_budget_facts_use_the_actual_sample_and_do_not_extend_deadline(monkeypatch):
    from src.engine.scalping.entry_deadline import EntryDeadline
    from src.engine.scalping import entry_deadline as D
    monkeypatch.setattr(D.time, 'time', lambda: 104.)
    monkeypatch.setattr(D.time, 'perf_counter', lambda: 204.)
    deadline = EntryDeadline(105., 205.)
    facts = {}
    assert deadline.transport_ms(5000, reserve_sec=.223, facts=facts) == 777
    assert facts['budget_before_transport_ms'] == 1000.
    assert facts['response_reserve_ms'] == 223.
    assert facts['timeout_override_ms'] == 777
    assert facts['original_deadline_perf'] == 205.
    monkeypatch.setattr(D.time, 'perf_counter', lambda: 205.)
    with pytest.raises(ValueError, match='entry_machine_input_deadline_expired'):
        deadline.transport_ms(5000, facts=facts)
    assert facts['timeout_override_ms'] == 0


def test_transport_observation_keeps_budget_and_sdk_remaining_separate_from_caller_return():
    observation = OpenAITransportObservation()
    observation.record_budget(dict(timeout_override_ms=777, response_reserve_ms=100))
    observation.mark('executor_enqueued', remaining_sec=.765)
    observation.mark('sdk_started', remaining_sec=.764)
    observation.mark('caller_adapter_finished')
    fields = observation.fields()
    assert fields['provider_deadline_budget']['timeout_override_ms'] == 777
    assert fields['provider_stage_remaining_ms']['sdk_started'] == 764.
    assert 'sdk_finished' not in fields['provider_stage_monotonic']
    assert fields['provider_response_received'] is False
    assert fields['provider_physical_transmission'] == 'unknown'


def test_expired_or_closed_hint_never_creates_a_new_visit_lease(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('034020', 1.)]))
    targets = [dict(code='slow', status='WATCHING'), dict(code='034020', status='WATCHING')]
    assert R.prioritize_native_watches(targets, now=8.) is targets
    R._NATIVE_VISIT_HINTS['034020'] = 8.
    R.set_native_ready_event(None)
    assert not R._NATIVE_VISIT_HINTS


def test_retained_fixed_result_precedes_other_watches_without_moving_protected_work(monkeypatch):
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict([('native', 102.)]))
    targets = [dict(code='holding', status='HOLDING'),
        dict(code='ordinary', status='WATCHING'),
        dict(code='commit', status='WATCHING', _scanner_scheduler_lane='COMMIT'),
        dict(code='native', status='WATCHING'), dict(code='order', status='BUY_ORDERED'),
        dict(code='ready', status='WATCHING', _scanner_async_generation_id='g',
             _scanner_async_cache_key='k'), dict(code='other', status='WATCHING')]
    actual = R.prioritize_native_watches(targets, now=103., completed_requests={('g', 'k'): 50.})
    assert [t['code'] for t in actual] == ['holding', 'ready', 'commit', 'native', 'order', 'ordinary', 'other']
    assert {id(t) for t in actual} == {id(t) for t in targets}
    assert targets[5]['_scanner_async_generation_id'] == 'g'
    # A result from another request cannot move the same symbol forward.
    monkeypatch.setattr(R, '_NATIVE_VISIT_HINTS', OrderedDict())
    assert R.prioritize_native_watches(targets, now=103., completed_requests={('g', 'successor'): 50.}) is targets


def test_same_process_ready_guard_clock_keeps_worker_to_poll_delay(monkeypatch):
    observed=[]
    monkeypatch.setattr(R, 'observe', lambda name, seconds: observed.append((name, seconds)))
    result=SimpleNamespace(coordinator_ready_perf=12., ai_payload={
        'entry_local_stage_clocks': {'async_evaluation_completed_perf': 10.}})
    fields=R.observe_async_main_guard(result, now_perf=12.25)
    assert fields['async_coordinator_ready_to_main_guard_ms'] == 250.
    assert fields['async_evaluation_to_coordinator_ready_ms'] == 2000.
    assert fields['async_evaluation_to_main_guard_ms'] == 2250.
    assert observed == [('coordinator_ready_to_main_guard', .25)]
    assert R.observe_async_main_guard(SimpleNamespace(coordinator_ready_perf=0.), now_perf=12.) == {}
    assert R.observe_async_main_guard(result, now_perf=11.) == {}


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
    remaining = row['transport_facts']['provider_stage_remaining_ms']
    assert 0 < remaining['sdk_started'] <= remaining['executor_enqueued'] <= 30


def test_optional_transport_observation_can_disappear_before_settlement(monkeypatch):
    monkeypatch.setattr(R, '_HTTP_SETTLEMENTS', deque(maxlen=128))
    entered, release = threading.Event(), threading.Event()
    def create(**kwargs):
        entered.set()
        assert release.wait(2)
        return 'response'
    engine = GPTSniperEngine.__new__(GPTSniperEngine)
    engine.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    engine._http_deadline_executor = ThreadPoolExecutor(max_workers=1)
    current = request(timeout_ms=30, transport_observation=OpenAITransportObservation())
    try:
        with pytest.raises(OpenAIHTTPWallClockDeadlineError):
            engine._create_openai_response_with_deadline(current, provider_payload={})
        assert entered.is_set()
        current.transport_observation = None
    finally:
        release.set()
        engine._http_deadline_executor.shutdown(wait=True)
    assert R._HTTP_SETTLEMENTS[-1]['request_id'] == 'request'
    assert R._HTTP_SETTLEMENTS[-1]['transport_facts'] == {}


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
