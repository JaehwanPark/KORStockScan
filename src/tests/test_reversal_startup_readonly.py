"""Cold native policy inspection keeps the mandatory OS isolation intact."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def guarded_child(tmp_path, body):
    """Each real kernel-isolated child starts before importing policy modules."""
    run = tmp_path / 'guarded-child'
    run.mkdir(mode=0o700)
    script = '''import json, sys
from pathlib import Path
sys.path.insert(0, ROOT)
from src.engine.infrastructure.startup_validation_isolation import install_validation_isolation, assert_no_forbidden_attempts
run = Path(RUN)
install_validation_isolation(run, run/'isolation.jsonl')
'''.replace('ROOT', repr(str(ROOT))).replace('RUN', repr(str(run)))
    script += body + "\nassert_no_forbidden_attempts()\n"
    result = subprocess.run([sys.executable, '-I', '-B', '-c', script], cwd=ROOT,
        env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1',
             'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1'},
        start_new_session=True, close_fds=True, capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, (result.stdout, result.stderr, (run/'isolation.jsonl').read_text())
    assert (run/'isolation.jsonl').read_bytes() == b''
    return json.loads((run/'result.json').read_text()) if (run/'result.json').exists() else None


def test_cold_v6_inventory_and_transition_hashes_never_import_execution_modules(tmp_path):
    result = guarded_child(tmp_path, '''
from src.engine.scalping import continuous_reversal_policy_v6 as V
from src.engine.scalping import reversal_auxiliary_input_transition as T
modules = V.contract_modules()
code = T.code_hashes()
for forbidden in ('requests', 'src.utils.kiwoom_utils', 'src.engine.kiwoom_orders',
                  'src.engine.sniper_config', 'src.engine.ai_engine_openai',
                  'src.engine.scalping.ai_decision_quality'):
    assert forbidden not in sys.modules, forbidden
(run/'result.json').write_text(json.dumps(dict(paths=[m.__file__ for m in modules], code=code)))
''')
    assert 'entry_machine_source_recovery.py' in {Path(p).name for p in result['paths']}
    assert set(result['code']) == {
        'reversal_auxiliary_input_transition.py', 'reversal_auxiliary_registry.py',
        'reversal_auxiliary_tuning.py', 'reversal_auxiliary_research.py',
        'reversal_auxiliary_risk_role_experiment.py', 'reversal_auxiliary_production_input.py',
        'reversal_auxiliary_wire.py', 'reversal_cumulative_postclose.py',
        'reversal_auxiliary_transition.py', 'ai_decision_quality.py', 'ai_engine_openai.py'}
    for name, digest in result['code'].items():
        path = ROOT/'src/engine'/name if name == 'ai_engine_openai.py' else ROOT/'src/engine/scalping'/name
        assert digest == hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_recovery_actual_route_reader_is_still_the_native_function(monkeypatch):
    from src.engine.scalping import entry_machine_source_recovery as R
    from src.engine.scalping import ai_market_snapshot as M
    calls = []
    ws, context = {}, {}
    monkeypatch.setattr(M, 'route_partitioned_ws_view', lambda *args: (calls.append(args), {'used': False}))
    assert R.select_prepared_route('005930', ws, context) is ws
    assert calls == [(ws, context)]


def _raw(root, *, incomplete=False):
    day = '2026-10-13'
    path = root/'observations/scalp_micro_reversion_forward'/f'trade_date={day}/venue=SOR/session=KRX_REGULAR/market_stream.jsonl'
    path.parent.mkdir(parents=True)
    dt = '2026-10-13T09:01:00+09:00'
    row = dict(schema='scalp_micro_reversion_market_stream_point_v3', symbol='005930', venue='SOR',
        session_bucket='KRX_REGULAR', source_item='005930_AL', trade_price=10000,
        local_receive_timestamp=dt, exchange_timestamp=dt, sequence_epoch=99, series_sequence=1,
        native_transport_epoch=7, native_route_sequence=1, path_consumer_eligible=True, path_order_status='accept')
    path.write_text(json.dumps(row)+'\n'+('{"partial"' if incomplete else ''))
    return day, path, [datetime.fromisoformat(dt).timestamp(), 7, 1, 10000]


@pytest.mark.parametrize('incomplete', [False, True])
def test_read_only_anchor_restore_preserves_original_prefix_without_saving(tmp_path, incomplete):
    root = tmp_path/'data'
    day, source, expected = _raw(root, incomplete=incomplete)
    before = source.read_bytes()
    result = guarded_child(tmp_path, f'''
from src.engine.scalping import reversal_path_runtime as R
from src.engine.scalping import reversal_anchor_index as I
result = R.restore_session_anchors(Path({str(root)!r}), {day!r}, read_only=True)
assert not I.location(Path({str(root)!r}), {day!r}).exists()
assert R._ANCHORS[('005930', 'SOR', '005930_AL', 'REGULAR', {day!r})] == {expected!r}
assert ({day!r} in R._RESTORED_DAYS) is {not incomplete!r}
(run/'result.json').write_text(json.dumps(result))
''')
    assert result['status'] == ('prefix_incomplete' if incomplete else 'restored')
    assert result['bytes_read'] > 0
    assert source.read_bytes() == before
    assert not (root/'runtime').exists()


def test_read_only_anchor_restore_rejects_corrupt_cached_index(tmp_path):
    from src.engine.scalping import reversal_anchor_index as I
    root = tmp_path/'data'
    target = I.location(root, '2026-10-13')
    target.parent.mkdir(parents=True)
    target.write_text('{}')
    guarded_child(tmp_path, f'''
from src.engine.scalping import reversal_path_runtime as R
try:
    R.restore_session_anchors(Path({str(root)!r}), '2026-10-13', read_only=True)
except ValueError as e:
    assert str(e) == 'session_anchor_index_contract_invalid'
else:
    raise AssertionError('corrupt source accepted')
''')
    assert target.read_text() == '{}'


def test_live_anchor_default_still_publishes_native_index(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import reversal_anchor_index as I
    root = tmp_path/'data'
    day, _, expected = _raw(root)
    for name in ('_STATES', '_ANCHORS', '_ANCHOR_CURSORS', '_ANCHOR_ROOTS'):
        monkeypatch.setattr(R, name, {})
    for name in ('_RESTORED_DAYS', '_EMPTY_PREFIX_DAYS', '_ANCHOR_GAPS'):
        monkeypatch.setattr(R, name, set())
    assert R.restore_session_anchors(root, day)['status'] == 'restored'
    assert I.load(root, day)[0][('005930', 'SOR', '005930_AL', 'REGULAR', day)] == expected


def test_transition_source_hashes_retain_exact_paths_and_detect_changed_provider_bytes(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_auxiliary_input_transition as T
    expected = T.code_hashes()
    package = tmp_path/'engine/scalping'
    package.mkdir(parents=True)
    for name in ('reversal_auxiliary_input_transition.py', 'ai_decision_quality.py'):
        (package/name).write_bytes((ROOT/'src/engine/scalping'/name).read_bytes())
    provider = package.parent/'ai_engine_openai.py'
    provider.write_bytes((ROOT/'src/engine/ai_engine_openai.py').read_bytes())
    monkeypatch.setattr(T, '__file__', str(package/'reversal_auxiliary_input_transition.py'))
    assert T.code_hashes() == expected
    provider.write_bytes(provider.read_bytes()+b'\n# changed immutable source fixture\n')
    changed = T.code_hashes()
    assert {key for key in expected if changed[key] != expected[key]} == {'ai_engine_openai.py'}
    assert changed['ai_engine_openai.py'] == hashlib.sha256(provider.read_bytes()).hexdigest()


@pytest.mark.parametrize('read_only', [False, True])
def test_read_only_and_live_reject_same_combined_index_budget(tmp_path, monkeypatch, read_only):
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import reversal_anchor_index as I
    root = tmp_path/'data'
    day, raw, expected = _raw(root)
    # The original index is small enough to read. The original valid prefix
    # plus its newly observed anchor/cursor exceeds the same native save limit.
    old = {'original-source': dict(inode=1, bytes=1, offset=0, retained='x'*2000)}
    I.save(root, day, {}, old)
    saved = I.location(root, day)
    original = saved.read_bytes()
    monkeypatch.setattr(I, 'LIMIT', len(original)+100)
    assert raw.stat().st_size < I.LIMIT
    for name in ('_STATES', '_ANCHORS', '_ANCHOR_CURSORS', '_ANCHOR_ROOTS'):
        monkeypatch.setattr(R, name, {})
    for name in ('_RESTORED_DAYS', '_EMPTY_PREFIX_DAYS', '_ANCHOR_GAPS'):
        monkeypatch.setattr(R, name, set())
    with pytest.raises(ValueError, match='session_anchor_index_budget_exceeded'):
        R.restore_session_anchors(root, day, read_only=read_only)
    assert R._ANCHORS[('005930', 'SOR', '005930_AL', 'REGULAR', day)] == expected
    assert saved.read_bytes() == original


def test_read_only_restore_preserves_existing_native_index_bytes(tmp_path):
    from src.engine.scalping import reversal_anchor_index as I
    root = tmp_path/'data'
    day, _, expected = _raw(root)
    key = ('005930', 'SOR', '005930_AL', 'REGULAR', day)
    I.save(root, day, {key: expected}, {})
    before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    guarded_child(tmp_path, f"""
from src.engine.scalping import reversal_path_runtime as R
assert R.restore_session_anchors(Path({str(root)!r}), {day!r}, read_only=True)['status'] == 'restored'
assert R._ANCHORS[{key!r}] == {expected!r}
""")
    assert {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()} == before
