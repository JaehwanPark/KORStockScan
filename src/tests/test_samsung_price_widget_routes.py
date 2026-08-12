from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask

from src.web import samsung_price_widget_routes as routes


class _FakeResponse:
    status_code = 200
    content = b"{}"

    def json(self):
        return {"return_code": 0, "cur_prc": "+71,200", "low_pric": "70,800"}


class _MissingReturnCodeResponse(_FakeResponse):
    def json(self):
        return {"cur_prc": "+71,200"}


def _client(monkeypatch):
    routes._reset_position_cache_for_test()
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY", "widget-secret")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH",
        "/tmp/korstockscan-test-no-widget-snapshot.json",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SAMSUNG_WIDGET_WS_SNAPSHOT_PATH",
        "/tmp/korstockscan-test-no-widget-ws-snapshot.json",
    )
    app = Flask(__name__)
    app.register_blueprint(routes.samsung_price_widget_bp)
    return app.test_client()


def test_websocket_price_comparison_accepts_fresh_shared_0b(monkeypatch, tmp_path):
    now = datetime(2026, 8, 13, 9, 20, tzinfo=ZoneInfo("Asia/Seoul"))
    snapshot_path = tmp_path / "ws.json"
    snapshot_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "stocks": {
                    "005930": {
                        "curr": 242_500,
                        "last_realtime_type_ts": {"0B": now.timestamp() - 0.4},
                        "last_realtime_type_item": {"0B": "005930_AL"},
                        "last_trade_tick": {
                            "price": 242_500,
                            "ts": now.timestamp() - 0.4,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SAMSUNG_WIDGET_WS_SNAPSHOT_PATH", str(snapshot_path)
    )

    comparison = routes._websocket_price_comparison(
        reference_price=242_000, observed_at=now
    )

    assert comparison["status"] == "OK"
    assert comparison["current_price"] == 242_500
    assert comparison["price_delta"] == 500
    assert comparison["market_route"] == "SOR"
    assert comparison["age_ms"] == 400.0
    assert comparison["used_for_manual_order"] is False
    assert comparison["runtime_effect"] is False


def test_websocket_price_comparison_rejects_stale_0b(monkeypatch, tmp_path):
    now = datetime(2026, 8, 13, 9, 20, tzinfo=ZoneInfo("Asia/Seoul"))
    snapshot_path = tmp_path / "ws.json"
    snapshot_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "stocks": {
                    "005930": {
                        "curr": 242_500,
                        "last_realtime_type_ts": {"0B": now.timestamp() - 5.1},
                        "last_realtime_type_item": {"0B": "005930_AL"},
                        "last_trade_tick": {
                            "price": 242_500,
                            "ts": now.timestamp() - 5.1,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SAMSUNG_WIDGET_WS_SNAPSHOT_PATH", str(snapshot_path)
    )

    comparison = routes._websocket_price_comparison(
        reference_price=242_000, observed_at=now
    )

    assert comparison["status"] == "UNAVAILABLE"
    assert comparison["reason"] == "samsung_0b_stale"


def test_websocket_price_comparison_rejects_unknown_samsung_item(monkeypatch, tmp_path):
    now = datetime(2026, 8, 13, 9, 20, tzinfo=ZoneInfo("Asia/Seoul"))
    snapshot_path = tmp_path / "ws.json"
    snapshot_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "stocks": {
                    "005930": {
                        "last_realtime_type_ts": {"0B": now.timestamp()},
                        "last_realtime_type_item": {"0B": "005930_BAD"},
                        "last_trade_tick": {
                            "price": 242_500,
                            "ts": now.timestamp(),
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SAMSUNG_WIDGET_WS_SNAPSHOT_PATH", str(snapshot_path)
    )

    comparison = routes._websocket_price_comparison(
        reference_price=242_000, observed_at=now
    )

    assert comparison["status"] == "UNAVAILABLE"
    assert comparison["reason"] == "samsung_0b_item_mismatch"


def test_samsung_widget_rejects_missing_or_wrong_access_key(monkeypatch):
    client = _client(monkeypatch)

    assert client.get("/api/widget/samsung-price").status_code == 401
    assert (
        client.get(
            "/api/widget/samsung-price",
            headers={"X-KORStockScan-Widget-Key": "wrong"},
        ).status_code
        == 401
    )


def test_samsung_widget_reads_access_key_from_aws_only_file(monkeypatch, tmp_path):
    key_path = tmp_path / "widget.key"
    key_path.write_text("file-only-secret\n", encoding="utf-8")
    monkeypatch.delenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY", raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE", str(key_path))

    app = Flask(__name__)
    app.register_blueprint(routes.samsung_price_widget_bp)
    client = app.test_client()

    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "wrong"},
    )

    assert response.status_code == 401
    assert routes._widget_access_key() == "file-only-secret"


def test_samsung_widget_uses_cached_token_only_and_returns_quote(monkeypatch):
    client = _client(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        routes,
        "_now_kst",
        lambda: datetime(2026, 7, 28, 10, 3, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )

    def fail_if_issued(*args, **kwargs):
        raise AssertionError("widget endpoint must never issue a Kiwoom token")

    monkeypatch.setattr(routes.kiwoom_utils, "get_kiwoom_token", fail_if_issued)
    monkeypatch.setattr(
        routes.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://api.example.test{path}",
    )

    def fake_post(url, *, headers, json, timeout):
        captured.setdefault("calls", []).append(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        response = _FakeResponse()
        if headers["api-id"] == "kt00018":
            response.json = lambda: {
                "return_code": 0,
                "acnt_evlt_remn_indv_tot": [
                    {
                        "stk_cd": "A005930",
                        "stk_nm": "삼성전자",
                        "rmnd_qty": "000000000003",
                        "pur_pric": "000000231500",
                    }
                ],
            }
        if headers["api-id"] == "ka10080":
            response.json = lambda: {
                "return_code": 0,
                "stk_min_pole_chart_qry": [
                    {"cntr_tm": "20260728100000", "cur_prc": "70000"},
                    {"cntr_tm": "20260728100100", "cur_prc": "70500"},
                    {"cntr_tm": "20260728100200", "cur_prc": "71000"},
                ],
            }
        return response

    monkeypatch.setattr(routes.requests, "post", fake_post)

    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )
    repeated_response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )

    assert response.status_code == 200
    assert repeated_response.status_code == 200
    assert repeated_response.get_json()["current_price"] == 71200
    assert response.get_json()["current_price"] == 71200
    assert response.get_json()["day_low_delta"] == 400
    assert response.get_json()["market_venue"] == "KRX"
    assert response.get_json()["quote_request_code"] == "005930"
    assert response.get_json()["token_mode"] == "shared_cache_only"
    assert response.get_json()["minute_trends"] == {
        "1m": "unavailable",
        "3m": "unavailable",
        "5m": "unavailable",
    }
    assert captured["calls"][0]["url"] == "https://api.example.test/api/dostk/stkinfo"
    assert captured["calls"][0]["headers"]["api-id"] == "ka10001"
    assert captured["calls"][0]["headers"]["authorization"] == "Bearer TOKEN"
    assert captured["calls"][0]["json"] == {"stk_cd": "005930"}
    assert captured["calls"][0]["timeout"] == 5
    assert len(captured["calls"]) == 3
    assert [call["headers"]["api-id"] for call in captured["calls"]] == [
        "ka10001",
        "kt00018",
        "kt00018",
    ]
    assert [call["url"] for call in captured["calls"][1:]] == [
        "https://api.example.test/api/dostk/acnt",
        "https://api.example.test/api/dostk/acnt",
    ]
    assert [call["json"] for call in captured["calls"][1:]] == [
        {"qry_tp": "1", "dmst_stex_tp": "KRX"},
        {"qry_tp": "1", "dmst_stex_tp": "NXT"},
    ]
    assert all(
        call["headers"]["cont-yn"] == "N" and call["headers"]["next-key"] == ""
        for call in captured["calls"][1:]
    )
    assert response.get_json()["position"]["quantity"] == 3
    assert response.get_json()["position"]["average_price"] == 231500
    assert response.get_json()["position"]["runtime_effect"] is False
    assert response.get_json()["advisory"]["state"] == "DATA_WAIT"
    assert response.get_json()["advisory"]["session"] == "KRX_REGULAR"
    assert response.get_json()["advisory"]["runtime_effect"] is False
    assert response.get_json()["exit_advisory"]["state"] == "DATA_WAIT"
    assert response.get_json()["exit_advisory"]["holding_independent"] is True


def test_samsung_widget_uses_nxt_route_after_krx_close(monkeypatch):
    client = _client(monkeypatch)
    captured = []
    monkeypatch.setattr(
        routes,
        "_now_kst",
        lambda: datetime(2026, 7, 28, 16, 10, tzinfo=ZoneInfo("Asia/Seoul")),
    )
    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )

    def fake_post(url, *, headers, json, timeout):
        captured.append({"headers": headers, "json": json})
        response = _FakeResponse()
        if headers["api-id"] == "kt00018":
            response.json = lambda: {
                "return_code": 0,
                "acnt_evlt_remn_indv_tot": [],
            }
        if headers["api-id"] == "ka10080":
            response.json = lambda: {
                "return_code": 0,
                "stk_min_pole_chart_qry": [
                    {"cntr_tm": "20260728160700", "cur_prc": "220500"},
                    {"cntr_tm": "20260728160800", "cur_prc": "221000"},
                    {"cntr_tm": "20260728160900", "cur_prc": "221500"},
                ],
            }
        return response

    monkeypatch.setattr(routes.requests, "post", fake_post)

    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )

    assert response.status_code == 200
    assert response.get_json()["market_venue"] == "NXT"
    assert response.get_json()["market_session"] == "nxt_aftermarket"
    assert response.get_json()["quote_request_code"] == "005930_NX"
    assert response.get_json()["advisory"]["session"] == "NXT_AFTERMARKET"
    assert [
        call["json"]["stk_cd"]
        for call in captured
        if call["headers"]["api-id"] == "ka10001"
    ] == ["005930_NX"]


def test_samsung_widget_uses_nxt_route_during_premarket(monkeypatch):
    client = _client(monkeypatch)
    captured = []
    monkeypatch.setattr(
        routes,
        "_now_kst",
        lambda: datetime(2026, 7, 28, 8, 10, tzinfo=ZoneInfo("Asia/Seoul")),
    )
    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )

    def fake_post(url, *, headers, json, timeout):
        captured.append({"headers": headers, "json": json})
        response = _FakeResponse()
        if headers["api-id"] == "kt00018":
            response.json = lambda: {
                "return_code": 0,
                "acnt_evlt_remn_indv_tot": [],
            }
        if headers["api-id"] == "ka10080":
            response.json = lambda: {
                "return_code": 0,
                "stk_min_pole_chart_qry": [
                    {"cntr_tm": "20260728080700", "cur_prc": "220500"},
                    {"cntr_tm": "20260728080800", "cur_prc": "221000"},
                    {"cntr_tm": "20260728080900", "cur_prc": "221500"},
                ],
            }
        return response

    monkeypatch.setattr(routes.requests, "post", fake_post)

    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )

    assert response.status_code == 200
    assert response.get_json()["market_venue"] == "NXT"
    assert response.get_json()["market_cohort"] == "PREMARKET_KRX_LIKE"
    assert response.get_json()["market_session"] == "krx_like_premarket"
    assert response.get_json()["quote_request_code"] == "005930_NX"
    assert response.get_json()["advisory"]["session"] == "NXT_PREMARKET"
    assert [
        call["json"]["stk_cd"]
        for call in captured
        if call["headers"]["api-id"] == "ka10001"
    ] == ["005930_NX"]


def test_samsung_widget_serves_fresh_collector_snapshot_with_position_overlay(
    monkeypatch, tmp_path
):
    client = _client(monkeypatch)
    now = datetime(2026, 8, 3, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    snapshot_time = now - timedelta(seconds=10)
    monkeypatch.setattr(routes, "_now_kst", lambda: now)
    snapshot_path = tmp_path / "widget-snapshot.json"
    snapshot_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "symbol": "005930",
                "current_price": 100_000,
                "observed_at_kst": snapshot_time.isoformat(),
                "token_mode": "shared_cache_only",
                "market_venue": "KRX",
                "market_cohort": "KRX",
                "quote_request_code": "005930",
                "advisory": {
                    "state": "ENTRY_READY",
                    "raw_state": "ENTRY_READY",
                    "session": "KRX_REGULAR",
                    "entry_price_low": 99_900,
                    "entry_price_high": 100_000,
                    "observed_at": snapshot_time.isoformat(),
                    "valid_until": (snapshot_time + timedelta(seconds=60)).isoformat(),
                    "source_quality": {"status": "PASS", "issues": []},
                    "authority": "widget_advisory_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH", str(snapshot_path))

    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )
    monkeypatch.setattr(
        routes,
        "_cached_samsung_position",
        lambda token, observed_at: routes._position_contract_payload(
            status="OK",
            observed_at=observed_at,
            quantity=7,
            average_price=232_000,
            source_exchanges=["KRX", "NXT"],
        ),
    )
    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )
    assert response.status_code == 200
    assert response.get_json()["advisory"]["state"] == "ENTRY_READY"
    assert response.get_json()["position"]["quantity"] == 7


def test_samsung_widget_rejects_snapshot_with_expired_inner_advisory(
    monkeypatch, tmp_path
):
    now = datetime(2026, 8, 3, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    snapshot_path = tmp_path / "widget-snapshot.json"
    snapshot_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "symbol": "005930",
                "current_price": 100_000,
                "observed_at_kst": now.isoformat(),
                "token_mode": "shared_cache_only",
                "market_venue": "KRX",
                "market_cohort": "KRX",
                "quote_request_code": "005930",
                "advisory": {
                    "state": "ENTRY_READY",
                    "raw_state": "ENTRY_READY",
                    "session": "KRX_REGULAR",
                    "entry_price_low": 99_900,
                    "entry_price_high": 100_000,
                    "observed_at": now.isoformat(),
                    "valid_until": (now - timedelta(seconds=1)).isoformat(),
                    "source_quality": {"status": "PASS", "issues": []},
                    "authority": "widget_advisory_only",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH", str(snapshot_path))

    assert routes._fresh_collector_snapshot(now) is None


def test_samsung_widget_rejects_snapshot_with_runtime_exit_authority(
    monkeypatch, tmp_path
):
    now = datetime(2026, 8, 3, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    snapshot = {
        "schema_version": 1,
        "status": "ok",
        "symbol": "005930",
        "current_price": 100_000,
        "observed_at_kst": now.isoformat(),
        "token_mode": "shared_cache_only",
        "market_venue": "KRX",
        "market_cohort": "KRX",
        "quote_request_code": "005930",
        "advisory": {
            "state": "WATCH",
            "raw_state": "WATCH",
            "session": "KRX_REGULAR",
            "entry_price_low": None,
            "entry_price_high": None,
            "observed_at": now.isoformat(),
            "valid_until": (now + timedelta(seconds=60)).isoformat(),
            "source_quality": {"status": "PASS", "issues": []},
            "authority": "widget_advisory_only",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "exit_advisory": {
            "state": "EXIT_READY",
            "session": "KRX_REGULAR",
            "reference_exit_price": 99_900,
            "peak_price": 101_000,
            "broken_support": 100_000,
            "observed_at": now.isoformat(),
            "valid_until": (now + timedelta(seconds=60)).isoformat(),
            "source_quality": {"status": "PASS", "issues": []},
            "holding_independent": True,
            "authority": "widget_advisory_only",
            "runtime_effect": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    snapshot_path = tmp_path / "widget-snapshot.json"
    snapshot_path.write_text(__import__("json").dumps(snapshot), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH", str(snapshot_path))

    assert routes._fresh_collector_snapshot(now) is None


def test_samsung_position_uses_krx_first_and_deduplicates_nxt(monkeypatch):
    now = datetime(2026, 8, 12, 10, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    calls = []

    def fake_post(token, *, path, api_id, payload):
        calls.append((path, api_id, payload))
        return {
            "return_code": 0,
            "acnt_evlt_remn_indv_tot": [
                {
                    "stk_cd": "A005930",
                    "rmnd_qty": "000000000004",
                    "pur_pric": "000000230125",
                }
            ],
        }

    monkeypatch.setattr(routes, "_kiwoom_post", fake_post)

    position = routes._load_samsung_position("TOKEN", now)

    assert position["status"] == "OK"
    assert position["quantity"] == 4
    assert position["average_price"] == 230125
    assert position["source_exchanges"] == ["KRX", "NXT"]
    assert [call[2]["dmst_stex_tp"] for call in calls] == ["KRX", "NXT"]
    assert all(call[2]["qry_tp"] == "1" for call in calls)


def test_samsung_position_fails_closed_on_venue_conflict(monkeypatch):
    now = datetime(2026, 8, 12, 10, 30, tzinfo=ZoneInfo("Asia/Seoul"))

    def fake_post(token, *, path, api_id, payload):
        quantity = "3" if payload["dmst_stex_tp"] == "KRX" else "4"
        return {
            "return_code": 0,
            "acnt_evlt_remn_indv_tot": [
                {"stk_cd": "005930", "rmnd_qty": quantity, "pur_pric": "230000"}
            ],
        }

    monkeypatch.setattr(routes, "_kiwoom_post", fake_post)

    position = routes._load_samsung_position("TOKEN", now)

    assert position["status"] == "UNAVAILABLE"
    assert position["quantity"] is None
    assert position["reason"] == "venue_position_conflict"


def test_samsung_position_does_not_treat_duplicate_rows_as_zero(monkeypatch):
    now = datetime(2026, 8, 12, 10, 30, tzinfo=ZoneInfo("Asia/Seoul"))

    def fake_post(token, *, path, api_id, payload):
        return {
            "return_code": 0,
            "acnt_evlt_remn_indv_tot": [
                {"stk_cd": "005930", "rmnd_qty": "2", "pur_pric": "230000"},
                {"stk_cd": "A005930", "rmnd_qty": "1", "pur_pric": "229000"},
            ],
        }

    monkeypatch.setattr(routes, "_kiwoom_post", fake_post)

    position = routes._load_samsung_position("TOKEN", now)

    assert position["status"] == "UNAVAILABLE"
    assert position["quantity"] is None
    assert position["reason"] == "position_contract_invalid"


def test_samsung_position_cache_limits_account_calls(monkeypatch):
    routes._reset_position_cache_for_test()
    now = datetime(2026, 8, 12, 10, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    calls = []

    def fake_load(token, observed_at):
        calls.append((token, observed_at))
        return routes._position_contract_payload(
            status="OK",
            observed_at=observed_at,
            quantity=1,
            average_price=229500,
            source_exchanges=["KRX"],
        )

    monkeypatch.setattr(routes, "_load_samsung_position", fake_load)

    first = routes._cached_samsung_position("TOKEN", now)
    second = routes._cached_samsung_position("TOKEN", now + timedelta(seconds=10))

    assert first["quantity"] == second["quantity"] == 1
    assert len(calls) == 1


def test_quote_route_uses_nxt_only_during_nxt_premarket():
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 7, 59, 59, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930", "KRX", "krx_or_closed")
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 8, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930_NX", "NXT", "krx_like_premarket")
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 8, 49, 59, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930_NX", "NXT", "krx_like_premarket")
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 8, 50, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930", "KRX", "krx_or_closed")


def test_quote_route_uses_nxt_only_during_nxt_aftermarket():
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 15, 39, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930", "KRX", "krx_or_closed")
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 15, 40, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930_NX", "NXT", "nxt_aftermarket")
    assert routes._quote_route_for_observed_at(
        datetime(2026, 7, 28, 20, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    ) == ("005930", "KRX", "krx_or_closed")


def test_samsung_widget_fails_closed_when_shared_token_is_missing(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: None)

    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )

    assert response.status_code == 503
    assert response.get_json()["reason"] == "shared_token_unavailable"


def test_samsung_widget_requires_kiwoom_return_code(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )
    monkeypatch.setattr(
        routes.requests, "post", lambda *args, **kwargs: _MissingReturnCodeResponse()
    )

    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )

    assert response.status_code == 503
    assert response.get_json()["reason"] == "kiwoom_quote_rejected"


class _ManualExecutor:
    def __init__(self):
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "accepted",
            "client_request_id": str(kwargs["client_request_id"]),
            "symbol": "005930",
            "side": str(kwargs["side"]),
            "quantity": int(kwargs["quantity"]),
            "authority": "operator_widget_manual_order_v1",
            "actual_order_submitted": True,
            "expected_order_count": 2,
            "accepted_order_count": 2,
            "orders": [],
        }

    def existing_response(self, **kwargs):
        return None


def _manual_order_client(monkeypatch, tmp_path, *, now, price=230_500):
    client = _client(monkeypatch)
    snapshot_path = tmp_path / "samsung-order-snapshot.json"
    context = routes.samsung_widget_contract.session_context(now)
    snapshot_path.write_text(
        __import__("json").dumps(
            {
                "schema_version": 1,
                "status": "ok",
                "symbol": "005930",
                "current_price": price,
                "observed_at_kst": (now - timedelta(seconds=5)).isoformat(),
                "token_mode": "shared_cache_only",
                "market_venue": context.market_venue,
                "market_cohort": context.market_cohort,
                "quote_request_code": context.request_code,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY", "order-secret")
    monkeypatch.setattr(routes, "_now_kst", lambda: now)
    executor = _ManualExecutor()
    monkeypatch.setattr(routes, "_MANUAL_ORDER_EXECUTOR", executor)
    return client, executor


def test_manual_order_requires_dedicated_order_key(monkeypatch, tmp_path):
    now = datetime(2026, 8, 12, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    client, executor = _manual_order_client(monkeypatch, tmp_path, now=now)
    body = {
        "side": "BUY",
        "quantity": 2,
        "displayed_price": 230_500,
        "client_request_id": "0a1e764d-287f-45db-836d-0685fc14746a",
    }

    assert client.post("/api/widget/samsung-order", json=body).status_code == 401
    assert (
        client.post(
            "/api/widget/samsung-order",
            json=body,
            headers={"X-KORStockScan-Widget-Key": "widget-secret"},
        ).status_code
        == 401
    )
    assert executor.calls == []

    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY", "widget-secret")
    assert (
        client.post(
            "/api/widget/samsung-order",
            json=body,
            headers={"X-KORStockScan-Widget-Order-Key": "widget-secret"},
        ).status_code
        == 401
    )


def test_manual_order_uses_fresh_server_price_and_krx_session(monkeypatch, tmp_path):
    now = datetime(2026, 8, 12, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    client, executor = _manual_order_client(monkeypatch, tmp_path, now=now)

    response = client.post(
        "/api/widget/samsung-order",
        json={
            "side": "BUY",
            "quantity": 3,
            "displayed_price": 230_000,
            "client_request_id": "c2f3d99e-ec9e-4a17-a491-fb12e1e07c02",
        },
        headers={"X-KORStockScan-Widget-Order-Key": "order-secret"},
    )

    assert response.status_code == 200
    assert executor.calls[0]["reference_price"] == 230_500
    assert executor.calls[0]["market_venue"] == "KRX"
    assert executor.calls[0]["session"] == "KRX_REGULAR"


def test_manual_order_rejects_stale_snapshot_and_large_display_drift(
    monkeypatch, tmp_path
):
    now = datetime(2026, 8, 12, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    client, executor = _manual_order_client(monkeypatch, tmp_path, now=now)
    headers = {"X-KORStockScan-Widget-Order-Key": "order-secret"}
    body = {
        "side": "SELL",
        "quantity": 1,
        "displayed_price": 225_000,
        "client_request_id": "8750aba6-4aac-462b-b129-c8654ca2c53e",
    }

    drift = client.post("/api/widget/samsung-order", json=body, headers=headers)
    assert drift.status_code == 409
    assert drift.get_json()["reason"] == "displayed_price_moved_refresh_required"

    snapshot_path = routes._snapshot_path()
    snapshot = __import__("json").loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["observed_at_kst"] = (now - timedelta(seconds=16)).isoformat()
    snapshot_path.write_text(__import__("json").dumps(snapshot), encoding="utf-8")
    body["displayed_price"] = 230_500
    stale = client.post("/api/widget/samsung-order", json=body, headers=headers)
    assert stale.status_code == 409
    assert stale.get_json()["reason"] == "fresh_active_session_snapshot_required"
    assert executor.calls == []


def test_minute_chart_and_trend_use_completed_bars_and_exclude_forming_bar():
    rows = [
        {"cntr_tm": "20260728100000", "cur_prc": "70000"},
        {"cntr_tm": "20260728100100", "cur_prc": "70500"},
        {"cntr_tm": "20260728100200", "cur_prc": "71000"},
        {"cntr_tm": "20260728100300", "cur_prc": "65000"},
    ]

    completed = routes._completed_minute_closes(
        rows,
        observed_at=datetime(2026, 7, 28, 10, 3, 30, tzinfo=ZoneInfo("Asia/Seoul")),
        limit=20,
    )
    trend, trend_at = routes._classify_minute_trend(completed)

    assert completed == [
        ("20260728100000", 70000),
        ("20260728100100", 70500),
        ("20260728100200", 71000),
    ]
    assert trend == "flat"
    assert trend_at == "20260728100200"


def test_minute_trends_classify_contiguous_1m_3m_5m_horizons():
    completed = [
        (f"20260728100{minute}00", 70_000 + minute * 100) for minute in range(7)
    ]

    trends, trend_at = routes._classify_minute_trends(completed)

    assert trends == {"1m": "flat", "3m": "up", "5m": "up"}
    assert trend_at == "20260728100600"


def test_minute_trends_mark_gapped_horizons_unavailable():
    completed = [
        ("20260728100000", 70_000),
        ("20260728100100", 70_100),
        ("20260728100300", 70_200),
        ("20260728100400", 70_300),
    ]

    trends, trend_at = routes._classify_minute_trends(completed)

    assert trends == {"1m": "flat", "3m": "unavailable", "5m": "unavailable"}
    assert trend_at == "20260728100400"


def test_completed_minute_closes_do_not_cross_session_start():
    rows = [
        {"cntr_tm": "20260728153800", "cur_prc": "70,000"},
        {"cntr_tm": "20260728153900", "cur_prc": "70,100"},
        {"cntr_tm": "20260728154000", "cur_prc": "70,200"},
        {"cntr_tm": "20260728154100", "cur_prc": "70,300"},
        {"cntr_tm": "20260728154200", "cur_prc": "70,400"},
    ]

    completed = routes._completed_minute_closes(
        rows,
        observed_at=datetime(
            2026,
            7,
            28,
            15,
            42,
            30,
            tzinfo=ZoneInfo("Asia/Seoul"),
        ),
        limit=20,
        session_start=routes._NXT_AFTERMARKET_START,
    )
    trends, _ = routes._classify_minute_trends(completed)

    assert completed == [
        ("20260728154000", 70_200),
        ("20260728154100", 70_300),
    ]
    assert trends == {"1m": "flat", "3m": "unavailable", "5m": "unavailable"}


def test_minute_trend_uses_flat_band_for_small_net_change():
    completed = [
        ("20260728100000", 70_000),
        ("20260728100100", 70_030),
    ]

    trend, trend_at = routes._classify_horizon_trend(
        completed,
        horizon_minutes=1,
    )

    assert trend == "flat"
    assert trend_at == "20260728100100"
