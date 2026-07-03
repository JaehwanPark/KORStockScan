from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.engine import bd_fbuy_accum_pre_scanner as mod


def _rows_for_code(
    code: str,
    name: str,
    *,
    volume: int = 120_000,
    close: int = 10_000,
    foreign_net: int = 18_000,
    days: int = 65,
) -> list[dict]:
    start = date(2026, 3, 18)
    rows = []
    for i in range(days):
        d = start + timedelta(days=i)
        low = close * 0.97
        rows.append(
            {
                "quote_date": d.isoformat(),
                "stock_code": code,
                "stock_name": name,
                "open_price": close * 0.99,
                "high_price": close * 1.02,
                "low_price": low,
                "close_price": close,
                "volume": volume,
                "ma5": close * 0.998,
                "foreign_net": foreign_net if i >= days - 3 else -1000,
            }
        )
    return rows


def test_db_pass_conditions_include_inflow_streak_volume_and_liquidity():
    df = pd.DataFrame(_rows_for_code("011200", "HMM"))
    frame = mod._prepare_candidate_frame(df)
    passed = mod.filter_pass_candidates(frame)

    assert len(passed) == 1
    row = passed.iloc[0]
    assert row["foreign_positive_streak"] >= 2
    assert row["foreign_qty_medvol20_ratio"] >= 0.10
    assert row["traded_value"] >= 500_000_000


def test_thin_absolute_liquidity_is_rejected_even_when_ratios_pass():
    df = pd.DataFrame(_rows_for_code("221980", "케이디켐", volume=1_500, close=10_000, foreign_net=300))
    frame = mod._prepare_candidate_frame(df)
    passed = mod.filter_pass_candidates(frame)

    assert passed.empty


def test_volume_spike_is_rejected_by_upper_band():
    rows = _rows_for_code("215100", "로보로보", volume=120_000, close=10_000, foreign_net=18_000)
    for row in rows[-1:]:
        row["volume"] = 240_000
    df = pd.DataFrame(rows)
    frame = mod._prepare_candidate_frame(df)
    passed = mod.filter_pass_candidates(frame)

    assert passed.empty


def test_star_score_components_and_live_adjustments_are_clamped():
    row = {
        "foreign_qty_medvol20_ratio": 0.35,
        "foreign_amt_medvalue20_ratio": 0.31,
        "foreign_positive_streak": 6,
        "dist_low20_pct": 2.5,
        "vol_med20_ratio": 1.0,
        "traded_value": 6_000_000_000,
        "med_value20": 7_000_000_000,
    }
    score = mod.compute_star_scores(
        row,
        {
            "today_foreign_broker_est_net_qty": 10,
            "price_above_vwap": True,
            "spread_ok": True,
        },
    )

    assert score["star_score"] == 5.0
    assert score["foreign_inflow_score"] == 1.5
    assert score["liquidity_score"] == 0.75


def test_runtime_forbidden_contract_is_preserved(monkeypatch, tmp_path):
    df = pd.DataFrame(_rows_for_code("011200", "HMM"))

    monkeypatch.setattr(mod, "_load_daily_quotes", lambda db_url, target: (df, "2026-05-21"))
    monkeypatch.setattr(mod, "ARTIFACT_DIR", tmp_path)

    report = mod.build_report("2026-05-21", db_url=mod.POSTGRES_URL, write=True)

    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True
    assert report["allowed_runtime_apply"] is False
    assert report["summary"]["db_pass_count"] == 1


def test_rebound_expansion_candidates_capture_hanon_type():
    df = pd.DataFrame(_rows_for_code("018880", "한온시스템", volume=120_000, close=10_000, foreign_net=20_000))
    frame = mod._prepare_candidate_frame(df)
    frame.loc[:, "dist_low20_pct"] = 32.0
    frame.loc[:, "vol_med20_ratio"] = 1.65
    frame.loc[:, "traded_value"] = 100_000_000_000
    frame.loc[:, "med_value20"] = 52_000_000_000

    passed = mod.filter_rebound_expansion_candidates(frame)
    score = mod.compute_rebound_expansion_scores(passed.iloc[0].to_dict())

    assert len(passed) == 1
    assert score["star_score"] >= 3.0
    assert score["rebound_position_score"] > 0


def test_daily_db_fallback_replaces_missing_ws_when_live_enabled(monkeypatch):
    monkeypatch.setattr(mod, "_load_ws_snapshot", lambda: {})
    rows = [
        {
            "stock_code": "011200",
            "quote_date": "2026-05-21",
            "foreign_net": 12345,
            "foreign_qty_medvol20_ratio": 0.2,
            "foreign_amt_medvalue20_ratio": 0.2,
        }
    ]

    mod._apply_live_confirmation(rows, live_intraday=True)

    live = rows[0]["live_confirmation"]
    assert live["source"] == "daily_stock_quotes"
    assert live["source_quality"] == "daily_db_fallback"
    assert live["fallback_from_source_quality"] == "missing_ws_snapshot"
    assert live["daily_foreign_net_qty"] == 12345
    assert rows[0]["live_confirmed"] is True
