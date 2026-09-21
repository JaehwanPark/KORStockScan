from __future__ import annotations

import json
from pathlib import Path

import pytest


def _widget_cache_fixture(tmp_path, monkeypatch):
    from src.utils import kiwoom_read_request_control as control
    clock = [601.0]
    monkeypatch.setattr(control.time, "time", lambda: clock[0])
    calls = []
    def fetch():
        calls.append(True)
        stamp = int(clock[0] * 1000)
        meta = {"api_id": "ka10004", "request_code": "005930", "rest_received_ts_ms": stamp}
        return {"return_code": 0, "buy_fpr_bid": "100", "sel_fpr_bid": "101",
                "buy_fpr_req": "10", "sel_fpr_req": "12", "_kiwoom_source_meta": meta}, {
            **meta, "request_succeeded": True, "request_attempt_count": 1,
            "request_token_digest": control.hashlib.sha256(b"PRIVATE-TOKEN").hexdigest()}
    cache = control.WidgetMarketResponseCache(tmp_path)
    kwargs = dict(token="PRIVATE-TOKEN", endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
                  api_id="ka10004", payload={"stk_cd": "005930"}, fetch=fetch)
    return cache, kwargs, clock, calls


def test_widget_response_cache_cross_instance_preserves_original_clock(tmp_path, monkeypatch):
    from src.utils.kiwoom_read_request_control import WidgetMarketResponseCache
    cache, kwargs, clock, calls = _widget_cache_fixture(tmp_path, monkeypatch)
    original, hit = cache.run(**kwargs)
    assert not hit
    clock[0] += 1
    reused, hit = WidgetMarketResponseCache(tmp_path).run(**kwargs)
    assert hit and len(calls) == 1
    assert reused[1]["rest_received_ts_ms"] == original[1]["rest_received_ts_ms"] == 601000
    assert reused[1]["request_attempt_count"] == 0
    reused[0]["buy_fpr_bid"] = "999"
    assert cache.run(**kwargs)[0][0]["buy_fpr_bid"] == "100"
    assert "PRIVATE-TOKEN" not in next(tmp_path.glob("*.json")).read_text()


def test_widget_response_cache_independent_process_read(tmp_path, monkeypatch):
    import subprocess, sys
    cache, kwargs, clock, calls = _widget_cache_fixture(tmp_path, monkeypatch)
    cache.run(**kwargs)
    script = '''import sys,json
from src.utils import kiwoom_read_request_control as c
c.time.time=lambda:602.0
def forbidden(): raise AssertionError("unexpected transport")
value,hit=c.WidgetMarketResponseCache(sys.argv[1]).run(token="PRIVATE-TOKEN",endpoint="https://api.kiwoom.com/api/dostk/mrkcond",api_id="ka10004",payload={"stk_cd":"005930"},fetch=forbidden)
print(json.dumps([hit,value[1]["rest_received_ts_ms"],value[1]["request_attempt_count"]]))
'''
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], check=True,
                            capture_output=True, text=True, timeout=10)
    assert json.loads(result.stdout.splitlines()[-1]) == [True, 601000, 0]


@pytest.mark.parametrize("change", ["token", "origin", "route", "body", "expired", "future", "minute", "corrupt", "receipt_conflict"])
def test_widget_response_cache_isolation_and_invalid_receipt(tmp_path, monkeypatch, change):
    cache, kwargs, clock, calls = _widget_cache_fixture(tmp_path, monkeypatch)
    if change == "minute": clock[0] = 659.5
    cache.run(**kwargs)
    if change == "token": kwargs["token"] = "OTHER"
    elif change == "origin": kwargs["endpoint"] = kwargs["endpoint"].replace("api.kiwoom", "mockapi.kiwoom")
    elif change == "route": kwargs["payload"] = {"stk_cd": "005930_AL"}
    elif change == "body": kwargs["payload"] = {"stk_cd": "005930", "extra": "1"}
    elif change == "expired": clock[0] += 3
    elif change == "future": clock[0] -= .1
    elif change == "minute": clock[0] += 1
    elif change == "corrupt": next(tmp_path.glob("*.json")).write_text("{")
    elif change == "receipt_conflict":
        p = next(tmp_path.glob("*.json")); d = json.loads(p.read_text())
        d["value"][0]["_kiwoom_source_meta"]["rest_received_ts_ms"] -= 1
        p.write_text(json.dumps(d))
    assert cache.run(**kwargs)[1] is False
    assert len(calls) == 2


@pytest.mark.parametrize("api,path", [("kt00011", "/api/dostk/acnt"), ("kt10000", "/api/dostk/ordr"), ("ka10004", "/wrong")])
def test_widget_response_cache_never_reuses_accounts_orders_or_wrong_path(tmp_path, monkeypatch, api, path):
    cache, kwargs, clock, calls = _widget_cache_fixture(tmp_path, monkeypatch)
    kwargs.update(api_id=api, endpoint="https://api.kiwoom.com" + path)
    cache.run(**kwargs); cache.run(**kwargs)
    assert len(calls) == 2 and not list(tmp_path.glob("*.json"))


def test_widget_response_cache_failure_and_io_fault_are_not_success(tmp_path, monkeypatch):
    cache, kwargs, clock, calls = _widget_cache_fixture(tmp_path, monkeypatch)
    def failed():
        raise RuntimeError("deferred")
    kwargs["fetch"] = failed
    with pytest.raises(RuntimeError, match="deferred"):
        cache.run(**kwargs)
    assert not list(tmp_path.glob("*.json"))


@pytest.mark.parametrize("defect", ["empty", "crossed", "token_changed", "io"])
def test_widget_response_cache_does_not_retain_partial_or_wrong_token(tmp_path, monkeypatch, defect):
    cache, kwargs, clock, calls = _widget_cache_fixture(tmp_path, monkeypatch)
    original = kwargs["fetch"]
    def fetch():
        data, receipt = original()
        if defect == "empty": data.pop("sel_fpr_req")
        elif defect == "crossed": data["sel_fpr_bid"] = "99"
        elif defect == "token_changed": receipt["request_token_digest"] = "changed"
        return data, receipt
    kwargs["fetch"] = fetch
    if defect == "io":
        p = tmp_path / "not_a_directory"; p.write_text("preserve")
        cache.directory = p
    assert cache.run(**kwargs)[1] is False
    assert cache.run(**kwargs)[1] is False
    assert len(calls) == 2

from src.utils.kiwoom_read_request_control import (
    KiwoomReadRequestCoordinator,
    is_kiwoom_read_rate_limit,
)


class MutableClock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.value

    def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.value += delay


def _coordinator(tmp_path: Path, clock: MutableClock) -> KiwoomReadRequestCoordinator:
    return KiwoomReadRequestCoordinator(
        state_dir=tmp_path,
        clock=clock,
        sleep=clock.sleep,
    )


def _acquire(
    coordinator: KiwoomReadRequestCoordinator,
    *,
    token: str = "SECRET-TOKEN",
    endpoint: str = "https://api.kiwoom.com/api/dostk/mrkcond",
    request_class: str = "source_only",
    max_wait_sec: float = 0.0,
):
    return coordinator.acquire(
        token=token,
        endpoint=endpoint,
        request_owner="test_owner",
        request_class=request_class,
        api_id="ka10004",
        request_code="005930",
        max_wait_sec=max_wait_sec,
    )


def test_source_only_reserves_fifth_slot_for_critical_read(tmp_path: Path) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)

    admitted = [_acquire(coordinator) for _ in range(4)]
    source_overflow = _acquire(coordinator)
    critical = _acquire(coordinator, request_class="execution_critical")
    critical_overflow = _acquire(
        coordinator,
        request_class="execution_critical",
        max_wait_sec=1.1,
    )

    assert all(item.admitted for item in admitted)
    assert source_overflow.admitted is False
    assert source_overflow.reason == "shared_read_rate_wait_budget_exhausted"
    assert critical.admitted is True
    assert critical.requests_in_window_before == 4
    assert critical_overflow.admitted is True
    assert clock.sleeps == pytest.approx([1.001])


def test_same_token_and_origin_share_window_across_paths(tmp_path: Path) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    second_process_view = _coordinator(tmp_path, clock)

    for _ in range(5):
        assert _acquire(
            coordinator,
            endpoint="https://api.kiwoom.com/api/dostk/acnt",
            request_class="runtime_required",
        ).admitted
    blocked = _acquire(
        second_process_view,
        endpoint="https://api.kiwoom.com/api/dostk/chart",
        request_class="runtime_required",
    )
    other_token = _acquire(
        coordinator,
        token="OTHER-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/chart",
        request_class="runtime_required",
    )

    assert blocked.admitted is False
    assert other_token.admitted is True
    state_text = "".join(path.read_text() for path in tmp_path.glob("*.json"))
    assert "SECRET-TOKEN" not in state_text
    assert "OTHER-TOKEN" not in state_text


def test_server_cooldown_defers_source_only_but_required_waits(tmp_path: Path) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    coordinator.record_rate_limit(
        token="SECRET-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
        request_owner="source_owner",
        request_class="source_only",
        api_id="ka10004",
        request_code="005930",
        http_status_code=429,
    )

    source_only = _acquire(coordinator)
    required = _acquire(
        coordinator,
        request_class="execution_critical",
        max_wait_sec=3.1,
    )

    assert source_only.admitted is False
    assert source_only.reason == "shared_read_rate_server_cooldown"
    assert required.admitted is True
    assert clock.sleeps == pytest.approx([3.0])


def test_corrupt_shared_state_fails_closed(tmp_path: Path) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    path, _digest = coordinator._state_path(
        token="SECRET-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not-json", encoding="utf-8")

    admission = _acquire(coordinator, request_class="runtime_required")

    assert admission.admitted is False
    assert admission.reason == "shared_read_rate_state_malformed"


def test_actual_rate_limit_repairs_invalid_prior_state_for_shared_cooldown(
    tmp_path: Path,
) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    path, _digest = coordinator._state_path(
        token="SECRET-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_domestic_read_rate_control_v1",
                "request_epochs": None,
                "cooldown_until_epoch": float("nan"),
            }
        ),
        encoding="utf-8",
    )

    recorded = coordinator.record_rate_limit(
        token="SECRET-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
        request_owner="test_owner",
        request_class="source_only",
        api_id="ka10004",
        request_code="005930",
        http_status_code=429,
    )
    source_only = _acquire(coordinator)

    assert recorded["recorded"] is True
    assert source_only.admitted is False
    assert source_only.reason == "shared_read_rate_server_cooldown"


@pytest.mark.parametrize(
    "invalid_epoch", [None, "100", True, -1.0, 999.0, float("nan")]
)
def test_invalid_shared_request_epoch_fails_closed(
    tmp_path: Path, invalid_epoch: object
) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    path, _digest = coordinator._state_path(
        token="SECRET-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_domestic_read_rate_control_v1",
                "request_epochs": [invalid_epoch],
            }
        ),
        encoding="utf-8",
    )

    admission = _acquire(coordinator, request_class="runtime_required")

    assert admission.admitted is False
    assert admission.reason == "shared_read_rate_request_epoch_value_invalid"


@pytest.mark.parametrize("invalid_cooldown", ["bad", -1.0, float("nan")])
def test_invalid_shared_cooldown_fails_closed(
    tmp_path: Path, invalid_cooldown: object
) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    path, _digest = coordinator._state_path(
        token="SECRET-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_domestic_read_rate_control_v1",
                "request_epochs": [],
                "cooldown_until_epoch": invalid_cooldown,
            }
        ),
        encoding="utf-8",
    )

    admission = _acquire(coordinator, request_class="runtime_required")

    assert admission.admitted is False
    assert admission.reason == "shared_read_rate_cooldown_invalid"


@pytest.mark.parametrize(
    ("http_status", "body", "expected"),
    [
        (429, {}, True),
        (200, {"return_code": 1700}, True),
        (200, {"return_code": "1701"}, True),
        (200, {"rt_cd": 1702}, True),
        (200, {"return_code": 0}, False),
    ],
)
def test_rate_limit_recognizes_http_and_official_body_codes(
    http_status: int, body: dict, expected: bool
) -> None:
    assert (
        is_kiwoom_read_rate_limit(
            http_status_code=http_status,
            response_body=body,
        )
        is expected
    )


def test_persisted_state_has_declared_five_per_second_contract(tmp_path: Path) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    assert _acquire(coordinator).admitted

    payload = json.loads(next(tmp_path.glob("*.json")).read_text())

    assert payload["bucket"] == "domestic_stock_read_tr"
    assert payload["window_sec"] == 1.0
    assert payload["max_requests"] == 5
    assert payload["source_only_limit"] == 4
    assert payload["environment"] == "production"
    assert payload["scope_api_id"] == "all_read_tr"


def test_mock_environment_uses_one_per_second_per_tr(tmp_path: Path) -> None:
    clock = MutableClock()
    coordinator = _coordinator(tmp_path, clock)
    endpoint = "https://mockapi.kiwoom.com/api/dostk/mrkcond"

    first = _acquire(coordinator, endpoint=endpoint, request_class="runtime_required")
    same_tr = _acquire(
        coordinator,
        endpoint=endpoint,
        request_class="runtime_required",
    )
    other_tr = coordinator.acquire(
        token="SECRET-TOKEN",
        endpoint="https://mockapi.kiwoom.com/api/dostk/stkinfo",
        request_owner="test_owner",
        request_class="runtime_required",
        api_id="ka10001",
        request_code="005930",
        max_wait_sec=0.0,
    )

    assert first.admitted is True
    assert first.max_limit == 1
    assert same_tr.admitted is False
    assert other_tr.admitted is True
    payloads = [json.loads(path.read_text()) for path in tmp_path.glob("*.json")]
    assert len(payloads) == 2
    assert {payload["scope_api_id"] for payload in payloads} == {
        "ka10001",
        "ka10004",
    }
    assert {payload["max_requests"] for payload in payloads} == {1}


def test_market_singleflight_joins_once_and_returns_independent_copies(monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from src.utils.kiwoom_read_request_control import MarketReadSingleFlight

    runner = MarketReadSingleFlight()
    entered, release, joining = threading.Event(), threading.Event(), threading.Event()
    calls = []

    def fetch():
        calls.append(1)
        entered.set()
        assert release.wait(2)
        return [{"source_received_at": 100, "price": 42}]

    with ThreadPoolExecutor(max_workers=2) as pool:
        owner = pool.submit(runner.run, "exact-scope", fetch, wait_sec=1)
        assert entered.wait(1)
        event = runner._in_flight["exact-scope"]["event"]
        real_wait = event.wait

        def wait(timeout):
            joining.set()
            return real_wait(timeout)

        monkeypatch.setattr(event, "wait", wait)
        follower = pool.submit(runner.run, "exact-scope", fetch, wait_sec=1)
        assert joining.wait(1)
        release.set()
        first, owned, _ = owner.result(1)
        second, joined, _ = follower.result(1)
    assert calls == [1]
    assert owned is False and joined is True
    first[0]["price"] = 0
    assert second == [{"source_received_at": 100, "price": 42}]
    assert not runner._in_flight
    runner.run("exact-scope", lambda: calls.append(2), wait_sec=1)
    assert calls == [1, 2]


def test_market_singleflight_follower_timeout_does_not_duplicate_or_cancel_owner():
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from src.utils.kiwoom_read_request_control import (
        MarketReadSingleFlight,
        MarketReadJoinDeferred,
    )

    runner = MarketReadSingleFlight()
    entered, release = threading.Event(), threading.Event()
    calls = []

    def fetch():
        calls.append(1)
        entered.set()
        assert release.wait(2)
        return {"received_at": 100}

    with ThreadPoolExecutor(max_workers=1) as pool:
        owner = pool.submit(runner.run, "key", fetch, wait_sec=1)
        assert entered.wait(1)
        with pytest.raises(MarketReadJoinDeferred, match="wait_budget"):
            runner.run("key", fetch, wait_sec=0)
        assert not owner.done()
        assert calls == [1]
        release.set()
        assert owner.result(1)[0] == {"received_at": 100}
    assert not runner._in_flight


def test_market_singleflight_failure_cleanup_and_recursive_call():
    from src.utils.kiwoom_read_request_control import MarketReadSingleFlight

    runner = MarketReadSingleFlight()
    with pytest.raises(ValueError, match="source_broken"):
        runner.run(
            "key",
            lambda: (_ for _ in ()).throw(ValueError("source_broken")),
            wait_sec=0,
        )
    assert not runner._in_flight
    assert runner.run("key", lambda: {"recovered": True}, wait_sec=0)[0] == {
        "recovered": True
    }
    with pytest.raises(RuntimeError, match="recursive"):
        runner.run(
            "key", lambda: runner.run("key", lambda: None, wait_sec=0), wait_sec=0
        )
    assert not runner._in_flight


@pytest.mark.parametrize("wait", [-1, float("nan"), float("inf")])
def test_market_singleflight_rejects_unbounded_wait(wait):
    from src.utils.kiwoom_read_request_control import MarketReadSingleFlight

    with pytest.raises(ValueError, match="wait_invalid"):
        MarketReadSingleFlight().run("key", lambda: None, wait_sec=wait)


def test_market_singleflight_forked_child_never_waits_for_parent_owner_or_mutex():
    import multiprocessing
    import os
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from src.utils.kiwoom_read_request_control import MarketReadSingleFlight

    if not hasattr(os, "register_at_fork"):
        pytest.skip("fork reset is POSIX-only")
    ctx = multiprocessing.get_context("fork")
    runner = MarketReadSingleFlight()
    entered, release = threading.Event(), threading.Event()
    receive, send = ctx.Pipe(duplex=False)

    def fetch():
        entered.set()
        assert release.wait(5)
        return {"parent": True}

    def child_read():
        try:
            send.send(runner.run("key", lambda: {"child": True}, wait_sec=0)[:2])
        finally:
            send.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        owner = pool.submit(runner.run, "key", fetch, wait_sec=0)
        assert entered.wait(1)
        child = ctx.Process(target=child_read)
        runner._lock.acquire()
        try:
            child.start()
        finally:
            runner._lock.release()
        try:
            assert receive.poll(3), "child inherited an unfinishable parent dependency"
            assert receive.recv() == ({"child": True}, False)
            child.join(1)
            assert child.exitcode == 0
            assert "key" in runner._in_flight
        finally:
            if child.is_alive():
                child.terminate()
                child.join(1)
            release.set()
            receive.close()
            send.close()
        assert owner.result(1)[0] == {"parent": True}
