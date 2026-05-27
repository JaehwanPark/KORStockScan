from __future__ import annotations

import json
import time

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
    def __init__(self, payload: dict, *, status_code: int = 200, headers: dict | None = None):
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
    monkeypatch.setenv("KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json"))
    monkeypatch.setenv("KIWOOM_TOKEN_LOCK_PATH", str(tmp_path / "kiwoom_token_cache.lock"))


def test_get_kiwoom_token_reuses_shared_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse("TOKEN_A")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}")

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_A"
    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_A"
    assert len(calls) == 1


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
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}")

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_B"
    assert len(calls) == 1


def test_get_kiwoom_token_force_refresh_bypasses_valid_cache(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return _FakeResponse(f"TOKEN_{len(calls)}")

    monkeypatch.setattr(kiwoom_utils.requests, "post", fake_post)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda endpoint: f"https://example.test{endpoint}")

    assert kiwoom_utils.get_kiwoom_token(_config()) == "TOKEN_1"
    assert kiwoom_utils.get_kiwoom_token(_config(), force_refresh=True) == "TOKEN_2"
    assert len(calls) == 2


def test_ws_token_refresh_uses_force_refresh(monkeypatch):
    calls = []

    def fake_get_token(conf, **kwargs):
        calls.append(kwargs)
        return "NEW_TOKEN"

    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", fake_get_token)

    manager = KiwoomWSManager("OLD_TOKEN")
    assert manager._refresh_ws_token() is True
    assert manager.token == "NEW_TOKEN"
    assert calls == [{"force_refresh": True}]


def test_fetch_kiwoom_api_continuous_refreshes_and_retries_once_on_8005(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
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
        posts.append({"url": url, "headers": dict(headers or {}), "payload": json, "timeout": timeout})
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
    assert invalidations == ["api_8005_retry:kt00008"]


def test_fetch_kiwoom_api_continuous_stops_after_single_8005_refresh_retry(monkeypatch):
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
    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FRESH_TOKEN")
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True)

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


def test_fetch_kiwoom_api_continuous_recognizes_rt_cd_8005(monkeypatch):
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
    monkeypatch.setattr(kiwoom_utils, "get_kiwoom_token", lambda *args, **kwargs: "FRESH_TOKEN")
    monkeypatch.setattr(kiwoom_utils, "log_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "log_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True)

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


def test_fetch_kiwoom_api_continuous_returns_8005_when_refresh_raises(monkeypatch):
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
    monkeypatch.setattr(kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True)

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
