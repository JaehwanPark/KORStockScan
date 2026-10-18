"""Reviewed integration binds source-only dependencies without new policy authority."""
import hashlib
import json
from pathlib import Path

import pytest
from src.engine.automation import intraday_release_handoff as H
from src.engine.automation import prepared_policy_code_handoff as C
from src.tests.test_prepared_policy_code_handoff import prepared

ORIGIN = '7f2552aedde8fec6ef904a43105827907e50dfc8'
CANDIDATE = 'c' * 40
OWN = 'src/engine/automation/intraday_release_handoff.py'
TRIGGER = 'src/engine/sniper_state_handlers.py'
ROOT = Path(H.__file__).resolve().parents[3]
NATIVE_VERIFY = H._verify_entry_code_delta
REAL_GIT = H.subprocess.check_output
DEPENDENCIES = next(iter(H.REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[TRIGGER].values()))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    """Current source projection with real historical Git bytes; no receipt issuance."""
    root = tmp_path / 'source'
    names = {OWN, *H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES, *DEPENDENCIES}
    committed = {name: (ROOT / name).read_bytes() for name in names}
    for name, raw in committed.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    original = {name: REAL_GIT(['git', '-C', str(ROOT), 'show', ORIGIN + ':' + name])
                for name in H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES}
    def revision(command, **kwargs):
        ref, name = command[-1].split(':', 1)
        return committed[name] if ref == CANDIDATE else original[name]
    monkeypatch.setattr(H.subprocess, 'check_output', revision)
    def verify(name=TRIGGER, *, alias=None):
        path_name = alias or name
        expected = digest({name: hashlib.sha256(original[name]).hexdigest()})
        return NATIVE_VERIFY(root, CANDIDATE, ORIGIN, {name: path_name}, expected)
    return root, committed, original, verify


@pytest.mark.parametrize('name', H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES)
def test_real_reviewed_pairs_preserve_exact_original_and_integrated_sources(candidate, name):
    root, committed, original, verify = candidate
    pair = H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES[name]
    assert tuple(hashlib.sha256(raw).hexdigest() for raw in (original[name], committed[name])) == pair
    before = {str(path): path.read_bytes() for path in root.rglob('*.py')}
    assert verify(name) == [name]
    assert before == {str(path): path.read_bytes() for path in root.rglob('*.py')}


@pytest.mark.parametrize('name', H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES)
@pytest.mark.parametrize('dirty', [False, True])
def test_reviewed_source_pairs_reject_unknown_committed_or_dirty_bytes(candidate, name, dirty):
    root, committed, original, verify = candidate
    path = root / name
    path.write_bytes(path.read_bytes() + b'\nUNKNOWN_INTEGRATION = True\n')
    if not dirty:
        committed[name] = path.read_bytes()
    with pytest.raises(ValueError, match=('dirty_release' if dirty else 'unreviewed_change|producer_changed')):
        verify(name)


@pytest.mark.parametrize('dependency', DEPENDENCIES)
@pytest.mark.parametrize('fault', ['missing', 'symlink', 'unknown_committed', 'dirty_git', 'reverify'])
def test_native_handoff_rechecks_helper_and_provenance_closure(candidate, dependency, fault):
    root, committed, original, verify = candidate
    assert verify() == [TRIGGER]
    path = root / dependency
    if fault == 'missing':
        path.unlink()
    elif fault == 'symlink':
        target = path.with_suffix('.saved')
        path.rename(target)
        path.symlink_to(target)
    elif fault == 'dirty_git':
        committed[dependency] += b'\nUNCOMMITTED_SOURCE = True\n'
    else:
        path.write_bytes(path.read_bytes() + b'\nUNKNOWN_HELPER = True\n')
        if fault == 'unknown_committed':
            committed[dependency] = path.read_bytes()
    expected = ('missing' if fault in {'missing', 'symlink'} else
                'dirty' if fault == 'dirty_git' else 'unreviewed')
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_' + expected):
        verify()


def test_normalized_trigger_checks_closure_even_when_handler_is_unchanged(candidate):
    root, committed, original, verify = candidate
    original[TRIGGER] = committed[TRIGGER]
    alias = 'src/engine/scalping/../sniper_state_handlers.py'
    assert verify(alias=alias) == []
    (root / next(iter(DEPENDENCIES))).unlink()
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_missing'):
        verify(alias=alias)


def test_old_handler_has_no_new_dependency_requirement(candidate):
    root, committed, original, verify = candidate
    committed[TRIGGER] = original[TRIGGER]
    (root / TRIGGER).write_bytes(original[TRIGGER])
    for dependency in DEPENDENCIES:
        (root / dependency).unlink()
    assert verify() == []


def test_prepared_verify_reexecutes_native_dependency_guard(prepared, candidate, monkeypatch):
    data, root, args, actual, receipt, pp = prepared
    code_root, committed, original, native = candidate
    calls = []
    def guard(*unused):
        calls.append(True)
        return native()
    monkeypatch.setattr(H, '_verify_entry_code_delta', guard)
    assert C.verify(data, '2026-10-19', **args, actual=actual)['actual_pid_consumed'] is False
    (code_root / next(iter(DEPENDENCIES))).write_bytes(b'unknown source\n')
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_unreviewed'):
        C.verify(data, '2026-10-19', **args, actual=actual)
    assert len(calls) == 2
