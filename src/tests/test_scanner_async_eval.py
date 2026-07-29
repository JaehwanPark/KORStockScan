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


def _wait_for_result(coordinator, timeout=1.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        results = coordinator.drain_completed()
        if results:
            return results[0]
        time.sleep(0.005)
    raise AssertionError("async result did not complete")


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

    assert result.status in {"superseded_before_ai", "superseded_result"}
    assert result.observation_only is True


def test_cancelled_generation_can_reactivate_only_after_transport_is_quiesced():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    generation = _generation()
    now = time.time()
    release = threading.Event()
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
            prepare=lambda ctx: (release.wait(0.5) and {"ready": True}) or {},
            evaluate=lambda ctx, prepared: {"action": "WAIT"},
        )
    ).accepted
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
