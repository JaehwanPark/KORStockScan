"""Zero-base Main handoff must commit only a matching attached generation."""

import json
import time
import threading
from concurrent.futures import Future
from queue import Empty
from types import SimpleNamespace
import pytest

from src.engine import kiwoom_sniper_v2 as main
from src.engine import sniper_state_handlers as handlers
from src.engine import kiwoom_orders
from src.trading.market import session_contract


@pytest.fixture(autouse=True)
def _isolate_cleanup_retries(monkeypatch):
    monkeypatch.setattr(main, '_ZERO_BASE_CLEANUP_RETRIES', {})
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_CLOSING', threading.Event())
    monkeypatch.setattr(main, '_zero_base_consumer_readiness', lambda: {'ready': True, 'runtime_generation': 'fixture'})


@pytest.mark.parametrize('complete', [False, True])
def test_shutdown_drains_exact_lease_callbacks_before_socket_stop(monkeypatch, complete):
    inflight={'123456'}
    monkeypatch.setattr(main,'_ZERO_BASE_PROBE_IN_FLIGHT',inflight)
    clock=iter([0.,0.,.1,.2,.3])
    monkeypatch.setattr(main.time,'monotonic',lambda:next(clock))
    monkeypatch.setattr(main.time,'sleep',lambda _:None)
    def native_cleanup():
        assert main._ZERO_BASE_PROBE_CLOSING.is_set()
        if complete:inflight.clear()
    monkeypatch.setattr(main,'_retry_zero_base_cleanup',native_cleanup)
    assert main._drain_zero_base_probe_leases(timeout=.1) is complete
    assert bool(inflight) is not complete


def test_shutdown_admission_rejects_new_probe_without_holding_callback_lock(monkeypatch):
    monkeypatch.setenv('KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED','true')
    monkeypatch.setattr(main,'ACTIVE_TARGETS',[])
    monkeypatch.setattr(main,'_ZERO_BASE_PROBE_IN_FLIGHT',set())
    slots=threading.BoundedSemaphore(1)
    monkeypatch.setattr(main,'_ZERO_BASE_PROBE_SLOTS',slots)
    monkeypatch.setattr(main,'evaluate_main_bot_control_exclusion',lambda _:SimpleNamespace(excluded=False))
    monkeypatch.setattr(main,'scalping_session_venue_provenance',lambda _:dict(
        market_session_regime=main.session_contract.MARKET_SESSION_REGIME_KRX_REGULAR))
    monkeypatch.setattr(main,'_ZERO_BASE_PROBE_EXECUTOR',SimpleNamespace(
        submit=lambda _:pytest.fail('new worker after shutdown admission closed')))
    published=[]
    def publish(topic,payload):
        assert main._ZERO_BASE_PROBE_LOCK.acquire(blocking=False)
        main._ZERO_BASE_PROBE_LOCK.release()
        published.append(payload)
    monkeypatch.setattr(main,'event_bus',SimpleNamespace(publish=publish))
    assert main._drain_zero_base_probe_leases()
    request={k:_result()[k] for k in ('claim','candidate')}
    request['consumer_readiness']={'ready':True,'runtime_generation':'fixture'}
    main.handle_zero_base_probe_requested(request)
    assert published[-1]['reason']=='probe_executor_unavailable'
    assert slots.acquire(blocking=False)


class _Session:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def add(self, row):
        row.id = len(self.rows) + 1
        self.rows[row.id] = row

    def flush(self):
        pass

    def get(self, _model, record_id):
        return self.rows.get(record_id)


class _Record:
    def __init__(self, **fields):
        self.__dict__.update(fields)


def _result():
    now = time.time()
    claim = {
        "code": "123456", "route": "krx_nxt_integrated", "source_sha256": "b" * 64,
        "claim_count": 1,
    }
    return {
        "claim": claim, "candidate": {**claim, "name": "TEST"},
        "result": "assessed", "machine_action": "ENTER_NOW",
        "result_epoch": now, "probe_price": 10000,
        "machine_bundle_sha256": "a" * 64,
        "probe_trade_epoch": now, "probe_depth_epoch": now,
    }


def _prepare(monkeypatch):
    rows = {}
    targets = []
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
    monkeypatch.setattr(main, "ACTIVE_TARGETS", targets)
    monkeypatch.setattr(main, "RecommendationHistory", _Record)
    monkeypatch.setattr(main, "DB", SimpleNamespace(get_session=lambda: _Session(rows)))
    monkeypatch.setattr(
        main, "evaluate_main_bot_control_exclusion",
        lambda _code: SimpleNamespace(excluded=False),
    )
    monkeypatch.setattr(main, "is_scalping_buy_time_allowed", lambda _time: True)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "krx_regular", "market_session_regime": "KRX_REGULAR",
    })
    monkeypatch.setattr(main, "_scalping_attach_capacity_decision", lambda *_args: (True, [], {}))
    monkeypatch.setattr(main, "_scanner_scheduler_startup_mode", lambda: "blocking_v0")
    monkeypatch.setattr(main, "_zero_base_attach_receipt", lambda *_args, **_kwargs: None)
    return rows, targets


def test_enter_now_commits_only_matching_attached_watching_row(monkeypatch):
    rows, targets = _prepare(monkeypatch)

    def attach(payload):
        assert payload["market_data_route"] == "krx_nxt_integrated"
        assert payload["broker_route"] == "SOR"
        assert payload["effective_venue"] == "KRX"
        targets.append({
            "id": payload["record_id"], "code": payload["code"],
            "status": "WATCHING", "zero_base_pending_db": True,
        })
        return True

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", lambda payload, **_kwargs: attach(payload))
    assert main.handle_zero_base_machine_enter(_result()) is True
    assert rows[1].status == "WATCHING"
    assert "zero_base_pending_db" not in targets[0]
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert len(rows) == 1


def _native_main_handoff(monkeypatch, route="krx_nxt_integrated"):
    import os
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.engine.scalping import reversal_source_diagnostics as D
    receipt_fn = main._zero_base_attach_receipt
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "_zero_base_attach_receipt", receipt_fn)
    result = _result()
    result["claim"]["route"] = result["candidate"]["route"] = route
    venue, suffix = ("NXT", "_NX") if route == "nxt_only" else ("SOR", "_AL")
    if route == "nxt_only":
        monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
            "market_session_bucket": "krx_like_premarket", "market_session_regime": "krx_like_premarket"})
    code = result["claim"]["code"]
    item = code + suffix
    now = time.time()
    expected = dict(snapshot=({"symbol": code, "venue": venue, "source_item": item,
                              "native_epoch": 88, "epoch": now, "signal_id": "original-signal",
                              "event_id": "original-event"}, {}),
                    deadline_epoch=now + 5, deadline_perf=time.perf_counter() + 5,
                    observer_pid=os.getpid(), observer_start_ticks=D._PROCESS_START_TICKS)
    result.update(native_observation=expected, ws_handoff_id="lease-native",
                  physical_probe_lease_id="lease-native")
    manager = KiwoomWSManager("test-token")
    manager.websocket = SimpleNamespace()  # Local ownership transfer sends no packets.
    manager._session_ready.set()
    manager._market_data_transport_epoch = 88
    manager.subscribed_codes = {code}
    manager._registered_items_by_code[code] = (item,)
    manager._registered_item_epochs[item] = 88
    manager._registered_item_types[item] = ("0B", "0D")
    manager._exact_probe_item_leases[item] = {"lease_id": "lease-native", "epoch": 88}
    manager._micro_reversion_observation_only_codes.add(code)
    manager._micro_reversion_observation_only_items.add(item)
    monkeypatch.setattr(main, "WS_MANAGER", manager)
    monkeypatch.setattr(main, "_ZERO_BASE_HANDOFFS", {
        "lease-native": {"event": threading.Event(), "outcome": None}})
    monkeypatch.setattr(main, "_ZERO_BASE_MAIN_PENDING", {"lease-native"})
    monkeypatch.setattr(main, "_resolve_stock_marcap", lambda *_args: 0)
    monkeypatch.setattr(main, "_scanner_identity_guard", lambda *_args: (True, {}))
    monkeypatch.setattr(main, "_log_scanner_runtime_target_attach", lambda *_args, **_kwargs: None)
    events = []
    def publish(topic, payload):
        events.append((topic, payload))
        if topic == "COMMAND_WS_REG":
            # Deterministically enter the actual REMOVE-before-REG boundary.
            manager._registered_item_epochs.pop(item, None)
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(publish=publish))
    monkeypatch.setattr(main, "emit_pipeline_event", lambda *_args, **kw: events.append(("receipt", kw["fields"])))
    claims = []
    monkeypatch.setattr(D, "claim_expected_snapshot", lambda p: (claims.append(p) or {"token": "native-once"}))
    return rows, targets, result, manager, events, claims


@pytest.mark.parametrize("route", ["nxt_only", "krx_nxt_integrated"])
def test_native_main_handoff_commits_without_subscription_gap(monkeypatch, route):
    import asyncio
    rows, targets, result, manager, events, claims = _native_main_handoff(monkeypatch, route)
    assert main.handle_zero_base_machine_enter(result)
    assert rows[1].status == "WATCHING"
    assert targets[0]["_continuous_reversal_pending_claim"] == {"token": "native-once"}
    assert targets[0]["_entry_native_deadline_binding"]["deadline_perf"] == result["native_observation"]["deadline_perf"]
    assert "zero_base_pending_db" not in targets[0]
    assert len(claims) == 1
    assert not any(topic == "COMMAND_WS_REG" for topic, _ in events)
    receipt = next(f for topic, f in reversed(events) if topic == "receipt")
    detail = json.loads(receipt["zero_base_finalize_receipt"])
    assert receipt["zero_base_attach_outcome"] == "attached"
    assert detail["reason"] == "watching_finalized" and detail["record_id"] == 1
    assert detail["physical_probe_lease_id"] == "lease-native"
    assert detail["native_signal_id"] == "original-signal"
    assert detail["native_event_id"] == "original-event"
    item = result["native_observation"]["snapshot"][0]["source_item"]
    assert asyncio.run(manager._release_exact_probe_item(item, "lease-native"))
    assert manager._registered_item_epochs[item] == 88


def test_native_handoff_failed_claim_expires_exact_row_and_preserves_reason(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as D
    rows, targets, _result_value, _manager, events, _claims = _native_main_handoff(monkeypatch)
    monkeypatch.setattr(D, "claim_expected_snapshot", lambda _p: None)
    assert not main.handle_zero_base_machine_enter(_result_value)
    assert rows[1].status == "EXPIRED" and targets == []
    receipt = next(f for topic, f in reversed(events) if topic == "receipt")
    detail = json.loads(receipt["zero_base_finalize_receipt"])
    assert detail["reason"] == "expected_native_claim_unavailable"
    assert not detail["finalized"]
    assert detail["rollback_receipt"]["reason"] == "probe_expired"
    assert detail["rollback_receipt"]["finalized"]
    assert receipt["zero_base_attach_outcome"] == "rejected"


def test_native_handoff_adoption_failure_expires_without_attaching(monkeypatch):
    rows, targets, result, manager, events, claims = _native_main_handoff(monkeypatch)
    monkeypatch.setattr(manager, "adopt_zero_base_probe_target", lambda _p: False)
    assert not main.handle_zero_base_machine_enter(result)
    assert rows[1].status == "EXPIRED" and not targets and not claims
    assert not any(topic == "COMMAND_WS_REG" for topic, _ in events)
    receipt = next(f for topic, f in reversed(events) if topic == "receipt")
    detail = json.loads(receipt["zero_base_finalize_receipt"])
    assert detail["reason"] == "probe_expired"
    assert detail["admission_failure_reason"] == "native_subscription_adoption_failed"
    assert receipt["zero_base_attach_reason"] == "native_subscription_adoption_failed"


def test_blocking_finalization_emits_original_inner_receipt(monkeypatch):
    receipt_fn = main._zero_base_attach_receipt
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "_zero_base_attach_receipt", receipt_fn)
    events = []
    monkeypatch.setattr(main, "emit_pipeline_event", lambda *_a, **kw: events.append(kw["fields"]))
    def attach(payload, **_kw):
        targets.append(dict(id=payload["record_id"], code=payload["code"], status="WATCHING"))
        return True
    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", attach)
    assert main.handle_zero_base_machine_enter(_result())
    detail = json.loads(events[-1]["zero_base_finalize_receipt"])
    assert detail["reason"] == "watching_finalized"
    assert detail["record_id"] == rows[1].id


def test_native_handoff_db_failure_preserves_original_error_and_exact_cleanup(monkeypatch):
    from src.engine.scalping import reversal_current_backend as B
    rows, targets, result, _manager, events, claims = _native_main_handoff(monkeypatch)
    sessions = []
    class FailedFinalize(_Session):
        def __exit__(self, *_args):
            if len(sessions) == 2:
                rows[1].status = "PROBE_READY"  # SQL rollback preserves the original row.
                raise OSError("commit failed")
            return False
    def session():
        sessions.append(1)
        return FailedFinalize(rows)
    monkeypatch.setattr(main, "DB", SimpleNamespace(get_session=session))
    closed = []
    monkeypatch.setattr(B, "acknowledge_any", lambda claim, **kw: closed.append((claim, kw)))
    assert not main.handle_zero_base_machine_enter(result)
    assert rows[1].status == "EXPIRED" and targets == []
    assert len(claims) == 1
    assert closed == [({"token": "native-once"}, {"status": "main_attach_commit_failed"})]
    receipt = next(f for topic, f in reversed(events) if topic == "receipt")
    detail = json.loads(receipt["zero_base_finalize_receipt"])
    assert detail["reason"] == "db_finalize_exception" and detail["exception_type"] == "OSError"
    assert detail["rollback_receipt"]["reason"] == "probe_expired"
    assert detail["physical_probe_lease_id"] == "lease-native"


def test_provisional_rollback_is_idempotent_and_retains_first_failure(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    rows[1] = _Record(stock_code="123456", status="PROBE_READY", scanner_source_signature="ZERO_BASE_DISCOVERY:a")
    targets.append(dict(id=1, code="123456", status="WATCHING", zero_base_pending_db=True))
    events = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(publish=lambda *args: events.append(args)))
    payload = dict(record_id=1, code="123456", zero_base_pending_db=True,
                   _zero_base_ws_adopted=True, market_data_route="krx_nxt_integrated",
                   _zero_base_finalize_receipt=dict(finalized=False, attached=True, reason="expected_native_claim_unavailable"))
    main._zero_base_rollback_uncommitted_target(payload)
    first = json.dumps(payload["_zero_base_finalize_receipt"], sort_keys=True)
    main._zero_base_rollback_uncommitted_target(payload)
    assert rows[1].status == "EXPIRED" and targets == [] and len(events) == 1
    assert json.dumps(payload["_zero_base_finalize_receipt"], sort_keys=True) == first


@pytest.mark.parametrize("status,pending", [("HOLDING", False), ("WATCHING", False)])
def test_provisional_rollback_keeps_committed_or_holding_target(monkeypatch, status, pending):
    rows, targets = _prepare(monkeypatch)
    rows[1] = _Record(stock_code="123456", status=status, scanner_source_signature="ZERO_BASE_DISCOVERY:a")
    target = dict(id=1, code="123456", status=status, zero_base_pending_db=pending)
    targets.append(target)
    events = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(publish=lambda *args: events.append(args)))
    main._zero_base_rollback_uncommitted_target(dict(record_id=1, code="123456", zero_base_pending_db=True))
    assert targets == [target] and rows[1].status == status and events == []


@pytest.mark.parametrize("claim_valid", [True, False])
def test_native_scheduler_inbox_handoff_keeps_lease_and_original_receipt(monkeypatch, claim_valid):
    from src.engine.scalping import reversal_source_diagnostics as D
    rows, targets, result, manager, events, claims = _native_main_handoff(monkeypatch)
    payload = dict(
        code="123456", name="TEST", record_id=1, strategy="SCALPING", status="WATCHING",
        position_tag="SCANNER", buy_price=10000, added_time=time.time(),
        source_signature="ZERO_BASE_DISCOVERY:" + "b" * 64,
        scanner_promotion_id="ZBPROM-123456-inbox", scanner_promotion_emitted_epoch=time.time(),
        market_data_route="krx_nxt_integrated", effective_venue="KRX", broker_route="SOR",
        native_observation=result["native_observation"], ws_handoff_id="lease-native",
        physical_probe_lease_id="lease-native", zero_base_pending_db=True)
    rows[1] = _Record(stock_code="123456", status="PROBE_READY", scanner_source_signature=payload["source_signature"])
    queue = [SimpleNamespace(payload=payload, enqueued_epoch=time.time())]
    def pop():
        if queue:
            return queue.pop(0)
        raise Empty
    monkeypatch.setattr(main, "_SCANNER_PROMOTION_INBOX", SimpleNamespace(get_nowait=pop))
    monkeypatch.setattr(main, "_scanner_scheduler_coalesce_duplicate_inbox", lambda *_a, **_kw: None)
    monkeypatch.setattr(main, "_scanner_scheduler_reconcile_active_targets", lambda *_a, **_kw: None)
    monkeypatch.setattr(main, "_register_scanner_scheduler_generation", lambda *_a, **_kw: None)
    monkeypatch.setattr(main, "_emit_scanner_scheduler_event", lambda *_a, **_kw: None)
    if not claim_valid:
        monkeypatch.setattr(D, "claim_expected_snapshot", lambda _p: None)
    summary = main._drain_scanner_promotion_inbox(SimpleNamespace(), max_items=1)
    assert summary["applied"] == int(claim_valid)
    assert rows[1].status == ("WATCHING" if claim_valid else "EXPIRED")
    assert bool(targets) == claim_valid
    assert len(claims) == int(claim_valid)
    assert not any(topic == "COMMAND_WS_REG" for topic, _ in events)
    receipt = next(f for topic, f in reversed(events) if topic == "receipt")
    detail = json.loads(receipt["zero_base_finalize_receipt"])
    assert detail["reason"] == ("watching_finalized" if claim_valid else "expected_native_claim_unavailable")
    assert detail["physical_probe_lease_id"] == "lease-native"
    assert manager._registered_item_epochs["123456_AL"] == 88


@pytest.mark.parametrize("fault", ["expired", "wrong_epoch", "conflict", "manual", "capacity"])
def test_native_main_handoff_preserves_original_rejection_guards(monkeypatch, fault):
    rows, targets, result, manager, events, claims = _native_main_handoff(monkeypatch)
    if fault == "expired":
        result["native_observation"]["deadline_perf"] = time.perf_counter() - 1
    elif fault == "wrong_epoch":
        manager._market_data_transport_epoch += 1
    elif fault == "conflict":
        monkeypatch.setattr(main, "_zero_base_active_conflict", lambda _code: True)
    elif fault == "manual":
        monkeypatch.setattr(main, "evaluate_main_bot_control_exclusion", lambda _code: SimpleNamespace(excluded=True))
    elif fault == "capacity":
        monkeypatch.setattr(main, "_scalping_attach_capacity_decision", lambda *_a, **_kw: (False, [], {}))
    assert not main.handle_zero_base_machine_enter(result)
    assert rows == {} and targets == [] and claims == []
    assert not manager._exact_probe_item_leases["123456_AL"].get("adopted")
    assert not any(topic == "COMMAND_WS_REG" for topic, _ in events)


def test_invalid_db_admission_does_not_consume_native_claim(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    targets.append(dict(id=7, code='123456', status='WATCHING'))
    from src.engine.scalping import reversal_source_diagnostics as D
    monkeypatch.setattr(main, '_zero_base_native_handoff_valid', lambda p: True)
    claims = []
    monkeypatch.setattr(D, 'claim_expected_snapshot', lambda p: claims.append(p))
    payload = dict(record_id=7, code='123456', native_observation={'deadline_perf':time.perf_counter()+5})
    assert not main._zero_base_finalize_candidate_record(payload, attached=True)
    assert claims == []
    assert payload['_zero_base_finalize_receipt']['reason']=='durable_probe_admission_mismatch'
    assert payload['_zero_base_finalize_receipt']['pid']==__import__('os').getpid()
    assert payload['_zero_base_finalize_receipt']['process_start_ticks']
    rows[7] = _Record(stock_code='123456',status='PROBE_READY',scanner_source_signature='ZERO_BASE_DISCOVERY:a')
    monkeypatch.setattr(D, 'claim_expected_snapshot', lambda p: {'token':'native'})
    assert main._zero_base_finalize_candidate_record(payload, attached=True)
    assert targets[0]['_continuous_reversal_pending_claim']['token'] == 'native'
    assert payload['_zero_base_finalize_receipt']['reason']=='watching_finalized'


def test_db_commit_failure_closes_consumed_claim(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as D, reversal_current_backend as B
    rows, targets = _prepare(monkeypatch)
    targets.append(dict(id=7, code='123456', status='WATCHING'))
    rows[7] = _Record(stock_code='123456',status='PROBE_READY',scanner_source_signature='ZERO_BASE_DISCOVERY:a')
    class FailedCommit(_Session):
        def __exit__(self, *_):
            raise OSError('commit failed')
    monkeypatch.setattr(main, 'DB', SimpleNamespace(get_session=lambda: FailedCommit(rows)))
    monkeypatch.setattr(main, '_zero_base_native_handoff_valid', lambda p: True)
    monkeypatch.setattr(D, 'claim_expected_snapshot', lambda p: {'token':'native'})
    closed=[]
    monkeypatch.setattr(B, 'acknowledge_any', lambda claim, **kwargs: closed.append((claim,kwargs)))
    assert not main._zero_base_finalize_candidate_record(dict(record_id=7,code='123456',
        native_observation={'deadline_perf':time.perf_counter()+5}), attached=True)
    assert closed == [({'token':'native'}, {'status':'main_attach_commit_failed'})]
    assert '_continuous_reversal_pending_claim' not in targets[0]


def test_finalize_diagnostic_failure_does_not_change_committed_admission(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as D
    from src.engine.monitoring import runtime_performance as R
    rows,targets=_prepare(monkeypatch)
    targets.append(dict(id=7,code='123456',status='WATCHING',zero_base_pending_db=True))
    rows[7]=_Record(stock_code='123456',status='PROBE_READY',scanner_source_signature='ZERO_BASE_DISCOVERY:a')
    monkeypatch.setattr(main,'_zero_base_native_handoff_valid',lambda p:True)
    monkeypatch.setattr(D,'claim_expected_snapshot',lambda p:{'token':'native'})
    monkeypatch.setattr(R,'process_identity_fields',lambda:(_ for _ in ()).throw(OSError('diagnostic only')))
    payload=dict(record_id=7,code='123456',native_observation={'deadline_perf':time.perf_counter()+5})
    assert main._zero_base_finalize_candidate_record(payload,attached=True)
    assert rows[7].status=='WATCHING' and targets[0]['_continuous_reversal_pending_claim']['token']=='native'
    assert '_zero_base_finalize_receipt' not in payload


def test_integrated_aftermarket_attaches_integrated_cohort_and_sor(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "KRX_NXT_AFTERMARKET",
        "market_session_regime": "KRX_NXT_AFTERMARKET",
    })
    def attach(payload, **_kwargs):
        targets.append({"id": payload["record_id"], "code": payload["code"], "status": "WATCHING"})
        assert payload["effective_venue"] == "KRX_NXT_INTEGRATED"
        assert payload["broker_route"] == "SOR"
        return True
    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", attach)
    assert main.handle_zero_base_machine_enter(_result()) is True
    assert rows[1].effective_venue == "KRX_NXT_INTEGRATED"


def test_separate_nxt_candidate_is_rejected(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    result = _result()
    result["claim"]["route"] = "nxt_only"
    result["candidate"]["route"] = "nxt_only"
    assert main.handle_zero_base_machine_enter(result) is False
    assert rows == {} and targets == []


def test_premarket_nxt_candidate_attaches_exact_route(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "krx_like_premarket",
        "market_session_regime": "krx_like_premarket",
    })
    result = _result()
    result["claim"]["route"] = "nxt_only"
    result["candidate"]["route"] = "nxt_only"

    def attach(payload, **_kwargs):
        assert payload["effective_venue"] == "PREMARKET_KRX_LIKE"
        assert payload["market_data_route"] == "nxt_only"
        assert payload["broker_route"] == "NXT"
        targets.append({"id": payload["record_id"], "code": payload["code"],
                        "status": "WATCHING"})
        return True

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", attach)
    assert main.handle_zero_base_machine_enter(result) is True
    assert rows[1].effective_venue == "PREMARKET_KRX_LIKE"


def test_integrated_candidate_is_rejected_in_premarket(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "krx_like_premarket",
        "market_session_regime": "krx_like_premarket",
    })
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert rows == {} and targets == []


def test_attached_integrated_watching_registers_al_item(monkeypatch):
    _rows, targets = _prepare(monkeypatch)
    published = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda name, payload: published.append((name, payload)),
    ))
    monkeypatch.setattr(main, "_resolve_stock_marcap", lambda *_args: 0)
    monkeypatch.setattr(main, "_resolve_scanner_runtime_record_id", lambda *_args: 1)
    monkeypatch.setattr(main, "_scanner_identity_guard", lambda *_args: (True, {}))
    monkeypatch.setattr(main, "_log_scanner_runtime_target_attach", lambda *_args, **_kwargs: None)
    now = time.time()
    attached = main._apply_scalping_scanner_promoted_target({
        "record_id": 1, "code": "123456", "name": "TEST",
        "strategy": "SCALPING", "position_tag": "SCANNER",
        "buy_price": 10000, "added_time": now,
        "scanner_promotion_id": "ZBPROM-123456-1-1",
        "scanner_promotion_emitted_epoch": now,
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "venue": "KRX", "effective_venue": "KRX",
        "market_data_route": "krx_nxt_integrated",
        "broker_route": "SOR", "market_session_bucket": "krx_regular",
    })
    assert attached is True
    assert targets[0]["market_data_route"] == "krx_nxt_integrated"
    assert targets[0]["broker_route"] == "SOR"
    assert published == [("COMMAND_WS_REG", {
        "codes": ["123456_AL"], "source": "scanner_runtime_target_attach",
    })]


def test_attached_premarket_watching_registers_nx_item(monkeypatch):
    _rows, targets = _prepare(monkeypatch)
    published = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda name, payload: published.append((name, payload)),
    ))
    monkeypatch.setattr(main, "_resolve_stock_marcap", lambda *_args: 0)
    monkeypatch.setattr(main, "_resolve_scanner_runtime_record_id", lambda *_args: 1)
    monkeypatch.setattr(main, "_scanner_identity_guard", lambda *_args: (True, {}))
    monkeypatch.setattr(main, "_log_scanner_runtime_target_attach", lambda *_args, **_kwargs: None)
    now = time.time()
    assert main._apply_scalping_scanner_promoted_target({
        "record_id": 1, "code": "123456", "name": "TEST",
        "strategy": "SCALPING", "position_tag": "SCANNER",
        "buy_price": 10000, "added_time": now,
        "scanner_promotion_id": "ZBPROM-123456-1-1",
        "scanner_promotion_emitted_epoch": now,
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "venue": "PREMARKET_KRX_LIKE", "effective_venue": "PREMARKET_KRX_LIKE",
        "market_data_route": "nxt_only",
        "broker_route": "NXT", "market_session_bucket": "krx_like_premarket",
    })
    assert targets[0]["broker_route"] == "NXT"
    assert published == [("COMMAND_WS_REG", {
        "codes": ["123456_NX"], "source": "scanner_runtime_target_attach",
    })]


@pytest.mark.parametrize(
    ("followup_result", "expected_action", "release_raises"),
    [("assessed", "ENTER_NOW", False),
     ("source_unavailable", "RECHECK", False),
     ("assessed", "ENTER_NOW", True)],
)
def test_recheck_reuses_probe_lease_then_publishes_only_final_assessment(
    monkeypatch, followup_result, expected_action, release_raises,
):
    published = []
    calls = []
    released = []
    futures = []
    errors = []
    request = {
        "claim": {"code": "123456", "route": "krx_nxt_integrated",
                  "source_sha256": "b" * 64},
        "candidate": {"code": "123456", "route": "krx_nxt_integrated",
                      "source_sha256": "b" * 64},
    }
    monkeypatch.setattr(main, "_zero_base_runtime_enabled", lambda: True)
    monkeypatch.setattr(main, "_zero_base_active_conflict", lambda _code: False)
    monkeypatch.setattr(main, "evaluate_main_bot_control_exclusion",
                        lambda _code: SimpleNamespace(excluded=False))
    monkeypatch.setattr(main, "scalping_session_venue_provenance",
                        lambda _epoch: {"market_session_regime": "KRX_REGULAR"})
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_SLOTS", slots)
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_IN_FLIGHT", set())
    def submit(worker):
        future = Future()
        futures.append(future)
        try:
            future.set_result(worker())
        except Exception as exc:
            future.set_exception(exc)
        return future

    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_EXECUTOR",
                        SimpleNamespace(submit=submit))
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda event, payload: published.append((event, payload)),
    ))
    def release(code, item):
        released.append((code, item))
        if release_raises:
            raise RuntimeError("release_failed")

    monkeypatch.setattr(main, "_zero_base_release_probe_ws", release)
    monkeypatch.setattr(main, "log_error", errors.append)

    def probe_once(_request, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {**request, "result": "assessed", "machine_action": "RECHECK",
                    "reason": "trigger_pending", "ws_observation": {"wait_ms": 3000},
                    "_ws_lease_retained": True}
        return {**request, "result": followup_result,
                "machine_action": "ENTER_NOW" if followup_result == "assessed" else "",
                "reason": "trigger_confirmed" if followup_result == "assessed"
                          else "route_snapshot_missing",
                "ws_observation": {"wait_ms": 6000,
                                   "exact_0b_count": 0 if followup_result != "assessed" else 5}}

    monkeypatch.setattr(main, "run_zero_base_probe", probe_once)
    main.handle_zero_base_probe_requested(dict(request, consumer_readiness={'ready': True, 'runtime_generation': 'fixture'}))
    assert futures[0].exception() is None
    assert bool(errors) is release_raises
    assert len(calls) == 2
    assert [call["ws_min_warmup_sec"] for call in calls] == [10.0, 2.0]
    assert [call["ws_wait_timeout_sec"] for call in calls] == [15.0, 6.0]
    assert [call["ws_wait_empty_timeout_sec"] for call in calls] == [10.0, 5.0]
    assert released == [("123456", "123456_AL")]
    assert len(published) == (1 if release_raises else 2)
    if not release_raises:
        assert published[1][0] == 'ZERO_BASE_HANDOFF_CLOSED'
    assert published[0][1]["machine_action"] == expected_action
    assert published[0][1]["recheck_attempts"] == 2
    assert published[0][1]["recheck_followup_result"] == followup_result
    assert published[0][1]["recheck_followup_ws_observation"]["wait_ms"] == 6000
    assert slots.acquire(blocking=False) is not release_raises
    if not release_raises:
        slots.release()


@pytest.mark.parametrize("regime", [
    session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET,
    session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
])
def test_quiet_sessions_have_longer_bounded_probe_observation(regime):
    profile = main._zero_base_probe_observation_profile(regime)
    assert profile["first_warmup_sec"] == 15.0
    assert profile["first_timeout_sec"] == 20.0
    assert profile["first_empty_timeout_sec"] == 15.0
    assert profile["recheck_warmup_sec"] == 3.0
    assert profile["recheck_timeout_sec"] == 10.0
    assert profile["recheck_empty_timeout_sec"] == 8.0
    assert profile["partial_extension_sec"] == 2.0


def test_regular_session_has_ten_second_first_probe_floor():
    profile = main._zero_base_probe_observation_profile(
        session_contract.MARKET_SESSION_REGIME_KRX_REGULAR,
    )
    assert profile["first_warmup_sec"] == 10.0
    assert profile["first_empty_timeout_sec"] == 10.0
    assert profile["first_timeout_sec"] == 15.0


@pytest.mark.parametrize("regime,route", [
    (session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET, "nxt_only"),
    (session_contract.MARKET_SESSION_REGIME_KRX_REGULAR, "krx_nxt_integrated"),
    (session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET, "krx_nxt_integrated"),
])
def test_probe_worker_hard_cap_is_five_in_every_buy_session(
    monkeypatch, regime, route,
):
    tasks = []
    events = []
    slots = threading.BoundedSemaphore(5)
    monkeypatch.setattr(main, "_zero_base_runtime_enabled", lambda: True)
    monkeypatch.setattr(main, "_zero_base_active_conflict", lambda _code: False)
    monkeypatch.setattr(main, "evaluate_main_bot_control_exclusion",
                        lambda _code: SimpleNamespace(excluded=False))
    monkeypatch.setattr(main, "scalping_session_venue_provenance",
                        lambda _epoch: {"market_session_regime": regime})
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_SLOTS", slots)
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_IN_FLIGHT", set())
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_EXECUTOR",
                        SimpleNamespace(submit=tasks.append))
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda event, payload: events.append((event, payload)),
    ))
    for number in range(6):
        code = f"{number + 1:06d}"
        claim = {"code": code, "route": route, "source_sha256": "b" * 64}
        main.handle_zero_base_probe_requested({
            "claim": claim, "candidate": dict(claim),
            "consumer_readiness": {"ready": True, "runtime_generation": "fixture"},
        })
    assert len(tasks) == 5
    assert len(main._ZERO_BASE_PROBE_IN_FLIGHT) == 5
    assert events[-1][1]["reason"] == "probe_worker_capacity"
    assert not slots.acquire(blocking=False)


def test_zero_base_entry_request_binds_sor_and_fails_closed_on_lost_route(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    class _Clock:
        @staticmethod
        def now(_zone):
            return datetime(2026, 9, 28, 16, 10, tzinfo=ZoneInfo("Asia/Seoul"))

    monkeypatch.setattr(handlers, "datetime", _Clock)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _time: True)
    stock = {
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "market_data_route": "krx_nxt_integrated",
        "broker_route": "SOR", "effective_venue": "KRX_NXT_INTEGRATED",
        "market_session_bucket": "KRX_NXT_AFTERMARKET",
    }
    request = {"qty": 1, "price": 10000, "order_type_code": "00"}
    assert handlers._bind_main_entry_order_request(stock, request)
    assert request["dmst_stex_tp"] == "SOR"
    assert kiwoom_orders.describe_buy_order_resolution(
        "00", price=10000, dmst_stex_tp=request["dmst_stex_tp"],
    )["effective_dmst_stex_tp"] == "SOR"
    for field, value in (("broker_route", "NXT"),
                         ("market_data_route", "nxt_only"),
                         ("effective_venue", "NXT"),
                         ("market_session_bucket", "krx_regular")):
        assert not handlers._bind_main_entry_order_request(
            {**stock, field: value}, {},
        )


def test_zero_base_sor_order_rejects_stale_session_cohort(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    clock = {"hour": 9, "minute": 10}

    class _Clock:
        @staticmethod
        def now(_zone):
            return datetime(2026, 9, 28, clock["hour"], clock["minute"],
                            tzinfo=ZoneInfo("Asia/Seoul"))

    monkeypatch.setattr(handlers, "datetime", _Clock)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _time: True)
    stock = {
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "market_data_route": "krx_nxt_integrated", "broker_route": "SOR",
        "effective_venue": "KRX", "market_session_bucket": "krx_regular",
    }
    assert handlers._bind_main_entry_order_request(stock, {})
    clock.update(hour=16, minute=10)
    assert not handlers._bind_main_entry_order_request(stock, {})
    stock.update(effective_venue="KRX_NXT_INTEGRATED",
                 market_session_bucket="KRX_NXT_AFTERMARKET")
    assert handlers._bind_main_entry_order_request(stock, {})
    clock.update(hour=19, minute=42)
    assert not handlers._bind_main_entry_order_request(stock, {})


def test_zero_base_watch_expires_on_session_transition():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    def epoch(hour, minute):
        return datetime(2026, 9, 28, hour, minute,
                        tzinfo=ZoneInfo("Asia/Seoul")).timestamp()

    premarket = {"effective_venue": "PREMARKET_KRX_LIKE",
                 "market_session_bucket": "krx_like_premarket"}
    regular = {"effective_venue": "KRX",
               "market_session_bucket": "krx_regular"}
    after = {"effective_venue": "KRX_NXT_INTEGRATED",
             "market_session_bucket": "KRX_NXT_AFTERMARKET"}
    assert main._zero_base_watch_session_matches(premarket, epoch(8, 40))
    assert not main._zero_base_watch_session_matches(premarket, epoch(9, 0))
    assert main._zero_base_watch_session_matches(regular, epoch(9, 10))
    assert not main._zero_base_watch_session_matches(regular, epoch(16, 0))
    assert main._zero_base_watch_session_matches(after, epoch(16, 10))
    assert not main._zero_base_watch_session_matches(after, epoch(19, 40))
    assert not main._zero_base_watch_session_matches({}, epoch(16, 10))


def test_zero_base_premarket_entry_binds_nxt_only_during_buy_window(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    class _Clock:
        @staticmethod
        def now(_zone):
            return datetime(2026, 9, 28, 8, 10, tzinfo=ZoneInfo("Asia/Seoul"))

    monkeypatch.setattr(handlers, "datetime", _Clock)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _time: True)
    stock = {
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "market_data_route": "nxt_only", "broker_route": "NXT",
        "effective_venue": "PREMARKET_KRX_LIKE",
        "market_session_bucket": "krx_like_premarket",
    }
    request = {"qty": 1, "price": 10000, "order_type_code": "00"}
    assert handlers._bind_main_entry_order_request(stock, request)
    assert request["dmst_stex_tp"] == "NXT"
    for field, value in (("broker_route", "SOR"),
                         ("market_data_route", "krx_nxt_integrated"),
                         ("effective_venue", "NXT")):
        assert not handlers._bind_main_entry_order_request({**stock, field: value}, {})


def test_enter_now_failure_expires_provisional_row(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", lambda _payload, **_kwargs: False)
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert rows[1].status == "EXPIRED"
    assert targets == []


def test_enter_now_attach_exception_expires_provisional_row(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    events = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda topic, payload: events.append((topic, payload)),
    ))

    def failed_attach(payload, **_kwargs):
        targets.append({
            "id": payload["record_id"], "code": payload["code"],
            "status": "WATCHING", "zero_base_pending_db": True,
        })
        raise RuntimeError("partial_attach")

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", failed_attach)
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert rows[1].status == "EXPIRED"
    assert targets == []
    assert events[-1][0] == "COMMAND_WS_UNREG"


def test_inbox_attach_exception_expires_provisional_row_and_continues(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    payload = {
        "code": "123456", "strategy": "SCALPING", "record_id": 1,
        "zero_base_pending_db": True,
    }
    rows[1] = _Record(
        stock_code="123456", status="PROBE_READY",
        scanner_source_signature="ZERO_BASE_DISCOVERY:" + "b" * 64,
    )
    inbox_items = [SimpleNamespace(payload=payload, enqueued_epoch=time.time())]

    def get_nowait():
        if inbox_items:
            return inbox_items.pop(0)
        raise Empty

    monkeypatch.setattr(main, "_SCANNER_PROMOTION_INBOX", SimpleNamespace(get_nowait=get_nowait))
    monkeypatch.setattr(main, "_scanner_scheduler_coalesce_duplicate_inbox", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(publish=lambda *_args: None))

    def failed_attach(attached_payload, **_kwargs):
        targets.append({
            "id": attached_payload["record_id"], "code": attached_payload["code"],
            "status": "WATCHING", "zero_base_pending_db": True,
        })
        raise RuntimeError("partial_attach")

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", failed_attach)
    summary = main._drain_scanner_promotion_inbox(SimpleNamespace(), max_items=1)
    assert summary["drained"] == 1
    assert summary["applied"] == 0
    assert rows[1].status == "EXPIRED"
    assert targets == []


def test_enter_now_rejects_source_or_bundle_gap_before_db(monkeypatch):
    rows, _targets = _prepare(monkeypatch)
    result = _result()
    result["machine_bundle_sha256"] = "invalid"
    assert main.handle_zero_base_machine_enter(result) is False
    result = _result()
    result["candidate"]["source_sha256"] = "c" * 64
    assert main.handle_zero_base_machine_enter(result) is False
    result = _result()
    result["probe_depth_epoch"] -= 10
    assert main.handle_zero_base_machine_enter(result) is False
    assert rows == {}


def test_zero_base_uses_global_watch_cap_without_owner_quota_or_eviction(monkeypatch):
    monkeypatch.setattr(main, "_scalping_fifo_max_active", lambda: 2)
    incoming = {
        "code": "123456", "strategy": "SCALPING", "status": "WATCHING",
        "position_tag": "SCANNER", "source_signature": "ZERO_BASE_DISCOVERY:" + "a" * 64,
    }
    assert main._is_zero_base_watch_target(incoming)
    one = [{**incoming, "code": "000001"}]
    allowed, replacements, fields = main._scalping_attach_capacity_decision(
        incoming, time.time(), watching_targets=one,
    )
    assert allowed is True and replacements == []
    assert fields["scanner_watch_budget_policy"] == "zero_base_global_watch_cap_v1"
    full = [*one, {**incoming, "code": "000002"}]
    allowed, replacements, _fields = main._scalping_attach_capacity_decision(
        incoming, time.time(), watching_targets=full,
    )
    assert allowed is False and replacements == []


@pytest.mark.parametrize("remove_sent,shutdown", [(True,False),(False,False),(True,True)])
def test_late_registration_keeps_same_code_probe_reserved_until_cleanup(
    monkeypatch, remove_sent, shutdown,
):
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
    monkeypatch.setattr(main, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_regime": main.session_contract.MARKET_SESSION_REGIME_KRX_REGULAR,
    })
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_IN_FLIGHT", set())
    slots = threading.BoundedSemaphore(2)
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_SLOTS", slots)
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_EXECUTOR", SimpleNamespace(
        submit=lambda fn: fn(),
    ))
    errors = []
    monkeypatch.setattr(main, "log_error", errors.append)
    monkeypatch.setattr(main, "evaluate_main_bot_control_exclusion", lambda _code: SimpleNamespace(excluded=False))
    events = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda topic, payload: events.append((topic, payload)),
    ))
    callbacks = []

    def probe(request, **kwargs):
        callbacks.append(kwargs["release_ws"])
        return {**request, "result": "source_unavailable", "reason": "ws_registration_timeout",
                "_ws_cleanup_deferred": True}

    monkeypatch.setattr(main, "run_zero_base_probe", probe)
    remove_completion = Future()
    monkeypatch.setattr(
        main, "_zero_base_release_probe_ws", lambda *_args: remove_completion,
    )
    request = {"claim": _result()["claim"], "candidate": _result()["candidate"]}
    main.handle_zero_base_probe_requested(dict(request, consumer_readiness={'ready': True, 'runtime_generation': 'fixture'}))
    assert "123456" in main._ZERO_BASE_PROBE_IN_FLIGHT
    assert slots.acquire(blocking=False)
    assert not slots.acquire(blocking=False)
    slots.release()
    main.handle_zero_base_probe_requested(dict(request, consumer_readiness={'ready': True, 'runtime_generation': 'fixture'}))
    assert events[-1][1]["reason"] == "same_code_probe_in_flight"
    callbacks[0]("123456", "123456")
    assert "123456" in main._ZERO_BASE_PROBE_IN_FLIGHT
    assert slots.acquire(blocking=False)
    assert not slots.acquire(blocking=False)
    slots.release()
    if shutdown:
        monkeypatch.setattr(main.time,'sleep',lambda _:remove_completion.set_result(True))
        assert main._drain_zero_base_probe_leases(timeout=.2)
    else:
        remove_completion.set_result(remove_sent)
    assert ("123456" not in main._ZERO_BASE_PROBE_IN_FLIGHT) is remove_sent
    assert bool(errors) is not remove_sent
    if not remove_sent:
        monkeypatch.setattr(main, '_zero_base_release_probe_ws', lambda *_args: True)
        monkeypatch.setattr(main.time, 'monotonic', lambda: float('inf'))
        main._retry_zero_base_cleanup()
        assert "123456" not in main._ZERO_BASE_PROBE_IN_FLIGHT
    assert slots.acquire(blocking=False)
    assert slots.acquire(blocking=False)
    assert not slots.acquire(blocking=False)
    slots.release()
    slots.release()


def test_read_only_main_target_snapshot_changes_with_release_and_identity(monkeypatch):
    targets = [{'code': '123456', 'id': 1, 'status': 'WATCHING', 'source_signature': 'one'},
               {'code': '654321', 'id': 2, 'status': 'COMPLETED'}]
    monkeypatch.setattr(main, 'ACTIVE_TARGETS', targets)
    owner = dict(runtime_generation='g1', process_pid=1, process_start_ticks='2', date='2026-10-14')
    first = main._zero_base_active_target_snapshot(owner)
    assert first['active_codes'] == ['123456']
    targets[0]['source_signature'] = 'two'
    replaced = main._zero_base_active_target_snapshot(owner)
    assert replaced['generation'] != first['generation']
    targets[0]['status'] = 'EXPIRED'
    released = main._zero_base_active_target_snapshot(owner)
    assert released['active_codes'] == [] and released['generation'] != replaced['generation']
    targets[:] = [None, ['invalid']]
    assert main._zero_base_active_target_snapshot(owner)['status'] == 'unobserved'


def test_probe_rechecks_active_target_after_executor_queue_without_registering(monkeypatch):
    monkeypatch.setattr(main, '_zero_base_runtime_enabled', lambda: True)
    monkeypatch.setattr(main, 'ACTIVE_TARGETS', [])
    monkeypatch.setattr(main, 'evaluate_main_bot_control_exclusion', lambda code: SimpleNamespace(excluded=False))
    monkeypatch.setattr(main, 'scalping_session_venue_provenance', lambda stamp: {'market_session_regime': 'KRX_REGULAR'})
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_SLOTS', slots)
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_IN_FLIGHT', set())
    work = []
    monkeypatch.setattr(main, '_ZERO_BASE_PROBE_EXECUTOR', SimpleNamespace(submit=lambda fn: work.append(fn)))
    events = []
    monkeypatch.setattr(main, 'event_bus', SimpleNamespace(publish=lambda event, payload: events.append((event, payload))))
    monkeypatch.setattr(main, 'run_zero_base_probe', lambda *a, **k: pytest.fail('existing target reached physical probe'))
    req = dict(claim={'code': '123456', 'route': 'krx_nxt_integrated', 'source_sha256': 'b'*64},
               candidate={'code': '123456', 'route': 'krx_nxt_integrated', 'source_sha256': 'b'*64},
               consumer_readiness={'ready': True, 'runtime_generation': 'fixture'})
    main.handle_zero_base_probe_requested(req)
    main.ACTIVE_TARGETS.append({'code': '123456', 'id': 1, 'status': 'WATCHING'})
    work[0]()
    result = next(payload for event, payload in events if event == main.PROBE_RESULT_EVENT)
    assert result['result'] == 'active_conflict' and result['reason'] == 'existing_runtime_target_at_worker'
    assert not main._ZERO_BASE_PROBE_IN_FLIGHT
    assert slots.acquire(blocking=False)
    assert sum(event == 'ZERO_BASE_HANDOFF_CLOSED' for event, _ in events) == 1


def test_main_target_snapshot_keeps_observation_time_before_hashing(monkeypatch):
    monkeypatch.setattr(main, 'ACTIVE_TARGETS', [{'code':'123456','id':1,'status':'WATCHING'}])
    epoch=[100.0]
    monkeypatch.setattr(main.time,'time',lambda:epoch[0])
    actual=main.hashlib.sha256
    def delayed_hash(value):
        epoch[0]+=3
        return actual(value)
    monkeypatch.setattr(main.hashlib,'sha256',delayed_hash)
    result=main._zero_base_active_target_snapshot(dict(runtime_generation='g',
        process_pid=1,process_start_ticks='2',date='2026-10-14'))
    assert result['observed_epoch']==100 and epoch[0]==103


def test_native_main_handoff_retains_exact_source_to_precheck_and_original_claim(monkeypatch):
    import asyncio
    from src.engine.scalping.continuous_reversal_postclose import digest
    rows, targets, result, manager, events, claims = _native_main_handoff(monkeypatch)
    expected = result['native_observation']
    item = expected['snapshot'][0]['source_item']
    manager._exact_probe_item_leases[item]['interval_started_epoch'] = time.time() - 0.01
    async def feed():
        for _ in range(4):
            await manager._handle_message(json.dumps({'trnm':'REAL', 'data':[
                {'type':'0D', 'item':item, 'values':{'41':'10010','51':'9990','61':'10','71':'10'}},
                {'type':'0B', 'item':item, 'values':{'10':'10000','15':'+1','228':'101.5'}},
            ]}))
    asyncio.run(feed())
    expected['snapshot'][0].update(epoch=time.time(), native_sequence=4)
    expected['snapshot_sha256'] = digest(expected['snapshot'])
    original = manager.get_exact_item_data(result['claim']['code'], item)
    assert main.handle_zero_base_machine_enter(result)
    target = targets[0]
    data = manager.get_latest_data(target['code'])
    assert target['_zero_base_source_continuity'] == data['_zero_base_source_continuity']
    assert data['strength_momentum_history'] == original['strength_momentum_history']
    fields = handlers._scanner_fast_precheck_fields(target, now_ts=time.time(), code=target['code'], ws_data=data)
    assert fields['scanner_native_source_continuity_ready'] is True
    assert fields['fast_precheck_post_attach_entry_realtime'] is False
    assert fields['fast_precheck_reason'] != 'awaiting_first_post_attach_trade_input'
    assert len(claims) == 1
    binding = target['_entry_native_deadline_binding']
    assert binding['deadline_perf'] == expected['deadline_perf']
    assert handlers._native_handoff_deadline_perf(target, {'token':'native-once'}) == expected['deadline_perf']
    assert rows[1].status == 'WATCHING'
    # Refresh consumer preserves the same immutable receipt rather than a new clock.
    refresh = main._scanner_runtime_handoff_updates(target, source='promotion_event_refresh', existing=target)
    assert refresh['_zero_base_source_continuity'] == target['_zero_base_source_continuity']
    refresh['_zero_base_source_continuity']['adopted_epoch'] += 1
    assert refresh['_zero_base_source_continuity'] != target['_zero_base_source_continuity']


def _fixed_route_stock(at, code="036930"):
    fixed = handlers.main_fixed_watch
    route = fixed.session_route(at, code)
    return dict(code=code, strategy="SCALPING", watch_origin="MAIN_FIXED_WATCH",
        watch_generation_id=fixed.generation_id(at, route),
        market_data_route=route["route"], market_session_bucket=route["bucket"],
        effective_venue=route["venue"], broker_route="NXT" if route["route"] == "nxt_only" else "SOR")


@pytest.mark.parametrize("hour,route", [(8,"NXT"),(10,"SOR"),(17,"SOR")])
@pytest.mark.parametrize("leg", ["normal", "initial_probe", "market_first", "ioc"])
def test_fixed_watch_route_survives_plan_request_and_cancel(monkeypatch, hour, route, leg):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    at = datetime(2026,10,19,hour,10,tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    stock = _fixed_route_stock(at)
    planned = dict(qty=2,price=10000,tag="normal")
    if leg == "initial_probe": planned["initial_quantity_probe_market"] = True
    elif leg == "market_first":
        planned.update(entry_split_order_market_first_leg_applied=True,
            entry_split_order_execution_mode="market_first",entry_split_order_leg_index=1)
    elif leg == "ioc": planned["tif"] = "IOC"
    monkeypatch.setattr(handlers,"is_scalping_buy_time_allowed",lambda _t:True)
    assert handlers._bind_main_entry_order_request(stock, planned, now_ts=at)
    request = handlers._resolve_live_entry_order_request("SCALPING",planned,"00",10000)
    assert request["dmst_stex_tp"] == route
    assert handlers._bind_main_entry_order_request(stock,request,now_ts=at)
    resolution = kiwoom_orders.describe_buy_order_resolution(
        request["order_type_code"],price=request["price"],tif=request["tif"],
        dmst_stex_tp=request["dmst_stex_tp"],now=datetime.fromtimestamp(at,ZoneInfo("Asia/Seoul")))
    assert resolution["effective_dmst_stex_tp"] == route
    assert resolution["broker_route_resolution"] == "explicit_request"
    assert handlers._entry_order_cancel_dmst_stex_tp({**request,"dmst_stex_tp_source":"request"}) == route
    assert stock["broker_route"] == route


@pytest.mark.parametrize("route_request", [
    {"dmst_stex_tp":"NXT"}, {"broker_route":"KRX"},
    {"dmst_stex_tp":"SOR","exchange":"NXT"}, {"dmst_stex_tp":"INVALID"}, {"dmst_stex_tp":0}, {"dmst_stex_tp":False},
])
def test_fixed_watch_rejects_conflicting_route_without_rewriting(monkeypatch, route_request):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    at=datetime(2026,10,19,17,10,tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    stock=_fixed_route_stock(at)
    monkeypatch.setattr(handlers,"is_scalping_buy_time_allowed",lambda _t:True)
    original=dict(route_request)
    assert not handlers._bind_main_entry_order_request(stock,route_request,now_ts=at)
    assert route_request == original


def test_fixed_watch_rejects_stale_session_generation_and_closed_buy(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    zone=ZoneInfo("Asia/Seoul")
    before=datetime(2026,10,19,10,10,tzinfo=zone).timestamp()
    after=datetime(2026,10,19,17,10,tzinfo=zone).timestamp()
    stock=_fixed_route_stock(before)
    monkeypatch.setattr(handlers,"is_scalping_buy_time_allowed",lambda _t:True)
    assert not handlers._bind_main_entry_order_request(stock,{},now_ts=after)
    monkeypatch.setattr(handlers,"is_scalping_buy_time_allowed",lambda _t:False)
    assert not handlers._bind_main_entry_order_request(_fixed_route_stock(after),{},now_ts=after)


@pytest.mark.parametrize("route", ["KRX","NXT","SOR"])
def test_ordinary_explicit_plan_retains_route_without_changing_auto_default(route):
    request=handlers._resolve_live_entry_order_request(
        "SCALPING",dict(qty=1,price=10000,broker_route=route),"00",10000)
    assert request["dmst_stex_tp"] == route
    assert handlers._bind_main_entry_order_request({},request)
    auto=handlers._resolve_live_entry_order_request("SCALPING",dict(qty=1,price=10000),"00",10000)
    assert "dmst_stex_tp" not in auto


@pytest.mark.parametrize("field,value", [
    ("market_data_route","nxt_only"),("effective_venue","KRX"),
    ("market_session_bucket","krx_regular"),("watch_generation_id","old"),
    ("last_watching_ai_machine_primary_fields",{"ai_trace_broker_route":"NXT"}),
    ("last_watching_ai_machine_primary_fields","invalid-source"),
])
def test_fixed_watch_order_rejects_lost_or_conflicting_source_identity(monkeypatch,field,value):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    at=datetime(2026,10,19,17,10,tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    stock=_fixed_route_stock(at);stock[field]=value
    monkeypatch.setattr(handlers,"is_scalping_buy_time_allowed",lambda _t:True)
    assert not handlers._bind_main_entry_order_request(stock,{},now_ts=at)


@pytest.mark.parametrize("hour,decision_route,allowed", [
    (8,"NXT",True),(10,"SOR",True),(17,"SOR",True),(17,"NXT",False),
])
def test_frozen_operating_route_matches_current_watch_and_decision(monkeypatch,hour,decision_route,allowed):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping import strategy_owner_replay as replay,avg_down_replay_capture as capture
    from src.engine.lifecycle import avg_down_policy_replay as lifecycle
    from src.engine import sniper_execution_receipts as receipts
    at=datetime(2026,10,19,hour,10,tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    stock=_fixed_route_stock(at)
    stock["last_watching_ai_machine_primary_fields"]={"ai_trace_broker_route":decision_route}
    monkeypatch.setattr(handlers,"is_scalping_buy_time_allowed",lambda _t:True)
    monkeypatch.setattr(handlers,"_is_any_simulated_position",lambda *_:False)
    monkeypatch.setattr(handlers,"_holding_sell_nxt_enabled_status",lambda *_:(False,"fixture"))
    monkeypatch.setattr(capture,"_cached_policy",lambda *_:{"rules":{}})
    monkeypatch.setattr(capture,"compact_policy_snapshot",lambda *_:{})
    monkeypatch.setattr(capture,"holding_state",lambda *_:{"stock":{}})
    monkeypatch.setattr(capture,"micro_state",lambda *_:{})
    monkeypatch.setattr(lifecycle,"snapshot_version",lambda *_:"fixture")
    monkeypatch.setattr(receipts,"initial_main_entry_exit_fields",lambda *_a,**_k:{})
    monkeypatch.setattr(replay,"entry_operating_model_identity",lambda:"a"*64)
    sizing=SimpleNamespace(budget_base_krw=10000,safety_ratio=1.,absolute_budget_cap_krw=0)
    if not allowed:
        with pytest.raises(ValueError,match="main_route_invalid|decision_route_conflict"):
            replay.freeze_entry_operating_context(handlers,stock,sizing,now_ts=at,strict=True)
        assert not handlers._bind_main_entry_order_request(stock,{},now_ts=at)
    else:
        frozen=replay.freeze_entry_operating_context(handlers,stock,sizing,now_ts=at,strict=True)
        assert frozen["broker_route"] == decision_route
        from src.engine.scalping.strategy_owner_components import digest
        assert frozen["sha256"] == digest({k:v for k,v in frozen.items() if k!="sha256"})
