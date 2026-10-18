"""Native Main extraction parity; no bootstrap, transport or order execution."""
import ast
from copy import deepcopy
import hashlib
import inspect
import symtable

import pytest

from src.engine import kiwoom_sniper_v2 as main


# The refactor's immutable input is 9e78afd1194233d87c4d340ba2f1981d340d88d4.
# These are AST hashes, independent of indentation, comments and line numbers.
ORIGINAL_LOOP_AST = 'a549e790d27ed4e4b86a14cfb46187cfec7dcee51f1fa869a84195e3f3dc04a5'
ORIGINAL_RUN_AST = '33b88984bb49cdc94d3d8f82d0c495edd35038d067cca86a9f4ccb1a253aee5a'
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
    assert _digest(function) == ORIGINAL_RUN_AST


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
