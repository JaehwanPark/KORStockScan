import json

from src.engine.lifecycle import greenfield_authority as mod


def _write_policy(path, rows):
    path.write_text(
        json.dumps(
            {
                "policy_version": "greenfield_real_environment_authority:2026-05-27",
                "scope": "full_lifecycle",
                "stages": {
                    "entry": [row for row in rows if row["stage"] == "entry"],
                    "submit": [row for row in rows if row["stage"] == "submit"],
                    "holding": [row for row in rows if row["stage"] == "holding"],
                    "scale_in": [row for row in rows if row["stage"] == "scale_in"],
                    "exit": [row for row in rows if row["stage"] == "exit"],
                },
            }
        ),
        encoding="utf-8",
    )


def test_greenfield_authority_inactive_allows_without_policy(monkeypatch):
    monkeypatch.delenv(mod.ENABLED_ENV, raising=False)

    decision = mod.evaluate_greenfield_authority(stage="entry", action="BUY", strategy="SCALPING")

    assert decision.active is False
    assert decision.allowed is True
    assert decision.reason == "greenfield_inactive"


def test_greenfield_authority_allows_promoted_bucket(tmp_path, monkeypatch):
    policy = tmp_path / "policy.json"
    _write_policy(
        policy,
        [
            {
                "stage": "entry",
                "action": "BUY",
                "strategy_scope": "scalping",
                "bucket_id": "entry:score_66_69",
                "family": "entry_wait6579_score66_69_recovery_gate_v1",
                "source_quality_gate": "pass",
                "ai_tier2_status": "parsed",
            }
        ],
    )
    monkeypatch.setenv(mod.ENABLED_ENV, "true")
    monkeypatch.setenv(mod.SCOPE_ENV, mod.FULL_LIFECYCLE_SCOPE)
    monkeypatch.setenv(mod.POLICY_FILE_ENV, str(policy))

    decision = mod.evaluate_greenfield_authority(stage="entry", action="BUY", strategy="SCALPING")

    assert decision.active is True
    assert decision.allowed is True
    assert decision.reason == "promoted_bucket_allowed"
    assert decision.matched_bucket_id == "entry:score_66_69"


def test_greenfield_authority_blocks_unpromoted_bucket(tmp_path, monkeypatch):
    policy = tmp_path / "policy.json"
    _write_policy(policy, [])
    monkeypatch.setenv(mod.ENABLED_ENV, "true")
    monkeypatch.setenv(mod.SCOPE_ENV, mod.FULL_LIFECYCLE_SCOPE)
    monkeypatch.setenv(mod.POLICY_FILE_ENV, str(policy))

    decision = mod.evaluate_greenfield_authority(stage="submit", action="ALLOW_SUBMIT", strategy="SCALPING")

    assert decision.active is True
    assert decision.allowed is False
    assert decision.reason == "unpromoted_bucket_blocked"


def test_greenfield_authority_enabled_with_missing_policy_fails_closed(monkeypatch):
    monkeypatch.setenv(mod.ENABLED_ENV, "true")
    monkeypatch.setenv(mod.SCOPE_ENV, mod.FULL_LIFECYCLE_SCOPE)
    monkeypatch.setenv(mod.POLICY_FILE_ENV, "/tmp/does-not-exist-greenfield-policy.json")

    decision = mod.evaluate_greenfield_authority(stage="submit", action="ALLOW_SUBMIT", strategy="SCALPING")

    assert mod.greenfield_authority_active() is True
    assert decision.active is True
    assert decision.allowed is False
    assert decision.reason == "greenfield_policy_missing_or_invalid"


def test_greenfield_authority_keeps_hard_safety_passthrough(tmp_path, monkeypatch):
    policy = tmp_path / "policy.json"
    _write_policy(policy, [])
    monkeypatch.setenv(mod.ENABLED_ENV, "true")
    monkeypatch.setenv(mod.SCOPE_ENV, mod.FULL_LIFECYCLE_SCOPE)
    monkeypatch.setenv(mod.POLICY_FILE_ENV, str(policy))

    decision = mod.evaluate_greenfield_authority(
        stage="exit",
        action="SELL",
        strategy="SCALPING",
        hard_safety=True,
    )

    assert decision.active is True
    assert decision.allowed is True
    assert decision.reason == "hard_safety_passthrough"
    assert decision.hard_safety_override is True
