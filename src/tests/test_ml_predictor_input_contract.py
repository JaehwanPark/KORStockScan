import numpy as np
import pandas as pd

from src.engine.swing import ml_predictor


class _ConstantModel:
    def __init__(self, prob, expected_columns):
        self.prob = prob
        self.expected_columns = expected_columns

    def predict_proba(self, frame):
        missing = [col for col in self.expected_columns if col not in frame.columns]
        assert not missing
        return np.array([[1.0 - self.prob, self.prob] for _ in range(len(frame))])


def _legacy_ohlcv_frame():
    dates = pd.date_range("2026-02-01", periods=60, freq="D")
    close = np.linspace(10000, 12000, len(dates))
    return pd.DataFrame(
        {
            "Date": dates,
            "Code": "402340",
            "Name": "SK스퀘어",
            "Open": close * 0.99,
            "High": close * 1.02,
            "Low": close * 0.98,
            "Close": close,
            "Volume": np.linspace(100000, 250000, len(dates)),
            "Foreign_Net": np.linspace(1000, 5000, len(dates)),
            "Inst_Net": np.linspace(500, 3000, len(dates)),
            "Margin_Rate": np.linspace(1.0, 1.5, len(dates)),
        }
    )


def test_predictor_accepts_legacy_uppercase_scanner_frame():
    models = (
        _ConstantModel(0.61, ml_predictor.FEATURES_XGB),
        _ConstantModel(0.62, ml_predictor.FEATURES_LGBM),
        _ConstantModel(0.63, ml_predictor.FEATURES_XGB),
        _ConstantModel(0.64, ml_predictor.FEATURES_LGBM),
        _ConstantModel(
            0.65,
            ["XGB_Prob", "LGBM_Prob", "Bull_XGB_Prob", "Bull_LGBM_Prob"],
        ),
    )

    prob = ml_predictor.predict_prob_for_df(_legacy_ohlcv_frame(), models)

    assert prob == 0.65


def test_normalize_model_input_frame_fills_required_identity_fields():
    frame = _legacy_ohlcv_frame().drop(columns=["Code", "Name"])

    normalized = ml_predictor.normalize_model_input_frame(frame)

    assert "date" in normalized.columns
    assert normalized["code"].iloc[-1] == "000000"
    assert normalized["name"].iloc[-1] == ""
    assert normalized["close"].iloc[-1] == frame["Close"].iloc[-1]
