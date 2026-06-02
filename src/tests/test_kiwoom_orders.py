import sys
import types

sys.modules.setdefault("holidays", types.SimpleNamespace())

import src.engine.kiwoom_orders as kiwoom_orders
import src.engine.sniper_config as sniper_config


def test_get_deposit_uses_virtual_orderable_amount(monkeypatch):
    monkeypatch.setattr(
        sniper_config,
        "CONF",
        {"VIRTUAL_ORDERABLE_AMOUNT": 10_000_000},
    )
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)

    def _should_not_call_api(*args, **kwargs):
        raise AssertionError("virtual orderable amount is enabled")

    monkeypatch.setattr(kiwoom_orders.requests, "post", _should_not_call_api)

    assert kiwoom_orders.get_deposit("TOKEN") == 10_000_000


def test_get_deposit_falls_back_to_api_when_virtual_amount_disabled(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"rt_cd": "0", "ord_alow_amt": "50000000"}

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(
        kiwoom_orders.requests,
        "post",
        lambda *args, **kwargs: DummyResponse(),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 50_000_000


def test_get_deposit_request_contract_matches_kiwoom_kt00001_guide(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"return_code": 0, "return_msg": "조회가 완료되었습니다.", "ord_alow_amt": "000000000085341"}

    calls = []

    def _post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "headers": dict(headers or {}), "json": dict(json or {}), "timeout": timeout})
        return DummyResponse()

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://api.kiwoom.com{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)

    assert kiwoom_orders.get_deposit("TOKEN") == 85_341
    assert calls == [
        {
            "url": "https://api.kiwoom.com/api/dostk/acnt",
            "headers": {
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": "Bearer TOKEN",
                "cont-yn": "N",
                "next-key": "",
                "api-id": "kt00001",
            },
            "json": {"qry_tp": "3"},
            "timeout": 5,
        }
    ]


def test_get_deposit_retries_then_succeeds(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"rt_cd": "0", "ord_alow_amt": "12345678"}

    state = {"count": 0}

    def _post(*args, **kwargs):
        state["count"] += 1
        if state["count"] == 1:
            raise RuntimeError("temporary deposit failure")
        return DummyResponse()

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 0)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 0.0)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)

    assert kiwoom_orders.get_deposit("TOKEN") == 12_345_678
    assert state["count"] == 2


def test_get_deposit_uses_recent_cached_amount_after_api_failure(monkeypatch):
    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 9_876_543)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 1_000.0)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(
        kiwoom_orders.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("network down")),
    )
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: 1_005.0)

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543


def test_get_deposit_enters_short_cooldown_after_request_limit(monkeypatch):
    class LimitResponse:
        status_code = 200

        def json(self):
            return {
                "return_code": "1700",
                "return_msg": "허용된 요청 개수를 초과하였습니다[1700:허용된 요청 개수를 초과하였습니다. API ID=kt00001]",
            }

    times = iter([1_000.0, 1_000.0, 1_000.0, 1_000.0, 1_001.0, 1_001.0, 1_001.0])
    post_count = {"value": 0}

    def _post(*args, **kwargs):
        post_count["value"] += 1
        return LimitResponse()

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 9_876_543)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 995.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_REASON", "")
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: next(times))
    monkeypatch.setattr(
        kiwoom_orders,
        "TRADING_RULES",
        types.SimpleNamespace(
            DEPOSIT_API_RETRY_COUNT=1,
            DEPOSIT_API_RETRY_DELAY_SEC=0.0,
            DEPOSIT_API_REQUEST_LIMIT_COOLDOWN_SEC=10.0,
            DEPOSIT_CACHE_FALLBACK_TTL_SEC=30,
        ),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert post_count["value"] == 1
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "request_count_exceeded_cooldown"


def test_get_deposit_request_limit_breaks_same_call_retry(monkeypatch):
    class LimitResponse:
        status_code = 200

        def json(self):
            return {"return_code": "1700", "return_msg": "허용된 요청 개수를 초과하였습니다"}

    post_count = {"value": 0}

    def _post(*args, **kwargs):
        post_count["value"] += 1
        return LimitResponse()

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 9_876_543)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 995.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_REASON", "")
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: 1000.0)
    monkeypatch.setattr(
        kiwoom_orders,
        "TRADING_RULES",
        types.SimpleNamespace(
            DEPOSIT_API_RETRY_COUNT=2,
            DEPOSIT_API_RETRY_DELAY_SEC=0.0,
            DEPOSIT_API_REQUEST_LIMIT_COOLDOWN_SEC=10.0,
            DEPOSIT_CACHE_FALLBACK_TTL_SEC=30,
        ),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert post_count["value"] == 1
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "request_count_exceeded"


def test_get_deposit_transport_failure_enters_short_cooldown(monkeypatch):
    class TransportResponse:
        status_code = 200

        def json(self):
            return {
                "return_code": "2000",
                "return_msg": "(-994:fail to sendReceive:WINGSj)",
            }

    times = iter([1_000.0, 1_000.0, 1_000.0, 1_001.0, 1_001.0, 1_001.0])
    post_count = {"value": 0}

    def _post(*args, **kwargs):
        post_count["value"] += 1
        return TransportResponse()

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 9_876_543)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 995.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_REASON", "")
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: next(times))
    monkeypatch.setattr(
        kiwoom_orders,
        "TRADING_RULES",
        types.SimpleNamespace(
            DEPOSIT_API_RETRY_COUNT=2,
            DEPOSIT_API_RETRY_DELAY_SEC=0.0,
            DEPOSIT_API_TRANSPORT_COOLDOWN_SEC=5.0,
            DEPOSIT_CACHE_FALLBACK_TTL_SEC=30,
        ),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert post_count["value"] == 1
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "deposit_transport_failure"

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert post_count["value"] == 1
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "deposit_transport_cooldown"


def test_get_deposit_transport_cooldown_without_cache_fails_closed(monkeypatch):
    class TransportResponse:
        status_code = 200

        def json(self):
            return {
                "rt_cd": "2000",
                "err_msg": "(-994:fail to sendReceive:WINGSj)",
            }

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 0)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_REASON", "")
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", lambda *args, **kwargs: TransportResponse())
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(
        kiwoom_orders,
        "TRADING_RULES",
        types.SimpleNamespace(
            DEPOSIT_API_RETRY_COUNT=2,
            DEPOSIT_API_RETRY_DELAY_SEC=0.0,
            DEPOSIT_API_TRANSPORT_COOLDOWN_SEC=5.0,
            DEPOSIT_CACHE_FALLBACK_TTL_SEC=30,
        ),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 0
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "deposit_transport_failure"


def test_get_deposit_transport_message_code_enters_cooldown(monkeypatch):
    class TransportResponse:
        status_code = 200

        def json(self):
            return {
                "return_code": "",
                "return_msg": "[2000](-994:fail to sendReceive:WINGSj)",
            }

    post_count = {"value": 0}

    def _post(*args, **kwargs):
        post_count["value"] += 1
        return TransportResponse()

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 9_876_543)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 995.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_REASON", "")
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(
        kiwoom_orders,
        "TRADING_RULES",
        types.SimpleNamespace(
            DEPOSIT_API_RETRY_COUNT=2,
            DEPOSIT_API_RETRY_DELAY_SEC=0.0,
            DEPOSIT_API_TRANSPORT_COOLDOWN_SEC=5.0,
            DEPOSIT_CACHE_FALLBACK_TTL_SEC=30,
        ),
    )

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert post_count["value"] == 1
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "deposit_transport_failure"


def test_get_deposit_success_with_invalid_orderable_amount_uses_cache(monkeypatch):
    class InvalidSchemaResponse:
        status_code = 200

        def json(self):
            return {"return_code": 0, "return_msg": "조회가 완료되었습니다.", "ord_alow_amt": "J대한통운"}

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 9_876_543)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 995.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(kiwoom_orders, "_DEPOSIT_API_COOLDOWN_REASON", "")
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")
    monkeypatch.setattr(kiwoom_orders.requests, "post", lambda *args, **kwargs: InvalidSchemaResponse())
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)
    monkeypatch.setattr(kiwoom_orders.time, "time", lambda: 1_000.0)

    assert kiwoom_orders.get_deposit("TOKEN") == 9_876_543
    assert kiwoom_orders.get_last_deposit_errors()[0]["classification"] == "deposit_response_schema_invalid"


def test_get_deposit_records_auth_failure(monkeypatch):
    class DummyResponse:
        status_code = 401

        def json(self):
            return {"return_code": "8005", "return_msg": "Token이 유효하지 않습니다"}

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 0)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 0.0)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(
        kiwoom_orders.requests,
        "post",
        lambda *args, **kwargs: DummyResponse(),
    )
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True)
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)

    assert kiwoom_orders.get_deposit("TOKEN") == 0
    errors = kiwoom_orders.get_last_deposit_errors()
    assert errors
    assert kiwoom_orders.is_auth_failure_error(errors[0]) is True
    assert errors[0]["return_code"] == "8005"


def test_get_deposit_refreshes_token_and_retries_once_on_8005(monkeypatch, tmp_path):
    monkeypatch.setenv("KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json"))
    monkeypatch.setenv("KIWOOM_TOKEN_LOCK_PATH", str(tmp_path / "kiwoom_token_cache.lock"))
    class DummyResponse:
        def __init__(self, payload, status_code=200):
            self._payload = payload
            self.status_code = status_code

        def json(self):
            return dict(self._payload)

    posts = []
    invalidations = []
    responses = [
        DummyResponse({"return_code": "8005", "return_msg": "Token이 유효하지 않습니다"}),
        DummyResponse({"rt_cd": "0", "ord_alow_amt": "123000"}),
    ]

    def _post(url, headers=None, json=None, timeout=None):
        posts.append(dict(headers or {}))
        return responses.pop(0)

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 0)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 0.0)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://example.test{path}",
    )
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kiwoom_orders.kiwoom_utils,
        "invalidate_kiwoom_token_cache",
        lambda reason="": invalidations.append(reason) or True,
    )
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FRESH_TOKEN")

    assert kiwoom_orders.get_deposit("STALE_TOKEN") == 123_000
    assert len(posts) == 2
    assert posts[0]["authorization"] == "Bearer STALE_TOKEN"
    assert posts[1]["authorization"] == "Bearer FRESH_TOKEN"
    assert invalidations == []


def test_get_deposit_returns_auth_failure_when_token_refresh_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json"))
    monkeypatch.setenv("KIWOOM_TOKEN_LOCK_PATH", str(tmp_path / "kiwoom_token_cache.lock"))
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"return_code": "8005", "return_msg": "Token이 유효하지 않습니다"}

    posts = []

    def _post(*args, **kwargs):
        posts.append(kwargs)
        return DummyResponse()

    def _raise_refresh(*args, **kwargs):
        raise RuntimeError("refresh transport down")

    monkeypatch.setattr(sniper_config, "CONF", {"VIRTUAL_ORDERABLE_AMOUNT": 0})
    monkeypatch.setattr(kiwoom_orders, "_LAST_DEPOSIT_OVERRIDE", None)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT", 0)
    monkeypatch.setattr(kiwoom_orders, "_LAST_SUCCESSFUL_DEPOSIT_AT", 0.0)
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")
    monkeypatch.setattr(kiwoom_orders.requests, "post", _post)
    monkeypatch.setattr(kiwoom_orders, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True)
    monkeypatch.setattr(kiwoom_orders.kiwoom_utils, "get_kiwoom_token", _raise_refresh)
    monkeypatch.setattr(kiwoom_orders.time, "sleep", lambda _: None)

    assert kiwoom_orders.get_deposit("STALE_TOKEN") == 0
    assert len(posts) == 2
    errors = kiwoom_orders.get_last_deposit_errors()
    assert errors[-1]["return_code"] == "8005"
    assert kiwoom_orders.is_auth_failure_error(errors[-1]) is True
