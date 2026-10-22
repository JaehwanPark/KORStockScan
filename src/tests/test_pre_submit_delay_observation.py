"""Same-symbol opportunity survival, finite observation and native due owner."""
from types import SimpleNamespace
import pytest
from src.engine.scalping import pre_submit_delay_observation as observer


@pytest.fixture(autouse=True)
def reset():
    observer._CLOSING = False
    observer._CLOSED_AT = None
    observer._ACTIVE.clear(); observer._HEAPS.clear(); observer._EXPIRIES.clear(); observer._RECENT.clear()
    observer._COUNTERS.clear(); observer.configure_sink(None)
    yield
    observer._ACTIVE.clear(); observer._HEAPS.clear(); observer._EXPIRIES.clear(); observer._RECENT.clear()
    observer.configure_sink(None)
    observer._CLOSING = False
    observer._CLOSED_AT = None


def test_shutdown_seals_admission_and_preserves_actual_censor_clock(monkeypatch):
    emitted = []
    observer.configure_sink(lambda callback, *args, **kw:
        emitted.append((args[3], kw)) or {'status': 'queued'})
    assert observer.register('123456', state('first'))
    assert observer.register('123456', state('second'))
    monkeypatch.setattr(observer.time, 'time', lambda: 61.25)
    assert observer.shutdown() is True
    assert not observer.register('123456', state('after-shutdown'))
    assert observer.health()['active'] == 0
    assert len(emitted) == 2
    for stage, envelope in emitted:
        fields = envelope['fields']
        assert stage == 'pre_submit_delay_intent_terminal'
        assert envelope['observed_at_epoch'] == fields['terminal_finished_at_epoch'] == 61.25
        assert fields['observation_only'] is True and fields['broker_order_forbidden'] is True
        assert fields['actual_order_submitted'] is False
    assert observer.shutdown() is True
    assert len(emitted) == 2


@pytest.mark.parametrize('failure', ['sampler', 'queue'])
def test_shutdown_failure_cannot_claim_censor_publication(monkeypatch, failure):
    emitted = []
    observer.configure_sink(lambda callback, *a, **kw:
        emitted.append(kw) or {'status': 'unavailable'})
    assert observer.register('123456', state('exact'))
    if failure == 'sampler':
        monkeypatch.setattr(observer, 'stop_sampler', lambda: False)
    assert observer.shutdown() is False
    assert not observer.register('123456', state('late'))
    if failure == 'sampler':
        assert emitted == [] and observer.health()['active'] == 1
    else:
        assert len(emitted) == 1 and observer.health()['queue_rejected'] == 1
        assert observer.shutdown() is False


def test_shutdown_serializes_commit_and_refuses_sampler_or_sink_reopening(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    entered, release, closing = threading.Event(), threading.Event(), threading.Event()
    stages = []
    def sink(callback, *args, **kwargs):
        stages.append(args[3])
        if args[3] == 'pre_submit_delay_committed':
            entered.set()
            assert release.wait(2)
        return {'status': 'queued'}
    observer.configure_sink(sink)
    def close():
        closing.set()
        return observer.shutdown()
    with ThreadPoolExecutor(max_workers=2) as executor:
        registration = executor.submit(observer.register, '123456', state('exact'), commit={'id': 'exact'})
        assert entered.wait(2)
        shutdown = executor.submit(close)
        assert closing.wait(2)
        release.set()
        assert registration.result(2) and shutdown.result(2)
    assert stages == ['pre_submit_delay_committed', 'pre_submit_delay_intent_terminal']
    assert observer.configure_sink(sink) is False
    assert observer.configure_sampler(lambda code: {}, lambda *a, **kw: None) is False
    assert observer.take_due('123456', 1000) == []


def test_failed_sampler_retry_retains_first_actual_shutdown_clock(monkeypatch):
    emitted = []
    observer.configure_sink(lambda callback, *args, **kw: emitted.append(kw) or {'status': 'queued'})
    assert observer.register('123456', state('exact'))
    monkeypatch.setattr(observer.time, 'time', lambda: 61.)
    monkeypatch.setattr(observer, 'stop_sampler', lambda: False)
    assert observer.shutdown() is False
    monkeypatch.setattr(observer.time, 'time', lambda: 200.)
    monkeypatch.setattr(observer, 'stop_sampler', lambda: True)
    assert observer.shutdown() is True
    assert emitted[0]['observed_at_epoch'] == 61.


def state(identity, stamp=10):
    return dict(id=identity, committed_at_epoch=stamp, remaining_sec=[0,30,60,120,180],
                route='KRX_NXT_INTEGRATED', quote_transport_epoch=1, decision_source_sha256='a'*64)


def test_two_opportunities_do_not_overwrite_and_completed_alias_cannot_reregister():
    assert observer.register('123456', state('first'))
    assert observer.register('123456', state('second'))
    due = observer.take_due('123456', 10)
    assert {r['id'] for r in due} == {'first','second'}
    for row in due:
        row['remaining_sec'].pop(0); observer.advance('123456', row)
    assert observer.health()['active'] == 2
    assert not observer.has_due('123456', 39)
    assert observer.has_due('123456', 40)
    observer.terminate('123456', reason='symbol_removed')
    assert observer.health()['active'] == 0
    assert not observer.register('123456', state('first'))


def test_silent_symbol_expires_without_tick_or_new_worker():
    observer.register('123456', state('silent'))
    observer.prune(194)
    assert observer.health()['active'] == 0
    assert observer.health()['expired_without_quote'] == 5
    assert observer.health()['writer_not_prepared'] == 1


def test_source_sampler_observes_short_horizons_without_a_main_target_visit(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    clock = [10.]
    emitted = []
    monkeypatch.setattr(observer.time, 'time', lambda: clock[0])
    monkeypatch.setattr(handlers, '_log_pre_submit_delay_event',
        lambda *a, **kw: emitted.append(kw) or True)
    depth = dict(item='123456_AL', market_route='KRX_NXT_INTEGRATED',
        transport_epoch=1, orderbook={'asks':[{'price':100,'volume':10}],
                                    'bids':[{'price':99,'volume':10}]})
    def read(code):
        assert code == '123456'
        return dict(market_data_transport_epoch=1,
            realtime_type_snapshots_by_route={'integrated': {'0D':
                dict(depth, observed_epoch=clock[0]-.01)}})
    value = state('short')
    value.update(remaining_sec=[0, 1, 3, 5],
                 observation_grid_version=observer.OBSERVATION_GRID_VERSION)
    observer.register('123456', value)
    for when in (10.02, 11.02, 13.02, 15.02):
        clock[0] = when
        assert observer.sample_due(read, handlers.observe_pre_submit_delay_quote) == 1
    assert [v['target_delay_sec'] for v in emitted] == [0,1,3,5]
    assert all(v['quote_valid'] for v in emitted)
    assert observer.health()['active'] == 0


def test_sampler_never_backdates_a_slow_or_stale_snapshot(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    clock = [11.]
    emitted = []
    monkeypatch.setattr(observer.time, 'time', lambda: clock[0])
    monkeypatch.setattr(handlers, '_log_pre_submit_delay_event',
        lambda *a, **kw: emitted.append(kw) or True)
    value = state('late')
    value.update(remaining_sec=[1], observation_grid_version=observer.OBSERVATION_GRID_VERSION)
    observer.register('123456', value)
    def read(code):
        clock[0] = 11.8
        return {}
    observer.sample_due(read, handlers.observe_pre_submit_delay_quote)
    assert emitted[0]['quote_valid'] is False
    assert emitted[0]['quote_source_reason'] == 'horizon_late_or_early'
    assert emitted[0]['quote_observed_at_epoch'] == 11.8


def test_sampling_cannot_escape_before_its_commit_is_admitted(monkeypatch):
    seen = []
    def sink(*a, **k):
        seen.extend(observer.take_due('123456', 10))
        return {'status':'queued'}
    observer.configure_sink(sink)
    assert observer.register('123456', state('exact'), commit={'id':'exact'})
    assert not seen
    assert len(observer.take_due('123456', 10)) == 1


def test_same_symbol_due_intents_share_exact_depth_without_sharing_identity(monkeypatch):
    from src.engine import sniper_state_handlers as h
    scans, emitted = [], []
    depth = dict(item='123456_AL', market_route='KRX_NXT_INTEGRATED', transport_epoch=1,
        observed_epoch=9.9, orderbook={'asks':[{'price':100,'volume':10}],
                                     'bids':[{'price':99,'volume':10}]})
    monkeypatch.setattr(h, '_pre_submit_delay_exact_depth', lambda *a: scans.append(a) or depth)
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    observer.register('123456', state('first'))
    observer.register('123456', state('second'))
    h.observe_pre_submit_delay_quote({'code':'123456'}, '123456',
                                     {'market_data_transport_epoch':1}, now_ts=10)
    assert len(scans) == 1 and len(emitted) == 2
    assert {row['delay_intent_id'] for row in emitted} == {'first','second'}
    assert all(row['quote_valid'] for row in emitted)
    assert len({row['route_depth_source_sha256'] for row in emitted}) == 1


def test_per_symbol_limit_includes_popped_inflight_rows():
    for n in range(observer.MAX_PER_SYMBOL):
        assert observer.register('123456', state(str(n)))
    observer.take_due('123456', 10)
    assert not observer.register('123456', state('overflow'))


def test_positive_due_rejects_unrelated_pass_and_expired_original_deadline(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.scanner_async_eval import ASYNC_CONSUMPTION
    from src.engine.scalping.pre_submit_delay_tuning import decision_type_snapshot
    frozen = decision_type_snapshot(price=100,ask=100,bid=99,venue='KRX',session='REGULAR')
    due = dict(schema='pre_submit_delay_policy_v2', id='intent', delay_sec=30,
        policy_sha256='policy', machine_key=('old', 'oldsha'), machine_policy_sha256='machine',
        ai_policy_sha256='ai', ai_effective_assessment='PASS', planned_qty=5,price_cap=100,
        route='KRX_NXT_INTEGRATED', decision_type=frozen, due_monotonic=50,due_epoch=100,
        successor_request_id='native-successor')
    machine = dict(entry_mechanistic_action='ENTER_NOW',evaluation_attempt_id='new',
        machine_observation_sha256='newsha', entry_mechanistic_policy_sha256='machine',
        entry_ai_soft_policy_sha256='ai',entry_ai_effective_assessment='PASS')
    policy = dict(status='loaded',delay_sec=30,policy_sha256='policy')
    monkeypatch.setattr(handlers.time,'monotonic',lambda:51)
    def matches(result):
        token=ASYNC_CONSUMPTION.set({'original_result':result})
        try:
            return handlers.pre_submit_delay_due_matches(due,policy,machine,frozen,
                quote_route='KRX_NXT_INTEGRATED',requested_qty=5,final_price=99)
        finally:
            ASYNC_CONSUMPTION.reset(token)
    right=SimpleNamespace(request_id='native-successor',submitted_epoch=100,
        completed_epoch=103,deadline_epoch=105,ai_payload={'evaluation_attempt_id':'new'})
    assert matches(right)
    assert not matches(SimpleNamespace(**{**vars(right),'request_id':'unrelated'}))
    assert not matches(SimpleNamespace(**{**vars(right),'completed_epoch':106}))
    assert not matches(SimpleNamespace(**{**vars(right),'submitted_epoch':99}))
    monkeypatch.setattr(handlers.time,'monotonic',lambda:56)
    assert not matches(right)


def test_rejected_writer_does_not_leave_orphan_observations_or_empty_symbol_heaps():
    observer.configure_sink(lambda *a,**k:{'status':'rejected'})
    assert observer.register('123456',state('lost'),commit={'id':'lost'}) is False
    assert not observer._HEAPS and observer.health()['active']==0
    for n in range(observer.MAX_ACTIVE):
        assert observer.register('123456'+str(n),state(str(n)))
    assert observer.register('other',state('overflow')) is False
    assert 'other' not in observer._HEAPS
    observer.take_due('1234560',10)
    observer.shutdown()
    assert observer.health()['active']==0


def test_delayed_append_preserves_original_quote_occurrence_and_partition(tmp_path,monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from types import SimpleNamespace
    from src.utils import pipeline_event_logger as logger
    from src.utils.constants import TRADING_RULES
    from dataclasses import replace
    monkeypatch.setattr(logger,'DATA_DIR',tmp_path)
    monkeypatch.setattr(logger,'TRADING_RULES',replace(TRADING_RULES,PIPELINE_EVENT_JSONL_ENABLED=True))
    monkeypatch.setattr(logger,'log_info',lambda *a,**k:None)
    monkeypatch.setattr(logger,'_get_producer_compactor',lambda:SimpleNamespace(submit=lambda *a,**k:None))
    queued=[]
    def sink(fn,*args,**kwargs):
        kwargs.pop('observation_category')
        queued.append((fn,args,kwargs));return {'status':'queued'}
    observer.configure_sink(sink)
    original=datetime.fromisoformat('2026-10-08T19:59:00+09:00').timestamp()
    assert observer.append('123456','stock','pre_submit_delay_quote_observed',{'quote_observed_at_epoch':original})
    fn,args,kwargs=queued[0]
    receipt=fn(*args,**kwargs)
    assert receipt['emitted_date']=='2026-10-08'
    assert datetime.fromisoformat(receipt['emitted_at']).timestamp()==original
    assert (tmp_path/'pipeline_events/pipeline_events_2026-10-08.jsonl').is_file()


def _book(at):
    return dict(item='123456_AL', market_route='KRX_NXT_INTEGRATED', transport_epoch=1,
        observed_epoch=at, orderbook={'asks':[{'price':100,'volume':10}],
                                     'bids':[{'price':99,'volume':10}]})


def _native_reference_result():
    from copy import deepcopy
    event = dict(symbol='123456', source_item='123456_AL', event_id='event', signal_id='signal', epoch=99.5,
                 confirmation_price=100)
    return SimpleNamespace(code='123456', completed_epoch=100,
        native_claim={'generation':'c'*64, 'token':'d'*64, 'snapshot':[event,{}]},
        ai_payload={'machine_observation_sha256':'a'*64,'evaluation_attempt_id':'evaluation',
            'entry_mechanistic_policy_sha256':'b'*64,
            'continuous_reversal_event_id':'event','continuous_reversal_signal_id':'signal',
            'entry_mechanistic_policy_decision':{'scope_execution_hash':'c'*64,
                'machine_component_sha256':'b'*64,'event':deepcopy(event),
                'event_id':'event','signal_id':'signal'}})


def test_reference_uses_native_scope_and_machine_manifest_without_quote_fallback():
    result = _native_reference_result()
    fields = observer.signal_reference_fields(result, machine_sha256='a'*64,
                                               evaluation_attempt_id='evaluation')
    assert fields == dict(signal_reference_contract_version='native_confirmation_price_v1',
        original_signal_reference_price=100, original_signal_reference_epoch=99.5,
        original_signal_id='signal')
    assert observer.signal_reference_fields(result, machine_sha256='f'*64) == {}
    assert observer.signal_reference_fields(result, evaluation_attempt_id='unrelated') == {}
    assert observer.signal_reference_fields(SimpleNamespace(ai_payload={}, prepared_context={
        'ws_data':{'curr':12345}})) == {}


@pytest.mark.parametrize('mutation', ['symbol','item','generation','token','proof','signal','future','nan','bool'])
def test_reference_rejects_unbound_or_invalid_native_values(mutation):
    result = _native_reference_result()
    event = result.native_claim['snapshot'][0]
    if mutation == 'symbol': result.code = '654321'
    elif mutation == 'item': event['source_item'] = '654321_AL'
    elif mutation == 'generation': result.native_claim['generation'] = 'f'*64
    elif mutation == 'token': result.native_claim['token'] = 'missing'
    elif mutation == 'proof': result.ai_payload['entry_mechanistic_policy_decision']['event']['confirmation_price'] = 200
    elif mutation == 'signal': result.ai_payload['continuous_reversal_signal_id'] = 'unrelated'
    else:
        field, value = ('epoch',101) if mutation == 'future' else ('confirmation_price', float('nan') if mutation == 'nan' else True)
        event[field] = value
        result.ai_payload['entry_mechanistic_policy_decision']['event'][field] = value
    assert observer.signal_reference_fields(result) == {}


def test_signal_registration_binds_grid_before_hash_and_uses_short_clock(monkeypatch):
    from src.engine import sniper_state_handlers as h
    from src.engine.scalping.pre_submit_delay_tuning import decision_source_sha256, _quote_source_issue
    commits, quotes = [], []
    def sink(fn, *args, **kwargs):
        commits.append(kwargs['fields'])
        return {'status':'queued'}
    observer.configure_sink(sink)
    result = SimpleNamespace(code='123456', request_id='request', completed_epoch=100,
        deadline_epoch=105, error_type=None, origin_fields={'market_session_bucket':'REGULAR'},
        prepared_context={'ws_data':{'market_data_transport_epoch':1}}, ai_payload={
            'entry_mechanistic_action':'ENTER_NOW','machine_observation_sha256':'a'*64,
            'evaluation_attempt_id':'evaluation','entry_ai_effective_assessment':{'effective_verdict':'PASS'}})
    assert observer.register_pass_result(result)
    commit = commits[0]
    assert commit['observation_horizons_sec'] == [0,1,3,5,30,60,120,180]
    assert commit['decision_source_sha256'] == decision_source_sha256(commit)
    assert commit['decision_source_sha256'] != decision_source_sha256({
        **commit,'observation_horizons_sec':[0,30,60,120,180]})
    monkeypatch.setattr(h, '_pre_submit_delay_exact_depth', lambda *a: _book(101.1))
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: quotes.append(kw) or True)
    h.observe_pre_submit_delay_quote({}, '123456', {'market_data_transport_epoch':1}, now_ts=101.2)
    assert [r['target_delay_sec'] for r in quotes] == [0,1]
    assert _quote_source_issue(commit, quotes[1]) is None
    assert quotes[1]['quote_valid'] is True
    # Shared legacy P0 still discloses its actual late capture; short research
    # applies its own P0 <=250ms qualification instead of backdating it.
    assert quotes[0]['actual_offset_sec'] == 1.2
    assert 'quote_contract_version' not in quotes[0]


def test_short_grid_does_not_backfill_missed_horizons(monkeypatch):
    from src.engine import sniper_state_handlers as h
    emitted = []
    monkeypatch.setattr(h, '_pre_submit_delay_exact_depth', lambda *a: _book(13.1))
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    row = {**state('short'), **observer.observation_contract(), 'remaining_sec':[1,3,5,30,60,120,180]}
    observer.register('123456', row)
    h.observe_pre_submit_delay_quote({}, '123456', {'market_data_transport_epoch':1}, now_ts=13.23456)
    assert [r['target_delay_sec'] for r in emitted] == [1,3]
    assert emitted[0]['quote_valid'] is False
    assert emitted[0]['quote_source_reason'] == 'horizon_late_or_early'
    assert emitted[1]['quote_valid'] is True
    assert all(r['quote_contract_version'] == 2 and r['observation_tolerance_sec'] == .25 for r in emitted)
    assert emitted[1]['target_due_at_epoch'] == 13
    assert emitted[1]['actual_offset_sec'] == emitted[1]['quote_observed_at_epoch'] - row['committed_at_epoch']
    assert emitted[1]['actual_offset_sec'] != round(emitted[1]['actual_offset_sec'], 3)
    assert observer._ACTIVE[('123456','short')]['remaining_sec'] == [5,30,60,120,180]


def test_horizon_budget_includes_late_rows_and_reschedules_untouched_states(monkeypatch):
    from src.engine import sniper_state_handlers as h
    emitted, scans = [], []
    monkeypatch.setattr(h, '_pre_submit_delay_exact_depth', lambda *a: scans.append(a) or _book(190))
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    for identity in ('first','second'):
        observer.register('123456', {**state(identity), **observer.observation_contract(),
                                    'remaining_sec':list(observer.OBSERVATION_HORIZONS)})
    h.observe_pre_submit_delay_quote({}, '123456', {'market_data_transport_epoch':1}, now_ts=190)
    assert len(emitted) == observer.MAX_HORIZONS_PER_TURN == 8
    assert len(scans) == 1
    assert observer.health()['active'] == 1
    assert observer.has_due('123456', 190)
    h.observe_pre_submit_delay_quote({}, '123456', {'market_data_transport_epoch':1}, now_ts=190)
    assert len(emitted) == 16 and observer.health()['active'] == 0
    assert {r['delay_intent_id'] for r in emitted} == {'first','second'}


def test_legacy_grid_and_hash_contract_are_preserved(monkeypatch):
    from src.engine import sniper_state_handlers as h
    from src.engine.scalping.pre_submit_delay_tuning import DELAYS_SEC, quote_source_sha256
    emitted = []
    monkeypatch.setattr(h, '_pre_submit_delay_exact_depth', lambda *a: _book(42.9))
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    observer.register('123456', {**state('legacy'), 'remaining_sec':[30,60,120,180]})
    h.observe_pre_submit_delay_quote({}, '123456', {'market_data_transport_epoch':1}, now_ts=43)
    assert tuple(DELAYS_SEC) == (0,30,60,120,180)
    assert len(emitted) == 1 and emitted[0]['quote_valid'] is True
    assert 'quote_contract_version' not in emitted[0]
    assert emitted[0]['quote_source_sha256'] == quote_source_sha256(emitted[0])


def _intent():
    return dict(schema='pre_submit_delay_policy_v2', id='delay', delay_sec=30,
        committed_at_epoch=10, due_epoch=40, due_monotonic=50,
        machine_key=('old','a'*64), machine_observation_sha256='a'*64,
        decision_source_sha256='b'*64, successor_request_id='new-request',
        successor_submitted_epoch=40)


def test_due_expiry_records_exactly_one_terminal_with_lineage(monkeypatch):
    from src.engine import sniper_state_handlers as h
    emitted = []
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append((a[2],kw)) or True)
    stock = {'_pre_submit_delay_due':_intent()}
    assert h.expire_untriggered_pre_submit_delay(stock, '123456', now_mono=56,
        reason='recheck_not_ready_before_expiry')
    assert not h.expire_untriggered_pre_submit_delay(stock, '123456', now_mono=57,
        reason='recheck_not_ready_before_expiry')
    assert [s for s,_ in emitted] == ['pre_submit_delay_recheck_observed','pre_submit_delay_intent_terminal']
    terminal = emitted[-1][1]
    assert terminal['delay_intent_id'] == 'delay'
    assert terminal['original_evaluation_attempt_id'] == 'old'
    assert terminal['successor_request_id'] == 'new-request' and terminal['due_at_epoch'] == 40
    assert not terminal['actual_order_submitted']


def test_expired_due_callsite_uses_terminal_owner_before_removal():
    import inspect
    from src.engine import sniper_state_handlers as h
    source = inspect.getsource(h)
    marker = 'if (isinstance(due_delay, dict) and due_delay.get("schema") == "pre_submit_delay_policy_v2"'
    branch = source[source.index(marker):].split('\n\n', 1)[0]
    assert 'expire_untriggered_pre_submit_delay(stock, code, reason="recheck_not_ready_before_expiry")' in branch
    assert 'stock.pop' not in branch


@pytest.mark.parametrize('blocked_reason', ['buy_side_paused', 'operator_manual_control_excluded_symbol',
                                          'zero_base_pending_db'])
def test_watching_early_guard_return_still_closes_expired_delay(monkeypatch, blocked_reason):
    from src.engine import sniper_state_handlers as h
    emitted = []
    monkeypatch.setattr(h.time, 'monotonic', lambda:56)
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append((a[2],kw)) or True)
    def early_return(stock, *args, **kwargs):
        h._set_async_terminal(stock, blocked_reason)
    monkeypatch.setattr(h, '_handle_watching_state_impl', early_return)
    stock = {'_pre_submit_delay_due':_intent()}
    h.handle_watching_state(stock,'123456',{},None)
    h.handle_watching_state(stock,'123456',{},None)
    assert [s for s,_ in emitted].count('pre_submit_delay_intent_terminal') == 1
    assert '_pre_submit_delay_due' not in stock
    assert '_async_consumption_guard' not in stock


def test_watching_cleanup_keeps_nonexpired_and_uncertain_intents(monkeypatch):
    from src.engine import sniper_state_handlers as h
    emitted = []
    monkeypatch.setattr(h.time, 'monotonic', lambda:54)
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    monkeypatch.setattr(h, '_handle_watching_state_impl', lambda *a,**kw:None)
    stock = {'_pre_submit_delay_due':_intent()}
    h.handle_watching_state(stock,'123456',{},None)
    assert '_pre_submit_delay_due' in stock and not emitted
    monkeypatch.setattr(h.time, 'monotonic', lambda:56)
    def uncertain(*args, **kwargs):
        raise RuntimeError('uncertain')
    monkeypatch.setattr(h, '_handle_watching_state_impl', uncertain)
    with pytest.raises(RuntimeError, match='uncertain'):
        h.handle_watching_state(stock,'123456',{},None)
    assert '_pre_submit_delay_due' in stock and not emitted


@pytest.mark.parametrize('verdict', ['PASS','VETO','CAUTION','INSUFFICIENT'])
def test_recheck_binds_only_admitted_request_and_preserves_verdict(monkeypatch, verdict):
    from src.engine import sniper_state_handlers as h
    emitted = []
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    stock = {'_pre_submit_delay_due':_intent()}
    result = SimpleNamespace(request_id='unrelated', submitted_epoch=40, completed_epoch=42,
        deadline_epoch=45, status='completed', ai_payload={'evaluation_attempt_id':'new',
        'machine_observation_sha256':'c'*64, 'entry_mechanistic_action':'ENTER_NOW',
        'entry_ai_effective_assessment':{'effective_verdict':verdict}})
    assert not h._observe_pre_submit_delay_recheck(stock,'123456',recheck_status='completed',result=result)
    assert not emitted
    result.request_id = 'new-request'
    assert h._observe_pre_submit_delay_recheck(stock,'123456',recheck_status='completed',result=result,
                                              recheck_commit_allowed=False)
    assert not h._observe_pre_submit_delay_recheck(stock,'123456',recheck_status='completed',result=result)
    assert len(emitted) == 1 and emitted[0]['recheck_auxiliary_effective_action'] == verdict
    assert emitted[0]['successor_evaluation_attempt_id'] == 'new'
    assert emitted[0]['recheck_commit_allowed'] is False
    assert emitted[0]['actual_order_submitted'] is False
    assert 'resolved_machine_attempt_id' not in stock['_pre_submit_delay_due']


def test_submit_terminal_preserves_actual_recheck_and_submit_ids(monkeypatch):
    from src.engine import sniper_state_handlers as h
    emitted = []
    monkeypatch.setattr(h, '_log_pre_submit_delay_event', lambda *a, **kw: emitted.append(kw) or True)
    monkeypatch.setattr(h, '_log_entry_pipeline', lambda *a, **kw: None)
    monkeypatch.setattr(h, 'submit_attempt_fields', lambda *a: {
        'entry_submit_attempt_id':'submit-1','entry_submit_attempt_broker_accepted':False})
    stock = {'_pre_submit_delay_due':{**_intent(), 'resolved_machine_attempt_id':'new',
        'resolved_machine_observation_sha256':'c'*64,'successor_completed_epoch':42,
        'successor_deadline_epoch':45}}
    h._observe_entry_submit_finished(stock,'123456',False)
    h._observe_entry_submit_finished(stock,'123456',False)
    assert len(emitted) == 1
    assert emitted[0]['entry_submit_attempt_id'] == 'submit-1'
    assert emitted[0]['recheck_completed_at_epoch'] == 42
    assert emitted[0]['resolved_machine_attempt_id'] == 'new'
    assert not emitted[0]['actual_order_submitted']
    assert emitted[0]['terminal_reason'] == 'submit_call_returned_false'


def test_pending_horizons_retain_source_even_while_sampler_holds_due_state():
    assert observer.register('053800', state('incident', stamp=10))
    due = observer.take_due('053800', 40)
    assert not observer._HEAPS
    assert observer.should_retain_ws_subscription('053800', now_ts=40)
    assert not observer.should_retain_ws_subscription('other', now_ts=40)
    for row in due:
        row['remaining_sec'].clear()
        observer.advance('053800', row)
    assert not observer.should_retain_ws_subscription('053800', now_ts=40)


def test_retention_is_per_intent_bounded_and_shutdown_never_waits_for_horizons():
    assert observer.register('053800', state('first', stamp=10))
    assert observer.register('053800', state('second', stamp=20))
    assert observer.should_retain_ws_subscription('053800', now_ts=192.9)
    observer.discard('053800', 'first', reason='test_censored')
    assert observer.should_retain_ws_subscription('053800', now_ts=202.9)
    assert not observer.should_retain_ws_subscription('053800', now_ts=203)
    assert not observer.should_retain_ws_subscription('053800', now_ts=19)
    observer.configure_sink(lambda *a, **kw: {'status':'queued'})
    assert observer.shutdown()
    assert not observer.should_retain_ws_subscription('053800', now_ts=40)


def test_watch_expiry_retains_ws_cache_until_all_follow_up_quotes(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as main, kiwoom_websocket as ws
    from src.engine import sniper_state_handlers as handlers
    import asyncio
    import json
    from concurrent.futures import Future
    packets = []
    async def send(payload):
        packets.append(json.loads(payload))
    def schedule(coroutine, loop):
        result = Future()
        result.set_result(asyncio.run(coroutine))
        return result
    monkeypatch.setattr(ws.asyncio, 'run_coroutine_threadsafe', schedule)
    clock = [10.]
    monkeypatch.setattr(observer.time, 'time', lambda: clock[0])
    manager = ws.KiwoomWSManager('test-token')
    manager._market_data_transport_epoch = 7
    manager.websocket = SimpleNamespace(send=send)
    manager.loop = SimpleNamespace(is_running=lambda: True)
    manager._session_ready.set()
    manager.subscribed_codes = {'053800', '000001'}
    manager._registered_items_by_code = {'053800': ('053800_NX',), '000001': ('000001_AL',)}
    manager.realtime_data['000001'] = {}
    monkeypatch.setattr(main, 'WS_MANAGER', manager)
    monkeypatch.setattr(main, 'should_retain_ws_subscription', lambda *a, **kw: False)
    monkeypatch.setattr(main, '_is_scanner_promotion_pending_attach', lambda *a, **kw: False)
    monkeypatch.setattr(handlers, 'should_retain_rising_missed_nxt_post_block_subscription', lambda *a, **kw: False)
    commands, quotes = [], []
    def publish(topic, payload):
        assert topic == 'COMMAND_WS_UNREG'
        commands.extend(payload['codes'])
        manager._handle_unreg_event(payload)
    monkeypatch.setattr(main, 'event_bus', SimpleNamespace(publish=publish))
    monkeypatch.setattr(handlers, '_log_pre_submit_delay_event', lambda *a, **kw: quotes.append(kw) or True)
    value = state('incident')
    value.update(route='NXT_ONLY', quote_transport_epoch=7, remaining_sec=[30,60,120,180])
    assert observer.register('053800', value)
    # A watch/order terminal is independent of the outstanding source lease.
    for horizon in (30,60,120,180):
        clock[0] = 10. + horizon + .02
        manager.realtime_data['053800'] = {'realtime_type_snapshots_by_route': {'nxt': {'0D': {
            'item':'053800_NX', 'market_route':'NXT_ONLY', 'transport_epoch':7,
            'observed_epoch':clock[0]-.01, 'orderbook':{
                'asks':[{'price':91900,'volume':10}], 'bids':[{'price':91800,'volume':10}]}}}}}
        main._prune_ws_subscriptions_for_inactive_targets([{'code':'053800','status':'EXPIRED'}])
        # Even an independently generated unregistration command is checked.
        manager._handle_unreg_event({'codes':['053800']})
        assert manager.get_pre_submit_delay_depth('053800')['realtime_type_snapshots_by_route']
        assert observer.sample_due(manager.get_pre_submit_delay_depth, handlers.observe_pre_submit_delay_quote) == 1
    assert [q['target_delay_sec'] for q in quotes] == [30,60,120,180]
    assert all(q['quote_valid'] for q in quotes)
    assert commands == ['000001']
    assert len(packets) == 1 and packets[0]['trnm'] == 'REMOVE'
    assert all(row['item'] == ['000001_AL'] for row in packets[0]['data'])
    main._prune_ws_subscriptions_for_inactive_targets([])
    assert commands == ['000001', '053800']
    assert '053800' not in manager.realtime_data
    assert '053800' not in manager.subscribed_codes
    assert len(packets) == 2 and packets[1]['trnm'] == 'REMOVE'
    assert all(row['item'] == ['053800_NX'] for row in packets[1]['data'])


def test_budget_expiry_preserves_only_pending_observation_source(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as main
    commands = []
    monkeypatch.setattr(observer.time, 'time', lambda: 40.)
    monkeypatch.setattr(main, 'should_retain_ws_subscription', lambda *a, **kw: False)
    monkeypatch.setattr(main.sniper_state_handlers, 'should_retain_rising_missed_nxt_post_block_subscription', lambda *a, **kw: False)
    monkeypatch.setattr(main, 'emit_pipeline_event', lambda *a, **kw: None)
    monkeypatch.setattr(main, 'event_bus', SimpleNamespace(publish=lambda topic, payload: commands.extend(payload['codes'])))
    assert observer.register('053800', state('pending'))
    targets = [dict(code=code, name=code, strategy='SCALPING', status='WATCHING',
                    position_tag='SCANNER') for code in ('053800','000001')]
    main._expire_scalping_watch_budget_targets(targets[:], targets, reason='test_reallocation')
    assert commands == ['000001']
    assert targets == []  # The source lease does not keep a trading target alive.


@pytest.mark.parametrize('mutation', ['transport', 'stale', 'conflict'])
def test_retained_subscription_does_not_approve_invalid_quote(monkeypatch, mutation):
    from src.engine import sniper_state_handlers as handlers
    quotes = []
    monkeypatch.setattr(handlers, '_log_pre_submit_delay_event', lambda *a, **kw: quotes.append(kw) or True)
    value = state('invalid'); value['remaining_sec'] = [30]
    assert observer.register('053800', value)
    depth = dict(item='053800_AL', market_route='KRX_NXT_INTEGRATED', transport_epoch=1,
                 observed_epoch=40.01, orderbook={'asks':[{'price':100,'volume':10}],
                                               'bids':[{'price':99,'volume':10}]})
    partitions = {'integrated':{'0D':depth}}
    if mutation == 'transport': depth['transport_epoch'] = 2
    elif mutation == 'stale': depth['observed_epoch'] = 30.
    else: partitions['duplicate'] = {'0D':dict(depth)}
    assert observer.should_retain_ws_subscription('053800', now_ts=40.02)
    handlers.observe_pre_submit_delay_quote({}, '053800', dict(market_data_transport_epoch=1,
        realtime_type_snapshots_by_route=partitions), now_ts=40.02)
    assert len(quotes) == 1 and quotes[0]['quote_valid'] is False
