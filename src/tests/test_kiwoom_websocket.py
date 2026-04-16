import asyncio
import json

import pytest

from src.engine.kiwoom_websocket import KiwoomWSManager


class _FakeWS:
    def __init__(self, messages):
        self._messages = list(messages)
        self.sent = []

    async def recv(self):
        if not self._messages:
            raise asyncio.TimeoutError
        return self._messages.pop(0)

    async def send(self, payload):
        self.sent.append(payload)


def test_login_success_message_helpers():
    success = {"trnm": "LOGIN", "return_code": 0}
    failure = {"trnm": "LOGIN", "return_code": 100}

    assert KiwoomWSManager._is_login_success_message(success) is True
    assert KiwoomWSManager._is_login_failure_message(success) is False
    assert KiwoomWSManager._is_login_success_message(failure) is False
    assert KiwoomWSManager._is_login_failure_message(failure) is True


def test_await_login_ack_handles_ping_then_success():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS(
        [
            json.dumps({"trnm": "PING"}),
            json.dumps({"trnm": "LOGIN", "return_code": 0, "return_msg": "OK"}),
        ]
    )

    asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))

    assert fake_ws.sent == [json.dumps({"trnm": "PONG"})]


def test_await_login_ack_raises_on_login_failure():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS(
        [
            json.dumps({"trnm": "LOGIN", "return_code": 100013, "return_msg": "login pending"}),
        ]
    )

    with pytest.raises(RuntimeError):
        asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))


@pytest.mark.parametrize(
    "code,message,expected",
    [
        ("8005", "Token이 유효하지 않습니다", True),
        ("805004", "토큰 인증에 실패했습니다 [CODE=8005]", True),
        ("100013", "login pending", False),
    ],
)
def test_is_auth_token_failure(code, message, expected):
    assert KiwoomWSManager._is_auth_token_failure(code, message) is expected
