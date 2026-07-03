import json
from dataclasses import replace
from datetime import datetime

from src.engine import holding_exit_matrix_runtime as mod


def _enable_runtime_bias(monkeypatch, **overrides):
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        replace(
            mod.TRADING_RULES,
            HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=True,
            **overrides,
        ),
    )


def test_holding_exit_matrix_runtime_bias_forces_hold_for_avg_down_wait(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    _enable_runtime_bias(monkeypatch)
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


def test_holding_exit_matrix_runtime_bias_does_not_force_hold_with_unusable_ai(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    _enable_runtime_bias(monkeypatch)
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
        position_ctx={
            "profit_rate": -0.4,
            "peak_profit": 0.1,
            "current_ai_score": 72,
            "holding_score_effective_usable": False,
            "holding_score_data_quality": "stale",
            "holding_score_source": "holding_ai_not_called",
        },
    )

    assert merged["action"] == "EXIT"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is False
    assert merged["holding_exit_matrix_ai_score_usable"] is False


def test_holding_exit_matrix_runtime_bias_forces_exit_for_prefer_exit(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    _enable_runtime_bias(monkeypatch)
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
    original_rules = mod.TRADING_RULES
    mod.TRADING_RULES = replace(original_rules, HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=True)
    try:
        action = mod.resolve_holding_exit_matrix_scale_in_bias(
            strategy="SCALPING",
            profit_rate=-0.45,
            peak_profit=0.0,
            current_ai_score=72,
            held_sec=45,
        )
    finally:
        mod.TRADING_RULES = original_rules

    assert action["should_add"] is True
    assert action["add_type"] == "AVG_DOWN"
    assert action["reason"] == "holding_exit_matrix_avg_down_bias"


def test_holding_exit_matrix_scale_in_bias_rejects_unusable_ai_score():
    original_rules = mod.TRADING_RULES
    mod.TRADING_RULES = replace(original_rules, HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=True)
    try:
        action = mod.resolve_holding_exit_matrix_scale_in_bias(
            strategy="SCALPING",
            profit_rate=-0.45,
            peak_profit=0.0,
            current_ai_score=72,
            held_sec=45,
            safety_context={
                "holding_score_effective_usable": False,
                "holding_score_data_quality": "stale",
                "holding_score_source": "holding_ai_not_called",
                "holding_score_age_sec": 999,
            },
        )
    finally:
        mod.TRADING_RULES = original_rules

    assert action["should_add"] is False
    assert action["reason"] == "holding_exit_matrix_ai_score_unusable"
    assert action["ai_score_usable"] is False
    assert action["ai_score_data_quality"] == "stale"


def test_holding_exit_matrix_safety_veto_blocks_runtime_action(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    _enable_runtime_bias(monkeypatch)
    (report_dir / "holding_exit_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "matrix_version": "holding_exit_decision_matrix_v1_2026-05-18",
                "entries": [
                    {
                        "axis": "price_bucket",
                        "bucket": "price_10k_30k",
                        "recommended_bias": "prefer_avg_down_wait",
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
        position_ctx={"exit_rule": "protect_stop", "profit_rate": -0.8},
    )

    assert merged["action"] == "EXIT"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is False
    assert merged["holding_exit_matrix_runtime_reason"] == "safety_veto_passthrough"


def test_holding_exit_matrix_trim_to_hold_requires_explicit_flag(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "holding_exit_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", report_dir)
    _enable_runtime_bias(monkeypatch, HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED=False)
    (report_dir / "holding_exit_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "matrix_version": "holding_exit_decision_matrix_v1_2026-05-18",
                "entries": [
                    {
                        "axis": "price_bucket",
                        "bucket": "price_10k_30k",
                        "recommended_bias": "prefer_avg_down_wait",
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

    merged = mod.merge_holding_exit_matrix_result_fields({"action": "TRIM", "score": 70}, context)

    assert merged["action"] == "TRIM"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is False


def test_holding_exit_matrix_scale_in_flag_blocks_lifecycle_scale_in(monkeypatch):
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        replace(mod.TRADING_RULES, HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=False),
    )
    monkeypatch.setattr(
        mod,
        "resolve_lifecycle_decision",
        lambda **_: {
            "lifecycle_matrix_runtime_effect": "avg_down_bias",
            "lifecycle_matrix_runtime_reason": "bounded_scale_in_bias",
        },
    )

    action = mod.resolve_holding_exit_matrix_scale_in_bias(
        strategy="SCALPING",
        profit_rate=-0.45,
        peak_profit=0.0,
        current_ai_score=72,
        held_sec=45,
    )

    assert action["should_add"] is False
    assert action["reason"] == "holding_exit_matrix_scale_in_bias_disabled"
    assert action["lifecycle_matrix_runtime_effect"] == "avg_down_bias"


def test_holding_exit_matrix_lifecycle_scale_in_bias_rejects_unusable_ai(monkeypatch):
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        replace(mod.TRADING_RULES, HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=True),
    )
    monkeypatch.setattr(
        mod,
        "resolve_lifecycle_decision",
        lambda **_: {
            "lifecycle_matrix_runtime_effect": "avg_down_bias",
            "lifecycle_matrix_runtime_reason": "bounded_scale_in_bias",
        },
    )

    action = mod.resolve_holding_exit_matrix_scale_in_bias(
        strategy="SCALPING",
        profit_rate=-0.45,
        peak_profit=0.0,
        current_ai_score=72,
        held_sec=45,
        safety_context={
            "holding_score_effective_usable": False,
            "holding_score_data_quality": "stale",
            "holding_score_source": "holding_ai_not_called",
            "holding_score_age_sec": 999,
        },
    )

    assert action["should_add"] is False
    assert action["reason"] == "holding_exit_matrix_ai_score_unusable"
    assert action["lifecycle_matrix_runtime_effect"] == "avg_down_bias"
