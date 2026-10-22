"""Native Main extraction parity; no bootstrap, transport or order execution."""
import ast
from copy import deepcopy
import hashlib
import inspect
import symtable

import pytest

from src.engine import kiwoom_sniper_v2 as main


# The loop's immutable input is 9e78afd1194233d87c4d340ba2f1981d340d88d4.
# The reviewed 105f6f031 startup includes native policy loading and the already
# deployed bounded local depth sampler. Preserve that exact baseline here.
# Re-inlining the unchanged loop must match that commit's entire run_sniper,
# including its early returns and original exception/cleanup boundary.
# These are AST hashes, independent of indentation, comments and line numbers.
ORIGINAL_LOOP_AST = 'a549e790d27ed4e4b86a14cfb46187cfec7dcee51f1fa869a84195e3f3dc04a5'
INTEGRATED_RUN_AST = '06fcd035cd24da039bf1123b4435475faf6e8c45f2ff4781e483e6462039ec4d'
STARTUP_BINDINGS = {
    'is_test_mode', 'targets', 'admin_id', 'radar', 'ai_engine',
    'last_db_poll_time', 'last_msg_min', 'scanner_ws_reg_last_emit_ts',
    'scanner_ws_repair_cycle_state_by_code', 'log_error', 'log_info',
}


def _digest(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def _native_loop():
    function = ast.parse(inspect.getsource(main._run_sniper_iterations)).body[0]
    assert len(function.body) == 2  # docstring, original loop
    loop = deepcopy(function.body[1])
    assert isinstance(loop, ast.While)
    assert ast.unparse(loop.test) == 'not shutdown_requested()'
    loop.test = ast.Constant(value=True)
    restart = next(n for n in loop.body if isinstance(n, ast.If)
                   and ast.unparse(n.test) == 'RESTART_FLAG_PATH.exists()')
    index = next(i for i, n in enumerate(restart.body) if ast.unparse(n) == 'request_shutdown()')
    restart.body[index:index+1] = ast.parse("""
from src.utils.pipeline_event_logger import drain_pipeline_event_summary_before_termination
drain_pipeline_event_summary_before_termination()
os.kill(os.getpid(), signal.SIGTERM)
""").body
    marker = loop.body.pop()
    assert isinstance(marker, ast.Expr) and isinstance(marker.value, ast.Yield)
    assert isinstance(marker.value.value, ast.Constant) and marker.value.value.value is None
    return loop


def test_native_iteration_body_is_original_loop_including_nested_scopes_and_literals():
    assert _digest(_native_loop()) == ORIGINAL_LOOP_AST
    assert main._run_sniper_iterations.__code__.co_freevars == ()
    symbols = symtable.symtable(inspect.getsource(main._run_sniper_iterations),
                               '<native-main>', 'exec').get_children()[0]
    assert set(symbols.get_parameters()) == STARTUP_BINDINGS
    assert {s.get_name() for s in symbols.get_symbols() if s.is_declared_global()} == {
        '_LOOP_METRICS_LAST_LOG_TS'}


def test_shutdown_successor_preserves_consumed_native_loop_and_startup_body():
    import subprocess
    from pathlib import Path
    source=subprocess.check_output(['git','show','70fc572f8:src/engine/kiwoom_sniper_v2.py'],
        cwd=Path(main.__file__).resolve().parents[2],text=True)
    old={n.name:n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    current=ast.parse(inspect.getsource(main._run_sniper_iterations)).body[0]
    assert _digest(current)==_digest(old['_run_sniper_iterations'])
    current=ast.parse(inspect.getsource(main.run_sniper)).body[0]
    current.body=[n for n in current.body if not (isinstance(n,ast.Expr)
        and isinstance(n.value,ast.Call) and ast.unparse(n.value)=='_ZERO_BASE_PROBE_CLOSING.clear()')]
    parent=next(n for n in current.body if isinstance(n,ast.Try)
        and any(isinstance(c,ast.For) for c in n.body))
    close=parent.finalbody[0]
    close.finalbody=[close.finalbody[0].finalbody[0]]
    assert _digest(current)==_digest(old['run_sniper'])


@pytest.mark.parametrize('drained',[False,True])
def test_native_shutdown_executes_drain_then_socket_then_sources(drained):
    function=ast.parse(inspect.getsource(main.run_sniper)).body[0]
    parent=next(n for n in function.body if isinstance(n,ast.Try)
        and any(isinstance(c,ast.For) for c in n.body))
    cleanup=parent.finalbody[0].finalbody[0]
    calls=[]
    class Manager:
        def stop(self):calls.append('socket');return True
    context=dict(_drain_zero_base_probe_leases=lambda:calls.append('probe') or drained,
        WS_MANAGER=Manager(),close_observation_sources=lambda:calls.append('sources'))
    code=compile(ast.Module(body=[cleanup],type_ignores=[]),'<native-cleanup>','exec')
    if drained:exec(code,context)
    else:
        with pytest.raises(RuntimeError,match='zero_base_probe_shutdown_incomplete'):exec(code,context)
    assert calls==['probe','socket','sources']


def test_live_startup_consumes_native_iterator_with_original_exception_and_cleanup_boundary():
    function = ast.parse(inspect.getsource(main.run_sniper)).body[0]
    parent = next(node for node in function.body if isinstance(node, ast.Try)
                  and any(isinstance(child, ast.For) and isinstance(child.iter, ast.Call)
                          and isinstance(child.iter.func, ast.Name)
                          and child.iter.func.id == '_run_sniper_iterations'
                          for child in node.body))
    idx = next(i for i, node in enumerate(parent.body) if isinstance(node, ast.For))
    invocation = parent.body[idx]
    assert invocation.body and all(isinstance(node, ast.Pass) for node in invocation.body)
    assert not invocation.orelse
    assert not invocation.iter.args
    assert {kw.arg for kw in invocation.iter.keywords} == STARTUP_BINDINGS
    assert all(isinstance(kw.value, ast.Name) and kw.value.id == kw.arg
               for kw in invocation.iter.keywords)
    # Replacing only the invocation with the original body reconstructs the
    # whole pre-refactor function: startup, continue/break, catches and cleanup.
    parent.body[idx] = _native_loop()
    # Prove the new nested finally guarantees both cleanup owners, then restore
    # only that reviewed shutdown delta for the original trading-body parity.
    shutdown = parent.finalbody[0]
    assert len(parent.finalbody) == 1 and isinstance(shutdown, ast.Try)
    probe_close = shutdown.finalbody[0]
    assert ast.unparse(probe_close.body[0].test) == 'not _drain_zero_base_probe_leases()'
    source_close = probe_close.finalbody[0]
    assert isinstance(source_close, ast.Try)
    assert ast.unparse(source_close.finalbody[0]) == 'close_observation_sources()'
    assert ast.unparse(source_close.body[0].test) == 'WS_MANAGER and WS_MANAGER.stop() is False'
    # Restore the sole startup admission reset before comparing native trading.
    function.body = [node for node in function.body if not (
        isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and ast.unparse(node.value) == '_ZERO_BASE_PROBE_CLOSING.clear()')]
    parent.finalbody = shutdown.body + ast.parse("""
close_observation_sources()
if WS_MANAGER:
    try:
        WS_MANAGER.stop()
    except Exception as e:
        log_error(f"WS manager stop failed: {e}")
""").body
    cleanup = next(node for node in parent.finalbody if isinstance(node, ast.Expr)
                   and isinstance(node.value, ast.Call)
                   and ast.unparse(node.value) == 'close_observation_sources()')
    # The old inline cleanup is consolidated into the shared termination owner.
    # Restore just that former block to keep the original whole-function proof.
    old_cleanup = ast.parse('''
from src.engine.scalping.pre_submit_delay_observation import shutdown as close_delay_observations
close_delay_observations()
from src.engine.scalping.initial_quantity_cap_observation import configure_sink as configure_quantity_sink
configure_quantity_sink(None)
from src.engine.scalping.main_stop_policy import configure_source_sink as configure_stop_sink
configure_stop_sink(None)
from src.engine.scalping.reversal_anchor_index import configure_sink as configure_anchor_sink
configure_anchor_sink(None)
_SCANNER_OBSERVATION_QUEUE.close(timeout=1.0)
''').body
    offset = parent.finalbody.index(cleanup)
    parent.finalbody[offset:offset+1] = old_cleanup
    assert _digest(function) == INTEGRATED_RUN_AST


@pytest.fixture
def isolated_observation_shutdown(monkeypatch):
    from collections import Counter, OrderedDict
    from src.engine.scalping import pre_submit_delay_observation as owner
    from src.engine.scalping import initial_quantity_cap_observation as quantity
    from src.engine.scalping import main_stop_policy as stop
    from src.engine.scalping import reversal_anchor_index as anchor
    for name, value in dict(_ACTIVE={}, _HEAPS={}, _EXPIRIES=[], _RECENT=OrderedDict(),
            _COUNTERS=Counter(), _CLOSING=False, _CLOSED_AT=None, _SINK=None, _SAMPLER=None).items():
        monkeypatch.setattr(owner, name, value)
    monkeypatch.setattr(quantity, 'configure_sink', lambda *a: None)
    monkeypatch.setattr(stop, 'configure_source_sink', lambda *a: None)
    monkeypatch.setattr(anchor, 'configure_sink', lambda *a: None)
    return owner


@pytest.mark.parametrize('offset,missing,censored', [(61,0,2), (160,1,1)])
def test_native_restart_cleanup_reaches_raw_compact_summary_and_missing_guard(
        monkeypatch, tmp_path, isolated_observation_shutdown, offset, missing, censored):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import timedelta
    import json
    from types import SimpleNamespace
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    from src.engine.pipeline_event_summary import ProducerSummaryCompactor
    from src.tests.test_submission_bottleneck_monitor import _delay_semantic_fixture
    from src.utils import pipeline_event_logger as logger
    owner = isolated_observation_shutdown
    producer = ProducerSummaryCompactor(summary_dir=tmp_path/'pipeline_event_summaries', mode='shadow')
    started, _ = _delay_semantic_fixture(tmp_path, grid=True, record_id=None, writer=producer,
        quote_horizons=(0,1,3,5,30,60))
    monkeypatch.setattr(logger, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(logger, 'TRADING_RULES', SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True))
    monkeypatch.setattr(logger, 'log_info', lambda *a, **k: None)
    monkeypatch.setattr(logger, '_PRODUCER_COMPACTOR', producer)
    monkeypatch.setattr(logger, '_RETIRING_COMPACTORS', [])
    monkeypatch.setattr(logger, '_TERMINATION_DRAIN_ACTIVE', False)
    monkeypatch.setattr(owner.time, 'time', lambda: started.timestamp()+offset)
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = logger.BoundedObservationQueue(executor)
        monkeypatch.setattr(main, '_SCANNER_OBSERVATION_QUEUE', queue)
        owner.configure_sink(queue.submit)
        assert owner.register('005930', dict(id='source-intent', committed_at_epoch=started.timestamp(),
            remaining_sec=[120,180], decision_source_sha256='a'*64))
        logger.drain_pipeline_event_summary_before_termination()
        assert queue.snapshot()['pending_items'] == 0
        assert owner.health()['active'] == 0
    rows = [json.loads(line) for p in (tmp_path/'pipeline_events').glob('*.jsonl')
            for line in p.read_text().splitlines()]
    terminal = next(row for row in rows if row['stage']=='pre_submit_delay_intent_terminal')
    assert terminal['fields']['terminal_finished_at_epoch'] == str(started.timestamp()+offset)
    result = monitor.pre_submit_delay_source_semantics(tmp_path, started+timedelta(seconds=360))
    assert result['sources'] == {'raw':'complete', 'summary':'complete', 'compact':'complete'}
    assert result['horizon_states']['censored'] == censored
    assert result['issues'].get('observation_horizon_missing',0) == missing
    assert 'intent_terminal_missing' not in result['issues']


@pytest.mark.parametrize('fault', ['queue', 'append', 'unobservable', 'timeout'])
def test_native_shutdown_does_not_call_failed_or_unobservable_writes_complete(
        monkeypatch, isolated_observation_shutdown, fault):
    from concurrent.futures import ThreadPoolExecutor
    from src.utils import pipeline_event_logger as logger
    owner = isolated_observation_shutdown
    errors = []
    monkeypatch.setattr(main, 'log_error', errors.append)
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = logger.BoundedObservationQueue(executor)
        monkeypatch.setattr(main, '_SCANNER_OBSERVATION_QUEUE', queue)
        if fault == 'timeout':
            monkeypatch.setattr(queue, 'close', lambda **kw: False)
        outcome = False if fault == 'append' else None if fault == 'unobservable' else {
            'structured_append_succeeded': True}
        callback = lambda *a, **kw: outcome
        owner.configure_sink((lambda *a, **kw: {'status':'unavailable'}) if fault=='queue' else
                             lambda *a, **kw: queue.submit(callback))
        assert owner.register('005930', dict(id='exact', committed_at_epoch=1,
            remaining_sec=[120], decision_source_sha256='a'*64))
        assert main.close_observation_sources() is False
    assert len(errors)==1 and 'SOURCE_OBSERVATION_SHUTDOWN_INCOMPLETE' in errors[0]


@pytest.mark.parametrize('exception', [RuntimeError('native phase failed'), KeyboardInterrupt()])
def test_native_iterator_is_lazy_and_propagates_first_entry_exception(monkeypatch, exception):
    from src.engine.monitoring import runtime_performance
    phases = []

    def record(phase, *args, **kwargs):
        phases.append(phase)
        raise exception

    monkeypatch.setattr(runtime_performance, 'record_main_phase', record)
    bindings = dict(is_test_mode=False, targets=[], admin_id=None, radar=None, ai_engine=None,
                    last_db_poll_time=10., last_msg_min=-1, scanner_ws_reg_last_emit_ts={},
                    scanner_ws_repair_cycle_state_by_code={}, log_error=None, log_info=None)
    iterator = main._run_sniper_iterations(**bindings)
    assert phases == []
    assert iterator.gi_frame.f_locals == bindings
    with pytest.raises(type(exception)) as captured:
        next(iterator)
    assert captured.value is exception
    assert phases == ['loop_prepare']
    assert iterator.gi_frame is None
