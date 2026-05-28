import json

from src.engine.lifecycle import greenfield_authority as mod


def _write_policy(path, rows):
    stage_contract = {
        "entry": {"baseline_passthrough_allowed": False},
        "submit": {"baseline_passthrough_allowed": True},
        "holding": {"baseline_passthrough_allowed": True},
        "scale_in": {"baseline_passthrough_allowed": True},
        "exit": {"baseline_passthrough_allowed": True},
    }
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
                "stage_contract": stage_contract,
                "allowlist": rows,
            }
        ),
        encoding="utf-8",
    )


def test_greenfield_authority_inactive_allows_without_policy(monkeypatch):
    monkeypatch.delenv(mod.ENABLED_ENV, raising=False)

    decision = mod.evaluate_greenfield_authority(
        stage="entry",
        action="BUY",
        strategy="SCALPING",
        observed_bucket_id="entry:score_66_69",
    )

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

    decision = mod.evaluate_greenfield_authority(
        stage="entry",
        action="BUY",
        strategy="SCALPING",
        observed_bucket_id="entry:score_66_69",
    )

    assert decision.active is True
    assert decision.allowed is True
    assert decision.reason == "promoted_bucket_allowed"
    assert decision.matched_bucket_id == "entry:score_66_69"


def test_greenfield_authority_blocks_entry_when_observed_bucket_missing(tmp_path, monkeypatch):
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
    assert decision.allowed is False
    assert decision.reason == "observed_bucket_missing"


def test_greenfield_authority_blocks_incomplete_full_lifecycle_bundle(tmp_path, monkeypatch):
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "policy_version": "greenfield_real_environment_authority:2026-05-27",
                "scope": "full_lifecycle",
                "stages": {
                    "entry": [
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
                    "submit": [],
                    "holding": [],
                    "scale_in": [],
                    "exit": [],
                },
                "allowlist": [
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
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(mod.ENABLED_ENV, "true")
    monkeypatch.setenv(mod.SCOPE_ENV, mod.FULL_LIFECYCLE_SCOPE)
    monkeypatch.setenv(mod.POLICY_FILE_ENV, str(policy))

    decision = mod.evaluate_greenfield_authority(stage="entry", action="BUY", strategy="SCALPING")

    assert decision.active is True
    assert decision.allowed is False
    assert decision.reason == "incomplete_lifecycle_bundle"


def test_greenfield_authority_blocks_unpromoted_bucket(tmp_path, monkeypatch):
    policy = tmp_path / "policy.json"
    _write_policy(policy, [])
    monkeypatch.setenv(mod.ENABLED_ENV, "true")
    monkeypatch.setenv(mod.SCOPE_ENV, mod.FULL_LIFECYCLE_SCOPE)
    monkeypatch.setenv(mod.POLICY_FILE_ENV, str(policy))

    decision = mod.evaluate_greenfield_authority(stage="submit", action="ALLOW_SUBMIT", strategy="SCALPING")

    assert decision.active is True
    assert decision.allowed is False
    assert decision.reason == "greenfield_policy_allowlist_empty"


def test_greenfield_authority_blocks_observed_bucket_mismatch(tmp_path, monkeypatch):
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

    decision = mod.evaluate_greenfield_authority(
        stage="entry",
        action="BUY",
        strategy="SCALPING",
        observed_bucket_id="entry:score_70p",
    )

    assert decision.active is True
    assert decision.allowed is False
    assert decision.reason == "observed_bucket_policy_mismatch"


def test_format_lifecycle_bucket_label_entry_combo_is_readable():
    bucket_id = (
        "entry:combo_entry_spot:"
        "score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|"
        "liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000"
    )

    label = mod.format_lifecycle_bucket_label(bucket_id, stage="entry")

    assert "score: score 66-69" in label
    assert "source: WAIT65-79 EV" in label
    assert "time: 09:00-10:00" in label
    assert "entry:combo_entry_spot" not in label


def test_format_lifecycle_bucket_label_entry_slug_is_readable():
    bucket_id = (
        "entry:combo_entry_spot:"
        "score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_"
        "liquidity_liquidity_unknown_overbought_overbought_unknown_time_time_unknown"
    )

    label = mod.format_lifecycle_bucket_label(bucket_id, stage="entry")

    assert "score: score 66-69" in label
    assert "source: WAIT65-79 EV" in label
    assert "time: time unclassified" in label
    assert "candidate bucket instrumentation gap" not in label


def test_format_greenfield_bucket_notice_line_keeps_raw_provenance():
    observed = (
        "entry:combo_entry_spot:"
        "score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|"
        "liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown"
    )
    decision = mod.GreenfieldDecision(
        active=True,
        allowed=True,
        stage="entry",
        action="BUY",
        reason="promoted_bucket_allowed",
        matched_bucket_id=observed,
        observed_bucket_id=observed,
    )

    line = mod.format_greenfield_bucket_notice_line(decision)

    assert "entry bucket promoted / submit bucket separate" in line
    assert "time: time unclassified" in line
    assert f"Bucket ID: `{observed}`" in line


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
