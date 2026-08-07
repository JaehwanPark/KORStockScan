from __future__ import annotations

import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.kiwoom_websocket import KiwoomWSManager
from src.utils import kiwoom_utils


class _FakeResponse:
    def __init__(self, token: str, *, status_code: int = 200, expires_in: int = 3600):
        self.status_code = status_code
        self.text = "OK"
        self._payload = {"access_token": token, "expires_in": expires_in}

    def json(self):
        return dict(self._payload)


class _FakeApiResponse:
    def __init__(
        self, payload: dict, *, status_code: int = 200, headers: dict | None = None
    ):
        self.status_code = status_code
        self.text = json.dumps(payload, ensure_ascii=False)
        self._payload = dict(payload)
        self.headers = headers or {}

    def json(self):
        return dict(self._payload)


def _config():
    return {
        "KIWOOM_BASE_URL": "https://example.test",
        "KIWOOM_APPKEY": "app-key-1234",
        "KIWOOM_SECRETKEY": "secret-key-5678",
    }


def _patch_cache_paths(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json")
    )
    monkeypatch.setenv(
        "KIWOOM_TOKEN_LOCK_PATH", str(tmp_path / "kiwoom_token_cache.lock")
    )


def _patch_config_path(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config()), encoding="utf-8")
    monkeypatch.setattr(kiwoom_utils, "CONFIG_PATH", config_path)
    monkeypatch.setattr(kiwoom_utils, "DEV_PATH", tmp_path / "missing_dev_config.json")


def test_get_kiwoom_token_reuses_shared_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse("TOKEN_A")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}"
    )

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_A"
    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_A"
    assert len(calls) == 1


def test_token_expiry_parses_official_expires_dt_as_kst():
    expected = datetime(
        2026,
        8,
        8,
        8,
        48,
        14,
        tzinfo=ZoneInfo("Asia/Seoul"),
    ).timestamp()

    assert (
        kiwoom_utils._parse_token_expires_at(
            {"expires_dt": "20260808084814"},
            now_ts=0,
        )
        == expected
    )


def test_get_cached_kiwoom_token_never_issues_when_cache_is_missing(
    monkeypatch, tmp_path
):
    _patch_cache_paths(monkeypatch, tmp_path)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("read-only token helper must not issue a token")

    monkeypatch.setattr(kiwoom_utils, "_request_new_kiwoom_token", fail_if_called)

    assert kiwoom_utils.get_cached_kiwoom_token(_config()) is None


def test_get_kiwoom_token_refreshes_expired_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    cache_path = tmp_path / "kiwoom_token_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cache_key": kiwoom_utils._token_cache_key(_config()),
                "access_token": "OLD_TOKEN",
                "issued_at": time.time() - 7200,
                "expires_at": time.time() - 60,
            }
        ),
        encoding="utf-8",
    )
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse("TOKEN_B")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}"
    )

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_B"
    assert len(calls) == 1


def test_get_kiwoom_token_force_refresh_bypasses_valid_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse(f"TOKEN_{len(calls)}")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}"
    )

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_1"
    assert kiwoom_utils.get_kiwoom_token(_config(), force_refresh=True) == "TOKEN_2"
    assert len(calls) == 2


def test_runtime_start_refreshes_valid_prior_day_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    now = time.time()
    cache_path = tmp_path / "kiwoom_token_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cache_key": kiwoom_utils._token_cache_key(_config()),
                "access_token": "PRIOR_DAY_TOKEN",
                "issued_at": now - (24 * 60 * 60),
                "expires_at": now + 3600,
            }
        ),
        encoding="utf-8",
    )
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse("TODAY_TOKEN")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}"
    )

    token = kiwoom_utils.get_kiwoom_token(
        _config(),
        require_issued_today=True,
    )

    assert token == "TODAY_TOKEN"
    assert len(calls) == 1


def test_runtime_start_reuses_valid_same_day_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    now = time.time()
    cache_path = tmp_path / "kiwoom_token_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cache_key": kiwoom_utils._token_cache_key(_config()),
                "access_token": "TODAY_TOKEN",
                "issued_at": now,
                "expires_at": now + 3600,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        kiwoom_utils,
        "_request_new_kiwoom_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("same-day runtime start must reuse the shared token")
        ),
    )

    assert (
        kiwoom_utils.get_kiwoom_token(
            _config(),
            require_issued_today=True,
        )
        == "TODAY_TOKEN"
    )


def test_ws_token_refresh_uses_force_refresh(monkeypatch):
    calls = []
    replacements = []

    def fake_get_token(conf, **kwargs):
        calls.append(kwargs)
        return "NEW_TOKEN"

    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", fake_get_token)
    monkeypatch.setattr(
        kiwoom_utils,
        "register_kiwoom_token_replacement",
        lambda failed, replacement, *, source: replacements.append(
            (failed, replacement, source)
        )
        or True,
    )

    manager = KiwoomWSManager("OLD_TOKEN")
    assert manager._refresh_ws_token() is True
    assert manager.token == "NEW_TOKEN"
    assert calls == [{"force_refresh": True}]
    assert replacements == []
    assert manager._pending_token_handoff == ("OLD_TOKEN", "NEW_TOKEN")

    assert manager._commit_ws_token_handoff() is True
    assert replacements == [("OLD_TOKEN", "NEW_TOKEN", "websocket_login_ack_success")]
    assert manager._pending_token_handoff is None


def test_fetch_kiwoom_api_continuous_refreshes_and_retries_once_on_8005(
    monkeypatch, tmp_path
):
    _patch_cache_paths(monkeypatch, tmp_path)
    _patch_config_path(monkeypatch, tmp_path)
    posts = []
    invalidations = []

    responses = [
        _FakeApiResponse(
            {
                "return_code": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        ),
        _FakeApiResponse({"return_code": "0", "rows": [{"ok": True}]}),
    ]

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append(
            {
                "url": url,
                "headers": dict(headers or {}),
                "payload": json,
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    def fake_get_token(*args, **kwargs):
        assert kwargs == {"force_refresh": True}
        return "FRESH_TOKEN"

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", fake_get_token)
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kiwoom_utils,
        "invalidate_kiwoom_token_cache",
        lambda reason="": invalidations.append(reason) or True,
    )

    result = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STALE_TOKEN",
        api_id="kt00008",
        payload={},
        use_continuous=False,
    )

    assert result == [{"return_code": "0", "rows": [{"ok": True}]}]
    assert len(posts) == 2
    assert posts[0]["headers"]["authorization"] == "Bearer STALE_TOKEN"
    assert posts[1]["headers"]["authorization"] == "Bearer FRESH_TOKEN"
    assert invalidations == []


def test_auth_retry_handoff_prevents_repeated_first_attempt_8005(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    posts = []
    responses = [
        _FakeApiResponse(
            {
                "return_code": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        ),
        _FakeApiResponse({"return_code": "0", "rows": [{"request": 1}]}),
        _FakeApiResponse({"return_code": "0", "rows": [{"request": 2}]}),
    ]

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append(dict(headers or {}))
        return responses.pop(0)

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FRESH_TOKEN"
    )
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)

    first = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STARTUP_TOKEN",
        api_id="ka10004",
        payload={},
    )
    second = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STARTUP_TOKEN",
        api_id="ka10084",
        payload={},
    )

    assert first == [{"return_code": "0", "rows": [{"request": 1}]}]
    assert second == [{"return_code": "0", "rows": [{"request": 2}]}]
    assert [headers["authorization"] for headers in posts] == [
        "Bearer STARTUP_TOKEN",
        "Bearer FRESH_TOKEN",
        "Bearer FRESH_TOKEN",
    ]


def test_auth_retry_does_not_publish_failed_refresh_token(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    responses = [
        _FakeApiResponse(
            {
                "return_code": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        ),
        _FakeApiResponse(
            {
                "return_code": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        ),
    ]
    monkeypatch.setattr(
        kiwoom_utils.requests,
        "post",
        lambda *args, **kwargs: responses.pop(0),
    )
    monkeypatch.setattr(
        kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FAILED_REFRESH"
    )
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)

    result = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STARTUP_TOKEN",
        api_id="ka10004",
        payload={},
    )

    assert result[-1]["return_code"] == "8005"
    assert kiwoom_utils.resolve_kiwoom_request_token("STARTUP_TOKEN") == (
        "STARTUP_TOKEN"
    )


def test_token_handoff_rejects_cycle(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)

    assert kiwoom_utils.register_kiwoom_token_replacement(
        "TOKEN_A", "TOKEN_B", source="test"
    )
    assert not kiwoom_utils.register_kiwoom_token_replacement(
        "TOKEN_B", "TOKEN_A", source="test_reverse"
    )
    assert kiwoom_utils.resolve_kiwoom_request_token("TOKEN_A") == "TOKEN_B"


def test_fetch_kiwoom_api_continuous_retries_transient_5xx(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    posts = []
    sleeps = []
    responses = [
        _FakeApiResponse({}, status_code=502),
        _FakeApiResponse({"return_code": "0", "rows": [{"ok": True}]}),
    ]

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append(
            {
                "url": url,
                "headers": dict(headers or {}),
                "payload": json,
                "timeout": timeout,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils.time, "sleep", lambda seconds: sleeps.append(seconds)
    )
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)

    result = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="TOKEN",
        api_id="ka10080",
        payload={"stk_cd": "005930"},
        use_continuous=False,
    )

    assert result == [{"return_code": "0", "rows": [{"ok": True}]}]
    assert len(posts) == 2
    assert posts[0]["headers"]["authorization"] == "Bearer TOKEN"
    assert posts[1]["headers"]["authorization"] == "Bearer TOKEN"
    assert sleeps == [2]


def test_fetch_kiwoom_api_continuous_stops_after_single_8005_refresh_retry(
    monkeypatch, tmp_path
):
    _patch_cache_paths(monkeypatch, tmp_path)
    posts = []

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append(dict(headers or {}))
        return _FakeApiResponse(
            {
                "return_code": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        )

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FRESH_TOKEN"
    )
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True
    )

    result = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STALE_TOKEN",
        api_id="kt00008",
        payload={},
        use_continuous=False,
    )

    assert len(posts) == 2
    assert posts[0]["authorization"] == "Bearer STALE_TOKEN"
    assert posts[1]["authorization"] == "Bearer FRESH_TOKEN"
    assert result == [
        {
            "return_code": "8005",
            "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
        }
    ]


def test_fetch_kiwoom_api_continuous_recognizes_rt_cd_8005(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    posts = []
    responses = [
        _FakeApiResponse(
            {
                "rt_cd": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        ),
        _FakeApiResponse({"return_code": "0", "rows": [{"ok": True}]}),
    ]

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append(dict(headers or {}))
        return responses.pop(0)

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(
        kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FRESH_TOKEN"
    )
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True
    )

    result = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STALE_TOKEN",
        api_id="kt00008",
        payload={},
        use_continuous=False,
    )

    assert result == [{"return_code": "0", "rows": [{"ok": True}]}]
    assert len(posts) == 2
    assert posts[1]["authorization"] == "Bearer FRESH_TOKEN"


def test_fetch_kiwoom_api_continuous_returns_8005_when_refresh_raises(
    monkeypatch, tmp_path
):
    _patch_cache_paths(monkeypatch, tmp_path)
    posts = []

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append(dict(headers or {}))
        return _FakeApiResponse(
            {
                "return_code": "8005",
                "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
            }
        )

    def _raise_refresh(*args, **kwargs):
        raise RuntimeError("refresh transport down")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", _raise_refresh)
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True
    )

    result = kiwoom_utils.fetch_kiwoom_api_continuous(
        url="https://example.test/api",
        token="STALE_TOKEN",
        api_id="kt00008",
        payload={},
        use_continuous=False,
    )

    assert len(posts) == 1
    assert result == [
        {
            "return_code": "8005",
            "return_msg": "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
        }
    ]


def test_8005_refresh_reuses_newer_cached_token_without_invalidating(
    monkeypatch, tmp_path
):
    _patch_cache_paths(monkeypatch, tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config()), encoding="utf-8")
    monkeypatch.setattr(kiwoom_utils, "CONFIG_PATH", config_path)
    monkeypatch.setattr(kiwoom_utils, "DEV_PATH", tmp_path / "missing_dev_config.json")
    cache_path = tmp_path / "kiwoom_token_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cache_key": kiwoom_utils._token_cache_key(_config()),
                "access_token": "NEWER_TOKEN",
                "issued_at": time.time(),
                "expires_at": time.time() + 3600,
            }
        ),
        encoding="utf-8",
    )
    invalidations = []

    monkeypatch.setattr(
        kiwoom_utils,
        "invalidate_kiwoom_token_cache",
        lambda reason="": invalidations.append(reason) or True,
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "get_kiwoom_token",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("refresh should not be called")
        ),
    )
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)

    token = kiwoom_utils.get_kiwoom_token_after_auth_failure(
        api_id="kt00001",
        failed_token="STALE_TOKEN",
        reason_prefix="order_api_8005_retry",
    )

    assert token == "NEWER_TOKEN"
    assert invalidations == []
