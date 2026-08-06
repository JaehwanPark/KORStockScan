from __future__ import annotations

from datetime import datetime

from flask import Flask

from src.engine.monitoring.samsung_widget_contract import KST
from src.web import hanwha_ocean_price_widget_routes as routes


def _client(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_ACCESS_KEY", "secret")
    monkeypatch.setenv(
        "KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_SNAPSHOT_PATH",
        "/tmp/no-hanwha_ocean-snapshot.json",
    )
    app = Flask(__name__)
    app.register_blueprint(routes.hanwha_ocean_price_widget_bp)
    return app.test_client()


def test_route_rejects_wrong_access_key(monkeypatch):
    client = _client(monkeypatch)
    assert client.get("/api/widget/hanwha-ocean-price").status_code == 401
    assert (
        client.get(
            "/api/widget/hanwha-ocean-price",
            headers={"X-KORStockScan-Widget-Key": "wrong"},
        ).status_code
        == 401
    )


def test_route_uses_cached_token_and_quote_only_fallback(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(
        routes,
        "_now_kst",
        lambda: datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST),
    )
    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )
    captured = []

    class Client:
        def __init__(self, token):
            assert token == "TOKEN"

        def post(self, path, api_id, payload):
            captured.append((path, api_id, payload))
            return {"cur_prc": "68200", "low_pric": "67000"}

    monkeypatch.setattr(routes, "KiwoomReadOnlyClient", Client)
    response = client.get(
        "/api/widget/hanwha-ocean-price",
        headers={"X-KORStockScan-Widget-Key": "secret"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["symbol"] == "042660"
    assert payload["current_price"] == 68_200
    assert payload["advisory"]["state"] == "DATA_WAIT"
    assert payload["advisory"]["runtime_effect"] is False
    assert captured == [("/api/dostk/stkinfo", "ka10001", {"stk_cd": "042660"})]


def test_hanwha_ocean_dedicated_key_file_precedes_shared_direct_key(
    monkeypatch, tmp_path
):
    key_file = tmp_path / "hanwha_ocean.key"
    key_file.write_text("dedicated-file-key\n", encoding="utf-8")
    monkeypatch.delenv("KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_ACCESS_KEY", raising=False)
    monkeypatch.setenv(
        "KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_ACCESS_KEY_FILE", str(key_file)
    )
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY", "shared-direct-key")

    assert routes._widget_access_key() == "dedicated-file-key"


def test_fresh_snapshot_strips_invalid_public_event(monkeypatch):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = {
        "schema_version": 1,
        "status": "ok",
        "symbol": "042660",
        "current_price": 68_200,
        "token_mode": "shared_cache_only",
        "quote_request_code": "042660",
        "market_venue": "KRX",
        "market_cohort": "KRX",
        "strategy_profile": "HANWHA_OCEAN_VWAP_FIRST_PULLBACK_V1",
        "observed_at_kst": now.isoformat(),
        "advisory": {},
        "exit_advisory": {},
        "entry_event": {"runtime_effect": True},
        "exit_event": None,
    }
    monkeypatch.setattr(routes.contract, "load_snapshot", lambda _path: source)
    monkeypatch.setattr(
        routes.contract, "snapshot_is_fresh", lambda *_args, **_kwargs: True
    )
    monkeypatch.setattr(
        routes.contract, "advisory_contract_is_valid", lambda *_args, **_kwargs: True
    )
    monkeypatch.setattr(
        routes.contract,
        "exit_advisory_contract_is_valid",
        lambda *_args, **_kwargs: True,
    )

    result = routes._fresh_snapshot(now)

    assert result is not None
    assert result["entry_event"] is None
    assert source["entry_event"] == {"runtime_effect": True}
