from __future__ import annotations

import pandas as pd

from src.engine.swing.bottom_rebound_pattern_research import (
    DECISION_AUTHORITY,
    ResearchConfig,
    _aggregate_label_rows,
    _apply_backtest_rank_score,
    _apply_kiwoom_enrichment_to_candidates,
    _build_kiwoom_enrichment,
    _build_portfolio_backtest,
    _dedupe_examples,
    build_research_report_from_frame,
    label_signal,
    mark_bottom_rebound_candidates,
    prepare_feature_frame,
)


def _synthetic_quotes(days: int = 150) -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2025-01-01", periods=days, freq="D")
    for code, name, base in [("000001", "Alpha", 12000.0), ("000002", "Beta", 7000.0)]:
        for idx, quote_date in enumerate(dates):
            if code == "000001":
                if idx < 90:
                    close = base - idx * 30
                elif idx < 125:
                    close = 9300.0 + ((idx % 5) - 2) * 35.0
                else:
                    close = 9400.0 + (idx - 125) * 20.0
            else:
                close = base + idx * 8.0
            open_price = close * 0.998
            high_price = close * 1.018
            low_price = close * 0.982
            volume = 120000.0 if code == "000001" else 90000.0
            rows.append(
                {
                    "quote_date": quote_date,
                    "stock_code": code,
                    "stock_name": name,
                    "open_price": open_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "close_price": close,
                    "volume": volume,
                    "ma5": None,
                    "ma20": None,
                    "ma60": None,
                    "ma120": None,
                    "rsi": 38.0 if code == "000001" else 55.0,
                    "bbp": 0.25 if code == "000001" else 0.55,
                    "vwap": close * 1.01,
                    "atr": close * 0.025,
                    "foreign_net": 8000.0 if idx % 3 else -1000.0,
                    "inst_net": 3000.0 if idx % 4 else -1000.0,
                    "margin_rate": 0.0,
                }
            )
    return pd.DataFrame(rows)


def test_feature_generation_is_per_stock_without_cross_stock_leakage() -> None:
    raw = _synthetic_quotes()
    features = prepare_feature_frame(raw)

    alpha = features[features["stock_code"].eq("000001")].reset_index(drop=True)
    beta = features[features["stock_code"].eq("000002")].reset_index(drop=True)

    assert int(alpha["history_count"].iloc[-1]) == 150
    assert int(beta["history_count"].iloc[-1]) == 150
    assert alpha["low60"].iloc[-1] != beta["low60"].iloc[-1]
    assert alpha["high60"].iloc[-1] != beta["high60"].iloc[-1]


def test_signal_features_do_not_use_future_rows() -> None:
    raw = _synthetic_quotes()
    signal_date = pd.Timestamp("2025-05-20")
    full = prepare_feature_frame(raw)
    truncated = prepare_feature_frame(raw[raw["quote_date"].le(signal_date)])

    full_row = full[(full["stock_code"].eq("000001")) & (full["quote_date"].eq(signal_date))].iloc[0]
    truncated_row = truncated[(truncated["stock_code"].eq("000001")) & (truncated["quote_date"].eq(signal_date))].iloc[0]

    for column in ["drawdown_high60_pct", "dist_low60_pct", "volume_ratio20", "foreign_roll20_ratio"]:
        assert round(float(full_row[column]), 8) == round(float(truncated_row[column]), 8)


def test_backtest_rank_score_does_not_use_future_rows() -> None:
    raw = _synthetic_quotes()
    signal_date = pd.Timestamp("2025-05-20")
    full = _apply_backtest_rank_score(prepare_feature_frame(raw))
    truncated = _apply_backtest_rank_score(prepare_feature_frame(raw[raw["quote_date"].le(signal_date)]))

    full_row = full[(full["stock_code"].eq("000001")) & (full["quote_date"].eq(signal_date))].iloc[0]
    truncated_row = truncated[(truncated["stock_code"].eq("000001")) & (truncated["quote_date"].eq(signal_date))].iloc[0]

    assert round(float(full_row["backtest_rank_score"]), 8) == round(float(truncated_row["backtest_rank_score"]), 8)


def test_entry_policies_cover_filled_expired_and_pending_states() -> None:
    raw = _synthetic_quotes()
    features = prepare_feature_frame(raw)
    signal = features[features["stock_code"].eq("000001")].iloc[130]
    future = features[features["stock_code"].eq("000001")].iloc[131:132].copy()
    future.loc[future.index[0], "open_price"] = signal["close_price"] * 1.01
    future.loc[future.index[0], "high_price"] = signal["close_price"] * 1.02
    future.loc[future.index[0], "low_price"] = signal["close_price"] * 0.990

    labels = label_signal(signal, future, config=ResearchConfig(), horizons=[1])
    by_policy = {row["entry_policy"]: row for row in labels}

    assert by_policy["next_open_entry"]["label_status"] == "labeled"
    assert by_policy["signal_close_retest_entry"]["label_status"] == "labeled"
    assert by_policy["atr_pullback_entry"]["entry_status"] == "expired"
    assert by_policy["open_guarded_retest_entry"]["label_status"] == "labeled"
    assert by_policy["close_zone_limit_entry"]["label_status"] == "labeled"

    pending = label_signal(signal, future.iloc[0:0], config=ResearchConfig(), horizons=[1])
    assert {row["label_status"] for row in pending} == {"pending_future_quotes"}


def test_open_guarded_entry_blocks_extreme_gap_up() -> None:
    raw = _synthetic_quotes()
    features = prepare_feature_frame(raw)
    signal = features[features["stock_code"].eq("000001")].iloc[130]
    future = features[features["stock_code"].eq("000001")].iloc[131:132].copy()
    future.loc[future.index[0], "open_price"] = signal["close_price"] * 1.05
    future.loc[future.index[0], "high_price"] = signal["close_price"] * 1.06
    future.loc[future.index[0], "low_price"] = signal["close_price"] * 0.99

    labels = label_signal(
        signal,
        future,
        config=ResearchConfig(),
        entry_policies=["open_guarded_retest_entry"],
        horizons=[1],
    )

    assert labels[0]["entry_status"] == "expired"
    assert labels[0]["entry_reason"] == "open_guarded_gap_up_blocked"


def test_report_contract_and_research_only_forbidden_uses() -> None:
    report = build_research_report_from_frame(_synthetic_quotes(), ResearchConfig(sample_floor=2))

    assert report["decision_authority"] == DECISION_AUTHORITY
    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True
    assert report["allowed_runtime_apply"] is False
    assert report["metric_contract"]["primary_decision_metric"] == "source_quality_adjusted_ev_pct"
    assert "broker_order_submit" in report["metric_contract"]["forbidden_uses"]
    assert report["summary"]["signal_rows"] > 0
    assert report["entry_policy_comparison"]
    assert report["portfolio_backtest"]["config"]["entry_policy"] == "atr_pullback_entry"
    assert report["portfolio_backtest"]["summary"]["trade_count"] > 0
    assert report["summary"]["backtest_trade_count"] == report["portfolio_backtest"]["summary"]["trade_count"]
    assert report["portfolio_backtest_variants"]
    assert "market_regime_bucket" in report["feature_bucket_ev_tables"]


def test_bucket_aggregation_applies_sample_floor_to_adjusted_ev() -> None:
    rows = [
        {
            "entry_policy": "next_open_entry",
            "horizon_days": 10,
            "label_status": "labeled",
            "final_return_pct": 10.0,
            "mfe_pct": 12.0,
            "mae_pct": -2.0,
        }
    ]
    aggregated = _aggregate_label_rows(rows, group_keys=["entry_policy", "horizon_days"], sample_floor=4)

    assert aggregated[0]["equal_weight_avg_profit_pct"] == 10.0
    assert aggregated[0]["source_quality_adjusted_ev_pct"] == 2.5


def test_candidate_marking_finds_bottom_rebound_signals() -> None:
    features = prepare_feature_frame(_synthetic_quotes())
    marked = mark_bottom_rebound_candidates(features, ResearchConfig(sample_floor=2))
    alpha_signals = marked[marked["stock_code"].eq("000001") & marked["is_bottom_rebound_signal"]]
    beta_signals = marked[marked["stock_code"].eq("000002") & marked["is_bottom_rebound_signal"]]

    assert not alpha_signals.empty
    assert beta_signals.empty


def test_example_dedupe_uses_trading_day_history_count() -> None:
    signals = pd.DataFrame(
        [
            {"stock_code": "000001", "quote_date": pd.Timestamp("2025-01-01"), "history_count": 120},
            {"stock_code": "000001", "quote_date": pd.Timestamp("2025-01-02"), "history_count": 125},
            {"stock_code": "000001", "quote_date": pd.Timestamp("2025-01-03"), "history_count": 130},
        ]
    )

    deduped = _dedupe_examples(signals, cooldown_days=10)

    assert deduped["history_count"].tolist() == [120, 130]


def test_portfolio_backtest_applies_capacity_and_trade_costs() -> None:
    labels = pd.DataFrame(
        [
            {
                "signal_date": "2025-01-01",
                "entry_date": "2025-01-02",
                "exit_date": "2025-01-12",
                "stock_code": "000001",
                "stock_name": "Alpha",
                "entry_policy": "atr_pullback_entry",
                "horizon_days": 10,
                "entry_status": "entered",
                "label_status": "labeled",
                "entry_price": 1000.0,
                "final_return_pct": 10.0,
                "backtest_rank_score": 2.0,
            },
            {
                "signal_date": "2025-01-01",
                "entry_date": "2025-01-02",
                "exit_date": "2025-01-12",
                "stock_code": "000002",
                "stock_name": "Beta",
                "entry_policy": "atr_pullback_entry",
                "horizon_days": 10,
                "entry_status": "entered",
                "label_status": "labeled",
                "entry_price": 1000.0,
                "final_return_pct": 5.0,
                "backtest_rank_score": 1.0,
            },
            {
                "signal_date": "2025-01-01",
                "entry_date": "2025-01-02",
                "exit_date": "2025-01-12",
                "stock_code": "000003",
                "stock_name": "Gamma",
                "entry_policy": "atr_pullback_entry",
                "horizon_days": 10,
                "entry_status": "entered",
                "label_status": "labeled",
                "entry_price": 1000.0,
                "final_return_pct": 20.0,
                "backtest_rank_score": 0.5,
            },
        ]
    )

    backtest = _build_portfolio_backtest(
        labels,
        ResearchConfig(backtest_max_positions=2, backtest_trade_cost_pct=0.25),
    )

    assert backtest["summary"]["trade_count"] == 2
    assert backtest["summary"]["skipped_capacity_count"] == 1
    assert [trade["stock_code"] for trade in backtest["trades"]] == ["000001", "000002"]
    assert backtest["trades"][0]["net_return_pct"] == 9.75


def test_kiwoom_enrichment_is_disabled_by_default() -> None:
    enrichment = _build_kiwoom_enrichment(
        [{"stock_code": "000001"}],
        target_date="2025-01-31",
        config=ResearchConfig(),
    )

    assert enrichment["enabled"] is False
    assert enrichment["requested_code_count"] == 0
    assert enrichment["rows_by_code"] == {}


def test_kiwoom_enrichment_maps_latest_candidates(monkeypatch) -> None:
    from src.engine import swing_sector_theme_source

    calls = {}

    def fake_build_sector_theme_map(codes, *, target_date, allow_external, write_cache):
        calls["codes"] = list(codes)
        calls["target_date"] = target_date
        calls["allow_external"] = allow_external
        calls["write_cache"] = write_cache
        return {
            "report_type": "swing_sector_theme_source",
            "requested_code_count": len(codes),
            "mapped_code_count": 1,
            "sector_mapped_count": 1,
            "theme_mapped_count": 1,
            "rows_by_code": {
                "000001": {
                    "sector": "Semiconductor",
                    "industry": "Fabless",
                    "market_type": "KOSDAQ",
                    "theme_tags": ["AI", "HPC"],
                    "sector_source_quality": "ok",
                    "theme_source_quality": "ok",
                }
            },
            "diagnostics": {"kiwoom": {"status": "ok"}},
            "warnings": [],
        }

    monkeypatch.setattr(swing_sector_theme_source, "build_sector_theme_map", fake_build_sector_theme_map)
    candidates = [{"stock_code": "000001", "stock_name": "Alpha"}, {"stock_code": "000002", "stock_name": "Beta"}]
    config = ResearchConfig(
        enable_kiwoom_enrichment=True,
        kiwoom_enrichment_max_codes=1,
        kiwoom_enrichment_write_cache=False,
    )

    enrichment = _build_kiwoom_enrichment(candidates, target_date="2025-01-31", config=config)
    enriched = _apply_kiwoom_enrichment_to_candidates(candidates, enrichment)

    assert calls == {
        "codes": ["000001"],
        "target_date": "2025-01-31",
        "allow_external": False,
        "write_cache": False,
    }
    assert enrichment["mapped_code_count"] == 1
    assert enriched[0]["kiwoom_sector"] == "Semiconductor"
    assert enriched[0]["kiwoom_theme_tags"] == ["AI", "HPC"]
    assert "kiwoom_sector" not in enriched[1]
