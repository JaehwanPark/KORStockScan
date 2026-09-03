from __future__ import annotations

from src.utils import kiwoom_utils
from src.utils.kiwoom_read_request_control import KiwoomReadRequestCoordinator


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)
        self.headers = {}

    def json(self):
        return self._payload


def test_ka10004_orderbook_does_not_publish_best_ask_as_curr(monkeypatch):
    def fake_fetch_kiwoom_api_continuous(**_kwargs):
        return [
            {
                "bid_req_base_tm": "093001",
                "sel_fpr_bid": "10100",
                "sel_fpr_req": "120",
                "buy_fpr_bid": "10000",
                "buy_fpr_req": "240",
                "tot_sel_req": "1000",
                "tot_buy_req": "2000",
            }
        ]

    monkeypatch.setattr(
        kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch_kiwoom_api_continuous
    )
    snapshot = kiwoom_utils.get_stock_orderbook_ka10004("token", "005930")

    assert snapshot["curr"] == 0
    assert snapshot["rest_current_price"] == 0
    assert snapshot["best_ask"] == 10100
    assert snapshot["best_bid"] == 10000
    assert snapshot["rest_mid_price"] == 10050
    assert snapshot["marketable_buy_touch_price"] == 10100
    assert snapshot["marketable_sell_touch_price"] == 10000
    assert snapshot["passive_buy_price"] == 10000
    assert snapshot["passive_sell_price"] == 10100
    assert snapshot["executable_buy_price"] == 10100
    assert snapshot["executable_sell_price"] == 10000
    assert snapshot["bid_req_base_tm"] == "093001"
    assert snapshot["bid_req_base_tm_authority"] == "raw_not_freshness_input"
    assert snapshot["source_time_basis"] == "response_received_epoch_ms"
    assert snapshot["rest_freshness_basis"] == "response_received_epoch_ms"
    assert snapshot["rest_age_source"] == "response_received_epoch_ms"
    assert snapshot["rest_age_ms"] == 0
    assert snapshot["age_ms"] == 0
    assert snapshot["rest_received_ts_ms"] > 0


def test_ka10004_preserves_explicit_nxt_market_suffix(monkeypatch):
    calls = []

    def fake_fetch_kiwoom_api_continuous(**kwargs):
        calls.append(kwargs)
        return [
            {
                "bid_req_base_tm": "093001",
                "sel_fpr_bid": "10100",
                "sel_fpr_req": "120",
                "buy_fpr_bid": "10000",
                "buy_fpr_req": "240",
            }
        ]

    monkeypatch.setattr(
        kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch_kiwoom_api_continuous
    )

    snapshot = kiwoom_utils.get_stock_orderbook_ka10004("token", "005930_NX")

    assert calls[0]["payload"]["stk_cd"] == "005930_NX"
    assert snapshot["stock_code"] == "005930"
    assert snapshot["request_code"] == "005930_NX"


def test_ka10004_explicit_request_code_bypasses_implicit_db_route(monkeypatch):
    calls = []

    monkeypatch.setattr(
        kiwoom_utils,
        "get_effective_kiwoom_code",
        lambda _code: "005930_NX",
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **kwargs: calls.append(kwargs)
        or [
            {
                "sel_fpr_bid": "10100",
                "buy_fpr_bid": "10000",
            }
        ],
    )

    snapshot = kiwoom_utils.get_stock_orderbook_ka10004(
        "token",
        "005930",
        explicit_request_code=True,
        max_retries=1,
    )

    assert calls[0]["payload"]["stk_cd"] == "005930"
    assert calls[0]["max_retries"] == 1
    assert snapshot["request_code"] == "005930"
    assert snapshot["explicit_request_code"] is True


def test_ka10004_http_429_is_structured_and_shares_source_only_cooldown(
    monkeypatch, tmp_path
):
    calls = []
    error_logs = []
    info_logs = []
    coordinator = KiwoomReadRequestCoordinator(state_dir=tmp_path)
    monkeypatch.setattr(kiwoom_utils, "log_error", error_logs.append)
    monkeypatch.setattr(kiwoom_utils, "log_info", info_logs.append)
    monkeypatch.setattr(
        kiwoom_utils.requests,
        "post",
        lambda *_args, **_kwargs: calls.append(1) or _Response(429, {}),
    )
    monkeypatch.setattr(
        kiwoom_utils.time,
        "sleep",
        lambda _delay: (_ for _ in ()).throw(
            AssertionError("the exhausted final attempt must not sleep")
        ),
    )

    first_results, first_meta = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://api.kiwoom.com/api/dostk/mrkcond",
        token="RATE-LIMIT-TOKEN",
        api_id="ka10004",
        payload={"stk_cd": "005930"},
        max_retries=1,
        return_meta=True,
        request_owner="test_source_owner",
        request_class="source_only",
        read_rate_coordinator=coordinator,
    )
    second_results, second_meta = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://api.kiwoom.com/api/dostk/mrkcond",
        token="RATE-LIMIT-TOKEN",
        api_id="ka10004",
        payload={"stk_cd": "000660"},
        max_retries=1,
        return_meta=True,
        request_owner="test_source_owner",
        request_class="source_only",
        read_rate_coordinator=coordinator,
    )

    assert first_results == []
    assert first_meta["rate_limit_detected"] is True
    assert first_meta["rate_limit_http_status_code"] == 429
    assert first_meta["rate_limit_retry_exhausted"] is True
    assert first_meta["request_owner"] == "test_source_owner"
    assert first_meta["request_pid"] > 0
    assert first_meta["request_code"] == "005930"
    assert second_results == []
    assert second_meta["read_rate_control_status"] == "deferred"
    assert second_meta["read_rate_control_reason"] == (
        "shared_read_rate_server_cooldown"
    )
    assert calls == [1]
    assert len(error_logs) == 1
    assert "[KIWOOM_READ_TR_RATE_LIMIT]" in error_logs[0]
    assert "api_id=ka10004" in error_logs[0]
    assert "http_status=429" in error_logs[0]
    assert "request_class=source_only" in error_logs[0]
    assert len(info_logs) == 1
    assert "[KIWOOM_READ_TR_DEFERRED]" in info_logs[0]
    assert "shared_read_rate_server_cooldown" in info_logs[0]


def test_shared_read_budget_defer_is_not_logged_as_request_failure(
    monkeypatch, tmp_path
):
    error_logs = []
    info_logs = []
    coordinator = KiwoomReadRequestCoordinator(state_dir=tmp_path)
    monkeypatch.setattr(kiwoom_utils, "log_error", error_logs.append)
    monkeypatch.setattr(kiwoom_utils, "log_info", info_logs.append)
    monkeypatch.setattr(
        kiwoom_utils.requests,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a deferred request must not reach Kiwoom")
        ),
    )
    for index in range(4):
        admission = coordinator.acquire(
            token="BUDGET-TOKEN",
            endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
            request_owner=f"budget_seed_{index}",
            request_class="source_only",
            api_id="ka10004",
            request_code=f"00000{index}",
            max_wait_sec=0.0,
        )
        assert admission.admitted is True

    results, meta = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://api.kiwoom.com/api/dostk/mrkcond",
        token="BUDGET-TOKEN",
        api_id="ka10004",
        payload={"stk_cd": "005930"},
        max_retries=1,
        return_meta=True,
        request_owner="test_source_owner",
        request_class="source_only",
        read_rate_max_wait_sec=0.0,
        read_rate_coordinator=coordinator,
    )

    assert results == []
    assert meta["request_attempt_count"] == 0
    assert meta["read_rate_control_status"] == "deferred"
    assert meta["read_rate_control_reason"] == (
        "shared_read_rate_wait_budget_exhausted"
    )
    assert error_logs == []
    assert len(info_logs) == 1
    assert "[KIWOOM_READ_TR_DEFERRED]" in info_logs[0]
    assert "deferred_attempt_sent=false" in info_logs[0]
    assert "prior_http_attempt_count=0" in info_logs[0]
    assert "waited_sec=" in info_logs[0]
    assert "scope_digest=" in info_logs[0]


def test_malformed_shared_read_admission_remains_a_typed_error(
    monkeypatch, tmp_path
):
    error_logs = []
    info_logs = []
    coordinator = KiwoomReadRequestCoordinator(state_dir=tmp_path)
    state_path, _digest = coordinator._state_path(
        token="MALFORMED-TOKEN",
        endpoint="https://api.kiwoom.com/api/dostk/mrkcond",
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(kiwoom_utils, "log_error", error_logs.append)
    monkeypatch.setattr(kiwoom_utils, "log_info", info_logs.append)
    monkeypatch.setattr(
        kiwoom_utils.requests,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("an invalid admission must fail before HTTP")
        ),
    )

    results, meta = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://api.kiwoom.com/api/dostk/mrkcond",
        token="MALFORMED-TOKEN",
        api_id="ka10004",
        payload={"stk_cd": "005930"},
        max_retries=1,
        return_meta=True,
        request_owner="test_runtime_owner",
        request_class="runtime_required",
        read_rate_coordinator=coordinator,
    )

    assert results == []
    assert meta["request_attempt_count"] == 0
    assert meta["read_rate_control_status"] == "deferred"
    assert meta["read_rate_control_reason"] == "shared_read_rate_state_malformed"
    assert info_logs == []
    assert len(error_logs) == 1
    assert "[KIWOOM_READ_TR_ADMISSION_FAILED]" in error_logs[0]
    assert "request_class=runtime_required" in error_logs[0]
    assert "shared_read_rate_state_malformed" in error_logs[0]


def test_ka10004_body_1700_is_not_published_as_a_quote(monkeypatch, tmp_path):
    error_logs = []
    coordinator = KiwoomReadRequestCoordinator(state_dir=tmp_path)
    monkeypatch.setattr(kiwoom_utils, "log_error", error_logs.append)
    monkeypatch.setattr(
        kiwoom_utils.requests,
        "post",
        lambda *_args, **_kwargs: _Response(
            200,
            {
                "return_code": 1700,
                "return_msg": "허용된 API 요청 개수를 초과하였습니다.",
            },
        ),
    )
    monkeypatch.setattr(
        kiwoom_utils.time,
        "sleep",
        lambda _delay: (_ for _ in ()).throw(
            AssertionError("the exhausted final attempt must not sleep")
        ),
    )

    results, meta = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://api.kiwoom.com/api/dostk/mrkcond",
        token="BODY-LIMIT-TOKEN",
        api_id="ka10004",
        payload={"stk_cd": "005930"},
        max_retries=1,
        return_meta=True,
        request_owner="test_runtime_owner",
        request_class="runtime_required",
        read_rate_coordinator=coordinator,
    )

    assert results == []
    assert meta["rate_limit_detected"] is True
    assert meta["rate_limit_response_code"] == "1700"
    assert meta["rate_limit_retry_exhausted"] is True
    assert len(error_logs) == 1
    assert "[KIWOOM_READ_TR_RATE_LIMIT]" in error_logs[0]
    assert "code=1700" in error_logs[0]
    assert "request_class=runtime_required" in error_logs[0]


def test_effective_kiwoom_code_preserves_explicit_market_suffix():
    assert kiwoom_utils.normalize_stock_code("A005930_NX") == "005930"
    assert (
        kiwoom_utils.get_effective_kiwoom_code("A005930_NX", is_nxt=False)
        == "005930_NX"
    )
    assert (
        kiwoom_utils.get_effective_kiwoom_code("005930_AL", is_nxt=False) == "005930_AL"
    )


def test_normalize_stock_code_does_not_collapse_alphanumeric_instrument_namespace():
    identity = kiwoom_utils.kiwoom_stock_code_identity("0182R0_AL")

    assert kiwoom_utils.normalize_stock_code("0182R0_AL") == "0182R0"
    assert identity == {
        "raw_instrument_code": "0182R0_AL",
        "raw_base_code": "0182R0",
        "market_suffix": "_AL",
        "canonical_code": "0182R0",
        "is_equity_code": False,
        "code_namespace": "non_equity_or_ambiguous",
    }
    assert kiwoom_utils.normalize_stock_code("A005930") == "005930"
    assert kiwoom_utils.normalize_stock_code("005930_AL") == "005930"
    assert kiwoom_utils.normalize_stock_code("1001820_AL") == "1001820"
    assert (
        kiwoom_utils.kiwoom_stock_code_identity("1001820_AL")["is_equity_code"] is False
    )
