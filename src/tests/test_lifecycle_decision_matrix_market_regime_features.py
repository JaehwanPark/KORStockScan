from src.engine import lifecycle_decision_matrix as ldm
from src.engine import scalp_entry_action_decision_matrix as entry_adm


def test_market_regime_continuous_fields_are_runtime_features_not_labels():
    row = {
        "market_regime": "RISK_OFF",
        "market_regime_continuous_score": 41.5,
        "market_regime_continuous_label": "RISK_OFF",
        "market_regime_component_scores": {"domestic_breadth": 10.0},
        "swing_entry_recovery_gate_score": 0,
        "market_regime_score_version": "market_regime_continuous_v1",
        "market_regime_source_quality": "valid",
        "profit_rate": 1.2,
    }

    runtime_features = ldm._runtime_features(row)
    labels = ldm._labels(row)

    assert runtime_features["market_regime_continuous_score"] == 41.5
    assert runtime_features["market_regime_continuous_label"] == "RISK_OFF"
    assert (
        runtime_features["market_regime_component_scores"]["domestic_breadth"] == 10.0
    )
    assert runtime_features["swing_entry_recovery_gate_score"] == 0
    assert "market_regime_continuous_label" not in labels
    assert labels["profit_rate"] == 1.2


def test_entry_adm_keeps_market_regime_continuous_as_context_feature():
    row = entry_adm._base_row(
        {
            "stage": "ai_confirmed",
            "stock_code": "000001",
            "emitted_at": "2026-05-21T09:10:00",
            "fields": {
                "action": "WAIT",
                "ai_score": 62,
                "market_regime": "RISK_OFF",
                "market_regime_continuous_score": 41.5,
                "market_regime_continuous_label": "RISK_OFF",
                "market_regime_component_scores": {"domestic_breadth": 10.0},
                "swing_entry_recovery_gate_score": 0,
                "market_regime_score_version": "market_regime_continuous_v1",
                "market_regime_source_quality": "valid",
                "risk_context_owner": "market_regime_continuous",
            },
        }
    )

    assert row["market_regime_continuous_bucket"] == "market_regime_risk_off"
    assert row["market_regime_continuous_score"] == 41.5
    assert row["market_regime_component_scores"]["domestic_breadth"] == 10.0
    assert row["risk_context_owner"] == "market_regime_continuous"
    assert row["chosen_action"] == "NO_BUY_AI"
