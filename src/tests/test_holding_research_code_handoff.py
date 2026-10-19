"""Reviewed generations retain exact source closure without new policy authority."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from src.engine.automation import intraday_release_handoff as H
from src.engine.automation import prepared_policy_code_handoff as C
from src.engine.scalping.main_stop_policy import implementation_paths
from src.engine.scalping.holding_vote_experiment import _code_paths
from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS
from src.tests.test_prepared_policy_code_handoff import prepared  # noqa: F401 -- shared pytest fixture

ORIGIN = '7f2552aedde8fec6ef904a43105827907e50dfc8'
OWN = 'src/engine/automation/intraday_release_handoff.py'
TRIGGER = 'src/engine/sniper_state_handlers.py'
ROOT = Path(H.__file__).resolve().parents[3]
NATIVE_VERIFY = H._verify_entry_code_delta
REAL_GIT = H.subprocess.check_output
FAMILY_PATHS = {
    'pre_submit_delay': {name: name for name in CONTRACT_PATHS},
    'main_stop': {name: 'src/engine/'+name for name in implementation_paths()},
    'holding_vote': {name: 'src/engine/'+name for name in _code_paths()},
}
ORIGINAL_DIGESTS = {
    'pre_submit_delay': 'bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256',
    'main_stop': '687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533',
    'holding_vote': '6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112',
}
GENERATIONS = {
    'historical_9d': '9d2201141aeae409fe960ff7795a1340718a7146',
    'historical_a8': 'a8f063105bbb1d8a3676e55ad5377990a87594df',
    'historical_8a8': '8a8fd0ba1845a69b0a829f5c4bcd551a602aea7e',
    'completed_current': '958d35b2b03f0a37462c1c0121fc14c108e709b8',  # frozen 76-source parent
}
PAIRS = {
    'historical_9d': H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES,
    'completed_current': {**H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES,
                          **H.REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES,
                          **H.REVIEWED_RESEARCH_BUDGET_INTEGRATION_SOURCES},
}
PAIRS['historical_a8'] = dict(PAIRS['completed_current'])
PAIRS['historical_8a8'] = {**PAIRS['completed_current'],
    'src/engine/automation/pre_submit_delay_partitioned_research.py':
        H.REVIEWED_DELAY_RESEARCH_SOURCES['src/engine/automation/pre_submit_delay_partitioned_research.py']}
PAIRS['completed_current'].update(H.REVIEWED_DELAY_PARENT_VERIFICATION_SOURCES)
DEPENDENCIES = {
    generation: H.REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[TRIGGER][pairs[TRIGGER][1]]
    for generation, pairs in PAIRS.items()
}
READONLY_VARIANT = H.REVIEWED_STARTUP_READONLY_DEPENDENCY_VARIANTS[(TRIGGER, PAIRS['completed_current'][TRIGGER][1])]
PARENT_VARIANT = H.REVIEWED_DELAY_PARENT_VERIFICATION_DEPENDENCY_VARIANTS[(TRIGGER, PAIRS['completed_current'][TRIGGER][1])]
DEPENDENCIES['historical_8a8'] = READONLY_VARIANT['dependencies']
DEPENDENCIES['completed_current'] = PARENT_VARIANT['dependencies']
# Every positive verification checks the full closure. Negative probes cover
# each old dependency plus distinct new source, cost and startup helper roles.
DEPENDENCY_CASES = {
    'historical_9d': tuple(DEPENDENCIES['historical_9d']),
    'historical_a8': ('src/engine/infrastructure/main_policy_loading.py',
                      'src/engine/scalping/reversal_evaluation_context.py'),
    'historical_8a8': ('src/engine/infrastructure/startup_validation_code_context.py',),
    'completed_current': (*DEPENDENCIES['historical_9d'],
        'src/engine/scalping/main_stop_runtime_source.py',
        'src/engine/lifecycle/holding_research_cost.py',
        'src/engine/infrastructure/main_prompt_policy_loading.py',
        'src/engine/lifecycle/research_input_budget.py',
        'src/engine/infrastructure/main_policy_loading.py',
        'src/engine/scalping/reversal_evaluation_context.py',
        'src/engine/scalping/reversal_anchor_index.py',
        'src/engine/infrastructure/startup_validation_code_context.py',
        'src/engine/automation/main_startup_validation.py',
        'src/engine/automation/auxiliary_reader_readiness.py',
        'src/engine/scalping/continuous_reversal_policy_v6.py',
        'src/engine/scalping/reversal_auxiliary_source_handoff.py',
        'src/engine/automation/pre_submit_delay_partitioned_research.py'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()


@pytest.fixture(params=tuple(GENERATIONS))
def candidate(tmp_path, monkeypatch, request):
    """Use exact historical Git objects; current cleanup has its own native fixture."""
    generation = request.param
    commit = GENERATIONS[generation]
    pairs = PAIRS[generation]
    dependencies = DEPENDENCIES[generation]
    root = tmp_path / 'source'
    names = {OWN, *pairs, *dependencies}
    if generation != 'historical_9d':
        names.update(os.path.normpath(name) for paths in FAMILY_PATHS.values() for name in paths.values())
    git_root=ROOT
    # Current verifier checks newer selectors before choosing a historical
    # closure. Supply their real historical bytes if that Git tree owns them.
    owned = set(REAL_GIT(['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', commit], text=True).splitlines())
    for name, variants in vars(H).items():
        if name.endswith('_DEPENDENCY_VARIANTS'):
            names.update(v['selector_path'] for v in variants.values() if v['selector_path'] in owned)
    committed = {name: REAL_GIT(['git', '-C', str(git_root), 'show', commit+':'+name])
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
            if name not in committed:
                raise subprocess.CalledProcessError(128, command)
            return committed[name]
        assert ref == ORIGIN
        if name not in original:
            original[name] = REAL_GIT(['git', '-C', str(ROOT), 'show', ORIGIN+':'+name])
        return original[name]
    monkeypatch.setattr(H.subprocess, 'check_output', revision)
    def verify(name=TRIGGER, *, alias=None):
        path_name = alias or name
        expected = digest({name: hashlib.sha256(original[name]).hexdigest()})
        return NATIVE_VERIFY(root, commit, ORIGIN, {name: path_name}, expected)
    return SimpleNamespace(root=root, committed=committed, original=original, verify=verify,
        pairs=pairs, dependencies=dependencies, generation=generation, commit=commit,git_root=git_root)


@pytest.mark.parametrize('candidate,name', [
    (generation, name) for generation, pairs in PAIRS.items() for name in pairs
], indirect=['candidate'])
def test_real_reviewed_pairs_preserve_exact_original_and_integrated_sources(candidate, name):
    c = candidate
    pair = c.pairs[name]
    assert tuple(hashlib.sha256(raw).hexdigest() for raw in (c.original[name], c.committed[name])) == pair
    assert c.committed[name] == REAL_GIT(['git', '-C', str(c.git_root), 'show', c.commit+':'+name])
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
    assert len(c.dependencies) == {'historical_9d': 2, 'historical_a8': 59,
                                   'historical_8a8': 75, 'completed_current': 76}[c.generation]
    for name, expected in c.dependencies.items():
        assert hashlib.sha256(c.committed[name]).hexdigest() == expected
        assert c.committed[name] == REAL_GIT(['git', '-C', str(c.git_root), 'show', c.commit+':'+name])
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


@pytest.mark.parametrize('candidate', ['historical_a8', 'historical_8a8', 'completed_current'], indirect=True)
@pytest.mark.parametrize('family', tuple(FAMILY_PATHS))
def test_native_three_family_inventories_preserve_original_digests(candidate, family):
    c = candidate
    paths = FAMILY_PATHS[family]
    assert len(paths) == {'pre_submit_delay': 28, 'main_stop': 44, 'holding_vote': 23}[family]
    before = {name: (c.root/name).read_bytes() for name in c.committed}
    changed = NATIVE_VERIFY(c.root, c.commit, ORIGIN, paths, ORIGINAL_DIGESTS[family])
    assert TRIGGER in changed
    assert before == {name: (c.root/name).read_bytes() for name in c.committed}


@pytest.mark.parametrize('candidate', ['historical_8a8', 'completed_current'], indirect=True)
def test_readonly_delay_extension_requires_its_complete_generation(candidate):
    c = candidate
    expected = ORIGINAL_DIGESTS['pre_submit_delay']
    name = 'src/engine/infrastructure/main_policy_loading.py'
    old = H.REVIEWED_DELAY_CONTRACT_EXTENSIONS[(ORIGIN, expected)][name]
    assert old == 'da58eb3fc403b5117cba011d6bb92f6e15790248d181ada4b73b263d38e073db'
    assert READONLY_VARIANT['contract_extensions'][(ORIGIN, expected)][name] == hashlib.sha256(c.committed[name]).hexdigest()
    assert name in NATIVE_VERIFY(c.root, c.commit, ORIGIN, FAMILY_PATHS['pre_submit_delay'], expected)
    selector = READONLY_VARIANT['selector_path']
    old_context = REAL_GIT(['git', '-C', str(ROOT), 'show', GENERATIONS['historical_a8']+':'+selector])
    (c.root/selector).write_bytes(old_context)
    c.committed[selector] = old_context
    error = ('entry_consumer_reviewed_dependency_unreviewed' if c.generation == 'completed_current'
             else 'entry_consumer_contract_extension_unreviewed')
    with pytest.raises(ValueError, match=error):
        NATIVE_VERIFY(c.root, c.commit, ORIGIN, FAMILY_PATHS['pre_submit_delay'], expected)


@pytest.mark.parametrize('candidate', ['completed_current'], indirect=True)
@pytest.mark.parametrize('name', [
    'src/engine/infrastructure/main_policy_loading.py',
    'src/engine/scalping/reversal_evaluation_context.py',
    'src/engine/scalping/entry_machine_source_recovery.py',
    'src/engine/scalping/reversal_anchor_index.py',
    'src/engine/automation/main_startup_validation.py',
    'src/engine/infrastructure/startup_validation_code_context.py',
])
def test_readonly_variant_rejects_mixed_reviewed_generations(candidate, name):
    c = candidate
    assert c.verify() == [TRIGGER]
    old = REAL_GIT(['git', '-C', str(ROOT), 'show', GENERATIONS['historical_a8']+':'+name])
    assert old != c.committed[name]
    (c.root/name).write_bytes(old)
    c.committed[name] = old
    # Both generations are individually reviewed. Combining their files must
    # still fail the one complete dependency map selected by the context.
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_unreviewed'):
        c.verify()


@pytest.mark.parametrize('candidate', ['completed_current'], indirect=True)
@pytest.mark.parametrize('name', [
    'src/engine/infrastructure/startup_validation_code_context.py',
    'src/engine/automation/pre_submit_delay_partitioned_research.py',
])
def test_parent_validation_variant_rejects_mixed_original_readonly_generation(candidate, name):
    c = candidate
    assert c.verify() == [TRIGGER]
    assert hashlib.sha256(c.committed[READONLY_VARIANT['selector_path']]).hexdigest() == READONLY_VARIANT['selector_sha256']
    assert hashlib.sha256(c.committed[PARENT_VARIANT['selector_path']]).hexdigest() == PARENT_VARIANT['selector_sha256']
    old = REAL_GIT(['git', '-C', str(ROOT), 'show', GENERATIONS['historical_8a8']+':'+name])
    assert old != c.committed[name]
    (c.root/name).write_bytes(old)
    c.committed[name] = old
    # Either selector is reviewed on its own. Neither a new validation owner with
    # the old context nor an old validation owner with the new context may pass.
    with pytest.raises(ValueError, match='entry_consumer_reviewed_dependency_unreviewed'):
        c.verify()
