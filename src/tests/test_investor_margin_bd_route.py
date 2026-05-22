from __future__ import annotations

from flask import Flask

from src.web.bd_fbuy_accum_pre_routes import bd_fbuy_accum_pre_bp


def test_investor_margin_default_renders_bd_screen(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(bd_fbuy_accum_pre_bp)

    monkeypatch.setattr(
        "src.web.bd_fbuy_accum_pre_routes.load_or_build_report",
        lambda *args, **kwargs: {
            "schema_version": "BD_FBUY_ACCUM_PRE_V1",
            "target_date": "2026-05-22",
            "effective_db_date": "2026-05-21",
            "generated_at": "2026-05-22T09:10:00",
            "decision_authority": "query_only",
            "runtime_effect": False,
            "broker_order_forbidden": True,
            "summary": {
                "db_pass_count": 1,
                "rebound_expansion_count": 1,
                "live_confirmed_count": 0,
                "source_quality_counts": {"missing_ws_snapshot": 1},
            },
            "candidates": [
                {
                    "stock_code": "011200",
                    "stock_name": "HMM",
                    "star_display": "★★★★☆",
                    "star_score": 4.2,
                    "close_price": 20250,
                    "dist_low20_pct": 5.97,
                    "dist_ma5_pct": 1.67,
                    "foreign_positive_streak": 3,
                    "foreign_qty_medvol20_ratio": 0.576,
                    "foreign_amt_medvalue20_ratio": 0.569,
                    "vol_med20_ratio": 1.24,
                    "volume_bucket": "active",
                    "traded_value": 32_120_000_000,
                    "med_value20": 26_160_000_000,
                    "liquidity_bucket": "liquid",
                    "foreign_net": 734518,
                    "live_confirmation": {"source_quality": "missing_ws_snapshot"},
                    "history": {"price": [], "volume": [], "foreign": []},
                }
            ],
            "rebound_expansion_candidates": [
                {
                    "stock_code": "018880",
                    "stock_name": "한온시스템",
                    "star_display": "★★★☆☆",
                    "star_score": 3.9,
                    "close_price": 4835,
                    "dist_low20_pct": 32.47,
                    "dist_ma5_pct": 2.0,
                    "foreign_positive_streak": 3,
                    "foreign_qty_medvol20_ratio": 0.213,
                    "foreign_amt_medvalue20_ratio": 0.248,
                    "vol_med20_ratio": 1.65,
                    "volume_bucket": "excluded",
                    "traded_value": 100_900_000_000,
                    "med_value20": 52_400_000_000,
                    "liquidity_bucket": "liquid",
                    "live_confirmation": {"source_quality": "missing_ws_snapshot"},
                    "history": {"price": [], "volume": [], "foreign": []},
                }
            ],
        },
    )

    client = app.test_client()
    response = client.get("/investor-margin?date=2026-05-22")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "BD_FBUY_ACCUM_PRE_V1" in body
    assert "HMM" in body
    assert "이미 반등이 시작됐고 외인이 거래량을 동반해 따라붙는 후보" in body
    assert "한온시스템" in body
    assert "broker_order_forbidden=True" not in body


def test_investor_margin_bd_api_returns_cache_payload(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(bd_fbuy_accum_pre_bp)

    monkeypatch.setattr(
        "src.web.bd_fbuy_accum_pre_routes.load_or_build_report",
        lambda *args, **kwargs: {
            "schema_version": "BD_FBUY_ACCUM_PRE_V1",
            "target_date": "2026-05-22",
            "summary": {"db_pass_count": 0},
            "candidates": [],
            "rebound_expansion_candidates": [],
        },
    )

    payload = app.test_client().get("/api/investor-margin?mode=bd_fbuy_accum_pre").get_json()

    assert payload["ok"] is True
    assert payload["mode"] == "bd_fbuy_accum_pre"
    assert payload["schema_version"] == "BD_FBUY_ACCUM_PRE_V1"
