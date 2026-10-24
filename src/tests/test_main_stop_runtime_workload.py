"""Native offline Main workload: real guards, private effects and restoration."""
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


def _native_scenario(order='normal_first', *, code='005930'):
    """Original native BUY receipt producer plus a frozen exact 0B/0D quote."""
    from src.tests.test_main_stop_quantity_source import native_stock
    at = datetime.fromisoformat('2026-10-16T10:11:11+09:00').timestamp()
    stock = native_stock(filled=10, ordered=10, code=code)
    stock.update(status='HOLDING', strategy='SCALPING', position_tag='SCALP_PRESET_TP',
                 exit_mode='SCALP_PRESET_TP', hard_stop_pct=-1.4,
                 hard_stop_emergency_pct=-2.4, hard_stop_grace_sec=0, buy_time=at-120)
    code, bid = stock['code'], 9800
    snapshot = dict(curr=bid, best_bid=bid, best_ask=bid+10, last_ws_update_ts=at,
        market_data_transport_epoch=1, last_realtime_type_item={'0D': code, '0B': code},
        last_realtime_type_ts={'0D': at, '0B': at},
        realtime_type_snapshots_by_route={'krx_only': {'0D': dict(item=code,
            market_route='krx_only', transport_epoch=1, observed_epoch=at,
            best_bid=bid, best_ask=bid+10, best_bid_qty=100,
            orderbook={'bids': [{'price': bid, 'volume': 100}]})}})
    return dict(stock=stock, snapshot=snapshot, at=at, dispatch_order=order)


def _native_cell_scenario(cell):
    """Frozen native route/clock inputs; no protocol or runtime guard changes."""
    role, market = cell.split('|')
    row = _native_scenario('fast_first')
    row.update(role=role, case_id='fast_hard')
    stock = row['stock']
    stock.update(position_tag=role, exit_mode='SCALP_PRESET_TP' if role == 'SCALP_PRESET_TP' else 'NORMAL')
    hour = {'PREMARKET': '08:30:00', 'REGULAR': '10:11:11', 'INTEGRATED_AFTERMARKET': '16:20:00'}[market]
    at = datetime.fromisoformat('2026-10-16T' + hour + '+09:00').timestamp()
    row['at'] = at
    stock['buy_time'] = at - 120
    code = stock['code']
    bid = 9800 if role == 'SCALP_PRESET_TP' else 9400
    suffix = {'PREMARKET': '_NX', 'REGULAR': '', 'INTEGRATED_AFTERMARKET': '_AL'}[market]
    route = {'PREMARKET': 'nxt_only', 'REGULAR': 'krx_only',
             'INTEGRATED_AFTERMARKET': 'krx_nxt_integrated'}[market]
    item = code + suffix
    if suffix:
        stock.update(is_nxt=True, entry_execution_broker_route='NXT' if market == 'PREMARKET' else 'SOR',
                     entry_execution_cohort='PREMARKET_KRX_LIKE' if market == 'PREMARKET' else 'KRX_NXT_INTEGRATED')
    depth = dict(item=item, market_route=route, transport_epoch=1, observed_epoch=at,
        best_bid=bid, best_ask=bid+10, best_bid_qty=100,
        orderbook={'bids': [{'price': bid, 'volume': 100}]})
    row['snapshot'] = dict(curr=bid, best_bid=bid, best_ask=bid+10, last_ws_update_ts=at,
        market_data_transport_epoch=1, last_realtime_type_item={'0D': item, '0B': item},
        last_realtime_type_ts={'0D': at, '0B': at},
        last_realtime_type_market_route={'0D': route, '0B': route},
        last_realtime_type_market_suffix={'0D': suffix, '0B': suffix},
        realtime_type_snapshots_by_route={(suffix + '|' + route) if suffix else route: {'0D': depth}})
    return row


# A fresh child owns all native caches and threads. No safety/evaluator/order
# guard is replaced. The audit guard rejects any accidental external effect.
CHILD = textwrap.dedent(r'''
    import json, os, sys, threading, time
    from contextlib import ExitStack
    from unittest.mock import patch
    from pathlib import Path
    root, mode, order = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    measurement_cell = sys.argv[4]
    root.mkdir(parents=True, exist_ok=True)
    from src.tests.test_main_stop_runtime_workload import _native_scenario, _native_cell_scenario
    from src.tests.test_main_stop_policy import baseline
    from src.engine.automation.main_stop_runtime_workload import isolated_main_workload
    from src.engine.automation.main_stop_performance import _isolated_native_capture
    from src.engine import kiwoom_sniper_v2 as main, sniper_state_handlers as handlers
    from src.engine import sniper_execution_receipts as receipts, kiwoom_orders as orders
    from src.engine import sniper_entry_state as entry_state
    from src.engine.scalping import main_stop_policy as policy
    from src.database.models import RecommendationHistory
    scenario = _native_scenario(order)
    if mode.startswith('typed_cell'):
        scenario = _native_cell_scenario(measurement_cell)
        if mode == 'typed_cell_wrong_clock':
            scenario['at'] = _native_cell_scenario('SCANNER|REGULAR')['at']
        elif mode == 'typed_cell_wrong_role':
            scenario['stock']['position_tag'] = 'SCALPING'
        elif mode == 'typed_cell_closed':
            scenario['at'] = scenario['at'] + 25 * 60
        elif mode == 'typed_cell_route_guard':
            scenario['stock']['entry_execution_cohort'] = 'PREMARKET_KRX_LIKE'
            scenario['snapshot'].update(curr=10000, best_bid=10000, best_ask=10010)
            for row in scenario['snapshot']['realtime_type_snapshots_by_route'].values():
                row['0D'].update(best_bid=10000, best_ask=10010,
                                orderbook={'bids': [{'price': 10000, 'volume': 100}]})
    if mode == 'burst':
        scenario['companions'] = [_native_scenario(order, code=code)
                                  for code in ('000660', '035420')]
        scenario['companions'][0].pop('at')  # Inherit the existing native frame.
    if mode == 'quantity_gap':
        scenario['account_inventory'] = dict(rows=[], successful_exchanges=[])
    if mode == 'continuous':
        at = scenario['at'] - 60
        scenario['at'] = at
        snapshot = scenario['snapshot']
        snapshot.update(curr=10000, best_bid=10000, best_ask=10010, last_ws_update_ts=at,
                        last_realtime_type_ts={'0B': at, '0D': at})
        depth = snapshot['realtime_type_snapshots_by_route']['krx_only']['0D']
        depth.update(observed_epoch=at, best_bid=10000, best_ask=10010,
                     orderbook={'bids':[{'price':10000, 'volume':100}]})
    (root/'capture').mkdir()
    denied = []
    def private(path):
        return isinstance(path, (str, bytes, os.PathLike)) and Path(os.fsdecode(path)).resolve().is_relative_to(root)
    def audit(event, args):
        if event in {'socket.connect', 'socket.connect_ex', 'socket.sendto',
                     'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn'}:
            denied.append(event)
            raise RuntimeError('external_denied:' + event)
        if event == 'sqlite3.connect' and not private(args[0]):
            denied.append(event + ':' + str(args[0]))
            raise RuntimeError('external_database_denied')
        if event == 'open':
            path, mode, flags = args
            writes = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writes and not isinstance(path, int) and not private(path):
                denied.append('open:' + str(path))
                raise RuntimeError('write_denied:' + str(path))
        if event in {'os.rename', 'os.remove', 'os.rmdir', 'os.mkdir'}:
            paths = args[:2] if event == 'os.rename' else args[:1]
            if any(not private(path) for path in paths):
                denied.append(event + ':' + str(paths))
                raise RuntimeError('mutation_denied:' + event)
    sys.addaudithook(audit)
    binding_names = {
        main: ['DB', 'ACTIVE_TARGETS', 'ENTRY_LOCK', 'event_bus', 'WS_MANAGER',
               '_STATE_HANDLER_DEPS', '_EXECUTION_DEPS', 'handle_holding_state'],
        handlers: ['DB', 'ACTIVE_TARGETS', 'ENTRY_LOCK', 'EVENT_BUS', 'WS_MANAGER',
                   'COOLDOWNS', 'HIGHEST_PRICES', 'SEND_EXIT_BEST_IOC',
                   'evaluate_and_dispatch_fast_scalp_exit', '_dispatch_scalp_preset_exit'],
        receipts: ['DB', 'ACTIVE_TARGETS', '_STATE_LOCK', 'event_bus', 'SELL_RECEIPT_RECOVERY_DIR'],
        orders: ['send_sell_order_market', '_post_kiwoom_with_auth_retry', 'get_my_inventory'],
        policy: ['_SOURCE_SINK'],
        entry_state: ['ENTRY_LOCK'],
    }
    bindings = [(module, name, getattr(module, name))
                for module, names in binding_names.items() for name in names]
    prior_env, prior_function_state = dict(os.environ), dict(main.run_sniper.__dict__)
    result, drained, private_database, private_journal = None, None, False, False
    repeated = []
    continuation = {}
    class UserFailure(RuntimeError): pass
    expected_failure = UserFailure('native context user failure')
    try:
        scenarios = [scenario, _native_scenario('fast_first')] if mode in {'repeat', 'stress'} else [scenario]
        with _isolated_native_capture(root/'capture') as (_, queue, capture, sink_calls), \
                isolated_main_workload(root/'runtime', baseline(), scenarios, measurement_cell=measurement_cell) as work:
            database = Path(main.DB.engine.url.database).resolve()
            private_database = database == root/'runtime/runtime.sqlite'
            assert handlers.DB is main.DB and receipts.DB is main.DB
            assert receipts._STATE_LOCK is main.ENTRY_LOCK
            assert entry_state.ENTRY_LOCK is handlers.ENTRY_LOCK is main.ENTRY_LOCK
            private_journal = receipts.SELL_RECEIPT_RECOVERY_DIR.resolve().is_relative_to(root)
            assert private_database and private_journal
            if mode == 'manual':
                Path(os.environ['KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE']).write_text('005930\n')
            if mode == 'priming_rejected':
                # Exercise a real bounded-sink rejection during source setup.
                queue.max_item_bytes = 1
                try:
                    work.run_cycle(0)
                except ValueError as error:
                    assert str(error) == 'stop_runtime_source_priming_rejected'
                    result = dict(setup_failure=str(error))
                else:
                    raise AssertionError('rejected native priming was accepted')
            if mode in {'typed_cell_wrong_clock', 'typed_cell_wrong_role', 'typed_cell_closed'}:
                try:
                    work.run_cycle(0)
                except ValueError as error:
                    expected = ('stop_runtime_unsupported_exit_session' if mode.endswith('closed') else
                                'stop_runtime_unsupported_native_' + ('market' if mode.endswith('clock') else 'role'))
                    assert str(error) == expected
                    result = dict(setup_failure=str(error))
                else:
                    raise AssertionError('wrong native measurement cell was accepted')
            if mode in {'normal', 'manual', 'quantity_gap', 'continuous', 'repeat', 'burst', 'priming_only',
                        'typed_cell', 'typed_cell_route_guard', 'stress', 'frame_setup', 'wake_unavailable', 'source_capture_race', 'superseded_loss'}:
                with ExitStack() as instrumentation:
                    if mode == 'superseded_loss':
                        from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor
                        from src.engine.scalping.main_stop_runtime_source import ensure_observation_epoch
                        original_wake = ScalpExitSafetyMonitor.wake
                        def fail_old_deferred_source(monitor, code):
                            owner = main.ACTIVE_TARGETS[0]
                            raw = dict(owner['_main_stop_last_quote_source'])
                            raw.pop('source_sha256')
                            prior_budget = queue.max_item_bytes
                            try:
                                with policy.defer_source_capture():
                                    assert policy.enqueue_source(owner, code, raw)
                                    # Only the source lifecycle changes. Exercise
                                    # real deferred admission rejection after it.
                                    owner.pop('_main_stop_observation_epoch')
                                    ensure_observation_epoch(owner)
                                    queue.max_item_bytes = 1
                            finally:
                                queue.max_item_bytes = prior_budget
                            return original_wake(monitor, code)
                        instrumentation.enter_context(patch.object(
                            ScalpExitSafetyMonitor, 'wake', fail_old_deferred_source))
                    if mode == 'source_capture_race':
                        original_capture = handlers._capture_main_stop_observation
                        capture_raced = []
                        def race_after_native_quote(stock, code, context, **kwargs):
                            result = original_capture(stock, code, context, **kwargs)
                            if context.get('evaluator') == 'normal' and not capture_raced:
                                capture_raced.append(True)
                                thread_result = []
                                def actual_fast_owner():
                                    thread_result.append(handlers.evaluate_and_dispatch_fast_scalp_exit(
                                        stock, code, main.WS_MANAGER.get_latest_data(code), now_ts=main.time.time()))
                                thread = threading.Thread(target=actual_fast_owner)
                                thread.start()
                                thread.join(2)
                                assert not thread.is_alive() and thread_result == [True]
                                continuation['source_capture_race_exercised'] = True
                            return result
                        instrumentation.enter_context(patch.object(
                            handlers, '_capture_main_stop_observation', race_after_native_quote))
                    if mode == 'frame_setup':
                        from sqlalchemy import event
                        continuation['delete_roster_records'] = []
                        def slow_private_reset(connection, cursor, statement, parameters, context, many):
                            if statement.lstrip().upper().startswith('DELETE FROM'):
                                continuation['delete_roster_records'].append(
                                    [owner['id'] for owner in main.ACTIVE_TARGETS])
                                # Delay only the private SQL input generation.
                                # The real monitor's 250ms poll remains active.
                                threading.Event().wait(.3)
                        event.listen(main.DB.engine, 'before_cursor_execute', slow_private_reset)
                        instrumentation.callback(event.remove, main.DB.engine,
                            'before_cursor_execute', slow_private_reset)
                    if mode == 'wake_unavailable':
                        from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor
                        original_wake = ScalpExitSafetyMonitor.wake
                        def withdraw_poll_input_then_wake(monitor, code):
                            # A real full poll observes an unavailable roster;
                            # restore the current HOLDING input before its wake.
                            # Native wake/holding admission and guards are real.
                            saved = list(main.ACTIVE_TARGETS)
                            main.ACTIVE_TARGETS.clear()
                            try:
                                monitor.run_once(now_ts=main.time.time())
                            finally:
                                main.ACTIVE_TARGETS[:] = saved
                            return original_wake(monitor, code)
                        instrumentation.enter_context(patch.object(
                            ScalpExitSafetyMonitor, 'wake', withdraw_poll_input_then_wake))
                    if mode == 'priming_only':
                        from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor
                        original_wake = ScalpExitSafetyMonitor.wake
                        def lose_roster_then_wake(monitor, code):
                            # Negative source-population fault after native priming.
                            # Both actual evaluators/guards remain untouched; no
                            # performance receipt is produced by this test.
                            main.ACTIVE_TARGETS.clear()
                            return original_wake(monitor, code)
                        instrumentation.enter_context(patch.object(
                            ScalpExitSafetyMonitor, 'wake', lose_roster_then_wake))
                    if mode == 'continuous':
                        from src.engine.monitoring import runtime_performance
                        original = main._run_sniper_iterations
                        original_phase = runtime_performance.record_main_phase
                        original_sleep = main.time.sleep
                        phases, sleeps = [], []
                        def phase(*args, **kwargs):
                            phases.append(args[0])
                            return original_phase(*args, **kwargs)
                        def sleep(seconds):
                            sleeps.append(seconds)
                            return original_sleep(seconds)
                        def two_iterations(**bindings):
                            iterator = original(**bindings)
                            try:
                                assert next(iterator) is None
                                first = iterator.gi_frame.f_locals
                                continuation['first_poll'] = first['last_db_poll_time']
                                continuation['first_message_minute'] = first['last_msg_min']
                                assert first['targets'] is main.ACTIVE_TARGETS is bindings['targets']
                                assert first['scanner_ws_reg_last_emit_ts'] is bindings['scanner_ws_reg_last_emit_ts']
                                at = scenario['at'] + 6
                                main.time.at = at
                                for quote in main.WS_MANAGER.snapshots.values():
                                    quote['last_ws_update_ts'] = at
                                    quote['last_realtime_type_ts'] = {'0B': at, '0D': at}
                                    quote['realtime_type_snapshots_by_route']['krx_only']['0D']['observed_epoch'] = at
                                assert next(iterator) is None
                                second = iterator.gi_frame.f_locals
                                continuation['second_poll'] = second['last_db_poll_time']
                                continuation['second_message_minute'] = second['last_msg_min']
                                assert second['targets'] is bindings['targets']
                                continuation['phases'] = phases
                                continuation['sleeps'] = sleeps
                                yield None
                            finally:
                                iterator.close()
                        instrumentation.enter_context(patch.object(main, '_run_sniper_iterations', two_iterations))
                        instrumentation.enter_context(patch.object(runtime_performance, 'record_main_phase', phase))
                        instrumentation.enter_context(patch.object(main.time, 'sleep', sleep))
                    stress_start = time.perf_counter()
                    result = work.run_cycle(0)
                    if mode == 'stress':
                        repeated.append(result)
                        for index in range(1, 100):
                            repeated.append(work.run_cycle(index))
                        result = repeated[-1]
                        continuation['stress_wall_sec'] = time.perf_counter() - stress_start
                    if mode == 'frame_setup':
                        repeated.append(result)
                        repeated.append(work.run_cycle(1))
                        result = repeated[-1]
                    if mode == 'repeat':
                        repeated.append(result)
                        repeated.append(work.run_cycle(1))
                        repeated.append(work.run_cycle(2))
                        result = repeated[-1]
                with main.DB.get_session() as session:
                    rows = session.query(RecommendationHistory).all()
                    expected_codes = {'005930', '000660', '035420'} if mode == 'burst' else {'005930'}
                    assert {row.stock_code for row in rows} == expected_codes
                    assert all(row.status == result['semantic']['status'] for row in rows)
            if mode == 'exception':
                raise expected_failure
            drained = work.drain()
    except UserFailure as error:
        assert mode == 'exception' and error is expected_failure
    assert all(getattr(module, name) is original for module, name, original in bindings), [
        module.__name__ + '.' + name for module, name, original in bindings
        if getattr(module, name) is not original]
    assert dict(os.environ) == prior_env
    assert main.run_sniper.__dict__ == prior_function_state
    assert not any(thread.name == 'scalp-exit-safety-monitor' and thread.is_alive()
                   for thread in threading.enumerate())
    assert not denied, denied
    race_sources = []
    if mode == 'source_capture_race':
        for line in (root/'capture/captured.jsonl').read_text().splitlines():
            event = json.loads(line)
            if event.get('stage') == 'main_stop_source':
                value = event['fields']['main_stop_source']
                race_sources.append(json.loads(value) if isinstance(value, str) else value)
    files = [str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()]
    print('NATIVE_WORKLOAD_RESULT=' + json.dumps(dict(result=result, drained=drained,
        files=files, private_database=private_database, private_journal=private_journal,
        denied=denied, continuation=continuation, repeated=repeated, race_sources=race_sources), default=str))
''')


def _run_child(tmp_path, *, mode, order='normal_first', measurement_cell='SCANNER|REGULAR'):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='.')
    result = subprocess.run([sys.executable, '-c', CHILD, str(tmp_path), mode, order, measurement_cell],
        cwd=Path(__file__).resolve().parents[2], env=env, text=True,
        capture_output=True, timeout=45)
    (tmp_path / 'native-child.stdout').write_text(result.stdout)
    (tmp_path / 'native-child.stderr').write_text(result.stderr)
    assert result.returncode == 0, result.stdout[-4000:] + '\n' + result.stderr[-10000:]
    line = next(line for line in result.stdout.splitlines() if line.startswith('NATIVE_WORKLOAD_RESULT='))
    return json.loads(line.partition('=')[2])


@pytest.mark.parametrize('mode', ['context', 'exception'])
def test_native_context_restores_bindings_environment_and_thread_on_exit(tmp_path, mode):
    result = _run_child(tmp_path, mode=mode)
    assert result['private_database'] and result['private_journal']
    assert result['denied'] == []
    if mode == 'context':
        assert result['drained']['complete'] is True
        assert result['drained']['actual_order_submitted'] is False


@pytest.mark.parametrize('order', ['normal_first', 'fast_first'])
def test_native_cycle_keeps_guards_and_custody_with_single_private_submit(tmp_path, order):
    body = _run_child(tmp_path, mode='normal', order=order)
    sample, drained = body['result'], body['drained']
    assert sample['semantic']['status'] == 'SELL_ORDERED'
    assert sample['semantic']['db_status'] == 'SELL_ORDERED'
    assert sample['semantic']['stop_family'] == 'preset_hard_stop'
    assert sample['semantic']['pending_custody_verified'] is True
    assert sample['raw_disposition']['exit_requested'] is True
    # Fast claims use an exit token; the normal preset owner uses its original
    # durable pending-submit generation without manufacturing a fast claim.
    assert sample['raw_disposition']['exit_rule'] in {'scalp_hard_stop_pct', 'scalp_preset_hard_stop_pct'}
    assert sample['raw_disposition']['exit_token_present'] is (
        sample['raw_disposition']['exit_rule'] == 'scalp_hard_stop_pct')
    assert sample['calls']['main_cycle'] == sample['calls']['monitor_wake'] == 1
    assert sample['calls']['final_guard'] == sample['calls']['isolated_submit'] == 1
    assert sample['native_elapsed_ns'] > 0 and sample['setup_ns'] > 0
    assert sample['lock_wait_ns'] and sample['lock_hold_ns']
    assert all(value >= 0 for value in sample['lock_wait_ns'] + sample['lock_hold_ns'])
    assert all(value == 0 for value in sample['losses'].values())
    assert drained['complete'] and not drained['errors']
    assert len(drained['transport_trace']) == 1
    assert drained['actual_order_submitted'] is False
    assert any('/sell_receipt_recovery/' in path for path in body['files'])


def test_actual_manual_guard_blocks_both_owners_without_external_calls(tmp_path):
    body = _run_child(tmp_path, mode='manual')
    sample = body['result']
    assert sample['semantic']['status'] == 'HOLDING'
    assert sample['raw_disposition']['exit_requested'] is False
    assert sample['calls'].get('normal_holding', 0) == 1
    assert sample['calls'].get('fast_evaluation', 0) >= 1
    assert sample['calls'].get('final_guard', 0) == 0
    assert sample['calls'].get('isolated_submit', 0) == 0
    assert not body['drained']['transport_trace'] and body['denied'] == []


def test_actual_quantity_guard_keeps_unknown_account_inventory_out_of_transport(tmp_path):
    body = _run_child(tmp_path, mode='quantity_gap')
    assert body['result']['semantic']['status'] == 'HOLDING'
    assert body['result']['calls'].get('frozen_account_read', 0) >= 1
    assert body['result']['calls'].get('isolated_submit', 0) == 0
    assert not body['drained']['transport_trace'] and body['denied'] == []


def test_same_native_iterator_preserves_cadence_locals_and_idle_wake_boundary(tmp_path):
    body = _run_child(tmp_path, mode='continuous')
    continuation = body['continuation']
    assert body['result']['semantic']['status'] == 'HOLDING'
    assert continuation['second_poll'] - continuation['first_poll'] == pytest.approx(6, abs=.5)
    assert continuation['first_message_minute'] == continuation['second_message_minute'] == 10
    assert continuation['sleeps'] == [1., 1.]
    selected = [phase for phase in continuation['phases']
                if phase in {'loop_prepare', 'idle_wait', 'main_wake'}]
    assert selected == ['loop_prepare', 'idle_wait', 'main_wake'] * 2
    assert body['result']['calls']['normal_holding'] == 2
    assert not body['drained']['transport_trace'] and body['denied'] == []


def test_repeated_native_positions_keep_separate_custody_and_one_submit_per_cycle(tmp_path):
    body = _run_child(tmp_path, mode='repeat')
    assert len(body['repeated']) == 3
    assert len({row['position_key'] for row in body['repeated']}) == 3
    assert all(row['semantic']['status'] == 'SELL_ORDERED' for row in body['repeated'])
    assert all(row['calls']['isolated_submit'] == 1 for row in body['repeated'])
    assert all(all(value == 0 for value in row['losses'].values()) for row in body['repeated'])
    assert len(body['drained']['transport_trace']) == 3
    assert body['denied'] == []


def test_native_three_holding_burst_keeps_each_guard_and_private_custody(tmp_path):
    body = _run_child(tmp_path, mode='burst', order='fast_first')
    sample = body['result']
    assert sample['calls']['positions_admitted'] == 3
    assert sample['calls']['main_cycle'] == 1
    assert sample['calls']['monitor_wake'] == 3
    assert sample['calls']['final_guard'] == sample['calls']['isolated_submit'] == 3
    assert all(value == 0 for value in sample['losses'].values())
    assert sample['semantic']['pending_custody_verified'] is True
    companions = sample['semantic']['companions']
    assert {row['code'] for row in companions} == {'000660', '035420'}
    for row in companions:
        assert row['status'] == row['db_status'] == 'SELL_ORDERED'
        assert row['pending_custody_verified'] is True
        assert len(row['submit_trace']) == 1
        assert row['submit_trace'][0]['code'] == row['code']
    traces = body['drained']['transport_trace']
    assert len(traces) == 3
    assert {row['code'] for row in traces} == {'005930', '000660', '035420'}
    assert sample['actual_call_cells']['SCALP_PRESET_TP|REGULAR']['isolated_submit'] == 3
    assert body['drained']['complete'] and body['denied'] == []


def test_native_priming_cannot_mask_missing_measured_position(tmp_path):
    body = _run_child(tmp_path, mode='priming_only', order='fast_first')
    sample = body['result']
    assert sample['calls']['positions_admitted'] == 1
    assert sample['losses']['missing'] == 1
    assert sample['calls'].get('normal_holding', 0) == 0
    assert sample['calls'].get('fast_evaluation', 0) == 0
    assert sample['calls'].get('isolated_submit', 0) == 0
    assert body['drained']['calls']['fast_evaluation'] >= 1  # Actual priming ran.
    assert sample['semantic']['status'] == 'HOLDING'
    assert not body['drained']['transport_trace'] and body['denied'] == []


def test_native_source_priming_rejection_cannot_become_clean_measured_input(tmp_path):
    body = _run_child(tmp_path, mode='priming_rejected')
    assert body['result']['setup_failure'] == 'stop_runtime_source_priming_rejected'
    assert body['drained']['calls']['fast_evaluation'] >= 1
    assert body['drained']['calls'].get('main_cycle', 0) == 0
    assert body['drained']['calls'].get('isolated_submit', 0) == 0
    assert not body['drained']['transport_trace'] and body['denied'] == []


@pytest.mark.parametrize('cell', ['SCANNER|PREMARKET', 'SCALPING|INTEGRATED_AFTERMARKET',
                                'SCALP_PRESET_TP|REGULAR'])
def test_typed_cell_uses_actual_native_role_session_and_final_guard(tmp_path, cell):
    body = _run_child(tmp_path, mode='typed_cell', measurement_cell=cell)
    sample = body['result']
    assert sample['measurement_cell'] == cell
    assert sample['semantic']['status'] == sample['semantic']['db_status'] == 'SELL_ORDERED'
    assert sample['semantic']['pending_custody_verified'] is True
    assert sample['actual_call_cells'][cell]['final_guard'] == 1
    assert sample['actual_call_cells'][cell]['isolated_submit'] == 1
    assert all(value == 0 for value in sample['losses'].values())
    assert body['denied'] == [] and body['drained']['actual_order_submitted'] is False


@pytest.mark.parametrize('fault', ['wrong_clock', 'wrong_role', 'closed'])
def test_typed_cell_never_relabels_an_unmatched_native_input(tmp_path, fault):
    body = _run_child(tmp_path, mode='typed_cell_' + fault, measurement_cell='SCANNER|PREMARKET')
    assert body['result']['setup_failure'].startswith('stop_runtime_unsupported_')
    assert not body['drained']['transport_trace'] and body['denied'] == []


def test_typed_aftermarket_keeps_native_recorded_route_conflict_guard(tmp_path):
    body = _run_child(tmp_path, mode='typed_cell_route_guard',
                      measurement_cell='SCALPING|INTEGRATED_AFTERMARKET')
    assert body['result']['semantic']['status'] == 'HOLDING'
    assert body['result']['calls'].get('final_guard', 0) == 0
    assert not body['drained']['transport_trace'] and body['denied'] == []
    events = [json.loads(line) for line in (tmp_path/'capture/captured.jsonl').read_text().splitlines()]
    blocked = [row['fields'] for row in events if row.get('stage') == 'scalp_fast_exit_venue_blocked']
    assert blocked and all(row['fast_exit_route_guard_reason'] == 'entry_execution_cohort_route_conflict'
                           for row in blocked)


def test_native_monitor_survives_100_frame_replacements_beyond_periodic_interval(tmp_path):
    body = _run_child(tmp_path, mode='stress')
    rows = body['repeated']
    assert len(rows) == len({row['position_key'] for row in rows}) == 100
    assert body['continuation']['stress_wall_sec'] > .25
    assert sum(row['calls'].get('monitor_full_poll', 0) for row in rows) > 0
    assert all(row['calls']['main_cycle'] == 1 for row in rows)
    assert [row['frame_generation'] for row in rows] == list(range(1, 101))
    assert all(set(row['accepted_wake_codes']) <= set(row['completed_wake_codes']) for row in rows)
    assert all(row['calls'].get('monitor_wake_accepted', 0) +
               row['calls'].get('monitor_wake_terminal_ignored', 0) == 1 for row in rows)
    assert all(row['calls'].get('monitor_wake_nonterminal_ignored', 0) == 0 for row in rows)
    assert all(row['calls']['isolated_submit'] == 1 for row in rows)
    assert all(row['semantic']['pending_custody_verified'] is True for row in rows)
    assert all(all(value == 0 for value in row['losses'].values()) for row in rows), [
        dict(position_key=row['position_key'], losses=row['losses'],
             source_gap=row['source_gap'], evaluation_source_gap=row['evaluation_source_gap'])
        for row in rows if any(row['losses'].values())]
    assert len(body['drained']['transport_trace']) == 100
    assert body['drained']['errors'] == [] and body['denied'] == []


def test_private_frame_commits_sql_before_roster_publication_and_drains_old_batches(tmp_path):
    body = _run_child(tmp_path, mode='frame_setup', order='fast_first')
    rows = body['repeated']
    assert len(rows) == 2 and rows[0]['position_key'] != rows[1]['position_key']
    prior_record = int(rows[0]['position_key'].split(':')[1])
    assert body['continuation']['delete_roster_records'] == [[], [prior_record]]
    assert body['drained']['calls']['monitor_frame_admission_skipped'] >= 1
    assert all(row['semantic']['pending_custody_verified'] is True for row in rows)
    assert all(all(value == 0 for value in row['losses'].values()) for row in rows), [
        dict(position_key=row['position_key'], losses=row['losses'],
             source_gap=row['source_gap'], evaluation_source_gap=row['evaluation_source_gap'])
        for row in rows if any(row['losses'].values())]
    assert body['drained']['errors'] == [] and body['denied'] == []


def test_native_nonterminal_wake_unavailability_is_a_loss_not_a_completed_batch(tmp_path):
    from src.engine.automation.main_stop_performance import _native_losses_verified
    body = _run_child(tmp_path, mode='wake_unavailable', order='fast_first')
    row = body['result']
    assert row['calls']['monitor_wake'] == row['calls']['monitor_wake_nonterminal_ignored'] == 1
    assert row['calls'].get('monitor_wake_accepted', 0) == 0
    assert row['calls'].get('monitor_ws_wake_dispatch', 0) == 0
    assert row['accepted_wake_codes'] == row['completed_wake_codes'] == []
    assert row['losses']['missing'] == 0  # The real normal owner still visited.
    assert row['losses']['wake_unavailable'] == 1
    assert not _native_losses_verified(row['losses'])
    assert row['semantic']['pending_custody_verified'] is True
    assert body['denied'] == []


def test_actual_normal_stage_keeps_its_source_when_fast_claims_after_quote_capture(tmp_path):
    from src.engine.scalping.main_stop_replay import evaluation_binding, quantity_support
    body = _run_child(tmp_path, mode='source_capture_race')
    row = body['result']
    assert body['continuation']['source_capture_race_exercised'] is True
    assert row['semantic']['pending_custody_verified'] is True
    assert row['calls']['isolated_submit'] == 1
    assert row['raw_disposition']['exit_rule'] == 'scalp_hard_stop_pct'
    assert all(value == 0 for value in row['losses'].values()), row
    quotes = {r['source_sha256']: r for r in body['race_sources'] if r['schema'] == 'main_stop_source_v1'}
    evaluations = [r for r in body['race_sources'] if r['schema'] == 'main_stop_evaluation_source_v1'
                   and r['at'] >= row['frame_start_epoch']]
    assert {r['evaluator'] for r in evaluations} == {'normal', 'fast'}
    assert len({r['evaluation_id'] for r in evaluations}) == len(evaluations)
    for evaluation in evaluations:
        quote = quotes[evaluation['quote_source_sha256']]
        assert evaluation_binding(evaluation, quote) is evaluation
        assert quote['at'] <= evaluation['at']
        assert evaluation['quote_binding_status'] == 'supported'
        assert quantity_support(evaluation['quantity_source'], quote, at=evaluation['at']) == ('full_fill', None)
    assert body['drained']['errors'] == [] and body['denied'] == []


def test_superseded_deferred_rejection_remains_a_performance_loss(tmp_path):
    from src.engine.automation.main_stop_performance import _native_losses_verified
    body = _run_child(tmp_path, mode='superseded_loss')
    row = body['result']
    assert row['semantic']['pending_custody_verified'] is True
    assert row['calls']['isolated_submit'] == 1
    assert row['losses']['source_rejected'] == row['losses']['evaluation_rejected'] == 0
    assert row['losses']['source_superseded_rejected'] == 1
    assert not _native_losses_verified(row['losses'])
    assert body['drained']['errors'] == [] and body['denied'] == []
