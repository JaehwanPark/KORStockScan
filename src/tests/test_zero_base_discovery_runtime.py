from datetime import datetime
from zoneinfo import ZoneInfo
import time
import threading
import pytest

from src.scanners.zero_base_discovery_runtime import (
    MAX_CONCURRENT_PROBES,
    MACHINE_ENTER_EVENT,
    PROBE_REQUEST_EVENT,
    PROBE_RESULT_EVENT,
    ZeroBaseDiscoveryRuntime,
)

T0 = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()


@pytest.fixture(autouse=True)
def _selected_fixture_requirements(monkeypatch):
    # These are orchestration tests; real selected definitions are exercised
    # separately by the native source/readiness contract tests.
    from src.engine.scalping import reversal_source_diagnostics as D

    monkeypatch.setattr(D, "residence_requirements", lambda *a: {"minimum_seconds": 0})
    from src.scanners import zero_base_discovery_runtime as R

    monkeypatch.setattr(
        R,
        "discovery_product_filter",
        lambda *a: lambda code, name, market: dict(
            eligible=True, status="fixture_equity"
        ),
    )


class Bus:
    def __init__(self, *, consumer=True):
        # Existing orchestration fixtures model an admitted local worker.
        self.callbacks = (
            {PROBE_REQUEST_EVENT: [lambda payload: None]} if consumer else {}
        )
        self.events = []

    def subscribe(self, event, callback):
        self.callbacks.setdefault(event, []).append(callback)

    def unsubscribe(self, event, callback):
        self.callbacks[event].remove(callback)

    def publish(self, event, payload):
        self.publish_with_dispatch_count(event, payload)

    def has_subscribers(self, event):
        return bool(self.callbacks.get(event))

    def consumer_readiness(self, event):
        return {"ready": self.has_subscribers(event), "reason": "fixture_ready"}

    def publish_with_dispatch_count(self, event, payload):
        self.events.append((event, payload))
        callbacks = list(self.callbacks.get(event, []))
        for callback in callbacks:
            callback(payload)
        return len(callbacks)


def _isolated_bus():
    from src.core.event_bus import EventBus

    class IsolatedBus(EventBus):
        _instance = None
        _lock = threading.Lock()

    return IsolatedBus()


def test_unchanged_dispatch_skips_durable_rewrite_but_changed_state_is_saved(
    tmp_path, monkeypatch
):
    from src.scanners import zero_base_discovery_runtime as module
    import json

    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(), session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    before = runtime.state_path.read_bytes()
    syncs = []
    monkeypatch.setattr(module.os, "fsync", lambda fd: syncs.append(fd))
    runtime.dispatch_due_probes(now_epoch=T0 + 2)
    assert syncs == []
    assert runtime.state_path.read_bytes() == before
    row = runtime.queue._candidates[("123456", "krx_nxt_integrated")]
    row.discovery_volume += 1
    runtime.dispatch_due_probes(now_epoch=T0 + 3)
    assert len(syncs) == 2
    assert (
        json.loads(runtime.state_path.read_bytes())["candidates"][0]["discovery_volume"]
        == row.discovery_volume
    )


def test_persist_skip_requires_same_file_generation(tmp_path, monkeypatch):
    from src.scanners import zero_base_discovery_runtime as module

    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(), session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    correct = runtime.state_path.read_bytes()
    runtime.state_path.unlink()
    runtime.state_path.write_bytes(b"{}")
    syncs = []
    monkeypatch.setattr(module.os, "fsync", lambda fd: syncs.append(fd))
    runtime.dispatch_due_probes(now_epoch=T0 + 2)
    assert len(syncs) == 2
    assert runtime.state_path.read_bytes() == correct


@pytest.mark.parametrize("fail_at", [1, 2])
def test_failed_fsync_never_primes_unchanged_state_cache(
    tmp_path, monkeypatch, fail_at
):
    from src.scanners import zero_base_discovery_runtime as module

    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(), session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    count = 0

    def fail_once(fd):
        nonlocal count
        count += 1
        if count == fail_at:
            raise OSError("fixture fsync failure")

    monkeypatch.setattr(module.os, "fsync", fail_once)
    with pytest.raises(OSError, match="fixture fsync failure"):
        runtime._persist()
    assert runtime._persisted_state is None
    assert not list(tmp_path.glob("*.tmp.*"))
    syncs = []
    monkeypatch.setattr(module.os, "fsync", lambda fd: syncs.append(fd))
    runtime._persist()
    assert len(syncs) == 2 and runtime._persisted_state is not None
    syncs.clear()
    runtime._persist()
    assert syncs == []


def test_missing_post_commit_generation_is_never_cached(tmp_path, monkeypatch):
    from src.scanners import zero_base_discovery_runtime as module

    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(), session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    syncs = []

    def removed_after_replace(fd):
        syncs.append(fd)
        if len(syncs) == 2:
            runtime.state_path.unlink()

    monkeypatch.setattr(module.os, "fsync", removed_after_replace)
    runtime._persist()
    assert runtime._persisted_state is None and not runtime.state_path.exists()
    monkeypatch.setattr(module.os, "fsync", lambda fd: syncs.append(fd))
    runtime._persist()
    assert runtime.state_path.exists() and len(syncs) == 4


def test_real_bus_startup_without_consumer_never_reserves_physical_capacity(tmp_path):
    bus = _isolated_bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    result = runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    assert (
        result["probe_requested_count"] == 0 and result["probe_consumer_ready"] is False
    )
    assert runtime.queue.in_flight_count() == 0
    assert runtime.queue.snapshot()["candidates"][0]["handoff_id"] == ""
    requests = []
    receiver = lambda payload: requests.append(payload)
    receiver.runtime_readiness = lambda: {"ready": True, "reason": "fixture_ready"}
    bus.subscribe(PROBE_REQUEST_EVENT, receiver)
    assert runtime.dispatch_due_probes(now_epoch=T0 + 2)["probe_requested_count"] == 1
    assert len(requests) == runtime.queue.in_flight_count() == 1


def test_consumer_disappearing_during_persist_closes_only_unstarted_claim(
    tmp_path, monkeypatch
):
    bus = _isolated_bus()
    receiver = lambda payload: pytest.fail("removed consumer ran")
    receiver.runtime_readiness = lambda: {"ready": True, "reason": "fixture_ready"}
    bus.subscribe(PROBE_REQUEST_EVENT, receiver)
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    persist = runtime._persist

    def remove_then_persist():
        bus.unsubscribe(PROBE_REQUEST_EVENT, receiver)
        persist()

    monkeypatch.setattr(runtime, "_persist", remove_then_persist)
    result = runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    assert (
        result["probe_requested_count"] == 0 and result["probe_no_consumer_count"] == 1
    )
    assert runtime.queue.in_flight_count() == 0
    row = runtime.queue.snapshot()["candidates"][0]
    assert row["lease_phase"] == "closed" and row["handoff_id"] == ""
    assert row["last_result"] == "probe_capacity_deferred"


def test_counted_publication_is_not_callback_success_or_order_authority(monkeypatch):
    from src.core import event_bus as module

    bus = _isolated_bus()
    errors = []
    monkeypatch.setattr(module, "log_error", errors.append)
    assert bus.publish_with_dispatch_count("event", {}) == 0

    def uncertain(payload):
        raise RuntimeError("callback started work then failed")

    bus.subscribe("event", uncertain)
    assert bus.publish_with_dispatch_count("event", {}) == 1
    assert bus.publish("event", {}) is None
    assert len(errors) == 2


def _panel(_token):
    return {
        "panels": [{"status": "observed_panel"}],
        "observations": [
            {
                "code": "123456",
                "route": "krx_nxt_integrated",
                "observed_epoch": T0,
                "source_sha256": "a" * 64,
                "source_scope": "observed_panel",
                "source_kind": "activity",
                "name": "TEST",
                "market": "KOSPI",
                "venue": "KRX",
                "price": 10000,
            }
        ],
    }


def _target_readiness(stamp, codes):
    owner = dict(
        runtime_generation="fixture",
        process_pid=123,
        process_start_ticks="456",
        date="2026-09-28",
    )
    return dict(
        ready=True,
        **owner,
        main_target_snapshot=dict(
            schema="zero_base_main_target_snapshot_v1",
            status="observed",
            **owner,
            generation="c" * 64,
            observed_epoch=stamp,
            active_codes=codes,
            runtime_effect=False,
        ),
    )


def test_active_target_snapshot_defers_before_claim_and_release_restores_admission(
    tmp_path,
):
    bus = Bus()
    readiness = _target_readiness(T0 + 1, ["123456"])
    bus.consumer_readiness = lambda event: readiness
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    summary = runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    assert summary["probe_requested_count"] == runtime.queue.in_flight_count() == 0
    assert summary["probe_claim_eligibility"]["active_target_deferred_count"] == 1
    assert runtime.queue.snapshot()["candidates"][0]["claim_count"] == 0
    readiness = _target_readiness(T0 + 2, [])
    assert runtime.dispatch_due_probes(now_epoch=T0 + 2)["probe_requested_count"] == 1


@pytest.mark.parametrize(
    "defect",
    [
        "stale",
        "future",
        "wrong_owner",
        "wrong_day",
        "invalid_code",
        "unknown",
        "unbounded",
    ],
)
def test_unproven_target_snapshot_falls_back_without_excluding_candidate(
    tmp_path, defect
):
    bus = Bus()
    readiness = _target_readiness(T0 + 1, ["123456"])
    snapshot = readiness["main_target_snapshot"]
    if defect == "stale":
        snapshot["observed_epoch"] -= 2.001
    if defect == "future":
        snapshot["observed_epoch"] += 0.001
    if defect == "wrong_owner":
        snapshot["process_start_ticks"] = "foreign"
    if defect == "wrong_day":
        snapshot["date"] = "2026-09-27"
    if defect == "invalid_code":
        snapshot["active_codes"] = ["invalid"]
    if defect == "unknown":
        snapshot["status"] = "unobserved"
    if defect == "unbounded":
        snapshot["active_codes"] = ["123456"] * 513
    bus.consumer_readiness = lambda event: readiness
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    summary = runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    assert summary["probe_requested_count"] == 1
    assert summary["probe_active_target_snapshot_status"] == "fallback"


@pytest.mark.parametrize(
    "defect",
    [
        "claim_clock",
        "claim_scope",
        "lease",
        "candidate",
        "action",
        "claim_shape",
        "code_shape",
        "action_shape",
        "ack_shape",
    ],
)
def test_invalid_result_cannot_occupy_exact_claim_inbox(tmp_path, defect):
    from copy import deepcopy

    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "queue.json"
    )
    runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    request = next(p for event, p in bus.events if event == PROBE_REQUEST_EVENT)
    valid = dict(
        request,
        result="assessed",
        machine_action="RECHECK",
        physical_probe_lease_id=request["claim"]["physical_probe_lease_id"],
    )
    invalid = deepcopy(valid)
    if defect == "claim_clock":
        invalid["claim"]["observed_epoch"] -= 1
    if defect == "claim_scope":
        invalid["claim"]["source_scope"] = "foreign"
    if defect == "lease":
        invalid["physical_probe_lease_id"] = "foreign"
    if defect == "candidate":
        invalid["candidate"] = {"code": "999999"}
    if defect == "action":
        invalid["machine_action"] = "INVALID"
    if defect == "claim_shape":
        invalid["claim"] = ["invalid"]
    if defect == "code_shape":
        invalid["claim"]["code"] = ["123456"]
    if defect == "action_shape":
        invalid["machine_action"] = {"value": "RECHECK"}
    if defect == "ack_shape":
        invalid["handoff_closed"] = 1
    bus.publish(PROBE_RESULT_EVENT, invalid)
    bus.publish(PROBE_RESULT_EVENT, valid)
    assert runtime.drain_results(now_epoch=T0 + 2) == [valid]
    assert runtime.queue.in_flight_count() == 1  # actual release ACK still required


@pytest.mark.parametrize("defect", ["lease", "claim_clock", "claim_scope"])
def test_wrong_ack_cannot_hide_real_release_ack(tmp_path, defect):
    from copy import deepcopy
    from src.scanners.zero_base_discovery_runtime import HANDOFF_ACK_EVENT

    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "queue.json"
    )
    runtime.scan_once("fixture", fetcher=_panel, now_epoch=T0 + 1)
    request = next(p for event, p in bus.events if event == PROBE_REQUEST_EVENT)
    valid = dict(
        handoff_closed=True,
        claim=request["claim"],
        ws_handoff_id=request["claim"]["physical_probe_lease_id"],
    )
    invalid = deepcopy(valid)
    if defect == "lease":
        invalid["ws_handoff_id"] = "foreign"
    if defect == "claim_clock":
        invalid["claim"]["observed_epoch"] -= 1
    if defect == "claim_scope":
        invalid["claim"]["source_scope"] = "foreign"
    bus.publish(HANDOFF_ACK_EVENT, invalid)
    bus.publish(HANDOFF_ACK_EVENT, valid)
    runtime.drain_results(now_epoch=T0 + 2)
    assert runtime.queue.in_flight_count() == 0


def test_claim_persist_failure_does_not_strand_unstarted_physical_lease(
    tmp_path, monkeypatch
):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    persist = runtime._persist
    monkeypatch.setattr(
        runtime, "_persist", lambda: (_ for _ in ()).throw(OSError("disk full"))
    )
    with pytest.raises(OSError):
        runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    assert runtime.queue.in_flight_count() == 0
    assert not bus.events
    monkeypatch.setattr(runtime, "_persist", persist)
    assert runtime.dispatch_due_probes(now_epoch=T0 + 2)["probe_requested_count"] == 1


@pytest.mark.parametrize("expired_after_persist", [False, True])
def test_result_persist_retry_is_once_and_original_native_deadline_bound(
    tmp_path, monkeypatch, expired_after_persist
):
    from src.engine.scalping import reversal_source_diagnostics as D
    from src.scanners.zero_base_discovery_runtime import HANDOFF_ACK_EVENT

    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    request = next(p for event, p in bus.events if event == PROBE_REQUEST_EVENT)
    expected = dict(
        snapshot=[{"epoch": T0}],
        deadline_epoch=T0 + 5,
        deadline_perf=time.perf_counter() + 5,
        observer_pid=D.os.getpid(),
        observer_start_ticks=D._PROCESS_START_TICKS,
    )
    result = dict(
        **request,
        result="assessed",
        machine_action="ENTER_NOW",
        machine_bundle_sha256="b" * 64,
        result_epoch=T0 + 2,
        native_observation=expected,
        physical_probe_lease_id=request["claim"]["physical_probe_lease_id"],
    )
    bus.publish(PROBE_RESULT_EVENT, result)
    persist = runtime._persist
    monkeypatch.setattr(
        runtime, "_persist", lambda: (_ for _ in ()).throw(OSError("disk full"))
    )
    with pytest.raises(OSError):
        runtime.drain_results(now_epoch=T0 + 2)
    assert not any(e == MACHINE_ENTER_EVENT for e, _ in bus.events)
    monkeypatch.setattr(runtime, "_persist", persist)
    runtime.drain_results(now_epoch=T0 + (6 if expired_after_persist else 3))
    runtime.drain_results(now_epoch=T0 + 4)
    assert sum(e == MACHINE_ENTER_EVENT for e, _ in bus.events) == int(
        not expired_after_persist
    )
    assert runtime.queue.in_flight_count() == 1
    ack = dict(
        handoff_closed=True,
        claim=request["claim"],
        ws_handoff_id=request["claim"]["physical_probe_lease_id"],
    )
    bus.publish(HANDOFF_ACK_EVENT, ack)
    bus.publish(HANDOFF_ACK_EVENT, ack)
    runtime.drain_results(now_epoch=T0 + 7)
    assert runtime.queue.in_flight_count() == 0


def test_pending_panel_transport_does_not_block_result_control_thread(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    request = next(p for event, p in bus.events if event == PROBE_REQUEST_EVENT)
    started, finish = threading.Event(), threading.Event()

    def slow(_):
        started.set()
        finish.wait(2)
        return dict(panels=[], observations=[])

    try:
        assert runtime.start_scan("token", fetcher=slow) and started.wait(1)
        bus.publish(
            PROBE_RESULT_EVENT,
            dict(**request, result="assessed", machine_action="RECHECK"),
        )
        assert len(runtime.drain_results(now_epoch=T0 + 2)) == 1
        assert not runtime._panel_future.done()
    finally:
        finish.set()
        runtime.close()


def test_runtime_durable_claim_machine_enter_and_late_result_rejection(tmp_path):
    bus = Bus()
    state = tmp_path / "2026-09-28.json"
    claim_receipts = []
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=state,
        claim_receipt_emitter=lambda *args, **kwargs: claim_receipts.append(
            (args, kwargs)
        ),
    )
    panel = _panel("token")
    panel["observations"][0]["volume"] = 12345
    summary = runtime.scan_once("token", fetcher=lambda _token: panel, now_epoch=T0 + 1)
    assert summary["probe_requested_count"] == 1
    request = next(
        payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT
    )
    assert state.exists()
    assert request["claim"]["source_kind"] == "activity"
    assert claim_receipts[0][0] == ("zero_base_probe_claim",)
    assert claim_receipts[0][1]["fields"]["zero_base_source_sha256"] == "a" * 64
    assert (
        claim_receipts[0][1]["fields"]["zero_base_discovery_volume"]
        == request["claim"]["discovery_volume"]
    )
    assert claim_receipts[0][1]["fields"]["zero_base_discovery_volume"] == 12345
    assert claim_receipts[0][1]["fields"]["zero_base_source_kind"] == "activity"
    assert (
        claim_receipts[0][1]["fields"]["physical_probe_lease_id"]
        == request["claim"]["physical_probe_lease_id"]
    )

    bus.publish(
        PROBE_RESULT_EVENT,
        {
            **request,
            "result": "assessed",
            "machine_action": "ENTER_NOW",
            "machine_bundle_sha256": "b" * 64,
            "result_epoch": T0 + 2,
        },
    )
    accepted = runtime.drain_results(now_epoch=T0 + 3)
    assert len(accepted) == 1
    assert [event for event, _ in bus.events].count(MACHINE_ENTER_EVENT) == 1

    bus.publish(
        PROBE_RESULT_EVENT,
        {
            **request,
            "result": "assessed",
            "machine_action": "ENTER_NOW",
            "machine_bundle_sha256": "b" * 64,
            "result_epoch": T0 + 2,
        },
    )
    assert runtime.drain_results(now_epoch=T0 + 4) == []
    assert [event for event, _ in bus.events].count(MACHINE_ENTER_EVENT) == 1
    restored = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(), session_date="2026-09-28", state_path=state
    )
    assert len(restored.queue.snapshot()["candidates"]) == 1
    assert restored.queue.snapshot()["candidates"][0]["source_kind"] == "activity"


def test_new_discovery_does_not_drop_running_probe_result(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=tmp_path / "state.json",
    )
    runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    request = next(
        payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT
    )
    newer = _panel("token")
    newer["observations"][0] = {
        **newer["observations"][0],
        "observed_epoch": T0 + 2,
        "source_sha256": "c" * 64,
    }
    repeat = runtime.scan_once("token", fetcher=lambda _token: newer, now_epoch=T0 + 3)
    assert repeat["observed_new_generation_count"] == 1
    assert repeat["probe_requested_count"] == 0
    bus.publish(
        PROBE_RESULT_EVENT,
        {
            **request,
            "result": "assessed",
            "machine_action": "RECHECK",
            "result_epoch": T0 + 4,
        },
    )
    assert len(runtime.drain_results(now_epoch=T0 + 4)) == 1
    assert runtime.queue.snapshot()["candidates"][0]["source_sha256"] == "c" * 64
    assert runtime.dispatch_due_probes(now_epoch=T0 + 7)["probe_requested_count"] == 1
    assert [
        payload["claim"]["source_sha256"]
        for event, payload in bus.events
        if event == PROBE_REQUEST_EVENT
    ][-1] == "c" * 64


def test_lost_probe_is_reclaimed_but_old_enter_cannot_promote(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=tmp_path / "state.json",
    )
    runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    first = next(
        payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT
    )
    summary = runtime.scan_once(
        "token",
        fetcher=lambda _token: {"panels": [], "observations": []},
        now_epoch=first["claim"]["residence_deadline_epoch"] + 1,
    )
    assert summary["probe_timeout_count"] == 1
    bus.publish(
        PROBE_RESULT_EVENT,
        {
            **first,
            "result": "assessed",
            "machine_action": "ENTER_NOW",
            "machine_bundle_sha256": "b" * 64,
            "result_epoch": T0 + 22,
        },
    )
    assert runtime.drain_results(now_epoch=T0 + 23) == []
    assert all(event != MACHINE_ENTER_EVENT for event, _ in bus.events)


def test_panel_interval_does_not_limit_probe_dispatch_and_stale_rows_wait(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=tmp_path / "state.json",
    )
    panel = {
        "panels": [{"status": "observed_panel"}],
        "observations": [
            {
                "code": f"{code:06d}",
                "route": "krx_nxt_integrated",
                "observed_epoch": T0,
                "source_sha256": "a" * 64,
                "source_scope": "observed_panel",
                "name": "TEST",
                "market": "KOSPI",
                "venue": "KRX",
                "price": 10000,
            }
            for code in range(1, 14)
        ],
    }
    first = runtime.scan_once("token", fetcher=lambda _token: panel, now_epoch=T0 + 1)
    assert first["probe_requested_count"] == MAX_CONCURRENT_PROBES == 5
    assert first["probe_capacity_limit"] == 5
    assert first["probe_claims_in_flight_count"] == 5
    assert runtime.queue.in_flight_count() == 5
    second = runtime.dispatch_due_probes(now_epoch=T0 + 11)
    assert second["probe_requested_count"] == 0
    assert second["probe_claims_in_flight_count"] == 5
    first_requests = [
        payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT
    ]
    for request in first_requests[:2]:
        bus.publish(
            PROBE_RESULT_EVENT,
            {
                **request,
                "result": "source_unavailable",
                "reason": "route_snapshot_missing",
            },
        )
    assert len(runtime.drain_results(now_epoch=T0 + 12)) == 2
    assert runtime.dispatch_due_probes(now_epoch=T0 + 13)["probe_requested_count"] == 2
    assert runtime.queue.in_flight_count() == 5
    stale = runtime.dispatch_due_probes(now_epoch=T0 + 121)
    assert stale["probe_requested_count"] == 0
    assert stale["stale_candidate_count"] == 13


def test_aftermarket_dispatch_uses_activity_rotation_without_dropping_gainers(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=tmp_path / "state.json",
    )
    after = datetime(2026, 9, 28, 18, 30, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    observations = [
        {
            **_panel("token")["observations"][0],
            "code": f"{code:06d}",
            "observed_epoch": after,
            "source_kind": "activity" if code <= 12 else "gainers",
        }
        for code in range(1, 17)
    ]
    summary = runtime.scan_once(
        "token",
        fetcher=lambda _token: {"panels": [], "observations": observations},
        now_epoch=after + 1,
    )
    assert summary["probe_requested_count"] == 5
    kinds = [
        payload["claim"]["source_kind"]
        for event, payload in bus.events
        if event == PROBE_REQUEST_EVENT
    ]
    assert kinds == ["activity"] * 5
    for request in [
        payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT
    ]:
        bus.publish(
            PROBE_RESULT_EVENT,
            {
                **request,
                "result": "source_unavailable",
                "reason": "route_snapshot_missing",
            },
        )
    assert len(runtime.drain_results(now_epoch=after + 2)) == 5
    assert (
        runtime.dispatch_due_probes(now_epoch=after + 3)["probe_requested_count"] == 5
    )
    kinds = [
        payload["claim"]["source_kind"]
        for event, payload in bus.events
        if event == PROBE_REQUEST_EVENT
    ]
    assert kinds == ["activity"] * 7 + ["gainers"] + ["activity"] * 2


def test_session_handoff_does_not_claim_premarket_route_in_regular_session(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=tmp_path / "state.json",
    )
    premarket = datetime(
        2026, 9, 28, 8, 59, 30, tzinfo=ZoneInfo("Asia/Seoul")
    ).timestamp()
    regular = datetime(2026, 9, 28, 9, 0, 30, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    runtime.queue.observe(
        code="123456",
        route="nxt_only",
        observed_epoch=premarket,
        source_sha256="a" * 64,
        source_scope="observed_panel",
        received_epoch=premarket,
        market="KOSPI",
        venue="NXT",
    )
    assert runtime.dispatch_due_probes(now_epoch=regular)["probe_requested_count"] == 0
    assert all(event != PROBE_REQUEST_EVENT for event, _payload in bus.events)


def test_enabled_scanner_enters_new_owner_without_legacy_radar(monkeypatch):
    from src.scanners import scalping_scanner as scanner

    bus = Bus()
    called = []
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
    monkeypatch.setattr(scanner, "DBManager", lambda: object())
    monkeypatch.setattr(scanner, "EventBus", lambda: bus)
    monkeypatch.setattr(scanner.kiwoom_utils, "get_kiwoom_token", lambda: "token")
    monkeypatch.setattr(
        scanner,
        "SniperRadar",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("legacy radar constructed")
        ),
    )
    monkeypatch.setattr(
        scanner,
        "run_zero_base_scanner",
        lambda **kwargs: called.append(kwargs),
    )
    scanner.run_scalper(is_test_mode=True)
    assert called == [{"token": "token", "event_bus": bus, "is_test_mode": True}]


@pytest.mark.parametrize(
    "release,active,expected",
    [(True, True, [0, 1]), (False, True, [0]), (True, False, [])],
)
def test_physical_release_reuses_normal_dispatch_without_poll_delay(
    monkeypatch, tmp_path, release, active, expected
):
    from collections import defaultdict
    from src.scanners import scalping_scanner as scanner
    from src.engine.error_detectors import process_health

    class StopScanner(Exception):
        pass

    clock = [
        datetime(2026, 10, 28, 8, 7, 31, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    ]
    initial = clock[0]
    calls = []

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromtimestamp(clock[0], tz=tz)

    class Queue:
        session_date = "2026-10-28"
        count = 5

        def in_flight_count(self):
            return self.count

    class Runtime:
        def __init__(self, **kwargs):
            self.queue, self.drains, self.waits = Queue(), 0, 0

        def drain_results(self):
            self.drains += 1
            if self.drains == 2 and release:
                self.queue.count -= 1
            return []

        def start_scan(self, token):
            return False

        def finish_scan(self):
            return None

        def dispatch_due_probes(self):
            calls.append(int(clock[0] - initial))
            return defaultdict(lambda: 0)

        def wait(self, seconds):
            self.waits += 1
            if self.waits == 2:
                raise StopScanner()
            clock[0] += 1

    monkeypatch.setattr(scanner, "ZeroBaseDiscoveryRuntime", Runtime)
    monkeypatch.setattr(scanner, "datetime", Clock)
    monkeypatch.setattr(scanner.time, "time", lambda: clock[0])
    monkeypatch.setattr(scanner, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        scanner, "_active_scalping_buy_window", lambda now: "PRE" if active else None
    )
    monkeypatch.setattr(scanner, "_zero_base_log_event", lambda *a, **kw: None)
    monkeypatch.setattr(process_health, "write_heartbeat", lambda *a: None)
    with pytest.raises(StopScanner):
        scanner.run_zero_base_scanner(token="offline", event_bus=Bus())
    assert calls == expected


def test_scanner_emits_failed_probe_identity_and_artifact_cause(monkeypatch, tmp_path):
    import pytest
    from src.scanners import scalping_scanner as scanner
    from src.engine.error_detectors import process_health

    class StopScanner(Exception):
        pass

    result = {
        "claim": {"code": "058610", "route": "krx_nxt_integrated"},
        "candidate": {},
        "result": "required_feature_insufficient",
        "reason": "source_quality_blocked_before_assessment",
        "machine_source_gap_kind": "runtime_preflight_artifact_not_ready",
        "machine_evaluation_status": "source_quality_blocked_before_assessment",
        "machine_preflight_artifact_status": "artifact_missing",
        "evaluation_attempt_id": "machine-source-invalid-exact",
        "provider_called": False,
        "continuous_reversal_rejected_claim_receipt": {"sha256": "exact-proof"},
        "machine_capture_status": "captured",
        "machine_observation_sha256": "a" * 64,
        "ws_source_trace": {
            "lease": {
                "collector_result_counts_by_type": {
                    "0D": {"enqueued": 10, "invalid_depth_snapshot": 2, "queue_full": 1}
                }
            }
        },
        "machine_input_trace": {
            "entry_machine_input_as_of": 11,
            "entry_machine_input_preparation_ms": 0,
            "entry_machine_input_preparation_stages_ms": {"policy_resolve_ms": 1.5},
        },
    }
    emitted = []
    monkeypatch.setattr(
        scanner,
        "ZeroBaseDiscoveryRuntime",
        lambda **_kwargs: type(
            "Runtime",
            (),
            {
                "queue": type("Queue", (), {"in_flight_count": lambda self: 0})(),
                "drain_results": lambda self: [result],
                "finish_scan": lambda self: None,
                "wait": lambda self, seconds: (_ for _ in ()).throw(StopScanner()),
            },
        )(),
    )
    monkeypatch.setattr(scanner, "DATA_DIR", tmp_path)
    monkeypatch.setattr(scanner, "_active_scalping_buy_window", lambda _now: None)
    monkeypatch.setattr(process_health, "write_heartbeat", lambda _name: None)
    monkeypatch.setattr(
        scanner,
        "_zero_base_log_event",
        lambda stage, **kwargs: emitted.append((stage, kwargs)),
    )
    monkeypatch.setattr(
        scanner.time, "sleep", lambda _seconds: (_ for _ in ()).throw(StopScanner())
    )
    with pytest.raises(StopScanner):
        scanner.run_zero_base_scanner(token="token", event_bus=Bus())
    assert len(emitted) == 1
    stage, payload = emitted[0]
    assert stage == "zero_base_probe_result" and payload["code"] == "058610"
    assert payload["fields"]["evaluation_attempt_id"] == result["evaluation_attempt_id"]
    assert (
        payload["fields"]["zero_base_machine_source_gap_kind"]
        == "runtime_preflight_artifact_not_ready"
    )
    assert (
        payload["fields"]["zero_base_machine_preflight_artifact_status"]
        == "artifact_missing"
    )
    assert (
        payload["fields"]["zero_base_machine_input_trace"]
        == result["machine_input_trace"]
    )
    assert payload["fields"]["provider_called"] is False
    assert (
        payload["fields"]["continuous_reversal_rejected_claim_receipt"]
        == result["continuous_reversal_rejected_claim_receipt"]
    )
    assert payload["fields"]["machine_observation_sha256"] == "a" * 64
    assert payload["fields"]["zero_base_ws_source_trace"] == result["ws_source_trace"]

    result.update(
        result="source_unavailable",
        evaluation_attempt_id=None,
        machine_evaluation_status=None,
        machine_preflight_artifact_status=None,
    )
    emitted.clear()
    with pytest.raises(StopScanner):
        scanner.run_zero_base_scanner(token="token", event_bus=Bus())
    fields = emitted[0][1]["fields"]
    assert fields["evaluation_attempt_id"] == "-"
    assert fields["zero_base_machine_evaluation_status"] == "-"
    assert fields["zero_base_machine_preflight_artifact_status"] == "-"


@pytest.mark.parametrize("frozen_clock", [False, True])
def test_live_callback_snapshot_uses_completion_clock_without_renewing_claim_deadline(
    tmp_path, monkeypatch, frozen_clock
):
    from src.scanners import zero_base_discovery_runtime as module
    from src.engine import kiwoom_sniper_v2 as main

    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    runtime.queue.observe(
        **{
            k: v
            for k, v in dict(
                code="123456",
                route="krx_nxt_integrated",
                observed_epoch=T0,
                source_sha256="a" * 64,
                source_scope="observed_panel",
                received_epoch=T0,
            ).items()
        }
    )
    epoch = [T0 + 1]
    perf = [100.0]
    monkeypatch.setattr(module.time, "time", lambda: epoch[0])
    monkeypatch.setattr(module.time, "perf_counter", lambda: perf[0])
    monkeypatch.setattr(
        main, "ACTIVE_TARGETS", [{"code": "123456", "id": 1, "status": "WATCHING"}]
    )

    def readiness(_event):
        epoch[0] += 0.05
        perf[0] += 0.05
        receipt = _target_readiness(epoch[0], ["123456"])
        receipt["main_target_snapshot"] = main._zero_base_active_target_snapshot(
            receipt
        )
        return receipt

    bus.consumer_readiness = readiness
    summary = runtime.dispatch_due_probes(
        **({"now_epoch": T0 + 1} if frozen_clock else {})
    )
    assert summary["probe_requested_count"] == 0
    assert summary["probe_active_target_snapshot_status"] == "observed"
    assert summary["probe_claim_eligibility"]["active_target_deferred_count"] == 1
    bus.consumer_readiness = lambda event: _target_readiness(epoch[0], [])
    next_boundary = epoch[0]
    summary = runtime.dispatch_due_probes(
        **({"now_epoch": next_boundary} if frozen_clock else {})
    )
    request = next(
        payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT
    )
    assert request["claim"]["last_claim_epoch"] == next_boundary
    assert request["claim"]["residence_deadline_epoch"] == next_boundary + 60


@pytest.mark.parametrize("panel_finished", [False, True])
def test_scanner_publishes_scheduler_diagnostics_in_both_cycle_paths(
    monkeypatch, tmp_path, panel_finished
):
    from src.scanners import scalping_scanner as scanner
    from src.engine.error_detectors import process_health

    class StopScanner(Exception):
        pass

    summary = dict(
        probe_requested_count=0,
        probe_consumer_ready=True,
        probe_no_consumer_count=0,
        probe_capacity_limit=5,
        probe_claims_in_flight_count=3,
        probe_timeout_count=0,
        stale_candidate_count=10,
        queue_count=20,
        probe_claim_eligibility={
            "eligible_due_count": 7,
            "eligible_due_wait_max_seconds": 40,
        },
        probe_residence_deferred={"long_slot_wait": 7},
        probe_active_target_snapshot_status="observed",
        probe_active_target_snapshot_generation="a" * 64,
        queue_restored_candidate_count=18,
        observed_new_generation_count=2,
        panels=[],
    )

    class Runtime:
        def __init__(self, **kwargs):
            self.queue = type("Queue", (), {"in_flight_count": lambda self: 0})()

        def drain_results(self):
            return []

        def start_scan(self, token):
            return False

        def finish_scan(self):
            return summary if panel_finished else None

        def dispatch_due_probes(self):
            return summary

        def wait(self, seconds):
            raise StopScanner()

    emitted = []
    monkeypatch.setattr(scanner, "ZeroBaseDiscoveryRuntime", Runtime)
    monkeypatch.setattr(scanner, "DATA_DIR", tmp_path)
    monkeypatch.setattr(process_health, "write_heartbeat", lambda *a: None)
    monkeypatch.setattr(
        scanner, "_zero_base_log_event", lambda stage, **kw: emitted.append((stage, kw))
    )
    with pytest.raises(StopScanner):
        scanner.run_zero_base_scanner(
            token="offline", event_bus=Bus(), is_test_mode=True
        )
    stage, payload = emitted[0]
    assert stage == (
        "zero_base_discovery_cycle"
        if panel_finished
        else "zero_base_probe_dispatch_cycle"
    )
    for key in [
        "probe_claim_eligibility",
        "probe_residence_deferred",
        "probe_active_target_snapshot_status",
        "probe_active_target_snapshot_generation",
        "queue_restored_candidate_count",
    ]:
        assert payload["fields"]["zero_base_" + key] == summary[key]


def test_restored_queue_product_rejection_never_dispatches_or_consumes_capacity(
    tmp_path, monkeypatch
):
    from src.scanners import zero_base_discovery_runtime as R

    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    runtime.queue.observe(
        code="487130",
        route="krx_nxt_integrated",
        observed_epoch=T0,
        source_sha256="a" * 64,
        source_scope="observed_panel",
        received_epoch=T0,
        name="Unlisted Brand",
        market="KOSPI",
    )
    runtime._persist()
    runtime.close()
    restored = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "q.json"
    )
    monkeypatch.setattr(
        R,
        "discovery_product_filter",
        lambda *a: lambda *args: dict(
            eligible=False, status="verified_non_common_stock"
        ),
    )
    before = len(bus.events)
    result = restored.dispatch_due_probes(now_epoch=T0 + 2)
    assert (
        result["probe_requested_count"] == 0 and restored.queue.in_flight_count() == 0
    )
    assert restored.queue._candidates[("487130", "krx_nxt_integrated")].claim_count == 0
    assert not [e for e in bus.events[before:] if e[0] == PROBE_REQUEST_EVENT]


def test_admission_deltas_are_bounded_resume_and_reach_existing_census(
    tmp_path, monkeypatch
):
    import json
    from src.scanners import scanner_source_census as source
    from src.engine.monitoring import market_opportunity_census as census

    monkeypatch.setattr(source, "MAX_ROWS", 1)
    bus = Bus(consumer=False)
    emitted = []

    def emit(stage, **kw):
        if stage == "zero_base_probe_admission":
            emitted.append(kw["fields"])
            return {"structured_append_succeeded": True}

    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus,
        session_date="2026-09-28",
        state_path=tmp_path / "q.json",
        claim_receipt_emitter=emit,
    )
    for code in ("123450", "123460"):
        runtime.queue.observe(
            code=code,
            route="krx_nxt_integrated",
            observed_epoch=T0,
            received_epoch=T0,
            source_sha256="a" * 64,
            source_scope="observed_panel",
        )
    for t in (T0 + 1, T0 + 2, T0 + 3):
        runtime.dispatch_due_probes(now_epoch=t)
    assert len(emitted) == 2
    records = [r for f in emitted for r in json.loads(f["zero_base_admission_records"])]
    assert [r["code"] for r in records] == ["123450", "123460"]
    assert emitted[0]["zero_base_admission_pending_count"] == 1
    assert emitted[1]["zero_base_admission_pending_count"] == 0
    assert not bus.events and not runtime.queue.in_flight_count()
    path = tmp_path / "pipeline.jsonl"
    path.write_text(
        "".join(
            json.dumps(
                dict(
                    pipeline="ENTRY_PIPELINE",
                    stage="zero_base_probe_admission",
                    emitted_at=datetime.fromtimestamp(
                        T0 + 10, ZoneInfo("Asia/Seoul")
                    ).isoformat(),
                    fields=f,
                )
            )
            + "\n"
            for f in emitted
        )
    )
    summary = {}
    index = census._load_stage_index(
        path,
        tmp_path / "absent-ai.jsonl",
        target_date="2026-09-28",
        zero_base_source_census=summary,
    )
    assert summary["admission_observation_count"] == 2
    assert (
        summary["valid_claim_count"] == summary["confirmed_watch_admission_count"] == 0
    )
    assert index["123450"]["zero_base_admission"][0]["reason"] == "eligible_due"
    rank = index["123450"]["zero_base_admission"][0]["preclaim_rank"]
    assert rank["claim_count"] == 0 and rank["last_claim_epoch"] == 0
    assert rank["first_seen_epoch"] == T0
    assert rank["eligible_since_epoch"] == T0 + 1
    assert emitted[0]["zero_base_admission_claim_sequence_before"] == 0
    assert not index["123450"].get("source_seen")


def test_claimed_rank_receipt_preserves_preclaim_state_and_retries_changes(tmp_path):
    import json

    emitted = []
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(), session_date="2026-09-28", state_path=tmp_path / "q.json",
        claim_receipt_emitter=lambda stage, **kw: (
            emitted.append(kw["fields"]) or {"structured_append_succeeded": True}
        ) if stage == "zero_base_probe_admission" else None,
    )
    runtime.queue.observe(
        code="123450", route="krx_nxt_integrated", observed_epoch=T0,
        received_epoch=T0, source_sha256="a" * 64, source_scope="observed_panel",
        discovery_volume=42, source_kind="activity", market="KOSPI",
    )
    assert runtime.dispatch_due_probes(now_epoch=T0 + 1)["probe_requested_count"] == 1
    row = json.loads(emitted[-1]["zero_base_admission_records"])[0]
    assert row["reason"] == "claimed" and row["claim_count"] == 1
    assert row["preclaim_rank"]["claim_count"] == 0
    assert row["preclaim_rank"]["last_claim_epoch"] == 0
    assert row["preclaim_rank"]["eligible_since_epoch"] == T0 + 1
    assert row["preclaim_rank"]["discovery_volume"] == 42
    runtime.dispatch_due_probes(now_epoch=T0 + 2)
    assert json.loads(emitted[-1]["zero_base_admission_records"])[0]["preclaim_rank"]["eligible_since_epoch"] is None
    count = len(emitted)
    runtime.queue._candidates[("123450", "krx_nxt_integrated")].discovery_volume = 43
    runtime.dispatch_due_probes(now_epoch=T0 + 3)
    assert len(emitted) == count + 1
    assert json.loads(emitted[-1]["zero_base_admission_records"])[0]["preclaim_rank"]["discovery_volume"] == 43


def test_admission_emit_failure_preserves_claims_and_pending_diagnostic(tmp_path):
    emitted = []

    def emit(stage, **kw):
        if stage == "zero_base_probe_admission":
            emitted.append(stage)
            raise OSError("fixture writer failure")

    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(consumer=False),
        session_date="2026-09-28",
        state_path=tmp_path / "q.json",
        claim_receipt_emitter=emit,
    )
    runtime.scan_once("offline", fetcher=_panel, now_epoch=T0 + 1)
    result = runtime.dispatch_due_probes(now_epoch=T0 + 2)
    assert result["probe_admission_diagnostic_status"] == "emit_failed:OSError"
    assert len(emitted) == 2 and not runtime._admission_emitted
    assert runtime.queue.in_flight_count() == 0


@pytest.mark.parametrize("outcome", [None, {}, {"structured_append_succeeded": False}])
def test_unconfirmed_admission_append_remains_pending(tmp_path, outcome):
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(consumer=False),
        session_date="2026-09-28",
        state_path=tmp_path / "q.json",
        claim_receipt_emitter=lambda *a, **k: outcome,
    )
    runtime.scan_once("offline", fetcher=_panel, now_epoch=T0 + 1)
    assert not runtime._admission_emitted
    result = runtime.dispatch_due_probes(now_epoch=T0 + 2)
    assert result["probe_admission_diagnostic_status"] == "append_unconfirmed"
    assert not runtime._admission_emitted and runtime.queue.in_flight_count() == 0


def test_full_admission_page_native_logger_reaches_census_after_append_retry(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace
    from src.utils import pipeline_event_logger as logger
    from src.scanners import scalping_scanner as scanner
    from src.scanners.scanner_source_census import MAX_ROWS
    from src.engine.monitoring import market_opportunity_census as census

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            value = datetime.fromtimestamp(T0 + 3, ZoneInfo("Asia/Seoul"))
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)

    logger._flush_producer_summary_at_exit()
    monkeypatch.setattr(logger, "_PRODUCER_COMPACTOR", None)
    monkeypatch.setattr(logger, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(logger, "datetime", Clock)
    monkeypatch.setattr(
        logger,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(
        logger, "log_info", lambda *a, **k: pytest.fail("diagnostic INFO")
    )
    monkeypatch.setattr(logger, "log_error", lambda *a, **k: None)
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=Bus(consumer=False),
        session_date="2026-09-28",
        state_path=tmp_path / "q.json",
        claim_receipt_emitter=scanner._zero_base_log_event,
    )
    for n in range(MAX_ROWS):
        runtime.queue.observe(
            code=str(123000 + n),
            route="krx_nxt_integrated",
            observed_epoch=T0,
            received_epoch=T0,
            source_sha256="a" * 64,
            source_scope="observed_panel",
        )
    append = logger._append_pipeline_event_jsonl

    def fail_append(*a, **kw):
        raise OSError("offline failed append")

    monkeypatch.setattr(logger, "_append_pipeline_event_jsonl", fail_append)
    assert (
        runtime.dispatch_due_probes(now_epoch=T0 + 1)[
            "probe_admission_diagnostic_status"
        ]
        == "append_unconfirmed"
    )
    assert not runtime._admission_emitted
    monkeypatch.setattr(logger, "_append_pipeline_event_jsonl", append)
    assert (
        runtime.dispatch_due_probes(now_epoch=T0 + 2)[
            "probe_admission_diagnostic_status"
        ]
        == "emitted"
    )
    path = logger._event_path("2026-09-28")
    summary = {}
    index = census._load_stage_index(
        path,
        tmp_path / "absent.jsonl",
        target_date="2026-09-28",
        zero_base_source_census=summary,
    )
    assert len(index) == summary["admission_observation_count"] == MAX_ROWS
    assert all(
        len(index[str(123000 + n)]["zero_base_admission"]) == 1 for n in range(MAX_ROWS)
    )
    assert (
        summary["valid_claim_count"] == summary["confirmed_watch_admission_count"] == 0
    )
    assert not runtime.queue.in_flight_count()
    logger._flush_producer_summary_at_exit()
