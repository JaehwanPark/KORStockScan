import json
from dataclasses import replace
from datetime import datetime

from src.engine import lifecycle_decision_matrix_runtime as mod


def _write_policy(path, *, promote_ready=True, confidence=0.8, selected_action="BUY_DEFENSIVE"):
    path.write_text(
        json.dumps(
            {
                "matrix_version": "lifecycle_decision_matrix_v1_2026-05-18",
                "policy_entries": [
                    {
                        "policy_key": "entry:weighted_adm_v1",
                        "stage": "entry",
                        "confidence": confidence,
                        "selected_action": selected_action,
                        "source_quality_gate": "pass",
                        "promote_ready": promote_ready,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _enable_rules(monkeypatch, *, policy_file, max_promotes=3, min_confidence=0.6, promote_enabled=True):
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        replace(
            mod.TRADING_RULES,
            LIFECYCLE_DECISION_MATRIX_ENABLED=True,
            LIFECYCLE_DECISION_MATRIX_POLICY_FILE=str(policy_file),
            LIFECYCLE_DECISION_MATRIX_POLICY_VERSION="test-v1",
            LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED=promote_enabled,
            LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY=max_promotes,
            LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE=min_confidence,
        ),
    )
    mod.reset_lifecycle_decision_matrix_promote_counter()


def test_lifecycle_runtime_hard_safety_passthrough_blocks_matrix_action(tmp_path, monkeypatch):
    policy_file = tmp_path / "lifecycle_decision_matrix_2026-05-18.json"
    _write_policy(policy_file)
    _enable_rules(monkeypatch, policy_file=policy_file)

    decision = mod.resolve_lifecycle_decision(
        stage="entry",
        original_action="WAIT",
        context={"broker_submit_blocked": True},
        now=datetime.fromisoformat("2026-05-19T09:10:00"),
    )

    assert decision["lifecycle_matrix_safety_passthrough"] is True
    assert decision["lifecycle_matrix_fixed_threshold_role"] == "hard_safety"
    assert decision["lifecycle_matrix_runtime_effect"] == "none"


def test_lifecycle_runtime_promotes_buy_defensive_with_daily_cap(tmp_path, monkeypatch):
    policy_file = tmp_path / "lifecycle_decision_matrix_2026-05-18.json"
    _write_policy(policy_file)
    _enable_rules(monkeypatch, policy_file=policy_file, max_promotes=1)

    first = mod.resolve_lifecycle_decision(
        stage="entry",
        original_action="WAIT",
        context={},
        now=datetime.fromisoformat("2026-05-19T09:10:00"),
    )
    payload = mod.apply_lifecycle_decision_to_payload({"action": "WAIT", "action_v2": "WAIT"}, first)

    assert first["lifecycle_matrix_runtime_effect"] == "promote_buy_defensive"
    assert payload["action"] == "BUY"
    assert payload["lifecycle_matrix_buy_variant"] == "BUY_DEFENSIVE"

    second = mod.resolve_lifecycle_decision(
        stage="entry",
        original_action="WAIT",
        context={},
        now=datetime.fromisoformat("2026-05-19T09:11:00"),
    )

    assert second["lifecycle_matrix_runtime_reason"] == "promote_cap_exhausted"
    assert second["lifecycle_matrix_runtime_effect"] == "none"


def test_lifecycle_runtime_low_confidence_keeps_baseline_prior_as_feature_only(tmp_path, monkeypatch):
    policy_file = tmp_path / "lifecycle_decision_matrix_2026-05-18.json"
    _write_policy(policy_file, confidence=0.2)
    _enable_rules(monkeypatch, policy_file=policy_file, min_confidence=0.6)

    decision = mod.resolve_lifecycle_decision(
        stage="entry",
        original_action="WAIT",
        context={"ai_score": 74},
        now=datetime.fromisoformat("2026-05-19T09:10:00"),
    )

    assert decision["lifecycle_matrix_runtime_reason"] == "confidence_below_min_stage_confidence"
    assert decision["lifecycle_matrix_runtime_effect"] == "none"


def test_lifecycle_runtime_submit_allow_is_observation_not_guard_override(tmp_path, monkeypatch):
    policy_file = tmp_path / "lifecycle_decision_matrix_2026-05-18.json"
    policy_file.write_text(
        json.dumps(
            {
                "matrix_version": "lifecycle_decision_matrix_v1_2026-05-18",
                "policy_entries": [
                    {
                        "policy_key": "submit:weighted_adm_v1",
                        "stage": "submit",
                        "confidence": 0.9,
                        "selected_action": "ALLOW_SUBMIT",
                        "source_quality_gate": "pass",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    _enable_rules(monkeypatch, policy_file=policy_file)

    decision = mod.resolve_lifecycle_decision(
        stage="submit",
        original_action="ALLOW_SUBMIT",
        context={"quote_age_at_submit_ms": 100},
        now=datetime.fromisoformat("2026-05-19T09:10:00"),
    )
    blocked = mod.resolve_lifecycle_decision(
        stage="submit",
        original_action="ALLOW_SUBMIT",
        context={"stale_quote_submit_block": True},
        now=datetime.fromisoformat("2026-05-19T09:11:00"),
    )

    assert decision["lifecycle_matrix_runtime_effect"] == "allow_submit_observe"
    assert blocked["lifecycle_matrix_safety_passthrough"] is True
    assert blocked["lifecycle_matrix_runtime_effect"] == "none"
