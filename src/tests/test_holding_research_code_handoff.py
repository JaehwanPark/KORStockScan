"""Reviewed generations retain exact source closure without new policy authority."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from src.engine.automation import intraday_release_handoff as H
from src.engine.automation import prepared_policy_code_handoff as C
from src.tests.test_prepared_policy_code_handoff import prepared

ORIGIN = '7f2552aedde8fec6ef904a43105827907e50dfc8'
OWN = 'src/engine/automation/intraday_release_handoff.py'
TRIGGER = 'src/engine/sniper_state_handlers.py'
ROOT = Path(H.__file__).resolve().parents[3]
NATIVE_VERIFY = H._verify_entry_code_delta
REAL_GIT = H.subprocess.check_output
GENERATIONS = {
    'historical_9d': '9d2201141aeae409fe960ff7795a1340718a7146',
    'completed_current': REAL_GIT(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
}
PAIRS = {
    'historical_9d': H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES,
    'completed_current': {**H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES,
                          **H.REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES},
}
DEPENDENCIES = {
    generation: H.REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[TRIGGER][pairs[TRIGGER][1]]
    for generation, pairs in PAIRS.items()
}
# Every positive verification checks the full closure. Negative probes cover
# each old dependency plus distinct new source, cost and startup helper roles.
DEPENDENCY_CASES = {
    'historical_9d': tuple(DEPENDENCIES['historical_9d']),
    'completed_current': (*DEPENDENCIES['historical_9d'],
        'src/engine/scalping/main_stop_runtime_source.py',
        'src/engine/lifecycle/holding_research_cost.py',
        'src/engine/infrastructure/main_prompt_policy_loading.py'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()


@pytest.fixture(params=tuple(GENERATIONS))
def candidate(tmp_path, monkeypatch, request):
    """Use exact 9d/current Git objects, never current bytes under an old label."""
    generation = request.param
    commit = GENERATIONS[generation]
    pairs = PAIRS[generation]
    dependencies = DEPENDENCIES[generation]
    root = tmp_path / 'source'
    names = {OWN, *pairs, *dependencies}
    committed = {name: REAL_GIT(['git', '-C', str(ROOT), 'show', commit+':'+name])
                 for name in names}
    for name, raw in committed.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    original = {name: REAL_GIT(['git', '-C', str(ROOT), 'show', ORIGIN+':'+name])
                for name in pairs}
    def revision(command, **kwargs):
        ref, name = command[-1].split(':', 1)
        if ref == commit:
            return committed[name]
        assert ref == ORIGIN
        return original[name]
    monkeypatch.setattr(H.subprocess, 'check_output', revision)
    def verify(name=TRIGGER, *, alias=None):
        path_name = alias or name
        expected = digest({name: hashlib.sha256(original[name]).hexdigest()})
        return NATIVE_VERIFY(root, commit, ORIGIN, {name: path_name}, expected)
    return SimpleNamespace(root=root, committed=committed, original=original, verify=verify,
        pairs=pairs, dependencies=dependencies, generation=generation, commit=commit)


@pytest.mark.parametrize('candidate,name', [
    (generation, name) for generation, pairs in PAIRS.items() for name in pairs
], indirect=['candidate'])
def test_real_reviewed_pairs_preserve_exact_original_and_integrated_sources(candidate, name):
    c = candidate
    pair = c.pairs[name]
    assert tuple(hashlib.sha256(raw).hexdigest() for raw in (c.original[name], c.committed[name])) == pair
    assert c.committed[name] == REAL_GIT(['git', '-C', str(ROOT), 'show', c.commit+':'+name])
    before = {str(path): path.read_bytes() for path in c.root.rglob('*.py')}
    assert c.verify(name) == [name]
    assert before == {str(path): path.read_bytes() for path in c.root.rglob('*.py')}


@pytest.mark.parametrize('candidate,name', [
    (generation, name) for generation, pairs in PAIRS.items() for name in pairs
], indirect=['candidate'])
@pytest.mark.parametrize('dirty', [False, True])
def test_reviewed_source_pairs_reject_unknown_committed_or_dirty_bytes(candidate, name, dirty):
    c = candidate
    path = c.root / name
    path.write_bytes(path.read_bytes() + b'\nUNKNOWN_INTEGRATION = True\n')
    if not dirty:
        c.committed[name] = path.read_bytes()
    with pytest.raises(ValueError, match=('dirty_release' if dirty else 'unreviewed_change|producer_changed')):
        c.verify(name)


@pytest.mark.parametrize('candidate,dependency', [
    (generation, name) for generation, names in DEPENDENCY_CASES.items() for name in names
], indirect=['candidate'])
@pytest.mark.parametrize('fault', ['missing', 'symlink', 'unknown_committed', 'dirty_git', 'reverify'])
def test_native_handoff_rechecks_helper_and_provenance_closure(candidate, dependency, fault):
    c = candidate
    assert c.verify() == [TRIGGER]
    path = c.root / dependency
    if fault == 'missing':
        path.unlink()
    elif fault == 'symlink':
        target = path.with_suffix('.saved')
        path.rename(target)
        path.symlink_to(target)
    elif fault == 'dirty_git':
        c.committed[dependency] += b'\nUNCOMMITTED_SOURCE = True\n'
    else:
        path.write_bytes(path.read_bytes() + b'\nUNKNOWN_HELPER = True\n')
        if fault == 'unknown_committed':
            c.committed[dependency] = path.read_bytes()
    expected = ('missing' if fault in {'missing', 'symlink'} else
                'dirty' if fault == 'dirty_git' else 'unreviewed')
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_' + expected):
        c.verify()


def test_generation_closures_are_separate_and_every_dependency_is_git_bound(candidate):
    c = candidate
    assert len(c.dependencies) == (2 if c.generation == 'historical_9d' else 59)
    for name, expected in c.dependencies.items():
        assert hashlib.sha256(c.committed[name]).hexdigest() == expected
        assert c.committed[name] == REAL_GIT(['git', '-C', str(ROOT), 'show', c.commit+':'+name])
    assert c.verify() == [TRIGGER]


def test_normalized_trigger_checks_closure_even_when_handler_is_unchanged(candidate):
    c = candidate
    c.original[TRIGGER] = c.committed[TRIGGER]
    alias = 'src/engine/scalping/../sniper_state_handlers.py'
    assert c.verify(alias=alias) == []
    (c.root / next(iter(c.dependencies))).unlink()
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_missing'):
        c.verify(alias=alias)


def test_old_handler_has_no_new_dependency_requirement(candidate):
    c = candidate
    c.committed[TRIGGER] = c.original[TRIGGER]
    (c.root / TRIGGER).write_bytes(c.original[TRIGGER])
    for dependency in c.dependencies:
        (c.root / dependency).unlink()
    assert c.verify() == []


def test_old_handler_cannot_authorize_an_unknown_successor(candidate):
    c = candidate
    c.committed[TRIGGER] = c.original[TRIGGER] + b'\nUNREVIEWED_RUNTIME_AUTHORITY = True\n'
    (c.root / TRIGGER).write_bytes(c.committed[TRIGGER])
    with pytest.raises(ValueError, match='entry_consumer_unreviewed_change'):
        c.verify()


def test_prepared_verify_reexecutes_native_dependency_guard(prepared, candidate, monkeypatch):
    data, root, args, actual, receipt, pp = prepared
    c = candidate
    calls = []
    def guard(*unused):
        calls.append(True)
        return c.verify()
    monkeypatch.setattr(H, '_verify_entry_code_delta', guard)
    assert C.verify(data, '2026-10-19', **args, actual=actual)['actual_pid_consumed'] is False
    (c.root / next(iter(c.dependencies))).write_bytes(b'unknown source\n')
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_unreviewed'):
        C.verify(data, '2026-10-19', **args, actual=actual)
    assert len(calls) == 2
