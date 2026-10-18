"""Shared native loaders preserve policy dates and fail closed without runtime I/O."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

import pytest

from src.engine.infrastructure import main_policy_loading as L
from src.engine.scalping import pre_submit_delay_tuning as D
from src.tests.test_reversal_operating_policy import native, parent, replay

OBSERVED = datetime.fromisoformat('2026-10-04T12:00:00+09:00')
TARGET = '2026-10-05'


@pytest.fixture(autouse=True)
def clean_policy_environment(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith('KORSTOCKSCAN_'):
            monkeypatch.delenv(key)
    monkeypatch.setattr(D, '_PREPARED_DELAY_KEY', None)
    monkeypatch.setattr(D, '_PREPARED_DELAY_POLICY', None)
    monkeypatch.setattr(D, '_PREPARED_DELAY_RECEIPT', None)
    from src.engine.scalping import main_stop_policy as S
    monkeypatch.setattr(S, '_LOADED', None)
    monkeypatch.setattr(S, '_LOADED_ENV', None)
    from src.engine.scalping import trailing_mechanical_policy as T
    T._loaded_classifier.cache_clear()
    T._loaded_policy_vector.cache_clear()
    yield
    T._loaded_classifier.cache_clear()
    T._loaded_policy_vector.cache_clear()


def _env(monkeypatch, env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from src.utils import constants
    monkeypatch.setattr(constants, 'TRADING_RULES', constants._build_trading_rules())
    return dict(os.environ)


def _prepared_delay(tmp_path, monkeypatch):
    from src.tests.test_pre_submit_delay_initial_policy import build
    from src.engine.scalping import pre_submit_delay_initial_policy as I
    report, policy = build(tmp_path, monkeypatch,
        [{'prices': {0: 10000, 30: 9950}} for _ in range(6)])
    I.publish(tmp_path, report, policy, expected_incumbent=None)
    report_file, policy_file, _, manifest = I.committed_paths(tmp_path, '2026-10-02')
    return policy, dict(KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED='true',
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE=str(policy_file),
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE=TARGET,
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_MANIFEST_SHA256=manifest['manifest_sha256'])


def _machine_stub(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_evaluation_context as E
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    bundle = dict(bundle_sha256='a' * 64, scope_policies={'KRX|KRX_REGULAR': {'machine_policy': {'active': True}}})
    source = tmp_path / 'machine.json'
    source.write_text(json.dumps(bundle))
    monkeypatch.setattr(E, 'prepare_policy_loading', lambda **kwargs: bundle)
    monkeypatch.setattr(N, 'preparation_path', lambda *_: source)
    from src.engine.automation import auxiliary_reader_readiness as A
    monkeypatch.setattr(A, 'verify_auxiliary_reader', lambda *args, **kwargs: {'status': 'not_required'})
    return bundle


def test_future_policy_date_loads_nonempty_native_delay_without_future_clock(tmp_path, monkeypatch):
    policy, env = _prepared_delay(tmp_path, monkeypatch)
    env = _env(monkeypatch, env)
    before = OBSERVED.isoformat()
    result = D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=tmp_path)
    assert result['status'] == 'prepared'
    assert result['target_date'] == TARGET
    assert result['policy_sha256'] == policy['policy_sha256']
    assert result['loaded_object_sha256']
    assert D._PREPARED_DELAY_POLICY.cells
    assert any(cell['delay_sec'] == 30 for cell in D._PREPARED_DELAY_POLICY.cells.values())
    assert OBSERVED.isoformat() == before
    # Native real-time lookup still refuses this future date; no activation.
    assert D.load_runtime_policy(now=OBSERVED)['delay_sec'] == 0
    again = D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=tmp_path)
    assert again['status'] == 'prepared_reused'
    assert again['loaded_object_sha256'] == result['loaded_object_sha256']


def test_same_policy_path_other_data_root_does_not_reuse_prepared_cache(tmp_path, monkeypatch):
    _, env = _prepared_delay(tmp_path, monkeypatch)
    env = _env(monkeypatch, env)
    assert D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=tmp_path)['status'] == 'prepared'
    other = tmp_path / 'other'
    result = D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=other)
    assert result['status'] == 'preparation_invalid'
    assert D._PREPARED_DELAY_POLICY is None


def test_disabled_preparation_reuse_stays_disabled(tmp_path):
    for _ in range(2):
        assert D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env={}, data_root=tmp_path)['status'] == 'disabled'


def test_delay_invalid_return_is_aggregate_failure_not_import_success(tmp_path, monkeypatch):
    _machine_stub(tmp_path, monkeypatch)
    env = _env(monkeypatch, {'KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED': 'true',
        'KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE': str(tmp_path / 'missing.json')})
    result = L.load_main_policies(target_date=TARGET, observed_at=OBSERVED,
        data_root=tmp_path, env=env, validation=True)
    assert result['status'] == 'failed'
    assert set(result['consumer_results']) == L.CONSUMER_IDS
    delay = result['consumer_results']['pre_submit_delay']
    assert delay['status'] == 'failed'
    assert 'preparation_invalid' in delay['reason']
    assert result['actual_pid_consumed'] is False


def test_actual_trailing_object_digest_and_scope_are_consumed(tmp_path, monkeypatch):
    from src.engine.scalping import trailing_mechanical_policy as T
    from src.engine.scalping import trailing_situation_policy as S
    values = {market: dict(T.DEFAULTS) for market in T.START_MARKETS}
    parent = T.market_values_hash(values)
    policy = S.initial_bundle(values, parent_sha256=parent, source_date='2026-10-02', target_date=TARGET)
    _machine_stub(tmp_path, monkeypatch)
    env = _env(monkeypatch, {S.ENV_KEY: json.dumps(policy), T.VECTOR_SHA_ENV_KEY: parent,
        'KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE': TARGET})
    result = L.load_main_policies(target_date=TARGET, observed_at=OBSERVED, data_root=tmp_path, env=env, validation=True)
    record = result['consumer_results']['trailing_situation']
    assert record['status'] == 'loaded'
    assert record['policy_sha256'] == policy['policy_sha256']
    assert len(record['scope_keys']) == len(T.START_MARKETS) * len(S.TYPES)
    assert S._PREPARED.cells
    assert record['loaded_object_sha256'] == L._digest(dict(policy_sha256=S._PREPARED.policy_sha256,
        parent_sha256=parent, classifier_sha256=None, target_date=TARGET, cells=S._PREPARED.cells))


def test_mutated_trailing_policy_cannot_become_parent_fallback(tmp_path, monkeypatch):
    _machine_stub(tmp_path, monkeypatch)
    env = _env(monkeypatch, {'KORSTOCKSCAN_TRAILING_SITUATION_POLICY_JSON': '{"schema":"bad"}'})
    result = L.load_main_policies(target_date=TARGET, observed_at=OBSERVED, data_root=tmp_path, env=env, validation=True)
    assert result['consumer_results']['trailing_situation']['status'] == 'failed'
    assert result['status'] == 'failed'


def test_stop_loading_never_records_operational_pid(tmp_path, monkeypatch):
    from src.tests.test_main_stop_policy import publication
    from src.engine.scalping import main_stop_policy as S
    bundle, _, _, _ = publication(tmp_path)
    # Publisher fixture is genuine and all native hashes/code guards remain on.
    target = bundle['target_date']
    path = tmp_path / 'stop-startup.json'
    path.write_text(json.dumps(bundle))
    _machine_stub(tmp_path, monkeypatch)
    parent_values = next(iter(bundle['cells'].values()))['parent_values']
    env = _env(monkeypatch, {S.ENV_FILE: str(path), S.ENV_SHA: hashlib.sha256(path.read_bytes()).hexdigest(), S.ENV_DATE: target,
        **{'KORSTOCKSCAN_' + S.KEYS[key]: str(value) for key, value in parent_values.items()}})
    monkeypatch.setattr(S, 'record_loaded_policy', lambda *_: pytest.fail('operational stop PID receipt attempted'))
    result = L.load_main_policies(target_date=target, observed_at=OBSERVED, data_root=tmp_path, env=env, validation=True)
    record = result['consumer_results']['main_stop']
    assert record['status'] == 'loaded', record
    assert record['scope_keys']
    assert S._LOADED
    assert not (tmp_path / 'runtime/main_stop_confirmation').exists()


def test_split_explicit_target_uses_actual_operator_clock(tmp_path):
    from src.engine.scalping.entry_split_order_plan import _load_policy_from_env
    env = {'KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED': 'true',
        'KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE': TARGET,
        'KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE': str(tmp_path / 'none')}
    assert _load_policy_from_env(now=OBSERVED, env=env)[1] == 'policy_inactive_date'
    assert _load_policy_from_env(now=OBSERVED, target_date=TARGET, env=env, preparation=True)[1] == 'policy_file_not_found'


def test_process_environment_mismatch_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='environment_mismatch'):
        L.load_main_policies(target_date=TARGET, observed_at=OBSERVED, data_root=tmp_path,
            env={'KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_FILE': '/foreign'}, validation=True)


def test_naive_observed_clock_rejected_before_loader(tmp_path):
    with pytest.raises(ValueError, match='clock_must_be_aware'):
        L.load_main_policies(target_date=TARGET, observed_at=datetime(2026, 10, 4), data_root=tmp_path, env={})


def test_native_entry_preparation_does_not_record_pid_or_enter_live_reader(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_evaluation_context as E
    from src.engine.scalping import reversal_current_backend as B
    from src.engine.scalping import reversal_auxiliary_intraday as A
    bundle = {'bundle_sha256': 'c' * 64, 'continuous_reversal': {'schema': 'continuous_reversal_policy_v6'}}
    monkeypatch.setattr(E.N, 'load', lambda **kwargs: bundle)
    monkeypatch.setattr(E.N, 'verified_evaluation', lambda **kwargs: pytest.fail('current activation reader attempted'))
    monkeypatch.setattr(A, 'record_pid_consumption', lambda *args: pytest.fail('actual PID attestation attempted'))
    configured = []
    monkeypatch.setattr(B, 'configure_bundle', lambda value, **kwargs: configured.append((value, kwargs)))
    assert E.prepare_policy_loading(data_root=tmp_path, day=TARGET, preparation=True) is bundle
    assert configured == [(bundle, {'data_root': tmp_path, 'day': TARGET, 'read_only': True})]


def test_live_invalid_trailing_retains_existing_startup_exception(tmp_path, monkeypatch):
    _machine_stub(tmp_path, monkeypatch)
    env = _env(monkeypatch, {'KORSTOCKSCAN_TRAILING_SITUATION_POLICY_JSON': '{"schema":"bad"}'})
    with pytest.raises(ValueError, match='trailing_situation_policy_invalid'):
        L.load_main_policies(target_date=TARGET, observed_at=OBSERVED, data_root=tmp_path, env=env)


def test_split_future_operator_content_does_not_grant_execution(tmp_path):
    from src.engine.scalping.entry_split_order_plan import _load_policy_from_env, POLICY_SCHEMA_VERSION
    path = tmp_path / 'legacy-split.json'
    path.write_text(json.dumps(dict(schema_version=POLICY_SCHEMA_VERSION, source_date='2026-08-31',
        policy_version='legacy-carried', buckets={}, runtime_apply_allowed=False)))
    env = {'KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED': 'true',
        'KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE': TARGET,
        'KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE': str(path),
        'KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED': 'true',
        'KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE': TARGET}
    loaded, status = _load_policy_from_env(now=OBSERVED, target_date=TARGET, env=env, preparation=True)
    assert status == 'loaded'
    assert loaded['execution_authority'] is False
    assert loaded['entry_split_order_operator_fallback_prepared'] is True
    assert 'entry_split_order_operator_fallback_authorized' not in loaded
    assert _load_policy_from_env(now=OBSERVED, env=env)[1] == 'policy_inactive_date'
    with pytest.raises(ValueError, match='requires_preparation'):
        _load_policy_from_env(now=OBSERVED, target_date=TARGET, env=env)
    env['KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE'] = '2026-10-06'
    assert _load_policy_from_env(now=OBSERVED, target_date=TARGET, env=env, preparation=True)[1] == 'policy_runtime_apply_not_allowed'


def test_native_nonempty_machine_prompt_and_trailing_complete_shared_load(tmp_path, monkeypatch):
    from src.tests.test_main_prompt_policy_loading import _prepare, _holding_candidates
    from src.engine.scalping import trailing_mechanical_policy as T
    from src.engine.scalping import trailing_situation_policy as S
    env, machine, _ = _prepare(monkeypatch, tmp_path)
    _holding_candidates(monkeypatch, tmp_path)
    target = machine['target_date']
    values = {market: dict(T.DEFAULTS) for market in T.START_MARKETS}
    parent = T.market_values_hash(values)
    trailing = S.initial_bundle(values, parent_sha256=parent,
        source_date=machine['source_date'], target_date=target)
    env.update({S.ENV_KEY: json.dumps(trailing), T.VECTOR_SHA_ENV_KEY: parent,
        'KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE': target})
    env = _env(monkeypatch, env)
    result = L.load_main_policies(target_date=target,
        observed_at=datetime.fromisoformat('2026-09-13T12:00:00+09:00'),
        data_root=tmp_path, env=env, validation=True)
    assert result['status'] == 'passed', result['consumer_results']
    assert set(result['consumer_results']) == L.CONSUMER_IDS
    assert result['consumer_results']['main_machine']['policy_sha256'] == machine['bundle_sha256']
    assert result['consumer_results']['main_machine']['scope_keys']
    assert result['consumer_results']['entry_prompt']['status'] == 'loaded'
    assert result['consumer_results']['holding_prompt']['status'] == 'loaded'
    assert len(result['consumer_results']['trailing_situation']['scope_keys']) == 12
    assert result['actual_pid_consumed'] is False
    assert result['runtime_effect'] is False
    assert not list(tmp_path.rglob('consumed'))
    assert not list(tmp_path.rglob('pid_*.json'))


def test_live_startup_preserves_lazy_consumer_lifecycle(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_evaluation_context as E
    from src.engine.scalping import main_stop_policy as S
    from src.engine.scalping import initial_quantity_activation as Q
    from src.engine.infrastructure import main_prompt_policy_loading as P
    for module, name in ((E, 'prepare_policy_loading'), (S, 'preload'),
                         (Q, 'load_pinned_initial_quantity_policy'), (P, 'load_prompt_policy_consumers')):
        monkeypatch.setattr(module, name, lambda *args, **kwargs: pytest.fail('lazy runtime consumer eagerly invoked'))
    env = _env(monkeypatch, {})
    result = L.load_main_policies(target_date=TARGET, observed_at=OBSERVED, data_root=tmp_path, env=env)
    assert result['status'] == 'deferred'
    assert result['consumer_results']['pre_submit_delay']['status'] == 'disabled'
    assert result['consumer_results']['trailing_situation']['status'] == 'parent_only'
    assert {name for name, record in result['consumer_results'].items() if record['status'] == 'deferred'} == (
        L.CONSUMER_IDS - {'pre_submit_delay', 'trailing_situation'})


def test_delay_receipt_failure_clears_cache_before_retry(tmp_path, monkeypatch):
    _, env = _prepared_delay(tmp_path, monkeypatch)
    env = _env(monkeypatch, env)
    original = D._digest
    with monkeypatch.context() as failure:
        failure.setattr(D, '_digest', lambda _: (_ for _ in ()).throw(ValueError('receipt_failure')))
        result = D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=tmp_path)
    assert result['status'] == 'preparation_invalid'
    assert D._PREPARED_DELAY_POLICY is D._PREPARED_DELAY_KEY is D._PREPARED_DELAY_RECEIPT is None
    assert D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=tmp_path)['status'] == 'prepared'


def test_delay_receipt_cannot_bind_different_bytes_after_object_load(tmp_path, monkeypatch):
    _, env = _prepared_delay(tmp_path, monkeypatch)
    env = _env(monkeypatch, env)
    policy_path = Path(env['KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE'])
    from src.engine.scalping.pre_submit_delay_initial_policy import PreparedPolicy
    prepared = []
    original_prepare = PreparedPolicy.from_artifacts
    def prepare(cls, *args, **kwargs):
        value = original_prepare(*args, **kwargs)
        prepared.append(True)
        return value
    monkeypatch.setattr(PreparedPolicy, 'from_artifacts', classmethod(prepare))
    original = Path.read_bytes
    def replaced(path):
        raw = original(path)
        if path == policy_path and prepared:
            return json.dumps({**json.loads(raw), 'late_rewrite': True}).encode()
        return raw
    monkeypatch.setattr(Path, 'read_bytes', replaced)
    result = D.prepare_runtime_policy(now=OBSERVED, target_date=TARGET, env=env, data_root=tmp_path)
    assert result['status'] == 'preparation_invalid'
    assert 'source_changed_after_loading' in result['reason']
    assert D._PREPARED_DELAY_KEY is None


def test_genuine_v6_prepared_bundle_loads_all_routes_without_current_or_pid_mutation(replay, monkeypatch):
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_policy_v5 as V5
    from src.engine.scalping import continuous_reversal_policy_v6 as V6
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_extended_registration as ER
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.scalping import reversal_extended_union as U
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_tuning as AT
    from src.engine.scalping import reversal_evaluation_context as E
    from src.engine.scalping import reversal_current_backend as B
    from src.engine.scalping import reversal_auxiliary_intraday as A
    from src.engine.automation.auxiliary_reader_readiness import verify_auxiliary_reader
    from src.tests.test_reversal_operating_policy import transport, authorize_initial
    root, base, machine = replay
    O.prepare_inputs(root, '2026-10-07', machine, base)
    O.L.calls(O, root, '2026-10-07', transport=transport, call_limit=5)
    authorize_initial(root, base)
    aux = O.auxiliary_report(root, '2026-10-07', '2026-10-07', base, publish_policy=False)
    issued = json.loads((O.directory(root, '2026-10-07') / 'machine.json').read_text())
    old = V5.stage(root, '2026-10-07', '2026-10-07', issued, aux,
        target_date='2026-10-08', release_commit='a' * 40)
    V5.validate_sources(old, root)
    from src.tests.test_reversal_startup_readonly import guarded_child
    v5_child_root = root.parent / 'v5-cold-check'
    v5_child_root.mkdir()
    v5_sources = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    cold_v5 = guarded_child(v5_child_root, f"""
from src.engine.scalping import reversal_evaluation_context as E
from src.engine.scalping import reversal_current_backend as B
loaded = E.prepare_policy_loading(data_root=Path({str(root)!r}), day='2026-10-08', preparation=True)
(run/'result.json').write_text(json.dumps(dict(bundle_sha256=loaded['bundle_sha256'],
    backend_generation=B.backend()._GENERATION)))
""")
    assert cold_v5['bundle_sha256'] == old['bundle_sha256']
    assert cold_v5['backend_generation'] == old['continuous_reversal']['family_sha256']
    assert {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()} == v5_sources
    changes = P.seal(dict(schema='main_extended_registration_request_v1', kind='ADD',
        parent_bundle_sha256=old['bundle_sha256'], operator_receipt=ER.AUTHORITY,
        research_batch_sha256=C.RESEARCH_BATCH_SHA256, target_date='2026-10-12', source_receipts=[],
        scopes={d['symbol_group']+'|'+d['market']+'|'+d['price_band']+'|'+d['route']: dict(add=[b], remove=[])
            for b, d in C.NEW_DEFINITIONS.items()},
        definition_hashes={b: P.digest(C.definition(b)) for b in C.NEW_DEFINITIONS}))
    P.write(ER.pending_path(root), changes)
    # Supply the prior validated bundle to the offline producer only. Native
    # readers/validators and backend setup below remain the real implementation.
    with monkeypatch.context() as producer:
        producer.setattr(N, 'load_effective', lambda **kw: old)
        source = P.seal(dict(normalized_sources=dict(partitions=[])))
        machine = O.machine_report(root, '2026-10-08', '2026-10-08', old, source=source, publish_outputs=False)
        candidate = G.register(root, G.definition(U.V1.ARMS[1]))
        AT.configure(root, candidate=candidate, scopes=['samsung|PRE|ALL|NXT'], seed='startup-v6-test')
        O.prepare_inputs(root, '2026-10-08', machine, old)
        auxiliary = O.auxiliary_report(root, '2026-10-08', '2026-10-08', old, publish_policy=True)
        issued = json.loads((O.directory(root, '2026-10-08') / 'machine.json').read_text())
        prepared = V6.stage(root, '2026-10-08', '2026-10-08', issued, auxiliary,
            target_date='2026-10-12', release_commit='a' * 40)
    V6.validate_sources(prepared, root)
    current = N.root(root) / 'current.json'
    original_current = current.read_bytes()
    monkeypatch.setattr(A, 'record_pid_consumption', lambda *args: pytest.fail('operational PID recording attempted'))
    # Restore every process-local backend/cache container after this genuine
    # configure call so the fixture cannot leak a policy into unrelated tests.
    pending, seen = [B], set()
    while pending:
        module = pending.pop()
        if id(module) in seen:
            continue
        seen.add(id(module))
        for name in ('_ACTIVE', '_FAMILY', '_GENERATION', '_STATES', '_CLAIMS',
                     '_ANCHORS', '_RESTORED_DAYS', '_EMPTY_PREFIX_DAYS'):
            if hasattr(module, name):
                value = getattr(module, name)
                monkeypatch.setattr(module, name, value.copy() if isinstance(value, (dict, set, list)) else value)
        for name in ('OLD', 'V6', 'V5', 'R', 'B'):
            value = getattr(module, name, None)
            if getattr(value, '__name__', '').startswith('src.engine.scalping.'):
                pending.append(value)
    # Run this genuine v6 generation in a fresh OS-isolated child as well as
    # the same-process reader. Production/setup imports in pytest cannot hide
    # cold collector imports or anchor-index writes in the child.
    from src.tests.test_reversal_startup_readonly import guarded_child
    source_before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    cold = guarded_child(root.parent, f"""
from src.engine.scalping import reversal_evaluation_context as E
from src.engine.scalping import reversal_current_backend as B
from src.engine.automation.auxiliary_reader_readiness import verify_auxiliary_reader
loaded = E.prepare_policy_loading(data_root=Path({str(root)!r}), day='2026-10-12', preparation=True)
auxiliary = verify_auxiliary_reader('2026-10-12', data_root=Path({str(root)!r}), preparation=True, bundle=loaded)
assert auxiliary['status'] == 'pass'
(run/'result.json').write_text(json.dumps(dict(bundle_sha256=loaded['bundle_sha256'],
    backend_generation=B.backend()._GENERATION, scope_count=auxiliary['scope_count'])))
""")
    assert cold['bundle_sha256'] == prepared['bundle_sha256']
    assert cold['backend_generation'] == prepared['continuous_reversal']['family_sha256']
    assert cold['scope_count'] > 0
    assert {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()} == source_before
    loaded = E.prepare_policy_loading(data_root=root, day='2026-10-12', preparation=True)
    assert loaded['bundle_sha256'] == prepared['bundle_sha256']
    assert B.backend()._GENERATION == prepared['continuous_reversal']['family_sha256']
    assert len(V6.scopes()) == 128
    assert sum(len(cell['routes']) for cell in loaded['continuous_reversal']['machine_cells'].values()) == 128
    auxiliary_result = verify_auxiliary_reader('2026-10-12', data_root=root, preparation=True, bundle=loaded)
    assert auxiliary_result['status'] == 'pass'
    assert auxiliary_result['scope_count'] > 0
    assert current.read_bytes() == original_current
    assert not list(root.rglob('consumed'))


def test_quantity_policy_import_never_initializes_broker_or_logger(tmp_path):
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[2]
    script = """import importlib.abc, sys
sys.path.insert(0, ROOT)
forbidden = {'src.engine.kiwoom_orders', 'src.engine.sniper_config', 'src.utils.logger', 'requests'}
class NoExecutionImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in forbidden:
            raise AssertionError('execution import attempted: ' + fullname)
sys.meta_path.insert(0, NoExecutionImports())
from src.engine.scalping.position_sizing_allocator import _runtime_position_sizing_policy
result = _runtime_position_sizing_policy(None, 'UNKNOWN')
assert result == ('entry_type_5stage_cap25_v1', (.10,.15,.20,.25,.25), 'policy_disabled_default', None, None), result
assert not forbidden.intersection(sys.modules)
""".replace('ROOT', repr(str(root)), 1)
    env = {key: value for key, value in os.environ.items() if not key.startswith('KORSTOCKSCAN_')}
    result = subprocess.run([sys.executable, '-I', '-B', '-c', script], cwd=tmp_path,
        env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
