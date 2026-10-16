import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from src.engine.infrastructure import validation_digest_session as D


def test_policy_pipeline_reference_never_opens_raw_and_survives_archive(tmp_path, monkeypatch):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    path = tmp_path / 'pipeline_events/pipeline_events_2026-10-15.jsonl'
    record = dict(path=str(path), sha256='a' * 64)
    def forbidden(*args, **kwargs):
        raise AssertionError('policy consumer opened raw pipeline')
    monkeypatch.setattr(N, '_source_hash', forbidden)
    assert N.source_receipt_matches(record, data_root=tmp_path)
    assert N.source_receipt_matches({**record, 'path': 'data/pipeline_events/' + path.name}, data_root=tmp_path)
    assert not N.source_receipt_matches({**record, 'sha256': 'invalid'}, data_root=tmp_path)
    with pytest.raises(ValueError, match='before_clean_baseline'):
        N.source_receipt_matches({**record, 'path': str(path.with_name('pipeline_events_2026-06-04.jsonl'))}, data_root=tmp_path)


def test_policy_reference_exclusion_keeps_reports_and_other_raw_strict(tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    for relative in ['report/result.json', 'other/pipeline_events_2026-10-15.jsonl',
                     'pipeline_events/not_a_daily_pipeline.jsonl']:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('original')
        record = dict(path=str(path), sha256=hashlib.sha256(b'original').hexdigest())
        assert N.source_receipt_matches(record, data_root=tmp_path)
        path.write_text('changed')
        assert not N.source_receipt_matches(record, data_root=tmp_path)


def session(root, **kw):
    return D.DigestSession(root, '2026-10-14', role='observer', generation={'code':'test'}, **kw)


@pytest.fixture
def source(tmp_path):
    path = tmp_path/'source.jsonl'
    path.write_bytes(b'a'*(D.MIN_BYTES+1))
    return path


def test_cold_warm_actual_digest_and_default_opt_out(tmp_path, source):
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    cold = session(tmp_path)
    with cold.activate():
        assert D.reused_digest(source) == expected
        assert D.reused_digest(source) == expected
    assert cold.stats['full_reads'] == 1
    warm = session(tmp_path)
    with warm.activate():
        assert D.reused_digest(source) == expected
    assert warm.stats['full_reads'] == 0
    assert warm.stats['reused_reads'] == 1
    assert D.reused_digest(source) is None


def test_postclose_is_fresh_per_invocation_and_has_no_store(tmp_path, source):
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    for _ in range(2):
        with D.postclose_session(tmp_path, '2026-10-14') as invocation:
            assert D.reused_digest(source) == expected
            with D.postclose_session(tmp_path, '2026-10-14') as nested:
                assert nested is invocation
                assert D.reused_digest(source) == expected
            assert D.ACTIVE.get() is invocation
        assert invocation.stats['full_reads'] == 1
        assert invocation.stats['reused_reads'] == 1
        assert invocation.entries == {}
        assert not invocation.directory.exists()
        assert D.ACTIVE.get() is None


def test_postclose_never_inherits_persistent_cache_and_restores_parent(tmp_path, source):
    with session(tmp_path).activate() as observer:
        D.reused_digest(source)
        with D.postclose_session(tmp_path, '2026-10-14') as invocation:
            D.reused_digest(source)
            assert invocation is not observer
        assert invocation.stats['full_reads'] == 1
        assert D.ACTIVE.get() is observer
        assert D.reused_digest(source)
        assert observer.stats['reused_reads'] == 1


@pytest.mark.parametrize('role', ['observer', 'transition'])
def test_explicit_persistent_role_cannot_borrow_postclose_lifetime(tmp_path, source, role):
    with D.postclose_session(tmp_path, '2026-10-14') as invocation:
        D.reused_digest(source)
        explicit = D.DigestSession(tmp_path, '2026-10-14', role=role, generation={'code':'test'})
        with explicit.activate() as nested:
            assert nested is explicit and nested is not invocation
            assert D.reused_digest(source)
        assert explicit.stats['full_reads'] == 1
        assert D.ACTIVE.get() is invocation
        assert D.reused_digest(source)
    assert invocation.stats['reused_reads'] == 1


def test_postclose_failure_clears_memory_without_caching_a_verdict(tmp_path, source):
    with pytest.raises(ValueError, match='semantic_failure'):
        with D.postclose_session(tmp_path, '2026-10-14') as invocation:
            D.reused_digest(source)
            raise ValueError('semantic_failure')
    assert not invocation.entries
    assert D.ACTIVE.get() is None
    with D.postclose_session(tmp_path, '2026-10-14') as retry:
        D.reused_digest(source)
    assert retry.stats['full_reads'] == 1


def test_postclose_missing_root_keeps_native_default_and_never_creates_store(tmp_path):
    root = tmp_path / 'missing'
    with D.postclose_session(root, '2026-10-14') as invocation:
        assert D.ACTIVE.get() is None
    assert not root.exists()
    assert invocation.stats['cache_status'] == 'storage_unavailable_full_fallback'


def test_postclose_inherited_context_cannot_reuse_after_fork(tmp_path, source, monkeypatch):
    with D.postclose_session(tmp_path, '2026-10-14') as invocation:
        assert D.reused_digest(source)
        with monkeypatch.context() as child:
            child.setattr(D.os, 'getpid', lambda: invocation.binding['pid'] + 1)
            assert D.reused_digest(source) is None
        assert D.reused_digest(source)
    assert invocation.stats['full_reads'] == 1
    assert invocation.stats['reused_reads'] == 1


def test_postclose_reuse_has_a_bounded_non_sliding_lifetime(tmp_path, source, monkeypatch):
    now = [time.time()]
    monkeypatch.setattr(D.time, 'time', lambda: now[0])
    with D.postclose_session(tmp_path, '2026-10-14') as invocation:
        D.reused_digest(source)
        now[0] += 590
        D.reused_digest(source)
        now[0] += 11
        D.reused_digest(source)
    assert invocation.stats['full_reads'] == 2
    assert invocation.stats['reused_reads'] == 1


def test_postclose_rechecks_changed_bytes_inside_invocation(tmp_path, source):
    with D.postclose_session(tmp_path, '2026-10-14') as invocation:
        first = D.reused_digest(source)
        before = source.stat()
        source.write_bytes(b'b' * before.st_size)
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
        assert D.reused_digest(source) != first
    assert invocation.stats['full_reads'] == 2


def test_postclose_nonlocal_falls_back_without_borrowing_parent(tmp_path, source, monkeypatch):
    with session(tmp_path).activate() as observer:
        D.reused_digest(source)
        monkeypatch.setattr(D, '_local_filesystem', lambda _: False)
        with D.postclose_session(tmp_path, '2026-10-14') as invocation:
            assert D.reused_digest(source) is None
        assert D.ACTIVE.get() is observer
    assert invocation.stats['cache_status'] == 'storage_unavailable_full_fallback'


def test_postclose_controller_cli_reruns_semantics_and_uses_no_persistent_pass(
        tmp_path, source, monkeypatch, capsys):
    from src.engine.automation import postclose_done_controller as C
    monkeypatch.setattr(C, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(C, '_wait_for_predecessor_succeeded', lambda *a, **k: True)
    calls = []
    def build(day, **kwargs):
        calls.append(day)
        assert D.reused_digest(source)
        assert D.reused_digest(source)
        return dict(date=day, status='done' if len(calls) == 1 else 'blocked_direct_evidence_gap')
    monkeypatch.setattr(C, 'build_postclose_done_controller', build)
    assert C.main(['--date', '2026-10-14']) == 0
    first = json.loads(capsys.readouterr().out)
    assert C.main(['--date', '2026-10-14']) == 1
    second = json.loads(capsys.readouterr().out)
    assert calls == ['2026-10-14'] * 2
    for result in (first, second):
        assert result['validation_io']['full_reads'] == 1
        assert result['validation_io']['reused_reads'] == 1
    assert second['status'] == 'blocked_direct_evidence_gap'


def test_prepare_cli_only_shares_digests_verify_keeps_default_full(
        tmp_path, source, monkeypatch, capsys):
    from src.engine.automation import next_preopen_readiness as N
    monkeypatch.setattr(N, 'DATA_DIR', tmp_path)
    def prepare(day, **kwargs):
        assert D.reused_digest(source)
        assert D.reused_digest(source)
        return dict(status='prepared_verified', actual_pid_consumed=False)
    def verify(day, **kwargs):
        assert D.ACTIVE.get() is None
        return dict(status='pass')
    monkeypatch.setattr(N, 'prepare', prepare)
    monkeypatch.setattr(N, 'verify_prepared', verify)
    assert N.main(['--prepare', '--source-date', '2026-10-14']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['validation_io']['reused_reads'] == 1
    assert result['actual_pid_consumed'] is False
    assert N.main(['--verify', '--target-date', '2026-10-15']) == 0
    assert json.loads(capsys.readouterr().out) == dict(status='pass')


@pytest.mark.parametrize('mutation', ['rewrite', 'replace', 'append', 'truncate', 'chmod'])
def test_source_generation_changes_invalidate(tmp_path, source, mutation):
    with session(tmp_path).activate() as cold:
        D.reused_digest(source)
    before = source.stat()
    if mutation == 'rewrite':
        source.write_bytes(b'b'*before.st_size)
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    elif mutation == 'replace':
        other = tmp_path/'next'
        other.write_bytes(source.read_bytes()); other.replace(source)
    elif mutation == 'append':
        with source.open('ab') as out: out.write(b'b')
    elif mutation == 'truncate':
        source.write_bytes(b'c'*D.MIN_BYTES)
    else:
        source.chmod(0o600)
    with session(tmp_path).activate() as warm:
        assert D.reused_digest(source) == hashlib.sha256(source.read_bytes()).hexdigest()
    assert warm.stats['full_reads'] == 1


def test_alias_replacement_expiry_and_corrupt_store(tmp_path, source):
    alias = tmp_path/'alias'; alias.symlink_to(source)
    with session(tmp_path).activate() as cold: D.reused_digest(alias)
    alias.unlink(); alias.symlink_to(source)
    with session(tmp_path).activate() as warm: D.reused_digest(alias)
    assert warm.stats['full_reads'] == 1
    warm.path.write_text('{broken')
    with session(tmp_path).activate() as repaired: D.reused_digest(alias)
    assert repaired.stats['full_reads'] == 1
    with session(tmp_path, ttl=-1).activate() as expired: D.reused_digest(alias)
    assert expired.stats['full_reads'] == 1


def test_corruption_permission_and_enospc_never_return_fake_pass(tmp_path, source, monkeypatch):
    with session(tmp_path).activate() as cold: D.reused_digest(source)
    cold.path.chmod(0o644)
    with session(tmp_path).activate() as unsafe: D.reused_digest(source)
    assert unsafe.stats['full_reads'] == 1
    source.write_bytes(b'b'*source.stat().st_size)
    monkeypatch.setattr(D.os, 'replace', lambda *a: (_ for _ in ()).throw(OSError('disk full')))
    with session(tmp_path).activate() as failed: assert D.reused_digest(source)
    assert failed.stats['cache_status'] == 'publication_failed_full_fallback'
    assert D.ACTIVE.get() is None


def test_native_expected_hash_still_checked_and_new_files_discovered(tmp_path, source):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    with session(tmp_path).activate():
        observed = N._source_hash(str(source), N._signature(source))
    with session(tmp_path).activate() as warm:
        assert N._source_hash(str(source), N._signature(source)) == observed
        assert N._source_hash(str(source), N._signature(source)) != '0'*64
        new = tmp_path/'current.json'; new.write_text('{"new":true}')
        assert json.loads(new.read_text()) == {'new':True}
    assert warm.stats['reused_reads'] == 2


def test_native_policy_validation_reuses_bytes_but_rejects_changed_source(tmp_path):
    from datetime import datetime
    from src.tests.test_mechanistic_entry_runtime_policy import source as policy_source
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import ai_action_outcome_calibration as C
    path = policy_source(tmp_path)
    report = json.loads(path.read_text())
    report['fixture_padding'] = 'a' * (D.MIN_BYTES+1)
    report = C._with_artifact_content_sha256(report)
    C._atomic_write_json(path, report)
    bundle = N.publish(path, data_root=tmp_path, bootstrap=True,
                       now=datetime(2026,9,13,20,tzinfo=N.KST))
    with session(tmp_path).activate() as cold:
        first = N.load(data_root=tmp_path,target_date=bundle['target_date'])
    with session(tmp_path).activate() as warm:
        second = N.load(data_root=tmp_path,target_date=bundle['target_date'])
    assert first == second
    assert cold.stats['full_reads'] > 0
    assert warm.stats['reused_reads'] > 0 and warm.stats['full_reads'] == 0
    frozen = N.root(tmp_path)/'sources'/(bundle['source_file_sha256']+'.json')
    frozen.write_bytes(frozen.read_bytes().replace(b'aaaa',b'bbbb',1))
    with session(tmp_path).activate():
        with pytest.raises(ValueError,match='source_hash_invalid'):
            N.load(data_root=tmp_path,target_date=bundle['target_date'])


def test_full_monitor_native_semantic_parity_across_digest_reuse(tmp_path,monkeypatch):
    from src.tests.test_submission_bottleneck_monitor import reversal_semantic_fixture
    from src.engine.monitoring import submission_bottleneck_monitor as M
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    _,_,now = reversal_semantic_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(D,'MIN_BYTES',1)
    N._CURRENT_CACHE.clear();N._cached_source_hash.cache_clear()
    baseline = M.machine_semantics(tmp_path,now)
    N._CURRENT_CACHE.clear();N._cached_source_hash.cache_clear()
    with session(tmp_path).activate() as cold:
        first = M.machine_semantics(tmp_path,now)
    N._CURRENT_CACHE.clear();N._cached_source_hash.cache_clear()
    with session(tmp_path).activate() as warm:
        second = M.machine_semantics(tmp_path,now)
    assert baseline == first == second
    assert not second['issues']
    assert cold.stats['full_reads'] > 0
    assert warm.stats['full_reads'] == 0 and warm.stats['reused_reads'] > 0


def test_changed_during_hash_is_never_published(tmp_path, source, monkeypatch):
    original = D.hashlib.file_digest
    def racing(stream, method):
        digest = original(stream, method)
        with source.open('ab') as out: out.write(b'changed')
        return digest
    monkeypatch.setattr(D.hashlib, 'file_digest', racing)
    with session(tmp_path).activate() as cold:
        with pytest.raises(ValueError, match='source_changed'): D.reused_digest(source)
        assert cold.entries == {}


def test_delay_raw_byte_generation_keeps_native_contract(tmp_path, source):
    from src.engine.lifecycle.holding_window_generation import byte_generation
    baseline = byte_generation(source)
    with session(tmp_path).activate() as cold:
        assert byte_generation(source) == baseline
    with session(tmp_path).activate() as warm:
        assert byte_generation(source) == baseline
    assert warm.stats['full_reads'] == 0 and warm.stats['reused_reads'] == 1
    source.write_bytes(b'b' * source.stat().st_size)
    with session(tmp_path).activate() as changed:
        assert byte_generation(source) != baseline
    assert changed.stats['full_reads'] == 1


def test_store_lock_is_bounded_and_not_unlinked(tmp_path):
    lock = tmp_path/'lock'
    with D.bounded_lock(lock):
        inode = lock.stat().st_ino
        with pytest.raises(D.ValidationDeferred):
            with D.bounded_lock(lock, seconds=0.01): pass
        assert lock.stat().st_ino == inode


def test_cross_process_reuse_role_and_pid_isolation(tmp_path, source):
    token = 'a'*32
    pid = os.getpid()
    with D.transition_session(tmp_path, '2026-10-14', token, pid) as first:
        D.reused_digest(source)
    script = '''import json,sys
from pathlib import Path
from src.engine.infrastructure import validation_digest_session as D
with D.transition_session(Path(sys.argv[1]),'2026-10-14',sys.argv[2],int(sys.argv[3])) as s:
    D.reused_digest(Path(sys.argv[1])/'source.jsonl')
print(json.dumps(s.stats))
'''
    run = subprocess.run([sys.executable,'-c',script,str(tmp_path),token,str(pid)],
                         capture_output=True,text=True,check=True,timeout=10)
    assert json.loads(run.stdout)['reused_reads'] == 1
    with D.transition_session(tmp_path, '2026-10-14', token) as prestart:
        D.reused_digest(source)
    assert prestart.stats['full_reads'] == 1
    with session(tmp_path).activate() as observer: D.reused_digest(source)
    assert observer.stats['full_reads'] == 1


def test_size_cap_does_not_write_truncated_proof(tmp_path, source, monkeypatch):
    monkeypatch.setattr(D, 'MAX_BYTES', 100)
    with session(tmp_path).activate() as cold: D.reused_digest(source)
    assert not cold.path.exists()
    assert cold.stats['cache_status'] == 'size_limit_full_fallback'


def test_observer_deadline_escapes_permissive_parser():
    from src.engine.monitoring.observation_budget import computation_budget, ObservationDeadline
    with pytest.raises(ObservationDeadline):
        with computation_budget(time.monotonic()+0.01):
            try: time.sleep(0.1)
            except Exception: pytest.fail('deadline swallowed')


def test_bootstrap_cli_repeats_semantic_verifier_with_shared_digest(tmp_path, source, monkeypatch, capsys):
    from src.engine.automation import runtime_policy_bootstrap as B
    monkeypatch.setattr(B, 'DATA_DIR', tmp_path)
    calls=[]
    def verify(day, **kwargs):
        calls.append(kwargs)
        assert D.reused_digest(source)
        return dict(status='pass' if len(calls)==1 else 'fail',findings=[])
    monkeypatch.setattr(B,'verify_bootstrap',verify)
    args=['--verify','--target-date','2026-10-14','--validation-session','f'*32]
    assert B.main(args)==0
    first=json.loads(capsys.readouterr().out)
    assert B.main(args)==1
    second=json.loads(capsys.readouterr().out)
    assert len(calls)==2
    assert first['validation_io']['full_reads']==1
    assert second['validation_io']['reused_reads']==1
    assert second['status']=='fail'


def test_handoff_cli_repeats_pid_checks_in_same_scope(tmp_path, source, monkeypatch, capsys):
    from src.engine.automation import intraday_release_handoff as H
    monkeypatch.setattr(H,'DATA_DIR',tmp_path)
    calls=[]
    def verify(day, *, pid):
        calls.append(pid)
        assert D.reused_digest(source)
        return dict(status='pass' if len(calls)==1 else 'fail',findings=['pid_gate_test'])
    monkeypatch.setattr(H,'verify_pid_consumption',verify)
    args=['--verify','--target-date','2026-10-14','--validation-session','c'*32,'--pid',str(os.getpid())]
    assert H.main(args)==0
    capsys.readouterr()
    assert H.main(args)==1
    second=json.loads(capsys.readouterr().out)
    assert calls==[os.getpid(),os.getpid()]
    assert second['validation_io']['reused_reads']==1


def test_nonlocal_storage_keeps_full_default_path(tmp_path,source,monkeypatch):
    monkeypatch.setattr(D,'_local_filesystem',lambda path:False)
    with session(tmp_path).activate() as disabled:
        assert D.reused_digest(source) is None
    assert disabled.stats['cache_status']=='storage_unavailable_full_fallback'


@pytest.mark.parametrize('status', ['pending','active'])
@pytest.mark.parametrize('attach,key', [
    ('attach_machine_semantics','machine_policy_receipt_contract'),
    ('attach_entry_execution_tuning_semantics','entry_execution_tuning_receipt_contract')])
def test_deferred_preserves_incident_and_notification_age(status, attach, key):
    from src.engine.monitoring import submission_bottleneck_monitor as M
    old = dict(status=status,first_seen='2026-10-14T09:00:00+09:00',
               last_seen='2026-10-14T09:01:00+09:00',notified_status=status,issues={'x':1})
    result = dict(as_of='2026-10-14T09:06:00+09:00',incidents={key:dict(old)},notification_pending=[])
    getattr(M,attach)(result,dict(status='validation_deferred',issues={}))
    assert result['incidents'][key] == old
    assert result['notification_pending'] == []
    getattr(M,attach)(result,dict(status='review_required',issues={'x':1}))
    assert result['incidents'][key]['first_seen'] == old['first_seen']
    assert result['incidents'][key]['status'] == 'active'
