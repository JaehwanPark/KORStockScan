"""Offline external adapters for the native Main iteration performance workload.

Only clocks, files, WS/account inputs, SQL storage and transport are private.
The Main iterator, holding/fast evaluators, custody and submission guards remain
the production functions. Import and use in an idle offline child only.
"""
from collections import Counter
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import os
import logging
import math
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo


class _Clock:
    def __init__(self):
        self.at = 0.

    def time(self):
        return self.at + max(0., time.perf_counter() - self._started_perf)

    @property
    def at(self):
        return self._at

    @at.setter
    def at(self, value):
        self._at = float(value)
        self._started_perf = time.perf_counter()

    def sleep(self, seconds):
        # Scheduling waits use a private, signalled input adapter. The measured
        # boundary is native work; it excludes the ordinary one-second idle.
        if seconds > 0:
            threading.Event().wait(0)

    def __getattr__(self, name):
        return getattr(time, name)


class _MeasuredLock:
    def __init__(self):
        self.lock = threading.RLock()
        self.wait_ns = []
        self.hold_ns = []
        self.local = threading.local()

    def acquire(self, *args, **kwargs):
        started = time.perf_counter_ns()
        result = self.lock.acquire(*args, **kwargs)
        if result:
            self.wait_ns.append(time.perf_counter_ns() - started)
            stack = getattr(self.local, 'stack', [])
            stack.append(time.perf_counter_ns())
            self.local.stack = stack
        return result

    def release(self):
        self.hold_ns.append(time.perf_counter_ns() - self.local.stack.pop())
        return self.lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()

    def __getattr__(self, name):
        return getattr(self.lock, name)


class _FrozenWS:
    def __init__(self):
        self.snapshots = {}

    def get_latest_data(self, code):
        return deepcopy(self.snapshots.get(str(code)[:6], {}))

    def get_exact_item_data(self, code, item):
        return self.get_latest_data(code)


class _Events:
    def __init__(self):
        self.events = []

    def publish(self, name, body):
        self.events.append((name, deepcopy(body)))


@contextmanager
def isolated_main_workload(root, values, scenarios, *, measurement_cell='SCANNER|REGULAR'):
    """Yield a resettable workload with an actual private ORM and native guards."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.db_manager import DBManager
    from src.database.models import Base, RecommendationHistory
    from src.engine import kiwoom_sniper_v2 as main
    from src.engine import sniper_state_handlers as handlers
    from src.engine import sniper_trade_utils as trade
    from src.engine import sniper_execution_receipts as execution_receipts
    from src.engine import sniper_entry_state as entry_state
    from src.engine import kiwoom_orders as orders
    from src.engine.error_detectors import process_health
    from src.engine.scalping import main_stop_policy as policy
    from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor
    from src.engine.scalping import exit_safety_monitor as monitor_module
    from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER, position_cycle_id
    from src.utils import constants, pipeline_event_logger
    from src.utils import logger as native_logger

    if (not isinstance(measurement_cell, str) or measurement_cell not in {
            role + '|' + market for role in policy.ROLES for market in policy.MARKETS}):
        raise ValueError('stop_runtime_measurement_cell_invalid')
    measured_role, measured_market = measurement_cell.split('|')

    def native_identity(template, *, expected_at=None):
        stock = template['stock']
        at = template.get('at', template.get('quote_inputs', {}).get('now_ts', expected_at))
        if (type(at) not in (int, float) or not math.isfinite(at) or at <= 0
                or (expected_at is not None and at != expected_at)):
            raise ValueError('stop_runtime_unsupported_scenario_clock')
        # Match the existing _main_stop_values classification, not a caller's
        # desired certificate label. The runtime's session owner owns markets.
        role = ('SCALP_PRESET_TP' if stock.get('exit_mode') == 'SCALP_PRESET_TP'
                else 'SCANNER' if stock.get('position_tag') == 'SCANNER' else 'SCALPING')
        market = handlers.scalp_trailing_market_type_at(at)
        if stock.get('strategy') != 'SCALPING' or template.get('role', role) != role:
            raise ValueError('stop_runtime_unsupported_native_role')
        if template.get('case_id') in {'common_soft_hold', 'fast_hard'} and role != measured_role:
            raise ValueError('stop_runtime_unsupported_measurement_role')
        if market != measured_market:
            raise ValueError('stop_runtime_unsupported_native_market')
        session = handlers.session_contract.resolve_market_session(
            datetime.fromtimestamp(at, ZoneInfo('Asia/Seoul')))
        if session.blocker or not session.exit_allowed_by_clock:
            raise ValueError('stop_runtime_unsupported_exit_session')
        return role, market, float(at)

    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    private_data = root / 'data'
    private_data.mkdir(exist_ok=True)
    clock = _Clock()
    state_lock = _MeasuredLock()
    # Private input-frame lifetime only. Main never holds this lock while
    # evaluating; its normal/fast competition retains the native state lock.
    frame_gate = threading.RLock()
    frame_state = dict(generation=0, open=False, wake_generation=None)
    batch_context = threading.local()
    wake_context = threading.local()
    ws = _FrozenWS()
    events = _Events()
    calls = Counter()
    cell_calls = Counter()
    errors = []
    traces = []
    targets = []
    account_inputs = {}
    fast_complete = threading.Event()
    wake_requested = threading.Event()
    wanted_wake_codes = set()
    completed_wake_codes = set()
    visited_positions = set()
    loggers = {}

    class ErrorObserver(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                errors.append(record.getMessage())

    def private_logger(caller, level):
        key = (caller, level)
        if key not in loggers:
            destination = root / 'logs'
            destination.mkdir(exist_ok=True)
            logger = logging.Logger('offline.' + caller + '.' + level)
            logger.addHandler(native_logger.ProcessSafeRotatingFileHandler(
                destination / (caller + '_' + level + '.log'), maxBytes=20 * 1024 * 1024,
                backupCount=10, encoding='utf-8'))
            logger.addHandler(ErrorObserver())
            loggers[key] = logger
        return loggers[key]
    old_data = Path(constants.DATA_DIR).resolve()
    engine = create_engine('sqlite:///' + str(root / 'runtime.sqlite'),
                           connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    db = DBManager.__new__(DBManager)
    db.engine = engine
    db.SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    saved_bindings = [(module, dict(vars(module))) for module in (handlers, execution_receipts)]

    def restore_bindings():
        for module, before in saved_bindings:
            for name, value in before.items():
                if name in vars(module) and vars(module)[name] is not value:
                    setattr(module, name, value)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            result = datetime.fromtimestamp(clock.time(), ZoneInfo('Asia/Seoul'))
            return result.astimezone(tz) if tz else result.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return datetime.fromtimestamp(clock.time(), timezone.utc).replace(tzinfo=None)

    def log_error(message, *args, **kwargs):
        errors.append(str(message))

    def log_info(*args, **kwargs):
        calls['log_info'] += 1

    def transport(url, headers, payload, api_id, timeout=5):
        # Native order type, route, owner-intent and custody guards precede
        # this external boundary. No request is sent to any server.
        if api_id != 'kt10001':
            raise ValueError('stop_runtime_unexpected_transport:' + str(api_id))
        calls['isolated_submit'] += 1
        for owner in targets:
            if str(owner['code'])[:6] == payload['stk_cd']:
                pin = owner['main_stop_policy_pin']
                cell_calls[(pin['role'] + '|' + pin['market'], 'isolated_submit')] += 1
        traces.append(dict(api_id=api_id, code=payload['stk_cd'], qty=payload['ord_qty'],
                           route=payload['dmst_stex_tp'], order_type=payload['trde_tp']))
        return SimpleNamespace(status_code=200), dict(return_code=0,
            ord_no=f"{calls['isolated_submit']:07d}")

    def inventory(token):
        calls['frozen_account_read'] += 1
        rows = account_inputs.get('rows', [dict(code=s['code'], qty=s['buy_qty']) for s in targets])
        return deepcopy(rows), set(account_inputs.get('successful_exchanges', ['KRX', 'NXT']))

    def observe_call(name, function):
        def observed(*args, **kwargs):
            calls[name] += 1
            stock = args[0] if args and isinstance(args[0], dict) else kwargs.get('stock')
            if stock is None and name == 'final_guard':
                symbol = str(kwargs.get('code') or (args[0] if args else ''))[:6]
                stock = next((owner for owner in targets if str(owner['code'])[:6] == symbol), None)
            if stock and stock.get('main_stop_policy_pin'):
                pin = stock['main_stop_policy_pin']
                cell_calls[(pin['role'] + '|' + pin['market'], name)] += 1
            old_token = stock.get('exit_token') if isinstance(stock, dict) else None
            if stock and name in {'normal_holding', 'fast_evaluation'}:
                visited_positions.add(position_cycle_id(stock))
            try:
                result = function(*args, **kwargs)
                if name == 'native_stage_evaluation' and result is not None:
                    stage = str(kwargs.get('stage', ''))
                    evaluator = str(kwargs.get('evaluator', ''))
                    calls['accepted_stage:' + evaluator + ':' + stage] += 1
                return result
            finally:
                if name == 'fast_evaluation':
                    if stock and not old_token and stock.get('exit_token'):
                        calls['claim'] += 1
        return observed

    monitor = None

    class WakeEventReceipt:
        # Observe the existing native input event; its lock/coalescing/holding
        # admission remain native. A wake ignored after an exit is not a batch.
        def __init__(self, event):
            self.event = event

        def set(self):
            if getattr(wake_context, 'requested_code', None) is not None:
                wake_context.accepted = True
            return self.event.set()

        def __getattr__(self, name):
            return getattr(self.event, name)

    def request_wakes(actual_snapshots):
        for wake_code in actual_snapshots:
            wake_context.requested_code = wake_code
            wake_context.accepted = False
            try:
                monitor.wake(wake_code)
                accepted = wake_context.accepted
            finally:
                wake_context.requested_code = None
            calls['monitor_wake'] += 1
            if accepted:
                calls['monitor_wake_accepted'] += 1
            else:
                # Do not invent a successful evaluator invocation. The actual
                # Main/fast visitation and source coverage are checked below.
                calls['monitor_wake_ignored'] += 1
                with state_lock:
                    owner = next((item for item in targets
                                  if str(item.get('code', ''))[:6] == wake_code), None)
                    terminal = owner is not None and owner.get('status') == 'SELL_ORDERED'
                calls['monitor_wake_terminal_ignored' if terminal else
                      'monitor_wake_nonterminal_ignored'] += 1
                with frame_gate:
                    wanted_wake_codes.discard(wake_code)
        with frame_gate:
            if wanted_wake_codes <= completed_wake_codes:
                fast_complete.set()
        if not fast_complete.wait(2):
            raise ValueError('stop_runtime_fast_wake_timeout')

    class Workload:
        def run_cycle(self, index):
            cycle_started = time.perf_counter_ns()
            with frame_gate:
                frame_state.update(generation=frame_state['generation'] + 1, open=False,
                                   wake_generation=None)
                scenario = deepcopy(scenarios[index % len(scenarios)])
                role, market, at = native_identity(scenario)
                account_inputs.clear()
                account_inputs.update(scenario.get('account_inventory', {}))
                stock = scenario['stock']
                code = str(stock['code'])[:6]
                record = int(stock.get('id', 1)) + 10000 * (index + 1)
                stock.update(id=record, status='HOLDING', name='OFFLINE_STOP_WORKLOAD',
                             initial_buy_qty=stock['buy_qty'], add_count=0, scale_in_filled_qty=0)
                clock.at = at
                day = datetime.fromtimestamp(at, ZoneInfo('Asia/Seoul')).date().isoformat()
                os.environ['KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE'] = day
                os.environ['KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE'] = day
                stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
                    role=role, market=market,
                    target=day, baseline=values)
                stock['_main_stop_typed_values'] = values
                stock['_main_stop_position_key'] = position_cycle_id(stock)
                snapshots = scenario.get('snapshot') or scenario.get('quote_inputs', {}).get('snapshot', {})
                safe = deepcopy(snapshots)
                safe['last_ws_update_ts'] = at - 1
                safe['last_realtime_type_ts'] = {'0B': at - 1, '0D': at - 1}
                for key in ('curr', 'best_bid', 'best_ask'):
                    safe[key] = int(stock['buy_price'])
                for routes in safe.get('realtime_type_snapshots_by_route', {}).values():
                    for depth in routes.values():
                        depth['observed_epoch'] = at - 1
                        depth['best_bid'] = depth['best_ask'] = int(stock['buy_price'])
                        if depth.get('orderbook', {}).get('bids'):
                            depth['orderbook']['bids'][0]['price'] = int(stock['buy_price'])
                companion_templates = scenario.get('companions', [])
                if not isinstance(companion_templates, list) or len(companion_templates) > 7:
                    raise ValueError('stop_runtime_companion_population_unbounded')
                companions = []
                actual_snapshots = {code: deepcopy(snapshots)}
                safe_snapshots = {code: safe}
                for offset, template in enumerate(companion_templates, 1):
                    other_role, other_market, _ = native_identity(template, expected_at=at)
                    other = deepcopy(template['stock'])
                    other_code = str(other['code'])[:6]
                    if other_code in actual_snapshots:
                        raise ValueError('stop_runtime_companion_symbol_duplicate')
                    other.update(id=record + offset, status='HOLDING', name='OFFLINE_STOP_COMPANION',
                        initial_buy_qty=other['buy_qty'], add_count=0, scale_in_filled_qty=0)
                    key = position_cycle_id(other)
                    other.update(main_stop_policy_pin=policy.pin(position_key=key,
                        role=other_role, market=other_market, target=day, baseline=values),
                        _main_stop_typed_values=values, _main_stop_position_key=key)
                    other_snapshot = deepcopy(template['snapshot'])
                    other_safe = deepcopy(other_snapshot)
                    other_safe.update(curr=int(other['buy_price']), best_bid=int(other['buy_price']),
                        best_ask=int(other['buy_price']), last_ws_update_ts=at - 1,
                        last_realtime_type_ts={'0B': at - 1, '0D': at - 1})
                    for routes in other_safe.get('realtime_type_snapshots_by_route', {}).values():
                        for depth in routes.values():
                            depth.update(observed_epoch=at - 1, best_bid=int(other['buy_price']),
                                         best_ask=int(other['buy_price']))
                            if depth.get('orderbook', {}).get('bids'):
                                depth['orderbook']['bids'][0]['price'] = int(other['buy_price'])
                    companions.append(other)
                    actual_snapshots[other_code], safe_snapshots[other_code] = other_snapshot, other_safe
                frame_owners = [stock, *companions]
                with db.get_session() as session:
                    session.query(RecommendationHistory).delete()
                    for owner in frame_owners:
                        session.add(RecommendationHistory(id=owner['id'], rec_date=datetime.fromtimestamp(at).date(),
                            stock_code=owner['code'], stock_name=owner['name'], status='HOLDING', strategy='SCALPING',
                            position_tag=owner.get('position_tag', 'SCALP_PRESET_TP'),
                            buy_price=owner['buy_price'], buy_qty=owner['buy_qty'],
                            buy_time=datetime.fromtimestamp(at - 120)))
                with state_lock:
                    targets[:] = frame_owners
                    ws.snapshots = safe_snapshots
                main.highest_prices.clear()
                main.alerted_stocks.clear()
                main.cooldowns.clear()
                for name in ('last_fifo_time', 'last_opening_rotation_ttl_sweep_time',
                             'last_account_sync_time', 'last_fixed_watch_reconcile_time',
                             'last_ws_prune_time', 'last_broker_snapshot_refresh_time'):
                    setattr(main.run_sniper, name, at)
                main.run_sniper.krx_open_watchlist_reset_date = day
                main.run_sniper.scanner_async_eval_coordinator = None
                main.run_sniper.scanner_runtime_scheduler = main.ScannerRuntimeScheduler(
                    max_active=main._scalping_fifo_base_max_active())
                main.run_sniper.scanner_scheduler_mode = 'legacy'
                trace_start = len(traces)
                error_start = len(errors)
                expected_positions = {position_cycle_id(owner) for owner in targets}
                priming_rejections = {position_cycle_id(owner): (
                    int(owner.get('main_stop_source_rejected_count', 0)),
                    int(owner.get('main_stop_evaluation_rejected_count', 0)),
                    int(owner.get('main_stop_source_superseded_rejected_count', 0))) for owner in targets}
                clock.at = at - 1
                frame_state['open'] = True
                monitor.run_once(now_ts=at - 1)
                if any((int(owner.get('main_stop_source_rejected_count', 0)),
                        int(owner.get('main_stop_evaluation_rejected_count', 0)),
                        int(owner.get('main_stop_source_superseded_rejected_count', 0))) !=
                       priming_rejections[position_cycle_id(owner)] for owner in targets):
                    raise ValueError('stop_runtime_source_priming_rejected')
                if len(traces) != trace_start or any(owner['status'] != 'HOLDING' for owner in targets):
                    raise ValueError('stop_runtime_source_priming_changed_disposition')
                clock.at = at
                with state_lock:
                    ws.snapshots = actual_snapshots
                # Source priming is setup. Only the measured native cycle may
                # satisfy visitation, per-cell coverage and call/lock counters.
                before = dict(calls)
                before_cells = dict(cell_calls)
                wait_start, hold_start = len(state_lock.wait_ns), len(state_lock.hold_ns)
                visited_positions.clear()
                rejected_before = {position_cycle_id(owner): (
                    int(owner.get('main_stop_source_rejected_count', 0)),
                    int(owner.get('main_stop_evaluation_rejected_count', 0)),
                    int(owner.get('main_stop_source_superseded_rejected_count', 0))) for owner in targets}
                calls['positions_admitted'] += len(expected_positions)
                fast_complete.clear()
                wanted_wake_codes.clear()
                wanted_wake_codes.update(actual_snapshots)
                completed_wake_codes.clear()
                frame_state['wake_generation'] = frame_state['generation']
                wake_requested.set()
                order = scenario.get('dispatch_order', 'normal_first' if index % 2 == 0 else 'fast_first')
                native_started = time.perf_counter_ns()
            if order == 'fast_first':
                request_wakes(actual_snapshots)
            iterator = main._run_sniper_iterations(is_test_mode=False, targets=targets,
                admin_id=None, radar=None, ai_engine=None, last_db_poll_time=at, last_msg_min=-1,
                scanner_ws_reg_last_emit_ts={}, scanner_ws_repair_cycle_state_by_code={},
                log_error=log_error, log_info=log_info)
            # The actual native cycle includes its scheduling wake boundary.
            next(iterator)
            calls['main_cycle'] += 1
            iterator.close()
            if order != 'fast_first':
                request_wakes(actual_snapshots)
            # Drain every native monitor batch before reading its outcome or
            # admitting the next frame. Do not serialize Main with fast work.
            with frame_gate:
                frame_state['open'] = False
                frame_state['wake_generation'] = None
                wake_requested.clear()
                native_elapsed_ns = time.perf_counter_ns() - native_started
            if errors[error_start:]:
                raise ValueError('stop_runtime_native_error:' + '|'.join(errors[error_start:])[:1500])
            raw_disposition = dict(status=stock['status'], exit_rule=stock.get('last_exit_rule'),
                exit_requested=bool(stock.get('exit_requested')), exit_token_present=bool(stock.get('exit_token')),
                buy_qty=stock.get('buy_qty'))
            native_rule = raw_disposition['exit_rule']
            # The normal preset owner and fast owner race on the same declared
            # preset threshold. Preserve the actual owner separately while
            # comparing the shared quantity/price/custody disposition.
            aliases = {'scalp_preset_hard_stop_pct', 'scalp_hard_stop_pct'}
            stop_family = 'preset_hard_stop' if native_rule in aliases else native_rule
            if native_rule in aliases and stock.get('exit_mode') != 'SCALP_PRESET_TP':
                stop_family = native_rule
            with db.get_session() as session:
                persisted = session.query(RecommendationHistory).filter_by(id=record).one()
                db_status = persisted.status
            journal, journal_reason = execution_receipts.load_pending_sell_submit_custody(
                target_id=record, code=code, position_qty=stock['buy_qty'], now_epoch=clock.time())
            submitted = sum(item['code'] == code for item in traces[trace_start:])
            if submitted and (journal is None or db_status != 'SELL_ORDERED'):
                raise ValueError('stop_runtime_native_submit_custody_unverified:' + journal_reason)
            semantic = dict(status=stock['status'], stop_family=stop_family,
                buy_qty=stock.get('buy_qty'), db_status=db_status,
                pending_custody_verified=bool(journal),
                submit_trace=sorted(deepcopy(traces[trace_start:]), key=lambda item: item['code']),
                manual_excluded=bool(stock.get('manual_control_exclusion_blocked')),
                reconciliation_required=bool(stock.get('sell_cancel_reconciliation_required')),
                sell_target_price=stock.get('sell_target_price'),
                last_sell_error=stock.get('last_sell_order_error'))
            if companions:
                outcomes = []
                with db.get_session() as session:
                    for other in companions:
                        row = session.query(RecommendationHistory).filter_by(id=other['id']).one()
                        proof, reason = execution_receipts.load_pending_sell_submit_custody(
                            target_id=other['id'], code=other['code'], position_qty=other['buy_qty'],
                            now_epoch=clock.time())
                        submitted_for_owner = [t for t in traces[trace_start:] if t['code'] == other['code']]
                        if submitted_for_owner and (proof is None or row.status != 'SELL_ORDERED'):
                            raise ValueError('stop_runtime_companion_custody_unverified:' + reason)
                        outcomes.append(dict(code=other['code'], status=other['status'], db_status=row.status,
                            buy_qty=other['buy_qty'], pending_custody_verified=bool(proof),
                            submit_trace=deepcopy(submitted_for_owner),
                            manual_excluded=bool(other.get('manual_control_exclusion_blocked')),
                            reconciliation_required=bool(other.get('sell_cancel_reconciliation_required'))))
                semantic['companions'] = outcomes
            expected = scenario.get('expected_semantic', {})
            if any(semantic.get(key) != value for key, value in expected.items()):
                raise ValueError('stop_runtime_expected_native_disposition_changed')
            return dict(semantic=semantic, position_key=position_cycle_id(stock),
                measurement_cell=measurement_cell,
                raw_disposition=raw_disposition, case_id=scenario.get('case_id'),
                frame_generation=frame_state['generation'],
                accepted_wake_codes=sorted(wanted_wake_codes),
                completed_wake_codes=sorted(completed_wake_codes),
                pending_custody_reason=journal_reason,
                native_elapsed_ns=native_elapsed_ns,
                setup_ns=native_started - cycle_started,
                clock_basis='frozen_frame_epoch_plus_real_monotonic_elapsed',
                frame_end_epoch=clock.time(), frame_start_epoch=at,
                calls={k: calls[k] - before.get(k, 0) for k in calls},
                actual_call_cells={cell: {name: number - before_cells.get((cell, name), 0)
                    for (owner, name), number in cell_calls.items() if owner == cell}
                    for cell, _ in cell_calls},
                lock_wait_ns=state_lock.wait_ns[wait_start:],
                lock_hold_ns=state_lock.hold_ns[hold_start:],
                losses=dict(missing=len(expected_positions - visited_positions),
                    wake_unavailable=calls['monitor_wake_nonterminal_ignored'] -
                        before.get('monitor_wake_nonterminal_ignored', 0),
                    duplicate=sum(max(0, number - 1) for number in Counter(
                        item['code'] for item in traces[trace_start:]).values()),
                    new_expiry=sum(owner['status'] == 'EXPIRED' for owner in targets),
                    queue_rejected=sum('queue_rejected' in str(owner.get('main_stop_source_gap', ''))
                                       for owner in targets),
                    source_rejected=sum(int(owner.get('main_stop_source_rejected_count', 0)) -
                        rejected_before[position_cycle_id(owner)][0] for owner in targets),
                    evaluation_rejected=sum(int(owner.get('main_stop_evaluation_rejected_count', 0)) -
                        rejected_before[position_cycle_id(owner)][1] for owner in targets),
                    source_superseded_rejected=sum(int(owner.get('main_stop_source_superseded_rejected_count', 0)) -
                        rejected_before[position_cycle_id(owner)][2] for owner in targets)),
                source_gap=stock.get('main_stop_source_gap'),
                evaluation_source_gap=stock.get('main_stop_evaluation_source_gap'))

        def drain(self):
            monitor.stop()
            if monitor.running:
                raise ValueError('stop_runtime_monitor_drain_timeout')
            return dict(complete=True, errors=list(errors), calls=dict(calls),
                        transport_trace=deepcopy(traces), actual_order_submitted=False)

    with ExitStack() as stack:
        stack.callback(restore_bindings)
        # Each arm starts with its own local mutable state. A previous arm's
        # transient source/receipt caches cannot silently warm the next arm.
        for module, before in saved_bindings:
            for name, value in before.items():
                if name.startswith('__') or type(value) not in (dict, list, set):
                    continue
                try:
                    private_value = deepcopy(value)
                except (TypeError, ValueError):
                    # Live futures/locks are not a supported offline context.
                    raise ValueError('stop_runtime_requires_idle_state:' + name)
                stack.enter_context(patch.object(module, name, private_value))
        stack.enter_context(patch.object(main, '_STATE_HANDLER_DEPS', dict(main._STATE_HANDLER_DEPS)))
        stack.enter_context(patch.object(main, '_EXECUTION_DEPS', dict(main._EXECUTION_DEPS)))
        stack.enter_context(patch.dict(main.run_sniper.__dict__, {}, clear=True))
        stack.enter_context(patch.dict(os.environ, {
            'KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE': str(private_data / 'symbol_policy.json'),
            'KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH': str(private_data / 'owner_registry.jsonl'),
            'KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE': str(private_data / 'excluded.txt'),
            'KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE': '',
            'KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE': '',
            'KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED': 'true',
            'HARD_STOP_MANUAL_HANDOFF_ENABLED': 'false',
        }))
        # Rebase existing data paths to the private filesystem adapter, without
        # replacing any decision, source validation or custody function.
        for module in tuple(sys.modules.values()):
            if module is None or not str(getattr(module, '__name__', '')).startswith('src.'):
                continue
            for name, value in tuple(vars(module).items()):
                if isinstance(value, Path) and value.is_absolute():
                    try:
                        relative = value.resolve().relative_to(old_data)
                    except (ValueError, OSError):
                        continue
                    stack.enter_context(patch.object(module, name, private_data / relative))
        for module in (main, handlers, trade, orders, execution_receipts):
            stack.enter_context(patch.object(module, 'datetime', FrozenDateTime))
            if hasattr(module, 'time'):
                stack.enter_context(patch.object(module, 'time', clock))
            for name, function in (('log_info', log_info), ('log_error', log_error)):
                if hasattr(module, name):
                    stack.enter_context(patch.object(module, name, function))
        stack.enter_context(patch.object(monitor_module, 'time', clock))
        for module in (main, handlers):
            for name, value in (('DB', db), ('ACTIVE_TARGETS', targets), ('ENTRY_LOCK', state_lock),
                                ('KIWOOM_TOKEN', 'OFFLINE_NO_NETWORK'), ('WS_MANAGER', ws)):
                stack.enter_context(patch.object(module, name, value))
        # Deferred source failures import the canonical owner dynamically.
        # Use the same native lock identity for decisions and source counters.
        stack.enter_context(patch.object(entry_state, 'ENTRY_LOCK', state_lock))
        for name, value in (('highest_prices', {}), ('alerted_stocks', set()), ('cooldowns', {}),
                            ('LAST_AI_CALL_TIMES', {}), ('LAST_LOG_TIMES', {})):
            stack.enter_context(patch.object(main, name, value))
        stack.enter_context(patch.object(main, 'event_bus', events))
        stack.enter_context(patch.object(main, 'MARKET_REGIME', SimpleNamespace(
            refresh_if_needed=lambda: SimpleNamespace(risk_state='NEUTRAL'))))
        stack.enter_context(patch.object(main, 'RESTART_FLAG_PATH', root / 'never-restart'))
        stack.enter_context(patch.object(native_logger, '_get_module_logger', private_logger))
        stack.enter_context(patch.object(native_logger, 'LOGS_DIR', root / 'logs'))
        stack.enter_context(patch.object(native_logger, 'LEGACY_LOGS_DIR', root / 'legacy_logs'))
        stack.enter_context(patch.object(process_health, 'HEARTBEAT_PATH', root / 'heartbeat.json'))
        stack.enter_context(patch.object(POSITION_PEAK_LEDGER, 'path', private_data / 'peak.json'))
        stack.enter_context(patch.object(execution_receipts, 'SELL_RECEIPT_RECOVERY_DIR',
                                        private_data / 'sell_receipt_recovery'))
        stack.enter_context(patch.object(execution_receipts, '_STATE_LOCK', state_lock))
        for module in (handlers, execution_receipts):
            if hasattr(module, 'emit_pipeline_event'):
                stack.enter_context(patch.object(module, 'emit_pipeline_event',
                                                pipeline_event_logger.emit_pipeline_event))
        stack.enter_context(patch.object(orders, '_post_kiwoom_with_auth_retry', transport))
        stack.enter_context(patch.object(orders, 'get_my_inventory', inventory))
        for module, name, counter in ((main, 'handle_holding_state', 'normal_holding'),
                (handlers, 'evaluate_and_dispatch_fast_scalp_exit', 'fast_evaluation'),
                (handlers, '_dispatch_scalp_preset_exit', 'native_exit_registration'),
                (handlers, '_observe_main_stop_evaluation', 'native_stage_evaluation'),
                (orders, 'send_sell_order_market', 'final_guard')):
            stack.enter_context(patch.object(module, name, observe_call(counter, getattr(module, name))))
        try:
            main._ensure_state_handler_deps()
            main._ensure_execution_deps()
            monitor = ScalpExitSafetyMonitor(targets_provider=lambda: (
                    targets if frame_state['open'] and getattr(batch_context, 'admitted', False) else []),
                ws_snapshot_provider=ws.get_latest_data,
                evaluator=handlers.evaluate_and_dispatch_fast_scalp_exit,
                state_lock=state_lock, interval_sec=.25, error_handler=log_error)
            monitor._wakeup_event = WakeEventReceipt(monitor._wakeup_event)
            native_once = monitor.run_once

            def observed_once(*args, **kwargs):
                # Pin at entry, before waiting for a setup/drain boundary. A
                # queued batch from an old frame must not consume new inputs.
                generation = frame_state['generation']
                entered_open = frame_state['open']
                with frame_gate:
                    admitted = entered_open and frame_state['open'] and generation == frame_state['generation']
                    if not admitted:
                        # A closed/obsolete private frame is no native input.
                        # In particular, do not let an empty old full poll
                        # overwrite the new frame's native holding roster.
                        calls['monitor_frame_admission_skipped'] += 1
                        return 0
                    previous = getattr(batch_context, 'admitted', False)
                    batch_context.admitted = admitted
                    try:
                        if admitted:
                            calls['monitor_cycle'] += 1
                            if kwargs.get('only_codes') is not None:
                                calls['monitor_ws_wake_dispatch'] += 1
                            else:
                                calls['monitor_full_poll'] += 1
                        result = native_once(*args, **kwargs)
                        if (admitted and kwargs.get('only_codes') is not None
                                and frame_state['wake_generation'] == generation and wake_requested.is_set()):
                            completed_wake_codes.update(kwargs['only_codes'])
                            if wanted_wake_codes <= completed_wake_codes:
                                fast_complete.set()
                        return result
                    finally:
                        batch_context.admitted = previous

            monitor.run_once = observed_once
            monitor.start()
            yield Workload()
        finally:
            if monitor is not None:
                monitor.stop()
                if monitor.running:
                    raise ValueError('stop_runtime_monitor_drain_timeout')
            for logger in loggers.values():
                for handler in logger.handlers:
                    handler.close()
            engine.dispose()
