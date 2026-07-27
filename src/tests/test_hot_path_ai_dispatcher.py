from __future__ import annotations

import threading
import time

from src.engine.ai.hot_path_ai_dispatcher import (
    HotPathAIDispatcher,
    HotPathAIRequest,
)


def _wait_for_results(dispatcher, count, timeout=1.0):
    deadline = time.time() + timeout
    results = []
    while len(results) < count and time.time() < deadline:
        results.extend(dispatcher.drain_completed())
        if len(results) < count:
            time.sleep(0.005)
    return results


def test_dispatcher_deduplicates_same_generation_and_cache_key():
    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    release = threading.Event()
    calls = []

    def execute():
        calls.append("called")
        release.wait(0.5)
        return {"action": "BUY"}

    now = time.time()
    first = HotPathAIRequest.create(
        request_id="request-1",
        generation_id="generation-1",
        cache_key="cache-1",
        endpoint="entry",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=execute,
    )
    duplicate = HotPathAIRequest.create(
        request_id="request-2",
        generation_id="generation-1",
        cache_key="cache-1",
        endpoint="entry",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=execute,
    )

    assert dispatcher.submit(first).accepted is True
    decision = dispatcher.submit(duplicate)
    assert decision.accepted is False
    assert decision.canonical_request_id == "request-1"
    release.set()
    results = _wait_for_results(dispatcher, 1)
    dispatcher.shutdown()

    assert len(calls) == 1
    assert results[0].status == "completed"
    assert dict(results[0].payload) == {"action": "BUY"}


def test_dispatcher_expires_before_provider_call():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    called = False

    def execute():
        nonlocal called
        called = True
        return {}

    now = time.time()
    request = HotPathAIRequest.create(
        request_id="expired",
        generation_id="generation-1",
        cache_key="cache-expired",
        endpoint="entry",
        venue="KRX",
        submitted_epoch=now - 2,
        deadline_epoch=now - 1,
        execute=execute,
    )
    dispatcher.submit(request)
    results = _wait_for_results(dispatcher, 1)
    dispatcher.shutdown()

    assert called is False
    assert results[0].status == "expired_before_start"
    assert results[0].observation_only is True


def test_dispatcher_limits_workers_to_loaded_key_count():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1, max_workers=2)
    assert dispatcher.max_workers == 1
    dispatcher.shutdown()


def test_dispatcher_rejects_missing_provider_keys():
    try:
        HotPathAIDispatcher(loaded_key_count=0)
    except ValueError as exc:
        assert "loaded provider key" in str(exc)
    else:
        raise AssertionError("missing provider keys must fail closed")


def test_dispatcher_marks_late_provider_response_observation_only():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    now = time.time()
    request = HotPathAIRequest.create(
        request_id="late-response",
        generation_id="generation-1",
        cache_key="cache-late",
        endpoint="entry",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 0.02,
        execute=lambda: (time.sleep(0.04) or {"action": "BUY"}),
    )

    assert dispatcher.submit(request).accepted is True
    result = _wait_for_results(dispatcher, 1)[0]
    dispatcher.shutdown()

    assert result.status == "expired_after_response"
    assert result.observation_only is True
    assert result.ai_response_sec >= 0.02


def test_dispatcher_preserves_results_owned_by_other_consumers():
    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    now = time.time()
    first = HotPathAIRequest.create(
        request_id="scanner:req",
        generation_id="scanner-generation",
        cache_key="entry",
        endpoint="scanner_entry",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: {"action": "BUY"},
    )
    second = HotPathAIRequest.create(
        request_id="holding:req",
        generation_id="holding-generation",
        cache_key="holding",
        endpoint="holding_flow",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: {"action": "HOLD"},
    )
    assert dispatcher.submit(first).accepted
    assert dispatcher.submit(second).accepted

    deadline = time.time() + 1
    scanner_results = []
    while not scanner_results and time.time() < deadline:
        scanner_results = dispatcher.drain_completed(request_ids={"scanner:req"})
        if not scanner_results:
            time.sleep(0.005)
    deadline = time.time() + 1
    holding_results = []
    while not holding_results and time.time() < deadline:
        holding_results = dispatcher.drain_completed(request_ids={"holding:req"})
        if not holding_results:
            time.sleep(0.005)
    dispatcher.shutdown()

    assert [result.request_id for result in scanner_results] == ["scanner:req"]
    assert [result.request_id for result in holding_results] == ["holding:req"]


def test_dispatcher_does_not_coalesce_distinct_endpoints_with_same_snapshot_key():
    """Endpoint results are not interchangeable for one position snapshot."""

    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    now = time.time()
    holding_score = HotPathAIRequest.create(
        request_id="position:holding-score",
        generation_id="position-cycle-1",
        cache_key="snapshot-42",
        endpoint="holding_score",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: {"score": 71},
    )
    holding_flow = HotPathAIRequest.create(
        request_id="position:holding-flow",
        generation_id="position-cycle-1",
        cache_key="snapshot-42",
        endpoint="holding_flow",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: {"action": "HOLD"},
    )

    assert dispatcher.submit(holding_score).accepted is True
    assert dispatcher.submit(holding_flow).accepted is True
    results = _wait_for_results(dispatcher, 2)
    dispatcher.shutdown()

    assert {result.endpoint for result in results} == {"holding_score", "holding_flow"}


def test_dispatcher_coalesces_endpoint_aliases_after_canonicalization():
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    now = time.time()
    release = threading.Event()
    first = HotPathAIRequest.create(
        request_id="position:price-1",
        generation_id="position-cycle-1",
        cache_key="snapshot-42",
        endpoint="entry_price",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: (release.wait(0.5), {"action": "USE_REFERENCE"})[1],
    )
    alias = HotPathAIRequest.create(
        request_id="position:price-2",
        generation_id="position-cycle-1",
        cache_key="snapshot-42",
        endpoint=" ENTRY_PRICE ",
        venue="KRX",
        submitted_epoch=now,
        deadline_epoch=now + 1,
        execute=lambda: {"action": "USE_REFERENCE"},
    )

    assert dispatcher.submit(first).accepted is True
    duplicate = dispatcher.submit(alias)
    release.set()
    results = _wait_for_results(dispatcher, 1)
    dispatcher.shutdown()

    assert duplicate.accepted is False
    assert duplicate.reason == "duplicate_generation_cache_key_coalesced"
    assert results[0].endpoint == "entry_price"
