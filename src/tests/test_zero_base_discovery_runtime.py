from datetime import datetime
from zoneinfo import ZoneInfo

from src.scanners.zero_base_discovery_runtime import (
    MAX_CONCURRENT_PROBES,
    MACHINE_ENTER_EVENT,
    PROBE_REQUEST_EVENT,
    PROBE_RESULT_EVENT,
    ZeroBaseDiscoveryRuntime,
)


T0 = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()


class Bus:
    def __init__(self):
        self.callbacks = {}
        self.events = []

    def subscribe(self, event, callback):
        self.callbacks.setdefault(event, []).append(callback)

    def publish(self, event, payload):
        self.events.append((event, payload))
        for callback in self.callbacks.get(event, []):
            callback(payload)


def _panel(_token):
    return {"panels": [{"status": "observed_panel"}], "observations": [{
        "code": "123456", "route": "krx_nxt_integrated", "observed_epoch": T0,
        "source_sha256": "a" * 64, "source_scope": "observed_panel",
        "source_kind": "activity",
        "name": "TEST", "market": "KOSPI", "venue": "KRX", "price": 10000,
    }]}


def test_runtime_durable_claim_machine_enter_and_late_result_rejection(tmp_path):
    bus = Bus()
    state = tmp_path / "2026-09-28.json"
    claim_receipts = []
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=state,
        claim_receipt_emitter=lambda *args, **kwargs: claim_receipts.append((args, kwargs)),
    )
    summary = runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    assert summary["probe_requested_count"] == 1
    request = next(payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT)
    assert state.exists()
    assert request["claim"]["source_kind"] == "activity"
    assert claim_receipts[0][0] == ("zero_base_probe_claim",)
    assert claim_receipts[0][1]["fields"]["zero_base_source_sha256"] == "a" * 64

    bus.publish(PROBE_RESULT_EVENT, {
        **request, "result": "assessed", "machine_action": "ENTER_NOW",
        "machine_bundle_sha256": "b" * 64, "result_epoch": T0 + 2,
    })
    accepted = runtime.drain_results(now_epoch=T0 + 3)
    assert len(accepted) == 1
    assert [event for event, _ in bus.events].count(MACHINE_ENTER_EVENT) == 1

    bus.publish(PROBE_RESULT_EVENT, {
        **request, "result": "assessed", "machine_action": "ENTER_NOW",
        "machine_bundle_sha256": "b" * 64, "result_epoch": T0 + 2,
    })
    assert runtime.drain_results(now_epoch=T0 + 4) == []
    assert [event for event, _ in bus.events].count(MACHINE_ENTER_EVENT) == 1
    restored = ZeroBaseDiscoveryRuntime(event_bus=Bus(), session_date="2026-09-28", state_path=state)
    assert len(restored.queue.snapshot()["candidates"]) == 1
    assert restored.queue.snapshot()["candidates"][0]["source_kind"] == "activity"


def test_new_discovery_does_not_drop_running_probe_result(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "state.json",
    )
    runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    request = next(payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT)
    newer = _panel("token")
    newer["observations"][0] = {
        **newer["observations"][0],
        "observed_epoch": T0 + 2,
        "source_sha256": "c" * 64,
    }
    repeat = runtime.scan_once("token", fetcher=lambda _token: newer, now_epoch=T0 + 3)
    assert repeat["observed_new_generation_count"] == 1
    assert repeat["probe_requested_count"] == 0
    bus.publish(PROBE_RESULT_EVENT, {
        **request, "result": "assessed", "machine_action": "RECHECK",
        "result_epoch": T0 + 4,
    })
    assert len(runtime.drain_results(now_epoch=T0 + 4)) == 1
    assert runtime.queue.snapshot()["candidates"][0]["source_sha256"] == "c" * 64
    assert runtime.dispatch_due_probes(now_epoch=T0 + 7)["probe_requested_count"] == 1
    assert [payload["claim"]["source_sha256"] for event, payload in bus.events
            if event == PROBE_REQUEST_EVENT][-1] == "c" * 64


def test_lost_probe_is_reclaimed_but_old_enter_cannot_promote(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "state.json",
    )
    runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    first = next(payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT)
    summary = runtime.scan_once("token", fetcher=lambda _token: {"panels": [], "observations": []}, now_epoch=T0 + 62)
    assert summary["probe_timeout_count"] == 1
    bus.publish(PROBE_RESULT_EVENT, {
        **first, "result": "assessed", "machine_action": "ENTER_NOW",
        "machine_bundle_sha256": "b" * 64, "result_epoch": T0 + 22,
    })
    assert runtime.drain_results(now_epoch=T0 + 23) == []
    assert all(event != MACHINE_ENTER_EVENT for event, _ in bus.events)


def test_panel_interval_does_not_limit_probe_dispatch_and_stale_rows_wait(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "state.json",
    )
    panel = {"panels": [{"status": "observed_panel"}], "observations": [
        {
            "code": f"{code:06d}", "route": "krx_nxt_integrated", "observed_epoch": T0,
            "source_sha256": "a" * 64, "source_scope": "observed_panel",
            "name": "TEST", "market": "KOSPI", "venue": "KRX", "price": 10000,
        }
        for code in range(1, 14)
    ]}
    first = runtime.scan_once("token", fetcher=lambda _token: panel, now_epoch=T0 + 1)
    assert first["probe_requested_count"] == MAX_CONCURRENT_PROBES == 5
    assert first["probe_capacity_limit"] == 5
    assert first["probe_claims_in_flight_count"] == 5
    assert runtime.queue.in_flight_count() == 5
    second = runtime.dispatch_due_probes(now_epoch=T0 + 11)
    assert second["probe_requested_count"] == 0
    assert second["probe_claims_in_flight_count"] == 5
    first_requests = [payload for event, payload in bus.events
                      if event == PROBE_REQUEST_EVENT]
    for request in first_requests[:2]:
        bus.publish(PROBE_RESULT_EVENT, {
            **request, "result": "source_unavailable",
            "reason": "route_snapshot_missing",
        })
    assert len(runtime.drain_results(now_epoch=T0 + 12)) == 2
    assert runtime.dispatch_due_probes(now_epoch=T0 + 13)["probe_requested_count"] == 2
    assert runtime.queue.in_flight_count() == 5
    stale = runtime.dispatch_due_probes(now_epoch=T0 + 121)
    assert stale["probe_requested_count"] == 0
    assert stale["stale_candidate_count"] == 13


def test_aftermarket_dispatch_uses_activity_rotation_without_dropping_gainers(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "state.json",
    )
    after = datetime(2026, 9, 28, 18, 30, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    observations = [
        {
            **_panel("token")["observations"][0],
            "code": f"{code:06d}", "observed_epoch": after,
            "source_kind": "activity" if code <= 12 else "gainers",
        }
        for code in range(1, 17)
    ]
    summary = runtime.scan_once(
        "token", fetcher=lambda _token: {"panels": [], "observations": observations},
        now_epoch=after + 1,
    )
    assert summary["probe_requested_count"] == 5
    kinds = [payload["claim"]["source_kind"] for event, payload in bus.events
             if event == PROBE_REQUEST_EVENT]
    assert kinds == ["activity"] * 5
    for request in [payload for event, payload in bus.events
                    if event == PROBE_REQUEST_EVENT]:
        bus.publish(PROBE_RESULT_EVENT, {
            **request, "result": "source_unavailable",
            "reason": "route_snapshot_missing",
        })
    assert len(runtime.drain_results(now_epoch=after + 2)) == 5
    assert runtime.dispatch_due_probes(now_epoch=after + 3)["probe_requested_count"] == 5
    kinds = [payload["claim"]["source_kind"] for event, payload in bus.events
             if event == PROBE_REQUEST_EVENT]
    assert kinds == ["activity"] * 7 + ["gainers"] + ["activity"] * 2


def test_session_handoff_does_not_claim_premarket_route_in_regular_session(tmp_path):
    bus = Bus()
    runtime = ZeroBaseDiscoveryRuntime(
        event_bus=bus, session_date="2026-09-28", state_path=tmp_path / "state.json",
    )
    premarket = datetime(2026, 9, 28, 8, 59, 30,
                         tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    regular = datetime(2026, 9, 28, 9, 0, 30,
                       tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    runtime.queue.observe(
        code="123456", route="nxt_only", observed_epoch=premarket,
        source_sha256="a" * 64, source_scope="observed_panel",
        received_epoch=premarket, market="KOSPI", venue="NXT",
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
        scanner, "SniperRadar",
        lambda *_args: (_ for _ in ()).throw(AssertionError("legacy radar constructed")),
    )
    monkeypatch.setattr(
        scanner, "run_zero_base_scanner",
        lambda **kwargs: called.append(kwargs),
    )
    scanner.run_scalper(is_test_mode=True)
    assert called == [{"token": "token", "event_bus": bus, "is_test_mode": True}]


def test_scanner_emits_failed_probe_identity_and_artifact_cause(monkeypatch, tmp_path):
    import pytest
    from src.scanners import scalping_scanner as scanner
    from src.engine.error_detectors import process_health

    class StopScanner(Exception):
        pass

    result = {
        "claim": {"code": "058610", "route": "krx_nxt_integrated"},
        "candidate": {}, "result": "required_feature_insufficient",
        "reason": "source_quality_blocked_before_assessment",
        "machine_source_gap_kind": "runtime_preflight_artifact_not_ready",
        "machine_evaluation_status": "source_quality_blocked_before_assessment",
        "machine_preflight_artifact_status": "artifact_missing",
        "evaluation_attempt_id": "machine-source-invalid-exact",
        "machine_capture_status": "captured", "machine_observation_sha256": "a" * 64,
    }
    emitted = []
    monkeypatch.setattr(scanner, "ZeroBaseDiscoveryRuntime", lambda **_kwargs: type(
        "Runtime", (), {"drain_results": lambda self: [result]})())
    monkeypatch.setattr(scanner, "DATA_DIR", tmp_path)
    monkeypatch.setattr(scanner, "_active_scalping_buy_window", lambda _now: None)
    monkeypatch.setattr(process_health, "write_heartbeat", lambda _name: None)
    monkeypatch.setattr(scanner, "_zero_base_log_event", lambda stage, **kwargs: emitted.append((stage, kwargs)))
    monkeypatch.setattr(scanner.time, "sleep", lambda _seconds: (_ for _ in ()).throw(StopScanner()))
    with pytest.raises(StopScanner):
        scanner.run_zero_base_scanner(token="token", event_bus=Bus())
    assert len(emitted) == 1
    stage, payload = emitted[0]
    assert stage == "zero_base_probe_result" and payload["code"] == "058610"
    assert payload["fields"]["evaluation_attempt_id"] == result["evaluation_attempt_id"]
    assert payload["fields"]["zero_base_machine_source_gap_kind"] == "runtime_preflight_artifact_not_ready"
    assert payload["fields"]["zero_base_machine_preflight_artifact_status"] == "artifact_missing"
    assert payload["fields"]["machine_observation_sha256"] == "a" * 64

    result.update(result="source_unavailable", evaluation_attempt_id=None,
                  machine_evaluation_status=None, machine_preflight_artifact_status=None)
    emitted.clear()
    with pytest.raises(StopScanner):
        scanner.run_zero_base_scanner(token="token", event_bus=Bus())
    fields = emitted[0][1]["fields"]
    assert fields["evaluation_attempt_id"] == "-"
    assert fields["zero_base_machine_evaluation_status"] == "-"
    assert fields["zero_base_machine_preflight_artifact_status"] == "-"
