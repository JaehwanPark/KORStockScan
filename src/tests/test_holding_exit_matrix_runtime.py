import json
from datetime import datetime

from src.engine import holding_exit_matrix_runtime as mod


def test_holding_exit_matrix_runtime_bias_forces_hold_for_avg_down_wait(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    (report_dir / "holding_exit_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "matrix_version": "holding_exit_decision_matrix_v1_2026-05-18",
                "source_date": "2026-05-18",
                "valid_for_date": "next_preopen",
                "application_mode": "operator_override_runtime_bias",
                "entries": [
                    {
                        "axis": "price_bucket",
                        "bucket": "price_10k_30k",
                        "recommended_bias": "prefer_avg_down_wait",
                        "policy_hint": "avg_down_wait",
                        "prompt_hint": "wait for avg-down confirmation",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = mod.build_holding_exit_matrix_runtime_context(
        prompt_profile="holding",
        ws_data={"curr": 20000, "volume": 1_000_000},
        recent_candles=[],
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
    )

    merged = mod.merge_holding_exit_matrix_result_fields(
        {"action": "EXIT", "score": 80},
        context,
        position_ctx={"profit_rate": -0.4, "peak_profit": 0.1, "current_ai_score": 72},
    )

    assert merged["action"] == "HOLD"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is True
    assert merged["holding_exit_matrix_runtime_effect"] == "force_hold"
    assert merged["holding_exit_matrix_scale_in_bias"] == "AVG_DOWN"


def test_holding_exit_matrix_runtime_bias_forces_exit_for_prefer_exit(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    (report_dir / "holding_exit_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "matrix_version": "holding_exit_decision_matrix_v1_2026-05-18",
                "source_date": "2026-05-18",
                "valid_for_date": "next_preopen",
                "application_mode": "operator_override_runtime_bias",
                "entries": [
                    {
                        "axis": "price_bucket",
                        "bucket": "price_10k_30k",
                        "recommended_bias": "prefer_exit",
                        "policy_hint": "exit_now",
                        "prompt_hint": "exit bucket",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = mod.build_holding_exit_matrix_runtime_context(
        prompt_profile="holding",
        ws_data={"curr": 20000, "volume": 1_000_000},
        recent_candles=[],
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
    )

    merged = mod.merge_holding_exit_matrix_result_fields({"action": "HOLD", "score": 55}, context)

    assert merged["action"] == "EXIT"
    assert merged["holding_exit_matrix_runtime_reason"] == "matrix_prefer_exit"


def test_holding_exit_matrix_scale_in_bias_returns_avg_down_action():
    action = mod.resolve_holding_exit_matrix_scale_in_bias(
        strategy="SCALPING",
        profit_rate=-0.45,
        peak_profit=0.0,
        current_ai_score=72,
        held_sec=45,
    )

    assert action["should_add"] is True
    assert action["add_type"] == "AVG_DOWN"
    assert action["reason"] == "holding_exit_matrix_avg_down_bias"
