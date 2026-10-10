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
