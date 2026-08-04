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
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY", "widget-secret")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SAMSUNG_WIDGET_SNAPSHOT_PATH",
        "/tmp/korstockscan-test-no-widget-snapshot.json",
    )
    app = Flask(__name__)
    app.register_blueprint(routes.samsung_price_widget_bp)
    return app.test_client()


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

    assert response.status_code == 200
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
    assert len(captured["calls"]) == 1
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
    assert [call["json"]["stk_cd"] for call in captured] == ["005930_NX"]


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
    assert [call["json"]["stk_cd"] for call in captured] == ["005930_NX"]


def test_samsung_widget_serves_fresh_collector_snapshot_without_token_call(
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

    def fail_if_token_read(*args, **kwargs):
        raise AssertionError("fresh collector snapshot must not read a token")

    monkeypatch.setattr(
        routes.kiwoom_utils, "get_cached_kiwoom_token", fail_if_token_read
    )
    response = client.get(
        "/api/widget/samsung-price",
        headers={"X-KORStockScan-Widget-Key": "widget-secret"},
    )
    assert response.status_code == 200
    assert response.get_json()["advisory"]["state"] == "ENTRY_READY"


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
