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
