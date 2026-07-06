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


def _strong_micro_context(**overrides):
    ctx = {
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 5,
        "buy_pressure_10t": 72.0,
        "tick_acceleration_ratio": 0.8,
        "curr_vs_micro_vwap_bp": -2.0,
        "micro_vwap_available": True,
        "large_sell_print_detected": False,
    }
    ctx.update(overrides)
    return ctx


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
        position_ctx={
            "profit_rate": -0.4,
            "peak_profit": 0.1,
            "current_ai_score": 72,
            "holding_score_source": "live",
            "holding_score_data_quality": "fresh",
            "holding_score_effective_usable": True,
            **_strong_micro_context(),
        },
    )

    assert merged["action"] == "HOLD"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is True
    assert merged["holding_exit_matrix_runtime_effect"] == "force_hold"
    assert merged["holding_exit_matrix_scale_in_bias"] == "AVG_DOWN"


def test_holding_exit_matrix_runtime_bias_treats_unusable_ai_as_neutral_prior(tmp_path, monkeypatch):
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
            **_strong_micro_context(),
        },
    )

    assert merged["action"] == "HOLD"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is True
    assert merged["holding_exit_matrix_ai_score_usable"] is False
    assert merged["holding_exit_matrix_score_gate_converted_to_prior"] is True
    assert merged["holding_exit_matrix_score_prior_band"] == "neutral_or_unknown"
    assert merged["holding_exit_matrix_ai_score_prior_weight"] == 0.0
    assert merged["holding_exit_matrix_current_micro_support"] is True


def test_holding_exit_matrix_runtime_bias_keeps_missing_ai_as_neutral_prior_without_opening_hold(tmp_path, monkeypatch):
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

    assert merged["action"] == "EXIT"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is False
    assert merged["holding_exit_matrix_runtime_reason"] == "current_micro_support_missing"
    assert merged["holding_exit_matrix_ai_score_usable"] is False
    assert merged["holding_exit_matrix_ai_score_excluded_reason"] == "holding_score_data_quality_insufficient"
    assert merged["holding_exit_matrix_score_prior_band"] == "neutral_or_unknown"
    assert merged["holding_exit_matrix_current_micro_support"] is False


def test_holding_exit_matrix_runtime_bias_does_not_hard_block_timeout_ai_source_with_micro_support(tmp_path, monkeypatch):
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
                        "recommended_bias": "prefer_pyramid_wait",
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
            "profit_rate": 1.2,
            "peak_profit": 1.3,
            "current_ai_score": 82,
            "holding_score_source": "timeout",
            "holding_score_data_quality": "fresh",
            **_strong_micro_context(profit_rate=1.2),
        },
    )

    assert merged["action"] == "HOLD"
    assert merged["holding_exit_matrix_runtime_bias_applied"] is True
    assert merged["holding_exit_matrix_ai_score_usable"] is False
    assert merged["holding_exit_matrix_ai_score_excluded_reason"] == "holding_score_source_timeout"
    assert merged["holding_exit_matrix_score_prior_band"] == "neutral_or_unknown"
    assert merged["holding_exit_matrix_current_micro_support"] is True


def test_holding_exit_matrix_runtime_bias_records_partial_score_prior_without_hard_block(tmp_path, monkeypatch):
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

    blocked = mod.merge_holding_exit_matrix_result_fields(
        {"action": "EXIT", "score": 80},
        context,
        position_ctx={
            "profit_rate": -0.4,
            "peak_profit": 0.1,
            "current_ai_score": 72,
            "holding_score_source": "live",
            "holding_score_data_quality": "partial",
            "holding_score_effective_usable": True,
        },
    )
    allowed = mod.merge_holding_exit_matrix_result_fields(
        {"action": "EXIT", "score": 80},
        context,
        position_ctx={
            "profit_rate": -0.4,
            "peak_profit": 0.1,
            "current_ai_score": 72,
            "holding_score_source": "live",
            "holding_score_data_quality": "partial",
            "holding_score_effective_usable": True,
            "tick_aggressor_trusted_count": 4,
        },
    )

    assert blocked["action"] == "EXIT"
    assert blocked["holding_exit_matrix_runtime_bias_applied"] is False
    assert blocked["holding_exit_matrix_ai_score_usable"] is False
    assert blocked["holding_exit_matrix_ai_score_excluded_reason"] == "holding_score_partial_requires_microstructure"
    assert blocked["holding_exit_matrix_score_prior_band"] == "neutral_or_unknown"
    assert allowed["action"] == "EXIT"
    assert allowed["holding_exit_matrix_ai_score_usable"] is True
    assert allowed["holding_exit_matrix_ai_score_microstructure_confirmed"] is True
    assert allowed["holding_exit_matrix_current_micro_support"] is False


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
            safety_context={
                "holding_score_source": "live",
                "holding_score_data_quality": "fresh",
                "holding_score_effective_usable": True,
                **_strong_micro_context(),
            },
        )
    finally:
        mod.TRADING_RULES = original_rules

    assert action["should_add"] is True
    assert action["add_type"] == "AVG_DOWN"
    assert action["reason"] == "holding_exit_matrix_avg_down_bias"


def test_holding_exit_matrix_scale_in_bias_keeps_missing_ai_as_neutral_prior_without_opening_add(monkeypatch):
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        replace(mod.TRADING_RULES, HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=True),
    )

    action = mod.resolve_holding_exit_matrix_scale_in_bias(
        strategy="SCALPING",
        profit_rate=-0.45,
        peak_profit=0.0,
        current_ai_score=72,
        held_sec=45,
    )

    assert action["should_add"] is False
    assert action["reason"] == "holding_exit_matrix_current_micro_support_missing"
    assert action["ai_score_usable"] is False
    assert action["ai_score_excluded_reason"] == "holding_score_data_quality_insufficient"
    assert action["score_gate_converted_to_prior"] is True
    assert action["score_prior_band"] == "neutral_or_unknown"
    assert action["ai_score_prior_weight"] == 0.0
    assert action["holding_exit_matrix_current_micro_support"] is False


def test_holding_exit_matrix_scale_in_bias_does_not_hard_block_unusable_ai_score_with_micro_support():
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
                **_strong_micro_context(),
            },
        )
    finally:
        mod.TRADING_RULES = original_rules

    assert action["should_add"] is True
    assert action["reason"] == "holding_exit_matrix_avg_down_bias"
    assert action["ai_score_usable"] is False
    assert action["ai_score_data_quality"] == "stale"
    assert action["score_prior_band"] == "neutral_or_unknown"
    assert action["holding_exit_matrix_current_micro_support"] is True


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


def test_holding_exit_matrix_lifecycle_scale_in_bias_keeps_unusable_ai_as_neutral_prior_with_micro_support(monkeypatch):
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
            **_strong_micro_context(),
        },
    )

    assert action["should_add"] is True
    assert action["reason"] == "lifecycle_decision_matrix_avg_down"
    assert action["lifecycle_matrix_runtime_effect"] == "avg_down_bias"
    assert action["ai_score_usable"] is False
    assert action["score_prior_band"] == "neutral_or_unknown"
    assert action["ai_score_prior_weight"] == 0.0
    assert action["holding_exit_matrix_current_micro_support"] is True
