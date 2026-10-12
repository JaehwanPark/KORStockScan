"""Diagnostic lifecycle, source-only labels and readiness; no broker/provider I/O."""
from collections import OrderedDict
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from types import SimpleNamespace
import json
import threading
import pytest

from src.engine.monitoring import runtime_performance as R
from src.engine.scalping import reversal_source_diagnostics as D
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_shared_ledger as L
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal as K
from src.scanners.zero_base_discovery_queue import DiscoveryQueue
from src.engine.scalping.zero_base_probe import consumer_readiness

T = datetime(2026, 10, 12, 10, tzinfo=K.KST).timestamp()


def quote(seq, stamp=None, price=100, valid=True, epoch=1):
    return [T+seq if stamp is None else stamp, epoch, seq, price, price, price, 10, 1, valid, 0, 0]


@pytest.fixture
def native(monkeypatch):
    for name in ('_READY', '_SELECTED_READY', '_LIFECYCLE_PENDING'):
        monkeypatch.setattr(R, name, OrderedDict())
    for name in ('_ACTIVE_SELECTED', '_LIFECYCLE_EVICTED'):
        monkeypatch.setattr(R, name, {})
    monkeypatch.setattr(R, '_SELECTED_EVICTED', dict(claimed=0, expired_before_claim=0, unobservable=0))
    monkeypatch.setattr(R, '_LIFECYCLE_APPEND_DROPPED', 0)
    monkeypatch.setattr(R, '_LIFECYCLE_SINK', None)
    monkeypatch.setattr(R.time, 'time', lambda: T+1)
    band = C.cell_key('123456', 'REGULAR', 100)
    scope = ('123456', 'SOR', '123456_AL', 'REGULAR', '2026-10-12', band)
    event = dict(epoch=T, event_id='event', signal_id='signal', native_epoch=1, native_sequence=0,
        symbol='123456', source_item='123456_AL', venue='SOR', market='REGULAR', confirmation_price=100,
        branch_signals={'first': {'decision_phase': 'FIRST_UPTICK', 'event_id': 'event'}})
    ready = dict(event=event, claimed=False)
    state = SimpleNamespace(generation='scope', ready=[ready],
        legacy=SimpleNamespace(turn={'event_id': 'event'}, last=quote(0), segment_start=T))
    backend = SimpleNamespace(_LOCK=threading.RLock(), _STATES={scope: state}, _GENERATION='family',
        _CLAIMS={}, _FAMILY=dict(schema='continuous_reversal_policy_v6', family_sha256='family',
        machine_cells={band: {'routes': {'SOR': dict(backend='union_v6', scope_execution_hash='scope',
        payload={'branches': [{'branch_id': 'first'}, {'branch_id': 'momentum'}]})}}}))
    return backend, scope, state, event


def observe(native, at=T):
    backend, scope, *_ = native
    R.record_native_ready(backend, *scope[:4], at)
    return next(iter(R._SELECTED_READY.values()))


def test_raw_first_can_be_ineligible_without_ever_being_a_delivery_miss(native):
    native[2].legacy.turn = None
    before = deepcopy(native[2].ready)
    row = observe(native)
    assert row['terminal'] == 'invalidated_before_claim'
    assert row['first_eligible_seen'] is None
    assert native[2].ready == before
    assert R.snapshot()['native_signal_lifecycle']['count'] == 1


def test_later_first_invalidation_preserves_valid_interval_and_main_visit(native):
    observe(native)
    R.record_native_visit('123456', 'SOR', '123456_AL', 'REGULAR', T+.2)
    native[2].legacy.turn = {'event_id': 'new_low'}
    row = observe(native, T+.4)
    assert row['terminal'] == 'invalidated_before_claim'
    assert row['main_first_visit'] == T+.2
    assert row['transition_interval'] == [T, T+.4]


def test_independent_surviving_branch_keeps_native_eligibility(native):
    native[3]['branch_signals']['momentum'] = {'decision_phase': 'MOMENTUM_CROSS', 'event_id': 'momentum'}
    native[2].legacy.turn = None
    row = observe(native)
    assert row['terminal'] is None
    assert row['branch_survival'] == {'first': False, 'momentum': True}


@pytest.mark.parametrize('change,reason', [('source', 'source_or_guard_blocked_before_claim'),
    ('epoch', 'source_or_guard_blocked_before_claim'), ('removed', 'unobservable')])
def test_source_and_missing_ready_are_not_all_expired(native, change, reason):
    observe(native)
    if change == 'source': native[2].legacy.last[8] = False
    if change == 'epoch': native[2].legacy.last[1] = 2
    if change == 'removed': native[2].ready.clear()
    row = observe(native, T+.3)
    assert row['terminal'] == reason


def test_age_only_timeout_remains_unobservable_and_append_is_real(native, monkeypatch, tmp_path):
    observe(native)
    monkeypatch.setattr(R.time, 'time', lambda: T+6)
    counts = R.snapshot()
    assert counts['selected_native_coverage']['expired_before_claim'] == 1
    assert counts['selected_native_coverage']['age_only_not_delivery_failure'] is True
    assert counts['native_signal_lifecycle']['counts']['unobservable'] == 1
    from src.utils import pipeline_event_logger as E
    monkeypatch.setattr(E, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(E, 'log_info', lambda *a: None)
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = E.BoundedObservationQueue(executor)
        R.set_lifecycle_sink(queue.submit)
        R.flush_lifecycle()
        assert queue.close(timeout=5)
        assert queue.snapshot()['append_confirmed'] == 1
    records = [json.loads(line) for path in (tmp_path/'pipeline_events').glob('*.jsonl') for line in path.read_text().splitlines()]
    capsule = json.loads(records[-1]['fields']['native_signal_lifecycle'])
    assert capsule['terminal'] == 'unobservable'
    assert capsule['original_deadline'] == T+5
    assert capsule['process_start_ticks'] == R._PROCESS_START_TICKS
    from src.engine.pipeline_event_summary import execution_projection_identity
    part = next((tmp_path/'threshold_cycle').glob('date=*/family=entry_mechanical_momentum/part-execution-*'))
    projection = json.loads(part.read_text().splitlines()[-1])
    assert json.loads(projection['fields']['native_signal_lifecycle']) == capsule
    assert projection['execution_source_event_sha256'] == execution_projection_identity(projection)


def test_claim_joins_exact_native_scope_not_signal_id_alone(native):
    row = observe(native)
    claim = dict(snapshot=[native[3], {}], generation='wrong')
    R.record_selected_native_claim(claim, family_sha256='family', now=T+.2)
    assert row['claimed'] is False
    claim['generation'] = 'scope'
    R.record_selected_native_claim(claim, family_sha256='other', now=T+.2)
    assert row['claimed'] is False
    R.record_selected_native_claim(claim, family_sha256='family', now=T+.2)
    assert row['claimed'] and row['claimed_epoch'] == T+.2
    assert R.snapshot()['native_signal_lifecycle']['counts']['claimed'] == 1


def test_eviction_and_observation_queue_rejection_are_explicit(native, monkeypatch):
    monkeypatch.setattr(R, '_LIMIT', 2)
    for i in range(3):
        native[3]['signal_id'] = 'signal'+str(i)
        observe(native, T+i*.1)
    counts = R.snapshot()['native_signal_lifecycle']
    assert counts['count'] == 3 and counts['counts']['unobservable'] >= 1
    R.set_lifecycle_sink(lambda *a: {'status': 'unavailable'})
    R.flush_lifecycle()
    assert R.snapshot()['native_signal_lifecycle']['append_admission_dropped'] == 3


def test_compact_predicates_do_not_copy_raw_registration(native):
    B, scope, state, event = native
    claim = dict(token='native-token', generation='scope', backend='operating_v6', snapshot=[event, {}],
        source_registration_receipt={'sha256': 'registration', 'snapshot': ['large-input']})
    B._CLAIMS['native-token'] = dict(scope=scope, snapshot=claim['snapshot'], generation='scope')
    state.legacy.last[1] = 2
    state.legacy.turn = None
    with B._LOCK:
        receipt = D.compact_claim_state(B, claim, 'family', T+.3, 'reversal_signal_path_changed')
    assert receipt['branch_survival']['first'] is False
    assert 'native_epoch_matches' in receipt['failed_predicates']
    assert receipt['registration_sha256'] == 'registration'
    assert receipt['scope_execution_hash'] == 'scope'
    assert not any(k in receipt for k in ('snapshot', 'supplied_snapshot', 'claim_token'))
    assert 'large-input' not in json.dumps(receipt)


def test_consumer_readiness_requires_actual_dependencies_and_no_secrets():
    event = threading.Event(); event.set()
    ws = SimpleNamespace(websocket=object(), _session_ready=event, _stop_event=threading.Event(),
                         _market_data_transport_epoch=3, uri='wss://api.kiwoom.com/api/dostk/websocket')
    kwargs = dict(ws_manager=ws, ai_engine=object(), token='secret-test', enabled=True, family_sha256='f', now_epoch=T)
    assert consumer_readiness(**kwargs)['ready']
    for field, value in [('ws_manager', None), ('ai_engine', None), ('token', ''), ('enabled', False), ('family_sha256', None)]:
        receipt = consumer_readiness(**dict(kwargs, **{field: value}))
        assert receipt['ready'] is False and 'secret-test' not in json.dumps(receipt)
    event.clear()
    assert consumer_readiness(**kwargs)['reason'] == 'ws_session_not_ready'


def test_readiness_generation_binds_reconnect_date_policy_and_runtime_objects(monkeypatch):
    from src.engine.scalping.zero_base_probe import readiness_issue, kiwoom_utils
    monkeypatch.setattr(kiwoom_utils, 'KIWOOM_BASE_URL', 'https://api.kiwoom.com')
    event = threading.Event(); event.set()
    ws = SimpleNamespace(websocket=object(), _session_ready=event, _stop_event=threading.Event(),
        _market_data_transport_epoch=3, uri='wss://api.kiwoom.com/api/dostk/websocket')
    kwargs = dict(ws_manager=ws, ai_engine=object(), token='never-publish-me', enabled=True,
                  family_sha256='family', now_epoch=T)
    old = consumer_readiness(**kwargs)
    assert readiness_issue(old, consumer_readiness(**dict(kwargs, now_epoch=T+1))) == ''
    for key, value in [('family_sha256','new'), ('ai_engine',object()), ('token','replaced'), ('now_epoch',T+86400)]:
        new = consumer_readiness(**dict(kwargs, **{key:value}))
        assert readiness_issue(old, new) == 'consumer_readiness_generation_changed'
        assert 'never-publish-me' not in json.dumps(new)
    ws._market_data_transport_epoch = 4
    assert readiness_issue(old, consumer_readiness(**kwargs)) == 'consumer_readiness_generation_changed'
    ws.uri = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'
    assert consumer_readiness(**kwargs)['reason'] == 'auth_environment_mismatch'


def test_native_wake_only_first_eligibility_and_no_authority(native, monkeypatch):
    event = threading.Event()
    monkeypatch.setattr(R, '_NATIVE_READY_EVENT', event)
    observe(native)
    assert event.is_set() and not native[2].ready[0]['claimed']
    event.clear()
    for _ in range(10): observe(native, T+.1)
    assert not event.is_set()
    native[2].legacy.turn = None
    observe(native, T+.2)
    assert not event.is_set()


def test_worker_rechecks_generation_before_physical_registration(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as main
    current = {'ready': True, 'runtime_generation': 'one'}
    tasks, results = [], []
    monkeypatch.setattr(main, '_zero_base_runtime_enabled', lambda: True)
    monkeypatch.setattr(main, '_zero_base_active_conflict', lambda _: False)
    monkeypatch.setattr(main, 'evaluate_main_bot_control_exclusion', lambda _: SimpleNamespace(excluded=False))
    monkeypatch.setattr(main, 'scalping_session_venue_provenance', lambda _: {'market_session_regime':'KRX_REGULAR'})
    monkeypatch.setattr(main, '_zero_base_consumer_readiness', lambda: dict(current))
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_EXECUTOR', SimpleNamespace(submit=tasks.append))
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_SLOTS', threading.BoundedSemaphore(5))
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_IN_FLIGHT', set())
    monkeypatch.setattr(main, 'run_zero_base_probe', lambda *a, **k: pytest.fail('physical worker ran'))
    monkeypatch.setattr(main, 'event_bus', SimpleNamespace(publish=lambda e, p: results.append(p)))
    claim = dict(code='123456', route='krx_nxt_integrated', source_sha256='a'*64)
    main.handle_zero_base_probe_requested(dict(claim=claim, candidate=claim, consumer_readiness=dict(current)))
    current['runtime_generation'] = 'two'
    tasks.pop()()
    assert results[0]['reason'] == 'consumer_readiness_generation_changed'
    assert not main._ZERO_BASE_PROBE_IN_FLIGHT
    assert results[-1]['handoff_closed'] is True


def test_branch_descriptor_changes_to_actual_native_band_without_renewing_deadline(native, monkeypatch):
    from src.engine.scalping import reversal_current_backend as current
    B, scope, state, _ = native
    B._FAMILY['machine_cells'][scope[-1]]['routes']['SOR']['payload']['branches'] = [C.branch('G1')]
    new_key = C.cell_key('123456', 'REGULAR', 30000)
    cell = deepcopy(B._FAMILY['machine_cells'][scope[-1]])
    bid = 'manual_path_dca327a873720e53'
    cell['routes']['SOR'].update(scope_execution_hash='new_scope', payload={'branches':[C.branch(bid)]})
    B._FAMILY['machine_cells'][new_key] = cell
    monkeypatch.setattr(current, 'backend', lambda: B)
    candidate = SimpleNamespace(code='123456', route='krx_nxt_integrated', discovery_price=100)
    original = D.residence_requirements(candidate, T)
    B._STATES = {scope[:5]+(new_key,):state}
    state.generation = 'new_scope'
    state.legacy.last = quote(20, stamp=T+60, price=30000)
    state.coverage_snapshot = {bid:'UNKNOWN'}; state.coverage_identity = tuple(state.legacy.last[:3])
    state.root_previous = {bid:None}; state._feature_values={'ret':None}
    state._feature_key = tuple(state.legacy.last[:3])
    result = D.branch_readiness(candidate, now=T+60, deadline=T+61, original_requirements=original)
    assert result['scope_changed'] and result['policy_scope'] == new_key
    assert result['remaining_seconds'] == 1
    row = result['branch_descriptors'][bid]
    assert row['minimum_seconds'] == 61 and row['transition_required']
    assert row['detector_truth'] == 'UNKNOWN' and row['root_condition_truth'] == 'UNKNOWN'
    assert row['window_fits_remaining'] is False
    row['minimum_seconds'] = 0
    assert D.residence_requirements(candidate,T,actual_price=30000)['minimum_seconds'] == 61
    state.coverage_snapshot = {bid:'TRUE'}; state.root_previous[bid] = True
    result = D.branch_readiness(candidate, now=T+64, deadline=T+150)
    assert result['branch_descriptors'][bid]['detector_truth'] == 'UNKNOWN'  # old tick, no fresh inference


def test_source_clocks_do_not_reuse_depth_freshness_or_unbound_packet_clock():
    from src.engine.scalping.zero_base_probe import probe_ws_observation
    trade = dict(item='123456_AL', market_route='krx_nxt_integrated', transport_epoch=1,
                 route_sequence=2, observed_epoch=T, provider_trade_epoch=T-.1)
    depth = dict(trade, route_sequence=5, observed_epoch=T+3)
    trade['market_source_latency'] = dict(item='wrong', transport_epoch=1, route_sequence=2,
                                         packet_received_epoch=T, normalized_epoch=T+.1)
    snap = dict(market_data_transport_epoch=1,
                realtime_type_snapshots_by_route={'_AL|krx_nxt_integrated':{'0B':trade,'0D':depth}})
    clocks = probe_ws_observation(snap, code='123456', route='krx_nxt_integrated',
                                 after_epoch=T-1, now_epoch=T+3.2)['source_clocks']
    assert clocks['0B']['age_ms'] == 3200 and clocks['0D']['age_ms'] == 200
    assert clocks['0B']['packet_received_epoch'] is None
    assert clocks['0D']['provider_epoch'] == T-.1  # explicitly supplied, not copied by observer
    snap['realtime_type_snapshots_by_route']['_AL|krx_nxt_integrated'].pop('0B')
    clocks = probe_ws_observation(snap, code='123456', route='krx_nxt_integrated',
                                 after_epoch=T-1, now_epoch=T+3.2)['source_clocks']
    assert clocks['0B']['cause'] == 'unobservable' and clocks['0B']['age_ms'] is None


def test_native_depth_builder_to_probe_counts_exact_unique_receipts_only(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.engine.scalping.zero_base_probe import probe_ws_observation
    monkeypatch.setattr(__import__('src.engine.kiwoom_websocket',fromlist=['time']).time,'time',lambda:T)
    depth=KiwoomWSManager._build_micro_reversion_depth_tick('123456_AL',{'41':'100','61':'10','51':'99','71':'10'})
    depth.update(transport_epoch=1,route_sequence=2)
    key='_AL|krx_nxt_integrated'
    snap=dict(market_data_transport_epoch=1,recent_depth_ticks_by_route={key:[depth,dict(depth)]})
    result=probe_ws_observation(snap,code='123456',route='krx_nxt_integrated',after_epoch=T-1,now_epoch=T+1)
    assert result['exact_0d_count']==1
    assert result['arrival_quality']['recent_depth_ticks_by_route']['duplicates']==1
    snap['recent_depth_ticks_by_route'][key][1]['received_at_ms']+=1
    assert probe_ws_observation(snap,code='123456',route='krx_nxt_integrated',after_epoch=T-1,now_epoch=T+1)['exact_0d_count']==0
    depth.pop('market_route')
    snap['recent_depth_ticks_by_route'][key][1].pop('market_route')
    assert probe_ws_observation(snap,code='123456',route='krx_nxt_integrated',after_epoch=T-1,now_epoch=T+1)['exact_0d_count']==0


def test_long_wait_does_not_starve_short_cohort_and_retains_original_wait():
    queue = DiscoveryQueue('2026-10-12')
    for i in range(6):
        queue.observe(code=f'{i+100001}', route='krx_nxt_integrated', observed_epoch=T,
            source_sha256='a'*64, source_scope='observed_panel', received_epoch=T,
            market='KOSPI', source_kind='activity')
    requirements = lambda c, _: {'minimum_seconds': 0 if c.code=='100006' else 61}
    selected = queue.claim(now_epoch=T+1,limit=5,residence_requirements=requirements)
    assert len(selected) == 3 and selected[-1]['code'] == '100006'
    assert queue.residence_deferred == {'long_slot_wait':3}
    waiting = queue.snapshot()['candidates'][2]
    assert waiting['claim_count'] == 0 and waiting['residence_wait_since_epoch'] == T+1
    first = selected[0]
    assert queue.resolve(first,result='required_feature_insufficient',machine_action='',next_due_epoch=T+100,
                         handoff_id=first['physical_probe_lease_id'])
    assert queue.close_handoff(first,first['physical_probe_lease_id'])
    next_claim = queue.claim(now_epoch=T+10,limit=1,residence_requirements=requirements)[0]
    assert next_claim['code'] == '100003' and next_claim['residence_wait_seconds'] == 9
    assert next_claim['residence_deadline_epoch'] == T+160
    assert queue.snapshot()['candidates'][2]['residence_wait_since_epoch'] == 0


def test_probe_capsules_survive_actual_execution_writer_without_text_duplication(monkeypatch, tmp_path):
    import ast
    from src.utils import pipeline_event_logger as E
    monkeypatch.setattr(E,'DATA_DIR',tmp_path)
    logs=[];monkeypatch.setattr(E,'log_info',logs.append)
    capsule={'runtime_generation':'exact-generation','source_clocks':{'0B':{'age_ms':3200},'0D':{'age_ms':200}}}
    result=E.emit_pipeline_event('ENTRY_PIPELINE','test','123456','zero_base_probe_result',
        fields={'zero_base_branch_readiness':capsule,'physical_probe_lease_id':'lease',
                'zero_base_probe_reason':'feature_window_incomplete'})
    assert result['structured_append_succeeded']
    assert all('exact-generation' not in text for text in logs)
    part=next((tmp_path/'threshold_cycle').glob('date=*/family=entry_mechanical_momentum/part-execution-*'))
    projected=json.loads(part.read_text().splitlines()[-1])
    assert ast.literal_eval(projected['fields']['zero_base_branch_readiness']) == capsule


def test_real_bus_subscriber_without_readiness_cannot_reserve():
    from src.core.event_bus import EventBus
    class Bus(EventBus):
        _instance = None
        _lock = threading.Lock()
    bus = Bus()
    cb = lambda payload: None
    bus.subscribe('probe', cb)
    assert bus.consumer_readiness('probe')['ready'] is False
    cb.runtime_readiness = lambda: {'ready': True}
    assert bus.consumer_readiness('probe')['ready'] is True
    def check():
        bus.unsubscribe('probe', cb)  # proves callback does not run under bus lock
        return {'ready': False, 'reason': 'detached'}
    cb.runtime_readiness = check
    assert bus.consumer_readiness('probe')['reason'] == 'detached'


def test_required_history_allocates_long_slots_and_preserves_queued_candidates():
    queue = DiscoveryQueue('2026-10-12')
    for i in range(5):
        queue.observe(code=f'{i:06}', route='krx_nxt_integrated', observed_epoch=T,
            source_sha256='a'*64, source_scope='observed_panel', received_epoch=T)
    selected = queue.claim(now_epoch=T+1, limit=5, residence_requirements=lambda *a: {'minimum_seconds': 61})
    assert len(selected) == 2
    assert all(c['residence_deadline_epoch'] == T+151 for c in selected)
    assert len(queue.snapshot()['candidates']) == 5
    assert queue.claim(now_epoch=T+2, limit=5, residence_requirements=lambda *a: {'minimum_seconds': 61}) == []
    # A genuinely short independent branch can still use existing short slots.
    short = queue.claim(now_epoch=T+3, limit=5, residence_requirements=lambda *a: {'minimum_seconds': 0})
    assert len(short) == 3 and all(c['residence_deadline_epoch'] == T+63 for c in short)
    assert queue.in_flight_count() == 5


def test_history_is_definition_driven_not_maximum_confirmation_wait():
    assert D.branch_required_seconds(C.definition('manual_path_dca327a873720e53')) == 61
    assert D.branch_required_seconds(C.definition('G1')) == 60
    assert D.branch_required_seconds(C.definition('G3')) == 120
    assert D.branch_required_seconds({'root_contract': {'maximum_wait_seconds': 120}}) == 0


def research_record():
    identity = dict(source_date='2026-10-12', process_pid=123, process_start_ticks='456',
        symbol='005930', source_item='005930_AL', venue='SOR', market='REGULAR',
        native_epoch=1, family_sha256='family', scope_execution_hash='scope')
    contract = dict(cost_rate=.0023, target_net_pct=.4, stop_net_pct=-3., horizon_seconds=1800)
    record = dict(identity=identity, event=dict(epoch=T, native_sequence=0, entry_ask=100,
        signal_id='signal', branch_signals={'first': {}}), label_contract=contract,
        source_ref='existing-index-entry', cohort='PASS_invalidated')
    return record


@pytest.mark.parametrize('kind,expected', [('win', 'WIN'), ('stop', 'FAIL_STOP'), ('timeout', 'FAIL_TIMEOUT'),
    ('partial', 'EXCLUDED'), ('gap', 'EXCLUDED'), ('epoch', 'EXCLUDED'), ('ambiguous', 'EXCLUDED')])
def test_native_label_contract_uses_ask_bid_cost_and_exact_path(kind, expected):
    record = research_record()
    rows = [quote(0), quote(1, T+1, price=101 if kind == 'win' else 96 if kind == 'stop' else 100)]
    if kind == 'timeout': rows.append(quote(2, T+1800))
    if kind == 'gap': rows[1][2] = 3
    if kind == 'epoch': rows[1][1] = 2
    if kind == 'ambiguous': rows[1][0] = T
    window = dict(rows=rows, identity=record['identity'], label_contract=record['label_contract'], rows_sha256=P.digest(rows))
    report = L.native_lifecycle_outcomes([record], window_reader=lambda ref: window)
    assert report['outcomes'][0]['status'] == expected
    assert report['provider_calls'] == 0 and report['actual_order_submitted'] is False
    if expected == 'EXCLUDED': assert report['groups'][0]['win_rate'] is None


def test_missing_index_and_current_price_diagnostic_never_become_zero_winrate():
    record = research_record()
    report = L.native_lifecycle_outcomes([record], window_reader=lambda ref: None)
    assert report['outcomes'][0]['reason'] == 'indexed_source_missing'
    assert report['groups'][0]['win_rate'] is None
    record['label_contract'] = {'target_net_pct': .5}
    report = L.native_lifecycle_outcomes([record], window_reader=lambda ref: pytest.fail('invalid source should not read'))
    assert report['outcomes'][0]['reason'] == 'native_label_contract_mismatch'


def test_exact_deadline_needs_fresh_contiguous_evidence_and_a_visit(native):
    observe(native)
    R.record_native_visit('123456', 'SOR', '123456_AL', 'REGULAR', T+.5)
    for i in range(1, 6):
        native[2].legacy.last = quote(i)
        row = observe(native, T+i)
    assert row['terminal'] == 'observed_valid_until_deadline_unclaimed'


def test_replacement_is_only_named_when_new_turn_has_ready_evidence(native):
    observe(native)
    native[2].legacy.turn = {'event_id': 'replacement'}
    new_event = dict(native[3], event_id='replacement', signal_id='replacement_signal',
                     branch_signals={'first': {'decision_phase': 'FIRST_UPTICK', 'event_id': 'replacement'}})
    native[2].ready = [dict(event=new_event, claimed=False)]
    observe(native, T+.2)
    assert list(R._SELECTED_READY.values())[0]['terminal'] == 'replaced_before_claim'


def test_bad_quote_cannot_be_labeled_as_delivery_miss(native):
    native[2].legacy.last[4] = None
    assert observe(native)['terminal'] == 'source_or_guard_blocked_before_claim'


def test_readiness_race_releases_only_before_any_physical_worker(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as main
    monkeypatch.setattr(main, '_zero_base_runtime_enabled', lambda: True)
    monkeypatch.setattr(main, '_zero_base_active_conflict', lambda code: False)
    monkeypatch.setattr(main, 'evaluate_main_bot_control_exclusion', lambda code: SimpleNamespace(excluded=False))
    monkeypatch.setattr(main, 'scalping_session_venue_provenance', lambda now: {'market_session_regime': 'KRX_REGULAR'})
    monkeypatch.setattr(main, '_zero_base_consumer_readiness', lambda: {'ready': False, 'reason': 'ws_session_not_ready'})
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_EXECUTOR', SimpleNamespace(submit=lambda *a: pytest.fail('unsent request started')))
    outcomes = []
    monkeypatch.setattr(main, '_zero_base_probe_result', lambda *a: outcomes.append(a))
    claim = dict(code='123456', route='krx_nxt_integrated', source_sha256='a'*64)
    main.handle_zero_base_probe_requested(dict(claim=claim, candidate=claim))
    assert outcomes[0][1:] == ('policy_unavailable', 'ws_session_not_ready')


def test_real_selected_requirements_bind_scope_without_source_or_provider_io(native, monkeypatch):
    from src.engine.scalping import reversal_current_backend as current
    B, scope, _, _ = native
    B._FAMILY['machine_cells'][scope[-1]]['routes']['SOR']['payload']['branches'] = [
        {'branch_id': 'G1'}, {'branch_id': 'manual_path_dca327a873720e53'}]
    monkeypatch.setattr(current, 'backend', lambda: B)
    result = D.residence_requirements(SimpleNamespace(code='123456', route='krx_nxt_integrated', discovery_price=100), T)
    assert result['minimum_seconds'] == 60
    assert result['branch_required_seconds']['manual_path_dca327a873720e53'] == 61
    assert result['family_sha256'] == 'family' and result['scope_execution_hash'] == 'scope'


def test_selector_consumed_without_exact_claim_ack_is_not_eligible(native):
    observe(native)
    native[2].ready[0]['claimed'] = True
    row = observe(native, T+.2)
    assert row['terminal'] == 'unobservable'
    assert row['terminal_reason'] == 'selector_consumed_without_claim_receipt'
    assert row['claimed'] is False


def test_concurrent_observation_and_claim_conserve_one_signal(native):
    observe(native)
    claim = dict(snapshot=[native[3], {}], generation='scope')
    barrier = threading.Barrier(4)
    before = deepcopy(native[2].ready)
    def worker(index):
        barrier.wait(timeout=5)
        for _ in range(40):
            if index % 2:
                R.record_selected_native_claim(claim, family_sha256='family', now=T+.1)
            else:
                observe(native, T+.1)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(worker, range(4)))
    result = R.snapshot()['native_signal_lifecycle']
    assert result['count'] == 1 and result['counts']['claimed'] == 1
    assert native[2].ready == before


def test_duplicate_source_is_counted_once_but_conflict_excluded():
    record = research_record()
    rows = [quote(0), quote(1, price=101)]
    window = dict(rows=rows, identity=record['identity'], label_contract=record['label_contract'], rows_sha256=P.digest(rows))
    result = L.native_lifecycle_outcomes([record, deepcopy(record)], window_reader=lambda ref: window)
    assert len(result['outcomes']) == 1 and result['duplicate_count'] == 1
    conflict = deepcopy(record); conflict['event']['entry_ask'] = 99
    result = L.native_lifecycle_outcomes([record, conflict], window_reader=lambda ref: pytest.fail('conflicted join must not read'))
    assert result['outcomes'][0]['reason'] == 'duplicate_opportunity_conflict'
    assert result['groups'][0]['win_rate'] is None


def test_late_win_is_secondary_and_paired_veto_remains_false_negative_only_for_30m_win():
    record = dict(research_record(), auxiliary_verdict='VETO', symbol_type='samsung_fixed')
    rows = [quote(0), quote(1, T+1800), quote(2, T+1801, price=101)]
    window = dict(rows=rows, identity=record['identity'], label_contract=record['label_contract'], rows_sha256=P.digest(rows))
    result = L.native_lifecycle_outcomes([record], window_reader=lambda ref: window)
    assert result['outcomes'][0]['status'] == 'FAIL_TIMEOUT'
    assert result['outcomes'][0]['late_outcome']['status'] == 'WIN'
    assert result['paired']['false_negative'] == 0
    assert result['paired']['winner_retention'] is None
    rows[1][3:6] = [101, 101, 101]
    window['rows_sha256'] = P.digest(rows)
    result = L.native_lifecycle_outcomes([record], window_reader=lambda ref: window)
    assert result['paired']['false_negative'] == 1 and result['paired']['winner_retention'] == 0
    assert result['groups'][0]['symbol_type'] == 'samsung_fixed'


def test_unjoinable_identity_does_not_abort_other_research_rows():
    invalid = research_record(); invalid['identity']['native_epoch'] = {'bad': 1}
    result = L.native_lifecycle_outcomes([invalid, research_record()], window_reader=lambda ref: None)
    assert result['outcomes'][0]['reason'] == 'exact_identity_missing'
    assert result['outcomes'][1]['reason'] == 'indexed_source_missing'
