from __future__ import annotations

import json
from pathlib import Path

import pytest

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
