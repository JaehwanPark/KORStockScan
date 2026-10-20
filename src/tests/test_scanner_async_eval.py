from __future__ import annotations

import time
import threading
import pytest

from src.engine.ai.hot_path_ai_dispatcher import (
    HotPathAIDispatcher,
    HotPathAIRequest,
)
from src.engine.scalping.scanner_async_eval import (
    ScannerAsyncEvalContext,
    ScannerAsyncEvalCoordinator,
    ScannerAsyncEvalRequest,
    validate_scanner_async_commit,
)
from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration


def test_exact_fixed_watch_completion_can_be_consumed_in_current_main_pass(monkeypatch):
    from src.engine.scalping import scanner_async_eval as M
    monkeypatch.setattr(M, 'record_async_disposition', lambda *a, **k: True)
    dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    coordinator=ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now=time.time()
    generation=M.FixedWatchGeneration('036930', 'SOR', 'fixed:g', 'source', now)
    context=ScannerAsyncEvalContext.create(generation=generation, cache_key='original',
        submitted_epoch=now, deadline_epoch=now+2., stock_snapshot={'status':'WATCHING'},
        ws_snapshot={'curr':1000}, state_version='WATCHING:0:0')
    try:
        assert coordinator.submit(ScannerAsyncEvalRequest(context=context,
            prepare=lambda ctx:{'ready':True}, evaluate=lambda ctx,prepared:{'action':'WAIT'})).accepted
        deadline=time.time()+1.
        while not coordinator.has_undrained_result() and time.time()<deadline:
            time.sleep(.005)
        assert coordinator.has_undrained_result()
        keys=coordinator.fixed_watch_ready_requests()
        assert list(keys)==[('fixed:g','original')]
        assert keys['fixed:g','original']>0
        assert not coordinator.has_undrained_result(direct_fixed_requests={('fixed:g','original')})
        assert coordinator.has_undrained_result(direct_fixed_requests={('fixed:g','different')})
        # Notification drain does not destroy the retained original identity.
        result=coordinator.drain_completed()[0]
        assert coordinator.fixed_watch_ready_requests()==keys
        assert result.deadline_epoch==context.deadline_epoch
        assert result.ai_payload['entry_local_stage_clocks']['async_evaluation_completed_perf'] <= result.coordinator_ready_perf
        assert coordinator.take_completed(generation_id='fixed:g',cache_key='original') is result
        assert not coordinator.fixed_watch_ready_requests()
        assert not coordinator.has_undrained_result()
    finally:
        coordinator.shutdown()


def test_scanner_completion_still_requires_scheduler_drain(monkeypatch):
    from src.engine.scalping import scanner_async_eval as M
    monkeypatch.setattr(M, 'record_async_disposition', lambda *a, **k: True)
    dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    coordinator=ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now=time.time()
    context=ScannerAsyncEvalContext.create(generation=_generation(),cache_key='scanner',
        submitted_epoch=now,deadline_epoch=now+2.,stock_snapshot={'status':'WATCHING'},
        ws_snapshot={'curr':1000},state_version='WATCHING:0:0')
    try:
        assert coordinator.submit(ScannerAsyncEvalRequest(context=context,
            prepare=lambda ctx:{},evaluate=lambda ctx,prepared:{'action':'WAIT'})).accepted
        deadline=time.time()+1.
        while not coordinator.has_undrained_result() and time.time()<deadline:
            time.sleep(.005)
        assert coordinator.has_undrained_result(direct_fixed_requests={('unused','scanner')})
        assert coordinator.fixed_watch_ready_requests()=={}
    finally:
        coordinator.shutdown()


def test_coordinator_ready_clock_is_stamped_only_at_locked_publication(monkeypatch):
    from src.engine.scalping import scanner_async_eval as M
    monkeypatch.setattr(M, 'record_async_disposition', lambda *a, **k: True)
    coordinator=ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    now=time.time()
    context=ScannerAsyncEvalContext.create(generation=_generation(),cache_key='publish',
        submitted_epoch=now,deadline_epoch=now+2.,stock_snapshot={'status':'WATCHING'},
        ws_snapshot={},state_version='WATCHING:0:0')
    request=ScannerAsyncEvalRequest(context=context,prepare=lambda ctx:{},evaluate=lambda ctx,p:{})
    coordinator._requests[context.request_id]=request
    calls=[]
    original_replace=M.replace
    def recorded_replace(result, **fields):
        calls.append(coordinator._lock._is_owned())
        return original_replace(result, **fields)
    monkeypatch.setattr(M, 'replace', recorded_replace)
    try:
        coordinator._finish(request,status='completed',preparation_started_epoch=now,
            preparation_completed_epoch=now,completed_epoch=now,observation_only=False)
        assert calls==[True]
        assert coordinator.peek_completed(generation_id=context.generation.generation_id,
            cache_key='publish').coordinator_ready_perf>0
    finally:
        coordinator.shutdown()


def _generation(*, promotion_id="PROMO-1", revision=1, venue="KRX"):
    return ScannerGeneration(
        code="005930",
        promotion_id=promotion_id,
        revision=revision,
        record_id=1,
        venue=venue,
        promotion_epoch=100.0,
        attach_epoch=101.0,
        observed_price=1000,
        source_signature="VALUE_TOP",
    )


def test_worker_completion_publishes_original_result_without_main_poll(monkeypatch):
    from src.engine.scalping import scanner_async_eval as M
    monkeypatch.setattr(M, 'record_async_disposition', lambda *a, **k: True)
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    generation = _generation()
    context = ScannerAsyncEvalContext.create(generation=generation, cache_key='direct',
        submitted_epoch=now, deadline_epoch=now+2, stock_snapshot={}, ws_snapshot={}, state_version='original')
    try:
        assert coordinator.submit(ScannerAsyncEvalRequest(context=context,
            prepare=lambda ctx: {'snapshot': {'price': 100}},
            evaluate=lambda ctx, prepared: {'action': 'BUY'})).accepted
        deadline = time.time()+1
        while time.time() < deadline:
            with coordinator._lock:
                published = list(coordinator._ready.values())
            if published:
                break
            time.sleep(.001)
        assert len(published) == 1
        result = published[0]
        assert result.original_generation is generation and result.deadline_epoch == context.deadline_epoch
        assert result.prepared_context['snapshot']['price'] == 100
        assert result.request_id == context.request_id
        # Immediate publication still has no authority to skip Main guards.
        decision = validate_scanner_async_commit(result, current_generation=generation,
            current_status='WATCHING', current_venue='KRX', current_source_signature='VALUE_TOP',
            venue_resolution_valid=True, current_state_version='original', quote_fresh=False,
            position_or_pending_order_present=False, cooldown_active=False, now_epoch=time.time())
        assert not decision.allowed
        assert coordinator.take_completed(generation_id=generation.generation_id, cache_key='direct') is result
        assert coordinator.take_completed(generation_id=generation.generation_id, cache_key='direct') is None
    finally:
        coordinator.shutdown()


def test_failed_immediate_completion_retains_result_and_prepared_source(monkeypatch):
    from src.engine.scalping import scanner_async_eval as M
    monkeypatch.setattr(M, 'record_async_disposition', lambda *a, **k: True)
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    context = ScannerAsyncEvalContext.create(generation=_generation(), cache_key='retained',
        submitted_epoch=now, deadline_epoch=now+2, stock_snapshot={}, ws_snapshot={}, state_version='original')
    original = coordinator._finish
    failed = threading.Event()
    def fail_once(*args, **kwargs):
        if not failed.is_set():
            failed.set()
            raise ValueError('diagnostic_projection_failed')
        return original(*args, **kwargs)
    monkeypatch.setattr(coordinator, '_finish', fail_once)
    try:
        assert coordinator.submit(ScannerAsyncEvalRequest(context=context,
            prepare=lambda ctx: {'source': 'original'}, evaluate=lambda ctx, p: {'action': 'WAIT'})).accepted
        assert failed.wait(1)
        # The callback publishes its failure before requeueing the same result.
        deadline=time.time()+1
        while time.time()<deadline:
            with dispatcher._lock:
                restored=bool(dispatcher._completed)
            if restored:
                break
            time.sleep(.001)
        assert restored
        assert coordinator.poll() == 1
        result=coordinator.take_completed(generation_id=context.generation.generation_id, cache_key='retained')
        assert result.prepared_context['source'] == 'original'
        assert result.deadline_epoch == context.deadline_epoch
        assert coordinator.poll() == 0
    finally:
        coordinator.shutdown()


def test_owned_async_snapshot_shares_only_proven_immutable_children(monkeypatch):
    from types import MappingProxyType, SimpleNamespace
    from src.engine.scalping import scanner_async_eval as M
    raw = {'quote': {'bid': 99}, 'rows': [{'price': 100}], 'tags': {'source'}}
    frozen = M._immutable_mapping(MappingProxyType(raw))
    raw['quote']['bid'] = 1
    raw['rows'][0]['price'] = 2
    assert frozen['quote']['bid'] == 99 and frozen['rows'][0]['price'] == 100
    assert M._immutable_mapping(frozen) is frozen
    with pytest.raises(TypeError):
        frozen['quote']['bid'] = 3
    with pytest.raises(TypeError):
        frozen._values = {}
    thawed = M.thaw_scanner_async_value(frozen)
    thawed['rows'][0]['price'] = 4
    assert frozen['rows'][0]['price'] == 100
    # Read-only mapping views and copied custom objects are not proof that
    # their backing objects are immutable at the next ownership boundary.
    box = SimpleNamespace(value=[1])
    first = M._immutable_mapping({'box': box, 'quote': frozen['quote']})
    second = M._immutable_mapping(first)
    first['box'].value.append(2)
    assert second['box'].value == [1]
    assert second['quote'] is first['quote']
    box.value.append(9)
    assert first['box'].value == [1, 2]


def test_async_scalar_snapshot_does_not_invoke_custom_copy_protocol(monkeypatch):
    from src.engine.scalping import scanner_async_eval as M
    def unexpected(value):
        raise AssertionError('atomic deepcopy')
    from src.engine.infrastructure import snapshot_copy as snapshots
    monkeypatch.setattr(snapshots.copy, 'deepcopy', unexpected)
    original = {'price': 100, 'rows': [{'source': '0B', 'ok': True, 'age': .5, 'missing': None}]}
    frozen = M._immutable_mapping(original)
    assert frozen['price'] == 100 and frozen['rows'][0]['missing'] is None


def _wait_for_result(coordinator, timeout=1.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        results = coordinator.drain_completed()
        if results:
            return results[0]
        time.sleep(0.005)
    raise AssertionError("async result did not complete")


@pytest.mark.parametrize('expired', [False, True])
def test_native_invalidation_keeps_cause_without_bypassing_deadline(expired):
    from types import SimpleNamespace
    generation = _generation()
    result = SimpleNamespace(status='completed', observation_only=False,
        deadline_epoch=104 if expired else 106, deadline_perf=0,
        completed_epoch=103, generation_id=generation.generation_id,
        venue='SOR', state_version='WATCHING:0:0')
    decision = validate_scanner_async_commit(result, current_generation=generation,
        current_status='WATCHING', current_venue='KRX', current_source_signature='VALUE_TOP',
        venue_resolution_valid=False, current_state_version='WATCHING:0:0',
        quote_fresh=True, position_or_pending_order_present=False, cooldown_active=False,
        now_epoch=105, native_validation_error='reversal_signal_path_changed')
    assert not decision.allowed
    assert decision.reason == ('result_deadline_expired' if expired else 'reversal_signal_path_changed')
    assert decision.fields['scanner_async_native_validation_error'] == 'reversal_signal_path_changed'


def test_async_execution_refresh_is_immutable_and_retained_for_commit():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    source = {"ws_data": {"curr": 1002}, "recent_ticks": [{"price": 1002}]}
    evaluated = []
    now = time.time()
    context = ScannerAsyncEvalContext.create(
        generation=_generation(),
        cache_key="execution-frame",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:0:0",
    )

    def refresh(_ctx, prepared):
        assert prepared["ws_data"]["curr"] == 1000
        with pytest.raises(TypeError):
            prepared["ws_data"]["curr"] = 9
        return source

    def evaluate(_ctx, prepared):
        evaluated.append(prepared)
        with pytest.raises(TypeError):
            prepared["ws_data"]["curr"] = 9
        source["ws_data"]["curr"] = 9000
        return {"action": "WAIT", "evaluated_price": prepared["ws_data"]["curr"]}

    try:
        assert coordinator.submit(
            ScannerAsyncEvalRequest(
                context=context,
                prepare=lambda _ctx: {"ws_data": {"curr": 1000}},
                evaluate=evaluate,
                refresh_before_evaluate=refresh,
            )
        ).accepted
        result = _wait_for_result(coordinator)
        assert result.status == "completed"
        assert result.prepared_context == evaluated[0]
        assert result.prepared_context["ws_data"]["curr"] == 1002
        assert result.ai_payload["evaluated_price"] == 1002
        assert context.ws_snapshot["curr"] == 1000
    finally:
        coordinator.shutdown(wait=True)


@pytest.mark.parametrize("failure", ["error", "deadline", "superseded", "malformed"])
def test_async_refresh_failure_never_reaches_evaluator(failure):
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    context = ScannerAsyncEvalContext.create(
        generation=_generation(),
        cache_key=f"refresh-{failure}",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:0:0",
    )
    evaluated = []

    def refresh(_ctx, prepared):
        if failure == "malformed":
            return None
        if failure == "error":
            raise ValueError("invalid frame")
        if failure == "superseded":
            coordinator.invalidate_generation(context.generation.generation_id)
        if failure == "deadline":
            threading.Event().wait(max(0, context.deadline_epoch - time.time()) + 0.02)
        return {"ws_data": {"curr": 1002}}

    try:
        assert coordinator.submit(
            ScannerAsyncEvalRequest(
                context=context,
                prepare=lambda _ctx: {"ws_data": {"curr": 1000}},
                evaluate=lambda _ctx, _prepared: evaluated.append(True) or {},
                refresh_before_evaluate=refresh,
            )
        ).accepted
        result = _wait_for_result(coordinator, timeout=2.0)
        assert evaluated == []
        assert result.observation_only is True
        assert result.status in {"error", "superseded_result"}
        assert result.ai_payload == {}
    finally:
        coordinator.shutdown(wait=True)


def test_async_eval_reports_exact_retained_result_before_commit_consumes_it():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    try:
        now = time.time()
        generation = _generation()
        context = ScannerAsyncEvalContext.create(
            generation=generation,
            cache_key="ready-before-commit",
            submitted_epoch=now,
            deadline_epoch=now + 1,
            stock_snapshot={"status": "WATCHING"},
            ws_snapshot={"curr": 1000},
            state_version="WATCHING:0:0",
        )
        assert coordinator.submit(
            ScannerAsyncEvalRequest(
                context=context,
                prepare=lambda _ctx: {"prepared": True},
                evaluate=lambda _ctx, _prepared: {},
                requires_ai_dispatch=False,
            )
        ).accepted

        _wait_for_result(coordinator)
        assert coordinator.has_completed(
            generation_id=generation.generation_id,
            cache_key="ready-before-commit",
        )
        assert (
            coordinator.take_completed(
                generation_id=generation.generation_id,
                cache_key="ready-before-commit",
            )
            is not None
        )
        assert not coordinator.has_completed(
            generation_id=generation.generation_id,
            cache_key="ready-before-commit",
        )
    finally:
        coordinator.shutdown(wait=True)


def test_async_eval_does_not_overwrite_completed_result_pending_commit():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    try:
        now = time.time()
        generation = _generation()
        context = ScannerAsyncEvalContext.create(
            generation=generation,
            cache_key="retain-first-result",
            submitted_epoch=now,
            deadline_epoch=now + 1,
            stock_snapshot={"status": "WATCHING"},
            ws_snapshot={"curr": 1000},
            state_version="WATCHING:0:0",
        )
        first = ScannerAsyncEvalRequest(
            context=context,
            prepare=lambda _ctx: {"sequence": 1},
            evaluate=lambda _ctx, _prepared: {"action": "BUY", "score": 72},
        )
        assert coordinator.submit(first).accepted
        _wait_for_result(coordinator)

        duplicate = ScannerAsyncEvalRequest(
            context=context,
            prepare=lambda _ctx: {"sequence": 2},
            evaluate=lambda _ctx, _prepared: {"action": "DROP", "score": 0},
        )
        duplicate_decision = coordinator.submit(duplicate)
        retained = coordinator.take_completed(
            generation_id=generation.generation_id,
            cache_key=context.cache_key,
        )

        assert duplicate_decision.accepted is False
        assert duplicate_decision.reason == "completed_result_pending_commit"
        assert retained is not None
        assert retained.prepared_context["sequence"] == 1
        assert retained.ai_payload["action"] == "BUY"
        assert retained.ai_payload["score"] == 72
    finally:
        coordinator.shutdown(wait=True)


def test_async_eval_keeps_worker_snapshots_immutable_and_commits_on_main_guard():
    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    generation = _generation()
    stock = {"status": "WATCHING", "nested": {"value": 1}}
    ws = {"curr": 1000, "nested": {"bid": 999}}
    context = ScannerAsyncEvalContext.create(
        generation=generation,
        cache_key="entry-context",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot=stock,
        ws_snapshot=ws,
        state_version="WATCHING:0:0",
    )
    stock["nested"]["value"] = 9
    ws["nested"]["bid"] = 1
    request = ScannerAsyncEvalRequest(
        context=context,
        prepare=lambda ctx: {
            "stock_value": ctx.stock_snapshot["nested"]["value"],
            "bid": ctx.ws_snapshot["nested"]["bid"],
        },
        evaluate=lambda ctx, prepared: {
            "action": "BUY",
            "stock_value": prepared["stock_value"],
        },
    )

    assert coordinator.submit(request).accepted is True
    result = _wait_for_result(coordinator)
    decision = validate_scanner_async_commit(
        result,
        current_generation=generation,
        current_status="WATCHING",
        current_venue="KRX",
        current_source_signature="VALUE_TOP",
        venue_resolution_valid=True,
        current_state_version="WATCHING:0:0",
        quote_fresh=True,
        position_or_pending_order_present=False,
        cooldown_active=False,
        now_epoch=time.time(),
    )
    coordinator.shutdown()

    assert result.status == "completed"
    assert result.prepared_context["stock_value"] == 1
    assert result.prepared_context["bid"] == 999
    assert result.ai_payload["action"] == "BUY"
    assert decision.allowed is True
    with pytest.raises(TypeError):
        context.stock_snapshot["nested"]["value"] = 3


def test_context_only_preparation_completes_without_ai_dispatch():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    context = ScannerAsyncEvalContext.create(
        generation=_generation(),
        cache_key="context-only",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:0:0",
    )
    assert coordinator.submit(
        ScannerAsyncEvalRequest(
            context=context,
            prepare=lambda _ctx: {"candles": [1, 2]},
            evaluate=lambda _ctx, _prepared: pytest.fail("AI must not be dispatched"),
            requires_ai_dispatch=False,
        )
    ).accepted

    result = _wait_for_result(coordinator)
    coordinator.shutdown()

    assert result.status == "completed"
    assert list(result.prepared_context["candles"]) == [1, 2]
    assert result.ai_dispatch_wait_sec == 0.0
    assert result.ai_response_sec == 0.0


def test_undrained_result_probe_closes_after_scheduler_drain_without_consuming_commit():
    """A heavy-loop yield must leave the result for the COMMIT owner."""

    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    context = ScannerAsyncEvalContext.create(
        generation=_generation(),
        cache_key="commit-ready-probe",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:0:0",
    )
    assert coordinator.submit(
        ScannerAsyncEvalRequest(
            context=context,
            prepare=lambda _ctx: {"ready": True},
            evaluate=lambda _ctx, _prepared: {},
            requires_ai_dispatch=False,
        )
    ).accepted

    deadline = time.time() + 1
    while not coordinator.has_undrained_result() and time.time() < deadline:
        time.sleep(0.005)
    completed = coordinator.drain_completed()
    assert len(completed) == 1
    assert coordinator.has_undrained_result() is False
    assert coordinator.has_completed_result() is True
    result = coordinator.take_completed(
        generation_id=context.generation.generation_id,
        cache_key=context.cache_key,
    )
    coordinator.shutdown()

    assert result is not None
    assert result.status == "completed"
    assert result.prepared_context["ready"] is True


def test_async_eval_superseded_result_is_observation_only():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    generation = _generation()
    context = ScannerAsyncEvalContext.create(
        generation=generation,
        cache_key="entry-context",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:0:0",
    )
    coordinator.submit(
        ScannerAsyncEvalRequest(
            context=context,
            prepare=lambda ctx: {"ticks": [1]},
            evaluate=lambda ctx, prepared: {"action": "BUY"},
        )
    )
    coordinator.invalidate_generation(generation.generation_id)
    result = _wait_for_result(coordinator)
    coordinator.shutdown()

    assert result.status in {"superseded_before_preparation", "superseded_before_ai", "superseded_result"}
    assert result.observation_only is True


def test_cancelled_generation_can_reactivate_only_after_transport_is_quiesced():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    generation = _generation()
    now = time.time()
    release = threading.Event()
    started = threading.Event()
    pending_context = ScannerAsyncEvalContext.create(
        generation=generation,
        cache_key="pending",
        submitted_epoch=now,
        deadline_epoch=now + 2,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:pending",
    )
    assert coordinator.submit(
        ScannerAsyncEvalRequest(
            context=pending_context,
            prepare=lambda ctx: (started.set(), release.wait(0.5), {"ready": True})[-1],
            evaluate=lambda ctx, prepared: {"action": "WAIT"},
        )
    ).accepted
    assert started.wait(0.5)  # Test an active physical worker, not queued cancellation.
    coordinator.invalidate_generation(generation.generation_id)
    assert coordinator.reactivate_generation(generation.generation_id) is False

    release.set()
    first = _wait_for_result(coordinator)
    assert first.status in {"superseded_before_ai", "superseded_result"}
    coordinator.discard_completed(
        generation_id=generation.generation_id,
        cache_key=pending_context.cache_key,
    )
    orphan_request_id = f"{generation.generation_id}:undrained"
    with coordinator._lock:
        coordinator._undrained_request_ids.add(orphan_request_id)
    assert coordinator.reactivate_generation(generation.generation_id) is False
    with coordinator._lock:
        coordinator._undrained_request_ids.discard(orphan_request_id)
    assert coordinator.reactivate_generation(generation.generation_id) is True

    retry_now = time.time()
    retry_context = ScannerAsyncEvalContext.create(
        generation=generation,
        cache_key="retry",
        submitted_epoch=retry_now,
        deadline_epoch=retry_now + 2,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1010},
        state_version="WATCHING:retry",
    )
    assert coordinator.submit(
        ScannerAsyncEvalRequest(
            context=retry_context,
            prepare=lambda ctx: {"ready": True},
            evaluate=lambda ctx, prepared: {"action": "BUY"},
        )
    ).accepted
    retry = _wait_for_result(coordinator)
    coordinator.shutdown()

    assert retry.status == "completed"
    assert retry.observation_only is False


def test_coordinator_can_release_without_closing_shared_dispatcher():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=dispatcher,
        owns_ai_dispatcher=False,
    )
    coordinator.shutdown()

    now = time.time()
    request = HotPathAIRequest.create(
        request_id="shared-dispatcher-still-open",
        generation_id="holding-generation",
        cache_key="holding",
        endpoint="holding_flow",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: {"action": "HOLD"},
    )
    assert dispatcher.submit(request).accepted
    deadline = time.time() + 1
    results = []
    while not results and time.time() < deadline:
        results = dispatcher.drain_completed()
        if not results:
            time.sleep(0.005)
    dispatcher.shutdown()

    assert [result.request_id for result in results] == ["shared-dispatcher-still-open"]


def test_commit_rejects_stale_quote_and_generation_change():
    generation = _generation()
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    now = time.time()
    context = ScannerAsyncEvalContext.create(
        generation=generation,
        cache_key="entry-context",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        stock_snapshot={"status": "WATCHING"},
        ws_snapshot={"curr": 1000},
        state_version="WATCHING:0:0",
    )
    coordinator.submit(
        ScannerAsyncEvalRequest(
            context=context,
            prepare=lambda ctx: {},
            evaluate=lambda ctx, prepared: {"action": "BUY"},
        )
    )
    result = _wait_for_result(coordinator)
    stale = validate_scanner_async_commit(
        result,
        current_generation=generation,
        current_status="WATCHING",
        current_venue="KRX",
        current_source_signature="VALUE_TOP",
        venue_resolution_valid=True,
        current_state_version="WATCHING:0:0",
        quote_fresh=False,
        position_or_pending_order_present=False,
        cooldown_active=False,
        now_epoch=time.time(),
    )
    superseded = validate_scanner_async_commit(
        result,
        current_generation=_generation(promotion_id="PROMO-2", revision=2),
        current_status="WATCHING",
        current_venue="KRX",
        current_source_signature="VALUE_TOP",
        venue_resolution_valid=True,
        current_state_version="WATCHING:0:0",
        quote_fresh=True,
        position_or_pending_order_present=False,
        cooldown_active=False,
        now_epoch=time.time(),
    )
    source_conflict = validate_scanner_async_commit(
        result,
        current_generation=generation,
        current_status="WATCHING",
        current_venue="KRX",
        current_source_signature="MOMENTUM_TOP",
        venue_resolution_valid=True,
        current_state_version="WATCHING:0:0",
        quote_fresh=True,
        position_or_pending_order_present=False,
        cooldown_active=False,
        now_epoch=time.time(),
    )
    venue_gap = validate_scanner_async_commit(
        result,
        current_generation=generation,
        current_status="WATCHING",
        current_venue="KRX",
        current_source_signature="VALUE_TOP",
        venue_resolution_valid=False,
        current_state_version="WATCHING:0:0",
        quote_fresh=True,
        position_or_pending_order_present=False,
        cooldown_active=False,
        now_epoch=time.time(),
    )
    coordinator.shutdown()

    assert stale.allowed is False
    assert stale.reason == "quote_stale_or_missing"
    assert superseded.allowed is False
    assert superseded.reason == "generation_superseded"
    assert source_conflict.reason == "source_signature_conflict"
    assert venue_gap.reason == "venue_resolution_missing_or_conflicted"


def test_async_eval_stress_16_promotions_and_superseded_generation():
    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    release = threading.Event()
    generations = [
        ScannerGeneration(
            code=f"{index:06d}",
            promotion_id=f"PROMO-{index}",
            revision=1,
            record_id=index,
            venue=("KRX", "PREMARKET_KRX_LIKE", "NXT")[index % 3],
            promotion_epoch=100.0 + index,
            attach_epoch=101.0 + index,
            observed_price=1000 + index,
            source_signature="VALUE_TOP",
        )
        for index in range(16)
    ]
    now = time.time()
    for index, generation in enumerate(generations):
        context = ScannerAsyncEvalContext.create(
            generation=generation,
            cache_key="entry-context",
            submitted_epoch=now,
            deadline_epoch=now + 2,
            stock_snapshot={"status": "WATCHING", "index": index},
            ws_snapshot={"curr": 1000 + index},
            state_version=f"WATCHING:{index}",
        )
        assert coordinator.submit(
            ScannerAsyncEvalRequest(
                context=context,
                prepare=lambda ctx: {"index": ctx.stock_snapshot["index"]},
                evaluate=lambda ctx, prepared: (
                    release.wait(0.25) and {"action": "BUY", "index": prepared["index"]}
                )
                or {"action": "WAIT", "index": prepared["index"]},
            )
        ).accepted

    coordinator.invalidate_generation(generations[-1].generation_id)
    release.set()
    deadline = time.time() + 3
    results = []
    while len(results) < 16 and time.time() < deadline:
        results.extend(coordinator.drain_completed())
        if len(results) < 16:
            time.sleep(0.005)
    coordinator.shutdown()

    assert len(results) == 16
    assert sum(result.status == "completed" for result in results) == 15
    superseded = [
        result
        for result in results
        if result.generation_id == generations[-1].generation_id
    ]
    assert len(superseded) == 1
    assert superseded[0].observation_only is True


def _bounded_request(key, prepare=None, *, generation=None):
    now = time.time()
    context = ScannerAsyncEvalContext.create(
        generation=generation or _generation(), cache_key=key,
        submitted_epoch=now, deadline_epoch=now + 5,
        stock_snapshot={}, ws_snapshot={}, state_version="WATCHING:0:0",
    )
    return ScannerAsyncEvalRequest(
        context=context, prepare=prepare or (lambda _ctx: {}),
        evaluate=lambda _ctx, _prepared: {}, requires_ai_dispatch=False,
    )


@pytest.mark.parametrize("submitted,deadline", [(True, 2), (1, True), (float("nan"), 2), (1, float("inf")), (float("-inf"), 2)])
def test_context_rejects_invalid_clock_values(submitted, deadline):
    with pytest.raises(ValueError):
        ScannerAsyncEvalContext.create(
            generation=_generation(), cache_key="invalid-clock",
            submitted_epoch=submitted, deadline_epoch=deadline,
            stock_snapshot={}, ws_snapshot={}, state_version="WATCHING",
        )


def test_preparation_capacity_preserves_pending_and_commit_results(monkeypatch):
    from src.engine.scalping import scanner_async_eval as module
    monkeypatch.setattr(module, "_MAX_READY_RESULTS", 3)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    entered, release = threading.Event(), threading.Event()
    def prepare(_ctx):
        entered.set()
        assert release.wait(2)
        return {}
    requests = [_bounded_request(str(i), prepare if i == 0 else None) for i in range(4)]
    try:
        assert coordinator.submit(requests[0]).accepted
        assert entered.wait(1)
        assert coordinator.submit(requests[1]).accepted
        assert coordinator.submit(requests[2]).accepted
        assert not coordinator.submit(requests[0]).accepted
        assert coordinator.submit(requests[3]).reason == "market_preparation_capacity_deferred"
        release.set()
        deadline = time.time() + 1
        while coordinator.pending_count() and time.time() < deadline:
            time.sleep(.005)
        assert coordinator.pending_count() == 0
        # Notification drain alone cannot discard output needed for COMMIT.
        assert len(coordinator.drain_completed()) == 3
        assert coordinator.submit(requests[3]).reason == "market_preparation_capacity_deferred"
        first = requests[0].context
        assert coordinator.take_completed(generation_id=first.generation.generation_id, cache_key=first.cache_key)
        assert coordinator.submit(requests[3]).accepted
    finally:
        release.set()
        coordinator.shutdown(wait=True)


def test_preparation_enqueue_failure_does_not_leave_pending(monkeypatch):
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    request = _bounded_request("enqueue-failure")
    original = coordinator._preparation_executor.submit
    def fail(*args, **kwargs):
        raise RuntimeError("executor unavailable")
    try:
        monkeypatch.setattr(coordinator._preparation_executor, "submit", fail)
        assert coordinator.submit(request).reason == "market_preparation_enqueue_failed"
        assert coordinator.pending_count() == 0
        assert coordinator._preparation_futures == {}
        monkeypatch.setattr(coordinator._preparation_executor, "submit", original)
        assert coordinator.submit(request).accepted
        assert _wait_for_result(coordinator).status == "completed"
    finally:
        coordinator.shutdown(wait=True)


def test_cancelled_queued_preparation_never_calls_source(monkeypatch):
    from src.engine.scalping import scanner_async_eval as module
    monkeypatch.setattr(module, "_MAX_CANCELLED_GENERATIONS", 2)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    entered, release = threading.Event(), threading.Event()
    calls = []
    def prepare(_ctx):
        entered.set()
        assert release.wait(2)
        return {}
    first = _bounded_request("running", prepare)
    second = _bounded_request("queued", lambda _ctx: calls.append(True) or {}, generation=_generation(promotion_id="PROMO-2"))
    try:
        assert coordinator.submit(first).accepted
        assert entered.wait(1)
        assert coordinator.submit(second).accepted
        coordinator.invalidate_generation(second.context.generation.generation_id)
        result = _wait_for_result(coordinator)
        assert result.status == "superseded_before_preparation"
        assert result.observation_only
        assert calls == []
        coordinator.invalidate_generation(first.context.generation.generation_id)
        for i in range(5):
            coordinator.invalidate_generation(f"quiescent-{i}")
        assert first.context.generation.generation_id in coordinator._cancelled_generations
        assert not coordinator.reactivate_generation(first.context.generation.generation_id)
        release.set()
        result = _wait_for_result(coordinator)
        assert result.observation_only and result.status == "superseded_before_ai"
    finally:
        release.set()
        coordinator.shutdown(wait=True)


def test_consumed_result_releases_notification_capacity_and_prevents_duplicate(monkeypatch):
    from src.engine.scalping import scanner_async_eval as module
    monkeypatch.setattr(module, "_MAX_READY_RESULTS", 2)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    try:
        requests = [_bounded_request(str(i)) for i in range(3)]
        for request in requests[:2]:
            assert coordinator.submit(request).accepted
            deadline = time.time() + 1
            while coordinator.pending_count() and time.time() < deadline:
                time.sleep(.005)
            ctx = request.context
            assert coordinator.take_completed(generation_id=ctx.generation.generation_id, cache_key=ctx.cache_key)
        assert coordinator.submit(requests[0]).reason == "result_already_consumed"
        assert coordinator.drain_completed(limit=1) == []
        assert coordinator.submit(requests[2]).accepted
    finally:
        coordinator.shutdown(wait=True)


def test_ai_dispatch_exception_closes_pending_as_observation(monkeypatch):
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    request = _bounded_request("ai-enqueue-failure")
    request = ScannerAsyncEvalRequest(context=request.context, prepare=request.prepare, evaluate=request.evaluate, requires_ai_dispatch=True)
    def fail(*args, **kwargs):
        raise RuntimeError("dispatcher unavailable")
    try:
        monkeypatch.setattr(coordinator.ai_dispatcher, "submit", fail)
        assert coordinator.submit(request).accepted
        result = _wait_for_result(coordinator)
        assert result.status == "ai_dispatch_error" and result.observation_only
        assert coordinator.pending_count() == 0
    finally:
        coordinator.shutdown(wait=True)


def test_poll_publication_failure_retains_all_drained_results_in_original_order(monkeypatch):
    from dataclasses import replace
    from src.engine.scalping import scanner_async_eval as M
    monkeypatch.setattr(M, 'record_async_disposition', lambda *a, **k: True)
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    requests = [replace(_bounded_request('retain-'+str(i), prepare=lambda ctx: {'source': ctx.cache_key}),
                        requires_ai_dispatch=True) for i in range(2)]
    coordinator._poll_lock.acquire()
    try:
        for request in requests:
            assert coordinator.submit(request).accepted
        deadline = time.time()+1
        while time.time()<deadline:
            with dispatcher._lock:
                original = list(dispatcher._completed)
            if len(original)==2:
                break
            time.sleep(.001)
        assert len(original)==2
    finally:
        coordinator._poll_lock.release()
    finish = coordinator._finish
    def failure(*args, **kwargs):
        raise ValueError('publication_failed')
    monkeypatch.setattr(coordinator, '_finish', failure)
    try:
        with pytest.raises(ValueError, match='publication_failed'):
            coordinator.poll()
        with dispatcher._lock:
            assert list(dispatcher._completed)==original
        monkeypatch.setattr(coordinator, '_finish', finish)
        assert coordinator.poll()==2
        for request in requests:
            result=coordinator.take_completed(generation_id=request.context.generation.generation_id,
                                              cache_key=request.context.cache_key)
            assert result.deadline_epoch==request.context.deadline_epoch
            assert result.prepared_context['source']==request.context.cache_key
        assert coordinator.poll()==0
    finally:
        coordinator.shutdown()
