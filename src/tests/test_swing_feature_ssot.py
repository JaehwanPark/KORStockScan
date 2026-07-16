import json

import numpy as np
import pandas as pd

from src.model import common_v2, feature_engineering_v2
from src.utils import update_kospi


def _raw_quote_fixture(rows: int = 80) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=rows, freq="B")
    base = np.linspace(1000.0, 1200.0, rows)
    return pd.DataFrame(
        {
            "quote_date": dates,
            "stock_code": ["000001"] * rows,
            "stock_name": ["SSOT"] * rows,
            "open_price": base,
            "high_price": base * 1.03,
            "low_price": base * 0.98,
            "close_price": base * 1.01,
            "volume": np.linspace(10000, 20000, rows),
            "foreign_net": np.linspace(-100, 100, rows),
            "inst_net": np.linspace(50, 150, rows),
            "margin_rate": np.linspace(2.0, 2.5, rows),
        }
    )


def test_common_v2_reexports_feature_engineering_ssot():
    assert (
        common_v2.calculate_all_features
        is feature_engineering_v2.calculate_all_features
    )


def test_update_kospi_uses_common_v2_feature_facade():
    assert update_kospi.calculate_all_features is common_v2.calculate_all_features


def test_update_kospi_normalizes_ssot_output_for_db_mapping():
    ssot_like = pd.DataFrame(
        {
            "date": [pd.Timestamp("2026-01-02")],
            "code": ["000001"],
            "name": ["SSOT"],
            "open": [1000.0],
            "high": [1030.0],
            "low": [990.0],
            "close": [1010.0],
            "volume": [10000],
            "return_1d": [0.01],
            "vwap20": [1005.0],
            "foreign_net": [100.0],
            "inst_net": [50.0],
            "margin_rate": [2.1],
        }
    )

    normalized = update_kospi._normalize_feature_output_columns(ssot_like)

    for column in [
        "Date",
        "Code",
        "Name",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Return",
        "VWAP",
        "Foreign_Net",
        "Inst_Net",
        "Margin_Rate",
    ]:
        assert column in normalized.columns

    row = normalized.iloc[0]
    assert row["Date"] == pd.Timestamp("2026-01-02")
    assert row["Code"] == "000001"
    assert row["Close"] == 1010.0
    assert row["Return"] == 0.01
    assert row["VWAP"] == 1005.0
    assert row["Foreign_Net"] == 100.0
    assert row["Inst_Net"] == 50.0
    assert row["Margin_Rate"] == 2.1


def test_update_kospi_prepares_title_case_input_for_feature_ssot():
    raw = _raw_quote_fixture().rename(
        columns={
            "quote_date": "Date",
            "stock_code": "Code",
            "stock_name": "Name",
            "open_price": "Open",
            "high_price": "High",
            "low_price": "Low",
            "close_price": "Close",
            "volume": "Volume",
            "foreign_net": "Foreign_Net",
            "inst_net": "Inst_Net",
            "margin_rate": "Margin_Rate",
        }
    )

    prepared = update_kospi._prepare_feature_input_columns(raw)
    for column in [
        "quote_date",
        "stock_code",
        "stock_name",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "foreign_net",
        "inst_net",
        "margin_rate",
    ]:
        assert column in prepared.columns

    features = update_kospi.calculate_all_features(prepared)
    assert "open" in features.columns
    assert "close" in features.columns
    assert "return_1d" in features.columns


def test_update_kospi_status_payload_records_warning_steps(monkeypatch, tmp_path):
    monkeypatch.setattr(
        update_kospi,
        "_load_latest_quote_state",
        lambda: {
            "db_state_status": "available",
            "latest_quote_date": "2026-05-11",
            "rows_on_latest_date": 2500,
        },
    )
    steps = [
        {
            "name": "update_kospi_data",
            "status": "completed",
            "finished_at": "2026-05-11T21:05:00",
        },
        {
            "name": "recommend_daily_v2",
            "status": "failed",
            "finished_at": "2026-05-11T21:06:00",
        },
    ]

    payload = update_kospi._build_update_kospi_status(
        "2026-05-11", "2026-05-11T21:00:00", steps
    )
    status_path = update_kospi._write_update_kospi_status(
        payload, tmp_path / "update_kospi_2026-05-11.json"
    )

    written = json.loads(status_path.read_text(encoding="utf-8"))
    assert written["status"] == "completed_with_warnings"
    assert written["feature_source"] == "src.model.common_v2.calculate_all_features"
    assert written["failed_steps"] == ["recommend_daily_v2"]


def test_update_kospi_bottom_rebound_sim_auto_loop_can_be_disabled(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_RUN_BOTTOM_REBOUND_SIM_AUTO_LOOP", "false")

    result = update_kospi._run_bottom_rebound_sim_auto_loop("2026-05-22")

    assert result == {"status": "skipped_disabled"}


def test_update_kospi_bottom_rebound_sim_auto_loop_command_order(monkeypatch):
    calls = []

    def fake_run(command, check, cwd):
        calls.append(command)

    monkeypatch.setenv("KORSTOCKSCAN_RUN_BOTTOM_REBOUND_SIM_AUTO_LOOP", "true")
    monkeypatch.setattr(update_kospi.subprocess, "run", fake_run)

    result = update_kospi._run_bottom_rebound_sim_auto_loop("2026-05-22")

    assert result["status"] == "completed"
    assert calls[0][2] == "src.engine.swing.bottom_rebound_pattern_research"
    assert calls[1][2] == "src.engine.swing.bottom_rebound_policy_auto_loop"
    assert calls[2][2] == "src.engine.swing.bottom_rebound_candidate_source"
    assert "--require-sim-auto-policy" in calls[2]
    assert calls[3][2] == "src.engine.swing_strategy_discovery_sim"
    assert "--include-bottom-rebound-source" in calls[3]
    assert result["runtime_effect"] is False
    assert result["allowed_runtime_apply"] is False
    assert result["broker_order_forbidden"] is True


def test_calculate_all_features_produces_swing_training_core_features():
    raw = _raw_quote_fixture()
    features = common_v2.calculate_all_features(raw)

    for column in [
        "date",
        "code",
        "return_1d",
        "ma_ratio",
        "macd",
        "macd_sig",
        "close_vwap_ratio",
        "obv_change_5",
        "up_trend_2d",
        "dist_ma5",
        "dual_net_buy",
        "foreign_net_roll5",
        "inst_net_roll5",
        "bbb",
        "bbp",
        "atr_ratio",
        "rsi",
        "breakout_20",
        "turnover_shock",
    ]:
        assert column in features.columns


def test_calculate_all_features_matches_expected_numeric_values():
    raw = _raw_quote_fixture()
    features = common_v2.calculate_all_features(raw)
    latest = features.iloc[-1]

    close = raw["close_price"]
    high = raw["high_price"]
    low = raw["low_price"]
    open_ = raw["open_price"]
    volume = raw["volume"]
    foreign_net = raw["foreign_net"]
    inst_net = raw["inst_net"]
    typical = (high + low + close) / 3.0
    turnover = close * volume

    expected = {
        "return_1d": close.pct_change().iloc[-1],
        "return_5d": close.pct_change(5).iloc[-1],
        "return_20d": close.pct_change(20).iloc[-1],
        "ma5": close.rolling(5).mean().iloc[-1],
        "ma20": close.rolling(20).mean().iloc[-1],
        "ma60": close.rolling(60).mean().iloc[-1],
        "ma_ratio": close.iloc[-1] / (close.rolling(20).mean().iloc[-1] + 1e-9),
        "dist_ma5": close.iloc[-1] / (close.rolling(5).mean().iloc[-1] + 1e-9),
        "vwap20": (
            (typical * volume).rolling(20).sum() / (volume.rolling(20).sum() + 1e-9)
        ).iloc[-1],
        "close_vwap_ratio": close.iloc[-1]
        / (
            (
                (typical * volume).rolling(20).sum() / (volume.rolling(20).sum() + 1e-9)
            ).iloc[-1]
            + 1e-9
        ),
        "foreign_net_roll5": foreign_net.rolling(5).sum().iloc[-1]
        / (volume.rolling(5).sum().iloc[-1] + 1e-9),
        "inst_net_roll5": inst_net.rolling(5).sum().iloc[-1]
        / (volume.rolling(5).sum().iloc[-1] + 1e-9),
        "turnover_shock": turnover.iloc[-1]
        / (turnover.rolling(20).median().iloc[-1] + 1e-9),
        "breakout_20": close.iloc[-1]
        / (high.rolling(20).max().shift(1).iloc[-1] + 1e-9),
        "body_ratio": abs(close.iloc[-1] - open_.iloc[-1])
        / (abs(high.iloc[-1] - low.iloc[-1]) + 1e-9),
        "range_ratio": (high.iloc[-1] - low.iloc[-1]) / (close.iloc[-1] + 1e-9),
        "gap_ratio": open_.iloc[-1] / (close.shift(1).iloc[-1] + 1e-9) - 1.0,
    }

    for column, expected_value in expected.items():
        assert np.isclose(
            latest[column], expected_value, rtol=1e-10, atol=1e-10
        ), column

    assert latest["dual_net_buy"] == 1
    assert latest["up_trend_2d"] == 1
