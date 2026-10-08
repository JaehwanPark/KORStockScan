"""Latency optimizations retain dependency, consumer and snapshot contracts."""
import copy
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_evaluation_context as E
from src.engine.infrastructure.snapshot_copy import snapshot_copy


@pytest.fixture
def loader(tmp_path, monkeypatch):
    N._CURRENT_CACHE.clear(); N._CURRENT_FLIGHTS.clear()
    E._CONFIGURED = E._CONSUMED = None
    root = tmp_path / 'data'; root.mkdir()
    path = N.root(root) / 'current.json'; path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'schema':'continuous_reversal_current_v6', 'generation':1}))
    calls = []
    def load(data_root, day):
        calls.append(1)
        pointer = N._read(path)
        return {'bundle_sha256':str(pointer['generation']), 'continuous_reversal':{
            'schema':'continuous_reversal_policy_v6', 'release_commit':'commit', 'cells':[{'value':1}]}}
    monkeypatch.setattr(N, '_load_current_uncached', load)
    yield root, path, calls
    N._CURRENT_CACHE.clear(); E._CONFIGURED = E._CONSUMED = None


def test_one_evaluation_is_immutable_and_next_boundary_revalidates(loader):
    root,path,calls=loader
    with pytest.raises(ValueError, match='generation_changed'), N.verified_evaluation(data_root=root,target_date='2026-10-08') as view:
        assert N.load_effective(data_root=root,target_date='2026-10-08') is view
        with pytest.raises(TypeError):view['continuous_reversal']['cells'][0]['value']=99
        with pytest.raises(TypeError):view['continuous_reversal']['cells'].append({})
        owned=copy.deepcopy(view); owned['continuous_reversal']['cells'][0]['value']=3
        assert view['continuous_reversal']['cells'][0]['value']==1
        path.write_text(json.dumps({'schema':'continuous_reversal_current_v6','generation':2}))
        with pytest.raises(ValueError,match='generation_changed'):
            N.load_effective(data_root=root,target_date='2026-10-08')
    assert N.load_effective(data_root=root,target_date='2026-10-08')['bundle_sha256']=='2'
    assert len(calls)==2


def test_same_mtime_size_and_atomic_replacement_invalidate(loader):
    root,path,calls=loader
    N.load_effective(data_root=root,target_date='2026-10-08')
    old=path.stat();path.write_text(path.read_text().replace(': 1', ': 2'))
    os.utime(path,ns=(old.st_atime_ns,old.st_mtime_ns))
    assert N.load_effective(data_root=root,target_date='2026-10-08')['bundle_sha256']=='2'
    replacement=path.with_suffix('.next');replacement.write_bytes(path.read_bytes())
    os.utime(replacement,ns=(old.st_atime_ns,old.st_mtime_ns));replacement.replace(path)
    N.load_effective(data_root=root,target_date='2026-10-08')
    assert len(calls)==3
    path.unlink()
    assert not N.dependencies_unchanged(next(iter(N._CURRENT_CACHE.values()))[0])


def test_symlink_replacement_even_same_target_invalidates(tmp_path):
    folder=tmp_path/'folder';folder.mkdir();(folder/'a').write_text('x')
    link=tmp_path/'link';link.symlink_to(folder,target_is_directory=True)
    before=N._signature(link/'a');link.unlink();link.symlink_to(folder,target_is_directory=True)
    assert N._signature(link/'a')!=before
    with pytest.raises(ValueError,match='path_changed'):
        with N.signature_pass():
            N._signature(link/'a');link.unlink();link.symlink_to(folder,target_is_directory=True)


def test_concurrent_miss_single_flight_and_failure_does_not_reuse(loader,monkeypatch):
    root,path,calls=loader
    original=N._load_current_uncached;entered=threading.Event();release=threading.Event()
    def slow(*args):
        entered.set();assert release.wait(1);return original(*args)
    monkeypatch.setattr(N,'_load_current_uncached',slow)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(N.load_effective,data_root=root,target_date='2026-10-08') for _ in range(6)]
        assert entered.wait(1);release.set()
        assert [f.result()['bundle_sha256'] for f in futures]==['1']*6
    assert len(calls)==1
    path.write_text(path.read_text().replace(': 1', ': 2'))
    monkeypatch.setattr(N,'_load_current_uncached',lambda *a:(_ for _ in ()).throw(ValueError('broken')))
    with pytest.raises(ValueError,match='broken'):N.load_effective(data_root=root,target_date='2026-10-08')
    assert not N._CURRENT_FLIGHTS and not N._CURRENT_CACHE


def test_prepare_reuses_configuration_and_receipt_but_observes_overlay(loader,monkeypatch):
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.scalping import reversal_current_backend as D, reversal_auxiliary_intraday as I
    root,path,calls=loader; configured=[];receipts=[]
    monkeypatch.setattr(router,'selected_release',lambda w:(root.parent,'commit'))
    monkeypatch.setattr(H,'_identity',lambda p:dict(pid=p,start_ticks='1',cwd=str(root.parent/'src')))
    monkeypatch.setattr(H,'_paths',lambda day,commit:(root/'handoff',root/'consumed'))
    monkeypatch.setattr(D,'configure_bundle',lambda bundle,**kw:configured.append(bundle))
    def receipt(data_root,bundle):
        assert N.load_effective(data_root=data_root,target_date='2026-10-08') is bundle
        receipts.append(bundle)
    monkeypatch.setattr(I,'record_pid_consumption',receipt)
    for _ in range(3):E.prepare(data_root=root,day='2026-10-08')
    assert len(calls)==len(configured)==len(receipts)==1
    overlay=I.root(root)/'current.json';overlay.parent.mkdir(parents=True);overlay.write_text('{}')
    E.prepare(data_root=root,day='2026-10-08')
    assert len(configured)==1 and len(receipts)==2
    E._CONFIGURED=None
    def fail(*a,**kw):raise ValueError('configure failed')
    monkeypatch.setattr(D,'configure_bundle',fail)
    with pytest.raises(ValueError,match='configure failed'):E.prepare(data_root=root,day='2026-10-08')
    assert E._CONFIGURED is None


def test_snapshot_copy_full_history_alias_cycles_and_consumer_isolation():
    from collections import deque
    rows=deque([{'price':i,'nested':{'values':[i]}} for i in range(2000)],maxlen=2000)
    source={'rows':rows,'alias':rows};source['cycle']=source
    actual=snapshot_copy(source)
    assert actual['cycle'] is actual and actual['rows'] is actual['alias']
    assert len(actual['rows'])==2000 and actual['rows'].maxlen==2000
    actual['rows'][0]['nested']['values'][0]=-1
    assert source['rows'][0]['nested']['values'][0]==0
    assert snapshot_copy(source)['rows'][0]['nested']['values'][0]==0


def test_actual_clock_is_acquired_after_claim_lock(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as S, reversal_current_backend as D
    now=[4.999];observed=[]
    class Lock:
        def __enter__(self):now[0]=5.001
        def __exit__(self,*a):pass
    backend=SimpleNamespace(_LOCK=Lock(),claim_snapshot=lambda **kw:observed.append(kw['now']))
    monkeypatch.setattr(D,'backend',lambda:backend)
    monkeypatch.setattr(S.time,'time',lambda:now[0])
    S.claim_snapshot_with_receipt(now=4.999,live_clock=True)
    assert observed==[5.001]


def test_changed_during_validation_is_not_cached(loader,monkeypatch):
    root,path,calls=loader;original=N._load_current_uncached
    def changed(*args):
        value=original(*args)
        path.write_text(path.read_text().replace(': 1', ': 2'))
        return value
    monkeypatch.setattr(N,'_load_current_uncached',changed)
    with pytest.raises(ValueError,match='dependency_changed'):
        N.load_effective(data_root=root,target_date='2026-10-08')
    assert not N._CURRENT_CACHE and not N._CURRENT_FLIGHTS


def test_validation_wait_is_bounded_and_never_returns_stale(loader):
    root,path,calls=loader
    N._CURRENT_FLIGHTS[(str(root.resolve()),'2026-10-08')]=threading.Event()
    try:
        with pytest.raises(ValueError,match='validation_in_progress'):
            N.load_effective(data_root=root,target_date='2026-10-08')
    finally:N._CURRENT_FLIGHTS.clear()


def test_waiting_on_guard_cannot_resurrect_five_second_signal(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as S,reversal_current_backend as D
    now=[4.999]
    class Lock:
        def __enter__(self):now[0]=5.001
        def __exit__(self,*a):pass
    def guard(claim,family,*,now):
        if now>5:raise ValueError('reversal_signal_expired')
        return 'valid'
    backend=SimpleNamespace(_LOCK=Lock(),validate_claim=guard,_CLAIMS={})
    monkeypatch.setattr(D,'backend',lambda *a:backend)
    monkeypatch.setattr(S.time,'time',lambda:now[0])
    monkeypatch.setattr(S,'_claim_failure_receipt',lambda *a:{'runtime_effect':False})
    with pytest.raises(ValueError,match='expired'):
        S.validate_claim_with_receipt({},'family',now=4.999,live_clock=True)


def test_performance_observes_every_loop_and_keeps_null_for_no_provider():
    from src.engine.monitoring import runtime_performance as P
    P.observe('loop_work',.1,generation='test-performance-only')
    for i in range(4200):P.observe('loop_work',i/1000)
    s=P.snapshot()
    assert s['metrics']['loop_work']['total_observed']==4201
    assert s['metrics']['loop_work']['n']==4096
    assert s['metrics']['provider_response']['p99_seconds'] is None
    assert s['decision_authority']=='none'


def test_absolute_symlink_dotdot_signature_matches_os_open(tmp_path):
    actual=tmp_path/'actual';actual.mkdir();(actual/'child').mkdir()
    (actual/'value').write_text('actual');(tmp_path/'value').write_text('other')
    link=tmp_path/'link';link.symlink_to(actual/'child',target_is_directory=True)
    source=link/'..'/'value'
    signature=N._signature(source)
    assert signature[0]==str(source.resolve())
    assert N._source_hash(str(source),signature)==__import__('hashlib').sha256(b'actual').hexdigest()
