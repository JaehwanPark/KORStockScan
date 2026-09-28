from datetime import datetime
from zoneinfo import ZoneInfo

from src.scanners.zero_base_discovery_runtime import (
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
        "code": "123456", "route": "krx_only", "observed_epoch": T0,
        "source_sha256": "a" * 64, "source_scope": "observed_panel",
        "name": "TEST", "market": "KOSPI", "venue": "KRX", "price": 10000,
    }]}


def test_runtime_durable_claim_machine_enter_and_late_result_rejection(tmp_path):
    bus = Bus()
    state = tmp_path / "2026-09-28.json"
    runtime = ZeroBaseDiscoveryRuntime(event_bus=bus, session_date="2026-09-28", state_path=state)
    summary = runtime.scan_once("token", fetcher=_panel, now_epoch=T0 + 1)
    assert summary["probe_requested_count"] == 1
    request = next(payload for event, payload in bus.events if event == PROBE_REQUEST_EVENT)
    assert state.exists()

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
