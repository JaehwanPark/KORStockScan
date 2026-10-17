"""Same-symbol opportunity survival, finite observation and native due owner."""
from types import SimpleNamespace
import pytest
from src.engine.scalping import pre_submit_delay_observation as observer


@pytest.fixture(autouse=True)
def reset():
    observer._ACTIVE.clear(); observer._HEAPS.clear(); observer._EXPIRIES.clear(); observer._RECENT.clear()
    observer._COUNTERS.clear(); observer.configure_sink(None)
    yield
    observer._ACTIVE.clear(); observer._HEAPS.clear(); observer._EXPIRIES.clear(); observer._RECENT.clear()
    observer.configure_sink(None)


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
